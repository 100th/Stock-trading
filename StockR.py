"""
국채시가배당률 = '현금배당 수익률' / '3년 만기 국채 수익률'

3년 만기 국채 수익률은 시장 금리와 같은 역할을 하는 대표적인 지표인데,
국채시가배당률이 1.0보다 크다는 것은 현금배당수익률이 3년 만기 국채 수익률보다 높은 경우이다.
즉, 돈을 은행에 저금해서 얻는 이자 수익보다 주식을 사서 배당금을 받는 수익이 더 높다.
한마디로 국채시가배당률이 높은 종목은 좋은 배당주라고 해석할 수 있다.
종목을 선정할 때 또는 같은 종목이라도 매수/매도 시점을 파악할 때 국채시가배당률 값이 상대적으로 높으면
좋은 매수 시기이고 상대적으로 낮다면 좋은 매도 시기로 해석하는 것이다.

앞서 파싱한 재무제표 데이터를 바탕으로 국채시가배당률이 높은 종목을 선정하는 프로그램을 구현

국채시가배당률을 계산하려면 3년 만기 국채 수익률이 필요. 3년 만기 국채 수익률은 국가지표체계 웹 사이트에서 파싱 가능.
"""
import requests
import pandas as pd
from bs4 import BeautifulSoup
import datetime
import numpy as np

# 함수 인자로 종목코드를 받고, 함수 인자로 전달된 종목코드는 URL의 중간에 삽입되어 최종 URL로 완성됨
# 1998년 이후로 연 단위로 국고채 3년(평균) 값이 제공
def get_financial_statements(code):
    url = "http://companyinfo.stock.naver.com/v1/company/ajax/cF1001.aspx?cmp_cd=%s&fin_typ=0&freq_typ=Y" % (code)
    html = requests.get(url).text
    
    # replace 메서드를 사용해 불필요한 HTML 태그 및 공백 문자열을 제거
    html = html.replace('<th class="bg r01c02 endLine line-bottom"colspan="8">연간</th>', "")
    html = html.replace("<span class='span-sub'>(IFRS연결)</span>", "")
    html = html.replace("<span class='span-sub'>(IFRS별도)</span>", "")
    html = html.replace("<span class='span-sub'>(GAAP개별)</span>", "")
    html = html.replace('\t', '')
    html = html.replace('\n', '')
    html = html.replace('\r', '')
    html = html.replace('<tr><th rowspan="2" class="r03c00 bg" style="width:125px">주요재무정보</th></tr><tr>', '<tr><th  class="r03c00 bg" style="width:125px">주요재무정보</th>')

    # 회사마다 결산월이 다르다. 5월까지 공시된 경우 이전 연도로 간주하고 6월부터는 당해 연도로 간주
    for year in range(2009, 2018):
        for month in range(6, 13):
            month = "/%02d" % month
            html = html.replace(str(year) + month, str(year))

        for month in range(1, 6):
            month = "/%02d" % month
            html = html.replace(str(year+1) + month, str(year))

        html = html.replace(str(year) + '(E)', str(year))

    df_list = pd.read_html(html, index_col='주요재무정보')
    df = df_list[0]
    return df

# 국고채금리를 파싱
def get_3year_treasury():
    url = "http://www.index.go.kr/strata/jsp/showStblGams3.jsp?stts_cd=288401&amp;idx_cd=2884&amp;freq=Y&amp;period=1998:2016"
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml') #HTML 문서를 파싱하기 위해 HTML 코드를 BeautifulSoop 객체로 변환
    #첫 번째 인자로 검색하고자 하는 HTML 태그를 입력, id 값을 지정해 해당 id 값을 갖는 행만 추출
    tr_data = soup.find_all('tr', id='tr_288401_1') #해당 행의 HTML 코드만 가져오기
    #td_data는 ResultSet이라는 데이터 타입인데, 파이썬 리스트와 같이 인덱싱을 통해 각 원소에 접근
    td_data = tr_data[0].find_all('td') #<td> 태그 데이터만 추출

    #연도별 국고채금리(3년 만기 국채 수익률)를 쉽게 얻을 수 있도록 파이썬 딕셔너리 형태로 데이터를 저장
    treasury_3year = {} #빈 딕셔너리 객체
    start_year = 1998

    for x in td_data:
        treasury_3year[start_year] = x.text
        start_year += 1

    #print(treasury_3year)
    return treasury_3year

#현금배당수익률 파싱
def get_dividend_yield(code):
    url = "http://companyinfo.stock.naver.com/company/c1010001.aspx?cmp_cd=" + code #기업 현황 웹페이지
    html = requests.get(url).text

    soup = BeautifulSoup(html, 'lxml')
    td_data = soup.find_all('td', {'class': 'cmp-table-cell td0301'})
    # HTML 코드에서 특정 td 태그가 존재하지 않는 경우 빈 문자열을 반환
    if not td_data:
        return ""
    dt_data = td_data[0].find_all('dt')

    dividend_yield = dt_data[5].text #현금배당수익률은 6번째에 위치하므로 [5]로 인덱싱해서 데이터에 접근
    dividend_yield = dividend_yield.split(' ')[1] #가져온 텍스트에서 현금배당수익률의 수치만 추출하도록 구현
    dividend_yield = dividend_yield[:-1]

    return dividend_yield

# 파싱한 주요 재무 정보에서 당해 연도의 현금배당수익률을 가져오는 함수
def get_estimated_dividend_yield(code):
    df = get_financial_statements(code) #앞서 구현한 함수로 재무제표를 DataFrame 객체 형태로 가져옴
    #'현금배당수익률'은 ix 메서드를 통해 DataFrame 객체의 로우에 접근해서 구할 수 있다.
    #로우 데이터는 pandas의 Series 객체이므로 인덱스를 통해 각 연도별 현금배당수익을 얻을 수 있다.
    dividend_yield = df.ix["현금배당수익률"]

    #프로그램이 동작할 때 당해 연도를 자동으로 알아내기 위해 datetime 모듈을 사용
    now = datetime.datetime.now()
    cur_year = now.year

    #만약 당해 연도에 현금배당수익률이 존재하지 않는 경우에는 이전 연도의 현금배당수익률을 반환하도록 구현
    #데이터가 존재하지 않을 때는 NaN을 돌려주는데, 이를 확인하기 위해 Numpy 모듈의 isnan 메서드를 사용
    if str(cur_year) in dividend_yield.index and not np.isnan(dividend_yield[str(cur_year)]):
        return dividend_yield[str(cur_year)]
    #해당 연도 및 이전 연도에 데이터가 존재하는지 확인하기 위해 np.isnan 메서드를 사용
    elif str(cur_year-1) in dividend_yield.index and not np.isnan(dividend_yield[str(cur_year-1)]):
        return dividend_yield[str(cur_year-1)]
    #예상 현금배당수익률이 존재하지 않는 경우에는 np.NaN을 반환
    else:
        return np.NaN

#3년 만기 국채 수익률의 일별 시세를 파싱하는 함수
def get_current_3year_treasury():
    url = "http://info.finance.naver.com/marketindex/interestDailyQuote.nhn?marketindexCd=IRR_GOVT03Y&page=1"
    html = requests.get(url).text

    soup = BeautifulSoup(html, 'lxml')
    tbody_data = soup.find_all('tbody')
    tr_data = tbody_data[0].find_all('tr')
    td_data = tr_data[0].find_all('td')
    return td_data[1].text #최근 날짜의 시세는 표에서 첫 번째 행의 두 번째 열에서 구할 수 있음

#재무제표에서 과거 5년치에 대한 현금배당수익률을 가져오는 함수
def get_previous_dividend_yield(code):
    df = get_financial_statements(code) #code에 해당하는 종목의 재무제표를 DataFrame 객체로 가져옴
    dividend_yield = df.ix['현금배당수익률'] #ix 메서드를 이용해 '현금배당수익률'에 해당하는 로우 데이터를 가져옴

    now = datetime.datetime.now()
    cur_year = now.year

    #네이버는 과거 5년 치 재무제표 정보를 제공하므로
    #다음과 같이 현재 연도를 기준으로 5년 치의 현금배당수익률을 파이썬 딕셔너리 형태로 가공
    #최근에 상장된 기업들은 최근 5년 치 데이터가 모두 존재하지는 않을 수 있으므로
    #다음과 같이 특정 연도가 인덱스에 존재할 때만 데이터를 가져오도록 코드를 작성
    previous_dividend_yield = {}

    for year in range(cur_year-5, cur_year):
        if str(year) in dividend_yield.index:
            previous_dividend_yield[year] = dividend_yield[str(year)]

    return previous_dividend_yield

if __name__ == "__main__":
    print(get_previous_dividend_yield('058470'))
