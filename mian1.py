#替换制定的网址，即可获取上面所有的图片



import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 设置目标文章链接
url = 'https://mp.weixin.qq.com/s/ht7WtFw5WsilxpQp0_OOfw'

# 设置请求头，模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
}

# 发送请求获取网页内容
response = requests.get(url, headers=headers)
response.raise_for_status()  # 如果请求失败，将抛出异常

# 解析网页内容
soup = BeautifulSoup(response.text, 'html.parser')

# 获取文章标题，并清理非法字符
title_tag = soup.find('h1')
title = title_tag.get_text(strip=True) if title_tag else 'wechat_article'
title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()

# 创建以标题命名的文件夹
folder_name = f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
os.makedirs(folder_name, exist_ok=True)

# 查找所有图片标签
img_tags = soup.find_all('img')

# 提取并下载图片
for idx, img in enumerate(img_tags, start=1):
    img_url = img.get('data-src')
    if img_url:
        # 获取图片格式
        img_format = img_url.split('=')[-1].split('&')[0]
        # 设置图片保存路径
        img_filename = os.path.join(folder_name, f'image_{idx}.{img_format}')
        # 下载并保存图片
        try:
            img_data = requests.get(img_url, headers=headers).content
            with open(img_filename, 'wb') as f:
                f.write(img_data)
            print(f"已保存图片：{img_filename}")
        except Exception as e:
            print(f"下载图片失败：{img_url}，错误信息：{e}")
