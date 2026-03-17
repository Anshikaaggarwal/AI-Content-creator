import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()


def analyze_patterns(
    youtube_data: list,
    reddit_data: list,
    news_data: list,
    twitter_data: list | None = None,
) -> dict:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # Build a compact summary for the prompt
    yt_titles = [
        f"[{v['views']:,} views, {v.get('likes', 0):,} likes, {v.get('format', 'long')}] {v['title']}"
        for v in youtube_data[:20]
    ]
    reddit_titles = [f"[{p['score']} upvotes] {p['title']}" for p in reddit_data[:20]]
    news_titles = [f"[{n['source']}] {n['title']}" for n in news_data[:20]]
    twitter_data = twitter_data or []
    twitter_titles = [
        f"[{t.get('likes', 0):,} likes, {t.get('retweets', 0)} RTs] {t.get('text', '')[:80]}..."
        for t in twitter_data[:20]
    ]

    prompt = f"""
You are a viral content analyst for crypto/finance social media.

Analyze the following viral crypto content and identify patterns:

## Top YouTube Videos (by views; format=short/long):
{chr(10).join(yt_titles)}

## Top Reddit Posts (by upvotes):
{chr(10).join(reddit_titles)}

## Viral Twitter/X Posts (crypto, web3):
{chr(10).join(twitter_titles) if twitter_titles else "(none)"}

## Latest Crypto News Headlines:
{chr(10).join(news_titles)}

Respond ONLY with a valid JSON object in this exact structure:
{{
  "viral_hooks": ["hook1", "hook2", "hook3", "hook4", "hook5"],
  "popular_topics": ["topic1", "topic2", "topic3", "topic4", "topic5"],
  "storytelling_structures": ["structure1", "structure2", "structure3"],
  "trending_narratives": ["narrative1", "narrative2", "narrative3"],
  "key_emotions": ["emotion1", "emotion2", "emotion3"],
  "summary": "2-3 sentence overview of what's driving engagement right now"
}}
"""

    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    text = (response.text or "").strip()

    # Strip markdown code blocks if present
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1]
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "viral_hooks": [],
            "popular_topics": [],
            "storytelling_structures": [],
            "trending_narratives": [],
            "key_emotions": [],
            "summary": "Analysis unavailable (invalid response).",
        }
