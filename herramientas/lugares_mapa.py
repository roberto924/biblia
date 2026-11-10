"""Lugares de Gn 1–11 (OpenBible Bible Geocoding Data, CC BY 4.0) y mapa base (Natural Earth).

Lo usa construir_datos.py. El NOMBRE del lugar sale del texto RV1909; la UBICACIÓN es la
identificación moderna que da OpenBible, con su puntuación. No se inventan coordenadas.
Solo biblioteca estándar.
"""
import json
import re
import unicodedata

OB = "https://raw.githubusercontent.com/openbibleinfo/Bible-Geocoding-Data/main/"
NE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
ARCHIVOS = {
    "ob_ancient": (OB + "data/ancient.jsonl", "ob_ancient.jsonl"),
    "ob_modern": (OB + "data/modern.jsonl", "ob_modern.jsonl"),
    "ob_readme": (OB + "readme.md", "ob_README.md"),
    "ne_land": (NE + "ne_50m_land.geojson", "ne_50m_land.geojson"),
    "ne_rios": (NE + "ne_50m_rivers_lake_centerlines.geojson", "ne_50m_rivers_lake_centerlines.geojson"),
    "ne_lagos": (NE + "ne_50m_lakes.geojson", "ne_50m_lakes.geojson"),
}
FUENTES = [
    {"id": "openbible", "nombre": "OpenBible.info, Bible Geocoding Data",
     "licencia": "CC BY 4.0",
     "url": "https://github.com/openbibleinfo/Bible-Geocoding-Data",
     "atribucion": "Ubicaciones: OpenBible.info Bible Geocoding Data, CC BY 4.0. Se usan sus "
                   "identificaciones y puntuaciones; nombres y niveles de confianza adaptados."},
    {"id": "naturalearth", "nombre": "Natural Earth (tierra, ríos y lagos 1:50m)",
     "licencia": "Dominio público", "url": "https://www.naturalearthdata.com/"},
]
# Umbrales sobre la puntuación de OpenBible (0–1000). README de OpenBible: el valor «se lee como
# fracción de 1000»; «100 refleja un 10 % de confianza, 500 un 50 %», y 500 o más es confianza alta.
UMBRAL_ALTA, UMBRAL_MEDIA = 500, 100

SIN_UBICAR_EDEN = ("Geografía del relato del Edén: el texto no permite ubicarlo y no hay consenso. "
                   "Las propuestas recogidas por OpenBible van en «alternativas».")
# id, nombre actual, formas en RV1909, id OpenBible, tipo, ¿ubicar?, nota
LUGARES = [
    ("eden", "Edén", ["Edén"], "af3daeb", "otro", False, SIN_UBICAR_EDEN),
    ("pison", "Pisón", ["Pisón"], "a19b076", "rio", False, SIN_UBICAR_EDEN),
    ("havila", "Havila", ["Havilah"], "ad7e819", "region", False,
     SIN_UBICAR_EDEN + " Distinta de las personas Havila de Gn 10."),
    ("gihon", "Gihón", ["Gihón"], "a71d79b", "rio", False, SIN_UBICAR_EDEN),
    ("cus", "Cus", ["Etiopía"], "a74ee0d", "region", False,
     "La RV1909 traduce «Etiopía»; el hebreo dice Cus. " + SIN_UBICAR_EDEN),
    ("tigris", "Tigris", ["Hiddekel"], "a38ebfd", "rio", True,
     "La RV1909 conserva el nombre hebreo Hiddekel, que se identifica con el Tigris."),
    ("eufrates", "Éufrates", ["Eufrates"], "a62dec4", "rio", True, ""),
    ("asiria", "Asiria", ["Asiria", "Assur"], "a3d1321", "region", True,
     "En Gn 10:11 «salió Assur» puede leerse como la persona o como la tierra; aquí se sigue a "
     "OpenBible, que lo da como lugar (Asiria). Punto representativo: Nínive."),
    ("nod", "Nod", ["Nod"], "a1ad8e1", "region", False,
     "El texto solo dice «al oriente de Edén»; OpenBible no da identificación."),
    ("ararat", "Ararat", ["Armenia"], "ab89be9", "region", True,
     "La RV1909 dice «montes de Armenia»; el hebreo dice Ararat (región de Urartu)."),
    ("babel", "Babel", ["Babel"], "ab8fdbc", "ciudad", True, ""),
    ("erec", "Erec", ["Erech"], "a5db1a6", "ciudad", True, ""),
    ("acad", "Acad", ["Accad"], "a8b7a6b", "ciudad", True, ""),
    ("calne", "Calne", ["Calneh"], "aee80af", "ciudad", True, ""),
    ("sinar", "Sinar", ["Shinar"], "af725b1", "region", True, "Punto representativo: Babilonia."),
    ("ninive", "Nínive", ["Nínive"], "a70fd5d", "ciudad", True, ""),
    ("rehobot", "Rehobot-Ir", ["Rehoboth"], "a260ff1", "ciudad", True, ""),
    ("cala", "Cala", ["Calah"], "ae1f807", "ciudad", True, ""),
    ("resen", "Resén", ["Ressen"], "abd8ada", "ciudad", True, ""),
    ("sidon", "Sidón", ["Sidón"], "a98e4d7", "ciudad", True,
     "En Gn 10:15 Sidón es una persona (hijo de Canaán); en Gn 10:19, la ciudad."),
    ("gerar", "Gerar", ["Gerar"], "a3f5814", "ciudad", True, ""),
    ("gaza", "Gaza", ["Gaza"], "aa8edd2", "ciudad", True, ""),
    ("sodoma", "Sodoma", ["Sodoma"], "a0aa664", "ciudad", True, ""),
    ("gomorra", "Gomorra", ["Gomorra"], "aa572e2", "ciudad", True, ""),
    ("adma", "Adma", ["Adma"], "a41a054", "ciudad", True, ""),
    ("zeboim", "Zeboim", ["Zeboim"], "abfbfb9", "ciudad", True, ""),
    ("lasa", "Lasa", ["Lasa"], "adaef13", "ciudad", True, ""),
    ("mesa", "Mesa", ["Mesa"], "a6b4fb2", "region", True, ""),
    ("sefar", "Sefar", ["Sephar"], "a3cae2c", "ciudad", True, ""),
    ("ur", "Ur de los Caldeos", ["Ur de los Caldeos"], "a6cf75c", "ciudad", True,
     "OpenBible registra aparte «Caldea» (región) en los mismos versículos."),
    ("haran", "Harán", ["Harán"], "a6d9af3", "ciudad", True,
     "En Gn 11:31 el primer «Harán» es la persona (hijo de Taré); el segundo, la ciudad."),
    ("canaan", "Canaán", ["Canaán"], "a581f0c", "region", True,
     "En Gn 9–10 Canaán es la persona (hijo de Cam); como tierra aparece en Gn 11:31."),
]
RIOS_ES = {"Euphrates": "Éufrates", "Al Furat": "Éufrates", "Firat": "Éufrates",
           "Tigris": "Tigris", "Dicle": "Tigris", "Nile": "Nilo", "El Bahr el Abyad": "Nilo Blanco",
           "El Bahr el Azraq": "Nilo Azul", "Abay": "Nilo Azul", "Rosetta Branch": "Nilo (brazo de Rosetta)",
           "Damietta Branch": "Nilo (brazo de Damieta)", "Jordan": "Jordán", "Shatt al Arab": "Shatt al-Arab"}


def sin_acentos(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


def gn(ref):
    return f"Gn {ref[0]}:{ref[1]}"


def u16(s, i):
    return len(s[:i].encode("utf-16-le")) // 2


def confianza(p):
    return "alta" if p >= UMBRAL_ALTA else "media" if p >= UMBRAL_MEDIA else "baja"


def _leer_jsonl(ruta, ids):
    """Devuelve {id: (n.º de línea, registro)} solo para los ids pedidos."""
    out = {}
    with open(ruta, encoding="utf-8") as f:
        for n, linea in enumerate(f, 1):
            d = json.loads(linea)
            if d["id"] in ids:
                out[d["id"]] = (n, d)
    return out


def construir_lugares(rv, menciones_personas, rutas, errores, avisos):
    anc = _leer_jsonl(rutas["ob_ancient"], {l[3] for l in LUGARES})
    mod_ids = set()
    for _, d in anc.values():
        mod_ids |= set(d.get("modern_associations", {}))
    mod = _leer_jsonl(rutas["ob_modern"], mod_ids)
    ocupado = {}
    for m in menciones_personas:
        ocupado.setdefault(m["ref"], []).append((m["inicio"], m["fin"]))

    lugares, menciones, descartadas = [], [], []
    for lid, nombre, formas, obid, tipo, ubicar, nota in LUGARES:
        if obid not in anc:
            errores.append(f"OpenBible no tiene {obid} ({nombre})"); continue
        _, d = anc[obid]
        ob_refs = sorted({tuple(map(int, v["usx"][4:].split(":"))) for v in d.get("verses", [])
                          if re.match(r"GEN ([1-9]|1[01]):", v["usx"])})
        pats = [re.compile(r"(?<!\w)%s(?!\w)" % re.escape(sin_acentos(f))) for f in formas]
        refs = []
        for r in ob_refs:
            if any(p.search(sin_acentos(rv.get(r, ""))) for p in pats):
                refs.append(r)
            else:
                descartadas.append(f"{nombre} {gn(r)}: OpenBible lo cita, pero la RV1909 no trae «{'/'.join(formas)}»")
        if not refs:
            errores.append(f"{nombre}: ningún versículo contiene el nombre"); continue
        # candidatos modernos ordenados por la puntuación ajustada de OpenBible
        cands = []
        for mid, ma in sorted(d.get("modern_associations", {}).items(), key=lambda x: -x[1]["score"]):
            if mid in mod and mod[mid][1].get("lonlat"):
                lon, lat = map(float, mod[mid][1]["lonlat"].split(","))
                cands.append({"identificacion": ma["name"], "lat": round(lat, 4), "lon": round(lon, 4),
                              "puntuacion_openbible": ma["score"]})
        ubic = None
        alts = cands[:3]
        if ubicar and cands:
            c = cands[0]
            ubic = dict(c, confianza=confianza(c["puntuacion_openbible"]))
            alts = cands[1:4]
        elif ubicar:
            nota = (nota + " " if nota else "") + "OpenBible no da identificación con coordenadas."
        lugares.append({"id": lid, "nombre": nombre, "nombre_rv1909": formas[0], "formas_rv1909": formas,
                        "tipo": tipo, "refs": [gn(r) for r in refs], "ubicacion": ubic,
                        "alternativas": alts, "fuente": "openbible",
                        "url_fuente": f"https://www.openbible.info/geo/ancient/{obid}/{d.get('url_slug', '')}",
                        "nota": nota})
        # menciones en el texto
        for r in refs:
            texto = rv[r]
            norm = "".join(n if len(n := sin_acentos(ch)) == 1 else ch.lower() for ch in texto)
            for p in pats:
                for m in p.finditer(norm):
                    a, b = u16(texto, m.start()), u16(texto, m.end())
                    if any(a < f and i < b for i, f in ocupado.get(gn(r), [])):
                        continue  # ya es mención de persona o de otro lugar
                    ocupado.setdefault(gn(r), []).append((a, b))
                    menciones.append({"ref": gn(r), "lugar": lid, "inicio": a, "fin": b})
    # nombres de lugar en versículos donde OpenBible no sitúa ese lugar y que no son personas
    ambiguos = []
    for lug in lugares:
        pats = [re.compile(r"(?<!\w)%s(?!\w)" % re.escape(sin_acentos(f))) for f in lug["formas_rv1909"]]
        for r, texto in sorted(rv.items()):
            if gn(r) in lug["refs"]:
                continue
            norm = "".join(n if len(n := sin_acentos(ch)) == 1 else ch.lower() for ch in texto)
            for p in pats:
                for m in p.finditer(norm):
                    a, b = u16(texto, m.start()), u16(texto, m.end())
                    if not any(a < f and i < b for i, f in ocupado.get(gn(r), [])):
                        ambiguos.append(f"{gn(r)} «{texto[m.start():m.end()]}» sin asignar (ni persona ni lugar de OpenBible)")
    menciones.sort(key=lambda x: (tuple(map(int, x["ref"][3:].split(":"))), x["inicio"]))

    # verificación: nombre en cada ref y offsets
    for lug in lugares:
        for ref in lug["refs"]:
            r = tuple(map(int, ref[3:].split(":")))
            if r not in rv or not any(sin_acentos(f) in sin_acentos(rv[r]) for f in lug["formas_rv1909"]):
                errores.append(f"Lugar {lug['id']}: {ref} no contiene el nombre")
    formas_de = {l["id"]: {sin_acentos(f) for f in l["formas_rv1909"]} for l in lugares}
    for m in menciones:
        t = rv[tuple(map(int, m["ref"][3:].split(":")))]
        frag = t.encode("utf-16-le")[2 * m["inicio"]:2 * m["fin"]].decode("utf-16-le")
        if sin_acentos(frag) not in formas_de[m["lugar"]]:
            errores.append(f"Mención de lugar no coincide: {m} {frag!r}")
    for lid in {m["lugar"] for m in menciones} ^ {l["id"] for l in lugares}:
        avisos.append(f"Lugar sin menciones en el texto: {lid}")

    # comprobación contra el JSON original (línea citada)
    lineas = []
    for lid, obid in (("ur", "a6cf75c"), ("ninive", "a70fd5d"), ("sidon", "a98e4d7")):
        n, d = anc[obid]
        mid, ma = max(d["modern_associations"].items(), key=lambda x: x[1]["score"])
        nm, dm = mod[mid]
        lug = next(l for l in lugares if l["id"] == lid)
        ok = (lug["ubicacion"] and lug["ubicacion"]["identificacion"] == ma["name"]
              and f'{lug["ubicacion"]["lon"]:.4f},{lug["ubicacion"]["lat"]:.4f}'
              == ",".join(f"{float(x):.4f}" for x in dm["lonlat"].split(",")))
        if not ok:
            errores.append(f"{lid}: no coincide con el JSON original de OpenBible")
        lineas.append(f'{lid}: ob_ancient.jsonl línea {n} "friendly_id":"{d["friendly_id"]}" → '
                      f'"{mid}" "name":"{ma["name"]}" "score":{ma["score"]}; ob_modern.jsonl línea {nm} '
                      f'"lonlat":"{dm["lonlat"]}" → {"OK" if ok else "DIFIERE"}')
    return lugares, menciones, ambiguos, descartadas, lineas


# ---------------------------------------------------------------- mapa base
def _clip_poly(ring, bb):
    """Sutherland–Hodgman de un anillo contra el rectángulo bb = (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = bb
    bordes = [(lambda p: p[0] >= x0, lambda a, b: _ix(a, b, x=x0)),
              (lambda p: p[0] <= x1, lambda a, b: _ix(a, b, x=x1)),
              (lambda p: p[1] >= y0, lambda a, b: _ix(a, b, y=y0)),
              (lambda p: p[1] <= y1, lambda a, b: _ix(a, b, y=y1))]
    out = ring
    for dentro, corte in bordes:
        if not out:
            break
        entrada, out = out, []
        prev = entrada[-1]
        for cur in entrada:
            if dentro(cur):
                if not dentro(prev):
                    out.append(corte(prev, cur))
                out.append(cur)
            elif dentro(prev):
                out.append(corte(prev, cur))
            prev = cur
    return out


def _ix(a, b, x=None, y=None):
    if x is not None:
        t = (x - a[0]) / (b[0] - a[0]) if b[0] != a[0] else 0
        return (x, a[1] + t * (b[1] - a[1]))
    t = (y - a[1]) / (b[1] - a[1]) if b[1] != a[1] else 0
    return (a[0] + t * (b[0] - a[0]), y)


def _simplificar(pts, tol=0.03):
    """Douglas–Peucker iterativo + redondeo a 2 decimales sin duplicados consecutivos."""
    if len(pts) > 2:
        keep = [False] * len(pts); keep[0] = keep[-1] = True
        pila = [(0, len(pts) - 1)]
        while pila:
            i, j = pila.pop()
            (ax, ay), (bx, by) = pts[i], pts[j]
            dx, dy = bx - ax, by - ay
            den = (dx * dx + dy * dy) ** 0.5 or 1e-12
            mejor, k = -1, None
            for n in range(i + 1, j):
                px, py = pts[n]
                dist = abs(dy * px - dx * py + bx * ay - by * ax) / den if (dx or dy) else ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
                if dist > mejor:
                    mejor, k = dist, n
            if k is not None and mejor > tol:
                keep[k] = True
                pila += [(i, k), (k, j)]
        pts = [p for p, q in zip(pts, keep) if q]
    out = []
    for x, y in pts:
        p = [round(x, 2), round(y, 2)]
        if not out or out[-1] != p:
            out.append(p)
    return out


def _clip_linea(pts, bb):
    x0, y0, x1, y1 = bb
    tramos, actual = [], []
    for p in pts:
        if x0 <= p[0] <= x1 and y0 <= p[1] <= y1:
            actual.append(p)
        else:
            if len(actual) > 1:
                tramos.append(actual)
            actual = []
    if len(actual) > 1:
        tramos.append(actual)
    return tramos


def _anillos(geom):
    if geom["type"] == "Polygon":
        return geom["coordinates"]
    if geom["type"] == "MultiPolygon":
        return [r for poly in geom["coordinates"] for r in poly]
    return []


def _lineas(geom):
    if geom["type"] == "LineString":
        return [geom["coordinates"]]
    if geom["type"] == "MultiLineString":
        return geom["coordinates"]
    return []


def construir_mapa(lugares, rutas, margen=6):
    pts = [(l["ubicacion"]["lon"], l["ubicacion"]["lat"]) for l in lugares if l["ubicacion"]]
    bb = (round(min(p[0] for p in pts) - margen), round(min(p[1] for p in pts) - margen),
          round(max(p[0] for p in pts) + margen), round(max(p[1] for p in pts) + margen))
    costas = []
    for f in json.load(open(rutas["ne_land"], encoding="utf-8"))["features"]:
        for ring in _anillos(f["geometry"]):
            c = _clip_poly([tuple(p[:2]) for p in ring], bb)
            s = _simplificar(c) if len(c) > 2 else []
            if len(s) > 3:
                costas.append(s)
    rios = []
    for f in json.load(open(rutas["ne_rios"], encoding="utf-8"))["features"]:
        nom = f["properties"].get("name") or ""
        for linea in _lineas(f["geometry"]):
            for tramo in _clip_linea([tuple(p[:2]) for p in linea], bb):
                s = _simplificar(tramo, 0.02)
                if len(s) > 1:
                    rios.append({"nombre": RIOS_ES.get(nom, nom), "nombre_original": nom, "puntos": s})
    lagos = []
    for f in json.load(open(rutas["ne_lagos"], encoding="utf-8"))["features"]:
        for ring in _anillos(f["geometry"]):
            c = _clip_poly([tuple(p[:2]) for p in ring], bb)
            s = _simplificar(c, 0.02) if len(c) > 2 else []
            if len(s) > 3:
                lagos.append({"nombre": f["properties"].get("name") or "", "puntos": s})
    return {"bbox": list(bb), "costas": costas, "rios": rios, "lagos": lagos,
            "fuente": "Natural Earth, dominio público", "url": "https://www.naturalearthdata.com/"}
