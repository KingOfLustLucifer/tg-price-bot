import yfinance as yf
from utils.cache import cached
from utils.sheets import get_setting
from .fx import get_fx_rate

TROY_OUNCE_IN_GRAMS = 31.1034768

def _yf_last(ticker):
    t = yf.Ticker(ticker)
    hist = t.history(period="1d")
    if hist is None or hist.empty:
        return None
    return float(hist["Close"].iloc[-1])

@cached(ttl=60)
async def get_gold_price_idr():
    """Return price per GRAM: usd (per gram) and idr (per gram)."""
    # Optional manual override (XAUUSD per ounce)
    try:
        override = await get_setting("gold_xauusd_override")
    except Exception:
        override = None

    usd_per_ounce = None
    if override:
        try:
            usd_per_ounce = float(override)
        except Exception:
            usd_per_ounce = None

    if usd_per_ounce is None:
        usd_per_ounce = _yf_last("XAUUSD=X")
    if usd_per_ounce is None:
        usd_per_ounce = _yf_last("GC=F")

    if usd_per_ounce is None:
        return {"ok": False, "error": "No data for XAUUSD or GC=F"}

    usd_per_gram = usd_per_ounce / TROY_OUNCE_IN_GRAMS

    # Convert to IDR
    try:
        fx = await get_fx_rate("USDIDR")
        idr_per_gram = usd_per_gram * fx["rate"] if fx.get("ok") else None
    except Exception:
        idr_per_gram = None

    return {"ok": True, "usd": usd_per_gram, "idr": idr_per_gram}
