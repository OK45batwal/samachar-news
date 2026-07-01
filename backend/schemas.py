from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    description: str | None = None
    icon: str | None = None


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    url: str | None = None
    country: str | None = None
    language: str | None = None


class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    slug: str
    summary: str | None = None
    content: str | None = None
    image_url: str | None = None
    source_url: str | None = None
    author: str | None = None
    status: str
    view_count: int | None = 0
    sentiment_score: int | None = 0
    category: CategoryOut | None = None
    source: SourceOut | None = None
    published_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ArticleListOut(BaseModel):
    articles: list[ArticleOut]
    total: int
    page: int
    limit: int
