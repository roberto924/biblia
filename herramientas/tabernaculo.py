"""Genera datos/tabernaculo.js (window.BIBLIA_TABERNACULO) a partir del texto RV1909 de datos/biblia.js.

Sin red. Regenerar: python -I herramientas/tabernaculo.py
Verifica (sale con código != 0 y no escribe nada si algo falla):
- cada `cita` es substring literal del versículo de su `ref`;
- las medidas y cantidades con certeza "texto" están escritas (en palabras) en su cita;
- cada cálculo cuadra (la operación da el resultado y sus cifras salen de los pasos);
- toda pieza tiene instrucción y construcción con versículos existentes;
- `montaje` va en orden no decreciente de versículos dentro de Ex 40:17-33.
"""
import ast
import datetime
import json
import operator
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"
SALIDA = DATOS / "tabernaculo.js"

URL_RV = "https://ebible.org/find/details.php?id=spaRV1909"
URL_RASHI = "https://www.sefaria.org/Rashi_on_Exodus.26"


def m(codos, ref, cita, certeza="texto", **extra):
    d = {"codos": codos, "ref": ref, "cita": cita, "certeza": certeza}
    d.update(extra)
    return d


def c(nombre, ref, cita):
    return {"nombre": nombre, "ref": ref, "cita": cita}


def p(texto, ref=None, cita=None, **extra):
    d = {"texto": texto, "ref": ref, "cita": cita}
    d.update(extra)
    return d


# --------------------------------------------------------------------------- codos y fuentes
CODOS = [
    {"id": "comun", "nombre": "codo común", "cm": 44.5, "defecto": True,
     "fuente": "Fuente externa: «Cubit», Insight on the Scriptures (Watch Tower, diccionario bíblico)",
     "url": "https://www.jw.org/en/library/books/Insight-on-the-Scriptures/Cubit/",
     "cita_fuente": "commonly used a cubit of about 44.5 cm (17.5 in.)",
     "nota": "Valor aproximado; el texto bíblico no define el codo en centímetros. La misma obra da ~51,8 cm "
             "para el codo largo de Ezequiel 40:5 (codo + un palmo). Consultada el 2026-11-11."},
    {"id": "real", "nombre": "codo real (largo)", "cm": 52.5,
     "fuente": "Fuente externa: Wikipedia (inglés), «Biblical and Talmudic units of measurement»",
     "url": "https://en.wikipedia.org/wiki/Biblical_and_Talmudic_units_of_measurement",
     "cita_fuente": "the larger Egyptian cubit was between 52.5 and 52.8 cm",
     "nota": "52,5 cm es el extremo inferior del codo egipcio largo (real); la misma página dice que no se sabe "
             "si el codo bíblico estándar era de 49,5 o de 52,5 cm. Fuente secundaria. Consultada el 2026-11-11."},
]

FUENTES = [
    {"id": "rv1909", "nombre": "Reina-Valera 1909", "tipo": "texto", "licencia": "dominio público", "url": URL_RV,
     "nota": "Todas las citas son literales del texto de datos/biblia.js."},
    {"id": "insight", "nombre": "Insight on the Scriptures, «Cubit»", "tipo": "Fuente externa",
     "url": CODOS[0]["url"], "uso": "equivalencia del codo común (44,5 cm)"},
    {"id": "wikipedia-unidades", "nombre": "Wikipedia (inglés), «Biblical and Talmudic units of measurement»",
     "tipo": "Fuente externa", "url": CODOS[1]["url"], "uso": "equivalencia del codo real (52,5 cm)"},
    {"id": "rashi", "nombre": "Rashi (s. XI), comentario a Éxodo 26, traducción inglesa en Sefaria",
     "tipo": "Fuente externa (tradición judía)", "url": URL_RASHI,
     "uso": "ancho interior de 10 codos (Rashi a Ex 26:5 y 26:23: tablas de un codo de grueso y esquinas que "
            "completan los 10 codos), lugar santo de 20 codos y santísimo de 10×10 (Rashi a Ex 26:32 y 26:35)."},
]

RASHI = "Rashi (Fuente externa, tradición)"

ORIENTACION = {
    "texto": "La entrada del atrio (y del tabernáculo) mira al oriente; el fondo del tabernáculo, al occidente. "
             "El lado largo sur es «el mediodía» (austro) y el norte «el aquilón».",
    "ref": "Ex 27:13", "cita": "por la parte de levante, al oriente",
    "otras": [p("Fondo del tabernáculo al occidente", "Ex 26:22", "al occidente, harás seis tablas"),
              p("Lado sur", "Ex 26:18", "veinte tablas al lado del mediodía, al austro"),
              p("Lado norte", "Ex 26:20", "á la parte del aquilón, veinte tablas")],
    "plano": "Coordenadas en codos; origen en la esquina suroeste del atrio; x hacia el oriente, y hacia el norte. "
             "rot en grados: 0 = eje largo de la pieza de oeste a este; 90 = de sur a norte.",
}

# --------------------------------------------------------------------------- cálculos
CALCULOS = [
    {"id": "largo-tabernaculo", "texto": "20 tablas × 1½ codos = 30 codos de largo del tabernáculo",
     "operacion": "20*1.5", "resultado": 30, "certeza": "calculo",
     "pasos": [p("20 tablas en el lado sur", "Ex 26:18", "veinte tablas al lado del mediodía", valor=20),
               p("cada tabla mide codo y medio de ancho", "Ex 26:16", "de codo y medio la anchura de cada tabla", valor=1.5)]},
    {"id": "pared-occidental", "texto": "6 tablas × 1½ codos = 9 codos en el fondo (sin las esquinas)",
     "operacion": "6*1.5", "resultado": 9, "certeza": "calculo",
     "pasos": [p("6 tablas al occidente", "Ex 26:22", "harás seis tablas", valor=6),
               p("cada tabla mide codo y medio de ancho", "Ex 26:16", "de codo y medio la anchura de cada tabla", valor=1.5)]},
    {"id": "ancho-interior", "texto": "9 codos + 2 esquinas × ½ codo = 10 codos de ancho interior (tradición)",
     "operacion": "9+2*0.5", "resultado": 10, "certeza": "tradicion",
     "nota": "El texto no da el ancho del tabernáculo. Los 10 codos son la lectura de Rashi: tablas de un codo de "
             "grueso; cada tabla de esquina añade medio codo al interior. Otras reconstrucciones dan 12 codos por fuera.",
     "pasos": [p("fondo sin esquinas", calculo="pared-occidental", valor=9),
               p("dos tablas de esquina", "Ex 26:23", "dos tablas para las esquinas", valor=2),
               p("cada esquina añade medio codo al interior", fuente=RASHI, url=URL_RASHI + ".23", valor=0.5,
                 nota="Rashi a Ex 26:23: «thus making up the breadth to ten cubits»")]},
    {"id": "tablas-total", "texto": "20 + 20 + 6 + 2 = 48 tablas",
     "operacion": "20+20+6+2", "resultado": 48, "certeza": "calculo",
     "pasos": [p("lado sur", "Ex 26:18", "veinte tablas al lado del mediodía", valor=20),
               p("lado norte", "Ex 26:20", "veinte tablas", valor=20),
               p("occidente", "Ex 26:22", "harás seis tablas", valor=6),
               p("esquinas", "Ex 26:23", "dos tablas para las esquinas", valor=2),
               p("el texto suma el occidente con las esquinas", "Ex 26:25", "serán ocho tablas", valor=8)]},
    {"id": "basas-tablas", "texto": "40 + 40 + 16 = 96 basas de plata bajo las tablas",
     "operacion": "40+40+16", "resultado": 96, "certeza": "calculo",
     "pasos": [p("sur", "Ex 26:19", "cuarenta basas de plata", valor=40),
               p("norte", "Ex 26:21", "sus cuarenta basas de plata", valor=40),
               p("occidente y esquinas", "Ex 26:25", "diez y seis basas", valor=16)]},
    {"id": "basas-por-tabla", "texto": "48 tablas × 2 basas = 96 basas (comprobación)",
     "operacion": "48*2", "resultado": 96, "certeza": "calculo",
     "pasos": [p("total de tablas", calculo="tablas-total", valor=48),
               p("dos basas por tabla", "Ex 26:19", "dos basas debajo de la una tabla", valor=2)]},
    {"id": "barras", "texto": "5 + 5 + 5 = 15 barras",
     "operacion": "5+5+5", "resultado": 15, "certeza": "calculo",
     "nota": "Si la barra del medio (Ex 26:28) es una de las cinco de cada lado o una más, el texto no lo precisa.",
     "pasos": [p("un lado", "Ex 26:26", "cinco barras de madera de Sittim", valor=5),
               p("el otro lado", "Ex 26:27", "cinco barras para las tablas del otro lado", valor=5),
               p("occidente", "Ex 26:27", "cinco barras para el otro lado del tabernáculo, que está al occidente", valor=5)]},
    {"id": "columnas-tabernaculo", "texto": "4 columnas del velo + 5 de la entrada = 9 columnas",
     "operacion": "4+5", "resultado": 9, "certeza": "calculo",
     "pasos": [p("velo", "Ex 26:32", "cuatro columnas de madera de Sittim", valor=4),
               p("cortina de la entrada", "Ex 26:37", "cinco columnas de madera de Sittim", valor=5)]},
    {"id": "lino-ancho", "texto": "10 cortinas × 4 codos = 40 codos de ancho unidas",
     "operacion": "10*4", "resultado": 40, "certeza": "calculo",
     "pasos": [p("diez cortinas", "Ex 26:1", "diez cortinas de lino torcido", valor=10),
               p("cuatro codos de ancho cada una", "Ex 26:2", "la anchura de la misma cortina de cuatro codos", valor=4)]},
    {"id": "lino-largo-total", "texto": "10 cortinas × 28 codos = 280 codos de cortina de lino",
     "operacion": "10*28", "resultado": 280, "certeza": "calculo",
     "pasos": [p("diez cortinas", "Ex 26:1", "diez cortinas de lino torcido", valor=10),
               p("28 codos de largo cada una", "Ex 26:2", "La longitud de la una cortina de veintiocho codos", valor=28)]},
    {"id": "lino-grupo", "texto": "5 cortinas × 4 codos = 20 codos cada mitad unida por los corchetes",
     "operacion": "5*4", "resultado": 20, "certeza": "calculo",
     "pasos": [p("dos grupos de cinco", "Ex 26:3", "Cinco cortinas estarán juntas", valor=5),
               p("cuatro codos de ancho", "Ex 26:2", "la anchura de la misma cortina de cuatro codos", valor=4),
               p("los grupos se unen con corchetes", "Ex 26:6", "cincuenta corchetes de oro", valor=50)]},
    {"id": "cabra-ancho", "texto": "11 cortinas × 4 codos = 44 codos de ancho unidas",
     "operacion": "11*4", "resultado": 44, "certeza": "calculo",
     "pasos": [p("once cortinas", "Ex 26:7", "once cortinas harás", valor=11),
               p("cuatro codos de ancho", "Ex 26:8", "la anchura de la misma cortina de cuatro codos", valor=4)]},
    {"id": "cabra-sobrante", "texto": "44 − 40 = 4 codos más que las de lino (una cortina)",
     "operacion": "44-40", "resultado": 4, "certeza": "calculo",
     "pasos": [p("pelo de cabra", calculo="cabra-ancho", valor=44),
               p("lino", calculo="lino-ancho", valor=40),
               p("la sexta se dobla delante", "Ex 26:9", "doblarás la sexta cortina delante de la faz del tabernáculo"),
               p("media cortina sobra detrás", "Ex 26:12", "la mitad de la una cortina que sobra, quedará á las espaldas del tabernáculo")]},
    {"id": "cabra-largo", "texto": "30 − 28 = 2 codos: uno de más a cada lado",
     "operacion": "30-28", "resultado": 2, "certeza": "calculo",
     "pasos": [p("pelo de cabra: 30 codos", "Ex 26:8", "La longitud de la una cortina será de treinta codos", valor=30),
               p("lino: 28 codos", "Ex 26:2", "La longitud de la una cortina de veintiocho codos", valor=28),
               p("el texto lo confirma: un codo por cada lado", "Ex 26:13", "un codo de la una parte, y otro codo de la otra", valor=1)]},
    {"id": "largo-santo", "texto": "Lugar santo: 5 cortinas × 4 codos = 20 codos desde la entrada hasta el velo",
     "operacion": "5*4", "resultado": 20, "certeza": "inferido",
     "nota": "El texto no da el largo del lugar santo. Sale de colgar el velo bajo los corchetes, suponiendo que las "
             "cortinas de lino empiezan en la entrada. Rashi (Ex 26:32-35) da también 20 codos.",
     "pasos": [p("el velo cuelga bajo los corchetes", "Ex 26:33", "pondrás el velo debajo de los corchetes"),
               p("primer grupo de cinco cortinas", "Ex 26:3", "Cinco cortinas estarán juntas", valor=5),
               p("cuatro codos cada una", "Ex 26:2", "la anchura de la misma cortina de cuatro codos", valor=4),
               p("supuesto: las cortinas empiezan en la entrada (oriente)", supuesto=True),
               p("Rashi llega a los mismos 20 codos", fuente=RASHI, url=URL_RASHI + ".35",
                 nota="Rashi a Ex 26:35: «from the entrance to the partition veil was 20 cubits»")]},
    {"id": "largo-santisimo", "texto": "Lugar santísimo: 30 − 20 = 10 codos",
     "operacion": "30-20", "resultado": 10, "certeza": "inferido",
     "pasos": [p("largo del tabernáculo", calculo="largo-tabernaculo", valor=30),
               p("largo del lugar santo (inferido)", calculo="largo-santo", valor=20)]},
    {"id": "alto-tabernaculo", "texto": "Altura: tablas de 10 codos puestas derechas = 10 codos",
     "operacion": "10", "resultado": 10, "certeza": "inferido",
     "pasos": [p("tablas derechas", "Ex 26:15", "que estén derechas"),
               p("10 codos de largo cada tabla", "Ex 26:16", "La longitud de cada tabla será de diez codos", valor=10)]},
    {"id": "atrio-oriente", "texto": "Lado oriental: 15 + 20 + 15 = 50 codos (cortinas, puerta, cortinas)",
     "operacion": "15+20+15", "resultado": 50, "certeza": "calculo",
     "pasos": [p("cortinas de un lado", "Ex 27:14", "serán de quince codos", valor=15),
               p("puerta", "Ex 27:16", "un pabellón de veinte codos", valor=20),
               p("cortinas del otro lado", "Ex 27:15", "Al otro lado quince codos de cortinas", valor=15),
               p("el lado oriental mide 50", "Ex 27:13", "habrá cincuenta codos", valor=50)]},
    {"id": "atrio-perimetro", "texto": "Perímetro del atrio: 100 + 100 + 50 + 50 = 300 codos",
     "operacion": "100+100+50+50", "resultado": 300, "certeza": "calculo",
     "pasos": [p("sur", "Ex 27:9", "cien codos de longitud", valor=100),
               p("norte", "Ex 27:11", "cortinas de cien codos de longitud", valor=100),
               p("occidente", "Ex 27:12", "cortinas de cincuenta codos", valor=50),
               p("oriente", "Ex 27:13", "habrá cincuenta codos", valor=50)]},
    {"id": "atrio-cortinas", "texto": "Cortinas de lino del atrio: 100 + 100 + 50 + 15 + 15 = 280 codos (más 20 de la puerta)",
     "operacion": "100+100+50+15+15", "resultado": 280, "certeza": "calculo",
     "pasos": [p("sur", "Ex 27:9", "cien codos de longitud", valor=100),
               p("norte", "Ex 27:11", "cortinas de cien codos de longitud", valor=100),
               p("occidente", "Ex 27:12", "cortinas de cincuenta codos", valor=50),
               p("oriente, un lado", "Ex 27:14", "serán de quince codos", valor=15),
               p("oriente, otro lado", "Ex 27:15", "quince codos de cortinas", valor=15)]},
    {"id": "atrio-area", "texto": "Superficie del atrio: 100 × 50 = 5000 codos cuadrados",
     "operacion": "100*50", "resultado": 5000, "certeza": "calculo",
     "pasos": [p("largo", "Ex 27:18", "La longitud del atrio será de cien codos", valor=100),
               p("ancho", "Ex 27:18", "la anchura cincuenta", valor=50)]},
    {"id": "columnas-atrio", "texto": "Columnas del atrio: 20 + 20 + 10 + 3 + 3 + 4 = 60",
     "operacion": "20+20+10+3+3+4", "resultado": 60, "certeza": "calculo",
     "nota": "Suma directa de las cifras del texto; si las columnas de las esquinas se cuentan dos veces, el número "
             "real sería menor. El texto no lo aclara.",
     "pasos": [p("sur", "Ex 27:10", "Sus veinte columnas", valor=20),
               p("norte", "Ex 27:11", "sus veinte columnas", valor=20),
               p("occidente", "Ex 27:12", "sus columnas diez", valor=10),
               p("oriente, un lado", "Ex 27:14", "sus columnas tres", valor=3),
               p("oriente, otro lado", "Ex 27:15", "sus columnas tres", valor=3),
               p("puerta", "Ex 27:16", "sus columnas cuatro", valor=4)]},
]

# --------------------------------------------------------------------------- zonas
ZONAS = [
    {"id": "atrio", "nombre": "Atrio",
     "largo": m(100, "Ex 27:18", "La longitud del atrio será de cien codos"),
     "ancho": m(50, "Ex 27:18", "la anchura cincuenta por un lado y cincuenta por el otro"),
     "alto": m(5, "Ex 27:18", "la altura de cinco codos"),
     "plano": {"x0": 0, "y0": 0, "x1": 100, "y1": 50, "certeza": "texto",
               "nota": "Medidas del texto; el origen es una convención del plano."},
     "nota": "Largo de oeste a este (lados sur y norte de 100 codos, Ex 27:9-11)."},
    {"id": "santo", "nombre": "Lugar santo",
     "largo": m(20, "Ex 26:33", "pondrás el velo debajo de los corchetes", "inferido", calculo="largo-santo"),
     "ancho": m(10, None, None, "tradicion", calculo="ancho-interior", fuente=RASHI),
     "alto": m(10, "Ex 26:16", "La longitud de cada tabla será de diez codos", "inferido", calculo="alto-tabernaculo"),
     "plano": {"x0": 30, "y0": 20, "x1": 50, "y1": 30, "certeza": "inferido",
               "nota": "El texto no dice dónde está el tabernáculo dentro del atrio. Supuesto de dibujo: centrado de "
                       "norte a sur y con el fondo a 20 codos del lado occidental."},
     "nota": "El texto no da sus dimensiones: 20 codos de largo es un cálculo con un supuesto; 10 de ancho, tradición (Rashi)."},
    {"id": "santisimo", "nombre": "Lugar santísimo",
     "largo": m(10, None, None, "inferido", calculo="largo-santisimo"),
     "ancho": m(10, None, None, "tradicion", calculo="ancho-interior", fuente=RASHI),
     "alto": m(10, "Ex 26:16", "La longitud de cada tabla será de diez codos", "inferido", calculo="alto-tabernaculo"),
     "plano": {"x0": 20, "y0": 20, "x1": 30, "y1": 30, "certeza": "inferido",
               "nota": "Mismo supuesto de dibujo que el lugar santo."},
     "nota": "Separado del lugar santo por el velo (Ex 26:33). Un cubo de 10 codos es la lectura tradicional "
             "(Rashi a Ex 26:32), no está escrito."},
]

# --------------------------------------------------------------------------- piezas
ZT = lambda id_, ref, cita, certeza="texto", nota=None: {"id": id_, "certeza": certeza, "ref": ref, "cita": cita, "nota": nota}
PI = lambda x, y, certeza="inferido", nota=None, **k: dict({"x": x, "y": y, "certeza": certeza, "nota": nota}, **k)
SUP = "Coordenada de dibujo dentro de su zona (supuesto)."

PIEZAS = [
    {"id": "arca", "nombre": "Arca del testimonio", "grupo": "mobiliario",
     "instruccion": "Ex 25:10-16", "construccion": "Ex 37:1-5",
     "medidas": {"largo": m(2.5, "Ex 25:10", "cuya longitud será de dos codos y medio"),
                 "ancho": m(1.5, "Ex 25:10", "su anchura de codo y medio"),
                 "alto": m(1.5, "Ex 25:10", "su altura de codo y medio")},
     "materiales": [c("madera de Sittim", "Ex 25:10", "un arca de madera de Sittim"),
                    c("oro puro (por dentro y por fuera)", "Ex 25:11", "la cubrirás de oro puro"),
                    c("cuatro anillos de oro", "Ex 25:12", "cuatro anillos de oro"),
                    c("varas de Sittim cubiertas de oro", "Ex 25:13", "harás unas varas de madera de Sittim")],
     "zona": ZT("santisimo", "Ex 26:33", "meterás allí, del velo adentro, el arca del testimonio"),
     "plano": PI(25, 25, nota="Centro del santísimo. " + SUP,
                 relacion=[p("detrás del velo", "Ex 26:33", "del velo adentro")]),
     "funcion": p("Guardar el testimonio", "Ex 25:16", "pondrás en el arca el testimonio"),
     "nota": "Las varas no se quitan del arca (Ex 25:15)."},
    {"id": "propiciatorio", "nombre": "Propiciatorio (cubierta) con dos querubines", "grupo": "mobiliario",
     "instruccion": "Ex 25:17-22", "construccion": "Ex 37:6-9",
     "medidas": {"largo": m(2.5, "Ex 25:17", "cuya longitud [será] de dos codos y medio"),
                 "ancho": m(1.5, "Ex 25:17", "su anchura de codo y medio")},
     "cantidad": {"valor": 1, "ref": "Ex 25:17", "cita": "una cubierta de oro fino", "certeza": "texto"},
     "materiales": [c("oro fino", "Ex 25:17", "una cubierta de oro fino"),
                    c("dos querubines de oro labrados a martillo", "Ex 25:18", "dos querubines de oro, labrados á martillo")],
     "detalles": [p("Querubines en los dos extremos, alas extendidas, caras uno frente al otro", "Ex 25:20",
                    "sus caras la una enfrente de la otra")],
     "zona": ZT("santisimo", "Ex 26:34", "pondrás la cubierta sobre el arca del testimonio en el lugar santísimo"),
     "plano": PI(25, 25, nota="Encima del arca (Ex 25:21). " + SUP,
                 relacion=[p("encima del arca", "Ex 25:21", "pondrás la cubierta encima del arca")]),
     "funcion": p("Lugar desde donde Dios habla a Moisés", "Ex 25:22", "hablaré contigo de sobre la cubierta"),
     "nota": "La RV1909 lo llama «cubierta». El texto no da su grosor ni la altura de los querubines."},
    {"id": "mesa", "nombre": "Mesa de los panes de la proposición", "grupo": "mobiliario",
     "instruccion": "Ex 25:23-30", "construccion": "Ex 37:10-16",
     "medidas": {"largo": m(2, "Ex 25:23", "su longitud será de dos codos"),
                 "ancho": m(1, "Ex 25:23", "de un codo su anchura"),
                 "alto": m(1.5, "Ex 25:23", "su altura de codo y medio")},
     "materiales": [c("madera de Sittim", "Ex 25:23", "una mesa de madera de Sittim"),
                    c("oro puro", "Ex 25:24", "la cubrirás de oro puro"),
                    c("moldura de un palmo", "Ex 25:25", "una moldura alrededor, del ancho de una mano")],
     "zona": ZT("santo", "Ex 26:35", "pondrás la mesa fuera del velo"),
     "plano": PI(40, 28, nota="Lado norte del lugar santo; la coordenada exacta es un supuesto.",
                 relacion=[p("al norte", "Ex 26:35", "pondrás la mesa al lado del aquilón"),
                           p("al norte, fuera del velo", "Ex 40:22", "al lado septentrional del pabellón, fuera del velo")]),
     "funcion": p("Sostener el pan de la proposición", "Ex 25:30",
                  "pondrás sobre la mesa el pan de la proposición delante de mí continuamente"),
     "nota": None},
    {"id": "candelabro", "nombre": "Candelabro (candelero) de oro", "grupo": "mobiliario",
     "instruccion": "Ex 25:31-40", "construccion": "Ex 37:17-24",
     "medidas": {},
     "materiales": [c("oro puro labrado a martillo", "Ex 25:31", "un candelero de oro puro"),
                    c("un talento de oro", "Ex 25:39", "De un talento de oro fino lo harás")],
     "detalles": [p("seis brazos, tres a cada lado", "Ex 25:32", "saldrán seis brazos de sus lados"),
                  p("siete lámparas", "Ex 25:37", "hacerle has siete candilejas")],
     "zona": ZT("santo", "Ex 40:24", "puso el candelero en el tabernáculo del testimonio"),
     "plano": PI(40, 22, nota="Lado sur del lugar santo; la coordenada exacta es un supuesto.",
                 relacion=[p("al sur, frente a la mesa", "Ex 26:35", "el candelero enfrente de la mesa al lado del tabernáculo al mediodía"),
                           p("al sur, frente a la mesa", "Ex 40:24", "enfrente de la mesa, al lado meridional del pabellón")]),
     "funcion": p("Alumbrar", "Ex 25:37", "las cuales encenderás para que alumbren"),
     "nota": "El texto NO da medidas del candelabro (ni alto ni ancho), solo su peso: un talento de oro."},
    {"id": "altar-incienso", "nombre": "Altar del incienso (altar de oro)", "grupo": "mobiliario",
     "instruccion": "Ex 30:1-10", "construccion": "Ex 37:25-28",
     "medidas": {"largo": m(1, "Ex 30:2", "Su longitud será de un codo"),
                 "ancho": m(1, "Ex 30:2", "su anchura de un codo"),
                 "alto": m(2, "Ex 30:2", "su altura de dos codos")},
     "materiales": [c("madera de Sittim", "Ex 30:1", "de madera de Sittim lo harás"),
                    c("oro puro", "Ex 30:3", "cubrirlo has de oro puro")],
     "zona": ZT("santo", "Ex 40:26", "Puso también el altar de oro en el tabernáculo del testimonio, delante del velo"),
     "plano": PI(32, 25, nota="Delante del velo, en el eje; la distancia exacta es un supuesto.",
                 relacion=[p("delante del velo", "Ex 30:6", "lo pondrás delante del velo que está junto al arca del testimonio"),
                           p("delante del velo", "Ex 40:26", "delante del velo")]),
     "funcion": p("Quemar incienso mañana y tarde", "Ex 30:7", "quemará sobre él Aarón sahumerio de aroma cada mañana"),
     "nota": "La RV1909 lo llama «altar de sahumerio de perfume» (Ex 30:1) y «altar de oro» (Ex 40:26)."},
    {"id": "altar-holocausto", "nombre": "Altar del holocausto (de bronce)", "grupo": "mobiliario",
     "instruccion": "Ex 27:1-8", "construccion": "Ex 38:1-7",
     "medidas": {"largo": m(5, "Ex 27:1", "de cinco codos de longitud"),
                 "ancho": m(5, "Ex 27:1", "de cinco codos de anchura"),
                 "alto": m(3, "Ex 27:1", "su altura de tres codos")},
     "materiales": [c("madera de Sittim", "Ex 27:1", "altar de madera de Sittim"),
                    c("cubierto de metal (bronce)", "Ex 27:2", "lo cubrirás de metal"),
                    c("enrejado de metal", "Ex 27:4", "un enrejado de metal de obra de malla")],
     "zona": ZT("atrio", "Ex 40:33", "erigió el atrio en derredor del tabernáculo y del altar"),
     "plano": PI(75, 25, nota="Entre la puerta del atrio y el tabernáculo; la distancia exacta es un supuesto.",
                 relacion=[p("delante de la puerta del tabernáculo", "Ex 40:6", "pondrás el altar del holocausto delante de la puerta del tabernáculo"),
                           p("a la puerta del tabernáculo", "Ex 40:29", "colocó el altar del holocausto á la puerta del tabernáculo")]),
     "funcion": p("Ofrecer holocaustos y presentes", "Ex 40:29", "ofreció sobre él holocausto y presente"),
     "nota": "«Metal» en la RV1909 traduce el hebreo nechóshet (bronce o cobre). Hueco, hecho de tablas (Ex 27:8)."},
    {"id": "fuente", "nombre": "Fuente de bronce (lavacro)", "grupo": "mobiliario",
     "instruccion": "Ex 30:17-21", "construccion": "Ex 38:8",
     "medidas": {},
     "materiales": [c("metal (bronce), con su basa", "Ex 30:18", "una fuente de metal, con su basa de metal"),
                    c("de los espejos de las mujeres que servían a la puerta", "Ex 38:8", "de los espejos de las que velaban")],
     "zona": ZT("atrio", "Ex 30:18", "entre el tabernáculo del testimonio y el altar", "inferido",
                "Está entre el tabernáculo y el altar, ambos dentro del atrio (Ex 40:33)."),
     "plano": PI(62, 25, nota="Entre el tabernáculo y el altar; la coordenada exacta es un supuesto.",
                 relacion=[p("entre el tabernáculo y el altar", "Ex 30:18", "la has de poner entre el tabernáculo del testimonio y el altar"),
                           p("entre el tabernáculo y el altar", "Ex 40:30", "puso la fuente entre el tabernáculo del testimonio y el altar")]),
     "funcion": p("Lavarse manos y pies los sacerdotes", "Ex 30:19", "se lavarán Aarón y sus hijos sus manos y sus pies"),
     "nota": "El texto NO da medidas ni forma de la fuente."},
    # ------------------------------------------------------------------ estructura
    {"id": "tablas", "nombre": "Tablas del tabernáculo", "grupo": "estructura",
     "instruccion": "Ex 26:15-25", "construccion": "Ex 36:20-30",
     "medidas": {"largo": m(10, "Ex 26:16", "La longitud de cada tabla será de diez codos",
                            nota="De pie, el largo de la tabla es la altura del tabernáculo."),
                 "ancho": m(1.5, "Ex 26:16", "de codo y medio la anchura de cada tabla")},
     "cantidad": {"valor": 48, "ref": None, "cita": None, "certeza": "calculo", "calculo": "tablas-total"},
     "materiales": [c("madera de Sittim", "Ex 26:15", "tablas de madera de Sittim"),
                    c("cubiertas de oro", "Ex 26:29", "cubrirás las tablas de oro")],
     "zona": None,
     "plano": PI(35, 25, rect={"x0": 20, "y0": 20, "x1": 50, "y1": 30},
                 nota="Contorno del tabernáculo: 30 codos de largo (cálculo) por 10 de ancho interior (tradición); "
                      "posición en el atrio = supuesto de dibujo."),
     "nota": "El texto no da el grosor de las tablas (Rashi: un codo)."},
    {"id": "basas", "nombre": "Basas de plata de las tablas", "grupo": "estructura",
     "instruccion": "Ex 26:19-25", "construccion": "Ex 36:24-30",
     "medidas": {},
     "cantidad": {"valor": 96, "ref": None, "cita": None, "certeza": "calculo", "calculo": "basas-tablas"},
     "materiales": [c("plata", "Ex 26:19", "cuarenta basas de plata")],
     "zona": None,
     "plano": PI(35, 25, rect={"x0": 20, "y0": 20, "x1": 50, "y1": 30}, nota="Bajo las tablas."),
     "nota": "Dos basas por tabla (Ex 26:19). No incluye las basas de las columnas del velo ni de la entrada."},
    {"id": "barras", "nombre": "Barras", "grupo": "estructura",
     "instruccion": "Ex 26:26-29", "construccion": "Ex 36:31-34",
     "medidas": {},
     "cantidad": {"valor": 15, "ref": None, "cita": None, "certeza": "calculo", "calculo": "barras"},
     "materiales": [c("madera de Sittim", "Ex 26:26", "cinco barras de madera de Sittim"),
                    c("cubiertas de oro", "Ex 26:29", "también cubrirás las barras de oro")],
     "detalles": [p("la barra del medio atraviesa de un extremo a otro", "Ex 26:28",
                    "la barra del medio pasará por medio de las tablas, del un cabo al otro")],
     "zona": None,
     "plano": PI(35, 25, rect={"x0": 20, "y0": 20, "x1": 50, "y1": 30}, nota="En las paredes sur, norte y occidental."),
     "nota": "El texto no da su longitud."},
    {"id": "columnas-tabernaculo", "nombre": "Columnas del velo y de la entrada", "grupo": "estructura",
     "instruccion": "Ex 26:32-37", "construccion": "Ex 36:36-38",
     "medidas": {},
     "cantidad": {"valor": 9, "ref": None, "cita": None, "certeza": "calculo", "calculo": "columnas-tabernaculo"},
     "materiales": [c("madera de Sittim cubierta de oro (velo)", "Ex 26:32", "cuatro columnas de madera de Sittim cubiertas de oro"),
                    c("basas de plata (velo)", "Ex 26:32", "sobre basas de plata"),
                    c("cubiertas de oro (entrada)", "Ex 26:37", "las cuales cubrirás de oro"),
                    c("cinco basas de metal (entrada)", "Ex 26:37", "cinco basas de metal")],
     "zona": None,
     "plano": PI(40, 25, nota="Cuatro en la línea del velo (x = 30) y cinco en la entrada (x = 50); reparto equidistante supuesto."),
     "nota": "El texto no da su altura."},
    # ------------------------------------------------------------------ cortinas
    {"id": "cortinas-lino", "nombre": "Cortinas de lino (el tabernáculo)", "grupo": "cortinas",
     "instruccion": "Ex 26:1-6", "construccion": "Ex 36:8-13",
     "medidas": {"largo": m(28, "Ex 26:2", "La longitud de la una cortina de veintiocho codos"),
                 "ancho": m(4, "Ex 26:2", "la anchura de la misma cortina de cuatro codos")},
     "cantidad": {"valor": 10, "ref": "Ex 26:1", "cita": "diez cortinas", "certeza": "texto"},
     "materiales": [c("lino torcido, cárdeno, púrpura y carmesí, con querubines", "Ex 26:1",
                      "diez cortinas de lino torcido, cárdeno, y púrpura, y carmesí"),
                    c("cincuenta corchetes de oro", "Ex 26:6", "cincuenta corchetes de oro")],
     "zona": None,
     "plano": PI(35, 25, rect={"x0": 20, "y0": 20, "x1": 50, "y1": 30}, nota="Cubren el tabernáculo."),
     "funcion": p("Forman el tabernáculo", "Ex 26:6", "se formará un tabernáculo"),
     "nota": "Dos grupos de cinco unidos con corchetes (Ex 26:3-6): ver cálculos lino-ancho y lino-grupo."},
    {"id": "cortinas-cabra", "nombre": "Cortinas de pelo de cabra (la tienda)", "grupo": "cortinas",
     "instruccion": "Ex 26:7-13", "construccion": "Ex 36:14-18",
     "medidas": {"largo": m(30, "Ex 26:8", "La longitud de la una cortina será de treinta codos"),
                 "ancho": m(4, "Ex 26:8", "la anchura de la misma cortina de cuatro codos")},
     "cantidad": {"valor": 11, "ref": "Ex 26:7", "cita": "once cortinas harás", "certeza": "texto"},
     "materiales": [c("pelo de cabras", "Ex 26:7", "cortinas de [pelo] de cabras"),
                    c("cincuenta corchetes de metal", "Ex 26:11", "cincuenta corchetes de alambre")],
     "zona": None,
     "plano": PI(35, 25, rect={"x0": 20, "y0": 20, "x1": 50, "y1": 30}, nota="Sobre las de lino."),
     "funcion": p("Cubierta sobre el tabernáculo", "Ex 26:7", "para una cubierta sobre el tabernáculo"),
     "nota": "Once cortinas: la sexta se dobla delante y media cortina cuelga detrás (Ex 26:9, 26:12)."},
    {"id": "cubiertas", "nombre": "Cubiertas de pieles", "grupo": "cortinas",
     "instruccion": "Ex 26:14", "construccion": "Ex 36:19",
     "medidas": {},
     "materiales": [c("cueros de carneros teñidos de rojo", "Ex 26:14", "una cubierta de cueros de carneros, teñidos de rojo"),
                    c("cueros de tejones, encima", "Ex 26:14", "una cubierta de cueros de tejones encima")],
     "zona": None,
     "plano": PI(35, 25, rect={"x0": 20, "y0": 20, "x1": 50, "y1": 30}, nota="Encima de todo."),
     "nota": "El texto NO da medidas. «Tejones» es la traducción de la RV1909; la identificación del animal es dudosa."},
    {"id": "velo", "nombre": "Velo", "grupo": "cortinas",
     "instruccion": "Ex 26:31-33", "construccion": "Ex 36:35-36",
     "medidas": {},
     "materiales": [c("cárdeno, púrpura, carmesí y lino torcido, con querubines", "Ex 26:31",
                      "un velo de cárdeno, y púrpura, y carmesí, y de lino torcido")],
     "zona": None,
     "plano": PI(30, 25, rot=90, nota="Línea entre el santo y el santísimo, bajo los corchetes (Ex 26:33); "
                                      "x = 30 resulta del cálculo largo-santo.",
                 relacion=[p("bajo los corchetes", "Ex 26:33", "pondrás el velo debajo de los corchetes")]),
     "funcion": p("Separar el lugar santo del santísimo", "Ex 26:33",
                  "aquel velo os hará separación entre el lugar santo y el santísimo"),
     "nota": "El texto no da sus medidas; 10 × 10 codos sería inferido del ancho y alto del tabernáculo."},
    {"id": "cortina-entrada", "nombre": "Cortina de la entrada del tabernáculo", "grupo": "cortinas",
     "instruccion": "Ex 26:36-37", "construccion": "Ex 36:37-38",
     "medidas": {},
     "materiales": [c("cárdeno, púrpura, carmesí y lino torcido, obra de bordador", "Ex 26:36",
                      "una cortina de cárdeno, y púrpura, y carmesí, y lino torcido, obra de bordador")],
     "zona": None,
     "plano": PI(50, 25, rot=90, nota="Lado oriental del tabernáculo (supuesto de dibujo).",
                 relacion=[p("a la puerta del tabernáculo", "Ex 26:36", "harás á la puerta del tabernáculo una cortina")]),
     "nota": "El texto no da sus medidas. En Ex 36:37 la RV1909 la llama «velo para la puerta»."},
    # ------------------------------------------------------------------ atrio
    {"id": "cortinas-atrio", "nombre": "Cortinas del atrio", "grupo": "atrio",
     "instruccion": "Ex 27:9-15", "construccion": "Ex 38:9-16",
     "medidas": {"largo": m(100, "Ex 27:9", "de cien codos de longitud cada un lado",
                            nota="Lados sur y norte; occidente 50 (Ex 27:12), oriente 15 + 15 (Ex 27:14-15)."),
                 "alto": m(5, "Ex 27:18", "la altura de cinco codos")},
     "materiales": [c("lino torcido", "Ex 27:9", "cortinas de lino torcido")],
     "zona": ZT("atrio", "Ex 27:9", "harás el atrio del tabernáculo"),
     "plano": PI(50, 25, certeza="texto", rect={"x0": 0, "y0": 0, "x1": 100, "y1": 50},
                 nota="Perímetro del atrio (medidas del texto)."),
     "nota": "Total: ver cálculo atrio-cortinas (280 codos más los 20 de la puerta)."},
    {"id": "columnas-atrio", "nombre": "Columnas del atrio", "grupo": "atrio",
     "instruccion": "Ex 27:10-17", "construccion": "Ex 38:10-19",
     "medidas": {},
     "cantidad": {"valor": 60, "ref": None, "cita": None, "certeza": "calculo", "calculo": "columnas-atrio"},
     "materiales": [c("basas de metal (bronce)", "Ex 27:10", "sus veinte basas serán de metal"),
                    c("capiteles y molduras de plata", "Ex 27:10", "los capiteles de las columnas y sus molduras, de plata"),
                    c("ceñidas de plata", "Ex 27:17", "serán ceñidas de plata")],
     "zona": ZT("atrio", "Ex 27:17", "Todas las columnas del atrio en derredor"),
     "plano": PI(50, 25, rect={"x0": 0, "y0": 0, "x1": 100, "y1": 50},
                 nota="En el perímetro; reparto cada 5 codos supuesto (100/20, 50/10)."),
     "nota": "El texto no da su altura ni su grosor; la altura de las cortinas es 5 codos (Ex 27:18)."},
    {"id": "puerta-atrio", "nombre": "Puerta (pabellón) del atrio", "grupo": "atrio",
     "instruccion": "Ex 27:16", "construccion": "Ex 38:18-19",
     "medidas": {"largo": m(20, "Ex 27:16", "un pabellón de veinte codos")},
     "materiales": [c("cárdeno, púrpura, carmesí y lino torcido, obra de bordador", "Ex 27:16",
                      "de cárdeno, y púrpura, y carmesí, y lino torcido, de obra de bordador")],
     "detalles": [p("cuatro columnas con cuatro basas", "Ex 27:16", "sus columnas cuatro, con sus cuatro basas")],
     "zona": ZT("atrio", "Ex 27:16", "á la puerta del atrio"),
     "plano": PI(100, 25, rot=90, nota="Lado oriental; centrada porque quedan 15 codos a cada lado (cálculo atrio-oriente).",
                 relacion=[p("al oriente", "Ex 27:13", "por la parte de levante, al oriente")]),
     "nota": "Los 20 codos son el ancho del vano; el texto no da su altura (Ex 38:18 la compara con las cortinas: cinco codos)."},
]

# --------------------------------------------------------------------------- montaje (Ex 40:17-33)
MONTAJE = [
    ("cortinas-lino", "Ex 40:18", "Moisés hizo levantar el tabernáculo", "inferido",
     "En Ex 26:1 «el tabernáculo» son las diez cortinas de lino; aquí puede designar el conjunto."),
    ("basas", "Ex 40:18", "asentó sus basas", "texto", None),
    ("tablas", "Ex 40:18", "colocó sus tablas", "texto", None),
    ("barras", "Ex 40:18", "puso sus barras", "texto", None),
    ("columnas-tabernaculo", "Ex 40:18", "hizo alzar sus columnas", "texto", None),
    ("cortinas-cabra", "Ex 40:19", "extendió la tienda sobre el tabernáculo", "inferido",
     "«La tienda» son las cortinas de pelo de cabra (Ex 26:7, 26:11)."),
    ("cubiertas", "Ex 40:19", "puso la sobrecubierta encima del mismo", "inferido",
     "La sobrecubierta = las cubiertas de pieles (Ex 26:14)."),
    ("arca", "Ex 40:20", "puso el testimonio dentro del arca", "texto", None),
    ("arca", "Ex 40:20", "colocó las varas en el arca", "texto", None),
    ("propiciatorio", "Ex 40:20", "encima la cubierta sobre el arca", "texto", None),
    ("arca", "Ex 40:21", "metió el arca en el tabernáculo", "texto", None),
    ("velo", "Ex 40:21", "puso el velo de la tienda", "texto", None),
    ("mesa", "Ex 40:22", "puso la mesa en el tabernáculo del testimonio", "texto", None),
    ("mesa", "Ex 40:23", "sobre ella puso por orden los panes", "texto", None),
    ("candelabro", "Ex 40:24", "puso el candelero en el tabernáculo del testimonio", "texto", None),
    ("candelabro", "Ex 40:25", "encendió las lámparas", "texto", None),
    ("altar-incienso", "Ex 40:26", "Puso también el altar de oro", "texto", None),
    ("altar-incienso", "Ex 40:27", "encendió sobre él el perfume aromático", "texto", None),
    ("cortina-entrada", "Ex 40:28", "Puso asimismo la cortina de la puerta del tabernáculo", "texto", None),
    ("altar-holocausto", "Ex 40:29", "colocó el altar del holocausto", "texto", None),
    ("fuente", "Ex 40:30", "puso la fuente entre el tabernáculo del testimonio y el altar", "texto", None),
    ("cortinas-atrio", "Ex 40:33", "erigió el atrio en derredor del tabernáculo y del altar", "texto", None),
    ("puerta-atrio", "Ex 40:33", "puso la cortina de la puerta del atrio", "texto", None),
]

OBLIGATORIAS = {"arca", "propiciatorio", "mesa", "candelabro", "altar-incienso", "altar-holocausto", "fuente",
                "tablas", "basas", "velo", "cortina-entrada", "cortinas-lino", "cortinas-cabra", "cubiertas",
                "cortinas-atrio", "columnas-atrio", "puerta-atrio"}

# --------------------------------------------------------------------------- numerales escritos
FRASES = [("dos codos y medio", 2.5), ("codo y medio", 1.5), ("diez y seis", 16)]
PALABRAS = {"un": 1, "una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7,
            "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12, "quince": 15, "veinte": 20,
            "veintiocho": 28, "treinta": 30, "cuarenta": 40, "cincuenta": 50, "cien": 100}


def valores(cita):
    s, vals = cita.lower(), set()
    for frase, v in FRASES:
        if frase in s:
            vals.add(v)
            s = s.replace(frase, " # ")
    for w in re.findall(r"[a-záéíóúñ]+", s):
        if w in PALABRAS:
            vals.add(PALABRAS[w])
    return vals


OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def evaluar(expr):
    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in OPS:
            return OPS[type(n.op)](ev(n.left), ev(n.right))
        raise ValueError(f"operación no permitida: {expr!r}")
    return ev(ast.parse(expr, mode="eval"))


def clave(ref):
    mm = re.fullmatch(r"Ex (\d+):(\d+)", ref or "")
    if not mm:
        raise ValueError(f"referencia mal formada: {ref!r}")
    return int(mm.group(1)), int(mm.group(2))


def cargar_js(ruta):
    s = ruta.read_text(encoding="utf-8")
    return json.loads(s[s.index("{"):s.rindex("}") + 1])


def num(x):
    return int(x) if float(x).is_integer() else x


# --------------------------------------------------------------------------- main
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    datos = cargar_js(DATOS / "biblia.js")
    V = {f'{c_["libro"]} {c_["cap"]}:{v["n"]}': v["texto"] for c_ in datos["capitulos"] for v in c_["versiculos"]}
    errores, ncitas = [], [0]

    def cita_ok(ref, cita, donde):
        if ref is None and cita is None:
            return
        ncitas[0] += 1
        if ref not in V:
            errores.append(f"{donde}: no existe {ref}")
        elif not cita or cita not in V[ref]:
            errores.append(f"{donde}: la cita {cita!r} no está en {ref}")

    def rango_ok(r, donde):
        mm = re.fullmatch(r"Ex (\d+):(\d+)(?:-(\d+))?", r or "")
        if not mm:
            errores.append(f"{donde}: rango mal formado {r!r}")
            return
        cap, a, b = int(mm.group(1)), int(mm.group(2)), int(mm.group(3) or mm.group(2))
        for n in (a, b):
            if f"Ex {cap}:{n}" not in V:
                errores.append(f"{donde}: no existe Ex {cap}:{n}")
        if b < a:
            errores.append(f"{donde}: rango invertido {r}")

    def medida_ok(md, donde):
        if md["certeza"] not in ("texto", "calculo", "inferido", "tradicion"):
            errores.append(f"{donde}: certeza {md['certeza']!r}")
        cita_ok(md["ref"], md["cita"], donde)
        if md["certeza"] == "texto":
            if md["codos"] not in valores(md["cita"]):
                errores.append(f"{donde}: {md['codos']} no está escrito en {md['cita']!r}")
        elif not md.get("calculo"):
            errores.append(f"{donde}: medida no textual sin cálculo")
        if md.get("calculo"):
            cal = calc.get(md["calculo"])
            if not cal or cal["resultado"] != md["codos"]:
                errores.append(f"{donde}: no cuadra con el cálculo {md['calculo']}")

    # cálculos
    calc = {}
    for k in CALCULOS:
        d = f"cálculo {k['id']}"
        res = evaluar(k["operacion"])
        if abs(res - k["resultado"]) > 1e-9:
            errores.append(f"{d}: {k['operacion']} = {res}, no {k['resultado']}")
        vals = set()
        for i, ps in enumerate(k["pasos"]):
            dp = f"{d} paso {i + 1}"
            if ps.get("calculo"):
                prev = calc.get(ps["calculo"])
                if not prev:
                    errores.append(f"{dp}: cálculo previo {ps['calculo']} inexistente o posterior")
                elif prev["resultado"] != ps.get("valor"):
                    errores.append(f"{dp}: valor {ps.get('valor')} ≠ {prev['resultado']}")
            elif ps.get("ref"):
                cita_ok(ps["ref"], ps["cita"], dp)
                if "valor" in ps and ps["valor"] not in valores(ps["cita"]):
                    errores.append(f"{dp}: {ps['valor']} no está escrito en {ps['cita']!r}")
            elif not (ps.get("fuente") or ps.get("supuesto")):
                errores.append(f"{dp}: paso sin ref, cálculo, fuente ni supuesto")
            if "valor" in ps:
                vals.add(ps["valor"])
        for n in re.findall(r"\d+(?:\.\d+)?", k["operacion"]):
            if float(n) not in {float(v) for v in vals}:
                errores.append(f"{d}: la cifra {n} de la operación no sale de ningún paso")
        if k["id"] in calc:
            errores.append(f"{d}: id repetido")
        calc[k["id"]] = k

    # orientación
    cita_ok(ORIENTACION["ref"], ORIENTACION["cita"], "orientación")
    for o in ORIENTACION["otras"]:
        cita_ok(o["ref"], o["cita"], "orientación")

    # zonas
    zids = set()
    for z in ZONAS:
        zids.add(z["id"])
        for eje in ("largo", "ancho", "alto"):
            if eje in z:
                medida_ok(z[eje], f"zona {z['id']}.{eje}")
        pl = z["plano"]
        if (pl["x1"] - pl["x0"], pl["y1"] - pl["y0"]) != (z["largo"]["codos"], z["ancho"]["codos"]):
            errores.append(f"zona {z['id']}: el rectángulo del plano no coincide con largo × ancho")
    if zids != {"atrio", "santo", "santisimo"}:
        errores.append(f"zonas: {zids}")

    # piezas
    pids = [x["id"] for x in PIEZAS]
    if len(set(pids)) != len(pids):
        errores.append("piezas: ids repetidos")
    if OBLIGATORIAS - set(pids):
        errores.append(f"faltan piezas: {sorted(OBLIGATORIAS - set(pids))}")
    for x in PIEZAS:
        d = f"pieza {x['id']}"
        if x["grupo"] not in ("mobiliario", "estructura", "cortinas", "atrio"):
            errores.append(f"{d}: grupo {x['grupo']!r}")
        rango_ok(x.get("instruccion"), d + " instrucción")
        rango_ok(x.get("construccion"), d + " construcción")
        for eje, md in x["medidas"].items():
            if eje not in ("largo", "ancho", "alto"):
                errores.append(f"{d}: eje {eje!r}")
            medida_ok(md, f"{d}.{eje}")
        cant = x.get("cantidad")
        if cant:
            if cant["certeza"] == "texto":
                cita_ok(cant["ref"], cant["cita"], d + " cantidad")
                if cant["valor"] not in valores(cant["cita"]):
                    errores.append(f"{d}: cantidad {cant['valor']} no escrita en {cant['cita']!r}")
            elif calc.get(cant.get("calculo"), {}).get("resultado") != cant["valor"]:
                errores.append(f"{d}: cantidad no cuadra con el cálculo")
        if not x["materiales"]:
            errores.append(f"{d}: sin materiales")
        for mt in x["materiales"]:
            cita_ok(mt["ref"], mt["cita"], d + " material")
        for dt in x.get("detalles", []):
            cita_ok(dt["ref"], dt["cita"], d + " detalle")
        if x.get("funcion"):
            cita_ok(x["funcion"]["ref"], x["funcion"]["cita"], d + " función")
        z = x.get("zona")
        if z:
            if z["id"] not in zids or z["certeza"] not in ("texto", "inferido"):
                errores.append(f"{d}: zona {z}")
            cita_ok(z["ref"], z["cita"], d + " zona")
        elif x["grupo"] == "mobiliario":
            errores.append(f"{d}: mobiliario sin zona")
        pl = x["plano"]
        if pl["certeza"] not in ("texto", "inferido", "tradicion") or not (0 <= pl["x"] <= 100 and 0 <= pl["y"] <= 50):
            errores.append(f"{d}: plano {pl}")
        for r in pl.get("relacion", []):
            cita_ok(r["ref"], r["cita"], d + " relación")
        if x["grupo"] == "mobiliario" and z and z["id"] != "atrio":
            zr = next(zz["plano"] for zz in ZONAS if zz["id"] == z["id"])
            if not (zr["x0"] <= pl["x"] <= zr["x1"] and zr["y0"] <= pl["y"] <= zr["y1"]):
                errores.append(f"{d}: coordenada fuera de su zona")
    # coherencia de relaciones norte/sur y oriente
    pos = {x["id"]: x["plano"] for x in PIEZAS}
    if not pos["mesa"]["y"] > 25 > pos["candelabro"]["y"]:
        errores.append("plano: la mesa debe quedar al norte y el candelabro al sur")
    if not 50 < pos["fuente"]["x"] < pos["altar-holocausto"]["x"] < 100:
        errores.append("plano: la fuente debe quedar entre el tabernáculo y el altar")
    if not 30 < pos["altar-incienso"]["x"] < pos["mesa"]["x"]:
        errores.append("plano: el altar del incienso debe quedar junto al velo, del lado del lugar santo")

    # montaje
    montaje, ant = [], (40, 17)
    for i, (pieza, ref, cita, certeza, nota) in enumerate(MONTAJE, 1):
        d = f"montaje {i}"
        cita_ok(ref, cita, d)
        k = clave(ref)
        if not ((40, 17) <= k <= (40, 33)) or k < ant:
            errores.append(f"{d}: {ref} fuera de Ex 40:17-33 o fuera de orden")
        ant = k
        if pieza not in pids:
            errores.append(f"{d}: pieza {pieza} inexistente")
        montaje.append({"orden": i, "pieza": pieza, "ref": ref, "cita": cita, "certeza": certeza, "nota": nota})

    if errores:
        print(f"{len(errores)} error(es):", file=sys.stderr)
        for e in errores:
            print("  " + e, file=sys.stderr)
        return 1

    for k in CALCULOS:
        k["resultado"] = num(k["resultado"])
    doc = {"generado": datetime.date.today().isoformat(), "unidad": "codo", "codos": CODOS,
           "orientacion": ORIENTACION, "zonas": ZONAS, "piezas": PIEZAS, "calculos": CALCULOS,
           "montaje": montaje, "fuentes": FUENTES}
    SALIDA.write_text("window.BIBLIA_TABERNACULO = " + json.dumps(doc, ensure_ascii=False, indent=1) + ";\n",
                      encoding="utf-8")
    n_texto = sum(1 for x in PIEZAS for md in x["medidas"].values() if md["certeza"] == "texto")
    n_zona = {z["id"]: {e: z[e]["certeza"] for e in ("largo", "ancho", "alto")} for z in ZONAS}
    print(f"OK: {len(PIEZAS)} piezas, {n_texto} medidas de pieza con texto, {len(CALCULOS)} cálculos, "
          f"{len(montaje)} pasos de montaje, {ncitas[0]} citas verificadas.")
    print(f"Zonas: {n_zona}")
    print(f"Sin medidas en el texto: {[x['id'] for x in PIEZAS if not x['medidas']]}")
    print(f"Escrito {SALIDA.relative_to(RAIZ)} ({SALIDA.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
