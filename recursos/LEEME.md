# Cómo se armó este catálogo

Investigación para acompañar la lectura. No modifica la aplicación. Cada ficha sale de una página abierta (museo, Wikimedia Commons, LibriVox, BibleProject o el canal oficial de Superbook). La licencia que se publica es la que devolvió la API de Commons (`LicenseShortName`), la ficha del museo o la página de términos, no una suposición. En noviembre de 2026 se añadieron Josué, Jueces y Rut.

Las 13 secciones de lectura del plan (6 de Génesis y 7 de Éxodo) tienen al menos tres imágenes locales.

## Totales

179 fichas en `catalogo.json`. 123 imágenes en `imagenes/` (JPG, lado máximo 1600 px, menos de 400 KB). El audio no se descargó. El texto reunido para ChatGPT es `PARA-CHATGPT.md` (no incluye las fichas añadidas después de Génesis, Éxodo y los Salmos).

| Tipo | Fichas |
| --- | ---: |
| Arte | 107 |
| Arqueología | 20 |
| Mapas antiguos | 16 |
| Video | 20 |
| Audio | 12 |
| Reconstrucción | 4 |

Referencias (una ficha puede citar más de un libro): Génesis 59, Éxodo 58, Levítico 4, Números 21, Deuteronomio 6, Josué 22, Jueces 14, Rut 8, Salmos 6.

| Uso | Fichas |
| --- | ---: |
| Descargable (123 imágenes locales y 11 audios de LibriVox, sin archivo de audio guardado) | 134 |
| Solo enlace | 30 |
| Incrustable (YouTube respondió al oEmbed con título y canal) | 15 |

| Licencia | Fichas |
| --- | ---: |
| Dominio público | 93 |
| CC BY-SA 4.0 | 34 |
| Derechos reservados | 23 |
| desconocida | 19 |
| CC0 | 7 |
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
- Josué, Jueces y Rut: no fiché Schnorr (esas búsquedas no devolvieron láminas). El mapa de Madaba tiene fotos en Commons con CC BY-SA 3.0, pero no comprobé qué fragmento muestra Jericó, Guilgal o Belén, y no lo fiché. No abrí una ficha de cerámica filistea: la crátera del British Museum 160152 es bícroma del Bronce tardío I, de Laquis, no filistea. Tel es-Sultan, et-Tell, Hazor, Silo, Gabaón, Tel Qasile y Belén quedaron sin ficha (la API de categorías de Commons respondió 429). Siquem (EA 252) y la estela de Merneptah ya estaban en el catálogo, con refs de Génesis y de Éxodo; no las dupliqué. No hay video por capítulo. En la guía de Superbook que abrí no apareció un episodio de Sansón. Los panoramas de Josué y de Jueces de Proyecto Biblia no se repiten: oEmbed confirmó que son `49ggVrdBN_Y` y `bCwaJz4L2nU`. La página en español de Rut no traía id de YouTube.

## Material de trabajo

`recursos/_trabajo/` guarda las búsquedas y los borradores. El catálogo que vale es `catalogo.json`.

## Cobertura por capítulo (Gn 1 a Dt 34)

Un video cuenta en un capítulo solo si sus referencias cubren ese capítulo y no más de ocho. Los panoramas de un libro entero (Levítico, Números, Deuteronomio, y los de Génesis y Éxodo ya fichados) no se reparten capítulo por capítulo: explican el libro, no el capítulo. Una imagen cuenta si el archivo está en imagenes/ y la ficha cita ese capítulo.

Proyecto Biblia no publica un video por capítulo de la Torá. Lo que hay, comprobado con oEmbed en el canal «Proyecto Biblia», son panoramas y dos episodios de la serie de la Torá. No se ficharon resubidas ni canales sin autor.

Capítulos de Levítico, Números y Deuteronomio con lámina local: Lv 10; Nm 12, 13, 16, 17, 20, 21, 22 y 24; Dt 34. El resto de esos libros no tenía, en Doré o en Tissot, una lámina cuyo pie citara el capítulo, o la escena era una lista o una ley sin grabado localizado.

No se pudo abrir una ficha de museo de la inscripción de Deir Alla (Balaam): solo apareció Wikipedia, y no se usó. La serpiente de cobre de Timna se menciona en un artículo académico como ofrenda de un santuario madianita, no como la serpiente de Moisés; no hay foto con licencia abierta, y no se fichó. El altar del monte Ebal sí se fichó como relación debatida, sin imagen.

| Capítulo | Videos de pasaje | Imágenes |
| --- | ---: | ---: |
| Gn 1 | 1 | 1 |
| Gn 2 | 0 | 1 |
| Gn 3 | 0 | 1 |
| Gn 4 | 0 | 1 |
| Gn 5 | 0 | 0 |
| Gn 6 | 0 | 0 |
| Gn 7 | 0 | 1 |
| Gn 8 | 0 | 1 |
| Gn 9 | 0 | 1 |
| Gn 10 | 0 | 2 |
| Gn 11 | 0 | 2 |
| Gn 12 | 0 | 2 |
| Gn 13 | 0 | 0 |
| Gn 14 | 0 | 0 |
| Gn 15 | 0 | 1 |
| Gn 16 | 0 | 1 |
| Gn 17 | 0 | 0 |
| Gn 18 | 0 | 1 |
| Gn 19 | 0 | 1 |
| Gn 20 | 0 | 0 |
| Gn 21 | 0 | 1 |
| Gn 22 | 0 | 1 |
| Gn 23 | 0 | 1 |
| Gn 24 | 0 | 1 |
| Gn 25 | 0 | 1 |
| Gn 26 | 0 | 0 |
| Gn 27 | 0 | 1 |
| Gn 28 | 0 | 1 |
| Gn 29 | 0 | 1 |
| Gn 30 | 0 | 0 |
| Gn 31 | 0 | 0 |
| Gn 32 | 0 | 1 |
| Gn 33 | 0 | 1 |
| Gn 34 | 0 | 1 |
| Gn 35 | 0 | 0 |
| Gn 36 | 0 | 0 |
| Gn 37 | 0 | 3 |
| Gn 38 | 0 | 1 |
| Gn 39 | 0 | 1 |
| Gn 40 | 0 | 1 |
| Gn 41 | 0 | 1 |
| Gn 42 | 0 | 0 |
| Gn 43 | 0 | 0 |
| Gn 44 | 0 | 1 |
| Gn 45 | 0 | 1 |
| Gn 46 | 0 | 1 |
| Gn 47 | 0 | 1 |
| Gn 48 | 0 | 0 |
| Gn 49 | 0 | 1 |
| Gn 50 | 0 | 1 |
| Ex 1 | 0 | 1 |
| Ex 2 | 0 | 1 |
| Ex 3 | 0 | 1 |
| Ex 4 | 0 | 1 |
| Ex 5 | 0 | 1 |
| Ex 6 | 0 | 1 |
| Ex 7 | 0 | 1 |
| Ex 8 | 0 | 1 |
| Ex 9 | 0 | 1 |
| Ex 10 | 0 | 1 |
| Ex 11 | 0 | 0 |
| Ex 12 | 0 | 2 |
| Ex 13 | 0 | 1 |
| Ex 14 | 0 | 2 |
| Ex 15 | 0 | 1 |
| Ex 16 | 0 | 1 |
| Ex 17 | 0 | 2 |
| Ex 18 | 0 | 1 |
| Ex 19 | 0 | 2 |
| Ex 20 | 0 | 2 |
| Ex 21 | 0 | 0 |
| Ex 22 | 0 | 0 |
| Ex 23 | 0 | 0 |
| Ex 24 | 0 | 0 |
| Ex 25 | 0 | 5 |
| Ex 26 | 0 | 2 |
| Ex 27 | 0 | 3 |
| Ex 28 | 0 | 0 |
| Ex 29 | 0 | 0 |
| Ex 30 | 0 | 1 |
| Ex 31 | 0 | 1 |
| Ex 32 | 0 | 4 |
| Ex 33 | 0 | 0 |
| Ex 34 | 0 | 0 |
| Ex 35 | 0 | 1 |
| Ex 36 | 0 | 1 |
| Ex 37 | 0 | 3 |
| Ex 38 | 0 | 1 |
| Ex 39 | 0 | 1 |
| Ex 40 | 0 | 3 |
| Lv 1 | 0 | 0 |
| Lv 2 | 0 | 0 |
| Lv 3 | 0 | 0 |
| Lv 4 | 0 | 0 |
| Lv 5 | 0 | 0 |
| Lv 6 | 0 | 0 |
| Lv 7 | 0 | 0 |
| Lv 8 | 0 | 0 |
| Lv 9 | 0 | 0 |
| Lv 10 | 0 | 1 |
| Lv 11 | 0 | 0 |
| Lv 12 | 0 | 0 |
| Lv 13 | 0 | 0 |
| Lv 14 | 0 | 0 |
| Lv 15 | 0 | 0 |
| Lv 16 | 0 | 0 |
| Lv 17 | 0 | 0 |
| Lv 18 | 0 | 0 |
| Lv 19 | 0 | 0 |
| Lv 20 | 0 | 0 |
| Lv 21 | 0 | 0 |
| Lv 22 | 0 | 0 |
| Lv 23 | 0 | 0 |
| Lv 24 | 0 | 0 |
| Lv 25 | 0 | 0 |
| Lv 26 | 0 | 0 |
| Lv 27 | 0 | 0 |
| Nm 1 | 0 | 0 |
| Nm 2 | 0 | 0 |
| Nm 3 | 0 | 0 |
| Nm 4 | 0 | 0 |
| Nm 5 | 0 | 0 |
| Nm 6 | 0 | 0 |
| Nm 7 | 0 | 0 |
| Nm 8 | 0 | 0 |
| Nm 9 | 0 | 0 |
| Nm 10 | 0 | 0 |
| Nm 11 | 0 | 0 |
| Nm 12 | 0 | 1 |
| Nm 13 | 0 | 2 |
| Nm 14 | 0 | 0 |
| Nm 15 | 0 | 0 |
| Nm 16 | 0 | 1 |
| Nm 17 | 0 | 1 |
| Nm 18 | 0 | 0 |
| Nm 19 | 0 | 0 |
| Nm 20 | 0 | 2 |
| Nm 21 | 0 | 2 |
| Nm 22 | 0 | 2 |
| Nm 23 | 0 | 0 |
| Nm 24 | 0 | 1 |
| Nm 25 | 0 | 0 |
| Nm 26 | 0 | 0 |
| Nm 27 | 0 | 0 |
| Nm 28 | 0 | 0 |
| Nm 29 | 0 | 0 |
| Nm 30 | 0 | 0 |
| Nm 31 | 0 | 0 |
| Nm 32 | 0 | 0 |
| Nm 33 | 0 | 0 |
| Nm 34 | 0 | 0 |
| Nm 35 | 0 | 0 |
| Nm 36 | 0 | 0 |
| Dt 1 | 0 | 0 |
| Dt 2 | 0 | 0 |
| Dt 3 | 0 | 0 |
| Dt 4 | 0 | 0 |
| Dt 5 | 0 | 0 |
| Dt 6 | 1 | 0 |
| Dt 7 | 0 | 0 |
| Dt 8 | 0 | 0 |
| Dt 9 | 0 | 0 |
| Dt 10 | 0 | 0 |
| Dt 11 | 0 | 0 |
| Dt 12 | 0 | 0 |
| Dt 13 | 0 | 0 |
| Dt 14 | 0 | 0 |
| Dt 15 | 0 | 0 |
| Dt 16 | 0 | 0 |
| Dt 17 | 0 | 0 |
| Dt 18 | 0 | 0 |
| Dt 19 | 0 | 0 |
| Dt 20 | 0 | 0 |
| Dt 21 | 0 | 0 |
| Dt 22 | 0 | 0 |
| Dt 23 | 0 | 0 |
| Dt 24 | 0 | 0 |
| Dt 25 | 0 | 0 |
| Dt 26 | 0 | 0 |
| Dt 27 | 0 | 0 |
| Dt 28 | 0 | 0 |
| Dt 29 | 0 | 0 |
| Dt 30 | 0 | 0 |
| Dt 31 | 0 | 0 |
| Dt 32 | 0 | 0 |
| Dt 33 | 0 | 0 |
| Dt 34 | 0 | 1 |

Sin video de pasaje: Gn 2, Gn 3, Gn 4, Gn 5, Gn 6, Gn 7, Gn 8, Gn 9, Gn 10, Gn 11, Gn 12, Gn 13, Gn 14, Gn 15, Gn 16, Gn 17, Gn 18, Gn 19, Gn 20, Gn 21, Gn 22, Gn 23, Gn 24, Gn 25, Gn 26, Gn 27, Gn 28, Gn 29, Gn 30, Gn 31, Gn 32, Gn 33, Gn 34, Gn 35, Gn 36, Gn 37, Gn 38, Gn 39, Gn 40, Gn 41, Gn 42, Gn 43, Gn 44, Gn 45, Gn 46, Gn 47, Gn 48, Gn 49, Gn 50, Ex 1, Ex 2, Ex 3, Ex 4, Ex 5, Ex 6, Ex 7, Ex 8, Ex 9, Ex 10, Ex 11, Ex 12, Ex 13, Ex 14, Ex 15, Ex 16, Ex 17, Ex 18, Ex 19, Ex 20, Ex 21, Ex 22, Ex 23, Ex 24, Ex 25, Ex 26, Ex 27, Ex 28, Ex 29, Ex 30, Ex 31, Ex 32, Ex 33, Ex 34, Ex 35, Ex 36, Ex 37, Ex 38, Ex 39, Ex 40, Lv 1, Lv 2, Lv 3, Lv 4, Lv 5, Lv 6, Lv 7, Lv 8, Lv 9, Lv 10, Lv 11, Lv 12, Lv 13, Lv 14, Lv 15, Lv 16, Lv 17, Lv 18, Lv 19, Lv 20, Lv 21, Lv 22, Lv 23, Lv 24, Lv 25, Lv 26, Lv 27, Nm 1, Nm 2, Nm 3, Nm 4, Nm 5, Nm 6, Nm 7, Nm 8, Nm 9, Nm 10, Nm 11, Nm 12, Nm 13, Nm 14, Nm 15, Nm 16, Nm 17, Nm 18, Nm 19, Nm 20, Nm 21, Nm 22, Nm 23, Nm 24, Nm 25, Nm 26, Nm 27, Nm 28, Nm 29, Nm 30, Nm 31, Nm 32, Nm 33, Nm 34, Nm 35, Nm 36, Dt 1, Dt 2, Dt 3, Dt 4, Dt 5, Dt 7, Dt 8, Dt 9, Dt 10, Dt 11, Dt 12, Dt 13, Dt 14, Dt 15, Dt 16, Dt 17, Dt 18, Dt 19, Dt 20, Dt 21, Dt 22, Dt 23, Dt 24, Dt 25, Dt 26, Dt 27, Dt 28, Dt 29, Dt 30, Dt 31, Dt 32, Dt 33, Dt 34

Sin imagen: Gn 5, Gn 6, Gn 13, Gn 14, Gn 17, Gn 20, Gn 26, Gn 30, Gn 31, Gn 35, Gn 36, Gn 42, Gn 43, Gn 48, Ex 11, Ex 21, Ex 22, Ex 23, Ex 24, Ex 28, Ex 29, Ex 33, Ex 34, Lv 1, Lv 2, Lv 3, Lv 4, Lv 5, Lv 6, Lv 7, Lv 8, Lv 9, Lv 11, Lv 12, Lv 13, Lv 14, Lv 15, Lv 16, Lv 17, Lv 18, Lv 19, Lv 20, Lv 21, Lv 22, Lv 23, Lv 24, Lv 25, Lv 26, Lv 27, Nm 1, Nm 2, Nm 3, Nm 4, Nm 5, Nm 6, Nm 7, Nm 8, Nm 9, Nm 10, Nm 11, Nm 14, Nm 15, Nm 18, Nm 19, Nm 23, Nm 25, Nm 26, Nm 27, Nm 28, Nm 29, Nm 30, Nm 31, Nm 32, Nm 33, Nm 34, Nm 35, Nm 36, Dt 1, Dt 2, Dt 3, Dt 4, Dt 5, Dt 6, Dt 7, Dt 8, Dt 9, Dt 10, Dt 11, Dt 12, Dt 13, Dt 14, Dt 15, Dt 16, Dt 17, Dt 18, Dt 19, Dt 20, Dt 21, Dt 22, Dt 23, Dt 24, Dt 25, Dt 26, Dt 27, Dt 28, Dt 29, Dt 30, Dt 31, Dt 32, Dt 33

## Cobertura por capítulo (Jos 1 a Rut 4)

Misma regla que arriba: una imagen cuenta si el archivo está en `imagenes/` y la ficha cita ese capítulo; un video cuenta si sus refs cubren el capítulo y no más de ocho. El mapa de Goeree ya fichado cita `Jos 1-12` entero, así que Jos 2, 9 y 12 tienen lámina local solo por ese mapa general, no por una escena del capítulo. Jos 3 y 4, además, tienen el mapa de MacCoun del paso del Jordán (1899). Los mapas de tribus de la Library of Congress, la BNE y otros siguen en solo enlace y no cuentan como lámina local.

Con escena de esta tanda (arte): Jos 1, 5, 6, 7, 8, 10 y 11; Jue 3, 4, 5, 7, 9, 11, 13, 14 y 16; Rut 1 y 2. Sin lámina local: Jos 13–24; Jue 1, 2, 6, 8, 10, 12, 15 y 17–21; Rut 3 y 4. Jue 6 y 8 tienen video de la historia de Gedeón y no tienen imagen. Rut 3 y 4 tienen video del libro o del episodio, y no tienen imagen.

| Capítulo | Videos de pasaje | Imágenes |
| --- | ---: | ---: |
| Jos 1 | 0 | 2 |
| Jos 2 | 1 | 1 |
| Jos 3 | 0 | 3 |
| Jos 4 | 0 | 2 |
| Jos 5 | 1 | 2 |
| Jos 6 | 1 | 3 |
| Jos 7 | 0 | 2 |
| Jos 8 | 0 | 2 |
| Jos 9 | 0 | 1 |
| Jos 10 | 0 | 4 |
| Jos 11 | 0 | 3 |
| Jos 12 | 0 | 1 |
| Jos 13 | 0 | 0 |
| Jos 14 | 0 | 0 |
| Jos 15 | 0 | 0 |
| Jos 16 | 0 | 0 |
| Jos 17 | 0 | 0 |
| Jos 18 | 0 | 0 |
| Jos 19 | 0 | 0 |
| Jos 20 | 0 | 0 |
| Jos 21 | 0 | 0 |
| Jos 22 | 0 | 0 |
| Jos 23 | 0 | 0 |
| Jos 24 | 0 | 0 |
| Jue 1 | 0 | 0 |
| Jue 2 | 0 | 0 |
| Jue 3 | 0 | 1 |
| Jue 4 | 0 | 3 |
| Jue 5 | 0 | 1 |
| Jue 6 | 1 | 0 |
| Jue 7 | 1 | 1 |
| Jue 8 | 1 | 0 |
| Jue 9 | 0 | 1 |
| Jue 10 | 0 | 0 |
| Jue 11 | 0 | 1 |
| Jue 12 | 0 | 0 |
| Jue 13 | 0 | 1 |
| Jue 14 | 0 | 1 |
| Jue 15 | 0 | 0 |
| Jue 16 | 0 | 4 |
| Jue 17 | 0 | 0 |
| Jue 18 | 0 | 0 |
| Jue 19 | 0 | 0 |
| Jue 20 | 0 | 0 |
| Jue 21 | 0 | 0 |
| Rut 1 | 3 | 2 |
| Rut 2 | 3 | 1 |
| Rut 3 | 3 | 0 |
| Rut 4 | 3 | 0 |

Sin video de pasaje: Jos 1, Jos 3, Jos 4, Jos 7, Jos 8, Jos 9, Jos 10, Jos 11, Jos 12, Jos 13, Jos 14, Jos 15, Jos 16, Jos 17, Jos 18, Jos 19, Jos 20, Jos 21, Jos 22, Jos 23, Jos 24, Jue 1, Jue 2, Jue 3, Jue 4, Jue 5, Jue 9, Jue 10, Jue 11, Jue 12, Jue 13, Jue 14, Jue 15, Jue 16, Jue 17, Jue 18, Jue 19, Jue 20, Jue 21

Sin imagen: Jos 13, Jos 14, Jos 15, Jos 16, Jos 17, Jos 18, Jos 19, Jos 20, Jos 21, Jos 22, Jos 23, Jos 24, Jue 1, Jue 2, Jue 6, Jue 8, Jue 10, Jue 12, Jue 15, Jue 17, Jue 18, Jue 19, Jue 20, Jue 21, Rut 3, Rut 4

