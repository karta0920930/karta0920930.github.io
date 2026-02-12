import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import os

# =========================
# 1. 基本設定與路徑 (GitHub 環境專用)
# =========================
# 確保資料會存在根目錄下的 data 資料夾
OUTPUT_DIR = "data"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

KEYWORD = "保険"
# 網頁顯示用的日期格式
TODAY_STR = datetime.datetime.today().strftime("%Y-%m-%d")

# =========================
# 2. 新聞爬取函數
# =========================
def get_nikkei_news():
    url = f"https://www.nikkei.com/search?keyword={KEYWORD}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")
        articles = []
        
        # 爬取連結與標題
        for a in soup.find_all("a"):
            title = a.text.strip()
            link = a.get("href")
            
            if link and link.startswith("/"):
                link = "https://www.nikkei.com" + link
            
            # 過濾條件：標題包含關鍵字且長度合理
            if KEYWORD in title and len(title) > 5:
                articles.append({
                    "title": title,
                    "link": link,
                    "date": TODAY_STR,
                    "category": "最新動態"
                })
        return pd.DataFrame(articles)
    except Exception as e:
        print(f"❌ 抓取過程發生錯誤: {e}")
        return pd.DataFrame()

# =========================
# 3. 執行主流程
# =========================
def main():
    print(f"🔎 開始抓取「{KEYWORD}」相關新聞...")
    df = get_nikkei_news()

    if df.empty:
        print("⚠️ 未找到相關新聞，請稍後再試。")
        return

    # 移除重複標題
    df.drop_duplicates(subset="title", inplace=True)

    # 輸出網頁用的 JSON 檔案
    json_path = os.path.join(OUTPUT_DIR, "news_data.json")
    df.to_json(json_path, orient="records", force_ascii=False, indent=4)
    print(f"✅ JSON 檔案更新成功: {json_path}")

    # 同時產生 Excel 備份供存檔
    excel_path = os.path.join(OUTPUT_DIR, f"news_log_{TODAY_STR}.xlsx")
    df.to_excel(excel_path, index=False)
    print(f"✅ Excel 備份更新成功: {excel_path}")

if __name__ == "__main__":
    main()
