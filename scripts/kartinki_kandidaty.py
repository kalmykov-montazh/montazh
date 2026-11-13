# 13.11.2026 (Евгений, 22:47: «картинки чтобы касались Испании и нашей темы»):
# листы кандидатов картинок по темам обложек «Б» — Wikimedia Commons + Openverse, смотреть глазами и выбрать.
#   python3 scripts/kartinki_kandidaty.py outdir
import sys, os, json, io, urllib.request, urllib.parse
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "hf/oblozhki"); from b_tekst import T
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "kalmykov-montazh/1.0 (covers; github actions)"}
X = {
 "Опоздали с продлением": ["Oficina de Extranjeros", "Policía Nacional comisaría"],
 "Страховая тянет": ["seguro hogar España", "insurance documents desk"],
 "Украли паспорт": ["Policía Nacional España coche", "comisaría Policía Nacional"],
 "Временный договор аренды": ["contrato de arrendamiento", "se alquila cartel"],
 "Что даёт временная защита": ["refugiados ucranianos España", "Ukrainian refugees Madrid"],
 "Не отказывайтесь от защиты": ["refugiados ucranianos Valencia", "Ukraine Spain solidarity"],
 "Зарплата есть, квартиры нет": ["se alquila cartel balcón", "Valencia edificio viviendas"],
 "Одна квартира разный налог": ["Agencia Tributaria edificio", "Hacienda España oficina"],
 "Гарантии на новостройка": ["obra nueva Valencia", "grúa construcción viviendas España"],
 "Гарантии на новостройку": ["obra nueva Valencia", "grúa construcción viviendas España"],
 "У моря налог выше": ["Malvarrosa", "playa de la Malvarrosa edificios"],
 "Расходы после покупки": ["billetes euro", "euro banknotes coins"],
 "Чек-лист пустующей": ["piso vacío", "empty flat Spain"],
 "Долги за комунидад": ["finca Valencia fachada", "buzones portal edificio"],
 "Долг по IBI": ["Ayuntamiento de Valencia", "Valencia City Hall"],
 "Nota simple": ["Registro de la Propiedad", "Registro de la Propiedad España"],
 "Дешёвая квартира": ["se vende cartel piso", "se vende sign Spain"],
 "Энергосертификат": ["certificado energético etiqueta", "etiqueta eficiencia energética"],
 "Cédula": ["contador de luz", "electricity meter Spain"],
 "Туристическая сдача": ["Barrio del Carmen Valencia", "turistas Valencia maletas"],
 "Дарение дороже": ["notaría España", "notario España"],
 "Купили с жильцами": ["portal edificio Valencia", "Valencia apartment building"],
 "Страховка к ипотеке": ["sucursal bancaria España", "oficina banco España"],
 "Модель 100": ["declaración de la renta", "Agencia Tributaria"],
 "ПМЖ с временной": ["Tarjeta de Identidad de Extranjero", "TIE tarjeta extranjero"],
 "ВНЖ детям": ["colegio Valencia niños", "escuela España niños"],
 "Не убрали за собакой": ["perro paseo Valencia", "excrementos perro cartel"],
 "Сдать комнату": ["habitación piso compartido", "bedroom flat Spain"],
 "Больничный": ["centro de salud Valencia", "centro de salud España"],
 "Пиво на улице": ["terraza bar Valencia", "cerveza terraza España"],
 "Автономо ради ВНЖ": ["autónomo España", "coworking Valencia"],
 "Стало плохо": ["ambulancia SAMU", "urgencias hospital España"],
 "Долгая поездка": ["Aeropuerto de Valencia", "Valencia airport terminal"],
 "Слабый контракт": ["contrato de trabajo", "firma contrato oficina"],
 "Лекарства по рецепту": ["farmacia cruz verde", "farmacia España"],
 "Нашли кошелёк": ["cartera perdida", "wallet on street"],
 "Наличными больше": ["billetes de euro", "euro cash"],
 "Машина с украинскими": ["matrícula Ucrania coche", "Ukrainian car plate"],
 "Маячок V-16": ["baliza V-16", "baliza luminosa coche"],
 "Автостраховка дешевле": ["coche Valencia calle", "car keys insurance"],
 "Отель подешевел": ["hotel Valencia", "habitación de hotel"],
}
def get(u, t=15): return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
def commons(q, n=5):
    api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search",
        "gsrnamespace": 6, "gsrlimit": 12, "gsrsearch": f"{q} filetype:bitmap", "prop": "imageinfo", "iiprop": "url|size|mime", "iiurlwidth": 1000})
    r = []
    for p in sorted(json.loads(get(api)).get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99)):
        ii = (p.get("imageinfo") or [{}])[0]
        if ii.get("mime") not in ("image/jpeg", "image/png") or ii.get("width", 0) < 500: continue
        r.append({"url": ii["thumburl"], "th": ii["thumburl"], "t": "C " + p["title"][5:60]})
        if len(r) >= n: break
    return r
def openverse(q, n=5):
    api = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode({"q": q, "page_size": 12, "mature": "false"})
    r = []
    for x in json.loads(get(api)).get("results", []):
        if (x.get("width") or 1000) < 600: continue
        r.append({"url": x["url"], "th": x.get("thumbnail") or x["url"], "t": "O " + (x.get("title") or "")[:55] + " · " + (x.get("source") or "")})
        if len(r) >= n: break
    return r
try: F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
except Exception: F = ImageFont.load_default()
import concurrent.futures as cf, time
res = {}
def one(k):
    l1, l2, pl, q = T[k]; t0 = time.time()
    cand, seen = [], set()
    for qq in [q] + X.get(k, []):
        for fn in (commons, openverse):
            try:
                for c in fn(qq):
                    if c["url"] not in seen: seen.add(c["url"]); c["q"] = qq; cand.append(c)
            except Exception as e: print("ошибка", k, qq, fn.__name__, e, flush=True)
    cand = cand[:20]; ok = []
    sheet = Image.new("RGB", (5 * 300, 4 * 260), "white"); d = ImageDraw.Draw(sheet)
    for c in cand:
        try: im = Image.open(io.BytesIO(get(c["th"], 12))).convert("RGB")
        except Exception: continue
        i = len(ok); im.thumbnail((296, 220)); x, y = (i % 5) * 300, (i // 5) * 260
        sheet.paste(im, (x + 2, y + 2)); d.rectangle([x + 2, y + 2, x + 40, y + 28], fill="yellow"); d.text((x + 6, y + 4), str(i), fill="black", font=F)
        d.text((x + 4, y + 226), c["t"][:30], fill="black", font=F); ok.append(c)
    res[k] = ok; idx = list(T).index(k)
    sheet.save(f"{OUT}/{idx:02d}.jpg", quality=80); print(idx, k, len(ok), int(time.time() - t0), "с", flush=True)
    json.dump(res, open(f"{OUT}/kand.json", "w"), ensure_ascii=False, indent=1)
with cf.ThreadPoolExecutor(10) as ex: list(ex.map(one, list(T)))
