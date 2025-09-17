# tg_instruments_bot (Render-ready, Docker)

## Fitur
- `/price <TICKER>` – yfinance (pakai `<CODE>.JK` untuk saham BEI)
- `/crypto <SYMBOL>` – harga USD + konversi IDR via `USDIDR=X`
- `/gold` – XAUUSD; override lewat Sheet `gold_xauusd_override`
- `/fx <PAIR>` – kurs FX (USDIDR, USDJPY, dsb.)
- `/rd <NAME|CODE>` – NAV reksadana dari tab `mutual_funds`
- `/watchlist`, `/addwatch`, `/delwatch`
- HTTP: `/healthz`, `/diag`, `/webhook/<secret>`

## Env (Render)
- `BOT_TOKEN` (wajib), `WEBHOOK_SECRET` (wajib)
- `SHEET_ID`, `GOOGLE_CREDENTIALS_JSON` (raw JSON)
- (opsional) `RENDER_EXTERNAL_URL` untuk auto-set webhook

## Sheet Tabs
- `settings`: `key`, `value` (contoh `gold_xauusd_override | 2450.0`)
- `watchlist`: `asset`
- `mutual_funds`: `Name`, `Code`, `NAV_IDR`, `Date`
