import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QFileDialog,
    QHBoxLayout, QVBoxLayout, QInputDialog,QMessageBox
)

from bs4 import BeautifulSoup
import requests
import img2pdf  # 用于把多张图片合并为 PDF


class ImageProcessor(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('转换器')
        self.setFixedSize(400, 200)

        # --- 布局部分 ---
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

        # --- 将窗口移动到屏幕中心 ---
        self.center_window()

        # 显示窗口
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
            print('剪贴板为空或者不包含URL。')
            return

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # # 获取文章标题作为子目录名
            # title_tag = soup.find('h1')
            # title = title_tag.get_text(strip=True) if title_tag else 'wechat_article'
            # title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()

            # 创建文件夹（转换图像/标题_时间）
            from datetime import datetime
            folder = os.path.join(os.getcwd(), "转换图像")
            # folder_name = f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            # folder = os.path.join(folder_root, folder_name)
            os.makedirs(folder, exist_ok=True)

            img_tags = soup.find_all('img')
            for index, img in enumerate(img_tags, start=1):
                img_url = img.get('data-src') or img.get('src')
                if img_url:
                    try:
                        # 根据链接尾部格式生成扩展名
                        img_format = img_url.split('=')[-1].split('&')[0]
                        filename = os.path.join(folder, f'{index}.{img_format}')
                        img_data = requests.get(img_url, headers=headers).content
                        with open(filename, 'wb') as f:
                            f.write(img_data)
                        print(f"成功下载: {filename}")
                    except Exception as e:
                        print(f"无法下载图片 {img_url}: {e}")

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText("所有图片下载完成！")
            msg.setWindowTitle("下载完成")
            msg.exec()

        except requests.RequestException as e:
            print(f'网络请求错误: {e}')
        except Exception as e:
            print(f'发生错误: {e}')

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
