import os, json, re, time, html, hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import yaml
from bs4 import BeautifulSoup

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors.rpcerrorlist import FloodWaitError
from telethon.tl.types import Message

from config import (
    STATE_DIR,
    STATE_FILE,
    CHANNELS_FILE,
    KEYWORDS_FILE,
    FEED_FILE,
    SITE_TITLE,
    SITE_LINK,
    SITE_DESC,
    FEED_LIMIT,
    FEED_DAYS,
    api_id,
    api_hash,
    string_session,
)

def load_yaml(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def load_state() -> Dict[str, int]:
    if not os.path.exists(STATE_DIR):
        os.makedirs(STATE_DIR, exist_ok=True)
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state: Dict[str, int]) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def msg_link(channel_username: str, msg_id: int) -> str:
    # Works for public channels/supergroups
    uname = channel_username.lstrip("@")
    return f"https://t.me/{uname}/{msg_id}"

def clean_text(text: str) -> str:
    # Strip excessive whitespace; keep code blocks etc.
    text = text.strip()
    # Optional: collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text

def html_escape(s: str) -> str:
    return html.escape(s, quote=True)

def item_guid(link: str, fallback: str) -> str:
    # Stable GUID: use link when possible; otherwise hash fallback
    if link:
        return link
    h = hashlib.sha1(fallback.encode("utf-8")).hexdigest()
    return f"urn:sha1:{h}"

def extract_first_url(text: str) -> str:
    m = re.search(r"(https?://[^\s)]+)", text)
    return m.group(1) if m else ""

def message_to_item(ch_username: str, m: Message) -> Dict[str, Any]:
    content = m.message or ""
    content = clean_text(content)
    link = msg_link(ch_username, m.id)
    first_url = extract_first_url(content)
    title = (content.splitlines()[0][:120] if content else f"Post {m.id}").strip()
    # Prefer first URL as item link if present; else link to Telegram post
    item_link = first_url or link

    # Convert simple newlines to <br/>; escape HTML; keep URLs clickable
    # Minimal formatting to be RSS-safe
    desc_html = html_escape(content).replace("\n", "<br/>")

    # If there are media/captions without text, set a sensible title
    if not content:
        title = f"Post {m.id} on {ch_username}"

    pub_dt = m.date.replace(tzinfo=timezone.utc)
    pub_rfc2822 = pub_dt.strftime("%a, %d %b %Y %H:%M:%S +0000")

    return {
        "title": title,
        "link": item_link,
        "guid": item_guid(item_link, f"{ch_username}-{m.id}"),
        "pubDate": pub_rfc2822,
        "pub_datetime": pub_dt,  # Store datetime object for filtering
        "description": desc_html,
        "tg_link": link
    }

def keyword_match(text: str, keywords: List[str]) -> bool:
    if not keywords:
        return True
    lower = text.lower()
    return any(k.lower() in lower for k in keywords)

def build_rss(channel_items: List[Dict[str, Any]]) -> str:
    last_build = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0">',
        "<channel>",
        f"<title>{html_escape(SITE_TITLE)}</title>",
        f"<link>{html_escape(SITE_LINK)}</link>",
        f"<description>{html_escape(SITE_DESC)}</description>",
        f"<lastBuildDate>{last_build}</lastBuildDate>",
        "<language>en</language>",
    ]

    count = 0
    for it in channel_items:
        parts += [
            "<item>",
            f"<title>{html_escape(it['title'])}</title>",
            f"<link>{html_escape(it['link'])}</link>",
            f"<guid isPermaLink=\"{'true' if it['guid'].startswith('http') else 'false'}\">{html_escape(it['guid'])}</guid>",
            f"<pubDate>{it['pubDate']}</pubDate>",
            f"<description><![CDATA[{it['description']}<br/><br/>Source: <a href=\"{html_escape(it['tg_link'])}\">Telegram</a>]]></description>",
            "</item>"
        ]
        count += 1
        if count >= FEED_LIMIT:
            break

    parts += ["</channel>", "</rss>"]
    return "\n".join(parts)

async def fetch_all() -> None:
    channels = load_yaml(CHANNELS_FILE).get("channels", [])
    kw = load_yaml(KEYWORDS_FILE).get("keywords", [])
    state = load_state()

    if not channels:
        raise RuntimeError("channels.yml is empty—add channel @usernames.")

    items: List[Dict[str, Any]] = []
    
    # Calculate the cutoff date for posts
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=FEED_DAYS)
    print(f"Fetching posts from last {FEED_DAYS} days (since {cutoff_date.strftime('%Y-%m-%d %H:%M:%S UTC')})")

    async with TelegramClient(StringSession(string_session), api_id, api_hash) as client:
        for ch in channels:
            uname = ch if ch.startswith("@") else f"@{ch}"
            min_id = state.get(uname, 0)
            fetched_for_channel = 0
            channel_post_count = 0

            try:
                print(f"Fetching from {uname}...")
                async for m in client.iter_messages(uname, limit=500, min_id=min_id):
                    if not m:
                        continue
                    
                    # Check if post is too old - if so, stop fetching from this channel
                    post_date = m.date.replace(tzinfo=timezone.utc)
                    if post_date < cutoff_date:
                        print(f"  Reached posts older than {FEED_DAYS} days in {uname}, stopping...")
                        break
                    
                    text = (m.message or "").strip()
                    if not text and not m.media:
                        continue  # skip empty

                    if not keyword_match(text, kw):
                        continue

                    item = message_to_item(uname, m)
                    items.append(item)
                    channel_post_count += 1
                    fetched_for_channel = max(fetched_for_channel, m.id)

                if fetched_for_channel > 0:
                    state[uname] = max(state.get(uname, 0), fetched_for_channel)
                
                print(f"  Added {channel_post_count} posts from {uname}")

            except FloodWaitError as e:
                # Respect Telegram rate limits
                wait = int(getattr(e, "seconds", 60))
                print(f"Rate limited, waiting {wait} seconds...")
                time.sleep(wait)
            except Exception as e:
                # Continue other channels; record error as a "meta" item
                print(f"Error reading {uname}: {str(e)}")
                err_text = f"Error reading {uname}: {str(e)}"
                items.append({
                    "title": f"Error reading {uname}",
                    "link": SITE_LINK,
                    "guid": item_guid("", err_text),
                    "pubDate": datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000"),
                    "pub_datetime": datetime.now(timezone.utc),
                    "description": html_escape(err_text),
                    "tg_link": SITE_LINK
                })

    # Filter items by date (in case some were already in the list)
    items = [item for item in items if item.get("pub_datetime", datetime.now(timezone.utc)) >= cutoff_date]
    
    # Sort newest first by datetime
    items.sort(key=lambda x: x.get("pub_datetime", datetime.now(timezone.utc)), reverse=True)
    
    print(f"\nTotal posts collected: {len(items)}")

    rss = build_rss(items)
    with open(FEED_FILE, "w", encoding="utf-8") as f:
        f.write(rss)

    save_state(state)

if __name__ == "__main__":
    import asyncio
    asyncio.run(fetch_all())