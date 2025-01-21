# 将微信客户端的图片全部保存下来

import os
import requests
from bs4 import BeautifulSoup

# 创建文件夹
if not os.path.exists('test'):
    os.makedirs('test')

url = "https://mp.weixin.qq.com/s/OwxHW9-N2SINtFPIGVAh-w"  # 网页 URL
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# 查找所有图片标签
images = soup.find_all('img')

# 下载图片并保存到文件夹
for index, img in enumerate(images, start=1):
    img_url = img.get('data-src') or img.get('src')  # 获取图片 URL
    if img_url:
        try:
            # 生成文件名，使用序号.JPG
            filename = os.path.join('test', f'{index}.jpg')

            # 下载图片并保存
            img_data = requests.get(img_url).content
            with open(filename, 'wb') as f:
                f.write(img_data)
            print(f"成功下载: {filename}")
        except Exception as e:
            print(f"无法下载图片 {img_url}: {e}")

print("所有图片下载完成。")
