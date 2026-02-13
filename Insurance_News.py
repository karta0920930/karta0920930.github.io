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
# 2. 爬取台灣新聞 (改用內建解析器)
# =========================
def get_taiwan_news():
    print("🔎 嘗試抓取台灣保險新聞...")
    # 使用 Google News 網頁版而非 RSS 避免 XML 庫遺失問題
    url = "https://news.google.com/search?q=%E4%BF%9D%E9%9A%AA&hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant"
    articles = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        # 關鍵：改用內建的 html.parser，不需要額外安裝 lxml
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 尋找所有新聞連結
        links = soup.find_all("a", limit=50)
        for link in links:
            title = link.get_text(strip=True)
            href = link.get('href')
            
            # 過濾標題長度，確保它是新聞標題而非按鈕文字
            if href and href.startswith('./articles/') and len(title) > 10:
                full_link = "https://news.google.com" + href[1:]
                articles.append({
                    "title": title,
                    "link": full_link,
                    "date": TODAY_STR,
                    "source": "台灣新聞"
                })
                if len(articles) >= 15: break # 抓 15 則就夠
    except Exception as e:
        print(f"❌ 台灣抓取錯誤: {e}")
    return articles

# =========================
# 3. 爬取日本新聞 (放寬規則版)
# =========================
def get_japan_news():
    print("🔎 抓取日本新聞...")
    url = "https://www.nikkei.com/search?keyword=%E4%BF%9D%E9%99%BA"
    articles = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 放寬條件：抓取所有包含「保險」關鍵字的連結
        links = soup.find_all("a")
        for link in links:
            title = link.get_text(strip=True)
            href = link.get('href')
            
            if href and "保険" in title and len(title) > 15:
                full_link = href
                if href.startswith('/'):
                    full_link = "https://www.nikkei.com" + href
                
                articles.append({
                    "title": title,
                    "link": full_link,
                    "date": TODAY_STR,
                    "source": "日本新聞"
                })
                if len(articles) >= 25: break
    except Exception as e:
        print(f"❌ 日本抓取錯誤: {e}")
    return articles

# =========================
# 4. 執行與儲存
# =========================
def main():
    tw_news = get_taiwan_news()
    jp_news = get_japan_news()
    
    # 移除重複標題
    all_news = tw_news + jp_news
    if all_news:
        df = pd.DataFrame(all_news).drop_duplicates(subset="title")
        all_news = df.to_dict('records')
    
    if not all_news:
        print("⚠️ 完全沒抓到新聞，產生一條測試資料")
        all_news = [{
            "title": "今日暫無更新新聞 (系統自動偵測中)",
            "link": "#",
            "date": TODAY_STR,
            "source": "台灣新聞"
        }]

    # 輸出 JSON
    import json
    json_path = os.path.join(OUTPUT_DIR, "news_data.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=4)
        
    print(f"✅ 更新完成！共 {len(all_news)} 則新聞已寫入 {json_path}")

if __name__ == "__main__":
    main()
