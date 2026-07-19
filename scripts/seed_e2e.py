"""Seed demo articles — delegates to backend/seed_e2e_inline.py."""
import asyncio
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.seed_e2e_inline import seed_demo_articles

if __name__ == "__main__":
    asyncio.run(seed_demo_articles())
