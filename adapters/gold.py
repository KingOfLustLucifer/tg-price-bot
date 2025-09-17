import yfinance as yf
from utils.cache import cached
from utils.sheets import get_setting
from .fx import get_fx_rate

def _yf_last(ticker):
    t = yf.Ticker(ticker)
    hist = t.history(period="1d")
    if hist is None or hist.empty:
        return None
    return float(hist["Close"].iloc[-1])

@cached(ttl=60)
async def get_gold_price_idr():
    # Allow override via Google Sheet key: gold_xauusd_override
    try:
        override = await get_setting("gold_xauusd_override")
    except Exception:
        override = None

    usd = None
    if override:
        try:
            usd = float(override)
        except Exception:
            usd = None

    # Try XAUUSD=X, fallback to GC=F (gold futures, close enough)
    if usd is None:
        usd = _yf_last("XAUUSD=X")
    if usd is None:
        usd = _yf_last("GC=F")

    if usd is None:
        return {"ok": False, "error": "No data for XAUUSD or GC=F"}

    # Convert to IDR
    try:
        fx = await get_fx_rate("USDIDR")
        idr = usd * fx["rate"] if fx.get("ok") else None
    except Exception:
        idr = None

    return {"ok": True, "usd": usd, "idr": idr}
