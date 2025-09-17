import yfinance as yf
import requests
from utils.cache import cached
from .fx import get_fx_rate

def _yf_price_usd(symbol: str):
    t = yf.Ticker(f"{symbol}-USD")
    hist = t.history(period="1d", interval="1m")
    if hist is None or hist.empty:
        hist = t.history(period="1d")
    if hist is None or hist.empty:
        return None
    return float(hist["Close"].dropna().iloc[-1])

def _coingecko_price_usd(symbol: str):
    # CoinGecko simple price (no key)
    try:
        # Map common symbols to coingecko IDs
        mapping = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "BNB": "binancecoin",
            "DOGE": "dogecoin",
            "ADA": "cardano",
            "XRP": "ripple",
            "TRX": "tron",
            "MATIC": "matic-network",
            "DOT": "polkadot"
        }
        coin_id = mapping.get(symbol.upper(), symbol.lower())
        r = requests.get("https://api.coingecko.com/api/v3/simple/price",
                         params={"ids": coin_id, "vs_currencies": "usd"}, timeout=6)
        if r.ok:
            data = r.json()
            val = data.get(coin_id, {}).get("usd")
            return float(val) if val is not None else None
    except Exception:
        return None
    return None

@cached(ttl=45)
async def get_crypto_price_idr(symbol: str):
    sym = symbol.upper()
    usd = None
    # Try Yahoo
    try:
        usd = _yf_price_usd(sym)
    except Exception:
        usd = None
    # Fallback to CoinGecko
    if usd is None:
        usd = _coingecko_price_usd(sym)
    if usd is None:
        return {"ok": False, "error": "No data from Yahoo or CoinGecko"}
    # Convert to IDR
    try:
        fx = await get_fx_rate("USDIDR")
        idr = usd * fx["rate"] if fx.get("ok") else None
    except Exception:
        idr = None
    return {"ok": True, "usd": usd, "idr": idr}
