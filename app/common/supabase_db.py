from supabase import create_client
from .config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
def insert_run(run_type: str, input_payload: dict, filtered_results_url: str | None,
throttle_mode: str, rpm: int, max_extract: int, max_price: int,
buyers_premium_pct: float, vat_pct: float) -> str:
data = {
"run_type": run_type,
"input_payload": input_payload,
"filtered_results_url": filtered_results_url,
"throttle_mode": throttle_mode,
"requests_per_minute_per_worker": rpm,
"max_extract_workers": max_extract,
"max_pricing_workers": max_price,
"buyers_premium_pct": buyers_premium_pct,
"vat_pct": vat_pct,
}
res = sb.table("runs").insert(data).execute()
return res.data[0]["run_id"]
def upsert_lot(run_id: str, lot_key: str, lot_url: str | None, fields: dict | None = None) -> str:
payload = {"run_id": run_id, "lot_key": lot_key, "lot_url": lot_url}
if fields:
payload.update(fields)
res = sb.table("lots").upsert(payload, on_conflict="run_id,lot_key").execute()
return res.data[0]["lot_row_id"]
def enqueue_extract(run_id: str, lot_row_id: str, priority: int = 100):
payload = {"run_id": run_id, "lot_row_id": lot_row_id, "priority": priority, "status": "pending"}
sb.table("jobs_extract").upsert(payload, on_conflict="run_id,lot_row_id").execute()
def enqueue_price(run_id: str, lot_row_id: str, category: str, priority: int = 100):
payload = {"run_id": run_id, "lot_row_id": lot_row_id, "category": category, "priority": priority, "status": "pen
sb.table("jobs_price").upsert(payload, on_conflict="run_id,lot_row_id").execute()
def mark_lot_extract_done(run_id: str, lot_row_id: str, fields: dict):
fields2 = dict(fields)
fields2.update({"extract_done": True})
sb.table("lots").update(fields2).eq("run_id", run_id).eq("lot_row_id", lot_row_id).execute()
def mark_lot_pricing_done(run_id: str, lot_row_id: str, fields: dict):
fields2 = dict(fields)
fields2.update({"pricing_done": True})
sb.table("lots").update(fields2).eq("run_id", run_id).eq("lot_row_id", lot_row_id).execute()
def insert_asset(run_id: str, lot_row_id: str, asset_type: str, source_url: str | None,
storage_path: str | None, position_index: int | None,
width_px: int | None = None, height_px: int | None = None):
payload = {
"run_id": run_id,
"lot_row_id": lot_row_id,
}
"asset_type": asset_type,
"source_url": source_url,
"storage_path": storage_path,
"position_index": position_index,
"width_px": width_px,
"height_px": height_px,
sb.table("lot_assets").insert(payload).execute( )
