# ABD Ekonomik Takvimi

Stablex için hazırlanan, ABD ekonomik takvim etkinliklerini (actual/
beklenti/önceki) gösteren sekmeli statik site. Veri her gün GitHub
Actions ile otomatik güncellenir.

- **Canlı site:** GitHub Pages üzerinden yayınlanır (bkz. repo ayarları
  → Pages).
- **Veri kaynağı:** TradingView'in genel ekonomik takvim API'si
  (`economic-calendar.tradingview.com/events`) — investing.com yerine
  bu kullanılıyor çünkü investing.com Cloudflare ile otomasyonu
  engelliyor. Detaylar için `scraper.py`'nin başındaki not.
- **Otomatik güncelleme:** `.github/workflows/update-calendar.yml` her
  gün 06:00 UTC'de `scraper.py`'yi çalıştırıp `data/economic_calendar.json`
  değiştiyse otomatik commit+push eder. Actions sekmesinden elle de
  tetiklenebilir ("Run workflow").

## Yerel çalıştırma

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scraper.py
open index.html   # ya da: python -m http.server, sonra tarayıcıdan aç
```

## ⚠️ Not

TradingView API'si resmi/dokümante bir public API değil — kişisel/iç
kullanım için kullanılıyor, çıktı üçüncü taraflara satılmamalı/
dağıtılmamalı.
