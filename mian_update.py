import sys
import os
import time
import mimetypes
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QFileDialog,
    QHBoxLayout, QVBoxLayout, QInputDialog, QMessageBox
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from bs4 import BeautifulSoup
import requests
import img2pdf
from urllib.parse import urlparse, parse_qs, urlunparse


class DownloadThread(QThread):
    finished = pyqtSignal(str)  # 下载完成信号，参数为文件夹路径
    error = pyqtSignal(str)     # 错误信号

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

    def clean_img_url(self, url):
        # old version
        # parsed = urlparse(url)
        # query = parse_qs(parsed.query)
        # allowed = {k: v for k, v in query.items() if k in ('wx_fmt',)}
        # new_query = '&'.join(f"{k}={v[0]}" for k, v in allowed.items())
        # return urlunparse(parsed._replace(query=new_query))

        # new version
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        allowed = {k: v[0] for k, v in qs.items() if k in ('wx_fmt', 'tp')}
        new_query = '&'.join(f"{k}={v}" for k, v in allowed.items())
        return urlunparse(parsed._replace(query=new_query))

class ImageProcessor(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        self.setWindowTitle('转换器')
        self.setFixedSize(400, 200)
        self.setWindowIcon(QIcon("1.ico"))  # 设置窗口图标

        self.setWindowTitle('转换器')
        self.setFixedSize(400, 200)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)


        button_layout = QHBoxLayout()
        button_layout.setSpacing(40)

        self.clipboard_button = QPushButton('保存图片', self)
        self.clipboard_button.clicked.connect(self.process_clipboard)
        button_layout.addWidget(self.clipboard_button)

        self.folder_button = QPushButton('转成PDF', self)
        self.folder_button.clicked.connect(self.convert_images_to_pdf)
        button_layout.addWidget(self.folder_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        self.center_window()
        self.show()

        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        self.show()

    def center_window(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())

    def process_clipboard(self):
        clipboard = QApplication.clipboard()
        url = clipboard.text().strip()
        if not url:
            print("剪贴板为空或不包含URL")
            return

        folder = os.path.join(os.getcwd(), "转换图像")
        os.makedirs(folder, exist_ok=True)

        self.thread = DownloadThread(url, folder)
        self.thread.finished.connect(self.on_download_finished)
        self.thread.error.connect(self.on_download_error)
        self.clipboard_button.setEnabled(False)
        self.clipboard_button.setText("下载中...")
        self.thread.start()

    def on_download_finished(self, folder):
        self.clipboard_button.setEnabled(True)
        self.clipboard_button.setText("保存图片")
        msg = QMessageBox(self)
        msg.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(f"所有图片下载完成！\n保存路径：{folder}")
        msg.setWindowTitle("下载完成")
        msg.exec()

    def on_download_error(self, error_msg):
        self.clipboard_button.setEnabled(True)
        self.clipboard_button.setText("保存图片")
        msg = QMessageBox(self)
        msg.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText(f"下载出错：\n{error_msg}")
        msg.setWindowTitle("错误")
        msg.exec()

    def convert_images_to_pdf(self):
        folder = QFileDialog.getExistingDirectory(self, '选择包含图片的文件夹')
        if not folder:
            return

        valid_exts = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
        images = [
            f for f in os.listdir(folder)
            if f.lower().endswith(valid_exts)
        ]

        def sort_key(x):
            name_without_ext, _ = os.path.splitext(x)
            try:
                return int(name_without_ext)
            except ValueError:
                return name_without_ext

        images.sort(key=sort_key)

        if not images:
            print('该文件夹下没有可转换的图片。')
            return

        pdf_path, _ = QFileDialog.getSaveFileName(self, '保存PDF文件', os.path.join(folder, '转换图像.pdf'), "PDF Files (*.pdf)")
        if not pdf_path:
            return

        img_paths = [os.path.join(folder, img) for img in images]
        try:
            with open(pdf_path, 'wb') as f:
                f.write(img2pdf.convert(img_paths))
            print(f'PDF 文件已保存为: {pdf_path}')
        except Exception as e:
            print(f'合并图片时出错: {e}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = ImageProcessor()
    sys.exit(app.exec())
