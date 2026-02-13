import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import os

# =========================
# 1. 基本設定
# =========================
OUTPUT_DIR = "data"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

TODAY_STR = datetime.datetime.today().strftime("%Y-%m-%d")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# =========================
# 2. 爬取台灣新聞 (使用穩定 RSS 來源)
# =========================
def get_taiwan_news():
    print("🔎 嘗試從 RSS 抓取台灣保險新聞...")
    # 使用 Google News RSS 格式，這在 GitHub Actions 上極度穩定
    rss_url = "https://news.google.com/rss/search?q=%E4%BF%9D%E9%9A%AA&hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant"
    articles = []
    try:
        response = requests.get(rss_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, "xml") # RSS 要用 xml 解析
        items = soup.find_all("item")
        
        for item in items[:15]: # 抓前 15 則
            articles.append({
                "title": item.title.text,
                "link": item.link.text,
                "date": TODAY_STR,
                "source": "台灣新聞"
            })
    except Exception as e:
        print(f"❌ 台灣 RSS 抓取錯誤: {e}")
    return articles

# =========================
# 3. 爬取日本新聞 (日經新聞)
# =========================
def get_japan_news():
    print("🔎 抓取日本新聞...")
    url = "https://www.nikkei.com/search?keyword=%E4%BF%9D%E9%99%BA"
    articles = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        # 擴大搜索範圍，避免 Selector 失效
        items = soup.find_all("article")
        
        for item in items:
            title_tag = item.find("h3") or item.find("a")
            link_tag = item.find("a")
            if title_tag and link_tag:
                title = title_tag.get_text(strip=True)
                link = link_tag.get('href')
                if link.startswith('/'):
                    link = "https://www.nikkei.com" + link
                
                # 過濾太短的標題（通常是導覽標籤）
                if len(title) > 10:
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
# 4. 執行與儲存
# =========================
def main():
    tw_news = get_taiwan_news()
    jp_news = get_japan_news()
    
    all_news = tw_news + jp_news
    
    if not all_news:
        print("⚠️ 完全沒抓到新聞，產生一條測試資料避免程式中斷")
        all_news = [{
            "title": "系統測試：目前線上暫無最新新聞，請稍後再試",
            "link": "#",
            "date": TODAY_STR,
            "source": "台灣新聞"
        }]

    df = pd.DataFrame(all_news)
    
    # 存成 JSON
    json_path = os.path.join(OUTPUT_DIR, "news_data.json")
    df.to_json(json_path, orient="records", force_ascii=False, indent=4)
    print(f"✅ 更新完成！共 {len(df)} 則新聞已寫入 {json_path}")

if __name__ == "__main__":
    main()
