import sys
from PyQt5.QtCore import qAbs, QRect
from PyQt5.QtGui import QGuiApplication, QColor, QPen, QPainter
from PyQt5.QtWidgets import QApplication
import os
from PyQt5.QtCore import pyqtSlot, pyqtSignal,  QSize, Qt
from PyQt5.QtGui import QMovie, QPixmap, QIcon
from PyQt5.QtWidgets import QWidget, QFileDialog
from PyQt5 import QtCore, QtWidgets
from QCandyUi.CandyWindow import colorful
import ctypes

import json
import base64
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.ocr.v20181119 import ocr_client, models

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")

# 资源路径
screen_shot_icon_url = './asset/scissors.png'
open_file_icon_url = './asset/pic2.png'
open_files_icon_url = './asset/files.png'
loading_gif_url = './asset/loading.gif'

# 设置
min_after_shot = False
window_title = 'OCR-V1.0'

app_icon_url = './asset/com.ico'

"""
    ui_image2text.py
"""
class Ui_image2textWidget(object):
    def setupUi(self, image2textWidget):
        image2textWidget.setObjectName("image2textWidget")
        image2textWidget.resize(611, 330)
        self.verticalLayout = QtWidgets.QVBoxLayout(image2textWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.textEdit = QtWidgets.QTextEdit(image2textWidget)
        self.textEdit.setObjectName("textEdit")
        self.verticalLayout.addWidget(self.textEdit)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButtonCapture = QtWidgets.QPushButton(image2textWidget)
        self.pushButtonCapture.setMinimumSize(QtCore.QSize(31, 31))
        self.pushButtonCapture.setMaximumSize(QtCore.QSize(31, 31))
        self.pushButtonCapture.setObjectName("pushButtonCapture")
        self.horizontalLayout.addWidget(self.pushButtonCapture)
        self.pushButtonOpen = QtWidgets.QPushButton(image2textWidget)
        self.pushButtonOpen.setMinimumSize(QtCore.QSize(31, 31))
        self.pushButtonOpen.setMaximumSize(QtCore.QSize(31, 31))
        self.pushButtonOpen.setObjectName("pushButtonOpen")
        self.horizontalLayout.addWidget(self.pushButtonOpen)
        self.pushButtonOpenFile = QtWidgets.QPushButton(image2textWidget)
        self.pushButtonOpenFile.setMinimumSize(QtCore.QSize(31, 31))
        self.pushButtonOpenFile.setMaximumSize(QtCore.QSize(31, 31))
        self.pushButtonOpenFile.setObjectName("pushButtonOpenFile")
        self.horizontalLayout.addWidget(self.pushButtonOpenFile)
        spacerItem = QtWidgets.QSpacerItem(33, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(image2textWidget)
        QtCore.QMetaObject.connectSlotsByName(image2textWidget)

    def retranslateUi(self, image2textWidget):
        _translate = QtCore.QCoreApplication.translate
        image2textWidget.setWindowTitle(_translate("image2textWidget", "Form"))
        self.pushButtonCapture.setText(_translate("image2textWidget", "cap"))
        self.pushButtonOpen.setText(_translate("image2textWidget", "Open"))
        self.pushButtonOpenFile.setText(_translate("image2textWidget", "Files"))

"""
    screen_capture.py
"""
class CaptureScreen(QWidget):
    """
    截屏：使用时仅需要new一个该实例即可出现全屏的截屏界面
    """
    load_pixmap = None
    screen_width = None
    screen_height = None
    is_mouse_pressed = None
    begin_pos = None
    end_pos = None
    capture_pixmap = None
    painter = QPainter()
    signal_complete_capture = pyqtSignal(QPixmap)

    def __init__(self):
        QWidget.__init__(self)
        self.init_window()
        self.load_background_pixmap()
        self.setCursor(Qt.CrossCursor)
        self.show()

    def init_window(self):
        self.setMouseTracking(True)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowState(Qt.WindowActive | Qt.WindowFullScreen)

    def load_background_pixmap(self):
        # 截下当前屏幕的图像
        self.load_pixmap = QGuiApplication.primaryScreen().grabWindow(QApplication.desktop().winId())
        self.screen_width = self.load_pixmap.width()
        self.screen_height = self.load_pixmap.height()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_mouse_pressed = True
            self.begin_pos = event.pos()
        if event.button() == Qt.RightButton:
            self.close()
        return QWidget.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if self.is_mouse_pressed is True:
            self.end_pos = event.pos()
            self.update()
        return QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        self.end_pos = event.pos()
        self.is_mouse_pressed = False
        return QWidget.mouseReleaseEvent(self, event)

    def mouseDoubleClickEvent(self, event):
        if self.capture_pixmap is not None:
            self.signal_complete_capture.emit(self.capture_pixmap)
            self.close()

    def paintEvent(self, event):
        self.painter.begin(self)
        shadow_color = QColor(0, 0, 0, 100)  # 阴影颜色设置
        self.painter.setPen(QPen(Qt.blue, 1, Qt.SolidLine, Qt.FlatCap))  # 设置画笔
        self.painter.drawPixmap(0, 0, self.load_pixmap)  # 将背景图片画到窗体上
        self.painter.fillRect(self.load_pixmap.rect(), shadow_color)  # 画影罩效果
        if self.is_mouse_pressed:
            selected_rect = self.get_rect(self.begin_pos, self.end_pos)
            self.capture_pixmap = self.load_pixmap.copy(selected_rect)
            self.painter.drawPixmap(selected_rect.topLeft(), self.capture_pixmap)
            self.painter.drawRect(selected_rect)
        self.painter.end()  # 重绘结束

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.signal_complete_capture.emit(self.capture_pixmap)
            self.close()

    def get_rect(self, beginPoint, endPoint):
        width = qAbs(beginPoint.x() - endPoint.x())
        height = qAbs(beginPoint.y() - endPoint.y())
        x = beginPoint.x() if beginPoint.x() < endPoint.x() else endPoint.x()
        y = beginPoint.y() if beginPoint.y() < endPoint.y() else endPoint.y()
        selected_rect = QRect(x, y, width, height)
        # 避免宽或高为0时拷贝截图有误
        # 当选取截图宽或高为0时默认为2
        if selected_rect.width() == 0:
            selected_rect.setWidth(1)
        if selected_rect.height() == 0:
            selected_rect.setHeight(1)
        return selected_rect

# 对本地图片的base64加密
def ImageEncoder(image_path):
    with open(image_path, 'rb')as f:
        byte_data = base64.b64encode(f.read())
        str_data = bytes.decode(byte_data, encoding = 'utf-8')
        return str_data
def get_text(image_full_path):
    try:
        cred = credential.Credential("SecretId", "SecretKey")
        httpProfile = HttpProfile()
        httpProfile.endpoint = "ocr.tencentcloudapi.com"
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = ocr_client.OcrClient(cred, "ap-beijing", clientProfile)
        req = models.GeneralBasicOCRRequest()
        params = {
            "ImageBase64": ImageEncoder(image_full_path),
            "LanguageType": "auto"  # 自动识别语言
        }
        req.from_json_string(json.dumps(params))
        resp = client.GeneralBasicOCR(req)
        resp_data = resp.TextDetections
        # print(resp.to_json_string())
    #         for data in resp_data:
    #             Data.append(data.DetectedText)
    except:
        pass
    return resp_data


@colorful('blue')
class Image2Text(QWidget):
    signal_response = pyqtSignal(str)

    def __init__(self):
        QWidget.__init__(self)
        self.ui = Ui_image2textWidget()
        self.ui.setupUi(self)
        self.ui.textEdit.setAcceptDrops(False)
        self.ui.textEdit.setPlaceholderText("Welcome here!!!")
        self.setAcceptDrops(True)
        self.m_start()
        self.beautify_button(self.ui.pushButtonOpen, open_file_icon_url)
        self.beautify_button(self.ui.pushButtonCapture, screen_shot_icon_url)
        self.beautify_button(self.ui.pushButtonOpenFile, open_files_icon_url)

    # 美化按钮
    def beautify_button(self, button, image_url):
        button.setText('')
        button.setIcon(QIcon(image_url))
        icon_width = button.height() >> 1
        button.setIconSize(QSize(icon_width, icon_width))
        button.setFlat(True)

    def m_start(self):
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(QtCore.QRect(250, 0, 300, 300))
        self.label.setObjectName("label")
        self.gif = QMovie(loading_gif_url)
        self.label.setMovie(self.gif)
        self.gif.start()
        self.label.setVisible(False)

    @pyqtSlot()
    def on_pushButtonCapture_clicked(self):
        self.ui.textEdit.clear()
        self.capture = CaptureScreen()
        self.capture.signal_complete_capture.connect(self.slot_screen_capture)

    @pyqtSlot(QPixmap)
    def slot_screen_capture(self, image):
        self.label.setVisible(True)
        image.save('capture.jpg')
        try:
            result_data = get_text('capture.jpg')
            for data in result_data:
                self.ui.textEdit.append(data.DetectedText)
            os.remove('capture.jpg')
            self.label.setVisible(False)
        except:
            self.ui.textEdit.append("error!!!")

    @pyqtSlot()
    def on_pushButtonOpen_clicked(self):
        file_urls = QFileDialog.getOpenFileNames()[0]
        self.label.setVisible(True)
        if len(file_urls) > 0:
            self.ui.textEdit.clear()
        for img_full_path in file_urls:
            if img_full_path is None or img_full_path == '':
                continue
            self.ui.textEdit.append(img_full_path + ':')
            try:
                result_data = get_text(img_full_path)
                for data in result_data:
                    self.ui.textEdit.append(data.DetectedText)
                self.ui.textEdit.append('----------------------------')
            except:
                self.ui.textEdit.append("error!!!")
        self.label.setVisible(False)

    @pyqtSlot()
    def on_pushButtonOpenFile_clicked(self):
        self.ui.textEdit.clear()
        self.label.setVisible(True)
        file_dir = QFileDialog.getExistingDirectory(self, "选择图片文件夹", "./") # 选择图片存放路径
        file_dir = file_dir + '/'
        file_list = os.listdir(file_dir)
        for file_name in file_list:
            if file_name.endswith(".jpg") or file_name.endswith(".png"):
                try:
                    result_data = get_text(file_dir+file_name)
                    for data in result_data:
                        with open(file_dir + file_name.split('.')[0]+'.txt', 'a+', encoding = 'utf-8') as f:
                            f.write(data.DetectedText + '\n')
                except:
                    self.ui.textEdit.append("error!!!")
        self.ui.textEdit.append("文字识别完成!!!")
        self.label.setVisible(False)


def except_hook(cls, exception, traceback): # pqyt5出错时，显示信息
    sys.__excepthook__(cls, exception, traceback)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    imageFrame = Image2Text()
    imageFrame.setWindowTitle(window_title)
    imageFrame.setWindowIcon(QIcon(app_icon_url))
    imageFrame.show()
    sys.excepthook = except_hook
    sys.exit(app.exec_())
