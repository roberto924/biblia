"""Jueces 1–21: personas, relaciones, pasajes, menciones y lugares (lo usa construir_datos.py).

Reutiliza la lógica de exodo.py (exodo.construir / exodo.construir_lugares con este módulo como configuración) y la
detección automática de lugares de josue.py (josue.lugares_auto con este módulo como cfg), igual que Josué. Cada dato
lleva versículo, fuente y certeza; las citas se comprueban literalmente contra la RV1909 (TM) o Brenton (LXX). Las
personas de Génesis–Josué (Caleb, Otoniel, Quenaz, Acsa, Finees, Josué…) son la misma persona (mismo id de BibleData):
se amplían sus `refs`.

Versificación (comprobada al generar): la RV1909 de eBible tiene 618 versículos con los mismos recuentos por capítulo
que la numeración inglesa, la hebrea y Brenton (tvtms.txt: en Jueces solo la Vulgata difiere, en 5:31-32 y
21:24-25). Una diferencia interna: la RV1909 parte el 14:18 inglés/hebreo en dos (14:18 la pregunta de los de la
ciudad, 14:19 la respuesta de Sansón) y une 14:19-20 en su 14:20. BibleData y OpenBible usan la numeración inglesa:
`REMAP_REF` lleva su 14:19 al 14:20 de la RV1909 (único punto). Brenton se usa solo como testigo de las cifras de
tiempo (Jue 3–16), que dice en los mismos versículos que la RV1909 (se comprueba en cronologia.py).

Solo biblioteca estándar.
"""
import sys

import exodo
import josue

LIBRO = "Jue"
NOMBRE = "Jueces"
USX = "JDG"
CAPITULOS = 21
VERSICULOS = 618
POR_CAPITULO = [36, 23, 31, 24, 31, 40, 25, 35, 57, 18, 40, 15, 25, 20, 20, 31, 13, 31, 30, 48, 25]
# Comienzo de los versículos donde la RV1909 difiere de la numeración inglesa/hebrea (se comprueba).
VERSIFICACION = [((14, 18), "Y al séptimo día, antes que el sol se pusiese"), ((14, 19), "Y él les respondió: Si no araseis"),
                 ((14, 20), "Y el espíritu de Jehová cayó sobre él, y descendió á Ascalón"),
                 ((5, 31), "Así perezcan todos tus enemigos"), ((21, 25), "En estos días no había rey en Israel")]
VERSIFICACION_LXX = [((14, 18), "If ye had not ploughed with my heifer"), ((14, 19), "he went down to Ascalon"),
                     ((14, 20), "the wife of Sampson was [given] to one of his friends")]


def REMAP_REF(r):
    """Numeración inglesa (BibleData, OpenBible) -> RV1909. Único punto: Jue 14:19 inglés = parte de RV 14:20."""
    return (14, 20) if r == (14, 19) else r


# Personas de BibleData que no se crean: Dios, «NA», el ángel de Jehová (como en Números), los reyes sin nombre de
# Ammón y Edom (como en Números y Josué), Ammón y Amalec (son los pueblos: «los hijos de Ammón», «Amalec»).
EXCLUIR = {"YHVH_1", "NA", "the angel of the LORD_1", "King of the sons of Ammon_1", "King of Edom_1",
           "Ben-ammi_1", "Amalek_1"}
# «Israel» es el pueblo (como en Josué): Jacob solo si el texto dice «Jacob».
SOLO_ETIQUETA = {"Jacob_1": {"Jacob"}}
FORMA_NO_MENCION = {("Jacob_1", "israel")}
_JABIN = "Jue 4 es otro rey de Hazor: Jos 11:10 dice que Josué hirió á cuchillo al rey de Hasor (el Jabín de Jos 11:1)."
_SUEGRO = ("el texto no lo nombra (Jue 1:16 «Cineo, suegro de Moisés») o nombra a Hobab (Jue 4:11); no se identifica "
           "con Jetro/Ragüel.")
PV_DESCARTAR = {
    **{("Jabin_1", r): _JABIN for r in ((4, 2), (4, 7), (4, 17), (4, 23), (4, 24))},
    ("Reuel_2", (1, 16)): "Jetro/Ragüel en Jue 1:16: " + _SUEGRO,
    ("Reuel_2", (4, 11)): "Jetro/Ragüel en Jue 4:11: " + _SUEGRO,
    ("Balak_1", (11, 17)): "Jue 11:17 habla de «el rey de Moab» sin nombre (Balac se nombra en 11:25).",
}
REL_DESCARTAR = {
    ("Gershom_2", "Manasseh_2", "padre"): "BibleData invierte la relación; Jue 18:30 dice «Gersón, hijo de Manasés».",
}
JABIN = "Jabin_Jue4"  # id propio: BibleData usa Jabin_1 para el de Jos 11 y el de Jue 4
FORMAS_FORZADAS = {"Ehud_1": ["Aod"], "Purah_1": ["Phara"], JABIN: ["Jabín"], "Gideon_1": ["Gedeón", "Jerobaal"],
                   "Anath_1": ["Anat", "Anath"], "Hamor_1": ["Hemor"], "Zippor_1": ["Sephor"], "Ahiman_1": ["Ahiman"],
                   "Delilah_1": ["Dalila"], "Joash_1": ["Joas"]}
MODERNO = {
    "Adoni-bezek_1": "Adoni-bezec", "Cushan-rishathaim_1": "Cusán-risataim", "Eglon_1": "Eglón", "Ehud_1": "Aod",
    "Gera_2": "Gera", "Shamgar_1": "Samgar", "Anath_1": "Anat", "Sisera_1": "Sísara", "Deborah_2": "Débora",
    "Lappidoth_1": "Lapidot", "Barak_1": "Barac", "Abinoam_1": "Abinoam", "Heber_2": "Heber", "Jael_1": "Jael",
    "Joash_1": "Joás", "Gideon_1": "Gedeón", "Purah_1": "Fura", "Oreb_1": "Oreb", "Zeeb_1": "Zeeb", "Zebah_1": "Zeba",
    "Zalmunna_1": "Zalmuna", "Jether_1": "Jeter", "Abimelech_2": "Abimelec", "Jotham_1": "Jotam", "Gaal_1": "Gaal",
    "Ebed_1": "Ebed", "Zebul_1": "Zebul", "Tola_2": "Tola", "Puah_2": "Fúa", "Dodo_1": "Dodo", "Jair_2": "Jair",
    "Jephthah_1": "Jefté", "Gilead_2": "Galaad", "Ibzan_1": "Ibzán", "Elon_3": "Elón", "Abdon_1": "Abdón",
    "Hillel_1": "Hilel", "Manoah_1": "Manoa", "Samson_1": "Sansón", "Delilah_1": "Dalila", "Micah_1": "Micaía",
    "Jonathan_1": "Jonatán", "Gershom_2": "Gersón", "Manasseh_2": "Manasés", JABIN: "Jabín",
}
NOTAS = {
    JABIN: ("Jue 4:2: «Jabín rey de Canaán, el cual reinó en Asor». BibleData lo identifica con el Jabín de Jos 11:1, "
            "pero Jos 11:10 dice que Josué tomó Hasor «é hirió á cuchillo á su rey»: se registra como otra persona "
            "(el texto no dice que sea pariente del primero)."),
    "Deborah_2": "Profetisa que gobierna a Israel (Jue 4:4). Distinta de Débora, la nodriza de Rebeca (Gn 35:8).",
    "Abimelech_2": ("Hijo de Gedeón y de su concubina de Siquem (Jue 8:31); distinto de Abimelec rey de Gerar (Gn 20). "
                    "Muere en Tebes herido por una muela que le arroja una mujer (Jue 9:53-54)."),
    "Jair_2": "Juez galaadita (Jue 10:3). Distinto de Jair hijo de Manasés (Nm 32:41), aunque sus villas se llaman igual (Jue 10:4).",
    "Elon_3": "Juez zabulonita (Jue 12:11). Distinto de Elón heteo (Gn 26:34) y de Elón hijo de Zabulón (Gn 46:14).",
    "Gera_2": "Padre de Aod, benjamita (Jue 3:15). Distinto de Gera hijo de Benjamín (Gn 46:21).",
    "Heber_2": "Ceneo, marido de Jael (Jue 4:11, 4:17). Distinto de Heber hijo de Bería (Gn 46:17).",
    "Gilead_2": "Padre de Jefté (Jue 11:1). Distinto de Galaad hijo de Maquir (Nm 26:29).",
    "Manasseh_2": ("Jue 18:30: «Jonathán, hijo de Gersón, hijo de Manasés». Distinto de Manasés hijo de José (Gn 41:51), "
                   "según BibleData."),
    "Gershom_2": "Jue 18:30: padre del sacerdote Jonatán. Distinto de Gersón hijo de Moisés (Ex 2:22), según BibleData.",
    "Jonathan_1": ("Sacerdote de los danitas en Dan (Jue 18:30). BibleData solo lo sitúa en 18:30; el joven levita de "
                   "Jue 17–18 no se nombra antes."),
    "Ehud_1": "Jue 3:15: «Aod, hijo de Gera, Benjamita, el cual tenía cerrada la mano derecha».",
    "Shamgar_1": "Jue 3:31: hiere a seiscientos filisteos «con una aguijada de bueyes».",
    "Purah_1": "Criado de Gedeón; baja con él al campamento de Madián (Jue 7:10-11).",
    "Samson_1": "Juzga a Israel veinte años (Jue 15:20; 16:31); muere en Gaza con los filisteos (Jue 16:30).",
    "Micah_1": "Hombre del monte de Efraín que se hace un ídolo y toma un levita por sacerdote (Jue 17:1-13).",
    "Jephthah_1": "Jue 11:1: «Jephté, Galaadita, hombre valiente, hijo de una ramera». Juzga seis años (Jue 12:7).",
}
IDENTIDAD = {
    "Gideon_1": {"certeza": "texto", "refs": ["Jue 6:32", "Jue 7:1"], "nombres_rv1909": ["Gedeón", "Jerobaal"],
                 "fuente": "rv1909",
                 "nota": "Jue 6:32: «llamó [él] á Gedeón Jerobaal»; Jue 7:1: «Jerobaal, el cual es Gedeón»."},
}
NOTAS_VERIFICAR = [
    ("TM", (4, 2), "Jabín rey de Canaán, el cual reinó en Asor"), ("TM", (4, 4), "Débora, profetisa"),
    ("TM", (8, 31), "su concubina que estaba en Sichêm"), ("TM", (9, 53), "una mujer dejó caer un pedazo de una rueda de molino"),
    ("TM", (10, 3), "Jair, Galaadita"), ("TM", (10, 4), "las villas de Jair"), ("TM", (12, 11), "Elón, Zabulonita"),
    ("TM", (3, 15), "Aod, hijo de Gera, Benjamita, el cual tenía cerrada la mano derecha"),
    ("TM", (4, 11), "Heber Cineo"), ("TM", (4, 17), "Jael mujer de Heber Cineo"),
    ("TM", (11, 1), "al cual había engendrado Galaad"), ("TM", (18, 30), "Jonathán, hijo de Gersón, hijo de Manasés"),
    ("TM", (3, 31), "con una aguijada de bueyes"), ("TM", (7, 10), "Phara tu criado"), ("TM", (15, 20), "veinte años"),
    ("TM", (16, 31), "juzgó á Israel veinte años"), ("TM", (17, 1), "monte de Ephraim, que se llamaba Michâs"),
    ("TM", (11, 1), "Jephté, Galaadita, hombre valiente, hijo de una ramera"), ("TM", (12, 7), "Jephté juzgó á Israel seis años"),
    ("TM", (6, 32), "llamó [él] á Gedeón Jerobaal"), ("TM", (7, 1), "Jerobaal, el cual es Gedeón"),
    ("TM", (2, 8), "Josué hijo de Nun, siervo de Jehová, siendo de ciento y diez años"), ("TM", (2, 9), "Timnath-sera"),
    ("TM", (1, 13), "Othoniel hijo de Cenez, hermano menor de Caleb"), ("TM", (3, 9), "Othoniel hijo de Cenez, hermano menor de Caleb"),
    ("TM", (3, 11), "reposó la tierra cuarenta años; y murió Othoniel"), ("TM", (1, 20), "tres hijos de Anac"),
    ("TM", (20, 28), "Phinees, hijo de Eleazar, hijo de Aarón, se presentaba delante de ella"),
    ("TM", (4, 11), "Hobab suegro de Moisés"), ("TM", (1, 16), "Cineo, suegro de Moisés"),
    ("TM", (1, 10), "hirieron á Sesai, y á Ahiman, y á Talmai"),
]
ROLES = {
    "Adoni-bezek_1": ("rey cananeo vencido por Judá en Bezec", (1, 5), "hallaron á Adoni-bezec en Bezec"),
    "Cushan-rishathaim_1": ("rey de Mesopotamia que oprime a Israel", (3, 8), "Chusan-risathaim, rey de Mesopotamia"),
    "Eglon_1": ("rey de Moab que oprime a Israel", (3, 12), "Eglón rey de Moab"),
    "Ehud_1": ("juez benjamita que mata a Eglón", (3, 15), "Aod, hijo de Gera, Benjamita"),
    "Shamgar_1": ("salva a Israel de los filisteos", (3, 31), "él también salvó á Israel"),
    JABIN: ("rey de Canaán que reina en Hazor", (4, 2), "Jabín rey de Canaán, el cual reinó en Asor"),
    "Sisera_1": ("capitán del ejército de Jabín", (4, 2), "el capitán de su ejército [se llamaba] Sísara"),
    "Deborah_2": ("profetisa que gobierna a Israel", (4, 4), "Débora, profetisa"),
    "Barak_1": ("capitán contra Sísara", (4, 6), "Barac hijo de Abinoam"),
    "Jael_1": ("mata a Sísara en su tienda", (4, 21), "Jael, mujer de Heber"),
    "Gideon_1": ("juez que libra a Israel de Madián", (6, 11), "su hijo Gedeón"),
    "Purah_1": ("criado de Gedeón", (7, 10), "Phara tu criado"),
    "Oreb_1": ("príncipe de Madián", (7, 25), "dos príncipes de los Madianitas, Oreb y Zeeb"),
    "Zeeb_1": ("príncipe de Madián", (7, 25), "dos príncipes de los Madianitas, Oreb y Zeeb"),
    "Zebah_1": ("rey de Madián", (8, 5), "Zeba y á Zalmunna, reyes de Madián"),
    "Zalmunna_1": ("rey de Madián", (8, 5), "Zeba y á Zalmunna, reyes de Madián"),
    "Abimelech_2": ("hijo de Gedeón, rey en Siquem", (9, 6), "eligieron á Abimelech por rey"),
    "Gaal_1": ("se rebela contra Abimelec en Siquem", (9, 26), "Gaal hijo de Ebed"),
    "Zebul_1": ("gobernador de Siquem por Abimelec", (9, 30), "Zebul asistente de la ciudad"),
    "Tola_2": ("juez de Israel veintitrés años", (10, 2), "juzgó á Israel veintitrés años"),
    "Jair_2": ("juez galaadita, veintidós años", (10, 3), "Jair, Galaadita, el cual juzgó á Israel veintidós años"),
    "Jephthah_1": ("juez galaadita que vence a Ammón", (11, 1), "Jephté, Galaadita"),
    "Ibzan_1": ("juez de Belén, siete años", (12, 8), "juzgó á Israel Ibzan de Beth-lehem"),
    "Elon_3": ("juez zabulonita, diez años", (12, 11), "Elón, Zabulonita, el cual juzgó á Israel diez años"),
    "Abdon_1": ("juez piratonita, ocho años", (12, 13), "Abdón hijo de Hillel, Piratonita"),
    "Manoah_1": ("padre de Sansón, de Zora, de la tribu de Dan", (13, 2), "el cual se llamaba Manoa"),
    "Samson_1": ("juez de Israel veinte años", (15, 20), "juzgó á Israel en días de los Filisteos veinte años"),
    "Delilah_1": ("mujer del valle de Sorec a quien ama Sansón", (16, 4), "la cual se llamaba Dalila"),
    "Micah_1": ("efraimita que se hace un ídolo y un sacerdote", (17, 1), "que se llamaba Michâs"),
    "Jonathan_1": ("sacerdote de los danitas", (18, 30), "él y sus hijos fueron sacerdotes en la tribu de Dan"),
}
SIN_NOMBRE = {
    "Mujer_de_Manoa": ("Mujer de Manoa, madre de Sansón", "f",
                       "El texto no da su nombre: era estéril (Jue 13:2) y el ángel de Jehová le anuncia un hijo (Jue 13:3).",
                       [("Manoah_1", "Mujer_de_Manoa", "conyuge", (13, 2), "explicito", "su mujer era estéril"),
                        ("Mujer_de_Manoa", "Samson_1", "madre", (13, 24), "explicito", "la mujer parió un hijo")]),
    "Hija_de_Jefte": ("Hija de Jefté", "f",
                      "El texto no da su nombre; era su única hija (Jue 11:34) y la alcanza el voto de su padre (Jue 11:30-40).",
                      [("Jephthah_1", "Hija_de_Jefte", "padre", (11, 34), "explicito", "su hija le salió á recibir")]),
}
RELACIONES = [
    ("Gera_2", "Ehud_1", "padre", (3, 15), "Aod, hijo de Gera", ""),
    ("Anath_1", "Shamgar_1", "padre", (3, 31), "Samgar hijo de Anat", "Jue 5:6: «Samgar hijo de Anath»."),
    ("Deborah_2", "Lappidoth_1", "conyuge", (4, 4), "Débora, profetisa, mujer de Lapidoth", ""),
    ("Abinoam_1", "Barak_1", "padre", (4, 6), "Barac hijo de Abinoam", ""),
    ("Heber_2", "Jael_1", "conyuge", (4, 17), "Jael mujer de Heber Cineo", ""),
    ("Joash_1", "Gideon_1", "padre", (6, 11), "Joas Abiezerita; y su hijo Gedeón", "Jue 8:29: «Jerobaal hijo de Joas»."),
    ("Gideon_1", "Jether_1", "padre", (8, 20), "dijo á Jether su primogénito", ""),
    ("Gideon_1", "Abimelech_2", "padre", (8, 31), "su concubina que estaba en Sichêm, también le parió un hijo; y púsole por nombre Abimelech",
     "Jue 9:1: «Abimelech hijo de Jerobaal» (Jerobaal = Gedeón, Jue 6:32; 7:1). La madre, concubina de Siquem, no tiene nombre."),
    ("Gideon_1", "Jotham_1", "padre", (9, 5), "Jotham, el más pequeño hijo de Jerobaal", ""),
    ("Ebed_1", "Gaal_1", "padre", (9, 26), "Gaal hijo de Ebed", ""),
    ("Puah_2", "Tola_2", "padre", (10, 1), "Tola hijo de Púa", ""),
    ("Dodo_1", "Puah_2", "padre", (10, 1), "Púa, hijo de Dodo", ""),
    ("Gilead_2", "Jephthah_1", "padre", (11, 1), "al cual había engendrado Galaad",
     "Jue 11:1: «hijo de una ramera»; su madre no tiene nombre."),
    ("Hillel_1", "Abdon_1", "padre", (12, 13), "Abdón hijo de Hillel", ""),
    ("Manoah_1", "Samson_1", "padre", (16, 31), "el sepulcro de su padre Manoa",
     "Jue 13:2 y 13:24: la mujer de Manoa pare a Sansón."),
    ("Gershom_2", "Jonathan_1", "padre", (18, 30), "Jonathán, hijo de Gersón", ""),
    ("Manasseh_2", "Gershom_2", "padre", (18, 30), "Gersón, hijo de Manasés", ""),
]
NOTAS_REL = {}
# Relaciones de los libros anteriores que Jueces repite: se añade la referencia a la nota.
REPITE_GN = [
    ("Nun_1", "Joshua_1", "padre", (2, 8), "Josué hijo de Nun"),
    ("Caleb_1", "Achsah_1", "padre", (1, 12), "Axa mi hija"),
    ("Kenaz_2", "Othniel_1", "padre", (1, 13), "Othoniel hijo de Cenez"),
    ("Kenaz_2", "Othniel_1", "padre", (3, 9), "Othoniel hijo de Cenez"),
    ("Achsah_1", "Othniel_1", "conyuge", (1, 13), "él le dió á Axa su hija por mujer"),
    ("Eleazar_1", "Phinehas_1", "padre", (20, 28), "Phinees, hijo de Eleazar"),
    ("Aaron_1", "Eleazar_1", "padre", (20, 28), "Eleazar, hijo de Aarón"),
    ("Zippor_1", "Balak_1", "padre", (11, 25), "Balac hijo de Sephor"),
    ("Hamor_1", "Shechem_1", "padre", (9, 28), "Hemor padre de Sichêm"),
]
EDADES = []
NOTAS_EXISTENTES = {
    "Joshua_1": "Jue 2:8-9 repite su muerte «siendo de ciento y diez años» y su sepultura en Timnath-sera.",
    "Othniel_1": ("Primer juez: Jue 1:13 y 3:9 repiten «Othoniel hijo de Cenez, hermano menor de Caleb»; libra a Israel "
                  "de Cusán-risataim y «reposó la tierra cuarenta años; y murió Othoniel» (Jue 3:11)."),
    "Phinehas_1": ("Jue 20:28: «Phinees, hijo de Eleazar, hijo de Aarón, se presentaba delante de ella» (el arca) durante "
                   "la guerra contra Benjamín."),
    "Caleb_1": "Jue 1:20: le dan Hebrón y echa de allí «tres hijos de Anac».",
    "Hobab_1": ("Jue 4:11: Heber ceneo era «de los hijos de Hobab suegro de Moisés»: aquí la RV1909 llama suegro de "
                "Moisés a Hobab, a quien Nm 10:29 hace hijo de Ragüel. Jue 1:16 dice solo «Cineo, suegro de Moisés». No se "
                "une a Jetro/Ragüel: el texto no lo resuelve."),
}
# Refs que el texto da a una persona y BibleData no sitúa.
REFS_EXTRA = {"Sheshai_1": [(1, 10)], "Ahiman_1": [(1, 10)], "Talmai_1": [(1, 10)], "Hobab_1": [(4, 11)],
              "Dan_1": [(18, 29)], JABIN: [(4, 2), (4, 7), (4, 17), (4, 23), (4, 24)]}
REFS_QUITAR = {}

S1 = "Conquista incompleta y el ciclo de los jueces (Jue 1:1–3:6)"
S2 = "Otoniel, Aod y Samgar (Jue 3:7-31)"
S3 = "Débora y Barac (Jue 4–5)"
S4 = "Gedeón (Jue 6–8)"
S5 = "Abimelec (Jue 9)"
S6 = "Tola, Jair, Jefté, Ibzán, Elón y Abdón (Jue 10–12)"
S7 = "Sansón (Jue 13–16)"
S8 = "Micaía y los danitas (Jue 17–18)"
S9 = "El levita de Efraín y la guerra contra Benjamín (Jue 19–21)"
PASAJES = [
    ("1:1", "1:15", "Judá sube primero", "Muerto Josué, Judá y Simeón vencen a Adoni-bezec; Otoniel toma Debir y recibe a Acsa.", S1),
    ("1:16", "1:26", "Los ceneos; la casa de José toma Bet-el", "Los ceneos suben con Judá; Judá toma Gaza, Ascalón y Ecrón; la casa de José toma Bet-el, antes Luz.", S1),
    ("1:27", "1:36", "Las ciudades que no conquistaron", "Manasés, Efraín, Zabulón, Aser, Neftalí y Dan no echan a los cananeos; los hacen tributarios.", S1),
    ("2:1", "2:10", "Boquim y muerte de Josué", "El ángel de Jehová reprende a Israel en Boquim; muere Josué y se levanta una generación que no conocía a Jehová.", S1),
    ("2:11", "3:6", "El ciclo de los jueces", "Israel sirve a los baales, Dios los entrega y levanta jueces que los libran; las naciones que quedan son para probar a Israel.", S1),
    ("3:7", "3:11", "Otoniel", "Israel sirve ocho años a Cusán-risataim; Otoniel lo libra y la tierra reposa cuarenta años.", S2),
    ("3:12", "3:23", "Aod mata a Eglón", "Aod, benjamita zurdo, lleva un presente a Eglón rey de Moab y lo mata con un puñal de dos filos.", S2),
    ("3:24", "3:31", "Moab sometido; Samgar", "Aod escapa y reúne a Israel en el monte de Efraín; la tierra reposa ochenta años; Samgar hiere a seiscientos filisteos.", S2),
    ("4:1", "4:10", "Débora llama a Barac", "Jabín oprime a Israel veinte años; la profetisa Débora manda a Barac juntar gente en el monte Tabor.", S3),
    ("4:11", "4:24", "Sísara en la tienda de Jael", "Sísara huye a pie tras la derrota junto al Cisón; Jael, mujer de Heber ceneo, lo mata en su tienda.", S3),
    ("5:1", "5:18", "El cántico de Débora: las tribus", "Débora y Barac cantan la victoria; alaban a las tribus que acudieron y reprochan a las que no.", S3),
    ("5:19", "5:31", "El cántico: Sísara y su madre", "Los reyes pelean en Taanac; el Cisón los arrastra; bendita Jael; la madre de Sísara espera en vano. La tierra reposa cuarenta años.", S3),
    ("6:1", "6:10", "Madián oprime a Israel", "Siete años los madianitas destruyen las cosechas; un profeta recuerda a Israel la salida de Egipto.", S4),
    ("6:11", "6:24", "El ángel llama a Gedeón", "El ángel de Jehová se aparece a Gedeón en Ofra; el fuego consume su ofrenda y él edifica un altar.", S4),
    ("6:25", "6:32", "Gedeón derriba el altar de Baal", "De noche Gedeón derriba el altar de Baal de su padre; Joás lo defiende y lo llama Jerobaal.", S4),
    ("6:33", "6:40", "El vellón", "Madián acampa en Jezreel; Gedeón convoca a las tribus y pide la señal del vellón dos veces.", S4),
    ("7:1", "7:8", "Los trescientos", "Dios reduce el ejército: vuelven los que temen y quedan los trescientos que lamen el agua.", S4),
    ("7:9", "7:15", "El sueño del pan de cebada", "Gedeón baja de noche con Fura al campamento y oye contar el sueño de un pan de cebada que derriba una tienda.", S4),
    ("7:16", "7:25", "Bocinas, cántaros y teas", "Los trescientos tocan las bocinas y quiebran los cántaros; Madián huye; Efraín toma a Oreb y Zeeb.", S4),
    ("8:1", "8:12", "Sucot, Penuel y los reyes de Madián", "Gedeón aplaca a Efraín; Sucot y Penuel le niegan pan; captura a Zeba y Zalmuna.", S4),
    ("8:13", "8:21", "Gedeón castiga a Sucot y Penuel", "Gedeón castiga a los de Sucot, derriba la torre de Penuel y mata a Zeba y Zalmuna.", S4),
    ("8:22", "8:35", "El efod de Gedeón y su muerte", "Gedeón no quiere ser rey; hace un efod que es tropiezo para Israel; muere y el pueblo vuelve a los baales.", S4),
    ("9:1", "9:6", "Abimelec rey en Siquem", "Abimelec, hijo de Jerobaal, mata a sus setenta hermanos y los de Siquem lo hacen rey; Jotam escapa.", S5),
    ("9:7", "9:21", "La fábula de Jotam", "Desde el monte Gerizim Jotam cuenta la fábula de los árboles que buscan rey y la zarza.", S5),
    ("9:22", "9:41", "Gaal se rebela", "Dios pone discordia entre Abimelec y Siquem; Gaal se rebela y Zebul avisa a Abimelec, que lo vence.", S5),
    ("9:42", "9:57", "Siquem destruida; muerte de Abimelec", "Abimelec destruye Siquem y quema su torre; en Tebes una mujer le arroja una muela y muere.", S5),
    ("10:1", "10:5", "Tola y Jair", "Tola juzga a Israel veintitrés años y Jair galaadita veintidós.", S6),
    ("10:6", "10:18", "Ammón oprime a Israel", "Israel sirve a dioses ajenos; los filisteos y Ammón lo oprimen dieciocho años; Israel clama y quita los dioses ajenos.", S6),
    ("11:1", "11:11", "Jefté, capitán de Galaad", "Jefté, echado por sus hermanos, vive en Tob; los ancianos de Galaad lo llaman como cabeza.", S6),
    ("11:12", "11:28", "Jefté responde al rey de Ammón", "Jefté envía embajadores y repasa cómo Israel tomó la tierra de Sehón; el rey de Ammón no escucha.", S6),
    ("11:29", "11:40", "El voto de Jefté", "Jefté hace un voto, vence a Ammón y su única hija sale a recibirlo; ella llora dos meses en los montes.", S6),
    ("12:1", "12:7", "Efraín y Shiboleth", "Efraín se enfrenta a Jefté; los galaaditas toman los vados del Jordán y prueban a cada uno con «Shiboleth».", S6),
    ("12:8", "12:15", "Ibzán, Elón y Abdón", "Ibzán de Belén juzga siete años, Elón zabulonita diez y Abdón piratonita ocho.", S6),
    ("13:1", "13:14", "El ángel anuncia a Sansón", "Cuarenta años en manos de los filisteos; el ángel anuncia a la mujer de Manoa que tendrá un hijo nazareo.", S7),
    ("13:15", "13:25", "Manoa y el ángel; nace Sansón", "El ángel sube en la llama del altar; nace Sansón y el espíritu de Jehová comienza a moverlo.", S7),
    ("14:1", "14:9", "El león de Timnat", "Sansón quiere una mujer filistea de Timnat; despedaza un león y luego halla miel en su cuerpo.", S7),
    ("14:10", "14:20", "El enigma", "En el banquete propone un enigma; su mujer lo descubre a los filisteos; Sansón mata a treinta en Ascalón.", S7),
    ("15:1", "15:8", "Las zorras y los campos de los filisteos", "A Sansón le niegan a su mujer; suelta trescientas zorras con teas en los sembrados de los filisteos.", S7),
    ("15:9", "15:20", "La quijada de asno", "Judá entrega atado a Sansón; en Lehi rompe las cuerdas y mata a mil con una quijada; Dios le da agua en En-hacore.", S7),
    ("16:1", "16:14", "Gaza; Dalila", "Sansón arranca las puertas de Gaza; Dalila, pagada por los filisteos, intenta tres veces saber de dónde viene su fuerza.", S7),
    ("16:15", "16:22", "Dalila descubre el secreto", "Sansón le revela que es nazareo; le rapan el cabello, lo prenden, le sacan los ojos y muele en la cárcel de Gaza.", S7),
    ("16:23", "16:31", "Muerte de Sansón", "En la fiesta de Dagón Sansón derriba las columnas y muere con los filisteos; lo entierran sus hermanos.", S7),
    ("17:1", "17:13", "El ídolo y el levita de Micaía", "Micaía devuelve la plata a su madre, hace imagen y efod y toma por sacerdote a un joven levita de Belén.", S8),
    ("18:1", "18:13", "Los danitas exploran Lais", "Dan busca heredad; cinco exploradores pasan por casa de Micaía y hallan a Lais confiada.", S8),
    ("18:14", "18:26", "Los danitas se llevan los dioses de Micaía", "Seiscientos danitas toman la imagen, el efod y al levita; Micaía no puede impedirlo.", S8),
    ("18:27", "18:31", "Lais, ahora Dan", "Los danitas queman Lais, la reedifican y la llaman Dan; Jonatán y sus hijos son sus sacerdotes.", S8),
    ("19:1", "19:15", "El levita y su concubina", "Un levita del monte de Efraín va a Belén a buscar a su concubina; al volver se detienen de noche en Gabaa.", S9),
    ("19:16", "19:30", "El crimen de Gabaa", "Un anciano los hospeda; los hombres de Gabaa rodean la casa y abusan de la concubina, que muere; el levita la parte en doce pedazos.", S9),
    ("20:1", "20:17", "Israel se junta en Mizpa", "Las tribus se reúnen en Mizpa, oyen al levita y piden a Benjamín los culpables; Benjamín se niega.", S9),
    ("20:18", "20:28", "Dos derrotas ante Gabaa", "Israel consulta a Dios y es vencido dos días; Finees pregunta ante el arca y Dios promete la victoria.", S9),
    ("20:29", "20:48", "La emboscada y la derrota de Benjamín", "Una emboscada toma Gabaa; Benjamín es vencido y solo seiscientos huyen a la peña de Rimón.", S9),
    ("21:1", "21:14", "Mujeres de Jabes de Galaad", "Israel se duele por Benjamín; destruye Jabes de Galaad, que no subió a Mizpa, y da sus doncellas a los benjamitas.", S9),
    ("21:15", "21:25", "Las hijas de Silo", "Los benjamitas que faltan toman mujeres de las hijas de Silo en la fiesta. «No había rey en Israel».", S9),
]
# Citas de los resúmenes que van entre comillas (se comprueban).
CITAS_RESUMEN = [((12, 6), "Shiboleth"), ((21, 25), "no había rey en Israel")]

# ---------------------------------------------------------------- lugares
# Lugares configurados a mano: obid -> (id, nombre, formas RV1909, tipo, nota, forzar baja). Para los ya registrados
# solo aportan formas.
LUGARES_MANUAL = {
    "a513646": ("dan", "Dan", ["Dan", "Lais"], "ciudad", "", False),
    "a159fa4": ("siria", "Siria", ["Siria"], "region", "Jue 10:6: «los dioses de Siria» (hebreo Aram).", False),
    "a53f299": ("bet-milo", "Bet-milo", ["Millo"], "otro",
                "La RV1909 dice «la casa de Millo» (Jue 9:6, 9:20); OpenBible la toma por una construcción de Siquem.", False),
    "a0dc90b": ("encina-de-meonenim", "Encina de Meonenim", ["Meonenim"], "otro",
                "La RV1909 dice «la campiña de Meonenim» (Jue 9:37).", False),
    "aeea26d": ("monte-heres", "Monte Heres", ["Heres"], "monte", "Jue 1:35: «el monte de Heres».", False),
    "ac8955e": ("monte-baal-hermon", "Monte Baal-hermón", ["Baal-hermón"], "monte", "", False),
    "ac54760": ("monte-libano", "Monte Líbano", ["Líbano"], "monte", "Jue 3:3: «el monte Líbano».", False),
    "a954735": ("monte-galaad", "Monte Galaad", ["Galaad"], "monte", "Jue 7:3: «el monte de Galaad».", False),
    "a884255": ("monte-salmon", "Monte Salmón", ["Salmón"], "monte", "Allí corta Abimelec la rama (Jue 9:48).", False),
    "a48191b": ("cedes-4-6", "Cedes de Neftalí (Jue 4:6)", ["Cedes"], "ciudad",
                "Patria de Barac. OpenBible la identifica con Khirbet Qedish, junto al mar de Galilea, no con la Cedes de "
                "refugio (Tel Kedesh, Jos 20:7); el texto dice «Cedes de Nephtalí» en ambos casos.", False),
    "a339971": ("valle-de-sorec", "Valle de Sorec", ["Sorec"], "otro", "Allí vive Dalila (Jue 16:4).", False),
}
PRECEDIDO = {"aeea26d": "monte de ", "ac8955e": "monte de ", "ac54760": "monte ", "a954735": "monte de ",
             "a884255": "monte de ", "a53f299": "casa de ", "a339971": "valle de "}
EXCLUIR_LUGAR = {
    "a957c5b": "Abel-keramim (Jue 11:33): la RV1909 traduce «la vega de las viñas».",
    "ab0b2dd": "«El oriente» (Jue 6:3…): la RV1909 dice «los orientales» (gentilicio).",
    "a2466e4": "Heres (Jue 8:13): la RV1909 traduce «antes que el sol subiese».",
    "ab3fd96": "Mahané-dan (Jue 13:25): la RV1909 traduce «los campamentos de Dan».",
    "a67325d": "Mahané-dan (Jue 18:12): la RV1909 traduce «el campo de Dan».",
    "a5e9c87": "Maare-geba (Jue 20:33): la RV1909 traduce «el prado de Gabaa».",
    "ab4d194": "Noha (Jue 20:43): la RV1909 lee «Menuchâ»; no se identifica sin más.",
    "a98b02e": "Sela (Jue 1:36): la RV1909 traduce «la piedra».",
    "a5948b2": "Tabur-erez (Jue 9:37): la RV1909 traduce «por medio de la tierra».",
    "a939939": "Torre de Siquem (Jue 9:46-49): la RV1909 dice «la torre de Sichêm», parte de Siquem.",
    "ab49753": "Zafón (Jue 12:1): la RV1909 traduce «hacia el aquilón».",
    "a529e92": "Ciudad de las palmas (Jue 3:13): la RV1909 no nombra la ciudad.",
    "ac4ff01": "Ciudad de las palmas (Jue 1:16): la RV1909 no nombra la ciudad.",
    "a1cb244": "Néguev: la RV1909 traduce «el mediodía»; no es nombre propio.",
    "af084cf": "Sefela: la RV1909 traduce «los llanos»; no es nombre propio.",
    "aaa3eca": "Gulot-maim (Jue 1:15): la RV1909 traduce «las fuentes de las aguas».",
    "aacc081": "Gulot de abajo (Jue 1:15): la RV1909 traduce «las de abajo».",
    "a380434": "Gulot de arriba (Jue 1:15): la RV1909 traduce «las fuentes de arriba».",
    "a549c0f": "Abiezer (Jue 8:2): es el clan («la vendimia de Abiezer»); ya se marca la persona Abiezer (Iezer_1).",
}
# Mizpa de Benjamín (Jue 20–21): OpenBible la separa de «Mizpeh 1» (Jos 18:26) con la misma identificación (Tell en-Nasbeh).
UNIR_LUGAR_MANUAL = {"a736f6c": "mizpa-18-26"}
UNIR_LUGAR = {}
NOMBRE_LUGAR = {"Asor": "Hazor", "Hasor": "Hazor", "Jerusalem": "Jerusalén", "Beer-seba": "Beerseba", "Beth-lehem": "Belén",
                "Ascalón": "Ascalón", "Thebes": "Tebes", "Cisón": "Cisón", "Haroseth": "Haroset-goim", "Lehi": "Lehi",
                "Ophra": "Ofra", "Gabaa": "Gabaa", "Achô": "Aco", "Chîtron": "Quitrón", "Sephath": "Sefat",
                "En-haccore": "En-hacore", "Jabes-galaad": "Jabes de Galaad", "Cerera": "Zerera", "Seirath": "Seirat",
                "Bochîm": "Boquim", "Carcor": "Carcor", "Ramath-lehi": "Ramat-lehi", "Tob": "Tob"}
NOMBRE_OB = {
    "abd637f": ("Ofra de Abiezer", "Ciudad de Joás abiezerita, padre de Gedeón (Jue 6:11, 6:24; 8:32); distinta de Ofra de "
                "Benjamín (Jos 18:23)."),
    "a0f8af9": ("Mizpa de Galaad", "Jue 11:29: «Mizpa de Galaad»; allí acampa Israel contra Ammón y vive Jefté (Jue 10:17; 11:34)."),
    "ac24f5f": ("Gabaa", "Gabaa de Benjamín (Jue 19:14; 20:4), escenario del crimen y de la guerra de Jue 19–20."),
    "aeeaca0": ("Lehi", "Allí Sansón mata a mil filisteos con una quijada de asno (Jue 15:9-17)."),
}
OBLIGATORIOS_LUGAR = ["hazor", "tabor", "ofra-de-abiezer", "siquem", "timna", "gaza", "gabaa", "siloh", "dan"]
LUGARES = {}
LUGAR_OPCIONAL = set()
EXCL_AUTO = {}
INFO_AUTO = {}
moderno = josue.moderno
# El mismo nombre es persona y lugar en el versículo: la aparición precedida de este texto es el lugar.
LUGAR_NO_PERSONA = [((18, 29), "Dan_1", "aquella ciudad "), ((9, 28), "Shechem_1", "qué es ")]


def construir(cx):
    rv, br, errores = cx["rv"], cx["br"], cx["errores"]
    for c, n in enumerate(POR_CAPITULO, 1):
        hay = sum(1 for (cc, _) in rv if cc == c)
        if hay != n:
            errores.append(f"Jueces {c}: la RV1909 tiene {hay} versículos (numeración inglesa/hebrea: {n})")
        if sum(1 for (cc, _) in br if cc == c) != n:
            errores.append(f"Jueces {c}: Brenton no tiene {n} versículos")
    for ref, ini in VERSIFICACION:
        if not rv.get(ref, "").startswith(ini):
            errores.append(f"Versificación de Jue {ref[0]}:{ref[1]}: la RV1909 no empieza «{ini}»")
    for ref, frag in VERSIFICACION_LXX:
        if frag not in br.get(ref, ""):
            errores.append(f"Brenton Jue {ref[0]}:{ref[1]} no dice «{frag}»")
    for ref, frag in CITAS_RESUMEN:
        if frag not in rv.get(ref, ""):
            errores.append(f"Resumen de pasaje: «{frag}» no está en Jue {ref[0]}:{ref[1]}")
    res = exodo.construir(cx, sys.modules[__name__])
    for p in res["nuevas"]:
        if p["id"] == JABIN:
            p["sexo"] = "m"  # id propio (no está en BibleData-Person): «rey» (Jue 4:2)
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
            LUGARES[obid] = (lid, prev[lid]["nombre"], list(prev[lid]["formas_rv1909"]), prev[lid]["tipo"], "", False)
            LUGAR_OPCIONAL.add(obid)
    UNIR_LUGAR = {**unir, **UNIR_LUGAR_MANUAL}
    EXCLUIR_LUGAR = {**EXCLUIR_LUGAR, **EXCL_AUTO}
    return exodo.construir_lugares(rv, menciones_personas, rutas, lugares_previos, errores, avisos, sa,
                                   sys.modules[__name__])


# ---------------------------------------------------------------- hechos obligatorios (sobre los datos finales)
def comprobar(datos, errores):
    """Comprueba los hechos pedidos para Jueces (falla si falta alguno). Devuelve líneas de informe."""
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
            errores.append(f"Hecho obligatorio (Jueces): {desc}")

    def tiene(pid, ref, mencion=True):
        return ref in P.get(pid, {}).get("refs", []) and (not mencion or (ref, pid) in M)

    def rel(de, a, tipo, ref):
        x = R.get((de, a, tipo))
        return bool(x) and (x["ref"] == ref and x.get("cita") and x["cita"] in texto.get(ref, "") or ref in x["nota"])

    def sin_libro(pid, pref):
        return not any(r.startswith(pref) for r in P.get(pid, {}).get("refs", []))

    def lugar_en(lid, ref):
        return ref in L.get(lid, {}).get("refs", []) and (ref, lid) in ML

    ok_(len(caps) == CAPITULOS and len(texto) == VERSICULOS and [len(c["versiculos"]) for c in caps] == POR_CAPITULO,
        f"{CAPITULOS} capítulos y {VERSICULOS} versículos (hay {len(caps)} y {len(texto)})")
    ok_(not [r for r, t in texto.items() if not t], "ningún versículo vacío")
    ok_(tiene("Othniel_1", "Jue 3:9") and "Jos 15:17" in P["Othniel_1"]["refs"] and rel("Kenaz_2", "Othniel_1", "padre", "Jue 3:9"),
        "Otoniel hijo de Quenaz (Jue 3:9) = el de Jos 15:17 (mismo id)")
    ok_(tiene("Ehud_1", "Jue 3:15") and tiene("Gera_2", "Jue 3:15") and rel("Gera_2", "Ehud_1", "padre", "Jue 3:15"),
        "Aod hijo de Gera (Jue 3:15)")
    ok_(tiene("Eglon_1", "Jue 3:12") and "Moab" in P["Eglon_1"]["rol"], "Eglón rey de Moab (Jue 3:12)")
    ok_(tiene("Deborah_2", "Jue 4:4") and "profetisa" in P["Deborah_2"]["rol"] and sin_libro("Deborah_2", "Gn ")
        and sin_libro("Deborah_1", "Jue "), "Débora profetisa (Jue 4:4) ≠ Débora de Gn 35:8")
    ok_(tiene("Barak_1", "Jue 4:6") and rel("Abinoam_1", "Barak_1", "padre", "Jue 4:6"), "Barac hijo de Abinoam (Jue 4:6)")
    ok_(tiene("Jael_1", "Jue 4:17") and rel("Heber_2", "Jael_1", "conyuge", "Jue 4:17") and sin_libro("Heber_2", "Gn "),
        "Jael mujer de Heber ceneo (Jue 4:17)")
    ok_(tiene("Sisera_1", "Jue 4:2"), "Sísara (Jue 4:2)")
    g = P.get("Gideon_1", {})
    ok_(tiene("Gideon_1", "Jue 6:11") and rel("Joash_1", "Gideon_1", "padre", "Jue 6:11") and tiene("Gideon_1", "Jue 6:32")
        and "Jerobaal" in g.get("formas_rv1909", []) and g.get("identidad", {}).get("certeza") == "texto"
        and "Jue 6:32" in g.get("identidad", {}).get("refs", []), "Gedeón hijo de Joás (Jue 6:11) = Jerobaal (Jue 6:32), identidad de texto")
    ok_(tiene("Abimelech_2", "Jue 9:1") and rel("Gideon_1", "Abimelech_2", "padre", "Jue 8:31") and sin_libro("Abimelech_2", "Gn ")
        and sin_libro("Abimelech_1", "Jue "), "Abimelec hijo de Gedeón (Jue 8:31; 9:1) ≠ Abimelec de Gn 20")
    ok_(tiene("Jephthah_1", "Jue 11:1") and "galaadita" in P["Jephthah_1"]["rol"], "Jefté galaadita (Jue 11:1)")
    ok_(tiene("Samson_1", "Jue 13:24") and tiene("Manoah_1", "Jue 13:2") and "Manoah_1" in {x["de"] for x in datos["relaciones"]
        if x["a"] == "Samson_1" and x["tipo"] == "padre"}, "Sansón hijo de Manoa (Jue 13:2, 13:24; 16:31)")
    ok_(tiene("Delilah_1", "Jue 16:4"), "Dalila (Jue 16:4)")
    ok_(tiene("Phinehas_1", "Jue 20:28") and "Nm 25:7" in P["Phinehas_1"]["refs"] and rel("Eleazar_1", "Phinehas_1", "padre", "Jue 20:28"),
        "Finees hijo de Eleazar (Jue 20:28) = el de Nm 25")
    ok_(tiene(JABIN, "Jue 4:2") and sin_libro("Jabin_1", "Jue ") and sin_libro(JABIN, "Jos "),
        "Jabín de Jue 4 ≠ Jabín de Jos 11 (Jos 11:10: muerto por Josué)")
    ok_(tiene("Hobab_1", "Jue 4:11") and sin_libro("Reuel_2", "Jue "), "Hobab (Jue 4:11) = Hobab de Nm 10:29; Jetro/Ragüel sin refs de Jue")
    ok_(tiene("Jonathan_1", "Jue 18:30") and rel("Gershom_2", "Jonathan_1", "padre", "Jue 18:30")
        and rel("Manasseh_2", "Gershom_2", "padre", "Jue 18:30") and sin_libro("Gershom_2", "Ex "),
        "Jonatán hijo de Gersón hijo de Manasés (Jue 18:30), como lo da el texto")
    ok_(not [p for p in EXCLUIR if any(r.startswith("Jue ") for r in P.get(p, {}).get("refs", []))]
        and sin_libro("Jacob_1", "Jue "), "sin personas para Dios, el ángel, reyes sin nombre, Ammón, Amalec ni «Israel»")
    # Lugares
    for lid in OBLIGATORIOS_LUGAR:
        l = L.get(lid)
        ok_(bool(l) and any(r.startswith("Jue ") and (r, lid) in ML for r in l["refs"]),
            f"lugar {lid} con refs de Jueces ({sum(1 for r in l['refs'] if r.startswith('Jue ')) if l else 0})")
    ok_(lugar_en("hazor", "Jue 4:2") and lugar_en("tabor", "Jue 4:6") and lugar_en("ofra-de-abiezer", "Jue 6:11")
        and lugar_en("timna", "Jue 14:1") and lugar_en("gabaa", "Jue 19:12") and lugar_en("siloh", "Jue 18:31"),
        "Hazor (4:2), Tabor (4:6), Ofra (6:11), Timnat (14:1), Gabaa (19:12) y Silo (18:31) marcados")
    mizpas = sorted({lid for (r, lid) in ML if r in ("Jue 10:17", "Jue 20:1") and lid.startswith("mizpa")})
    ok_(len(mizpas) == 2, f"Mizpa de Galaad (10:17) y Mizpa de Benjamín (20:1) {mizpas}")
    d = L.get("dan", {})
    ok_(lugar_en("dan", "Jue 18:29") and lugar_en("dan", "Jue 18:7") and "Lais" in d.get("formas_rv1909", [])
        and tiene("Dan_1", "Jue 18:29"), "Lais = Dan (Jue 18:29): lugar con la forma «Lais» y Dan su padre como persona")
    sin = [l for l in datos["lugares"] if any(r.startswith("Jue ") for r in l["refs"]) and not l["ubicacion"]]
    ok_(all("OpenBible no da identificación" in l["nota"] for l in sin), f"lugares de Jueces sin coordenadas con nota ({len(sin)})")
    # Pasajes, secciones y orden de lectura
    pas = [p for p in datos["pasajes"] if p["libro"] == LIBRO]
    ok_(len(pas) == len(PASAJES) and pas[0]["inicio"] == "Jue 1:1" and pas[-1]["fin"] == "Jue 21:25",
        f"{len(pas)} pasajes jue-NN de Jue 1:1 a Jue 21:25")
    ok_(len({p["seccion"] for p in pas}) == 9, "9 secciones")
    ids = [p["id"] for p in datos["pasajes"]]
    ult_jos = max(i for i, p in enumerate(datos["pasajes"]) if p["libro"] == "Jos")
    ok_(ids.index(pas[0]["id"]) == ult_jos + 1 and datos["libros"][-1]["id"] == LIBRO,
        "Jueces va justo después de Josué en el orden de los pasajes (lectura en orden)")
    return lineas

