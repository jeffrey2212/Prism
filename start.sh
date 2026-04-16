#!/bin/bash
# WNACG Gallery 啟動腳本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🖼️  WNACG Gallery"
echo "=================="
echo ""
echo "📂 掃描目錄：~/Downloads/wnacg/"
echo "🌐 訪問地址："
echo "   本地：http://localhost:5000"
echo "   Tailscale: http://<your-tailscale-ip>:5000"
echo ""
echo "按 Ctrl+C 停止服務"
echo ""

# 檢查目錄是否存在
if [ ! -d "$HOME/Downloads/wnacg" ]; then
    echo "⚠️  警告：~/Downloads/wnacg/ 目錄不存在"
    echo "   請先下載一些圖片"
    echo ""
fi

# 啟動服務
python3 app.py
