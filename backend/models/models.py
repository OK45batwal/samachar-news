import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from ..database import Base


def _utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UserRole(str, enum.Enum):
    USER = "user"
    EDITOR = "editor"
    ADMIN = "admin"


class ArticleStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class FactCheckStatus(str, enum.Enum):
    VERIFIED = "verified"         # Multi-source corroborated fact (85%+ credibility)
    CORROBORATED = "corroborated" # Multiple outlets confirming event (70-84%)
    DEVELOPING = "developing"     # Initial reports, active story (50-69%)
    UNVERIFIED = "unverified"     # Single unconfirmed source or low credibility (<50%)
    DISPUTED = "disputed"         # Conflicting claims / debunked


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)
    full_name = Column(String(255))
    role = Column(SAEnum(UserRole, values_callable=lambda x: [e.value for e in x]), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    preferences = Column(JSON, default=dict)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    icon = Column(String(50))
    created_at = Column(DateTime, default=_utc_now)

    articles = relationship("Article", back_populates="category")


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500))
    feed_url = Column(String(500))
    country = Column(String(100))
    language = Column(String(10), default="en")
    is_active = Column(Boolean, default=True)
    reliability_score = Column(Integer, default=88)  # 0-100 historical credibility
    bias_rating = Column(String(50), default="center")
    etag = Column(String(255), nullable=True)
    last_modified = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=_utc_now)

    articles = relationship("Article", back_populates="source")


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    slug = Column(String(500), unique=True, nullable=False, index=True)
    summary = Column(Text)
    content = Column(Text)
    image_url = Column(String(1000))
    source_url = Column(String(1000), unique=True)
    author = Column(String(255))
    status = Column(SAEnum(ArticleStatus, values_callable=lambda x: [e.value for e in x]), default=ArticleStatus.PUBLISHED, nullable=False)
    view_count = Column(Integer, default=0)
    sentiment_score = Column(Integer, default=0)  # -100 to +100
    
    # Fact Checking & Credibility Engine Metrics
    fact_check_status = Column(
        SAEnum(FactCheckStatus, values_callable=lambda x: [e.value for e in x]),
        default=FactCheckStatus.VERIFIED,
        nullable=False,
    )
    credibility_score = Column(Integer, default=88)      # 0 to 100%
    sensationalism_score = Column(Integer, default=12)   # 0 to 100% (clickbait penalty)
    key_claims = Column(JSON, default=list)              # [{"claim": "...", "status": "verified", "evidence": "..."}]
    corroborating_sources = Column(JSON, default=list)   # ["Reuters", "BBC News", "AP"]
    bias_spectrum = Column(String(50), default="Neutral Analytic")

    category_id = Column(Integer, ForeignKey("categories.id"))
    source_id = Column(Integer, ForeignKey("sources.id"))
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    category = relationship("Category", back_populates="articles")
    source = relationship("Source", back_populates="articles")
    bookmarks = relationship("Bookmark", back_populates="article", cascade="all, delete-orphan")


class FactCheckQuery(Base):
    __tablename__ = "fact_check_queries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_text = Column(Text, nullable=False)
    query_type = Column(String(20), default="claim")  # "claim" or "url"
    verdict = Column(String(50), default="Verified Fact")
    credibility_score = Column(Integer, default=85)
    sensationalism_score = Column(Integer, default=10)
    analysis = Column(Text)
    claims_breakdown = Column(JSON, default=list)
    corroborated_sources = Column(JSON, default=list)
    created_at = Column(DateTime, default=_utc_now)


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    folder = Column(String(100), default="default")
    notes = Column(Text)
    created_at = Column(DateTime, default=_utc_now)

    user = relationship("User", back_populates="bookmarks")
    article = relationship("Article", back_populates="bookmarks")


class RateLimitEntry(Base):
    __tablename__ = "rate_limits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String(20), default="running")
    articles_fetched = Column(Integer, default=0)
    articles_created = Column(Integer, default=0)
    articles_verified = Column(Integer, default=0)
    sources_success = Column(Integer, default=0)
    sources_failed = Column(Integer, default=0)
    errors = Column(JSON, default=list)
    started_at = Column(DateTime, default=_utc_now)
    completed_at = Column(DateTime, nullable=True)
