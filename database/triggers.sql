-- ==============================================================================
-- POSTGRESQL TRIGGERS & PROCEDURES: AUTOMATION & COUNTER CACHING
-- ==============================================================================

-- 1. AUTOMATED updated_at TRIGGER FUNCTION
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach updated_at triggers to all mutable tables
DROP TRIGGER IF EXISTS set_timestamp_news_sources ON news_sources;
CREATE TRIGGER set_timestamp_news_sources
    BEFORE UPDATE ON news_sources
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();

DROP TRIGGER IF EXISTS set_timestamp_categories ON categories;
CREATE TRIGGER set_timestamp_categories
    BEFORE UPDATE ON categories
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();

DROP TRIGGER IF EXISTS set_timestamp_authors ON authors;
CREATE TRIGGER set_timestamp_authors
    BEFORE UPDATE ON authors
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();

DROP TRIGGER IF EXISTS set_timestamp_users ON users;
CREATE TRIGGER set_timestamp_users
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();

DROP TRIGGER IF EXISTS set_timestamp_articles ON articles;
CREATE TRIGGER set_timestamp_articles
    BEFORE UPDATE ON articles
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();

DROP TRIGGER IF EXISTS set_timestamp_comments ON comments;
CREATE TRIGGER set_timestamp_comments
    BEFORE UPDATE ON comments
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();


-- ------------------------------------------------------------------------------
-- 2. DENORMALIZED LIKE/REACTION COUNTER CACHE TRIGGER
-- Automatically increments/decrements articles.like_count in real-time
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trigger_article_reaction_counter()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE articles 
        SET like_count = like_count + 1 
        WHERE id = NEW.article_id;
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE articles 
        SET like_count = GREATEST(0, like_count - 1) 
        WHERE id = OLD.article_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS maintain_article_like_count ON article_reactions;
CREATE TRIGGER maintain_article_like_count
    AFTER INSERT OR DELETE ON article_reactions
    FOR EACH ROW
    EXECUTE FUNCTION trigger_article_reaction_counter();


-- ------------------------------------------------------------------------------
-- 3. DENORMALIZED COMMENT COUNTER CACHE TRIGGER
-- Adjusts articles.comment_count when comments are added, approved, or soft-deleted
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trigger_article_comment_counter()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        IF (NEW.status = 'approved' AND NEW.deleted_at IS NULL) THEN
            UPDATE articles SET comment_count = comment_count + 1 WHERE id = NEW.article_id;
        END IF;
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        -- From approved to unapproved/soft-deleted
        IF ((OLD.status = 'approved' AND OLD.deleted_at IS NULL) AND 
            (NEW.status != 'approved' OR NEW.deleted_at IS NOT NULL)) THEN
            UPDATE articles SET comment_count = GREATEST(0, comment_count - 1) WHERE id = NEW.article_id;
        -- From unapproved to approved
        ELSIF ((OLD.status != 'approved' OR OLD.deleted_at IS NOT NULL) AND 
               (NEW.status = 'approved' AND NEW.deleted_at IS NULL)) THEN
            UPDATE articles SET comment_count = comment_count + 1 WHERE id = NEW.article_id;
        END IF;
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        IF (OLD.status = 'approved' AND OLD.deleted_at IS NULL) THEN
            UPDATE articles SET comment_count = GREATEST(0, comment_count - 1) WHERE id = OLD.article_id;
        END IF;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS maintain_article_comment_count ON comments;
CREATE TRIGGER maintain_article_comment_count
    AFTER INSERT OR UPDATE OR DELETE ON comments
    FOR EACH ROW
    EXECUTE FUNCTION trigger_article_comment_counter();


-- ------------------------------------------------------------------------------
-- 4. BATCH VIEW SYNCHRONIZATION PROCEDURE
-- Efficiently synchronizes high-throughput raw article_views buffer to articles.view_count
-- Designed to be run via pg_cron or worker every 60 seconds
-- ------------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sync_article_view_counts(lookback_interval INTERVAL DEFAULT INTERVAL '5 minutes')
LANGUAGE plpgsql
AS $$
BEGIN
    WITH recent_views AS (
        SELECT 
            article_id,
            COUNT(*) AS recent_count
        FROM article_views
        WHERE viewed_at >= CURRENT_TIMESTAMP - lookback_interval
        GROUP BY article_id
    )
    UPDATE articles a
    SET view_count = a.view_count + rv.recent_count
    FROM recent_views rv
    WHERE a.id = rv.article_id;
END;
$$;
