import requests
import pandas as pd
from bs4 import BeautifulSoup

# 함수 인자로 종목코드를 받고, 함수 인자로 전달된 종목코드는 URL의 중간에 삽입되어 최종 URL로 완성됨
def get_financial_statements(code):
    url = "http://companyinfo.stock.naver.com/v1/company/ajax/cF1001.aspx?cmp_cd=%s&fin_typ=0&freq_typ=Y" % (code)
    html = requests.get(url).text

    df_list = pd.read_html(html)
    df = df_list[0]

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

    print(treasury_3year)
    return treasury_3year

if __name__ == "__main__":
    df = get_financial_statements('035720')
    print(df)
