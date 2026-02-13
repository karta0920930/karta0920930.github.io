import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import os
import json

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
# 2. 爬取台灣新聞 (改用 Yahoo 新聞 - 保險關鍵字)
# =========================
def get_taiwan_news():
    print("🔎 嘗試抓取台灣保險新聞 (Yahoo)...")
    # 抓取 Yahoo 搜尋「保險」的最新新聞結果
    url = "https://tw.news.yahoo.com/search?p=%E4%BF%9D%E9%9A%AA&fr=news"
    articles = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Yahoo 新聞標題通常在 <h3> 中
        items = soup.find_all("h3")
        for item in items:
            title_tag = item.find("a")
            if title_tag:
                title = title_tag.get_text(strip=True)
                href = title_tag.get('href')
                
                # 確保連結完整且標題長度合理
                if href and len(title) > 8:
                    if not href.startswith('http'):
                        href = "https://tw.news.yahoo.com" + href
                    
                    articles.append({
                        "title": title,
                        "link": href,
                        "date": TODAY_STR,
                        "source": "台灣新聞"
                    })
            if len(articles) >= 15: break
    except Exception as e:
        print(f"❌ 台灣抓取錯誤: {e}")
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
        
        links = soup.find_all("a")
        for link in links:
            title = link.get_text(strip=True)
            href = link.get('href')
            
            # 日經新聞標題通常較長且包含關鍵字
            if href and "保険" in title and len(title) > 15:
                full_link = href if href.startswith('http') else "https://www.nikkei.com" + href
                
                articles.append({
                    "title": title,
                    "link": full_link,
                    "date": TODAY_STR,
                    "source": "日本新聞"
                })
                if len(articles) >= 20: break
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
    
    # 移除重複標題
    if all_news:
        df = pd.DataFrame(all_news).drop_duplicates(subset="title")
        all_news = df.to_dict('records')
    
    if not all_news:
        all_news = [{
            "title": "今日暫無更新新聞",
            "link": "#",
            "date": TODAY_STR,
            "source": "台灣新聞"
        }]

    # 直接使用 json 庫寫入，避免依賴 pandas 的特殊格式
    json_path = os.path.join(OUTPUT_DIR, "news_data.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=4)
        
    print(f"✅ 更新完成！抓到 {len(tw_news)} 則台灣新聞，{len(jp_news)} 則日本新聞。")

if __name__ == "__main__":
    main()
