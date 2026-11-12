# Biblia · Compañero de lectura — reglas del proyecto

Responder en español. PWA estática (JS sin dependencias ni build) publicada en GitHub Pages desde `main`. Al publicar se sube `VERSION` en `sw.js`.

## Principio (no negociable)
Todo dato dice de dónde sale y su certeza. Se distingue siempre:
- **Texto** (lo dice el versículo, con cita) · **Inferido** · **Cálculo** (con sus pasos).
- **Registro histórico** (objeto, manuscrito, mapa antiguo, con museo/institución) vs **arte** (interpretación de un artista, con fecha) vs **ilustración moderna** (incluida la generada por IA: siempre rotulada «Ilustración moderna») vs **reconstrucción moderna** (con sus supuestos).
- Lo que viene de fuera de la Biblia se marca «Fuente externa».
- Nada inventado: si no hay fuente, no se muestra.

## Decisiones del usuario (2026-11-11)
- Es un **apoyo a la lectura, no un cuestionario**: nada de preguntas tipo examen en la lectura. *Excepción (decidida después, mismo día):* el juego desbloquea personajes con preguntas de selección (ver abajo).
- Se asume **conexión permanente**: se pueden usar recursos web (videos incrustados, audio en línea, imágenes remotas). El modo sin conexión no es requisito.
- Las imágenes o pinturas deben estar **relacionadas con el pasaje** concreto.
- Interactivo pero **no básico ni repetitivo** (p. ej. la ruta del éxodo).
- Habrá **perfil de usuario**: niño (contenido filtrado) o adulto (todo, incluido lo cruento).
- Aprobado: imagen por pasaje, ruta del éxodo animada, tabernáculo interactivo, objetos de museo y Rollos del Mar Muerto (de dónde sale el texto), audio en lengua original y en la del usuario, mapas antiguos comparados con el actual, profundizar en personajes, curiosidades, fichas coleccionables, plagas, videos que muestran de dónde a dónde va el relato, comparar textos lado a lado, «Mientras tanto en…», notas y subrayados.

## Lectura en orden (decisiones del usuario, 2026-11-11)
- La Biblia se **desbloquea leyendo en orden** (orden de los pasajes, Gn → Ap). Todo lo posterior al primer pasaje sin leer queda bloqueado: texto, búsqueda, mapa, línea de tiempo, fichas, recursos, comparar y juego muestran solo lo leído (más el pasaje actual).
- **Tiempo mínimo** antes de poder marcar un pasaje como leído: palabras ÷ 250 por minuto (adulto) o ÷ 150 (niño); solo cuenta el tiempo con el pasaje abierto y visible.
- Lo ya marcado fuera de orden se conserva; desde ahora solo se avanza desde el primer pasaje sin leer.

## Juego (decisiones del usuario, 2026-11-11; diseño en `docs/superpowers/specs/2026-11-11-catalogo-juego-design.md`)
- Se coleccionan **personajes, objetos y escenarios**; fichas con todo lo que se sabe (con certeza y fuente). Las habilidades y poderes son invención del juego, nunca dato bíblico.
- **Por cada libro que se ingresa**: catálogo (`herramientas/juego/<Libro>.json` → `python -I herramientas/juego.py` → `datos/juego.js`) con genealogías, historias, personajes, objetos y escenarios, más `docs/juego/ideas-<Libro>.md` con minijuegos por historia para que el usuario elija. Al llegar a Apocalipsis se afina el conjunto.
- Las genealogías no desbloquean; quien solo sale en genealogías es NPC. Nivel según versículos de aparición.
- Un personaje queda listo al terminar el capítulo de su última aparición en la primera historia donde es principal; las menciones posteriores suman a la ficha, no retrasan.
- Futuro, por partes: prueba de selección con tiempo, dos oportunidades, espera de días; puntos = mejor puntaje por personaje; ranking (primero local, luego servidor con antitrampas); láminas con imagen basada en registros de época («Ilustración moderna»); objetos que potencian; escenarios jugables pocas veces al día; misiones por historia.

## Archivos
- Datos: `herramientas/*.py` → `datos/biblia.js` (`window.BIBLIA_DATOS`) y `datos/mapa-base.js`. Regenerar: `python -I herramientas/construir_datos.py --sin-red`. Detalle en `datos/LEEME.md`.
- Interfaz: `index.html`, `app.js` (núcleo puro `globalThis.BibliaNucleo`), `estilos.css`, `sw.js`. Pruebas: `node pruebas/probar.mjs`.
- Vista local: servidor en http://127.0.0.1:8765 (`preview_start` nombre «biblia»).
