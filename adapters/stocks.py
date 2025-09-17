import yfinance as yf
import requests
from utils.cache import cached

def _yf_history_last(ticker: str):
    t = yf.Ticker(ticker)
    hist = t.history(period="5d")
    if hist is None or hist.empty:
        return None, None
    last = float(hist["Close"].dropna().iloc[-1])
    # currency via fast_info or empty
    info = getattr(t, "fast_info", {}) or {}
    currency = info.get("currency") if isinstance(info, dict) else None
    return last, currency

def _yahoo_chart_last(ticker: str):
    """Fallback: hit Yahoo chart API directly (often works where yfinance fails)."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {"range": "5d", "interval": "1d"}
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, params=params, headers=headers, timeout=8)
    if not r.ok:
        return None, None
    data = r.json()
    result = (data or {}).get("chart", {}).get("result")
    if not result:
        return None, None
    r0 = result[0]
    currency = r0.get("meta", {}).get("currency")
    closes = r0.get("indicators", {}).get("quote", [{}])[0].get("close", [])
    closes = [c for c in closes if c is not None]
    if not closes:
        return None, currency
    return float(closes[-1]), currency

@cached(ttl=60)
async def get_stock_price(ticker: str):
    # 1) yfinance fast_info + history
    try:
        t = yf.Ticker(ticker)
        info = getattr(t, "fast_info", {}) or {}
        last = info.get("last_price")
        currency = (info.get("currency") if isinstance(info, dict) else None) or ""
        if last is None:
            last, cur2 = _yf_history_last(ticker)
            currency = currency or (cur2 or "")
        if last is not None:
            return {"ok": True, "price": float(last), "currency": currency or "IDR"}
    except Exception:
        pass

    # 2) Fallback: Yahoo Chart API direct
    try:
        last, currency = _yahoo_chart_last(ticker)
        if last is not None:
            return {"ok": True, "price": float(last), "currency": (currency or "IDR")}
    except Exception:
        pass

    return {"ok": False, "error": "No data from Yahoo (both yfinance and chart API)"}
