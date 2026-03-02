# WordPress Markdown Tools

這是一個用於在 WordPress 和 Markdown 檔案之間雙向傳輸和轉換的自動化工具組。

## 包含腳本與主要功能

### 1. `publish_to_wp.py`
將本地的 Markdown 檔案發佈或更新到 WordPress 網站上，並且將內容轉換為原生 Gutenberg 區塊格式。
- **YAML Front Matter 支援**: 在 Markdown 開頭使用 YAML 自訂文章資訊 (例如 `wp_id`, `title`, `slug`, `categories`, `tags`, `status`, `featured_media`, `description`)。
- **自動化處理**:
  - 如果未提供 `slug`，會自動將中文標題翻譯成英文產生 slug。
  - 會自動抓出首段文字或指定 `description` 寫入 SEOPress meta description。
  - 自動偵測 Markdown 內的本地圖片，上傳至 WordPress 媒體庫，並轉換為圖文區塊，預設抓取第一張上傳的圖片作為**特色圖片**(Featured Image)。
  - 自動判斷連結如果是 YouTube / Vimeo 影片，會轉換成 Embed 區塊。
- **更新機制**: 如果 YAML 中含有 `wp_id` (或發佈後程式自動印出 ID)，往後執行皆會對該現有文章進行「更新」，否則為「發佈新文章」。
- **自動路徑偵測**: 支援跨裝置環境的路徑偵測邏輯，確保能順利讀取工作區檔案。

### 2. `wp_downloader.py`
將 WordPress 上已經發佈的文章下載為帶有 YAML 標頭的 Markdown 檔案，方便您在本地端保存或透過 Obsidian 等工具繼續編輯修改。
- **批次模式**: 批次下載最近發布的 N 篇文章（預設為 10 篇，可在程式內設定）。
- **狙擊模式**: 只要提供文章 ID，就可以針對單一文章進行下載。
- **Metadata 匯出**: 會建立標準的 YAML Front Matter，自動帶入 `wp_id`, `title`, `date`, `slug`, `status`, `featured_media`, 且支援擷取 SEOPress 的 meta description。
- **存檔路徑偵測**: 自動建立存放文章的 `OldPosts` 資料夾，並依照不同裝置優先順序進行存檔。圖片部分則會保留遠端網址。

---

## 使用說明

### 系統需求與安裝

請先確保安裝環境所需的 Python 套件：
```bash
pip install -r requirements.txt
```

### 相關配置

每個 python 腳本開頭皆有「設定區」(或「配置區」)，請記得根據您的網站資訊修改其中對應的參數：
- `WP_URL`: WordPress 網站網址 (例如: `https://your-wordpress-site.com/`)
- `WP_USER`: WordPress 登入帳號 (使用者名稱)
- `WP_APP_PASSWORD`: WordPress 產生的「應用程式密碼」

> **資安提醒：**
> 請勿在腳本中使用您的真實登入密碼。前往 WordPress 後台的「使用者 > 個人資料」頁面最下方，新增一組「應用程式密碼」(Application Passwords) 並將其貼入腳本中以策安全。

### 執行: 發佈文章 (Markdown to WordPress)

在您要上傳的 md 檔開頭加上 YAML 格式的 Front matter：
```yaml
---
title: "AI 自動化心得：從輸入到輸出的無縫接軌"
slug: ai-automation-workflow
categories: [AI學習]
tags: [Obsidian, Python, WordPress]
status: draft
---
```

**指令：**
```bash
python publish_to_wp.py "您要發佈的檔案路徑.md"
```
（成功上傳後，終端機會顯示建立的文章 ID。）

### 執行: 下載文章 (WordPress to Markdown)

直接執行腳本會自動建立 `OldPosts` 並開始批次下載。

**指令：**
```bash
# 下載最新預設數量的所有文章 (批次模式)
python wp_downloader.py

# 針對單一文章 ID 進行下載 (狙擊模式)
python wp_downloader.py 1234
```
（下載後的文章會加上前綴 YAML，方便日後若有修改，可再搭配 `publish_to_wp.py` 將更新打回網站！）
