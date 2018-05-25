import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from Kiwoom import *

form_class = uic.loadUiType("StockT.ui")[0]

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

        self.lineEdit.textChanged.connect(self.code_changed) #lineEdit 객체가 변경될 때 호출되는 슬롯을 지정
        self.pushButton.clicked.connect(self.send_order) #현금주문

        accouns_num = int(self.kiwoom.get_login_info("ACCOUNT_CNT")) #계좌 정보를 QComboBox 위젯에 출력하는 코드
        accounts = self.kiwoom.get_login_info("ACCNO") #로그인 정보 가져오기
        accounts_list = accounts.split(';')[0:accouns_num] #계좌가 여러 개인 경우 각 계좌는';'를 통해 구분

        self.comboBox.addItems(accounts_list)

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

    def code_changed(self): #사용자가 ineEdit에 종목코드를 입력하면 종목코드를 읽은 후 API를 사용해 종목명 알아내기
        code = self.lineEdit.text()
        name = self.kiwoom.get_master_code_name(code)
        self.lineEdit_2.setText(name)

    def send_order(self): #pushButton 객체가 클릭될 때 호출되는 send_order 메서드
        order_type_lookup = {'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소': 4}
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        account = self.comboBox.currentText()
        order_type = self.comboBox_2.currentText()
        code = self.lineEdit.text()
        hoga = self.comboBox_3.currentText()
        num = self.spinBox.value()
        price = self.spinBox_2.value()

        self.kiwoom.send_order("send_order_req", "0101", account, order_type_lookup[order_type], code, num, price, hoga_lookup[hoga], "")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
