import feedparser
import requests
from bs4 import BeautifulSoup


CRYPTO_RSS_FEEDS = [
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("CoinTelegraph", "https://cointelegraph.com/rss"),
    ("Decrypt", "https://decrypt.co/feed"),
    ("The Block", "https://www.theblock.co/rss.xml"),
]


def get_crypto_news(limit_per_feed: int = 10) -> list[dict]:
    results = []

    for source_name, feed_url in CRYPTO_RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:limit_per_feed]:
                results.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", "")[:400],
                    "url": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "source": source_name,
                })
        except Exception as e:
            print(f"[News] Error fetching {source_name}: {e}")

    return results
