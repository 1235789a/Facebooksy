#!/bin/bash
# Whale Wallet Tracker - Lead Radar MVP 一键安装脚本
# 运行方式: bash install_lead_radar.sh

set -e

INSTALL_DIR="$HOME/Desktop/lead_radar_project"

echo "=========================================="
echo "  Lead Radar MVP 安装中..."
echo "  安装目录: $INSTALL_DIR"
echo "=========================================="
echo ""

# 创建目录结构
mkdir -p "$INSTALL_DIR/lead_radar"
mkdir -p "$INSTALL_DIR/output"

cd "$INSTALL_DIR"

# 写入所有文件
echo "📝 写入代码文件..."

cat > lead_radar/__init__.py << 'EOF'
"""Whale Wallet Tracker - Lead Radar MVP"""
__version__ = "0.1.0"
EOF

cat > lead_radar/config.py << 'EOF'
"""Configuration: keywords, scoring rules, output settings."""

REDDIT_KEYWORDS = [
    "how to track whale wallets",
    "best wallet tracker crypto",
    "smart money wallets",
    "whale alerts crypto",
    "onchain alerts",
    "tracking wallets",
    "fresh wallets",
    "crypto alpha tools",
    "Telegram bot crypto",
    "wallet tracker Solana",
]

REDDIT_SUBS = [
    "CryptoCurrency",
    "solana",
    "base",
    "memecoin",
    "CryptoMoonShots",
    "AllCryptoBets",
    "SatoshiStreetBets",
    "defi",
    "ethfinance",
    "Crypto_General",
]

X_KEYWORDS = [
    "smart money wallet",
    "whale wallet",
    "fresh wallets",
    "repeat buyers",
    "wallet tracker",
    "onchain alpha",
    "Solana alpha",
    "Base alpha",
    "meme alpha",
    "alpha group",
    "Telegram alpha",
    "Discord alpha",
    "daily alpha",
    "crypto newsletter",
    "whale alerts",
    "wallet alerts",
]

COMMUNITY_KEYWORDS = [
    "telegram", "t.me", "discord", "group", "community",
    "newsletter", "channel", "alpha room", "my group",
    "our community", "join our", "dm me", "dm for",
]

CRYPTO_CONTENT_KEYWORDS = [
    "token", "meme coin", "memecoin", "solana", "base",
    "wallet", "whale", "smart money", "on-chain", "onchain",
    "alpha", "market update", "defi", "nft", "eth",
    "btc", "crypto", "dex", "airdop", "presale",
]

MANUAL_WORKFLOW_KEYWORDS = [
    "manually checked", "manual check", "screenshot",
    "dexscreener", "arkham", "lookonchain",
    "not sure", "need to check", "anyone tracking",
    "missed this early", "missed early",
    "copied from", "i checked", "i track",
    "hard to track", "tracking manually",
]

MONETIZATION_KEYWORDS = [
    "paid", "vip", "premium", "private group",
    "dm for access", "collab", "sponsor",
    "newsletter", "referral", "affiliate",
    "subscription", "plan", "pricing",
]

PAIN_SIGNAL_KEYWORDS = [
    "missed early", "need alerts", "hard to track",
    "any tool", "who bought this", "anyone know",
    "how to find", "how to track", "can't find",
    "too many", "overwhelmed", "manual",
    "struggle", "wondering", "looking for",
    "recommend", "best way", "tool for",
]

INTERACTION_KEYWORDS = [
    "what do you think", "thoughts", "opinions",
    "let me know", "comment", "discussion",
    "agree", "disagree", "question",
]

SCAM_KEYWORDS = [
    "100x", "guaranteed profit", "fake giveaway",
    "free airdrop", "rug pull", "pump and dump",
    "click here", "link in bio", "sign up bonus",
    "make money fast", "get rich", "investment advice",
    "financial advice", "not financial advice",
]

TOP_N = 10

OUTPUT_DIR = "output"
EOF

cat > lead_radar/models.py << 'EOF'
"""Data models for leads."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional


@dataclass
class Lead:
    name: str
    username: str
    platform: str
    profile_url: str
    source_post_url: str
    bio: str = ""
    recent_post_text: str = ""
    detected_keywords: List[str] = field(default_factory=list)
    type_guess: str = "unknown"
    pain_signal: bool = False
    community_signal: bool = False
    manual_workflow_signal: bool = False
    monetization_signal: bool = False
    interaction_signal: bool = False
    score: float = 0.0
    score_breakdown: dict = field(default_factory=dict)
    suggested_angle: str = ""
    status: str = "new"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Lead":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
EOF

cat > lead_radar/reddit_source.py << 'EOF'
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
EOF

cat > lead_radar/scorer.py << 'EOF'
"""Lead scoring engine.

5 dimensions, each 0-2 points, total 0-10.
Also guesses lead type and suggests outreach angles.
"""

import re
from typing import List, Tuple

from .config import (
    COMMUNITY_KEYWORDS,
    CRYPTO_CONTENT_KEYWORDS,
    MANUAL_WORKFLOW_KEYWORDS,
    MONETIZATION_KEYWORDS,
    PAIN_SIGNAL_KEYWORDS,
    INTERACTION_KEYWORDS,
    SCAM_KEYWORDS,
)
from .models import Lead


def _find_keywords(text: str, keywords: List[str]) -> List[str]:
    """Case-insensitive keyword matching. Returns matched keywords."""
    text_lower = text.lower()
    found = []
    for kw in keywords:
        if kw.lower() in text_lower:
            found.append(kw)
    return found


def _score_dimension(text: str, keywords: List[str], max_points: int = 2) -> Tuple[float, List[str]]:
    """Score a dimension: 2 points if many matches, 1 if some, 0 if none."""
    found = _find_keywords(text, keywords)
    count = len(found)
    if count >= 3:
        score = max_points
    elif count == 2:
        score = max_points * 0.75
    elif count == 1:
        score = max_points * 0.5
    else:
        score = 0.0
    return round(score, 1), found


def _guess_type(lead: Lead) -> str:
    """Guess what kind of crypto small-B this lead is."""
    text = f"{lead.bio} {lead.recent_post_text}".lower()
    has_community = lead.community_signal
    has_monetization = lead.monetization_signal
    has_manual = lead.manual_workflow_signal

    if "newsletter" in text:
        return "newsletter operator"
    if "community manager" in text or "cm " in text or lead.bio and "cm" in lead.bio.lower():
        return "project community manager"
    if has_community and has_monetization:
        return "alpha group owner"
    if has_community and ("telegram" in text or "discord" in text):
        return "group admin / KOL"
    if "alpha" in text and "call" in text:
        return "signals / calls admin"
    if has_manual and "whale" in text:
        return "on-chain content creator"
    if has_community:
        return "community builder"
    if lead.interaction_signal and "meme" in text:
        return "meme coin KOL"
    return "ordinary trader / unknown"


def _suggest_angle(lead: Lead) -> str:
    """Suggest a non-spammy outreach angle based on signals."""
    angles = []

    if lead.pain_signal:
        if "hard to track" in lead.recent_post_text.lower() or "manual" in lead.recent_post_text.lower():
            angles.append("Acknowledge the pain of manual wallet tracking, offer a tool that auto-aggregates smart-money moves for their community")
        elif "missed early" in lead.recent_post_text.lower():
            angles.append("Mention you noticed they talked about missing early moves — share that you built a tool that catches fresh whale wallets in real-time")
        elif "looking for" in lead.recent_post_text.lower() or "recommend" in lead.recent_post_text.lower():
            angles.append("Reply to their tool-seeking post with a concise, honest take on what your bot does — no hard sell")

    if lead.manual_workflow_signal and not angles:
        angles.append("Comment on how time-consuming manual Dexscreener/Arkham checks are — share that your feed is built for people who do this daily")

    if lead.community_signal:
        if "newsletter" in lead.type_guess.lower():
            angles.append("Position as a content source for their newsletter — smart-money alerts they can repackage into their own voice")
        elif "alpha group" in lead.type_guess.lower():
            angles.append("Pitch as a way to level up their alpha group's on-chain signal quality — more edges, less manual work")
        else:
            angles.append("Offer to give them a free community plan trial — help them test if whale alerts boost engagement in their group")

    if lead.monetization_signal and not angles:
        angles.append("Frame it as a revenue multiplier — better content = higher retention = more paid members")

    if not angles:
        angles.append("Start with genuine engagement — reply to their post with a useful on-chain insight, no pitch first")

    return angles[0]


def _suggest_action(lead: Lead) -> str:
    """Suggest what to do with this lead: observe / comment manually / DM manually / skip."""
    if lead.score < 4:
        return "skip"
    if lead.score < 6:
        return "observe"
    if lead.pain_signal or lead.manual_workflow_signal:
        return "comment manually"
    if lead.community_signal and lead.monetization_signal:
        return "DM manually"
    return "observe"


def is_scam(lead: Lead) -> bool:
    """Quick scam/noise filter."""
    text = f"{lead.bio} {lead.recent_post_text}".lower()
    scam_hits = _find_keywords(text, SCAM_KEYWORDS)
    if len(scam_hits) >= 3:
        return True
    if "guaranteed" in text and "profit" in text:
        return True
    if "100x" in text and "giveaway" in text:
        return True
    return False


def score_lead(lead: Lead) -> Lead:
    """Score a single lead in-place. Returns the lead (modified)."""
    combined_text = f"{lead.bio}\n{lead.recent_post_text}"

    community_score, community_found = _score_dimension(combined_text, COMMUNITY_KEYWORDS, 2)
    crypto_score, crypto_found = _score_dimension(combined_text, CRYPTO_CONTENT_KEYWORDS, 2)
    manual_score, manual_found = _score_dimension(combined_text, MANUAL_WORKFLOW_KEYWORDS, 2)
    monetization_score, monetization_found = _score_dimension(combined_text, MONETIZATION_KEYWORDS, 2)

    interaction_score = 0.0
    interaction_found = _find_keywords(combined_text, INTERACTION_KEYWORDS)
    if lead.interaction_signal:
        interaction_score += 1.0
    if interaction_found:
        interaction_score += 0.5
    if "?" in lead.recent_post_text:
        interaction_score += 0.5
    interaction_score = min(interaction_score, 2.0)

    pain_found = _find_keywords(combined_text, PAIN_SIGNAL_KEYWORDS)

    all_keywords = list(set(
        community_found + crypto_found + manual_found +
        monetization_found + interaction_found + pain_found
    ))

    total = round(community_score + crypto_score + manual_score +
                  monetization_score + interaction_score, 1)

    lead.score = total
    lead.score_breakdown = {
        "community": community_score,
        "crypto_content": crypto_score,
        "manual_workflow": manual_score,
        "monetization": monetization_score,
        "interaction": interaction_score,
    }
    lead.detected_keywords = all_keywords
    lead.community_signal = community_score > 0
    lead.manual_workflow_signal = manual_score > 0
    lead.monetization_signal = monetization_score > 0
    lead.pain_signal = len(pain_found) > 0
    lead.type_guess = _guess_type(lead)
    lead.suggested_angle = _suggest_angle(lead)

    return lead


def score_and_filter_leads(leads: List[Lead], top_n: int = 10) -> List[Lead]:
    """Score all leads, filter out scams/low-quality, return top N."""
    scored = []
    for lead in leads:
        if is_scam(lead):
            continue
        scored_lead = score_lead(lead)
        if scored_lead.score >= 2.0:
            scored.append(scored_lead)

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:top_n]
EOF

cat > lead_radar/storage.py << 'EOF'
"""Lead storage and output: CSV, Markdown, JSON history."""

import csv
import json
import os
from datetime import datetime
from typing import List

from .models import Lead


def ensure_output_dir(output_dir: str = "output") -> str:
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def _today_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def export_csv(leads: List[Lead], output_dir: str = "output") -> str:
    """Export top leads to CSV. Returns file path."""
    ensure_output_dir(output_dir)
    path = os.path.join(output_dir, f"lead_radar_{_today_str()}.csv")

    fieldnames = [
        "rank", "score", "platform", "username", "profile_url",
        "source_post_url", "type_guess", "why_lead", "pain_points",
        "signals", "suggested_angle", "suggested_action",
        "detected_keywords", "bio", "status", "created_at",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, lead in enumerate(leads, 1):
            why = []
            if lead.community_signal:
                why.append("has community")
            if lead.manual_workflow_signal:
                why.append("manual workflow")
            if lead.monetization_signal:
                why.append("monetization setup")
            if lead.type_guess and lead.type_guess != "unknown":
                why.append(lead.type_guess)

            pain = []
            if lead.pain_signal:
                pain = [kw for kw in lead.detected_keywords
                        if kw.lower() in ("missed early", "need alerts",
                                          "hard to track", "any tool",
                                          "who bought this", "manual",
                                          "looking for", "recommend",
                                          "best way", "how to track")]

            signals = []
            if lead.community_signal:
                signals.append("community")
            if lead.monetization_signal:
                signals.append("monetization")
            if lead.manual_workflow_signal:
                signals.append("manual-workflow")
            if lead.interaction_signal:
                signals.append("interactive")
            if lead.pain_signal:
                signals.append("pain")

            action = _action_for_lead(lead)

            writer.writerow({
                "rank": i,
                "score": lead.score,
                "platform": lead.platform,
                "username": lead.username,
                "profile_url": lead.profile_url,
                "source_post_url": lead.source_post_url,
                "type_guess": lead.type_guess,
                "why_lead": "; ".join(why),
                "pain_points": "; ".join(pain) if pain else "none detected",
                "signals": ", ".join(signals),
                "suggested_angle": lead.suggested_angle,
                "suggested_action": action,
                "detected_keywords": ", ".join(lead.detected_keywords[:15]),
                "bio": lead.bio[:300],
                "status": lead.status,
                "created_at": lead.created_at,
            })

    return path


def _action_for_lead(lead: Lead) -> str:
    if lead.score < 4:
        return "skip"
    if lead.score < 6:
        return "observe"
    if lead.pain_signal or lead.manual_workflow_signal:
        return "comment manually"
    if lead.community_signal and lead.monetization_signal:
        return "DM manually"
    return "observe"


def export_markdown(leads: List[Lead], output_dir: str = "output") -> str:
    """Export top leads as a readable Markdown report. Returns file path."""
    ensure_output_dir(output_dir)
    path = os.path.join(output_dir, f"lead_radar_{_today_str()}.md")

    lines = []
    lines.append(f"# Daily Lead Radar — {_today_str()}")
    lines.append("")
    lines.append(f"**Top {len(leads)} leads** from today's scan.")
    lines.append("")
    lines.append("---")
    lines.append("")

    for i, lead in enumerate(leads, 1):
        signals = []
        if lead.community_signal:
            signals.append("community")
        if lead.monetization_signal:
            signals.append("monetization")
        if lead.manual_workflow_signal:
            signals.append("manual-workflow")
        if lead.interaction_signal:
            signals.append("interactive")
        if lead.pain_signal:
            signals.append("pain-signal")

        breakdown = lead.score_breakdown or {}
        breakdown_str = (
            f"community={breakdown.get('community', 0)}, "
            f"crypto={breakdown.get('crypto_content', 0)}, "
            f"manual={breakdown.get('manual_workflow', 0)}, "
            f"monetization={breakdown.get('monetization', 0)}, "
            f"interaction={breakdown.get('interaction', 0)}"
        )

        action = _action_for_lead(lead)

        lines.append(f"## #{i} — {lead.username} ({lead.score}/10)")
        lines.append("")
        lines.append(f"- **Platform:** {lead.platform}")
        lines.append(f"- **Profile:** {lead.profile_url}")
        lines.append(f"- **Source post:** {lead.source_post_url or 'n/a'}")
        lines.append(f"- **Type guess:** {lead.type_guess}")
        lines.append(f"- **Signals:** {', '.join(signals) if signals else 'none'}")
        lines.append(f"- **Score breakdown:** {breakdown_str}")
        lines.append("")
        lines.append(f"### Why they look like a prospect")
        lines.append("")
        lines.append(_prospect_reason(lead))
        lines.append("")
        lines.append(f"### Pain points detected")
        lines.append("")
        lines.append(_pain_summary(lead))
        lines.append("")
        lines.append(f"### Community & monetization signals")
        lines.append("")
        lines.append(_signal_summary(lead))
        lines.append("")
        lines.append(f"### Suggested angle")
        lines.append("")
        lines.append(f"> {lead.suggested_angle}")
        lines.append("")
        lines.append(f"**Suggested action:** `{action}`")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("")
    lines.append(f"*Generated by Lead Radar MVP — {_today_str()}*")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return path


def _prospect_reason(lead: Lead) -> str:
    reasons = []
    if lead.type_guess and lead.type_guess != "unknown":
        reasons.append(f"Profile/activity suggests they are a **{lead.type_guess}**.")
    if lead.community_signal:
        reasons.append("They mention a community/group/Telegram/Discord — potential customer of a community plan.")
    if lead.manual_workflow_signal:
        reasons.append("They appear to do manual on-chain research (screenshots, Dexscreener, etc.) — our product saves them time.")
    if lead.monetization_signal:
        reasons.append("They already monetize their audience (VIP/premium/private group) — they can afford and benefit from better content tools.")
    if lead.interaction_signal:
        reasons.append("They have real interactions in comments — higher chance they'll reply to an outreach.")
    if not reasons:
        reasons.append("Crypto-related activity detected, but signal is weak. Worth monitoring.")
    return "\n".join(f"- {r}" for r in reasons)


def _pain_summary(lead: Lead) -> str:
    pains = []
    text = f"{lead.bio} {lead.recent_post_text}".lower()
    if "manual" in text or "manually" in text:
        pains.append("Doing things manually — would benefit from automation")
    if "hard to track" in text or "can't find" in text:
        pains.append("Struggling to track wallets / find smart money")
    if "missed" in text and "early" in text:
        pains.append("Missing early moves — wants faster alerts")
    if "looking for" in text or "recommend" in text or "best way" in text:
        pains.append("Actively looking for tools/solutions")
    if not pains:
        return "No strong pain signal detected from current data. Would need more posts or direct engagement to confirm."
    return "\n".join(f"- {p}" for p in pains)


def _signal_summary(lead: Lead) -> str:
    sigs = []
    text = f"{lead.bio} {lead.recent_post_text}".lower()
    if "telegram" in text or "t.me" in text:
        sigs.append("Telegram presence detected")
    if "discord" in text:
        sigs.append("Discord presence detected")
    if "newsletter" in text:
        sigs.append("Newsletter mentioned")
    if "vip" in text or "premium" in text or "paid" in text:
        sigs.append("Paid/monetized offering mentioned")
    if "private group" in text or "dm for access" in text:
        sigs.append("Private group / gated access")
    if not sigs:
        return "No explicit community or monetization signals in current data."
    return "\n".join(f"- {s}" for s in sigs)


def save_all_leads_json(leads: List[Lead], output_dir: str = "output") -> str:
    """Save full lead list as JSON for history / re-processing."""
    ensure_output_dir(output_dir)
    path = os.path.join(output_dir, f"all_leads_{_today_str()}.json")
    data = [lead.to_dict() for lead in leads]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path
EOF

cat > lead_radar/manual_import.py << 'EOF'
"""Manual import of leads from X/Twitter or other sources.

Since X scraping is complex and risky for an MVP, we support manual entry.
You can paste X profile URLs + bio/post text, and we'll score them.
"""

import csv
import json
import re
from typing import List

from .models import Lead


def parse_manual_csv(filepath: str) -> List[Lead]:
    """Import leads from a CSV file with manual entries.

    Expected columns:
        name, username, platform, profile_url, source_post_url,
        bio, recent_post_text
    """
    leads = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lead = Lead(
                name=row.get("name", row.get("username", "")),
                username=row.get("username", ""),
                platform=row.get("platform", "x"),
                profile_url=row.get("profile_url", ""),
                source_post_url=row.get("source_post_url", ""),
                bio=row.get("bio", ""),
                recent_post_text=row.get("recent_post_text", ""),
            )
            if lead.username or lead.profile_url:
                leads.append(lead)
    return leads


def parse_manual_json(filepath: str) -> List[Lead]:
    """Import leads from a JSON array."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Lead.from_dict(item) for item in data]


def interactive_x_import() -> List[Lead]:
    """Interactive CLI to paste X/Twitter profile info."""
    print("\n=== Manual X / Twitter Lead Import ===")
    print("Paste info one lead at a time. Empty username when done.\n")
    leads = []
    while True:
        username = input("Username (@ handle): ").strip()
        if not username:
            break
        username = username.lstrip("@")
        profile_url = input(f"Profile URL (default: https://x.com/{username}): ").strip()
        if not profile_url:
            profile_url = f"https://x.com/{username}"
        source_post_url = input("Source tweet/post URL: ").strip()
        bio = input("Bio: ").strip()
        print("Recent post text (multi-line, end with Ctrl-D or empty line):")
        post_lines = []
        while True:
            try:
                line = input()
                if not line and post_lines:
                    break
                post_lines.append(line)
            except EOFError:
                break
        recent_post_text = "\n".join(post_lines)

        lead = Lead(
            name=username,
            username=username,
            platform="x",
            profile_url=profile_url,
            source_post_url=source_post_url,
            bio=bio,
            recent_post_text=recent_post_text,
        )
        leads.append(lead)
        print(f"  Added: @{username}\n")

    return leads


def quick_x_lead(username: str, bio: str = "", post_text: str = "",
                 source_url: str = "") -> Lead:
    """Create a single X lead quickly (for programmatic use)."""
    username = username.lstrip("@")
    return Lead(
        name=username,
        username=username,
        platform="x",
        profile_url=f"https://x.com/{username}",
        source_post_url=source_url,
        bio=bio,
        recent_post_text=post_text,
    )
EOF

cat > lead_radar/__main__.py << 'EOF'
"""Main CLI entry point for Lead Radar.

Usage:
    python -m lead_radar reddit                # scrape & score Reddit
    python -m lead_radar import --csv FILE     # import manual CSV & score
    python -m lead_radar interactive           # interactive manual import
    python -m lead_radar full                  # Reddit + manual (if file exists)
"""

import argparse
import os
import sys

from .config import (
    REDDIT_KEYWORDS,
    REDDIT_SUBS,
    TOP_N,
    OUTPUT_DIR,
)
from .reddit_source import search_reddit, enrich_reddit_leads
from .scorer import score_and_filter_leads
from .storage import export_csv, export_markdown, save_all_leads_json
from .manual_import import parse_manual_csv


def run_reddit(top_n: int = TOP_N, output_dir: str = OUTPUT_DIR,
               limit_per_kw: int = 25, enrich: bool = True,
               proxy: str = None) -> list:
    """Run the full Reddit pipeline."""
    print("\n" + "=" * 60)
    print("  Lead Radar MVP — Reddit Scan")
    print("=" * 60 + "\n")

    print(f"Keywords: {len(REDDIT_KEYWORDS)} across {len(REDDIT_SUBS)} subs")
    print(f"Limit per keyword: {limit_per_kw} posts")
    if proxy:
        print(f"Proxy: {proxy}")
    print()

    leads = search_reddit(
        keywords=REDDIT_KEYWORDS,
        subreddits=REDDIT_SUBS,
        limit_per_keyword=limit_per_kw,
        proxy=proxy,
    )

    if not leads:
        print("\nNo leads found. Check network or try different keywords.")
        return []

    if enrich:
        print(f"\nEnriching top user profiles (fetching bios)...")
        leads = enrich_reddit_leads(leads, max_users=min(50, len(leads)),
                                    proxy=proxy)

    print(f"\nScoring and filtering {len(leads)} leads...")
    top_leads = score_and_filter_leads(leads, top_n=top_n)

    if not top_leads:
        print("\nNo leads passed scoring threshold.")
        return []

    csv_path = export_csv(top_leads, output_dir)
    md_path = export_markdown(top_leads, output_dir)
    json_path = save_all_leads_json(leads, output_dir)

    print("\n" + "=" * 60)
    print(f"  Top {len(top_leads)} Leads")
    print("=" * 60 + "\n")

    for i, lead in enumerate(top_leads, 1):
        print(f"  #{i}  {lead.score:>4}/10  {lead.platform:8s}  u/{lead.username}")
        print(f"       {lead.type_guess}")
        print(f"       {lead.profile_url}")
        print()

    print(f"  CSV output:  {csv_path}")
    print(f"  Markdown:    {md_path}")
    print(f"  Full JSON:   {json_path}")
    print()

    return top_leads


def run_import(csv_file: str, top_n: int = TOP_N,
               output_dir: str = OUTPUT_DIR) -> list:
    """Import leads from CSV and score them."""
    print(f"\nImporting leads from: {csv_file}")
    if not os.path.exists(csv_file):
        print(f"  Error: file not found: {csv_file}")
        return []

    leads = parse_manual_csv(csv_file)
    print(f"  Imported {len(leads)} leads")

    if not leads:
        return []

    print(f"  Scoring...")
    top_leads = score_and_filter_leads(leads, top_n=top_n)

    csv_path = export_csv(top_leads, output_dir)
    md_path = export_markdown(top_leads, output_dir)

    print(f"\n  Top {len(top_leads)} from import:")
    for i, lead in enumerate(top_leads, 1):
        print(f"  #{i}  {lead.score:>4}/10  {lead.platform:8s}  {lead.username}")

    print(f"\n  CSV output:  {csv_path}")
    print(f"  Markdown:    {md_path}\n")

    return top_leads


def main():
    parser = argparse.ArgumentParser(
        description="Whale Wallet Tracker — Lead Radar MVP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m lead_radar reddit
  python -m lead_radar reddit --top 20
  python -m lead_radar import --csv my_leads.csv
  python -m lead_radar full --manual-csv x_leads.csv
  python -m lead_radar reddit --proxy http://127.0.0.1:7890
        """,
    )
    parser.add_argument("command", choices=["reddit", "import", "full"],
                        help="What to run")
    parser.add_argument("--top", type=int, default=TOP_N,
                        help=f"Number of top leads to output (default: {TOP_N})")
    parser.add_argument("--output-dir", default=OUTPUT_DIR,
                        help=f"Output directory (default: {OUTPUT_DIR})")
    parser.add_argument("--limit-per-kw", type=int, default=25,
                        help="Posts per keyword on Reddit (default: 25)")
    parser.add_argument("--no-enrich", action="store_true",
                        help="Skip fetching user bios on Reddit (faster)")
    parser.add_argument("--csv", dest="csv_file", default="",
                        help="CSV file for import command")
    parser.add_argument("--manual-csv", default="",
                        help="Additional manual CSV for 'full' command")
    parser.add_argument("--proxy", default=None,
                        help="HTTP/SOCKS proxy, e.g. http://127.0.0.1:7890")

    args = parser.parse_args()

    if args.command == "reddit":
        run_reddit(
            top_n=args.top,
            output_dir=args.output_dir,
            limit_per_kw=args.limit_per_kw,
            enrich=not args.no_enrich,
            proxy=args.proxy,
        )
    elif args.command == "import":
        if not args.csv_file:
            print("Error: --csv required for import command")
            sys.exit(1)
        run_import(args.csv_file, top_n=args.top, output_dir=args.output_dir)
    elif args.command == "full":
        all_leads = []
        reddit_leads = run_reddit(
            top_n=args.top,
            output_dir=args.output_dir,
            limit_per_kw=args.limit_per_kw,
            enrich=not args.no_enrich,
            proxy=args.proxy,
        )
        all_leads.extend(reddit_leads)

        if args.manual_csv and os.path.exists(args.manual_csv):
            manual_leads = run_import(
                args.manual_csv, top_n=args.top, output_dir=args.output_dir
            )
            all_leads.extend(manual_leads)

        if all_leads:
            from .scorer import score_and_filter_leads as saf
            combined = saf(all_leads, top_n=args.top)
            md_path = export_markdown(combined, args.output_dir)
            print(f"  Combined Top {args.top} Markdown: {md_path}")


if __name__ == "__main__":
    main()
EOF

# 写入 sample CSV 模板
cat > sample_x_leads.csv << 'EOF'
name,username,platform,profile_url,source_post_url,bio,recent_post_text
AlphaWhaleGuy,alphawhaleguy,x,https://x.com/alphawhaleguy,https://x.com/alphawhaleguy/status/123456789,"Building the best Solana alpha Telegram group. Daily whale wallet alerts for my VIP members. 👇 t.me/alpha_whale_group","Just manually tracked 12 fresh wallets that bought $SOLPEPE early. Missed the first one but caught the rest with Dexscreener. Anyone else tracking smart money wallets? It's so hard to keep up manually. Join my Telegram for daily alpha calls - VIP for premium signals."
EOF

# 写入 README
cat > README.md << 'EOF'
# Whale Wallet Tracker — Lead Radar MVP

A minimum viable lead radar for finding crypto-native small-B prospects (alpha group admins, KOLs, newsletter operators, community managers) who could benefit from smart-money whale alert tools.

**No auto-DM, no auto-comment, no spam.** Just research, scoring, and a daily Top 10 shortlist for manual outreach.

---

## Quick start

### Run a Reddit scan (with proxy)

```bash
python -m lead_radar reddit --proxy http://127.0.0.1:7890
```

### Import manual X/Twitter leads

```bash
python -m lead_radar import --csv sample_x_leads.csv
```

### Run everything combined

```bash
python -m lead_radar full --manual-csv my_x_leads.csv --proxy http://127.0.0.1:7890
```

## CLI options

```
positional arguments:
  {reddit,import,full}   What to run

optional arguments:
  --top N                Number of top leads (default: 10)
  --output-dir DIR       Output directory (default: output)
  --limit-per-kw N       Posts per keyword on Reddit (default: 25)
  --no-enrich            Skip Reddit user bio fetching (faster)
  --csv FILE             CSV file for 'import' command
  --manual-csv FILE      Manual CSV for 'full' command
  --proxy URL            HTTP/SOCKS proxy (e.g. http://127.0.0.1:7890)
```

## Scoring rules (0-10)

| Dimension | Points | How to score |
|-----------|--------|--------------|
| Community identity | 0-2 | Telegram/Discord/group/community/newsletter mentions |
| Crypto content | 0-2 | Token/Solana/whale/on-chain/alpha mentions |
| Manual workflow | 0-2 | Screenshots, Dexscreener, Arkham, "need to check", etc. |
| Monetization | 0-2 | VIP, premium, paid group, collab, sponsor, newsletter |
| Interaction | 0-2 | Comments, replies, questions, discussions |

## Output files

- `output/lead_radar_YYYY-MM-DD.md` — readable report with full analysis
- `output/lead_radar_YYYY-MM-DD.csv` — spreadsheet-friendly format
- `output/all_leads_YYYY-MM-DD.json` — raw data for re-processing

## Important: what this tool does NOT do

- ❌ No auto-DM or auto-comment
- ❌ No auto-follow or auto-join
- ❌ No scraping of private data
- ❌ No bypassing platform rate limits or anti-bot measures
- ❌ No spam or mass outreach

This is a **research and scoring tool**. All outreach is manual and human-initiated.

## Customizing keywords

Edit `lead_radar/config.py` to adjust keywords, subreddits, and scoring rules.
EOF

echo ""
echo "✅ 安装完成！"
echo ""
echo "📂 安装目录: $INSTALL_DIR"
echo ""
echo "🚀 快速开始（需要梯子开着）:"
echo "   cd $INSTALL_DIR"
echo "   python -m lead_radar reddit --proxy http://127.0.0.1:7890"
echo ""
echo "📖 查看 README 了解更多用法"
echo ""
