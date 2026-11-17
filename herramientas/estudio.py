"""El Estudio de la Biblia narrada: servidor local para ver, revisar, editar prompts y generar las imágenes.

    python -I herramientas/estudio.py [--puerto 8766] [--sin-capa]
    python -I herramientas/estudio.py --autoprueba     # con un capa-ia falso y un repo temporal: no genera ni gasta

Solo en 127.0.0.1; no se publica (ni la PWA ni sw.js lo tocan). Toda generación pasa por capa-ia; el token de
capa-ia lo usa su cliente Python aquí y nunca llega al navegador. `--sin-capa`: no arranca `capa-ia servir` y no
deja generar (para pruebas); leer el registro y la cuota sí (no gasta).
"""
import argparse, datetime, json, os, pathlib, shutil, subprocess, sys, threading, time, types, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import imagenes as I  # noqa: E402
import estudio_datos as D  # noqa: E402

CODIGO = pathlib.Path(__file__).resolve().parent
ESTATICOS = CODIGO / "estudio"
PUERTO = 8766
MAX_CUERPO = 64 * 1024


TIPOS = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".js": "text/javascript; charset=utf-8", ".json": "application/json; charset=utf-8",
         ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon", ".txt": "text/plain; charset=utf-8"}
MARCADOR = """<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Estudio · Biblia narrada</title><body style="font-family:system-ui;margin:2rem;background:#fff;color:#222">
<h1>Estudio · Biblia narrada</h1><p>El servidor está listo, pero la página todavía no existe
(<code>herramientas/estudio/index.html</code>). La API responde en <code>/api/datos</code>, <code>/api/estado</code>
y <code>/api/lote</code>.</p></body></html>"""


def _ahora():
    return datetime.datetime.now().isoformat(timespec="seconds")


def _parado_por(estado):
    return estado if estado in ("esperando_cuota", "bloqueado_coste") else "fallo"


# --------------------------------------------------------------------------- el lote
class Lote:
    """Un lote a la vez, en un hilo: una imagen tras otra vía capa-ia; para en el primer resultado que no sea ok.

    «Detener» deja terminar la imagen en curso (el cliente de capa-ia no expone cancelar) y no empieza otra.
    """

    def __init__(self, estudio):
        self.estudio = estudio
        self.cerrojo = threading.Lock()
        self.en_curso, self.actual, self.hechas, self.parado_por = False, None, [], None
        self._detener = False

    def estado(self):
        with self.cerrojo:
            return {"en_curso": self.en_curso, "actual": dict(self.actual) if self.actual else None,
                    "hechas": [dict(h) for h in self.hechas], "parado_por": self.parado_por}

    def actual_id(self):
        with self.cerrojo:
            return self.actual["id"] if self.en_curso and self.actual else None

    def iniciar(self, n=None, ids=None, regenerar=False):
        with self.cerrojo:
            if self.en_curso:
                return False
            self.en_curso, self.actual, self.hechas, self.parado_por = True, None, [], None
            self._detener = False
        threading.Thread(target=self._correr, args=(n, ids, regenerar), daemon=True, name="lote").start()
        return True

    def detener(self):
        with self.cerrojo:
            self._detener = True
            return self.en_curso

    def _ejecutar(self, trabajo, intervalo=1.0):
        with self.cerrojo:
            self.actual = {"id": trabajo["etiqueta"], "desde": _ahora()}
        try:
            return self.estudio.capa.ejecutar(trabajo)
        finally:
            with self.cerrojo:
                self.actual = None

    def _anotar(self, t, r):
        h = {"id": t.get("id") or r.get("etiqueta"), "estado": r.get("estado"), "motivo": r.get("motivo"),
             "segundos": r.get("segundos"), "reinicio_en": r.get("reinicio_en"), "proveedor": r.get("proveedor"),
             "cuota_antes": r.get("cuota_antes"), "cuota_despues": r.get("cuota_despues"), "fecha": _ahora()}
        with self.cerrojo:
            self.hechas.append(h)

    def _correr(self, n, ids, regenerar):
        parado = None
        detener = lambda: self._detener  # noqa: E731
        try:
            if ids is not None:
                for id_ in ids:
                    if self._detener:
                        parado = "detenido"
                        break
                    if regenerar:
                        t = next((x for x in I.pendientes(I.leer(I.F / "estilo.json")) if x["id"] == id_), None)
                        if t is None or t["bloqueo"]:
                            self._anotar({"id": id_}, {"estado": "saltado",
                                                       "motivo": "id desconocido" if t is None else t["bloqueo"]})
                            continue
                        D.apartar_para_regenerar(id_)
                    res = I.generar_lote(1, ids=[id_], ejecutar=self._ejecutar, al_progreso=self._anotar,
                                         detener=detener)
                    if res and res[-1].get("estado") not in ("ok", "saltado"):
                        parado = _parado_por(res[-1].get("estado"))
                        break
            else:
                res = I.generar_lote(n, ejecutar=self._ejecutar, al_progreso=self._anotar, detener=detener)
                if res and res[-1].get("estado") != "ok":
                    parado = _parado_por(res[-1].get("estado"))
                elif self._detener and len(res) < n:
                    parado = "detenido"
        except Exception as e:  # noqa: BLE001 — el lote se para y lo dice; no se reintenta
            self._anotar({"id": self.actual_id()}, {"estado": "fallo", "motivo": f"{type(e).__name__}: {e}"})
            parado = "fallo"
        with self.cerrojo:
            self.en_curso, self.actual = False, None
            self.parado_por = parado or "terminado"


# --------------------------------------------------------------------------- estado de capa-ia
def _fecha(s):
    """ISO (con Z o sin zona = hora local) → datetime con zona; None si no se entiende."""
    try:
        d = datetime.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.astimezone()


def _tope_biblia():
    try:
        return json.loads((D.RAIZ / "capa-ia.json").read_text(encoding="utf-8")).get("tope_semanal_pct", 30)
    except (OSError, ValueError, AttributeError):
        return 30


class Estudio:
    def __init__(self, capa, generar=True, aviso=None):
        self.capa, self.generar, self.aviso = capa, generar, aviso
        self.lote = Lote(self)

    def datos(self):
        aviso = None
        try:
            reg = self.capa.registro(app=I.APP)
        except Exception as e:  # noqa: BLE001
            reg, aviso = None, f"No se pudo leer el registro de capa-ia ({e}); solo se muestra el historial viejo."
        d = D.datos(reg)
        if aviso:
            d["aviso"] = aviso
        return d

    def estado(self):
        avisos = [self.aviso] if self.aviso else []
        try:
            modo = self.capa.modo()
        except Exception:  # noqa: BLE001
            modo = "cli"
        cuota, inicio = None, None
        try:
            cx = ((self.capa.estado() or {}).get("cuotas") or {}).get("codex")
        except Exception as e:  # noqa: BLE001
            cx = None
            avisos.append(f"No se pudo leer el estado de capa-ia: {e}")
        if cx:
            sem = cx.get("semanal") or {}
            # usado_pct/reinicio_en son de la ventana MÁS LLENA (5 h o semanal): ventana_min dice cuál es
            cuota = {"usado_pct": cx.get("usado_pct"), "semanal_pct": sem.get("pct"),
                     "reinicio_en": cx.get("reinicio_en"), "ventana_min": cx.get("ventana_min"),
                     "semanal_reinicio_en": sem.get("reinicio_en"), "leida": cx.get("at")}
            fin = _fecha(sem.get("reinicio_en")) if sem.get("reinicio_en") else None
            inicio = fin - datetime.timedelta(minutes=sem.get("ventana_min") or 10080) if fin else None
        elif not avisos:
            avisos.append("La cuota de Codex no se pudo leer: capa-ia no lanzará Codex hasta que se lea.")
        inicio = inicio or datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
        gasto = None
        try:
            filas = self.capa.registro(app=I.APP, desde=inicio.isoformat(timespec="seconds"))
            gasto = round(sum(f["costo_estimado"] for f in filas
                              if f.get("app") == I.APP and isinstance(f.get("costo_estimado"), (int, float))
                              and (_fecha(f.get("fecha")) or inicio) >= inicio), 2)
        except Exception as e:  # noqa: BLE001
            avisos.append(f"No se pudo leer el registro de capa-ia: {e}")
        r = {"capa": modo, "cuota": cuota, "gasto_biblia_semana_pct": gasto, "tope_biblia_pct": _tope_biblia(),
             "generar": self.generar}
        if avisos:
            r["aviso"] = " ".join(avisos)
        return r


# --------------------------------------------------------------------------- HTTP
def _dentro(base, rel):
    """Archivo `rel` (ya decodificado) dentro de `base`, o None: sin «..», sin rutas absolutas ni de unidad."""
    if not rel or "\\" in rel or ":" in rel or "\x00" in rel or rel.startswith("/"):
        return None
    partes = rel.split("/")
    if any(p in ("", ".", "..") for p in partes):
        return None
    base = base.resolve()
    p = (base / rel).resolve()
    try:
        p.relative_to(base)
    except ValueError:
        return None
    return p if p.is_file() else None


class Manejador(BaseHTTPRequestHandler):
    server_version = "EstudioBiblia/1"
    protocol_version = "HTTP/1.1"

    def log_message(self, formato, *args):
        if self.server.registrar:
            sys.stderr.write(f"{self.log_date_time_string()} {formato % args}\n")

    # -- respuestas
    def _enviar(self, codigo, cuerpo, tipo):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(cuerpo)

    def _json(self, codigo, obj):
        self._enviar(codigo, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _archivo(self, p):
        if p is None:
            return self._json(404, {"error": "no encontrado"})
        tipo = TIPOS.get(p.suffix.lower())
        if tipo is None:
            return self._json(404, {"error": "no encontrado"})
        self._enviar(200, p.read_bytes(), tipo)

    def _permitido(self):
        hosts = self.server.hosts
        error = None
        if self.headers.get("Host", "") not in hosts:
            error = "Host no permitido"
        elif self.headers.get("Origin") is not None and self.headers["Origin"] not in {f"http://{h}" for h in hosts}:
            error = "Origen no permitido"  # otra página del navegador no puede mandar trabajos al Estudio
        if error:
            self.close_connection = True  # el cuerpo, si lo hay, no se lee
            self._json(403, {"error": error})
            return False
        return True

    def _cuerpo(self):
        """El JSON del cuerpo (dict) o None si ya se respondió con el error."""
        if not self.headers.get("Content-Type", "").split(";")[0].strip().lower() == "application/json":
            self.close_connection = True
            self._json(415, {"error": "El cuerpo debe ser JSON (Content-Type: application/json)"})
            return None
        try:
            largo = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            largo = -1
        if largo < 0 or largo > MAX_CUERPO:
            self.close_connection = True
            self._json(413, {"error": f"Cuerpo de más de {MAX_CUERPO // 1024} KB"})
            return None
        try:
            obj = json.loads(self.rfile.read(largo).decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            self._json(400, {"error": "JSON inválido"})
            return None
        if not isinstance(obj, dict):
            self._json(400, {"error": "Se espera un objeto JSON"})
            return None
        return obj

    # -- rutas
    def do_GET(self):
        if not self._permitido():
            return
        ruta = urllib.parse.urlsplit(self.path).path
        est = self.server.estudio
        try:
            if ruta in ("/", "/index.html"):
                p = ESTATICOS / "index.html"
                return self._archivo(p) if p.is_file() else self._enviar(200, MARCADOR.encode("utf-8"), TIPOS[".html"])
            if ruta.startswith("/estudio/"):
                return self._archivo(_dentro(ESTATICOS, urllib.parse.unquote(ruta[len("/estudio/"):])))
            if ruta.startswith("/img/"):
                p = _dentro(D.IMG, urllib.parse.unquote(ruta[len("/img/"):]))
                return self._archivo(p if p is not None and p.suffix.lower() == ".png" else None)
            if ruta == "/api/datos":
                return self._json(200, est.datos())
            if ruta == "/api/estado":
                return self._json(200, est.estado())
            if ruta == "/api/lote":
                return self._json(200, est.lote.estado())
        except Exception as e:  # noqa: BLE001
            return self._json(500, {"error": f"{type(e).__name__}: {e}"})
        self._json(404, {"error": "no encontrado"})

    do_HEAD = do_GET

    def do_POST(self):
        if not self._permitido():
            return
        ruta = urllib.parse.urlsplit(self.path).path
        if ruta not in ("/api/revision", "/api/prompt", "/api/generar", "/api/lote/detener"):
            self.close_connection = True
            return self._json(404, {"error": "no encontrado"})
        c = self._cuerpo()
        if c is None:
            return
        est = self.server.estudio
        try:
            if ruta == "/api/revision":
                # Aprobar la lámina 2 provisional la renombra, y todo trabajo del lote la lleva adjunta por su
                # ruta: con un lote en curso no se renombra (409). El cerrojo del lote impide que uno empiece
                # entre la comprobación y el renombrado.
                with est.lote.cerrojo:
                    if est.lote.en_curso and D.renombraria(c.get("id"), c.get("estado")):
                        return self._json(409, {"ok": False, "error": D.MOTIVO_NO_RENOMBRAR})
                    try:
                        return self._json(200, D.marcar(c.get("id"), c.get("estado"), c.get("nota") or ""))
                    except ValueError as e:
                        return self._json(400, {"ok": False, "error": str(e)})
            if ruta == "/api/prompt":
                if est.lote.actual_id() and est.lote.actual_id() == c.get("id"):
                    return self._json(409, {"ok": False, "errores": [
                        f"{c.get('id')}: se está generando ahora; espera a que termine para editar su prompt"]})
                r = D.editar_prompt(c.get("id"), c.get("campo"), c.get("valor"))
                return self._json(200 if r["ok"] else 400, r)
            if ruta == "/api/generar":
                return self._generar(est, c)
            if ruta == "/api/lote/detener":
                return self._json(200, {"ok": True, "en_curso": est.lote.detener()})
        except Exception as e:  # noqa: BLE001
            return self._json(500, {"ok": False, "error": f"{type(e).__name__}: {e}"})

    def _generar(self, est, c):
        if not est.generar:
            return self._json(403, {"ok": False, "error": "Arrancado con --sin-capa: no se genera nada."})
        ids, n, regenerar = c.get("ids"), c.get("n"), c.get("regenerar", False)
        if ids is not None:
            if (not isinstance(ids, list) or not ids or len(ids) > 200
                    or not all(isinstance(x, str) and x for x in ids)):
                return self._json(400, {"ok": False, "error": "ids: lista de ids (texto), de 1 a 200"})
            n = None
        elif not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= 200:
            return self._json(400, {"ok": False, "error": "Hace falta n (1 a 200) o ids"})
        if not isinstance(regenerar, bool):
            return self._json(400, {"ok": False, "error": "regenerar: true o false"})
        if not est.lote.iniciar(n=n, ids=ids, regenerar=regenerar):
            return self._json(409, {"ok": False, "error": "Ya hay un lote en curso"})
        self._json(202, {"ok": True, "lote": est.lote.estado()})

    def _no_permitido(self):
        if self._permitido():
            self.close_connection = True
            self._json(405, {"error": "método no permitido"})

    do_PUT = do_DELETE = do_PATCH = do_OPTIONS = _no_permitido


def crear_servidor(puerto=PUERTO, capa=None, generar=True, aviso=None, registrar=False):
    """Servidor en 127.0.0.1:`puerto` (0 = uno libre) con el Estudio; aún sin servir (`serve_forever`)."""
    srv = ThreadingHTTPServer(("127.0.0.1", puerto), Manejador)
    srv.daemon_threads = True
    p = srv.server_address[1]
    srv.hosts = {f"127.0.0.1:{p}", f"localhost:{p}"}
    srv.estudio = Estudio(capa or I.capa(), generar=generar, aviso=aviso)
    srv.registrar = registrar
    return srv


def arrancar_capa(capa):
    """Si capa-ia no responde por HTTP, lanza `capa-ia servir` aparte (sigue tras cerrar el Estudio) y espera 10 s.

    Devuelve None si quedó en HTTP, o el aviso para /api/estado si sigue en CLI.
    """
    try:
        if capa.modo() == "http":
            return None
    except Exception:  # noqa: BLE001
        pass
    repo = os.environ.get("CAPA_IA_REPO", r"C:\PROYECTOS IA\capa-ia")
    cmd = [shutil.which("node") or "node", os.path.join(repo, "bin", "capa-ia.mjs"), "servir"]
    extra = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS}  # sin consola
             if sys.platform == "win32" else {"start_new_session": True})
    try:
        subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         close_fds=True, **extra)
    except OSError as e:
        return f"No se pudo arrancar capa-ia servir ({e}): se usa la CLI de capa-ia."
    fin = time.time() + 10
    while time.time() < fin:
        time.sleep(0.5)
        try:
            if capa.modo() == "http":
                return None
        except Exception:  # noqa: BLE001
            pass
    return "capa-ia servir no respondió en 10 s: se usa la CLI de capa-ia (sin cola compartida con otras apps)."


# --------------------------------------------------------------------------- autoprueba
def capa_falsa():
    """capa_ia falso: escribe PNG de 16×9 o devuelve el estado que se le pida. Nunca llama a nada real."""
    m = types.ModuleType("capa_ia")

    class CapaIAError(Exception):
        def __init__(self, codigo, resultado):
            super().__init__(f"capa-ia terminó con código {codigo}")
            self.codigo, self.resultado = codigo, resultado

    m.CapaIAError = CapaIAError
    m.llamadas = []
    m.conducta = {"estado": "ok", "falla": set(), "espera": None}
    ahora = datetime.datetime.now(datetime.timezone.utc)
    m.filas = [{"fecha": (ahora - datetime.timedelta(hours=h)).isoformat(timespec="seconds"), "id": f"r{h}",
                "app": "biblia", "etiqueta": "personajes/jose", "tipo": "imagen", "proveedor": "codex",
                "prompt": "…", "estado": "ok", "segundos": 60, "cuota_antes": 4, "cuota_despues": 5,
                "costo_estimado": 0.2} for h in (1, 2)]
    m.modo = lambda: "http"
    m.estado = lambda: {"cuotas": {"codex": {
        "proveedor": "codex", "usado_pct": 12, "reinicio_en": "2026-11-17T15:00:00.000Z", "ventana_min": 300,
        "semanal": {"pct": 5, "reinicio_en": (ahora + datetime.timedelta(days=5)).isoformat(),
                    "ventana_min": 10080}, "at": ahora.isoformat()}, "claude": None}}
    m.registro = lambda app=None, desde=None: [f for f in m.filas if not app or f["app"] == app]

    def ejecutar(trabajo, intervalo=1.0):
        m.llamadas.append(trabajo)
        if m.conducta["espera"] is not None:
            m.conducta["espera"].wait(10)
        base = {"id": f"falso-{len(m.llamadas)}", "proveedor": "codex", "segundos": 0.1, "etiqueta": trabajo["etiqueta"],
                "archivos": [], "motivo": None, "reinicio_en": None}
        if trabajo["etiqueta"] in m.conducta["falla"]:
            raise CapaIAError(1, dict(base, estado="fallo", motivo="falló a propósito (prueba)"))
        if m.conducta["estado"] != "ok":
            return dict(base, estado=m.conducta["estado"], motivo="cuota (prueba)", reinicio_en="2026-11-22T10:00:00Z")
        p = pathlib.Path(trabajo["salida"])
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(I._png_falso())
        return dict(base, estado="ok", archivos=[str(p)], cuota_antes=5, cuota_despues=5)
    m.ejecutar = ejecutar
    return m


def autoprueba():
    import http.client
    falso = capa_falsa()
    sys.modules["capa_ia"] = falso  # antes de cualquier uso de capa_ia
    real = D.RAIZ
    fallos = []

    def comprobar(cond, msg):
        print(("  ✓ " if cond else "  ✗ ") + msg)
        if not cond:
            fallos.append(msg)

    tmp = D.copia_temporal("estudio servidor é ")
    srv = None
    try:
        D.fijar_raiz(tmp)
        srv = crear_servidor(0, capa=falso)
        puerto = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()

        def pedir(metodo, ruta, cuerpo=None, host=None, tipo="application/json", crudo=None, extra=None):
            c = http.client.HTTPConnection("127.0.0.1", puerto, timeout=60)
            cab = {"Host": host or f"127.0.0.1:{puerto}"}
            datos_ = crudo if crudo is not None else (None if cuerpo is None else json.dumps(cuerpo).encode())
            if datos_ is not None:
                cab["Content-Type"] = tipo
            cab.update(extra or {})
            c.request(metodo, ruta, body=datos_, headers=cab)
            r = c.getresponse()
            b = r.read()
            c.close()
            try:
                return r.status, json.loads(b.decode("utf-8")), r
            except ValueError:
                return r.status, b, r

        def esperar_lote():
            for _ in range(200):
                s, L, _r = pedir("GET", "/api/lote")
                if not L["en_curso"]:
                    return L
                time.sleep(0.05)
            return L

        s, b, r = pedir("GET", "/")
        comprobar(s == 200 and r.getheader("Content-Type", "").startswith("text/html"), "GET / → 200 html")
        comprobar(isinstance(b, bytes) and b"/estudio/estudio.js" in b and b"/estudio/estudio.css" in b,
                  "GET / sirve la página del Estudio (index.html con su JS y su CSS)")
        for ruta, tipo in (("/estudio/estudio.js", "text/javascript"), ("/estudio/estudio.css", "text/css")):
            s, b, r = pedir("GET", ruta)
            comprobar(s == 200 and r.getheader("Content-Type", "").startswith(tipo) and len(b) > 1000,
                      f"GET {ruta} → 200 {tipo}")
        for ruta in ("/img/../CLAUDE.md", "/img/%2e%2e/CLAUDE.md", "/img/..%5C..%5CCLAUDE.md", "/img/C:/Windows/win.ini",
                     "/img/C%3A/Windows/win.ini", "/img//etc/passwd", "/estudio/../estudio.py", "/img/personajes/jose.json",
                     "/estudio/%2e%2e/imagenes.py"):
            s, b, r = pedir("GET", ruta)
            comprobar(s == 404, f"{ruta} → 404 ({s})")
        s, b, r = pedir("GET", "/img/personajes/jose.png")
        comprobar(s == 200 and r.getheader("Content-Type") == "image/png" and b[:8] == b"\x89PNG\r\n\x1a\n",
                  "imagen servida desde una raíz con espacios y «é»")
        s, b, r = pedir("GET", "/api/datos", host="evil.com")
        comprobar(s == 403, "Host: evil.com → 403")
        s, b, r = pedir("GET", "/api/datos", host=f"localhost:{puerto}")
        comprobar(s == 200, "Host: localhost:<puerto> → 200")
        comprobar(r.getheader("Access-Control-Allow-Origin") is None, "sin CORS")
        s, b, r = pedir("POST", "/api/revision", {"id": "personajes/jose", "estado": "aprobada"},
                        extra={"Origin": "http://evil.com"})
        comprobar(s == 403, "POST con Origin ajeno → 403")
        s, b, r = pedir("POST", "/api/revision", crudo=b'{"id": "personajes/jose", "estado": "aprobada"}',
                        tipo="text/plain")
        comprobar(s == 415, "POST sin JSON (text/plain) → 415")
        s, b, r = pedir("POST", "/api/prompt", crudo=b"{" + b" " * (MAX_CUERPO + 1) + b"}")
        comprobar(s == 413, "cuerpo > 64 KB → 413")

        s, d, r = pedir("GET", "/api/datos")
        comprobar(s == 200 and all(k in d for k in ("estilo", "laminas", "personajes", "escenarios", "pasajes"))
                  and len(d["personajes"]) == 3, "/api/datos 200 con los grupos")
        jose = next(x for x in d["personajes"] if x["id"] == "personajes/jose")
        comprobar(sum(1 for h in jose["historial"] if h.get("id") in ("r1", "r2")) == 2
                  and any(h.get("origen") == I.ORIGEN_VIEJO for h in jose["historial"]),
                  "historial: filas de capa-ia y la vieja")
        s, e, r = pedir("GET", "/api/estado")
        comprobar(s == 200 and e["capa"] == "http" and e["cuota"]["usado_pct"] == 12 and e["cuota"]["semanal_pct"] == 5
                  and e["cuota"]["reinicio_en"] and e["cuota"]["leida"], f"/api/estado: cuota de Codex ({e.get('cuota')})")
        comprobar(e["cuota"]["ventana_min"] == 300, "I1: la cuota dice de qué ventana es la más llena (300 = 5 h)")
        estado_falso = falso.estado
        falso.estado = lambda: {"cuotas": {"codex": {
            "proveedor": "codex", "usado_pct": 40, "reinicio_en": "2026-11-21T10:00:00.000Z", "ventana_min": 10080,
            "semanal": {"pct": 40, "reinicio_en": "2026-11-21T10:00:00.000Z", "ventana_min": 10080},
            "at": "2026-11-17T12:00:00Z"}}}
        s, e2, r = pedir("GET", "/api/estado")
        comprobar(s == 200 and e2["cuota"]["usado_pct"] == 40 and e2["cuota"]["ventana_min"] == 10080
                  and e2["cuota"]["reinicio_en"] == "2026-11-21T10:00:00.000Z",
                  "I1: si la semanal es la más llena, ventana_min = 10080 (no se rotula «5 h»)")
        falso.estado = estado_falso
        comprobar(e["gasto_biblia_semana_pct"] == 0.4 and e["tope_biblia_pct"] == 30, "gasto de la Biblia ≈ 0,4 % de 30 %")
        comprobar("token" not in json.dumps(e).lower(), "el estado no lleva el token")

        s, b, r = pedir("POST", "/api/prompt", {"id": "personajes/jose", "campo": "prompt_en",
                                                 "valor": jose["prompt_en"] + " A halo."})
        comprobar(s == 400 and not b["ok"] and any("halo" in x for x in b["errores"]), "POST /api/prompt inválido → 400")
        s, b, r = pedir("POST", "/api/revision", {"id": "personajes/jose", "estado": "rechazada", "nota": "toga"})
        comprobar(s == 200 and b["ok"], "POST /api/revision → 200")
        # el fixture no tiene tomas (imágenes falsas de tamaño fijo): los ids esperados salen de las fuentes
        pend = I.pendientes(I.leer(I.F / "estilo.json"))
        tomas = [t["id"] for t in pend if not t["id"].startswith(("estilo/", "personajes/", "escenarios/"))]
        con_hermanos = next(t["id"] for t in pend if D.IMG / "personajes" / "hermanos.png" in t["refs"])
        s, b, r = pedir("POST", "/api/revision", {"id": tomas[0], "estado": "aprobada"})
        comprobar(s == 400, "revisar sin imagen → 400")

        # lote de 2
        s, b, r = pedir("POST", "/api/generar", {"n": 2})
        comprobar(s == 202, "POST /api/generar {n: 2} → 202")
        L = esperar_lote()
        comprobar([h["estado"] for h in L["hechas"]] == ["ok", "ok"] and L["parado_por"] == "terminado"
                  and [h["id"] for h in L["hechas"]] == tomas[:2], f"lote de 2 → 2 ok ({L})")
        comprobar(all(D.imagen_actual(i) for i in tomas[:2]), "las imágenes quedan en su sitio")

        # esperando cuota (foco 4)
        falso.llamadas.clear()
        falso.conducta["estado"] = "esperando_cuota"
        pedir("POST", "/api/generar", {"n": 3})
        L = esperar_lote()
        comprobar(L["parado_por"] == "esperando_cuota" and len(falso.llamadas) == 1
                  and L["hechas"][0]["reinicio_en"] == "2026-11-22T10:00:00Z",
                  "esperando_cuota → para, con reinicio_en y una sola llamada")
        falso.conducta["estado"] = "bloqueado_coste"
        pedir("POST", "/api/generar", {"n": 3})
        comprobar(esperar_lote()["parado_por"] == "bloqueado_coste", "bloqueado_coste → para")
        falso.conducta["estado"] = "ok"

        # regenerar con fallo (foco 3)
        falso.conducta["falla"] = {"personajes/hermanos"}
        s, b, r = pedir("POST", "/api/generar", {"ids": ["personajes/hermanos"], "regenerar": True})
        L = esperar_lote()
        comprobar(s == 202 and L["parado_por"] == "fallo" and L["hechas"][0]["estado"] == "fallo"
                  and "propósito" in (L["hechas"][0]["motivo"] or ""), "regenerar que falla → parado_por fallo")
        s, d, r = pedir("GET", "/api/datos")
        h = next(x for x in d["personajes"] if x["id"] == "personajes/hermanos")
        comprobar(h["imagen"] is None and len(h["anteriores"]) == 1, "la imagen vieja sigue en _anteriores y datos la lista")
        s, b, r = pedir("GET", h["anteriores"][0])
        comprobar(s == 200 and b[:4] == b"\x89PNG", "la versión anterior se sirve")
        falso.conducta["falla"] = set()

        # regenerar bien: ids exactos en su orden; uno bloqueado se salta con motivo
        s, b, r = pedir("POST", "/api/generar", {"ids": [tomas[0], "personajes/benjamin"], "regenerar": True})
        L = esperar_lote()
        comprobar([(x["id"], x["estado"]) for x in L["hechas"]] == [(tomas[0], "ok"), ("personajes/benjamin", "ok")]
                  and L["parado_por"] == "terminado", "regenerar 2 ids en su orden")
        s, b, r = pedir("POST", "/api/generar", {"ids": [con_hermanos], "regenerar": True})
        L = esperar_lote()
        comprobar(L["hechas"][0]["estado"] == "saltado" and "hermanos" in L["hechas"][0]["motivo"]
                  and not any(p.name.startswith(con_hermanos.replace("/", "__") + "-") for p in D.ANTERIORES.iterdir()),
                  f"id bloqueado → saltado con motivo y sin apartar ({L['hechas'][0]['motivo']})")

        # lote en curso: 409 al generar y al editar el prompt de la imagen actual; detener tras la actual
        falso.conducta["espera"] = threading.Event()
        falso.llamadas.clear()
        s, b, r = pedir("POST", "/api/generar", {"n": 5})
        for _ in range(100):
            s, L, r = pedir("GET", "/api/lote")
            if L.get("actual"):
                break
            time.sleep(0.05)
        comprobar(L["en_curso"] and L["actual"] and L["actual"]["id"] and L["actual"]["desde"], f"actual: {L['actual']}")
        s, b, r = pedir("POST", "/api/generar", {"n": 1})
        comprobar(s == 409, "segundo POST /api/generar con lote en curso → 409")
        s, b, r = pedir("POST", "/api/prompt", {"id": L["actual"]["id"], "campo": "negativo_en",
                                                 "valor": "Do not show any bird."})
        comprobar(s == 409, "editar el prompt de la imagen en curso → 409")
        provisional = D.IMG / "estilo" / "patron-2-interior-codex.png"
        comprobar(provisional.is_file(), "el fixture tiene la lámina 2 provisional")
        s, b, r = pedir("POST", "/api/revision", {"id": "estilo/patron-2-interior", "estado": "aprobada"})
        comprobar(s == 409 and not b["ok"] and "lote en curso" in b["error"] and provisional.is_file()
                  and not (D.IMG / "estilo" / "patron-2-interior.png").exists()
                  and D.estado_revision("estilo/patron-2-interior") != "aprobada",
                  "M2: aprobar la lámina 2 con un lote en curso → 409, sin renombrar ni aprobar")
        s, b, r = pedir("POST", "/api/revision", {"id": "estilo/patron-2-interior", "estado": "rechazada",
                                                   "nota": "prueba"})
        comprobar(s == 200 and b["ok"] and provisional.is_file(), "M2: rechazarla con el lote en curso sí se puede")
        s, b, r = pedir("POST", "/api/lote/detener", {})
        comprobar(s == 200, "POST /api/lote/detener → 200")
        falso.conducta["espera"].set()
        L = esperar_lote()
        comprobar(L["parado_por"] == "detenido" and len(falso.llamadas) == 1, "detener: termina tras la actual")
        falso.conducta["espera"] = None
        s, b, r = pedir("POST", "/api/revision", {"id": "estilo/patron-2-interior", "estado": "aprobada"})
        comprobar(s == 200 and b.get("renombrada") == "guiones/imagenes/estilo/patron-2-interior.png"
                  and not provisional.exists(), "M2: sin lote en curso, aprobar la lámina 2 la renombra")

        s, b, r = pedir("POST", "/api/generar", {})
        comprobar(s == 400, "generar sin n ni ids → 400")
        srv.estudio.generar = False
        s, b, r = pedir("POST", "/api/generar", {"n": 1})
        comprobar(s == 403, "con --sin-capa no se genera (403)")
        s, b, r = pedir("GET", "/api/nada")
        comprobar(s == 404, "ruta desconocida → 404")
    finally:
        if srv:
            srv.shutdown()
            srv.server_close()
        D.fijar_raiz(real)
        shutil.rmtree(tmp, ignore_errors=True)

    print("AUTOPRUEBA:", "OK" if not fallos else f"{len(fallos)} FALLOS")
    return 1 if fallos else 0


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=PUERTO)
    ap.add_argument("--sin-capa", action="store_true", help="no arranca capa-ia ni deja generar (pruebas)")
    ap.add_argument("--autoprueba", action="store_true")
    a = ap.parse_args(argv)
    if a.autoprueba:
        return autoprueba()
    capa = I.capa()
    if a.sin_capa:
        aviso = "Arrancado con --sin-capa: no se genera nada desde el Estudio."
    else:
        aviso = arrancar_capa(capa)
    srv = crear_servidor(a.puerto, capa=capa, generar=not a.sin_capa, aviso=aviso, registrar=True)
    print(f"Estudio · Biblia narrada en http://127.0.0.1:{srv.server_address[1]}/  (Ctrl+C para salir)", flush=True)
    if aviso:
        print("Aviso:", aviso, flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
