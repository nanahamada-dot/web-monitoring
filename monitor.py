import requests
from bs4 import BeautifulSoup
import json
import os

# 監視対象リスト
SITES = [
    {"name": "デジタル未来塾", "url": "https://digital-mirai-juku.com/"},
    {"name": "デジタル未来塾(note)", "url": "https://note.com/digitalmiraijuku"},
    {"name": "ブレスユー(TOP)", "url": "https://janpia.mothers-blessu.org/index.html"},
    {"name": "ブレスユー(NEWS)", "url": "https://janpia.mothers-blessu.org/news/index.html"},
    {"name": "きらりコーポレーション", "url": "https://www.kirari-co.info/blog"},
    {"name": "キャリア・マム", "url": "https://corp.c-mam.co.jp/"},
    {"name": "キャリア・マム(ブログ)", "url": "https://corp.c-mam.co.jp/blog/"},
    {"name": "うむさんラボ(note)", "url": "https://note.com/umusun_lab_"},
    {"name": "うむさんラボ(公式サイト)", "url": "https://umusunlab.co.jp/"},
    {"name": "スタンドアップマザー", "url": "https://www.standupmother.com/"},
    {"name": "オカヤマビューティサミット", "url": "https://okayamabs.org/"},
    {"name": "オカヤマビューティサミット(投稿)", "url": "https://okayamabs.org/?post_type=post"},
    {"name": "ミアフォルツァ", "url": "https://miaforza.jp/report/"},
    {"name": "CCOBI(TOP)", "url": "https://cco-bi.com/"},
    {"name": "CCOBI(ニュース)", "url": "https://cco-bi.com/news/"},
    {"name": "CCOBI(ブログ)", "url": "https://cco-bi.com/blog/"},
    {"name": "コグニティ", "url": "https://cognitee.info/camelliaport/"},
    {"name": "キズキ", "url": "https://kizuki-corp.com/single-mother-support/"}
]

DB_FILE = "last_content.json"
WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

def get_content(url):
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        # 不要なタグを除去してテキストのみ抽出（差分判定の精度を上げるため）
        for s in soup(['script', 'style']):
            s.decompose()
        return soup.get_text()[:2000] # 前半2000文字程度で判定
    except Exception as e:
        print(f"Error checking {url}: {e}")
        return None

def main():
    # 前回データの読み込み
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            last_data = json.load(f)
    else:
        last_data = {}

    current_data = {}
    updates = []

    for site in SITES:
        name = site["name"]
        url = site["url"]
        content = get_content(url)
        
        if content:
            current_data[name] = hash(content) # 内容をハッシュ化して保存
            if name in last_data:
                if last_data[name] != current_data[name]:
                    updates.append(f"【更新検知】{name}\n{url}")
            else:
                print(f"Initial check for {name}")

    # Slack通知
    if updates and WEBHOOK_URL:
        message = "\n\n".join(updates)
        requests.post(WEBHOOK_URL, json={"text": message})

    # データ更新保存
    with open(DB_FILE, "w") as f:
        json.dump(current_data, f)

if __name__ == "__main__":
    main()
