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
