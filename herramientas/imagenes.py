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

RAIZ = G = F = IMG = REGISTRO_VIEJO = PROMPTS_V1 = None


def fijar_raiz(raiz):
    """Apunta el módulo a otra raíz de repositorio (las autopruebas usan una copia temporal)."""
    global RAIZ, G, F, IMG, REGISTRO_VIEJO, PROMPTS_V1
    RAIZ = pathlib.Path(raiz).resolve()
    G = RAIZ / "guiones"
    F = G / "fuentes"
    IMG = G / "imagenes"
    REGISTRO_VIEJO = G / "registro" / "imagenes.jsonl"
    PROMPTS_V1 = G / "registro" / "imagenes-prompts-v1.json"


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


def _sha16(texto):
    return hashlib.sha256(texto.encode()).hexdigest()[:16]


def _clave(f):
    """Clave de una fila del registro viejo en imagenes-prompts-v1.json: «fecha id»."""
    return f"{f.get('fecha')} {f.get('id')}"


def _filas_viejas():
    if not REGISTRO_VIEJO.exists():
        return []
    filas = []
    for linea in REGISTRO_VIEJO.read_text(encoding="utf-8").splitlines():
        try:
            filas.append(json.loads(linea)) if linea.strip() else None
        except ValueError:
            continue
    return filas


def _congelados():
    """{clave: {prompt_sha256, prompt}} de imagenes-prompts-v1.json ({} si no está o no se lee)."""
    try:
        d = json.loads(PROMPTS_V1.read_text(encoding="utf-8")).get("prompts")
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError, AttributeError):
        return {}


def _reconstruir(filas):
    """{clave: prompt} de las filas cuyo `pedido_v1` sobre las fuentes actuales da su sha256[:16]."""
    try:
        E = leer(F / "estilo.json")
        T = {t["id"]: t for t in pendientes(E)}
        instr = instrucciones()
    except (OSError, ValueError, KeyError, AttributeError):
        return {}
    out = {}
    for f in filas:
        t = T.get(f.get("id"))
        if not t:
            continue
        # las referencias y el archivo, los de la fila (la lámina 2 se renombra al aprobarla)
        t = dict(t, refs=[RAIZ / r for r in f.get("refs", [])], destino=RAIZ / f.get("archivo", ""))
        try:
            texto = pedido_v1(t, instr)
        except ValueError:
            continue
        if _sha16(texto) == f.get("prompt_sha256"):
            out[_clave(f)] = texto
    return out


def congelar_prompts_v1():
    """Guarda (una vez) en imagenes-prompts-v1.json los prompts del 16-nov que hoy se reconstruyen con sha coincidente.

    Conserva lo ya congelado; devuelve (total congelados, nuevos). Así editar las fuentes no borra el historial.
    """
    filas = _filas_viejas()
    previos = _congelados()
    nuevos = {k: {"id": k.split(" ", 1)[1], "prompt_sha256": _sha16(p), "prompt": p}
              for k, p in _reconstruir(filas).items() if k not in previos}
    todos = dict(previos, **nuevos)
    orden = [_clave(f) for f in filas if _clave(f) in todos]
    doc = {"_nota": ("Prompts que mandó imagenes_codex.py el 2026-11-16 (Codex directo), reconstruidos con la misma "
                     "función (pedido_v1) y aceptados solo si su sha256[:16] coincide con el de "
                     "guiones/registro/imagenes.jsonl. Se congelan para que editar las fuentes no los borre del "
                     "historial del Estudio. No se edita a mano."),
           "prompts": {k: todos[k] for k in orden}}
    PROMPTS_V1.parent.mkdir(parents=True, exist_ok=True)
    PROMPTS_V1.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(doc["prompts"]), len(nuevos)


def historial_viejo():
    """Las filas de guiones/registro/imagenes.jsonl (Codex directo, 16-nov) con la forma del registro de capa-ia.

    El prompt sale primero de imagenes-prompts-v1.json (congelado) y, si no está, se reconstruye con `pedido_v1`
    sobre las fuentes actuales y las referencias y el archivo de la fila; en los dos casos solo se da si su
    sha256[:16] coincide con el guardado. No se escribe nada en el registro de capa-ia.
    """
    filas_v = _filas_viejas()
    congelados = _congelados()
    reconstruidos = None
    filas = []
    for f in filas_v:
        c = congelados.get(_clave(f)) or {}
        prompt = c.get("prompt") if isinstance(c.get("prompt"), str) and _sha16(c["prompt"]) == f.get(
            "prompt_sha256") else None
        if prompt is None:
            if reconstruidos is None:
                reconstruidos = _reconstruir(filas_v)
            prompt = reconstruidos.get(_clave(f))
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


TAM_FIXTURE = (32, 18)


def copia_temporal(prefijo="imagenes prueba é ", origen=None):
    """Raíz temporal para las autopruebas, independiente de las imágenes reales.

    Copia de `origen` (el repo por defecto) solo lo que es texto versionado: guiones/fuentes, guiones/estilo.md, el
    registro viejo y sus prompts congelados. Las imágenes NO se copian: se escriben PNG falsos de TAM_FIXTURE para
    cada lámina (la 2 siempre como `-codex`, la provisional), cada hoja de personaje y de escenario; ninguna toma ni
    `_anteriores`. Así aprobar la lámina 2, generar tomas o regenerar hojas en el repo no cambia el fixture.
    """
    origen = pathlib.Path(origen) if origen else pathlib.Path(__file__).resolve().parent.parent
    tmp = pathlib.Path(tempfile.mkdtemp(prefix=prefijo))
    g, go = tmp / "guiones", origen / "guiones"
    shutil.copytree(go / "fuentes", g / "fuentes")
    shutil.copy2(go / "estilo.md", g / "estilo.md")
    (g / "registro").mkdir()
    for nombre in ("imagenes.jsonl", "imagenes-prompts-v1.json"):
        if (go / "registro" / nombre).exists():
            shutil.copy2(go / "registro" / nombre, g / "registro" / nombre)
    falso = _png_falso(*TAM_FIXTURE)
    E = leer(g / "fuentes" / "estilo.json")
    destinos = [g / "imagenes" / "estilo" / (L["archivo"][:-4] + "-codex.png" if i == 1 else L["archivo"])
                for i, L in enumerate(E["laminas_patron"])]
    for carpeta in ("personajes", "escenarios"):
        destinos += [g / "imagenes" / carpeta / f"{leer(f)['id']}.png"
                     for f in sorted((g / "fuentes" / carpeta).glob("*.json"))]
    for p in destinos:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(falso)
    return tmp


def _listado(raiz):
    """[(ruta relativa, bytes)] de todos los archivos bajo `raiz`, ordenado."""
    return sorted((p.relative_to(raiz).as_posix(), p.read_bytes()) for p in raiz.rglob("*") if p.is_file())


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
    comprobar(len(con_prompt) == len(filas) and PROMPTS_V1.exists(),
              f"historial_viejo trae {len(con_prompt)} de {len(filas)} prompts (congelados en "
              f"{PROMPTS_V1.name}: {PROMPTS_V1.exists()})")
    comprobar(all(_sha16(f["prompt"]) == v["prompt_sha256"] for f in con_prompt
                  for v in [next(x for x in _filas_viejas() if x["fecha"] == f["fecha"] and x["id"] == f["etiqueta"])]),
              "cada prompt del historial viejo tiene el sha256[:16] de su fila")

    tmp = copia_temporal()
    post = otra = None
    try:
        # el fixture no depende de las imágenes del repo: un repo «después de la tarea 5» (lámina 2 aprobada y
        # renombrada, hojas regeneradas de otro tamaño, tomas generadas, versiones anteriores) da la misma copia
        post = pathlib.Path(tempfile.mkdtemp(prefix="imagenes post é "))
        for x in ("fuentes", "estilo.md", "registro"):
            (shutil.copytree if (tmp / "guiones" / x).is_dir() else shutil.copy2)(tmp / "guiones" / x, post / "guiones" / x)
        E0 = leer(tmp / "guiones" / "fuentes" / "estilo.json")
        for i, L in enumerate(E0["laminas_patron"]):
            p = post / "guiones" / "imagenes" / "estilo" / L["archivo"]  # la 2 ya aprobada: sin -codex
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(_png_falso(1672, 9 + i))
        for rel in ("personajes/jose.png", "escenarios/casa-jose-sala.png", "Gn/gn-01-t1.png", "Gn/gn-98-t4.png",
                    "_anteriores/personajes__jose-20261120-101010.png"):
            p = post / "guiones" / "imagenes" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(_png_falso(1672, 941))
        otra = copia_temporal("imagenes otra é ", origen=post)
        comprobar(_listado(otra / "guiones" / "imagenes") == _listado(tmp / "guiones" / "imagenes"),
                  "fixture independiente de las imágenes: con la lámina 2 aprobada y tomas generadas sale igual")
        comprobar((tmp / "guiones" / "imagenes" / "estilo" / "patron-2-interior-codex.png").exists()
                  and not (tmp / "guiones" / "imagenes" / "Gn").exists()
                  and not (tmp / "guiones" / "imagenes" / "_anteriores").exists(),
                  "fixture: lámina 2 como -codex, sin tomas ni _anteriores")

        fijar_raiz(tmp)
        E = leer(F / "estilo.json")
        T = pendientes(E)
        tomas = [t for t in T if not t["id"].startswith(("estilo/", "personajes/", "escenarios/"))]
        comprobar(tomas and all(png(t["destino"]) == TAM_FIXTURE for t in T if t["destino"].exists())
                  and not any(t["destino"].exists() for t in tomas), "fixture: PNG falsos de tamaño conocido")
        # se quita la hoja de escenario de la primera toma: esa toma queda bloqueada hasta que se genere
        hoja = tomas[0]["refs"][-1]
        esc = f"escenarios/{hoja.stem}"
        hoja.unlink()
        T = pendientes(E)
        toma = next(t for t in T if t["id"] == tomas[0]["id"])
        comprobar(toma["bloqueo"] is not None, f"{toma['id']} está bloqueada sin la hoja {esc}")
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
        comprobar(hechos == [esc, toma["id"]],
                  f"generar_lote(2) recalcula: {hechos}")
        comprobar(len(res) == 2 and all(r["estado"] == "ok" for r in res) and progreso == hechos,
                  "generar_lote devuelve 2 Resultados ok y avisa el progreso")
        comprobar(png(hoja) == (16, 9), "la hoja quedó escrita por el falso (16×9)")

        # solo por prefijo e ids exactos
        pref = tomas[-1]["id"].rsplit("-", 1)[0]  # el último pasaje, p. ej. Gn/gn-98
        g2 = [t["id"] for t in tomas if t["id"].startswith(pref + "-")]
        llamadas = []
        generar_lote(1, solo=pref, ejecutar=ejecutar_falso(llamadas))
        comprobar([x["etiqueta"] for x in llamadas] == [g2[0]], f"solo = prefijo ({pref})")
        llamadas = []
        res = generar_lote(5, ids=[g2[2], g2[1], g2[0], "no/existe"], ejecutar=ejecutar_falso(llamadas))
        comprobar([x["etiqueta"] for x in llamadas] == [g2[2], g2[1]],
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

        # prompts congelados: editar una fuente no borra el prompt del 16-nov del historial (Ruling R4)
        viejos = {f.get("id") for f in _filas_viejas()}
        objetivo = next(i for i in ("personajes/jose", *sorted(viejos))
                        if i in viejos and i.startswith(("personajes/", "escenarios/")))
        carpeta, nombre = objetivo.split("/")
        fj = F / carpeta / f"{nombre}.json"
        x = leer(fj)
        x["hoja_referencia"]["prompt_en"] += " Edited after the sixteenth of November."
        fj.write_text(json.dumps(x, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        h = [f for f in historial_viejo() if f["etiqueta"] == objetivo]
        comprobar(h and all(f["prompt"] for f in h), f"{objetivo} editado: el historial viejo sigue con su prompt")
        PROMPTS_V1.unlink(missing_ok=True)
        h = [f for f in historial_viejo() if f["etiqueta"] == objetivo]
        comprobar(h and all(f["prompt"] is None and f["prompt_nota"] == "no se pudo reconstruir" for f in h),
                  "sin el archivo congelado ya no se podría reconstruir (lo dice)")
        n, nuevos = congelar_prompts_v1()
        comprobar(n == len(_filas_viejas()) - len(h) and nuevos == n,
                  f"congelar_prompts_v1 en la copia: {n} congelados (el editado no)")
    finally:
        fijar_raiz(real)
        for d in (tmp, post, otra):
            if d:
                shutil.rmtree(d, ignore_errors=True)

    print("AUTOPRUEBA:", "OK" if not fallos else f"{len(fallos)} FALLOS")
    return 1 if fallos else 0


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--generar", type=int, default=0, help="cuántas imágenes generar (0 = solo listar)")
    ap.add_argument("--solo", help="prefijo de id (estilo/, personajes/, escenarios/, Gn/…)")
    ap.add_argument("--autoprueba", action="store_true")
    ap.add_argument("--congelar-prompts-v1", action="store_true",
                    help="guarda en guiones/registro/imagenes-prompts-v1.json los prompts del 16-nov reconstruibles")
    a = ap.parse_args(argv)
    if a.autoprueba:
        return autoprueba()
    if a.congelar_prompts_v1:
        n, nuevos = congelar_prompts_v1()
        print(f"{PROMPTS_V1.relative_to(RAIZ).as_posix()}: {n} prompts congelados ({nuevos} nuevos) de "
              f"{len(_filas_viejas())} filas.")
        return 0
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
