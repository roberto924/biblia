"""1 Samuel 1–31: personas, relaciones, edades, pasajes, menciones y lugares (lo usa construir_datos.py).

Id del libro: «1S» (el código canónico de CANON en app.js; Rut quedó como «Rut» con alias). Reutiliza la lógica de
exodo.py (exodo.construir / exodo.construir_lugares con este módulo como configuración) y la detección automática de
lugares de josue.py (josue.lugares_auto), como Jueces. Cada dato lleva versículo, fuente y certeza; las citas se
comprueban literalmente contra la RV1909 (TM) o Brenton (LXX). Las personas de Génesis–Rut (David e Isaí de Rut 4,
Moisés, Aarón, Jacob, Benjamín, Judá, Raquel, Sísara, Barac, Gedeón/Jerobaal, Jefté, el faraón del éxodo) son la misma
persona (mismo id de BibleData): se amplían sus `refs`.

Versificación (comprobada al generar, versículo a versículo):
- La RV1909 de eBible tiene 810 versículos con los recuentos de la numeración inglesa (BibleData y OpenBible), pero
  en 1 S 23–24 sigue la hebrea: deja 23:29 vacío, pone en 24:1 «ENTONCES David subió de allí… Engaddi» (23:29
  inglés = 24:1 hebreo) y funde en 24:22 los dos últimos versículos (24:21-22 inglés = 24:22-23 hebreo). En 20:42 /
  21:1 sigue la inglesa: «Y él se levantó y fuése…» va al final de 20:42 (hebreo 21:1) y el capítulo 21 tiene 15.
  `REMAP_REF` (único punto) lleva la numeración inglesa de BibleData y OpenBible a la de la RV1909.
- Brenton (LXX) numera 21 y 24 como el hebreo y le faltan versículos que la LXX no tiene (13:1; 17:41, 17:50,
  17:55-58; 18:1-5, 18:9-11, 18:17-19, 18:30; 23:12). `br_a_rv` (único punto de versificación de Brenton) lo lleva a
  la numeración de la RV1909. Después se comprueba que en cada capítulo el emparejamiento sin desfase compara mejor
  (longitudes) que con desfase ±1, que nombres poco frecuentes caen en los mismos versículos y los extremos de 20–24.

Solo biblioteca estándar.
"""
import math
import re
import sys

import exodo
import josue

LIBRO = "1S"
NOMBRE = "1 Samuel"
USX = "1SA"
CAPITULOS = 31
VERSICULOS = 810
POR_CAPITULO = [28, 36, 21, 22, 12, 21, 17, 22, 27, 27, 15, 25, 23, 52, 35, 23, 58, 30, 24, 42, 15, 23, 29, 22, 44, 25,
                12, 25, 11, 31, 13]
# Versículo que la RV1909 de eBible deja vacío (su texto está en el siguiente).
VACIOS = {(23, 29): "1S 24:1"}
# Comienzo/fin de los versículos de las zonas donde el hebreo numera distinto (se comprueban).
VERSIFICACION = [((20, 42), "Y Jonathán dijo á David: Vete en paz"), ((21, 1), "Y VINO David á Nob"),
                 ((21, 15), "¿Fáltanme á mí locos"), ((23, 28), "Volvióse por tanto Saúl de perseguir á David"),
                 ((24, 1), "ENTONCES David subió de allí"), ((24, 2), "Y como Saúl volvió de los Filisteos"),
                 ((24, 21), "Y ahora, como yo entiendo que tú has de reinar"), ((24, 22), "Júrame pues ahora por Jehová"),
                 ((13, 1), "HABÍA ya Saúl reinado un año")]
FIN_VERSICULO = [((20, 42), "y Jonathán se entró en la ciudad."), ((24, 22), "se subieron al sitio fuerte.")]
# Brenton, ya en numeración RV1909 (tras br_a_rv).
VERSIFICACION_LXX = [((20, 42), "and Jonathan went into the city"), ((21, 1), "And David comes to Nomba"),
                     ((21, 15), "I in want of madmen"), ((24, 1), "dwelt in the narrow passes of Engaddi"),
                     ((24, 2), "when Saul returned from pursuing after the Philistines"),
                     ((24, 22), "So David swore to Saul")]
# Versículos que Brenton (LXX) no tiene (numeración RV1909).
SIN_LXX = {(13, 1), (17, 41), (17, 50), (17, 55), (17, 56), (17, 57), (17, 58), (18, 1), (18, 2), (18, 3), (18, 4),
           (18, 5), (18, 9), (18, 10), (18, 11), (18, 17), (18, 18), (18, 19), (18, 30), (23, 12), (23, 29)}
# Nombres que deben caer en los mismos versículos en la RV1909 y en Brenton (solo versículos que tienen ambos).
PARALELOS = [("Dagón", "Dagon"), ("Asdod", "Azotus"), ("Cis", "Kis"), ("Agag", "Agag"), ("Abner", "Abenner"),
             ("Merab", "Merob"), ("Abigail", "Abigaia"), ("Doeg", "Doec"), ("Abiathar", "Abiathar"),
             ("Siclag", "Sekelac"), ("Gilboa", "Gelbue"), ("Abisai", "Abessa"), ("Nob", "Nomba"), ("Mizpa", "Massepha")]
PROPORCION = (0.15, 3.2)  # longitud RV1909 / Brenton por versículo (observado 0,20–3,06: la LXX añade u omite frases)


def REMAP_REF(r):
    """Numeración inglesa (BibleData, OpenBible) -> RV1909. Único punto: 23:29 inglés = 24:1 RV; 24:1-21 inglés =
    24:2-22 RV (24:22 inglés va dentro de 24:22 RV)."""
    c, v = r
    if (c, v) == (23, 29):
        return (24, 1)
    if c == 24:
        return (24, min(v + 1, 22))
    return r


def br_a_rv(br):
    """Brenton (numeración hebrea/LXX en 21 y 24) -> numeración de la RV1909. Único punto de versificación de
    Brenton: 21:1 LXX va al final de 20:42; 21:n LXX = 21:n-1; 24:23 LXX va al final de 24:22."""
    out = {}
    for (c, v), t in sorted(br.items()):
        k = (20, 42) if (c, v) == (21, 1) else (21, v - 1) if c == 21 else (24, 22) if (c, v) == (24, 23) else (c, v)
        out[k] = f"{out[k]} {t}" if k in out else t
    return out


# Personas de BibleData que no se crean: Dios, «NA», Amalec y Ammón (son los pueblos: «hiere á Amalec» 15:3, «los
# hijos de Ammón»; van como lugares/pueblos de OpenBible, como en Jueces) y los reyes de Moab sin nombre (12:9; 22:3-4,
# como los reyes sin nombre de Josué y Jueces).
EXCLUIR = {"YHVH_1", "NA", "Amalek_1", "Ben-ammi_1", "King of Moab_1", "King of Moab_2"}
# «Israel» es el pueblo (como en Josué y Jueces): Jacob solo si el texto dice «Jacob» (12:8).
SOLO_ETIQUETA = {"Jacob_1": {"Jacob"}}
FORMA_NO_MENCION = {("Jacob_1", "israel")}
PV_DESCARTAR = {}
REL_DESCARTAR = {}
FORMAS_FORZADAS = {
    "Elkanah_2": ["Elcana"], "Jeroham_1": ["Jeroham"], "Elihu_1": ["Eliú"], "Tohu_1": ["Thohu"], "Zuph_1": ["Suph"],
    "Hannah_1": ["Anna"], "Peninnah_1": ["Peninna"], "Eli_1": ["Eli"], "Hophni_1": ["Ophni"], "Phinehas_2": ["Phinees"],
    "Samuel_2": ["Samuel"], "Ichabod_1": ["Ichâbod"], "Joshua_2": ["Josué"], "Abinadab_1": ["Abinadab"],
    "Eleazar_2": ["Eleazar"], "Joel_1": ["Joel"], "Abijah_1": ["Abia"], "Kish_1": ["Cis"], "Abiel_1": ["Abiel"],
    "Zeror_1": ["Seor"], "Becorath_1": ["Bechôra"], "Aphiah_1": ["Aphia"], "Saul_1": ["Saúl"], "Nahash_1": ["Naas"],
    "Jonathan_2": ["Jonathán"], "Ahijah_1": ["Achîas"], "Ahitub_1": ["Ahitob", "Achîtob"], "Ishvi_2": ["Isui", "Abinadab"],
    "Malchi-shua_1": ["Melchi-sua", "Melchîsua"], "Merab_1": ["Merab"], "Michal_1": ["Michâl"], "Ahinoam_1": ["Ahinoam"],
    "Ahimaaz_1": ["Aimaas"], "Abner_1": ["Abner"], "Ner_1": ["Ner"], "Agag_2": ["Agag"], "Eliab_3": ["Eliab"],
    "Abinadab_2": ["Abinadab"], "Shammah_2": ["Samma"], "Goliath_1": ["Goliath"], "Adriel_1": ["Adriel"],
    "Ahimelech_1": ["Ahimelech"], "Doeg_1": ["Doeg"], "Achish_1": ["Achîs"], "Gad_2": ["Gad"], "Abiathar_1": ["Abiathar"],
    "Nabal_1": ["Nabal"], "Abigail_1": ["Abigail"], "Ahinoam_2": ["Ahinoam"], "Palti_2": ["Palti"], "Laish_1": ["Lais"],
    "Ahimelech_2": ["Ahimelech"], "Abishai_1": ["Abisai"], "Zeruiah_1": ["Sarvia"], "Joab_1": ["Joab"], "Maoch_1": ["Maoch"],
    "Barak_1": ["Barac", "Bedán"],
}
MODERNO = {
    "Elkanah_2": "Elcana", "Jeroham_1": "Jeroham", "Elihu_1": "Eliú", "Tohu_1": "Tohu", "Zuph_1": "Zuf", "Hannah_1": "Ana",
    "Peninnah_1": "Penina", "Eli_1": "Elí", "Hophni_1": "Ofni", "Phinehas_2": "Finees", "Samuel_2": "Samuel",
    "Ichabod_1": "Icabod", "Joshua_2": "Josué", "Abinadab_1": "Abinadab", "Eleazar_2": "Eleazar", "Joel_1": "Joel",
    "Abijah_1": "Abías", "Kish_1": "Cis", "Abiel_1": "Abiel", "Zeror_1": "Zeror", "Becorath_1": "Becorat",
    "Aphiah_1": "Afía", "Saul_1": "Saúl", "Nahash_1": "Nahas", "Jonathan_2": "Jonatán", "Ahijah_1": "Ahías",
    "Ahitub_1": "Ahitob", "Ishvi_2": "Isúi", "Malchi-shua_1": "Malquisúa", "Merab_1": "Merab", "Michal_1": "Mical",
    "Ahinoam_1": "Ahinoam", "Ahimaaz_1": "Ahimaas", "Abner_1": "Abner", "Ner_1": "Ner", "Agag_2": "Agag",
    "Eliab_3": "Eliab", "Abinadab_2": "Abinadab", "Shammah_2": "Sama", "Goliath_1": "Goliat", "Adriel_1": "Adriel",
    "Ahimelech_1": "Ahimelec", "Doeg_1": "Doeg", "Achish_1": "Aquis", "Gad_2": "Gad", "Abiathar_1": "Abiatar",
    "Nabal_1": "Nabal", "Abigail_1": "Abigail", "Ahinoam_2": "Ahinoam", "Palti_2": "Palti", "Laish_1": "Lais",
    "Ahimelech_2": "Ahimelec", "Abishai_1": "Abisai", "Zeruiah_1": "Sarvia", "Joab_1": "Joab", "Maoch_1": "Maoc",
}
NOTAS = {
    "Elkanah_2": ("Efrateo de Ramataim de Sofim, del monte de Efraín (1 S 1:1). Distinto de Elcana hijo de Coré "
                  "(Ex 6:24)."),
    "Hannah_1": "1 S 1:11: promete a Jehová el hijo que le dé. 1 S 2:21: después «parió tres hijos, y dos hijas».",
    "Eli_1": ("Sacerdote en Silo (1 S 1:9). Muere a los 98 años al saber que el arca fue tomada (1 S 4:15-18); «había "
              "juzgado á Israel cuarenta años» (1 S 4:18)."),
    "Phinehas_2": ("Hijo de Elí, sacerdote en Silo (1 S 1:3); muere en la batalla en que se pierde el arca (1 S 4:11). "
                   "Distinto de Finees hijo de Eleazar (Nm 25:7)."),
    "Samuel_2": ("Hijo de Elcana y Ana (1 S 1:19-20); profeta (1 S 3:20) y juez de Israel «todo el tiempo que vivió» "
                 "(1 S 7:15). Muere en 1 S 25:1. Distinto de Samuel hijo de Amiud (Nm 34:20)."),
    "Ichabod_1": "1 S 4:21: el nombre recuerda que «Traspasada es la gloria de Israel».",
    "Joshua_2": "Bet-semita: en su campo se para el carro que trae el arca (1 S 6:14). Distinto de Josué hijo de Nun.",
    "Eleazar_2": ("Hijo de Abinadab; lo santifican para guardar el arca en Quiriat-jearim (1 S 7:1). Distinto de Eleazar "
                  "hijo de Aarón."),
    "Abinadab_1": "En su casa del collado de Quiriat-jearim está el arca (1 S 7:1).",
    "Saul_1": ("Hijo de Cis, benjaminita (1 S 9:1-2, 9:21). Muere en el monte Gilboa (1 S 31:4-6). 1 S 13:1 no permite "
               "sacar la duración de su reinado: ver la cronología."),
    "Jonathan_2": "Hijo de Saúl (1 S 14:1). Distinto de Jonatán, sacerdote de los danitas (Jue 18:30).",
    "Ishvi_2": ("1 S 14:49 nombra a los hijos de Saúl «Jonathán, Isui, y Melchi-sua»; 1 S 31:2 nombra a los que mueren en "
                "Gilboa «Jonathán, y á Abinadab, y á Melchîsua». BibleData identifica a Isúi con este Abinadab (Fuente "
                "externa: no lo dice el texto); se deja así. Distinto de Isúi hijo de Aser (Gn 46:17) y de los otros "
                "Abinadab (1 S 7:1; 16:8)."),
    "Abinadab_2": "Segundo hijo de Isaí (1 S 17:13). Distinto de Abinadab de Quiriat-jearim (1 S 7:1).",
    "Eliab_3": "Primogénito de Isaí (1 S 17:13). Distinto de los Eliab de Números.",
    "Shammah_2": "Tercer hijo de Isaí (1 S 17:13). Distinto de Sama, jefe edomita (Gn 36:13).",
    "Agag_2": ("Rey de Amalec que Saúl toma vivo (1 S 15:8) y Samuel mata en Gilgal (1 S 15:33). Distinto del Agag del "
               "oráculo de Balaam (Nm 24:7), según BibleData."),
    "Goliath_1": "1 S 17:4: «tenía de altura seis codos y un palmo».",
    "Abner_1": "General del ejército de Saúl (1 S 14:50); su padre Ner era tío de Saúl (1 S 14:50-51).",
    "Michal_1": ("Hija menor de Saúl (1 S 14:49), mujer de David (1 S 18:27); Saúl la da luego a Palti (1 S 25:44)."),
    "Ahinoam_1": "Mujer de Saúl, hija de Ahimaas (1 S 14:50). Distinta de Ahinoam de Jezreel, mujer de David (1 S 25:43).",
    "Ahinoam_2": "De Jezreel, mujer de David (1 S 25:43; 27:3). Distinta de Ahinoam, mujer de Saúl (1 S 14:50).",
    "Ahimelech_1": "Sacerdote de Nob (1 S 21:1); Saúl lo manda matar con los sacerdotes (1 S 22:16-18).",
    "Ahimelech_2": "Heteo, de los de David (1 S 26:6). Distinto de Ahimelec, sacerdote de Nob.",
    "Ahitub_1": ("1 S 14:3: «Achîas hijo de Achîtob, hermano de Ichâbod, hijo de Phinees». 1 S 22:9: «Ahimelech hijo de "
                 "Ahitob». BibleData los toma por el mismo Ahitob; la RV1909 escribe «Achîtob» en 14:3 y «Ahitob» en 22."),
    "Gad_2": "Profeta (1 S 22:5). Distinto de Gad hijo de Jacob.",
    "Laish_1": "Padre de Palti, de Galim (1 S 25:44). No es la ciudad de Lais (Jue 18).",
    "Palti_2": "1 S 25:44: Saúl le da a Mical, mujer de David. Distinto de Palti de Benjamín (Nm 13:9).",
    "Nahash_1": "Rey de los hijos de Ammón (1 S 12:12) que sitia Jabes de Galaad (1 S 11:1-2).",
    "Achish_1": "Rey de Gat (1 S 21:10), hijo de Maoc (1 S 27:2); da Siclag a David (1 S 27:6).",
    "Doeg_1": "Idumeo, principal de los pastores de Saúl (1 S 21:7); mata a los sacerdotes de Nob (1 S 22:18).",
    "Abiathar_1": "Hijo de Ahimelec; único que escapa de la matanza de Nob y huye a David (1 S 22:20).",
}
IDENTIDAD = {
    "Barak_1": {"certeza": "inferido", "refs": ["1S 12:11"], "nombres_rv1909": ["Barac", "Bedán"], "fuente": "bibledata",
                "nota": ("1 S 12:11 (RV1909, texto masorético): «envió á Jerobaal, y á Bedán, y á Jephté». Ningún juez se "
                         "llama Bedán en Jueces; Brenton (LXX) lee «Barac» en ese versículo y BibleData lo identifica con "
                         "Barac. No lo dice el texto hebreo: identidad inferida.")},
    "Ishvi_2": {"certeza": "inferido", "refs": ["1S 14:49", "1S 31:2"], "nombres_rv1909": ["Isui", "Abinadab"],
                "fuente": "bibledata",
                "nota": ("1 S 14:49 «Jonathán, Isui, y Melchi-sua»; 1 S 31:2 «Jonathán, y á Abinadab, y á Melchîsua». "
                         "BibleData los toma por la misma persona; el texto no lo dice.")},
}
NOTAS_VERIFICAR = [
    ("TM", (1, 1), "Ramathaim de Sophim, del monte de Ephraim"), ("TM", (1, 1), "Ephrateo"),
    ("TM", (2, 21), "parió tres hijos, y dos hijas"), ("TM", (1, 9), "el sacerdote Eli"),
    ("TM", (4, 15), "noventa y ocho años"), ("TM", (4, 18), "había juzgado á Israel cuarenta años"),
    ("TM", (4, 11), "muertos los dos hijos de Eli, Ophni y Phinees"), ("TM", (4, 21), "Traspasada es la gloria de Israel"),
    ("TM", (6, 14), "al campo de Josué Beth-semita"), ("TM", (7, 15), "todo el tiempo que vivió"),
    ("TM", (3, 20), "fiel profeta de Jehová"), ("TM", (9, 21), "¿No soy yo hijo de Benjamín"),
    ("TM", (14, 49), "Jonathán, Isui, y Melchi-sua"), ("TM", (31, 2), "Jonathán, y á Abinadab, y á Melchîsua"),
    ("TM", (14, 50), "Abner, hijo de Ner tío de Saúl"), ("TM", (15, 33), "Samuel cortó en pedazos á Agag"),
    ("TM", (17, 4), "tenía de altura seis codos y un palmo"), ("TM", (17, 13), "Eliab el primogénito, el segundo Abinadab"),
    ("TM", (21, 7), "Doeg, Idumeo, principal de los pastores de Saúl"), ("TM", (22, 18), "revolviéndose Doeg Idumeo"),
    ("TM", (14, 3), "Achîas hijo de Achîtob, hermano de Ichâbod, hijo de Phinees"), ("TM", (22, 9), "Ahimelech hijo de Ahitob"),
    ("TM", (22, 5), "Gad profeta"), ("TM", (25, 44), "Palti hijo de Lais, que era de Gallim"),
    ("TM", (12, 12), "Naas rey de lo hijos de Ammón"), ("TM", (27, 6), "Achîs le dió aquel día á Siclag"),
    ("TM", (26, 6), "Ahimelech Hetheo"), ("TM", (12, 11), "envió á Jerobaal, y á Bedán, y á Jephté"),
    ("LXX", (12, 11), "Jerobaal, and Barac, and Jephthae"), ("TM", (31, 4), "tomó Saúl la espada, y echóse sobre ella"),
    ("TM", (14, 50), "el nombre del general de su ejército era Abner"), ("TM", (25, 43), "Ahinoam de Jezreel"),
    ("TM", (1, 11), "E hizo voto"), ("TM", (22, 20), "escapó, y huyóse á David"),
]
ROLES = {
    "Elkanah_2": ("efrateo de Ramataim, marido de Ana y Penina", (1, 1), "que se llamaba Elcana"),
    "Hannah_1": ("mujer de Elcana, madre de Samuel", (1, 2), "el nombre de la una era Anna"),
    "Peninnah_1": ("mujer de Elcana", (1, 2), "el nombre de la otra Peninna"),
    "Eli_1": ("sacerdote en Silo", (1, 9), "el sacerdote Eli"),
    "Hophni_1": ("hijo de Elí, sacerdote en Silo", (1, 3), "Ophni y Phinees, sacerdotes de Jehová"),
    "Phinehas_2": ("hijo de Elí, sacerdote en Silo", (1, 3), "Ophni y Phinees, sacerdotes de Jehová"),
    "Samuel_2": ("profeta y juez de Israel", (3, 20), "Samuel era fiel profeta de Jehová"),
    "Joshua_2": ("de Bet-semes, en cuyo campo para el carro del arca", (6, 14), "al campo de Josué Beth-semita"),
    "Saul_1": ("primer rey de Israel, benjaminita, hijo de Cis", (9, 21), "¿No soy yo hijo de Benjamín"),
    "Nahash_1": ("rey de los hijos de Ammón", (12, 12), "Naas rey de lo hijos de Ammón"),
    "Ahijah_1": ("sacerdote que lleva el efod con Saúl", (14, 3), "llevaba el ephod"),
    "Abner_1": ("general del ejército de Saúl", (14, 50), "el nombre del general de su ejército era Abner"),
    "Agag_2": ("rey de Amalec", (15, 8), "Agag rey de Amalec"),
    "Goliath_1": ("gigante filisteo de Gat", (17, 4), "se llamaba Goliath, de Gath"),
    "Ahimelech_1": ("sacerdote de Nob", (21, 1), "á Ahimelech sacerdote"),
    "Doeg_1": ("idumeo, principal de los pastores de Saúl", (21, 7), "Doeg, Idumeo, principal de los pastores de Saúl"),
    "Achish_1": ("rey de Gat", (21, 10), "Achîs rey de Gath"),
    "Gad_2": ("profeta", (22, 5), "Gad profeta"),
    "Ahimelech_2": ("heteo, de los hombres de David", (26, 6), "Ahimelech Hetheo"),
    "Joab_1": ("hermano de Abisai", (26, 6), "Abisai hijo de Sarvia, hermano de Joab"),
    "Nabal_1": ("hombre rico de Maón, del linaje de Caleb", (25, 3), "era del linaje de Caleb"),
}
SIN_NOMBRE = {}
RELACIONES = [
    ("Jeroham_1", "Elkanah_2", "padre", (1, 1), "Elcana, hijo de Jeroham", ""),
    ("Elihu_1", "Jeroham_1", "padre", (1, 1), "Jeroham, hijo de Eliú", ""),
    ("Tohu_1", "Elihu_1", "padre", (1, 1), "Eliú, hijo de Thohu", ""),
    ("Zuph_1", "Tohu_1", "padre", (1, 1), "Thohu, hijo de Suph", ""),
    ("Elkanah_2", "Hannah_1", "conyuge", (1, 2), "Y tenía él dos mujeres; el nombre de la una era Anna", ""),
    ("Elkanah_2", "Peninnah_1", "conyuge", (1, 2), "el nombre de la otra Peninna", "1 S 1:4: «Peninna su mujer»."),
    ("Eli_1", "Hophni_1", "padre", (1, 3), "dos hijos de Eli, Ophni y Phinees", ""),
    ("Eli_1", "Phinehas_2", "padre", (1, 3), "dos hijos de Eli, Ophni y Phinees", ""),
    ("Elkanah_2", "Samuel_2", "padre", (1, 19), "Elcana conoció á Anna su mujer",
     "1 S 1:20: Ana concibe y pare a Samuel; 1 S 1:21-23 y 2:11: Elcana, su marido."),
    ("Hannah_1", "Samuel_2", "madre", (1, 20), "después de haber concebido Anna, parió un hijo, y púsole por nombre Samuel", ""),
    ("Phinehas_2", "Ichabod_1", "padre", (4, 21), "llamó al niño Ichâbod",
     "1 S 4:19: quien lo pare es «la mujer de Phinees»; 1 S 14:3: «Ichâbod, hijo de Phinees». La madre no tiene nombre."),
    ("Phinehas_2", "Ahitub_1", "padre", (14, 3), "Achîtob, hermano de Ichâbod, hijo de Phinees", ""),
    ("Ahitub_1", "Ahijah_1", "padre", (14, 3), "Achîas hijo de Achîtob", ""),
    ("Abinadab_1", "Eleazar_2", "padre", (7, 1), "santificaron á Eleazar su hijo", ""),
    ("Samuel_2", "Joel_1", "padre", (8, 2), "el nombre de su hijo primogénito fué Joel", ""),
    ("Samuel_2", "Abijah_1", "padre", (8, 2), "el nombre del segundo, Abia", ""),
    ("Abiel_1", "Kish_1", "padre", (9, 1), "Cis, hijo de Abiel", "1 S 14:51: Cis y Ner «fueron hijos de Abiel»."),
    ("Zeror_1", "Abiel_1", "padre", (9, 1), "Abiel, hijo de Seor", ""),
    ("Becorath_1", "Zeror_1", "padre", (9, 1), "Seor, hijo de Bechôra", ""),
    ("Aphiah_1", "Becorath_1", "padre", (9, 1), "Bechôra, hijo de Aphia", ""),
    ("Kish_1", "Saul_1", "padre", (9, 2), "tenía él un hijo que se llamaba Saúl", "1 S 9:3: «Cis, padre de Saúl»."),
    ("Saul_1", "Jonathan_2", "padre", (14, 1), "Jonathán hijo de Saúl", "1 S 13:16: «Saúl pues y Jonathán su hijo»."),
    ("Saul_1", "Ishvi_2", "padre", (14, 49), "los hijos de Saúl fueron Jonathán, Isui, y Melchi-sua",
     "1 S 31:2 nombra «Abinadab» entre los hijos de Saúl; BibleData lo identifica con Isúi."),
    ("Saul_1", "Malchi-shua_1", "padre", (14, 49), "los hijos de Saúl fueron Jonathán, Isui, y Melchi-sua",
     "1 S 31:2: «Melchîsua, hijos de Saúl»."),
    ("Saul_1", "Merab_1", "padre", (14, 49), "el nombre de la mayor, Merab", "1 S 18:19: «Merab, hija de Saúl»."),
    ("Saul_1", "Michal_1", "padre", (18, 20), "Michâl la [otra] hija de Saúl", "1 S 14:49: «el de la menor, Michâl»."),
    ("Saul_1", "Ahinoam_1", "conyuge", (14, 50), "el nombre de la mujer de Saúl era Ahinoam", ""),
    ("Ahimaaz_1", "Ahinoam_1", "padre", (14, 50), "Ahinoam, hija de Aimaas", ""),
    ("Ner_1", "Abner_1", "padre", (14, 50), "Abner, hijo de Ner", "1 S 14:51: «Ner padre de Abner»."),
    ("Abiel_1", "Ner_1", "padre", (14, 51), "Ner padre de Abner, fueron hijos de Abiel", ""),
    ("Jesse_1", "Eliab_3", "padre", (17, 13), "los tres hijos mayores de Isaí",
     "1 S 17:13: «Eliab el primogénito, el segundo Abinadab, y el tercero Samma»; 1 S 16:6-9."),
    ("Jesse_1", "Abinadab_2", "padre", (17, 13), "el segundo Abinadab", "1 S 17:13: hijos de Isaí; 1 S 16:8."),
    ("Jesse_1", "Shammah_2", "padre", (17, 13), "el tercero Samma", "1 S 17:13: hijos de Isaí; 1 S 16:9."),
    ("Adriel_1", "Merab_1", "conyuge", (18, 19), "fué dada por mujer á Adriel Meholatita", ""),
    ("David_1", "Michal_1", "conyuge", (18, 27), "Saúl le dió á su hija Michâl por mujer", "1 S 19:11: «Michâl su mujer»."),
    ("Ahitub_1", "Ahimelech_1", "padre", (22, 9), "Ahimelech hijo de Ahitob", ""),
    ("Ahimelech_1", "Abiathar_1", "padre", (22, 20), "uno de los hijos de Ahimelech hijo de Ahitob, que se llamaba Abiathar", ""),
    ("Abigail_1", "Nabal_1", "conyuge", (25, 3), "el nombre de su mujer, Abigail", ""),
    ("Abigail_1", "David_1", "conyuge", (25, 42), "fué su mujer", "1 S 25:39: David envía «para tomarla por su mujer»."),
    ("Ahinoam_2", "David_1", "conyuge", (25, 43), "También tomó David á Ahinoam de Jezreel", "«ambas á dos fueron sus mujeres»."),
    ("Michal_1", "Palti_2", "conyuge", (25, 44), "Saúl había dado su hija Michâl mujer de David, á Palti", ""),
    ("Laish_1", "Palti_2", "padre", (25, 44), "Palti hijo de Lais", ""),
    ("Zeruiah_1", "Abishai_1", "madre", (26, 6), "Abisai hijo de Sarvia", ""),
    ("Maoch_1", "Achish_1", "padre", (27, 2), "Achîs hijo de Maoch", ""),
]
NOTAS_REL = {}
# Relaciones de los libros anteriores que 1 Samuel repite: se añade la referencia a la nota.
REPITE_GN = [
    ("Jesse_1", "David_1", "padre", (17, 12), "David era hijo de aquel hombre Ephrateo"),
    ("Jesse_1", "David_1", "padre", (17, 58), "Yo soy hijo de tu siervo Isaí de Beth-lehem"),
]
# Edad de Elí el día de su muerte (1 S 4:15, 4:18): TM 98, LXX 90.
EDADES = [("Eli_1", "en_evento", (4, 15), 0, 0, "el día en que llega la noticia de la batalla y muere (1 S 4:18)")]
NOTAS_EXISTENTES = {
    "David_1": ("1 S 16:13: Samuel lo unge «de entre sus hermanos»; 1 S 17:12: «David era hijo de aquel hombre Ephrateo "
                "de Beth-lehem de Judá, cuyo nombre era Isaí» (la misma persona que en Rut 4:17-22)."),
    "Jesse_1": "1 S 17:12: «el cual tenía ocho hijos»; 1 S 16:10: «sus siete hijos» pasan delante de Samuel antes de David.",
    "Barak_1": ("1 S 12:11: la RV1909 dice «Bedán» donde Brenton (LXX) dice «Barac»; BibleData lo identifica con Barac "
                "(identidad inferida)."),
    "Pharaoh_4": ("1 S 6:6: los filisteos recuerdan «como los Egipcios y Faraón endurecieron su corazón»; 1 S 2:27: «en "
                  "Egipto en casa de Faraón». BibleData lo asigna al faraón de las plagas."),
}
NOTAS_VERIFICAR += [("TM", (16, 13), "ungiólo de entre sus hermanos"), ("TM", (17, 12), "el cual tenía ocho hijos"),
                    ("TM", (16, 10), "sus siete hijos"), ("TM", (6, 6), "como los Egipcios y Faraón endurecieron su corazón"),
                    ("TM", (2, 27), "en Egipto en casa de Faraón"), ("TM", (13, 16), "Saúl pues y Jonathán su hijo"),
                    ("TM", (18, 19), "Merab, hija de Saúl"), ("TM", (19, 11), "Michâl su mujer"), ("TM", (9, 3), "Cis, padre de Saúl"),
                    ("TM", (1, 4), "Peninna su mujer"), ("TM", (25, 39), "para tomarla por su mujer")]
# Refs que el texto da a una persona y BibleData no sitúa: «el hijo de Isaí» nombra a Isaí; Samuel en 10:26 y 28:20.
REFS_EXTRA = {"Jesse_1": [(20, 27), (20, 30), (20, 31), (22, 7), (22, 8), (22, 9), (22, 13), (25, 10)],
              "Samuel_2": [(10, 26), (28, 20)]}
REFS_QUITAR = {}

S1 = "Ana y el nacimiento de Samuel (1 S 1:1–2:11)"
S2 = "Elí y sus hijos; el llamado de Samuel (1 S 2:12–3:21)"
S3 = "El arca entre los filisteos (1 S 4–7)"
S4 = "Israel pide rey; Saúl ungido (1 S 8–12)"
S5 = "Las guerras y el rechazo de Saúl (1 S 13–15)"
S6 = "David ungido y Goliat (1 S 16–17)"
S7 = "David en la corte y su huida (1 S 18–20)"
S8 = "David fugitivo (1 S 21–27)"
S9 = "Endor y Gilboa (1 S 28–31)"
PASAJES = [
    ("1:1", "1:8", "Elcana, Ana y Penina", "Elcana de Ramataim sube cada año a Silo; Penina tiene hijos y Ana no, y su rival la irrita.", S1),
    ("1:9", "1:18", "El voto de Ana", "En Silo Ana ora llorando y promete a Jehová el hijo que le dé; Elí la cree ebria y luego la despide en paz.", S1),
    ("1:19", "1:28", "Nace Samuel", "Ana da a luz a Samuel; cuando lo desteta lo lleva a Elí en Silo y lo deja dedicado a Jehová.", S1),
    ("2:1", "2:11", "El cántico de Ana", "Ana alaba a Jehová, que abate y ensalza; Elcana vuelve a Ramá y el niño sirve a Jehová delante de Elí.", S1),
    ("2:12", "2:26", "Los hijos de Elí", "Ofni y Finees desprecian las ofrendas de Jehová; Elí los reprende sin éxito, mientras Samuel crece sirviendo con su efod de lino.", S2),
    ("2:27", "2:36", "El varón de Dios contra la casa de Elí", "Un varón de Dios anuncia a Elí que sus dos hijos morirán el mismo día y que Dios levantará un sacerdote fiel.", S2),
    ("3:1", "3:21", "«Habla, que tu siervo oye»", "De noche Jehová llama a Samuel; Elí le enseña a responder; Jehová le anuncia el juicio sobre la casa de Elí y todo Israel lo reconoce como profeta.", S2),
    ("4:1", "4:11", "El arca tomada", "Israel, vencido junto a Eben-ezer, trae el arca de Silo; los filisteos de Afec vuelven a vencer, toman el arca y mueren Ofni y Finees.", S3),
    ("4:12", "4:22", "Muerte de Elí; nace Icabod", "Un benjamita trae la noticia a Silo; Elí cae de la silla y muere; la mujer de Finees da a luz a Icabod.", S3),
    ("5:1", "5:12", "El arca en Asdod, Gat y Ecrón", "Dagón cae ante el arca en Asdod; la mano de Jehová hiere a las ciudades filisteas adonde la llevan.", S3),
    ("6:1", "6:12", "Los filisteos devuelven el arca", "A los siete meses los filisteos devuelven el arca en un carro nuevo, tirado por dos vacas, con ofrendas de oro.", S3),
    ("6:13", "7:2", "Bet-semes y Quiriat-jearim", "En Bet-semes reciben el arca y son heridos por mirar dentro; la llevan a casa de Abinadab en Quiriat-jearim, donde pasan veinte años.", S3),
    ("7:3", "7:17", "Samuel juzga a Israel; Eben-ezer", "Israel quita los baales; en Mizpa Jehová truena contra los filisteos y Samuel pone una piedra: «Hasta aquí nos ayudó Jehová».", S3),
    ("8:1", "8:22", "«Constitúyenos ahora un rey»", "Los hijos de Samuel no andan en sus caminos; los ancianos piden rey; Samuel les advierte cómo los tratará el rey, y Jehová manda oírlos.", S4),
    ("9:1", "9:14", "Saúl busca las asnas de Cis", "Saúl, hijo de Cis, busca con un criado las asnas perdidas de su padre y llega a la ciudad del vidente.", S4),
    ("9:15", "9:27", "Samuel recibe a Saúl", "Jehová había avisado a Samuel; este sienta a Saúl a la cabecera del banquete y al alba lo aparta para darle palabra de Dios.", S4),
    ("10:1", "10:16", "Saúl ungido; las señales", "Samuel unge a Saúl; se cumplen las señales anunciadas y Saúl profetiza con los profetas.", S4),
    ("10:17", "10:27", "Saúl elegido en Mizpa", "En Mizpa la suerte cae sobre Benjamín y sobre Saúl, escondido entre el bagaje; el pueblo grita «Viva el rey».", S4),
    ("11:1", "11:15", "Saúl libra a Jabes de Galaad", "Nahas amonita sitia Jabes; Saúl convoca a Israel, vence a los amonitas y en Gilgal lo invisten rey.", S4),
    ("12:1", "12:25", "Discurso de Samuel", "Samuel pide al pueblo testimonio de su rectitud, repasa la historia de Israel y Jehová envía truenos y lluvia en la siega.", S4),
    ("13:1", "13:15", "Saúl ofrece el holocausto en Gilgal", "Ante los filisteos en Micmas, Saúl no espera a Samuel y ofrece el holocausto; Samuel le anuncia que su reino no durará.", S5),
    ("13:16", "14:15", "Jonatán y su paje de armas", "Israel no tiene herreros; Jonatán y su paje trepan hasta la guarnición filistea y la tierra tiembla.", S5),
    ("14:16", "14:35", "El juramento de Saúl y la miel", "Los filisteos huyen; Saúl conjura al pueblo a no comer, Jonatán prueba miel sin saberlo y el pueblo cansado come con sangre.", S5),
    ("14:36", "14:52", "Jonatán salvado; la familia de Saúl", "La suerte cae sobre Jonatán y el pueblo lo libra de morir; guerras de Saúl, sus hijos, su mujer y su general Abner.", S5),
    ("15:1", "15:23", "Saúl y Amalec", "Saúl vence a Amalec pero perdona a Agag y lo mejor del ganado; Samuel le dice que «el obedecer es mejor que los sacrificios».", S5),
    ("15:24", "15:35", "Jehová desecha a Saúl", "Saúl rasga el manto de Samuel; Samuel le anuncia que Jehová le ha quitado el reino y da muerte a Agag en Gilgal.", S5),
    ("16:1", "16:13", "Samuel unge a David", "En Belén pasan ante Samuel los hijos de Isaí; Jehová elige al menor, David, y Samuel lo unge.", S6),
    ("16:14", "16:23", "David tañe el arpa ante Saúl", "Un espíritu malo atormenta a Saúl; David, que sabe tocar, entra a su servicio y lo alivia con el arpa.", S6),
    ("17:1", "17:11", "El desafío de Goliat", "Filisteos e israelitas acampan frente a frente; Goliat de Gat, armado de bronce, desafía a Israel.", S6),
    ("17:12", "17:30", "David llega al campamento", "Isaí envía a David con provisiones para sus hermanos; David oye el desafío y pregunta qué se dará a quien venza al filisteo.", S6),
    ("17:31", "17:58", "David vence a Goliat", "Sin armadura, con honda y piedra, David derriba a Goliat; los filisteos huyen y Saúl pregunta de quién es hijo.", S6),
    ("18:1", "18:16", "Jonatán y David; los celos de Saúl", "Jonatán hace alianza con David; las mujeres cantan «Saúl hirió sus miles, y David sus diez miles» y Saúl lo mira con recelo.", S7),
    ("18:17", "18:30", "Merab y Mical", "Saúl promete a Merab y la da a otro; Mical ama a David y Saúl se la da por mujer a cambio de una dote de guerra.", S7),
    ("19:1", "19:10", "Jonatán intercede; la lanza", "Jonatán aplaca a Saúl, pero el espíritu malo vuelve y Saúl intenta clavar a David en la pared.", S7),
    ("19:11", "19:24", "Mical salva a David; Najot", "Mical descuelga a David por una ventana; David huye a Samuel en Ramá y Saúl también profetiza en Najot.", S7),
    ("20:1", "20:23", "El pacto de David y Jonatán", "David y Jonatán acuerdan una señal con saetas para saber la intención de Saúl y renuevan su alianza.", S7),
    ("20:24", "20:42", "Las saetas de Jonatán", "En la fiesta de la luna nueva Saúl se enfurece contra Jonatán; este avisa a David con las saetas y se despiden.", S7),
    ("21:1", "21:9", "David en Nob", "El sacerdote Ahimelec da a David el pan sagrado y la espada de Goliat; Doeg idumeo lo ve.", S8),
    ("21:10", "22:5", "Ante Aquis; la cueva de Adulam", "David se finge loco ante Aquis de Gat, se refugia en la cueva de Adulam y deja a sus padres con el rey de Moab.", S8),
    ("22:6", "22:23", "La matanza de Nob", "Doeg delata a Ahimelec; Saúl manda matar a los sacerdotes de Nob y solo Abiatar escapa a David.", S8),
    ("23:1", "23:14", "David libra a Keila", "David libra a Keila de los filisteos; consulta a Jehová con el efod y huye antes de que Saúl lo cerque.", S8),
    ("23:15", "23:29", "Zif y Maón", "Jonatán anima a David; los de Zif lo delatan y Saúl lo rodea en Maón, hasta que lo llaman a pelear contra los filisteos.", S8),
    ("24:1", "24:22", "David perdona a Saúl en En-gadi", "En una cueva David corta la orilla del manto de Saúl y no lo mata: «es el ungido de Jehová»; Saúl llora y le pide un juramento.", S8),
    ("25:1", "25:22", "Muere Samuel; Nabal", "Muere Samuel; Nabal, rico de Maón, desprecia a los mensajeros de David y David sale a vengarse.", S8),
    ("25:23", "25:44", "Abigail", "Abigail sale al encuentro de David con presentes y lo aparta de derramar sangre; muere Nabal y David la toma por mujer.", S8),
    ("26:1", "26:25", "La lanza y la botija", "De noche David y Abisai entran en el campamento de Saúl; David no deja que lo maten y se lleva su lanza y su botija.", S8),
    ("27:1", "27:12", "David entre los filisteos: Siclag", "David se refugia con Aquis de Gat, recibe Siclag y hace incursiones contra los pueblos del sur.", S8),
    ("28:1", "28:14", "Saúl y la adivina de Endor", "Jehová no responde a Saúl; disfrazado, Saúl pide a una mujer de Endor que haga subir a Samuel.", S9),
    ("28:15", "28:25", "Samuel anuncia la derrota", "Samuel anuncia a Saúl que Jehová le ha quitado el reino y que al día siguiente él y sus hijos estarán con él.", S9),
    ("29:1", "29:11", "Los filisteos despiden a David", "Los príncipes filisteos no quieren a David en la batalla; Aquis lo envía de vuelta.", S9),
    ("30:1", "30:15", "Siclag quemada", "Los amalecitas queman Siclag y se llevan a las mujeres y los hijos; David se esfuerza en Jehová y un egipcio lo guía.", S9),
    ("30:16", "30:31", "David recobra todo", "David vence a los amalecitas y recobra todo; reparte por igual el botín y envía presentes a los ancianos de Judá.", S9),
    ("31:1", "31:13", "Muerte de Saúl en Gilboa", "Los filisteos vencen en el monte Gilboa; mueren los hijos de Saúl y Saúl se echa sobre su espada; los de Jabes recogen sus cuerpos.", S9),
]
# Citas de los resúmenes que van entre comillas (se comprueban).
CITAS_RESUMEN = [((3, 10), "Habla, que tu siervo oye"), ((7, 12), "Hasta aquí nos ayudó Jehová"),
                 ((8, 5), "constitúyenos ahora un rey"), ((10, 24), "Viva el rey"),
                 ((15, 22), "el obedecer es mejor que los sacrificios"), ((18, 7), "Saúl hirió sus miles, y David sus diez miles"),
                 ((24, 7), "es el ungido de Jehová")]

# ---------------------------------------------------------------- lugares
# Lugares configurados a mano: obid -> (id, nombre, formas RV1909, tipo, nota, forzar baja).
_RAMA = ("1 S 1:1: Elcana es «de Ramathaim de Sophim»; 1 S 1:19 y 2:11: vuelven «á su casa en Ramatha»; 1 S 7:17: Samuel "
         "tiene su casa en «Rama». Se toman como el mismo lugar (inferido del texto). OpenBible los registra aparte "
         "(Ramathaim-zophim y Ramah 4), ambos con Al Ram como identificación preferida, la misma que da para Ramá de "
         "Benjamín (Jos 18:25); OpenBible no los une y aquí tampoco.")
LUGARES_MANUAL = {
    "a90f6e1": ("rama-de-samuel", "Ramá (Ramataim de Sofim)", ["Ramathaim de Sophim", "Ramatha", "Rama"], "ciudad", _RAMA, False),
    "a54ef72": ("ramataim-de-sofim", "Ramataim de Sofim", ["Ramathaim de Sophim"], "ciudad", "", False),
    "abfdefc": ("eben-ezer", "Eben-ezer", ["Eben-ezer"], "ciudad",
                "Campamento de Israel frente a Afec (1 S 4:1); de allí llevan los filisteos el arca a Asdod (1 S 5:1).", False),
    "aadaf09": ("piedra-de-eben-ezer", "Piedra de Eben-ezer", ["Eben-ezer"], "otro",
                "1 S 7:12: Samuel pone una piedra «entre Mizpa y Sen» y la llama Eben-ezer. OpenBible la separa del "
                "Eben-ezer de 1 S 4:1.", False),
    "ab183f8": ("valle-de-ela", "Valle de Ela", ["Alcornoque"], "otro",
                "La RV1909 traduce «el valle del Alcornoque» (1 S 17:2, 17:19; 21:9); OpenBible: Valley of Elah. Allí "
                "David vence a Goliat.", False),
    "acf57c5": ("monte-gilboa", "Monte Gilboa", ["Gilboa"], "monte", "Allí mueren Saúl y sus hijos (1 S 31:1-8).", False),
    "afdda14": ("nob", "Nob", ["Nob"], "ciudad", "«Nob, ciudad de los sacerdotes» (1 S 22:19).", False),
    "ac702f1": ("mizpa-de-moab", "Mizpa de Moab", ["Mizpa"], "ciudad", "1 S 22:3: «Mizpa de Moab».", False),
    "a7df136": ("bosque-de-haret", "Bosque de Haret", ["Hareth"], "otro", "1 S 22:5: «el bosque de Hareth».", False),
    "a57df09": ("torrente-de-besor", "Torrente de Besor", ["Besor"], "rio", "1 S 30:9-10, 21: «el torrente de Besor».", False),
    "a7c5927": ("valle-de-seboim", "Valle de Seboim", ["Seboim"], "otro", "1 S 13:18: «el valle de Seboim».", False),
    "a50057d": ("desierto-de-zif", "Desierto de Zif", ["Ziph"], "region", "1 S 23:14; 26:2: «el desierto de Ziph».", False),
    "ae11a0d": ("desierto-de-maon", "Desierto de Maón", ["Maón"], "region", "1 S 23:24-25: «el desierto de Maón».", False),
    "a897bdb": ("sela-hama-lecot", "Sela-hama-lecot", ["Sela-hammah-lecoth"], "otro",
                "1 S 23:28: nombre que ponen al lugar donde Saúl deja de perseguir a David.", False),
    "a8530e9": ("campina-de-tabor", "Campiña de Tabor", ["Tabor"], "otro",
                "1 S 10:3: «la campiña de Tabor»; distinta del monte Tabor.", False),
}
PRECEDIDO = {"ab183f8": "valle del ", "a8530e9": "campiña de ", "a7df136": "bosque de ", "a57df09": "torrente de ",
             "a7c5927": "valle de ", "a50057d": "desierto de ", "ae11a0d": "desierto de "}
EXCLUIR_LUGAR = {
    "a1cb244": "Néguev: la RV1909 traduce «el mediodía»; no es nombre propio.",
    "ac71e65": "Filistea (1 S 31:9): la RV1909 dice «tierra de los Filisteos» (gentilicio).",
}
# Mizpa de Benjamín (1 S 7; 10:17): OpenBible la separa de «Mizpeh 1» (Jos 18:26) con la misma identificación (Tell
# en-Nasbeh), como en Jueces. Jezreel de Judá (1 S 25:43): la misma identificación que «jezreel-juda» (Jos 15:56).
UNIR_LUGAR_MANUAL = {"a736f6c": "mizpa-18-26", "ac644e9": "jezreel-juda"}
FORMAS_UNIR = {"ac644e9": ["Jezreel"]}
UNIR_LUGAR = {}
NOMBRE_LUGAR = {"Beer-sebah": "Beerseba", "Beth-lehem": "Belén", "Jerusalem": "Jerusalén", "Michmas": "Micmas",
                "Engaddi": "En-gadi", "Najoth": "Najot", "Selsah": "Selsa", "Hachîla": "Haquila", "Ziph": "Zif",
                "Sochô": "Soco", "Sela-hammah-lecoth": "Sela-hama-lecot", "Gallim": "Galim", "Bethcar": "Bet-car"}
NOMBRE_OB = {"a15bdfd": ("Ramá junto a Gabaa", "1 S 22:6: Saúl está «en Gabaa debajo de un árbol en Rama». OpenBible la "
                         "toma por una altura junto a Gabaa, distinta de la Ramá de Samuel."),
             "aeb5f24": ("Betel del sur", "1 S 30:27: ciudad del sur de Judá a la que David envía presentes; distinta de "
                         "Betel (Gn 28:19).")}
OBLIGATORIOS_LUGAR = ["rama-de-samuel", "siloh", "eben-ezer", "afec", "asdod", "gat", "ecron", "bet-semes",
                      "quiriat-jearim", "mizpa-18-26", "gilgal", "gabaa", "belen", "valle-de-ela", "nob", "ceila", "engedi",
                      "siclag", "endor", "monte-gilboa", "bet-san", "jabes-de-galaad"]
LUGARES = {}
LUGAR_OPCIONAL = set()
EXCL_AUTO = {}
INFO_AUTO = {}
moderno = josue.moderno
LUGAR_NO_PERSONA = []
INFO_VERSIFICACION = {}


def comprobar_versificacion(rv, br, errores):
    """Recuentos, extremos, versículos sin LXX, desfase por capítulo, nombres paralelos y longitudes."""
    for c, n in enumerate(POR_CAPITULO, 1):
        hay = sum(1 for (cc, _) in rv if cc == c)
        if hay != n:
            errores.append(f"1 Samuel {c}: la RV1909 tiene {hay} versículos (numeración inglesa: {n})")
    vacios = sorted(k for k, t in rv.items() if not t.strip())
    if vacios != sorted(VACIOS):
        errores.append(f"1 Samuel: versículos vacíos {vacios} (se esperaban {sorted(VACIOS)})")
    for ref, ini in VERSIFICACION:
        if not rv.get(ref, "").startswith(ini):
            errores.append(f"Versificación de 1 S {ref[0]}:{ref[1]}: la RV1909 no empieza «{ini}»")
    for ref, fin in FIN_VERSICULO:
        if not rv.get(ref, "").endswith(fin):
            errores.append(f"Versificación de 1 S {ref[0]}:{ref[1]}: la RV1909 no termina «{fin}»")
    for ref, frag in VERSIFICACION_LXX:
        if frag not in br.get(ref, ""):
            errores.append(f"Brenton 1 S {ref[0]}:{ref[1]} (numeración RV) no dice «{frag}»")
    falta = {k for k in rv if k not in br}
    if falta != SIN_LXX or [k for k in br if k not in rv]:
        errores.append(f"1 Samuel: versículos sin Brenton {sorted(falta ^ SIN_LXX)} o de más {[k for k in br if k not in rv]}")
    # Desfase: en cada capítulo, comparar el versículo n con el n de Brenton debe dar menos diferencia de longitud
    # (media de |log(RV/LXX)|) que compararlo con el n-1 o el n+1.
    costes = {}
    for c in range(1, CAPITULOS + 1):
        def coste(d):
            xs = [abs(math.log(len(rv[(c, v)]) / len(br[(c, v + d)]))) for (cc, v) in rv
                  if cc == c and rv[(c, v)] and (c, v) in br and (c, v + d) in br]
            return sum(xs) / len(xs)
        costes[c] = (coste(0), coste(-1), coste(1))
        if not costes[c][0] < min(costes[c][1:]):
            errores.append(f"Versificación de 1 S {c}: el emparejamiento con desfase compara mejor que sin él {costes[c]}")
    INFO_VERSIFICACION["desfase"] = {c: tuple(round(x, 2) for x in v) for c, v in costes.items()}
    comunes = {k for k in rv if k in br and rv[k]}
    for es, en in PARALELOS:
        a = {k for k in comunes if re.search(r"(?<!\w)%s(?!\w)" % re.escape(es), rv[k])}
        b = {k for k in comunes if re.search(r"(?<!\w)%s" % re.escape(en), br[k])}
        if a != b or not a:
            errores.append(f"Versificación de 1 S: «{es}» (RV1909) y «{en}» (Brenton) no caen en los mismos versículos: "
                           f"solo RV {sorted(a - b)}, solo LXX {sorted(b - a)}")
    for k in sorted(comunes):
        r = len(rv[k]) / len(br[k])
        if not PROPORCION[0] <= r <= PROPORCION[1]:
            errores.append(f"Versificación de 1 S {k[0]}:{k[1]}: longitud RV1909/Brenton fuera de rango ({r:.2f})")
    INFO_VERSIFICACION["comunes"] = len(comunes)


def construir(cx):
    rv, br, errores = cx["rv"], cx["br"], cx["errores"]
    comprobar_versificacion(rv, br, errores)
    for ref, frag in CITAS_RESUMEN:
        if frag not in rv.get(ref, ""):
            errores.append(f"Resumen de pasaje: «{frag}» no está en 1 S {ref[0]}:{ref[1]}")
    res = exodo.construir(cx, sys.modules[__name__])
    for c in res["capitulos"]:
        for v in c["versiculos"]:
            if (c["cap"], v["n"]) in VACIOS and not v["texto"]:
                v["nota"] = (f"La RV1909 no tiene este versículo aparte: numera el capítulo como el texto hebreo y su texto "
                             f"está en {VACIOS[(c['cap'], v['n'])]}.")
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
    prev = {l["id"]: l for l in lugares_previos}
    for obid, lid in UNIR_LUGAR_MANUAL.items():
        if lid in prev:
            formas = list(dict.fromkeys(prev[lid]["formas_rv1909"] + FORMAS_UNIR.get(obid, [])))
            LUGARES[obid] = (lid, prev[lid]["nombre"], formas, prev[lid]["tipo"], "", False)
            LUGAR_OPCIONAL.add(obid)
    UNIR_LUGAR = {**unir, **UNIR_LUGAR_MANUAL}
    EXCLUIR_LUGAR = {**EXCLUIR_LUGAR, **EXCL_AUTO}
    nuevos, menciones, info = exodo.construir_lugares(rv, menciones_personas, rutas, lugares_previos, errores, avisos, sa,
                                                      sys.modules[__name__])
    # Ramataim de Sofim (1 S 1:1) es la Ramá de Samuel: se une (ver _RAMA).
    por = {l["id"]: l for l in nuevos}
    a, b = por.get("rama-de-samuel"), por.get("ramataim-de-sofim")
    if not a or not b:
        errores.append("1 Samuel: falta Ramá o Ramataim de Sofim para unirlos")
    else:
        a["refs"] = sorted(set(a["refs"]) | set(b["refs"]), key=exodo.clave_ref)
        a["alternativas"] = a["alternativas"] + [dict(x, nota=f"OpenBible para «Ramathaim-zophim» ({b['url_fuente']})")
                                                 for x in ([b["ubicacion"]] if b["ubicacion"] else [])]
        for m in menciones:
            if m["lugar"] == "ramataim-de-sofim":
                m["lugar"] = "rama-de-samuel"
        nuevos.remove(b)
    return nuevos, menciones, info


# ---------------------------------------------------------------- hechos obligatorios (sobre los datos finales)
def comprobar(datos, errores):
    """Comprueba los hechos pedidos para 1 Samuel (falla si falta alguno). Devuelve líneas de informe."""
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
            errores.append(f"Hecho obligatorio (1 Samuel): {desc}")

    def tiene(pid, ref, mencion=True):
        return ref in P.get(pid, {}).get("refs", []) and (not mencion or (ref, pid) in M)

    def rel(de, a, tipo, ref):
        if tipo == "conyuge":
            de, a = sorted((de, a))
        x = R.get((de, a, tipo))
        return bool(x) and x["certeza"] == "explicito" and (
            x["ref"] == ref and x.get("cita") and x["cita"] in texto.get(ref, "") or f"{ref}:" in x["nota"])

    def sin_libro(pid, pref):
        return not any(r.startswith(pref) for r in P.get(pid, {}).get("refs", []))

    ok_(len(caps) == CAPITULOS and len(texto) == VERSICULOS and [len(c["versiculos"]) for c in caps] == POR_CAPITULO,
        f"{CAPITULOS} capítulos y {VERSICULOS} versículos (hay {len(caps)} y {len(texto)})")
    vacios = [r for r, t in texto.items() if not t]
    v_nota = [v for c in caps for v in c["versiculos"] if not v["texto"]]
    ok_(vacios == ["1S 23:29"] and all("1S 24:1" in v.get("nota", "") for v in v_nota),
        f"solo 1S 23:29 vacío, con nota que remite a 24:1 ({vacios})")
    ok_(tiene("Elkanah_2", "1S 1:1") and rel("Elkanah_2", "Hannah_1", "conyuge", "1S 1:2")
        and rel("Elkanah_2", "Peninnah_1", "conyuge", "1S 1:2") and tiene("Hannah_1", "1S 1:2") and tiene("Peninnah_1", "1S 1:2")
        and sin_libro("Elkanah_2", "Ex ") and sin_libro("Elkanah_1", "1S "),
        "Elcana, con Ana y Penina como mujeres (1:1-2); distinto de Elcana de Ex 6:24")
    ok_(tiene("Samuel_2", "1S 1:20") and rel("Elkanah_2", "Samuel_2", "padre", "1S 1:19") and rel("Hannah_1", "Samuel_2", "madre", "1S 1:20")
        and sin_libro("Samuel_1", "1S ") and sin_libro("Samuel_2", "Nm "), "Samuel, hijo de Elcana y Ana (1:19-20)")
    ok_(tiene("Eli_1", "1S 1:9") and "sacerdote" in P["Eli_1"]["rol"], "Elí sacerdote (1:9)")
    ok_(rel("Eli_1", "Hophni_1", "padre", "1S 1:3") and rel("Eli_1", "Phinehas_2", "padre", "1S 1:3")
        and tiene("Hophni_1", "1S 1:3") and tiene("Phinehas_2", "1S 1:3") and sin_libro("Phinehas_1", "1S ")
        and sin_libro("Phinehas_2", "Nm "), "Ofni y Finees, hijos de Elí (1:3); Finees ≠ el de Nm 25")
    ok_(tiene("Ichabod_1", "1S 4:21") and rel("Phinehas_2", "Ichabod_1", "padre", "1S 4:21") and "1S 4:19" in P["Phinehas_2"]["refs"],
        "Icabod, hijo de Finees (4:19-21)")
    ok_(tiene("Saul_1", "1S 9:2") and tiene("Kish_1", "1S 9:1") and rel("Kish_1", "Saul_1", "padre", "1S 9:2")
        and "benjaminita" in P["Saul_1"]["rol"], "Saúl, hijo de Cis (9:1-2), benjaminita")
    ok_(tiene("Jonathan_2", "1S 14:1") and rel("Saul_1", "Jonathan_2", "padre", "1S 14:1") and sin_libro("Jonathan_1", "1S ")
        and sin_libro("Jonathan_2", "Jue "), "Jonatán, hijo de Saúl (14:1), distinto del de Jue 18:30")
    ok_(tiene("David_1", "1S 16:13") and tiene("David_1", "1S 17:12") and "Rut 4:17" in P["David_1"]["refs"]
        and tiene("Jesse_1", "1S 16:1") and rel("Jesse_1", "David_1", "padre", "1S 17:12"),
        "David, hijo de Isaí (16:1-13; 17:12), el mismo id que en Rut 4:17")
    ok_(tiene("Goliath_1", "1S 17:4") and "Gat" in P["Goliath_1"]["rol"], "Goliat de Gat (17:4)")
    ok_(tiene("Abner_1", "1S 14:50") and rel("Ner_1", "Abner_1", "padre", "1S 14:50"), "Abner, hijo de Ner (14:50)")
    ok_(tiene("Michal_1", "1S 18:20") and tiene("Michal_1", "1S 18:27") and rel("Saul_1", "Michal_1", "padre", "1S 18:20")
        and rel("David_1", "Michal_1", "conyuge", "1S 18:27"), "Mical, hija de Saúl y mujer de David (18:20-27)")
    ok_(tiene("Abigail_1", "1S 25:3") and rel("Nabal_1", "Abigail_1", "conyuge", "1S 25:3")
        and rel("David_1", "Abigail_1", "conyuge", "1S 25:42"), "Abigail, mujer de Nabal (25:3) y luego de David (25:39-42)")
    ok_(tiene("Achish_1", "1S 21:10") and "rey de Gat" in P["Achish_1"]["rol"], "Aquis, rey de Gat (21:10)")
    ok_(not [p for p in EXCLUIR if any(r.startswith("1S ") for r in P.get(p, {}).get("refs", []))]
        and [r for r in P["Jacob_1"]["refs"] if r.startswith("1S ")] == ["1S 12:8"],
        "sin personas para Dios, «NA», Amalec, Ammón ni los reyes de Moab sin nombre; Jacob solo en 12:8 («Israel» es el pueblo)")
    b = P.get("Barak_1", {})
    ok_(tiene("Barak_1", "1S 12:11") and "Bedán" in b.get("formas_rv1909", []) and b.get("identidad", {}).get("certeza") == "inferido",
        "Bedán (12:11) = Barac según BibleData y la LXX, identidad inferida")
    ok_(tiene("Ishvi_2", "1S 14:49") and tiene("Ishvi_2", "1S 31:2") and P["Ishvi_2"].get("identidad", {}).get("certeza") == "inferido"
        and sin_libro("Ishvi_1", "1S ") and sin_libro("Abinadab_1", "1S 31") and sin_libro("Abinadab_2", "1S 31"),
        "Isúi (14:49) = Abinadab hijo de Saúl (31:2) según BibleData, identidad inferida")
    ok_(tiene("Pharaoh_4", "1S 6:6") and "Ex 7:13" in P["Pharaoh_4"]["refs"], "Faraón de 1 S 6:6 = el de las plagas (Pharaoh_4)")
    ok_(rel("Saul_1", "Ishvi_2", "padre", "1S 14:49") and rel("Saul_1", "Malchi-shua_1", "padre", "1S 14:49")
        and tiene("Malchi-shua_1", "1S 31:2") and tiene("Jonathan_2", "1S 31:2"), "hijos de Saúl en 14:49 y 31:2")
    e = [x for x in datos["edades"] if x["persona"] == "Eli_1"]
    ok_(sorted((x["tradicion"], x["valor"]) for x in e) == [("LXX", 90), ("TM", 98)], f"edad de Elí: TM 98, LXX 90 (4:15) {e and [x['valor'] for x in e]}")
    for lid in OBLIGATORIOS_LUGAR:
        l = L.get(lid)
        ok_(bool(l) and any(r.startswith("1S ") and (r, lid) in ML for r in l["refs"]),
            f"lugar {lid} con refs de 1 S ({sum(1 for r in l['refs'] if r.startswith('1S ')) if l else 0})")
    ok_(("1S 1:1", "rama-de-samuel") in ML and ("1S 7:17", "rama-de-samuel") in ML and "ramataim-de-sofim" not in L,
        "Ramataim de Sofim (1:1) y Ramá (7:17) son el mismo lugar")
    ok_(("1S 24:1", "engedi") in ML and ("1S 7:6", "mizpa-18-26") in ML and ("1S 17:2", "valle-de-ela") in ML,
        "En-gadi en 24:1 (23:29 inglés), Mizpa de Benjamín (7:6) y el valle del Alcornoque (17:2)")
    sin = [l for l in datos["lugares"] if any(r.startswith("1S ") for r in l["refs"]) and not l["ubicacion"]]
    ok_(all("OpenBible no da identificación" in l["nota"] for l in sin), f"lugares de 1 S sin coordenadas con nota ({len(sin)})")
    pas = [p for p in datos["pasajes"] if p["libro"] == LIBRO]
    ok_(len(pas) == len(PASAJES) and pas[0]["inicio"] == "1S 1:1" and pas[-1]["fin"] == "1S 31:13" and pas[0]["id"] == "1s-01",
        f"{len(pas)} pasajes 1s-NN de 1S 1:1 a 1S 31:13")
    ok_(len({p["seccion"] for p in pas}) == 9, "9 secciones")
    ids = [p["id"] for p in datos["pasajes"]]
    ult_rut = max(i for i, p in enumerate(datos["pasajes"]) if p["libro"] == "Rut")
    lb = [l["id"] for l in datos["libros"]]
    ok_(ids.index(pas[0]["id"]) == ult_rut + 1 and lb.index(LIBRO) == lb.index("Rut") + 1,
        "1 Samuel va justo después de Rut en el orden de los pasajes (lectura en orden)")
    return lineas
