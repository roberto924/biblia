#!/usr/bin/env python3
"""Construye datos/genesis.js (Génesis 1–11) a partir de fuentes abiertas.

Uso:  python herramientas/construir_datos.py [--sin-red]

- Descarga (con caché en herramientas/cache/) RV1909, Brenton (LXX inglesa) y BibleData.
- Genera datos/genesis.js con  window.BIBLIA_DATOS = {...};
- Verifica citas, cifras, sumas, relaciones y nombres. Sale con código 1 si falla
  una verificación obligatoria (las sumas que no cuadran y los nombres no hallados
  se listan como advertencias).
Solo biblioteca estándar de Python 3.11.
"""
import csv
import io
import json
import re
import sys
import unicodedata
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "herramientas" / "cache"
SALIDA = RAIZ / "datos" / "genesis.js"

BD = "https://raw.githubusercontent.com/BradyStephenson/bible-data/HEAD/"
FUENTES = [
    {"id": "rv1909", "nombre": "Reina-Valera 1909 (texto masorético), vía eBible.org",
     "licencia": "Dominio público", "url": "https://ebible.org/Scriptures/spaRV1909_vpl.zip"},
    {"id": "brenton", "nombre": "Septuaginta, traducción inglesa de L. C. L. Brenton (1851), vía eBible.org",
     "licencia": "Dominio público", "url": "https://ebible.org/Scriptures/eng-Brenton_vpl.zip"},
    {"id": "bibledata", "nombre": "BibleData (Brady Stephenson): Person, PersonLabel y PersonRelationship",
     "licencia": "CC BY 4.0", "url": "https://github.com/BradyStephenson/bible-data"},
]
ARCHIVOS = {
    "rv": ("https://ebible.org/Scriptures/spaRV1909_vpl.zip", "spaRV1909_vpl.zip"),
    "br": ("https://ebible.org/Scriptures/eng-Brenton_vpl.zip", "eng-Brenton_vpl.zip"),
    "rel": (BD + "BibleData-PersonRelationship.csv", "BibleData-PersonRelationship.csv"),
    "per": (BD + "BibleData-Person.csv", "BibleData-Person.csv"),
    "lab": (BD + "BibleData-PersonLabel.csv", "BibleData-PersonLabel.csv"),
}

# Nombre tal como aparece en RV1909 (o en Brenton→español para los solo-LXX).
NOMBRES = {
    "Adam_1": "Adam", "Eve_1": "Eva", "Cain_1": "Caín", "Abel_1": "Abel", "Enoch_1": "Henoch",
    "Irad_1": "Irad", "Mehujael_1": "Mehujael", "Methushael_1": "Methusael", "Lamech_1": "Lamech",
    "Adah_1": "Ada", "Zillah_1": "Zilla", "Jabal_1": "Jabal", "Jubal_1": "Jubal",
    "Tubal-cain_1": "Tubal-Caín", "Naamah_1": "Naama", "Seth_1": "Seth", "Enosh_1": "Enós",
    "Kenan_1": "Cainán", "Mahalalel_1": "Mahalaleel", "Jared_1": "Jared", "Enoch_2": "Henoch",
    "Methuselah_1": "Mathusalam", "Lamech_2": "Lamech", "Noah_1": "Noé", "Japheth_1": "Japhet",
    "Shem_1": "Sem", "Ham_1": "Châm", "Canaan_1": "Canaán", "Gomer_1": "Gomer", "Magog_1": "Magog",
    "Madai_1": "Madai", "Javan_1": "Javán", "Tubal_1": "Tubal", "Meshech_1": "Meshech",
    "Tiras_1": "Tiras", "Elishah_2": "Elisa", "Ashkenaz_1": "Ashkenaz", "Riphath_1": "Riphat",
    "Togarmah_1": "Togorma", "Elishah_1": "Elisa", "Tarshish_1": "Tarsis", "Kittim_1": "Kittim",
    "Dodanim_1": "Dodanim", "Cush_1": "Cush", "Mizraim_1": "Mizraim", "Put_1": "Phut",
    "Seba_1": "Seba", "Havilah_1": "Havila", "Sabtah_1": "Sabta", "Raamah_1": "Raama",
    "Sabteca_1": "Sabtecha", "Sheba_1": "Sheba", "Dedan_1": "Dedán", "Nimrod_1": "Nimrod",
    "Lud_1": "Ludim", "Anam_1": "Anamim", "Lehab_1": "Lehabim", "Naphtuh_1": "Naphtuhim",
    "Pathrus_1": "Pathrusim", "Casluh_1": "Casluim", "Caphtor_1": "Caphtorim", "Sidon_1": "Sidón",
    "Heth_1": "Heth", "Jebus_1": "Jebuseo", "Amor_1": "Amorrheo", "Girgash_1": "Gergeseo",
    "Hivi_1": "Heveo", "Ark_1": "Araceo", "Sini_1": "Sineo", "Arvad_1": "Aradio",
    "Zemar_1": "Samareo", "Hamath_1": "Amatheo", "Elam_1": "Elam", "Asshur_1": "Assur",
    "Arpachshad_1": "Arphaxad", "Lud_2": "Lud", "Aram_1": "Aram", "Uz_1": "Uz", "Hul_1": "Hul",
    "Gether_1": "Gether", "Mash_1": "Mas", "Shelah_1": "Sala", "Eber_1": "Heber", "Peleg_1": "Peleg",
    "Joktan_1": "Joctán", "Almodad_1": "Almodad", "Sheleph_1": "Sheleph",
    "Hazarmaveth_1": "Hazarmaveth", "Jerah_1": "Jera", "Hadoram_1": "Hadoram", "Uzal_1": "Uzal",
    "Diklah_1": "Dicla", "Obal_1": "Obal", "Abimael_1": "Abimael", "Sheba_2": "Seba",
    "Ophir_1": "Ophir", "Havilah_2": "Havila", "Jobab_1": "Jobad", "Reu_1": "Reu", "Serug_1": "Serug",
    "Nahor_1": "Nachôr", "Terah_1": "Thare", "Abram_1": "Abram", "Nahor_2": "Nachôr",
    "Haran_1": "Harán", "Lot_1": "Lot", "Sarai_1": "Sarai", "Milcah_1": "Milca", "Iscah_1": "Isca",
    "Cainan_1": "Cainán",
}
# Grafía española actual de uso común (tipo RVR1960/NVI) para cada persona.
MODERNO = {
    "Adam_1": "Adán", "Eve_1": "Eva", "Cain_1": "Caín", "Abel_1": "Abel", "Enoch_1": "Enoc",
    "Irad_1": "Irad", "Mehujael_1": "Mehujael", "Methushael_1": "Metusael", "Lamech_1": "Lamec",
    "Adah_1": "Ada", "Zillah_1": "Zila", "Jabal_1": "Jabal", "Jubal_1": "Jubal",
    "Tubal-cain_1": "Tubal-Caín", "Naamah_1": "Naama", "Seth_1": "Set", "Enosh_1": "Enós",
    "Kenan_1": "Cainán", "Mahalalel_1": "Mahalaleel", "Jared_1": "Jared", "Enoch_2": "Enoc",
    "Methuselah_1": "Matusalén", "Lamech_2": "Lamec", "Noah_1": "Noé", "Japheth_1": "Jafet",
    "Shem_1": "Sem", "Ham_1": "Cam", "Canaan_1": "Canaán", "Gomer_1": "Gomer", "Magog_1": "Magog",
    "Madai_1": "Madai", "Javan_1": "Javán", "Tubal_1": "Tubal", "Meshech_1": "Mesec",
    "Tiras_1": "Tiras", "Elishah_2": "Elisa", "Ashkenaz_1": "Askenaz", "Riphath_1": "Rifat",
    "Togarmah_1": "Togarma", "Elishah_1": "Elisa", "Tarshish_1": "Tarsis", "Kittim_1": "Quitim",
    "Dodanim_1": "Dodanim", "Cush_1": "Cus", "Mizraim_1": "Mizraim", "Put_1": "Fut",
    "Seba_1": "Seba", "Havilah_1": "Havila", "Sabtah_1": "Sabta", "Raamah_1": "Raama",
    "Sabteca_1": "Sabteca", "Sheba_1": "Sabá", "Dedan_1": "Dedán", "Nimrod_1": "Nimrod",
    "Lud_1": "Ludim", "Anam_1": "Anamim", "Lehab_1": "Lehabim", "Naphtuh_1": "Naftuhim",
    "Pathrus_1": "Patrusim", "Casluh_1": "Casluhim", "Caphtor_1": "Caftorim", "Sidon_1": "Sidón",
    "Heth_1": "Het", "Jebus_1": "Jebuseo", "Amor_1": "Amorreo", "Girgash_1": "Gergeseo",
    "Hivi_1": "Heveo", "Ark_1": "Araceo", "Sini_1": "Sineo", "Arvad_1": "Arvadeo",
    "Zemar_1": "Zemareo", "Hamath_1": "Hamateo", "Elam_1": "Elam", "Asshur_1": "Asur",
    "Arpachshad_1": "Arfaxad", "Lud_2": "Lud", "Aram_1": "Aram", "Uz_1": "Uz", "Hul_1": "Hul",
    "Gether_1": "Geter", "Mash_1": "Mas", "Shelah_1": "Sala", "Eber_1": "Heber", "Peleg_1": "Péleg",
    "Joktan_1": "Joctán", "Almodad_1": "Almodad", "Sheleph_1": "Selef",
    "Hazarmaveth_1": "Hazar-mavet", "Jerah_1": "Jera", "Hadoram_1": "Hadoram", "Uzal_1": "Uzal",
    "Diklah_1": "Dicla", "Obal_1": "Obal", "Abimael_1": "Abimael", "Sheba_2": "Sabá",
    "Ophir_1": "Ofir", "Havilah_2": "Havila", "Jobab_1": "Jobab", "Reu_1": "Reu", "Serug_1": "Serug",
    "Nahor_1": "Nacor", "Terah_1": "Taré", "Abram_1": "Abram", "Nahor_2": "Nacor",
    "Haran_1": "Harán", "Lot_1": "Lot", "Sarai_1": "Sarai", "Milcah_1": "Milca", "Iscah_1": "Isca",
    "Cainan_1": "Cainán",
}
# Personas que solo están en la LXX: el nombre se comprueba en Brenton con esta forma inglesa.
SOLO_LXX = {
    "Cainan_1": ("Cainan", "Solo en la Septuaginta (Gn 11:12-13) y en Lucas 3:36; no está en el texto masorético."),
    "Elishah_2": ("Elisa", "Solo en la Septuaginta (Gn 10:2), según BibleData; no está en el texto masorético."),
}
GENTILICIO = "El texto nombra un pueblo (gentilicio o plural); BibleData lo trata como antepasado epónimo."

# Edades: persona -> {tradicion: [(tipo, ref, indice_de_cifra_en_el_versiculo), ...]}
# El índice elige qué cifra del versículo es la buena cuando hay varias.
def _g5(v0):
    return [("al_engendrar", (5, v0), 0), ("restantes", (5, v0 + 1), 0), ("total", (5, v0 + 2), 0)]

def _g11(v0):
    return [("al_engendrar", (11, v0), 0), ("restantes", (11, v0 + 1), 0)]

G5 = {"Adam_1": 3, "Seth_1": 6, "Enosh_1": 9, "Kenan_1": 12, "Mahalalel_1": 15, "Jared_1": 18,
      "Enoch_2": 21, "Methuselah_1": 25}
EDADES = {p: {"TM": _g5(v), "LXX": _g5(v)} for p, v in G5.items()}
EDADES["Lamech_2"] = {t: [("al_engendrar", (5, 28), 0), ("restantes", (5, 30), 0), ("total", (5, 31), 0)]
                      for t in ("TM", "LXX")}
EDADES["Noah_1"] = {t: [("al_engendrar", (5, 32), 0), ("al_diluvio", (7, 6), 0),
                        ("restantes", (9, 28), 0), ("total", (9, 29), 0)] for t in ("TM", "LXX")}
G11 = {"Shem_1": 10, "Arpachshad_1": 12, "Shelah_1": 14, "Eber_1": 16, "Peleg_1": 18, "Reu_1": 20,
       "Serug_1": 22, "Nahor_1": 24}
for p, v in G11.items():
    EDADES[p] = {"TM": _g11(v), "LXX": _g11(v)}
# Brenton Gn 11:13 contiene a Arfaxad (restantes) y a Cainán (al engendrar, restantes).
EDADES["Cainan_1"] = {"LXX": [("al_engendrar", (11, 13), 1), ("restantes", (11, 13), 2)]}
EDADES["Terah_1"] = {t: [("al_engendrar", (11, 26), 0), ("total", (11, 32), 0)] for t in ("TM", "LXX")}
NOTA_EDAD = {
    ("Noah_1", "restantes"): "Años vividos después del diluvio (no después de engendrar).",
    ("Noah_1", "al_diluvio"): "Edad de Noé al llegar el diluvio.",
    ("Shem_1", "al_engendrar"): "El texto lo sitúa «dos años después del diluvio».",
}
CAINAN_REL = [("Arpachshad_1", "Cainan_1", (11, 12)), ("Cainan_1", "Shelah_1", (11, 13))]


# ---------------------------------------------------------------- descarga
def obtener(clave, sin_red):
    url, nombre = ARCHIVOS[clave]
    ruta = CACHE / nombre
    if not ruta.exists():
        if sin_red:
            sys.exit(f"Falta {ruta} y se pidió --sin-red")
        CACHE.mkdir(parents=True, exist_ok=True)
        print(f"Descargando {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "biblia-datos/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            ruta.write_bytes(r.read())
    return ruta


def leer_vpl(ruta_zip):
    """Devuelve {(cap, vers): texto} de Génesis 1–11."""
    with zipfile.ZipFile(ruta_zip) as z:
        nombre = next(n for n in z.namelist() if n.endswith("_vpl.txt"))
        texto = z.read(nombre).decode("utf-8-sig")
    v = {}
    for linea in texto.splitlines():
        m = re.match(r"GEN (\d+):(\d+) (.*)", linea)
        if m and int(m.group(1)) <= 11:
            v[(int(m.group(1)), int(m.group(2)))] = m.group(3).strip()
    return v


def leer_csv(ruta):
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- numerales
ES = {"un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6,
      "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12, "trece": 13,
      "catorce": 14, "quince": 15, "dieciseis": 16, "diecisiete": 17, "dieciocho": 18,
      "diecinueve": 19, "veinte": 20, "veintiun": 21, "veintiuno": 21, "veintidos": 22,
      "veintitres": 23, "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26,
      "veintisiete": 27, "veintiocho": 28, "veintinueve": 29, "treinta": 30, "cuarenta": 40,
      "cincuenta": 50, "sesenta": 60, "setenta": 70, "ochenta": 80, "noventa": 90, "cien": 100,
      "ciento": 100, "doscientos": 200, "trescientos": 300, "cuatrocientos": 400,
      "quinientos": 500, "seiscientos": 600, "setecientos": 700, "ochocientos": 800,
      "novecientos": 900}
EN = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
      "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
      "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
      "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
      "eighty": 80, "ninety": 90}


def sin_acentos(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


def numeral_a_numero(frase, idioma):
    """'ciento y treinta' -> 130 ; 'two hundred and thirty-five' -> 235."""
    total = actual = 0
    vistos = 0
    for w in re.split(r"[\s\-]+", sin_acentos(frase).strip()):
        if not w:
            continue
        if idioma == "es":
            if w == "y":
                continue
            if w == "mil":
                total += max(actual, 1) * 1000; actual = 0; vistos += 1; continue
            if w not in ES:
                raise ValueError(f"palabra no numérica: {w!r} en {frase!r}")
            actual += ES[w]; vistos += 1
        else:
            if w in ("and", "a", "an"):
                continue
            if w == "hundred":
                actual = max(actual, 1) * 100; vistos += 1; continue
            if w == "thousand":
                total += max(actual, 1) * 1000; actual = 0; vistos += 1; continue
            if w not in EN:
                raise ValueError(f"palabra no numérica: {w!r} en {frase!r}")
            actual += EN[w]; vistos += 1
    if not vistos:
        raise ValueError(f"sin cifra: {frase!r}")
    return total + actual


def _patron(idioma):
    if idioma == "es":
        pal = sorted(set(ES) | {"mil", "veintiún", "dieciséis", "veintidós", "veintitrés", "veintiséis"},
                     key=len, reverse=True)
        num = r"(?:%s)" % "|".join(pal)
        return re.compile(r"\b%s(?:(?:\s+y)?\s+%s)*\s+años\b" % (num, num), re.I)
    pal = sorted(set(EN) | {"hundred", "thousand"}, key=len, reverse=True)
    num = r"(?:%s)" % "|".join(pal)
    return re.compile(r"\b(?:(?:a|an)\s+)?%s(?:(?:\s+and\s+|\s+|-)%s)*\s+years\b" % (num, num), re.I)


PATRON = {"es": _patron("es"), "en": _patron("en")}


def cifras(verso, idioma):
    return [m.group(0) for m in PATRON[idioma].finditer(verso)]


def gn(ref):
    return f"Gn {ref[0]}:{ref[1]}"


def parse_gn(s):
    m = re.match(r"Gn (\d+):(\d+)$", s)
    return (int(m.group(1)), int(m.group(2)))


# ---------------------------------------------------------------- construcción
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sin_red = "--sin-red" in sys.argv
    errores, avisos = [], []
    rv = leer_vpl(obtener("rv", sin_red))
    br = leer_vpl(obtener("br", sin_red))
    rels = leer_csv(obtener("rel", sin_red))
    per = {r["person_id"]: r for r in leer_csv(obtener("per", sin_red))}
    obtener("lab", sin_red)  # se guarda en caché como referencia (etiquetas/nombres alternativos)

    # Capítulos
    capitulos = []
    for c in range(1, 12):
        vs = sorted(v for (cc, v) in rv if cc == c)
        if vs != list(range(1, len(vs) + 1)):
            errores.append(f"Gn {c}: numeración de versículos no continua")
        capitulos.append({"libro": "Génesis", "cap": c,
                          "versiculos": [{"n": v, "texto": rv[(c, v)]} for v in vs]})

    # Relaciones de BibleData en Gn 1–11
    def ref_gen(s):
        m = re.match(r"GEN (\d+):(\d+)$", s.strip())
        return (int(m.group(1)), int(m.group(2))) if m and int(m.group(1)) <= 11 else None

    candidatas = {}  # (de, a, tipo) -> dict
    descartadas = Counter()
    for r in rels:
        ref = ref_gen(r["reference_id"])
        if not ref:
            continue
        p1, t, p2 = r["person_id_1"], r["relationship_type"].strip().lower(), r["person_id_2"]
        sexo2 = per.get(p2, {}).get("sex", "")
        if t == "father":
            de, a, tipo = p1, p2, "padre"
        elif t == "mother":
            de, a, tipo = p1, p2, "madre"
        elif t in ("son", "daughter"):
            de, a, tipo = p2, p1, ("madre" if sexo2 == "female" else "padre")
        elif t in ("husband", "wife"):
            de, a = sorted((p1, p2)); tipo = "conyuge"
        else:
            descartadas[t] += 1
            continue
        cert = "explicito" if r["relationship_category"].strip() == "explicit" else "inferido"
        nuevo = {"de": de, "a": a, "tipo": tipo, "ref": gn(ref), "certeza": cert,
                 "fuente": "bibledata", "nota": r["relationship_notes"].strip()}
        k = (de, a, tipo)
        viejo = candidatas.get(k)
        rank = lambda x: (x["certeza"] != "explicito", parse_gn(x["ref"]))
        if viejo is None or rank(nuevo) < rank(viejo):
            if viejo and not nuevo["nota"]:
                nuevo["nota"] = viejo["nota"]
            candidatas[k] = nuevo
    for de, a, ref in CAINAN_REL:
        candidatas[(de, a, "padre")] = {"de": de, "a": a, "tipo": "padre", "ref": gn(ref),
                                        "certeza": "explicito", "fuente": "brenton",
                                        "nota": "Solo en la Septuaginta."}
    # En TM, Arfaxad engendra a Sala (Gn 11:12); se conserva (BibleData) junto a la línea LXX.
    # Subir certeza: (a) edad al_engendrar "texto" cuyo versículo nombra al hijo;
    # (b) relación inferida cuyo versículo nombra a ambos con engendró/parió.
    def nombra(verso, nombre):
        return re.search(r"(?<!\w)%s(?!\w)" % re.escape(sin_acentos(nombre)), sin_acentos(verso))
    subidas = 0
    for p, trads in EDADES.items():
        for trad, items in trads.items():
            for tipo, ref, _ in items:
                if tipo != "al_engendrar":
                    continue
                textos, fuente = (rv, "rv1909") if trad == "TM" else (br, "brenton")
                verso = textos.get(ref, "")
                for x in candidatas.values():
                    # TM decide para los hijos del texto masorético; LXX solo para los solo-LXX.
                    if x["de"] != p or x["tipo"] != "padre" or (x["a"] in SOLO_LXX) != (trad == "LXX"):
                        continue
                    hijo = SOLO_LXX[x["a"]][0] if x["a"] in SOLO_LXX else NOMBRES[x["a"]]
                    if nombra(verso, hijo) and re.search(r"engendr|begot", verso):
                        subidas += x["certeza"] != "explicito"
                        x.update(certeza="explicito", ref=gn(ref), fuente=fuente,
                                 nota="Confirmada por la edad al engendrar en este versículo.")
    # Comprobación: toda relación con fuente de texto nombra al hijo en su versículo.
    for x in candidatas.values():
        if x["fuente"] in ("rv1909", "brenton"):
            textos = rv if x["fuente"] == "rv1909" else br
            hijo = SOLO_LXX[x["a"]][0] if x["a"] in SOLO_LXX else NOMBRES[x["a"]]
            if not nombra(textos.get(parse_gn(x["ref"]), ""), hijo):
                errores.append(f"Hijo «{hijo}» no está en {x['ref']} ({x['fuente']})")
    for x in candidatas.values():
        if x["certeza"] == "inferido" and x["tipo"] in ("padre", "madre"):
            verso = rv.get(parse_gn(x["ref"]), "")
            if (nombra(verso, NOMBRES[x["de"]]) and nombra(verso, NOMBRES[x["a"]])
                    and re.search(r"engendr|pari[oó]", sin_acentos(verso))):
                subidas += 1
                x.update(certeza="explicito", fuente="rv1909",
                         nota=(x["nota"] + " " if x["nota"] else "") +
                         "BibleData la marca inferida; el versículo nombra a ambos.")
    relaciones = sorted(candidatas.values(), key=lambda x: (parse_gn(x["ref"]), x["de"], x["a"]))

    # Personas
    refs = defaultdict(set)
    for x in relaciones:
        refs[x["de"]].add(parse_gn(x["ref"])); refs[x["a"]].add(parse_gn(x["ref"]))
    for p, trads in EDADES.items():
        for trad, items in trads.items():
            for _, ref, _ in items:
                refs[p].add(ref)
    for p in list(refs):
        if p not in NOMBRES:
            errores.append(f"Persona sin nombre español en NOMBRES: {p}")
    personas, fallos_nombre = [], []
    for p in sorted(refs, key=lambda q: (min(refs[q]), q)):
        nombre = NOMBRES.get(p, p)
        lista = sorted(refs[p])
        if p in SOLO_LXX:
            fuente_v, buscado = br, SOLO_LXX[p][0]
        else:
            fuente_v, buscado = rv, nombre
        pat = re.compile(r"(?<!\w)%s(?!\w)" % re.escape(sin_acentos(buscado)))
        con_nombre = [r for r in lista if pat.search(sin_acentos(fuente_v.get(r, "")))]
        primera = con_nombre[0] if con_nombre else lista[0]
        if not con_nombre:
            fallos_nombre.append(f"{p} «{buscado}» no aparece en {gn(primera)}")
        sexo = {"male": "m", "female": "f"}.get(per.get(p, {}).get("sex", ""), "?")
        nota = SOLO_LXX[p][1] if p in SOLO_LXX else ""
        if re.search(r"(im|eo)$", nombre) and p not in ("Dodanim_1", "Kittim_1", "Mizraim_1"):
            nota = GENTILICIO
        if p == "Kenan_1":
            nota = "Distinto del Cainán hijo de Arfaxad que solo aparece en la Septuaginta (Gn 11:12-13)."
        moderno = MODERNO.get(p)
        if not moderno:
            errores.append(f"Persona sin grafía actual en MODERNO: {p}")
            moderno = nombre
        forma_rv = None if p in SOLO_LXX else nombre
        if forma_rv and forma_rv != moderno:
            nota = f"En la Reina-Valera 1909: {forma_rv}." + (" " + nota if nota else "")
        personas.append({"id": p, "nombre": moderno, "nombre_rv1909": forma_rv, "sexo": sexo,
                         "primera_ref": gn(primera), "refs": [gn(r) for r in lista], "nota": nota})
    ids = {x["id"] for x in personas}
    for x in relaciones:
        for q in (x["de"], x["a"]):
            if q not in ids:
                errores.append(f"Relación a persona inexistente: {q}")

    # Edades
    edades = []
    for p, trads in EDADES.items():
        for trad, items in trads.items():
            fuente, textos, idioma = (("rv1909", rv, "es") if trad == "TM" else ("brenton", br, "en"))
            for tipo, ref, idx in items:
                verso = textos.get(ref, "")
                hallados = cifras(verso, idioma)
                if idx >= len(hallados):
                    errores.append(f"{p} {trad} {tipo}: no hay cifra n.º {idx} en {gn(ref)}")
                    continue
                cita = hallados[idx]
                edades.append({"persona": p, "tipo": tipo, "tradicion": trad,
                               "valor": numeral_a_numero(re.sub(r"\s+(años|years)$", "", cita, flags=re.I), idioma),
                               "ref": gn(ref), "certeza": "texto", "fuente": fuente, "cita": cita,
                               "nota": NOTA_EDAD.get((p, tipo), "")})
            # Cifra que falta: se calcula y se marca como cálculo.
            tipos = {e["tipo"]: e for e in edades if e["persona"] == p and e["tradicion"] == trad}
            base = "al_diluvio" if p == "Noah_1" else "al_engendrar"
            if "total" not in tipos and base in tipos and "restantes" in tipos:
                edades.append({"persona": p, "tipo": "total", "tradicion": trad,
                               "valor": tipos[base]["valor"] + tipos["restantes"]["valor"],
                               "ref": f'{tipos[base]["ref"]}-{tipos["restantes"]["ref"].split(" ")[1]}'
                               if tipos[base]["ref"] != tipos["restantes"]["ref"] else tipos[base]["ref"],
                               "certeza": "calculo", "fuente": fuente, "cita": "",
                               "nota": "Total no escrito en el texto: suma de las dos cifras anteriores."})
            elif "restantes" not in tipos and base in tipos and "total" in tipos:
                edades.append({"persona": p, "tipo": "restantes", "tradicion": trad,
                               "valor": tipos["total"]["valor"] - tipos[base]["valor"],
                               "ref": tipos["total"]["ref"], "certeza": "calculo", "fuente": fuente,
                               "cita": "", "nota": "No escrito en el texto: total menos edad al engendrar."})

    # ------------------------------------------------------------ verificación
    textos_de = {"rv1909": rv, "brenton": br}
    for e in edades:
        if e["certeza"] != "texto":
            continue
        verso = textos_de[e["fuente"]].get(parse_gn(e["ref"]), "")
        if not e["cita"] or e["cita"] not in verso:                       # 1
            errores.append(f"Cita no literal: {e['persona']} {e['ref']} {e['cita']!r}")
        idioma = "es" if e["fuente"] == "rv1909" else "en"
        n = numeral_a_numero(re.sub(r"\s+(años|years)$", "", e["cita"], flags=re.I), idioma)
        if n != e["valor"]:                                                 # 2
            errores.append(f"Cifra {e['valor']} ≠ cita {n}: {e['persona']} {e['ref']}")
    # comprobaciones fijas del conversor
    for f, idi, n in [("ciento y treinta", "es", 130), ("novecientos y treinta", "es", 930),
                      ("ochocientos y siete", "es", 807), ("two hundred and thirty", "en", 230),
                      ("a hundred and thirty-five", "en", 135), ("nine hundred and sixty-nine", "en", 969)]:
        if numeral_a_numero(f, idi) != n:
            errores.append(f"Conversor falla: {f}")
    sumas_ok = 0
    for p, trads in EDADES.items():                                         # 3
        for trad in trads:
            t = {e["tipo"]: e for e in edades if e["persona"] == p and e["tradicion"] == trad}
            base = "al_diluvio" if p == "Noah_1" else "al_engendrar"
            if all(k in t and t[k]["certeza"] == "texto" for k in (base, "restantes", "total")):
                if t[base]["valor"] + t["restantes"]["valor"] != t["total"]["valor"]:
                    avisos.append(f"Suma no cuadra {p} {trad}: {t[base]['valor']}+{t['restantes']['valor']}"
                                  f"≠{t['total']['valor']}")
                else:
                    sumas_ok += 1
    vistos = set()
    for x in relaciones:
        k = (x["de"], x["a"], x["tipo"])
        if k in vistos or (x["a"], x["de"], x["tipo"]) in vistos:
            errores.append(f"Relación duplicada o inversa: {k}")
        vistos.add(k)
    avisos.extend("Nombre no hallado: " + f for f in fallos_nombre)          # 4

    datos = {"generado": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
             "fuentes": FUENTES, "capitulos": capitulos, "personas": personas,
             "relaciones": relaciones, "edades": edades}
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("window.BIBLIA_DATOS = " + json.dumps(datos, ensure_ascii=False, indent=1) + ";\n",
                      encoding="utf-8")
    # relectura: JSON válido tras el '='
    txt = SALIDA.read_text(encoding="utf-8")
    json.loads(txt[txt.index("=") + 1:].rstrip().rstrip(";"))

    # ------------------------------------------------------------ resumen   5
    cert = Counter(x["certeza"] for x in relaciones)
    porte = Counter((e["tradicion"], e["certeza"]) for e in edades)
    print("=== RESUMEN genesis.js ===")
    print(f"Versículos: {sum(len(c['versiculos']) for c in capitulos)} (Gn 1–11)")
    print(f"Personas: {len(personas)}")
    print(f"Relaciones: {len(relaciones)} (explícitas {cert['explicito']}, inferidas {cert['inferido']}); "
          f"descartadas por tipo no genealógico: {dict(descartadas)}")
    print(f"Relaciones subidas de inferido a explícito por el texto: {subidas}; "
          f"por fuente: {dict(Counter(x['fuente'] for x in relaciones))}")
    for trad in ("TM", "LXX"):
        print(f"Edades {trad}: texto {porte[(trad, 'texto')]}, cálculo {porte[(trad, 'calculo')]}")
    print(f"Sumas al_engendrar+restantes=total comprobadas y correctas: {sumas_ok}")
    print(f"Advertencias ({len(avisos)}):")
    for a in avisos:
        print("  - " + a)
    if errores:
        print(f"ERRORES ({len(errores)}):")
        for e in errores:
            print("  - " + e)
        sys.exit(1)
    print("Verificación: OK")


if __name__ == "__main__":
    main()
