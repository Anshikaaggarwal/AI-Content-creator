### AI Content Creator – Viral Crypto/Web3 Engine

This app is a Streamlit-based “Viral Crypto Content Engine” that helps Web3 creators turn high-signal market content into concrete ideas for Reels, YouTube videos, and Twitter threads.

A short walkthrough of the flow and UI:  
[Project Loom overview](https://www.loom.com/share/cf0723a9c67d44de96b8252e8c25a863)

---

### Features

- **Multi-source collection**
  - **YouTube** (`collectors/youtube_collector.py`):
    - Scrapes long-form + Shorts via `scrapetube` for many crypto/Web3 search terms and selected channels.
    - Parses views, likes (best-effort), duration, published time, and classifies videos as `short` / `long`.
    - Filters by min views/likes, recency, and crypto/Web3 keywords in the title to avoid off-topic videos.
  - **Reddit** (`collectors/reddit_collector.py`):
    - Uses Selenium on **old.reddit.com** (no API keys).
    - Scrapes hot posts from major crypto subreddits, filtered by score (upvotes).
  - **Twitter/X** (`collectors/twitter_collector.py` + `apify_fetch_twitter.py`):
    - No live scraping in the app; loads a local JSON cache (`data/twitter_web3.json`).
    - The cache is generated offline via an Apify actor/task using only keyword search (e.g. `web3`, `defi`, `onchain`) and strong engagement filters (likes / impressions).
  - **Crypto news** (`collectors/news_collector.py`):
    - Ingests RSS feeds from CoinDesk, CoinTelegraph, Decrypt, and The Block via `feedparser`.

- **Pattern analysis with Gemini**
  - `analyzer.py` sends top YouTube/Reddit/Twitter items and news headlines to Gemini.
  - Gemini returns:
    - Viral hooks
    - Popular topics
    - Storytelling structures
    - Trending narratives
    - Key emotions
    - A short market summary

- **Idea generation with Gemini**
  - `generator.py` turns patterns into:
    - 5 Instagram Reel ideas
    - 3 YouTube video ideas
    - 3 Twitter thread ideas  
  - Each idea has a hook, topic, angle, CTA/structure/thread outline.
  - Includes robust JSON parsing to handle minor formatting issues from the LLM.

- **Creator-friendly UI** (`app.py`)
  - Single-page Streamlit UX:
    1. **Collect**: run pipeline (YouTube, Reddit, News, cached Twitter).
    2. **Inspect**: clean expanders for each platform showing titles + basic metrics.
    3. **Analyze**: platform-specific hooks (raw titles) + Gemini cross-platform summary.
    4. **Generate**: structured Reels, YouTube, and Thread ideas.

---

### Environment variables

Create `thesujalshow/.env`:

```env
# Gemini
GEMINI_API_KEY=...

# Apify
APIFY_TOKEN=...
APIFY_TWITTER_ACTOR_ID=...        # e.g. sovereigntaylor/twitter-scraper or another actor ID
APIFY_TWITTER_TASK_ID=...         # optional: saved task ID with “Maximum cost per run”
TWITTER_CACHE_PATH=data/twitter_web3.json
```

---

## Run locally

This project is a single-process Streamlit app. You do NOT need `uvicorn` unless you add a separate FastAPI/Flask backend.

1) Activate your virtual environment:

```bash
venv\Scripts\activate
```

2) Install dependencies:

```bash
pip install -r requirements.txt
```

3) Run the Streamlit app:

```bash
python -m streamlit run app.py
```

Then open:

```text
http://localhost:8501
```


```bash
python -m streamlit run app.py --server.port 8502
```

