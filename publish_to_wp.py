import os
import re
import sys
import requests
import yaml
from urllib.parse import urljoin, unquote
from slugify import slugify
import markdown
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup

# === 配置區 ===
WP_URL = "https://yourdomain.com/" # 填寫您的 WordPress 網址，例如 https://example.com/
WP_USER = "your_username"          # 填寫您的 WordPress 使用者名稱
WP_APP_PASSWORD = "your_application_password" # 填寫在 WordPress 後台產生的「應用程式密碼」
API_ENDPOINT = urljoin(WP_URL, "wp-json/wp/v2/")

# --- 環境偵測邏輯 (保持與下載腳本一致) ---
POTENTIAL_PATHS = [
    r"C:\Your\Path\To\Obsidian\Vault",
    r"D:\Your\Path\To\Obsidian\Vault"
]

CURRENT_ENV = "Unknown"
for path in POTENTIAL_PATHS:
    if os.path.exists(path):
        CURRENT_ENV = path
        break

class WordPressClient:
    def __init__(self, user, password, api_url):
        self.user = user
        self.password = password
        self.api_url = api_url
        self.auth = (user, password)

    def upload_media(self, file_path):
        if not os.path.exists(file_path): return None, None
        file_name = os.path.basename(file_path)
        mime_type = "image/png" if file_name.lower().endswith(".png") else "image/jpeg"
        headers = {"Content-Disposition": f"attachment; filename={file_name}", "Content-Type": mime_type}
        with open(file_path, "rb") as file:
            data = file.read()
        response = requests.post(self.api_url + "media", headers=headers, data=data, auth=self.auth)
        if response.status_code == 201:
            res = response.json()
            return res['id'], res['source_url']
        return None, None

    def get_or_create_term(self, taxonomy, name):
        params = {"search": name}
        response = requests.get(self.api_url + taxonomy, params=params, auth=self.auth)
        if response.status_code == 200:
            results = response.json()
            for item in results:
                if item["name"] == name:
                    return item["id"]

        data = {"name": name, "slug": slugify(name)}
        response = requests.post(self.api_url + taxonomy, json=data, auth=self.auth)
        if response.status_code == 201:
            return response.json()["id"]
        return None

    def update_post(self, post_id, title, content, slug, featured_image_id=None, seo_desc="", categories=None, tags=None, status="publish"):
        data = {
            "title": title,
            "content": content,
            "status": status,
            "slug": slug,
            "meta": {"_seopress_titles_desc": seo_desc}
        }
        if featured_image_id:
            data["featured_media"] = featured_image_id
        if categories:
            data["categories"] = categories
        if tags:
            data["tags"] = tags

        response = requests.post(f"{self.api_url}posts/{post_id}", json=data, auth=self.auth)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[Error] 更新失敗！代碼: {response.status_code}")
            print(f"錯誤訊息: {response.text}")
            return None
            
    def create_post(self, title, content, slug, featured_image_id=None, seo_desc="", categories=None, tags=None, status="draft"):
        data = {
            "title": title,
            "content": content,
            "status": status,
            "slug": slug,
            "meta": {"_seopress_titles_desc": seo_desc}
        }
        if featured_image_id:
            data["featured_media"] = featured_image_id
        if categories:
            data["categories"] = categories
        if tags:
            data["tags"] = tags

        response = requests.post(self.api_url + "posts", json=data, auth=self.auth)
        return response.json() if response.status_code == 201 else None

def translate_to_slug(text):
    try:
        translated = GoogleTranslator(source='zh-TW', target='en').translate(text)
        return slugify(translated)
    except:
        return slugify(text)

def parse_yaml_front_matter(md_text):
    if md_text.startswith('---'):
        parts = md_text.split('---', 2)
        if len(parts) >= 3:
            yaml_block = parts[1]
            content = parts[2].lstrip()
            data = yaml.safe_load(yaml_block) or {}
            return data, content
    return {}, md_text

def convert_to_gutenberg(html_text):
    # 此處保留您原本的 convert_to_gutenberg 邏輯，不作變動
    clean_html = html_text.replace('\n', '')
    soup = BeautifulSoup(clean_html, 'html.parser')
    output = []
    def is_video_url(url):
        return any(domain in url for domain in ["youtube.com", "youtu.be", "vimeo.com", ".mp4", ".webm", ".ogg"])
    for element in soup.contents:
        if isinstance(element, str):
            text = element.strip()
            if text: output.append(f'<!-- wp:paragraph -->\n<p>{text}</p>\n<!-- /wp:paragraph -->')
            continue
        tag = element.name
        inner = element.decode_contents()
        if tag == 'p':
            img = element.find('img')
            if img: output.append(f'<!-- wp:image {{"sizeSlug":"full"}} -->\n<figure class="wp-block-image size-full">{str(img)}</figure>\n<!-- /wp:image -->')
            else: output.append(f'<!-- wp:paragraph -->\n<p>{inner}</p>\n<!-- /wp:paragraph -->')
        elif tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(tag[1]); output.append(f'<!-- wp:heading {{"level":{level}}} -->\n<{tag} class="wp-block-heading">{inner}</{tag}>\n<!-- /wp:heading -->')
        elif tag in ['ul', 'ol']:
            ordered = "true" if tag == 'ol' else "false"; output.append(f'<!-- wp:list {{"ordered":{ordered}}} -->\n<{tag} class="wp-block-list">{inner}</{tag}>\n<!-- /wp:list -->')
        elif tag == 'blockquote':
            output.append(f'<!-- wp:quote -->\n<blockquote class="wp-block-quote">{inner}</blockquote>\n<!-- /wp:quote -->')
        elif tag == 'table':
            output.append(f'<!-- wp:table -->\n<figure class="wp-block-table"><table>{inner}</table></figure>\n<!-- /wp:table -->')
        elif tag == 'pre':
            code = element.find('code'); code_text = code.get_text() if code else element.get_text()
            output.append(f'<!-- wp:code -->\n<pre class="wp-block-code"><code>{code_text}</code></pre>\n<!-- /wp:code -->')
        elif tag == 'iframe':
            src = element.get('src', '')
            if is_video_url(src): output.append(f'<!-- wp:embed {{"url":"{src}"}} -->\n<figure class="wp-block-embed"><div class="wp-block-embed__wrapper">\n{src}\n</div></figure>\n<!-- /wp:embed -->')
            else: output.append(f'<!-- wp:html -->\n{str(element)}\n<!-- /wp:html -->')
        elif tag == 'video':
            src = element.get('src', ''); output.append(f'<!-- wp:video -->\n<figure class="wp-block-video"><video src="{src}" controls></video></figure>\n<!-- /wp:video -->')
        elif tag == 'a':
            href = element.get('href', '')
            if is_video_url(href): output.append(f'<!-- wp:embed {{"url":"{href}"}} -->\n<figure class="wp-block-embed"><div class="wp-block-embed__wrapper">\n{href}\n</div></figure>\n<!-- /wp:embed -->')
            else: output.append(f'<!-- wp:paragraph -->\n<p>{str(element)}</p>\n<!-- /wp:paragraph -->')
        else:
            output.append(f'<!-- wp:html -->\n{str(element)}\n<!-- /wp:html -->')
    return "\n\n".join(output)

def process_markdown(file_path, client):
    # 打印當前環境
    print(f"[Info] 當前工作環境: {CURRENT_ENV}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    front_matter, md_body = parse_yaml_front_matter(raw_content)
    wp_id = front_matter.get("wp_id") 
    
    md_dir = os.path.dirname(os.path.abspath(file_path))
    filename_base = os.path.splitext(os.path.basename(file_path))[0]
    seo_desc = front_matter.get("description") or re.sub(r'[#*`\[\]!]', '', md_body)[:150].strip()

    first_image_id = None

    def replace_image(match):
        nonlocal first_image_id
        if match.group(2):
            rel_path = unquote(match.group(2))
            alt = match.group(1)
        else:
            inner = match.group(3)
            rel_path, alt = inner.split('|', 1) if '|' in inner else (inner, "")
            rel_path = unquote(rel_path)

        if wp_id or rel_path.startswith("http"):
            return match.group(0)

        full_path = os.path.join(md_dir, rel_path)
        if os.path.exists(full_path):
            img_id, url = client.upload_media(full_path)
            if img_id:
                if first_image_id is None: first_image_id = img_id
                return f"![{alt}]({url})"
        return match.group(0)

    processed_md = re.sub(r'!\[(.*?)\]\((.*?)\)|!\[\[(.*?)\]\]', replace_image, md_body)
    html_raw = markdown.markdown(processed_md, extensions=['fenced_code', 'tables'])
    gutenberg_content = convert_to_gutenberg(html_raw)

    title = front_matter.get("title", filename_base)
    slug = front_matter.get("slug") or translate_to_slug(title)

    def get_ids(field, taxonomy):
        names = front_matter.get(field, [])
        if isinstance(names, str): names = [names]
        ids = []
        for name in names:
            tid = client.get_or_create_term(taxonomy, name)
            if tid: ids.append(tid)
        return ids

    category_ids = get_ids("categories", "categories")
    tag_ids = get_ids("tags", "tags")

    if wp_id:
        print(f"[Action] Detecting wp_id: {wp_id}. Updating existing post...")
        result = client.update_post(
            post_id=wp_id,
            title=title,
            content=gutenberg_content,
            slug=slug,
            featured_image_id=first_image_id,
            seo_desc=seo_desc,
            categories=category_ids,
            tags=tag_ids,
            status=front_matter.get("status", "publish")
        )
    else:
        print("[Action] No wp_id found. Creating new post...")
        result = client.create_post(
            title=title,
            content=gutenberg_content,
            slug=slug,
            featured_image_id=first_image_id,
            seo_desc=seo_desc,
            categories=category_ids,
            tags=tag_ids,
            status=front_matter.get("status", "draft")
        )

    if result:
        action = "updated" if wp_id else "published"
        # [Note] 關鍵修改：從回傳的結果中抓取 ID
        final_id = result.get('id')
        print(f"[Success] Success: this file has been {action}! (Post ID: {final_id})")

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    client = WordPressClient(WP_USER, WP_APP_PASSWORD, API_ENDPOINT)
    process_markdown(sys.argv[1], client)
