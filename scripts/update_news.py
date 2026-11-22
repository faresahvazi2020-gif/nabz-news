
import json
import re
import urllib.request
import xml.etree.ElementTree as ET

from pathlib import Path
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

NEWS_FILE = DATA_DIR / "news.json"
DIGEST_FILE = DATA_DIR / "daily_digest.json"

CATEGORIES = {
    "ai": "هوش مصنوعی فناوری",
    "security": "امنیتی نظامی",
    "politics": "سیاست",
    "football": "فوتبال",
    "markets": "اقتصاد بازارهای مالی طلا نفت",
    "crypto": "ارز دیجیتال بیت کوین"
}

def clean_html(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", unescape(value)).strip()

def fetch_feed(category, query):
    url = (
        "https://news.google.com/rss/search?q="
        + quote(query)
        + "&hl=fa&gl=IR&ceid=IR:fa"
    )

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=25) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    results = []

    for item in root.findall(".//item"):
        title = clean_html(item.findtext("title"))
        link = item.findtext("link", "").strip()
        description = clean_html(item.findtext("description"))
        pub_date = item.findtext("pubDate", "")
        
        if not title or not link:
            continue

        source = item.find("source")
        source_name = clean_html(source.text) if source is not None else "Google News"

        try:
            published = parsedate_to_datetime(pub_date).astimezone(
                timezone.utc
            ).isoformat()
        except Exception:
            published = None

        results.append({
            "title": title,
            "summary": description[:500],
            "category": category,
            "source": source_name,
            "url": link,
            "published": published
        })

    return results

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_items = []
    errors = []

    for category, query in CATEGORIES.items():
        try:
            items = fetch_feed(category, query)
            all_items.extend(items)
            print(category, len(items), "news")
        except Exception as error:
            errors.append(category)
            print("Feed error:", category, error)

    unique = {}
    for item in all_items:
        unique[item["url"]] = item

    items = list(unique.values())

    items.sort(
        key=lambda x: x["published"] or "",
        reverse=True
    )

    updated = datetime.now(timezone.utc).isoformat()

    if items:
        news_data = {
            "updated_at": updated,
            "items": items[:100]
        }

        NEWS_FILE.write_text(
            json.dumps(news_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        highlights = [
            {
                "text": item["title"],
                "url": item["url"]
            }
            for item in items[:10]
        ]

        digest = {
            "date_label": datetime.now().strftime("%Y-%m-%d"),
            "summary": (
                "گزارش روزانه نبض بر اساس تیترهای منتشرشده "
                "در منابع خبری گردآوری شده است."
            ),
            "highlights": highlights
        }

        DIGEST_FILE.write_text(
            json.dumps(digest, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        print("News updated:", len(items))

    elif not NEWS_FILE.exists():
        NEWS_FILE.write_text(
            json.dumps(
                {"updated_at": updated, "items": []},
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

    if errors:
        print("Some feeds could not be reached:", errors)

if __name__ == "__main__":
    main()
  
