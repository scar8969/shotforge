import hashlib
import os
import time

from .. import paths


def cache_key(url: str, fmt: str, viewport: tuple, full_page: bool) -> str:
    return hashlib.sha256(f"{url}|{fmt}|{viewport}|{full_page}".encode()).hexdigest()


def get(key):
    p = _path(key)
    if os.path.exists(p):
        # TTL 1h
        if time.time() - os.path.getmtime(p) < 3600:
            with open(p, "rb") as f:
                return f.read()
    return None


def put(key, data):
    os.makedirs(_CACHE_DIR, exist_ok=True)
    with open(_path(key), "wb") as f:
        f.write(data)


_CACHE_DIR = str(paths.DATA_DIR)


def _path(key):
    return os.path.join(_CACHE_DIR, key)
