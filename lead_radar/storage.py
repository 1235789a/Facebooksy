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
