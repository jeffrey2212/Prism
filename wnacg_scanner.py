#!/usr/bin/env python3
"""
WNACG 掃描器 - 獨立版本
只負責掃描和發現新本子，不下載

輸出：新發現的 aid 列表（JSON 格式）
"""

import json
import sqlite3
import re
import sys
from pathlib import Path
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ 缺少依賴：pip install requests beautifulsoup4")
    sys.exit(1)

# 配置
DOWNLOAD_DIR = Path("~/Downloads/wnacg").expanduser()
DB_PATH = DOWNLOAD_DIR / ".downloaded.db"
WNACG_BASE = "https://wnacg.com"

def init_db():
    """初始化 SQLite 資料庫"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS downloaded (
            aid INTEGER PRIMARY KEY,
            title TEXT,
            download_time TEXT,
            image_count INTEGER,
            folder_name TEXT
        )
    ''')
    conn.commit()
    return conn

def is_downloaded(aid):
    """檢查是否已下載"""
    conn = init_db()
    c = conn.cursor()
    c.execute("SELECT aid FROM downloaded WHERE aid=?", (aid,))
    result = c.fetchone()
    conn.close()
    return result is not None

def scan_latest_pages(max_pages=3):
    """掃描最新上傳頁面，返回新發現的 aid 列表"""
    print(f"🔍 掃描最新上傳 (共{max_pages}頁)...", file=sys.stderr)
    
    new_found = []
    
    for page in range(1, max_pages + 1):
        url = f"https://wnacg.com/photos-index-page-{page}.html"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://wnacg.com/'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找所有本子連結
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/photos-slide-aid-' in href:
                    aid_match = re.search(r'aid-(\d+)', href)
                    if aid_match:
                        aid = int(aid_match.group(1))
                        
                        # 檢查是否已下載
                        if not is_downloaded(aid):
                            title = a.get_text(strip=True)
                            new_found.append({
                                'aid': aid,
                                'title': title,
                                'url': WNACG_BASE + href
                            })
                            print(f"🆕 發現：aid={aid} {title}", file=sys.stderr)
            
        except Exception as e:
            print(f"❌ 掃描頁面 {page} 失敗：{e}", file=sys.stderr)
    
    return new_found

def main():
    """主函數"""
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    
    new_found = scan_latest_pages(pages)
    
    # 輸出 JSON 結果
    result = {
        'scan_time': datetime.now().isoformat(),
        'pages_scanned': pages,
        'new_count': len(new_found),
        'new_items': new_found
    }
    
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
