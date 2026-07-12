"""Feed parsing utilities for RSS and Atom feeds."""
import re


def extract_image_fallback(entry: dict) -> str:
    """Extract the best image URL from an RSS entry using multiple fallback strategies."""
    # 1. media:content (url attribute)
    for m in (entry.get("media_content") or []):
        url = m.get("url", "")
        if url.startswith("http"):
            return url

    # 2. media:thumbnail (url attribute)
    for m in (entry.get("media_thumbnail") or []):
        url = m.get("url", "")
        if url.startswith("http"):
            return url

    # 3. enclosures (href attribute)
    for m in (entry.get("enclosures") or []):
        url = m.get("href", "")
        if url.startswith("http"):
            ct = (m.get("type") or "").lower()
            if not ct or ct.startswith("image"):
                return url

    # 4. Extract first <img src> from HTML content
    content_html = ""
    if entry.get("content"):
        content_html = entry["content"][0].get("value", "")
    if not content_html:
        content_html = entry.get("summary", "")
    if content_html:
        m = re.search(r'<img[^>]+src=["\'](https?://[^"\']+)["\']', content_html)
        if m:
            return m.group(1)

    return ""
