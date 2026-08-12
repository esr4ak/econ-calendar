# ABD Ekonomik Takvimi — Stablex

Stablex resmi sitesine entegrasyon için hazırlanan, yalnızca **yüksek
etkili (3/3)** ABD ekonomik takvim etkinliklerini gösteren, Stablex
marka kimliğiyle tasarlanmış statik site. Her etkinlik kartı; gösterge
açıklaması, tipik piyasa etkisi ve (veri açıklandıysa) kural tabanlı bir
"Anlık Durum Özeti" içerir.

- **Canlı site:** GitHub Pages üzerinden yayınlanır (bkz. repo ayarları
  → Pages) — https://esr4ak.github.io/econ-calendar/
- **Veri kaynağı:** TradingView'in genel ekonomik takvim API'si
  (`economic-calendar.tradingview.com/events`) — investing.com yerine
  bu kullanılıyor çünkü investing.com Cloudflare ile otomasyonu
  engelliyor. Detaylar için `scraper.py`'nin başındaki not.
- **Filtre:** Sadece `impact = 3` (Yüksek/3-yıldız) etkinlikler
  gösteriliyor — `scraper.py` içindeki `MIN_IMPACT` sabitiyle değiştirilebilir.
- **Türkçe çeviri:** `translations.py` — 250+ gösterge başlığı için sabit
  sözlük, bilinmeyen başlıklarda İngilizce'ye güvenli düşüş yapar.
- **Gösterge açıklamaları + özet motoru:** `event_info.py` — her yüksek
  etkili gösterge için sabit "Ne Anlama Gelir?" / "Piyasa Etkisi"
  metinleri, ve actual/forecast/previous karşılaştırmasına dayanan
  **kural tabanlı** (LLM KULLANMAZ) "Anlık Durum Özeti" cümle üretici.
  Neden LLM değil: aynı girdi her zaman aynı, önceden gözden geçirilmiş
  metni üretir; resmi bir banka kuruluşu sitesinde yanlış/yanıltıcı bir
  AI yorumunun yayınlanma riski taşımaz. Detaylar dosyanın başındaki notta.
- **Otomatik güncelleme:** `.github/workflows/update-calendar.yml` günde
  3 kez — TR saatiyle **12:00, 17:00, 00:00** (UTC 09:00/14:00/21:00) —
  `scraper.py`'yi çalıştırıp `data/economic_calendar.json` değiştiyse
  otomatik commit+push eder. Actions sekmesinden elle de tetiklenebilir
  ("Run workflow").
- **Mobil uyumlu:** 640px altında kartlar tek sütuna düşer, yatay
  kaydırma yoktur.

## Yerel çalıştırma

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scraper.py
open index.html   # ya da: python -m http.server, sonra tarayıcıdan aç
```

## ⚠️ Notlar

- TradingView API'si resmi/dokümante bir public API değil — kişisel/iç
  kullanım için kullanılıyor, çıktı üçüncü taraflara satılmamalı/
  dağıtılmamalı.
- **"Ne Anlama Gelir?" / "Piyasa Etkisi" / "Anlık Durum Özeti"**
  metinleri bilgilendirme amaçlıdır, **yatırım tavsiyesi değildir**.
  Resmi siteye eklenmeden önce Stablex'in finans/hukuk/uyum ekibinin bu
  metinleri (`event_info.py`) gözden geçirmesi ve SPK mevzuatı
  açısından uygunluğunu teyit etmesi önerilir.
- Logo bloğu şu an düz metin ("STABLEX") — resmi siteye entegre
  edilmeden önce gerçek logo dosyasıyla değiştirilmelidir.
