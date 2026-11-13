"""Éxodo 1–40: personas, relaciones, edades, pasajes, menciones y lugares (lo usa construir_datos.py).

Mismo principio que Génesis: cada dato lleva versículo, fuente y certeza; las citas se comprueban
literalmente contra la RV1909 (TM) o Brenton (LXX). Las personas compartidas con Génesis (Jacob, Leví…)
son la misma persona (mismo id de BibleData): se amplían sus `refs`.
Solo biblioteca estándar.
"""
import json
import re
import sys
from collections import Counter, defaultdict

import lugares_mapa as lm
import nombres_auto as na

LIBRO = "Ex"
NOMBRE = "Éxodo"
USX = "EXO"  # código del libro en BibleData/OpenBible/VPL
CAPITULOS = 40
EXCLUIR = {"YHVH_1", "NA", "the angel of the LORD_1",
           "Amalek_1"}  # en Éxodo «Amalec» es el pueblo (va como lugar/pueblo de OpenBible), no el nieto de Esaú
# Jacob: en Éxodo «Israel» casi siempre es el pueblo; solo se toman las filas de BibleData con la etiqueta «Jacob».
SOLO_ETIQUETA = {"Jacob_1": {"Jacob"}}
FORMA_NO_MENCION = {("Jacob_1", "israel")}  # no se marca «Israel» como mención de Jacob en Éxodo
# Filas de BibleData-PersonVerse que no se usan (el versículo no habla de esa persona).
PV_DESCARTAR = {("Bezalel_1", (34, 23)): "Ex 34:23 no menciona a Bezaleel (probable errata de BibleData)."}
FORMAS_FORZADAS = {"Puah_1": ["Phúa"], "Miriam_1": ["María"], "Reuel_2": ["Ragüel", "Jethro"]}

MODERNO = {
    "Moses_1": "Moisés", "Aaron_1": "Aarón", "Pharaoh_3": "Faraón", "Pharaoh_4": "Faraón", "Shiphrah_1": "Sifra",
    "Puah_1": "Fúa", "Reuel_2": "Jetro (Reuel)", "Zipporah_1": "Séfora", "Gershom_1": "Gersón", "Libni_1": "Libni",
    "Shimei_1": "Simei", "Amram_1": "Amram", "Izhar_1": "Izhar", "Hebron_1": "Hebrón", "Uzziel_1": "Uziel",
    "Mahli_1": "Mahli", "Mushi_1": "Musi", "Jochebed_1": "Jocabed", "Korah_3": "Coré", "Nepheg_1": "Nefeg",
    "Zichri_1": "Zicri", "Mishael_1": "Misael", "Elzaphan_1": "Elzafán", "Sithri_1": "Sitri",
    "Elisheba_1": "Elisabet", "Amminadab_1": "Aminadab", "Nahshon_1": "Naasón", "Nadab_1": "Nadab",
    "Abihu_1": "Abiú", "Eleazar_1": "Eleazar", "Ithamar_1": "Itamar", "Assir_1": "Asir", "Elkanah_1": "Elcana",
    "Abiasaph_1": "Abiasaf", "Putiel_1": "Futiel", "Phinehas_1": "Finees", "Miriam_1": "Miriam",
    "Joshua_1": "Josué", "Hur_1": "Hur", "Eliezer_2": "Eliezer", "Bezalel_1": "Bezaleel", "Uri_1": "Uri",
    "Oholiab_1": "Aholiab", "Ahisamach_1": "Ahisamac", "Nun_1": "Nun",
}
NOTAS = {
    "Reuel_2": ("El texto lo llama Ragüel (Reuel) en Ex 2:18 y Jetro desde Ex 3:1; en ambos casos es el sacerdote "
                "de Madián y suegro de Moisés (Ex 2:16-21; 3:1; 18:1). Se trata como una sola persona siguiendo a "
                "BibleData: la identificación es inferida, el texto no dice que sean el mismo. Distinto de Reuel, "
                "hijo de Esaú (Gn 36:4)."),
    "Hur_1": ("BibleData identifica al Hur que acompaña a Moisés (Ex 17:10; 24:14) con el abuelo de Bezaleel "
              "(Ex 31:2); el texto no lo dice (identificación inferida)."),
    "Miriam_1": ("Ex 15:20 la llama «hermana de Aarón»; el texto masorético de Éxodo no nombra a sus padres: "
                 "su filiación (Amram y Jocabed) es inferida. La LXX (Brenton) en Ex 6:20 añade «and Mariam "
                 "their sister». La «hermana» de Moisés de Ex 2:4-8 no tiene nombre y no se identifica con ella."),
    "Jochebed_1": ("Ex 6:20: la RV1909 dice «su tía»; la LXX (Brenton) dice «the daughter of his father's "
                   "brother». BibleData la hace hermana de Coat (relación entre hermanos: no se registra)."),
    "Gershom_1": "Hijo de Moisés; distinto de Gersón, hijo de Leví (Ex 6:16).",
    "Korah_3": "Hijo de Izhar (Ex 6:21); distinto de Coré, hijo de Esaú (Gn 36:5).",
    "Eliezer_2": "Hijo de Moisés; distinto de Eliezer, mayordomo de Abram (Gn 15:2).",
    "Zichri_1": ("La RV1909 escribe «Zithri», igual que el hijo de Uziel (Ex 6:22); el hebreo distingue Zicri "
                 "(hijo de Izhar) y Sitri (hijo de Uziel)."),
    "Sithri_1": "Hijo de Uziel (Ex 6:22); la RV1909 escribe «Zithri», como al hijo de Izhar (Ex 6:21).",
    "Pharaoh_3": ("BibleData distingue dos faraones en Éxodo: el que somete a Israel y muere (Ex 1:8–2:23) y el de "
                  "las plagas y la salida (desde Ex 3:10). El texto no da sus nombres."),
    "Pharaoh_4": ("Faraón de las plagas y de la salida (desde Ex 3:10); BibleData lo distingue del que muere en "
                  "Ex 2:23. El texto no da su nombre."),
}
# Identificaciones de una persona con dos nombres o dos papeles: certeza inferida, con versículos.
IDENTIDAD = {
    "Reuel_2": {"certeza": "inferido", "refs": ["Ex 2:18", "Ex 3:1"], "nombres_rv1909": ["Ragüel", "Jethro"],
                "fuente": "bibledata"},
    "Hur_1": {"certeza": "inferido", "refs": ["Ex 17:10", "Ex 31:2"], "fuente": "bibledata"},
}
# Fragmentos que las notas afirman: deben estar en el versículo (tradición, ref, texto).
NOTAS_VERIFICAR = [("TM", (2, 18), "Ragüel su padre"), ("TM", (3, 1), "Jethro su suegro, sacerdote de Madián"),
                   ("TM", (15, 20), "hermana de Aarón"), ("LXX", (6, 20), "and Mariam their sister"),
                   ("TM", (6, 20), "su tía"), ("LXX", (6, 20), "the daughter of his father's brother"),
                   ("TM", (17, 10), "Hur"), ("TM", (31, 2), "hijo de Uri, hijo de Hur")]
# Personas sin parentesco (o con un papel que conviene decir): (rol, ref, cita literal RV1909)
ROLES = {
    "Shiphrah_1": ("partera de las hebreas", (1, 15), "una de las cuales se llamaba Siphra"),
    "Puah_1": ("partera de las hebreas", (1, 15), "y otra Phúa"),
    "Pharaoh_3": ("rey de Egipto que somete a Israel", (1, 11), "edificaron á Faraón las ciudades de los bastimentos"),
    "Pharaoh_4": ("rey de Egipto ante quien hablan Moisés y Aarón", (5, 1), "entraron Moisés y Aarón á Faraón"),
    "Hija_de_Faraon": ("recoge a Moisés del río y lo prohíja", (2, 10), "la hija de Faraón, la cual lo prohijó"),
    "Aaron_1": ("hermano de Moisés", (4, 14), "tu hermano Aarón"),
    "Miriam_1": ("profetisa, hermana de Aarón", (15, 20), "María la profetisa, hermana de Aarón"),
    "Reuel_2": ("sacerdote de Madián, suegro de Moisés", (3, 1), "Jethro su suegro, sacerdote de Madián"),
    "Joshua_1": ("ayudante de Moisés; pelea contra Amalec", (17, 9), "dijo Moisés á Josué"),
    "Hur_1": ("sube con Moisés y Aarón al collado", (17, 10), "Moisés y Aarón y Hur subieron"),
    "Bezalel_1": ("artífice del tabernáculo, de la tribu de Judá", (31, 2), "Bezaleel, hijo de Uri, hijo de Hur, de la tribu de Judá"),
    "Oholiab_1": ("artífice del tabernáculo, de la tribu de Dan", (31, 6), "Aholiab, hijo de Ahisamac, de la tribu de Dan"),
}
# Personas que el texto menciona sin nombre: id -> (nombre, sexo, nota, [(de, a, tipo, ref, certeza, cita)])
SIN_NOMBRE = {
    "Hija_de_Faraon": ("Hija de Faraón", "f", "El texto no da su nombre.",
                       [("Pharaoh_3", "Hija_de_Faraon", "padre", (2, 5), "explicito", "la hija de Faraón")]),
    "Hija_de_Putiel": ("Hija de Futiel, mujer de Eleazar", "f",
                       "El texto solo dice «mujer de las hijas de Phutiel» (Ex 6:25); no da su nombre.",
                       [("Eleazar_1", "Hija_de_Putiel", "conyuge", (6, 25), "explicito",
                         "tomó para sí mujer de las hijas de Phutiel"),
                        ("Putiel_1", "Hija_de_Putiel", "padre", (6, 25), "explicito", "mujer de las hijas de Phutiel"),
                        ("Hija_de_Putiel", "Phinehas_1", "madre", (6, 25), "explicito", "la cual le parió á Phinees")]),
}
# Relaciones que el texto dice (fijan cita y certeza): (de, a, tipo, ref, cita, nota)
RELACIONES = [
    ("Moses_1", "Zipporah_1", "conyuge", (2, 21), "dió á Moisés á su hija Séphora", "También Ex 18:2: «Séphora la mujer de Moisés»."),
    ("Reuel_2", "Zipporah_1", "padre", (2, 21), "dió á Moisés á su hija Séphora",
     "El padre de Séfora es llamado Ragüel en Ex 2:18 y Jetro en Ex 3:1 (identificación inferida)."),
    ("Moses_1", "Gershom_1", "padre", (2, 22), "le parió un hijo, y él le puso por nombre Gersom",
     "Ex 2:21-22: Séfora, dada a Moisés, le pare un hijo."),
    ("Zipporah_1", "Gershom_1", "madre", (2, 22), "La cual le parió un hijo", "Ex 2:21-22."),
    ("Moses_1", "Eliezer_2", "padre", (18, 4), "el otro se llamaba Eliezer",
     "Ex 18:2-4: «sus dos hijos» (de Moisés y Séfora): Gersom y Eliezer."),
    ("Zipporah_1", "Eliezer_2", "madre", (18, 4), "el otro se llamaba Eliezer", "Ex 18:2-4."),
    ("Amram_1", "Jochebed_1", "conyuge", (6, 20), "Amram tomó por mujer á Jochêbed su tía", ""),
    ("Amram_1", "Aaron_1", "padre", (6, 20), "Amram tomó por mujer á Jochêbed su tía; la cual le parió á Aarón", ""),
    ("Amram_1", "Moses_1", "padre", (6, 20), "la cual le parió á Aarón y á Moisés", ""),
    ("Jochebed_1", "Aaron_1", "madre", (6, 20), "Jochêbed su tía; la cual le parió á Aarón", ""),
    ("Jochebed_1", "Moses_1", "madre", (6, 20), "la cual le parió á Aarón y á Moisés", ""),
    ("Kohath_1", "Amram_1", "padre", (6, 18), "los hijos de Coath: Amram", ""),
    ("Aaron_1", "Elisheba_1", "conyuge", (6, 23), "tomóse Aarón por mujer á Elisabeth", ""),
    ("Eleazar_1", "Phinehas_1", "padre", (6, 25), "Eleazar, hijo de Aarón, tomó para sí mujer de las hijas de Phutiel, la cual le parió á Phinees", ""),
]
for _h in ("Nadab", "Abiú", "Eleazar", "Ithamar"):
    _id = {"Nadab": "Nadab_1", "Abiú": "Abihu_1", "Eleazar": "Eleazar_1", "Ithamar": "Ithamar_1"}[_h]
    RELACIONES.append(("Aaron_1", _id, "padre", (6, 23), "tomóse Aarón por mujer á Elisabeth", ""))
    RELACIONES.append(("Elisheba_1", _id, "madre", (6, 23), "la cual le parió á Nadab", ""))
NOTAS_REL = {
    ("Amram_1", "Miriam_1", "padre"): "Inferida: Éxodo solo la llama «hermana de Aarón» (Ex 15:20); la LXX de Ex 6:20 añade «and Mariam their sister».",
    ("Jochebed_1", "Miriam_1", "madre"): "Inferida: Éxodo solo la llama «hermana de Aarón» (Ex 15:20); la LXX de Ex 6:20 añade «and Mariam their sister».",
}
# Relaciones que ya están en Génesis y que Éxodo repite: se añade la referencia a la nota.
REPITE_GN = [("Levi_1", "Kohath_1", "padre", (6, 16), "los hijos de Leví por sus linajes: Gersón, y Coath, y Merari")]
# Edades escritas: (persona, tipo, ref, índice de cifra TM, índice LXX, evento)
EDADES = [
    ("Moses_1", "en_evento", (7, 7), 0, 0, "al hablar a Faraón"),
    ("Aaron_1", "en_evento", (7, 7), 1, 1, "al hablar a Faraón"),
    ("Levi_1", "total", (6, 16), 0, 0, ""),
    ("Kohath_1", "total", (6, 18), 0, 0, ""),
    ("Amram_1", "total", (6, 20), 0, 0, ""),
]

S1 = "Opresión y llamamiento de Moisés (Ex 1–6)"
S2 = "Las plagas y la Pascua (Ex 7:1–13:16)"
S3 = "Del mar Bermejo al Sinaí (Ex 13:17–18:27)"
S4 = "La alianza en el Sinaí (Ex 19–24)"
S5 = "Instrucciones para el tabernáculo (Ex 25–31)"
S6 = "El becerro de oro y la renovación del pacto (Ex 32–34)"
S7 = "La construcción del tabernáculo (Ex 35–40)"
PASAJES = [
    ("1:1", "1:14", "Israel se multiplica y es oprimido", "Los descendientes de Jacob crecen en Egipto; un nuevo rey que no conocía a José los somete a dura servidumbre.", S1),
    ("1:15", "1:22", "Las parteras de las hebreas", "Faraón manda a las parteras Sifra y Fúa matar a los niños varones; ellas temen a Dios y Faraón ordena echarlos al río.", S1),
    ("2:1", "2:10", "El nacimiento de Moisés", "Una mujer de la familia de Leví esconde a su hijo en una arquilla junto al río; la hija de Faraón lo recoge y lo llama Moisés.", S1),
    ("2:11", "2:22", "Moisés huye a Madián", "Moisés mata a un egipcio, huye a Madián, defiende a las hijas del sacerdote y recibe por mujer a Séfora, que le da a Gersón.", S1),
    ("2:23", "3:12", "La zarza ardiente", "Dios oye el clamor de Israel y llama a Moisés desde una zarza que arde en Horeb para enviarlo a Faraón.", S1),
    ("3:13", "3:22", "El nombre de Dios y la misión", "Dios revela su nombre a Moisés y le anuncia que sacará a Israel de Egipto a la tierra prometida.", S1),
    ("4:1", "4:17", "Las señales y Aarón como portavoz", "Dios da a Moisés señales (la vara, la mano, el agua) y le da a su hermano Aarón para que hable por él.", S1),
    ("4:18", "4:31", "Moisés vuelve a Egipto", "Moisés se despide de Jetro y vuelve con su familia; Séfora circuncida a su hijo; Moisés y Aarón hablan a los ancianos y el pueblo cree.", S1),
    ("5:1", "5:14", "Ladrillos sin paja", "Moisés y Aarón piden a Faraón que deje ir al pueblo; Faraón niega la paja y aumenta el trabajo.", S1),
    ("5:15", "6:1", "La queja de los capataces", "Los capataces hebreos se quejan a Faraón y a Moisés; Moisés clama a Dios, que promete actuar contra Faraón.", S1),
    ("6:2", "6:13", "Dios renueva su promesa", "Dios recuerda su pacto con Abraham, Isaac y Jacob y promete libertar a Israel; el pueblo no escucha a Moisés.", S1),
    ("6:14", "6:30", "La genealogía de Moisés y Aarón", "Lista de las familias de Rubén, Simeón y Leví hasta Aarón, Moisés y Finees, con las edades de Leví, Coat y Amram.", S1),
    ("7:1", "7:13", "La vara de Aarón ante Faraón", "Dios envía a Moisés (80 años) y Aarón (83) ante Faraón; la vara de Aarón se vuelve culebra y devora las de los magos.", S2),
    ("7:14", "7:25", "Primera plaga: el agua en sangre", "Aarón extiende la vara sobre las aguas de Egipto y se convierten en sangre; Faraón no escucha.", S2),
    ("8:1", "8:15", "Segunda plaga: las ranas", "Las ranas cubren Egipto; Faraón pide que se quiten y, cuando cesan, endurece su corazón.", S2),
    ("8:16", "8:32", "Tercera y cuarta plagas: piojos y moscas", "El polvo se vuelve piojos y vienen enjambres de moscas, pero no en Gosén; Faraón cede y luego se vuelve atrás.", S2),
    ("9:1", "9:12", "Quinta y sexta plagas: el ganado y las úlceras", "Muere el ganado de Egipto pero no el de Israel; luego vienen úlceras sobre hombres y animales.", S2),
    ("9:13", "9:26", "Séptima plaga: el granizo", "Dios anuncia y envía un granizo con fuego sobre Egipto; en la tierra de Gosén no cae.", S2),
    ("9:27", "9:35", "Faraón promete y se vuelve atrás", "Faraón reconoce su pecado y pide que cese el granizo; cuando cesa, vuelve a endurecerse.", S2),
    ("10:1", "10:20", "Octava plaga: las langostas", "Las langostas devoran lo que dejó el granizo; un viento las echa al mar Bermejo.", S2),
    ("10:21", "10:29", "Novena plaga: las tinieblas", "Tres días de tinieblas cubren Egipto; Faraón despide a Moisés sin dejar ir al ganado.", S2),
    ("11:1", "11:10", "Anuncio de la muerte de los primogénitos", "Dios anuncia la última plaga: morirá todo primogénito en la tierra de Egipto.", S2),
    ("12:1", "12:20", "La Pascua y los panes sin levadura", "Dios ordena el cordero de la Pascua, la sangre en los postes y la fiesta de los panes sin levadura.", S2),
    ("12:21", "12:36", "La noche de la Pascua", "Moisés instruye a los ancianos; a medianoche mueren los primogénitos de Egipto y Faraón deja ir al pueblo.", S2),
    ("12:37", "12:51", "La salida de Egipto", "Israel parte de Ramesés a Sucot al cumplirse los 430 años; normas sobre quién puede comer la Pascua.", S2),
    ("13:1", "13:16", "Los primogénitos y la fiesta de los ázimos", "Dios manda consagrarle los primogénitos y celebrar cada año los panes sin levadura.", S2),
    ("13:17", "14:9", "La columna de nube y Faraón persigue", "Dios guía al pueblo por el desierto con columnas de nube y de fuego; Faraón sale tras ellos con sus carros.", S3),
    ("14:10", "14:20", "El pueblo teme junto al mar", "Los israelitas se asustan al ver a los egipcios; Moisés los anima y la nube se pone entre los dos campamentos.", S3),
    ("14:21", "14:31", "El paso del mar", "Las aguas se abren y el pueblo pasa en seco; las aguas vuelven y cubren a los egipcios.", S3),
    ("15:1", "15:21", "El cántico de Moisés y de Miriam", "Moisés e Israel cantan a Dios por la victoria en el mar; Miriam y las mujeres responden con panderos.", S3),
    ("15:22", "15:27", "Las aguas de Mara y Elim", "En Mara las aguas amargas se endulzan con un árbol; luego acampan en Elim, junto a doce fuentes.", S3),
    ("16:1", "16:21", "Las codornices y el maná", "En el desierto de Sin el pueblo murmura; Dios envía codornices por la tarde y maná por la mañana.", S3),
    ("16:22", "16:36", "El maná y el sábado", "El sexto día recogen doble porción; el séptimo no hay maná; se guarda un gomer de maná como memoria.", S3),
    ("17:1", "17:16", "Agua de la peña y batalla contra Amalec", "En Refidim Moisés golpea la peña y sale agua; Josué vence a Amalec mientras Moisés alza las manos.", S3),
    ("18:1", "18:12", "Jetro visita a Moisés", "Jetro trae a Séfora y a sus dos hijos, escucha lo que Dios ha hecho y ofrece sacrificios.", S3),
    ("18:13", "18:27", "El consejo de Jetro", "Jetro aconseja a Moisés poner jueces sobre el pueblo; Moisés lo hace y Jetro vuelve a su tierra.", S3),
    ("19:1", "19:15", "Israel llega al Sinaí", "Al tercer mes llegan al desierto de Sinaí; Dios propone su pacto y el pueblo se prepara.", S4),
    ("19:16", "19:25", "Dios desciende sobre el monte", "Truenos, relámpagos, humo y sonido de bocina; Dios desciende sobre el monte Sinaí y llama a Moisés.", S4),
    ("20:1", "20:17", "Los diez mandamientos", "Dios pronuncia las palabras del decálogo.", S4),
    ("20:18", "20:26", "El pueblo teme; la ley del altar", "El pueblo, atemorizado, pide que Moisés hable por Dios; normas sobre el altar.", S4),
    ("21:1", "21:11", "Leyes sobre los siervos", "Normas sobre el siervo hebreo y la sierva.", S4),
    ("21:12", "21:27", "Leyes sobre la violencia contra las personas", "Penas por homicidio, golpes y heridas, y la ley del talión.", S4),
    ("21:28", "21:36", "Daños causados por animales", "Responsabilidad por el buey que acornea y por el hoyo abierto.", S4),
    ("22:1", "22:15", "Robo y daños a la propiedad", "Restitución por robo, por daños en campos y por bienes dados en depósito o prestados.", S4),
    ("22:16", "22:31", "Leyes diversas", "Normas sobre la doncella seducida, la hechicería, el extranjero, la viuda, el préstamo y las primicias.", S4),
    ("23:1", "23:19", "Justicia, año sabático y fiestas", "Normas sobre el testimonio y la justicia, el año séptimo, el sábado y las tres fiestas anuales.", S4),
    ("23:20", "23:33", "El ángel y la promesa de la tierra", "Dios promete enviar un ángel delante del pueblo y echar a los pueblos de la tierra poco a poco.", S4),
    ("24:1", "24:18", "Se confirma el pacto", "Moisés lee el libro del pacto y rocía la sangre; los ancianos ven a Dios y Moisés sube al monte cuarenta días.", S4),
    ("25:1", "25:22", "La ofrenda y el arca del testimonio", "Dios pide una ofrenda para el santuario y da las medidas del arca y del propiciatorio.", S5),
    ("25:23", "25:40", "La mesa y el candelero", "Instrucciones para la mesa de los panes y el candelero de oro.", S5),
    ("26:1", "26:14", "Las cortinas del tabernáculo", "Instrucciones para las cortinas de lino y de pelo de cabra y las cubiertas.", S5),
    ("26:15", "26:37", "Las tablas y el velo", "Instrucciones para las tablas, las barras, el velo y la cortina de la entrada.", S5),
    ("27:1", "27:21", "El altar, el atrio y el aceite", "Instrucciones para el altar del holocausto, el atrio y el aceite de la lámpara.", S5),
    ("28:1", "28:14", "Las vestiduras sacerdotales: el efod", "Dios aparta a Aarón y a sus hijos para el sacerdocio y manda hacer el efod.", S5),
    ("28:15", "28:30", "El pectoral del juicio", "Instrucciones para el pectoral con doce piedras, el Urim y el Tumim.", S5),
    ("28:31", "28:43", "El manto, la lámina y las túnicas", "Instrucciones para el manto, la lámina de oro, la mitra y las túnicas.", S5),
    ("29:1", "29:21", "La consagración de los sacerdotes", "Ritual de consagración de Aarón y sus hijos con sacrificios y unción.", S5),
    ("29:22", "29:37", "El carnero de las consagraciones", "Porciones del carnero de las consagraciones y siete días de consagración del altar.", S5),
    ("29:38", "29:46", "El holocausto continuo", "Dos corderos cada día; Dios promete habitar en medio de Israel.", S5),
    ("30:1", "30:16", "El altar del incienso y el rescate", "Instrucciones para el altar del incienso y el medio siclo de rescate en el censo.", S5),
    ("30:17", "30:38", "La fuente, el aceite de la unción y el incienso", "Instrucciones para la fuente de bronce, el aceite santo de la unción y el incienso.", S5),
    ("31:1", "31:18", "Bezaleel y Aholiab; el sábado", "Dios llama a Bezaleel y Aholiab para la obra, manda guardar el sábado y da a Moisés las tablas.", S5),
    ("32:1", "32:14", "El becerro de oro", "El pueblo pide dioses, Aarón hace un becerro de oro y Moisés intercede por el pueblo.", S6),
    ("32:15", "32:35", "Moisés rompe las tablas", "Moisés baja, rompe las tablas y quema el becerro; los levitas castigan al pueblo y Moisés vuelve a interceder.", S6),
    ("33:1", "33:11", "El tabernáculo fuera del campamento", "Dios manda partir hacia la tierra; Moisés habla con Dios en el tabernáculo del testimonio, fuera del campo.", S6),
    ("33:12", "33:23", "Moisés pide ver la gloria de Dios", "Moisés pide que Dios vaya con el pueblo y ver su gloria; Dios lo pone en una hendidura de la peña.", S6),
    ("34:1", "34:9", "Nuevas tablas y el nombre de Jehová", "Moisés labra dos tablas nuevas; Dios pasa ante él proclamando su nombre.", S6),
    ("34:10", "34:28", "La renovación del pacto", "Dios renueva el pacto con mandatos sobre la idolatría y las fiestas; Moisés escribe las palabras.", S6),
    ("34:29", "34:35", "El rostro de Moisés resplandece", "Moisés baja del monte con el rostro resplandeciente y se cubre con un velo.", S6),
    ("35:1", "35:19", "El sábado y la ofrenda para el tabernáculo", "Moisés recuerda el sábado y pide ofrendas y artífices para la obra.", S7),
    ("35:20", "35:35", "El pueblo trae ofrendas", "Hombres y mujeres traen ofrendas voluntarias; Moisés presenta a Bezaleel y Aholiab.", S7),
    ("36:1", "36:19", "La ofrenda sobrante y las cortinas", "El pueblo trae más de lo necesario; los artífices hacen las cortinas y las cubiertas.", S7),
    ("36:20", "36:38", "Las tablas, el velo y la cortina", "Se hacen las tablas, las barras, el velo y la cortina de la entrada.", S7),
    ("37:1", "37:16", "El arca y la mesa", "Bezaleel hace el arca, el propiciatorio con los querubines y la mesa.", S7),
    ("37:17", "37:29", "El candelero y el altar del incienso", "Se hacen el candelero, el altar del incienso, el aceite y el incienso.", S7),
    ("38:1", "38:20", "El altar, la fuente y el atrio", "Se hacen el altar del holocausto, la fuente de bronce y el atrio.", S7),
    ("38:21", "38:31", "La cuenta de los metales", "Cuenta del oro, la plata y el bronce empleados en el tabernáculo.", S7),
    ("39:1", "39:21", "El efod y el pectoral", "Se hacen las vestiduras sacerdotales: el efod y el pectoral.", S7),
    ("39:22", "39:43", "Las demás vestiduras; Moisés revisa la obra", "Se hacen el manto, las túnicas y la lámina; Moisés ve la obra terminada y bendice al pueblo.", S7),
    ("40:1", "40:16", "La orden de erigir el tabernáculo", "Dios manda erigir el tabernáculo el primer día del primer mes y ungir a Aarón y a sus hijos.", S7),
    ("40:17", "40:38", "Se erige el tabernáculo; la nube lo cubre", "Moisés erige el tabernáculo en el segundo año; la nube lo cubre y la gloria de Jehová lo llena.", S7),
]

# Lugares de OpenBible en Éxodo: obid -> (id, nombre, formas RV1909 o None = detectar, tipo, nota, forzar confianza baja)
_BAJA_SINAI = ("No hay consenso sobre la ubicación del monte Sinaí/Horeb: OpenBible propone varias identificaciones "
               "(Jebel Musa, Har Karkom…). Se fija confianza baja aunque la puntuación de OpenBible sea {p}.")
LUGARES = {  # el orden importa: el desierto de Sinaí se asigna antes que el monte (Ex 19:2)
    "a3870fe": ("piton", "Pitón", None, "ciudad", "", False),
    "aa28709": ("sucot-egipto", "Sucot", None, "campamento", "Distinta de Sucot de Gn 33:17 (al oriente del Jordán).", False),
    "a27d0e0": ("etam", "Etam", None, "campamento", "", False),
    "ababfd2": ("pi-hahirot", "Pi-hahirot", None, "campamento", "", False),
    "a22663b": ("baal-zefon", "Baal-zefón", None, "campamento", "", False),
    "a411283": ("migdol", "Migdol", None, "campamento", "", False),
    "a3d18b2": ("mar-rojo", "Mar Rojo", ["mar Bermejo"], "mar",
                "La RV1909 dice «mar Bermejo» (en hebreo yam suf). OpenBible separa el «mar Rojo» del paso (Ex 13–15) "
                "de los de Ex 10:19 y Ex 23:31, con identificaciones distintas.", False),
    "a3ba698": ("mar-rojo-plaga", "Mar Rojo (Ex 10:19)", ["mar Bermejo"], "mar",
                "Donde el viento echa las langostas (Ex 10:19); identificación propia de OpenBible.", False),
    "ad64d75": ("mar-rojo-limite", "Mar Rojo (límite, Ex 23:31)", ["mar Bermejo"], "mar",
                "Límite de la tierra prometida (Ex 23:31); OpenBible lo identifica con el golfo de Áqaba.", False),
    "ad3970d": ("mara", "Mara", ["Mara"], "fuente", "", False),
    "a2410c1": ("elim", "Elim", None, "campamento", "", False),
    "a0f54e4": ("desierto-de-sin", "Desierto de Sin", ["Sin"], "region", "", False),
    "a05ebb7": ("refidim", "Refidim", None, "campamento", "", False),
    "a296e06": ("masah", "Masah", None, "campamento", "Nombre que Moisés da al lugar de Refidim (Ex 17:7).", False),
    "a65db0f": ("meriba", "Meriba", None, "campamento", "Nombre que Moisés da al lugar de Refidim (Ex 17:7).", False),
    "ab95484": ("amalec", "Amalec", None, "region",
                "En Éxodo «Amalec» es el pueblo amalecita (Ex 17:8-16); OpenBible lo registra como región.", False),
    "ae50cf1": ("desierto-de-sinai", "Desierto de Sinaí", ["Sinaí"], "region", _BAJA_SINAI, True),
    "abfba2a": ("sinai", "Monte Sinaí", ["Sinaí"], "monte", _BAJA_SINAI, True),
    "a9bb03e": ("horeb", "Horeb", ["Horeb"], "monte", "«Monte de Dios» (Ex 3:1). " + _BAJA_SINAI, True),
}
OBLIGATORIOS_LUGAR = ["gosen", "rameses", "piton", "madian", "sucot-egipto", "etam", "pi-hahirot", "mar-rojo", "mara",
                      "elim", "desierto-de-sin", "refidim", "sinai"]


def ex(ref):
    return f"Ex {ref[0]}:{ref[1]}"


def parse_ex(s):
    m = re.match(r"Ex (\d+):(\d+)$", s)
    return (int(m.group(1)), int(m.group(2)))


ORDEN_LIBRO = {"Gn": 0, "Ex": 1, "Lv": 2, "Nm": 3, "Dt": 4, "Jos": 5, "Jue": 6, "Rut": 7, "1S": 8, "2S": 9, "1R": 10}


def parse_ref(s):
    """«Lv 10:1» -> (10, 1), para cualquier libro."""
    m = re.match(r"\w+ (\d+):(\d+)$", s)
    return (int(m.group(1)), int(m.group(2)))


def clave_ref(s):
    m = re.match(r"(\w+) (\d+):(\d+)", s)
    return (ORDEN_LIBRO.get(m.group(1), 99), int(m.group(2)), int(m.group(3)))


def _u16(s, i):
    return len(s[:i].encode("utf-16-le")) // 2


def _numeral_regex(ES, EN):
    pal_es = sorted(set(ES) | {"mil", "veintiún", "dieciséis", "veintidós", "veintitrés", "veintiséis"}, key=len, reverse=True)
    pal_en = sorted(set(EN) | {"hundred", "thousand"}, key=len, reverse=True)
    n_es, n_en = "(?:%s)" % "|".join(pal_es), "(?:%s)" % "|".join(pal_en)
    return {"es": re.compile(r"\b%s(?:(?:\s+y)?\s+%s)*(?:\s+años)?\b" % (n_es, n_es), re.I),
            "en": re.compile(r"\b(?:(?:a|an)\s+)?%s(?:(?:\s+and\s+|\s+|-)%s)*(?:\s+years)?\b" % (n_en, n_en), re.I)}


def construir(cx, cfg=None):
    """cx: rv, br (Éxodo, {(c, v): texto}), rels, pv_filas, per, personas, relaciones, edades (de Génesis,
    se amplían), sin_acentos, numeral, ES, EN, errores, avisos. Devuelve un dict con lo propio del libro.
    cfg: módulo con la configuración del libro (por defecto este, Éxodo; Levítico usa herramientas/levitico.py)."""
    cfg = cfg or sys.modules[__name__]
    L, NOMBRE, USX, CAPS = cfg.LIBRO, cfg.NOMBRE, cfg.USX, cfg.CAPITULOS
    EXCLUIR = cfg.EXCLUIR
    SOLO_ETIQUETA = cfg.SOLO_ETIQUETA
    FORMA_NO_MENCION = cfg.FORMA_NO_MENCION
    PV_DESCARTAR = cfg.PV_DESCARTAR
    FORMAS_FORZADAS = cfg.FORMAS_FORZADAS
    MODERNO = cfg.MODERNO
    NOTAS = cfg.NOTAS
    IDENTIDAD = cfg.IDENTIDAD
    NOTAS_VERIFICAR = cfg.NOTAS_VERIFICAR
    ROLES = cfg.ROLES
    SIN_NOMBRE = cfg.SIN_NOMBRE
    RELACIONES = cfg.RELACIONES
    NOTAS_REL = cfg.NOTAS_REL
    REPITE_GN = cfg.REPITE_GN
    EDADES = cfg.EDADES
    PASAJES = cfg.PASAJES
    NOTAS_EXISTENTES = getattr(cfg, "NOTAS_EXISTENTES", {})  # nota que se añade a una persona ya existente
    REFS_EXTRA = getattr(cfg, "REFS_EXTRA", {})  # refs que el texto da a una persona sin nombrarla
    REL_DESCARTAR = getattr(cfg, "REL_DESCARTAR", {})  # (de, a, tipo) de BibleData que no se usan -> motivo
    remap = getattr(cfg, "REMAP_REF", lambda r: r)  # versificación de BibleData/OpenBible (inglesa) -> RV1909
    ex = lambda r: f"{L} {r[0]}:{r[1]}"  # noqa: E731
    parse_ex = parse_ref
    rv, br, sa = cx["rv"], cx["br"], cx["sin_acentos"]
    errores, avisos, per = cx["errores"], cx["avisos"], cx["per"]
    personas, relaciones, edades = cx["personas"], cx["relaciones"], cx["edades"]
    P = {p["id"]: p for p in personas}
    textos = {"TM": rv, "LXX": br}

    def nombra(verso, forma):
        return re.search(r"(?<!\w)%s(?!\w)" % re.escape(sa(forma)), sa(verso))

    # ------------------------------------------------ capítulos
    capitulos = []
    for c in range(1, CAPS + 1):
        vs = sorted(v for (cc, v) in rv if cc == c)
        if not vs or vs != list(range(1, len(vs) + 1)):
            errores.append(f"{L} {c}: numeración de versículos no continua o vacía")
        capitulos.append({"libro": L, "cap": c, "versiculos": [{"n": v, "texto": rv[(c, v)]} for v in vs]})

    # ------------------------------------------------ personas de BibleData en Éxodo
    valido = lambda p: re.match(r".+_\d+$", p) and p not in EXCLUIR
    refs_pv, pv_cuenta, auto = defaultdict(set), defaultdict(dict), defaultdict(Counter)
    for r in cx["pv_filas"]:
        p = r["person_id"]
        if not valido(p) or (p in SOLO_ETIQUETA and r["person_label"] not in SOLO_ETIQUETA[p]):
            continue
        ref = remap(tuple(map(int, r["reference_id"][4:].split(":"))))
        if (p, ref) in PV_DESCARTAR:
            avisos.append(f"{NOMBRE}: se descarta {p} en {ex(ref)}: {PV_DESCARTAR[(p, ref)]}")
            continue
        refs_pv[p].add(ref)
        try:
            n = int(r["person_label_count"] or 1)
        except ValueError:
            n = 1
        pv_cuenta[ref][p] = pv_cuenta[ref].get(p, 0) + n
        f, _ = na.mejor_forma(r["person_label"], rv.get(ref, ""))
        if f and not f.isupper():
            auto[p][f] += 1
    FORMAS = {p: [w for w, _ in c.most_common()] for p, c in auto.items()}
    FORMAS.update(FORMAS_FORZADAS)

    def formas_de(p):
        fs = list(P[p]["formas_rv1909"]) if p in P else []
        for f in FORMAS.get(p, []):
            if sa(f) not in {sa(x) for x in fs}:
                fs.append(f)
        return fs

    # ------------------------------------------------ relaciones
    claves_gn = {(x["de"], x["a"], x["tipo"]) for x in relaciones}
    cand, descartadas = {}, Counter()
    for r in cx["rels"]:
        refs = [x.strip() for x in r["reference_id"].split(",")]
        exo = [x for x in refs if x.startswith(USX + " ")]
        if not exo:
            continue
        ref = remap(tuple(map(int, exo[0][4:].split(":"))))
        p1, t, p2 = r["person_id_1"], r["relationship_type"].strip().lower(), r["person_id_2"]
        if not (valido(p1) and valido(p2)):
            continue
        sexo2 = per.get(p2, {}).get("sex", "")
        if t == "father":
            de, a, tipo = p1, p2, "padre"
        elif t == "mother":
            de, a, tipo = p1, p2, "madre"
        elif t in ("son", "daughter"):
            de, a, tipo = p2, p1, ("madre" if sexo2 == "female" else "padre")
        elif t in ("husband", "wife"):
            (de, a), tipo = sorted((p1, p2)), "conyuge"
        else:
            descartadas[t] += 1
            continue
        k = (de, a, tipo)
        if k in claves_gn:
            continue
        if k in REL_DESCARTAR:
            if k not in cand:
                avisos.append(f"{NOMBRE}: se descarta la relación de BibleData {de}→{a} {tipo}: {REL_DESCARTAR[k]}")
            cand[k] = None
            continue
        nuevo = {"de": de, "a": a, "tipo": tipo, "ref": ex(ref),
                 "certeza": "explicito" if r["relationship_category"].strip() == "explicit" else "inferido",
                 "fuente": "bibledata", "nota": r["relationship_notes"].strip()}
        viejo = cand.get(k)
        rank = lambda x: (x["certeza"] != "explicito", parse_ex(x["ref"]))
        if viejo is None or rank(nuevo) < rank(viejo):
            if viejo and not nuevo["nota"]:
                nuevo["nota"] = viejo["nota"]
            cand[k] = nuevo
    cand = {k: x for k, x in cand.items() if x is not None}
    subidas = 0
    for x in cand.values():
        if x["certeza"] == "inferido" and x["tipo"] in ("padre", "madre"):
            v = rv.get(parse_ex(x["ref"]), "")
            if (any(nombra(v, f) for f in formas_de(x["de"])) and any(nombra(v, f) for f in formas_de(x["a"]))
                    and re.search(r"engendr|pari[oó]", sa(v))):
                subidas += 1
                x.update(certeza="explicito", fuente="rv1909",
                         nota=(x["nota"] + " " if x["nota"] else "") + "BibleData la marca inferida; el versículo nombra a ambos.")
    for k, nota in NOTAS_REL.items():
        if k in cand:
            cand[k]["nota"] = (cand[k]["nota"] + " " + nota).strip()
    sin_nombre = {}
    for pid, (nombre, sexo, nota, rs) in SIN_NOMBRE.items():
        sin_nombre[pid] = (nombre, sexo, nota)
        for de, a, tipo, ref, cert, cita in rs:
            if tipo == "conyuge":
                de, a = sorted((de, a))
            cand[(de, a, tipo)] = {"de": de, "a": a, "tipo": tipo, "ref": ex(ref), "certeza": cert,
                                   "fuente": "rv1909", "nota": "", "cita": cita}
    for de, a, tipo, ref, cita, nota in RELACIONES:
        if tipo == "conyuge":
            de, a = sorted((de, a))
        previo = cand.get((de, a, tipo))
        cand[(de, a, tipo)] = {"de": de, "a": a, "tipo": tipo, "ref": ex(ref), "certeza": "explicito",
                               "fuente": "rv1909", "nota": nota or (previo or {}).get("nota", ""), "cita": cita}
    for de, a, tipo, ref, cita in REPITE_GN:
        g = next((x for x in relaciones if (x["de"], x["a"], x["tipo"]) == (de, a, tipo)), None)
        if not g:
            errores.append(f"Falta en los libros anteriores la relación {de}→{a} que repite {ex(ref)}")
            continue
        if cita not in rv.get(ref, ""):
            errores.append(f"Cita no literal {ex(ref)}: {cita!r}")
        extra = f"También {ex(ref)}: «{cita}»."
        if extra not in g["nota"]:
            g["nota"] = (g["nota"] + " " + extra).strip()
    rel_ex = sorted(cand.values(), key=lambda x: (parse_ex(x["ref"]), x["de"], x["a"]))
    for x in rel_ex:
        if x.get("cita") and x["cita"] not in rv.get(parse_ex(x["ref"]), ""):
            errores.append(f"Cita de relación no literal: {x['de']}→{x['a']} {x['ref']} {x['cita']!r}")

    # ------------------------------------------------ edades (TM de RV1909 y LXX de Brenton)
    NUM = _numeral_regex(cx["ES"], cx["EN"])
    ed_ex = []
    for p, tipo, ref, i_tm, i_lxx, evento in EDADES:
        par = {}
        for trad, idioma, fuente, idx in (("TM", "es", "rv1909", i_tm), ("LXX", "en", "brenton", i_lxx)):
            verso = textos[trad].get(ref, "")
            hallados = [m.group(0) for m in NUM[idioma].finditer(verso)]
            if idx >= len(hallados):
                errores.append(f"{p} {trad} {ex(ref)}: no hay cifra n.º {idx}")
                continue
            cita = hallados[idx]
            valor = cx["numeral"](re.sub(r"\s+(años|years)$", "", cita, flags=re.I), idioma)
            e = {"persona": p, "tipo": tipo, "tradicion": trad, "valor": valor, "ref": ex(ref), "certeza": "texto",
                 "fuente": fuente, "cita": cita, "nota": ""}
            if tipo == "en_evento":
                e["evento"] = evento
            par[trad] = e
            ed_ex.append(e)
        if len(par) == 2 and par["TM"]["valor"] != par["LXX"]["valor"]:
            par["TM"]["nota"] = f"La LXX (Brenton) da {par['LXX']['valor']} («{par['LXX']['cita']}»)."
            par["LXX"]["nota"] = f"El TM (RV1909) da {par['TM']['valor']} («{par['TM']['cita']}»)."
    for e in ed_ex:
        verso = textos[e["tradicion"]].get(parse_ex(e["ref"]), "")
        if e["cita"] not in verso:
            errores.append(f"Cita de edad no literal: {e['persona']} {e['ref']} {e['cita']!r}")
        idioma = "es" if e["tradicion"] == "TM" else "en"
        if cx["numeral"](re.sub(r"\s+(años|years)$", "", e["cita"], flags=re.I), idioma) != e["valor"]:
            errores.append(f"Cifra ≠ cita: {e['persona']} {e['ref']}")
    edades.extend(ed_ex)

    # ------------------------------------------------ personas (nuevas y ampliadas)
    refs = defaultdict(set)
    for p, rs in refs_pv.items():
        refs[p] |= rs
    for x in rel_ex:
        refs[x["de"]].add(parse_ex(x["ref"])); refs[x["a"]].add(parse_ex(x["ref"]))
    for e in ed_ex:
        refs[e["persona"]].add(parse_ex(e["ref"]))
    for p, (_, rref, _) in ROLES.items():
        refs[p].add(rref)
    for p, rs in REFS_EXTRA.items():
        refs[p] |= set(rs)
    for p, rs in getattr(cfg, "REFS_QUITAR", {}).items():  # refs de BibleData que son de otra persona
        faltan = set(rs) - refs[p]
        if faltan:
            errores.append(f"REFS_QUITAR de {p}: {sorted(faltan)} no están en sus refs")
        refs[p] -= set(rs)
    for trad, ref, frag in NOTAS_VERIFICAR:
        if frag not in textos[trad].get(ref, ""):
            errores.append(f"Nota sin base: «{frag}» no está en {ex(ref)} ({trad})")
    for p, (rol, rref, rcita) in ROLES.items():
        if rcita not in rv.get(rref, ""):
            errores.append(f"Rol de {p}: «{rcita}» no está en {ex(rref)}")
    nuevas, ampliadas, fallos_nombre = [], [], []
    for p in sorted(refs, key=lambda q: (min(refs[q]), q)):
        lista = sorted(refs[p])
        if p in P:  # persona de Génesis: misma persona, se amplían refs y formas
            g = P[p]
            fs = formas_de(p)
            nuevas_f = [f for f in fs if f not in g["formas_rv1909"]]
            if nuevas_f and not g["sin_nombre"]:
                g["formas_rv1909"] = fs
                g["nota"] = (g["nota"] + " " + f"En {NOMBRE} la RV1909 escribe también «{'/'.join(nuevas_f)}».").strip()
            g["refs"] = sorted(set(g["refs"]) | {ex(r) for r in lista}, key=clave_ref)
            if p in NOTAS_EXISTENTES and NOTAS_EXISTENTES[p] not in g["nota"]:
                g["nota"] = (g["nota"] + " " + NOTAS_EXISTENTES[p]).strip()
            if p in IDENTIDAD and "identidad" not in g:  # identificación que aparece en este libro
                g["identidad"] = IDENTIDAD[p]
            ampliadas.append(p)
            continue
        if p in sin_nombre:
            nombre, sexo, nota = sin_nombre[p]
            rol = ROLES.get(p, ("",))[0]
            nuevas.append({"id": p, "nombre": nombre, "nombre_rv1909": None, "formas_rv1909": [], "rol": rol,
                           "sin_nombre": True, "sexo": sexo, "primera_ref": ex(lista[0]),
                           "refs": [ex(r) for r in lista], "nota": nota, "ref_mencion": ex(lista[0])})
            continue
        fs = formas_de(p)
        if not fs:
            errores.append(f"Persona de {NOMBRE} sin forma RV1909: {p}")
            continue
        con_nombre = [r for r in lista if any(nombra(rv.get(r, ""), f) for f in fs)]
        if not con_nombre:
            fallos_nombre.append(f"{p} «{fs[0]}»")
        moderno = MODERNO.get(p)
        if not moderno:
            errores.append(f"Persona de {NOMBRE} sin grafía moderna: {p} ({fs[0]})")
            moderno = fs[0]
        nota = NOTAS.get(p, "")
        if fs[0] != moderno:
            nota = (f"En la Reina-Valera 1909: {'/'.join(fs)}. " + nota).strip()
        d = {"id": p, "nombre": moderno, "nombre_rv1909": fs[0], "rol": ROLES.get(p, ("",))[0], "formas_rv1909": fs,
             "sin_nombre": False, "sexo": {"male": "m", "female": "f"}.get(per.get(p, {}).get("sex", ""), "?"),
             "primera_ref": ex((con_nombre or lista)[0]), "refs": [ex(r) for r in lista], "nota": nota}
        if p in IDENTIDAD:
            d["identidad"] = IDENTIDAD[p]
        nuevas.append(d)
    personas.extend(nuevas)
    P = {p["id"]: p for p in personas}
    for p in IDENTIDAD:
        if p not in P or "identidad" not in P[p]:
            errores.append(f"Falta la identificación inferida de {p}")
    for x in rel_ex:
        for q in (x["de"], x["a"]):
            if q not in P:
                errores.append(f"Relación de {NOMBRE} a persona inexistente: {q}")
    relaciones.extend(rel_ex)
    # padres sin vínculo conyugal (Éxodo)
    conyuges = {tuple(sorted((x["de"], x["a"]))) for x in relaciones if x["tipo"] == "conyuge"}
    pm = defaultdict(lambda: {"padre": set(), "madre": set()})
    for x in rel_ex:
        if x["tipo"] in ("padre", "madre"):
            pm[x["a"]][x["tipo"]].add(x["de"])
    for hijo, d in pm.items():
        for pa in d["padre"]:
            for ma in d["madre"]:
                if tuple(sorted((pa, ma))) not in conyuges:
                    errores.append(f"{NOMBRE}: padres sin vínculo conyugal: {pa} + {ma} → {hijo}")
    con_rel = {q for x in relaciones for q in (x["de"], x["a"])}
    for p in nuevas:
        if p["id"] not in con_rel and not p["rol"]:
            errores.append(f"Persona de {NOMBRE} sin relación ni rol: {p['id']}")

    # ------------------------------------------------ pasajes
    orden = sorted(rv)
    pos = {k: i for i, k in enumerate(orden)}
    pasajes, esperado, tam = [], 0, []
    for i, (ini, fin, titulo, resumen, seccion) in enumerate(PASAJES, 1):
        a, b = tuple(map(int, ini.split(":"))), tuple(map(int, fin.split(":")))
        if a not in pos or b not in pos or pos[a] != esperado or pos[b] < pos[a]:
            errores.append(f"Pasaje {L} {ini}–{fin}: hueco, solape o desorden")
        else:
            esperado = pos[b] + 1
        pasajes.append({"id": f"{L.lower()}-{i:02d}", "libro": L, "inicio": ex(a), "fin": ex(b), "titulo": titulo,
                        "titulo_origen": "editorial", "resumen": resumen, "seccion": seccion})
        tam.append(pos.get(b, 0) - pos.get(a, 0) + 1)
    if esperado != len(orden):
        errores.append(f"Los pasajes de {NOMBRE} no cubren hasta {ex(orden[-1])}")

    # ------------------------------------------------ menciones de personas
    por_forma = defaultdict(list)
    for p in personas:
        for f in p["formas_rv1909"]:
            if (p["id"], sa(f)) not in FORMA_NO_MENCION:
                por_forma[sa(f)].append(p["id"])
    sitio = {p["id"]: {r for r in p["refs"] if r.startswith(L + " ")} for p in personas}
    formas = sorted(por_forma, key=len, reverse=True)
    menciones, ambiguos, no_situados = [], [], Counter()
    for ref in orden:
        texto, R = rv[ref], ex(ref)
        norm = "".join(n if len(n := sa(ch)) == 1 else ch.lower() for ch in texto)
        if len(norm) != len(texto):
            errores.append(f"Normalización altera longitud en {R}"); continue
        ocupado = [False] * len(texto)
        for forma in formas:
            hallados = [m for m in re.finditer(r"(?<!\w)%s(?!\w)" % re.escape(forma), norm)
                        if not any(ocupado[m.start():m.end()]) and texto[m.start()].isupper()]
            if not hallados:
                continue
            cands = list(dict.fromkeys(q for q in por_forma[forma] if q in pv_cuenta[ref] or R in sitio[q]))
            if not cands:
                no_situados[forma] += len(hallados); continue
            if len(cands) > 1:
                ambiguos.append(f"{R} «{texto[hallados[0].start():hallados[0].end()]}» ×{len(hallados)} {cands}")
                continue
            for m in hallados:
                for j in range(m.start(), m.end()):
                    ocupado[j] = True
                menciones.append({"ref": R, "persona": cands[0], "inicio": _u16(texto, m.start()), "fin": _u16(texto, m.end())})
    menciones.sort(key=lambda x: (parse_ex(x["ref"]), x["inicio"]))
    forma_de = {p["id"]: {sa(f) for f in p["formas_rv1909"]} for p in personas}
    for x in menciones:
        t = rv[parse_ex(x["ref"])]
        b = t.encode("utf-16-le")[2 * x["inicio"]:2 * x["fin"]].decode("utf-16-le")
        if sa(b) not in forma_de[x["persona"]]:
            errores.append(f"Mención de {NOMBRE} no coincide {x}: {b!r}")
    for p in nuevas:
        if not p["sin_nombre"] and not any(m["persona"] == p["id"] for m in menciones):
            avisos.append(f"Persona de {NOMBRE} sin menciones en el texto: {p['id']}")
    if fallos_nombre:
        avisos.append(f"{NOMBRE}, nombre no hallado en ninguna ref: " + ", ".join(fallos_nombre))

    return {"capitulos": capitulos, "pasajes": pasajes, "menciones": menciones, "relaciones": rel_ex,
            "edades": ed_ex, "nuevas": nuevas, "ampliadas": ampliadas, "ambiguos": ambiguos,
            "no_situados": no_situados, "subidas": subidas, "descartadas": dict(descartadas), "tam_pasaje": tam}


# ---------------------------------------------------------------- lugares
def construir_lugares(rv, menciones_personas, rutas, lugares_gn, errores, avisos, sa, cfg=None):
    """Amplía los lugares de los libros anteriores con refs de este libro y añade los propios.
    cfg: módulo del libro (por defecto Éxodo). Devuelve (nuevos, menciones, info)."""
    cfg = cfg or sys.modules[__name__]
    L, NOMBRE, USX, LUGARES = cfg.LIBRO, cfg.NOMBRE, cfg.USX, cfg.LUGARES
    EXCLUIR_LUGAR = getattr(cfg, "EXCLUIR_LUGAR", {})  # obid -> motivo (aviso)
    PRECEDIDO = getattr(cfg, "PRECEDIDO", {})  # obid -> texto que debe preceder al nombre
    remap = getattr(cfg, "REMAP_REF", lambda r: r)  # versificación de OpenBible (inglesa) -> RV1909
    ex = lambda r: f"{L} {r[0]}:{r[1]}"  # noqa: E731
    parse_ex = parse_ref
    anc = {}
    with open(rutas["ob_ancient"], encoding="utf-8") as f:
        for n, linea in enumerate(f, 1):
            d = json.loads(linea)
            if any(v["usx"].startswith(USX + " ") for v in d.get("verses", [])):
                anc[d["id"]] = (n, d)
    for obid, motivo in EXCLUIR_LUGAR.items():
        if anc.pop(obid, None):
            avisos.append(f"{NOMBRE}: no se incluye el lugar de OpenBible {obid}: {motivo}")
    mod_ids = set()
    for _, d in anc.values():
        mod_ids |= set(d.get("modern_associations", {}))
    mod = lm._leer_jsonl(rutas["ob_modern"], mod_ids)
    gn_por_ob = {l["url_fuente"].split("/ancient/")[1].split("/")[0]: l for l in lugares_gn
                 if "/ancient/" in (l.get("url_fuente") or "")}  # Judá (Rut) no es de OpenBible
    # obid de OpenBible que es el mismo lugar que uno ya registrado con otro obid (amplía ese lugar)
    por_lid = {l["id"]: l for l in lugares_gn}
    for obid, lid in getattr(cfg, "UNIR_LUGAR", {}).items():
        if lid not in por_lid:
            errores.append(f"{NOMBRE}: UNIR_LUGAR {obid} -> {lid}: no existe ese lugar"); continue
        gn_por_ob[obid] = por_lid[lid]
        avisos.append(f"{NOMBRE}: el lugar de OpenBible {obid} se une a «{lid}» (misma identificación moderna)")
    ocupado = defaultdict(list)
    for m in menciones_personas:
        ocupado[m["ref"]].append((m["inicio"], m["fin"]))
    orden_ob = list(LUGARES) + [o for o in sorted(anc, key=lambda o: anc[o][0]) if o not in LUGARES]
    nuevos, menciones, sin_forma, descartadas = [], [], [], []
    ids = {l["id"] for l in lugares_gn}
    for obid in orden_ob:
        if obid not in anc:
            errores.append(f"OpenBible no tiene {obid}"); continue
        _, d = anc[obid]
        vs = sorted({remap(tuple(map(int, v["usx"][4:].split(":")))) for v in d["verses"] if v["usx"].startswith(USX + " ")})
        conf = LUGARES.get(obid)
        if conf and conf[2]:
            formas = conf[2]
        else:
            nombres_en = d.get("translation_name_counts") or {d["friendly_id"]: 1}
            ingles = max(nombres_en.items(), key=lambda x: x[1])[0]
            cuenta = Counter()
            for r in vs:
                fm, _ = na.mejor_forma(ingles, rv.get(r, ""))
                if fm:
                    cuenta[fm] += 1
            formas = [fm for fm, _ in cuenta.most_common()]
        if obid in gn_por_ob:
            formas = list(dict.fromkeys(gn_por_ob[obid]["formas_rv1909"] + formas))
        if not formas:
            sin_forma.append(d["friendly_id"]); continue
        pats = []
        for fm in formas:
            mayus = [k for k, ch in enumerate(fm) if ch.isupper()]
            pats.append((re.compile(r"(?<!\w)%s(?!\w)" % re.escape(sa(fm))), mayus))
        refs = []
        for r in vs:
            texto = rv.get(r, "")
            norm = "".join(n if len(n := sa(ch)) == 1 else ch.lower() for ch in texto)
            ok = False
            for pat, mayus in pats:
                for m in pat.finditer(norm):
                    if not all(texto[m.start() + k].isupper() for k in mayus):
                        continue
                    if obid in PRECEDIDO and not norm[:m.start()].endswith(sa(PRECEDIDO[obid])):
                        continue
                    a, b = _u16(texto, m.start()), _u16(texto, m.end())
                    R = ex(r)
                    if any(a < f2 and i2 < b for i2, f2 in ocupado[R]):
                        continue
                    ok = True
                    ocupado[R].append((a, b))
                    menciones.append({"ref": R, "lugar": None, "inicio": a, "fin": b, "_ob": obid})
            if ok:
                refs.append(r)
            else:
                descartadas.append(f"{d['friendly_id']} {ex(r)}")
        if not refs:
            if conf and obid not in getattr(cfg, "LUGAR_OPCIONAL", ()):  # configurado a mano: debe aparecer
                errores.append(f"Lugar de {NOMBRE} {conf[1]}: ningún versículo contiene «{'/'.join(formas)}»")
            else:
                sin_forma.append(d["friendly_id"])
            continue
        if obid in gn_por_ob:
            l = gn_por_ob[obid]
            l["formas_rv1909"] = formas
            l["refs"] = sorted(set(l["refs"]) | {ex(r) for r in refs}, key=clave_ref)
            lid = l["id"]
        else:
            if not conf:
                errores.append(f"Lugar de OpenBible en {NOMBRE} sin configurar: {obid} {d['friendly_id']} «{formas[0]}»")
                continue
            lid, nombre, _, tipo, nota, baja = conf
            if lid in ids:
                errores.append(f"Id de lugar repetido: {lid}")
            ids.add(lid)
            cands = []
            for mid, ma in sorted(d.get("modern_associations", {}).items(), key=lambda x: -x[1]["score"]):
                if mid in mod and mod[mid][1].get("lonlat"):
                    lon, lat = map(float, mod[mid][1]["lonlat"].split(","))
                    cands.append({"identificacion": ma["name"], "lat": round(lat, 4), "lon": round(lon, 4),
                                  "puntuacion_openbible": ma["score"]})
            ubic, alts = None, cands[:3]
            if cands:
                ubic = dict(cands[0], confianza=lm.confianza(cands[0]["puntuacion_openbible"]))
                alts = cands[1:4]
                if baja:
                    nota = nota.format(p=cands[0]["puntuacion_openbible"])
                    ubic["confianza"] = "baja"
            else:
                nota = (nota + " " if nota else "") + "OpenBible no da identificación con coordenadas."
            nuevos.append({"id": lid, "nombre": nombre, "nombre_rv1909": formas[0], "formas_rv1909": formas,
                           "tipo": tipo, "refs": [ex(r) for r in refs], "ubicacion": ubic, "alternativas": alts,
                           "fuente": "openbible",
                           "url_fuente": f"https://www.openbible.info/geo/ancient/{obid}/{d.get('url_slug', '')}",
                           "nota": nota})
        for m in menciones:
            if m.get("_ob") == obid:
                m["lugar"] = lid
                del m["_ob"]
    menciones = [m for m in menciones if m["lugar"]]
    menciones.sort(key=lambda x: (parse_ex(x["ref"]), x["inicio"]))
    todos = {l["id"]: l for l in lugares_gn + nuevos}
    for m in menciones:
        t = rv[parse_ex(m["ref"])]
        frag = t.encode("utf-16-le")[2 * m["inicio"]:2 * m["fin"]].decode("utf-16-le")
        if sa(frag) not in {sa(f) for f in todos[m["lugar"]]["formas_rv1909"]}:
            errores.append(f"Mención de lugar ({NOMBRE}) no coincide: {m} {frag!r}")
    return nuevos, menciones, {"sin_forma": sin_forma, "descartadas": descartadas}


# ---------------------------------------------------------------- hechos obligatorios (sobre los datos finales)
def comprobar(datos, errores):
    """Comprueba que estén los hechos pedidos (falla si falta alguno). Devuelve líneas de informe."""
    P = {p["id"]: p for p in datos["personas"]}
    R = {}
    for x in datos["relaciones"]:
        R[(x["de"], x["a"], x["tipo"])] = x
    lineas = []

    def rel(de, a, tipo, refs, certeza="explicito"):
        k = (de, a, tipo) if tipo != "conyuge" else tuple(sorted((de, a))) + ("conyuge",)
        x = R.get(k)
        ok = bool(x) and x["ref"] in refs and x["certeza"] == certeza
        lineas.append(f"{'OK ' if ok else 'FALTA'} {de}→{a} {tipo} {refs} {certeza}"
                      + (f" (hay: {x['ref']} {x['certeza']})" if x and not ok else ""))
        if not ok:
            errores.append(f"Hecho obligatorio: {de}→{a} {tipo} en {refs} ({certeza})")

    rel("Levi_1", "Kohath_1", "padre", ["Gn 46:11", "Ex 6:16"])
    rel("Kohath_1", "Amram_1", "padre", ["Ex 6:18"])
    rel("Amram_1", "Jochebed_1", "conyuge", ["Ex 6:20"])
    for h in ("Aaron_1", "Moses_1"):
        rel("Amram_1", h, "padre", ["Ex 6:20"]); rel("Jochebed_1", h, "madre", ["Ex 6:20"])
    # Éxodo solo la llama «hermana de Aarón» (inferida); si ya está Números, Nm 26:59 lo dice (explícita).
    ref_m, cert_m = (("Nm 26:59", "explicito") if any(c["libro"] == "Nm" for c in datos["capitulos"])
                     else ("Ex 15:20", "inferido"))
    rel("Amram_1", "Miriam_1", "padre", [ref_m], cert_m)
    rel("Jochebed_1", "Miriam_1", "madre", [ref_m], cert_m)
    rel("Moses_1", "Zipporah_1", "conyuge", ["Ex 2:21"])
    rel("Moses_1", "Gershom_1", "padre", ["Ex 2:22"]); rel("Zipporah_1", "Gershom_1", "madre", ["Ex 2:22"])
    rel("Moses_1", "Eliezer_2", "padre", ["Ex 18:4"]); rel("Zipporah_1", "Eliezer_2", "madre", ["Ex 18:4"])
    rel("Reuel_2", "Zipporah_1", "padre", ["Ex 2:21"])
    rel("Aaron_1", "Elisheba_1", "conyuge", ["Ex 6:23"])
    for h in ("Nadab_1", "Abihu_1", "Eleazar_1", "Ithamar_1"):
        rel("Aaron_1", h, "padre", ["Ex 6:23"]); rel("Elisheba_1", h, "madre", ["Ex 6:23"])
    rel("Eleazar_1", "Hija_de_Putiel", "conyuge", ["Ex 6:25"])
    rel("Putiel_1", "Hija_de_Putiel", "padre", ["Ex 6:25"])
    rel("Eleazar_1", "Phinehas_1", "padre", ["Ex 6:25"]); rel("Hija_de_Putiel", "Phinehas_1", "madre", ["Ex 6:25"])
    rel("Pharaoh_3", "Hija_de_Faraon", "padre", ["Ex 2:5"])
    # Reuel/Jetro: una persona con identificación inferida y ambos versículos
    j = P.get("Reuel_2", {})
    ok = (j.get("identidad", {}).get("certeza") == "inferido" and {"Ex 2:18", "Ex 3:1"} <= set(j.get("identidad", {}).get("refs", []))
          and "Ex 2:18" in j.get("nota", "") and "Ex 3:1" in j.get("nota", ""))
    lineas.append(f"{'OK ' if ok else 'FALTA'} Reuel/Jetro: una persona, identidad inferida (Ex 2:18; Ex 3:1)")
    if not ok:
        errores.append("Hecho obligatorio: Reuel/Jetro sin nota ni identidad inferida")
    # Mujeres
    for pid, nombre, sn in (("Shiphrah_1", "Sifra", False), ("Puah_1", "Fúa", False), ("Hija_de_Faraon", None, True),
                            ("Jochebed_1", "Jocabed", False), ("Miriam_1", "Miriam", False),
                            ("Zipporah_1", "Séfora", False), ("Elisheba_1", "Elisabet", False),
                            ("Hija_de_Putiel", None, True)):
        p = P.get(pid)
        ok = bool(p) and p["sexo"] == "f" and p["sin_nombre"] == sn and (nombre is None or p["nombre"] == nombre)
        lineas.append(f"{'OK ' if ok else 'FALTA'} mujer {pid} ({p['nombre'] if p else '—'})")
        if not ok:
            errores.append(f"Hecho obligatorio: mujer {pid}")
    # Edades
    E = defaultdict(dict)
    for e in datos["edades"]:
        E[(e["persona"], e["tipo"], e["ref"])][e["tradicion"]] = e
    for p, tipo, ref, tm in (("Moses_1", "en_evento", "Ex 7:7", 80), ("Aaron_1", "en_evento", "Ex 7:7", 83),
                             ("Levi_1", "total", "Ex 6:16", 137), ("Kohath_1", "total", "Ex 6:18", 133),
                             ("Amram_1", "total", "Ex 6:20", 137)):
        d = E.get((p, tipo, ref), {})
        ok = (d.get("TM", {}).get("valor") == tm and d["TM"]["certeza"] == "texto" and "LXX" in d
              and d["LXX"]["cita"] and d["LXX"]["certeza"] == "texto")
        lxx = d.get("LXX", {}).get("valor")
        lineas.append(f"{'OK ' if ok else 'FALTA'} edad {p} {tipo} {ref}: TM {d.get('TM', {}).get('valor')} "
                      f"«{d.get('TM', {}).get('cita')}», LXX {lxx} «{d.get('LXX', {}).get('cita')}»")
        if not ok:
            errores.append(f"Hecho obligatorio: edad {p} {ref} TM {tm} (y LXX con cita)")
    # Lugares
    L = {l["id"]: l for l in datos["lugares"]}
    for lid in OBLIGATORIOS_LUGAR + ["horeb"]:
        l = L.get(lid)
        ok = bool(l) and l["ubicacion"] and l["ubicacion"].get("confianza") and "alternativas" in l \
            and any(r.startswith("Ex ") for r in l["refs"])
        if lid in ("sinai", "horeb"):
            ok = ok and l["ubicacion"]["confianza"] == "baja"
        lineas.append(f"{'OK ' if ok else 'FALTA'} lugar {lid}" + (f" ({l['nombre_rv1909']}, {l['ubicacion']['identificacion']}, "
                                                                     f"{l['ubicacion']['confianza']})" if ok else ""))
        if not ok:
            errores.append(f"Hecho obligatorio: lugar {lid} con ubicación, confianza y refs de Éxodo")
    # Esposas de Esaú sin armonizar
    for pid, ref, cita_padre in (("Judith_1", "Gn 26:34", "Beeri_1"), ("Basemath_1", "Gn 26:34", "Elon_1"),
                                 ("Mahalath_1", "Gn 28:9", "Ishmael_1"), ("Adah_2", "Gn 36:2", "Elon_1"),
                                 ("Oholibamah_esposa", "Gn 36:2", None), ("Basemath_2", "Gn 36:3", "Ishmael_1")):
        x = R.get(tuple(sorted(("Esau_1", pid))) + ("conyuge",))
        ok = bool(x) and x["ref"] == ref and pid in P
        if cita_padre:
            ok = ok and (cita_padre, pid, "padre") in R
        lineas.append(f"{'OK ' if ok else 'FALTA'} esposa de Esaú {pid} ({ref}) formas {P.get(pid, {}).get('formas_rv1909')}")
        if not ok:
            errores.append(f"Hecho obligatorio: esposa de Esaú {pid} en {ref}")
    juntos = [p["id"] for p in datos["personas"] if len({"judith", "aholibama"} & {f.lower() for f in p["formas_rv1909"]}) > 1
              or len({"mahaleth", "basemath"} & {f.lower() for f in p["formas_rv1909"]}) > 1
              or len({"basemat", "ada"} & {f.lower() for f in p["formas_rv1909"]}) > 1]
    if juntos:
        errores.append(f"Esposas de Esaú fusionadas: {juntos}")
    lineas.append(f"{'OK ' if not juntos else 'FALTA'} esposas de Esaú sin fusionar")
    return lineas
