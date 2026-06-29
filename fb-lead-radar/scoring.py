import re
from typing import List, Tuple

from models import Lead, NEED_TYPES
from keywords import (
    STORE_REVIEW_KEYWORDS,
    NO_SALES_KEYWORDS,
    BUILDING_PHASE_KEYWORDS,
    SHOPIFY_DESIGNER_KEYWORDS,
    PRODUCT_PAGE_KEYWORDS,
    PRODUCT_VISUALS_KEYWORDS,
    PROMO_VIDEO_KEYWORDS,
    DIGITAL_PRODUCT_KEYWORDS,
    HANDMADE_CRAFT_KEYWORDS,
    LANDING_PAGE_KEYWORDS,
    BAD_FIT_KEYWORDS,
    SERVICE_PROVIDER_KEYWORDS,
    SCAM_KEYWORDS,
    REAL_BUSINESS_SIGNALS,
    WEBSITE_PATTERNS,
)


def _count_matches(text: str, keywords: List[str]) -> int:
    text_lower = text.lower()
    count = 0
    for kw in keywords:
        if kw.lower() in text_lower:
            count += 1
    return count


def _has_any(text: str, keywords: List[str]) -> bool:
    return _count_matches(text, keywords) > 0


def classify_need_type(lead: Lead) -> str:
    text = lead.post_text.lower()
    scores = {}

    scores["store_review"] = _count_matches(text, STORE_REVIEW_KEYWORDS)
    scores["no_sales"] = _count_matches(text, NO_SALES_KEYWORDS) * 2
    scores["building_phase"] = _count_matches(text, BUILDING_PHASE_KEYWORDS)
    scores["shopify_designer_needed"] = _count_matches(text, SHOPIFY_DESIGNER_KEYWORDS)
    scores["product_page_help"] = _count_matches(text, PRODUCT_PAGE_KEYWORDS)
    scores["product_visuals_needed"] = _count_matches(text, PRODUCT_VISUALS_KEYWORDS)
    scores["promo_video_needed"] = _count_matches(text, PROMO_VIDEO_KEYWORDS)
    scores["digital_product_store"] = _count_matches(text, DIGITAL_PRODUCT_KEYWORDS)
    scores["handmade_or_craft_store"] = _count_matches(text, HANDMADE_CRAFT_KEYWORDS)

    if max(scores.values()) == 0:
        return "unclear_or_low_quality"

    return max(scores, key=scores.get)


def detect_pain_signal(lead: Lead) -> str:
    text = lead.post_text.lower()
    pains = []

    if _has_any(text, NO_SALES_KEYWORDS):
        pains.append("有流量没转化 / 不出单")
    if _has_any(text, STORE_REVIEW_KEYWORDS):
        pains.append("不知道店铺哪里有问题")
    if _has_any(text, BUILDING_PHASE_KEYWORDS):
        pains.append("店铺还在建设中")
    if _has_any(text, PRODUCT_VISUALS_KEYWORDS):
        pains.append("产品图片/素材不够好")
    if _has_any(text, PROMO_VIDEO_KEYWORDS):
        pains.append("需要产品短视频")
    if _has_any(text, PRODUCT_PAGE_KEYWORDS):
        pains.append("产品页需要优化")

    return "；".join(pains) if pains else "需求不明确"


def guess_business_type(lead: Lead) -> str:
    text = lead.post_text.lower()
    types = []

    if _has_any(text, DIGITAL_PRODUCT_KEYWORDS):
        types.append("数字产品店")
    if _has_any(text, HANDMADE_CRAFT_KEYWORDS):
        types.append("手工/手作店")
    if "dropshipping" in text or "dropship" in text:
        types.append("代发货店")
    if "print on demand" in text or "pod" in text:
        types.append("按需打印店")
    if "clothing" in text or "fashion" in text or "apparel" in text:
        types.append("服饰类")
    if "jewelry" in text:
        types.append("珠宝配饰")
    if "beauty" in text or "skincare" in text:
        types.append("美妆护肤")
    if "home" in text and ("decor" in text or "goods" in text):
        types.append("家居用品")
    if "pet" in text:
        types.append("宠物用品")

    if not types:
        types.append("电商类型不明")

    return " / ".join(types)


def check_skip(lead: Lead) -> Tuple[bool, str]:
    text = lead.post_text.lower()

    if _count_matches(text, SERVICE_PROVIDER_KEYWORDS) >= 3:
        return True, "疑似服务商发帖/广告帖"

    scam_count = _count_matches(text, SCAM_KEYWORDS)
    if scam_count >= 2:
        return True, "疑似 scam / 与电商无关"

    bad_fit_count = _count_matches(text, BAD_FIT_KEYWORDS)
    if bad_fit_count >= 3:
        return True, "需求超出能力范围（广告投放/账号代管/保证销量等）"

    if "guarantee" in text and ("sales" in text or "result" in text or "income" in text):
        return True, "承诺保证销量/结果 - 不接"

    if "manage my store" in text or "full service" in text or "entire store" in text:
        if "product page" not in text and "homepage" not in text:
            return True, "要整店代管/全套服务 - 超出范围"

    if len(text.strip()) < 30:
        return True, "帖子内容过短，没有具体需求"

    return False, ""


def score_clarity(lead: Lead) -> Tuple[float, List[str]]:
    text = lead.post_text.lower()
    score = 0
    reasons = []

    need_keywords = (
        STORE_REVIEW_KEYWORDS + NO_SALES_KEYWORDS + BUILDING_PHASE_KEYWORDS
        + SHOPIFY_DESIGNER_KEYWORDS + PRODUCT_PAGE_KEYWORDS
        + PRODUCT_VISUALS_KEYWORDS + PROMO_VIDEO_KEYWORDS
    )
    match_count = _count_matches(text, need_keywords)
    if match_count >= 2:
        score += 2
        reasons.append(f"明确提到 {match_count} 个需求关键词")
    elif match_count == 1:
        score += 1
        reasons.append("提到了一个需求方向")

    if "need" in text or "help" in text or "looking for" in text or "want" in text:
        score += 0.5
        score = min(score, 2)
        if "明确提到需求关键词" not in " ".join(reasons):
            reasons.append("有明确求助语气")

    return score, reasons


def score_fit(lead: Lead) -> Tuple[float, List[str], List[str]]:
    text = lead.post_text.lower()
    score = 1.0
    good_reasons = []
    bad_reasons = []

    good_fit_keywords = (
        PRODUCT_PAGE_KEYWORDS + LANDING_PAGE_KEYWORDS
        + PRODUCT_VISUALS_KEYWORDS + PROMO_VIDEO_KEYWORDS
        + ["first impression", "layout", "design", "sections"]
    )
    good_count = _count_matches(text, good_fit_keywords)
    if good_count >= 2:
        score += 1
        good_reasons.append(f"需求正好匹配主页/产品页/视觉/短视频方向（{good_count}个匹配）")
    elif good_count == 1:
        score += 0.5
        good_reasons.append("有一个匹配的能力方向")

    bad_fit_count = _count_matches(text, BAD_FIT_KEYWORDS)
    if bad_fit_count >= 2:
        score -= 1.5
        bad_reasons.append(f"提到了 {bad_fit_count} 个超出能力范围的需求（广告投放/代运营等）")
    elif bad_fit_count == 1:
        score -= 0.5
        bad_reasons.append("提到了一个超出范围的需求")

    if _has_any(text, ["product page", "product description", "product listing"]):
        good_reasons.append("产品页需求 - 核心能力匹配")

    if _has_any(text, ["homepage", "landing page", "layout", "sections"]):
        good_reasons.append("主页/落地页布局需求 - 核心能力匹配")

    if _has_any(text, ["product photo", "product image", "visual", "creative"]):
        good_reasons.append("产品视觉/素材需求 - 能力匹配")

    if _has_any(text, ["short video", "product video", "reel", "tiktok"]):
        good_reasons.append("短视频需求 - 能力匹配")

    score = max(0, min(2, score))
    return score, good_reasons, bad_reasons


def score_authenticity(lead: Lead) -> Tuple[float, List[str]]:
    text = lead.post_text.lower()
    score = 0
    reasons = []

    if _has_any(text, REAL_BUSINESS_SIGNALS):
        score += 1
        reasons.append("用第一人称描述自己的生意")

    has_url = any(re.search(pattern, text, re.IGNORECASE) for pattern in WEBSITE_PATTERNS)
    if has_url:
        score += 0.5
        reasons.append("贴了网站链接")

    if len(text) > 200:
        score += 0.5
        reasons.append("描述详细，内容充实")

    score = min(2, score)
    return score, reasons


def score_competition(lead: Lead) -> Tuple[float, List[str]]:
    score = 0
    reasons = []

    if lead.comment_count is not None:
        if lead.comment_count <= 3:
            score += 2
            reasons.append(f"评论很少（{lead.comment_count}条），竞争低")
        elif lead.comment_count <= 10:
            score += 1
            reasons.append(f"评论适中（{lead.comment_count}条）")
        elif lead.comment_count <= 20:
            score += 0.5
            reasons.append(f"评论较多（{lead.comment_count}条），有一定竞争")
        else:
            score += 0
            reasons.append(f"评论很多（{lead.comment_count}条），竞争激烈")
    else:
        score += 1
        reasons.append("评论数未知，默认中等竞争")

    return score, reasons


def score_deal_feasibility(lead: Lead) -> Tuple[float, List[str]]:
    text = lead.post_text.lower()
    score = 1.0
    reasons = []

    if _has_any(text, BUILDING_PHASE_KEYWORDS):
        score += 0.5
        reasons.append("新店建设期，容易从小单切入")
    else:
        score += 0.2
        reasons.append("已有店铺，可能需要先建立信任")

    if _has_any(text, PRODUCT_PAGE_KEYWORDS + PRODUCT_VISUALS_KEYWORDS + PROMO_VIDEO_KEYWORDS):
        score += 0.5
        reasons.append("需求具体（产品页/图片/视频），容易报价小单")

    if _has_any(text, BAD_FIT_KEYWORDS):
        bad_count = _count_matches(text, BAD_FIT_KEYWORDS)
        score -= min(bad_count * 0.5, 1)
        if "大而全需求" not in reasons:
            reasons.append("需求偏大，可能要完整方案")

    if _has_any(text, ["full store", "complete store", "entire website", "whole site"]):
        score -= 0.5
        reasons.append("要完整店铺，不是小单")

    if _has_any(text, ["small fix", "quick fix", "just need", "only need", "one thing"]):
        score += 0.3
        reasons.append("明确说只要改一点，小单明确")

    score = max(0, min(2, score))
    return score, reasons


def generate_angle(lead: Lead) -> str:
    need = lead.detected_need_type

    angles = {
        "store_review": "从产品页第一印象角度切入，先看再给具体建议，不要一上来就说全面review",
        "no_sales": "从产品页结构和第一印象角度切入，说我可以帮看转化漏斗的最上面那层",
        "building_phase": "从产品页和主页布局切入，说可以先搭好最核心的几块，不用一次做完整站",
        "shopify_designer_needed": "强调自己不是大agency，专做产品页和主页布局这种小而具体的活",
        "product_page_help": "直接说产品页结构和转化文案是强项，可以先改一页看看效果",
        "product_visuals_needed": "从产品图创意和布局角度切入，说可以先给几个主图优化idea",
        "promo_video_needed": "从短视频创意脚本角度切入，说可以先出15秒短视频的idea和脚本",
        "digital_product_store": "从数字产品展示和落地页角度切入，强调价值感呈现",
        "handmade_or_craft_store": "从手作产品的品牌感和故事呈现切入，强调小而美的视觉",
        "unclear_or_low_quality": "先问清楚对方卖什么、具体卡在哪一步",
    }

    return angles.get(need, "先了解清楚对方的具体需求再决定切入角度")


def generate_reply(lead: Lead) -> str:
    need = lead.detected_need_type

    replies = {
        "store_review": "I can take a quick look from a product page / first impression angle. What are you selling?",
        "no_sales": "I can take a quick look at your product pages and tell you the first thing I'd fix. What's your store?",
        "building_phase": "I'm not a big Shopify agency, but I can help with product page layout and homepage sections. What's your store about?",
        "shopify_designer_needed": "I do small Shopify design gigs — product pages, homepage layout, promo visuals. What do you need help with first?",
        "product_page_help": "Product page layout is what I do. Send your store link and I'll tell you the first thing I'd change.",
        "product_visuals_needed": "I can help with product image ideas and layout. What are you selling? Happy to throw out a few quick ideas.",
        "promo_video_needed": "I do short product video ideas. What product is this for? I can sketch out a 15-second concept.",
        "digital_product_store": "I can help with digital product landing page layout. What are you selling?",
        "handmade_or_craft_store": "I can help your handmade store look more polished — product pages, homepage layout. What do you make?",
        "unclear_or_low_quality": "Hey, saw your post. What are you selling and what do you need help with?",
    }

    return replies.get(need, "Hey, saw your post. What do you need help with?")


def calculate_contact_recommendation(total_score: float, should_skip: bool) -> str:
    if should_skip:
        return "NO"
    if total_score >= 7:
        return "YES"
    if total_score >= 5:
        return "MAYBE"
    return "NO"


def score_lead(lead: Lead) -> Lead:
    lead.should_skip, lead.skip_reason = check_skip(lead)

    if lead.should_skip:
        lead.total_score = 0
        lead.contact_recommendation = "NO"
        return lead

    lead.detected_need_type = classify_need_type(lead)
    lead.pain_signal = detect_pain_signal(lead)
    lead.business_type_guess = guess_business_type(lead)

    clarity_score, _ = score_clarity(lead)
    fit_score, fit_good, fit_bad = score_fit(lead)
    authenticity_score, _ = score_authenticity(lead)
    competition_score, _ = score_competition(lead)
    deal_score, _ = score_deal_feasibility(lead)

    lead.fit_score = fit_score

    total = round(clarity_score + fit_score + authenticity_score + competition_score + deal_score, 1)
    lead.total_score = min(total, 10.0)

    lead.why_good_fit = "；".join(fit_good) if fit_good else "匹配度一般"
    lead.why_risk = "；".join(fit_bad) if fit_bad else "无明显不匹配点"

    lead.suggested_angle = generate_angle(lead)
    lead.suggested_manual_reply = generate_reply(lead)
    lead.contact_recommendation = calculate_contact_recommendation(lead.total_score, lead.should_skip)

    return lead


def rank_leads(leads: List[Lead], top_n: int = 10) -> List[Lead]:
    valid_leads = [l for l in leads if not l.should_skip]
    valid_leads.sort(key=lambda x: x.total_score, reverse=True)
    return valid_leads[:top_n]
