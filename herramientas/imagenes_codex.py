"""Genera en lote las imágenes de los guiones con Codex (su herramienta de imágenes integrada).

Uso (desde la raíz del repositorio):
    python -I herramientas/imagenes_codex.py            # lista lo pendiente, no genera nada
    python -I herramientas/imagenes_codex.py --generar 10

Reglas («sin gasto adicional», decisión del usuario 2026-11-16):
- Solo con la sesión de ChatGPT (gasta el límite semanal del plan). Si hay OPENAI_API_KEY o CODEX_API_KEY en el
  entorno, no arranca: con clave se cobraría a precio de API. Además se quitan del entorno del proceso hijo.
- La cuenta no tiene créditos ni recarga automática: al llegar al límite, Codex se detiene y el lote se para.
- Se para en el primer fallo; nunca reintenta en bucle.

Orden: láminas patrón → hojas de personaje → hojas de escenario → imágenes iniciales de cada toma (solo cuando ya
existen las hojas que la toma necesita). Lo ya generado no se repite. Cada generación queda en
guiones/registro/imagenes.jsonl.
"""
import argparse, datetime, hashlib, json, os, pathlib, re, shutil, subprocess, sys, time

RAIZ = pathlib.Path(__file__).resolve().parent.parent
G = RAIZ / "guiones"
F = G / "fuentes"
IMG = G / "imagenes"
REGISTRO = G / "registro" / "imagenes.jsonl"
CODEX = shutil.which("codex") or "codex"  # en Windows es codex.cmd


def leer(p):
    return json.loads(p.read_text(encoding="utf-8"))


def png(p):
    """(ancho, alto) si p es un PNG; si no, None."""
    try:
        b = p.read_bytes()[:24]
    except OSError:
        return None
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big")


def lamina(nombre):
    """Lámina patrón aprobada; la 2 provisional de Codex vale mientras no haya otra."""
    p = IMG / "estilo" / nombre
    if p.exists():
        return p
    alt = p.with_name(p.stem + "-codex.png")
    return alt if alt.exists() else None


def prompt_imagen(E, prompt_en, negativo_en=""):
    return " ".join(x for x in (E["base_imagen_en"], prompt_en, E["negativo_en"], negativo_en) if x)


def instrucciones():
    md = (G / "estilo.md").read_text(encoding="utf-8")
    sec = md[md.index("## Instrucciones del proyecto de ChatGPT"):]
    return re.search(r"```text\n(.*?)```", sec, re.S).group(1).strip()


def pendientes(E):
    """Lista ordenada de trabajos: dict(id, destino, prompt, refs, bloqueo)."""
    T = []
    lams = E["laminas_patron"]
    for i, L in enumerate(lams):
        refs = [lamina(x["archivo"]) for x in lams[:i]]
        T.append(dict(id=f"estilo/{L['archivo'][:-4]}", destino=lamina(L["archivo"]) or IMG / "estilo" / L["archivo"],
                      hoja=False,
                      prompt=prompt_imagen(E, L["prompt_en"]), refs=refs,
                      bloqueo=None if all(refs) else "faltan láminas anteriores"))
    estilo = [lamina(x["archivo"]) for x in lams]
    est_ok = all(estilo)
    for carpeta in ("personajes", "escenarios"):
        for f in sorted((F / carpeta).glob("*.json")):
            x = leer(f)
            h = x["hoja_referencia"]
            T.append(dict(id=f"{carpeta}/{x['id']}", destino=IMG / carpeta / f"{x['id']}.png", hoja=True,
                          prompt=prompt_imagen(E, h["prompt_en"], h.get("negativo_en", "")), refs=estilo,
                          bloqueo=None if est_ok else "faltan láminas patrón"))
    for f in sorted(F.glob("*/*.json")):
        if f.parent.name in ("personajes", "escenarios"):
            continue
        g = leer(f)
        for es in g["escenas"]:
            for t in es["tomas"]:
                hojas = [IMG / "personajes" / f"{p}.png" for p in t.get("personajes", [])]
                hojas.append(IMG / "escenarios" / f"{t['escenario']}.png")
                falta = [h.stem for h in hojas if not h.exists()]
                T.append(dict(id=f"{g['libro']}/{g['id']}-{t['id']}", hoja=False,
                              destino=IMG / g["libro"] / f"{g['id']}-{t['id']}.png",
                              prompt=prompt_imagen(E, t["imagen"]["prompt_en"], t["imagen"].get("negativo_en", "")),
                              refs=estilo + hojas,
                              bloqueo=None if est_ok and not falta else "faltan hojas: " + ", ".join(falta or ["estilo"])))
    return T


def pedido(t, instr):
    rel = lambda p: p.relative_to(RAIZ).as_posix()
    refs = "\n".join(f"- {rel(r)}" for r in t["refs"]) or "- (none)"
    formato = ("a character or place reference sheet on a plain light grey background, landscape 16:9"
               if t["hoja"] else "landscape 16:9, the widest landscape size available")
    return f"""Biblia · {t['id']}

Task: generate exactly ONE image with your built-in image generation tool (image_gen). Do not use the CLI/API fallback script, do not use any API key, do not write code to make the image, and do not retry more than once.

Attached images, in this order (pass them all to the image tool as references):
{refs}
The style reference panels (guiones/imagenes/estilo/) fix only the line work, cel shading and palette: do not copy their scenes. Character and place sheets fix identity and architecture.

Standing art-direction instructions:
<<<
{instr}
>>>

Image prompt (use it verbatim; {formato}, high quality):
<<<
{t['prompt']}
>>>

Save the result as a PNG at exactly: {rel(t['destino'])}
Do not create, modify or delete any other file in the repository. Reply with the saved path and pixel size, or with the exact error if the image could not be made."""


def entorno_seguro():
    for k in ("OPENAI_API_KEY", "CODEX_API_KEY"):
        if os.environ.get(k):
            sys.exit(f"Alto: {k} está definida. Con clave de API se cobraría aparte; quítala y vuelve a intentar.")
    r = subprocess.run([CODEX, "login", "status"], capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    if "ChatGPT" not in (r.stdout + r.stderr):
        sys.exit("Alto: Codex no tiene sesión de ChatGPT («codex login status»).")
    env = dict(os.environ)
    env.pop("OPENAI_API_KEY", None)
    env.pop("CODEX_API_KEY", None)
    return env


def generar(t, instr, env, tmp):
    t["destino"].parent.mkdir(parents=True, exist_ok=True)
    texto = pedido(t, instr)
    salida = tmp / (t["id"].replace("/", "_") + ".txt")
    cmd = [CODEX, "exec", "-C", str(RAIZ), "-s", "workspace-write"]
    if t["refs"]:
        cmd += ["-i"] + [str(r) for r in t["refs"]]
    cmd += ["-o", str(salida), "-"]
    t0 = time.time()
    r = subprocess.run(cmd, input=texto, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=env, timeout=900)
    seg = round(time.time() - t0)
    dim = png(t["destino"])
    log = (r.stdout or "") + (r.stderr or "")
    limite = bool(re.search(r"usage.?limit|rate.?limit|quota", log, re.I))
    fila = dict(fecha=datetime.datetime.now().isoformat(timespec="seconds"), id=t["id"],
                archivo=t["destino"].relative_to(RAIZ).as_posix(), ok=bool(dim) and r.returncode == 0,
                ancho=dim and dim[0], alto=dim and dim[1], segundos=seg, codex_salida=r.returncode,
                limite=limite, refs=[p.relative_to(RAIZ).as_posix() for p in t["refs"]],
                prompt_sha256=hashlib.sha256(texto.encode()).hexdigest()[:16], herramienta="codex image_gen")
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRO.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(fila, ensure_ascii=False) + "\n")
    if not fila["ok"]:
        (tmp / (t["id"].replace("/", "_") + ".log")).write_text(log, encoding="utf-8")
    return fila


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generar", type=int, default=0, help="cuántas imágenes generar (0 = solo listar)")
    ap.add_argument("--solo", help="prefijo de id (estilo/, personajes/, escenarios/, Gn/…)")
    ap.add_argument("--tmp", default=str(RAIZ / "guiones" / "registro" / "codex"))
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    E = leer(F / "estilo.json")
    T = [t for t in pendientes(E) if not t["destino"].exists() and not (a.solo and not t["id"].startswith(a.solo))]
    listas = [t for t in T if not t["bloqueo"]]
    print(f"Pendientes: {len(T)} · listas para generar: {len(listas)}")
    for t in T:
        print(f"  {'·' if not t['bloqueo'] else 'x'} {t['id']}" + (f"  ({t['bloqueo']})" if t["bloqueo"] else ""))
    if not a.generar:
        return
    env = entorno_seguro()
    instr = instrucciones()
    tmp = pathlib.Path(a.tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    hechas = 0
    while hechas < a.generar:
        # se recalcula en cada vuelta: una hoja recién hecha desbloquea tomas
        listas = [t for t in pendientes(E) if not t["destino"].exists() and not t["bloqueo"]
                  and not (a.solo and not t["id"].startswith(a.solo))]
        if not listas:
            print("No queda nada listo para generar.")
            break
        t = listas[0]
        print(f"[{hechas + 1}/{a.generar}] {t['id']} …", flush=True)
        fila = generar(t, instr, env, tmp)
        print(f"    {'ok' if fila['ok'] else 'FALLO'} · {fila['segundos']} s · {fila['ancho']}×{fila['alto']}", flush=True)
        if not fila["ok"]:
            print("Lote detenido en el primer fallo" + (" (parece el límite de uso)." if fila["limite"] else "."))
            sys.exit(1)
        hechas += 1
    print(f"Hechas: {hechas}. Registro: {REGISTRO.relative_to(RAIZ).as_posix()}")


if __name__ == "__main__":
    main()
