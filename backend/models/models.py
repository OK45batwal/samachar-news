import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from ..database import Base


class UserRole(str, enum.Enum):
    USER = "user"
    EDITOR = "editor"
    ADMIN = "admin"

class ArticleStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

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
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    icon = Column(String(50))
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    articles = relationship("Article", back_populates="category")

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500))
    feed_url = Column(String(500))
    country = Column(String(100))
    language = Column(String(10))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

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
    status = Column(SAEnum(ArticleStatus, values_callable=lambda x: [e.value for e in x]), default=ArticleStatus.DRAFT, nullable=False)
    view_count = Column(Integer, default=0)
    sentiment_score = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey("categories.id"))
    source_id = Column(Integer, ForeignKey("sources.id"))
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    category = relationship("Category", back_populates="articles")
    source = relationship("Source", back_populates="articles")
    bookmarks = relationship("Bookmark", back_populates="article", cascade="all, delete-orphan")

class RateLimitEntry(Base):
    __tablename__ = "rate_limits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.utcnow(), index=True)

class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String(20), default="running", nullable=False)  # running, completed, failed
    total_feeds = Column(Integer, default=0)
    feeds_succeeded = Column(Integer, default=0)
    feeds_failed = Column(Integer, default=0)
    articles_added = Column(Integer, default=0)
    errors = Column(JSON, default=list)
    started_at = Column(DateTime, default=lambda: datetime.utcnow())
    completed_at = Column(DateTime, nullable=True)

class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    folder = Column(String(100), default="default")
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    user = relationship("User", back_populates="bookmarks")
    article = relationship("Article", back_populates="bookmarks")
