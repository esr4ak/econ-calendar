"""
ABD Ekonomik Takvimi - TradingView Economic Calendar API istemcisi
====================================================================

ONCEKI YAKLASIM VE NEDEN DEGISTI: Ilk versiyon investing.com'u Playwright
ile tarayarak kazidiyordu. investing.com, Cloudflare arkasinda ve
headless/otomasyon isaretleri tasiyan tarayicilari 403 ile engelliyor;
stealth/gercek-Chrome denemelerine ragmen tutarli calismadi.

Bunun yerine, getmidas.com/ekonomik-takvim/ gibi sitelerin de kullandigi
TradingView'in **genel/herkese acik ekonomik takvim API'sine** dogrudan
istek atiliyor. Bu API:
  - Cloudflare bot korumasi ARKASINDA DEGIL - sadece Origin/Referer/
    User-Agent header'lari beklenen bir istekle 200 donuyor, JS render'a
    ya da tarayici otomasyonuna hic gerek yok (duz `requests` yeterli).
  - API key/kimlik dogrulama gerektirmiyor.
  - country filtresi (countries=US) ve tarih araligi (from/to, ISO 8601
    UTC) destekliyor.
  - actual/forecast/previous, onem derecesi (importance), birim (unit:
    '%' vb.) ve olcek (scale: K/M/B/T) bilgisini yapili sekilde veriyor
    - investing.com'un HTML'inden metin ayristirmaktan cok daha saglam.
  - Kapsam investing.com'a esdeger ya da daha genis: Agustos 2026 icin
    305 ABD etkinligi donuyor (investing.com taramasinda 232 idi).

Endpoint, tradingview.com/economic-calendar/ sayfasi acikken tarayicinin
Network sekmesinde XHR olarak gozlemlenerek bulundu:
    https://economic-calendar.tradingview.com/events
        ?from=<ISO8601Z>&to=<ISO8601Z>&countries=US

ONEMLI (yasal not): Bu, TradingView'in kendi sitesinde kullandigi genel
bir XHR endpoint'idir, resmi/dokumante edilmis bir public API degildir -
istedigi an degisebilir ya da erisimi kisitlanabilir. Bu script SADECE
kisisel/ic kullanim icin yazilmistir; ciktiyi yeniden dagitmayin/satmayin.

Kullanim:
    pip install -r requirements.txt
    python scraper.py

Cikti:
    data/economic_calendar.json
"""

from __future__ import annotations

import calendar
import json
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import requests

from translations import translate_title

API_URL = "https://economic-calendar.tradingview.com/events"
OUTPUT_PATH = Path(__file__).parent / "data" / "economic_calendar.json"

# API'nin beklendigi gibi 200 donmesi icin bu header'lar sart - Origin/
# Referer olmadan 403 veriyor (bkz. modul dokstring'i).
HEADERS = {
    "Origin": "https://www.tradingview.com",
    "Referer": "https://www.tradingview.com/",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

DISPLAY_TZ = ZoneInfo("America/New_York")  # ABD takvimi icin dogal secim

IMPORTANCE_TO_IMPACT = {1: 3, 0: 2, -1: 1}
IMPACT_LABELS = {0: "None", 1: "Low", 2: "Medium", 3: "High"}


@dataclass
class CalendarEvent:
    datetime_raw: str
    date: str
    time: str
    impact: int
    impact_label: str
    event: str
    actual: str
    forecast: str
    previous: str


def log(msg: str) -> None:
    print(f"[scraper] {msg}", flush=True)


def format_value(raw: Optional[float], unit: Optional[str], scale: Optional[str]) -> str:
    """TradingView'in sayisal actual/forecast/previous degerini
    investing.com'daki gibi okunur bir metne cevirir: 0.3 + unit='%' ->
    '0.3%'; 80 + scale='K' -> '80K'. Deger yoksa bos string doner."""
    if raw is None:
        return ""
    if isinstance(raw, float) and raw.is_integer():
        text = str(int(raw))
    else:
        text = str(raw)
    if unit == "%":
        return f"{text}%"
    if scale:
        return f"{text}{scale}"
    return text


def transform(raw_events: list[dict]) -> list[CalendarEvent]:
    events: list[CalendarEvent] = []
    for ev in raw_events:
        dt_utc = datetime.fromisoformat(ev["date"].replace("Z", "+00:00"))
        dt_local = dt_utc.astimezone(DISPLAY_TZ)
        importance = int(ev.get("importance") or 0)
        impact = IMPORTANCE_TO_IMPACT.get(importance, 2)
        unit = ev.get("unit")
        scale = ev.get("scale")
        events.append(
            CalendarEvent(
                datetime_raw=dt_local.strftime("%A, %B %d, %Y %H:%M"),
                date=dt_local.date().isoformat(),
                time=dt_local.strftime("%H:%M"),
                impact=impact,
                impact_label=IMPACT_LABELS.get(impact, "Unknown"),
                event=translate_title(ev.get("title") or ""),
                actual=format_value(ev.get("actual"), unit, scale),
                forecast=format_value(ev.get("forecast"), unit, scale),
                previous=format_value(ev.get("previous"), unit, scale),
            )
        )
    events.sort(key=lambda e: (e.date, e.time))
    return events


def fetch_range(start: date, end: date, country: str = "US", retries: int = 3) -> list[dict]:
    """[start, end] (dahil, ABD Dogu saatiyle) tarih araligi icin
    TradingView'den ham etkinlik listesini ceker. API sorgusu UTC
    bekliyor ama gosterim DISPLAY_TZ'de (America/New_York) yapiliyor;
    UTC ile Dogu saati arasindaki 4-5 saatlik farktan dolayi ayin/
    haftanin son gunundeki gec saatli bir etkinlik (orn. 23:00 Dogu
    saati = ertesi gun ~03:00 UTC) tam sinirda sorgulanirsa disarida
    kalabilirdi. Bunu onlemek icin UTC sorgu penceresini her iki
    yonden 1'er gun genisletiyoruz; sonuc listesi zaten Dogu saatine
    cevrilip transform() icinde dogru tarihe atanacagi icin fazladan
    gelen komsu gun etkinlikleri scrape_range() tarafinda filtrelenir."""
    from_iso = datetime.combine(start - timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    to_dt = datetime.combine(end + timedelta(days=2), datetime.min.time(), tzinfo=timezone.utc)
    to_iso = to_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    label = f"{start.isoformat()} -> {end.isoformat()}"
    params = {"from": from_iso, "to": to_iso, "countries": country}

    for attempt in range(1, retries + 1):
        try:
            log(f"veri cekiliyor: {label} (deneme {attempt})")
            resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            payload = resp.json()
            if payload.get("status") != "ok":
                raise RuntimeError(f"beklenmeyen yanit: {payload}")
            events = payload.get("result", [])
            log(f"{len(events)} etkinlik bulundu ({label})")
            return events
        except Exception as exc:
            log(f"hata ({label}), deneme {attempt}: {exc}")
            time.sleep(2 * attempt)
    log(f"vazgeciliyor: {label} icin veri cekilemedi")
    return []


def scrape_range(start: date, end: date) -> list[dict]:
    """fetch_range UTC sinirinda tasma payi biraktigi icin (bkz. o
    fonksiyonun docstring'i) donen etkinlikler DISPLAY_TZ'deki yerel
    tarihe gore [start, end] disina tasabilir - burada kesin olarak
    filtreleniyor, boylece bir ayin/haftanin verisi komsu ayin/haftanin
    etkinliklerini icermez."""
    raw_events = fetch_range(start, end)
    events = transform(raw_events)
    in_range = [e for e in events if start.isoformat() <= e.date <= end.isoformat()]
    return [asdict(e) for e in in_range]


# ---------------------------------------------------------------------------
# Tarih araligi yardimcilari
# ---------------------------------------------------------------------------
def month_bounds(year: int, month: int) -> tuple[date, date]:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def week_chunks(start: date, end: date, min_days: int = 4) -> list[tuple[date, date]]:
    """Ay siniri Pazartesi-Pazar hizasina uymadigi icin ilk/son parca
    genelde 1-3 gunluk kaliyor (orn. ay Cumartesi baslarsa). Bu kucuk
    kalintilari komsu haftaya birlestirerek daha dengeli, tek basina
    'bos' gorunmeyen araliklar elde ediyoruz (min_days'ten kisa parca
    tek basina kalmaz)."""
    chunks = []
    cursor = start
    while cursor <= end:
        week_end = min(cursor + timedelta(days=6 - cursor.weekday()), end)
        chunks.append([cursor, week_end])
        cursor = week_end + timedelta(days=1)

    def days(chunk: list) -> int:
        return (chunk[1] - chunk[0]).days + 1

    if len(chunks) > 1 and days(chunks[0]) < min_days:
        first = chunks.pop(0)
        chunks[0][0] = first[0]
    if len(chunks) > 1 and days(chunks[-1]) < min_days:
        last = chunks.pop()
        chunks[-1][1] = last[1]

    return [(c[0], c[1]) for c in chunks]


def previous_months(reference: date, count: int) -> list[tuple[int, int]]:
    results = []
    y, m = reference.year, reference.month
    for _ in range(count):
        m -= 1
        if m == 0:
            m = 12
            y -= 1
        results.append((y, m))
    return results


# ---------------------------------------------------------------------------
# Veri seti insasi
# ---------------------------------------------------------------------------
def build_dataset(today: date, past_months_count: int = 2) -> dict:
    dataset: dict = {
        "generated_at": today.isoformat(),
        "country": "United States",
        "current_month": {},
        "current_month_weekly": {},
        "past_months": {},
    }

    cur_start, cur_end = month_bounds(today.year, today.month)
    month_key = cur_start.strftime("%Y-%m")
    dataset["current_month"][month_key] = scrape_range(cur_start, cur_end)

    for idx, (w_start, w_end) in enumerate(week_chunks(cur_start, cur_end), start=1):
        week_key = f"week_{idx}"
        dataset["current_month_weekly"][week_key] = {
            "label": f"{idx}. Hafta ({w_start.strftime('%d %b')} - {w_end.strftime('%d %b')})",
            "start": w_start.isoformat(),
            "end": w_end.isoformat(),
            "events": scrape_range(w_start, w_end),
        }

    for (y, m) in previous_months(today, past_months_count):
        p_start, p_end = month_bounds(y, m)
        p_key = p_start.strftime("%Y-%m")
        dataset["past_months"][p_key] = scrape_range(p_start, p_end)

    return dataset


def run(today: Optional[date] = None, past_months_count: int = 2) -> None:
    today = today or date.today()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    dataset = build_dataset(today, past_months_count=past_months_count)

    OUTPUT_PATH.write_text(json.dumps(dataset, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"JSON kaydedildi: {OUTPUT_PATH}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ABD ekonomik takvimi - TradingView API istemcisi")
    parser.add_argument(
        "--past-months",
        type=int,
        default=2,
        help="Kac gecmis ay taransin (varsayilan: 2)",
    )
    args = parser.parse_args()

    run(past_months_count=args.past_months)
