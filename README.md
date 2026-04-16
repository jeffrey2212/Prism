# Prism Gallery

🌈 A modern, self-hosted image gallery with automatic collection and infinite scroll.

---

## ✨ Features

### Gallery Web App
- 🖼️ **Infinite Scroll** - Load images in batches for smooth browsing
- 🎨 **Dark Theme** - Easy on the eyes
- 🔍 **Smart Sorting** - Sort by date, image count, or name
- 📍 **Position Memory** - Remember where you left off
- 🔙 **Floating Navigation** - Quick back button
- 💡 **Lightbox** - Click zones for prev/next, click to close

### Auto Collector
- 🤖 **Automatic Scanning** - Periodically scan for new content
- 🔄 **Hybrid Strategy** - Collect new uploads + backfill old content
- 🗄️ **Deduplication** - SQLite database prevents duplicates
- 📊 **Progress Tracking** - Track collection progress
- ⏰ **Cron Scheduled** - Runs automatically every 6 hours

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Cron Job (every 6h)                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Collection Script                               │
│  1. Scan source pages                                        │
│  2. Extract album IDs                                        │
│  3. Check database for duplicates                            │
│  4. Download new albums                                      │
│  5. Update database                                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   SQLite Database                            │
│         (Tracks downloaded albums, prevents duplicates)      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                Gallery Web App                               │
│              Flask + Vanilla JS                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

```bash
pip install -r requirements.txt
```

### Start Gallery

```bash
python3 app.py --port 8080
```

Or with PM2:

```bash
pm2 start app.py --name prism-gallery -- --port 8080
```

### Run Collector

```bash
python3 cosplay_collector.py
```

### Setup Cron Job

```bash
# Edit crontab
crontab -e

# Add (runs every 6 hours)
0 */6 * * * cd /path/to/prism-gallery && python3 cosplay_collector.py
```

---

## 📁 Project Structure

```
prism-gallery/
├── app.py                      # Flask web server
├── cosplay_collector.py        # Auto collector script
├── requirements.txt            # Python dependencies
├── static/
│   ├── css/style.css          # Dark theme styles
│   └── js/main.js             # Frontend logic
├── templates/
│   ├── index.html             # Gallery home
│   └── album.html             # Album detail view
└── README.md
```

---

## ⚙️ Configuration

### Gallery Server

```bash
python3 app.py --host 0.0.0.0 --port 8080 --debug
```

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `0.0.0.0` | Server host |
| `--port` | `8080` | Server port |
| `--debug` | `false` | Enable debug mode |

### Collector

Edit `cosplay_collector.py` to configure:

```python
# New albums collection
NEW_ALBUMS_PAGE = 1          # Scan page 1 for new uploads
NEW_MAX_DOWNLOAD = 2         # Max 2 new albums per run

# Old albums backfill
OLD_ALBUMS_START_PAGE = 2    # Start from page 2
OLD_ALBUMS_RANGE = 5         # Scan 5 pages per run
OLD_MAX_DOWNLOAD = 2         # Max 2 old albums per run
MAX_PAGES = 863              # Total pages to scan
```

---

## 🎯 Key Features

### Infinite Scroll

- Loads images in batches (20 per batch)
- Smooth scrolling experience
- Loading indicator at bottom

### Lightbox Navigation

| Action | Result |
|--------|--------|
| Click left 30% | ← Previous image |
| Click right 30% | → Next image |
| Click image/background | Close lightbox |
| Press ← / → | Navigate images |
| Press Esc | Close lightbox |

### Smart Sorting

- 🕐 **Latest Upload** (default)
- 📅 **Earliest Upload**
- 🖼️ **Most Images**
- 📄 **Fewest Images**
- 🔤 **Name A-Z**
- 🔠 **Name Z-A**

### Position Memory

- Remembers scroll position
- Highlights last viewed album
- Persists across page navigation

---

## 📊 Database Schema

```sql
CREATE TABLE downloaded (
    aid INTEGER PRIMARY KEY,
    title TEXT,
    download_time TEXT,
    image_count INTEGER,
    folder_name TEXT
);
```

---

## 🔧 Troubleshooting

### Gallery won't start

```bash
# Check dependencies
pip install -r requirements.txt

# Check if port is in use
lsof -i :8080
```

### Collector not downloading

```bash
# Check logs
tail -f ~/Downloads/wnacg/.log.txt

# Test manually
python3 cosplay_collector.py
```

### Database issues

```bash
# View downloaded albums
sqlite3 ~/Downloads/wnacg/.downloaded.db "SELECT * FROM downloaded LIMIT 10"

# Remove specific album
sqlite3 ~/Downloads/wnacg/.downloaded.db "DELETE FROM downloaded WHERE aid=12345"
```

---

## 🛡️ .gitignore

The following are excluded from version control:

- Images and media files
- SQLite database
- Cache files (`__pycache__/`)
- Logs
- Configuration files with sensitive data

---

## 📝 License

MIT License - Feel free to use and modify.

---

**Built with:** Python • Flask • Vanilla JS • SQLite
