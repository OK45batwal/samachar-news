"""Test utility functions."""
from backend.utils.utils import slugify, truncate_text


def test_slugify():
    assert slugify("Hello World") == "hello-world"
    assert slugify("  AI & Machine Learning!  ") == "ai-machine-learning"
    assert slugify("Special___Chars!!!") == "special-chars"


def test_truncate_text():
    text = "This is a long text that should be truncated"
    result = truncate_text(text, 20)
    assert len(result) <= 23  # 20 + "..."
    assert result.endswith("...")

    short = "Short"
    assert truncate_text(short, 20) == "Short"
