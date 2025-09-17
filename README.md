# tg_instruments_bot (Resilient Build)

Perbedaan utama vs build sebelumnya:
- **FX**: yfinance `USDIDR=X` → fallback ke **exchangerate.host** (tanpa API key).
- **Crypto**: yfinance `<SYMBOL>-USD` → fallback ke **CoinGecko** simple price (tanpa API key).
- **Gold**: `XAUUSD=X` → fallback ke **GC=F**; tetap dukung override via Sheet `gold_xauusd_override`.
- **Stocks**: default `currency="IDR"` saat `fast_info.currency` hilang.
- **Requirements**: tambah `requests` untuk panggil API publik.

Tetap tersedia:
- `/healthz`, `/diag`
- Watchlist & mutual funds via Google Sheets.

> Catatan: Layanan publik (exchangerate.host, CoinGecko) punya rate limit. Bot akan menampilkan pesan error yang jelas jika keduanya tidak tersedia sementara.


- **Stocks fallback**: direct Yahoo Chart API if yfinance empty (helps for .JK tickers on some regions).

- **FX override**: set `usd_idr_override` in `settings` tab to force USDIDR rate if all providers fail.

- `/gold` sekarang menampilkan **harga per gram** (USD/gram & IDR/gram).
