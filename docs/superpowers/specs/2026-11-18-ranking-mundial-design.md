# Ranking mundial del desafío — diseño (2026-11-18, borrador para aprobar)

## Qué pidió el usuario
Ranking mundial de puntajes con nombre de usuario, **niños separados de adultos**.

## Decisiones del usuario (2026-11-18)
| Tema | Decisión |
|---|---|
| Servidor | **Supabase, plan gratuito** (sin tarjeta, sin gasto adicional) |
| Nombres | **Niño: nombre generado** a elegir (nunca escribe texto libre). **Adulto: nombre libre** con filtro y único |
| Puntaje | **Suma por personaje** superado: puntos según su nivel + extra por rapidez; el ranking suma toda la colección |
| Antitrampas | **Fuerte desde ya**: las respuestas salen de la app y el servidor corrige y cronometra cada pregunta |

## Consecuencia: el banco de respuestas sale del repositorio
El repositorio `roberto924/biblia` es **público** (GitHub Pages). Con antitrampas fuerte, las respuestas no pueden estar en git ni en la app publicada:
- `herramientas/juego/preguntas/` y `datos/preguntas.js` quedan en `.gitignore` (hecho el 2026-11-18, antes de cualquier commit: no se filtró nada).
- El banco vive en Supabase (tabla sin acceso para la app) y en la copia local del usuario. **Respaldo**: hay que decidir dónde guardar una copia fuera de este equipo (repositorio privado aparte o exportación periódica desde Supabase).
- La app publicada recibe solo `datos/desafios.js`: escala, segundos, `sinNino` y, por personaje, las `ref` de sus preguntas (para saber cuántas hay disponibles según lo leído), **sin texto de preguntas ni respuestas**.
- Sin conexión o sin servidor, el desafío no se puede jugar (el proyecto ya asume conexión permanente).

## Arquitectura
**Auth**: cada perfil local (adulto o niño) se registra de forma **anónima** en Supabase la primera vez que entra a un desafío (`signInAnonymously`, sin correo ni contraseña). La sesión se guarda con el perfil. Cambiar de equipo pierde la cuenta (una «llave de recuperación» queda para después).

**Tablas** (RLS activado en todas):
- `perfiles` (id = `auth.uid()`, `nombre` único sin distinguir mayúsculas, `tipo` adulto | nino, `zona_horaria` fijada al registrarse, `creado`). La app solo lee su propia fila; el nombre se pone vía función.
- `preguntas` (personaje, ref, cita, pregunta, opciones, correcta, nino, libro). **Sin ninguna política de lectura**: solo la leen las funciones con la clave de servicio.
- `personajes_desafio` (personaje, nivel, n_preguntas, sin_nino), derivada de `datos/juego.js`.
- `intentos` (perfil, personaje, día local, preguntas servidas con el orden de sus opciones, hora en que se sirvió cada una, respuestas, aciertos, ms, superado, puntos). La app solo lee los suyos; se escriben solo vía función.
- Vista pública `ranking` (nombre, tipo, puntos, personajes superados, tiempo total), lectura anónima; es lo único público.

**Edge Function `desafio`** (una, con acciones):
1. `empezar {personaje, leidos}` → comprueba: perfil registrado; un intento por personaje y día (según su zona horaria fija); no superado; perfil niño sin personajes `sin_nino`. Elige N preguntas al azar entre las que caen en lo leído (lo leído lo declara la app: mentir no da puntos, solo cambia qué preguntas salen). El perfil niño no recibe las `nino: false`. Devuelve **solo la primera pregunta** (texto y opciones barajadas, sin la correcta) y anota la hora.
2. `responder {intento, indice, opcion}` → rechaza si pasaron más de los segundos permitidos + 2 s de margen por la red (cuenta como fallada); anota; devuelve la siguiente pregunta o el resultado. Salir de la pantalla manda `opcion: -1`.
3. Al terminar: si acertó todas, `superado` y puntos; devuelve el repaso (respuesta, versículo y cita). Si no, solo «a de n» (no dice cuáles falló).

Así no hay forma de ver las preguntas siguientes ni las respuestas antes de contestar, ni de tomarse más tiempo del permitido.

**Puntaje** (propuesta; Cálculo, se muestra con sus pasos):
- Por personaje superado: `10 × preguntas` + rapidez `round(5 × preguntas × tiempo_sobrante / tiempo_total)`. Noé (10 preguntas, 15 s): de 100 a 150 puntos.
- Ranking = suma de todos los superados; a igualdad, menos tiempo total.
- Cuando un personaje suba de nivel con un set nuevo (fase futura), suma ese set aparte.

**Nombres**:
- Niño: la app ofrece 5 nombres generados (adjetivo + sustantivo del mundo bíblico sin personas reales + número: «Pastor Valiente 482», «Estrella Alegre 17»); puede pedir otros 5. Nunca escribe.
- Adulto: 3–20 caracteres (letras, números, espacio), único, filtro de palabras ofensivas en el servidor; se puede cambiar.
- Los rankings de niños y de adultos son pestañas separadas; cada perfil ve los dos y se destaca su posición.

## Privacidad (menores)
- Ningún dato personal: sin correo, sin nombre real, sin edad exacta. Solo un id anónimo, el nombre generado y el puntaje.
- La app explica qué se publica antes de registrarse; registrarse en el ranking pide el PIN de adulto si existe (como los perfiles).
- **Investigar antes de publicar** (lineamientos, tema nuevo): obligaciones de la Ley 21.719 (Chile) y de normas como COPPA/GDPR-K para un servicio con perfiles infantiles seudónimos; límites del plan gratuito de Supabase (proyectos, MAU, invocaciones de funciones, pausa por inactividad). Hoy sin fuente verificada en `lineamientos`.

## Lo que hace el usuario (no lo puede hacer Claude)
1. Crear la cuenta y el proyecto en Supabase (plan gratuito) o autorizar el conector de Supabase en Claude (`/mcp`, en una terminal con `claude`) para que el proyecto se cree desde aquí con su aprobación.
2. Aprobar este diseño y la fórmula de puntaje.

## Contrato app ↔ servidor (fijo; aprobado el 2026-11-18 junto con el diseño)
Sin dependencias en la app: `fetch` directo. Configuración pública en `datos/servidor.js`:
`window.BIBLIA_SERVIDOR = { url: "https://<ref>.supabase.co", anon: "<clave anon pública>" }` (si falta o está vacío, el desafío dice «El desafío necesita conexión con el servidor»).

**Auth anónima** (REST de Supabase Auth, sin supabase-js):
- Alta: `POST {url}/auth/v1/signup` con cabecera `apikey: anon`, cuerpo `{}` → `{ access_token, refresh_token, expires_in, user: { id } }`.
- Renovar: `POST {url}/auth/v1/token?grant_type=refresh_token` cuerpo `{ refresh_token }`.
- La app guarda `{ access_token, refresh_token, expira }` en el store del perfil local (clave `servidor.sesion`).

**Función** `POST {url}/functions/v1/desafio`, cabeceras `apikey: anon`, `Authorization: Bearer <access_token>`, cuerpo JSON `{ accion, ... }`. Respuestas JSON; error = `{ error: "<código>", ...extra }` con HTTP 4xx.
| accion | cuerpo | respuesta |
|---|---|---|
| `perfil` | — | `{ perfil: { nombre, tipo } \| null }` |
| `nombres` | — | `{ nombres: [5 nombres generados para niño] }` |
| `registrar` | `{ tipo: "adulto"\|"nino", nombre, zona, consentimiento? }` (zona IANA, p. ej. `America/Santiago`) | `{ perfil }` · errores `nombre-usado`, `nombre-invalido`, `nombre-ofensivo`, `ya-registrado`, `falta-consentimiento`. Niño: el nombre debe salir del generador (se valida contra sus listas) y `consentimiento: true` es obligatorio (un adulto lo declara en la app con su PIN; el servidor guarda `consentimiento_en`). Motivo: Ley 21.719 art. 16 quáter (menores de 14: consentimiento de padres o representantes), ver `lineamientos/temas/supabase-y-datos-de-menores`. |
| `renombrar` | `{ nombre }` (solo adulto) | `{ perfil }` · mismos errores; `solo-adulto` |
| `estado` | — | `{ hoy, hasta, personajes: { [id]: { superado, puntos, intentadoHoy, ultimo: { aciertos, total } \| null } } }` (`hasta` = ISO de la próxima medianoche en su zona) |
| `empezar` | `{ personaje, ids: [ids de pregunta disponibles según lo leído] }` | `{ intento, n, seg, i: 0, pregunta: { p, o: [4] } }` · errores `sin-perfil`, `ya-intentado-hoy` (+`hasta`), `superado`, `sin-desafio`, `faltan-preguntas` |
| `responder` | `{ intento, i, opcion }` (0–3, o −1 = salió de la pantalla) | siguiente: `{ i, pregunta }` · final: `{ fin: true, aciertos, total, ms, superado, puntos, hasta, repaso?: [{ p, respuesta, ref, cita }] }` (`repaso` solo si superó) · errores `intento-invalido`, `fuera-de-orden` |

Reglas del servidor: N según el nivel (`escala`), segundos 15 adulto / 25 niño; una pregunta a la vez; respuesta aceptada solo si llega a ≤ `seg` s + 2 s desde que se sirvió (si no, fallada); un intento por personaje y día en la zona fija del perfil (empezar ya lo consume); niño: sin `nino: false` ni personajes `sin_nino`.

**Ranking**: vista pública `ranking` por PostgREST, `GET {url}/rest/v1/ranking?tipo=eq.<tipo>&order=puesto.asc&limit=100` con `apikey: anon` → `[{ puesto, nombre, tipo, puntos, personajes, ms }]`. Posición propia: `...&nombre=eq.<nombre>`.

**Datos públicos** `datos/desafios.js` (sin preguntas ni respuestas): `window.BIBLIA_DESAFIOS = { escala, segundos, sinNino, personajes: { [id]: [{ id: "<opaco>", ref, nino? }] } }`.

## Cambios al contrato tras la revisión de seguridad (2026-11-18, v2; manda sobre lo de arriba)
1. **`empezar { personaje }`**: la app ya no manda ids. El servidor arma el set con **todas** las preguntas del personaje cuyo versículo cae hasta el final de su capítulo `listo` (y sin `nino:false` en niño), al azar. Así nadie puede forzar qué preguntas le salen.
2. **Banco mínimo = 2 × n** por personaje, en adulto y en niño (antes, n). Lo exige `herramientas/preguntas.py`.
3. **Repaso** al superar: solo `[{ p, ref }]` (pregunta y versículo, para leerlo), **sin la respuesta ni la cita**: el repaso no sirve para pasarle respuestas a otra cuenta.
4. **`borrar {}`** → `{ ok: true }`: borra la cuenta anónima (auth) y en cascada su perfil e intentos. La app la llama al borrar un perfil local y cuando el adulto retira la autorización del niño.
5. **Ranking por RPC** (no vista security definer): `POST {url}/rest/v1/rpc/ranking` con `apikey: anon`, cuerpo `{ tipo, nombre?: string|null, limite?: 100 }` → `[{ puesto, nombre, puntos, personajes, ms }]`. Con `nombre`, solo esa fila.
6. `datos/desafios.js`: `personajes[id] = [{ ref, nino? }]`, **sin ids**.
7. `authenticated` no lee ninguna tabla por REST (todo va por la función); `no-autorizado` (401) hace que la app olvide el token de acceso.
8. Plazo por respuesta: seg + 2 s medido con la hora de la base de datos; empezar con un intento aún abierto del mismo personaje → `ya-intentado-hoy`.
9. Nombres de adulto: solo alfabeto latino (con tildes y ñ), números y espacios.

## v3 — niños solo ven su posición (decisión del usuario, 2026-11-18; manda sobre lo anterior)
- **Ningún nombre de niño se publica en una lista.** `rpc/ranking` solo responde con `tipo = 'adulto'`; con `'nino'` devuelve vacío.
- Acción nueva **`posicion {}`** (cualquier perfil, vía la función con su token) → `{ puesto: n | null, total, puntos, personajes, ms }`: su puesto entre los de su tipo con al menos un superado (`null` si aún no tiene puntos). El niño ve «Vas 12.º de 340» y sus puntos; el adulto, su fila aunque no esté entre los 100 primeros.
- Se sigue pidiendo la autorización del adulto con el PIN para el perfil niño (sus datos se tratan en el servidor aunque no se publiquen).

## Fuera de esta fase
Llave de recuperación de cuenta, subir de nivel con sets nuevos, ranking por libro o semanal, moderación manual de nombres, minijuegos y objetos que potencian.

## Plan (tras aprobar)
1. Investigación corta (Supabase gratis, privacidad de menores) → `lineamientos`.
2. Esquema SQL + RLS + Edge Function + carga del banco (script `herramientas/subir_preguntas.py`, que no deja nada en git).
3. App: registro anónimo y nombre, desafío contra el servidor, pestaña Ranking (niños | adultos), `datos/desafios.js` sin respuestas.
4. Pruebas: núcleo (node), función (casos de trampa: responder tarde, segunda vez en el día, pedir respuesta, perfil niño con personaje excluido), revisión de seguridad (`/security-review`), captura.
