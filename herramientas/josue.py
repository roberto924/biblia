"""Josué 1–24: personas, relaciones, edades, pasajes, menciones y lugares (lo usa construir_datos.py).

Reutiliza la lógica de exodo.py (exodo.construir / exodo.construir_lugares con este módulo como configuración),
igual que numeros.py y deuteronomio.py. Cada dato lleva versículo, fuente y certeza; las citas se comprueban
literalmente contra la RV1909 (TM) o Brenton (LXX). Las personas de Génesis–Deuteronomio (Josué, Caleb, Eleazar,
José, las hijas de Zelofehad, los hijos de Anac…) son la misma persona (mismo id de BibleData): se amplían sus `refs`.

Versificación (comprobada al generar): la RV1909 de eBible numera Josué como la inglesa (658 versículos, ninguno
vacío, mismos recuentos por capítulo), incluidos Jos 21:36-37 (las ciudades levíticas de Rubén), que faltan en el
Códice de Leningrado y están en otros manuscritos hebreos, en la LXX y en las Biblias castellanas e inglesas.
BibleData y OpenBible usan esa numeración: no hace falta REMAP_REF. Brenton (643 versículos: la LXX es más corta en
Jos 6, 8, 10, 13 y 20) ordena Jos 24:29-31 de otro modo (su 24:29 es el 24:31 de la RV); `br_a_rv` lo pasa a la
numeración de la RV1909 en un solo punto. La adición griega tras 21:42 (los cuchillos de pedernal) no está en el
Brenton de eBible (21:42 dice solo «and their suburbs…»); la de 24:33 tampoco: no se usan.

Lugares: Josué nombra cientos de lugares (reyes vencidos, fronteras y ciudades por tribus, ciudades de refugio y
levíticas). Los ya registrados amplían sus refs; los nuevos de OpenBible entran automáticamente (`lugares_auto`)
con la forma RV1909 detectada en cada versículo y la misma regla de confianza; la grafía actual del nombre se adapta
por regla (`moderno`) salvo los fijados en `NOMBRE_LUGAR`, y lo dice la nota. Solo biblioteca estándar.
"""
import json
import re
import sys
from collections import Counter

import exodo
import lugares_mapa as lm
import nombres_auto as na

LIBRO = "Jos"
NOMBRE = "Josué"
USX = "JOS"
CAPITULOS = 24
VERSICULOS = 658
# Versículos por capítulo en la numeración inglesa (KJV); la RV1909 de eBible coincide (se comprueba).
POR_CAPITULO = [18, 24, 17, 24, 15, 27, 26, 35, 27, 43, 23, 24, 33, 15, 63, 10, 18, 28, 51, 9, 45, 34, 16, 33]
# Comienzo de los versículos donde las tradiciones difieren (se comprueba).
VERSIFICACION = [((21, 36), "Y de la tribu de Rubén, á Beser con sus ejidos"), ((21, 37), "A Cedemoth con sus ejidos"),
                 ((21, 38), "De la tribu de Gad"), ((24, 29), "Y después de estas cosas murió Josué"),
                 ((24, 30), "Y enterráronlo en el término de su posesión"), ((24, 33), "También murió Eleazar")]
# Brenton ya pasado a la numeración RV (br_a_rv): los versículos que se usan dicen lo mismo que la RV1909.
VERSIFICACION_LXX = [((4, 19), "on the tenth day of the first month"), ((14, 7), "I was forty years old"),
                     ((14, 10), "this day eighty-five years old"), ((14, 10), "the forty-fifth year"),
                     ((24, 29), "Joshua the son of Naue the servant of the Lord died"), ((24, 30), "Thamnasarach"),
                     ((24, 31), "Israel served the Lord all the days of Joshua"), ((24, 32), "the bones of Joseph"),
                     ((24, 33), "Eleazar the high-priest the son of Aaron died"), ((21, 36), "Bosor in the wilderness")]


def br_a_rv(br):
    """Brenton (orden de la LXX) -> numeración de la RV1909. Único punto: Jos 24:29-31.
    LXX 24:29 (Israel sirvió a Jehová) = RV 24:31; LXX 24:30 (muere Josué) = RV 24:29; LXX 24:31 (sepultura) = RV 24:30."""
    out = dict(br)
    if all(k in br for k in ((24, 29), (24, 30), (24, 31))):
        out[(24, 29)], out[(24, 30)], out[(24, 31)] = br[(24, 30)], br[(24, 31)], br[(24, 29)]
    return out


# Personas de BibleData que no se crean: Dios, «NA», el príncipe del ejército de Jehová (Jos 5:14, como el ángel
# en Números), los reyes sin nombre («King of Jericho»… como en Números), «Ben-ammi» (los hijos de Ammón, pueblo) y
# «Jashar» (Jos 10:13 «el libro de Jasher» es el título de un libro, no un personaje del relato).
EXCLUIR = {"YHVH_1", "NA", "the captain of the host of the LORD_1", "Ben-ammi_1", "Jashar_1",
           "King of Jericho_1", "King of Makkedah_1", "King of Shimron_1", "King of Achshaph_1", "King of Debir_1",
           "King of Geder_1", "King of Hormah_1", "King of Arad_2", "King of Libnah_1", "King of Adullam_1",
           "King of Bethel_1", "King of Tappuah_1", "King of Hepher_1", "King of Aphek_1", "King of Lasharon_1",
           "King of Shimron-meron_1", "King of Taanach_1", "King of Megiddo_1", "King of Kedesh_1", "King of Jokneam_1",
           "King of Dor_1", "King of Goiim in Gilgal_1", "King of Tirzah_1"}
# «Israel» casi siempre es el pueblo (cananeos, heteos, gabaonitas… no son personas en BibleData).
SOLO_ETIQUETA = {"Jacob_1": {"Jacob"}}
FORMA_NO_MENCION = {("Jacob_1", "israel")}
PV_DESCARTAR = {
    ("Arba_1", (12, 24)): "Jos 12:24 es el rey de Tirsa; no nombra a Arba (probable errata de BibleData).",
}
REL_DESCARTAR = {}
FORMAS_FORZADAS = {"Adoni-zedek_1": ["Adonisedec"], "Hoham_1": ["Oham"], "Piram_1": ["Phiream"], "Horam_1": ["Horam"],
                   "Jabin_1": ["Jabín"], "Arba_1": ["Arba"], "Achsah_1": ["Axa"], "Othniel_1": ["Othoniel"],
                   "Kenaz_2": ["Cenez"], "Achan_1": ["Achân"], "Bohan_1": ["Bohán"]}
MODERNO = {
    "Rahab_1": "Rahab", "Achan_1": "Acán", "Carmi_2": "Carmi", "Zabdi_1": "Zabdi", "Adoni-zedek_1": "Adonisedec",
    "Hoham_1": "Hoham", "Piram_1": "Piream", "Japhia_1": "Jafía", "Debir_1": "Debir", "Horam_1": "Horam",
    "Jabin_1": "Jabín", "Jobab_3": "Jobab", "Arba_1": "Arba", "Bohan_1": "Bohán", "Achsah_1": "Acsa",
    "Othniel_1": "Otoniel", "Kenaz_2": "Quenaz",
}
_REY = "Rey de {c}, uno de los cinco reyes amorreos que atacan Gabaón (Jos 10:3-5); muere en Maceda (Jos 10:26)."
NOTAS = {
    "Rahab_1": ("Jos 2:1: «una mujer ramera que se llamaba Rahab», de Jericó; esconde a los espías y es salvada con la "
                "casa de su padre (Jos 6:25: «habitó ella entre los Israelitas hasta hoy»)."),
    "Achan_1": ("Jos 7:1: «Achân, hijo de Carmi, hijo de Zabdi, hijo de Zera, de la tribu de Judá»; toma del anatema y "
                "lo apedrean en el valle de Acor (Jos 7:24-26). Jos 7:24 lo llama «Achân hijo de Zera» (descendiente)."),
    "Carmi_2": "Padre de Acán, de Judá (Jos 7:1). Distinto de Carmi hijo de Rubén (Gn 46:9).",
    "Zabdi_1": "Abuelo de Acán, hijo de Zera, de Judá (Jos 7:1).",
    "Adoni-zedek_1": "Jos 10:1: «Adonisedec rey de Jerusalem». Reúne a los reyes amorreos contra Gabaón (Jos 10:3-5).",
    "Hoham_1": _REY.format(c="Hebrón") + " La RV1909 escribe «Oham».",
    "Piram_1": _REY.format(c="Jarmut («Jerimoth» en la RV1909)") + " La RV1909 escribe «Phiream».",
    "Japhia_1": _REY.format(c="Laquis") + " Distinto de la ciudad de Jafía (Jos 19:12).",
    "Debir_1": _REY.format(c="Eglón") + " Distinto de la ciudad de Debir.",
    "Horam_1": "Jos 10:33: «Horam, rey de Gezer», sube en ayuda de Laquis y es vencido.",
    "Jabin_1": ("Jos 11:1: «Jabín rey de Hasor» convoca a los reyes del norte; Josué toma Hazor y la quema (Jos 11:10-11). "
                "Puede no ser el Jabín de Jueces 4 (el texto no lo dice)."),
    "Jobab_3": "Jos 11:1: «Jobab rey de Madón». Distinto de Jobab de Gn 10:29 y del rey de Edom (Gn 36:33).",
    "Arba_1": ("Jos 14:15: Hebrón «fué antes llamada Chîriath-arba; fué [Arba] un hombre grande entre los Anaceos» (el "
               "nombre va entre corchetes en la RV1909: palabra añadida por el traductor). Jos 15:13: «Chîriath-arba, "
               "del padre de Anac»."),
    "Bohan_1": "Jos 15:6 y 18:17: «la piedra de Bohán, hijo de Rubén», hito del límite entre Judá y Benjamín (descendiente de Rubén).",
    "Achsah_1": "Hija de Caleb (Jos 15:16); Caleb la da por mujer a Otoniel, que toma Quiriat-sefer (Jos 15:17).",
    "Othniel_1": ("Jos 15:17: «Othoniel, hijo de Cenez, hermano de Caleb»: el texto no deja claro si el hermano de Caleb "
                  "es Otoniel o Cenez."),
    "Kenaz_2": ("Padre de Otoniel (Jos 15:17). BibleData lo toma por hermano de Caleb; Jos 15:17 se puede leer así o "
                "referirlo a Otoniel. Distinto de Cenez hijo de Elifaz (Gn 36:11)."),
}
IDENTIDAD = {}
NOTAS_VERIFICAR = [
    ("TM", (2, 1), "una mujer ramera que se llamaba Rahab"), ("TM", (6, 25), "habitó ella entre los Israelitas hasta hoy"),
    ("TM", (7, 1), "Achân, hijo de Carmi, hijo de Zabdi, hijo de Zera, de la tribu de Judá"),
    ("TM", (7, 24), "Achân hijo de Zera"), ("TM", (10, 1), "Adonisedec rey de Jerusalem"), ("TM", (10, 3), "Oham rey de Hebrón"),
    ("TM", (10, 3), "Phiream rey de Jerimoth"), ("TM", (10, 3), "Japhia rey de Lachîs"), ("TM", (10, 3), "Debir rey de Eglón"),
    ("TM", (10, 33), "Horam, rey de Gezer"), ("TM", (11, 1), "Jabín rey de Hasor"), ("TM", (11, 1), "Jobab rey de Madón"),
    ("TM", (14, 15), "fué antes llamada Chîriath-arba; fué [Arba] un hombre grande entre los Anaceos"),
    ("TM", (15, 13), "Chîriath-arba, del padre de Anac"), ("TM", (15, 6), "la piedra de Bohán, hijo de Rubén"),
    ("TM", (15, 17), "Othoniel, hijo de Cenez, hermano de Caleb"), ("TM", (24, 29), "siendo de ciento y diez años"),
    ("TM", (24, 30), "Timnath-sera, que está en el monte de Ephraim"), ("TM", (24, 32), "los huesos de José"),
    ("TM", (24, 33), "al cual enterraron en el collado de Phinees su hijo"),
    ("TM", (14, 7), "Yo era de edad de cuarenta años, cuando Moisés siervo de Jehová me envió de Cades-barnea"),
    ("TM", (14, 10), "estos cuarenta y cinco años"), ("TM", (14, 10), "soy hoy día de ochenta y cinco años"),
    ("TM", (15, 14), "Sesai, Aiman, y Talmai, hijos de Anac"), ("TM", (17, 3), "Maala, Noa, Hogla, Milchâ, y Tirsa"),
]
_RR = "rey vencido por Josué"
ROLES = {
    "Rahab_1": ("mujer de Jericó que esconde a los espías", (2, 1), "una mujer ramera que se llamaba Rahab"),
    "Adoni-zedek_1": ("rey de Jerusalén, " + _RR, (10, 1), "Adonisedec rey de Jerusalem"),
    "Hoham_1": ("rey de Hebrón, " + _RR, (10, 3), "Oham rey de Hebrón"),
    "Piram_1": ("rey de Jarmut, " + _RR, (10, 3), "Phiream rey de Jerimoth"),
    "Japhia_1": ("rey de Laquis, " + _RR, (10, 3), "Japhia rey de Lachîs"),
    "Debir_1": ("rey de Eglón, " + _RR, (10, 3), "Debir rey de Eglón"),
    "Horam_1": ("rey de Gezer, " + _RR, (10, 33), "Horam, rey de Gezer"),
    "Jabin_1": ("rey de Hazor, " + _RR, (11, 1), "Jabín rey de Hasor"),
    "Jobab_3": ("rey de Madón, " + _RR, (11, 1), "Jobab rey de Madón"),
    "Bohan_1": ("su piedra marca el límite de Judá y Benjamín", (15, 6), "la piedra de Bohán, hijo de Rubén"),
}
SIN_NOMBRE = {}
# Relaciones que dice el versículo (se añaden con cita; si BibleData ya la tiene, se sustituye por esta).
RELACIONES = [
    ("Carmi_2", "Achan_1", "padre", (7, 1), "Achân, hijo de Carmi", ""),
    ("Zabdi_1", "Carmi_2", "padre", (7, 1), "Carmi, hijo de Zabdi", ""),
    ("Zerah_3", "Zabdi_1", "padre", (7, 1), "Zabdi, hijo de Zera, de la tribu de Judá",
     "Zera hijo de Judá (Gn 38:30), por «de la tribu de Judá»; identificación de BibleData."),
    ("Arba_1", "Anak_1", "padre", (15, 13), "Chîriath-arba, del padre de Anac",
     "La ciudad lleva el nombre de Arba, «padre de Anac» (también Jos 21:11)."),
    ("Caleb_1", "Achsah_1", "padre", (15, 16), "mi hija Axa", ""),
    ("Kenaz_2", "Othniel_1", "padre", (15, 17), "Othoniel, hijo de Cenez", ""),
    ("Achsah_1", "Othniel_1", "conyuge", (15, 17), "él le dió por mujer á su hija Axa", ""),
]
NOTAS_REL = {}
# Relaciones de los libros anteriores que Josué repite: se añade la referencia a la nota.
REPITE_GN = [
    ("Nun_1", "Joshua_1", "padre", (1, 1), "Josué hijo de Nun"),
    ("Nun_1", "Joshua_1", "padre", (24, 29), "Josué, hijo de Nun"),
    ("Jephunneh_1", "Caleb_1", "padre", (14, 6), "Caleb, hijo de Jephone"),
    ("Aaron_1", "Eleazar_1", "padre", (24, 33), "Eleazar, hijo de Aarón"),
    ("Eleazar_1", "Phinehas_1", "padre", (22, 13), "Phinees hijo de Eleazar"),
    ("Beor_2", "Balaam_1", "padre", (13, 22), "Balaam adivino, hijo de Beor"),
    ("Zippor_1", "Balak_1", "padre", (24, 9), "Balac hijo de Sephor"),
    ("Hamor_1", "Shechem_1", "padre", (24, 32), "Hemor padre de Sichêm"),
    ("Hepher_1", "Zelophehad_1", "padre", (17, 3), "Salphaad, hijo de Hepher"),
    ("Gilead_1", "Hepher_1", "padre", (17, 3), "Hepher, hijo de Galaad"),
    ("Machir_1", "Gilead_1", "padre", (17, 3), "Galaad, hijo de Machîr"),
    ("Manasseh_1", "Machir_1", "padre", (17, 3), "Machîr, hijo de Manasés"),
    ("Zelophehad_1", "Mahlah_1", "padre", (17, 3), "Maala"), ("Zelophehad_1", "Noah_2", "padre", (17, 3), "Noa"),
    ("Zelophehad_1", "Hoglah_1", "padre", (17, 3), "Hogla"), ("Zelophehad_1", "Milcah_2", "padre", (17, 3), "Milchâ"),
    ("Zelophehad_1", "Tirzah_1", "padre", (17, 3), "Tirsa"),
]
# Edades escritas: (persona, tipo, ref, índice de cifra TM, índice LXX, evento). La LXX es Brenton ya pasado a la
# numeración RV (br_a_rv): «muere Josué» es el 24:30 de Brenton.
EDADES = [("Joshua_1", "total", (24, 29), 0, 0, ""),
          ("Caleb_1", "en_evento", (14, 7), 0, 0, "cuando Moisés lo envió de Cades-barnea a reconocer la tierra (Jos 14:7)"),
          ("Caleb_1", "en_evento", (14, 10), 1, 1, "al pedir Hebrón a Josué («soy hoy día», Jos 14:10)")]
NOTAS_EXISTENTES = {
    "Joshua_1": ("Muere a los 110 años (Jos 24:29: «siendo de ciento y diez años») y lo entierran en Timnat-sera, «que está "
                 "en el monte de Ephraim» (Jos 24:30), la ciudad que había pedido (Jos 19:50)."),
    "Caleb_1": ("Jos 14:7-10: tenía cuarenta años cuando Moisés lo envió de Cades-barnea y «ochenta y cinco» cuando pide "
                "Hebrón, «estos cuarenta y cinco años» después (40 + 45 = 85, cálculo comprobado); recibe Hebrón (Jos 14:13)."),
    "Eleazar_1": "Muere y lo entierran «en el collado de Phinees su hijo», en el monte de Efraín (Jos 24:33).",
    "Joseph_1": "Sus huesos, traídos de Egipto, se entierran en Siquem, en el campo que compró Jacob (Jos 24:32).",
    "Anak_1": "Jos 15:14: Caleb echa de Hebrón a «Sesai, Aiman, y Talmai, hijos de Anac» (los de Nm 13:22).",
    "Ahiman_1": "En Jos 15:14 la RV1909 escribe «Aiman».",
    "Zelophehad_1": "Jos 17:3-4: sus hijas reclaman ante Eleazar y Josué la heredad que Moisés mandó darles (Nm 27).",
}
REFS_EXTRA = {"Arba_1": [(14, 15)]}
# BibleData atribuye a Adonisedec (rey de Jerusalén, Jos 10:1) los versículos del rey de Hai (Jos 8) y de los
# reyes de Jericó y Hai (Jos 12:9), que el texto no nombra y son otras personas.
REFS_QUITAR = {"Adoni-zedek_1": [(8, 1), (8, 14), (8, 23), (8, 29), (12, 9)]}

S1 = "Entrada en la tierra y paso del Jordán (Jos 1–5)"
S2 = "Jericó y Hai (Jos 6–8)"
S3 = "Gabaón y las campañas del sur y del norte (Jos 9–12)"
S4 = "El reparto de la tierra (Jos 13–21)"
S5 = "El altar junto al Jordán (Jos 22)"
S6 = "Despedida de Josué y pacto en Siquem (Jos 23–24)"
PASAJES = [
    ("1:1", "1:9", "Dios habla a Josué", "Muerto Moisés, Dios manda a Josué pasar el Jordán con el pueblo: «Esfuérzate y sé valiente».", S1),
    ("1:10", "1:18", "Preparativos para pasar", "Josué manda prevenir comida; Rubén, Gad y la media tribu de Manasés pasarán armados delante de sus hermanos.", S1),
    ("2:1", "2:14", "Rahab esconde a los espías", "Josué envía dos espías desde Sitim a Jericó; Rahab los esconde en su terrado y les pide un juramento.", S1),
    ("2:15", "2:24", "El cordón de grana", "Rahab los descuelga por la ventana; atará a ella un cordón de grana para que su casa se salve.", S1),
    ("3:1", "3:17", "El arca abre paso en el Jordán", "Los sacerdotes entran en el río con el arca; las aguas se detienen y el pueblo pasa en seco frente a Jericó.", S1),
    ("4:1", "4:14", "Las doce piedras del Jordán", "Un hombre por tribu saca una piedra del río; Josué pone otras doce en medio del Jordán.", S1),
    ("4:15", "4:24", "Las piedras de Gilgal", "Salen los sacerdotes y vuelven las aguas; el día diez del mes primero acampan en Gilgal y levantan las piedras.", S1),
    ("5:1", "5:12", "Circuncisión y Pascua en Gilgal", "Los nacidos en el desierto son circuncidados; celebran la Pascua y cesa el maná.", S1),
    ("5:13", "6:5", "El príncipe del ejército de Jehová", "Junto a Jericó un varón con la espada desnuda se presenta como príncipe del ejército de Jehová; la orden de rodear la ciudad.", S2),
    ("6:6", "6:21", "Caen los muros de Jericó", "Siete días rodean la ciudad con el arca y las bocinas; al séptimo el pueblo grita, cae el muro y destruyen la ciudad.", S2),
    ("6:22", "6:27", "Rahab es salvada", "Los espías sacan a Rahab y a su familia; queman la ciudad y Josué maldice a quien la reedifique.", S2),
    ("7:1", "7:15", "Derrota en Hai", "Acán toma del anatema; Israel huye ante Hai y Josué se postra; Dios manda buscar al culpable.", S2),
    ("7:16", "7:26", "Acán es descubierto", "La suerte cae sobre Acán, que confiesa haber escondido un manto, plata y oro; es apedreado en el valle de Acor.", S2),
    ("8:1", "8:17", "La emboscada contra Hai", "Josué pone una emboscada detrás de la ciudad y finge huir; los de Hai salen tras Israel y dejan la ciudad abierta.", S2),
    ("8:18", "8:29", "Hai es tomada", "Josué extiende la lanza, la emboscada entra y quema la ciudad; el rey de Hai muere.", S2),
    ("8:30", "8:35", "El altar en el monte Ebal", "Josué edifica un altar en el Ebal, escribe la ley en piedras y la lee ante todo Israel, entre Ebal y Gerizim.", S2),
    ("9:1", "9:15", "El engaño de los gabaonitas", "Los de Gabaón fingen venir de tierra lejana con pan seco y odres rotos; Israel hace alianza sin consultar a Dios.", S3),
    ("9:16", "9:27", "Leñadores y aguadores", "Se descubre el engaño; por el juramento no los matan, pero serán leñadores y aguadores.", S3),
    ("10:1", "10:15", "Cinco reyes contra Gabaón; el sol se detiene", "Adonisedec y otros cuatro reyes atacan Gabaón; Josué acude desde Gilgal: «Sol, detente en Gabaón».", S3),
    ("10:16", "10:27", "La cueva de Maceda", "Los cinco reyes se esconden en una cueva de Maceda; Josué los saca y los mata.", S3),
    ("10:28", "10:43", "Las ciudades del sur", "Josué toma Maceda, Libna, Laquis, Eglón, Hebrón y Debir, y vuelve a Gilgal.", S3),
    ("11:1", "11:15", "La coalición del norte", "Jabín rey de Hazor reúne a los reyes del norte junto a las aguas de Merom; Josué los vence y quema Hazor.", S3),
    ("11:16", "11:23", "Toda la tierra tomada", "Josué toma la tierra desde el monte Halac hasta Baal-gad y destruye a los anaceos; la tierra reposa.", S3),
    ("12:1", "12:6", "Los reyes vencidos al oriente", "Sehón y Og, vencidos por Moisés; su tierra dada a Rubén, Gad y la media tribu de Manasés.", S3),
    ("12:7", "12:24", "Los reyes vencidos al occidente", "Lista de los treinta y un reyes que venció Josué al occidente del Jordán.", S3),
    ("13:1", "13:14", "La tierra que queda por tomar", "Josué es viejo y queda mucha tierra; Dios le manda repartirla; Leví no tiene heredad.", S4),
    ("13:15", "13:33", "Rubén, Gad y la media tribu de Manasés", "Las heredades que Moisés dio al oriente del Jordán, con sus ciudades.", S4),
    ("14:1", "14:15", "Caleb pide Hebrón", "Comienza el reparto en Canaán; Caleb, de ochenta y cinco años, pide el monte que le prometió Moisés y recibe Hebrón.", S4),
    ("15:1", "15:12", "Los límites de Judá", "El término de Judá por el sur, el oriente, el norte y el occidente.", S4),
    ("15:13", "15:19", "Caleb, Otoniel y Acsa", "Caleb echa de Hebrón a los hijos de Anac; Otoniel toma Debir y recibe a Acsa, que pide fuentes de aguas.", S4),
    ("15:20", "15:32", "Ciudades de Judá: el sur", "Las ciudades de Judá hacia el término de Edom, al mediodía.", S4),
    ("15:33", "15:47", "Ciudades de Judá: los llanos y la costa", "Las ciudades de los llanos y las de Ecrón, Asdod y Gaza hasta el río de Egipto.", S4),
    ("15:48", "15:63", "Ciudades de las montañas y del desierto", "Las ciudades de las montañas de Judá y del desierto; los jebuseos siguen en Jerusalén.", S4),
    ("16:1", "16:10", "La heredad de Efraín", "La suerte de los hijos de José y el término de Efraín; el cananeo sigue en Gezer.", S4),
    ("17:1", "17:18", "Manasés y las hijas de Zelofehad", "La heredad de Manasés; las hijas de Zelofehad reciben su parte; los hijos de José piden más tierra.", S4),
    ("18:1", "18:10", "Siloh: se describe la tierra", "El tabernáculo se levanta en Siloh; Josué envía hombres a describir la tierra y la reparte por suertes.", S4),
    ("18:11", "18:28", "La heredad de Benjamín", "El término de Benjamín entre Judá y José, y sus ciudades.", S4),
    ("19:1", "19:9", "La heredad de Simeón", "Simeón recibe su heredad dentro de la de Judá.", S4),
    ("19:10", "19:23", "Zabulón e Isacar", "Los términos y las ciudades de Zabulón y de Isacar.", S4),
    ("19:24", "19:39", "Aser y Neftalí", "Los términos y las ciudades de Aser y de Neftalí.", S4),
    ("19:40", "19:51", "Dan; la heredad de Josué", "La heredad de Dan, que toma Lesem; Israel da a Josué Timnat-sera; termina el reparto en Siloh.", S4),
    ("20:1", "20:9", "Las ciudades de refugio", "Seis ciudades para el que mata sin querer: Cedes, Siquem y Quiriat-arba; Beser, Ramot y Golán.", S4),
    ("21:1", "21:19", "Ciudades de los levitas: los hijos de Aarón", "Los levitas piden sus ciudades; los sacerdotes reciben trece ciudades de Judá, Simeón y Benjamín.", S4),
    ("21:20", "21:33", "Ciudades de coatitas y gersonitas", "Las ciudades de los demás coatitas y de los gersonitas, con sus ejidos.", S4),
    ("21:34", "21:45", "Ciudades de los meraritas; todo se cumplió", "Las ciudades de los meraritas; cuarenta y ocho en total. «No faltó palabra» de lo que Dios prometió.", S4),
    ("22:1", "22:9", "Las tribus del oriente vuelven a casa", "Josué despide con bendición a Rubén, Gad y la media tribu de Manasés.", S5),
    ("22:10", "22:20", "El altar junto al Jordán", "Edifican un gran altar junto al Jordán; Israel se junta en Siloh y envía a Finees a pedir cuentas.", S5),
    ("22:21", "22:34", "Un testimonio entre nosotros", "Las tribus explican que el altar es testimonio, no para sacrificios; lo llaman «Ed».", S5),
    ("23:1", "23:16", "Despedida de Josué", "Josué, viejo, reúne a Israel: guarden la ley y no se mezclen con las naciones que quedan.", S6),
    ("24:1", "24:13", "Josué recuerda la historia en Siquem", "En Siquem Josué repasa la historia desde Taré y Abraham hasta la entrada en la tierra.", S6),
    ("24:14", "24:28", "El pacto en Siquem", "«Yo y mi casa serviremos á Jehová»: el pueblo elige servir a Dios; Josué escribe el pacto y pone una piedra.", S6),
    ("24:29", "24:33", "Muerte de Josué y de Eleazar", "Josué muere a los ciento diez años; los huesos de José se entierran en Siquem; muere Eleazar.", S6),
]
# Citas de los resúmenes que van entre comillas (se comprueban).
CITAS_RESUMEN = [((1, 6), "Esfuérzate y sé valiente"), ((10, 12), "Sol, detente en Gabaón"), ((21, 45), "No faltó palabra"),
                 ((22, 34), "Ed"), ((24, 15), "yo y mi casa serviremos á Jehová")]

# ---------------------------------------------------------------- lugares
# Lugares configurados a mano: obid -> (id, nombre, formas RV1909 o None = detectar, tipo, nota, forzar baja).
# Van primero (el orden importa: «Beth-oron la de abajo» antes que «Beth-oron»). Para lugares ya registrados solo
# aportan formas.
LUGARES_MANUAL = {
    "a094036": ("bet-horon-de-abajo", "Bet-horón de abajo", ["Beth-oron la de abajo"], "ciudad", "", False),
    "ab682e6": ("bet-horon-de-arriba", "Bet-horón de arriba", ["Beth-oron la de arriba"], "ciudad", "", False),
    "a6ee047": ("aguas-de-merom", "Aguas de Merom", ["Merom"], "fuente",
                "Junto a ellas Josué vence a los reyes del norte (Jos 11:5-7).", False),
    "a37c8e6": ("valle-de-hinom", "Valle de Hinom", ["Hinnom"], "otro",
                "Límite entre Judá y Benjamín, al sur de Jerusalén (Jos 15:8; 18:16).", False),
    "a2e6de9": ("valle-de-ajalon", "Valle de Ajalón", ["Ajalón"], "otro", "«Y tú, Luna, en el valle de Ajalón» (Jos 10:12).", False),
    "a3e0180": ("valle-de-jefte-el", "Valle de Jefte-el", ["Iphtael"], "otro", "", False),
    "aa516c2": ("valle-de-jezreel", "Valle de Jezreel", ["Jezreel"], "otro", "", False),
    "ad94cc9": ("jezreel-juda", "Jezreel (de Judá)", ["Izreel"], "ciudad",
                "Ciudad de las montañas de Judá (Jos 15:56); distinta de Jezreel de Isacar (Jos 19:18).", False),
    "ae0bf4a": ("jezreel", "Jezreel (de Isacar)", ["Izreel"], "ciudad", "Jos 19:18; distinta de Jezreel de Judá (Jos 15:56).", False),
    "ac86af5": ("sunem", "Sunem", ["Sunem"], "ciudad", "", False),
    "ac2b4ef": ("monte-baala", "Monte Baala", ["Baala"], "monte", "", False),
    "a75aff4": ("monte-efron", "Monte Efrón", ["Ephrón"], "monte", "", False),
    "a11fadd": ("monte-halac", "Monte Halac", ["Halac"], "monte", "Límite sur de las conquistas de Josué, «que sube hasta Seir» (Jos 11:17).", False),
    "a3587ba": ("monte-jearim", "Monte Jearim", ["Jearim"], "monte", "Jos 15:10: «el monte de Jearim hacia el norte, esta es Chesalón».", False),
    "a36c283": ("monte-seir-juda", "Monte Seir (de Judá)", ["Seir"], "monte",
                "Hito del límite de Judá junto a Quiriat-jearim (Jos 15:10); distinto de Seir, la tierra de Edom.", False),
    "abf8060": ("jetla", "Jetla", ["Jeth-la"], "ciudad", "", False),
    "a774e50": ("emec-casis", "Emec-casis", ["Casis"], "ciudad", "La RV1909 dice «el valle de Casis» (Jos 18:21).", False),
    "ae32196": ("llano-de-mizpa", "Llano de Mizpa", ["Mizpa"], "region", "Hasta allí persigue Josué a los reyes del norte (Jos 11:8).", False),
    "a03cc2d": ("baalat-beer", "Baalat-beer", ["Baalath-beer"], "ciudad", "Jos 19:8: «Baalath-beer, [que es] Ramat del mediodía».", False),
    "a31492f": ("valle-de-acor", "Valle de Acor", ["Achôr"], "otro", "Allí apedrean a Acán (Jos 7:24-26); límite de Judá (Jos 15:7).", False),
    "ad5c4a1": ("hesron", "Hesrón", ["Hebrón"], "ciudad",
                "Límite sur de Judá (Jos 15:3). La RV1909 escribe «Hebrón»; es Hesrón (hebreo Ḥeṣrón), no la Hebrón de Caleb.", False),
    "a728e07": ("ebron", "Ebrón", ["Hebrón"], "ciudad",
                "Ciudad de Aser (Jos 19:28). La RV1909 escribe «Hebrón»; es Ebrón, no la Hebrón de Judá.", False),
    "a539e01": ("jarmut", "Jarmut", ["Jerimoth", "Jarmuth"], "ciudad",
                "La RV1909 escribe «Jerimoth» (Jos 10:3-23; 15:35) y «Jarmuth» (Jos 12:11).", False),
    "a85151a": ("hebron", "Hebrón", ["Hebrón", "Chîriath-arba"], "ciudad", "", False),
    "a26c8f2": ("havot-jair", "Havot-jair", ["aldeas de Jair"], "region", "", False),
    "a293fbf": ("beestera", "Beestera", ["Bosra"], "ciudad",
                "Ciudad levítica de Manasés en Basán (Jos 21:27). La RV1909 escribe «Bosra» (hebreo Beesterá); no es Bosra de Edom.", False),
    # Ya registrados: solo formas que la detección no halla.
    "abb5c1e": ("golan", "Golán", ["Gaulón"], "ciudad", "", False),
    "aa805fb": ("mar-grande", "Mar Grande", ["gran mar", "mar grande"], "mar", "", False),
    "abed304": ("mar-salado", "Mar Salado", ["mar Salado", "mar de los llanos"], "mar", "", False),
    "a562fcc": ("mar-de-cineret", "Mar de Cineret", ["mar de Cinneroth", "mar de Cinnereth"], "mar", "", False),
    "aca767b": ("campos-de-moab", "Campos de Moab", ["llanos de Moab"], "region", "", False),
    "a5eb047": ("lebo-hamat", "Lebo-hamat", ["entrar en Hamath"], "otro", "", False),
    "a7a59b4": ("torrente-de-egipto", "Torrente de Egipto", ["arroyo de Egipto", "río de Egipto"], "rio", "", False),
}
PRECEDIDO = {"ac2b4ef": "monte de ", "a36c283": "monte de ", "a3587ba": "monte de "}
EXCLUIR_LUGAR = {
    "a2bb5ef": "Arabá: la RV1909 traduce «la llanura» / «la campiña»; no es nombre propio en este texto.",
    "a1cb244": "Néguev: la RV1909 traduce «el mediodía»; no es nombre propio.",
    "af084cf": "Sefela: la RV1909 traduce «los valles» / «los llanos»; no es nombre propio.",
    "a3bba31": "Gabaa de Finees (Jos 24:33): la RV1909 traduce «el collado de Phinees».",
    "a97126d": "Gabaat-haaralot (Jos 5:3): la RV1909 traduce «el collado de los prepucios».",
    "a3cefc6": "Goyim (Jos 12:23): la RV1909 traduce «Gentes en Gilgal».",
    "aaa3eca": "Gulot-maim (Jos 15:19): la RV1909 traduce «fuentes de aguas».",
    "aacc081": "Gulot de abajo (Jos 15:19): la RV1909 traduce «las de abajo».",
    "a380434": "Gulot de arriba (Jos 15:19): la RV1909 traduce «las fuentes de arriba».",
    "acc1702": "Ciudad de la Sal (Jos 15:62): la RV1909 traduce «la ciudad de la sal».",
    "a9a2541": "Gebal (Jos 13:5): la RV1909 dice «la tierra de los Gibleos» (gentilicio).",
    "a9a6f72": "Efrón (Jos 18:15): la RV1909 no lo nombra en ese versículo.",
    "a159fa4": "Siria (Jos 1:4): la RV1909 no la nombra en ese versículo.",
    "a7559e6": "Valle de Refaim (Jos 15:8; 18:16): la RV1909 traduce «la campiña de los gigantes».",
    "a5bf0bd": "Misrefot-maim (Jos 11:8; 13:6): la RV1909 traduce «las aguas calientes».",
    "a70e38b": "Aguas de Jericó (Jos 16:1): se marca Jericó.",
    "ad05040": "Nafot-dor (Jos 11:2; 12:23): la RV1909 traduce «las regiones / la provincia de Dor»; se marca Dor.",
    "ac2192b": "Valle del Líbano (Jos 11:17; 12:7): la RV1909 dice «la llanura / el llano del Líbano»; se marca Líbano.",
    "ac6f1a8": "Mahaleb (Jos 19:29): la RV1909 no lo nombra.",
    "a664d03": "Ramá de Aser (Jos 19:29): la RV1909 escribe «Horma» en ese lugar; no se identifica sin más.",
    "a4e39f6": ("Galilea 2 (Jos 12:23): la RV1909 dice «el rey de Gentes en Gilgal»; OpenBible sigue la lectura «Galilea» "
                "(LXX); no se incluye."),
    "a00de1e": "Alón (Jos 19:33): la RV1909 lo une en «Allón-saananim» (se marca como Zaananim).",
}
UNIR_LUGAR = {}
# Grafía actual fijada a mano por forma RV1909 (el resto se adapta por regla, ver `moderno`).
NOMBRE_LUGAR = {
    "Jerusalem": "Jerusalén", "Hasor": "Hazor", "Asor": "Hazor", "Jerimoth": "Jarmut", "Gabaón": "Gabaón",
    "Timnath-sera": "Timnat-sera", "Beer-seba": "Beerseba", "Beersebah": "Beerseba", "Ayalón": "Ajalón",
    "Lachîs": "Laquis", "Maceda": "Maceda", "Chîriath-jearim": "Quiriat-jearim", "Beth-semes": "Bet-semes",
    "Achôr": "Acor", "Sittim": "Sitim", "Madón": "Madón", "Simrom": "Simrón", "Achsaph": "Acsaf",
    "Chîriath-sepher": "Quiriat-sefer", "Gessuri": "Gesur", "Maachâti": "Maaca", "Rogel": "En-rogel",
    "Beth-oron": "Bet-horón", "Megiddo": "Meguido", "Engannim": "En-ganim", "Ailón": "Ajalón", "Joppa": "Jope",
    "Adullam": "Adulam", "Chîriath-arba": "Quiriat-arba", "Chêdes": "Cedes", "Hebrón": "Hebrón",
}
# Nombre fijado por id de OpenBible (homónimos que conviene distinguir por algo más que la referencia).
NOMBRE_OB = {"a662eed": ("Cedes de Neftalí", "Ciudad de refugio en Galilea, en el monte de Neftalí (Jos 20:7; 19:37)."),
             "a03f6cf": ("Sión (de Isacar)", "Ciudad de Isacar (Jos 19:19); no es Sión de Jerusalén ni el «monte de Sión» de Dt 4:48."),
             "ad6b2b7": ("En-tapúa", "Jos 17:7: «la fuente de Tappua»; distinta de la ciudad de Tapúa.")}
# Gentilicios y nombres de pueblo que la detección puede tomar por lugar.
_GENTILICIO = re.compile(r"(?:itas?|eos?|ios)$")
TIPOS_OB = [("mountain", "monte"), ("hill", "monte"), ("river", "rio"), ("stream", "rio"), ("wadi", "rio"),
            ("spring", "fuente"), ("well", "fuente"), ("pool", "fuente"), ("water", "fuente"), ("sea", "mar"),
            ("lake", "mar"), ("region", "region"), ("territory", "region"), ("land", "region"), ("people", "region"),
            ("valley", "otro"), ("plain", "region"), ("wilderness", "region"), ("settlement", "ciudad"),
            ("city", "ciudad"), ("town", "ciudad"), ("village", "ciudad"), ("fortress", "ciudad")]
OBLIGATORIOS_LUGAR = ["jerico", "hai", "gabaon", "gilgal", "siquem", "hebron", "timnat-sera", "beser", "ramot-galaad",
                      "golan", "jordan", "siloh", "monte-ebal", "monte-gerizim", "aguas-de-merom", "hazor", "laquis", "maceda"]
LUGARES = {}  # se rellena en construir_lugares (manuales + automáticos)
LUGAR_OPCIONAL = set()  # configurados automáticamente: si no aparecen en el texto, van a «sin forma» (no es error)
OPC = LUGAR_OPCIONAL
EXCL_AUTO = {}
INFO_AUTO = {}
# Versículos donde BibleData sitúa a una persona y el mismo nombre aparece además como lugar: la aparición precedida
# de este texto es el lugar, no la persona (se quita la mención de persona para que se marque el lugar).
LUGAR_NO_PERSONA = [((24, 32), "Shechem_1", "enterraron en "), ((19, 47), "Dan_1", "Lesem, "), ((17, 1), "Gilead_1", "tuvo á ")]


def moderno(f):
    """Grafía actual por regla a partir de la forma RV1909 (editorial, se dice en la nota)."""
    s = f.translate(str.maketrans("âêîôûÂÊÎÔÛ", "aeiouAEIOU"))
    s = re.sub(r"Ch(?=[eiéí])", "Qu", s)
    s = re.sub(r"ch(?=[eiéí])", "qu", s)
    s = s.replace("Ch", "C").replace("ch", "c")
    s = re.sub(r"K(?=[eiéí])", "Qu", s)
    s = re.sub(r"k(?=[eiéí])", "qu", s)
    s = s.replace("K", "C").replace("k", "c")
    for a, b in (("Th", "T"), ("th", "t"), ("Ph", "F"), ("ph", "f"), ("Sh", "S"), ("sh", "s")):
        s = s.replace(a, b)
    s = re.sub(r"([bcdfgjmnpstvz])\1", r"\1", s)
    s = re.sub(r"(?<=[aeiouáéíóú])h\b", "", s)
    return s[0].upper() + s[1:]


def _tipo(d):
    ts = " ".join(str(t) for t in (d.get("types") or [])).lower()
    for clave, tipo in TIPOS_OB:
        if clave in ts:
            return tipo
    return "otro"


def lugares_auto(rv, rutas, lugares_previos, avisos, cfg=None):
    """Configura los lugares de OpenBible en Josué que no están a mano: formas RV1909 detectadas (sin gentilicios),
    nombre actual (NOMBRE_LUGAR o regla), tipo de OpenBible, homónimos con la primera ref y unión con un lugar ya
    registrado del mismo nombre e idéntica identificación moderna. cfg: módulo del libro (por defecto Josué;
    Jueces usa herramientas/jueces.py)."""
    cfg = cfg or sys.modules[__name__]
    USX, LIB = cfg.USX, cfg.LIBRO
    LUGARES_MANUAL, EXCLUIR_LUGAR, NOMBRE_OB, NOMBRE_LUGAR = cfg.LUGARES_MANUAL, cfg.EXCLUIR_LUGAR, cfg.NOMBRE_OB, cfg.NOMBRE_LUGAR
    OPC, EXCL_AUTO, INFO_AUTO, moderno_ = cfg.LUGAR_OPCIONAL, cfg.EXCL_AUTO, cfg.INFO_AUTO, getattr(cfg, "moderno", moderno)
    remap = getattr(cfg, "REMAP_REF", lambda r: r)  # versificación de OpenBible (inglesa) -> RV1909
    anc = {}
    with open(rutas["ob_ancient"], encoding="utf-8") as f:
        for n, linea in enumerate(f, 1):
            d = json.loads(linea)
            if any(v["usx"].startswith(USX + " ") for v in d.get("verses", [])):
                anc[d["id"]] = (n, d)
    mod_ids = set()
    for _, d in anc.values():
        mod_ids |= set(d.get("modern_associations", {}))
    mod = lm._leer_jsonl(rutas["ob_modern"], mod_ids)
    prev_ob = {l["url_fuente"].split("/ancient/")[1].split("/")[0]: l for l in lugares_previos}
    prev_id = {l["id"]: l for l in lugares_previos}
    conf, unir, cand, sin_forma = {}, {}, [], []
    for obid, (_, d) in sorted(anc.items(), key=lambda x: x[1][0]):
        if obid in LUGARES_MANUAL or obid in EXCLUIR_LUGAR:
            continue
        vs = sorted({remap(tuple(map(int, v["usx"][4:].split(":")))) for v in d["verses"] if v["usx"].startswith(USX + " ")})
        nombres_en = d.get("translation_name_counts") or {d["friendly_id"]: 1}
        ingles = max(nombres_en.items(), key=lambda x: x[1])[0]
        cuenta = Counter()
        for r in vs:
            fm, _ = na.mejor_forma(ingles, rv.get(r, ""))
            if fm and not _GENTILICIO.search(fm):
                cuenta[fm] += 1
        formas = [fm for fm, _ in cuenta.most_common()]
        if obid in prev_ob:  # ya registrado: formas explícitas (evita que la detección meta gentilicios)
            l = prev_ob[obid]
            conf[obid] = (l["id"], l["nombre"], formas or list(l["formas_rv1909"]), l["tipo"], "", False)
            OPC.add(obid)
            continue
        if not formas:
            sin_forma.append(d["friendly_id"])
            if any(na.mejor_forma(ingles, rv.get(r, ""))[0] for r in vs):  # solo gentilicios («Ascalonitas»)
                EXCL_AUTO[obid] = (f"{d['friendly_id']}: en {cfg.NOMBRE} la RV1909 solo trae el gentilicio, no el nombre del "
                                   "lugar.")
            continue
        coord = None
        for mid, ma in sorted(d.get("modern_associations", {}).items(), key=lambda x: -x[1]["score"]):
            if mid in mod and mod[mid][1].get("lonlat"):
                coord = tuple(round(float(x), 2) for x in mod[mid][1]["lonlat"].split(","))
                break
        nombre = NOMBRE_OB.get(obid, (None,))[0] or NOMBRE_LUGAR.get(formas[0]) or moderno_(formas[0])
        cand.append({"obid": obid, "formas": formas, "nombre": nombre, "slug": lm._slug(nombre), "coord": coord,
                     "ref": vs[0], "tipo": _tipo(d), "nota": NOMBRE_OB.get(obid, (None, ""))[1]})
    # mismo nombre que un lugar ya registrado: si la identificación moderna coincide, es el mismo lugar
    previos_slug = {}
    for l in lugares_previos:
        previos_slug.setdefault(lm._slug(l["nombre"]), []).append(l)
    restantes = []
    for c in cand:
        igual = [l for l in previos_slug.get(c["slug"], []) + ([prev_id[c["slug"]]] if c["slug"] in prev_id else [])
                 if l["ubicacion"] and c["coord"] and (round(l["ubicacion"]["lon"], 2), round(l["ubicacion"]["lat"], 2)) == c["coord"]]
        if igual:
            unir[c["obid"]] = igual[0]["id"]
            conf[c["obid"]] = (igual[0]["id"], igual[0]["nombre"], list(dict.fromkeys(igual[0]["formas_rv1909"] + c["formas"])),
                               igual[0]["tipo"], "", False)
            OPC.add(c["obid"])
        else:
            restantes.append(c)
    # homónimos: el primero (por ref) conserva el id simple si está libre; todos llevan la ref en el nombre
    ids = set(prev_id) | {v[0] for v in LUGARES_MANUAL.values()}
    grupos = {}
    for c in restantes:
        grupos.setdefault(c["slug"], []).append(c)
    n_homon = 0
    for slug, gs in grupos.items():
        gs.sort(key=lambda c: c["ref"])
        homon = len(gs) > 1 or slug in ids
        for i, c in enumerate(gs):
            lid = slug if (i == 0 and slug not in ids) else f"{slug}-{c['ref'][0]}-{c['ref'][1]}"
            while lid in ids:
                lid += "-b"
            ids.add(lid)
            nombre = c["nombre"] + (f" ({LIB} {c['ref'][0]}:{c['ref'][1]})" if homon else "")
            nota = [c["nota"]] if c["nota"] else []
            if c["nombre"] != c["formas"][0] and c["formas"][0] not in NOMBRE_LUGAR and not c["nota"]:
                nota.append(f"Grafía actual adaptada por regla de la RV1909 «{c['formas'][0]}».")
            if homon:
                n_homon += 1
                nota.append(f"Hay otros lugares llamados {c['nombre']}: este es el de {LIB} {c['ref'][0]}:{c['ref'][1]} "
                            "según OpenBible.")
            conf[c["obid"]] = (lid, nombre, c["formas"], c["tipo"], " ".join(nota), False)
            OPC.add(c["obid"])
    INFO_AUTO.update(auto=len(restantes), unidos=dict(unir), homonimos=n_homon, sin_forma_auto=sin_forma)
    # Primero las formas más largas: «Asor-hadatta» antes que «Asor» (el nombre corto casaría dentro del compuesto).
    conf = dict(sorted(conf.items(), key=lambda kv: -max(len(f) for f in kv[1][2])))
    return conf, unir


def construir(cx):
    rv, br, errores = cx["rv"], cx["br"], cx["errores"]
    for c, n in enumerate(POR_CAPITULO, 1):
        hay = sum(1 for (cc, _) in rv if cc == c)
        if hay != n:
            errores.append(f"Josué {c}: la RV1909 tiene {hay} versículos (numeración inglesa: {n})")
    for ref, ini in VERSIFICACION:
        if not rv.get(ref, "").startswith(ini):
            errores.append(f"Versificación de Jos {ref[0]}:{ref[1]}: la RV1909 no empieza «{ini}»")
    for ref, frag in VERSIFICACION_LXX:
        if frag not in br.get(ref, ""):
            errores.append(f"Brenton Jos {ref[0]}:{ref[1]} (numeración RV) no dice «{frag}»")
    for ref, frag in CITAS_RESUMEN:
        if frag not in rv.get(ref, ""):
            errores.append(f"Resumen de pasaje: «{frag}» no está en Jos {ref[0]}:{ref[1]}")
    res = exodo.construir(cx, sys.modules[__name__])
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
    auto, unir = lugares_auto(rv, rutas, lugares_previos, avisos)
    LUGARES = dict(LUGARES_MANUAL)
    for k, v in auto.items():
        LUGARES.setdefault(k, v)
    UNIR_LUGAR = unir
    EXCLUIR_LUGAR = {**EXCLUIR_LUGAR, **EXCL_AUTO}
    return exodo.construir_lugares(rv, menciones_personas, rutas, lugares_previos, errores, avisos, sa,
                                   sys.modules[__name__])


# ---------------------------------------------------------------- hechos obligatorios (sobre los datos finales)
def comprobar(datos, errores, numeral=None):
    """Comprueba los hechos pedidos para Josué (falla si falta alguno). Devuelve líneas de informe."""
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
            errores.append(f"Hecho obligatorio (Josué): {desc}")

    def tiene(pid, ref, mencion=True):
        return ref in P.get(pid, {}).get("refs", []) and (not mencion or (ref, pid) in M)

    def nota_rel(de, a, tipo, frag):
        x = R.get((de, a, tipo))
        ok_(bool(x) and frag in x["nota"], f"{de}→{a} {tipo} con la cita de {frag}" + (f" [{x['ref']}]" if x else " [falta]"))

    def lugar_en(lid, ref):
        return ref in L.get(lid, {}).get("refs", []) and (ref, lid) in ML

    # Versificación
    ok_(len(caps) == CAPITULOS and len(texto) == VERSICULOS and [len(c["versiculos"]) for c in caps] == POR_CAPITULO,
        f"{CAPITULOS} capítulos y {VERSICULOS} versículos con los recuentos de la numeración inglesa (hay {len(caps)} y {len(texto)})")
    ok_(not [r for r, t in texto.items() if not t], "ningún versículo vacío (Jos 21:36-37 presentes)")
    # Josué hijo de Nun, el de Ex–Dt; muere a los 110 (TM y LXX) y lo entierran en Timnat-sera
    ok_(tiene("Joshua_1", "Jos 1:1") and {"Ex 17:9", "Nm 13:17", "Dt 34:9"} <= set(P["Joshua_1"]["refs"]),
        "Josué hijo de Nun (Jos 1:1) = Josué de Ex 17:9, Nm 13:17 y Dt 34:9")
    nota_rel("Nun_1", "Joshua_1", "padre", "Jos 1:1")
    ed = {e["tradicion"]: e for e in datos["edades"] if e["persona"] == "Joshua_1" and e["ref"] == "Jos 24:29"}
    ok_(set(ed) == {"TM", "LXX"} and all(e["valor"] == 110 and e["tipo"] == "total" for e in ed.values())
        and ed["TM"]["cita"] in texto["Jos 24:29"], "Josué muere a los 110 años (Jos 24:29, TM y LXX con cita)")
    ok_(lugar_en("timnat-sera", "Jos 24:30") and lugar_en("timnat-sera", "Jos 19:50"),
        "Josué sepultado en Timnat-sera (Jos 24:30; también 19:50)")
    # Caleb: 40 (14:7) + 45 (14:10) = 85 (14:10)
    ce = {(e["ref"], e["tradicion"]): e["valor"] for e in datos["edades"] if e["persona"] == "Caleb_1"}
    t1410 = {"TM": ("cuarenta y cinco años", "es"), "LXX": ("forty-fifth year", "en")}
    for trad in ("TM", "LXX"):
        frase, idioma = t1410[trad]
        n45 = numeral(frase.replace("-fifth", "-five").replace(" year", "").replace(" años", ""), idioma) if numeral else 45
        a, b = ce.get(("Jos 14:7", trad)), ce.get(("Jos 14:10", trad))
        ok_(a == 40 and b == 85 and n45 == 45 and a + n45 == b,
            f"Caleb ({trad}): {a} años al ser enviado (Jos 14:7) + {n45} años (Jos 14:10) = {None if a is None else a + n45} = {b} (Jos 14:10)")
    ok_("cuarenta y cinco años" in texto["Jos 14:10"], "Jos 14:10 escribe «cuarenta y cinco años»")
    EV = {e["id"]: e for e in datos["cronologia"]["eventos"]}
    c = "TM|tare70|sem2|egipto"
    if all(k in EV for k in ("ev-nac-caleb", "ev-caleb-hebron", "ev-salida-sinai", "ev-paso-jordan", "ev-discursos-moab", "ev-salida-egipto")):
        for cc in (c, "LXX|tare70|sem2|egipto"):
            ok_(EV["ev-caleb-hebron"]["anios"][cc] - EV["ev-nac-caleb"]["anios"][cc] == 85
                and EV["ev-caleb-hebron"]["anios"][cc] - EV["ev-salida-sinai"]["anios"][cc] == 45,
                f"cronología {cc.split('|')[0]}: Caleb pide Hebrón 85 años después de nacer y 45 después de la salida del Sinaí")
        ok_(EV["ev-paso-jordan"]["anios"][c] - EV["ev-salida-egipto"]["anios"][c] == 41 and EV["ev-paso-jordan"]["ref"] == "Jos 4:19"
            and EV["ev-paso-jordan"]["certeza"] == "calculo" and EV["ev-paso-jordan"]["depende_de"] == "ev-discursos-moab",
            "paso del Jordán (Jos 4:19): año 41 desde la salida en el TM (Dt 1:3 + 1), cálculo con pasos")
    else:
        ok_(False, "cronología de Josué: faltan eventos (ev-paso-jordan, ev-nac-caleb, ev-caleb-hebron)")
    ok_(any(h["ref"] == "Jos 24:29" for h in datos["cronologia"]["hitos_sin_fecha"]),
        "muerte de Josué en hitos sin fecha (sin base para su año)")
    # Personas nuevas e identidades
    ok_(tiene("Rahab_1", "Jos 2:1") and all(r.startswith("Jos ") for r in P["Rahab_1"]["refs"]), "Rahab (Jos 2:1), persona nueva")
    ok_(tiene("Achan_1", "Jos 7:1") and tiene("Carmi_2", "Jos 7:1"), "Acán hijo de Carmi en Jos 7:1")
    x = R.get(("Carmi_2", "Achan_1", "padre"))
    ok_(bool(x) and x.get("cita") and x["cita"] in texto["Jos 7:1"], "Carmi padre de Acán con cita (Jos 7:1)")
    ok_("Gn 46:9" not in P.get("Carmi_2", {}).get("refs", []), "Carmi de Jos 7:1 ≠ Carmi hijo de Rubén")
    ok_(tiene("Eleazar_1", "Jos 24:33") and "Ex 6:23" in P["Eleazar_1"]["refs"] and "Jos 24:33" in P["Eleazar_1"]["nota"],
        "Eleazar muere (Jos 24:33) = Eleazar de Ex 6:23")
    for h in ("Mahlah_1", "Noah_2", "Hoglah_1", "Milcah_2", "Tirzah_1"):
        ok_(tiene(h, "Jos 17:3") and "Nm 27:1" in P.get(h, {}).get("refs", []), f"hija de Zelofehad {h} en Jos 17:3 = la de Nm 27:1")
    ok_(tiene("Joseph_1", "Jos 24:32") and "Gn 30:24" in P["Joseph_1"]["refs"], "huesos de José en Siquem (Jos 24:32) = José de Gn 30:24")
    for h in ("Sheshai_1", "Ahiman_1", "Talmai_1"):
        ok_(tiene(h, "Jos 15:14") and any(r.startswith("Nm 13:") for r in P.get(h, {}).get("refs", [])),
            f"{h}, hijo de Anac en Jos 15:14 = el de Nm 13:22")
    ok_(tiene("Caleb_1", "Jos 14:6") and "Nm 13:7" in P["Caleb_1"]["refs"], "Caleb (Jos 14:6) = Caleb de Nm 13")
    ok_(not [p for p in EXCLUIR if any(r.startswith("Jos ") for r in P.get(p, {}).get("refs", []))], "sin personas para Dios, reyes sin nombre, el príncipe del ejército ni el libro de Jaser")
    for pid in ("Adoni-zedek_1", "Othniel_1", "Achsah_1", "Jobab_3"):
        ok_(any(r.startswith("Jos ") for r in P.get(pid, {}).get("refs", [])) and (P[pid]["primera_ref"], pid) in M,
            f"persona nueva {pid} con mención en el texto")
    # Lugares
    for lid in OBLIGATORIOS_LUGAR:
        l = L.get(lid)
        ok_(bool(l) and any(r.startswith("Jos ") for r in l["refs"]),
            f"lugar {lid} con refs de Josué ({sum(1 for r in l['refs'] if r.startswith('Jos ')) if l else 0})")
    ok_(lugar_en("siquem", "Jos 24:32") and lugar_en("siquem", "Jos 20:7") and lugar_en("siquem", "Jos 24:1"),
        "Siquem: pacto (24:1), huesos de José (24:32) y refugio (20:7)")
    cedes = [l for l in datos["lugares"] if lm._slug(l["nombre"]).startswith("cedes") and lugar_en(l["id"], "Jos 20:7")]
    ok_(bool(cedes), f"Cedes, ciudad de refugio (Jos 20:7) [{cedes[0]['id'] if cedes else 'falta'}]")
    heb = [lid for lid in L if lugar_en(lid, "Jos 20:7") and lid in ("hebron", "quiriat-arba")]
    ok_(bool(heb), f"Quiriat-arba / Hebrón, ciudad de refugio (Jos 20:7) {heb}")
    ok_(all({"Dt 4:43", "Jos 20:8"} <= set(L.get(x, {}).get("refs", [])) for x in ("beser", "ramot-galaad", "golan")),
        "ciudades de refugio de Jos 20:8 = las de Dt 4:43 (Beser, Ramot, Golán)")
    sin = [l for l in datos["lugares"] if any(r.startswith("Jos ") for r in l["refs"]) and not l["ubicacion"]]
    ok_(all("OpenBible no da identificación" in l["nota"] for l in sin), f"lugares de Josué sin coordenadas con nota ({len(sin)})")
    # Pasajes y secciones
    pas = [p for p in datos["pasajes"] if p["libro"] == LIBRO]
    ok_(len(pas) == len(PASAJES) and pas[0]["inicio"] == "Jos 1:1" and pas[-1]["fin"] == "Jos 24:33",
        f"{len(pas)} pasajes jos-NN de Jos 1:1 a Jos 24:33")
    ok_(len({p["seccion"] for p in pas}) == 6, "6 secciones")
    return lineas
