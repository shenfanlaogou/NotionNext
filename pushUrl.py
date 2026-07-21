import random
import re
import ssl
import time
from typing import List, Optional

import requests
import argparse

# 预编译正则表达式，避免重复编译
LOC_PATTERN = re.compile(r'<loc>(.*?)</loc>', re.DOTALL)

# 全局 SSL 上下文配置（仅配置一次）
ssl._create_default_https_context = ssl._create_unverified_context

# 创建会话对象，复用 TCP 连接
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (compatible; SitemapBot/1.0)',
    'Accept-Encoding': 'gzip, deflate',
})

# 请求超时设置（秒）
REQUEST_TIMEOUT = 30

# 每日推送限额，可根据实际情况修改
QUOTA = 100


def parse_sitemap(site: str) -> Optional[List[str]]:
    """解析 sitemap.xml 并提取所有 URL"""
    sitemap_url = f'{site}/sitemap.xml'
    try:
        response = session.get(sitemap_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        content = response.text
        # 使用预编译的正则表达式
        urls = LOC_PATTERN.findall(content)
        return urls if urls else None
    except requests.exceptions.RequestException as e:
        print(f'网络请求错误：{e}')
        print('请检查你的 url 是否有误。')
        print("正确的应是完整的域名，包含 https://，且不包含'sitemap.xml', 如下所示：")
        print('正确的示例：https://ghlcode.cn')
        print('详情参见：https://ghlcode.cn/fe032806-5362-4d82-b746-a0b26ce8b9d9')
        return None


def push_to_bing(site: str, urls: List[str], api_key: str) -> None:
    """批量推送 URL 到 Bing 搜索引擎"""
    endpoint = f"https://ssl.bing.com/webmaster/api.svc/json/SubmitUrlbatch?apikey={api_key}"

    payload = {
        "siteUrl": site,
        "urlList": urls
    }

    try:
        response = session.post(endpoint, json=payload, timeout=REQUEST_TIMEOUT)
        result = response.json()
        if response.status_code == 200:
            print("成功推送到 Bing.")
        elif "ErrorCode" in result:
            print("推送到 Bing 出现错误，错误信息为：", result["Message"])
    except requests.exceptions.RequestException as e:
        print(f"Bing 推送请求失败：{e}")
    except Exception as e:
        print(f"发生未知错误：{e}")


def push_to_baidu(site: str, urls: List[str], token: str) -> None:
    """批量推送 URL 到百度搜索引擎"""
    api_url = f"http://data.zz.baidu.com/urls?site={site}&token={token}"

    payload = "\n".join(urls)
    headers = {"Content-Type": "text/plain"}

    try:
        response = session.post(api_url, data=payload, headers=headers, timeout=REQUEST_TIMEOUT)
        result = response.json()
        if "success" in result and result["success"]:
            print("成功推送到百度.")
        elif "error" in result:
            print("推送到百度出现错误，错误信息为：", result["message"])
        else:
            print("百度返回未知响应：", result)
    except requests.exceptions.RequestException as e:
        print(f"百度推送请求失败：{e}")
    except Exception as e:
        print(f"发生未知错误：{e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='parse sitemap')
    parser.add_argument('--url', type=str, default=None, help='The url of your website')
    parser.add_argument('--bing_api_key', type=str, default=None, help='your bing api key')
    parser.add_argument('--baidu_token', type=str, default=None, help='Your baidu push token')
    args = parser.parse_args()

    # 获取当前的时间戳作为随机种子
    current_timestamp = int(time.time())
    random.seed(current_timestamp)

    if args.url:
        # 解析 urls
        urls = parse_sitemap(args.url)
        if urls is not None:
            # 判断当前 urls 数量是否超过额度，若超过则取当日最大值，默认为 100，可根据实际情况修改
            if len(urls) > QUOTA:
                urls = random.sample(urls, QUOTA)
            # 推送 bing
            if args.bing_api_key:
                print('正在推送至必应，请稍后……')
                push_to_bing(args.url, urls, args.bing_api_key)
            # 推送百度
            if args.baidu_token:
                print('正在推送至百度，请稍后……')
                push_to_baidu(args.url, urls, args.baidu_token)
    else:
        print('请前往 Github Action Secrets 配置 URL')
        print('详情参见：https://ghlcode.cn/fe032806-5362-4d82-b746-a0b26ce8b9d9')
