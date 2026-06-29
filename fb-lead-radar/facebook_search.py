import json
import re
import subprocess
import shutil
from typing import List, Optional

from models import Lead


def is_opencli_available() -> bool:
    return shutil.which("opencli") is not None


def check_opencli_status() -> dict:
    if not is_opencli_available():
        return {
            "available": False,
            "reason": "opencli 命令未找到",
            "fix": "安装：npm install -g @jackwener/opencli",
        }

    try:
        result = subprocess.run(
            ["opencli", "daemon", "status"],
            capture_output=True, text=True, timeout=15
        )
        output = result.stdout + result.stderr
        daemon_running = "running" in output.lower() and "not running" not in output.lower()
        extension_connected = "extension: connected" in output.lower()

        return {
            "available": True,
            "daemon_running": daemon_running,
            "extension_connected": extension_connected,
            "raw_output": output.strip(),
            "ready": extension_connected,
        }
    except subprocess.TimeoutExpired:
        return {
            "available": True,
            "daemon_running": False,
            "extension_connected": False,
            "raw_output": "timeout",
            "ready": False,
        }
    except Exception as e:
        return {
            "available": True,
            "error": str(e),
            "ready": False,
        }


def check_facebook_status() -> dict:
    if not is_opencli_available():
        return {
            "status": "unavailable",
            "reason": "OpenCLI 未安装",
            "fix_steps": [
                "1. 安装 OpenCLI: npm install -g @jackwener/opencli",
                "2. 在 Chrome 浏览器安装 OpenCLI 扩展",
                "   https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk",
                "3. 在 Chrome 中登录 facebook.com",
                "4. 运行 opencli doctor 验证连接",
            ]
        }

    st = check_opencli_status()
    if not st.get("ready", False):
        return {
            "status": "not_configured",
            "opencli_status": st,
            "reason": "OpenCLI 已安装但 Chrome 扩展未连接或未登录 Facebook",
            "fix_steps": [
                "1. 确保 Chrome 浏览器已打开",
                "2. 安装 OpenCLI Chrome 扩展（如果还没装）：",
                "   https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk",
                "3. 在 Chrome 中登录 facebook.com（建议用小号）",
                "4. 运行: opencli doctor",
                "5. 确认显示 Extension: connected",
                "注意：必须是桌面环境，服务器/无头环境无法使用 OpenCLI",
            ]
        }

    return {
        "status": "ready",
        "opencli_status": st,
        "note": "Facebook 渠道可用，复用 Chrome 登录态",
    }


def search_facebook_posts(keyword: str, max_results: int = 20) -> List[Lead]:
    if not is_opencli_available():
        raise RuntimeError("OpenCLI 未安装")

    st = check_opencli_status()
    if not st.get("ready", False):
        raise RuntimeError("OpenCLI 未就绪，请先配置 Chrome 扩展和 Facebook 登录")

    try:
        result = subprocess.run(
            ["opencli", "facebook", "search", keyword, "-f", "json"],
            capture_output=True, text=True, timeout=60
        )
        output = result.stdout.strip()

        if not output:
            return []

        data = None
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            try:
                data = json.loads(result.stderr.strip())
            except Exception:
                pass

        if data is None:
            return _parse_text_output(output, keyword)

        return _parse_json_results(data, keyword)

    except subprocess.TimeoutExpired:
        print(f"搜索超时: {keyword}")
        return []
    except Exception as e:
        print(f"搜索出错: {keyword} - {e}")
        return []


def _parse_json_results(data, keyword: str) -> List[Lead]:
    leads = []
    items = []

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for key in ["results", "posts", "items", "data"]:
            if key in data and isinstance(data[key], list):
                items = data[key]
                break
        if not items:
            items = [data]

    for item in items:
        if not isinstance(item, dict):
            continue

        lead = Lead()
        lead.post_text = item.get("text", item.get("content", item.get("message", "")))
        lead.lead_name = item.get("author", item.get("name", item.get("from", "")))
        if isinstance(lead.lead_name, dict):
            lead.lead_name = lead.lead_name.get("name", "")

        lead.post_url = item.get("url", item.get("link", item.get("permalink", "")))
        lead.profile_url = item.get("author_url", item.get("profile_url", ""))
        lead.group_name = item.get("group", item.get("group_name", ""))
        lead.post_time = item.get("time", item.get("created_time", item.get("date", "")))

        comments = item.get("comments", item.get("comment_count", 0))
        if isinstance(comments, (int, float)):
            lead.comment_count = int(comments)
        elif isinstance(comments, dict):
            lead.comment_count = comments.get("count", 0)

        if lead.post_text:
            leads.append(lead)

    return leads


def _parse_text_output(text: str, keyword: str) -> List[Lead]:
    leads = []
    lines = text.splitlines()
    current_post = {}

    for line in lines:
        line = line.strip()
        if not line:
            if current_post.get("text"):
                lead = Lead()
                lead.post_text = current_post.get("text", "")
                lead.lead_name = current_post.get("author", "")
                lead.post_url = current_post.get("url", "")
                lead.group_name = current_post.get("group", "")
                leads.append(lead)
            current_post = {}
            continue

        if line.startswith("Author:") or line.startswith("作者:"):
            current_post["author"] = line.split(":", 1)[1].strip()
        elif line.startswith("URL:") or line.startswith("链接:"):
            current_post["url"] = line.split(":", 1)[1].strip()
        elif line.startswith("Group:") or line.startswith("群组:"):
            current_post["group"] = line.split(":", 1)[1].strip()
        elif line.startswith("Text:") or line.startswith("内容:"):
            current_post["text"] = line.split(":", 1)[1].strip()
        elif "text" not in current_post:
            current_post["text"] = current_post.get("text", "") + " " + line

    if current_post.get("text"):
        lead = Lead()
        lead.post_text = current_post.get("text", "")
        lead.lead_name = current_post.get("author", "")
        lead.post_url = current_post.get("url", "")
        lead.group_name = current_post.get("group", "")
        leads.append(lead)

    return leads


def search_multiple_keywords(keywords: List[str], per_keyword_max: int = 10) -> List[Lead]:
    all_leads = []
    seen_urls = set()

    for kw in keywords:
        print(f"搜索关键词: {kw}")
        try:
            leads = search_facebook_posts(kw, max_results=per_keyword_max)
            for lead in leads:
                if lead.post_url and lead.post_url in seen_urls:
                    continue
                if lead.post_url:
                    seen_urls.add(lead.post_url)
                all_leads.append(lead)
            print(f"  找到 {len(leads)} 条结果")
        except Exception as e:
            print(f"  搜索失败: {e}")

    return all_leads
