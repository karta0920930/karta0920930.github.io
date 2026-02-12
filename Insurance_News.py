import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import os
import matplotlib.pyplot as plt

# =========================
# 1. 基本設定與路徑
# =========================
OUTPUT_DIR = "data"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

KEYWORD = "保険"
TODAY = datetime.datetime.today().strftime("%Y-%m-%d")

# =========================
# 2. 新聞爬取
# =========================
def get_nikkei_news():
    url = f"https://www.nikkei.com/search?keyword={KEYWORD}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        articles = []
        
        # 尋找新聞連結
        for a in soup.find_all("a"):
            title = a.text.strip()
            link = a.get("href")
            if link and link.startswith("/"):
                link = "https://www.nikkei.com" + link
            
            # 簡單過濾：包含關鍵字且長度足夠
            if KEYWORD in title and len(title) > 5:
                articles.append({
                    "title": title,
                    "link": link,
                    "date": TODAY,
                    "category": "保險新聞" # 預設分類
                })
        return pd.DataFrame(articles)
    except Exception as e:
        print(f"抓取失敗: {e}")
        return pd.DataFrame()

# =========================
# 3. 主執行流程
# =========================
def main():
    print("🔎 正在抓取最新保險新聞...")
    df = get_nikkei_news()

    if df.empty:
        print("⚠️ 沒有抓到資料，請檢查網路或網頁結構。")
        return

    # 去重
    df.drop_duplicates(subset="title", inplace=True)

    # 輸出 JSON (這是網頁讀取的重點)
    json_output = os.path.join(OUTPUT_DIR, "news_data.json")
    df.to_json(json_output, orient="records", force_ascii=False, indent=4)
    print(f"✅ 成功產出 JSON: {json_output}")

    # 備份 Excel
    excel_output = os.path.join(OUTPUT_DIR, f"news_{TODAY}.xlsx")
    df.to_excel(excel_output, index=False)
    print(f"✅ 成功產出 Excel 備份: {excel_output}")

if __name__ == "__main__":
    main()
