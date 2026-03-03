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
    print("🔎 正在過濾保險業深度研究與專業新聞...")
    
    # 使用 OR 邏輯組合專業關鍵字
    # 包含：保險業界面、調查報告、中期計畫、金融廳動態
    keywords = [
        '"保険業界"', 
        '"ファクトブック"', 
        '"意識調査"', 
        '"中期経営計画"', 
        '"新商品発表"',
        '"金融庁 監督"'
    ]
    query = " OR ".join(keywords)
    rss_url = f"https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP%3Aja"
    
    articles = []
    # 專業黑名單：過濾掉一般的社會案件或廣告
    PROFESSIONAL_BLACKLIST = ["逮捕", "火災", "事故現場", "保険金詐欺"]

    try:
        response = requests.get(rss_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")
        items = soup.find_all("item")
        
        for item in items:
            title = item.title.text
            link = item.link.text
            
            # 邏輯過濾：
            # 1. 排除黑名單
            if any(word in title for word in PROFESSIONAL_BLACKLIST):
                continue
                
            # 2. 強化過濾：必須包含以下「從業人員」感興趣的詞
            pro_filters = ["発行", "調査", "発表", "開始", "導入", "DX", "戦略"]
            if any(word in title for word in pro_filters):
                articles.append({
                    "title": title,
                    "link": link,
                    "date": TODAY_STR,
                    "source": "日本業界動態"
                })

            if len(articles) >= 10: break
                
        print(f"✅ 篩選完成，共找到 {len(articles)} 則專業深度新聞。")
    except Exception as e:
        print(f"❌ 抓取失敗: {e}")
        
    return articles
#3.5 論文定期更新
#
#
def get_journal_papers():
    journals = [
        "Journal of Financial Economics", "Journal of Banking and Finance", 
        "Journal of Corporate Finance", "Journal of Japanese International Economy",
        "Journal of Money, Credit and Banking", "Journal of Financial and Quantitative Analysis",
        "Review of Financial Studies", "Journal of Risk and Insurance", "Insurance: Mathematics and Economics"
    ]
    
    all_papers = []
    print(f"🔎 開始監測 {len(journals)} 本金融頂刊...")

    for j in journals:
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
                    clean_title = raw_title.split(' - ')[0].split(' | ')[0]
                    
                    # --- 縮排修正區開始 ---
                    raw_link = link_tag.get_text()
                    if not raw_link or "http" not in raw_link:
                        if link_tag.next_sibling:
                            raw_link = str(link_tag.next_sibling).strip()
                        else:
                            raw_link = ""

                    if "http" in raw_link:
                        all_papers.append({
                            "title": clean_title.strip(),
                            "link": raw_link,
                            "journal": j,
                            "date": TODAY_STR
                        })
                        count += 1
                    # --- 縮排修正區結束 ---

                if count >= 3: 
                    break 
            print(f"✅ {j}: 已抓取 {count} 篇")
        except Exception as e:
            print(f"❌ {j} 抓取失敗: {e}")
            
    return all_papers
# =========================
# 4. 執行與儲存
# =========================
def main():
    # 1. 確保輸出目錄存在
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 2. 執行抓取
    tw_news = get_taiwan_news()
    jp_news = get_japan_news()
    papers_list = get_journal_papers()  # 改名避免混淆
    
    # --- 處理新聞資料 ---
    all_news = tw_news + jp_news
    if all_news:
        df_news = pd.DataFrame(all_news).drop_duplicates(subset="title")
        all_news = df_news.to_dict('records')
    else:
        all_news = [{
            "title": "今日暫無更新新聞",
            "link": "#",
            "date": TODAY_STR,
            "source": "系統訊息"
        }]

    # 寫入新聞 JSON
    news_json_path = os.path.join(OUTPUT_DIR, "news_data.json")
    with open(news_json_path, 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=4)
        
    print(f"✅ 新聞更新完成！存入 {len(all_news)} 則 (台:{len(tw_news)}/日:{len(jp_news)})")

    # --- 處理論文資料 ---
    if papers_list:
        # 論文也做去重處理
        df_papers = pd.DataFrame(papers_list).drop_duplicates(subset="title")
        papers_final = df_papers.to_dict('records')
    else:
        papers_final = [] # 如果沒抓到就留空列表

    # 寫入論文 JSON
    paper_json_path = os.path.join(OUTPUT_DIR, "paper_data.json")
    with open(paper_json_path, 'w', encoding='utf-8') as f:
        json.dump(papers_final, f, ensure_ascii=False, indent=4)
        
    print(f"✅ 論文更新完成！共存入 {len(papers_final)} 篇論文。")

if __name__ == "__main__":
    main()
