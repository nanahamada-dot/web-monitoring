import requests
from bs4 import BeautifulSoup
import json
import os
import hashlib
import re

# 奈々さんが一軒ずつ調査し、指定したターゲット地点のリスト
SITES = [
    {"name": "ブレスユー(TOP)", "url": "https://janpia.mothers-blessu.org/index.html", "selector": "#top_news"},
    {"name": "デジタル未来塾(note)", "url": "https://note.com/digitalmiraijuku", "selector": "[data-testname='cardList'] h3"},
    {"name": "デジタル未来塾(公式サイト)", "url": "https://digital-mirai-juku.com/", "selector": "#home-news, .home-post"},
    {"name": "きらりコーポレーション(公式)", "url": "https://www.kirari-co.info/", "selector": "#info-list"},
    {"name": "きらりコーポレーション(親子の窓口)", "url": "https://www.kirari-shinmama.com/", "selector": "#news"},
    {"name": "キャリア・マム(公式)", "url": "https://corp.c-mam.co.jp/", "selector": "#topics"},
    {"name": "キャリア・マム(ブログ)", "url": "https://corp.c-mam.co.jp/blog/", "selector": "main#main, .entry-content"},
    {"name": "うむさんラボ(note)", "url": "https://note.com/umusun_lab_", "selector": "[data-testname='cardList'] h3"},
    {"name": "Shimalov沖縄(Instagram)", "url": "https://www.instagram.com/shimalov.okinawa/", "selector": "article"},
    {"name": "スタンドアップマザー", "url": "https://www.standupmother.com/", "selector": "#home-news"},
    {"name": "オカヤマビューティサミット", "url": "https://okayamabs.org/", "selector": "#top-news"},
    {"name": "ミアフォルツァ(公式)", "url": "https://miaforza.jp/report/", "selector": "main, .post-list"},
    {"name": "ミアフォルツァ(Instagram)", "url": "https://www.instagram.com/miaforza2021/", "selector": "article"},
    {"name": "CCOBI(NEWS)", "url": "https://cco-bi.com/", "selector": "#news"},
    {"name": "CCOBI(BLOG)", "url": "https://cco-bi.com/", "selector": "#blog"},
    {"name": "コグニティ", "url": "https://cognitee.info/camelliaport/", "selector": ".news-list, #information"},
    {"name": "キズキ", "url": "https://kizuki-corp.com/single-mother-support/", "selector": "main, .post-list"}
]

SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')
DATA_FILE = 'last_content.json'

def get_site_text(url, selector):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=25)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 奈々さんが指定したターゲット（セレクタ）をピンポイントで抽出
        target = None
        for s in selector.split(','):
            target = soup.select_one(s.strip())
            if target: break
            
        if not target:
            # 指定場所が見つからない場合はスキップ（誤通知防止）
            return None
            
        # ターゲットの中にある「不要なタグ」を事前に抹殺
        for node in target(['script', 'style', 'nav', 'footer', 'button', 'input']):
            node.decompose()
            
        # ターゲット内の純粋なテキストのみを取得
        text = target.get_text()
        
        # 【徹底ノイズ除去】
        # 1. 改行、タブ、全角・半角スペースをすべて削除
        # 2. 数字、記号、アルファベットもすべて削除
        # 3. 残った「日本語の文字」だけを隙間なく並べる
        clean_text = "".join(re.findall(r'[ぁ-んァ-ン一-龥]+', text))
        
        return clean_text
    except:
        return None

def main():
    last_data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                last_data = json.load(f)
        except: pass

    new_data = {}
    updates = []

    for site in SITES:
        name, url, selector = site['name'], site['url'], site['selector']
        current_text = get_site_text(url, selector)
        
        # ターゲット内に「意味のある日本語」がない場合は無視
        if not current_text or current_text == "":
            continue
            
        # 抽出した日本語のみの並びからハッシュを作成
        current_hash = hashlib.md5(current_text.encode('utf-8')).hexdigest()
        new_data[name] = current_hash

        # 過去の「ターゲット内の日本語」と比較
        if name in last_data and last_data[name] != current_hash:
            # 過去データが空でない場合のみ通知
            if last_data[name]:
                updates.append(f"【更新検知】 {name}\n{url}")

    if updates and SLACK_WEBHOOK_URL:
        payload = {"text": "\n\n".join(updates)}
        requests.post(SLACK_WEBHOOK_URL, json=payload)

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
