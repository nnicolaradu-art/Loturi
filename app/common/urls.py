import re
from urllib.parse import urlparse, urlunparse
LOT_UUID_RE = re.compile(r"/lot-([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})")
def canonical_url(url: str) -> str:
u = urlparse(url.strip())
# drop fragments, keep query
return urlunparse((u.scheme, u.netloc, u.path, u.params, u.query, ""))
def extract_lot_uuid(url: str) -> str | None:
m = LOT_UUID_RE.search(url)
return m.group(1).lower() if m else None
