import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QFileDialog,
    QHBoxLayout, QVBoxLayout
)
from PyQt6.QtGui import QClipboard
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QScreen
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
        # 获取屏幕尺寸并计算居中位置
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()

        # 将窗口的中心点移至屏幕中心
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())

    def process_clipboard(self):
        """
        从剪切板获取URL并抓取网页上的所有 img 标签，按序号保存为图片文件。
        支持 jpg、png、webp、gif 等格式。
        """
        clipboard = QApplication.clipboard()
        url = clipboard.text().strip()

        if not url:
            print('剪贴板为空或者不包含URL。')
            return

        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            img_tags = soup.find_all('img')

            if not img_tags:
                print('网页中未找到任何图片。')
                return

            save_folder = QFileDialog.getExistingDirectory(self, '选择保存图片的文件夹')
            if not save_folder:
                return

            count = 0
            for idx, img in enumerate(img_tags, start=1):
                img_url = img.get('src')
                if not img_url:
                    continue

                # 根据实际情况，补齐协议或相对路径
                if img_url.startswith('//'):
                    img_url = 'http:' + img_url
                elif img_url.startswith('/') or not img_url.startswith('http'):
                    img_url = os.path.join(url, img_url)

                # 获取图片后缀，若无则默认jpg
                ext = os.path.splitext(img_url)[-1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    ext = '.jpg'

                try:
                    img_data = requests.get(img_url).content
                    img_path = os.path.join(save_folder, f'{idx}{ext}')
                    with open(img_path, 'wb') as f:
                        f.write(img_data)
                    count += 1
                except Exception as e:
                    print(f'下载图片失败: {e}')

            print(f'已下载 {count} 张图片到文件夹: {save_folder}')

        except requests.RequestException as e:
            print(f'网络请求错误: {e}')
        except Exception as e:
            print(f'发生错误: {e}')

    def convert_images_to_pdf(self):
        """
        选择包含图片的文件夹，将其中的所有常见图片文件（jpg/jpeg/png/webp/gif）
        按照数字序号排序后合并成一个 PDF（使用 img2pdf）。
        """
        folder = QFileDialog.getExistingDirectory(self, '选择包含图片的文件夹')
        if not folder:
            return

        # 获取文件夹下所有可能的图片文件
        valid_exts = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
        images = [
            f for f in os.listdir(folder)
            if f.lower().endswith(valid_exts)
        ]

        # 按照文件名前的数字进行排序
        def sort_key(x):
            # 去掉后缀，转化为 int 用于排序
            name_without_ext, _ = os.path.splitext(x)
            try:
                return int(name_without_ext)
            except ValueError:
                # 如果转换失败，则返回原始字符串保证不报错
                return name_without_ext

        images.sort(key=sort_key)

        # 如果没有图片，直接返回
        if not images:
            print('该文件夹下没有可转换的图片。')
            return

        output_pdf = os.path.join(folder, 'output.pdf')

        # 使用 img2pdf 将多张图片合并为一个 PDF
        img_paths = [os.path.join(folder, img) for img in images]
        try:
            with open(output_pdf, 'wb') as f:
                f.write(img2pdf.convert(img_paths))
            print(f'PDF 文件已保存为: {output_pdf}')
        except Exception as e:
            print(f'合并图片时出错: {e}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = ImageProcessor()
    sys.exit(app.exec())
