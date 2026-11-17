# Guía de estilo de los videos

Guía única para todos los videos de pasajes (uno por pasaje: `<pasaje>.mp4`). Los valores que se copian a las
herramientas viven en `guiones/fuentes/estilo.json`; este documento los repite literalmente y
`python -I herramientas/guiones.py` comprueba que coincidan.

Herramientas por defecto: **imágenes** (hojas de referencia de personajes y escenarios, imagen inicial de cada
toma) en **ChatGPT Images**, a mano; **videos y lipsync** en **Higgsfield** (web, modo ilimitado). Alternativa
para comparar en el piloto: GPT Image dentro de Higgsfield (si entra en el ilimitado: no verificado).

## Aspecto: Estilo v1 · animación 2D de largometraje

**Decisión del usuario (2026-11-16): todos los videos y todas las ilustraciones generadas de la app (fichas de
personaje, láminas del juego), de Génesis a Apocalipsis, usan este mismo estilo.** La referencia que dio el
usuario es el estilo de las películas de animación 2D de Warner. En los prompts se describe con palabras y nunca
se nombra: los filtros bloquean marcas, personajes con nombre y artistas vivos, y no se copia ninguna obra
concreta. Nada realista, nada pintado al óleo, nada 3D. Cambiarlo exige una decisión del usuario y una versión
nueva («Estilo v2»); en ese caso se rehacen las hojas de personaje y de escenario. Los registros históricos y el
arte antiguo que ya muestra la app (Doré, manuscritos, objetos de museo) no se tocan: son otra categoría.

- **Fotograma de largometraje de animación 2D dibujado a mano**: contornos oscuros limpios y marcados, colores
  planos con sombras de celuloide de borde duro (uno o dos tonos), rostros simplificados y algo angulosos
  (mandíbula firme, cejas definidas, ojos expresivos), fondos pintados con más textura y atmósfera que los
  personajes. Paleta apagada de tonos tierra (ocre, arena, oliva, terracota, azul profundo) y luz natural.
  Formato **16:9**.
- Proporciones adultas atléticas pero creíbles. Ni caricatura chibi, ni anime o manga, ni nada de superhéroes
  (trajes, capas, máscaras, emblemas, músculos exagerados).
- Personas, vestido y arquitectura del **Oriente Próximo antiguo según los registros de época** de
  `fuentes/referencias.json` (solo las de `comprobado: true`). Lo que no consta en un registro es interpretación
  del ilustrador y se rotula así en la ficha.
- Sin globos de diálogo, texto ni bordes de viñeta dentro de la imagen: el texto lo pone la narración.
- En los prompts tampoco se nombran estudios ni marcas: el validador rechaza «Warner», «DC», «Batman», «Disney»,
  «Pixar», «Marvel» y «superhero».
- **Nunca nombres de artistas vivos, de editoriales ni de estudios** en un prompt. Higgsfield bloquea a los
  artistas vivos y, además, no sería honesto. Tampoco nombres de personajes: los prompts describen a la persona
  («an Egyptian official of about thirty-nine…»), porque los filtros bloquean personajes con nombre. No consta
  cómo tratan a las figuras religiosas (no verificado).
- Prompts de imagen en **inglés y en lenguaje natural**, con frases completas. Las etiquetas `#` de cámara van
  **solo** en los prompts de video.
- El validador rechaza en los prompts de cada toma las palabras que arrastran a otro estilo («photorealistic»,
  «cinematic», «oil painting», «painterly», «watercolor», «3D», «anime», «manga»…; la lista está en
  `estilo.json`).
- Las láminas patrón aprobadas también se usan en la app: toda ilustración generada (ficha de personaje, lámina
  del juego, imagen del pasaje) sale de las mismas hojas de referencia, con el mismo estilo, y se rotula
  «Ilustración moderna (generada con IA)».

## Láminas patrón (anclas del estilo)

Las palabras no bastan para que cientos de videos se vean iguales. Antes de cualquier hoja de personaje se hacen
**tres láminas patrón**. Cuando el usuario las aprueba, se guardan en `guiones/imagenes/estilo/` y **se adjuntan
en toda generación**, de imagen y de video, hasta el Apocalipsis. No ilustran ningún pasaje y no se muestran en
la app.

| Lámina | Archivo | Qué fija |
|---|---|---|
| 1 · Paisaje sin personas | `guiones/imagenes/estilo/patron-1-paisaje.png` | trazo, color y luz exterior |
| 2 · Interior con dos personas | `guiones/imagenes/estilo/patron-2-interior.png` | rostros, ropa de lino, luz interior |
| 3 · Grupo al aire libre | `guiones/imagenes/estilo/patron-3-grupo.png` | grupos, barbas, ropa de lana, atardecer |

Se hacen en orden: la 1 sin adjuntos; la 2 y la 3, adjuntando la 1 ya aprobada. Cada prompt va después de la
base de imagen y antes de «Qué evitar», como en cualquier toma.

```text
Style reference panel number one, a landscape with no people: dry rocky hill country in the ancient Near East in the morning, with terraced slopes, scattered olive trees, a dirt path and a distant range of hills under a clear sky.
```

```text
Style reference panel number two, an interior with two people: inside a mud-brick room of an ancient Egyptian house lit by daylight from small high windows, a seated man in a white linen kilt writes on a papyrus roll while a standing woman in a simple white linen dress holds a clay jar; there are reed mats, a low wooden table and plastered walls with a painted border.
```

```text
Style reference panel number three, an outdoor scene with a group: a family of herders from western Asia walks beside their donkeys and goats along a dusty track at dusk; the men wear striped wool tunics and have dark beards, the women wear long patterned dresses, following Egyptian Middle Kingdom paintings of travelers from western Asia.
```

Traducción:
1. Paisaje sin personas: colinas secas y rocosas del antiguo Oriente Próximo por la mañana, con terrazas, olivos
   dispersos, un camino de tierra y montes lejanos bajo un cielo despejado.
2. Interior con dos personas: un cuarto de adobe de una casa egipcia con luz de ventanas altas. Un hombre sentado,
   con faldellín de lino, escribe en un rollo de papiro, y una mujer de pie, con vestido de lino, sostiene una
   vasija. Hay esteras, una mesa baja y paredes enlucidas con una cenefa pintada.
3. Grupo al aire libre: una familia de pastores de Asia occidental camina junto a sus asnos y cabras por un camino
   polvoriento al atardecer. Los hombres llevan túnicas de lana a rayas y barbas oscuras; las mujeres, vestidos
   largos estampados. Sigue las pinturas egipcias del Reino Medio de viajeros de Asia occidental (referencias A1
   y A2).

### Base de prompt de imagen (se antepone siempre)

```text
Create a frame from a 2D hand-drawn animated feature film, in a wide 16:9 frame and one consistent house style: clean, bold dark outlines; flat colors with crisp hard-edged cel shadows in one or two tones; simplified, slightly angular faces with strong jawlines, defined brows and expressive eyes; athletic but believable adult proportions. The backgrounds are softly painted, with more texture and atmosphere than the characters. Use a muted earthy palette of ochre, sand, olive, terracotta and deep blue, with natural light only: daylight, dusk or the glow of oil lamps. Base the people, their dress and the architecture on records of the ancient Near East, and keep the composition clear and readable. Match the line work, shading and palette of the attached style reference panels exactly.
```

Traducción: Crea un fotograma de un largometraje de animación 2D dibujado a mano, en encuadre ancho 16:9 y con un único estilo de la casa: contornos oscuros limpios y marcados; colores planos con sombras de celuloide nítidas, de borde duro, en uno o dos tonos; rostros simplificados y algo angulosos, con mandíbula firme, cejas definidas y ojos expresivos; proporciones adultas atléticas pero creíbles. Los fondos van pintados con suavidad, con más textura y atmósfera que los personajes. Paleta apagada de tonos tierra (ocre, arena, oliva, terracota y azul profundo) y solo luz natural: la del día, el atardecer o lámparas de aceite. Personas, vestido y arquitectura según los registros del Oriente Próximo antiguo, con una composición clara y legible. Iguala exactamente el trazo, el sombreado y la paleta de las láminas patrón de estilo adjuntas.

### Qué evitar (se añade siempre al final; GPT Image no tiene campo de negativo)

```text
Do not use photographic realism, 3D or CGI rendering, oil-paint or watercolor texture on the characters, anime or manga features, or chibi or cartoonish caricature. Do not add superhero costumes, capes, masks, emblems or exaggerated muscles. Avoid the look of a glossy video game or a Hollywood blockbuster. Do not add lens flares, neon, halos, glowing auras or wings. Do not include modern clothing or objects, medieval or Renaissance European costume, Roman armor or fantasy costume. Do not write any text, captions, speech balloons, panel borders, watermarks or logos. Show no blood or graphic violence and no heavy makeup.
```

Traducción: No uses realismo fotográfico, render 3D o CGI, textura de óleo o acuarela en los personajes, rasgos de anime o manga, ni caricatura chibi o infantil. No añadas trajes de superhéroe, capas, máscaras, emblemas ni músculos exagerados. Evita el aspecto de videojuego brillante o de superproducción de Hollywood. No añadas destellos de lente, neón, halos, auras luminosas ni alas. No incluyas ropa u objetos modernos, vestuario medieval o renacentista europeo, armadura romana ni vestuario de fantasía. No escribas texto, subtítulos, globos de diálogo, bordes de viñeta, marcas de agua ni logotipos. Sin sangre ni violencia gráfica, sin maquillaje marcado.

### Base de prompt de movimiento (video, se antepone siempre)

```text
Animate it like a 2D hand-drawn animated feature: keep the bold outlines, flat colors and hard-edged cel shadows of the starting image from the first frame to the last, never turning photographic, painted or 3D. Slow, restrained motion with a steady camera; cloth, water, air and light move naturally; no flashes and no sudden zooms.
```

Traducción: Anímalo como un largometraje de animación 2D dibujado a mano: conserva los contornos marcados, los colores planos y las sombras de celuloide de borde duro de la imagen inicial del primer al último fotograma, sin volverse nunca fotográfico, pintado ni 3D. Movimiento lento y contenido con cámara estable; telas, agua, aire y luz se mueven con naturalidad; sin destellos ni zooms bruscos.

En Higgsfield también se adjuntan las láminas patrón, si la herramienta admite referencias. Según la
investigación del 16-nov-2026, Cinema Studio admite varias (no verificado en la interfaz). Si un clip se vuelve
realista, pintado o 3D, se descarta y se repite: no se publica.

Detrás de la base van el prompt de la toma y sus etiquetas de cámara (`#static`, `#slow-push-in`…). Los nombres
exactos de las etiquetas de Cinema Studio **no están verificados**: hay que usar el equivalente que ofrezca la
interfaz (estática, mano alzada, zoom, paneo…).

## Reglas fijas

Las reglas 1 y 2 son propuestas por defecto hasta que el usuario decida; el resto son inamovibles.

1. **Dios nunca tiene rostro ni figura humana**: se muestra solo por sus efectos (luz, viento o aliento sobre el
   agua) y por la voz. *Propuesta por defecto; decisión pendiente del usuario.* El validador rechaza «God» y
   «Jesus» en los prompts positivos para que nadie lo pinte por descuido.
2. En gn-01 **la voz de Dios la lee el narrador**, sin eco ni voz aparte. *Propuesta por defecto; decisión
   pendiente del usuario.*
3. **Sin halos, nimbos ni auras** (también en el validador).
4. **Nadie dice palabras que el texto no le da**: un personaje solo habla dentro de su discurso directo en la
   RV1909 (lo comprueba el validador). Lo demás lo lee el narrador. Si el texto dice que alguien habló sin dar sus
   palabras (Gn 45:15), se le ve hablar sin audio.
5. **Orden del texto**: nada aparece antes de que el texto lo cuente (en gn-01, ni sol ni luna ni estrellas antes
   del día cuarto; ni animales antes del quinto). Cada guion puede declarar `prohibido_hasta` y el validador lo
   comprueba en los prompts.
6. **Sin adelantos**: el video de un pasaje no muestra lugares ni personas de pasajes siguientes (la app se lee en
   orden).
7. **Certeza**: cada dato de la ficha o de la toma dice si es Texto (con cita literal), Inferido, Cálculo (con
   pasos), Supuesto, Fuente externa o Interpretación del ilustrador.

## Perfiles

- `todos`: apto para niño y adulto (gn-01 y gn-98 lo son enteros).
- Cuando un pasaje tenga violencia o crudeza, la toma se hace en dos versiones: `adulto` (lo que dice el texto,
  sin regodearse) y `nino` (la misma acción sugerida fuera de cuadro o con un plano lejano). La narración no
  cambia: el texto bíblico se lee completo en los dos perfiles salvo decisión del usuario.

## Voz del narrador

- Español neutro, voz adulta, cálida y serena; ritmo pausado (~150 palabras por minuto, el valor con el que se
  calculan las duraciones); sin dramatizar ni música de fondo en el piloto.
- Pausa breve en cada «:» y «;» de la RV1909; pausa larga entre escenas.
- Pronunciación de formas antiguas de la Reina-Valera 1909: se leen como la ortografía actual equivalente; la
  tilde antigua (á, é, fué, vió, dió) no cambia la pronunciación (á = a, é = e, fué = fue, vió = vio, dió = dio);
  «crió» se lee cri-Ó. Las demás formas se leen tal cual: «púsolas» (PÚ-so-las), «señorease», «echóse», «priesa». La «â» y la «ê» de nombres como Issachâr o Rachêl se leen como
  «a» y «e». «EN» y «NO» en mayúsculas al comenzar capítulo se leen normal.
- Las palabras entre corchetes de la RV1909 («[están]», «[hizo]») las añadieron los traductores: se leen con
  naturalidad, sin énfasis; el guion de audio (`*.narracion.txt`) ya las trae sin corchetes.
- Voces disponibles en el ilimitado de Higgsfield según `higgsfield.md`: Eleven v3, MiniMax Speech 2.8 HD, Seed
  Audio, VibeVoice, Seed Speech. Elección: decisión pendiente del usuario.

## Rótulos obligatorios

Al inicio de cada video, en este orden: título del pasaje, referencia, «Pasaje N de M», y:

- «Ilustración moderna (generada con IA)»
- «Texto: Reina-Valera 1909»

En pasajes que continúan una historia, un rótulo opcional «Antes: …» con el resumen editorial del pasaje anterior
(de `datos/biblia.js`, rotulado «Resumen editorial»). Al final, créditos **«En qué se basa»** (texto bíblico y
referencias de época con museo, inventario, datación y licencia; lo demás, interpretación del ilustrador) y
«Sigue: <título del pasaje siguiente>». Las hojas de rodaje generan estos rótulos con datos existentes; nunca se
inventa narración.

## Instrucciones del proyecto de ChatGPT

Se pegan en las instrucciones del Proyecto de ChatGPT («GUIONES BIBLIA») y reemplazan cualquier versión anterior.
Están en inglés porque el modelo responde mejor; la traducción va debajo.

```text
You make illustrations for a Bible reading companion. Every image is a modern illustration of a specific Bible passage and must stay faithful to the text and to historical records.

Style (fixed for the whole project, from Genesis to Revelation): every image looks like a frame from a 2D hand-drawn animated feature film, always in a wide 16:9 frame. Clean, bold dark outlines; flat colors with crisp hard-edged cel shadows in one or two tones; simplified, slightly angular faces with strong jawlines, defined brows and expressive eyes; athletic but believable adult proportions; softly painted backgrounds with more texture and atmosphere than the characters. A muted earthy palette of ochre, sand, olive, terracotta and deep blue, and natural light only (daylight, dusk or oil lamps). Never photographic realism, 3D or CGI rendering, anime or manga features, chibi caricature, or anything from superheroes (costumes, capes, masks, emblems, exaggerated muscles). When I attach the style reference panels, match their line work, shading and palette exactly. Base people, dress and architecture on records of the ancient Near East; when I attach a photo of a museum object or tomb painting, follow its clothing, hairstyles, colors and architecture closely, but draw them in this animated style.

Fixed rules:
1. Never show God with a face, a body or any human or animal figure. God may only be suggested through light, wind or breath moving over water, never as a person, a hand or a dove.
2. No halos, glowing auras, wings or other supernatural decorations on anyone.
3. No anachronisms: no modern objects or clothing, no medieval, Renaissance or Roman costume, no fantasy armor, no Hollywood blockbuster look, no glossy computer graphics.
4. Never write text, captions, speech balloons, letters, panel borders, watermarks or logos inside the image.
5. Show nothing that my prompt does not ask for: no extra characters, animals or objects.
6. No blood or graphic violence unless I explicitly ask for an adult version.
7. Do not imitate the style of any living artist, publisher or studio.

Character and place consistency: when I attach a character reference sheet or a place reference sheet, keep that person's identity exactly — face, age, skin tone, hair, beard, build and clothing — and keep the place's architecture and colors, changing only the pose, expression, angle and light that my prompt describes. If I attach several sheets, each person in the scene must match their own sheet.

Always produce one 16:9 image per request unless I ask for a reference sheet, which uses a plain light grey background. If a request conflicts with these rules, follow the rules and tell me what you changed.
```

Traducción: Haces ilustraciones para un compañero de lectura de la Biblia. Cada imagen es una ilustración moderna
de un pasaje concreto y debe ser fiel al texto y a los registros históricos.

Estilo, fijo para todo el proyecto, de Génesis a Apocalipsis:
- Cada imagen parece un fotograma de un largometraje de animación 2D dibujado a mano, siempre 16:9.
- Contornos oscuros limpios y marcados, colores planos con sombras de celuloide de borde duro, rostros
  simplificados y algo angulosos, proporciones adultas atléticas pero creíbles, y fondos pintados con más
  textura que los personajes.
- Paleta apagada de tonos tierra (ocre, arena, oliva, terracota, azul profundo) y solo luz natural.
- Nunca realismo fotográfico, 3D, anime, manga, caricatura chibi ni nada de superhéroes.
- Con las láminas patrón adjuntas, igualar su trazo, su sombreado y su paleta.
- Personas, vestido y arquitectura según los registros del Oriente Próximo antiguo. Si se adjunta la foto de un
  objeto de museo o de una pintura de tumba, seguirla de cerca, pero dibujada en este estilo de animación.

Reglas fijas:
1. Dios nunca tiene rostro, cuerpo ni figura humana o animal. Solo se sugiere con luz, viento o aliento sobre el
   agua; nunca como persona, mano ni paloma.
2. Sin halos, auras ni alas.
3. Sin anacronismos ni estética de Hollywood o CGI.
4. Nunca texto, globos, letras, bordes de viñeta, marcas de agua ni logotipos.
5. Nada que el prompt no pida.
6. Sin sangre ni violencia gráfica, salvo que se pida una versión adulta.
7. No imitar el estilo de ningún artista vivo, editorial ni estudio.

Consistencia: con una hoja de referencia adjunta, mantener exactamente la identidad de la persona (rostro, edad,
piel, pelo, barba, complexión, ropa) y la arquitectura y los colores del lugar. Solo cambian la pose, la
expresión, el ángulo y la luz. Con varias hojas, cada persona según la suya.

Siempre una imagen 16:9 por pedido, salvo las hojas de referencia, que van con fondo gris claro liso. Si un pedido
choca con estas reglas, se siguen las reglas y se dice qué se cambió.
