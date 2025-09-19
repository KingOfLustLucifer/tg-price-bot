import re
from typing import Optional, List

import aiohttp
from bs4 import BeautifulSoup

from utils.cache import cached
from utils.sheets import get_setting
from .fx import get_fx_rate

# ===== Helpers =====
_IDR_NUM = re.compile(r"[^0-9]")
_RP_REGEX = re.compile(r"Rp\s*[0-9\.\,]+", re.I)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/",
    "Cache-Control": "no-cache",
}

def _parse_idr(text: str) -> Optional[int]:
    if not text:
        return None
    digits = _IDR_NUM.sub("", text)
    try:
        return int(digits) if digits else None
    except Exception:
        return None

def _pick_reasonable(values: List[int]) -> Optional[int]:
    """
    Pilih angka yang 'masuk akal' untuk harga per gram ritel Indonesia.
    Biasanya 900k - 3.0M (tergantung kondisi pasar).
    Kita pilih nilai terkecil yang >= 800k untuk menghindari harga per-mg.
    """
    vals = sorted(v for v in values if 800_000 <= v <= 3_500_000)
    return vals[0] if vals else None

async def _fetch_html(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url, timeout=25, headers=HEADERS) as resp:
        resp.raise_for_status()
        return await resp.text()

# ===== Scrapers =====
async def _scrape_antam_idr(session: aiohttp.ClientSession) -> Optional[int]:
    url = "https://www.logammulia.com/id/harga-emas-hari-ini"
    try:
        html = await _fetch_html(session, url)
        soup = BeautifulSoup(html, "lxml")

        # Pola 1: tabel dengan atribut data-title
        td = soup.find("td", attrs={"data-title": re.compile(r"Harga Emas per Gram", re.I)})
        if td and td.text.strip():
            val = _parse_idr(td.text)
            if val:
                print("[gold] Antam: ketemu via data-title =", val)
                return val

        # Pola 2: cari label + next Rp…
        label = soup.find(string=re.compile(r"Harga Emas per Gram", re.I))
        if label:
            nxt = label.parent.find_next(string=_RP_REGEX)
            if nxt:
                val = _parse_idr(nxt)
                if val:
                    print("[gold] Antam: ketemu via label-sibling =", val)
                    return val

        # Pola 3: regex sweeping semua 'Rp ...'
        texts = soup.find_all(string=_RP_REGEX)
        candidates = [_parse_idr(t) for t in texts]
        candidates = [c for c in candidates if c]
        val = _pick_reasonable(candidates)
        if val:
            print("[gold] Antam: ketemu via regex fallback =", val)
            return val

        print("[gold] Antam: tidak ketemu selector manapun")
        return None
    except Exception as e:
        print(f"[gold] Antam error: {e}")
        return None

async def _scrape_pegadaian_idr(session: aiohttp.ClientSession) -> Optional[int]:
    url = "https://www.pegadaian.co.id/harga-emas-hari-ini"
    try:
        html = await _fetch_html(session, url)
        soup = BeautifulSoup(html, "lxml")

        texts = soup.find_all(string=_RP_REGEX)
        candidates = []
        for t in texts:
            v = _parse_idr(t)
            if v:
                candidates.append(v)
        val = _pick_reasonable(candidates)
        if val:
            print("[gold] Pegadaian: ketemu =", val)
        else:
            print("[gold] Pegadaian: regex tidak menemukan angka yang wajar")
        return val
    except Exception as e:
        print(f"[gold] Pegadaian error: {e}")
        return None

async def _scrape_hargaemas_idr(session: aiohttp.ClientSession) -> Optional[int]:
    """
    Fallback tambahan: harga-emas.org sering menampilkan 1 gram.
    Kita sweep angka 'Rp …' lalu pilih yang masuk akal.
    """
    url = "https://harga-emas.org/1-gram/"
    try:
        html = await _fetch_html(session, url)
        soup = BeautifulSoup(html, "lxml")
        texts = soup.find_all(string=_RP_REGEX)
        candidates = []
        for t in texts:
            v = _parse_idr(t)
            if v:
                candidates.append(v)
        val = _pick_reasonable(candidates)
        if val:
            print("[gold] HargaEmas.org: ketemu =", val)
        else:
            print("[gold] HargaEmas.org: regex tidak menemukan angka yang wajar")
        return val
    except Exception as e:
        print(f"[gold] HargaEmas.org error: {e}")
        return None

# ===== Public API =====
@cached(ttl=1800)  # 30 menit biar hemat request
async def get_gold_price_idr():
    """
    Return:
      {"ok": bool, "usd": float|None, "idr": float|None, "source": str|None, "error": str|None}
    Urutan sumber: Antam -> Pegadaian -> HargaEmas.org
    """
    # Override manual (IDR/gram)
    try:
        override_idr = await get_setting("gold_idr_override")
    except Exception:
        override_idr = None

    idr_per_gram: Optional[float] = None
    source: Optional[str] = None

    if override_idr:
        try:
            idr_per_gram = float(override_idr)
            source = "override"
            print(f"[gold] gunakan override: {idr_per_gram}")
        except Exception:
            idr_per_gram = None

    if idr_per_gram is None:
        async with aiohttp.ClientSession() as session:
            # 1) Antam
            idr_per_gram = await _scrape_antam_idr(session)
            source = "Antam" if idr_per_gram else None

            # 2) Pegadaian
            if idr_per_gram is None:
                idr_per_gram = await _scrape_pegadaian_idr(session)
                source = "Pegadaian" if idr_per_gram else None

            # 3) HargaEmas.org
            if idr_per_gram is None:
                idr_per_gram = await _scrape_hargaemas_idr(session)
                source = "HargaEmas.org" if idr_per_gram else None

    if idr_per_gram is None:
        return {
            "ok": False,
            "usd": None,
            "idr": None,
            "source": None,
            "error": "Gagal ambil Antam/Pegadaian/HargaEmas.org"
        }

    # Konversi ke USD/gram (opsional, pakai rate internal kamu)
    usd_per_gram = None
    try:
        fx = await get_fx_rate("USDIDR")
        if fx.get("ok") and fx.get("rate"):
            usd_per_gram = float(idr_per_gram) / float(fx["rate"])
    except Exception as e:
        print(f"[gold] FX error: {e}")
        usd_per_gram = None

    return {
        "ok": True,
        "usd": usd_per_gram,
        "idr": float(idr_per_gram),
        "source": source,
        "error": None
    }
