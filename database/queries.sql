-- ==============================================================================
-- PRODUCTION-READY OPTIMIZED SQL QUERIES FOR REAL-TIME NEWS PLATFORM
-- All queries leverage composite, partial, and GIN indexes for zero sequential scans
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. LATEST NEWS FEED (Cursor / Keyset Pagination)
-- Avoids expensive OFFSET by querying on (published_at, id) tuple
-- Uses index: idx_articles_published_latest
-- ------------------------------------------------------------------------------
-- Initial Page Request:
SELECT 
    a.id,
    a.uuid,
    a.title,
    a.slug,
    a.short_summary,
    a.featured_image_url,
    a.published_at,
    a.view_count,
    a.like_count,
    a.comment_count,
    c.name AS category_name,
    c.slug AS category_slug,
    s.name AS source_name,
    s.logo_url AS source_logo_url,
    ath.name AS author_name
FROM articles a
JOIN categories c ON c.id = a.category_id
LEFT JOIN news_sources s ON s.id = a.source_id
LEFT JOIN authors ath ON ath.id = a.author_id
WHERE a.status = 'published' 
  AND a.deleted_at IS NULL
ORDER BY a.published_at DESC, a.id DESC
LIMIT 20;

-- Subsequent Keyset Cursor Page Request (pass $last_published_at and $last_id):
-- SELECT a.id, a.title, ...
-- WHERE a.status = 'published' AND a.deleted_at IS NULL
--   AND (a.published_at, a.id) < ($last_published_at, $last_id)
-- ORDER BY a.published_at DESC, a.id DESC
-- LIMIT 20;


-- ------------------------------------------------------------------------------
-- 2. BREAKING NEWS ALERTS & TICKER
-- Instant retrieval of top active breaking stories
-- Uses index: idx_articles_breaking
-- ------------------------------------------------------------------------------
SELECT 
    a.id,
    a.uuid,
    a.title,
    a.slug,
    a.short_summary,
    a.published_at,
    c.name AS category_name,
    s.name AS source_name
FROM articles a
JOIN categories c ON c.id = a.category_id
LEFT JOIN news_sources s ON s.id = a.source_id
WHERE a.is_breaking = TRUE 
  AND a.status = 'published' 
  AND a.deleted_at IS NULL
  AND a.published_at >= CURRENT_TIMESTAMP - INTERVAL '12 hours'
ORDER BY a.published_at DESC
LIMIT 5;


-- ------------------------------------------------------------------------------
-- 3. TRENDING NEWS (Time-Decayed Popularity Algorithm)
-- Calculates dynamic trending score: (Views + 5*Likes + 10*Comments) / (Age in Hours + 2)^1.5
-- Uses index: idx_articles_trending
-- ------------------------------------------------------------------------------
SELECT 
    a.id,
    a.uuid,
    a.title,
    a.slug,
    a.short_summary,
    a.featured_image_url,
    a.published_at,
    a.view_count,
    a.like_count,
    a.comment_count,
    c.name AS category_name,
    c.slug AS category_slug,
    s.name AS source_name,
    (
        (a.view_count + (a.like_count * 5) + (a.comment_count * 10))::float / 
        POWER(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - a.published_at)) / 3600.0 + 2.0, 1.5)
    ) AS trending_score
FROM articles a
JOIN categories c ON c.id = a.category_id
LEFT JOIN news_sources s ON s.id = a.source_id
WHERE a.status = 'published' 
  AND a.deleted_at IS NULL
  AND a.published_at >= CURRENT_TIMESTAMP - INTERVAL '48 hours'
ORDER BY trending_score DESC, a.published_at DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- 4. CATEGORY NEWS LISTING WITH CURSOR PAGINATION
-- Uses index: idx_articles_category_published
-- ------------------------------------------------------------------------------
SELECT 
    a.id,
    a.uuid,
    a.title,
    a.slug,
    a.short_summary,
    a.featured_image_url,
    a.published_at,
    a.view_count,
    s.name AS source_name,
    ath.name AS author_name
FROM articles a
JOIN categories c ON c.id = a.category_id
LEFT JOIN news_sources s ON s.id = a.source_id
LEFT JOIN authors ath ON ath.id = a.author_id
WHERE a.category_id = :target_category_id
  AND a.status = 'published'
  AND a.deleted_at IS NULL
ORDER BY a.published_at DESC, a.id DESC
LIMIT 20;


-- ------------------------------------------------------------------------------
-- 5. NEWS BY SOURCE (Syndication Feed Overview)
-- Uses index: idx_articles_source_published
-- ------------------------------------------------------------------------------
SELECT 
    a.id,
    a.title,
    a.slug,
    a.short_summary,
    a.published_at,
    a.view_count,
    c.name AS category_name
FROM articles a
JOIN categories c ON c.id = a.category_id
WHERE a.source_id = :target_source_id
  AND a.status = 'published'
  AND a.deleted_at IS NULL
ORDER BY a.published_at DESC
LIMIT 25;


-- ------------------------------------------------------------------------------
-- 6. FULL-TEXT SEARCH WITH WEBSPAN HIGHLIGHTING & RELEVANCE RANKING
-- Supports natural phrases, AND/OR, and quotes via websearch_to_tsquery
-- Uses index: idx_articles_search_vector (GIN)
-- ------------------------------------------------------------------------------
SELECT 
    a.id,
    a.uuid,
    a.title,
    a.slug,
    ts_headline(
        'english', 
        a.full_content, 
        websearch_to_tsquery('english', :user_query), 
        'StartSel=<mark class="highlight">, StopSel=</mark>, MaxWords=35, MinWords=15'
    ) AS highlighted_snippet,
    a.featured_image_url,
    a.published_at,
    c.name AS category_name,
    s.name AS source_name,
    ts_rank_cd(a.search_vector, websearch_to_tsquery('english', :user_query), 32) AS relevance_rank
FROM articles a
JOIN categories c ON c.id = a.category_id
LEFT JOIN news_sources s ON s.id = a.source_id
WHERE a.search_vector @@ websearch_to_tsquery('english', :user_query)
  AND a.status = 'published'
  AND a.deleted_at IS NULL
ORDER BY relevance_rank DESC, a.published_at DESC
LIMIT 20;


-- ------------------------------------------------------------------------------
-- 7. RELATED ARTICLES (Shared Tags Jaccard Overlap)
-- Given an article ID, finds published stories sharing the highest number of tags
-- Uses indexes: idx_article_tags_tag_id & idx_articles_published_latest
-- ------------------------------------------------------------------------------
WITH current_tags AS (
    SELECT tag_id 
    FROM article_tags 
    WHERE article_id = :current_article_id
)
SELECT 
    a.id,
    a.uuid,
    a.title,
    a.slug,
    a.featured_image_url,
    a.published_at,
    c.name AS category_name,
    COUNT(at.tag_id) AS shared_tags_count
FROM articles a
JOIN article_tags at ON at.article_id = a.id
JOIN current_tags ct ON ct.tag_id = at.tag_id
JOIN categories c ON c.id = a.category_id
WHERE a.id != :current_article_id
  AND a.status = 'published'
  AND a.deleted_at IS NULL
GROUP BY a.id, a.uuid, a.title, a.slug, a.featured_image_url, a.published_at, c.name
ORDER BY shared_tags_count DESC, a.published_at DESC
LIMIT 4;


-- ------------------------------------------------------------------------------
-- 8. MOST VIEWED ARTICLES IN PAST 24 HOURS (From Partitioned Views Table)
-- Aggregates raw view log events in the active monthly partition
-- Uses index: idx_article_views_article_date
-- ------------------------------------------------------------------------------
SELECT 
    a.id,
    a.uuid,
    a.title,
    a.slug,
    a.featured_image_url,
    a.published_at,
    c.name AS category_name,
    COUNT(v.id) AS views_last_24h
FROM article_views v
JOIN articles a ON a.id = v.article_id
JOIN categories c ON c.id = a.category_id
WHERE v.viewed_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
  AND a.status = 'published'
  AND a.deleted_at IS NULL
GROUP BY a.id, a.uuid, a.title, a.slug, a.featured_image_url, a.published_at, c.name
ORDER BY views_last_24h DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- 9. USER BOOKMARKED ARTICLES
-- Retrieves all saved stories for a specific reader with reverse index
-- Uses index: idx_bookmarks_user_date
-- ------------------------------------------------------------------------------
SELECT 
    a.id,
    a.uuid,
    a.title,
    a.slug,
    a.short_summary,
    a.featured_image_url,
    a.published_at,
    b.created_at AS bookmarked_at,
    c.name AS category_name,
    s.name AS source_name
FROM bookmarks b
JOIN articles a ON a.id = b.article_id
JOIN categories c ON c.id = a.category_id
LEFT JOIN news_sources s ON s.id = a.source_id
WHERE b.user_id = :authenticated_user_id
  AND a.status = 'published'
  AND a.deleted_at IS NULL
ORDER BY b.created_at DESC
LIMIT 50;


-- ------------------------------------------------------------------------------
-- 10. THREADED COMMENT TREE (Recursive CTE for Nested Replies)
-- Loads all approved parent comments and their nested replies in chronological order
-- Uses index: idx_comments_article_parent
-- ------------------------------------------------------------------------------
WITH RECURSIVE comment_tree AS (
    -- Anchor member: root comments (no parent)
    SELECT 
        c.id,
        c.article_id,
        c.parent_comment_id,
        c.content,
        c.created_at,
        u.name AS author_name,
        u.profile_image_url AS author_avatar,
        1 AS depth,
        ARRAY[c.id] AS path
    FROM comments c
    JOIN users u ON u.id = c.user_id
    WHERE c.article_id = :target_article_id
      AND c.parent_comment_id IS NULL
      AND c.status = 'approved'
      AND c.deleted_at IS NULL

    UNION ALL

    -- Recursive member: replies
    SELECT 
        child.id,
        child.article_id,
        child.parent_comment_id,
        child.content,
        child.created_at,
        u.name AS author_name,
        u.profile_image_url AS author_avatar,
        parent.depth + 1,
        parent.path || child.id
    FROM comments child
    JOIN comment_tree parent ON parent.id = child.parent_comment_id
    JOIN users u ON u.id = child.user_id
    WHERE child.status = 'approved'
      AND child.deleted_at IS NULL
)
SELECT * 
FROM comment_tree 
ORDER BY path;
