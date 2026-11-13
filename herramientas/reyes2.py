"""2 Reyes 1–25: personas, relaciones, edades, pasajes, menciones y lugares (lo usa construir_datos.py).

Id del libro: «2R» (el código canónico de CANON en app.js). Reutiliza la lógica de exodo.py (exodo.construir /
exodo.construir_lugares con este módulo como configuración) y la detección automática de lugares de josue.py
(josue.lugares_auto), como 1 Reyes. Cada dato lleva versículo, fuente y certeza; las citas se comprueban literalmente
contra la RV1909 (TM) o Brenton (LXX). Las personas de Génesis–1 Reyes (Elías, Eliseo, Acab, Jezabel, Jehú, Hazael,
Ben-adad, Joram hijo de Josafat, Ocozías hijo de Acab, Josafat, Omri, Josías…) son la misma persona (mismo id de
BibleData): se amplían sus `refs`.

Versificación (comprobada al generar, versículo a versículo; detalle en datos/LEEME.md, «2 Reyes: decisiones»):
- La RV1909 de eBible tiene 719 versículos con los recuentos de la numeración inglesa (la de BibleData y OpenBible):
  11:21 «Era Joas de siete años» es versículo propio (el hebreo y la LXX lo numeran 12:1) y 12 tiene 21 versículos
  (hebreo y LXX 12:2-22). TVTMS (STEPBible) confirma que en 2 Reyes es la única diferencia entre la numeración inglesa
  y la hebrea; se comprueba al generar. No hay `REMAP_REF`: BibleData y OpenBible numeran igual que la RV1909.
- Brenton («4 Kingdoms») sigue la numeración hebrea en 11–12 y tiene los 719 versículos. `br_a_rv` (único punto de
  versificación de Brenton) lleva su 12:1 a 11:21 y su 12:2-22 a 12:1-21; después se comprueba capítulo a capítulo que
  el emparejamiento sin desfase compara mejor que con desfase ±1, que nombres poco frecuentes caen en los mismos
  versículos, los extremos y la proporción de longitudes.

Solo biblioteca estándar.
"""
import math
import re
import sys
from pathlib import Path

import exodo
import josue

LIBRO = "2R"
NOMBRE = "2 Reyes"
USX = "2KI"
CAPITULOS = 25
VERSICULOS = 719
POR_CAPITULO = [18, 25, 27, 44, 27, 33, 20, 29, 37, 36, 21, 21, 25, 29, 38, 20, 41, 37, 37, 21, 26, 20, 37, 20, 30]
VACIOS = {}
# Comienzo y final de los versículos de la zona donde el hebreo (y la LXX) numeran distinto del inglés (se comprueban).
VERSIFICACION = [((11, 20), "Y todo el pueblo de la tierra hizo alegrías"), ((11, 21), "Era Joas de siete años"),
                 ((12, 1), "EN el séptimo año de Jehú comenzó á reinar Joas"), ((12, 2), "Y Joas hizo lo recto"),
                 ((12, 21), "Pues Josachâr hijo de Simaath"), ((13, 1), "EN el año veintitrés de Joas")]
FIN_VERSICULO = [((11, 21), "cuando comenzó á reinar."), ((12, 21), "y reinó en su lugar Amasías su hijo.")]
# Brenton, ya en numeración RV1909 (tras br_a_rv).
VERSIFICACION_LXX = [((11, 20), "they slew Gotholia with the sword"), ((11, 21), "Joas [was] seven years old"),
                     ((12, 1), "Joas began to reign in the seventh year of Ju"),
                     ((12, 21), "Jezirchar the son of Jemuath"), ((13, 1), "In the twenty-third year of Joas")]
SIN_LXX = set()
# Nombres que deben caer en los mismos versículos en la RV1909 y en Brenton.
PARALELOS = [("Sennachêrib", "Sennacherim"), ("Jezabel", "Jezabel"), ("Nabucodonosor", "Nabuchodonosor"),
             ("Gedalías", "Godolias"), ("Manasés", "Manasses"), ("Josías", "Josias"), ("Amasías", "Amessias"),
             ("Sedecías", "Sedekias"), ("Oseas", "Osee"), ("Peka", "Phakee")]
PROPORCION = (0.35, 3.0)  # longitud RV1909 / Brenton por versículo (observado 0,40 en 10:21 – 2,72 en 1:17)
# TVTMS: bloques de 2 Reyes donde la numeración inglesa y la hebrea difieren (se comprueba que no haya otros).
TVTMS_2R = {"2Ki.11:21--12:21"}


def br_a_rv(br):
    """Brenton (4 Reinos) -> numeración de la RV1909. Único punto de versificación de Brenton: la LXX numera 11–12 como
    el hebreo (su 12:1 «Joas [was] seven years old» es el 11:21 inglés; su 12:2-22 es el 12:1-21)."""
    out = {}
    for (c, v), t in sorted(br.items()):
        k = (11, 21) if (c, v) == (12, 1) else (12, v - 1) if c == 12 else (c, v)
        out[k] = f"{out[k]} {t}" if k in out else t
    return out


# ---------------------------------------------------------------- identidades
# Ids propios (acaban en «_número» para que exodo.construir los acepte como ids de persona).
SUNAMITA = "Shunammite_2R4_1"      # la sunamita (4:8-37; 8:1-6), sin nombre
MAACATI = "Maachathi_2R25_1"       # «Maachâti», padre de Jaazanías (25:23)
_MAACATI = ("2 R 25:23: «Jaazanías hijo de Maachâti». La RV1909 lo escribe como nombre propio; BibleData lo toma por "
            "gentilicio («el maacateo») y lo identifica con Osaías, padre de Jezanías (Jer 42:1, libro aún no cargado). "
            "Se registra como lo da la RV1909, con id propio (Maachathi_2R25_1).")
_SO = ("2 R 18:21: Rabsaces habla de «Faraón rey de Egipto» en tiempos de Ezequías; BibleData lo identifica con So (17:4, "
       "en tiempos de Oseas). El texto no lo dice: no se marca como So.")
_JORAM_3 = ("En 2 R 3 el rey de Judá que va con Joram de Israel contra Moab es Josafat (3:7 y 3:14: «Josaphat rey de "
            "Judá»); BibleData pone ahí a Joram de Judá (Jehoram_1). Se descarta.")
# (id de BibleData, ref RV1909) -> id con que se usa aquí. Único punto de reasignación de BibleData-PersonVerse.
PV_REASIGNAR = {("Hoshaiah_2", (25, 23)): MAACATI}
SEXO_PROPIO = {MAACATI: "m"}

# Personas de BibleData que no se crean: Dios, «NA», el ángel de Jehová (1:3, 15; 19:35) y los reyes sin nombre
# («King of Edom/Assyria/Hamath/Arpad/Sepharvaim/Hena/Ivvah»), como en los libros anteriores. BibleData no toma por
# personas a los pueblos en 2 Reyes (moabitas, sirios, caldeos… no tienen filas).
EXCLUIR = {"YHVH_1", "NA", "the angel of the LORD_1", "King of Edom_2", "King of Assyria_1", "King of Hamath_1",
           "King of Arpad_1", "King of Sepharvaim_1", "King of Hena_1", "King of Ivvah_1"}
# «Israel» es el pueblo: Jacob solo si el texto dice «Jacob» (13:23; 17:34).
SOLO_ETIQUETA = {"Jacob_1": {"Jacob"}}
FORMA_NO_MENCION = {("Jacob_1", "israel")}
PV_DESCARTAR = {("So_1", (18, 21)): _SO, ("Jehoram_1", (3, 7)): _JORAM_3, ("Jehoram_1", (3, 9)): _JORAM_3,
                ("Jehoram_1", (3, 14)): _JORAM_3}
_ATALIA = ("2 R 8:18 dice de Joram de Judá que «una hija de Achâb fué su mujer», sin nombrarla; 8:26 llama a Atalía, "
           "madre de Ocozías hijo de Joram, «hija de Omri rey de Israel», y 1 R 16:28 hace a Acab hijo de Omri. Se "
           "registra lo que dice cada versículo: Omri padre (8:26, texto) y Acab padre (8:18, inferido: el texto no "
           "nombra a la hija). No se armoniza.")
_SIMEAT = ("2 R 12:21 dice «hijo de Simaath» y «hijo de Somer» sin decir si son el padre o la madre; BibleData los hace "
           "madres (por 2 Cr 24:26, libro aún no cargado, que las llama amonita y moabita): inferido.")
REL_DESCARTAR = {}
NOTAS_REL = {
    ("Ahab_1", "Athaliah_1", "padre"): _ATALIA,
    ("Athaliah_1", "Jehoram_1", "conyuge"): ("2 R 8:18: «una hija de Achâb fué su mujer»; 8:26: Atalía es madre de "
                                             "Ocozías hijo de Joram (8:24-25). Que esa hija sea Atalía es inferido."),
    ("Shimeath_1", "Jozacar_1", "madre"): _SIMEAT, ("Shomer_1", "Jehozabad_1", "madre"): _SIMEAT,
    ("Josiah_1", "Mattaniah_1", "padre"): ("2 R 24:17 llama a Matanías «tío» de Joaquín (hijo de Joacim, hijo de Josías), "
                                          "y 24:18 le da la misma madre que a Joacaz hijo de Josías (23:31): que sea hijo "
                                          "de Josías es inferido (BibleData)."),
}
FORMAS_FORZADAS = {
    "Jehu_2": ["Jehú"], "Elisha_1": ["Eliseo"], "Ahab_1": ["Achâb"], "Ahaziah_1": ["Ochôzías"],
    "Ahaziah_2": ["Ochôzías"], "Jehoram_1": ["Joram"], "Jehoram_2": ["Joram"], "Jehoshaphat_3": ["Josaphat"],
    "Jehoshaphat_4": ["Josaphat"], "Ben-hadad_1": ["Ben-adad"], "Ben-hadad_2": ["Ben-adad"], "Arieh_1": ["Ariph"],
    "Pharaoh Neco_1": ["Faraón Nechâo", "Faraón"], "Azariah_3": ["Azarías", "Uzzía"], "Eliakim_2": ["Eliacim", "Joacim"],
    "Mattaniah_1": ["Mathanías", "Sedecías"], "Jehoiachin_1": ["Joachîn"], "Jehoahaz_1": ["Joachâz"],
    "Jehoahaz_2": ["Joachâz"], "Joash_3": ["Joas"], "Joash_4": ["Joas"], MAACATI: ["Maachâti"], "So_1": ["So"],
    "Hoshea_1": ["Oseas"], "Tiglath-pileser_1": ["Tiglath-pileser"], "Nebuchadnezzar_1": ["Nabucodonosor"],
    "Sennacherib_1": ["Sennachêrib"], "Rabshakeh_1": ["Rabsaces"], "Tartan_1": ["Thartán"], "Rab-saris_1": ["Rabsaris"],
    "Shebnah_1": ["Sebna"], "Hezekiah_1": ["Ezechîas"], "Isaiah_1": ["Isaías"], "Amoz_1": ["Amós"],
    "Esarhaddon_1": ["Esar-hadón"], "Adrammelech_1": ["Adramelech"], "Sharezer_1": ["Saresar"], "Jacob_1": ["Jacob"],
    "Berodach-baladan_1": ["Berodach-baladán"], "Baladan_1": ["Baladán"], "Tirhakah_1": ["Thiraca"],
    "Jedidah_1": ["Idida"], "Harhas_1": ["Araas"], "Hamutal_1": ["Amutal"], "Zebidah_1": ["Zebuda"],
    "Nehushta_1": ["Neusta"], "Jehoaddin_1": ["Joaddan"], "Jehosheba_1": ["Josaba"], "Zibiah_1": ["Sibia"],
    "Jozacar_1": ["Josachâr"], "Shimeath_1": ["Simaath"], "Jehozabad_1": ["Jozabad"], "Shomer_1": ["Somer"],
    "Jehonadab_1": ["Jonadab"], "Rechab_2": ["Rechâb"], "Menachem_1": ["Manahem"], "Pul_1": ["Phul"],
    "Pekahiah_1": ["Pekaía"], "Remaliah_1": ["Remalías"], "Rezin_1": ["Resín"], "Ahaz_1": ["Achâz"],
    "Urijah_1": ["Urías"], "Shalmaneser_1": ["Salmanasar"], "Zechariah_1": ["Zachârías"], "Zechariah_2": ["Zachârías"],
    "Jecoliah_1": ["Jecolía"], "Jotham_2": ["Jotham"], "Shallum_1": ["Sallum"], "Shallum_2": ["Sallum"],
    "Jabesh_1": ["Jabes"], "Jerusha_1": ["Jerusa"], "Zadok_2": ["Sadoc"], "Elah_3": ["Ela"], "Meshullemeth_1": ["Mesalemeth"],
    "Haruz_1": ["Harus"], "Adaiah_1": ["Adaía"], "Shaphan_1": ["Saphán"], "Azaliah_1": ["Azalía"],
    "Meshullam_1": ["Mesullam"], "Hilkiah_1": ["Hilcías"], "Hilkiah_2": ["Hilcías"], "Ahikam_1": ["Ahicam"],
    "Achbor_2": ["Achbor"], "Micaiah_2": ["Michâía"], "Asaiah_1": ["Asaía"], "Huldah_1": ["Hulda"], "Tikvah_1": ["Ticva"],
    "Joshua_3": ["Josué"], "Nathan-melech_1": ["Nathan-melech"], "Jeremiah_1": ["Jeremías"], "Pedaiah_1": ["Pedaia"],
    "Elnathan_1": ["Elnathán"], "Nebuzaradan_1": ["Nabuzaradán"], "Seraiah_2": ["Saraías"], "Seraiah_3": ["Saraía"],
    "Zephaniah_1": ["Sophonías"], "Gedaliah_1": ["Gedalías"], "Ishmael_2": ["Ismael"], "Nethaniah_1": ["Nathanías"],
    "Johanan_1": ["Johanán"], "Kareah_1": ["Carea"], "Tanhumeth_1": ["Tanhumet"], "Jaazaniah_1": ["Jaazanías"],
    "Elishama_3": ["Elisama"], "Evil-merodach_1": ["Evil-merodach"], "Eliakim_1": ["Eliacim"], "Joah_1": ["Joah"],
    "Asaph_1": ["Asaph"], "Hephzibah_1": ["Hepsiba"], "Manasseh_3": ["Manasés"], "Amon_2": ["Amón"], "Uzza_1": ["Uzza"],
    "Amaziah_1": ["Amasías"], "Jehoiada_2": ["Joiada"], "Mattan_1": ["Mathán"], "Gehazi_1": ["Giezi"],
    "Naaman_2": ["Naamán"], "Mesha_1": ["Mesa"], "Bidkar_1": ["Bidkar"], "Jonah_1": ["Jonás"], "Amittai_1": ["Amittai"],
    "Gadi_1": ["Gadi"], "Pekah_1": ["Peka"], "Argob_1": ["Argob"], "Abi_1": ["Abi"], "Jeroboam_2": ["Jeroboam"],
    "Athaliah_1": ["Athalía"], "Josiah_1": ["Josías"],
}
MODERNO = {
    "Jehoram_2": "Joram", "Mesha_1": "Mesa", "Gehazi_1": "Giezi", "Naaman_2": "Naamán", "Ahaziah_2": "Ocozías",
    "Athaliah_1": "Atalía", "Jehoshaphat_4": "Josafat", "Bidkar_1": "Bidcar", "Jehonadab_1": "Jonadab",
    "Rechab_2": "Recab", "Jehoahaz_1": "Joacaz", "Jehosheba_1": "Josaba", "Joash_3": "Joás", "Jehoiada_2": "Joiada",
    "Mattan_1": "Matán", "Zibiah_1": "Sibia", "Jozacar_1": "Josacar", "Shimeath_1": "Simeat", "Jehozabad_1": "Jozabad",
    "Shomer_1": "Somer", "Amaziah_1": "Amasías", "Ben-hadad_2": "Ben-adad", "Joash_4": "Joás", "Jeroboam_2": "Jeroboam",
    "Jehoaddin_1": "Joadán", "Azariah_3": "Azarías", "Jonah_1": "Jonás", "Amittai_1": "Amitai",
    "Zechariah_1": "Zacarías", "Jecoliah_1": "Jecolías", "Jotham_2": "Jotam", "Shallum_1": "Salum", "Jabesh_1": "Jabes",
    "Menachem_1": "Manahem", "Gadi_1": "Gadi", "Pul_1": "Pul", "Pekahiah_1": "Pekaía", "Pekah_1": "Peka",
    "Remaliah_1": "Remalías", "Argob_1": "Argob", "Arieh_1": "Arie", "Tiglath-pileser_1": "Tiglat-pileser",
    "Hoshea_1": "Oseas", "Elah_3": "Ela", "Jerusha_1": "Jerusa", "Zadok_2": "Sadoc", "Rezin_1": "Rezín",
    "Ahaz_1": "Acaz", "Urijah_1": "Urías", "Hezekiah_1": "Ezequías", "Shalmaneser_1": "Salmanasar", "So_1": "So",
    "Abi_1": "Abi", "Zechariah_2": "Zacarías", "Sennacherib_1": "Senaquerib", "Tartan_1": "Tartán",
    "Rab-saris_1": "Rabsaris", "Rabshakeh_1": "Rabsaces", "Eliakim_1": "Eliaquim", "Hilkiah_1": "Hilcías",
    "Shebnah_1": "Sebna", "Joah_1": "Joa", "Asaph_1": "Asaf", "Isaiah_1": "Isaías", "Amoz_1": "Amoz",
    "Tirhakah_1": "Tirhaca", "Adrammelech_1": "Adramelec", "Sharezer_1": "Sarezer", "Esarhaddon_1": "Esar-hadón",
    "Berodach-baladan_1": "Berodac-baladán", "Baladan_1": "Baladán", "Manasseh_3": "Manasés", "Hephzibah_1": "Hepsiba",
    "Uzza_1": "Uza", "Amon_2": "Amón", "Meshullemeth_1": "Mesulemet", "Haruz_1": "Haruz", "Jedidah_1": "Jedida",
    "Adaiah_1": "Adaía", "Shaphan_1": "Safán", "Azaliah_1": "Azalía", "Meshullam_1": "Mesulam", "Hilkiah_2": "Hilcías",
    "Ahikam_1": "Ahicam", "Achbor_2": "Acbor", "Micaiah_2": "Micaías", "Asaiah_1": "Asaías", "Huldah_1": "Hulda",
    "Shallum_2": "Salum", "Tikvah_1": "Ticva", "Harhas_1": "Harhas", "Joshua_3": "Josué", "Nathan-melech_1": "Natán-melec",
    "Pharaoh Neco_1": "Faraón Necao", "Jehoahaz_2": "Joacaz", "Hamutal_1": "Hamutal", "Jeremiah_1": "Jeremías",
    "Eliakim_2": "Eliaquim", "Zebidah_1": "Zebuda", "Pedaiah_1": "Pedaías", "Nebuchadnezzar_1": "Nabucodonosor",
    "Jehoiachin_1": "Joaquín", "Nehushta_1": "Nehusta", "Elnathan_1": "Elnatán", "Mattaniah_1": "Matanías",
    "Nebuzaradan_1": "Nabuzaradán", "Seraiah_2": "Seraías", "Zephaniah_1": "Sofonías", "Gedaliah_1": "Gedalías",
    "Ishmael_2": "Ismael", "Nethaniah_1": "Netanías", "Johanan_1": "Johanán", "Kareah_1": "Carea", "Seraiah_3": "Seraías",
    "Tanhumeth_1": "Tanhumet", "Jaazaniah_1": "Jaazanías", MAACATI: "Maacati", "Elishama_3": "Elisama",
    "Evil-merodach_1": "Evil-merodac",
}
_CARGOS = ("En la RV1909 aparecen como nombres propios («á Thartán y á Rabsaris y á Rabsaces», 2 R 18:17). Fuente "
           "externa: los diccionarios bíblicos de dominio público (Easton, Smith) los explican como títulos de cargos "
           "asirios, no como nombres. Se registran como los da el texto, igual que «Faraón».")
NOTAS = {
    "Jehoram_2": ("Hijo de Acab, rey de Israel en Samaria doce años (2 R 3:1); su madre es Jezabel (9:22). Jehú lo mata "
                  "en la heredad de Nabot (9:24). Distinto de Joram hijo de Josafat, rey de Judá. BibleData le atribuye "
                  "también «el rey de Israel» sin nombre de 2 R 5–7."),
    "Ahaziah_2": "Hijo de Joram y de Atalía, rey de Judá un año (2 R 8:25-26). Distinto de Ocozías hijo de Acab, rey de Israel.",
    "Athaliah_1": "Madre de Ocozías de Judá; reina seis años sobre el país (2 R 11:3). " + _ATALIA,
    "Jehoshaphat_4": ("Padre de Jehú, hijo de Nimsi (2 R 9:2, 14). Distinto del rey Josafat hijo de Asa (Jehoshaphat_3) y "
                      "de los Josafat de 1 Reyes."),
    "Joash_3": "Hijo de Ocozías, rey de Judá (2 R 11:2, 21; 12:1). Distinto de Joás hijo de Joacaz, rey de Israel (13:10).",
    "Joash_4": "Hijo de Joacaz, rey de Israel (2 R 13:9-10). Distinto de Joás hijo de Ocozías, rey de Judá.",
    "Jehoahaz_1": "Hijo de Jehú, rey de Israel (2 R 10:35; 13:1). Distinto de Joacaz hijo de Josías, rey de Judá (23:30).",
    "Jehoahaz_2": "Hijo de Josías, rey de Judá tres meses (2 R 23:30-31). Distinto de Joacaz hijo de Jehú, rey de Israel.",
    "Jeroboam_2": "Hijo de Joás, rey de Israel cuarenta y un años (2 R 14:23). Distinto de Jeroboam hijo de Nabat.",
    "Ben-hadad_2": "Hijo de Hazael, rey de Siria (2 R 13:3, 24). Distinto del Ben-adad de 1 R 15 y 20 y de 2 R 6–8.",
    "Azariah_3": ("Hijo de Amasías, rey de Judá (2 R 14:21; 15:1); leproso hasta su muerte (15:5). 2 R 15:13, 30, 32 y 34 "
                  "lo llaman «Uzzía» (ver identidad)."),
    "Zechariah_1": "Hijo de Jeroboam, rey de Israel seis meses (2 R 15:8). Distinto de Zacarías padre de Abi (18:2).",
    "Zechariah_2": "Padre de Abi, madre de Ezequías (2 R 18:2). Distinto del rey Zacarías.",
    "Eliakim_1": "Hijo de Hilcías, mayordomo de Ezequías (2 R 18:18). Distinto de Eliaquim hijo de Josías (Joacim).",
    "Eliakim_2": "Hijo de Josías; Faraón Necao le cambia el nombre por Joacim (2 R 23:34). Distinto del mayordomo de Ezequías.",
    "Hilkiah_1": "Padre de Eliaquim el mayordomo (2 R 18:18). Distinto de Hilcías sumo sacerdote (22:4).",
    "Hilkiah_2": "Sumo sacerdote en tiempos de Josías; halla el libro de la ley (2 R 22:8). Distinto del padre de Eliaquim.",
    "Shallum_1": "Hijo de Jabes; reina un mes en Samaria (2 R 15:13). Distinto de Salum marido de Hulda.",
    "Shallum_2": "Marido de Hulda, «guarda de las vestiduras» (2 R 22:14). Distinto del rey Salum.",
    "Seraiah_2": "«Saraías primer sacerdote» (2 R 25:18). Distinto de Seraías hijo de Tanhumet (25:23).",
    "Seraiah_3": "Hijo de Tanhumet netofatita, de los príncipes del ejército (2 R 25:23). Distinto del primer sacerdote.",
    "Manasseh_3": "Hijo de Ezequías, rey de Judá (2 R 20:21; 21:1). Distinto de Manasés hijo de José.",
    "Amon_2": "Hijo de Manasés, rey de Judá (2 R 21:18-19). Distinto de Amón gobernador de la ciudad (1 R 22:26).",
    "Uzza_1": "Dueño del huerto donde se sepulta a Manasés y a Amón (2 R 21:18, 26). Distinto de Uza de 2 S 6.",
    "Zadok_2": "Padre de Jerusa, madre de Jotam (2 R 15:33). Distinto del sacerdote Sadoc de David.",
    "Micaiah_2": "Padre de Acbor (2 R 22:12). Distinto del profeta Micaías hijo de Imla (1 R 22).",
    "Joshua_3": "«Josué, gobernador de la ciudad» (2 R 23:8). Distinto de Josué hijo de Nun.",
    "Mattaniah_1": ("«Mathanías su tío» (de Joaquín): el rey de Babilonia lo pone por rey y le cambia el nombre por "
                    "Sedecías (2 R 24:17). Distinto del profeta Sedequías de 1 R 22:11."),
    "Jehoiachin_1": "Hijo de Joacim, rey de Judá tres meses; llevado a Babilonia (2 R 24:8, 15); Evil-merodac lo saca de la cárcel (25:27).",
    "Rabshakeh_1": "Enviado del rey de Asiria que habla al pueblo desde el muro (2 R 18:17-37; 19:4, 8). " + _CARGOS,
    "Tartan_1": "Enviado del rey de Asiria con Rabsaris y Rabsaces (2 R 18:17). " + _CARGOS,
    "Rab-saris_1": "Enviado del rey de Asiria con Tartán y Rabsaces (2 R 18:17). " + _CARGOS,
    MAACATI: _MAACATI,
    "So_1": "«So, rey de Egipto» (2 R 17:4), al que Oseas envía embajadores. " + _SO,
    "Shalmaneser_1": ("«Salmanasar rey de los Asirios» (2 R 17:3; 18:9). BibleData le atribuye también «el rey de Asiria» "
                      "sin nombre de 17:4-27; el texto solo da su nombre en 17:3 y 18:9."),
    "Pharaoh Neco_1": "«Faraón Nechâo rey de Egipto» (2 R 23:29); mata a Josías en Megido y pone por rey a Eliaquim (23:34).",
    "Shimeath_1": "Padre o madre de Josacar (2 R 12:21). " + _SIMEAT,
    "Shomer_1": "Padre o madre de Jozabad (2 R 12:21). " + _SIMEAT,
    "Gehazi_1": "Criado de Eliseo (2 R 4:12); la lepra de Naamán se le pega (5:27).",
    "Naaman_2": "General del ejército del rey de Siria, leproso, sanado en el Jordán (2 R 5:1, 14). Distinto de Naamán hijo de Benjamín.",
    "Huldah_1": "Profetisa, mujer de Salum (2 R 22:14).",
    "Isaiah_1": "Profeta, hijo de Amoz (2 R 19:2). La RV1909 escribe «Amós» al padre; no es el profeta Amós (BibleData los distingue).",
    "Amoz_1": "Padre del profeta Isaías (2 R 19:2). La RV1909 escribe «Amós»; BibleData lo distingue del profeta Amós.",
}
IDENTIDAD = {
    "Azariah_3": {"certeza": "inferido", "refs": ["2R 15:13", "2R 15:30", "2R 15:32", "2R 15:34"],
                  "nombres_rv1909": ["Azarías", "Uzzía"], "fuente": "bibledata",
                  "nota": ("BibleData identifica a «Uzzía» (2 R 15:13, 30, 32, 34) con Azarías hijo de Amasías (14:21; 15:1-7). "
                           "2 Reyes no dice que sean el mismo; lo sugiere que ambos se dan como padre de Jotam (15:7 «Jotham "
                           "su hijo»; 15:32 «Jotham hijo de Uzzía») y que 15:13 («año treinta y nueve de Uzzía») y 15:17 "
                           "(«año treinta y nueve de Azarías») fechan reinados seguidos. Se sigue a la fuente: inferido.")},
    "Eliakim_2": {"certeza": "texto", "refs": ["2R 23:34"], "nombres_rv1909": ["Eliacim", "Joacim"], "fuente": "rv1909",
                  "nota": "2 R 23:34: Faraón Nechâo «puso por rey á Eliacim hijo de Josías ... y mudóle el nombre en el de Joacim»."},
    "Mattaniah_1": {"certeza": "texto", "refs": ["2R 24:17"], "nombres_rv1909": ["Mathanías", "Sedecías"],
                    "fuente": "rv1909",
                    "nota": "2 R 24:17: el rey de Babilonia «puso por rey en lugar de Joachîn á Mathanías su tío, y mudóle el nombre en el de Sedecías»."},
}
NOTAS_VERIFICAR = [
    ("TM", (25, 23), "Jaazanías hijo de Maachâti"), ("TM", (18, 21), "Faraón rey de Egipto"), ("TM", (17, 4), "So, rey de Egipto"),
    ("TM", (3, 7), "Josaphat rey de Judá"), ("TM", (3, 14), "Josaphat rey de Judá"), ("TM", (8, 18), "una hija de Achâb fué su mujer"),
    ("TM", (8, 26), "Athalía hija de Omri rey de Israel"), ("TM", (12, 21), "Josachâr hijo de Simaath"),
    ("TM", (12, 21), "Jozabad hijo de Somer"), ("TM", (24, 17), "Mathanías su tío"), ("TM", (18, 17), "á Thartán y á Rabsaris y á Rabsaces"),
    ("TM", (3, 1), "reinó doce años"), ("TM", (9, 22), "Jezabel tu madre"), ("TM", (9, 24), "hirió á Joram"),
    ("TM", (8, 25), "Ochôzías hijo de Joram rey de Judá"), ("TM", (8, 26), "reinó un año en Jerusalem"),
    ("TM", (11, 3), "Athalía fué reina sobre el país"), ("TM", (9, 2), "Jehú hijo de Josaphat hijo de Nimsi"),
    ("TM", (9, 14), "Jehú hijo de Josaphat hijo de Nimsi"), ("TM", (11, 2), "Joas hijo de Ochôzías"), ("TM", (11, 21), "Era Joas de siete años"),
    ("TM", (13, 10), "Joas hijo de Joachâz"), ("TM", (13, 9), "reinó en su lugar Joas su hijo"),
    ("TM", (10, 35), "reinó en su lugar Joachâz su hijo"), ("TM", (13, 1), "Joachâz hijo de Jehú"),
    ("TM", (23, 30), "Joachâz hijo de Josías"), ("TM", (23, 31), "reinó tres meses en Jerusalem"),
    ("TM", (14, 23), "Jeroboam hijo de Joas"), ("TM", (14, 23), "cuarenta y un años"), ("TM", (13, 3), "Ben-adad hijo de Hazael"),
    ("TM", (13, 24), "reinó en su lugar Ben-adad su hijo"), ("TM", (14, 21), "tomó á Azarías"), ("TM", (15, 1), "Azarías hijo de Amasías"),
    ("TM", (15, 5), "fué leproso hasta el día de su muerte"), ("TM", (15, 13), "Uzzía"), ("TM", (15, 30), "Uzzía"),
    ("TM", (15, 32), "Jotham hijo de Uzzía"), ("TM", (15, 34), "Uzzía"), ("TM", (15, 7), "reinó en su lugar Jotham su hijo"),
    ("TM", (15, 17), "En el año treinta y nueve de Azarías"), ("TM", (15, 13), "en el año treinta y nueve de Uzzía"),
    ("TM", (15, 8), "Zachârías hijo de Jeroboam"), ("TM", (18, 2), "Abi hija de Zachârías"), ("TM", (18, 18), "Eliacim hijo de Hilcías"),
    ("TM", (23, 34), "Eliacim hijo de Josías"), ("TM", (22, 4), "Hilcías, sumo sacerdote"), ("TM", (22, 8), "El libro de la ley he hallado"),
    ("TM", (15, 13), "reinó el tiempo de un mes en Samaria"), ("TM", (22, 14), "mujer de Sallum hijo de Ticva"),
    ("TM", (22, 14), "guarda de las vestiduras"), ("TM", (25, 18), "Saraías primer sacerdote"),
    ("TM", (25, 23), "Saraía hijo de Tanhumet Netofatita"), ("TM", (20, 21), "reinó en su lugar Manasés su hijo"),
    ("TM", (21, 18), "en el huerto de Uzza"), ("TM", (21, 26), "en el huerto de Uzza"), ("TM", (21, 18), "reinó en su lugar Amón su hijo"),
    ("TM", (15, 33), "Jerusa hija de Sadoc"), ("TM", (22, 12), "Achbor hijo de Michâía"), ("TM", (23, 8), "Josué, gobernador de la ciudad"),
    ("TM", (24, 8), "reinó en Jerusalem tres meses"), ("TM", (24, 15), "trasportó á Joachîn á Babilonia"),
    ("TM", (25, 27), "levantó la cabeza de Joachîn rey de Judá"), ("TM", (18, 19), "Y díjoles Rabsaces"),
    ("TM", (19, 8), "regresando Rabsaces"), ("TM", (17, 3), "Salmanasar rey de los Asirios"), ("TM", (18, 9), "Salmanasar rey de los Asirios"),
    ("TM", (23, 29), "Faraón Nechâo rey de Egipto"), ("TM", (23, 29), "matólo en Megiddo"), ("TM", (4, 12), "Giezi su criado"),
    ("TM", (5, 27), "La lepra de Naamán se te pegará á ti"), ("TM", (5, 14), "zambullóse siete veces en el Jordán"),
    ("TM", (22, 14), "Hulda profetisa"), ("TM", (19, 2), "Isaías profeta hijo de Amós"),
    ("TM", (23, 34), "puso por rey á Eliacim hijo de Josías"), ("TM", (23, 34), "mudóle el nombre en el de Joacim"),
    ("TM", (24, 17), "puso por rey en lugar de Joachîn á Mathanías su tío, y mudóle el nombre en el de Sedecías"),
    ("TM", (8, 24), "reinó en lugar suyo Ochôzías, su hijo"), ("TM", (8, 25), "Ochôzías hijo de Joram"),
    ("TM", (2, 11), "Elías subió al cielo en un torbellino"), ("TM", (2, 13), "Alzó luego el manto de Elías"),
    ("TM", (13, 20), "murió Eliseo, y sepultáronlo"), ("TM", (9, 33), "Echadla abajo"), ("TM", (9, 36), "comerán los perros las carnes de Jezabel"),
    ("TM", (10, 36), "fué veintiocho años"), ("TM", (8, 15), "reinó Hazael en su lugar"), ("TM", (8, 7), "Ben-adad rey de Siria estaba enfermo"),
    ("TM", (8, 16), "comenzó á reinar Joram hijo de Josaphat rey de Judá"), ("TM", (8, 17), "ocho años reinó en Jerusalem"),
    ("TM", (22, 1), "reinó en Jerusalem treinta y un años"), ("TM", (23, 25), "No hubo tal rey antes de él"),
    ("TM", (1, 17), "porque [Ochôzías] no tenía hijo"), ("TM", (1, 2), "cayó por las celosías"), ("TM", (8, 26), "El nombre de su madre fué Athalía"),
    ("TM", (9, 20), "Jehú hijo de Nimsi"), ("TM", (10, 28), "Así extinguió Jehú á Baal de Israel"),
    ("TM", (17, 7), "de bajo la mano de Faraón rey de Egipto"),
]
ROLES = {
    "Jehoram_2": ("hijo de Acab, rey de Israel", (3, 1), "JORAM hijo de Achâb comenzó á reinar en Samaria sobre Israel"),
    "Mesha_1": ("rey de Moab", (3, 4), "Mesa rey de Moab"),
    "Gehazi_1": ("criado de Eliseo", (4, 12), "dijo á Giezi su criado"),
    SUNAMITA: ("mujer principal de Sunem que hospeda a Eliseo", (4, 12), "Llama á esta Sunamita"),
    "Naaman_2": ("general del ejército del rey de Siria", (5, 1), "NAAMÁN, general del ejército del rey de Siria"),
    "Ahaziah_2": ("hijo de Joram, rey de Judá", (8, 25), "comenzó á reinar Ochôzías hijo de Joram rey de Judá"),
    "Athaliah_1": ("madre de Ocozías; reina sobre el país", (11, 3), "Athalía fué reina sobre el país"),
    "Jehoshaphat_4": ("padre de Jehú", (9, 2), "Jehú hijo de Josaphat hijo de Nimsi"),
    "Bidkar_1": ("capitán de Jehú", (9, 25), "Dijo luego [Jehú] á Bidkar su capitán"),
    "Jehonadab_1": ("hijo de Recab, va con Jehú", (10, 15), "encontróse con Jonadab hijo de Rechâb"),
    "Jehoahaz_1": ("hijo de Jehú, rey de Israel", (13, 1), "comenzó á reinar Joachâz hijo de Jehú sobre Israel"),
    "Jehosheba_1": ("hija del rey Joram; esconde a Joás", (11, 2), "Josaba hija del rey Joram, hermana de Ochôzías"),
    "Joash_3": ("hijo de Ocozías, rey de Judá", (12, 1), "comenzó á reinar Joas, y reinó cuarenta años en Jerusalem"),
    "Jehoiada_2": ("sacerdote", (11, 9), "el sacerdote Joiada"),
    "Mattan_1": ("sacerdote de Baal", (11, 18), "Mathán sacerdote de Baal"),
    "Jozacar_1": ("siervo que mata a Joás", (12, 21), "Josachâr hijo de Simaath"),
    "Jehozabad_1": ("siervo que mata a Joás", (12, 21), "Jozabad hijo de Somer"),
    "Amaziah_1": ("hijo de Joás, rey de Judá", (14, 1), "comenzó á reinar Amasías hijo de Joas rey de Judá"),
    "Joash_4": ("hijo de Joacaz, rey de Israel", (13, 10), "comenzó á reinar Joas hijo de Joachâz sobre Israel"),
    "Jeroboam_2": ("hijo de Joás, rey de Israel", (14, 23), "comenzó á reinar Jeroboam hijo de Joas sobre Israel"),
    "Azariah_3": ("hijo de Amasías, rey de Judá", (15, 1), "comenzó á reinar Azarías hijo de Amasías rey de Judá"),
    "Jonah_1": ("profeta de Gat-hefer", (14, 25), "Jonás hijo de Amittai, profeta que fué de Gath-hepher"),
    "Zechariah_1": ("hijo de Jeroboam, rey de Israel", (15, 8), "reinó Zachârías hijo de Jeroboam sobre Israel seis meses"),
    "Jotham_2": ("hijo de Azarías (Uzías), rey de Judá", (15, 32), "comenzó á reinar Jotham hijo de Uzzía rey de Judá"),
    "Shallum_1": ("rey de Israel un mes", (15, 13), "Sallum hijo de Jabes comenzó á reinar"),
    "Menachem_1": ("rey de Israel", (15, 17), "reinó Manahem hijo de Gadi sobre Israel diez años"),
    "Pul_1": ("rey de Asiria", (15, 19), "Phul rey de Asiria"),
    "Pekahiah_1": ("rey de Israel", (15, 23), "reinó Pekaía hijo de Manahem sobre Israel"),
    "Pekah_1": ("capitán de Pekaía; rey de Israel", (15, 25), "Peka hijo de Remalías, capitán suyo"),
    "Argob_1": ("conjurado con Peka", (15, 25), "en compañía de Argob y de Ariph"),
    "Arieh_1": ("conjurado con Peka", (15, 25), "en compañía de Argob y de Ariph"),
    "Tiglath-pileser_1": ("rey de Asiria", (15, 29), "Tiglath-pileser rey de los Asirios"),
    "Hoshea_1": ("hijo de Ela, último rey de Israel", (17, 1), "comenzó á reinar Oseas hijo de Ela en Samaria sobre Israel"),
    "Rezin_1": ("rey de Siria", (15, 37), "Resín rey de Siria"),
    "Ahaz_1": ("hijo de Jotam, rey de Judá", (16, 1), "comenzó á reinar Achâz hijo de Jotham rey de Judá"),
    "Urijah_1": ("sacerdote que edifica el altar según el diseño de Damasco", (16, 11), "Urías el sacerdote edificó el altar"),
    "Hezekiah_1": ("hijo de Acaz, rey de Judá", (18, 1), "comenzó á reinar Ezechîas hijo de Achâz rey de Judá"),
    "Shalmaneser_1": ("rey de los asirios", (17, 3), "Salmanasar rey de los Asirios"),
    "So_1": ("rey de Egipto", (17, 4), "So, rey de Egipto"),
    "Sennacherib_1": ("rey de Asiria", (18, 13), "Sennachêrib rey de Asiria"),
    "Tartan_1": ("enviado del rey de Asiria", (18, 17), "á Thartán y á Rabsaris y á Rabsaces"),
    "Rab-saris_1": ("enviado del rey de Asiria", (18, 17), "á Thartán y á Rabsaris y á Rabsaces"),
    "Rabshakeh_1": ("enviado del rey de Asiria", (18, 17), "á Thartán y á Rabsaris y á Rabsaces"),
    "Eliakim_1": ("mayordomo de Ezequías", (18, 18), "Eliacim hijo de Hilcías, que era mayordomo"),
    "Shebnah_1": ("escriba de Ezequías", (18, 18), "Sebna escriba"),
    "Joah_1": ("canciller de Ezequías", (18, 18), "Joah hijo de Asaph, canciller"),
    "Isaiah_1": ("profeta", (19, 2), "Isaías profeta hijo de Amós"),
    "Tirhakah_1": ("rey de Etiopía", (19, 9), "Thiraca rey de Ethiopía"),
    "Esarhaddon_1": ("hijo de Senaquerib; rey de Asiria", (19, 37), "reinó en su lugar Esar-hadón su hijo"),
    "Berodach-baladan_1": ("rey de Babilonia", (20, 12), "Berodach-baladán hijo de Baladán, rey de Babilonia"),
    "Manasseh_3": ("hijo de Ezequías, rey de Judá", (21, 1), "DE doce años era Manasés cuando comenzó á reinar"),
    "Uzza_1": ("dueño del huerto donde sepultan a Manasés", (21, 18), "en el huerto de Uzza"),
    "Amon_2": ("hijo de Manasés, rey de Judá", (21, 19), "De veinte y dos años era Amón cuando comenzó á reinar"),
    "Shaphan_1": ("escriba de Josías", (22, 3), "Saphán hijo de Azalía, hijo de Mesullam, escriba"),
    "Hilkiah_2": ("sumo sacerdote", (22, 4), "Hilcías, sumo sacerdote"),
    "Asaiah_1": ("siervo del rey Josías", (22, 12), "Asaía siervo del rey"),
    "Huldah_1": ("profetisa", (22, 14), "Hulda profetisa"),
    "Shallum_2": ("guarda de las vestiduras", (22, 14), "guarda de las vestiduras"),
    "Joshua_3": ("gobernador de la ciudad", (23, 8), "Josué, gobernador de la ciudad"),
    "Nathan-melech_1": ("eunuco", (23, 11), "Nathan-melech eunuco"),
    "Pharaoh Neco_1": ("rey de Egipto", (23, 29), "Faraón Nechâo rey de Egipto"),
    "Jehoahaz_2": ("hijo de Josías, rey de Judá", (23, 31), "De veintitrés años era Joachâz cuando comenzó á reinar"),
    "Eliakim_2": ("hijo de Josías, rey de Judá (Joacim)", (23, 34), "puso por rey á Eliacim hijo de Josías"),
    "Nebuchadnezzar_1": ("rey de Babilonia", (24, 1), "Nabucodonosor rey de Babilonia"),
    "Jehoiachin_1": ("hijo de Joacim, rey de Judá", (24, 8), "De dieciocho años era Joachîn cuando comenzó á reinar"),
    "Mattaniah_1": ("tío de Joaquín, rey de Judá (Sedecías)", (24, 17), "Mathanías su tío"),
    "Nebuzaradan_1": ("capitán de la guardia del rey de Babilonia", (25, 8), "Nabuzaradán, capitán de los de la guardia"),
    "Seraiah_2": ("primer sacerdote", (25, 18), "Saraías primer sacerdote"),
    "Zephaniah_1": ("segundo sacerdote", (25, 18), "Sophonías segundo sacerdote"),
    "Gedaliah_1": ("gobernador puesto por el rey de Babilonia", (25, 22), "puso por gobernador á Gedalías"),
    "Ishmael_2": ("de la estirpe real; mata a Gedalías", (25, 25), "Ismael hijo de Nathanías, hijo de Elisama, de la estirpe real"),
    "Evil-merodach_1": ("rey de Babilonia", (25, 27), "Evil-merodach rey de Babilonia"),
}
SIN_NOMBRE = {
    SUNAMITA: ("La sunamita", "f",
               "«Una mujer principal» de Sunem que hospeda a Eliseo (2 R 4:8-10); el texto no da su nombre. Eliseo le "
               "anuncia un hijo, que muere y revive (4:16-37); por consejo de Eliseo vive siete años en tierra de los "
               "filisteos y el rey le devuelve sus tierras (8:1-6).", []),
}
RELACIONES = [
    ("Ahab_1", "Jehoram_2", "padre", (3, 1), "JORAM hijo de Achâb", "También 2 R 8:16, 25, 28-29; 9:15 (no lo nombra)."),
    ("Jezebel_1", "Jehoram_2", "madre", (9, 22), "las fornicaciones de Jezabel tu madre", "Lo dice Jehú a Joram (2 R 9:22)."),
    ("Jehoram_1", "Ahaziah_2", "padre", (8, 24), "reinó en lugar suyo Ochôzías, su hijo", "2 R 8:25: «Ochôzías hijo de Joram rey de Judá»."),
    ("Athaliah_1", "Ahaziah_2", "madre", (8, 26), "El nombre de su madre fué Athalía", "También 2 R 11:1: «ATHALÍA madre de Ochôzías»."),
    ("Omri_1", "Athaliah_1", "padre", (8, 26), "Athalía hija de Omri rey de Israel", _ATALIA),
    ("Jehoshaphat_4", "Jehu_2", "padre", (9, 2), "Jehú hijo de Josaphat hijo de Nimsi",
     "También 2 R 9:14. 1 R 19:16 y 2 R 9:20 dicen «Jehú hijo de Nimsi»: ver la relación con Nimsi. No se armoniza."),
    ("Nimshi_1", "Jehoshaphat_4", "padre", (9, 2), "Josaphat hijo de Nimsi", "También 2 R 9:14."),
    ("Rechab_2", "Jehonadab_1", "padre", (10, 15), "Jonadab hijo de Rechâb", "También 2 R 10:23."),
    ("Jehu_2", "Jehoahaz_1", "padre", (10, 35), "reinó en su lugar Joachâz su hijo", "2 R 13:1: «Joachâz hijo de Jehú»."),
    ("Jehoram_1", "Jehosheba_1", "padre", (11, 2), "Josaba hija del rey Joram",
     "El texto la llama «hermana de Ochôzías» (2 R 11:2) y no dice quién es su madre."),
    ("Ahaziah_2", "Joash_3", "padre", (11, 2), "Joas hijo de Ochôzías", "También 2 R 13:1; 14:13."),
    ("Zibiah_1", "Joash_3", "madre", (12, 1), "El nombre de su madre fué Sibia, de Beer-seba", ""),
    ("Ahaziah_2", "Zibiah_1", "conyuge", (12, 1), "El nombre de su madre fué Sibia",
     "Madre de Joás hijo de Ocozías (2 R 11:2; 12:1); el texto no la llama mujer de Ocozías: inferido."),
    ("Joash_3", "Amaziah_1", "padre", (12, 21), "reinó en su lugar Amasías su hijo", "2 R 14:1: «Amasías hijo de Joas rey de Judá»."),
    ("Hazael_1", "Ben-hadad_2", "padre", (13, 3), "Ben-adad hijo de Hazael", "También 2 R 13:24-25."),
    ("Jehoahaz_1", "Joash_4", "padre", (13, 9), "reinó en su lugar Joas su hijo", "2 R 13:10: «Joas hijo de Joachâz»."),
    ("Joash_4", "Jeroboam_2", "padre", (14, 16), "reinó en su lugar Jeroboam su hijo", "2 R 14:23: «Jeroboam hijo de Joas»."),
    ("Jehoaddin_1", "Amaziah_1", "madre", (14, 2), "el nombre de su madre fué Joaddan, de Jerusalem", ""),
    ("Joash_3", "Jehoaddin_1", "conyuge", (14, 2), "el nombre de su madre fué Joaddan",
     "Madre de Amasías hijo de Joás (2 R 14:1-2); el texto no la llama mujer de Joás: inferido."),
    ("Amaziah_1", "Azariah_3", "padre", (14, 21), "hiciéronlo rey en lugar de Amasías su padre", "2 R 15:1: «Azarías hijo de Amasías»."),
    ("Amittai_1", "Jonah_1", "padre", (14, 25), "Jonás hijo de Amittai", ""),
    ("Jeroboam_2", "Zechariah_1", "padre", (14, 29), "reinó en su lugar Zachârías su hijo", "2 R 15:8: «Zachârías hijo de Jeroboam»."),
    ("Jecoliah_1", "Azariah_3", "madre", (15, 2), "el nombre de su madre fué Jecolía, de Jerusalem", ""),
    ("Amaziah_1", "Jecoliah_1", "conyuge", (15, 2), "el nombre de su madre fué Jecolía",
     "Madre de Azarías hijo de Amasías (2 R 15:1-2); el texto no la llama mujer de Amasías: inferido."),
    ("Azariah_3", "Jotham_2", "padre", (15, 7), "reinó en su lugar Jotham su hijo",
     "2 R 15:32: «Jotham hijo de Uzzía» (ver la identidad de Azarías)."),
    ("Jabesh_1", "Shallum_1", "padre", (15, 10), "Sallum hijo de Jabes", "También 2 R 15:13-14."),
    ("Gadi_1", "Menachem_1", "padre", (15, 14), "Manahem hijo de Gadi", "También 2 R 15:17."),
    ("Menachem_1", "Pekahiah_1", "padre", (15, 22), "reinó en su lugar Pekaía su hijo", "2 R 15:23: «Pekaía hijo de Manahem»."),
    ("Remaliah_1", "Pekah_1", "padre", (15, 25), "Peka hijo de Remalías", "También 2 R 15:27, 30, 32, 37; 16:1, 5."),
    ("Elah_3", "Hoshea_1", "padre", (15, 30), "Oseas hijo de Ela", "También 2 R 17:1; 18:1, 9."),
    ("Jerusha_1", "Jotham_2", "madre", (15, 33), "El nombre de su madre fué Jerusa hija de Sadoc", ""),
    ("Zadok_2", "Jerusha_1", "padre", (15, 33), "Jerusa hija de Sadoc", ""),
    ("Azariah_3", "Jerusha_1", "conyuge", (15, 33), "El nombre de su madre fué Jerusa",
     "Madre de Jotam hijo de Uzías (2 R 15:32-33); el texto no la llama mujer de Azarías: inferido."),
    ("Jotham_2", "Ahaz_1", "padre", (15, 38), "reinó en su lugar Achâz su hijo", "2 R 16:1: «Achâz hijo de Jotham»."),
    ("Ahaz_1", "Hezekiah_1", "padre", (16, 20), "reinó en su lugar Ezechîas su hijo", "2 R 18:1: «Ezechîas hijo de Achâz»."),
    ("Abi_1", "Hezekiah_1", "madre", (18, 2), "El nombre de su madre [fué] Abi hija de Zachârías", ""),
    ("Zechariah_2", "Abi_1", "padre", (18, 2), "Abi hija de Zachârías", ""),
    ("Ahaz_1", "Abi_1", "conyuge", (18, 2), "El nombre de su madre [fué] Abi",
     "Madre de Ezequías hijo de Acaz (2 R 18:1-2); el texto no la llama mujer de Acaz: inferido."),
    ("Hilkiah_1", "Eliakim_1", "padre", (18, 18), "Eliacim hijo de Hilcías", "También 2 R 18:26, 37."),
    ("Asaph_1", "Joah_1", "padre", (18, 18), "Joah hijo de Asaph", "También 2 R 18:37."),
    ("Amoz_1", "Isaiah_1", "padre", (19, 2), "Isaías profeta hijo de Amós", "También 2 R 19:20; 20:1."),
    ("Sennacherib_1", "Adrammelech_1", "padre", (19, 37), "Adramelech y Saresar sus hijos", ""),
    ("Sennacherib_1", "Sharezer_1", "padre", (19, 37), "Adramelech y Saresar sus hijos", ""),
    ("Sennacherib_1", "Esarhaddon_1", "padre", (19, 37), "reinó en su lugar Esar-hadón su hijo", ""),
    ("Baladan_1", "Berodach-baladan_1", "padre", (20, 12), "Berodach-baladán hijo de Baladán", ""),
    ("Hezekiah_1", "Manasseh_3", "padre", (20, 21), "reinó en su lugar Manasés su hijo", ""),
    ("Hephzibah_1", "Manasseh_3", "madre", (21, 1), "el nombre de su madre fué Hepsiba", ""),
    ("Hezekiah_1", "Hephzibah_1", "conyuge", (21, 1), "el nombre de su madre fué Hepsiba",
     "Madre de Manasés hijo de Ezequías (2 R 20:21; 21:1); el texto no la llama mujer de Ezequías: inferido."),
    ("Manasseh_3", "Amon_2", "padre", (21, 18), "reinó en su lugar Amón su hijo", ""),
    ("Meshullemeth_1", "Amon_2", "madre", (21, 19), "El nombre de su madre fué Mesalemeth", ""),
    ("Haruz_1", "Meshullemeth_1", "padre", (21, 19), "Mesalemeth hija de Harus de Jotba", ""),
    ("Manasseh_3", "Meshullemeth_1", "conyuge", (21, 19), "El nombre de su madre fué Mesalemeth",
     "Madre de Amón hijo de Manasés (2 R 21:18-19); el texto no la llama mujer de Manasés: inferido."),
    ("Amon_2", "Josiah_1", "padre", (21, 24), "por rey en su lugar á Josías su hijo", "También 2 R 21:26."),
    ("Jedidah_1", "Josiah_1", "madre", (22, 1), "El nombre de su madre fué Idida", ""),
    ("Adaiah_1", "Jedidah_1", "padre", (22, 1), "Idida hija de Adaía de Boscath", ""),
    ("Amon_2", "Jedidah_1", "conyuge", (22, 1), "El nombre de su madre fué Idida",
     "Madre de Josías hijo de Amón (2 R 21:24; 22:1); el texto no la llama mujer de Amón: inferido."),
    ("Azaliah_1", "Shaphan_1", "padre", (22, 3), "Saphán hijo de Azalía", ""),
    ("Meshullam_1", "Azaliah_1", "padre", (22, 3), "Azalía, hijo de Mesullam", ""),
    ("Shaphan_1", "Ahikam_1", "padre", (22, 12), "Ahicam hijo de Saphán", "También 2 R 25:22."),
    ("Micaiah_2", "Achbor_2", "padre", (22, 12), "Achbor hijo de Michâía", ""),
    ("Huldah_1", "Shallum_2", "conyuge", (22, 14), "Hulda profetisa, mujer de Sallum", ""),
    ("Tikvah_1", "Shallum_2", "padre", (22, 14), "Sallum hijo de Ticva", ""),
    ("Harhas_1", "Tikvah_1", "padre", (22, 14), "Ticva hijo de Araas", ""),
    ("Josiah_1", "Jehoahaz_2", "padre", (23, 30), "Joachâz hijo de Josías", ""),
    ("Hamutal_1", "Jehoahaz_2", "madre", (23, 31), "El nombre de su madre fué Amutal", ""),
    ("Jeremiah_1", "Hamutal_1", "padre", (23, 31), "Amutal, hija de Jeremías de Libna", "También 2 R 24:18."),
    ("Josiah_1", "Hamutal_1", "conyuge", (23, 31), "El nombre de su madre fué Amutal",
     "Madre de Joacaz hijo de Josías (2 R 23:30-31); el texto no la llama mujer de Josías: inferido."),
    ("Josiah_1", "Eliakim_2", "padre", (23, 34), "Eliacim hijo de Josías", ""),
    ("Zebidah_1", "Eliakim_2", "madre", (23, 36), "El nombre de su madre fué Zebuda", ""),
    ("Pedaiah_1", "Zebidah_1", "padre", (23, 36), "Zebuda hija de Pedaia, de Ruma", ""),
    ("Josiah_1", "Zebidah_1", "conyuge", (23, 36), "El nombre de su madre fué Zebuda",
     "Madre de Joacim hijo de Josías (2 R 23:34-36); el texto no la llama mujer de Josías: inferido."),
    ("Eliakim_2", "Jehoiachin_1", "padre", (24, 6), "reinó en su lugar Joachîn su hijo", ""),
    ("Nehushta_1", "Jehoiachin_1", "madre", (24, 8), "El nombre de su madre fué Neusta", ""),
    ("Elnathan_1", "Nehushta_1", "padre", (24, 8), "Neusta hija de Elnathán", ""),
    ("Eliakim_2", "Nehushta_1", "conyuge", (24, 8), "El nombre de su madre fué Neusta",
     "Madre de Joaquín hijo de Joacim (2 R 24:6-8); el texto no la llama mujer de Joacim: inferido."),
    ("Hamutal_1", "Mattaniah_1", "madre", (24, 18), "El nombre de su madre fué Amutal hija de Jeremías", ""),
    ("Ahikam_1", "Gedaliah_1", "padre", (25, 22), "Gedalías, hijo de Ahicam hijo de Saphán", ""),
    ("Nethaniah_1", "Ishmael_2", "padre", (25, 23), "Ismael hijo de Nathanías", "También 2 R 25:25."),
    ("Elishama_3", "Nethaniah_1", "padre", (25, 25), "Nathanías, hijo de Elisama", ""),
    ("Kareah_1", "Johanan_1", "padre", (25, 23), "Johanán hijo de Carea", ""),
    ("Tanhumeth_1", "Seraiah_3", "padre", (25, 23), "Saraía hijo de Tanhumet Netofatita", ""),
    (MAACATI, "Jaazaniah_1", "padre", (25, 23), "Jaazanías hijo de Maachâti", _MAACATI),
]
# Relaciones que el texto no dice tal cual: certeza «inferido» (la nota dice por qué).
INFERIDAS = {("Ahaziah_2", "Zibiah_1", "conyuge"), ("Jehoaddin_1", "Joash_3", "conyuge"),
             ("Amaziah_1", "Jecoliah_1", "conyuge"), ("Azariah_3", "Jerusha_1", "conyuge"), ("Abi_1", "Ahaz_1", "conyuge"),
             ("Hephzibah_1", "Hezekiah_1", "conyuge"), ("Manasseh_3", "Meshullemeth_1", "conyuge"),
             ("Amon_2", "Jedidah_1", "conyuge"), ("Hamutal_1", "Josiah_1", "conyuge"), ("Josiah_1", "Zebidah_1", "conyuge"),
             ("Eliakim_2", "Nehushta_1", "conyuge"), ("Ahab_1", "Athaliah_1", "padre"),
             ("Athaliah_1", "Jehoram_1", "conyuge"), ("Shimeath_1", "Jozacar_1", "madre"),
             ("Shomer_1", "Jehozabad_1", "madre"), ("Josiah_1", "Mattaniah_1", "padre")}
# Relaciones de los libros anteriores que 2 Reyes repite: se añade la referencia a la nota.
REPITE_GN = [
    ("Shaphat_2", "Elisha_1", "padre", (3, 11), "Eliseo hijo de Saphat"),
    ("Nebat_1", "Jeroboam_1", "padre", (3, 3), "Jeroboam, hijo de Nabat"),
    ("Ahijah_3", "Baasha_1", "padre", (9, 9), "Baasa hijo de Ahía"),
    ("Jehoshaphat_3", "Jehoram_1", "padre", (8, 16), "Joram hijo de Josaphat rey de Judá"),
    ("Nimshi_1", "Jehu_2", "padre", (9, 20), "Jehú hijo de Nimsi"),
    ("David_1", "Solomon_1", "padre", (21, 7), "á David y á Salomón su hijo"),
]
# 1 R 19:16 y 2 R 9:20 dicen «Jehú hijo de Nimsi»; 2 R 9:2 y 9:14, «Jehú hijo de Josaphat hijo de Nimsi». Se añade a la
# relación Nimsi → Jehú (de 1 R) sin cambiar lo que dice cada versículo.
NOTA_NIMSI = ("2 R 9:2 y 9:14 dicen «Jehú hijo de Josaphat hijo de Nimsi»: ahí Nimsi es el abuelo y Josafat el padre "
              "(relaciones aparte, con cita). 1 R 19:16 y 2 R 9:20 dicen «hijo de Nimsi». No se armoniza.")
# Edades escritas (TM de la RV1909 y LXX de Brenton) al comenzar a reinar: índice de la cifra en cada texto.
EDADES = [
    ("Jehoram_1", "en_evento", (8, 17), 0, 0, "cuando comienza a reinar (2 R 8:17)"),
    ("Ahaziah_2", "en_evento", (8, 26), 0, 0, "cuando comienza a reinar (2 R 8:26)"),
    ("Joash_3", "en_evento", (11, 21), 0, 0, "cuando comienza a reinar (2 R 11:21)"),
    ("Amaziah_1", "en_evento", (14, 2), 0, 0, "cuando comienza a reinar (2 R 14:2)"),
    ("Azariah_3", "en_evento", (15, 2), 0, 0, "cuando comienza a reinar (2 R 15:2; también 14:21)"),
    ("Jotham_2", "en_evento", (15, 33), 0, 0, "cuando comienza a reinar (2 R 15:33)"),
    ("Ahaz_1", "en_evento", (16, 2), 0, 0, "cuando comienza a reinar (2 R 16:2)"),
    ("Hezekiah_1", "en_evento", (18, 2), 0, 0, "cuando comienza a reinar (2 R 18:2)"),
    ("Manasseh_3", "en_evento", (21, 1), 0, 0, "cuando comienza a reinar (2 R 21:1)"),
    ("Amon_2", "en_evento", (21, 19), 0, 0, "cuando comienza a reinar (2 R 21:19)"),
    ("Josiah_1", "en_evento", (22, 1), 0, 0, "cuando comienza a reinar (2 R 22:1)"),
    ("Jehoahaz_2", "en_evento", (23, 31), 0, 0, "cuando comienza a reinar (2 R 23:31)"),
    ("Eliakim_2", "en_evento", (23, 36), 0, 0, "cuando comienza a reinar (2 R 23:36)"),
    ("Jehoiachin_1", "en_evento", (24, 8), 0, 0, "cuando comienza a reinar (2 R 24:8)"),
    ("Mattaniah_1", "en_evento", (24, 18), 0, 0, "cuando comienza a reinar (2 R 24:18)"),
]
NOTAS_EXISTENTES = {
    "Elijah_1": ("2 R 1: anuncia a Ocozías que morirá y hace descender fuego sobre dos capitanes de cincuenta; 2 R 2:11: "
                 "«Elías subió al cielo en un torbellino», y Eliseo alza su manto (2:13)."),
    "Elisha_1": "2 R 2–13: hereda el manto de Elías; «murió Eliseo, y sepultáronlo» (2 R 13:20).",
    "Jezebel_1": "2 R 9:33-36: Jehú dice «Echadla abajo»; se cumple la palabra de Elías: «comerán los perros las carnes de Jezabel».",
    "Jehu_2": ("2 R 9: ungido rey en Ramot de Galaad; 9:2 y 9:14 lo llaman «hijo de Josaphat hijo de Nimsi» (ver su padre "
               "Josafat, Jehoshaphat_4); 10:28: «Así extinguió Jehú á Baal de Israel»; reina «veintiocho años» (10:36)."),
    "Hazael_1": "2 R 8:15: «reinó Hazael en su lugar»; su hijo es Ben-adad (2 R 13:3, 24).",
    "Ben-hadad_1": ("2 R 6:24 y 8:7: «Ben-adad rey de Siria estaba enfermo»; Hazael lo ahoga (8:15). BibleData lo une con el "
                    "de 1 R 15 y 20; distinto de Ben-adad hijo de Hazael (2 R 13:3)."),
    "Jehoram_1": ("2 R 8:16-17: «comenzó á reinar Joram hijo de Josaphat rey de Judá»; «ocho años reinó en Jerusalem». "
                  "Distinto de Joram hijo de Acab, rey de Israel (2 R 3:1)."),
    "Ahaziah_1": "2 R 1:2: «cayó por las celosías»; muere sin hijo («porque [Ochôzías] no tenía hijo», 1:17). Distinto de Ocozías de Judá.",
    "Josiah_1": ("2 R 22:1: «reinó en Jerusalem treinta y un años»; halla el libro de la ley y renueva el pacto; «No hubo tal "
                 "rey antes de él» (23:25); muere en Megido (23:29)."),
    "Nimshi_1": NOTA_NIMSI,
    "Pharaoh_4": "2 R 17:7: «de bajo la mano de Faraón rey de Egipto» (el de la salida).",
}
# Refs que el texto da a una persona y BibleData no sitúa.
REFS_EXTRA = {
    SUNAMITA: [(4, 8), (4, 9), (4, 13), (4, 16), (4, 17), (4, 22), (4, 25), (4, 26), (4, 28), (4, 30), (4, 36), (4, 37),
               (8, 1), (8, 2), (8, 3), (8, 5), (8, 6)],
    "Jehoram_1": [(8, 29)], "Joash_3": [(14, 23)], "Athaliah_1": [(11, 16), (11, 20)],
    # nombrados en el versículo (sin corchetes) y que BibleData no sitúa ahí
    "Elisha_1": [(3, 15), (4, 31)], "Gehazi_1": [(4, 13)], "Ben-hadad_1": [(8, 15)], "Ahab_1": [(8, 29)],
    "Hazael_1": [(8, 29)], "Ahaziah_2": [(8, 29)], "Jacob_1": [(13, 23)], "Pekah_1": [(15, 27)],
    "Remaliah_1": [(15, 27)], "Jeroboam_1": [(15, 28)], "Nebat_1": [(15, 28)], "Jehoiachin_1": [(24, 17)],
    "Nebuzaradan_1": [(25, 12)],
}
REFS_QUITAR = {}
# Versículos donde dos personas con la misma forma aparecen juntas: se asignan por orden de aparición (único punto; se
# comprueba el número de apariciones). (cap, vers) -> (forma, [persona en el orden del texto]).
ORDEN_MENCIONES = {
    (1, 17): ("Joram", ["Jehoram_2", "Jehoram_1"]),          # reinó en su lugar Joram, en el segundo año de Joram, hijo de Josaphat
    (8, 16): ("Joram", ["Jehoram_2", "Jehoram_1"]),          # quinto año de Joram hijo de Achâb … Joram hijo de Josaphat
    (8, 25): ("Joram", ["Jehoram_2", "Jehoram_1"]),          # año doce de Joram hijo de Achâb … Ochôzías hijo de Joram
    (8, 29): ("Joram", ["Jehoram_2", "Jehoram_1", "Jehoram_2"]),  # el rey Joram … hijo de Joram rey de Judá … á Joram hijo de Achâb
    (13, 10): ("Joas", ["Joash_3", "Joash_4"]),             # año treinta y siete de Joas rey de Judá … Joas hijo de Joachâz
    (14, 1): ("Joas", ["Joash_4", "Joash_3"]),              # Joas hijo de Joachâz … Amasías hijo de Joas rey de Judá
    (14, 13): ("Joas", ["Joash_4", "Joash_3"]),             # Joas rey de Israel … hijo de Joas hijo de Ochôzías
    (14, 17): ("Joas", ["Joash_3", "Joash_4"]),             # Amasías hijo de Joas … muerte de Joas hijo de Joachâz
    (14, 23): ("Joas", ["Joash_3", "Joash_4"]),             # Amasías hijo de Joas … Jeroboam hijo de Joas
}

S1 = "Elías sube al cielo (2 R 1–2)"
S2 = "Los hechos de Eliseo (2 R 3–8)"
S3 = "Jehú (2 R 9–10)"
S4 = "Atalía y Joás (2 R 11–12)"
S5 = "Los reyes hasta la caída de Samaria (2 R 13–17)"
S6 = "Ezequías y Senaquerib (2 R 18–20)"
S7 = "Manasés y Josías (2 R 21–23)"
S8 = "La caída de Jerusalén (2 R 24–25)"
PASAJES = [
    ("1:1", "1:18", "Ocozías y los capitanes de cincuenta", "Ocozías cae por una celosía y manda consultar a Baal-zebub; Elías le anuncia que morirá, y el fuego del cielo consume a dos capitanes de cincuenta. Ocozías muere sin hijo y reina Joram.", S1),
    ("2:1", "2:14", "Elías sube al cielo", "Elías y Eliseo van de Gilgal a Betel, a Jericó y al Jordán; un carro de fuego los aparta y «Elías subió al cielo en un torbellino». Eliseo alza su manto y divide las aguas.", S1),
    ("2:15", "2:25", "Eliseo en Jericó y en Betel", "Los hijos de los profetas buscan a Elías tres días sin hallarlo; Eliseo sana las aguas de Jericó con sal, y en el camino de Betel unos muchachos se burlan de él.", S1),
    ("3:1", "3:12", "Joram, Josafat y el rey de Edom contra Moab", "Joram, hijo de Acab, reina en Samaria; Mesa de Moab se rebela, y los reyes de Israel, Judá y Edom se quedan sin agua en el desierto y van a Eliseo.", S2),
    ("3:13", "3:27", "Agua en el valle; la derrota de Moab", "Eliseo manda abrir acequias y el valle se llena de agua; los moabitas la ven roja como sangre, atacan y son vencidos.", S2),
    ("4:1", "4:7", "El aceite de la viuda", "La viuda de uno de los hijos de los profetas llena vasos prestados con su botija de aceite y paga a su acreedor.", S2),
    ("4:8", "4:17", "La sunamita y el hijo anunciado", "Una mujer principal de Sunem prepara a Eliseo una cámara; él le anuncia que abrazará un hijo, y lo da a luz.", S2),
    ("4:18", "4:37", "El hijo de la sunamita revive", "El niño muere en las rodillas de su madre; ella va al Carmelo a buscar a Eliseo, que ora y se tiende sobre él, y el niño revive.", S2),
    ("4:38", "4:44", "La olla y los panes", "En Gilgal Eliseo sana un potaje de calabazas silvestres («¡Varón de Dios, la muerte en la olla!») y veinte panes de cebada alcanzan para cien hombres.", S2),
    ("5:1", "5:14", "Naamán sanado en el Jordán", "Una muchacha cautiva de Israel habla del profeta; Naamán, general del rey de Siria, se lava siete veces en el Jordán y queda limpio de su lepra.", S2),
    ("5:15", "5:27", "Naamán agradece; Giezi", "Eliseo no acepta el presente de Naamán; Giezi corre tras él, toma plata y vestidos, y queda leproso.", S2),
    ("6:1", "6:7", "El hacha que flota", "Cortando vigas junto al Jordán, a uno se le cae al agua un hacha prestada; Eliseo echa un palo y hace nadar el hierro.", S2),
    ("6:8", "6:23", "Los sirios en Dotán", "Eliseo avisa al rey de Israel de los planes del rey de Siria; cercado en Dotán, su criado ve el monte lleno de carros de fuego, y los sirios, heridos de ceguera, son llevados a Samaria y despedidos.", S2),
    ("6:24", "6:33", "El hambre en Samaria", "Ben-adad cerca Samaria y hay grande hambre; el rey de Israel oye a una mujer y culpa a Eliseo.", S2),
    ("7:1", "7:20", "Los cuatro leprosos", "Eliseo anuncia abundancia para el día siguiente; cuatro leprosos hallan vacío el campamento sirio, y el príncipe que no creyó muere atropellado en la puerta.", S2),
    ("8:1", "8:6", "La sunamita recupera sus tierras", "Tras siete años en tierra de los filisteos, la sunamita pide al rey su casa y sus tierras, y Giezi cuenta cómo Eliseo resucitó a su hijo.", S2),
    ("8:7", "8:15", "Eliseo y Hazael en Damasco", "Ben-adad, enfermo, envía a Hazael a consultar a Eliseo; Eliseo llora por el mal que Hazael hará a Israel, y Hazael reina en lugar de Ben-adad.", S2),
    ("8:16", "8:29", "Joram y Ocozías, reyes de Judá", "Joram hijo de Josafat reina ocho años en Jerusalén; Edom se rebela. Ocozías, hijo de Joram y de Atalía, reina un año y visita a Joram de Israel, herido, en Jezreel.", S2),
    ("9:1", "9:13", "Jehú ungido rey", "Un hijo de los profetas unge a Jehú en Ramot de Galaad por mandato de Eliseo, y los capitanes lo aclaman: «Jehú es rey».", S3),
    ("9:14", "9:29", "Jehú mata a Joram y a Ocozías", "Jehú va en su carro a Jezreel; hiere a Joram en la heredad de Nabot, y Ocozías, herido en la huida, muere en Megido.", S3),
    ("9:30", "9:37", "Muerte de Jezabel", "Jezabel se asoma a la ventana; los eunucos la echan abajo y se cumple la palabra de Elías sobre ella.", S3),
    ("10:1", "10:17", "La casa de Acab", "Los principales de Samaria entregan las cabezas de los setenta hijos de Acab; Jehú mata a los que quedan de su casa y sube con Jonadab hijo de Recab.", S3),
    ("10:18", "10:36", "Jehú destruye a Baal", "Jehú reúne a los siervos de Baal en su templo y los hace matar; derriba la casa de Baal, pero no se aparta de los becerros de Betel y Dan. Reina veintiocho años.", S3),
    ("11:1", "11:12", "Atalía; Joás escondido y coronado", "Atalía destruye la simiente real; Josaba esconde a Joás seis años en la casa de Jehová, y al séptimo Joiada lo corona: «¡Viva el rey!».", S4),
    ("11:13", "11:21", "Muerte de Atalía; el pacto", "Atalía grita «¡Traición, traición!» y la matan fuera del templo; Joiada hace pacto entre Jehová, el rey y el pueblo, y derriban el templo de Baal.", S4),
    ("12:1", "12:16", "Joás repara el templo", "Joás reina cuarenta años; Joiada pone un arca junto al altar para recoger el dinero con que se reparan las aberturas de la casa de Jehová.", S4),
    ("12:17", "12:21", "Hazael; muere Joás", "Joás da a Hazael el oro del templo para que no suba contra Jerusalén; sus siervos lo matan y reina Amasías.", S4),
    ("13:1", "13:13", "Joacaz y Joás, reyes de Israel", "Joacaz hijo de Jehú reina diecisiete años, oprimido por Hazael; le sucede Joás su hijo.", S5),
    ("13:14", "13:25", "Muerte de Eliseo", "Eliseo, enfermo, manda a Joás tirar la saeta de salud y herir la tierra; muere, y un muerto echado en su sepulcro revive al tocar sus huesos.", S5),
    ("14:1", "14:22", "Amasías de Judá", "Amasías vence a Edom y desafía a Joás de Israel, que lo derrota en Bet-semes y saquea Jerusalén; muere en Laquis y reina Azarías.", S5),
    ("14:23", "14:29", "Jeroboam hijo de Joás", "Jeroboam reina cuarenta y un años y restituye los términos de Israel, conforme a la palabra de Jonás hijo de Amitai.", S5),
    ("15:1", "15:7", "Azarías, el rey leproso", "Azarías reina cincuenta y dos años; Jehová lo hiere con lepra y su hijo Jotam gobierna el palacio.", S5),
    ("15:8", "15:31", "De Zacarías a Peka", "Cinco reyes de Israel en pocos años: Zacarías, Salum, Manahem, Pekaía y Peka; Pul y Tiglat-pileser de Asiria llegan a la tierra.", S5),
    ("15:32", "16:4", "Jotam y Acaz", "Jotam reina dieciséis años y edifica la puerta más alta del templo; Acaz no hace lo recto y anda en el camino de los reyes de Israel.", S5),
    ("16:5", "16:20", "Acaz y el altar de Damasco", "Resín y Peka suben contra Jerusalén; Acaz pide ayuda a Tiglat-pileser y manda a Urías hacer un altar como el de Damasco.", S5),
    ("17:1", "17:23", "Caída de Samaria", "Oseas deja de pagar tributo; el rey de Asiria toma Samaria y lleva a Israel a Asiria, porque no escucharon a los profetas.", S5),
    ("17:24", "17:41", "Los pueblos traídos a Samaria", "El rey de Asiria pone en las ciudades de Samaria gentes de Babilonia, Cuta, Ava, Hamat y Sefarvaim, que temen a Jehová y sirven a sus dioses.", S5),
    ("18:1", "18:12", "Ezequías", "Ezequías quita los altos y hace pedazos la serpiente de bronce de Moisés; en su sexto año cae Samaria.", S6),
    ("18:13", "18:37", "Senaquerib y Rabsaces", "Senaquerib toma las ciudades de Judá; desde el conducto del estanque de arriba, Rabsaces habla al pueblo contra Ezequías.", S6),
    ("19:1", "19:19", "Ezequías ora", "Ezequías se cubre de saco y envía a Isaías; extiende ante Jehová las cartas de Senaquerib y ora.", S6),
    ("19:20", "19:37", "La respuesta de Isaías", "Isaías anuncia que el rey de Asiria no entrará en Jerusalén; el ángel de Jehová hiere el campamento asirio, y Senaquerib vuelve a Nínive.", S6),
    ("20:1", "20:11", "Enfermedad de Ezequías", "Ezequías ora y Jehová le añade quince años; como señal, la sombra vuelve atrás diez grados en el reloj de Acaz.", S6),
    ("20:12", "20:21", "Los enviados de Babilonia", "Ezequías muestra sus tesoros a los enviados de Berodac-baladán; Isaías anuncia que todo será llevado a Babilonia.", S6),
    ("21:1", "21:18", "Manasés", "Manasés reedifica los altos, levanta altares a Baal en la casa de Jehová y llena Jerusalén de sangre inocente.", S7),
    ("21:19", "21:26", "Amón", "Amón anda en los caminos de su padre; sus siervos lo matan, y el pueblo pone por rey a Josías.", S7),
    ("22:1", "22:20", "El libro de la ley", "Hilcías dice a Safán: «El libro de la ley he hallado»; Josías rasga sus vestidos y consultan a la profetisa Hulda.", S7),
    ("23:1", "23:14", "Josías renueva el pacto", "Josías lee el libro del pacto al pueblo y quita del templo y de Judá los ídolos, los altos y los caballos del sol.", S7),
    ("23:15", "23:27", "Betel; la pascua", "Josías destruye el altar de Betel, conforme a la palabra del varón de Dios, y celebra una pascua como no la hubo desde los jueces.", S7),
    ("23:28", "23:37", "Muerte de Josías; Joacaz y Joacim", "Faraón Necao mata a Josías en Megido; prende a Joacaz y pone por rey a Eliaquim con el nombre de Joacim.", S7),
    ("24:1", "24:20", "Joacim, Joaquín y Sedecías", "Joacim sirve a Nabucodonosor y se rebela; Joaquín es llevado a Babilonia con los tesoros del templo, y Sedecías reina en su lugar.", S8),
    ("25:1", "25:21", "La caída de Jerusalén", "Nabucodonosor cerca Jerusalén; Sedecías es apresado en las llanuras de Jericó, y Nabuzaradán quema la casa de Jehová y derriba los muros.", S8),
    ("25:22", "25:30", "Gedalías; Joaquín liberado", "Gedalías gobierna a los que quedan en Judá hasta que Ismael lo mata; Evil-merodac saca a Joaquín de la cárcel en Babilonia.", S8),
]

# ---------------------------------------------------------------- lugares
# Lugares que la detección automática no halla porque la RV1909 escribe otra forma (obid de OpenBible -> (id, nombre,
# formas RV1909, tipo, nota, confianza baja)). Edom amplía sus formas con «Idumea» (3:8-26).
LUGARES_MANUAL = {
    "a2735ff": ("edom", "Edom", ["Edom", "Idumea"], "region", "", False),
    # Formas fijas: la detección automática tomaba «Galilea» por Galaad (15:29) y «Zachârías» por Samaria (15:8).
    "ae73b90": ("galaad", "Galaad", ["Galaad"], "region", "", False),
    "a041bb3": ("samaria", "Samaria", ["Samaria"], "ciudad", "", False),
    "a5eb047": ("lebo-hamat", "Lebo-hamat (entrada de Hamat)", ["entrada de Amath"], "ciudad", "", False),  # 14:25
    "abed304": ("mar-salado", "Mar Salado (mar Muerto)", ["mar de la llanura"], "mar", "", False),  # 14:25
    "a062b95": ("ijon", "Ijón", ["Ahión"], "ciudad", "La RV1909 escribe «Ahión» (2 R 15:29).", False),
    "af936bd": ("valle-de-la-sal", "Valle de la Sal", ["valle de las Salinas"], "otro",
                "La RV1909 dice «el valle de las Salinas» (2 R 14:7).", False),
    "abd9596": ("monte-sion", "Monte de Sión", ["monte de Sión"], "monte",
                "2 R 19:31: «del monte de Sión». OpenBible lo distingue de Sión (la fortaleza, 2 S 5:7) por su "
                "identificación moderna.", False),
    "ac5a1ec": ("cus-19-9", "Etiopía (Cus, 2R 19:9)", ["Ethiopía"], "region",
                "«Thiraca rey de Ethiopía» (2 R 19:9): la RV1909 traduce Cus por Etiopía. OpenBible lo distingue del Cus "
                "de Gn 2:13 y lo identifica con Meroe.", False),
}
PRECEDIDO = {}
EXCLUIR_LUGAR = {}
# Ramot de Galaad (8:28; 9:1-14) y «Ramoth» (8:29, OpenBible «Ramah 5», misma identificación moderna, Tall er Rumeith):
# el lugar de 1 R 22.
UNIR_LUGAR_MANUAL = {"a2fe63c": "ramot-galaad", "ad27541": "ramot-galaad",
                     "a736f6c": "mizpa-18-26"}  # la Mizpa de Gedalías (25:23, 25), unida como en Jue, 1 S y 1 R
FORMAS_UNIR = {}
UNIR_LUGAR = {}
NOMBRE_LUGAR = {"Jerusalem": "Jerusalén", "Beth-el": "Betel", "Beer-seba": "Beerseba", "Beth-lehem": "Belén"}
NOMBRE_OB = {}
LUGARES = {}
LUGAR_OPCIONAL = set()
EXCL_AUTO = {}
INFO_AUTO = {}
moderno = josue.moderno
INFO_VERSIFICACION = {}


def comprobar_tvtms(errores):
    """TVTMS (STEPBible): en 2 Reyes la numeración inglesa y la hebrea solo difieren en 11:21–12:21."""
    ruta = Path(__file__).resolve().parent / "cache" / "tvtms.txt"
    if not ruta.exists():
        errores.append(f"2 Reyes: falta {ruta} para comprobar la versificación hebrea (TVTMS)")
        return
    bloques = set()
    for linea in ruta.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\$(2Ki\.\S+)\t", linea)
        if m:
            bloques.add(m.group(1))
    if bloques != TVTMS_2R:
        errores.append(f"2 Reyes: TVTMS da otras diferencias inglés/hebreo {sorted(bloques)} (se esperaba {sorted(TVTMS_2R)})")
    INFO_VERSIFICACION["tvtms"] = sorted(bloques)


def comprobar_versificacion(rv, br, errores):
    """Recuentos, extremos, versículos sin LXX, desfase por capítulo, nombres paralelos, longitudes y TVTMS."""
    for c, n in enumerate(POR_CAPITULO, 1):
        hay = sum(1 for (cc, _) in rv if cc == c)
        if hay != n:
            errores.append(f"2 Reyes {c}: la RV1909 tiene {hay} versículos (numeración inglesa: {n})")
    vacios = sorted(k for k, t in rv.items() if not t.strip())
    if vacios != sorted(VACIOS):
        errores.append(f"2 Reyes: versículos vacíos {vacios} (se esperaban {sorted(VACIOS)})")
    for ref, ini in VERSIFICACION:
        if not rv.get(ref, "").startswith(ini):
            errores.append(f"Versificación de 2 R {ref[0]}:{ref[1]}: la RV1909 no empieza «{ini}»")
    for ref, fin in FIN_VERSICULO:
        if not rv.get(ref, "").endswith(fin):
            errores.append(f"Versificación de 2 R {ref[0]}:{ref[1]}: la RV1909 no termina «{fin}»")
    for ref, frag in VERSIFICACION_LXX:
        if frag not in br.get(ref, ""):
            errores.append(f"Brenton 2 R {ref[0]}:{ref[1]} (numeración RV) no dice «{frag}»")
    falta = {k for k in rv if k not in br}
    if falta != SIN_LXX or [k for k in br if k not in rv]:
        errores.append(f"2 Reyes: versículos sin Brenton {sorted(falta ^ SIN_LXX)} o de más {[k for k in br if k not in rv]}")
    costes = {}
    for c in range(1, CAPITULOS + 1):
        def coste(d):
            xs = [abs(math.log(len(rv[(c, v)]) / len(br[(c, v + d)]))) for (cc, v) in rv
                  if cc == c and rv[(c, v)] and (c, v) in br and (c, v + d) in br]
            return sum(xs) / len(xs)
        costes[c] = (coste(0), coste(-1), coste(1))
        if not costes[c][0] < min(costes[c][1:]):
            errores.append(f"Versificación de 2 R {c}: el emparejamiento con desfase compara mejor que sin él {costes[c]}")
    INFO_VERSIFICACION["desfase"] = {c: tuple(round(x, 2) for x in v) for c, v in costes.items()}
    comunes = {k for k in rv if k in br and rv[k]}
    for es, en in PARALELOS:
        a = {k for k in comunes if re.search(r"(?<!\w)%s(?!\w)" % re.escape(es), rv[k])}
        b = {k for k in comunes if re.search(r"(?<!\w)%s" % re.escape(en), br[k])}
        if a != b or not a:
            errores.append(f"Versificación de 2 R: «{es}» (RV1909) y «{en}» (Brenton) no caen en los mismos versículos: "
                           f"solo RV {sorted(a - b)}, solo LXX {sorted(b - a)}")
    for k in sorted(comunes):
        r = len(rv[k]) / len(br[k])
        if not PROPORCION[0] <= r <= PROPORCION[1]:
            errores.append(f"Versificación de 2 R {k[0]}:{k[1]}: longitud RV1909/Brenton fuera de rango ({r:.2f})")
    INFO_VERSIFICACION["comunes"] = len(comunes)
    INFO_VERSIFICACION["sin_lxx"] = len(falta)
    comprobar_tvtms(errores)


def _reasignar_pv(filas, errores):
    """Aplica PV_REASIGNAR a las filas de BibleData-PersonVerse (copias) y comprueba que se usó cada entrada."""
    usadas, out = set(), []
    for r in filas:
        ref = tuple(map(int, r["reference_id"][4:].split(":")))
        nuevo = PV_REASIGNAR.get((r["person_id"], ref))
        if nuevo:
            usadas.add((r["person_id"], ref))
            r = {**r, "person_id": nuevo}
        out.append(r)
    for k in set(PV_REASIGNAR) - usadas:
        errores.append(f"PV_REASIGNAR sin uso: {k}")
    return out


def _citas_resumen(rv, errores):
    """Toda frase entre «» de un resumen de pasaje debe estar literal en algún versículo del pasaje."""
    orden = sorted(rv)
    for ini, fin, titulo, resumen, _ in PASAJES:
        a, b = tuple(map(int, ini.split(":"))), tuple(map(int, fin.split(":")))
        textos = [rv[k] for k in orden if a <= k <= b]
        for frag in re.findall(r"«([^»]+)»", resumen):
            if not any(frag in t for t in textos):
                errores.append(f"Resumen de 2 R {ini}–{fin}: «{frag}» no está en el pasaje")


def construir(cx):
    rv, br, errores = cx["rv"], cx["br"], cx["errores"]
    comprobar_versificacion(rv, br, errores)
    _citas_resumen(rv, errores)
    cx = {**cx, "pv_filas": _reasignar_pv(cx["pv_filas"], errores)}
    res = exodo.construir(cx, sys.modules[__name__])
    for x in res["relaciones"]:
        if (x["de"], x["a"], x["tipo"]) in INFERIDAS:
            x["certeza"] = "inferido"
    faltan = INFERIDAS - {(x["de"], x["a"], x["tipo"]) for x in res["relaciones"]}
    if faltan:
        errores.append(f"2 Reyes: relaciones inferidas sin crear {sorted(faltan)}")
    for p in res["nuevas"]:
        if p["id"] in SEXO_PROPIO:
            p["sexo"] = SEXO_PROPIO[p["id"]]  # id propio (no está en BibleData-Person)
    # Nimsi → Jehú (de 1 R 19:16): 2 R 9:2 y 9:14 lo hacen abuelo. Se anota sin cambiar la relación.
    x = next((x for x in cx["relaciones"] if (x["de"], x["a"], x["tipo"]) == ("Nimshi_1", "Jehu_2", "padre")), None)
    if not x:
        errores.append("2 Reyes: falta la relación Nimsi → Jehú de 1 R 19:16")
    elif NOTA_NIMSI not in x["nota"]:
        x["nota"] = (x["nota"] + " " + NOTA_NIMSI).strip()
    # Homónimos en el mismo versículo: por orden de aparición (ORDEN_MENCIONES).
    for (c, v), (forma, pids) in ORDEN_MENCIONES.items():
        R, t = f"{LIBRO} {c}:{v}", rv[(c, v)]
        pos = [m.start() for m in re.finditer(r"(?<!\w)%s(?!\w)" % re.escape(forma), t)]
        if len(pos) != len(pids):
            errores.append(f"ORDEN_MENCIONES {R}: «{forma}» aparece {len(pos)} veces (se esperaban {len(pids)})")
            continue
        tramos = [(exodo._u16(t, i), exodo._u16(t, i + len(forma))) for i in pos]
        res["menciones"] = [m for m in res["menciones"] if not (m["ref"] == R and (m["inicio"], m["fin"]) in tramos)]
        for (a, b), pid in zip(tramos, pids):
            if R not in next((p["refs"] for p in cx["personas"] if p["id"] == pid), []):
                errores.append(f"ORDEN_MENCIONES {R}: {pid} no tiene esa ref")
            res["menciones"].append({"ref": R, "persona": pid, "inicio": a, "fin": b})
        res["ambiguos"] = [y for y in res["ambiguos"] if not y.startswith(f"{R} «{forma}»")]
    res["menciones"].sort(key=lambda m: (exodo.parse_ref(m["ref"]), m["inicio"]))
    # «la ciudad de David»: el nombre de David forma parte del nombre del lugar (como en 2 S y 1 R).
    for ref in sorted(k for k, t in rv.items() if "ciudad de David" in t):
        R, t = f"{LIBRO} {ref[0]}:{ref[1]}", rv[ref]
        quitar = [m for m in res["menciones"] if m["ref"] == R and m["persona"] == "David_1"
                  and t.encode("utf-16-le")[:2 * m["inicio"]].decode("utf-16-le").endswith("iudad de ")]
        if len(quitar) != t.count("ciudad de David"):
            errores.append(f"2 R {ref[0]}:{ref[1]}: «ciudad de David» sin mención de David que quitar ({len(quitar)})")
        for m in quitar:
            res["menciones"].remove(m)
        INFO_VERSIFICACION.setdefault("ciudad_de_david", []).append(f"{ref[0]}:{ref[1]}")
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
    return exodo.construir_lugares(rv, menciones_personas, rutas, lugares_previos, errores, avisos, sa,
                                   sys.modules[__name__])


# ---------------------------------------------------------------- hechos obligatorios (sobre los datos finales)
def comprobar(datos, errores):
    """Comprueba los hechos pedidos para 2 Reyes (falla si falta alguno). Devuelve líneas de informe."""
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
            errores.append(f"Hecho obligatorio (2 Reyes): {desc}")

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

    def dice(ref, frag):
        return frag in texto.get(ref, "")

    ok_(len(caps) == CAPITULOS and len(texto) == VERSICULOS and [len(c["versiculos"]) for c in caps] == POR_CAPITULO
        and all(texto.values()), f"{CAPITULOS} capítulos y {VERSICULOS} versículos, ninguno vacío (hay {len(caps)} y {len(texto)})")
    ok_(texto["2R 11:21"].startswith("Era Joas de siete años") and texto["2R 12:1"].startswith("EN el séptimo año de Jehú")
        and INFO_VERSIFICACION.get("tvtms") == sorted(TVTMS_2R),
        "versificación: 11:21 «Era Joas de siete años» (hebreo y LXX 12:1); TVTMS sin otras diferencias")
    ok_(dice("2R 2:11", "Elías subió al cielo en un torbellino") and tiene("Elijah_1", "2R 2:11")
        and "1R 17:1" in P["Elijah_1"]["refs"], "2:11: «Elías subió al cielo en un torbellino» (el Elías de 1 R)")
    ok_(dice("2R 5:1", "NAAMÁN, general del ejército del rey de Siria") and tiene("Naaman_2", "2R 5:1")
        and sin_libro("Naaman_1", "2R "), "5:1: «NAAMÁN, general del ejército del rey de Siria» (no el hijo de Benjamín)")
    ok_(dice("2R 8:26", "Athalía hija de Omri rey de Israel") and tiene("Athaliah_1", "2R 8:26")
        and rel("Omri_1", "Athaliah_1", "padre", "2R 8:26") and rel("Athaliah_1", "Ahaziah_2", "madre", "2R 8:26")
        and rel("Ahab_1", "Athaliah_1", "padre", "2R 8:18", "inferido") and "no se armoniza" in R[("Omri_1", "Athaliah_1", "padre")]["nota"].lower()
        and dice("2R 8:18", "una hija de Achâb fué su mujer") and rel("Athaliah_1", "Jehoram_1", "conyuge", "2R 8:18", "inferido"),
        "8:26: «Athalía hija de Omri rey de Israel», madre de Ocozías; 8:18 «una hija de Achâb» (inferido), sin armonizar")
    ok_(dice("2R 9:2", "Jehú hijo de Josaphat hijo de Nimsi") and tiene("Jehu_2", "2R 9:2") and "1R 19:16" in P["Jehu_2"]["refs"]
        and tiene("Jehoshaphat_4", "2R 9:2") and rel("Jehoshaphat_4", "Jehu_2", "padre", "2R 9:2")
        and rel("Nimshi_1", "Jehoshaphat_4", "padre", "2R 9:2") and sin_libro("Jehoshaphat_3", "2R 9:")
        and sin_libro("Jehoshaphat_4", "2R 3:") and NOTA_NIMSI in R[("Nimshi_1", "Jehu_2", "padre")]["nota"],
        "9:2: «Jehú hijo de Josaphat hijo de Nimsi» (el Jehú de 1 R 19:16; su padre Josafat ≠ el rey Josafat)")
    ok_(dice("2R 12:1", "El nombre de su madre fué Sibia, de Beer-seba") and tiene("Joash_3", "2R 12:1")
        and rel("Zibiah_1", "Joash_3", "madre", "2R 12:1"), "12:1: Joás, «El nombre de su madre fué Sibia, de Beer-seba»")
    ok_(dice("2R 16:20", "reinó en su lugar Ezechîas su hijo") and rel("Ahaz_1", "Hezekiah_1", "padre", "2R 16:20")
        and tiene("Ahaz_1", "2R 16:20") and tiene("Hezekiah_1", "2R 16:20"), "16:20: Acaz, «reinó en su lugar Ezechîas su hijo»")
    ok_(dice("2R 17:6", "En el año nueve de Oseas tomó el rey de Asiria á Samaria") and tiene("Hoshea_1", "2R 17:6")
        and ("2R 17:6", "samaria") in ML, "17:6: «En el año nueve de Oseas tomó el rey de Asiria á Samaria»")
    ok_(dice("2R 18:13", "Sennachêrib rey de Asiria") and tiene("Sennacherib_1", "2R 18:13"), "18:13: «Sennachêrib rey de Asiria»")
    ok_(dice("2R 21:1", "el nombre de su madre fué Hepsiba") and tiene("Manasseh_3", "2R 21:1")
        and rel("Hephzibah_1", "Manasseh_3", "madre", "2R 21:1") and sin_libro("Manasseh_1", "2R 2"),
        "21:1: Manasés (el rey, no el hijo de José), «el nombre de su madre fué Hepsiba»")
    ok_(dice("2R 22:8", "El libro de la ley he hallado") and tiene("Hilkiah_2", "2R 22:8") and tiene("Shaphan_1", "2R 22:8")
        and dice("2R 22:8", "Saphán escriba") and sin_libro("Hilkiah_1", "2R 22"),
        "22:8: «Hilcías» (el sumo sacerdote) y «Saphán escriba»: «El libro de la ley he hallado»")
    ok_(dice("2R 23:29", "Faraón Nechâo") and dice("2R 23:29", "en Megiddo") and tiene("Pharaoh Neco_1", "2R 23:29")
        and tiene("Josiah_1", "2R 23:29") and ("2R 23:29", "meguido") in ML, "23:29: «Faraón Nechâo»; Josías muerto «en Megiddo»")
    ok_(dice("2R 24:1", "Nabucodonosor rey de Babilonia") and tiene("Nebuchadnezzar_1", "2R 24:1") and tiene("Eliakim_2", "2R 24:1")
        and P["Eliakim_2"].get("identidad", {}).get("certeza") == "texto", "24:1: «Nabucodonosor rey de Babilonia» y Joacim (= Eliaquim, 23:34)")
    ok_(dice("2R 25:7", "Sedecías") and tiene("Mattaniah_1", "2R 25:7") and sin_libro("Zedekiah_1", "2R ")
        and P["Mattaniah_1"].get("identidad", {}).get("certeza") == "texto", "25:7: Sedecías (= Matanías, 24:17; no el profeta de 1 R 22)")
    ok_(dice("2R 25:27", "Evil-merodach rey de Babilonia") and dice("2R 25:27", "Joachîn rey de Judá")
        and tiene("Evil-merodach_1", "2R 25:27") and tiene("Jehoiachin_1", "2R 25:27"),
        "25:27: «Evil-merodach rey de Babilonia» y «Joachîn rey de Judá»")
    # identidades y homónimos
    ok_(all(r in P["Azariah_3"]["refs"] for r in ("2R 14:21", "2R 15:1", "2R 15:13", "2R 15:32"))
        and P["Azariah_3"].get("identidad", {}).get("certeza") == "inferido" and tiene("Azariah_3", "2R 15:13")
        and sin_libro("Azariah_1", "2R ") and sin_libro("Azariah_2", "2R "),
        "Azarías (14:21) y «Uzzía» (15:13, 30): un id de BibleData, identidad inferida")
    ok_(tiene("Jehoram_2", "2R 3:1") and tiene("Jehoram_1", "2R 8:16") and tiene("Jehoram_2", "2R 8:16")
        and sin_libro("Jehoram_1", "2R 3:") and sin_libro("Jehoram_1", "2R 9:") and ("2R 9:24", "Jehoram_2") in M,
        "Joram de Israel (Jehoram_2) ≠ Joram de Judá (Jehoram_1); en 2 R 3 el rey de Judá es Josafat")
    ok_(tiene("Ahaziah_1", "2R 1:2") and tiene("Ahaziah_2", "2R 8:25") and sin_libro("Ahaziah_1", "2R 8")
        and sin_libro("Ahaziah_2", "2R 1:"), "Ocozías de Israel (1:2) ≠ Ocozías de Judá (8:25)")
    ok_(tiene("Joash_3", "2R 14:1") and tiene("Joash_4", "2R 14:1") and tiene("Joash_4", "2R 13:10")
        and tiene("Joash_3", "2R 13:10") and sin_libro("Joash_1", "2R ") and sin_libro("Joash_2", "2R "),
        "Joás de Judá (Joash_3) ≠ Joás de Israel (Joash_4), asignados por orden en 13:10 y 14:1")
    ok_(tiene("Jehoahaz_1", "2R 13:1") and tiene("Jehoahaz_2", "2R 23:31") and sin_libro("Jehoahaz_1", "2R 23")
        and tiene("Jeroboam_2", "2R 14:23") and tiene("Jeroboam_1", "2R 14:24") and sin_libro("Jeroboam_1", "2R 14:23"),
        "Joacaz de Israel ≠ Joacaz de Judá; Jeroboam hijo de Joás ≠ Jeroboam hijo de Nabat")
    ok_(tiene("Ben-hadad_2", "2R 13:3") and rel("Hazael_1", "Ben-hadad_2", "padre", "2R 13:3") and sin_libro("Ben-hadad_1", "2R 13")
        and tiene("Eliakim_1", "2R 18:18") and tiene("Eliakim_2", "2R 23:34") and tiene("Hilkiah_1", "2R 18:18")
        and tiene("Zechariah_1", "2R 15:8") and tiene("Zechariah_2", "2R 18:2") and tiene("Shallum_1", "2R 15:13")
        and tiene("Shallum_2", "2R 22:14") and tiene("Seraiah_2", "2R 25:18") and tiene("Seraiah_3", "2R 25:23")
        and tiene("Amon_2", "2R 21:19") and sin_libro("Amon_1", "2R ") and tiene("Uzza_1", "2R 21:18")
        and tiene("Zadok_2", "2R 15:33") and sin_libro("Zadok_1", "2R "),
        "homónimos: Ben-adad hijo de Hazael, Eliaquim, Hilcías, Zacarías, Salum, Seraías, Amón, Uza y Sadoc")
    ok_(not [p for p in EXCLUIR if any(r.startswith("2R ") for r in P.get(p, {}).get("refs", []))]
        and P.get(SUNAMITA, {}).get("sin_nombre") and tiene(MAACATI, "2R 25:23") and sin_libro("Hoshaiah_2", "2R ")
        and sin_libro("So_1", "2R 18") and all(p in P for p in ("Rabshakeh_1", "Tartan_1", "Rab-saris_1")),
        "sin Dios, «NA», el ángel ni los reyes sin nombre; la sunamita sin nombre; Maacati (25:23) con id propio; "
        "So no es el Faraón de 18:21; Rabsaces, Tartán y Rabsaris como en el texto")
    e = {(x["persona"], x["tradicion"]): x["valor"] for x in datos["edades"] if x["ref"].startswith("2R ")}
    ok_(e.get(("Joash_3", "TM")) == 7 and e.get(("Josiah_1", "TM")) == 8 and e.get(("Manasseh_3", "TM")) == 12
        and e.get(("Hezekiah_1", "LXX")) == 25 and all(e.get((p, "TM")) == e.get((p, "LXX")) for p, _ in e),
        f"edades al comenzar a reinar (TM = LXX): {len(e) // 2} reyes")
    for lid, ref in (("samaria", "2R 17:6"), ("jerico", "2R 2:4"), ("betel", "2R 2:23"), ("sunem", "2R 4:8"),
                     ("dotan", "2R 6:13"), ("damasco", "2R 8:7"), ("meguido", "2R 9:27"), ("jezreel", "2R 9:30"),
                     ("laquis", "2R 18:14"), ("ninive", "2R 19:36"), ("babilonia", "2R 20:12"), ("ribla-23-33", "2R 25:6"),
                     ("ramot-galaad", "2R 8:28"), ("ramot-galaad", "2R 8:29"), ("edom", "2R 3:8"), ("ijon", "2R 15:29"),
                     ("lebo-hamat", "2R 14:25"), ("mar-salado", "2R 14:25"),
                     ("hala", "2R 17:6"), ("habor", "2R 17:6"), ("gozan", "2R 17:6"), ("jordan", "2R 2:13")):
        ok_(lid in L and ref in L[lid]["refs"] and (ref, lid) in ML, f"lugar {lid} en {ref}")
    sin = [l for l in datos["lugares"] if any(r.startswith("2R ") for r in l["refs"]) and not l["ubicacion"]]
    ok_(all("OpenBible no da identificación" in l["nota"] or l["id"] == "tarsis" for l in sin)
        and L["ribla"]["refs"][-1][:3] != "2R " and "Idumea" in L["edom"]["formas_rv1909"]
        and L["samaria"]["formas_rv1909"] == ["Samaria"] and L["galaad"]["formas_rv1909"] == ["Galaad"]
        and ("2R 25:23", "mizpa-18-26") in ML,
        f"lugares de 2 R sin coordenadas con nota ({len(sin)}); la Ribla de 2 R (23:33) no es la de Nm 34:11; Edom = «Idumea»; "
        "Mizpa (25:23) = la de Jue–1 R; Samaria y Galaad sin formas ajenas")
    C = datos["cronologia"]
    rein = [r for r in C.get("reinados", []) if r["duracion"]["TM"]["ref"].startswith("2R ")]
    calc = C.get("calculos_2r", [])
    hitos = [h for h in C["hitos_sin_fecha"] if h["ref"].startswith("2R ")]
    ok_(len(rein) == 27 and all(r["certeza"] == "texto" and r["duracion"]["TM"]["valor"] for r in rein)
        and len(calc) == 6 and all(c["certeza"] == "calculo" and c["advertencia"] and c["pasos"]
                                   and c["comparacion"]["TM"]["valor"] is not None for c in calc)
        and not any(re.search(r"a\. ?C\.|antes de Cristo", h["nota"]) and "Nada de 2 Reyes" not in h["nota"] for h in hitos)
        and not any((e.get("ref") or "").startswith("2R ") for e in C["eventos"]),
        f"cronología: {len(rein)} reinados con cita, {len(calc)} cálculos de sincronismos que no cuadran, sin años a. C. "
        "ni años desde Adán")
    pas = [p for p in datos["pasajes"] if p["libro"] == LIBRO]
    ok_(len(pas) == len(PASAJES) and pas[0]["inicio"] == "2R 1:1" and pas[-1]["fin"] == "2R 25:30" and pas[0]["id"] == "2r-01",
        f"{len(pas)} pasajes 2r-NN de 2R 1:1 a 2R 25:30")
    ok_(len({p["seccion"] for p in pas}) == 8, "8 secciones")
    ids = [p["id"] for p in datos["pasajes"]]
    ult_1r = max(i for i, p in enumerate(datos["pasajes"]) if p["libro"] == "1R")
    lb = [l["id"] for l in datos["libros"]]
    ok_(ids.index(pas[0]["id"]) == ult_1r + 1 and lb.index(LIBRO) == lb.index("1R") + 1
        and (lb[-1] == LIBRO or lb[lb.index(LIBRO) + 1] == "1Cr"),
        "2 Reyes va justo después de 1 Reyes en el orden de los pasajes (lectura en orden)")
    return lineas
