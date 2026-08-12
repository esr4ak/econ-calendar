"""
Yuksek etkili (impact=3) ABD ekonomik gostergeleri icin statik aciklamalar
ve kural tabanli "Anlik Durum Ozeti" cumle uretici.

NEDEN LLM DEGIL: Bu site resmi bir banka kurulusu (Stablex/Akbank) sitesine
entegre edilecek. Her scraper.py calismasinda (gunde 3 kez) bir LLM'e
finansal yorum ürettirmek iki risk tasir: (1) maliyet/API bagimliligi,
(2) daha onemlisi, halka acik bir finans kurumunun sitesinde LLM'in
uydurabilecegi/yanlis yonlendirebilecegi bir "yorum" yayinlanmasi -
itibar ve olasi mevzuat (SPK vb.) riski. Bunun yerine tamamen
deterministik, onceden incelenmis sablon cumleler kullaniliyor: aynı
girdi (actual/forecast/previous) HER ZAMAN aynı, once gozden gecirilmis
metni uretir - siirpriz yok.

EVENT_INFO: Her gosterge basligi (translations.py'deki Turkce baslikla
birebir eslesir) icin sabit bilgiler:
  - meaning: gosterge ne olcer (yayindan yayina degismez)
  - market_impact: bu gostergeye piyasanin genel olarak nasil tepki
    verdigine dair genel/betimleyici bir not (yatirim tavsiyesi degil,
    "genellikle"/"olabilir" gibi hedge'lenmis dil kullanilir)
  - category: asagidaki siniflardan biri, classify_and_summarize()
    hangi sablonu secece bunu kullanir

DEGERLENDIRME NOTU: Bu metinler bilgilendirme amaclidir, yatirim tavsiyesi
degildir. Stablex ekibinin yayina almadan once finans/hukuk ekibiyle bir
inceleme turu yapmasi onerilir (bkz. README.md).
"""

from __future__ import annotations

from typing import Optional

HIGHER_GOOD = "higher_good"    # actual yuksek gelmesi genelde "guclu ekonomi" okunur
HIGHER_BAD = "higher_bad"      # actual yuksek gelmesi genelde "baski/zayiflik" okunur (enflasyon, issizlik)
RATE_DECISION = "rate_decision"  # Fed faiz karari - ozel karsilastirma (onceki faize gore)
NO_NUMBER = "no_number"        # sayisal actual gelmez (konusma, tutanak, basin toplantisi vb.)

EVENT_INFO: dict[str, dict] = {
    "Tarım Dışı İstihdam": {
        "category": HIGHER_GOOD,
        "meaning": "ABD'de tarım sektörü dışındaki işyerlerinde bir ay içinde eklenen net istihdam sayısını gösterir; ABD Çalışma Bakanlığı tarafından her ayın ilk Cuma günü yayınlanır ve işgücü piyasasının en çok izlenen göstergesidir.",
        "market_impact": "Beklentinin belirgin üzerinde gelmesi güçlü istihdam piyasasına işaret eder ve genellikle doları destekler; beklentinin altında kalması Fed'in faiz indirimine gidebileceği ihtimalini güçlendirdiği için riskli varlıkları (kripto, hisse senedi) destekleyebilir.",
    },
    "Tarım Dışı İstihdam Yıllık Revizyon (Öncül)": {
        "category": HIGHER_GOOD,
        "meaning": "ABD İşgücü İstatistikleri Bürosu'nun (BLS) önceki 12 aylık tarım dışı istihdam verilerine yaptığı yıllık öncül revizyonu gösterir; gerçek istihdam tablosunun aylık verilerle ne ölçüde uyumlu olduğunu ortaya koyar.",
        "market_impact": "Aşağı yönlü büyük bir revizyon, işgücü piyasasının önceden düşünülenden daha zayıf olduğunu ortaya koyduğu için Fed'in gevşeme ihtimalini artırabilir; yukarı yönlü revizyon tam tersi etki yapabilir.",
    },
    "İşsizlik Oranı": {
        "category": HIGHER_BAD,
        "meaning": "İşgücüne dahil olup aktif olarak iş arayan ancak istihdam edilemeyen kişilerin toplam işgücüne oranını gösterir; işgücü piyasasının genel sağlığının temel göstergesidir.",
        "market_impact": "Beklentinin üzerinde (daha yüksek) gelmesi işgücü piyasasında zayıflamaya işaret eder ve Fed'in faiz indirimine daha yakın durabileceği düşüncesiyle riskli varlıkları destekleyebilirken doları baskılayabilir; beklentinin altında kalması tam tersi yönde çalışabilir.",
    },
    "JOLTs Açık İş Sayısı": {
        "category": HIGHER_GOOD,
        "meaning": "ABD'de ay sonu itibarıyla doldurulmayı bekleyen açık iş pozisyonu sayısını gösterir; işgücü talebinin ve piyasadaki gerginliğin öncü bir göstergesidir.",
        "market_impact": "Beklentinin üzerinde gelmesi işgücü talebinin güçlü kaldığına işaret eder ve genellikle doları destekler; belirgin düşüş işgücü piyasasının soğuduğuna işaret ederek Fed'in gevşeme ihtimalini artırabilir.",
    },
    "ISM İmalat PMI": {
        "category": HIGHER_GOOD,
        "meaning": "İmalat sektöründeki satın alma yöneticilerine yapılan ankete dayanır; 50 üzeri sektörde büyümeye, 50 altı daralmaya işaret eder.",
        "market_impact": "50 eşiğinin üzerinde ve beklentiyi aşan bir okuma imalat sektöründe toparlanmaya işaret ederek riskli varlıkları destekleyebilir; 50 altına düşen veya beklentinin belirgin altında kalan bir okuma resesyon endişesi yaratabilir.",
    },
    "ISM Hizmet PMI": {
        "category": HIGHER_GOOD,
        "meaning": "ABD ekonomisinin büyük bölümünü oluşturan hizmet sektöründeki satın alma yöneticilerine yapılan ankete dayanır; 50 üzeri büyümeye, 50 altı daralmaya işaret eder.",
        "market_impact": "Hizmet sektörü ABD ekonomisinin en büyük bileşeni olduğu için bu veri genel büyüme görünümü açısından yakından izlenir; beklentinin üzerinde gelmesi genellikle doları ve risk iştahını destekler, altında kalması tam tersi etki yapabilir.",
    },
    "TÜFE (Aylık)": {
        "category": HIGHER_BAD,
        "meaning": "Tüketicilerin satın aldığı mal ve hizmet sepetinin fiyatındaki bir önceki aya göre yüzdesel değişimi gösterir; enflasyonun aylık hızını ölçen temel göstergedir.",
        "market_impact": "Beklentinin üzerinde (daha sıcak) gelmesi enflasyonun öngörülenden inatçı olduğuna işaret ederek Fed'in şahin duruşunu sürdürme ihtimalini artırır ve riskli varlıklar üzerinde baskı yaratabilir; beklentinin altında kalması faiz indirimi beklentilerini güçlendirerek risk iştahını destekleyebilir.",
    },
    "TÜFE (Yıllık)": {
        "category": HIGHER_BAD,
        "meaning": "Tüketici fiyatlarının bir önceki yılın aynı dönemine göre yüzdesel değişimini gösterir; Fed'in enflasyon hedefiyle (%2) karşılaştırdığı temel yıllık göstergedir.",
        "market_impact": "Beklentinin üzerinde gelmesi enflasyonun hedeften uzaklaştığına işaret ederek Fed'in sıkı duruşunu koruma ihtimalini artırır; beklentinin altında kalması Fed'in gevşeme alanını genişletebileceği için risk iştahını destekleyebilir.",
    },
    "Çekirdek TÜFE (Aylık)": {
        "category": HIGHER_BAD,
        "meaning": "Gıda ve enerji gibi oynak kalemler hariç tutularak hesaplanan TÜFE'nin aylık değişimini gösterir; Fed tarafından çekirdek enflasyon trendini görmek için tercih edilir.",
        "market_impact": "Gıda/enerji dışı fiyat baskısının altında yatan trendi yansıttığı için TÜFE'den daha yakından izlenir; beklentinin üzerinde gelmesi şahin, altında kalması güvercin bir sinyal olarak okunabilir.",
    },
    "Çekirdek TÜFE (Yıllık)": {
        "category": HIGHER_BAD,
        "meaning": "Gıda ve enerji hariç tutularak hesaplanan TÜFE'nin yıllık değişimini gösterir; Fed'in politika kararlarında en çok referans aldığı enflasyon ölçütlerinden biridir.",
        "market_impact": "Beklentinin üzerinde gelmesi çekirdek enflasyonun inatçı kaldığına işaret ederek Fed'in şahin duruşunu destekler; beklentinin altında kalması gevşeme ihtimalini güçlendirebilir.",
    },
    "ÜFE (Aylık)": {
        "category": HIGHER_BAD,
        "meaning": "Üreticilerin sattığı mal ve hizmetlerin toptan fiyatlarındaki aylık değişimi gösterir; tüketici enflasyonuna (TÜFE) birkaç ay önden öncü bir sinyal olarak izlenir.",
        "market_impact": "Beklentinin üzerinde gelmesi üretici maliyetlerindeki artışın ileride tüketici fiyatlarına yansıyabileceğine işaret ederek enflasyon endişesini artırabilir; altında kalması tam tersi yönde rahatlatıcı olabilir.",
    },
    "Çekirdek PCE Fiyat Endeksi (Aylık)": {
        "category": HIGHER_BAD,
        "meaning": "Fed'in enflasyon hedeflemesinde resmi olarak esas aldığı, gıda ve enerji hariç kişisel tüketim harcamaları fiyat endeksinin aylık değişimidir.",
        "market_impact": "Fed'in en çok önem verdiği enflasyon göstergesi olduğu için piyasa tepkisi genellikle güçlüdür; beklentinin üzerinde gelmesi şahin, altında kalması güvercin bir sinyal olarak okunur.",
    },
    "GSYH Büyümesi (Çeyreklik, Öncül)": {
        "category": HIGHER_GOOD,
        "meaning": "ABD ekonomisinin bir önceki çeyreğe göre yıllıklandırılmış büyüme oranının ilk (öncül) tahminini gösterir; ekonominin genel sağlığının en geniş kapsamlı ölçütüdür.",
        "market_impact": "Beklentinin üzerinde güçlü büyüme resesyon endişelerini azaltarak riskli varlıkları destekleyebilir; ancak aşırı güçlü veri enflasyonist baskı endişesiyle Fed'in şahin kalmasına da yol açabilir. Beklentinin belirgin altında kalması resesyon endişesini artırabilir.",
    },
    "GSYH Büyümesi (Çeyreklik, 2. Tahmin)": {
        "category": HIGHER_GOOD,
        "meaning": "Öncül tahminden sonra daha kapsamlı verilerle güncellenen ikinci GSYH büyüme tahminidir; genellikle piyasa etkisi öncül veriden daha sınırlıdır.",
        "market_impact": "Öncül tahminden belirgin sapma olmadıkça piyasa tepkisi sınırlı kalır; büyük bir revizyon büyüme görünümüne dair beklentileri yeniden fiyatlayabilir.",
    },
    "GSYH Büyümesi (Çeyreklik, Kesin)": {
        "category": HIGHER_GOOD,
        "meaning": "Çeyreklik GSYH büyümesinin en kapsamlı verilerle hesaplanan nihai (kesin) tahminidir.",
        "market_impact": "Öncül ve ikinci tahminden büyük sapma olmadıkça piyasa etkisi genellikle sınırlıdır; veri seri sonunda geldiği için tepkiler çoğunlukla önceki tahminlerde fiyatlanmış olur.",
    },
    "Perakende Satışlar (Aylık)": {
        "category": HIGHER_GOOD,
        "meaning": "Perakende mağazalardaki toplam satışların bir önceki aya göre yüzdesel değişimini gösterir; tüketici harcamalarının ve iç talebin en güncel göstergelerinden biridir.",
        "market_impact": "Beklentinin üzerinde gelmesi tüketici harcamalarının güçlü kaldığına işaret ederek riskli varlıkları ve doları destekleyebilir; beklentinin altında kalması tüketici talebinde yavaşlamaya işaret edebilir.",
    },
    "Konut Başlangıçları": {
        "category": HIGHER_GOOD,
        "meaning": "Bir ay içinde inşaatına başlanan yeni konut sayısını gösterir; inşaat sektörü ve faiz oranlarına duyarlı ekonomik aktivitenin öncü göstergesidir.",
        "market_impact": "Beklentinin üzerinde gelmesi konut/inşaat sektöründe canlılığa işaret eder; yüksek faiz ortamında beklenenden zayıf gelmesi faizlerin ekonomiyi yavaşlattığının bir işareti olarak okunabilir.",
    },
    "İnşaat İzinleri (Öncül)": {
        "category": HIGHER_GOOD,
        "meaning": "Gelecekte başlanacak konut inşaatları için alınan izin sayısının öncül verisini gösterir; konut başlangıçlarına göre birkaç ay önden öncü bir sinyaldir.",
        "market_impact": "Konut sektöründeki gelecek aktiviteye dair öncü bir gösterge olduğu için beklentiden sapmalar inşaat/emlak sektörüne yönelik beklentileri etkileyebilir; genel piyasa etkisi konut başlangıçlarına göre daha sınırlıdır.",
    },
    "İkinci El Konut Satışları": {
        "category": HIGHER_GOOD,
        "meaning": "Bir ay içinde el değiştiren ikinci el konut sayısını gösterir; ABD konut piyasasının büyük bölümünü (yeni konutlardan çok daha fazlasını) oluşturur.",
        "market_impact": "Beklentinin üzerinde gelmesi konut piyasasında ve tüketici güveninde canlılığa işaret eder; mortgage faizlerine oldukça duyarlı olduğu için beklenenden zayıf veri yüksek faiz ortamının etkisini yansıtıyor olabilir.",
    },
    "Kişisel Gelir (Aylık)": {
        "category": HIGHER_GOOD,
        "meaning": "Hane halklarının bir ay içinde elde ettiği toplam gelirdeki yüzdesel değişimi gösterir; tüketici harcama kapasitesinin öncü göstergelerinden biridir.",
        "market_impact": "Beklentinin üzerinde gelmesi hane halkı gelirlerinin güçlü seyrettiğine işaret ederek tüketim harcamaları açısından olumlu okunabilir; zayıf gelmesi tüketici talebinde yavaşlama endişesi yaratabilir.",
    },
    "Kişisel Harcamalar (Aylık)": {
        "category": HIGHER_GOOD,
        "meaning": "Hane halklarının bir ay içindeki toplam tüketim harcamalarındaki yüzdesel değişimi gösterir; ABD GSYH'sinin en büyük bileşeni olan tüketici harcamalarını doğrudan ölçer.",
        "market_impact": "Beklentinin üzerinde gelmesi güçlü tüketici talebine işaret ederek riskli varlıkları destekleyebilir; ancak aşırı güçlü harcama verisi enflasyon endişesiyle de ilişkilendirilebilir.",
    },
    "Dayanıklı Mal Siparişleri (Aylık)": {
        "category": HIGHER_GOOD,
        "meaning": "Otomobil, uçak, makine gibi 3 yıldan uzun kullanım ömrüne sahip dayanıklı malların yeni siparişlerindeki aylık değişimi gösterir; iş dünyası yatırım iştahının öncü göstergesidir.",
        "market_impact": "Beklentinin üzerinde gelmesi işletmelerin yatırım iştahının güçlü kaldığına işaret eder; bu kalem genellikle uçak siparişleri gibi tekil büyük işlemlerden dolayı oynak olabileceği için piyasa genellikle 'ulaşım hariç' alt kalemine de bakar.",
    },
    "Michigan Tüketici Güveni (Öncül)": {
        "category": HIGHER_GOOD,
        "meaning": "Michigan Üniversitesi'nin tüketicilerin kişisel finansal durumları ve genel ekonomiye ilişkin algısını ölçen anketinin öncül (ay ortası) sonucudur.",
        "market_impact": "Beklentinin üzerinde gelmesi tüketici güveninin güçlendiğine ve harcama iştahının sürebileceğine işaret eder; zayıf gelmesi tüketici davranışında temkinliliğe işaret edebilir.",
    },
    "Fed Faiz Kararı": {
        "category": RATE_DECISION,
        "meaning": "FOMC'nin (Federal Açık Piyasa Komitesi) belirlediği, bankalar arası gecelik borçlanma faizi olan federal fon oranı hedef aralığını gösterir; ABD para politikasının temel aracıdır.",
        "market_impact": "Faiz artışı genellikle doları destekleyip riskli varlıklar üzerinde baskı yaratırken, faiz indirimi tam tersi yönde etki edebilir; faizin sabit tutulduğu durumlarda piyasa odağı genellikle karar metnindeki dile ve basın toplantısına kayar.",
    },
    "Fed Basın Toplantısı": {
        "category": NO_NUMBER,
        "meaning": "Fed Başkanı'nın faiz kararı sonrası düzenlediği, komitenin ekonomik görünüme ve gelecekteki politika patikasına dair sinyaller verdiği basın toplantısıdır.",
        "market_impact": "Faiz kararının kendisinden çok, toplantıda kullanılan dilin şahin ya da güvercin algılanması piyasalarda daha güçlü ve ani hareketlere yol açabilir.",
    },
    "FOMC Toplantı Tutanakları": {
        "category": NO_NUMBER,
        "meaning": "Bir önceki FOMC toplantısının ayrıntılı tutanaklarıdır; komite üyelerinin karar sürecindeki görüş ayrılıklarını ve tartışılan senaryoları ortaya koyar.",
        "market_impact": "Toplantı sırasında verilen sinyallerden daha ayrıntılı ve bazen farklı nüanslar içerebildiği için, özellikle gelecekteki faiz patikasına dair yeni ipuçları çıkarsa piyasa hareketine yol açabilir.",
    },
    "FOMC Ekonomik Projeksiyonları": {
        "category": NO_NUMBER,
        "meaning": "FOMC üyelerinin büyüme, işsizlik, enflasyon ve faiz oranına dair güncellenmiş tahminlerini (ünlü 'dot plot' faiz projeksiyonu dahil) içeren rapordur.",
        "market_impact": "Özellikle faiz projeksiyonlarındaki (dot plot) değişim piyasa beklentileriyle uyumsuzsa güçlü bir piyasa tepkisine yol açabilir.",
    },
    "Fed Başkanı Warsh Konuşması": {
        "category": NO_NUMBER,
        "meaning": "Fed Başkanı'nın para politikasına, enflasyona veya ekonomik görünüme dair yaptığı planlı bir konuşmadır.",
        "market_impact": "Konuşmanın şahin ya da güvercin tonu, özellikle faiz patikasına dair yeni bir sinyal içeriyorsa piyasalarda ani hareketlere yol açabilir.",
    },
    "Fed Başkanı Warsh Kongre İfadesi": {
        "category": NO_NUMBER,
        "meaning": "Fed Başkanı'nın ABD Kongresi önünde para politikası ve ekonomik görünüm hakkında verdiği periyodik ifadedir.",
        "market_impact": "Kongre üyelerinin sorularına verilen yanıtlar genellikle planlı konuşmalardan daha fazla ayrıntı içerdiği için beklenmedik sinyaller piyasa hareketine yol açabilir.",
    },
}

# Kategori x sonuc (above/below/inline) icin sablon cumleler. Ayni girdi
# HER ZAMAN ayni cumleyi uretir - bkz. modul dokstring'i.
_TEMPLATES = {
    HIGHER_GOOD: {
        "above": "Açıklanan veri, piyasa beklentisinin üzerinde gelerek bu alanda öngörülenden güçlü bir görünüme işaret etti; bu tür sürpriz güçlü veriler genellikle risk iştahını ve doları destekler.",
        "below": "Açıklanan veri, piyasa beklentisinin altında kalarak bu alanda öngörülenden zayıf bir görünüme işaret etti; bu durum Fed'in gevşek para politikasına yönelme ihtimalini güçlendirebileceği için riskli varlıkları destekleyebilirken doları baskılayabilir.",
        "inline": "Açıklanan veri, piyasa beklentisiyle büyük ölçüde uyumlu geldi; belirgin bir sürpriz olmadığı için piyasa tepkisinin sınırlı kalması bekleniyor.",
    },
    HIGHER_BAD: {
        "above": "Açıklanan veri, piyasa beklentisinin üzerinde gelerek bu alandaki baskının öngörülenden güçlü olduğuna işaret etti; bu tür sürpriz yüksek okumalar Fed'in şahin duruşunu sürdürme ihtimalini artırdığı için riskli varlıklar üzerinde baskı yaratabilir.",
        "below": "Açıklanan veri, piyasa beklentisinin altında kalarak bu alandaki baskının öngörülenden zayıf olduğuna işaret etti; bu tür sürpriz düşük okumalar Fed'in gevşemeye daha yakın durabileceği ihtimalini güçlendirdiği için risk iştahını destekleyebilir.",
        "inline": "Açıklanan veri, piyasa beklentisiyle büyük ölçüde uyumlu geldi; belirgin bir sürpriz olmadığı için piyasa tepkisinin sınırlı kalması bekleniyor.",
    },
    RATE_DECISION: {
        "hike": "Fed, politika faizini artırarak sıkılaştırıcı bir adım attı; bu genellikle kısa vadede doları destekleyip riskli varlıklar üzerinde baskı yaratabilir.",
        "cut": "Fed, politika faizini indirerek gevşeme adımı attı; bu genellikle riskli varlıklar (kripto, hisse senedi) için destekleyici olurken doları baskılayabilir.",
        "unchanged": "Fed, politika faizini piyasa beklentisiyle uyumlu şekilde sabit tuttu; bu tür toplantılarda piyasa odağı genellikle karar metnindeki dile ve basın toplantısındaki sinyallere kayar.",
    },
}

# 'higher_good'/'higher_bad' siniflandirmasinda kucuk farklari 'inline'
# sayan gorece tolerans esigi (baseline'a oranla).
_INLINE_TOLERANCE_RATIO = 0.03


def _to_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_meaning(title: str) -> str:
    return EVENT_INFO.get(title, {}).get("meaning", "")


def get_market_impact(title: str) -> str:
    return EVENT_INFO.get(title, {}).get("market_impact", "")


def get_category(title: str) -> Optional[str]:
    return EVENT_INFO.get(title, {}).get("category")


def generate_summary(title: str, actual, forecast, previous) -> str:
    """Kural tabanli 'Anlik Durum Ozeti' cumlesi uretir. actual henuz
    aciklanmadiysa ('' ya da None) bos string doner - kart bu durumda
    ozet bolumunu hic gostermez."""
    category = get_category(title)
    if category is None or category == NO_NUMBER:
        return ""

    actual_f = _to_float(actual)
    if actual_f is None:
        return ""

    if category == RATE_DECISION:
        previous_f = _to_float(previous)
        if previous_f is None:
            return ""
        if actual_f > previous_f:
            return _TEMPLATES[RATE_DECISION]["hike"]
        if actual_f < previous_f:
            return _TEMPLATES[RATE_DECISION]["cut"]
        return _TEMPLATES[RATE_DECISION]["unchanged"]

    baseline = _to_float(forecast)
    if baseline is None:
        baseline = _to_float(previous)
    if baseline is None:
        return ""

    diff = actual_f - baseline
    tolerance = max(abs(baseline) * _INLINE_TOLERANCE_RATIO, 0.01)
    if abs(diff) <= tolerance:
        outcome = "inline"
    elif diff > 0:
        outcome = "above"
    else:
        outcome = "below"

    return _TEMPLATES.get(category, {}).get(outcome, "")
