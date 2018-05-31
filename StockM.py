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
import StockR
import numpy as np

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
        time.sleep(3.6)

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
            f.writelines("매수;"+ code + ";시장가;10;0;매수전\n") #메서드 인자로 전달된 매수 종목에 대해 파일에 라인 단위로 출력
        f.close()                                             #매수 수량은 예시 단순화 위해 '10주'로

    def run(self):
        buy_list = [] #빈 리스트 생성
        num = len(self.kosdaq_codes)

        for i, code in enumerate(self.kosdaq_codes):
            print(i, '/', num)
            if self.check_speedy_rising_volume(code): #check_speedy~ 반환값이 True인 종목의 종목코드를 해당 리스트에 추가
                #print("급등주: ", code)
                #print("급등주: %s, %s" % (code, self.kiwoom.get_master_code_name(code)))
                buy_list.append(code)

        self.update_buy_list(buy_list) #거래량 급증 종목을 파일로 출력

    #현재 거래일 기준으로 예상 현금배당수익률(or 현금배당수익률)과 3년 만기 국채수익률의 일별 시세를 가져와 국채시가배당률을 계산하는 메서드
    #예상 현금배당수익률은 StockR 모듈의 get_estimated_dividend_yield 함수를 호출
    #현금배당수익률은 get_dividend_yield 함수를 사용
    #3년 만기 국채수익률은 get_current_3year_treasury 함수로
    #예상 현금배당수익률이 존재하는 종목은 해당 값을 사용하고, 그렇지 않은 종목은 현금배당수익률을 사용
    #현금배당수익률이 존재하지 않는 경우 빈 문자열이 반환되는데 이 경우 현금배당수익률을 0으로 할당
    def calculate_estimated_dividend_to_treasury(self, code):
        estimated_dividend_yield = StockR.get_estimated_dividend_yield(code)
        if np.isnan(estimated_dividend_yield):
            estimated_dividend_yield = StockR.get_dividend_yield(code)

            if estimated_dividend_yield == "":
                estimated_dividend_yield = 0

        current_3year_treasury = StockR.get_current_3year_treasury()
        estimated_dividend_to_treasury = float(estimated_dividend_yield) / float(current_3year_treasury)
        return estimated_dividend_to_treasury
        #국채시가배당률 = 현금배당수익률 / 3년 만기 국채수익률. 함수를 호출해 가져온 값이 문자열이므로 실수형으로 형을 변환한 후 나눔

    #최근 5년에 대한 국채시가배당률 중 최댓값과 최솟값을 반환하는 함수 구현
    #StockR 모듈 내의 함수를 사용해 최대 5년 치에 대한 시가배당률과 연도별 3년 만기 국채 수익률 데이터(1998년~2016년)를 얻어옵
    def get_min_max_dividend_to_treasury(self, code):
        previous_dividend_yield = StockR.get_previous_dividend_yield(code)
        three_years_treasury = StockR.get_3year_treasury()

        now = datetime.datetime.now()
        cur_year = now.year
        previous_dividend_to_treasury = {} #각 연도별 국채시가배당률을 저장할 파이썬 딕셔너리 객체를 생성

        #각 연도에 대해 국채시가배당률을 계산한 후 딕셔너리에 추가
        #딕셔너리의 키는 연도이고 값은 해당 연도의 국채시가 배당률
        #일부 종목은 과거 연도의 데이터가 존재하지 않을 수 있기 때문에 if 문을 사용해 먼저 해당 연도가 딕셔너리의 키 값에 존재하는지 확인
        for year in range(cur_year-5, cur_year):
            if year in previous_dividend_yield.keys() and year in three_years_treasury.keys():
                ratio = float(previous_dividend_yield[year]) / float(three_years_treasury[year])
                previous_dividend_to_treasury[year] = ratio

        #print(previous_dividend_to_treasury)
        if not previous_dividend_yield:
            return (0, 0)

        min_ratio = min(previous_dividend_to_treasury.values())
        max_ratio = max(previous_dividend_to_treasury.values())

        return (min_ratio, max_ratio)

    #현재 시점을 기준으로 계산한 국채시가배당률이 과거 5년 치 국채시가배당률의 최댓값보다 큰 경우 해당 종목을 매수하는 알고리즘
    #현시점에서의 예상 국채시가배당률을 calculate_estimated_dividend_to_treasury 메서드를 호출
    #과거 5년에 대한 최대, 최소 국채시가배당률은 get_min_max_dividend_to_treasury 메서드를 호출
    #if 문을 사용해 현시점의 예상 국채시가배당률이 과거 5년에 대한 국채시가배당률의 최댓값보다 크거나 같은 경우 ‘(1, 예상 국채시가배당률)’의 튜플을 리턴
    def buy_check_by_dividend_algorithm(self, code):
        estimated_dividend_to_treasury = self.calculate_estimated_dividend_to_treasury(code)
        (min_ratio, max_ratio) = self.get_min_max_dividend_to_treasury(code)

        #데이터가 존재하지 않는 경우 estimated_dividend_to_treasury와 max_ratio가 0이 된다.
        #이 경우 if 문을 만족해서 매수 신호가 발생하기 때문에 max_ratio !=0 구문을 추가
        if estimated_dividend_to_treasury >= max_ratio and max_ratio != 0:
            return (1, estimated_dividend_to_treasury)
        else:
            return (0, estimated_dividend_to_treasury)

    #유가증권시장의 전 종목에 대해 국채시가배당률 알고리즘을 사용해 매수 여부를 체크
    def run_dividend(self):
        buy_list = []

        # 반복문에서 self.kospi_codes의 종목을 하나씩 가져온 후 buy_check_by_dividend_algorithm 메서드를 호출
        # 간단히 구현한 메서드를 테스트하기 위해 유가증권시장의 50개 종목에 대해서만 체크하도록 코드를 수정
        for code in self.kospi_codes[0:100]:
            print('Check: ', code)
            time.sleep(0.1)
            ret = self.buy_check_by_dividend_algorithm(code)
            # 반환값인 튜플의 첫 번째 원소가 1이면 buy_list에 추가
            if ret[0] == 1:
                print("Pass", ret)
                buy_list.append((code, ret[1]))
            else:
                print("Fail", ret)

        #국채시가배당률 알고리즘 기반으로 매수 신호가 발생한 경우 종목과 해당 종목에 대한 국채시가배당률이 buy_list에 저장
        #매수 종목이 여러 개인 경우 그중 국채시가배당률이 높은 종목이 더 매수에 적합하므로 다음과 같이 국채시가배당률이 높은 종목을 기준으로 정렬
        sorted_list = sorted(buy_list, key=lambda t: t[1], reverse=True)


        #국채시가배당률이 높은 상위 5개 종목을 buy_list.txt 파일에 추가
        #매수 종목 리스트를 buy_list.txt 파일에 출력하는 기능은 update_buy_list 메서드에 이미 구현되어 있음
        #따라서 sorted_list에서 상위 5개 종목에 대한 종목 코드로 새로운 리스트로 만든 후 해당 리스트를 update_buy_list 메서드의 인자로 전달

        buy_list = []
        for i in range(0, 5):
            code = sorted_list[i][0]
            buy_list.append(code)

        self.update_buy_list(buy_list)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    stockM = StockM()
    stockM.run_dividend()
