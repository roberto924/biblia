"""Cronología relativa de Génesis (años desde la creación de Adán). Todo año es CÁLCULO.

Cada evento depende de otro (`depende_de`) y suma sus `pasos`; cada paso es una edad de `edades`
(tomada de los datos, nunca tecleada) o una cifra escrita en el versículo (verificada contra el texto).
"""
import itertools
import re

TRADS = ("TM", "LXX")
SUPUESTOS = [
    {"id": "tare", "pregunta": "¿Qué edad tenía Taré al nacer Abram?",
     "opciones": [
         {"id": "tare70", "texto": "70 años (lectura directa de Gn 11:26)", "refs": ["Gn 11:26"],
          "nota": "Gn 11:26 dice que Taré vivió setenta años y engendró a Abram, Nacor y Harán; se toma a Abram como nacido entonces."},
         {"id": "tare130", "texto": "130 años (Abram sale de Harán a los 75, tras morir Taré a los 205)",
          "refs": ["Gn 11:32", "Gn 12:4"],
          "nota": "Supone que Abram salió de Harán después de morir Taré; se apoya además en Hechos 7:4, fuera de Génesis."}],
     "defecto": "tare70"},
    {"id": "sem", "pregunta": "¿Cómo se enlaza Sem con el diluvio?",
     "opciones": [
         {"id": "sem2", "texto": "Arfaxad nace «dos años después del diluvio» (Gn 11:10)", "refs": ["Gn 11:10", "Gn 7:6"],
          "nota": "Sem tenía 100 años al engendrar a Arfaxad; con ello Sem nace cuando Noé tiene 502."},
         {"id": "noe500", "texto": "Sem nace cuando Noé tiene 500 años (Gn 5:32)", "refs": ["Gn 5:32", "Gn 11:10"],
          "nota": "Gn 5:32 nombra a los tres hijos a la vez; tomarlo como edad de Noé al nacer Sem deja a Arfaxad naciendo el año del diluvio."}],
     "defecto": "sem2"},
    {"id": "jose", "pregunta": "¿Qué edad tenía Jacob al nacer José?",
     "opciones": [
         {"id": "jose91", "texto": "91 años: cálculo de varios pasos (130 − 30 − 7 − 2)",
          "refs": ["Gn 47:9", "Gn 41:46", "Gn 41:47", "Gn 45:6"],
          "nota": "Jacob tiene 130 ante Faraón; José tenía 30 al presentarse ante Faraón, pasan 7 años de abundancia "
                  "y 2 de hambre hasta que llega Jacob. Génesis no da la edad de Jacob al nacer José."}],
     "defecto": "jose91"},
    {"id": "e430", "pregunta": "¿Qué abarcan los 430 años de Ex 12:40?",
     "opciones": [
         {"id": "egipto", "texto": "Solo la estancia en Egipto (lectura del TM)", "refs": ["Ex 12:40", "Gn 47:9"],
          "nota": "El TM (RV1909) dice que los hijos de Israel «habitaron en Egipto» 430 años: se cuentan desde que "
                  "Jacob, de 130 años, entra en Egipto (Gn 47:9)."},
         {"id": "canaan", "texto": "Canaán y Egipto (lectura de la LXX)", "refs": ["Ex 12:40", "Gn 12:4"],
          "nota": "La LXX (Brenton) dice explícitamente «in the land of Egypt and the land of Chanaan»: se cuentan "
                  "desde que Abram, de 75 años, sale de Harán y entra en Canaán (Gn 12:4-5; se toma el mismo año)."}],
     "defecto": "egipto"},
]
# Citas literales del supuesto e430 (se rellenan y verifican contra el texto en construir()).
CITAS_430 = {"TM": ("Ex 12:40", "rv1909", "habitaron en Egipto"),
             "LXX": ("Ex 12:40", "brenton", "the land of Egypt and the land of Chanaan")}
NOTAS = ["Cainán, hijo de Arfaxad (Gn 11:12-13), solo existe en la Septuaginta: en la LXX su generación (130 años) se suma "
         "en la cadena; en el TM no existe. No es un supuesto: es propio de cada tradición.",
         "Convención del cálculo: una edad N al ocurrir algo se cuenta como N años después del nacimiento.",
         "La LXX es la de Brenton (1851); otros manuscritos dan cifras distintas.",
         "Éxodo no da edades de padres al engendrar: la salida de Egipto se enlaza con Génesis mediante los 430 años "
         "de Ex 12:40 (supuesto «e430»); los nacimientos de Moisés y Aarón se calculan hacia atrás desde Ex 7:7.",
         "Números fecha algunos hechos desde la salida (Nm 1:1; 9:1; 10:11; 33:38): «el segundo año» se cuenta como "
         "un año después de la salida, igual que Ex 40:17.",
         "Deuteronomio fecha los discursos de Moab desde la salida (Dt 1:3, «á los cuarenta años», mes undécimo); la "
         "muerte de Moisés (Dt 34:5-8) no tiene año propio y se pone en ese mismo año.",
         "Josué: el paso del Jordán (Jos 4:19, «el diez del mes primero») se pone en el año siguiente al de Dt 1:3 (mes "
         "undécimo + treinta días de luto, Dt 34:8). La edad de Caleb (40 en Jos 14:7, 85 en Jos 14:10, «cuarenta y cinco "
         "años» después) se comprueba: 40 + 45 = 85. La muerte de Josué (110 años) no tiene base para un año.",
         "Jueces da duraciones (años de opresión, de reposo y de cada juez: `duraciones`), pero no dice si se suceden "
         "o se solapan: no se fechan desde Adán. Sus sumas son cálculo con esa advertencia; Jue 11:26 («trescientos "
         "años») se compara con la suma hasta Jefté. 1 Re 6:1 queda para cuando se añada Reyes."]
# Paso fijo de convención (no es cifra del texto): {"fija": n, "signo": s, "texto": ..., "ref": ...}
F = lambda n, ref, signo=1, texto="": {"fija": n, "ref": ref, "signo": signo, "texto": texto}

E = lambda persona, tipo, ref=None, signo=1, texto="": {"edad": (persona, tipo, ref), "signo": signo, "texto": texto}
# Cifra escrita en el versículo que no es una edad: (ref, {trad: (cita, numeral)})
C = lambda ref, citas, signo=1, texto="": {"constante": (ref, citas), "signo": signo, "texto": texto}

GN5 = [("Adam_1", "Seth_1", "set"), ("Seth_1", "Enosh_1", "enos"), ("Enosh_1", "Kenan_1", "cainan5"),
       ("Kenan_1", "Mahalalel_1", "mahalaleel"), ("Mahalalel_1", "Jared_1", "jared"), ("Jared_1", "Enoch_2", "enoc"),
       ("Enoch_2", "Methuselah_1", "matusalen"), ("Methuselah_1", "Lamech_2", "lamec"), ("Lamech_2", "Noah_1", "noe")]
GN11 = [("Shelah_1", "Eber_1", "heber"), ("Eber_1", "Peleg_1", "peleg"), ("Peleg_1", "Reu_1", "reu"),
        ("Reu_1", "Serug_1", "serug"), ("Serug_1", "Nahor_1", "nacor"), ("Nahor_1", "Terah_1", "tare")]


def definir(nombre):
    """Lista de eventos internos: id, titulo, tipo, ref, personas, depende_de, pasos | variantes, nota."""
    ev = [dict(id="ev-adan", titulo="Creación de Adán (año 0 del cálculo)", tipo="nacimiento", ref="Gn 1:27",
               personas=["Adam_1"], depende_de=None, pasos=[], nota="Punto de partida del cálculo.")]
    nac = {"Adam_1": "ev-adan"}
    for padre, hijo, slug in GN5:
        ev.append(dict(id=f"ev-nac-{slug}", titulo=f"Nace {nombre(hijo)}", tipo="nacimiento", ref=None,
                       personas=[hijo], depende_de=nac[padre],
                       pasos=[E(padre, "al_engendrar", texto=f"{nombre(padre)} tenía {{v}} años al engendrar a {nombre(hijo)}")]))
        nac[hijo] = f"ev-nac-{slug}"
    ev.append(dict(id="ev-diluvio", titulo="Comienza el diluvio", tipo="evento", ref="Gn 7:6", personas=["Noah_1"],
                   depende_de=nac["Noah_1"], pasos=[E("Noah_1", "al_diluvio", texto="Noé tenía {v} años cuando llegó el diluvio")]))
    ev.append(dict(id="ev-fin-diluvio", titulo="Las aguas se secan (fin del diluvio)", tipo="evento", ref="Gn 8:13",
                   personas=["Noah_1"], depende_de=nac["Noah_1"],
                   pasos=[C("Gn 8:13", {"TM": ("año seiscientos y uno", "seiscientos y uno"),
                                        "LXX": ("six hundred and first year", "six hundred and first")},
                            texto="«Año {v}» de la vida de Noé")],
                   nota="Se cuenta el «año 601» como 601 años desde su nacimiento, igual que las demás edades."))
    # Sem y Arfaxad (supuesto «sem»)
    ev.append(dict(id="ev-nac-sem", titulo="Nace Sem", tipo="nacimiento", ref="Gn 11:10", personas=["Shem_1"],
                   depende_de=nac["Noah_1"],
                   variantes=[({"sem": "sem2"}, [E("Noah_1", "al_diluvio", texto="Noé tenía {v} años al llegar el diluvio"),
                                                 C("Gn 11:10", {"TM": ("dos años después del diluvio", "dos"),
                                                                "LXX": ("the second year after the flood", "second")},
                                                   texto="Arfaxad nace {v} años después del diluvio"),
                                                 E("Shem_1", "al_engendrar", signo=-1, texto="Sem tenía {v} años al engendrar a Arfaxad")]),
                              ({"sem": "noe500"}, [E("Noah_1", "al_engendrar", texto="Noé tenía {v} años al engendrar a Sem, Cam y Jafet")])]))
    nac["Shem_1"] = "ev-nac-sem"
    ev.append(dict(id="ev-nac-arfaxad", titulo="Nace Arfaxad", tipo="nacimiento", ref="Gn 11:10", personas=["Arpachshad_1"],
                   depende_de="ev-nac-sem", pasos=[E("Shem_1", "al_engendrar", texto="Sem tenía {v} años al engendrar a Arfaxad")]))
    nac["Arpachshad_1"] = "ev-nac-arfaxad"
    ev.append(dict(id="ev-nac-cainan11", titulo="Nace Cainán, hijo de Arfaxad (solo LXX)", tipo="nacimiento", ref="Gn 11:12",
                   personas=["Cainan_1"], depende_de="ev-nac-arfaxad",
                   variantes=[({"tradicion": "TM"}, None),
                              ({"tradicion": "LXX"}, [E("Arpachshad_1", "al_engendrar", texto="Arfaxad tenía {v} años al engendrar a Cainán")])]))
    nac["Cainan_1"] = "ev-nac-cainan11"
    ev.append(dict(id="ev-nac-sala", titulo="Nace Sala", tipo="nacimiento", ref="Gn 11:12", personas=["Shelah_1"],
                   depende_de="ev-nac-arfaxad",
                   variantes=[({"tradicion": "TM"}, [E("Arpachshad_1", "al_engendrar", texto="Arfaxad tenía {v} años al engendrar a Sala")]),
                              ({"tradicion": "LXX"}, [E("Arpachshad_1", "al_engendrar", texto="Arfaxad tenía {v} años al engendrar a Cainán"),
                                                      E("Cainan_1", "al_engendrar", texto="Cainán tenía {v} años al engendrar a Sala")])])),
    nac["Shelah_1"] = "ev-nac-sala"
    for padre, hijo, slug in GN11:
        ev.append(dict(id=f"ev-nac-{slug}", titulo=f"Nace {nombre(hijo)}", tipo="nacimiento", ref=None, personas=[hijo],
                       depende_de=nac[padre],
                       pasos=[E(padre, "al_engendrar", texto=f"{nombre(padre)} tenía {{v}} años al engendrar a {nombre(hijo)}")]))
        nac[hijo] = f"ev-nac-{slug}"
    ev.append(dict(id="ev-nac-abram", titulo="Nace Abram", tipo="nacimiento", ref="Gn 11:26", personas=["Abram_1"],
                   depende_de=nac["Terah_1"],
                   variantes=[({"tare": "tare70"}, [E("Terah_1", "al_engendrar", texto="Taré tenía {v} años al engendrar a Abram (lectura directa)")]),
                              ({"tare": "tare130"}, [E("Terah_1", "total", texto="Taré murió a los {v} años en Harán"),
                                                     E("Abram_1", "en_evento", "Gn 12:4", signo=-1,
                                                       texto="Abram tenía {v} años al salir de Harán, tras la muerte de Taré")])]))
    nac["Abram_1"] = "ev-nac-abram"
    A = "ev-nac-abram"

    def evento(i, titulo, tipo, ref, personas, dep, pasos, nota=""):
        ev.append(dict(id=i, titulo=titulo, tipo=tipo, ref=ref, personas=personas, depende_de=dep, pasos=pasos, nota=nota))

    evento("ev-nac-sara", "Nace Sarai (Sara)", "nacimiento", "Gn 17:17", ["Sarai_1"], A,
           [E("Abram_1", "en_evento", "Gn 17:17", texto="Abraham dice tener {v} años"),
            E("Sarai_1", "en_evento", "Gn 17:17", signo=-1, texto="y Sara {v} (Gn 17:17)")],
           "Supone que las dos edades de Gn 17:17 son del mismo momento.")
    nac["Sarai_1"] = "ev-nac-sara"
    evento("ev-salida-haran", "Abram sale de Harán", "evento", "Gn 12:4", ["Abram_1", "Lot_1"], A,
           [E("Abram_1", "en_evento", "Gn 12:4", texto="Abram tenía {v} años cuando salió de Harán")])
    evento("ev-nac-ismael", "Nace Ismael", "nacimiento", "Gn 16:16", ["Ishmael_1", "Hagar_1"], A,
           [E("Abram_1", "en_evento", "Gn 16:16", texto="Abram tenía {v} años cuando Agar dio a luz a Ismael")])
    nac["Ishmael_1"] = "ev-nac-ismael"
    evento("ev-pacto-circuncision", "Dios se aparece a Abram; pacto y circuncisión", "evento", "Gn 17:1", ["Abram_1", "Ishmael_1"], A,
           [E("Abram_1", "en_evento", "Gn 17:1", texto="Abram tenía {v} años cuando se le apareció Jehová")],
           "Gn 17:24-25: Abraham, de 99 años, e Ismael, de 13, son circuncidados.")
    evento("ev-nac-isaac", "Nace Isaac", "nacimiento", "Gn 21:5", ["Isaac_1", "Sarai_1"], A,
           [E("Abram_1", "en_evento", "Gn 21:5", texto="Abraham tenía {v} años cuando le nació Isaac")])
    nac["Isaac_1"] = I = "ev-nac-isaac"
    evento("ev-muerte-sara", "Muere Sara", "muerte", "Gn 23:1", ["Sarai_1"], "ev-nac-sara",
           [E("Sarai_1", "total", texto="Sara vivió {v} años")])
    evento("ev-boda-isaac", "Isaac toma por mujer a Rebeca", "evento", "Gn 25:20", ["Isaac_1", "Rebekah_1"], I,
           [E("Isaac_1", "en_evento", "Gn 25:20", texto="Isaac tenía {v} años cuando tomó por mujer a Rebeca")])
    evento("ev-nac-esau-jacob", "Nacen Esaú y Jacob", "nacimiento", "Gn 25:26", ["Esau_1", "Jacob_1", "Rebekah_1"], I,
           [E("Isaac_1", "en_evento", "Gn 25:26", texto="Isaac tenía {v} años cuando Rebeca los dio a luz")])
    nac["Esau_1"] = nac["Jacob_1"] = J = "ev-nac-esau-jacob"
    evento("ev-muerte-abraham", "Muere Abraham", "muerte", "Gn 25:7", ["Abram_1"], A,
           [E("Abram_1", "total", texto="Abraham vivió {v} años")])
    evento("ev-boda-esau", "Esaú toma por mujeres a Judit y Basemat", "evento", "Gn 26:34", ["Esau_1"], J,
           [E("Esau_1", "en_evento", "Gn 26:34", texto="Esaú tenía {v} años")])
    evento("ev-muerte-ismael", "Muere Ismael", "muerte", "Gn 25:17", ["Ishmael_1"], "ev-nac-ismael",
           [E("Ishmael_1", "total", texto="Ismael vivió {v} años")])
    evento("ev-muerte-isaac", "Muere Isaac", "muerte", "Gn 35:28", ["Isaac_1"], I, [E("Isaac_1", "total", texto="Isaac vivió {v} años")])
    evento("ev-jacob-egipto", "Jacob entra en Egipto y se presenta ante Faraón", "evento", "Gn 47:9", ["Jacob_1"], J,
           [E("Jacob_1", "en_evento", "Gn 47:9", texto="Jacob dice a Faraón que tiene {v} años")])
    evento("ev-nac-jose", "Nace José", "nacimiento", "Gn 30:24", ["Joseph_1", "Rachel_1"], "ev-jacob-egipto",
           [E("Joseph_1", "en_evento", "Gn 41:46", signo=-1, texto="José tenía {v} años al presentarse ante Faraón"),
            C("Gn 41:47", {"TM": ("aquellos siete años de hartura", "siete"), "LXX": ("the seven years of plenty", "seven")},
              signo=-1, texto="pasan {v} años de abundancia"),
            C("Gn 45:6", {"TM": ("dos años de hambre", "dos"), "LXX": ("this second year there is famine", "second")},
              signo=-1, texto="y {v} de hambre hasta la llegada de Jacob")],
           "Cálculo de varios pasos (supuesto «jose»): Jacob tendría unos 91 años al nacer José.")
    nac["Joseph_1"] = JO = "ev-nac-jose"
    evento("ev-jose-17", "José, de 17 años, apacienta las ovejas; es vendido", "evento", "Gn 37:2", ["Joseph_1"], JO,
           [E("Joseph_1", "en_evento", "Gn 37:2", texto="José tenía {v} años")],
           "Gn 37 no dice cuánto tiempo pasa entre Gn 37:2 y la venta.")
    evento("ev-jose-faraon", "José se presenta ante Faraón", "evento", "Gn 41:46", ["Joseph_1"], JO,
           [E("Joseph_1", "en_evento", "Gn 41:46", texto="José tenía {v} años")])
    evento("ev-muerte-jacob", "Muere Jacob", "muerte", "Gn 47:28", ["Jacob_1"], J, [E("Jacob_1", "total", texto="Jacob vivió {v} años")])
    evento("ev-muerte-jose", "Muere José", "muerte", "Gn 50:26", ["Joseph_1"], JO, [E("Joseph_1", "total", texto="José vivió {v} años")])
    # Éxodo: la salida se enlaza con Génesis por los 430 años de Ex 12:40 (supuesto «e430»).
    C430 = C("Ex 12:40", {"TM": ("cuatrocientos treinta años", "cuatrocientos treinta"),
                          "LXX": ("four hundred and thirty years", "four hundred and thirty")},
             texto="{v} años de Ex 12:40")
    ev.append(dict(id="ev-salida-egipto", titulo="Salida de Egipto", tipo="evento", ref="Ex 12:41",
                   personas=["Moses_1", "Aaron_1"], depende_de=A,
                   variantes=[({"e430": "egipto"}, [
                       E("Abram_1", "en_evento", "Gn 21:5", texto="Abraham tenía {v} años cuando le nació Isaac"),
                       E("Isaac_1", "en_evento", "Gn 25:26", texto="Isaac tenía {v} años cuando nació Jacob"),
                       E("Jacob_1", "en_evento", "Gn 47:9", texto="Jacob tenía {v} años al entrar en Egipto"),
                       dict(C430, texto="los hijos de Israel habitaron en Egipto {v} años (Ex 12:40, solo Egipto)")]),
                       ({"e430": "canaan"}, [
                           E("Abram_1", "en_evento", "Gn 12:4", texto="Abram tenía {v} años al salir de Harán hacia Canaán"),
                           dict(C430, texto="{v} años en Canaán y en Egipto (Ex 12:40 según la LXX)")])],
                   nota="Ex 12:41: «pasados cuatrocientos treinta años, en el mismo día salieron». El punto de partida "
                        "de los 430 años depende del supuesto «e430»."))
    S = "ev-salida-egipto"
    evento("ev-nac-moises", "Nace Moisés", "nacimiento", "Ex 2:2", ["Moses_1"], S,
           [E("Moses_1", "en_evento", "Ex 7:7", signo=-1, texto="Moisés tenía {v} años cuando hablaron a Faraón")],
           "Cálculo hacia atrás desde Ex 7:7; supone que Moisés y Aarón hablan a Faraón el mismo año de la salida "
           "(las plagas y la salida se narran seguidas, sin cifra de tiempo).")
    nac["Moses_1"] = "ev-nac-moises"
    evento("ev-nac-aaron", "Nace Aarón", "nacimiento", "Ex 7:7", ["Aaron_1"], S,
           [E("Aaron_1", "en_evento", "Ex 7:7", signo=-1, texto="Aarón tenía {v} años cuando hablaron a Faraón")],
           "Mismo supuesto que el nacimiento de Moisés.")
    nac["Aaron_1"] = "ev-nac-aaron"
    evento("ev-ante-faraon", "Moisés y Aarón hablan a Faraón", "evento", "Ex 7:7", ["Moses_1", "Aaron_1"], "ev-nac-moises",
           [E("Moses_1", "en_evento", "Ex 7:7", texto="Moisés tenía {v} años")])
    evento("ev-llegada-sinai", "Israel llega al desierto de Sinaí", "evento", "Ex 19:1", ["Moses_1"], S, [],
           "«Al mes tercero de la salida» (Ex 19:1): mismo año del cálculo que la salida.")
    evento("ev-tabernaculo", "Se erige el tabernáculo", "evento", "Ex 40:17", ["Moses_1"], S,
           [C("Ex 40:17", {"TM": ("en el segundo año", "segundo"), "LXX": ("in the second year", "second")},
              texto="«el segundo año» ({v}) desde la salida"),
            F(1, "Ex 40:17", signo=-1, texto="el primer año es el de la salida: se resta {v}")],
           "Ex 40:17: el día primero del primer mes del segundo año (la LXX añade «after their going forth out of Egypt»).")
    # Números: fechas relativas a la salida (Nm 1:1; 9:1; 10:11; 33:38). Mismo convenio que Ex 40:17.
    SEG = lambda ref, tm: [C(ref, {"TM": (tm, "segundo"), "LXX": ("in the second year", "second")},
                             texto="«el segundo año» ({v}) de la salida"),
                           F(1, ref, signo=-1, texto="el primer año es el de la salida: se resta {v}")]
    evento("ev-censo-sinai", "Censo en el desierto de Sinaí", "evento", "Nm 1:1", ["Moses_1", "Aaron_1"], S,
           SEG("Nm 1:1", "en el segundo año"), "Nm 1:1: el día primero del mes segundo, en el segundo año de la salida.")
    evento("ev-pascua-sinai", "Pascua en el desierto de Sinaí", "evento", "Nm 9:1", ["Moses_1"], S,
           SEG("Nm 9:1", "en el segundo año"), "Nm 9:1-5: en el mes primero del segundo año, el día catorce.")
    evento("ev-salida-sinai", "Israel parte del Sinaí", "evento", "Nm 10:11", ["Moses_1"], S,
           SEG("Nm 10:11", "en el año segundo"), "Nm 10:11: el día veinte del mes segundo del año segundo.")
    C3338 = {"TM": ("á los cuarenta años de la salida", "cuarenta"), "LXX": ("in the fortieth year", "fortieth")}
    ev.append(dict(id="ev-muerte-aaron", titulo="Muere Aarón en el monte Hor", tipo="muerte", ref="Nm 33:38",
                   personas=["Aaron_1"], depende_de=S, margen_total=1,
                   variantes=[({"tradicion": "TM"}, [
                       C("Nm 33:38", C3338, texto="la RV1909 dice que murió «á los cuarenta años de la salida» ({v})")]),
                       ({"tradicion": "LXX"}, [
                           C("Nm 33:38", C3338, texto="la LXX dice «in the fortieth year» (año {v} desde la salida)"),
                           F(1, "Nm 33:38", signo=-1, texto="el primer año es el de la salida: se resta {v}")])],
                   nota=("Nm 33:38: en el mes quinto, el día primero. TM (RV1909): «á los cuarenta años de la salida»: "
                         "83 años en Ex 7:7 + 40 = 123, lo que dice Nm 33:39. LXX: «in the fortieth year» da 39 años "
                         "desde la salida y 83 + 39 = 122; la diferencia de un año cabe en lo que el cálculo no cuenta "
                         "(Ex 7:7 ocurre antes de la salida y Aarón muere en el mes quinto).")))
    # Deuteronomio: Dt 1:3 fecha los discursos desde la salida, como Nm 33:38; la muerte de Moisés no lleva año.
    C13 = {"TM": ("á los cuarenta años", "cuarenta"), "LXX": ("in the fortieth year", "fortieth")}
    ev.append(dict(id="ev-discursos-moab", titulo="Moisés habla a Israel en Moab", tipo="evento", ref="Dt 1:3",
                   personas=["Moses_1"], depende_de=S,
                   variantes=[({"tradicion": "TM"}, [
                       C("Dt 1:3", C13, texto="la RV1909 dice «á los cuarenta años» ({v}) de la salida")]),
                       ({"tradicion": "LXX"}, [
                           C("Dt 1:3", C13, texto="la LXX dice «in the fortieth year» (año {v} desde la salida)"),
                           F(1, "Dt 1:3", signo=-1, texto="el primer año es el de la salida: se resta {v}")])],
                   nota=("Dt 1:3: en el mes undécimo, el día primero. Se lee igual que Nm 33:38 (muerte de Aarón, mes "
                         "quinto del mismo año): TM «á los cuarenta años» → 40; LXX «in the fortieth year» → 39.")))
    ev.append(dict(id="ev-muerte-moises", titulo="Muere Moisés en Moab", tipo="muerte", ref="Dt 34:5",
                   personas=["Moses_1"], depende_de="ev-discursos-moab", margen_total=1, pasos=[],
                   nota=("El texto no da el año de su muerte: Dt 1:3 sitúa los discursos en el mes undécimo del año "
                         "cuarenta y Dt 34:8 da treinta días de luto; se toma el mismo año del cálculo. TM: 80 años en "
                         "Ex 7:7 + 40 = 120, lo que dicen Dt 31:2 y Dt 34:7. LXX: 80 + 39 = 119 frente a 120 en Dt 34:7; "
                         "la diferencia de un año cabe en lo que el cálculo no cuenta (Ex 7:7 ocurre antes de la salida).")))
    # Josué: el paso del Jordán es el primer «mes primero» después de Dt 1:3 (mes undécimo) y Dt 34:8 (30 días de luto).
    ev.append(dict(id="ev-paso-jordan", titulo="Israel pasa el Jordán y acampa en Gilgal", tipo="evento", ref="Jos 4:19",
                   personas=["Joshua_1"], depende_de="ev-discursos-moab",
                   pasos=[F(1, "Jos 4:19", texto="Dt 1:3 es el mes undécimo; con los treinta días de luto (Dt 34:8), el "
                                                  "«mes primero» de Jos 4:19 es el del año siguiente: se suma {v}")],
                   nota=("Jos 4:19: «el diez del mes primero». El texto no da el año: Dt 1:3 sitúa los discursos en el mes "
                         "undécimo del año cuarenta y Dt 34:8 da treinta días de luto por Moisés; Jos 1:11 y 3:2 hablan de "
                         "tres días. Se toma el primer mes primero posible, el del año siguiente: TM 40 + 1 = 41 años desde la "
                         "salida; LXX 39 + 1 = 40 (Dt 1:3 «in the fortieth year»). Si pasara más tiempo, el año sería posterior; "
                         "nada en el texto lo indica.")))
    ev.append(dict(id="ev-pascua-gilgal", titulo="Pascua en Gilgal; cesa el maná", tipo="evento", ref="Jos 5:10",
                   personas=["Joshua_1"], depende_de="ev-paso-jordan", pasos=[],
                   nota="Jos 5:10-12: «á los catorce días del mes», cuatro días después de pasar el Jordán (Jos 4:19): mismo año."))
    # Caleb: 40 años al ser enviado (Jos 14:7) y 85 «hoy» (Jos 14:10), 45 años después (40 + 45 = 85).
    ev.append(dict(id="ev-nac-caleb", titulo="Nace Caleb", tipo="nacimiento", ref="Jos 14:7", personas=["Caleb_1"],
                   depende_de="ev-salida-sinai",
                   pasos=[E("Caleb_1", "en_evento", "Jos 14:7", signo=-1,
                            texto="Caleb tenía {v} años cuando Moisés lo envió de Cades-barnea")],
                   nota=("Cálculo hacia atrás desde Jos 14:7. Supone que los espías salen de Cades el mismo año en que Israel "
                         "deja el Sinaí (Nm 10:11, «el año segundo»); Nm 13 no da el año del envío.")))
    ev.append(dict(id="ev-caleb-hebron", titulo="Caleb pide Hebrón a los 85 años", tipo="evento", ref="Jos 14:10",
                   personas=["Caleb_1"], depende_de="ev-nac-caleb",
                   pasos=[E("Caleb_1", "en_evento", "Jos 14:10", texto="Caleb dice tener hoy {v} años")],
                   nota=("Comprobación: 40 años al ser enviado (Jos 14:7) + «estos cuarenta y cinco años» (Jos 14:10) = 85, "
                         "lo que dice Jos 14:10. El año resulta 45 después de la salida del Sinaí, con el mismo supuesto que "
                         "el nacimiento de Caleb.")))
    # Muertes de Gn 5 y 11
    for p in dict.fromkeys([x[0] for x in GN5] + ["Noah_1", "Shem_1", "Arpachshad_1", "Cainan_1", "Shelah_1"] + [x[0] for x in GN11] + ["Terah_1"]):
        if p == "Enoch_2":
            evento("ev-fin-enoc", "Enoc desaparece («le llevó Dios»)", "evento", "Gn 5:24", [p], nac[p],
                   [E(p, "total", texto="Los días de Enoc fueron {v} años")])
            continue
        slug = "adan" if nac[p] == "ev-adan" else nac[p].replace("ev-nac-", "")
        evento(f"ev-muerte-{slug}", f"Muere {nombre(p)}", "muerte", None, [p], nac[p],
               [E(p, "total", texto=f"{nombre(p)} vivió {{v}} años")])
    return ev, nac


HITOS = [
    ("Caín mata a Abel", "Gn 4:8"), ("La torre de Babel", "Gn 11:1-9"), ("Abram y Lot se separan", "Gn 13:5-12"),
    ("La guerra de los reyes y Melquisedec", "Gn 14:1-24"), ("Destrucción de Sodoma y Gomorra", "Gn 19:24-25"),
    ("La prueba de Abraham en Moriah", "Gn 22:1-19"), ("El sueño de Jacob en Betel", "Gn 28:10-22"),
    ("Jacob sirve a Labán y se casa con Lea y Raquel", "Gn 29:15-30"), ("La lucha de Jacob en Peniel", "Gn 32:24-32"),
    ("Encuentro de Jacob y Esaú", "Gn 33:1-17"), ("Dina y Siquem", "Gn 34:1-31"), ("Muerte de Raquel", "Gn 35:16-20"),
    ("Judá y Tamar", "Gn 38:1-30"), ("Bendiciones de Jacob a sus hijos", "Gn 49:1-28"),
]
NOTA_HITO_GN = "Génesis no da edad ni año: va solo en el orden del relato."
NOTA_SIN_NAC = ("El texto da la edad total ({v}), pero ni su año de nacimiento ni la edad del padre al engendrarlo: "
                "no hay base para fecharla.")
HITOS_EX = [
    ("Muere Leví", "Ex 6:16", NOTA_SIN_NAC.format(v="Ex 6:16")),
    ("Muere Coat", "Ex 6:18", NOTA_SIN_NAC.format(v="Ex 6:18")),
    ("Muere Amram", "Ex 6:20", NOTA_SIN_NAC.format(v="Ex 6:20")),
    ("Moisés huye a Madián", "Ex 2:11-15", "Éxodo no dice qué edad tenía Moisés."),
    ("La zarza ardiente en Horeb", "Ex 3:1-6", "Éxodo no da el año; Ex 7:7 da la edad de Moisés algo después."),
    ("El paso del mar Bermejo", "Ex 14:21-31", "Ocurre poco después de la salida; el texto no da cifra de tiempo."),
    ("El becerro de oro", "Ex 32:1-6", "Entre la llegada al Sinaí y la erección del tabernáculo; sin cifra de año."),
]
HITOS_NM = [
    ("Muere María (Miriam) en Cades", "Nm 20:1", "El texto da «el mes primero» pero no el año."),
    ("Los doce enviados reconocen la tierra", "Nm 13:2-33",
     "Números no da el año; Nm 13:26 (RV1909) dice que volvieron «al cabo de cuarenta días»."),
    ("La rebelión de Coré, Datán y Abiram", "Nm 16:1-35", "Números no da el año."),
    ("La serpiente de bronce", "Nm 21:4-9", "Números no da el año; Nm 21:4 la sitúa después de partir del monte Hor."),
    ("Balac y Balaam", "Nm 22:1-24:25", "Números no da el año."),
]
HITOS_JOS = [
    ("Caen los muros de Jericó", "Jos 6:1-21", "Josué no da el año; ocurre después de la Pascua de Gilgal (Jos 5:10)."),
    ("El sol se detiene en Gabaón", "Jos 10:12-14", "Sin cifra de año."),
    ("El reparto de la tierra en Siloh", "Jos 18:1-10", "Sin cifra de año; Jos 14:10 sitúa a Caleb 45 años después del envío."),
    ("Pacto en Siquem", "Jos 24:1-28", "Sin cifra de año."),
    ("Muere Josué a los 110 años", "Jos 24:29",
     "El texto da su edad (110, Jos 24:29; también en la LXX) pero no su año de nacimiento ni cuánto tiempo pasa desde la "
     "entrada en la tierra (Jos 23:1 dice solo que pasaron muchos días): no hay base para fecharla."),
    ("Muere Eleazar", "Jos 24:33", "Sin edad ni año."),
]


# Jueces: duraciones que da el texto (opresión, reposo, gobierno de un juez). El texto no dice si son consecutivas ni
# si se solapan: no se convierten en años desde Adán. 1 Re 6:1 (480 años desde la salida) queda para cuando llegue Reyes.
# (id, tipo, título, ref, cita TM (RV1909), cita LXX (Brenton))
PERIODOS_JUE = [
    ("jue-cusan", "opresion", "Israel sirve a Cusán-risataim", "Jue 3:8", "ocho años", "eight years"),
    ("jue-reposo-otoniel", "reposo", "Reposo tras Otoniel", "Jue 3:11", "cuarenta años", "forty years"),
    ("jue-eglon", "opresion", "Israel sirve a Eglón", "Jue 3:14", "diez y ocho años", "eighteen years"),
    ("jue-reposo-aod", "reposo", "Reposo tras Aod", "Jue 3:30", "ochenta años", "eighty years"),
    ("jue-jabin", "opresion", "Jabín oprime a Israel", "Jue 4:3", "veinte años", "twenty years"),
    ("jue-reposo-debora", "reposo", "Reposo tras Débora y Barac", "Jue 5:31", "cuarenta años", "forty years"),
    ("jue-madian", "opresion", "Israel en manos de Madián", "Jue 6:1", "siete años", "seven years"),
    ("jue-reposo-gedeon", "reposo", "Reposo en los días de Gedeón", "Jue 8:28", "cuarenta años", "forty years"),
    ("jue-abimelec", "gobierno", "Abimelec domina sobre Israel", "Jue 9:22", "tres años", "three years"),
    ("jue-tola", "juez", "Tola juzga a Israel", "Jue 10:2", "veintitrés años", "twenty-three years"),
    ("jue-jair", "juez", "Jair juzga a Israel", "Jue 10:3", "veintidós años", "twenty-two years"),
    ("jue-ammon", "opresion", "Ammón oprime a Israel", "Jue 10:8", "dieciocho años", "eighteen years"),
    ("jue-jefte", "juez", "Jefté juzga a Israel", "Jue 12:7", "seis años", "six years"),
    ("jue-ibzan", "juez", "Ibzán juzga a Israel", "Jue 12:9", "siete años", "seven years"),
    ("jue-elon", "juez", "Elón juzga a Israel", "Jue 12:11", "diez años", "ten years"),
    ("jue-abdon", "juez", "Abdón juzga a Israel", "Jue 12:14", "ocho años", "eight years"),
    ("jue-filisteos", "opresion", "Israel en manos de los filisteos", "Jue 13:1", "cuarenta años", "forty years"),
    ("jue-sanson", "juez", "Sansón juzga a Israel «en días de los Filisteos»", "Jue 15:20", "veinte años", "twenty years"),
]
REPITE_JUE = {"jue-sanson": ("Jue 16:31", "juzgó á Israel veinte años", "judged Israel twenty years")}
TRESCIENTOS = ("Jue 11:26", "trescientos años", "three hundred years")
ADV_JUE = ("El texto no dice si estos periodos se suceden uno tras otro ni si se solapan: la suma solo vale si fueran "
           "consecutivos.")


def duraciones_jueces(textos, numeral, errores):
    """Periodos de Jueces (texto, TM y LXX) y dos sumas (cálculo). Devuelve (duraciones, hitos) o (None, [])."""
    if "Jue 3:8" not in textos["TM"]:
        return None, []
    per, val = [], {}
    for pid, tipo, titulo, ref, c_tm, c_lxx in PERIODOS_JUE:
        citas = {}
        for trad, cita, idioma, fuente in (("TM", c_tm, "es", "rv1909"), ("LXX", c_lxx, "en", "brenton")):
            if cita not in textos[trad].get(ref, ""):
                errores.append(f"Duración de Jueces: «{cita}» no está en {ref} ({trad})")
            n = numeral(re.sub(r"\s+(años|years)$", "", cita), idioma)
            citas[trad] = {"cita": cita, "fuente": fuente, "valor": n}
        if citas["TM"]["valor"] != citas["LXX"]["valor"]:
            errores.append(f"Duración de Jueces {ref}: TM {citas['TM']['valor']} ≠ LXX {citas['LXX']['valor']}")
        val[pid] = citas["TM"]["valor"]
        d = {"id": pid, "tipo": tipo, "titulo": titulo, "ref": ref, "valor": val[pid], "certeza": "texto", "citas": citas}
        if pid in REPITE_JUE:
            r2, t2, l2 = REPITE_JUE[pid]
            if t2 not in textos["TM"].get(r2, "") or l2 not in textos["LXX"].get(r2, ""):
                errores.append(f"Duración de Jueces: {r2} no repite la cifra")
            d["tambien"] = {"ref": r2, "cita": t2}
        per.append(d)
    if not all(c in textos[t].get(TRESCIENTOS[0], "") for t, c in (("TM", TRESCIENTOS[1]), ("LXX", TRESCIENTOS[2]))):
        errores.append("Jue 11:26 no dice «trescientos años»")
    t300 = numeral(TRESCIENTOS[1].replace(" años", ""), "es")

    def suma(ids):
        pasos = [{"ref": p["ref"], "texto": p["titulo"], "valor": p["valor"], "signo": 1} for p in per if p["id"] in ids]
        return pasos, sum(x["valor"] for x in pasos)

    orden = [p["id"] for p in per]
    p1, s1 = suma(orden[:orden.index("jue-ammon") + 1])
    p2, s2 = suma(orden)
    calculos = [
        {"id": "jue-suma-hasta-jefte", "titulo": "Suma de los periodos de Jue 3:8–10:8 (hasta Jefté)", "certeza": "calculo",
         "pasos": p1, "total": s1, "advertencia": ADV_JUE,
         "comparacion": {"ref": TRESCIENTOS[0], "cita": TRESCIENTOS[1], "valor": t300, "certeza": "texto",
                         "nota": (f"Jefté dice que Israel habita en Hesbón desde hace «trescientos años» (Jue 11:26), contando "
                                  f"desde la conquista de Hesbón (Nm 21:25), antes de Josué. Si los periodos de Jue 3:8–10:8 "
                                  f"fueran consecutivos sumarían {s1}, más que {t300} sin contar el tiempo de Josué y de los "
                                  "ancianos (sin cifra). El texto no explica la diferencia (cifra redonda, periodos que se "
                                  "solapan u otra cosa): no se decide.")}},
        {"id": "jue-suma-total", "titulo": "Suma de todos los periodos con cifra de Jueces (Jue 3:8–15:20)",
         "certeza": "calculo", "pasos": p2, "total": s2,
         "advertencia": ADV_JUE + " Además, Jue 15:20 sitúa los veinte años de Sansón «en días de los Filisteos», sin "
                                  "decir si caen dentro de los cuarenta de Jue 13:1."},
    ]
    v = lambda i: val[i]  # noqa: E731
    hitos = [
        ("Otoniel libra a Israel de Cusán-risataim", "Jue 3:7-11",
         f"Texto: {v('jue-cusan')} años de servidumbre (Jue 3:8) y {v('jue-reposo-otoniel')} de reposo (Jue 3:11). Sin año: "
         "el texto no dice cuánto pasó desde la muerte de Josué."),
        ("Aod mata a Eglón", "Jue 3:12-30",
         f"Texto: {v('jue-eglon')} años de servidumbre (Jue 3:14) y {v('jue-reposo-aod')} de reposo (Jue 3:30)."),
        ("Samgar hiere a seiscientos filisteos", "Jue 3:31", "Sin cifra de tiempo."),
        ("Débora y Barac vencen a Sísara", "Jue 4:1-5:31",
         f"Texto: {v('jue-jabin')} años de opresión de Jabín (Jue 4:3) y {v('jue-reposo-debora')} de reposo (Jue 5:31)."),
        ("Gedeón vence a Madián", "Jue 6:1-8:35",
         f"Texto: {v('jue-madian')} años en manos de Madián (Jue 6:1) y {v('jue-reposo-gedeon')} de reposo «en los días "
         "de Gedeón» (Jue 8:28)."),
        ("Abimelec, rey en Siquem", "Jue 9:1-57", f"Texto: domina {v('jue-abimelec')} años sobre Israel (Jue 9:22)."),
        ("Tola y Jair juzgan a Israel", "Jue 10:1-5",
         f"Texto: Tola {v('jue-tola')} años (Jue 10:2), Jair {v('jue-jair')} (Jue 10:3)."),
        ("Jefté vence a Ammón", "Jue 10:6-12:7",
         f"Texto: {v('jue-ammon')} años de opresión (Jue 10:8); Jefté juzga {v('jue-jefte')} (Jue 12:7). Jue 11:26 da "
         f"«trescientos años» desde que Israel habita en Hesbón. Cálculo: si los periodos de Jue 3:8–10:8 fueran "
         f"consecutivos sumarían {s1} años, más que esos {t300}. " + ADV_JUE),
        ("Ibzán, Elón y Abdón juzgan a Israel", "Jue 12:8-15",
         f"Texto: {v('jue-ibzan')} años (Jue 12:9), {v('jue-elon')} (Jue 12:11) y {v('jue-abdon')} (Jue 12:14)."),
        ("Sansón", "Jue 13:1-16:31",
         f"Texto: {v('jue-filisteos')} años en manos de los filisteos (Jue 13:1); Sansón juzga {v('jue-sanson')} años «en "
         f"días de los Filisteos» (Jue 15:20; 16:31). Cálculo: todos los periodos con cifra de Jue 3:8–15:20 suman {s2} "
         "años si fueran consecutivos; el texto no lo dice."),
        ("Micaía y la migración de Dan", "Jue 17:1-18:31", "Sin cifra de tiempo."),
        ("La guerra contra Benjamín", "Jue 19:1-21:25",
         "Sin cifra de tiempo. Jue 20:28 dice que entonces ministraba Finees, hijo de Eleazar, hijo de Aarón."),
    ]
    dur = {"libro": "Jue", "nota": ADV_JUE + " No se fechan desde Adán ni se usa 1 Re 6:1.", "periodos": per,
           "calculos": calculos}
    return dur, hitos


def construir(edades, nombre, textos, numeral, parse_gn, pasaje_de, errores):
    """textos = {"TM": rv, "LXX": br}; numeral(frase, idioma) -> int."""
    idx = {}
    for e in edades:
        idx.setdefault((e["persona"], e["tipo"], e["tradicion"]), []).append(e)
    usadas = set()

    def edad(persona, tipo, ref, trad):
        c = [e for e in idx.get((persona, tipo, trad), []) if ref is None or e["ref"] == ref]
        if len(c) > 1:
            c = [e for e in c if e["certeza"] == "texto"] or c
        if len(c) > 1:
            errores.append(f"Edad ambigua {persona} {tipo} {trad}")
        if c:
            usadas.add((persona, tipo, ref))
            return c[0]["valor"]
        return None

    def constante(ref, citas, trad):
        cita, num = citas[trad]
        verso = textos[trad].get(parse_gn(ref), "")
        if cita not in verso or num not in cita:
            errores.append(f"Constante no literal en {ref} ({trad}): {cita!r}")
            return None
        frase = num.replace("first", "one").replace("second", "two").replace("segundo", "dos").replace("fortieth", "forty")
        return numeral(frase, "es" if trad == "TM" else "en")

    # Citas del supuesto e430, verificadas contra el texto.
    for s in SUPUESTOS:
        if s["id"] != "e430":
            continue
        s["citas"] = {}
        for trad, (ref, fuente, clave) in CITAS_430.items():
            verso = textos[trad].get(parse_gn(ref), "")
            if clave not in verso:
                errores.append(f"Supuesto e430: «{clave}» no está en {ref} ({trad})")
            s["citas"][trad] = {"ref": ref, "fuente": fuente, "texto": verso, "clave": clave}

    ev, nac = definir(nombre)
    por_id = {e["id"]: e for e in ev}
    # ciclo
    for e in ev:
        vistos, x = set(), e
        while x and x["depende_de"]:
            if x["id"] in vistos:
                errores.append(f"Ciclo en depende_de: {e['id']}"); break
            vistos.add(x["id"]); x = por_id.get(x["depende_de"])
            if x is None:
                errores.append(f"depende_de inexistente en {e['id']}"); break
    combos = [dict(tradicion=t, tare=a, sem=b, jose="jose91", e430=x) for t in TRADS for a in ("tare70", "tare130")
              for b in ("sem2", "noe500") for x in ("egipto", "canaan")]
    cid = lambda c: f"{c['tradicion']}|{c['tare']}|{c['sem']}|{c['e430']}"

    def pasos_de(e, c):
        if "variantes" not in e:
            return e["pasos"]
        for cond, pasos in e["variantes"]:
            if all(c.get(k) == v for k, v in cond.items()):
                return pasos
        return None

    def valor_paso(p, trad):
        if "edad" in p:
            return edad(*p["edad"], trad)
        if "fija" in p:
            return p["fija"]
        return constante(*p["constante"], trad)

    memo = {}

    def anio(eid, c):
        k = (eid, cid(c))
        if k in memo:
            return memo[k]
        e = por_id[eid]
        base = 0 if e["depende_de"] is None else anio(e["depende_de"], c)
        pasos = pasos_de(e, c)
        r = None
        if base is not None and pasos is not None:
            r = base
            for p in pasos:
                v = valor_paso(p, c["tradicion"])
                if v is None:
                    r = None; break
                r += p["signo"] * v
        memo[k] = r
        return r

    def salida_pasos(pasos, trad="TM"):
        out = []
        for p in pasos or []:
            v = valor_paso(p, trad)
            d = {"texto": p["texto"].replace("{v}", str(v) if v is not None else "?"), "signo": p["signo"]}
            if "edad" in p:
                persona, tipo, ref = p["edad"]
                d["ref"] = ref or next((e["ref"] for e in idx.get((persona, tipo, trad), [])), None)
                d["edad"] = {"persona": persona, "tipo": tipo} | ({"ref": ref} if ref else {})
            elif "fija" in p:
                d["ref"] = p["ref"]
                d["convencion"] = True
            else:
                d["ref"] = p["constante"][0]
                d["cifra_texto"] = {t: p["constante"][1][t][0] for t in TRADS}
            out.append(d)
        return out

    eventos = []
    for e in ev:
        pasos0 = pasos_de(e, combos[0])
        ref = e["ref"] or (salida_pasos(pasos0)[0]["ref"] if pasos0 else None)
        d = {"id": e["id"], "titulo": e["titulo"], "tipo": e["tipo"], "ref": ref, "pasaje": pasaje_de(ref),
             "personas": e["personas"], "depende_de": e["depende_de"], "pasos": salida_pasos(pasos0),
             "anios": {cid(c): anio(e["id"], c) for c in combos}, "certeza": "calculo", "nota": e.get("nota", "")}
        if "variantes" in e:
            d["variantes"] = [{"cuando": cond, "pasos": salida_pasos(p, cond.get("tradicion", "TM")) if p is not None else None}
                              for cond, p in e["variantes"]]
        eventos.append(d)
    E_ = {d["id"]: d for d in eventos}
    # Matusalén y quién vive al diluvio
    vivos = {}
    for c in combos:
        dil = E_["ev-diluvio"]["anios"][cid(c)]
        lst = []
        for p, ev_nac in nac.items():
            m = next((d for d in eventos if d["tipo"] in ("muerte", "evento") and d["id"].startswith(("ev-muerte-", "ev-fin-enoc"))
                      and d["personas"] == [p]), None)
            a, b = E_[ev_nac]["anios"][cid(c)], (m["anios"][cid(c)] if m else None)
            if a is not None and b is not None and dil is not None and a <= dil <= b:
                lst.append((p, b - dil))
        vivos[cid(c)] = lst
    for c in ("TM|tare70|sem2|egipto", "LXX|tare70|sem2|egipto"):
        mat = dict(vivos[c]).get("Methuselah_1")
        if mat is not None:
            tr = c.split("|")[0]
            E_["ev-muerte-matusalen"]["nota"] += (f" {tr}: el cálculo da su muerte {mat} años después del comienzo del diluvio"
                                                  f"{' (el mismo año)' if mat == 0 else ''}; es resultado del cálculo, no se corrige.")
    # muerte = nacimiento + total
    for d in eventos:
        if d["tipo"] == "muerte" or d["id"] == "ev-fin-enoc":
            p = d["personas"][0]
            for c in combos:
                a, b = E_[nac[p]]["anios"][cid(c)], d["anios"][cid(c)]
                t = edad(p, "total", None, c["tradicion"])
                margen = por_id[d["id"]].get("margen_total", 0)  # año que el cálculo no distingue (nota del evento)
                if a is not None and b is not None and t is not None and not 0 <= t - (b - a) <= margen:
                    errores.append(f"Muerte ≠ nacimiento + total: {p} {cid(c)}")
    cron = {"unidad": "años desde la creación de Adán (cálculo)", "supuestos": SUPUESTOS, "notas": NOTAS,
            "combinaciones": [{"id": cid(c), "tradicion": c["tradicion"],
                               "supuestos": {"tare": c["tare"], "sem": c["sem"], "jose": c["jose"], "e430": c["e430"]}}
                              for c in combos],
            "eventos": eventos,
            "hitos_sin_fecha": [{"titulo": t, "ref": r, "nota": NOTA_HITO_GN} for t, r in HITOS]
                               + [{"titulo": t, "ref": r, "nota": n} for t, r, n in HITOS_EX + HITOS_NM + HITOS_JOS]}
    dur, hitos_jue = duraciones_jueces(textos, numeral, errores)
    if dur:
        cron["duraciones"] = dur
        cron["hitos_sin_fecha"] += [{"titulo": t, "ref": r, "nota": n} for t, r, n in hitos_jue]
    return cron, vivos, usadas
