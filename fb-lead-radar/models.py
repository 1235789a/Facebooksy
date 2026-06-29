from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


NEED_TYPES = [
    "store_review",
    "no_sales",
    "building_phase",
    "shopify_designer_needed",
    "product_page_help",
    "product_visuals_needed",
    "promo_video_needed",
    "digital_product_store",
    "handmade_or_craft_store",
    "unclear_or_low_quality",
]

STATUS_TYPES = ["new", "reviewed", "contacted", "replied", "rejected"]


@dataclass
class Lead:
    lead_name: str = ""
    platform: str = "Facebook"
    profile_url: str = ""
    post_url: str = ""
    group_name: str = ""
    post_time: str = ""
    post_text: str = ""
    detected_need_type: str = "unclear_or_low_quality"
    pain_signal: str = ""
    business_type_guess: str = ""
    urgency_score: float = 0.0
    fit_score: float = 0.0
    competition_level: float = 0.0
    total_score: float = 0.0
    suggested_angle: str = ""
    suggested_manual_reply: str = ""
    status: str = "new"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    comment_count: Optional[int] = None
    why_good_fit: str = ""
    why_risk: str = ""
    contact_recommendation: str = "MAYBE"
    skip_reason: str = ""
    should_skip: bool = False
