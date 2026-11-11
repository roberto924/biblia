# Catálogo de juego (personajes, objetos, escenarios, genealogías) — diseño

Fecha: 2026-11-11 · Estado: aprobado en conversación, pendiente de revisión del constructor.

## Intención
El usuario quiere que estudiar la Biblia sea entretenido y motivante: recompensas, desbloqueos, minijuegos ligados a cada historia. El juego completo (desbloqueo con preguntas, puntos, ranking, misiones) se construye **por partes y más adelante**. Ahora, mientras se ingresan los libros uno a uno (hoy Génesis y Éxodo; el último es Apocalipsis), se arma un **catálogo ordenado** de todo lo que aparece, para que el juego tenga sentido cuando se construya, y se proponen minijuegos por historia para que el usuario los revise.

## Decisiones del usuario (2026-11-11)
- Personajes, **objetos** y **escenarios** se coleccionan. Las fichas muestran **información detallada de todo lo que se sabe** de cada uno.
- Las **genealogías no desbloquean** personajes. Quien aparece solo en una genealogía en toda la Biblia es personaje de **nivel bajísimo o NPC**. La app debe saber qué fragmentos son genealogías.
- **Nivel** del personaje según cuánto material hay sobre él (Jesús: altísimo, «ultrapoderoso»). Los personajes tendrán habilidades para juegos futuros; los objetos se usan en minijuegos o potencian personajes; los escenarios son minijuegos que suman puntos (pocas partidas al día).
- **Desbloqueo futuro** (no en esta fase): disponible cuando ya se leyó todo lo del personaje; preguntas de selección con tiempo corto, un par de oportunidades, espera de un par de días si falla; puntos = mejor puntaje por set; ranking. Al principio todo local; después servidor con análisis antitrampas.
- Las preguntas existen **solo para desbloquear**; la lectura sigue siendo acompañamiento sin examen.
- Minijuegos: los propongo yo, **acordes a la historia y al capítulo**; el usuario los revisa.
- Láminas con imagen «lo más similar a la realidad» (fase aparte): basadas en registros de época, rotuladas «Ilustración moderna» con su base.

## Cuándo se puede desbloquear un personaje (usuario, 2026-11-11)
- **Aparición** = el personaje está presente en el relato: actúa, habla o se le habla (aunque no se le nombre). **Mención posterior** = otros lo nombran más adelante («el Dios de Abraham», Hebreos 11): suma a la ficha y al nivel, **no** retrasa el desbloqueo.
- El catálogo divide el texto en **historias** (arcos: Creación y Edén, Noé, Abraham, Jacob, José, Moisés en Egipto, Éxodo y Sinaí…). Un personaje es **principal** en las historias donde es actor central.
- El personaje queda **listo para la prueba** al **terminar de leer el capítulo** que contiene su **última aparición en la primera historia donde es principal** (Abraham: su sepultura está en Gn 25:9-10 → listo al terminar Gn 25). Así se responde con el capítulo completo leído y está disponible para el juego de esa historia. «Terminar el capítulo» = leídos todos los pasajes que cubren ese capítulo.
- Si vuelve a ser principal en otra historia (Moisés en Números), al terminarla **sube de nivel** con un set de preguntas nuevo (fase futura).
- Personajes secundarios (no principales en ninguna historia): listos al leer su última aparición en el relato.
- Mientras no exista la prueba de preguntas, «listo para la prueba» = **desbloqueado** en la colección (reemplaza el desbloqueo actual por primera aparición; antes de leer la última aparición la ficha se ve «en curso» con el avance).

## Objetivos de esta fase
1. Catálogo de Génesis y Éxodo: genealogías, personajes (apariciones y nivel provisional), objetos, escenarios, cada dato con su certeza.
2. Fichas en la app: personajes enriquecidos y fichas nuevas de objetos y escenarios.
3. Documento de ideas de minijuegos y habilidades por historia, para revisión del usuario.
4. Dejar fijado el proceso para cada libro siguiente (Levítico en adelante).

## No objetivos (ahora)
Preguntas de desbloqueo, puntos, ranking, cuentas, servidor, minijuegos jugables, imágenes nuevas de láminas.

## Antiobjetivos
- Un dato sin fuente o inventado. Las habilidades y poderes son **invención del juego** y nunca se presentan como dato bíblico.
- Contar como «aparición» una mención en genealogía.
- Romper la colección actual (hoy se desbloquea al leer la primera aparición) antes de que exista el desbloqueo con preguntas.

## Datos
Fuentes por libro escritas por agentes en `herramientas/juego/<libro>.json` (Gn, Ex…); `herramientas/juego.py` las verifica y genera `datos/juego.js` → `window.BIBLIA_JUEGO`. Sin red, Python stdlib, `python -I`, sale ≠ 0 si falla una verificación.

```js
BIBLIA_JUEGO = {
  generado, libros: ["Gn","Ex"],
  genealogias: [{ id, inicio: "Gn 5:1", fin: "Gn 5:32", titulo, cita }],
  historias:   [{ id: "abraham", titulo: "Abraham", inicio: "Gn 11:27", fin: "Gn 25:11", principales: ["Abraham_1", "Sarah_1"] }],
  // en cada personaje, además: menciones_posteriores [{ref}], listo: { historia, ref } (calculado por el script: última aparición en su primera historia principal)
  personajes: { "Adam_1": {             // ids de personas de biblia.js
    apariciones: [{ inicio: "Gn 2:7", fin: "Gn 3:24" }],   // presente aunque no se le nombre (pronombre, «el hombre»), sin genealogías
    versiculos: 74,                      // calculado por el script desde apariciones
    nivel: 6, npc: false,                // calculados por el script (fórmula abajo)
    resumen,                             // 1–2 frases, editorial
    datos: [{ texto, certeza: "texto"|"inferido", ref, cita }],          // todo lo que dice el texto
    externo: [{ texto, fuente, url }]    // «Fuente externa» (historia, arqueología, tradición), opcional
  }},
  objetos:    { "arca-noe": { nombre, tipo, apariciones, personas, lugares, tabernaculo?: idPieza, resumen, datos, externo } },
  escenarios: { "eden":     { nombre, lugar?: idLugar, apariciones, personas, objetos, resumen, datos, externo } }
}
```
- Ejemplos reales de campos visibles (para que los agentes compartan grafía): `resumen` de Adán: «Primer hombre, formado del polvo y puesto en el huerto del Edén.»; un `dato`: `{texto: "Vivió 930 años", certeza: "texto", ref: "Gn 5:5", cita: "novecientos y treinta años"}`.
- **Nivel provisional** (mi decisión, ajustable al final): `nivel = 1 + floor(log2(versiculos))`, tope 12; `npc = true` si no tiene apariciones fuera de genealogías (nivel 0). Se recalcula con cada libro.
- Profundidad según importancia: personajes de nivel ≥ 5 con datos completos; nivel 1–4 con lo esencial; NPC con una línea.
- El script verifica: citas literales del versículo; refs existentes; apariciones dentro de los libros cargados y sin solaparse con genealogías; ids de personas/lugares/piezas existentes; `externo` siempre con fuente y url; **lista de hechos que deben estar** (Gn 5, Gn 10, Gn 11:10-32, Gn 25:12-18, Gn 36, Gn 46:8-27, Ex 6:14-25 son genealogías; Adán aparece en Gn 2:7; el arca de Noé en Gn 6:14; la vara de Moisés en Ex 4:2; el Edén es escenario).

## Ideas de minijuegos
`docs/juego/ideas-<libro>.md`: por historia o capítulo, minijuegos propuestos (cómo se juega, con qué personaje/objeto/escenario, citas en que se basa), habilidades propuestas por personaje y efecto de cada objeto. Todo rotulado como propuesta. No se construye nada hasta que el usuario elija.

## Interfaz
- Vista «Colección» (la de personajes actual ampliada) con tres grupos: Personajes, Objetos, Escenarios.
- Ficha de objeto y de escenario: resumen, «Lo que dice el texto» (datos con insignias Texto/Inferido y cita), «Fuera de la Biblia» (Fuente externa), apariciones con enlace al pasaje, relacionados (personas, lugares, pieza del tabernáculo, imágenes del catálogo de recursos si existen).
- Ficha de personaje: se añaden nivel provisional (o NPC), apariciones y «Todo lo que se sabe».
- Objetos y escenarios se obtienen como hoy los personajes: al leer su primera aparición. El perfil niño respeta el filtro de contenido.

## Proceso por cada libro nuevo
Texto y acompañante (como hasta ahora) → catálogo del libro (`herramientas/juego/<libro>.json`) → regenerar y verificar → `docs/juego/ideas-<libro>.md` → el usuario revisa ideas.

## Respuestas a la revisión del constructor (decisiones del orquestador, ajustables)
1. **Colección actual:** *(sustituido por «Cuándo se puede desbloquear», decisión del usuario)* los personajes se desbloquean al leer `listo.ref`; se ajustan sus pruebas. Objetos y escenarios usan el `inicio` de su primera `aparicion`. Un personaje solo de genealogía sigue apareciendo en la colección como hoy, marcado NPC.
2. **Alcance:** todas las personas de `biblia.js` tienen entrada. El script deriva apariciones base de `menciones` (versículos con el nombre) quitando las genealogías; los agentes añaden rangos de presencia sin nombre («el hombre», pronombres) y `datos` para los personajes con nivel base ≥ 3. NPC y nivel 1–2: solo lo derivado más un `resumen` de una línea.
3. **Conteo:** `versiculos` = número de versículos distintos en la unión de rangos (un rango puede cruzar capítulos dentro de un libro; nunca cruza libros: se parte en dos).
4. **Texto canónico:** RV1909 de `biblia.js`; las citas se verifican contra él. `externo`: el agente que lo escribe abre la URL al redactarlo; el script solo exige fuente y url `https`. Fuentes aceptables: museos e instituciones, enciclopedias académicas, Wikipedia como secundaria (rotulada así).
5. **Perfil niño:** se reutilizan las marcas por versículo de `datos/contenido.js`: en perfil niño, un dato cuya `ref` está marcada como contenido alto se pliega como el resto de la app. No hay campo nuevo.
6. **Ideas de minijuegos:** 1–3 por historia o grupo de pasajes, cada una en 3–6 líneas (cómo se juega, con qué, citas), más una línea de habilidad por personaje de nivel ≥ 5 y una de efecto por objeto.
7. **Ids:** lugares = `lugares[].id` de `biblia.js`; piezas = `piezas` de `tabernaculo.js`. `sw.js` precachea `datos/juego.js` como los demás datos.

## Para el constructor
Diseño visual de las fichas, orden de agrupación, fórmula exacta de presentación del nivel, cómo se reparte el trabajo entre agentes.
