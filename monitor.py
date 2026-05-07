import requests
from bs4 import BeautifulSoup
import json
import os
import hashlib
import re

# 奈々さんの精密調査に基づき確定した、全17サイトの「急所」リスト
SITES = [
    {"name": "ブレスユー(TOP)", "url": "https://janpia.mothers-blessu.org/index.html", "selector": ".right-box"},
    {"name": "デジタル未来塾(note)", "url": "https://note.com/digitalmiraijuku", "selector": ".max-w-\\[var\\(--size-content\\)\\]"},
    {"name": "デジタル未来塾(公式サイト)", "url": "https://digital-mirai-juku.com/", "selector": ".news-box"},
    {"name": "きらりコーポレーション(公式)", "url": "https://www.kirari-co.info/", "selector": "#pro-gallery-margin-container-comp-lf0r4o17"},
    {"name": "きらりコーポレーション(親子の窓口)", "url": "https://www.kirari-shinmama.com/", "selector": "[data-hook='post-list-pro-gallery-container']"},
    {"name": "キャリア・マム(公式)", "url": "https://corp.c-mam.co.jp/", "selector": ".postList"},
    {"name": "キャリア・マム(ブログ)", "url": "https://corp.c-mam.co.jp/blog/", "selector": "main article"},
    {"name": "うむさんラボ(note)", "url": "https://note.com/umusun_lab_", "selector": ".max-w-\\[var\\(--size-content\\)\\]"},
    {"name": "Shimalov沖縄(Instagram)", "url": "https://www.instagram.com/shimalov.okinawa/", "selector": "article"},
    {"name": "スタンドアップマザー", "url": "https://www.standupmother.com/", "selector": "#reports"}, # 今回確定した正解ID
    {"name": "オカヤマビューティサミット", "url": "https://okayamabs.org/", "selector": "#top-news"},
    {"name": "ミアフォルツァ(公式)", "url": "https://miaforza.jp/report/", "selector": ".report-list-inner"},
    {"name": "ミアフォルツァ(Instagram)", "url": "https://www.instagram.com/miaforza2021/", "selector": "article"},
    {"name": "CCOBI(NEWS)", "url": "https://cco-bi.com/", "selector": "#news"},
    {"name": "CCOBI(BLOG)", "url": "https://cco-bi.com/", "selector": "#index-blog"},
    {"name": "コグニティ", "url": "https://cognitee.info/camelliaport/", "selector": ".wp-block-post-template"},
    {"name": "キズキ", "url": "https://kizuki-corp.com/single-mother-support/", "selector": "ul.cat_postlist__ul"}
    {"name": "キャリア・マム(公式)", "url": "https://corp.c-mam.co.jp/", "selector": "#ltg_post_list-3"},
]

SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')
DATA_FILE = 'last_content.json'

def get_site_text(url, selector):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        target = None
        for s in selector.split(','):
            target = soup.select_one(s.strip())
            if target: break
            
        if not target:
            return None
            
        # 不要なタグを事前に削除
        for node in target(['script', 'style', 'nav', 'footer', 'button', 'input']):
            node.decompose()
            
        text = target.get_text()
        
        # 【徹底ノイズ除去】
        # 日本語と英数字のみを隙間なく連結。
        # これにより、サイト側の微細な空白や記号のズレによる誤通知を物理的に防ぎます。
        clean_text = "".join(re.findall(r'[ぁ-んァ-ン一-龥a-zA-Z0-9]+', text))
        
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
        
        if not current_text:
            continue
            
        current_hash = hashlib.md5(current_text.encode('utf-8')).hexdigest()
        new_data[name] = current_hash

        if name in last_data and last_data[name] != current_hash:
            # 日本語内容に変化があった時だけ通知
            updates.append(f"【更新検知】 {name}\n{url}")

    if updates and SLACK_WEBHOOK_URL:
        payload = {"text": "\n\n".join(updates)}
        requests.post(SLACK_WEBHOOK_URL, json=payload)

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
