import requests
from bs4 import BeautifulSoup
import json
import os
import hashlib

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

SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')
DATA_FILE = 'last_content.json'

def get_site_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.37 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.37'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 不要なタグを削除してノイズを減らす
        for script_or_style in soup(['script', 'style', 'header', 'footer', 'nav']):
            script_or_style.decompose()
            
        # 純粋なテキストのみを取得し、余計な空白を詰める
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        clean_text = '\n'.join(chunk for chunk in lines if chunk)
        return clean_text
    except Exception as e:
        print(f"Error checking {url}: {e}")
        return None

def main():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            last_data = json.load(f)
    else:
        last_data = {}

    new_data = {}
    updates = []

    for site in SITES:
        name = site['name']
        url = site['url']
        print(f"Checking {name}...")
        
        current_text = get_site_text(url)
        if current_text is None:
            continue
            
        current_hash = hashlib.md5(current_text.encode('utf-8')).hexdigest()
        new_data[name] = current_hash

        if name in last_data:
            if last_data[name] != current_hash:
                # 変化があった場合、文字数の差をチェック（あまりに小さい変化は無視）
                # 初回は比較対象がないため通知しません
                updates.append(f"【更新検知】 {name}\n{url}")
        else:
            print(f"First time checking {name}. Saving data.")

    # Slack送信
    if updates and SLACK_WEBHOOK_URL:
        payload = {"text": "\n\n".join(updates)}
        requests.post(SLACK_WEBHOOK_URL, json=payload)

    # データ保存
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
