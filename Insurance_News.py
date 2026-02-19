import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import os
import json
import warnings
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
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
    TW_BLACKLIST = ["保險套",  "廣告", "發財"]
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Yahoo 新聞標題通常在 <h3> 中
        items = soup.find_all("h3")
        for item in items:
            title_tag = item.find("a")
            if title_tag:
                raw_title = title_tag.get_text(strip=True)
                href = title_tag.get('href')
                
                # --- 抓重點邏輯 1：移除來源字樣 ---
                # 很多標題會長這樣：「保險業獲利創新高 - Yahoo奇摩新聞」
                # 我們只取 '-' 或是 '|' 之前的內容
                clean_title = raw_title.split(' - ')[0].split(' | ')[0].split(' (')[0]

                # --- 抓重點邏輯 2：過濾 ---
                if any(word in clean_title for word in TW_BLACKLIST):
                    continue

                if href and len(clean_title) > 10:
                    if not href.startswith('http'):
                        href = "https://tw.news.yahoo.com" + href
                    
                    articles.append({
                        "title": clean_title, # 使用清理後的重點標題
                        "link": href,
                        "date": TODAY_STR,
                        "source": "台灣新聞"
                    })
            
            # --- 數量限制：限 10 則 ---
            if len(articles) >= 10:
                break
                
        print(f"✅ 台灣新聞更新完成，共 {len(articles)} 則精華。")
    except Exception as e:
        print(f"❌ 台灣抓取錯誤: {e}")
    return articles

# =========================
# 3. 爬取日本新聞 (日經新聞)
# =========================
# 忽略討厭的警告訊息
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def get_japan_news():
    print("🔎 正在精確抓取日本保險產業新聞 (穩定限制版)...")
    # 搜尋關鍵字：確保精準對準業界與壽險/損害保險
    rss_url = "https://news.google.com/rss/search?q=%22%E4%BF%9D%E9%99%BA%E6%A5%AD%E7%95%8C%22%20OR%20%22%E7%94%9F%E5%91%BD%E4%BF%9D%E9%99%BA%22%20OR%20%22%E6%90%8D%E5%AE%B3%E4%BF%9D%E9%99%BA%22&hl=ja&gl=JP&ceid=JP%3Aja"
    
    articles = []
    # 精確黑名單
    JP_BLACKLIST = ["保険套", "保険証"]

    try:
        response = requests.get(rss_url, headers=HEADERS, timeout=15)
        # 既然沒有 lxml，我們就統一用 html.parser，但調整抓取標籤的寫法
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 在 html.parser 之下，XML 的 <item> 會被識別為 <item></item>
        items = soup.find_all("item")
        
        for item in items:
            # 嘗試抓取標題與連結
            title_tag = item.find("title")
            link_tag = item.find("link")
            
            if title_tag and link_tag:
                title = title_tag.get_text()
                # 處理 Google News RSS 特有的連結讀取問題
                link = link_tag.next_sibling if link_tag.next_sibling and "http" in str(link_tag.next_sibling) else link_tag.get_text()
                link = str(link).strip()

                # 過濾邏輯
                if any(word in title for word in JP_BLACKLIST):
                    continue
                
                # 標題長度檢查且必須包含核心詞彙
                if len(title) > 15 and "保険" in title:
                    articles.append({
                        "title": title,
                        "link": link,
                        "date": TODAY_STR,
                        "source": "日本新聞"
                    })
            
            # 🔴 強制煞車：最多只拿 10 則，絕對不再噴 100 則
            if len(articles) >= 10:
                break
                
        print(f"✅ 更新完成！成功篩選出 {len(articles)} 則日本精華新聞。")
    except Exception as e:
        print(f"❌ 日本抓取失敗: {e}")
        
    return articles
#3.5 論文定期更新
#
#
def get_journal_papers():
    journals = [
        "Journal of Financial Economics", "Journal of Banking and Finance", 
        "Journal of Corporate Finance", "Journal of Japanese International Economy",
        "Journal of Money, Credit and Banking", "Journal of Financial and Quantitative Analysis",
        "Review of Financial Studies","Journal of Risk and Insurance","Insurance: Mathematics and Economics"
    ]
    
    all_papers = []
    print(f"🔎 開始監測 {len(journals)} 本金融頂刊...")

    for j in journals:
        # 使用 Google News RSS 針對特定期刊搜尋標題
        # 加上 intitle: 確保抓到的是論文標題而非新聞報導
        rss_url = f"https://news.google.com/rss/search?q=intitle:%22{j.replace(' ', '+')}%22&hl=en-US&gl=US&ceid=US:en"
        
        try:
            response = requests.get(rss_url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.find_all("item")

            count = 0
            for item in items:
                title_tag = item.find("title")
                link_tag = item.find("link")
                
                if title_tag and link_tag:
                    raw_title = title_tag.get_text()
                    # 抓重點邏輯：切除標題後方的期刊名稱 (例如 "Title - Journal of...")
                    clean_title = raw_title.split(' - ')[0].split(' | ')[0]
                    
                    # 抓連結邏輯
                    link = link_tag.next_sibling if link_tag.next_sibling and "http" in str(link_tag.next_sibling) else link_tag.get_text()
                    
                    all_papers.append({
                        "title": clean_title.strip(),
                        "link": str(link).strip(),
                        "journal": j,
                        "date": TODAY_STR
                    })
                    count += 1
                if count >= 3: break # 每個期刊取最新 3 篇，避免頁面太長
            print(f"✅ {j}: 已抓取 {count} 篇")
        except Exception as e:
            print(f"❌ {j} 抓取失敗: {e}")
            
    return all_papers
# =========================
# 4. 執行與儲存
# =========================
def main():
    tw_news = get_taiwan_news()
    jp_news = get_japan_news()
    papers = get_journal_papers()
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
    # 儲存論文資料
    with open(os.path.join(OUTPUT_DIR, "paper_data.json"), 'w', encoding='utf-8') as f:
        json.dump(papers, f, ensure_ascii=False, indent=4)
if __name__ == "__main__":
    main()
