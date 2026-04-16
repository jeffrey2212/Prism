# WNACG Cosplay 自動化收集系統

自動掃描、下載、去重 WNACG 寫真&Cosplay 分類的圖片集。

---

## 🎯 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│                    Cron Job (每 6 小時)                        │
│                 wnacg-cosplay-collector                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              cosplay_collector.py                            │
│  1. 掃描 cate-3（寫真&Cosplay）最新 3 頁                         │
│  2. 使用 browser 工具提取 aid                                 │
│  3. 檢查 SQLite 資料庫去重                                     │
│  4. 下載新本子                                                │
│  5. 更新資料庫                                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   SQLite Database                            │
│            ~/Downloads/wnacg/.downloaded.db                  │
│         (記錄已下載的 aid，避免重複下載)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                Download Directory                            │
│            ~/Downloads/wnacg/                                │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│   │ Album 1     │  │ Album 2     │  │ Album N     │        │
│   │ (101 張)     │  │ (8 張)       │  │ (82 張)       │        │
│   └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Gallery Web App (PM2, Port 8081)                │
│         http://localhost:8081                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 當前狀態

| 項目 | 數值 |
|------|------|
| 已下載本子 | 8 個 |
| 總圖片數 | 414 張 |
| 掃描頻率 | 每 6 小時 |
| 掃描分類 | cate-3（寫真&Cosplay） |
| 掃描頁數 | 3 頁 |

---

## 📁 目錄結構

```
~/Downloads/wnacg/
├── .downloaded.db      # SQLite 資料庫
├── .config.json        # 配置文件
├── .log.txt            # 下載日誌
├── Bomi - Officer 2B_354364/           (101 張)
├── Puutin-2B Witch_355536/             (8 張)
├── Yurihime - Elegg_355537/            (62 張)
├── 屿鱼 - 天雨亚子同人护士_355446/       (31 張)
├── Qiandai - Bunny 2B_355445/          (29 張)
├── Natsuko 夏夏子 - NIKKE 布兰儿_355444/  (81 張)
├── yuuhui - Jade Collection Twin Black_354370/ (20 張)
└── Natsuko 夏夏子 - GRIDMAN 新条茜_355780/   (82 張) ← 新增！

/home/jeff/papertowne/Manager/workspace/wnacg-gallery/
├── app.py              # Gallery Web App
├── cosplay_collector.py # Cosplay 自動化收集器
├── README.md           # 本文件
└── ...
```

---

## 🚀 使用方式

### 手動掃描
```bash
python3 /home/jeff/papertowne/Manager/workspace/wnacg-gallery/wnacg_scanner.py 3
```

### 查看統計
```bash
python3 /home/jeff/papertowne/Manager/workspace/wnacg-gallery/auto_collector.py stats
```

### 列出已下載
```bash
python3 /home/jeff/papertowne/Manager/workspace/wnacg-gallery/auto_collector.py list
```

### 手動觸發收集（測試用）
```bash
# 直接在 Hermes 中運行 cron job
hermes -c "cronjob run 71a6c5983d56"
```

---

## 📋 配置文件 (~/.Downloads/wnacg/.config.json)

```json
{
  "scan_pages": 3,           // 每次掃描多少頁
  "auto_download": true,     // 是否自動下載
  "notify": true,            // 是否通知
  "track_artists": [],       // 追蹤的畫師（未來功能）
  "track_series": [],        // 追蹤的系列（未來功能）
  "exclude_keywords": []     // 排除關鍵字（未來功能）
}
```

---

## 🎯 去重機制

系統使用 **aid** (Album ID) 作為唯一標識：

1. 掃描時提取每個本子的 aid
2. 檢查 SQLite 資料庫是否已存在
3. 已存在 → 跳過
4. 不存在 → 下載並記錄

**即使刪除文件夾，資料庫仍會記錄**，避免重複下載。

---

## 📊 統計命令

```bash
# 查看已下載總數
python3 auto_collector.py stats

# 列出所有已下載（按 aid 排序）
python3 auto_collector.py list

# 查看下載日誌
tail -f ~/Downloads/wnacg/.log.txt
```

---

## 🔧 故障排除

### 問題：腳本無法運行
```bash
# 安裝依賴
pip install requests beautifulsoup4
```

### 問題：資料庫損壞
```bash
# 刪除並重建
rm ~/Downloads/wnacg/.downloaded.db
python3 auto_collector.py stats  # 會自動重建
```

### 問題：想重新下載某個本子
```bash
# 從資料庫移除特定 aid
sqlite3 ~/Downloads/wnacg/.downloaded.db "DELETE FROM downloaded WHERE aid=354364"
```

---

## 📝 日誌位置

- **下載日誌：** `~/Downloads/wnacg/.log.txt`
- **Cron 日誌：** `pm2 logs wnacg-auto-collector`

---

## 🎉 當前狀態

| 項目 | 數值 |
|------|------|
| 已下載本子 | 7 個 |
| 總圖片數 | 332 張 |
| 掃描頻率 | 每 6 小時 |
| 掃描頁數 | 3 頁 |

---

**最後更新：** 2026-04-16
