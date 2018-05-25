import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from Kiwoom import *

form_class = uic.loadUiType("pytrader.ui")[0]

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()  #키움 로그인

        self.timer = QTimer(self)
        self.timer.start(1000) #1초에 한 번씩 주기적으로 timeout 시그널이 발생
        self.timer.timeout.connect(self.timeout) #timeout 시그널이 발생할 때 이를 처리할 슬롯으로 self.timeout을 설정
        #StatusBar 위젯에 서버 연결 상태 및 현재 시간을 출력

    def timeout(self):
        current_time = QTime.currentTime() #현재 시간
        text_time = current_time.toString("hh:mm:ss") #시간:분:초
        time_msg = "현재시간: " + text_time

        state = self.kiwoom.GetConnectState() #서버 연결 상태 확인
        if state == 1:
            state_msg = "서버 연결 중"
        else:
            state_msg = "서버 미 연결 중"

        self.statusbar.showMessage(state_msg + " | " + time_msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
