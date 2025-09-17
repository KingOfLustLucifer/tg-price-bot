import yfinance as yf
import requests
from utils.cache import cached
from utils.sheets import get_setting

def _yf_rate(symbol: str):
    t = yf.Ticker(symbol)
    hist = t.history(period="1d")
    if hist is None or hist.empty:
        return None
    return float(hist["Close"].dropna().iloc[-1])

def _yahoo_chart_rate(symbol: str):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"range": "5d", "interval": "1d"}
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, params=params, headers=headers, timeout=8)
    if not r.ok:
        return None
    data = r.json()
    result = (data or {}).get("chart", {}).get("result")
    if not result:
        return None
    r0 = result[0]
    closes = r0.get("indicators", {}).get("quote", [{}])[0].get("close", [])
    closes = [c for c in closes if c is not None]
    if not closes:
        return None
    return float(closes[-1])

def _erh_rate(base: str, quote: str):
    try:
        r = requests.get("https://api.exchangerate.host/latest", params={"base": base, "symbols": quote}, timeout=6)
        if r.ok:
            data = r.json()
            return float(data["rates"][quote])
    except Exception:
        return None
    return None

@cached(ttl=60)
async def get_fx_rate(pair: str):
    pair = pair.upper().replace("=X","")
    base, quote = pair[:3], pair[3:]
    yf_symbol = f"{base}{quote}=X"
    # 0) Manual override from Sheets (usd_idr_override etc)
    try:
        if base == "USD" and quote == "IDR":
            manual = await get_setting("usd_idr_override")
            if manual:
                return {"ok": True, "rate": float(manual)}
    except Exception:
        pass
    # 1) Yahoo via yfinance
    try:
        rate = _yf_rate(yf_symbol)
        if rate:
            return {"ok": True, "rate": rate}
    except Exception:
        pass
    # 2) Yahoo Chart API
    try:
        rate = _yahoo_chart_rate(yf_symbol)
        if rate:
            return {"ok": True, "rate": rate}
    except Exception:
        pass
    # 3) exchangerate.host fallback
    try:
        rate = _erh_rate(base, quote)
        if rate:
            return {"ok": True, "rate": rate}
    except Exception:
        pass
    return {"ok": False, "error": "No data from Yahoo (yfinance/chart) or exchangerate.host; consider setting 'usd_idr_override' in Sheet"}
