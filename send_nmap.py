import os
import re
import sys
import json
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

# 从 GitHub Secrets 读取敏感配置
USER = os.getenv("MY_USER", "abcd").strip()
PASS = os.getenv("MY_PASS", "EfGh").strip()
# 🎯 新增保底：直接把工作流里传进来的服务器 IP 也读取进来作为保底
FALLBACK_IP = os.getenv("MY_TARGET_IP", "").strip()

# 配置并发线程数
CONCURRENT_WORKERS = 50 


def test_socks5_proxy(server, port):
    """使用原生 socket 对单个端口进行高速 SOCKS5 代理登录和连通性验证"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        sock.connect((server, int(port)))

        # 1. 握手
        sock.sendall(b"\x05\x02\x00\x02")
        method_res = sock.recv(2)
        if not method_res or len(method_res) < 2 or (method_res[1] != 0x02 and method_res[1] != 0x00):
            sock.close()
            return port, False, None

        # 2. 密码认证
        if method_res[1] == 0x02:
            user_bytes = USER.encode('utf-8')
            pass_bytes = PASS.encode('utf-8')
            auth_packet = b"\x01" + bytes([len(user_bytes)]) + user_bytes + bytes([len(pass_bytes)]) + pass_bytes
            sock.sendall(auth_packet)
            auth_res = sock.recv(2)
            if not auth_res or len(auth_res) < 2 or auth_res[1] != 0x00:
                sock.close()
                return port, False, None

        # 3. 对撞测试
        dest_ip = socket.inet_aton("149.154.167.50")
        dest_port = (443).to_bytes(2, byteorder='big')
        connect_packet = b"\x05\x01\x00\x01" + dest_ip + dest_port
        sock.sendall(connect_packet)
        conn_res = sock.recv(10)
        sock.close()
        
        is_valid = conn_res and len(conn_res) >= 2 and conn_res[1] == 0x00
        tg_link = f"https://t.me/socks?server={server}&port={port}&user={USER}&pass={PASS}" if is_valid else None
        return port, is_valid, tg_link
    except Exception:
        return port, False, None


def main():
    scan_result_file = "nmap_report.txt"
    if not os.path.exists(scan_result_file):
        print("❌ 错误：未找到 Nmap 扫描报告文件。")
        sys.exit(1)

    with open(scan_result_file, "r", encoding="utf-8") as f:
        report_content = f.read()

    # 💡 Debug 强力打印：在日志里先印出 Nmap 报告的前 300 个字符，看看到底扫成功了没
    print("--- 🔍 Nmap 报告前瞻（Debug） ---")
    print(report_content[:300])
    print("---------------------------------")

    # 尝试解析 IP
    ip_match = re.search(r"scan report for ([\d\.]+)", report_content)
    
    if ip_match:
        target_ip = ip_match.group(1)
        print(f"✅ 成功从 Nmap 报告中解析到目标 IP: {target_ip}")
    else:
        # 🎯 核心改变：如果 Nmap 文本里没捞到，直接用环境变量传入的保底 IP，不再强制崩溃中断！
        if FALLBACK_IP:
            target_ip = FALLBACK_IP
            print(f"⚠️ Nmap 报告中未发现标准 IP 格式，已激活 Secrets 备用保底 IP: {target_ip}")
        else:
            print("❌ 错误：无法从报告中解析出目标 IP，且环境变量中的保底 IP 均为空！")
            sys.exit(1)

    # 提取所有开放端口
    open_ports = []
    lines = report_content.split("\n")
    for line in lines:
        if "open" in line and "/" in line:
            port_num = line.split("/")[0].strip()
            if port_num.isdigit():
                open_ports.append(int(port_num))

    print(f"📊 提取完成，开始并发测试 {len(open_ports)} 个开放端口的可用性...")

    valid_proxies = []
    proxy_links = []
    with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = [executor.submit(test_socks5_proxy, target_ip, port) for port in open_ports]
        for future in as_completed(futures):
            port, is_ok, tg_link = future.result()
            if is_ok:
                valid_proxies.append(port)
                proxy_links.append(tg_link)

    open_ports.sort()
    valid_proxies.sort()
    proxy_links.sort()

    final_report = {
        "scan_time": os.popen("date '+%Y-%m-%d %H:%M:%S'").read().strip(),
        "target_host": target_ip,
        "total_open_ports_count": len(open_ports),
        "total_valid_proxies_count": len(valid_proxies),
        "valid_proxy_links": proxy_links,
        "all_open_ports_list": open_ports
    }

    output_filename = "report.json"
    with open(output_filename, "w", encoding="utf-8") as json_file:
        json.dump(final_report, json_file, ensure_ascii=False, indent=4)
        
    print(f"🏁 扫描并验证完成！数据成功写入本地 {output_filename}")


if __name__ == "__main__":
    main()
