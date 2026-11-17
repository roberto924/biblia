"""Imágenes de los guiones: qué falta, cómo se pide y el lote, delegando la ejecución en capa-ia.

Uso (desde la raíz del repositorio):
    python -I herramientas/imagenes.py                      # lista lo pendiente, no genera nada
    python -I herramientas/imagenes.py --generar 10 [--solo Gn/]
    python -I herramientas/imagenes.py --autoprueba         # con un capa-ia falso: no genera ni gasta

Toda generación pasa por capa-ia (`app: "biblia"`, `capa-ia.json` en la raíz): ella elige el proveedor, cuida el
gasto («sin gasto adicional»: sin claves de API ni créditos, tope semanal) y anota cada trabajo en su registro.
Aquí queda lo propio de la Biblia: orden láminas → hojas → tomas, bloqueos y el texto del pedido.

Se manda un trabajo a la vez, se recalculan los pendientes en cada vuelta (una hoja recién hecha desbloquea tomas)
y se para en el primer resultado que no sea `ok`; nunca se reintenta. Códigos de salida: 0 bien · 1 fallo ·
2 esperando cuota · 3 bloqueado por coste.

El Estudio (`python -I herramientas/estudio.py`) usa este mismo módulo.
"""
import argparse, hashlib, json, os, pathlib, re, shutil, sys, tempfile, zlib

RAIZ = G = F = IMG = REGISTRO_VIEJO = None


def fijar_raiz(raiz):
    """Apunta el módulo a otra raíz de repositorio (las autopruebas usan una copia temporal)."""
    global RAIZ, G, F, IMG, REGISTRO_VIEJO
    RAIZ = pathlib.Path(raiz).resolve()
    G = RAIZ / "guiones"
    F = G / "fuentes"
    IMG = G / "imagenes"
    REGISTRO_VIEJO = G / "registro" / "imagenes.jsonl"


fijar_raiz(pathlib.Path(__file__).resolve().parent.parent)

APP = "biblia"
ORIGEN_VIEJO = "codex directo (2026-11-16)"
NO_REPETIR = ("Use the attached style reference panels only for line work, cel shading and palette: do not reuse "
              "their composition, objects, trees, buildings or layout.")


def capa():
    """El cliente Python de capa-ia (o el sustituto que una prueba haya puesto en sys.modules)."""
    if "capa_ia" not in sys.modules:
        sys.path.insert(0, os.environ.get("CAPA_IA_REPO", r"C:\PROYECTOS IA\capa-ia") + r"\clientes\python")
    import capa_ia
    return capa_ia


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
    """Lista ordenada de trabajos: dict(id, destino, hoja, prompt, refs, bloqueo). No filtra por existencia."""
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


# --------------------------------------------------------------------------- el pedido
def texto_pedido(t, instr):
    """Instrucciones de dirección de arte + NO_REPETIR + el prompt de `t`. Lo propio de Codex lo pone capa-ia."""
    formato = ("a character or place reference sheet on a plain light grey background, landscape 16:9"
               if t["hoja"] else "landscape 16:9, the widest landscape size available")
    hojas = ("" if t["hoja"] or t["id"].startswith("estilo/") else
             "\nThe attached character and place reference sheets fix identity, dress and architecture.")
    return f"""Standing art-direction instructions:
<<<
{instr}
>>>

{NO_REPETIR}{hojas}

Image prompt (use it verbatim; {formato}, high quality):
<<<
{t['prompt']}
>>>"""


def trabajo_de(t, instr, sobrescribir=False):
    """El trabajo de capa-ia para `t` (rutas absolutas; la config de la app sale de `ruta_app`)."""
    return {"app": APP, "tipo": "imagen", "prompt": texto_pedido(t, instr),
            "adjuntos": [str(r) for r in t["refs"]], "salida": str(t["destino"]), "etiqueta": t["id"],
            "ruta_app": str(RAIZ), "sobrescribir": sobrescribir}


def pedido_v1(t, instr):
    """Copia literal del `pedido` de imagenes_codex.py (16-nov): solo para reconstruir el historial viejo."""
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


def historial_viejo():
    """Las filas de guiones/registro/imagenes.jsonl (Codex directo, 16-nov) con la forma del registro de capa-ia.

    El prompt se reconstruye con `pedido_v1` sobre las fuentes actuales y las referencias y el archivo de la fila;
    solo se da si su sha256[:16] coincide con el guardado. No se escribe nada en el registro de capa-ia.
    """
    if not REGISTRO_VIEJO.exists():
        return []
    try:
        E = leer(F / "estilo.json")
        T = {t["id"]: t for t in pendientes(E)}
        instr = instrucciones()
    except (OSError, ValueError, KeyError, AttributeError):
        T, instr = {}, None
    filas = []
    for linea in REGISTRO_VIEJO.read_text(encoding="utf-8").splitlines():
        if not linea.strip():
            continue
        try:
            f = json.loads(linea)
        except ValueError:
            continue
        prompt = None
        t = T.get(f.get("id"))
        if t and instr is not None:
            t = dict(t, refs=[RAIZ / r for r in f.get("refs", [])], destino=RAIZ / f.get("archivo", ""))
            try:
                texto = pedido_v1(t, instr)
            except ValueError:
                texto = None
            if texto and hashlib.sha256(texto.encode()).hexdigest()[:16] == f.get("prompt_sha256"):
                prompt = texto
        filas.append({"fecha": f.get("fecha"), "id": None, "app": APP, "etiqueta": f.get("id"), "tipo": "imagen",
                      "proveedor": "codex", "modelo": None, "prompt": prompt,
                      "prompt_nota": None if prompt else "no se pudo reconstruir",
                      "adjuntos": f.get("refs", []), "salida": f.get("archivo"),
                      "estado": "ok" if f.get("ok") else "fallo", "motivo": None, "segundos": f.get("segundos"),
                      "reinicio_en": None, "cuota_antes": None, "cuota_despues": None, "costo_estimado": None,
                      "ancho": f.get("ancho"), "alto": f.get("alto"), "origen": ORIGEN_VIEJO})
    return filas


# --------------------------------------------------------------------------- el lote
def _resultado(ejecutar, trabajo):
    """Resultado de capa-ia; `CapaIAError` (fallo, bloqueado por coste, Node ausente…) se vuelve Resultado."""
    try:
        r = ejecutar(trabajo)
    except Exception as e:  # noqa: BLE001 — cualquier error para el lote, nunca se reintenta
        r = getattr(e, "resultado", None)
        if not isinstance(r, dict):
            r = {"error": str(e)}
        r = dict(r)
        if r.get("estado") not in ("ok", "fallo", "esperando_cuota", "bloqueado_coste", "cancelado"):
            r["estado"] = "bloqueado_coste" if getattr(e, "codigo", None) == 3 else "fallo"
        r.setdefault("motivo", r.get("error") or str(e))
    if not isinstance(r, dict):
        r = {"estado": "fallo", "motivo": f"respuesta inesperada de capa-ia: {r!r}"}
    r.setdefault("etiqueta", trabajo["etiqueta"])
    return r


def _saltado(id_, motivo):
    return {"estado": "saltado", "etiqueta": id_, "motivo": motivo}


def generar_lote(n, solo=None, ejecutar=None, al_progreso=None, detener=lambda: False, ids=None):
    """Genera hasta `n` imágenes de una en una vía capa-ia y devuelve los Resultados.

    Sin `ids`: en cada vuelta se recalculan los pendientes (no existen, sin bloqueo, con el prefijo `solo`) y se
    manda el primero. Con `ids`: esos ids exactos en ese orden; los que ya existen, están bloqueados o no se
    conocen se saltan con su motivo (`estado: "saltado"`). En cada vuelta se releen las fuentes, así cada imagen usa
    el prompt vigente al empezar. Para en el primer Resultado que no sea `ok` o cuando `detener()` da True.
    """
    ejecutar = ejecutar or capa().ejecutar
    resultados, hechas = [], 0
    cola = list(ids) if ids is not None else None
    while hechas < n and not detener():
        E = leer(F / "estilo.json")
        if cola is not None:
            if not cola:
                break
            id_ = cola.pop(0)
            t = next((x for x in pendientes(E) if x["id"] == id_), None)
            if t is None or t["destino"].exists() or t["bloqueo"]:
                motivo = "id desconocido" if t is None else ("ya existe" if t["destino"].exists() else t["bloqueo"])
                resultados.append(_saltado(id_, motivo))
                if al_progreso:
                    al_progreso(t or {"id": id_}, resultados[-1])
                continue
        else:
            listas = [x for x in pendientes(E) if not x["destino"].exists() and not x["bloqueo"]
                      and not (solo and not x["id"].startswith(solo))]
            if not listas:
                break
            t = listas[0]
        t["destino"].parent.mkdir(parents=True, exist_ok=True)
        r = _resultado(ejecutar, trabajo_de(t, instrucciones()))
        resultados.append(r)
        hechas += 1
        if al_progreso:
            al_progreso(t, r)
        if r.get("estado") != "ok":
            break
    return resultados


def codigo(resultados):
    """Código de salida del lote: 0 bien · 1 fallo · 2 esperando cuota · 3 bloqueado por coste."""
    ultimo = next((r for r in reversed(resultados) if r.get("estado") != "saltado"), None)
    if ultimo is None or ultimo.get("estado") == "ok":
        return 0
    return {"esperando_cuota": 2, "bloqueado_coste": 3}.get(ultimo.get("estado"), 1)


# --------------------------------------------------------------------------- autoprueba
def _png_falso(ancho=16, alto=9):
    """Un PNG entero (firma, IHDR, IDAT, IEND) de ancho×alto en gris."""
    def trozo(tipo, datos):
        return (len(datos).to_bytes(4, "big") + tipo + datos
                + zlib.crc32(tipo + datos).to_bytes(4, "big"))
    ihdr = ancho.to_bytes(4, "big") + alto.to_bytes(4, "big") + bytes([8, 0, 0, 0, 0])
    filas = b"".join(b"\x00" + b"\x80" * ancho for _ in range(alto))
    return (b"\x89PNG\r\n\x1a\n" + trozo(b"IHDR", ihdr) + trozo(b"IDAT", zlib.compress(filas))
            + trozo(b"IEND", b""))


def copia_temporal(prefijo="imagenes prueba é "):
    """Raíz temporal con guiones/fuentes, guiones/imagenes y guiones/estilo.md copiados del repo real."""
    real = pathlib.Path(__file__).resolve().parent.parent
    tmp = pathlib.Path(tempfile.mkdtemp(prefix=prefijo))
    shutil.copytree(real / "guiones" / "fuentes", tmp / "guiones" / "fuentes")
    shutil.copytree(real / "guiones" / "imagenes", tmp / "guiones" / "imagenes",
                    ignore=shutil.ignore_patterns("_anteriores"))
    shutil.copy2(real / "guiones" / "estilo.md", tmp / "guiones" / "estilo.md")
    (tmp / "guiones" / "registro").mkdir()
    return tmp


def ejecutar_falso(llamadas, estados=None):
    """capa_ia.ejecutar falso: escribe un PNG de 16×9 en `salida` (o devuelve el estado que toque). No gasta nada."""
    def ejecutar(trabajo, intervalo=1.0):
        llamadas.append(trabajo)
        estado = (estados or {}).get(len(llamadas), "ok")
        if estado != "ok":
            return {"id": f"falso-{len(llamadas)}", "estado": estado, "proveedor": "codex", "segundos": 0.1,
                    "motivo": "cuota (falso)", "reinicio_en": "2026-11-22T10:00:00Z", "etiqueta": trabajo["etiqueta"],
                    "archivos": []}
        p = pathlib.Path(trabajo["salida"])
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(_png_falso())
        return {"id": f"falso-{len(llamadas)}", "estado": "ok", "proveedor": "codex", "segundos": 0.1,
                "motivo": None, "reinicio_en": None, "etiqueta": trabajo["etiqueta"], "archivos": [str(p)],
                "cuota_antes": 2, "cuota_despues": 2}
    return ejecutar


def capa_que_no_gasta():
    """Sustituto de capa_ia para las autopruebas: si algo intenta ejecutar de verdad, falla en vez de gastar."""
    import types
    m = types.ModuleType("capa_ia")

    class CapaIAError(Exception):
        def __init__(self, codigo, resultado):
            super().__init__(f"capa-ia (prueba) código {codigo}")
            self.codigo, self.resultado = codigo, resultado

    def ejecutar(trabajo, intervalo=1.0):
        raise AssertionError("una autoprueba intentó ejecutar con el capa-ia real")
    m.CapaIAError, m.ejecutar = CapaIAError, ejecutar
    m.modo = lambda: "cli"
    m.estado = lambda: {"cuotas": {"codex": None}}
    m.registro = lambda app=None, desde=None: []
    return m


def autoprueba():
    sys.modules["capa_ia"] = capa_que_no_gasta()
    real = RAIZ
    fallos = []

    def comprobar(cond, msg):
        print(("  ✓ " if cond else "  ✗ ") + msg)
        if not cond:
            fallos.append(msg)

    # historial viejo sobre el registro real (solo lectura)
    filas = historial_viejo()
    con_prompt = [f for f in filas if f["prompt"]]
    comprobar(len(filas) >= 1 and all(f["origen"] == ORIGEN_VIEJO for f in filas),
              f"historial_viejo lee {len(filas)} filas con origen «{ORIGEN_VIEJO}»")
    comprobar(len(con_prompt) >= 1,
              f"historial_viejo reconstruye {len(con_prompt)} de {len(filas)} prompts con sha coincidente"
              + ("" if con_prompt else " (ninguno: los prompts de las fuentes cambiaron desde el 16-nov)"))
    comprobar(all(f["prompt_nota"] == "no se pudo reconstruir" for f in filas if not f["prompt"]),
              "las filas sin reconstruir lo dicen")

    tmp = copia_temporal()
    try:
        fijar_raiz(tmp)
        hoja = IMG / "escenarios" / "creacion-abismo.png"
        hoja.unlink()
        E = leer(F / "estilo.json")
        T = pendientes(E)
        toma = next(t for t in T if t["id"].startswith("Gn/") and hoja in t["refs"])
        comprobar(toma["bloqueo"] is not None, f"{toma['id']} está bloqueada sin la hoja creacion-abismo")
        instr = instrucciones()

        # el trabajo que se manda a capa-ia
        t0 = next(t for t in T if t["id"] == "personajes/jose")
        tr = trabajo_de(t0, instr)
        comprobar(tr["app"] == "biblia" and tr["tipo"] == "imagen" and tr["etiqueta"] == "personajes/jose",
                  "trabajo_de: app biblia, tipo imagen, etiqueta = id")
        comprobar(pathlib.Path(tr["ruta_app"]).is_absolute() and pathlib.Path(tr["ruta_app"]) == RAIZ,
                  "trabajo_de: ruta_app absoluta (la raíz)")
        comprobar(len(tr["adjuntos"]) == 3 and all(pathlib.Path(a).is_absolute() for a in tr["adjuntos"]),
                  "trabajo_de: adjuntos absolutos (las 3 láminas)")
        comprobar(NO_REPETIR in tr["prompt"] and t0["prompt"] in tr["prompt"] and instr in tr["prompt"],
                  "trabajo_de: prompt con instrucciones, NO_REPETIR y el prompt de la ficha")
        comprobar(not re.search(r"codex|image_gen|api key|Save the result", tr["prompt"], re.I),
                  "trabajo_de: nada propio de Codex en el prompt")
        comprobar(tr["sobrescribir"] is False and trabajo_de(t0, instr, True)["sobrescribir"] is True,
                  "trabajo_de: sobrescribir")

        # lote de 2 que recalcula
        llamadas, progreso = [], []
        res = generar_lote(2, ejecutar=ejecutar_falso(llamadas), al_progreso=lambda t, r: progreso.append(t["id"]))
        hechos = [x["etiqueta"] for x in llamadas]
        comprobar(hechos == ["escenarios/creacion-abismo", toma["id"]],
                  f"generar_lote(2) recalcula: {hechos}")
        comprobar(len(res) == 2 and all(r["estado"] == "ok" for r in res) and progreso == hechos,
                  "generar_lote devuelve 2 Resultados ok y avisa el progreso")
        comprobar(png(hoja) == (16, 9), "la hoja quedó escrita por el falso (16×9)")

        # solo por prefijo e ids exactos
        llamadas = []
        generar_lote(1, solo="Gn/gn-98", ejecutar=ejecutar_falso(llamadas))
        comprobar([x["etiqueta"] for x in llamadas] == ["Gn/gn-98-t1"], "solo = prefijo")
        llamadas = []
        res = generar_lote(5, ids=["Gn/gn-98-t3", "Gn/gn-98-t2", "Gn/gn-98-t1", "no/existe"],
                           ejecutar=ejecutar_falso(llamadas))
        comprobar([x["etiqueta"] for x in llamadas] == ["Gn/gn-98-t3", "Gn/gn-98-t2"],
                  "ids exactos en su orden; los que ya existen o no existen se saltan")
        comprobar([r["estado"] for r in res] == ["ok", "ok", "saltado", "saltado"], "saltados con motivo")

        # detener
        llamadas = []
        res = generar_lote(3, ejecutar=ejecutar_falso(llamadas), detener=lambda: len(llamadas) >= 1)
        comprobar(len(llamadas) == 1, "detener() para antes de la siguiente")

        # esperando cuota: para en 1 y código 2
        llamadas = []
        res = generar_lote(3, ejecutar=ejecutar_falso(llamadas, {1: "esperando_cuota"}))
        comprobar(len(llamadas) == 1 and len(res) == 1 and res[0]["estado"] == "esperando_cuota",
                  "esperando_cuota: una sola llamada y para")
        comprobar(codigo(res) == 2, "esperando_cuota → código 2")
        comprobar(codigo([{"estado": "bloqueado_coste"}]) == 3 and codigo([{"estado": "fallo"}]) == 1
                  and codigo([{"estado": "ok"}]) == 0 and codigo([]) == 0, "códigos 3, 1 y 0")

        # capa-ia real lanza CapaIAError en fallo y bloqueado_coste: se convierte en Resultado y para
        class Err(Exception):
            def __init__(self, codigo, resultado):
                self.codigo, self.resultado = codigo, resultado

        def lanza(trabajo, intervalo=1.0):
            llamadas.append(trabajo)
            raise Err(3, {"estado": "bloqueado_coste", "motivo": "tope de la app"})
        llamadas = []
        res = generar_lote(3, ejecutar=lanza)
        comprobar(len(llamadas) == 1 and res[0]["estado"] == "bloqueado_coste" and codigo(res) == 3,
                  "CapaIAError (bloqueado_coste) → Resultado, para, código 3")
    finally:
        fijar_raiz(real)
        shutil.rmtree(tmp, ignore_errors=True)

    print("AUTOPRUEBA:", "OK" if not fallos else f"{len(fallos)} FALLOS")
    return 1 if fallos else 0


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--generar", type=int, default=0, help="cuántas imágenes generar (0 = solo listar)")
    ap.add_argument("--solo", help="prefijo de id (estilo/, personajes/, escenarios/, Gn/…)")
    ap.add_argument("--autoprueba", action="store_true")
    a = ap.parse_args(argv)
    if a.autoprueba:
        return autoprueba()
    E = leer(F / "estilo.json")
    T = [t for t in pendientes(E) if not t["destino"].exists() and not (a.solo and not t["id"].startswith(a.solo))]
    listas = [t for t in T if not t["bloqueo"]]
    print(f"Pendientes: {len(T)} · listas para generar: {len(listas)}")
    for t in T:
        print(f"  {'·' if not t['bloqueo'] else 'x'} {t['id']}" + (f"  ({t['bloqueo']})" if t["bloqueo"] else ""))
    if not a.generar:
        return 0

    def progreso(t, r):
        cuota = (f" · cuota {r.get('cuota_antes')}→{r.get('cuota_despues')} %"
                 if r.get("cuota_antes") is not None else "")
        print(f"    {t['id']}: {r.get('estado')} · {r.get('proveedor') or '-'} · {r.get('segundos') or 0} s{cuota}"
              + (f" · {r['motivo']}" if r.get("motivo") else "")
              + (f" · reinicio {r['reinicio_en']}" if r.get("reinicio_en") else ""), flush=True)

    print(f"Generando hasta {a.generar} vía capa-ia …", flush=True)
    res = generar_lote(a.generar, solo=a.solo, al_progreso=progreso)
    c = codigo(res)
    hechas = sum(1 for r in res if r.get("estado") == "ok")
    print(f"Hechas: {hechas}." + {0: "", 1: " Lote detenido en el primer fallo.",
                                  2: " Lote detenido: esperando cuota.",
                                  3: " Lote detenido: bloqueado por coste."}[c]
          + " Registro: capa-ia registro --app biblia")
    return c


if __name__ == "__main__":
    sys.exit(main())
