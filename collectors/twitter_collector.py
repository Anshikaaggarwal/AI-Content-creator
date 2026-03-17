import json
import os
from pathlib import Path


DEFAULT_TWITTER_CACHE_PATH = "data/twitter_web3.json"


def _load_cached_tweets(path: str | os.PathLike) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "tweets" in data:
            return list(data.get("tweets") or [])
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        print(f"[Twitter] Failed to load cached tweets from {p}: {e}")
        return []


def get_viral_twitter_posts(
    limit_per_term: int = 15,  # unused but kept for API compatibility
    min_likes: int = 50,
    min_retweets: int = 2,
    min_reach: int = 1_000,
) -> list[dict]:
    """
    Load pre-scraped crypto/web3 tweets from a local JSON file produced by Apify.

    Environment variables:
      - TWITTER_CACHE_PATH: optional, path to JSON file with tweets.
        Default: data/twitter_web3.json
    """
    cache_path = os.getenv("TWITTER_CACHE_PATH", DEFAULT_TWITTER_CACHE_PATH)
    raw = _load_cached_tweets(cache_path)

    results: list[dict] = []
    for t in raw:
        if not isinstance(t, dict):
            continue

        text = (t.get("text") or t.get("full_text") or "")[:500]
        if not text.strip():
            continue

        likes = int(t.get("likes") or t.get("favorite_count", 0) or 0)
        retweets = int(t.get("retweets") or t.get("retweet_count", 0) or 0)
        reach = int(t.get("views") or t.get("impressions", 0) or 0)
        if reach <= 0:
            reach = (likes + retweets) * 50

        # Only filter when we have known (non-zero) values below threshold.
        if likes > 0 and likes < min_likes:
            continue
        if retweets > 0 and retweets < min_retweets:
            continue
        if reach > 0 and reach < min_reach:
            continue

        tweet_id = str(t.get("id_str") or t.get("id") or t.get("tweet_id") or "")
        author = (
            (t.get("user") or {}).get("screen_name")
            if isinstance(t.get("user"), dict)
            else t.get("username") or t.get("author", "")
        )
        url = t.get("url") or t.get("link") or t.get("tweet_url") or (
            f"https://twitter.com/i/status/{tweet_id}" if tweet_id else ""
        )

        results.append(
            {
                "id": tweet_id or text[:50],
                "text": text,
                "author": author,
                "likes": likes,
                "retweets": retweets,
                "reach": reach,
                "url": url,
                "source": "twitter",
            }
        )

    # Deduplicate by id
    seen = set()
    unique: list[dict] = []
    for r in results:
        rid = r.get("id") or r.get("text", "")[:50]
        if rid not in seen:
            seen.add(rid)
            unique.append(r)

    return sorted(unique, key=lambda x: x.get("likes", 0), reverse=True)
