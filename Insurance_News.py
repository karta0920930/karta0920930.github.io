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
    print("🔎 正在過濾日本保險業深度研究與專業新聞...")
    keywords = [
        '"保険業界"', '"ファクトブック"', '"意識調査"', 
        '"中期経営計画"', '"新商品発表"', '"金融庁 監督"'
    ]
    query = " OR ".join(keywords)
    rss_url = f"https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP%3Aja"
    
    articles = []
    PROFESSIONAL_BLACKLIST = ["逮捕", "避妊", "事件"]
    
    # --- 設定門檻：標題必須出現「保険」幾次以上 ---
    REQUIRED_COUNT = 3
    # ------------------------------------------

    try:
        response = requests.get(rss_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")
        items = soup.find_all("item")
        
        for item in items:
            title_tag = item.find("title")
            title = title_tag.get_text() if title_tag else "無標題"
            
            link = ""
            link_tag = item.find("link")
            if link_tag:
                link = link_tag.get_text().strip()
                if not link and link_tag.next_sibling:
                    link = str(link_tag.next_sibling).strip()
            
            if not link or not link.startswith("http"):
                continue

            # 1. 黑名單過濾
            if any(word in title for word in PROFESSIONAL_BLACKLIST):
                continue

            # 2. 頻率檢查：計算日文「保険」出現次數
            if title.count("保険") < REQUIRED_COUNT:
                continue
                
            # 3. 從業人員專業詞過濾
            pro_filters = ["発行", "調査", "発表", "開始", "導入", "DX", "戦略", "経営"]
            if any(word in title for word in pro_filters):
                articles.append({
                    "title": title,
                    "link": link,
                    "date": TODAY_STR,
                    "source": "日本業界動態"
                })

            if len(articles) >= 10: 
                break
                
        print(f"✅ 日本新聞篩選完成，符合門檻共找到 {len(articles)} 則。")
    except Exception as e:
        print(f"❌ 日本新聞抓取失敗: {e}")
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
