# capa-ia y el Estudio de la Biblia narrada — diseño

Fecha: 2026-11-17 · Estado: borrador para aprobación del usuario.
Este documento vive en el repo de la Biblia mientras `capa-ia` no exista; al crear el repo se copia a
`capa-ia/docs/diseño.md` y aquí queda solo la parte del Estudio con un enlace.

Certeza de los datos: **[M]** medido en este equipo · **[L]** leído en código o documento (con ruta) ·
**[O]** documentación oficial (URL y fecha) · **[I]** inferido · **[D]** decisión del usuario · **[C]** decisión
del diseñador (corregible).

---

## 1. Intención

El usuario quiere dos cosas, en este orden:

1. **capa-ia**: una capa de IA local y reutilizable que se instala en un equipo y cualquier app suya
   (Python, Node, Electron, JUCE) puede usar para pedir trabajos de IA —texto, imágenes y, más adelante,
   tareas de código—. La capa mira qué hay en el equipo (herramientas, sesiones, cuota, GPU) y elige con qué
   hacerlo, usando **solo sus suscripciones y la cuota del plan, sin gasto adicional** [D].
2. **El Estudio de la Biblia narrada**: un panel local donde se ve todo lo de los guiones —láminas, hojas de
   personaje y de escenario, tomas, prompts, imágenes y su revisión— y desde donde se maneja la generación,
   que pasa por capa-ia [D].

Por qué así: el motor de ejecución ya existe y está probado dentro de Orchestrator (adaptadores de Codex,
Claude y Cursor, regla de coste cero, detección de cuota agotada). Orchestrator se dejó de usar por la
ceremonia que lo rodeaba, no por ese motor [L: `docs/audits/2026-10-20-auditoria-estrategica/00-RESUMEN-EJECUTIVO.md`].
El usuario quiere **volver a aprovechar Orchestrator** [D]: su motor pasa a ser capa-ia y, más adelante,
Orchestrator vuelve como tablero que lee el registro común.

## 2. Objetivos, no objetivos y anti-objetivos

**Objetivos**
- Una sola forma de pedir IA desde cualquier app del usuario, por CLI y por HTTP local.
- Elección automática del proveedor y del modelo según lo instalado, la sesión, la cuota y el hardware.
- Gasto adicional cero garantizado por reglas duras (no por confirmaciones a mano).
- Todo trabajo queda registrado con su prompt, proveedor, resultado, tiempo y cuota: es lo que se muestra.
- Primera app cliente: la Biblia (imágenes de guiones), con su Estudio.

**No objetivos (por ahora)**
- Tareas de código sobre repos (lo que hacía Play): fase 5, después de que texto e imagen funcionen.
- Video y lipsync: Higgsfield sigue a mano en la web [D, CLAUDE.md].
- Migrar Orchestrator a capa-ia: fase 6, aparte.
- Editar prompts desde el Estudio (v1 solo los muestra; se editan en los JSON de `guiones/fuentes/`).

**Anti-objetivos (si pasa esto, fracasó aunque funcione)**
- Cualquier gasto fuera de la cuota del plan: clave de API, créditos, recarga, restablecimientos de límite.
- Un proxy que reexponga las suscripciones como API para terceros o fuera del equipo (prohibido por los
  términos; ver §4).
- Volver a la ceremonia de Orchestrator: misiones registradas, confirmar cada ejecución, autorizaciones por
  paso, sprints con ADR por cada cambio. Las reglas se declaran una vez por app.
- Datos inventados en el Estudio: lo que no está en los archivos no se muestra.

## 3. Lo que hay en este equipo (2026-11-17)

| Qué | Estado | Certeza |
|---|---|---|
| Codex CLI 0.163.0, sesión ChatGPT, plan `prolite` (Pro 100) | sesión activa; solo ventana semanal (10 080 min); 0 créditos; 3 restablecimientos disponibles (no se usan) | [M] |
| Cuota Codex antes de lanzar | `codex app-server` (JSON-RPC por stdio): `initialize` + `account/rateLimits/read` → `usedPercent`, `resetsAt`, `credits`, `spendControlReached`, `rateLimitReachedType`; ~2 s, no llama al modelo | [M] |
| Cuota Codex después de cada llamada | evento `token_count` de los rollouts en `~/.codex/sessions/…/*.jsonl`, campo `rate_limits` | [M] |
| Costo de las 10 imágenes del 16-nov | uso semanal 1 % → 2 % (el CLI informa enteros) ⇒ ~0,1–0,2 % por imagen | [C]álculo |
| Claude Code 2.1.319, plan Max 5x | `claude auth status --json` da plan y método, no cuota | [M] |
| Cuota Claude | solo llega al script de statusline (`rate_limits.five_hour/seven_day.used_percentage`, `resets_at`) tras la primera respuesta de una sesión | [O] https://code.claude.com/docs/en/statusline, leído 2026-11-17 |
| LM Studio | instalado, servidor apagado; modelos: llama-3.2-1b, mistral-small-3.2-24b, gpt-oss-20b, qwen3-30b-a3b-instruct-2507, nomic-embed (embeddings) | [M] |
| Ollama | instalado, servicio no levantado, sin modelos listados | [M] |
| Cursor, Gemini, Copilot, Antigravity CLI | no instalados en PATH | [M] |
| Hardware | RTX 5060 Ti 16 GB VRAM · 63 GB RAM · Ryzen 7 7700X | [M] |
| Modelos locales que caben | hasta ~14 B Q4 enteros en VRAM; 20 B justos; 24–30 B (MoE incluidos) con parte en RAM, más lentos | [I] |
| Node | v24.15.0 instalado; el código a copiar exige ≥ 18 | [M]/[L] |

## 4. Reglas externas que el diseño respeta

De la investigación del 4-nov-2026 [L: Orchestrator `docs/audits/2026-11-04-integrador-suscripciones/00-INFORME.md:36-46,102-115`]:

| Proveedor | Permitido | Prohibido |
|---|---|---|
| OpenAI (Codex) | lanzar `codex` / `codex app-server` con el login que gestiona el binario; leer la cuota por `account/rateLimits/read` | usar esa autenticación en servicios comerciales o alojados |
| Anthropic (Claude) | lanzar `claude` sin modificar con el login propio; leer la cuota del statusline o del `stream-json` | enrutar peticiones con credenciales de suscripción, leer el token de `~/.claude`, routers tipo proxy, SDK con login de suscripción. **Zona gris**: flotas de `claude -p` en paralelo y sin supervisión |
| Google (Antigravity) | uso interactivo | software de terceros para acceder (suspensiones desde feb-2026): **no se integra** |
| Cursor | `-p --mode ask` (solo lectura) con su sesión | — (no instalado hoy) |

Consecuencias de diseño:
- capa-ia **siempre lanza los binarios oficiales** con la sesión que ellos gestionan; nunca lee credenciales ni
  habla con las APIs de los proveedores.
- El HTTP escucha solo en `127.0.0.1`, exige token y **no imita la API de OpenAI ni de Anthropic** (no es un
  endpoint `/v1/chat/completions`): es una cola de trabajos para las apps del propio usuario en su equipo [I:
  esto queda dentro de «uso local personal»; si el usuario quisiera exponerlo a otra persona o a la red, se
  vuelve un proxy prohibido].
- Claude: concurrencia 1 y nunca en lotes desatendidos largos por defecto (§7.3).

## 5. Enfoques considerados

- **A · Repo nuevo `capa-ia`, copiando el motor de Orchestrator (elegido por el usuario [D]).** Proceso
  liviano, sin sprints ni ADR. Orchestrator conserva su copia hasta la fase 6, cuando pasa a importar capa-ia.
- B · Paquete `core/` dentro de Orchestrator. Una sola fuente desde el día uno, pero cada cambio hereda el
  proceso de Orchestrator, que es lo que frenaba. Descartado.
- C · Reescribir en Python (como las herramientas de la Biblia). Perdería ~1 300 líneas probadas y las
  mediciones con fecha que contienen. Descartado; Python se atiende con un cliente fino (§8.3).

## 6. Arquitectura de capa-ia

Repo `C:\PROYECTOS IA\capa-ia`, Node ≥ 20 ESM, **sin dependencias npm**, Windows primero (lo Windows-específico
aislado, Linux/Mac sin probar).

```
capa-ia/
  bin/capa-ia.mjs              CLI
  src/nucleo/ejecutores.js     copia recortada de Orchestrator src/shared/executors/nucleo.js
  src/nucleo/proceso.js        copia de src/main/executors/proceso.js (spawn, topes, matar árbol)
  src/proveedores/codex.js     adaptador (copia de src/main/executors/codex.js) + cuota por app-server
  src/proveedores/claude.js    adaptador (copia de claude.js)
  src/proveedores/cursor.js    adaptador (copia de cursor.js; inactivo si no está instalado)
  src/proveedores/ollama.js    copia de src/main/llm/provider.js + adaptador de trabajo
  src/proveedores/lmstudio.js  nuevo: `lms` + API local compatible en 127.0.0.1:1234
  src/equipo.js                detección: binarios, sesiones, coste, GPU/VRAM, modelos locales
  src/cuota.js                 lectura y caché de cuota por proveedor
  src/elegir.js                elección de proveedor y modelo (explicada)
  src/trabajos.js              ejecución de un trabajo: preparar → lanzar → leer salida → estado final
  src/registro.js              registro JSONL
  src/config.js                config de equipo y de app, con validación
  src/servidor.js              HTTP local
  clientes/python/capa_ia.py   cliente Python de stdlib
  pruebas/                     suites sin cuota, con ejecutables falsos
  docs/                        este diseño, LEEME, reglas medidas con fecha
```

### 6.1 Qué se copia de Orchestrator y qué no [L: inventario del 17-nov]

- `nucleo.js` (1 876 líneas) → queda en ~1 300. Se conservan **íntegros**: catálogo de ejecutores, coste y
  sesión (`metodoDeLoginCodex`, `loginDeClaude`, `clavesDeRiesgo*`, `evaluarCoste`, «UNKNOWN bloquea»),
  `entornoHijo` (retira `OPENAI_*`, `CODEX_*`, `AZURE_OPENAI*`, `ANTHROPIC_*`, `CLAUDE*`, Bedrock/Vertex y
  `*_API_KEY`/`*_TOKEN`/`*_SECRET`), argumentos de CLI, lectores de salida, `limiteDeUsoDeTexto` /
  `reinicioDeTexto`, `estadoFinal`, vigilantes (`vigilarLineaClaude` mata el proceso si `apiKeySource ≠ none`).
- Se cortan: los imports de `shared/herramientas/nucleo.js` (se reemplazan por literales) y de
  `shared/operating-standard/ejecucion.js` (solo servía a `gitAislado`/`salidaDeGitFallido`, que se eliminan);
  todo lo de Play (`PLAY_RESULT`, cierres de rol, `modoSugerido`), evidencia/commits/trailers, etiquetas de UI,
  y el bloque de participación de suscripción de `disponibilidad`.
- No se copian: `servicio.js`, `repo.js`, `routing.js`, `play/*`, base de datos, IPC. El bucle
  spawn → leer → estado final se **reescribe** en `trabajos.js` sobre `lanzarProceso`.
- «Misión» se generaliza a «trabajo»: textos de motivos, `modo` lo da quien llama, `sesion` de Claude se genera
  por trabajo.
- Las mediciones con fecha que viven en comentarios (p. ej. `forced_login_method` cierra la sesión de Codex,
  2026-10-06; `claude auth status` dice `loggedIn` con sesión caducada, 2026-10-07) se pasan a
  `docs/reglas-medidas.md` con su fecha, además de quedar en el código.
- Pruebas: se copian las partes puras de `scripts/test-ejecutor.mjs` (EX-A, EX-B, EX-C),
  `test-ejecutor-claude.mjs` (núcleo y compuerta económica) y `test-ejecutor-cursor.mjs` (NUC, LEC), más los
  ejecutables falsos de `scripts/fixtures/ejecutor/` y las capturas reales. Se escriben nuevas para
  `trabajos.js`, `elegir.js`, `cuota.js`, CLI y HTTP, siempre con falsos: **las pruebas nunca gastan cuota**.

### 6.2 Conceptos

**Proveedor**: `codex`, `claude`, `cursor`, `lmstudio`, `ollama`. Cada uno declara capacidades
(`texto`, `imagen`, `vision` —acepta imágenes de entrada—, `codigo`), si es local, y cómo se lee su cuota.

| Proveedor | texto | imagen | vision | codigo | local | cuota |
|---|---|---|---|---|---|---|
| codex | sí | sí (`image_gen` integrada) | sí (`-i`) | fase 5 | no | se lee antes (app-server) |
| claude | sí | no | sí | fase 5 | no | solo después (statusline/stream-json) |
| cursor | sí (solo lectura) | no | — | no | no | no expuesta |
| lmstudio | sí | no | según modelo | no | sí | no tiene |
| ollama | sí | no | según modelo | no | sí | no tiene |

**Trabajo** (lo que pide una app):

```json
{
  "app": "biblia",
  "tipo": "imagen",
  "prompt": "…",
  "adjuntos": ["ruta/a/referencia.png"],
  "salida": "C:/…/guiones/imagenes/personajes/jose.png",
  "proveedor": "auto",
  "privado": false,
  "timeout_s": 900,
  "etiqueta": "personajes/jose"
}
```

- `tipo`: `texto` | `imagen` (fase 5: `codigo`).
- `proveedor`: `auto` o uno concreto; si es concreto y no está disponible, falla con motivo (no cambia solo).
- `privado: true` ⇒ solo proveedores locales.
- `salida`: obligatoria en `imagen`; en `texto`, opcional (si falta, el texto va en el resultado).
- `etiqueta`: el id del lado de la app (lo usa el Estudio para cruzar).

**Resultado**: `{id, estado, proveedor, modelo, texto?, archivos[], segundos, cuota_antes, cuota_despues,
motivo?, reinicio_en?}` con `estado` ∈ `ok` | `fallo` | `esperando_cuota` | `bloqueado_coste` | `cancelado`.

## 7. Cómo elige y cómo cuida el gasto

### 7.1 Detección del equipo (`capa-ia estado`)

Sin gastar cuota: localiza binarios (PATH y rutas de las apps de escritorio, como hace hoy Orchestrator),
pregunta la sesión al binario (`codex login status`, `claude auth status --json`), revisa configuraciones de
riesgo (`~/.codex/config.toml`, `settings.json` de Claude), lee la cuota de Codex por app-server, lista modelos
de LM Studio (`lms ls`) y Ollama (`/api/tags`), y la GPU (`nvidia-smi`). Resultado en caché
`%APPDATA%\capa-ia\equipo.json` (10 min; `--refrescar` lo fuerza). La comprobación real de Claude (una llamada
mínima que gasta un poco) **nunca es automática**: `capa-ia comprobar claude` la hace a pedido.

### 7.2 Reglas duras (no configurables)

1. Si en el entorno hay claves de API de un proveedor, se quitan del proceso hijo; si la configuración del
   binario apunta a clave, proxy o base URL ajena, el proveedor queda **bloqueado por coste** (UNKNOWN bloquea).
2. Codex: no se lanza si `credits.hasCredits` o `unlimited` es verdadero sin que el usuario lo haya anotado en la
   config de equipo (hoy son falsos [M]); no se lanza si `spendControlReached` o `rateLimitReachedType` vienen
   puestos; nunca se llama a `account/rateLimitResetCredit/consume`.
3. **Tope de cuota del equipo**: por defecto 80 % de la ventana semanal (reserva del 20 % para uso manual, ya
   decidida por el usuario en Orchestrator [L: `docs/audits/2026-11-04-integrador-suscripciones/README.md`]).
   Configurable entre 0 y 95 %. Al llegar, el trabajo queda `esperando_cuota` con `reinicio_en`. Se mide con el
   `usedPercent` real de la cuenta (app-server) antes de cada trabajo.
   **Tope por app** [C]: como Codex informa la cuota en enteros y una imagen gasta ~0,1–0,2 %, la diferencia
   antes/después de un trabajo casi siempre es 0. Por eso cada trabajo lleva un **costo estimado**: el promedio
   móvil por proveedor y tipo, calculado como (subida de `usedPercent` entre dos lecturas) ÷ (trabajos de capa-ia
   entre esas lecturas), con valor inicial configurable (`costo_inicial`: imagen 0,2 %, texto 0,05 %). El gasto
   de una app en la semana = suma de sus costos estimados desde el último `resetsAt`. Es una estimación (se
   rotula «≈» en el Estudio); el tope del equipo, medido, sigue mandando. El uso manual del usuario en la misma
   cuenta también sube `usedPercent` y se atribuye solo al tope del equipo, no a las apps.
4. Claude: como no hay lectura previa, se cuenta con el último `rate_limits` que guarde el statusline (si el
   usuario lo autoriza, §13.2) y con el último límite de uso detectado; concurrencia 1; en lotes, como máximo `claude.lote_max` trabajos seguidos
   (por defecto 5) [C].
5. Un fallo por límite de uso nunca se reintenta solo; se registra con su hora de reinicio.
6. Nada se descarga ni se instala solo (modelos incluidos).

### 7.3 Elección (`src/elegir.js`)

Para cada trabajo con `proveedor: auto`:
1. Candidatos = proveedores con la capacidad pedida, instalados, con sesión, **coste demostrado cero**,
   permitidos por la config de la app y, si `privado`, locales.
2. Se quitan los que están en tope de cuota o con límite vigente.
3. Se ordena por la preferencia de la app para ese tipo; si la app no la da, por la del equipo; por defecto
   [C]: `imagen` → codex; `texto` → codex, claude, lmstudio, ollama.
4. Para proveedores locales, el modelo se elige por VRAM: el mayor modelo instalado que cabe entero en la VRAM
   libre (con margen de 1,5 GB); si ninguno cabe, el menor que cabe en VRAM+RAM; los de embeddings se excluyen.
   La app puede fijar `modelo`.
5. Si no queda ninguno: `esperando_cuota` (si la causa es cuota, con el `reinicio_en` más próximo) o `fallo`
   con el motivo de cada descarte.

Cada elección lleva su **explicación** (lista de candidatos y por qué cayó cada uno), que se guarda en el
registro y la muestra el Estudio.

Servidores locales: si LM Studio u Ollama están apagados, capa-ia puede arrancarlos (`lms server start`,
`ollama serve`) solo si la config del equipo dice `arrancar_locales: true` (por defecto `false`) [C].

### 7.4 Cómo se ejecuta cada tipo

- **imagen (codex)**: carpeta de trabajo temporal en `%LOCALAPPDATA%\capa-ia\trabajos\<id>\`;
  `codex exec -C <tmp> -s workspace-write --skip-git-repo-check -i <adjuntos…> -o <respuesta> -` con el pedido
  por stdin. El pedido pide usar solo `image_gen`, guardar en `<tmp>/salida.png`, no usar la vía CLI/API ni
  clave, a lo sumo un reintento (el mismo texto probado el 16-nov en `herramientas/imagenes_codex.py`). Al
  terminar se verifica que es PNG, se copia a `salida` y se lee el `rate_limits` del rollout para
  `cuota_despues`. Codex nunca escribe en el repo de la app.
- **texto (codex)**: igual, con `-s read-only`; la respuesta sale de `-o`.
- **texto (claude)**: `claude -p --output-format stream-json --verbose --tools "" --permission-mode plan` en
  carpeta temporal, prompt por stdin, con el vigilante de `apiKeySource`.
- **texto (lmstudio / ollama)**: HTTP local a 127.0.0.1 (`/v1/chat/completions` de LM Studio, `/api/generate`
  de Ollama).
- Adjuntos de imagen en texto: solo a proveedores con `vision`.

## 8. Interfaces

### 8.1 CLI (`capa-ia`)

```
capa-ia estado [--refrescar] [--json]       qué hay, sesiones, coste, cuota, modelos locales
capa-ia elegir --tipo imagen [--app biblia] qué proveedor usaría ahora y por qué (no ejecuta)
capa-ia ejecutar trabajo.json [--json]      ejecuta un trabajo y espera el resultado
capa-ia ejecutar --tipo texto --prompt "…"  atajo
capa-ia registro [--app X] [--desde F]      lista trabajos
capa-ia comprobar claude                    comprobación real (gasta un poco; solo a pedido)
capa-ia instalar-statusline | desinstalar-statusline   lectura de cuota de Claude (§13.2)
capa-ia servir [--puerto 8780]              arranca el HTTP local
```

Códigos de salida: 0 ok · 2 esperando cuota · 3 bloqueado por coste · 1 otro fallo. `--json` imprime el
Resultado.

### 8.2 HTTP local

Solo `127.0.0.1`, puerto 8780 por defecto [C]; rechaza conexiones que no sean de loopback; token en
`%APPDATA%\capa-ia\token` (se crea al primer `servir`), cabecera `Authorization: Bearer`.

```
GET  /estado                         igual que la CLI
POST /elegir        {tipo, app}
POST /trabajos      Trabajo          → {id}  (cola en memoria; concurrencia por proveedor)
GET  /trabajos/:id                   → Resultado (o estado en curso)
POST /trabajos/:id/cancelar
GET  /registro?app=&desde=
GET  /eventos                        SSE con avance de trabajos (para paneles)
```

### 8.3 Clientes

- Python (`clientes/python/capa_ia.py`, stdlib): usa el HTTP si `servir` está arriba; si no, llama a la CLI.
  Funciones `estado()`, `elegir()`, `ejecutar(trabajo)`, `registro()`.
- Node: importa `src/` directo o usa HTTP.
- JUCE/C++ y otros: HTTP.

### 8.4 Configuración

- **Equipo** `%APPDATA%\capa-ia\config.json`: `tope_semanal_pct` (80), `preferencias` por tipo,
  `arrancar_locales` (false), `claude.lote_max` (5), rutas fijadas de binarios, puerto.
- **App** `capa-ia.json` en la raíz de cada app: `app`, `permitidos` por tipo, `preferencias`, `modelo` por tipo,
  `privado` por defecto, `tope_semanal_pct` propio (nunca mayor que el del equipo). La cuota es de la cuenta,
  no de la app: el tope de la app limita cuánto de la ventana puede usar esa app en la semana según el
  registro, y el del equipo manda sobre todos.

Ejemplo de la Biblia:

```json
{ "app": "biblia",
  "permitidos": { "imagen": ["codex"], "texto": ["codex", "claude", "lmstudio"] },
  "tope_semanal_pct": 30 }
```

### 8.5 Registro

`%APPDATA%\capa-ia\registro\AAAA-MM.jsonl`, una línea por trabajo terminado: `fecha, id, app, etiqueta, tipo,
proveedor, modelo, prompt` (texto completo), `adjuntos, salida, estado, motivo, segundos, cuota_antes,
cuota_despues, eleccion` (la explicación). Es local, no sale del equipo. Es la fuente de verdad que leen el
Estudio y, en la fase 6, Orchestrator.

## 9. El Estudio de la Biblia narrada

Herramienta **local** del repo de la Biblia, fuera de la PWA publicada (no la toca `sw.js` ni GitHub Pages).

- `herramientas/estudio.py` (Python stdlib): servidor en `127.0.0.1:8766` que sirve `herramientas/estudio/`
  (HTML, CSS, JS sin dependencias) y una API JSON que lee los archivos del repo. Se añade a
  `.claude/launch.json` como «estudio».
- `herramientas/imagenes_codex.py` pasa a `herramientas/imagenes.py`: conserva su lógica propia de la Biblia
  (qué falta, orden láminas → hojas → tomas, bloqueos, armado del pedido con instrucciones y referencias) y
  delega la ejecución en capa-ia por el cliente Python. Sus salvaguardas de gasto pasan a capa-ia; el registro
  propio `guiones/registro/imagenes.jsonl` se reemplaza por el de capa-ia (filtrado por `app: biblia`).

**Vistas**

```
┌ Estudio · Biblia narrada ──────────────────── Codex: 2 % semana · tope Biblia 30 % · reinicia dom 22 ┐
│ Resumen │ Estilo │ Personajes │ Escenarios │ Tomas │ Cola y registro                                  │
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Personajes                                                   [Generar pendientes (3)] [Generar 1]  │
│ ┌──────────┐ José · 39 años · Gn 39–50                 Estado: ⚠ rechazada                          │
│ │ imagen   │ Prompt (inglés) ▸   Negativo ▸   Ficha ▸   Nota: «toga griega; parece de 30»           │
│ └──────────┘ [Aprobar] [Rechazar con nota] [Regenerar]   Generada 16-nov · codex · 84 s · +0,1 %    │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

- **Resumen**: pendientes por grupo, generadas, aprobadas, rechazadas; cuota y tope; últimos trabajos.
- **Estilo / Personajes / Escenarios**: tarjeta por lámina u hoja con imagen, prompt completo (base + prompt +
  negativos, exactamente lo que se envió), ficha de origen, estado de revisión y su historial de trabajos.
- **Tomas**: por libro → pasaje → escena → toma; imagen inicial, prompt de imagen, prompt de video, hojas que
  usa y si está bloqueada (qué hoja falta).
- **Cola y registro**: trabajos en curso (vía `/eventos` de capa-ia) y terminados, con prompt, proveedor,
  elección explicada, segundos y cuota antes/después.

**Arranque y lotes** [C]: `estudio.py` arranca `capa-ia servir` si no responde y lo deja corriendo; el token lo
lee `estudio.py` del disco y el navegador nunca lo ve (el Estudio habla solo con `estudio.py`, que reenvía a
capa-ia). El lote «Generar N» lo lleva `estudio.py`, no capa-ia: manda **un trabajo a la vez**, recalcula
pendientes en cada vuelta (una hoja recién hecha desbloquea tomas) y para en el primer fallo, como hoy
`imagenes_codex.py`. Si se cierra el Estudio, el trabajo en curso termina y el lote no sigue.

**Historial** [C]: el Estudio lee el registro de capa-ia (`app: biblia`). Las 10 filas viejas de
`guiones/registro/imagenes.jsonl` se migran una vez: el prompt se reconstruye con la misma función que lo armó
y solo se acepta si su `sha256` coincide con el guardado; si no coincide, la fila entra sin prompt y lo dice.
Las imágenes hechas a mano (ChatGPT Images, alternativa que permite CLAUDE.md) entran en la revisión por su
archivo, con origen «a mano», y no cuentan para el tope.

**Corregir una imagen rechazada**: se edita el prompt en el Estudio (§13.1) y se regenera.

**Acciones**: generar N pendientes, generar o regenerar una (borra la anterior solo tras confirmar en
pantalla y la guarda en `guiones/imagenes/_anteriores/`), aprobar, rechazar con nota, cancelar un trabajo.
La revisión se guarda en `guiones/registro/revision.json` (`{id: {estado, nota, fecha, archivo_sha256}}`); si
la imagen cambia, la revisión vuelve a «pendiente de revisar». Al aprobar la lámina 2 se renombra
`patron-2-interior-codex.png` → `patron-2-interior.png` (regla ya acordada).

Lo que el Estudio **no** hace en v1: generar video ni publicar nada.

### 9.1 Primeras correcciones (revisión del 16-nov)

De la revisión de las 10 imágenes del lote [hecha en la sesión del 16-nov]:

| Imagen | Problema | Corrección en su ficha (`guiones/fuentes/…`) |
|---|---|---|
| `personajes/jose` | vestido drapeado como toga griega/romana; aparenta ~30 años | vestido largo egipcio de lino ceñido a la cintura, «not a draped Greek or Roman toga»; rasgos de unos 40 años |
| `personajes/hermanos` | la mayoría aparenta 25–35 (ficha: 40–46) | edad marcada: canas, arrugas, «middle-aged» |
| `escenarios/creacion-tierra-seca` | pedía dos estados y salió uno; copia el olivo de la lámina 1 | una sola escena por hoja |
| `escenarios/creacion-lumbreras` | mezcló día y noche en un cuadro partido | una sola escena por hoja |
| `escenarios/casa-jose-sala` (menor) | por la puerta se ven colinas con olivos | valle llano del Nilo por la puerta |

Además, el pedido de `imagenes.py` añade «do not reuse the composition or objects of the style reference
panels», porque las referencias pesan tanto que se repite la composición de la lámina 1. Rehacer la lámina 1
queda a decisión del usuario desde el Estudio (rechazarla la vuelve pendiente).

## 10. Fases y equipo

| Fase | Entrega | Terminado cuando |
|---|---|---|
| 1 · Núcleo | repo `capa-ia` con el núcleo copiado y recortado, adaptadores y pruebas copiadas | `node pruebas/todas.mjs` en verde; `grep` sin imports de Orchestrator ni de Play |
| 2 · Trabajos | `equipo`, `cuota`, `elegir`, `trabajos` (texto e imagen), `registro`, CLI | pruebas con falsos en verde; `capa-ia estado` real correcto en este equipo; **un** texto con LM Studio y **una** imagen real con Codex, con aprobación del usuario |
| 3 · HTTP y cliente Python | `servir`, endpoints, SSE, `capa_ia.py` | pruebas de HTTP (loopback, token, rechazo externo) en verde |
| 4 · Biblia | `imagenes.py` sobre capa-ia, Estudio con sus vistas y acciones, correcciones de fichas | las 4 imágenes de §9.1 corregidas y regeneradas desde el Estudio y aprobadas por el usuario en él; vista previa revisada en el navegador |
| 5 · Código | trabajos `codigo` en repos (Codex/Claude) | fuera de este diseño; diseño propio |
| 6 · Orchestrator | Orchestrator importa capa-ia y muestra el registro | fuera de este diseño; diseño propio |

Equipo (skill `metodo-base`): el orquestador (sesión principal) integra y verifica; **implementadores Opus**, uno
por fase y un solo escritor por archivo (fases 1→2→3 en serie; el Estudio de la fase 4 puede empezar en
paralelo con la 3 contra datos falsos); **verificador Opus** con contexto nuevo al cerrar cada fase; lectores
Sonnet para consultas. Commit por fase; ramas propias; nada se publica sin el visto bueno del usuario.

## 11. Pruebas

- Ninguna suite gasta cuota: ejecutables falsos de Codex, Claude y Cursor (copiados de Orchestrator), servidor
  falso de LM Studio/Ollama, app-server falso para la cuota.
- Casos obligatorios: clave de API en el entorno → no llega al hijo; config de riesgo → bloqueado por coste;
  `apiKeySource ≠ none` → proceso muerto; créditos presentes → no se lanza; cuota ≥ tope → esperando; límite
  de uso en la salida → registrado con reinicio y sin reintento; HTTP desde una IP no loopback → rechazo; sin
  token → 401.
- Las pruebas reales (fase 2 y 4) son pocas, se anuncian antes y se miden en «Chats principales» y en el
  `rate_limits` del rollout.

## 12. Lo que queda al constructor

- Nombres internos, estructura de pruebas, formato exacto de los mensajes de la CLI.
- Cómo se implementa la cola del HTTP y el SSE.
- Detalle visual del Estudio, siguiendo los estilos de la PWA de la Biblia.
- Cómo leer la VRAM libre si `nvidia-smi` no está (entonces, sin modelos locales automáticos).

## 13. Decisiones del usuario (2026-11-17)

1. **Corregir una imagen rechazada: se edita en el Estudio** [D]. La tarjeta tiene «Editar prompt»: edita
   `prompt_en` y `negativo_en` de la ficha (hojas) o de la toma (`imagen.prompt_en`/`negativo_en`), muestra el
   cambio (antes/después) y al guardar escribe el JSON de `guiones/fuentes/…` conservando el resto del
   archivo y su formato (indentación de 2, UTF-8, sin escapar acentos). Tras guardar se corre el validador de
   `herramientas/guiones.py` (por ejemplo, las palabras prohibidas de `estilo.json`); si falla, no se guarda y
   se muestra el error. Las láminas patrón se editan igual en `estilo.json → laminas_patron`. La base de
   imagen y los negativos generales no se editan desde el Estudio (cambian el estilo de todo: exigen decisión
   y versión nueva).
2. **Cuota de Claude: se instala el statusline** [D]. `capa-ia instalar-statusline` añade a
   `~/.claude/settings.json` un `statusLine` que guarda `rate_limits` en `%APPDATA%\capa-ia\claude-cuota.json`
   con la hora; si ya hay un statusline, lo encadena (lo llama y devuelve su salida) en vez de reemplazarlo;
   hace copia del `settings.json` antes y tiene `desinstalar-statusline`. Con ese archivo, Claude entra en el
   tope del equipo (la mayor de sus dos ventanas, 5 h y 7 d) igual que Codex; la lectura puede estar vieja y se
   rotula con su hora.
