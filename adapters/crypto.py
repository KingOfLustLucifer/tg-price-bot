import yfinance as yf
import requests
from utils.cache import cached
from .fx import get_fx_rate

_COINGECKO_MAP = {
    "BTC": "bitcoin",
    "XBT": "bitcoin",
    "WBTC": "wrapped-bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "DOGE": "dogecoin",
    "ADA": "cardano",
    "XRP": "ripple",
    "TRX": "tron",
    "MATIC": "matic-network",
    "POL": "polygon-ecosystem-token",
    "DOT": "polkadot",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
    "TON": "the-open-network",
    "LTC": "litecoin"
}

def _yf_price_usd(symbol: str):
    t = yf.Ticker(f"{symbol}-USD")
    hist = t.history(period="1d", interval="1m")
    if hist is None or hist.empty:
        hist = t.history(period="1d")
    if hist is None or hist.empty:
        return None
    return float(hist["Close"].dropna().iloc[-1])

def _coingecko_price_usd(symbol: str):
    try:
        coin_id = _COINGECKO_MAP.get(symbol.upper(), symbol.lower())
        r = requests.get("https://api.coingecko.com/api/v3/simple/price",
                         params={"ids": coin_id, "vs_currencies": "usd"},
                         timeout=8)
        if r.ok:
            data = r.json()
            val = data.get(coin_id, {}).get("usd")
            return float(val) if val is not None else None
    except Exception:
        return None
    return None

def _binance_price_usd(symbol: str):
    """Fetch price from Binance public API in USDT (≈ USD)."""
    try:
        # Map common symbols directly to USDT pairs
        pair = f"{symbol.upper()}USDT"
        r = requests.get("https://api.binance.com/api/v3/ticker/price",
                         params={"symbol": pair}, timeout=8)
        if r.ok:
            price = r.json().get("price")
            if price is not None:
                return float(price)  # USDT ≈ USD
    except Exception:
        return None
    return None

@cached(ttl=45)
async def get_crypto_price_idr(symbol: str):
    sym = symbol.upper().strip()
    usd = None
    # 1) Yahoo
    try:
        usd = _yf_price_usd(sym)
    except Exception:
        usd = None
    # 2) CoinGecko
    if usd is None:
        usd = _coingecko_price_usd(sym)
    # 3) Binance
    if usd is None:
        usd = _binance_price_usd(sym)
    if usd is None:
        return {"ok": False, "error": "No data from Yahoo, CoinGecko, or Binance"}
    # Convert to IDR
    try:
        fx = await get_fx_rate("USDIDR")
        idr = usd * fx["rate"] if fx.get("ok") else None
    except Exception:
        idr = None
    return {"ok": True, "usd": usd, "idr": idr}
