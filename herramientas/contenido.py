"""Valida herramientas/contenido.json y genera datos/contenido.js. Uso: python -I herramientas/contenido.py"""
import json, re, sys, os, datetime
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATS = {"sexual", "violencia", "crueldad"}
NIVELES = {"medio": 1, "alto": 2}
LIBROS = ["Gn", "Ex", "Lv", "Nm", "Dt", "Jos", "Jue", "Rut", "1S"]

def fallo(m):
    print("ERROR:", m); sys.exit(1)

s = open(os.path.join(RAIZ, "datos", "biblia.js"), encoding="utf-8").read()
datos = json.loads(s[s.index("{"):s.rindex("}") + 1])
vers = {}
for c in datos["capitulos"]:
    vers[(c["libro"], c["cap"])] = {v["n"] for v in c["versiculos"]}
orden = []  # posiciones ordenadas
for c in datos["capitulos"]:
    for n in sorted(vers[(c["libro"], c["cap"])]):
        orden.append((c["libro"], c["cap"], n))
pos = {t: i for i, t in enumerate(orden)}

def ref(r, i):
    m = re.fullmatch(r"(\w+) (\d+):(\d+)", r or "")
    if not m: fallo(f"marca {i}: referencia mal formada {r!r}")
    t = (m[1], int(m[2]), int(m[3]))
    if t not in pos: fallo(f"marca {i}: no existe {r} en biblia.js")
    return pos[t]

cont = json.load(open(os.path.join(RAIZ, "herramientas", "contenido.json"), encoding="utf-8"))
if not str(cont.get("criterio", "")).strip(): fallo("falta criterio")
marcas = cont.get("marcas")
if not isinstance(marcas, list) or not marcas: fallo("marcas vacío")
rangos = []
for i, m in enumerate(marcas):
    for k in ("desde", "hasta", "categoria", "nivel", "motivo"):
        if not str(m.get(k, "")).strip(): fallo(f"marca {i}: falta {k}")
    a, b = ref(m["desde"], i), ref(m["hasta"], i)
    if a > b: fallo(f"marca {i}: desde > hasta")
    if m["categoria"] not in CATS: fallo(f"marca {i}: categoría inválida")
    if m["nivel"] not in NIVELES: fallo(f"marca {i}: nivel inválido")
    if i and a < rangos[-1][0]: fallo(f"marca {i}: fuera de orden bíblico")
    rangos.append((a, b, m["categoria"], m["nivel"], i))
for x in range(len(rangos)):
    for y in range(x + 1, len(rangos)):
        a1, b1, c1, n1, i1 = rangos[x]; a2, b2, c2, n2, i2 = rangos[y]
        if a1 <= b2 and a2 <= b1 and (c1 != c2 or n1 != n2):
            fallo(f"marcas {i1} y {i2} se solapan con categoría/nivel distintos")
salida = {"generado": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
          "origen": "clasificación editorial del proyecto, no del texto bíblico",
          "criterio": cont["criterio"], "marcas": marcas}
with open(os.path.join(RAIZ, "datos", "contenido.js"), "w", encoding="utf-8") as f:
    f.write("window.BIBLIA_CONTENIDO = " + json.dumps(salida, ensure_ascii=False, indent=1) + ";\n")
print(f"OK: {len(marcas)} marcas -> datos/contenido.js")
