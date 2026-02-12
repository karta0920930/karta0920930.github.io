{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 7,
   "id": "27135b1d-d579-43cf-a2b5-84ba590098fa",
   "metadata": {},
   "outputs": [
    {
     "ename": "IndentationError",
     "evalue": "unindent does not match any outer indentation level (<string>, line 56)",
     "output_type": "error",
     "traceback": [
      "  \u001b[36mFile \u001b[39m\u001b[32m<string>:56\u001b[39m\n\u001b[31m    \u001b[39m\u001b[31mreturn pd.DataFrame(articles)\u001b[39m\n                                 ^\n\u001b[31mIndentationError\u001b[39m\u001b[31m:\u001b[39m unindent does not match any outer indentation level\n"
     ]
    }
   ],
   "source": [
    "import requests\n",
    "from bs4 import BeautifulSoup\n",
    "import pandas as pd\n",
    "import datetime\n",
    "import matplotlib.pyplot as plt\n",
    "import os\n",
    "import matplotlib\n",
    "\n",
    "# --- 1. 路徑與設定 (修正為相對路徑) ---\n",
    "OUTPUT_DIR = \"data\"\n",
    "if not os.path.exists(OUTPUT_DIR):\n",
    "    os.makedirs(OUTPUT_DIR)\n",
    "\n",
    "KEYWORD = \"保険\"\n",
    "TODAY = datetime.datetime.today().strftime(\"%Y-%m-%d\")\n",
    "\n",
    "categories = {\n",
    "    \"再保険\": [\"再保険\", \"reinsurance\"],\n",
    "    \"ESG\": [\"ESG\", \"サステナ\", \"気候変動\", \"脫炭素\"],\n",
    "    \"災害リスク\": [\"地震\", \"台風\", \"洪水\", \"豪雨\"],\n",
    "    \"生命保険\": [\"生命保険\", \"生保\"],\n",
    "    \"損害保険\": [\"損保\", \"火災保険\", \"自動車保険\"]\n",
    "}\n",
    "\n",
    "# --- 2. 爬取函數 ---\n",
    "def get_nikkei_news():\n",
    "    url = f\"https://www.nikkei.com/search?keyword={KEYWORD}\"\n",
    "    headers = {\"User-Agent\": \"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\"}\n",
    "    try:\n",
    "        response = requests.get(url, headers=headers, timeout=10)\n",
    "        soup = BeautifulSoup(response.text, \"html.parser\")\n",
    "        articles = []\n",
    "        for a in soup.find_all(\"a\"):\n",
    "            title = a.text.strip()\n",
    "            link = a.get(\"href\")\n",
    "            if link and link.startswith(\"/\"):\n",
    "                link = \"https://www.nikkei.com\" + link\n",
    "            if KEYWORD in title and len(title) > 5:\n",
    "                articles.append({\"title\": title, \"link\": link, \"date\": TODAY})\n",
    "        return pd.DataFrame(articles)\n",
    "    except Exception as e:\n",
    "        print(f\"抓取失敗: {e}\")\n",
    "        return pd.DataFrame()\n",
    "\n",
    "def categorize(title):\n",
    "    for category, keywords in categories.items():\n",
    "        for word in keywords:\n",
    "            if word in title: return category\n",
    "    return \"その他\"\n",
    "\n",
    "# --- 3. 主流程 ---\n",
    "def main():\n",
    "    print(\"🔎 抓取新聞中...\")\n",
    "    df = get_nikkei_news()\n",
    "    if df.empty:\n",
    "        print(\"❌ 沒有新資料\")\n",
    "        return\n",
    "\n",
    "    df.drop_duplicates(subset=\"title\", inplace=True)\n",
    "    df[\"category\"] = df[\"title\"].apply(categorize)\n",
    "\n",
    "    # --- 4. 輸出 JSON (網頁用) ---\n",
    "    json_output = os.path.join(OUTPUT_DIR, \"news_data.json\")\n",
    "    df.to_json(json_output, orient=\"records\", force_ascii=False, indent=4)\n",
    "    print(f\"✅ JSON 已更新: {json_output}\")\n",
    "\n",
    "    # --- 5. 繪圖 (加入 Linux 環境保護) ---\n",
    "    try:\n",
    "        plt.figure(figsize=(10, 6))\n",
    "        df[\"category\"].value_counts().plot(kind=\"bar\")\n",
    "        plt.title(\"Insurance News Distribution\")\n",
    "        plt.tight_layout()\n",
    "        plt.savefig(os.path.join(OUTPUT_DIR, \"category_distribution.png\"))\n",
    "        plt.close()\n",
    "    except Exception as e:\n",
    "        print(f\"⚠️ 繪圖跳過 (Linux 環境字體限制): {e}\")\n",
    "\n",
    "if __name__ == \"__main__\":\n",
    "    main()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "c63c1126-2e35-4871-af16-0d996d139051",
   "metadata": {},
   "outputs": [],
   "source": [
    "import matplotlib.font_manager as fm\n",
    "for font in fm.findSystemFonts():\n",
    "    print(font)"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.14.1"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
