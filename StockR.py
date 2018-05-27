import requests
import pandas as pd

# 함수 인자로 종목코드를 받고, 함수 인자로 전달된 종목코드는 URL의 중간에 삽입되어 최종 URL로 완성됨
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

if __name__ == "__main__":
    df = get_financial_statements('035720')
    print(df)
