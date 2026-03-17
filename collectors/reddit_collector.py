import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


CRYPTO_SUBREDDITS = ["CryptoCurrency", "Bitcoin", "ethereum", "altcoin", "CryptoMoonShots"]


OLD_REDDIT_BASE = "https://old.reddit.com"


def _get_driver(headless: bool = True) -> webdriver.Chrome:
    """Create headless Chrome driver. Uses webdriver-manager if available."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-background-networking")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
    except ImportError:
        service = None
    if service:
        return webdriver.Chrome(service=service, options=options)
    return webdriver.Chrome(options=options)


def _parse_score(text: str) -> int:
    """Parse score from text like '1.2k', '50', '2.3m'."""
    if not text:
        return 0
    text = text.strip().replace(",", "").lower()
    try:
        if text.endswith("k"):
            return int(float(text[:-1]) * 1_000)
        if text.endswith("m"):
            return int(float(text[:-1]) * 1_000_000)
        return int(float(text))
    except ValueError:
        return 0


def get_viral_reddit_posts(
    limit_per_sub: int = 10,
    min_score: int = 20,
    headless: bool = True,
) -> list[dict]:
    driver = _get_driver(headless=headless)
    results = []
    try:
        for sub_name in CRYPTO_SUBREDDITS:
            url = f"{OLD_REDDIT_BASE}/r/{sub_name}/hot/"
            try:
                driver.get(url)
                # Old Reddit uses .thing for each post
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.thing"))
                )
                time.sleep(1)
            except Exception as e:
                print(f"[Reddit] Error loading r/{sub_name}: {e}")
                continue

            # Old Reddit: div.thing = post, a.title = title link, .score = upvotes
            posts = driver.find_elements(By.CSS_SELECTOR, "div.thing")
            count = 0
            for post in posts:
                if count >= limit_per_sub:
                    break
                try:
                    # Skip promoted / ads
                    if "promoted" in (post.get_attribute("class") or "").lower():
                        continue
                    title_el = post.find_element(By.CSS_SELECTOR, "a.title")
                    title = title_el.text.strip() or "Unknown"
                    href = title_el.get_attribute("href") or ""
                except Exception:
                    continue

                if not href or "reddit.com" not in href:
                    continue

                score = 0
                try:
                    score_el = post.find_element(By.CSS_SELECTOR, "div.score")
                    raw = (score_el.get_attribute("title") or score_el.text or "").replace(" points", "").strip()
                    score = _parse_score(raw)
                except Exception:
                    pass
                if score < min_score:
                    continue

                post_id = ""
                m = re.search(r"/comments/([a-z0-9]+)/", href)
                if m:
                    post_id = m.group(1)

                results.append({
                    "id": post_id or href,
                    "title": title,
                    "score": score,
                    "comments": 0,
                    "url": href,
                    "subreddit": sub_name,
                    "text": "",
                    "source": "reddit",
                })
                count += 1
    finally:
        driver.quit()

    return sorted(results, key=lambda x: x["score"], reverse=True)
