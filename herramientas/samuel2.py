"""2 Samuel 1–24: personas, relaciones, edades, pasajes, menciones y lugares (lo usa construir_datos.py).

Id del libro: «2S» (el código canónico de CANON en app.js), como «1S». Reutiliza la lógica de exodo.py
(exodo.construir / exodo.construir_lugares con este módulo como configuración) y la detección automática de lugares de
josue.py (josue.lugares_auto), como 1 Samuel. Cada dato lleva versículo, fuente y certeza; las citas se comprueban
literalmente contra la RV1909 (TM) o Brenton (LXX). Las personas de Génesis–1 Samuel (David, Saúl, Jonatán, Abner, Joab,
Abisai, Mical, Merab, Abigail, Ahinoam, Abiatar, Nahas, Gad, Isaí, Cis, Goliat, Gedeón/Jerobaal, Abimelec…) son la misma
persona (mismo id de BibleData): se amplían sus `refs`.

Versificación (comprobada al generar, versículo a versículo):
- La RV1909 de eBible tiene 695 versículos con los recuentos de la numeración inglesa (la de BibleData y OpenBible),
  también en 18:33 / 19:1-43, donde el hebreo numera 19:1-44 (TVTMS: «2Sa.18:33--19:43»). Única rareza: deja 20:26
  vacío y pone su texto («é Ira Jaireo fué un jefe principal cerca de David») al final de 20:25. `REMAP_REF` (único
  punto) lleva 20:26 de BibleData y OpenBible a 20:25.
- Brenton (LXX) numera 18–19 como el hebreo (su 19:1 es el 18:33 de la RV1909), tiene 20:26 aparte y no tiene 23:30-31
  (la LXX los resume en 23:29). `br_a_rv` (único punto de versificación de Brenton) lo lleva a la numeración de la
  RV1909. Después se comprueba que en cada capítulo el emparejamiento sin desfase compara mejor (longitudes) que con
  desfase ±1, que nombres poco frecuentes caen en los mismos versículos y los extremos de 18–20 y 23.

Solo biblioteca estándar.
"""
import math
import re
import sys

import exodo
import josue

LIBRO = "2S"
NOMBRE = "2 Samuel"
USX = "2SA"
CAPITULOS = 24
VERSICULOS = 695
POR_CAPITULO = [27, 32, 39, 12, 25, 23, 29, 18, 13, 19, 27, 31, 39, 33, 37, 23, 29, 33, 43, 26, 22, 51, 39, 25]
# Versículo que la RV1909 de eBible deja vacío -> versículo donde está su texto.
VACIOS = {(20, 26): "2S 20:25"}
NOTA_VACIO = ("La RV1909 de eBible no tiene este versículo aparte: su texto («é Ira Jaireo fué un jefe principal cerca "
              "de David») va al final de 2S 20:25.")
# Comienzo/fin de los versículos de las zonas donde el hebreo o la LXX numeran distinto (se comprueban).
VERSIFICACION = [((18, 32), "El rey entonces dijo á Cusi"), ((18, 33), "Entonces el rey se turbó"),
                 ((19, 1), "Y DIERON aviso á Joab"), ((19, 43), "Entonces respondieron los varones de Israel"),
                 ((20, 25), "Y Seba, escriba"), ((23, 29), "Helec hijo de Baana"), ((23, 30), "Benaía Pirathonita"),
                 ((23, 39), "Uría Hetheo")]
FIN_VERSICULO = [((20, 25), "é Ira Jaireo fué un jefe principal cerca de David."),
                 ((18, 33), "Absalom, hijo mío, hijo mío!")]
# Brenton, ya en numeración RV1909 (tras br_a_rv).
VERSIFICACION_LXX = [((18, 33), "And the king was troubled"), ((19, 1), "And they brought Joab word"),
                     ((19, 43), "the speech of the men of Juda was sharper"), ((20, 25), "Moreover Iras"),
                     ((23, 29), "Esthai the son of Riba"), ((23, 32), "the sons of Asan, Jonathan")]
# Versículos sin Brenton (numeración RV1909): 20:26 (vacío en la RV1909) y 23:30-31 (la LXX no los tiene aparte).
SIN_LXX = {(20, 26), (23, 30), (23, 31)}
# Nombres que deben caer en los mismos versículos en la RV1909 y en Brenton (solo versículos que tienen ambos).
PARALELOS = [("Siba", "Siba"), ("Barzillai", "Berzelli"), ("Uría", "Urias"), ("Hanún", "Annon"), ("Arauna", "Orna"),
             ("Hiram", "Chiram"), ("Jonadab", "Jonadab"), ("Sadoc", "Sadoc"), ("Ahimaas", "Achimaas"), ("Rispa", "Respha")]
PROPORCION = (0.15, 4.6)  # longitud RV1909 / Brenton por versículo (observado 0,19–4,51: 7:26, la LXX abrevia)


def REMAP_REF(r):
    """Numeración inglesa (BibleData, OpenBible) -> RV1909. Único punto: 20:26 va dentro de 20:25."""
    return (20, 25) if r == (20, 26) else r


def br_a_rv(br):
    """Brenton (numeración hebrea/LXX en 18–19) -> numeración de la RV1909. Único punto de versificación de Brenton:
    19:1 LXX = 18:33; 19:n LXX = 19:n-1; 20:26 LXX va al final de 20:25."""
    out = {}
    for (c, v), t in sorted(br.items()):
        k = (18, 33) if (c, v) == (19, 1) else (19, v - 1) if c == 19 else (20, 25) if (c, v) == (20, 26) else (c, v)
        out[k] = f"{out[k]} {t}" if k in out else t
    return out


# Personas de BibleData que no se crean: Dios, «NA», el ángel de Jehová (como en Éxodo, Números y Jueces), el «libro de
# Jaser» (1:18; la RV1909 dice «el libro del derecho», como en Josué), el rey de Maaca sin nombre (10:6), los pueblos
# (`Ben-ammi_1` = «los hijos de Ammón»; `Amalek_1` = los amalecitas, 8:12; van como lugares, igual que en 1 Samuel),
# «Rafa» (21:16-22: la RV1909 dice «el gigante») y «Ariel» (23:20: la RV1909 traduce «dos leones de Moab»).
# `Jerubbesheth_1` y `Abimelech_3` (11:21) son Gedeón y su hijo Abimelec (ver NOTAS_EXISTENTES).
EXCLUIR = {"YHVH_1", "NA", "the angel of the LORD_1", "Jashar_1", "King of Maacah_1", "Ben-ammi_1", "Amalek_1",
           "Raphah_1", "Ariel_1", "Jerubbesheth_1", "Abimelech_3"}
# «Israel» es el pueblo: Jacob solo si el texto dice «Jacob» (BibleData no lo sitúa en 2 S).
SOLO_ETIQUETA = {"Jacob_1": {"Jacob"}}
FORMA_NO_MENCION = {("Jacob_1", "israel")}
# Itai geteo (15:19 «tú eres extranjero») e Itai hijo de Ribai, benjamita de Gabaa (23:29), son dos personas: BibleData
# los une en Ittai_1; aquí el de 23:29 lleva id propio.
ITAI = "Ittai_2S23"
_ITAI = ("Itai hijo de Ribai, de Gabaa de Benjamín (2 S 23:29), no es Itai geteo, «extranjero» (2 S 15:19): lleva id "
         "propio (Ittai_2S23).")
PV_DESCARTAR = {("Ittai_1", (23, 29)): _ITAI,
                ("Japhia_2", (5, 15)): ("la RV1909 pone a «Japhia» en 5:16 (la numeración inglesa de BibleData, en 5:15): "
                                        "se usa 5:16 (ver RELACIONES).")}
REL_DESCARTAR = {
    ("Ribai_1", "Ittai_1", "padre"): _ITAI,
    ("Eliahba_1", "Jashen_1", "padre"): ("2 S 23:32 dice «Elihaba de Saalbón, Jonathán de los hijos de Jassén»: no dice "
                                         "que Jasén sea hijo de Eliaba."),
    ("Eliahba_1", "Jonathan_5", "padre"): ("2 S 23:32 dice «Jonathán de los hijos de Jassén»: no dice que sea hijo de "
                                           "Eliaba."),
}
FORMAS_FORZADAS = {
    "Ithream_1": ["Jetream"], "Japhia_2": ["Japhia"], "Ira_1": ["Ira"], "Ikkesh_1": ["Jecces"],
    "Josheb-basshebeth_1": ["Adino"], "Merab_1": ["Michâl"], ITAI: ["Ittai"], "Talmai_2": ["Talmai"],
    "Hiram_1": ["Hiram"], "Hadadezer_1": ["Hadad-ezer"], "Toi_1": ["Toi"], "Sheva_1": ["Seba"],
    "Solomon_1": ["Salomón", "Jedidiah"], "Amnon_1": ["Amnón", "Ammón"], "Absalom_1": ["Absalom", "Absalóm"],
    "Ahilud_1": ["Ahilud", "Ahillud"], "Benaiah_1": ["Benaía", "Benahía"], "Ammiel_2": ["Amiel", "Ammiel"],
    "Sibbecai_1": ["Sibechâi", "Mebunnai"], "Elhanan_1": ["Elhanan", "Elhaanan"], "Jaare-oregim_1": ["Jaare-oregim", "Dodo"],
    "Ahithophel_1": ["Achitophel", "Achîtophel"], "Shammah_2": ["Simea", "Sima"],
}
MODERNO = {
    "Ish-bosheth_1": "Is-boset", "Asahel_1": "Asael", "Amnon_1": "Amnón", "Chileab_1": "Quileab", "Absalom_1": "Absalón",
    "Maacah_2": "Maaca", "Talmai_2": "Talmai", "Adonijah_1": "Adonías", "Haggith_1": "Haguit", "Shephatiah_1": "Sefatías",
    "Abital_1": "Abital", "Ithream_1": "Itream", "Eglah_1": "Egla", "Rizpah_1": "Rizpa", "Aiah_2": "Aja",
    "Baanah_1": "Baana", "Rechab_1": "Recab", "Rimmon_1": "Rimón", "Mephibosheth_1": "Mefi-boset", "Hiram_1": "Hiram",
    "Shammua_2": "Samúa", "Shobab_1": "Sobab", "Nathan_1": "Natán", "Solomon_1": "Salomón", "Ibhar_1": "Ibhar",
    "Elishua_1": "Elisúa", "Nepheg_2": "Nefeg", "Japhia_2": "Jafía", "Elishama_2": "Elisama", "Eliada_1": "Eliada",
    "Eliphelet_1": "Elifelet", "Uzzah_1": "Uza", "Ahio_1": "Ahío", "Obed-edom_1": "Obed-edom", "Nathan_2": "Natán",
    "Hadadezer_1": "Hadad-ezer", "Rehob_1": "Rehob", "Toi_1": "Toi", "Joram_1": "Joram", "Jehoshaphat_1": "Josafat",
    "Ahilud_1": "Ahilud", "Zadok_1": "Sadoc", "Ahitub_2": "Ahitob", "Ahimelech_3": "Ahimelec", "Seraiah_1": "Seraías",
    "Benaiah_1": "Benaía", "Jehoiada_1": "Joiada", "Ziba_1": "Siba", "Machir_2": "Maquir", "Ammiel_2": "Amiel",
    "Mica_1": "Micá", "Hanun_1": "Hanún", "Shobach_1": "Sobac", "Bathsheba_1": "Betsabé", "Eliam_1": "Eliam",
    "Uriah_1": "Urías", "Tamar_2": "Tamar", "Jonadab_1": "Jonadab", "Ammihud_4": "Amiud", "Tamar_3": "Tamar",
    "Ahithophel_1": "Ahitofel", "Ittai_1": "Itai", "Ahimaaz_2": "Ahimaas", "Jonathan_3": "Jonatán", "Hushai_1": "Husai",
    "Shimei_2": "Simei", "Gera_3": "Gera", "Amasa_1": "Amasa", "Ithra_1": "Itra", "Abigail_2": "Abigail",
    "Nahash_2": "Nahas", "Shobi_1": "Sobi", "Barzillai_1": "Barzilai", "Chimham_1": "Quimam", "Sheba_4": "Seba",
    "Bichri_1": "Bicri", "Adoram_1": "Adoram", "Sheva_1": "Seva", "Ira_1": "Ira", "Armoni_1": "Armoni",
    "Mephibosheth_2": "Mefi-boset", "Barzillai_2": "Barzilai", "Ishbi-benob_1": "Isbi-benob", "Sibbecai_1": "Sibecai",
    "Saph_1": "Saf", "Elhanan_1": "Elhanán", "Jaare-oregim_1": "Jaare-oregim", "Jonathan_4": "Jonatán",
    "Josheb-basshebeth_1": "Adino", "Eleazar_3": "Eleazar", "Dodo_2": "Dodo", "Shammah_3": "Sama", "Agee_1": "Age",
    "Shammah_4": "Sama", "Elika_1": "Elica", "Helez_1": "Heles", "Ira_2": "Ira", "Ikkesh_1": "Iques",
    "Abiezer_1": "Abiezer", "Zalmon_1": "Selmo", "Maharai_1": "Maharai", "Heleb_1": "Heleb", "Baanah_2": "Baana",
    "Ribai_1": "Ribai", ITAI: "Itai", "Benaiah_2": "Benaía", "Hiddai_1": "Hidai", "Abi-albon_1": "Abi-albón",
    "Azmaveth_1": "Azmavet", "Eliahba_1": "Eliaba", "Jashen_1": "Jasén", "Jonathan_5": "Jonatán", "Shammah_5": "Sama",
    "Ahiam_1": "Ahíam", "Sharar_1": "Sarar", "Eliphelet_2": "Elifelet", "Ahasbai_1": "Ahasbai", "Eliam_2": "Eliam",
    "Hezro_1": "Hezrai", "Paarai_1": "Paarai", "Igal_2": "Igal", "Nathan_3": "Natán", "Bani_1": "Bani",
    "Zelek_1": "Selec", "Naharai_1": "Naharai", "Ira_3": "Ira", "Gareb_1": "Gareb", "Araunah_1": "Arauna",
}
NOTAS = {
    "Ish-bosheth_1": ("Hijo de Saúl (2 S 2:8); Abner lo hace rey sobre Israel en Mahanaim. «De cuarenta años… y reinó "
                      "dos años» (2 S 2:10). Lo matan Recab y Baana en su cama (2 S 4:5-7)."),
    "Absalom_1": "Tercer hijo de David, de Maaca hija de Talmai rey de Gesur (2 S 3:3). Muere en el bosque de Efraín (2 S 18:9-15).",
    "Mephibosheth_1": ("Hijo de Jonatán hijo de Saúl (2 S 4:4; 9:6), «lisiado de los pies» desde los cinco años (2 S 4:4). "
                       "Distinto de Mefi-boset hijo de Saúl y de Rizpa (2 S 21:8)."),
    "Mephibosheth_2": "Hijo de Saúl y de Rizpa (2 S 21:8). Distinto de Mefi-boset hijo de Jonatán (2 S 4:4; 9:6).",
    "Nathan_1": "Hijo de David nacido en Jerusalén (2 S 5:14). Distinto del profeta Natán.",
    "Nathan_2": "Profeta (2 S 7:2; 12:25). Distinto de Natán hijo de David (2 S 5:14) y del padre de Igal (2 S 23:36).",
    "Nathan_3": "Padre de Igal, de Soba (2 S 23:36). Distinto del profeta y del hijo de David.",
    "Solomon_1": ("Hijo de David y de Betsabé (2 S 12:24); Jehová, «por mano de Nathán profeta», lo llama Jedidiah "
                  "(2 S 12:25)."),
    "Uzzah_1": "Hijo de Abinadab (2 S 6:3); toca el arca y muere junto a ella (2 S 6:6-7).",
    "Zadok_1": ("Sacerdote (2 S 8:17; 15:24-29). La RV1909 de eBible escribe «Sadoc hijo de Ahitud» en 8:17; Brenton (LXX) "
                "«Sadoc the son of Achitob»."),
    "Ahitub_2": ("Padre de Sadoc (2 S 8:17). La RV1909 de eBible escribe «Ahitud»; Brenton (LXX), «Achitob». BibleData lo "
                 "distingue de Ahitob padre de Ahimelec (1 S 22:9)."),
    "Ahimelech_3": ("Sacerdote, «hijo de Abiathar» (2 S 8:17). En 1 S 22:20 es al revés: Abiatar es hijo de Ahimelec "
                    "(Ahimelech_1). El texto dice las dos cosas; no se armoniza."),
    "Bathsheba_1": "Hija de Eliam, mujer de Urías heteo (2 S 11:3); después mujer de David (2 S 11:27) y madre de Salomón (2 S 12:24).",
    "Eliam_1": "Padre de Betsabé (2 S 11:3). BibleData lo distingue de Eliam hijo de Ahitofel (2 S 23:34).",
    "Eliam_2": "Hijo de Ahitofel gilonita, de los treinta (2 S 23:34). BibleData lo distingue de Eliam padre de Betsabé (2 S 11:3).",
    "Uriah_1": "Heteo (2 S 11:3), de los valientes de David (2 S 23:39). Muere en el cerco de Rabá por orden de David (2 S 11:15-17).",
    "Tamar_2": ("Hermana de Absalón (2 S 13:1); Amnón la fuerza (2 S 13:14). Distinta de Tamar hija de Absalón (2 S 14:27) "
                "y de Tamar nuera de Judá (Gn 38)."),
    "Tamar_3": "Hija de Absalón, «hermosa de ver» (2 S 14:27). Distinta de Tamar hermana de Absalón (2 S 13:1).",
    "Amnon_1": "Primogénito de David, de Ahinoam (2 S 3:2; la RV1909 escribe «Ammón» en ese versículo). Lo matan los criados de Absalón (2 S 13:28-29).",
    "Jonathan_3": "Hijo del sacerdote Abiatar (2 S 15:27). Distinto de Jonatán hijo de Saúl.",
    "Jonathan_4": "Hijo de Sima hermano de David; mata al gigante de Gat (2 S 21:20-21). Distinto de Jonatán hijo de Saúl.",
    "Jonathan_5": "De los treinta valientes (2 S 23:32). Distinto de Jonatán hijo de Saúl.",
    "Ahimaaz_2": "Hijo de Sadoc (2 S 15:27; 18:19). Distinto de Ahimaas padre de Ahinoam, mujer de Saúl (1 S 14:50).",
    "Abigail_2": ("Madre de Amasa: «hija de Naas, hermana de Sarvia, madre de Joab» (2 S 17:25). Distinta de Abigail, "
                  "mujer de Nabal y de David."),
    "Nahash_2": ("2 S 17:25: «Abigail hija de Naas». BibleData registra a este Naas como mujer (madre de Abigail) y lo "
                 "distingue de Nahas rey de los amonitas; el texto no dice si es padre o madre."),
    "Amasa_1": "Hijo de Itra (2 S 17:25); Absalón lo pone sobre el ejército. Joab lo mata junto a la peña de Gabaón (2 S 20:8-10).",
    "Sheba_4": "Hijo de Bicri, «hombre de Benjamín» (2 S 20:1); se rebela contra David y muere en Abel de Bet-maaca (2 S 20:22).",
    "Sheva_1": "Escriba de David (2 S 20:25). La RV1909 escribe «Seba», como Seba hijo de Bicri; es otra persona.",
    "Ira_1": ("Jaireo, «jefe principal cerca de David» (2 S 20:26 en el hebreo y en la numeración inglesa; en la RV1909 "
              "va al final de 20:25)."),
    "Ira_2": "Hijo de Iques, de Tecoa, de los treinta (2 S 23:26; la RV1909 escribe «Hira»).",
    "Ira_3": "Itrita, de los treinta (2 S 23:38).",
    "Baanah_1": "Hijo de Rimón beerotita; con su hermano Recab mata a Is-boset (2 S 4:2-7).",
    "Baanah_2": "Padre de Heleb, de Netofa (2 S 23:29). Distinto de Baana hijo de Rimón.",
    "Barzillai_1": "Galaadita de Rogelim (2 S 17:27), «de ochenta años» (2 S 19:32). Distinto de Barzilai meholatita (2 S 21:8).",
    "Barzillai_2": "Meholatita, padre de Adriel (2 S 21:8). Distinto de Barzilai galaadita.",
    "Shammah_3": "Hijo de Age ararita, uno de los tres valientes (2 S 23:11). Distinto de Sama hijo de Isaí.",
    "Shammah_4": "De Harod, de los treinta (2 S 23:25). Distinto de Sama hijo de Isaí.",
    "Shammah_5": "De Arar, de los treinta (2 S 23:33). Distinto de Sama hijo de Isaí.",
    "Benaiah_1": "Hijo de Joiada, sobre los cereteos y peleteos (2 S 8:18; 20:23). Distinto de Benaía piratonita (2 S 23:30).",
    "Benaiah_2": "Piratonita, de los treinta (2 S 23:30). Distinto de Benaía hijo de Joiada.",
    "Eleazar_3": "Hijo de Dodo, uno de los tres valientes (2 S 23:9). Distinto de Eleazar hijo de Aarón y del de 1 S 7:1.",
    "Josheb-basshebeth_1": ("2 S 23:8 (RV1909): «El Tachmonita, que se sentaba en cátedra, principal de los capitanes: era "
                            "éste Adino el Eznita». BibleData lo llama Josheb-basshebeth («el que se sentaba en cátedra»)."),
    "Elhanan_1": ("2 S 21:19: «Elhanan, hijo de Jaare-oregim de Beth-lehem, hirió á Goliath Getheo»; 2 S 23:24: «Elhaanan "
                  "hijo de Dodo de Beth-lehem». BibleData los toma por la misma persona (identidad inferida) y asigna a "
                  "ese Goliat el id de 1 S 17 (ver Goliat)."),
    "Jaare-oregim_1": ("Padre de Elhanán (2 S 21:19). BibleData lo identifica con Dodo, padre de Elhaanán de Belén "
                       "(2 S 23:24); el texto no lo dice."),
    "Sibbecai_1": ("2 S 21:18: «Sibechâi Husathita hirió á Saph»; 2 S 23:27: «Mebunnai de Husa». BibleData los identifica; "
                   "el texto no lo dice."),
    ITAI: _ITAI,
    "Ittai_1": "Geteo, «extranjero» (2 S 15:19), que sigue a David con seiscientos de Gat (2 S 15:18-22) y manda un tercio del ejército (2 S 18:2).",
    "Hushai_1": "Arquita, «amigo de David» (2 S 15:32, 37); desbarata el consejo de Ahitofel (2 S 17:14).",
    "Ahithophel_1": "Gilonita, consejero de David que se pasa a Absalón (2 S 15:12); se ahorca (2 S 17:23).",
    "Shimei_2": "Hijo de Gera, de la casa de Saúl; maldice a David en Bahurim (2 S 16:5-13) y luego le pide perdón (2 S 19:16-23).",
    "Araunah_1": "Jebuseo; David le compra la era donde edifica un altar (2 S 24:18-25).",
    "Hiram_1": "Rey de Tiro (2 S 5:11).",
    "Rizpah_1": "Hija de Aja, concubina de Saúl (2 S 3:7; 21:11); vela los cuerpos de sus hijos ahorcados (2 S 21:10).",
    "Maacah_2": "Hija de Talmai rey de Gesur, madre de Absalón (2 S 3:3).",
}
IDENTIDAD = {
    "Shammah_2": {"certeza": "inferido", "refs": ["2S 13:3", "2S 13:32", "2S 21:21"], "nombres_rv1909": ["Simea", "Sima"],
                  "fuente": "bibledata",
                  "nota": ("2 S 13:3 y 13:32: «Jonadab, hijo de Simea, hermano de David»; 21:21: «Jonathán, hijo de Sima "
                           "hermano de David». BibleData lo identifica con Samma, tercer hijo de Isaí (1 S 16:9; 17:13): el "
                           "texto dice que es hermano de David, no que sea Samma.")},
    "Merab_1": {"certeza": "inferido", "refs": ["2S 21:8"], "nombres_rv1909": ["Michâl"], "fuente": "bibledata",
                "nota": ("2 S 21:8 (RV1909, TM; también Brenton, LXX: «Michol»): «cinco hijos de Michâl hija de Saúl, los "
                         "cuales ella había parido á Adriel». Adriel es el marido de Merab (1 S 18:19) y Mical «nunca tuvo "
                         "hijos» (2 S 6:23): BibleData asigna el versículo a Merab. No lo dice el texto: identidad inferida.")},
    "Elhanan_1": {"certeza": "inferido", "refs": ["2S 21:19", "2S 23:24"], "nombres_rv1909": ["Elhanan", "Elhaanan"],
                  "fuente": "bibledata",
                  "nota": ("21:19 «Elhanan, hijo de Jaare-oregim de Beth-lehem»; 23:24 «Elhaanan hijo de Dodo de "
                           "Beth-lehem». BibleData los toma por la misma persona; el texto no lo dice.")},
    "Jaare-oregim_1": {"certeza": "inferido", "refs": ["2S 21:19", "2S 23:24"], "nombres_rv1909": ["Jaare-oregim", "Dodo"],
                       "fuente": "bibledata",
                       "nota": "BibleData identifica a Jaare-oregim (21:19) con Dodo (23:24), padres de Elhanán; el texto no lo dice."},
    "Sibbecai_1": {"certeza": "inferido", "refs": ["2S 21:18", "2S 23:27"], "nombres_rv1909": ["Sibechâi", "Mebunnai"],
                   "fuente": "bibledata",
                   "nota": ("21:18 «Sibechâi Husathita»; 23:27 «Mebunnai de Husa». BibleData los toma por la misma "
                            "persona; el texto no lo dice.")},
}
NOTAS_VERIFICAR = [
    ("TM", (2, 8), "Is-boseth hijo de Saúl"), ("TM", (2, 10), "De cuarenta años era Is-boseth"),
    ("TM", (2, 10), "reinó dos años"), ("TM", (4, 5), "Rechâb y Baana"), ("TM", (4, 4), "lisiado de los pies"),
    ("TM", (4, 4), "de edad de cinco años"), ("TM", (9, 6), "Mephi-boseth, hijo de Jonathán hijo de Saúl"),
    ("TM", (21, 8), "Rispa hija de Aja"), ("TM", (5, 14), "Nathán"), ("TM", (7, 2), "al profeta Nathán"),
    ("TM", (12, 25), "Nathán profeta"), ("TM", (23, 36), "Igheal hijo de Nathán de Soba"), ("TM", (12, 25), "Jedidiah"),
    ("TM", (6, 7), "cayó allí muerto junto al arca de Dios"), ("TM", (8, 17), "Sadoc hijo de Ahitud"),
    ("LXX", (8, 17), "Sadoc the son of Achitob"), ("TM", (8, 17), "Ahimelech hijo de Abiathar"),
    ("TM", (11, 3), "Bath-sheba hija de Eliam, mujer de Uría Hetheo"), ("TM", (11, 27), "fué ella su mujer"),
    ("TM", (12, 24), "llamó su nombre Salomón"), ("TM", (23, 34), "Eliam hijo de Achîtophel"),
    ("TM", (23, 39), "Uría Hetheo"), ("TM", (13, 1), "una hermana hermosa que se llamaba Thamar"),
    ("TM", (13, 14), "la forzó"), ("TM", (14, 27), "hermosa de ver"), ("TM", (13, 28), "Herid á Amnón"),
    ("TM", (15, 27), "Jonathán hijo de Abiathar"), ("TM", (21, 21), "Jonathán, hijo de Sima hermano de David"),
    ("TM", (23, 32), "Jonathán de los hijos de Jassén"), ("TM", (18, 19), "Ahimaas hijo de Sadoc"),
    ("TM", (17, 25), "Abigail hija de Naas, hermana de Sarvia, madre de Joab"), ("TM", (20, 10), "cayó muerto"),
    ("TM", (20, 1), "hombre de Benjamín"), ("TM", (20, 22), "cortaron la cabeza á Seba hijo de Bichri"),
    ("TM", (20, 25), "Seba, escriba"), ("TM", (20, 25), "Ira Jaireo fué un jefe principal cerca de David"),
    ("TM", (23, 26), "Hira, hijo de Jecces, de Tecoa"), ("TM", (23, 38), "Ira de Ithri"),
    ("TM", (4, 2), "hijos de Rimmón Beerothita"), ("TM", (23, 29), "Helec hijo de Baana de Netophath"),
    ("TM", (17, 27), "Barzillai Galaadita de Rogelim"), ("TM", (19, 32), "de ochenta años"),
    ("TM", (21, 8), "Barzillai Molathita"), ("TM", (23, 11), "Samma, hijo de Age Araita"),
    ("TM", (23, 25), "Samma de Harodi"), ("TM", (23, 33), "Samma de Arar"), ("TM", (8, 18), "Ceretheos y Peletheos"),
    ("TM", (23, 30), "Benaía Pirathonita"), ("TM", (23, 9), "Eleazar, hijo de Dodo"), ("TM", (23, 8), "era éste Adino el Eznita"),
    ("TM", (21, 19), "Elhanan, hijo de Jaare-oregim de Beth-lehem, hirió á Goliath Getheo"),
    ("TM", (23, 24), "Elhaanan hijo de Dodo de Beth-lehem"), ("TM", (21, 18), "Sibechâi Husathita hirió á Saph"),
    ("TM", (23, 27), "Mebunnai de Husa"), ("TM", (15, 19), "tú eres extranjero"), ("TM", (15, 18), "seiscientos hombres"),
    ("TM", (23, 29), "Ittai hijo de Ribai de Gabaa de los hijos de Benjamín"), ("TM", (15, 32), "Husai Arachîta"),
    ("TM", (15, 37), "Husai amigo de David"), ("TM", (17, 14), "el consejo de Achitophel"), ("TM", (15, 12), "Achitophel Gilonita"),
    ("TM", (17, 23), "ahorcóse"), ("TM", (16, 5), "Semei, hijo de Gera"), ("TM", (24, 18), "la era de Arauna Jebuseo"),
    ("TM", (5, 11), "Hiram rey de Tiro"), ("TM", (3, 7), "una concubina que se llamaba Rispa"),
    ("TM", (21, 11), "Rispa hija de Aja, concubina de Saúl"), ("TM", (21, 10), "Rispa hija de Aja"),
    ("TM", (3, 3), "Absalóm, hijo de Maachâ, hija de Talmai rey de Gessur"), ("TM", (3, 2), "su primogénito fué Ammón"),
    ("TM", (18, 2), "la tercera parte"), ("TM", (13, 3), "Jonadab, hijo de Simea, hermano de David"),
    ("TM", (13, 32), "Jonadab, hijo de Simea hermano de David"), ("TM", (6, 23), "nunca tuvo hijos"),
    ("TM", (21, 8), "cinco hijos de Michâl hija de Saúl, los cuales ella había parido á Adriel"),
    ("LXX", (21, 8), "the five sons of Michol daughter of Saul"),
]
ROLES = {
    "Ish-bosheth_1": ("hijo de Saúl, rey sobre Israel", (2, 10), "De cuarenta años era Is-boseth hijo de Saúl, cuando comenzó á reinar sobre Israel"),
    "Talmai_2": ("rey de Gesur", (3, 3), "Talmai rey de Gessur"),
    "Mephibosheth_1": ("hijo de Jonatán, lisiado de los pies", (4, 4), "tenía un hijo lisiado de los pies"),
    "Hiram_1": ("rey de Tiro", (5, 11), "Hiram rey de Tiro"),
    "Uzzah_1": ("muere junto al arca", (6, 7), "cayó allí muerto junto al arca de Dios"),
    "Obed-edom_1": ("geteo, en cuya casa está el arca tres meses", (6, 11), "en casa de Obed-edom Getheo tres meses"),
    "Nathan_2": ("profeta", (7, 2), "al profeta Nathán"),
    "Toi_1": ("rey de Hamat", (8, 9), "Toi, rey de Hamath"),
    "Hadadezer_1": ("rey de Soba", (8, 3), "Hadad-ezer hijo de Rehob, rey de Soba"),
    "Zadok_1": ("sacerdote", (8, 17), "eran sacerdotes"),
    "Ahimelech_3": ("sacerdote", (8, 17), "eran sacerdotes"),
    "Seraiah_1": ("escriba de David", (8, 17), "Seraía era escriba"),
    "Jehoshaphat_1": ("canciller de David", (8, 16), "Josaphat hijo de Ahilud, canciller"),
    "Benaiah_1": ("sobre los cereteos y peleteos", (8, 18), "Benahía hijo de Joiada, era sobre los Ceretheos y Peletheos"),
    "Ziba_1": ("siervo de la casa de Saúl", (9, 2), "un siervo de la casa de Saúl, que se llamaba Siba"),
    "Hanun_1": ("rey de los amonitas", (10, 1), "reinó en lugar suyo Hanún su hijo"),
    "Shobach_1": ("general del ejército de Hadad-ezer", (10, 16), "Sobach general del ejército de Hadad-ezer"),
    "Uriah_1": ("heteo, marido de Betsabé", (11, 3), "mujer de Uría Hetheo"),
    "Bathsheba_1": ("hija de Eliam, mujer de Urías y después de David", (11, 3), "Bath-sheba hija de Eliam, mujer de Uría Hetheo"),
    "Jonadab_1": ("amigo de Amnón", (13, 3), "Amnón tenía un amigo que se llamaba Jonadab"),
    "Ahithophel_1": ("gilonita, consejero de David", (15, 12), "Achitophel Gilonita, del consejo de David"),
    "Ittai_1": ("geteo, extranjero que sigue a David", (15, 19), "Ittai Getheo"),
    "Hushai_1": ("arquita, amigo de David", (16, 16), "Husai Arachîta amigo de David"),
    "Amasa_1": ("jefe del ejército de Absalón", (17, 25), "Absalom constituyó á Amasa sobre el ejército"),
    "Barzillai_1": ("galaadita de Rogelim", (17, 27), "Barzillai Galaadita de Rogelim"),
    "Chimham_1": ("pasa el Jordán con el rey en lugar de Barzilai", (19, 38), "Pues pase conmigo Chimham"),
    "Sheba_4": ("benjamita que se rebela contra David", (20, 1), "hombre de Benjamín"),
    "Adoram_1": ("sobre los tributos", (20, 24), "Adoram sobre los tributos"),
    "Sheva_1": ("escriba de David", (20, 25), "Seba, escriba"),
    "Ira_1": ("jaireo, jefe principal cerca de David", (20, 25), "Ira Jaireo fué un jefe principal cerca de David"),
    "Ishbi-benob_1": ("de los hijos del gigante", (21, 16), "Isbi-benob, el cual era de los hijos del gigante"),
    "Saph_1": ("de los hijos del gigante", (21, 18), "Saph, que era de los hijos del gigante"),
    "Sibbecai_1": ("husatita, mata a Saf", (21, 18), "Sibechâi Husathita hirió á Saph"),
    "Elhanan_1": ("de Belén; hiere a Goliat geteo", (21, 19), "hirió á Goliath Getheo"),
    "Josheb-basshebeth_1": ("principal de los capitanes de David", (23, 8), "principal de los capitanes"),
    "Eleazar_3": ("uno de los tres valientes", (23, 9), "fué de los tres valientes que estaban con David"),
    "Shammah_3": ("ararita, uno de los tres valientes", (23, 11), "Samma, hijo de Age Araita"),
    "Shammah_4": ("de Harod, de los treinta", (23, 25), "Samma de Harodi"),
    "Elika_1": ("de Harod, de los treinta", (23, 25), "Elica de Harodi"),
    "Helez_1": ("de los treinta", (23, 26), "Heles de Palti"),
    "Ira_2": ("de Tecoa, de los treinta", (23, 26), "Hira, hijo de Jecces, de Tecoa"),
    "Abiezer_1": ("de Anatot, de los treinta", (23, 27), "Abiezer de Anathoth"),
    "Zalmon_1": ("de los treinta", (23, 28), "Selmo de Hahoh"),
    "Maharai_1": ("de Netofa, de los treinta", (23, 28), "Maharai de Netophath"),
    "Heleb_1": ("de Netofa, de los treinta", (23, 29), "Helec hijo de Baana de Netophath"),
    ITAI: ("benjamita de Gabaa, de los treinta", (23, 29), "Ittai hijo de Ribai de Gabaa de los hijos de Benjamín"),
    "Benaiah_2": ("piratonita, de los treinta", (23, 30), "Benaía Pirathonita"),
    "Hiddai_1": ("de los treinta", (23, 30), "Hiddai del arroyo de Gaas"),
    "Abi-albon_1": ("de los treinta", (23, 31), "Abi-albon de Arbath"),
    "Azmaveth_1": ("de los treinta", (23, 31), "Asmaveth de Barhum"),
    "Eliahba_1": ("de Saalbón, de los treinta", (23, 32), "Elihaba de Saalbón"),
    "Jashen_1": ("de cuyos hijos es Jonatán, de los treinta", (23, 32), "Jonathán de los hijos de Jassén"),
    "Jonathan_5": ("de los treinta", (23, 32), "Jonathán de los hijos de Jassén"),
    "Shammah_5": ("de Arar, de los treinta", (23, 33), "Samma de Arar"),
    "Hezro_1": ("del Carmelo, de los treinta", (23, 35), "Hesrai del Carmelo"),
    "Paarai_1": ("de los treinta", (23, 35), "Pharai de Arbi"),
    "Bani_1": ("de los treinta", (23, 36), "Bani de Gadi"),
    "Zelek_1": ("amonita, de los treinta", (23, 37), "Selec de Ammón"),
    "Naharai_1": ("de Beerot, escudero de Joab", (23, 37), "Naharai de Beeroth, escudero de Joab"),
    "Ira_3": ("itrita, de los treinta", (23, 38), "Ira de Ithri"),
    "Gareb_1": ("itrita, de los treinta", (23, 38), "Gareb de Ithri"),
    "Araunah_1": ("jebuseo, dueño de la era", (24, 18), "la era de Arauna Jebuseo"),
}
SIN_NOMBRE = {}
RELACIONES = [
    ("Saul_1", "Ish-bosheth_1", "padre", (2, 8), "Is-boseth hijo de Saúl", "2 S 2:10: «Is-boseth hijo de Saúl»."),
    ("Zeruiah_1", "Joab_1", "madre", (2, 13), "Joab hijo de Sarvia", ""),
    ("Zeruiah_1", "Asahel_1", "madre", (2, 18), "los tres hijos de Sarvia: Joab, y Abisai, y Asael", ""),
    ("David_1", "Amnon_1", "padre", (3, 2), "nacieron hijos á David en Hebrón: su primogénito fué Ammón",
     "La RV1909 escribe «Ammón» en 2 S 3:2 y «Amnón» desde 13:1 («Amnón hijo de David»)."),
    ("Ahinoam_2", "Amnon_1", "madre", (3, 2), "de Ahinoam Jezreelita", ""),
    ("David_1", "Chileab_1", "padre", (3, 3), "Su segundo Chileab", "2 S 3:2-5: hijos que «nacieron á David en Hebrón»."),
    ("Abigail_1", "Chileab_1", "madre", (3, 3), "de Abigail la mujer de Nabal", ""),
    ("David_1", "Absalom_1", "padre", (3, 3), "el tercero, Absalóm", "2 S 13:1: «Absalom hijo de David»."),
    ("Maacah_2", "Absalom_1", "madre", (3, 3), "Absalóm, hijo de Maachâ", ""),
    ("Talmai_2", "Maacah_2", "padre", (3, 3), "Maachâ, hija de Talmai rey de Gessur", ""),
    ("David_1", "Adonijah_1", "padre", (3, 4), "El cuarto, Adonías", "2 S 3:2-5: hijos que «nacieron á David en Hebrón»."),
    ("Haggith_1", "Adonijah_1", "madre", (3, 4), "Adonías hijo de Haggith", ""),
    ("David_1", "Shephatiah_1", "padre", (3, 4), "el quinto, Saphatías", "2 S 3:2-5: hijos que «nacieron á David en Hebrón»."),
    ("Abital_1", "Shephatiah_1", "madre", (3, 4), "Saphatías hijo de Abital", ""),
    ("David_1", "Ithream_1", "padre", (3, 5), "El sexto, Jetream", "2 S 3:5: «Estos nacieron á David en Hebrón»."),
    ("Eglah_1", "Ithream_1", "madre", (3, 5), "Jetream, de Egla mujer de David", ""),
    ("David_1", "Eglah_1", "conyuge", (3, 5), "Egla mujer de David", ""),
    ("Saul_1", "Rizpah_1", "conyuge", (3, 7), "había Saúl tenido una concubina que se llamaba Rispa",
     "El texto la llama «concubina» (2 S 3:7; 21:11)."),
    ("Aiah_2", "Rizpah_1", "padre", (3, 7), "Rispa, hija de Aja", ""),
    ("Rimmon_1", "Baanah_1", "padre", (4, 2), "hijos de Rimmón Beerothita", ""),
    ("Rimmon_1", "Rechab_1", "padre", (4, 2), "hijos de Rimmón Beerothita", ""),
    ("Jonathan_2", "Mephibosheth_1", "padre", (4, 4), "Jonathán, hijo de Saúl, tenía un hijo lisiado de los pies",
     "2 S 9:6: «Mephi-boseth, hijo de Jonathán hijo de Saúl»."),
    ("David_1", "Japhia_2", "padre", (5, 16), "Y Japhia",
     "2 S 5:14-16: «los nombres de los que le nacieron en Jerusalem» (5:14). La RV1909 pone a Jafía al comienzo de 5:16; "
     "BibleData (numeración inglesa), en 5:15."),
    ("Abinadab_1", "Uzzah_1", "padre", (6, 3), "Uzza y Ahio, hijos de Abinadab", ""),
    ("Abinadab_1", "Ahio_1", "padre", (6, 3), "Uzza y Ahio, hijos de Abinadab", ""),
    ("Rehob_1", "Hadadezer_1", "padre", (8, 3), "Hadad-ezer hijo de Rehob", ""),
    ("Toi_1", "Joram_1", "padre", (8, 10), "Envió Toi á Joram su hijo", ""),
    ("Ahilud_1", "Jehoshaphat_1", "padre", (8, 16), "Josaphat hijo de Ahilud", "2 S 20:24: «Josaphat hijo de Ahillud»."),
    ("Ahitub_2", "Zadok_1", "padre", (8, 17), "Sadoc hijo de Ahitud",
     "La RV1909 de eBible escribe «Ahitud»; Brenton (LXX): «Sadoc the son of Achitob»."),
    ("Abiathar_1", "Ahimelech_3", "padre", (8, 17), "Ahimelech hijo de Abiathar",
     "En 1 S 22:20 Abiatar es hijo de Ahimelec (otra persona, Ahimelech_1): el texto dice las dos cosas; no se armoniza."),
    ("Jehoiada_1", "Benaiah_1", "padre", (8, 18), "Benahía hijo de Joiada", "2 S 20:23 y 23:20: «Benaía hijo de Joiada»."),
    ("Ammiel_2", "Machir_2", "padre", (9, 4), "Machîr hijo de Amiel", ""),
    ("Mephibosheth_1", "Mica_1", "padre", (9, 12), "tenía Mephi-boseth un hijo pequeño, que se llamaba Michâ", ""),
    ("Nahash_1", "Hanun_1", "padre", (10, 2), "Hanún hijo de Naas", ""),
    ("Eliam_1", "Bathsheba_1", "padre", (11, 3), "Bath-sheba hija de Eliam", ""),
    ("Uriah_1", "Bathsheba_1", "conyuge", (11, 3), "mujer de Uría Hetheo", ""),
    ("David_1", "Bathsheba_1", "conyuge", (11, 27), "fué ella su mujer", "2 S 12:24: «Bath-sheba su mujer»."),
    ("David_1", "Solomon_1", "padre", (12, 24), "llamó su nombre Salomón",
     "2 S 12:24: «consoló David á Bath-sheba su mujer… y parió un hijo»; 5:14: entre «los que le nacieron en Jerusalem»."),
    ("Bathsheba_1", "Solomon_1", "madre", (12, 24), "parió un hijo, y llamó su nombre Salomón", ""),
    ("Shammah_2", "Jonadab_1", "padre", (13, 3), "Jonadab, hijo de Simea, hermano de David", ""),
    ("Ammihud_4", "Talmai_2", "padre", (13, 37), "Talmai hijo de Amiud", ""),
    ("Absalom_1", "Tamar_3", "padre", (14, 27), "Naciéronle á Absalom tres hijos, y una hija que se llamó Thamar", ""),
    ("Zadok_1", "Ahimaaz_2", "padre", (15, 27), "tu hijo Ahimaas", "2 S 18:19: «Ahimaas hijo de Sadoc»."),
    ("Abiathar_1", "Jonathan_3", "padre", (15, 27), "Jonathán hijo de Abiathar", ""),
    ("Gera_3", "Shimei_2", "padre", (16, 5), "Semei, hijo de Gera", ""),
    ("Ithra_1", "Amasa_1", "padre", (17, 25), "Amasa fué hijo de un varón de Israel llamado Itra", ""),
    ("Ithra_1", "Abigail_2", "conyuge", (17, 25), "el cual había entrado á Abigail",
     "El texto dice que Itra «había entrado á» Abigail; no la llama su mujer."),
    ("Nahash_1", "Shobi_1", "padre", (17, 27), "Sobi hijo de Naas de Rabba de los hijos de Ammon", ""),
    ("Bichri_1", "Sheba_4", "padre", (20, 1), "Seba, hijo de Bichri", ""),
    ("Saul_1", "Armoni_1", "padre", (21, 8), "los cuales ella había parido á Saúl", ""),
    ("Rizpah_1", "Armoni_1", "madre", (21, 8), "dos hijos de Rispa hija de Aja", ""),
    ("Saul_1", "Mephibosheth_2", "padre", (21, 8), "los cuales ella había parido á Saúl", ""),
    ("Rizpah_1", "Mephibosheth_2", "madre", (21, 8), "dos hijos de Rispa hija de Aja", ""),
    ("Barzillai_2", "Adriel_1", "padre", (21, 8), "Adriel, hijo de Barzillai Molathita", ""),
    ("Jaare-oregim_1", "Elhanan_1", "padre", (21, 19), "Elhanan, hijo de Jaare-oregim",
     "2 S 23:24: «Elhaanan hijo de Dodo» (BibleData: Dodo = Jaare-oregim)."),
    ("Shammah_2", "Jonathan_4", "padre", (21, 21), "Jonathán, hijo de Sima hermano de David", ""),
    ("Dodo_2", "Eleazar_3", "padre", (23, 9), "Eleazar, hijo de Dodo", ""),
    ("Agee_1", "Shammah_3", "padre", (23, 11), "Samma, hijo de Age", ""),
    ("Ikkesh_1", "Ira_2", "padre", (23, 26), "Hira, hijo de Jecces", ""),
    ("Baanah_2", "Heleb_1", "padre", (23, 29), "Helec hijo de Baana", ""),
    ("Ribai_1", ITAI, "padre", (23, 29), "Ittai hijo de Ribai", ""),
    ("Sharar_1", "Ahiam_1", "padre", (23, 33), "Ahiam hijo de Sarar", ""),
    ("Ahasbai_1", "Eliphelet_2", "padre", (23, 34), "Elipheleth hijo de Asbai", ""),
    ("Ahithophel_1", "Eliam_2", "padre", (23, 34), "Eliam hijo de Achîtophel", ""),
    ("Nathan_3", "Igal_2", "padre", (23, 36), "Igheal hijo de Nathán", ""),
]
NOTAS_REL = {
    ("David_1", "Tamar_2", "padre"): ("2 S 13:1: «Absalom hijo de David una hermana hermosa que se llamaba Thamar»; 13:18: "
                                      "lleva el traje que «las hijas vírgenes de los reyes» vestían. El texto no dice "
                                      "«hija de David»: relación inferida, como en BibleData."),
}
# Relaciones de los libros anteriores que 2 Samuel repite: se añade la referencia a la nota.
REPITE_GN = [
    ("Jesse_1", "David_1", "padre", (23, 1), "Dijo David hijo de Isaí"),
    ("Saul_1", "Jonathan_2", "padre", (1, 4), "Saúl y Jonathán su hijo"),
    ("Saul_1", "Michal_1", "padre", (6, 23), "Michâl hija de Saúl"),
    ("Ner_1", "Abner_1", "padre", (2, 8), "Abner hijo de Ner"),
    ("Zeruiah_1", "Abishai_1", "madre", (2, 18), "los tres hijos de Sarvia: Joab, y Abisai, y Asael"),
    ("Kish_1", "Saul_1", "padre", (21, 14), "el sepulcro de Cis su padre"),
    ("Michal_1", "Palti_2", "conyuge", (3, 15), "quitóla á su marido Paltiel"),
    ("Laish_1", "Palti_2", "padre", (3, 15), "Paltiel, hijo de Lais"),
    ("Adriel_1", "Merab_1", "conyuge", (21, 8), "los cuales ella había parido á Adriel"),
    ("Gideon_1", "Abimelech_2", "padre", (11, 21), "Abimelech hijo de Jerobaal"),
]
# Edades escritas (TM de la RV1909 y LXX de Brenton): índice de la cifra en cada texto (en 4:4 la RV1909 dice antes
# «un hijo»).
EDADES = [
    ("Ish-bosheth_1", "en_evento", (2, 10), 0, 0, "cuando comienza a reinar sobre Israel (2 S 2:10)"),
    ("Mephibosheth_1", "en_evento", (4, 4), 1, 0, "cuando llega de Jezreel la noticia de Saúl y Jonatán y queda cojo (2 S 4:4)"),
    ("David_1", "en_evento", (5, 4), 0, 0, "cuando comienza a reinar (2 S 5:4)"),
    ("Barzillai_1", "en_evento", (19, 32), 0, 0, "cuando acompaña al rey al Jordán (2 S 19:31-32)"),
]
_GEDEON = ("2 S 11:21: «¿Quién hirió á Abimelech hijo de Jerobaal? ¿no echó una mujer del muro un pedazo de una rueda de "
           "molino, y murió en Thebes?», la muerte de Jue 9:50-53. BibleData usa ahí otros ids (Jerubbesheth_1 y "
           "Abimelech_3); aquí son Gedeón (Jerobaal, Jue 6:32; 1 S 12:11) y su hijo Abimelec, por lo que cuenta el texto.")
NOTAS_EXISTENTES = {
    "Gideon_1": _GEDEON,
    "Abimelech_2": _GEDEON,
    "Goliath_1": ("2 S 21:19: «Elhanan, hijo de Jaare-oregim de Beth-lehem, hirió á Goliath Getheo, el asta de cuya lanza "
                  "era como un enjullo de telar». BibleData asigna ese versículo a este mismo Goliat (Goliath_1), al que "
                  "1 S 17:50-51 da por muerto a manos de David. Se deja como en la fuente, sin unir ni separar ni "
                  "armonizar."),
    "Merab_1": ("2 S 21:8: la RV1909 (y Brenton) dicen «Michâl»; BibleData asigna el versículo a Merab, mujer de Adriel "
                "(identidad inferida)."),
    "Michal_1": "2 S 3:13-16: David la reclama y Is-boset se la quita a Paltiel; 2 S 6:23: «nunca tuvo hijos hasta el día de su muerte».",
    "Shammah_2": ("2 S 13:3 y 21:21: «Simea» / «Sima», «hermano de David», padre de Jonadab y de Jonatán; BibleData lo "
                  "identifica con Samma (identidad inferida)."),
    "Jonathan_2": "2 S 1:17-27: David lo llora con Saúl; 2 S 4:4 y 9:6: padre de Mefi-boset; 2 S 21:12-14: sus huesos se entierran en Sela.",
    "David_1": ("2 S 2:4: ungido rey de Judá en Hebrón; 2 S 5:3-5: rey de todo Israel, «de treinta años», siete años y "
                "seis meses en Hebrón y treinta y tres en Jerusalén."),
    "Palti_2": "2 S 3:15-16: la RV1909 lo llama «Paltiel, hijo de Lais»; sigue llorando a Mical hasta Bahurim.",
}
NOTAS_VERIFICAR += [("TM", (11, 21), "Abimelech hijo de Jerobaal"), ("TM", (11, 21), "murió en Thebes"),
                    ("TM", (6, 23), "nunca tuvo hijos hasta el día de su muerte"), ("TM", (3, 15), "Paltiel, hijo de Lais"),
                    ("TM", (2, 4), "ungieron allí á David por rey sobre la casa de Judá"),
                    ("TM", (5, 4), "Era David de treinta años"), ("TM", (5, 5), "siete años y seis meses"),
                    ("TM", (21, 14), "sepultaron los huesos de Saúl y los de su hijo Jonathán"),
                    ("TM", (12, 24), "Bath-sheba su mujer"), ("TM", (13, 18), "las hijas vírgenes de los reyes"),
                    ("TM", (14, 33), "el rey besó á Absalom")]
# Refs que el texto da a una persona y BibleData no sitúa.
REFS_EXTRA = {"Gideon_1": [(11, 21)], "Abimelech_2": [(11, 21)], "Jesse_1": [(20, 1)], ITAI: [(23, 29)]}
REFS_QUITAR = {}

S1 = "David llora a Saúl (2 S 1)"
S2 = "David rey en Hebrón; guerra con la casa de Saúl (2 S 2–4)"
S3 = "Jerusalén y el arca (2 S 5–6)"
S4 = "La promesa a David y sus victorias (2 S 7–10)"
S5 = "Betsabé y Natán (2 S 11–12)"
S6 = "Amnón, Tamar y Absalón (2 S 13–14)"
S7 = "La rebelión de Absalón (2 S 15–19)"
S8 = "Seba (2 S 20)"
S9 = "Apéndices (2 S 21–24)"
PASAJES = [
    ("1:1", "1:16", "La noticia de Gilboa", "En Siclag un amalecita trae a David la corona de Saúl y dice que él lo mató; David manda matarlo por haber alzado la mano contra el ungido de Jehová.", S1),
    ("1:17", "1:27", "El lamento por Saúl y Jonatán", "David endecha a Saúl y a Jonatán su hijo: «¡Cómo han caído los valientes!»", S1),
    ("2:1", "2:11", "David rey en Hebrón; Is-boset rey de Israel", "Los de Judá ungen a David en Hebrón; Abner hace rey a Is-boset, hijo de Saúl, sobre el resto de Israel.", S2),
    ("2:12", "2:32", "Gabaón: muere Asael", "Junto al estanque de Gabaón luchan los de Abner y los de Joab; Asael persigue a Abner y Abner lo mata con el regatón de la lanza.", S2),
    ("3:1", "3:21", "Abner se pasa a David", "Nacen a David hijos en Hebrón; Abner rompe con Is-boset por la concubina de Saúl, devuelve a Mical a David y promete traerle todo Israel.", S2),
    ("3:22", "3:39", "Joab mata a Abner", "Joab hace volver a Abner y lo mata en la puerta de Hebrón por la muerte de Asael; David lo llora y hace caer la culpa sobre Joab.", S2),
    ("4:1", "4:12", "Muerte de Is-boset", "Recab y Baana matan a Is-boset en su cama y llevan su cabeza a David, que los manda matar; Mefi-boset, hijo de Jonatán, había quedado cojo.", S2),
    ("5:1", "5:16", "David rey de todo Israel; Jerusalén", "Las tribus ungen a David en Hebrón; toma la fortaleza de Sion y la llama Ciudad de David; Hiram le envía cedro y le nacen hijos en Jerusalén.", S3),
    ("5:17", "5:25", "Victorias sobre los filisteos", "David consulta a Jehová y vence a los filisteos en Baal-perasim y en el valle de Refaim.", S3),
    ("6:1", "6:11", "El arca y Uza", "David lleva el arca en un carro nuevo; Uza la sostiene y muere; el arca queda tres meses en casa de Obed-edom.", S3),
    ("6:12", "6:23", "El arca en la Ciudad de David; Mical", "David sube el arca saltando con toda su fuerza delante de Jehová; Mical lo menosprecia y nunca tiene hijos.", S3),
    ("7:1", "7:17", "La promesa de Natán", "David quiere edificar casa para el arca; por Natán, Jehová le promete que su descendiente edificará casa a su nombre y que su trono será estable para siempre.", S4),
    ("7:18", "7:29", "La oración de David", "David agradece la promesa delante de Jehová y le pide que bendiga su casa para siempre.", S4),
    ("8:1", "8:18", "Las victorias de David", "David vence a filisteos y moabitas, a Hadad-ezer de Soba, a los sirios y a Edom; lista de sus oficiales.", S4),
    ("9:1", "9:13", "Mefi-boset a la mesa del rey", "Por amor de Jonatán, David devuelve a Mefi-boset las tierras de Saúl y lo hace comer siempre a su mesa; Siba labrará sus tierras.", S4),
    ("10:1", "10:19", "Guerra con Ammón y Siria", "Hanún afrenta a los enviados de David; Joab y Abisai vencen a amonitas y sirios, y David vence a Sobac en Helam.", S4),
    ("11:1", "11:13", "David y Betsabé", "Mientras Joab sitia Rabá, David toma a Betsabé, mujer de Urías; ella concibe, y David hace venir a Urías, que no baja a su casa.", S5),
    ("11:14", "11:27", "Muerte de Urías", "David escribe a Joab que ponga a Urías donde la batalla es más recia; Urías muere y David toma a Betsabé por mujer.", S5),
    ("12:1", "12:14", "«Tú eres aquel hombre»", "Natán cuenta la parábola de la cordera del pobre; David reconoce su pecado y Natán anuncia que el niño morirá.", S5),
    ("12:15", "12:31", "Muere el niño; nace Salomón; Rabá tomada", "David ayuna por el niño enfermo, que muere al séptimo día; Betsabé da a luz a Salomón y David toma Rabá de los amonitas.", S5),
    ("13:1", "13:22", "Amnón y Tamar", "Amnón, fingiéndose enfermo, fuerza a su hermana Tamar y luego la echa; Absalón la recoge en su casa y aborrece a Amnón.", S6),
    ("13:23", "13:39", "Absalón mata a Amnón", "Dos años después, en el esquileo de Bala-hasor, los criados de Absalón matan a Amnón; Absalón huye a Gesur y está allí tres años.", S6),
    ("14:1", "14:24", "La mujer de Tecoa", "Joab envía al rey una mujer de Tecoa con una historia; David deja volver a Absalón a Jerusalén, pero sin ver su rostro.", S6),
    ("14:25", "14:33", "Absalón ve al rey", "Absalón, el más hermoso de Israel, pasa dos años sin ver al rey; hace quemar las cebadas de Joab, y al fin el rey lo besa.", S6),
    ("15:1", "15:12", "Absalón se gana a Israel", "Absalón se gana a los que vienen a juicio; en Hebrón se hace proclamar rey y Ahitofel se le une.", S7),
    ("15:13", "15:37", "David huye de Jerusalén", "David sale de la ciudad; Itai geteo va con él; Sadoc y Abiatar vuelven el arca, y Husai vuelve para frustrar el consejo de Ahitofel.", S7),
    ("16:1", "16:14", "Siba y Semei", "Siba trae provisiones y acusa a Mefi-boset; en Bahurim Semei maldice a David y le tira piedras, y David no deja que Abisai lo mate.", S7),
    ("16:15", "17:14", "Ahitofel y Husai", "Absalón entra a las concubinas de su padre; Husai desbarata el consejo de Ahitofel de perseguir enseguida a David.", S7),
    ("17:15", "17:29", "Aviso a David; Mahanaim", "Jonatán y Ahimaas, escondidos en un pozo, avisan a David, que pasa el Jordán; Ahitofel se ahorca; en Mahanaim, Sobi, Maquir y Barzilai abastecen al rey.", S7),
    ("18:1", "18:18", "La batalla del bosque de Efraín", "David pide que traten bien a Absalón; en el bosque de Efraín Absalón queda colgado de un alcornoque y Joab le clava tres dardos.", S7),
    ("18:19", "19:8", "«Hijo mío Absalom»", "Ahimaas y Cusi llevan la noticia; David llora a su hijo, y Joab le reprocha que avergüence a los que lo salvaron.", S7),
    ("19:9", "19:23", "El regreso del rey", "Judá llama al rey de vuelta; David promete a Amasa el mando en lugar de Joab y perdona a Semei en el Jordán.", S7),
    ("19:24", "19:43", "Mefi-boset, Barzilai y la disputa por el rey", "Mefi-boset sale a recibir al rey; Barzilai, de ochenta años, se despide y deja a Quimam; Israel y Judá discuten por el rey.", S7),
    ("20:1", "20:13", "Seba se rebela; Joab mata a Amasa", "Seba, hijo de Bicri, aparta a Israel de David; junto a la peña de Gabaón Joab mata a Amasa con su daga.", S8),
    ("20:14", "20:26", "Abel de Bet-maaca; los oficiales de David", "Joab cerca a Seba en Abel de Bet-maaca; una mujer sabia hace que le corten la cabeza y se la echen desde el muro. Lista de los oficiales de David.", S8),
    ("21:1", "21:14", "Los gabaonitas y Rizpa", "Tras tres años de hambre, David entrega a los gabaonitas siete descendientes de Saúl, que los ahorcan; Rizpa vela sus cuerpos y David sepulta los huesos de Saúl y de Jonatán.", S9),
    ("21:15", "21:22", "Guerras con los filisteos", "Abisai salva a David de Isbi-benob; en Gob y en Gat caen otros hijos del gigante, y Elhanán hiere a Goliat geteo.", S9),
    ("22:1", "22:25", "El cántico de David (1)", "David canta a Jehová, su roca y su libertador, que lo libró de todos sus enemigos y de la mano de Saúl.", S9),
    ("22:26", "22:51", "El cántico de David (2)", "Dios es perfecto en su camino: da a David la victoria y hace misericordia a su ungido.", S9),
    ("23:1", "23:17", "Las postreras palabras de David; los tres valientes", "Últimas palabras de David; Adino, Eleazar y Sama, y los tres que le traen agua de la cisterna de Belén.", S9),
    ("23:18", "23:39", "Abisai, Benaía y los treinta", "Hazañas de Abisai y de Benaía, hijo de Joiada; lista de los valientes de David hasta Urías heteo: «Entre todos treinta y siete».", S9),
    ("24:1", "24:14", "El censo", "David manda contar a Israel y a Judá; Joab vuelve a los nueve meses y veinte días; David reconoce su pecado y Gad le da a elegir el castigo.", S9),
    ("24:15", "24:25", "La peste y la era de Arauna", "Mueren setenta mil por la peste; el ángel se detiene junto a la era de Arauna jebuseo, y David la compra y edifica allí un altar.", S9),
]
# Citas de los resúmenes que van entre comillas (se comprueban).
CITAS_RESUMEN = [((1, 19), "¡Cómo han caído los valientes!"), ((12, 7), "Tú eres aquel hombre"),
                 ((18, 33), "Hijo mío Absalom"), ((23, 39), "Entre todos treinta y siete")]

# ---------------------------------------------------------------- lugares
# Lugares configurados a mano: obid -> (id, nombre, formas RV1909, tipo, nota, forzar baja).
LUGARES_MANUAL = {
    "af20c46": ("sion", "Sion (fortaleza de Sion)", ["Sión"], "ciudad",
                "2 S 5:7: «David tomó la fortaleza de Sión, la cual es la ciudad de David». OpenBible la registra aparte "
                "de Jerusalén, con la misma identificación (Jerusalén). Distinta de «Sión» del Hermón (Dt 4:48).", False),
    "a84f426": ("ciudad-de-david", "Ciudad de David", ["ciudad de David"], "ciudad",
                "2 S 5:7, 9: nombre que David da a la fortaleza de Sion. OpenBible la registra aparte de Jerusalén.", False),
    "aa24ad4": ("bosque-de-efrain", "Bosque de Efraín", ["Ephraim"], "region",
                "2 S 18:6: «el bosque de Ephraim», donde muere Absalón (2 S 18:9-17). OpenBible lo sitúa en Galaad, al "
                "este del Jordán (David está en Mahanaim, 2 S 17:24).", False),
    "a7559e6": ("valle-de-refaim", "Valle de Refaim", ["Raphaim"], "otro", "2 S 5:18, 22; 23:13: «el valle de Raphaim».", False),
    "af936bd": ("valle-de-la-sal", "Valle de la Sal", ["sal"], "otro", "2 S 8:13: «el valle de la sal».", False),
    "a553110": ("torrente-de-cedron", "Torrente de Cedrón", ["Cedrón"], "rio", "2 S 15:23: «el torrente de Cedrón».", False),
    "ac2c4c5": ("monte-de-los-olivos", "Monte de los Olivos", ["cuesta de las olivas"], "monte",
                "La RV1909 dice «la cuesta de las olivas» (2 S 15:30); OpenBible lo identifica con el monte de los Olivos. "
                "En 15:32 y 16:1 la RV1909 dice solo «la cumbre [del monte]».", False),
    "abffcaa": ("abel-bet-maaca", "Abel-bet-maaca", ["Abel de Beth-maachâ", "Abel"], "ciudad",
                "2 S 20:14-15: «Abel y Beth-maachâ», «Abel de Beth-maachâ»; allí muere Seba (2 S 20:22).", False),
}
PRECEDIDO = {"af20c46": "fortaleza de ", "aa24ad4": "bosque de ", "a7559e6": "valle de ", "af936bd": "valle de la ",
             "a553110": "torrente de ", "ac2c4c5": "la "}
EXCLUIR_LUGAR = {
    "a1cb244": "Néguev (24:7): la RV1909 traduce «al mediodía de Judá»; no es nombre propio.",
    "ac71e65": "Filistea (8:12): la RV1909 dice «los Filisteos» (gentilicio).",
    "ab45bd3": ("Etiopía (18:21-32): la RV1909 escribe «Cusi», nombre del mensajero; OpenBible lo toma por «el etíope» "
                "(Cus). No se marca como lugar."),
}
UNIR_LUGAR_MANUAL = {}
FORMAS_UNIR = {}
UNIR_LUGAR = {}
NOMBRE_LUGAR = {"Beer-seba": "Beerseba", "Beth-lehem": "Belén", "Jerusalem": "Jerusalén", "Bahurim": "Bahurim",
                "Lodebar": "Lodebar", "Rogelim": "Rogelim", "Baal-perasim": "Baal-perazim", "Pérez-uzza": "Pérez-uza",
                "Methegamma": "Meteg-ama", "Millo": "Milo", "Tecoa": "Tecoa", "Netophath": "Netofa",
                "Bala-hasor": "Baal-hazor", "Gittaim": "Gitaim", "Helcath-assurim": "Helcat-hazurim", "Amma": "Amá",
                "Gía": "Gía", "Saalbón": "Saalbón", "Harodi": "Harod", "Husa": "Husa", "Sira": "Sira", "Gob": "Gob",
                "Helam": "Helam", "Pirathón": "Piratón"}
NOMBRE_OB = {"a2bb5ef": ("Arbat", "2 S 23:31: «Abi-albon de Arbath». OpenBible lo asigna al Arabá (la llanura del Jordán, "
                                 "«Arabah»), donde la RV1909 dice «la campiña» (2 S 2:29; 4:7)."),
             "a507da9": ("Efraín (junto a Baal-hazor)", "2 S 13:23: «Bala-hasor, que está junto á Ephraim»; OpenBible la "
                         "registra como lugar propio, distinto del territorio de Efraín.")}
OBLIGATORIOS_LUGAR = ["hebron", "jerusalen", "sion", "ciudad-de-david", "mahanaim", "gesur", "raba-amon",
                      "bosque-de-efrain", "gabaon", "siclag", "valle-de-refaim", "abel-bet-maaca"]
LUGARES = {}
LUGAR_OPCIONAL = set()
EXCL_AUTO = {}
INFO_AUTO = {}
moderno = josue.moderno
# «la ciudad de David»: el nombre de David forma parte del nombre del lugar (se quita la mención de persona para que se
# marque el lugar, como Siquem en Jos 24:32). Se rellena con los versículos de OpenBible (se comprueba uno por versículo).
LUGAR_NO_PERSONA = [((5, 7), "David_1", "iudad de "), ((5, 9), "David_1", "iudad de "), ((6, 10), "David_1", "iudad de "),
                    ((6, 12), "David_1", "iudad de "), ((6, 16), "David_1", "iudad de ")]
INFO_VERSIFICACION = {}


def comprobar_versificacion(rv, br, errores):
    """Recuentos, extremos, versículos sin LXX, desfase por capítulo, nombres paralelos y longitudes."""
    for c, n in enumerate(POR_CAPITULO, 1):
        hay = sum(1 for (cc, _) in rv if cc == c)
        if hay != n:
            errores.append(f"2 Samuel {c}: la RV1909 tiene {hay} versículos (numeración inglesa: {n})")
    vacios = sorted(k for k, t in rv.items() if not t.strip())
    if vacios != sorted(VACIOS):
        errores.append(f"2 Samuel: versículos vacíos {vacios} (se esperaban {sorted(VACIOS)})")
    for ref, ini in VERSIFICACION:
        if not rv.get(ref, "").startswith(ini):
            errores.append(f"Versificación de 2 S {ref[0]}:{ref[1]}: la RV1909 no empieza «{ini}»")
    for ref, fin in FIN_VERSICULO:
        if not rv.get(ref, "").endswith(fin):
            errores.append(f"Versificación de 2 S {ref[0]}:{ref[1]}: la RV1909 no termina «{fin}»")
    for ref, frag in VERSIFICACION_LXX:
        if frag not in br.get(ref, ""):
            errores.append(f"Brenton 2 S {ref[0]}:{ref[1]} (numeración RV) no dice «{frag}»")
    falta = {k for k in rv if k not in br}
    if falta != SIN_LXX or [k for k in br if k not in rv]:
        errores.append(f"2 Samuel: versículos sin Brenton {sorted(falta ^ SIN_LXX)} o de más {[k for k in br if k not in rv]}")
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
            errores.append(f"Versificación de 2 S {c}: el emparejamiento con desfase compara mejor que sin él {costes[c]}")
    INFO_VERSIFICACION["desfase"] = {c: tuple(round(x, 2) for x in v) for c, v in costes.items()}
    comunes = {k for k in rv if k in br and rv[k]}
    for es, en in PARALELOS:
        a = {k for k in comunes if re.search(r"(?<!\w)%s(?!\w)" % re.escape(es), rv[k])}
        b = {k for k in comunes if re.search(r"(?<!\w)%s" % re.escape(en), br[k])}
        if a != b or not a:
            errores.append(f"Versificación de 2 S: «{es}» (RV1909) y «{en}» (Brenton) no caen en los mismos versículos: "
                           f"solo RV {sorted(a - b)}, solo LXX {sorted(b - a)}")
    for k in sorted(comunes):
        r = len(rv[k]) / len(br[k])
        if not PROPORCION[0] <= r <= PROPORCION[1]:
            errores.append(f"Versificación de 2 S {k[0]}:{k[1]}: longitud RV1909/Brenton fuera de rango ({r:.2f})")
    INFO_VERSIFICACION["comunes"] = len(comunes)


def construir(cx):
    rv, br, errores = cx["rv"], cx["br"], cx["errores"]
    comprobar_versificacion(rv, br, errores)
    for ref, frag in CITAS_RESUMEN:
        if frag not in rv.get(ref, ""):
            errores.append(f"Resumen de pasaje: «{frag}» no está en 2 S {ref[0]}:{ref[1]}")
    res = exodo.construir(cx, sys.modules[__name__])
    for c in res["capitulos"]:
        for v in c["versiculos"]:
            if (c["cap"], v["n"]) in VACIOS and not v["texto"]:
                v["nota"] = NOTA_VACIO
    for p in res["nuevas"]:
        if p["id"] == ITAI:
            p["sexo"] = "m"  # id propio (no está en BibleData-Person): «hijo de Ribai» (23:29)
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
    return exodo.construir_lugares(rv, menciones_personas, rutas, lugares_previos, errores, avisos, sa,
                                   sys.modules[__name__])


# ---------------------------------------------------------------- hechos obligatorios (sobre los datos finales)
def comprobar(datos, errores):
    """Comprueba los hechos pedidos para 2 Samuel (falla si falta alguno). Devuelve líneas de informe."""
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
            errores.append(f"Hecho obligatorio (2 Samuel): {desc}")

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

    ok_(len(caps) == CAPITULOS and len(texto) == VERSICULOS and [len(c["versiculos"]) for c in caps] == POR_CAPITULO,
        f"{CAPITULOS} capítulos y {VERSICULOS} versículos (hay {len(caps)} y {len(texto)})")
    vacios = [r for r, t in texto.items() if not t]
    v_nota = [v for c in caps for v in c["versiculos"] if not v["texto"]]
    ok_(vacios == ["2S 20:26"] and all("2S 20:25" in v.get("nota", "") for v in v_nota)
        and texto["2S 20:25"].endswith("cerca de David.") and texto["2S 19:1"].startswith("Y DIERON aviso á Joab"),
        f"solo 2S 20:26 vacío, con nota que remite a 20:25; 18:33/19:1 en numeración inglesa ({vacios})")
    ok_(tiene("Ish-bosheth_1", "2S 2:8") and rel("Saul_1", "Ish-bosheth_1", "padre", "2S 2:8"), "Is-boset, hijo de Saúl (2:8)")
    ok_(tiene("Absalom_1", "2S 3:3") and rel("David_1", "Absalom_1", "padre", "2S 3:3")
        and rel("Maacah_2", "Absalom_1", "madre", "2S 3:3") and rel("Talmai_2", "Maacah_2", "padre", "2S 3:3")
        and rol("Talmai_2", "rey de Gesur") and tiene("Talmai_2", "2S 3:3"),
        "Absalón, hijo de David y de Maaca hija de Talmai, rey de Gesur (3:3)")
    ok_(tiene("Mephibosheth_1", "2S 4:4") and tiene("Mephibosheth_1", "2S 9:6")
        and rel("Jonathan_2", "Mephibosheth_1", "padre", "2S 4:4") and rol("Mephibosheth_1", "lisiado de los pies")
        and "1S 14:1" in P["Jonathan_2"]["refs"] and tiene("Jonathan_2", "2S 4:4") and tiene("Jonathan_2", "2S 9:6")
        and sin_libro("Mephibosheth_2", "2S 4") and sin_libro("Mephibosheth_2", "2S 9"),
        "Mefi-boset, hijo de Jonatán (el de 1 S), lisiado de los pies (4:4; 9:6); ≠ el hijo de Rizpa (21:8)")
    ok_(tiene("Hiram_1", "2S 5:11") and rol("Hiram_1", "rey de Tiro"), "Hiram, rey de Tiro (5:11)")
    ok_(tiene("Uzzah_1", "2S 6:6") and tiene("Uzzah_1", "2S 6:7") and rol("Uzzah_1", "junto al arca"),
        "Uza, muerto junto al arca (6:6-7)")
    ok_(tiene("Nathan_2", "2S 7:2") and tiene("Nathan_2", "2S 12:1") and rol("Nathan_2", "profeta")
        and sin_libro("Nathan_1", "2S 7") and sin_libro("Nathan_2", "2S 5:"), "Natán, profeta (7:2; 12:1), ≠ Natán hijo de David (5:14)")
    ok_(tiene("Bathsheba_1", "2S 11:3") and rel("Eliam_1", "Bathsheba_1", "padre", "2S 11:3")
        and rel("Uriah_1", "Bathsheba_1", "conyuge", "2S 11:3") and rol("Uriah_1", "heteo"),
        "Betsabé, hija de Eliam y mujer de Urías heteo (11:3)")
    ok_(tiene("Solomon_1", "2S 12:24") and rel("David_1", "Solomon_1", "padre", "2S 12:24")
        and rel("Bathsheba_1", "Solomon_1", "madre", "2S 12:24") and rel("David_1", "Bathsheba_1", "conyuge", "2S 11:27"),
        "Salomón, hijo de David y Betsabé (12:24)")
    ok_(tiene("Tamar_2", "2S 13:1") and tiene("Amnon_1", "2S 13:1") and rel("David_1", "Amnon_1", "padre", "2S 3:2")
        and rel("David_1", "Tamar_2", "padre", "2S 13:1", "inferido") and "Absalom hijo de David" in texto["2S 13:1"]
        and "Amnón hijo de David" in texto["2S 13:1"] and sin_libro("Tamar_3", "2S 13") and sin_libro("Tamar_2", "2S 14"),
        "Tamar y Amnón, hijos de David (13:1; Tamar, inferido: «hermana» de Absalón), ≠ Tamar hija de Absalón (14:27)")
    ok_(tiene("Amasa_1", "2S 17:25") and rel("Ithra_1", "Amasa_1", "padre", "2S 17:25"), "Amasa, hijo de Itra (17:25)")
    ok_(tiene("Sheba_4", "2S 20:1") and rel("Bichri_1", "Sheba_4", "padre", "2S 20:1") and rol("Sheba_4", "benjamita")
        and sin_libro("Sheva_1", "2S 20:1"), "Seba, hijo de Bicri, benjamita (20:1); ≠ Seva el escriba (20:25)")
    ok_(tiene("Zadok_1", "2S 8:17") and rel("Ahitub_2", "Zadok_1", "padre", "2S 8:17") and rol("Zadok_1", "sacerdote")
        and P["Ahitub_2"]["nombre"] == "Ahitob" and "Ahitud" in P["Ahitub_2"]["formas_rv1909"],
        "Sadoc, hijo de Ahitob (RV1909 «Ahitud»), sacerdote (8:17)")
    ok_(not [p for p in EXCLUIR if any(r.startswith("2S ") for r in P.get(p, {}).get("refs", []))]
        and all(sin_libro(p, "2S ") for p in ("Ben-ammi_1", "Amalek_1", "Jacob_1")),
        "sin personas para Dios, «NA», el ángel, Jaser, el rey de Maaca, Rafa, Ariel ni los pueblos (Ammón, Amalec)")
    ok_(tiene("Gideon_1", "2S 11:21") and tiene("Abimelech_2", "2S 11:21") and "Jerubbesheth_1" not in P
        and "Abimelech_3" not in P and "2S 11:21" in R[("Gideon_1", "Abimelech_2", "padre")]["nota"],
        "Jerobaal y Abimelec (11:21) = Gedeón y su hijo de Jue 9 (no Jerubbesheth_1/Abimelech_3)")
    ok_(tiene("Goliath_1", "2S 21:19") and "1S 17:4" in P["Goliath_1"]["refs"] and "2 S 21:19" in P["Goliath_1"]["nota"]
        and tiene("Elhanan_1", "2S 21:19") and P["Elhanan_1"].get("identidad", {}).get("certeza") == "inferido",
        "Elhanán hiere a «Goliath Getheo» (21:19): Goliath_1 como en BibleData, con nota; Elhanán = Elhaanán (23:24) inferido")
    ok_(tiene("Shammah_2", "2S 13:3") and tiene("Shammah_2", "2S 21:21") and "1S 16:9" in P["Shammah_2"]["refs"]
        and P["Shammah_2"].get("identidad", {}).get("certeza") == "inferido", "Simea/Sima hermano de David = Sama (inferido)")
    ok_(tiene("Merab_1", "2S 21:8") and P["Merab_1"].get("identidad", {}).get("certeza") == "inferido"
        and sin_libro("Michal_1", "2S 21"), "21:8 «Michâl» = Merab según BibleData (inferido)")
    ok_(tiene("Ittai_1", "2S 15:19") and sin_libro("Ittai_1", "2S 23") and tiene(ITAI, "2S 23:29")
        and rel("Ribai_1", ITAI, "padre", "2S 23:29"), "Itai geteo (15:19) ≠ Itai hijo de Ribai (23:29)")
    ok_(tiene("Ira_1", "2S 20:25") and tiene("Mephibosheth_2", "2S 21:8") and rel("Saul_1", "Rizpah_1", "conyuge", "2S 3:7"),
        "Ira en 20:25 (20:26 hebreo), hijos de Rizpa y Saúl (21:8)")
    for pid, rs in (("Tamar_3", ["2S 14:27"]), ("Abigail_2", ["2S 17:25"]), ("Ahimelech_3", ["2S 8:17"]),
                    ("Ahitub_2", ["2S 8:17"]), ("Nahash_2", ["2S 17:25"]), ("Eleazar_3", ["2S 23:9"]),
                    ("Benaiah_2", ["2S 23:30"]), ("Jonathan_3", ["2S 15:27", "2S 15:36", "2S 17:17", "2S 17:20"]), ("Jonathan_4", ["2S 21:21"]),
                    ("Jonathan_5", ["2S 23:32"]), ("Eliam_2", ["2S 23:34"]), ("Baanah_2", ["2S 23:29"]),
                    ("Barzillai_2", ["2S 21:8"]), ("Shammah_3", ["2S 23:11"]), ("Shammah_4", ["2S 23:25"]),
                    ("Shammah_5", ["2S 23:33"]), ("Ira_2", ["2S 23:26"]), ("Ira_3", ["2S 23:38"])):
        ok_(all(tiene(pid, r) for r in rs) and [r for r in P[pid]["refs"] if r.startswith("2S ")] == rs,
            f"homónimo {pid} solo en {rs}")
    ok_(sin_libro("Jonathan_2", "2S 15") and sin_libro("Abigail_1", "2S 17") and sin_libro("Nahash_1", "2S 17:25")
        and sin_libro("Ahitub_1", "2S ") and sin_libro("Ahimelech_1", "2S "), "los homónimos de 1 S no se mezclan")
    e = {(x["persona"], x["tradicion"]): x["valor"] for x in datos["edades"] if x["ref"].startswith("2S ")}
    ok_(e.get(("David_1", "TM")) == 30 and e.get(("Ish-bosheth_1", "TM")) == 40 and e.get(("Barzillai_1", "TM")) == 80
        and e.get(("Mephibosheth_1", "TM")) == 5 and e.get(("David_1", "LXX")) == 30, f"edades de 2 S {sorted(e.items())}")
    for lid in OBLIGATORIOS_LUGAR:
        l = L.get(lid)
        ok_(bool(l) and any(r.startswith("2S ") and (r, lid) in ML for r in l["refs"]),
            f"lugar {lid} con refs de 2 S ({sum(1 for r in l['refs'] if r.startswith('2S ')) if l else 0})")
    ok_(("2S 5:7", "sion") in ML and ("2S 5:7", "ciudad-de-david") in ML and ("2S 5:6", "jerusalen") in ML
        and ("2S 18:6", "bosque-de-efrain") in ML, "Jerusalén, la fortaleza de Sion y la Ciudad de David (5:6-7); bosque de Efraín (18:6)")
    sin = [l for l in datos["lugares"] if any(r.startswith("2S ") for r in l["refs"]) and not l["ubicacion"]]
    ok_(all("OpenBible no da identificación" in l["nota"] for l in sin), f"lugares de 2 S sin coordenadas con nota ({len(sin)})")
    pas = [p for p in datos["pasajes"] if p["libro"] == LIBRO]
    ok_(len(pas) == len(PASAJES) and pas[0]["inicio"] == "2S 1:1" and pas[-1]["fin"] == "2S 24:25" and pas[0]["id"] == "2s-01",
        f"{len(pas)} pasajes 2s-NN de 2S 1:1 a 2S 24:25")
    ok_(len({p["seccion"] for p in pas}) == 9, "9 secciones")
    ids = [p["id"] for p in datos["pasajes"]]
    ult_1s = max(i for i, p in enumerate(datos["pasajes"]) if p["libro"] == "1S")
    lb = [l["id"] for l in datos["libros"]]
    ok_(ids.index(pas[0]["id"]) == ult_1s + 1 and lb.index(LIBRO) == lb.index("1S") + 1
        and (lb[-1] == LIBRO or lb[lb.index(LIBRO) + 1] == "1R"),
        "2 Samuel va justo después de 1 Samuel en el orden de los pasajes (lectura en orden) y antes de 1 Reyes (si está)")
    return lineas
