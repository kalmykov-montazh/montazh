# 13.11.2026: картинка-предмет для обложки «Б» — первая подходящая с Wikimedia Commons (свободные лицензии).
#   python3 scripts/oblozhka_b_kartinka.py "<запрос по-английски>" out.jpg
import sys, json, urllib.request, urllib.parse
q, out = sys.argv[1], sys.argv[2]
UA = {"User-Agent": "kalmykov-montazh/1.0 (covers; github actions)"}
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read()
api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
    "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrlimit": 15,
    "gsrsearch": f"{q} filetype:bitmap", "prop": "imageinfo", "iiprop": "url|size|mime", "iiurlwidth": 900})
pages = sorted(json.loads(get(api)).get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
for p in pages:
    ii = (p.get("imageinfo") or [{}])[0]
    if ii.get("mime") not in ("image/jpeg", "image/png") or ii.get("width", 0) < 500: continue
    if ii.get("height", 1) / max(ii.get("width", 1), 1) > 1.8: continue
    open(out, "wb").write(get(ii["thumburl"])); print("картинка:", p.get("title")); break
else:
    print("картинка не найдена:", q)
