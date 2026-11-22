#!/usr/bin/env python3
'''Fetch public Google News RSS feeds and publish a compact news index.'''
import json, re, time, html
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
QUERIES = {
 "ai": ['("artificial intelligence" OR AI) technology', 'هوش مصنوعی فناوری'],
 "security": ['military security defense world', 'اخبار امنیتی نظامی جهان'],
 "politics": ['world politics geopolitics Middle East', 'اخبار سیاسی جهان خاورمیانه'],
 "football": ['football soccer latest news', 'اخبار فوتبال جهان'],
 "markets": ['gold oil dollar stock markets economy', 'قیمت طلا نفت دلار بورس اقتصاد'],
 "crypto": ['Bitcoin Ethereum cryptocurrency market', 'بیت کوین اتریوم ارز دیجیتال'],
}
def clean(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    return re.sub(r"\s+", " ", s).strip()
def fetch(query):
    url = "https://news.google.com/rss/search?q=" + quote(query) + "&hl=fa&gl=IR&ceid=IR:fa"
    req = Request(url, headers={"User-Agent":"Mozilla/5.0 NabzNewsBot/1.0"})
    with urlopen(req, timeout=25) as r:
        root = ET.fromstring(r.read())
    out=[]
    for item in root.findall(".//item"):
        title=clean(item.findtext("title"))
        link=(item.findtext("link") or "").strip()
        desc=clean(item.findtext("description"))
        source=clean(item.findtext("source")) or "Google News"
        pub=item.findtext("pubDate")
        try: published=parsedate_to_datetime(pub).astimezone(timezone.utc).isoformat()
        except Exception: published=datetime.now(timezone.utc).isoformat()
        if title and link: out.append({"title":title,"summary":desc[:360],"url":link,"source":source,"published":published})
    return out

now=datetime.now(timezone.utc)
items=[]
for category, queries in QUERIES.items():
    collected=[]
    for q in queries:
        try: collected.extend(fetch(q))
        except Exception as e: print("Feed failed",category,q,str(e))
    seen=set()
    for n in collected:
        key=re.sub(r"\W+","",n["title"].lower())
        if key in seen: continue
        seen.add(key); n["category"]=category
        items.append(n)
items.sort(key=lambda x:x["published"], reverse=True)
# Keep recent 72h; preserve a useful cap per category.
cutoff=now-timedelta(hours=72)
items=[n for n in items if datetime.fromisoformat(n["published"])>=cutoff]
counts={}
limited=[]
for n in items:
    c=n["category"]; counts[c]=counts.get(c,0)+1
    if counts[c]<=35: limited.append(n)
payload={"updated_at":now.isoformat(),"items":limited}
(DATA/"news.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")

# Daily extractive digest: latest items in the last 24 hours, ranked by source-independent recency.
recent=[n for n in limited if datetime.fromisoformat(n["published"])>=now-timedelta(hours=24)]
highlights=[]
for n in recent:
    if len(highlights)>=18: break
    highlights.append({"text":n["title"],"url":n["url"],"category":n["category"]})
labels={"ai":"هوش مصنوعی و فناوری","security":"امنیتی و نظامی","politics":"سیاسی","football":"فوتبال","markets":"بازارها و اقتصاد","crypto":"ارز دیجیتال"}
summary="در ۲۴ ساعت گذشته "+str(len(recent))+" خبر در دسته‌های مختلف گردآوری شد. موارد زیر بر اساس تازگی انتشار مرتب شده‌اند؛ برای جزئیات و زمینه، منبع اصلی هر خبر را باز کنید."
digest={"generated_at":now.isoformat(),"date_label":datetime.now(ZoneInfo("Asia/Tehran")).strftime("%Y-%m-%d")+" · خلاصه ۲۴ ساعت گذشته","summary":summary,"highlights":[{"text":"["+labels.get(x["category"],"خبر")+"] "+x["text"],"url":x["url"]} for x in highlights]}
(DATA/"daily_digest.json").write_text(json.dumps(digest,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"Published {len(limited)} news items and {len(highlights)} digest highlights.")
