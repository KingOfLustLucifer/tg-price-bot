from utils.cache import cached
from utils.sheets import get_mutual_fund_row

@cached(ttl=300)
async def get_mutual_fund_nav(name_or_code: str):
    """Lookup NAV from Google Sheet 'mutual_funds' (Name, Code, NAV_IDR, Date)."""
    query = " ".join(name_or_code.split()).strip()
    if not query:
        return {"ok": False, "error": "empty query"}
    row = await get_mutual_fund_row(query)
    if not row:
        return {"ok": False, "error": "not found in Sheet 'mutual_funds' (add row with columns: Name, Code, NAV_IDR, Date)"}
    try:
        nav_idr = float(str(row.get("NAV_IDR")).replace(",","").replace("_",""))
    except Exception:
        return {"ok": False, "error": "invalid NAV value (must be numeric)"}
    return {"ok": True, "nav_idr": nav_idr, "date": row.get("Date"), "code": row.get("Code"), "name": row.get("Name")}
