import asyncio
import time
from app.common.config import HEADLESS, EXTRACT_LEASE_SECONDS
from app.common.supabase_db import sb, mark_lot_extract_done, insert_asset, enqueue_price
from playwright.async_api import async_playwright
WORKER_ID = "extract-worker-1"
async def claim_next_extract_job(run_id: str):
# Uses SQL function from Query Pack v2
res = sb.rpc("claim_next_extract_job", {"p_run_id": run_id, "p_worker_id": WORKER_ID, "p_lease_seconds": EXTRACT_
if not res.data:
return None
return res.data[0]["job_id"], res.data[0]["lot_row_id"]
async def fetch_lot_row(run_id: str, lot_row_id: str):
res = sb.table("lots").select("*").eq("run_id", run_id).eq("lot_row_id", lot_row_id).execute()
return res.data[0] if res.data else None
async def set_job_status(table: str, job_id: str, status: str, last_error: str | None = None):
payload = {"status": status, "updated_at": "now()"}
if status in ("done","failed"):
payload["finished_at"] = "now()"
if last_error:
payload["last_error"] = last_error
sb.table(table).update(payload).eq("job_id", job_id).execute()
async def extract_one_lot(page, run_id: str, lot_row_id: str, lot_url: str | None):
# Two modes:
# - Web lot: lot_url is not None -> navigate and extract from page
# - desc_image: lot_url is None -> local extract from stored text/assets (not shown in this skeleton)
fields = {}
category = "unknown"
if lot_url:
await page.goto(lot_url, wait_until="domcontentloaded")
await page.wait_for_timeout(500)
# TODO: selectors must be tuned after testing on the-saleroom layout
# title = await page.text_content("h1")
# description = await page.text_content("[data-testid='lot-description']")
# estimate = await page.text_content("text=Estimate")
# auction_house/date/lot_number parsing...
#
# For now: store basic proof screenshot
proof_bytes = await page.screenshot(full_page=False)
# Upload to Supabase Storage in real implementation; here we store path placeholder
insert_asset(run_id, lot_row_id, "screenshot_proof", lot_url, storage_path=None, position_index=0)
# fields update placeholders
fields.update({
"title": fields.get("title"),
"description": fields.get("description"),
"proof_screenshot_count": 1,
"image_count": fields.get("image_count", 0),
"category": category,
})
# Mark lot extracted and enqueue pricing
mark_lot_extract_done(run_id, lot_row_id, fields)
enqueue_price(run_id, lot_row_id, category=category)
async def worker_loop(run_id: str):
async with async_playwright() as p:
browser = await p.chromium.launch(headless=HEADLESS)
context = await browser.new_context()
page = await context.new_page()
while True:
job = await claim_next_extract_job(run_id)
if not job:
await asyncio.sleep(2)
continue
job_id, lot_row_id = job
lot = await fetch_lot_row(run_id, lot_row_id)
try:
await set_job_status("jobs_extract", job_id, "claimed")
await extract_one_lot(page, run_id, lot_row_id, lot.get("lot_url"))
await set_job_status("jobs_extract", job_id, "done")
except Exception as e:
await set_job_status("jobs_extract", job_id, "failed", last_error=str(e))
await asyncio.sleep(1)
await context.close()
await browser.close()
if __name__ == "__main__":
import sys
run_id = sys.argv[1]
asyncio.run(worker_loop(run_id))
