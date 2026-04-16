#!/usr/bin/env python3
"""WNACG Gallery Web App - Flask Backend"""

import os
import argparse
import re
from flask import Flask, jsonify, send_from_directory, render_template, request

app = Flask(__name__)

# 圖片目錄配置
IMAGE_DIR = os.path.expanduser("~/Downloads/wnacg")
IMAGE_DIR = os.path.abspath(IMAGE_DIR)

# 支持的圖片擴展名
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}


def get_aid_from_name(album_name):
    """從 album 名稱提取 AID"""
    # 嘗試從名稱末尾提取 _數字 格式
    match = re.search(r'_(\d+)$', album_name)
    if match:
        return int(match.group(1))
    return 0


def get_albums():
    """掃描並返回所有 album 列表"""
    albums = []
    if not os.path.exists(IMAGE_DIR):
        return albums
    
    for name in sorted(os.listdir(IMAGE_DIR)):
        album_path = os.path.join(IMAGE_DIR, name)
        if os.path.isdir(album_path):
            images = get_album_images(name)
            if images:
                cover = f"/images/{name}/{images[0]}" if images else None
                albums.append({
                    "name": name,
                    "cover": cover,
                    "count": len(images)
                })
    return albums


def get_album_images(album_name):
    """獲取指定 album 的所有圖片"""
    album_path = os.path.join(IMAGE_DIR, album_name)
    if not os.path.exists(album_path):
        return []
    
    images = []
    for filename in sorted(os.listdir(album_path)):
        ext = os.path.splitext(filename)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            images.append(filename)
    return images


@app.route("/")
def index():
    """首頁"""
    return render_template("index.html")


@app.route("/album/<album_name>")
def album(album_name):
    """Album 詳情頁"""
    return render_template("album.html", album_name=album_name)


@app.route("/api/albums")
def api_albums():
    """API: 獲取所有 album 列表（支持排序）"""
    # 獲取排序參數
    sort_by = request.args.get('sort', 'aid_desc')  # 預設：最新上傳
    
    albums = get_albums()
    
    # 排序邏輯
    if sort_by == 'aid_desc':
        # 最新上傳（AID 降序）
        albums.sort(key=lambda x: get_aid_from_name(x['name']), reverse=True)
    elif sort_by == 'aid_asc':
        # 最早上傳（AID 升序）
        albums.sort(key=lambda x: get_aid_from_name(x['name']))
    elif sort_by == 'count_desc':
        # 圖片最多
        albums.sort(key=lambda x: x['count'], reverse=True)
    elif sort_by == 'count_asc':
        # 圖片最少
        albums.sort(key=lambda x: x['count'])
    elif sort_by == 'name_asc':
        # 名稱 A-Z
        albums.sort(key=lambda x: x['name'])
    elif sort_by == 'name_desc':
        # 名稱 Z-A
        albums.sort(key=lambda x: x['name'], reverse=True)
    
    return jsonify(albums)


@app.route("/api/albums/<album_name>/images")
def api_album_images(album_name):
    """API: 獲取指定 album 的圖片列表"""
    images = get_album_images(album_name)
    if not images:
        return jsonify({"error": "Album not found"}), 404
    return jsonify({
        "album": album_name,
        "images": images
    })


@app.route("/images/<album>/<filename>")
def serve_image(album, filename):
    """提供圖片訪問"""
    return send_from_directory(os.path.join(IMAGE_DIR, album), filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WNACG Gallery Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind (default: 8080)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    
    print(f"WNACG Gallery Server")
    print(f"Image directory: {IMAGE_DIR}")
    print(f"Starting server on http://{args.host}:{args.port}")
    
    app.run(host=args.host, port=args.port, debug=args.debug)
