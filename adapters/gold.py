# adapters/gold.py  (atau file yang sekarang memuat fungsi ini)
import re
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup

from utils.cache import cached
from utils.sheets import get_setting
from .fx import get_fx_rate  # tetap dipakai untuk USDIDR

_IDR_NUM = re.compile(r"[^0-9]")

def _parse_idr(text: str) -> Optional[int]:
    """
    "Rp 2.090.000" -> 2090000
    """
    if not text:
        return None
    digits = _IDR_NUM.sub("", text)
    return int(digits) if digits else None

async def _fetch_html(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"}) as resp:
        resp.raise_for_status()
        return await resp.text()

async def _scrape_antam_idr(session: aiohttp.ClientSession) -> Optional[int]:
    """
    Ambil harga per gram dari laman resmi Logam Mulia (Antam).
    """
    html = await _fetch_html(session, "https://www.logammulia.com/id/harga-emas-hari-ini")
    soup = BeautifulSoup(html, "lxml")

    # Pola umum: sel tabel dengan atribut data-title
    td = soup.find("td", attrs={"data-title": re.compile(r"Harga Emas per Gram", re.I)})
    if td and td.text.strip():
        val = _parse_idr(td.text)
        if val:
            return val

    # Fallback: cari label lalu angka Rp terdekat
    label = soup.find(string=re.compile(r"Harga Emas per Gram", re.I))
    if label:
        nxt = label.parent.find_next(string=re.compile(r"Rp\s*[0-9\.\,]+"))
        if nxt:
            val = _parse_idr(nxt)
            if val:
                return val

    return None

async def _scrape_pegadaian_idr(session: aiohttp.ClientSession) -> Optional[int]:
    """
    Fallback: ambil dari Pegadaian. Struktur bisa berubah, jadi ambil angka Rp terbesar yang wajar.
    """
    html = await _fetch_html(session, "https://www.pegadaian.co.id/harga-emas-hari-ini")
    soup = BeautifulSoup(html, "lxml")
    texts = soup.find_all(string=re.compile(r"Rp\s*[0-9\.\,]+"))
    candidates = []
    for t in texts:
        val = _parse_idr(t)
        if val and val > 500_000:  # buang angka kecil yg bukan per-gram
            candidates.append(val)
    if not candidates:
        return None
    # biasanya ada beberapa angka; ambil yang paling kecil (mendekati per-gram)
    return min(candidates)

@cached(ttl=60)
async def get_gold_price_idr():
    """
    Return price per GRAM:
      {"ok": bool, "usd": float|None, "idr": float|None, "source": str|None, "error": str|None}

    - Ambil IDR/gram dari Antam (fallback Pegadaian).
    - USD/gram dihitung dari kurs USDIDR (via get_fx_rate).
    - Ada override manual 'gold_idr_override' (IDR/gram).
    """
    # 0) Manual override (IDR per gram)
    try:
        override_idr = await get_setting("g
