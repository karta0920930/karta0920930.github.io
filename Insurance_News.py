import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import os
import json
import warnings
from bs4 import XMLParsedAsHTMLWarning

# =========================
# 1. 基本設定
# =========================
# 忽略 Google News RSS 的解析警告
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

OUTPUT_DIR = "data"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

TODAY_STR = datetime.datetime.today().strftime("%Y-%m-%d")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# =========================
# 2. 爬取台灣新聞 (Yahoo 新聞)
# =========================
def get_taiwan_news():
    print("🔎 嘗試抓取台灣保險新聞 (Yahoo)...")
    url = "https://tw.news.yahoo.com/search?p=%E4%BF%9D%E9%9A%AA&fr=news"
    articles = []
    TW_BLACKLIST = ["保險套", "廣告", "發財", "色情"]
    
    # --- 設定門檻：標題必須出現「保險」幾次以上 ---
    REQUIRED_COUNT = 3  # 如果要更嚴格，可以改成 2
    # ------------------------------------------

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("h3")
        
        for item in items:
            title_tag = item.find("a")
            if title_tag:
                raw_title = title_tag.get_text(strip=True)
                href = title_tag.get('href', '')
                
                # 清理標題來源文字
                clean_title = raw_title.split(' - ')[0].split(' | ')[0].split(' (')[0]

                # 1. 過濾黑名單
                if any(word in clean_title for word in TW_BLACKLIST):
                    continue

                # 2. 關鍵字頻率檢查：計算「保險」出現的次數
                # 注意：次數越多，過濾越嚴格，相對的新聞量會變少
                if clean_title.count("保險") < REQUIRED_COUNT:
                    continue

                if href and len(clean_title) > 10:
                    if not href.startswith('http'):
                        href = "https://tw.news.yahoo.com" + href
                    
                    articles.append({
                        "title": clean_title,
                        "link": href,
                        "date": TODAY_STR,
                        "source": "台灣新聞"
                    })
            
            if len(articles) >= 10:
                break
                
        print(f"✅ 台灣新聞抓取完成，符合門檻共 {len(articles)} 則。")
    except Exception as e:
        print(f"❌ 台灣抓取錯誤: {e}")
    return articles

# =========================
# 3. 爬取日本新聞 (Google News RSS) - 增強過濾版
# =========================
def get_japan_news():
    print("🔎 正在從專業媒體 (日經/新日本) 獲取情報...")
    articles = []
    
    # --- 來源 1: 新日本保險新聞 (業界最專業) ---
    try:
        shinnichi_url = "https://www.shinnichi.com/"
        res = requests.get(shinnichi_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # 抓取該網站最新消息列表 (通常在 .news_list 或 dl dt 結構中)
        # 注意：此處需根據該網站當前 HTML 結構微調
        news_items = soup.select('.news_list dl') 
        
        for item in news_items:
            title_tag = item.find('a')
            date_tag = item.find('dt') # 抓取日期
            if title_tag:
                title = title_tag.get_text(strip=True)
                link = "https://www.shinnichi.com" + title_tag.get('href', '')
                
                # 關鍵字過濾：確保標題包含「保険」
                if "保険" in title:
                    articles.append({
                        "title": title,
                        "link": link,
                        "date": date_tag.get_text(strip=True) if date_tag else TODAY_STR,
                        "source": "新日本保険新聞"
                    })
            if len(articles) >= 5: break # 先取 5 則
    except Exception as e:
        print(f"❌ 新日本保險新聞抓取失敗: {e}")

    # --- 來源 2: 日経新聞 (金融版) ---
    try:
        # 日經搜尋「保険業界」的結果頁
        nikkei_url = "https://www.nikkei.com/search?keyword=%E4%BF%9D%E9%99%BA%E6%A5%AD%E7%95%8C"
        res = requests.get(nikkei_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # 日經的新聞標題通常在 h3 或特定 class 中
        titles = soup.find_all('h3')
        
        for t in titles:
            link_tag = t.find('a')
            if link_tag:
                title = link_tag.get_text(strip=True)
                href = link_tag.get('href', '')
                
                # 過濾：保險字眼必須出現，且排除付費牆標記(如有)
                if "保険" in title and "https" in href:
                    articles.append({
                        "title": title,
                        "link": href,
                        "date": TODAY_STR,
                        "source": "日本経済新聞"
                    })
            if len(articles) >= 10: break
    except Exception as e:
        print(f"❌ 日經新聞抓取失敗: {e}")

    print(f"✅ 專業新聞篩選完成，共找到 {len(articles)} 則。")
    return articles

# =========================
# 4. 論文監測
# =========================
def get_journal_papers():
    journals = [
        "Journal of Financial Economics", "Journal of Banking and Finance", 
        "Journal of Corporate Finance", "Journal of Risk and Insurance", 
        "Insurance: Mathematics and Economics"
    ]
    
    all_papers = []
    print(f"🔎 開始監測 {len(journals)} 本金融頂刊...")

    for j in journals:
        # 修正：針對期刊名稱搜尋
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
                    
                    # 穩定抓取連結
                    raw_link = link_tag.get_text().strip()
                    if not raw_link and link_tag.next_sibling:
                        raw_link = str(link_tag.next_sibling).strip()

                    if "http" in raw_link:
                        all_papers.append({
                            "title": clean_title.strip(),
                            "link": raw_link,
                            "journal": j,
                            "date": TODAY_STR
                        })
                        count += 1

                if count >= 3: 
                    break 
            print(f"✅ {j}: 已抓取 {count} 篇")
        except Exception as e:
            print(f"❌ {j} 抓取失敗: {e}")
            
    return all_papers

# =========================
# 5. 主程式入口
# =========================
def main():
    # 執行抓取
    tw_news = get_taiwan_news()
    jp_news = get_japan_news()
    papers_list = get_journal_papers()
    
    # 處理新聞資料
    all_news = tw_news + jp_news
    if all_news:
        df_news = pd.DataFrame(all_news).drop_duplicates(subset="title")
        all_news = df_news.to_dict('records')
    else:
        all_news = [{"title": "今日暫無新聞更新", "link": "#", "date": TODAY_STR, "source": "系統"}]

    # 儲存新聞
    with open(os.path.join(OUTPUT_DIR, "news_data.json"), 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=4)
        
    # 儲存論文
    if papers_list:
        df_papers = pd.DataFrame(papers_list).drop_duplicates(subset="title")
        papers_final = df_papers.to_dict('records')
    else:
        papers_final = []

    with open(os.path.join(OUTPUT_DIR, "paper_data.json"), 'w', encoding='utf-8') as f:
        json.dump(papers_final, f, ensure_ascii=False, indent=4)
        
    print(f"🎉 全部更新完成！新聞: {len(all_news)} 則, 論文: {len(papers_final)} 篇。")

if __name__ == "__main__":
    main()
