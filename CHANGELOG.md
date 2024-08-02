# Changelog

All notable changes to **Samachar News** will be documented in this file.

## [2.0.0] - 2024-08-02

### Added
- **AI Sentiment Processor Module**: Real-time lexical sentiment scoring (-100 to +100), key takeaway extraction, and topic keyword tagging.
- **SQLite WAL Mode Listener**: Enabled WAL journal mode pragma to prevent database lock contention under concurrent async requests.
- **Conditional RSS Ingestion**: `If-None-Match` (ETag) and `If-Modified-Since` HTTP headers support to minimize bandwidth and redundant XML parsing.
- **DhanuAI Intelligence Hub (`ai.html`)**: Real-time sentiment distribution gauges, geopolitical risk index, and interactive AI news assistant.
- **Video Bulletins Feed (`videos.html`)**: Video news player gallery with duration timestamps and category filters.
- **Admin Dashboard (`admin.html`)**: On-demand real-time RSS ingestion trigger and article management dashboard.

### Fixed
- Multi-term search query filtering across title, summary, and author.
- Safeguarded Vite buildInput entry resolution in `vite.config.js`.
