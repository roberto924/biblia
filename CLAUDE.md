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
- **Videos y audios externos** (Proyecto Biblia, Superbook… y el video de cada libro) comentan o resumen: solo se ven cuando está **leído** todo lo que cubren; el pasaje en curso no cuenta (2026-11-17). Mientras tanto se avisa con candado y hasta dónde hay que leer; al terminar, salen como «Repaso de lo leído» en el pasaje siguiente y en los pasajes que cubren.
- **Galería del pasaje** (2026-11-18): bajo el título, dos pestañas **Videos | Imágenes** (una a la vez); lo elegido en grande y el resto en miniaturas que pasan al grande al tocarlas. Por defecto, Videos si hay alguno desbloqueado (los narrados propios, `propio: true` en `recursos`, siempre primero), si no Imágenes. Los videos ya no van en el acompañante (allí queda el audio), así que pulsar versículos no los reinicia.
- El **video narrado** de un pasaje (Higgsfield) es el propio pasaje: se ve en el pasaje en curso, y verlo entero contará como leerlo (desbloquea igual que el tiempo mínimo). Se implementa cuando ese video entre en la app.

## Pantalla de lectura (decisiones del usuario, 2026-11-18)
- La lectura manda, como el texto en el centro de las Biblias glosadas; lo adicional va al margen. En pantalla muy ancha (≥1800 px), tres columnas: título y galería · libro · acompañante.
- **Leer = libro abierto**: páginas del alto de la pantalla, dos a la vista (una en estrecho), cabecera con libro y capítulo, número de página, lomo; se pasa con botones, flechas o deslizando. El papel sigue el tema (marfil en claro, carbón en oscuro).
- **Modo Original**: la foto del folio del Códice de Leningrado junto a su transcripción hebrea y la RV1909, versículo a versículo. Rollos y Códice Vaticano siguen solo como enlace.

## Juego (decisiones del usuario, 2026-11-11; diseño en `docs/superpowers/specs/2026-11-11-catalogo-juego-design.md`)
- Se coleccionan **personajes, objetos y escenarios**; fichas con todo lo que se sabe (con certeza y fuente). Las habilidades y poderes son invención del juego, nunca dato bíblico.
- **Por cada libro que se ingresa**: catálogo (`herramientas/juego/<Libro>.json` → `python -I herramientas/juego.py` → `datos/juego.js`) con genealogías, historias, personajes, objetos y escenarios, más `docs/juego/ideas-<Libro>.md` con minijuegos por historia para que el usuario elija. Al llegar a Apocalipsis se afina el conjunto.
- Las genealogías no desbloquean; quien solo sale en genealogías es NPC. Nivel según versículos de aparición.
- Un personaje queda listo al terminar el capítulo de su última aparición en la primera historia donde es principal; las menciones posteriores suman a la ficha, no retrasan.
- Futuro, por partes: prueba de selección con tiempo, dos oportunidades, espera de días; puntos = mejor puntaje por personaje; ranking (primero local, luego servidor con antitrampas); láminas con imagen basada en registros de época («Ilustración moderna»); objetos que potencian; escenarios jugables pocas veces al día; misiones por historia.

## Explicaciones y manuscritos (decisiones del usuario, 2026-11-13; diseño en `docs/superpowers/specs/2026-11-13-explicaciones-design.md`)
- **Explicaciones al tocar**: palabras antiguas de la RV1909, medidas y monedas (equivalencia como Cálculo con pasos y supuestos), costumbres y conceptos, y **pasajes difíciles** (qué dice el texto + posturas con su fuente, sin decidir por el lector). Punteado suave con interruptor por perfil; versión propia para niño; nada que adelante pasajes no leídos. Fuentes: la Biblia, diccionarios de dominio público (Easton, Smith, Jewish/Catholic Encyclopedia), Wikcionario; redactado con palabras propias. Cada tanda pasa una **auditoría de todo** (pasajes, medidas y términos; con muestra se escaparon ~1 de cada 3 conceptos con errores) antes de publicarse.
- **El manuscrito de cada pasaje**: folio del Códice de Leningrado (Wikimedia Commons, dominio público) mostrado como «Registro histórico»; rollos (Leon Levy, IAA) y Códice Vaticano (BAV) **solo como enlace**: sus términos no permiten mostrar las imágenes.
- **Por cada libro que se ingresa**, además del catálogo de juego:
  - Explicaciones: términos nuevos en `herramientas/explicaciones/terminos-*.json` (los existentes se aplican solos por sus `formas`; revisar las ambigüedades del libro) y `pasajes-<Libro>.json`, auditoría, y `python -I herramientas/explicaciones.py` → `datos/explicaciones.js`.
  - Manuscritos: añadir el libro a `herramientas/manuscritos.py` (folios de Leningrado, rollos, página del Vaticano) → `datos/manuscritos.js`; todo pasaje debe tener folio.

## Biblia narrada y actuada (decisiones del usuario, 2026-11-16; guía en `guiones/LEEME.md` y `guiones/estilo.md`)
- **Un video por pasaje** (la pantalla de lectura): `guiones/fuentes/<Libro>/<pasaje>.json` → `python -I herramientas/guiones.py` → hoja de rodaje, guion de audio y fichas. El guion se ordena en escenas → tomas, con apertura, cierre y continuidad con el pasaje anterior y el siguiente. La narración y los diálogos son la RV1909 letra por letra; nadie dice lo que el texto no le da.
- **Estilo único de Génesis a Apocalipsis: «Estilo v1 · animación 2D de largometraje»** (`guiones/fuentes/estilo.json`). Rige los videos y toda ilustración generada de la app (fichas de personaje, láminas del juego), con tres láminas patrón que se adjuntan en toda generación. El usuario tomó como referencia las películas de animación 2D de Warner: en los prompts se describe con palabras, nunca se nombran estudios, marcas ni personajes, y no se copia ninguna obra. Nada realista, pintado ni 3D. Cambiarlo exige una decisión del usuario y una versión nueva. Los registros históricos y el arte antiguo de la app no se tocan.
- Las imágenes se generan en lote con Codex (herramienta de imágenes integrada, sesión de ChatGPT) **vía capa-ia** (`app: "biblia"`, `capa-ia.json` en la raíz, tope del 30 % de la semana): `python -I herramientas/imagenes.py --generar N` (sin `--generar` solo lista; nunca se llama a `codex` directamente). Para ver, revisar, editar prompts y regenerar: el **Estudio**, `python -I herramientas/estudio.py` (local en http://127.0.0.1:8766, `preview_start` nombre «estudio»; no se publica). **Sin gasto adicional** (decisión del usuario, 2026-11-16): nunca clave de API, créditos ni recarga automática, ni usar los restablecimientos de límite; al llegar al límite semanal se para. Cada imagen se revisa contra su ficha antes de usarse; ChatGPT Images a mano queda como alternativa. Los videos y el lipsync, en Higgsfield, a mano en la web (el modo ilimitado no se puede automatizar). Todo se rotula «Ilustración moderna (generada con IA)».
- Los guiones empiezan en Génesis y avanzan con cada libro. Cada tanda pasa una auditoría completa, no por muestra.

## Archivos
- Datos: `herramientas/*.py` → `datos/biblia.js` (`window.BIBLIA_DATOS`) y `datos/mapa-base.js`. Regenerar: `python -I herramientas/construir_datos.py --sin-red`. Detalle en `datos/LEEME.md`.
- Interfaz: `index.html`, `app.js` (núcleo puro `globalThis.BibliaNucleo`), `estilos.css`, `sw.js`. Pruebas: `node pruebas/probar.mjs`.
- Vista local: servidor en http://127.0.0.1:8765 (`preview_start` nombre «biblia»).
