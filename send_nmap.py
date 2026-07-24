import os
import re
import sys
import json
import socket
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

# 从 GitHub Secrets 读取敏感配置
USER = os.getenv("MY_USER", "abcd").strip()
PASS = os.getenv("MY_PASS", "EfGh").strip()
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "").strip()
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "").strip()

# 配置并发线程数（300个端口使用50个线程并发，几秒内即可全部测完）
CONCURRENT_WORKERS = 50 


def send_tg_message(text):
    """安全发送 Telegram 消息（带超长大容量自动切片防护）"""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("❌ 未配置 TG 密钥，取消发送。")
        return False
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

    max_length = 4000
    message_chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]

    for index, chunk in enumerate(message_chunks, 1):
        if len(message_chunks) > 1:
            chunk += f"\n\n(第 {index}/{len(message_chunks)} 页)"

        payload = {
            "chat_id": TG_CHAT_ID,
            "text": chunk
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                print(f"TG 第 {index} 页发送成功，状态码: {response.status}")
        except Exception as e:
            print(f"❌ 发送 TG 第 {index} 页失败: {e}")
    return True


def test_socks5_proxy(server, port):
    """使用原生 socket 对单个端口进行高速 SOCKS5 代理登录和连通性验证"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 300多个端口并发时，超时时间设置为 3 秒足够，卡死服务会瞬间被切断
        sock.settimeout(3.0)
        sock.connect((server, int(port)))

        # 握手
        sock.sendall(b"\x05\x02\x00\x02")
        method_res = sock.recv(2)
        if not method_res or method_res[1] != 0x02 and method_res[1] != 0x00:
            sock.close()
            return port, False

        # 如果需要密码认证
        if method_res[1] == 0x02:
            user_bytes = USER.encode('utf-8')
            pass_bytes = PASS.encode('utf-8')
            auth_packet = b"\x01" + bytes([len(user_bytes)]) + user_bytes + bytes([len(pass_bytes)]) + pass_bytes
            sock.sendall(auth_packet)
            auth_res = sock.recv(2)
            if not auth_res or auth_res[1] != 0x00:
                sock.close()
                return port, False

        # 对撞测试：尝试连接 Telegram 核心服务器 IP
        dest_ip = socket.inet_aton("149.154.167.50")
        dest_port = (443).to_bytes(2, byteorder='big')
        connect_packet = b"\x05\x01\x00\x01" + dest_ip + dest_port
        sock.sendall(connect_packet)
        conn_res = sock.recv(10)
        sock.close()
        
        # 第二字节为 0x00 代表真正可以用来连通 TG
        is_valid = conn_res and conn_res[1] == 0x00
        return port, is_valid
    except Exception:
        return port, False


def main():
    scan_result_file = "nmap_report.txt"
    if not os.path.exists(scan_result_file):
        print("❌ 未找到 Nmap 扫描报告文件。")
        sys.exit(1)

    with open(scan_result_file, "r", encoding="utf-8") as f:
        report_content = f.read()

    ip_match = re.search(r"scan report for ([\d\.]+)", report_content)
    if not ip_match:
        print("❌ 无法从报告中解析出目标 IP")
        sys.exit(1)
    target_ip = ip_match.group(1)

    # 1. 提取所有开放端口
    open_ports = []
    lines = report_content.split("\n")
    for line in lines:
        if "open" in line and "/" in line:
            port_num = line.split("/")[0].strip()
            if port_num.isdigit():
                open_ports.append(int(port_num))

    print(f"📊 Nmap 快扫完成！检测到目标主机 {target_ip} 共有 {len(open_ports)} 个开放端口。")
    print(f"🚀 启动多线程并发验证（线程数: {CONCURRENT_WORKERS}），正在对撞测试...")

    # 2. 🌟 核心改进：引入线程池并发验证，让 300 多个端口速度飙升
    valid_proxies = []
    with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = [executor.submit(test_socks5_proxy, target_ip, port) for port in open_ports]
        
        for future in as_completed(futures):
            port, is_ok = future.result()
            if is_ok:
                print(f"🔥 [命中成功] 发现可用代理端口: {port}")
                valid_proxies.append(port)

    # 排序使列表整齐
    open_ports.sort()
    valid_proxies.sort()

    # 3. 🌟 重新设计排版：将可用端口和原始端口完美剥离输出
    msg_header = f"⏰ 【双重检测任务】扫描验证完成！\n目标主机: {target_ip}\n\n"
    
    # 💎 专区：高亮单独列出能够正常使用的代理链接
    msg_proxy_section = "🚀 【100% 可用代理链接清单】\n"
    if valid_proxies:
        for port in valid_proxies:
            msg_proxy_section += f"🔹 端口 {port} 可用：\n`https://t.me/socks?server={target_ip}&port={port}&user={USER}&pass={PASS}\n\n"
    else:
        msg_proxy_section += "🚫 本次扫描的 300+ 个端口中，未发现符合账号密码配置的可用代理。\n\n"

    # 📂 专区：紧凑列出服务器开放的所有端口，方便你做全量查阅
    ports_str = ", ".join([str(p) for p in open_ports])
    msg_raw_section = f"----------------------------------------\n📂 【全量开放端口查阅（共 {len(open_ports)} 个）】:\n`{ports_str}`"

    final_msg = msg_header + msg_proxy_section + msg_raw_section
    
    # 发送最终切片安全报告
    send_tg_message(final_msg)


if __name__ == "__main__":
    main()
