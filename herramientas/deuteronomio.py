"""Deuteronomio 1–34: personas, relaciones, edades, pasajes, menciones y lugares (lo usa construir_datos.py).

Reutiliza la lógica de exodo.py (exodo.construir / exodo.construir_lugares con este módulo como
configuración), igual que levitico.py y numeros.py. Cada dato lleva versículo, fuente y certeza; las citas se
comprueban literalmente contra la RV1909 (TM) o Brenton (LXX). Las personas de Génesis–Números (Moisés, Aarón,
Josué, Datán y Abiram, Balaam, Og, Sehón…) son la misma persona (mismo id de BibleData): se amplían sus `refs`.

Versificación: comprobada al generar (ver `comprobar`). La RV1909 de eBible numera Deuteronomio como la
inglesa (959 versículos, ninguno vacío): Dt 12:32, 22:30 y 29:1 son versículos propios (en el hebreo son 13:1,
23:1 y 28:69) y Dt 29:2-29 coincide con la inglesa (hebreo 29:1-28). BibleData y OpenBible usan esa misma
numeración, así que no hace falta REMAP_REF. Brenton sigue la hebrea en Dt 12–13 y 22–23 (958 versículos), pero
solo se usan sus versículos de Dt 1:3, 31:2 y 34:7, que coinciden en contenido con la RV1909 (se comprueba).
Solo biblioteca estándar.
"""
import sys

import exodo

LIBRO = "Dt"
NOMBRE = "Deuteronomio"
USX = "DEU"
CAPITULOS = 34
VERSICULOS = 959
# Versículos por capítulo en la numeración inglesa (KJV); la RV1909 de eBible coincide (se comprueba).
POR_CAPITULO = [46, 37, 29, 49, 33, 25, 26, 20, 29, 22, 32, 32, 18, 29, 23, 22, 20, 22, 21, 20, 23, 30, 25, 22,
                19, 19, 26, 68, 29, 20, 30, 52, 29, 12]
# Puntos donde hebreo e inglés difieren: la RV1909 sigue la inglesa (se comprueba el comienzo de cada versículo).
VERSIFICACION = [((12, 32), "Cuidaréis de hacer todo lo que yo os mando"), ((13, 1), "CUANDO se levantare en medio de ti profeta"),
                 ((22, 30), "No tomará alguno la mujer de su padre"), ((23, 1), "NO entrará en la congregación de Jehová"),
                 ((29, 1), "ESTAS son las palabras del pacto"), ((29, 2), "Moisés pues llamó á todo Israel"),
                 ((29, 29), "Las cosas secretas pertenecen á Jehová")]
# Brenton: los versículos que se usan dicen lo mismo que la RV1909.
VERSIFICACION_LXX = [((1, 3), "in the fortieth year, in the eleventh month"), ((31, 2), "I am this day a hundred and twenty years"),
                     ((34, 7), "Moses was a hundred and twenty years old at his death")]

# «Amalec» y «Ammón» son los pueblos (Amalec va como lugar/pueblo de OpenBible; «hijos de Ammón», región).
EXCLUIR = {"YHVH_1", "NA", "Amalek_1", "Ben-ammi_1"}
# «Israel» casi siempre es el pueblo; «Jeshurun» (Dt 32:15; 33:5, 26) es un nombre poético del pueblo.
SOLO_ETIQUETA = {"Jacob_1": {"Jacob"}}
FORMA_NO_MENCION = {("Jacob_1", "israel")}
PV_DESCARTAR = {
    ("Jacob_1", (32, 9)): "en el cántico «Jacob la cuerda de su heredad» es el pueblo, no el patriarca.",
    ("Jacob_1", (33, 4)): "«la congregación de Jacob» es el pueblo, no el patriarca.",
}
REL_DESCARTAR = {}
FORMAS_FORZADAS = {}
MODERNO = {}
NOTAS = {}
IDENTIDAD = {}
ROLES = {}
SIN_NOMBRE = {}
RELACIONES = []
NOTAS_REL = {}
# Bendición de Moisés (Dt 33): BibleData sitúa a Rubén, Judá, Leví, José, Efraín y Manasés, pero no al resto de
# las tribus que el texto nombra igual («Y á Benjamín dijo…»). Se añaden para marcar todas por igual.
REFS_EXTRA = {"Benjamin_1": [(33, 12)], "Zebulun_1": [(33, 18)], "Issachar_1": [(33, 18)], "Gad_1": [(33, 20)],
              "Dan_1": [(33, 22)], "Naphtali_1": [(33, 23)], "Asher_1": [(33, 24)]}
NOTAS_EXISTENTES = {
    "Moses_1": ("Muere en la tierra de Moab a los 120 años (Dt 34:5-7): «Y era Moisés de edad de ciento y veinte años "
                "cuando murió»; lo entierran en el valle, enfrente de Bet-peor, «y ninguno sabe su sepulcro hasta hoy» "
                "(Dt 34:6)."),
    "Aaron_1": ("Dt 10:6 dice que murió y fue sepultado en Moserá («allí murió Aarón, y allí fué sepultado»); "
                "Nm 20:28 y 33:38 y Dt 32:50, que murió en el monte Hor. Se registran las dos citas sin armonizarlas."),
    "Eleazar_1": "Dt 10:6: «en lugar suyo tuvo el sacerdocio su hijo Eleazar».",
    "Joshua_1": ("Sucesor de Moisés: Dt 31:7 («tú entrarás con este pueblo á la tierra») y Dt 34:9 («Josué hijo de Nun "
                 "fué lleno de espíritu de sabiduría, porque Moisés había puesto sus manos sobre él»)."),
    "Og_1": "Dt 3:11: su cama de hierro, de nueve codos, «¿no está en Rabbath de los hijos de Ammón?».",
    "Sihon_1": "Dt 2:24: «Sehón rey de Hesbón, Amorrheo»; sale a pelear en Jahaza («Jaas», Dt 2:32).",
    "Dathan_1": "Dt 11:6: «Dathán y Abiram, hijos de Eliab hijo de Rubén» (Eliab es nieto de Rubén por Falú, Nm 26:5-8).",
    "Abiram_1": "Dt 11:6: «Dathán y Abiram, hijos de Eliab hijo de Rubén» (Eliab es nieto de Rubén por Falú, Nm 26:5-8).",
    "Balaam_1": "Dt 23:4: «Balaam hijo de Beor de Pethor de Mesopotamia de Siria».",
    "Jacob_1": "En Deuteronomio «Jeshurun» (Dt 32:15) es nombre del pueblo: no se marca como Jacob.",
}
NOTAS_VERIFICAR = [
    ("TM", (34, 7), "Y era Moisés de edad de ciento y veinte años cuando murió"), ("TM", (34, 6), "ninguno sabe su sepulcro hasta hoy"),
    ("TM", (34, 6), "enfrente de Bethpeor"), ("TM", (34, 5), "Y murió allí Moisés siervo de Jehová, en la tierra de Moab"),
    ("TM", (10, 6), "allí murió Aarón, y allí fué sepultado"), ("TM", (10, 6), "Moserá"), ("TM", (32, 50), "en el monte de Hor"),
    ("TM", (10, 6), "en lugar suyo tuvo el sacerdocio su hijo Eleazar"),
    ("TM", (31, 7), "tú entrarás con este pueblo á la tierra"),
    ("TM", (34, 9), "Josué hijo de Nun fué lleno de espíritu de sabiduría, porque Moisés había puesto sus manos sobre él"),
    ("TM", (3, 11), "¿no está en Rabbath de los hijos de Ammón?"), ("TM", (2, 24), "Sehón rey de Hesbón, Amorrheo"),
    ("TM", (2, 32), "Jaas"), ("TM", (11, 6), "Dathán y Abiram, hijos de Eliab hijo de Rubén"),
    ("TM", (23, 4), "Balaam hijo de Beor de Pethor de Mesopotamia de Siria"), ("TM", (32, 15), "Jeshurun"),
    ("TM", (32, 9), "Jacob la cuerda de su heredad"), ("TM", (33, 4), "la congregación de Jacob"),
    ("TM", (33, 12), "Benjamín"), ("TM", (33, 18), "Zabulón"), ("TM", (33, 18), "Issachâr"), ("TM", (33, 20), "Gad"),
    ("TM", (33, 22), "Dan"), ("TM", (33, 23), "Nephtalí"), ("TM", (33, 24), "Aser"),
]
# Relaciones de los libros anteriores que Deuteronomio repite: se añade la referencia a la nota.
REPITE_GN = [
    ("Eliab_2", "Dathan_1", "padre", (11, 6), "Dathán y Abiram, hijos de Eliab"),
    ("Eliab_2", "Abiram_1", "padre", (11, 6), "Dathán y Abiram, hijos de Eliab"),
    ("Beor_2", "Balaam_1", "padre", (23, 4), "Balaam hijo de Beor"),
    ("Nun_1", "Joshua_1", "padre", (1, 38), "Josué hijo de Nun"),
    ("Nun_1", "Joshua_1", "padre", (34, 9), "Josué hijo de Nun"),
    ("Jephunneh_1", "Caleb_1", "padre", (1, 36), "Caleb hijo de Jephone"),
    ("Aaron_1", "Eleazar_1", "padre", (10, 6), "su hijo Eleazar"),
]
# Edades escritas: (persona, tipo, ref, índice de cifra TM, índice LXX, evento)
EDADES = [("Moses_1", "total", (34, 7), 0, 0, ""),
          ("Moses_1", "en_evento", (31, 2), 0, 0, "al despedirse del pueblo («soy hoy día», Dt 31:2)")]

S1 = "Primer discurso: memoria del desierto (Dt 1:1–4:43)"
S2 = "Segundo discurso: el Decálogo y el Shemá (Dt 4:44–11:32)"
S3 = "Las leyes (Dt 12–26)"
S4 = "Bendiciones y maldiciones (Dt 27–28)"
S5 = "El pacto en Moab (Dt 29–30)"
S6 = "Josué, el cántico y la bendición (Dt 31–33)"
S7 = "Muerte de Moisés (Dt 34)"
PASAJES = [
    ("1:1", "1:8", "Las palabras de Moisés en Moab", "El año cuarenta, mes undécimo, Moisés habla a Israel al otro lado del Jordán y recuerda la orden de salir de Horeb.", S1),
    ("1:9", "1:18", "Jefes y jueces para el pueblo", "Moisés no puede llevar solo al pueblo: pone jefes por tribus y manda juzgar con justicia.", S1),
    ("1:19", "1:33", "Cades-barnea: el pueblo no quiere subir", "Los enviados traen fruto de la tierra, pero el pueblo teme a los amorreos y no confía en Jehová.", S1),
    ("1:34", "1:46", "Castigo y derrota en Horma", "Esa generación no verá la tierra, salvo Caleb y Josué; el pueblo sube sin Dios y es derrotado.", S1),
    ("2:1", "2:15", "Por Seir y Moab sin pelear", "Rodean el monte Seir; no han de pelear con los hijos de Esaú ni con Moab; pasan el arroyo de Zered tras treinta y ocho años.", S1),
    ("2:16", "2:25", "Junto a Ammón; hacia el Arnón", "No han de molestar a los hijos de Ammón; antiguos pueblos de gigantes; Dios manda pasar el Arnón.", S1),
    ("2:26", "2:37", "Victoria sobre Sehón", "Sehón, rey de Hesbón, niega el paso; Israel lo vence en Jahaza y toma sus ciudades.", S1),
    ("3:1", "3:11", "Victoria sobre Og", "Og, rey de Basán, sale a pelear en Edrei; Israel toma sesenta ciudades de Argob; la cama de hierro de Og.", S1),
    ("3:12", "3:22", "El reparto al oriente del Jordán", "Rubén, Gad y la media tribu de Manasés reciben la tierra; Jair y Maquir; los hombres de guerra pasarán armados.", S1),
    ("3:23", "3:29", "Moisés no pasará el Jordán", "Moisés ruega pasar; Dios le manda subir a la cumbre del Pisga y mirar, y animar a Josué.", S1),
    ("4:1", "4:14", "Guardar los mandamientos; el día de Horeb", "No añadir ni quitar; lo que pasó en Baal-peor; el pueblo oyó la voz de Dios en Horeb.", S1),
    ("4:15", "4:31", "Contra las imágenes", "En Horeb no vieron figura: no harán imágenes; si las hacen serán esparcidos, y si vuelven Dios no los olvidará.", S1),
    ("4:32", "4:43", "Ningún dios como Jehová; ciudades de refugio", "¿Qué pueblo oyó la voz de Dios y vivió? Moisés aparta Beser, Ramot y Golán al oriente del Jordán.", S1),
    ("4:44", "5:5", "Introducción: el pacto de Horeb", "Esta es la ley que Moisés puso delante de Israel en Moab; el pacto de Horeb es con los que viven hoy.", S2),
    ("5:6", "5:21", "Los diez mandamientos", "Moisés repite las diez palabras: un solo Dios, sin imágenes, el nombre, el sábado, los padres, la vida, el matrimonio, lo ajeno.", S2),
    ("5:22", "5:33", "El pueblo pide que Moisés hable", "El pueblo teme la voz de Dios en el fuego y pide que Moisés les transmita lo que Dios diga.", S2),
    ("6:1", "6:9", "Oye, Israel (el Shemá)", "«Oye, Israel: Jehová nuestro Dios, Jehová uno es»; amarle con todo el corazón y enseñar estas palabras a los hijos.", S2),
    ("6:10", "6:25", "No olvidar a Jehová en la tierra", "Al entrar en la tierra no olvidarán a Dios ni lo tentarán como en Massa; contarán a sus hijos la salida de Egipto.", S2),
    ("7:1", "7:11", "Un pueblo santo, escogido por amor", "Orden de destruir a las siete naciones y no emparentar con ellas; Dios los escogió por amor, no por ser muchos.", S2),
    ("7:12", "7:26", "La bendición de obedecer; no temer", "Si obedecen serán bendecidos; no temerán a las naciones; quemarán sus imágenes.", S2),
    ("8:1", "8:20", "No olvidar en la abundancia", "Cuarenta años en el desierto y el maná: «el hombre no vivirá de solo pan»; en la tierra buena no olvidarán a Dios.", S2),
    ("9:1", "9:14", "No por tu justicia; la rebelión en Horeb", "Dios echará a las naciones no por la justicia de Israel; Moisés recuerda cómo el pueblo se rebeló en Horeb.", S2),
    ("9:15", "9:29", "El becerro de oro y la intercesión", "Moisés quiebra las tablas al ver el becerro, lo quema y ruega cuarenta días por el pueblo y por Aarón.", S2),
    ("10:1", "10:11", "Las nuevas tablas; los levitas", "Dios escribe otra vez las tablas, que se guardan en el arca; muerte de Aarón; la tribu de Leví apartada.", S2),
    ("10:12", "10:22", "¿Qué pide Jehová?", "Temer a Dios, andar en sus caminos y amarle; circuncidar el corazón y amar al extranjero.", S2),
    ("11:1", "11:12", "Lo que vieron sus ojos", "Las señales en Egipto y en el mar, lo que hizo con Datán y Abiram; la tierra que Dios cuida.", S2),
    ("11:13", "11:21", "La lluvia a su tiempo; las palabras en el corazón", "Si aman a Dios tendrán lluvia y cosecha; pondrán estas palabras en su corazón y en sus puertas.", S2),
    ("11:22", "11:32", "Bendición y maldición: Gerizim y Ebal", "La tierra hasta el Éufrates; delante de ellos la bendición y la maldición, puestas sobre Gerizim y Ebal.", S2),
    ("12:1", "12:14", "El lugar que Dios escoja", "Destruirán los lugares de culto de las naciones y ofrecerán sus sacrificios solo en el lugar que Dios escoja.", S3),
    ("12:15", "12:32", "Comer carne; no imitar a las naciones", "Pueden comer carne en sus ciudades, pero no la sangre; no imitarán el culto de las naciones.", S3),
    ("13:1", "13:18", "Contra quien incita a otros dioses", "El profeta, el pariente o la ciudad que inciten a servir a otros dioses serán castigados.", S3),
    ("14:1", "14:21", "Animales limpios e inmundos", "Pueblo santo: qué animales, peces y aves pueden comer y cuáles no.", S3),
    ("14:22", "14:29", "El diezmo", "Diezmo de la cosecha comido delante de Dios; cada tres años, para el levita, el extranjero, el huérfano y la viuda.", S3),
    ("15:1", "15:11", "El año de la remisión", "Cada siete años se perdonan las deudas; no endurecer el corazón con el pobre.", S3),
    ("15:12", "15:23", "El siervo hebreo; los primogénitos", "El siervo hebreo sale libre al séptimo año y con provisión; los primogénitos del ganado son de Dios.", S3),
    ("16:1", "16:17", "Las tres fiestas", "La Pascua, la fiesta de las semanas y la de las cabañas, en el lugar que Dios escoja.", S3),
    ("16:18", "17:7", "Jueces justos; contra la idolatría", "Jueces que no reciban soborno; no plantar bosques ni ofrecer animales con defecto; castigo del que sirve a otros dioses.", S3),
    ("17:8", "17:20", "El tribunal y el rey", "Los casos difíciles van a los sacerdotes y al juez; el rey no multiplicará caballos, mujeres ni oro, y leerá la ley.", S3),
    ("18:1", "18:8", "La porción de los levitas", "Los levitas no tienen heredad: Jehová es su heredad y viven de las ofrendas.", S3),
    ("18:9", "18:22", "Contra la adivinación; el profeta", "No habrá adivinos ni encantadores; Dios levantará un profeta como Moisés.", S3),
    ("19:1", "19:13", "Las ciudades de refugio", "Tres ciudades para quien mata sin intención; el homicida voluntario no tiene refugio.", S3),
    ("19:14", "19:21", "Lindes y testigos", "No mover los mojones del prójimo; dos o tres testigos; castigo del testigo falso.", S3),
    ("20:1", "20:20", "Leyes de la guerra", "El sacerdote anima al pueblo; quiénes vuelven a casa; ofrecer paz a las ciudades; no cortar los árboles frutales.", S3),
    ("21:1", "21:9", "El muerto hallado en el campo", "Si aparece un muerto y no se sabe quién lo mató, los ancianos de la ciudad más cercana hacen expiación.", S3),
    ("21:10", "21:23", "La cautiva, el primogénito y el hijo rebelde", "Leyes sobre la mujer tomada en la guerra, el derecho del primogénito, el hijo rebelde y el colgado de un madero.", S3),
    ("22:1", "22:12", "Cuidar lo del prójimo y otras leyes", "Devolver el animal perdido; el nido de aves; el pretil del terrado; no mezclar semillas ni tejidos; los flecos.", S3),
    ("22:13", "22:30", "Leyes sobre el matrimonio", "La acusación contra la recién casada, el adulterio y otras faltas contra el matrimonio.", S3),
    ("23:1", "23:14", "La congregación y el campamento", "Quiénes no entran en la congregación (amonitas y moabitas, por Balaam); limpieza del campamento.", S3),
    ("23:15", "23:25", "Siervos, préstamos y votos", "No entregar al siervo fugitivo; no cobrar usura al hermano; cumplir los votos; comer de la viña ajena sin llevarse.", S3),
    ("24:1", "24:9", "Divorcio, recién casados y prendas", "La carta de divorcio; el recién casado no va a la guerra; no tomar en prenda la muela; acordarse de María.", S3),
    ("24:10", "24:22", "El jornal y el extranjero", "Las prendas del pobre, el jornal el mismo día, cada uno muere por su pecado; las espigas para el extranjero, el huérfano y la viuda.", S3),
    ("25:1", "25:10", "Azotes y levirato", "Límite de cuarenta azotes; no poner bozal al buey; el hermano del difunto toma a la viuda.", S3),
    ("25:11", "25:19", "Pesas justas; Amalec", "Pesas y medidas justas; acordarse de lo que hizo Amalec en el camino.", S3),
    ("26:1", "26:19", "Las primicias, el diezmo y el pacto", "Al ofrecer las primicias se recuerda la historia («Un Siro á punto de perecer fué mi padre»); Israel, pueblo de Dios.", S3),
    ("27:1", "27:10", "Las piedras en el monte Ebal", "Al pasar el Jordán levantarán piedras con la ley escrita y un altar en el monte Ebal.", S4),
    ("27:11", "27:26", "Las maldiciones entre Gerizim y Ebal", "Seis tribus sobre Gerizim y seis sobre Ebal; los levitas pronuncian doce maldiciones y el pueblo responde «Amén».", S4),
    ("28:1", "28:14", "Las bendiciones", "Si obedecen serán benditos en la ciudad y en el campo, en sus hijos, su ganado y sus cosechas.", S4),
    ("28:15", "28:29", "Maldiciones: plagas y sequía", "Si no obedecen vendrán maldición, enfermedad, sequía y derrota.", S4),
    ("28:30", "28:46", "Maldiciones: despojo y destierro", "Otros gozarán lo que ellos trabajaron; serán llevados a otra nación y el extranjero los dominará.", S4),
    ("28:47", "28:57", "El asedio", "Una nación lejana pondrá cerco a sus ciudades y el hambre será extrema.", S4),
    ("28:58", "28:68", "Esparcidos entre los pueblos", "Plagas, pocos sobrevivientes, dispersión entre las naciones y vuelta a Egipto en navíos.", S4),
    ("29:1", "29:15", "El pacto en Moab", "Palabras del pacto en Moab, además del de Horeb; todo Israel, presentes y futuros, entran en él.", S5),
    ("29:16", "29:29", "Contra la idolatría; lo secreto y lo revelado", "Quien se aparte para servir a otros dioses traerá ruina sobre la tierra; las cosas secretas son de Dios.", S5),
    ("30:1", "30:10", "La vuelta y el corazón circuncidado", "Si en el destierro vuelven a Dios, él los reunirá y circuncidará su corazón.", S5),
    ("30:11", "30:20", "La vida y la muerte delante de ti", "El mandamiento no está lejos; Moisés pone delante la vida y la muerte: «escoge pues la vida».", S5),
    ("31:1", "31:13", "Josué, sucesor; la ley escrita", "Moisés, de ciento veinte años, anima a Josué; escribe la ley y manda leerla cada siete años.", S6),
    ("31:14", "31:30", "Dios anuncia la infidelidad; el cántico", "En el tabernáculo Dios encarga a Josué y anuncia que el pueblo se apartará; Moisés escribe un cántico y deja el libro junto al arca.", S6),
    ("32:1", "32:18", "El cántico de Moisés: la Roca", "«Escuchad, cielos»: Dios es la Roca, perfecta su obra; cuidó a su pueblo en el desierto, pero Jeshurun lo dejó.", S6),
    ("32:19", "32:33", "El cántico de Moisés: el castigo", "Dios esconde su rostro y anuncia el castigo de un pueblo infiel.", S6),
    ("32:34", "32:43", "El cántico de Moisés: Dios juzga", "«Mía es la venganza»: Dios juzgará a su pueblo y se apiadará de sus siervos.", S6),
    ("32:44", "32:52", "Moisés verá la tierra desde Nebo", "Moisés pide guardar todas estas palabras; Dios le manda subir al monte Nebo para ver Canaán y morir allí.", S6),
    ("33:1", "33:12", "La bendición de Moisés: de Rubén a Benjamín", "Moisés, varón de Dios, bendice a las tribus: Rubén, Judá, Leví y Benjamín.", S6),
    ("33:13", "33:29", "La bendición de Moisés: de José a Aser", "Bendiciones de José, Zabulón e Isacar, Gad, Dan, Neftalí y Aser; «Bienaventurado tú, oh Israel».", S6),
    ("34:1", "34:12", "Muerte de Moisés", "Desde el Nebo Dios muestra a Moisés la tierra; muere en Moab a los ciento veinte años; Josué le sucede.", S7),
]
# Citas de los resúmenes que van entre comillas (se comprueban).
CITAS_RESUMEN = [((6, 4), "Oye, Israel: Jehová nuestro Dios, Jehová uno es"), ((8, 3), "el hombre no vivirá de solo pan"),
                 ((26, 5), "Un Siro á punto de perecer fué mi padre"), ((30, 19), "escoge pues la vida"),
                 ((32, 1), "ESCUCHAD, cielos"), ((32, 35), "Mía es la venganza"), ((33, 29), "Bienaventurado tú, oh Israel"),
                 ((27, 15), "Amén")]

# Lugares de OpenBible en Deuteronomio: obid -> (id, nombre, formas RV1909 o None = detectar, tipo, nota, forzar baja).
# Van primero (el orden importa): «campos de Moab», «camino del mar Bermejo», «Basán-havoth-jair», «aguas de la
# rencilla», «mar del llano». Las entradas de lugares ya registrados solo aportan formas.
LUGARES = {
    "aca767b": ("campos-de-moab", "Campos de Moab", ["campos de Moab"], "region", "", False),
    "a55c970": ("camino-mar-rojo", "Camino del mar Rojo", ["camino del mar Bermejo"], "otro", "", False),
    "a26c8f2": ("havot-jair", "Havot-jair", ["Basán-havoth-jair"], "region", "", False),
    "a505743": ("meriba-cades", "Meriba de Cades", ["aguas de la rencilla"], "fuente", "", False),
    "a65db0f": ("meriba", "Meriba", ["aguas de la rencilla"], "fuente", "", False),
    "abed304": ("mar-salado", "Mar Salado", ["mar Salado", "mar del llano"], "mar", "", False),
    "aa805fb": ("mar-grande", "Mar Grande", ["gran mar", "mar postrera"], "mar", "", False),
    "a581f0c": ("canaan", "Canaán", ["Canaán"], "region", "", False),
    "ab5161f": ("arroyo-de-zered", "Arroyo de Zered", ["Zered"], "rio", "", False),
    "aefaa2d": ("monte-nebo", "Monte Nebo", ["Nebo"], "monte",
                "Desde aquí Moisés ve la tierra antes de morir (Dt 32:49; 34:1). Distinto de la ciudad de Nebo (Nm 32:3).", False),
    "aa5cc66": ("monte-ebal", "Monte Ebal", ["Ebal"], "monte",
                "Monte de la maldición (Dt 11:29; 27:13); allí se levantan las piedras con la ley (Dt 27:4).", False),
    "a30e967": ("monte-gerizim", "Monte Gerizim", ["Gerizim"], "monte", "Monte de la bendición (Dt 11:29; 27:12).", False),
    "a341fe8": ("monte-hermon", "Monte Hermón", ["Hermón", "Sirión", "Sión"], "monte",
                "Dt 3:9: «Los Sidonios llaman á Hermón Sirión; y los Amorrheos, Senir». Dt 4:48: «el monte de Sión, "
                "que es Hermón» (no es Sion de Jerusalén).", False),
    "ad27e17": ("senir", "Senir", None, "monte", "Nombre amorreo del Hermón (Dt 3:9); OpenBible lo registra aparte.", False),
    "af693b8": ("monte-paran", "Monte de Parán", ["Parán"], "monte", "En la bendición de Moisés (Dt 33:2).", False),
    "a2bb265": ("cineret", "Cineret", ["Cinereth"], "ciudad",
                "Límite de lo que reciben Rubén y Gad (Dt 3:17). OpenBible la identifica sobre todo con Tel Kinrot y "
                "propone también el mar de Galilea.", False),
    "a42a5b2": ("argob", "Argob", None, "region", "Región del reino de Og en Basán, con sesenta ciudades (Dt 3:4).", False),
    "a6fea11": ("astarot", "Astarot", None, "ciudad", "Donde habitaba Og, rey de Basán (Dt 1:4).", False),
    "a280f83": ("beerot-bene-jaacan", "Beerot-bene-jaacán", None, "campamento",
                "Dt 10:6. Probablemente el mismo lugar que Bene-jaacán (Nm 33:31); OpenBible los registra aparte.", False),
    "af3ce34": ("bet-peor", "Bet-peor", None, "ciudad", "Moisés es enterrado en el valle, enfrente de Bet-peor (Dt 34:6).", False),
    "a0cd098": ("beser", "Beser", None, "ciudad", "Ciudad de refugio de Rubén (Dt 4:43).", False),
    "abb5c1e": ("golan", "Golán", None, "ciudad", "Ciudad de refugio de Manasés, en Basán (Dt 4:43).", False),
    "a95147f": ("ramot-galaad", "Ramot de Galaad", None, "ciudad", "Ciudad de refugio de Gad (Dt 4:43: «Ramoth en Galaad»).", False),
    "a329990": ("caftor", "Caftor", None, "region", "De donde salieron los caftoreos (Dt 2:23).", False),
    "afcb77d": ("dizahab", "Dizahab", None, "otro", "En la descripción del lugar de los discursos (Dt 1:1).", False),
    "a7ecf6c": ("tofel", "Tofel", None, "otro", "En la descripción del lugar de los discursos (Dt 1:1).", False),
    "ad763b1": ("laban", "Labán (lugar)", None, "otro", "Lugar de Dt 1:1; no es Labán, el hermano de Rebeca.", False),
    "af0ac29": ("elat", "Elat", None, "ciudad", "", False),
    "a84a509": ("gilgal-more", "Gilgal (junto a More)", None, "ciudad",
                "Dt 11:30: «delante de Gilgal, junto á los llanos de Moreh».", False),
    "a416b43": ("cademot", "Cademot", None, "region", "Desierto desde el que Moisés envía mensajeros a Sehón (Dt 2:26).", False),
    "a730058": ("libano", "Líbano", None, "region", "", False),
    "ae067b5": ("raba-amon", "Rabá de los hijos de Amón", None, "ciudad", "Allí está la cama de hierro de Og (Dt 3:11).", False),
    "ac3bc41": ("salca", "Salca", None, "ciudad", "Límite del reino de Og en Basán (Dt 3:10).", False),
}
# Mismo lugar con dos entradas de OpenBible (misma identificación moderna): se amplía el lugar ya registrado.
UNIR_LUGAR = {"af4c2cd": "arnon", "ab5161f": "arroyo-de-zered"}
EXCLUIR_LUGAR = {
    "a2bb5ef": ("Arabá: la RV1909 traduce «el llano», «la llanura» o «la campiña» (Dt 1:1; 1:7; 2:8; 3:17; 4:49; 11:30); "
                "no es nombre propio en este texto. «La mar del llano» va como mar Salado."),
    "a1cb244": "Néguev: la RV1909 traduce «el mediodía» / «la parte meridional» (Dt 1:7; 34:3); no es nombre propio.",
    "af084cf": "Sefela: la RV1909 traduce «los valles» (Dt 1:7); no es nombre propio.",
    "af725bb": "Suf (Dt 1:1): la RV1909 dice «delante del mar Bermejo»; no nombra Suf.",
    "a529e92": "«Ciudad de las palmas» (Dt 34:3): en la RV1909 es otro nombre de Jericó; se marca Jericó.",
    "ac9a77c": "«La vega de Jericó» (Dt 34:3): se marca Jericó.",
    "a3d6e81": "Baal-peor (Dt 4:3): es el dios por el que fue castigado el pueblo (Nm 25:3); OpenBible lo registra como lugar.",
}
PRECEDIDO = {"af693b8": "monte de "}
OBLIGATORIOS_LUGAR = ["monte-nebo", "pisga", "monte-ebal", "monte-gerizim", "monte-hermon", "senir", "argob", "ar", "jahaza",
                      "edrei", "beser", "ramot-galaad", "golan", "hesbon", "basan", "campos-de-moab", "moserot", "monte-hor",
                      "bet-peor", "jerico"]

# La cronología de Deuteronomio (Dt 1:3 y la muerte de Moisés) está en cronologia.py.


def construir(cx):
    rv, br, errores = cx["rv"], cx["br"], cx["errores"]
    for c, n in enumerate(POR_CAPITULO, 1):
        hay = sum(1 for (cc, _) in rv if cc == c)
        if hay != n:
            errores.append(f"Deuteronomio {c}: la RV1909 tiene {hay} versículos (numeración inglesa: {n})")
    for ref, ini in VERSIFICACION:
        if not rv.get(ref, "").startswith(ini):
            errores.append(f"Versificación de Dt {ref[0]}:{ref[1]}: la RV1909 no empieza «{ini}»")
    for ref, frag in VERSIFICACION_LXX:
        if frag not in br.get(ref, ""):
            errores.append(f"Brenton Dt {ref[0]}:{ref[1]} no dice «{frag}»")
    for ref, frag in CITAS_RESUMEN:
        if frag not in rv.get(ref, ""):
            errores.append(f"Resumen de pasaje: «{frag}» no está en Dt {ref[0]}:{ref[1]}")
    return exodo.construir(cx, sys.modules[__name__])


def construir_lugares(rv, menciones_personas, rutas, lugares_previos, errores, avisos, sa):
    return exodo.construir_lugares(rv, menciones_personas, rutas, lugares_previos, errores, avisos, sa,
                                   sys.modules[__name__])


# ---------------------------------------------------------------- hechos obligatorios (sobre los datos finales)
def comprobar(datos, errores):
    """Comprueba los hechos pedidos para Deuteronomio (falla si falta alguno). Devuelve líneas de informe."""
    P = {p["id"]: p for p in datos["personas"]}
    R = {(x["de"], x["a"], x["tipo"]): x for x in datos["relaciones"]}
    L = {l["id"]: l for l in datos["lugares"]}
    caps = [c for c in datos["capitulos"] if c["libro"] == LIBRO]
    texto = {f"{LIBRO} {c['cap']}:{v['n']}": v["texto"] for c in caps for v in c["versiculos"]}
    M = {(m["ref"], m["persona"]) for m in datos["menciones"]}
    lineas = []

    def ok_(cond, desc):
        lineas.append(f"{'OK ' if cond else 'FALTA'} {desc}")
        if not cond:
            errores.append(f"Hecho obligatorio (Deuteronomio): {desc}")

    def tiene(pid, ref, mencion=True):
        return ref in P.get(pid, {}).get("refs", []) and (not mencion or (ref, pid) in M)

    def nota_rel(de, a, tipo, frag):
        x = R.get((de, a, tipo))
        ok_(bool(x) and frag in x["nota"], f"{de}→{a} {tipo} con la cita de {frag}" + (f" [{x['ref']}]" if x else " [falta]"))

    # Versificación: 34 capítulos, 959 versículos en numeración inglesa, sin vacíos
    ok_(len(caps) == CAPITULOS and len(texto) == VERSICULOS
        and [len(c["versiculos"]) for c in caps] == POR_CAPITULO,
        f"{CAPITULOS} capítulos y {VERSICULOS} versículos con los recuentos de la numeración inglesa (hay {len(caps)} y {len(texto)})")
    ok_(not [r for r, t in texto.items() if not t], "ningún versículo vacío")
    # Moisés muere en Moab a los 120 años (TM y LXX con cita)
    ok_(tiene("Moses_1", "Dt 34:5") and "en la tierra de Moab" in texto["Dt 34:5"], "Moisés muere en la tierra de Moab (Dt 34:5)")
    ed = {e["tradicion"]: e for e in datos["edades"] if e["persona"] == "Moses_1" and e["ref"] == "Dt 34:7"}
    ok_(set(ed) == {"TM", "LXX"} and all(e["valor"] == 120 and e["tipo"] == "total" for e in ed.values())
        and ed["TM"]["cita"] in texto["Dt 34:7"], "Moisés muere a los 120 años (Dt 34:7, TM y LXX con cita)")
    EV = {e["id"]: e for e in datos["cronologia"]["eventos"]}
    e77 = [e for e in datos["edades"] if e["persona"] == "Moses_1" and e["ref"] == "Ex 7:7" and e["tradicion"] == "TM"]
    mu, sa_, di = EV.get("ev-muerte-moises"), EV.get("ev-salida-egipto"), EV.get("ev-discursos-moab")
    c = "TM|tare70|sem2|egipto"
    if e77 and mu and sa_ and di and ed.get("TM"):
        trans = mu["anios"][c] - sa_["anios"][c]
        ok_(e77[0]["valor"] == 80 and e77[0]["valor"] + trans == ed["TM"]["valor"],
            f"edad de Moisés: 80 (Ex 7:7) + {trans} años (salida → Dt 1:3) = {e77[0]['valor'] + trans} = 120 (Dt 34:7)")
        c2 = "LXX|tare70|sem2|egipto"
        t2 = mu["anios"][c2] - sa_["anios"][c2]
        ok_(0 <= ed["LXX"]["valor"] - (80 + t2) <= mu.get("margen_total", 1),
            f"LXX: 80 + {t2} = {80 + t2}, texto 120 (margen de un año, ver nota)")
        ok_(di["anios"][c] - sa_["anios"][c] == 40 and di["certeza"] == "calculo" and di["ref"] == "Dt 1:3"
            and di["depende_de"] == "ev-salida-egipto" and di["pasos"],
            "discursos de Moab: «á los cuarenta años» de la salida (Dt 1:3), cálculo con pasos")
        ok_(mu["depende_de"] == "ev-discursos-moab" and mu["ref"] == "Dt 34:5", "muerte de Moisés después de Dt 1:3 (Dt 34:5)")
    else:
        ok_(False, "edad de Moisés 80 → 120: faltan datos (Ex 7:7, ev-discursos-moab, ev-muerte-moises o Dt 34:7)")
    # Josué hijo de Nun, sucesor (mismo id que en Ex/Nm)
    j = P.get("Joshua_1", {})
    ok_(tiene("Joshua_1", "Dt 31:7") and tiene("Joshua_1", "Dt 34:9")
        and {"Ex 17:9", "Nm 13:17"} <= set(j.get("refs", [])), "Josué sucesor (Dt 31:7; 34:9) = Josué de Ex 17:9 y Nm 13:17")
    nota_rel("Nun_1", "Joshua_1", "padre", "Dt 34:9")
    # Og y Sehón, los mismos de Nm 21
    ok_(tiene("Og_1", "Dt 3:1") and "Nm 21:33" in P["Og_1"]["refs"] and "Og rey de Basán" in texto["Dt 3:1"],
        "Og rey de Basán (Dt 3:1) = Og de Nm 21:33")
    ok_(tiene("Sihon_1", "Dt 2:24") and "Nm 21:21" in P["Sihon_1"]["refs"] and "Sehón rey de Hesbón" in texto["Dt 2:24"],
        "Sehón rey de Hesbón (Dt 2:24) = Sehón de Nm 21:21")
    # Datán y Abiram hijos de Eliab, los de Nm 16
    for h in ("Dathan_1", "Abiram_1"):
        ok_(tiene(h, "Dt 11:6") and "Nm 16:1" in P[h]["refs"], f"{h} en Dt 11:6 = el de Nm 16:1")
        nota_rel("Eliab_2", h, "padre", "Dt 11:6")
    ok_(tiene("Eliab_2", "Dt 11:6") and "Dt 11:6" not in P.get("Eliab_1", {}).get("refs", []), "Eliab de Dt 11:6 es el de Rubén (Eliab_2)")
    # Balaam hijo de Beor, el de Nm 22
    ok_(tiene("Balaam_1", "Dt 23:4") and tiene("Beor_2", "Dt 23:4") and "Nm 22:5" in P["Balaam_1"]["refs"],
        "Balaam hijo de Beor (Dt 23:4) = Balaam de Nm 22:5")
    nota_rel("Beor_2", "Balaam_1", "padre", "Dt 23:4")
    # Eleazar sucede a Aarón; Aarón muere en Moserá (Dt 10:6) / monte Hor (Nm 20:28; 33:38): sin armonizar
    ok_(tiene("Eleazar_1", "Dt 10:6") and tiene("Aaron_1", "Dt 10:6"), "Eleazar y Aarón en Dt 10:6")
    nota_rel("Aaron_1", "Eleazar_1", "padre", "Dt 10:6")
    na = P.get("Aaron_1", {}).get("nota", "")
    ok_("Dt 10:6" in na and "Moserá" in na and "Nm 20:28" in na and "sin armonizar" in na,
        "muerte de Aarón: Moserá (Dt 10:6) y monte Hor (Nm 20:28; 33:38) en la nota, sin armonizar")
    ok_("Dt 10:6" in L.get("moserot", {}).get("refs", []) and {"Nm 33:38", "Dt 32:50"} <= set(L.get("monte-hor", {}).get("refs", [])),
        "lugares: Moserá (Dt 10:6) y monte Hor (Nm 33:38; Dt 32:50) con sus refs")
    # Lugares
    for lid in OBLIGATORIOS_LUGAR:
        l = L.get(lid)
        ok_(bool(l) and any(r.startswith("Dt ") for r in l["refs"]),
            f"lugar {lid} con refs de Deuteronomio ({sum(1 for r in l['refs'] if r.startswith('Dt ')) if l else 0})")
    ok_({"Dt 32:49", "Dt 34:1"} <= set(L.get("monte-nebo", {}).get("refs", [])) and "Dt 34:1" in L.get("pisga", {}).get("refs", []),
        "monte Nebo (Dt 32:49; 34:1) y Pisga (Dt 34:1)")
    ok_({"Dt 11:29", "Dt 27:4", "Dt 27:13"} <= set(L.get("monte-ebal", {}).get("refs", []))
        and {"Dt 11:29", "Dt 27:12"} <= set(L.get("monte-gerizim", {}).get("refs", [])), "Ebal (Dt 11:29; 27:4, 13) y Gerizim (Dt 11:29; 27:12)")
    ok_(all("Dt 4:43" in L.get(x, {}).get("refs", []) for x in ("beser", "ramot-galaad", "golan")),
        "ciudades de refugio de Dt 4:43 (Beser, Ramot, Golán)")
    # Pasajes y secciones
    pas = [p for p in datos["pasajes"] if p["libro"] == LIBRO]
    ok_(len(pas) == len(PASAJES) and pas[0]["inicio"] == "Dt 1:1" and pas[-1]["fin"] == "Dt 34:12",
        f"{len(pas)} pasajes dt-NN de Dt 1:1 a Dt 34:12")
    ok_(len({p["seccion"] for p in pas}) == 7, "7 secciones")
    return lineas
