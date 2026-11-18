# Guiones de video · Biblia narrada y actuada (piloto)

En vez de leer, el lector podrá **ver** cada pasaje: **un video por pasaje** (`gn-01.mp4`, `gn-98.mp4`…) que se
mostrará en la app dentro de la pantalla de su pasaje (la app todavía no lo integra). El video lee la RV1909
completa, letra por letra: el narrador lee todo salvo las palabras que el texto pone en boca de un personaje, que
las dice ese personaje.

Piloto: **gn-01** (Gn 1:1-19, la creación, días 1-4) y **gn-98** (Gn 45:1-15, José se da a conocer). Si sale bien
se repite para todo Génesis y luego libro a libro.

## Qué hay aquí

| Ruta | Qué es |
|---|---|
| `estilo.md` | Guía única de estilo, reglas fijas, voz del narrador e **instrucciones del Proyecto de ChatGPT**. |
| `fuentes/estilo.json` | Los mismos valores de estilo en formato que lee el script. |
| `fuentes/referencias.json` | Referencias de época (museo, inventario, datación, licencia, URL). Solo se usan las `comprobado: true`. |
| `fuentes/personajes/*.json`, `fuentes/objetos/*.json`, `fuentes/escenarios/*.json` | Fichas de personajes, objetos y escenarios (Elements). |
| `fuentes/Gn/gn-01.json`, `fuentes/Gn/gn-98.json` | Guion de cada video: escenas → tomas → partes (voz + texto exacto). |
| `Gn/gn-01.md`, `Gn/gn-98.md` | **Hoja de rodaje** generada: montaje, rótulos, continuidad, y por toma qué adjuntar, prompts y fidelidad. |
| `Gn/*.narracion.txt` | Guion de audio (narrador / personaje), sin corchetes. |
| `personajes/*.md`, `objetos/*.md`, `escenarios/*.md` | Fichas legibles con la hoja de referencia de cada Element. |
| `imagenes/estilo/`, `imagenes/personajes/`, `imagenes/objetos/`, `imagenes/escenarios/`, `imagenes/Gn/` | Láminas patrón, hojas de referencia e imágenes iniciales de cada toma. |
| `imagenes/_anteriores/` | Versiones reemplazadas al regenerar desde el Estudio (`<id con / → __>-<fecha>.png`). |
| `registro/revision.json` | Revisión de cada imagen en el Estudio: aprobada o rechazada, nota, fecha y `sha256` del archivo. |
| `registro/imagenes.jsonl` | Registro viejo del lote con Codex directo (16-nov); el Estudio lo muestra como historial. Lo nuevo va al registro de capa-ia. |

Los `.md` y `.txt` se generan; se editan las fuentes JSON y se regenera:

```text
python -I herramientas/guiones.py              valida y escribe las hojas (sale 0 si todo es válido)
python -I herramientas/guiones.py --sin-salida solo valida
python -I herramientas/guiones.py --autoprueba casos que deben fallar (y uno que debe pasar)
```

El script comprueba, entre otras cosas: que las escenas y las tomas cubren el pasaje entero de `datos/biblia.js`
en orden, sin huecos; que las partes de cada versículo reproducen exactamente el texto RV1909 (con corchetes); que
un personaje solo habla dentro de un discurso directo suyo en el texto; que toda cita es literal; que los ids
existen; que no se usa una referencia sin comprobar; que los prompts de imagen están en frases (sin `#`) y no
contienen términos prohibidos (halo, «God», sol antes del día cuarto…); y calcula la duración de cada toma
(palabras ÷ 150 por minuto) avisando si una toma de nivel A declara menos clips de 8 s de los necesarios.

**Objetos** (desde Gn 2–9, 2026-11-17): un objeto que se repite entre tomas (el arca, los dos árboles del huerto, la
paloma) tiene ficha propia en `fuentes/objetos/<id>.json`, con la misma forma que un escenario (`texto` con lo que
dice el versículo, `rasgos` con la interpretación del ilustrador, `hoja_referencia`, y `sin_laminas` si hace falta).
El id es el del catálogo de juego (`herramientas/juego/<Libro>.json`) cuando el objeto está allí, para que la lámina
del juego pueda salir de la misma hoja. Una toma los nombra en `"objetos": ["arca-noe"]`: su hoja se adjunta y la toma
espera a que exista. Lo que el texto no describe no se dibuja: no hay ficha de la señal de Caín (Gn 4:15).

Un personaje que no es persona en `datos/biblia.js` (la serpiente) deja `personas` vacío y explica por qué en
`sin_persona`. Todavía no puede tener voz propia en un guion: las voces van por persona.

Niveles de toma: **A** = clip de video (unos 3 por pasaje, en los momentos clave); **B** = imagen con movimiento
leve (y lipsync si habla alguien); **C** = narración sobre imagen fija.

## Imágenes con capa-ia y el Estudio

Las láminas patrón, las hojas de referencia y las imágenes iniciales de las tomas se generan con Codex (su
herramienta de imágenes integrada, sesión de ChatGPT) **a través de capa-ia** (`C:\PROYECTOS IA\capa-ia`), nunca
llamando a `codex` directamente. capa-ia elige el proveedor, aplica las reglas de «sin gasto adicional» (sin claves
de API ni créditos, tope del equipo) y el tope de la Biblia (`capa-ia.json` en la raíz: 30 % de la semana), y anota
cada trabajo con su prompt completo en su registro (`capa-ia registro --app biblia`).

```text
python -I herramientas/estudio.py              el Estudio: http://127.0.0.1:8766 (local, no se publica)
python -I herramientas/imagenes.py             lista lo pendiente (no genera nada)
python -I herramientas/imagenes.py --generar N genera N vía capa-ia, de una en una [--solo Gn/]
```

El orden es láminas → hojas (personajes, objetos, escenarios) → tomas (una toma espera a las hojas que usa). Se manda una imagen a la vez y el lote se
para en el primer fallo, al llegar a la cuota (`esperando_cuota`, con la hora de reinicio) o al tope de coste
(`bloqueado_coste`); nunca se reintenta solo.

Cada imagen lleva adjuntas las tres láminas patrón. Un escenario puede apartar alguna con
`"sin_laminas": ["patron-1-paisaje.png"]`, y entonces tampoco la llevan sus tomas. Sirve cuando el paisaje copia la
composición de la lámina en vez de solo su estilo, como pasó con la tierra seca y las lumbreras de la creación.
Siempre se adjunta al menos una lámina.

En el **Estudio** se ve cada lámina, hoja y toma con su imagen («Ilustración moderna (generada con IA)»), el prompt
exacto que se envía, su ficha y su historial, y se puede:

- **Aprobar** o **rechazar con nota** (se guarda en `registro/revision.json` con el `sha256` de la imagen: si el
  archivo cambia, vuelve a «pendiente de revisar»). Aprobar la lámina 2 renombra `patron-2-interior-codex.png` a
  `patron-2-interior.png`.
- **Editar el prompt** (`prompt_en` y `negativo_en` de la ficha, de la toma o de la lámina): antes de guardar se
  valida con `herramientas/guiones.py` y, si hay errores (p. ej. una palabra prohibida de `estilo.json`), no se
  escribe nada; si pasa, se guarda el JSON y se regeneran las fichas `.md`. La base de imagen, el negativo general
  y la base de movimiento de `estilo.json` no se editan desde el Estudio (cambian el estilo de todo).
- **Regenerar**: la imagen actual pasa a `imagenes/_anteriores/` y se pide otra; si la nueva falla, la anterior
  sigue ahí.
- **Generar pendientes** y ver la cola y el registro.

ChatGPT Images a mano sigue siendo la alternativa (pasos 1 y 3 de abajo): la imagen se guarda en su ruta y el
Estudio la revisa igual.

## Flujo para el usuario

Herramientas: **imágenes con capa-ia y el Estudio** (arriba) **o en ChatGPT Images** (suscripción, a mano) y **video y voz en Higgsfield** (web, modo
ilimitado, a mano: las generaciones ilimitadas solo valen usadas por una persona en la web; automatizarlas está
prohibido y el MCP o la CLI siempre gastan créditos). Lo marcado *(no verificado)* no consta en la investigación
de Higgsfield del 16-nov-2026: comprobarlo en la interfaz la primera vez y anotarlo.

### 0. Una sola vez

1. En ChatGPT, crear un Proyecto («GUIONES BIBLIA») y pegar en sus instrucciones el bloque **«Instrucciones del
   proyecto de ChatGPT»** de `estilo.md` (en ChatGPT web: Ajustes del proyecto → Instrucciones).
2. **Láminas patrón de estilo** (ver `estilo.md`): generar las tres en orden y que el usuario las apruebe. Se guardan en
   `guiones/imagenes/estilo/` y se adjuntan en **toda** generación posterior, de imagen y de video. El estilo es único
   para todo el proyecto (Estilo v1 · animación 2D de largometraje, decisión del usuario del 2026-11-16).
3. Descargar las referencias de época que use el pasaje desde su URL de Wikimedia Commons (están en cada hoja de
   rodaje y en `fuentes/referencias.json`). Guardar el archivo tal cual con su licencia.

### 1. Hojas de referencia (ChatGPT)

Para cada personaje y escenario del pasaje, abrir su ficha (`personajes/<id>.md`, `escenarios/<id>.md`), adjuntar
las referencias de época que indica y pegar el prompt del bloque «Hoja de referencia del Element». Guardar la imagen
como `guiones/imagenes/personajes/<id>.png` o `guiones/imagenes/escenarios/<id>.png`.

- **Descargar la imagen original, sin recortarla, retocarla ni hacerle captura**, para no quitar sus metadatos de
  procedencia (los términos de Higgsfield piden no quitar marcas de procedencia y rotular la IA).
- Revisar contra la ficha antes de seguir: edad, ropa, nada de halos ni corona, Benjamín no niño, diez hermanos
  distintos con Rubén y Judá reconocibles.

### 2. Elements (Higgsfield, Cinema Studio)

Subir cada hoja y guardarla como Element con el nombre que da la ficha (`JOSE_GOBERNADOR`, `BENJAMIN`,
`HERMANOS_GRUPO`, `SALA_CASA_JOSE`, `PATIO_CASA_JOSE`, `ABISMO_AGUAS`…). Los Elements (personajes, lugares y
objetos reutilizables, «Save to Elements») constan; *subir una imagen propia directamente como Element: no
verificado*. Si el grupo de diez hermanos no conserva las caras, crear Elements aparte para Rubén y Judá.

### 3. Imagen inicial de cada toma (ChatGPT)

En la hoja de rodaje (`Gn/<pasaje>.md`), para cada toma: adjuntar en el Proyecto de ChatGPT lo que indica
«Adjuntar en ChatGPT» (hojas de los personajes en cuadro, hoja del escenario, referencias de época) y pegar el
prompt entero. Guardar como `guiones/imagenes/Gn/<pasaje>-<toma>.png` (p. ej. `gn-98-t1.png`).

*Alternativa para comparar en el piloto*: generar las mismas hojas o imágenes con GPT Image dentro de Higgsfield
(Higgsfield lo ofrece; *si entra en el ilimitado: no verificado*). Anotar cuál sale más fiel y más consistente.

### 4. Clip desde la imagen (Higgsfield)

Nombres de modelos y controles (Unlimited, Start & End Frame, Lipsync Studio, Kling 3.0, Wan 2.7, Seedance 2.0):
según la investigación del 16-nov-2026, no comprobados en la interfaz; si difieren, usar el equivalente y anotarlo
en el registro.

Para las tomas A y B: abrir Cinema Studio, activar el interruptor **Unlimited**, subir la imagen inicial como
fotograma inicial (*Start & End Frame*, disponible en Plus/Ultra), añadir los Elements de la toma, pegar el
prompt de movimiento y las etiquetas de cámara `#`. Modelos en ilimitado con el plan Plus mensual: **Kling 3.0** o
**Wan 2.7** (1080p, 8 s) o **Seedance 2.0** (720p, 8 s). Generar tantos clips de 8 s como declara la toma.

- *Elegir 16:9 en la interfaz: no verificado* (la relación de aspecto no se encontró documentada).
- *Nombres exactos de las etiquetas de cámara: no verificados*; usar los equivalentes (estática, paneo, zoom…).
- Kling, Veo y Wan pueden generar audio propio: no usarlo; el audio es el de la narración. *(Si se puede apagar:
  no verificado.)*
- Las tomas C no necesitan clip: la imagen fija se monta con un movimiento suave en el editor.
- Si la voz dura más que los clips, estirar la imagen inicial con zoom lento en el editor, o generar los clips
  adicionales que indica la tabla («Clips 8 s decl./nec.»). No acelerar la voz.

### 5. Voces y lipsync (Higgsfield)

1. **Narrador**: generar el audio de cada toma con la línea `NARRADOR:` de `Gn/<pasaje>.narracion.txt` y la voz
   elegida (voces del ilimitado: Eleven v3, MiniMax Speech 2.8 HD, Seed Audio, VibeVoice, Seed Speech). *Dónde se
   genera solo voz, sin lipsync, dentro de Higgsfield: no verificado.*
2. **José** (gn-98): en **Lipsync Studio**, con el clip o la imagen de la toma y el texto de su línea (texto→voz
   con la voz elegida) o un audio propio. Usar siempre la misma voz. Consta que dice soportar español; *la duración
   máxima no está publicada*: si una línea larga falla (45:6-8, 45:9-11), partirla por versículos.
3. Nadie más habla: los hermanos y Benjamín no tienen líneas.

### 6. Montaje (editor de video del usuario)

En el editor que prefiera el usuario (fuera de Higgsfield), seguir el bloque **Montaje** de la hoja de rodaje:
rótulos de apertura en su orden (título, referencia, «Pasaje N de M», «Ilustración moderna (generada con IA)»,
«Texto: Reina-Valera 1909» y, opcional, «Antes:»), tomas en orden con sus transiciones, pista de narración y
diálogos, sin música en el piloto, y cierre con «En qué se basa» y «Sigue: …». Exportar `<pasaje>.mp4` en 16:9.
No quitar marcas de procedencia de Higgsfield. Si la voz de una toma dura más que sus clips, estirar la imagen
inicial con zoom lento o generar los clips adicionales que indica la tabla; no acelerar la voz.

## Controles del piloto

- **Halos y estética de Hollywood**: los negativos los nombran («Do not add … halos», «Avoid the look of a Hollywood
  blockbuster»). Nombrarlos puede atraerlos. Si aparecen, reformular en positivo, por ejemplo: «keep every head
  plain, lit only by natural light, like a frame from a 2D animated feature», y anotar en el registro qué funcionó.
- **Identidad entre tomas**: comparar cada imagen con la hoja de su personaje antes de pasar a video.
- **Orden del texto**: en gn-01, nada de sol, luna ni estrellas antes de la toma t10 ni de cielo antes de t5.

## Qué guardar de cada generación

Una línea por intento (también los descartados) en `guiones/registro/<pasaje>.jsonl` (crearlo al empezar):

```json
{"pasaje": "gn-98", "toma": "t1", "paso": "imagen inicial", "herramienta": "ChatGPT Images", "modelo": "el que muestre la interfaz", "fecha": "2026-11-20", "prompt": "copia exacta del prompt pegado", "adjuntos": ["jose.png", "hermanos.png", "benjamin.png", "casa-jose-sala.png", "C1", "A1"], "ajustes": "16:9", "creditos": "ilimitado | 0 | número", "archivo": "guiones/imagenes/Gn/gn-98-t1.png", "elegido": true, "notas": "qué falló o se cambió (filtros, rostro, ropa)"}
```

Para clips: modelo, resolución, duración, Elements y etiquetas de cámara en `ajustes`. Para voces: la voz y el texto
exacto. Si un filtro bloquea un prompt, anotar el texto exacto del aviso y cómo se reformuló.

## Cómo devolver los archivos para revisión

Dejar en la carpeta del proyecto (sin hacer commit todavía: los videos pesan y hay que decidir si van a git):

- `guiones/imagenes/personajes/<id>.png`, `guiones/imagenes/escenarios/<id>.png`
- `guiones/imagenes/Gn/<pasaje>-<toma>.png`
- `guiones/videos/Gn/<pasaje>-<toma>-<n>.mp4` (clips) y `guiones/videos/Gn/<pasaje>.mp4` (montado)
- `guiones/audio/Gn/<pasaje>-<toma>-<voz>.mp3`
- `guiones/registro/<pasaje>.jsonl`

Y pedir a Claude «revisa gn-98». Claude comprueba cada imagen y clip contra la fidelidad de su toma (nada que el
texto no diga presentado como dato, Dios sin figura, sin halos, sin anacronismos, orden del texto, sin adelantos),
la identidad de los personajes entre tomas, los rótulos y créditos, la duración real frente al Cálculo, y que el
registro esté completo; y propone cambios en las fuentes JSON.

## Decisiones pendientes del usuario

1. **Dios sin rostro ni figura humana** (solo luz, viento sobre el agua, voz): propuesta por defecto.
2. **Voz de Dios en gn-01 leída por el narrador**, sin voz aparte: propuesta por defecto.
3. **Época visual del Egipto de José**: supuesto por defecto Reino Medio (Beni Hasan, Meketre), con Rekhmire
   (Reino Nuevo) como contraste; posturas en `escenarios/casa-jose-sala.md`, sin decidir.
4. **Voz del narrador** y **voz de José** (Eleven v3, MiniMax Speech 2.8 HD u otra).
5. **Música**: ninguna en el piloto; Suno más adelante, opcional.
6. **Rótulo «Antes:»** con el resumen editorial del pasaje anterior: incluirlo o no (gn-98 lo propone).
7. ¿Se muestra la salida de los egipcios en gn-98 (45:1) o se empieza con la sala ya vacía?
8. La lumbrera mayor como sol y la menor como luna (inferido por su función; el texto no las nombra).
9. **ChatGPT Images o GPT Image en Higgsfield** para las imágenes: comparar en el piloto.
10. Si los videos y las imágenes se guardan en git o fuera del repositorio.
11. Cómo se integra el video en la app (no implementado).
12. **Desnudez de Gn 2:25** (Adán y Eva antes de 3:21): propuesta por defecto, nunca explícita en ningún perfil. Las
    hojas fijan el rostro y los visten con la túnica de pieles de 3:21; las tomas anteriores encuadran de hombros
    arriba o cubren con la vegetación, y desde 3:7 con el delantal de hojas de higuera.
13. **Voz de la serpiente** (Gn 3:1, 3:4-5): voz propia o leída por el narrador. Para darle voz propia, `guiones.py`
    tiene que admitir una voz que no es persona de `datos/biblia.js`.
14. **Querubines y espada encendida** (Gn 3:24): sin hoja todavía. El texto no describe a los querubines y el
    negativo general del estilo prohíbe alas; darles forma pide una decisión y, si llevan alas, una versión nueva
    del estilo.
15. **Ropa de Gn 4–11:26**: supuesto por defecto sin referencia de época (el texto no fecha estos relatos): pieles
    para Caín y Abel, como sus padres; lana lisa sin teñir para Noé y su familia y para los constructores de Babel,
    que descienden de ellos.
16. **Altar de Noé en el catálogo de juego**: tiene hoja (`objetos/altar-noe`) pero no es objeto en
    `herramientas/juego/Gn.json`, donde el primer altar es el de Abram. Lo mismo pasa con los ladrillos y el betún de
    Babel (`objetos/ladrillos-betun`) y con la tienda de Abram (`objetos/tienda-abram`).
17. **Ropa de Abram y los suyos (Gn 11:27 en adelante)**: supuesto por defecto, la gente de Asia occidental del mural
    de Beni Hasan (A1, A2), la misma referencia de los hermanos de José: lana de franjas y dibujos, cinta en el pelo
    de las mujeres. Los reyes de Canaán (Melquisedec, el rey de Sodoma) van sin corona y se distinguen por un tejido
    más rico, como los jefes de ese cortejo. El faraón de Gn 12 sigue la época supuesta del Egipto de José (n.º 3),
    con la esfinge de Senusret III del Met (F1) para el tocado y la barba.
18. **El ángel de Jehová** (Gn 16:7-12, ante Agar): sin hoja todavía. El texto no lo describe y el negativo general
    del estilo prohíbe alas. Opciones: sin figura, solo voz y luz, como Dios (n.º 1), o un varón sin alas.
19. **Animales partidos de Gn 15:9-17**: propuesta por defecto, nunca gráficos en ningún perfil: bultos en penumbra
    en dos hileras, sin sangre ni entrañas; el horno se deja ver y la antorcha pasa entre ellos, sin nadie que los
    lleve.
20. **Voces a coro de Babel** (Gn 11:3-4): los constructores no son personas de `datos/biblia.js`; mismo caso que
    la serpiente (n.º 13).
21. **Los tres varones de Mamre y Jehová** (Gn 18): el texto dice que Abraham ve «tres varones» (18:2) que comen
    (18:8), y después que habla Jehová (18:13, 18:17-33) sin decir si es uno de ellos; dos llegan a Sodoma como
    «ángeles» (19:1). Propuesta por defecto (hoja `personajes/varones-mamre`): tres hombres iguales, sin alas, halo ni
    luz propia, ninguno marcado como Dios (n.º 1); las palabras de Jehová no se ponen en la boca de ninguno, y desde
    18:22 Abraham queda solo «delante de Jehová», sin figura. Quién habla en 18:10 y 18:15 («dijo») y en 19:17 y
    19:21-22 queda para el guion. Alternativa: mostrar al tercero hablando con Abraham hasta 18:33.
22. **Voces sin persona en Gn 18–19**: los varones y ángeles (18:5, 18:9; 19:2, 19:12-13, 19:15) y el coro de los
    hombres de Sodoma (19:5, 19:9) no son personas de `datos/biblia.js`; mismo caso que la serpiente (n.º 13) y
    Babel (n.º 20): voces propias o leídas por el narrador.
23. **Ropa de Gerar** (Abimelec y Ficol, Gn 20–21, «tierra de los Filisteos»): no hay referencia comprobada.
    Supuesto por defecto, el mismo de los reyes de Canaán (n.º 17): sin corona ni casco, tejido rico de Beni Hasan
    (A1, A2); Ficol con una lanza en reposo para que se lea su cargo.
24. **Circuncisión** (Gn 17:10-14, 17:23-27; 21:4): propuesta por defecto, nunca se muestra en ningún perfil; se
    entiende por la narración (los varones de la casa reunidos, la tienda cerrada).
25. **Gn 19 en los perfiles**: el cerco de la casa de Lot (19:4-11), la lluvia de azufre y fuego (19:24-25), la
    mujer de Lot hecha sal (19:26) y las hijas en la cueva (19:32-35). Propuesta por defecto, nada explícito en
    ningún perfil: puertas, gritos y sombras en la noche; ciudades ardiendo a lo lejos, sin cuerpos; la estatua sin
    rostro de espanto y sin transformación paso a paso (`objetos/estatua-sal`); en la cueva, solo el vino y Lot
    dormido, con fundido. La narración se lee entera en los dos perfiles salvo que el usuario decida otra cosa.
26. **Voz del criado de Abraham** (Gn 24): no es persona de `datos/biblia.js` (el texto no lo nombra) y habla en buena
    parte de gn-48 a gn-51. Opciones: añadirlo a `datos/biblia.js` como persona sin nombre (como la mujer de Lot),
    admitir en `guiones.py` una voz que no es persona (como la n.º 13 y la n.º 20) o que lo lea el narrador. Lo mismo,
    en menor medida, para la madre de Rebeca (Gn 24:55, a la vez que Labán). No se le llama Eliezer: Gn 24 no lo
    nombra y no dice que sea el mayordomo de Gn 15:2.
27. **Una persona con varias hojas por edad**: `guiones.py` admite una sola ficha con «voz» por persona y exige que
    esa ficha esté en la toma donde habla. Desde Gn 17 ya choca: Abraham, Sara y Agar hablan con las hojas `abraham`,
    `sara` y `agar-mayor`, pero su voz está en `abram`, `sarai` y `agar` (Lot no: su voz está en `lot-mayor`, porque
    antes no habla). Isaac tiene dos hojas: `isaac-muchacho` (Gn 22, con la voz) e `isaac-adulto` (Gn 24–25, sin voz
    porque ahí no habla); cuando hable de adulto (Gn 26–27) chocará igual. Opciones: llevar la voz a la persona y no a
    la ficha, admitir la misma voz en varias fichas de una persona, o una ficha por persona con varias hojas por edad.
    Faltan además hojas por edad en gn-52 (Gn 25:9): Ismael solo tiene la de muchacho y allí tiene unos ochenta y
    nueve años; Isaac, unos setenta y cinco con la hoja de los cuarenta (cálculos en sus fichas).
28. **Edad visual de Isaac en Gn 22**: propuesta por defecto, un muchacho de unos dieciséis años, nunca un niño
    pequeño. El texto lo llama «muchacho» (Gn 22:5, 22:12) y le hace cargar la leña (Gn 22:6); por cálculo tiene como
    mucho unos treinta y siete años (Gn 23:1 y 17:17). Su edad no consta.
29. **Isaac atado, el cuchillo y el holocausto del carnero (Gn 22:9-13)**: propuesta por defecto, como la n.º 19,
    nada gráfico en ningún perfil. Las hojas muestran a Isaac de pie y libre, el cuchillo limpio junto a su funda, el
    carnero vivo en el zarzal y el altar con la leña sin encender; en el perfil niño, la mano con el cuchillo queda
    fuera de cuadro. La narración no cambia.
30. **Objetos con hoja que no están en el catálogo de juego** (como la n.º 16): el altar de Moriah
    (`objetos/altar-moriah`; el catálogo lo deja dentro del escenario «moriah» y de `lena-cuchillo`), el cántaro de
    Rebeca (`objetos/cantaro-rebeca`) y los camellos del criado (`objetos/camellos-siervo`); y, de Gn 18–21, la comida
    de Mamre (`objetos/comida-mamre`), la estatua de sal (`objetos/estatua-sal`) y el pozo de Beerseba con las siete
    corderas (`objetos/pozo-beerseba`; el catálogo tiene `pozos-isaac`, de Gn 26).
31. **Ropa de la familia de Nacor y de los hijos de Het**: supuesto por defecto, la gente de Asia occidental de Beni
    Hasan (A2) de la n.º 17, para Betuel, Labán, Rebeca y su madre (ciudad de Nacor, en Mesopotamia, Gn 24:10) y para
    Efrón y los hijos de Het (Hebrón, Gn 23:2). No hay referencia comprobada propia de ninguno de los dos lugares. El
    dueño de tierras (Efrón) y el cabeza de casa (Betuel) llevan tejidos más ricos, sin corona.
32. **Los hijos de Het y la persona Heth_1**: la hoja de grupo `hijos-het` usa la persona Heth_1 (Het, hijo de
    Canaán, Gn 10:15), como el catálogo de juego, para que el grupo pueda hablar en Gn 23:5-6. Confirmarlo, o pasar a
    una voz que no es persona (n.º 13, 20 y 26) o al narrador.
33. **Ismael anciano** (gn-52, hoja `personajes/ismael-mayor`): propuesta por defecto, el mismo rostro y la misma
    túnica corta de franjas rojas y blancas de la hoja de muchacho, para que se le reconozca, aparentando unos sesenta y
    cinco años: por cálculo tiene unos ochenta y nueve (Gn 25:7 y 16:16) y vive hasta los ciento treinta y siete
    (Gn 25:17), y tiene que verse mayor que Isaac en la misma toma. Alternativa: vestirlo como hombre del desierto de
    Parán (Gn 21:21), que el texto no describe. No habla, así que no lleva voz. Con esta hoja, de la falta de hojas por
    edad en gn-52 que señala la n.º 27 queda solo la de Isaac.
34. **Ciudades sin referencia de época** (Sodoma y Zoar, Gerar, la ciudad de los hijos de Het y la de Nacor; escenarios
    `sodoma`, `casa-lot-puerta`, `casa-lot-sala`, `llanura-zoar`, `gerar`, `puerta-het`, `pozo-nacor`, `casa-betuel`):
    supuesto por defecto, adobe sobre zócalo de piedra, techos planos, puertas de ciudad entre dos torres bajas con
    bancos, sin palacios, templos, zigurats ni almenas; la puerta de Het, con más piedra, para que no se confunda con la
    de Sodoma. `referencias.json` no tiene ninguna referencia comprobada de arquitectura de Canaán ni de Mesopotamia.
35. **Moriah sin identificar**: la hoja `escenarios/moriah` es un monte pelado, sin ciudad ni templo. 2 Crónicas 3:1
    llama Moriah al monte donde Salomón edificó el templo, y la tradición los identifica (Fuente externa; el libro aún no
    está en `datos/biblia.js`), pero Gn 22 no lo dice. Alternativa: sugerir el lugar sin nombrarlo.
36. **Escenarios que no están en el catálogo de juego** (como la n.º 16 y la n.º 30): `vista-sodoma`,
    `casa-lot-puerta`, `casa-lot-sala`, `llanura-zoar`, `cueva-lot`, `desierto-beerseba`, `puerta-het`, `pozo-nacor`,
    `casa-betuel` y `campo-isaac`. Los que sí están usan su id (`mamre`, `sodoma`, `gerar`, `beerseba`, `moriah`,
    `macpela`), aunque la hoja muestre una parte del lugar (la puerta de Sodoma, la sala del rey de Gerar). Además, el
    catálogo pone Gn 24:62-63 en `pozo-viviente`, pero el texto no dice que el campo donde Isaac sale a orar esté junto
    al pozo: `campo-isaac` no lo dibuja.
37. **Paisajes sin la lámina 1 desde el principio**: `mamre`, `vista-sodoma`, `llanura-zoar`, `beerseba`,
    `desierto-beerseba`, `moriah`, `macpela` y `campo-isaac` llevan `sin_laminas: ["patron-1-paisaje.png"]` antes de
    generarse, porque su paisaje de colinas secas es casi el de la lámina 1 y la creación ya copió su composición. Las
    fichas generadas dicen «copiaba su composición», que es la frase de `guiones.py` para el caso de la creación: aquí
    es preventivo. Alternativa: generarlos con las tres láminas y apartarla solo si copian.

## Pendiente del proyecto (fuera de los guiones)

- Las explicaciones al tocar de «crió», «haz» y «expansión» (Gn 1) **no existen** en `datos/explicaciones.js`
  (de los términos de Gn 1 solo está «lumbrera»). Añadirlas por el flujo de explicaciones
  (`herramientas/explicaciones/terminos-*.json`, auditoría, `python -I herramientas/explicaciones.py`); no se
  añadieron desde aquí.
