# tg_instruments_bot (Render-ready, Docker)

Telegram bot investasi dengan endpoint webhook FastAPI dan handler `python-telegram-bot` v20.

## Fitur
- `/price <TICKER>` – Harga saham via yfinance (fallback pakai Close kalau last_price None)
- `/crypto <SYMBOL>` – BTC/ETH, dll via yfinance; konversi ke IDR pakai `USDIDR=X`
- `/gold` – XAUUSD dengan opsi override dari Google Sheet: key `gold_xauusd_override`
- `/fx <PAIR>` – Kurs (mis. `USDIDR`, `USDJPY`)
- `/rd <NAME|CODE>` – NAV reksadana dari tab `mutual_funds` di Google Sheet
- `/watchlist`, `/addwatch`, `/delwatch` – Simpan watchlist di tab `watchlist`
- `/diag` (HTTP) – Diagnostik koneksi dan permission Sheet

## Env Vars
- `BOT_TOKEN` – token bot Telegram
- `WEBHOOK_SECRET` – secret untuk path webhook, mis: `/webhook/<secret>`
- `SHEET_ID` – Google Sheet ID
- `GOOGLE_CREDENTIALS_JSON` – JSON service account **(isi string JSON langsung)**

Opsional di Render:
- `RENDER_EXTERNAL_URL` – otomatis set webhook ke `<RENDER_EXTERNAL_URL>/webhook/<WEBHOOK_SECRET>` saat startup

## Struktur Sheet
Buat 3 tab berikut (huruf kecil/kapital bebas, yang penting judul tepat):
- `settings`: kolom `key`, `value`
  - baris contoh: `gold_xauusd_override | 2450.0`
- `watchlist`: kolom `asset`
- `mutual_funds`: kolom `Name`, `Code`, `NAV_IDR`, `Date`

## Deploy di Render (Web Service)
1. Buat Web Service baru dari repo ini (Docker).
2. Env:
   - `BOT_TOKEN`, `WEBHOOK_SECRET`, `SHEET_ID`, `GOOGLE_CREDENTIALS_JSON` (string JSON lengkap)
3. Health check path: `/healthz`
4. Setelah service up, cek `/diag`.
5. Pastikan variabel `RENDER_EXTERNAL_URL` otomatis ada (Render menyediakannya). Bila tidak, set manual env `RENDER_EXTERNAL_URL` = URL service.
6. Bot akan set webhook otomatis ke `RENDER_EXTERNAL_URL/webhook/<WEBHOOK_SECRET>`.

## Local run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export BOT_TOKEN=xxxxx WEBHOOK_SECRET=abc SHEET_ID=... GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'
uvicorn app:app --reload --port 10000
```
Lalu set webhook manual:
```bash
curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://your-ngrok-or-render-url/webhook/abc"}'
```

## Catatan
- Handler berjalan via webhook pada Render; fallback ke polling jika `RENDER_EXTERNAL_URL` tidak tersedia (dev lokal).
- `get_mutual_fund_nav` bergantung ke tab `mutual_funds`. Sesuaikan isi Sheet Anda.
- Bila muncul `PermissionError` pada Sheet, pastikan service account punya **Editor** ke spreadsheet yang benar (via share ke email service account).
