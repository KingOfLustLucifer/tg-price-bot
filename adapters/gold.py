from utils.cache import cached
from utils.sheets import get_setting
from .fx import get_fx_rate
import re
from typing import Optional
import aiohttp
from bs4 import BeautifulSoup

_IDR_NUM = re.compile(r"[^0-9]")

def _parse_idr(text: str) -> Optional[int]:
    digits = _IDR_NUM.sub("", text or "")
    return int(digits) if digits else None

async def _fetch_html(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"}) as resp:
        resp.raise_for_status()
        return await resp.text()

async def _scrape_antam_idr(session: aiohttp.ClientSession) -> Optional[int]:
    html = await _fetch_html(session, "https://www.logammulia.com/id/harga-emas-hari-ini")
    soup = BeautifulSoup(html, "lxml")
    td = soup.find("td", attrs={"data-title": re.compile(r"Harga Emas per Gram", re.I)})
    if td and td.text.strip():
        val = _parse_idr(td.text)
        if val:
            return val
    label = soup.find(string=re.compile(r"Harga Emas per Gram", re.I))
    if label:
        nxt = label.parent.find_next(string=re.compile(r"Rp\s*[0-9\.\,]+"))
        if nxt:
            val = _parse_idr(nxt)
            if val:
                return val
    return None

async def _scrape_pegadaian_idr(session: aiohttp.ClientSession) -> Optional[int]:
    html = await _fetch_html(session, "https://www.pegadaian.co.id/harga-emas-hari-ini")
    soup = BeautifulSoup(html, "lxml")
    texts = soup.find_all(string=re.compile(r"Rp\s*[0-9\.\,]+"))
    candidates = []
    for t in texts:
        val = _parse_idr(t)
        if val and val > 500_000:
            candidates.append(val)
    return min(candidates) if candidates else None

@cached(ttl=60)
async def get_gold_price_idr():
    """
    Return {"ok": bool, "usd": float|None, "idr": float|None, "source": str|None, "error": str|None}
    """
    # ✅ perbaikan baris ini:
    try:
        override_idr = await get_setting("gold_idr_override")
    except Exception:
        override_idr = None

    idr_per_gram = None
    source = None

    if override_idr:
        try:
            idr_per_gram = float(override_idr)
            source = "override"
        except Exception:
            idr_per_gram = None

    if idr_per_gram is None:
        async with aiohttp.ClientSession() as session:
            try:
                idr_per_gram = await _scrape_antam_idr(session)
                source = "Antam" if idr_per_gram else None
            except Exception:
                idr_per_gram = None
            if idr_per_gram is None:
                try:
                    idr_per_gram = await _scrape_pegadaian_idr(session)
                    source = "Pegadaian" if idr_per_gram else None
                except Exception:
                    idr_per_gram = None

    if idr_per_gram is None:
        return {"ok": False, "usd": None, "idr": None, "source": None, "error": "Gagal ambil Antam/Pegadaian"}

    # Konversi USD/gram pakai kurs USDIDR kamu
    usd_per_gram = None
    try:
        fx = await get_fx_rate("USDIDR")
        if fx.get("ok") and fx.get("rate"):
            usd_per_gram = float(idr_per_gram) / float(fx["rate"])
    except Exception:
        usd_per_gram = None

    return {"ok": True, "usd": usd_per_gram, "idr": float(idr_per_gram), "source": source, "error": None}
