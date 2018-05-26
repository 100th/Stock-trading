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
import datetime

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
        time.sleep(0.5)

        #효율적으로 저장하기 위해 pandas의 dataframe
        df = DataFrame(self.kiwoom.ohlcv, columns=['open', 'high', 'low', 'close', 'volume'], index=self.kiwoom.ohlcv['date'])
        return df

    #'급등주 포착' 알고리즘
    #특정 거래일의 거래량이 이전 시점의 평균 거래량보다 1000% 이상 급증하는 종목을 매수
    #'이전 시점의 평균 거래량'을 특정 거래일 이전의 20일(거래일 기준) 동안의 평균 거래량으로 정의
    #'거래량 급증'은 특정 거래일의 거래량이 평균 거래량보다 1000% 초과일 때 급등한 것으로 정의
    def check_speedy_rising_volume(self, code): #메서드 인자로 종목코드 전달 받기
        today = datetime.datetime.today().strftime("%Y%m%d") #오늘 날짜
        df = self.get_ohlcv(code, today) #앞서 구현한 get_ohlcv 메서드를 호출해서
        volumes = df['volume'] # 해당 종목 데이터를 DataFrame 객체로 얻어온 후 그중 거래량 칼럼만 바인딩

        if len(volumes) < 21: #최근에 상장된 종목이라면 데이터가 충분하지 않으므로 걸러내기
            return False

        sum_vol20 = 0 #일별 거래량 누적
        today_vol = 0 #조회 시작일 거래량

        for i, vol in enumerate(volumes):
            if i == 0:
                today_vol = vol
            elif 1 <= i <= 20:
                sum_vol20 += vol
            else:
                break

        avg_vol20 = sum_vol20 / 20  #20일의 평균 거래량을 계산한 후 조회 시작일의 거래량과 비교
        if today_vol > avg_vol20 * 10:
            return True #만약 조회 시작일의 거래량이 평균 거래량을 1,000% 초과한다면 True를 반환

    # 선정된 종목에 대한 정보를 파일로 쓰는 기능
    def update_buy_list(self, buy_list): #종목코드 리스트 받기
        f = open("buy_list.txt", "wt")
        for code in buy_list:
            f.writelines("매수;", code, ";시장가;10;0;매수전") #메서드 인자로 전달된 매수 종목에 대해 파일에 라인 단위로 출력
        f.close()                                             #매수 수량은 예시 단순화 위해 '10주'로

    def run(self):
        buy_list = [] #빈 리스트 생성
        num = len(self.kosdaq_codes)

        for i, code in enumerate(self.kosdaq_codes):
            print(i, '/', num)
            if self.check_speedy_rising_volume(code): #check_speedy~ 반환값이 True인 종목의 종목코드를 해당 리스트에 추가
                buy_list.append(code)

        self.update_buy_list(buy_list) #거래량 급증 종목을 파일로 출력

if __name__ == "__main__":
    app = QApplication(sys.argv)
    stockm = StockM()
    stockm.run()
