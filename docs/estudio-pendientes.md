# Estudio · pendientes menores

Minor que dejaron las revisiones del Estudio (2026-11-17) y que se aplazaron porque no afectaban al primer uso real. Ninguno rompe datos. Se arreglan cuando se toque esa zona.

## Servidor y lote (`herramientas/estudio.py`, `estudio_datos.py`)
- «Regenerar» aparta la imagen a `_anteriores/` antes de saber si capa-ia la hará. Si responde `esperando_cuota`, `bloqueado_coste` o `fallo`, la imagen queda apartada sin nueva. Lo mismo pasa con «Detener» durante un regenerar.
- Detener en el último id da «terminado» en vez de «detenido».
- Carrera posible en el 409 de `/api/prompt`.
- `_cuerpo` lee sin timeout.
- `/api/datos` calcula el sha256 de cada imagen en cada llamada.
- Se omite el aviso de cuota no leída.
- Las reglas de las láminas están duplicadas fuera de `guiones.py`.
- El falso de `capa_ia` de las autopruebas está duplicado.
- `estudio.py` pasa de 650 líneas: conviene separar las autopruebas.
- Una excepción del lote se anota sin id («Parado por un fallo en …» no dice en qué imagen): `actual_id()` ya es `None`.
- La prueba de independencia del fixture es casi tautológica.
- `refs[-1]` supone que la hoja de escenario va al final.

## Página (`herramientas/estudio/estudio.js`, `estudio.css`)
- «Generar pendientes» supera el tope de 200 del servidor cuando esté Génesis entero.
- El sondeo del lote arranca siempre tras el 202.
- `decodeURIComponent` sin `try`.
- Las claves de los desplegables usan el índice.
- El registro se ordena por fecha como texto.
- Sin `reinicio_en`, la cabecera muestra el semanal.
- El «~0,2 %» por imagen está escrito a mano.
- `body` con `overflow-x: hidden`.
- Aprobar y Rechazar siguen activos durante un lote.
- El error de una tarjeta persiste hasta la siguiente acción exitosa.
- Esc mientras «Validando…» deja el prompt guardado y el negativo no, sin avisar.

## Observado en el primer uso real
- La frase `NO_REPETIR` no impide que los paisajes de la creación copien la composición de la lámina 1 (árbol a la izquierda, rocas abajo, mismas colinas). Opciones: rehacer la lámina 1 o no adjuntarla a esos escenarios (decisión del usuario).
