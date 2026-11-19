"""Genera datos/preguntas.js (window.BIBLIA_PREGUNTAS): las preguntas de selección (A–D) con que se desbloquea
cada personaje de la colección, verificadas contra datos/biblia.js (texto RV1909) y datos/juego.js.

Sin red. Regenerar: python -I herramientas/preguntas.py
Opciones:
  --sin-salida    solo verifica, no escribe nada
  --informe       lista, por personaje, cuántas preguntas hay y cuántas pide su nivel

Fuentes: herramientas/juego/preguntas/<Libro>.json
  { "libro": "Gn",
    "personajes": { "<id de persona>": [
      { "pregunta": "¿…?", "opciones": ["…", "…", "…", "…"], "correcta": 0,
        "ref": "Gn 4:2", "cita": "texto literal del versículo", "nino": true } ] } }

Reglas (diseño: docs/superpowers/specs/2026-11-18-desafio-coleccion-design.md):
- Cada respuesta correcta sale del texto: `cita` literal de `ref` (RV1909). Las opciones falsas son plausibles, pero
  el texto las descarta; nunca otra respuesta también verdadera según el texto.
- Una pregunta se puede hacer solo cuando ya se leyó el pasaje de su `ref` (lo filtra la app).
- `nino: false` = la pregunta toca algo no apto para niños (cruento, o un tramo «alto» de datos/contenido.js, o el
  tema aunque el versículo no esté marcado): el perfil niño no la recibe.
- `sin_desafio_nino` (lista de ids, en la raíz del archivo): personajes cuya historia no es apta; el perfil niño no
  tiene su desafío (decisión del usuario, 2026-11-18: Canaán) y los obtiene leyendo, como antes.
- Cuántas preguntas pide el desafío según el nivel del personaje: ESCALA. Las que caen hasta el capítulo en que el
  personaje queda listo deben ser al menos el doble de un desafío (MINIMO_BANCO), en adulto y en niño.
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"
FUENTES = Path(__file__).resolve().parent / "juego" / "preguntas"
SALIDA = DATOS / "preguntas.js"

# Nivel mínimo → preguntas por desafío (todas deben ser correctas). Segundos por pregunta según el perfil.
ESCALA = [[1, 3], [3, 5], [5, 7], [7, 10], [9, 12]]
SEGUNDOS = {"adulto": 15, "nino": 25}
MINIMO_BANCO = 2  # banco ≥ 2 × preguntas del set, en adulto y en niño
REF_RE = re.compile(r"^([1-3]?[A-Za-z]+) (\d+):(\d+)$")


def cargar_js(ruta):
    s = ruta.read_text(encoding="utf-8")
    return json.loads(s[s.index("{"):s.rindex("}") + 1])


def por_nivel(nivel):
    n = 0
    for minimo, cuantas in ESCALA:
        if (nivel or 0) >= minimo:
            n = cuantas
    return n


def construir(fuentes, biblia, juego):
    libros = [l["id"] for l in biblia["libros"]]
    V, orden = {}, {}
    for c in sorted(biblia["capitulos"], key=lambda c: (libros.index(c["libro"]), c["cap"])):
        for v in c["versiculos"]:
            ref = f'{c["libro"]} {c["cap"]}:{v["n"]}'
            orden[ref] = len(orden)
            V[ref] = v["texto"]
    errores, avisos, salida, informe, sin_nino = [], [], {}, [], []

    def err(ruta, msg):
        errores.append(f"{ruta}: {msg}")

    for nombre, f in sorted(fuentes.items()):
        if not isinstance(f, dict) or not isinstance(f.get("personajes"), dict):
            err(nombre, "falta el objeto «personajes»")
            continue
        sn = f.get("sin_desafio_nino", [])
        if not isinstance(sn, list) or any(x not in f["personajes"] for x in sn):
            err(nombre, "«sin_desafio_nino» debe listar ids de personajes del archivo")
            sn = []
        sin_nino += sn
        for pid, lista in f["personajes"].items():
            ruta = f"{nombre} · {pid}"
            e = juego["personajes"].get(pid)
            if not e:
                err(ruta, "no es un personaje de datos/juego.js")
                continue
            if e.get("npc"):
                err(ruta, "es NPC: los NPC entran sin desafío")
                continue
            if not isinstance(lista, list) or not lista:
                err(ruta, "lista de preguntas vacía")
                continue
            vistas, buenas = set(), []
            for i, q in enumerate(lista):
                r = f"{ruta} · #{i + 1}"
                if not isinstance(q, dict):
                    err(r, "no es un objeto")
                    continue
                p = (q.get("pregunta") or "").strip()
                if not p.startswith("¿") or not p.endswith("?"):
                    err(r, "la pregunta debe ir entre ¿ y ?")
                if p.lower() in vistas:
                    err(r, "pregunta repetida")
                vistas.add(p.lower())
                ops = q.get("opciones")
                if not (isinstance(ops, list) and len(ops) == 4 and all(isinstance(o, str) and o.strip() for o in ops)):
                    err(r, "debe tener exactamente 4 opciones no vacías")
                    continue
                if len({o.strip().lower() for o in ops}) != 4:
                    err(r, "opciones repetidas")
                if q.get("correcta") not in (0, 1, 2, 3):
                    err(r, "«correcta» debe ser 0, 1, 2 o 3")
                ref, cita = q.get("ref"), q.get("cita")
                if not (isinstance(ref, str) and REF_RE.match(ref) and ref in V):
                    err(r, f"referencia inexistente {ref!r}")
                    continue
                if not cita or cita not in V[ref]:
                    err(r, f"la cita {cita!r} no es literal de {ref}")
                    continue
                if "nino" in q and not isinstance(q["nino"], bool):
                    err(r, "«nino» debe ser true o false")
                extra = set(q) - {"pregunta", "opciones", "correcta", "ref", "cita", "nino", "nota"}
                if extra:
                    err(r, f"campos desconocidos: {sorted(extra)}")
                buenas.append({"p": p, "o": [o.strip() for o in ops], "c": q["correcta"], "ref": ref, "cita": cita,
                               **({"nino": False} if q.get("nino") is False else {}),
                               **({"nota": q["nota"]} if q.get("nota") else {})})
            # Alcance para el primer desafío: preguntas hasta el final del capítulo en que queda listo.
            cap = (e.get("listo") or {}).get("capitulo")
            necesita = por_nivel(e.get("nivel"))
            if cap:
                libro, n = cap.rsplit(" ", 1)
                ult = max((orden[x] for x in orden if x.startswith(f"{libro} {n}:")), default=None)
                hasta = [q for q in buenas if ult is not None and orden[q["ref"]] <= ult]
                ninos = [q for q in hasta if q.get("nino") is not False]
                # Antitrampas (revisión de seguridad 2026-11-18): el banco debe doblar el set, para que fallar un día
                # no deje ver todas las preguntas del siguiente.
                if len(hasta) < MINIMO_BANCO * necesita:
                    err(ruta, f"nivel {e.get('nivel')} pide {necesita} preguntas por set y un banco de {MINIMO_BANCO * necesita}; hasta {cap} solo hay {len(hasta)}")
                elif len(ninos) < MINIMO_BANCO * necesita and pid not in sn:
                    err(ruta, f"perfil niño: banco de {MINIMO_BANCO * necesita} (set de {necesita}); hasta {cap} solo hay {len(ninos)} aptas")
            informe.append(f"{pid:24} nivel {e.get('nivel')!s:>2} · pide {necesita:2} · hay {len(buenas):2}")
            salida[pid] = buenas
    return salida, errores, avisos, informe, sorted(set(sin_nino))


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    biblia = cargar_js(DATOS / "biblia.js")
    juego = cargar_js(DATOS / "juego.js")
    fuentes = {}
    for ruta in sorted(FUENTES.glob("*.json")):
        try:
            fuentes[ruta.stem] = json.loads(ruta.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            print(f"{ruta.name}: JSON inválido: {e}", file=sys.stderr)
            return 1
    personajes, errores, avisos, informe, sin_nino = construir(fuentes, biblia, juego)
    if "--informe" in argv:
        print("\n".join(informe))
    for a in avisos:
        print("aviso: " + a, file=sys.stderr)
    for e in errores:
        print("ERROR: " + e, file=sys.stderr)
    if errores:
        print(f"{len(errores)} errores. No se escribe la salida.", file=sys.stderr)
        return 1
    total = sum(len(x) for x in personajes.values())
    print(f"OK: {len(personajes)} personajes, {total} preguntas")
    if "--sin-salida" in argv:
        return 0
    doc = {"escala": ESCALA, "segundos": SEGUNDOS, "sinNino": sin_nino, "personajes": personajes}
    SALIDA.write_text("window.BIBLIA_PREGUNTAS = " + json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + ";\n",
                      encoding="utf-8")
    print(f"Escrito datos/preguntas.js ({SALIDA.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
