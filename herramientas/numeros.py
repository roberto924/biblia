"""Números 1–36: personas, relaciones, edades, pasajes, menciones y lugares (lo usa construir_datos.py).

Reutiliza la lógica de exodo.py (exodo.construir / exodo.construir_lugares con este módulo como
configuración), igual que levitico.py. Cada dato lleva versículo, fuente y certeza; las citas se comprueban
literalmente contra la RV1909 (TM) o Brenton (LXX). Las personas de Génesis/Éxodo/Levítico (Moisés, Aarón,
Coré hijo de Izhar, Finees…) son la misma persona (mismo id de BibleData): se amplían sus `refs`.

Versificación: la RV1909 de eBible numera Nm 13 y Nm 30 como el texto hebreo (Nm 12:16 y 29:40 quedan
vacíos; su texto está en 13:1 y 30:1) y funde dos versículos al final de cada capítulo (13:33, 30:16).
BibleData y OpenBible usan la numeración inglesa: REMAP_REF las pasa a la de la RV1909.
Solo biblioteca estándar.
"""
import sys

import exodo

LIBRO = "Nm"
NOMBRE = "Números"
USX = "NUM"
CAPITULOS = 36
VERSICULOS = 1288
# Versículos que la RV1909 de eBible deja vacíos (su texto está en el siguiente).
VACIOS = {(12, 16): "Nm 13:1", (29, 40): "Nm 30:1"}


def REMAP_REF(r):
    """Referencia de BibleData/OpenBible (numeración inglesa) -> numeración de la RV1909 (eBible)."""
    c, v = r
    if (c, v) == (12, 16):
        return (13, 1)
    if c == 13:
        return (13, min(v + 1, 33))
    if (c, v) == (29, 40):
        return (30, 1)
    if c == 30:
        return (30, min(v + 1, 16))
    return r


# «Amalec», «Moab» y «Ammón» son en Números los pueblos (van como lugares/pueblos de OpenBible);
# los reyes sin nombre de BibleData (Edom, Arad, Moab) no se crean como personas.
EXCLUIR = {"YHVH_1", "NA", "the angel of the LORD_1", "Amalek_1", "Moab_1", "Ben-ammi_1",
           "King of Edom_1", "King of Arad_1", "King of Moab_1"}
SOLO_ETIQUETA = {"Jacob_1": {"Jacob"}}
FORMA_NO_MENCION = {("Jacob_1", "israel")}
PV_DESCARTAR = {
    ("Bezalel_1", (16, 9)): "Nm 16:9 no menciona a Bezaleel (probable errata de BibleData).",
    ("Jacob_1", (24, 17)): "en el oráculo de Balaam «Jacob» es el pueblo («saldrá ESTRELLA de Jacob»), no el patriarca.",
    ("Jacob_1", (24, 19)): "en el oráculo de Balaam «Jacob» es el pueblo, no el patriarca.",
    ("Ishvah_1", (26, 44)): ("Nm 26:44 dice «Issui» (hebreo Yishví): corresponde a Isúi de Gn 46:17 (RV «Isui»), "
                             "no a Isúa; se asigna a Isúi."),
}
REL_DESCARTAR = {
    ("Simeon_1", "Salu_1", "padre"): "Nm 25:14 dice que Zimri era «de la tribu de Simeón»: es la tribu, no el padre de Salu.",
    ("Bela_2", "Ard_1", "padre"): ("Gn 46:21 cuenta a Ard entre los hijos de Benjamín; Nm 26:40 lo pone entre los "
                                   "«hijos de Bela»: se deja la relación de Génesis y se anota la de Números."),
    ("Bela_2", "Naaman_1", "padre"): ("Gn 46:21 cuenta a Naamán entre los hijos de Benjamín; Nm 26:40 lo pone entre los "
                                      "«hijos de Bela»: se deja la relación de Génesis y se anota la de Números."),
    ("Eliab_2", "Nemuel_1", "padre"): "BibleData la cita en Nm 16:1, que no nombra a Nemuel: se toma de Nm 26:9.",
}
FORMAS_FORZADAS = {"Balak_1": ["Balac"], "Joshua_1": ["Josué", "Oseas"], "Gaddi_1": ["Gaddi"],
                   "Ishvi_1": ["Issui"], "Gideoni_1": ["Gedeón"],
                   "Hori_2": ["Hurí"], "Vophsi_1": ["Vapsi"]}

MODERNO = {
    "Elizur_1": "Elisur", "Shedeur_1": "Sedeur", "Shelumiel_1": "Selumiel", "Zurishaddai_1": "Zurisadai",
    "Nethanel_1": "Natanael", "Zuar_1": "Zuar", "Eliab_1": "Eliab", "Helon_1": "Helón", "Elishama_1": "Elisama",
    "Ammihud_1": "Amiud", "Gamaliel_1": "Gamaliel", "Pedahzur_1": "Pedasur", "Abidan_1": "Abidán",
    "Gideoni_1": "Gedeoni", "Ahiezer_1": "Ahiezer", "Ammishaddai_1": "Amisadai", "Pagiel_1": "Pagiel",
    "Ochran_1": "Ocrán", "Eliasaph_1": "Eliasaf", "Deuel_1": "Deuel", "Ahira_1": "Ahira", "Enan_1": "Enán",
    "Eliasaph_2": "Eliasaf", "Lael_1": "Lael", "Zuriel_1": "Zuriel", "Abihail_1": "Abihail", "Hobab_1": "Hobab",
    "Eldad_1": "Eldad", "Medad_1": "Medad", "Shammua_1": "Samúa", "Zaccur_1": "Zacur", "Shaphat_1": "Safat",
    "Hori_2": "Horí", "Caleb_1": "Caleb", "Jephunneh_1": "Jefone", "Igal_1": "Igal", "Joseph_2": "José",
    "Palti_1": "Palti", "Raphu_1": "Rafú", "Gaddiel_1": "Gadiel", "Sodi_1": "Sodi", "Gaddi_1": "Gadi",
    "Susi_1": "Susi", "Ammiel_1": "Amiel", "Gemalli_1": "Gemali", "Sethur_1": "Setur", "Michael_1": "Micael",
    "Nahbi_1": "Nahbi", "Vophsi_1": "Vapsi", "Geuel_1": "Geuel", "Machi_1": "Maqui", "Ahiman_1": "Ahimán",
    "Sheshai_1": "Sesai", "Talmai_1": "Talmai", "Anak_1": "Anac", "Dathan_1": "Datán", "Abiram_1": "Abiram",
    "Eliab_2": "Eliab", "On_1": "On", "Peleth_1": "Pelet", "Sihon_1": "Sehón", "Og_1": "Og", "Balak_1": "Balac",
    "Zippor_1": "Zipor", "Balaam_1": "Balaam", "Beor_2": "Beor", "Agag_1": "Agag", "Zimri_1": "Zimri",
    "Salu_1": "Salu", "Cozbi_1": "Cozbi", "Zur_1": "Zur", "Nemuel_1": "Nemuel", "Gilead_1": "Galaad",
    "Iezer_1": "Jezer", "Helek_1": "Helec", "Asriel_1": "Asriel", "Shechem_2": "Siquem", "Shemida_1": "Semida",
    "Hepher_1": "Hefer", "Zelophehad_1": "Zelofehad", "Mahlah_1": "Maala", "Noah_2": "Noa", "Hoglah_1": "Hogla",
    "Milcah_2": "Milca", "Tirzah_1": "Tirsa", "Shuthelah_1": "Sutela", "Becher_2": "Bequer", "Tahan_1": "Tahán",
    "Eran_1": "Erán", "Evi_1": "Evi", "Rekem_1": "Requem", "Zur_2": "Zur", "Hur_2": "Hur", "Reba_1": "Reba",
    "Jair_1": "Jair", "Nobah_1": "Noba", "Samuel_1": "Samuel", "Ammihud_2": "Amiud", "Elidad_1": "Elidad",
    "Chislon_1": "Quislón", "Bukki_1": "Buqui", "Jogli_1": "Jogli", "Hanniel_1": "Haniel", "Ephod_1": "Efod",
    "Kemuel_2": "Kemuel", "Shiphtan_1": "Siftán", "Elizaphan_1": "Elizafán", "Parnach_1": "Parnac",
    "Paltiel_1": "Paltiel", "Azzan_1": "Azán", "Ahihud_1": "Ahiud", "Shelomi_1": "Selomi", "Pedahel_1": "Pedael",
    "Ammihud_3": "Amiud",
}
_JEFE = "Jefe de la tribu de {t} en el censo del Sinaí (Nm 1:{v}; también Nm 2, 7 y 10)."
NOTAS = {
    "Eliab_1": "Jefe de la tribu de Zabulón (Nm 1:9). Distinto de Eliab, padre de Datán y Abiram (Nm 16:1), de la tribu de Rubén.",
    "Eliab_2": "De la tribu de Rubén, padre de Datán y Abiram (Nm 16:1). Distinto de Eliab, jefe de Zabulón (Nm 1:9).",
    "Eliasaph_1": "Jefe de la tribu de Gad (Nm 1:14). Distinto de Eliasaf hijo de Lael, jefe de los gersonitas (Nm 3:24).",
    "Eliasaph_2": "Jefe de los gersonitas (Nm 3:24). Distinto de Eliasaf hijo de Deuel, jefe de Gad (Nm 1:14).",
    "Deuel_1": "La RV1909 escribe «Dehuel» (Nm 1:14; 7:42…) y «Rehuel» (Nm 2:14), como el hebreo. Distinto de Ragüel, suegro de Moisés.",
    "Ammihud_1": "Padre de Elisama, de Efraín (Nm 1:10). BibleData distingue otros dos Amiud en Nm 34:20 y 34:28.",
    "Ammihud_2": "Padre de Samuel, de Simeón (Nm 34:20). Distinto de los Amiud de Nm 1:10 y Nm 34:28.",
    "Ammihud_3": "Padre de Pedael, de Neftalí (Nm 34:28). Distinto de los Amiud de Nm 1:10 y Nm 34:20.",
    "Gideoni_1": "La RV1909 escribe «Gedeón» (Nm 1:11); en hebreo es Gidoní, distinto del juez Gedeón.",
    "Joseph_2": "Padre de Igal, de la tribu de Isacar (Nm 13:8 en la RV1909). Distinto de José, hijo de Jacob.",
    "Hobab_1": ("Nm 10:29: «Hobab, hijo de Ragüel Madianita, su suegro»; la frase no deja claro si «su suegro» "
                "es Hobab o Ragüel."),
    "Anak_1": "Antepasado de los «gigantes, hijos de Anac» (Nm 13:33 en la RV1909).",
    "Caleb_1": "Uno de los doce enviados a reconocer la tierra; Nm 32:12 lo llama «Caleb, hijo de Jephone Cenezeo».",
    "Balak_1": "Nm 22:4: «Balac, hijo de Zippor, era entonces rey de Moab».",
    "Balaam_1": "Nm 22:5: Balac lo manda llamar «á Pethor, que está junto al río». Muere a espada en la guerra contra Madián (Nm 31:8).",
    "Zur_1": ("Nm 25:15: «Zur, príncipe de pueblos, padre de familia en Madián». BibleData lo distingue de Zur, uno de los "
              "cinco reyes de Madián (Nm 31:8); podrían ser el mismo, pero el texto no lo dice."),
    "Zur_2": ("Uno de los cinco reyes de Madián muertos en la guerra (Nm 31:8). BibleData lo distingue de Zur, padre de "
              "Cozbi (Nm 25:15); podrían ser el mismo, pero el texto no lo dice."),
    "Hur_2": "Uno de los cinco reyes de Madián (Nm 31:8). Distinto de Hur, que acompaña a Moisés en Éxodo (Ex 17:10).",
    "Milcah_2": "Hija de Zelofehad (Nm 26:33; 27:1). Distinta de Milca, mujer de Nacor (Gn 11:29).",
    "Noah_2": "Hija de Zelofehad (Nm 26:33). La RV1909 escribe «Noa»; distinta de Noé.",
    "Gilead_1": "Hijo de Maquir (Nm 26:29). «Galaad» es también la región al oriente del Jordán (Nm 32).",
    "Shechem_2": "Hijo de Galaad, de Manasés (Nm 26:31). Distinto de Siquem, hijo de Hamor (Gn 34).",
    "Becher_2": "De la tribu de Efraín (Nm 26:35). Distinto de Bequer, hijo de Benjamín (Gn 46:21).",
    "Nemuel_1": "Hijo de Eliab, de Rubén (Nm 26:9). Distinto de Jemuel, hijo de Simeón, al que Nm 26:12 también llama «Nemuel».",
    "Kemuel_2": "Jefe de Efraín para el reparto de la tierra (Nm 34:24). Distinto de Kemuel, hijo de Nacor (Gn 22:21).",
    "Elizaphan_1": "Jefe de Zabulón para el reparto (Nm 34:25). Distinto de Elzafán hijo de Uziel (Ex 6:22; Nm 3:30), aunque la RV1909 escribe igual «Elisaphán».",
    "Samuel_1": "Jefe de Simeón para el reparto de la tierra (Nm 34:20). No es el profeta Samuel.",
    "Jair_1": "Nm 32:41: «Jair hijo de Manasés» (descendiente de Manasés; el texto no da su padre).",
    "Agag_1": "Solo se nombra en el oráculo de Balaam (Nm 24:7) como rey con quien se compara al de Israel.",
}
for _pid, _t, _v in (("Elizur_1", "Rubén", 5), ("Shelumiel_1", "Simeón", 6), ("Nethanel_1", "Isacar", 8),
                     ("Elishama_1", "Efraín", 10), ("Gamaliel_1", "Manasés", 10), ("Abidan_1", "Benjamín", 11),
                     ("Ahiezer_1", "Dan", 12), ("Pagiel_1", "Aser", 13), ("Ahira_1", "Neftalí", 15)):
    NOTAS[_pid] = _JEFE.format(t=_t, v=_v)
# Identificaciones de una persona con dos nombres (certeza y versículos).
IDENTIDAD = {
    "Joshua_1": {"certeza": "texto", "refs": ["Nm 13:9", "Nm 13:17"], "nombres_rv1909": ["Oseas", "Josué"],
                 "fuente": "rv1909",
                 "nota": "Nm 13:17 (13:16 en la numeración inglesa): «á Oseas hijo de Nun, le puso Moisés el nombre de Josué»."},
}
NOTAS_VERIFICAR = [
    ("TM", (13, 17), "á Oseas hijo de Nun, le puso Moisés el nombre de Josué"), ("TM", (13, 9), "Oseas hijo de Nun"),
    ("TM", (10, 29), "Hobab, hijo de Ragüel Madianita, su suegro"), ("TM", (22, 4), "Balac, hijo de Zippor, era entonces rey de Moab"),
    ("TM", (25, 15), "Zur, príncipe de pueblos, padre de familia en Madián"), ("TM", (32, 12), "Caleb, hijo de Jephone Cenezeo"),
    ("TM", (32, 41), "Jair hijo de Manasés"), ("TM", (13, 33), "gigantes, hijos de Anac"),
    ("TM", (20, 1), "allí murió María, y fué allí sepultada"), ("TM", (20, 28), "Aarón murió allí en la cumbre del monte"),
    ("TM", (33, 38), "Y subió Aarón el sacerdote al monte de Hor"), ("TM", (26, 59), "Jochâbed, hija de Leví, la cual nació á Leví en Egipto"),
    ("TM", (26, 40), "Y los hijos de Bela fueron Ard y Naamán"), ("TM", (25, 14), "jefe de una familia de la tribu de Simeón"),
    ("TM", (26, 12), "de Nemuel"), ("TM", (26, 44), "de Issui"), ("TM", (16, 1), "Y CORÉ, hijo de Ishar, hijo de Coath, hijo de Leví"),
    ("TM", (25, 7), "Phinees, hijo de Eleazar, hijo de Aarón el sacerdote"),
]
ROLES = {
    "Eldad_1": ("profetiza en el campamento", (11, 26), "llamado el uno Eldad y el otro Medad"),
    "Medad_1": ("profetiza en el campamento", (11, 26), "llamado el uno Eldad y el otro Medad"),
    "Caleb_1": ("enviado a reconocer la tierra, de la tribu de Judá", (13, 7), "De la tribu de Judá, Caleb hijo de Jephone"),
    "Sihon_1": ("rey de los amorreos", (21, 21), "Sehón, rey de los Amorrheos"),
    "Og_1": ("rey de Basán", (21, 33), "Og rey de Basán"),
    "Balak_1": ("rey de Moab", (22, 4), "Balac, hijo de Zippor, era entonces rey de Moab"),
    "Balaam_1": ("adivino llamado por Balac para maldecir a Israel", (22, 5), "envió mensajeros á Balaam hijo de Beor"),
    "Agag_1": ("rey nombrado en el oráculo de Balaam", (24, 7), "ensalzarse ha su rey más que Agag"),
    "Zimri_1": ("israelita muerto por Finees", (25, 14), "era Zimri hijo de Salu, jefe de una familia de la tribu de Simeón"),
    "Cozbi_1": ("madianita muerta por Finees", (25, 15), "el nombre de la mujer Madianita muerta, era Cozbi"),
    "Evi_1": ("rey de Madián", (31, 8), "cinco reyes de Madián"),
    "Rekem_1": ("rey de Madián", (31, 8), "cinco reyes de Madián"),
    "Zur_2": ("rey de Madián", (31, 8), "cinco reyes de Madián"),
    "Hur_2": ("rey de Madián", (31, 8), "cinco reyes de Madián"),
    "Reba_1": ("rey de Madián", (31, 8), "cinco reyes de Madián"),
    "Jair_1": ("toma las aldeas de Galaad (Havot-jair)", (32, 41), "Jair hijo de Manasés fué y tomó sus aldeas"),
    "Nobah_1": ("toma Kenat y le pone su nombre", (32, 42), "Noba fué y tomó á Kenath"),
    "Dathan_1": ("se rebela contra Moisés con Coré", (26, 9), "hicieron el motín contra Moisés y Aarón con la compañía de Coré"),
    "Abiram_1": ("se rebela contra Moisés con Coré", (26, 9), "hicieron el motín contra Moisés y Aarón con la compañía de Coré"),
}
SIN_NOMBRE = {}
REFS_EXTRA = {"Ishvi_1": [(26, 44)]}
NOTAS_EXISTENTES = {
    "Aaron_1": ("Muere en la cumbre del monte de Hor (Nm 20:25-28; 33:38), a los 123 años (Nm 33:39); "
                "Eleazar recibe sus vestiduras."),
    "Miriam_1": ("Muere y es sepultada en Cades, en el desierto de Zin (Nm 20:1). Nm 26:59 sí nombra a sus padres: "
                 "«parió de Amram á Aarón y á Moisés, y á María su hermana»."),
    "Jochebed_1": "Nm 26:59: «Jochâbed, hija de Leví, la cual nació á Leví en Egipto».",
    "Joshua_1": "Nm 13:17 (RV1909): «á Oseas hijo de Nun, le puso Moisés el nombre de Josué».",
    "Korah_3": ("Encabeza la rebelión contra Moisés y Aarón (Nm 16:1-35); Nm 26:11: «los hijos de Coré no murieron». "
                "Distinto de Coré, hijo de Esaú (Gn 36:5)."),
    "Eleazar_1": "Sucede a Aarón como sacerdote: Moisés le pone las vestiduras de su padre en el monte Hor (Nm 20:28).",
    "Phinehas_1": "Nm 25:7-13: atraviesa a Zimri y a Cozbi y detiene la mortandad; Dios le da «pacto del sacerdocio perpetuo».",
    "Ard_1": "Nm 26:40 lo cuenta entre los «hijos de Bela» (hijo de Benjamín); Gn 46:21, entre los hijos de Benjamín.",
    "Naaman_1": "Nm 26:40 lo cuenta entre los «hijos de Bela» (hijo de Benjamín); Gn 46:21, entre los hijos de Benjamín.",
    "Ishvi_1": ("Nm 26:44 lo llama «Issui» (BibleData asigna ese versículo a Isúa; el nombre hebreo, Yishví, es el de "
                "Isúi)."),
}
for _pid, _ref, _forma, _gn in (("Jemuel_1", "26:12", "Nemuel", "Jemuel"), ("Zohar_2", "26:13", "Zera", "Zohar"),
                                ("Ziphion_1", "26:15", "Zephón", "Zifión"), ("Ezbon_1", "26:16", "Ozni", "Ezbón"),
                                ("Ehi_1", "26:38", "Achîram", "Ehi"), ("Muppim_1", "26:39", "Supham", "Mupim"),
                                ("Huppim_1", "26:39", "Hupham", "Hupim"), ("Hushim_1", "26:42", "Suham", "Husim"),
                                ("Iob_1", "26:24", "Jasub", "Job")):
    NOTAS_EXISTENTES[_pid] = (f"Nm {_ref} lo llama «{_forma}»; la identificación con {_gn} (Gn 46) es de BibleData "
                              "(inferida por la lista de familias).")
    NOTAS_VERIFICAR.append(("TM", tuple(map(int, _ref.split(":"))), _forma))

RELACIONES = [
    ("Eliab_2", "Dathan_1", "padre", (16, 1), "Dathán y Abiram, hijos de Eliab", "También Nm 26:9."),
    ("Eliab_2", "Abiram_1", "padre", (16, 1), "Dathán y Abiram, hijos de Eliab", "También Nm 26:9."),
    ("Eliab_2", "Nemuel_1", "padre", (26, 9), "los hijos de Eliab: Nemuel", ""),
    ("Pallu_1", "Eliab_2", "padre", (26, 8), "los hijos de Phallú: Eliab", ""),
    ("Peleth_1", "On_1", "padre", (16, 1), "Hon, hijo de Peleth", ""),
    ("Zippor_1", "Balak_1", "padre", (22, 2), "Balac, hijo de Zippor", ""),
    ("Beor_2", "Balaam_1", "padre", (22, 5), "Balaam hijo de Beor", "También Nm 31:8."),
    ("Jephunneh_1", "Caleb_1", "padre", (13, 7), "Caleb hijo de Jephone", "Nm 13:6 en la numeración inglesa."),
    ("Salu_1", "Zimri_1", "padre", (25, 14), "Zimri hijo de Salu", ""),
    ("Zur_1", "Cozbi_1", "padre", (25, 15), "Cozbi, hija de Zur", "También Nm 25:18: «Cozbi, hija del príncipe de Madián»."),
    ("Levi_1", "Jochebed_1", "padre", (26, 59), "Jochâbed, hija de Leví", "Nm 26:59: «la cual nació á Leví en Egipto»."),
    ("Machir_1", "Gilead_1", "padre", (26, 29), "Machîr engendró á Galaad", ""),
    ("Hepher_1", "Zelophehad_1", "padre", (26, 33), "Salphaad, hijo de Hepher", "También Nm 27:1."),
]
for _h in ("Mahlah_1", "Noah_2", "Hoglah_1", "Milcah_2", "Tirzah_1"):
    RELACIONES.append(("Zelophehad_1", _h, "padre", (26, 33), "los nombres de las hijas de Salphaad fueron Maala, y Noa, y Hogla, y Milca, y Tirsa",
                       "También Nm 27:1 y 36:11."))
NOTAS_REL = {
    ("Anak_1", "Ahiman_1", "padre"): "«Hijos de Anac» (Nm 13:23 en la RV1909) puede indicar descendencia: Nm 13:33 llama así a todo el pueblo de gigantes.",
    ("Anak_1", "Sheshai_1", "padre"): "«Hijos de Anac» (Nm 13:23 en la RV1909) puede indicar descendencia: Nm 13:33 llama así a todo el pueblo de gigantes.",
    ("Anak_1", "Talmai_1", "padre"): "«Hijos de Anac» (Nm 13:23 en la RV1909) puede indicar descendencia: Nm 13:33 llama así a todo el pueblo de gigantes.",
    ("Ephraim_1", "Shuthelah_1", "padre"): "Nm 26:35 los da como «hijos de Ephraim por sus familias» (puede indicar descendencia).",
    ("Ephraim_1", "Becher_2", "padre"): "Nm 26:35 los da como «hijos de Ephraim por sus familias» (puede indicar descendencia).",
    ("Ephraim_1", "Tahan_1", "padre"): "Nm 26:35 los da como «hijos de Ephraim por sus familias» (puede indicar descendencia).",
}
# Relaciones de los libros anteriores que Números repite: se añade la referencia a la nota.
REPITE_GN = [
    ("Izhar_1", "Korah_3", "padre", (16, 1), "CORÉ, hijo de Ishar"),
    ("Kohath_1", "Izhar_1", "padre", (16, 1), "hijo de Ishar, hijo de Coath"),
    ("Eleazar_1", "Phinehas_1", "padre", (25, 7), "Phinees, hijo de Eleazar"),
    ("Nun_1", "Joshua_1", "padre", (13, 9), "Oseas hijo de Nun"),
    ("Kohath_1", "Amram_1", "padre", (26, 58), "Coath engendró á Amram"),
    ("Amram_1", "Aaron_1", "padre", (26, 59), "parió de Amram á Aarón"),
    ("Amram_1", "Moses_1", "padre", (26, 59), "parió de Amram á Aarón y á Moisés"),
    ("Jochebed_1", "Aaron_1", "madre", (26, 59), "ésta parió de Amram á Aarón"),
    ("Jochebed_1", "Moses_1", "madre", (26, 59), "ésta parió de Amram á Aarón y á Moisés"),
    ("Aaron_1", "Nadab_1", "padre", (26, 60), "á Aarón nacieron Nadab y Abiú, Eleazar é Ithamar"),
    ("Aaron_1", "Abihu_1", "padre", (26, 60), "á Aarón nacieron Nadab y Abiú, Eleazar é Ithamar"),
    ("Aaron_1", "Eleazar_1", "padre", (26, 60), "á Aarón nacieron Nadab y Abiú, Eleazar é Ithamar"),
    ("Aaron_1", "Ithamar_1", "padre", (26, 60), "á Aarón nacieron Nadab y Abiú, Eleazar é Ithamar"),
    ("Manasseh_1", "Machir_1", "padre", (32, 40), "Machîr hijo de Manasés"),
]
# Edades escritas: (persona, tipo, ref, índice de cifra TM, índice LXX, evento)
EDADES = [("Aaron_1", "total", (33, 39), 0, 0, "")]

S1 = "Censo y orden del campamento (Nm 1–4)"
S2 = "Leyes y preparativos en el Sinaí (Nm 5:1–10:10)"
S3 = "Del Sinaí a Cades (Nm 10:11–14:45)"
S4 = "Leyes y rebeliones en el desierto (Nm 15–19)"
S5 = "Hacia Moab (Nm 20–21)"
S6 = "Balac y Balaam (Nm 22–24)"
S7 = "Baal-peor y el segundo censo (Nm 25–26)"
S8 = "Preparativos para entrar en la tierra (Nm 27–36)"
PASAJES = [
    ("1:1", "1:16", "El censo: los jefes de cada tribu", "En el segundo año de la salida, Dios manda contar a los varones de veinte años arriba; se nombra un jefe por tribu.", S1),
    ("1:17", "1:33", "El censo de Rubén a Efraín", "Moisés y Aarón cuentan a los hombres de guerra de Rubén, Simeón, Gad, Judá, Isacar, Zabulón y Efraín.", S1),
    ("1:34", "1:46", "El censo de Manasés a Neftalí; el total", "Se cuentan Manasés, Benjamín, Dan, Aser y Neftalí; en total 603.550 hombres.", S1),
    ("1:47", "1:54", "Los levitas no se cuentan", "Los levitas quedan al cuidado del tabernáculo y acampan alrededor de él.", S1),
    ("2:1", "2:16", "El campamento: oriente y mediodía", "Cada tribu acampa bajo su bandera; Judá, Isacar y Zabulón al oriente; Rubén, Simeón y Gad al mediodía.", S1),
    ("2:17", "2:34", "El tabernáculo en medio; occidente y norte", "El tabernáculo marcha en medio; Efraín, Manasés y Benjamín al occidente; Dan, Aser y Neftalí al norte.", S1),
    ("3:1", "3:13", "Los sacerdotes y los levitas", "Los hijos de Aarón; los levitas son dados a Aarón y tomados en lugar de los primogénitos.", S1),
    ("3:14", "3:26", "Censo de los levitas: los gersonitas", "Se cuentan los levitas desde un mes arriba; los gersonitas acampan al occidente y cuidan las cortinas.", S1),
    ("3:27", "3:39", "Los coatitas y los meraritas", "Los coatitas guardan el santuario; los meraritas, las tablas y basas; Moisés y Aarón acampan al oriente.", S1),
    ("3:40", "3:51", "El rescate de los primogénitos", "Se cuentan los primogénitos; los que exceden a los levitas se rescatan a cinco siclos cada uno.", S1),
    ("4:1", "4:20", "El cargo de los coatitas", "Aarón y sus hijos cubren los objetos santos; los coatitas los llevan sin tocarlos.", S1),
    ("4:21", "4:33", "El cargo de los gersonitas y los meraritas", "Los gersonitas llevan las cortinas y cubiertas; los meraritas, las tablas, columnas y basas.", S1),
    ("4:34", "4:49", "Los levitas contados para el servicio", "Se cuentan los levitas de treinta a cincuenta años que sirven en el tabernáculo.", S1),
    ("5:1", "5:10", "Pureza del campamento y restitución", "Los inmundos salen del campamento; quien daña a otro confiesa y restituye con un quinto más.", S2),
    ("5:11", "5:31", "La ley de los celos", "Rito ante el sacerdote cuando un marido sospecha que su mujer le ha sido infiel.", S2),
    ("6:1", "6:21", "El voto de nazareo", "Quien se aparta para Jehová no bebe vino, no se corta el cabello ni se acerca a un muerto.", S2),
    ("6:22", "6:27", "La bendición sacerdotal", "«Jehová te bendiga, y te guarde»: así bendecirán Aarón y sus hijos a Israel.", S2),
    ("7:1", "7:11", "Las ofrendas de los príncipes: los carros", "Al ungir el tabernáculo, los príncipes traen carros y bueyes; cada uno ofrecerá en su día.", S2),
    ("7:12", "7:29", "Ofrendas de los días primero a tercero", "Naasón (Judá), Natanael (Isacar) y Eliab (Zabulón) traen la misma ofrenda.", S2),
    ("7:30", "7:47", "Ofrendas de los días cuarto a sexto", "Elisur (Rubén), Selumiel (Simeón) y Eliasaf (Gad) traen la misma ofrenda.", S2),
    ("7:48", "7:65", "Ofrendas de los días séptimo a noveno", "Elisama (Efraín), Gamaliel (Manasés) y Abidán (Benjamín) traen la misma ofrenda.", S2),
    ("7:66", "7:89", "Ofrendas de los días décimo a duodécimo; la voz", "Ahiezer (Dan), Pagiel (Aser) y Ahira (Neftalí); suma de las ofrendas; Moisés oye la voz desde el propiciatorio.", S2),
    ("8:1", "8:13", "Las lámparas y la purificación de los levitas", "Aarón enciende las siete lámparas; los levitas son purificados y presentados como ofrenda.", S2),
    ("8:14", "8:26", "Los levitas en lugar de los primogénitos", "Los levitas son de Dios en lugar de los primogénitos; sirven de veinticinco a cincuenta años.", S2),
    ("9:1", "9:14", "La Pascua en el desierto", "Israel celebra la Pascua en el Sinaí; quien estaba inmundo la celebra el mes segundo.", S2),
    ("9:15", "9:23", "La nube sobre el tabernáculo", "Cuando la nube se alza, el pueblo parte; cuando se detiene, acampa.", S2),
    ("10:1", "10:10", "Las trompetas de plata", "Dos trompetas de plata para convocar, para partir, para la guerra y para las fiestas.", S2),
    ("10:11", "10:28", "Partida del Sinaí", "El año segundo, mes segundo, día veinte, la nube se alza; las tribus parten en su orden.", S3),
    ("10:29", "10:36", "Hobab y el arca delante", "Moisés pide a Hobab que los guíe; el arca va delante tres días de camino.", S3),
    ("11:1", "11:15", "Tabera y la queja por la carne", "El fuego arde en Tabera; el pueblo pide carne y Moisés dice que no puede llevarlo solo.", S3),
    ("11:16", "11:35", "Los setenta ancianos y las codornices", "El espíritu reposa sobre setenta ancianos, también sobre Eldad y Medad; llegan codornices y una plaga en Kibrot-hataava.", S3),
    ("12:1", "13:1", "María y Aarón murmuran contra Moisés", "Hablan contra Moisés por su mujer cusita; María queda leprosa siete días fuera del campamento.", S3),
    ("13:2", "13:21", "Los doce enviados a reconocer la tierra", "Moisés envía a un jefe de cada tribu a Canaán; a Oseas hijo de Nun lo llama Josué.", S3),
    ("13:22", "13:33", "El informe de los enviados", "Traen un racimo del valle de Escol; Caleb anima a subir, los demás dicen que no podrán.", S3),
    ("14:1", "14:10", "El pueblo se rebela", "El pueblo llora y quiere volver a Egipto; Josué y Caleb defienden que la tierra es buena.", S3),
    ("14:11", "14:25", "Moisés intercede", "Dios quiere destruir al pueblo; Moisés intercede y Dios perdona, pero no verán la tierra.", S3),
    ("14:26", "14:38", "Cuarenta años en el desierto", "Los de veinte años arriba morirán en el desierto, salvo Caleb y Josué; los diez enviados mueren.", S3),
    ("14:39", "14:45", "Derrota en Horma", "El pueblo sube sin Moisés ni el arca y es derrotado por amalecitas y cananeos.", S3),
    ("15:1", "15:21", "Ofrendas al entrar en la tierra", "Presente y libación con cada sacrificio; una misma ley para el natural y el extranjero.", S4),
    ("15:22", "15:31", "Pecados por yerro y con soberbia", "Expiación por los pecados por yerro; quien peca con altivez será cortado.", S4),
    ("15:32", "15:41", "El que recogía leña en sábado; los pendones", "Un hombre recoge leña en sábado y es apedreado; flecos en los bordes de los vestidos.", S4),
    ("16:1", "16:19", "Coré, Datán y Abiram", "Coré, levita, y los rubenitas Datán y Abiram se levantan contra Moisés y Aarón con doscientos cincuenta príncipes.", S4),
    ("16:20", "16:35", "La tierra se abre", "La tierra traga a Coré, Datán y Abiram con sus casas; un fuego consume a los doscientos cincuenta.", S4),
    ("16:36", "16:50", "Los incensarios y la mortandad detenida", "Los incensarios cubren el altar; el pueblo murmura y Aarón detiene la mortandad con el incienso.", S4),
    ("17:1", "17:13", "La vara de Aarón florece", "De las doce varas, la de Aarón echa flores y almendras; se guarda delante del testimonio.", S4),
    ("18:1", "18:20", "Cargo y porción de los sacerdotes", "Aarón y sus hijos guardan el santuario; las ofrendas y primicias son su porción; Jehová es su heredad.", S4),
    ("18:21", "18:32", "El diezmo de los levitas", "Los levitas reciben el diezmo de Israel y dan a su vez el diezmo de ese diezmo.", S4),
    ("19:1", "19:10", "La vaca alazana", "Se quema una vaca alazana fuera del campamento y sus cenizas se guardan para el agua de purificación.", S4),
    ("19:11", "19:22", "La purificación por contacto con un muerto", "Quien toca un muerto queda inmundo siete días y se purifica con el agua de la expiación.", S4),
    ("20:1", "20:13", "Muerte de María; las aguas de la rencilla", "María muere en Cades; Moisés golpea la peña y sale agua, pero no entrará en la tierra.", S5),
    ("20:14", "20:21", "Edom niega el paso", "Moisés pide pasar por Edom por el camino real; Edom sale armado e Israel se desvía.", S5),
    ("20:22", "20:29", "Muerte de Aarón en el monte Hor", "Aarón sube al monte Hor, Eleazar recibe sus vestiduras y Aarón muere; el pueblo lo llora treinta días.", S5),
    ("21:1", "21:9", "Horma y la serpiente de bronce", "Israel vence al rey de Arad; el pueblo murmura, vienen serpientes y Moisés hace una serpiente de bronce.", S5),
    ("21:10", "21:20", "Hacia el Arnón; el pozo", "Etapas hasta el Arnón; en Beer Dios da agua y el pueblo canta al pozo.", S5),
    ("21:21", "21:35", "Victorias sobre Sehón y Og", "Sehón, rey de los amorreos, niega el paso y es vencido; también Og, rey de Basán.", S5),
    ("22:1", "22:20", "Balac llama a Balaam", "Balac, rey de Moab, manda llamar a Balaam para maldecir a Israel; Dios le dice que no los maldiga.", S6),
    ("22:21", "22:35", "La asna de Balaam", "El ángel de Jehová se pone en el camino; la asna lo ve y habla; Balaam solo dirá lo que Dios le diga.", S6),
    ("22:36", "23:12", "El primer oráculo", "Balac lleva a Balaam a los altos de Baal; en lugar de maldecir, Balaam bendice a Israel.", S6),
    ("23:13", "23:30", "El segundo oráculo", "Desde el Pisga, Balaam vuelve a bendecir: «Dios no es hombre para que mienta»; Balac lo lleva a Peor.", S6),
    ("24:1", "24:13", "El tercer oráculo", "El espíritu de Dios viene sobre Balaam y bendice las tiendas de Jacob; Balac se enoja.", S6),
    ("24:14", "24:25", "Los últimos oráculos", "Balaam anuncia una estrella de Jacob y habla de Moab, Edom, Amalec y los ceneos; cada uno vuelve a su lugar.", S6),
    ("25:1", "25:9", "Baal-peor", "En Sitim el pueblo se une a las moabitas y a Baal-peor; Finees mata a un israelita y a una madianita y cesa la mortandad.", S7),
    ("25:10", "25:18", "Pacto con Finees; Zimri y Cozbi", "Dios da a Finees pacto de sacerdocio perpetuo; se nombra a los muertos y se ordena herir a Madián.", S7),
    ("26:1", "26:18", "Segundo censo: Rubén, Simeón y Gad", "Tras la mortandad se cuenta otra vez al pueblo en los campos de Moab; familias de Rubén, Simeón y Gad.", S7),
    ("26:19", "26:37", "Judá, Isacar, Zabulón, Manasés y Efraín", "Familias de Judá, Isacar, Zabulón, Manasés —con las hijas de Zelofehad— y Efraín.", S7),
    ("26:38", "26:51", "Benjamín, Dan, Aser y Neftalí; el total", "Familias de Benjamín, Dan, Aser y Neftalí; en total 601.730 hombres.", S7),
    ("26:52", "26:65", "El reparto y los levitas", "La tierra se repartirá por suertes; censo de los levitas; ninguno de los del Sinaí queda, salvo Caleb y Josué.", S7),
    ("27:1", "27:11", "Las hijas de Zelofehad", "Maala, Noa, Hogla, Milca y Tirsa piden la herencia de su padre; Dios les da la razón.", S8),
    ("27:12", "27:23", "Josué, sucesor de Moisés", "Moisés ve la tierra desde Abarim; Dios elige a Josué y Moisés le impone las manos.", S8),
    ("28:1", "28:15", "Ofrendas diarias, del sábado y de cada mes", "El holocausto continuo, el del sábado y el del principio de cada mes.", S8),
    ("28:16", "28:31", "La Pascua y la fiesta de las semanas", "Ofrendas de los panes sin levadura y del día de las primicias.", S8),
    ("29:1", "29:11", "Las trompetas y el día de la expiación", "Ofrendas del día primero y del día diez del mes séptimo.", S8),
    ("29:12", "29:28", "La fiesta de las cabañas (días primero a sexto)", "Desde el día quince del mes séptimo, ofrendas que van disminuyendo de trece a ocho becerros.", S8),
    ("29:29", "29:40", "La fiesta de las cabañas (último día)", "Séptimo y octavo día de la fiesta; resumen de las ofrendas.", S8),
    ("30:1", "30:16", "Los votos", "Moisés transmite las leyes de los votos: del varón, de la hija en casa de su padre y de la mujer casada.", S8),
    ("31:1", "31:12", "Guerra contra Madián", "Mil hombres por tribu, con Finees, pelean contra Madián; mueren los cinco reyes y Balaam.", S8),
    ("31:13", "31:24", "Moisés se enoja; la purificación", "Moisés se enoja con los capitanes por las cautivas; purificación de personas y objetos.", S8),
    ("31:25", "31:41", "El reparto del botín", "El botín se divide entre los que pelearon y la congregación, con un tributo para Jehová.", S8),
    ("31:42", "31:54", "La parte de la congregación y la ofrenda de oro", "Los capitanes, que no han perdido a ninguno, ofrecen el oro a Jehová como memoria.", S8),
    ("32:1", "32:15", "Rubén y Gad piden Galaad", "Rubén y Gad, con mucho ganado, piden quedarse al oriente del Jordán; Moisés les recuerda Cades-barnea.", S8),
    ("32:16", "32:32", "El compromiso de Rubén y Gad", "Pasarán armados delante de Israel hasta que todos tengan su heredad; Moisés acepta.", S8),
    ("32:33", "32:42", "Las ciudades de Galaad y Basán", "Moisés da a Gad, Rubén y media tribu de Manasés el reino de Sehón y el de Og; reedifican ciudades.", S8),
    ("33:1", "33:15", "Las jornadas: de Ramesés al Sinaí", "Moisés escribe las salidas de Israel: de Ramesés por el mar hasta el desierto de Sinaí.", S8),
    ("33:16", "33:37", "Las jornadas: del Sinaí al monte Hor", "Del Sinaí, por Kibrot-hataava, Haserot y Ezión-geber, hasta Cades y el monte Hor.", S8),
    ("33:38", "33:49", "Muerte de Aarón; hasta los campos de Moab", "Aarón muere en el monte Hor a los 123 años; Israel llega a los campos de Moab, junto al Jordán.", S8),
    ("33:50", "33:56", "Orden de echar a los moradores", "Al pasar el Jordán echarán a los moradores, destruirán sus imágenes y repartirán la tierra.", S8),
    ("34:1", "34:15", "Los límites de la tierra", "Límites de Canaán al sur, al oeste, al norte y al este.", S8),
    ("34:16", "34:29", "Los que repartirán la tierra", "Eleazar, Josué y un príncipe por tribu repartirán la heredad.", S8),
    ("35:1", "35:8", "Las ciudades de los levitas", "Cuarenta y ocho ciudades con sus ejidos para los levitas.", S8),
    ("35:9", "35:21", "Las ciudades de refugio; el homicida", "Seis ciudades de refugio; quien mata con instrumento o por enemistad es homicida y morirá.", S8),
    ("35:22", "35:34", "El que mata sin intención", "El homicida sin intención queda en la ciudad de refugio hasta la muerte del sumo sacerdote.", S8),
    ("36:1", "36:13", "La herencia de las hijas casadas", "Las hijas de Zelofehad se casan dentro de su tribu para que la heredad no pase a otra.", S8),
]

# Lugares de OpenBible en Números: obid -> (id, nombre, formas RV1909 o None = detectar, tipo, nota, forzar confianza baja)
# Van primero (el orden importa): los nombres compuestos («campos de Moab», «ciudad de Moab», «camino del mar
# Bermejo») se asignan antes que «Moab» o «mar Bermejo» de los libros anteriores.
_TRAD = "La RV1909 traduce el nombre: «{f}»."
LUGARES = {
    "aca767b": ("campos-de-moab", "Campos de Moab", ["campos de Moab"], "region",
                "Llanura al oriente del Jordán, frente a Jericó, donde acampa Israel (Nm 22:1).", False),
    "a6c0a5f": ("ir-moab", "Ir-moab (ciudad de Moab)", ["ciudad de Moab"], "ciudad", _TRAD.format(f="la ciudad de Moab"), False),
    "a55c970": ("camino-mar-rojo", "Camino del mar Rojo", ["camino del mar Bermejo"], "otro", "Ruta (Nm 14:25; 21:4).", False),
    "a057d59": ("camino-real", "Camino real", ["camino real"], "otro", "Ruta por la que Israel pide pasar por Edom (Nm 20:17) y por la tierra de Sehón (Nm 21:22).", False),
    "a7a59b4": ("torrente-de-egipto", "Torrente de Egipto", ["torrente de Egipto"], "rio", "Límite sur de la tierra (Nm 34:5).", False),
    "aa805fb": ("mar-grande", "Mar Grande (Mediterráneo)", ["gran mar"], "mar", "Límite occidental de la tierra (Nm 34:6).", False),
    "abed304": ("mar-salado", "Mar Salado (mar Muerto)", ["mar salado"], "mar", "", False),
    "a562fcc": ("mar-de-cineret", "Mar de Cineret (mar de Galilea)", ["mar de Cinnereth"], "mar", "", False),
    "a505743": ("meriba-cades", "Meriba de Cades", ["aguas de la rencilla"], "fuente",
                _TRAD.format(f="aguas de la rencilla") + " Distinta de Meriba de Refidim (Ex 17:7).", False),
    "ad8027f": ("monte-hor", "Monte Hor", ["Hor"], "monte", "Donde muere Aarón, «en los confines de la tierra de Edom» (Nm 20:23).", False),
    "a62fa2d": ("monte-hor-norte", "Monte Hor (límite norte)", ["Hor"], "monte",
                "Límite norte de la tierra (Nm 34:7-8); distinto del monte Hor donde muere Aarón.", False),
    "a39fe14": ("monte-sefer", "Monte Sefer", ["Sepher"], "campamento", "", False),
    "a5e36e6": ("hor-gidgad", "Hor-gidgad", ["Gidgad"], "campamento", "La RV1909 dice «monte de Gidgad».", False),
    "a577c27": ("bamot-baal", "Bamot-baal", ["altos de Baal"], "monte", _TRAD.format(f="los altos de Baal"), False),
    "aeb19d6": ("quiriat-huzot", "Quiriat-huzot", ["Husoth"], "ciudad", "La RV1909 dice «la ciudad de Husoth».", False),
    "a5eb047": ("lebo-hamat", "Lebo-hamat (entrada de Hamat)", ["Emath", "Hamath"], "ciudad",
                "La RV1909 dice «entrando en Emath» (Nm 13:22) y «la entrada de Hamath» (Nm 34:8).", False),
    "a38ecff": ("valle-de-escol", "Valle de Escol", ["Escol", "Nahal-escol"], "otro", "", False),
    "aaa2177": ("arroyo-de-zered", "Arroyo de Zered", ["Zared"], "rio", "La RV1909 escribe «arroyada de Zared».", False),
    "a6046fa": ("amon", "Amón", None, "region", "En Números «los hijos de Ammón» es el pueblo amonita; OpenBible lo registra como región.", False),
    "aa8275b": ("abarim", "Montes de Abarim", None, "monte", "", False),
    "a51d1fa": ("abel-sitim", "Abel-sitim", None, "campamento", "", False),
    "a7560c2": ("abrona", "Abrona", None, "campamento", "", False),
    "a89511f": ("ain", "Aín", None, "ciudad", "", False),
    "a39267b": ("acrabim", "Subida de Acrabim", None, "otro", "", False),
    "aeb052c": ("almon-diblataim", "Almón-diblataim", None, "campamento", "", False),
    "a32397f": ("alus", "Alús", None, "campamento", "", False),
    "a38ad07": ("ar", "Ar", None, "ciudad", "", False),
    "abc358b": ("arad", "Arad", None, "ciudad", "", False),
    "a3e66cd": ("aram", "Aram", None, "region", "", False),
    "a4cc324": ("arnon", "Arnón", None, "rio", "", False),
    "ae46f2e": ("aroer", "Aroer", None, "ciudad", "", False),
    "a874951": ("asur", "Asur", None, "ciudad", "En los oráculos de Balaam (Nm 24:22, 24). OpenBible lo identifica con la ciudad de Asur.", False),
    "abc9a1d": ("atarot", "Atarot", None, "ciudad", "", False),
    "afdb74b": ("atrot-sofan", "Atrot-sofán", None, "ciudad", "", False),
    "a8f6a28": ("azmon", "Azmón", None, "ciudad", "", False),
    "a76f7b7": ("baal-meon", "Baal-meón", None, "ciudad", "", False),
    "a1db553": ("bamot", "Bamot", None, "campamento", "", False),
    "aa7a40a": ("basan", "Basán", None, "region", "", False),
    "a656cb6": ("beer", "Beer", None, "campamento", "«El pozo» donde Dios da agua al pueblo (Nm 21:16).", False),
    "a0fe2be": ("bene-jaacan", "Bene-jaacán", None, "campamento", "", False),
    "a882ef5": ("beon", "Beón", None, "ciudad", "", False),
    "a4590cd": ("bet-haran", "Bet-arán", None, "ciudad", "", False),
    "a30f37b": ("bet-jesimot", "Bet-jesimot", None, "campamento", "", False),
    "af66b89": ("bet-nimra", "Bet-nimra", None, "ciudad", "", False),
    "a0d784a": ("dibon", "Dibón", None, "ciudad", "Nm 33:45-46 la llama «Dibon-gad» en el itinerario.", False),
    "a070c7b": ("dofca", "Dofca", None, "campamento", "", False),
    "aaa6f7a": ("edrei", "Edrei", None, "ciudad", "", False),
    "a5ccd34": ("eleale", "Eleale", None, "ciudad", "", False),
    "a8e53d5": ("ezion-geber", "Ezión-geber", None, "campamento", "", False),
    "a73af5f": ("harada", "Harada", None, "campamento", "", False),
    "aaa8a88": ("hasmona", "Hasmona", None, "campamento", "", False),
    "a26c8f2": ("havot-jair", "Havot-jair", None, "region", "Nombre que Jair da a las aldeas que toma (Nm 32:41).", False),
    "a3f301c": ("hasar-adar", "Hasar-adar", None, "ciudad", "", False),
    "a1ce1b7": ("hasar-enan", "Hasar-enán", None, "ciudad", "", False),
    "a1b6474": ("haserot", "Haserot", None, "campamento", "", False),
    "abf2fc1": ("hesbon", "Hesbón", None, "ciudad", "Ciudad de Sehón, rey de los amorreos (Nm 21:26).", False),
    "ada25df": ("horma", "Horma", None, "ciudad", "", False),
    "a0574da": ("ije-abarim", "Ije-abarim", None, "campamento", "", False),
    "ad9b1cd": ("jahaza", "Jahaza", None, "ciudad", "", False),
    "a095b6e": ("jazer", "Jazer", None, "ciudad", "", False),
    "a231f80": ("jerico", "Jericó", None, "ciudad", "", False),
    "ad41f6e": ("jesimon", "Jesimón", None, "region", "", False),
    "acf6e00": ("jogbeha", "Jogbeha", None, "ciudad", "", False),
    "a7384d7": ("jotbata", "Jotbata", None, "campamento", "", False),
    "a32d25a": ("ceelata", "Ceelata", None, "campamento", "", False),
    "a4f650b": ("kenat", "Kenat", None, "ciudad", "", False),
    "ae7836a": ("kibrot-hataava", "Kibrot-hataava", None, "campamento", "«Sepulcros de la codicia» (Nm 11:34).", False),
    "ad54201": ("quiriataim", "Quiriataim", None, "ciudad", "", False),
    "aeb46a8": ("quitim", "Quitim", None, "region", "En el último oráculo de Balaam (Nm 24:24).", False),
    "a3e94bd": ("libna", "Libna", None, "campamento", "", False),
    "ac1fbba": ("macelot", "Macelot", None, "campamento", "", False),
    "a033373": ("matana", "Matana", None, "campamento", "", False),
    "af4f21c": ("medeba", "Medeba", None, "ciudad", "", False),
    "aa5f658": ("mitca", "Mitca", None, "campamento", "", False),
    "a88331e": ("moserot", "Moserot", None, "campamento", "", False),
    "a8dafd6": ("nahaliel", "Nahaliel", None, "campamento", "", False),
    "ab5bd29": ("nebo", "Nebo", None, "ciudad", "", False),
    "a314731": ("nimra", "Nimra", None, "ciudad", "", False),
    "aed6b0e": ("nofa", "Nofa", None, "ciudad", "", False),
    "a0ef1e1": ("obot", "Obot", None, "campamento", "", False),
    "a9ef72b": ("peor", "Peor", None, "monte", "", False),
    "aa9e754": ("petor", "Petor", None, "ciudad", "Ciudad de Balaam, «junto al río» (Nm 22:5).", False),
    "afd9259": ("pisga", "Pisga", None, "monte", "", False),
    "a9ecc26": ("punon", "Punón", None, "campamento", "", False),
    "ae4cd38": ("rehob", "Rehob", None, "ciudad", "", False),
    "ac95bd8": ("ribla", "Ribla", None, "ciudad", "", False),
    "ac79b33": ("rimon-peres", "Rimón-peres", None, "campamento", "", False),
    "af04ad9": ("risa", "Risa", None, "campamento", "", False),
    "a2e73ba": ("ritma", "Ritma", None, "campamento", "", False),
    "a9ba60c": ("sefam", "Sefam", None, "ciudad", "", False),
    "af64fb3": ("sitim", "Sitim", None, "campamento", "", False),
    "aa10f27": ("sibma", "Sibma", None, "ciudad", "", False),
    "a028191": ("tabera", "Tabera", None, "campamento", "«Incendio» (Nm 11:3).", False),
    "abe40d1": ("tahat", "Tahat", None, "campamento", "", False),
    "a944b90": ("tare", "Tare", None, "campamento", "", False),
    "a1c6a50": ("salmona", "Salmona", None, "campamento", "", False),
    "aab92ca": ("zedad", "Zedad", None, "ciudad", "", False),
    "a0b5c50": ("desierto-de-zin", "Desierto de Zin", ["Zin"], "region", "Distinto del desierto de Sin (Ex 16:1).", False),
    "a190097": ("zin", "Zin (límite sur)", ["Zin"], "otro", "Punto del límite sur de la tierra (Nm 34:4).", False),
    "adf05b8": ("zifron", "Zifrón", None, "ciudad", "", False),
    "ac31fee": ("zoan", "Zoán", None, "ciudad", "«Zoán, la de Egipto» (Nm 13:23).", False),
    "ae7f7b5": ("zofim", "Campo de Zofim", None, "otro", "", False),
}
EXCLUIR_LUGAR = {
    "aa23a3e": ("Noba (Nm 32:42): es el nombre que Noba da a Kenat; en el versículo «Noba» se marca como la persona "
                "y el lugar va como Kenat."),
    "ac5cab3": "Amau (Nm 22:5): la RV1909 dice «la tierra de los hijos de su pueblo»; no nombra el lugar.",
    "a2c34ce": "Atarim (Nm 21:1): la RV1909 traduce «el camino de los centinelas»; no es nombre propio.",
    "ab0b2dd": "«Oriente» (Nm 23:7): la RV1909 dice «los montes del oriente»; no es nombre propio.",
    "a13cde9": "«Lugar santo» (Nm 28:7): es el santuario, no un lugar del mapa.",
    "a765bd8": "Caín/Quenitas (Nm 24:22): la RV1909 dice «el Cineo» (el pueblo ceneo); no se sitúa como lugar.",
    "a1cb244": "Néguev: la RV1909 traduce «mediodía» (el sur); no es nombre propio en este texto.",
    "a669096": "«El río» (Nm 22:5): la RV1909 no lo nombra; OpenBible lo identifica con el Éufrates (Fuente externa).",
    "a88bcb2": "Sufa (Nm 21:14): la RV1909 traduce de otro modo («lo que hizo en el mar Bermejo»); el nombre no aparece.",
    "adec54b": "Vaheb (Nm 21:14): la RV1909 traduce de otro modo («lo que hizo en el mar Bermejo»); el nombre no aparece.",
}
# «monte de Sinaí» y «desierto de Sinaí»; el monte Hor siempre va precedido de «monte de».
PRECEDIDO = {"abfba2a": "monte de ", "ae50cf1": "desierto de ", "ad8027f": "monte de ", "a62fa2d": "monte de "}
OBLIGATORIOS_LUGAR = ["sinai", "desierto-de-sinai", "cades", "monte-hor", "desierto-de-zin", "campos-de-moab", "jordan"]

# La cronología de Números (eventos desde la salida e hitos sin fecha) está en cronologia.py.


# Relaciones que Éxodo dejó como inferidas y que Números dice: pasan a explícitas con la cita de Números.
SUBE_A_EXPLICITO = [
    ("Amram_1", "Miriam_1", "padre", (26, 59), "parió de Amram á Aarón y á Moisés, y á María su hermana"),
    ("Jochebed_1", "Miriam_1", "madre", (26, 59), "ésta parió de Amram á Aarón y á Moisés, y á María su hermana"),
]


def construir(cx):
    for de, a, tipo, ref, cita in SUBE_A_EXPLICITO:
        x = next((x for x in cx["relaciones"] if (x["de"], x["a"], x["tipo"]) == (de, a, tipo)), None)
        if not x or cita not in cx["rv"].get(ref, ""):
            cx["errores"].append(f"Números: no se puede subir a explícita {de}→{a} ({LIBRO} {ref[0]}:{ref[1]})")
            continue
        antes = f"{x['ref']}, {x['certeza']}"
        x.update(ref=f"{LIBRO} {ref[0]}:{ref[1]}", certeza="explicito", fuente="rv1909", cita=cita,
                 nota=(f"Éxodo solo la llama «hermana de Aarón» (Ex 15:20; antes: {antes}); "
                       f"{LIBRO} {ref[0]}:{ref[1]} nombra a sus padres."))
    r = exodo.construir(cx, sys.modules[__name__])
    for c in r["capitulos"]:
        for v in c["versiculos"]:
            if (c["cap"], v["n"]) in VACIOS and not v["texto"]:
                v["nota"] = (f"La RV1909 no tiene este versículo aparte: numera el capítulo de otra forma y su texto "
                             f"está en {VACIOS[(c['cap'], v['n'])]}.")
    return r


def construir_lugares(rv, menciones_personas, rutas, lugares_previos, errores, avisos, sa):
    return exodo.construir_lugares(rv, menciones_personas, rutas, lugares_previos, errores, avisos, sa,
                                   sys.modules[__name__])


# ---------------------------------------------------------------- hechos obligatorios (sobre los datos finales)
def comprobar(datos, errores):
    """Comprueba los hechos pedidos para Números (falla si falta alguno). Devuelve líneas de informe."""
    P = {p["id"]: p for p in datos["personas"]}
    R = {(x["de"], x["a"], x["tipo"]): x for x in datos["relaciones"]}
    caps = [c for c in datos["capitulos"] if c["libro"] == LIBRO]
    texto = {f"{LIBRO} {c['cap']}:{v['n']}": v["texto"] for c in caps for v in c["versiculos"]}
    M = {(m["ref"], m["persona"]) for m in datos["menciones"]}
    lineas = []

    def ok_(cond, desc):
        lineas.append(f"{'OK ' if cond else 'FALTA'} {desc}")
        if not cond:
            errores.append(f"Hecho obligatorio (Números): {desc}")

    ok_(len(caps) == CAPITULOS and len(texto) == VERSICULOS,
        f"{CAPITULOS} capítulos y {VERSICULOS} versículos (hay {len(caps)} y {len(texto)})")
    vacios = [r for r, t in texto.items() if not t]
    ok_(sorted(vacios) == sorted(f"Nm {c}:{v}" for c, v in VACIOS), f"versículos vacíos solo {sorted(VACIOS)} ({vacios})")

    def tiene(pid, ref, mencion=True):
        return ref in P.get(pid, {}).get("refs", []) and (not mencion or (ref, pid) in M)

    def rel(de, a, tipo, ref=None, certeza="explicito", nota=None):
        x = R.get((de, a, tipo))
        c = bool(x) and x["certeza"] == certeza and (ref is None or x["ref"] == ref) and (nota is None or nota in x["nota"])
        ok_(c, f"{de}→{a} {tipo}" + (f" {ref}" if ref else "") + (f" (nota con {nota})" if nota else "")
            + (f" [hay {x['ref']} {x['certeza']}]" if x and not c else ""))
        if x and x.get("cita") and x["cita"] not in texto.get(x["ref"], "") and x["ref"].startswith("Nm "):
            ok_(False, f"cita literal de {de}→{a} en {x['ref']}")

    # Coré, hijo de Izhar (RV «Ishar»), distinto del Coré de Gn 36
    ok_(tiene("Korah_3", "Nm 16:1") and "Ishar" in texto["Nm 16:1"], "Coré (Korah_3) con ref y mención en Nm 16:1")
    rel("Izhar_1", "Korah_3", "padre", nota="Nm 16:1")
    k1 = P.get("Korah_1", {})
    ok_(bool(k1) and not any(r.startswith("Nm ") for r in k1["refs"]) and ("Gn 36:5" in k1["refs"]),
        "Coré hijo de Esaú (Korah_1) sigue en Gn 36 y sin refs de Números")
    for h in ("Dathan_1", "Abiram_1"):
        ok_(tiene(h, "Nm 16:1"), f"{h} con ref y mención en Nm 16:1")
        rel("Eliab_2", h, "padre", "Nm 16:1")
    ok_("Eliab_1" in P and "Eliab_2" in P and "Nm 16:1" not in P["Eliab_1"]["refs"], "dos Eliab distintos (Zabulón / Rubén)")
    # Balaam y Balac
    ok_(tiene("Balaam_1", "Nm 22:5") and tiene("Beor_2", "Nm 22:5"), "Balaam y Beor en Nm 22:5")
    rel("Beor_2", "Balaam_1", "padre", "Nm 22:5")
    ok_(tiene("Balak_1", "Nm 22:2") and tiene("Zippor_1", "Nm 22:2") and P["Balak_1"]["nombre_rv1909"] == "Balac",
        "Balac y Zippor en Nm 22:2")
    rel("Zippor_1", "Balak_1", "padre", "Nm 22:2")
    # Las cinco hijas de Zelofehad
    v271 = texto.get("Nm 27:1", "")
    for h in ("Mahlah_1", "Noah_2", "Hoglah_1", "Milcah_2", "Tirzah_1"):
        p = P.get(h, {})
        ok_(p.get("sexo") == "f" and tiene(h, "Nm 27:1") and p.get("nombre_rv1909", "") in v271,
            f"{h} ({p.get('nombre_rv1909')}) hija de Zelofehad con ref y mención en Nm 27:1")
        rel("Zelophehad_1", h, "padre", "Nm 26:33")
    ok_(tiene("Zelophehad_1", "Nm 27:1") and "Salphaad" in v271, "Zelofehad (RV «Salphaad») en Nm 27:1")
    rel("Hepher_1", "Zelophehad_1", "padre", "Nm 26:33")
    m1 = P.get("Milcah_1", {})
    ok_(bool(m1) and "Gn 11:29" in m1["refs"] and not any(r.startswith("Nm ") for r in m1["refs"])
        and "Nm 27:1" in P.get("Milcah_2", {}).get("refs", []), "Milca hija de Zelofehad ≠ Milca mujer de Nacor (Gn 11:29)")
    # Finees, el mismo de Ex 6:25
    ok_(tiene("Phinehas_1", "Nm 25:7") and "Ex 6:25" in P["Phinehas_1"]["refs"], "Finees de Nm 25:7 = Finees de Ex 6:25")
    rel("Eleazar_1", "Phinehas_1", "padre", "Ex 6:25", nota="Nm 25:7")
    # Josué hijo de Nun (= Oseas) y Caleb hijo de Jefone (RV1909: Nm 13:9, 13:7, 13:17)
    j = P.get("Joshua_1", {})
    ok_(tiene("Joshua_1", "Nm 13:9") and tiene("Joshua_1", "Nm 13:17") and "Oseas" in j.get("formas_rv1909", [])
        and j.get("identidad", {}).get("certeza") == "texto"
        and {"Nm 13:9", "Nm 13:17"} <= set(j.get("identidad", {}).get("refs", [])),
        "Josué = Oseas (Nm 13:9 y 13:17 en la RV1909; 13:8 y 13:16 en la inglesa), identidad de texto")
    rel("Nun_1", "Joshua_1", "padre", nota="Nm 13:9")
    ok_(tiene("Caleb_1", "Nm 13:7") and tiene("Jephunneh_1", "Nm 13:7"), "Caleb y Jefone en Nm 13:7 (13:6 inglesa)")
    rel("Jephunneh_1", "Caleb_1", "padre", "Nm 13:7")
    # Homónimos: Hur rey de Madián ≠ Hur de Éxodo
    ok_(tiene("Hur_2", "Nm 31:8") and not any(r.startswith("Nm ") for r in P.get("Hur_1", {}).get("refs", [])),
        "Hur rey de Madián (Nm 31:8) ≠ Hur de Éxodo")
    # Muerte de María en Cades y de Aarón en el monte Hor
    L = {l["id"]: l for l in datos["lugares"]}
    ok_(tiene("Miriam_1", "Nm 20:1") and "Nm 20:1" in L.get("cades", {}).get("refs", []) and "murió María" in texto["Nm 20:1"],
        "muerte de María en Cades (Nm 20:1)")
    ok_(tiene("Aaron_1", "Nm 20:28") and "Aarón murió allí" in texto["Nm 20:28"]
        and {"Nm 20:22", "Nm 20:25", "Nm 33:38", "Nm 33:39"} <= set(L.get("monte-hor", {}).get("refs", [])),
        "muerte de Aarón en el monte Hor (Nm 20:28; 33:38-39)")
    # Edad de Aarón al morir: 123 en TM y LXX, con cita
    ed = {e["tradicion"]: e for e in datos["edades"] if e["persona"] == "Aaron_1" and e["ref"] == "Nm 33:39"}
    ok_(set(ed) == {"TM", "LXX"} and all(e["valor"] == 123 and e["tipo"] == "total" for e in ed.values())
        and ed["TM"]["cita"] in texto["Nm 33:39"], "Aarón muere a los 123 años (Nm 33:39, TM y LXX con cita)")
    # 83 (Ex 7:7) → 123 (Nm 33:39): cuadra con la cronología
    e77 = [e for e in datos["edades"] if e["persona"] == "Aaron_1" and e["ref"] == "Ex 7:7" and e["tradicion"] == "TM"]
    EV = {e["id"]: e for e in datos["cronologia"]["eventos"]}
    mu, sa_ = EV.get("ev-muerte-aaron"), EV.get("ev-salida-egipto")
    c = "TM|tare70|sem2|egipto"
    if e77 and mu and sa_ and ed.get("TM"):
        trans = mu["anios"][c] - sa_["anios"][c]
        ok_(e77[0]["valor"] == 83 and e77[0]["valor"] + trans == ed["TM"]["valor"],
            f"edad de Aarón: 83 (Ex 7:7) + {trans} años (salida → Nm 33:38) = {e77[0]['valor'] + trans} = 123 (Nm 33:39)")
        c2 = "LXX|tare70|sem2|egipto"
        t2 = mu["anios"][c2] - EV["ev-salida-egipto"]["anios"][c2]
        ok_(0 <= ed["LXX"]["valor"] - (83 + t2) <= 1, f"LXX: 83 + {t2} = {83 + t2}, texto 123 (margen de un año, ver nota)")
    else:
        ok_(False, "edad de Aarón 83 → 123: faltan datos (Ex 7:7, ev-muerte-aaron o Nm 33:39)")
    for eid in ("ev-censo-sinai", "ev-salida-sinai", "ev-muerte-aaron"):
        e = EV.get(eid)
        ok_(bool(e) and e["certeza"] == "calculo" and e["ref"].startswith("Nm ") and e["pasos"]
            and e["depende_de"] == "ev-salida-egipto", f"evento de cronología {eid} (cálculo desde la salida)")
    ok_(EV.get("ev-censo-sinai", {}).get("anios", {}).get(c, 0) - EV["ev-salida-egipto"]["anios"][c] == 1,
        "censo del Sinaí: un año después de la salida (Nm 1:1, «el segundo año»)")
    ok_(any(h["ref"] == "Nm 20:1" for h in datos["cronologia"]["hitos_sin_fecha"]), "muerte de María como hito sin fecha (Nm 20:1)")
    # Formas RV1909 literales: cada persona nueva de Números aparece tal cual en alguna de sus refs de Nm
    for p in datos["personas"]:
        if p["sin_nombre"] or not p.get("nombre_rv1909") or not any(r.startswith("Nm ") for r in p["refs"]):
            continue
        if not any(r.startswith(("Gn ", "Ex ", "Lv ")) for r in p["refs"]):
            ok_(any(p["nombre_rv1909"] in texto.get(r, "") for r in p["refs"]),
                f"forma literal «{p['nombre_rv1909']}» de {p['id']}")
    # Pasajes y secciones
    pas = [p for p in datos["pasajes"] if p["libro"] == LIBRO]
    ok_(len(pas) == len(PASAJES) and pas[0]["inicio"] == "Nm 1:1" and pas[-1]["fin"] == "Nm 36:13",
        f"{len(pas)} pasajes nm-NN de Nm 1:1 a Nm 36:13")
    ok_(len({p["seccion"] for p in pas}) == 8, "8 secciones")
    # Lugares
    for lid in OBLIGATORIOS_LUGAR:
        l = L.get(lid)
        ok_(bool(l) and any(r.startswith("Nm ") for r in l["refs"]),
            f"lugar {lid} con refs de Números ({sum(1 for r in l['refs'] if r.startswith('Nm ')) if l else 0})")
    return lineas
