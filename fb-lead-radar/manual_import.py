import re
from typing import Optional

from models import Lead


def parse_manual_post(
    post_text: str,
    lead_name: str = "",
    post_url: str = "",
    group_name: str = "",
    profile_url: str = "",
    post_time: str = "",
    comment_count: Optional[int] = None,
) -> Lead:
    lead = Lead()
    lead.post_text = post_text.strip()
    lead.lead_name = lead_name.strip()
    lead.post_url = post_url.strip()
    lead.group_name = group_name.strip()
    lead.profile_url = profile_url.strip()
    lead.post_time = post_time.strip()
    lead.comment_count = comment_count

    if not lead.lead_name and lead.post_text:
        name_match = re.search(r"(?:Posted by|From|来自)\s*[:：]\s*([^\n]+)", post_text, re.IGNORECASE)
        if name_match:
            lead.lead_name = name_match.group(1).strip()

    if not lead.post_url and lead.post_text:
        url_match = re.search(r'https?://[^\s)>\]"]+', post_text)
        if url_match:
            lead.profile_url = lead.profile_url or ""

    return lead


def import_from_text(text: str) -> list:
    posts = []
    chunks = re.split(r'\n---\n|\n\*\*\*\n|\n=+\n', text.strip())

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        lines = chunk.split('\n')
        data = {"post_text": ""}
        text_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            lower = line.lower()
            if lower.startswith("name:") or lower.startswith("author:") or lower.startswith("发帖人:"):
                data["lead_name"] = line.split(":", 1)[1].strip()
            elif lower.startswith("url:") or lower.startswith("link:") or lower.startswith("帖子链接:"):
                data["post_url"] = line.split(":", 1)[1].strip()
            elif lower.startswith("group:") or lower.startswith("群组:"):
                data["group_name"] = line.split(":", 1)[1].strip()
            elif lower.startswith("profile:") or lower.startswith("profile_url:") or lower.startswith("主页链接:"):
                data["profile_url"] = line.split(":", 1)[1].strip()
            elif lower.startswith("time:") or lower.startswith("date:") or lower.startswith("时间:"):
                data["post_time"] = line.split(":", 1)[1].strip()
            elif lower.startswith("comments:") or lower.startswith("评论数:"):
                try:
                    data["comment_count"] = int(re.findall(r'\d+', line)[0])
                except (IndexError, ValueError):
                    pass
            else:
                text_lines.append(line)

        data["post_text"] = "\n".join(text_lines)

        if data["post_text"]:
            posts.append(parse_manual_post(**data))

    return posts
