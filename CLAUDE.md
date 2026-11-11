# Biblia · Compañero de lectura — reglas del proyecto

Responder en español. PWA estática (JS sin dependencias ni build) publicada en GitHub Pages desde `main`. Al publicar se sube `VERSION` en `sw.js`.

## Principio (no negociable)
Todo dato dice de dónde sale y su certeza. Se distingue siempre:
- **Texto** (lo dice el versículo, con cita) · **Inferido** · **Cálculo** (con sus pasos).
- **Registro histórico** (objeto, manuscrito, mapa antiguo, con museo/institución) vs **arte** (interpretación de un artista, con fecha) vs **ilustración moderna** (incluida la generada por IA: siempre rotulada «Ilustración moderna») vs **reconstrucción moderna** (con sus supuestos).
- Lo que viene de fuera de la Biblia se marca «Fuente externa».
- Nada inventado: si no hay fuente, no se muestra.

## Decisiones del usuario (2026-11-11)
- Es un **apoyo a la lectura, no un cuestionario**: nada de preguntas tipo examen.
- Se asume **conexión permanente**: se pueden usar recursos web (videos incrustados, audio en línea, imágenes remotas). El modo sin conexión no es requisito.
- Las imágenes o pinturas deben estar **relacionadas con el pasaje** concreto.
- Interactivo pero **no básico ni repetitivo** (p. ej. la ruta del éxodo).
- Habrá **perfil de usuario**: niño (contenido filtrado) o adulto (todo, incluido lo cruento).
- Aprobado: imagen por pasaje, ruta del éxodo animada, tabernáculo interactivo, objetos de museo y Rollos del Mar Muerto (de dónde sale el texto), audio en lengua original y en la del usuario, mapas antiguos comparados con el actual, profundizar en personajes, curiosidades, fichas coleccionables, plagas, videos que muestran de dónde a dónde va el relato, comparar textos lado a lado, «Mientras tanto en…», notas y subrayados.

## Archivos
- Datos: `herramientas/*.py` → `datos/biblia.js` (`window.BIBLIA_DATOS`) y `datos/mapa-base.js`. Regenerar: `python -I herramientas/construir_datos.py --sin-red`. Detalle en `datos/LEEME.md`.
- Interfaz: `index.html`, `app.js` (núcleo puro `globalThis.BibliaNucleo`), `estilos.css`, `sw.js`. Pruebas: `node pruebas/probar.mjs`.
- Vista local: servidor en http://127.0.0.1:8765 (`preview_start` nombre «biblia»).
