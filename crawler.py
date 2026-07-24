from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import time
import requests

# 基础配置
TARGET_URL = os.getenv("MY_SERVERG", "")
MAX_WORKERS = 40  # 并发线程数

# 从 GitHub Secrets 读取敏感信息
USER = os.getenv("MY_USER", "abcd")
PASS = os.getenv("MY_PASS", "EfGh")

# Telegram 配置
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")


def check_port(port):
    """测试单个端口"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {
        "server": "42.194.173.209",
        "port": str(port),
        "user": USER,
        "pass": PASS,
    }

    try:
        response = requests.post(
            TARGET_URL, headers=headers, data=payload, timeout=5
        )
        if response.status_code == 200:
            res_json = response.json()
            # 核心判断：当且仅当 code 为 0 时判定为真正找到了正确端口
            if res_json.get("code") == 0:
                return port, res_json
        return port, None
    except Exception:
        return port, None


def send_tg_notification(message_text):
    """通过 Telegram Bot 发送纯文本通知（严格支持长文本自动切片）"""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("未配置 TG_BOT_TOKEN 或 TG_CHAT_ID，跳过 TG 通知。")
        return

    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN.strip()}/sendMessage"

    # TG 消息最大长度限制为 4096 字符，若超出则自动进行分段发送
    max_length = 4000
    message_chunks = [
        message_text[i : i + max_length] for i in range(0, len(message_text), max_length)
    ]

    for chunk in message_chunks:
        payload = {"chat_id": TG_CHAT_ID.strip(), "text": chunk}
        try:
            res = requests.post(url, json=payload, timeout=10)
            print(f"TG 发送状态码: {res.status_code}")
        except Exception as e:
            print(f"发送 TG 时发生网络异常: {e}")


def main():
    print(f"开始全量扫描端口 0-65535... 当前并发线程数: {MAX_WORKERS}")
    start_time = time.time()
    success_results = {}

    # 使用线程池并发执行
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_port, port): port for port in range(65536)}

        for count, future in enumerate(as_completed(futures), 1):
            port, success_data = future.result()
            if success_data:
                print(f"🎉 发现有效端口: {port}")
                success_results[port] = success_data

            if count % 5000 == 0:
                print(
                    f"已扫描 {count}/65536 个端口... 已耗时: {time.time() - start_time:.1f}秒"
                )

    print(f"\n扫描完成！总耗时: {time.time() - start_time:.2f} 秒。")

    # 🚀 在这里构建最终发送给 TG 的文本，根除“提示”被当作端口的 BUG
    if success_results:
        # 情况 A：真正找到了有效端口，组装详细的格式化排版
        msg_title = f"🔥 【警报】端口扫描发现有效数据！\n累计在全量范围内发现了 {len(success_results)} 个有效端口。\n\n"
        msg_body = ""
        for port, data in success_results.items():
            msg_body += "====================\n"
            msg_body += f"📍 开放端口: 【 {port} 】\n"
            msg_body += f"📄 详细 JSON 数据:\n{json.dumps(data, ensure_ascii=False, indent=2)}\n"
            msg_body += "====================\n\n"
        final_message = msg_title + msg_body
    else:
        # 情况 B：一个都没捞到，发送极其干净的报平安文本
        final_message = "⏰ 定时端口扫描完成！\n\n💡 本次全量扫描（0-65535）结束，未发现任何开放或匹配的目标端口。"

    # 将最终组装好的纯文本投递出去
    send_tg_notification(final_message)


if __name__ == "__main__":
    main()
