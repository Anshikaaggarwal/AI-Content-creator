import re
import scrapetube


CRYPTO_SEARCH_TERMS = [
    "crypto",
    "web3",
    "blockchain",
    "bitcoin",
    "ethereum",
    "altcoins",
    "defi",
    "nft",
    "dao",

    "what is crypto",
    "what is web3",
    "crypto explained",
    "blockchain explained",
    "defi explained",
    "nft explained",
    "crypto for beginners",
    "web3 for beginners",
    "bitcoin explained",
    "ethereum explained",

    "crypto investing",
    "crypto trading",
    "crypto passive income",
    "make money crypto",
    "earn from crypto",
    "crypto portfolio",
    "best crypto to buy",
    "top altcoins",
    "crypto 100x",
    "next bitcoin",

    "crypto bull run",
    "crypto bear market",
    "bitcoin price prediction",
    "ethereum prediction",
    "altcoin season",
    "crypto news",
    "crypto trends",
    "crypto update",

    "smart contracts",
    "layer 2 crypto",
    "zk rollups",
    "tokenomics",
    "crypto staking",
    "yield farming",
    "liquidity mining",
    "on chain analysis",
    "crypto wallets",
    "metamask tutorial",

    "solana crypto",
    "polygon crypto",
    "arbitrum crypto",
    "optimism crypto",
    "binance crypto",
    "coinbase crypto",

    "crypto crash",
    "crypto scam",
    "is crypto dead",
    "future of crypto",
    "web3 future",
    "crypto secrets",
    "crypto mistakes",
    "crypto strategy",

    "web3 jobs",
    "crypto career",
    "earn in web3",
    "freelance web3",
]

# Extra terms to include Shorts (short-form)
SHORTS_SEARCH_TERMS = [
    "crypto shorts",
    "bitcoin shorts",
    "web3 shorts",
    "defi shorts",
    "nft shorts",
    "crypto tips",
    "crypto facts",
    "crypto quick explanation",
]
CRYPTO_CHANNELS = [
    "UCqK_GSMbpiV8spgD3ZGloSw",  # Coin Bureau
    "UCl2oCaw8hdR_kbqyqd2klIA",  # Crypto Banter
]

# Extra safety keywords to ensure results stay crypto/web3 related even when YouTube search returns off-topic videos
CRYPTO_KEYWORDS = [
    "crypto",
    "bitcoin",
    "btc",
    "ethereum",
    "eth",
    "altcoin",
    "altcoins",
    "web3",
    "blockchain",
    "defi",
    "nft",
    "nfts",
    "solana",
    "layer 2",
    "l2",
    "tokenomics",
    "stablecoin",
    "airdrops",
    "on-chain",
]

# YouTube Shorts = 60 seconds or less
SHORT_FORM_MAX_SECONDS = 60


def _parse_view_count(video: dict) -> int:
    try:
        text = video.get("viewCountText", {})
        if isinstance(text, dict) and "simpleText" in text:
            text = text["simpleText"]
        else:
            return 0
        text = text.replace(" views", "").replace(",", "").strip()
        if "M" in text:
            return int(float(text.replace("M", "")) * 1_000_000)
        if "K" in text:
            return int(float(text.replace("K", "")) * 1_000)
        return int(text)
    except Exception:
        return 0


def _parse_duration_seconds(video: dict) -> int | None:
    """Parse lengthText (e.g. '1:23', '0:45') to seconds. Returns None if missing."""
    try:
        length_text = video.get("lengthText") or video.get("lengthSeconds")
        if length_text is None:
            return None
        if isinstance(length_text, dict) and "simpleText" in length_text:
            length_text = length_text["simpleText"].strip()
        elif isinstance(length_text, (int, float)):
            return int(length_text)
        elif isinstance(length_text, str) and length_text.isdigit():
            return int(length_text)
        # "1:23" or "0:45"
        if isinstance(length_text, str) and ":" in length_text:
            parts = length_text.split(":")
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return None
    except Exception:
        return None


def _parse_like_count(video: dict) -> int:
    """Parse like count from video dict. Search results often don't have it; use 0 as fallback."""
    try:
        # Some responses have top-level likeCount
        if "likeCount" in video:
            return int(video["likeCount"])
        # Accessibility label sometimes: "1.2M views, 50K likes"
        acc = video.get("accessibility", {})
        if isinstance(acc, dict) and "accessibilityData" in acc:
            label = acc["accessibilityData"].get("label", "")
            if "likes" in label.lower():
                # e.g. "50K likes" or "1,234 likes"
                m = re.search(r"([\d,\.]+[KMB]?)\s*likes?", label, re.I)
                if m:
                    raw = m.group(1).replace(",", "").strip()
                    if raw.endswith("M"):
                        return int(float(raw[:-1]) * 1_000_000)
                    if raw.endswith("K"):
                        return int(float(raw[:-1]) * 1_000)
                    return int(float(raw))
        return 0
    except Exception:
        return 0


def _estimate_age_days(published_text: str) -> int | None:
    """Estimate age in days from YouTube's publishedTimeText (e.g. '3 days ago', '2 years ago')."""
    if not published_text:
        return None
    text = published_text.lower().strip()
    # Handle "streamed X days ago" / "premiered X hours ago"
    text = text.replace("streamed ", "").replace("premiered ", "")
    m = re.search(r"(\d+)\s+(second|seconds|minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years)", text)
    if not m:
        return None
    value = int(m.group(1))
    unit = m.group(2)
    if "second" in unit or "minute" in unit or "hour" in unit:
        return 0
    if "day" in unit:
        return value
    if "week" in unit:
        return value * 7
    if "month" in unit:
        return value * 30
    if "year" in unit:
        return value * 365
    return None


def _is_relevant_by_time(published_text: str, title: str, max_age_days: int) -> bool:
    """
    Keep recent content, but also allow older evergreen videos (explainers, tutorials, guides).
    """
    age = _estimate_age_days(published_text)
    if age is None:
        # If we can't parse the age, keep the video (fail open).
        return True
    if age <= max_age_days:
        return True

    # Older than max_age_days → keep only if looks evergreen (still relevant today)
    evergreen_keywords = [
        "what is",
        "explained",
        "tutorial",
        "for beginners",
        "beginner",
        "guide",
        "strategy",
        "how to",
        "wallet",
        "introduction",
    ]
    lower_title = (title or "").lower()
    return any(k in lower_title for k in evergreen_keywords)


def _format_type(duration_seconds: int | None) -> str:
    """Return 'short' or 'long' based on duration."""
    if duration_seconds is None:
        return "long"  # unknown => treat as long
    return "short" if duration_seconds <= SHORT_FORM_MAX_SECONDS else "long"


def _parse_video(video: dict) -> dict:
    try:
        title = "Unknown"
        if "title" in video and "runs" in video["title"]:
            title = video["title"]["runs"][0].get("text", "Unknown")
    except Exception:
        pass

    duration_sec = _parse_duration_seconds(video)
    views = _parse_view_count(video)
    likes = _parse_like_count(video)

    video_id = video.get("videoId", "")
    return {
        "id": video_id,
        "title": title,
        "views": views,
        "likes": likes,
        "published": (video.get("publishedTimeText") or {}).get("simpleText", ""),
        "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else "",
        "source": "youtube",
        "format": _format_type(duration_sec),  # "short" | "long"
        "duration_seconds": duration_sec,
    }


def _is_crypto_relevant_title(title: str) -> bool:
    """
    Simple title-level relevance check so obviously off-topic videos (e.g. music) don't enter the dataset.
    """
    if not title:
        return False
    lower = title.lower()
    return any(k in lower for k in CRYPTO_KEYWORDS)


def get_viral_youtube_videos(
    limit_per_term: int = 10,
    min_views: int = 50_000,
    min_likes: int = 100,
    max_age_days: int = 60,
    include_shorts: bool = True,
) -> list[dict]:
    results = []

    # Only filter by min_likes when we have like data (scrapetube often returns 0 for search)
    def _passes_likes(likes: int) -> bool:
        if likes == 0:
            return True  # unknown, don't filter out
        return likes >= min_likes

    # Search by keywords (videos + mixed), sorted by view_count to get high-engagement
    for term in CRYPTO_SEARCH_TERMS:
        try:
            videos = scrapetube.get_search(term, limit=limit_per_term, sort_by="view_count")
            for video in videos:
                parsed = _parse_video(video)
                if (
                    parsed["views"] >= min_views
                    and _passes_likes(parsed["likes"])
                    and _is_relevant_by_time(parsed["published"], parsed["title"], max_age_days)
                    and _is_crypto_relevant_title(parsed["title"])
                ):
                    results.append(parsed)
        except Exception as e:
            print(f"[YouTube] Error searching '{term}': {e}")

    # Optional: extra shorts-focused searches
    if include_shorts:
        for term in SHORTS_SEARCH_TERMS:
            try:
                videos = scrapetube.get_search(term, limit=min(limit_per_term, 15), sort_by="view_count")
                for video in videos:
                    parsed = _parse_video(video)
                    if (
                        parsed["views"] >= min_views
                        and _passes_likes(parsed["likes"])
                        and _is_relevant_by_time(parsed["published"], parsed["title"], max_age_days)
                        and _is_crypto_relevant_title(parsed["title"])
                    ):
                        results.append(parsed)
            except Exception as e:
                print(f"[YouTube] Error searching shorts '{term}': {e}")

    # Top videos from known channels
    for channel_id in CRYPTO_CHANNELS:
        try:
            videos = scrapetube.get_channel(channel_id, limit=limit_per_term, sort_by="popular")
            for video in videos:
                parsed = _parse_video(video)
                if (
                    _passes_likes(parsed["likes"])
                    and _is_relevant_by_time(parsed["published"], parsed["title"], max_age_days)
                    and _is_crypto_relevant_title(parsed["title"])
                ):
                    results.append(parsed)
        except Exception as e:
            print(f"[YouTube] Error fetching channel {channel_id}: {e}")

    # Deduplicate by video id
    seen = set()
    unique = []
    for v in results:
        if v["id"] not in seen:
            seen.add(v["id"])
            unique.append(v)

    return sorted(unique, key=lambda x: x["views"], reverse=True)
