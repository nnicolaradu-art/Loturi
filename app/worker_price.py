import asyncio
from app.common.config import PRICE_LEASE_SECONDS
from app.common.supabase_db import sb, mark_lot_pricing_done
from app.common.scoring import compute_profitability_score
WORKER_ID = "price-worker-1"
async def claim_next_pricing_job(run_id: str, category: str | None = None):
args = {"p_run_id": run_id, "p_worker_id": WORKER_ID, "p_lease_seconds": PRICE_LEASE_SECONDS}
if category:
args["p_category"] = category
res = sb.rpc("claim_next_pricing_job", args).execute()
if not res.data:
return None
return res.data[0]["job_id"], res.data[0]["lot_row_id"]
def fetch_lot(run_id: str, lot_row_id: str):
return sb.table("lots").select("*").eq("run_id", run_id).eq("lot_row_id", lot_row_id).execute().data[0]
def set_job_status(table: str, job_id: str, status: str, last_error: str | None = None):
payload = {"status": status}
if status in ("done","failed"):
payload["finished_at"] = "now()"
if last_error:
payload["last_error"] = last_error
sb.table(table).update(payload).eq("job_id", job_id).execute()
def estimate_market_value(lot: dict) -> dict:
# TODO: implement per category:
# - cameras: sold comps, etc.
# - coins/toys/console: category sources
# Return dict: market_value_low/high/best, pricing_confidence
return {"market_value_low": None, "market_value_high": None, "market_value_best": None, "pricing_confidence": "un
async def worker_loop(run_id: str, category: str | None = None):
while True:
job = await claim_next_pricing_job(run_id, category)
if not job:
await asyncio.sleep(2)
continue
job_id, lot_row_id = job
try:
set_job_status("jobs_price", job_id, "claimed")
lot = fetch_lot(run_id, lot_row_id)
est = estimate_market_value(lot)
score = compute_profitability_score(run_id, lot, est)
fields = dict(est)
fields["profitability_score"] = score
mark_lot_pricing_done(run_id, lot_row_id, fields)
set_job_status("jobs_price", job_id, "done")
except Exception as e:
set_job_status("jobs_price", job_id, "failed", last_error=str(e))
await asyncio.sleep(1)
if __name__ == "__main__":
import sys
run_id = sys.argv[1]
category = sys.argv[2] if len(sys.argv) > 2 else None
asyncio.run(worker_loop(run_id, category))
11) app/common/scoring.py (profitability score 1-10 skeleton)
from app.common.supabase_db import sb
def get_run_fees(run_id: str) -> tuple[float,float]:
r = sb.table("runs").select("buyers_premium_pct,vat_pct").eq("run_id", run_id).execute().data[0]
return float(r["buyers_premium_pct"] or 0), float(r["vat_pct"] or 0)
def compute_profitability_score(run_id: str, lot: dict, est: dict) -> int:
# Conservative default when data is missing
bp, vat = get_run_fees(run_id)
he_low = lot.get("house_estimate_low")
he_high = lot.get("house_estimate_high")
mv_best = est.get("market_value_best")
# If no market estimate, return low score
if mv_best is None:
return 1
# If house estimate missing, score based on confidence/risk (conservative)
if he_low is None and he_high is None:
conf = (est.get("pricing_confidence") or "unknown")
return 4 if conf == "high" else 2
# Use midpoint of house estimate
he_mid = None
if he_low is not None and he_high is not None:
he_mid = (float(he_low) + float(he_high)) / 2.0
elif he_low is not None:
he_mid = float(he_low)
else:
he_mid = float(he_high)
# Adjust house figure with buyer fees
multiplier = 1.0 + (bp/100.0) + (vat/100.0)
he_all_in = he_mid * multiplier
mv = float(mv_best)
# Ratio of market value to all-in estimate
ratio = mv / max(he_all_in, 1e-6)
# Map ratio to 1..10 (tune later)
if ratio >= 2.2: return 10
if ratio >= 2.0: return 9
if ratio >= 1.8: return 8
if ratio >= 1.6: return 7
if ratio >= 1.45: return 6
if ratio >= 1.3: return 5
if ratio >= 1.15: return 4
if ratio >= 1.0: return 3
if ratio >= 0.85: return 2
return 1
