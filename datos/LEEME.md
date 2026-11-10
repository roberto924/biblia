# Datos de Génesis 1–11 (`genesis.js`)

Generado por `herramientas/construir_datos.py`; no editar a mano. Define `window.BIBLIA_DATOS` (capítulos, personas, relaciones, edades).

**Fuentes y licencias**
- Texto español: Reina-Valera 1909 (tradición masorética, TM), dominio público, vía eBible.org (`spaRV1909_vpl.zip`).
- Septuaginta (LXX): traducción inglesa de L. C. L. Brenton (1851), dominio público, vía eBible.org (`eng-Brenton_vpl.zip`). Se usa solo como testigo de las cifras de Gn 5 y 11.
- Parentescos y sexo: **BibleData** de Brady Stephenson, licencia **CC BY 4.0** (https://github.com/BradyStephenson/bible-data). Atribución exigida: «Datos de parentesco: BibleData, Brady Stephenson, CC BY 4.0, https://github.com/BradyStephenson/bible-data. Modificados: filtrados a Gn 1–11, normalizados a padre/madre/cónyuge y traducidos los nombres a la forma de la RV1909». La interfaz debe mostrar esta atribución.

**Regenerar**: `python herramientas/construir_datos.py` (descarga a `herramientas/cache/` si falta; `--sin-red` usa solo la caché). El script verifica que cada cita sea literal del versículo, convierte los numerales escritos («ciento y treinta», «two hundred and thirty») y exige que coincidan con el valor, comprueba las sumas, las relaciones y que cada nombre aparezca en su `primera_ref`; si algo falla sale con código ≠ 0.

**Cómo leer los datos**
- `pasajes`: 26 unidades de lectura editoriales que cubren los 299 versículos. `menciones`: offsets UTF-16 (`String.slice`) del nombre RV1909 en cada versículo; los homónimos se resuelven con BibleData-PersonVerse; no se marcan «mas» (conjunción), los usos como lugar ni los nombres que BibleData no sitúa en ese versículo.
- `certeza: "texto"` = la cifra está escrita en el versículo (`cita`). `"calculo"` = no está escrita (p. ej. totales de Gn 11, restantes de Taré); se obtiene sumando o restando.
- Relaciones: `explicito`/`inferido` según BibleData; las de Cainán (LXX) llevan `fuente: "brenton"`.
- Noé tiene además `tipo: "al_diluvio"` (Gn 7:6); su `restantes` son años tras el diluvio (Gn 9:28).
- `nombre` usa la grafía española actual (Adán, Set, Cam, Taré); `nombre_rv1909` guarda la forma literal del texto (Adam, Seth, Châm, Thare), que es la que se verifica. Es `null` en las personas que solo están en la LXX. Las relaciones confirmadas por el propio versículo llevan `fuente: "rv1909"`.
- `primera_ref` = la primera referencia de esa persona (en sus relaciones o edades) cuyo versículo contiene su nombre; no siempre es la primera mención absoluta.

**Limitaciones**
- Brenton traduce un texto griego concreto (básicamente el Códice Vaticano); otros manuscritos y ediciones de la LXX (p. ej. Rahlfs) dan cifras distintas en algunos casos (Matusalén, Lamec).
- El Pentateuco Samaritano NO está incluido: no hay fuente abierta verificada para sus cifras y no se inventan.
- BibleData trata como personas a pueblos de Gn 10 (Ludim, Jebuseo…); van marcados con una nota. Elisa en Gn 10:2 solo está en la LXX.
- Personas sin nombre (`sin_nombre: true`): esposas de Caín, Noé, Sem, Cam y Jafet, más 17 grupos «otros hijos e hijas». Sus relaciones llevan una `cita` literal. Las «hijas de los hombres» de Gn 6:1-4 no se incluyen porque no son genealogía.
- Se descartan relaciones no genealógicas de BibleData (hermano, homicida, Creador).
