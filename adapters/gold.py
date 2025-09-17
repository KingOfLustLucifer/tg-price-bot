import yfinance as yf
from utils.cache import cached
from utils.sheets import get_setting

def _usd_to_idr_rate():
    try:
        fx = yf.Ticker("USDIDR=X").history(period="1d")
        if fx is not None and not fx.empty:
            return float(fx["Close"].iloc[-1])
    except Exception:
        pass
    return None

@cached(ttl=60)
async def get_gold_price_idr():
    try:
        override = await get_setting("gold_xauusd_override")
    except Exception:
        override = None

    try:
        if override:
            usd = float(override)
        else:
            t = yf.Ticker("XAUUSD=X")
            hist = t.history(period="1d")
            if hist is None or hist.empty:
                return {"ok": False, "error": "No data"}
            usd = float(hist["Close"].iloc[-1])
        rate = _usd_to_idr_rate()
        idr = usd * rate if rate else None
        return {"ok": True, "usd": usd, "idr": idr}
    except Exception as e:
        return {"ok": False, "error": str(e)}
