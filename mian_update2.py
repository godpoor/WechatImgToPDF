import os
import time
import mimetypes
from urllib.parse import urlparse, parse_qs, urlunparse
from PyQt6.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup
import requests

class DownloadThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, folder):
        super().__init__()
        self.url = url
        self.folder = folder

    def run(self):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            }
            resp = requests.get(self.url, headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            img_tags = soup.find_all('img')

            for idx, img in enumerate(img_tags, start=1):
                raw_url = img.get('data-src') or img.get('src')
                if not raw_url:
                    continue

                # 清洗 URL，保留 wx_fmt 与 tp 参数
                img_url = self.clean_img_url(raw_url)

                # 发 GET 请求，获取二进制内容与响应头
                img_resp = requests.get(img_url, headers=headers)
                img_resp.raise_for_status()

                # 从 Content-Type 推断扩展名，fallback 到 URL 路径后缀或 .jpg
                content_type = img_resp.headers.get('Content-Type', '').split(';')[0]
                ext = mimetypes.guess_extension(content_type) \
                      or os.path.splitext(urlparse(img_url).path)[1] \
                      or '.jpg'

                filename = os.path.join(self.folder, f'{idx}{ext}')
                with open(filename, 'wb') as f:
                    f.write(img_resp.content)

                print(f"已下载: {filename}")
                time.sleep(0.5)

            self.finished.emit(self.folder)
        except Exception as e:
            self.error.emit(str(e))

    def clean_img_url(self, url: str) -> str:
        """
        仅保留 wx_fmt（格式）和 tp（类型）两个查询参数，
        以确保下载到正确的图片格式。
        """
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        allowed = {k: v[0] for k, v in qs.items() if k in ('wx_fmt', 'tp')}
        new_query = '&'.join(f"{k}={v}" for k, v in allowed.items())
        return urlunparse(parsed._replace(query=new_query))
