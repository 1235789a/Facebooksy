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
