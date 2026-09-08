-- ==============================================================================
-- SAMPLE SEED DATASET FOR TESTING & VERIFICATION
-- ==============================================================================

-- 1. SEED NEWS SOURCES
INSERT INTO news_sources (name, slug, website_url, logo_url, country, language, reliability_score, is_active)
VALUES 
('Global Wire Service', 'global-wire-service', 'https://wireservice.org', 'https://wireservice.org/logo.png', 'GLO', 'en', 95, true),
('Associated Press News', 'associated-press', 'https://apnews.com', 'https://apnews.com/logo.png', 'USA', 'en', 98, true),
('Press Trust of India', 'press-trust-india', 'https://ptinews.com', 'https://ptinews.com/logo.png', 'IND', 'en', 94, true),
('BBC World Intelligence', 'bbc-world', 'https://bbc.com/news', 'https://bbc.com/logo.png', 'GBR', 'en', 96, true),
('TechCrunch Network', 'techcrunch-network', 'https://techcrunch.com', 'https://techcrunch.com/logo.png', 'USA', 'en', 88, true)
ON CONFLICT (slug) DO NOTHING;

-- 2. SEED CATEGORIES
INSERT INTO categories (name, slug, description, display_order, is_active)
VALUES 
('World News', 'world', 'Geopolitics, diplomacy, international summits, and global security.', 1, true),
('Technology & AI', 'technology', 'Autonomous systems, artificial intelligence, semiconductors, and cybersecurity.', 2, true),
('Business & Economy', 'business', 'Financial markets, trade corridors, macroeconomics, and central bank policies.', 3, true),
('Science & Space', 'science', 'Astrophysics, clean energy innovations, quantum mechanics, and deep space exploration.', 4, true),
('Climate & Environment', 'climate', 'Renewable energy transition, climate diplomacy, and biodiversity conservation.', 5, true)
ON CONFLICT (slug) DO NOTHING;

-- 3. SEED TAGS
INSERT INTO tags (name, slug)
VALUES 
('Artificial Intelligence', 'artificial-intelligence'),
('Quantum Computing', 'quantum-computing'),
('Central Banks', 'central-banks'),
('Renewable Energy', 'renewable-energy'),
('Space Exploration', 'space-exploration'),
('Cybersecurity', 'cybersecurity')
ON CONFLICT (slug) DO NOTHING;

-- 4. SEED AUTHORS
INSERT INTO authors (name, slug, email, bio, is_active)
VALUES 
('Elena Rostova', 'elena-rostova', 'elena.rostova@samachar.news', 'Senior investigative journalist specializing in European defense and transatlantic security.', true),
('Dr. Vikramaditya Sen', 'vikramaditya-sen', 'vikram.sen@samachar.news', 'Technology editor, AI researcher, and author on cognitive computing ethics.', true),
('Sarah Jenkins', 'sarah-jenkins', 'sarah.jenkins@samachar.news', 'Global economics correspondent focusing on sovereign debt markets and energy finance.', true)
ON CONFLICT (slug) DO NOTHING;

-- 5. SEED USERS
INSERT INTO users (name, email, password_hash, role, is_active)
VALUES 
('Arjun Mehta', 'arjun.mehta@example.com', '$2b$12$KIXe2vK8dM.sB35T7d1zReW9h.oWvU4b6zYn9F2zH0t6t.5qQ2Z2W', 'admin', true),
('Devin Clark', 'devin.clark@example.com', '$2b$12$KIXe2vK8dM.sB35T7d1zReW9h.oWvU4b6zYn9F2zH0t6t.5qQ2Z2W', 'subscriber', true),
('Priya Sharma', 'priya.sharma@example.com', '$2b$12$KIXe2vK8dM.sB35T7d1zReW9h.oWvU4b6zYn9F2zH0t6t.5qQ2Z2W', 'reader', true)
ON CONFLICT (email) DO NOTHING;

-- 6. SEED ARTICLES
INSERT INTO articles (
    title, slug, short_summary, full_content, featured_image_url, source_url, 
    source_id, category_id, author_id, status, is_featured, is_breaking, 
    view_count, published_at
)
VALUES 
(
    'Global Central Banks Announce Unified Settlement Framework for Cross-Border Liquidity',
    'global-central-banks-announce-unified-settlement-framework',
    'Ten major central banks have reached a landmark multilateral accord to establish instant cryptographic sovereign settlement channels, aiming to reduce bilateral friction.',
    'In a joint summit communique released this morning, monetary authorities from eleven sovereign economies outlined the technical specifications for an interoperable wholesale liquidity network. The framework leverages distributed ledger consensus with zero-knowledge cryptographic verification to provide 24/7 continuous settlement while preserving sovereign monetary discretion.',
    'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200',
    'https://wireservice.org/economy/unified-settlement-accord-2026',
    1, 3, 3, 'published', true, true, 1420, CURRENT_TIMESTAMP - INTERVAL '2 hours'
),
(
    'Next-Generation Superconducting Qubits Achieve 99.9% Quantum Gate Fidelity at Room Temperature',
    'superconducting-qubits-achieve-gate-fidelity-milestone',
    'Researchers demonstrate fault-tolerant topological quantum error correction without cryogenic cooling requirements, marking a pivotal commercial inflection point.',
    'A collaborative consortium of international physicists and material engineers has published experimental verification of stable topological coherence in synthetic kagome superlattices. By stabilizing majorana zero modes at ambient pressure, the prototype processor maintained coherence over three orders of magnitude longer than conventional transmon architectures.',
    'https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=1200',
    'https://techcrunch.com/quantum/superconducting-qubits-99-percent',
    5, 2, 2, 'published', true, false, 3890, CURRENT_TIMESTAMP - INTERVAL '5 hours'
),
(
    'International Renewable Energy Pact Deploys Gigawatt-Scale Ocean Current Turbine Array',
    'international-renewable-energy-pact-ocean-turbines',
    'Deep-sea kinetic harvesting units begin generating continuous baseload power along the North Atlantic conveyor belt, supplying resilient energy to coastal grids.',
    'Marine engineering teams completed the installation of the third subsea tidal generator cluster today. Unlike solar and terrestrial wind, deep underwater ocean currents maintain continuous hydrokinetic flow rates year-round, delivering uninterruptible baseload power directly into regional high-voltage direct current lines.',
    'https://images.unsplash.com/photo-1466611653911-95081537e5b7?w=1200',
    'https://wireservice.org/energy/ocean-current-turbine-deployment',
    1, 5, 1, 'published', false, false, 820, CURRENT_TIMESTAMP - INTERVAL '1 day'
)
ON CONFLICT (slug) DO NOTHING;

-- 7. SEED ARTICLE TAGS
INSERT INTO article_tags (article_id, tag_id)
SELECT a.id, t.id 
FROM articles a, tags t 
WHERE a.slug = 'global-central-banks-announce-unified-settlement-framework' 
  AND t.slug IN ('central-banks', 'artificial-intelligence')
ON CONFLICT DO NOTHING;

INSERT INTO article_tags (article_id, tag_id)
SELECT a.id, t.id 
FROM articles a, tags t 
WHERE a.slug = 'superconducting-qubits-achieve-gate-fidelity-milestone' 
  AND t.slug IN ('quantum-computing', 'artificial-intelligence')
ON CONFLICT DO NOTHING;

-- 8. SEED BOOKMARKS
INSERT INTO bookmarks (user_id, article_id)
SELECT u.id, a.id 
FROM users u, articles a 
WHERE u.email = 'devin.clark@example.com' 
  AND a.slug = 'superconducting-qubits-achieve-gate-fidelity-milestone'
ON CONFLICT DO NOTHING;

-- 9. SEED COMMENTS (Including Threaded Child Comment)
INSERT INTO comments (user_id, article_id, parent_comment_id, content, status)
SELECT u.id, a.id, NULL, 'The zero-knowledge settlement protocol architecture solves the counterparty risk problem cleanly without creating a centralized single point of failure.', 'approved'
FROM users u, articles a 
WHERE u.email = 'devin.clark@example.com' 
  AND a.slug = 'global-central-banks-announce-unified-settlement-framework';

-- Reply to the comment above
INSERT INTO comments (user_id, article_id, parent_comment_id, content, status)
SELECT u.id, a.id, c.id, 'Agreed, particularly because capital controls can remain enforced locally at the participant bank edge node.', 'approved'
FROM users u, articles a, comments c
WHERE u.email = 'priya.sharma@example.com' 
  AND a.slug = 'global-central-banks-announce-unified-settlement-framework'
  AND c.parent_comment_id IS NULL
LIMIT 1;

-- 10. SEED ARTICLE REACTIONS
INSERT INTO article_reactions (user_id, article_id, reaction_type)
SELECT u.id, a.id, 'insightful'
FROM users u, articles a 
WHERE u.email = 'devin.clark@example.com' 
  AND a.slug = 'superconducting-qubits-achieve-gate-fidelity-milestone'
ON CONFLICT (user_id, article_id) DO NOTHING;

-- 11. SEED ARTICLE VIEWS (Partitioned)
INSERT INTO article_views (article_id, user_id, ip_hash, device_category, viewed_at)
SELECT a.id, u.id, 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'mobile', CURRENT_TIMESTAMP - INTERVAL '30 minutes'
FROM articles a, users u 
WHERE a.slug = 'superconducting-qubits-achieve-gate-fidelity-milestone' 
  AND u.email = 'devin.clark@example.com';

-- 12. SEED INGESTION LOG & ITEMS
INSERT INTO news_ingestion_log (source_id, batch_id, fetch_status, items_fetched, items_created, items_duplicate)
VALUES (1, gen_random_uuid(), 'success', 25, 1, 24);

INSERT INTO news_ingestion_items (
    ingestion_run_id, source_id, external_article_id, source_url, 
    source_url_hash, content_hash, fetch_status
)
VALUES (
    1, 1, 'wire-item-88912',
    'https://wireservice.org/economy/unified-settlement-accord-2026',
    encode(sha256('https://wireservice.org/economy/unified-settlement-accord-2026'::bytea), 'hex'),
    encode(sha256('Ten major central banks have reached a landmark multilateral accord'::bytea), 'hex'),
    'success'
)
ON CONFLICT (source_id, external_article_id) DO NOTHING;
