"""Reddit public search source - uses Reddit's public JSON API.

No API key needed. Uses urllib from stdlib to keep dependencies minimal.
Respects rate limits and only reads public posts.
"""

import json
import os
import time
import urllib.parse
import urllib.request
from typing import List, Optional

from .models import Lead

USER_AGENT = "LeadRadar/0.1 (MVP research tool; public data only)"


def _build_opener(proxy: Optional[str] = None):
    """Build urllib opener with optional HTTP/SOCKS proxy."""
    handlers = []
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    if handlers:
        return urllib.request.build_opener(*handlers)
    return None


def _reddit_json_get(url: str, timeout: int = 15,
                     proxy: Optional[str] = None) -> Optional[dict]:
    """Fetch JSON from Reddit with a polite user-agent and optional proxy."""
    headers = {"User-Agent": USER_AGENT}
    req = urllib.request.Request(url, headers=headers)
    try:
        if proxy:
            opener = _build_opener(proxy)
            with opener.open(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        else:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [warn] Reddit request failed: {e}")
        return None


def _fetch_user_info(username: str, proxy: Optional[str] = None) -> dict:
    """Fetch basic user profile info from Reddit."""
    url = f"https://www.reddit.com/user/{username}/about.json"
    data = _reddit_json_get(url, proxy=proxy)
    if not data:
        return {}
    return data.get("data", {})


def search_reddit(keywords: List[str], subreddits: List[str] = None,
                  limit_per_keyword: int = 25, max_age_days: int = 7,
                  proxy: Optional[str] = None) -> List[Lead]:
    """Search Reddit for posts matching keywords and collect leads.

    Only uses public search endpoints. Collects the poster as a lead candidate.
    proxy format: "http://127.0.0.1:7890" or "socks5h://127.0.0.1:7890"
    """
    subreddits = subreddits or ["all"]
    leads_by_username: dict[str, Lead] = {}

    for sub in subreddits:
        for kw in keywords:
            print(f"  Searching r/{sub} for: {kw}")
            query = urllib.parse.quote(kw)
            url = (
                f"https://www.reddit.com/r/{sub}/search.json"
                f"?q={query}&restrict_sr=1&sort=relevance"
                f"&t=week&limit={limit_per_keyword}"
            )
            data = _reddit_json_get(url, proxy=proxy)
            if not data:
                time.sleep(2)
                continue

            children = data.get("data", {}).get("children", [])
            for post in children:
                p = post.get("data", {})
                author = p.get("author", "")
                if not author or author == "[deleted]":
                    continue

                permalink = p.get("permalink", "")
                post_url = f"https://reddit.com{permalink}" if permalink else ""
                title = p.get("title", "")
                selftext = p.get("selftext", "")
                full_text = f"{title}\n{selftext}"
                num_comments = p.get("num_comments", 0)

                if author in leads_by_username:
                    existing = leads_by_username[author]
                    existing.recent_post_text += f"\n\n---\n{full_text}"
                    if not existing.source_post_url:
                        existing.source_post_url = post_url
                    if num_comments > 3:
                        existing.interaction_signal = True
                else:
                    profile_url = f"https://reddit.com/user/{author}"
                    lead = Lead(
                        name=author,
                        username=author,
                        platform="reddit",
                        profile_url=profile_url,
                        source_post_url=post_url,
                        bio="",
                        recent_post_text=full_text,
                        detected_keywords=[],
                        interaction_signal=(num_comments > 3),
                    )
                    leads_by_username[author] = lead

            time.sleep(2)  # polite delay between requests

    print(f"  Collected {len(leads_by_username)} unique Reddit authors")
    return list(leads_by_username.values())


def enrich_reddit_leads(leads: List[Lead], max_users: int = 50,
                       proxy: Optional[str] = None) -> List[Lead]:
    """Fetch user bios for top leads (limited to avoid rate limits)."""
    enriched = 0
    for lead in leads:
        if enriched >= max_users:
            break
        if lead.platform != "reddit" or lead.bio:
            continue
        info = _fetch_user_info(lead.username, proxy=proxy)
        if info:
            lead.bio = info.get("subreddit", {}).get("public_description", "")
            if not lead.bio:
                lead.bio = info.get("title", "")
            comment_karma = info.get("comment_karma", 0)
            total_karma = info.get("total_karma", 0)
            if comment_karma > 1000:
                lead.interaction_signal = True
            lead.name = info.get("subreddit", {}).get("title", lead.username)
            enriched += 1
        time.sleep(1.5)
    print(f"  Enriched {enriched} Reddit user profiles")
    return leads
