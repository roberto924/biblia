"""Genera los retratos de la colección (recursos/retratos/*.webp) y su índice datos/retratos.js
(window.BIBLIA_RETRATOS) a partir de las hojas de personaje de guiones/imagenes/personajes.

Solo entran las hojas **aprobadas** en el Estudio (guiones/registro/revision.json) cuyo archivo no cambió desde la
aprobación (sha256 igual): cada imagen se revisa contra su ficha antes de usarse (CLAUDE.md). Todas son
«Ilustración moderna (generada con IA)», Estilo v1.

Por hoja aprobada:
  <id>-hoja.webp     la hoja completa (frente, tres cuartos y cuerpo entero), 1200 px de ancho, para la ficha.
  <id>-retrato.webp  el busto de frente (primer tercio de la hoja), 3:4, para la carta. Solo en hojas de una
                     persona: las de grupo (los hermanos, la familia de Noé) se ven en la ficha, no en la carta.

Sin red. Regenerar: python -I herramientas/retratos.py   (--sin-salida: solo lista lo que haría)
"""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
HOJAS = RAIZ / "guiones" / "imagenes" / "personajes"
FICHAS = RAIZ / "guiones" / "fuentes" / "personajes"
REVISION = RAIZ / "guiones" / "registro" / "revision.json"
DESTINO = RAIZ / "recursos" / "retratos"
SALIDA = RAIZ / "datos" / "retratos.js"
ROTULO = "Ilustración moderna (generada con IA)"


def sha256(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    rev = json.loads(REVISION.read_text(encoding="utf-8"))
    personas, hojas, omitidas = {}, [], []
    for clave, r in sorted(rev.items()):
        if not clave.startswith("personajes/") or r.get("estado") != "aprobada":
            continue
        fid = clave.split("/", 1)[1]
        png, ficha = HOJAS / f"{fid}.png", FICHAS / f"{fid}.json"
        if not png.exists() or not ficha.exists():
            omitidas.append(f"{fid}: falta la imagen o la ficha")
            continue
        if r.get("archivo_sha256") and sha256(png) != r["archivo_sha256"]:
            omitidas.append(f"{fid}: la imagen cambió después de aprobarse (hay que revisarla de nuevo)")
            continue
        f = json.loads(ficha.read_text(encoding="utf-8"))
        ids = [p for p in f.get("personas") or [] if isinstance(p, str)]
        if not ids:
            omitidas.append(f"{fid}: la ficha no nombra personas de la colección")
            continue
        grupo = len(ids) > 1
        entrada = {"ficha": fid, "nombre": f.get("nombre") or fid, "pasaje": (f.get("pasajes") or [None])[0],
                   "hoja": f"recursos/retratos/{fid}-hoja.webp", "grupo": grupo, "fecha": (r.get("fecha") or "")[:10]}
        if not grupo:
            entrada["retrato"] = f"recursos/retratos/{fid}-retrato.webp"
        for pid in ids:
            personas.setdefault(pid, []).append(entrada)
        hojas.append((png, entrada))
    for o in omitidas:
        print("omitida: " + o)
    print(f"{len(hojas)} hojas aprobadas · {len(personas)} personas con imagen")
    if "--sin-salida" in argv:
        return 0
    DESTINO.mkdir(parents=True, exist_ok=True)
    for png, e in hojas:
        im = Image.open(png).convert("RGB")
        w, h = im.size
        hoja = im.copy()
        hoja.thumbnail((1200, 1200))
        hoja.save(RAIZ / e["hoja"], "WEBP", quality=78, method=6)
        if "retrato" in e:
            # Busto de frente: primer tercio (36 % del ancho), recortado a 3:4 desde arriba.
            cw = round(w * 0.36)
            ch = min(h, round(cw * 4 / 3))
            busto = im.crop((0, 0, cw, ch)).resize((480, 640), Image.LANCZOS)
            busto.save(RAIZ / e["retrato"], "WEBP", quality=80, method=6)
    for v in personas.values():
        v.sort(key=lambda e: (e["grupo"], e["pasaje"] or ""))
    doc = {"rotulo": ROTULO, "estilo": "Estilo v1 · animación 2D de largometraje", "personas": personas}
    SALIDA.write_text("window.BIBLIA_RETRATOS = " + json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + ";\n",
                      encoding="utf-8")
    peso = sum(p.stat().st_size for p in DESTINO.glob("*.webp"))
    print(f"Escrito datos/retratos.js y {len(list(DESTINO.glob('*.webp')))} webp ({peso // 1024} KB en total)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
