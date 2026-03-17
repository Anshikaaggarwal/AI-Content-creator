import os
import json
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()


def _safe_parse_gemini_json(text: str) -> dict:
    """
    Try to robustly parse JSON from a Gemini response.
    Falls back to an empty-structure dict if parsing fails.
    """
    cleaned = text.strip()

    # Strip surrounding markdown fences like ```json ... ```
    if cleaned.startswith("```"):
        parts = cleaned.split("```")
        if len(parts) >= 2:
            cleaned = parts[1]
        if cleaned.lstrip().startswith("json"):
            cleaned = cleaned.lstrip()[4:]

    cleaned = cleaned.strip()

    # First attempt: direct JSON parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Second attempt: extract the largest {...} block
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        candidate = match.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Final fallback: return an empty but valid structure
    return {
        "instagram_reels": [],
        "youtube_videos": [],
        "twitter_threads": [],
    }


def generate_content_ideas(patterns: dict) -> dict:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    prompt = f"""
You are a viral crypto content strategist. Based on these patterns from top-performing content:

Viral Hooks: {patterns.get('viral_hooks', [])}
Popular Topics: {patterns.get('popular_topics', [])}
Storytelling Structures: {patterns.get('storytelling_structures', [])}
Trending Narratives: {patterns.get('trending_narratives', [])}
Key Emotions: {patterns.get('key_emotions', [])}
Market Context: {patterns.get('summary', '')}

Generate content ideas. Respond ONLY with valid JSON in this exact structure:
{{
  "instagram_reels": [
    {{
      "hook": "opening line that grabs attention in 2 seconds",
      "topic": "specific topic covered",
      "angle": "unique angle or storyline",
      "cta": "call to action"
    }}
  ],
  "youtube_videos": [
    {{
      "hook": "thumbnail/title hook",
      "topic": "specific topic covered",
      "angle": "unique angle or storyline",
      "structure": "brief outline of video flow"
    }}
  ],
  "twitter_threads": [
    {{
      "hook": "first tweet that stops the scroll",
      "topic": "specific topic covered",
      "angle": "unique angle or storyline",
      "thread_outline": ["tweet 1 topic", "tweet 2 topic", "tweet 3 topic", "thread end/CTA"]
    }}
  ]
}}

Generate exactly 5 instagram_reels, 3 youtube_videos, and 3 twitter_threads.
Make them highly specific, not generic. Use real crypto terminology and current trends.
"""

    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    text = response.text or ""

    return _safe_parse_gemini_json(text)
