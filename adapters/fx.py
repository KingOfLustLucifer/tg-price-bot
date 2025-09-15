import yfinance as yf
from utils.cache import cached

@cached(ttl=60)
async def get_fx_rate(pair: str):
    pair = pair.upper()
    yf_symbol = pair + "=X" if not pair.endswith("=X") else pair
    try:
        t = yf.Ticker(yf_symbol)
        hist = t.history(period="1d")
        if hist is None or hist.empty:
            return {"ok": False, "error": "No data"}
        rate = float(hist["Close"].iloc[-1])
        return {"ok": True, "rate": rate}
    except Exception as e:
        return {"ok": False, "error": str(e)}
