# Encargo para Cursor · Imágenes e información para la colección del juego (Génesis y Éxodo)

Responde y escribe en español. Proyecto: PWA «Biblia · Compañero de lectura». Lee primero `CLAUDE.md` (principio de certeza) y `recursos/LEEME.md` (cómo hiciste el catálogo anterior).

## Contexto
La app tendrá una **colección de personajes, objetos y escenarios** (lo están catalogando ahora otros agentes). Cada ficha mostrará todo lo que se sabe. Tú buscas **imágenes e información histórica** para esas fichas y **referencias de época** para las futuras láminas de personajes.

## NO TOCAR (otros agentes trabajan ahí ahora)
`app.js`, `estilos.css`, `index.html`, `sw.js`, `datos/`, `herramientas/`, `docs/`, `pruebas/`, `CLAUDE.md`. Escribe **solo** en `recursos/juego/` y en `recursos/catalogo.json` (solo para la corrección del punto 4).

## 1. Objetos y escenarios — `recursos/juego/catalogo-juego.json`
Mismo esquema que `recursos/catalogo.json` (id, tipo, titulo, descripcion, refs, autor, fecha_obra, institucion, url_fuente, url_archivo, archivo_local, licencia, atribucion, uso, certeza, nota_certeza) **más**:
- `"para": {"clase": "objeto"|"escenario", "nombre": "Arca de Noé"}`
- `"sensible": "no"|"medio"|"alto"` (alto = violencia o sangre explícita; el perfil niño lo oculta).

Imágenes descargables en `recursos/juego/imagenes/`.

Lista (usa estos nombres en `para.nombre`; añade otros que encuentres en el texto):
- **Génesis — objetos:** árbol de la vida, árbol de la ciencia del bien y del mal, túnicas de pieles, arca de Noé, arco iris, ladrillos y betún de Babel, cuchillo y leña del sacrificio de Isaac (Gn 22), pozos de Abraham e Isaac, escalera de Jacob, piedra de Betel (columna), terafines de Labán, túnica de José, copa de José, carros de Egipto.
- **Génesis — escenarios:** huerto del Edén, torre de Babel, Ur de los caldeos, Harán, Betel, Sodoma y Gomorra, monte Moriah, cueva de Macpela, Peniel (vado de Jaboc), cisterna de Dotán, casa de Potifar, cárcel de José, corte del faraón, Gosén.
- **Éxodo — objetos:** cesta de juncos, vara de Moisés, ladrillos con paja, sangre en los dinteles, panes sin levadura, columna de nube y de fuego, maná y el gomer, tablas de la ley, becerro de oro, pectoral y efod del sumo sacerdote, Urim y Tumim, cuernos del altar.
- **Éxodo — escenarios:** el Nilo y el palacio del faraón, pozo de Madián, zarza ardiente en Horeb, cada una de las 10 plagas, Ramesés y Sucot, mar Rojo, Mara y Elim, Refidim (agua de la roca, batalla con Amalec), monte Sinaí, campamento al pie del Sinaí.

Por cada uno busca, en este orden de preferencia:
1. **Registro histórico** relacionado (objeto o escena de museo de esa época que muestra cómo era algo así): p. ej. cestas de juncos egipcias, ladrilleros en la tumba de Rekhmire, zigurat de Ur para Babel, carros egipcios del Imperio Nuevo, cayados egipcios, becerros/toros de culto cananeos, pectorales egipcios. La `nota_certeza` dice **qué es y qué no es**: «objeto comparable de la época, no el objeto del relato».
2. **Arte** con fecha (Doré, Tissot, maestros antiguos), relacionado con **ese** pasaje concreto.
3. **Reconstrucción moderna** con sus supuestos y su autor.
Nada generado por IA en este encargo. Abre cada URL, verifica licencia y que la imagen corresponde. No dupliques imágenes que ya estén en `recursos/catalogo.json` (compara url_fuente): si ya existe, solo nómbrala en el informe.

## 2. Información histórica — `recursos/juego/contexto-objetos-escenarios.md`
Por cada objeto y escenario: 2–5 viñetas de lo que se sabe **fuera de la Biblia** (arqueología, historia, identificaciones propuestas y debatidas), cada viñeta con fuente y URL (museos, universidades, enciclopedias académicas; Wikipedia solo como secundaria, diciéndolo). Distingue hecho establecido / hipótesis / tradición. Nada sin fuente.

## 3. Referencias de época para láminas de personajes — `recursos/juego/referencias-laminas.md`
Las láminas futuras serán «Ilustración moderna» lo más cercanas posible a la realidad. Para cada época, qué muestran los registros sobre **ropa, peinado, barba, calzado, armas, herramientas, colores y tipos físicos**, con la imagen de museo y su fuente:
- Mesopotamia del Bronce (Ur, Mari) → Abraham joven, Taré.
- Semitas en Egipto, Bronce Medio (mural de Beni Hasan, tumba de Jnumhotep II, ~1890 a. C.) → patriarcas, Jacob y sus hijos.
- Corte egipcia del Imperio Medio/Nuevo → José en Egipto, faraón, Potifar, Asenat.
- Imperio Nuevo y pueblos del desierto (shasu) → Moisés, Aarón, Miriam, Jetro, Madián.
Y para los personajes principales (Adán, Eva, Noé, Abraham, Sara, Isaac, Rebeca, Jacob, Raquel, José, Moisés, Aarón, Miriam): una ficha con edad en la escena elegida (con cita bíblica si el texto la da), qué referencias usar y un **prompt borrador** para generar la ilustración, sin generarla. Para Adán, Eva y Noé (sin registros de época) dilo explícitamente y propone un criterio.

## 4. Corrección pendiente
En `recursos/catalogo.json`, las obras de James Tissot tienen `fecha_obra` mal (p. ej. «2018-12-11», que es la fecha de subida). Pon el año de la obra (Tissot pintó la serie del Antiguo Testamento hacia 1896–1902; usa la fecha que dé el museo, The Jewish Museum de Nueva York, si la encuentras por obra). Lista en el informe cada id corregido.

## 5. Informe — `recursos/juego/LEEME.md`
Cifras: imágenes por clase y tipo (registro/arte/reconstrucción), objetos y escenarios **sin** imagen, URLs que no pudiste verificar, licencias dudosas, ids de Tissot corregidos. Al terminar, avísame con un resumen de 10 líneas.
