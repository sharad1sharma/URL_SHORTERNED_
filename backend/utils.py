import secrets
import string
from urllib.parse import urlparse

ALPHABET = string.ascii_letters + string.digits

def generate_short_code(length=6):
    return "".join(secrets.choice(ALPHABET) for _ in range(length))

def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False

def row_to_dict(row):
    return dict(row) if row else None
