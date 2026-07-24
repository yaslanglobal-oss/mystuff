import json
import os
import re
import sys
import urllib.request

# 从 GitHub Secrets 读取敏感配置
USER = os.getenv("MY_USER", "abcd").strip()
PASS = os.getenv("MY_PASS", "EfGh").strip()
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "").strip()
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "").strip()


def send_tg_message(text):
    """安全发送 Telegram 消息"""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("❌ 未配置 TG 密钥，取消发送。")
        return False
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.status == 200
    except Exception as e:
        print(f"❌ 发送 TG 时发生异常: {e}")
        return False


def test_socks5_proxy(server, port):
    """
    不依赖第三方库，直接使用 Python 原生 socket 库对 SOCKS5 进行握手和登录验证。
    如果验证成功，证明这是一个完全可用的高匿 TG 代理链接。
    """
    import socket

    try:
        # 1. 建立基础 TCP 连接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(4)
        sock.connect((server, int(port)))

        # 2. 发送 SOCKS5 握手信号 (支持 无认证0x00 和 密码认证0x02)
        sock.sendall(b"\x05\x02\x00\x02")
        method_res = sock.recv(2)

        if not method_res or method_res[0] != 0x05:
            sock.close()
            return False

        # 3. 如果服务器要求密码验证 (0x02)
        if method_res[1] == 0x02:
            user_bytes = USER.encode("utf-8")
            pass_bytes = PASS.encode("utf-8")
            # 构造验证包: [版本0x01, 账号长度, 账号, 密码长度, 密码]
            auth_packet = (
                b"\x01"
                + bytes([len(user_bytes)])
                + user_bytes
                + bytes([len(pass_bytes)])
                + pass_bytes
            )
            sock.sendall(auth_packet)
            auth_res = sock.recv(2)
            if not auth_res or auth_res[1] != 0x00:  # 0x00 代表认证成功
                sock.close()
                return False

        # 4. 尝试向 Telegram 官方服务器 IP 发起代理连接请求 (测试连通性)
        # 这里使用 TG 官方核心数据中心 IP：149.154.167.50，端口 443
        dest_ip = socket.inet_aton("149.154.167.50")
        dest_port = (443).to_bytes(2, byteorder="big")
        # 构造连接包: [版本0x05, 命令0x01(CONNECT), 保留0x00, 地址类型0x01(IPv4), IP, 端口]
        connect_packet = b"\x05\x01\x00\x01" + dest_ip + dest_port
        sock.sendall(connect_packet)
        conn_res = sock.recv(10)

        sock.close()
        # 响应的第二字节为 0x00 代表代理服务器成功连接到了 Telegram 目标端
        return conn_res and conn_res[1] == 0x00
    except Exception:
        return False


def main():
    scan_result_file = "nmap_report.txt"
    if not os.path.exists(scan_result_file):
        print("❌ 未找到 Nmap 扫描报告文件。")
        sys.exit(1)

    with open(scan_result_file, "r", encoding="utf-8") as f:
        report_content = f.read()

    # 1. 解析 Nmap 报告中的目标 IP
    ip_match = re.search(r"scan report for ([\d\.]+)", report_content)
    if not ip_match:
        print("❌ 无法从报告中解析出目标 IP")
        sys.exit(1)
    target_ip = ip_match.group(1)

    # 2. 提取所有开放的端口号
    open_ports = []
    lines = report_content.split("\n")
    for line in lines:
        if "open" in line and "/" in line:
            # 提取例如 "32774/tcp open" 中的 "32774"
            port_num = line.split("/")[0].strip()
            if port_num.isdigit():
                open_ports.append(int(port_num))

    print(f"📊 Nmap 扫描完成，检测到目标主机 {target_ip} 共开放了 {len(open_ports)} 个端口。")

    # 3. 精准对开放端口进行 SOCKS5 代理可用性测试
    valid_proxies = []
    for port in open_ports:
        print(f"🔄 正在验证端口 {port} 是否支持 SOCKS5 登录...")
        if test_socks5_proxy(target_ip, port):
            print(f"✅ 端口 {port} 验证通过！这是一个可用的 TG 代理。")
            valid_proxies.append(port)
        else:
            print(f"❌ 端口 {port} 未通过代理认证。")

    # 4. 组装结果并发送至 Telegram 手机端
    msg_header = f"⏰ 【双重检测任务】扫描验证完成！\n目标主机: {target_ip}\n\n"

    # 组装开放端口信息
    if open_ports:
        ports_str = ", ".join([str(p) for p in open_ports])
        msg_body = f"📍 服务器实际开放的端口: \n`{ports_str}`\n\n"
    else:
        msg_body = "📍 服务器没有开放任何端口。\n\n"

    # 组装有效的代理快捷链接
    msg_proxy = "🔗 【检测通过】可用 SOCKS5 代理链接：\n"
    if valid_proxies:
        for port in valid_proxies:
            msg_proxy += f"▶️ https://t.me{target_ip}&port={port}&user={USER}&pass={PASS}\n\n"
    else:
        msg_proxy += "🚫 本次扫描未发现符合账号密码配置的可用 TG 代理。"

    final_msg = msg_header + msg_body + msg_proxy

    # 发送通知
    send_tg_message(final_msg)


if __name__ == "__main__":
    main()
