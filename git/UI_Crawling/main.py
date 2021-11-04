import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import QtCore
import natsort
import argparse
import copy
import cv2
import os
import glob
import time

parser = argparse.ArgumentParser(description='Wine Label Search Tool')
parser.add_argument('--save_high_folder', default='./high-definition/', type=str)
parser.add_argument('--save_no_high_folder', default='./no_high.txt', type=str)
parser.add_argument('--save_no_service_folder', default='./no_service.txt', type=str)
parser.add_argument('--save_service_folder', default='./service_db/', type=str)
args = parser.parse_args()


def make_list(img_paths,path):
    lists = []
    for i,img_path in enumerate(img_paths) :
        list = []
        list.append(img_path)
        name = os.path.basename(img_path).split(".")[0]
        crawlings = glob.glob( os.path.join(path,'*'+name+"_*.*"))
        crawling_path = []
        for j, crawling in enumerate(crawlings):
            max_and_path = []
            img = cv2.imread(crawling, cv2.IMREAD_UNCHANGED)
            try :
                h, w, c = img.shape
                if h > w :
                    max_len = h
                else :
                    max_len = w
                max_and_path.append(max_len)
                max_and_path.append(crawling)
                crawling_path.append(max_and_path)
            except Exception as e:
                pass
            crawling_path.sort(key=lambda x: x[0], reverse=True)
        for j, crawling in enumerate(crawling_path):
            list.append(crawling[1])
        lists.append(list)
    return lists


def list_files(in_path):
    img_files = []
    for (dirpath, dirnames, filenames) in os.walk(in_path):
        for file in filenames:
            filename, ext = os.path.splitext(file)
            ext = str.lower(ext)
            if ext == '.jpg' or ext == '.jpeg' or ext == '.gif' or ext == '.png' or ext == '.pgm':
                if len(filename.split("_")) == 2 :
                    img_files.append(os.path.join(dirpath, file))

    img_files = natsort.natsorted(img_files)
    return img_files

def min_resize(img, hmedian, wmedian):
    h, w = img.shape[:2]
    if h >= w:
        if h >= hmedian:
            interpolation = cv2.INTER_AREA
        else:
            interpolation = cv2.INTER_LANCZOS4
        nw = int(w * (hmedian / h))
        img = cv2.resize(img, (nw, hmedian), interpolation=interpolation)
    else:
        if w >= wmedian:
            interpolation = cv2.INTER_AREA
        else:
            interpolation = cv2.INTER_LANCZOS4
        nh = int(h * (wmedian / w))
        img = cv2.resize(img, (wmedian, nh), interpolation=interpolation)
    return img


class MyApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()
        self.single_save_list = []
        self.total_save_list = []
        self.total_save_list.append([])
        self.high_list = []
        self.service_list = []

        if os.path.isfile(args.save_no_high_folder):
            print("고화질 데이터가 없는 파일 리스트 존재")
            pass
        else :
            f = open(args.save_no_high_folder, 'w')
            f.close()
        if os.path.isfile(args.save_no_service_folder):
            print("서비스 데이터가 없는 파일 리스트 존재")
            pass
        else:
            f = open(args.save_no_service_folder, 'w')
            f.close()


    def flush_save_list(self):
        self.single_save_list = []


    def initUI(self):
        self.widget = QWidget(self)
        self.setWindowTitle('SAVE DB Tool')
        # 파일 리스트
        self.file_list = []
        self.cnt = 0
        self.max_cnt = 0

        # 검색창
        self.scrollArea_searching = QScrollArea()
        self.scrollArea_searching.setWidgetResizable(True)
        self.scrollArea_searching.setFixedWidth(1000)
        self.create_grid()


        # 프로그래스 바
        self.progress = QProgressBar(self)
        self.progress.setFixedSize(500, 10)
        self.progress.setAlignment(Qt.AlignCenter)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress_information = QLabel()

        # target
        self.scrollArea_query_img = QScrollArea()
        self.scrollArea_query_img.setFixedSize(500, 500)
        self.origin_size = QLabel()
        self.origin_name = QLabel()


        self.save_high_button = QPushButton('고화질 와인 저장 (단축키 command + s)')
        self.save_no_high_button = QPushButton('고하질 와인 없음 (단축키 command + x)')
        self.save_service_button = QPushButton('서비스 와인병 저장 (단축키 shift + s)')
        self.save_no_service_button = QPushButton('서비스 와인병 없음 (단축키 shift + x)')

        self.open_button = QPushButton('열기 (단축키 o)')
        self.prev_button = QPushButton('이전 (단축키 a)')
        self.next_button = QPushButton('다음 (단축키 d)')


        self.open_button.setShortcut('o')
        self.prev_button.setShortcut('a')
        self.next_button.setShortcut('d')

        self.prev_button.clicked.connect(self.prev)
        self.next_button.clicked.connect(self.next)
        self.open_button.clicked.connect(self.find_image_folder)
        self.save_high_button.clicked.connect(self.save_high_file)
        self.save_no_high_button.clicked.connect(self.save_no_high_file)
        self.save_service_button.clicked.connect(self.save_service_file)
        self.save_no_service_button.clicked.connect(self.save_no_service_file)

        # 저장 다이어로그
        self.dialog = QDialog()
        self.dialog.setWindowTitle('저장 결과')
        self.dialog.resize(300, 200)
        self.dialog_check = 0
        self.dialog_label = QLabel()
        self.dialog_label.setAlignment(Qt.AlignCenter)
        self.btnDialog = QPushButton("확인(단축키 Enter)")
        self.btnDialog.clicked.connect(self.dialog_close)
        DiadlogLayOut = QVBoxLayout()
        DiadlogLayOut.addWidget(self.dialog_label)
        DiadlogLayOut.addWidget(self.btnDialog)
        self.dialog.setLayout(DiadlogLayOut)

        # group box
        GroupTarget = QGroupBox()
        GroupContorl = QGroupBox()
        GroupSource = QGroupBox()
        GroupSave = QGroupBox()

        # left
        controlLayer = QHBoxLayout()
        controlLayer.addWidget(self.open_button)
        controlLayer.addWidget(self.prev_button)
        controlLayer.addWidget(self.next_button)
        GroupContorl.setLayout(controlLayer)

        leftInnerLayOut = QVBoxLayout()
        leftInnerLayOut.setSpacing(0)
        leftInnerLayOut.addWidget(self.origin_name)
        leftInnerLayOut.addWidget(self.scrollArea_query_img)
        leftInnerLayOut.addWidget(self.origin_size)
        leftInnerLayOut.addWidget(self.progress_information)
        leftInnerLayOut.addWidget(self.progress)
        leftInnerLayOut.setSpacing(0)
        leftInnerLayOut.addWidget(GroupContorl)
        leftInnerLayOut.setSpacing(0)
        GroupTarget.setLayout(leftInnerLayOut)

        # right
        saveLayer = QHBoxLayout()
        saveLayer.addWidget(self.save_high_button)
        saveLayer.addWidget(self.save_no_high_button)
        saveLayer.addWidget(self.save_service_button)
        saveLayer.addWidget(self.save_no_service_button)
        GroupSave.setLayout(saveLayer)
        rightInnerLayOut = QVBoxLayout()
        rightInnerLayOut.addWidget(self.scrollArea_searching)
        rightInnerLayOut.addWidget(GroupSave)
        GroupSource.setLayout(rightInnerLayOut)

        layout = QHBoxLayout()
        layout.addWidget(GroupTarget)
        layout.addWidget(GroupSource)

        self.widget.setLayout(layout)
        self.setCentralWidget(self.widget)
        self.setGeometry(0, 0, 1500 ,1000)
        self.show()


    def find_image_folder(self):
        self.file_list = []
        FileFolder = QFileDialog.getExistingDirectory(self, 'Find Folder')
        if len(FileFolder) != 0:
            img_paths = list_files(FileFolder)
            Files = make_list(img_paths,FileFolder)
            if len(Files) != 0:
                self.file_list = Files
                self.target_image_open()
        # if len(img_paths) > 10 :
        #     Files_upper50 = make_list(img_paths[10:],FileFolder)
        #     self.file_list = self.file_list + Files_upper50



    def next(self):
        if len(self.file_list) == 0 :
            return
        self.flush_save_list()
        if self.cnt == len(self.file_list) - 1:
            return
        else:
            self.cnt += 1
            if self.cnt > self.max_cnt:
                self.max_cnt = self.cnt
                list = []
                self.total_save_list.append(list)
            self.target_image_open()
        self.progress.setValue(int(((self.cnt + 1) / len(self.file_list)) * 100))
        self.set_progress()

    def prev(self):
        if len(self.file_list) == 0 :
            return
        self.flush_save_list()
        if self.cnt == 0 :
            return
        else:
            self.cnt -= 1
            self.target_image_open()
        self.progress.setValue(int(((self.cnt + 1) / len(self.file_list)) * 100))
        self.set_progress()

    def target_image_open(self):
        files = copy.deepcopy(self.file_list[self.cnt])
        self.query_img_path = files[0]
        self.query_img = cv2.imread(files[0], cv2.IMREAD_UNCHANGED)
        query_img =  copy.deepcopy(self.query_img)
        self.origin_name.setText(os.path.basename(files[0]).split(".")[0])
        h, w, c = query_img.shape
        self.origin_size.setText("width : " + str(w) + " height : " + str(h))
        query_img = cv2.cvtColor(query_img, cv2.COLOR_BGR2RGB)
        query_img = cv2.rectangle(query_img, (0, 0), (w - 1, h - 1), (255, 0, 0), 10)
        query_img = min_resize(query_img,500,500)
        h_resize, w_resize, c_resize = query_img.shape
        bytesPerLine = 3 * w_resize
        qImg = QImage(query_img.data, w_resize,  h_resize, bytesPerLine, QImage.Format_RGB888)
        pixmap = QPixmap(qImg)
        self.pixLabel_query_img = ClickableLabel(parent=self, pixmap=pixmap, name='image', path=self.query_img_path,check=0, crawling= False)
        self.pixLabel_query_img.setAlignment(Qt.AlignCenter)
        self.scrollArea_query_img.setWidget(self.pixLabel_query_img)
        self.query_img_path = files[0]
        self.load_search_result(files[1:])


    def load_search_result(self,index_list):
        self.flush_search_result_grid()
        for i in range(0, len(index_list)):
            img = cv2.imread(index_list[i], cv2.IMREAD_UNCHANGED )
            h, w, c = img.shape
            img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
            img = cv2.rectangle(img, (0, 0), (w - 1, h - 1), (255, 0, 0),10)
            img = min_resize(img, 400, 400)
            h_resize, w_resize, c_resize = img.shape
            bytesPerLine = 3 * w_resize
            qImg = QImage(img.data, w_resize, h_resize, bytesPerLine, QImage.Format_RGB888)
            pixmap = QPixmap(qImg)
            if index_list[i] in self.total_save_list[self.cnt] :
                pixLabel = ClickableLabel(parent=self, pixmap=pixmap, name='image', path=index_list[i], check=1)
            else :
                pixLabel = ClickableLabel(parent=self, pixmap=pixmap, name='image', path=index_list[i], check=0)
            scrollArea_img = QScrollArea()
            scrollArea_img.setWidgetResizable(True)
            scrollArea_img.setFixedSize(400,400)
            pixLabel.setAlignment(Qt.AlignCenter)
            scrollArea_img.setWidget(pixLabel)
            name = QLabel()#.setFixedHeight(20)
            size = QLabel()#.setFixedHeight(20)
            size.setText( "width : " + str(w) + " height : " + str(h))
            name.setText(os.path.basename(index_list[i]).split(".")[0])
            label_crawling= QVBoxLayout()
            label_crawling.addWidget(name)
            label_crawling.setSpacing(0)
            label_crawling.addWidget(scrollArea_img)
            label_crawling.setSpacing(0)
            label_crawling.addWidget(size)
            GroupLabel = QGroupBox()
            GroupLabel.setLayout(label_crawling)
            self.gridLayout_searching.addWidget(GroupLabel, 0, i)
            if len(index_list) == 1 or len(index_list) == i:
                return


    def flush_search_result_grid(self):
        for i in reversed(range(self.gridLayout_searching.count())):
            self.gridLayout_searching.itemAt(i).widget().deleteLater()


    def create_grid(self): # search
        self.scrollAreaWidgetContents = QWidget(self)
        self.gridLayout_searching = QGridLayout(self.scrollAreaWidgetContents)
        self.scrollArea_searching.setWidget(self.scrollAreaWidgetContents)


    def save_high_file(self):
        try:
            single_path  = self.single_save_list

            print('---------------')
            print('single_paths : ',  single_path)
            print('---------------')

            # save positive samples
            basename = os.path.basename(self.query_img_path)
            fn, ext = basename.split('.')
            os.makedirs(args.save_high_folder, exist_ok=True)
            # save negative samples
            if len(single_path) == 1:
                path = single_path[0]
                save_img = cv2.imread(path)
                new_name = fn + '.' + "png"
                cv2.imwrite(os.path.join(args.save_high_folder,  new_name), save_img)
                #print("new DB", os.path.join(args.save_high_folder, new_name))
                self.dialog_open("고화질 이미지 저장 완료")
                self.total_save_list[self.cnt] = single_path
                self.remove_text(mode="high")
                self.high_list.append(fn)
            elif len(single_path) == 0 :
                self.dialog_open("저장할 고화질 이미지를 선택하지 않았습니다.")
            else:
                self.dialog_open("저장할 고화질 이미지를 하나만 선택하세요.")
        except Exception as e:
            print(e)
            pass


    def save_no_high_file(self):
        try:
            basename = os.path.basename(self.query_img_path)
            fn, ext = basename.split('.')
            if fn in self.high_list:
                self.dialog_open("고화질 이미지를 이미 저장했습니다.")
                return
            check_list = self.in_text(mode="high")
            if not check_list:
                with open(args.save_no_high_folder, "a") as file:
                    file.write(fn + "\n")
                    file.close()
                self.dialog_open("고화질 이미지가 없는 리스트 저장완료")
            else:
                self.dialog_open("고화질 이미지가 없는 리스트에 이미 있습니다.")
                pass
        except:
            pass


    def save_service_file(self):
        try:
            single_path = self.single_save_list
            print('---------------')
            print('single_paths : ', single_path)
            print('---------------')
            # save positive samples
            basename = os.path.basename(self.query_img_path)
            fn, ext = basename.split('.')
            os.makedirs(args.save_service_folder, exist_ok=True)
            # save negative samples
            if len(single_path) == 1:
                path = single_path[0]
                save_img = cv2.imread(path)
                new_name = fn + '.' + "png"
                cv2.imwrite(os.path.join(args.save_service_folder, new_name), save_img)
                self.dialog_open("서비스 이미지 저장 완료")
                self.total_save_list[self.cnt] = single_path
                self.remove_text(mode= "service")
                self.service_list.append(fn)
            elif len(single_path) == 0:
                self.dialog_open("저장할 서비스 이미지를 선택하지 않았습니다.")
            else:
                self.dialog_open("저장할 서비스 이미지를 하나만 선택하세요.")
        except Exception as e:
            print(e)
            pass

    def save_no_service_file(self):
        try:
            basename = os.path.basename(self.query_img_path)
            fn, ext = basename.split('.')
            if fn in self.service_list:
                self.dialog_open("서비스 이미지를 이미 저장했습니다.")
                return
            check_list = self.in_text(mode= "service")
            if not check_list:
                with open(args.save_no_service_folder, "a") as file:
                    file.write(fn + "\n")
                    file.close()
                self.dialog_open("서비스 이미지가 없는 리스트 저장완료")
            else :
                self.dialog_open("서비스 이미지가 없는 리스트에 이미 있습니다.")
                pass
        except:
            pass

    def in_text(self, mode):
        try :
            basename = os.path.basename(self.query_img_path)
            fn, _ = basename.split('.')
            fn = fn+"\n"
            if mode == "high":
                path = args.save_no_high_folder
            elif mode == "service":
                path = args.save_no_service_folder
            else :
                return False
            file = open(path, "r")
            strings = file.readlines()
            file.close()
            if fn in strings:
                return True
            else :
                return False
        except :
            pass

    def remove_text(self, mode):
        basename = os.path.basename(self.query_img_path)
        fn, _ = basename.split('.')
        fn = fn + "\n"
        try :
            if mode == "high":
                path = args.save_no_high_folder
            elif mode == "service":
                path = args.save_no_service_folder
            else:
                return
            file = open(path, "r")
            strings = file.readlines()
            file.close()
            file = open(path, "w")
            for string in strings:
                if str(string) != str(fn) :
                    file.write(str(string))
            file.close()
        except:
            pass


    def keyPressEvent(self,e):
        if e.modifiers() == QtCore.Qt.ControlModifier and  e.key() == QtCore.Qt.Key_S :
            if len(self.file_list) == 0 :
                return
            self.save_high_file()

        if e.modifiers() == QtCore.Qt.ControlModifier and  e.key() == QtCore.Qt.Key_X :
            self.save_no_high_file()

        if e.modifiers() == QtCore.Qt.ShiftModifier and  e.key() == QtCore.Qt.Key_S :
            if len(self.file_list) == 0 :
                return
            self.save_service_file()
        if e.modifiers() == QtCore.Qt.ShiftModifier and e.key() == QtCore.Qt.Key_X:
            self.save_no_service_file()

        if e.key() == QtCore.Qt.Key_Enter and self.dialog_check:
            self.dialog_close()


    def dialog_open(self, text):
        self.dialog_check = 1
        # 버튼 추가
        self.dialog_label.clear()
        self.dialog_label.setText(text)

        # QDialog 세팅
        self.dialog.setWindowModality(Qt.ApplicationModal)
        self.dialog.show()

    def dialog_close(self):
        self.dialog_check = 0
        self.dialog.close()

    def set_progress(self):
        self.progress_information.setText(str(self.cnt+1) + " / " + str(len(self.file_list)) )

class ClickableLabel(QLabel):
    def __init__(self, parent, pixmap ,name,  path ,check, crawling = True ):
        super().__init__(name)
        self._parent = parent
        self.pixmap = pixmap
        self.check = check
        self.zoom = 1
        self.path = path
        self.crawling = crawling
        if check :
            self.setStyleSheet(
                "color: #41E881; border-style: solid; border-width: 2px; border-color: #67E841; ")
            self._parent.single_save_list.append(self.path)
        else:
            self.setStyleSheet("")

        self.width = int(self.pixmap.width())
        self.height = int(self.pixmap.height())
        self.set_image()


    def mousePressEvent(self, e):
        if ((e.buttons() == Qt.LeftButton) or (e.buttons() == Qt.RightButton)) and self.crawling  :
            self.select_image()


    def select_image(self):
        try:
            if self.check == 0:
                self.setStyleSheet(
                    "color: #41E881; border-style: solid; border-width: 2px; border-color: #67E841; ")
                self.check = 1
                self._parent.single_save_list.append(self.path)
            else:
                self.setStyleSheet("")
                self.check = 0
                self._parent.single_save_list.remove(self.path)
        except Exception as e:
            print(e)


    def wheelEvent(self, e):
        self.zoom += e.angleDelta().y() / 2800
        self.set_image()


    def set_image(self):
        if self.crawling:
            if self.width > self.height:
                pixmap = self.pixmap.scaledToWidth(self.zoom * 400, mode=Qt.SmoothTransformation)
            else:
                pixmap = self.pixmap.scaledToHeight(self.zoom * 400, mode=Qt.SmoothTransformation)
            self.setPixmap(pixmap)
        else :
            if self.width > self.height:
                pixmap = self.pixmap.scaledToWidth(self.zoom * 500, mode=Qt.SmoothTransformation)
            else:
                pixmap = self.pixmap.scaledToHeight(self.zoom * 500, mode=Qt.SmoothTransformation)
            self.setPixmap(pixmap)




if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())