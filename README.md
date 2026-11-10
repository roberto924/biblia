# Biblia · Compañero de lectura

Aplicación web instalable (celular y PC) que acompaña la lectura de la Biblia con árbol genealógico, edades y plan de lectura. Cada dato muestra su versículo y su fuente, y distingue lo que dice el texto de lo inferido o calculado.

**Piloto actual:** Génesis 1–11.

## Usarla

Abrir https://roberto924.github.io/biblia/ y elegir «Instalar» o «Agregar a pantalla de inicio» en el navegador. Funciona sin conexión y se actualiza sola al publicar una versión nueva.

## Actualizarla

1. Cambiar lo necesario (los datos se regeneran con `python herramientas/construir_datos.py`).
2. Subir el valor de `VERSION` en `sw.js`.
3. `git push`. GitHub Pages publica y ambas instalaciones avisan de la versión nueva.

## Fuentes

- Texto: Reina-Valera 1909, dominio público (eBible.org).
- Septuaginta: traducción de Brenton (1851), dominio público (eBible.org).
- Parentescos: BibleData, Brady Stephenson, CC BY 4.0, https://github.com/BradyStephenson/bible-data (modificados; ver `datos/LEEME.md`).

El estudio previo del proyecto está en `ESTUDIO.md`.
