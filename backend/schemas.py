from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class UserBase(BaseModel):
    email: str
    username: str
    full_name: Optional[str] = None


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        import re
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError("Invalid email format")
        return v

    @field_validator("password")
    @classmethod
    def valid_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    role: str
    is_active: bool
    created_at: datetime


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    url: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = "en"
    reliability_score: int = 88
    bias_rating: str = "center"


class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    slug: str
    summary: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    author: Optional[str] = None
    status: str
    view_count: int = 0
    sentiment_score: int = 0
    fact_check_status: str = "verified"
    credibility_score: int = 88
    sensationalism_score: int = 12
    key_claims: List[Dict[str, Any]] = []
    corroborating_sources: List[str] = []
    bias_spectrum: str = "Neutral Analytic"
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    category: Optional[CategoryOut] = None
    source: Optional[SourceOut] = None


class ArticleListOut(BaseModel):
    articles: List[ArticleOut]
    total: int
    page: int
    limit: int


class FactCheckRequest(BaseModel):
    query: Optional[str] = None
    claim: Optional[str] = None
    query_type: str = "claim"  # "claim" or "url"


class FactCheckResponse(BaseModel):
    verdict: str
    credibility_score: int
    sensationalism_score: int
    analysis: str
    claims_breakdown: List[Dict[str, Any]] = []
    corroborated_sources: List[str] = []
    created_at: Optional[datetime] = None


class BookmarkCreate(BaseModel):
    article_id: int
    folder: str = "default"
    notes: Optional[str] = None


class BookmarkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: str
    article_id: int
    folder: str
    notes: Optional[str] = None
    created_at: datetime
    article: Optional[ArticleOut] = None


class CognitiveDepthResponse(BaseModel):
    radar: Dict[str, Any]
    brief: Dict[str, Any]
    deep: Dict[str, Any]
    eli5: Dict[str, Any]


class ArticleAskRequest(BaseModel):
    question: str
    selected_context: Optional[str] = None


class ArticleAskResponse(BaseModel):
    question: str
    answer: str
    highlighted_claim: Optional[str] = None
    evidence_tag: str
    confidence_score: int


class PerspectivePrismResponse(BaseModel):
    consensus_points: List[str]
    perspectives: List[Dict[str, Any]]
    omission_radar: Dict[str, Any]
    consensus_percentage: int


class PersonalImpactRequest(BaseModel):
    persona: str = "general"  # "consumer", "tech_worker", "investor", "student", "general"


class PersonalImpactResponse(BaseModel):
    persona: str
    impact_level: str
    relevance_score: int
    takeaway: str
    action_item: str
    article_title: str
