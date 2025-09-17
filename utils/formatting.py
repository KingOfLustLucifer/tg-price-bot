def fmt_idr(n: float) -> str:
    try:
        return "Rp {:,.0f}".format(n).replace(",", ".")
    except Exception:
        return f"Rp {n}"

def fmt_usd(n: float) -> str:
    try:
        return "${:,.2f}".format(n)
    except Exception:
        return f"${n}"

def ok_status(msg: str):
    return {"status": "ok", "message": msg}
