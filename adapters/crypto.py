import yfinance as yf
from utils.cache import cached

def _usd_to_idr_rate():
    try:
        fx = yf.Ticker("USDIDR=X").history(period="1d")
        if fx is not None and not fx.empty:
            return float(fx["Close"].iloc[-1])
    except Exception:
        pass
    return None

@cached(ttl=45)
async def get_crypto_price_idr(symbol: str):
    try:
        ticker = f"{symbol.upper()}-USD"
        t = yf.Ticker(ticker)
        hist = t.history(period="1d", interval="1m")
        if hist is None or hist.empty:
            hist = t.history(period="1d")
        if hist is None or hist.empty:
            return {"ok": False, "error": "No data"}
        usd = float(hist["Close"].dropna().iloc[-1])
        rate = _usd_to_idr_rate()
        idr = usd * rate if rate else None
        return {"ok": True, "usd": usd, "idr": idr}
    except Exception as e:
        return {"ok": False, "error": str(e)}
