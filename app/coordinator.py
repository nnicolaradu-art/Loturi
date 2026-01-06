import uuid
from typing import List, Optional
from app.common.supabase_db import insert_run, upsert_lot, enqueue_extract
from app.common.urls import canonical_url, extract_lot_uuid
# NOTE:
# - Option 1/2 require parsing a results page into lot URLs.
# - The HTML structure can change; keep selectors configurable later.
# - This skeleton avoids any security bypass; use conservative browsing and rate limits.
def create_run_and_queue_lots(
run_type: str,
input_payload: dict,
filtered_results_url: Optional[str],
throttle_mode: str = "safe",
rpm: int = 3,
max_extract: int = 4,
max_price: int = 2,
buyers_premium_pct: float = 0.0,
vat_pct: float = 0.0,
) -> str:
run_id = insert_run(
run_type=run_type,
input_payload=input_payload,
filtered_results_url=filtered_results_url,
throttle_mode=throttle_mode,
rpm=rpm,
max_extract=max_extract,
max_price=max_price,
buyers_premium_pct=buyers_premium_pct,
vat_pct=vat_pct,
)
# Dispatch per run_type
if run_type in ("filtered_multi", "single_page"):
# placeholder: you will implement Playwright page -> collect lot urls
lot_urls = collect_lot_urls_from_results(filtered_results_url, paginate=(run_type=="filtered_multi"))
for url in lot_urls:
queue_one_lot(run_id, url)
elif run_type == "lot_list":
lot_urls = input_payload.get("lot_urls", [])
for url in lot_urls:
queue_one_lot(run_id, url)
elif run_type == "desc_image":
# Each submitted item becomes a synthetic lot
items = input_payload.get("items", [])
for item in items:
lot_key = str(uuid.uuid4())
lot_row_id = upsert_lot(run_id, lot_key, None, fields={"title": item.get("title"), "description": item.ge
enqueue_extract(run_id, lot_row_id)
else:
raise ValueError("Unknown run_type")
return run_id
def queue_one_lot(run_id: str, url: str):
url = canonical_url(url)
lot_uuid = extract_lot_uuid(url)
if not lot_uuid:
# not a lot URL, ignore
return
lot_row_id = upsert_lot(run_id, lot_uuid, url)
enqueue_extract(run_id, lot_row_id)
def collect_lot_urls_from_results(results_url: str, paginate: bool) -> List[str]:
# TODO implement with Playwright:
# - open results_url
# - collect all lot links on the page
# - if paginate: iterate next pages until end
# - if single_page: stop after first page
return [
