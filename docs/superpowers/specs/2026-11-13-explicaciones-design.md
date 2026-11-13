# Explicaciones al tocar una palabra o un pasaje — diseño

Fecha: 2026-11-13 · Estado: aprobado en el chat por el usuario («sí a todas»), pendiente de la revisión del constructor.

## Para qué

Quien lee la RV1909 tropieza con tres cosas:
- palabras que ya no se usan («almete», «enjullo», «holgar»);
- medidas y costumbres que no conoce (codo, siclo, levirato, anatema);
- pasajes que chocan o confunden (la hija de Jefté, el anatema de Jericó, Endor).

El usuario quiere que se pueda **tocar la palabra o la frase** y ver una explicación breve, sin salir de la lectura. Debe valer para todo lo ya cargado (Gn–1 S) y quedar como **paso fijo** al añadir cada libro.

Rige el principio del proyecto (`CLAUDE.md`):
- toda explicación dice de dónde sale y con qué certeza;
- lo de fuera de la Biblia se marca «Fuente externa»;
- nada inventado.

## Decisiones del usuario (2026-11-13)

1. **Qué se explica.** Los cuatro tipos:
   - **palabra**: arcaísmos de la RV1909;
   - **medida**: medidas y monedas, con su equivalencia actual como **Cálculo**, con pasos y supuestos;
   - **concepto**: costumbres, instituciones, objetos y ritos;
   - **pasaje**: pasajes difíciles. Dice qué dice el texto (con cita) y qué posturas existen, cada una con su fuente, **sin decidir por el lector**.
2. **Cómo se ve.** Un punteado suave bajo la palabra, y en el lector un interruptor para ocultarlo y leer el texto limpio. Está encendido por defecto y se guarda por perfil.
3. **Perfil niño.** Cada explicación trae una versión corta y sencilla para niño. Un pasaje difícil cuya escena está oculta para el niño (`datos/contenido.js`) no se le muestra.
4. **Fuentes.** Las explicaciones las redactamos nosotros, siempre con cita y certeza. Fuentes válidas:
   - la propia Biblia cuando lo explica (Ex 30:13 dice cuánto vale el siclo);
   - diccionarios bíblicos de dominio público (Easton 1897, Smith 1863 y, si se encuentra, uno en español de dominio público);
   - el DLE de la RAE, solo como enlace;
   - obras de consulta con autor identificable para las posturas de los pasajes.

## Objetivos

- Tocar un término subrayado abre una tarjeta con:
  - la explicación (la de niño en ese perfil);
  - la insignia de certeza;
  - las fuentes con enlace;
  - en las medidas, el cálculo con sus pasos.
- Los pasajes difíciles se anuncian al principio del pasaje con un aviso plegable: «Pasaje difícil: qué dice el texto y qué posturas hay».
- Un **glosario** lista los términos que ya aparecieron en lo leído, respetando la lectura en orden.
- Cada libro nuevo suma sus términos y pasajes difíciles en el mismo flujo que el catálogo de juego.

## No-objetivos

- No es un comentario bíblico ni toma postura doctrinal.
- No hay preguntas tipo examen.
- No se explica cada palabra: solo lo que un lector actual probablemente no entienda.
- No se reproducen definiciones del DLE ni de diccionarios con derechos: se resume con palabras propias y se enlaza.

## Antiobjetivos (sería un fracaso aunque funcione)

- Una explicación sin fuente, o una postura presentada como la verdad.
- Un texto tan lleno de subrayados que cueste leer.
- Mostrar al niño lo que su perfil ya oculta.
- Desbloquear términos de pasajes aún no leídos (romper la lectura en orden).

## Datos

### Archivos fuente (editables por los agentes)

`herramientas/explicaciones/terminos.json`: glosario **global**, porque un término como «siclo» sirve en todos los libros.

```json
{
  "siclo": {
    "tipo": "medida",
    "lema": "siclo",
    "formas": ["siclo", "siclos"],
    "adulto": "Unidad de peso (y luego de valor) para metales…",
    "nino": "Un peso que se usaba para pagar con plata.",
    "certeza": "texto",
    "fuentes": [
      {"tipo": "biblia", "ref": "Ex 30:13", "cita": "el siclo es de veinte óbolos"},
      {"tipo": "diccionario", "obra": "Easton's Bible Dictionary (1897)", "entrada": "Shekel", "url": "…"}
    ],
    "calculo": {"resultado": "≈ 11,4 g", "pasos": ["…"], "supuestos": ["…"], "fuente": {"…": "…"}},
    "excluir": ["Gn 23:15"],
    "solo": null
  }
}
```

- `formas`: las formas exactas que se buscan en la RV1909, sin distinguir mayúsculas. Los acentos cuentan.
- `excluir` y `solo`: referencias para quitar o limitar las apariciones donde la forma tiene otro sentido. Por ejemplo, «codo» como parte del cuerpo.
- `certeza`, con las categorías del proyecto:
  - `texto`, cuando lo dice la Biblia;
  - `inferido`;
  - `calculo`;
  - `externa`, cuando sale de un diccionario u obra de fuera de la Biblia.

`herramientas/explicaciones/pasajes-<Libro>.json`: los pasajes difíciles de cada libro.

```json
{
  "jue-11-hija-jefte": {
    "refs": "Jue 11:29-40",
    "titulo": "El voto de Jefté",
    "dice": [{"ref": "Jue 11:31", "cita": "…"}],
    "posturas": [
      {"resumen": "…", "fuente": {"obra": "…", "autor": "…", "url": "…"}}
    ],
    "nino": "texto corto o null si no se le muestra",
    "certeza": "externa"
  }
}
```

### Generador

`python -I herramientas/explicaciones.py` → `datos/explicaciones.js` (`window.BIBLIA_EXPLICACIONES`):
- `terminos`, tal como están en el fuente;
- `ocurrencias` por versículo (clave de la app), `[{t, i, f}]`, con offsets UTF-16 como `menciones`;
- `pasajes`.

Comprobaciones (sale ≠ 0 si falla):
- ids únicos;
- cada término con al menos una fuente, `adulto` y `nino`;
- cada `cita` bíblica se encuentra literal en su versículo;
- cada `ref` es válida;
- `pasajes` tiene refs de libros cargados y al menos una postura con fuente;
- las ocurrencias no se solapan entre sí (gana la forma más larga).

Se informa sin fallar:
- términos con 0 ocurrencias;
- términos con muchas ocurrencias (posible ambigüedad que revisar).

Incluye `--autoprueba` con un fixture que debe fallar.

## Interfaz (`app.js`, `estilos.css`)

- **Marcado.** En modo Leer, el texto ya se parte en segmentos para personas y lugares; se añade un segmento `termino`.
  - Si una persona o un lugar se solapa con un término, gana la persona o el lugar.
  - *Criterio del orquestador:* se subraya solo la **primera aparición de cada término por pasaje**, para no llenar el texto.
  - El estilo es un punteado sutil. Debe distinguirse de los enlaces de persona y lugar y verse bien en tema claro y oscuro.
- **Tarjeta.** Usa el diálogo o panel que ya existe para personas y lugares, si encaja. Trae:
  - título;
  - explicación (`nino` en ese perfil);
  - insignia de certeza;
  - el cálculo con sus pasos si lo hay;
  - las fuentes con enlace;
  - «Fuente externa» cuando corresponda.
- **Interruptor.** «Explicaciones» en el lector, junto a los modos. Se guarda por perfil.
- **Pasaje difícil.** Un aviso plegable al inicio del pasaje. Para el niño se muestra `nino`, o nada si es `null` o si `contenido.js` oculta esos versículos.
- **Glosario.** Una lista de términos accesibles (con ocurrencias en pasajes ya desbloqueados), con búsqueda simple.
  - *Criterio del orquestador:* va dentro de la vista «Fuentes», para no añadir otra entrada al menú.
- **Lectura en orden.** Nada de un pasaje bloqueado aparece en el glosario ni en las búsquedas.
- **Pruebas** en `pruebas/probar.mjs` (núcleo puro):
  - segmentación con términos y personas solapados;
  - primera aparición por pasaje;
  - filtro del niño;
  - accesibilidad por lectura en orden.

## Contenido para Gn–1 S

- Lo escriben agentes que leen el texto completo por tandas: qué palabras, medidas y conceptos necesitan explicación, y qué pasajes son difíciles.
- **Un solo escritor por archivo:**
  - un agente escribe `terminos.json`;
  - los de pasajes escriben su propio `pasajes-<Libro>.json`.
  - Si se reparten los términos, cada agente escribe `terminos-<grupo>.json` y el generador los une y falla con ids duplicados.
- *Criterio del orquestador:* objetivo orientativo de 60–120 términos y 3–8 pasajes difíciles por libro largo. Es mejor pocos y buenos.

## Paso fijo por libro

Al ingresar un libro, después del agente de datos y en paralelo con originales y juego, un agente de explicaciones:
- añade los términos nuevos del libro (los existentes ya se aplican solos por sus `formas`);
- revisa las ocurrencias ambiguas;
- escribe `pasajes-<Libro>.json`.

Se documenta en `CLAUDE.md` («Por cada libro…») y en `datos/LEEME.md`.

## Respuestas a la revisión del constructor (criterios del orquestador)

1. **Verificación del contenido.** El generador comprueba las citas bíblicas, los ids y las refs. Además, cada tanda de contenido pasa por una **auditoría** de un agente distinto, como la de las láminas. El auditor revisa:
   - todos los pasajes difíciles: que cada postura diga lo que dice su fuente, abriéndola;
   - todas las medidas: los pasos del cálculo y el supuesto, con su fuente;
   - una muestra de al menos el 20 % de los demás términos, contra su fuente.

   Los veredictos van a `herramientas/explicaciones/auditoria.json` (OK, AJUSTAR o RECHAZAR) y el generador no publica lo RECHAZADO.
2. **Diccionario en español.** Si no aparece uno de dominio público, la explicación se redacta en español resumiendo a Easton o Smith (en inglés). La fuente lleva `idioma: "en"` y la certeza es `externa`. Si la Biblia lo dice, la certeza es `texto` y prima esa cita.
3. **Primera aparición por pasaje.** Se cuenta **después** de descartar las apariciones que pierden contra una persona o un lugar. La segmentación recibe las menciones y los términos juntos.
4. **Lectura en orden y citas.**
   - Una cita bíblica de una fuente que cae en un versículo aún no accesible se muestra sin texto, como «Ex 30:13 · se verá al llegar».
   - Los textos `adulto` y `nino` se redactan sin contar sucesos de pasajes posteriores al primer lugar donde aparece el término; el auditor lo revisa.
   - El glosario muestra solo los términos con alguna aparición accesible.
   - Un pasaje difícil se muestra solo si su rango es accesible.
5. **Niño y contenido.**
   - Los versículos que el perfil niño ya pliega no se subrayan, porque no se ven.
   - El texto `nino` de un término nunca describe violencia ni sexo explícito, y el auditor lo revisa.
   - No hace falta otro filtro de contenido para los términos.
6. **Interruptor.** Clave `biblia.p.<id>.explicaciones`. Sin valor guardado, cuenta como encendido, así que los perfiles ya creados no necesitan migración.
7. **Glosario.** Va como sección de la vista «Fuentes», que ya existe en el menú. El constructor confirma en `app.js` dónde encaja mejor.

## Queda a criterio del constructor

- La forma exacta del diálogo o panel, reutilizando lo existente.
- Los nombres internos y la estructura de las funciones.
- Cómo se ordena el glosario.
