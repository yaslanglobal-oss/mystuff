import os
import re
import sys
import json
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

# 从 GitHub Secrets 读取敏感配置
USER = os.getenv("MY_USER", "abcd").strip()
PASS = os.getenv("MY_PASS", "EfGh").strip()

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
        if not method_res or method_res[1] != 0x02 and method_res[1] != 0x00:
            sock.close()
            return port, False, None

        # 2. 密码认证
        if method_res[1] == 0x02:
            user_bytes = USER.encode('utf-8')
            pass_bytes = PASS.encode('utf-8')
            auth_packet = b"\x01" + bytes([len(user_bytes)]) + user_bytes + bytes([len(pass_bytes)]) + pass_bytes
            sock.sendall(auth_packet)
            auth_res = sock.recv(2)
            if not auth_res or auth_res[1] != 0x00:
                sock.close()
                return port, False, None

        # 3. 对撞测试：尝试连接 Telegram 核心服务器 IP
        dest_ip = socket.inet_aton("149.154.167.50")
        dest_port = (443).to_bytes(2, byteorder='big')
        connect_packet = b"\x05\x01\x00\x01" + dest_ip + dest_port
        sock.sendall(connect_packet)
        conn_res = sock.recv(10)
        sock.close()
        
        # 真正可用的代理通道
        is_valid = conn_res and conn_res[1] == 0x00
        
        # 如果可用，顺便生成快捷订阅链接
        tg_link = f"https://t.me{server}&port={port}&user={USER}&pass={PASS}" if is_valid else None
        return port, is_valid, tg_link
    except Exception:
        return port, False, None


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

    # 提取所有开放端口
    open_ports = []
    lines = report_content.split("\n")
    for line in lines:
        if "open" in line and "/" in line:
            port_num = line.split("/")[0].strip()
            if port_num.isdigit():
                open_ports.append(int(port_num))

    print(f"📊 Nmap 扫描完成！开放端口共 {len(open_ports)} 个。开始并发测试可用性...")

    # 多线程并发验证
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

    # 🎯 核心改变：不再打包发给 TG，而是组装成结构规范的 JSON 结果字典
    final_report = {
        "scan_time": os.popen("date '+%Y-%m-%d %H:%M:%S'").read().strip(),
        "target_host": target_ip,
        "total_open_ports_count": len(open_ports),
        "total_valid_proxies_count": len(valid_proxies),
        "valid_proxy_links": proxy_links,
        "all_open_ports_list": open_ports
    }

    # 将结果写入本地 report.json 文件中，等待工作流将其搬运走
    output_filename = "report.json"
    with open(output_filename, "w", encoding="utf-8") as json_file:
        json.dump(final_report, json_file, ensure_ascii=False, indent=4)
        
    print(f"🏁 扫描并验证完成！数据成功写入本地 {output_filename} 文件。")


if __name__ == "__main__":
    main()
