"""Genera datos/explicaciones.js (window.BIBLIA_EXPLICACIONES): términos que se explican al tocarlos en la lectura
(palabras antiguas, medidas, conceptos) y pasajes difíciles, verificados contra el texto RV1909 de datos/biblia.js.

Sin red. Regenerar: python -I herramientas/explicaciones.py
Opciones:
  --fuentes DIR   lee las fuentes de DIR (por defecto herramientas/explicaciones)
  --salida RUTA   escribe en RUTA (por defecto datos/explicaciones.js)
  --sin-salida    solo verifica, no escribe nada
  --autoprueba    corre un fixture interno: el válido debe pasar y cada copia alterada debe fallar. No escribe nada.

Fuentes (en DIR):
  terminos*.json      {id: término}; varios archivos se unen (un id repetido entre archivos es error)
  pasajes-<Libro>.json {id: pasaje difícil}
  auditoria.json      opcional: {id: {"veredicto": "OK"|"AJUSTAR"|"RECHAZAR", "nota": "…"}}
                      RECHAZAR no se publica; AJUSTAR se informa.

Término: {tipo: palabra|medida|concepto, lema, formas: [..], adulto, nino, certeza: texto|inferido|calculo|externa,
          fuentes: [fuente, ..], calculo?: {resultado, pasos: [..], supuestos: [..], fuente: fuente},
          excluir?: [ref|rango, ..], solo?: [ref|rango, ..] | null}
Pasaje: {refs: "Jue 11:29-40", titulo, dice: [{ref, cita}], posturas: [{resumen, fuente}], nino: texto | null,
         certeza}
Fuente: {tipo: "biblia"|"diccionario"|"rae"|"obra", ref?, cita?, obra?, autor?, entrada?, url?, idioma?}
  biblia      ref obligatoria (versículo o rango de un libro cargado); cita, si va, literal de ese versículo
              (o de uno del rango)
  diccionario obra y entrada obligatorias (url recomendada)
  rae         entrada y url obligatorias (el DLE solo se enlaza)
  obra        obra y autor obligatorios
  idioma      código de idioma de la fuente si no es español («en»)

Si falla una verificación imprime cada error (archivo · id · campo) y sale con código != 0 sin escribir.
Diseño: docs/superpowers/specs/2026-11-13-explicaciones-design.md
"""
import copy
import datetime
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"
FUENTES = Path(__file__).resolve().parent / "explicaciones"
SALIDA = DATOS / "explicaciones.js"

TIPOS_TERMINO = {"palabra", "medida", "concepto"}
CERTEZAS = {"texto", "inferido", "calculo", "externa"}
TIPOS_FUENTE = {"biblia", "diccionario", "rae", "obra"}
CAMPOS_FUENTE = {"tipo", "ref", "cita", "obra", "autor", "entrada", "url", "idioma"}
CAMPOS_TERMINO = {"tipo", "lema", "formas", "adulto", "nino", "certeza", "fuentes", "calculo", "excluir", "solo"}
CAMPOS_PASAJE = {"refs", "titulo", "dice", "posturas", "nino", "certeza"}
VEREDICTOS = {"OK", "AJUSTAR", "RECHAZAR"}
MUCHAS = 150  # más versículos con el término que esto: aviso de posible ambigüedad
# Libros conocidos (para distinguir «libro aún no cargado» de una errata en excluir/solo).
CANON = ["Gn", "Ex", "Lv", "Nm", "Dt", "Jos", "Jue", "Rut", "Rt", "1S", "2S", "1R", "2R", "1Cr", "2Cr", "Esd", "Neh",
         "Est", "Job", "Sal", "Pr", "Ec", "Cnt", "Is", "Jer", "Lm", "Ez", "Dn", "Os", "Jl", "Am", "Abd", "Jon", "Mi",
         "Nah", "Hab", "Sof", "Hag", "Zac", "Mal", "Mt", "Mr", "Lc", "Jn", "Hch", "Ro", "1Co", "2Co", "Ga", "Ef", "Fil",
         "Col", "1Ts", "2Ts", "1Ti", "2Ti", "Tit", "Flm", "He", "Stg", "1P", "2P", "1Jn", "2Jn", "3Jn", "Jud", "Ap"]
REF_RE = re.compile(r"^([1-3]?[A-Za-z]+) (\d+):(\d+)(?:-(?:(\d+):)?(\d+))?$")
URL_RE = re.compile(r"^https?://\S+$")
ID_RE = re.compile(r"^[^\s]+$")
IDIOMA_RE = re.compile(r"^[a-z]{2,3}$")


def cargar_js(ruta):
    s = ruta.read_text(encoding="utf-8")
    return json.loads(s[s.index("{"):s.rindex("}") + 1])


def u16(s, i):
    """Índice de Python → offset UTF-16 (como los de `menciones`)."""
    return len(s[:i].encode("utf-16-le")) // 2


class Texto:
    """Versículos de biblia.js en orden canónico, con índice global."""

    def __init__(self, biblia):
        self.libros = [l["id"] for l in biblia["libros"]]
        self.orden, self.idx, self.V = [], {}, {}
        caps = sorted(biblia["capitulos"], key=lambda c: (self.libros.index(c["libro"]), c["cap"]))
        for c in caps:
            for v in c["versiculos"]:
                ref = f'{c["libro"]} {c["cap"]}:{v["n"]}'
                self.idx[ref] = len(self.orden)
                self.orden.append(ref)
                self.V[ref] = v.get("texto") or ""

    def rango(self, s):
        """'Lib C:V', 'Lib C:V-V' o 'Lib C:V-C:V' → (i, j, None) o (None, None, motivo)."""
        m = REF_RE.match(s) if isinstance(s, str) else None
        if not m:
            return None, None, f"referencia mal formada {s!r}"
        lb, c, v, c2, v2 = m.groups()
        if lb not in self.libros:
            return None, None, (f"libro no cargado: {lb}" if lb in CANON else f"libro desconocido: {lb}")
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


# --------------------------------------------------------------------------- construcción y verificación
def construir(terminos_arch, pasajes_arch, auditoria, biblia):
    """terminos_arch / pasajes_arch: {archivo: {id: obj}}; auditoria: dict o None.
    Devuelve (doc | None, errores, avisos). errores: [(archivo, id, campo, msg)]."""
    T = Texto(biblia)
    errores, avisos = [], []

    def err(arch, id_, campo, msg):
        errores.append((arch, id_, campo, msg))

    def texto_ok(x, arch, id_, campo):
        if not isinstance(x, str) or not x.strip():
            err(arch, id_, campo, "falta el texto (cadena no vacía)")
            return False
        return True

    def rango_ok(r, arch, id_, campo, cargado=True):
        i, j, motivo = T.rango(r)
        if motivo:
            if not cargado and motivo.startswith("libro no cargado"):
                avisos.append(f"{arch} · {id_} · {campo}: {motivo} (se ignora hasta cargarlo)")
            else:
                err(arch, id_, campo, motivo)
            return None
        return i, j

    def cita_ok(ref, cita, arch, id_, campo):
        r = rango_ok(ref, arch, id_, campo + ".ref")
        if r is None or cita is None:
            return r
        if not isinstance(cita, str) or not cita.strip():
            err(arch, id_, campo + ".cita", "cita vacía")
        elif not any(cita in T.V[T.orden[k]] for k in range(r[0], r[1] + 1)):
            err(arch, id_, campo + ".cita", f"la cita {cita!r} no es literal de {ref}")
        return r

    def fuente_ok(f, arch, id_, campo):
        if not isinstance(f, dict):
            err(arch, id_, campo, "la fuente no es un objeto")
            return None
        extra = set(f) - CAMPOS_FUENTE
        if extra:
            err(arch, id_, campo, f"campos no previstos en la fuente: {sorted(extra)} (esquema: {sorted(CAMPOS_FUENTE)})")
        tipo = f.get("tipo")
        if tipo not in TIPOS_FUENTE:
            err(arch, id_, campo + ".tipo", f"tipo de fuente {tipo!r} (válidos: {sorted(TIPOS_FUENTE)})")
            return None
        for k in ("ref", "cita", "obra", "autor", "entrada", "url", "idioma"):
            if k in f and f[k] is not None and not (isinstance(f[k], str) and f[k].strip()):
                err(arch, id_, f"{campo}.{k}", "debe ser texto no vacío")
        if f.get("url") and not URL_RE.match(f["url"]):
            err(arch, id_, campo + ".url", f"url no válida {f['url']!r}")
        if f.get("idioma") and not IDIOMA_RE.match(f["idioma"]):
            err(arch, id_, campo + ".idioma", f"idioma {f['idioma']!r} (código como «en»)")
        if tipo == "biblia":
            if not f.get("ref"):
                err(arch, id_, campo + ".ref", "una fuente bíblica necesita ref")
            else:
                cita_ok(f["ref"], f.get("cita"), arch, id_, campo)
        else:
            if f.get("ref") or f.get("cita"):
                err(arch, id_, campo, "ref y cita son solo para fuentes de tipo biblia")
            pide = {"diccionario": ("obra", "entrada"), "rae": ("entrada", "url"), "obra": ("obra", "autor")}[tipo]
            for k in pide:
                if not f.get(k):
                    err(arch, id_, f"{campo}.{k}", f"una fuente de tipo {tipo} necesita {k}")
            if tipo == "diccionario" and not f.get("url"):
                avisos.append(f"{arch} · {id_} · {campo}: diccionario sin url")
        return tipo

    # ---- unión de archivos e ids únicos (términos y pasajes comparten espacio de ids)
    terminos, pasajes, origen = {}, {}, {}
    for destino, grupo in ((terminos, terminos_arch), (pasajes, pasajes_arch)):
        for arch, obj in sorted(grupo.items()):
            if not isinstance(obj, dict):
                err(arch, "-", "-", "el archivo debe ser un objeto {id: …}")
                continue
            for id_, x in obj.items():
                if not ID_RE.match(id_):
                    err(arch, id_, "id", "id vacío o con espacios")
                if id_ in origen:
                    err(arch, id_, "id", f"id repetido (también en {origen[id_]})")
                    continue
                origen[id_] = arch
                destino[id_] = x

    # ---- auditoría
    rechazados, audit = set(), auditoria or {}
    if not isinstance(audit, dict):
        err("auditoria.json", "-", "-", "debe ser un objeto {id: {veredicto, nota}}")
        audit = {}
    for id_, a in audit.items():
        v = a.get("veredicto") if isinstance(a, dict) else None
        if v not in VEREDICTOS:
            err("auditoria.json", id_, "veredicto", f"veredicto {v!r} (válidos: {sorted(VEREDICTOS)})")
            continue
        if id_ not in origen:
            avisos.append(f"auditoria.json · {id_}: no hay término ni pasaje con ese id")
            continue
        nota = (a.get("nota") or "").strip()
        if v == "RECHAZAR":
            rechazados.add(id_)
            avisos.append(f"RECHAZADO (no se publica): {id_}" + (f" — {nota}" if nota else ""))
        elif v == "AJUSTAR":
            avisos.append(f"AJUSTAR: {id_}" + (f" — {nota}" if nota else ""))

    # ---- términos
    forma_de = {}  # forma en minúsculas → id del término
    patrones = []  # (id, forma, regex, permitidos | None)
    for id_, t in terminos.items():
        arch = origen[id_]
        if not isinstance(t, dict):
            err(arch, id_, "-", "el término no es un objeto")
            continue
        extra = set(t) - CAMPOS_TERMINO
        if extra:
            err(arch, id_, "-", f"campos no previstos: {sorted(extra)}")
        if t.get("tipo") not in TIPOS_TERMINO:
            err(arch, id_, "tipo", f"tipo {t.get('tipo')!r} (válidos: {sorted(TIPOS_TERMINO)}; los pasajes van en pasajes-<Libro>.json)")
        for k in ("lema", "adulto", "nino"):
            texto_ok(t.get(k), arch, id_, k)
        if t.get("certeza") not in CERTEZAS:
            err(arch, id_, "certeza", f"certeza {t.get('certeza')!r} (válidas: {sorted(CERTEZAS)})")
        fs = t.get("fuentes")
        tipos_f = []
        if not isinstance(fs, list) or not fs:
            err(arch, id_, "fuentes", "hace falta al menos una fuente")
        else:
            tipos_f = [fuente_ok(f, arch, id_, f"fuentes[{n}]") for n, f in enumerate(fs)]
        if t.get("certeza") == "texto" and not any(f.get("tipo") == "biblia" and f.get("cita") for f in (fs or []) if isinstance(f, dict)):
            err(arch, id_, "certeza", "certeza «texto» pide una fuente bíblica con cita")
        if t.get("certeza") == "externa" and not any(x and x != "biblia" for x in tipos_f):
            err(arch, id_, "certeza", "certeza «externa» pide una fuente de fuera de la Biblia")
        calc = t.get("calculo")
        if t.get("tipo") == "medida" and calc is None:
            err(arch, id_, "calculo", "una medida lleva su equivalencia como cálculo (resultado, pasos, supuestos, fuente)")
        if calc is not None:
            if not isinstance(calc, dict):
                err(arch, id_, "calculo", "debe ser un objeto")
            else:
                texto_ok(calc.get("resultado"), arch, id_, "calculo.resultado")
                for k in ("pasos", "supuestos"):
                    xs = calc.get(k)
                    if not isinstance(xs, list) or not xs or not all(isinstance(x, str) and x.strip() for x in xs):
                        err(arch, id_, f"calculo.{k}", "lista de textos no vacía")
                if "fuente" not in calc:
                    err(arch, id_, "calculo.fuente", "el cálculo necesita su fuente")
                else:
                    fuente_ok(calc["fuente"], arch, id_, "calculo.fuente")
                extra = set(calc) - {"resultado", "pasos", "supuestos", "fuente"}
                if extra:
                    err(arch, id_, "calculo", f"campos no previstos: {sorted(extra)}")
        # excluir y solo → conjuntos de índices de versículo
        def indices(campo):
            xs = t.get(campo)
            if xs is None:
                return None
            if not isinstance(xs, list):
                err(arch, id_, campo, "debe ser una lista de refs o null")
                return None
            out = set()
            for n, r in enumerate(xs):
                ij = rango_ok(r, arch, id_, f"{campo}[{n}]", cargado=False)
                if ij:
                    out.update(range(ij[0], ij[1] + 1))
            return out
        excl, solo = indices("excluir") or set(), indices("solo")
        formas = t.get("formas")
        if not isinstance(formas, list) or not formas:
            err(arch, id_, "formas", "hace falta al menos una forma")
            continue
        vistas = set()
        for f in formas:
            if not isinstance(f, str) or not f.strip() or f != f.strip():
                err(arch, id_, "formas", f"forma vacía o con espacios en los bordes: {f!r}")
                continue
            k = f.lower()
            if k in vistas:
                err(arch, id_, "formas", f"forma repetida {f!r}")
                continue
            vistas.add(k)
            if k in forma_de:
                err(arch, id_, "formas", f"la forma {f!r} ya es del término {forma_de[k]!r} ({origen[forma_de[k]]})")
                continue
            forma_de[k] = id_
            rx = re.compile(r"(?<![^\W\d_])" + re.escape(f) + r"(?![^\W\d_])", re.IGNORECASE)
            patrones.append((id_, k, rx, excl, solo))

    # ---- ocurrencias: cada forma en cada versículo permitido; en solapes gana la forma más larga
    publicados = [p for p in patrones if p[0] not in rechazados]
    ocurrencias, por_termino, descartes = {}, Counter(), []
    usados_excl = {id_: set() for id_ in terminos}
    for i, ref in enumerate(T.orden):
        txt = T.V[ref]
        if not txt:
            continue
        bajo = txt.lower()
        cand = []
        for id_, k, rx, excl, solo in publicados:
            if k not in bajo:
                continue
            for m in rx.finditer(txt):
                if i in excl or (solo is not None and i not in solo):
                    usados_excl[id_].add(i)
                    continue
                cand.append((m.start(), m.end(), id_))
        if not cand:
            continue
        cand.sort(key=lambda c: (-(c[1] - c[0]), c[0]))
        tomadas = []
        for c in cand:
            if any(c[0] < b and a < c[1] for a, b, _ in tomadas):
                descartes.append(f"{ref} «{txt[c[0]:c[1]]}» ({c[2]})")
                continue
            tomadas.append(c)
        tomadas.sort()
        for (a1, b1, _), (a2, b2, _) in zip(tomadas, tomadas[1:]):
            if a2 < b1:
                err("-", ref, "ocurrencias", "solape entre ocurrencias")
        ocurrencias[ref] = [{"t": id_, "i": u16(txt, a), "f": u16(txt, b)} for a, b, id_ in tomadas]
        for id_ in {c[2] for c in tomadas}:
            por_termino[id_] += 1
    for id_, t in terminos.items():
        if id_ in rechazados or not isinstance(t, dict):
            continue
        n = por_termino[id_]
        if n == 0:
            avisos.append(f"{origen[id_]} · {id_}: 0 ocurrencias en el texto cargado")
        elif n > MUCHAS:
            avisos.append(f"{origen[id_]} · {id_}: {n} versículos con el término (¿ambigüedad? revisar excluir/solo)")
        if isinstance(t.get("excluir"), list) and t["excluir"] and not usados_excl[id_]:
            avisos.append(f"{origen[id_]} · {id_}: excluir/solo no quita ninguna aparición")
    if descartes:
        avisos.append(f"{len(descartes)} aparición(es) descartadas por solaparse con una forma más larga: "
                      + "; ".join(descartes[:8]) + (" …" if len(descartes) > 8 else ""))

    # ---- pasajes difíciles
    for id_, p in pasajes.items():
        arch = origen[id_]
        if not isinstance(p, dict):
            err(arch, id_, "-", "el pasaje no es un objeto")
            continue
        extra = set(p) - CAMPOS_PASAJE
        if extra:
            err(arch, id_, "-", f"campos no previstos: {sorted(extra)}")
        rango_ok(p.get("refs"), arch, id_, "refs")
        texto_ok(p.get("titulo"), arch, id_, "titulo")
        if p.get("certeza") not in CERTEZAS:
            err(arch, id_, "certeza", f"certeza {p.get('certeza')!r} (válidas: {sorted(CERTEZAS)})")
        if p.get("nino") is not None:
            texto_ok(p.get("nino"), arch, id_, "nino")
        elif "nino" not in p:
            err(arch, id_, "nino", "falta nino (texto corto, o null si no se le muestra al niño)")
        dice = p.get("dice")
        if not isinstance(dice, list) or not dice:
            err(arch, id_, "dice", "hace falta al menos una cita de lo que dice el texto")
        else:
            for n, x in enumerate(dice):
                if not isinstance(x, dict) or not x.get("ref") or not x.get("cita"):
                    err(arch, id_, f"dice[{n}]", "cada elemento lleva ref y cita")
                else:
                    cita_ok(x["ref"], x["cita"], arch, id_, f"dice[{n}]")
        pos = p.get("posturas")
        if not isinstance(pos, list) or not pos:
            err(arch, id_, "posturas", "hace falta al menos una postura con su fuente")
        else:
            for n, x in enumerate(pos):
                if not isinstance(x, dict):
                    err(arch, id_, f"posturas[{n}]", "la postura no es un objeto")
                    continue
                texto_ok(x.get("resumen"), arch, id_, f"posturas[{n}].resumen")
                if set(x) - {"resumen", "fuente"}:
                    err(arch, id_, f"posturas[{n}]", f"campos no previstos: {sorted(set(x) - {'resumen', 'fuente'})}")
                if "fuente" not in x:
                    err(arch, id_, f"posturas[{n}].fuente", "cada postura lleva su fuente")
                elif fuente_ok(x["fuente"], arch, id_, f"posturas[{n}].fuente") == "biblia":
                    err(arch, id_, f"posturas[{n}].fuente", "una postura cita una obra de consulta, no solo la Biblia")

    if errores:
        return None, errores, avisos
    doc = {
        "generado": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
        "terminos": {k: v for k, v in sorted(terminos.items()) if k not in rechazados},
        "ocurrencias": ocurrencias,
        "pasajes": {k: v for k, v in sorted(pasajes.items()) if k not in rechazados},
    }
    return doc, errores, avisos


# --------------------------------------------------------------------------- E/S
def leer_fuentes(dirr):
    terminos, pasajes, auditoria, errores = {}, {}, None, []
    for ruta in sorted(Path(dirr).glob("*.json")):
        if not (ruta.name.startswith("terminos") or ruta.name.startswith("pasajes-") or ruta.name == "auditoria.json"):
            continue
        try:
            obj = json.loads(ruta.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            errores.append((ruta.name, "-", "-", f"JSON inválido: {e}"))
            continue
        if ruta.name == "auditoria.json":
            auditoria = obj
        elif ruta.name.startswith("terminos"):
            terminos[ruta.name] = obj
        else:
            pasajes[ruta.name] = obj
    return terminos, pasajes, auditoria, errores


def informar(errores, avisos, salida=sys.stderr):
    for a in avisos:
        print("aviso: " + a)
    if not errores:
        return
    print(f"{len(errores)} error(es):", file=salida)
    for arch, id_, campo, msg in sorted(errores, key=lambda e: (e[0], str(e[1]), e[2])):
        print(f"  {arch} · {id_} · {campo}: {msg}", file=salida)
    print("Resumen por archivo:", file=salida)
    for arch, n in sorted(Counter(e[0] for e in errores).items()):
        print(f"  {arch}: {n}", file=salida)


def resumen(doc):
    tipos = Counter(t["tipo"] for t in doc["terminos"].values())
    n = sum(len(x) for x in doc["ocurrencias"].values())
    return (f"{len(doc['terminos'])} términos (" + ", ".join(f"{k}: {v}" for k, v in sorted(tipos.items()))
            + f"), {n} ocurrencias en {len(doc['ocurrencias'])} versículos, {len(doc['pasajes'])} pasajes difíciles")


def escribir(salida, texto, intentos=6):
    """Escribe con reintentos: en Windows, un .js grande abierto por otro proceso da a veces OSError 22."""
    for n in range(intentos):
        try:
            salida.write_text(texto, encoding="utf-8")
            return
        except OSError as e:
            if n == intentos - 1 or getattr(e, "errno", None) not in (13, 22):
                raise
            time.sleep(0.5 * (n + 1))


# --------------------------------------------------------------------------- autoprueba
FIX_TERMINOS = {
    "terminos-a.json": {
        "siclo": {"tipo": "medida", "lema": "siclo", "formas": ["siclo", "siclos"], "adulto": "Peso.", "nino": "Un peso.",
                  "certeza": "texto",
                  "fuentes": [{"tipo": "biblia", "ref": "Ex 30:13", "cita": "siclo es de veinte"}],
                  "calculo": {"resultado": "≈ 14 g", "pasos": ["1 siclo = 20 óbolos"], "supuestos": ["ninguno"],
                              "fuente": {"tipo": "diccionario", "obra": "Easton", "entrada": "Shekel", "url": "https://example.org/x", "idioma": "en"}},
                  "excluir": ["Gn 23:15"], "solo": None},
        "medio-siclo": {"tipo": "medida", "lema": "medio siclo", "formas": ["medio siclo"], "adulto": "La mitad.", "nino": "La mitad.",
                        "certeza": "texto", "fuentes": [{"tipo": "biblia", "ref": "Ex 30:13", "cita": "medio siclo"}],
                        "calculo": {"resultado": "≈ 7 g", "pasos": ["½ × 14"], "supuestos": ["el del siclo"],
                                    "fuente": {"tipo": "biblia", "ref": "Ex 30:13"}}},
    },
    "terminos-b.json": {
        "enjullo": {"tipo": "palabra", "lema": "enjullo", "formas": ["enjullo"], "adulto": "Madero del telar.", "nino": "Parte del telar.",
                    "certeza": "externa", "fuentes": [{"tipo": "rae", "entrada": "enjullo", "url": "https://dle.rae.es/enjullo"}],
                    "solo": ["1S 17:1-58", "Ez 1:1"]},
    },
}
FIX_PASAJES = {
    "pasajes-Jue.json": {
        "jue-11": {"refs": "Jue 11:29-40", "titulo": "El voto", "dice": [{"ref": "Jue 11:31", "cita": "holocausto"}],
                   "posturas": [{"resumen": "Una.", "fuente": {"tipo": "obra", "obra": "Obra", "autor": "Autor"}}],
                   "nino": None, "certeza": "externa"},
    },
}


def autoprueba(biblia):
    ok = True
    doc, errores, avisos = construir(FIX_TERMINOS, FIX_PASAJES, {"enjullo": {"veredicto": "AJUSTAR", "nota": "x"}}, biblia)
    if doc is None:
        print("FALLA: el fixture válido no pasa:")
        informar(errores, avisos, sys.stdout)
        return 1
    print(f"OK fixture válido: {resumen(doc)}")
    o = doc["ocurrencias"]
    esperado = [t["t"] for t in o.get("Ex 30:13", [])]
    # «medio siclo» (más larga) gana a «siclo» en su primera aparición; luego tres «siclo» sueltos.
    if esperado != ["medio-siclo", "siclo", "siclo", "siclo"]:
        print(f"FALLA: ocurrencias de Ex 30:13 inesperadas: {o.get('Ex 30:13')}")
        ok = False
    if "Gn 23:15" in o or "Gn 23:16" not in o:
        print("FALLA: excluir no quitó Gn 23:15 (o quitó de más)")
        ok = False
    if [k for k, v in o.items() if any(x["t"] == "enjullo" for x in v)] != ["1S 17:7"]:
        print("FALLA: enjullo debería estar solo en 1S 17:7")
        ok = False
    if not any(a.startswith("AJUSTAR: enjullo") for a in avisos) or not any("libro no cargado: Ez" in a for a in avisos):
        print(f"FALLA: faltan avisos de AJUSTAR o de libro no cargado: {avisos}")
        ok = False
    doc2, _, _ = construir(FIX_TERMINOS, FIX_PASAJES, {"enjullo": {"veredicto": "RECHAZAR"}}, biblia)
    if doc2 is None or "enjullo" in doc2["terminos"] or any(x["t"] == "enjullo" for v in doc2["ocurrencias"].values() for x in v):
        print("FALLA: un término RECHAZADO se publica")
        ok = False
    else:
        print("OK lo RECHAZADO no se publica")

    casos = []
    def caso(nombre, campo_esperado, mut):
        t, p = copy.deepcopy(FIX_TERMINOS), copy.deepcopy(FIX_PASAJES)
        mut(t, p)
        casos.append((nombre, t, p, campo_esperado))
    caso("cita no literal", "fuentes[0].cita", lambda t, p: t["terminos-a.json"]["siclo"]["fuentes"][0].update(cita="siclo vale veinte"))
    caso("id repetido entre archivos", "id", lambda t, p: t["terminos-b.json"].update(siclo=copy.deepcopy(t["terminos-a.json"]["medio-siclo"])))
    caso("misma forma en dos términos", "formas", lambda t, p: t["terminos-b.json"]["enjullo"]["formas"].append("Siclos"))
    caso("término sin fuentes", "fuentes", lambda t, p: t["terminos-b.json"]["enjullo"].update(fuentes=[]))
    caso("término sin texto de niño", "nino", lambda t, p: t["terminos-b.json"]["enjullo"].pop("nino"))
    caso("medida sin cálculo", "calculo", lambda t, p: t["terminos-a.json"]["siclo"].pop("calculo"))
    caso("ref inexistente", "fuentes[0].ref", lambda t, p: t["terminos-a.json"]["siclo"]["fuentes"][0].update(ref="Ex 30:99"))
    caso("fuente fuera del esquema", "fuentes[0]", lambda t, p: t["terminos-b.json"]["enjullo"]["fuentes"][0].update(pagina="3"))
    caso("pasaje sin posturas", "posturas", lambda t, p: p["pasajes-Jue.json"]["jue-11"].update(posturas=[]))
    caso("pasaje de un libro no cargado", "refs", lambda t, p: p["pasajes-Jue.json"]["jue-11"].update(refs="Ez 1:1-3"))
    caso("postura sin autor", "posturas[0].fuente.autor", lambda t, p: p["pasajes-Jue.json"]["jue-11"]["posturas"][0]["fuente"].pop("autor"))
    for nombre, t, p, campo in casos:
        d, errs, _ = construir(t, p, None, biblia)
        if d is None and any(e[2] == campo for e in errs):
            print(f"OK falla como se espera ({nombre}): " + "; ".join(f"{e[1]} · {e[2]}: {e[3]}" for e in errs))
        else:
            print(f"FALLA: el caso «{nombre}» debía dar error en {campo!r}; errores: {errs}")
            ok = False
    return 0 if ok else 1


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    biblia = cargar_js(DATOS / "biblia.js")
    if "--autoprueba" in argv:
        return autoprueba(biblia)
    dirr = Path(argv[argv.index("--fuentes") + 1]) if "--fuentes" in argv else FUENTES
    salida = Path(argv[argv.index("--salida") + 1]) if "--salida" in argv else SALIDA
    terminos, pasajes, auditoria, errs = leer_fuentes(dirr)
    if not terminos and not pasajes and not errs:
        print(f"No hay terminos*.json ni pasajes-*.json en {dirr}", file=sys.stderr)
        return 2
    doc, errores, avisos = construir(terminos, pasajes, auditoria, biblia)
    errores = errs + errores
    informar(errores, avisos)
    if errores or doc is None:
        print("No se escribe la salida.", file=sys.stderr)
        return 1
    print("OK: " + resumen(doc))
    if "--sin-salida" in argv:
        return 0
    escribir(salida, "window.BIBLIA_EXPLICACIONES = " + json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + ";\n")
    try:
        nombre = salida.resolve().relative_to(RAIZ)
    except ValueError:
        nombre = salida
    print(f"Escrito {nombre} ({salida.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
