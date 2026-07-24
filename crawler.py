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
            # 核心判断：当 code 为 0 时判定为正确端口
            if res_json.get("code") == 0:
                return port, res_json
        return port, None
    except Exception:
        return port, None


def send_tg_notification(results, is_safe_report=False):
    """通过 Telegram Bot 发送通知（严格格式化实际数据与平安报告）"""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("未配置 TG_BOT_TOKEN 或 TG_CHAT_ID，跳过 TG 通知。")
        return False

    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN.strip()}/sendMessage"

    if is_safe_report:
        # 情况 A：未发现任何有效端口，发送清爽的平安报告
        full_message = "⏰ 定时端口扫描完成！\n\n💡 本次全量扫描（0-65535）结束，未发现任何开放或匹配的目标端口。"
    else:
        # 情况 B：真正找到了有效端口，进行漂亮、详细的格式化排版
        header = f"🔥 【警报】端口扫描发现有效数据！\n累计在全量范围内发现了 {len(results)} 个有效端口。\n\n"
        content = ""
        for port, data in results.items():
            content += "====================\n"
            content += f"📍 开放端口: 【 {port} 】\n"
            content += f"📄 详细 JSON 数据:\n{json.dumps(data, ensure_ascii=False, indent=2)}\n"
            content += "====================\n\n"
        full_message = header + content

    # TG 消息最大长度限制为 4096 字符，若超出则自动进行分段发送
    max_length = 4000
    message_chunks = [
        full_message[i : i + max_length]
        for i in range(0, len(full_message), max_length)
    ]

    for chunk in message_chunks:
        payload = {"chat_id": TG_CHAT_ID.strip(), "text": chunk}
        try:
            res = requests.post(url, json=payload, timeout=10)
            print(f"TG 实际响应状态码: {res.status_code}")
        except Exception as e:
            print(f"发送 TG 时发生网络异常: {e}")
            return False
    return True


def main():
    print(f"开始全量扫描端口 0-65535... 当前并发线程数: {MAX_WORKERS}")
    start_time = time.time()
    success_results = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_port, port): port for port in range(65536)}

        for count, future in enumerate(as_completed(futures), 1):
            port, success_data = future.result()
            if success_data:
                print(f"🎉 发现有效端口: {port}")  # GitHub 侧只留极简日志
                success_results[port] = success_data

            if count % 5000 == 0:
                print(
                    f"已扫描 {count}/65536 个端口... 已耗时: {time.time() - start_time:.1f}秒"
                )

    print(f"\n扫描完成！总耗时: {time.time() - start_time:.2f} 秒。")

    # 根据是否抓到真实数据，走两条完全不同的通知通道
    if success_results:
        # 抓到了真家伙：直接把包含端口、详细 JSON 的字典扔进去
        send_tg_notification(success_results, is_safe_report=False)
    else:
        # 啥也没捞到：发送专门的报平安文案，不再统计字典数量
        send_tg_notification(None, is_safe_report=True)


if __name__ == "__main__":
    main()


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

            # 进度提示
            if count % 5000 == 0:
                print(
                    f"已扫描 {count}/65536 个端口... 已耗时: {time.time() - start_time:.1f}秒"
                )

    print(f"\n扫描完成！总耗时: {time.time() - start_time:.2f} 秒。")

    # 根据扫描结果发送通知
    if success_results:
        send_tg_notification(success_results)
    else:
        send_tg_notification({"提示": "本次扫描结束，未发现任何开放的目标端口。"})


if __name__ == "__main__":
    main()
