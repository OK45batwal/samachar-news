-- ==============================================================================
-- PRODUCTION-READY POSTGRESQL DATABASE SCHEMA: REAL-TIME NEWS PLATFORM
-- Target: PostgreSQL 14, 15, 16+
-- Optimized for: High-velocity ingestion, sub-millisecond FTS, & high-volume events
-- ==============================================================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- 2. CUSTOM ENUM TYPES
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('reader', 'subscriber', 'moderator', 'editor', 'admin');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE article_status AS ENUM ('draft', 'published', 'archived', 'deleted');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE comment_status AS ENUM ('pending', 'approved', 'flagged', 'rejected');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE reaction_type AS ENUM ('like', 'love', 'insightful', 'disagree');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE fetch_status AS ENUM ('pending', 'success', 'failed', 'duplicate', 'skipped');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;


-- ==============================================================================
-- 3. CORE ENTITIES
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Table 1: NEWS SOURCES
-- Tracks news outlets, wire providers, and RSS/API syndication endpoints
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS news_sources (
    id                  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name                VARCHAR(200) NOT NULL,
    slug                CITEXT NOT NULL UNIQUE,
    website_url         TEXT NOT NULL,
    logo_url            TEXT,
    country             VARCHAR(3) DEFAULT 'GLO' NOT NULL,      -- ISO 3166-1 alpha-3 code
    language            VARCHAR(5) DEFAULT 'en' NOT NULL,       -- ISO 639-1 language code
    api_config          JSONB DEFAULT '{}'::jsonb NOT NULL,     -- Ingestion credentials / rate-limits / endpoints
    rss_feed_url        TEXT,
    reliability_score   SMALLINT DEFAULT 80 NOT NULL CHECK (reliability_score BETWEEN 0 AND 100),
    is_active           BOOLEAN DEFAULT TRUE NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ------------------------------------------------------------------------------
-- Table 2: CATEGORIES
-- Hierarchical news categorization (e.g. World, Technology -> AI)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id                  SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name                VARCHAR(100) NOT NULL,
    slug                CITEXT NOT NULL UNIQUE,
    description         TEXT,
    icon_url            TEXT,
    parent_id           SMALLINT REFERENCES categories(id) ON DELETE SET NULL,
    display_order       SMALLINT DEFAULT 0 NOT NULL,
    is_active           BOOLEAN DEFAULT TRUE NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ------------------------------------------------------------------------------
-- Table 3: TAGS
-- Normalized keywords and topic identifiers
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tags (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name                VARCHAR(80) NOT NULL UNIQUE,
    slug                CITEXT NOT NULL UNIQUE,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ------------------------------------------------------------------------------
-- Table 4: AUTHORS
-- Editorial writers, journalists, columnists, and syndicated wire authors
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS authors (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name                VARCHAR(200) NOT NULL,
    slug                CITEXT NOT NULL UNIQUE,
    email               CITEXT UNIQUE,
    bio                 TEXT,
    profile_image_url   TEXT,
    social_links        JSONB DEFAULT '{}'::jsonb NOT NULL,
    is_active           BOOLEAN DEFAULT TRUE NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ------------------------------------------------------------------------------
-- Table 5: USERS
-- Registered readers, subscribers, and internal platform staff
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    uuid                UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
    name                VARCHAR(150) NOT NULL,
    email               CITEXT NOT NULL UNIQUE,
    password_hash       VARCHAR(255) NOT NULL,
    profile_image_url   TEXT,
    role                user_role DEFAULT 'reader' NOT NULL,
    is_active           BOOLEAN DEFAULT TRUE NOT NULL,
    preferences         JSONB DEFAULT '{"theme": "dark", "verified_only": true}'::jsonb NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_login_at       TIMESTAMPTZ
);

-- ------------------------------------------------------------------------------
-- Table 6: ARTICLES
-- Core journalism entity storing articles, breaking news, full-text vector, and counters
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS articles (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    uuid                UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
    title               VARCHAR(500) NOT NULL,
    slug                CITEXT NOT NULL UNIQUE,
    short_summary       VARCHAR(1200),
    full_content        TEXT NOT NULL,
    featured_image_url  TEXT,
    source_url          TEXT NOT NULL UNIQUE,
    source_id           INT REFERENCES news_sources(id) ON DELETE SET NULL,
    category_id         SMALLINT NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    author_id           BIGINT REFERENCES authors(id) ON DELETE SET NULL,
    language            VARCHAR(10) DEFAULT 'en' NOT NULL,
    country             VARCHAR(3) DEFAULT 'GLO' NOT NULL,
    status              article_status DEFAULT 'draft' NOT NULL,
    is_featured         BOOLEAN DEFAULT FALSE NOT NULL,
    is_breaking         BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Denormalized counter cache (avoid expensive COUNT(*) across millions of rows)
    view_count          BIGINT DEFAULT 0 NOT NULL CHECK (view_count >= 0),
    like_count          INT DEFAULT 0 NOT NULL CHECK (like_count >= 0),
    comment_count       INT DEFAULT 0 NOT NULL CHECK (comment_count >= 0),
    
    -- Timestamps
    published_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at          TIMESTAMPTZ, -- Soft deletion support

    -- Generated PostgreSQL Full-Text Search column with weighted ranking:
    -- 'A' (1.0) = Title, 'B' (0.4) = Summary, 'C' (0.2) = Body Content
    search_vector       tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(short_summary, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(full_content, '')), 'C')
    ) STORED
);

-- ------------------------------------------------------------------------------
-- Table 7: ARTICLE TAGS (Many-to-Many Bridge)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS article_tags (
    article_id          BIGINT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    tag_id              BIGINT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (article_id, tag_id)
);

-- ------------------------------------------------------------------------------
-- Table 8: BOOKMARKS (User Saved Articles)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bookmarks (
    user_id             BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id          BIGINT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (user_id, article_id)
);

-- ------------------------------------------------------------------------------
-- Table 9: COMMENTS (Threaded discussions with self-referential parent)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS comments (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id             BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id          BIGINT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    parent_comment_id   BIGINT REFERENCES comments(id) ON DELETE CASCADE,
    content             TEXT NOT NULL CHECK (length(trim(content)) > 0 AND length(content) <= 3000),
    status              comment_status DEFAULT 'approved' NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at          TIMESTAMPTZ
);

-- ------------------------------------------------------------------------------
-- Table 10: ARTICLE REACTIONS (Likes, Loves, Insights)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS article_reactions (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id             BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id          BIGINT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    reaction_type       reaction_type DEFAULT 'like' NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE (user_id, article_id)
);

-- ------------------------------------------------------------------------------
-- Table 11: ARTICLE VIEWS (High-Velocity Partitioned Analytics Table)
-- Partitioned by month on viewed_at to easily manage hundreds of millions of events
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS article_views (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY,
    article_id          BIGINT NOT NULL,
    user_id             BIGINT,
    ip_hash             VARCHAR(64) NOT NULL,
    device_category     VARCHAR(20) DEFAULT 'desktop',
    referer_host        VARCHAR(255),
    viewed_at           TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (id, viewed_at)
) PARTITION BY RANGE (viewed_at);

-- Initial monthly partitions for operational continuity
CREATE TABLE IF NOT EXISTS article_views_2026_08 PARTITION OF article_views
    FOR VALUES FROM ('2026-08-01 00:00:00+00') TO ('2026-09-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS article_views_2026_09 PARTITION OF article_views
    FOR VALUES FROM ('2026-09-01 00:00:00+00') TO ('2026-10-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS article_views_2026_10 PARTITION OF article_views
    FOR VALUES FROM ('2026-10-01 00:00:00+00') TO ('2026-11-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS article_views_default PARTITION OF article_views DEFAULT;


-- ------------------------------------------------------------------------------
-- Table 12: NEWS INGESTION BATCH LOG
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS news_ingestion_log (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id           INT NOT NULL REFERENCES news_sources(id) ON DELETE CASCADE,
    batch_id            UUID NOT NULL,
    fetch_status        fetch_status DEFAULT 'pending' NOT NULL,
    items_fetched       INT DEFAULT 0 NOT NULL,
    items_created       INT DEFAULT 0 NOT NULL,
    items_duplicate     INT DEFAULT 0 NOT NULL,
    items_failed        INT DEFAULT 0 NOT NULL,
    error_log           JSONB DEFAULT '[]'::jsonb NOT NULL,
    started_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at        TIMESTAMPTZ
);

-- ------------------------------------------------------------------------------
-- Table 13: NEWS INGESTION ITEMS (Per-item Dedup & Content Fingerprint Engine)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS news_ingestion_items (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ingestion_run_id    BIGINT REFERENCES news_ingestion_log(id) ON DELETE CASCADE,
    source_id           INT NOT NULL REFERENCES news_sources(id) ON DELETE CASCADE,
    external_article_id VARCHAR(255),
    source_url          TEXT NOT NULL,
    source_url_hash     VARCHAR(64) NOT NULL, -- SHA-256 of canonicalized URL
    content_hash        VARCHAR(64) NOT NULL, -- SHA-256 of stripped body text
    fetch_status        fetch_status DEFAULT 'success' NOT NULL,
    article_id          BIGINT REFERENCES articles(id) ON DELETE SET NULL,
    error_message       TEXT,
    first_fetched_at    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_fetched_at     TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Deduplication Rule 1: No duplicate stories from same source feed ID
    CONSTRAINT uq_source_external_id UNIQUE (source_id, external_article_id)
);


-- ==============================================================================
-- 4. HIGH-PERFORMANCE PRODUCTION INDEXES
-- ==============================================================================

-- Articles: Full-Text Search GIN Index (Weighted title, summary, content)
CREATE INDEX IF NOT EXISTS idx_articles_search_vector 
    ON articles USING GIN(search_vector);

-- Articles: Latest News Feed (Partial index for published stories only)
CREATE INDEX IF NOT EXISTS idx_articles_published_latest 
    ON articles (published_at DESC, id DESC) 
    WHERE status = 'published' AND deleted_at IS NULL;

-- Articles: Breaking News Alerts (Partial index for instant retrieval)
CREATE INDEX IF NOT EXISTS idx_articles_breaking 
    ON articles (published_at DESC) 
    WHERE is_breaking = TRUE AND status = 'published' AND deleted_at IS NULL;

-- Articles: Hero / Featured Stories
CREATE INDEX IF NOT EXISTS idx_articles_featured 
    ON articles (published_at DESC) 
    WHERE is_featured = TRUE AND status = 'published' AND deleted_at IS NULL;

-- Articles: Category Pages with Keyset Cursor Pagination
CREATE INDEX IF NOT EXISTS idx_articles_category_published 
    ON articles (category_id, published_at DESC, id DESC) 
    WHERE status = 'published' AND deleted_at IS NULL;

-- Articles: Source Listing Pages
CREATE INDEX IF NOT EXISTS idx_articles_source_published 
    ON articles (source_id, published_at DESC) 
    WHERE status = 'published' AND deleted_at IS NULL;

-- Articles: Author Portfolio Pages
CREATE INDEX IF NOT EXISTS idx_articles_author_published 
    ON articles (author_id, published_at DESC) 
    WHERE status = 'published' AND deleted_at IS NULL;

-- Articles: Trending Stories (combining view_count and published_at)
CREATE INDEX IF NOT EXISTS idx_articles_trending 
    ON articles (view_count DESC, published_at DESC) 
    WHERE status = 'published' AND deleted_at IS NULL;

-- Articles: Fuzzy Title Matching via Trigrams (autocomplete & typos)
CREATE INDEX IF NOT EXISTS idx_articles_title_trgm 
    ON articles USING GIN (title gin_trgm_ops);

-- Article Tags: Reverse Lookup (Find all articles for a tag)
CREATE INDEX IF NOT EXISTS idx_article_tags_tag_id 
    ON article_tags (tag_id, article_id);

-- Comments: Fast thread retrieval by article and parent hierarchy
CREATE INDEX IF NOT EXISTS idx_comments_article_parent 
    ON comments (article_id, parent_comment_id, created_at ASC) 
    WHERE status = 'approved' AND deleted_at IS NULL;

-- Bookmarks: Reverse user lookup (Find all articles bookmarked by user)
CREATE INDEX IF NOT EXISTS idx_bookmarks_user_date 
    ON bookmarks (user_id, created_at DESC);

-- Article Views: Partition index on (article_id, viewed_at)
CREATE INDEX IF NOT EXISTS idx_article_views_article_date 
    ON article_views (article_id, viewed_at DESC);

-- News Ingestion: Global content fingerprint deduplication
CREATE INDEX IF NOT EXISTS idx_ingestion_content_hash 
    ON news_ingestion_items (content_hash);

-- News Ingestion: Normalized URL hash lookup
CREATE INDEX IF NOT EXISTS idx_ingestion_url_hash 
    ON news_ingestion_items (source_url_hash);
