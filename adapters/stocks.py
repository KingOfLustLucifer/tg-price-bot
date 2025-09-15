import yfinance as yf
from utils.cache import cached

@cached(ttl=60)
async def get_stock_price(ticker: str):
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info  # fast path
        last = info.get("last_price")
        currency = info.get("currency", "IDR")
        if last is None:
            # Fallback to previous close via history
            hist = t.history(period="5d")
            if hist is None or hist.empty:
                return {"ok": False, "error": "No data"}
            last = float(hist["Close"].dropna().iloc[-1])
        return {"ok": True, "price": float(last), "currency": currency}
    except Exception as e:
        return {"ok": False, "error": str(e)}
