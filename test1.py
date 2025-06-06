import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QFileDialog,
    QHBoxLayout, QVBoxLayout, QInputDialog,QMessageBox
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

        # 在程序当前路径下创建名为“转换图像”的文件夹
        folder = os.path.join(os.getcwd(), "转换图像")
        if not os.path.exists(folder):
            os.makedirs(folder)

        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            img_tags = soup.find_all('img')
            for index, img in enumerate(img_tags, start=1):
                img_url = img.get('data-src') or img.get('src')
                if img_url:
                    try:
                        filename = os.path.join(folder, f'{index}.jpg')
                        img_data = requests.get(img_url).content
                        with open(filename, 'wb') as f:
                            f.write(img_data)
                        print(f"成功下载: {filename}")
                    except Exception as e:
                        print(f"无法下载图片 {img_url}: {e}")
             # 弹出提示框，通知图片下载完成
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)  # 修改这里
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
