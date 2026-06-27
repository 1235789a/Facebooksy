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
