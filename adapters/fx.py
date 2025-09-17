import yfinance as yf
import requests
from utils.cache import cached

def _yf_rate(symbol: str):
    t = yf.Ticker(symbol)
    hist = t.history(period="1d")
    if hist is None or hist.empty:
        return None
    return float(hist["Close"].iloc[-1])

def _erh_rate(base: str, quote: str):
    try:
        r = requests.get(f"https://api.exchangerate.host/latest", params={"base": base, "symbols": quote}, timeout=6)
        if r.ok:
            data = r.json()
            return float(data["rates"][quote])
    except Exception:
        return None
    return None

@cached(ttl=60)
async def get_fx_rate(pair: str):
    pair = pair.upper()
    # Support forms: USDIDR or USDIDR=X
    yf_symbol = pair if pair.endswith("=X") else pair + "=X"
    # Yahoo first
    try:
        rate = _yf_rate(yf_symbol)
        if rate:
            return {"ok": True, "rate": rate}
    except Exception:
        pass
    # Fallback: exchangerate.host
    try:
        base, quote = pair[:3], pair[3:]
        if base and quote and len(base) == 3 and len(quote) == 3:
            rate = _erh_rate(base, quote)
            if rate:
                return {"ok": True, "rate": rate}
    except Exception:
        pass
    return {"ok": False, "error": "No data from Yahoo or exchangerate.host"}
