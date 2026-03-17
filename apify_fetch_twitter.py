import json
import os
from pathlib import Path

from apify_client import ApifyClient
from dotenv import load_dotenv


load_dotenv()


APIFY_TOKEN = os.getenv("APIFY_TOKEN")
TASK_ID = os.getenv("APIFY_TWITTER_TASK_ID")
ACTOR_ID = os.getenv("APIFY_TWITTER_ACTOR_ID", "apidojo/twitter-scraper-lite")
CACHE_PATH = os.getenv("TWITTER_CACHE_PATH", "data/twitter_web3.json")


def fetch_web3_tweets(
    max_tweets: int = 12,
    min_likes: int = 500,
    min_impressions: int = 10_000,
) -> None:
    if not APIFY_TOKEN:
        raise RuntimeError("APIFY_TOKEN not set in .env")

    client = ApifyClient(APIFY_TOKEN)

    search_terms = [
        "web3",
        "defi",
        "onchain",
    ]

    # Input shape adapted for sovereigntaylor/twitter-scraper
    run_input = {
        "handles": [],                  # IMPORTANT: no user handles, so no @elonmusk etc.
        "searchTerms": search_terms,    # keyword-based search only
        "maxTweets": max_tweets,
        "includeReplies": False,
        "scrapeProfile": False,
        "includeMedia": True,
        # Let the actor decide proxy settings; don't force useApifyProxy here.
    }

    # Prefer calling a saved task (with cost limit configured in Console) when TASK_ID is set.
    if TASK_ID:
        run = client.task(TASK_ID).call(input=run_input)
    else:
        run = client.actor(ACTOR_ID).call(run_input=run_input)

    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

    filtered: list[dict] = []
    for t in items:
        if not isinstance(t, dict):
            continue
        likes = int(t.get("likes") or t.get("favorite_count", 0) or 0)
        impressions = int(t.get("views") or t.get("impressions", 0) or 0)

        # Always enforce strong like threshold
        if likes < min_likes:
            continue
        # Only enforce impressions threshold when we actually have an impressions value
        if impressions > 0 and impressions < min_impressions:
            continue

        filtered.append(t)

    cache_path = Path(CACHE_PATH)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(filtered, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(filtered)} tweets to {cache_path}")


if __name__ == "__main__":
    fetch_web3_tweets()

