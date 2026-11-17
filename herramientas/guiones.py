"""Valida los guiones de video de cada pasaje (Higgsfield) y genera las hojas de rodaje legibles.

Sin red ni dependencias. Ejecutar: python -I herramientas/guiones.py
Opciones:
  --fuentes DIR   lee las fuentes de DIR (por defecto guiones/fuentes)
  --salida DIR    escribe los .md/.txt en DIR (por defecto guiones)
  --sin-salida    solo valida, no escribe nada
  --autoprueba    corre un fixture interno: el válido debe pasar y cada copia alterada debe fallar. No escribe nada.

Fuentes (en DIR):
  estilo.json                 base de prompt, negativos, rótulos, palabras por minuto, términos prohibidos
  referencias.json            {id: referencia de época}; solo las de «comprobado: true» pueden usarse
  personajes/<id>.json        ficha de personaje (Element de Cinema Studio); id = nombre del archivo
  escenarios/<id>.json        ficha de escenario (Element); id = nombre del archivo
  <Libro>/<pasaje>.json       guion = un video completo del pasaje (<pasaje>.mp4); id = id del pasaje en biblia.js

Un guion cubre su pasaje entero: inicio y fin iguales a los de `pasajes` en datos/biblia.js; cada versículo se
cubre una vez, en orden, por las `partes` de las tomas, y la unión de las partes de un versículo (normalizando
espacios) es idéntica al texto RV1909 con sus corchetes. Una parte con voz de persona debe estar dentro de un
`discurso` declarado: introducción literal del versículo que termina en «:» y lleva verbo de habla, persona
nombrada en ese versículo o en el pasaje, y fin literal del discurso. Toda `cita` (con su `ref`) es subcadena
exacta del versículo. Toda `certeza` es una de CERTEZAS, con sus campos obligatorios.

Salidas (en DIR de salida): <Libro>/<pasaje>.md (hoja de rodaje y montaje), <Libro>/<pasaje>.narracion.txt,
personajes/<id>.md, escenarios/<id>.md. Si hay errores los imprime (archivo · id · campo) y sale con código 1
sin escribir nada.
"""
import copy
import json
import math
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FUENTES = RAIZ / "guiones" / "fuentes"
SALIDA = RAIZ / "guiones"
BIBLIA = RAIZ / "datos" / "biblia.js"
ESTILO_MD = "estilo.md"
IMAGENES = "guiones/imagenes"  # donde se devuelven las imágenes generadas (hojas e imágenes iniciales)  # en la carpeta de salida; debe repetir literalmente la base y los negativos

CERTEZAS = {"texto", "inferido", "calculo", "interpretacion", "supuesto", "externa"}
NOMBRE_CERTEZA = {"texto": "Texto", "inferido": "Inferido", "calculo": "Cálculo",
                  "interpretacion": "Interpretación del ilustrador", "supuesto": "Supuesto",
                  "externa": "Fuente externa"}
NIVELES = {"A": "clip de video", "B": "imagen con movimiento leve", "C": "narración sobre imagen fija"}
PERFILES = {"todos", "nino", "adulto"}
TRANSICIONES = {"corte", "fundido", "fundido a negro", "encadenado"}
VERBOS_HABLA = re.compile(r"\b(dijo|dijeron|clamó|clamaron|respondió|respondieron|habló|hablaron|diciendo|dice|"
                          r"decía|decían|llamó|gritó|preguntó|mandó|exclamó|contestó|dijéronle|díjole|díjoles)\b",
                          re.IGNORECASE)
REF_RE = re.compile(r"^([1-3]?[A-Za-z]+) (\d+):(\d+)(?:-(?:(\d+):)?(\d+))?$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
CAMPOS_ESTILO = {"base_imagen_en", "base_imagen_es", "negativo_en", "negativo_es", "base_movimiento_en",
                 "base_movimiento_es", "rotulo_ia", "rotulo_texto", "palabras_por_minuto", "segundos_clip",
                 "prohibidos_prompt", "nombre_estilo"}


def cargar_js(ruta):
    s = ruta.read_text(encoding="utf-8")
    return json.loads(s[s.index("{"):s.rindex("}") + 1])


def norm(s):
    return " ".join(str(s).split())


def palabras(s):
    """Palabras que se pronuncian: fragmentos con alguna letra o cifra (sin corchetes)."""
    return sum(1 for w in s.replace("[", "").replace("]", "").split() if re.search(r"\w", w))


class Texto:
    """Versículos de biblia.js en orden canónico, con índice global (patrón de explicaciones.py)."""

    def __init__(self, biblia):
        self.libros = [l["id"] for l in biblia["libros"]]
        self.nombre_libro = {l["id"]: l.get("nombre", l["id"]) for l in biblia["libros"]}
        self.orden, self.idx, self.V = [], {}, {}
        caps = sorted(biblia["capitulos"], key=lambda c: (self.libros.index(c["libro"]), c["cap"]))
        for c in caps:
            for v in c["versiculos"]:
                ref = f'{c["libro"]} {c["cap"]}:{v["n"]}'
                self.idx[ref] = len(self.orden)
                self.orden.append(ref)
                self.V[ref] = v.get("texto") or ""
        self.personas = {p["id"]: p for p in biblia.get("personas", [])}
        self.pasajes = {p["id"]: p for p in biblia.get("pasajes", [])}
        self.menciones = {(m["ref"], m["persona"]) for m in biblia.get("menciones", [])}

    def rango(self, s):
        """'Lib C:V', 'Lib C:V-V' o 'Lib C:V-C:V' → (i, j, None) o (None, None, motivo)."""
        m = REF_RE.match(s) if isinstance(s, str) else None
        if not m:
            return None, None, f"referencia mal formada {s!r}"
        lb, c, v, c2, v2 = m.groups()
        if lb not in self.libros:
            return None, None, f"libro no cargado: {lb}"
        a = f"{lb} {c}:{v}"
        b = f"{lb} {c2 or c}:{v2}" if v2 else a
        if a not in self.idx:
            return None, None, f"no existe {a}"
        if b not in self.idx:
            return None, None, f"no existe {b}"
        i, j = self.idx[a], self.idx[b]
        if i > j:
            return None, None, f"rango al revés {s}"
        return i, j, None


def ref_corta(T, i, j):
    a, b = T.orden[i], T.orden[j]
    if i == j:
        return a
    la, ca = a.rsplit(":", 1)
    lb, cb = b.rsplit(":", 1)
    return f"{a}-{cb}" if la == lb else f"{a}-{b.split(' ', 1)[1]}"


# --------------------------------------------------------------------------- validación
def validar(F, biblia, estilo_md=None):
    """F: {'estilo', 'referencias', 'personajes': {id: obj}, 'escenarios': {id: obj}, 'guiones': {id: obj},
    'archivos': {clave: nombre}}. Devuelve (errores, avisos, calc). errores: [(archivo, id, campo, msg)]."""
    T = Texto(biblia)
    errores, avisos = [], []
    calc = {}
    A = F.get("archivos", {})

    def err(arch, id_, campo, msg):
        errores.append((arch, id_, campo, msg))

    # ---- estilo
    E = F.get("estilo") or {}
    falta = CAMPOS_ESTILO - set(E)
    if falta:
        err("estilo.json", "-", "campos", f"faltan {sorted(falta)}")
        return errores, avisos, calc
    ppm, seg_clip = E["palabras_por_minuto"], E["segundos_clip"]
    prohibidos = [re.compile(r"\b" + re.escape(t) + r"\b", re.IGNORECASE) for t in E["prohibidos_prompt"]]
    if estilo_md is not None:
        for k in ("nombre_estilo", "base_imagen_en", "negativo_en", "base_movimiento_en", "rotulo_ia", "rotulo_texto"):
            if E[k] not in estilo_md:
                err(ESTILO_MD, "-", k, "estilo.md no repite literalmente este valor de estilo.json")

    # ---- referencias
    R = F.get("referencias") or {}
    for rid, r in R.items():
        if not isinstance(r.get("comprobado"), bool):
            err("referencias.json", rid, "comprobado", "debe ser true o false")
        for k in ("titulo", "institucion", "datacion", "url_ficha"):
            if not r.get(k):
                err("referencias.json", rid, k, "falta")
        if r.get("comprobado"):
            for k in ("url_imagen", "licencia", "inventario"):
                if not r.get(k):
                    err("referencias.json", rid, k, "falta (obligatorio si comprobado)")

    usadas = set()

    def refs_epoca(lista, arch, id_, campo):
        if not isinstance(lista, list):
            err(arch, id_, campo, "debe ser una lista de ids de referencias.json")
            return
        for rid in lista:
            if rid not in R:
                err(arch, id_, campo, f"referencia inexistente {rid!r}")
            elif not R[rid].get("comprobado"):
                err(arch, id_, campo, f"referencia {rid!r} no comprobada: no se puede usar")
            else:
                usadas.add(rid)

    def cita_ok(ref, cita, arch, id_, campo):
        i, j, motivo = T.rango(ref)
        if motivo:
            err(arch, id_, campo + ".ref", motivo)
            return
        if not isinstance(cita, str) or not cita.strip():
            err(arch, id_, campo + ".cita", "cita vacía")
            return
        if not any(cita in T.V[T.orden[k]] for k in range(i, j + 1)):
            err(arch, id_, campo + ".cita", f"no es literal de {ref}: {cita!r}")

    def recorrer(x, arch, id_, campo):
        """Revisa citas, certezas y referencias de época en cualquier nivel del objeto."""
        if isinstance(x, dict):
            if "cita" in x:
                if "ref" not in x:
                    err(arch, id_, campo, "cita sin ref")
                else:
                    cita_ok(x["ref"], x["cita"], arch, id_, campo)
            if "certeza" in x:
                c = x["certeza"]
                if c not in CERTEZAS:
                    err(arch, id_, campo + ".certeza", f"certeza desconocida {c!r} (usar {sorted(CERTEZAS)})")
                elif c == "texto" and not ("ref" in x and "cita" in x):
                    err(arch, id_, campo, "certeza texto exige ref y cita literal")
                elif c == "calculo":
                    calculo_ok(x, arch, id_, campo)
                elif c in ("inferido", "supuesto", "interpretacion") and not (x.get("nota") or x.get("base")):
                    err(arch, id_, campo, f"certeza {c} exige «nota» (por qué) o «base» (citas)")
                elif c == "externa" and not (x.get("fuente") or x.get("referencias")):
                    err(arch, id_, campo, "certeza externa exige «fuente» o «referencias»")
            for k, v in x.items():
                if k == "referencias":
                    refs_epoca(v, arch, id_, f"{campo}.{k}")
                else:
                    recorrer(v, arch, id_, f"{campo}.{k}" if campo else k)
        elif isinstance(x, list):
            for n, v in enumerate(x):
                recorrer(v, arch, id_, f"{campo}[{n}]")

    def calculo_ok(x, arch, id_, campo):
        c = x.get("calculo")
        if not isinstance(c, dict) or not isinstance(c.get("pasos"), list) or not c["pasos"]:
            err(arch, id_, campo, "certeza calculo exige «calculo» con «pasos»")
            return
        op = c.get("operacion")
        if op not in ("suma", "resta"):
            err(arch, id_, campo + ".calculo.operacion", "se admite «suma» o «resta» (primer paso menos los demás)")
            return
        try:
            vals = [p["valor"] for p in c["pasos"]]
            total = sum(vals) if op == "suma" else vals[0] - sum(vals[1:])
        except (KeyError, TypeError):
            err(arch, id_, campo + ".calculo.pasos", "cada paso necesita «valor» numérico")
            return
        for n, p in enumerate(c["pasos"]):
            if not ("ref" in p and "cita" in p):
                err(arch, id_, f"{campo}.calculo.pasos[{n}]", "cada paso del cálculo necesita ref y cita")
        if total != c.get("resultado") or ("valor" in x and x["valor"] != total):
            err(arch, id_, campo + ".calculo", f"la {op} de los pasos da {total}, no {c.get('resultado')}"
                                               f"/{x.get('valor')}")
        if not c.get("supuestos"):
            err(arch, id_, campo + ".calculo.supuestos", "un cálculo declara sus supuestos")

    def hoja_ok(h, arch, id_):
        for k in ("prompt_en", "prompt_es", "negativo_en", "negativo_es"):
            if not isinstance((h or {}).get(k), str) or not h[k].strip():
                err(arch, id_, f"hoja_referencia.{k}", "falta")
        if h and isinstance(h.get("prompt_en"), str):
            prompt_ok(h["prompt_en"], arch, id_, "hoja_referencia.prompt_en")
            natural_ok(h["prompt_en"], arch, id_, "hoja_referencia.prompt_en")
            natural_ok(h.get("negativo_en"), arch, id_, "hoja_referencia.negativo_en")

    def natural_ok(p, arch, id_, campo):
        if not isinstance(p, str):
            return
        if "#" in p:
            err(arch, id_, campo, "las etiquetas # solo van en los prompts de video")
        if not p.rstrip().endswith((".", "!")):
            err(arch, id_, campo, "prompt de imagen en frases completas (termina en punto)")

    def prompt_ok(p, arch, id_, campo, extra=()):
        for rx in list(prohibidos) + list(extra):
            m = rx.search(p)
            if m:
                err(arch, id_, campo, f"término prohibido en prompt positivo: {m.group(0)!r}")

    # ---- personajes y escenarios
    elementos = {}
    voces = {}  # persona → personaje con voz
    P = F.get("personajes") or {}
    for pid, p in P.items():
        arch = A.get(("personaje", pid), f"personajes/{pid}.json")
        if p.get("id") != pid or not ID_RE.match(pid):
            err(arch, pid, "id", "debe coincidir con el nombre del archivo (minúsculas, cifras, guiones)")
        for k in ("nombre", "personas", "element", "hoja_referencia", "rasgos"):
            if not p.get(k):
                err(arch, pid, k, "falta")
        for per in p.get("personas") or []:
            if per not in T.personas:
                err(arch, pid, "personas", f"persona inexistente en biblia.js: {per!r}")
            elif p.get("voz"):
                if per in voces:
                    err(arch, pid, "personas", f"{per} ya tiene voz en {voces[per]}")
                voces[per] = pid
        hoja_ok(p.get("hoja_referencia"), arch, pid)
        el = (p.get("element") or {}).get("nombre")
        if el:
            if el in elementos:
                err(arch, pid, "element.nombre", f"repetido con {elementos[el]}")
            elementos[el] = pid
        recorrer({k: v for k, v in p.items() if k != "hoja_referencia"}, arch, pid, "")
    S = F.get("escenarios") or {}
    for sid, s in S.items():
        arch = A.get(("escenario", sid), f"escenarios/{sid}.json")
        if s.get("id") != sid or not ID_RE.match(sid):
            err(arch, sid, "id", "debe coincidir con el nombre del archivo")
        for k in ("nombre", "element", "hoja_referencia", "texto"):
            if not s.get(k):
                err(arch, sid, k, "falta")
        hoja_ok(s.get("hoja_referencia"), arch, sid)
        el = (s.get("element") or {}).get("nombre")
        if el:
            if el in elementos:
                err(arch, sid, "element.nombre", f"repetido con {elementos[el]}")
            elementos[el] = sid
        recorrer({k: v for k, v in s.items() if k != "hoja_referencia"}, arch, sid, "")

    # ---- guiones
    for gid, g in (F.get("guiones") or {}).items():
        arch = A.get(("guion", gid), f"{gid}.json")
        n_err = len(errores)
        pas = T.pasajes.get(gid)
        if g.get("id") != gid:
            err(arch, gid, "id", "debe coincidir con el nombre del archivo")
        if not pas:
            err(arch, gid, "id", "no hay pasaje con este id en biblia.js")
            continue
        if g.get("inicio") != pas["inicio"] or g.get("fin") != pas["fin"]:
            err(arch, gid, "inicio/fin", f"el guion debe cubrir el pasaje entero: {pas['inicio']} – {pas['fin']}")
            continue
        gi, gj, motivo = T.rango(f'{pas["inicio"]}-{pas["fin"].split(" ", 1)[1]}')
        if motivo:
            err(arch, gid, "inicio/fin", motivo)
            continue
        mont = g.get("montaje") or {}
        if mont.get("archivo") != f"{gid}.mp4":
            err(arch, gid, "montaje.archivo", f"debe ser {gid}.mp4")
        if mont.get("titulo") != pas["titulo"]:
            err(arch, gid, "montaje.titulo", f"debe ser el título del pasaje: {pas['titulo']!r}")
        if not isinstance(mont.get("musica"), dict):
            err(arch, gid, "montaje.musica", "falta (usar: false si no lleva)")
        prohib_g = []
        for n, ph in enumerate(g.get("prohibido_hasta") or []):
            i, j, motivo = T.rango(ph.get("hasta", ""))
            if motivo:
                err(arch, gid, f"prohibido_hasta[{n}]", motivo)
                continue
            prohib_g.append((j, [re.compile(r"\b" + re.escape(t) + r"\b", re.IGNORECASE) for t in ph["terminos"]],
                             ph["hasta"]))
        # discursos
        D = {}
        for n, d in enumerate(g.get("discursos") or []):
            campo = f"discursos[{n}]"
            did = d.get("id")
            if not did or did in D:
                err(arch, gid, campo + ".id", "falta o repetido")
                continue
            per = d.get("persona")
            if per not in T.personas:
                err(arch, gid, campo + ".persona", f"persona inexistente {per!r}")
                continue
            i1, _, m1 = T.rango(d.get("ref", ""))
            i2, _, m2 = T.rango(d.get("fin_ref", ""))
            if m1 or m2:
                err(arch, gid, campo, m1 or m2)
                continue
            if not (gi <= i1 <= i2 <= gj):
                err(arch, gid, campo, "el discurso debe estar dentro del pasaje")
                continue
            v1, v2 = norm(T.V[T.orden[i1]]), norm(T.V[T.orden[i2]])
            intro, fin = norm(d.get("introduccion", "")), norm(d.get("fin_cita", ""))
            if not intro or v1.count(intro) != 1:
                err(arch, gid, campo + ".introduccion", "debe ser literal y aparecer una sola vez en el versículo")
                continue
            if not intro.endswith(":"):
                err(arch, gid, campo + ".introduccion", "el texto no introduce un discurso directo (falta «:»)")
                continue
            if not VERBOS_HABLA.search(intro):
                err(arch, gid, campo + ".introduccion", "sin verbo de habla")
                continue
            if not fin or v2.count(fin) != 1:
                err(arch, gid, campo + ".fin_cita", "debe ser literal y aparecer una sola vez en el versículo")
                continue
            ini = (i1, v1.index(intro) + len(intro))
            fn = (i2, v2.index(fin) + len(fin))
            if not ini < fn:
                err(arch, gid, campo, "el fin está antes de la introducción")
                continue
            if (T.orden[i1], per) not in T.menciones:
                if any((T.orden[k], per) in T.menciones for k in range(gi, gj + 1)):
                    avisos.append(f"{arch} · {gid} · {campo}: {per} no se nombra en {T.orden[i1]} (sí en el pasaje);"
                                  " confirmar que es el sujeto")
                else:
                    err(arch, gid, campo + ".persona", f"{per} no se nombra en {T.orden[i1]} ni en el pasaje")
                    continue
            if per not in voces:
                err(arch, gid, campo + ".persona", f"{per} no tiene ficha de personaje con «voz»")
            D[did] = {"persona": per, "ini": ini, "fin": fn, "usado": False}
        cont = g.get("continuidad") or {}
        for k in ("empieza_con", "termina_con"):
            if not cont.get(k):
                err(arch, gid, f"continuidad.{k}", "falta: con qué imagen empieza / termina el video")
        # escenas: cubren el pasaje en orden, sin huecos ni solapes
        escenas = g.get("escenas") or []
        if not escenas:
            err(arch, gid, "escenas", "sin escenas")
            continue
        tomas, rangos_esc, sig = [], [], gi
        for en, es in enumerate(escenas):
            campo = f"escenas[{en}]"
            for k in ("id", "titulo", "proposito", "progresion_visual"):
                if not es.get(k):
                    err(arch, gid, f"{campo}.{k}", "falta")
            ei, ej, motivo = T.rango(es.get("versiculos", ""))
            if motivo:
                err(arch, gid, campo + ".versiculos", motivo)
                ei = ej = None
            elif ei != sig:
                err(arch, gid, campo + ".versiculos",
                    f"debe empezar en {T.orden[sig] if sig < len(T.orden) else '¿?'} (escenas en orden, sin huecos "
                    "ni solapes)")
            if ej is not None:
                sig = ej + 1
            rangos_esc.append((ei, ej))
            if not es.get("tomas"):
                err(arch, gid, campo + ".tomas", "escena sin tomas")
            for t in es.get("tomas") or []:
                tomas.append(t)
                t["_escena"] = en
        if sig != gj + 1:
            err(arch, gid, "escenas", f"las escenas no terminan en {pas['fin']}")
        for t in tomas:
            ti, tj, motivo = T.rango(t.get("versiculos", ""))
            ei, ej = rangos_esc[t["_escena"]]
            if not motivo and ei is not None and not (ei <= ti <= tj <= ej):
                err(arch, gid, f"toma {t.get('id')}", f"sus versículos {t.get('versiculos')} no pertenecen a su escena "
                                                     f"{escenas[t['_escena']].get('id')} "
                                                     f"({escenas[t['_escena']].get('versiculos')})")
        # tomas y partes
        partes = []  # (toma_n, parte_n, vi, texto, voz, discurso)
        ids_t = set()
        info_tomas = []
        for tn, t in enumerate(tomas):
            tid = t.get("id")
            campo = f"tomas[{tn}]"
            if not tid or tid in ids_t:
                err(arch, gid, campo + ".id", "falta o repetido")
            ids_t.add(tid)
            nivel = t.get("nivel")
            if nivel not in NIVELES:
                err(arch, gid, campo + ".nivel", "A, B o C")
            if t.get("perfil") not in PERFILES:
                err(arch, gid, campo + ".perfil", f"uno de {sorted(PERFILES)}")
            if t.get("transicion") not in TRANSICIONES:
                err(arch, gid, campo + ".transicion", f"una de {sorted(TRANSICIONES)}")
            for pj in t.get("personajes") or []:
                if pj not in P:
                    err(arch, gid, campo + ".personajes", f"personaje inexistente {pj!r}")
            if t.get("escenario") not in S:
                err(arch, gid, campo + ".escenario", f"escenario inexistente {t.get('escenario')!r}")
            im = t.get("imagen") or {}
            for k in ("prompt_en", "descripcion_es"):
                if not im.get(k):
                    err(arch, gid, campo + f".imagen.{k}", "falta")
            natural_ok(im.get("prompt_en"), arch, gid, campo + ".imagen.prompt_en")
            if im.get("negativo_en"):
                natural_ok(im["negativo_en"], arch, gid, campo + ".imagen.negativo_en")
            mv = t.get("movimiento")
            if nivel in ("A", "B") and not (isinstance(mv, dict) and mv.get("prompt_en") and mv.get("camara")):
                err(arch, gid, campo + ".movimiento", "A y B necesitan prompt_en y camara")
            clips = t.get("clips_8s")
            if not isinstance(clips, int) or clips < 0 or (nivel == "A" and clips < 1):
                err(arch, gid, campo + ".clips_8s", "entero ≥ 0 (≥ 1 en nivel A)")
                clips = 0
            if not t.get("fidelidad"):
                err(arch, gid, campo + ".fidelidad", "falta")
            positivos = [im.get("prompt_en", "")] + ([mv.get("prompt_en", "")] if isinstance(mv, dict) else [])
            ti, tj, motivo = T.rango(t.get("versiculos", ""))
            if motivo:
                err(arch, gid, campo + ".versiculos", motivo)
                ti = tj = None
            for p_ in positivos:
                extra = [rx for (hj, rxs, _) in prohib_g if tj is not None and tj <= hj for rx in rxs]
                prompt_ok(p_, arch, gid, f"{campo} ({tid}) prompt", extra)
            recorrer({k: v for k, v in t.items() if k not in ("partes", "_escena")}, arch, gid, f"{campo} ({tid})")
            refs_t = []
            for pn, pa in enumerate(t.get("partes") or []):
                c2 = f"{campo}.partes[{pn}]"
                if pa.get("ref") not in T.idx:
                    err(arch, gid, c2 + ".ref", f"versículo inexistente {pa.get('ref')!r}")
                    continue
                vi = T.idx[pa["ref"]]
                if ti is not None and not (ti <= vi <= tj):
                    err(arch, gid, c2 + ".ref", f"{pa['ref']} fuera de los versículos de la toma {t.get('versiculos')}")
                voz = pa.get("voz")
                if voz != "narrador" and voz not in T.personas:
                    err(arch, gid, c2 + ".voz", f"voz desconocida {voz!r} (narrador o id de persona)")
                if not isinstance(pa.get("texto"), str) or not pa["texto"].strip():
                    err(arch, gid, c2 + ".texto", "vacío")
                    continue
                partes.append((tn, pn, vi, pa["texto"], voz, pa.get("discurso")))
                refs_t.append(vi)
            if not refs_t:
                err(arch, gid, campo + ".partes", "sin partes")
            elif ti is not None and (refs_t[0] != ti or refs_t[-1] != tj):
                err(arch, gid, campo + ".versiculos", f"no coincide con las partes "
                                                      f"({T.orden[refs_t[0]]} – {T.orden[refs_t[-1]]})")
            info_tomas.append((t, clips))
        # cobertura: cada versículo una vez, en orden, con texto idéntico
        orden_vis, grupos = [], {}
        for (tn, pn, vi, tx, voz, dis) in partes:
            if orden_vis and orden_vis[-1] == vi:
                grupos[vi].append((tn, pn, tx, voz, dis))
            elif vi in grupos:
                err(arch, gid, f"tomas[{tn}].partes[{pn}]", f"{T.orden[vi]} vuelve a aparecer (no contiguo o repetido)")
            else:
                orden_vis.append(vi)
                grupos[vi] = [(tn, pn, tx, voz, dis)]
        esperado = list(range(gi, gj + 1))
        if orden_vis != esperado:
            faltan = [T.orden[k] for k in esperado if k not in grupos]
            sobran = [T.orden[k] for k in orden_vis if k not in esperado]
            if faltan:
                err(arch, gid, "tomas", f"versículos sin cubrir: {', '.join(faltan)}")
            if sobran:
                err(arch, gid, "tomas", f"versículos fuera del pasaje: {', '.join(sobran)}")
            if not faltan and not sobran:
                err(arch, gid, "tomas", "los versículos no van en orden")
        for vi, gs in grupos.items():
            v = norm(T.V[T.orden[vi]])
            junto = norm(" ".join(x[2] for x in gs))
            if junto != v:
                k = next((n for n, (a, b) in enumerate(zip(junto, v)) if a != b), min(len(junto), len(v)))
                err(arch, gid, T.orden[vi], f"las partes no reproducen el texto RV1909 (difiere en el carácter {k}: "
                                            f"…{junto[max(0, k - 20):k + 20]!r} ≠ …{v[max(0, k - 20):k + 20]!r})")
                continue
            off = 0
            for (tn, pn, tx, voz, dis) in gs:
                t_ = norm(tx)
                ps, pe = (vi, off), (vi, off + len(t_))
                off += len(t_) + 1
                for did, d in D.items():
                    dentro = ps >= d["ini"] and pe <= d["fin"]
                    toca = ps < d["fin"] and pe > d["ini"]
                    if toca and not dentro:
                        err(arch, gid, f"tomas[{tn}].partes[{pn}]", f"la parte cruza el límite del discurso {did}")
                    elif dentro and (voz != d["persona"] or dis != did):
                        err(arch, gid, f"tomas[{tn}].partes[{pn}]",
                            f"dentro del discurso {did} la voz es {d['persona']} con discurso «{did}»")
                    elif dentro:
                        d["usado"] = True
                if voz != "narrador":
                    d = D.get(dis)
                    if not d or d["persona"] != voz or not (ps >= d["ini"] and pe <= d["fin"]):
                        err(arch, gid, f"tomas[{tn}].partes[{pn}].voz",
                            f"{voz} no puede decir {tx[:40]!r}: no está dentro de un discurso suyo del texto")
        for did, d in D.items():
            if not d["usado"]:
                avisos.append(f"{arch} · {gid} · discurso {did} declarado y sin partes")
        if len(errores) > n_err:
            continue
        # duración (Cálculo) y clips
        filas = []
        for (t, clips), tn in zip(info_tomas, range(len(info_tomas))):
            por_voz = {}
            for (tn2, pn, vi, tx, voz, dis) in partes:
                if tn2 == tn:
                    por_voz[voz] = por_voz.get(voz, 0) + palabras(tx)
            pal = sum(por_voz.values())
            seg = pal * 60 / ppm
            nec = math.ceil(seg / seg_clip)
            if t["nivel"] == "A" and clips < nec:
                avisos.append(f"{arch} · {gid} · {t['id']}: nivel A con {pal} palabras ≈ {seg:.1f} s necesita "
                              f"{nec} clips de {seg_clip} s y declara {clips}")
            hablan = [v for v in por_voz if v != "narrador"]
            for v in hablan:
                if voces.get(v) not in (t.get("personajes") or []):
                    avisos.append(f"{arch} · {gid} · {t['id']}: habla {v} y su personaje no está en cuadro")
            filas.append({"toma": t["id"], "palabras": pal, "por_voz": por_voz, "segundos": seg,
                          "clips_necesarios": nec, "clips": clips})
        # apertura y cierre: solo datos existentes de biblia.js
        lista = list(T.pasajes.values())
        pos = [p["id"] for p in lista].index(gid)
        del_libro = [p for p in lista if p["libro"] == pas["libro"]]
        ant = lista[pos - 1] if pos > 0 else None
        sigp = lista[pos + 1] if pos + 1 < len(lista) else None
        calc[gid] = {"filas": filas, "total_palabras": sum(f["palabras"] for f in filas),
                     "total_segundos": sum(f["segundos"] for f in filas), "ppm": ppm, "seg_clip": seg_clip,
                     "rango": ref_corta(T, gi, gj), "partes": partes, "voces": voces, "tomas": tomas,
                     "n": [p["id"] for p in del_libro].index(gid) + 1, "m": len(del_libro),
                     "libro": T.nombre_libro.get(pas["libro"], pas["libro"]),
                     "antes": ant if ant and ant.get("seccion") and ant.get("seccion") == pas.get("seccion")
                     and ant.get("resumen") else None,
                     "sigue": sigp}
    calc["_usadas"] = usadas
    calc["_texto"] = T
    return errores, avisos, calc


# --------------------------------------------------------------------------- salida legible
def fmt_s(s):
    s = round(s)
    return f"{s // 60} min {s % 60:02d} s" if s >= 60 else f"{s} s"


def lista_certeza(items, indent=""):
    out = []
    for x in items or []:
        c = NOMBRE_CERTEZA.get(x.get("certeza"), x.get("certeza", ""))
        txt = x.get("rasgo") or x.get("dato") or x.get("texto") or ""
        extra = ""
        if x.get("cita"):
            extra += f" — {x['ref']}: «{x['cita']}»"
        if x.get("nota"):
            extra += f" — {x['nota']}"
        for b in x.get("base") or []:
            extra += f" — base: {b['ref']} «{b['cita']}»"
        if x.get("fuente"):
            extra += f" — fuente: {x['fuente']}"
        if x.get("referencias"):
            extra += f" — referencias: {', '.join(x['referencias'])}"
        out.append(f"{indent}- **{c}**: {txt}{extra}")
        if x.get("certeza") == "calculo":
            cc = x["calculo"]
            signo = "−" if cc.get("operacion") == "resta" else "+"
            for n, p in enumerate(cc["pasos"], 1):
                out.append(f"{indent}  {n}. {'' if n == 1 else signo + ' '}{p['texto']}: {p['valor']} "
                           f"({p['ref']}: «{p['cita']}»)")
            out.append(f"{indent}  = {cc['resultado']}. Supuestos: " + "; ".join(cc["supuestos"]))
    return out


def credito(rid, r):
    return (f"- {r['titulo']} — {r['institucion']}"
            + (f", inv. {r['inventario']}" if r.get("inventario") else "")
            + f" — {r['datacion']} — licencia: {r.get('licencia', '¿?')} — imagen: {r.get('url_imagen', '')} [{rid}]")


def rotulo_ref(k):
    """«Génesis 45:1–15» a partir de «Gn 45:1-15»."""
    return f"{k['libro']} {k['rango'].split(' ', 1)[1].replace('-', '–')}"


def creditos_guion(g, F):
    R, P, S = F["referencias"], F["personajes"], F["escenarios"]
    ts = [t for es in g["escenas"] for t in es["tomas"]]
    usadas = sorted({r for t in ts for r in (t.get("imagen") or {}).get("referencias", [])}
                    | {r for pj in {p for t in ts for p in t.get("personajes", [])} for r in P[pj].get("referencias", [])}
                    | {r for t in ts for r in S[t["escenario"]].get("referencias", [])})
    return [credito(rid, R[rid]) for rid in usadas]


def hoja_guion(g, c, F):
    E, R, P, S = F["estilo"], F["referencias"], F["personajes"], F["escenarios"]
    k = c[g["id"]]
    m = g["montaje"]
    filas = {f["toma"]: f for f in k["filas"]}
    ts = [t for es in g["escenas"] for t in es["tomas"]]
    L = [f"# {g['id']} · {m['titulo']} ({k['rango']})", "",
         "Hoja de rodaje generada por `python -I herramientas/guiones.py` desde "
         f"`guiones/fuentes/{g['libro']}/{g['id']}.json`. No editar a mano.", "",
         f"Un solo video para todo el pasaje: **`{m['archivo']}`**. Se mostrará en la app dentro de la pantalla de "
         f"su pasaje ({g['id']}); la app todavía no lo integra.", "", "## Montaje", "",
         f"- **Título del video**: {m['titulo']}",
         f"- **Archivo final**: `{m['archivo']}` (16:9)",
         f"- **Duración total (Cálculo)**: {k['total_palabras']} palabras ÷ {k['ppm']} palabras/min × 60 = "
         f"{k['total_segundos']:.1f} s ≈ {fmt_s(k['total_segundos'])} de voz (suma de las {len(ts)} tomas), más "
         "rótulos y transiciones. Supuesto: lectura pausada a 150 palabras por minuto; se corrige con la duración "
         "real del audio.",
         f"- **Pista de narración y diálogos**: `{g['id']}.narracion.txt` (narrador con la voz de `estilo.md`; las "
         "líneas de personaje se generan con su voz en Lipsync Studio y van sobre su toma).",
         f"- **Música**: {'sí' if m['musica'].get('usar') else 'no'} — {m['musica'].get('nota', '')}"]
    if m.get("notas"):
        L.append(f"- **Notas de montaje**: {m['notas']}")
    L += ["", "### Apertura (rótulos, en este orden)", "",
          f"1. «{m['titulo']}»", f"2. «{rotulo_ref(k)}»", f"3. «Pasaje {k['n']} de {k['m']}» ({k['libro']})",
          f"4. «{E['rotulo_ia']}»", f"5. «{E['rotulo_texto']}»"]
    if k["antes"]:
        L.append(f"6. Opcional: «Antes: {k['antes']['resumen']}» — resumen editorial de {k['antes']['id']} "
                 f"({k['antes']['titulo']}), rotulado «Resumen editorial».")
    else:
        L.append("- Sin rótulo «Antes:» (el pasaje no continúa una historia de la misma sección).")
    L += ["", "### Cierre", "", "1. Créditos «En qué se basa»:",
          f"   - Texto: Reina-Valera 1909 (dominio público), {k['rango']}."]
    L += ["   " + x for x in creditos_guion(g, F)]
    L += ["   - Rostros, colores, gestos y encuadres: interpretación del ilustrador.",
          f"   - «{E['rotulo_ia']}». Herramienta y modelo: ver registro de generación "
          f"(`guiones/registro/{g['id']}.jsonl`)."]
    if k["sigue"]:
        L.append(f"2. «Sigue: {k['sigue']['titulo']}» ({k['sigue']['id']})")
    cont = g["continuidad"]
    L += ["", "### Continuidad entre videos", "",
          f"- **Empieza con**: {cont['empieza_con']}", f"- **Termina con**: {cont['termina_con']}"]
    if cont.get("enlace_anterior"):
        L.append(f"- **Enlace con el anterior**: {cont['enlace_anterior']}")
    if cont.get("enlace_siguiente"):
        L.append(f"- **Enlace con el siguiente**: {cont['enlace_siguiente']}")
    L += ["", "### Orden de escenas y tomas", "",
          "| Escena | # | Toma | Versículos | Nivel | Voz (s) | Clips 8 s (decl./nec.) | Transición de entrada |",
          "|---|---|---|---|---|---|---|---|"]
    n = 0
    for es in g["escenas"]:
        for t in es["tomas"]:
            n += 1
            f = filas[t["id"]]
            L.append(f"| {es['id']} | {n} | {t['id']} | {t['versiculos']} | {t['nivel']} | {f['segundos']:.1f} | "
                     f"{f['clips']}/{f['clips_necesarios']} | {t['transicion']} |")
    L += ["", "Cálculo por toma: palabras de las partes ÷ 150 × 60 s; clips necesarios = duración ÷ 8 s redondeado "
              "hacia arriba. En B y C los clips son opcionales (imagen con movimiento leve o fija).", ""]
    if g.get("decisiones_pendientes"):
        L += ["## Decisiones pendientes del usuario", ""] + [f"- {d}" for d in g["decisiones_pendientes"]] + [""]
    n = 0
    for en, es in enumerate(g["escenas"], 1):
        L += [f"## Escena {en} · {es['titulo']} · {es['versiculos']}", "",
              f"- **Propósito**: {es['proposito']}", f"- **Progresión visual**: {es['progresion_visual']}"]
        if es.get("cierre"):
            L.append(f"- **Cierre / estribillo**: {es['cierre']}")
        L.append("")
        for t in es["tomas"]:
            n += 1
            f = filas[t["id"]]
            esc = S[t["escenario"]]
            elems = [P[p]["element"]["nombre"] for p in t.get("personajes", [])] + [esc["element"]["nombre"]]
            L += [f"### Toma {n} · {t['id']} · {t.get('titulo', '')} · {t['versiculos']}", "",
                  f"- **Nivel**: {t['nivel']} ({NIVELES[t['nivel']]}) · **perfil**: {t['perfil']} · "
                  f"**clips de 8 s**: {t['clips_8s']} declarados, {f['clips_necesarios']} para cubrir la voz",
                  f"- **Duración de voz (Cálculo)**: {f['palabras']} palabras ÷ 150 × 60 = {f['segundos']:.1f} s"
                  + "".join(f"; {('narrador' if v == 'narrador' else P[k['voces'][v]]['nombre'])}: {w} palabras = "
                            f"{w * 60 / k['ppm']:.1f} s" for v, w in f["por_voz"].items()),
                  "- **Personajes en cuadro**: "
                  + (", ".join(P[p]["nombre"] for p in t.get("personajes", [])) or "ninguno")
                  + (f" · figurantes: {t['figurantes']}" if t.get("figurantes") else ""),
                  f"- **Escenario**: {esc['nombre']}",
                  f"- **Elements a usar**: {', '.join('`' + e + '`' for e in elems)}",
                  f"- **Transición de entrada**: {t['transicion']}", "", "**Voz y texto**", ""]
            for pa in t["partes"]:
                quien = "Narrador" if pa["voz"] == "narrador" else P[k["voces"][pa["voz"]]]["nombre"]
                L.append(f"- `{pa['ref']}` **{quien}**: {pa['texto']}")
            im = t["imagen"]
            L += ["", f"**Imagen inicial** → guardar como `{IMAGENES}/{g['libro']}/{g['id']}-{t['id']}.png`", "",
                  f"_{im['descripcion_es']}_", "", "Adjuntar en ChatGPT (en este orden):", "",
                  f"- Láminas patrón de estilo: `{IMAGENES}/estilo/patron-1-paisaje.png`, `patron-2-interior.png`, "
                  "`patron-3-grupo.png` (siempre)"]
            for pj in t.get("personajes", []):
                L.append(f"- Hoja: {P[pj]['nombre']}: `{IMAGENES}/personajes/{pj}.png`")
            L.append(f"- Hoja del escenario: {esc['nombre']}: `{IMAGENES}/escenarios/{t['escenario']}.png`")
            for r in im.get("referencias", []):
                L.append(f"- Referencia de época {r}: {R[r]['titulo']} ({R[r]['institucion']}) — {R[r]['url_imagen']}")
            L += ["", "Prompt para ChatGPT Images o GPT Image en Higgsfield (copiar entero):", "", "```text",
                  prompt_imagen(E, im), "```", ""]
            mv = t.get("movimiento")
            if mv:
                L += ["**Movimiento**", "", f"_{mv.get('descripcion_es', '')}_", "", "```text",
                      f"{E['base_movimiento_en']} {mv['prompt_en']}", "```", "",
                      "Etiquetas de cámara (nombres exactos en Cinema Studio: no verificados): "
                      + " ".join(f"`#{x}`" for x in mv["camara"]), ""]
            if t.get("lipsync"):
                L += [f"**Lipsync**: {t['lipsync']}", ""]
            L += ["**Fidelidad**", ""] + lista_certeza(t["fidelidad"]) + [""]
    return "\n".join(L) + "\n"


def narracion(g, c, F):
    P = F["personajes"]
    k = c[g["id"]]
    L = [f"{g['id']} · {g['montaje']['titulo']} ({k['rango']}) · Texto: Reina-Valera 1909",
         "Guion de audio. Narrador: voz de guiones/estilo.md. Personajes: su voz en Lipsync Studio.",
         "Se leen tal cual las formas antiguas (crió, á, fué); sin corchetes.", ""]
    n = 0
    for en, es in enumerate(g["escenas"], 1):
        L += [f"# Escena {en} · {es['titulo']} · {es['versiculos']}", ""]
        for t in es["tomas"]:
            n += 1
            L.append(f"## Toma {n} · {t['id']} · {t['versiculos']}")
            for pa in t["partes"]:
                quien = "NARRADOR" if pa["voz"] == "narrador" else P[k["voces"][pa["voz"]]]["nombre"].upper()
                L.append(f"{quien}: {norm(pa['texto'].replace('[', '').replace(']', ''))}")
            L.append("")
    return "\n".join(L)


def prompt_imagen(E, im):
    """Prompt completo en lenguaje natural: estilo + escena + qué evitar (GPT Image no tiene campo negativo)."""
    return " ".join(x for x in (E["base_imagen_en"], im["prompt_en"], E["negativo_en"], im.get("negativo_en", ""))
                    if x)


def hoja_ficha(x, tipo, F):
    R = F["referencias"]
    h = x["hoja_referencia"]
    L = [f"# {x['nombre']} ({tipo})", "", "Generado por `python -I herramientas/guiones.py`. No editar a mano.", "",
         f"- **Element en Cinema Studio**: `{x['element']['nombre']}` ({x['element'].get('tipo', '')})"]
    if x.get("personas"):
        L.append(f"- **Personas (datos/biblia.js)**: {', '.join(x['personas'])}")
    if x.get("pasajes"):
        L.append(f"- **Pasajes**: {', '.join(x['pasajes'])}")
    if x.get("nota"):
        L.append(f"- **Nota**: {x['nota']}")
    L.append("")
    for clave, titulo in (("edades", "Edad"), ("texto", "Lo que dice el texto"), ("rasgos", "Rasgos"),
                          ("vestuario", "Vestuario"), ("epoca", "Época visual"), ("miembros", "Miembros")):
        v = x.get(clave)
        if not v:
            continue
        L += [f"## {titulo}", ""]
        if clave == "miembros":
            L += [f"- {m['nombre']} ({m['persona']}): {m.get('rol_visual', '')}" for m in v]
        elif isinstance(v, dict):
            L += lista_certeza([v])
            for ps in v.get("posturas", []):
                L.append(f"  - Postura: {ps['resumen']} — {ps['fuente']}")
        else:
            L += lista_certeza(v)
        L.append("")
    if x.get("voz"):
        L += ["## Voz", "", x["voz"]["descripcion"], ""]
    if x.get("referencias"):
        L += ["## Referencias de época", ""] + [credito(r, R[r]) for r in x["referencias"]] + [""]
    carpeta = "personajes" if tipo == "personaje" else "escenarios"
    L += ["## Hoja de referencia del Element", "",
          f"Generar en ChatGPT Images (o GPT Image en Higgsfield) y guardar como `{IMAGENES}/{carpeta}/{x['id']}.png`; "
          f"luego subirla a Cinema Studio como Element `{x['element']['nombre']}`.", ""]
    L += [f"Adjuntar en ChatGPT, siempre, las tres láminas patrón de estilo (`{IMAGENES}/estilo/`, ver `estilo.md`)."
          + (" Además, las referencias de época de arriba (descargadas de su URL de Commons)." if x.get("referencias") else ""),
          ""]
    L += [f"_{h['prompt_es']}_ Evitar: _{h['negativo_es']}_", "", "```text",
          prompt_imagen(F["estilo"], {"prompt_en": h["prompt_en"], "negativo_en": h["negativo_en"]}), "```", ""]
    return "\n".join(L)


def escribir(F, calc, salida):
    escritos = []
    for gid, g in F["guiones"].items():
        d = salida / g["libro"]
        d.mkdir(parents=True, exist_ok=True)
        for nombre, txt in ((f"{gid}.md", hoja_guion(g, calc, F)), (f"{gid}.narracion.txt", narracion(g, calc, F))):
            (d / nombre).write_text(txt, encoding="utf-8")
            escritos.append(d / nombre)
    for carpeta, fichas, tipo in (("personajes", F["personajes"], "personaje"),
                                  ("escenarios", F["escenarios"], "escenario")):
        d = salida / carpeta
        d.mkdir(parents=True, exist_ok=True)
        for i, x in fichas.items():
            (d / f"{i}.md").write_text(hoja_ficha(x, tipo, F), encoding="utf-8")
            escritos.append(d / f"{i}.md")
    return escritos


# --------------------------------------------------------------------------- carga
def cargar_fuentes(d):
    F = {"personajes": {}, "escenarios": {}, "guiones": {}, "archivos": {}}
    F["estilo"] = json.loads((d / "estilo.json").read_text(encoding="utf-8"))
    F["referencias"] = json.loads((d / "referencias.json").read_text(encoding="utf-8"))
    for tipo, carpeta in (("personaje", "personajes"), ("escenario", "escenarios")):
        for a in sorted((d / carpeta).glob("*.json")):
            F[carpeta][a.stem] = json.loads(a.read_text(encoding="utf-8"))
            F["archivos"][(tipo, a.stem)] = f"{carpeta}/{a.name}"
    for a in sorted(d.glob("*/*.json")):
        if a.parent.name in ("personajes", "escenarios"):
            continue
        F["guiones"][a.stem] = json.loads(a.read_text(encoding="utf-8"))
        F["archivos"][("guion", a.stem)] = f"{a.parent.name}/{a.name}"
    return F


# --------------------------------------------------------------------------- autoprueba
def fixture():
    biblia = {
        "libros": [{"id": "Gn", "nombre": "Génesis", "capitulos": 50}],
        "capitulos": [{"libro": "Gn", "cap": 45, "versiculos": [
            {"n": 1, "texto": "NO podía ya José contenerse, y clamó: Haced salir á todos. Y no quedó nadie."},
            {"n": 2, "texto": "Y dijo José á sus hermanos: Yo soy José. Y sus [hermanos] callaron."},
            {"n": 3, "texto": "Y besó á todos sus hermanos: y después sus hermanos hablaron con él."}]}],
        "personas": [{"id": "Joseph_1", "nombre": "José"}, {"id": "Judah_1", "nombre": "Judá"}],
        "menciones": [{"ref": "Gn 45:1", "persona": "Joseph_1"}, {"ref": "Gn 45:2", "persona": "Joseph_1"}],
        "pasajes": [{"id": "gn-98", "libro": "Gn", "inicio": "Gn 45:1", "fin": "Gn 45:3", "titulo": "José se da a conocer"}],
    }
    hoja = {"prompt_en": "A man.", "prompt_es": "hombre", "negativo_en": "No text.", "negativo_es": "x"}
    F = {
        "estilo": {"base_imagen_en": "Sober painting.", "base_imagen_es": "Pintura.", "negativo_en": "no halo",
                   "negativo_es": "sin halo", "base_movimiento_en": "Slow.", "base_movimiento_es": "Lento.",
                   "rotulo_ia": "Ilustración moderna (generada con IA)", "rotulo_texto": "Texto: Reina-Valera 1909",
                   "palabras_por_minuto": 150, "segundos_clip": 8, "prohibidos_prompt": ["halo", "god"],
                   "nombre_estilo": "Estilo de prueba"},
        "referencias": {"R1": {"titulo": "t", "institucion": "Met", "datacion": "ca. 1900 a. C.", "url_ficha": "u",
                               "url_imagen": "u", "licencia": "CC0", "inventario": "1", "comprobado": True},
                        "R2": {"titulo": "t", "institucion": "Met", "datacion": "d", "url_ficha": "u",
                               "comprobado": False}},
        "personajes": {"jose": {"id": "jose", "nombre": "José", "personas": ["Joseph_1"],
                                "element": {"nombre": "JOSE"}, "hoja_referencia": hoja, "voz": {"descripcion": "v"},
                                "referencias": ["R1"],
                                "edades": [{"dato": "edad", "certeza": "calculo", "valor": 3, "calculo": {
                                    "operacion": "suma", "resultado": 3, "supuestos": ["s"],
                                    "pasos": [{"texto": "a", "valor": 1, "ref": "Gn 45:1", "cita": "clamó"},
                                              {"texto": "b", "valor": 2, "ref": "Gn 45:2", "cita": "Yo soy José"}]}}],
                                "rasgos": [{"rasgo": "habla", "certeza": "texto", "ref": "Gn 45:2",
                                            "cita": "Yo soy José"}]}},
        "escenarios": {"sala": {"id": "sala", "nombre": "Sala", "element": {"nombre": "SALA"},
                                "hoja_referencia": hoja,
                                "texto": [{"dato": "d", "certeza": "texto", "ref": "Gn 45:1", "cita": "Haced salir"}]}},
        "guiones": {"gn-98": {
            "id": "gn-98", "libro": "Gn", "inicio": "Gn 45:1", "fin": "Gn 45:3",
            "montaje": {"archivo": "gn-98.mp4", "titulo": "José se da a conocer", "musica": {"usar": False}},
            "prohibido_hasta": [{"hasta": "Gn 45:1", "terminos": ["sun"]}],
            "discursos": [
                {"id": "d1", "persona": "Joseph_1", "ref": "Gn 45:1", "introduccion": "y clamó:",
                 "fin_ref": "Gn 45:1", "fin_cita": "Haced salir á todos."},
                {"id": "d2", "persona": "Joseph_1", "ref": "Gn 45:2", "introduccion": "Y dijo José á sus hermanos:",
                 "fin_ref": "Gn 45:2", "fin_cita": "Yo soy José."}],
            "continuidad": {"empieza_con": "sala", "termina_con": "abrazo"},
            "escenas": [{"id": "e1", "titulo": "a", "proposito": "p", "versiculos": "Gn 45:1",
                         "progresion_visual": "v", "tomas": [
                {"id": "t1", "nivel": "A", "perfil": "todos", "transicion": "fundido", "versiculos": "Gn 45:1",
                 "personajes": ["jose"], "escenario": "sala", "clips_8s": 1,
                 "imagen": {"prompt_en": "A hall.", "descripcion_es": "sala", "referencias": ["R1"]},
                 "movimiento": {"prompt_en": "slow", "camara": ["static"]},
                 "fidelidad": [{"dato": "x", "certeza": "interpretacion", "nota": "n"}],
                 "partes": [
                     {"ref": "Gn 45:1", "voz": "narrador", "texto": "NO podía ya José contenerse, y clamó:"},
                     {"ref": "Gn 45:1", "voz": "Joseph_1", "discurso": "d1", "texto": "Haced salir á todos."},
                     {"ref": "Gn 45:1", "voz": "narrador", "texto": "Y no quedó nadie."}]}]},
                {"id": "e2", "titulo": "b", "proposito": "p", "versiculos": "Gn 45:2-3",
                 "progresion_visual": "v", "tomas": [
                {"id": "t2", "nivel": "C", "perfil": "todos", "transicion": "corte", "versiculos": "Gn 45:2-3",
                 "personajes": ["jose"], "escenario": "sala", "clips_8s": 0,
                 "imagen": {"prompt_en": "A hall.", "descripcion_es": "sala"}, "movimiento": None,
                 "fidelidad": [{"dato": "x", "certeza": "texto", "ref": "Gn 45:3", "cita": "besó"}],
                 "partes": [
                     {"ref": "Gn 45:2", "voz": "narrador", "texto": "Y dijo José á sus hermanos:"},
                     {"ref": "Gn 45:2", "voz": "Joseph_1", "discurso": "d2", "texto": "Yo soy José."},
                     {"ref": "Gn 45:2", "voz": "narrador", "texto": "Y sus [hermanos] callaron."},
                     {"ref": "Gn 45:3", "voz": "narrador",
                      "texto": "Y besó á todos sus hermanos: y después sus hermanos hablaron con él."}]}]}]}},
    }
    return biblia, F


def autoprueba():
    biblia, F0 = fixture()
    fallos = []
    e, a, c = validar(F0, biblia)
    if e:
        fallos.append(f"el fixture válido falla: {e}")
    G = lambda F: F["guiones"]["gn-98"]  # noqa: E731
    T = lambda F, n: [t for es in G(F)["escenas"] for t in es["tomas"]][n]  # noqa: E731
    Es = lambda F, n: G(F)["escenas"][n]  # noqa: E731

    def judah_habla(F):
        p = T(F, 1)["partes"]
        p[3:4] = [{"ref": "Gn 45:3", "voz": "narrador", "texto": "Y besó á todos sus hermanos: y después"},
                  {"ref": "Gn 45:3", "voz": "Judah_1", "texto": "sus hermanos hablaron con él."}]

    def discurso_sin_dos_puntos(F):
        G(F)["discursos"].append({"id": "d3", "persona": "Judah_1", "ref": "Gn 45:3",
                                  "introduccion": "y después sus hermanos hablaron con él.", "fin_ref": "Gn 45:3",
                                  "fin_cita": "con él."})

    def narrador_en_discurso(F):
        T(F, 0)["partes"][1]["voz"] = "narrador"

    def parte_cruza(F):
        p = T(F, 0)["partes"]
        p[1:3] = [{"ref": "Gn 45:1", "voz": "Joseph_1", "discurso": "d1",
                   "texto": "Haced salir á todos. Y no quedó nadie."}]

    casos = {
        "falta un versículo": lambda F: T(F, 1)["partes"].pop(),
        "texto alterado": lambda F: T(F, 0)["partes"][0].__setitem__("texto", "NO podia ya José contenerse, y clamó:"),
        "sin corchetes": lambda F: T(F, 1)["partes"][2].__setitem__("texto", "Y sus hermanos callaron."),
        "orden de escenas cambiado": lambda F: G(F)["escenas"].reverse(),
        "escena con hueco": lambda F: Es(F, 1).__setitem__("versiculos", "Gn 45:3"),
        "escenas solapadas": lambda F: Es(F, 0).__setitem__("versiculos", "Gn 45:1-2"),
        "toma fuera de su escena": lambda F: (Es(F, 0).__setitem__("versiculos", "Gn 45:1-2"),
                                               Es(F, 1).__setitem__("versiculos", "Gn 45:3")),
        "escena sin propósito": lambda F: Es(F, 0).pop("proposito"),
        "sin continuidad": lambda F: G(F).pop("continuidad"),
        "versículo repetido": lambda F: T(F, 1)["partes"].insert(0, dict(T(F, 0)["partes"][2])),
        "persona habla sin discurso (45:15)": judah_habla,
        "discurso sin «:»": discurso_sin_dos_puntos,
        "narrador dentro de un discurso declarado": narrador_en_discurso,
        "parte que cruza el fin del discurso": parte_cruza,
        "voz desconocida": lambda F: T(F, 0)["partes"][1].__setitem__("voz", "Nadie_9"),
        "cita no literal": lambda F: F["personajes"]["jose"]["rasgos"][0].__setitem__("cita", "Yo soy Jose"),
        "certeza texto sin cita": lambda F: F["personajes"]["jose"]["rasgos"][0].pop("cita"),
        "certeza desconocida": lambda F: T(F, 0)["fidelidad"][0].__setitem__("certeza", "probable"),
        "inferido sin nota": lambda F: T(F, 0)["fidelidad"].append({"dato": "x", "certeza": "inferido"}),
        "resta mal hecha": lambda F: F["personajes"]["jose"]["edades"][0]["calculo"].__setitem__("operacion", "resta"),
        "operación desconocida": lambda F: F["personajes"]["jose"]["edades"][0]["calculo"].__setitem__("operacion", "x"),
        "cálculo que no suma": lambda F: F["personajes"]["jose"]["edades"][0]["calculo"].__setitem__("resultado", 4),
        "personaje inexistente": lambda F: T(F, 0)["personajes"].append("benjamin"),
        "escenario inexistente": lambda F: T(F, 0).__setitem__("escenario", "patio"),
        "referencia no comprobada": lambda F: T(F, 0)["imagen"]["referencias"].append("R2"),
        "referencia inexistente": lambda F: F["personajes"]["jose"]["referencias"].append("R9"),
        "rango distinto del pasaje": lambda F: G(F).__setitem__("fin", "Gn 45:2"),
        "id sin pasaje": lambda F: F["guiones"].__setitem__("gn-99", dict(G(F), id="gn-99")),
        "archivo de montaje": lambda F: G(F)["montaje"].__setitem__("archivo", "otro.mp4"),
        "título de montaje": lambda F: G(F)["montaje"].__setitem__("titulo", "Otro"),
        "halo en el prompt": lambda F: T(F, 0)["imagen"].__setitem__("prompt_en", "a man with a halo"),
        "Dios con figura en el prompt": lambda F: T(F, 1)["imagen"].__setitem__("prompt_en", "God as an old man"),
        "sol antes de tiempo": lambda F: T(F, 0)["movimiento"].__setitem__("prompt_en", "the sun rises"),
        "nivel A sin clips": lambda F: T(F, 0).__setitem__("clips_8s", 0),
        "nivel A sin movimiento": lambda F: T(F, 0).__setitem__("movimiento", None),
        "versiculos de toma mal": lambda F: T(F, 1).__setitem__("versiculos", "Gn 45:2"),
        "etiqueta # en prompt de imagen": lambda F: T(F, 0)["imagen"].__setitem__("prompt_en", "A hall #static."),
        "prompt de imagen como lista": lambda F: T(F, 0)["imagen"].__setitem__("prompt_en", "hall, columns, lamps"),
        "transición desconocida": lambda F: T(F, 0).__setitem__("transicion", "barrido"),
        "estilo.md desalineado": None,
    }
    for nombre, mut in casos.items():
        F = copy.deepcopy(F0)
        if mut is None:
            e, _, _ = validar(F, biblia, estilo_md="otra cosa")
        else:
            mut(F)
            e, _, _ = validar(F, biblia)
        if not e:
            fallos.append(f"debía fallar y pasó: {nombre}")
    # aviso de clips: una toma A con más voz que sus clips
    F = copy.deepcopy(F0)
    T(F, 0)["partes"][2]["texto"] = "Y no quedó nadie."
    T(F, 0)["clips_8s"] = 1
    biblia2 = copy.deepcopy(biblia)
    largo = " ".join(["palabra"] * 30)
    biblia2["capitulos"][0]["versiculos"][0]["texto"] = (
        f"NO podía ya José contenerse, y clamó: Haced salir á todos. Y no quedó nadie. {largo}")
    T(F, 0)["partes"][2]["texto"] = f"Y no quedó nadie. {largo}"
    e, a, _ = validar(F, biblia2)
    if e or not any("necesita" in x for x in a):
        fallos.append(f"debía avisar de clips insuficientes: {e or a}")
    print(f"autoprueba: {len(casos) + 2} casos, {len(fallos)} fallos")
    for f in fallos:
        print("  FALLO:", f)
    return 1 if fallos else 0


# --------------------------------------------------------------------------- main
def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    if "--autoprueba" in argv:
        return autoprueba()
    fuentes = Path(argv[argv.index("--fuentes") + 1]) if "--fuentes" in argv else FUENTES
    salida = Path(argv[argv.index("--salida") + 1]) if "--salida" in argv else SALIDA
    F = cargar_fuentes(fuentes)
    biblia = cargar_js(BIBLIA)
    md = salida / ESTILO_MD
    estilo_md = md.read_text(encoding="utf-8") if md.exists() else ""
    errores, avisos, calc = validar(F, biblia, estilo_md)
    for a in avisos:
        print("AVISO:", a)
    if errores:
        for e in errores:
            print("ERROR:", " · ".join(map(str, e)))
        print(f"{len(errores)} errores; no se escribe nada.")
        return 1
    for gid in F["guiones"]:
        k = calc[gid]
        print(f"{gid}: {len(k['filas'])} tomas, {k['total_palabras']} palabras ≈ {k['total_segundos']:.1f} s "
              f"({fmt_s(k['total_segundos'])}) a {k['ppm']} palabras/min")
    no_usadas = sorted(r for r, x in F["referencias"].items() if x.get("comprobado") and r not in calc["_usadas"])
    if no_usadas:
        print("Referencias comprobadas sin usar:", ", ".join(no_usadas))
    if "--sin-salida" in argv:
        print("OK (sin salida)")
        return 0
    escritos = escribir(F, calc, salida)
    print(f"OK: {len(escritos)} archivos escritos en {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
