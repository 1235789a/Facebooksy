import re
from typing import Optional, List

from models import Lead


def _clean_text(text: str) -> str:
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text


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
        name_patterns = [
            r"(?:Posted by|From|来自)\s*[:：]\s*([^\n]+)",
            r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s*$",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, lead.post_text, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                if len(name) > 2 and len(name) < 50:
                    lead.lead_name = name
                    break

    if not lead.post_url and lead.post_text:
        urls = re.findall(r'https?://[^\s)>\]"\'`]+', lead.post_text)
        fb_urls = [u for u in urls if 'facebook.com' in u or 'fb.com' in u]
        if fb_urls:
            lead.post_url = fb_urls[0]

    return lead


def _smart_parse_chunk(chunk: str) -> dict:
    data = {"post_text_lines": []}
    lines = chunk.split('\n')

    field_patterns = {
        'lead_name': [r'^name\s*[:：]\s*(.+)$', r'^author\s*[:：]\s*(.+)$',
                      r'^发帖人\s*[:：]\s*(.+)$', r'^作者\s*[:：]\s*(.+)$'],
        'post_url': [r'^url\s*[:：]\s*(.+)$', r'^link\s*[:：]\s*(.+)$',
                     r'^帖子链接\s*[:：]\s*(.+)$', r'^链接\s*[:：]\s*(.+)$'],
        'group_name': [r'^group\s*[:：]\s*(.+)$', r'^群组\s*[:：]\s*(.+)$',
                       r'^群名\s*[:：]\s*(.+)$'],
        'profile_url': [r'^profile\s*[:：]\s*(.+)$', r'^profile_url\s*[:：]\s*(.+)$',
                        r'^主页链接\s*[:：]\s*(.+)$', r'^个人主页\s*[:：]\s*(.+)$'],
        'post_time': [r'^time\s*[:：]\s*(.+)$', r'^date\s*[:：]\s*(.+)$',
                      r'^时间\s*[:：]\s*(.+)$', r'^发布时间\s*[:：]\s*(.+)$'],
        'comment_count': [r'^comments?\s*[:：]\s*(.+)$', r'^评论数?\s*[:：]\s*(.+)$',
                          r'^回复数?\s*[:：]\s*(.+)$'],
    }

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        matched = False
        for field, patterns in field_patterns.items():
            for pattern in patterns:
                match = re.match(pattern, line_stripped, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    if field == 'comment_count':
                        nums = re.findall(r'\d+', value)
                        if nums:
                            data[field] = int(nums[0])
                    else:
                        data[field] = value
                    matched = True
                    break
            if matched:
                break

        if not matched:
            data["post_text_lines"].append(line_stripped)

    data["post_text"] = "\n".join(data["post_text_lines"])
    del data["post_text_lines"]
    return data


def import_from_text(text: str) -> List[Lead]:
    text = _clean_text(text)
    posts = []

    if not text:
        return []

    chunks = re.split(r'\n---\n|\n\*\*\*\n|\n=+\n|\n###\s+', text)

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk or len(chunk) < 10:
            continue

        data = _smart_parse_chunk(chunk)

        if not data.get("post_text") or len(data["post_text"].strip()) < 5:
            continue

        lead = parse_manual_post(
            post_text=data.get("post_text", ""),
            lead_name=data.get("lead_name", ""),
            post_url=data.get("post_url", ""),
            group_name=data.get("group_name", ""),
            profile_url=data.get("profile_url", ""),
            post_time=data.get("post_time", ""),
            comment_count=data.get("comment_count"),
        )
        posts.append(lead)

    return posts


def import_from_clipboard_text(text: str) -> List[Lead]:
    return import_from_text(text)
