import yfinance as yf
import requests
from utils.cache import cached

CANDIDATE_SUFFIXES = ["", ".JK"]  # try raw first, then Indonesian exchange

def _yf_fast_last(sym: str):
    t = yf.Ticker(sym)
    info = getattr(t, "fast_info", {}) or {}
    return info.get("last_price"), (info.get("currency") if isinstance(info, dict) else None)

def _yf_history_last(sym: str):
    t = yf.Ticker(sym)
    hist = t.history(period="5d")
    if hist is None or hist.empty:
        return None
    return float(hist["Close"].dropna().iloc[-1])

def _yahoo_chart_last(sym: str):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
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

def _try_symbol(sym: str):
    # 1) fast_info
    last, currency = _yf_fast_last(sym)
    if last is not None:
        return {"ok": True, "price": float(last), "currency": currency or "IDR"}
    # 2) history
    last = _yf_history_last(sym)
    if last is not None:
        return {"ok": True, "price": float(last), "currency": currency or "IDR"}
    # 3) chart API
    last, currency2 = _yahoo_chart_last(sym)
    if last is not None:
        return {"ok": True, "price": float(last), "currency": (currency2 or "IDR")}
    return {"ok": False}

@cached(ttl=60)
async def get_stock_price(ticker: str):
    raw = ticker.upper().strip()
    # Build candidates: raw, and if not already with .JK, try raw + .JK
    candidates = []
    seen = set()
    for suf in CANDIDATE_SUFFIXES:
        sym = raw if suf == "" else (raw if raw.endswith(suf) else raw + suf)
        if sym not in seen:
            candidates.append(sym)
            seen.add(sym)
    # Ensure the original raw ticker is first
    if raw not in candidates:
        candidates.insert(0, raw)

    for sym in candidates:
        try:
            res = _try_symbol(sym)
            if res.get("ok"):
                return res
        except Exception:
            continue
    return {"ok": False, "error": f"No data for {raw} (tried: {', '.join(candidates)})"}
