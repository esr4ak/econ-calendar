"""
ABD ekonomik takvim etkinlik basliklarinin Turkce cevirileri.

TradingView API'si (ve tr.tradingview.com'un kendi Turkce sitesi bile)
etkinlik basliklarini Turkce'ye cevirmiyor - sadece ulke isimleri
yerellestiriliyor, gostergelerin adlari her zaman Ingilizce geliyor
(tarayicida dogrulandi: ayni /events endpoint'i, locale parametresi
etkisiz). Bu yuzden bilinen basliklar icin sabit bir sozluk tutuyoruz.

TITLE_TR: tam eslesen basliklar icin dogrudan sozluk lookup'i.
translate_title(): once TITLE_TR'ye bakar, sonra "Fed <Isim> Speech"
gibi yeni Fed konusmaci isimlerini de kapsayan birkac genel desen dener
(yeni bir Fed uyesi konusma yaptiginda sozlugu guncellemeye gerek
kalmasin diye), hicbiri eslesmezse ORIJINAL INGILIZCE basligi dondurur
(veri kaybi olmasin - ceviri eksikse sessizce bos gostermek yerine
Ingilizce goster).
"""

from __future__ import annotations

import re

TITLE_TR: dict[str, str] = {
    # --- Hazine ihaleleri (bill/note/bond/TIPS/FRN) ---
    "4-Week Bill Auction": "4 Haftalık Bono İhalesi",
    "6-Week Bill Auction": "6 Haftalık Bono İhalesi",
    "8-Week Bill Auction": "8 Haftalık Bono İhalesi",
    "17-Week Bill Auction": "17 Haftalık Bono İhalesi",
    "3-Month Bill Auction": "3 Aylık Bono İhalesi",
    "6-Month Bill Auction": "6 Aylık Bono İhalesi",
    "52-Week Bill Auction": "52 Haftalık Bono İhalesi",
    "2-Year Note Auction": "2 Yıllık Tahvil İhalesi",
    "3-Year Note Auction": "3 Yıllık Tahvil İhalesi",
    "5-Year Note Auction": "5 Yıllık Tahvil İhalesi",
    "7-Year Note Auction": "7 Yıllık Tahvil İhalesi",
    "10-Year Note Auction": "10 Yıllık Tahvil İhalesi",
    "2-Year FRN Auction": "2 Yıllık Değişken Faizli Tahvil İhalesi",
    "20-Year Bond Auction": "20 Yıllık Tahvil İhalesi",
    "30-Year Bond Auction": "30 Yıllık Tahvil İhalesi",
    "5-Year TIPS Auction": "5 Yıllık Enflasyona Endeksli Tahvil İhalesi",
    "10-Year TIPS Auction": "10 Yıllık Enflasyona Endeksli Tahvil İhalesi",
    "30-Year TIPS Auction": "30 Yıllık Enflasyona Endeksli Tahvil İhalesi",
    "Treasury Refunding Announcement": "Hazine Refinansman Duyurusu",
    "Treasury Refunding Financing Estimates": "Hazine Refinansman Finansman Tahminleri",

    # --- Mortgage / konut ---
    "15-Year Mortgage Rate": "15 Yıllık Mortgage Faizi",
    "30-Year Mortgage Rate": "30 Yıllık Mortgage Faizi",
    "MBA 30-Year Mortgage Rate": "MBA 30 Yıllık Mortgage Faizi",
    "MBA Mortgage Applications": "MBA Mortgage Başvuruları",
    "MBA Mortgage Market Index": "MBA Mortgage Piyasası Endeksi",
    "MBA Mortgage Refinance Index": "MBA Mortgage Yeniden Finansman Endeksi",
    "MBA Purchase Index": "MBA Konut Alım Endeksi",
    "Housing Starts": "Konut Başlangıçları",
    "Housing Starts MoM": "Konut Başlangıçları (Aylık)",
    "Building Permits Final": "İnşaat İzinleri (Kesin)",
    "Building Permits Prel": "İnşaat İzinleri (Öncül)",
    "Building Permits MoM Final": "İnşaat İzinleri (Aylık, Kesin)",
    "Building Permits MoM Prel": "İnşaat İzinleri (Aylık, Öncül)",
    "Existing Home Sales": "İkinci El Konut Satışları",
    "Existing Home Sales MoM": "İkinci El Konut Satışları (Aylık)",
    "New Home Sales": "Yeni Konut Satışları",
    "New Home Sales MoM": "Yeni Konut Satışları (Aylık)",
    "Pending Home Sales MoM": "Bekleyen Konut Satışları (Aylık)",
    "Pending Home Sales YoY": "Bekleyen Konut Satışları (Yıllık)",
    "NAHB Housing Market Index": "NAHB Konut Piyasası Endeksi",
    "House Price Index": "Konut Fiyat Endeksi",
    "House Price Index MoM": "Konut Fiyat Endeksi (Aylık)",
    "House Price Index YoY": "Konut Fiyat Endeksi (Yıllık)",
    "S&P/Case-Shiller Home Price MoM": "S&P/Case-Shiller Konut Fiyat Endeksi (Aylık)",
    "S&P/Case-Shiller Home Price YoY": "S&P/Case-Shiller Konut Fiyat Endeksi (Yıllık)",

    # --- Enflasyon (TÜFE/ÜFE/PCE) ---
    "CPI": "TÜFE",
    "CPI s.a": "TÜFE (Mevsimsellikten Arındırılmış)",
    "Inflation Rate MoM": "TÜFE (Aylık)",
    "Inflation Rate YoY": "TÜFE (Yıllık)",
    "Core Inflation Rate MoM": "Çekirdek TÜFE (Aylık)",
    "Core Inflation Rate YoY": "Çekirdek TÜFE (Yıllık)",
    "PPI": "ÜFE",
    "PPI MoM": "ÜFE (Aylık)",
    "PPI YoY": "ÜFE (Yıllık)",
    "Core PPI MoM": "Çekirdek ÜFE (Aylık)",
    "Core PPI YoY": "Çekirdek ÜFE (Yıllık)",
    "PPI Ex Food, Energy and Trade MoM": "ÜFE (Gıda, Enerji ve Ticaret Hariç, Aylık)",
    "PPI Ex Food, Energy and Trade YoY": "ÜFE (Gıda, Enerji ve Ticaret Hariç, Yıllık)",
    "Core PCE Price Index MoM": "Çekirdek PCE Fiyat Endeksi (Aylık)",
    "Core PCE Price Index YoY": "Çekirdek PCE Fiyat Endeksi (Yıllık)",
    "PCE Price Index MoM": "PCE Fiyat Endeksi (Aylık)",
    "PCE Price Index YoY": "PCE Fiyat Endeksi (Yıllık)",
    "Core PCE Prices QoQ Adv": "Çekirdek PCE Fiyatları (Çeyreklik, Öncül)",
    "Core PCE Prices QoQ 2nd Est": "Çekirdek PCE Fiyatları (Çeyreklik, 2. Tahmin)",
    "Core PCE Prices QoQ Final": "Çekirdek PCE Fiyatları (Çeyreklik, Kesin)",
    "PCE Prices QoQ Adv": "PCE Fiyatları (Çeyreklik, Öncül)",
    "PCE Prices QoQ 2nd Est": "PCE Fiyatları (Çeyreklik, 2. Tahmin)",
    "PCE Prices QoQ Final": "PCE Fiyatları (Çeyreklik, Kesin)",
    "Consumer Inflation Expectations": "Tüketici Enflasyon Beklentileri",
    "Used Car Prices MoM": "İkinci El Araç Fiyatları (Aylık)",
    "Used Car Prices YoY": "İkinci El Araç Fiyatları (Yıllık)",
    "Import Prices MoM": "İthalat Fiyatları (Aylık)",
    "Import Prices YoY": "İthalat Fiyatları (Yıllık)",
    "Export Prices MoM": "İhracat Fiyatları (Aylık)",
    "Export Prices YoY": "İhracat Fiyatları (Yıllık)",

    # --- Istihdam ---
    "Non Farm Payrolls": "Tarım Dışı İstihdam",
    "Non Farm Payrolls Annual Revision Prel": "Tarım Dışı İstihdam Yıllık Revizyon (Öncül)",
    "Nonfarm Payrolls Private": "Özel Sektör Tarım Dışı İstihdam",
    "Government Payrolls": "Kamu İstihdamı",
    "Manufacturing Payrolls": "İmalat Sektörü İstihdamı",
    "ADP Employment Change": "ADP İstihdam Değişimi",
    "ADP Employment Change Weekly": "ADP Haftalık İstihdam Değişimi",
    "Average Hourly Earnings MoM": "Ortalama Saatlik Kazançlar (Aylık)",
    "Average Hourly Earnings YoY": "Ortalama Saatlik Kazançlar (Yıllık)",
    "Average Weekly Hours": "Ortalama Haftalık Çalışma Saatleri",
    "Unemployment Rate": "İşsizlik Oranı",
    "U-6 Unemployment Rate": "Geniş Tanımlı İşsizlik Oranı (U-6)",
    "Participation Rate": "İşgücüne Katılım Oranı",
    "Initial Jobless Claims": "Haftalık İşsizlik Başvuruları",
    "Continuing Jobless Claims": "Devam Eden İşsizlik Başvuruları",
    "Jobless Claims 4-week Average": "İşsizlik Başvuruları (4 Haftalık Ortalama)",
    "Challenger Job Cuts": "Challenger İşten Çıkarma Raporu",
    "JOLTs Job Openings": "JOLTs Açık İş Sayısı",
    "JOLTs Job Quits": "JOLTs İşten Ayrılma Sayısı",
    "Nonfarm Productivity QoQ Final": "Tarım Dışı Verimlilik (Çeyreklik, Kesin)",
    "Nonfarm Productivity QoQ Prel": "Tarım Dışı Verimlilik (Çeyreklik, Öncül)",
    "Unit Labour Costs QoQ Final": "Birim İşgücü Maliyetleri (Çeyreklik, Kesin)",
    "Unit Labour Costs QoQ Prel": "Birim İşgücü Maliyetleri (Çeyreklik, Öncül)",
    "Employment Cost Index QoQ": "İstihdam Maliyet Endeksi (Çeyreklik)",
    "Employment Cost - Wages QoQ": "İstihdam Maliyeti - Ücretler (Çeyreklik)",
    "Employment Cost - Benefits QoQ": "İstihdam Maliyeti - Yan Haklar (Çeyreklik)",

    # --- GSYH / buyume ---
    "GDP Growth Rate QoQ Adv": "GSYH Büyümesi (Çeyreklik, Öncül)",
    "GDP Growth Rate QoQ 2nd Est": "GSYH Büyümesi (Çeyreklik, 2. Tahmin)",
    "GDP Growth Rate QoQ Final": "GSYH Büyümesi (Çeyreklik, Kesin)",
    "GDP Price Index QoQ Adv": "GSYH Fiyat Endeksi (Çeyreklik, Öncül)",
    "GDP Price Index QoQ 2nd Est": "GSYH Fiyat Endeksi (Çeyreklik, 2. Tahmin)",
    "GDP Price Index QoQ Final": "GSYH Fiyat Endeksi (Çeyreklik, Kesin)",
    "GDP Sales QoQ Adv": "GSYH Satışları (Çeyreklik, Öncül)",
    "GDP Sales QoQ 2nd Est": "GSYH Satışları (Çeyreklik, 2. Tahmin)",
    "GDP Sales QoQ Final": "GSYH Satışları (Çeyreklik, Kesin)",
    "Corporate Profits QoQ Prel": "Şirket Kârları (Çeyreklik, Öncül)",
    "Corporate Profits QoQ Final": "Şirket Kârları (Çeyreklik, Kesin)",
    "Real Consumer Spending QoQ Adv": "Reel Tüketici Harcamaları (Çeyreklik, Öncül)",
    "Real Consumer Spending QoQ 2nd Est": "Reel Tüketici Harcamaları (Çeyreklik, 2. Tahmin)",
    "Real Consumer Spending QoQ Final": "Reel Tüketici Harcamaları (Çeyreklik, Kesin)",
    "Personal Income MoM": "Kişisel Gelir (Aylık)",
    "Personal Spending MoM": "Kişisel Harcamalar (Aylık)",
    "Real Personal Spending MoM": "Reel Kişisel Harcamalar (Aylık)",

    # --- ISM / PMI ---
    "ISM Manufacturing PMI": "ISM İmalat PMI",
    "ISM Manufacturing Prices": "ISM İmalat Fiyatlar Endeksi",
    "ISM Manufacturing Employment": "ISM İmalat İstihdam Endeksi",
    "ISM Manufacturing New Orders": "ISM İmalat Yeni Siparişler Endeksi",
    "ISM Services PMI": "ISM Hizmet PMI",
    "ISM Services Business Activity": "ISM Hizmet İş Faaliyeti Endeksi",
    "ISM Services Employment": "ISM Hizmet İstihdam Endeksi",
    "ISM Services New Orders": "ISM Hizmet Yeni Siparişler Endeksi",
    "ISM Services Prices": "ISM Hizmet Fiyatlar Endeksi",
    "S&P Global Manufacturing PMI Flash": "S&P Global İmalat PMI (Öncü)",
    "S&P Global Manufacturing PMI Final": "S&P Global İmalat PMI (Nihai)",
    "S&P Global Services PMI Flash": "S&P Global Hizmet PMI (Öncü)",
    "S&P Global Services PMI Final": "S&P Global Hizmet PMI (Nihai)",
    "S&P Global Composite PMI Flash": "S&P Global Bileşik PMI (Öncü)",
    "S&P Global Composite PMI Final": "S&P Global Bileşik PMI (Nihai)",
    "Chicago PMI": "Chicago PMI",

    # --- Perakende ---
    "Retail Sales MoM": "Perakende Satışlar (Aylık)",
    "Retail Sales YoY": "Perakende Satışlar (Yıllık)",
    "Retail Sales Control Group MoM": "Perakende Satışlar Kontrol Grubu (Aylık)",
    "Retail Sales Ex Autos MoM": "Perakende Satışlar (Otomobil Hariç, Aylık)",
    "Retail Sales Ex Gas/Autos MoM": "Perakende Satışlar (Benzin/Otomobil Hariç, Aylık)",
    "Retail Inventories Ex Autos MoM": "Perakende Stokları (Otomobil Hariç, Aylık)",
    "Retail Inventories Ex Autos MoM Adv": "Perakende Stokları (Otomobil Hariç, Aylık, Öncül)",

    # --- Sanayi / uretim ---
    "Industrial Production MoM": "Sanayi Üretimi (Aylık)",
    "Industrial Production YoY": "Sanayi Üretimi (Yıllık)",
    "Manufacturing Production MoM": "İmalat Üretimi (Aylık)",
    "Manufacturing Production YoY": "İmalat Üretimi (Yıllık)",
    "Capacity Utilization": "Kapasite Kullanım Oranı",
    "Factory Orders MoM": "Fabrika Siparişleri (Aylık)",
    "Factory Orders ex Transportation": "Fabrika Siparişleri (Ulaşım Hariç)",
    "Durable Goods Orders MoM": "Dayanıklı Mal Siparişleri (Aylık)",
    "Durable Goods Orders Ex Transp MoM": "Dayanıklı Mal Siparişleri (Ulaşım Hariç, Aylık)",
    "Durable Goods Orders ex Defense MoM": "Dayanıklı Mal Siparişleri (Savunma Hariç, Aylık)",
    "Non Defense Goods Orders Ex Air": "Savunma Dışı Mal Siparişleri (Uçak Hariç)",
    "Business Inventories MoM": "İşletme Stokları (Aylık)",
    "Wholesale Inventories MoM": "Toptan Satış Stokları (Aylık)",
    "Wholesale Inventories MoM Adv": "Toptan Satış Stokları (Aylık, Öncül)",
    "Construction Spending MoM": "İnşaat Harcamaları (Aylık)",
    "Total Vehicle Sales": "Toplam Araç Satışları",

    # --- Dis ticaret / odemeler dengesi ---
    "Balance of Trade": "Dış Ticaret Dengesi",
    "Exports": "İhracat",
    "Imports": "İthalat",
    "Goods Trade Balance Adv": "Mal Ticareti Dengesi (Öncül)",
    "Current Account": "Cari İşlemler Dengesi",
    "Net Long-term TIC Flows": "Net Uzun Vadeli TIC Sermaye Akışları",
    "Overall Net Capital Flows": "Toplam Net Sermaye Akışları",
    "Foreign Bond Investment": "Yabancı Tahvil Yatırımı",

    # --- Bolgesel Fed endeksleri ---
    "Chicago Fed National Activity Index": "Chicago Fed Ulusal Faaliyet Endeksi",
    "Dallas Fed Manufacturing Index": "Dallas Fed İmalat Endeksi",
    "Dallas Fed Services Index": "Dallas Fed Hizmet Endeksi",
    "Dallas Fed Services Revenues Index": "Dallas Fed Hizmet Gelirleri Endeksi",
    "Kansas Fed Composite Index": "Kansas Fed Bileşik Endeksi",
    "Kansas Fed Manufacturing Index": "Kansas Fed İmalat Endeksi",
    "NY Empire State Manufacturing Index": "New York Empire State İmalat Endeksi",
    "NY Fed Services Activity Index": "New York Fed Hizmet Faaliyet Endeksi",
    "Philadelphia Fed Manufacturing Index": "Philadelphia Fed İmalat Endeksi",
    "Philly Fed Business Conditions": "Philly Fed İş Koşulları Endeksi",
    "Philly Fed CAPEX Index": "Philly Fed Yatırım Harcamaları Endeksi",
    "Philly Fed Employment": "Philly Fed İstihdam Endeksi",
    "Philly Fed New Orders": "Philly Fed Yeni Siparişler Endeksi",
    "Philly Fed Prices Paid": "Philly Fed Ödenen Fiyatlar Endeksi",
    "Richmond Fed Manufacturing Index": "Richmond Fed İmalat Endeksi",
    "Richmond Fed Manufacturing Shipments Index": "Richmond Fed İmalat Sevkiyat Endeksi",
    "Richmond Fed Services Revenues Index": "Richmond Fed Hizmet Gelirleri Endeksi",
    "LMI Logistics Managers Index": "LMI Lojistik Yöneticileri Endeksi",

    # --- Guven / beklenti endeksleri ---
    "CB Consumer Confidence": "Conference Board Tüketici Güveni",
    "CB Leading Index MoM": "Conference Board Öncü Göstergeler Endeksi (Aylık)",
    "Michigan Consumer Sentiment Final": "Michigan Tüketici Güveni (Kesin)",
    "Michigan Consumer Sentiment Prel": "Michigan Tüketici Güveni (Öncül)",
    "Michigan Consumer Expectations Final": "Michigan Tüketici Beklentileri (Kesin)",
    "Michigan Consumer Expectations Prel": "Michigan Tüketici Beklentileri (Öncül)",
    "Michigan Current Conditions Final": "Michigan Mevcut Koşullar Endeksi (Kesin)",
    "Michigan Current Conditions Prel": "Michigan Mevcut Koşullar Endeksi (Öncül)",
    "Michigan Inflation Expectations Final": "Michigan Enflasyon Beklentileri (Kesin)",
    "Michigan Inflation Expectations Prel": "Michigan Enflasyon Beklentileri (Öncül)",
    "Michigan 5 Year Inflation Expectations Final": "Michigan 5 Yıllık Enflasyon Beklentileri (Kesin)",
    "Michigan 5 Year Inflation Expectations Prel": "Michigan 5 Yıllık Enflasyon Beklentileri (Öncül)",
    "NFIB Business Optimism Index": "NFIB İş Dünyası İyimserlik Endeksi",
    "RCM/TIPP Economic Optimism Index": "RCM/TIPP Ekonomik İyimserlik Endeksi",
    "Redbook YoY": "Redbook Perakende Satışları (Yıllık)",

    # --- Fed / para politikasi ---
    "Fed Interest Rate Decision": "Fed Faiz Kararı",
    "Fed Press Conference": "Fed Basın Toplantısı",
    "FOMC Minutes": "FOMC Toplantı Tutanakları",
    "FOMC Economic Projections": "FOMC Ekonomik Projeksiyonları",
    "Fed Beige Book": "Fed Bej Kitap Raporu",
    "Fed Balance Sheet": "Fed Bilançosu",
    "Fed Bank Stress Test Results": "Fed Banka Stres Testi Sonuçları",
    "Interest Rate Projection - Current": "Faiz Oranı Projeksiyonu (Cari Yıl)",
    "Interest Rate Projection - 1st Yr": "Faiz Oranı Projeksiyonu (1. Yıl)",
    "Interest Rate Projection - 2nd Yr": "Faiz Oranı Projeksiyonu (2. Yıl)",
    "Interest Rate Projection - Longer": "Faiz Oranı Projeksiyonu (Uzun Vadeli)",
    "Fed Chair Warsh Speech": "Fed Başkanı Warsh Konuşması",
    "Fed Chair Warsh Testimony": "Fed Başkanı Warsh Kongre İfadesi",
    "Jackson Hole Symposium": "Jackson Hole Sempozyumu",
    "Loan Officer Survey": "Kredi Görevlileri Anketi",

    # --- Para / kredi / butce ---
    "Consumer Credit Change": "Tüketici Kredisi Değişimi",
    "Money Supply": "Para Arzı",
    "Total Household Debt": "Toplam Hane Halkı Borcu",
    "Monthly Budget Statement": "Aylık Bütçe Dengesi",

    # --- Enerji / emtia ---
    "API Crude Oil Stock Change": "API Ham Petrol Stok Değişimi",
    "EIA Crude Oil Stocks Change": "EIA Ham Petrol Stok Değişimi",
    "EIA Crude Oil Imports Change": "EIA Ham Petrol İthalatı Değişimi",
    "EIA Cushing Crude Oil Stocks Change": "EIA Cushing Ham Petrol Stok Değişimi",
    "EIA Distillate Fuel Production Change": "EIA Distilat Yakıt Üretimi Değişimi",
    "EIA Distillate Stocks Change": "EIA Distilat Stok Değişimi",
    "EIA Gasoline Production Change": "EIA Benzin Üretimi Değişimi",
    "EIA Gasoline Stocks Change": "EIA Benzin Stok Değişimi",
    "EIA Heating Oil Stocks Change": "EIA Isıtma Yağı Stok Değişimi",
    "EIA Natural Gas Stocks Change": "EIA Doğal Gaz Stok Değişimi",
    "EIA Refinery Crude Runs Change": "EIA Rafineri Ham Petrol İşleme Değişimi",
    "EIA Short-Term Energy Outlook": "EIA Kısa Vadeli Enerji Görünümü Raporu",
    "Baker Hughes Oil Rig Count": "Baker Hughes Petrol Kulesi Sayısı",
    "Baker Hughes Total Rigs Count": "Baker Hughes Toplam Kule Sayısı",
    "WASDE Report": "WASDE Tarım Raporu",
    "NOPA Crush Report": "NOPA Soya Fasulyesi İşleme Raporu",
    "Quarterly Grain Stocks - Corn": "Üç Aylık Tahıl Stokları - Mısır",
    "Quarterly Grain Stocks - Soy": "Üç Aylık Tahıl Stokları - Soya",
    "Quarterly Grain Stocks - Wheat": "Üç Aylık Tahıl Stokları - Buğday",

    # --- NY Fed islemleri ---
    "NY Fed Bill Purchases 1 to 4 months": "New York Fed Bono Alımları (1-4 Ay)",
    "NY Fed Bill Purchases 4 to 12 months": "New York Fed Bono Alımları (4-12 Ay)",

    # --- Resmi tatiller ---
    "Independence Day": "Bağımsızlık Günü (Resmi Tatil)",
    "Juneteenth National Independence Day": "Juneteenth Ulusal Bağımsızlık Günü (Resmi Tatil)",
}

# "Fed <Isim> Speech/Testimony" - yeni bir Fed yetkilisi konustugunda
# sozlugu guncellemeye gerek kalmasin diye genel bir desenle yakalanir.
_FED_SPEECH_RE = re.compile(r"^Fed (?P<name>.+) Speech$")
_FED_TESTIMONY_RE = re.compile(r"^Fed (?P<name>.+) Testimony$")


def translate_title(title: str) -> str:
    """Bilinen basligi Turkce'ye cevirir. Sozlukte yoksa Fed konusma/
    ifade desenlerini dener; o da eslesmezse orijinal Ingilizce basligi
    dondurur (veri kaybi olmasin diye sessizce Turkce uydurmak yerine)."""
    if title in TITLE_TR:
        return TITLE_TR[title]

    m = _FED_SPEECH_RE.match(title)
    if m:
        return f"Fed {m.group('name')} Konuşması"

    m = _FED_TESTIMONY_RE.match(title)
    if m:
        return f"Fed {m.group('name')} Kongre İfadesi"

    return title
