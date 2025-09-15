import os
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update
from telegram.ext import Application, ApplicationBuilder
from bot_handlers import register_handlers
from utils.sheets import diag_info
from utils.formatting import ok_status

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "secret")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is required")

app = FastAPI(title="tg_instruments_bot")

# CORS (optional, helpful during pings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Telegram application (singleton)
tg_app: Application | None = None

@app.on_event("startup")
async def on_startup():
    global tg_app
    tg_app = ApplicationBuilder().token(BOT_TOKEN).concurrent_updates(True).build()
    register_handlers(tg_app)
    # Try to set the webhook automatically if an external URL is known
    if RENDER_EXTERNAL_URL and WEBHOOK_SECRET:
        webhook_url = f"{RENDER_EXTERNAL_URL}/webhook/{WEBHOOK_SECRET}"
        await tg_app.bot.set_webhook(webhook_url, drop_pending_updates=True, allowed_updates=["message", "callback_query"])
    else:
        # Fallback to long-poll (not used on Render, but useful locally)
        asyncio.create_task(tg_app.run_polling(allowed_updates=Update.ALL_TYPES))

@app.on_event("shutdown")
async def on_shutdown():
    global tg_app
    if tg_app:
        await tg_app.shutdown()
        tg_app = None

@app.get("/diag")
async def diag():
    """Lightweight diagnostics to verify env & sheet connectivity."""
    info = await diag_info()
    return JSONResponse(info)

@app.get("/healthz")
async def healthz():
    return PlainTextResponse("ok")

@app.post("/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request):
    if secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="forbidden")
    if tg_app is None:
        raise HTTPException(status_code=503, detail="bot not ready")
    try:
        data = await request.json()
    except Exception:
        data = {}
    update = Update.de_json(data, tg_app.bot)
    await tg_app.initialize()
    await tg_app.process_update(update)
    return JSONResponse(ok_status("processed"))
