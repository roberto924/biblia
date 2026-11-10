# Estudio inicial: compañero de lectura de la Biblia

Primera pasada, 10 de noviembre de 2026. Solo estudio: no hay código ni diseño.

## 1. La idea en una frase

Una aplicación en español que acompaña la lectura con genealogías, edades, mapas, línea de tiempo y planes de lectura, y que en cada dato dice de dónde sale y si es **texto bíblico** o **supuesto**.

**Hueco confirmado:** de los sitios revisados (viz.bible, STEP Bible, Blue Letter Bible, BibleGateway, OpenBible), ninguno marca dato por dato si es texto, cálculo o tradición. Solo OpenBible publica un nivel de confianza, y solo para lugares. Ninguno de los abiertos tiene interfaz en español comprobada. Logos, Bible Hub, Sefaria y las apps en español no se revisaron.

## 2. El eje del proyecto: nivel de certeza

Todo dato (persona, parentesco, edad, lugar, fecha, ruta) llevaría una de estas etiquetas, más su fuente:

| Nivel | Significado | Ejemplo |
|---|---|---|
| 1. Texto explícito | Lo dice un versículo, en una tradición textual concreta | «Adán vivió 130 años y engendró a Set» (Gn 5:3, texto masorético) |
| 2. Cálculo desde el texto | Suma o deducción a partir de cifras del texto | 1656 años de Adán al diluvio |
| 3. Ancla externa | Fecha fijada por arqueología o astronomía | Batalla de Qarqar, 853 a.C. |
| 4. Tradición | Fuente antigua no bíblica | Josefo identifica a Gómer con Galacia |
| 5. Discutido | Sin consenso | Fecha y ruta del Éxodo |

«Lo dice el texto» depende de qué texto: el masorético (hebreo), la Septuaginta (griego) y el Pentateuco Samaritano dan cifras distintas en Génesis 5 y 11. La app tendría que mostrar la tradición textual junto a cada cifra.

## 3. Fuentes de datos por área

Marca **V** = licencia o contenido comprobado por el orquestador hoy. Sin marca = lo informó un agente tras abrir la página.

### Texto bíblico en español

| Fuente | Licencia | Nota |
|---|---|---|
| Reina-Valera 1909 — https://ebible.org/find/details.php?id=spaRV1909 | Dominio público **V** | USFM, USFX, SQL. Castellano arcaico |
| Versión Biblia Libre — https://github.com/seven1m/open-bibles | CC BY-SA 4.0 **V** | Moderna |
| Biblia en Español Sencillo (mismo repositorio) | CC BY 4.0 **V** | Moderna, lenguaje simple |
| RVR1960, NVI, DHH, Biblia de Jerusalén | Con copyright (no verificado en fuente) | Requieren licencia |

### Lenguas originales y manuscritos

- Hebreo con morfología: https://github.com/openscriptures/morphhb (texto de dominio público, anotaciones CC BY 4.0).
- Hebreo y griego etiquetados, léxicos y nombres propios: https://github.com/STEPBible/STEPBible-Data (CC BY 4.0 según su README). Su tabla del Nuevo Testamento indica qué ediciones traen cada variante.
- Septuaginta: no se encontró una fuente abierta limpia. Pentateuco Samaritano y Vulgata: no investigados.
- **«Versión más antigua» de cada pasaje:** no existe un dataset abierto listo. Habría que construir la tabla a mano con citas (Rollos del Mar Muerto, códices Sinaítico, Vaticano, Alepo, Leningradense, papiros). Las imágenes del Sinaítico son de uso no comercial.

### Personas, parentescos y edades

| Fuente | Licencia | Para qué sirve |
|---|---|---|
| BibleData — https://github.com/BradyStephenson/bible-data | CC BY 4.0 **V** | 5.450 relaciones; cada una trae versículo y la marca `explicit` o `inferred` **V**. Es la base más cercana a lo que pides |
| Theographic — https://github.com/robertrouse/theographic-bible-metadata | CC BY-SA 4.0 **V** | 3.067 personas, 450 eventos, 1.298 lugares. Sus fechas siguen una sola cronología (Floyd Jones, derivada de Ussher) y los parentescos no citan versículo |

- Tabla comparativa de edades Adán–Abraham en las tres tradiciones: obtenida, pero de una sola fuente secundaria (Wikipedia, que cita a Skinner 1910). Hay celdas dudosas (Nacor y Taré en la Septuaginta). **No publicable** hasta cotejarla con ediciones críticas.
- Casos que deben marcarse como supuesto: Cainán de Gn 11 (solo en la Septuaginta y Lucas 3:36), genealogías de Jesús en Mateo y Lucas, generaciones omitidas, esposa de Caín, personas distintas con el mismo nombre (Enoc, Lamec).

### Lugares, pueblos y mapas

| Fuente | Licencia | Para qué sirve |
|---|---|---|
| OpenBible Geocoding — https://github.com/openbibleinfo/Bible-Geocoding-Data | CC BY 4.0 **V** (sin cambios desde 2021 **V**) | Cada lugar antiguo con sus identificaciones candidatas y una puntuación de confianza |
| Pleiades — https://pleiades.stoa.org/downloads | CC BY 3.0 | Lugares del mundo antiguo en general |
| Teselas CAWM (Universidad de Iowa) | CC BY 4.0 | Mapa base del mundo antiguo. No se comprobó que sigan en línea |

- Mapas antiguos de dominio público en Wikimedia Commons: Tabula Peutingeriana (facsímil de 1887), mapas medievales T-O, Hereford, categoría «Maps of the Holy Land» (353 archivos), Survey of Western Palestine (1872-1880). Mapa de Madaba (siglo VI): licencia de la imagen sin confirmar. David Rumsey: licencia no comercial, riesgo.
- «Adónde fue cada pueblo»: Génesis 10 da 70 pueblos en tres ramas; las identificaciones con regiones concretas son de Josefo o de la investigación moderna, no del texto. Rutas de Abraham, Éxodo, exilios y Pablo: **no investigadas** en esta pasada.

### Cronología

- La Biblia no tiene fechas absolutas: toda fecha a.C. es cálculo. Sistemas principales: Ussher (creación en 4004 a.C.), cómputo judío Seder Olam (3761 a.C.), Septuaginta (más larga), Thiele para los reyes, e historiografía crítica.
- Desde aproximadamente 850 a.C. hay anclas externas: Qarqar (853), tributo de Jehú (c. 841), eclipse asirio (763), Senaquerib, Crónicas Babilónicas. Antes, las cronologías difieren por siglos.
- Único dataset de eventos con fechas: Theographic, con una sola cronología. Habría que añadir las alternativas.
- La tabla comparativa de fechas por sistema quedó con muchas celdas sin confirmar; la mayoría de lo confirmado viene de Wikipedia.

### Lectura ordenada y otros apoyos

- Planes: canónico, cronológico, por fecha de composición, M'Cheyne, Horner, orden judío (Tanaj). No hay dataset abierto de planes; se generan a partir de listas de capítulos.
- Referencias cruzadas: https://a.openbible.info/data/cross-references.zip (unas 340.000, CC BY 4.0).
- Sin fuente abierta encontrada: diccionario bíblico en español, pesos y medidas, calendario y fiestas, género y autoría de cada libro, contexto de culturas vecinas. Habría que redactarlos con fuente propia.

## 4. Lo que quedó sin resolver

1. Tablas numéricas (edades por tradición, fechas por sistema): necesitan fuentes primarias, no Wikipedia.
2. Rutas y migraciones de pueblos: sin investigar.
3. Tabla del manuscrito más antiguo por libro: sin dataset; trabajo manual.
4. Septuaginta, Pentateuco Samaritano y Vulgata en formato abierto: sin fuente confirmada.
5. Apps comerciales (Logos, YouVersion en detalle) y apps en español: sin revisar.

## 5. Decisiones que te tocan

1. **Texto base en español:** Reina-Valera 1909 (libre, arcaica) o una moderna abierta (Biblia Libre, Español Sencillo).
2. **Compartir igual:** usar Theographic y Biblia Libre (CC BY-SA) obliga a publicar lo derivado con la misma licencia. La alternativa es limitarse a fuentes CC BY y dominio público.
3. **Tradición textual por defecto** cuando las cifras difieren: masorético con alternativas visibles, o las tres siempre.
4. **Fechas antes de ~1000 a.C.:** mostrar solo orden relativo y edades, o varias cronologías en paralelo.
5. **Canon:** protestante (66 libros), católico u otro como predeterminado.

## 6. Paso siguiente propuesto

Un piloto solo con **Génesis 1–11**: árbol de Adán a Abraham con edades en las tres tradiciones, cada dato con versículo y etiqueta de certeza. Es lo que motivó el proyecto, cabe en pocas fuentes ya comprobadas (BibleData + Reina-Valera 1909) y pone a prueba el eje de certeza antes de ampliar a mapas y línea de tiempo.
