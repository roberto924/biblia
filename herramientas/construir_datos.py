#!/usr/bin/env python3
"""Construye datos/biblia.js (Génesis 1–50, Éxodo 1–40, Levítico 1–27, Números 1–36, Deuteronomio 1–34, Josué 1–24, Jueces 1–21, Rut 1–4 y 1 Samuel 1–31) a partir de fuentes abiertas.

Uso:  python herramientas/construir_datos.py [--sin-red]

- Descarga (con caché en herramientas/cache/) RV1909, Brenton (LXX inglesa) y BibleData.
- Genera datos/biblia.js con  window.BIBLIA_DATOS = {...};  (Éxodo: herramientas/exodo.py; Levítico: herramientas/levitico.py;
  Números: herramientas/numeros.py; Deuteronomio: herramientas/deuteronomio.py; Josué: herramientas/josue.py;
  Jueces: herramientas/jueces.py; Rut: herramientas/rut.py; 1 Samuel: herramientas/samuel1.py)
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

sys.path.insert(0, str(Path(__file__).resolve().parent))  # para importar lugares_mapa con python -I
import lugares_mapa as lm  # noqa: E402

import nombres_auto as na  # noqa: E402
import cronologia as cr  # noqa: E402
import genesis_12_50 as g2  # noqa: E402
import exodo  # noqa: E402
import levitico  # noqa: E402
import numeros  # noqa: E402
import deuteronomio  # noqa: E402
import josue  # noqa: E402
import jueces  # noqa: E402
import rut  # noqa: E402
import samuel1  # noqa: E402

MAXCAP = 50
RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "herramientas" / "cache"
SALIDA = RAIZ / "datos" / "biblia.js"
LIBROS = [{"id": "Gn", "nombre": "Génesis", "capitulos": 50}, {"id": "Ex", "nombre": "Éxodo", "capitulos": 40},
          {"id": "Lv", "nombre": "Levítico", "capitulos": 27}, {"id": "Nm", "nombre": "Números", "capitulos": 36},
          {"id": "Dt", "nombre": "Deuteronomio", "capitulos": 34},
          {"id": "Jos", "nombre": "Josué", "capitulos": 24}, {"id": "Jue", "nombre": "Jueces", "capitulos": 21},
          {"id": "Rut", "nombre": "Rut", "capitulos": 4}, {"id": "1S", "nombre": "1 Samuel", "capitulos": 31}]

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
    "pv": (BD + "BibleData-PersonVerse.csv", "BibleData-PersonVerse.csv"),
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
    "Cainan_1": "Cainán", "Jucam_1": "Jucam",
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
SOLO_LXX["Jucam_1"] = ("Jucam", "Solo en la Septuaginta (Gn 36:27), según BibleData; no está en el texto masorético.")
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
# Unidades de lectura (títulos y resúmenes editoriales, solo describen lo que dice el texto).
PASAJES = [
    ("Gn 1:1", "Gn 1:19", "La creación: días primero a cuarto",
     "Dios crea la luz, el firmamento, la tierra seca con las plantas y las lumbreras del cielo."),
    ("Gn 1:20", "Gn 2:3", "La creación: días quinto a séptimo",
     "Dios crea los animales del mar, del aire y de la tierra, y al ser humano; el séptimo día reposa."),
    ("Gn 2:4", "Gn 2:17", "El hombre en el huerto de Edén",
     "Dios forma al hombre del polvo, planta un huerto en Edén y le prohíbe comer del árbol de la ciencia del bien y del mal."),
    ("Gn 2:18", "Gn 2:25", "La formación de la mujer",
     "El hombre pone nombre a los animales y Dios forma a la mujer de su costilla."),
    ("Gn 3:1", "Gn 3:13", "La serpiente y el fruto prohibido",
     "La serpiente habla con la mujer, ella y el hombre comen del árbol y Dios les pregunta qué han hecho."),
    ("Gn 3:14", "Gn 3:24", "Las sentencias y la salida del huerto",
     "Dios se dirige a la serpiente, a la mujer y al hombre, y los saca del huerto de Edén."),
    ("Gn 4:1", "Gn 4:8", "Caín y Abel",
     "Nacen Caín y Abel, ambos presentan ofrendas y Caín mata a su hermano."),
    ("Gn 4:9", "Gn 4:16", "Caín errante",
     "Dios pregunta a Caín por Abel, lo maldice y Caín se va a la tierra de Nod."),
    ("Gn 4:17", "Gn 4:26", "Los descendientes de Caín y el nacimiento de Set",
     "Se enumeran los descendientes de Caín hasta los hijos de Lamec, y nacen Set y Enós."),
    ("Gn 5:1", "Gn 5:11", "De Adán a Enós",
     "Comienza la lista de generaciones de Adán con las edades de Adán, Set y Enós."),
    ("Gn 5:12", "Gn 5:20", "De Cainán a Jared",
     "Sigue la lista con las edades de Cainán, Mahalaleel y Jared."),
    ("Gn 5:21", "Gn 5:32", "De Enoc a Noé",
     "La lista llega a Enoc, Matusalén, Lamec y Noé y a los tres hijos de Noé."),
    ("Gn 6:1", "Gn 6:8", "La maldad de los hombres",
     "Los hijos de Dios toman mujeres de las hijas de los hombres y Dios decide raer al hombre, pero Noé halla gracia."),
    ("Gn 6:9", "Gn 6:22", "La orden de construir el arca",
     "Dios anuncia a Noé el diluvio y le da las medidas del arca y lo que debe meter en ella."),
    ("Gn 7:1", "Gn 7:16", "La entrada en el arca",
     "Noé, su familia y los animales entran en el arca y comienza el diluvio."),
    ("Gn 7:17", "Gn 8:5", "Las aguas crecen y decrecen",
     "Las aguas cubren los montes y mueren los seres vivos; después Dios se acuerda de Noé y las aguas bajan."),
    ("Gn 8:6", "Gn 8:19", "Las aves y la salida del arca",
     "Noé suelta un cuervo y una paloma y, cuando la tierra se seca, sale del arca con todos."),
    ("Gn 8:20", "Gn 9:7", "El altar de Noé y la bendición",
     "Noé ofrece holocaustos, Dios promete no volver a maldecir la tierra y bendice a Noé y a sus hijos."),
    ("Gn 9:8", "Gn 9:17", "El pacto y el arco en las nubes",
     "Dios establece un pacto con Noé y con los seres vivos, y pone el arco en las nubes como señal."),
    ("Gn 9:18", "Gn 9:29", "Noé y sus hijos después del diluvio",
     "Noé planta una viña y se embriaga; Cam ve su desnudez, Noé maldice a Canaán y muere a los 950 años."),
    ("Gn 10:1", "Gn 10:12", "Los hijos de Jafet y de Cam",
     "Se enumeran los descendientes de Jafet y los de Cam por Cus, entre ellos Nimrod."),
    ("Gn 10:13", "Gn 10:20", "Los descendientes de Mizraim y de Canaán",
     "Siguen los descendientes de Cam por Mizraim y Canaán y el territorio de los cananeos."),
    ("Gn 10:21", "Gn 10:32", "Los hijos de Sem",
     "Se enumeran los descendientes de Sem, incluidos Heber, Péleg y los hijos de Joctán."),
    ("Gn 11:1", "Gn 11:9", "La torre de Babel",
     "Los hombres edifican una ciudad y una torre, y Dios confunde su lengua y los esparce."),
    ("Gn 11:10", "Gn 11:26", "De Sem a Taré",
     "Lista de generaciones de Sem hasta Taré con la edad de cada uno al engendrar y los años que vivió después."),
    ("Gn 11:27", "Gn 11:32", "La familia de Taré",
     "Se presentan los hijos de Taré, Sarai y Milca, y Taré sale de Ur con los suyos hasta Harán, donde muere."),
]
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


def leer_vpl(ruta_zip, libro="GEN", maxcap=MAXCAP):
    """Devuelve {(cap, vers): texto} del libro pedido (código VPL: GEN, EXO)."""
    with zipfile.ZipFile(ruta_zip) as z:
        nombre = next(n for n in z.namelist() if n.endswith("_vpl.txt"))
        texto = z.read(nombre).decode("utf-8-sig")
    v = {}
    for linea in texto.splitlines():
        m = re.match(libro + r" (\d+):(\d+) (.*)", linea)
        if m and int(m.group(1)) <= maxcap:
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

    def ref_gen(s):
        m = re.match(r"GEN (\d+):(\d+)$", s.strip())
        return (int(m.group(1)), int(m.group(2))) if m and int(m.group(1)) <= MAXCAP else None

    # Formas RV1909 de cada persona: tabla fija (Gn 1–11), forzadas, o detectadas en sus versículos.
    def cargar_pv():
        filas = []
        for r in leer_csv(obtener("pv", sin_red)):
            ref = ref_gen(r["reference_id"])
            if not ref:
                continue
            for viejo, cap, nuevo in g2.PV_REASIGNAR:
                if r["person_id"] == viejo and ref[0] == cap:
                    r = dict(r, person_id=nuevo)
            filas.append(r)
        return filas
    pv_filas = cargar_pv()
    auto = defaultdict(Counter)
    for r in pv_filas:
        p = r["person_id"]
        if p in g2.EXCLUIR_PERSONAS or p in g2.SIN_NOMBRE_BD or p in NOMBRES or p in g2.FORMAS_FORZADAS:
            continue
        f, _ = na.mejor_forma(r["person_label"], rv.get(ref_gen(r["reference_id"]), ""))
        if f and f not in g2.FORMAS_EXCLUIDAS and not f.isupper():
            auto[p][f] += 1
    FORMAS = {p: [n] for p, n in NOMBRES.items()}
    FORMAS.update({p: [w for w, _ in c.most_common()] for p, c in auto.items()})
    FORMAS.update(g2.FORMAS_FORZADAS)
    FORMAS.update({p: [v[2]] for p, v in g2.PERSONAS_NUEVAS.items()})
    for p, fs in FORMAS.items():
        vistos_f, limpio = set(), []
        for f in fs:
            if sin_acentos(f) not in vistos_f:
                vistos_f.add(sin_acentos(f)); limpio.append(f)
        FORMAS[p] = limpio

    def forma_busqueda(p):
        return [SOLO_LXX[p][0]] if p in SOLO_LXX else FORMAS.get(p, [])

    # Capítulos
    capitulos = []
    for c in range(1, MAXCAP + 1):
        vs = sorted(v for (cc, v) in rv if cc == c)
        if vs != list(range(1, len(vs) + 1)):
            errores.append(f"Gn {c}: numeración de versículos no continua")
        capitulos.append({"libro": "Gn", "cap": c,
                          "versiculos": [{"n": v, "texto": rv[(c, v)]} for v in vs]})

    # Relaciones de BibleData en Génesis

    candidatas = {}  # (de, a, tipo) -> dict
    descartadas = Counter()
    for r in rels:
        ref = ref_gen(r["reference_id"])
        if not ref:
            continue
        p1, t, p2 = r["person_id_1"], r["relationship_type"].strip().lower(), r["person_id_2"]
        reasignada = False
        for viejo, cap, nuevo_id in g2.REL_REASIGNAR:  # esposas de Esaú: no se armonizan (Gn 36)
            if ref[0] == cap and viejo in (p1, p2):
                p1, p2 = (nuevo_id if p1 == viejo else p1), (nuevo_id if p2 == viejo else p2)
                reasignada = True
        sexo2 = per.get(p2, {}).get("sex", "") or ("female" if p2 in g2.PERSONAS_NUEVAS else "")
        if t == "father":
            de, a, tipo = p1, p2, "padre"
        elif t == "mother":
            de, a, tipo = p1, p2, "madre"
        elif t in ("son", "daughter"):
            de, a, tipo = p2, p1, ("madre" if sexo2 == "female" else "padre")
        elif t in ("husband", "wife", "concubine", "concubinator"):
            de, a = sorted((p1, p2)); tipo = "conyuge"
        else:
            descartadas[t] += 1
            continue
        cert = "explicito" if r["relationship_category"].strip() == "explicit" else "inferido"
        nuevo = {"de": de, "a": a, "tipo": tipo, "ref": gn(ref), "certeza": cert,
                 "fuente": "bibledata", "nota": "" if reasignada else r["relationship_notes"].strip()}
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
                    if any(nombra(verso, h) for h in forma_busqueda(x["a"])) and re.search(r"engendr|begot", verso):
                        subidas += x["certeza"] != "explicito"
                        x.update(certeza="explicito", ref=gn(ref), fuente=fuente,
                                 nota="Confirmada por la edad al engendrar en este versículo.")
    # (c) edad «al nacer …» escrita en el versículo: el padre de los hijos nombrados en él pasa a explícito.
    for p, tipo, ref, *_resto, evento in g2.EDADES_EVENTO:
        if not evento.startswith("al nacer"):
            continue
        verso = rv.get(ref, "")
        for x in candidatas.values():
            if x["de"] == p and x["tipo"] == "padre" and any(nombra(verso, h) for h in forma_busqueda(x["a"])):
                subidas += x["certeza"] != "explicito"
                x.update(certeza="explicito", ref=gn(ref), fuente="rv1909",
                         nota="Confirmada por la edad del padre al nacer el hijo, escrita en este versículo.")
    # Comprobación: toda relación con fuente de texto nombra al hijo en su versículo.
    for x in candidatas.values():
        if x["fuente"] in ("rv1909", "brenton"):
            textos = rv if x["fuente"] == "rv1909" else br
            if x["tipo"] != "conyuge" and not x.get("cita") and not any(
                    nombra(textos.get(parse_gn(x["ref"]), ""), h) for h in forma_busqueda(x["a"])):
                errores.append(f"Hijo «{x['a']}» no está en {x['ref']} ({x['fuente']})")
    for x in candidatas.values():
        if x["certeza"] == "inferido" and x["tipo"] in ("padre", "madre"):
            verso = rv.get(parse_gn(x["ref"]), "")
            if (any(nombra(verso, f) for f in forma_busqueda(x["de"])) and any(nombra(verso, f) for f in forma_busqueda(x["a"]))
                    and re.search(r"engendr|pari[oó]", sin_acentos(verso))):
                subidas += 1
                x.update(certeza="explicito", fuente="rv1909",
                         nota=(x["nota"] + " " if x["nota"] else "") +
                         "BibleData la marca inferida; el versículo nombra a ambos.")
    # Personas que el texto menciona sin nombre (RV1909), con su relación y cita literal.
    sin_nombre = {}  # id -> (nombre, sexo, nota)
    def anadir_sn(pid, nombre, sexo, nota, rels_sn):
        sin_nombre[pid] = (nombre, sexo, nota)
        for de, a, tipo, ref, cert, cita in rels_sn:
            if tipo == "conyuge":
                de, a = sorted((de, a))
            candidatas[(de, a, tipo)] = {"de": de, "a": a, "tipo": tipo, "ref": gn(ref), "certeza": cert,
                                         "fuente": "rv1909", "nota": "", "cita": cita}
    anadir_sn("Esposa_de_Cain", "Esposa de Caín", "f", "", [
        ("Cain_1", "Esposa_de_Cain", "conyuge", (4, 17), "explicito", "conoció Caín á su mujer"),
        ("Esposa_de_Cain", "Enoch_1", "madre", (4, 17), "explicito", "la cual concibió y parió á Henoch")])
    anadir_sn("Esposa_de_Noe", "Esposa de Noé", "f", "", [
        ("Noah_1", "Esposa_de_Noe", "conyuge", (7, 13), "explicito", "la mujer de Noé")]
        + [("Esposa_de_Noe", h, "madre", (7, 13), "inferido", "") for h in ("Shem_1", "Ham_1", "Japheth_1")])
    for h, nom in (("Shem_1", "Sem"), ("Ham_1", "Cam"), ("Japheth_1", "Jafet")):
        anadir_sn(f"Esposa_de_{nom}", f"Esposa de {nom}", "f",
                  "El versículo solo dice «las tres mujeres de sus hijos»; no nombra a ninguna ni dice "
                  "cuál es de quién: se asigna una a cada hijo.",
                  [(h, f"Esposa_de_{nom}", "conyuge", (7, 13), "explicito", "las tres mujeres de sus hijos")])
    cita_hh = "engendró hijos é hijas"
    for p, trads in EDADES.items():
        for tipo, ref, _ in trads.get("TM", []):
            if tipo == "restantes" and cita_hh in rv.get(ref, ""):
                anadir_sn(f"Otros_hijos_{p}", f"Otros hijos e hijas de {MODERNO[p]}", "?",
                          "Grupo sin nombre: el texto solo dice que engendró hijos e hijas.",
                          [(p, f"Otros_hijos_{p}", "padre", ref, "explicito", cita_hh)])
    # Gn 12–50: personas sin nombre añadidas y las que BibleData ya trae sin nombre.
    for pid, nombre, sexo, nota, rels_sn in g2.SIN_NOMBRE_EXTRA:
        anadir_sn(pid, nombre, sexo, nota, rels_sn)
    for pid, (nombre, sexo) in g2.SIN_NOMBRE_BD.items():
        sin_nombre[pid] = (nombre, sexo, "El texto no da su nombre.")
    # Concubinas y siervas dadas «por mujer»: cónyuge, con nota de cómo las llama el texto.
    refs_pv = defaultdict(set)
    for r in pv_filas:
        refs_pv[r["person_id"]].add(ref_gen(r["reference_id"]))
    trato_mujer = {}
    for varon, mujer, ref, cita in g2.CONYUGES_EXTRA:
        de, a = sorted((varon, mujer))
        vistos_t = []
        for t in g2.TRATO_MUJER:
            for r in sorted(refs_pv[mujer] | {ref}):
                v = rv.get(r, "")
                if t in v and any(nombra(v, f) for f in forma_busqueda(mujer)):
                    vistos_t.append(f"«{t}» (Gn {r[0]}:{r[1]})"); break
        nota = "El texto la llama " + ", ".join(vistos_t) + "." if vistos_t else ""
        trato_mujer[mujer] = nota
        previo = candidatas.get((de, a, "conyuge"), {})
        candidatas[(de, a, "conyuge")] = {"de": de, "a": a, "tipo": "conyuge", "ref": gn(ref),
                                          "certeza": "explicito", "fuente": "rv1909",
                                          "nota": nota + (" " + previo["nota"] if previo.get("nota") else ""),
                                          "cita": cita}
    # Auditoría de matrimonios: cada uno con versículo y cita literal.
    for k in [k for k in candidatas if k[2] == "conyuge" and (k[0], k[1]) in g2.QUITAR_CONYUGE]:
        del candidatas[k]
    matrimonios_nuevos = 0
    for x1, x2, ref, cita, nota in g2.MATRIMONIOS:
        de, a = sorted((x1, x2))
        previo = candidatas.get((de, a, "conyuge"))
        matrimonios_nuevos += previo is None
        nota_previa = previo["nota"] if previo and previo["fuente"] == "rv1909" else ""
        candidatas[(de, a, "conyuge")] = {"de": de, "a": a, "tipo": "conyuge", "ref": gn(ref), "certeza": "explicito",
                                          "fuente": "rv1909", "nota": (nota + " " + nota_previa).strip(), "cita": cita}
    for de, a, tipo, ref, cita, nota in g2.RELACIONES_EXTRA:
        candidatas[(de, a, tipo)] = {"de": de, "a": a, "tipo": tipo, "ref": gn(ref), "certeza": "explicito",
                                     "fuente": "rv1909", "nota": nota, "cita": cita}
    # Hijos de Jacob: madre y versículo de nacimiento (Gn 29–30, 35).
    comprobacion_jacob = []
    for hijo, madre, ref in g2.HIJOS_JACOB:
        v = rv.get(ref, "")
        if not any(nombra(v, f) for f in forma_busqueda(hijo)):
            errores.append(f"{hijo} no aparece en {gn(ref)}")
        previo = candidatas.get((madre, hijo, "madre"))
        candidatas[(madre, hijo, "madre")] = {"de": madre, "a": hijo, "tipo": "madre", "ref": gn(ref),
                                              "certeza": "explicito", "fuente": "rv1909",
                                              "nota": "Versículo del nacimiento." if not previo else previo["nota"]}
        padre = candidatas.get(("Jacob_1", hijo, "padre"))
        if not padre:
            errores.append(f"Falta Jacob padre de {hijo}")
        otras = [x["de"] for x in candidatas.values() if x["a"] == hijo and x["tipo"] == "madre" and x["de"] != madre]
        if otras:
            errores.append(f"{hijo} tiene otra madre: {otras}")
        comprobacion_jacob.append(f"{hijo}: madre {madre} ({gn(ref)}), padre Jacob "
                                  f"({padre['ref'] if padre else 'FALTA'})")
    for x in candidatas.values():
        if x.get("cita") and x["cita"] not in rv.get(parse_gn(x["ref"]), ""):
            errores.append(f"Cita de relación no literal: {x['de']}→{x['a']} {x['ref']} {x['cita']!r}")
    # Comprobaciones pedidas sobre Milca, Isca y Sarai
    for hija in ("Milcah_1", "Iscah_1"):
        if candidatas.get(("Haran_1", hija, "padre"), {}).get("ref") != "Gn 11:29":
            errores.append(f"Falta Harán padre de {hija} en Gn 11:29")
    if any(x["a"] == "Sarai_1" and x["tipo"] in ("padre", "madre") and parse_gn(x["ref"])[0] <= 11
           for x in candidatas.values()):
        errores.append("Sarai no debería tener progenitor en Gn 1–11")
    relaciones = sorted(candidatas.values(), key=lambda x: (parse_gn(x["ref"]), x["de"], x["a"]))

    # Personas
    refs = defaultdict(set)
    for x in relaciones:
        refs[x["de"]].add(parse_gn(x["ref"])); refs[x["a"]].add(parse_gn(x["ref"]))
    for p, trads in EDADES.items():
        for trad, items in trads.items():
            for _, ref, _ in items:
                refs[p].add(ref)
    for p, _, ref, *_ in g2.EDADES_EVENTO:
        refs[p].add(ref)
    for p, rs in refs_pv.items():
        if p not in g2.EXCLUIR_PERSONAS:
            refs[p] |= rs
    for p in list(refs):
        if p in g2.EXCLUIR_PERSONAS:
            del refs[p]
        elif not FORMAS.get(p) and p not in sin_nombre and p not in SOLO_LXX:
            errores.append(f"Persona sin forma RV1909: {p}")
    personas, fallos_nombre, sin_moderno = [], [], []
    for p in sorted(refs, key=lambda q: (min(refs[q]), q)):
        lista = sorted(refs[p])
        if p in sin_nombre:
            nombre, sexo, nota = sin_nombre[p]
            rol = g2.ROLES.get(p, ("",))[0]
            if p in g2.ROLES and g2.ROLES[p][2] not in rv.get(g2.ROLES[p][1], ""):
                errores.append(f"Rol de {p}: cita no literal")
            personas.append({"id": p, "nombre": nombre, "nombre_rv1909": None, "formas_rv1909": [], "rol": rol,
                             "sin_nombre": True,
                             "sexo": sexo, "primera_ref": gn(lista[0]), "refs": [gn(r) for r in lista],
                             "nota": nota, "ref_mencion": gn(lista[0])})
            continue
        formas = forma_busqueda(p)
        if not formas:
            continue  # ya registrado como error
        nombre = formas[0]
        fuente_v = br if p in SOLO_LXX else rv
        pats = [re.compile(r"(?<!\w)%s(?!\w)" % re.escape(sin_acentos(f))) for f in formas]
        con_nombre = [r for r in lista if any(pt.search(sin_acentos(fuente_v.get(r, ""))) for pt in pats)]
        primera = con_nombre[0] if con_nombre else lista[0]
        if not con_nombre:
            fallos_nombre.append(f"{p} «{nombre}» no aparece en {gn(primera)}")
        sexo = {"male": "m", "female": "f"}.get(per.get(p, {}).get("sex", ""), "?")
        if p in g2.PERSONAS_NUEVAS:
            sexo = g2.PERSONAS_NUEVAS[p][1]
        nota = SOLO_LXX[p][1] if p in SOLO_LXX else ""
        if p in g2.PERSONAS_NUEVAS:
            nota = g2.PERSONAS_NUEVAS[p][3]
        if p in g2.NOTAS_PERSONA:
            nota = (nota + " " + g2.NOTAS_PERSONA[p]).strip()
        if (re.search(r"(im|eo)$", nombre) and p not in ("Dodanim_1", "Kittim_1", "Mizraim_1")
                and lista[0][0] == 10):
            nota = GENTILICIO
        if p == "Kenan_1":
            nota = "Distinto del Cainán hijo de Arfaxad que solo aparece en la Septuaginta (Gn 11:12-13)."
        if p in g2.NOTAS_NOMBRE:
            nota = (g2.NOTAS_NOMBRE[p] + " " + nota).strip()
        if p in trato_mujer and trato_mujer[p]:
            nota = (nota + " " + trato_mujer[p]).strip()
        moderno = {"Abram_1": "Abraham", "Sarai_1": "Sara", "Adah_2": "Ada"}.get(p) or MODERNO.get(p) or g2.MODERNO2.get(p)
        if not moderno:
            sin_moderno.append(nombre)
            moderno = nombre
        forma_rv = None if p in SOLO_LXX else nombre
        if forma_rv and forma_rv != moderno:
            nota = f"En la Reina-Valera 1909: {'/'.join(formas)}." + (" " + nota if nota else "")
        rol = ""
        if p in g2.ROLES:
            rol, rref, rcita = g2.ROLES[p]
            if rcita not in rv.get(rref, ""):
                errores.append(f"Rol de {p}: «{rcita}» no está en {gn(rref)}")
            primera = rref
        personas.append({"id": p, "nombre": moderno, "nombre_rv1909": forma_rv, "rol": rol,
                         "formas_rv1909": [] if p in SOLO_LXX else formas, "sin_nombre": False,
                         "sexo": sexo,
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

    # Edades escritas en Gn 12–50 (TM desde RV1909, LXX desde Brenton).
    for p, tipo, ref, i_tm, i_lxx, evento in g2.EDADES_EVENTO:
        for trad, textos, idioma, fuente, idx in (("TM", rv, "es", "rv1909", i_tm), ("LXX", br, "en", "brenton", i_lxx)):
            hallados = cifras(textos.get(ref, ""), idioma)
            if idx >= len(hallados):
                (errores if trad == "TM" else avisos).append(f"{p} {trad} {gn(ref)}: no hay cifra n.º {idx}")
                continue
            cita = hallados[idx]
            e = {"persona": p, "tipo": tipo, "tradicion": trad,
                 "valor": numeral_a_numero(re.sub(r"\s+(años|years)$", "", cita, flags=re.I), idioma),
                 "ref": gn(ref), "certeza": "texto", "fuente": fuente, "cita": cita, "nota": ""}
            if tipo == "en_evento":
                e["evento"] = evento
            edades.append(e)

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

    # ------------------------------------------------------------ pasajes
    pasajes, tam_pasaje = [], []
    orden = sorted(rv)
    pos = {k: i for i, k in enumerate(orden)}
    esperado = 0
    todos_pasajes = [p + (g2.SECCION_1,) for p in PASAJES] + g2.PASAJES2
    for i, (ini, fin, titulo, resumen, seccion) in enumerate(todos_pasajes, 1):
        a, b = parse_gn(ini), parse_gn(fin)
        if a not in pos or b not in pos or pos[a] != esperado or pos[b] < pos[a]:
            errores.append(f"Pasaje {ini}–{fin}: hueco, solape o desorden (se esperaba {gn(orden[min(esperado, len(orden)-1)])})")
        else:
            esperado = pos[b] + 1
        pasajes.append({"id": f"gn-{i:02d}", "libro": "Gn", "inicio": ini, "fin": fin, "titulo": titulo,
                        "titulo_origen": "editorial", "resumen": resumen, "seccion": seccion})
        tam_pasaje.append(pos.get(b, 0) - pos.get(a, 0) + 1)
    if esperado != len(orden):
        errores.append(f"Los pasajes no cubren hasta {gn(orden[-1])}")

    # ------------------------------------------------------------ menciones
    pv = defaultdict(dict)  # ref -> {persona: n.º de apariciones según BibleData}
    for r in cargar_pv():
        ref = ref_gen(r["reference_id"])
        if ref:
            try:
                n = int(r["person_label_count"] or 1)
            except ValueError:
                n = 1
            pv[ref][r["person_id"]] = pv[ref].get(r["person_id"], 0) + n
    por_forma = defaultdict(list)
    for p in personas:
        for f in p["formas_rv1909"]:
            por_forma[sin_acentos(f)].append(p["id"])
    sitio = {p["id"]: {parse_gn(r) for r in p["refs"]} for p in personas}
    formas = sorted(por_forma, key=len, reverse=True)  # largas primero (Tubal-Caín antes que Tubal/Caín)

    def u16(s, i):
        return len(s[:i].encode("utf-16-le")) // 2

    menciones, ambiguos, no_situados = [], [], Counter()
    for ref in orden:
        texto = rv[ref]
        # normalización carácter a carácter para que los índices coincidan con el original
        norm = "".join(n if len(n := sin_acentos(ch)) == 1 else ch.lower() for ch in texto)
        if len(norm) != len(texto):
            errores.append(f"Normalización altera longitud en {gn(ref)}"); continue
        ocupado = [False] * len(texto)
        for forma in formas:
            hallados = [m for m in re.finditer(r"(?<!\w)%s(?!\w)" % re.escape(forma), norm)
                        if not any(ocupado[m.start():m.end()]) and texto[m.start()].isupper()]
            if not hallados:
                continue
            cands = [q for q in por_forma[forma] if q in pv[ref] or ref in sitio[q]]
            if not cands:
                no_situados[forma] += len(hallados); continue
            # Uso como lugar («en Harán», «hasta Harán», «tierra de Canaán»): no es mención de persona.
            lugar = [m for m in hallados if forma in ("haran", "canaan") and re.search(r"(?<!\w)(en|hasta|tierra de)\s+$", norm[:m.start()])]
            if lugar:
                no_situados[forma + " (lugar)"] += len(lugar)
                hallados = [m for m in hallados if m not in lugar]
            if not hallados:
                continue
            if len(cands) > 1:
                ambiguos.append(f"{gn(ref)} «{texto[hallados[0].start():hallados[0].end()]}» "
                                f"×{len(hallados)} candidatos {cands}")
                continue
            for m in hallados:
                for j in range(m.start(), m.end()):
                    ocupado[j] = True
                menciones.append({"ref": gn(ref), "persona": cands[0],
                                  "inicio": u16(texto, m.start()), "fin": u16(texto, m.end())})
    menciones.sort(key=lambda x: (parse_gn(x["ref"]), x["inicio"]))
    # verificación de menciones
    forma_de = {p["id"]: {sin_acentos(f) for f in p["formas_rv1909"]} for p in personas}
    ultimo = {}
    for x in menciones:
        t = rv[parse_gn(x["ref"])]
        b = t.encode("utf-16-le")[2 * x["inicio"]:2 * x["fin"]].decode("utf-16-le")
        if sin_acentos(b) not in forma_de[x["persona"]]:
            errores.append(f"Mención no coincide {x}: {b!r}")
        if x["ref"] in ultimo and x["inicio"] < ultimo[x["ref"]]:
            errores.append(f"Menciones solapadas en {x['ref']}")
        ultimo[x["ref"]] = x["fin"]

    # ------------------------------------------------------------ listas «hijos de X» (Gn 36 y 46:8-27)
    sexo_de = {p["id"]: p["sexo"] for p in personas}
    tiene = {(x["de"], x["a"]) for x in relaciones if x["tipo"] in ("padre", "madre")}
    progenitor_tipo = defaultdict(set)
    for x in relaciones:
        if x["tipo"] in ("padre", "madre"):
            progenitor_tipo[(x["a"], x["tipo"])].add(x["de"])
    men_por_ref = defaultdict(list)
    for m in menciones:
        men_por_ref[m["ref"]].append(m)
    listas_dif, padres_nuevos = [], 0
    for ref in [r for r in orden if r[0] == 36 or (r[0] == 46 and 8 <= r[1] <= 27)]:
        texto, R = rv[ref], gn(ref)
        for h in re.finditer(r"hijos de ", texto):
            ms = sorted(men_por_ref[R], key=lambda m: m["inicio"])
            padre_m = next((m for m in ms if h.end() <= m["inicio"] <= h.end() + 1), None)
            if not padre_m:
                continue
            resto = texto[padre_m["fin"]:]
            fin_seg = len(texto)
            for corte in (re.search(r"[.;]", resto), re.search(r"hijos de ", resto)):
                if corte:
                    fin_seg = min(fin_seg, padre_m["fin"] + corte.start())
            cab = re.match(r"(,[^:.;]*)?(\s+fueron)?\s*:?", resto)
            if not re.match(r"(,[^:.;]*)?:|\s+fueron", resto):
                continue  # no es una lista («Estos son los hijos de Lea, los cuales parió…»)
            ini_seg = padre_m["fin"] + cab.end()
            hijos = [m for m in ms if ini_seg <= m["inicio"] < fin_seg and m["persona"] != padre_m["persona"]
                     and not re.search(r"((hij[oa]|mujer|hermana|padre) de|á)\s+$", texto[:m["inicio"]])]
            tipo = "madre" if sexo_de.get(padre_m["persona"]) == "f" else "padre"
            for m in hijos:
                if (padre_m["persona"], m["persona"]) in tiene:
                    continue
                otros = progenitor_tipo[(m["persona"], tipo)]
                if otros:
                    listas_dif.append(f"{R}: {m['persona']} en la lista de {padre_m['persona']}, pero su {tipo} registrado es {sorted(otros)} (no se cambia)")
                    continue
                cita = texto[h.start():padre_m["fin"]]
                nueva = {"de": padre_m["persona"], "a": m["persona"], "tipo": tipo, "ref": R, "certeza": "explicito",
                         "fuente": "rv1909", "nota": "Añadida desde la lista del versículo.", "cita": cita}
                relaciones.append(nueva); tiene.add((nueva["de"], nueva["a"]))
                progenitor_tipo[(m["persona"], tipo)].add(nueva["de"])
                padres_nuevos += 1
                listas_dif.append(f"{R}: {m['persona']} añadido como hijo de {padre_m['persona']} («{cita}»)")
    # ------------------------------------------------------------ padres sin vínculo conyugal
    conyuges = {tuple(sorted((x["de"], x["a"]))) for x in relaciones if x["tipo"] == "conyuge"}
    padres_de = defaultdict(lambda: {"padre": set(), "madre": set()})
    for x in relaciones:
        if x["tipo"] in ("padre", "madre"):
            padres_de[x["a"]][x["tipo"]].add(x["de"])
    sin_vinculo = defaultdict(list)
    for hijo, pm in padres_de.items():
        for pa in pm["padre"]:
            for ma in pm["madre"]:
                if tuple(sorted((pa, ma))) not in conyuges:
                    sin_vinculo[(pa, ma)].append(hijo)
    for (pa, ma), hijos in sin_vinculo.items():
        nota = g2.SIN_PAREJA_NOTA.get((pa, ma))
        if not nota:
            errores.append(f"Padres sin vínculo conyugal y sin explicación: {pa} + {ma} → {hijos}")
            continue
        for x in relaciones:
            if x["a"] in hijos and x["de"] in (pa, ma) and nota not in x["nota"]:
                x["nota"] = (x["nota"] + " " + nota).strip()
    relaciones.sort(key=lambda x: (parse_gn(x["ref"]), x["de"], x["a"]))
    for x in relaciones:
        if x.get("cita") and x["cita"] not in rv.get(parse_gn(x["ref"]), ""):
            errores.append(f"Cita de relación no literal: {x['de']}→{x['a']} {x['ref']} {x['cita']!r}")
        for q in (x["de"], x["a"]):
            if q not in sexo_de:
                errores.append(f"Relación a persona inexistente: {q}")
    con_rel = {q for x in relaciones for q in (x["de"], x["a"])}
    sueltas = [p for p in personas if p["id"] not in con_rel]
    for p in sueltas:
        if not p.get("rol"):
            errores.append(f"Persona sin relación ni rol: {p['id']}")

    # ------------------------------------------------------------ Éxodo 1–40 (herramientas/exodo.py)
    rv_ex = leer_vpl(obtener("rv", sin_red), "EXO", 40)
    br_ex = leer_vpl(obtener("br", sin_red), "EXO", 40)
    pv_ex = [r for r in leer_csv(obtener("pv", sin_red)) if re.match(r"EXO \d+:\d+$", r["reference_id"].strip())]
    n_rel_gn, n_per_gn, n_ed_gn = len(relaciones), len(personas), len(edades)
    EXO = exodo.construir(dict(rv=rv_ex, br=br_ex, rels=rels, pv_filas=pv_ex, per=per, personas=personas,
                               relaciones=relaciones, edades=edades, sin_acentos=sin_acentos,
                               numeral=numeral_a_numero, ES=ES, EN=EN, errores=errores, avisos=avisos))
    capitulos += EXO["capitulos"]
    pasajes += EXO["pasajes"]
    menciones_gn = menciones
    menciones = menciones + EXO["menciones"]

    # ------------------------------------------------------------ Levítico 1–27 (herramientas/levitico.py)
    rv_lv = leer_vpl(obtener("rv", sin_red), "LEV", 27)
    br_lv = leer_vpl(obtener("br", sin_red), "LEV", 27)
    pv_lv = [r for r in leer_csv(obtener("pv", sin_red)) if re.match(r"LEV \d+:\d+$", r["reference_id"].strip())]
    LEV = levitico.construir(dict(rv=rv_lv, br=br_lv, rels=rels, pv_filas=pv_lv, per=per, personas=personas,
                                  relaciones=relaciones, edades=edades, sin_acentos=sin_acentos,
                                  numeral=numeral_a_numero, ES=ES, EN=EN, errores=errores, avisos=avisos))
    capitulos += LEV["capitulos"]
    pasajes += LEV["pasajes"]
    menciones = menciones + LEV["menciones"]

    # ------------------------------------------------------------ Números 1–36 (herramientas/numeros.py)
    rv_nm = leer_vpl(obtener("rv", sin_red), "NUM", 36)
    br_nm = leer_vpl(obtener("br", sin_red), "NUM", 36)
    pv_nm = [r for r in leer_csv(obtener("pv", sin_red)) if re.match(r"NUM \d+:\d+$", r["reference_id"].strip())]
    NUM = numeros.construir(dict(rv=rv_nm, br=br_nm, rels=rels, pv_filas=pv_nm, per=per, personas=personas,
                                 relaciones=relaciones, edades=edades, sin_acentos=sin_acentos,
                                 numeral=numeral_a_numero, ES=ES, EN=EN, errores=errores, avisos=avisos))
    capitulos += NUM["capitulos"]
    pasajes += NUM["pasajes"]
    menciones = menciones + NUM["menciones"]

    # ------------------------------------------------------------ Deuteronomio 1–34 (herramientas/deuteronomio.py)
    rv_dt = leer_vpl(obtener("rv", sin_red), "DEU", 34)
    br_dt = leer_vpl(obtener("br", sin_red), "DEU", 34)
    pv_dt = [r for r in leer_csv(obtener("pv", sin_red)) if re.match(r"DEU \d+:\d+$", r["reference_id"].strip())]
    DEU = deuteronomio.construir(dict(rv=rv_dt, br=br_dt, rels=rels, pv_filas=pv_dt, per=per, personas=personas,
                                      relaciones=relaciones, edades=edades, sin_acentos=sin_acentos,
                                      numeral=numeral_a_numero, ES=ES, EN=EN, errores=errores, avisos=avisos))
    capitulos += DEU["capitulos"]
    pasajes += DEU["pasajes"]
    menciones = menciones + DEU["menciones"]

    # ------------------------------------------------------------ Josué 1–24 (herramientas/josue.py)
    rv_jos = leer_vpl(obtener("rv", sin_red), "JOS", 24)
    br_jos = josue.br_a_rv(leer_vpl(obtener("br", sin_red), "JOS", 24))  # único punto de versificación de Brenton
    pv_jos = [r for r in leer_csv(obtener("pv", sin_red)) if re.match(r"JOS \d+:\d+$", r["reference_id"].strip())]
    JOS = josue.construir(dict(rv=rv_jos, br=br_jos, rels=rels, pv_filas=pv_jos, per=per, personas=personas,
                               relaciones=relaciones, edades=edades, sin_acentos=sin_acentos,
                               numeral=numeral_a_numero, ES=ES, EN=EN, errores=errores, avisos=avisos))
    capitulos += JOS["capitulos"]
    pasajes += JOS["pasajes"]
    menciones = menciones + JOS["menciones"]

    # ------------------------------------------------------------ Jueces 1–21 (herramientas/jueces.py)
    rv_jue = leer_vpl(obtener("rv", sin_red), "JDG", 21)
    br_jue = leer_vpl(obtener("br", sin_red), "JDG", 21)
    pv_jue = [r for r in leer_csv(obtener("pv", sin_red)) if re.match(r"JDG \d+:\d+$", r["reference_id"].strip())]
    JUE = jueces.construir(dict(rv=rv_jue, br=br_jue, rels=rels, pv_filas=pv_jue, per=per, personas=personas,
                                relaciones=relaciones, edades=edades, sin_acentos=sin_acentos,
                                numeral=numeral_a_numero, ES=ES, EN=EN, errores=errores, avisos=avisos))
    capitulos += JUE["capitulos"]
    pasajes += JUE["pasajes"]
    menciones = menciones + JUE["menciones"]

    # ------------------------------------------------------------ Rut 1–4 (herramientas/rut.py)
    rv_rut = leer_vpl(obtener("rv", sin_red), "RUT", 4)
    br_rut = leer_vpl(obtener("br", sin_red), "RUT", 4)
    pv_rut = [r for r in leer_csv(obtener("pv", sin_red)) if re.match(r"RUT \d+:\d+$", r["reference_id"].strip())]
    RUT = rut.construir(dict(rv=rv_rut, br=br_rut, rels=rels, pv_filas=pv_rut, per=per, personas=personas,
                             relaciones=relaciones, edades=edades, sin_acentos=sin_acentos,
                             numeral=numeral_a_numero, ES=ES, EN=EN, errores=errores, avisos=avisos))
    capitulos += RUT["capitulos"]
    pasajes += RUT["pasajes"]
    menciones = menciones + RUT["menciones"]

    # ------------------------------------------------------------ 1 Samuel 1–31 (herramientas/samuel1.py)
    rv_1s = leer_vpl(obtener("rv", sin_red), "1SA", 31)
    br_1s = samuel1.br_a_rv(leer_vpl(obtener("br", sin_red), "1SA", 31))  # único punto de versificación de Brenton
    pv_1s = [r for r in leer_csv(obtener("pv", sin_red)) if re.match(r"1SA \d+:\d+$", r["reference_id"].strip())]
    S1 = samuel1.construir(dict(rv=rv_1s, br=br_1s, rels=rels, pv_filas=pv_1s, per=per, personas=personas,
                                relaciones=relaciones, edades=edades, sin_acentos=sin_acentos,
                                numeral=numeral_a_numero, ES=ES, EN=EN, errores=errores, avisos=avisos))
    capitulos += S1["capitulos"]
    pasajes += S1["pasajes"]
    menciones = menciones + S1["menciones"]
    personas.sort(key=lambda p: (exodo.clave_ref(p["refs"][0]) if p["refs"] else (9, 0, 0), p["id"]))
    vistos_id = Counter(p["id"] for p in personas)
    errores.extend(f"Persona duplicada: {k}" for k, n in vistos_id.items() if n > 1)
    vistos_r = Counter((x["de"], x["a"], x["tipo"]) for x in relaciones)
    errores.extend(f"Relación duplicada entre libros: {k}" for k, n in vistos_r.items() if n > 1)

    # ------------------------------------------------------------ cronología relativa
    nombre_de = {p["id"]: p["nombre"] for p in personas}
    lv = lambda k: f"Lv {k[0]}:{k[1]}"  # noqa: E731
    nm = lambda k: f"Nm {k[0]}:{k[1]}"  # noqa: E731
    dt = lambda k: f"Dt {k[0]}:{k[1]}"  # noqa: E731
    jos = lambda k: f"Jos {k[0]}:{k[1]}"  # noqa: E731
    jue = lambda k: f"Jue {k[0]}:{k[1]}"  # noqa: E731
    rt = lambda k: f"Rut {k[0]}:{k[1]}"  # noqa: E731
    s1 = lambda k: f"1S {k[0]}:{k[1]}"  # noqa: E731
    texto_ref = {"TM": {**{gn(k): v for k, v in rv.items()}, **{exodo.ex(k): v for k, v in rv_ex.items()},
                        **{lv(k): v for k, v in rv_lv.items()}, **{nm(k): v for k, v in rv_nm.items()},
                        **{dt(k): v for k, v in rv_dt.items()}, **{jos(k): v for k, v in rv_jos.items()},
                        **{jue(k): v for k, v in rv_jue.items()}, **{rt(k): v for k, v in rv_rut.items()},
                        **{s1(k): v for k, v in rv_1s.items()}},
                 "LXX": {**{gn(k): v for k, v in br.items()}, **{exodo.ex(k): v for k, v in br_ex.items()},
                         **{lv(k): v for k, v in br_lv.items()}, **{nm(k): v for k, v in br_nm.items()},
                         **{dt(k): v for k, v in br_dt.items()}, **{jos(k): v for k, v in br_jos.items()},
                         **{jue(k): v for k, v in br_jue.items()}, **{rt(k): v for k, v in br_rut.items()},
                         **{s1(k): v for k, v in br_1s.items()}}}
    rango_pasaje = [(exodo.clave_ref(p["inicio"]), exodo.clave_ref(p["fin"]), p["id"]) for p in pasajes]

    def pasaje_de(ref):
        if not ref or not re.match(r"(Gn|Ex|Lv|Nm|Dt|Jos|Jue|Rut|1S) \d+:\d+", ref):
            return None
        k = exodo.clave_ref(ref)
        return next((pid for a0, b0, pid in rango_pasaje if a0 <= k <= b0), None)

    cronologia, vivos_diluvio, edades_usadas = cr.construir(
        edades, lambda q: nombre_de.get(q, q), texto_ref, numeral_a_numero, lambda s: s, pasaje_de, errores)
    for h in cronologia["hitos_sin_fecha"]:
        h["pasaje"] = pasaje_de(h["ref"])
    EV = {e["id"]: e for e in cronologia["eventos"]}
    for e in cronologia["eventos"]:
        for c, v in e["anios"].items():
            if v is None and c.startswith("TM") and "cainan11" not in e["id"]:
                errores.append(f"Evento sin año en TM: {e['id']} {c}")
    if len(cronologia["combinaciones"]) != 16:
        errores.append(f"Cronología: {len(cronologia['combinaciones'])} combinaciones (se esperaban 16)")
    ids_ev = Counter(e["id"] for e in cronologia["eventos"])
    errores.extend(f"Evento con id repetido: {k}" for k, n in ids_ev.items() if n > 1)
    for eid in ("ev-salida-egipto", "ev-nac-moises", "ev-nac-aaron", "ev-llegada-sinai", "ev-tabernaculo"):
        if eid not in ids_ev:
            errores.append(f"Cronología: falta {eid}")
    for h in ("Ex 6:16", "Ex 6:18", "Ex 6:20"):
        if not any(x["ref"] == h for x in cronologia["hitos_sin_fecha"]):
            errores.append(f"Cronología: falta el hito sin fecha {h}")
            if v is None and c.startswith("LXX"):
                errores.append(f"Evento sin año en LXX: {e['id']} {c}")
    for eid, comb, esperado in (("ev-diluvio", "TM|tare70|sem2|egipto", 1656), ("ev-diluvio", "LXX|tare70|sem2|egipto", 2242),
                                ("ev-nac-abram", "TM|tare70|sem2|egipto", 1948), ("ev-nac-abram", "TM|tare130|sem2|egipto", 2008),
                                ("ev-nac-isaac", "TM|tare70|sem2|egipto", 2048),
                                ("ev-salida-egipto", "TM|tare70|sem2|egipto", 2668),
                                ("ev-salida-egipto", "TM|tare130|sem2|canaan", 2513)):
        if eid not in EV:
            errores.append(f"Cronología: falta el evento {eid}"); continue
        if EV[eid]["anios"].get(comb) != esperado:
            errores.append(f"Cronología: {eid} {comb} = {EV[eid]['anios'][comb]}, se esperaba {esperado}")
    claves_edad = {(e["persona"], e["tipo"]) for e in edades}
    for persona, tipo, ref in edades_usadas:
        if (persona, tipo) not in claves_edad:
            errores.append(f"Edad usada inexistente: {persona} {tipo} {ref}")

    # ------------------------------------------------------------ lugares y mapa
    rutas = {}
    for k, (url, nombre) in lm.ARCHIVOS.items():
        ARCHIVOS[k] = (url, nombre)
        rutas[k] = obtener(k, sin_red)
    lugares, menciones_lugar, amb_lugar, desc_lugar, lineas_ob, lug_sin_forma, lug_sin_moderno = lm.construir_lugares(
        rv, menciones_gn, rutas, errores, avisos)
    for m in menciones_lugar:
        if m["ref"].startswith("Ex "):
            errores.append(f"Mención de Génesis con ref de Éxodo: {m}")
    lug_ex, men_lug_ex, info_lug_ex = exodo.construir_lugares(rv_ex, EXO["menciones"], rutas, lugares, errores, avisos, sin_acentos)
    lugares += lug_ex
    menciones_lugar += men_lug_ex
    lug_lv, men_lug_lv, info_lug_lv = levitico.construir_lugares(rv_lv, LEV["menciones"], rutas, lugares, errores, avisos,
                                                                sin_acentos)
    lugares += lug_lv
    menciones_lugar += men_lug_lv
    lug_nm, men_lug_nm, info_lug_nm = numeros.construir_lugares(rv_nm, NUM["menciones"], rutas, lugares, errores, avisos,
                                                               sin_acentos)
    lugares += lug_nm
    menciones_lugar += men_lug_nm
    lug_dt, men_lug_dt, info_lug_dt = deuteronomio.construir_lugares(rv_dt, DEU["menciones"], rutas, lugares, errores,
                                                                     avisos, sin_acentos)
    lugares += lug_dt
    menciones_lugar += men_lug_dt
    lug_jos, men_lug_jos, info_lug_jos = josue.construir_lugares(rv_jos, JOS["menciones"], rutas, lugares, errores,
                                                                 avisos, sin_acentos)
    lugares += lug_jos
    menciones_lugar += men_lug_jos
    lug_jue, men_lug_jue, info_lug_jue = jueces.construir_lugares(rv_jue, JUE["menciones"], rutas, lugares, errores,
                                                                  avisos, sin_acentos)
    lugares += lug_jue
    menciones_lugar += men_lug_jue
    lug_rut, men_lug_rut, info_lug_rut = rut.construir_lugares(rv_rut, RUT["menciones"], rutas, lugares, errores,
                                                               avisos, sin_acentos)
    lugares += lug_rut
    menciones_lugar += men_lug_rut
    lug_1s, men_lug_1s, info_lug_1s = samuel1.construir_lugares(rv_1s, S1["menciones"], rutas, lugares, errores,
                                                                avisos, sin_acentos)
    lugares += lug_1s
    menciones_lugar += men_lug_1s
    mapa = lm.construir_mapa(lugares, rutas)
    x0, y0, x1, y1 = mapa["bbox"]
    for l in lugares:
        u = l["ubicacion"]
        if u and not (x0 <= u["lon"] <= x1 and y0 <= u["lat"] <= y1):
            errores.append(f"Lugar fuera del bbox: {l['id']}")
    nombres_rios = {r["nombre"] for r in mapa["rios"]}
    for rio in ("Tigris", "Éufrates", "Nilo"):
        if rio not in nombres_rios:
            errores.append(f"Falta el río {rio} en el mapa")
    MAPA = SALIDA.parent / "mapa-base.js"
    MAPA.write_text("window.BIBLIA_MAPA = " + json.dumps(mapa, ensure_ascii=False, separators=(",", ":")) + ";\n",
                    encoding="utf-8")
    tam_mapa = MAPA.stat().st_size
    if tam_mapa >= 300_000:
        errores.append(f"mapa-base.js ocupa {tam_mapa} bytes (objetivo < 300 KB)")

    datos = {"generado": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
             "fuentes": FUENTES + lm.FUENTES, "libros": LIBROS, "capitulos": capitulos, "personas": personas,
             "relaciones": relaciones, "edades": edades, "pasajes": pasajes, "menciones": menciones,
             "lugares": lugares, "menciones_lugar": menciones_lugar, "cronologia": cronologia}
    hechos = exodo.comprobar(datos, errores)
    hechos_lv = levitico.comprobar(datos, errores)
    hechos_nm = numeros.comprobar(datos, errores)
    hechos_dt = deuteronomio.comprobar(datos, errores)
    hechos_jos = josue.comprobar(datos, errores, numeral_a_numero)
    hechos_jue = jueces.comprobar(datos, errores)
    hechos_rut = rut.comprobar(datos, errores)
    hechos_1s = samuel1.comprobar(datos, errores)
    for lb in LIBROS:
        n = sum(1 for c in capitulos if c["libro"] == lb["id"])
        if n != lb["capitulos"]:
            errores.append(f"{lb['id']}: {n} capítulos (se esperaban {lb['capitulos']})")
    ids_p = Counter(p["id"] for p in pasajes)
    errores.extend(f"Pasaje con id repetido: {k}" for k, n in ids_p.items() if n > 1)
    errores.extend(f"Pasaje sin libro: {p['id']}" for p in pasajes if p.get("libro") not in [lb["id"] for lb in LIBROS])
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("window.BIBLIA_DATOS = " + json.dumps(datos, ensure_ascii=False, indent=1) + ";\n",
                      encoding="utf-8")
    # relectura: JSON válido tras el '='
    txt = SALIDA.read_text(encoding="utf-8")
    json.loads(txt[txt.index("=") + 1:].rstrip().rstrip(";"))

    # ------------------------------------------------------------ resumen   5
    cert = Counter(x["certeza"] for x in relaciones)
    porte = Counter((e["tradicion"], e["certeza"]) for e in edades)
    print("=== RESUMEN biblia.js (totales de Génesis + Éxodo salvo donde se indica) ===")
    print(f"Versículos: {sum(len(c['versiculos']) for c in capitulos)} (Gn 1–{MAXCAP} y Ex 1–40)")
    fem = lambda sn: sum(1 for p in personas if p["sexo"] == "f" and p["sin_nombre"] == sn)
    print(f"Personas: {len(personas)} (con nombre {sum(1 for p in personas if not p['sin_nombre'])}, "
          f"sin nombre {sum(1 for p in personas if p['sin_nombre'])}; mujeres con nombre {fem(False)}, "
          f"mujeres sin nombre {fem(True)})")
    print(f"Relaciones: {len(relaciones)} (explícitas {cert['explicito']}, inferidas {cert['inferido']}); "
          f"descartadas por tipo no genealógico: {dict(descartadas)}")
    tam = tam_pasaje
    print(f"Pasajes por sección: {dict(Counter(p['seccion'] for p in pasajes))}")
    print(f"Pasajes: {len(pasajes)} (Génesis: versículos {sum(tam)}, mín {min(tam)}, máx {max(tam)}; "
          f"fuera de 8–20: {[p['id'] + ':' + str(n) for p, n in zip(pasajes, tam) if not 8 <= n <= 20]})")
    print(f"Menciones: {len(menciones)} en {len({m['ref'] for m in menciones})} versículos; "
          f"personas con nombre mencionadas: {len({m['persona'] for m in menciones})}")
    print(f"Ambiguas descartadas ({len(ambiguos)}):")
    for a in ambiguos[:25]:
        print("  - " + a)
    if len(ambiguos) > 25:
        print(f"  … y {len(ambiguos) - 25} más")
    print(f"Nombre presente pero persona no situada en ese versículo (no se marca): "
          f"{sum(no_situados.values())} apariciones; más frecuentes {dict(no_situados.most_common(12))}")
    print(f"Personas sin grafía moderna segura (se deja la RV1909) ({len(sin_moderno)}): {', '.join(sorted(sin_moderno))}")
    conf = Counter(l["ubicacion"]["confianza"] for l in lugares if l["ubicacion"])
    print(f"Lugares: {len(lugares)}; ubicados {sum(conf.values())} (alta {conf['alta']}, media {conf['media']}, "
          f"baja {conf['baja']}); sin ubicación {sum(1 for l in lugares if not l['ubicacion'])}: "
          f"{[l['nombre'] for l in lugares if not l['ubicacion']]}")
    print(f"Menciones de lugar: {len(menciones_lugar)} en {len({m['ref'] for m in menciones_lugar})} versículos")
    print(f"Nombres de lugar sin asignar ({len(amb_lugar)}):")
    for a in amb_lugar[:15]:
        print("  - " + a)
    if len(amb_lugar) > 15:
        print(f"  … y {len(amb_lugar) - 15} más")
    print(f"Lugares de OpenBible sin forma hallada en RV1909 (no incluidos) ({len(lug_sin_forma)}): {', '.join(lug_sin_forma)}")
    print(f"Lugares sin grafía moderna segura ({len(lug_sin_moderno)}): {', '.join(lug_sin_moderno)}")
    print(f"Versículos de OpenBible descartados por no traer el nombre en RV1909 ({len(desc_lugar)}):")
    for a in desc_lugar[:15]:
        print("  - " + a)
    if len(desc_lugar) > 15:
        print(f"  … y {len(desc_lugar) - 15} más")
    print("Contraste con el JSON original de OpenBible:")
    for a in lineas_ob:
        print("  - " + a)
    print(f"Mapa base: bbox {mapa['bbox']}, {len(mapa['costas'])} anillos de costa, {len(mapa['rios'])} tramos de río "
          f"({sorted(nombres_rios)}), {len(mapa['lagos'])} lagos; {tam_mapa / 1024:.1f} KB")
    print(f"Mujeres con nombre: {sum(1 for p in personas if p['sexo'] == 'f' and not p['sin_nombre'])}; "
          f"mujeres sin nombre: {sum(1 for p in personas if p['sexo'] == 'f' and p['sin_nombre'])}; "
          f"grupos «otros hijos e hijas»: {sum(1 for p in personas if p['id'].startswith('Otros_hijos_'))}")
    print(f"Relaciones subidas de inferido a explícito por el texto: {subidas}; "
          f"por fuente: {dict(Counter(x['fuente'] for x in relaciones))}")
    for trad in ("TM", "LXX"):
        print(f"Edades {trad}: texto {porte[(trad, 'texto')]}, cálculo {porte[(trad, 'calculo')]}; por tipo "
              f"{dict(Counter(e['tipo'] for e in edades if e['tradicion'] == trad))}")
    print("Comprobación hijos de Jacob:")
    for a in comprobacion_jacob:
        print("  - " + a)
    r2526 = [f"{x['de']}→{x['a']} {x['tipo']} {x['ref']} {x['certeza']}" for x in relaciones
             if x["a"] in ("Esau_1", "Jacob_1") and x["tipo"] in ("padre", "madre")]
    e2526 = [f"{e['tradicion']} {e['valor']} «{e['cita']}» ({e.get('evento', '')})" for e in edades
             if e["persona"] == "Isaac_1" and e["ref"] == "Gn 25:26"]
    print(f"Gn 25:26 — relaciones: {r2526}; edad de Isaac: {e2526}")
    for need in ("Isaac_1→Esau_1 padre", "Isaac_1→Jacob_1 padre", "Rebekah_1→Esau_1 madre", "Rebekah_1→Jacob_1 madre"):
        if not any(r.startswith(need) for r in r2526):
            errores.append(f"Falta {need}")
    if not any(e.startswith("TM 60") for e in e2526):
        errores.append("Falta la edad 60 de Isaac en Gn 25:26")
    print(f"Matrimonios: {sum(1 for x in relaciones if x['tipo'] == 'conyuge')} (añadidos en esta auditoría {matrimonios_nuevos}); "
          f"relaciones padre/madre añadidas desde listas: {padres_nuevos}")
    print(f"Listas «hijos de X» (Gn 36, 46:8-27) frente a relaciones ({len(listas_dif)}):")
    for a in listas_dif:
        print("  - " + a)
    print("Padres sin vínculo conyugal registrado:")
    for (pa, ma), hijos in sorted(sin_vinculo.items()):
        print(f"  - {pa} + {ma} → {hijos}: {g2.SIN_PAREJA_NOTA.get((pa, ma), 'SIN EXPLICAR')}")
    print(f"Personas sin relación ({len(sueltas)}): " + "; ".join(f"{p['nombre']} ({p['rol']}, {p['primera_ref']})" for p in sueltas))
    print(f"Cronología: {len(cronologia['eventos'])} eventos, {len(cronologia['combinaciones'])} combinaciones, "
          f"{len(cronologia['hitos_sin_fecha'])} hitos sin fecha")
    print("  Año (supuestos por defecto)          TM    LXX")
    for eid in ("ev-diluvio", "ev-nac-abram", "ev-nac-isaac", "ev-nac-esau-jacob", "ev-jacob-egipto", "ev-muerte-jose"):
        print(f"  {EV[eid]['titulo'][:34]:34} {EV[eid]['anios']['TM|tare70|sem2|egipto']:>5} {EV[eid]['anios']['LXX|tare70|sem2|egipto']:>5}")
    print(f"  Nace Abram con tare130: TM {EV['ev-nac-abram']['anios']['TM|tare130|sem2|egipto']}; con noe500: TM "
          f"{EV['ev-nac-abram']['anios']['TM|tare70|noe500|egipto']}")
    j = EV["ev-jacob-egipto"]["anios"]["TM|tare70|sem2|egipto"] - EV["ev-nac-jose"]["anios"]["TM|tare70|sem2|egipto"]
    print(f"  Edad de Jacob al nacer José (cálculo): {130 - j}")
    for c in ("TM|tare70|sem2|egipto", "LXX|tare70|sem2|egipto"):
        print(f"  Vivos al comenzar el diluvio ({c}): " + ", ".join(
            f"{nombre_de.get(p, p)} (muere {d} años después)" for p, d in vivos_diluvio[c]))
    print(f"Tamaño: biblia.js {SALIDA.stat().st_size / 1024:.0f} KB; mapa-base.js {tam_mapa / 1024:.1f} KB")
    print("=== POR LIBRO ===")
    for lb in LIBROS:
        L = lb["id"] + " "
        en = lambda refs: any(r.startswith(L) for r in refs)
        print(f"{lb['nombre']}: capítulos {sum(1 for c in capitulos if c['libro'] == lb['id'])}, versículos "
              f"{sum(len(c['versiculos']) for c in capitulos if c['libro'] == lb['id'])}, pasajes "
              f"{sum(1 for x in pasajes if x['libro'] == lb['id'])}, personas con refs en el libro "
              f"{sum(1 for x in personas if en(x['refs']))}, relaciones {sum(1 for x in relaciones if x['ref'].startswith(L))}, "
              f"edades {sum(1 for x in edades if x['ref'].startswith(L))}, menciones {sum(1 for x in menciones if x['ref'].startswith(L))}, "
              f"lugares con refs {sum(1 for x in lugares if en(x['refs']))}, menciones de lugar "
              f"{sum(1 for x in menciones_lugar if x['ref'].startswith(L))}")
    compartidas = [x["nombre"] for x in personas if en(x["refs"]) and any(r.startswith("Gn ") for r in x["refs"])]
    print(f"Personas compartidas Gn+Ex ({len(compartidas)}): {', '.join(compartidas)}")
    print(f"Éxodo: personas nuevas {len(EXO['nuevas'])} (mujeres {sum(1 for x in EXO['nuevas'] if x['sexo'] == 'f')}, "
          f"sin nombre {sum(1 for x in EXO['nuevas'] if x['sin_nombre'])}); relaciones subidas a explícito por el texto "
          f"{EXO['subidas']}; descartadas {EXO['descartadas']}; pasajes fuera de 8–20 versículos: "
          f"{[x['id'] + ':' + str(n) for x, n in zip(EXO['pasajes'], EXO['tam_pasaje']) if not 8 <= n <= 20]}")
    print(f"Éxodo: menciones ambiguas descartadas ({len(EXO['ambiguos'])}): {EXO['ambiguos'][:10]}")
    print(f"Éxodo: nombre presente pero persona no situada: {dict(EXO['no_situados'].most_common(10))}")
    print(f"Éxodo: lugares OpenBible sin forma en RV1909: {info_lug_ex['sin_forma']}; versículos descartados "
          f"{len(info_lug_ex['descartadas'])}: {info_lug_ex['descartadas'][:12]}")
    print("Edades de Éxodo (TM / LXX):")
    for e in EXO["edades"]:
        print(f"  {e['tradicion']:3} {e['persona']:10} {e['tipo']:9} {e['ref']:8} {e['valor']:>4} «{e['cita']}»")
    print("Años (cálculo) de Éxodo:")
    for c in ("TM|tare70|sem2|egipto", "TM|tare70|sem2|canaan", "TM|tare130|sem2|egipto", "TM|tare130|sem2|canaan",
              "LXX|tare70|sem2|egipto", "LXX|tare70|sem2|canaan"):
        print(f"  {c:24} " + ", ".join(f"{k.replace('ev-', '')} {EV[k]['anios'][c]}" for k in
                                         ("ev-jacob-egipto", "ev-salida-egipto", "ev-nac-moises", "ev-nac-aaron", "ev-llegada-sinai", "ev-tabernaculo")))
    print("Hechos obligatorios:")
    for h in hechos:
        print("  " + h)
    print(f"Levítico: personas nuevas {[x['nombre'] for x in LEV['nuevas']]}; ampliadas {len(LEV['ampliadas'])}; "
          f"pasajes {len(LEV['pasajes'])} (fuera de 8–20 versículos: "
          f"{[x['id'] + ':' + str(n) for x, n in zip(LEV['pasajes'], LEV['tam_pasaje']) if not 8 <= n <= 20]}); "
          f"secciones {dict(Counter(x['seccion'] for x in LEV['pasajes']))}")
    print(f"Levítico: menciones ambiguas descartadas ({len(LEV['ambiguos'])}): {LEV['ambiguos'][:10]}; no situadas "
          f"{dict(LEV['no_situados'].most_common(10))}; relaciones BibleData descartadas {LEV['descartadas']}")
    print(f"Levítico: lugares nuevos {[x['id'] for x in lug_lv]}; OpenBible sin forma en RV1909 {info_lug_lv['sin_forma']}; "
          f"versículos descartados {info_lug_lv['descartadas']}")
    print("Hechos obligatorios de Levítico:")
    for h in hechos_lv:
        print("  " + h)
    print(f"Números: personas nuevas ({len(NUM['nuevas'])}) {[x['id'] for x in NUM['nuevas']]}; ampliadas {len(NUM['ampliadas'])}; "
          f"pasajes {len(NUM['pasajes'])} (fuera de 8–20 versículos: "
          f"{[x['id'] + ':' + str(n) for x, n in zip(NUM['pasajes'], NUM['tam_pasaje']) if not 8 <= n <= 20]}); "
          f"secciones {dict(Counter(x['seccion'] for x in NUM['pasajes']))}")
    print(f"Números: menciones ambiguas descartadas ({len(NUM['ambiguos'])}): {NUM['ambiguos'][:15]}; no situadas "
          f"{dict(NUM['no_situados'].most_common(15))}; relaciones BibleData descartadas {NUM['descartadas']}; "
          f"subidas a explícito {NUM['subidas']}")
    print(f"Números: lugares nuevos ({len(lug_nm)}) {[x['id'] for x in lug_nm]}; OpenBible sin forma en RV1909 "
          f"{info_lug_nm['sin_forma']}; versículos descartados ({len(info_lug_nm['descartadas'])}) {info_lug_nm['descartadas']}")
    print("Hechos obligatorios de Números:")
    for h in hechos_nm:
        print("  " + h)
    print(f"Deuteronomio: personas nuevas ({len(DEU['nuevas'])}) {[x['id'] for x in DEU['nuevas']]}; ampliadas "
          f"({len(DEU['ampliadas'])}) {DEU['ampliadas']}; pasajes {len(DEU['pasajes'])} (fuera de 8–20 versículos: "
          f"{[x['id'] + ':' + str(n) for x, n in zip(DEU['pasajes'], DEU['tam_pasaje']) if not 8 <= n <= 20]}); "
          f"secciones {dict(Counter(x['seccion'] for x in DEU['pasajes']))}")
    print(f"Deuteronomio: menciones ambiguas descartadas ({len(DEU['ambiguos'])}): {DEU['ambiguos'][:15]}; no situadas "
          f"{dict(DEU['no_situados'].most_common(15))}; relaciones BibleData descartadas {DEU['descartadas']}")
    print(f"Deuteronomio: lugares nuevos ({len(lug_dt)}) {[x['id'] for x in lug_dt]}; OpenBible sin forma en RV1909 "
          f"{info_lug_dt['sin_forma']}; versículos descartados ({len(info_lug_dt['descartadas'])}) {info_lug_dt['descartadas']}")
    print("Hechos obligatorios de Deuteronomio:")
    for h in hechos_dt:
        print("  " + h)
    print(f"Josué: personas nuevas ({len(JOS['nuevas'])}) {[x['id'] for x in JOS['nuevas']]}; ampliadas "
          f"({len(JOS['ampliadas'])}); pasajes {len(JOS['pasajes'])} (fuera de 8–20 versículos: "
          f"{[x['id'] + ':' + str(n) for x, n in zip(JOS['pasajes'], JOS['tam_pasaje']) if not 8 <= n <= 20]}); "
          f"secciones {dict(Counter(x['seccion'] for x in JOS['pasajes']))}")
    print(f"Josué: menciones ambiguas descartadas ({len(JOS['ambiguos'])}): {JOS['ambiguos'][:15]}; no situadas "
          f"{dict(JOS['no_situados'].most_common(15))}; relaciones BibleData descartadas {JOS['descartadas']}")
    cj = Counter(l["ubicacion"]["confianza"] if l["ubicacion"] else "sin" for l in lug_jos)
    print(f"Josué: lugares nuevos {len(lug_jos)} (automáticos {josue.INFO_AUTO.get('auto')}, homónimos con ref "
          f"{josue.INFO_AUTO.get('homonimos')}; confianza {dict(cj)}); unidos a uno ya registrado {josue.INFO_AUTO.get('unidos')}; "
          f"OpenBible sin forma en RV1909 ({len(info_lug_jos['sin_forma'])}) {info_lug_jos['sin_forma']}; versículos "
          f"descartados ({len(info_lug_jos['descartadas'])}) {info_lug_jos['descartadas'][:40]}")
    print("Hechos obligatorios de Josué:")
    for h in hechos_jos:
        print("  " + h)
    print(f"Jueces: personas nuevas ({len(JUE['nuevas'])}) {[x['id'] for x in JUE['nuevas']]}; ampliadas "
          f"({len(JUE['ampliadas'])}) {JUE['ampliadas']}; pasajes {len(JUE['pasajes'])} (fuera de 8–20 versículos: "
          f"{[x['id'] + ':' + str(n) for x, n in zip(JUE['pasajes'], JUE['tam_pasaje']) if not 8 <= n <= 20]}); "
          f"secciones {dict(Counter(x['seccion'] for x in JUE['pasajes']))}")
    print(f"Jueces: menciones ambiguas descartadas ({len(JUE['ambiguos'])}): {JUE['ambiguos'][:15]}; no situadas "
          f"{dict(JUE['no_situados'].most_common(15))}; relaciones BibleData descartadas {JUE['descartadas']}")
    cju = Counter(l["ubicacion"]["confianza"] if l["ubicacion"] else "sin" for l in lug_jue)
    print(f"Jueces: lugares nuevos {len(lug_jue)} {[x['id'] for x in lug_jue]} (automáticos {jueces.INFO_AUTO.get('auto')}, "
          f"homónimos con ref {jueces.INFO_AUTO.get('homonimos')}; confianza {dict(cju)}); unidos a uno ya registrado "
          f"{jueces.INFO_AUTO.get('unidos')}; OpenBible sin forma en RV1909 ({len(info_lug_jue['sin_forma'])}) "
          f"{info_lug_jue['sin_forma']}; versículos descartados ({len(info_lug_jue['descartadas'])}) {info_lug_jue['descartadas'][:40]}; "
          f"menciones de lugar {len(men_lug_jue)}")
    print("Hechos obligatorios de Jueces:")
    for h in hechos_jue:
        print("  " + h)
    print(f"Rut: personas nuevas ({len(RUT['nuevas'])}) {[x['id'] for x in RUT['nuevas']]}; ampliadas "
          f"({len(RUT['ampliadas'])}) {RUT['ampliadas']}; pasajes {len(RUT['pasajes'])} (tamaños {RUT['tam_pasaje']}); "
          f"secciones {dict(Counter(x['seccion'] for x in RUT['pasajes']))}")
    print(f"Rut: menciones {len(RUT['menciones'])}; ambiguas descartadas ({len(RUT['ambiguos'])}): {RUT['ambiguos'][:15]}; "
          f"no situadas {dict(RUT['no_situados'].most_common(15))}; relaciones BibleData descartadas {RUT['descartadas']}")
    print(f"Rut: lugares nuevos {[x['id'] for x in lug_rut]}; menciones de lugar {len(men_lug_rut)} "
          f"{dict(Counter(m['lugar'] for m in men_lug_rut))}; OpenBible sin forma {info_lug_rut['sin_forma']}; "
          f"versículos descartados {info_lug_rut['descartadas']}")
    print("Hechos obligatorios de Rut:")
    for h in hechos_rut:
        print("  " + h)
    cs1 = Counter(l["ubicacion"]["confianza"] if l["ubicacion"] else "sin" for l in lug_1s)
    print(f"1 Samuel: personas nuevas ({len(S1['nuevas'])}) {[x['id'] for x in S1['nuevas']]}; ampliadas "
          f"({len(S1['ampliadas'])}) {S1['ampliadas']}; pasajes {len(S1['pasajes'])} (tamaños {S1['tam_pasaje']}); "
          f"secciones {dict(Counter(x['seccion'] for x in S1['pasajes']))}")
    print(f"1 Samuel: menciones {len(S1['menciones'])}; ambiguas descartadas ({len(S1['ambiguos'])}): {S1['ambiguos'][:15]}; "
          f"no situadas {dict(S1['no_situados'].most_common(15))}; relaciones BibleData descartadas {S1['descartadas']}")
    print(f"1 Samuel: versificación {samuel1.INFO_VERSIFICACION}")
    print(f"1 Samuel: lugares nuevos {len(lug_1s)} {[x['id'] for x in lug_1s]} (automáticos {samuel1.INFO_AUTO.get('auto')}, "
          f"homónimos {samuel1.INFO_AUTO.get('homonimos')}; confianza {dict(cs1)}); unidos {samuel1.INFO_AUTO.get('unidos')}; "
          f"menciones de lugar {len(men_lug_1s)}; OpenBible sin forma ({len(info_lug_1s['sin_forma'])}) "
          f"{info_lug_1s['sin_forma']}; versículos descartados {info_lug_1s['descartadas']}")
    print("Hechos obligatorios de 1 Samuel:")
    for h in hechos_1s:
        print("  " + h)
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
