# Cómo se armó este catálogo

Investigación para acompañar la lectura de Génesis, Éxodo y los Salmos. No modifica la aplicación. Cada ficha sale de una página abierta (museo, Wikimedia Commons, LibriVox o BibleProject). La licencia que se publica es la que devolvió la API de Commons (`LicenseShortName`), la ficha del Met (`isPublicDomain` / política Open Access CC0) o la página de términos, no una suposición.

Las 13 secciones de lectura del plan (6 de Génesis y 7 de Éxodo) tienen al menos tres imágenes locales.

## Totales

119 fichas en `catalogo.json`. 84 imágenes en `imagenes/` (JPG, lado máximo 1600 px, menos de 400 KB). El audio no se descargó: aunque LibriVox lo declara descargable, aquí solo queda el enlace. El texto reunido para ChatGPT es `PARA-CHATGPT.md`, en esta misma carpeta.

| Tipo | Fichas |
| --- | ---: |
| Arte | 70 |
| Arqueología | 15 |
| Mapas antiguos | 14 |
| Video | 10 |
| Audio | 6 |
| Reconstrucción | 4 |

Referencias (una ficha puede citar más de un libro): Génesis 48, Éxodo 48, Salmos 6.

| Uso | Fichas |
| --- | ---: |
| Descargable (84 imágenes locales y 5 audios de LibriVox, sin archivo de audio guardado) | 89 |
| Solo enlace | 24 |
| Incrustable (YouTube respondió al oEmbed con título y canal «Proyecto Biblia») | 6 |

| Licencia | Fichas |
| --- | ---: |
| Dominio público | 67 |
| Desconocida | 16 |
| Derechos reservados | 11 |
| CC BY-SA 4.0 | 18 |
| CC0 | 4 |
| CC BY-SA 3.0 | 2 |
| CC BY 4.0 | 1 |

No hay descargas con NC, ND o derechos reservados. Las fichas del British Museum quedan en licencia desconocida: su página general habla de CC BY-NC-SA para parte del contenido, pero la ficha del objeto no muestra esa licencia.

## Qué se comprobó otra vez

- Estela de Merneptah: Global Egyptian Museum, inventario JE 31408. La propia ficha dice que no hay prueba de que Merenptah sea el faraón del Éxodo. No hay imagen del museo con licencia abierta; sí una foto de Commons (CC BY-SA 4.0, Alyssa Bivins).
- Tablilla del diluvio (Gilgamesh XI), K.3375, y el mapa babilónico del mundo, 92687: fichas del British Museum, solo enlace.
- Cartas de Amarna del Met (Abi-milku de Tiro, 24.2.12, y Asur-ubalit de Asiria, 24.2.11) y facsímil de Beni Hasan (33.8.17, Norman de Garis Davies): Open Access, CC0, descargados. El de Rejmira (30.4.77, Nina de Garis Davies) no se descargó: el Met lo marca CC0, pero la autora murió en 1965 y en España el plazo de 70 años puede no haber vencido.
- Grabados de Doré, Schnorr, Tissot, Holman (1890) y *Figures de la Bible* (1728): dominio público según Commons.
- LibriVox: la página «Public Domain» y el tiempo total de cada audiolibro (Salmos en español 05:28:51).
- BibleProject: los términos permiten incrustar el video oficial, con crédito, sin descargarlo, reeditarlo ni cobrar por verlo. Seis videos quedaron incrustables porque oEmbed devolvió título y canal. Cuatro se quedaron en solo enlace porque la ficha no traía URL de YouTube para comprobar el flag.

## Huecos

- No existe una «estela de la Tabla de las Naciones». En su lugar: el mapa babilónico del mundo (British Museum) y el prisma Weld-Blundell de la lista real sumeria (Ashmolean, AN1923.444, imagen con derechos reservados).
- No hay lámina de dominio público o CC localizada, con el versículo en el pie, para estos capítulos: Génesis 5, 6, 10, 13, 14, 17, 20, 26, 30, 31, 35, 36, 42, 43 y 48; Éxodo 1, 11, 21–24, 26, 28, 29, 33, 34, 36 y 38. Varios son listas, leyes o instrucciones sin una escena que Doré o Tissot dibujaran en las series revisadas.
- No se halló una ficha de museo, con licencia abierta, de un ladrillo de adobe con paja identificado como de los trabajadores del relato. El ladrillo EA6020 del Rameseo lleva cartucho de Ramsés II y desgrasante vegetal; queda solo enlace.
- No se encontró una producción de «salmos actuados» con página oficial y licencia clara.
- No hay un video comprobado por cada salmo. Hay resumen del libro, «cómo leer los Salmos», el Salmo 8 (solo enlace) y el Salmo 148 (incrustable), más la lectura completa de LibriVox (Salmos 1–150).
- Las duraciones de los videos se dejaron vacías: figuraban en bibleproject.com, pero no se volvieron a cronometrar. Las de LibriVox sí se leyeron en la página del audiolibro.
- Mapas de la Library of Congress, la BNE, Gallica y David Rumsey: solo enlace. En la LoC la ficha dice que no conoce restricciones de copyright en Estados Unidos para mapas anteriores a 1922; no se pudo bajar el JPEG. En la BNE y en Rumsey la ficha consultada no cede una licencia abierta explícita.
- La datación del éxodo (siglo XV a. C., siglo XIII a. C., o relato no histórico en esos términos) está en `contexto-historico.md` como debate, no como fecha.

## Material de trabajo

`recursos/_trabajo/` guarda las búsquedas y los borradores. El catálogo que vale es `catalogo.json`.
