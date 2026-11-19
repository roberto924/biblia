"""Prepara el banco de preguntas para el servidor del desafío (ranking mundial). Sin red.

Uso: python -I herramientas/subir_preguntas.py [--sin-salida] [--salida DIR]

Lee el banco (herramientas/juego/preguntas/*.json) con la misma verificación que herramientas/preguntas.py
(se importa: no se duplican reglas, incluido el banco mínimo) y datos/juego.js, y escribe:
  - datos/desafios.js  (público, va a la app): window.BIBLIA_DESAFIOS = { escala, segundos, sinNino,
    personajes: { [id]: [{ ref, nino? }] } }. SIN ids, texto de preguntas, opciones, respuestas ni citas.
  - supabase/seed.sql  (secreto, en .gitignore): upsert idempotente de `personajes_desafio` (con `hasta_orden`, el
    ordinal del último versículo de su capítulo «listo») y `preguntas` (con `orden`, el ordinal de su `ref`), y borra
    lo que ya no está en el banco. Se carga con la clave de servicio (SQL Editor, psql o `supabase db reset`).
--salida DIR escribe los dos archivos en DIR (para revisar sin tocar los de verdad). --sin-salida solo verifica.

Ids de pregunta (solo en la base; la app nunca los ve): sha256(«personaje + texto de la pregunta»), 16 hex.

Diseño: docs/superpowers/specs/2026-11-18-ranking-mundial-design.md (contrato v2)
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent


def cargar_modulo_preguntas():
    spec = importlib.util.spec_from_file_location("preguntas_banco", AQUI / "preguntas.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


PB = cargar_modulo_preguntas()


def id_pregunta(personaje, texto):
    return hashlib.sha256(f"{personaje}\n{texto}".encode("utf-8")).hexdigest()[:16]


def ordinales(biblia):
    """Ordinal de cada versículo en el orden de la Biblia (Gn 1:1 = 0), y el último de cada capítulo."""
    libros = [l["id"] for l in biblia["libros"]]
    orden, ultimo = {}, {}
    for c in sorted(biblia["capitulos"], key=lambda c: (libros.index(c["libro"]), c["cap"])):
        for v in c["versiculos"]:
            k = len(orden)
            orden[f'{c["libro"]} {c["cap"]}:{v["n"]}'] = k
            ultimo[f'{c["libro"]} {c["cap"]}'] = k
    return orden, ultimo


def lit(s):
    s = str(s)
    if "\x00" in s:
        raise ValueError("texto con NUL")
    return "'" + s.replace("'", "''") + "'"


def jsonb(x):
    return lit(json.dumps(x, ensure_ascii=False)) + "::jsonb"


def booleano(b):
    return "true" if b else "false"


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    salida_js = RAIZ / "datos" / "desafios.js"
    salida_sql = RAIZ / "supabase" / "seed.sql"
    if "--salida" in argv:
        d = Path(argv[argv.index("--salida") + 1])
        d.mkdir(parents=True, exist_ok=True)
        salida_js, salida_sql = d / "desafios.js", d / "seed.sql"
    if not PB.FUENTES.is_dir() or not list(PB.FUENTES.glob("*.json")):
        print(f"No está el banco local ({PB.FUENTES.relative_to(RAIZ)}/*.json).", file=sys.stderr)
        return 1
    biblia = PB.cargar_js(PB.DATOS / "biblia.js")
    juego = PB.cargar_js(PB.DATOS / "juego.js")
    fuentes = {}
    for ruta in sorted(PB.FUENTES.glob("*.json")):
        try:
            fuentes[ruta.stem] = json.loads(ruta.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            print(f"{ruta.name}: JSON inválido: {e}", file=sys.stderr)
            return 1
    personajes, errores, avisos, _informe, sin_nino = PB.construir(fuentes, biblia, juego)
    for a in avisos:
        print("aviso: " + a, file=sys.stderr)
    for e in errores:
        print("ERROR: " + e, file=sys.stderr)
    if errores:
        print(f"{len(errores)} errores (los mismos de herramientas/preguntas.py). No se escribe nada.", file=sys.stderr)
        return 1

    orden, ultimo = ordinales(biblia)
    publico, filas_pj, filas_q, vistos = {}, [], [], set()
    for pid, qs in personajes.items():
        e = juego["personajes"][pid]
        nivel = e.get("nivel") or 0
        n = PB.por_nivel(nivel)
        cap = (e.get("listo") or {}).get("capitulo")
        if not n or cap not in ultimo:
            print(f"ERROR: {pid}: sin desafío posible (nivel {nivel}, capítulo listo {cap!r})", file=sys.stderr)
            return 1
        filas_pj.append((pid, int(nivel), n, ultimo[cap], pid in sin_nino))
        lista = []
        for q in qs:
            qid = id_pregunta(pid, q["p"])
            if qid in vistos:
                print(f"ERROR: id repetido {qid} ({pid}: {q['p']})", file=sys.stderr)
                return 1
            vistos.add(qid)
            libro = PB.REF_RE.match(q["ref"]).group(1)
            nino = q.get("nino") is not False
            lista.append({"ref": q["ref"], **({} if nino else {"nino": False})})
            filas_q.append((qid, pid, libro, q["ref"], orden[q["ref"]], q["cita"], q["p"], q["o"], q["c"], nino))
        publico[pid] = lista

    doc = {"escala": PB.ESCALA, "segundos": PB.SEGUNDOS, "sinNino": sin_nino, "personajes": publico}
    js = "window.BIBLIA_DESAFIOS = " + json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + ";\n"
    # Defensa: ningún id, texto de pregunta, opción ni cita puede acabar en el archivo público.
    for (qid, _pid, _libro, _ref, _ord, cita, p, ops, _c, _nino) in filas_q:
        for t in [qid, cita, p, *ops]:
            if len(t) >= 8 and t in js:
                print(f"ERROR: datos/desafios.js contendría «{t}»", file=sys.stderr)
                return 1

    sql = [
        "-- GENERADO por herramientas/subir_preguntas.py. NO va al repositorio: contiene las respuestas.",
        "-- Carga idempotente del banco del desafío. Ejecutar con la clave de servicio (SQL Editor o psql).",
        "begin;",
        "",
        "insert into public.personajes_desafio (personaje, nivel, n_preguntas, hasta_orden, sin_nino) values",
        ",\n".join(f"  ({lit(p)}, {nv}, {n}, {h}, {booleano(sn)})" for p, nv, n, h, sn in filas_pj),
        "on conflict (personaje) do update set nivel = excluded.nivel, n_preguntas = excluded.n_preguntas,",
        "  hasta_orden = excluded.hasta_orden, sin_nino = excluded.sin_nino;",
        "",
        "insert into public.preguntas (id, personaje, libro, ref, orden, cita, pregunta, opciones, correcta, nino) values",
        ",\n".join(f"  ({lit(i)}, {lit(p)}, {lit(lb)}, {lit(r)}, {o_}, {lit(ci)}, {lit(pr)}, {jsonb(o)}, {c}, {booleano(ni)})"
                   for i, p, lb, r, o_, ci, pr, o, c, ni in filas_q),
        "on conflict (id) do update set personaje = excluded.personaje, libro = excluded.libro, ref = excluded.ref,",
        "  orden = excluded.orden, cita = excluded.cita, pregunta = excluded.pregunta, opciones = excluded.opciones,",
        "  correcta = excluded.correcta, nino = excluded.nino;",
        "",
        "-- Lo que ya no está en el banco local.",
        "delete from public.preguntas where id not in (" + ", ".join(lit(x[0]) for x in filas_q) + ");",
        "delete from public.personajes_desafio where personaje not in (" + ", ".join(lit(x[0]) for x in filas_pj) + ");",
        "",
        "commit;",
        "",
    ]
    if "--sin-salida" in argv:
        print(f"OK: {len(filas_pj)} personajes, {len(filas_q)} preguntas (no se escribe nada)")
        return 0
    salida_js.write_text(js, encoding="utf-8")
    salida_sql.parent.mkdir(exist_ok=True)
    salida_sql.write_text("\n".join(sql), encoding="utf-8")
    print(f"OK: {len(filas_pj)} personajes, {len(filas_q)} preguntas")
    print(f"Escrito {salida_js} ({salida_js.stat().st_size} bytes, público, sin ids, preguntas ni respuestas)")
    print(f"Escrito {salida_sql} ({salida_sql.stat().st_size} bytes, secreto: fuera de git)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
