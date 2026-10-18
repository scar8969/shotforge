"""B9 shotapi — tests. Run: pytest test_shotforge.py"""

flask_ok = True
try:
    import flask_sqlalchemy
except ImportError:
    flask_ok = False


def test_cache_key_deterministic():
    from shotapi.shot.cache import cache_key

    a = cache_key("https://x.com", "png", (1280, 800), True)
    b = cache_key("https://x.com", "png", (1280, 800), True)
    assert a == b
    assert a != cache_key("https://x.com", "png", (1280, 800), False)


def test_cache_miss(tmp_path):
    from shotapi.shot.cache import get

    assert get("nonexistent") is None
