import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from Kiwoom import *

form_class = uic.loadUiType("StockT.ui")[0]

class StockT(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()  #키움 로그인

        self.trade_stocks_done = False #자동 주문

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

        self.pushButton_2.clicked.connect(self.check_balance) #시그널과 슬롯을 연결하는 코드

        self.load_buy_sell_list() #선정 종목 리스트 출력

    def timeout(self):
        # 현재 시간이 09시 00분 00초를 지났고 매수/매도 주문을 수행하지 않았을 때 trade_stocks 메서드 호출
        market_start_time = QTime(9, 0, 0)
        current_time = QTime.currentTime()

        # 장이 시작할 때 매수/매도 주문을 넣으려면 timeout 메서드에서 시간 체크
        if current_time > market_start_time and self.trade_stocks_done is False:
            self.trade_stocks()
            self.trade_stocks_done = True

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

    def check_balance(self): #'조회' 버튼이 클릭됐을 때 '잔고 및 보유종목현황' 데이터 호출하도록
        self.kiwoom.reset_opw00018_output()
        account_number = self.kiwoom.get_login_info("ACCNO")
        account_number = account_number.split(';')[0]

        self.kiwoom.set_input_value("계좌번호", account_number) #입력 데이터 설정
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000") #TR 요청

        while self.kiwoom.remained_data:
            time.sleep(0.2)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")

        # opw00001
        # 예수금 데이터를 얻기 위해 opw00001 TR을 요청
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")

        # balance
        item = QTableWidgetItem(self.kiwoom.d2_deposit)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget.setItem(0, 0, item) #칼럼의 위치로 (0, 0)

        for i in range(1, 6): #리스트로 저장되어 있기에 반복문으로 가져오기
            item = QTableWidgetItem(self.kiwoom.opw00018_output['single'][i - 1])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.tableWidget.setItem(0, i, item)

        self.tableWidget.resizeRowsToContents() #아이템의 크기에 맞춰 행의 높이를 조절

        # Item list
        # 보유 종목별 평가 잔고 데이터를 QTableWidget에 추가
        # 행의 개수를 따로 설정하지 않았기에, 먼저 보유종목의 개수를 확인한 후 행의 개수를 설정해야 함
        # (열의 개수는 Qt Designer가 자동으로 설정)
        item_count = len(self.kiwoom.opw00018_output['multi'])
        self.tableWidget_2.setRowCount(item_count)

        for j in range(item_count): #아이템 추가
            row = self.kiwoom.opw00018_output['multi'][j]
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tableWidget_2.setItem(j, i, item)

        self.tableWidget_2.resizeRowsToContents() #행의 크기를 조절

        # Timer2
        # [실시간 조회] 체크박스를 체크하면 데이터가 자동으로 갱신
        self.timer2 = QTimer(self)
        self.timer2.start(1000*10) #10초에 한 번
        self.timer2.timeout.connect(self.timeout2)

    def timeout2(self): # QCheckBox가 체크됐는지 확인한 후 체크돼 있을 때 데이터를 갱신
        if self.checkBox.isChecked():
            self.check_balance()

    # buy_list.txt와 sell_list.txt 파일을 열고 파일로부터 데이터를 읽는 코드
    # 아직 알고리즘을 안만들었기에
    def load_buy_sell_list(self):
        f = open("buy_list.txt", 'rt')
        buy_list = f.readlines()
        f.close()

        f = open("sell_list.txt", 'rt')
        sell_list = f.readlines()
        f.close()

        #데이터의 총 개수 확인
        row_count = len(buy_list) + len(sell_list)
        self.tableWidget_3.setRowCount(row_count)

        # buy list 매수 종목
        for j in range(len(buy_list)):
            row_data = buy_list[j]
            split_row_data = row_data.split(';')
            split_row_data[1] = self.kiwoom.get_master_code_name(split_row_data[1].rsplit())

            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_3.setItem(j, i, item)

        # sell list 매도 종목
        for j in range(len(sell_list)): #j : 행(row)에 대한 인덱스 값
            row_data = sell_list[j]
            split_row_data = row_data.split(';') #문자열을 ;로 분리
            split_row_data[1] = self.kiwoom.get_master_code_name(split_row_data[1].rstrip()) #종목코드로부터 종목명 구하기

            for i in range(len(split_row_data)): #i : 열(column)에 대한 인덱스 값
                item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_3.setItem(len(buy_list) + j, i, item)

        self.tableWidget_3.resizeRowsToContents() #행의 크기 조절


    # 장이 시작하면 미리 선정된 종목에 대해 자동으로 주문하는 기능 구현
    def trade_stocks(self):
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        f = open("buy_list.txt", 'rt')
        buy_list = f.readlines()
        f.close()

        f = open("sell_list.txt", 'rt')
        sell_list = f.readlines()
        f.close()                           #미리 생성된 파일로부터 매수/매도 종목을 읽는 코드

        # account
        # 주문할 때 필요한 계좌 정보
        account = self.comboBox.currentText()

        # buy list 매수 주문
        # 데이터를 하나씩 얻어온 후 문자열을 분리해서 주문에 필요한 정보 준비
        for row_data in buy_list:
            split_row_data = row_data.split(';')
            hoga = split_row_data[2]
            code = split_row_data[1]
            num = split_row_data[3]
            price = split_row_data[4]

            # 읽어온 데이터의 주문 수행 여부가 ‘매수전’인 경우에만 해당 주문 데이터를 토대로 send_order 메서드를 통해 매수 주문 수행
            if split_row_data[-1].rstrip() == '매수전':
                self.kiwoom.send_order("send_order_req", "0101", account, 1, code, num, price, hoga_lookup[hoga], "")

        # sell list 매도 주문
        for row_data in sell_list:
            split_row_data = row_data.split(';')
            hoga = split_row_data[2]
            code = split_row_data[1]
            num = split_row_data[3]
            price = split_row_data[4]

            if split_row_data[-1].rstrip() == '매도전':
                self.kiwoom.send_order("send_order_req", "0101", account, 2, code, num, price, hoga_lookup[hoga], "")

        # buy list
        # 저장된 주문 여부를 업데이트
        for i, row_data in enumerate(buy_list):
            buy_list[i] = buy_list[i].replace("매수전", "주문완료") #바꾸기

        # file update
        f = open("buy_list.txt", 'wt')
        for row_data in buy_list:
            f.write(row_data)
        f.close()

        # sell list
        for i, row_data in enumerate(sell_list):
            sell_list[i] = sell_list[i].replace("매도전", "주문완료")

        # file update
        f = open("sell_list.txt", 'wt')
        for row_data in sell_list:
            f.write(row_data)
        f.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    stockt = StockT()
    stockt.show()
    app.exec_()
