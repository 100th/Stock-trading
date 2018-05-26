"""
* 급등주 포착 알고리즘 기반의 종목 선정 *
: 매일 장 종료 후 자동으로 실행되어
유가증권 시장과 코스닥 시장에서 미리 구현된 매수/매도 알고리즘에 부합하는 종목을 찾은 후
이를 buy_list.txt와 sell_list.txt로 저장
"""
import sys
from PyQt5.QtWidgets import *
import Kiwoom
import time
from pandas import DataFrame

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

    #오늘 날짜를 시작으로 과거 거래일별로 시가, 고가, 저가, 종가, 거래량을 가져오는 메서드
    #메서드의 인자로 조회할 종목에 대한 종목코드와 기준일자를 받는다
    def get_ohlcv(self, code, start):
        self.kiwoom.ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

        self.kiwoom.set_input_value("종목코드", code)
        self.kiwoom.set_input_value("기준일자", start)
        self.kiwoom.set_input_value("수정주가구분", 1)
        self.kiwoom.comm_rq_data("opt10081_req", "opt10081", 0, "0101")
        time.sleep(0.2) #0.2초 간격

        #효율적으로 저장하기 위해 pandas의 dataframe
        df = DataFrame(self.kiwoom.ohlcv, columns=['open', 'high', 'low', 'close', 'volume'], index=self.kiwoom.ohlcv['date'])
        return df

    def run(self):
        df = self.get_ohlcv("039490", "20170321")
        print(df) #테스트

if __name__ == "__main__":
    app = QApplication(sys.argv)
    stockm = StockM()
    stockm.run()
