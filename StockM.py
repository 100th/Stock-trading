import sys
from PyQt5.QtWidgets import *
import Kiwoom

"""
* 급등주 포착 알고리즘 기반의 종목 선정 *
: 매일 장 종료 후 자동으로 실행되어
유가증권 시장과 코스닥 시장에서 미리 구현된 매수/매도 알고리즘에 부합하는 종목을 찾은 후
이를 buy_list.txt와 sell_list.txt로 저장
"""

MARKET_KOSPI   = 0
MARKET_KOSDAQ  = 10

class StockM:
    def __init__(self):
        self.kiwoom = Kiwoom.Kiwoom()
        self.kiwoom.comm_connect()
        self.get_code_list() #StockM이 실행되면 한 번만 수행하면 되기 때문에

    #유가증권과 코스닥 시장에 상장된 종목의 코드를 가져오는 메서드 (모든 종목에 대한 종목코드를 알고 있어야 하기에)
    #get_code_list 메서드뿐 아니라 다른 메서드에서 사용될 것이므로 각각의 서로 다른 이름으로 바인딩
    def get_code_list(self):
        self.kospi_codes = self.kiwoom.get_code_list_by_market(MARKET_KOSPI)
        self.kosdaq_codes = self.kiwoom.get_code_list_by_market(MARKET_KOSDAQ)

    def run(self):
        print(self.kospi_codes[0:4])
        print(self.kosdaq_codes[0:4]) #테스트

if __name__ == "__main__":
    app = QApplication(sys.argv)
    stockm = StockM()
    stockm.run()
