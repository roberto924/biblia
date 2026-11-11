"""Fase 7b: textos originales y testigos de Génesis, Éxodo, Levítico y Números.

Genera:
  datos/originales.js          window.BIBLIA_ORIGINALES (hebreo WLC, testigos, variantes, videos)
  datos/griego-swete.js        window.BIBLIA_GRIEGO (LXX de Swete, GPL-3.0)
  datos/LICENCIA-griego-swete.txt

Uso:  python -I herramientas/originales.py [--sin-red]
Solo biblioteca estándar. Descarga a herramientas/cache/ lo que falte; con
--sin-red usa solo la caché (los videos se comprueban con oembed.json de la caché).
Sale con código != 0 si falla cualquier verificación.

Principio del proyecto: todo dato dice de dónde sale. Nada se inventa; lo que no se
pudo confirmar va en «nota».
"""
import bisect
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "herramientas" / "cache"
DATOS = RAIZ / "datos"
UA = {"User-Agent": "biblia-datos/1.0"}

GH = "https://raw.githubusercontent.com/"
TVTMS_URL = (GH + "STEPBible/STEPBible-Data/master/Versification/TVTMS%20-%20Translators%20"
             "Versification%20Traditions%20with%20Methodology%20for%20Standardisation%20for%20"
             "Eng%2BHeb%2BLat%2BGrk%2BOthers%20-%20STEPBible.org%20CC%20BY.txt")
ARCHIVOS = {
    "oshb_gen": (GH + "openscriptures/morphhb/master/wlc/Gen.xml", "oshb_Gen.xml"),
    "oshb_exo": (GH + "openscriptures/morphhb/master/wlc/Exod.xml", "oshb_Exod.xml"),
    "oshb_lev": (GH + "openscriptures/morphhb/master/wlc/Lev.xml", "oshb_Lev.xml"),
    "oshb_num": (GH + "openscriptures/morphhb/master/wlc/Num.xml", "oshb_Num.xml"),
    "tvtms": (TVTMS_URL, "tvtms.txt"),
    "swete_vers": (GH + "eliranwong/LXX-Swete-1930/master/00-Swete_versification.csv",
                   "swete_00-Swete_versification.csv"),
    "swete_pal": (GH + "eliranwong/LXX-Swete-1930/master/01-Swete_word_with_punctuations.csv",
                  "swete_01-Swete_word_with_punctuations.csv"),
    "swete_lic": (GH + "eliranwong/LXX-Swete-1930/master/LICENSE", "swete_LICENSE.txt"),
}
for _f in ("otype", "oslots", "scroll", "book", "chapter", "verse", "rec", "full"):
    ARCHIVOS["dss_" + _f] = (GH + "ETCBC/dss/master/tf/2.0/%s.tf" % _f, "dss_%s.tf" % _f)

LIBROS = ("Gn", "Ex", "Lv", "Nm")
LIBRO_OSIS = {"Gn": "Gen", "Ex": "Exo", "Lv": "Lev", "Nm": "Num"}          # códigos TVTMS / Swete
OSIS_LIBRO = {"Gen": "Gn", "Exo": "Ex", "Exod": "Ex", "Lev": "Lv", "Num": "Nm"}
DSS_LIBRO = {"Gen": "Gn", "Ex": "Ex", "Lev": "Lv", "Num": "Nm"}            # códigos de libro en ETCBC/dss
OSIS_RE = "Gen|Exo|Lev|Num"                                   # libros TVTMS / Swete que se leen
FALLOS = []
ROLLOS_PRESENTES = set()          # nombres de rollo que aparecen en ETCBC/dss (lo llena leer_dss)


def fallo(msg):
    FALLOS.append(msg)
    print("FALLO:", msg)


# ------------------------------------------------------------------ descarga
def obtener(clave, sin_red):
    url, nombre = ARCHIVOS[clave]
    ruta = CACHE / nombre
    if not ruta.exists():
        if sin_red:
            sys.exit(f"Falta {ruta} y se pidió --sin-red")
        CACHE.mkdir(parents=True, exist_ok=True)
        print(f"Descargando {url}")
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=180) as r:
            ruta.write_bytes(r.read())
    return ruta


def ref(lib, c, v):
    return f"{lib} {c}:{v}"


# ------------------------------------------------------------------ RV1909
def leer_rv():
    s = (DATOS / "biblia.js").read_text(encoding="utf-8")
    d = json.loads(s[s.index("{"):s.rindex("}") + 1])
    orden, texto = [], {}
    for cap in d["capitulos"]:
        for v in cap["versiculos"]:
            k = (cap["libro"], cap["cap"], v["n"])
            orden.append(k)
            texto[k] = v["texto"]
    return orden, texto


# ------------------------------------------------------------------ hebreo (OSHB / WLC)
OSIS_NS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"


def leer_oshb(ruta, lib):
    """{(lib, c, v): texto} con vocales y acentos del WLC; sin morfología ni notas."""
    raiz = ET.parse(ruta).getroot()
    res = {}
    for verso in raiz.iter(OSIS_NS + "verse"):
        partes = []

        def recorrer(el):
            for h in el:
                tag = h.tag.replace(OSIS_NS, "")
                if tag == "note":
                    pass                                   # notas y qere: fuera
                elif tag == "w":
                    partes.append(("w", (h.text or "").replace("/", "")))
                elif tag == "seg":
                    t = h.get("type", "")
                    if t == "x-maqqef":
                        partes.append(("pegado", h.text or "־"))
                    elif t == "x-sof-pasuq":
                        partes.append(("pegado", h.text or "׃"))
                    elif t in ("x-pe", "x-samekh"):
                        pass                               # marcas de párrafo: fuera
                    else:
                        partes.append(("w", h.text or ""))
                else:
                    recorrer(h)
                if h.tail and h.tail.strip() and tag != "note":
                    partes.append(("w", h.tail.strip()))

        recorrer(verso)
        txt = ""
        pegar = False
        for tipo, t in partes:
            if not t:
                continue
            if tipo == "pegado":
                txt += t
                pegar = t == "־"
            else:
                txt += ("" if (pegar or not txt) else " ") + t
                pegar = False
        _, c, v = verso.get("osisID").split(".")
        res[(lib, int(c), int(v))] = txt.strip()
    return res


def consonantes(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^א-ת ]", "", s.replace("־", " "))


# ------------------------------------------------------------------ griego (Swete)
def leer_swete(ruta_vers, ruta_pal):
    inicios = []
    for l in ruta_vers.read_text(encoding="utf-8").splitlines():
        i, r = l.split("\t")
        inicios.append((int(i), r))
    inicios.sort()
    fin_ot = None
    sel = []
    for n, (i, r) in enumerate(inicios):
        m = re.match(r"(%s)\.(\d+):(\d+)$" % OSIS_RE, r)
        if m:
            sig = inicios[n + 1][0] if n + 1 < len(inicios) else None
            sel.append(((OSIS_LIBRO[m[1]], int(m[2]), int(m[3])), i, sig))
            fin_ot = sig
        elif r.startswith(tuple(x + "." for x in OSIS_RE.split("|"))):
            fallo(f"Swete: etiqueta no reconocida {r}")
    palabras = {}
    with open(ruta_pal, encoding="utf-8") as f:
        for l in f:
            i, w = l.rstrip("\n").split("\t", 1)
            i = int(i)
            if i >= fin_ot:
                break
            palabras[i] = w
    res = {}
    for k, a, b in sel:
        res[k] = unicodedata.normalize("NFC", " ".join(palabras[i] for i in range(a, b) if i in palabras))
    return res


# ------------------------------------------------------------------ TVTMS
class Tradicion:
    """Acceso a una tradición (RV, hebreo, Swete) para evaluar los TEST del TVTMS."""

    def __init__(self, textos):
        self.t = textos
        self.ult = {}
        for (lib, c, v) in textos:
            self.ult[(lib, c)] = max(self.ult.get((lib, c), 0), v)

    def existe(self, lib, c, v, sub):
        return sub is None and (lib, c, v) in self.t

    def largo(self, lib, c, v):
        return len(re.sub(r"\W", "", self.t.get((lib, c, v), "")))


class SoloUltimo:
    """Envuelve una tradición para evaluar solo los TEST «=Last» (los demás se dan por buenos)."""

    def __init__(self, trad):
        self.ult = trad.ult
        self.t = trad.t

    def existe(self, lib, c, v, sub):
        return None

    def largo(self, lib, c, v):
        return None


def punto(txt, cap):
    """'5' o '5.2' o '7:5' -> (cap, v, sub)."""
    if ":" in txt:
        c, txt = txt.split(":", 1)
        cap = int(c)
    if "." in txt:
        v, s = txt.split(".", 1)
        return cap, int(v), s
    return cap, int(txt), None


def parse_refs(token):
    """Devuelve (lib, [(c, v, sub)...], anotacion) o (None, None, anotacion) si ausente/vacío."""
    token = token.strip()
    anot = " ".join(re.findall(r"\[(.*?)\]", token))
    base = re.sub(r"\[.*?\]", "", token).strip()
    if not base or base.startswith("Absent") or base == "Empty" or "Empty" in anot:
        return None, None, anot or base
    m = re.match(r"(%s)\.(.*)$" % OSIS_RE, base)
    if not m:
        return None, None, "no reconocido: " + token
    lib = OSIS_LIBRO[m[1]]
    cap = None
    out = []
    for p in re.split(r"[;,]", m[2]):
        p = p.strip()
        if not p:
            continue
        if "-" in p:
            a, b = p.split("-", 1)
            c1, v1, s1 = punto(a, cap)
            if ":" in b:                                   # rango entre capítulos
                return None, None, "rango entre capítulos: " + token
            if s1 is not None and "." not in b:            # subversos de un mismo verso
                out.append((c1, v1, s1 + "-" + b))
                cap = c1
                continue
            c2, v2, s2 = punto(b, c1)
            for v in range(v1, v2 + (1 if s2 is None else 0)):
                out.append((c1, v, s1 if v == v1 else None))
            if s2 is not None:
                out.append((c1, v2, s2))
            cap = c1
        else:
            c, v, s = punto(p, cap)
            out.append((c, v, s))
            cap = c
    return lib, out, anot


def evaluar_test(expr, trad):
    expr = expr.strip()
    m = re.match(r"(%s)\.(\d+):(\d+)(?:\.(\d+))?=(Last|Exist|NotExist)$" % OSIS_RE, expr, re.I)
    if m:
        lib, c, v, s, que = OSIS_LIBRO[m[1]], int(m[2]), int(m[3]), m[4], m[5].lower()
        if que == "last":
            return trad.ult.get((lib, c)) == v and s is None
        e = trad.existe(lib, c, v, s)
        if e is None:
            return True
        return e if que == "exist" else not e
    un = r"(?:%s)\.\d+:\d+" % OSIS_RE
    m = re.match(r"(%s(?:\+%s)*)([<>])(%s(?:\+%s)*)$" % (un, un, un, un), expr)
    if m:                                              # largos de versículos (o sumas: «Num.1:32+Num.1:33>…»)
        def suma(lado):
            tot = 0
            for p in lado.split("+"):
                q = re.match(r"(\w+)\.(\d+):(\d+)$", p)
                x = trad.largo(OSIS_LIBRO[q[1]], int(q[2]), int(q[3]))
                if x is None:
                    return None
                tot += x
            return tot
        a, b = suma(m[1]), suma(m[3])
        if a is None or b is None:
            return True
        return a < b if m[2] == "<" else a > b
    raise ValueError("TEST no reconocido: " + expr)


def leer_bloques_tvtms(ruta):
    """Bloques condensados de Gn/Ex: [{'cab': [...], 'tests': [[...]], 'filas': [(tipo, [...])]}]."""
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    i = next(n for n, l in enumerate(lineas) if l.startswith("#DataStart(Condensed)"))
    bloques, b = [], None
    for l in lineas[i + 1:]:
        if l.startswith("#DataEnd"):
            break
        cols = l.split("\t")
        if l.startswith("$"):
            b = None
            if re.match(r"\$(%s)\." % OSIS_RE, l):
                b = {"cab": [c.strip() for c in cols], "tests": [], "filas": []}
                bloques.append(b)
            continue
        if b is None or not l.strip():
            continue
        if cols[0].startswith("TEST"):
            b["tests"].append([c.strip() for c in cols])
        elif cols[0].strip():
            b["filas"].append((cols[0].strip(), [c.strip() for c in cols]))
    return bloques


def columna_valida(bloque, col, trad):
    for t in bloque["tests"]:
        if col < len(t) and t[col]:
            if not evaluar_test(t[col], trad):
                return False
    return True


def construir_mapa(bloques, nombre_col, trad_destino, trad_rv, orden_rv, estricto):
    """Mapa RV -> destino. Devuelve (mapa {rvkey: [destkeys]}, notas {rvkey: nota}, usados)."""
    mapa, notas = {}, {}
    cubiertos = set()
    for b in bloques:
        cab = b["cab"]
        if not columna_valida(b, 1, trad_rv):
            fallo(f"TVTMS {cab[0]}: la RV1909 no cumple los TEST de la columna English KJV")
        if nombre_col == "Hebrew":
            cands = [cab.index("Hebrew")]
        else:
            cands = [n for n, c in enumerate(cab) if c.startswith("Greek")]
        col = next((n for n in cands if columna_valida(b, n, trad_destino)), None)
        forzada = COLUMNA_FORZADA.get(cab[0]) if nombre_col != "Hebrew" else None
        if forzada:
            col = cab.index(forzada[0])
        aproximada = False
        if col is None and nombre_col != "Hebrew" and columna_valida(b, 1, trad_destino):
            # ninguna columna griega cumple sus TEST pero la edición cumple los de la KJV: sigue ese orden (Nm 6:24-27 y 10:34-36 en Swete)
            col = 1
        if col is None and not estricto:
            # ninguna columna cumple todos los TEST: se acepta la primera que cumple los de «=Last»
            col = next((n for n in cands if columna_valida(b, n, SoloUltimo(trad_destino))), None)
            aproximada = col is not None
        if col is None:
            if estricto:
                fallo(f"TVTMS {cab[0]}: ninguna columna {nombre_col} cumple los TEST")
            for tipo, cols in b["filas"]:
                lib, eng, _ = parse_refs(cols[1])
                for (c, v, s) in eng or []:
                    cubiertos.add((lib, c, v))
                    notas.setdefault((lib, c, v), f"TVTMS {cab[0]}: ninguna columna griega encaja con esta edición")
            continue
        for tipo, cols in b["filas"]:
            if col >= len(cols):
                continue
            lib, eng, _ = parse_refs(cols[1])
            if not eng:
                continue
            libd, dst, anot = parse_refs(cols[col])
            for (c, v, s) in eng:
                cubiertos.add((lib, c, v))
            eng_sub = any(s is not None for (_, _, s) in eng)
            if dst is not None and any(s == "0" for (_, _, s) in dst):
                dst = [(c, v, None if s == "0" else s) for (c, v, s) in dst]   # «.0» = parte principal del versículo
                anot = (anot + " " if anot else "") + "parte principal (.0) del versículo"
            dst_ok = dst is not None and all(s is None for (_, _, s) in dst)
            pares = None
            if cols[col] == cols[1]:                           # misma referencia en ambas tradiciones
                vs = sorted({(c, v) for (c, v, s) in eng})
                pares = [((lib, c, v), [(lib, c, v)]) for (c, v) in vs]
            elif dst_ok and not eng_sub:
                if len(eng) == len(dst):
                    pares = [((lib, e[0], e[1]), [(libd, d[0], d[1])]) for e, d in zip(eng, dst)]
                elif len(eng) == 1:
                    pares = [((lib, eng[0][0], eng[0][1]), [(libd, d[0], d[1]) for d in dst])]
            if pares:
                for k, ds in pares:
                    if k not in mapa:
                        mapa[k] = ds
                        notas.pop(k, None)
                        if anot or tipo != "OneToOne" or aproximada or forzada:
                            notas[k] = f"TVTMS ({tipo}): {cab[col]} «{cols[col]}»" + (
                                "; correspondencia aproximada (esta edición no cumple todos los TEST del bloque)" if aproximada else "") + (
                                "; " + forzada[1] if forzada else "")
            else:
                for (c, v, s) in eng:
                    k = (lib, c, v)
                    if k not in mapa and k not in notas:
                        notas[k] = f"TVTMS ({tipo}): en {cab[col]} corresponde a «{cols[col]}»; sin versículo completo equivalente"
    for k in orden_rv:
        if k not in cubiertos and k not in mapa:
            mapa[k] = [k]
    return mapa, notas


# La RV1909 de eBible no sigue a la KJV (columna «English KJV» del TVTMS) en Nm 12:16–13:33 ni en Nm 29:40–30:16:
# RV -> versículos KJV. Comprobado por contenido (anclas hebreas y griegas): RV 13:1 «movió el pueblo de Haseroth» = KJV y TM 12:16;
# RV 13:33 reúne KJV 13:32-33; RV 30:1 «Y Moisés dijo» = KJV 29:40 = TM 30:1; RV 30:16 reúne KJV 30:15-16.
def _rv_propia():
    m = {("Nm", 12, 16): [], ("Nm", 13, 1): [("Nm", 12, 16)], ("Nm", 13, 33): [("Nm", 13, 32), ("Nm", 13, 33)],
         ("Nm", 29, 40): [], ("Nm", 30, 1): [("Nm", 29, 40)], ("Nm", 30, 16): [("Nm", 30, 15), ("Nm", 30, 16)]}
    for v in range(2, 33):
        m[("Nm", 13, v)] = [("Nm", 13, v - 1)]
    for v in range(2, 16):
        m[("Nm", 30, v)] = [("Nm", 30, v - 1)]
    return m


RV_PROPIA = _rv_propia()
NOTA_RV_PROPIA = {
    13: ("La RV1909 (eBible) numera Nm 13 de otra forma que el TM y la KJV: su 13:1 es el 12:16 de ambos (su 12:16 queda vacío) "
         "y su 13:33 reúne los versículos 13:32-33. Correspondencia propia sobre el TVTMS, comprobada por contenido."),
    30: ("La RV1909 (eBible) numera Nm 30 como el TM (su 29:40 queda vacío), pero su 30:16 reúne los versículos 30:16-17 del TM "
         "(30:15-16 de la KJV). Correspondencia propia sobre el TVTMS, comprobada por contenido."),
}


def aplicar_rv_propia(mapa, notas):
    """Pasa el mapa (calculado como si la RV fuese la KJV) a la numeración propia de la RV en RV_PROPIA."""
    base_m, base_n = dict(mapa), dict(notas)
    for rv, kjvs in RV_PROPIA.items():
        mapa.pop(rv, None)
        notas.pop(rv, None)
        if not kjvs:
            continue                                   # versículo vacío en la RV: sin original
        ds, faltan = [], [k for k in kjvs if k not in base_m]
        for k in kjvs:
            ds += base_m.get(k, [])
        nota = NOTA_RV_PROPIA[rv[1] if rv[1] in NOTA_RV_PROPIA else rv[1] + 1]
        if faltan:
            notas[rv] = nota + " " + " ".join(base_n.get(k, "") for k in faltan)
            continue
        mapa[rv] = ds
        extra = " ".join(base_n[k] for k in kjvs if k in base_n)
        notas[rv] = nota + (" " + extra if extra else "")


# ------------------------------------------------------------------ Rollos (ETCBC/dss, Abegg)
def leer_tf(ruta):
    res = {}
    lineas = ruta.read_text(encoding="utf-8").split("\n")
    i = 0
    while lineas[i].startswith("@"):
        i += 1
    nodo = 0
    for l in lineas[i + 1:]:
        if not l:
            continue
        if "\t" in l:
            k, v = l.split("\t", 1)
            nodos = []
            for p in k.split(","):
                if "-" in p:
                    a, b = p.split("-")
                    nodos += range(int(a), int(b) + 1)
                else:
                    nodos.append(int(p))
        else:
            v, nodos = l, [nodo + 1]
        for n in nodos:
            res[n] = v
        nodo = nodos[-1]
    return res


def rango_slots(v):
    p = v.split(",")
    return int(p[0].split("-")[0]), int(p[-1].split("-")[-1])


def leer_dss(sin_red):
    rutas = {f: obtener("dss_" + f, sin_red) for f in ("otype", "oslots", "scroll", "book", "chapter", "verse", "rec", "full")}
    tipos = {}
    for l in rutas["otype"].read_text(encoding="utf-8").splitlines():
        m = re.match(r"(\d+)-(\d+)\t(\w+)$", l)
        if m:
            tipos[m[3]] = (int(m[1]), int(m[2]))
    maxslot = tipos["sign"][1]
    osl = {}
    lineas = rutas["oslots"].read_text(encoding="utf-8").split("\n")
    i = 0
    while lineas[i].startswith("@"):
        i += 1
    nodo = maxslot
    for l in lineas[i + 1:]:
        if not l:
            continue
        if "\t" in l:
            k, l = l.split("\t")
            nodo = int(k)
        else:
            nodo += 1
        osl[nodo] = l
    book = leer_tf(rutas["book"])
    cap = leer_tf(rutas["chapter"])
    ver = leer_tf(rutas["verse"])
    scroll = leer_tf(rutas["scroll"])
    rec = leer_tf(rutas["rec"])
    full = leer_tf(rutas["full"])
    ROLLOS_PRESENTES.update(scroll.values())
    a, z = tipos["line"]
    lineas_l = sorted((rango_slots(osl[n]), scroll[n]) for n in range(a, z + 1) if n in scroll and n in osl)
    inicios = [r[0][0] for r in lineas_l]
    palabras = {}   # scroll -> {(lib,c,v): [(texto, conservado)]}
    for w, b in book.items():
        if b not in DSS_LIBRO:
            continue
        s0, s1 = rango_slots(osl[w])
        conservado = any(rec.get(x) != "1" for x in range(s0, s1 + 1))
        j = bisect.bisect_right(inicios, s0) - 1
        (la, lz), sc = lineas_l[j]
        if not la <= s0 <= lz:
            fallo(f"DSS: palabra {w} fuera de línea")
            continue
        if not ver[w].isdigit():
            continue
        k = (DSS_LIBRO[b], int(cap[w]), int(ver[w]))
        palabras.setdefault(sc, {}).setdefault(k, []).append((full.get(w, ""), conservado))
    return palabras


# ------------------------------------------------------------------ datos fijos
FUENTES = [
    {"id": "wlc-oshb", "nombre": "Westminster Leningrad Codex 4.20 (texto del Códice de Leningrado), vía Open Scriptures Hebrew Bible (morphhb)",
     "licencia": "Texto WLC: dominio público. Atribución: Open Scriptures Hebrew Bible (lemas y morfología CC BY 4.0, no usados aquí)",
     "url": "https://github.com/openscriptures/morphhb"},
    {"id": "tvtms", "nombre": "TVTMS (Translators Versification Traditions with Methodology for Standardisation), STEPBible / Tyndale House",
     "licencia": "CC BY 4.0", "url": "https://github.com/STEPBible/STEPBible-Data/tree/master/Versification"},
    {"id": "swete", "nombre": "H. B. Swete, The Old Testament in Greek (Cambridge, ed. 1930), digitalización LXX-Swete-1930 (Eliran Wong)",
     "licencia": "GPL-3.0 (texto de Swete en dominio público; digitalización GPL); va aparte en datos/griego-swete.js",
     "url": "https://github.com/eliranwong/LXX-Swete-1930"},
    {"id": "etcbc-dss", "nombre": "ETCBC/dss: datos de los Rollos del Mar Muerto de M. Abegg, J. Bowley y E. Cook (conversión Text-Fabric de J. Jacobs, M. Naaijer y D. Roorda)",
     "licencia": "CC BY-NC 4.0. Solo se usan para calcular qué versículos conserva cada rollo y para verificar Ex 1:5; no se redistribuye su texto salvo la lectura breve citada en la variante",
     "url": "https://github.com/ETCBC/dss"},
    {"id": "leon-levy", "nombre": "The Leon Levy Dead Sea Scrolls Digital Library (Israel Antiquities Authority): fichas con período y edición oficial (DJD)",
     "licencia": "Solo enlace: las imágenes no se pueden reproducir sin permiso de la IAA (https://www.deadseascrolls.org.il/terms)",
     "url": "https://www.deadseascrolls.org.il/"},
    {"id": "wikipedia", "nombre": "Wikipedia en inglés (fuente secundaria para fechas y contenido de los códices), consultada el 2026-11-11",
     "licencia": "CC BY-SA 4.0 (solo se toman datos, no texto)", "url": "https://en.wikipedia.org/"},
    {"id": "proyecto-biblia", "nombre": "Proyecto Biblia (BibleProject en español), canal de YouTube",
     "licencia": "Solo inserción del reproductor de YouTube; no se descarga ni se modifica", "url": "https://www.youtube.com/@ProyectoBibliaOficial"},
]

CODICES = [
    {"id": "leningrado", "nombre": "Códice de Leningrado (Firkovich B 19 A)", "tipo": "codice", "idioma": "hebreo",
     "fecha": "1008 (o 1009) d. C.", "fecha_certeza": "colofón",
     "contiene": ["Gn 1:1-Gn 50:26", "Ex 1:1-Ex 40:38", "Lv 1:1-Lv 27:34", "Nm 1:1-Nm 36:13"],
     "institucion": "Biblioteca Nacional de Rusia, San Petersburgo",
     "url": "https://archive.org/details/Leningrad_Codex", "uso": "solo_enlace",
     "nota": "Es la base del texto hebreo de esta app (WLC). Copiado en El Cairo según su colofón. Facsímil en archive.org (B/N, 988 págs.; en color: https://archive.org/details/Leningrad_Codex_Color_Images); licencia del facsímil no declarada: solo enlace.",
     "fuente": "Wikipedia «Leningrad Codex» (fecha, signatura, institución y facsímiles), consultada el 2026-11-11"},
    {"id": "alepo", "nombre": "Códice de Alepo", "tipo": "codice", "idioma": "hebreo",
     "fecha": "c. 920 d. C. (Tiberíades)", "fecha_certeza": "estimación (un colofón posterior atribuye la vocalización a Aarón ben Moisés ben Aser)",
     "contiene": [],
     "institucion": "Museo de Israel (Santuario del Libro), Jerusalén",
     "url": "https://www.aleppocodex.org/", "uso": "solo_enlace",
     "nota": "NO conserva Génesis, Éxodo, Levítico ni Números: le falta todo el Pentateuco hasta Dt 28:17. Solo se han recuperado aparte un fragmento con partes de Éx 8 (publicado por Yosef Ofer en 2016) y otra hoja de Éxodo aparecida en los años 80; no verifiqué los versículos exactos, por eso «contiene» va vacío.",
     "fuente": "Wikipedia «Aleppo Codex», consultada el 2026-11-11"},
    {"id": "vaticano", "nombre": "Códice Vaticano (Vat. gr. 1209)", "tipo": "codice", "idioma": "griego (Septuaginta)",
     "fecha": "c. 300–350 d. C.", "fecha_certeza": "datación paleográfica",
     "contiene": ["Gn 46:28-Gn 50:26", "Ex 1:1-Ex 40:38", "Lv 1:1-Lv 27:34", "Nm 1:1-Nm 36:13"],
     "institucion": "Biblioteca Apostólica Vaticana",
     "url": "https://digi.vatlib.it/view/MSS_Vat.gr.1209", "uso": "solo_enlace",
     "nota": "Se perdieron las hojas con Gn 1:1–46:28a; las que hay ahora son una reposición del s. XV (no son testigo antiguo). La fuente solo menciona como perdidos, en el Antiguo Testamento, Gn 1:1–46:28a, Sal 105:27–137:6b y 2 Re 2:5–7, 10–13 (inferido: Éxodo, Levítico y Números presentes). Gn 46:28 se conserva solo en parte (desde 46:28b). En Ex 35–40 la Septuaginta ordena y numera el texto de otra forma.",
     "fuente": "Wikipedia «Codex Vaticanus», consultada el 2026-11-11"},
    {"id": "sinaitico", "nombre": "Códice Sinaítico", "tipo": "codice", "idioma": "griego (Septuaginta)",
     "fecha": "c. 325–360 d. C.", "fecha_certeza": "datación paleográfica",
     "contiene": ["Gn 23:19-Gn 24:46", "Lv 20:27-Lv 22:30"],
     "institucion": "British Library, Biblioteca Universitaria de Leipzig, Monasterio de Santa Catalina y Biblioteca Nacional de Rusia (repartido)",
     "url": "https://codexsinaiticus.org/", "uso": "solo_enlace",
     "nota": "De Génesis solo quedan fragmentos de Gn 23:19–24:46; NO contiene Éxodo; de Levítico conserva Lv 20:27–22:30 (lista de contenidos de Wikipedia, según Würthwein y Swete). De Números la misma lista dice solo «fragmentos», sin versículos: no se añaden a «contiene». No comprobé el contenido de las hojas del Pentateuco halladas en 1975 en el Sinaí. No pude abrir codexsinaiticus.org (no respondió) ni confirmar en qué institución están esas hojas.",
     "fuente": "Wikipedia «Codex Sinaiticus», consultada el 2026-11-11"},
    {"id": "alejandrino", "nombre": "Códice Alejandrino (Royal MS 1 D V–VIII)", "tipo": "codice", "idioma": "griego (Septuaginta)",
     "fecha": "c. 400–440 d. C.", "fecha_certeza": "datación paleográfica",
     "contiene": ["Gn 1:1-Gn 50:26", "Ex 1:1-Ex 40:38", "Lv 1:1-Lv 27:34", "Nm 1:1-Nm 36:13"],
     "institucion": "British Library, Londres",
     "url": "https://www.bl.uk/manuscripts/FullDisplay.aspx?ref=Royal_MS_1_D_V", "uso": "solo_enlace",
     "nota": "El primer volumen contiene de Génesis a 2 Crónicas (inferido: Éxodo, Levítico y Números presentes; la fuente no los nombra ni cita daños en Números). Dañados Gn 14:14–17, 15:1–5, 15:16–19 y 16:6–9; defectos por hojas rotas en Gn 1:20–25, 1:29–2:3 y Lv 8:6, 8:7 y 8:16 (según Swete). El enlace de la British Library responde, pero no comprobé que muestre las imágenes del volumen I.",
     "fuente": "Wikipedia «Codex Alexandrinus», consultada el 2026-11-11"},
    {"id": "samaritano-cul-add1846", "nombre": "Pentateuco Samaritano, Cambridge University Library Add. 1846", "tipo": "pentateuco_samaritano",
     "idioma": "hebreo (escritura samaritana)",
     "fecha": "comienzos del s. XII d. C. (según el catálogo de Cambridge)", "fecha_certeza": "no verificada en la ficha (dato del catálogo leído solo a través de un buscador)",
     "contiene": [],
     "institucion": "Cambridge University Library",
     "url": "https://cudl.lib.cam.ac.uk/view/MS-ADD-01846", "uso": "solo_enlace",
     "nota": "Considerado el manuscrito conservado más antiguo del Pentateuco Samaritano. Lleva una nota de un escriba que cuenta cómo se salvó de un incendio en 1201. La ficha de Cambridge Digital Library devolvió 403 a la consulta automática: no confirmé el contenido por versículos (tampoco el de Levítico ni el de Números), por eso «contiene» va vacío.",
     "fuente": "Catálogo de Cambridge University Library (vía buscador, 2026-11-11); no abierto directamente"},
]

LL = "https://www.deadseascrolls.org.il/explore-the-archive/manuscript/"
PERIODO = {"Hasmonean": "período asmoneo", "Herodian": "período herodiano", "Roman": "período romano",
           "Hellenistic-Roman": "período helenístico-romano", "Early Hellenistic": "período helenístico temprano"}
# (claves Abegg, id, sigla, ficha Leon Levy, período Leon Levy, edición oficial según Leon Levy, escritura)
ROLLOS = [
    (["1Q1"], "1QGen", "1Q1-1", "Herodian", "Barthélemy 1955, DJD 1: 49-50", "cuadrada"),
    (["1Q2"], "1QExod", "1Q2-1", "Hellenistic-Roman", "Barthélemy 1955, DJD 1: 50-51", "cuadrada"),
    (["2Q1"], "2QGen", "2Q1-1", "Herodian", "Baillet 1962, DJD 3: 48-49", "cuadrada"),
    (["2Q2"], "2QExod-a", "2Q2-1", "Herodian", "Baillet 1962, DJD 3: 49-52", "cuadrada"),
    (["2Q3"], "2QExod-b", "2Q3-1", "Herodian", "Baillet 1962, DJD 3: 52-55", "cuadrada"),
    (["2Q4"], "2QExod-c", "2Q4-1", "Hellenistic-Roman", "Baillet 1962, DJD 3: 56", "cuadrada"),
    (["4Q1"], "4QGen-Exod-a", "4Q1-1", "Hasmonean", "Davila 1994, DJD 12: 7-30", "cuadrada"),
    (["4Q2"], "4QGen-b", "4Q2-1", "Roman", "Davila 1994, DJD 12: 31-38", "cuadrada"),
    (["4Q3"], "4QGen-c", "4Q3-1", "Herodian", "Davila 1994, DJD 12: 39-42", "cuadrada"),
    (["4Q4"], "4QGen-d", "4Q4-1", "Hasmonean", "Davila 1994, DJD 12: 43-45", "cuadrada"),
    (["4Q5"], "4QGen-e", "4Q5-1", "Herodian", "Davila 1994, DJD 12: 47-52", "cuadrada"),
    (["4Q6"], "4QGen-f", "4Q6-1", "Hasmonean", "Davila 1994, DJD 12: 53-55; H. Eshel y E. Eshel 2005, DSD 12: 134-137", "cuadrada"),
    (["4Q7"], "4QGen-g", "4Q7-1", "Hasmonean", "Davila 1994, DJD 12: 57-60", "cuadrada"),
    (["4Q8a", "4Q8b", "4Q8c"], "4QGen-h (h1, h2, h-para)", "4Q8-1", "Herodian", "Davila 1994, DJD 12: 61-64", "cuadrada"),
    (["4Q9"], "4QGen-j", "4Q9-1", "Herodian", "Davila 1994, DJD 12: 65-73", "cuadrada"),
    (["4Q10"], "4QGen-k", "4Q10-1", "Herodian", "Davila 1994, DJD 12: 75-78", "cuadrada"),
    (["4Q11"], "4QpaleoGen-Exod-l", "4Q11-1", "Hasmonean", "Skehan, Ulrich y Sanderson 1992, DJD 9: 17-50", "paleohebrea"),
    (["4Q12"], "4QpaleoGen-m", "4Q12-1", "Hasmonean", "Skehan, Ulrich y Sanderson 1992, DJD 9: 51-52", "paleohebrea"),
    (["4Q13"], "4QExod-b", "4Q13-1", "Herodian", "Cross 1994, DJD 12: 79-95", "cuadrada"),
    (["4Q14"], "4QExod-c", "4Q14-1", "Herodian", "Sanderson 1994, DJD 12: 97-125", "cuadrada"),
    (["4Q15"], "4QExod-d", "4Q15-1", "Hasmonean", "Sanderson 1994, DJD 12: 127-128", "cuadrada"),
    (["4Q16"], "4QExod-e", "4Q16-1", "Hasmonean", "Sanderson 1994, DJD 12: 129-131", "cuadrada"),
    (["4Q17"], "4QExod-Lev-f", "4Q17-1", "Early Hellenistic", "Cross 1994, DJD 12: 133-144", "cuadrada"),
    (["4Q18"], "4QExod-g", "4Q18-1", "Hasmonean", "Sanderson 1994, DJD 12: 145-146", "cuadrada"),
    (["4Q19"], "4QExod-h", "4Q19-1", "Herodian", "Sanderson 1994, DJD 12: 147", "cuadrada"),
    (["4Q20"], "4QExod-j", "4Q20-1", "Herodian", "Sanderson 1994, DJD 12: 149-150", "cuadrada"),
    (["4Q21"], "4QExod-k", "4Q21-1", "Roman", "Sanderson 1994, DJD 12: 151", "cuadrada"),
    (["4Q22"], "4QpaleoExod-m", "4Q22-1", "Hasmonean", "Skehan, Ulrich y Sanderson 1992, DJD 9: 53-130", "paleohebrea"),
    (["6Q1"], "6QpaleoGen", "6Q1-1", "Early Hellenistic", "Baillet 1962, DJD 3: 105-106", "paleohebrea"),
    (["8Q1"], "8QGen", "8Q1-1", "Herodian", "Baillet 1962, DJD 3: 147-148", "cuadrada"),
    # Levítico (fichas de la Leon Levy leídas el 2026-11-11: campos «period», «script_type» y «official_publications»)
    (["1Q3"], "1QpaleoLev-Num", "1Q3-1", "Hellenistic-Roman", "Barthélemy 1955, DJD 1: 51-54", "paleohebrea"),
    (["2Q5"], "2QpaleoLev", "2Q5-1", "Hasmonean", "Baillet 1962, DJD 3: 56-57", "paleohebrea"),
    (["4Q23"], "4QLev-Num-a", "4Q23-1", "Hasmonean", "Ulrich 1994, DJD 12: 153-176", "cuadrada"),
    (["4Q24"], "4QLev-b", "4Q24-1", "Hasmonean", "Ulrich 1994, DJD 12: 177-187", "cuadrada"),
    (["4Q25"], "4QLev-c", "4Q25-1", "Hellenistic-Roman", "Tov 1994, DJD 12: 189-192", "cuadrada"),
    (["4Q26"], "4QLev-d", "4Q26-1", "Hellenistic-Roman", "Tov 1994, DJD 12: 193-204", "cuadrada"),
    (["4Q26a"], "4Q26a", None, None, None, None),
    (["4Q26b"], "4Q26b", None, None, None, None),
    (["4Q26c"], "4Q26c", None, None, None, None),
    (["4Q249j"], "4Q pap cryptA Lev-h", "4Q249-6", "Hellenistic-Roman", "Pfann 2000, DJD 36: 516-677; Pfann 1999, DJD 35: 1-24", "críptica A (papiro)"),
    (["6Q2"], "6QpaleoLev", "6Q2-1", "Early Hellenistic", "Baillet 1962, DJD 3: 106", "paleohebrea"),
    (["11Q1"], "11QpaleoLev-a", "11Q1-1", "Herodian", "Tigchelaar 1997, RevQ 18: 325-330; Freedman y Mathews 1985, The Paleo-Hebrew Leviticus Scroll; Puech 1989, RB 96", "paleohebrea"),
    (["11Q2"], "11QLev-b", "11Q2-1", "Herodian", "García Martínez, Tigchelaar y van der Woude 1998, DJD 23: 1-9", "cuadrada"),
    # Números (fichas de la Leon Levy leídas el 2026-11-11: campos «copy», «period», «script_type» y «official_publications»)
    (["2Q6"], "2QNum-a", "2Q6-1", "Herodian", "Baillet 1962, DJD 3: 57-58", "cuadrada"),
    (["2Q7"], "2QNum-b", "2Q7-1", "Herodian", "Baillet 1962, DJD 3: 58-59", "cuadrada"),
    (["2Q8"], "2QNum-c", "2Q8-1", "Herodian", "Baillet 1962, DJD 3: 59", "cuadrada"),
    (["2Q9"], "2QNum-d(?)", "2Q9-1", "Hellenistic-Roman", "Baillet 1962, DJD 3: 59-60", "cuadrada"),
    (["2Q29"], "2Q29", "2Q29-1", "Hellenistic-Roman", "Baillet 1962, DJD 3: 92", "cuadrada"),
    (["4Q27"], "4QNum-b", "4Q27-1", "Herodian", "Jastram 1994, DJD 12: 205-267", "cuadrada"),
    (["4Q156"], "4QtgLev", "4Q156-1", "Hasmonean", "Milik 1977, DJD 6: 86-89; Beyer 1984, Die aramäischen Texte: 278-280", "cuadrada"),
]
# Rollos sin ficha propia en la Leon Levy o con datos especiales (idioma, contenido no calculable, notas).
ROLLO_EXTRA = {
    "4Q26a": {"sin_ficha": True}, "4Q26b": {"sin_ficha": True}, "4Q26c": {"sin_ficha": True},
    "4Q249j": {"nota": " Ficha de la Leon Levy: 4Q249-6, «4Q pap cryptA Lev», copia «h»; que sea el 4Q249j de los datos de Abegg es inferido "
                       "(la lámina 590 de esa ficha lista «4Q249j pap cryptA Levh?»). Las dos ediciones son las que da la ficha para todo el grupo 4Q249."},
    "4Q156": {"idioma": "arameo (targum)", "sin_calculo": True,
              "nota": "Targum (traducción aramea) de Levítico. Está en los datos de Abegg (ETCBC/dss), pero sin referencia de libro, capítulo y versículo, "
                      "así que no se calcula qué versículos contiene: «contiene» va vacío. La fecha es la etiqueta paleográfica de la Leon Levy Library, no una fecha numérica."},
    "2Q9": {"nota": " La Leon Levy lo titula «2Q Numbers(?)» (copia «d»): la identificación con Números es dudosa en la propia ficha."},
    "2Q29": {"nota": " La Leon Levy lo cataloga como «2Q Unidentified» (sin libro ni copia); que contenga Nm 23 es la asignación de los datos de Abegg (inferido). "
                     "Por eso la sigla es solo el número."},
}

# Bloques del TVTMS donde la columna elegida por los TEST no encaja con el contenido de Swete.
COLUMNA_FORZADA = {
    "$Exo.35:8-35:27": ("Greek3 (Brenton)",
                        "columna elegida a mano (inferido): Swete sigue el mismo texto que Brenton (Códice Vaticano) y las anclas de contenido lo confirman, aunque no cumple el TEST «Exo.35:18=notExist»"),
}
# Anclas de contenido del griego: RV -> (palabra en la RV, palabra en el griego asignado)
ANCLAS_GRIEGO = {
    ("Gn", 1, 1): ("principio", "ΑΡΧΗ"), ("Gn", 31, 55): ("Labán", "Λαβὰν"), ("Ex", 1, 5): ("setenta", "ἑβδομήκοντα"),
    ("Ex", 8, 1): ("Faraón", "Φαραὼ"), ("Ex", 20, 13): ("matarás", "φονεύσεις"), ("Ex", 20, 14): ("adulterio", "μοιχεύσεις"),
    ("Ex", 21, 16): ("robare", "κλέψῃ"), ("Ex", 22, 1): ("buey", "μόσχον"), ("Ex", 25, 7): ("onix", "σαρδίου"),
    ("Ex", 28, 30): ("Urim", "δήλωσιν"), ("Ex", 35, 9): ("onix", "σαρδίου"), ("Ex", 35, 13): ("mesa", "τράπεζαν"),
    ("Ex", 35, 14): ("candelero", "λυχνίαν"), ("Ex", 35, 17): ("atrio", "αὐλῆς"), ("Ex", 37, 1): ("arca", "κιβωτόν"),
    ("Ex", 38, 9): ("atrio", "αὐλήν"), ("Ex", 39, 2): ("ephod", "ἐπωμίδα"), ("Ex", 40, 33): ("atrio", "αὐλὴν"),
    # Levítico (Swete numera Lv 7:1-10 RV como 6:31-40 y Lv 7:11-38 RV como 7:1-28)
    ("Lv", 7, 1): ("culpa", "πλημμελίας"), ("Lv", 7, 11): ("paces", "σωτηρίου"), ("Lv", 7, 38): ("Sinaí", "Σεινά"),
    ("Lv", 11, 7): ("puerco", "ὗν"), ("Lv", 16, 8): ("Azazel", "ἀποπομπαίῳ"), ("Lv", 19, 18): ("amarás á tu prójimo", "ἀγαπήσεις τὸν πλησίον"),
    # Números (Swete numera RV 1:24-37 en otro orden, 13:1 = KJV 12:16 y reparte 13:33 y 30:16 en dos versículos)
    ("Nm", 1, 24): ("Gad", "Γὰδ"), ("Nm", 6, 24): ("Jehová te bendiga", "Εὐλογήσαι σε Κύριος"), ("Nm", 10, 35): ("Levántate", "Ἐξεγέρθητι"),
    ("Nm", 13, 1): ("Haseroth", "Ἁσηρώθ"), ("Nm", 13, 33): ("gigantes", "γίγαντας"), ("Nm", 21, 9): ("serpiente de metal", "ὄφιν χαλκοῦν"),
    ("Nm", 22, 28): ("asna", "ὄνου"), ("Nm", 30, 16): ("ordenanzas", "δικαιώματα"),
}

# Anclas de contenido del hebreo (consonantes): RV -> (palabra en la RV, palabra en el hebreo asignado)
ANCLAS_HEBREO = {
    ("Lv", 6, 2): ("prójimo", "בעמיתו"),         # TM 5:21
    ("Lv", 6, 9): ("holocausto", "העלה"),        # TM 6:2
    ("Lv", 16, 8): ("Azazel", "לעזאזל"),
    ("Nm", 13, 1): ("Haseroth", "מחצרות"),       # TM 12:16
    ("Nm", 13, 33): ("gigantes", "הנפילים"),     # TM 13:32-33
    ("Nm", 16, 48): ("mortandad", "המגפה"),      # TM 17:13
    ("Nm", 17, 8): ("almendras", "שקדים"),       # TM 17:23
    ("Nm", 26, 1): ("mortandad", "המגפה"),       # TM 25:19-26:1
    ("Nm", 30, 16): ("ordenanzas", "החקים"),     # TM 30:16-17
}

# RV -> (Swete, palabra que debe estar en el griego, palabra que debe estar en la RV)
CORRECCIONES_GRIEGO = {
    ("Ex", 40, 14): (("Ex", 40, 12), "χιτῶνας", "túnicas"),
    ("Ex", 40, 15): (("Ex", 40, 13), "ἀλείψεις", "ungirás"),
}

VIDEOS = [
    ("Gn", "HQMKA6w5ZZM", "Resumen del libro de Génesis: un panorama completo animado (parte 1)", "Gn 1:1-Gn 11:32", "inferido"),
    ("Gn", "MC8BqGu9B8A", "Resumen del libro de Génesis: un panorama completo animado (parte 2)", "Gn 12:1-Gn 50:26", "inferido"),
    ("Gn", "MLhplmsb_vk", "El tema principal del libro de Génesis • parte 2 • Serie de la Torá • (episodio 2)", "Gn 1:1-Gn 50:26", "libro entero (tema)"),
    ("Ex", "y9pED55wMM4", "Resumen del libro de Éxodo: un panorama completo animado (parte 1)", "Ex 1:1-Ex 18:27", "inferido"),
    ("Ex", "U2lUpubEMDI", "Resumen del libro de Éxodo: un panorama completo animado (parte 2)", "Ex 19:1-Ex 40:38", "inferido"),
    ("Ex", "zCJUcscTrDw", "El tema principal del libro de Éxodo • parte 1 • Serie de la Torá • (episodio 3)", "Ex 1:1-Ex 40:38", "libro entero (tema)"),
    ("Ex", "13zKQAlBHpg", "El tema principal del libro de Éxodo • parte 2 • Serie de la Torá • (episodio 4)", "Ex 1:1-Ex 40:38", "libro entero (tema)"),
    ("Lv", "vKT8eo3hAMw", "Resumen del libro de Levítico: un panorama completo animado", "Lv 1:1-Lv 27:34", "inferido"),
    ("Lv", "xkIZrB0PXg8", "¿Estás evitando el libro de Levítico? • Lo analizamos para ti (Serie de la Torá Ep.5)", "Lv 1:1-Lv 27:34", "libro entero (tema)"),
    ("Nm", "dtfbSxNecMk", "Resumen del libro de Números: un panorama completo animado", "Nm 1:1-Nm 36:13", "inferido"),
    ("Nm", "IhW7gXB3o8I", "El tema principal del libro de Números • Serie de la Torá • (episodio 6)", "Nm 1:1-Nm 36:13", "libro entero (tema)"),
]
VIDEOS_DESCARTADOS = {"y2pED55wMM4": "Errata del informe de fuentes: oEmbed responde 404. El ID correcto del resumen de Éxodo (parte 1) es y9pED55wMM4."}


def oembed(vid, sin_red, cache):
    if sin_red:                       # sin red: vale la última comprobación guardada
        return cache.get(vid)
    url = "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=%s&format=json" % vid
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            d = json.loads(r.read().decode("utf-8"))
            res = {"estado": r.status, "title": d.get("title"), "author_name": d.get("author_name")}
    except urllib.error.HTTPError as e:
        res = {"estado": e.code}
    res["comprobado"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cache[vid] = res
    return res


# ------------------------------------------------------------------ utilidades
def comprimir(refs, indice):
    """Lista de claves RV -> ['Gn 1:1-Gn 1:28', 'Gn 2:4', ...] en orden RV."""
    idx = sorted(indice[k] for k in refs)
    orden = sorted(indice, key=indice.get)
    out, ini, prev = [], None, None
    for i in idx + [None]:
        if ini is not None and (i is None or i != prev + 1):
            a, b = orden[ini], orden[prev]
            out.append(ref(*a) if a == b else ref(*a) + "-" + ref(*b))
            ini = None
        if i is not None and ini is None:
            ini = i
        prev = i
    return out


def escribir_js(ruta, cabecera, var, obj):
    txt = cabecera + "window.%s = " % var + json.dumps(obj, ensure_ascii=False, indent=1) + ";\n"
    ruta.write_text(txt, encoding="utf-8")
    return len(txt.encode("utf-8"))


# ------------------------------------------------------------------ principal
def main():
    sin_red = "--sin-red" in sys.argv
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    orden_rv, texto_rv = leer_rv()
    indice = {k: n for n, k in enumerate(orden_rv)}
    conteo_rv = {lib: sum(1 for k in orden_rv if k[0] == lib and texto_rv[k]) for lib in LIBROS}   # sin los versículos vacíos
    vacios_rv = [k for k in orden_rv if not texto_rv[k]]

    heb = {}
    heb.update(leer_oshb(obtener("oshb_gen", sin_red), "Gn"))
    heb.update(leer_oshb(obtener("oshb_exo", sin_red), "Ex"))
    heb.update(leer_oshb(obtener("oshb_lev", sin_red), "Lv"))
    heb.update(leer_oshb(obtener("oshb_num", sin_red), "Nm"))
    gr = leer_swete(obtener("swete_vers", sin_red), obtener("swete_pal", sin_red))
    bloques = leer_bloques_tvtms(obtener("tvtms", sin_red))
    t_rv, t_heb, t_gr = Tradicion(texto_rv), Tradicion(heb), Tradicion(gr)

    # ---- hebreo: mapa RV -> TM
    mapa_h, notas_h = construir_mapa(bloques, "Hebrew", t_heb, t_rv, orden_rv, estricto=True)
    aplicar_rv_propia(mapa_h, notas_h)
    if sorted(vacios_rv) != sorted(k for k, v in RV_PROPIA.items() if not v):
        fallo(f"versículos vacíos de la RV inesperados: {[ref(*k) for k in vacios_rv]}")
    hebreo, sin_hebreo = {}, {}
    usados_h = {}
    for k in orden_rv:
        ds = mapa_h.get(k)
        if not texto_rv[k]:                              # versículo vacío en la RV (su texto está en otro): sin hebreo
            if ds:
                fallo(f"versículo vacío {ref(*k)} con hebreo asignado")
            continue
        if not ds or not all(d in heb for d in ds):
            sin_hebreo[ref(*k)] = notas_h.get(k, "sin correspondencia en el TVTMS")
            continue
        for d in ds:
            if d in usados_h:
                fallo(f"hebreo {ref(*d)} asignado a {ref(*usados_h[d])} y a {ref(*k)}")
            usados_h[d] = k
        e = {"t": " ".join(heb[d] for d in ds)}
        if ds != [k]:
            if len(ds) > 1:                              # varios versículos hebreos seguidos en uno de la RV
                orden_h = sorted(heb)
                if any(orden_h.index(b) != orden_h.index(a) + 1 for a, b in zip(ds, ds[1:])):
                    fallo(f"{ref(*k)}: versículos hebreos no seguidos {ds}")
                a, z = ds[0], ds[-1]
                e["r"] = f"{a[0]} {a[1]}:{a[2]}-" + (f"{z[2]}" if z[1] == a[1] else f"{z[1]}:{z[2]}")
            else:
                e["r"] = ref(*ds[0])
        hebreo[ref(*k)] = e
    sobrantes_h = [ref(*d) for d in heb if d not in usados_h]
    if sobrantes_h:
        fallo(f"versículos hebreos sin asignar: {sobrantes_h[:10]}")
    if sin_hebreo:
        fallo(f"versículos RV sin hebreo: {list(sin_hebreo)[:10]}")
    renum_h = {k: v["r"] for k, v in hebreo.items() if "r" in v}
    inv_h = {d: k for d, k in usados_h.items()}          # TM -> RV

    # ---- griego: mapa RV -> Swete
    mapa_g, notas_g = construir_mapa(bloques, "Greek", t_gr, t_rv, orden_rv, estricto=False)
    aplicar_rv_propia(mapa_g, notas_g)
    for k, (d, pal_gr, pal_rv) in CORRECCIONES_GRIEGO.items():
        if pal_gr in gr.get(d, "") and pal_rv in texto_rv[k] and k not in mapa_g:
            mapa_g[k] = [d]
            notas_g[k] = ("Corrección propia (inferido por el contenido): el TVTMS da «Exo.40:12-15 → Exo.40:12-13», "
                          "incoherente con sus filas 40:12 → 40:10 y 40:13 → 40:11; aquí "
                          f"{ref(*d)} griego («{pal_gr}») corresponde a {ref(*k)} RV («{pal_rv}»).")
        else:
            fallo(f"corrección griega {ref(*k)}: ya no aplica o el contenido no coincide")
    griego, ref_griega, notas_griego, sin_griego = {}, {}, {}, {}
    usos_g = {}
    for k in orden_rv:
        ds = mapa_g.get(k)
        if not texto_rv[k]:                              # versículo vacío en la RV: ni griego ni «sin_texto»
            if ds:
                fallo(f"versículo vacío {ref(*k)} con griego asignado")
            continue
        if not ds or not all(d in gr for d in ds):
            sin_griego[ref(*k)] = notas_g.get(k) or "la edición de Swete no tiene este versículo con esa numeración"
            continue
        griego[ref(*k)] = " ".join(gr[d] for d in ds)
        if ds != [k]:
            ref_griega[ref(*k)] = ref(*ds[0]) + "".join(", " + (ref(*d) if d[1] != ds[0][1] else str(d[2])) for d in ds[1:])
        if k in notas_g:
            notas_griego[ref(*k)] = notas_g[k]
        for d in ds:
            usos_g.setdefault(d, []).append(ref(*k))
    for d, ks in usos_g.items():
        if len(ks) > 1:
            for kk in ks:
                notas_griego[kk] = (notas_griego.get(kk, "") + f" El versículo griego {ref(*d)} se reparte entre {', '.join(ks)} (se repite completo).").strip()
    for k, (p_rv, p_gr) in ANCLAS_GRIEGO.items():
        if p_rv not in texto_rv[k] or p_gr not in griego.get(ref(*k), ""):
            fallo(f"ancla griega {ref(*k)}: se esperaba «{p_rv}» en la RV y «{p_gr}» en el griego")
    griego_sin_asignar = [ref(*d) for d in sorted(gr, key=lambda x: (LIBROS.index(x[0]), x[1], x[2])) if d not in usos_g]

    # ---- rollos
    pal = leer_dss(sin_red)
    testigos = list(CODICES)
    for claves, sigla, llid, per, djd, escritura in ROLLOS:
        vs = set()
        for c in claves:
            for kheb, ws in pal.get(c, {}).items():
                if any(cons for _, cons in ws):
                    if kheb not in inv_h:
                        fallo(f"{c}: {ref(*kheb)} no existe en el TM")
                        continue
                    vs.add(inv_h[kheb])
        num = claves[0] if len(claves) == 1 else re.match(r"\d+Q\d+", claves[0]).group(0)
        extra = ROLLO_EXTRA.get(num, {})
        if extra.get("sin_calculo"):
            if vs:
                fallo(f"{num}: ahora tiene versículos en ETCBC/dss; revisar «sin_calculo»")
            if num not in ROLLOS_PRESENTES:
                fallo(f"{num}: no aparece en ETCBC/dss")
        elif not vs:
            fallo(f"{sigla}: sin versículos en ETCBC/dss")
        if extra.get("sin_calculo"):
            nota = extra["nota"]
        elif extra.get("sin_ficha"):
            nota = ("Contenido calculado: versículos con al menos una letra conservada (sin contar el texto reconstruido por los editores) "
                    "según los datos de Abegg (ETCBC/dss), pasados a numeración RV. No encontré ficha de este rollo en la Leon Levy Library "
                    f"(la dirección {LL}{num}-1 responde 404 y su buscador no lo devuelve; consultado el 2026-11-11): sin período, sigla ni edición oficial comprobados, "
                    "y el enlace lleva a los datos de Abegg.")
        else:
            nota = ("Contenido calculado: versículos con al menos una letra conservada (sin contar el texto reconstruido por los editores) "
                    "según los datos de Abegg (ETCBC/dss), pasados a numeración RV. La fecha es la etiqueta paleográfica de la Leon Levy Library, no una fecha numérica.")
            nota += extra.get("nota", "")
        if claves[0].startswith("4Q8"):
            nota += (" Reúne 4Q8a (h1), 4Q8b (h2) y 4Q8c (h-para, paráfrasis) de los datos de Abegg; la correspondencia con las fichas 4Q8-2/-3/-4 de la Leon Levy es inferida."
                     " Se excluye 4Q8d (Abegg lo sitúa en Gn 1:1; sería el fragmento del título). El período es el de la ficha general 4Q8-1.")
        if num == "4Q1":
            nota += " La lista de Wikipedia le atribuye «Gn 8:20–21»; los datos de Abegg no lo confirman y no se usa."
        sin_ficha = extra.get("sin_ficha")
        testigos.append({
            "id": num, "sigla": sigla, "nombre": sigla if sigla == num else f"{sigla} ({num})", "tipo": "rollo",
            "idioma": extra.get("idioma", "hebreo"), "escritura": escritura or "no consta",
            "fecha": "sin dato" if sin_ficha else PERIODO[per],
            "fecha_certeza": "sin ficha en la Leon Levy Library" if sin_ficha else "datación paleográfica",
            "contiene": comprimir(vs, indice),
            "institucion": "Autoridad de Antigüedades de Israel (IAA)",
            "url": "https://github.com/ETCBC/dss" if sin_ficha else LL + llid, "uso": "solo_enlace", "edicion": djd, "nota": nota,
            "fuente": ("Contenido: ETCBC/dss (Abegg, Bowley y Cook), CC BY-NC 4.0; ficha de la Leon Levy no encontrada (2026-11-11)" if sin_ficha else
                       "Leon Levy Dead Sea Scrolls Digital Library (período y edición oficial, ficha consultada el 2026-11-11)"
                       + ("; contenido: no calculado" if extra.get("sin_calculo") else "; contenido: ETCBC/dss (Abegg, Bowley y Cook), CC BY-NC 4.0")),
        })

    # ---- variantes (cada cifra se comprueba en el texto de la fuente)
    def heb_cons(r):
        return consonantes(hebreo[r]["t"])

    def dss_lectura(sc, k):
        ws = pal.get(sc, {}).get(k, [])
        txt = ""
        for t, _ in ws:                     # Abegg separa prefijos (ו, ל, ב…) y el sof pasuq
            t = t.strip()
            if not t:
                continue
            if t == "׃" or txt.endswith(tuple(" " + p for p in "ובלכהמש")) or txt in tuple("ובלכהמש"):
                txt += t
            else:
                txt += (" " if txt else "") + t
        return txt, [t for t, c in ws if c]

    l13, cons13 = dss_lectura("4Q13", ("Ex", 1, 5))
    l1, cons1 = dss_lectura("4Q1", ("Ex", 1, 5))
    if not ("שבעים" in heb_cons("Ex 1:5") and "חמש" not in heb_cons("Ex 1:5")):
        fallo("Ex 1:5 hebreo: se esperaba «שבעים» sin «חמש»")
    if "πέντε" not in griego.get("Ex 1:5", ""):
        fallo("Ex 1:5 griego sin «πέντε»")
    if not (any("חמש" in t for t in cons13) and any("שבעים" in t for t in cons13)):
        fallo("4Q13 Ex 1:5: «חמש» y «שבעים» deberían estar conservados")
    if not any("חמש" in t for t in cons1):
        fallo("4Q1 Ex 1:5: «חמש» debería estar conservado")
    if "setenta" not in texto_rv[("Ex", 1, 5)]:
        fallo("RV Ex 1:5 sin «setenta»")
    m_gr15 = re.search(r"πέντε καὶ ἑβδομήκοντα", griego.get("Ex 1:5", ""))
    variantes = [{
        "ref": "Ex 1:5", "tema": "¿Setenta o setenta y cinco personas de la casa de Jacob?",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["Ex 1:5"]["t"],
             "traduccion_es": "Y todas las personas que salieron del muslo de Jacob fueron setenta personas; y José estaba en Egipto (traducción propia, literal).",
             "cifra": 70},
            {"testigos": ["4Q13"], "texto_original": l13,
             "traduccion_es": "…cinco y setenta personas (traducción propia; «]» marca el borde roto del fragmento).",
             "cifra": 75},
            {"testigos": ["4Q1"], "texto_original": l1,
             "traduccion_es": "…[setenta] y cinco personas (traducción propia; «setenta» es reconstrucción de los editores, «y cinco» está conservado).",
             "nota": "Transcripción de Abegg: [ ] = texto reconstruido por los editores; # = letra dañada o dudosa.",
             "cifra": 75},
            {"testigos": ["vaticano"], "texto_original": m_gr15.group(0) if m_gr15 else "",
             "traduccion_es": "cinco y setenta (traducción propia).",
             "cifra": 75, "nota": "Texto de la edición de Swete, cuya base para Éxodo es el Códice Vaticano. Hechos 7:14 también dice 75 (fuente externa, no comprobado en esta app)."},
        ],
        "fuente": "Ediciones oficiales: F. M. Cross, DJD 12 (1994), pp. 79-95 (4QExod-b = 4Q13); J. R. Davila, DJD 12 (1994), pp. 7-30 (4QGen-Exod-a = 4Q1), según la Leon Levy Library. Lectura de los rollos comprobada en los datos de Abegg (ETCBC/dss); TM en el WLC; LXX en Swete.",
        "url_fuente": LL + "4Q13-1",
        "nota": "Texto: las cifras se leen en cada fuente (el script lo comprueba). Divulgación: M. Z. Brettler, TheTorah.com, https://www.thetorah.com/article/all-of-jacobs-descendants-numbered-seventy-five-the-opening-of-exodus-in-the-dead-sea-scrolls (solo leí el título). La RV1909 sigue al TM («setenta»).",
    }]
    if "נלכה" in heb_cons("Gn 4:8"):
        fallo("Gn 4:8 hebreo: no debería tener «נלכה»")
    m48 = re.search(r"[Δδ]ιέλθωμεν εἰς τὸ πεδίον", griego.get("Gn 4:8", ""))
    if not m48:
        fallo("Gn 4:8 griego: falta «διέλθωμεν εἰς τὸ πεδίον»")
    variantes.append({
        "ref": "Gn 4:8", "tema": "¿Qué le dijo Caín a Abel?",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["Gn 4:8"]["t"],
             "traduccion_es": "Y dijo Caín a Abel su hermano; y sucedió que, estando ellos en el campo, Caín se levantó contra Abel su hermano y lo mató (traducción propia, literal: el texto no dice qué le dijo)."},
            {"testigos": ["alejandrino"], "texto_original": m48.group(0) if m48 else "",
             "traduccion_es": "Pasemos al campo (traducción propia).",
             "nota": "Texto de la edición de Swete. Para Gn 1:1–46:28 el Vaticano no conserva el original y Swete lo suple con otro uncial, normalmente el Alejandrino (inferido; no comprobé en su aparato qué códice usa en este versículo)."},
        ],
        "fuente": "Comparación directa de las ediciones: WLC (OSHB) y Swete (LXX-Swete-1930).",
        "url_fuente": "https://github.com/eliranwong/LXX-Swete-1930",
        "nota": "Texto (las palabras se comprueban en cada edición). El Pentateuco Samaritano también trae la frase según la bibliografía, pero no hay fuente abierta verificada y no se incluye.",
    })
    if "השביעי" not in heb_cons("Gn 2:2").split("ויכל")[-1][:60]:
        fallo("Gn 2:2 hebreo: se esperaba «השביעי» al principio")
    m22 = re.search(r"τῇ ἡμέρᾳ τῇ ἕκτῃ", re.sub(r"[\[\]]", "", griego.get("Gn 2:2", "")))
    if not m22 or "] τῇ ἕκτῃ" not in griego.get("Gn 2:2", ""):
        fallo("Gn 2:2 griego: falta «τῇ ἡμέρᾳ τῇ ἕκτῃ» (con «τῇ ἕκτῃ» fuera de corchetes)")
    variantes.append({
        "ref": "Gn 2:2", "tema": "¿Acabó Dios su obra el día séptimo o el sexto?",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["Gn 2:2"]["t"],
             "traduccion_es": "Y acabó Dios en el día séptimo su obra que había hecho… (traducción propia, literal)."},
            {"testigos": ["alejandrino"], "texto_original": griego.get("Gn 2:2", ""),
             "traduccion_es": "Y acabó Dios en el día sexto sus obras que hizo, y descansó en el día séptimo de todas sus obras que hizo (traducción propia).",
             "nota": "Texto de la edición de Swete (ver la nota de Gn 4:8 sobre el códice que usa en Génesis). Los corchetes de Swete marcan letras que faltan en el códice (hay daños en Gn 1:29–2:3); «τῇ ἕκτῃ» (el sexto) está fuera de ellos."},
        ],
        "fuente": "Comparación directa de las ediciones: WLC (OSHB) y Swete (LXX-Swete-1930).",
        "url_fuente": "https://github.com/eliranwong/LXX-Swete-1930",
        "nota": "Texto. La RV1909 sigue al TM («el séptimo día»).",
    })
    if not ("במצרים" in heb_cons("Ex 12:40") and "כנען" not in heb_cons("Ex 12:40")):
        fallo("Ex 12:40 hebreo: se esperaba «במצרים» sin «כנען»")
    m1240 = re.search(r"ἐν γῇ Αἰγύπτῳ καὶ ἐν γῇ Χανάαν ἔτη τετρακόσια τριάκοντα πέντε", griego.get("Ex 12:40", ""))
    if not m1240:
        fallo("Ex 12:40 griego: falta «ἐν γῇ Αἰγύπτῳ καὶ ἐν γῇ Χανάαν ἔτη τετρακόσια τριάκοντα πέντε»")
    if "ארבע מאות שנה" not in heb_cons("Ex 12:40") or "שלשים שנה" not in heb_cons("Ex 12:40"):
        fallo("Ex 12:40 hebreo: se esperaba «שלשים שנה וארבע מאות שנה» (430)")
    variantes.append({
        "ref": "Ex 12:40", "tema": "¿Los 430 años fueron solo en Egipto?",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["Ex 12:40"]["t"],
             "traduccion_es": "Y el tiempo que los hijos de Israel habitaron en Egipto fue cuatrocientos treinta años (traducción propia, literal)."},
            {"testigos": ["vaticano"], "texto_original": griego.get("Ex 12:40", ""),
             "traduccion_es": "Y la estancia de los hijos de Israel, que habitaron en tierra de Egipto y en tierra de Canaán, fue de cuatrocientos treinta y cinco años (traducción propia).",
             "nota": "Texto de la edición de Swete (base: Códice Vaticano). Además de añadir «y en tierra de Canaán», este texto dice 435 años, no 430; otras ediciones de la LXX (y la traducción de Brenton que usa biblia.js) dan 430: no lo comprobé en ellas."},
        ],
        "fuente": "Comparación directa de las ediciones: WLC (OSHB) y Swete (LXX-Swete-1930).",
        "url_fuente": "https://github.com/eliranwong/LXX-Swete-1930",
        "nota": "Texto. La cronología de la app (biblia.js, supuesto «e430») ya trata las dos lecturas. El Pentateuco Samaritano no se incluye (sin fuente abierta verificada).",
    })

    # ---- videos
    ruta_oe = CACHE / "oembed.json"
    cache_oe = json.loads(ruta_oe.read_text(encoding="utf-8")) if ruta_oe.exists() else {}
    videos = []
    for lib, vid, titulo, rango, cert in VIDEOS:
        r = oembed(vid, sin_red, cache_oe)
        if not r or r.get("estado") != 200:
            fallo(f"video {vid}: oEmbed no verificado ({r})")
            continue
        if r.get("author_name") != "Proyecto Biblia" or r.get("title") != titulo:
            fallo(f"video {vid}: título o canal distinto: {r.get('title')} / {r.get('author_name')}")
        videos.append({"libro": lib, "titulo": titulo, "youtube_id": vid, "idioma": "es", "rango": rango,
                       "rango_certeza": cert, "fuente": "Proyecto Biblia / BibleProject",
                       "url": "https://www.youtube.com/watch?v=" + vid, "verificado": "oEmbed 200, " + r["comprobado"]})
    for vid in VIDEOS_DESCARTADOS:
        r = oembed(vid, sin_red, cache_oe)
        if r and r.get("estado") == 200:
            fallo(f"video descartado {vid} ahora responde 200: revisar")
    CACHE.mkdir(parents=True, exist_ok=True)
    ruta_oe.write_text(json.dumps(cache_oe, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- verificaciones generales
    for lib in LIBROS:
        nh = sum(1 for r in hebreo if r.startswith(lib + " "))
        if nh != conteo_rv[lib]:
            fallo(f"{lib}: hebreo {nh} versículos frente a RV {conteo_rv[lib]}")
    for rv_r, he_r in (("Gn 31:55", "Gn 32:1"), ("Ex 8:1", "Ex 7:26"), ("Ex 8:4", "Ex 7:29"), ("Ex 22:1", "Ex 21:37"),
                       ("Gn 32:1", "Gn 32:2"), ("Ex 8:5", "Ex 8:1"), ("Ex 22:2", "Ex 22:1"),
                       ("Lv 6:1", "Lv 5:20"), ("Lv 6:7", "Lv 5:26"), ("Lv 6:8", "Lv 6:1"), ("Lv 6:30", "Lv 6:23"),
                       ("Lv 5:19", None), ("Lv 7:1", None),
                       ("Nm 12:15", None), ("Nm 13:1", "Nm 12:16"), ("Nm 13:2", "Nm 13:1"), ("Nm 13:32", "Nm 13:31"), ("Nm 13:33", "Nm 13:32-33"),
                       ("Nm 16:35", None), ("Nm 16:36", "Nm 17:1"), ("Nm 16:50", "Nm 17:15"), ("Nm 17:1", "Nm 17:16"), ("Nm 17:13", "Nm 17:28"),
                       ("Nm 25:18", None), ("Nm 26:1", "Nm 25:19-26:1"), ("Nm 26:2", None), ("Nm 29:39", None), ("Nm 30:1", None),
                       ("Nm 30:15", None), ("Nm 30:16", "Nm 30:16-17")):
        if renum_h.get(rv_r) != he_r:
            fallo(f"numeración: RV {rv_r} debería ser hebreo {he_r}, es {renum_h.get(rv_r)}")
    for r in ("Nm 12:16", "Nm 29:40"):                      # vacíos en la RV: ni hebreo ni griego ni «sin_texto»
        if r in hebreo or r in griego or r in sin_griego:
            fallo(f"{r} (vacío en la RV) no debería tener original")
    for k, (p_rv, p_he) in ANCLAS_HEBREO.items():
        if p_rv not in texto_rv[k] or p_he not in consonantes(hebreo.get(ref(*k), {}).get("t", "")).split():
            fallo(f"ancla hebrea {ref(*k)}: se esperaba «{p_rv}» en la RV y «{p_he}» en el hebreo")
    for t in testigos:
        for campo in ("id", "nombre", "tipo", "fecha", "fecha_certeza", "contiene", "institucion", "url", "uso", "nota", "fuente"):
            if campo not in t or (campo not in ("contiene",) and not t[campo]):
                fallo(f"testigo {t.get('id')}: falta {campo}")
        if not t["url"].startswith("https://"):
            fallo(f"testigo {t['id']}: url no válida")
    ids = {t["id"] for t in testigos}
    for v in variantes:
        if not v.get("fuente") or not v.get("url_fuente", "").startswith("https://"):
            fallo(f"variante {v['ref']}: sin fuente o url")
        for l in v["lecturas"]:
            if not l["texto_original"]:
                fallo(f"variante {v['ref']}: lectura vacía")
            for tid in l["testigos"]:
                if tid not in ids:
                    fallo(f"variante {v['ref']}: testigo {tid} no existe")
    ex15 = griego.get("Ex 1:5", "")
    if not ("πέντε" in ex15 or "ἑβδομήκοντα πέντε" in ex15):
        fallo("Ex 1:5 griego")

    if FALLOS:
        print(f"\n{len(FALLOS)} verificaciones fallidas; no se escriben los archivos.")
        sys.exit(1)

    # ---- escribir
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    orig = {
        "generado": ahora,
        "fuentes": FUENTES,
        "hebreo_nota": ("Texto hebreo del Códice de Leningrado (WLC 4.20) con vocales y acentos; sin morfología, notas ni marcas de párrafo (פ/ס). "
                        "Clave = referencia en numeración RV1909; «r» = referencia hebrea cuando difiere (correspondencia del TVTMS, CC BY 4.0)."),
        "hebreo": hebreo,
        "testigos": testigos,
        "variantes": variantes,
        "videos": videos,
        "videos_descartados": [{"youtube_id": k, "motivo": v} for k, v in VIDEOS_DESCARTADOS.items()],
    }
    cab_o = "// Generado por herramientas/originales.py; no editar a mano. Fuentes y licencias en «fuentes».\n"
    t1 = escribir_js(DATOS / "originales.js", cab_o, "BIBLIA_ORIGINALES", orig)
    griego_obj = {
        "fuente": ("H. B. Swete, The Old Testament in Greek according to the Septuagint (Cambridge University Press; ed. 1930), "
                   "digitalización LXX-Swete-1930 de Eliran Wong (texto compilado por P. Amicarelli). Swete imprime el Códice Vaticano "
                   "y lo suple con otro uncial (sobre todo el Alejandrino) donde falta, como en Gn 1:1–46:28."),
        "licencia": "GPL-3.0 (texto de Swete 1930 en dominio público; digitalización GPL)",
        "url": "https://github.com/eliranwong/LXX-Swete-1930",
        "nota": ("Clave = referencia RV1909. Swete numera como la LXX, que en Gn 2, Gn 5, Ex 20, 21, 25, 28 y 35–40, Lv 7 y Nm 1, 13 y 30 difiere de la RV: "
                 "la correspondencia se toma del TVTMS (STEPBible, CC BY 4.0), eligiendo en cada bloque la columna griega cuyos TEST cumple esta edición. "
                 "«ref_griega» da la referencia de Swete cuando difiere; «sin_texto» lista los versículos RV sin equivalente completo en la LXX, con el motivo."),
        "texto": griego,
        "ref_griega": ref_griega,
        "notas": notas_griego,
        "sin_texto": sin_griego,
        "griego_sin_asignar": griego_sin_asignar,
    }
    cab_g = ("// LXX de Swete (1930) por versículo. Digitalización: LXX-Swete-1930 (Eliran Wong), licencia GNU GPL-3.0.\n"
             "// Este archivo se distribuye bajo la GPL-3.0: ver datos/LICENCIA-griego-swete.txt y https://www.gnu.org/licenses/gpl-3.0.html\n"
             "// El texto impreso de Swete es de dominio público. Generado por herramientas/originales.py; no editar a mano.\n")
    t2 = escribir_js(DATOS / "griego-swete.js", cab_g, "BIBLIA_GRIEGO", griego_obj)
    lic = obtener("swete_lic", sin_red).read_text(encoding="utf-8")
    (DATOS / "LICENCIA-griego-swete.txt").write_text(
        "datos/griego-swete.js — Septuaginta de Swete (Génesis, Éxodo, Levítico y Números)\n\n"
        "Texto: H. B. Swete, The Old Testament in Greek according to the Septuagint, Cambridge University Press (ed. 1930). Dominio público.\n"
        "Digitalización: LXX-Swete-1930, Eliran Wong (https://github.com/eliranwong/LXX-Swete-1930), licencia GNU GPL-3.0.\n"
        "Modificaciones: palabras unidas por versículo y claves pasadas a la numeración de la RV1909 con el TVTMS (STEPBible, CC BY 4.0).\n"
        "El archivo griego-swete.js se distribuye bajo la misma GPL-3.0; el resto de la app no deriva de él.\n"
        "Texto de la licencia: https://www.gnu.org/licenses/gpl-3.0.html (copia íntegra a continuación, tomada del repositorio de origen).\n\n"
        + "=" * 72 + "\n\n" + lic, encoding="utf-8")

    # ---- resumen
    print("Conteos RV:", conteo_rv)
    for lib in LIBROS:
        print(f"  {lib}: hebreo {sum(1 for r in hebreo if r.startswith(lib + ' '))}, "
              f"griego {sum(1 for r in griego if r.startswith(lib + ' '))}, sin griego {sum(1 for r in sin_griego if r.startswith(lib + ' '))}")
    print("Renumeración hebrea (RV -> TM):", len(renum_h), "versículos; casos:",
          {k: renum_h[k] for k in ("Gn 31:55", "Ex 8:1", "Ex 8:4", "Ex 22:1")})
    print("Griego con referencia distinta:", len(ref_griega), "· griego sin asignar:", len(griego_sin_asignar))
    print("Ex 1:5 heb:", heb_cons("Ex 1:5")[-30:], "| gr:", m_gr15.group(0) if m_gr15 else None, "| 4Q13:", l13)
    print(f"Testigos: {len(testigos)} ({len(CODICES)} códices, {len(ROLLOS)} rollos) · variantes: {len(variantes)} · videos: {len(videos)}")
    print(f"Escritos: originales.js {t1/1e6:.2f} MB, griego-swete.js {t2/1e6:.2f} MB, LICENCIA-griego-swete.txt")
    print("Verificación: OK")


if __name__ == "__main__":
    main()
