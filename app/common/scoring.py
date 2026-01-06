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
