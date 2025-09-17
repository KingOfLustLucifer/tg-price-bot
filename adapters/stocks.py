import yfinance as yf
from utils.cache import cached

@cached(ttl=60)
async def get_stock_price(ticker: str):
    try:
        t = yf.Ticker(ticker)
        info = getattr(t, "fast_info", {}) or {}
        last = info.get("last_price")
        currency = (info.get("currency") if isinstance(info, dict) else None) or "IDR"
        if last is None:
            hist = t.history(period="5d")
            if hist is None or hist.empty:
                return {"ok": False, "error": "No data from Yahoo"}
            last = float(hist["Close"].dropna().iloc[-1])
        return {"ok": True, "price": float(last), "currency": currency}
    except Exception as e:
        return {"ok": False, "error": str(e)}
