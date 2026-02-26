import requests
import os
import sys
from markdownify import markdownify as md

# --- 設定區 ---
WP_URL = "https://yourdomain.com" # 填寫您的 WordPress 網址，例如 https://example.com/
WP_USER = "your_username"         # 填寫您的 WordPress 使用者名稱
WP_APP_PASSWORD = "your_application_password" # 填寫在 WordPress 後台產生的「應用程式密碼」
POST_COUNT = 1

# --- 自動路徑偵測邏輯 ---
POTENTIAL_PATHS = [
    r"C:\Your\Path\To\Obsidian\Vault\OldPosts",
    r"D:\Your\Path\To\Obsidian\Vault\OldPosts"
]

SAVE_PATH = None
for path in POTENTIAL_PATHS:
    # 檢查該路徑的父目錄 (Valut-Wordpress) 是否存在，代表該硬碟/空間已掛載
    parent_dir = os.path.dirname(path)
    if os.path.exists(parent_dir):
        SAVE_PATH = path
        break

# 如果都找不到，則預設在程式碼所在目錄建立 OldPosts 資料夾
if not SAVE_PATH:
    SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "OldPosts")

# 確保存檔資料夾存在
if not os.path.exists(SAVE_PATH):
    os.makedirs(SAVE_PATH)

print(f"[Info] 當前存檔路徑設定為: {SAVE_PATH}")

def fetch_and_save(post):
    """處理單一文章的轉換與儲存"""
    wp_id = post['id']
    title = post['title']['rendered']
    content_html = post['content']['rendered']
    date = post['date']
    slug = post['slug']

    # 轉換 HTML 為 Markdown
    content_md = md(content_html, heading_style="ATX")

    # 準備 YAML 內容
    yaml_header = f"""---
wp_id: {wp_id}
title: "{title}"
date: {date}
slug: {slug}
status: publish
---

"""
    filename = f"{slug}.md"
    full_path = os.path.join(SAVE_PATH, filename)
    
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(yaml_header + content_md)
    
    print(f"[Success] 已成功下載/更新: {title} (ID: {wp_id})")

def start_download(post_id=None):
    """
    post_id: 如果有提供，則下載單篇；否則下載最新列表。
    """
    if post_id:
        # 狙擊模式：下載單一文章
        endpoint = f"{WP_URL}/wp-json/wp/v2/posts/{post_id}"
        print(f"[Action] 正在精準抓取文章 ID: {post_id}...")
        response = requests.get(endpoint)
        if response.status_code == 200:
            fetch_and_save(response.json())
        else:
            print(f"[Error] 找不到文章 ID: {post_id} (代碼: {response.status_code})")
    else:
        # 大網模式：批量下載最近文章
        endpoint = f"{WP_URL}/wp-json/wp/v2/posts"
        params = {'per_page': POST_COUNT, 'status': 'publish'}
        print(f"[Action] 正在批量抓取最近的 {POST_COUNT} 篇文章...")
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            posts = response.json()
            for post in posts:
                fetch_and_save(post)
        else:
            print(f"[Error] 批量抓取失敗 (代碼: {response.status_code})")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_id = sys.argv[1]
        start_download(target_id)
    else:
        start_download()
