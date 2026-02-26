# WordPress Markdown Tools

這是一個用於在 WordPress 和 Markdown 檔案之間雙向傳輸和轉換的工具組。

## 包含腳本

- `publish_to_wp.py`: 將 Markdown 檔案發佈/更新到 WordPress。
- `wp_downloader.py`: 將 WordPress 上已經發佈的文章下載為 Markdown 檔案。

## 使用說明

1. 請先確保安裝所需的套件：
   ```bash
   pip install -r requirements.txt
   ```

2. 每個 python 檔案中皆有「設定區」(或「配置區」)，請記得填入您專屬的參數：
   - `WP_URL`: WordPress 網站網址 (例如: `https://yourdomain.com/`)
   - `WP_USER`: WordPress 帳號 (使用者名稱)
   - `WP_APP_PASSWORD`: WordPress 產生的「應用程式密碼」

   **備註：**
   為確保系統安全，請勿直接輸入您的帳號密碼，請到 WordPress 後台的「使用者 > 個人資料」最下方，新增「應用程式密碼」(Application Passwords) 來取得 API 密碼。

3. **發佈文章**
   ```bash
   python publish_to_wp.py "您要發佈的檔案路徑.md"
   ```

4. **下載文章**
   ```bash
   python wp_downloader.py
   python wp_downloader.py <文章ID>  # 如果要下載單一文章
   ```
