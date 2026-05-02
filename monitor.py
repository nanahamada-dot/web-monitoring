import requests
from bs4 import BeautifulSoup
import json
import os
import hashlib
import re

# 奈々さんの指示と解析に基づく監視リスト
SITES = [
    {"name": "ブレスユー(TOP)", "url": "https://janpia.mothers-blessu.org/index.html", "selector": "#top_news"},
    {"name": "デジタル未来塾(note)", "url": "https://note.com/digitalmiraijuku", "selector": "[data-testname='cardList']"},
    {"name": "デジタル未来塾(公式サイト)", "url": "https://digital-mirai-juku.com/", "selector": "#home-news, .home-post"},
    {"name": "きらりコーポレーション(公式)", "url": "https://www.kirari-co.info/", "selector": "section#information, .news-list"},
    {"name": "きらりコーポレーション(親子の窓口)", "url": "https://www.kirari-shinmama.com/", "selector": "#news, .instagram-section"},
    {"name": "キャリア・マム(公式)", "url": "https://corp.c-mam.co.jp/", "selector": "#topics, .topics-list"},
    {"name": "キャリア・マム(ブログ)", "url": "https://corp.c-mam.co.jp/blog/", "selector": "main#main, .entry-content"},
    {"name": "うむさんラボ(note)", "url": "https://note.com/umusun_lab_", "selector": "[data-testname='cardList']"},
    {"name": "Shimalov沖縄(Instagram)", "url": "https://www.instagram.com/shimalov.okinawa/", "selector": "article"},
    {"name": "スタンドアップマザー", "url": "https://www.standupmother.com/", "selector": "#home-news"},
    {"name": "オカヤマビューティサミット", "url": "https://okayamabs.org/", "selector": "#top-news, section.home-news"},
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
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 指示されたセレクタで範囲を絞り込む
        target = None
        for s in selector.split(','):
            target = soup.select_one(s.strip())
            if target: break
            
        if not target:
            target = soup.find('main') or soup.find('body')
            
        # スクリプトやスタイルを削除
        for node in target(['script', 'style']):
            node.decompose()
            
        # 【重要】数字を無視して比較（スキの数や〇日前などの変動対策）
        text = re.sub(r'\d+', '', target.get_text())
        
        # 空白を詰めて1行に正規化
        return "".join(text.split())
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
        if current_text is None: continue
            
        current_hash = hashlib.md5(current_text.encode('utf-8')).hexdigest()
        new_data[name] = current_hash

        # 初回は保存のみ、2回目以降の変化を通知
        if name in last_data and last_data[name] != current_hash:
            updates.append(f"【更新検知】 {name}\n{url}")

    if updates and SLACK_WEBHOOK_URL:
        payload = {"text": "\n\n".join(updates)}
        requests.post(SLACK_WEBHOOK_URL, json=payload)

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
