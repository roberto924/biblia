"""Configuración editorial para Génesis 12–50 (la usa construir_datos.py)."""

# Personas que BibleData no nombra: id de BibleData -> nombre descriptivo.
SIN_NOMBRE_BD = {
    "Wife of Lot_1": ("Esposa de Lot", "f"),
    "Firstborn of Lot_1": ("Hija mayor de Lot", "f"),
    "Younger of Lot_1": ("Hija menor de Lot", "f"),
    "King of Bela_1": ("Rey de Bela (Zoar)", "m"),
}
EXCLUIR_PERSONAS = {"YHVH_1", "NA", "the angel of the LORD_1"}

# Formas RV1909 que el detector automático no encuentra o confunde.
FORMAS_FORZADAS = {"Hanoch_1": ["Enech"], "Iob_1": ["Job"], "Pallu_1": ["Phallu"], "Perez_1": ["Phares"],
                   "Puvvah_1": ["Phua"], "Abram_1": ["Abram", "Abraham"], "Sarai_1": ["Sarai", "Sara"],
                   "Jacob_1": ["Jacob", "Israel"], "Esau_1": ["Esaú", "Edom"], "Zerah_3": ["Zara"],
                   "Zohar_1": ["Zohar"], "Ben-ammi_1": ["Ben-ammí"], "Benjamin_1": ["Benjamín", "Benoni"],
                   "Joseph_1": ["José", "Zaphnath-paaneah"]}
FORMAS_EXCLUIDAS = {"Una", "Ammonitas"}

NOTAS_NOMBRE = {
    "Abram_1": "Se llama Abram hasta Gn 17:5, donde Dios le cambia el nombre por Abraham.",
    "Sarai_1": "Se llama Sarai hasta Gn 17:15, donde Dios le cambia el nombre por Sara.",
    "Jacob_1": "En Gn 32:28 recibe el nombre de Israel; el texto sigue usando ambos.",
    "Esau_1": "El texto lo llama también Edom (Gn 25:30; 36:1).",
    "Benjamin_1": "Su madre lo llamó Benoni; su padre, Benjamín (Gn 35:18).",
    "Joseph_1": "Faraón le da el nombre Zaphnath-paaneah (Gn 41:45).",
}

# Grafía actual de uso común. Las personas que no estén aquí conservan la forma RV1909 y se listan.
MODERNO2 = {
    "Abimelech_1": "Abimelec", "Isaac_1": "Isaac", "Ishmael_1": "Ismael", "Jacob_1": "Jacob",
    "Esau_1": "Esaú", "Rebekah_1": "Rebeca", "Rachel_1": "Raquel", "Leah_1": "Lea", "Laban_1": "Labán",
    "Bilhah_1": "Bilha", "Zilpah_1": "Zilpa", "Hagar_1": "Agar", "Keturah_1": "Cetura",
    "Reuben_1": "Rubén", "Simeon_1": "Simeón", "Levi_1": "Leví", "Judah_1": "Judá", "Dan_1": "Dan",
    "Naphtali_1": "Neftalí", "Gad_1": "Gad", "Asher_1": "Aser", "Issachar_1": "Isacar",
    "Zebulun_1": "Zabulón", "Dinah_1": "Dina", "Joseph_1": "José", "Benjamin_1": "Benjamín",
    "Ephraim_1": "Efraín", "Manasseh_1": "Manasés", "Asenath_1": "Asenat", "Potiphar_1": "Potifar",
    "Potiphera_1": "Potifera", "Tamar_1": "Tamar", "Er_1": "Er", "Onan_1": "Onán", "Shelah_2": "Sela",
    "Perez_1": "Fares", "Zerah_3": "Zara", "Hamor_1": "Hamor", "Shechem_1": "Siquem",
    "Melchizedek_1": "Melquisedec", "Chedorlaomer_1": "Quedorlaomer", "Amraphel_1": "Amrafel",
    "Arioch_1": "Arioc", "Tidal_1": "Tidal", "Bera_1": "Bera", "Birsha_1": "Birsa", "Shinab_1": "Sinab",
    "Shemeber_1": "Semeber", "Bethuel_1": "Betuel", "Eliezer_1": "Eliezer", "Ephron_1": "Efrón",
    "Deborah_1": "Débora", "Basemath_1": "Basemat", "Judith_1": "Judit", "Eliphaz_1": "Elifaz",
    "Amalek_1": "Amalec", "Reuel_1": "Reuel", "Moab_1": "Moab", "Ben-ammi_1": "Ben-ammi",
    "Midian_1": "Madián", "Kedar_1": "Cedar", "Nebaioth_1": "Nebaiot", "Phicol_1": "Ficol",
    "Ahuzzath_1": "Ahuzat", "Mamre_1": "Mamre", "Aner_1": "Aner", "Eshcol_1": "Escol", "Buz_1": "Buz",
    "Kemuel_1": "Quemuel", "Chesed_1": "Quesed", "Hirah_1": "Hira", "Shua_1": "Súa", "Seir_1": "Seir",
    "Lotan_1": "Lotán", "Timna_1": "Timna", "Timna_2": "Timna", "Anah_1": "Aná", "Zibeon_1": "Zibeón",
    "Zibeon_2": "Zibeón", "Shobal_1": "Sobal", "Dishon_1": "Disón", "Dishon_2": "Disón", "Ezer_1": "Ezer",
    "Dishan_1": "Disán", "Gershon_1": "Gersón", "Kohath_1": "Coat", "Merari_1": "Merari",
    "Hezron_1": "Hezrón", "Hezron_2": "Hezrón", "Hamul_1": "Hamul", "Tola_1": "Tola",
    "Shimron_1": "Simrón", "Hanoch_1": "Hanoc", "Hanoch_2": "Hanoc", "Pallu_1": "Falú", "Carmi_1": "Carmi",
    "Jemuel_1": "Jemuel", "Jamin_1": "Jamín", "Ohad_1": "Ohad", "Jachin_1": "Jaquín", "Zohar_1": "Zohar",
    "Zohar_2": "Zohar", "Shaul_1": "Saúl", "Shaul_2": "Saúl", "Puvvah_1": "Fúa", "Iob_1": "Job",
    "Sered_1": "Sered", "Elon_1": "Elón", "Elon_2": "Elón", "Jahleel_1": "Jahleel", "Ziphion_1": "Zifión",
    "Haggi_1": "Hagui", "Shuni_1": "Suni", "Ezbon_1": "Ezbón", "Eri_1": "Eri", "Arodi_1": "Arodi",
    "Areli_1": "Areli", "Imnah_1": "Imna", "Ishvah_1": "Isúa", "Ishvi_1": "Isúi", "Beriah_1": "Bería",
    "Serah_1": "Sera", "Heber_1": "Heber", "Malchiel_1": "Malquiel", "Bela_2": "Bela",
    "Becher_1": "Bequer", "Ashbel_1": "Asbel", "Gera_1": "Gera", "Naaman_1": "Naamán", "Ehi_1": "Ehi",
    "Rosh_1": "Ros", "Muppim_1": "Mupim", "Huppim_1": "Hupim", "Ard_1": "Ard", "Hushim_1": "Husim",
    "Jahzeel_1": "Jahzeel", "Guni_1": "Guni", "Jezer_1": "Jezer", "Shillem_1": "Silem",
    "Uz_2": "Uz", "Uz_3": "Uz", "Aram_2": "Aram", "Adbeel_1": "Adbeel", "Mibsam_1": "Mibsam",
    "Mishma_1": "Misma", "Dumah_1": "Duma", "Massa_1": "Masa", "Tema_1": "Tema", "Jetur_1": "Jetur",
    "Naphish_1": "Nafis", "Kedemah_1": "Cedema", "Zimran_1": "Zimram", "Jokshan_1": "Jocsán",
    "Medan_1": "Medán", "Ishbak_1": "Isbac", "Shuah_1": "Súa", "Sheba_3": "Sabá", "Dedan_2": "Dedán",
    "Asshur_2": "Asurim", "Letush_1": "Letusim", "Leum_1": "Leumim", "Ephah_1": "Efa", "Epher_1": "Efer",
    "Abida_1": "Abida", "Eldaah_1": "Elda", "Mahalath_1": "Mahalat", "Oholibamah_1": "Aholibama",
    "Jeush_1": "Jeús", "Jalam_1": "Jaalam", "Korah_1": "Coré", "Korah_2": "Coré", "Teman_1": "Temán",
    "Omar_1": "Omar", "Zepho_1": "Zefo", "Gatam_1": "Gatam", "Kenaz_1": "Cenaz", "Nahath_1": "Nahat",
    "Zerah_1": "Zera", "Zerah_2": "Zera", "Shammah_1": "Sama", "Mizzah_1": "Miza", "Alvan_1": "Alván",
    "Manahath_1": "Manahat", "Ebal_1": "Ebal", "Shepho_1": "Sefo", "Onam_1": "Onam", "Aiah_1": "Aja",
    "Hemdan_1": "Hemdán", "Eshban_1": "Esbán", "Ithran_1": "Itrán", "Cheran_1": "Querán",
    "Bilhan_1": "Bilhán", "Zaavan_1": "Zaaván", "Akan_1": "Acán", "Hori_1": "Hori", "Hemam_1": "Hemam",
    "Aran_1": "Arán", "Bela_1": "Bela", "Beor_1": "Beor", "Jobab_2": "Jobab", "Husham_1": "Husam",
    "Hadad_1": "Hadad", "Hadad_2": "Hadad", "Bedad_1": "Bedad", "Samlah_1": "Samla",
    "Baal-hanan_1": "Baal-hanán", "Achbor_1": "Acbor", "Hadar_1": "Hadar", "Mehetabel_1": "Mehetabel",
    "Matred_1": "Matred", "Mezahab_1": "Mezaab", "Alvah_1": "Alva", "Jetheth_1": "Jetet",
    "Elah_1": "Ela", "Pinon_1": "Pinón", "Mibzar_1": "Mibzar", "Magdiel_1": "Magdiel", "Iram_1": "Iram",
    "Pharaoh_1": "Faraón", "Pharaoh_2": "Faraón", "Machir_1": "Maquir", "Maacah_1": "Maaca",
    "Tebah_1": "Teba", "Gaham_1": "Gaham", "Tahash_1": "Tahas", "Hazo_1": "Hazo", "Pildash_1": "Pildas",
    "Jidlaph_1": "Jidlaf", "Beeri_1": "Beeri", "Reumah_1": "Reúma", "Shimron_2": "Simrón",
}

# Concubinas y siervas que el texto da por mujer: (varón, mujer, ref, cita literal RV1909)
CONYUGES_EXTRA = [
    ("Abram_1", "Hagar_1", (16, 3), "dióla á Abram su marido por mujer"),
    ("Jacob_1", "Bilhah_1", (30, 4), "le dió á Bilha su sierva por mujer"),
    ("Jacob_1", "Zilpah_1", (30, 9), "dióla á Jacob por mujer"),
    ("Abram_1", "Keturah_1", (25, 1), "tomó otra mujer, cuyo nombre fué Cetura"),
    ("Nahor_2", "Reumah_1", (22, 24), "su concubina, que se llamaba Reúma"),
    ("Eliphaz_1", "Timna_1", (36, 12), "Timna fué concubina de Eliphaz"),
]
TRATO_MUJER = ["concubina", "sierva", "por mujer"]

# Personas sin nombre añadidas (id, nombre, sexo, nota, [(de, a, tipo, ref, certeza, cita)])
SIN_NOMBRE_EXTRA = [
    ("Esposa_de_Ismael", "Esposa de Ismael", "f", "El texto solo dice que era «de la tierra de Egipto».",
     [("Ishmael_1", "Esposa_de_Ismael", "conyuge", (21, 21), "explicito", "su madre le tomó mujer de la tierra de Egipto")]),
    ("Hija_de_Sua", "Hija de Súa", "f", "Esposa de Judá; la RV1909 no da su nombre.",
     [("Shua_1", "Hija_de_Sua", "padre", (38, 2), "explicito", "la hija de un hombre Cananeo, el cual se llamaba Súa"),
      ("Judah_1", "Hija_de_Sua", "conyuge", (38, 2), "explicito", "tomóla, y entró á ella"),
      ("Hija_de_Sua", "Er_1", "madre", (38, 3), "explicito", "parió un hijo; y llamó su nombre Er"),
      ("Hija_de_Sua", "Onan_1", "madre", (38, 4), "explicito", "parió un hijo, y llamó su nombre Onán"),
      ("Hija_de_Sua", "Shelah_2", "madre", (38, 5), "explicito", "parió un hijo, y llamó su nombre Sela")]),
    ("Esposa_de_Potifar", "Esposa de Potifar", "f", "El texto la llama «la mujer de su señor».",
     [("Potiphar_1", "Esposa_de_Potifar", "conyuge", (39, 7), "explicito", "la mujer de su señor")]),
    ("La_cananea", "La cananea, madre de Saúl", "f", "Madre de Saúl, hijo de Simeón; el texto no la nombra.",
     [("La_cananea", "Shaul_2", "madre", (46, 10), "explicito", "Saúl, hijo de la Cananea")]),
]

# Hijos de Jacob: (hijo, madre, versículo de nacimiento)
HIJOS_JACOB = [("Reuben_1", "Leah_1", (29, 32)), ("Simeon_1", "Leah_1", (29, 33)), ("Levi_1", "Leah_1", (29, 34)),
               ("Judah_1", "Leah_1", (29, 35)), ("Dan_1", "Bilhah_1", (30, 6)), ("Naphtali_1", "Bilhah_1", (30, 8)),
               ("Gad_1", "Zilpah_1", (30, 11)), ("Asher_1", "Zilpah_1", (30, 13)), ("Issachar_1", "Leah_1", (30, 18)),
               ("Zebulun_1", "Leah_1", (30, 20)), ("Dinah_1", "Leah_1", (30, 21)), ("Joseph_1", "Rachel_1", (30, 24)),
               ("Benjamin_1", "Rachel_1", (35, 18))]

# Edades escritas en Gn 12–50: (persona, tipo, ref, índice de cifra TM, índice LXX, evento)
EDADES_EVENTO = [
    ("Abram_1", "en_evento", (12, 4), 0, 0, "al salir de Harán"),
    ("Abram_1", "en_evento", (16, 16), 0, 0, "cuando Agar dio a luz a Ismael"),
    ("Abram_1", "en_evento", (17, 1), 0, 0, "cuando se le apareció Jehová"),
    ("Abram_1", "en_evento", (17, 17), 0, 0, "según sus propias palabras, al recibir la promesa de un hijo"),
    ("Sarai_1", "en_evento", (17, 17), 1, 1, "según palabras de Abraham, al recibir la promesa de un hijo"),
    ("Abram_1", "en_evento", (17, 24), 0, 0, "al ser circuncidado"),
    ("Ishmael_1", "en_evento", (17, 25), 0, 0, "al ser circuncidado"),
    ("Abram_1", "en_evento", (21, 5), 0, 0, "al nacer Isaac"),
    ("Sarai_1", "total", (23, 1), 0, 0, ""),
    ("Abram_1", "total", (25, 7), 0, 0, ""),
    ("Ishmael_1", "total", (25, 17), 0, 0, ""),
    ("Isaac_1", "en_evento", (25, 20), 0, 0, "al tomar por mujer a Rebeca"),
    ("Isaac_1", "en_evento", (25, 26), 0, 0, "al nacer Esaú y Jacob"),
    ("Esau_1", "en_evento", (26, 34), 0, 0, "al tomar por mujer a Judit"),
    ("Isaac_1", "total", (35, 28), 0, 0, ""),
    ("Joseph_1", "en_evento", (37, 2), 0, 0, "cuando apacentaba las ovejas con sus hermanos"),
    ("Joseph_1", "en_evento", (41, 46), 0, 0, "al presentarse ante Faraón"),
    ("Jacob_1", "en_evento", (47, 9), 0, 0, "según sus palabras ante Faraón"),
    ("Jacob_1", "total", (47, 28), 1, 1, ""),
    ("Joseph_1", "total", (50, 22), 0, 0, ""),
    ("Joseph_1", "en_evento", (50, 26), 0, 0, "al morir"),
]

SECCION_1 = "Los orígenes (Gn 1–11)"
# (inicio, fin, título, resumen, sección) — continúan tras los 26 pasajes de Gn 1–11.
S2, S3, S4, S5, S6 = ("Abraham (Gn 12–25)", "Isaac, Esaú y Jacob (Gn 25–28)",
                      "Jacob en Harán y su regreso (Gn 29–36)", "José y sus hermanos (Gn 37–45)",
                      "Jacob y José en Egipto (Gn 46–50)")
PASAJES2 = [
    ("Gn 12:1", "Gn 12:9", "El llamamiento de Abram", "Dios manda a Abram salir de su tierra y le promete una descendencia; Abram llega a Canaán y edifica altares.", S2),
    ("Gn 12:10", "Gn 12:20", "Abram y Sarai en Egipto", "Por el hambre Abram baja a Egipto, presenta a Sarai como su hermana y Faraón la toma y luego la devuelve.", S2),
    ("Gn 13:1", "Gn 13:18", "Abram y Lot se separan", "Abram y Lot se separan por sus ganados; Lot elige la llanura del Jordán y Abram se asienta en Mamre.", S2),
    ("Gn 14:1", "Gn 14:16", "La guerra de los reyes", "Cuatro reyes vencen a los reyes de Sodoma y Gomorra y se llevan a Lot; Abram los persigue y lo rescata.", S2),
    ("Gn 14:17", "Gn 14:24", "Melquisedec y el rey de Sodoma", "Melquisedec bendice a Abram, que le da el diezmo y rechaza los bienes del rey de Sodoma.", S2),
    ("Gn 15:1", "Gn 15:21", "El pacto con Abram", "Dios promete a Abram una descendencia como las estrellas y hace un pacto con él sobre la tierra.", S2),
    ("Gn 16:1", "Gn 16:16", "Agar e Ismael", "Sarai da su sierva Agar a Abram; Agar huye, el ángel la encuentra y nace Ismael.", S2),
    ("Gn 17:1", "Gn 17:14", "El pacto de la circuncisión", "Dios cambia el nombre de Abram por Abraham y manda la circuncisión como señal del pacto.", S2),
    ("Gn 17:15", "Gn 17:27", "La promesa de un hijo de Sara", "Dios cambia el nombre de Sarai por Sara y promete un hijo, Isaac; Abraham circuncida a su casa.", S2),
    ("Gn 18:1", "Gn 18:15", "Los tres visitantes en Mamre", "Abraham recibe a tres varones que anuncian que Sara tendrá un hijo, y Sara se ríe.", S2),
    ("Gn 18:16", "Gn 18:33", "Abraham intercede por Sodoma", "Dios revela a Abraham lo que hará con Sodoma y Abraham pregunta si la perdonará por unos pocos justos.", S2),
    ("Gn 19:1", "Gn 19:14", "Los ángeles en casa de Lot", "Dos ángeles se alojan con Lot, los hombres de Sodoma rodean la casa y los ángeles avisan a Lot.", S2),
    ("Gn 19:15", "Gn 19:29", "La destrucción de Sodoma y Gomorra", "Lot sale con su familia, su mujer mira atrás y Dios destruye las ciudades de la llanura.", S2),
    ("Gn 19:30", "Gn 19:38", "Lot y sus hijas", "Lot vive en una cueva con sus dos hijas, que tienen de él a Moab y a Ben-ammi.", S2),
    ("Gn 20:1", "Gn 20:18", "Abraham y Abimelec", "En Gerar Abraham presenta a Sara como su hermana; Dios advierte en sueños a Abimelec, que la devuelve.", S2),
    ("Gn 21:1", "Gn 21:8", "El nacimiento de Isaac", "Sara da a luz a Isaac, Abraham lo circuncida y hace un banquete cuando es destetado.", S2),
    ("Gn 21:9", "Gn 21:21", "Agar e Ismael en el desierto", "Abraham despide a Agar e Ismael; en el desierto Dios oye al muchacho y les muestra un pozo.", S2),
    ("Gn 21:22", "Gn 21:34", "El pacto en Beerseba", "Abraham y Abimelec hacen un pacto por un pozo y el lugar se llama Beerseba.", S2),
    ("Gn 22:1", "Gn 22:19", "La prueba de Abraham", "Dios pide a Abraham que ofrezca a Isaac en Moriah; el ángel lo detiene y se ofrece un carnero.", S2),
    ("Gn 22:20", "Gn 22:24", "Los hijos de Nacor", "Abraham recibe noticia de los hijos de Nacor, entre ellos Betuel, padre de Rebeca.", S2),
    ("Gn 23:1", "Gn 23:20", "La muerte de Sara y la cueva de Macpela", "Muere Sara y Abraham compra a Efrón la cueva de Macpela para sepultarla.", S2),
    ("Gn 24:1", "Gn 24:14", "El siervo enviado a buscar esposa", "Abraham envía a su siervo a su tierra a buscar mujer para Isaac y el siervo ora junto a un pozo.", S2),
    ("Gn 24:15", "Gn 24:27", "Rebeca junto al pozo", "Rebeca da de beber al siervo y a sus camellos, y él bendice a Dios.", S2),
    ("Gn 24:28", "Gn 24:49", "El siervo en casa de Labán", "El siervo cuenta a la familia de Rebeca su misión y lo ocurrido en el pozo.", S2),
    ("Gn 24:50", "Gn 24:67", "Rebeca va con Isaac", "La familia consiente, Rebeca parte con el siervo e Isaac la toma por mujer.", S2),
    ("Gn 25:1", "Gn 25:18", "Muerte de Abraham y descendientes de Ismael", "Se enumeran los hijos de Abraham y Cetura; Abraham muere y se listan los hijos de Ismael.", S2),
    ("Gn 25:19", "Gn 25:34", "Esaú y Jacob", "Rebeca da a luz gemelos, Esaú y Jacob; Esaú vende su primogenitura por un guiso.", S3),
    ("Gn 26:1", "Gn 26:16", "Isaac en Gerar", "Por el hambre Isaac va a Gerar, presenta a Rebeca como su hermana y prospera.", S3),
    ("Gn 26:17", "Gn 26:35", "Los pozos y el pacto de Beerseba", "Isaac abre pozos disputados, Dios se le aparece en Beerseba y hace pacto con Abimelec.", S3),
    ("Gn 27:1", "Gn 27:17", "Rebeca prepara el engaño", "Isaac pide caza a Esaú para bendecirlo y Rebeca prepara a Jacob para ocupar su lugar.", S3),
    ("Gn 27:18", "Gn 27:29", "Jacob recibe la bendición", "Jacob se presenta como Esaú e Isaac lo bendice.", S3),
    ("Gn 27:30", "Gn 27:46", "El llanto de Esaú", "Esaú llega, descubre el engaño y amenaza a Jacob; Rebeca dispone que Jacob se vaya.", S3),
    ("Gn 28:1", "Gn 28:9", "Jacob es enviado a Padan-aram", "Isaac envía a Jacob a buscar mujer en casa de Labán y Esaú toma otra mujer.", S3),
    ("Gn 28:10", "Gn 28:22", "El sueño de Jacob en Betel", "Jacob sueña con una escalera, Dios le repite la promesa y Jacob llama Betel al lugar.", S3),
    ("Gn 29:1", "Gn 29:14", "Jacob llega a casa de Labán", "Jacob encuentra a Raquel junto a un pozo y Labán lo recibe en su casa.", S4),
    ("Gn 29:15", "Gn 29:30", "Jacob se casa con Lea y Raquel", "Jacob sirve siete años por Raquel, Labán le da a Lea y luego a Raquel por otros siete.", S4),
    ("Gn 29:31", "Gn 30:13", "Los hijos de Lea, Bilha y Zilpa", "Lea da a luz a cuatro hijos; Bilha y Zilpa, siervas de Raquel y Lea, dan a luz otros cuatro.", S4),
    ("Gn 30:14", "Gn 30:24", "Las mandrágoras y el nacimiento de José", "Lea tiene más hijos y una hija, Dina; Raquel da a luz a José.", S4),
    ("Gn 30:25", "Gn 30:43", "Jacob y el ganado de Labán", "Jacob pacta con Labán su salario en ganado y se enriquece.", S4),
    ("Gn 31:1", "Gn 31:21", "Jacob huye de Labán", "Jacob parte en secreto con su familia y bienes; Raquel se lleva los ídolos de su padre.", S4),
    ("Gn 31:22", "Gn 31:42", "Labán alcanza a Jacob", "Labán persigue a Jacob, busca sus ídolos y Jacob le reprocha veinte años de servicio.", S4),
    ("Gn 31:43", "Gn 31:55", "El pacto de Galaad", "Jacob y Labán levantan un majano como testimonio de su pacto y se separan.", S4),
    ("Gn 32:1", "Gn 32:21", "Jacob se prepara para ver a Esaú", "Jacob envía mensajeros y presentes a Esaú y ora a Dios.", S4),
    ("Gn 32:22", "Gn 32:32", "La lucha en Peniel", "Jacob lucha con un varón hasta el alba, recibe el nombre de Israel y llama Peniel al lugar.", S4),
    ("Gn 33:1", "Gn 33:20", "El encuentro de Jacob y Esaú", "Esaú recibe a Jacob en paz y Jacob se asienta junto a Siquem.", S4),
    ("Gn 34:1", "Gn 34:17", "Dina y Siquem", "Siquem toma a Dina y pide casarse con ella; los hijos de Jacob exigen la circuncisión.", S4),
    ("Gn 34:18", "Gn 34:31", "La venganza de Simeón y Leví", "Los varones de la ciudad se circuncidan y Simeón y Leví los matan.", S4),
    ("Gn 35:1", "Gn 35:15", "El regreso a Betel", "Jacob vuelve a Betel, edifica un altar y Dios le confirma el nombre de Israel.", S4),
    ("Gn 35:16", "Gn 35:29", "Benjamín, Raquel e Isaac", "Raquel muere al dar a luz a Benjamín; se enumeran los hijos de Jacob e Isaac muere.", S4),
    ("Gn 36:1", "Gn 36:19", "Los descendientes de Esaú", "Se enumeran las mujeres, los hijos y los jefes descendientes de Esaú.", S4),
    ("Gn 36:20", "Gn 36:30", "Los hijos de Seir", "Se enumeran los hijos de Seir el horeo y sus jefes.", S4),
    ("Gn 36:31", "Gn 36:43", "Los reyes y jefes de Edom", "Se enumeran los reyes que reinaron en Edom y los jefes de Esaú.", S4),
    ("Gn 37:1", "Gn 37:11", "Los sueños de José", "José, preferido de su padre, cuenta sus sueños y sus hermanos lo aborrecen.", S5),
    ("Gn 37:12", "Gn 37:24", "José en la cisterna", "José busca a sus hermanos en Dotán y ellos lo echan en una cisterna.", S5),
    ("Gn 37:25", "Gn 37:36", "José es vendido", "Los hermanos venden a José a mercaderes y engañan a Jacob con su túnica.", S5),
    ("Gn 38:1", "Gn 38:11", "Judá y sus hijos", "Judá se casa, tiene tres hijos y mueren Er y Onán.", S5),
    ("Gn 38:12", "Gn 38:30", "Judá y Tamar", "Tamar se presenta a Judá sin que la reconozca y da a luz a Fares y Zara.", S5),
    ("Gn 39:1", "Gn 39:10", "José en casa de Potifar", "José prospera en casa de Potifar y rechaza a la mujer de su señor.", S5),
    ("Gn 39:11", "Gn 39:23", "José en la cárcel", "La mujer de Potifar acusa a José, que es encarcelado y prospera en la cárcel.", S5),
    ("Gn 40:1", "Gn 40:8", "El copero y el panadero", "El copero y el panadero de Faraón, presos con José, tienen sueños.", S5),
    ("Gn 40:9", "Gn 40:23", "José interpreta los sueños", "José interpreta sus sueños, que se cumplen, pero el copero se olvida de él.", S5),
    ("Gn 41:1", "Gn 41:16", "Los sueños de Faraón", "Faraón tiene dos sueños que nadie interpreta y el copero recuerda a José.", S5),
    ("Gn 41:17", "Gn 41:36", "José interpreta a Faraón", "José anuncia siete años de abundancia y siete de hambre y aconseja almacenar.", S5),
    ("Gn 41:37", "Gn 41:46", "José gobernador de Egipto", "Faraón pone a José sobre Egipto, le da nombre y mujer.", S5),
    ("Gn 41:47", "Gn 41:57", "Los años de abundancia y de hambre", "José almacena grano, tiene a Manasés y Efraín, y llega el hambre.", S5),
    ("Gn 42:1", "Gn 42:17", "Los hermanos bajan a Egipto", "Diez hermanos van a comprar grano; José los reconoce y los acusa de espías.", S5),
    ("Gn 42:18", "Gn 42:38", "Simeón queda preso", "José retiene a Simeón y exige que traigan a Benjamín; Jacob se niega.", S5),
    ("Gn 43:1", "Gn 43:15", "El segundo viaje con Benjamín", "El hambre continúa y Jacob deja ir a Benjamín con Judá.", S5),
    ("Gn 43:16", "Gn 43:34", "La comida en casa de José", "Los hermanos comen en casa de José, que se conmueve al ver a Benjamín.", S5),
    ("Gn 44:1", "Gn 44:17", "La copa en el costal de Benjamín", "José hace esconder su copa en el costal de Benjamín y los hace volver.", S5),
    ("Gn 44:18", "Gn 44:34", "La súplica de Judá", "Judá pide quedarse como siervo en lugar de Benjamín.", S5),
    ("Gn 45:1", "Gn 45:15", "José se da a conocer", "José se da a conocer a sus hermanos y les pide que traigan a su padre.", S5),
    ("Gn 45:16", "Gn 45:28", "Faraón invita a la familia de Jacob", "Faraón ofrece tierra en Egipto; los hermanos vuelven y Jacob decide ir.", S5),
    ("Gn 46:1", "Gn 46:7", "Jacob baja a Egipto", "Dios habla a Jacob en Beerseba y Jacob parte hacia Egipto con su familia.", S6),
    ("Gn 46:8", "Gn 46:27", "La lista de la familia de Jacob", "Se enumeran los descendientes de Jacob que entraron en Egipto.", S6),
    ("Gn 46:28", "Gn 47:12", "Jacob ante José y Faraón", "José recibe a su padre en Gosén y presenta a su familia ante Faraón.", S6),
    ("Gn 47:13", "Gn 47:26", "José y el hambre en Egipto", "Durante el hambre José compra para Faraón el ganado y las tierras de Egipto.", S6),
    ("Gn 47:27", "Gn 48:7", "El juramento de José", "Jacob hace jurar a José que lo sepultará en Canaán y recuerda la promesa de Dios.", S6),
    ("Gn 48:8", "Gn 48:22", "La bendición de Efraín y Manasés", "Jacob bendice a los hijos de José y pone a Efraín delante de Manasés.", S6),
    ("Gn 49:1", "Gn 49:15", "Las palabras de Jacob a sus hijos (I)", "Jacob habla a Rubén, Simeón, Leví, Judá, Zabulón e Isacar.", S6),
    ("Gn 49:16", "Gn 49:33", "Las palabras de Jacob a sus hijos (II) y su muerte", "Jacob habla a Dan, Gad, Aser, Neftalí, José y Benjamín, y muere.", S6),
    ("Gn 50:1", "Gn 50:14", "La sepultura de Jacob", "Egipto llora a Jacob y sus hijos lo sepultan en la cueva de Macpela.", S6),
    ("Gn 50:15", "Gn 50:26", "José y sus hermanos; muerte de José", "José tranquiliza a sus hermanos, ve a sus bisnietos y muere a los 110 años.", S6),
]

# Lugares de Gn 12–50: id OpenBible -> (nombre actual, tipo). Sin entrada: se usa la forma RV1909.
LUGARES2 = {
    "a70ac98": ("Abel-mizraim", "otro"), "a7e13e1": ("Hai", "ciudad"), "af9a894": ("Alón-bacut", "otro"),
    "afe4be0": ("Astarot-karnaim", "ciudad"), "a2f186d": ("Atad", "otro"), "aae8a95": ("Avit", "ciudad"),
    "a075d61": ("Beerseba", "ciudad"), "aa3ff18": ("Bered", "otro"), "a64f355": ("Betel", "ciudad"),
    "a112427": ("Belén", "ciudad"), "a871210": ("Bosra", "ciudad"), "ab41e6b": ("Quezib", "ciudad"),
    "a69c1d4": ("Damasco", "ciudad"), "a513646": ("Dan", "ciudad"), "ae28fc7": ("Dinaba", "ciudad"),
    "ab635e4": ("Dotán", "ciudad"), "a2735ff": ("Edom", "region"), "af301ca": ("Egipto", "region"),
    "a7e3a59": ("Elam", "region"), "a30b045": ("El-Betel", "otro"), "a6f4a6d": ("Elasar", "ciudad"),
    "a738bf1": ("El-parán", "otro"), "af4e985": ("Efrata", "ciudad"), "a43608b": ("Esek", "otro"),
    "ae73b90": ("Galaad", "region"), "a60f092": ("Gosén", "region"), "a7a5f29": ("Ham", "ciudad"),
    "ac5e5c4": ("Havila", "region"), "a4d6a38": ("Hazezón-tamar", "ciudad"), "a85151a": ("Hebrón", "ciudad"),
    "acd9137": ("On", "ciudad"), "a6779cd": ("Hoba", "ciudad"), "aca7bd9": ("Jaboc", "rio"),
    "ae686c9": ("Jordán", "rio"), "ac2cef0": ("Cades", "ciudad"), "a397042": ("Luz", "ciudad"),
    "ae00861": ("Macpela", "otro"), "ae5bfe9": ("Mahanaim", "ciudad"), "aeb9e97": ("Mamre", "otro"),
    "a57e0a0": ("Masreca", "ciudad"), "a43f60f": ("Mesopotamia", "region"), "acc6d8e": ("Madián", "region"),
    "aa0b1d6": ("Moab", "region"), "a38ad9f": ("More", "otro"), "adaf385": ("Moriah", "monte"),
    "ae981db": ("Seir", "monte"), "aff43ac": ("Nacor (ciudad)", "ciudad"), "a8ec7ba": ("Padan-aram", "region"),
    "aa6b19b": ("Parán", "region"), "a880de2": ("Pau", "ciudad"), "a8a9ff9": ("Peniel", "otro"),
    "a079b21": ("Ramesés", "region"), "ab1d954": ("Rehobot (pozo)", "otro"), "a17e154": ("Rehobot del Río", "ciudad"),
    "aad7e4e": ("Salem", "ciudad"), "a86d49f": ("Save-quiriataim", "otro"), "adf74d4": ("Siquem", "ciudad"),
    "aa4680a": ("Siloh", "otro"), "acdbce0": ("Shur", "region"), "aa454f7": ("Sitna", "otro"),
    "a0905b5": ("Sucot", "ciudad"), "a17c178": ("Timnat", "ciudad"), "aacfcda": ("Zoar", "ciudad"),
}
NOTAS_LUGAR2 = {
    "aa4680a": "En Gn 49:10 «Shiloh» puede entenderse como lugar o de otras maneras; OpenBible lo registra como lugar.",
    "a2735ff": "Edom es también otro nombre de Esaú; donde el texto se refiere a la persona, la mención va como persona.",
}
# Formas de lugar que no se usan (gentilicios o confusiones del detector).
FORMAS_LUGAR_EXCLUIDAS = {"Adullamita", "Ammonitas", "Caphtorim", "Caldeos", "Damasceno", "Elá", "Galaad@a694ea2",
                          "Gerar@a816ed9", "Parán@a738bf1", "Elazar"}

# Persona que BibleData no separa: en su PersonVerse, la Ada de Gn 36 figura como Adah_1 (mujer de Lamec).
# Esposas de Esaú: NO se armonizan. Cada nombre se registra como lo da el texto (Gn 26:34; 28:9; 36:2-3);
# BibleData identifica Judit = Aholibama, Basemat (hija de Elón) = Ada y Mahalat = Basemath (hija de Ismael):
# eso queda solo en `nota`. Sus filas de Gn 36 se reasignan a personas propias.
PV_REASIGNAR = [("Adah_1", 36, "Adah_2"), ("Judith_1", 36, "Oholibamah_esposa"), ("Mahalath_1", 36, "Basemath_2")]
# Relaciones de BibleData con ref en ese capítulo: (persona, cap, persona nueva).
REL_REASIGNAR = [("Judith_1", 36, "Oholibamah_esposa"), ("Mahalath_1", 36, "Basemath_2"), ("Basemath_1", 36, "Adah_2")]
_ID_TRAD = " La identificación tradicional ({}) no está en el texto: no se fusionan."
PERSONAS_NUEVAS = {
    "Adah_2": ("Ada", "f", "Ada", "Mujer de Esaú, hija de Elón heteo (Gn 36:2). BibleData no la registra como persona "
                                  "propia (su índice de versículos la confunde con Ada, mujer de Lamec); aquí se separa."
               + _ID_TRAD.format("BibleData la trata como la Basemat hija de Elón de Gn 26:34")),
    "Oholibamah_esposa": ("Aholibama", "f", "Aholibama",
                          "Mujer de Esaú, «hija de Ana, hija de Zibeón el Heveo» (Gn 36:2; 36:14, 25)."
                          + _ID_TRAD.format("con Judit hija de Beeri, Gn 26:34") +
                          " Distinta del jefe Aholibama de Gn 36:41."),
    "Basemath_2": ("Basemat", "f", "Basemath",
                   "Mujer de Esaú, «hija de Ismael, hermana de Navaioth» (Gn 36:3)."
                   + _ID_TRAD.format("con Mahalat hija de Ismael, Gn 28:9") +
                   " Distinta de Basemat hija de Elón (Gn 26:34)."),
}
# Matrimonios que el texto dice: (a, b, ref, cita literal RV1909, nota)
MATRIMONIOS = [
    ("Abram_1", "Sarai_1", (11, 29), "el nombre de la mujer de Abram fué Sarai", ""),
    ("Nahor_2", "Milcah_1", (11, 29), "el nombre de la mujer de Nachôr, Milca", ""),
    ("Lot_1", "Wife of Lot_1", (19, 26), "la mujer de Lot", ""),
    ("Isaac_1", "Rebekah_1", (24, 67), "tomó á Rebeca por mujer", ""),
    ("Esau_1", "Judith_1", (26, 34), "tomó por mujer á Judith hija de Beeri Hetheo",
     "Gn 36:2-3 da otra lista de mujeres de Esaú (Ada hija de Elón, Aholibama hija de Ana, Basemath hija de "
     "Ismael); el texto no dice cuál corresponde a cuál y no se armoniza."),
    ("Esau_1", "Basemath_1", (26, 34), "y á Basemat hija de Elón Hetheo",
     "Hija de Elón según Gn 26:34; la «Basemath» de Gn 36:3 es hija de Ismael y va aparte."),
    ("Esau_1", "Mahalath_1", (28, 9), "tomó para sí por mujer á Mahaleth", ""),
    ("Esau_1", "Adah_2", (36, 2), "á Ada, hija de Elón Hetheo",
     "En Gn 26:34 la hija de Elón se llama Basemat; el texto no dice si es la misma mujer y no se armoniza."),
    ("Esau_1", "Oholibamah_esposa", (36, 2), "á Aholibama, hija de Ana, hija de Zibeón el Heveo",
     "No se registra un padre: el texto dice «hija de Ana» sin precisar qué Ana es."),
    ("Esau_1", "Basemath_2", (36, 3), "Y á Basemath, hija de Ismael", ""),
    ("Jacob_1", "Leah_1", (29, 23), "tomó á Lea su hija, y se la trajo: y él entró á ella", ""),
    ("Jacob_1", "Rachel_1", (29, 28), "le dió á Rachêl su hija por mujer", ""),
    ("Er_1", "Tamar_1", (38, 6), "Judá tomó mujer para su primogénito Er, la cual se llamaba Thamar", ""),
    ("Onan_1", "Tamar_1", (38, 8), "Entra á la mujer de tu hermano, y despósate con ella",
     "Judá ordena a Onán desposarse con la viuda de su hermano; Gn 38:9 dice que Onán entraba a ella."),
    ("Joseph_1", "Asenath_1", (41, 45), "dióle por mujer á Asenath", ""),
    ("Hadar_1", "Mehetabel_1", (36, 39), "el nombre de su mujer Meetabel", ""),
]
QUITAR_CONYUGE = {("Judah_1", "Tamar_1")}
SIN_NOMBRE_EXTRA += [
    ("Esposa_de_Abimelec", "Esposa de Abimelec", "f", "El texto solo dice «su mujer».",
     [("Abimelech_1", "Esposa_de_Abimelec", "conyuge", (20, 17), "explicito", "sanó á Abimelech y á su mujer")]),
]
RELACIONES_EXTRA = [  # (de, a, tipo, ref, cita, nota)
    ("Elon_1", "Adah_2", "padre", (36, 2), "Ada, hija de Elón", ""),
    ("Adah_2", "Eliphaz_1", "madre", (36, 10), "Eliphaz, hijo de Ada", ""),
    ("Ishmael_1", "Basemath_2", "padre", (36, 3), "Basemath, hija de Ismael", ""),
    ("Basemath_2", "Reuel_1", "madre", (36, 4), "Basemath parió á Reuel", ""),
    ("Oholibamah_esposa", "Jeush_1", "madre", (36, 5), "Aholibama parió á Jeús", ""),
    ("Oholibamah_esposa", "Jalam_1", "madre", (36, 5), "Aholibama parió á Jeús, y á Jaalam", ""),
    ("Oholibamah_esposa", "Korah_1", "madre", (36, 5), "Aholibama parió á Jeús, y á Jaalam, y á Cora", ""),
]
_NOTA_ESAU = "Mujer de Esaú. Identificación tradicional (BibleData): {}. El texto no lo dice: no se fusionan."
NOTAS_ESPOSAS_ESAU = {
    "Judith_1": _NOTA_ESAU.format("la misma que Aholibama hija de Ana (Gn 36:2)"),
    "Basemath_1": _NOTA_ESAU.format("la misma que Ada hija de Elón (Gn 36:2)"),
    "Mahalath_1": _NOTA_ESAU.format("la misma que Basemath hija de Ismael (Gn 36:3)"),
}
# Pares padre–madre sin matrimonio en el texto: nota que se pone en las relaciones del hijo.
SIN_PAREJA_NOTA = {
    ("Judah_1", "Tamar_1"): "El texto no presenta a Judá y Tamar como matrimonio (Gn 38:15-18, 26).",
    ("Lot_1", "Firstborn of Lot_1"): "Hijo de Lot y de su hija mayor (Gn 19:33-37); el texto no lo presenta como matrimonio.",
    ("Simeon_1", "La_cananea"): "El texto solo dice «Saúl, hijo de la Cananea» (Gn 46:10); no menciona matrimonio.",
    ("Lot_1", "Younger of Lot_1"): "Hijo de Lot y de su hija menor (Gn 19:35-38); el texto no lo presenta como matrimonio.",
}
NOTAS_PERSONA = {p: "Gn 46:21 lo cuenta entre los hijos de Benjamín; otras listas bíblicas (Nm 26:38-40; "
                    "1 Cr 7:6-12; 8:1-5) dan la familia de Benjamín de otra manera. Aquí se sigue a Génesis."
                 for p in ("Ard_1", "Huppim_1", "Muppim_1", "Naaman_1")}
# Personas sin parentesco en el texto: (rol, ref, cita literal RV1909)
ROLES = {
    "Pharaoh_1": ("rey de Egipto en tiempos de Abram", (12, 15), "Faraón"),
    "Amraphel_1": ("rey de Sinar", (14, 1), "Amraphel, rey de Shinar"),
    "Arioch_1": ("rey de Elazar", (14, 1), "Arioch, rey de Elazar"),
    "Chedorlaomer_1": ("rey de Elam (la RV1909 escribe «Elá»)", (14, 1), "Chêdorlaomer, rey de Elá"),
    "Tidal_1": ("rey de naciones", (14, 1), "Tidal, rey de naciones"),
    "Bera_1": ("rey de Sodoma", (14, 2), "Bera, rey de Sodoma"),
    "Birsha_1": ("rey de Gomorra", (14, 2), "Birsha, rey de Gomorra"),
    "King of Bela_1": ("rey de Bela, que es Zoar", (14, 2), "el rey de Bela, la cual es Zoar"),
    "Shemeber_1": ("rey de Zeboim", (14, 2), "Shemeber, rey de Zeboim"),
    "Shinab_1": ("rey de Adma", (14, 2), "Shinab, rey de Adma"),
    "Aner_1": ("amorreo, aliado de Abram", (14, 13), "Aner"),
    "Eshcol_1": ("amorreo, aliado de Abram", (14, 13), "Eschôl"),
    "Mamre_1": ("amorreo, aliado de Abram", (14, 13), "Mamre Amorrheo"),
    "Melchizedek_1": ("rey de Salem, sacerdote del Dios alto", (14, 18), "Melchîsedec, rey de Salem"),
    "Eliezer_1": ("mayordomo de la casa de Abram, damasceno", (15, 2), "Eliezer"),
    "Abimelech_1": ("rey de Gerar", (20, 2), "Abimelech, rey de Gerar"),
    "Phicol_1": ("príncipe del ejército de Abimelec", (21, 22), "Phicol, príncipe de su ejército"),
    "Ahuzzath_1": ("amigo de Abimelec", (26, 26), "Ahuzzath, amigo suyo"),
    "Deborah_1": ("ama de Rebeca", (35, 8), "Débora, ama de Rebeca"),
    "Zibeon_1": ("heveo, antepasado de Aholibama", (36, 2), "Zibeón el Heveo"),
    "Husham_1": ("rey de Edom", (36, 34), "Husam"),
    "Samlah_1": ("rey de Edom", (36, 36), "Samla"),
    "Shaul_1": ("rey de Edom", (36, 37), "Saúl"),
    "Pharaoh_2": ("rey de Egipto en tiempos de José", (37, 36), "Faraón"),
    "Hirah_1": ("adullamita, amigo de Judá", (38, 12), "su amigo Hira el Adullamita"),
}
for _p, _r in (("Alvah_1", 40), ("Jetheth_1", 40), ("Timna_2", 40), ("Elah_1", 41), ("Oholibamah_1", 41),
               ("Pinon_1", 41), ("Mibzar_1", 42), ("Iram_1", 43), ("Magdiel_1", 43)):
    ROLES[_p] = ("jefe (duque) de Edom", (36, _r), "duque")
NOTAS_PERSONA.update({
    "Timna_2": "Jefe de Edom (Gn 36:40); BibleData lo distingue de Timna, concubina de Elifaz.",
    "Oholibamah_1": "Jefe de Edom (Gn 36:41); BibleData lo distingue de Aholibama, mujer de Esaú.",
})
NOTAS_PERSONA.update(NOTAS_ESPOSAS_ESAU)
MODERNO2.update({"Oholibamah_esposa": "Aholibama", "Basemath_2": "Basemat"})
