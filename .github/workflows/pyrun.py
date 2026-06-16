import os
import requests  # 确保导入了 requests 库

# 创建一个 session 对象
session = requests.Session()

# 你的 User-Agent
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"

# 设置请求头
headers = {
    "User-Agent": user_agent,
    "Referer": "https://x10hosting.com/login",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1"
}

# 从 GitHub Secrets 中安全读取 Cookies，如果没有配置则使用空字符串
xsrf_token = os.environ.get("XSRF_TOKEN", "你的 XSRF-TOKEN 值")
x10_session = os.environ.get("X10HOSTING_SESSION", "你的 x10hosting_session 值")

cookies = {
    "XSRF-TOKEN": xsrf_token,
    "x10hosting_session": x10_session
}

# 访问面板页面
response = session.get("https://x10hosting.com/panel", headers=headers, cookies=cookies)

# 检查是否成功访问
if response.status_code == 200:
    print("登录成功！x10hosting 保活成功。")
else:
    print(f"登录失败，状态码: {response.status_code}")
