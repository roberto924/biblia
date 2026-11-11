"""Recorridos (itinerarios) de Génesis y Éxodo con varias hipótesis de ubicación.

Genera datos/recorridos.js  ->  window.BIBLIA_RECORRIDOS = {generado, fuentes, recorridos}

Uso:  python -I herramientas/recorridos.py
No usa la red: lee datos/biblia.js (texto RV1909, lugares, personas) y la caché de OpenBible
(herramientas/cache/ob_ancient.jsonl y ob_modern.jsonl, que descarga construir_datos.py).

Principio: ninguna coordenada se escribe a mano. Cada ubicación se toma de OpenBible (identificación
moderna asociada al lugar antiguo, con su puntuación) y lleva su URL. Las hipótesis llevan la
referencia (verificada) que las describe. Si una hipótesis no propone lugar para una etapa,
la ubicación va con lat/lon = null y confianza «baja», y la nota de la etapa lo dice.

Sale con código != 0 (y sin escribir nada) si falla alguna verificación:
  citas literales (etapas y pasos de tiempo), refs ascendentes dentro de cada recorrido,
  ubicación con coordenadas en la hipótesis por defecto de cada etapa, fuente+url en cada
  hipótesis, ids de lugares y personas existentes, coherencia con biblia.js.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "herramientas" / "cache"
DATOS = RAIZ / "datos"
SALIDA = DATOS / "recorridos.js"

UMBRAL_ALTA, UMBRAL_MEDIA = 500, 100          # mismos umbrales que lugares_mapa.py
SINAI_OB = {"abfba2a", "ae50cf1", "a9bb03e"}  # monte Sinaí, desierto de Sinaí, Horeb: siempre «baja»
OB_SINAI = "abfba2a"
OB_NEGEB = "a1cb244"
OB_FUENTE = "OpenBible.info, Bible Geocoding Data (CC BY 4.0)"

WIKI_SINAI = "https://en.wikipedia.org/wiki/Biblical_Mount_Sinai"
WIKI_KARKOM = "https://en.wikipedia.org/wiki/Har_Karkom"
WIKI_LAWZ = "https://en.wikipedia.org/wiki/Jabal_al-Lawz"
WIKI_UR = "https://en.wikipedia.org/wiki/Ur_Ka%C5%9Bdim"

FUENTES = [
    {"id": "rv1909", "nombre": "Reina-Valera 1909 (texto de las citas)", "licencia": "Dominio público",
     "url": "https://ebible.org/Scriptures/spaRV1909_vpl.zip"},
    {"id": "openbible", "nombre": "OpenBible.info, Bible Geocoding Data (coordenadas, identificaciones y puntuaciones)",
     "licencia": "CC BY 4.0", "url": "https://github.com/openbibleinfo/Bible-Geocoding-Data",
     "atribucion": "Ubicaciones: OpenBible.info, CC BY 4.0; identificaciones y puntuaciones adaptadas"},
    {"id": "wikipedia", "nombre": "Wikipedia en inglés (fuente secundaria para describir las hipótesis): "
     "«Biblical Mount Sinai», «Har Karkom», «Jabal al-Lawz», «Ur Kaśdim»", "licencia": "CC BY-SA 4.0 (solo datos, no texto)",
     "url": WIKI_SINAI},
]

# --------------------------------------------------------------------------- hipótesis
HIP_EXODO = [
    {"id": "tradicional", "nombre": "Sinaí en Jebel Musa (tradición bizantina)", "defecto": True,
     "descripcion": "Ruta por el sur de la península del Sinaí: cruce en la zona de los lagos Amargos, bajada por la "
                    "costa del golfo de Suez y llegada a Jebel Musa. La identificación del Sinaí con Jebel Musa es "
                    "la tradición cristiana desde el s. IV (iglesia de Elena hacia el 330; monasterio de Santa "
                    "Catalina, s. VI; la peregrina Egeria). Fuente externa. Cada etapa usa la identificación mejor "
                    "puntuada de OpenBible, salvo el cruce (ver la nota de esa etapa).",
     "fuente": "Wikipedia, «Biblical Mount Sinai» (tradición de Jebel Musa); coordenadas: OpenBible.info",
     "url": WIKI_SINAI},
    {"id": "sin-bishar", "nombre": "Sinaí en Jebel Sin Bishar (oeste-centro del Sinaí)", "defecto": False,
     "descripcion": "Propuesta de Menashe Har-El, geógrafo bíblico de la Universidad de Tel Aviv (The Sinai Journeys): "
                    "el monte estaría en el oeste-centro de la península, mucho más al norte que Jebel Musa. "
                    "Solo se sitúa aquí el monte (y las etapas de Egipto comunes a todas); las estaciones intermedias "
                    "de esta propuesta no se han podido verificar y quedan sin ubicación. Fuente externa.",
     "fuente": "Wikipedia, «Biblical Mount Sinai» (Har-El y Jebel Sin Bishar); coordenadas: OpenBible.info",
     "url": WIKI_SINAI},
    {"id": "har-karkom", "nombre": "Sinaí en Har Karkom (Négueb)", "defecto": False,
     "descripcion": "Emmanuel Anati, que excavó Har Karkom (también Jabal Ideid), en el Négueb, la identificó con el "
                    "monte Sinaí (The Riddle of Mount Sinai, 2001). Críticas recogidas: I. Finkelstein y J. K. "
                    "Hoffmeier (cronología unos mil años anterior y hallazgos no exclusivos de este monte). Solo se "
                    "sitúa el monte; las estaciones intermedias quedan sin ubicación. Fuente externa.",
     "fuente": "Wikipedia, «Har Karkom» y «Biblical Mount Sinai»; E. Anati, The Riddle of Mount Sinai (2001); "
               "coordenadas: OpenBible.info",
     "url": WIKI_KARKOM},
    {"id": "al-lawz", "nombre": "Sinaí en Jabal al-Lawz, Arabia (minoritaria)", "defecto": False, "minoritaria": True,
     "descripcion": "Teoría «arábiga»: el mar sería el golfo de Áqaba y el Sinaí estaría en Jabal al-Lawz (o Jabal "
                    "Maqla), en el noroeste de Arabia Saudí. La defienden autores como R. Wyatt, B. Cornuke y L. "
                    "Möller; la rechazan académicos como J. K. Hoffmeier (Ancient Israel in Sinai, 2005). Se marca "
                    "minoritaria porque OpenBible le da una puntuación de 4 frente a 465 de Jebel Musa. Fuente externa.",
     "fuente": "Wikipedia, «Jabal al-Lawz» y «Biblical Mount Sinai»; coordenadas: OpenBible.info",
     "url": WIKI_LAWZ},
]

HIP_ABRAHAM = [
    {"id": "ur-sur", "nombre": "Ur del sur (Tell el-Muqayyar, Irak)", "defecto": True,
     "descripcion": "Identificación de H. Rawlinson (1862), excavada por L. Woolley; es la opinión académica "
                    "mayoritaria. Fuente externa.",
     "fuente": "Wikipedia, «Ur Kaśdim»; coordenadas: OpenBible.info", "url": WIKI_UR},
    {"id": "ur-norte", "nombre": "Ur del norte (Urfa / Şanlıurfa, Turquía)", "defecto": False, "minoritaria": True,
     "descripcion": "Tradición judía e islámica que sitúa a Abraham en Urfa (la antigua Edesa), cerca de Harán; "
                    "apoyo académico minoritario (p. ej. G. Rendsburg, 2019). Solo cambia la primera etapa. Fuente externa.",
     "fuente": "Wikipedia, «Ur Kaśdim»; coordenadas: OpenBible.info", "url": WIKI_UR},
]

HIP_JACOB = [
    {"id": "openbible", "nombre": "Identificaciones mejor puntuadas de OpenBible", "defecto": True,
     "descripcion": "Una sola hipótesis: en cada lugar, la identificación moderna con mayor puntuación en OpenBible "
                    "(la misma que usa el mapa de la aplicación). Fuente externa.",
     "fuente": OB_FUENTE, "url": "https://www.openbible.info/geo/"},
]

# --------------------------------------------------------------------------- etapas
# Especificación de ubicación por hipótesis:
#   L          -> la identificación por defecto del lugar (la de biblia.js)
#   C          -> común: la misma que la hipótesis por defecto, marcada como compartida
#   ("Nombre moderno", obid|None)  -> otra identificación de OpenBible (obid None = el del lugar)
#   ausente    -> la hipótesis no propone lugar (lat/lon null)
L, C = "L", "C"


def paso(texto, ref=None, cita=None, **extra):
    p = {"texto": texto, "ref": ref}
    if cita:
        p["cita"] = cita
    p.update(extra)
    return p


EXODO = [
    dict(nombre="Ramesés", lugar="rameses", ref="Ex 12:37", cita="Y partieron los hijos de Israel de Rameses",
         ub={"tradicional": L, "sin-bishar": C, "har-karkom": C, "al-lawz": C},
         tiempo={"texto": "Mes primero, día 15 (la noche que sigue a la pascua del día 14)", "mes": 1, "dia": 15,
                 "certeza": "calculo", "pasos": [
                     paso("Este mes es el primero del año.", "Ex 12:2", "será este para vosotros el primero en los meses del año"),
                     paso("El cordero se guarda hasta el día 14 y se inmola «entre las dos tardes».", "Ex 12:6",
                          "hasta el día catorce de este mes"),
                     paso("Los panes sin levadura empiezan el día 14 por la tarde.", "Ex 12:18",
                          "el día catorce del mes por la tarde"),
                     paso("A medianoche mueren los primogénitos.", "Ex 12:29", "á la medianoche"),
                     paso("Faraón llama a Moisés y Aarón de noche y los manda salir.", "Ex 12:31",
                          "E hizo llamar á Moisés y á Aarón de noche"),
                     paso("Convención: el día hebreo empieza al ponerse el sol; la noche posterior a la tarde del "
                          "día 14 ya es el día 15. Números 33:3 da expresamente «el día quince del mes primero», "
                          "pero Números no está en los datos y aquí no se verifica.", None, convencion=True)]},
         nota="El texto no dice el día de la salida: dice el día 14 para la pascua y que salieron esa noche."),
    dict(nombre="Sucot", lugar="sucot-egipto", ref="Ex 12:37", cita="de Rameses á Succoth",
         ub={"tradicional": L, "sin-bishar": C, "har-karkom": C, "al-lawz": C}, tiempo=None,
         nota="Distinta de Sucot de Gn 33:17 (al este del Jordán)."),
    dict(nombre="Etam", lugar="etam", ref="Ex 13:20", cita="asentaron campo en Etham, á la entrada del desierto",
         ub={"tradicional": L}, tiempo=None, nota=""),
    dict(nombre="Pi-hahirot", lugar="pi-hahirot", ref="Ex 14:2",
         cita="asienten su campo delante de Pihahiroth, entre Migdol y la mar hacia Baalzephón",
         ub={"tradicional": L}, tiempo=None,
         nota="Entre Migdol y el mar, frente a Baal-zefón. OpenBible da casi el mismo peso a otras propuestas "
              "(p. ej. Tell Defenneh, que identifica con Baal-zefón)."),
    dict(nombre="Cruce del mar", lugar="mar-rojo", ref="Ex 14:22",
         cita="Entonces los hijos de Israel entraron por medio de la mar en seco",
         ub={"tradicional": ("Bitter Lakes", None), "al-lawz": ("Gulf of Aqaba", None)},
         tiempo={"texto": "De noche", "dia": None, "certeza": "texto", "pasos": [
             paso("El viento sopla «toda aquella noche».", "Ex 14:21", "por recio viento oriental toda aquella noche")]},
         nota="Ex 14 dice «la mar»; Ex 15:4 lo llama «mar Bermejo» (yam suf). La identificación mejor puntuada de "
              "OpenBible es el golfo de Suez (369), pero su punto es el centro del golfo, unos 170 km al sur de "
              "Pi-hahirot; para la ruta tradicional se toma la segunda, los lagos Amargos (304). Esta elección es "
              "inferida. Otras propuestas en OpenBible: lago Timsah, lagos de Ballah, lago Manzala, lago Bardawil "
              "(Sirbonis)."),
    dict(nombre="Desierto de Shur", lugar="shur", ref="Ex 15:22", cita="salieron al desierto de Shur",
         ub={"tradicional": L}, tiempo=None, nota="Región; el punto es representativo."),
    dict(nombre="Mara", lugar="mara", ref="Ex 15:23", cita="Y llegaron á Mara",
         ub={"tradicional": L},
         tiempo={"texto": "Tres días después de dejar el mar", "dia": None, "certeza": "calculo", "pasos": [
             paso("Caminan tres días sin agua desde el mar Bermejo.", "Ex 15:22",
                  "anduvieron tres días por el desierto sin hallar agua"),
             paso("Al terminar ese camino llegan a Mara.", "Ex 15:23", "Y llegaron á Mara")]},
         nota="Aguas amargas."),
    dict(nombre="Elim", lugar="elim", ref="Ex 15:27",
         cita="Y llegaron á Elim, donde había doce fuentes de aguas, y setenta palmas",
         ub={"tradicional": L}, tiempo=None, nota=""),
    dict(nombre="Desierto de Sin", lugar="desierto-de-sin", ref="Ex 16:1",
         cita="vino al desierto de Sin, que está entre Elim y Sinaí",
         ub={"tradicional": L},
         tiempo={"texto": "Mes segundo, día 15", "mes": 2, "dia": 15, "certeza": "texto", "pasos": [
             paso("Llegan «á los quince días del segundo mes» desde la salida de Egipto.", "Ex 16:1",
                  "á los quince días del segundo mes después que salieron de la tierra de Egipto")]},
         nota="Región; el punto es representativo."),
    dict(nombre="Refidim", lugar="refidim", ref="Ex 17:1", cita="asentaron el campo en Rephidim",
         ub={"tradicional": L}, tiempo=None, nota="Aquí sitúa el texto el agua de la peña y la batalla con Amalec (Ex 17)."),
    dict(nombre="Desierto y monte Sinaí", lugar="desierto-de-sinai", ref="Ex 19:1",
         cita="vinieron al desierto de Sinaí",
         ub={"tradicional": ("Jebel Musa", OB_SINAI), "sin-bishar": ("Jebel Sin Bishar", OB_SINAI),
             "har-karkom": ("Har Karkom", OB_SINAI), "al-lawz": ("Jabal al Lawz", OB_SINAI)},
         tiempo={"texto": "Mes tercero", "mes": 3, "dia": None, "certeza": "texto", "pasos": [
             paso("Llegan «al mes tercero» de la salida, «en aquel día» (el texto no precisa el día).", "Ex 19:1",
                  "AL mes tercero de la salida de los hijos de Israel de la tierra de Egipto")]},
         nota="Ex 19:2: «acampó allí Israel delante del monte». Las coordenadas son las del monte Sinaí en OpenBible; "
              "no hay consenso y todas van con confianza baja."),
]

ABRAHAM = [
    dict(nombre="Ur de los caldeos", lugar="ur", ref="Gn 11:31", cita="salió con ellos de Ur de los Caldeos",
         ub={"ur-sur": L, "ur-norte": ("Urfa", None)}, tiempo=None,
         nota="Sale Taré con Abram, Sarai y Lot."),
    dict(nombre="Harán", lugar="haran", ref="Gn 11:31", cita="y vinieron hasta Harán, y asentaron allí",
         ub={"ur-sur": L, "ur-norte": C},
         tiempo={"texto": "Abram sale de Harán a los 75 años", "dia": None, "certeza": "texto", "pasos": [
             paso("Taré muere en Harán a los 205 años.", "Gn 11:32", "murió Thare en Harán"),
             paso("Abram tiene 75 años al salir de Harán.", "Gn 12:4",
                  "era Abram de edad de setenta y cinco años cuando salió de Harán")]},
         nota=""),
    dict(nombre="Siquem, valle de More", lugar="siquem", ref="Gn 12:6",
         cita="hasta el lugar de Sichêm, hasta el valle de Moreh", ub={"ur-sur": L, "ur-norte": C}, tiempo=None,
         nota="Primera parada en Canaán."),
    dict(nombre="Entre Betel y Hai", lugar="betel", ref="Gn 12:8", cita="á un monte al oriente de Bethel",
         ub={"ur-sur": L, "ur-norte": C}, tiempo=None,
         nota="El texto dice «teniendo á Bethel al occidente y Hai al oriente»; el punto es el de Betel."),
    dict(nombre="Négueb («el Mediodía»)", lugar=None, ob_lugar=OB_NEGEB, ref="Gn 12:9",
         cita="caminando y yendo hacia el Mediodía",
         ub={"ur-sur": ("Tel Beer Sheva", OB_NEGEB), "ur-norte": C}, tiempo=None,
         nota="La RV1909 dice «el Mediodía» (el Négueb). No está en la lista de lugares de la aplicación; el punto "
              "es el que OpenBible usa para representar la región (coincide con Beerseba)."),
    dict(nombre="Egipto", lugar="egipto", ref="Gn 12:10", cita="descendió Abram á Egipto",
         ub={"ur-sur": L, "ur-norte": C}, tiempo=None,
         nota="País: el punto es el representativo de OpenBible (On/Heliópolis); el texto no dice a qué ciudad fue."),
    dict(nombre="Regreso a Betel", lugar="betel", ref="Gn 13:3",
         cita="hasta el lugar donde había estado antes su tienda entre Bethel y Hai",
         ub={"ur-sur": L, "ur-norte": C}, tiempo=None, nota=""),
    dict(nombre="Mamre, en Hebrón", lugar="mamre", ref="Gn 13:18", cita="moró en el alcornocal de Mamre, que es en Hebrón",
         ub={"ur-sur": L, "ur-norte": C}, tiempo=None, nota=""),
    dict(nombre="Gerar", lugar="gerar", ref="Gn 20:1", cita="habitó como forastero en Gerar",
         ub={"ur-sur": L, "ur-norte": C}, tiempo=None, nota="«Entre Cades y Shur»."),
    dict(nombre="Beerseba", lugar="beerseba", ref="Gn 21:33", cita="Y plantó [Abraham] un bosque en Beer-seba",
         ub={"ur-sur": L, "ur-norte": C}, tiempo=None, nota="El nombre del lugar se explica en Gn 21:31."),
    dict(nombre="Tierra de Moriah", lugar="moriah", ref="Gn 22:2", cita="vete á tierra de Moriah",
         ub={"ur-sur": L, "ur-norte": C}, tiempo=None,
         nota="El texto no dice qué monte; la identificación con el monte del templo de Jerusalén es tradicional "
              "(OpenBible, confianza media)."),
    dict(nombre="Regreso a Beerseba", lugar="beerseba", ref="Gn 22:19", cita="y habitó Abraham en Beer-seba",
         ub={"ur-sur": L, "ur-norte": C}, tiempo=None, nota=""),
    dict(nombre="Hebrón (Quiriat-arba)", lugar="hebron", ref="Gn 23:2", cita="murió Sara en Kiriath-arba, que es Hebrón",
         ub={"ur-sur": L, "ur-norte": C}, tiempo=None, nota="Muere Sara; Abraham compra la cueva de Macpela (Gn 23)."),
    dict(nombre="Cueva de Macpela", lugar="macpela", ref="Gn 25:9", cita="en la cueva de Macpela",
         ub={"ur-sur": L, "ur-norte": C},
         tiempo={"texto": "Abraham muere a los 175 años", "dia": None, "certeza": "texto", "pasos": [
             paso("Edad de Abraham al morir.", "Gn 25:7", "ciento setenta y cinco años")]},
         nota="Lo sepultan Isaac e Ismael «enfrente de Mamre»."),
]

T = {"openbible": L}
JACOB = [
    dict(nombre="Beerseba", lugar="beerseba", ref="Gn 28:10", cita="Y salió Jacob de Beer-seba, y fué á Harán",
         ub=T, tiempo=None, nota=""),
    dict(nombre="Betel", lugar="betel", ref="Gn 28:19", cita="llamó el nombre de aquel lugar Beth-el",
         ub=T, tiempo=None, nota="El sueño de la escalera; antes se llamaba Luz."),
    dict(nombre="Harán", lugar="haran", ref="Gn 29:4", cita="De Harán somos", ub=T, tiempo=None,
         nota="Jacob sirve a Labán; se casa con Lea y Raquel."),
    dict(nombre="Monte de Galaad", lugar="galaad", ref="Gn 31:21", cita="puso su rostro al monte de Galaad", ub=T,
         tiempo={"texto": "Tras veinte años en casa de Labán", "dia": None, "certeza": "texto", "pasos": [
             paso("Jacob dice a Labán cuánto tiempo le sirvió.", "Gn 31:41", "Así he estado veinte años en tu casa")]},
         nota="Labán lo alcanza allí (Gn 31:25). Región: el punto es representativo."),
    dict(nombre="Mahanaim", lugar="mahanaim", ref="Gn 32:2", cita="llamó el nombre de aquel lugar Mahanaim", ub=T,
         tiempo=None, nota=""),
    dict(nombre="Peniel", lugar="peniel", ref="Gn 32:30", cita="Y llamó Jacob el nombre de aquel lugar, Peniel", ub=T,
         tiempo=None, nota="Junto al vado de Jaboc (Gn 32:22). OpenBible usa el mismo punto para Galaad."),
    dict(nombre="Sucot", lugar="sucot", ref="Gn 33:17", cita="Y Jacob se partió á Succoth", ub=T, tiempo=None,
         nota="Al este del Jordán; distinta de Sucot de Ex 12:37."),
    dict(nombre="Siquem", lugar="siquem", ref="Gn 33:18", cita="Y vino Jacob sano á la ciudad de Sichêm", ub=T,
         tiempo=None, nota=""),
    dict(nombre="Betel", lugar="betel", ref="Gn 35:6", cita="Y llegó Jacob á Luz", ub=T, tiempo=None,
         nota="«esta es Beth-el»."),
    dict(nombre="Efrata (Belén)", lugar="efrata", ref="Gn 35:19", cita="en el camino de Ephrata, la cual es Beth-lehem",
         ub=T, tiempo=None, nota="Muere Raquel al dar a luz a Benjamín."),
    dict(nombre="Mamre, Hebrón", lugar="mamre", ref="Gn 35:27", cita="Y vino Jacob á Isaac su padre á Mamre", ub=T,
         tiempo=None, nota="«á la ciudad de Arba, que es Hebrón»."),
    dict(nombre="Beerseba", lugar="beerseba", ref="Gn 46:1", cita="vino á Beer-seba", ub=T, tiempo=None,
         nota="Camino de Egipto."),
    dict(nombre="Gosén, en Egipto", lugar="gosen", ref="Gn 46:28", cita="y llegaron á la tierra de Gosén", ub=T,
         tiempo={"texto": "Jacob tiene 130 años ante Faraón", "dia": None, "certeza": "texto", "pasos": [
             paso("Entran en Egipto.", "Gn 46:6", "viniéronse á Egipto"),
             paso("Jacob dice su edad a Faraón.", "Gn 47:9", "ciento treinta años")]},
         nota="Región: el punto es representativo."),
]

RECORRIDOS = [
    {"id": "exodo", "titulo": "De Egipto al Sinaí", "libro": "Ex",
     "personas": ["Moses_1", "Aaron_1", "Miriam_1", "Joshua_1", "Hur_1"],
     "resumen": "Itinerario de Ex 12–19: de Ramesés al desierto de Sinaí, con las fechas que da el texto (mes "
                "primero, día 15 del mes segundo, mes tercero) y cuatro hipótesis sobre dónde está el monte.",
     "hipotesis": HIP_EXODO, "etapas": EXODO},
    {"id": "abraham", "titulo": "Los caminos de Abraham", "libro": "Gn",
     "personas": ["Terah_1", "Abram_1", "Sarai_1", "Lot_1"],
     "resumen": "De Ur de los caldeos a Harán, Canaán, Egipto y de vuelta al Négueb y Hebrón (Gn 11–25), "
                "con dos hipótesis sobre Ur.",
     "hipotesis": HIP_ABRAHAM, "etapas": ABRAHAM},
    {"id": "jacob", "titulo": "Los viajes de Jacob", "libro": "Gn",
     "personas": ["Jacob_1", "Leah_1", "Rachel_1"],
     "resumen": "De Beerseba a Harán y vuelta a Canaán por Galaad, Peniel y Siquem; después Betel, Belén, Hebrón y "
                "la bajada a Gosén (Gn 28–46).",
     "hipotesis": HIP_JACOB, "etapas": JACOB},
]


# --------------------------------------------------------------------------- utilidades
def cargar_js(ruta):
    s = ruta.read_text(encoding="utf-8")
    return json.loads(s[s.index("{"):s.rindex("}") + 1])


def clave_ref(ref):
    m = re.fullmatch(r"(Gn|Ex) (\d+):(\d+)", ref or "")
    if not m:
        raise ValueError(f"Referencia mal formada: {ref!r}")
    return (["Gn", "Ex"].index(m.group(1)), int(m.group(2)), int(m.group(3)))


def confianza(score, obid):
    if obid in SINAI_OB:
        return "baja"
    return "alta" if score >= UMBRAL_ALTA else "media" if score >= UMBRAL_MEDIA else "baja"


def leer_openbible():
    anc, mod = {}, {}
    for linea in (CACHE / "ob_ancient.jsonl").open(encoding="utf-8"):
        d = json.loads(linea)
        anc[d["id"]] = d
    for linea in (CACHE / "ob_modern.jsonl").open(encoding="utf-8"):
        d = json.loads(linea)
        mod[d["id"]] = d
    return anc, mod


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    errores = []
    if not (CACHE / "ob_ancient.jsonl").exists() or not (CACHE / "ob_modern.jsonl").exists():
        print("Falta la caché de OpenBible: ejecuta antes python -I herramientas/construir_datos.py", file=sys.stderr)
        return 2
    datos = cargar_js(DATOS / "biblia.js")
    anc, mod = leer_openbible()
    V = {f'{c["libro"]} {c["cap"]}:{v["n"]}': v["texto"] for c in datos["capitulos"] for v in c["versiculos"]}
    lugares = {l["id"]: l for l in datos["lugares"]}
    personas = {p["id"] for p in datos["personas"]}

    def comprobar_cita(ref, cita, donde):
        if ref not in V:
            errores.append(f"{donde}: no existe el versículo {ref}")
        elif cita not in V[ref]:
            errores.append(f"{donde}: la cita «{cita}» no es literal de {ref}: «{V[ref]}»")

    def ubicar(obid, nombre, donde):
        """Coordenadas y puntuación de la identificación «nombre» del lugar antiguo obid (OpenBible)."""
        a = anc.get(obid)
        if not a:
            errores.append(f"{donde}: OpenBible no tiene el lugar antiguo {obid}")
            return None
        hits = [(mid, ma) for mid, ma in a.get("modern_associations", {}).items() if ma["name"] == nombre]
        if len(hits) != 1:
            errores.append(f"{donde}: «{nombre}» no es una identificación única de {a['friendly_id']} en OpenBible")
            return None
        mid, ma = hits[0]
        if mid not in mod or not mod[mid].get("lonlat"):
            errores.append(f"{donde}: «{nombre}» ({mid}) sin coordenadas en ob_modern.jsonl")
            return None
        lon, lat = map(float, mod[mid]["lonlat"].split(","))
        return {"lat": round(lat, 4), "lon": round(lon, 4), "confianza": confianza(ma["score"], obid),
                "identificacion": nombre, "puntuacion_openbible": ma["score"],
                "fuente": OB_FUENTE + f": {a['friendly_id']} → {nombre}",
                "url": f"https://www.openbible.info/geo/ancient/{obid}/{a.get('url_slug', '')}"}

    salida = []
    for rec in RECORRIDOS:
        rid = rec["id"]
        hips = rec["hipotesis"]
        hids = [h["id"] for h in hips]
        defecto = [h["id"] for h in hips if h.get("defecto")]
        if len(defecto) != 1:
            errores.append(f"{rid}: debe haber exactamente una hipótesis por defecto ({defecto})")
            continue
        hdef = defecto[0]
        if len(set(hids)) != len(hids):
            errores.append(f"{rid}: ids de hipótesis repetidos")
        for h in hips:
            if not h.get("fuente") or not str(h.get("url", "")).startswith("https://"):
                errores.append(f"{rid}/{h['id']}: hipótesis sin fuente o url")
        for p in rec["personas"]:
            if p not in personas:
                errores.append(f"{rid}: persona inexistente {p}")
        etapas = []
        anterior = None
        for n, e in enumerate(rec["etapas"], 1):
            donde = f"{rid} etapa {n} ({e['nombre']})"
            comprobar_cita(e["ref"], e["cita"], donde)
            k = clave_ref(e["ref"])
            if anterior and k < anterior:
                errores.append(f"{donde}: {e['ref']} va antes que la etapa anterior")
            anterior = k
            lug = lugares.get(e["lugar"]) if e["lugar"] else None
            if e["lugar"] and not lug:
                errores.append(f"{donde}: el lugar «{e['lugar']}» no existe en biblia.js")
                continue
            if lug:
                m = re.search(r"/ancient/([0-9a-f]+)/", lug.get("url_fuente") or "")
                ob_lugar = m.group(1) if m else None
                ident_def = (lug.get("ubicacion") or {}).get("identificacion")
            else:
                ob_lugar, ident_def = e.get("ob_lugar"), None
            spec = e["ub"]
            for h in spec:
                if h not in hids:
                    errores.append(f"{donde}: hipótesis desconocida {h}")
            ub, sin = {}, []
            orden = [hdef] + [h for h in hids if h != hdef]
            for h in orden:
                s = spec.get(h)
                if s == L:
                    if not (ob_lugar and ident_def):
                        errores.append(f"{donde}: el lugar no tiene identificación por defecto")
                        continue
                    u = ubicar(ob_lugar, ident_def, donde)
                    if u and (u["lat"], u["lon"]) != (lug["ubicacion"]["lat"], lug["ubicacion"]["lon"]):
                        errores.append(f"{donde}: coordenadas distintas de biblia.js para {ident_def}")
                elif s == C:
                    base = ub.get(hdef)
                    if not base or base["lat"] is None:
                        errores.append(f"{donde}: «común» sin ubicación por defecto")
                        continue
                    u = dict(base, identificacion=base["identificacion"] + " (común a todas las hipótesis)")
                elif isinstance(s, tuple):
                    u = ubicar(s[1] or ob_lugar, s[0], donde)
                else:
                    hh = next(x for x in hips if x["id"] == h)
                    u = {"lat": None, "lon": None, "confianza": "baja",
                         "identificacion": "Sin identificación propuesta en esta hipótesis",
                         "fuente": hh["fuente"], "url": hh["url"]}
                    sin.append(hh["nombre"])
                if u:
                    ub[h] = u
            if hdef not in ub or ub[hdef]["lat"] is None:
                errores.append(f"{donde}: sin ubicación en la hipótesis por defecto «{hdef}»")
            for u in ub.values():
                if u["confianza"] not in ("alta", "media", "baja"):
                    errores.append(f"{donde}: confianza inválida")
            tiempo = e["tiempo"]
            if tiempo:
                if tiempo["certeza"] not in ("texto", "calculo"):
                    errores.append(f"{donde}: certeza de tiempo inválida")
                if not tiempo.get("pasos"):
                    errores.append(f"{donde}: tiempo sin pasos")
                for p in tiempo.get("pasos", []):
                    if p.get("ref"):
                        comprobar_cita(p["ref"], p.get("cita", ""), donde + " (tiempo)")
                        if not p.get("cita"):
                            errores.append(f"{donde}: paso de tiempo con ref y sin cita")
                    elif not p.get("convencion"):
                        errores.append(f"{donde}: paso de tiempo sin versículo que no está marcado como convención")
                if tiempo["certeza"] == "texto" and not any(p.get("ref") for p in tiempo["pasos"]):
                    errores.append(f"{donde}: certeza «texto» sin versículo")
            nota = e.get("nota", "")
            if sin:
                nota = (nota + " " if nota else "") + "Sin ubicación propuesta en: " + "; ".join(sin) + "."
            confs = {u["confianza"] for u in ub.values() if u["lat"] is not None}
            if "baja" in confs and "confianza baja" not in nota:
                nota = (nota + " " if nota else "") + "Alguna identificación va con confianza baja (dudosa)."
            etapas.append({"orden": n, "lugar": e["lugar"], "nombre": e["nombre"], "ref": e["ref"], "cita": e["cita"],
                           "tiempo": tiempo, "ubicaciones": ub, "nota": nota})
        salida.append({k: rec[k] for k in ("id", "titulo", "libro", "personas", "resumen", "hipotesis")} | {"etapas": etapas})

    if not any(r["id"] == "exodo" for r in salida):
        errores.append("Falta el recorrido obligatorio «exodo»")
    if errores:
        print("ERRORES:", file=sys.stderr)
        for e in errores:
            print(" -", e, file=sys.stderr)
        return 1

    doc = {"generado": datetime.now(timezone.utc).isoformat(timespec="seconds"), "fuentes": FUENTES,
           "recorridos": salida}
    SALIDA.write_text("window.BIBLIA_RECORRIDOS = " + json.dumps(doc, ensure_ascii=False, indent=1) + ";\n",
                      encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"Escrito {SALIDA.relative_to(RAIZ)}")
    for r in salida:
        print(f"  {r['id']}: {len(r['etapas'])} etapas, {len(r['hipotesis'])} hipótesis "
              f"({', '.join(h['id'] for h in r['hipotesis'])})")
        for e in r["etapas"]:
            u = e["ubicaciones"]
            desc = " | ".join(f"{h}: {v['identificacion'].replace(' (común a todas las hipótesis)', ' (común)')}"
                              f" {v['confianza'] if v['lat'] is not None else '—'}" for h, v in u.items())
            t = f" [{e['tiempo']['certeza']}: {e['tiempo']['texto']}]" if e["tiempo"] else ""
            print(f"    {e['orden']:>2}. {e['ref']:<9} {e['nombre']}{t}  ·  {desc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
