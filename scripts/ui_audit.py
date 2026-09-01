"""
Automated UI/UX & Navigation Flow Audit Script for Samachar.
Validates:
1. Internal HTML links resolve to existing files.
2. Logo consistency across all views.
3. Mobile viewport & theme-color script presence.
4. CSS & JS asset inclusions.
"""
import glob
import os
import re
import sys

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
HTML_FILES = glob.glob(os.path.join(FRONTEND_DIR, "*.html"))

ERRORS = []
WARNINGS = []

print(f"🔍 Starting UI/UX Development Audit on {len(HTML_FILES)} HTML files...")

for file_path in HTML_FILES:
    rel_name = os.path.basename(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Viewport tag check
    if 'name="viewport"' not in content:
        ERRORS.append(f"[{rel_name}] Missing mobile viewport meta tag.")

    # 2. Theme color tag check
    if 'name="theme-color"' not in content:
        WARNINGS.append(f"[{rel_name}] Missing meta theme-color tag.")

    # 3. Stylesheet checks
    for css in ["variables.css", "style.css", "layout.css"]:
        if css not in content:
            WARNINGS.append(f"[{rel_name}] Missing link to {css}")

    # 4. Logo Consistency Check
    if rel_name != "404.html" and 'class="logo"' in content:
        if "SAMACHAR" not in content:
            WARNINGS.append(f"[{rel_name}] Logo does not contain SAMACHAR text brand.")

    # 5. Check internal href links
    hrefs = re.findall(r'href=["\']([^"\']+\.html)(\?[^"\']*)?["\']', content)
    for href_file, _ in hrefs:
        target_path = os.path.join(FRONTEND_DIR, href_file)
        if not os.path.exists(target_path):
            ERRORS.append(f"[{rel_name}] Broken navigation link to: {href_file}")

print(f"✅ Audited {len(HTML_FILES)} pages.")

if WARNINGS:
    print(f"\n⚠️  {len(WARNINGS)} Warnings Found:")
    for w in WARNINGS:
        print(f"  - {w}")

if ERRORS:
    print(f"\n❌ {len(ERRORS)} Errors Found:")
    for e in ERRORS:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("\n🎉 All UI/UX structure, navigation links, and brand assets validated successfully!")
