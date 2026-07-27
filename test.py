from src import news as news 
from src import krx_client as krx 

def run(date: str = None):
    date = date or krx.get_latest_business_date()
    print(f"==={date} 기준 뉴스 서치 시작")

    results = news.search_news_for_stock("삼성전자")

    if not results:
        print("결과없음")
    else :
        for r in results :
           print(f"[{r['pub_date_display']}] {r['title']}")
           print(f"  -> {r['link']}")


if __name__ == "__main__":
    run()