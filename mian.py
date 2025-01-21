import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QVBoxLayout
from PyQt6.QtGui import QClipboard, QPixmap
from bs4 import BeautifulSoup
import requests
from PyPDF2 import PdfMerger

class ImageProcessor(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Clipboard Image Processor')
        self.setGeometry(100, 100, 600, 400)
        
        layout = QVBoxLayout()

        self.clipboard_button = QPushButton('Read Clipboard and Save Images', self)
        self.clipboard_button.clicked.connect(self.process_clipboard)
        layout.addWidget(self.clipboard_button)

        self.folder_button = QPushButton('Convert Images to PDF', self)
        self.folder_button.clicked.connect(self.convert_images_to_pdf)
        layout.addWidget(self.folder_button)

        self.setLayout(layout)

    def process_clipboard(self):
        clipboard = QApplication.clipboard()
        url = clipboard.text()
        if not url:
            print('Clipboard is empty or does not contain a URL')
            return

        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            img_tags = soup.find_all('img')
            save_folder = QFileDialog.getExistingDirectory(self, 'Select Folder to Save Images')
            if not save_folder:
                return

            for idx, img in enumerate(img_tags, start=1):
                img_url = img.get('src')
                if img_url.startswith('//'):
                    img_url = 'http:' + img_url
                elif not img_url.startswith('http'):
                    img_url = url + img_url
                
                img_data = requests.get(img_url).content
                img_path = os.path.join(save_folder, f'{idx}.jpg')
                with open(img_path, 'wb') as f:
                    f.write(img_data)
            print(f'Images saved to {save_folder}')
        except Exception as e:
            print(f'Error: {e}')

    def convert_images_to_pdf(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder Containing Images')
        if not folder:
            return

        images = [f for f in os.listdir(folder) if f.lower().endswith(('jpg', 'jpeg'))]
        images.sort(key=lambda x: int(os.path.splitext(x)[0]))  # Sort numerically

        merger = PdfMerger()
        for img in images:
            img_path = os.path.join(folder, img)
            merger.append(img_path)

        output_pdf = os.path.join(folder, 'output.pdf')
        merger.write(output_pdf)
        merger.close()
        print(f'PDF saved as {output_pdf}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageProcessor()
    ex.show()
    sys.exit(app.exec())
