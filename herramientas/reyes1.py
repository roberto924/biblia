"""1 Reyes 1–22: personas, relaciones, edades, pasajes, menciones y lugares (lo usa construir_datos.py).

Id del libro: «1R» (el código canónico de CANON en app.js). Reutiliza la lógica de exodo.py (exodo.construir /
exodo.construir_lugares con este módulo como configuración) y la detección automática de lugares de josue.py
(josue.lugares_auto), como 1 y 2 Samuel. Cada dato lleva versículo, fuente y certeza; las citas se comprueban
literalmente contra la RV1909 (TM) o Brenton (LXX). Las personas de Génesis–2 Samuel (David, Salomón, Betsabé, Adonías,
Joab, Abiatar, Sadoc, Benaía, Simei, Natán profeta, Hiram, Urías, Absalón, Amasa…) son la misma persona (mismo id de
BibleData): se amplían sus `refs`.

Versificación (comprobada al generar, versículo a versículo; detalle en datos/LEEME.md, «1 Reyes: decisiones»):
- La RV1909 de eBible tiene 816 versículos con los recuentos de la numeración inglesa (la de BibleData y OpenBible).
  En 4–5 numera como el inglés (4:21-34 y 5:1-18; el hebreo numera 5:1-32). Diferencias con el inglés solo dentro del
  capítulo: 18:33/34 corta como el hebreo, y en 22 divide 22:43 en dos versículos (43-44, como el hebreo) y junta en
  22:53 los dos últimos (hebreo 22:53-54 = inglés 22:52-53). `REMAP_REF` (único punto) lleva la numeración inglesa de
  BibleData y OpenBible a la de la RV1909 en 22:44-53.
- Brenton («3 Kingdoms») reordena 4–5, 7 y 11:5-8, cambia el orden de los capítulos 20 y 21, omite versículos (los
  pone en otro sitio: 3:1, 9:15-25, 14:1-20…) y añade bloques propios con letra (2:35a-o, 2:46a-l, 12:24a-z, 16:28a-h…)
  que `leer_vpl` no lee: no tienen versículo en la RV1909. `br_a_rv` (único punto de versificación de Brenton) lo lleva
  a la numeración de la RV1909; después se comprueba capítulo a capítulo que el emparejamiento sin desfase compara
  mejor que con desfase ±1, que nombres poco frecuentes caen en los mismos versículos, los extremos y los vacíos.

Solo biblioteca estándar.
"""
import math
import re
import sys

import exodo
import josue

LIBRO = "1R"
NOMBRE = "1 Reyes"
USX = "1KI"
CAPITULOS = 22
VERSICULOS = 816
POR_CAPITULO = [53, 46, 28, 34, 18, 38, 51, 66, 28, 29, 43, 33, 34, 31, 34, 34, 24, 46, 21, 43, 29, 53]
VACIOS = {}
# Comienzo de los versículos de las zonas donde el hebreo, el inglés o la LXX numeran distinto (se comprueban).
VERSIFICACION = [((4, 20), "Judá é Israel eran muchos"), ((4, 21), "Y Salomón señoreaba"), ((4, 34), "Y venían de todos los pueblos"),
                 ((5, 1), "HIRAM rey de Tiro"), ((5, 18), "Y los albañiles de Salomón"), ((18, 33), "Compuso luego la leña"),
                 ((18, 34), "Y dijo: Henchid cuatro cántaros"), ((20, 1), "ENTONCES Ben-adad rey de Siria"),
                 ((21, 1), "PASADOS estos negocios"), ((22, 43), "Y anduvo en todo el camino de Asa"),
                 ((22, 44), "Con todo eso los altos no fueron quitados"), ((22, 45), "Y Josaphat hizo paz"),
                 ((22, 51), "Y durmió Josaphat con sus padres"), ((22, 52), "Y Ochôzías hijo de Achâb comenzó"),
                 ((22, 53), "E hizo lo malo")]
FIN_VERSICULO = [((18, 33), "y púsolo sobre la leña."), ((22, 53), "conforme á todas las cosas que su padre había hecho.")]
# Brenton, ya en numeración RV1909 (tras br_a_rv).
VERSIFICACION_LXX = [((4, 17), "Josaphat son of Phuasud"), ((4, 18), "Semei son of Ela"), ((4, 19), "Gaber son of Adai"),
                     ((4, 27), "the officers provided king Solomon"), ((4, 29), "the Lord gave understanding to Solomon"),
                     ((5, 1), "Chiram king of Tyre"), ((6, 1), "four hundred and fortieth year"),
                     ((7, 1), "Solomon built a house for himself in thirteen years"), ((7, 13), "Chiram out of Tyre"),
                     ((20, 1), "the son of Ader gathered all his forces"), ((21, 1), "Nabuthai the Jezraelite"),
                     ((22, 51), "And Josaphat slept with his fathers"), ((22, 53), "And he served Baalim")]
# Versículos de la RV1909 sin Brenton (la LXX no los tiene en su sitio: los omite o los pone en un bloque con letra).
SIN_LXX = {(3, 1), (4, 20), (4, 21), (4, 25), (4, 26), (4, 28), (5, 17), (6, 11), (6, 12), (6, 13), (6, 14), (6, 18),
           (6, 32), (6, 33), (6, 37), (6, 38), (7, 22), (7, 31), (8, 12), (8, 13), *((9, v) for v in range(15, 26)),
           (11, 3), (11, 23), (11, 24), (11, 39), (12, 2), (12, 17), (13, 27), *((14, v) for v in range(1, 21)), (15, 6),
           (15, 32), (22, 47), (22, 48), (22, 49), (22, 50)}
# Nombres que deben caer en los mismos versículos en la RV1909 y en Brenton (solo versículos que tienen ambos).
PARALELOS = [("Abisag", "Abisag"), ("Semei", "Semei"), ("Abiathar", "Abiathar"), ("Sadoc", "Sadoc"), ("Abiam", "Abiu"),
             ("Sisac", "Susakim"), ("Hazael", "Azael"), ("Ochôzías", "Ochozias")]
PROPORCION = (0.2, 5.2)  # longitud RV1909 / Brenton por versículo (observado 0,26 en 18:33 – 5,0 en 8:2, la LXX abrevia)


def REMAP_REF(r):
    """Numeración inglesa (BibleData, OpenBible) -> RV1909. Único punto: en 22 la RV1909 corta 22:43 en dos (como el
    hebreo) y junta los dos últimos en 22:53."""
    c, v = r
    if c == 22 and 44 <= v <= 51:
        return (22, v + 1)
    return (22, 53) if r == (22, 52) else r


# Brenton (LXX) -> RV1909: 4–5 (la LXX pone 4:20-21, 4:25-26 en 2:46a-l, 4:22-24, 4:27 y 4:29-34 en 5:1-14, y
# 5:1-16 en 5:15-30), 7 (otro orden; 7:1 se parte en 7:38 y 7:50) y 11:5-8.
_BR_4_5 = {(4, 17): (4, 18), (4, 18): (4, 19), (4, 19): (4, 17), (5, 1): (4, 27), (5, 2): (4, 22), (5, 3): (4, 23),
           (5, 4): (4, 24), **{(5, v): (4, v + 20) for v in range(9, 15)}, **{(5, v): (5, v - 14) for v in range(15, 31)},
           (5, 32): (5, 18)}
_BR_7 = {**{(7, v): (7, v + 12) for v in range(1, 7)}, (7, 7): (7, 21), (7, 8): (7, 19), (7, 9): (7, 20), (7, 10): (7, 23),
         (7, 11): (7, 24), (7, 12): (7, 26), (7, 13): (7, 25), **{(7, v): (7, v + 13) for v in range(14, 18)},
         **{(7, v): (7, v + 14) for v in range(18, 23)}, (7, 23): (7, 37), **{(7, v): (7, v + 14) for v in range(24, 32)},
         (7, 32): (7, 47), (7, 33): (7, 46), **{(7, v): (7, v + 14) for v in range(34, 38)}, (7, 38): (7, 1),
         **{(7, v): (7, v - 37) for v in range(39, 50)}, (7, 50): (7, 1)}
_BR_11 = {(11, 5): (11, 7), (11, 6): (11, 5), (11, 7): (11, 8), (11, 8): (11, 6)}


def br_a_rv(br):
    """Brenton (3 Reinos) -> numeración de la RV1909. Único punto de versificación de Brenton: las tablas de 4–5, 7 y
    11:5-8; los capítulos 20 y 21 cambiados (LXX 20 = RV 21; LXX 21 = RV 20); 22:54 LXX va al final de 22:53."""
    out = {}
    for (c, v), t in sorted(br.items()):
        k = _BR_4_5.get((c, v)) or _BR_7.get((c, v)) or _BR_11.get((c, v))
        if k is None:
            k = (21, v) if c == 20 else (20, v) if c == 21 else (22, 53) if (c, v) == (22, 54) else (c, v)
        out[k] = f"{out[k]} {t}" if k in out else t
    return out


# ---------------------------------------------------------------- identidades
# Ids propios donde BibleData une personas que el texto no une, o usa un id que en esta app ya es otra persona. Acaban en
# «_número» para que exodo.construir los acepte como ids de persona (lee sus filas reasignadas de BibleData).
AHIAS = "Ahijah_1R11_1"      # Ahías silonita, profeta (11:29)
SEMEI = "Shimei_1R1_1"       # Semei de 1:8
MAHOL = "Mahol_1R4_1"        # Mahol, padre de Hemán, Calcol y Darda (4:31)
BASEMAT = "Basemath_1R4_1"   # Basemat hija de Salomón (4:15)
HIJA_FARAON = "Pharaoh_5_hija_1R3"
REINA_SEBA = "Queen of Sheba_1"
_AHIAS = ("Ahías silonita, profeta (1 R 11:29; 14:2), no es Ahías hijo de Ahitob, el sacerdote del tiempo de Saúl "
          "(1 S 14:3): BibleData los une en Ahijah_1; el texto no lo dice. Aquí lleva id propio (Ahijah_1R11_1).")
_SEMEI = ("1 R 1:8 nombra a «Semei» entre los que no siguen a Adonías, sin decir de quién es hijo. BibleData lo "
          "identifica con Sama (Simea), hermano de David (Shammah_2); el texto no lo dice: lleva id propio (Shimei_1R1_1).")
_MAHOL = ("1 R 4:31: «Hemán y Calchôl y Darda, hijos de Mahol». BibleData pone a Zera hijo de Judá como padre (por "
          "1 Cr 2:6, libro posterior); el texto dice «Mahol»: lleva id propio (Mahol_1R4_1).")
_BASEMAT = ("Basemat hija de Salomón (1 R 4:15). BibleData la llama Basemath_2, pero en esta app ese id es Basemat hija de "
            "Ismael, mujer de Esaú (Gn 36:3): lleva id propio (Basemath_1R4_1).")
_SISAC = "1 R 11:40 y 14:25 nombran a «Sisac rey de Egipto»: es Shishak_1 de BibleData, no el Faraón suegro de Salomón."
# (id de BibleData, ref RV1909) -> id con que se usa aquí. Único punto de reasignación de BibleData-PersonVerse.
PV_REASIGNAR = {**{("Ahijah_1", r): AHIAS for r in ((11, 29), (11, 30), (12, 15), (14, 2), (14, 4), (14, 5), (14, 6),
                                                     (14, 18), (15, 29))},
                ("Ahijah_1", (15, 33)): "Ahijah_3",  # «Baasa hijo de Ahía» (15:33), el de 15:27
                ("Shammah_2", (1, 8)): SEMEI, ("Zerah_3", (4, 31)): MAHOL, ("Basemath_2", (4, 15)): BASEMAT,
                ("Pharaoh_5", (11, 40)): "Shishak_1", ("Pharaoh_5", (14, 25)): "Shishak_1"}
SEXO_PROPIO = {AHIAS: "m", SEMEI: "m", MAHOL: "m", BASEMAT: "f"}

# Personas de BibleData que no se crean: Dios, «NA» y el ángel de Jehová (19:7), como en los libros anteriores.
EXCLUIR = {"YHVH_1", "NA", "the angel of the LORD_1"}
# «Israel» es el pueblo: Jacob solo si el texto dice «Jacob» (18:31).
SOLO_ETIQUETA = {"Jacob_1": {"Jacob"}}
FORMA_NO_MENCION = {("Jacob_1", "israel")}
PV_DESCARTAR = {("Rehoboam_1", (11, 40)): "1 R 11:40 habla de Jeroboam y de Salomón; Roboam no aparece."}
_ZERA = "el padre es Mahol (1 R 4:31), con id propio; ver Mahol."
REL_DESCARTAR = {
    ("Solomon_1", "Basemath_2", "padre"): _BASEMAT, ("Ahimaaz_3", "Basemath_2", "conyuge"): _BASEMAT,
    ("Zerah_3", "Ethan_1", "padre"): ("1 R 4:31 dice «Ethán Ezrahita»; no lo hace hijo de Zera ni de Mahol (BibleData lo "
                                     "toma de 1 Cr 2:6)."),
    ("Zerah_3", "Heman_1", "padre"): _ZERA, ("Zerah_3", "Calcol_1", "padre"): _ZERA, ("Zerah_3", "Darda_1", "padre"): _ZERA,
    ("Ela_1", "Shimei_4", "padre"): ("BibleData usa Shimei_4 en la relación y Shimei_3 en el versículo (4:18, «Semei hijo "
                                     "de Ela»): se usa Shimei_3."),
    ("Maacah_3", "Asa_1", "madre"): "se añade aparte, con nota (ver MADRE_ASA).",
}
FORMAS_FORZADAS = {
    "Ben-hur_1": ["hijo de Hur"], "Ben-deker_1": ["hijo de Decar"], "Ben-hesed_1": ["hijo de Hesed"],
    "Ben-abinadab_1": ["hijo de Abinadab"], "Ben-geber_1": ["hijo de Geber"], "Elisha_1": ["Eliseo"],
    "Rehoboam_1": ["Roboam"], "Ahaziah_1": ["Ochôzías"], "Obadiah_1": ["Abdías"], "Pharaoh_5": ["Faraón"],
    "Shishak_1": ["Sisac"], AHIAS: ["Ahías"], SEMEI: ["Semei"], MAHOL: ["Mahol"], BASEMAT: ["Basemath"],
    "Heman_1": ["Emán"], "Hadad_3": ["Adad"], "Rei_1": ["Reihi"], "Ahab_1": ["Achâb"], "Solomon_1": ["Salomón"],
    "Hiram_1": ["Hiram"], "Adonijah_1": ["Adonías", "Adonía"], "Jehoshaphat_3": ["Josaphat"],
}
MODERNO = {
    "Abishag_1": "Abisag", "Rei_1": "Reí", SEMEI: "Simei", "Pharaoh_5": "Faraón", "Azariah_1": "Azarías",
    "Elihoreph_1": "Elihoref", "Ahijah_2": "Ahías", "Shisha_1": "Sisa", "Azariah_2": "Azarías", "Nathan_4": "Natán",
    "Zabud_1": "Zabud", "Nathan_5": "Natán", "Ahishar_1": "Ahisar", "Adoniram_1": "Adoniram", "Abda_1": "Abda",
    "Ben-hur_1": "Ben-hur", "Ben-deker_1": "Ben-decar", "Ben-hesed_1": "Ben-hesed", "Ben-abinadab_1": "Ben-abinadab",
    "Taphath_1": "Tafat", "Baana_1": "Baana", "Ahilud_2": "Ahilud", "Ben-geber_1": "Ben-geber", "Ahinadab_1": "Ahinadab",
    "Iddo_1": "Iddo", "Ahimaaz_3": "Ahimaas", BASEMAT: "Basemat", "Baana_2": "Baana", "Hushai_2": "Husai",
    "Jehoshaphat_2": "Josafat", "Paruah_1": "Parúa", "Shimei_3": "Simei", "Ela_1": "Ela", "Geber_1": "Geber",
    "Uri_2": "Uri", "Ethan_1": "Etán", "Heman_1": "Hemán", "Calcol_1": "Calcol", "Darda_1": "Darda", MAHOL: "Mahol",
    "Hiram_2": "Hiram", "Hadad_3": "Hadad", "Tahpenes_1": "Tafnes", "Genubath_1": "Genubat", "Rezon_1": "Rezón",
    "Eliada_2": "Eliada", "Jeroboam_1": "Jeroboam", "Nebat_1": "Nabat", "Zeruah_1": "Serúa", AHIAS: "Ahías",
    "Rehoboam_1": "Roboam", "Shemaiah_1": "Semaías", "Josiah_1": "Josías", "Abijah_2": "Abías", "Nadab_2": "Nadab",
    "Naamah_2": "Naama", "Abijam_1": "Abiam", "Maacah_3": "Maaca", "Abishalom_1": "Abisalom", "Asa_1": "Asa",
    "Baasha_1": "Baasa", "Ben-hadad_1": "Ben-adad", "Tabrimmon_1": "Tabrimón", "Hezion_1": "Hezión",
    "Jehoshaphat_3": "Josafat", "Ahijah_3": "Ahías", "Jehu_1": "Jehú", "Hanani_1": "Hanani", "Elah_2": "Ela",
    "Zimri_2": "Zimri", "Arza_1": "Arsa", "Omri_1": "Omri", "Tibni_1": "Tibni", "Ginath_1": "Ginat", "Shemer_1": "Semer",
    "Ahab_1": "Acab", "Jezebel_1": "Jezabel", "Ethbaal_1": "Et-baal", "Hiel_1": "Hiel", "Abiram_2": "Abiram",
    "Segub_1": "Segub", "Elijah_1": "Elías", "Obadiah_1": "Abdías", "Hazael_1": "Hazael", "Jehu_2": "Jehú",
    "Nimshi_1": "Nimsi", "Elisha_1": "Eliseo", "Shaphat_2": "Safat", "Naboth_1": "Nabot", "Micaiah_1": "Micaías",
    "Imlah_1": "Imla", "Zedekiah_1": "Sedequías", "Chenaanah_1": "Quenaana", "Amon_1": "Amón", "Joash_2": "Joás",
    "Ahaziah_1": "Ocozías", "Azubah_1": "Azuba", "Shilhi_1": "Silhi", "Jehoram_1": "Joram", "Shishak_1": "Sisac",
}
NOTAS = {
    AHIAS: _AHIAS + " Rasga su capa en doce pedazos y da diez a Jeroboam (1 R 11:29-31); anuncia la muerte del hijo de "
                    "Jeroboam (1 R 14:1-18).",
    SEMEI: _SEMEI,
    MAHOL: _MAHOL,
    BASEMAT: _BASEMAT + " Mujer de Ahimaas, gobernador en Neftalí.",
    "Shimei_3": "Hijo de Ela, gobernador de Salomón en Benjamín (1 R 4:18). Distinto de Simei hijo de Gera y del Semei de 1 R 1:8.",
    "Nathan_4": ("Padre de Azarías (1 R 4:5). BibleData lo distingue del profeta Natán y del Natán padre de Zabud; el texto "
                 "no dice quién es."),
    "Nathan_5": ("Padre de Zabud, «principal [oficial], amigo del rey» (1 R 4:5). BibleData lo distingue del profeta y del "
                 "padre de Azarías; el texto no dice quién es."),
    "Azariah_1": "«Azarías hijo de Sadoc, sacerdote» (1 R 4:2). Distinto de Azarías hijo de Natán (1 R 4:5).",
    "Azariah_2": "Hijo de Natán, sobre los gobernadores (1 R 4:5). Distinto de Azarías hijo de Sadoc (1 R 4:2).",
    "Ahijah_2": "Hijo de Sisa, escriba de Salomón (1 R 4:3). Distinto de Ahías silonita y del padre de Baasa.",
    "Ahijah_3": "Padre de Baasa, «de la casa de Issachâr» (1 R 15:27, 33; 21:22). Distinto de Ahías silonita.",
    "Jehoshaphat_2": "Hijo de Parúa, gobernador en Isacar (1 R 4:17). Distinto de Josafat hijo de Ahilud y del rey Josafat.",
    "Jehoshaphat_3": "Hijo de Asa, rey de Judá (1 R 15:24; 22:41-42). Distinto de Josafat hijo de Ahilud y del hijo de Parúa.",
    "Hiram_2": ("Artífice en bronce traído de Tiro, «hijo de una viuda de la tribu de Nephtalí» (1 R 7:13-14). Distinto de "
                "Hiram rey de Tiro."),
    "Jehu_1": "Profeta, hijo de Hanani (1 R 16:1, 7). Distinto de Jehú hijo de Nimsi (1 R 19:16).",
    "Jehu_2": "Hijo de Nimsi, al que Elías debe ungir rey sobre Israel (1 R 19:16). Distinto del profeta Jehú hijo de Hanani.",
    "Nadab_2": "Hijo de Jeroboam, rey de Israel dos años (1 R 15:25). Distinto de Nadab hijo de Aarón.",
    "Abiram_2": "Primogénito de Hiel de Betel (1 R 16:34). Distinto de Abiram hijo de Eliab (Nm 16).",
    "Zimri_2": "Comandante de la mitad de los carros de Ela; reina siete días en Tirsa (1 R 16:9-18). Distinto del Zimri de Nm 25:14.",
    "Hadad_3": "Idumeo, «de la sangre real» de Edom, adversario de Salomón (1 R 11:14-22, 25).",
    "Pharaoh_5": ("Rey de Egipto, suegro de Salomón (1 R 3:1; 9:16). No es el Faraón del éxodo. BibleData le atribuye "
                  "también el Faraón que acoge a Hadad (1 R 11:18-22); el texto no dice si es el mismo (ver identidad)."),
    "Shishak_1": "«Sisac rey de Egipto» (1 R 11:40; 14:25). " + _SISAC,
    "Ben-hadad_1": ("Rey de Siria, «hijo de Tabrimón, hijo de Hezión» (1 R 15:18), en tiempos de Asa; BibleData le da también "
                    "el Ben-adad de 1 R 20 (tiempos de Acab). El texto no dice si es el mismo (ver identidad)."),
    "Maacah_3": ("«Maachâ, hija de Abisalom»: madre de Abiam (1 R 15:2) y, según 1 R 15:10, también de Asa, hijo de Abiam "
                 "(1 R 15:8); Asa la priva «de ser princesa» (1 R 15:13). El texto no lo explica; no se armoniza."),
    "Josiah_1": "1 R 13:2: el varón de Dios anuncia que «á la casa de David nacerá un hijo, llamado Josías».",
    "Elijah_1": "Tisbita, «de los moradores de Galaad» (1 R 17:1).",
    "Elisha_1": "Hijo de Safat, de Abel-mehola (1 R 19:16); Elías echa sobre él su manto (1 R 19:19).",
    "Naboth_1": "De Jezreel; no quiere vender a Acab su viña y es apedreado (1 R 21:1-13).",
    "Obadiah_1": "Mayordomo de Acab, «temeroso de Jehová»; esconde a cien profetas (1 R 18:3-4).",
    "Joash_2": "«Joas hijo del rey» (1 R 22:26). BibleData lo hace hijo de Acab (el rey de Israel del pasaje): inferido.",
}
IDENTIDAD = {
    "Pharaoh_5": {"certeza": "inferido", "refs": ["1R 11:18", "1R 11:19", "1R 11:20", "1R 11:21", "1R 11:22"],
                  "nombres_rv1909": ["Faraón"], "fuente": "bibledata",
                  "nota": ("BibleData identifica al Faraón que acoge a Hadad en tiempos de David (1 R 11:18-22) con el "
                           "suegro de Salomón (1 R 3:1). El texto no dice si es el mismo.")},
    "Ben-hadad_1": {"certeza": "inferido", "refs": ["1R 15:18", "1R 20:1"], "nombres_rv1909": ["Ben-adad"],
                    "fuente": "bibledata",
                    "nota": ("BibleData da un solo id al Ben-adad hijo de Tabrimón, en tiempos de Asa (1 R 15:18-20), y al "
                             "Ben-adad de las guerras con Acab (1 R 20). El texto no dice si es el mismo rey.")},
}
NOTAS_VERIFICAR = [
    ("TM", (11, 29), "el profeta Ahías Silonita"), ("TM", (14, 2), "Ahías profeta"), ("TM", (1, 8), "Semei"),
    ("TM", (4, 31), "Calchôl y Darda, hijos de Mahol"), ("TM", (4, 31), "Ethán Ezrahita"), ("TM", (4, 15), "Basemath hija de Salomón"),
    ("TM", (11, 40), "Sisac rey de Egipto"), ("TM", (14, 25), "Sisac rey de Egipto"), ("TM", (4, 18), "Semei hijo de Ela"),
    ("TM", (4, 5), "Zabud hijo de Nathán era principal [oficial], amigo del rey"), ("TM", (4, 2), "Azarías hijo de Sadoc, sacerdote"),
    ("TM", (15, 27), "Ahía, el cual era de la casa de Issachâr"), ("TM", (7, 14), "Hijo de una viuda de la tribu de Nephtalí"),
    ("TM", (16, 7), "Jehú profeta, hijo de Hanani"), ("TM", (19, 16), "Jehú hijo de Nimsi"), ("TM", (15, 13), "de ser princesa"),
    ("TM", (15, 10), "el nombre de su madre fué Maachâ, hija de Abisalom"), ("TM", (15, 8), "reinó Asa su hijo en su lugar"),
    ("TM", (13, 2), "á la casa de David nacerá un hijo, llamado Josías"), ("TM", (17, 1), "de los moradores de Galaad"),
    ("TM", (19, 19), "echó sobre él su manto"), ("TM", (21, 13), "apedreáronlo con piedras"), ("TM", (18, 3), "Abdías su mayordomo"),
    ("TM", (18, 4), "Abdías tomó cien profetas"), ("TM", (22, 26), "Joas hijo del rey"), ("TM", (11, 14), "Adad, Idumeo, de la sangre real"),
    ("TM", (3, 1), "hizo parentesco con Faraón rey de Egipto"), ("TM", (9, 16), "su hija la mujer de Salomón"),
    ("TM", (11, 18), "á Faraón rey de Egipto"), ("TM", (15, 18), "Ben-adad, hijo de Tabrimón, hijo de Hezión"),
    ("TM", (16, 9), "comandante de la mitad de los carros"), ("TM", (16, 15), "siete días en Thirsa"),
    ("TM", (16, 34), "Hiel de Beth-el"), ("TM", (15, 25), "reinó sobre Israel dos años"),
]
ROLES = {
    "Abishag_1": ("sunamita que sirve al rey David", (1, 3), "hallaron á Abisag Sunamita"),
    "Rei_1": ("de los que no siguen a Adonías", (1, 8), "y Reihi, y todos los grandes de David, no seguían á Adonía"),
    SEMEI: ("de los que no siguen a Adonías", (1, 8), "y Semei, y Reihi"),
    "Pharaoh_5": ("rey de Egipto, suegro de Salomón", (3, 1), "hizo parentesco con Faraón rey de Egipto"),
    "Azariah_1": ("sacerdote, príncipe de Salomón", (4, 2), "Azarías hijo de Sadoc, sacerdote"),
    "Elihoreph_1": ("escriba de Salomón", (4, 3), "Elioreph y Ahía, hijos de Sisa, escribas"),
    "Ahijah_2": ("escriba de Salomón", (4, 3), "Elioreph y Ahía, hijos de Sisa, escribas"),
    "Azariah_2": ("sobre los gobernadores de Salomón", (4, 5), "Azaría hijo de Nathán era sobre los gobernadores"),
    "Zabud_1": ("principal oficial, amigo del rey", (4, 5), "Zabud hijo de Nathán era principal [oficial], amigo del rey"),
    "Ahishar_1": ("mayordomo de Salomón", (4, 6), "Ahisar era mayordomo"),
    "Adoniram_1": ("sobre el tributo", (4, 6), "Adoniram hijo de Abda era sobre el tributo"),
    "Ben-hur_1": ("gobernador en el monte de Efraín", (4, 8), "el hijo de Hur en el monte de Ephraim"),
    "Ben-deker_1": ("gobernador en Macas, Saalbim y Bet-semes", (4, 9), "El hijo de Decar, en Maccas"),
    "Ben-hesed_1": ("gobernador en Arubot", (4, 10), "El hijo de Hesed, en Aruboth"),
    "Ben-abinadab_1": ("gobernador en los términos de Dor", (4, 11), "El hijo de Abinadab, en todos los términos de Dor"),
    "Baana_1": ("gobernador en Taanac y Meguido", (4, 12), "Baana hijo de Ahilud, en Taanach y Megiddo"),
    "Ben-geber_1": ("gobernador en Ramot de Galaad", (4, 13), "El hijo de Geber, en Ramoth de Galaad"),
    "Ahinadab_1": ("gobernador en Mahanaim", (4, 14), "Ahinadab hijo de Iddo, en Mahanaim"),
    "Ahimaaz_3": ("gobernador en Neftalí", (4, 15), "Ahimaas en Nephtalí"),
    "Baana_2": ("gobernador en Aser", (4, 16), "Baana hijo de Husai, en Aser"),
    "Jehoshaphat_2": ("gobernador en Isacar", (4, 17), "Josaphat hijo de Pharua, en Issachâr"),
    "Shimei_3": ("gobernador en Benjamín", (4, 18), "Semei hijo de Ela, en Benjamín"),
    "Geber_1": ("gobernador en Galaad", (4, 19), "Geber hijo de Uri, en la tierra de Galaad"),
    "Ethan_1": ("ezraíta, sabio", (4, 31), "Ethán Ezrahita"),
    "Hiram_2": ("artífice en bronce, de Tiro", (7, 14), "trabajaba él en bronce"),
    REINA_SEBA: ("reina que viene a probar a Salomón", (10, 1), "OYENDO la reina de Seba la fama de Salomón"),
    "Hadad_3": ("idumeo, adversario de Salomón", (11, 14), "un adversario á Salomón, á Adad, Idumeo"),
    "Tahpenes_1": ("reina de Egipto", (11, 19), "la reina Thaphnes"),
    "Rezon_1": ("adversario de Salomón", (11, 23), "Despertóle también Dios por adversario á Rezón"),
    "Jeroboam_1": ("efrateo de Sereda, siervo de Salomón; rey de Israel", (11, 26), "Jeroboam hijo de Nabat, Ephrateo de Sereda, siervo de Salomón"),
    "Zeruah_1": ("mujer viuda, madre de Jeroboam", (11, 26), "su madre se llamaba Serva, mujer viuda"),
    AHIAS: ("profeta silonita", (11, 29), "el profeta Ahías Silonita"),
    "Rehoboam_1": ("hijo de Salomón, rey de Judá", (14, 21), "Roboam hijo de Salomón reinó en Judá"),
    "Shemaiah_1": ("varón de Dios", (12, 22), "Semeías varón de Dios"),
    "Josiah_1": ("hijo anunciado a la casa de David", (13, 2), "á la casa de David nacerá un hijo, llamado Josías"),
    "Abijam_1": ("rey de Judá", (15, 1), "Abiam comenzó á reinar sobre Judá"),
    "Asa_1": ("rey de Judá", (15, 9), "Asa comenzó á reinar sobre Judá"),
    "Nadab_2": ("rey de Israel", (15, 25), "Nadab, hijo de Jeroboam, comenzó á reinar sobre Israel"),
    "Baasha_1": ("rey de Israel", (15, 33), "comenzó á reinar Baasa hijo de Ahía sobre todo Israel"),
    "Ben-hadad_1": ("rey de Siria", (15, 18), "Ben-adad, hijo de Tabrimón, hijo de Hezión, rey de Siria"),
    "Shishak_1": ("rey de Egipto", (11, 40), "Sisac rey de Egipto"),
    "Jehu_1": ("profeta", (16, 7), "Jehú profeta, hijo de Hanani"),
    "Elah_2": ("rey de Israel", (16, 8), "comenzó á reinar Ela hijo de Baasa sobre Israel"),
    "Zimri_2": ("comandante de la mitad de los carros; reina siete días", (16, 9), "Zimri, comandante de la mitad de los carros"),
    "Arza_1": ("mayordomo de Ela en Tirsa", (16, 9), "Arsa su mayordomo en Thirsa"),
    "Omri_1": ("general del ejército; rey de Israel", (16, 16), "Omri, general del ejército"),
    "Tibni_1": ("al que sigue la mitad del pueblo para hacerlo rey", (16, 21), "la mitad del pueblo seguía á Thibni hijo de Gineth, para hacerlo rey"),
    "Shemer_1": ("dueño del monte de Samaria", (16, 24), "compró él de Semer el monte de Samaria"),
    "Ahab_1": ("rey de Israel", (16, 29), "comenzó á reinar Achâb hijo de Omri sobre Israel"),
    "Ethbaal_1": ("rey de los sidonios", (16, 31), "Ethbaal rey de los Sidonios"),
    "Hiel_1": ("de Betel; reedifica Jericó", (16, 34), "Hiel de Beth-el reedificó á Jericó"),
    "Elijah_1": ("profeta tisbita", (17, 1), "Elías Thisbita"),
    "Obadiah_1": ("mayordomo de Acab", (18, 3), "Abdías su mayordomo"),
    "Hazael_1": ("al que Elías debe ungir rey de Siria", (19, 15), "ungirás á Hazael por rey de Siria"),
    "Jehu_2": ("al que Elías debe ungir rey sobre Israel", (19, 16), "Jehú hijo de Nimsi, ungirás por rey sobre Israel"),
    "Elisha_1": ("profeta en lugar de Elías", (19, 16), "ungirás para que sea profeta en lugar de ti"),
    "Naboth_1": ("de Jezreel, dueño de una viña", (21, 1), "Naboth de Jezreel tenía en Jezreel una viña"),
    "Micaiah_1": ("profeta", (22, 8), "Michêas, hijo de Imla"),
    "Zedekiah_1": ("profeta que se hace cuernos de hierro", (22, 11), "se había hecho unos cuernos de hierro"),
    "Amon_1": ("gobernador de la ciudad", (22, 26), "Amón gobernador de la ciudad"),
    "Jehoshaphat_3": ("rey de Judá", (22, 41), "Josaphat hijo de Asa comenzó á reinar sobre Judá"),
    "Ahaziah_1": ("rey de Israel", (22, 52), "Ochôzías hijo de Achâb comenzó á reinar sobre Israel"),
    "Jehoram_1": ("hijo de Josafat, rey en su lugar", (22, 51), "en su lugar reinó Joram su hijo"),
}
SIN_NOMBRE = {
    REINA_SEBA: ("Reina de Seba", "f", "1 R 10:1-13: «la reina de Seba» viene a probar a Salomón con preguntas; el texto no da su nombre.", []),
    HIJA_FARAON: ("Hija de Faraón", "f",
                  "Mujer de Salomón (1 R 3:1; 7:8); su padre le da Gezer en dote (1 R 9:16); sube de la ciudad de David a "
                  "su casa (1 R 9:24). El texto no da su nombre.",
                  [("Pharaoh_5", HIJA_FARAON, "padre", (3, 1), "explicito", "tomó la hija de Faraón"),
                   ("Solomon_1", HIJA_FARAON, "conyuge", (7, 8), "explicito", "una casa para la hija de Faraón, que había tomado por mujer")]),
}
RELACIONES = [
    ("Zadok_1", "Azariah_1", "padre", (4, 2), "Azarías hijo de Sadoc", "BibleData: «hijo [descendiente]»; el texto dice «hijo»."),
    ("Ela_1", "Shimei_3", "padre", (4, 18), "Semei hijo de Ela", ""),
    ("Solomon_1", BASEMAT, "padre", (4, 15), "Basemath hija de Salomón", ""),
    ("Ahimaaz_3", BASEMAT, "conyuge", (4, 15), "tomó también por mujer á Basemath", ""),
    (MAHOL, "Heman_1", "padre", (4, 31), "Emán y Calchôl y Darda, hijos de Mahol",
     "La RV1909 escribe «Emán». El texto no dice si «Ethán Ezrahita», nombrado antes, es también hijo de Mahol."),
    (MAHOL, "Calcol_1", "padre", (4, 31), "Calchôl y Darda, hijos de Mahol", ""),
    (MAHOL, "Darda_1", "padre", (4, 31), "Darda, hijos de Mahol", ""),
    ("Nebat_1", "Jeroboam_1", "padre", (11, 26), "Jeroboam hijo de Nabat", ""),
    ("Zeruah_1", "Jeroboam_1", "madre", (11, 26), "su madre se llamaba Serva, mujer viuda", ""),
    ("Nebat_1", "Zeruah_1", "conyuge", (11, 26), "su madre se llamaba Serva, mujer viuda",
     "El texto la llama madre de Jeroboam hijo de Nabat y «mujer viuda»; no dice que fuera mujer de Nabat: inferido."),
    ("Solomon_1", "Rehoboam_1", "padre", (11, 43), "reinó en su lugar Roboam su hijo", "1 R 14:21: «Roboam hijo de Salomón»."),
    ("Naamah_2", "Rehoboam_1", "madre", (14, 21), "El nombre de su madre fué Naama, Ammonita", "También 1 R 14:31."),
    ("Solomon_1", "Naamah_2", "conyuge", (14, 21), "El nombre de su madre fué Naama, Ammonita",
     "Madre de Roboam «hijo de Salomón» (1 R 14:21); el texto no la llama mujer de Salomón: inferido."),
    ("Rehoboam_1", "Abijam_1", "padre", (14, 31), "reinó en su lugar Abiam su hijo", ""),
    ("Maacah_3", "Abijam_1", "madre", (15, 2), "El nombre de su madre fué Maachâ, hija de Abisalom", ""),
    ("Abishalom_1", "Maacah_3", "padre", (15, 2), "Maachâ, hija de Abisalom", "También 1 R 15:10."),
    ("Rehoboam_1", "Maacah_3", "conyuge", (15, 2), "El nombre de su madre fué Maachâ",
     "Madre de Abiam hijo de Roboam (1 R 14:31; 15:2); el texto no la llama mujer de Roboam: inferido."),
    ("Abijam_1", "Asa_1", "padre", (15, 8), "reinó Asa su hijo en su lugar", ""),
    ("Asa_1", "Jehoshaphat_3", "padre", (15, 24), "reinó en su lugar Josaphat su hijo", "1 R 22:41: «Josaphat hijo de Asa»."),
    ("Azubah_1", "Jehoshaphat_3", "madre", (22, 42), "El nombre de su madre fué Azuba hija de Silai", ""),
    ("Shilhi_1", "Azubah_1", "padre", (22, 42), "Azuba hija de Silai", ""),
    ("Asa_1", "Azubah_1", "conyuge", (22, 42), "El nombre de su madre fué Azuba",
     "Madre de Josafat hijo de Asa (1 R 22:41-42); el texto no la llama mujer de Asa: inferido."),
    ("Jeroboam_1", "Nadab_2", "padre", (14, 20), "reinó en su lugar Nadab su hijo", "1 R 15:25: «Nadab, hijo de Jeroboam»."),
    ("Jeroboam_1", "Abijah_2", "padre", (14, 1), "Abías hijo de Jeroboam", ""),
    ("Ahijah_3", "Baasha_1", "padre", (15, 27), "Baasa hijo de Ahía", "También 1 R 15:33 y 21:22."),
    ("Baasha_1", "Elah_2", "padre", (16, 6), "reinó en su lugar Ela su hijo", "1 R 16:8: «Ela hijo de Baasa»."),
    ("Omri_1", "Ahab_1", "padre", (16, 28), "reinó en lugar suyo Achâb, su hijo", "1 R 16:29-30: «Achâb hijo de Omri»."),
    ("Ahab_1", "Jezebel_1", "conyuge", (16, 31), "tomó por mujer á Jezabel", ""),
    ("Ethbaal_1", "Jezebel_1", "padre", (16, 31), "Jezabel hija de Ethbaal rey de los Sidonios", ""),
    ("Hiel_1", "Abiram_2", "padre", (16, 34), "Abiram su primogénito", ""),
    ("Hiel_1", "Segub_1", "padre", (16, 34), "Segub su [hijo] postrero", ""),
    ("Nimshi_1", "Jehu_2", "padre", (19, 16), "Jehú hijo de Nimsi", ""),
    ("Shaphat_2", "Elisha_1", "padre", (19, 16), "Eliseo hijo de Saphat", "También 1 R 19:19."),
    ("Imlah_1", "Micaiah_1", "padre", (22, 8), "Michêas, hijo de Imla", ""),
    ("Chenaanah_1", "Zedekiah_1", "padre", (22, 11), "Sedechîas hijo de Chânaana", ""),
    ("Ahab_1", "Ahaziah_1", "padre", (22, 40), "reinó en su lugar Ochôzías su hijo", "1 R 22:52: «Ochôzías hijo de Achâb»."),
    ("Jehoshaphat_3", "Jehoram_1", "padre", (22, 51), "en su lugar reinó Joram su hijo", ""),
]
# Relaciones que el texto no dice: se dejan con certeza «inferido» (la nota dice por qué).
INFERIDAS = {("Nebat_1", "Zeruah_1", "conyuge"), ("Naamah_2", "Solomon_1", "conyuge"), ("Maacah_3", "Rehoboam_1", "conyuge"),
             ("Asa_1", "Azubah_1", "conyuge")}
# 1 R 15:10 da a Asa (hijo de Abiam, 15:8) la misma madre que a Abiam (15:2). Se registra como dice el texto, sin
# vínculo conyugal (el texto no lo da) y con nota; se añade después de exodo.construir.
MADRE_ASA = ("Maacah_3", "Asa_1", "madre", (15, 10), "el nombre de su madre fué Maachâ, hija de Abisalom",
             "1 R 15:2 y 15:10 dan la misma madre, «Maachâ, hija de Abisalom», a Abiam y a su hijo Asa (1 R 15:8); en "
             "15:13 Asa priva «á su madre Maachâ» de ser princesa. El texto no lo explica ni dice que Abiam y Maaca "
             "fueran cónyuges; no se armoniza.")
NOTAS_REL = {}
# Relaciones de los libros anteriores que 1 Reyes repite: se añade la referencia a la nota.
REPITE_GN = [
    ("David_1", "Solomon_1", "padre", (2, 1), "mandó á Salomón su hijo"),
    ("David_1", "Adonijah_1", "padre", (1, 6), "su padre nunca lo entristeció"),
    ("Haggith_1", "Adonijah_1", "madre", (1, 5), "Adonía hijo de Haggith"),
    ("Zeruiah_1", "Joab_1", "madre", (2, 5), "Joab hijo de Sarvia"),
    ("Ner_1", "Abner_1", "padre", (2, 5), "Abner hijo de Ner"),
    ("Ithra_1", "Amasa_1", "padre", (2, 5), "Amasa hijo de Jether"),
    ("Gera_3", "Shimei_2", "padre", (2, 8), "Semei hijo de Gera"),
    ("Jehoiada_1", "Benaiah_1", "padre", (1, 8), "Benaía hijo de Joiada"),
    ("Ahilud_1", "Jehoshaphat_1", "padre", (4, 3), "Josaphat hijo de Ahilud"),
    ("Abiathar_1", "Jonathan_3", "padre", (1, 42), "Jonathán hijo de Abiathar"),
    ("Bathsheba_1", "Solomon_1", "madre", (2, 13), "Bath-sheba madre de Salomón"),
    ("Maoch_1", "Achish_1", "padre", (2, 39), "Achîs, hijo de Maachâ"),
    ("Nun_1", "Joshua_1", "padre", (16, 34), "Josué hijo de Nun"),
]
# Edades escritas (TM de la RV1909 y LXX de Brenton): índice de la cifra en cada texto.
EDADES = [
    ("Rehoboam_1", "en_evento", (14, 21), 0, 0, "cuando comienza a reinar (1 R 14:21)"),
    ("Jehoshaphat_3", "en_evento", (22, 42), 0, 0, "cuando comienza a reinar (1 R 22:42)"),
]
NOTAS_EXISTENTES = {
    "Ahijah_1": "1 R no lo nombra: Ahías silonita (1 R 11:29) es otra persona (Ahijah_1R11_1).",
    "Shammah_2": "1 R 1:8 «Semei» no se identifica con él (BibleData sí): ver Shimei_1R1_1.",
    "Nathan_2": "1 R 1: con Betsabé hace que David nombre rey a Salomón; con Sadoc lo unge en Gihón (1 R 1:34, 45).",
    "Solomon_1": ("1 R 1:39: Sadoc «ungió á Salomón»; reina «cuarenta años» (1 R 11:42) y «reinó en su lugar Roboam su "
                  "hijo» (1 R 11:43)."),
    "David_1": "1 R 2:10-11: muere y es sepultado en la ciudad de David; reinó «cuarenta años»: siete en Hebrón y treinta y tres en Jerusalén.",
    "Adonijah_1": "1 R 1:5: «Yo reinaré»; 1 R 2:25: Benaía lo mata por orden de Salomón. La RV1909 escribe «Adonía» en 1 Reyes.",
    "Joab_1": "1 R 2:28-34: huye al tabernáculo y Benaía lo mata junto al altar.",
    "Shimei_2": "1 R 2:36-46: Salomón le manda vivir en Jerusalén; sale a Gat por sus siervos y Benaía lo mata.",
    "Abiathar_1": "1 R 2:26-27: Salomón lo echa del sacerdocio a Anatot.",
    "Hiram_1": "1 R 5: hace pacto con Salomón y le da cedro y haya para el templo. Distinto de Hiram el artífice (1 R 7:13).",
}
NOTAS_VERIFICAR += [("TM", (1, 39), "ungió á Salomón"), ("TM", (11, 42), "cuarenta años"), ("TM", (2, 25), "Benaía hijo de Joiada"),
                    ("TM", (2, 11), "siete años reinó en Hebrón, y treinta y tres años reinó en Jerusalem"),
                    ("TM", (1, 5), "Yo reinaré"), ("TM", (2, 26), "Vete á Anathoth"), ("TM", (1, 45), "lo han ungido en Gihón")]
# Refs que el texto da a una persona y BibleData no sitúa.
REFS_EXTRA = {"Pharaoh_5": [(7, 8), (11, 1)], HIJA_FARAON: [(9, 16), (9, 24), (11, 1)], "Maacah_3": [(15, 13)],
              "Jeroboam_1": [(12, 2)]}
REFS_QUITAR = {}

S1 = "La sucesión de David (1 R 1–2)"
S2 = "La sabiduría y el reino de Salomón (1 R 3–4)"
S3 = "El templo y el palacio (1 R 5–8)"
S4 = "La gloria y la caída de Salomón (1 R 9–11)"
S5 = "La división del reino (1 R 12–14)"
S6 = "Los reyes de Judá e Israel (1 R 15–16)"
S7 = "Elías (1 R 17–19)"
S8 = "Acab: las guerras arameas, Nabot y Micaías (1 R 20–22)"
PASAJES = [
    ("1:1", "1:10", "David anciano; Adonías se hace rey", "Abisag sunamita sirve al rey anciano; Adonías, hijo de Haguit, dice «Yo reinaré» y hace banquete con Joab y Abiatar, sin llamar a Natán, Sadoc, Benaía ni Salomón.", S1),
    ("1:11", "1:31", "Betsabé y Natán ante David", "Natán y Betsabé recuerdan al rey su juramento; David jura que Salomón reinará después de él.", S1),
    ("1:32", "1:53", "Salomón ungido en Gihón", "Sadoc y Natán ungen a Salomón en Gihón y el pueblo grita «¡Viva el rey Salomón!»; Adonías se ase de los cuernos del altar y Salomón lo perdona.", S1),
    ("2:1", "2:12", "Últimas palabras y muerte de David", "David encarga a Salomón guardar la ley de Jehová y le habla de Joab, de los hijos de Barzilai y de Simei; muere tras reinar cuarenta años.", S1),
    ("2:13", "2:35", "Adonías, Abiatar y Joab", "Adonías pide a Abisag por mujer y Salomón lo manda matar; echa a Abiatar del sacerdocio, y Benaía mata a Joab junto al altar.", S1),
    ("2:36", "2:46", "Simei", "Salomón manda a Simei vivir en Jerusalén; a los tres años sale a Gat a buscar a sus siervos, y Benaía lo mata.", S1),
    ("3:1", "3:15", "Salomón pide sabiduría", "Salomón emparenta con Faraón; en Gabaón Jehová le aparece en sueños y él pide un corazón dócil para juzgar al pueblo.", S2),
    ("3:16", "3:28", "El juicio de las dos mujeres", "Dos mujeres se disputan un niño; el rey manda partirlo, y la verdadera madre se descubre por su compasión.", S2),
    ("4:1", "4:19", "Los príncipes y los gobernadores de Salomón", "Lista de los príncipes de Salomón y de sus doce gobernadores, cada uno con su región.", S2),
    ("4:20", "4:34", "La grandeza y la sabiduría de Salomón", "Judá é Israel comen y se alegran; Salomón señorea desde el río hasta Egipto, y su sabiduría excede a la de todos los orientales.", S2),
    ("5:1", "5:18", "Pacto con Hiram", "Hiram de Tiro da a Salomón cedro y haya del Líbano a cambio de trigo y aceite; Salomón impone una leva para la obra.", S3),
    ("6:1", "6:13", "Comienza el templo", "En el año cuatrocientos ochenta después de la salida de Egipto, en el cuarto de su reinado, Salomón comienza la casa de Jehová.", S3),
    ("6:14", "6:38", "El interior del templo", "Cedro, oro y querubines en el lugar santísimo; la casa queda acabada en el año undécimo: «Edificóla pues, en siete años».", S3),
    ("7:1", "7:12", "El palacio de Salomón", "Salomón edifica su casa en trece años, la casa del bosque del Líbano y una casa para la hija de Faraón.", S3),
    ("7:13", "7:39", "Hiram el artífice: columnas, mar y basas", "Hiram, hijo de una viuda de Neftalí, funde las columnas Jachîn y Boaz, el mar de fundición y las basas con sus fuentes.", S3),
    ("7:40", "7:51", "Los utensilios del templo", "Hiram acaba la obra de bronce; Salomón hace los utensilios de oro y mete en el templo lo que David había dedicado.", S3),
    ("8:1", "8:21", "El arca entra en el templo", "Los sacerdotes llevan el arca al lugar santísimo y la nube llena la casa; Salomón habla al pueblo.", S3),
    ("8:22", "8:53", "La oración de Salomón", "Salomón, ante el altar, pide a Jehová que oiga desde los cielos las oraciones que se hagan hacia esta casa.", S3),
    ("8:54", "8:66", "Bendición y dedicación", "Salomón bendice al pueblo; ofrecen sacrificios y celebran la fiesta catorce días.", S3),
    ("9:1", "9:9", "Jehová responde a Salomón", "Jehová aparece a Salomón por segunda vez: si anda en sus caminos confirmará su trono; si no, la casa será desechada.", S4),
    ("9:10", "9:28", "Ciudades, leva y naves", "Salomón da a Hiram veinte ciudades en Galilea, edifica ciudades con la leva y hace naves en Ezión-geber que van a Ofir.", S4),
    ("10:1", "10:13", "La reina de Seba", "La reina de Seba viene a probar a Salomón con preguntas y alaba su sabiduría.", S4),
    ("10:14", "10:29", "Las riquezas de Salomón", "Oro, escudos, el trono de marfil, las naves de Tarsis y los caballos de Egipto.", S4),
    ("11:1", "11:13", "Las mujeres de Salomón", "Las mujeres extranjeras inclinan el corazón de Salomón a otros dioses; Jehová le anuncia que romperá el reino.", S4),
    ("11:14", "11:25", "Adversarios: Hadad y Rezón", "Jehová levanta contra Salomón a Hadad edomita y a Rezón, que reina en Damasco.", S4),
    ("11:26", "11:43", "Jeroboam y Ahías; muere Salomón", "Ahías silonita rasga su capa nueva en doce pedazos y da diez a Jeroboam; Salomón muere y reina Roboam.", S4),
    ("12:1", "12:24", "Roboam y la división del reino", "Roboam endurece el yugo por consejo de los jóvenes; Israel se aparta de la casa de David y hace rey a Jeroboam.", S5),
    ("12:25", "12:33", "Los becerros de oro", "Jeroboam hace dos becerros de oro, los pone en Betel y en Dan y ordena una fiesta en el mes octavo.", S5),
    ("13:1", "13:10", "El varón de Dios en Betel", "Un varón de Dios anuncia contra el altar de Betel a Josías; la mano de Jeroboam se seca y el altar se rompe.", S5),
    ("13:11", "13:34", "El profeta viejo y el león", "Un profeta viejo engaña al varón de Dios para que coma en Betel; un león lo mata en el camino.", S5),
    ("14:1", "14:20", "Ahías y el hijo de Jeroboam", "La mujer de Jeroboam va disfrazada a Ahías, que anuncia la muerte del niño y el fin de la casa de Jeroboam.", S5),
    ("14:21", "14:31", "Roboam en Judá; Sisac", "Judá hace lo malo; Sisac rey de Egipto toma los tesoros del templo; Roboam muere y reina Abiam.", S5),
    ("15:1", "15:24", "Abiam y Asa", "Abiam reina tres años; Asa quita los ídolos, priva a Maaca de ser princesa y compra la ayuda de Ben-adad contra Baasa.", S6),
    ("15:25", "16:7", "Nadab y Baasa", "Baasa mata a Nadab y extermina la casa de Jeroboam; el profeta Jehú anuncia lo mismo contra la casa de Baasa.", S6),
    ("16:8", "16:28", "Ela, Zimri y Omri", "Zimri mata a Ela y reina siete días; Omri lo cerca en Tirsa, vence a Tibni y edifica Samaria.", S6),
    ("16:29", "16:34", "Acab y Jezabel", "Acab toma por mujer a Jezabel, sirve a Baal y le hace altar en Samaria; Hiel reedifica Jericó.", S6),
    ("17:1", "17:16", "Elías en Querit y en Sarepta", "Elías anuncia la sequía; los cuervos lo alimentan junto al arroyo de Querit, y en Sarepta la harina y el aceite de la viuda no se acaban.", S7),
    ("17:17", "17:24", "El hijo de la viuda", "Muere el hijo de la viuda; Elías clama a Jehová y el niño revive.", S7),
    ("18:1", "18:19", "Elías y Abdías", "Al tercer año Elías sale al encuentro de Acab; Abdías, que escondió cien profetas, lo lleva ante el rey.", S7),
    ("18:20", "18:40", "El monte Carmelo", "En el Carmelo los profetas de Baal claman en vano; el fuego de Jehová consume el holocausto de Elías.", S7),
    ("18:41", "18:46", "La lluvia", "Elías ora en la cumbre del Carmelo; una nube pequeña trae una gran lluvia.", S7),
    ("19:1", "19:8", "Elías huye al desierto", "Jezabel amenaza a Elías; él huye a Beerseba y al desierto, y un ángel le da de comer.", S7),
    ("19:9", "19:21", "Horeb; Eliseo", "En Horeb Jehová pasa en un silbo apacible y delicado; Elías echa su manto sobre Eliseo.", S7),
    ("20:1", "20:21", "Ben-adad cerca Samaria", "Ben-adad y treinta y dos reyes cercan Samaria; los criados de los príncipes de las provincias los vencen.", S8),
    ("20:22", "20:43", "Afec; Acab suelta a Ben-adad", "Los sirios caen otra vez en Afec; Acab hace alianza con Ben-adad y un profeta le anuncia su castigo.", S8),
    ("21:1", "21:16", "La viña de Nabot", "Nabot no quiere vender su viña; Jezabel hace que dos testigos lo acusen y es apedreado.", S8),
    ("21:17", "21:29", "Elías ante Acab", "Elías anuncia a Acab y a Jezabel su castigo; Acab se humilla y el mal se difiere.", S8),
    ("22:1", "22:28", "Micaías", "Acab y Josafat consultan a los profetas sobre Ramot de Galaad; Micaías, hijo de Imla, anuncia la derrota.", S8),
    ("22:29", "22:40", "Muere Acab en Ramot de Galaad", "Acab se disfraza; una flecha lo hiere y muere a la tarde; los perros lamen su sangre en Samaria.", S8),
    ("22:41", "22:53", "Josafat y Ocozías", "Josafat reina veinticinco años en Jerusalén; Ocozías, hijo de Acab, reina dos años sobre Israel y sirve a Baal.", S8),
]
# Citas de los resúmenes que van entre comillas (se comprueban).
CITAS_RESUMEN = [((1, 5), "Yo reinaré"), ((1, 39), "¡Viva el rey Salomón!"), ((6, 38), "Edificóla pues, en siete años")]

# ---------------------------------------------------------------- lugares
LUGARES_MANUAL = {}
PRECEDIDO = {}
EXCLUIR_LUGAR = {}
UNIR_LUGAR_MANUAL = {"a2fe63c": "ramot-galaad", "a736f6c": "mizpa-18-26"}  # Ramot de Galaad; Mizpa (15:22), como en 1 S
FORMAS_UNIR = {}
UNIR_LUGAR = {}
NOMBRE_LUGAR = {"Jerusalem": "Jerusalén", "Beth-el": "Betel", "Beer-seba": "Beerseba", "Beth-lehem": "Belén"}
NOMBRE_OB = {}
OBLIGATORIOS_LUGAR = ["jerusalen", "gabaon", "tiro", "sidon", "siquem", "betel", "dan", "tirsa", "horeb", "jezreel",
                      "ramot-galaad", "ezion-geber"]
LUGARES = {}
LUGAR_OPCIONAL = set()
# Lugares sin punto en el mapa aunque OpenBible proponga uno (como el Edén): la propuesta pasa a «alternativas».
SIN_UBICAR = {"tarsis": ("El texto no la sitúa (1 R 10:22; 22:49: naves «de Tharsis»). OpenBible propone Huelva (España) con "
                         "confianza baja (puntuación 90), y también Cerdeña, Cartago o Tarso: no hay acuerdo, y no se pone "
                         "en el mapa (alargaría el mapa base hasta el Atlántico). Las propuestas quedan como alternativas.")}
EXCL_AUTO = {}
INFO_AUTO = {}
moderno = josue.moderno
# «la ciudad de David»: el nombre de David forma parte del nombre del lugar (como en 2 Samuel): se quita la mención de
# persona para que se marque el lugar (se comprueba una por versículo).
LUGAR_NO_PERSONA = [((c, v), "David_1", "iudad de ") for c, v in ((2, 10), (3, 1), (8, 1), (11, 27), (14, 31), (15, 8),
                                                                    (15, 24), (22, 51))]
INFO_VERSIFICACION = {}


def comprobar_versificacion(rv, br, errores):
    """Recuentos, extremos, versículos sin LXX, desfase por capítulo, nombres paralelos y longitudes."""
    for c, n in enumerate(POR_CAPITULO, 1):
        hay = sum(1 for (cc, _) in rv if cc == c)
        if hay != n:
            errores.append(f"1 Reyes {c}: la RV1909 tiene {hay} versículos (numeración inglesa: {n})")
    vacios = sorted(k for k, t in rv.items() if not t.strip())
    if vacios != sorted(VACIOS):
        errores.append(f"1 Reyes: versículos vacíos {vacios} (se esperaban {sorted(VACIOS)})")
    for ref, ini in VERSIFICACION:
        if not rv.get(ref, "").startswith(ini):
            errores.append(f"Versificación de 1 R {ref[0]}:{ref[1]}: la RV1909 no empieza «{ini}»")
    for ref, fin in FIN_VERSICULO:
        if not rv.get(ref, "").endswith(fin):
            errores.append(f"Versificación de 1 R {ref[0]}:{ref[1]}: la RV1909 no termina «{fin}»")
    for ref, frag in VERSIFICACION_LXX:
        if frag not in br.get(ref, ""):
            errores.append(f"Brenton 1 R {ref[0]}:{ref[1]} (numeración RV) no dice «{frag}»")
    falta = {k for k in rv if k not in br}
    if falta != SIN_LXX or [k for k in br if k not in rv]:
        errores.append(f"1 Reyes: versículos sin Brenton {sorted(falta ^ SIN_LXX)} o de más {[k for k in br if k not in rv]}")
    costes = {}
    for c in range(1, CAPITULOS + 1):
        def coste(d):
            xs = [abs(math.log(len(rv[(c, v)]) / len(br[(c, v + d)]))) for (cc, v) in rv
                  if cc == c and rv[(c, v)] and (c, v) in br and (c, v + d) in br]
            return sum(xs) / len(xs)
        costes[c] = (coste(0), coste(-1), coste(1))
        if not costes[c][0] < min(costes[c][1:]):
            errores.append(f"Versificación de 1 R {c}: el emparejamiento con desfase compara mejor que sin él {costes[c]}")
    INFO_VERSIFICACION["desfase"] = {c: tuple(round(x, 2) for x in v) for c, v in costes.items()}
    comunes = {k for k in rv if k in br and rv[k]}
    for es, en in PARALELOS:
        a = {k for k in comunes if re.search(r"(?<!\w)%s(?!\w)" % re.escape(es), rv[k])}
        b = {k for k in comunes if re.search(r"(?<!\w)%s" % re.escape(en), br[k])}
        if a != b or not a:
            errores.append(f"Versificación de 1 R: «{es}» (RV1909) y «{en}» (Brenton) no caen en los mismos versículos: "
                           f"solo RV {sorted(a - b)}, solo LXX {sorted(b - a)}")
    for k in sorted(comunes):
        r = len(rv[k]) / len(br[k])
        if not PROPORCION[0] <= r <= PROPORCION[1]:
            errores.append(f"Versificación de 1 R {k[0]}:{k[1]}: longitud RV1909/Brenton fuera de rango ({r:.2f})")
    INFO_VERSIFICACION["comunes"] = len(comunes)
    INFO_VERSIFICACION["sin_lxx"] = len(falta)


def _reasignar_pv(filas, errores):
    """Aplica PV_REASIGNAR a las filas de BibleData-PersonVerse (copias) y comprueba que se usó cada entrada."""
    usadas, out = set(), []
    for r in filas:
        ref = REMAP_REF(tuple(map(int, r["reference_id"][4:].split(":"))))
        nuevo = PV_REASIGNAR.get((r["person_id"], ref))
        if nuevo:
            usadas.add((r["person_id"], ref))
            r = {**r, "person_id": nuevo}
        out.append(r)
    for k in set(PV_REASIGNAR) - usadas:
        errores.append(f"PV_REASIGNAR sin uso: {k}")
    return out


def construir(cx):
    rv, br, errores = cx["rv"], cx["br"], cx["errores"]
    comprobar_versificacion(rv, br, errores)
    for ref, frag in CITAS_RESUMEN:
        if frag not in rv.get(ref, ""):
            errores.append(f"Resumen de pasaje: «{frag}» no está en 1 R {ref[0]}:{ref[1]}")
    cx = {**cx, "pv_filas": _reasignar_pv(cx["pv_filas"], errores)}
    res = exodo.construir(cx, sys.modules[__name__])
    for x in res["relaciones"]:
        if (x["de"], x["a"], x["tipo"]) in INFERIDAS:
            x["certeza"] = "inferido"
    faltan = INFERIDAS - {(x["de"], x["a"], x["tipo"]) for x in res["relaciones"]}
    if faltan:
        errores.append(f"1 Reyes: relaciones inferidas sin crear {sorted(faltan)}")
    for p in res["nuevas"]:
        if p["id"] in SEXO_PROPIO:
            p["sexo"] = SEXO_PROPIO[p["id"]]  # id propio (no está en BibleData-Person)
    # Madre de Asa (15:10): sin vínculo conyugal con Abiam (el texto no lo da).
    de, a, tipo, ref, cita, nota = MADRE_ASA
    R = f"{LIBRO} {ref[0]}:{ref[1]}"
    if cita not in rv.get(ref, ""):
        errores.append(f"Cita no literal {R}: {cita!r}")
    x = {"de": de, "a": a, "tipo": tipo, "ref": R, "certeza": "explicito", "fuente": "rv1909", "nota": nota, "cita": cita}
    res["relaciones"].append(x)
    cx["relaciones"].append(x)
    # 4:5: «Azaría hijo de Nathán… Zabud hijo de Nathán»: dos Natán distintos en el mismo versículo (BibleData). La
    # primera mención es el padre de Azarías; la segunda, el de Zabud.
    t, R = rv[(4, 5)], f"{LIBRO} 4:5"
    pos = [m.start() for m in re.finditer(r"Nathán", t)]
    if len(pos) != 2 or any(m["ref"] == R and m["persona"].startswith("Nathan_") for m in res["menciones"]):
        errores.append(f"1 R 4:5: se esperaban dos «Nathán» sin asignar ({len(pos)})")
    else:
        for i, pid in zip(pos, ("Nathan_4", "Nathan_5")):
            res["menciones"].append({"ref": R, "persona": pid, "inicio": exodo._u16(t, i), "fin": exodo._u16(t, i + 6)})
        res["menciones"].sort(key=lambda m: (exodo.parse_ref(m["ref"]), m["inicio"]))
        res["ambiguos"] = [x for x in res["ambiguos"] if not x.startswith(R + " «Nathán»")]
    for ref, pid, antes in LUGAR_NO_PERSONA:
        R, t = f"{LIBRO} {ref[0]}:{ref[1]}", rv.get(ref, "")
        quitar = [m for m in res["menciones"] if m["ref"] == R and m["persona"] == pid
                  and t.encode("utf-16-le")[:2 * m["inicio"]].decode("utf-16-le").endswith(antes)]
        if len(quitar) != 1:
            errores.append(f"LUGAR_NO_PERSONA {R} {pid}: se esperaba una mención precedida de «{antes}» ({len(quitar)})")
        for m in quitar:
            res["menciones"].remove(m)
    return res


def construir_lugares(rv, menciones_personas, rutas, lugares_previos, errores, avisos, sa):
    global LUGARES, UNIR_LUGAR, EXCLUIR_LUGAR
    auto, unir = josue.lugares_auto(rv, rutas, lugares_previos, avisos, sys.modules[__name__])
    LUGARES = dict(LUGARES_MANUAL)
    for k, v in auto.items():
        if k not in UNIR_LUGAR_MANUAL:
            LUGARES.setdefault(k, v)
    UNIR_LUGAR = {**unir, **UNIR_LUGAR_MANUAL}
    EXCLUIR_LUGAR = {**EXCLUIR_LUGAR, **EXCL_AUTO}
    nuevos, menciones, info = exodo.construir_lugares(rv, menciones_personas, rutas, lugares_previos, errores, avisos, sa,
                                                      sys.modules[__name__])
    for l in nuevos:
        if l["id"] in SIN_UBICAR and l["ubicacion"]:
            u = {k: v for k, v in l["ubicacion"].items() if k != "confianza"}
            l["alternativas"] = [u] + l["alternativas"]
            l["ubicacion"] = None
            l["nota"] = (l["nota"] + " " + SIN_UBICAR[l["id"]]).strip()
    faltan = set(SIN_UBICAR) - {l["id"] for l in nuevos if not l["ubicacion"]}
    if faltan:
        errores.append(f"1 Reyes: SIN_UBICAR sin aplicar {sorted(faltan)}")
    return nuevos, menciones, info


# ---------------------------------------------------------------- hechos obligatorios (sobre los datos finales)
def comprobar(datos, errores):
    """Comprueba los hechos pedidos para 1 Reyes (falla si falta alguno). Devuelve líneas de informe."""
    P = {p["id"]: p for p in datos["personas"]}
    R = {(x["de"], x["a"], x["tipo"]): x for x in datos["relaciones"]}
    L = {l["id"]: l for l in datos["lugares"]}
    caps = [c for c in datos["capitulos"] if c["libro"] == LIBRO]
    texto = {f"{LIBRO} {c['cap']}:{v['n']}": v["texto"] for c in caps for v in c["versiculos"]}
    M = {(m["ref"], m["persona"]) for m in datos["menciones"]}
    ML = {(m["ref"], m["lugar"]) for m in datos["menciones_lugar"]}
    lineas = []

    def ok_(cond, desc):
        lineas.append(f"{'OK ' if cond else 'FALTA'} {desc}")
        if not cond:
            errores.append(f"Hecho obligatorio (1 Reyes): {desc}")

    def tiene(pid, ref, mencion=True):
        return ref in P.get(pid, {}).get("refs", []) and (not mencion or (ref, pid) in M)

    def rel(de, a, tipo, ref, certeza="explicito"):
        if tipo == "conyuge":
            de, a = sorted((de, a))
        x = R.get((de, a, tipo))
        return bool(x) and x["certeza"] == certeza and (
            x["ref"] == ref and (certeza != "explicito" or x.get("cita") and x["cita"] in texto.get(ref, ""))
            or f"{ref}:" in x["nota"])

    def sin_libro(pid, pref):
        return not any(r.startswith(pref) for r in P.get(pid, {}).get("refs", []))

    def rol(pid, frag):
        return frag in P.get(pid, {}).get("rol", "")

    def dice(ref, frag):
        return frag in texto.get(ref, "")

    ok_(len(caps) == CAPITULOS and len(texto) == VERSICULOS and [len(c["versiculos"]) for c in caps] == POR_CAPITULO
        and all(texto.values()), f"{CAPITULOS} capítulos y {VERSICULOS} versículos, ninguno vacío (hay {len(caps)} y {len(texto)})")
    ok_(dice("1R 4:34", "Y venían de todos los pueblos") and texto["1R 5:1"].startswith("HIRAM rey de Tiro")
        and texto["1R 22:51"].startswith("Y durmió Josaphat con sus padres") and dice("1R 22:53", "Porque sirvió á Baal"),
        "versificación: 4:34 / 5:1 como el inglés; 22:51 «Y durmió Josaphat» y 22:53 = hebreo 22:53-54")
    ok_(dice("1R 1:39", "ungió á Salomón") and dice("1R 1:39", "Sadoc sacerdote") and tiene("Zadok_1", "1R 1:39")
        and tiene("Solomon_1", "1R 1:39") and "2S 8:17" in P["Zadok_1"]["refs"], "1:39: Sadoc (el de 2 S) «ungió á Salomón»")
    ok_(dice("1R 3:1", "tomó la hija de Faraón") and tiene("Pharaoh_5", "1R 3:1") and rol("Pharaoh_5", "suegro de Salomón")
        and rel("Pharaoh_5", HIJA_FARAON, "padre", "1R 3:1") and rel("Solomon_1", HIJA_FARAON, "conyuge", "1R 7:8")
        and not any(r[:3] in ("Gn ", "Ex ") for r in P["Pharaoh_5"]["refs"]) and sin_libro("Pharaoh_5", "1R 14"),
        "3:1: Salomón «tomó la hija de Faraón» (Faraón suegro, Pharaoh_5, no es el del éxodo ni Sisac)")
    ok_(dice("1R 11:26", "Jeroboam hijo de Nabat, Ephrateo de Sereda") and dice("1R 11:26", "(su madre se llamaba Serva, mujer viuda)")
        and rel("Nebat_1", "Jeroboam_1", "padre", "1R 11:26") and rel("Zeruah_1", "Jeroboam_1", "madre", "1R 11:26")
        and rel("Nebat_1", "Zeruah_1", "conyuge", "1R 11:26", "inferido") and tiene("Zeruah_1", "1R 11:26"),
        "11:26: Jeroboam hijo de Nabat, efrateo de Sereda; su madre Serva, viuda (cónyuge de Nabat: inferido)")
    ok_(dice("1R 11:43", "reinó en su lugar Roboam su hijo") and dice("1R 14:21", "Roboam hijo de Salomón")
        and rel("Solomon_1", "Rehoboam_1", "padre", "1R 11:43") and tiene("Rehoboam_1", "1R 14:21")
        and rel("Naamah_2", "Rehoboam_1", "madre", "1R 14:21") and sin_libro("Rehoboam_1", "1R 11:40"),
        "11:43 y 14:21: Roboam, hijo de Salomón (y de Naama), reina en su lugar")
    ok_(dice("1R 16:23", "comenzó á reinar Omri sobre Israel") and tiene("Omri_1", "1R 16:23")
        and dice("1R 16:24", "compró él de Semer el monte de Samaria") and tiene("Shemer_1", "1R 16:24")
        and ("1R 16:24", "samaria") in ML, "16:23-24: Omri reina y compra a Semer el monte de Samaria")
    ok_(dice("1R 16:30", "Achâb hijo de Omri") and rel("Omri_1", "Ahab_1", "padre", "1R 16:28") and tiene("Ahab_1", "1R 16:30"),
        "16:30: «Achâb hijo de Omri»")
    ok_(dice("1R 16:31", "Jezabel hija de Ethbaal rey de los Sidonios") and rel("Ethbaal_1", "Jezebel_1", "padre", "1R 16:31")
        and rel("Ahab_1", "Jezebel_1", "conyuge", "1R 16:31") and rol("Ethbaal_1", "rey de los sidonios"),
        "16:31: Jezabel hija de Et-baal rey de los sidonios, mujer de Acab")
    ok_(dice("1R 17:1", "Elías Thisbita") and tiene("Elijah_1", "1R 17:1") and rol("Elijah_1", "tisbita"), "17:1: «Elías Thisbita»")
    ok_(dice("1R 19:16", "Jehú hijo de Nimsi") and dice("1R 19:16", "Eliseo hijo de Saphat, de Abelmehula")
        and rel("Nimshi_1", "Jehu_2", "padre", "1R 19:16") and rel("Shaphat_2", "Elisha_1", "padre", "1R 19:16")
        and tiene("Jehu_2", "1R 19:16") and sin_libro("Jehu_1", "1R 19") and sin_libro("Jehu_2", "1R 16")
        and ("Hanani_1", "Jehu_1", "padre") in R,
        "19:16: Jehú hijo de Nimsi (≠ Jehú profeta hijo de Hanani, 16:1) y Eliseo hijo de Safat, de Abel-mehola")
    ok_(dice("1R 21:1", "Naboth de Jezreel") and tiene("Naboth_1", "1R 21:1") and ("1R 21:1", "jezreel") in ML,
        "21:1: «Naboth de Jezreel»")
    ok_(dice("1R 22:40", "reinó en su lugar Ochôzías su hijo") and rel("Ahab_1", "Ahaziah_1", "padre", "1R 22:40")
        and tiene("Ahaziah_1", "1R 22:52") and tiene("Jehoram_1", "1R 22:51"), "22:40: «reinó en su lugar Ochôzías su hijo»")
    # identidades
    ok_(tiene("Nathan_2", "1R 1:8") and tiene("Nathan_2", "1R 1:45") and "2S 7:2" in P["Nathan_2"]["refs"]
        and sin_libro("Nathan_1", "1R ") and tiene("Nathan_4", "1R 4:5") and tiene("Nathan_5", "1R 4:5")
        and sin_libro("Nathan_2", "1R 4:"), "Natán profeta (1:8) es el de 2 S 7; los Natán de 4:5 son otros (BibleData)")
    ok_(sin_libro("Ahijah_1", "1R ") and all(tiene(AHIAS, r) for r in ("1R 11:29", "1R 14:2", "1R 15:29"))
        and "1S 14:3" in P["Ahijah_1"]["refs"] and tiene("Ahijah_3", "1R 15:27") and tiene("Ahijah_3", "1R 15:33")
        and tiene("Ahijah_2", "1R 4:3") and sin_libro(AHIAS, "1R 15:33"),
        "Ahías silonita (11:29) ≠ Ahías de 1 S 14:3; Ahía de 4:3 y el padre de Baasa (15:27, 33) son otros")
    ok_(tiene("Hiram_2", "1R 7:13") and sin_libro("Hiram_1", "1R 7:") and tiene("Hiram_1", "1R 5:1")
        and "2S 5:11" in P["Hiram_1"]["refs"], "Hiram rey de Tiro (el de 2 S 5:11) ≠ Hiram el artífice (7:13)")
    ok_(tiene("Shishak_1", "1R 14:25") and tiene("Shishak_1", "1R 11:40") and sin_libro("Pharaoh_5", "1R 11:40"),
        "Sisac (11:40; 14:25) no es el Faraón suegro")
    ok_(tiene(SEMEI, "1R 1:8") and sin_libro("Shammah_2", "1R ") and tiene("Shimei_2", "1R 2:8") and "2S 16:5" in P["Shimei_2"]["refs"]
        and tiene("Shimei_3", "1R 4:18") and rel("Ela_1", "Shimei_3", "padre", "1R 4:18"),
        "Simei hijo de Gera (2:8, el de 2 S 16) ≠ Semei de 1:8 ≠ Simei hijo de Ela (4:18)")
    ok_(tiene(BASEMAT, "1R 4:15") and sin_libro("Basemath_2", "1R ") and rel("Solomon_1", BASEMAT, "padre", "1R 4:15"),
        "Basemat hija de Salomón (4:15) no es Basemath_2 (mujer de Esaú)")
    ok_(tiene(MAHOL, "1R 4:31") and sin_libro("Zerah_3", "1R ") and rel(MAHOL, "Heman_1", "padre", "1R 4:31"),
        "Mahol (4:31) con id propio, no Zera hijo de Judá")
    ok_(tiene("Jehoshaphat_1", "1R 4:3") and tiene("Jehoshaphat_2", "1R 4:17") and tiene("Jehoshaphat_3", "1R 22:41")
        and sin_libro("Jehoshaphat_3", "1R 4") and tiene("Azariah_1", "1R 4:2") and tiene("Azariah_2", "1R 4:5")
        and sin_libro("Azariah_1", "1R 4:5"), "homónimos de 4: Josafat (4:3; 4:17; el rey) y Azarías (4:2; 4:5)")
    ok_(tiene("Hadad_3", "1R 11:14") and tiene("Zimri_2", "1R 16:9") and sin_libro("Zimri_1", "1R ")
        and tiene("Nadab_2", "1R 15:25") and sin_libro("Nadab_1", "1R ") and tiene("Abiram_2", "1R 16:34")
        and sin_libro("Abiram_1", "1R "), "Hadad edomita; Zimri, Nadab y Abiram de 1 R no son los de Nm/Ex")
    ok_(not [p for p in EXCLUIR if any(r.startswith("1R ") for r in P.get(p, {}).get("refs", []))]
        and P.get(REINA_SEBA, {}).get("sin_nombre") and P.get(HIJA_FARAON, {}).get("sin_nombre"),
        "sin personas para Dios, «NA» ni el ángel; la reina de Seba y la hija de Faraón sin nombre")
    x = R.get(("Maacah_3", "Asa_1", "madre"))
    ok_(bool(x) and x["ref"] == "1R 15:10" and "no se armoniza" in x["nota"] and rel("Maacah_3", "Abijam_1", "madre", "1R 15:2")
        and ("Abijam_1", "Maacah_3", "conyuge") not in R, "Maaca, madre de Abiam (15:2) y de Asa (15:10), sin cónyuge inventado")
    e = {(x["persona"], x["tradicion"]): x["valor"] for x in datos["edades"] if x["ref"].startswith("1R ")}
    ok_(e.get(("Rehoboam_1", "TM")) == 41 and e.get(("Rehoboam_1", "LXX")) == 41 and e.get(("Jehoshaphat_3", "TM")) == 35
        and e.get(("Jehoshaphat_3", "LXX")) == 35, f"edades de 1 R {sorted(e.items())}")
    for lid, ref in (("jerusalen", "1R 3:1"), ("gabaon", "1R 3:4"), ("tiro", "1R 5:1"), ("sidon", "1R 17:9"),
                     ("siquem", "1R 12:1"), ("betel", "1R 12:29"), ("dan", "1R 12:29"), ("tirsa", "1R 15:33"),
                     ("samaria", "1R 16:24"), ("sarepta", "1R 17:9"), ("carmel", "1R 18:19"), ("horeb", "1R 19:8"),
                     ("jezreel", "1R 21:1"), ("ramot-galaad", "1R 22:3"), ("ezion-geber", "1R 9:26")):
        ok_(lid in L and ref in L[lid]["refs"] and (ref, lid) in ML, f"lugar {lid} en {ref}")
    ok_("Carmelo" in L["carmel"]["formas_rv1909"] and "Sarepta" in L["sarepta"]["formas_rv1909"],
        "Carmelo (18:19) y Sarepta (17:9) con su forma")
    sin = [l for l in datos["lugares"] if any(r.startswith("1R ") for r in l["refs"]) and not l["ubicacion"]]
    ok_(all("OpenBible no da identificación" in l["nota"] or l["id"] in SIN_UBICAR for l in sin)
        and not (L.get("tarsis") or {}).get("ubicacion"), f"lugares de 1 R sin coordenadas con nota ({len(sin)}); Tarsis sin punto")
    pas = [p for p in datos["pasajes"] if p["libro"] == LIBRO]
    ok_(len(pas) == len(PASAJES) and pas[0]["inicio"] == "1R 1:1" and pas[-1]["fin"] == "1R 22:53" and pas[0]["id"] == "1r-01",
        f"{len(pas)} pasajes 1r-NN de 1R 1:1 a 1R 22:53")
    ok_(len({p["seccion"] for p in pas}) == 8, "8 secciones")
    ids = [p["id"] for p in datos["pasajes"]]
    ult_2s = max(i for i, p in enumerate(datos["pasajes"]) if p["libro"] == "2S")
    lb = [l["id"] for l in datos["libros"]]
    ok_(ids.index(pas[0]["id"]) == ult_2s + 1 and lb.index(LIBRO) == lb.index("2S") + 1
        and (lb[-1] == LIBRO or lb[lb.index(LIBRO) + 1] == "2R"),
        "1 Reyes va justo después de 2 Samuel en el orden de los pasajes (lectura en orden) y antes de 2 Reyes (si está)")
    return lineas
