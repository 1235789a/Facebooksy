#!/usr/bin/env python3
import argparse
import csv
import re
import sys
import urllib.parse
from typing import List, Dict, Tuple

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_SCRAPING = True
except ImportError:
    HAS_SCRAPING = False

KEYWORDS = [
    "crypto trading group",
    "meme coin trading",
    "Solana trading",
    "ETH trading",
    "smart money crypto",
    "whale tracking",
    "wallet tracker crypto",
    "on-chain alpha",
    "copy trading wallets",
    "insider wallet",
    "whale alerts",
    "profitable wallets",
    "fresh wallet crypto",
    "alpha signals crypto",
]

SEARCH_TEMPLATES = [
    ('facebook_groups', 'site:facebook.com/groups "{kw}"'),
    ('facebook_groups', 'site:facebook.com/groups "{kw}" crypto'),
    ('reddit', 'site:reddit.com "{kw}"'),
    ('reddit', 'site:reddit.com "{kw}" crypto'),
    ('x', 'site:x.com "{kw}"'),
    ('x', 'site:x.com "{kw}" crypto'),
    ('telegram', 'site:t.me "{kw}"'),
    ('telegram', 'site:t.me "{kw}" crypto'),
]

HIGH_RELEVANCE_TERMS = [
    "wallet tracking", "wallet tracker", "smart money", "whale alert",
    "whale tracking", "copy trading", "on-chain alpha", "alpha signal",
    "meme coin trading", "solana trading", "eth trading", "insider wallet",
    "fresh wallet", "profitable wallet", "on chain signal",
]

MEDIUM_RELEVANCE_TERMS = [
    "crypto trading", "altcoin", "degen", "signals", "trading group",
    "crypto group", "trading signal", "crypto signal",
]

LOW_RELEVANCE_TERMS = [
    "airdrop", "giveaway", "free money", "get rich", "guaranteed",
    "100x", "1000x", "moon shot", "rug pull", "scam",
    "official announcement", "press release", "news",
]


def build_queries() -> List[Tuple[str, str, str]]:
    queries = []
    seen = set()
    for platform, template in SEARCH_TEMPLATES:
        for kw in KEYWORDS:
            q = template.replace("{kw}", kw)
            key = (platform, q)
            if key not in seen:
                seen.add(key)
                queries.append((platform, kw, q))
    return queries


def duckduckgo_search(query: str, max_results: int = 5) -> List[Dict]:
    if not HAS_SCRAPING:
        return []
    results = []
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.post(url, data={"q": query}, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select(".result")[:max_results]:
            title_el = item.select_one(".result__title a")
            snippet_el = item.select_one(".result__snippet")
            if not title_el:
                continue
            href = title_el.get("href", "")
            if href.startswith("/l/?uddg="):
                parsed = urllib.parse.urlparse(href)
                params = urllib.parse.parse_qs(parsed.query)
                if "uddg" in params:
                    href = params["uddg"][0]
            title = title_el.get_text(strip=True)
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            results.append({"title": title, "url": href, "snippet": snippet})
    except Exception:
        pass
    return results


def fallback_search_url(query: str) -> str:
    return f"https://duckduckgo.com/?q={urllib.parse.quote(query)}"


def score_relevance(title: str, snippet: str) -> Tuple[int, List[str]]:
    text = f"{title} {snippet}".lower()
    matched_high = [t for t in HIGH_RELEVANCE_TERMS if t in text]
    matched_medium = [t for t in MEDIUM_RELEVANCE_TERMS if t in text]
    matched_low = [t for t in LOW_RELEVANCE_TERMS if t in text]

    score = 3
    if matched_high:
        score = min(10, 7 + len(matched_high))
    elif matched_medium:
        score = min(7, 5 + len(matched_medium) - 1)

    if matched_low:
        score = max(1, score - len(matched_low) * 2)

    matched = matched_high + matched_medium
    return score, matched


def detect_platform(url: str, platform_hint: str) -> str:
    u = url.lower()
    if "facebook.com/groups" in u or platform_hint == "facebook_groups":
        return "Facebook Groups"
    if "reddit.com" in u or platform_hint == "reddit":
        return "Reddit"
    if "x.com" in u or "twitter.com" in u or platform_hint == "x":
        return "X (Twitter)"
    if "t.me" in u or platform_hint == "telegram":
        return "Telegram"
    return "Other"


def suggest_entry_method(platform: str, score: int) -> str:
    if score < 4:
        return "skip"
    if platform == "Facebook Groups":
        return "public post"
    if platform == "Reddit":
        return "public comment"
    if platform == "X (Twitter)":
        return "public comment"
    if platform == "Telegram":
        return "admin outreach"
    return "skip"


def assess_risk(platform: str, title: str, snippet: str) -> str:
    text = f"{title} {snippet}".lower()
    high_risk = ["scam", "rug", "guaranteed", "100x", "1000x", "get rich"]
    medium_risk = ["airdrop", "giveaway", "free"]
    if any(r in text for r in high_risk):
        return "high"
    if any(r in text for r in medium_risk):
        return "medium"
    return "low"


def generate_reason(score: int, matched: List[str], risk: str) -> str:
    if score >= 8:
        base = f"High relevance: matches strong terms ({', '.join(matched[:5])})"
    elif score >= 5:
        base = f"Medium relevance: matches general crypto terms ({', '.join(matched[:5])})"
    else:
        base = "Low relevance: generic or low-value content"
    if risk != "low":
        base += f"; {risk} risk indicators detected"
    return base


def main():
    parser = argparse.ArgumentParser(description="Whale Wallet Tracker - KR2 Community Index Tool")
    parser.add_argument("--limit", type=int, default=50, help="Max results to output (default: 50)")
    parser.add_argument("--output", type=str, default="community_index.csv", help="Output CSV file")
    parser.add_argument("--fallback", action="store_true", help="Use fallback URL-only mode (no web requests)")
    args = parser.parse_args()

    queries = build_queries()
    all_results = {}
    use_scraping = HAS_SCRAPING and not args.fallback

    if use_scraping:
        print(f"[INFO] Using DuckDuckGo HTML search. Found {len(queries)} query combinations.")
    else:
        if not HAS_SCRAPING:
            print("[WARN] requests/beautifulsoup4 not installed. Using fallback URL generation mode.")
        else:
            print("[INFO] Fallback mode enabled. Generating search URLs only.")
        print(f"[INFO] {len(queries)} search queries will be generated.")

    count = 0
    for platform_hint, keyword, query_str in queries:
        if count >= args.limit * 2:
            break

        if use_scraping:
            results = duckduckgo_search(query_str, max_results=5)
            for r in results:
                url = r["url"]
                if url in all_results:
                    continue
                title = r["title"]
                snippet = r["snippet"]
                score, matched = score_relevance(title, snippet)
                plat = detect_platform(url, platform_hint)
                entry = suggest_entry_method(plat, score)
                risk = assess_risk(plat, title, snippet)
                reason = generate_reason(score, matched, risk)
                all_results[url] = {
                    "platform": plat,
                    "title": title,
                    "url": url,
                    "query_used": query_str,
                    "matched_keywords": ", ".join(matched) if matched else keyword,
                    "estimated_relevance_score": score,
                    "suggested_entry_method": entry,
                    "risk_level": risk,
                    "reason": reason,
                }
                count += 1
        else:
            search_url = fallback_search_url(query_str)
            key = f"{platform_hint}:{query_str}"
            score, matched = score_relevance(keyword, "")
            plat = detect_platform("", platform_hint)
            entry = suggest_entry_method(plat, score)
            risk = assess_risk(plat, keyword, "")
            reason = generate_reason(score, [keyword] if not matched else matched, risk)
            all_results[search_url] = {
                "platform": plat,
                "title": f"Search: {query_str}",
                "url": search_url,
                "query_used": query_str,
                "matched_keywords": keyword,
                "estimated_relevance_score": score,
                "suggested_entry_method": entry,
                "risk_level": risk,
                "reason": reason,
            }
            count += 1

    sorted_results = sorted(
        all_results.values(),
        key=lambda x: (-x["estimated_relevance_score"], x["platform"])
    )
    sorted_results = sorted_results[:args.limit]

    fieldnames = [
        "platform", "title", "url", "query_used", "matched_keywords",
        "estimated_relevance_score", "suggested_entry_method", "risk_level", "reason"
    ]

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in sorted_results:
            writer.writerow(row)

    print(f"\n[DONE] {len(sorted_results)} results written to {args.output}")
    print(f"[INFO] Top 5 by relevance score:")
    for i, r in enumerate(sorted_results[:5], 1):
        print(f"  {i}. [{r['estimated_relevance_score']}] {r['platform']} - {r['title'][:60]}")


if __name__ == "__main__":
    main()
