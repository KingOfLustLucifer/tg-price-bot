from utils.cache import cached
from utils.sheets import get_mutual_fund_row

@cached(ttl=300)
async def get_mutual_fund_nav(name_or_code: str):
    row = await get_mutual_fund_row(name_or_code)
    if not row:
        return {"ok": False, "error": "not found in Sheet 'mutual_funds'"}
    try:
        nav_idr = float(row.get("NAV_IDR"))
    except Exception:
        return {"ok": False, "error": "invalid NAV value"}
    return {"ok": True, "nav_idr": nav_idr, "date": row.get("Date"), "code": row.get("Code"), "name": row.get("Name")}
