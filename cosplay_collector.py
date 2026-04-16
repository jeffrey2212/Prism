#!/usr/bin/env python3
"""
WNACG Cosplay 自動化收集器 - 溫和版
專門掃描 cate-3（寫真&Cosplay）分類，自動下載新本子

策略：
- 每次只下載 1-2 個新本子
- 添加延遲，避免給服務器造成負擔
- 從最新往回掃描
- 記錄當前掃描頁面，下次繼續
"""

import json
import sqlite3
import subprocess
import re
import sys
import time
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
STATE_PATH = DOWNLOAD_DIR / ".collector_state.json"
CATE_ID = 3  # 寫真&Cosplay

# 新本收集配置
NEW_ALBUMS_PAGE = 1      # 新本掃描頁（第 1 頁）
NEW_MAX_DOWNLOAD = 2     # 新本每次最多下載幾個

# 舊本收集配置
OLD_ALBUMS_START_PAGE = 2    # 舊本起始頁（第 2 頁開始）
OLD_ALBUMS_RANGE = 5         # 每次掃描幾頁
OLD_MAX_DOWNLOAD = 2         # 舊本每次最多下載幾個
MAX_PAGES = 863              # WNACG cate-3 總頁數

# 通用配置
DELAY_BETWEEN_DOWNLOADS = 5  # 下載間隔秒數

def load_state():
    """加載掃描狀態"""
    if STATE_PATH.exists():
        with open(STATE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {
            'new_page': 1,              # 新本掃描頁（固定第 1 頁）
            'old_page_start': 2,        # 舊本起始頁
            'old_page_current': 2,      # 舊本當前掃描頁
            'last_scan_time': None,
            'total_scanned': 0,
            'new_count': 0,             # 新本下載計數
            'old_count': 0              # 舊本下載計數
        }

def save_state(state):
    """保存掃描狀態"""
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

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

def log(message):
    """寫入日誌"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}\n"
    print(log_msg, end='')
    log_file = DOWNLOAD_DIR / ".log.txt"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_msg)

def scan_page(page_num):
    """掃描單頁，使用 requests。返回 (新本子列表，是否遇到已下載的)"""
    url = f"https://wnacg.com/albums-index-page-{page_num}-cate-{CATE_ID}.html"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://wnacg.com/'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取所有 aid
        aids = []
        seen = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            match = re.search(r'/photos-index-aid-(\d+)\.html', href)
            if match:
                aid = int(match.group(1))
                if aid not in seen:
                    seen.add(aid)
                    aids.append(aid)
        
        items = []
        found_existing = False  # 是否遇到已下載的
        for aid in aids:
            # 檢查是否已下載
            if is_downloaded(aid):
                found_existing = True  # 遇到已下載的，標記
                continue  # 跳過已下載的
            
            # 提取標題
            title = f"Unknown_{aid}"
            for a in soup.find_all('a', href=True):
                if f'aid-{aid}' in a.get('href', ''):
                    title = a.get_text(strip=True)
                    break
            
            items.append({
                'aid': aid,
                'title': title,
                'url': f'https://wnacg.com/photos-slide-aid-{aid}.html'
            })
        
        # 如果遇到已下載的，表示這頁之後的都是舊的，可以停止
        return items, found_existing
        
    except Exception as e:
        log(f"❌ 掃描頁面 {page_num} 失敗：{e}")
        return [], True

def download_album(url):
    """下載單一本子，使用 browser 工具"""
    from hermes_tools import browser_navigate, browser_get_images
    
    try:
        # 訪問頁面
        nav_result = browser_navigate(url=url)
        if not nav_result.get('success'):
            log(f"❌ 無法訪問頁面：{url}")
            return None
        
        title = nav_result.get('title', 'unknown')
        clean_title = re.sub(r'\s*-\s*列表.*$', '', title)
        clean_title = re.sub(r'\s*-\s*紳士漫畫.*$', '', clean_title)
        
        # 清理文件名
        clean_title = re.sub(r'[<>:"/\\|？*]', '', clean_title)
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
        if len(clean_title) > 100:
            clean_title = clean_title[:100]
        
        # 提取 aid
        aid_match = re.search(r'aid-(\d+)', url)
        if not aid_match:
            return None
        aid = int(aid_match.group(1))
        
        # 獲取圖片 - 使用 browser 工具
        images_result = browser_get_images()
        if not images_result.get('success'):
            log(f"❌ 無法獲取圖片：aid={aid}")
            return None
        
        images = images_result.get('images', [])
        if not images:
            log(f"❌ 未找到圖片：aid={aid}")
            return None
        
        # 創建文件夾
        folder_name = f"{clean_title}_{aid}"
        download_dir = DOWNLOAD_DIR / folder_name
        download_dir.mkdir(parents=True, exist_ok=True)
        
        # 下載圖片
        downloaded = 0
        headers = ['-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', '-e', 'https://wnacg.com/', '-H', 'Referer: https://wnacg.com/']
        for i, img in enumerate(images, 1):
            src = img.get('src', '')
            if not src:
                continue
            
            filename = src.split('/')[-1]
            filepath = download_dir / filename
            
            try:
                cmd = ['curl', '-s', '-o', str(filepath)] + headers + [src]
                result = subprocess.run(cmd, capture_output=True, timeout=60)
                if result.returncode == 0 and filepath.exists() and filepath.stat().st_size > 0:
                    downloaded += 1
            except Exception as e:
                log(f"  圖片下載失敗：{filename} - {e}")
        
        return {'aid': aid, 'title': clean_title, 'count': downloaded, 'folder': folder_name}
        
    except Exception as e:
        log(f"❌ 下載失敗：{e}")
        return None

def main():
    """主函數 - 混合策略：新本 + 舊本同時收集"""
    log("=" * 60)
    log("🐌 WNACG Cosplay 收集器（混合策略）")
    log("=" * 60)
    
    # 加載狀態
    state = load_state()
    old_page_current = state.get('old_page_current', 2)
    
    total_downloaded = 0
    
    # ========== 第一部分：掃描第 1 頁（新本） ==========
    log("\n📌 【新本收集】掃描第 1 頁...")
    new_items, _ = scan_page(NEW_ALBUMS_PAGE)
    
    if new_items:
        log(f"  發現 {len(new_items)} 個新本子")
        to_download = new_items[:NEW_MAX_DOWNLOAD]
        log(f"  📥 準備下載 {len(to_download)} 個...")
        
        for item in to_download:
            log(f"\n  [{item['aid']}] {item['title']}... ")
            result = download_album(item['url'])
            if result:
                mark_downloaded(result['aid'], result['title'], result['count'], result['folder'])
                log(f"  ✅ {result['count']}張")
                total_downloaded += 1
                state['new_count'] = state.get('new_count', 0) + 1
                time.sleep(DELAY_BETWEEN_DOWNLOADS)
            else:
                log("  ❌ 失敗")
    else:
        log("  ✅ 第 1 頁沒有新本子")
    
    # ========== 第二部分：掃描舊本範圍 ==========
    log(f"\n📌 【舊本收集】掃描第 {old_page_current}-{min(old_page_current + OLD_ALBUMS_RANGE - 1, MAX_PAGES)} 頁...")
    
    old_items = []
    for page_offset in range(OLD_ALBUMS_RANGE):
        page_num = old_page_current + page_offset
        if page_num > MAX_PAGES:
            log(f"  📌 已達最後一頁（{MAX_PAGES}），重置為第 2 頁")
            old_page_current = 2
            break
        
        log(f"  掃描第 {page_num} 頁...")
        items, _ = scan_page(page_num)
        old_items.extend(items)
    
    if old_items:
        log(f"  發現 {len(old_items)} 個未下載的本子")
        to_download = old_items[:OLD_MAX_DOWNLOAD]
        log(f"  📥 準備下載 {len(to_download)} 個...")
        
        for item in to_download:
            log(f"\n  [{item['aid']}] {item['title']}... ")
            result = download_album(item['url'])
            if result:
                mark_downloaded(result['aid'], result['title'], result['count'], result['folder'])
                log(f"  ✅ {result['count']}張")
                total_downloaded += 1
                state['old_count'] = state.get('old_count', 0) + 1
                time.sleep(DELAY_BETWEEN_DOWNLOADS)
            else:
                log("  ❌ 失敗")
    else:
        log("  ✅ 這範圍沒有未下載的本子")
    
    # ========== 更新狀態 ==========
    # 舊本頁數遞增
    state['old_page_current'] = min(old_page_current + OLD_ALBUMS_RANGE, MAX_PAGES)
    if state['old_page_current'] >= MAX_PAGES:
        state['old_page_current'] = 2  # 循環重新開始
    
    state['last_scan_time'] = datetime.now().isoformat()
    state['total_scanned'] = state.get('total_scanned', 0) + len(new_items) + len(old_items)
    save_state(state)
    
    # ========== 統計 ==========
    conn = init_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*), SUM(image_count) FROM downloaded")
    total, total_images = c.fetchone()
    conn.close()
    
    log("\n" + "=" * 60)
    log(f"✅ 本次完成：下載 {total_downloaded} 個")
    log(f"   新本：{state.get('new_count', 0)} 個")
    log(f"   舊本：{state.get('old_count', 0)} 個")
    log(f"\n總共：{total} 個本子，{total_images or 0} 張圖片")
    log(f"\n下次舊本從第 {state['old_page_current']} 頁開始")
    log(f"目錄：{DOWNLOAD_DIR}")
    log("=" * 60)

if __name__ == "__main__":
    main()
