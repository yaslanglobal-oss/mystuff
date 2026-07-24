import json
import os
import sys
import urllib.request


def send_tg_message(token, chat_id, text):
    """安全发送 Telegram 消息"""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
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


def main():
    # 从命令行获取当前属于哪个阶段 (例如: stage1, stage2)
    stage = sys.argv[1] if len(sys.argv) > 1 else "stage1"

    token = os.getenv("TG_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TG_CHAT_ID", "").strip()

    scan_result_file = "nmap_report.txt"
    if not os.path.exists(scan_result_file):
        print("❌ 未找到扫描报告文件。")
        sys.exit(1)

    with open(scan_result_file, "r", encoding="utf-8") as f:
        report_content = f.read()

    # 提取开放端口行
    lines = report_content.split("\n")
    formatted_lines = []
    for line in lines:
        if "open" in line or "Nmap done" in line or "scan report for" in line:
            formatted_lines.append(line)

    # 根据不同的阶段配置不同的 TG 提示文案
    if stage == "stage1":
        msg_header = "⚡ 【第一阶段】常用端口（Top 1000）快扫完成！\n程序正在后台继续扫描剩余高位端口...\n\n🎯 当前发现开放端口：\n"
    else:
        msg_header = (
            "🏁 【第二阶段】高位端口（1001-65535）全量扫描完成！\n\n🎯 发现开放端口：\n"
        )

    msg_body = "\n".join(formatted_lines) if formatted_lines else "未发现任何开放端口"
    final_msg = msg_header + msg_body

    send_tg_message(token, chat_id, final_msg)


if __name__ == "__main__":
    main()
