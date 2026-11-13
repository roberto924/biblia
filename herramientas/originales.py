"""Fase 7b: textos originales y testigos de Génesis, Éxodo, Levítico, Números, Deuteronomio, Josué, Jueces, Rut, 1 Samuel, 2 Samuel, 1 Reyes y 2 Reyes.

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
import math
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
    "oshb_deu": (GH + "openscriptures/morphhb/master/wlc/Deut.xml", "oshb_Deut.xml"),
    "oshb_jos": (GH + "openscriptures/morphhb/master/wlc/Josh.xml", "oshb_Josh.xml"),
    "uxlc_jos": ("https://tanach.us/Books/Joshua.xml", "uxlc_Joshua.xml"),   # solo para leer la marca «X» (versículo ausente del Códice de Leningrado)
    "oshb_jue": (GH + "openscriptures/morphhb/master/wlc/Judg.xml", "oshb_Judg.xml"),
    "uxlc_jue": ("https://tanach.us/Books/Judges.xml", "uxlc_Judges.xml"),  # marca «X» (no hay en Jueces) y letra suspendida de Jue 18:30
    "oshb_rut": (GH + "openscriptures/morphhb/master/wlc/Ruth.xml", "oshb_Ruth.xml"),
    "uxlc_rut": ("https://tanach.us/Books/Ruth.xml", "uxlc_Ruth.xml"),      # marca «X» (no hay en Rut) y ketiv/qere (<k>/<q>) para cotejar con OSHB
    "oshb_1s": (GH + "openscriptures/morphhb/master/wlc/1Sam.xml", "oshb_1Sam.xml"),
    "uxlc_1s": ("https://tanach.us/Books/Samuel_1.xml", "uxlc_Samuel_1.xml"),  # marca «X» (no hay en 1 S), ketiv/qere y 13:1 para cotejar con OSHB
    "oshb_2s": (GH + "openscriptures/morphhb/master/wlc/2Sam.xml", "oshb_2Sam.xml"),
    "uxlc_2s": ("https://tanach.us/Books/Samuel_2.xml", "uxlc_Samuel_2.xml"),  # marca «X» y ketiv/qere para cotejar con OSHB
    "oshb_1r": (GH + "openscriptures/morphhb/master/wlc/1Kgs.xml", "oshb_1Kgs.xml"),
    "uxlc_1r": ("https://tanach.us/Books/Kings_1.xml", "uxlc_Kings_1.xml"),    # marca «X» y ketiv/qere para cotejar con OSHB
    "oshb_2r": (GH + "openscriptures/morphhb/master/wlc/2Kgs.xml", "oshb_2Kgs.xml"),
    "uxlc_2r": ("https://tanach.us/Books/Kings_2.xml", "uxlc_Kings_2.xml"),    # marca «X» y ketiv/qere para cotejar con OSHB
    "tvtms": (TVTMS_URL, "tvtms.txt"),
    "swete_vers": (GH + "eliranwong/LXX-Swete-1930/master/00-Swete_versification.csv",
                   "swete_00-Swete_versification.csv"),
    "swete_pal": (GH + "eliranwong/LXX-Swete-1930/master/01-Swete_word_with_punctuations.csv",
                  "swete_01-Swete_word_with_punctuations.csv"),
    "swete_lic": (GH + "eliranwong/LXX-Swete-1930/master/LICENSE", "swete_LICENSE.txt"),
}
for _f in ("otype", "oslots", "scroll", "book", "chapter", "verse", "rec", "full", "fragment", "line"):
    ARCHIVOS["dss_" + _f] = (GH + "ETCBC/dss/master/tf/2.0/%s.tf" % _f, "dss_%s.tf" % _f)

LIBROS = ("Gn", "Ex", "Lv", "Nm", "Dt", "Jos", "Jue", "Rut", "1S", "2S", "1R", "2R")
LIBRO_OSIS = {"Gn": "Gen", "Ex": "Exo", "Lv": "Lev", "Nm": "Num", "Dt": "Deu", "Jos": "Jos", "Jue": "Jdg", "Rut": "Rut", "1S": "1Sa", "2S": "2Sa", "1R": "1Ki", "2R": "2Ki"}          # códigos TVTMS / Swete
OSIS_LIBRO = {"Gen": "Gn", "Exo": "Ex", "Exod": "Ex", "Lev": "Lv", "Num": "Nm", "Deu": "Dt", "Deut": "Dt", "Jos": "Jos", "Josh": "Jos",
              "Jdg": "Jue", "Judg": "Jue", "Rut": "Rut", "Ruth": "Rut", "1Sa": "1S", "1Sam": "1S", "2Sa": "2S", "2Sam": "2S", "1Ki": "1R", "1Kgs": "1R", "2Ki": "2R", "2Kgs": "2R"}
DSS_LIBRO = {"Gen": "Gn", "Ex": "Ex", "Lev": "Lv", "Num": "Nm", "Deut": "Dt", "Josh": "Jos", "Judg": "Jue", "Ruth": "Rut", "1Sam": "1S", "2Sam": "2S", "1Kgs": "1R", "2Kgs": "2R"}            # códigos de libro en ETCBC/dss
OSIS_RE = "Gen|Exo|Lev|Num|Deu|Jos|Jdg|Rut|1Sa|2Sa|1Ki|2Ki"                               # libros TVTMS / Swete que se leen
FALLOS = []
ROLLOS_PRESENTES = set()          # nombres de rollo que aparecen en ETCBC/dss (lo llena leer_dss)
ORDEN_DSS = {}                    # rollo -> [(slot, fragmento, línea, (lib, c, v))] en el orden del rollo (lo llena leer_dss)


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
                elif tag == "w":                         # itertext: incluye las letras grandes o pequeñas (<seg> dentro de <w>)
                    partes.append(("w", "".join(h.itertext()).replace("/", "")))
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


def leer_uxlc_x(ruta, lib):
    """Versículos con la marca «X» del UXLC (tanach.us): «This verse does NOT occur in the Leningrad Codex»."""
    s = ruta.read_text(encoding="utf-8")
    if "This verse does NOT occur in the Leningrad Codex" not in s:
        fallo("UXLC: falta la definición de la nota «X»")
    res = []
    for mc in re.finditer(r'<c n="(\d+)">(.*?)</c>', s, re.S):
        for mv in re.finditer(r'<v n="(\d+)">(.*?)</v>', mc[2], re.S):
            if "<x>X</x>" in mv[2]:
                res.append((lib, int(mc[1]), int(mv[1])))
    return res


def leer_kq_oshb(ruta, lib):
    """Ketiv/qere del WLC (OSHB): {(lib, c, v): [(ketiv sin «/» o None, qere con vocales o None)]} en el orden del versículo.
    Ketiv = <w type="x-ketiv">; qere = <note type="variant"><rdg type="x-qere"> (sin <catchWord>: qere sin ketiv; qere vacío: ketiv sin qere)."""
    res = {}
    for verso in ET.parse(ruta).getroot().iter(OSIS_NS + "verse"):
        _, c, v = verso.get("osisID").split(".")
        k, lista = (lib, int(c), int(v)), []
        for h in verso.iter():
            tag = h.tag.replace(OSIS_NS, "")
            if tag == "w" and h.get("type") == "x-ketiv":
                lista.append(["".join(h.itertext()).replace("/", ""), None])
            elif tag == "note" and h.get("type") == "variant":
                rdg = h.find(OSIS_NS + "rdg")
                if rdg is None or rdg.get("type") != "x-qere":
                    continue
                q = "".join(rdg.itertext()).replace("/", "").strip() or None
                cw = h.find(OSIS_NS + "catchWord")
                if cw is not None and lista and lista[-1][0] == (cw.text or "").replace("/", "") and lista[-1][1] is None:
                    lista[-1][1] = q
                else:
                    lista.append([None, q])
        if lista:
            res[k] = [tuple(x) for x in lista]
    return res


def leer_kq_uxlc(ruta, lib):
    """Ketiv/qere del UXLC: {(lib, c, v): ([ketiv…], [qere…])} (etiquetas <k> y <q>)."""
    s = ruta.read_text(encoding="utf-8")
    res = {}
    for mc in re.finditer(r'<c n="(\d+)">(.*?)</c>', s, re.S):
        for mv in re.finditer(r'<v n="(\d+)">(.*?)</v>', mc[2], re.S):
            ks, qs = re.findall(r"<k>(.*?)</k>", mv[2]), re.findall(r"<q>(.*?)</q>", mv[2])
            if ks or qs:
                res[(lib, int(mc[1]), int(mv[1]))] = (ks, qs)
    return res


def uxlc_consonantes(ruta, c, v):
    """Consonantes de un versículo del UXLC (sin notas)."""
    s = ruta.read_text(encoding="utf-8")
    mc = re.search(r'<c n="%d">(.*?)</c>' % c, s, re.S)
    mv = mc and re.search(r'<v n="%d">(.*?)</v>' % v, mc[1], re.S)
    return consonantes(re.sub(r"<x>.*?</x>|<[^>]+>", " ", mv[1])) if mv else ""


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
    un = r"(?:%s)\.\d+:\d+(?:\*\d+)?" % OSIS_RE
    m = re.match(r"(%s(?:\+%s)*)([<>])(%s(?:\+%s)*)$" % (un, un, un, un), expr)
    if m:                                              # largos de versículos (sumas: «Num.1:32+Num.1:33>…»; múltiplos: «1Ki.6:6*2»)
        def suma(lado):
            tot = 0
            for p in lado.split("+"):
                q = re.match(r"(\w+)\.(\d+):(\d+)(?:\*(\d+))?$", p)
                x = trad.largo(OSIS_LIBRO[q[1]], int(q[2]), int(q[3]))
                if x is None:
                    return None
                tot += x * int(q[4] or 1)
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
            eng = [(c, v, None if s == "0" else s) for (c, v, s) in eng]   # «.0» en la KJV = el versículo (Jos 9:27.0 frente a 9:27.1-6, que es otra tradición)
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
    # 1 Samuel 23–24: la RV1909 (eBible) numera como el hebreo (23:29 vacío; su 24:1 = KJV 23:29; su 24:22 reúne KJV 24:21-22).
    # Comprobado por contenido: RV 24:1 «Engaddi» = TM 24:1 (עין גדי); RV 24:22 «David juró» = TM 24:23 (וישבע).
    m[("1S", 23, 29)] = []
    m[("1S", 24, 1)] = [("1S", 23, 29)]
    for v in range(2, 22):
        m[("1S", 24, v)] = [("1S", 24, v - 1)]
    m[("1S", 24, 22)] = [("1S", 24, 21), ("1S", 24, 22)]
    # 2 Samuel 20: la RV1909 (eBible) deja vacío el 20:26 y pone su texto («é Ira Jaireo fué un jefe principal cerca de David») al final de 20:25.
    # Comprobado por contenido: TM 20:26 = «וגם עירא היארי היה כהן לדוד» (ancla RV 20:25 «Jaireo» = היארי).
    m[("2S", 20, 25)] = [("2S", 20, 25), ("2S", 20, 26)]
    m[("2S", 20, 26)] = []
    return m


RV_PROPIA = _rv_propia()
NOTA_RV_PROPIA = {          # (libro, capítulo) -> nota; un versículo vacío usa la del capítulo siguiente
    ("Nm", 13): ("La RV1909 (eBible) numera Nm 13 de otra forma que el TM y la KJV: su 13:1 es el 12:16 de ambos (su 12:16 queda vacío) "
         "y su 13:33 reúne los versículos 13:32-33. Correspondencia propia sobre el TVTMS, comprobada por contenido."),
    ("Nm", 30): ("La RV1909 (eBible) numera Nm 30 como el TM (su 29:40 queda vacío), pero su 30:16 reúne los versículos 30:16-17 del TM "
         "(30:15-16 de la KJV). Correspondencia propia sobre el TVTMS, comprobada por contenido."),
    ("1S", 24): ("La RV1909 (eBible) numera 1 S 23–24 como el hebreo, no como la KJV que sigue en el resto del libro: su 23:29 queda vacío, "
                 "su 24:1 («Engaddi») es el 23:29 de la KJV y el 24:1 del TM, y su 24:22 reúne los versículos 24:21-22 de la KJV (24:22-23 del TM). "
                 "Correspondencia propia sobre el TVTMS, comprobada por contenido."),
    ("2S", 20): ("La RV1909 (eBible) deja vacío 2 S 20:26 y pone su texto («é Ira Jaireo fué un jefe principal cerca de David») al final de 20:25: "
                 "su 20:25 reúne los versículos 20:25-26 del TM, la KJV y la LXX. Correspondencia propia sobre el TVTMS, comprobada por contenido."),
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
        nota = NOTA_RV_PROPIA[(rv[0], rv[1]) if (rv[0], rv[1]) in NOTA_RV_PROPIA else (rv[0], rv[1] + 1)]
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
    rutas = {f: obtener("dss_" + f, sin_red) for f in ("otype", "oslots", "scroll", "book", "chapter", "verse", "rec", "full", "fragment", "line")}
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
    frag = leer_tf(rutas["fragment"])
    lin = leer_tf(rutas["line"])
    ROLLOS_PRESENTES.update(scroll.values())
    a, z = tipos["line"]
    lineas_l = sorted((rango_slots(osl[n]), scroll[n]) for n in range(a, z + 1) if n in scroll and n in osl)
    inicios = [r[0][0] for r in lineas_l]
    a, z = tipos["line"]
    lineas_n = sorted((rango_slots(osl[n]), n) for n in range(a, z + 1) if n in scroll and n in osl)
    a, z = tipos["fragment"]
    frags = sorted((rango_slots(osl[n]), frag.get(n, "")) for n in range(a, z + 1) if n in osl)
    ini_f = [r[0][0] for r in frags]
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
        jf = bisect.bisect_right(ini_f, s0) - 1
        fr = frags[jf][1] if jf >= 0 and frags[jf][0][0] <= s0 <= frags[jf][0][1] else ""
        ORDEN_DSS.setdefault(sc, []).append((s0, fr, lin.get(lineas_n[j][1], ""), k))
    for v in ORDEN_DSS.values():
        v.sort()
    return palabras


# ------------------------------------------------------------------ datos fijos
FUENTES = [
    {"id": "wlc-oshb", "nombre": "Westminster Leningrad Codex 4.20 (texto del Códice de Leningrado), vía Open Scriptures Hebrew Bible (morphhb)",
     "licencia": "Texto WLC: dominio público. Atribución: Open Scriptures Hebrew Bible (lemas y morfología CC BY 4.0, no usados aquí)",
     "url": "https://github.com/openscriptures/morphhb"},
    {"id": "uxlc", "nombre": "UXLC 2.6 (Unicode/XML Leningrad Codex), C. V. Kimball, tanach.us: solo se leen su marca «X» (versículo que no está en el Códice de Leningrado: Jos 21:36-37; en Jueces y en Rut no hay ninguna), su marca de letra suspendida en Jue 18:30 (nota «7») y, en Rut, 1 Samuel y 2 Samuel, sus ketiv/qere (<k>/<q>) para cotejarlos con el WLC (también en 1 Reyes y 2 Reyes; y en 1 S 13:1, el comienzo del versículo); en 2 Reyes, además, sus consonantes, para compararlas versículo a versículo con el WLC",
     "licencia": "«Freely available» según su cabecera (no se redistribuye su texto)", "url": "https://tanach.us/Books/Joshua.xml, https://tanach.us/Books/Judges.xml, https://tanach.us/Books/Ruth.xml, https://tanach.us/Books/Samuel_1.xml, https://tanach.us/Books/Samuel_2.xml, https://tanach.us/Books/Kings_1.xml y https://tanach.us/Books/Kings_2.xml"},
    {"id": "tvtms", "nombre": "TVTMS (Translators Versification Traditions with Methodology for Standardisation), STEPBible / Tyndale House",
     "licencia": "CC BY 4.0", "url": "https://github.com/STEPBible/STEPBible-Data/tree/master/Versification"},
    {"id": "swete", "nombre": "H. B. Swete, The Old Testament in Greek (Cambridge, ed. 1930), digitalización LXX-Swete-1930 (Eliran Wong)",
     "licencia": "GPL-3.0 (texto de Swete en dominio público; digitalización GPL); va aparte en datos/griego-swete.js",
     "url": "https://github.com/eliranwong/LXX-Swete-1930"},
    {"id": "etcbc-dss", "nombre": "ETCBC/dss: datos de los Rollos del Mar Muerto de M. Abegg, J. Bowley y E. Cook (conversión Text-Fabric de J. Jacobs, M. Naaijer y D. Roorda)",
     "licencia": "CC BY-NC 4.0. Solo se usan para calcular qué versículos conserva cada rollo y para verificar Ex 1:5, Dt 32:8, el orden de Jos 8:30-35 en 4Q47, que 4Q49 pasa de Jue 6:6 a 6:11, las lecturas de 4Q104 (Rut 1:2, 1:9) y 2Q17 (Rut 3:14, 3:15) las de 4Q51 en 1 Samuel (1:24, 2:9, 2:10, 10:27, 17:4) en 2 Samuel (5:6, 6:2, 8:4, 11:3, 13:21, 13:27, 24:16) la de 4Q54 en 1 R 8:16 y la de 6Q4 en 2 R 7:8; no se redistribuye su texto salvo las lecturas breves citadas en esas variantes",
     "url": "https://github.com/ETCBC/dss"},
    {"id": "leon-levy", "nombre": "The Leon Levy Dead Sea Scrolls Digital Library (Israel Antiquities Authority): fichas con período y edición oficial (DJD)",
     "licencia": "Solo enlace: las imágenes no se pueden reproducir sin permiso de la IAA (https://www.deadseascrolls.org.il/terms)",
     "url": "https://www.deadseascrolls.org.il/"},
    {"id": "wikipedia", "nombre": "Wikipedia en inglés (fuente secundaria para fechas y contenido de los códices), consultada el 2026-11-11, el 2026-11-12 (Jueces y Rut) y el 2026-11-13 (2 Samuel, 1 Reyes y 2 Reyes)",
     "licencia": "CC BY-SA 4.0 (solo se toman datos, no texto)", "url": "https://en.wikipedia.org/"},
    {"id": "cudl", "nombre": "Cambridge Digital Library (Cambridge University Library): ficha del Papiro Nash, MS Or.233 (registro JSON)",
     "licencia": "Metadatos CC BY-NC 4.0 (solo se toman datos); imágenes: solo enlace", "url": "https://cudl.lib.cam.ac.uk/view/MS-OR-00233"},
    {"id": "manchester", "nombre": "Manchester Digital Collections (John Rylands Library): ficha del Papiro Rylands 458 (Greek P 458)",
     "licencia": "Metadatos CC BY-NC 4.0 (solo se toman datos); imágenes: solo enlace", "url": "https://www.digitalcollections.manchester.ac.uk/view/MS-GREEK-P-00458"},
    {"id": "proyecto-biblia", "nombre": "Proyecto Biblia (BibleProject en español), canal de YouTube",
     "licencia": "Solo inserción del reproductor de YouTube; no se descarga ni se modifica", "url": "https://www.youtube.com/@ProyectoBibliaOficial"},
]

CODICES = [
    {"id": "leningrado", "nombre": "Códice de Leningrado (Firkovich B 19 A)", "tipo": "codice", "idioma": "hebreo",
     "fecha": "1008 (o 1009) d. C.", "fecha_certeza": "colofón",
     "contiene": ["Gn 1:1-Gn 50:26", "Ex 1:1-Ex 40:38", "Lv 1:1-Lv 27:34", "Nm 1:1-Nm 36:13", "Dt 1:1-Dt 34:12", "Jos 1:1-Jos 21:35", "Jos 21:38-Jos 24:33", "Jue 1:1-Jue 21:25", "Rut 1:1-Rut 4:22", "1S 1:1-1S 31:13", "2S 1:1-2S 24:25", "1R 1:1-1R 22:53", "2R 1:1-2R 25:30"],
     "institucion": "Biblioteca Nacional de Rusia, San Petersburgo",
     "url": "https://archive.org/details/Leningrad_Codex", "uso": "solo_enlace",
     "nota": "Es la base del texto hebreo de esta app (WLC). Copiado en El Cairo según su colofón. Facsímil en archive.org (B/N, 988 págs.; en color: https://archive.org/details/Leningrad_Codex_Color_Images); licencia del facsímil no declarada: solo enlace. NO tiene Jos 21:36-37: el UXLC (tanach.us) los marca «X», «This verse does NOT occur in the Leningrad Codex» (comprobado al generar); el WLC los incluye solo para no romper la numeración y aquí van sin hebreo. Jueces: entero; el UXLC no marca con «X» ningún versículo de Jueces (comprobado al generar). Rut: entero; el UXLC tampoco marca con «X» ningún versículo de Rut (comprobado al generar). En este códice Rut va en los Ketuvim (tras Proverbios), no tras Jueces como en la RV (Wikipedia «Leningrad Codex»). 1 Samuel: entero; el UXLC no marca con «X» ningún versículo de 1 Samuel (comprobado al generar). 2 Samuel: entero; el UXLC tampoco marca con «X» ningún versículo de 2 Samuel (comprobado al generar). 1 Reyes: entero; el UXLC no marca con «X» ningún versículo de 1 Reyes (comprobado al generar). 2 Reyes: entero; el UXLC tampoco marca con «X» ningún versículo de 2 Reyes, y sus consonantes coinciden con las del WLC en los 719 versículos (comprobado al generar).",
     "fuente": "Wikipedia «Leningrad Codex» (fecha, signatura, institución y facsímiles), consultada el 2026-11-11; Jos 21:36-37: UXLC 2.x, https://tanach.us/Books/Joshua.xml (nota «X»); Jueces: https://tanach.us/Books/Judges.xml (2026-11-12); Rut: https://tanach.us/Books/Ruth.xml (2026-11-12); 1 Samuel: https://tanach.us/Books/Samuel_1.xml (2026-11-12); 2 Samuel: https://tanach.us/Books/Samuel_2.xml (2026-11-13); 1 Reyes: https://tanach.us/Books/Kings_1.xml (2026-11-13); 2 Reyes: https://tanach.us/Books/Kings_2.xml (2026-11-13)"},
    {"id": "alepo", "nombre": "Códice de Alepo", "tipo": "codice", "idioma": "hebreo",
     "fecha": "c. 920 d. C. (Tiberíades)", "fecha_certeza": "estimación (un colofón posterior atribuye la vocalización a Aarón ben Moisés ben Aser)",
     "contiene": ["Dt 28:17-Dt 34:12", "Jos 1:1-Jos 21:35", "Jos 21:38-Jos 24:33", "Jue 1:1-Jue 21:25", "Rut 1:1-Rut 4:22", "1S 1:1-1S 31:13", "2S 1:1-2S 24:25", "1R 1:1-1R 22:53", "2R 1:1-2R 14:20", "2R 18:14-2R 25:30"],
     "institucion": "Museo de Israel (Santuario del Libro), Jerusalén",
     "url": "https://www.aleppocodex.org/", "uso": "solo_enlace",
     "nota": "NO conserva Génesis, Éxodo, Levítico ni Números: le falta todo el Pentateuco hasta Dt 28:17. De Deuteronomio, «contiene» va desde Dt 28:17 hasta el final (inferido: la fuente no lista otras lagunas en Dt; no comprobé si el 28:17 está entero). Solo se han recuperado aparte un fragmento con partes de Éx 8 (publicado por Yosef Ofer en 2016) y otra hoja de Éxodo aparecida en los años 80; no verifiqué sus versículos exactos y no van en «contiene». Josué: la lista de partes perdidas de la fuente no lo nombra (inferido: completo); Jos 21:36-37, que faltan en el Códice de Leningrado, no van en «contiene» porque no comprobé si este códice los tiene. Jueces: la lista de partes perdidas de la fuente tampoco lo nombra (inferido: completo; releída el 2026-11-12). Rut: la fuente da el orden de los Ketuvim de este códice (Crónicas, Salmos, Job, Proverbios, Rut, Cantar…) y su lista de lo perdido en esa parte empieza en Cantar 3:11; no nombra Rut (inferido: completo; 2026-11-12). 1 Samuel: la lista de lo perdido de la fuente (Pentateuco hasta Dt 28:17, 2 Re 14:21–18:13, partes de Jeremías, Amós–Miqueas, Sofonías–Zacarías, 2 Crónicas, Salmos, Cantar desde 3:11 y los Ketuvim finales) no lo nombra (inferido: completo; releída el 2026-11-12). 2 Samuel: esa misma lista tampoco lo nombra (inferido: completo; no se volvió a abrir la fuente para 2 S). 1 Reyes: la lista de lo perdido, releída el 2026-11-13, empieza «The current text is missing all of the Pentateuch to the Book of Deuteronomy 28.17; II Kings 14.21–18.13…»: nombra 2 Reyes, no 1 Reyes (inferido: completo). 2 Reyes: esa lista da perdido «II Kings 14.21–18.13»; «contiene» es el resto, 2 R 1:1–14:20 y 18:14–25:30 (la RV1909 numera esos capítulos como el hebreo; inferido: la fuente no dice si los versículos de los bordes están enteros; no se volvió a abrir la fuente para 2 R).",
     "fuente": "Wikipedia «Aleppo Codex», consultada el 2026-11-11, el 2026-11-12 (Jueces, Rut y 1 Samuel) y el 2026-11-13 (1 Reyes)"},
    {"id": "vaticano", "nombre": "Códice Vaticano (Vat. gr. 1209)", "tipo": "codice", "idioma": "griego (Septuaginta)",
     "fecha": "c. 300–350 d. C.", "fecha_certeza": "datación paleográfica",
     "contiene": ["Gn 46:28-Gn 50:26", "Ex 1:1-Ex 40:38", "Lv 1:1-Lv 27:34", "Nm 1:1-Nm 36:13", "Dt 1:1-Dt 34:12", "Jos 1:1-Jos 24:33", "Jue 1:1-Jue 21:25", "Rut 1:1-Rut 4:22"],
     "institucion": "Biblioteca Apostólica Vaticana",
     "url": "https://digi.vatlib.it/view/MSS_Vat.gr.1209", "uso": "solo_enlace",
     "nota": "Se perdieron las hojas con Gn 1:1–46:28a; las que hay ahora son una reposición del s. XV (no son testigo antiguo). La fuente solo menciona como perdidos, en el Antiguo Testamento, Gn 1:1–46:28a, Sal 105:27–137:6b y «2 Kings 2:5–7, 10–13» (es 2 Samuel, «2 Reinos» en la LXX: ver abajo) (inferido: Éxodo, Levítico, Números, Deuteronomio y Josué presentes; «contiene» de Josué va con la numeración RV, aunque la LXX ordena y numera parte del libro de otra forma, p. ej. el altar del Ebal tras Jos 9:2). Gn 46:28 se conserva solo en parte (desde 46:28b). En Ex 35–40 la Septuaginta ordena y numera el texto de otra forma. Jueces: la fuente no lo cita entre lo perdido (inferido: presente), dice que en Jueces su texto difiere mucho del de la mayoría de los manuscritos y coincide con la Vetus Latina, la versión sahídica y Cirilo de Alejandría, y da su lectura de Jue 18:30, «υἱὸς Μανασση» (según Rahlfs). Es la forma «B» de Jueces: la que imprime Swete y la que muestra esta app. Rut: la fuente lo nombra al describir la página (44 líneas por columna en el Pentateuco, Josué, Jueces, Rut y 1 Reyes 1:1–19:11) y no lo cita entre lo perdido (inferido: completo; 2026-11-12). 1 Samuel (1 Reinos en la LXX): la fuente no lo cita entre lo perdido (solo Gn 1:1–46:28a y Sal 105:27–137:6b) (inferido: presente). Su texto es más breve que el TM: «contiene» de 1 Samuel es un cálculo, los versículos RV que tienen texto en la edición de Swete, que imprime este códice (inferido); los que no lo tienen —13:1, gran parte de 1 S 17–18, 20:16 y 23:12— se listan en «sin_texto» del griego (comprobado en los datos de Swete, 2026-11-12). 2 Samuel (2 Reinos en la LXX): Wikipedia da como perdidos por una hoja rota «2 Kings 2:5–7, 10–13»; la Introducción de Swete (cap. V) precisa «Through the tearing of fol. 178 2 Regn. ii. 5–7, 10–13, has also disappeared», es decir 2 S 2:5-7 y 2:10-13, que no van en «contiene». El resto de 2 Samuel: «contiene» es un cálculo, los versículos RV con texto en la edición de Swete menos esos siete (inferido: Swete imprime este códice). 1 Reyes (3 Reinos en la LXX): ni Wikipedia ni la Introducción de Swete (cap. V: «Every book of the Greek O. T. is included, except 1 -- 4 Maccabees»; en Reinos solo da perdidos 2 Regn. ii. 5–7, 10–13) citan nada perdido (inferido: presente). «contiene» es un cálculo: los versículos RV con texto en la edición de Swete (inferido: Swete imprime este códice); los que la LXX no tiene en su sitio van en «sin_texto» del griego y los bloques que añade, en «bloques_sin_paralelo». 2 Reyes (4 Reinos en la LXX): las mismas fuentes tampoco citan nada perdido (inferido: presente). «contiene» es un cálculo: los versículos RV con texto en la edición de Swete, es decir, todos menos 25:10, que la digitalización trae vacío (ver «sin_texto» del griego); el bloque que añade tras 1:18 va en «bloques_sin_paralelo».",
     "fuente": "Wikipedia «Codex Vaticanus», consultada el 2026-11-11 y el 2026-11-12 (Jueces, Rut y 1 Samuel); 1 Samuel: cálculo sobre la edición de Swete (LXX-Swete-1930); 2 Samuel: la misma página (2026-11-13), H. B. Swete, «An Introduction to the Old Testament in Greek», cap. V (texto en https://biblehub.com/library/swete/an_introduction_to_the_old_testament_in_greek_additional_notes/chapter_v_manuscripts_of_the.htm, consultado el 2026-11-13) y cálculo sobre la edición de Swete"},
    {"id": "sinaitico", "nombre": "Códice Sinaítico", "tipo": "codice", "idioma": "griego (Septuaginta)",
     "fecha": "c. 325–360 d. C.", "fecha_certeza": "datación paleográfica",
     "contiene": ["Gn 23:19-Gn 24:46", "Lv 20:27-Lv 22:30", "Jos 1:10", "Jue 5:7-Jue 11:2"],
     "institucion": "British Library, Biblioteca Universitaria de Leipzig, Monasterio de Santa Catalina y Biblioteca Nacional de Rusia (repartido)",
     "url": "https://codexsinaiticus.org/", "uso": "solo_enlace",
     "nota": "De Génesis solo quedan fragmentos de Gn 23:19–24:46; NO contiene Éxodo; de Levítico conserva Lv 20:27–22:30 (lista de contenidos de Wikipedia, según Würthwein y Swete). De Números, Deuteronomio y Josué la misma lista dice solo «fragmentos», sin versículos: no se añaden a «contiene», salvo Jos 1:10, el texto del fragmento que halló Nikolas Sarris en 2009 en el monasterio de Santa Catalina (según Wikipedia, que cita a The Independent del 2 de septiembre de 2009; no comprobado en la fuente original). No comprobé el contenido de las hojas del Pentateuco halladas en 1975 en el Sinaí. No pude abrir codexsinaiticus.org (no respondió) ni confirmar en qué institución están esas hojas. Jueces: la lista de contenidos de Wikipedia da «5:7 - 11:2 + fragments»: en «contiene» va Jue 5:7–11:2 (no comprobado en las imágenes; los «fragmentos», sin versículos, no se añaden). Rut: la lista de contenidos de Wikipedia no lo nombra (releída el 2026-11-12): no va en «contiene»; no comprobé si se conserva algo. 1 Samuel: la misma lista tampoco lo nombra (pasa de Jueces a 1 Crónicas 9:27; 2026-11-12): no va en «contiene». 2 Samuel: tampoco lo nombra, ni la lista del contenido que da la Introducción de Swete (cap. V; 2026-11-13): no va en «contiene». 1 Reyes: tampoco lo nombran ni Wikipedia ni la Introducción de Swete (releída el 2026-11-13): no va en «contiene». 2 Reyes: tampoco lo nombran esas dos listas (las releídas para 1 Reyes; no se volvieron a abrir): no va en «contiene».",
     "fuente": "Wikipedia «Codex Sinaiticus», consultada el 2026-11-11 y el 2026-11-12 (Jueces, Rut y 1 Samuel)"},
    {"id": "alejandrino", "nombre": "Códice Alejandrino (Royal MS 1 D V–VIII)", "tipo": "codice", "idioma": "griego (Septuaginta)",
     "fecha": "c. 400–440 d. C.", "fecha_certeza": "datación paleográfica",
     "contiene": ["Gn 1:1-Gn 50:26", "Ex 1:1-Ex 40:38", "Lv 1:1-Lv 27:34", "Nm 1:1-Nm 36:13", "Dt 1:1-Dt 34:12", "Jos 1:1-Jos 24:33", "Jue 1:1-Jue 21:25", "Rut 1:1-Rut 4:22", "1S 1:1-1S 12:16", "1S 14:10-1S 31:13", "2S 1:1-2S 24:25", "1R 1:1-1R 22:53", "2R 1:1-2R 25:30"],
     "institucion": "British Library, Londres",
     "url": "https://www.bl.uk/manuscripts/FullDisplay.aspx?ref=Royal_MS_1_D_V", "uso": "solo_enlace",
     "nota": "El primer volumen contiene de Génesis a 2 Crónicas (inferido: Éxodo, Levítico, Números, Deuteronomio y Josué presentes; la fuente no los nombra ni cita daños en Números, Deuteronomio ni Josué, y da lecturas suyas de Jos 10:42 y 11:1). Dañados Gn 14:14–17, 15:1–5, 15:16–19 y 16:6–9; defectos por hojas rotas en Gn 1:20–25, 1:29–2:3 y Lv 8:6, 8:7 y 8:16 (según Swete). El enlace de la British Library responde, pero no comprobé que muestre las imágenes del volumen I. Jueces: inferido presente (va en el primer volumen; la fuente da su lectura de Jue 18:30, «υιος Μωυση», «hijo de Moisés», según Rahlfs). Es la forma «A» de Jueces, que la digitalización de Swete no trae: su texto no está en esta app. Rut: la fuente cita el facsímil de Kenyon (1915) «Vol. 1: Genesis – Ruth» y no da daños en Rut (inferido: completo; 2026-11-12). 1 Samuel: la fuente da como perdida una hoja con 1 S 12:17–14:9 (según Würthwein) y cita el facsímil de Kenyon (1930) «Vol. 2: 1 Samuel – 2 Chronicles»; «contiene» es el resto del libro (inferido: no cita más daños; 2026-11-12). Su texto de 1 Samuel no está en esta app (Swete imprime el Vaticano). 2 Samuel: la Introducción de Swete (cap. V) solo da en 1-2 Reinos la laguna «1 Regn. xii. 18—xiv. 9 (leaf missing)», ninguna en 2 Reinos, y Wikipedia tampoco cita daños (inferido: completo; 2026-11-13). Su texto de 2 Samuel tampoco está en esta app. 1 Reyes (3 Reinos): va en el primer volumen («vol. i. Genesis -- 2 Chronicles», Introducción de Swete, cap. V), que en Reinos solo da la laguna de 1 Regn. xii. 18 – xiv. 9 (inferido: completo; 2026-11-13). Su texto tampoco está en esta app. 2 Reyes (4 Reinos): lo mismo, va en el primer volumen y la fuente no da lagunas en 4 Reinos (inferido: completo; no se volvió a abrir la fuente). Su texto tampoco está en esta app.",
     "fuente": "Wikipedia «Codex Alexandrinus», consultada el 2026-11-11 y el 2026-11-12 (Jueces, Rut y 1 Samuel); 2 Samuel: H. B. Swete, «An Introduction to the Old Testament in Greek», cap. V (biblehub.com, 2026-11-13)"},
    {"id": "samaritano-cul-add1846", "nombre": "Pentateuco Samaritano, Cambridge University Library Add. 1846", "tipo": "pentateuco_samaritano",
     "idioma": "hebreo (escritura samaritana)",
     "fecha": "comienzos del s. XII d. C. (según el catálogo de Cambridge)", "fecha_certeza": "no verificada en la ficha (dato del catálogo leído solo a través de un buscador)",
     "contiene": [],
     "institucion": "Cambridge University Library",
     "url": "https://cudl.lib.cam.ac.uk/view/MS-ADD-01846", "uso": "solo_enlace",
     "nota": "Considerado el manuscrito conservado más antiguo del Pentateuco Samaritano. Lleva una nota de un escriba que cuenta cómo se salvó de un incendio en 1201. La ficha de Cambridge Digital Library devolvió 403 a la consulta automática: no confirmé el contenido por versículos (tampoco el de Levítico, Números ni Deuteronomio), por eso «contiene» va vacío.",
     "fuente": "Catálogo de Cambridge University Library (vía buscador, 2026-11-11); no abierto directamente"},
    {"id": "papiro-nash", "nombre": "Papiro Nash (Cambridge University Library, MS Or.233)", "tipo": "papiro", "idioma": "hebreo",
     "fecha": "mediados del s. II a. C. (según la ficha de Cambridge)", "fecha_certeza": "datación paleográfica (la ficha cita a Albright 1937; el informe de la biblioteca de 1903 lo situaba en el s. I d. C.)",
     "contiene": ["Dt 5:4-Dt 5:21", "Dt 6:4-Dt 6:5"],
     "institucion": "Cambridge University Library",
     "url": "https://cudl.lib.cam.ac.uk/view/MS-OR-00233", "uso": "solo_enlace",
     "nota": "Una hoja de papiro (cuatro trozos unidos), 24 líneas, probablemente del Fayum (Egipto). Según la ficha contiene los Diez Mandamientos, en un texto mixto de Éx 20:1-17 y Dt 5:4-21, seguidos del Shemá (Dt 6:4-5); quizá era de una filacteria o un texto litúrgico. Solo se pone Deuteronomio en «contiene» (el texto de Éxodo va mezclado y la ficha no da qué versículos de cada libro sigue); los versículos están dañados (agujeros, «barely legible»). La página de Cambridge Digital Library devolvió 403 a la consulta automática; los datos se leyeron en su registro JSON (MS-OR-00233.json) el 2026-11-11. Imágenes CC BY-NC 4.0 según la ficha: aquí solo se enlazan.",
     "fuente": "Cambridge Digital Library, ficha MS Or.233 (registro JSON consultado el 2026-11-11)"},
    {"id": "rylands-458", "nombre": "Papiro Rylands 458 (P. Ryl. Gr. 458; Rahlfs 957)", "tipo": "papiro", "idioma": "griego (Septuaginta)",
     "fecha": "s. II a. C. (según la ficha de la John Rylands Library)", "fecha_certeza": "datación paleográfica (la ficha la apoya en la escritura y en la mano documental del reverso)",
     "contiene": ["Dt 24:1-Dt 24:3", "Dt 25:1-Dt 25:3", "Dt 26:12", "Dt 26:17-Dt 26:19", "Dt 27:15", "Dt 28:2", "Dt 28:31-Dt 28:33"],
     "institucion": "The John Rylands Library, Universidad de Mánchester",
     "url": "https://www.digitalcollections.manchester.ac.uk/view/MS-GREEK-P-00458", "uso": "solo_enlace",
     "nota": "Ocho fragmentos (a-h) de un rollo de papiro de Deuteronomio sacados de cartonaje de momia del Fayum; la ficha dice que están «dispersos entre los capítulos 23 y 28», sin versículos. Los versículos de «contiene» son de Wikipedia (según Würthwein): Dt 24:1-3, 25:1-3, 26:12, 26:17-19, 27:15, 28:2 y 28:31-33, todos fragmentarios; Wikipedia da además «23:24(26)» al principio del primer tramo, con numeración ambigua, y no se añade. En Dt 26:18 hay un hueco donde se esperaría el nombre de Dios (fuente externa: Wikipedia).",
     "fuente": "Manchester Digital Collections, ficha Greek P 458 (abierta el 2026-11-11: fecha, institución, fragmentos); versículos: Wikipedia «Papyrus Rylands 458», consultada el 2026-11-11"},
]

LL = "https://www.deadseascrolls.org.il/explore-the-archive/manuscript/"
PERIODO = {"Hasmonean": "período asmoneo", "Herodian": "período herodiano", "Roman": "período romano",
           "Hellenistic-Roman": "período helenístico-romano", "Early Hellenistic": "período helenístico temprano"}
ED38 = ("Duncan 1995, DJD 14: 93-108; Puech 2001, RevQ 20: 123-127; Tigchelaar 2004, RevQ 21: 647-648; "
        "Tigchelaar 2008, RevQ 23: 525-528 («A Forgotten Qumran Cave 4 Deuteronomy Fragment (4Q38d = 4QDeut/u)»)")   # misma lista en las fichas del grupo 4Q38
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
    # Deuteronomio (fichas de la Leon Levy leídas el 2026-11-11 con un script: campos «copy», «period», «script_type» y «official_publications»).
    # No van filacterias ni mezuzot (1Q13, 4Q128-4Q146, 4Q150-4Q153, 8Q3, 8Q4, XQ1-3) ni los de fuera de Qumrán (Mas1c, Mur2, Mur4, XHev/Se3, XHev/Se5).
    (["1Q4"], "1QDeut-a", "1Q4-1", "Hellenistic-Roman", "Barthélemy 1955, DJD 1: 54-57", "cuadrada"),
    (["1Q5"], "1QDeut-b", "1Q5-1", "Hellenistic-Roman", "Barthélemy 1955, DJD 1: 57-62", "cuadrada"),
    (["2Q10"], "2QDeut-a", "2Q10-1", "Herodian", "Baillet 1962, DJD 3: 60", "cuadrada"),
    (["2Q11"], "2QDeut-b", "2Q11-1", "Herodian", "Baillet 1962, DJD 3: 60-61", "cuadrada"),
    (["2Q12"], "2QDeut-c", "2Q12-1", "Herodian", "Baillet 1962, DJD 3: 61-62", "cuadrada"),
    (["4Q28"], "4QDeut-a", "4Q28-1", "Hasmonean", "Crawford 1995, DJD 14: 7-8", "cuadrada"),
    (["4Q29"], "4QDeut-b", "4Q29-1", "Hasmonean", "Duncan 1995, DJD 14: 9-14; Tigchelaar 2004, RevQ 21: 646", "cuadrada"),
    (["4Q30"], "4QDeut-c", "4Q30-1", "Hasmonean", "Crawford 1995, DJD 14: 15-34 (la ficha da también «16-34»)", "cuadrada"),
    (["4Q31"], "4QDeut-d", "4Q31-1", "Hasmonean", "Crawford 1995, DJD 14: 35-38", "cuadrada"),
    (["4Q32"], "4QDeut-e", "4Q32-1", "Herodian", "Duncan 1995, DJD 14: 39-44", "cuadrada"),
    (["4Q33"], "4QDeut-f", "4Q33-1", "Hasmonean", "Crawford 1995, DJD 14: 45-54 (la ficha repite la entrada con errores: «Crawford 14. DJD 1995: 45-59»)", "cuadrada"),
    (["4Q34"], "4QDeut-g", "4Q34-1", "Herodian", "Crawford 1995, DJD 14: 55-59; Tigchelaar 2004, RevQ 21: 646", "cuadrada"),
    (["4Q35"], "4QDeut-h", "4Q35-1", "Herodian", "Duncan 1995, DJD 14: 61-70", "cuadrada"),
    (["4Q36"], "4QDeut-i", "4Q36-1", "Hasmonean", "Crawford 1995, DJD 14: 71-74", "cuadrada"),
    (["4Q37"], "4QDeut-j", "4Q37-1", "Herodian", "Duncan 1995, DJD 14: 70-91", "cuadrada"),
    (["4Q38"], "4QDeut-k", "4Q38-1", "Herodian", ED38, "cuadrada"),
    (["4Q38a"], "4Q38a", None, None, None, None),
    (["4Q38b"], "4QDeut-k", "4Q38b-1", "Herodian", ED38, "cuadrada"),
    (["4Q38c"], "4QDeut-t", "4Q38c-1", "Herodian", ED38, "cuadrada"),
    (["4Q38d"], "4QDeut-u", "4Q38d-1", "Herodian", ED38, "cuadrada"),
    (["4Q39"], "4QDeut-l", "4Q39-1", "Hasmonean", "Duncan 1995, DJD 14: 109-112", "cuadrada"),
    (["4Q40"], "4QDeut-m", "4Q40-1", "Herodian", "Duncan 1995, DJD 14: 113-116", "cuadrada"),
    (["4Q41"], "4QDeut-n", "4Q41-1", "Herodian", "Crawford 1995, DJD 14: 117-128", "cuadrada"),
    (["4Q42"], "4QDeut-o", "4Q42-1", "Hasmonean", "Crawford 1995, DJD 14: 129-133", "cuadrada"),
    (["4Q43"], "4QDeut-p", "4Q43-1", "Hasmonean", "Crawford 1995, DJD 14: 135-136", "cuadrada"),
    (["4Q44"], "4QDeut-q", "4Q44-1", "Herodian", "Skehan y Ulrich 1995, DJD 14: 137-142", "cuadrada"),
    (["4Q45"], "4QpaleoDeut-r", "4Q45-1", "Hasmonean", "Skehan, Ulrich y Sanderson 1992, DJD 9: 131-152", "paleohebrea"),
    (["4Q46"], "4QpaleoDeut-s", "4Q46-1", "Early Hellenistic", "Skehan, Ulrich y Sanderson 1992, DJD 9: 153-154", "paleohebrea"),
    (["5Q1"], "5QDeut", "5Q1-1", "Early Hellenistic", "Milik 1962, DJD 3: 169-171", "cuadrada"),
    (["6Q3"], "6QpapDeut(?)", "6Q3-1", "Hellenistic-Roman", "Baillet 1962, DJD 3: 106-107", "cuadrada (papiro)"),
    (["11Q3"], "11QDeut", "11Q3-1", "Herodian", "García Martínez, Tigchelaar y van der Woude 1998, DJD 23: 11-14", "cuadrada"),
    # Josué (fichas de la Leon Levy leídas el 2026-11-11 con un script: «copy», «period», «script_type», «official_publications»).
    # No va XJoshua (en los datos de Abegg, Jos 1:9-12 y 2:4-5): no es de Qumrán y la dirección XJosh-1 de la Leon Levy da 404.
    (["4Q47"], "4QJosh-a", "4Q47-1", "Hasmonean", "Ulrich 1995, DJD 14: 143-152", "cuadrada"),
    (["4Q48"], "4QJosh-b", "4Q48-1", "Hasmonean", "Tov 1995, DJD 14: 153-160", "cuadrada"),
    # Jueces (fichas de la Leon Levy descargadas con un script el 2026-11-12: «copy», «period», «script_type», «official_publications»).
    # No va «Xjudges» (en los datos de Abegg, Jue 1:10-13, 3:23-24 y 4:5-9): no es de Qumrán y la dirección XJudg-1 de la Leon Levy da 404.
    (["1Q6"], "1QJudg", "1Q6-1", "Hellenistic-Roman", "Barthélemy 1955, DJD 1: 62-64", "cuadrada"),
    (["4Q49"], "4QJudg-a", "4Q49-1", "Herodian", "Trebolle Barrera 1995, DJD 14: 161-164", "cuadrada"),
    (["4Q50"], "4QJudg-b", "4Q50-1", "Herodian", "Trebolle Barrera 1995, DJD 14: 165-169", "cuadrada"),
    # Rut (fichas de la Leon Levy descargadas con un script el 2026-11-12: «copy», «period», «script_type», «official_publications»).
    (["2Q16"], "2QRuth-a", "2Q16-1", "Herodian", "Baillet 1962, DJD 3: 71-74", "cuadrada"),
    (["2Q17"], "2QRuth-b", "2Q17-1", "Hasmonean", "Baillet 1962, DJD 3: 74-75", "cuadrada"),
    (["4Q104"], "4QRuth-a", "4Q104-1", "Hasmonean", "Ulrich y Murphy 2000, DJD 16: 187-189", "cuadrada"),
    (["4Q105"], "4QRuth-b", "4Q105-1", "Herodian", "Ulrich y Murphy 2000, DJD 16: 191-194", "cuadrada"),
    # 1 Samuel: todos los que hay en los datos de Abegg (fichas de la Leon Levy descargadas con un script el 2026-11-12: «copy», «period»,
    # «script_type», «official_publications»). 4Q51: la ficha 4Q51-2 («4Q Samuel», copia «a») no da período; se toma el de la ficha general 4Q51-1.
    (["1Q7"], "1QSam", "1Q7-1", "Hellenistic-Roman", "Barthélemy 1955, DJD 1: 64-65", "cuadrada"),
    (["4Q51"], "4QSam-a", "4Q51-2", "Herodian", "Cross, Parry y Saley 2005, DJD 17: 1-216 y 217", "cuadrada"),
    (["4Q52"], "4QSam-b", "4Q52-1", "Early Hellenistic", "Cross, Parry y Saley 2002, DJD 17: 219-246", "cuadrada"),
    (["4Q53"], "4QSam-c", "4Q53-1", "Hasmonean", "Ulrich 2002, DJD 17: 247-267", "cuadrada"),
    # 1 Reyes: todos los que hay en los datos de Abegg (fichas de la Leon Levy descargadas con un script el 2026-11-13: «name», «copy»,
    # «period», «script_type», «material», «official_publications»). Ninguna ficha da letra de copia.
    (["4Q54"], "4QKgs", "4Q54-1", "Herodian", "Trebolle Barrera 1995, DJD 14: 171-183", "cuadrada"),
    (["5Q2"], "5QKgs", "5Q2-1", "Hasmonean", "Milik 1962, DJD 3: 171-172", "cuadrada"),
    (["6Q4"], "6QpapKgs", "6Q4-1", "Hasmonean", "Baillet 1962, DJD 3: 107-112", "cuadrada (papiro)"),
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
    "4Q38": {"nota": " La ficha da la misma lista de ediciones para todo el grupo 4Q38 (no dice cuál corresponde a esta copia)."},
    "4Q38b": {"nota": " La ficha da la copia «k», igual que 4Q38. La ficha da la misma lista de ediciones para todo el grupo 4Q38 (no dice cuál corresponde a esta copia)."},
    "4Q38c": {"nota": " La ficha da la misma lista de ediciones para todo el grupo 4Q38 (no dice cuál corresponde a esta copia)."},
    "4Q38d": {"nota": " La ficha da la misma lista de ediciones para todo el grupo 4Q38 (no dice cuál corresponde a esta copia)."},
    "4Q38a": {"sin_ficha": True,
              "motivo_sin_ficha": "la dirección " + LL + "4Q38a-1 responde, pero sin datos de manuscrito, y 4Q38-2 y 4Q38-3 dan 404; no probé el buscador; consultado el 2026-11-11"},
    "4Q37": {"nota": " Abegg le asigna además versículos de Éx 12:43-13:16, que también van en «contiene». Es el testigo de la variante de Dt 32:8."},
    "4Q47": {"fuera_de_versiculo": [("Jos", 5, 0)],
             "nota": " En los fragmentos 1-2, tras Jos 8:34-35 (lectura de la ley junto al altar), viene un texto de enlace que Abegg numera «5:0» "
                     "(no es un versículo del TM; no entra en «contiene») y después Jos 5:2-7: es el testigo de la variante sobre el lugar del altar de Jos 8:30-35."},
    "1Q6": {"nota": " La ficha de la Leon Levy no da letra de copia («copy» vacío): sigla sin letra."},
    "4Q49": {"nota": " En el fragmento 1, la línea 5 conserva el final de Jue 6:6 y la línea 6 ya conserva Jue 6:11 (el principio de 6:11, al final de la línea 5, "
                     "es reconstrucción de los editores): el rollo no tiene Jue 6:7-10 (el profeta enviado a Israel). "
                     "Es el testigo de la variante de Jue 6:7-10 (comprobado al generar en los datos de Abegg)."},
    "4Q104": {"nota": " Es el testigo de las variantes de Rut 1:2 («וישבו», «y habitaron») y Rut 1:9 («קולם»), comprobadas al generar en los datos de Abegg."},
    "2Q17": {"nota": " Es el testigo de la variante de Rut 3:15 («שם», «allí», de más) y en Rut 3:14 escribe «מ[רג]לתיו», con la י de la qere (ver la nota del texto hebreo de Rut 3:14)."},
    "1Q7": {"nota": " La ficha de la Leon Levy («1Q Samuel») no da letra de copia («copy» vacío): sigla sin letra. En los datos de Abegg tiene también texto de 2 Samuel "
                    "(2 S 20:6-10, 21:16-19 y 23:9-12; ver «contiene»). Conserva letras de 1 S 18:17-18, versículos que la LXX de Swete no tiene (ver la variante de 1 S 17–18)."},
    "4Q51": {"nota": " Fichas de la Leon Levy: 4Q51-2 («4Q Samuel», copia «a», escritura cuadrada, sin período) y 4Q51-1, la ficha general del número "
                     "(«4Q Multiple Compositions», período herodiano, la misma edición DJD 17); la fecha es la de 4Q51-1. En los datos de Abegg tiene también "
                     "texto de 2 Samuel (letras conservadas en los 24 capítulos; ver «contiene»)."},
    "4Q53": {"nota": " En los datos de Abegg tiene también texto de 2 Samuel (2 S 14–15; ver «contiene»)."},
    "4Q54": {"nota": " La ficha de la Leon Levy («4Q Kings», pergamino) no da letra de copia («copy» vacío): sigla sin letra."},
    "5Q2": {"nota": " La ficha de la Leon Levy («5Q Kings», pergamino) no da letra de copia («copy» vacío): sigla sin letra."},
    "6Q4": {"nota": " La ficha de la Leon Levy («6Q papKings») no da letra de copia («copy» vacío): sigla sin letra. Es un papiro (campo «material» de la ficha)."},
    "4Q52": {"nota": " En 1 S 14:41 conserva solo «או» y una «ב» («o en…»), letras de la forma larga del versículo que tiene el griego (ver la variante de 1 S 14:41)."},
    "4Q41": {"nota": " Abegg le asigna además Éx 20:11 (dentro del Decálogo), que también va en «contiene»."},
    "6Q3": {"nota": " La Leon Levy lo titula «6Q papDeuteronomy(?)» (tipo «Biblical Compositions?»): la identificación es dudosa en la propia ficha. Papiro."},
    "2Q29": {"nota": " La Leon Levy lo cataloga como «2Q Unidentified» (sin libro ni copia); que contenga Nm 23 es la asignación de los datos de Abegg (inferido). "
                     "Por eso la sigla es solo el número."},
}

# Bloques del TVTMS donde la columna elegida por los TEST no encaja con el contenido de Swete.
COLUMNA_FORZADA = {
    "$Exo.35:8-35:27": ("Greek3 (Brenton)",
                        "columna elegida a mano (inferido): Swete sigue el mismo texto que Brenton (Códice Vaticano) y las anclas de contenido lo confirman, aunque no cumple el TEST «Exo.35:18=notExist»"),
    # 1 S 20:42–21:15: Swete numera como la Vulgata (20:42-43; 21:1-15), no como la columna griega del TVTMS (20:42; 21:1-16, la de Brenton).
    "$1Sa.20:42--21:15": ("Latin",
                          "columna «Latin» elegida a mano (comprobado por contenido): Swete numera aquí como la Vulgata, con un 20:43 «καὶ Ἰωναθὰν εἰσῆλθεν εἰς τὴν πόλιν» "
                          "(el final de RV 20:42, «Jonathán se entró en la ciudad») y 21:1-15 = RV 21:1-15; la columna griega del TVTMS (20:42; 21:1-16) no cumple sus TEST con esta edición"),
}
NOTA_ADICION_LXX = ("El texto griego trae, tras la marca «[1]» (y «[2]»…), frases que la LXX añade y que no están en el hebreo (TM) ni en la RV1909 "
                    "(inferido: la digitalización LXX-Swete-1930 marca así los subversículos 'a', 'b'… de Swete). Se dejan dentro de este versículo.")
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
    # Deuteronomio (Swete invierte Dt 5:17-18, no tiene «todo cuervo» de 14:14 y numera 14:15-29 RV como 14:14-28)
    ("Dt", 5, 6): ("Yo soy Jehová tu Dios", "Ἐγώ Κύριος ὁ θεός σου"), ("Dt", 5, 17): ("matarás", "φονεύσεις"),
    ("Dt", 5, 18): ("adulterarás", "μοιχεύσεις"), ("Dt", 5, 21): ("codiciarás", "ἐπιθυμήσεις"), ("Dt", 6, 4): ("Oye, Israel", "Ἄκουε, Ἰσραήλ"),
    ("Dt", 12, 32): ("no añadirás", "οὐ προσθήσεις"), ("Dt", 14, 15): ("buho", "στρουθὸν"), ("Dt", 14, 16): ("cisne", "κύκνον"),
    ("Dt", 22, 30): ("mujer de su padre", "γυναῖκα τοῦ πατρὸς"), ("Dt", 29, 1): ("Moab", "Μωάβ"),
    ("Dt", 34, 7): ("ciento y veinte", "ἑκατὸν καὶ εἴκοσι"),
    # Josué (Swete pone el altar del Ebal, RV 8:30-35, como 9:3-8 y numera RV 9:3-27 como 9:9-33; sigue el orden del TM en 24:29-31)
    ("Jos", 1, 1): ("Moisés", "Μωυσῆ"), ("Jos", 6, 20): ("muro", "τεῖχος"), ("Jos", 8, 30): ("Ebal", "Γαιβάλ"),
    ("Jos", 8, 35): ("mujeres y niños", "ταῖς γυναιξὶν"), ("Jos", 9, 3): ("Gabaón", "Γαβαὼν"), ("Jos", 9, 27): ("leñadores", "ξυλοκόπους"),
    ("Jos", 10, 13): ("el sol se detuvo", "ἔστη ὁ ἥλιος"), ("Jos", 21, 36): ("Rubén", "Ῥουβὴν"), ("Jos", 24, 29): ("ciento y diez", "ἑκατὸν δέκα"),
    ("Jos", 24, 30): ("Timnath-sera", "Θαμναθασαχαρὰ"),
    # Jueces (Swete = forma B, Códice Vaticano; misma numeración que el TM salvo el corte propio de la RV en 14:18-20)
    ("Jue", 1, 1): ("Josué", "Ἰησοῦ"), ("Jue", 4, 4): ("Débora", "Δεββωρὰ"), ("Jue", 7, 20): ("espada", "Ῥομφαία"),
    ("Jue", 14, 18): ("dulce", "γλυκύτερον"), ("Jue", 14, 19): ("araseis", "ἠροτριάσατε"), ("Jue", 14, 20): ("Ascalón", "Ἀσκάλωνα"),
    ("Jue", 16, 30): ("Muera yo con los Filisteos", "Ἀποθανέτω ψυχή μου μετὰ ἀλλοφύλων"), ("Jue", 18, 30): ("Manasés", "Μανασσή"),
    ("Jue", 21, 25): ("no había rey", "οὐκ ἦν βασιλεὺς"),
    # Rut (misma numeración en la RV, el TM y Swete; el TVTMS no tiene ningún bloque de Rut)
    ("Rut", 1, 16): ("Ruth respondió", "εἶπεν δὲ Ῥούθ"), ("Rut", 2, 3): ("Booz", "Βόος, τοῦ ἐκ συγγενείας Ἀβειμέλεχ"),
    ("Rut", 4, 17): ("Obed", "Ὠβήδ"), ("Rut", 4, 22): ("David", "Δαυείδ"),
    # 1 Samuel (Swete = 1 Reinos; numera 20:42-43 como la Vulgata y 24 como el hebreo)
    ("1S", 1, 20): ("Samuel", "Σαμουὴλ"), ("1S", 3, 10): ("Habla, que tu siervo oye", "Λάλει, ὅτι ἀκούει ὁ δοῦλός σου"),
    ("1S", 16, 13): ("ungiólo", "ἔχρισεν αὐτὸν"), ("1S", 17, 4): ("Goliath", "Γολιὰθ"), ("1S", 20, 42): ("se entró en la ciudad", "εἰσῆλθεν εἰς τὴν πόλιν"),
    ("1S", 21, 1): ("Nob", "Νόμβα"), ("1S", 24, 1): ("Engaddi", "Ἐνγάδδει"), ("1S", 24, 22): ("David juró", "ὤμοσεν Δαυεὶδ"),
    ("1S", 31, 6): ("murió Saúl", "ἀπέθανεν Σαοὺλ"),
    # 2 Samuel (Swete = 2 Reinos; numera 18:33/19 como la KJV y la Vulgata, no como la columna griega del TVTMS, que es la de Brenton)
    ("2S", 1, 1): ("Siclag", "Σεκελὰκ"), ("2S", 7, 12): ("estableceré tu simiente", "ἀναστήσω τὸ σπέρμα σου"),
    ("2S", 12, 7): ("Tú eres aquel hombre", "Σὺ εἶ ὁ ἀνὴρ"), ("2S", 18, 33): ("Hijo mío Absalom", "Υἱέ μου υἱέ μου Ἀβεσσαλώμ"),
    ("2S", 19, 1): ("aviso á Joab", "ἀνηγγέλη τῷ Ἰωὰβ"), ("2S", 19, 43): ("diez partes", "Δέκα χεῖρές"),
    ("2S", 20, 25): ("Ira Jaireo", "Εἴρας ὁ Ἰαρεὶν"), ("2S", 23, 1): ("postreras palabras de David", "οἱ λόγοι Δαυεὶδ οἱ ἔσχατοι"),
    ("2S", 24, 13): ("siete años de hambre", "τρία ἔτη λιμὸς"),
    # 1 Reyes (Swete = 3 Reinos; numera 4–6 y 10 a su manera, invierte 20 y 21 y numera 22 como el hebreo: ver _griego_1r)
    ("1R", 4, 17): ("Josaphat", "Ἰωσαφὰτ"), ("1R", 4, 18): ("Ela", "Ἠλὰ"), ("1R", 4, 19): ("Sehón", "Σηὼν"),
    ("1R", 4, 27): ("mantenían", "ἐχορήγουν"), ("1R", 4, 28): ("cebada", "κριθὰς"), ("1R", 4, 29): ("arena", "ἄμμος"),
    ("1R", 4, 32): ("tres mil parábolas", "τρισχιλίας παραβολάς"), ("1R", 5, 1): ("HIRAM", "Χειρὰμ"), ("1R", 5, 18): ("aparejaron", "ἡτοίμασαν"),
    ("1R", 6, 1): ("cuatrocientos ochenta", "τετρακοσιοστῷ"), ("1R", 6, 36): ("atrio", "αὐλὴν"), ("1R", 7, 1): ("trece años", "τρισκαίδεκα"),
    ("1R", 7, 13): ("Hiram", "Χειρὰμ"), ("1R", 10, 26): ("doce mil", "δώδεκα χιλιάδες"), ("1R", 11, 7): ("Chêmos", "Χαμὼς"),
    ("1R", 20, 1): ("Ben-adad", "υἱὸς Ἁδὲρ"), ("1R", 21, 1): ("Naboth", "Ναβουθαὶ"), ("1R", 22, 51): ("durmió Josaphat", "ἐκοιμήθη"),
    ("1R", 22, 53): ("Baal", "Βααλεὶμ"),
}

# Anclas de contenido del hebreo (consonantes): RV -> (palabra en la RV, palabra en el hebreo asignado)
# Versículos RV que el WLC (OSHB) trae pero el Códice de Leningrado no tiene (marca «X» del UXLC, que se comprueba al generar).
_NOTA_FUERA_L = ("Sin texto hebreo: este versículo no está en el Códice de Leningrado. El UXLC (tanach.us, la transcripción del WLC) "
                 "lo marca «X»: «This verse does NOT occur in the Leningrad Codex. Included for continuity of verse numbering». "
                 "El WLC (OSHB) incluye un texto solo para no romper la numeración, sin decir de qué manuscrito sale, y aquí no se muestra "
                 "como si fuera del códice. Jos 21:36-37 (ciudades levíticas de Rubén) sí están en la RV1909 y en la LXX (Swete), comprobado al generar.")
HEBREO_FUERA_DE_L = {("Jos", 21, 36): _NOTA_FUERA_L, ("Jos", 21, 37): _NOTA_FUERA_L}

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
    ("Dt", 6, 4): ("Oye, Israel", "שמע"),         # letra grande ע (seg x-large)
    ("Dt", 12, 32): ("añadirás", "תסף"),         # TM 13:1
    ("Dt", 13, 1): ("profeta", "נביא"),          # TM 13:2
    ("Dt", 22, 30): ("padre", "אביו"),           # TM 23:1
    ("Dt", 23, 1): ("congregación", "בקהל"),     # TM 23:2
    ("Dt", 29, 1): ("Moab", "מואב"),             # TM 28:69
    ("Dt", 29, 29): ("secretas", "הנסתרת"),      # TM 29:28
    ("Dt", 34, 7): ("ciento y veinte", "ועשרים"),
    ("Jos", 5, 15): ("zapatos", "נעלך"),
    ("Jos", 8, 30): ("Ebal", "עיבל"),
    ("Jos", 9, 27): ("leñadores", "חטבי"),
    ("Jos", 10, 13): ("sol", "השמש"),
    ("Jos", 21, 38): ("Gad", "גד"),               # el siguiente a los dos versículos que faltan en el Códice de Leningrado
    ("Jos", 24, 29): ("ciento y diez", "ועשר"),
    ("Jue", 1, 1): ("Josué", "יהושע"),
    ("Jue", 4, 4): ("profetisa", "נביאה"),
    ("Jue", 14, 18): ("dulce", "מתוק"),          # TM 14:18, primera parte
    ("Jue", 14, 19): ("araseis", "חרשתם"),        # TM 14:18, segunda parte
    ("Jue", 14, 20): ("Ascalón", "אשקלון"),       # TM 14:19-20
    ("Jue", 16, 13): ("tela", "המסכת"),
    ("Jue", 18, 30): ("Manasés", "מנשה"),         # con la nun suspendida
    ("Jue", 21, 25): ("rey", "מלך"),
    ("Rut", 1, 16): ("Ruth", "רות"),
    ("Rut", 2, 3): ("Booz", "לבעז"),
    ("Rut", 4, 17): ("Obed", "עובד"),
    ("Rut", 4, 20): ("Salmón", "שלמה"),          # Salmá (שַׂלְמָה) en 4:20 …
    ("Rut", 4, 21): ("Salmón", "ושלמון"),        # … y Salmón (שַׂלְמוֹן) en 4:21: ver SALMA_SALMON
    ("Rut", 4, 22): ("David", "דוד"),
    ("1S", 1, 20): ("Samuel", "שמואל"),
    ("1S", 3, 10): ("Samuel", "שמואל"),
    ("1S", 16, 13): ("ungiólo", "וימשח"),
    ("1S", 17, 4): ("seis codos", "שש"),
    ("1S", 20, 42): ("ciudad", "העיר"),            # TM 20:42 + 21:1
    ("1S", 21, 1): ("Nob", "נבה"),                # TM 21:2
    ("1S", 21, 15): ("locos", "משגעים"),          # TM 21:16
    ("1S", 23, 28): ("Sela-hammah-lecoth", "המחלקות"),
    ("1S", 24, 1): ("Engaddi", "גדי"),            # TM 24:1 (KJV 23:29)
    ("1S", 24, 22): ("juró", "וישבע"),            # TM 24:22-23
    ("1S", 31, 6): ("murió Saúl", "וימת"),
    ("2S", 1, 1): ("Siclag", "בצקלג"),
    ("2S", 7, 12): ("simiente", "זרעך"),
    ("2S", 12, 7): ("Nathán", "נתן"),
    ("2S", 18, 33): ("Absalom", "אבשלום"),     # TM 19:1
    ("2S", 19, 1): ("Joab", "ליואב"),          # TM 19:2
    ("2S", 19, 43): ("diez partes", "עשר"),     # TM 19:44
    ("2S", 20, 25): ("Jaireo", "היארי"),        # TM 20:25-26
    ("2S", 23, 1): ("David", "דוד"),
    ("2S", 24, 13): ("siete años", "שבע"),
    ("1R", 4, 21): ("Filisteos", "פלשתים"),     # TM 5:1
    ("1R", 4, 34): ("sabiduría", "חכמת"),       # TM 5:14
    ("1R", 5, 1): ("HIRAM", "חירם"),            # TM 5:15
    ("1R", 5, 18): ("Hiram", "חירום"),          # TM 5:32
    ("1R", 6, 1): ("ochenta", "בשמונים"),
    ("1R", 18, 34): ("cántaros", "כדים"),
    ("1R", 22, 43): ("Asa", "אסא"),
    ("1R", 22, 44): ("altos", "הבמות"),
    ("1R", 22, 52): ("Ochôzías", "אחזיהו"),
    ("1R", 22, 53): ("Baal", "הבעל"),           # TM 22:53-54
}

# RV -> (Swete, palabra que debe estar en el griego, palabra que debe estar en la RV)
CORRECCIONES_GRIEGO = {
    ("Ex", 40, 14): (("Ex", 40, 12), "χιτῶνας", "túnicas"),
    ("Ex", 40, 15): (("Ex", 40, 13), "ἀλείψεις", "ungirás"),
    ("Dt", 14, 15): (("Dt", 14, 14), "στρουθὸν", "buho"),
}
NOTA_CORRECCION_GRIEGO = {
    ("Dt", 14, 15): ("Corrección propia (inferido por el contenido): el TVTMS une en la LXX el 14:15 al 14:14 («Absent [=Deu.14:14]»), "
                     "pero el 14:14 de Swete («καὶ στρουθὸν καὶ γλαῦκα καὶ λάρον», avestruz, lechuza y gaviota) son las aves de RV 14:15 "
                     "(hebreo בת היענה, תחמס, שחף); el halcón está en Swete 14:16 (ἱέρακα)."),
}
# Tramos RV -> Swete que el TVTMS no recoge (ninguna de sus columnas griegas numera como esta edición): (libro, cap, v1, v2, cap Swete, v1 Swete, nota).
# Jos 8:30-35 (altar del Ebal): la LXX lo pone tras 9:2; el TVTMS lo da como subversículos «9:2.1-6» (Greek*) o en su sitio (Brenton),
# pero Swete lo numera 9:3-8 y corre el resto del capítulo (Swete 9:9-33 = RV 9:3-27). Comprobado con las anclas de 8:30, 8:35, 9:3 y 9:27.
_NOTA_JOS9 = ("Corrección propia (comprobada por el contenido): en la LXX el altar del monte Ebal (RV 8:30-35) va después de 9:2, y Swete lo numera 9:3-8, "
              "así que Swete 9:9-33 = RV 9:3-27. El TVTMS no tiene una columna con esta numeración (da «Jos.9:2.1-6» o el orden de Brenton).")
DESPLAZAMIENTO_GRIEGO = [
    ("Jos", 8, 30, 35, 9, 3, _NOTA_JOS9),
    ("Jos", 9, 2, 2, 9, 2, "Swete 9:2 = RV 9:2; a continuación Swete pone el altar del monte Ebal (RV 8:30-35) como 9:3-8."),
    ("Jos", 9, 3, 27, 9, 9, _NOTA_JOS9),
]

# La RV1909 de eBible parte en dos el 14:18 del TM y de Swete (que numeran como la KJV; el TVTMS no recoge el corte) y reúne sus 14:19-20
# en su 14:20 (ver jueces.py). Aquí: RV 14:18 = primera parte del 14:18 (la pregunta de los de la ciudad), RV 14:19 = segunda parte
# (la respuesta de Sansón), cortando justo antes de las palabras de CORTES; RV 14:20 = TM/Swete 14:19-20. Cada parte se usa una vez.
RV_PARTIDA = {("Jue", 14, 18): (("Jue", 14, 18), 0, "Jue 14:18a"), ("Jue", 14, 19): (("Jue", 14, 18), 1, "Jue 14:18b")}
CORTES = {("Jue", 14, 18): ("ויאמר להם", "καὶ εἶπεν αὐτοῖς Σαμψών")}       # (hebreo en consonantes, griego literal)
# Cada parte NO debe contener la palabra de la otra (se comprueba en hebreo y en griego).
NO_EN_PARTE = {("Jue", 14, 18): (("חרשתם", "ἠροτριάσατε"), ("מתוק", "γλυκύτερον"))}
RV_UNIDA = {("Jue", 14, 20): [("Jue", 14, 19), ("Jue", 14, 20)]}
_NOTA_JUE14 = ("Corrección propia (comprobada por el contenido): la RV1909 (eBible) parte en dos el 14:18 del texto hebreo y de Swete "
               "(14:18 la pregunta de los de la ciudad; 14:19 la respuesta de Sansón, «Si no araseis con mi novilla…») y reúne sus 14:19-20 "
               "(Ascalón y la mujer de Sansón dada a su compañero) en su 14:20. El TVTMS no recoge este corte. El original de RV 14:18 y 14:19 "
               "es el 14:18, cortado justo antes de «{corte}»; el de RV 14:20, los versículos 14:19-20.")


def partir(txt, corte, hebreo):
    """Corta el texto justo antes de «corte» (en hebreo, comparando consonantes palabra a palabra). Devuelve (a, b) o None."""
    if not hebreo:
        return (txt[:txt.index(corte)].strip(), txt[txt.index(corte):].strip()) if txt.count(corte) == 1 else None
    ps, cs = txt.split(), corte.split()
    pos = [i for i in range(len(ps)) if [consonantes(w).strip() for w in ps[i:i + len(cs)]] == cs]
    return (" ".join(ps[:pos[0]]), " ".join(ps[pos[0]:])) if len(pos) == 1 and pos[0] > 0 else None


# RV -> (Swete que el TVTMS le asigna, palabra que NO está en ese griego, palabra que sí está en la RV, motivo)
QUITAR_GRIEGO = {
    ("Dt", 14, 14): (("Dt", 14, 14), "κόρακ", "cuervo",
                     "Corrección propia (inferido por el contenido): la edición de Swete (Códice Vaticano) no tiene «todo cuervo según su especie»; "
                     "su 14:14 son las aves de RV 14:15. Sin equivalente en esta edición."),
}

# ------------------------------------------------------------------ Rut
# Comprobación versículo a versículo (además del recuento): cada nombre debe caer en los mismos versículos en la RV, el hebreo
# (consonantes; basta con que la palabra contenga la forma, para admitir prefijos) y el griego (sin acentos ni mayúsculas).
# El griego no se compara con Booz ni Rut (la LXX añade el sujeto «Βόος»/«Ῥούθ» en varios versículos) ni con Noemí (la RV suple «[Noemi]»).
NOMBRES_RUT = [  # (RV, formas hebreas, forma griega o None)
    ("Elimelech", ("אלימלך",), "μελεχ"), ("Mahalón", ("מחלון",), "μααλων"), ("Chelión", ("כליון",), None),
    ("Orpha", ("ערפה",), "ορφα"), ("Booz", ("בעז",), None), ("Obed", ("עובד", "עבד"), "ωβηδ"), ("Isaí", ("ישי",), "ιεσσα"),
    ("David", ("דוד",), "δαυει"), ("Phares", ("פרץ",), "φαρες"), ("Mara", ("מרא",), None),
]
RATIO_RUT = {"hebreo": (1.15, 2.7), "griego": (0.5, 1.7)}     # letras RV / letras del original, por versículo
# Salmá / Salmón (Rut 4:20-21): dato del texto hebreo (no variante entre testigos). Se comprueba en el WLC (OSHB) y en el UXLC.
SALMA_SALMON = {("Rut", 4, 20): "שלמה", ("Rut", 4, 21): "ושלמון"}
_NOTA_SALMA = ("Dato del texto hebreo (Códice de Leningrado: WLC 4.20 vía OSHB; igual en el UXLC, comprobado al generar): el padre de Booz se escribe "
               "«שַׂלְמָה» (Salmá) en Rut 4:20 («y Naasón engendró a Salmá») y «שַׂלְמוֹן» (Salmón) en Rut 4:21 («y Salmón engendró a Booz»). "
               "No es una variante entre manuscritos: son dos grafías dentro del mismo texto. La RV1909 escribe «Salmón» en los dos versículos "
               "y la LXX de Swete «Σαλμάν» en los dos (comprobado al generar). Que sea la misma persona es lo que da el texto (4:20 lo engendra, "
               "4:21 engendra a Booz); OSHB les da dos lemas Strong distintos (8009 y 8012).")
_NOTA_KQ = ("Ketiv y qere (dato del texto hebreo, Códice de Leningrado: WLC 4.20 vía OSHB; el UXLC marca los mismos, comprobado al generar): "
            "el ketiv es lo escrito en el texto consonántico (el texto hebreo de esta app lo muestra, sin vocales) y el qere, lo que lee la tradición "
            "masorética (nota al margen; aquí no se muestra). Aquí ")
# Variantes de los rollos de Rut: (ref RV, rollo, palabras que deben estar conservadas en el rollo, palabra del TM, tema, traducciones, nota)
VARIANTES_RUT = [
    (("Rut", 1, 2), "4Q104", ("ישבו", "שם"), ("ויהיו", "שם"), "¿«Estuvieron» o «habitaron» allí? (Rut 1:2)",
     "…y llegaron a los campos de Moab y estuvieron allí (traducción propia, literal).",
     "…y llegaron al campo de Moab y habitaron allí (traducción propia, literal).",
     "En 4Q104 (4QRuth-a) el versículo acaba «ו ישבו שם», con las letras conservadas (no reconstruidas) según los datos de Abegg; el TM acaba «ויהיו שם»."),
    (("Rut", 1, 9), "4Q104", ("קולם",), ("קולן",), "«Alzaron su voz»: sufijo femenino o masculino (Rut 1:9)",
     "…y alzaron su voz (de ellas) y lloraron (traducción propia, literal).",
     "…y alzaron su voz (con sufijo masculino, «de ellos») y lloraron (traducción propia, literal).",
     "En 4Q104 (4QRuth-a) la palabra conservada es «קול׳ם» (Abegg separa el sufijo con «׳»), con sufijo masculino plural; el TM tiene «קולן», femenino plural "
     "(Noemí y sus nueras). Es una diferencia gramatical: el sentido no cambia."),
    (("Rut", 3, 15), "2Q17", ("ימד", "שם", "שש"), ("וימד", "שש"), "«Midió seis…» o «midió allí seis…» (Rut 3:15)",
     "…y midió seis (medidas) de cebada (traducción propia, literal).",
     "…y midió allí seis (medidas) de cebada (traducción propia, literal).",
     "En 2Q17 (2QRuth-b) se conservan «ו ימד שם שש שערי[ם]»: tiene «שם» («allí») entre «midió» y «seis», que el TM no tiene."),
]


# ------------------------------------------------------------------ 1 Samuel
# Comprobación versículo a versículo (además del recuento): nombres poco frecuentes en los mismos versículos en la RV y en el hebreo
# (consonantes; la palabra puede llevar hasta dos letras de prefijo) y, para los que la LXX no añade ni quita, en el griego.
NOMBRES_1S_HEBREO = [("Dagón", ("דגון",)), ("Agag", ("אגג",)), ("Goliath", ("גלית",)), ("Siclag", ("צקלג", "ציקלג")), ("Gilboa", ("גלבע",)),
                     ("Abiathar", ("אביתר",)), ("Michâl", ("מיכל",)), ("Achîs", ("אכיש",)), ("Cis", ("קיש",)), ("Abisai", ("אבישי",))]
NOMBRES_1S_GRIEGO = [("Dagón", "δαγων"), ("Doeg", "δωηκ"), ("Abiathar", "αβιαθαρ"), ("Abisai", "αβεισα")]
RATIO_1S = {"hebreo": (0.8, 3.0), "griego": (0.2, 4.0)}     # letras RV / letras del original, por versículo (1 S 2:9 y 14:42 son los extremos griegos)
# Versículos RV sin griego en Swete (comprobado al generar; todos son marca de versículo vacía en la digitalización o «Absent» en el TVTMS).
_SIN_GR_1S = [(13, 1)] + [(17, v) for v in range(12, 32)] + [(17, 41), (17, 50)] + [(17, v) for v in range(55, 59)] +              [(18, v) for v in range(1, 6)] + [(18, 10), (18, 11), (18, 17), (18, 18), (18, 19), (18, 30), (20, 16), (23, 12)]
SIN_GRIEGO_1S = {("1S", c, v) for c, v in _SIN_GR_1S}
NOTA_FORMA_BREVE = (" Forma breve de la LXX en 1 S 17–18: la edición de Swete, que aquí imprime el Códice Vaticano (inferido), no tiene 17:12-31, 17:41, 17:50, "
                    "17:55–18:5, 18:10-11, 18:17-19 ni 18:30 (lista comprobada al generar). El TM y la RV1909 sí los tienen (ver la variante de 1 S 17:12).")
CAPS_4Q51 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 17, 18, 20, 22, 24, 25, 26, 27, 28, 29, 30, 31]   # capítulos con letras conservadas (Abegg)
KQ_UNIDOS_1S = {("1S", 9, 1), ("1S", 20, 2), ("1S", 24, 9)}    # OSHB parte el ketiv en dos palabras y da una qere sin ketiv; el UXLC las empareja
# Diferencias de marca entre OSHB y el UXLC (comprobadas al generar; aquí solo se usan las de OSHB):
# 17:17 el UXLC marca ketiv «הקליא» / qere «הקלי» (nota «y», yatir: letra sobrante) y OSHB no; 19:23 OSHB marca dos (נוית y בנוית) y el UXLC solo el segundo.
KQ_SOLO_UXLC_1S = {("1S", 17, 17)}
KQ_SOLO_OSHB_1S = {("1S", 19, 23): 1}
_NOTA_13_1 = ("Dato del texto hebreo (Códice de Leningrado: WLC 4.20 vía OSHB; igual en el UXLC, comprobado al generar): el versículo dice "
              "«בֶּן־שָׁנָה שָׁאוּל בְּמָלְכוֹ וּשְׁתֵּי שָׁנִים מָלַךְ עַל־יִשְׂרָאֵל», literalmente «hijo de un año era Saúl al reinar, y dos años reinó sobre Israel» "
              "(traducción propia). En la fórmula de edad del hebreo va «בן» + cifra + «שנה», como en 1 S 4:15, «בֶּן־תִּשְׁעִים וּשְׁמֹנֶה שָׁנָה» (Elí, noventa y ocho años); "
              "aquí no hay cifra entre «בן» y «שנה» (comprobado al generar): el texto parece haber perdido un número (inferido; qué número era no se sabe por estos datos). "
              "La LXX de Swete no tiene este versículo (marca vacía, comprobado) y 4QSam-a (4Q51) no conserva el capítulo 13. "
              "La RV1909 lo traduce «Había ya Saúl reinado un año; y reinado que hubo dos años sobre Israel».")

# ------------------------------------------------------------------ 2 Samuel
# Comprobación versículo a versículo (además del recuento): nombres poco frecuentes en los mismos versículos en la RV y en el hebreo
# (consonantes; hasta dos letras de prefijo) y en el griego (palabra que empieza por la forma, sin acentos). Siba, Husai, Ahimaas,
# Barzillai y Amasa cubren 2 S 18–20, donde la numeración hebrea difiere (RV 18:33 = TM 19:1; RV 19:k = TM 19:k+1).
NOMBRES_2S_HEBREO = [("Siba", ("ציבא",)), ("Hanún", ("חנון",)), ("Arauna", ("ארונה", "אורנה", "ארניה", "האורנה")), ("Jonadab", ("יונדב", "יהונדב")),
                     ("Sadoc", ("צדוק",)), ("Ahimaas", ("אחימעץ",)), ("Husai", ("חושי",)), ("Amasa", ("עמשא",)), ("Thamar", ("תמר",)),
                     ("Abisai", ("אבישי", "אבשי")), ("Hadad-ezer", ("הדדעזר",)), ("Barzillai", ("ברזלי",))]
NOMBRES_2S_GRIEGO = [("Hanún", "αννων"), ("Arauna", "ορνα"), ("Hiram", "χειραμ"), ("Barzillai", "βερζελλει"), ("Hadad-ezer", "αδρααζαρ"), ("Siba", "σειβα")]
RATIO_2S = {"hebreo": (0.8, 3.6), "griego": (0.15, 4.3)}     # letras RV / letras del original (extremos: hebreo 2:32 y 2:31; griego 11:22 y 7:26)
# El Códice Vaticano perdió 2 S 2:5-7 y 2:10-13 (hoja 178 rota: Introducción de Swete, cap. V, «2 Regn. ii. 5–7, 10–13»).
VAT_PERDIDO_2S = {("2S", 2, v) for v in (5, 6, 7, 10, 11, 12, 13)}
NOTA_VAT_PERDIDO = (" El Códice Vaticano perdió este versículo (hoja 178 rota: «2 Regn. ii. 5–7, 10–13», Introducción de Swete, cap. V): "
                    "el texto que imprime Swete aquí no es del Vaticano (de qué manuscrito lo toma no se comprueba en esta app).")
NOTA_23_30 = ("La digitalización de Swete trae dentro de su 23:30 la marca «[31]» seguida de «Γαδαβιὴλ υἱὸς τοῦ Ἀραβωθαίου» («Gadabiel, hijo del arabotita»), "
              "que corresponde al principio de RV 23:31 («Abi-albon de Arbath»; inferido por el contenido), y su 23:31 empieza en «Ἀσβὼθ ὁ Βαρδιαμείτης» "
              "(«Asmaveth de Barhum»). Se deja la numeración de la digitalización. En la lista de los valientes (23:24-39) la LXX da otros nombres y otro orden "
              "en varios versículos (p. ej. no tiene a «Helec» en 23:29 ni a «Benaía Pirathonita» en 23:30).")
KQ_UNIDOS_2S = {("2S", 21, 12)}                     # OSHB: ketiv «שם» + «הפלשתים» y qere «שָׁמָּה פְּלִשְׁתִּים» aparte; el UXLC los empareja
KQ_SOLO_UXLC_2S = {("2S", 13, 33), ("2S", 15, 21)}  # el UXLC marca «אם» escrito y no leído; OSHB no (no se añaden)
KQ_SOLO_OSHB_2S = {("2S", 20, 8): 1}                # OSHB marca ketiv «ועלו» / qere «ועליו»; el UXLC escribe «וְעָלָו» sin marca
KQ_DISTINTOS_2S = {("2S", 13, 37): ("עמיחור", "עמיחוד")}   # el UXLC lleva la nota «t» (transcripción dudosa)


# ------------------------------------------------------------------ 1 Reyes
# Hebreo: el TVTMS (columna «Hebrew») da RV 4:21-34 = TM 5:1-14 y RV 5:1-18 = TM 5:15-32 (la RV1909 numera 4–5 como la KJV).
# En 22 la RV1909 numera como el hebreo: parte en dos (43 y 44) el 22:43 de la KJV y reúne en su 22:53 los versículos 22:53-54
# del TM (22:52-53 de la KJV). Las filas del TVTMS para 22:43-53 son de la KJV y aquí se sustituyen (único punto: DIRECTO_1R_22).
# Comprobado por contenido (anclas hebreas y griegas de 22:43, 22:44, 22:52 y 22:53).
DIRECTO_1R_22 = {("1R", 22, v): [("1R", 22, v)] for v in range(43, 53)}
DIRECTO_1R_22[("1R", 22, 53)] = [("1R", 22, 53), ("1R", 22, 54)]
NOTA_1R_22 = ("La RV1909 (eBible) numera 1 R 22:43-53 como el hebreo, no como la KJV: parte en dos (43 y 44) el 22:43 de la KJV y reúne "
              "en su 22:53 los versículos 22:53-54 del TM y de Swete (22:52-53 de la KJV). Correspondencia propia sobre el TVTMS, comprobada por contenido.")
NOMBRES_1R_HEBREO = [("Abisag", ("אבישג",)), ("Adoniram", ("אדנירם",)), ("Naboth", ("נבות",)), ("Ochôzías", ("אחזיהו",)),
                     ("Zimri", ("זמרי",)), ("Hazael", ("חזאל",)), ("Rezón", ("רזון",)), ("Benaía", ("בניהו",)),
                     ("Semei", ("שמעי",)), ("Abiathar", ("אביתר",)), ("Josaphat", ("יהושפט",))]
NOMBRES_1R_GRIEGO = [("Abisag", "αβεισα"), ("Hazael", "αζαηλ"), ("Abiathar", "αβιαθαρ")]
RATIO_1R = {"hebreo": (0.75, 3.6), "griego": (0.2, 7.5)}       # letras RV / letras del original (extremos en el resumen)


# Griego (3 Reinos de Swete). La digitalización de Swete numera 1 R a su manera en 4–6 y 10 (sus «5:14a-b», «6:1a-d», «10:22a-c»
# y «10:26a» son versículos propios: 4:31-33, 6:2-5, 10:23-25 y 10:30), y ninguna columna griega del TVTMS cumple los TEST de esos
# bloques con esta edición (se comprueba al generar). Tabla propia RV -> Swete por contenido, guiada por la columna Greek* del TVTMS;
# en 7, 11:5-8 y 20–21 coincide con la que da el TVTMS (se comprueba). Regla, la de «1 Reyes: decisiones» en datos/LEEME.md:
# los bloques que la LXX añade con letra (2:35a-o, 2:46a-l, 5:14a-b, 6:1a-d, 6:36a, 8:53a, 9:9a, 10:22a-c, 10:26a, 12:24a-z,
# 16:28a-h) no se emparejan con ningún versículo RV aunque repitan su contenido: van en «bloques_sin_paralelo»; lo que la LXX
# solo cambia de orden (4:17-19, 4:27-34, 6, 7, 11:4-8, capítulos 20 y 21) sí se empareja. [] = sin texto griego (SIN_GRIEGO_1R).
def _griego_1r():
    m = {}

    def p(c, v, *sw):
        m[("1R", c, v)] = [("1R",) + x for x in sw]
    p(4, 17, (4, 19)); p(4, 18, (4, 17)); p(4, 19, (4, 18)); p(4, 27, (4, 20)); p(4, 28, (4, 21))
    for v in range(29, 35):
        p(4, v, (4, v - 4))
    p(5, 18, (5, 17))
    # 7: la del TVTMS (columna Greek*), que la digitalización de Swete cumple (se comprueba que coinciden)
    p(7, 1, (7, 38), (7, 50))
    for v in range(2, 13):
        p(7, v, (7, v + 37))
    for v in range(13, 19):
        p(7, v, (7, v - 12))
    p(7, 19, (7, 8)); p(7, 20, (7, 9)); p(7, 21, (7, 7)); p(7, 23, (7, 10)); p(7, 24, (7, 11)); p(7, 25, (7, 13)); p(7, 26, (7, 12))
    for v in range(27, 31):
        p(7, v, (7, v - 13))
    for v in range(32, 38):
        p(7, v, (7, v - 14))
    for v in range(38, 46):
        p(7, v, (7, v - 14))
    p(7, 46, (7, 33)); p(7, 47, (7, 32))
    for v in range(48, 52):
        p(7, v, (7, v - 14))
    p(6, 2, (6, 6)); p(6, 3, (6, 7), (6, 8))
    for v in range(4, 11):
        p(6, v, (6, v + 5))
    p(6, 15, (6, 16)); p(6, 16, (6, 17)); p(6, 17, (6, 18)); p(6, 20, (6, 19), (6, 20))
    for v in range(22, 31):
        p(6, v, (6, v - 1))
    p(6, 31, (6, 30), (6, 31)); p(6, 34, (6, 32)); p(6, 35, (6, 33)); p(6, 36, (6, 34))
    for v in range(23, 27):
        p(10, v, (10, v + 3))
    for v in range(27, 30):
        p(10, v, (10, v + 4))
    p(11, 4, (11, 3), (11, 4)); p(11, 5, (11, 6)); p(11, 6, (11, 8)); p(11, 7, (11, 5)); p(11, 8, (11, 7))
    for v in range(1, 44):
        p(20, v, (21, v))
    for v in range(1, 30):
        p(21, v, (20, v))
    for k, ds in DIRECTO_1R_22.items():
        m[k] = ds
    for k in SIN_GRIEGO_1R:
        m[k] = []
    return m


_B246 = "el bloque que Swete añade tras 2:46 (2:46a-l en la numeración de Brenton; en Swete, tras la marca «[1]» de su 2:46)"
_B235 = "el bloque que Swete añade tras 2:35 (2:35a-o en Brenton; en Swete, tras la marca «[1]» de su 2:35)"
_B1224 = "el bloque que Swete añade tras 12:24 (12:24a-z en Brenton; en Swete, tras la marca «[1]» de su 12:24)"
_SIN_SITIO = "La LXX (edición de Swete) no tiene este versículo en su sitio"
SIN_GRIEGO_1R = {
    ("1R", 3, 1): f"{_SIN_SITIO} (la digitalización trae la marca 3:1 vacía). Una forma de su texto está en dos bloques añadidos: en {_B235}, marca «[3]», y en el que Swete numera 4:31 (5:14a en Brenton). Ver «bloques_sin_paralelo».",
    ("1R", 4, 20): f"{_SIN_SITIO}. Una forma de su texto está en {_B246}, marca «[1]». Ver «bloques_sin_paralelo».",
    ("1R", 4, 21): f"{_SIN_SITIO}. Una forma de su texto está en {_B246}, marca «[11]», y en el versículo que Swete numera 10:30 (10:26a en Brenton). Ver «bloques_sin_paralelo».",
    ("1R", 4, 25): f"{_SIN_SITIO}. Una forma de su texto está en {_B246}, marca «[7]». Ver «bloques_sin_paralelo».",
    ("1R", 4, 26): f"{_SIN_SITIO}. Una forma de su texto está en {_B246}, marca «[9]». Ver «bloques_sin_paralelo».",
    ("1R", 5, 17): f"{_SIN_SITIO}: lo pone tras 6:1, en el versículo que Swete numera 6:2 (6:1a en Brenton). Ver «bloques_sin_paralelo».",
    **{("1R", 6, v): "La LXX (edición de Swete) no tiene 1 R 6:11-14 (la palabra de Jehová a Salomón mientras edificaba la casa)." for v in range(11, 15)},
    ("1R", 6, 18): "La LXX (edición de Swete) no tiene este versículo (el revestimiento de cedro con calabazas y flores).",
    ("1R", 6, 19): "En Swete el contenido de este versículo (el lugar del arca, «δοῦναι ἐκεῖ τὴν κιβωτὸν διαθήκης Κυρίου») va al final de su 6:18, que se muestra con RV 6:17.",
    ("1R", 6, 21): "La LXX (edición de Swete) no tiene este versículo (las cadenas de oro ante el oráculo); su 6:20-21 corresponde a RV 6:20 y 6:22.",
    ("1R", 6, 32): "La LXX (edición de Swete) no tiene este versículo (las puertas de olivo talladas); sus puertas de 6:32-33 son las de RV 6:34-35.",
    ("1R", 6, 33): "La LXX (edición de Swete) no tiene este versículo (los postes de la puerta del templo).",
    ("1R", 6, 37): f"{_SIN_SITIO}: lo pone tras 6:1, en el versículo que Swete numera 6:4 (6:1c en Brenton). Ver «bloques_sin_paralelo».",
    ("1R", 6, 38): f"{_SIN_SITIO}: lo pone tras 6:1, en el versículo que Swete numera 6:5 (6:1d en Brenton). Ver «bloques_sin_paralelo».",
    ("1R", 7, 22): "La LXX (edición de Swete) no tiene este versículo: el TVTMS lo da «Absent» en la columna griega y los 50 versículos de Swete 7 corresponden a otros de la RV.",
    ("1R", 7, 31): "La LXX (edición de Swete) no tiene este versículo: el TVTMS lo da «Absent» en la columna griega y los 50 versículos de Swete 7 corresponden a otros de la RV.",
    ("1R", 8, 12): f"{_SIN_SITIO} (marca vacía en la digitalización). Las palabras de Salomón sobre la casa están, en otra forma, en el bloque que Swete añade tras 8:53 (8:53a en Brenton; en Swete, tras la marca «[1]»), que cita el «libro del cántico». Ver «bloques_sin_paralelo».",
    ("1R", 8, 13): f"{_SIN_SITIO} (marca vacía en la digitalización). Ver la nota de 8:12 y el bloque tras 8:53 en «bloques_sin_paralelo».",
    ("1R", 9, 15): f"{_SIN_SITIO} (marca vacía en la digitalización). Una forma de su texto está en el versículo que Swete numera 10:23 (10:22a en Brenton; el TVTMS lo hace corresponder a «1Ki.10:22.1»). Ver «bloques_sin_paralelo».",
    ("1R", 9, 16): f"{_SIN_SITIO} (marca vacía en la digitalización). Una forma de su texto está en los versículos que Swete numera 4:32-33 (5:14b en Brenton). Ver «bloques_sin_paralelo».",
    **{("1R", 9, v): f"{_SIN_SITIO} (marca vacía en la digitalización). Las ciudades que edificó Salomón están, en otra forma, en el versículo que Swete numera 10:23 (10:22a en Brenton; el TVTMS da «Absent [=1Ki.10:22.1]») y en {_B235}, marca «[9]». Ver «bloques_sin_paralelo»." for v in (17, 18, 19)},
    ("1R", 9, 20): f"{_SIN_SITIO} (marca vacía en la digitalización). Una forma de su texto está en el versículo que Swete numera 10:24 (10:22b en Brenton; el TVTMS lo hace corresponder a «1Ki.10:22.2»). Ver «bloques_sin_paralelo».",
    ("1R", 9, 21): f"{_SIN_SITIO} (marca vacía en la digitalización). Una forma de su texto está en el versículo que Swete numera 10:24 (10:22b en Brenton). Ver «bloques_sin_paralelo».",
    ("1R", 9, 22): f"{_SIN_SITIO} (marca vacía en la digitalización). Una forma de su texto está en el versículo que Swete numera 10:25 (10:22c en Brenton; el TVTMS lo hace corresponder a «1Ki.10:22.3»). Ver «bloques_sin_paralelo».",
    ("1R", 9, 23): f"{_SIN_SITIO} (marca vacía en la digitalización). Los jefes de las obras están, con otra cifra, en {_B235}, marca «[8]». Ver «bloques_sin_paralelo».",
    ("1R", 9, 24): f"{_SIN_SITIO} (marca vacía en la digitalización). Una forma de su texto está al final de Swete 9:9 (9:9a en Brenton) y en {_B235}, marca «[6]». Ver «bloques_sin_paralelo».",
    ("1R", 9, 25): f"{_SIN_SITIO} (marca vacía en la digitalización). Una forma de su texto está en {_B235}, marca «[7]». Ver «bloques_sin_paralelo».",
    ("1R", 11, 3): "En Swete «setecientas princesas y trescientas concubinas» van dentro de su 11:1 (que se muestra con RV 11:1), y lo demás del versículo («sus mujeres torcieron su corazón») en su 11:4, que se muestra con RV 11:4.",
    **{("1R", 11, v): "En Swete el contenido de 11:23-25 (Rezón, aquí «Ἑσρὼμ υἱὸν Ἐλιαδᾶε», que toma Damasco y es adversario de Israel) va dentro de su 11:14, que se muestra con RV 11:14 (el TVTMS da «Absent [=1Ki.11:14…]»)." for v in (23, 24, 25)},
    ("1R", 12, 2): "En Swete el contenido de este versículo (Jeroboam en Egipto oye la noticia) va al final de su 11:43, que se muestra con RV 11:43 (el TVTMS da «Absent [=1Ki.11:43]»).",
    **{("1R", 14, v): f"{_SIN_SITIO} (marca vacía en la digitalización): Swete no tiene 14:1-20 en su sitio. La historia del hijo enfermo de Jeroboam y del profeta Ahías está, en otra forma, en {_B1224}, marcas «[7]» a «[14]». Ver «bloques_sin_paralelo»." for v in range(1, 21)},
}
# Versículos RV cuyo versículo de Swete está vacío en la digitalización (el bucle general les da el motivo); aquí, lo que se añade.
EXTRA_SIN_1R = {
    **{("1R", 22, v): " En Swete, una forma de 22:47-50 está en el bloque que añade tras 16:28 (16:28a-h en Brenton; marcas «[4]» a «[7]»; el TVTMS da «Absent [=1Ki.16:28.4-7]»). Ver «bloques_sin_paralelo»." for v in range(47, 51)},
    ("1R", 11, 39): "", ("1R", 12, 17): "", ("1R", 13, 27): "", ("1R", 15, 6): "", ("1R", 15, 32): "", ("1R", 21, 11): "", ("1R", 21, 12): "",
}
# Bloques de Swete sin paralelo en el TM ni en la RV1909. (verso de Swete, corte o None, versos enteros, ref RV tras la que va, letras de Brenton, nota)
# corte: «[1]» (marcas de subversículo de la digitalización) o la frase griega donde empieza el bloque; None = versículos enteros de Swete.
BLOQUES_1R = [
    ((2, 35), "[1]", None, (2, 35), "2:35a-o",
     "Catorce frases (marcas [1]-[9] y [11]-[15]: la digitalización no tiene «[10]», como Brenton no tiene «2:35j»): la sabiduría de Salomón, la hija de Faraón, "
     "los trabajadores, el mar de bronce, los holocaustos, los jefes de las obras y las ciudades que edificó (en el TM, en 3:1 y en 4–9), y la orden de David sobre Semei (en el TM, 2:8-9)."),
    ((2, 46), "[1]", None, (2, 46), "2:46a-l",
     "Once frases (marcas [1]-[9], [11] y [12]): la sabiduría y la prosperidad de Salomón, su comida diaria, sus príncipes y sus caballos (en el TM, sobre todo en 1 R 4)."),
    (None, None, [(4, 31), (4, 32), (4, 33)], (4, 34), "5:14a-b",
     "Swete los numera 4:31-33: Salomón toma por mujer a la hija de Faraón; Faraón toma Gezer y se la da a su hija; Salomón edifica Gezer (en el TM, 3:1 y 9:16-17)."),
    (None, None, [(6, 2), (6, 3), (6, 4), (6, 5)], (6, 1), "6:1a-d",
     "Swete los numera 6:2-5: las piedras para los cimientos, los canteros de Salomón y de Hiram, y el cuarto y el undécimo año de la obra (en el TM, 5:31-32 —RV 5:17-18— y 6:37-38)."),
    ((6, 34), "καὶ ᾠκοδόμησε καταπέτασμα", None, (6, 36), "6:36a",
     "Final de Swete 6:34: el velo del atrio del pórtico de la casa, sin paralelo en el TM."),
    ((8, 53), "[1]", None, (8, 53), "8:53a",
     "Las palabras de Salomón al terminar la casa («el Señor dio a conocer el sol en el cielo…»), que remiten al «libro del cántico»; en el TM, una forma distinta en 8:12-13."),
    ((9, 9), "Τότε ἀνήγαγεν", None, (9, 9), "9:9a",
     "Final de Swete 9:9: Salomón sube a la hija de Faraón de la ciudad de David a la casa que le edificó (en el TM, 9:24)."),
    (None, None, [(10, 23), (10, 24), (10, 25)], (10, 22), "10:22a-c",
     "Swete los numera 10:23-25: la leva de Salomón, las ciudades que edificó y los pueblos sometidos a tributo (en el TM, 9:15-22)."),
    (None, None, [(10, 30)], (10, 26), "10:26a",
     "Swete lo numera 10:30: Salomón señorea sobre todos los reyes desde el río hasta la tierra de los filisteos y el término de Egipto (en el TM, 4:21 RV = 5:1 TM)."),
    ((12, 24), "[1]", None, (12, 24), "12:24a-z",
     "Otro relato de la subida de Jeroboam (marcas [1]-[9], [11]-[21] y [24]-[26]; Brenton no tiene las letras j, v ni w): su madre Sarisa, su huida a Egipto ante «Susakim», "
     "la enfermedad y muerte de su hijo con el profeta Ahías, el manto en doce trozos de Semeías y la asamblea de Siquem (en el TM, en otra forma, 11:26-12:24 y 14:1-20)."),
    ((16, 28), "[1]", None, (16, 28), "16:28a-h",
     "El reinado de Josafat de Judá (marcas [1]-[8]), con otras cifras que 22:41-50 (el año once de Omri, su madre «Γαβουζά»)."),
]
# Anclas de los bloques: palabra griega que debe estar en el texto del bloque y palabra inglesa en el lugar de Brenton (eng-Brenton_vpl).
ANCLAS_BLOQUES_1R = {"2:35a-o": ("Σεμεεὶ υἱὸς Γηρά", "2:35l", "Semei"), "2:46a-l": ("Θερμαὶ", "2:46d", "Thermæ"),
                     "5:14a-b": ("Γάζερ", "5:14b", "Gazer"), "6:1a-d": ("Χειράμ", "6:1b", "Chiram"), "6:36a": ("καταπέτασμα", "6:36a", "curtain"),
                     "8:53a": ("ᾠδῆς", "8:53a", "song"), "9:9a": ("θυγατέρα Φαραὼ", "9:9a", "Pharao"), "10:22a-c": ("Χετταίου", "10:22b", "Chettite"),
                     "10:26a": ("ἀλλοφύλων", "10:26a", "Philistines"), "12:24a-z": ("Σουσακεὶμ", "12:24c", "Susakim"), "16:28a-h": ("Γαβουζά", "16:28a", "Josaphat")}
KQ_UNIDOS_1R = {("1R", 17, 15)}
KQ_SOLO_UXLC_1R = set()
KQ_SOLO_OSHB_1R = {}
KQ_DISTINTOS_1R = {}
N_KQ_1R = 45


# ------------------------------------------------------------------ 2 Reyes
# Hebreo: la RV1909 numera 11:21 como la KJV (versículo propio); en el TM es 12:1, y el TM 12:2-22 es la RV 12:1-21. Es el único
# bloque del TVTMS en 2 Reyes ($2Ki.11:21--12:21) y se aplica sin correcciones propias (se comprueba por contenido y con el UXLC).
# Griego: la digitalización de Swete (4 Reinos) tiene los 719 versículos con los mismos recuentos por capítulo que la RV1909 (también
# 11:21 y 12:1-21): no numera como el TM ni como Brenton. La columna «Greek» del TVTMS (12:2-22) no cumple su TEST «2Ki.12:22=Last» con
# esta edición y el script sigue la numeración de la KJV, que sí la cumple (comprobado por contenido: anclas de 11:21, 12:1 y 12:21).
NOMBRES_2R_HEBREO = [("Josías", ("יאשיהו",)), ("Jezabel", ("איזבל",)), ("Isaías", ("ישעיהו",)), ("Gedalías", ("גדליהו",)),
                     ("Sedecías", ("צדקיהו",)), ("Jonadab", ("יהונדב",)), ("Joas", ("יהואש", "יואש"))]
NOMBRES_2R_GRIEGO = [("Jezabel", "ιεζαβελ"), ("Gedalías", "γοδολια"), ("Jonadab", "ιωναδαβ"), ("Manasés", "μανασση"),
                     ("Nabucodonosor", "ναβουχοδονοσορ")]
RATIO_2R = {"hebreo": (1.1, 3.0), "griego": (0.35, 3.7)}       # letras RV / letras del original (extremos en el resumen)
NOTA_2R_11_12 = ("La RV1909 numera 2 R 11:21 como la KJV («Era Joas de siete años cuando comenzó á reinar»); en el TM es 12:1 y el TM 12:2-22 "
                 "es la RV 12:1-21 (TVTMS). La digitalización de Swete numera estos versículos como la RV1909, no como el TM ni como Brenton "
                 "(«4 Kingdoms» 12:1-22): la columna «Greek» del TVTMS no cumple su TEST con esta edición y se sigue la numeración de la KJV, "
                 "comprobada por contenido (Swete 11:21 «Υἱὸς ἐτῶν ἐπτὰ Ἰωὰς», 12:1 «ἐν ἔτει ἑβδόμῳ τῷ Εἰοὺ», 12:21 «Ἰεζειχὰρ»).")
NOTA_2R_25_10 = (" Brenton (eBible) sí trae un 25:10 («the force of the Chaldeans pulled down the wall of Jerusalem»): no comprobé en el impreso "
                 "de Swete si le falta el versículo o si es un hueco de la digitalización.")
BLOQUE_2R_118 = ("Cuatro frases (marcas [1]-[4]): Joram hijo de Acab reina sobre Israel en Samaria doce años desde el año dieciocho de Josafat, hace "
                 "lo malo pero quita las estelas de Baal y sigue en los pecados de Jeroboam, y la ira del Señor contra la casa de Acab (en el TM, en "
                 "otra forma, 3:1-3).")
KQ_UNIDOS_2R = {("2R", 6, 25)}
N_KQ_2R = 73


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
    ("Dt", "qfMplfJoYA0", "Resumen del libro de Deuteronomio: un panorama completo animado", "Dt 1:1-Dt 34:12", "inferido"),
    ("Dt", "lq36F3b-S2U", "El tema principal del libro de Deuteronomio • Serie de la Torá • (episodio 7)", "Dt 1:1-Dt 34:12", "libro entero (tema)"),
    ("Jos", "49ggVrdBN_Y", "Resumen del libro de Josué: un panorama completo animado", "Jos 1:1-Jos 24:33", "inferido"),
    ("Jue", "bCwaJz4L2nU", "Resumen del libro de Jueces: un panorama completo animado", "Jue 1:1-Jue 21:25", "inferido"),
    ("Rut", "f984fG4-xlE", "Resumen del libro de Rut: un panorama completo animado", "Rut 1:1-Rut 4:22", "inferido"),
    ("1S", "34biq4ivs5I", "Resumen del libro de 1 Samuel: un panorama completo animado", "1S 1:1-1S 31:13", "inferido"),
    ("2S", "BEvicPpjQBE", "Resumen del libro de 2 Samuel: un panorama completo animado", "2S 1:1-2S 24:25", "inferido"),   # buscador de YouTube, 2026-11-13
    # El video es de 1 y 2 Reyes (buscador de YouTube, 2026-11-13; el canal no tiene uno de cada libro): el mismo id va en los dos libros, con
    # el rango de los dos (inferido), porque la app busca el video por libro. oEmbed se comprueba una sola vez por id.
    ("1R", "8V-TefJJc0g", "Resumen del libro de 1-2 Reyes: un panorama completo animado", "1R 1:1-2R 25:30", "inferido"),
    ("2R", "8V-TefJJc0g", "Resumen del libro de 1-2 Reyes: un panorama completo animado", "1R 1:1-2R 25:30", "inferido"),
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
    heb.update(leer_oshb(obtener("oshb_deu", sin_red), "Dt"))
    heb.update(leer_oshb(obtener("oshb_jos", sin_red), "Jos"))
    heb.update(leer_oshb(obtener("oshb_jue", sin_red), "Jue"))
    heb.update(leer_oshb(obtener("oshb_rut", sin_red), "Rut"))
    heb.update(leer_oshb(obtener("oshb_1s", sin_red), "1S"))
    heb.update(leer_oshb(obtener("oshb_2s", sin_red), "2S"))
    heb.update(leer_oshb(obtener("oshb_1r", sin_red), "1R"))
    heb.update(leer_oshb(obtener("oshb_2r", sin_red), "2R"))
    fuera_l = (leer_uxlc_x(obtener("uxlc_jos", sin_red), "Jos") + leer_uxlc_x(obtener("uxlc_jue", sin_red), "Jue")
               + leer_uxlc_x(obtener("uxlc_rut", sin_red), "Rut") + leer_uxlc_x(obtener("uxlc_1s", sin_red), "1S")
               + leer_uxlc_x(obtener("uxlc_2s", sin_red), "2S") + leer_uxlc_x(obtener("uxlc_1r", sin_red), "1R")
               + leer_uxlc_x(obtener("uxlc_2r", sin_red), "2R"))
    if set(fuera_l) != set(HEBREO_FUERA_DE_L):
        fallo(f"UXLC: versículos marcados «X» (no están en el Códice de Leningrado) {sorted(fuera_l)}, se esperaban {sorted(HEBREO_FUERA_DE_L)}")
    for k in HEBREO_FUERA_DE_L:
        if k not in heb:
            fallo(f"{ref(*k)}: se esperaba en el WLC (OSHB) aunque falte en el Códice de Leningrado")
        heb.pop(k, None)                                 # el WLC lo incluye solo por continuidad de numeración: no se usa
    gr = leer_swete(obtener("swete_vers", sin_red), obtener("swete_pal", sin_red))
    bloques = leer_bloques_tvtms(obtener("tvtms", sin_red))
    t_rv, t_heb, t_gr = Tradicion(texto_rv), Tradicion(heb), Tradicion(gr)

    # ---- hebreo: mapa RV -> TM
    mapa_h, notas_h = construir_mapa(bloques, "Hebrew", t_heb, t_rv, orden_rv, estricto=True)
    aplicar_rv_propia(mapa_h, notas_h)
    for k, ds in RV_UNIDA.items():
        mapa_h[k] = ds
    for k, ds in DIRECTO_1R_22.items():                 # 1 R 22:43-53: la RV1909 numera como el hebreo, no como la KJV
        mapa_h[k] = ds
        notas_h.pop(k, None)
        if ds != [k]:
            notas_h[k] = NOTA_1R_22
    hebreo_notas = {ref(*k): _NOTA_JUE14.format(corte=CORTES[RV_PARTIDA.get(k, (("Jue", 14, 18),))[0]][0]) for k in list(RV_PARTIDA) + list(RV_UNIDA)}
    partes_h = {}                                        # TM partido -> {parte: RV}
    if sorted(vacios_rv) != sorted(k for k, v in RV_PROPIA.items() if not v):
        fallo(f"versículos vacíos de la RV inesperados: {[ref(*k) for k in vacios_rv]}")
    hebreo, sin_hebreo, hebreo_sin_texto = {}, {}, {}
    usados_h = {}
    for k in orden_rv:
        ds = mapa_h.get(k)
        if not texto_rv[k]:                              # versículo vacío en la RV (su texto está en otro): sin hebreo
            if ds:
                fallo(f"versículo vacío {ref(*k)} con hebreo asignado")
            continue
        if k in HEBREO_FUERA_DE_L:
            hebreo_sin_texto[ref(*k)] = HEBREO_FUERA_DE_L[k]
            continue
        if k in RV_PARTIDA:                              # RV que tiene solo una parte de un versículo hebreo (Jue 14:18-19)
            d, parte, r = RV_PARTIDA[k]
            pp = partir(heb.get(d, ""), CORTES[d][0], True)
            if not pp:
                fallo(f"{ref(*k)}: no se pudo cortar el hebreo {ref(*d)} antes de «{CORTES[d][0]}»")
                continue
            if parte in partes_h.setdefault(d, {}):
                fallo(f"hebreo {ref(*d)} (parte {parte}) asignado dos veces")
            partes_h[d][parte] = k
            hebreo[ref(*k)] = {"t": pp[parte], "r": r}
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
    for d in CORTES:
        if sorted(partes_h.get(d, {})) != [0, 1] or d in usados_h:
            fallo(f"hebreo {ref(*d)}: se esperaba repartido en dos partes, una por versículo RV ({partes_h.get(d)})")
        else:
            usados_h[d] = partes_h[d][0]
            pp = partir(heb[d], CORTES[d][0], True)
            for parte, (no_he, _) in enumerate(NO_EN_PARTE[d]):
                if no_he in consonantes(pp[parte]).split():
                    fallo(f"hebreo {ref(*d)}: la parte {parte} no debería tener «{no_he}»")
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
    for lib, c, v1, v2, cg, vg, nota in DESPLAZAMIENTO_GRIEGO:
        for v in range(v1, v2 + 1):
            d = (lib, cg, vg + v - v1)
            if (lib, c, v) not in texto_rv or d not in gr:
                fallo(f"desplazamiento griego {ref(lib, c, v)} -> {ref(*d)}: no existe")
            mapa_g[(lib, c, v)] = [d]
            notas_g[(lib, c, v)] = nota
    for k, ds in RV_UNIDA.items():
        mapa_g[k] = ds
        notas_g[k] = hebreo_notas[ref(*k)].replace("«" + CORTES[("Jue", 14, 18)][0] + "»", "«" + CORTES[("Jue", 14, 18)][1] + "»")
    for k, (d, falta_gr, pal_rv, motivo) in QUITAR_GRIEGO.items():
        if mapa_g.get(k) == [d] and falta_gr not in gr.get(d, "") and pal_rv in texto_rv[k]:
            del mapa_g[k]
            notas_g[k] = motivo
        else:
            fallo(f"griego a quitar {ref(*k)}: ya no aplica o el contenido no coincide")
    for k, (d, pal_gr, pal_rv) in CORRECCIONES_GRIEGO.items():
        if pal_gr in gr.get(d, "") and pal_rv in texto_rv[k] and k not in mapa_g:
            mapa_g[k] = [d]
            notas_g[k] = NOTA_CORRECCION_GRIEGO.get(k) or (
                          "Corrección propia (inferido por el contenido): el TVTMS da «Exo.40:12-15 → Exo.40:12-13», "
                          "incoherente con sus filas 40:12 → 40:10 y 40:13 → 40:11; aquí "
                          f"{ref(*d)} griego («{pal_gr}») corresponde a {ref(*k)} RV («{pal_rv}»).")
        else:
            fallo(f"corrección griega {ref(*k)}: ya no aplica o el contenido no coincide")
    # 1 Reyes: tabla propia RV -> Swete (ver _griego_1r); se guarda lo que da el TVTMS para compararlo
    tvtms_1r = {k: mapa_g.get(k) for k in orden_rv if k[0] == "1R"}
    bloques_sin_col_1r = sorted({mm[1] for k in tvtms_1r for mm in [re.match(r"TVTMS (\$1Ki\.\S+): ninguna columna", notas_g.get(k, ""))] if mm})
    tabla_1r = _griego_1r()
    for k in tvtms_1r:
        ds = tabla_1r.get(k, [k])
        if ds != tvtms_1r[k]:
            notas_g.pop(k, None)
        if ds:
            mapa_g[k] = ds
        else:
            mapa_g.pop(k, None)
            notas_g[k] = SIN_GRIEGO_1R[k]
        if ds == DIRECTO_1R_22.get(k) and ds != [k]:
            notas_g[k] = NOTA_1R_22
    griego, ref_griega, notas_griego, sin_griego = {}, {}, {}, {}
    usos_g, partes_g = {}, {}
    for k in orden_rv:
        ds = mapa_g.get(k)
        if not texto_rv[k]:                              # versículo vacío en la RV: ni griego ni «sin_texto»
            if ds:
                fallo(f"versículo vacío {ref(*k)} con griego asignado")
            continue
        if k in RV_PARTIDA:                              # RV que tiene solo una parte de un versículo de Swete (Jue 14:18-19)
            d, parte, r = RV_PARTIDA[k]
            pp = partir(gr.get(d, ""), CORTES[d][1], False)
            if not pp:
                fallo(f"{ref(*k)}: no se pudo cortar el griego {ref(*d)} antes de «{CORTES[d][1]}»")
                continue
            for i, (_, no_gr) in enumerate(NO_EN_PARTE[d]):
                if no_gr in pp[i]:
                    fallo(f"griego {ref(*d)}: la parte {i} no debería tener «{no_gr}»")
            partes_g.setdefault(d, {})[parte] = k
            griego[ref(*k)], ref_griega[ref(*k)] = pp[parte], r
            notas_griego[ref(*k)] = hebreo_notas[ref(*k)].replace("«" + CORTES[d][0] + "»", "«" + CORTES[d][1] + "»")
            if parte == 0:
                usos_g.setdefault(d, []).append(ref(*k))
            continue
        if not ds or not all(d in gr for d in ds):
            sin_griego[ref(*k)] = notas_g.get(k) or "la edición de Swete no tiene este versículo con esa numeración"
            continue
        if not all(gr[d] for d in ds):                   # la marca de versículo existe en Swete, pero sin palabras
            sin_griego[ref(*k)] = ("La digitalización de Swete (LXX-Swete-1930) tiene " + ", ".join(ref(*d) for d in ds if not gr[d])
                                   + " vacío (marca de versículo sin palabras): sin texto griego para este versículo.")
            continue
        griego[ref(*k)] = " ".join(gr[d] for d in ds)
        if ds != [k]:
            ref_griega[ref(*k)] = ref(*ds[0]) + "".join(", " + (ref(*d) if d[1] != ds[0][1] else str(d[2])) for d in ds[1:])
        if k in notas_g:
            notas_griego[ref(*k)] = notas_g[k]
        if k[0] in ("Jos", "1S") and re.search(r"\[\d\]", griego[ref(*k)]):    # adiciones de la LXX (15:59a, 21:42a-d, 24:33a-b…)
            notas_griego[ref(*k)] = (notas_griego.get(ref(*k), "") + " " + NOTA_ADICION_LXX).strip()
        for d in ds:
            usos_g.setdefault(d, []).append(ref(*k))
    for d in CORTES:
        if sorted(partes_g.get(d, {})) != [0, 1] or len(usos_g.get(d, [])) != 1:
            fallo(f"griego {ref(*d)}: se esperaba repartido en dos partes, una por versículo RV ({partes_g.get(d)}, {usos_g.get(d)})")
    for d, ks in usos_g.items():
        if len(ks) > 1:
            for kk in ks:
                notas_griego[kk] = (notas_griego.get(kk, "") + f" El versículo griego {ref(*d)} se reparte entre {', '.join(ks)} (se repite completo).").strip()
    for k, (p_rv, p_gr) in ANCLAS_GRIEGO.items():
        if p_rv not in texto_rv[k] or p_gr not in griego.get(ref(*k), ""):
            fallo(f"ancla griega {ref(*k)}: se esperaba «{p_rv}» en la RV y «{p_gr}» en el griego")
    griego_sin_asignar = [ref(*d) for d in sorted(gr, key=lambda x: (LIBROS.index(x[0]), x[1], x[2])) if d not in usos_g and gr[d]]

    # ---- rollos
    pal = leer_dss(sin_red)
    testigos = list(CODICES)
    for claves, sigla, llid, per, djd, escritura in ROLLOS:
        vs = set()
        num = claves[0] if len(claves) == 1 else re.match(r"\d+Q\d+", claves[0]).group(0)
        extra = ROLLO_EXTRA.get(num, {})
        for c in claves:
            for kheb, ws in pal.get(c, {}).items():
                if kheb in extra.get("fuera_de_versiculo", ()):
                    continue                             # texto sin versículo en el TM (p. ej. 4Q47 «5:0»): no entra en «contiene»
                if any(cons for _, cons in ws):
                    if kheb not in inv_h:
                        fallo(f"{c}: {ref(*kheb)} no existe en el TM")
                        continue
                    vs.add(inv_h[kheb])
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
                    f"({extra.get('motivo_sin_ficha') or f'la dirección {LL}{num}-1 responde 404 y su buscador no lo devuelve; consultado el 2026-11-11'}): sin período, sigla ni edición oficial comprobados, "
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
        txt, prev = "", ""
        for t, _ in ws:                     # Abegg separa prefijos (ו, ל, ב…) y el sof pasuq
            t = t.strip()
            if not t:
                continue
            # se pega a un prefijo suelto (token de una letra, quizá con «[»), no al final de otra palabra («הנחי[ ל» + «עליון»)
            if t == "׃" or re.sub(r"[\[\]\s]", "", prev) in tuple("ובלכהמש"):
                txt += t
            else:
                txt += (" " if txt else "") + t
            prev = t
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
    l37, cons37 = dss_lectura("4Q37", ("Dt", 32, 8))
    l37 = re.sub(r"\s*ε", "", l37)                   # signo de la transcripción de Abegg, no es letra hebrea
    if not ("בני ישראל" in heb_cons("Dt 32:8") and "אלהים" not in heb_cons("Dt 32:8")):
        fallo("Dt 32:8 hebreo: se esperaba «בני ישראל» sin «אלהים»")
    if not (any("בני" in t for t in cons37) and any("אלוהים" in t for t in cons37)):
        fallo("4Q37 Dt 32:8: «בני» y «אלוהים» deberían estar conservados")
    m328 = re.search(r"κατὰ ἀριθμὸν ἀγγέλων θεοῦ", griego.get("Dt 32:8", ""))
    if not m328:
        fallo("Dt 32:8 griego: falta «κατὰ ἀριθμὸν ἀγγέλων θεοῦ»")
    if "hijos de Israel" not in texto_rv[("Dt", 32, 8)]:
        fallo("RV Dt 32:8 sin «hijos de Israel»")
    variantes.append({
        "ref": "Dt 32:8", "tema": "¿Según el número de los hijos de Israel o de los hijos de Dios?",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["Dt 32:8"]["t"],
             "traduccion_es": "Cuando el Altísimo dio herencia a las naciones, cuando separó a los hijos de Adán, fijó los límites de los pueblos según el número de los hijos de Israel (traducción propia, literal)."},
            {"testigos": ["4Q37"], "texto_original": l37,
             "traduccion_es": "…[según el número de] los hijos de Dios (traducción propia; «אלוהים» puede traducirse «Dios» o «dioses»).",
             "nota": "Transcripción de Abegg: [ ] = texto reconstruido por los editores; # = letra dañada o dudosa. «בני אלוהים» está conservado; casi todo lo anterior es reconstrucción. Se omite el signo «ε» de la transcripción (no es una letra hebrea)."},
            {"testigos": ["vaticano"], "texto_original": m328.group(0) if m328 else "",
             "traduccion_es": "según el número de los ángeles de Dios (traducción propia).",
             "nota": "Texto de la edición de Swete (base: Códice Vaticano)."},
        ],
        "fuente": "Edición oficial de 4QDeut-j (4Q37): Duncan 1995, DJD 14: 70-91, según la Leon Levy Library. Lectura del rollo comprobada en los datos de Abegg (ETCBC/dss); TM en el WLC; LXX en Swete.",
        "url_fuente": LL + "4Q37-1",
        "nota": "Texto: cada lectura se comprueba en su fuente al generar. La RV1909 sigue al TM («hijos de Israel»). Qué significa la diferencia es interpretación y no se incluye.",
    })

    # Jos 8:30-35 (altar del monte Ebal): el TM lo pone tras Hai; 4Q47 (4QJosh-a) tras el paso del Jordán, antes de 5:2; Swete tras 9:2.
    seq47 = []
    for _, fr, _, k in ORDEN_DSS.get("4Q47", []):
        if fr == "f1_2" and (not seq47 or seq47[-1] != k):
            seq47.append(k)
    if seq47[:4] != [("Jos", 8, 34), ("Jos", 8, 35), ("Jos", 5, 0), ("Jos", 5, 2)]:
        fallo(f"4Q47 fragmentos 1-2: se esperaba Jos 8:34, 8:35, «5:0», 5:2 seguidos; hay {seq47[:4]}")
    l835, cons835 = dss_lectura("4Q47", ("Jos", 8, 35))
    l50, cons50 = dss_lectura("4Q47", ("Jos", 5, 0))
    l50 = re.sub(r"\s*ε", "", l50)
    if not any("ירד" in t for t in cons835):
        fallo("4Q47 Jos 8:35: «הירדן» debería estar conservado")
    if not (any("ספר" in t for t in cons50) and any("תורה" in t for t in cons50)):
        fallo("4Q47 «5:0»: «ספר» y «תורה» deberían estar conservados")
    if "עיבל" not in heb_cons("Jos 8:30").split():
        fallo("Jos 8:30 hebreo: falta «עיבל»")
    if ref_griega.get("Jos 8:30") != "Jos 9:3" or "Γαιβάλ" not in griego.get("Jos 8:30", ""):
        fallo("Jos 8:30 griego: se esperaba Swete 9:3 con «Γαιβάλ»")
    variantes.append({
        "ref": "Jos 8:30", "tema": "¿En qué momento edificó Josué el altar del monte Ebal (Jos 8:30-35)?",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["Jos 8:30"]["t"],
             "traduccion_es": "Entonces edificó Josué un altar a YHVH, Dios de Israel, en el monte Ebal (traducción propia, literal).",
             "nota": "En el TM (y en la RV1909) el altar y la lectura de la ley (8:30-35) van después de la toma de Hai (8:1-29) y antes de 9:1."},
            {"testigos": ["4Q47"], "texto_original": l835 + " … " + l50,
             "traduccion_es": ("…no hubo palabra de todo lo que mandó Moisés […] que no leyera Josué delante de todo [Israel al pasar] el Jordán, "
                               "y las mujeres y los niños y el extranjero que andaba entre ellos. … Después que se apartaron(?) […] el libro de la ley; "
                               "después de esto […] los que llevaban el arca […] (traducción propia, aproximada; «נתקו» es lectura dudosa)."),
             "nota": ("Orden comprobado en los datos de Abegg: en los fragmentos 1-2 de 4Q47, las líneas 1-2 tienen Jos 8:34-35; las líneas 2-4, un texto de enlace "
                      "sin versículo en el TM (Abegg lo numera «5:0»), y desde la línea 4 sigue Jos 5:2-7 (la circuncisión en Gilgal). Es decir, aquí la lectura de la ley "
                      "va justo después del paso del Jordán. Transcripción de Abegg: [ ] = texto reconstruido por los editores; # = letra dañada; ? = lectura dudosa; "
                      "se omite el signo «ε». «Israel al pasar» es reconstrucción; «el Jordán» está conservado.")},
            {"testigos": ["vaticano"], "texto_original": griego.get("Jos 8:30", ""),
             "traduccion_es": "Entonces edificó Josué un altar al Señor, Dios de Israel, en el monte Gaibal (traducción propia).",
             "nota": "Texto de la edición de Swete (base: Códice Vaticano), que pone este pasaje después de Jos 9:2 (el pacto de los reyes contra Israel) y lo numera 9:3-8."},
        ],
        "fuente": "Edición oficial de 4QJosh-a (4Q47): Ulrich 1995, DJD 14: 143-152, según la Leon Levy Library. Orden y lectura del rollo comprobados en los datos de Abegg (ETCBC/dss); TM en el WLC; LXX en Swete.",
        "url_fuente": LL + "4Q47-1",
        "nota": "Texto: el orden de cada testigo se comprueba al generar. La RV1909 sigue al TM. Cuál de los tres órdenes es el más antiguo es interpretación y no se incluye.",
    })

    # Jue 18:30: la nun suspendida de מנשה (Manasés); sin ella, משה (Moisés). Se comprueba en el WLC (OSHB) y en el UXLC.
    xml_jue = obtener("oshb_jue", sin_red).read_text(encoding="utf-8")
    v1830 = re.search(r'<verse osisID="Judg\.18\.30".*?</verse>', xml_jue, re.S)
    if not (v1830 and re.search(r'<w [^>]*lemma="4519"[^>]*>[^<]*<seg type="x-suspended">נ', v1830.group(0))):
        fallo("Jue 18:30 OSHB: se esperaba la נ de מנשה marcada «x-suspended»")
    ux_jue = obtener("uxlc_jue", sin_red).read_text(encoding="utf-8")
    c18 = re.search(r'<c n="18">(.*?)</c>', ux_jue, re.S)
    u1830 = re.search(r'<v n="30">(.*?)</v>', c18.group(1), re.S) if c18 else None
    if not (u1830 and re.search(r'<s t="suspended">נ[^<]*</s><x>7</x>', u1830.group(1))
            and re.search(r"<code>7</code>.*?Suspended letter", ux_jue, re.S)):
        fallo("Jue 18:30 UXLC: se esperaba la נ suspendida con la nota «7» (Suspended letter(s))")
    if "מנשה" not in heb_cons("Jue 18:30").split() or "Manasés" not in texto_rv[("Jue", 18, 30)]:
        fallo("Jue 18:30: se esperaba «מנשה» en el hebreo y «Manasés» en la RV")
    m1830 = re.search(r"Ἰωναθὰμ υἱὸς Γηρσὸμ υἱὸς Μανασσή", griego.get("Jue 18:30", ""))
    if not m1830:
        fallo("Jue 18:30 griego: falta «Ἰωναθὰμ υἱὸς Γηρσὸμ υἱὸς Μανασσή»")
    variantes.append({
        "ref": "Jue 18:30", "tema": "¿Hijo de Manasés o de Moisés? La letra suspendida de Jue 18:30",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["Jue 18:30"]["t"],
             "traduccion_es": ("Y se levantaron los hijos de Dan la imagen tallada; y Jonatán, hijo de Guersón, hijo de Manasés, él y sus hijos fueron "
                               "sacerdotes de la tribu de Dan hasta el día del cautiverio de la tierra (traducción propia, literal)."),
             "nota": ("La נ (nun) de מנשה, «Manasés», va escrita en alto, suspendida sobre la línea: el WLC (OSHB) la marca como letra suspendida "
                      "(«x-suspended») y el UXLC (tanach.us) con su nota «7», «Suspended letter(s)» (comprobado al generar). Sin esa letra, las "
                      "consonantes son משה, «Moisés» (cálculo: מנשה sin la נ).")},
            {"testigos": ["vaticano"], "texto_original": m1830.group(0) if m1830 else "",
             "traduccion_es": "Jonatán, hijo de Gersón, hijo de Manasés (traducción propia).",
             "nota": ("Texto de la edición de Swete, que en Jueces imprime el Códice Vaticano (forma «B»). Según Wikipedia («Codex Vaticanus» y "
                      "«Codex Alexandrinus»), que cita la edición de Rahlfs, el Códice Alejandrino (forma «A») lee aquí «Moisés»: fuente externa, "
                      "no está en los datos de esta app y no se comprueba.")},
        ],
        "fuente": "Comparación directa: WLC (OSHB) y UXLC 2.x (tanach.us) para la letra suspendida; Swete (LXX-Swete-1930) para el griego.",
        "url_fuente": "https://tanach.us/Books/Judges.xml",
        "nota": "Texto: la letra y las palabras se comprueban en cada fuente al generar. La RV1909 lee «Manasés». Por qué se escribió suspendida es interpretación y no se incluye.",
    })

    # Jue 6:7-10 (el profeta enviado a Israel): 4Q49 (4QJudg-a) pasa de 6:6 a 6:11 dentro de la línea 5 del fragmento 1.
    lin49, seq49 = {}, []
    for _, fr, ln, k in ORDEN_DSS.get("4Q49", []):
        if fr == "f1" and str(ln).isdigit():
            lin49.setdefault(k, set()).add(int(ln))
            if not seq49 or seq49[-1] != k:
                seq49.append(k)
    if any(("Jue", 6, v) in pal.get("4Q49", {}) for v in range(7, 11)):
        fallo("4Q49: no debería tener Jue 6:7-10")
    k66, k611 = ("Jue", 6, 6), ("Jue", 6, 11)
    def lineas_conservadas(k):                       # líneas de las palabras con alguna letra conservada (mismo orden en ORDEN_DSS y en pal)
        ls = [int(ln) for _, fr, ln, kk in ORDEN_DSS.get("4Q49", []) if kk == k]
        ws = pal.get("4Q49", {}).get(k, [])
        return {l for l, (_, c) in zip(ls, ws) if c} if len(ls) == len(ws) else set()
    if not (k66 in seq49 and seq49[seq49.index(k66) + 1:seq49.index(k66) + 2] == [k611]
            and lineas_conservadas(k66) == {5} and lineas_conservadas(k611) == {6}):
        fallo("4Q49 fragmento 1: se esperaba Jue 6:6 seguido de 6:11, con lo conservado de 6:6 en la línea 5 y lo de 6:11 en la 6: " + repr(lin49))
    l66, cons66 = dss_lectura("4Q49", k66)
    l611, cons611 = dss_lectura("4Q49", k611)
    if not (any("יזעקו" in t for t in cons66) and any("יואש" in t for t in cons611)):
        fallo("4Q49: «יזעקו» (6:6) y «יואש» (6:11) deberían estar conservados")
    if "נביא" not in heb_cons("Jue 6:8").split() or "profeta" not in texto_rv[("Jue", 6, 8)]:
        fallo("Jue 6:8: se esperaba «נביא» en el hebreo y «profeta» en la RV")
    m68 = re.search(r"ἐξαπέστειλεν Κύριος ἄνδρα προφήτην", griego.get("Jue 6:8", ""))
    if not m68:
        fallo("Jue 6:8 griego: falta «ἐξαπέστειλεν Κύριος ἄνδρα προφήτην»")
    variantes.append({
        "ref": "Jue 6:7", "tema": "¿Estaba en Jueces 6 el pasaje del profeta (Jue 6:7-10)?",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["Jue 6:8"]["t"],
             "traduccion_es": ("Y envió YHVH un varón profeta a los hijos de Israel, y les dijo: Así dice YHVH, Dios de Israel: Yo os hice subir de "
                               "Egipto y os saqué de la casa de esclavos (traducción propia, literal; es Jue 6:8)."),
             "nota": "En el TM (y en la RV1909), 6:7-10 —el profeta que reprende a Israel— va entre 6:6 (Israel clama a YHVH) y 6:11 (el ángel en Ofra)."},
            {"testigos": ["4Q49"], "texto_original": l66 + " … " + l611,
             "traduccion_es": ("…y clamaron los hijos de Isr[ael a] YHVH. […] que era de Joás el abiezerita, y G[edeón…] "
                               "(traducción propia, aproximada; es Jue 6:6 seguido de 6:11)."),
             "nota": ("Orden comprobado en los datos de Abegg: en el fragmento 1 de 4Q49, Jue 6:6 ocupa las líneas 4-5 y en la misma línea 5 sigue Jue 6:11 "
                      "(el resto de la línea 5, el principio de 6:11, es reconstrucción de los editores). Lo conservado: el final de 6:6 en la línea 5 («יזעקו», "
                      "«יהוה») y parte de 6:11 en la línea 6 («ליואש האביעזרי»). Jue 6:7-10 no aparece en ningún lugar del rollo; que no quepa en lo que "
                      "falta de la línea 5 es la reconstrucción de la edición (inferido). Transcripción de Abegg: [ ] = texto "
                      "reconstruido por los editores; # = letra dañada; ? = lectura dudosa.")},
            {"testigos": ["vaticano"], "texto_original": m68.group(0) if m68 else "",
             "traduccion_es": "Y envió el Señor un varón profeta (traducción propia; Jue 6:8).",
             "nota": "Texto de la edición de Swete (forma «B», Códice Vaticano), que tiene Jue 6:7-10."},
        ],
        "fuente": "Edición oficial de 4QJudg-a (4Q49): Trebolle Barrera 1995, DJD 14: 161-164, según la Leon Levy Library. Orden y lectura del rollo comprobados en los datos de Abegg (ETCBC/dss); TM en el WLC; LXX en Swete.",
        "url_fuente": LL + "4Q49-1",
        "nota": "Texto: el orden de cada testigo se comprueba al generar. La RV1909 sigue al TM. Si el rollo omitió el pasaje o copia un texto que aún no lo tenía es interpretación y no se incluye.",
    })

    # Jue 16:13-14: la LXX (Swete) tiene una frase más en cada versículo («y seré débil…»; «mientras dormía, tejió…»).
    h1613, h1614 = heb_cons("Jue 16:13").split(), heb_cons("Jue 16:14").split()
    if not (h1613[-1:] == ["המסכת"] and "וחליתי" not in h1613 and h1614[:2] == ["ותתקע", "ביתד"]):
        fallo("Jue 16:13-14 hebreo: se esperaba 16:13 terminado en «המסכת», sin «וחליתי», y 16:14 empezando por «ותתקע ביתד»")
    m1613 = re.search(r"Ἐὰν ὑφάνῃς τὰς ἑπτὰ σειρὰς τῆς κεφαλῆς μου σὺν τῷ διάσματι καὶ ἐνκρούσῃς τῷ πασσάλῳ εἰς τὸν τοῖχον, καὶ ἔσομαι ὡς εἷς τῶν ἀνθρώπων ἀσθενής",
                      griego.get("Jue 16:13", ""))
    m1614 = re.search(r"καὶ ἐγένετο ἐν τῷ κοιμᾶσθαι αὐτὸν καὶ ἔλαβεν Δαλειδὰ τὰς ἑπτὰ σειρὰς τῆς κεφαλῆς αὐτοῦ καὶ ὕφανεν ἐν τῷ διάσματι καὶ ἔπηξεν τῷ πασσάλῳ εἰς τὸν τοῖχον",
                      griego.get("Jue 16:14", ""))
    if not (m1613 and m1614):
        fallo("Jue 16:13-14 griego: faltan las frases más largas de Swete")
    if not (texto_rv[("Jue", 16, 13)].endswith("con la tela.") and texto_rv[("Jue", 16, 14)].startswith("Y ella hincó la estaca")):
        fallo("RV Jue 16:13-14: se esperaba el texto corto (como el TM)")
    variantes.append({
        "ref": "Jue 16:13", "tema": "¿Qué dijo Sansón a Dalila la tercera vez (Jue 16:13-14)?",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["Jue 16:13"]["t"] + " " + hebreo["Jue 16:14"]["t"],
             "traduccion_es": ("…Y él le dijo: Si tejes las siete trenzas de mi cabeza con la urdimbre. Y ella (las) fijó con la estaca, y le dijo: "
                               "¡Los filisteos sobre ti, Sansón! Y él despertó de su sueño y arrancó la estaca del telar y la urdimbre (traducción propia, literal)."),
             "nota": "El TM pasa de la propuesta de Sansón (16:13) a «y ella fijó con la estaca» (16:14), sin decir qué pasaría ni que ella tejiera mientras él dormía."},
            {"testigos": ["vaticano"], "texto_original": (m1613.group(0) + " … " + m1614.group(0)) if (m1613 and m1614) else "",
             "traduccion_es": ("Si tejes las siete trenzas de mi cabeza con la urdimbre y las clavas con la estaca en la pared, seré débil como uno de "
                               "los hombres. … Y sucedió que, mientras él dormía, Dalila tomó las siete trenzas de su cabeza, las tejió con la urdimbre "
                               "y las fijó con la estaca en la pared (traducción propia)."),
             "nota": "Texto de la edición de Swete (forma «B», Códice Vaticano). Las dos frases de más se comprueban al generar."},
        ],
        "fuente": "Comparación directa de las ediciones: WLC (OSHB) y Swete (LXX-Swete-1930).",
        "url_fuente": "https://github.com/eliranwong/LXX-Swete-1930",
        "nota": "Texto (las palabras se comprueban en cada edición). La RV1909 sigue al TM (texto corto). Cuál de los dos textos es el más antiguo es interpretación y no se incluye.",
    })

    # ---- Rut: comprobaciones versículo a versículo, Salmá/Salmón, ketiv/qere y variantes de los rollos
    rut = [k for k in orden_rv if k[0] == "Rut"]
    if any(r.startswith("Rut ") for r in renum_h) or any(r.startswith("Rut ") for r in ref_griega):
        fallo("Rut: no debería haber renumeración hebrea ni griega")
    if sorted(k for k in gr if k[0] == "Rut") != rut or any(k not in heb for k in rut) or len(rut) != 85:
        fallo(f"Rut: se esperaban los mismos 85 versículos en la RV, el WLC y Swete ({len(rut)})")
    lineas_tv = obtener("tvtms", sin_red).read_text(encoding="utf-8").splitlines()
    linea_tv = next((l.split("\t")[2].strip() for l in lineas_tv if l.startswith("Rut\tRuth\t")), "")
    ult_rv = "; ".join(f"{c}:{max(v for _, cc, v in rut if cc == c)}" for c in sorted({k[1] for k in rut}))
    if linea_tv != ult_rv or any("Rut." in l for l in lineas_tv):
        fallo(f"Rut TVTMS: se esperaba la tabla «{ult_rv}» y ningún bloque de Rut; tabla «{linea_tv}»")

    def sin_acentos(t):
        return "".join(ch for ch in unicodedata.normalize("NFD", t) if unicodedata.category(ch) != "Mn").lower()
    for nom, formas_h, forma_g in NOMBRES_RUT:
        en_rv = {k for k in rut if nom in texto_rv[k]}
        en_h = {k for k in rut if any(f in w for w in consonantes(hebreo[ref(*k)]["t"]).split() for f in formas_h)}
        if not en_rv or en_rv != en_h:
            fallo(f"Rut «{nom}»: versículos RV {sorted(en_rv)} ≠ hebreo {sorted(en_h)}")
        if forma_g and en_rv != {k for k in rut if forma_g in sin_acentos(griego.get(ref(*k), ""))}:
            fallo(f"Rut «{nom}»: no cae en los mismos versículos en el griego («{forma_g}»)")
    for k in rut:
        letras = len(re.sub(r"\W", "", texto_rv[k]))
        for idioma, txt in (("hebreo", consonantes(hebreo[ref(*k)]["t"]).replace(" ", "")), ("griego", re.sub(r"\W", "", griego.get(ref(*k), "")))):
            a, b = RATIO_RUT[idioma]
            if not txt or not a <= letras / len(txt) <= b:
                fallo(f"{ref(*k)}: proporción de longitud RV/{idioma} fuera de {a}-{b}")
    # Salmá / Salmón
    ux_rut = obtener("uxlc_rut", sin_red)
    for k, forma in SALMA_SALMON.items():
        otra = "שלמון" if forma == "שלמה" else "שלמה"
        cons_k, ux_k = consonantes(hebreo[ref(*k)]["t"]).split(), uxlc_consonantes(ux_rut, k[1], k[2]).split()
        if forma not in cons_k or forma not in ux_k or any(otra in w for w in cons_k + ux_k) or "Salmón" not in texto_rv[k]:
            fallo(f"{ref(*k)}: se esperaba «{forma}» (no «{otra}») en el WLC y en el UXLC, y «Salmón» en la RV")
        if "σαλμαν" not in sin_acentos(griego.get(ref(*k), "")):
            fallo(f"{ref(*k)} griego: se esperaba «Σαλμάν»")
        hebreo_notas[ref(*k)] = _NOTA_SALMA
    # ketiv / qere (solo lo que marcan los datos; se cotejan OSHB y UXLC)
    kq = leer_kq_oshb(obtener("oshb_rut", sin_red), "Rut")
    kq_ux = leer_kq_uxlc(ux_rut, "Rut")

    def c_(t):
        return consonantes(t).replace(" ", "")
    if sorted(kq) != sorted(kq_ux):
        fallo(f"Rut ketiv/qere: versículos distintos en OSHB {sorted(kq)} y UXLC {sorted(kq_ux)}")
    n_kq = 0
    for k, lista in sorted(kq.items()):
        ks_ux, qs_ux = kq_ux.get(k, ([], []))
        if [c_(x) for x, _ in lista if x] != [c_(x) for x in ks_ux] or [c_(y) for _, y in lista if y] != [c_(y) for y in qs_ux]:
            fallo(f"{ref(*k)} ketiv/qere: OSHB {lista} ≠ UXLC {(ks_ux, qs_ux)}")
        partes = []
        for x, y in lista:
            n_kq += 1
            if x and x not in hebreo[ref(*k)]["t"].replace("־", " ").split():
                fallo(f"{ref(*k)}: el ketiv «{x}» debería estar en el texto mostrado")
            if x and y:
                partes.append(f"se escribe «{x}» y se lee «{y}»")
            elif x:
                partes.append(f"se escribe «{x}» pero no se lee (ketiv sin qere)")
            else:
                partes.append(f"se lee «{y}», que no está escrito (qere sin ketiv; el texto mostrado no lo incluye)")
        nota = _NOTA_KQ + "; ".join(partes) + "."
        if k == ("Rut", 3, 14):
            w2q17 = [t for t, cons in pal.get("2Q17", {}).get(k, []) if cons and "לתי" in t]
            if not (w2q17 and re.sub(r"[^א-ת]", "", re.sub(r"\[.*?\]", "", w2q17[0])) == "מלתיו"):
                fallo(f"2Q17 Rut 3:14: se esperaba «מ[רג]לתי׳ו» conservado ({w2q17})")
            nota += (" El rollo 2Q17 (2QRuth-b) escribe esta palabra «מ[רג]לתיו» (datos de Abegg; «רג» reconstruido por los editores): "
                     "con la י de la forma que se lee (qere), no como el ketiv «מרגלתו».")
        hebreo_notas[ref(*k)] = (hebreo_notas[ref(*k)] + " " + nota) if ref(*k) in hebreo_notas else nota
    if n_kq != 13:
        fallo(f"Rut ketiv/qere: se esperaban 13 (10 con ketiv y qere, 1 ketiv sin qere y 2 qere sin ketiv), hay {n_kq}")
    # variantes de los rollos de Rut
    for k, sc, en_rollo, en_tm, tema, tr_tm, tr_rollo, nota_v in VARIANTES_RUT:
        toks = [(re.sub(r"[^א-ת]", "", t), cons and "[" not in t and "]" not in t) for t, cons in pal.get(sc, {}).get(k, [])]
        ok_rollo = any(all(toks[i + j][0] == w and toks[i + j][1] for j, w in enumerate(en_rollo)) for i in range(len(toks) - len(en_rollo) + 1))
        h = consonantes(hebreo[ref(*k)]["t"]).split()
        ok_tm = any(h[i:i + len(en_tm)] == list(en_tm) for i in range(len(h))) and "".join(en_rollo) not in "".join(h)
        if not (ok_rollo and ok_tm):
            fallo(f"variante {ref(*k)}: se esperaba {en_rollo} conservado en {sc} y {en_tm} en el TM")
        lect, _ = dss_lectura(sc, k)
        llid, djd, sigla = next((r[2], r[4], r[1]) for r in ROLLOS if r[0] == [sc])
        variantes.append({
            "ref": ref(*k), "tema": tema,
            "lecturas": [
                {"testigos": ["leningrado"], "texto_original": hebreo[ref(*k)]["t"], "traduccion_es": tr_tm,
                 "nota": "Texto masorético (WLC). La RV1909 sigue aquí al TM."},
                {"testigos": [sc], "texto_original": lect, "traduccion_es": tr_rollo,
                 "nota": nota_v + " Transcripción de Abegg: [ ] = texto reconstruido por los editores; # = letra dañada; ? = lectura dudosa; ׳ separa el sufijo."},
            ],
            "fuente": f"Edición oficial de {sigla} ({sc}): {djd}, según la Leon Levy Library. Lectura del rollo comprobada en los datos de Abegg (ETCBC/dss); TM en el WLC.",
            "url_fuente": LL + llid,
            "nota": "Texto: las palabras se comprueban al generar (en el rollo, solo letras conservadas, no reconstruidas). Cuál de las dos lecturas es la original es interpretación y no se incluye.",
        })

    # ---- 1 Samuel: versificación, comparación versículo a versículo, griego breve, 13:1, ketiv/qere, rollos y variantes
    s1 = [k for k in orden_rv if k[0] == "1S" and texto_rv[k]]
    if len(s1) != 809 or len([k for k in orden_rv if k[0] == "1S"]) != 810:
        fallo(f"1 S: se esperaban 810 versículos RV (809 con texto, 23:29 vacío); hay {len(s1)} con texto")
    if len([k for k in heb if k[0] == "1S"]) != 811:
        fallo("1 S: se esperaban 811 versículos en el WLC (21:16 y 24:23 hebreos)")
    linea_1s = next((l.split("\t")[2].strip() for l in lineas_tv if l.startswith("1Sa\t1Sam\t")), "")
    todos_1s = [k for k in orden_rv if k[0] == "1S"]
    ult_1s = "; ".join(f"{c}:{max(v for _, cc, v in todos_1s if cc == c)}" for c in sorted({k[1] for k in todos_1s}))
    if linea_1s != ult_1s:
        fallo(f"1 S TVTMS: la tabla de la KJV «{linea_1s}» debería coincidir con los últimos versículos de la RV «{ult_1s}»")
    for nom, formas in NOMBRES_1S_HEBREO:
        en_rv = {k for k in s1 if nom in texto_rv[k]}
        en_h = {k for k in s1 if any(w.endswith(f) and len(w) - len(f) <= 2 for w in consonantes(hebreo[ref(*k)]["t"]).split() for f in formas)}
        if not en_rv or en_rv != en_h:
            fallo(f"1 S «{nom}»: versículos RV {sorted(en_rv)} ≠ hebreo {sorted(en_h)}")
    for nom, forma in NOMBRES_1S_GRIEGO:
        en_rv = {k for k in s1 if nom in texto_rv[k]}
        if not en_rv or en_rv != {k for k in s1 if forma in sin_acentos(griego.get(ref(*k), ""))}:
            fallo(f"1 S «{nom}»: no cae en los mismos versículos en el griego («{forma}»)")

    def largo_orig(k, idioma):
        r = ref(*k)
        if idioma == "hebreo":
            return len(consonantes(hebreo[r]["t"]).replace(" ", "")) if r in hebreo else 0
        return len(re.sub(r"\W", "", griego.get(r, "")))

    def largo_rv(k):
        return len(re.sub(r"\W", "", texto_rv.get(k, "")))
    extremos_1s = {}
    for idioma in ("hebreo", "griego"):
        a, b = RATIO_1S[idioma]
        rs = []
        for k in s1:
            n = largo_orig(k, idioma)
            if not n:
                continue
            x = largo_rv(k) / n
            rs.append((round(x, 2), ref(*k)))
            if not a <= x <= b:
                fallo(f"{ref(*k)}: proporción de longitud RV/{idioma} {x:.2f} fuera de {a}-{b}")
        extremos_1s[idioma] = (min(rs), max(rs))
        # en cada capítulo, el emparejamiento sin desfase compara mejor (longitudes) que con desfase ±1;
        # se mide la desviación del logaritmo de la proporción respecto de su mediana en el libro
        lg = sorted(math.log(x) for x, _ in rs)
        med = lg[len(lg) // 2]
        for c in sorted({k[1] for k in s1}):
            vs = [k for k in s1 if k[1] == c]

            def coste(d):
                tot, n = 0.0, 0
                for k in vs:
                    k2 = (k[0], k[1], k[2] + d)
                    lo = largo_orig(k2, idioma) if texto_rv.get(k2) else 0
                    if lo:
                        tot += abs(math.log(largo_rv(k) / lo) - med)
                        n += 1
                return tot / n if n else 99
            if not (coste(0) < coste(1) and coste(0) < coste(-1)):
                fallo(f"1 S {c} ({idioma}): el emparejamiento con desfase compara mejor que sin desfase ({coste(-1):.3f} {coste(0):.3f} {coste(1):.3f})")
    # griego: lista exacta de lo que Swete no tiene, con su motivo
    sin_gr_1s = {k for k in orden_rv if k[0] == "1S" and ref(*k) in sin_griego}
    if sin_gr_1s != SIN_GRIEGO_1S:
        fallo(f"1 S griego: sin texto {sorted(sin_gr_1s ^ SIN_GRIEGO_1S)} distinto de lo esperado")
    for k in SIN_GRIEGO_1S & sin_gr_1s:
        if k[1] in (17, 18):
            sin_griego[ref(*k)] += NOTA_FORMA_BREVE
    if not griego.get("1S 20:15", "").endswith("καὶ ἐκζητήσαι Κύριος ἐχθροὺς τοῦ Δαυείδ.") or "Requiéralo Jehová" not in texto_rv[("1S", 20, 16)]:
        fallo("1 S 20:15-16 griego: se esperaba que Swete 20:15 acabase en «καὶ ἐκζητήσαι Κύριος ἐχθροὺς τοῦ Δαυείδ»")
    for r, extra in (("1S 20:16", " Swete 20:15 acaba con «καὶ ἐκζητήσαι Κύριος ἐχθροὺς τοῦ Δαυείδ» («y que el Señor lo demande a los enemigos de David»), "
                                   "que corresponde al final de RV 20:16 («Requiéralo Jehová de la mano de los enemigos de David»; inferido por el contenido)."),
                     ("1S 13:1", " Ver la nota del texto hebreo de este versículo."),
                     ("1S 23:12", " Swete 23:11 es más breve que el TM y no tiene la segunda pregunta de David ni su respuesta (inferido por el contenido).")):
        if r in sin_griego:
            sin_griego[r] += extra
    for t in testigos:
        if t["id"] == "vaticano":
            t["contiene"] += comprimir([k for k in s1 if ref(*k) in griego], indice)
    # 13:1: falta la cifra de la edad (dato del texto hebreo)
    ux_1s = obtener("uxlc_1s", sin_red)
    for cons_131 in (consonantes(hebreo["1S 13:1"]["t"]).split(), uxlc_consonantes(ux_1s, 13, 1).split()):
        if cons_131[:3] != ["בן", "שנה", "שאול"]:
            fallo(f"1 S 13:1: se esperaba «בן שנה שאול» al principio ({cons_131[:4]})")
    if "בן תשעים ושמנה שנה" not in consonantes(hebreo["1S 4:15"]["t"]) or "1S 13:1" not in sin_griego or ("1S", 13, 1) in pal.get("4Q51", {}):
        fallo("1 S 13:1: comprobaciones de 4:15, Swete y 4Q51")
    if "Saúl reinado un año" not in texto_rv[("1S", 13, 1)]:
        fallo("RV 1 S 13:1: texto inesperado")
    hebreo_notas["1S 13:1"] = _NOTA_13_1
    # ketiv / qere (solo los que marca OSHB; se cotejan con el UXLC)
    def ketiv_qere(lib, clave_oshb, ruta_ux, unidos_esp, solo_ux, solo_oshb, distintos, n_esp):
        """Escribe en hebreo_notas los ketiv/qere de OSHB del libro, cotejados con el UXLC.
        solo_ux: versículos que solo marca el UXLC (no se añaden); solo_oshb: {versículo: marcas de OSHB que el UXLC no tiene};
        distintos: {versículo: (ketiv de OSHB, ketiv del UXLC)} cuando el UXLC lleva la nota «t» (transcripción dudosa)."""
        kq = leer_kq_oshb(obtener(clave_oshb, sin_red), lib)
        kq_ux = leer_kq_uxlc(ruta_ux, lib)
        unidos = set()
        for k, lista in kq.items():                      # ketiv partido en palabras + qere sin ketiv -> un solo par
            nueva, i = [], 0
            while i < len(lista):
                j = i
                while j < len(lista) and lista[j][0] and lista[j][1] is None:
                    j += 1
                if j > i + 1 and j < len(lista) and lista[j][0] is None and lista[j][1]:
                    nueva.append((" ".join(x for x, _ in lista[i:j]), lista[j][1]))
                    unidos.add(k)
                    i = j + 1
                else:
                    nueva.append(lista[i])
                    i += 1
            kq[k] = nueva
        if unidos != unidos_esp:
            fallo(f"{lib} ketiv/qere: ketiv partidos {sorted(unidos)}, se esperaban {sorted(unidos_esp)}")
        sin_ux = {k for k, n in solo_oshb.items() if n == len(kq.get(k, []))}     # versículos que el UXLC no marca en absoluto
        if set(kq_ux) - set(kq) != set(solo_ux) or set(kq) - set(kq_ux) != sin_ux:
            fallo(f"{lib} ketiv/qere: versículos distintos en OSHB y UXLC {sorted(set(kq) ^ set(kq_ux))}")
        if distintos and "Transcription uncertain. Examine the LC image for other possible readings." not in ruta_ux.read_text(encoding="utf-8"):
            fallo(f"{lib} UXLC: falta la definición de la nota «t»")
        n = 0
        for k, lista in sorted(kq.items()):
            rk = ref(*inv_h[k])                          # versículo RV (la numeración hebrea puede diferir)
            ks_ux, qs_ux = kq_ux.get(k, ([], []))
            a_o, b_o = [c_(x) for x, _ in lista if x], [c_(y) for _, y in lista if y]
            a_u, b_u = [c_(re.sub(r"<x>.*?</x>", "", x)) for x in ks_ux], [c_(y) for y in qs_ux]
            if k in distintos:
                ko, ku = distintos[k]
                if ko not in a_o or ku not in a_u or not any("<x>t</x>" in x for x in ks_ux):
                    fallo(f"{ref(*k)} ketiv: se esperaba «{ko}» en OSHB y «{ku}» con nota «t» en el UXLC")
                a_u = [ko if x == ku else x for x in a_u]
            sobra = solo_oshb.get(k, 0)
            if "".join(a_o[sobra:]) != "".join(a_u) or "".join(b_o[sobra:]) != "".join(b_u):
                fallo(f"{ref(*k)} ketiv/qere: OSHB {lista} ≠ UXLC {(ks_ux, qs_ux)}")
            partes = []
            for x, y in lista:
                n += 1
                if x and not all(c_(w) in consonantes(hebreo[rk]["t"]).split() for w in x.split()):
                    fallo(f"{rk}: el ketiv «{x}» debería estar en el texto mostrado")
                if x and y:
                    partes.append(f"se escribe «{x}» y se lee «{y}»")
                elif x:
                    partes.append(f"se escribe «{x}» pero no se lee (ketiv sin qere)")
                else:
                    partes.append(f"se lee «{y}», que no está escrito (qere sin ketiv; el texto mostrado no lo incluye)")
            nota = _NOTA_KQ.replace("el UXLC marca los mismos", "cotejado con el UXLC") + "; ".join(partes) + "."
            if k in unidos:
                nota += " (OSHB da el ketiv en palabras sueltas y la qere aparte; el UXLC los empareja.)"
            if k in sin_ux:
                ux_txt = uxlc_consonantes(ruta_ux, k[1], k[2]).split()
                if not all(c_(x) in ux_txt for x, _ in lista if x):
                    fallo(f"{ref(*k)}: se esperaba en el UXLC la palabra del ketiv sin marcar")
                nota += (" El UXLC no marca este caso: escribe la palabra con las letras del ketiv y sin ketiv ni qere (comprobado al generar); "
                         "la marca es de OSHB.")
            elif sobra:
                nota += " El UXLC marca solo el último de estos casos; el primero lo marca OSHB."
            if k in distintos:
                nota += (f" OSHB transcribe el ketiv «{distintos[k][0]}»; el UXLC, «{distintos[k][1]}», con su nota «t», «Transcription uncertain. "
                         "Examine the LC image for other possible readings» (transcripción dudosa; comprobado al generar). El texto mostrado sigue a OSHB.")
            if rk != ref(*k):
                nota += f" (Hebreo {k[1]}:{k[2]}.)"
            hebreo_notas[rk] = (hebreo_notas[rk] + " " + nota) if rk in hebreo_notas else nota
        if n != n_esp:
            fallo(f"{lib} ketiv/qere: se esperaban {n_esp} (OSHB, con los ketiv partidos unidos), hay {n}")
        return kq, kq_ux, n
    kq1, kq1_ux, n_kq_1s = ketiv_qere("1S", "oshb_1s", ux_1s, KQ_UNIDOS_1S, KQ_SOLO_UXLC_1S, KQ_SOLO_OSHB_1S, {}, 70)
    if ("1S", 17, 17) in kq1 or ("1S", 17, 17) not in kq1_ux:
        fallo("1 S 17:17: se esperaba ketiv/qere solo en el UXLC")
    # rollos de 1 Samuel
    caps51 = sorted({inv_h[k][1] for k, ws in pal.get("4Q51", {}).items() if k[0] == "1S" and any(c for _, c in ws)})
    if caps51 != CAPS_4Q51:
        fallo(f"4Q51: capítulos de 1 S {caps51}, se esperaban {CAPS_4Q51}")
    for t in testigos:
        if t["id"] == "4Q51":
            t["nota"] += (" En 1 Samuel conserva letras de los capítulos " + ", ".join(map(str, caps51))
                          + " (cálculo sobre los datos de Abegg; no conserva nada de 13, 16, 19, 21 y 23). Es el testigo de las variantes de 1 S 1:24, 2:9, 10:27 y 17:4.")

    def letras_cons(t, cons):                       # letras fuera de [ ] (texto conservado, no reconstruido)
        if not cons:
            return ""
        m0 = re.search(r"[\[\]]", t)
        dentro, out = bool(m0 and m0.group(0) == "]"), []
        for ch in t:
            if ch == "[":
                dentro = True
            elif ch == "]":
                dentro = False
            elif "א" <= ch <= "ת" and not dentro:
                out.append(ch)
        return "".join(out)

    def cons_rollo(sc, k):
        return [letras_cons(t, c) for t, c in pal.get(sc, {}).get(k, [])]
    breves = SIN_GRIEGO_1S - {("1S", 13, 1), ("1S", 20, 16), ("1S", 23, 12)}
    en_rollos = {sc: [ref(*inv_h[k]) for k, ws in sorted(pal.get(sc, {}).items()) if k[0] == "1S" and any(c for _, c in ws) and inv_h[k] in breves]
                 for sc in ("4Q51", "1Q7")}
    if en_rollos != {"4Q51": ["1S 17:41", "1S 18:4", "1S 18:5"], "1Q7": ["1S 18:17", "1S 18:18"]}:
        fallo(f"1 S 17–18: versículos de la forma larga conservados en los rollos {en_rollos}")
    # variantes de 1 Samuel (cada palabra se comprueba en su fuente)
    h = {r: consonantes(hebreo[r]["t"]).split() for r in ("1S 1:24", "1S 2:8", "1S 2:9", "1S 2:10", "1S 10:27", "1S 11:1", "1S 14:41", "1S 17:4", "1S 17:12")}
    c124, c29, c210, c1027, c174 = (cons_rollo("4Q51", ("1S",) + x) for x in ((1, 24), (2, 9), (2, 10), (10, 27), (17, 4)))
    m124 = re.search(r"ἐν μόσχῳ τριετίζοντι καὶ ἄρτοις", griego.get("1S 1:24", ""))
    if not (m124 and {"בקר", "משלש", "לחם"} <= set(c124) and "בפרים" in h["1S 1:24"] and "שלשה" in h["1S 1:24"]
            and "משלש" not in h["1S 1:24"] and "tres becerros" in texto_rv[("1S", 1, 24)]):
        fallo("variante 1 S 1:24: lecturas no comprobadas")
    m28 = re.search(r"διδοὺς εὐχὴν τῷ εὐχομένῳ, καὶ εὐλόγησεν ἔτη δικαίου", griego.get("1S 2:8", ""))
    if not (m28 and {"נתן", "יברך"} <= set(c29) and not {"נתן", "יברך"} & set(h["1S 2:8"] + h["1S 2:9"]) and h["1S 2:9"][:2] == ["רגלי", "חסידו"]
            and griego.get("1S 2:9") == "ὅτι οὐκ ἐν ἰσχύι δυνατὸς ἀνήρ·" and "pies de sus santos" in texto_rv[("1S", 2, 9)]):
        fallo("variante 1 S 2:9: lecturas no comprobadas")
    m210 = re.search(r"μὴ καυχάσθω ὁ φρόνιμος ἐν τῇ φρονήσει αὐτοῦ.*?ἐν μέσῳ τῆς γῆς\.", griego.get("1S 2:10", ""))
    if not (m210 and "יתהלל" not in h["1S 2:10"] and "חכם" not in h["1S 2:10"] and "אל" in c210 and "יתל" in c210):
        fallo("variante 1 S 2:10: lecturas no comprobadas")
    g1027_111 = griego.get("1S 10:27", "") + " " + griego.get("1S 11:1", "")
    if not ({"לחץ", "גד", "ראובן", "חזקה", "כמו", "חדש"} <= set(c1027) and "ראובן" not in h["1S 10:27"] + h["1S 11:1"]
            and h["1S 10:27"][-2:] == ["ויהי", "כמחריש"] and "Ῥουβ" not in g1027_111 and "ὡς μετὰ μῆνα" in griego.get("1S 11:1", "")
            and texto_rv[("1S", 10, 27)].endswith("mas él disimuló.")):
        fallo("variante 1 S 10:27 (Najas): lecturas no comprobadas")
    m174 = re.search(r"ὕψος αὐτοῦ τεσσάρων πήχεων καὶ σπιθαμῆς", griego.get("1S 17:4", ""))
    if not (m174 and "ארבע" in c174 and "זרת" in c174 and h["1S 17:4"][-3:] == ["שש", "אמות", "וזרת"] and "seis codos" in texto_rv[("1S", 17, 4)]):
        fallo("variante 1 S 17:4: lecturas no comprobadas")
    if not ("δὸς δήλους" in griego.get("1S 14:41", "") and "δὸς δὴ ὁσιότητα" in griego.get("1S 14:41", "") and "הבה" in h["1S 14:41"]
            and "תמים" in h["1S 14:41"] and "אורים" not in h["1S 14:41"] and "Da perfección" in texto_rv[("1S", 14, 41)]
            and "או" in cons_rollo("4Q52", ("1S", 14, 41)) and "או" not in h["1S 14:41"] and ("1S", 14, 41) not in pal.get("4Q51", {})):
        fallo("variante 1 S 14:41: lecturas no comprobadas")
    if not ("שמנה" in h["1S 17:12"] and griego.get("1S 17:11", "").endswith("ἐφοβήθησαν σφόδρα.") and griego.get("1S 17:32", "").startswith("Καὶ εἶπεν Δαυεὶδ πρὸς Σαούλ")):
        fallo("variante 1 S 17:12: lecturas no comprobadas")
    NOTA_ABEGG = " Transcripción de Abegg: [ ] = texto reconstruido por los editores; # = letra dañada; ? = lectura dudosa; ׳ separa el sufijo."
    l124, _ = dss_lectura("4Q51", ("1S", 1, 24))
    l29, _ = dss_lectura("4Q51", ("1S", 2, 9))
    l1027, _ = dss_lectura("4Q51", ("1S", 10, 27))
    l111, _ = dss_lectura("4Q51", ("1S", 11, 1))
    l174, _ = dss_lectura("4Q51", ("1S", 17, 4))
    ll51, dj51 = LL + "4Q51-2", next(r[4] for r in ROLLOS if r[0] == ["4Q51"])
    fuente51 = f"Edición oficial de 4QSam-a (4Q51): {dj51}, según la Leon Levy Library. Lectura del rollo comprobada en los datos de Abegg (ETCBC/dss); TM en el WLC; LXX en Swete."
    variantes += [{
        "ref": "1S 1:24", "tema": "¿Tres novillos o un novillo de tres años? (1 S 1:24)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["1S 1:24"]["t"],
             "traduccion_es": "Y lo subió consigo cuando lo destetó, con tres novillos, un efa de harina y un odre de vino, y lo llevó a la casa de YHVH en Silo; y el niño era niño (traducción propia, literal).",
             "nota": "Texto masorético (WLC): «בפרים שלשה», «con tres novillos». La RV1909 sigue al TM («con tres becerros»)."},
            {"testigos": ["4Q51"], "texto_original": l124,
             "traduccion_es": "Y lo subió a Silo, como [sube Elcana a sacrificar a YHVH, con un novillo] de vacuno de tres años, y pan… (traducción propia, aproximada).",
             "nota": "Conservadas (no reconstruidas) según los datos de Abegg: «בקר», «משלש» («de tres años») y «לחם» («pan»); «בפר בן» («con un novillo») es reconstrucción de los editores." + NOTA_ABEGG},
            {"testigos": ["vaticano"], "texto_original": m124.group(0) if m124 else "",
             "traduccion_es": "con un becerro de tres años y panes (traducción propia).",
             "nota": "Texto de la edición de Swete (Códice Vaticano)."},
        ],
        "fuente": fuente51, "url_fuente": ll51,
        "nota": "Texto: las palabras se comprueban al generar. Cuál es la lectura original es interpretación y no se incluye.",
    }, {
        "ref": "1S 2:9", "tema": "El cántico de Ana: «guarda los pies de sus santos» o «da el voto al que hace votos» (1 S 2:8-9)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["1S 2:9"]["t"],
             "traduccion_es": "Él guarda los pies de sus fieles, y los malvados callan en las tinieblas; porque no por la fuerza prevalece el hombre (traducción propia, literal).",
             "nota": "Texto masorético (WLC). La RV1909 sigue al TM. Ni el 2:8 ni el 2:9 del TM tienen «נתן» («da») ni «יברך» («bendice»)."},
            {"testigos": ["4Q51"], "texto_original": l29,
             "traduccion_es": "…y el camino de [sus] fie[les guarda…] da el vo[to] al que hace votos, y bendice los a[ños del justo…] (traducción propia, aproximada).",
             "nota": "Conservadas según los datos de Abegg: «נתן» («da») y «יברך» («y bendice»), con letras de «נדר» y «נודר» («voto», «el que hace votos»); lo que va entre [ ] es reconstrucción de los editores." + NOTA_ABEGG},
            {"testigos": ["vaticano"], "texto_original": (m28.group(0) + " … " + griego.get("1S 2:9", "")) if m28 else "",
             "traduccion_es": "da el voto al que hace votos, y bendijo los años del justo. … Porque no en la fuerza es poderoso el hombre (traducción propia).",
             "nota": "Texto de la edición de Swete: esta frase cierra su 2:8, y su 2:9 solo tiene «ὅτι οὐκ ἐν ἰσχύι δυνατὸς ἀνήρ», el final del 2:9 del TM; la primera mitad del 2:9 del TM («guarda los pies de sus fieles…») no está en Swete (comprobado al generar)."},
        ],
        "fuente": fuente51, "url_fuente": ll51,
        "nota": "Texto: las palabras se comprueban al generar (en el rollo, solo letras conservadas). 4Q51 y Swete coinciden aquí frente al TM. Cuál es la lectura original es interpretación y no se incluye.",
    }, {
        "ref": "1S 2:10", "tema": "El cántico de Ana: «no se gloríe el sabio…» en el griego (1 S 2:10)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["1S 2:10"]["t"],
             "traduccion_es": ("YHVH: quebrantados serán sus adversarios; sobre él tronará desde los cielos. YHVH juzgará los confines de la tierra, y dará fuerza a su rey "
                               "y alzará el cuerno de su ungido (traducción propia, literal)."),
             "nota": "Texto masorético (WLC). La RV1909 sigue al TM."},
            {"testigos": ["vaticano"], "texto_original": m210.group(0) if m210 else "",
             "traduccion_es": ("No se gloríe el prudente en su prudencia, ni se gloríe el poderoso en su poder, ni se gloríe el rico en su riqueza; sino gloríese en esto el que se gloría: "
                               "en entender y conocer al Señor, y en hacer juicio y justicia en medio de la tierra (traducción propia)."),
             "nota": "Texto de la edición de Swete, que lo da tras las marcas «[1]» y «[2]» de la digitalización, dentro del 2:10; el TM no lo tiene (comprobado al generar)."},
        ],
        "fuente": "Comparación directa de las ediciones: WLC (OSHB) y Swete (LXX-Swete-1930); rollo: datos de Abegg (ETCBC/dss).",
        "url_fuente": "https://github.com/eliranwong/LXX-Swete-1930",
        "nota": ("Texto (las palabras se comprueban en cada edición). En 4Q51 (4QSam-a), los datos de Abegg conservan aquí unas pocas letras de una frase que el TM no tiene "
                 "(«א#ל», «י#?ת##[ה]ל[ל]», «…ת», «מש…»: «no se gloríe…», «…juicio»), pero casi todo lo demás de esa frase es reconstrucción de los editores, "
                 "así que no se da como lectura del rollo. Cuál de los dos textos es el más antiguo es interpretación y no se incluye."),
    }, {
        "ref": "1S 10:27", "tema": "Najas y los hijos de Gad y de Rubén: un párrafo antes de 1 S 11:1 en 4QSam-a",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["1S 10:27"]["t"] + " " + hebreo["1S 11:1"]["t"],
             "traduccion_es": ("Y los hijos de Belial dijeron: ¿Cómo nos salvará este? Y lo despreciaron y no le trajeron presente; y él fue como quien calla. "
                               "Y subió Najas el amonita y acampó contra Jabes de Galaad; y dijeron todos los hombres de Jabes a Najas: Haz alianza con nosotros y te serviremos "
                               "(traducción propia, literal)."),
             "nota": "Texto masorético (WLC): de 10:27 pasa a 11:1 sin el párrafo. La RV1909 sigue al TM («mas él disimuló»)."},
            {"testigos": ["4Q51"], "texto_original": l1027 + " " + l111,
             "traduccion_es": ("…y no le trajeron presente. Y Najas, rey de los hijos de Amón, oprimía con dureza a los hijos de Gad y a los hijos de Rubén, y les sacaba a todos el ojo derecho, "
                               "y no dejaba salvador a Israel; y no quedó hombre de los hijos de Israel al otro lado [del Jordán] a quien Najas, [rey] de los hijos de Amón, no sacara el ojo derecho; "
                               "pero siete mil hombres [escaparon de los] hijos de Amón y llegaron a Jabes de Galaad. Y fue como un mes después, y subió Najas el amonita y acampó contra Jabes… "
                               "(traducción propia, aproximada; [ ] = reconstrucción de los editores)."),
             "nota": ("Conservadas según los datos de Abegg, entre otras: «לחץ» («oprimía»), «גד», «ראובן», «חזקה» («dureza»), «כמו חדש» («como un mes»). "
                      "«ויהי כמו חדש» y el principio de 11:1 van entre ^ ^ en la transcripción: corrección antigua escrita sobre la línea (documentación de ETCBC/dss). "
                      "Abegg numera el párrafo dentro de 10:27." + NOTA_ABEGG)},
            {"testigos": ["vaticano"], "texto_original": g1027_111,
             "traduccion_es": ("Y los hijos pestilentes dijeron: ¿Quién nos salvará, este? Y lo deshonraron y no le trajeron presentes. Y sucedió como un mes después, y subió Naas el amonita "
                               "y acampó contra Jabes de Galaad; y dijeron todos los hombres de Jabes a Naas el amonita: Haz alianza con nosotros y te serviremos (traducción propia)."),
             "nota": "Texto de la edición de Swete: no tiene el párrafo, pero su 11:1 empieza «ὡς μετὰ μῆνα» («como un mes después»), como lo escrito sobre la línea en 4Q51, donde el TM dice «ויהי כמחריש» («y fue como quien calla», final de 10:27)."},
        ],
        "fuente": fuente51, "url_fuente": ll51,
        "nota": "Texto: las palabras se comprueban al generar (en el rollo, solo letras conservadas). Si el párrafo se perdió en el TM o se añadió en el rollo es interpretación y no se incluye.",
    }, {
        "ref": "1S 14:41", "tema": "La suerte entre Saúl y Jonatán: el griego más largo (1 S 14:41)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["1S 14:41"]["t"],
             "traduccion_es": "Y dijo Saúl a YHVH, Dios de Israel: Da (lo) perfecto («הבה תמים»). Y fueron tomados Jonatán y Saúl, y el pueblo salió (traducción propia, literal).",
             "nota": "Texto masorético (WLC). La RV1909 sigue al TM («Da perfección»)."},
            {"testigos": ["vaticano"], "texto_original": griego.get("1S 14:41", ""),
             "traduccion_es": ("Y dijo Saúl: Señor, Dios de Israel, ¿por qué no has respondido hoy a tu siervo? ¿Está en mí o en Jonatán mi hijo la culpa? Señor, Dios de Israel, da «manifiestos» (δήλους); "
                               "y si dice esto, da, pues, a tu pueblo Israel, da, pues, «santidad» (ὁσιότητα). Y cae la suerte sobre Jonatán y Saúl, y el pueblo salió (traducción propia)."),
             "nota": "Texto de la edición de Swete (Códice Vaticano): las preguntas de Saúl y las dos peticiones con δήλους y ὁσιότητα no están en el TM (comprobado al generar)."},
        ],
        "fuente": "Comparación directa de las ediciones: WLC (OSHB) y Swete (LXX-Swete-1930).",
        "url_fuente": "https://github.com/eliranwong/LXX-Swete-1930",
        "nota": ("Texto (las palabras se comprueban en cada edición). Que δήλους y ὁσιότητα nombren el Urim y el Tumim (las suertes sagradas) es interpretación (inferido) y no se comprueba aquí; "
                 "en el TM «תמים» («perfecto») tiene las mismas consonantes que «Tumim». 4Q51 no conserva este versículo; de 4Q52 (4QSam-b) los datos de Abegg conservan solo «או» y una «ב» "
                 "(«o en…»), que el TM no tiene y que encajan con la pregunta larga del griego («¿en mí o en Jonatán…?»), pero todo lo demás es reconstrucción de los editores "
                 "y no se da como lectura del rollo. Cuál de los dos textos es el más antiguo es interpretación y no se incluye."),
    }, {
        "ref": "1S 17:4", "tema": "¿Cuánto medía Goliat: seis codos o cuatro? (1 S 17:4)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["1S 17:4"]["t"],
             "traduccion_es": "Y salió un hombre de entre los dos campos, de las filas de los filisteos; Goliat era su nombre, de Gat; su altura, seis codos y un palmo (traducción propia, literal).",
             "cifra": 6, "nota": "Texto masorético (WLC): «שש אמות וזרת». La RV1909 sigue al TM («seis codos y un palmo»)."},
            {"testigos": ["4Q51"], "texto_original": l174,
             "traduccion_es": "…[su altura,] cuatro [co]dos y un palmo (traducción propia).",
             "cifra": 4, "nota": "Conservadas según los datos de Abegg: «ארבע» («cuatro», con la primera letra dañada), «מות» de «אמות» y «זרת» («palmo»)." + NOTA_ABEGG},
            {"testigos": ["vaticano"], "texto_original": m174.group(0) if m174 else "",
             "traduccion_es": "su altura, de cuatro codos y un palmo (traducción propia).",
             "cifra": 4, "nota": "Texto de la edición de Swete (Códice Vaticano)."},
        ],
        "fuente": fuente51, "url_fuente": ll51,
        "nota": "Texto: las cifras se comprueban en cada fuente al generar. Cuál es la original es interpretación y no se incluye.",
    }, {
        "ref": "1S 17:12", "tema": "1 S 17–18: el texto griego es más breve",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["1S 17:12"]["t"],
             "traduccion_es": ("Y David era hijo de aquel hombre efrateo de Belén de Judá, cuyo nombre era Isaí, que tenía ocho hijos; y el hombre en los días de Saúl era viejo, "
                               "entrado en años (traducción propia, literal; es 1 S 17:12, el principio de 17:12-31)."),
             "nota": "El TM (y la RV1909) tienen 17:12-31, 17:41, 17:50, 17:55–18:5, 18:10-11, 18:17-19 y 18:30."},
            {"testigos": ["vaticano"], "texto_original": griego.get("1S 17:11", "") + " … " + griego.get("1S 17:32", ""),
             "traduccion_es": ("Y oyeron Saúl y todo Israel estas palabras del extranjero, y se espantaron y temieron mucho. … Y dijo David a Saúl: No desfallezca el corazón de mi señor por él; "
                               "tu siervo irá y peleará con este extranjero (traducción propia; Swete pasa de 17:11 a 17:32)."),
             "nota": "Edición de Swete (Códice Vaticano): no tiene ninguno de esos versículos (marca de versículo vacía en la digitalización, o «Absent» en el TVTMS para 17:55-58 y 18:30); lista comprobada al generar."},
        ],
        "fuente": "Comparación directa de las ediciones: WLC (OSHB) y Swete (LXX-Swete-1930); rollos: datos de Abegg (ETCBC/dss).",
        "url_fuente": "https://github.com/eliranwong/LXX-Swete-1930",
        "nota": ("Texto (cálculo sobre las ediciones). En los datos de Abegg, 4Q51 (4QSam-a) conserva letras de 17:41, 18:4 y 18:5, y 1Q7 (1QSam) de 18:17 y 18:18, "
                 "versículos que Swete no tiene (comprobado al generar; son pocas letras). Por qué el griego es más breve es interpretación y no se incluye."),
    }]

    # ---- 2 Samuel: versificación, comparación versículo a versículo, ketiv/qere, Vaticano, rollos y variantes
    s2 = [k for k in orden_rv if k[0] == "2S" and texto_rv[k]]
    if len(s2) != 694 or len([k for k in orden_rv if k[0] == "2S"]) != 695:
        fallo(f"2 S: se esperaban 695 versículos RV (694 con texto, 20:26 vacío); hay {len(s2)} con texto")
    if len([k for k in heb if k[0] == "2S"]) != 695 or ("2S", 19, 44) not in heb or ("2S", 18, 33) in heb:
        fallo("2 S: se esperaban 695 versículos en el WLC, con 18:1-32 y 19:1-44")
    if len([k for k in gr if k[0] == "2S"]) != 695 or ("2S", 19, 44) in gr or ("2S", 18, 33) not in gr:
        fallo("2 S: se esperaban 695 versículos en Swete, con 18:1-33 y 19:1-43 (como la KJV)")
    linea_2s = next((l.split("\t")[2].strip() for l in lineas_tv if l.startswith("2Sa\t2Sam\t")), "")
    todos_2s = [k for k in orden_rv if k[0] == "2S"]
    ult_2s = "; ".join(f"{c}:{max(v for _, cc, v in todos_2s if cc == c)}" for c in sorted({k[1] for k in todos_2s}))
    if linea_2s != ult_2s:
        fallo(f"2 S TVTMS: la tabla de la KJV «{linea_2s}» debería coincidir con los últimos versículos de la RV «{ult_2s}»")
    for nom, formas in NOMBRES_2S_HEBREO:
        en_rv = {k for k in s2 if nom in texto_rv[k]}
        en_h = {k for k in s2 if any(w.endswith(f) and len(w) - len(f) <= 2 for w in consonantes(hebreo[ref(*k)]["t"]).split() for f in formas)}
        if not en_rv or en_rv != en_h:
            fallo(f"2 S «{nom}»: versículos RV {sorted(en_rv)} ≠ hebreo {sorted(en_h)}")
    for nom, forma in NOMBRES_2S_GRIEGO:
        en_rv = {k for k in s2 if nom in texto_rv[k]}
        if not en_rv or en_rv != {k for k in s2 if any(w.startswith(forma) for w in re.findall(r"\w+", sin_acentos(griego.get(ref(*k), ""))))}:
            fallo(f"2 S «{nom}»: no cae en los mismos versículos en el griego («{forma}»)")
    extremos_2s = {}
    for idioma in ("hebreo", "griego"):
        a, b = RATIO_2S[idioma]
        rs = []
        for k in s2:
            n = largo_orig(k, idioma)
            if not n:
                fallo(f"{ref(*k)}: sin texto {idioma}")
                continue
            x = largo_rv(k) / n
            rs.append((round(x, 2), ref(*k)))
            if not a <= x <= b:
                fallo(f"{ref(*k)}: proporción de longitud RV/{idioma} {x:.2f} fuera de {a}-{b}")
        extremos_2s[idioma] = (min(rs), max(rs))
        lg = sorted(math.log(x) for x, _ in rs)
        med = lg[len(lg) // 2]
        for c in sorted({k[1] for k in s2}):
            vs = [k for k in s2 if k[1] == c]

            def coste2(d):
                tot, n = 0.0, 0
                for k in vs:
                    k2 = (k[0], k[1], k[2] + d)
                    lo = largo_orig(k2, idioma) if texto_rv.get(k2) else 0
                    if lo:
                        tot += abs(math.log(largo_rv(k) / lo) - med)
                        n += 1
                return tot / n if n else 99
            if not (coste2(0) < coste2(1) and coste2(0) < coste2(-1)):
                fallo(f"2 S {c} ({idioma}): el emparejamiento con desfase compara mejor que sin desfase ({coste2(-1):.3f} {coste2(0):.3f} {coste2(1):.3f})")
    if [r for r in sin_griego if r.startswith("2S ")]:
        fallo(f"2 S griego: versículos sin texto {[r for r in sin_griego if r.startswith('2S ')]}")
    # Swete 23:30-31: la marca «[31]» de la digitalización cae dentro de su 23:30
    if not (griego.get("2S 23:30", "").endswith("[31] Γαδαβιὴλ υἱὸς τοῦ Ἀραβωθαίου.") and griego.get("2S 23:31", "").startswith("Ἀσβὼθ ὁ Βαρδιαμείτης")
            and texto_rv[("2S", 23, 31)].startswith("Abi-albon de Arbath, Asmaveth") and "Helec" in texto_rv[("2S", 23, 29)]
            and "Benaía Pirathonita" in texto_rv[("2S", 23, 30)] and not re.search(r"\[\d+\]", " ".join(griego.get(ref(*k), "") for k in s2 if k != ("2S", 23, 30)))):
        fallo("2 S 23:30-31 griego: se esperaba la marca «[31]» solo dentro de Swete 23:30")
    for r in ("2S 23:30", "2S 23:31"):
        notas_griego[r] = (notas_griego.get(r, "") + " " + NOTA_23_30).strip()
    # Códice Vaticano: perdió 2 S 2:5-7 y 2:10-13
    for k in sorted(VAT_PERDIDO_2S):
        if ref(*k) not in griego:
            fallo(f"{ref(*k)}: se esperaba texto en Swete")
        notas_griego[ref(*k)] = (notas_griego.get(ref(*k), "") + NOTA_VAT_PERDIDO).strip()
    for t in testigos:
        if t["id"] == "vaticano":
            t["contiene"] += comprimir([k for k in s2 if ref(*k) in griego and k not in VAT_PERDIDO_2S], indice)
    # ketiv / qere
    ux_2s = obtener("uxlc_2s", sin_red)
    kq2, kq2_ux, n_kq_2s = ketiv_qere("2S", "oshb_2s", ux_2s, KQ_UNIDOS_2S, KQ_SOLO_UXLC_2S, KQ_SOLO_OSHB_2S, KQ_DISTINTOS_2S, 89)
    for k in KQ_SOLO_UXLC_2S:
        if kq2_ux[k] != (["אִם־"], []) or "אם" not in consonantes(hebreo[ref(*inv_h[k])]["t"]).split():
            fallo(f"{ref(*k)}: se esperaba en el UXLC solo el ketiv «אם» (escrito y no leído) y «אם» en el texto de OSHB")
    # rollos de 2 Samuel (todos los de los datos de Abegg con texto de 2 S salvo 11Q5, que es un rollo de Salmos)
    con_2s = sorted(sc for sc, d in pal.items() if any(k[0] == "2S" and any(c for _, c in ws) for k, ws in d.items()))
    if con_2s != ["11Q5", "1Q7", "4Q51", "4Q53"]:
        fallo(f"2 S: rollos con texto en los datos de Abegg {con_2s}")
    if sorted(k for k in pal.get("11Q5", {}) if k[0] == "2S") != [("2S", 23, 7)]:
        fallo("11Q5: se esperaba solo 2 S 23:7")
    caps51_2s = sorted({inv_h[k][1] for k, ws in pal.get("4Q51", {}).items() if k[0] == "2S" and any(c for _, c in ws)})
    if caps51_2s != list(range(1, 25)):
        fallo(f"4Q51: capítulos de 2 S {caps51_2s}")
    # variantes de 2 Samuel (cada palabra se comprueba en su fuente; en los rollos, solo letras fuera de [ ])
    h2 = {r: consonantes(hebreo[r]["t"]).split() for r in ("2S 5:6", "2S 5:8", "2S 6:2", "2S 8:4", "2S 11:3", "2S 13:21", "2S 13:27", "2S 23:8", "2S 24:13", "2S 24:16")}
    cr = {x: cons_rollo("4Q51", ("2S",) + x) for x in ((5, 6), (5, 8), (6, 2), (8, 4), (11, 3), (13, 21), (13, 27), (24, 16))}
    g2 = {r: griego.get(r, "") for r in h2}
    m2413 = re.search(r"εἰ ἔλθῃ σοι τρία ἔτη λιμὸς ἐν τῇ γῇ σου", g2["2S 24:13"])
    if not (m2413 and "שבע שנים רעב" in " ".join(h2["2S 24:13"]) and "siete años de hambre" in texto_rv[("2S", 24, 13)] and ("2S", 24, 13) not in pal.get("4Q51", {})):
        fallo("variante 2 S 24:13: lecturas no comprobadas")
    m84 = re.search(r"χίλια ἅρματα καὶ ἑπτὰ χιλιάδας ἱππέων", g2["2S 8:4"])
    i84 = cr[(8, 4)].index("אלף") if "אלף" in cr[(8, 4)] else -1
    if not (m84 and " ".join(h2["2S 8:4"][3:7]) == "אלף ושבע מאות פרשים" and i84 >= 0 and cr[(8, 4)][i84 + 1] == "ר"
            and "mil y setecientos de á caballo" in texto_rv[("2S", 8, 4)]):
        fallo("variante 2 S 8:4: lecturas no comprobadas")
    m1321 = re.search(r"καὶ οὐκ ἐλύπησεν τὸ πνεῦμα Ἀμνὼν τοῦ υἱοῦ αὐτοῦ, ὅτι ἠγάπα αὐτόν, ὅτι πρωτότοκος αὐτοῦ ἦν\.", g2["2S 13:21"])
    if not (m1321 and {"כי", "בכור"} <= set(cr[(13, 21)]) and not {"בכור", "אמנון", "עצב"} & set(h2["2S 13:21"])
            and texto_rv[("2S", 13, 21)].endswith("fué muy enojado.")):
        fallo("variante 2 S 13:21: lecturas no comprobadas")
    m1327 = re.search(r"καὶ ἐποίησεν Ἀβεσσαλὼμ πότον κατὰ τὸν πότον τοῦ βασιλέως\.", g2["2S 13:27"])
    if not (m1327 and "משתה" not in h2["2S 13:27"] and "משתה" not in cr[(13, 27)]
            and any("משתה" in t for t, _ in pal["4Q51"][("2S", 13, 27)]) and texto_rv[("2S", 13, 27)].endswith("todos los hijos del rey.")):
        fallo("variante 2 S 13:27: lecturas no comprobadas")
    if not ({"ושא", "כלי", "יואב"} <= set(cr[(11, 3)]) and not {"כלי", "יואב"} & set(h2["2S 11:3"]) and h2["2S 11:3"][-2:] == ["אוריה", "החתי"]
            and "Ἰωάβ" not in g2["2S 11:3"] and texto_rv[("2S", 11, 3)].endswith("mujer de Uría Hetheo.")):
        fallo("variante 2 S 11:3: lecturas no comprobadas")
    if not ({"עומד", "שלופה", "שקים", "ארץ"} <= set(cr[(24, 16)]) and not {"עומד", "שלופה", "שקים"} & set(h2["2S 24:16"])
            and "ῥομφαί" not in g2["2S 24:16"] and "σάκκ" not in g2["2S 24:16"] and "era de Arauna Jebuseo." in texto_rv[("2S", 24, 16)]):
        fallo("variante 2 S 24:16: lecturas no comprobadas")
    m62 = re.search(r"ἀπὸ τῶν ἀρχόντων Ἰούδα ἐν ἀναβάσει", g2["2S 6:2"])
    if not (m62 and {"בעלה", "היא", "קרי"} <= set(cr[(6, 2)]) and "מבעלי" in h2["2S 6:2"] and not {"בעלה", "קרית"} & set(h2["2S 6:2"])
            and "de Baal de Judá" in texto_rv[("2S", 6, 2)]):
        fallo("variante 2 S 6:2: lecturas no comprobadas")
    i56 = cr[(5, 6)].index("כי") if "כי" in cr[(5, 6)] else -1
    m56 = re.search(r"ὅτι ἀντέστησαν οἱ τυφλοὶ καὶ οἱ χωλοὶ", g2["2S 5:6"])
    if not (m56 and i56 >= 0 and cr[(5, 6)][i56 + 1] == "הסית" and "כי אם הסירך" in " ".join(h2["2S 5:6"]) and "הסית" not in " ".join(h2["2S 5:6"])
            and "si no echares los ciegos y los cojos" in texto_rv[("2S", 5, 6)]):
        fallo("variante 2 S 5:6: lecturas no comprobadas")
    m58 = re.search(r"διὰ τοῦτο ἐροῦσιν Τυφλοὶ καὶ χωλοὶ οὐκ εἰσελεύσονται εἰς οἶκον Κυρίου\.", g2["2S 5:8"])
    if not (m58 and h2["2S 5:8"][-2:] == ["אל", "הבית"] and "יהוה" not in h2["2S 5:8"]
            and "הבית" not in cr[(5, 8)] and texto_rv[("2S", 5, 8)].endswith("no entrará en casa.")):
        fallo("variante 2 S 5:8: lecturas no comprobadas")
    m238a = re.search(r"Ἰεβόσθε ὁ Χαναναῖος", g2["2S 23:8"])
    m238b = re.search(r"οὗτος ἐσπάσατο τὴν ῥομφαίαν αὐτοῦ ἐπὶ ὀκτακοσίους στρατιώτας εἰς ἅπαξ", g2["2S 23:8"])
    if not (m238a and m238b and "ישב בשבת תחכמני" in " ".join(h2["2S 23:8"]) and {"עדינו", "העצנו", "שמנה", "מאות"} <= set(h2["2S 23:8"])
            and "חרב" not in " ".join(h2["2S 23:8"]) and "que se sentaba en cátedra" in texto_rv[("2S", 23, 8)] and "Adino el Eznita" in texto_rv[("2S", 23, 8)]
            and ("2S", 23, 8) not in pal.get("4Q51", {}) and ("2S", 23, 8) not in pal.get("1Q7", {})):
        fallo("variante 2 S 23:8: lecturas no comprobadas")
    l2 = {x: dss_lectura("4Q51", ("2S",) + x)[0] for x in ((5, 6), (6, 2), (11, 3), (13, 21), (24, 16))}
    variantes += [{
        "ref": "2S 5:6", "tema": "Los ciegos y los cojos: «a menos que los quites» o «porque se opusieron» (2 S 5:6)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["2S 5:6"]["t"],
             "traduccion_es": ("Y fue el rey con sus hombres a Jerusalén, al jebuseo que habitaba la tierra; y dijo a David: No entrarás aquí, a menos que quites a los ciegos y a los cojos "
                               "(o: «sino que te rechazarán los ciegos y los cojos»), diciendo: No entrará David aquí (traducción propia, literal; «כי אם הסירך» admite las dos lecturas)."),
             "nota": "Texto masorético (WLC): «כי אם הסירך», «a menos que quites / sino que te quitarán». La RV1909 sigue al TM («si no echares los ciegos y los cojos»)."},
            {"testigos": ["4Q51"], "texto_original": l2[(5, 6)],
             "traduccion_es": "…no entrarás aquí, porque [te] incita[ron] los ciegos [y los cojos, diciendo: No entrará] David aquí (traducción propia, aproximada).",
             "nota": "Conservadas según los datos de Abegg: «כי» seguido de «הסית» («porque incitó/incitaron»), sin «אם», y letras de «העורים» («los ciegos»); la terminación de «הסית[וך]» es reconstrucción de los editores." + NOTA_ABEGG},
            {"testigos": ["vaticano"], "texto_original": m56.group(0) if m56 else "",
             "traduccion_es": "porque se opusieron los ciegos y los cojos (traducción propia).",
             "nota": "Texto de la edición de Swete (Códice Vaticano): «ὅτι» («porque») y un verbo, «ἀντέστησαν» («se opusieron»), donde el TM tiene «כי אם הסירך»."},
        ],
        "fuente": fuente51, "url_fuente": ll51,
        "nota": "Texto: las palabras se comprueban al generar (en el rollo, solo letras conservadas). 4Q51 y Swete coinciden en «porque…» frente al «a menos que…» del TM. Cuál es la lectura original es interpretación y no se incluye.",
    }, {
        "ref": "2S 5:8", "tema": "«No entrará en la casa» o «en la casa del Señor» (2 S 5:8)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["2S 5:8"]["t"],
             "traduccion_es": ("Y dijo David aquel día: Todo el que hiera al jebuseo y llegue al canal… a los cojos y a los ciegos, aborrecidos del alma de David. "
                               "Por eso dicen: Ciego y cojo no entrará en la casa (traducción propia, literal)."),
             "nota": "Texto masorético (WLC): acaba «אל הבית», «en la casa». La RV1909 sigue al TM («no entrará en casa»)."},
            {"testigos": ["vaticano"], "texto_original": m58.group(0) if m58 else "",
             "traduccion_es": "Por eso dirán: Ciegos y cojos no entrarán en la casa del Señor (traducción propia).",
             "nota": "Texto de la edición de Swete (Códice Vaticano): «εἰς οἶκον Κυρίου», «en la casa del Señor» (comprobado al generar)."},
        ],
        "fuente": "Comparación directa de las ediciones: WLC (OSHB) y Swete (LXX-Swete-1930); rollo: datos de Abegg (ETCBC/dss).",
        "url_fuente": "https://github.com/eliranwong/LXX-Swete-1930",
        "nota": ("Texto (las palabras se comprueban en cada edición). En 4Q51 (4QSam-a) se conservan «כן יאמרו עור ופסח לוא» («por eso dicen: ciego y cojo no…»), "
                 "pero el final («יבוא אל הבית») es reconstrucción de los editores: el rollo no decide aquí. Cuál es la lectura original es interpretación y no se incluye."),
    }, {
        "ref": "2S 6:2", "tema": "¿«De Baalé de Judá» o «a Baalá, que es Quiriat-jearim»? (2 S 6:2)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["2S 6:2"]["t"],
             "traduccion_es": "Y se levantó y fue David, y todo el pueblo que estaba con él, desde Baalé de Judá, para subir de allí el arca de Dios… (traducción propia, literal; «מבעלי יהודה»).",
             "nota": "Texto masorético (WLC). La RV1909 sigue al TM («de Baal de Judá»)."},
            {"testigos": ["4Q51"], "texto_original": l2[(6, 2)],
             "traduccion_es": "…[y todo el pueblo que] con él [estaba] a Baalá, que es Quiriat-[jearim, la] de Judá, para subir [de allí el arca de Dios]… (traducción propia, aproximada).",
             "nota": "Conservadas según los datos de Abegg: «בעלה היא קרי…» («Baalá, que es Quiri[at]…») y «ליהודה» («de Judá»); «יערים» es reconstrucción de los editores." + NOTA_ABEGG},
            {"testigos": ["vaticano"], "texto_original": m62.group(0) if m62 else "",
             "traduccion_es": "de los jefes de Judá, en subida (traducción propia).",
             "nota": "Texto de la edición de Swete (Códice Vaticano): «ἀπὸ τῶν ἀρχόντων Ἰούδα», «de los jefes de Judá», donde el TM tiene «מבעלי יהודה» (que leído como nombre común sería «de los señores de Judá»: inferido)."},
        ],
        "fuente": fuente51, "url_fuente": ll51,
        "nota": "Texto: las palabras se comprueban al generar (en el rollo, solo letras conservadas). Cuál es la lectura original es interpretación y no se incluye.",
    }, {
        "ref": "2S 8:4", "tema": "¿Mil setecientos jinetes o mil carros y siete mil jinetes? (2 S 8:4)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["2S 8:4"]["t"],
             "traduccion_es": "Y tomó David de él mil setecientos jinetes y veinte mil hombres de a pie; y desjarretó David todos los carros, y dejó de ellos cien carros (traducción propia, literal).",
             "nota": "Texto masorético (WLC): «אלף ושבע מאות פרשים», «mil setecientos jinetes», sin carros entre los tomados. La RV1909 sigue al TM («mil y setecientos de á caballo»)."},
            {"testigos": ["vaticano"], "texto_original": m84.group(0) if m84 else "",
             "traduccion_es": "mil carros y siete mil jinetes (traducción propia).",
             "nota": "Texto de la edición de Swete (Códice Vaticano): «χίλια ἅρματα καὶ ἑπτὰ χιλιάδας ἱππέων» (comprobado al generar)."},
        ],
        "fuente": "Comparación directa de las ediciones: WLC (OSHB) y Swete (LXX-Swete-1930); rollo: datos de Abegg (ETCBC/dss).",
        "url_fuente": "https://github.com/eliranwong/LXX-Swete-1930",
        "nota": ("Texto (las palabras y cifras se comprueban en cada edición). En 4Q51 (4QSam-a) los datos de Abegg conservan «דויד אלף ר…» («David, mil» y una ר): "
                 "tras «mil» no viene la ו de «ושבע» del TM sino una ר, que encaja con «רכב», «carros» (inferido); «…כב ושבעת אלפים פרשים» es reconstrucción de los editores "
                 "y no se da como lectura del rollo. Cuál es la lectura original es interpretación y no se incluye."),
    }, {
        "ref": "2S 11:3", "tema": "Urías, «escudero de Joab» en 4QSam-a (2 S 11:3)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["2S 11:3"]["t"],
             "traduccion_es": "Y envió David y preguntó por la mujer, y dijo (uno): ¿No es esta Betsabé, hija de Eliam, mujer de Urías el hitita? (traducción propia, literal).",
             "nota": "Texto masorético (WLC): acaba en «אוריה החתי», «Urías el hitita». La RV1909 sigue al TM («mujer de Uría Hetheo»)."},
            {"testigos": ["4Q51"], "texto_original": l2[(11, 3)],
             "traduccion_es": "…mujer de Urías el hitita, escudero de Joab (traducción propia; «[נ]ושא כלי יואב», «el que lleva las armas de Joab»).",
             "nota": "Conservadas según los datos de Abegg: «ושא», «כלי» y «יואב»; la נ inicial es reconstrucción de los editores." + NOTA_ABEGG},
        ],
        "fuente": fuente51, "url_fuente": ll51,
        "nota": "Texto: las palabras se comprueban al generar (en el rollo, solo letras conservadas). Swete tampoco lo tiene (su 11:3 acaba «γυνὴ Οὐρείου τοῦ Χετταίου»; comprobado que no nombra a Joab). Si el rollo añade o el TM omite es interpretación y no se incluye.",
    }, {
        "ref": "2S 13:21", "tema": "David no castiga a Amnón «porque era su primogénito» (2 S 13:21)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["2S 13:21"]["t"],
             "traduccion_es": "Y el rey David oyó todas estas cosas y se enojó mucho (traducción propia, literal).",
             "nota": "Texto masorético (WLC): acaba ahí. La RV1909 sigue al TM («fué muy enojado»)."},
            {"testigos": ["4Q51"], "texto_original": l2[(13, 21)],
             "traduccion_es": "…[y no entristeció el ánimo de Amnón su hijo, porque] lo [amaba], porque era su primogénito (traducción propia, aproximada; [ ] = reconstrucción de los editores).",
             "nota": "Conservadas según los datos de Abegg: «…ו כי בכור…» («…lo, porque primogénit…»); casi todo lo demás de la frase es reconstrucción, que coincide con el griego." + NOTA_ABEGG},
            {"testigos": ["vaticano"], "texto_original": g2["2S 13:21"],
             "traduccion_es": "Y oyó el rey David todas estas palabras y se irritó mucho; y no entristeció el espíritu de Amnón su hijo, porque lo amaba, porque era su primogénito (traducción propia).",
             "nota": "Texto de la edición de Swete (Códice Vaticano): la frase «καὶ οὐκ ἐλύπησεν… ὅτι πρωτότοκος αὐτοῦ ἦν» no está en el TM (comprobado al generar)."},
        ],
        "fuente": fuente51, "url_fuente": ll51,
        "nota": "Texto: las palabras se comprueban al generar (en el rollo, solo letras conservadas). 4Q51 y Swete coinciden aquí frente al TM. Cuál es la lectura original es interpretación y no se incluye.",
    }, {
        "ref": "2S 13:27", "tema": "«E hizo Absalón un banquete como el banquete del rey» en el griego (2 S 13:27)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["2S 13:27"]["t"],
             "traduccion_es": "Y le insistió Absalón, y envió con él a Amnón y a todos los hijos del rey (traducción propia, literal).",
             "nota": "Texto masorético (WLC). La RV1909 sigue al TM."},
            {"testigos": ["vaticano"], "texto_original": g2["2S 13:27"],
             "traduccion_es": "Y lo forzó Absalón, y envió con él a Amnón y a todos los hijos del rey; e hizo Absalón un banquete como el banquete del rey (traducción propia).",
             "nota": "Texto de la edición de Swete (Códice Vaticano): la última frase no está en el TM (comprobado al generar)."},
        ],
        "fuente": "Comparación directa de las ediciones: WLC (OSHB) y Swete (LXX-Swete-1930); rollo: datos de Abegg (ETCBC/dss).",
        "url_fuente": "https://github.com/eliranwong/LXX-Swete-1930",
        "nota": ("Texto (las palabras se comprueban en cada edición). En 4Q51 (4QSam-a) los editores reconstruyen ahí «ויעש אבשלום משתה כמשתה המלך», pero los datos de Abegg "
                 "solo conservan unas letras dañadas de «המלך»: no se da como lectura del rollo. Cuál de los dos textos es el más antiguo es interpretación y no se incluye."),
    }, {
        "ref": "2S 23:8", "tema": "El primero de los valientes: «el que se sentaba en la silla» o «Iebosthe», y la espada (2 S 23:8)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["2S 23:8"]["t"],
             "traduccion_es": ("Estos son los nombres de los valientes que tuvo David: Yoseb-basébet («el que se sienta en la silla») el tacmonita, jefe de los tres (o: de los capitanes); "
                               "él es Adino el ezenita, sobre ochocientos muertos de una vez (traducción propia, literal; «ישב בשבת» y «עדינו העצנו» son oscuros)."),
             "nota": "Texto masorético (WLC); en «העצנו» hay ketiv/qere (ver la nota del texto hebreo). La RV1909 sigue al TM («que se sentaba en cátedra… Adino el Eznita»)."},
            {"testigos": ["vaticano"], "texto_original": (m238a.group(0) + " … " + m238b.group(0)) if (m238a and m238b) else "",
             "traduccion_es": "Iebosthe el cananeo … este desenvainó su espada contra ochocientos soldados de una vez (traducción propia).",
             "nota": "Texto de la edición de Swete (Códice Vaticano): lee un nombre propio, «Ἰεβόσθε», donde el TM tiene «ישב בשבת», y «ἐσπάσατο τὴν ῥομφαίαν αὐτοῦ» («desenvainó su espada»), que el TM no tiene (comprobado al generar). La cifra, 800, es la misma."},
        ],
        "fuente": "Comparación directa de las ediciones: WLC (OSHB) y Swete (LXX-Swete-1930).",
        "url_fuente": "https://github.com/eliranwong/LXX-Swete-1930",
        "nota": "Texto (las palabras se comprueban en cada edición). Ningún rollo de los datos de Abegg conserva este versículo (comprobado). Cuál es la lectura original es interpretación y no se incluye.",
    }, {
        "ref": "2S 24:13", "tema": "¿Siete o tres años de hambre? (2 S 24:13)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["2S 24:13"]["t"],
             "traduccion_es": ("Y vino Gad a David y se lo hizo saber, y le dijo: ¿Vendrán sobre ti siete años de hambre en tu tierra, o huirás tres meses delante de tus enemigos "
                               "y ellos te perseguirán, o habrá tres días de peste en tu tierra? Ahora piensa y mira qué responderé al que me envió (traducción propia, literal)."),
             "cifra": 7, "nota": "Texto masorético (WLC): «שבע שנים רעב», «siete años de hambre». La RV1909 sigue al TM («siete años de hambre»)."},
            {"testigos": ["vaticano"], "texto_original": m2413.group(0) if m2413 else "",
             "traduccion_es": "si vendrán sobre ti tres años de hambre en tu tierra (traducción propia).",
             "cifra": 3, "nota": "Texto de la edición de Swete (Códice Vaticano): «τρία ἔτη λιμὸς», «tres años de hambre»."},
        ],
        "fuente": "Comparación directa de las ediciones: WLC (OSHB) y Swete (LXX-Swete-1930).",
        "url_fuente": "https://github.com/eliranwong/LXX-Swete-1930",
        "nota": "Texto: las cifras se comprueban en cada edición al generar. 4Q51 no conserva este versículo (comprobado). Cuál es la original es interpretación y no se incluye.",
    }, {
        "ref": "2S 24:16", "tema": "David ve al ángel con la espada desenvainada: un texto más largo en 4QSam-a (2 S 24:16)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["2S 24:16"]["t"],
             "traduccion_es": ("Y extendió el ángel su mano sobre Jerusalén para destruirla, y YHVH se arrepintió del mal, y dijo al ángel que destruía al pueblo: Basta ya, retira tu mano. "
                               "Y el ángel de YHVH estaba junto a la era de Arauna el jebuseo (traducción propia, literal)."),
             "nota": "Texto masorético (WLC): acaba en la era de Arauna. La RV1909 sigue al TM."},
            {"testigos": ["4Q51"], "texto_original": l2[(24, 16)],
             "traduccion_es": ("…[y el ángel de YH]VH estaba de pie junto a [la era de Ar]na el jebuseo. Y alzó [Da]vid [sus ojos y vio al ángel de YHVH de pie entre] la tierra y el cielo, "
                               "y su espada desenvainada en su mano, extendida [sobre Jerusalén; y cayeron los ancianos sobre] sus [rostros] cubiertos de sacos "
                               "(traducción propia, aproximada; [ ] = reconstrucción de los editores)."),
             "nota": "Conservadas según los datos de Abegg, entre otras: «עומד» («de pie»), «הארץ ובין השמים» (con letras dañadas), «שלופה בידו נטוא[ה]» («desenvainada en su mano, extendida») y «שקים» («sacos»)." + NOTA_ABEGG},
        ],
        "fuente": fuente51, "url_fuente": ll51,
        "nota": "Texto: las palabras se comprueban al generar (en el rollo, solo letras conservadas). Swete tampoco tiene la frase (sin «ῥομφαία» ni «σάκκος» en su 24:16; comprobado). Si el rollo añade o el TM omite es interpretación y no se incluye.",
    }]
    for t in testigos:
        if t["id"] == "4Q51":
            t["nota"] += " En 2 Samuel es el testigo de las variantes de 5:6, 6:2, 11:3, 13:21 y 24:16 (y se cita en las notas de 5:8, 8:4 y 13:27)."

    # ---- 1 Reyes: versificación, comparación versículo a versículo, bloques de la LXX, ketiv/qere, Vaticano, rollos y variantes
    r1 = [k for k in orden_rv if k[0] == "1R"]
    if len(r1) != 816 or not all(texto_rv[k] for k in r1):
        fallo(f"1 R: se esperaban 816 versículos RV con texto; hay {len(r1)}")
    if len([k for k in heb if k[0] == "1R"]) != 817 or ("1R", 5, 32) not in heb or ("1R", 22, 54) not in heb or ("1R", 4, 21) in heb:
        fallo("1 R: se esperaban 817 versículos en el WLC (4:1-20, 5:1-32, 22:1-54)")
    if len([k for k in gr if k[0] == "1R"]) != 814:
        fallo(f"1 R: se esperaban 814 marcas de versículo en Swete; hay {len([k for k in gr if k[0] == '1R'])}")
    linea_1r = next((l.split("\t")[2].strip() for l in lineas_tv if l.startswith("1Ki\t1Kgs\t")), "")
    ult_1r_kjv = "; ".join(f"{c}:{max(v for _, cc, v in r1 if cc == c)}" for c in sorted({k[1] for k in r1}))
    if linea_1r != ult_1r_kjv:
        fallo(f"1 R TVTMS: la tabla de la KJV «{linea_1r}» debería coincidir con los últimos versículos de la RV «{ult_1r_kjv}»")
    if sorted(bloques_sin_col_1r) != ["$1Ki.2:8--7:23", "$1Ki.5:17--6:38"]:
        fallo(f"1 R TVTMS: bloques sin columna griega válida para Swete {bloques_sin_col_1r}")
    dif_tv = [ref(*k) for k in r1 if (k[1] in (7, 20, 21) or (k[1] == 11 and 5 <= k[2] <= 8)) and mapa_g.get(k) != tvtms_1r.get(k)]
    if dif_tv:
        fallo(f"1 R griego: la tabla propia no coincide con el TVTMS en {dif_tv}")
    for nom, formas in NOMBRES_1R_HEBREO:
        en_rv = {k for k in r1 if nom in texto_rv[k]}
        en_h = {k for k in r1 if any(w.endswith(f) and len(w) - len(f) <= 2 for w in consonantes(hebreo[ref(*k)]["t"]).split() for f in formas)}
        if not en_rv or en_rv != en_h:
            fallo(f"1 R «{nom}»: versículos RV {sorted(en_rv - en_h)} / hebreo {sorted(en_h - en_rv)} no coinciden")
    for nom, forma in NOMBRES_1R_GRIEGO:
        en_rv = {k for k in r1 if nom in texto_rv[k] and ref(*k) in griego}
        en_g = {k for k in r1 if any(w.startswith(forma) for w in re.findall(r"\w+", sin_acentos(griego.get(ref(*k), ""))))}
        if not en_rv or en_rv != en_g:
            fallo(f"1 R «{nom}»: versículos RV {sorted(en_rv - en_g)} / griego {sorted(en_g - en_rv)} no coinciden")
    # bloques que la LXX añade con letra: fuera de los versículos, en «bloques_sin_paralelo»
    import zipfile
    ruta_br = CACHE / "eng-Brenton_vpl.zip"
    brenton = {}
    if ruta_br.exists():
        for l in zipfile.ZipFile(ruta_br).read("eng-Brenton_vpl.txt").decode("utf-8-sig").splitlines():
            mb = re.match(r"1KI (\d+:\d+)([a-z])? (.*)$", l)
            if mb and mb[2]:
                brenton.setdefault(mb[1], {})[mb[2]] = mb[3]
    else:
        fallo("falta cache/eng-Brenton_vpl.zip (lo descarga construir_datos.py) para comprobar las letras de los bloques")
    letras_br = sorted(f"{v}{l}" for v, d in brenton.items() for l in d)
    esperadas = []
    bloques_1r = []
    for sw, corte, enteros, tras, letras, nota in BLOQUES_1R:
        r, ktras = ref("1R", *tras), ("1R",) + tras
        v_br, l0, l1 = re.fullmatch(r"(\d+:\d+)([a-z])(?:-([a-z]))?", letras).groups()
        let = [chr(x) for x in range(ord(l0), ord(l1 or l0) + 1) if chr(x) in brenton.get(v_br, {})]
        esperadas += [v_br + x for x in let]
        if sw:
            txt = griego.get(r, "")
            if mapa_g.get(ktras) != [("1R",) + sw] or txt.count(corte) != 1:
                fallo(f"bloque {letras}: se esperaba «{corte}» una vez en Swete {ref('1R', *sw)} (= RV {r})")
                continue
            i = txt.index(corte)
            cabeza, bloque = txt[:i].strip(), txt[i:].strip()
            if corte == "[1]":
                marcas = [int(x) for x in re.findall(r"\[(\d+)\]", bloque)]
                if [chr(96 + n) for n in marcas] != let:
                    fallo(f"bloque {letras}: marcas de Swete {marcas} ≠ letras de Brenton {let}")
                ref_sw = f"{ref('1R', *sw)}, desde la marca «[1]»"
            else:
                if len(let) != 1:
                    fallo(f"bloque {letras}: se esperaba una letra en Brenton")
                ref_sw = f"final de {ref('1R', *sw)}, desde «{corte}»"
            griego[r] = cabeza
        else:
            ks = [("1R",) + x for x in enteros]
            if any(k in usos_g or not gr.get(k) for k in ks) or len(ks) < len(let) - 1:
                fallo(f"bloque {letras}: Swete {[ref(*k) for k in ks]} vacío o ya asignado")
                continue
            bloque = " ".join(gr[k] for k in ks)
            ref_sw = ref(*ks[0]) + (f"-{ks[-1][2]}" if len(ks) > 1 else "")
        pg, vb, pb = ANCLAS_BLOQUES_1R[letras]
        if pg not in bloque or pb not in brenton.get(vb.rstrip("abcdefghijklmnopqrstuvwxyz"), {}).get(vb[-1], ""):
            fallo(f"bloque {letras}: ancla «{pg}» (Swete) / «{pb}» (Brenton {vb}) no encontrada")
        bloques_1r.append({"ref_swete": ref_sw, "brenton": letras, "tras": r, "texto": bloque, "nota": nota})
        notas_griego[r] = (notas_griego.get(r, "") + f" Tras este versículo la LXX (Swete, {ref_sw}) trae texto sin paralelo en el hebreo ni en la RV1909 "
                           f"({letras} en la numeración de Brenton): {nota} No se muestra como texto de ningún versículo: va aparte, en «bloques_sin_paralelo» de griego-swete.js.").strip()
    if sorted(esperadas) != letras_br:
        fallo(f"1 R: versículos con letra de Brenton no recogidos en BLOQUES_1R {sorted(set(letras_br) - set(esperadas))}")
    if any(re.search(r"\[\d+\]", griego.get(ref(*k), "")) for k in r1):
        fallo("1 R griego: quedan marcas «[n]» dentro de algún versículo")
    asig_1r = sorted(ref(*d) for d in gr if d[0] == "1R" and d not in usos_g and gr[d])
    ent_1r = sorted(ref("1R", *x) for b in BLOQUES_1R for x in (b[2] or []))
    if asig_1r != ent_1r:
        fallo(f"1 R griego sin asignar {asig_1r}, se esperaban los bloques enteros {ent_1r}")
    extremos_1r = {}
    for idioma in ("hebreo", "griego"):
        a, b = RATIO_1R[idioma]
        rs = []
        for k in r1:
            n = largo_orig(k, idioma)
            if not n:
                continue
            x = largo_rv(k) / n
            rs.append((round(x, 2), ref(*k)))
            if not a <= x <= b:
                fallo(f"{ref(*k)}: proporción de longitud RV/{idioma} {x:.2f} fuera de {a}-{b}")
        extremos_1r[idioma] = (min(rs), max(rs))
        lg = sorted(math.log(x) for x, _ in rs)
        med = lg[len(lg) // 2]
        for c in sorted({k[1] for k in r1}):
            vs = [k for k in r1 if k[1] == c]

            def coste3(d):
                tot, n = 0.0, 0
                for k in vs:
                    k2 = (k[0], k[1], k[2] + d)
                    lo = largo_orig(k2, idioma) if texto_rv.get(k2) else 0
                    if lo and largo_orig(k, idioma):
                        tot += abs(math.log(largo_rv(k) / lo) - med)
                        n += 1
                return tot / n if n else 99
            if not (coste3(0) < coste3(1) and coste3(0) < coste3(-1)):
                fallo(f"1 R {c} ({idioma}): el emparejamiento con desfase compara mejor que sin desfase ({coste3(-1):.3f} {coste3(0):.3f} {coste3(1):.3f})")
    # griego: lista exacta de lo que no tiene texto, y comprobación de que el versículo de Swete con el mismo número está vacío o se usa en otro
    sin_gr_1r = {k for k in r1 if ref(*k) in sin_griego}
    if sin_gr_1r != set(SIN_GRIEGO_1R) | set(EXTRA_SIN_1R):
        fallo(f"1 R griego: sin texto distinto de lo esperado {sorted(sin_gr_1r ^ (set(SIN_GRIEGO_1R) | set(EXTRA_SIN_1R)))}")
    for k in SIN_GRIEGO_1R:
        mismo = ("1R", 20 if k[1] == 21 else 21 if k[1] == 20 else k[1], k[2])
        if gr.get(mismo) and mismo not in usos_g and not any(mismo in [("1R",) + x for x in (b[2] or [])] for b in BLOQUES_1R):
            fallo(f"{ref(*k)}: Swete {ref(*mismo)} tiene texto y no se usa")
    for k, extra in EXTRA_SIN_1R.items():
        if "marca de versículo sin palabras" not in sin_griego.get(ref(*k), ""):
            fallo(f"{ref(*k)}: se esperaba la marca vacía en Swete")
        sin_griego[ref(*k)] = sin_griego.get(ref(*k), "") + extra
    for k in r1:                                         # nota de los versículos que la LXX pone en otro orden (tabla propia)
        ds = mapa_g.get(k)
        if ds and ds != [k] and ds != tvtms_1r.get(k) and k not in DIRECTO_1R_22:
            notas_griego[ref(*k)] = ("La LXX pone este texto en otro lugar o lo numera de otra forma: Swete " + ref_griega[ref(*k)].replace("1R ", "")
                                     + ". Correspondencia propia por contenido (la digitalización de Swete no numera 1 R 4–6 y 10 como ninguna columna del TVTMS)."
                                     + (" " + notas_griego[ref(*k)] if ref(*k) in notas_griego else ""))
    for c, otro in ((20, 21), (21, 20)):
        for k in r1:
            if k[1] == c and ref(*k) in griego:
                notas_griego[ref(*k)] = (f"La LXX invierte el orden de los capítulos 20 y 21: RV {c} es el capítulo {otro} de Swete "
                                         f"({'las guerras con Ben-adad' if c == 20 else 'la viña de Nabot'}). Correspondencia del TVTMS (columna Greek*), comprobada por contenido.")
    for t in testigos:
        if t["id"] == "vaticano":
            t["contiene"] += comprimir([k for k in r1 if ref(*k) in griego], indice)
    # ketiv / qere
    ux_1r = obtener("uxlc_1r", sin_red)
    kq3, kq3_ux, n_kq_1r = ketiv_qere("1R", "oshb_1r", ux_1r, KQ_UNIDOS_1R, KQ_SOLO_UXLC_1R, KQ_SOLO_OSHB_1R, KQ_DISTINTOS_1R, N_KQ_1R)
    # rollos de 1 Reyes (todos los de los datos de Abegg con texto de 1 R)
    con_1r = sorted(sc for sc, d in pal.items() if any(k[0] == "1R" and any(c for _, c in ws) for k, ws in d.items()))
    if con_1r != ["4Q54", "5Q2", "6Q4"]:
        fallo(f"1 R: rollos con texto en los datos de Abegg {con_1r}")
    # variantes de 1 Reyes (cada palabra o cifra se comprueba en su fuente; en el rollo, solo letras fuera de [ ])
    h3 = {r: consonantes(hebreo[r]["t"]) for r in ("1R 6:1", "1R 8:16", "1R 15:9", "1R 16:29")}
    g3 = {r: griego.get(r, "") for r in h3}
    m61 = re.search(r"ἐν τῷ τεσσερακοστῷ καὶ τετρακοσιοστῷ ἔτει τῆς ἐξόδου", g3["1R 6:1"])
    if not (m61 and "בשמונים שנה וארבע מאות שנה" in h3["1R 6:1"] and "cuatrocientos ochenta" in texto_rv[("1R", 6, 1)]):
        fallo("variante 1 R 6:1: cifras no comprobadas")
    m159 = re.search(r"Ἐν τῷ ἐνιαυτῷ τῷ τετάρτῳ καὶ εἰκοστῷ τοῦ Ἰεροβοὰμ", g3["1R 15:9"])
    if not (m159 and "ובשנת עשרים לירבעם" in h3["1R 15:9"] and "En el año veinte de Jeroboam" in texto_rv[("1R", 15, 9)]):
        fallo("variante 1 R 15:9: cifras no comprobadas")
    m1629 = re.search(r"Ἐν ἔτει δευτέρῳ τῷ Ἰωσαφὰθ", g3["1R 16:29"])
    if not (m1629 and "בשנת שלשים ושמנה שנה לאסא" in h3["1R 16:29"] and "Asa" in texto_rv[("1R", 16, 29)] and "treinta y ocho" in texto_rv[("1R", 16, 29)]
            and "Ἀσὰ" not in g3["1R 16:29"]):
        fallo("variante 1 R 16:29: lecturas no comprobadas")
    c816 = cons_rollo("4Q54", ("1R", 8, 16))
    m816 = re.search(r"καὶ ἐξελεξάμην ἐν Ἰερουσαλὴμ μεῖναι τὸ ὄνομά μου ἐκεῖ", g3["1R 8:16"])
    if not ("נגיד" in c816 and "נגיד" not in h3["1R 8:16"].split() and "ירושלם" not in h3["1R 8:16"] and m816
            and "בירושלם" not in c816 and "Jerusalem" not in texto_rv[("1R", 8, 16)]):
        fallo(f"variante 1 R 8:16: lecturas no comprobadas ({c816})")
    l816 = dss_lectura("4Q54", ("1R", 8, 16))[0]
    ll54 = LL + "4Q54-1"
    variantes += [{
        "ref": "1R 6:1", "tema": "¿480 o 440 años desde la salida de Egipto hasta el templo? (1 R 6:1)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["1R 6:1"]["t"],
             "traduccion_es": ("Y fue en el año cuatrocientos ochenta de la salida de los hijos de Israel de la tierra de Egipto, en el año cuarto, en el mes de Ziv, "
                               "que es el mes segundo, del reinado de Salomón sobre Israel, que edificó la casa a YHVH (traducción propia, literal)."),
             "cifra": 480, "nota": "Texto masorético (WLC): «בִּשְׁמוֹנִים שָׁנָה וְאַרְבַּע מֵאוֹת שָׁנָה», «en el año ochenta y cuatrocientos». La RV1909 sigue al TM («cuatrocientos ochenta»)."},
            {"testigos": ["vaticano"], "texto_original": m61.group(0) if m61 else "",
             "traduccion_es": "en el año cuadragésimo y cuadringentésimo de la salida (traducción propia).",
             "cifra": 440, "nota": "Texto de la edición de Swete (Códice Vaticano): «τεσσερακοστῷ καὶ τετρακοσιοστῷ», 440."},
        ],
        "fuente": "Comparación directa de las ediciones: WLC (OSHB) y Swete (LXX-Swete-1930).",
        "url_fuente": "https://github.com/eliranwong/LXX-Swete-1930",
        "nota": "Texto: las cifras se comprueban en cada edición al generar. La cronología de la app ya usa las dos cifras (biblia.js, «ev-templo-salomon»). Ningún rollo de los datos de Abegg conserva 1 R 6. Cuál es la original es interpretación y no se incluye.",
    }, {
        "ref": "1R 8:16", "tema": "«No escogí a nadie para ser príncipe sobre mi pueblo»: una frase más en 4QKgs (1 R 8:16)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["1R 8:16"]["t"],
             "traduccion_es": ("Desde el día que saqué a mi pueblo Israel de Egipto no escogí ciudad de todas las tribus de Israel para edificar casa donde estuviese mi nombre, "
                               "pero escogí a David para que estuviese sobre mi pueblo Israel (traducción propia, literal)."),
             "nota": "Texto masorético (WLC): no tiene «נָגִיד» («príncipe») ni nombra Jerusalén (comprobado al generar). La RV1909 sigue al TM."},
            {"testigos": ["4Q54"], "texto_original": l816,
             "traduccion_es": ("…[y no escogí a ningún hombre para] ser príncipe sobre [mi] pueblo [Israel… y escogí a David pa]ra estar sobre mi pueblo… "
                               "(traducción propia, aproximada; [ ] = reconstrucción de los editores)."),
             "nota": "Conservadas según los datos de Abegg: «היות נגיד על ע[מ]י» («ser príncipe sobre mi pueblo», con letras dañadas) y «ל היות על עמי» al final; "
                     "el resto, también la mención de Jerusalén, es reconstrucción de los editores (no se usa)." + NOTA_ABEGG},
            {"testigos": ["vaticano"], "texto_original": m816.group(0) if m816 else "",
             "traduccion_es": "y escogí Jerusalén para que mi nombre permaneciese allí (traducción propia).",
             "nota": "Texto de la edición de Swete (Códice Vaticano): tiene la elección de Jerusalén, que el TM no tiene, pero no la frase del «príncipe» (comprobado al generar)."},
        ],
        "fuente": "Edición oficial de 4QKgs (4Q54): Trebolle Barrera 1995, DJD 14: 171-183, según la Leon Levy Library. Lectura del rollo comprobada en los datos de Abegg (ETCBC/dss); TM en el WLC; LXX en Swete.",
        "url_fuente": ll54,
        "nota": "Texto: las palabras se comprueban al generar (en el rollo, solo letras conservadas). Cuál es la lectura original, y si el TM perdió la frase, es interpretación y no se incluye.",
    }, {
        "ref": "1R 15:9", "tema": "¿En el año veinte o veinticuatro de Jeroboam empezó a reinar Asa? (1 R 15:9)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["1R 15:9"]["t"],
             "traduccion_es": "Y en el año veinte de Jeroboam, rey de Israel, reinó Asa sobre Judá (traducción propia, literal).",
             "cifra": 20, "nota": "Texto masorético (WLC): «בִשְׁנַת עֶשְׂרִים לְיָרָבְעָם». La RV1909 sigue al TM («En el año veinte de Jeroboam»)."},
            {"testigos": ["vaticano"], "texto_original": m159.group(0) if m159 else "",
             "traduccion_es": "En el año vigésimo cuarto de Jeroboam (traducción propia).",
             "cifra": 24, "nota": "Texto de la edición de Swete (Códice Vaticano)."},
        ],
        "fuente": "Comparación directa de las ediciones: WLC (OSHB) y Swete (LXX-Swete-1930).",
        "url_fuente": "https://github.com/eliranwong/LXX-Swete-1930",
        "nota": "Texto: las cifras se comprueban al generar. Es uno de los sincronismos de los reyes que la LXX da de otra forma (ver también 16:29); la cronología de la app los recoge en «reinados». Cómo se explica la diferencia es interpretación y no se incluye.",
    }, {
        "ref": "1R 16:29", "tema": "¿Acab empezó a reinar en el año 38 de Asa o en el segundo de Josafat? (1 R 16:29)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["1R 16:29"]["t"],
             "traduccion_es": ("Y Acab hijo de Omri reinó sobre Israel en el año treinta y ocho de Asa, rey de Judá; y reinó Acab hijo de Omri sobre Israel en Samaria "
                               "veintidós años (traducción propia, literal)."),
             "cifra": 38, "nota": "Texto masorético (WLC): «בִּשְׁנַת שְׁלֹשִׁים וּשְׁמֹנֶה שָׁנָה לְאָסָא». La RV1909 sigue al TM («el año treinta y ocho de Asa»)."},
            {"testigos": ["vaticano"], "texto_original": m1629.group(0) if m1629 else "",
             "traduccion_es": "En el año segundo de Josafat (traducción propia).",
             "cifra": 2, "nota": "Texto de la edición de Swete (Códice Vaticano): fecha por el rey siguiente de Judá, Josafat, no por Asa (comprobado al generar). Los veintidós años de reinado son los mismos."},
        ],
        "fuente": "Comparación directa de las ediciones: WLC (OSHB) y Swete (LXX-Swete-1930).",
        "url_fuente": "https://github.com/eliranwong/LXX-Swete-1930",
        "nota": "Texto: las cifras se comprueban al generar. La «cifra» de cada lectura cuenta años de reyes distintos (Asa y Josafat): no se pueden restar. Cómo se explica es interpretación y no se incluye.",
    }]
    for t in testigos:
        if t["id"] == "4Q54":
            t["nota"] += " Es el testigo de la variante de 1 R 8:16 (comprobada al generar en los datos de Abegg)."

    # ---- 2 Reyes: versificación (11:21-12:21), comparación versículo a versículo y con el UXLC, bloque de la LXX, ketiv/qere, Vaticano, rollos y variantes
    r2 = [k for k in orden_rv if k[0] == "2R"]
    if len(r2) != 719 or not all(texto_rv[k] for k in r2):
        fallo(f"2 R: se esperaban 719 versículos RV con texto; hay {len(r2)}")
    if len([k for k in heb if k[0] == "2R"]) != 719 or ("2R", 12, 22) not in heb or ("2R", 11, 21) in heb:
        fallo("2 R: se esperaban 719 versículos en el WLC, con 11:1-20 y 12:1-22")
    if len([k for k in gr if k[0] == "2R"]) != 719 or ("2R", 11, 21) not in gr or ("2R", 12, 22) in gr:
        fallo("2 R: se esperaban 719 versículos en Swete, con 11:1-21 y 12:1-21 (como la RV1909)")
    cap_sw = {c: max(v for l, cc, v in gr if l == "2R" and cc == c) for c in range(1, 26)}
    cap_rv = {c: max(v for _, cc, v in r2 if cc == c) for c in range(1, 26)}
    if cap_sw != cap_rv:
        fallo(f"2 R: recuentos por capítulo de Swete {cap_sw} distintos de la RV {cap_rv}")
    linea_2r = next((l.split("\t")[2].strip() for l in lineas_tv if l.startswith("2Ki\t2Kgs\t")), "")
    ult_2r = "; ".join(f"{c}:{cap_rv[c]}" for c in sorted(cap_rv))
    if linea_2r != ult_2r:
        fallo(f"2 R TVTMS: la tabla de la KJV «{linea_2r}» debería coincidir con los últimos versículos de la RV «{ult_2r}»")
    if [b["cab"][0] for b in bloques if b["cab"][0].startswith("$2Ki.")] != ["$2Ki.11:21--12:21"]:
        fallo("2 R TVTMS: se esperaba un solo bloque, $2Ki.11:21--12:21")
    if [ref(*k) for k in r2 if (mapa_h.get(k) != [k]) != (k == ("2R", 11, 21) or k[1] == 12)]:
        fallo("2 R: solo 11:21 y 12:1-21 deberían tener otra numeración hebrea")
    if [ref(*k) for k in r2 if mapa_g.get(k) not in ([k], None)]:
        fallo("2 R griego: se esperaba la misma numeración que la RV en todo el libro")
    # 11–12 por contenido (hebreo, griego y RV)
    h2r = {r: consonantes(hebreo[r]["t"]).split() for r in ("2R 11:20", "2R 11:21", "2R 12:1", "2R 12:21", "2R 13:1")}
    anclas_2r = [("2R 11:20", "עתליהו", "Γοθολίαν", "Athalía"), ("2R 11:21", "שבע", "ἐπτὰ", "siete años"),
                 ("2R 12:1", "ליהוא", "ἑβδόμῳ τῷ Εἰοὺ", "séptimo año de Jehú"), ("2R 12:21", "אמציה", "Ἰεζειχὰρ", "Amasías su hijo"),
                 ("2R 13:1", "ושלש", "εἰκοστῷ καὶ τρίτῳ", "veintitrés")]
    for r, ph, pg, pr in anclas_2r:
        k = ("2R",) + tuple(int(x) for x in r[3:].split(":"))
        if ph not in h2r[r] or pg not in griego.get(r, "") or pr not in texto_rv[k]:
            fallo(f"ancla de {r}: se esperaba «{ph}» en el hebreo, «{pg}» en el griego y «{pr}» en la RV")
    if "יהואש" not in h2r["2R 11:21"] or "Joas" not in texto_rv[("2R", 11, 21)] or "Ἰωὰς" not in griego.get("2R 11:21", ""):
        fallo("2 R 11:21: se esperaba Joás (יהואש, Ἰωὰς) en las tres tradiciones")
    # el WLC (OSHB) y el UXLC tienen las mismas consonantes en los 719 versículos (el UXLC sin sus qere ni notas)
    ux_2r = obtener("uxlc_2r", sin_red)
    s_ux = ux_2r.read_text(encoding="utf-8")
    ux_cons = {}
    for mc in re.finditer(r'<c n="(\d+)">(.*?)</c>', s_ux, re.S):
        for mv in re.finditer(r'<v n="(\d+)">(.*?)</v>', mc[2], re.S):
            ux_cons[("2R", int(mc[1]), int(mv[1]))] = "".join(consonantes(re.sub(r"<q>.*?</q>|<x>.*?</x>|<[^>]+>", " ", mv[2])).split())
    heb_2r = {k: t for k, t in heb.items() if k[0] == "2R"}
    dif_ux = [ref(*k) for k in heb_2r if ux_cons.get(k) != "".join(consonantes(heb_2r[k]).split())]
    if set(ux_cons) != set(heb_2r) or dif_ux:
        fallo(f"2 R: el UXLC y el WLC (OSHB) no coinciden ({len(ux_cons)} y {len(heb_2r)} versículos; distintos {dif_ux[:10]})")
    for nom, formas in NOMBRES_2R_HEBREO:
        en_rv = {k for k in r2 if nom in texto_rv[k]}
        en_h = {k for k in r2 if any(w.endswith(f) and len(w) - len(f) <= 2 for w in consonantes(hebreo[ref(*k)]["t"]).split() for f in formas)}
        if not en_rv or en_rv != en_h:
            fallo(f"2 R «{nom}»: versículos RV {sorted(en_rv - en_h)} / hebreo {sorted(en_h - en_rv)} no coinciden")
    for nom, forma in NOMBRES_2R_GRIEGO:
        en_rv = {k for k in r2 if nom in texto_rv[k] and ref(*k) in griego}
        en_g = {k for k in r2 if any(w.startswith(forma) for w in re.findall(r"\w+", sin_acentos(griego.get(ref(*k), ""))))}
        if not en_rv or en_rv != en_g:
            fallo(f"2 R «{nom}»: versículos RV {sorted(en_rv - en_g)} / griego {sorted(en_g - en_rv)} no coinciden")
    # bloque que la LXX añade tras 1:18 (1:18a-d en Brenton): fuera del versículo, en «bloques_sin_paralelo»
    br_2r, br_2510 = {}, ""
    if ruta_br.exists():
        for l in zipfile.ZipFile(ruta_br).read("eng-Brenton_vpl.txt").decode("utf-8-sig").splitlines():
            mb = re.match(r"2KI (\d+:\d+)([a-z])? (.*)$", l)
            if mb and mb[1] == "25:10" and not mb[2]:
                br_2510 = mb[3]
            if mb and mb[2]:
                br_2r.setdefault(mb[1], {})[mb[2]] = mb[3]
    bloques_2r = []
    t118 = griego.get("2R 1:18", "")
    if sorted(f"{v}{l}" for v, d in br_2r.items() for l in d) != ["1:18a", "1:18b", "1:18c", "1:18d"] or t118.count("[1]") != 1:
        fallo(f"2 R: se esperaba un solo bloque con letra en Brenton (1:18a-d) y la marca «[1]» una vez en Swete 1:18 ({sorted(br_2r)})")
    else:
        i = t118.index("[1]")
        cabeza, bloque = t118[:i].strip(), t118[i:].strip()
        if [int(x) for x in re.findall(r"\[(\d+)\]", bloque)] != [1, 2, 3, 4] or "Ἰωρὰμ υἱὸς Ἀχαὰβ" not in bloque \
                or "ἐν ἔτει ὀκτωκαιδεκάτῳ Ἰωσαφὰθ" not in bloque or "Joram son of Achaab" not in br_2r["1:18"]["a"] \
                or not cabeza.startswith("καὶ τὰ λοιπὰ τῶν λόγων Ὀχοζείου") or "Ochôzías" not in texto_rv[("2R", 1, 18)]:
            fallo("2 R 1:18: el bloque de la LXX no tiene las marcas [1]-[4] y las anclas esperadas")
        griego["2R 1:18"] = cabeza
        bloques_2r.append({"ref_swete": "2R 1:18, desde la marca «[1]»", "brenton": "1:18a-d", "tras": "2R 1:18", "texto": bloque, "nota": BLOQUE_2R_118})
        notas_griego["2R 1:18"] = (notas_griego.get("2R 1:18", "") + " Tras este versículo la LXX (Swete, 2R 1:18, desde la marca «[1]») trae texto sin "
                                   f"paralelo en el hebreo ni en la RV1909 (1:18a-d en la numeración de Brenton): {BLOQUE_2R_118} No se muestra como texto "
                                   "de ningún versículo: va aparte, en «bloques_sin_paralelo» de griego-swete.js.").strip()
    if any(re.search(r"\[\d+\]", griego.get(ref(*k), "")) for k in r2):
        fallo("2 R griego: quedan marcas «[n]» dentro de algún versículo")
    if [d for d in gr if d[0] == "2R" and gr[d] and d not in usos_g]:
        fallo("2 R griego: versículos de Swete sin asignar")
    for r in ("2R 11:21", "2R 12:1"):
        notas_griego[r] = (notas_griego.get(r, "") + " " + NOTA_2R_11_12).strip()
    # longitudes y desfase por capítulo
    extremos_2r = {}
    for idioma in ("hebreo", "griego"):
        a, b = RATIO_2R[idioma]
        rs = []
        for k in r2:
            n = largo_orig(k, idioma)
            if not n:
                continue
            x = largo_rv(k) / n
            rs.append((round(x, 2), ref(*k)))
            if not a <= x <= b:
                fallo(f"{ref(*k)}: proporción de longitud RV/{idioma} {x:.2f} fuera de {a}-{b}")
        extremos_2r[idioma] = (min(rs), max(rs))
        lg = sorted(math.log(x) for x, _ in rs)
        med = lg[len(lg) // 2]
        for c in sorted({k[1] for k in r2}):
            vs = [k for k in r2 if k[1] == c]

            def coste4(d):
                tot, n = 0.0, 0
                for k in vs:
                    k2 = (k[0], k[1], k[2] + d)
                    lo = largo_orig(k2, idioma) if texto_rv.get(k2) else 0
                    if lo and largo_orig(k, idioma):
                        tot += abs(math.log(largo_rv(k) / lo) - med)
                        n += 1
                return tot / n if n else 99
            if not (coste4(0) < coste4(1) and coste4(0) < coste4(-1)):
                fallo(f"2 R {c} ({idioma}): el emparejamiento con desfase compara mejor que sin desfase ({coste4(-1):.3f} {coste4(0):.3f} {coste4(1):.3f})")
    # griego: solo 25:10 sin texto (marca vacía en la digitalización)
    if [r for r in sin_griego if r.startswith("2R ")] != ["2R 25:10"] or "marca de versículo sin palabras" not in sin_griego["2R 25:10"] \
            or "wall of Jerusalem" not in br_2510:
        fallo(f"2 R griego: sin texto {[r for r in sin_griego if r.startswith('2R ')]}, se esperaba solo 25:10 (y su texto en Brenton)")
    else:
        sin_griego["2R 25:10"] += NOTA_2R_25_10
    for t in testigos:
        if t["id"] == "vaticano":
            t["contiene"] += comprimir([k for k in r2 if ref(*k) in griego], indice)
    # ketiv / qere
    kq4, kq4_ux, n_kq_2r = ketiv_qere("2R", "oshb_2r", ux_2r, KQ_UNIDOS_2R, set(), {}, {}, N_KQ_2R)
    # rollos de 2 Reyes (todos los de los datos de Abegg con texto de 2 R)
    con_2r = sorted(sc for sc, d in pal.items() if any(k[0] == "2R" and any(c for _, c in ws) for k, ws in d.items()))
    if con_2r != ["6Q4"]:
        fallo(f"2 R: rollos con texto en los datos de Abegg {con_2r}")
    caps_6q4 = sorted({k[1] for k, ws in pal.get("6Q4", {}).items() if k[0] == "2R" and any(c for _, c in ws)})
    c78 = cons_rollo("6Q4", ("2R", 7, 8))
    h78 = consonantes(hebreo["2R 7:8"]["t"]).split()
    if caps_6q4 != [5, 6, 7, 8, 9, 10] or "משואם" not in c78 or "משואם" in h78 or h78.count("משם") != 2:
        fallo(f"6Q4: se esperaban letras de 2 R 5–10 y «משואם» conservado en 7:8 ({caps_6q4}, {c78})")
    for t in testigos:
        if t["id"] == "6Q4":
            t["nota"] += (" En los datos de Abegg tiene también texto de 2 Reyes (letras conservadas en 2 R " + ", ".join(map(str, caps_6q4))
                          + "; ver «contiene»). Comparado con el TM solo da diferencias pequeñas, que no se presentan como variantes: en 2 R 7:8 "
                          "conserva «משואם» («su carga») donde el TM lee «משם» («de allí»), y otras de ortografía (comprobado al generar en los datos de Abegg).")
    # variantes de 2 Reyes (cada palabra o cifra se comprueba en su fuente)
    h117 = consonantes(hebreo["2R 1:17"]["t"])
    m31 = re.search(r"ἐν ἔτει ὀκτωκαιδεκάτῳ Ἰωσαφὰθ", griego.get("2R 3:1", ""))
    b118 = bloques_2r[0]["texto"] if bloques_2r else ""
    m118 = re.search(r"Ἰωρὰμ υἱὸς Ἀχαὰβ βασιλεύει ἐπὶ Ἰσραὴλ ἐν Σαμαρείᾳ ἔτη δέκα δύο, ἐν ἔτει ὀκτωκαιδεκάτῳ Ἰωσαφὰθ βασιλέως Ἰούδα", b118)
    if not ("בשנת שתים ליהורם בן יהושפט" in h117 and "Ἰωρὰμ" not in griego.get("2R 1:17", "") and "ἔτει" not in griego.get("2R 1:17", "")
            and m31 and m118 and "בשנת שמנה עשרה ליהושפט" in consonantes(hebreo["2R 3:1"]["t"])
            and "en el segundo año de Joram, hijo de Josaphat" in texto_rv[("2R", 1, 17)] and "el año dieciocho de Josaphat" in texto_rv[("2R", 3, 1)]):
        fallo("variante 2 R 1:17: lecturas no comprobadas")
    h1221 = consonantes(hebreo["2R 12:21"]["t"]).split()
    m1221 = re.search(r"Ἰεζειχὰρ υἱὸς Ἰεμουὰθ", griego.get("2R 12:21", ""))
    if not (h1221[:3] == ["ויוזבד", "בן", "שמעת"] and "יוזכר" not in h1221 and m1221 and "Josachâr hijo de Simaath" in texto_rv[("2R", 12, 21)]
            and "יוזבד" in ux_cons.get(("2R", 12, 22), "")):
        fallo("variante 2 R 12:21: lecturas no comprobadas")
    variantes += [{
        "ref": "2R 1:17", "tema": "¿Cuándo empezó a reinar Joram de Israel? El sincronismo de 2 R 1:17 y 3:1",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["2R 1:17"]["t"],
             "traduccion_es": ("Y murió conforme a la palabra de YHVH que había hablado Elías; y reinó Joram en su lugar, en el año segundo de Joram hijo de Josafat, "
                               "rey de Judá, porque no tenía hijo (traducción propia, literal)."),
             "nota": ("Texto masorético (WLC): fecha el comienzo de Joram de Israel por Joram de Judá («בִּשְׁנַת שְׁתַּיִם לִיהוֹרָם בֶּן־יְהוֹשָׁפָט»); en 3:1 "
                      "el mismo TM lo fecha en «el año dieciocho de Josafat» (comprobado al generar). La RV1909 sigue al TM en los dos lugares.")},
            {"testigos": ["vaticano"], "texto_original": griego.get("2R 1:17", "") + " … " + (m118.group(0) if m118 else ""),
             "traduccion_es": ("Y murió según la palabra del Señor que habló Elías. … Joram hijo de Acab reina sobre Israel en Samaria doce años, en el año "
                               "dieciocho de Josafat, rey de Judá (traducción propia)."),
             "nota": ("Texto de la edición de Swete (Códice Vaticano): su 1:17 no tiene el sincronismo ni «no tenía hijo», y el bloque que añade tras 1:18 "
                      "(1:18a en Brenton; ver «bloques_sin_paralelo») da solo el año dieciocho de Josafat, como su 3:1 (comprobado al generar).")},
        ],
        "fuente": "Comparación directa de las ediciones: WLC (OSHB) y Swete (LXX-Swete-1930).",
        "url_fuente": "https://github.com/eliranwong/LXX-Swete-1930",
        "nota": "Texto: las palabras se comprueban en cada edición al generar. Ningún rollo de los datos de Abegg conserva 2 R 1 ni 3. Cómo se concilian las dos fechas del TM es interpretación y no se incluye.",
    }, {
        "ref": "2R 12:21", "tema": "¿Josacar o Jozabad? El primero de los asesinos de Joás (2 R 12:21)",
        "lecturas": [
            {"testigos": ["leningrado"], "texto_original": hebreo["2R 12:21"]["t"],
             "traduccion_es": ("Y Jozabad hijo de Simat y Jozabad hijo de Somer, sus siervos, lo hirieron, y murió; y lo sepultaron con sus padres en la ciudad "
                               "de David, y reinó Amasías su hijo en su lugar (traducción propia, literal; en el TM es 12:22)."),
             "nota": ("El Códice de Leningrado (WLC; el UXLC tiene las mismas letras, comprobado al generar) escribe «וְיוֹזָבָד», «Jozabad», también para el "
                      "primero de los dos siervos. La RV1909 lee «Josachâr», que no es la lectura de este códice.")},
            {"testigos": ["vaticano"], "texto_original": m1221.group(0) if m1221 else "",
             "traduccion_es": "Iezeijar hijo de Iemuat (traducción propia; transcripción del griego).",
             "nota": "Texto de la edición de Swete (Códice Vaticano): el primer nombre termina en «-χάρ», como el «Josachâr» de la RV1909, no en «-bad»."},
        ],
        "fuente": "Comparación directa de las ediciones: WLC (OSHB), UXLC y Swete (LXX-Swete-1930).",
        "url_fuente": "https://github.com/eliranwong/LXX-Swete-1930",
        "nota": ("Texto: los nombres se comprueban al generar. Qué manuscrito hebreo o edición siguió la RV1909 aquí no está en los datos de esta app y no se "
                 "dice. Ningún rollo de los datos de Abegg conserva 2 R 12."),
    }]

    # ---- videos
    ruta_oe = CACHE / "oembed.json"
    cache_oe = json.loads(ruta_oe.read_text(encoding="utf-8")) if ruta_oe.exists() else {}
    videos, vistos_oe = [], {}
    for lib, vid, titulo, rango, cert in VIDEOS:
        r = vistos_oe[vid] if vid in vistos_oe else oembed(vid, sin_red, cache_oe)     # un mismo id (1-2 Reyes) se comprueba una vez
        vistos_oe[vid] = r
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
        nh += sum(1 for r in hebreo_sin_texto if r.startswith(lib + " "))
        if nh != conteo_rv[lib]:
            fallo(f"{lib}: hebreo {nh} versículos frente a RV {conteo_rv[lib]}")
    for rv_r, he_r in (("Gn 31:55", "Gn 32:1"), ("Ex 8:1", "Ex 7:26"), ("Ex 8:4", "Ex 7:29"), ("Ex 22:1", "Ex 21:37"),
                       ("Gn 32:1", "Gn 32:2"), ("Ex 8:5", "Ex 8:1"), ("Ex 22:2", "Ex 22:1"),
                       ("Lv 6:1", "Lv 5:20"), ("Lv 6:7", "Lv 5:26"), ("Lv 6:8", "Lv 6:1"), ("Lv 6:30", "Lv 6:23"),
                       ("Lv 5:19", None), ("Lv 7:1", None),
                       ("Nm 12:15", None), ("Nm 13:1", "Nm 12:16"), ("Nm 13:2", "Nm 13:1"), ("Nm 13:32", "Nm 13:31"), ("Nm 13:33", "Nm 13:32-33"),
                       ("Nm 16:35", None), ("Nm 16:36", "Nm 17:1"), ("Nm 16:50", "Nm 17:15"), ("Nm 17:1", "Nm 17:16"), ("Nm 17:13", "Nm 17:28"),
                       ("Nm 25:18", None), ("Nm 26:1", "Nm 25:19-26:1"), ("Nm 26:2", None), ("Nm 29:39", None), ("Nm 30:1", None),
                       ("Nm 30:15", None), ("Nm 30:16", "Nm 30:16-17"),
                       ("Dt 12:31", None), ("Dt 12:32", "Dt 13:1"), ("Dt 13:1", "Dt 13:2"), ("Dt 13:18", "Dt 13:19"), ("Dt 14:1", None),
                       ("Dt 22:29", None), ("Dt 22:30", "Dt 23:1"), ("Dt 23:25", "Dt 23:26"), ("Dt 24:1", None),
                       ("Dt 28:68", None), ("Dt 29:1", "Dt 28:69"), ("Dt 29:2", "Dt 29:1"), ("Dt 29:29", "Dt 29:28"), ("Dt 30:1", None),
                       ("Jue 14:17", None), ("Jue 14:18", "Jue 14:18a"), ("Jue 14:19", "Jue 14:18b"), ("Jue 14:20", "Jue 14:19-20"), ("Jue 15:1", None),
                       ("1S 20:41", None), ("1S 20:42", "1S 20:42-21:1"), ("1S 21:1", "1S 21:2"), ("1S 21:15", "1S 21:16"), ("1S 22:1", None),
                       ("1S 23:28", None), ("1S 24:1", None), ("1S 24:2", None), ("1S 24:21", None), ("1S 24:22", "1S 24:22-23"), ("1S 25:1", None),
                       ("2S 18:32", None), ("2S 18:33", "2S 19:1"), ("2S 19:1", "2S 19:2"), ("2S 19:43", "2S 19:44"), ("2S 20:1", None),
                       ("2S 20:24", None), ("2S 20:25", "2S 20:25-26"), ("2S 21:1", None),
                       ("1R 4:20", None), ("1R 4:21", "1R 5:1"), ("1R 4:34", "1R 5:14"), ("1R 5:1", "1R 5:15"), ("1R 5:18", "1R 5:32"),
                       ("1R 6:1", None), ("1R 22:42", None), ("1R 22:43", None), ("1R 22:44", None), ("1R 22:52", None), ("1R 22:53", "1R 22:53-54"),
                       ("2R 11:20", None), ("2R 11:21", "2R 12:1"), ("2R 12:1", "2R 12:2"), ("2R 12:21", "2R 12:22"), ("2R 13:1", None)):
        if renum_h.get(rv_r) != he_r:
            fallo(f"numeración: RV {rv_r} debería ser hebreo {he_r}, es {renum_h.get(rv_r)}")
    for r in ("Nm 12:16", "Nm 29:40", "1S 23:29", "2S 20:26"):          # vacíos en la RV: ni hebreo ni griego ni «sin_texto»
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
    # Jueces: la digitalización de Swete trae una sola forma del texto (la que imprime Swete, «B»), con la misma numeración que el TM.
    jue_gr = {k for k in gr if k[0] == "Jue"}
    if jue_gr != {k for k in orden_rv if k[0] == "Jue"}:
        fallo(f"Swete Jueces: se esperaban los mismos {conteo_rv['Jue']} versículos que la RV; hay {len(jue_gr)}")
    if {k for k in gr if k[0] == "Rut"} != {k for k in orden_rv if k[0] == "Rut"}:
        fallo("Swete Rut: se esperaban los mismos versículos que la RV")
    ex15 = griego.get("Ex 1:5", "")
    if not ("πέντε" in ex15 or "ἑβδομήκοντα πέντε" in ex15):
        fallo("Ex 1:5 griego")

    if FALLOS:
        print(f"\n{len(FALLOS)} verificaciones fallidas; no se escriben los archivos.")
        sys.exit(1)

    # ---- escribir
    # La app normaliza el libro «Rut» de biblia.js a su id canónico «Rt» (CANON de app.js) y busca hebreo y griego por la clave exacta
    # «Rt 1:1»: aquí las referencias de Rut salen con «Rt». (biblia.js sigue con «Rut»; parseRef de la app acepta los dos.)
    def rt(x):
        return re.sub(r"^Rut (?=\d)", "Rt ", x) if isinstance(x, str) else x

    def rt_claves(d):
        return {rt(k): ({**v, "r": rt(v["r"])} if isinstance(v, dict) and "r" in v else v) for k, v in d.items()}
    hebreo, hebreo_notas, hebreo_sin_texto = rt_claves(hebreo), rt_claves(hebreo_notas), rt_claves(hebreo_sin_texto)
    griego, ref_griega = rt_claves(griego), {rt(k): rt(v) for k, v in ref_griega.items()}
    notas_griego, sin_griego, griego_sin_asignar = rt_claves(notas_griego), rt_claves(sin_griego), [rt(x) for x in griego_sin_asignar]
    for t in testigos:
        t["contiene"] = [re.sub(r"(^|-)Rut (?=\d)", r"\1Rt ", x) for x in t["contiene"]]
    for v in variantes:
        v["ref"] = rt(v["ref"])
    for v in videos:
        v["rango"] = re.sub(r"(^|-)Rut (?=\d)", r"\1Rt ", v["rango"])
        v["libro"] = "Rt" if v["libro"] == "Rut" else v["libro"]
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    orig = {
        "generado": ahora,
        "fuentes": FUENTES,
        "hebreo_nota": ("Texto hebreo del Códice de Leningrado (WLC 4.20) con vocales y acentos; sin morfología, notas ni marcas de párrafo (פ/ס). "
                        "Clave = referencia en numeración RV1909; «r» = referencia hebrea cuando difiere (correspondencia del TVTMS, CC BY 4.0); «14:18a»/«14:18b» = primera o segunda parte de ese versículo hebreo (Jue 14:18-19 RV, ver «hebreo_notas»). Rut va con el id de la app, «Rt» (p. ej. «Rt 1:1»); 1 Samuel, con «1S» (p. ej. «1S 1:1»); 2 Samuel, con «2S»; 1 Reyes, con «1R»; 2 Reyes, con «2R» (11:21 y 12:1-21 RV = 12:1-22 TM)."),
        "hebreo": hebreo,
        "hebreo_notas": hebreo_notas,
        "hebreo_sin_texto": hebreo_sin_texto,
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
        "nota": ("Clave = referencia RV1909. Swete numera como la LXX, que en Gn 2, Gn 5, Ex 20, 21, 25, 28 y 35–40, Lv 7, Nm 1, 13 y 30, Dt 5 y 14 y Jos 8–10 y 13 y 1 S 20 difiere de la RV (en Jue 14:18-20 es la RV la que parte y une versículos; en 1 S 23–24 la RV numera como el hebreo; en 2 S 20:25 la RV reúne 20:25-26): "
                 "la correspondencia se toma del TVTMS (STEPBible, CC BY 4.0), eligiendo en cada bloque la columna griega cuyos TEST cumple esta edición. "
                 "«ref_griega» da la referencia de Swete cuando difiere; «sin_texto» lista los versículos RV sin equivalente completo en la LXX, con el motivo. Jueces: la LXX tiene dos formas textuales (A, Alejandrino; B, Vaticano); "
                 "la digitalización de Swete trae solo la que imprime Swete, la del Códice Vaticano («B»), y es la única que se muestra: no se mezcla con «A». 1 Samuel (1 Reinos en la LXX): el texto de Swete es más breve que el TM (13:1, 1 S 17–18, 20:16 y 23:12 van en «sin_texto»). 2 Samuel (2 Reinos): Swete numera como la RV; el Vaticano perdió 2:5-7 y 2:10-13 (ver «notas»). 1 Reyes (3 Reinos): la LXX ordena y numera distinto 4–7, 10, 11:4-8 y los capítulos 20 y 21 (correspondencia por contenido, ver «notas»); "
                 "los versículos que no tiene en su sitio van en «sin_texto», y los bloques que añade con letra (2:35a-o, 2:46a-l, 5:14a-b, 6:1a-d, 6:36a, 8:53a, 9:9a, 10:22a-c, 10:26a, 12:24a-z, 16:28a-h en la numeración de Brenton), "
                 "que no tienen paralelo en el hebreo ni en la RV1909, en «bloques_sin_paralelo» (ref_swete; tras = versículo RV tras el que van; texto; nota). 2 Reyes (4 Reinos): la digitalización numera como la RV1909 (también 11:21 y 12:1-21, que en el TM y en Brenton son 12:1-22); 25:10 está vacío («sin_texto») y el bloque que añade tras 1:18 (1:18a-d en Brenton) va en «bloques_sin_paralelo»."),
        "texto": griego,
        "ref_griega": ref_griega,
        "notas": notas_griego,
        "sin_texto": sin_griego,
        "griego_sin_asignar": griego_sin_asignar,
        "bloques_sin_paralelo": bloques_1r + bloques_2r,
    }
    cab_g = ("// LXX de Swete (1930) por versículo. Digitalización: LXX-Swete-1930 (Eliran Wong), licencia GNU GPL-3.0.\n"
             "// Este archivo se distribuye bajo la GPL-3.0: ver datos/LICENCIA-griego-swete.txt y https://www.gnu.org/licenses/gpl-3.0.html\n"
             "// El texto impreso de Swete es de dominio público. Generado por herramientas/originales.py; no editar a mano.\n")
    t2 = escribir_js(DATOS / "griego-swete.js", cab_g, "BIBLIA_GRIEGO", griego_obj)
    lic = obtener("swete_lic", sin_red).read_text(encoding="utf-8")
    (DATOS / "LICENCIA-griego-swete.txt").write_text(
        "datos/griego-swete.js — Septuaginta de Swete (Génesis, Éxodo, Levítico, Números, Deuteronomio, Josué, Jueces, Rut, 1 Samuel, 2 Samuel, 1 Reyes y 2 Reyes)\n\n"
        "Texto: H. B. Swete, The Old Testament in Greek according to the Septuagint, Cambridge University Press (ed. 1930). Dominio público.\n"
        "Digitalización: LXX-Swete-1930, Eliran Wong (https://github.com/eliranwong/LXX-Swete-1930), licencia GNU GPL-3.0.\n"
        "Modificaciones: palabras unidas por versículo y claves pasadas a la numeración de la RV1909 con el TVTMS (STEPBible, CC BY 4.0).\n"
        "El archivo griego-swete.js se distribuye bajo la misma GPL-3.0; el resto de la app no deriva de él.\n"
        "Texto de la licencia: https://www.gnu.org/licenses/gpl-3.0.html (copia íntegra a continuación, tomada del repositorio de origen).\n\n"
        + "=" * 72 + "\n\n" + lic, encoding="utf-8")

    # ---- resumen
    print("Conteos RV:", conteo_rv)
    for lib in LIBROS:
        lb = "Rt" if lib == "Rut" else lib
        print(f"  {lib}: hebreo {sum(1 for r in hebreo if r.startswith(lb + ' '))}, "
              f"griego {sum(1 for r in griego if r.startswith(lb + ' '))}, sin griego {sum(1 for r in sin_griego if r.startswith(lb + ' '))}")
    print("Rut: ketiv/qere", n_kq, "· notas hebreas de Rut", sorted(k for k in hebreo_notas if k.startswith("Rt ")))
    print("1 S: ketiv/qere", n_kq_1s, "en", len(kq1), "versículos · sin griego", len([r for r in sin_griego if r.startswith("1S ")]),
          "· 4Q51 capítulos", caps51, "· extremos de proporción", extremos_1s)
    print("2 S: ketiv/qere", n_kq_2s, "en", len(kq2), "versículos · sin griego", len([r for r in sin_griego if r.startswith("2S ")]),
          "· 4Q51 capítulos", caps51_2s, "· extremos de proporción", extremos_2s,
          "· variantes", [v["ref"] for v in variantes if v["ref"].startswith("2S ")])
    print("1 R: ketiv/qere", n_kq_1r, "en", len(kq3), "versículos · sin griego", len([r for r in sin_griego if r.startswith("1R ")]),
          "· rollos", con_1r, "· bloques sin paralelo", [b["brenton"] for b in bloques_1r], "· extremos de proporción", extremos_1r,
          "· TVTMS sin columna para Swete", bloques_sin_col_1r, "· variantes", [v["ref"] for v in variantes if v["ref"].startswith("1R ")])
    print("2 R: ketiv/qere", n_kq_2r, "en", len(kq4), "versículos · sin griego", [r for r in sin_griego if r.startswith("2R ")],
          "· rollos", con_2r, "· 6Q4 capítulos", caps_6q4, "· bloques sin paralelo", [b["brenton"] for b in bloques_2r],
          "· extremos de proporción", extremos_2r, "· variantes", [v["ref"] for v in variantes if v["ref"].startswith("2R ")])
    print("Renumeración hebrea (RV -> TM):", len(renum_h), "versículos; casos:",
          {k: renum_h[k] for k in ("Gn 31:55", "Ex 8:1", "Ex 8:4", "Ex 22:1")})
    print("Griego con referencia distinta:", len(ref_griega), "· griego sin asignar:", len(griego_sin_asignar))
    print("Ex 1:5 heb:", heb_cons("Ex 1:5")[-30:], "| gr:", m_gr15.group(0) if m_gr15 else None, "| 4Q13:", l13)
    print(f"Testigos: {len(testigos)} ({len(CODICES)} códices y papiros, {len(ROLLOS)} rollos) · variantes: {len(variantes)} · videos: {len(videos)}")
    print(f"Escritos: originales.js {t1/1e6:.2f} MB, griego-swete.js {t2/1e6:.2f} MB, LICENCIA-griego-swete.txt")
    print("Verificación: OK")


if __name__ == "__main__":
    main()
