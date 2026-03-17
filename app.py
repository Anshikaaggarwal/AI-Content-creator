import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from collectors.youtube_collector import get_viral_youtube_videos
from collectors.reddit_collector import get_viral_reddit_posts
from collectors.news_collector import get_crypto_news
from collectors.twitter_collector import get_viral_twitter_posts
from analyzer import analyze_patterns
from generator import generate_content_ideas

st.set_page_config(page_title="Viral Crypto Content Engine", page_icon="🚀", layout="wide")

st.title("🚀 Viral Crypto Content Engine")
st.caption("Collects viral content → Identifies patterns → Generates content ideas using Gemini AI")

# ── Sidebar controls ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    yt_limit = st.slider("YouTube videos per search term", 5, 20, 10)
    reddit_limit = st.slider("Reddit posts per subreddit", 5, 25, 10)
    news_limit = st.slider("News articles per feed", 5, 20, 10)
    min_views = st.number_input("Min YouTube views", value=50_000, step=10_000)
    min_likes_yt = st.number_input("Min YouTube likes", value=100, step=50)
    min_score_reddit = st.number_input("Min Reddit score", value=20, step=5)
    min_likes_twitter = st.number_input("Min Twitter likes", value=50, step=25)
    min_retweets = st.number_input("Min Twitter retweets", value=2, step=1)
    min_reach_twitter = st.number_input("Min Twitter reach (approx)", value=1000, step=1000)
    use_reddit = st.checkbox("Include Reddit ", value=True)
    use_twitter = st.checkbox("Include Twitter ", value=True)
    use_news = st.checkbox("Include Crypto News", value=True)

# Persist collected data so we don't call Gemini until user clicks "Analyze"
if "yt_data" not in st.session_state:
    st.session_state.yt_data = []
if "reddit_data" not in st.session_state:
    st.session_state.reddit_data = []
if "twitter_data" not in st.session_state:
    st.session_state.twitter_data = []
if "news_data" not in st.session_state:
    st.session_state.news_data = []
if "collection_done" not in st.session_state:
    st.session_state.collection_done = False

run = st.button("▶ Fetch data from sources", type="primary", use_container_width=True)

if run:
    # ── Step 1: Collect only (no Gemini) ───────────────────────────────────────
    st.header("1️⃣ Collect viral crypto content")

    with st.spinner("Scraping YouTube (videos + shorts)..."):
        yt_data = get_viral_youtube_videos(
            limit_per_term=yt_limit,
            min_views=int(min_views),
            min_likes=int(min_likes_yt),
        )
    st.success(f"✅ YouTube: {len(yt_data)} videos collected (long + short)")

    reddit_data = []
    if use_reddit:
        with st.spinner("Scraping Reddit "):
            try:
                reddit_data = get_viral_reddit_posts(
                    limit_per_sub=reddit_limit,
                    min_score=int(min_score_reddit),
                )
                st.success(f"✅ Reddit: {len(reddit_data)} posts collected")
            except Exception as e:
                st.warning(f"Reddit skipped: {e}")

    twitter_data = []
    if use_twitter:
        with st.spinner("Scraping Twitter"):
            try:
                twitter_data = get_viral_twitter_posts(
                    limit_per_term=15,
                    min_likes=int(min_likes_twitter),
                    min_retweets=int(min_retweets),
                    min_reach=int(min_reach_twitter),
                )
                st.success(f"✅ Twitter: {len(twitter_data)} posts collected")
            except Exception as e:
                st.warning(f"Twitter skipped: {e}")

    news_data = []
    if use_news:
        with st.spinner("Fetching crypto news RSS feeds..."):
            news_data = get_crypto_news(limit_per_feed=news_limit)
        st.success(f"✅ News: {len(news_data)} articles collected")

    # Save to session so we can run Gemini later on button click
    st.session_state.yt_data = yt_data
    st.session_state.reddit_data = reddit_data
    st.session_state.twitter_data = twitter_data
    st.session_state.news_data = news_data
    st.session_state.collection_done = True

# When we have collected data, show it and offer "Analyze & Generate" (uses Gemini)
if st.session_state.collection_done:
    yt_data = st.session_state.yt_data
    reddit_data = st.session_state.reddit_data
    twitter_data = st.session_state.twitter_data
    news_data = st.session_state.news_data

    st.header("1️⃣ Collected data")
    with st.expander("📺 YouTube — long form & shorts"):
        if yt_data:
            for v in yt_data[:10]:
                fmt = v.get("format", "long")
                st.markdown(f"**{v['title']}**")
                st.caption(
                    f"{v['views']:,} views · {v.get('likes', 0):,} likes · {fmt.upper()} · {v['published']}"
                )
        else:
            st.caption("No YouTube data. Lower min views/likes or check connection.")

    if reddit_data:
        with st.expander("🔴 Reddit"):
            for p in reddit_data[:10]:
                st.markdown(f"**{p['title']}**")
                st.caption(f"{p['score']:,} upvotes · r/{p['subreddit']}")

    if twitter_data:
        with st.expander("🐦 Twitter"):
            for t in twitter_data[:10]:
                st.markdown(f"**{t.get('text', '')[:80]}...**")
                st.caption(f"{t.get('likes', 0):,} likes · {t.get('retweets', 0)} retweets")
    elif use_twitter:
        with st.expander("🐦 Twitter"):
            st.caption("No cached Twitter data found. Run your Apify scraper and export to the JSON path set in TWITTER_CACHE_PATH.")

    if news_data:
        with st.expander("📰 News"):
            for n in news_data[:10]:
                st.markdown(f"**[{n['source']}]** {n['title']}")

    total = len(yt_data) + len(reddit_data) + len(twitter_data) + len(news_data)
    st.caption(f"Total items: {total} — Click below to analyze and generate ideas.")

    analyze_clicked = False
    if total == 0:
        st.warning("No data collected. Lower filters (min views, min likes) or enable more sources, then run the pipeline again.")
    else:
        analyze_clicked = st.button("🧠 Analyze patterns & generate ideas (Gemini)", type="primary", use_container_width=True)

    if total > 0 and analyze_clicked:
        # ── Step 2: Analyze ───────────────────────────────────────────────
        st.header("2️⃣ Identify patterns")
        with st.spinner("Analyzing pattern"):
            patterns = analyze_patterns(yt_data, reddit_data, news_data, twitter_data)

        # Platform-level hooks from raw data (for creators who want to inspect titles directly)
        st.subheader("🎯 Platform hooks")
        col_y, col_r, col_t = st.columns(3)

        with col_y:
            st.markdown("**YouTube**")
            for v in yt_data[:6]:
                st.markdown(f"- {v['title']}")

        with col_r:
            st.markdown("**Reddit**")
            for p in reddit_data[:6]:
                st.markdown(f"- {p['title']}")

        with col_t:
            st.markdown("**Twitter**")
            for tw in twitter_data[:6]:
                st.markdown(f"- {tw.get('text', '')[:80]}...")

        st.divider()

        # Gemini summary of patterns
        st.subheader("Summary of cross‑platform pattern")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🎣 Viral Hooks**")
            for h in patterns.get("viral_hooks", []):
                st.markdown(f"- {h}")

            st.markdown("**🔥 Popular Topics**")
            for t in patterns.get("popular_topics", []):
                st.markdown(f"- {t}")

            st.markdown("**💡 Key Emotions**")
            for e in patterns.get("key_emotions", []):
                st.markdown(f"- {e}")

        with col2:
            st.markdown("**📖 Storytelling Structures**")
            for s in patterns.get("storytelling_structures", []):
                st.markdown(f"- {s}")

            st.markdown("**📈 Trending Narratives**")
            for n in patterns.get("trending_narratives", []):
                st.markdown(f"- {n}")

        st.info(f"**Market Context:** {patterns.get('summary', '')}")

        # ── Step 3: Generate ──────────────────────────────────────────────
        st.header("3️⃣ Generate content ideas")
        with st.spinner("Generating viral content ideas with Gemini..."):
            ideas = generate_content_ideas(patterns)

        st.subheader("Instagram Reel Ideas")
        for i, reel in enumerate(ideas.get("instagram_reels", []), 1):
            with st.expander(f"Reel {i}: {reel.get('topic', '')}"):
                st.markdown(f"**Hook:** {reel.get('hook', '')}")
                st.markdown(f"**Topic:** {reel.get('topic', '')}")
                st.markdown(f"**Angle:** {reel.get('angle', '')}")
                st.markdown(f"**CTA:** {reel.get('cta', '')}")

        st.subheader("YouTube Video Ideas")
        for i, video in enumerate(ideas.get("youtube_videos", []), 1):
            with st.expander(f"Video {i}: {video.get('topic', '')}"):
                st.markdown(f"**Hook:** {video.get('hook', '')}")
                st.markdown(f"**Topic:** {video.get('topic', '')}")
                st.markdown(f"**Angle:** {video.get('angle', '')}")
                st.markdown(f"**Structure:** {video.get('structure', '')}")

        st.subheader("Twitter Thread Ideas")
        for i, thread in enumerate(ideas.get("twitter_threads", []), 1):
            with st.expander(f"Thread {i}: {thread.get('topic', '')}"):
                st.markdown(f"**Hook Tweet:** {thread.get('hook', '')}")
                st.markdown(f"**Topic:** {thread.get('topic', '')}")
                st.markdown(f"**Angle:** {thread.get('angle', '')}")
                st.markdown("**Thread Outline:**")
                for j, tweet in enumerate(thread.get("thread_outline", []), 1):
                    st.markdown(f"  {j}. {tweet}")

        st.balloons()
        st.success("Done!")
