import os
from dotenv import load_dotenv
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
EXTRACT_LEASE_SECONDS = int(os.getenv("EXTRACT_LEASE_SECONDS", "600"))
PRICE_LEASE_SECONDS = int(os.getenv("PRICE_LEASE_SECONDS", "900"))
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
