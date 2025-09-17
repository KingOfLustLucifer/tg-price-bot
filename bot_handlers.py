from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, Application
from adapters.stocks import get_stock_price
from adapters.crypto import get_crypto_price_idr
from adapters.fx import get_fx_rate
from adapters.gold import get_gold_price_idr
from utils.formatting import fmt_idr, fmt_usd

HELP_TEXT = (
    "Hai! Aku bot investasi.\n"
    "Perintah yang tersedia:\n"
    "/price <TICKER> – harga saham (yfinance)\n"
    "/crypto <SYMBOL> – harga crypto (BTC, ETH, dll)\n"
    "/gold – harga emas XAU di IDR\n"
    "/fx <PAIR> – kurs FX (mis. USDIDR, USDJPY)\n"
    "/rd <CODE> – NAV reksadana (IDN)\n"
    "/watchlist – lihat watchlist\n"
    "/addwatch <ASSET> – tambah ke watchlist\n"
    "/delwatch <ASSET> – hapus dari watchlist\n"
)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)

async def cmd_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Format: /price <TICKER>, contoh: /price BBCA.JK")
        return
    ticker = context.args[0].upper()
    data = await get_stock_price(ticker)
    if data["ok"]:
        price = data["price"]
        currency = data.get("currency") or ""
        await update.message.reply_text(f"{ticker}: {price} {currency}".strip())
    else:
        await update.message.reply_text(f"Gagal mengambil harga {ticker}: {data['error']}")

async def cmd_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Format: /crypto <SYMBOL>, contoh: /crypto BTC")
        return
    sym = context.args[0].upper()
    data = await get_crypto_price_idr(sym)
    if data["ok"]:
        usd = data["usd"]
        idr = data["idr"]
        idr_txt = fmt_idr(idr) if idr else "N/A"
        await update.message.reply_text(f"{sym}-USD: {fmt_usd(usd)} ≈ {idr_txt}")
    else:
        await update.message.reply_text(f"Gagal mengambil harga crypto: {data['error']}")

async def cmd_gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_gold_price_idr()
    if data["ok"]:
        usd_txt = fmt_usd(data['usd'])
        idr_txt = fmt_idr(data['idr']) if data['idr'] else "N/A"
        await update.message.reply_text(f"Emas per gram ≈ {usd_txt} | ≈ {idr_txt}")
    else:
        await update.message.reply_text(f"Gagal mengambil harga emas: {data['error']}")

async def cmd_fx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Format: /fx <PAIR>, contoh: /fx USDIDR")
        return
    pair = context.args[0].upper()
    data = await get_fx_rate(pair)
    if data["ok"]:
        await update.message.reply_text(f"{pair}: {data['rate']}")
    else:
        await update.message.reply_text(f"Gagal mengambil kurs {pair}: {data['error']}")


async def cmd_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from utils.sheets import get_watchlist
    wl = await get_watchlist()
    if not wl:
        await update.message.reply_text("Watchlist kosong. Tambah dengan /addwatch <ASSET>")
        return
    text = "Watchlist:\n" + "\n".join(f"• {x}" for x in wl)
    await update.message.reply_text(text)

async def cmd_addwatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from utils.sheets import add_watch
    if not context.args:
        await update.message.reply_text("Format: /addwatch <ASSET>")
        return
    asset = " ".join(context.args).strip()
    ok, msg = await add_watch(asset)
    await update.message.reply_text(msg)

async def cmd_delwatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from utils.sheets import del_watch
    if not context.args:
        await update.message.reply_text("Format: /delwatch <ASSET>")
        return
    asset = " ".join(context.args).strip()
    ok, msg = await del_watch(asset)
    await update.message.reply_text(msg)

def register_handlers(app: Application):
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("price", cmd_price))
    app.add_handler(CommandHandler("crypto", cmd_crypto))
    app.add_handler(CommandHandler("gold", cmd_gold))
    app.add_handler(CommandHandler("fx", cmd_fx))
    app.add_handler(CommandHandler("watchlist", cmd_watchlist))
    app.add_handler(CommandHandler("addwatch", cmd_addwatch))
    app.add_handler(CommandHandler("delwatch", cmd_delwatch))
