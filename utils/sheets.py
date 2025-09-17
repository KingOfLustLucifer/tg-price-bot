import os
import json
from typing import Optional, Dict, Any, List
from utils.cache import cached

_gspread = None
_gclient = None
_gsheet = None

def _ensure_gspread():
    global _gspread, _gclient, _gsheet
    if _gspread is None:
        import gspread
        from google.oauth2.service_account import Credentials
        _gspread = gspread
        creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if not creds_json:
            raise RuntimeError("GOOGLE_CREDENTIALS_JSON env is missing")
        try:
            info = json.loads(creds_json)
        except Exception:
            with open(creds_json, "r", encoding="utf-8") as f:
                info = json.load(f)
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        _gclient = _gspread.authorize(creds)
        sheet_id = os.getenv("SHEET_ID")
        if not sheet_id:
            raise RuntimeError("SHEET_ID env is missing")
        _gsheet = _gclient.open_by_key(sheet_id)

def _worksheet(name: str):
    _ensure_gspread()
    try:
        return _gsheet.worksheet(name)
    except Exception:
        return _gsheet.add_worksheet(title=name, rows=100, cols=10)

@cached(ttl=30)
async def get_setting(key: str) -> Optional[str]:
    ws = _worksheet("settings")
    header = ws.row_values(1)
    if not header:
        ws.update("A1:B1", [["key", "value"]])
        return None
    keys = ws.col_values(1)
    values = ws.col_values(2)
    mapping = {k: v for k, v in zip(keys[1:], values[1:])}
    return mapping.get(key)

@cached(ttl=10)
async def get_watchlist() -> List[str]:
    ws = _worksheet("watchlist")
    header = ws.row_values(1)
    if not header:
        ws.update("A1:A1", [["asset"]])
        return []
    assets = ws.col_values(1)[1:]
    return [a for a in assets if a.strip()]

async def add_watch(asset: str):
    ws = _worksheet("watchlist")
    wl = await get_watchlist()
    if asset in wl:
        return True, "Sudah ada di watchlist"
    ws.append_row([asset])
    return True, f"Ditambahkan: {asset}"

async def del_watch(asset: str):
    ws = _worksheet("watchlist")
    data = ws.col_values(1)
    for idx, val in enumerate(data, start=1):
        if val.strip() == "asset":
            continue
        if val.strip() == asset:
            ws.delete_rows(idx)
            return True, f"Dihapus: {asset}"
    return False, "Tidak ditemukan"


async def diag_info():
    ok = True
    details = {}
    try:
        _ = _worksheet("settings")
        details["settings"] = "ok"
    except Exception as e:
        ok = False
        details["settings"] = f"error: {e}"

    try:
        _ = _worksheet("watchlist")
        details["watchlist"] = "ok"
    except Exception as e:
        ok = False
        details["watchlist"] = f"error: {e}"


    try:
        gold_override = await get_setting("gold_xauusd_override")
        details["gold_xauusd_override"] = "set" if gold_override else "unset"
    except Exception as e:
        details["gold_xauusd_override"] = f"error: {e}"
        ok = False

    return {
        "ok": ok,
        "details": details,
        "env": {
            "SHEET_ID": bool(os.getenv("SHEET_ID")),
            "GOOGLE_CREDENTIALS_JSON": bool(os.getenv("GOOGLE_CREDENTIALS_JSON")),
        }
    }
