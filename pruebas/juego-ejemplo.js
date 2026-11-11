// EJEMPLO del catálogo de juego (esquema de docs/superpowers/specs/2026-11-11-catalogo-juego-design.md) para probar
// la interfaz mientras no exista datos/juego.js. Refs y citas literales de la RV1909 de datos/biblia.js.
// Se carga con ?ejemplo o ?juego-ejemplo, y en pruebas/probar.mjs. No es el catálogo real.
window.BIBLIA_JUEGO = {
  generado: '2026-11-11 (ejemplo)',
  libros: ['Gn', 'Ex'],
  genealogias: [
    { id: 'gn-5', inicio: 'Gn 5:1', fin: 'Gn 5:32', titulo: 'De Adán a Noé', cita: 'ESTE es el libro de las generaciones de Adam' },
    { id: 'gn-25-ismael', inicio: 'Gn 25:12', fin: 'Gn 25:18', titulo: 'Descendientes de Ismael', cita: 'estas son las generaciones de Ismael' }
  ],
  historias: [
    { id: 'creacion-eden', titulo: 'Creación y Edén', inicio: 'Gn 1:1', fin: 'Gn 3:24', principales: ['Adam_1', 'Eve_1'] },
    { id: 'noe', titulo: 'Noé', inicio: 'Gn 6:1', fin: 'Gn 9:29', principales: ['Noah_1'] },
    { id: 'abraham', titulo: 'Abraham', inicio: 'Gn 11:27', fin: 'Gn 25:11', principales: ['Abram_1', 'Sarai_1'] }
  ],
  personajes: {
    Adam_1: {
      apariciones: [{ inicio: 'Gn 2:7', fin: 'Gn 3:24' }, { inicio: 'Gn 4:1', fin: 'Gn 4:1' }],
      versiculos: 44, nivel: 6, npc: false,
      listo: { historia: 'creacion-eden', ref: 'Gn 3:24', capitulo: 'Gn 3' },
      menciones_posteriores: [{ ref: 'Gn 5:1' }],
      resumen: 'Primer hombre, formado del polvo y puesto en el huerto del Edén.',
      datos: [
        { texto: 'Dios lo formó del polvo de la tierra', certeza: 'texto', ref: 'Gn 2:7', cita: 'Formó, pues, Jehová Dios al hombre del polvo de la tierra' },
        { texto: 'Fue puesto en el huerto para labrarlo y guardarlo', certeza: 'texto', ref: 'Gn 2:15', cita: 'le puso en el huerto de Edén, para que lo labrara y lo guardase' },
        { texto: 'Puso nombre a los animales', certeza: 'texto', ref: 'Gn 2:20', cita: 'Y puso Adam nombres á toda bestia' },
        { texto: '«El hombre» de Gn 2:7–19 es Adán, aunque el texto aún no lo nombre', certeza: 'inferido', ref: 'Gn 2:20', cita: 'mas para Adam no halló ayuda' },
        { texto: 'Vivió 930 años', certeza: 'texto', ref: 'Gn 5:5', cita: 'novecientos y treinta años' }
      ],
      externo: [{ texto: 'Figura central de las tradiciones judía, cristiana e islámica sobre el origen humano.', fuente: 'Wikipedia (secundaria): «Adán»', url: 'https://es.wikipedia.org/wiki/Ad%C3%A1n' }]
    },
    Noah_1: {
      apariciones: [{ inicio: 'Gn 6:8', fin: 'Gn 9:29' }],
      versiculos: 98, nivel: 7, npc: false,
      listo: { historia: 'noe', ref: 'Gn 9:29', capitulo: 'Gn 9' },
      resumen: 'Varón justo que construye el arca por mandato de Dios.',
      datos: [
        { texto: 'Varón justo que caminó con Dios', certeza: 'texto', ref: 'Gn 6:9', cita: 'Noé, varón justo, perfecto fué en sus generaciones' },
        { texto: 'Hizo todo lo que Dios le mandó', certeza: 'texto', ref: 'Gn 6:22', cita: 'hizo conforme á todo lo que Dios le mandó' },
        { texto: 'Plantó una viña después del diluvio', certeza: 'texto', ref: 'Gn 9:20', cita: 'plantó una viña' },
        { texto: 'Vivió 950 años', certeza: 'texto', ref: 'Gn 9:29', cita: 'novecientos y cincuenta años' }
      ],
      externo: []
    },
    Abram_1: {
      apariciones: [{ inicio: 'Gn 11:27', fin: 'Gn 25:10' }],
      versiculos: 600, nivel: 10, npc: false,
      listo: { historia: 'abraham', ref: 'Gn 25:8', capitulo: 'Gn 25' },
      menciones_posteriores: [{ ref: 'Ex 3:6' }],
      resumen: 'Llamado por Dios a salir de su tierra; padre de Isaac.',
      datos: [
        { texto: 'Vivió 175 años', certeza: 'texto', ref: 'Gn 25:7', cita: 'ciento setenta y cinco años' },
        { texto: 'Murió en buena vejez', certeza: 'texto', ref: 'Gn 25:8', cita: 'murió Abraham en buena vejez' }
      ],
      externo: [{ texto: 'Considerado patriarca común del judaísmo, el cristianismo y el islam.', fuente: 'Wikipedia (secundaria): «Abraham»', url: 'https://es.wikipedia.org/wiki/Abraham' }]
    },
    Mahalalel_1: {
      apariciones: [], versiculos: 0, nivel: 0, npc: true,
      resumen: 'Descendiente de Set, nombrado solo en la genealogía de Génesis 5.',
      datos: [{ texto: 'Vivió 895 años', certeza: 'texto', ref: 'Gn 5:17', cita: 'ochocientos noventa y cinco años' }],
      externo: []
    }
  },
  objetos: {
    'arca-noe': {
      nombre: 'Arca de Noé', tipo: 'embarcación',
      apariciones: [{ inicio: 'Gn 6:14', fin: 'Gn 8:19' }],
      personas: ['Noah_1'], lugares: ['ararat'],
      resumen: 'Gran embarcación de madera que Noé construye para salvar a su familia y a los animales del diluvio.',
      datos: [
        { texto: 'De madera de gofer, con aposentos y embetunada con brea', certeza: 'texto', ref: 'Gn 6:14', cita: 'Hazte un arca de madera de Gopher' },
        { texto: '300 codos de largo, 50 de ancho y 30 de alto', certeza: 'texto', ref: 'Gn 6:15', cita: 'de trescientos codos la longitud del arca' },
        { texto: 'Reposó sobre los montes de Armenia (Ararat)', certeza: 'texto', ref: 'Gn 8:4', cita: 'reposó el arca en el mes séptimo' }
      ],
      externo: [{ texto: 'Relatos de un diluvio con una gran barca aparecen también en textos mesopotámicos, como la Epopeya de Gilgamesh.', fuente: 'Wikipedia (secundaria): «Arca de Noé»', url: 'https://es.wikipedia.org/wiki/Arca_de_No%C3%A9' }]
    },
    'arca-pacto': {
      nombre: 'Arca del pacto', tipo: 'mueble del tabernáculo', tabernaculo: 'arca',
      apariciones: [{ inicio: 'Ex 25:10', fin: 'Ex 25:22' }],
      personas: [], lugares: [],
      resumen: 'Cofre de madera de acacia cubierto de oro, con el propiciatorio y dos querubines.',
      datos: [
        { texto: 'Dos codos y medio de largo, codo y medio de ancho y de alto', certeza: 'texto', ref: 'Ex 25:10', cita: 'cuya longitud será de dos codos y medio' }
      ],
      externo: []
    }
  },
  escenarios: {
    eden: {
      nombre: 'Huerto del Edén', lugar: 'eden',
      apariciones: [{ inicio: 'Gn 2:8', fin: 'Gn 3:24' }],
      personas: ['Adam_1', 'Eve_1'], objetos: [],
      resumen: 'Huerto que Dios planta al oriente, en Edén, donde pone al hombre.',
      datos: [
        { texto: 'Dios plantó un huerto en Edén, al oriente', certeza: 'texto', ref: 'Gn 2:8', cita: 'plantado un huerto en Edén al oriente' },
        { texto: 'Querubines y una espada encendida guardan el camino al árbol de la vida', certeza: 'texto', ref: 'Gn 3:24', cita: 'puso al oriente del huerto de Edén querubines' }
      ],
      externo: []
    }
  }
};
