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
    print("🔎 嘗試抓取日本保險新聞 (Google News RSS)...")
    rss_url = "https://news.google.com/rss/search?q=%E4%BF%9D%E9%99%BA&hl=ja&gl=JP&ceid=JP%3Aja"
    articles = []
    try:
        response = requests.get(rss_url, headers=HEADERS, timeout=15)
        # 關鍵修正：RSS 是 XML 格式，我們直接用 find_all('item')
        soup = BeautifulSoup(response.content, "xml") # 如果這行報錯，改用 "html.parser"
        items = soup.find_all("item")
        
        for item in items:
            title = item.title.text if item.title else "無標題"
            # 關鍵修正：嘗試多種方式獲取連結
            link = ""
            if item.link:
                link = item.link.text
            elif item.find("link"):
                link = item.find("link").next_sibling.strip()
            
            if link and len(title) > 10:
                articles.append({
                    "title": title,
                    "link": link,
                    "date": TODAY_STR,
                    "source": "日本新聞"
                })
            if len(articles) >= 15: break
            
        print(f"✅ 成功抓到 {len(articles)} 則日本新聞")
    except Exception as e:
        # 如果 "xml" 解析器失敗，換成 "html.parser" 的保險寫法
        print(f"⚠️ XML 解析失敗，嘗試相容模式... Error: {e}")
        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("item")
        for item in items:
            # 在 html.parser 下，標籤會變小寫
            t = item.find("title")
            l = item.find("link")
            if t and l:
                articles.append({
                    "title": t.get_text(),
                    "link": l.next_sibling.strip() if l.next_sibling else l.get_text(),
                    "date": TODAY_STR,
                    "source": "日本新聞"
                })
    return articles
#3.5 論文定期更新
#
#
def get_journal_papers():
    print("🔎 正在檢索 Journal of Risk and Insurance 最新論文...")
    # 使用 Google News RSS 搜尋學術期刊更新，這對 GitHub Actions 最穩定
    rss_url = "https://news.google.com/rss/search?q=source:%22Journal+of+Risk+and+Insurance%22&hl=en-US&gl=US&ceid=US:en"
    papers = []
    try:
        response = requests.get(rss_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item")

        for item in items:
            papers.append({
                "title": item.title.text,
                "link": item.link.text,
                "date": item.pubDate.text if item.pubDate else TODAY_STR,
                "journal": "JRI"
            })
            if len(papers) >= 10: break
        print(f"✅ 成功抓取 {len(papers)} 篇最新論文")
    except Exception as e:
        print(f"❌ 論文抓取失敗: {e}")
    return papers
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
