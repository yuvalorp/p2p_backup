from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog as FileDialog
from os import path
import ui_client
import sys
import logging
from json import loads

logger = logging.getLogger('peer_server')
#logger.setLevel(logging.INFO)


settings_path="settings.json"
settings_file=open(settings_path)
settings=loads(settings_file.read())
settings_file.close()
port=settings["host_port"]
ui_client.set_host('127.0.0.1', port)

if not ui_client.serv_exist():
    logger.critical('cant connect to the server please try again later')
    exit()
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        global c_path
        global selected_file


        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 750)
        font = QtGui.QFont()
        font.setPointSize(12)
        MainWindow.setFont(font)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.title = QtWidgets.QLabel(self.centralwidget)
        self.title.setGeometry(QtCore.QRect(20, 10, 281, 71))
        font.setPointSize(36)
        self.title.setFont(font)
        self.title.setTextFormat(QtCore.Qt.RichText)
        self.title.setScaledContents(False)
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        self.title.setWordWrap(False)
        self.title.setObjectName("title")

        self.path_display = QtWidgets.QPushButton(self.centralwidget)
        self.path_display.setGeometry(QtCore.QRect(20, 100, 700, 71))
        font.setPointSize(9)
        self.path_display.setFont(font)
        self.path_display.setObjectName("path_display")

        self.files_list_display = QtWidgets.QListWidget(self.centralwidget)
        self.files_list_display.setGeometry(QtCore.QRect(20, 200, 700, 400))
        self.files_list_display.setObjectName("files_list_display")
        self.files_list_display.itemClicked.connect(choose_file)#Double


        self.horizontalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(20, 620, 750, 80))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.back_but = QtWidgets.QPushButton(self.horizontalLayoutWidget)

        font.setPointSize(12)
        self.back_but.setFont(font)
        self.back_but.setObjectName("back_but")
        self.horizontalLayout.addWidget(self.back_but)
        self.open_but = QtWidgets.QPushButton(self.horizontalLayoutWidget)

        self.open_but.setFont(font)
        self.open_but.setObjectName("open_but")
        self.horizontalLayout.addWidget(self.open_but)

        self.del_but = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.del_but.setFont(font)
        self.del_but.setObjectName("del_but")
        self.horizontalLayout.addWidget(self.del_but)

        self.recover_but = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.recover_but.setObjectName("recover_but")
        self.horizontalLayout.addWidget(self.recover_but)

        self.create_but = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.create_but.setObjectName("create_but")
        self.horizontalLayout.addWidget(self.create_but)

        self.disconnect_but = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.disconnect_but.setObjectName("disconnect_but")
        self.horizontalLayout.addWidget(self.disconnect_but)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        global c_path
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.title.setText(_translate("MainWindow", "back2back"))
        self.path_display.setText(_translate("MainWindow", c_path))
        self.back_but.setText(_translate("MainWindow", "back"))
        self.open_but.setText(_translate("MainWindow", "open"))
        self.del_but.setText(_translate("MainWindow", "delete backup"))
        self.recover_but.setText(_translate("MainWindow", "recover"))
        self.create_but.setText(_translate("MainWindow", "create backup"))
        self.disconnect_but.setText(_translate("MainWindow", "disconnect"))

        self.del_but.clicked.connect(del_pack)
        self.back_but.clicked.connect(back)
        self.open_but.clicked.connect(open_dir)
        self.path_display.clicked.connect(choose_dir)
        self.create_but.clicked.connect(create_beckup)
        self.recover_but.clicked.connect(recover)
        self.disconnect_but.clicked.connect(disconnect)



c_path=r"C:\Users"
selected_file=r"C:\Users"
selected_file_stat="directory"
def main():
    global ex

    app = QtWidgets.QApplication(sys.argv)

    MainWindow=QtWidgets.QWidget()
    ex = Ui_MainWindow()
    ex.setupUi(MainWindow)
    show_dir()
    MainWindow.show()
    sys.exit(app.exec_())

def disconnect():
    qm = QtWidgets.QMessageBox
    qm.question(ex, '', f"Are you sure you want to disconect ", qm.Yes | qm.No)
    if qm.Yes:
        logger.info('disconecting')
        ui_client.disconect()
        exit()
def recover():
    global selected_file
    global selected_file_stat
    
    if selected_file_stat=='directory' or path.isdir(selected_file) :
        showDialog("error", "this is directory")
    elif selected_file_stat=='doesnt_backuped':
        showDialog("error", "the file doesnt have backup")
    else:
        recover(file_path)
        
def create_beckup():
    global selected_file
    global selected_file_stat
    global c_path
    global ex

    if not path.exists(selected_file):

        showDialog("error", "the file doesnt exist")
    
    elif selected_file_stat=='directory' or path.isdir(selected_file) :
        showDialog("error", "can becup only files not directorys")
    elif selected_file_stat=='backuped':
        showDialog("error", "the file have backup")
    else:
        ui_client.beckup_file(selected_file)

def back():
    global c_path
    global selected_file

    selected_file=c_path+""
    c_path=path.dirname(c_path)
    show_dir()

def del_pack():
    global selected_file
    global ex
    if not path.exists(selected_file):
        showDialog("error", "the file doesnt exist")
    elif selected_file_stat == 'directory' or path.isdir(selected_file):
        showDialog("error", "can becup only files not directorys")
    elif selected_file_stat != 'doesnt_backuped':
        showDialog("error", "their is a beckup for this file")
    else:
        qm=QtWidgets.QMessageBox
        qm.question(ex, '', f"Are you sure you want to del {selected_file}?", qm.Yes | qm.No)
        if qm.Yes:
            logger.info(f'delete {selected_file}')
            ui_client.del_file(selected_file)

def open_dir():
    global selected_file
    global c_path
    if path.isfile(path.join(selected_file)):
        showDialog("error", "you can open only directories ")
    else:
        c_path=selected_file+""
        show_dir()

def choose_file(item):
    global selected_file
    global selected_file_stat
    selected_file=item.text()
    selected_file = selected_file.split(" ")
    selected_file_stat=selected_file[-1]
    selected_file=selected_file[0]

def choose_dir():
    #item
    global c_path
    global ex
    global selected_file
    options = FileDialog.Options()
    options |= FileDialog.DontUseNativeDialog
    #fileName, _ = FileDialog.getOpenFileName(None, "QFileDialog.getOpenFileName()", "",
    #                                          "All Files (*);;Python Files (*.py)", options=options)
    fileName =  FileDialog.getExistingDirectory(None,"Choose Directory",c_path)
    if fileName!="":
        c_path=fileName+""
        selected_file=fileName+""
        show_dir()

def show_dir():
    global c_path
    global ex
    _translate = QtCore.QCoreApplication.translate

    ex.path_display.setText(_translate("MainWindow", c_path))

    files=ui_client.get_files_status(c_path)
    for a,b in files.items():
       print(a+'   '+b)
    print()
    ex.files_list_display.clear()
    ex.files_list_display.addItems([a+'   '+b for a,b in files.items()])
    ex.files_list_display.repaint()


def showDialog(title,mesege):
    msgBox = QtWidgets.QMessageBox()
    msgBox.setWindowTitle(title)
    msgBox.setText(mesege)
    msgBox.exec()

if __name__ == '__main__':
    main()







