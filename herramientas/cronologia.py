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
]
NOTAS = ["Cainán, hijo de Arfaxad (Gn 11:12-13), solo existe en la Septuaginta: en la LXX su generación (130 años) se suma "
         "en la cadena; en el TM no existe. No es un supuesto: es propio de cada tradición.",
         "Convención del cálculo: una edad N al ocurrir algo se cuenta como N años después del nacimiento.",
         "La LXX es la de Brenton (1851); otros manuscritos dan cifras distintas."]

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
    # Muertes de Gn 5 y 11
    for p in [x[0] for x in GN5] + ["Noah_1", "Shem_1", "Arpachshad_1", "Cainan_1", "Shelah_1"] + [x[0] for x in GN11] + ["Terah_1"]:
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
        frase = num.replace("first", "one").replace("second", "two")
        return numeral(frase, "es" if trad == "TM" else "en")

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
    combos = [dict(tradicion=t, tare=a, sem=b, jose="jose91") for t in TRADS for a in ("tare70", "tare130") for b in ("sem2", "noe500")]
    cid = lambda c: f"{c['tradicion']}|{c['tare']}|{c['sem']}"

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
    for c in ("TM|tare70|sem2", "LXX|tare70|sem2"):
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
                if a is not None and b is not None and b - a != t:
                    errores.append(f"Muerte ≠ nacimiento + total: {p} {cid(c)}")
    cron = {"unidad": "años desde la creación de Adán (cálculo)", "supuestos": SUPUESTOS, "notas": NOTAS,
            "combinaciones": [{"id": cid(c), "tradicion": c["tradicion"], "supuestos": {"tare": c["tare"], "sem": c["sem"], "jose": c["jose"]}}
                              for c in combos],
            "eventos": eventos,
            "hitos_sin_fecha": [{"titulo": t, "ref": r, "nota": "Génesis no da edad ni año: va solo en el orden del relato."}
                                for t, r in HITOS]}
    return cron, vivos, usadas
