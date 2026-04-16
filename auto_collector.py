#!/usr/bin/env python3
"""
WNACG 自動化收集器
自動掃描、下載、去重

功能：
1. 掃描 WNACG 最新上傳列表
2. 檢查是否已下載（基於 aid 去重）
3. 自動下載新本子
4. 記錄下載歷史
"""

import json
import sqlite3
import subprocess
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
DB_PATH = Path("~/Downloads/wnacg/.downloaded.db").expanduser()
CONFIG_PATH = Path("~/Downloads/wnacg/.config.json").expanduser()
LOG_PATH = Path("~/Downloads/wnacg/.log.txt").expanduser()

# WNACG 網址
WNACG_BASE = "https://wnacg.com"
WNACG_LATEST = "https://wnacg.com/photos-index-page-1.html"  # 最新上傳

def init_db():
    """初始化 SQLite 資料庫"""
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

def mark_downloaded(aid, title, image_count, folder_name):
    """標記為已下載"""
    conn = init_db()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO downloaded 
        (aid, title, download_time, image_count, folder_name)
        VALUES (?, ?, ?, ?, ?)
    ''', (aid, title, datetime.now().isoformat(), image_count, folder_name))
    conn.commit()
    conn.close()

def get_downloaded_list():
    """獲取已下載列表"""
    conn = init_db()
    c = conn.cursor()
    c.execute("SELECT aid, title, download_time, image_count FROM downloaded ORDER BY download_time DESC")
    results = c.fetchall()
    conn.close()
    return results

def log(message):
    """寫入日誌"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}\n"
    print(log_msg, end='')
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(log_msg)

def sanitize_folder_name(name):
    """清理文件夾名稱"""
    name = re.sub(r'[<>:"/\\|？*]', '', name)
    name = re.sub(r'\s+', ' ', name)
    name = name.strip()
    if len(name) > 100:
        name = name[:100]
    return name

def download_album(url):
    """下載單一本子"""
    from hermes_tools import browser_navigate, browser_get_images
    
    try:
        # 訪問頁面
        nav_result = browser_navigate(url=url)
        if not nav_result.get('success'):
            return False
        
        title = nav_result.get('title', 'unknown')
        clean_title = re.sub(r'\s*-\s*列表.*$', '', title)
        clean_title = re.sub(r'\s*-\s*紳士漫畫.*$', '', clean_title)
        clean_title = sanitize_folder_name(clean_title)
        
        # 提取 aid
        aid_match = re.search(r'aid-(\d+)', url)
        if not aid_match:
            return False
        aid = int(aid_match.group(1))
        
        # 檢查是否已下載
        if is_downloaded(aid):
            log(f"⏭️  已存在，跳過：aid={aid}")
            return False
        
        # 獲取圖片
        images_result = browser_get_images()
        if not images_result.get('success'):
            return False
        
        images = images_result.get('images', [])
        if not images:
            log(f"❌ 未找到圖片：aid={aid}")
            return False
        
        # 創建文件夾
        folder_name = f"{clean_title}_{aid}"
        download_dir = DOWNLOAD_DIR / folder_name
        download_dir.mkdir(parents=True, exist_ok=True)
        
        # 下載圖片
        downloaded = 0
        for i, img in enumerate(images, 1):
            src = img.get('src', '')
            if not src:
                continue
            
            filename = src.split('/')[-1]
            filepath = download_dir / filename
            
            result = subprocess.run(
                ['curl', '-s', '-o', str(filepath), '-A', 'Mozilla/5.0', src],
                capture_output=True,
                timeout=60
            )
            
            if result.returncode == 0 and filepath.exists() and filepath.stat().st_size > 0:
                downloaded += 1
        
        # 記錄
        mark_downloaded(aid, clean_title, downloaded, folder_name)
        log(f"✅ 下載完成：{clean_title} (aid={aid}, {downloaded}張)")
        
        return True
        
    except Exception as e:
        log(f"❌ 下載失敗：{e}")
        return False

def scan_latest_pages(max_pages=3):
    """掃描最新上傳頁面"""
    log(f"🔍 開始掃描最新上傳 (共{max_pages}頁)...")
    
    new_found = 0
    
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
                            full_url = WNACG_BASE + href
                            log(f"🆕 發現新本子：aid={aid}")
                            if download_album(full_url):
                                new_found += 1
                        else:
                            # 已下載，跳過
                            pass
            
        except Exception as e:
            log(f"❌ 掃描頁面 {page} 失敗：{e}")
    
    return new_found

def load_config():
    """加載配置"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 默認配置
        config = {
            "scan_pages": 3,
            "auto_download": True,
            "notify": True
        }
        save_config(config)
        return config

def save_config(config):
    """保存配置"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def show_stats():
    """顯示統計"""
    results = get_downloaded_list()
    total = len(results)
    total_images = sum(r[3] for r in results)
    
    print("\n" + "=" * 50)
    print("📊 下載統計")
    print("=" * 50)
    print(f"總共：{total} 個本子")
    print(f"總圖片：{total_images} 張")
    print(f"下載目錄：{DOWNLOAD_DIR}")
    print("=" * 50)
    
    if results:
        print("\n最近下載：")
        for i, (aid, title, time, count) in enumerate(results[:10], 1):
            print(f"  {i}. {title} ({count}張)")

def main():
    """主函數"""
    log("=" * 50)
    log("🚀 WNACG 自動化收集器啟動")
    log("=" * 50)
    
    # 加載配置
    config = load_config()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "scan":
            # 掃描模式
            pages = int(sys.argv[2]) if len(sys.argv) > 2 else config.get("scan_pages", 3)
            new_found = scan_latest_pages(pages)
            log(f"\n✅ 掃描完成，發現 {new_found} 個新本子")
            
        elif command == "stats":
            # 統計模式
            show_stats()
            
        elif command == "list":
            # 列出已下載
            results = get_downloaded_list()
            print(f"\n已下載 {len(results)} 個本子：")
            for aid, title, time, count in results:
                print(f"  [{aid}] {title} ({count}張)")
            
        elif command == "clear":
            # 清空資料庫（慎用）
            if len(sys.argv) > 2 and sys.argv[2] == "--yes":
                conn = init_db()
                c = conn.cursor()
                c.execute("DELETE FROM downloaded")
                conn.commit()
                conn.close()
                log("✅ 資料庫已清空")
            else:
                print("⚠️  確定要清空資料庫嗎？加上 --yes 確認")
        
        else:
            print("用法：python auto_collector.py [scan|stats|list|clear]")
    else:
        # 默認：掃描 + 下載
        pages = config.get("scan_pages", 3)
        new_found = scan_latest_pages(pages)
        log(f"\n✅ 收集完成，新增 {new_found} 個本子")
        show_stats()

if __name__ == "__main__":
    main()
