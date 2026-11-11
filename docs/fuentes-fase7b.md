# Fuentes verificadas · Fase 7b (hebreo, griego, audio, manuscritos, video)

Verificado el 2026-11-11. «Verificado» = abrí la URL (curl o WebFetch) y leí el dato citado. Lo que no pude abrir o confirmar está en «No verificado». Los conteos de versículos los medí sobre los archivos descargados.

## 1. Texto hebreo (Génesis y Éxodo)

| Recurso | URL verificada | Licencia / condiciones | Formato | ¿Sirve? | Nota |
|---|---|---|---|---|---|
| OSHB / morphhb (WLC = Códice de Leningrado) | https://raw.githubusercontent.com/openscriptures/morphhb/master/wlc/Gen.xml (1,86 MB) y `.../wlc/Exod.xml` (1,52 MB), ambos HTTP 200 | Repo: «Lemma and morphology data are licensed under a Creative Commons Attribution 4.0 International license»; «The text of the WLC remains in the Public Domain». LICENSE.md: «based on The Westminster Leningrad Codex, which is in the public domain» | OSIS XML; `<verse osisID="Gen.1.1">` con `<w lemma= morph=>` por palabra; con vocales y cantilación. Cabecera: `refSystem Bible.MT` | **Sí** (atribución CC BY 4.0 para lemas y morfología) | **No incluye transliteración.** Habría que generarla y rotularla «Transliteración moderna (cálculo)». Cabecera: «Updated to WLC version 4.20» (2016). |

### Numeración TM (hebrea) frente a RV1909/inglesa (medida)
Versículos por capítulo medidos: OSHB (hebreo) frente a Swete (numeración inglesa, igual que la RV en estos capítulos): Gn 31 = 54 frente a 55; Gn 32 = 33 frente a 32; Ex 7 = 29 frente a 25; Ex 8 = 28 frente a 32; Ex 21 = 37 frente a 36; Ex 22 = 30 frente a 31. Comprobar la RV1909 contra `datos/biblia.js` (no la medí).

| Hebreo (TM/OSHB) | Inglesa/RV/Swete | Verificado |
|---|---|---|
| Gn 32:1 | Gn 31:55 | Sí: TVTMS (línea `Gen.31:55 → Gen.32:1`) y conteo |
| Gn 32:2–33 | Gn 32:1–32 | TVTMS: desplazamiento de 1 |
| Ex 7:26–29 | Ex 8:1–4 | Por conteo (7: 29 frente a 25; 8: 28 frente a 32) |
| Ex 8:1–28 | Ex 8:5–32 | Por conteo |
| Ex 21:37 | Ex 22:1 | Por conteo |
| Ex 22:1–30 | Ex 22:2–31 | Por conteo |

| Recurso | URL | Licencia | Formato | ¿Sirve? | Nota |
|---|---|---|---|---|---|
| **TVTMS** (STEPBible, Tyndale House) | https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/Versification/TVTMS%20-%20Translators%20Versification%20Traditions%20with%20Methodology%20for%20Standardisation%20for%20Eng%2BHeb%2BLat%2BGrk%2BOthers%20-%20STEPBible.org%20CC%20BY.txt (5,8 MB, HTTP 200) | CC BY 4.0: «Include any part of this data in software or publications ... without requesting permission» | TXT tabulado; líneas tipo `Gen.31:55<TAB>Gen.32:1`; cubre Eng+Heb+Lat+Grk | **Sí** | Es la tabla de correspondencia abierta. Contiene mucho más que Gn/Ex: filtrar. Solo leí líneas de ejemplo; las columnas se explican en un Google Doc que no abrí. Comprobar antes de usar. |
| bcv-commons/versification | https://huggingface.co/datasets/bcv-commons/versification | No pude leerla | n/d | No verificado | Solo por buscador (dice derivar del TVTMS). |
| morphhb `remapVerses` | https://www.npmjs.com/package/morphhb | n/d | JS | No verificado | Solo por buscador. |

## 2. Texto griego de la Septuaginta

| Recurso | URL verificada | Licencia / condiciones | Formato | ¿Sirve? | Nota |
|---|---|---|---|---|---|
| **LXX-Swete-1930** (Eliran Wong) | https://github.com/eliranwong/LXX-Swete-1930; CSV en `https://raw.githubusercontent.com/eliranwong/LXX-Swete-1930/master/`: `00-Swete_versification.csv`, `01-Swete_word_with_punctuations.csv`, `02-Swete_word_without_punctuations.csv`, `03-Swete_SBL_transliterations.csv` (HTTP 200) | Repo: **GPL-3.0** (LICENSE leído). Swete (1909, Cambridge UP) es de dominio público; el README enlaza escaneos en archive.org (vol. I: `theoldtestamenti00unknuoft`). Texto digital compilado por P. Amicarelli (módulo BibleWorks) | CSV por palabra (id de palabra y texto); el CSV de versificación mapea id de palabra a `Gen.31:55` / `Exo.1:5` | **Con condiciones** | Sirve y trae transliteración SBL. Pero el conjunto digital es **GPL-3.0**: incrustarlo en una app JS pública implicaría distribuirlo bajo GPL. Decisión de licencia pendiente del dueño. El README dice que la «modern Greek pronunciation» está planificada (no la vi hecha). |
| Numeración Swete | CSV de versificación | n/a | n/a | n/a | Usa la numeración inglesa/RV (medido: Gn 31 = 55, Gn 32 = 32; Ex 7 = 25, 8 = 32, 21 = 36, 22 = 31). Códigos `Gen`, `Exo`. El emparejamiento con RV1909 es directo; solo el hebreo necesita tabla. |
| Rahlfs-Hanhart | n/a | No la abrí | n/a | No | Evitar (restricciones según tu aviso; no lo comprobé). |

## 3. Audio

| Recurso | URL verificada | Licencia / condiciones | Formato | ¿Sirve? | Nota |
|---|---|---|---|---|---|
| Mechon Mamre (hebreo, por capítulo) | https://www.mechon-mamre.org/about.htm | «The audio (MP3) recordings presented on this site are used with permission from Talking Bibles International © 1992 (to request permission to use recordings write ...)»; «not chanted with a melody, but ... clearly pronounced in Sephardic-style Hebrew» | MP3 por capítulo (la ruta `/mp3/` da 403; no vi un archivo) | **No** para incrustar o redistribuir; con condiciones solo como enlace saliente | Derechos de Talking Bibles International, no del sitio: requiere permiso. Sin sincronía por versículo (no consta). |
| Word-by-word Hebrew audio (Eliran Wong, Open Hebrew Bible) | https://github.com/eliranwong/MP3_BHS5_word-by-word | CC BY-NC 4.0; «Permissions beyond the scope ... may be available» | MP3 por palabra y lexema (orden ETCBC BHSA 4c) | Con condiciones | Solo no comercial y con atribución; no es por capítulo. No confirmé si es voz humana o sintética. |
| Bible Brain / Digital Bible Platform (Faith Comes By Hearing) | https://www.faithcomesbyhearing.com/bible-brain/license (última modificación 4/15/21) | Hay que dar nombre, email, descripción de uso y «request an API Key»; FCBH aprueba cada solicitud; la clave puede revocarse o limitarse; no se comparte. El apartado «Guidelines» salió cortado | API REST JSON con clave | Con condiciones | **No confirmé que haya audio en hebreo bíblico ni griego LXX** en su catálogo. |
| bible.is | https://www.faithcomesbyhearing.com/audio-bible-resources/bible-is?language_name=Hebrew | Pie «© 2026 Faith Comes By Hearing» | n/d | No verificado | La página no listó versiones. |
| Rabbi Dan Be'eri (hebreo) | https://archive.org/details/TanakhAudioRecordingByRabbiDanBeeri-BookByBook | No leí licencia | MP3 por libro | No verificado | Solo por buscador. |
| koinegreek.com (Génesis LXX, Vaticano) | https://koinegreek.com/audio | Sin licencia declarada (buscador); descargas solo a patrocinadores | Audio | No | Solo escuchar en su sitio. |
| Audible / ElevenReader (LXX) | n/d | Comerciales | n/d | No | Sin licencia de uso. |
| **Voz del navegador (Web Speech API)** | https://readium.org/speech/docs/WebSpeech.html (leído) | n/d | `speechSynthesis` | Con condiciones | Confirmado: `getVoices()` devuelve `name, voiceURI, lang, localService, default`; en Android la lista varía por fabricante y versión, y Chrome para Android «returns an unfiltered list of languages/regions» (no sirve para saber si hay voz he-IL o el-GR). Windows: una respuesta de comunidad Microsoft cita «Hila» y «Avri» (son voces neuronales de Azure en la nube, no confirmadas como locales del navegador). iOS: he-IL y el-GR desde iOS 8 (blog antiguo, useyourloaf.com). **Todas son pronunciación moderna** (hebreo israelí, griego moderno), no hebreo bíblico ni koiné. |

**Conclusión:** no hallé grabación del hebreo bíblico por capítulo con licencia abierta ni una del griego LXX. Rótulo honesto: «Voz sintética moderna».

## 4. Manuscritos

### (a) Testigos principales
Fechas y contenidos tomados de Wikipedia (secundaria); para la app citar la institución como registro.

| Testigo | Fecha | Contenido en Gn/Ex | Facsímil digital | ¿Sirve? |
|---|---|---|---|---|
| Códice de Leningrado (Firkovich B 19 A, Bibl. Nacional de Rusia) | colofón 1008 (posible 1009) | Pentateuco completo | https://archive.org/details/Leningrad_Codex (988 págs., B/N); `.../Leningrad_Codex_Color_Images`; Commons `Category:Codex_Leningradensis`. Licencia del facsímil no declarada | Con condiciones: enlazar sí; incrustar, verificar licencia |
| Códice de Alepo (Museo de Israel) | c. 920 | **Génesis ausente; Éxodo casi todo ausente** (fragmento de Éx 8 publicado en 2016) | https://www.aleppocodex.org/ (HTTP 200); Commons `Category:Aleppo Codex` | Como testigo famoso sí, pero **no testifica Gn/Ex**: decirlo |
| Códice Vaticano (Vat. gr. 1209) | c. 300–350 | Gn y Ex, pero **Gn 1:1–46:28a es reposición del s. XV** | https://digi.vatlib.it/view/MSS_Vat.gr.1209 (HTTP 200) | Con condiciones (licencia no leída) |
| Códice Sinaítico | c. 325–360 | Solo Gn 23:19–24:46 (fragmentos); **sin Éxodo** | codexsinaiticus.org no respondió; no verificado | No para Ex |
| Códice Alejandrino (BL Royal MS 1 D V–VIII) | c. 400–440 | Pentateuco; dañados Gn 14:14–17, 15:1–5, 15:16–19, 16:6–9 | El enlace BL de Wikipedia es del NT y está archivado; no verificado | Con condiciones |
| Pentateuco Samaritano, ms. completo más antiguo: Cambridge Add. 1846 | 1100 | Pentateuco completo | https://cudl.lib.cam.ac.uk/view/MS-ADD-01846/1 (dado por Wikipedia; no abierto) | Con condiciones |

### (b) Rollos del Mar Muerto con Génesis y Éxodo
Fuente: https://en.wikipedia.org/wiki/List_of_manuscripts_from_Qumran_Cave_4 (wikitexto; cita a Fitzmyer 2008 y enlaza a la Biblioteca Digital). **Tiene erratas visibles** (p. ej. «Exodus 1:1–6,16–12»); contrastar con DJD antes de publicar. La datación es solo la etiqueta paleográfica de la lista (Hasmonea, Herodiana), no una fecha numérica.

| Sigla | Contenido (según la lista) | Datación (según la lista) | Enlace (base `https://www.deadseascrolls.org.il/explore-the-archive/manuscript/`; HTTP 200, página SPA) |
|---|---|---|---|
| 4QGen-Exod-a (4Q1) | Gn 8:20–21; Ex 1–4; 5:3–17; 6:4–21,25; 7:5–13,15–20; 8:20–22; 9:8; 22:14; 27:38–39,42–43; 34:17–21 | Hasmonea | `4Q1-1` |
| 4QGen-b (4Q2) | Gn 1:1–27; 2:14–19; 4:2–4; 5:13 | no figura | `4Q2-1` |
| 4QGen-c (4Q3) | Gn 40–41 | Herodiana | `4Q3-1` |
| 4QGen-d (4Q4) | Gn 1:18–27 | Hasmonea | `4Q4-1` |
| 4QGen-e (4Q5) | Gn 36–37; 40–43; 49 | Herodiana | `4Q5-1` |
| 4QGen-f (4Q6) | Gn 48:1–11 | Hasmonea | `4Q6-1` |
| 4QGen-g (4Q7) | Gn 1:1–11,13–22; 2:6–7 | Hasmonea | `4Q7-1` |
| 4QGen-h (4Q8, 8a–c) | Gn 1:8–10; 2:17–18; 12:4–5 (paráfrasis) | Herodiana | `4Q8-1` a `4Q8-4` |
| 4QGen-j (4Q9), 4QGen-k (4Q10) | Gn 41–43; 45 / Gn 1:9,14–16,27–28; 2:1–3; 3:1–2 | Herodiana | `4Q9-1`, `4Q10-1` |
| 4QpaleoGen-Exod-l (4Q11) | Gn 50:26; Ex 1:1–5; 2:10,22–25; 3:1–4,17–21; 8:13–15,19–21; ... 20:1–2; ... | Hasmonea; paleohebrea | `4Q11-1` |
| 4QExod-b (4Q13) | Ex 1:1–6,[...]; 2:2–18; 3:13–4:8; 5:3–14 | Herodiana | `4Q13-1` |
| 4QExod-c (4Q14) | Ex 7:17–23; 7:26–8:1; 8:5–14,16–18,22; 9; 10; 11:9–10; 12:12–16,31–48; 13:18–14:13; 17:1–18:12 | Herodiana | `4Q14-1` |
| 4QpaleoExod-m (4Q22) | Ex 6:25–7:19,29–8:1,[5],12–22; 9:5–16,... hasta 37:9–16 (la lista abrevia) | Hasmonea; paleohebrea | `4Q22-1` |

No consulté Gn/Ex en otras cuevas (Masada, Murabba'at). Tabla abierta «manuscritos por pasaje»: solo hallé la lista de Wikipedia (CC BY-SA); ninguna oficial abierta confirmada.

**Condiciones de imágenes (Leon Levy Library)**: https://deadseascrolls.org.il/terms. «This material may not be reproduced, displayed, modified or distributed in any form, with the exception of single copies for private use» sin permiso escrito previo de la IAA; para licencias, contactar. La página **no trata enlazar ni incrustar**. Recomendación: **solo enlazar** (ficha de texto y botón «Ver imagen en la Leon Levy Library»); no copiar ni incrustar imágenes sin permiso.

### (c) Variantes notables
| Pasaje | Lo confirmado | Fuente |
|---|---|---|
| Éx 1:5 | El TM cuenta 70 personas; el manuscrito 4QExod-b registra 75 | Marc Zvi Brettler, TheTorah.com: https://www.thetorah.com/article/all-of-jacobs-descendants-numbered-seventy-five-the-opening-of-exodus-in-the-dead-sea-scrolls (leí solo el resumen; que la LXX diga 75 viene de tu enunciado, no lo verifiqué) |
| Gn 4:8, Éx 12:40 | **No verificado** | n/d |

## 5. Videos en español

| Video | URL e ID | Canal | ¿Incrustable? |
|---|---|---|---|
| Resumen del libro de Génesis: un panorama completo animado (parte 1) | https://www.youtube.com/watch?v=HQMKA6w5ZZM, `HQMKA6w5ZZM` | Proyecto Biblia (@ProyectoBibliaOficial) | oEmbed HTTP 200 |
| Resumen del libro de Éxodo: un panorama completo animado (parte 1) | https://www.youtube.com/watch?v=y9pED55wMM4, `y9pED55wMM4` | Proyecto Biblia | oEmbed HTTP 200 |
| El tema principal del libro de Génesis · parte 2 · Serie de la Torá (ep. 2) | https://www.youtube.com/watch?v=MLhplmsb_vk, `MLhplmsb_vk` | Proyecto Biblia | oEmbed HTTP 200 |

oEmbed 200 indica que la inserción no está bloqueada; no probé el reproductor insertado. Títulos en bibleproject.com/es (de la página de descargas): Génesis 1-11 (8:10), Génesis 12-50, Éxodo 1-18, Éxodo 19-40, Torá: Génesis parte 1 y 2, Éxodo parte 1 «Redención y esclavitud», parte 2 «Pacto en el monte Sinaí». Esas páginas ofrecen solo MP4 de mux.com, sin ID de YouTube.

**Condiciones (BibleProject)**: no pude abrir sus páginas de ayuda (403) ni https://bibleproject.com/terms/. Según buscador (no es cita leída): se permite incrustar vídeos de YouTube en webs sin fines de lucro; no editar ni quitar el audio; no subirlos a otros canales; en apps, incrustar o enlazar a su web o YouTube y no almacenar el contenido. Recomendación: usar el reproductor de YouTube, sin descargar los MP4, y confirmar los términos antes de publicar.

**Video o animación del recorrido del éxodo con mapa**: no hallé ninguno con licencia clara. Candidatos no verificados: https://the-map-as-history.com/bible-and-history/the-routes-of-exodus (mapa animado, licencia no leída) y https://theisraelbible.com/?p=463 (mapa estático). La ubicación del cruce del mar es discutida; la ruta de la app debe rotularse como interpretación con supuestos.

## Recomendación
- **Hebreo**: OSHB (`wlc/Gen.xml`, `Exod.xml`); aviso «Texto: WLC, dominio público; lemas y morfología: CC BY 4.0, Open Scriptures». Transliteración: calcularla y rotularla.
- **Numeración**: TVTMS (CC BY 4.0) para TM a RV/Swete; extraer solo Gn/Ex a un JSON propio y validarlo con los conteos medidos (Gn 31/32, Ex 7/8/21/22).
- **Griego**: Swete (dominio público) vía LXX-Swete-1930; decidir antes el asunto GPL-3.0. Alternativa: escaneos PD de archive.org (OCR, no verificado).
- **Audio**: sin fuente abierta confirmada. Opción realista: Web Speech API rotulada «Voz sintética moderna (no es pronunciación bíblica)», con detección por `getVoices()` y sin voz si no hay. Audio real: pedir permiso a Talking Bibles International (Mechon Mamre) o solicitar clave a Bible Brain y comprobar si tiene hebreo o griego.
- **Manuscritos**: fichas propias (sigla, pasaje, etiqueta de datación, institución) con enlace a la Leon Levy Library; **no incrustar imágenes** (IAA). Facsímiles: enlazar Leningrado (archive.org), Vaticano (DigiVatLib), Cambridge.
- **Variantes**: Éx 1:5 con cita a Brettler; Gn 4:8 y Éx 12:40 solo cuando se cite una edición (DJD, Tov u otra).
- **Video**: incrustar de YouTube los tres IDs verificados; faltan los IDs españoles de Génesis 12-50 y Éxodo 1-18 / 19-40.

## No verificado
- Audio hebreo o griego en Bible Brain y bible.is; condiciones completas de la API.
- Rutas y reglas de reproducción de los MP3 de Mechon Mamre.
- Voces concretas he-IL y el-GR en Windows, Android e iOS (solo buscador y guía Readium; sin prueba en dispositivo).
- Licencias de los facsímiles de Leningrado, Vaticano, Cambridge y British Library; enlaces vigentes del Alejandrino y el Sinaítico.
- Variantes Gn 4:8 y Éx 12:40; LXX = 75 en Éx 1:5; fechas numéricas de los rollos.
- IDs de YouTube españoles de Génesis 12-50, Éxodo 1-18, Éxodo 19-40, Torá Génesis 1 y Éxodo 1-2; términos de BibleProject (403).
- Fidelidad del CSV de Swete frente al impreso y transliteración completa en `03-...csv`.
- Columnas exactas del TVTMS.
- Conteos de la RV1909 (medí solo OSHB y Swete).
