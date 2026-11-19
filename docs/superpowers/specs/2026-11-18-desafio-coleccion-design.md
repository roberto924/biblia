# Desafío de la colección y retratos — diseño (2026-11-18)

## Qué pidió el usuario
- Aprovechar las imágenes de personajes generadas para que la colección se vea bonita: un primer diseño de fichas con la información importante.
- El personaje se desbloquea con un cuestionario: mientras no lo pase, su ficha dice «bloqueado» con un candado; al tocar el candado empieza el cuestionario.
- Preguntas de selección (A, B, C o D) con tiempo por pregunta, para que no alcance a buscar en la web: tiene que ser un desafío.
- **Un intento al día.** Si no responde bien el set, espera al día siguiente; se muestra un contador de cuánto falta.
- **Cuántas preguntas depende del personaje y su importancia** (su nivel): los más importantes tienen más. Siempre según lo que el usuario ya leyó.
- Al superarlo, aparecen las imágenes del personaje.

## Decisiones tomadas por defecto (el usuario puede cambiarlas)
| Tema | Valor | Dónde se cambia |
|---|---|---|
| Aprobar | Acertar **todas** las preguntas del set | `estadoDesafio` / `anotarIntento` (app.js) |
| Preguntas por nivel | nivel 1–2 → 3 · 3–4 → 5 · 5–6 → 7 · 7–8 → 10 · 9 o más → 12 | `ESCALA` en `herramientas/preguntas.py` |
| Tiempo por pregunta | 15 s adulto · 25 s niño | `SEGUNDOS` en `herramientas/preguntas.py` |
| «Otro día» | Medianoche local del dispositivo | `proximaMedianoche` (app.js) |
| Origen de las preguntas | Escritas a mano por personaje, cada respuesta con versículo y cita RV1909, auditadas | `herramientas/juego/preguntas/<Libro>.json` |
| Imágenes | Solo hojas **aprobadas** en el Estudio y sin cambios desde la aprobación | `herramientas/retratos.py` |
| NPC | Entran sin desafío (no hay de qué preguntar) | `estadoDesafio` |
| Perfil niño (decisión del usuario) | Se excluye toda pregunta no apta: tramo «alto» de `datos/contenido.js` y también por tema (sangre, violencia). Sin desafío para el niño en personajes cuya historia no es apta (Canaán): los obtiene leyendo | `nino: false` y `sin_desafio_nino` en `herramientas/juego/preguntas/<Libro>.json` |

## Cómo funciona
1. **Leer** sigue igual: el personaje está «en curso» hasta terminar el capítulo donde se cierra su primera historia como protagonista (`listo.capitulo`).
2. Al terminarlo queda **listo para el desafío**: carta con candado (borde ámbar, «Desafío · N preguntas»). No cuenta como obtenido. Su ficha muestra el candado en lugar del retrato y oculta «Lo que dice el texto».
3. Tocar el candado abre el diálogo del desafío: reglas y «Empezar». Al empezar se anota el intento del día (cerrar, recargar o abandonar cuenta como fallado).
4. Cada pregunta: barra y segundos que bajan, cuatro opciones A–D (también teclas 1–4 o A–D). Si se acaba el tiempo, o se sale de la pantalla (otra pestaña o ventana: `visibilitychange`/`blur`), la pregunta cuenta como fallada. No se dice cuál se falló.
5. **Supera** (todas bien): se revela el retrato (Ilustración moderna, generada con IA) y entra a la colección; se muestran las preguntas con su respuesta, versículo y cita.
6. **Falla**: «No esta vez: a de n» y cuenta atrás hasta la medianoche. Al día siguiente, otro set al azar con las opciones en otro orden.
7. Sin `datos/preguntas.js`, o sin preguntas suficientes para un personaje, se obtiene como antes (sin desafío).

Solo se pregunta lo leído: la app filtra las preguntas cuyo versículo cae en un pasaje marcado como leído. El perfil niño no recibe las marcadas `nino: false` (algo cruento).

## Datos
- `herramientas/juego/preguntas/<Libro>.json` → `python -I herramientas/preguntas.py` → `datos/preguntas.js` (`window.BIBLIA_PREGUNTAS`: `escala`, `segundos`, `personajes[id] = [{ p, o[4], c, ref, cita, nino? }]`). El script comprueba: cita literal, 4 opciones distintas, personaje no NPC, y que hasta el capítulo en que queda listo haya preguntas para un set completo en adulto y en niño.
- `herramientas/retratos.py` → `recursos/retratos/<ficha>-retrato.webp` (busto de frente recortado 3:4, 480×640) y `<ficha>-hoja.webp` (hoja entera, 1200 px) + `datos/retratos.js` (`window.BIBLIA_RETRATOS.personas[id]`). Hojas de grupo (los hermanos, la familia de Noé) solo van en la ficha. La carta usa el retrato de la última hoja individual cuyo pasaje ya se leyó: envejece al avanzar la lectura (Jacob joven → anciano).
- Progreso: `store` del perfil, clave `desafios`: `{ [id]: { superado, intentos: [{ dia, aciertos, total, ms, fecha }], mejor } }`.

## Límites conocidos
- Todo es local: cambiar la hora del equipo o borrar el almacenamiento salta la espera. El antitrampas va con el servidor (fase futura, como el ranking).
- Los personajes obtenidos antes de que exista su banco de preguntas pasan a «desafío» cuando llega el banco.
- Puntos y ranking: se guarda el mejor tiempo del set superado (`mejor`), aún no se muestra.

## Por cada libro que se ingresa
Preguntas de sus personajes en `herramientas/juego/preguntas/<Libro>.json` (lo que pide su nivel + 3), auditoría completa, `python -I herramientas/preguntas.py`. Retratos: aprobar en el Estudio y correr `python -I herramientas/retratos.py`.
