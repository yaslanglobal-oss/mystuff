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


def send_tg_notification(results):
    """通过 Telegram Bot 发送通知（带长文本切片防护与严格变量校验）"""
    # 🌟 增强校验：防止变量为空或未读到
    if not TG_BOT_TOKEN or TG_BOT_TOKEN.strip() == "":
        print("❌ 错误：未读取到有效的 TG_BOT_TOKEN，请检查 GitHub Secrets 配置！")
        return
    if not TG_CHAT_ID or TG_CHAT_ID.strip() == "":
        print("❌ 错误：未读取到有效的 TG_CHAT_ID，请检查 GitHub Secrets 配置！")
        return

    # 正确拼接 URL，确保没有多余的斜杠或星号
    url = f"https://telegram.org{TG_BOT_TOKEN.strip()}/sendMessage"

    # 构建纯文本格式的内容
    header = f"⏰ 端口扫描完成！\n共发现 {len(results)} 个有效端口。\n\n"
    content = ""
    for port, data in results.items():
        if port != "提示":
            content += f"📍 端口 {port}:\n{json.dumps(data, ensure_ascii=False, indent=2)}\n\n"
        else:
            content += f"💡 {data}\n"

    full_message = header + content

    # TG 消息最大长度限制为 4096 字符，若超出则自动进行分段发送
    max_length = 4000
    message_chunks = [
        full_message[i:i+max_length] 
        for i in range(0, len(full_message), max_length)
    ]

    for chunk in message_chunks:
        payload = {
            "chat_id": TG_CHAT_ID.strip(),
            "text": chunk
        }
        try:
            # 打印实际请求的脱敏 URL 方便排查
            print(f"正在尝试发送消息到 TG，接口地址: https://telegram.org[已隐藏].../sendMessage")
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                print("─────── Telegram 消息发送成功！───────")
            else:
                print(f"❌ Telegram 服务器拒绝，状态码: {res.status_code}, 原因: {res.text}")
                print("💡 提示：如果提示 chat not found，说明你还没有在 TG 里面关注并 [/start] 你的机器人！")
        except Exception as e:
            print(f"❌ 发送 TG 通知时发生网络异常: {e}")



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
