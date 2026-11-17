"""Datos del Estudio de la Biblia narrada: lectura de fuentes e imágenes, revisión y edición de prompts. Sin red.

    python -I herramientas/estudio_datos.py --autoprueba    # sobre una copia temporal; no toca el repo ni gasta

Lo usa `herramientas/estudio.py` (el servidor). Revisión en `guiones/registro/revision.json`
(`{id: {estado, nota, fecha, archivo, archivo_sha256}}`); versiones reemplazadas en `guiones/imagenes/_anteriores/`.
"""
import copy, datetime, hashlib, json, os, pathlib, re, shutil, subprocess, sys, tempfile, threading, time
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import imagenes as I  # noqa: E402

CODIGO = pathlib.Path(__file__).resolve().parent          # herramientas/ (de aquí sale guiones.py)
GUIONES_PY = CODIGO / "guiones.py"
RAIZ = G = F = IMG = REVISION = ANTERIORES = None
EDITABLES = ("prompt_en", "negativo_en")
ESTADOS = ("aprobada", "rechazada")
_CERROJO = threading.RLock()  # revisión y ediciones de uno en uno: nunca dos escrituras a la vez


def fijar_raiz(raiz):
    """Apunta el módulo (y `imagenes`) a otra raíz de repositorio (las autopruebas usan una copia temporal)."""
    global RAIZ, G, F, IMG, REVISION, ANTERIORES
    I.fijar_raiz(raiz)
    RAIZ, G, F, IMG = I.RAIZ, I.G, I.F, I.IMG
    REVISION = G / "registro" / "revision.json"
    ANTERIORES = IMG / "_anteriores"


fijar_raiz(CODIGO.parent)


# --------------------------------------------------------------------------- índice
def _rel(p):
    return p.relative_to(RAIZ).as_posix()


def _url(p):
    return "/img/" + urllib.parse.quote(p.relative_to(IMG).as_posix())


def _campo(ruta, campo):
    """['escenas', 0, 'tomas', 2, 'imagen'] + 'prompt_en' → 'escenas[0].tomas[2].imagen.prompt_en'."""
    s = ""
    for k in ruta:
        s += f"[{k}]" if isinstance(k, int) else ("." if s else "") + k
    return f"{s}.{campo}" if s else campo


def _indice():
    """(E, [entrada]) con cada lámina, hoja y toma: id, grupo, título, JSON de origen y ruta al dict del prompt."""
    E = I.leer(F / "estilo.json")
    lams = E["laminas_patron"]
    lam_ids = [f"estilo/{L['archivo'][:-4]}" for L in lams]
    out = []
    for i, L in enumerate(lams):
        out.append(dict(id=lam_ids[i], grupo="estilo", titulo=f"Lámina patrón {i + 1}", fuente=F / "estilo.json",
                        ruta=["laminas_patron", i], x=L, base=L, refs=lam_ids[:i], editables=("prompt_en",),
                        ficha={"archivo": L["archivo"]}))
    for carpeta in ("personajes", "escenarios"):
        for f in sorted((F / carpeta).glob("*.json")):
            x = I.leer(f)
            h = x.get("hoja_referencia") or {}
            ficha = {k: v for k, v in x.items() if k not in ("id", "nombre", "hoja_referencia")}
            ficha.update({k: h[k] for k in ("prompt_es", "negativo_es") if h.get(k)})
            out.append(dict(id=f"{carpeta}/{x['id']}", grupo=carpeta, titulo=x.get("nombre") or x["id"], fuente=f,
                            ruta=["hoja_referencia"], x=x, base=h, refs=list(lam_ids), editables=EDITABLES,
                            ficha=ficha))
    for f in sorted(F.glob("*/*.json")):
        if f.parent.name in ("personajes", "escenarios"):
            continue
        g = I.leer(f)
        for a, es in enumerate(g["escenas"]):
            for b, t in enumerate(es["tomas"]):
                im, mov = t.get("imagen") or {}, t.get("movimiento") or {}
                ficha = {k: t[k] for k in ("versiculos", "nivel", "perfil", "transicion", "personajes", "escenario",
                                           "clips_8s", "fidelidad") if k in t}
                ficha.update({"escena": es.get("titulo"), "descripcion_es": im.get("descripcion_es"),
                              "movimiento_es": mov.get("descripcion_es"), "camara": mov.get("camara")})
                refs = list(lam_ids) + [f"personajes/{p}" for p in t.get("personajes", [])]
                refs.append(f"escenarios/{t['escenario']}")
                out.append(dict(id=f"{g['libro']}/{g['id']}-{t['id']}", grupo="tomas", titulo=t.get("titulo") or t["id"],
                                fuente=f, ruta=["escenas", a, "tomas", b, "imagen"], x=t, base=im, refs=refs,
                                editables=EDITABLES, ficha={k: v for k, v in ficha.items() if v is not None},
                                guion=g, escena=es, movimiento_en=mov.get("prompt_en")))
    return E, out


def _pendientes():
    return {t["id"]: t for t in I.pendientes(I.leer(F / "estilo.json"))}


def imagen_actual(id_):
    """Ruta de la imagen actual de `id_`, o None si no hay. ValueError si el id no existe."""
    t = _pendientes().get(id_)
    if t is None:
        raise ValueError(f"{id_}: id desconocido")
    return t["destino"] if t["destino"].is_file() else None


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for trozo in iter(lambda: fh.read(1 << 20), b""):
            h.update(trozo)
    return h.hexdigest()


def _reemplazar(origen, destino):
    """`os.replace` con reintento corto: en Windows, un lector puede tener el archivo abierto un instante."""
    for intento in range(20):
        try:
            os.replace(origen, destino)
            return
        except PermissionError:
            if intento == 19:
                raise
            time.sleep(0.05)


def _escribir_atomico(p, texto):
    """Escribe en un temporal de la misma carpeta y lo cambia por el original: nunca queda a medio escribir."""
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{p.name}.", suffix=".tmp", dir=p.parent)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(texto.encode("utf-8"))
        _reemplazar(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


# --------------------------------------------------------------------------- revisión
def _revisiones():
    try:
        r = json.loads(REVISION.read_text(encoding="utf-8"))
        return r if isinstance(r, dict) else {}
    except (OSError, ValueError):
        return {}


def _estado(r, img):
    if not r:
        return "pendiente"
    if img is None or _sha(img) != r.get("archivo_sha256"):
        return "cambiada"
    return r.get("estado") or "pendiente"


def estado_revision(id_):
    """«pendiente», «aprobada», «rechazada» o «cambiada» (la imagen ya no es la revisada: sha256 distinto)."""
    return _estado(_revisiones().get(id_), imagen_actual(id_))


LAMINA2, LAMINA2_PROVISIONAL = "estilo/patron-2-interior", "patron-2-interior-codex.png"
MOTIVO_NO_RENOMBRAR = ("La lámina 2 no se puede aprobar mientras hay un lote en curso: aprobarla renombra "
                       "patron-2-interior-codex.png, que cada imagen del lote lleva adjunta. Apruébala cuando termine.")


def renombraria(id_, estado):
    """True si aprobar `id_` ahora renombraría la lámina 2 provisional (lo que hace `marcar`)."""
    if id_ != LAMINA2 or estado != "aprobada":
        return False
    img = imagen_actual(id_)
    return img is not None and img.name == LAMINA2_PROVISIONAL and not img.with_name("patron-2-interior.png").exists()


def marcar(id_, estado, nota=""):
    """Aprueba o rechaza la imagen actual de `id_` (con su sha256). Aprobar la lámina 2 provisional la renombra."""
    if estado not in ESTADOS:
        raise ValueError(f"estado inválido: {estado!r} (aprobada o rechazada)")
    nota = (nota or "").strip()
    with _CERROJO:
        img = imagen_actual(id_)
        if img is None:
            raise ValueError(f"{id_}: no hay imagen que revisar")
        renombrada = None
        if renombraria(id_, estado):
            final = img.with_name("patron-2-interior.png")
            _reemplazar(img, final)
            img, renombrada = final, _rel(final)
        rev = _revisiones()
        rev[id_] = {"estado": estado, "nota": nota, "fecha": datetime.datetime.now().isoformat(timespec="seconds"),
                    "archivo": _rel(img), "archivo_sha256": _sha(img)}
        _escribir_atomico(REVISION, json.dumps(rev, ensure_ascii=False, indent=2) + "\n")
    r = {"ok": True, "id": id_, "revision": rev[id_]}
    if renombrada:
        r["renombrada"] = renombrada
        r["mensaje"] = f"Lámina 2 aprobada: patron-2-interior-codex.png pasa a {renombrada}."
    return r


# --------------------------------------------------------------------------- edición de prompts
def _serializar(texto, nuevo_obj, antes, valor, existia):
    """El JSON con el campo cambiado y el resto del archivo como estaba (formato y finales de línea).

    Si el valor viejo aparece una sola vez como literal, se cambia solo ese literal (y se comprueba que el resultado
    es exactamente el objeto esperado); si no, `json.dumps(…, ensure_ascii=False, indent=2) + "\\n"`.
    """
    if existia and isinstance(antes, str):
        viejo, nuevo = json.dumps(antes, ensure_ascii=False), json.dumps(valor, ensure_ascii=False)
        if texto.count(viejo) == 1:
            cand = texto.replace(viejo, nuevo)
            try:
                if json.loads(cand) == nuevo_obj:
                    return cand
            except ValueError:
                pass
    s = json.dumps(nuevo_obj, ensure_ascii=False, indent=2) + "\n"
    return s.replace("\n", "\r\n") if "\r\n" in texto else s


def _guiones(*args):
    return subprocess.run([sys.executable, "-I", str(GUIONES_PY), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=300)


def _errores_extra(E, entrada, campo, valor):
    """Lo que guiones.py no mira: los prompts de las láminas patrón (mismas reglas que las hojas)."""
    if entrada["grupo"] != "estilo":
        return []
    donde = f"estilo.json · {entrada['id']} · {_campo(entrada['ruta'], campo)} · "
    errores = []
    for t in E.get("prohibidos_prompt", []):
        m = re.search(r"\b" + re.escape(t) + r"\b", valor, re.IGNORECASE)
        if m:
            errores.append(donde + f"término prohibido en prompt positivo: {m.group(0)!r}")
    if "#" in valor:
        errores.append(donde + "las etiquetas # solo van en los prompts de video")
    if not valor.rstrip().endswith((".", "!")):
        errores.append(donde + "prompt de imagen en frases completas (termina en punto)")
    return errores


def _validar(fuente, texto):
    """Errores de guiones.py con el cambio aplicado sobre una copia temporal de las fuentes ([] si valida)."""
    with tempfile.TemporaryDirectory(prefix="estudio valida ") as d:
        copia = pathlib.Path(d) / "fuentes"
        shutil.copytree(F, copia)
        (copia / fuente.relative_to(F)).write_bytes(texto.encode("utf-8"))
        r = _guiones("--fuentes", str(copia), "--salida", str(G), "--sin-salida")
    if r.returncode == 0:
        return []
    errores = [l[len("ERROR: "):] for l in r.stdout.splitlines() if l.startswith("ERROR: ")]
    return errores or [((r.stdout or "") + (r.stderr or "")).strip()[-2000:]
                       or f"el validador salió con código {r.returncode}"]


def editar_prompt(id_, campo, valor):
    """Cambia `prompt_en` o `negativo_en` de `id_` en su JSON de guiones/fuentes, solo si el validador lo acepta.

    Devuelve {ok, antes, despues, errores}; con errores no se escribe nada. Si se escribe (de forma atómica), se
    regeneran las fichas .md con guiones.py.
    """
    if campo not in EDITABLES:
        return {"ok": False, "antes": None, "despues": None,
                "errores": [f"{id_} · {campo}: no se edita desde el Estudio (solo prompt_en y negativo_en)"]}
    if not isinstance(valor, str):
        return {"ok": False, "antes": None, "despues": None, "errores": [f"{id_} · {campo}: el valor debe ser texto"]}
    valor = valor.strip()
    with _CERROJO:
        E, indice = _indice()
        e = next((x for x in indice if x["id"] == id_), None)
        if e is None:
            return {"ok": False, "antes": None, "despues": valor, "errores": [f"{id_}: id desconocido"]}
        if campo not in e["editables"]:
            return {"ok": False, "antes": None, "despues": valor,
                    "errores": [f"{id_} · {campo}: las láminas patrón solo tienen prompt_en (el negativo es el general "
                                "de estilo.json, que no se edita desde el Estudio)"]}
        fuente = e["fuente"]
        texto = fuente.read_bytes().decode("utf-8")
        obj = json.loads(texto)
        nuevo_obj = copy.deepcopy(obj)
        cont = nuevo_obj
        for k in e["ruta"]:
            cont = cont[k]
        existia = campo in cont
        antes = cont.get(campo, "")
        cont[campo] = valor
        r = {"ok": False, "antes": antes, "despues": valor, "archivo": _rel(fuente),
             "campo": _campo(e["ruta"], campo), "errores": []}
        if not valor:
            if campo == "prompt_en":
                r["errores"] = [f"{_rel(fuente)} · {id_} · {r['campo']} · no puede quedar vacío"]
                return r
            del cont[campo]  # negativo vacío = sin negativo propio
        nuevo_texto = _serializar(texto, nuevo_obj, antes, valor, existia and bool(valor))
        r["errores"] = _errores_extra(E, e, campo, valor) or _validar(fuente, nuevo_texto)
        if r["errores"]:
            return r
        if nuevo_texto != texto:
            _escribir_atomico(fuente, nuevo_texto)
        g = _guiones("--fuentes", str(F), "--salida", str(G))
        r["ok"] = True
        if g.returncode != 0:
            r["aviso"] = "Se guardó el prompt, pero no se pudieron regenerar las fichas .md: " + g.stdout[-500:]
        return r


# --------------------------------------------------------------------------- regenerar
def apartar_para_regenerar(id_):
    """Mueve la imagen actual a _anteriores/<id con / → __>-<AAAAMMDD-HHMMSS>.png; devuelve la ruta (None si no hay)."""
    with _CERROJO:
        img = imagen_actual(id_)
        if img is None:
            return None
        ANTERIORES.mkdir(parents=True, exist_ok=True)
        base = id_.replace("/", "__") + "-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        dest, k = ANTERIORES / f"{base}.png", 2
        while dest.exists():
            dest, k = ANTERIORES / f"{base}-{k}.png", k + 1
        shutil.move(str(img), str(dest))
        return dest


def _anteriores(id_, nombres):
    patron = re.compile(re.escape(id_.replace("/", "__")) + r"-\d{8}-\d{6}(?:-\d+)?\.png")
    return ["/img/_anteriores/" + urllib.parse.quote(n) for n in sorted(nombres) if patron.fullmatch(n)]


# --------------------------------------------------------------------------- datos para la página
def datos(registro_capa=None):
    """Todo lo que muestra la página. `registro_capa`: filas del registro de capa-ia (app biblia), si las hay."""
    E, indice = _indice()
    T = _pendientes()
    rev = _revisiones()
    hist = {}
    for fila in list(registro_capa or []) + I.historial_viejo():
        if isinstance(fila, dict) and fila.get("etiqueta"):
            hist.setdefault(fila["etiqueta"], []).append(fila)
    nombres = [p.name for p in ANTERIORES.iterdir()] if ANTERIORES.is_dir() else []

    def item(e):
        t = T[e["id"]]
        img = t["destino"] if t["destino"].is_file() else None
        dim = I.png(img) if img else None
        r = rev.get(e["id"]) or {}
        it = {"id": e["id"], "titulo": e["titulo"], "grupo": e["grupo"],
              "imagen": _url(img) if img else None, "ancho": dim and dim[0], "alto": dim and dim[1],
              "prompt_en": e["base"].get("prompt_en", ""), "negativo_en": e["base"].get("negativo_en", ""),
              "prompt_enviado": t["prompt"], "ficha": e["ficha"], "fuente": _rel(e["fuente"]),
              "campo": _campo(e["ruta"], "prompt_en"), "campo_negativo": _campo(e["ruta"], "negativo_en"),
              "editables": list(e["editables"]), "refs": e["refs"], "bloqueo": t["bloqueo"],
              "revision": {"estado": _estado(r, img), "nota": r.get("nota", ""), "fecha": r.get("fecha")},
              "historial": sorted(hist.get(e["id"], []), key=lambda f: str(f.get("fecha") or "")),
              "anteriores": _anteriores(e["id"], nombres)}
        if e["grupo"] == "tomas":
            it["movimiento_en"] = e["movimiento_en"]
        return it

    grupos = {"estilo": [], "personajes": [], "escenarios": []}
    pasajes, por_guion = [], {}
    for e in indice:
        if e["grupo"] != "tomas":
            grupos[e["grupo"]].append(item(e))
            continue
        g, es = e["guion"], e["escena"]
        p = por_guion.get(g["id"])
        if p is None:
            p = por_guion[g["id"]] = {"libro": g["libro"], "id": g["id"],
                                      "titulo": f"{g.get('inicio', '')}–{g.get('fin', '')}", "escenas": []}
            pasajes.append(p)
        if not p["escenas"] or p["escenas"][-1]["id"] != es["id"]:
            p["escenas"].append({"id": es["id"], "titulo": es.get("titulo", ""), "tomas": []})
        p["escenas"][-1]["tomas"].append(item(e))
    return {"estilo": {"nombre": E.get("nombre_estilo"), "rotulo_ia": E.get("rotulo_ia")},
            "laminas": grupos["estilo"], "personajes": grupos["personajes"], "escenarios": grupos["escenarios"],
            "pasajes": pasajes}


# --------------------------------------------------------------------------- autoprueba
def copia_temporal(prefijo="estudio prueba é "):
    """Repo mínimo en una carpeta con espacios y «é»: fuentes, imágenes, estilo.md, registro viejo y una revisión."""
    tmp = I.copia_temporal(prefijo)  # imágenes falsas de tamaño fijo: no depende de guiones/imagenes del repo
    (tmp / "guiones" / "registro" / "revision.json").write_text(json.dumps(
        {"personajes/benjamin": {"estado": "aprobada", "nota": "", "fecha": "2026-11-16T21:00:00",
                                 "archivo": "guiones/imagenes/personajes/benjamin.png", "archivo_sha256": "0" * 64}},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return tmp


def autoprueba():
    sys.modules["capa_ia"] = I.capa_que_no_gasta()
    real = RAIZ
    fallos = []

    def comprobar(cond, msg):
        print(("  ✓ " if cond else "  ✗ ") + msg)
        if not cond:
            fallos.append(msg)

    def sin(d, ruta):
        """Copia de d sin la clave al final de `ruta` (para comparar que solo cambió ese campo)."""
        d = copy.deepcopy(d)
        c = d
        for k in ruta[:-1]:
            c = c[k]
        c.pop(ruta[-1], None)
        return d

    tmp = copia_temporal()
    try:
        fijar_raiz(tmp)
        comprobar(" " in str(RAIZ) and "é" in str(RAIZ), f"raíz temporal con espacios y «é»: {RAIZ.name}")
        fila_capa = {"fecha": "2026-11-17T12:00:00", "id": "x1", "app": "biblia", "etiqueta": "personajes/jose",
                     "tipo": "imagen", "proveedor": "codex", "prompt": "…", "estado": "ok", "segundos": 80,
                     "cuota_antes": 2, "cuota_despues": 2, "costo_estimado": 0.2}
        d = datos([fila_capa, dict(fila_capa, etiqueta="otra/cosa")])
        comprobar(d["estilo"]["rotulo_ia"] == "Ilustración moderna (generada con IA)" and d["estilo"]["nombre"],
                  "estilo: nombre y rótulo de la IA")
        esperado = (len(I.leer(F / "estilo.json")["laminas_patron"]), len(list((F / "personajes").glob("*.json"))),
                    len(list((F / "escenarios").glob("*.json"))))
        comprobar((len(d["laminas"]), len(d["personajes"]), len(d["escenarios"])) == esperado == (3, 3, 6),
                  f"3 láminas, 3 personajes, 6 escenarios: {len(d['laminas'])}, {len(d['personajes'])}, "
                  f"{len(d['escenarios'])}")
        pas = {p["id"]: p for p in d["pasajes"]}
        ntomas = {k: sum(len(e["tomas"]) for e in p["escenas"]) for k, p in pas.items()}
        guiones_ = {g["id"]: sum(len(e["tomas"]) for e in g["escenas"])
                    for g in (I.leer(f) for f in sorted(F.glob("*/*.json"))
                              if f.parent.name not in ("personajes", "escenarios"))}
        comprobar(ntomas == guiones_ and {"gn-01", "gn-98"} <= set(ntomas), f"tomas de gn-01 y gn-98: {ntomas}")
        L2 = d["laminas"][1]
        comprobar(L2["id"] == "estilo/patron-2-interior" and L2["campo"] == "laminas_patron[1].prompt_en"
                  and L2["fuente"] == "guiones/fuentes/estilo.json" and L2["grupo"] == "estilo",
                  "lámina 2: id, campo y fuente")
        comprobar(L2["imagen"] == "/img/estilo/patron-2-interior-codex.png" and L2["refs"] == ["estilo/patron-1-paisaje"],
                  "lámina 2: imagen provisional de Codex y refs")
        jose = next(x for x in d["personajes"] if x["id"] == "personajes/jose")
        comprobar(jose["campo"] == "hoja_referencia.prompt_en" and jose["fuente"] == "guiones/fuentes/personajes/jose.json"
                  and jose["titulo"] == "José", "hoja de José: campo, fuente y título")
        comprobar(jose["imagen"] == "/img/personajes/jose.png" and (jose["ancho"], jose["alto"]) == I.TAM_FIXTURE,
                  "hoja de José: imagen y tamaño")
        comprobar(jose["prompt_enviado"].startswith(I.leer(F / "estilo.json")["base_imagen_en"])
                  and jose["prompt_en"] in jose["prompt_enviado"] and jose["negativo_en"] in jose["prompt_enviado"],
                  "prompt_enviado = base + prompt + negativos")
        comprobar("rasgos" in jose["ficha"] and "vestuario" in jose["ficha"] and "edades" in jose["ficha"],
                  "ficha legible de José")
        comprobar([h.get("origen") for h in jose["historial"]] == [I.ORIGEN_VIEJO, None]
                  and jose["historial"][1]["id"] == "x1", "historial: el viejo (16-nov) y el de capa-ia, por fecha")
        comprobar(jose["historial"][0]["prompt"] is not None, "historial viejo con el prompt reconstruido")
        t1 = pas["gn-01"]["escenas"][0]["tomas"][0]
        comprobar(t1["id"] == "Gn/gn-01-t1" and t1["campo"] == "escenas[0].tomas[0].imagen.prompt_en"
                  and t1["fuente"] == "guiones/fuentes/Gn/gn-01.json" and t1["grupo"] == "tomas",
                  "toma gn-01 t1: id, campo y fuente")
        comprobar(t1["imagen"] is None and t1["movimiento_en"] and t1["bloqueo"] is None
                  and f"escenarios/{t1['ficha']['escenario']}" in t1["refs"], "toma: sin imagen, movimiento, refs y bloqueo")
        g98 = pas["gn-98"]["escenas"][-1]["tomas"][-1]
        comprobar(re.fullmatch(r"escenas\[\d+\]\.tomas\[\d+\]\.imagen\.prompt_en", g98["campo"]) is not None
                  and g98["fuente"] == "guiones/fuentes/Gn/gn-98.json", "toma de gn-98: campo y fuente")
        benj = next(x for x in d["personajes"] if x["id"] == "personajes/benjamin")
        comprobar(benj["revision"]["estado"] == "cambiada", "revisión con sha distinto → cambiada")
        comprobar(jose["revision"]["estado"] == "pendiente", "sin revisión → pendiente")

        # marcar y sha (foco 5)
        r = marcar("personajes/jose", "rechazada", "toga griega; parece de 30")
        comprobar(r["ok"] and estado_revision("personajes/jose") == "rechazada", "marcar rechazada con nota")
        rv = json.loads(REVISION.read_text(encoding="utf-8"))["personajes/jose"]
        comprobar(rv["nota"] == "toga griega; parece de 30" and len(rv["archivo_sha256"]) == 64
                  and rv["archivo"] == "guiones/imagenes/personajes/jose.png", "revision.json guarda nota, archivo y sha")
        with open(IMG / "personajes" / "jose.png", "ab") as fh:
            fh.write(b"\x00")
        comprobar(estado_revision("personajes/jose") == "cambiada", "un byte distinto → cambiada")
        try:
            marcar("Gn/gn-01-t1", "aprobada")
            comprobar(False, "marcar sin imagen falla")
        except ValueError:
            comprobar(True, "marcar sin imagen falla")
        try:
            marcar("personajes/jose", "quizas")
            comprobar(False, "marcar con estado inválido falla")
        except ValueError:
            comprobar(True, "marcar con estado inválido falla")

        # editar con «halo»: no se escribe nada
        f_jose = F / "personajes" / "jose.json"
        antes_b = f_jose.read_bytes()
        r = editar_prompt("personajes/jose", "prompt_en", jose["prompt_en"] + " He wears a faint halo.")
        comprobar(not r["ok"] and any("halo" in e for e in r["errores"]), f"«halo» → ok false con errores: {r['errores'][:1]}")
        comprobar(all(e.count(" · ") >= 3 for e in r["errores"]), "errores «archivo · id · campo · msg»")
        comprobar(f_jose.read_bytes() == antes_b, "con errores el archivo queda idéntico (bytes)")
        for id_, campo in (("personajes/jose", "base_imagen_en"), ("estilo/patron-1-paisaje", "negativo_en"),
                           ("no/existe", "prompt_en")):
            r = editar_prompt(id_, campo, "Anything.")
            comprobar(not r["ok"] and r["errores"], f"{id_} · {campo}: no editable → error")

        # edición válida en un archivo con formato propio (listas en una línea)
        f_ab = F / "escenarios" / "creacion-abismo.json"
        texto0 = f_ab.read_text(encoding="utf-8")
        obj0 = json.loads(texto0)
        nuevo = "A boundless dark ocean under total darkness, with a faint grey sheen on the slow swell."
        r = editar_prompt("escenarios/creacion-abismo", "prompt_en", nuevo)
        texto1 = f_ab.read_text(encoding="utf-8")
        obj1 = json.loads(texto1)
        comprobar(r["ok"] and r["antes"] == obj0["hoja_referencia"]["prompt_en"] and r["despues"] == nuevo,
                  "edición válida → ok, antes y después")
        comprobar(obj1["hoja_referencia"]["prompt_en"] == nuevo
                  and sin(obj1, ["hoja_referencia", "prompt_en"]) == sin(obj0, ["hoja_referencia", "prompt_en"])
                  and list(obj1) == list(obj0), "el JSON cambia solo ese campo (como dict, mismo orden de claves)")
        comprobar(texto1.endswith("}\n") and "\n  \"id\"" in texto1 and "\\u00" not in texto1 and "ó" in texto1,
                  "conserva indentación 2, acentos literales y salto final")
        comprobar(len(texto1.splitlines()) == len(texto0.splitlines()), "el resto del formato del archivo no cambia")
        ficha_md = G / "escenarios" / "creacion-abismo.md"
        comprobar(ficha_md.exists() and nuevo in ficha_md.read_text(encoding="utf-8"), "fichas .md regeneradas")

        # estilo.json conserva CRLF; las láminas también se validan
        f_est = F / "estilo.json"
        e0 = json.loads(f_est.read_text(encoding="utf-8"))
        crlf0 = f_est.read_bytes().count(b"\r\n")
        nuevo_l = e0["laminas_patron"][0]["prompt_en"] + " The light is soft and even."
        r = editar_prompt("estilo/patron-1-paisaje", "prompt_en", nuevo_l)
        b1 = f_est.read_bytes()
        e1 = json.loads(b1.decode("utf-8"))
        comprobar(r["ok"] and e1["laminas_patron"][0]["prompt_en"] == nuevo_l
                  and sin(e1, ["laminas_patron", 0, "prompt_en"]) == sin(e0, ["laminas_patron", 0, "prompt_en"]),
                  "lámina 1 editada: solo ese campo")
        comprobar(b1.count(b"\r\n") == crlf0 and b1.count(b"\n") == crlf0 and b1.endswith(b"}\r\n"),
                  "estilo.json conserva CRLF")
        s = _serializar('{\r\n  "a": "x"\r\n}\r\n', {"a": "x", "b": "é"}, "", "é", False)
        comprobar(s == '{\r\n  "a": "x",\r\n  "b": "é"\r\n}\r\n', "sin literal único: json.dumps con indent 2 y CRLF si lo tenía")
        antes_b = f_est.read_bytes()
        r = editar_prompt("estilo/patron-1-paisaje", "prompt_en", nuevo_l + " A halo of light.")
        comprobar(not r["ok"] and f_est.read_bytes() == antes_b, "lámina con «halo» → error y archivo idéntico")

        # dos ediciones seguidas y dos a la vez (foco 2)
        p1 = jose["prompt_en"] + " He looks about forty."
        n1 = "Do not give him a crown, a beard or a draped Greek or Roman toga, and keep the background plain."
        r1 = editar_prompt("personajes/jose", "prompt_en", p1)
        r2 = editar_prompt("personajes/jose", "negativo_en", n1)
        h = json.loads(f_jose.read_text(encoding="utf-8"))["hoja_referencia"]
        comprobar(r1["ok"] and r2["ok"] and h["prompt_en"] == p1 and h["negativo_en"] == n1,
                  "dos ediciones seguidas: la segunda ve la primera")
        hv = [x for x in next(x for x in datos()["personajes"] if x["id"] == "personajes/jose")["historial"]
              if x.get("origen") == I.ORIGEN_VIEJO]
        comprobar(hv and all(x["prompt"] and h["prompt_en"] not in x["prompt"] for x in hv),
                  "tras editar el prompt de José, su historial viejo sigue trayendo el prompt del 16-nov")
        f98 = F / "Gn" / "gn-98.json"
        g0 = json.loads(f98.read_text(encoding="utf-8"))
        res = {}
        hilos = [threading.Thread(target=lambda k=k, v=v: res.__setitem__(k, editar_prompt("Gn/gn-98-t1", k, v)))
                 for k, v in (("prompt_en", g0["escenas"][0]["tomas"][0]["imagen"]["prompt_en"] + " The hall is quiet."),
                              ("negativo_en", "Do not show any servant in the hall."))]
        for x in hilos:
            x.start()
        for x in hilos:
            x.join()
        im = json.loads(f98.read_text(encoding="utf-8"))["escenas"][0]["tomas"][0]["imagen"]
        comprobar(all(v["ok"] for v in res.values()) and im["prompt_en"].endswith("The hall is quiet.")
                  and im["negativo_en"] == "Do not show any servant in the hall.",
                  "dos ediciones a la vez de la misma toma: se guardan las dos")

        # apartar para regenerar (foco 3) con la raíz con espacios y «é»
        p = apartar_para_regenerar("personajes/benjamin")
        comprobar(p is not None and p.parent == ANTERIORES and p.exists()
                  and re.fullmatch(r"personajes__benjamin-\d{8}-\d{6}\.png", p.name) is not None
                  and not (IMG / "personajes" / "benjamin.png").exists(), f"apartar mueve a _anteriores: {p and p.name}")
        b = next(x for x in datos()["personajes"] if x["id"] == "personajes/benjamin")
        comprobar(b["imagen"] is None and b["anteriores"] == ["/img/_anteriores/" + urllib.parse.quote(p.name)],
                  "la imagen vieja queda accesible por anteriores")
        comprobar(apartar_para_regenerar("personajes/benjamin") is None, "apartar sin imagen → None")

        # aprobar la lámina 2 la renombra (con el archivo «abierto» las dos primeras veces: se reintenta)
        comprobar(renombraria("estilo/patron-2-interior", "aprobada")
                  and not renombraria("estilo/patron-2-interior", "rechazada")
                  and not renombraria("personajes/jose", "aprobada"), "renombraria: solo aprobar la lámina 2 provisional")
        replace_real, ocupado = os.replace, [2]

        def replace_ocupado(a, b):
            if ocupado[0]:
                ocupado[0] -= 1
                raise PermissionError(32, "El proceso no tiene acceso al archivo (prueba)")
            return replace_real(a, b)
        os.replace = replace_ocupado
        try:
            r = marcar("estilo/patron-2-interior", "aprobada")
        finally:
            os.replace = replace_real
        comprobar(ocupado[0] == 0, "el renombrado de la lámina 2 se reintenta tras PermissionError")
        comprobar(r["ok"] and r.get("renombrada") == "guiones/imagenes/estilo/patron-2-interior.png"
                  and (IMG / "estilo" / "patron-2-interior.png").exists()
                  and not (IMG / "estilo" / "patron-2-interior-codex.png").exists(), "aprobar la lámina 2 la renombra")
        L2 = datos()["laminas"][1]
        comprobar(L2["imagen"] == "/img/estilo/patron-2-interior.png" and L2["revision"]["estado"] == "aprobada",
                  "la lámina 2 renombrada sigue aprobada")
    finally:
        fijar_raiz(real)
        shutil.rmtree(tmp, ignore_errors=True)

    print("AUTOPRUEBA:", "OK" if not fallos else f"{len(fallos)} FALLOS")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if "--autoprueba" in sys.argv[1:]:
        sys.exit(autoprueba())
    print(__doc__)
