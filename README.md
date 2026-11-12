# Biblia · Compañero de lectura

Aplicación web instalable (celular y PC) que acompaña la lectura de la Biblia con árbol genealógico, edades y plan de lectura. Cada dato muestra su versículo y su fuente, y distingue lo que dice el texto de lo inferido o calculado.

**Alcance actual:** Génesis 1–50, Éxodo 1–40, Levítico 1–27, Números 1–36, Deuteronomio 1–34 y Josué 1–24: lectura por pasajes con acompañante, árbol, línea de tiempo (años desde Adán, con tradiciones y supuestos elegibles) y mapa de lugares.

## Usarla

Abrir https://roberto924.github.io/biblia/ y elegir «Instalar» o «Agregar a pantalla de inicio» en el navegador. Funciona sin conexión y se actualiza sola al publicar una versión nueva.

La lectura avanza **en orden**: lo que viene después del primer pasaje sin leer queda bloqueado en todas las vistas, y cada pasaje pide un tiempo mínimo antes de marcarlo como leído (sus palabras a 250 por minuto en perfil adulto, 150 en perfil de niño). Detalle en `datos/LEEME.md`.

## Actualizarla

1. Cambiar lo necesario (los datos se regeneran con `python herramientas/construir_datos.py`).
2. Subir el valor de `VERSION` en `sw.js`.
3. `git push`. GitHub Pages publica y ambas instalaciones avisan de la versión nueva.

## Fuentes

- Texto: Reina-Valera 1909, dominio público (eBible.org).
- Septuaginta: traducción de Brenton (1851), dominio público (eBible.org).
- Parentescos: BibleData, Brady Stephenson, CC BY 4.0, https://github.com/BradyStephenson/bible-data (modificados; ver `datos/LEEME.md`).
- Ubicación de lugares: OpenBible.info Bible Geocoding, CC BY 4.0, https://www.openbible.info/geo/.
- Mapa base: Natural Earth, dominio público.

El estudio previo del proyecto está en `ESTUDIO.md`.
