import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import os
import time

# =========================
# 1. 基本設定
# =========================
OUTPUT_DIR = "data"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

TODAY_STR = datetime.datetime.today().strftime("%Y-%m-%d")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
}

# =========================
# 2. 爬取日本新聞 (日經新聞精準版)
# =========================
def get_japan_news():
    print("🔎 抓取日本新聞...")
    url = "https://www.nikkei.com/search?keyword=保険"
    articles = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 修正：精準定位日經搜尋結果的文章區塊
        items = soup.select('article') 
        
        for item in items:
            title_tag = item.select_one('h3')
            link_tag = item.select_one('a')
            if title_tag and link_tag:
                title = title_tag.get_text(strip=True)
                link = link_tag.get('href')
                if link.startswith('/'):
                    link = "https://www.nikkei.com" + link
                
                # 關鍵：標題長度大於12通常才是新聞，避開標籤
                if len(title) > 12:
                    articles.append({
                        "title": title,
                        "link": link,
                        "date": TODAY_STR,
                        "source": "日本新聞"
                    })
    except Exception as e:
        print(f"❌ 日本抓取錯誤: {e}")
    return articles

# =========================
# 3. 爬取台灣新聞 (Google News 搜尋版)
# =========================
def get_taiwan_news():
    print("🔎 抓取台灣新聞...")
    # 搜尋「保險」並按時間排序
    url = "https://news.google.com/search?q=%E4%BF%9D%E9%9A%AA&hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant"
    articles = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Google News 文章標題區塊
        items = soup.select('article')[:15] # 抓前 15 則
        
        for item in items:
            title_tag = item.select_one('h3') # 或選取 a 標籤
            link_tag = item.select_one('a')
            if title_tag and link_tag:
                title = title_tag.get_text(strip=True)
                link = "https://news.google.com" + link_tag.get('href')[1:] # 修正連結
                
                articles.append({
                    "title": title,
                    "link": link,
                    "date": TODAY_STR,
                    "source": "台灣新聞"
                })
    except Exception as e:
        print(f"❌ 台灣抓取錯誤: {e}")
    return articles

# =========================
# 4. 執行與儲存
# =========================
def main():
    jp_news = get_japan_news()
    tw_news = get_taiwan_news()
    
    all_news = jp_news + tw_news
    df = pd.DataFrame(all_news)

    if df.empty:
        print("⚠️ 未抓取到任何新聞")
        return

    # 存成 JSON
    json_path = os.path.join(OUTPUT_DIR, "news_data.json")
    df.to_json(json_path, orient="records", force_ascii=False, indent=4)
    
    # 存成 Excel 備份
    excel_path = os.path.join(OUTPUT_DIR, f"news_log_{TODAY_STR}.xlsx")
    df.to_excel(excel_path, index=False)
    
    print(f"✅ 更新完成！共 {len(df)} 則新聞。")

if __name__ == "__main__":
    main()
