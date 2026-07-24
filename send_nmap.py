import json
import os
import sys
import urllib.parse
import urllib.request

# 从 GitHub Secrets 读取敏感配置
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "").strip()
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "").strip()


def send_tg_message(text):
    """使用 Python 原生库安全发送 Telegram 消息"""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("❌ 未配置 TG 密钥，取消发送。")
        return

    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 200:
                print("─────── Telegram 报告发送成功！───────")
            else:
                print(f"❌ TG 发送失败，状态码: {response.status}")
    except Exception as e:
        print(f"❌ 发送 TG 时发生异常: {e}")


def main():
    # 读取 Nmap 刚刚扫描出来的结果文件
    scan_result_file = "nmap_report.txt"

    if not os.path.exists(scan_result_file):
        print("❌ 未找到扫描报告文件。")
        sys.exit(1)

    with open(scan_result_file, "r", encoding="utf-8") as f:
        report_content = f.read()

    # 在日志里打印一下，确保可见
    print("--- 扫描报告内容 ---")
    print(report_content)

    # 提取扫描报告中的关键开放端口信息（过滤无用行，使手机排版更好看）
    lines = report_content.split("\n")
    formatted_lines = []

    for line in lines:
        # 只提取包含 open 状态的端口行，或者包含统计的行
        if "open" in line or "Nmap done" in line or "scan report for" in line:
            formatted_lines.append(line)

    # 组装发送给手机的文本
    if formatted_lines:
        msg_header = "⏰ 【定时任务】服务器端口扫描完成！\n\n🎯 发现开放端口明细：\n"
        msg_body = "\n".join(formatted_lines)
        final_msg = msg_header + msg_body
    else:
        final_msg = "⏰ 定时端口扫描完成，但未成功解析到数据，请检查日志。"

    # 推送至 Telegram
    send_tg_message(final_msg)


if __name__ == "__main__":
    main()
