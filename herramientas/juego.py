"""Genera datos/juego.js (window.BIBLIA_JUEGO): catálogo de juego (genealogías, historias, personajes, objetos,
escenarios) a partir de las fuentes por libro herramientas/juego/<Libro>.json, verificadas contra datos/biblia.js
(texto RV1909) y datos/tabernaculo.js.

Sin red. Regenerar: python -I herramientas/juego.py
Opciones:
  --fuentes DIR   lee las fuentes de DIR (por defecto herramientas/juego)
  --salida RUTA   escribe en RUTA (por defecto datos/juego.js)
  --sin-salida    solo verifica, no escribe nada
  --autoprueba    corre el fixture herramientas/juego/_prueba: debe pasar, y dos copias alteradas
                  (cita no literal; aparición dentro de una genealogía) deben fallar. No escribe nada.

Si falla una verificación imprime cada error con su ruta (libro · sección · id · campo), un resumen por libro y
tipo, y sale con código != 0 sin escribir la salida. Diseño: docs/superpowers/specs/2026-11-11-catalogo-juego-design.md
"""
import copy
import datetime
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"
FUENTES = Path(__file__).resolve().parent / "juego"
PRUEBA = FUENTES / "_prueba"
SALIDA = DATOS / "juego.js"

NIVEL_TOPE = 12
CERTEZAS = ("texto", "inferido")
ABRAHAM, MOISES, ADAN = "Abram_1", "Moses_1", "Adam_1"

# --------------------------------------------------------------------------- hechos obligatorios (ampliable por libro)
# Solo se exigen los del libro si ese libro está cargado.
HECHOS = {
    "Gn": {
        "genealogia": [("Gn 5:1", "Gn 5:32"), ("Gn 10:1", "Gn 10:1"), ("Gn 11:10", "Gn 11:26"),
                       ("Gn 25:12", "Gn 25:18"), ("Gn 36:1", "Gn 36:1"), ("Gn 46:8", "Gn 46:27")],
        "aparece": [(ADAN, "Gn 2:7")],
        "objeto_en": [("Gn 6:14", "arca de Noé")],
        "escenario_lugar": ["eden"],
        "principal": [(ABRAHAM, "Gn", "Gn 25")],   # (persona, libro de la historia, listo.capitulo exigido o None)
    },
    "Ex": {
        "genealogia": [("Ex 6:14", "Ex 6:25")],
        "objeto_en": [("Ex 4:2", "vara de Moisés")],
        "principal": [(MOISES, "Ex", None)],
    },
    "Lv": {
        "aparece": [("Nadab_1", "Lv 10:1"), ("Abihu_1", "Lv 10:1"), ("Shelomith_1", "Lv 24:11")],
        "objeto_en": [("Lv 16:8", "macho cabrío de Azazel"), ("Lv 8:8", "Urim y Tumim")],
        "escenario_lugar": ["sinai"],
        "principal": [("Aaron_1", "Lv", None), ("Nadab_1", "Lv", "Lv 10")],
    },
    "Nm": {
        "genealogia": [("Nm 1:5", "Nm 1:16"), ("Nm 13:4", "Nm 13:16"), ("Nm 26:5", "Nm 26:62"), ("Nm 34:19", "Nm 34:28")],
        "aparece": [("Korah_3", "Nm 16:1"), ("Balaam_1", "Nm 22:7")],
        "objeto_en": [("Nm 21:9", "serpiente de bronce")],
        "escenario_lugar": ["monte-hor"],
        "principal": [("Balaam_1", "Nm", None), ("Phinehas_1", "Nm", "Nm 25")],
    },
}

REF_RE = re.compile(r"^([1-3]?[A-Za-z]+) (\d+):(\d+)$")


def cargar_js(ruta):
    s = ruta.read_text(encoding="utf-8")
    return json.loads(s[s.index("{"):s.rindex("}") + 1])


# --------------------------------------------------------------------------- índice de versículos
class Texto:
    """Versículos de biblia.js en orden canónico, con índice global."""

    def __init__(self, biblia):
        self.libros = [l["id"] for l in biblia["libros"]]
        self.orden, self.idx, self.V = [], {}, {}
        self.rango_libro = {}
        caps = sorted(biblia["capitulos"], key=lambda c: (self.libros.index(c["libro"]), c["cap"]))
        for c in caps:
            for v in c["versiculos"]:
                ref = f'{c["libro"]} {c["cap"]}:{v["n"]}'
                self.idx[ref] = len(self.orden)
                self.orden.append((c["libro"], c["cap"], v["n"]))
                self.V[ref] = v["texto"]
                a, _ = self.rango_libro.get(c["libro"], (len(self.orden) - 1, 0))
                self.rango_libro[c["libro"]] = (a, len(self.orden) - 1)

    def ref(self, i):
        l, c, v = self.orden[i]
        return f"{l} {c}:{v}"

    def libro(self, i):
        return self.orden[i][0]

    def capitulo(self, i):
        l, c, _ = self.orden[i]
        return f"{l} {c}"


# --------------------------------------------------------------------------- construcción y verificación
def construir(fuentes, biblia, tab):
    """fuentes: {libro: dict}. Devuelve (doc | None, errores, avisos). errores: [(libro, seccion, id, campo, tipo, msg)]."""
    T = Texto(biblia)
    personas = {p["id"]: p for p in biblia["personas"]}
    lugares = {l["id"] for l in biblia["lugares"]}
    piezas = {p["id"] for p in tab["piezas"]}
    errores, avisos = [], []

    def err(libro, sec, id_, campo, tipo, msg):
        errores.append((libro, sec, id_, campo, tipo, msg))

    # ---- utilidades de verificación
    def ref_ok(ref, ruta, campo):
        if not isinstance(ref, str) or not REF_RE.match(ref):
            err(*ruta, campo, "ref", f"referencia mal formada {ref!r}")
            return None
        if ref not in T.idx:
            err(*ruta, campo, "ref", f"no existe {ref}")
            return None
        return T.idx[ref]

    def rango_ok(r, ruta, campo, libro=None):
        """Valida {inicio, fin}; devuelve (i, j) o None."""
        if not isinstance(r, dict):
            err(*ruta, campo, "rango", f"rango no es objeto: {r!r}")
            return None
        i = ref_ok(r.get("inicio"), ruta, campo + ".inicio")
        j = ref_ok(r.get("fin"), ruta, campo + ".fin")
        if i is None or j is None:
            return None
        if T.libro(i) != T.libro(j):
            err(*ruta, campo, "rango", f"cruza libros: {r['inicio']} – {r['fin']} (partirlo en dos)")
            return None
        if i > j:
            err(*ruta, campo, "rango", f"inicio > fin: {r['inicio']} – {r['fin']}")
            return None
        if libro and T.libro(i) != libro:
            err(*ruta, campo, "rango", f"{r['inicio']} – {r['fin']} no es del libro {libro}")
            return None
        return i, j

    def cita_ok(ref, cita, ruta, campo, obligatoria=True):
        if cita is None or cita == "":
            if obligatoria:
                err(*ruta, campo, "cita", "falta la cita")
            return
        if ref in T.V and cita not in T.V[ref]:
            err(*ruta, campo, "cita", f"la cita {cita!r} no es literal de {ref}")

    def datos_ok(lista, ruta):
        if not isinstance(lista, list):
            err(*ruta, "datos", "estructura", "datos no es lista")
            return []
        for k, d in enumerate(lista):
            c = f"datos[{k}]"
            if not isinstance(d, dict) or not d.get("texto"):
                err(*ruta, c, "estructura", "dato sin texto")
                continue
            if d.get("certeza") not in CERTEZAS:
                err(*ruta, c + ".certeza", "certeza", f"certeza {d.get('certeza')!r} (válidas: texto, inferido)")
            if ref_ok(d.get("ref"), ruta, c + ".ref") is not None:
                cita_ok(d["ref"], d.get("cita"), ruta, c + ".cita", obligatoria=d.get("certeza") == "texto")
        return lista

    def externo_ok(lista, ruta):
        if not isinstance(lista, list):
            err(*ruta, "externo", "estructura", "externo no es lista")
            return []
        for k, e in enumerate(lista):
            c = f"externo[{k}]"
            if not isinstance(e, dict) or not e.get("texto"):
                err(*ruta, c, "estructura", "externo sin texto")
                continue
            if not e.get("fuente"):
                err(*ruta, c + ".fuente", "externo", "externo sin fuente")
            if not str(e.get("url") or "").startswith("https://"):
                err(*ruta, c + ".url", "externo", f"url no https: {e.get('url')!r}")
        return lista

    def persona_ok(pid, ruta, campo):
        if pid not in personas:
            err(*ruta, campo, "id", f"persona inexistente en biblia.js: {pid!r}")
            return False
        return True

    def apariciones(lista, ruta, libro):
        res = []
        if not isinstance(lista, list):
            err(*ruta, "apariciones", "estructura", "apariciones no es lista")
            return res
        for k, r in enumerate(lista):
            ij = rango_ok(r, ruta, f"apariciones[{k}]", libro)
            if ij:
                res.append(ij)
        return res

    libros = [l for l in T.libros if l in fuentes]
    for l in fuentes:
        if l not in T.libros:
            err(l, "archivo", "-", "libro", "libro", f"libro {l!r} no está en biblia.js")

    # ---- genealogías e historias por libro
    genealogias, historias, gen_idx = [], [], set()
    vistos_g, vistos_h = set(), set()
    for libro in libros:
        F = fuentes[libro]
        if F.get("libro") != libro:
            err(libro, "archivo", "-", "libro", "libro", f"el campo libro es {F.get('libro')!r}, no {libro!r}")
        for g in F.get("genealogias", []):
            ruta = (libro, "genealogias", g.get("id", "?"))
            if g.get("id") in vistos_g:
                err(*ruta, "id", "id", "id de genealogía repetido")
            vistos_g.add(g.get("id"))
            if not g.get("titulo"):
                err(*ruta, "titulo", "estructura", "sin título")
            ij = rango_ok(g, ruta, "rango", libro)
            if ij:
                cita_ok(g["inicio"], g.get("cita"), ruta, "cita")
                gen_idx.update(range(ij[0], ij[1] + 1))
                genealogias.append(dict(g, _i=ij))
        hs = []
        for h in F.get("historias", []):
            ruta = (libro, "historias", h.get("id", "?"))
            if h.get("id") in vistos_h:
                err(*ruta, "id", "id", "id de historia repetido")
            vistos_h.add(h.get("id"))
            if not h.get("titulo"):
                err(*ruta, "titulo", "estructura", "sin título")
            for k, pid in enumerate(h.get("principales", [])):
                persona_ok(pid, ruta, f"principales[{k}]")
            ij = rango_ok(h, ruta, "rango", libro)
            if ij:
                hs.append(dict(h, _i=ij))
        hs.sort(key=lambda h: h["_i"])
        a, b = T.rango_libro[libro]
        esperado = a
        for h in hs:
            i, j = h["_i"]
            if i > esperado:
                err(libro, "historias", h["id"], "inicio", "cobertura",
                    f"hueco antes de {h['inicio']}: {T.ref(esperado)} – {T.ref(i - 1)} sin historia")
            elif i < esperado:
                err(libro, "historias", h["id"], "inicio", "cobertura",
                    f"se solapa con la historia anterior ({h['inicio']} ≤ {T.ref(esperado - 1)})")
            esperado = max(esperado, j + 1)
        if not hs:
            err(libro, "historias", "-", "-", "cobertura", "el libro no tiene historias")
        elif esperado <= b:
            err(libro, "historias", hs[-1]["id"], "fin", "cobertura", f"hueco al final: {T.ref(esperado)} – {T.ref(b)}")
        historias.extend(hs)
    historias.sort(key=lambda h: h["_i"])

    # ---- fusión de personajes, objetos y escenarios
    pj, obj, esc = {}, {}, {}
    for libro in libros:
        F = fuentes[libro]
        for pid, e in (F.get("personajes") or {}).items():
            ruta = (libro, "personajes", pid)
            if not persona_ok(pid, ruta, "id"):
                continue
            ap = apariciones(e.get("apariciones", []), ruta, libro)
            for k, (i, j) in enumerate(ap):
                sol = [x for x in range(i, j + 1) if x in gen_idx]
                if sol:
                    err(*ruta, f"apariciones[{k}]", "genealogia",
                        f"se solapa con una genealogía en {T.ref(sol[0])}" + (f" (y {len(sol) - 1} más)" if len(sol) > 1 else ""))
            mp = []
            for k, m in enumerate(e.get("menciones_posteriores", [])):
                r = m.get("ref") if isinstance(m, dict) else m
                if ref_ok(r, ruta, f"menciones_posteriores[{k}]") is not None:
                    mp.append(r)
            d = pj.setdefault(pid, {"_ap": [], "menciones_posteriores": [], "resumen": "", "datos": [], "externo": []})
            d["_ap"] += ap
            d["menciones_posteriores"] += mp
            if not d["resumen"] and e.get("resumen"):
                d["resumen"] = e["resumen"]
            d["datos"] += datos_ok(e.get("datos", []), ruta)
            d["externo"] += externo_ok(e.get("externo", []), ruta)

        for sec, dest in (("objetos", obj), ("escenarios", esc)):
            for oid, e in (F.get(sec) or {}).items():
                ruta = (libro, sec, oid)
                if not e.get("nombre"):
                    err(*ruta, "nombre", "estructura", "sin nombre")
                ap = apariciones(e.get("apariciones", []), ruta, libro)
                if not e.get("apariciones"):
                    err(*ruta, "apariciones", "estructura", "sin apariciones")
                for k, pid in enumerate(e.get("personas", [])):
                    persona_ok(pid, ruta, f"personas[{k}]")
                d = dest.get(oid)
                if d is None:
                    d = dest[oid] = {"nombre": e.get("nombre", ""), "_ap": [], "personas": [], "resumen": "",
                                     "datos": [], "externo": []}
                    if sec == "objetos":
                        d.update(tipo=e.get("tipo", ""), lugares=[], tabernaculo=None)
                    else:
                        d.update(lugar=None, objetos=[])
                elif e.get("nombre") and e["nombre"] != d["nombre"]:
                    avisos.append(f"{libro} · {sec} · {oid}: nombre distinto entre libros ({d['nombre']!r} / {e['nombre']!r}); se usa el primero")
                d["_ap"] += ap
                d["personas"] += [p for p in e.get("personas", []) if p not in d["personas"]]
                if not d["resumen"] and e.get("resumen"):
                    d["resumen"] = e["resumen"]
                d["datos"] += datos_ok(e.get("datos", []), ruta)
                d["externo"] += externo_ok(e.get("externo", []), ruta)
                if sec == "objetos":
                    if not d["tipo"] and e.get("tipo"):
                        d["tipo"] = e["tipo"]
                    for k, lid in enumerate(e.get("lugares", [])):
                        if lid not in lugares:
                            err(*ruta, f"lugares[{k}]", "id", f"lugar inexistente en biblia.js: {lid!r}")
                        elif lid not in d["lugares"]:
                            d["lugares"].append(lid)
                    tb = e.get("tabernaculo")
                    if tb is not None:
                        if tb not in piezas:
                            err(*ruta, "tabernaculo", "id", f"pieza inexistente en tabernaculo.js: {tb!r}")
                        elif d["tabernaculo"] is None:
                            d["tabernaculo"] = tb
                else:
                    lid = e.get("lugar")
                    if lid is not None:
                        if lid not in lugares:
                            err(*ruta, "lugar", "id", f"lugar inexistente en biblia.js: {lid!r}")
                        elif d["lugar"] is None:
                            d["lugar"] = lid
                    d["objetos"] += [o for o in e.get("objetos", []) if o not in d["objetos"]]
                    d.setdefault("_obj_ruta", []).append((ruta, e.get("objetos", [])))

    for oid, d in esc.items():
        for ruta, lista in d.pop("_obj_ruta", []):
            for k, o in enumerate(lista):
                if o not in obj:
                    err(*ruta, f"objetos[{k}]", "id", f"objeto inexistente en el catálogo: {o!r}")

    # ---- derivación de personas sin entrada (menciones de biblia.js fuera de genealogías)
    cargados = set(libros)
    por_persona = {}
    for m in biblia["menciones"]:
        i = T.idx.get(m["ref"])
        if i is not None and T.libro(i) in cargados and i not in gen_idx:
            por_persona.setdefault(m["persona"], set()).add(i)
    derivados = 0
    for p in biblia["personas"]:
        if p["id"] in pj:
            continue
        derivados += 1
        ap = []
        for i in sorted(por_persona.get(p["id"], ())):
            if ap and ap[-1][1] == i - 1 and T.libro(i) == T.libro(ap[-1][0]):
                ap[-1] = (ap[-1][0], i)
            else:
                ap.append((i, i))
        pj[p["id"]] = {"_ap": ap, "menciones_posteriores": [], "resumen": "", "datos": [], "externo": [],
                       "derivado": True}
    if derivados:
        avisos.append(f"{derivados} persona(s) de biblia.js sin entrada en las fuentes: apariciones derivadas de "
                      f"`menciones` fuera de genealogías")

    # ---- cálculos
    def unir(rangos):
        res = []
        for i, j in sorted(rangos):
            if res and i <= res[-1][1] + 1 and T.libro(i) == T.libro(res[-1][1]):
                res[-1] = (res[-1][0], max(res[-1][1], j))
            else:
                res.append((i, j))
        return res

    def a_refs(rangos):
        return [{"inicio": T.ref(i), "fin": T.ref(j)} for i, j in rangos]

    principal_en = {}
    for h in historias:
        for pid in h.get("principales", []):
            principal_en.setdefault(pid, []).append(h)

    def historia_de(i):
        return next((h["id"] for h in historias if h["_i"][0] <= i <= h["_i"][1]), None)

    personajes, npc_nombrados = {}, []
    orden_ids = [p["id"] for p in biblia["personas"]]
    for pid in orden_ids:
        d = pj[pid]
        rg = unir(d.pop("_ap"))
        versiculos = sum(j - i + 1 for i, j in rg)
        mp_idx = {T.idx[r] for r in d["menciones_posteriores"]}
        versiculos_nivel = versiculos + sum(1 for x in mp_idx if not any(i <= x <= j for i, j in rg))
        npc = versiculos == 0
        nivel = 0 if npc else min(NIVEL_TOPE, 1 + int(math.floor(math.log2(versiculos_nivel))))
        if npc:
            fuera = sorted(x for x in por_persona.get(pid, ()) if x not in mp_idx)
            if fuera:
                npc_nombrados.append(f"{pid} ({', '.join(T.ref(x) for x in fuera[:4])}"
                                     + (f" y {len(fuera) - 4} más" if len(fuera) > 4 else "") + ")")
        listo = None
        if not npc:
            hs = principal_en.get(pid)
            if hs:
                h = hs[0]
                dentro = [min(j, h["_i"][1]) for i, j in rg if i <= h["_i"][1] and j >= h["_i"][0]]
                if dentro:
                    ult = max(dentro)
                    listo = {"historia": h["id"], "ref": T.ref(ult), "capitulo": T.capitulo(ult)}
                else:
                    err(T.libro(h["_i"][0]), "historias", h["id"], "principales", "principal",
                        f"{pid} es principal pero no tiene apariciones dentro de la historia")
            else:
                ult = rg[-1][1]
                listo = {"historia": historia_de(ult), "ref": T.ref(ult), "capitulo": T.capitulo(ult)}
        e = {"apariciones": a_refs(rg), "menciones_posteriores": [{"ref": r} for r in d["menciones_posteriores"]],
             "versiculos": versiculos, "versiculos_nivel": versiculos_nivel, "nivel": nivel, "npc": npc, "listo": listo,
             "resumen": d["resumen"], "datos": d["datos"], "externo": d["externo"]}
        if d.get("derivado"):
            e["derivado"] = True
        personajes[pid] = e
    if npc_nombrados:
        avisos.append(f"{len(npc_nombrados)} NPC con su nombre en versículos fuera de genealogías que no están en "
                      f"sus menciones_posteriores (revisar si aparecen o son menciones): " + "; ".join(npc_nombrados))

    def cerrar(dic, campos):
        out = {}
        for oid, d in dic.items():
            rg = unir(d.pop("_ap"))
            o = {"nombre": d["nombre"]}
            for c in campos:
                if c == "apariciones":
                    o[c] = a_refs(rg)
                elif c == "tabernaculo":
                    if d.get("tabernaculo"):
                        o[c] = d["tabernaculo"]
                elif c == "lugar":
                    if d.get("lugar"):
                        o[c] = d["lugar"]
                else:
                    o[c] = d[c]
            out[oid] = (o, rg)
        return out

    objetos = cerrar(obj, ["tipo", "apariciones", "personas", "lugares", "tabernaculo", "resumen", "datos", "externo"])
    escenarios = cerrar(esc, ["lugar", "apariciones", "personas", "objetos", "resumen", "datos", "externo"])

    # ---- hechos obligatorios
    for libro in libros:
        H = HECHOS.get(libro, {})
        for a, b in H.get("genealogia", []):
            for x in range(T.idx[a], T.idx[b] + 1):
                if x not in gen_idx:
                    err(libro, "hechos", "genealogia", f"{a}–{b}", "hecho", f"{T.ref(x)} debe estar dentro de una genealogía")
                    break
        for pid, ref in H.get("aparece", []):
            x = T.idx[ref]
            ap = personajes.get(pid, {}).get("apariciones", [])
            if not any(T.idx[r["inicio"]] <= x <= T.idx[r["fin"]] for r in ap):
                err(libro, "hechos", pid, "apariciones", "hecho", f"{pid} debe aparecer en {ref}")
        for ref, que in H.get("objeto_en", []):
            x = T.idx[ref]
            if not any(i <= x <= j for _, rg in objetos.values() for i, j in rg):
                err(libro, "hechos", "objetos", ref, "hecho", f"falta un objeto que aparezca en {ref} ({que})")
        for lid in H.get("escenario_lugar", []):
            if not any(o.get("lugar") == lid for o, _ in escenarios.values()):
                err(libro, "hechos", "escenarios", lid, "hecho", f"falta un escenario con lugar {lid!r}")
        for pid, lib, cap in H.get("principal", []):
            hs = [h for h in principal_en.get(pid, []) if T.libro(h["_i"][0]) == lib]
            if not hs:
                err(libro, "hechos", pid, "principales", "hecho", f"{pid} debe ser principal en alguna historia de {lib}")
            elif cap:
                got = (personajes[pid]["listo"] or {}).get("capitulo")
                if got != cap:
                    err(libro, "hechos", pid, "listo.capitulo", "hecho", f"listo.capitulo de {pid} es {got!r}, debe ser {cap!r}")

    if errores:
        return None, errores, avisos

    def limpiar(x):
        return {k: v for k, v in x.items() if k != "_i"}

    doc = {"generado": datetime.date.today().isoformat(), "libros": libros,
           "genealogias": [limpiar(g) for g in sorted(genealogias, key=lambda g: g["_i"])],
           "historias": [limpiar(h) for h in historias],
           "personajes": personajes,
           "objetos": {k: o for k, (o, _) in objetos.items()},
           "escenarios": {k: o for k, (o, _) in escenarios.items()}}
    return doc, errores, avisos


# --------------------------------------------------------------------------- E/S
def leer_fuentes(dirr, libros):
    fuentes, errores = {}, []
    for ruta in sorted(Path(dirr).glob("*.json")):
        try:
            fuentes[ruta.stem] = json.loads(ruta.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            errores.append((ruta.stem, "archivo", ruta.name, "-", "json", f"JSON inválido: {e}"))
    return fuentes, errores


def informar(errores, avisos, salida=sys.stderr):
    for a in avisos:
        print("aviso: " + a)
    if not errores:
        return
    print(f"{len(errores)} error(es):", file=salida)
    for e in sorted(errores, key=lambda e: (e[0], e[4], e[1], str(e[2]))):
        libro, sec, id_, campo, tipo, msg = e
        print(f"  [{tipo}] {libro} · {sec} · {id_} · {campo}: {msg}", file=salida)
    print("Resumen por libro y tipo:", file=salida)
    for (libro, tipo), n in sorted(Counter((e[0], e[4]) for e in errores).items()):
        print(f"  {libro} · {tipo}: {n}", file=salida)


def resumen(doc):
    pj = doc["personajes"].values()
    npc = sum(1 for p in pj if p["npc"])
    der = sum(1 for p in pj if p.get("derivado"))
    niveles = Counter(p["nivel"] for p in pj)
    return (f"{len(doc['libros'])} libro(s) {doc['libros']}, {len(doc['genealogias'])} genealogías, "
            f"{len(doc['historias'])} historias, {len(doc['personajes'])} personajes ({npc} NPC, {der} derivados), "
            f"{len(doc['objetos'])} objetos, {len(doc['escenarios'])} escenarios. Niveles: "
            + ", ".join(f"{k}:{v}" for k, v in sorted(niveles.items())))


def autoprueba(biblia, tab):
    fuentes, errs = leer_fuentes(PRUEBA, None)
    ok = True
    doc, errores, avisos = construir(fuentes, biblia, tab)
    errores = errs + errores
    if errores or doc is None:
        print("FALLA: el fixture válido no pasa:")
        informar(errores, avisos, sys.stdout)
        return 1
    a = doc["personajes"][ABRAHAM]
    print(f"OK fixture válido: {resumen(doc)}")
    print(f"   Abraham: versiculos={a['versiculos']} nivel={a['nivel']} listo={a['listo']}")
    # Adán en el fixture: Gn 2:7-25 (19) + Gn 3:1-24 (24) + Gn 4:1 + Gn 4:25 = 45 versículos → 1 + floor(log2 45) = 6
    v = doc["personajes"][ADAN]
    if (v["versiculos"], v["nivel"]) != (45, 6):
        print(f"FALLA: Adán debería tener 45 versículos y nivel 6, tiene {v['versiculos']} / {v['nivel']}")
        ok = False
    if a["listo"] != {"historia": "abraham", "ref": "Gn 25:10", "capitulo": "Gn 25"}:
        print(f"FALLA: listo de Abraham inesperado: {a['listo']}")
        ok = False
    if a["menciones_posteriores"] != [{"ref": "Ex 3:6"}]:
        print(f"FALLA: la fusión entre libros no unió las menciones de Abraham: {a['menciones_posteriores']}")
        ok = False

    casos = []
    f1 = copy.deepcopy(fuentes)
    f1["Gn"]["personajes"][ADAN]["datos"][0]["cita"] = "novecientos treinta años"
    casos.append(("cita no literal", f1, "cita"))
    f2 = copy.deepcopy(fuentes)
    f2["Gn"]["personajes"][ADAN]["apariciones"].append({"inicio": "Gn 5:3", "fin": "Gn 5:5"})
    casos.append(("aparición dentro de una genealogía", f2, "genealogia"))
    f3 = copy.deepcopy(fuentes)
    f3["Ex"]["historias"][1]["inicio"] = "Ex 15:23"
    casos.append(("hueco entre historias", f3, "cobertura"))
    f4 = copy.deepcopy(fuentes)
    f4["Gn"]["genealogias"] = [g for g in f4["Gn"]["genealogias"] if g["inicio"] != "Gn 46:8"]
    casos.append(("falta la genealogía de Gn 46", f4, "hecho"))
    for nombre, f, tipo in casos:
        doc, errores, _ = construir(f, biblia, tab)
        tipos = {e[4] for e in errores}
        if doc is None and tipo in tipos:
            print(f"OK falla como se espera ({nombre}):")
            for e in errores:
                print(f"   [{e[4]}] {e[0]} · {e[1]} · {e[2]} · {e[3]}: {e[5]}")
        else:
            print(f"FALLA: el caso «{nombre}» debía dar error de tipo {tipo!r}; errores: {errores}")
            ok = False
    return 0 if ok else 1


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    biblia = cargar_js(DATOS / "biblia.js")
    tab = cargar_js(DATOS / "tabernaculo.js")
    if "--autoprueba" in argv:
        return autoprueba(biblia, tab)
    dirr = Path(argv[argv.index("--fuentes") + 1]) if "--fuentes" in argv else FUENTES
    salida = Path(argv[argv.index("--salida") + 1]) if "--salida" in argv else SALIDA
    fuentes, errs = leer_fuentes(dirr, None)
    if not fuentes and not errs:
        print(f"No hay fuentes *.json en {dirr}", file=sys.stderr)
        return 2
    doc, errores, avisos = construir(fuentes, biblia, tab)
    errores = errs + errores
    informar(errores, avisos)
    if errores or doc is None:
        print("No se escribe la salida.", file=sys.stderr)
        return 1
    print("OK: " + resumen(doc))
    if "--sin-salida" in argv:
        return 0
    salida.write_text("window.BIBLIA_JUEGO = " + json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + ";\n",
                      encoding="utf-8")
    try:
        nombre = salida.resolve().relative_to(RAIZ)
    except ValueError:
        nombre = salida
    print(f"Escrito {nombre} ({salida.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
