"""Manuscritos: el registro real de donde sale el texto de cada pasaje (Gn, Ex, Lv, Nm, Dt, Jos, Jue, Rut, 1 S, 2 S, 1 R, 2 R).

Genera:
  datos/manuscritos.js     window.BIBLIA_MANUSCRITOS
    leningrado  folios del Códice de Leningrado en Wikimedia Commons (imagen en línea si la licencia es abierta)
    rollos      imágenes de la Leon Levy Dead Sea Scrolls Digital Library (solo enlace: la IAA no permite mostrarlas)
    vaticano    página donde empieza cada libro en el Códice Vaticano (solo enlace: la BAV no permite mostrarlas)

Uso:  python -I herramientas/manuscritos.py [--sin-red] [--autoprueba]
Solo biblioteca estándar. Descarga a herramientas/cache/manuscritos/ lo que falte (con pausas);
--sin-red usa solo la caché. --autoprueba corre el fixture herramientas/manuscritos/_prueba/fixture.json
(debe pasar) y sus copias alteradas (deben fallar) y no escribe nada.
Sale con código != 0 si falla cualquier verificación, y entonces no escribe nada.
Documentación: datos/LEEME.md, sección «Manuscritos: el registro real».

Reutiliza de herramientas/originales.py (solo se importa): la caché del WLC (OSHB) para la lista de
versículos hebreos, los datos de Abegg (ETCBC/dss) y la tabla de rollos. La correspondencia
hebreo -> RV se lee de datos/originales.js (campo «r», que sale del TVTMS).
"""
import copy
import importlib.util
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
HERR = RAIZ / "herramientas"
CACHE = HERR / "cache" / "manuscritos"
DATOS = RAIZ / "datos"
FIXTURE = HERR / "manuscritos" / "_prueba" / "fixture.json"
UA = {"User-Agent": "biblia-datos/1.0 (lectura de metadatos, uso no comercial)"}
HOY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

LIBROS = ("Gn", "Ex", "Lv", "Nm", "Dt", "Jos", "Jue", "Rut", "1S", "2S", "1R", "2R")

# ------------------------------------------------------------------ Leningrado (Commons)
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
CATEGORIAS = ("001-100", "101-200", "201-300", "401-491")   # Gn–2 S en 1b–184a; 1 R desde 184a; 2 R en 202b–220b; Rut en 421a–423a
LIBRO_EN = {"Genesis": "Gn", "Exodus": "Ex", "Leviticus": "Lv", "Numbers": "Nm", "Deuteronomy": "Dt",
            "Joshua": "Jos", "Judges": "Jue", "Ruth": "Rut", "1 Samuel": "1S", "2 Samuel": "2S", "1 Kings": "1R", "2 Kings": "2R"}
LICENCIA_ABIERTA = re.compile(r"^(Public domain|PD\b|CC0|CC BY(-SA)? \d)")
ANCHO_MINIATURA = 1280

# ------------------------------------------------------------------ Leon Levy
LL_API = "https://www.deadseascrolls.org.il/api/search?t=image&q={q}&p={p}"
LL_IMAGEN = "https://www.deadseascrolls.org.il/explore-the-archive/image/"
FOTO_COLOR = "Full Spectrum Color Image"
FOTO_IR = ("Infrared Image", "Scanned Infrared Negative")
# Muestra comprobada a mano (imagen de la Leon Levy abierta solo para verificar, comparada con el texto de Abegg).
# El script exige que cada una siga enlazada a nivel de fragmento con la misma imagen.
MUESTRA_VERIFICADA = {   # (rollo, fragmento de Abegg): (imagen LL, qué se comprobó el 2026-11-13; la página pública dice «<rollo> Plate N Frag 1»)
    ("4Q49", "f1"): ("B-360503", "Jue 6:2-13: se lee «שה שור» (Abegg, línea 3) y el texto conservado está a la derecha de las líneas, como en Abegg."),
    ("4Q19", "f1"): ("B-472329", "Ex 6:3-6: se leen «מעבידים אותם» y «אתכם מתח[ת]» (Abegg, líneas 3 y 4)."),
    ("2Q1", "f1"): ("B-482966", "Gn 19:27-28: se lee «ועמרה» al final de la línea 3 de Abegg; solo dos líneas con letras, como en Abegg."),
    ("4Q12", "f1"): ("B-367578", "Gn 26:21-28 (4QpaleoGen-m): escritura paleohebrea y ocho líneas con el final conservado a la izquierda, "
                                 "como en Abegg; no leí palabras sueltas."),
    ("2Q5", "f1"): ("B-366043", "Lv 11:22-29 (2QpaleoLev): escritura paleohebrea, nueve líneas con el final conservado junto al margen "
                                "izquierdo cosido, como en Abegg; no leí palabras sueltas."),
}

# ------------------------------------------------------------------ Vaticano
VAT_MANIFIESTO = "https://digi.vatlib.it/iiif/MSS_Vat.gr.1209/manifest.json"
VAT_VISOR = "https://digi.vatlib.it/view/MSS_Vat.gr.1209/"
VAT_LIBRO = {"Genesis": "Gn", "Exodus": "Ex", "Leviticus": "Lv", "Numeri": "Nm", "Deuteronomium": "Dt",
             "Iosue": "Jos", "Iudicum": "Jue", "Ruth": "Rut", "Samuelis I": "1S", "Samuelis II": "2S", "Regum I": "1R", "Regum II": "2R"}
# Diferencias entre el rótulo del catálogo («p. 47-99 Exodus») y la primera imagen que el manifiesto
# pone en ese tramo, revisadas a mano. Se usa la página del rótulo solo si está aquí.
VAT_REVISADO = {
    "Ex": ("El manifiesto IIIF pone en el tramo «p. 47-99 Exodus» las imágenes desde la p. 43 (0047), dentro de Génesis. "
           "Revisado a mano el 2026-11-13: la p. 46 (0050) acaba Génesis con la suscripción «ΓΕΝΕΣΙΣ» y la p. 47 (0051) "
           "lleva arriba «ἔξοδος» y empieza «ΤΑΥΤΑ ΤΑ ΟΝΟΜΑΤΑ» (Ex 1:1). Se enlaza la p. 47, la del rótulo."),
}
VAT_NOTA = {
    "Gn": "En el Códice Vaticano, Gn 1:1–46:28 es una reposición del siglo XV (ver el testigo «vaticano»); estas páginas no son del siglo IV.",
    "Ex": VAT_REVISADO["Ex"],
    "Rut": "Rut empieza en la misma página en que acaba Jueces (p. 304, según el rótulo del catálogo; no revisado a mano).",
    "1S": ("En la Septuaginta, 1 Samuel es «1 Reinos» (Βασιλειῶν Α). Revisado a mano el 2026-11-13: la p. 309 (0313) acaba Rut "
           "(genealogía y suscripción «ΡΟΥΘ») y empieza «ΑΝΘΡΩΠΟΣ ΗΝ ΕΞ ΑΡΜΑΘΑΙΜ» (1 S 1:1) bajo el título «Βασιλειῶν α»."),
    "2S": ("En la Septuaginta, 2 Samuel es «2 Reinos» (Βασιλειῶν Β). Revisado a mano el 2026-11-13: la p. 353 (0357) acaba 1 Reinos "
           "con «ΚΑΙ ΕΓΕΝΕΤΟ ΜΕΤΑ ΤΟ ΑΠΟΘΑΝΕΙΝ ΣΑΟΥΛ … ΕΝ ΣΕΚΕΛΑΚ ΗΜΕΡΑΣ ΔΥΟ» (el texto de 2 S 1:1) y la suscripción «ΒΑΣΙΛΕΙΩΝ Α»; "
           "la p. 354 (0358) lleva arriba «Βασιλειῶν β» y empieza, con inicial grande, «ΚΑΙ ΕΓΕΝΕΤΟ ΜΕΤΑ ΤΟ ΑΠΟΘΑΝΕΙΝ ΣΑΟΥΛ» (2 S 1:1, "
           "que así sale dos veces). Se enlaza la p. 354, la del rótulo. Este códice perdió 2 S 2:5-7 y 2:10-13 (hoja 178 rota, según la "
           "Introducción de Swete; ver el testigo «vaticano»)."),
    "1R": ("En la Septuaginta, 1 Reyes es «3 Reinos» (Βασιλειῶν Γ); el catálogo lo rotula «Regum I». Revisado a mano el 2026-11-13: "
           "la p. 394 (0398) acaba 2 Reinos con «… ΚΑΙ ΠΡΟΣΕΘΗΚΕ ΣΑΛΩΜΩΝ ΕΠΙ ΤΟ ΘΥΣΙΑΣΤΗΡΙΟΝ …» (el final que la LXX da a 2 S 24:25) y deja "
           "en blanco el resto de la tercera columna; la p. 395 (0399) lleva arriba «Βασιλειων γ», una banda de adorno y empieza, con inicial "
           "grande, «ΚΑΙ Ο ΒΑΣΙΛΕΥΣ ΔΑΥΕΙΔ ΠΡΕΣΒΥΤΕΡΟΣ ΠΡΟΒΕΒΗΚΩΣ ΗΜΕΡΑΙΣ» (1 R 1:1). Se enlaza la p. 395, la del rótulo."),
    "2R": ("En la Septuaginta, 2 Reyes es «4 Reinos» (Βασιλειῶν Δ); el catálogo lo rotula «Regum II». Revisado a mano el 2026-11-13: "
           "4 Reinos empieza en la misma página en que acaba 3 Reinos, la p. 442 (0446), que lleva arriba «Βασιλειων δ». La primera columna "
           "acaba 3 Reinos con «… ΚΑΙ ΗΘΕΤΗΣΕΝ ΜΩΑΒ ΕΝ ΙΣΡΑΗΛ ΜΕΤΑ ΤΟ ΑΠΟΘΑΝΕΙΝ ΑΧΑΑΒ» (el texto de 2 R 1:1) y la suscripción «ΒΑΣΙΛΕΙΩΝ Γ»; "
           "la segunda empieza, bajo una banda de adorno y con inicial grande, «ΚΑΙ ΗΘΕΤΗΣΕΝ ΜΩΑΒ ΕΝ ΙΣΡΑΗΛ ΜΕΤΑ ΤΟ ΑΠΟΘΑΝΕΙΝ ΑΧΑΑΒ ΚΑΙ ΕΠΕΣΕΝ "
           "ΟΧΟΖΕΙΑΣ ΔΙΑ ΤΟΥ ΔΙΚΤΥΩΤΟΥ» (2 R 1:1-2; 1:1 sale así dos veces). Se enlaza la p. 442, la del rótulo."),
}

FALLOS = []
AVISOS = []


def fallo(msg):
    FALLOS.append(msg)
    print("FALLO:", msg)


def aviso(msg):
    AVISOS.append(msg)
    print("Aviso:", msg)


# ------------------------------------------------------------------ utilidades
def cargar_originales_py():
    spec = importlib.util.spec_from_file_location("originales", HERR / "originales.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def leer_js(nombre):
    s = (DATOS / nombre).read_text(encoding="utf-8")
    return json.loads(s[s.index("{"):s.rindex("}") + 1])


def pedir_json(url, sin_red, ruta, pausa=1.5):
    """JSON con caché en `ruta`. Con red, si la caché existe se usa (como originales.py)."""
    if ruta.exists():
        return json.loads(ruta.read_text(encoding="utf-8"))
    if sin_red:
        sys.exit(f"Falta {ruta} y se pidió --sin-red")
    ultimo, espera = None, pausa
    for intento in range(6):
        try:
            time.sleep(espera)
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read().decode("utf-8"))
            CACHE.mkdir(parents=True, exist_ok=True)
            ruta.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
            return d
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            ultimo = e
            espera = pausa * (intento + 2)
            if isinstance(e, urllib.error.HTTPError) and e.code == 429:      # demasiadas peticiones: esperar más
                ra = e.headers.get("Retry-After", "")
                espera = max(int(ra) if ra.isdigit() else 0, 20 * (intento + 1))
                print(f"  429 en {url[:80]}…: espero {espera} s")
    sys.exit(f"No se pudo leer {url}: {ultimo}")


def ref(k):
    return f"{k[0]} {k[1]}:{k[2]}"


def parse_ref(s):
    m = re.fullmatch(r"(\S+) (\d+):(\d+)", s.strip())
    return (m[1], int(m[2]), int(m[3])) if m else None


def comprimir(claves, orden_idx, orden):
    idx = sorted({orden_idx[k] for k in claves})
    out, ini, prev = [], None, None
    for i in idx + [None]:
        if ini is not None and (i is None or i != prev + 1):
            a, b = orden[ini], orden[prev]
            out.append(ref(a) if a == b else ref(a) + "-" + ref(b))
            ini = None
        if i is not None and ini is None:
            ini = i
        prev = i
    return out


def miniatura(u):
    """thumburl de Commons sin parámetros de seguimiento y en upload.wikimedia.org (mismo camino /thumb/)."""
    u = u.split("?")[0]
    return re.sub(r"^https://thumb\.wikimedia\.org/", "https://upload.wikimedia.org/", u)


def sin_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def escribir_js(ruta, cabecera, var, obj):
    txt = cabecera + "window.%s = " % var + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + ";\n"
    for intento in range(6):
        try:
            ruta.write_text(txt, encoding="utf-8")
            break
        except OSError as e:
            if e.errno != 22 or intento == 5:
                raise
            time.sleep(1 + intento)
    return len(txt.encode("utf-8"))


# ------------------------------------------------------------------ contexto: RV, hebreo y su correspondencia
def contexto_textos(orig, sin_red):
    """orden RV, pasajes, orden hebreo por libro y hebreo -> [RV]."""
    bib = leer_js("biblia.js")
    rv_orden = [(c["libro"], c["cap"], v["n"]) for c in bib["capitulos"] for v in c["versiculos"]]
    pasajes = [(p["id"], parse_ref(p["inicio"]), parse_ref(p["fin"])) for p in bib["pasajes"]]
    ori = leer_js("originales.js")
    norm = lambda s: re.sub(r"^Rt ", "Rut ", s)
    heb_orden = {}
    claves_oshb = {"Gn": "oshb_gen", "Ex": "oshb_exo", "Lv": "oshb_lev", "Nm": "oshb_num", "Dt": "oshb_deu",
                   "Jos": "oshb_jos", "Jue": "oshb_jue", "Rut": "oshb_rut", "1S": "oshb_1s", "2S": "oshb_2s", "1R": "oshb_1r", "2R": "oshb_2r"}
    for lib, clave in claves_oshb.items():
        heb_orden[lib] = list(orig.leer_oshb(orig.obtener(clave, sin_red), lib))
    heb_idx = {k: (lib, i) for lib, l in heb_orden.items() for i, k in enumerate(l)}
    heb_a_rv = {}
    for k_rv, v in ori["hebreo"].items():
        krv = parse_ref(norm(k_rv))
        r = re.sub(r"(\d)[ab]$", r"\1", norm(v.get("r", k_rv)))     # «Jue 14:18a/b»: medio versículo hebreo
        if "-" in r:
            a, b = r.split("-")
            ka = parse_ref(a)
            if ":" in b:                                 # «Nm 25:19-26:1»
                c, vv = b.split(":")
                kb = (ka[0], int(c), int(vv))
            else:                                        # «Nm 13:32-33»
                kb = (ka[0], ka[1], int(b))
            lib, ia = heb_idx[ka]
            _, ib = heb_idx[kb]
            hs = heb_orden[lib][ia:ib + 1]
        else:
            hs = [parse_ref(r)]
        for h in hs:
            if h not in heb_idx:
                fallo(f"hebreo: {ref(h)} (de {k_rv}) no está en el WLC")
                continue
            heb_a_rv.setdefault(h, []).append(krv)
    sin_texto = {parse_ref(norm(k)) for k in ori["hebreo_sin_texto"]}
    rv_vacios = {(c["libro"], c["cap"], v["n"]) for c in bib["capitulos"] for v in c["versiculos"] if not v["texto"].strip()}
    return {"rv_orden": rv_orden, "pasajes": pasajes, "heb_orden": heb_orden, "heb_a_rv": heb_a_rv,
            "sin_texto": sin_texto, "rv_vacios": rv_vacios, "testigos": ori["testigos"]}


# ------------------------------------------------------------------ Leningrado
def leer_commons(sin_red):
    """{título: imageinfo} de las categorías de folios en color."""
    paginas = {}
    for cat in CATEGORIAS:
        cont, n = {}, 0
        while True:
            p = {"action": "query", "format": "json", "generator": "categorymembers",
                 "gcmtitle": "Category:Leningrad Codex, color JPG images " + cat, "gcmtype": "file", "gcmlimit": "50",
                 "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": str(ANCHO_MINIATURA),
                 "iiextmetadatafilter": "ImageDescription|LicenseShortName|LicenseUrl|UsageTerms|Artist|Credit|AttributionRequired|Copyrighted"}
            p.update(cont)
            d = pedir_json(COMMONS_API + "?" + urllib.parse.urlencode(p), sin_red, CACHE / f"commons_{cat}_{n:02d}.json")
            for pg in d.get("query", {}).get("pages", {}).values():
                if pg.get("imageinfo"):
                    paginas[pg["title"]] = pg["imageinfo"][0]
            if "continue" not in d:
                break
            cont = {k: v for k, v in d["continue"].items()}
            n += 1
    return paginas


REF_EN = r"((?:[12] )?[A-Z][a-z]+(?: of [A-Z][a-z]+)*) (\d+):(\d+)"


def parse_descripcion(desc):
    """'… showing Genesis 14:12–15:13.' -> ((libro_en, c, v), (libro_en, c, v)) o None."""
    m = re.search(r"showing (.+?)\.?\s*$", desc)
    if not m:
        return None
    s = m[1].replace("–", "-").replace("—", "-").strip()
    s = re.sub(r"\s+followed by .*$", "", s)           # «Deuteronomy 34:1–12 followed by a Masoretic list»
    s = re.sub(r"^to ", "", s)                          # «showing to Ruth 1:17–2:14» (errata de Commons en 421b–423a)
    m = re.fullmatch(REF_EN + r" to " + REF_EN, s)
    if m:
        return (m[1], int(m[2]), int(m[3])), (m[4], int(m[5]), int(m[6]))
    m = re.fullmatch(REF_EN + r"\s*-\s*(\d+):(\d+)", s)
    if m:
        return (m[1], int(m[2]), int(m[3])), (m[1], int(m[4]), int(m[5]))
    m = re.fullmatch(REF_EN + r"\s*-\s*(\d+)", s)
    if m:
        return (m[1], int(m[2]), int(m[3])), (m[1], int(m[2]), int(m[4]))
    m = re.fullmatch(REF_EN, s)
    if m:
        return (m[1], int(m[2]), int(m[3])), (m[1], int(m[2]), int(m[3]))
    return None


def tramo_hebreo(a, b, heb_orden):
    """Versículos hebreos de nuestros libros entre a y b (nombres en inglés). Libro ajeno = fuera."""
    la, lb = LIBRO_EN.get(a[0]), LIBRO_EN.get(b[0])
    out = []
    for lib, ini, fin in ((la, a, None), (lb, None, b)) if la != lb else ((la, a, b),):
        if lib is None:
            continue
        l = heb_orden[lib]
        i = l.index((lib,) + ini[1:]) if ini else 0
        j = l.index((lib,) + fin[1:]) if fin else len(l) - 1
        out += l[i:j + 1]
    return out


def construir_leningrado(paginas, ctx):
    heb_orden, heb_a_rv = ctx["heb_orden"], ctx["heb_a_rv"]
    rv_orden = ctx["rv_orden"]
    rv_idx = {k: i for i, k in enumerate(rv_orden)}
    folios, por_rv, previo = {}, {}, {}
    nombres = sorted(paginas)
    for titulo in nombres:
        m = re.fullmatch(r"File:Leningrad Codex Folio (\d{3}[ab])\.jpg", titulo)
        if not m:
            continue
        info = paginas[titulo]
        meta = info.get("extmetadata", {})
        desc = sin_html(meta.get("ImageDescription", {}).get("value", ""))
        if " showing " not in desc or not any(re.search(r"\b" + re.escape(n) + r" \d", desc.split(" showing ", 1)[1]) for n in LIBRO_EN):
            continue                                     # folio sin texto de nuestros libros (o cubierta, como 474a)
        tramo = parse_descripcion(desc)
        if not tramo:
            fallo(f"Leningrado {m[1]}: no entiendo la descripción «{desc}»")
            continue
        try:
            hs = tramo_hebreo(*tramo, heb_orden)
        except ValueError:
            fallo(f"Leningrado {m[1]}: la descripción cita un versículo que no está en el WLC: «{desc}»")
            continue
        if not hs:
            continue
        lib0 = hs[0][0]
        if lib0 in previo:                               # continuidad con el folio anterior del mismo libro
            ult = previo[lib0]
            i_ult, i_ini = heb_orden[lib0].index(ult), heb_orden[lib0].index(hs[0])
            if i_ini not in (i_ult, i_ult + 1):
                fallo(f"Leningrado {m[1]}: empieza en {ref(hs[0])} pero el folio anterior acaba en {ref(ult)}")
        for h in hs:
            previo[h[0]] = h
        rvs = []
        for h in hs:
            rvs += heb_a_rv.get(h, [])
        lic = sin_html(meta.get("LicenseShortName", {}).get("value", ""))
        abierta = bool(LICENCIA_ABIERTA.match(lic))
        f = {
            "archivo": titulo,
            "pagina": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(titulo.replace(" ", "_"), safe=":/_"),
            "miniatura": miniatura(info.get("thumburl", "")),
            "ancho_miniatura": info.get("thumbwidth"),
            "alto_miniatura": info.get("thumbheight"),
            "licencia": lic,
            "licencia_url": sin_html(meta.get("LicenseUrl", {}).get("value", "")) or None,
            "autor": sin_html(meta.get("Artist", {}).get("value", "")) or None,
            "credito": sin_html(meta.get("Credit", {}).get("value", "")) or None,
            "uso": "mostrar" if abierta else "solo_enlace",
            "hebreo": ref(hs[0]) + ("" if len(hs) == 1 else "-" + ref(hs[-1])) if hs[0][0] == hs[-1][0]
                      else ref(hs[0]) + "-" + ref(hs[-1]),
            "rv": comprimir(rvs, rv_idx, rv_orden),
        }
        if not abierta:
            aviso(f"Leningrado {m[1]}: licencia «{lic}» no abierta: solo enlace")
        folios[m[1]] = f
        for k in rvs:
            por_rv.setdefault(k, []).append(m[1])
    pasajes = {}
    for pid, a, b in ctx["pasajes"]:
        if a[0] not in LIBROS:
            continue
        vs = rv_orden[rv_idx[a]:rv_idx[b] + 1]
        fs = []
        for k in vs:
            for fo in por_rv.get(k, []):
                if fo not in fs:
                    fs.append(fo)
        pasajes[pid] = sorted(fs)
    sin_folio = [k for k in rv_orden if k[0] in LIBROS and k not in por_rv]
    return {"folios": folios, "pasajes": pasajes}, sin_folio


# ------------------------------------------------------------------ rollos (Abegg + Leon Levy)
def fragmentos_abegg(orig, sin_red):
    """{rollo: {etiqueta_fragmento: set((lib,c,v) hebreo con alguna letra conservada)}}; misma lectura que originales.leer_dss."""
    import bisect
    rutas = {f: orig.obtener("dss_" + f, sin_red) for f in ("otype", "oslots", "scroll", "book", "chapter", "verse", "rec", "fragment", "line")}
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
    book, cap, ver = orig.leer_tf(rutas["book"]), orig.leer_tf(rutas["chapter"]), orig.leer_tf(rutas["verse"])
    scroll, rec, frag = orig.leer_tf(rutas["scroll"]), orig.leer_tf(rutas["rec"]), orig.leer_tf(rutas["fragment"])
    a, z = tipos["fragment"]
    frags = sorted((orig.rango_slots(osl[n]), frag.get(n, ""), scroll.get(n)) for n in range(a, z + 1) if n in osl)
    ini_f = [r[0][0] for r in frags]
    res = {}
    for w, b in book.items():
        if b not in orig.DSS_LIBRO or not ver.get(w, "").isdigit():
            continue
        s0, s1 = orig.rango_slots(osl[w])
        jf = bisect.bisect_right(ini_f, s0) - 1
        if jf < 0 or not frags[jf][0][0] <= s0 <= frags[jf][0][1]:
            continue
        (_, _), fr, sc = frags[jf]
        conservado = any(rec.get(x) != "1" for x in range(s0, s1 + 1))
        d = res.setdefault(sc, {}).setdefault(fr, set())
        if conservado:
            d.add((orig.DSS_LIBRO[b], int(cap[w]), int(ver[w])))
    return res


def numeros_fragmento(etq):
    """Etiqueta de Abegg -> conjunto de números de fragmento, o None si no es numeración de fragmentos.
    'f1' {1}; 'f2_3' {2,3} (tramo); 'f1i' {1} (columna i del fragmento 1); 'f4ii+6' {4,6}.
    Sin «f» (columnas: '1', '10b_c') o con letras ('f1a', 'fA'): None."""
    if not etq.startswith("f"):
        return None
    nums = set()
    for parte in etq[1:].split("+"):
        m = re.fullmatch(r"(\d+)(?:[ivx]+)?(?:_(\d+)(?:[ivx]+)?)?", parte)
        if not m:
            return None
        a, b = int(m[1]), int(m[2] or m[1])
        if b < a:
            return None
        nums.update(range(a, b + 1))
    return nums


def leer_ll(numero, sin_red):
    ruta = CACHE / f"ll_{numero}.json"
    if ruta.exists():
        return json.loads(ruta.read_text(encoding="utf-8"))["resultados"]
    if sin_red:
        sys.exit(f"Falta {ruta} y se pidió --sin-red")
    q = urllib.parse.quote(f"manuscript_numbers:'{numero}'", safe=":'")
    res, p, total = [], 1, 1
    while p <= total:
        d = pedir_json(LL_API.format(q=q, p=p), False, CACHE / "_ll_pagina.json", pausa=2)
        (CACHE / "_ll_pagina.json").unlink()
        res += d.get("results", [])
        total = int(d.get("totalpages") or 0)
        p += 1
    CACHE.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps({"consulta": f"manuscript_numbers:'{numero}'", "consultado": HOY, "resultados": res},
                               ensure_ascii=False), encoding="utf-8")
    return res


def elegir_imagen(imgs):
    """La Full Spectrum Color más reciente; si no hay, la infrarroja más reciente. Recto antes que verso."""
    for tipos in ((FOTO_COLOR,), FOTO_IR):
        cand = [x for x in imgs if x.get("photo_type") in tipos]
        if cand:
            cand.sort(key=lambda x: ((x.get("side") or "") == "Recto", x.get("date") or ""), reverse=True)
            return cand[0]
    return None


def ficha_imagen(x, **extra):
    d = dict(extra)
    d.update({"imagen": x["name"], "tipo_foto": x.get("photo_type"),
              "fecha_foto": (x.get("date") or "")[:10] or None, "lado": x.get("side"),
              "laminas": x.get("plate_numbers") or []})
    return d


def construir_rollos(testigos, rollos_tabla, abegg, ll, ctx):
    """Para cada rollo testigo: nivel 'fragmento' | 'lamina' | 'ficha'."""
    heb_a_rv, rv_orden = ctx["heb_a_rv"], ctx["rv_orden"]
    rv_idx = {k: i for i, k in enumerate(rv_orden)}
    tabla = {}
    for claves, sigla, llid, *_ in rollos_tabla:
        num = claves[0] if len(claves) == 1 else re.match(r"\d+Q\d+", claves[0]).group(0)
        tabla[num] = (claves, llid)
    out = {}
    for t in testigos:
        if t.get("tipo") != "rollo":
            continue
        num = t["id"]
        claves, llid = tabla[num]
        imgs = ll.get(num) or []
        r = {"sigla": t.get("sigla"), "ficha": t.get("url"), "nivel": "ficha", "motivo": "", "laminas": [], "fragmentos": []}
        # láminas: una imagen por lámina y lado
        grupos = {}
        for x in imgs:
            if x.get("content_type") == "Plate":
                grupos.setdefault((tuple(x.get("plate_numbers") or []), x.get("side") or ""), []).append(x)
        for (lams, lado), xs in sorted(grupos.items(), key=lambda g: ([int(p) if p.isdigit() else 10**6 for p in g[0][0]], g[0][1] != "Recto")):
            e = elegir_imagen(xs)
            if e:
                r["laminas"].append(ficha_imagen(e))
        # fragmentos: criterio de cruce
        etqs = {}
        for c in claves:
            for etq, vs in (abegg.get(c) or {}).items():
                etqs.setdefault(etq, set()).update(vs)
        frag_ll = {}
        for x in imgs:
            if x.get("content_type") == "Fragment":
                frag_ll.setdefault(str(x.get("frag_num")), []).append(x)
        A, motivo = set(), ""
        if not imgs:
            motivo = "la Leon Levy no devuelve imágenes de este rollo"
        elif len(claves) > 1:
            motivo = (f"Abegg reparte este rollo en {', '.join(claves)}, que numeran sus fragmentos por separado: "
                      "no se puede saber a cuál corresponde cada número de la Leon Levy")
        for etq in ([] if motivo else etqs):
            n = numeros_fragmento(etq)
            if n is None:
                motivo = f"Abegg numera «{etq}» como columna o con letra, no como fragmento"
                break
            A |= n
        L = set()
        if not motivo:
            if not imgs:
                motivo = "la Leon Levy no devuelve imágenes de este rollo"
            elif not frag_ll:
                motivo = "la Leon Levy no tiene imágenes de fragmentos sueltos de este rollo"
            elif not all(k.isdigit() for k in frag_ll):
                motivo = "la Leon Levy numera algún fragmento con letras"
            else:
                L = {int(k) for k in frag_ll}
                if A != L:
                    motivo = (f"los números de fragmento no coinciden (Abegg {sorted(A)}, Leon Levy {sorted(L)}): "
                              "las dos fuentes no numeran igual")
                else:
                    for k, xs in frag_ll.items():
                        if len({tuple(x.get("plate_numbers") or []) for x in xs}) > 1:
                            motivo = f"el fragmento {k} de la Leon Levy sale en láminas distintas"
                            break
        if not motivo and A:
            r["nivel"] = "fragmento"
            for etq in sorted(etqs, key=lambda e: (min(numeros_fragmento(e)), e)):
                rvs = [k for h in etqs[etq] for k in heb_a_rv.get(h, [])]
                if not rvs:
                    continue                             # fragmento sin letra conservada de un versículo
                imgs_f = []
                for n in sorted(numeros_fragmento(etq)):
                    e = elegir_imagen(frag_ll[str(n)])
                    if e:
                        imgs_f.append(ficha_imagen(e, fragmento_ll=str(n)))
                if not imgs_f:
                    continue
                r["fragmentos"].append({"abegg": etq, "versiculos": comprimir(rvs, rv_idx, rv_orden), "imagenes": imgs_f})
            if not r["fragmentos"]:
                r["nivel"], motivo = "ficha", "ningún fragmento con imagen elegible"
        if r["nivel"] != "fragmento":
            r["motivo"] = motivo or ("sin datos de Abegg" if not etqs else "")
            if r["laminas"]:
                r["nivel"] = "lamina"
        r["_A"], r["_L"] = sorted(A), sorted(L)
        out[num] = r
    return out


# ------------------------------------------------------------------ Vaticano
def construir_vaticano(man):
    canv = man["sequences"][0]["canvases"]
    por_id = {c["@id"]: c for c in canv}
    por_etq = {}
    for c in canv:
        por_etq.setdefault(str(c["label"]).strip(), []).append(c)
    libros = {}
    for s in man.get("structures", []):
        etq = re.sub(r"\s+", " ", str(s.get("label", "")).replace("\xa0", " ")).strip()
        m = re.fullmatch(r"p\. ?(\d+)-(\d+) (.+)", etq)
        if not m or m[3] not in VAT_LIBRO:
            continue
        lib = VAT_LIBRO[m[3]]
        cs = por_etq.get(m[1], [])
        if len(cs) > 1:                                  # la numeración se repite (p. ej. «1» del Nuevo Testamento): la del tramo
            cs = [c for c in cs if c["@id"] in s.get("canvases", [])]
        if len(cs) != 1:
            fallo(f"Vaticano {lib}: la página {m[1]} sale {len(cs)} veces en el manifiesto")
            continue
        c = cs[0]
        if c["@id"] not in s.get("canvases", []):
            fallo(f"Vaticano {lib}: la página {m[1]} no está en el tramo «{etq}» del manifiesto")
        primera = por_id[s["canvases"][0]]["label"] if s.get("canvases") else None
        if str(primera) != m[1] and lib not in VAT_REVISADO:
            fallo(f"Vaticano {lib}: el rótulo dice p. {m[1]} y la primera imagen del tramo es la p. {primera}: revisar a mano")
        imagen = re.search(r"/canvas/p(\d{4})$", c["@id"])
        if not imagen:
            fallo(f"Vaticano {lib}: canvas inesperado {c['@id']}")
            continue
        libros[lib] = {"catalogo": etq, "pagina": m[1], "imagen": imagen[1], "url": VAT_VISOR + imagen[1],
                       "nota": VAT_NOTA.get(lib)}
    return libros


# ------------------------------------------------------------------ verificación (también la usa --autoprueba)
def verificar(sal, ctx_v):
    """Devuelve la lista de errores. ctx_v: {pasajes: [ids], rollos_testigo: [ids], muestra: [[rollo, fragmento, imagen]]}."""
    err = []
    L = sal["leningrado"]
    for pid in ctx_v["pasajes"]:
        if not L["pasajes"].get(pid):
            err.append(f"pasaje {pid} sin folio de Leningrado")
    for fo, f in L["folios"].items():
        if not f["archivo"].startswith("File:Leningrad Codex Folio ") or not f["pagina"].startswith("https://commons.wikimedia.org/wiki/File:"):
            err.append(f"folio {fo}: archivo o página de Commons mal formados")
        if not f["licencia"]:
            err.append(f"folio {fo}: sin licencia leída")
        if f["uso"] == "mostrar":
            if not LICENCIA_ABIERTA.match(f["licencia"]):
                err.append(f"folio {fo}: se muestra con licencia «{f['licencia']}», que no es abierta")
            if not f["miniatura"].startswith("https://upload.wikimedia.org/wikipedia/commons/thumb/"):
                err.append(f"folio {fo}: miniatura fuera de upload.wikimedia.org/…/thumb/")
        if not f["rv"]:
            err.append(f"folio {fo}: sin versículos RV")
    for fs in L["pasajes"].values():
        for fo in fs:
            if fo not in L["folios"]:
                err.append(f"pasaje con folio inexistente {fo}")
    R = sal["rollos"]
    for i in ctx_v["rollos_testigo"]:
        if i not in R:
            err.append(f"rollo {i}: falta")
    for i, r in R.items():
        if r["nivel"] == "fragmento":
            A, L2 = set(), set()
            for fr in r["fragmentos"]:
                n = numeros_fragmento(fr["abegg"])
                if n is None:
                    err.append(f"rollo {i}: fragmento «{fr['abegg']}» sin numeración de fragmento")
                    continue
                A |= n
                if {int(x["fragmento_ll"]) for x in fr["imagenes"]} - n:
                    err.append(f"rollo {i}: el fragmento {fr['abegg']} enlaza otro número de la Leon Levy")
            if r.get("_A") is not None and (set(r["_A"]) != set(r["_L"]) or not set(r["_A"])):
                err.append(f"rollo {i}: enlazado a fragmentos sin que coincidan los números (Abegg {r['_A']}, LL {r['_L']})")
        elif r["nivel"] == "lamina" and not r["laminas"]:
            err.append(f"rollo {i}: nivel lámina sin láminas")
        for x in r["laminas"] + [im for fr in r["fragmentos"] for im in fr["imagenes"]]:
            if not re.fullmatch(r"B-\d+", x["imagen"]):
                err.append(f"rollo {i}: imagen con nombre raro {x['imagen']}")
            if x["tipo_foto"] not in (FOTO_COLOR,) + FOTO_IR:
                err.append(f"rollo {i}: tipo de foto no elegible {x['tipo_foto']}")
    for rid, etq, img in ctx_v["muestra"]:
        r = R.get(rid)
        fr = [f for f in (r or {}).get("fragmentos", []) if f["abegg"] == etq]
        if not r or r["nivel"] != "fragmento" or not fr or img not in [x["imagen"] for x in fr[0]["imagenes"]]:
            err.append(f"muestra verificada {rid} {etq}: ya no se enlaza con {img}")
    V = sal["vaticano"]["libros"]
    for lib in LIBROS:
        if lib not in V:
            err.append(f"Vaticano: falta {lib}")
        elif not re.fullmatch(re.escape(VAT_VISOR) + r"\d{4}", V[lib]["url"]):
            err.append(f"Vaticano {lib}: enlace mal formado")
    return err


def autoprueba():
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ok = True
    for caso in fx["descripciones"]:
        got = parse_descripcion(caso["desc"])
        got = [list(x) for x in got] if got else None
        if got != caso["esperado"]:
            print(f"autoprueba: parse_descripcion «{caso['desc']}» -> {got}, se esperaba {caso['esperado']}")
            ok = False
    for caso in fx["etiquetas"]:
        n = numeros_fragmento(caso["etq"])
        if (sorted(n) if n is not None else None) != caso["esperado"]:
            print(f"autoprueba: numeros_fragmento «{caso['etq']}» -> {n}, se esperaba {caso['esperado']}")
            ok = False
    base, cv = fx["salida"], fx["contexto"]
    e = verificar(base, cv)
    print(f"autoprueba: fixture base -> {len(e)} errores (debe ser 0)")
    ok &= not e
    for alt in fx["alteraciones"]:
        s = copy.deepcopy(base)
        obj = s
        for k in alt["ruta"][:-1]:
            obj = obj[k]
        if alt.get("borrar"):
            del obj[alt["ruta"][-1]]
        else:
            obj[alt["ruta"][-1]] = alt["valor"]
        e = verificar(s, cv)
        print(f"autoprueba: «{alt['nombre']}» -> {len(e)} errores (debe fallar){': ' + e[0] if e else ''}")
        ok &= bool(e)
    print("AUTOPRUEBA", "OK" if ok else "FALLA")
    return ok


# ------------------------------------------------------------------ principal
def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--autoprueba" in sys.argv:
        sys.exit(0 if autoprueba() else 1)
    sin_red = "--sin-red" in sys.argv
    orig = cargar_originales_py()
    ctx = contexto_textos(orig, sin_red)

    # Leningrado
    paginas = leer_commons(sin_red)
    leningrado, sin_folio = construir_leningrado(paginas, ctx)
    sin_folio_reales = [k for k in sin_folio if k not in ctx["sin_texto"] and k not in ctx["rv_vacios"]]
    for k in sin_folio_reales:
        fallo(f"Leningrado: {ref(k)} (RV) sin folio")
    if sin_folio:
        aviso("Leningrado: sin folio por no estar en el códice: " + ", ".join(ref(k) for k in sin_folio if k in ctx["sin_texto"]))
    test_L = next(t for t in ctx["testigos"] if t["id"] == "leningrado")

    # Rollos
    abegg = fragmentos_abegg(orig, sin_red)
    ll = {}
    for t in ctx["testigos"]:
        if t.get("tipo") == "rollo":
            ll[t["id"]] = leer_ll(t["id"], sin_red)
    rollos = construir_rollos(ctx["testigos"], orig.ROLLOS, abegg, ll, ctx)
    for (rid, etq), (img, nota) in MUESTRA_VERIFICADA.items():
        for fr in rollos.get(rid, {}).get("fragmentos", []):
            if fr["abegg"] == etq and img in [x["imagen"] for x in fr["imagenes"]]:
                fr["comprobado"] = f"Comprobado a mano el 2026-11-13 con la imagen {img}: {nota}"

    # Vaticano
    man = pedir_json(VAT_MANIFIESTO, sin_red, CACHE / "vat_manifest.json")
    vat = construir_vaticano(man)
    test_V = next(t for t in ctx["testigos"] if t["id"] == "vaticano")

    sal = {
        "generado": HOY,
        "leningrado": {
            "testigo": "leningrado",
            "nombre": test_L["nombre"],
            "institucion": test_L["institucion"],
            "fecha": test_L["fecha"],
            "clase": "registro_historico",
            "fuente": ("Imágenes: Wikimedia Commons, categorías «Leningrad Codex, color JPG images» (escaneo de la USC Dornsife "
                       "a partir de las fotografías del códice; origen indicado en Commons: manuscripts.sefaria.org). "
                       f"Licencia, autor y crédito leídos de la API de Commons para cada archivo ({HOY})."),
            "nota": ("Qué versículos muestra cada folio sale de la descripción de Commons (ImageDescription), que usa la numeración "
                     "hebrea; aquí se pasa a la RV1909 con la correspondencia de originales.js (TVTMS). El primer y el último "
                     "versículo de un folio pueden estar partidos entre dos folios. «miniatura» es la imagen de Commons a "
                     f"{ANCHO_MINIATURA} px de ancho, cargada en línea (sin copia local)."),
            **leningrado,
        },
        "rollos": {
            "fuente": ("Leon Levy Dead Sea Scrolls Digital Library (Autoridad de Antigüedades de Israel): API de búsqueda de imágenes, "
                       "consultada con pausas y guardada en caché. Fragmentos de cada rollo: datos de Abegg (ETCBC/dss, CC BY-NC 4.0)."),
            "uso": "solo_enlace",
            "url_imagen": LL_IMAGEN,
            "nota": ("Enlace de cada imagen: url_imagen + imagen (p. ej. «B-360503»). Los términos de la IAA no permiten mostrar sus imágenes: solo se enlaza la página de cada imagen. "
                     "«fragmento»: el enlace va a la imagen del fragmento, solo si los números de fragmento de Abegg y de la Leon Levy "
                     "coinciden en todo el rollo. «lamina»: a las láminas del rollo (sin saber cuál tiene cada versículo). «ficha»: a la "
                     "ficha del rollo. Por imagen se elige la «Full Spectrum Color» más reciente o, si no hay, la infrarroja."),
            "rollos": {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")} for k, v in rollos.items()},
        },
        "vaticano": {
            "testigo": "vaticano",
            "nombre": test_V["nombre"],
            "institucion": test_V["institucion"],
            "clase": "registro_historico",
            "uso": "solo_enlace",
            "fuente": (f"Manifiesto IIIF de la Biblioteca Apostólica Vaticana ({VAT_MANIFIESTO}), «structures» por libro; "
                       f"consultado el {HOY}. La BAV no permite mostrar sus imágenes: solo enlace al visor."),
            "libros": vat,
        },
    }

    # verificación (con los campos internos de rollos para comprobar el criterio)
    sal_v = copy.deepcopy(sal)
    sal_v["rollos"] = rollos
    ids_rollo = [t["id"] for t in ctx["testigos"] if t.get("tipo") == "rollo"]
    for e in verificar(sal_v, {"pasajes": [p for p, a, _ in ctx["pasajes"] if a[0] in LIBROS], "rollos_testigo": ids_rollo,
                                "muestra": [(r, e, img) for (r, e), (img, _) in MUESTRA_VERIFICADA.items()]}):
        fallo(e)

    # resumen
    por_libro = {}
    for fo, f in leningrado["folios"].items():
        for r in f["rv"]:
            for extremo in r.split("-"):
                por_libro.setdefault(extremo.split(" ")[0], set()).add(fo)
    print("Leningrado: folios por libro:", {l: len(por_libro.get(l, ())) for l in LIBROS})
    lic = {}
    for f in leningrado["folios"].values():
        lic[f["licencia"]] = lic.get(f["licencia"], 0) + 1
    print("Leningrado: licencias:", lic, "· mostrar:", sum(f["uso"] == "mostrar" for f in leningrado["folios"].values()))
    n_p = sum(1 for p in leningrado["pasajes"].values() if p)
    print(f"Leningrado: pasajes con folio {n_p}/{len(leningrado['pasajes'])}")
    niv = {}
    for r in rollos.values():
        niv[r["nivel"]] = niv.get(r["nivel"], 0) + 1
    print("Rollos por nivel:", niv)
    print("  fragmento:", [k for k, r in rollos.items() if r["nivel"] == "fragmento"])
    print("Vaticano:", {l: v["pagina"] + " (" + v["imagen"] + ")" for l, v in vat.items()})
    if "--muestra" in sys.argv:
        for k, r in rollos.items():
            if r["nivel"] == "fragmento":
                for fr in r["fragmentos"]:
                    print(" ", k, fr["abegg"], fr["versiculos"], [(x["imagen"], x["tipo_foto"], x["fecha_foto"]) for x in fr["imagenes"]])

    if FALLOS:
        print(f"\n{len(FALLOS)} fallos: no se escribe nada.")
        sys.exit(1)
    cab = ("// Generado por herramientas/manuscritos.py. No editar a mano.\n"
           "// Leningrado: Wikimedia Commons (licencia por archivo). Rollos: Leon Levy DSS Digital Library (IAA), solo enlace.\n"
           "// Vaticano: Biblioteca Apostólica Vaticana, solo enlace.\n")
    n = escribir_js(DATOS / "manuscritos.js", cab, "BIBLIA_MANUSCRITOS", sal)
    print(f"datos/manuscritos.js: {n / 1024:.0f} KB")


if __name__ == "__main__":
    main()
