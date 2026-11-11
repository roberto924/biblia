window.BIBLIA_TABERNACULO = {
 "generado": "2026-11-11",
 "unidad": "codo",
 "codos": [
  {
   "id": "comun",
   "nombre": "codo común",
   "cm": 44.5,
   "defecto": true,
   "fuente": "Fuente externa: «Cubit», Insight on the Scriptures (Watch Tower, diccionario bíblico)",
   "url": "https://www.jw.org/en/library/books/Insight-on-the-Scriptures/Cubit/",
   "cita_fuente": "commonly used a cubit of about 44.5 cm (17.5 in.)",
   "nota": "Valor aproximado; el texto bíblico no define el codo en centímetros. La misma obra da ~51,8 cm para el codo largo de Ezequiel 40:5 (codo + un palmo). Consultada el 2026-11-11."
  },
  {
   "id": "real",
   "nombre": "codo real (largo)",
   "cm": 52.5,
   "fuente": "Fuente externa: Wikipedia (inglés), «Biblical and Talmudic units of measurement»",
   "url": "https://en.wikipedia.org/wiki/Biblical_and_Talmudic_units_of_measurement",
   "cita_fuente": "the larger Egyptian cubit was between 52.5 and 52.8 cm",
   "nota": "52,5 cm es el extremo inferior del codo egipcio largo (real); la misma página dice que no se sabe si el codo bíblico estándar era de 49,5 o de 52,5 cm. Fuente secundaria. Consultada el 2026-11-11."
  }
 ],
 "orientacion": {
  "texto": "La entrada del atrio (y del tabernáculo) mira al oriente; el fondo del tabernáculo, al occidente. El lado largo sur es «el mediodía» (austro) y el norte «el aquilón».",
  "ref": "Ex 27:13",
  "cita": "por la parte de levante, al oriente",
  "otras": [
   {
    "texto": "Fondo del tabernáculo al occidente",
    "ref": "Ex 26:22",
    "cita": "al occidente, harás seis tablas"
   },
   {
    "texto": "Lado sur",
    "ref": "Ex 26:18",
    "cita": "veinte tablas al lado del mediodía, al austro"
   },
   {
    "texto": "Lado norte",
    "ref": "Ex 26:20",
    "cita": "á la parte del aquilón, veinte tablas"
   }
  ],
  "plano": "Coordenadas en codos; origen en la esquina suroeste del atrio; x hacia el oriente, y hacia el norte. rot en grados: 0 = eje largo de la pieza de oeste a este; 90 = de sur a norte."
 },
 "zonas": [
  {
   "id": "atrio",
   "nombre": "Atrio",
   "largo": {
    "codos": 100,
    "ref": "Ex 27:18",
    "cita": "La longitud del atrio será de cien codos",
    "certeza": "texto"
   },
   "ancho": {
    "codos": 50,
    "ref": "Ex 27:18",
    "cita": "la anchura cincuenta por un lado y cincuenta por el otro",
    "certeza": "texto"
   },
   "alto": {
    "codos": 5,
    "ref": "Ex 27:18",
    "cita": "la altura de cinco codos",
    "certeza": "texto"
   },
   "plano": {
    "x0": 0,
    "y0": 0,
    "x1": 100,
    "y1": 50,
    "certeza": "texto",
    "nota": "Medidas del texto; el origen es una convención del plano."
   },
   "nota": "Largo de oeste a este (lados sur y norte de 100 codos, Ex 27:9-11)."
  },
  {
   "id": "santo",
   "nombre": "Lugar santo",
   "largo": {
    "codos": 20,
    "ref": "Ex 26:33",
    "cita": "pondrás el velo debajo de los corchetes",
    "certeza": "inferido",
    "calculo": "largo-santo"
   },
   "ancho": {
    "codos": 10,
    "ref": null,
    "cita": null,
    "certeza": "tradicion",
    "calculo": "ancho-interior",
    "fuente": "Rashi (Fuente externa, tradición)"
   },
   "alto": {
    "codos": 10,
    "ref": "Ex 26:16",
    "cita": "La longitud de cada tabla será de diez codos",
    "certeza": "inferido",
    "calculo": "alto-tabernaculo"
   },
   "plano": {
    "x0": 30,
    "y0": 20,
    "x1": 50,
    "y1": 30,
    "certeza": "inferido",
    "nota": "El texto no dice dónde está el tabernáculo dentro del atrio. Supuesto de dibujo: centrado de norte a sur y con el fondo a 20 codos del lado occidental."
   },
   "nota": "El texto no da sus dimensiones: 20 codos de largo es un cálculo con un supuesto; 10 de ancho, tradición (Rashi)."
  },
  {
   "id": "santisimo",
   "nombre": "Lugar santísimo",
   "largo": {
    "codos": 10,
    "ref": null,
    "cita": null,
    "certeza": "inferido",
    "calculo": "largo-santisimo"
   },
   "ancho": {
    "codos": 10,
    "ref": null,
    "cita": null,
    "certeza": "tradicion",
    "calculo": "ancho-interior",
    "fuente": "Rashi (Fuente externa, tradición)"
   },
   "alto": {
    "codos": 10,
    "ref": "Ex 26:16",
    "cita": "La longitud de cada tabla será de diez codos",
    "certeza": "inferido",
    "calculo": "alto-tabernaculo"
   },
   "plano": {
    "x0": 20,
    "y0": 20,
    "x1": 30,
    "y1": 30,
    "certeza": "inferido",
    "nota": "Mismo supuesto de dibujo que el lugar santo."
   },
   "nota": "Separado del lugar santo por el velo (Ex 26:33). Un cubo de 10 codos es la lectura tradicional (Rashi a Ex 26:32), no está escrito."
  }
 ],
 "piezas": [
  {
   "id": "arca",
   "nombre": "Arca del testimonio",
   "grupo": "mobiliario",
   "instruccion": "Ex 25:10-16",
   "construccion": "Ex 37:1-5",
   "medidas": {
    "largo": {
     "codos": 2.5,
     "ref": "Ex 25:10",
     "cita": "cuya longitud será de dos codos y medio",
     "certeza": "texto"
    },
    "ancho": {
     "codos": 1.5,
     "ref": "Ex 25:10",
     "cita": "su anchura de codo y medio",
     "certeza": "texto"
    },
    "alto": {
     "codos": 1.5,
     "ref": "Ex 25:10",
     "cita": "su altura de codo y medio",
     "certeza": "texto"
    }
   },
   "materiales": [
    {
     "nombre": "madera de Sittim",
     "ref": "Ex 25:10",
     "cita": "un arca de madera de Sittim"
    },
    {
     "nombre": "oro puro (por dentro y por fuera)",
     "ref": "Ex 25:11",
     "cita": "la cubrirás de oro puro"
    },
    {
     "nombre": "cuatro anillos de oro",
     "ref": "Ex 25:12",
     "cita": "cuatro anillos de oro"
    },
    {
     "nombre": "varas de Sittim cubiertas de oro",
     "ref": "Ex 25:13",
     "cita": "harás unas varas de madera de Sittim"
    }
   ],
   "zona": {
    "id": "santisimo",
    "certeza": "texto",
    "ref": "Ex 26:33",
    "cita": "meterás allí, del velo adentro, el arca del testimonio",
    "nota": null
   },
   "plano": {
    "x": 25,
    "y": 25,
    "certeza": "inferido",
    "nota": "Centro del santísimo. Coordenada de dibujo dentro de su zona (supuesto).",
    "relacion": [
     {
      "texto": "detrás del velo",
      "ref": "Ex 26:33",
      "cita": "del velo adentro"
     }
    ]
   },
   "funcion": {
    "texto": "Guardar el testimonio",
    "ref": "Ex 25:16",
    "cita": "pondrás en el arca el testimonio"
   },
   "nota": "Las varas no se quitan del arca (Ex 25:15)."
  },
  {
   "id": "propiciatorio",
   "nombre": "Propiciatorio (cubierta) con dos querubines",
   "grupo": "mobiliario",
   "instruccion": "Ex 25:17-22",
   "construccion": "Ex 37:6-9",
   "medidas": {
    "largo": {
     "codos": 2.5,
     "ref": "Ex 25:17",
     "cita": "cuya longitud [será] de dos codos y medio",
     "certeza": "texto"
    },
    "ancho": {
     "codos": 1.5,
     "ref": "Ex 25:17",
     "cita": "su anchura de codo y medio",
     "certeza": "texto"
    }
   },
   "cantidad": {
    "valor": 1,
    "ref": "Ex 25:17",
    "cita": "una cubierta de oro fino",
    "certeza": "texto"
   },
   "materiales": [
    {
     "nombre": "oro fino",
     "ref": "Ex 25:17",
     "cita": "una cubierta de oro fino"
    },
    {
     "nombre": "dos querubines de oro labrados a martillo",
     "ref": "Ex 25:18",
     "cita": "dos querubines de oro, labrados á martillo"
    }
   ],
   "detalles": [
    {
     "texto": "Querubines en los dos extremos, alas extendidas, caras uno frente al otro",
     "ref": "Ex 25:20",
     "cita": "sus caras la una enfrente de la otra"
    }
   ],
   "zona": {
    "id": "santisimo",
    "certeza": "texto",
    "ref": "Ex 26:34",
    "cita": "pondrás la cubierta sobre el arca del testimonio en el lugar santísimo",
    "nota": null
   },
   "plano": {
    "x": 25,
    "y": 25,
    "certeza": "inferido",
    "nota": "Encima del arca (Ex 25:21). Coordenada de dibujo dentro de su zona (supuesto).",
    "relacion": [
     {
      "texto": "encima del arca",
      "ref": "Ex 25:21",
      "cita": "pondrás la cubierta encima del arca"
     }
    ]
   },
   "funcion": {
    "texto": "Lugar desde donde Dios habla a Moisés",
    "ref": "Ex 25:22",
    "cita": "hablaré contigo de sobre la cubierta"
   },
   "nota": "La RV1909 lo llama «cubierta». El texto no da su grosor ni la altura de los querubines."
  },
  {
   "id": "mesa",
   "nombre": "Mesa de los panes de la proposición",
   "grupo": "mobiliario",
   "instruccion": "Ex 25:23-30",
   "construccion": "Ex 37:10-16",
   "medidas": {
    "largo": {
     "codos": 2,
     "ref": "Ex 25:23",
     "cita": "su longitud será de dos codos",
     "certeza": "texto"
    },
    "ancho": {
     "codos": 1,
     "ref": "Ex 25:23",
     "cita": "de un codo su anchura",
     "certeza": "texto"
    },
    "alto": {
     "codos": 1.5,
     "ref": "Ex 25:23",
     "cita": "su altura de codo y medio",
     "certeza": "texto"
    }
   },
   "materiales": [
    {
     "nombre": "madera de Sittim",
     "ref": "Ex 25:23",
     "cita": "una mesa de madera de Sittim"
    },
    {
     "nombre": "oro puro",
     "ref": "Ex 25:24",
     "cita": "la cubrirás de oro puro"
    },
    {
     "nombre": "moldura de un palmo",
     "ref": "Ex 25:25",
     "cita": "una moldura alrededor, del ancho de una mano"
    }
   ],
   "zona": {
    "id": "santo",
    "certeza": "texto",
    "ref": "Ex 26:35",
    "cita": "pondrás la mesa fuera del velo",
    "nota": null
   },
   "plano": {
    "x": 40,
    "y": 28,
    "certeza": "inferido",
    "nota": "Lado norte del lugar santo; la coordenada exacta es un supuesto.",
    "relacion": [
     {
      "texto": "al norte",
      "ref": "Ex 26:35",
      "cita": "pondrás la mesa al lado del aquilón"
     },
     {
      "texto": "al norte, fuera del velo",
      "ref": "Ex 40:22",
      "cita": "al lado septentrional del pabellón, fuera del velo"
     }
    ]
   },
   "funcion": {
    "texto": "Sostener el pan de la proposición",
    "ref": "Ex 25:30",
    "cita": "pondrás sobre la mesa el pan de la proposición delante de mí continuamente"
   },
   "nota": null
  },
  {
   "id": "candelabro",
   "nombre": "Candelabro (candelero) de oro",
   "grupo": "mobiliario",
   "instruccion": "Ex 25:31-40",
   "construccion": "Ex 37:17-24",
   "medidas": {},
   "materiales": [
    {
     "nombre": "oro puro labrado a martillo",
     "ref": "Ex 25:31",
     "cita": "un candelero de oro puro"
    },
    {
     "nombre": "un talento de oro",
     "ref": "Ex 25:39",
     "cita": "De un talento de oro fino lo harás"
    }
   ],
   "detalles": [
    {
     "texto": "seis brazos, tres a cada lado",
     "ref": "Ex 25:32",
     "cita": "saldrán seis brazos de sus lados"
    },
    {
     "texto": "siete lámparas",
     "ref": "Ex 25:37",
     "cita": "hacerle has siete candilejas"
    }
   ],
   "zona": {
    "id": "santo",
    "certeza": "texto",
    "ref": "Ex 40:24",
    "cita": "puso el candelero en el tabernáculo del testimonio",
    "nota": null
   },
   "plano": {
    "x": 40,
    "y": 22,
    "certeza": "inferido",
    "nota": "Lado sur del lugar santo; la coordenada exacta es un supuesto.",
    "relacion": [
     {
      "texto": "al sur, frente a la mesa",
      "ref": "Ex 26:35",
      "cita": "el candelero enfrente de la mesa al lado del tabernáculo al mediodía"
     },
     {
      "texto": "al sur, frente a la mesa",
      "ref": "Ex 40:24",
      "cita": "enfrente de la mesa, al lado meridional del pabellón"
     }
    ]
   },
   "funcion": {
    "texto": "Alumbrar",
    "ref": "Ex 25:37",
    "cita": "las cuales encenderás para que alumbren"
   },
   "nota": "El texto NO da medidas del candelabro (ni alto ni ancho), solo su peso: un talento de oro."
  },
  {
   "id": "altar-incienso",
   "nombre": "Altar del incienso (altar de oro)",
   "grupo": "mobiliario",
   "instruccion": "Ex 30:1-10",
   "construccion": "Ex 37:25-28",
   "medidas": {
    "largo": {
     "codos": 1,
     "ref": "Ex 30:2",
     "cita": "Su longitud será de un codo",
     "certeza": "texto"
    },
    "ancho": {
     "codos": 1,
     "ref": "Ex 30:2",
     "cita": "su anchura de un codo",
     "certeza": "texto"
    },
    "alto": {
     "codos": 2,
     "ref": "Ex 30:2",
     "cita": "su altura de dos codos",
     "certeza": "texto"
    }
   },
   "materiales": [
    {
     "nombre": "madera de Sittim",
     "ref": "Ex 30:1",
     "cita": "de madera de Sittim lo harás"
    },
    {
     "nombre": "oro puro",
     "ref": "Ex 30:3",
     "cita": "cubrirlo has de oro puro"
    }
   ],
   "zona": {
    "id": "santo",
    "certeza": "texto",
    "ref": "Ex 40:26",
    "cita": "Puso también el altar de oro en el tabernáculo del testimonio, delante del velo",
    "nota": null
   },
   "plano": {
    "x": 32,
    "y": 25,
    "certeza": "inferido",
    "nota": "Delante del velo, en el eje; la distancia exacta es un supuesto.",
    "relacion": [
     {
      "texto": "delante del velo",
      "ref": "Ex 30:6",
      "cita": "lo pondrás delante del velo que está junto al arca del testimonio"
     },
     {
      "texto": "delante del velo",
      "ref": "Ex 40:26",
      "cita": "delante del velo"
     }
    ]
   },
   "funcion": {
    "texto": "Quemar incienso mañana y tarde",
    "ref": "Ex 30:7",
    "cita": "quemará sobre él Aarón sahumerio de aroma cada mañana"
   },
   "nota": "La RV1909 lo llama «altar de sahumerio de perfume» (Ex 30:1) y «altar de oro» (Ex 40:26)."
  },
  {
   "id": "altar-holocausto",
   "nombre": "Altar del holocausto (de bronce)",
   "grupo": "mobiliario",
   "instruccion": "Ex 27:1-8",
   "construccion": "Ex 38:1-7",
   "medidas": {
    "largo": {
     "codos": 5,
     "ref": "Ex 27:1",
     "cita": "de cinco codos de longitud",
     "certeza": "texto"
    },
    "ancho": {
     "codos": 5,
     "ref": "Ex 27:1",
     "cita": "de cinco codos de anchura",
     "certeza": "texto"
    },
    "alto": {
     "codos": 3,
     "ref": "Ex 27:1",
     "cita": "su altura de tres codos",
     "certeza": "texto"
    }
   },
   "materiales": [
    {
     "nombre": "madera de Sittim",
     "ref": "Ex 27:1",
     "cita": "altar de madera de Sittim"
    },
    {
     "nombre": "cubierto de metal (bronce)",
     "ref": "Ex 27:2",
     "cita": "lo cubrirás de metal"
    },
    {
     "nombre": "enrejado de metal",
     "ref": "Ex 27:4",
     "cita": "un enrejado de metal de obra de malla"
    }
   ],
   "zona": {
    "id": "atrio",
    "certeza": "texto",
    "ref": "Ex 40:33",
    "cita": "erigió el atrio en derredor del tabernáculo y del altar",
    "nota": null
   },
   "plano": {
    "x": 75,
    "y": 25,
    "certeza": "inferido",
    "nota": "Entre la puerta del atrio y el tabernáculo; la distancia exacta es un supuesto.",
    "relacion": [
     {
      "texto": "delante de la puerta del tabernáculo",
      "ref": "Ex 40:6",
      "cita": "pondrás el altar del holocausto delante de la puerta del tabernáculo"
     },
     {
      "texto": "a la puerta del tabernáculo",
      "ref": "Ex 40:29",
      "cita": "colocó el altar del holocausto á la puerta del tabernáculo"
     }
    ]
   },
   "funcion": {
    "texto": "Ofrecer holocaustos y presentes",
    "ref": "Ex 40:29",
    "cita": "ofreció sobre él holocausto y presente"
   },
   "nota": "«Metal» en la RV1909 traduce el hebreo nechóshet (bronce o cobre). Hueco, hecho de tablas (Ex 27:8)."
  },
  {
   "id": "fuente",
   "nombre": "Fuente de bronce (lavacro)",
   "grupo": "mobiliario",
   "instruccion": "Ex 30:17-21",
   "construccion": "Ex 38:8",
   "medidas": {},
   "materiales": [
    {
     "nombre": "metal (bronce), con su basa",
     "ref": "Ex 30:18",
     "cita": "una fuente de metal, con su basa de metal"
    },
    {
     "nombre": "de los espejos de las mujeres que servían a la puerta",
     "ref": "Ex 38:8",
     "cita": "de los espejos de las que velaban"
    }
   ],
   "zona": {
    "id": "atrio",
    "certeza": "inferido",
    "ref": "Ex 30:18",
    "cita": "entre el tabernáculo del testimonio y el altar",
    "nota": "Está entre el tabernáculo y el altar, ambos dentro del atrio (Ex 40:33)."
   },
   "plano": {
    "x": 62,
    "y": 25,
    "certeza": "inferido",
    "nota": "Entre el tabernáculo y el altar; la coordenada exacta es un supuesto.",
    "relacion": [
     {
      "texto": "entre el tabernáculo y el altar",
      "ref": "Ex 30:18",
      "cita": "la has de poner entre el tabernáculo del testimonio y el altar"
     },
     {
      "texto": "entre el tabernáculo y el altar",
      "ref": "Ex 40:30",
      "cita": "puso la fuente entre el tabernáculo del testimonio y el altar"
     }
    ]
   },
   "funcion": {
    "texto": "Lavarse manos y pies los sacerdotes",
    "ref": "Ex 30:19",
    "cita": "se lavarán Aarón y sus hijos sus manos y sus pies"
   },
   "nota": "El texto NO da medidas ni forma de la fuente."
  },
  {
   "id": "tablas",
   "nombre": "Tablas del tabernáculo",
   "grupo": "estructura",
   "instruccion": "Ex 26:15-25",
   "construccion": "Ex 36:20-30",
   "medidas": {
    "largo": {
     "codos": 10,
     "ref": "Ex 26:16",
     "cita": "La longitud de cada tabla será de diez codos",
     "certeza": "texto",
     "nota": "De pie, el largo de la tabla es la altura del tabernáculo."
    },
    "ancho": {
     "codos": 1.5,
     "ref": "Ex 26:16",
     "cita": "de codo y medio la anchura de cada tabla",
     "certeza": "texto"
    }
   },
   "cantidad": {
    "valor": 48,
    "ref": null,
    "cita": null,
    "certeza": "calculo",
    "calculo": "tablas-total"
   },
   "materiales": [
    {
     "nombre": "madera de Sittim",
     "ref": "Ex 26:15",
     "cita": "tablas de madera de Sittim"
    },
    {
     "nombre": "cubiertas de oro",
     "ref": "Ex 26:29",
     "cita": "cubrirás las tablas de oro"
    }
   ],
   "zona": null,
   "plano": {
    "x": 35,
    "y": 25,
    "certeza": "inferido",
    "nota": "Contorno del tabernáculo: 30 codos de largo (cálculo) por 10 de ancho interior (tradición); posición en el atrio = supuesto de dibujo.",
    "rect": {
     "x0": 20,
     "y0": 20,
     "x1": 50,
     "y1": 30
    }
   },
   "nota": "El texto no da el grosor de las tablas (Rashi: un codo)."
  },
  {
   "id": "basas",
   "nombre": "Basas de plata de las tablas",
   "grupo": "estructura",
   "instruccion": "Ex 26:19-25",
   "construccion": "Ex 36:24-30",
   "medidas": {},
   "cantidad": {
    "valor": 96,
    "ref": null,
    "cita": null,
    "certeza": "calculo",
    "calculo": "basas-tablas"
   },
   "materiales": [
    {
     "nombre": "plata",
     "ref": "Ex 26:19",
     "cita": "cuarenta basas de plata"
    }
   ],
   "zona": null,
   "plano": {
    "x": 35,
    "y": 25,
    "certeza": "inferido",
    "nota": "Bajo las tablas.",
    "rect": {
     "x0": 20,
     "y0": 20,
     "x1": 50,
     "y1": 30
    }
   },
   "nota": "Dos basas por tabla (Ex 26:19). No incluye las basas de las columnas del velo ni de la entrada."
  },
  {
   "id": "barras",
   "nombre": "Barras",
   "grupo": "estructura",
   "instruccion": "Ex 26:26-29",
   "construccion": "Ex 36:31-34",
   "medidas": {},
   "cantidad": {
    "valor": 15,
    "ref": null,
    "cita": null,
    "certeza": "calculo",
    "calculo": "barras"
   },
   "materiales": [
    {
     "nombre": "madera de Sittim",
     "ref": "Ex 26:26",
     "cita": "cinco barras de madera de Sittim"
    },
    {
     "nombre": "cubiertas de oro",
     "ref": "Ex 26:29",
     "cita": "también cubrirás las barras de oro"
    }
   ],
   "detalles": [
    {
     "texto": "la barra del medio atraviesa de un extremo a otro",
     "ref": "Ex 26:28",
     "cita": "la barra del medio pasará por medio de las tablas, del un cabo al otro"
    }
   ],
   "zona": null,
   "plano": {
    "x": 35,
    "y": 25,
    "certeza": "inferido",
    "nota": "En las paredes sur, norte y occidental.",
    "rect": {
     "x0": 20,
     "y0": 20,
     "x1": 50,
     "y1": 30
    }
   },
   "nota": "El texto no da su longitud."
  },
  {
   "id": "columnas-tabernaculo",
   "nombre": "Columnas del velo y de la entrada",
   "grupo": "estructura",
   "instruccion": "Ex 26:32-37",
   "construccion": "Ex 36:36-38",
   "medidas": {},
   "cantidad": {
    "valor": 9,
    "ref": null,
    "cita": null,
    "certeza": "calculo",
    "calculo": "columnas-tabernaculo"
   },
   "materiales": [
    {
     "nombre": "madera de Sittim cubierta de oro (velo)",
     "ref": "Ex 26:32",
     "cita": "cuatro columnas de madera de Sittim cubiertas de oro"
    },
    {
     "nombre": "basas de plata (velo)",
     "ref": "Ex 26:32",
     "cita": "sobre basas de plata"
    },
    {
     "nombre": "cubiertas de oro (entrada)",
     "ref": "Ex 26:37",
     "cita": "las cuales cubrirás de oro"
    },
    {
     "nombre": "cinco basas de metal (entrada)",
     "ref": "Ex 26:37",
     "cita": "cinco basas de metal"
    }
   ],
   "zona": null,
   "plano": {
    "x": 40,
    "y": 25,
    "certeza": "inferido",
    "nota": "Cuatro en la línea del velo (x = 30) y cinco en la entrada (x = 50); reparto equidistante supuesto."
   },
   "nota": "El texto no da su altura."
  },
  {
   "id": "cortinas-lino",
   "nombre": "Cortinas de lino (el tabernáculo)",
   "grupo": "cortinas",
   "instruccion": "Ex 26:1-6",
   "construccion": "Ex 36:8-13",
   "medidas": {
    "largo": {
     "codos": 28,
     "ref": "Ex 26:2",
     "cita": "La longitud de la una cortina de veintiocho codos",
     "certeza": "texto"
    },
    "ancho": {
     "codos": 4,
     "ref": "Ex 26:2",
     "cita": "la anchura de la misma cortina de cuatro codos",
     "certeza": "texto"
    }
   },
   "cantidad": {
    "valor": 10,
    "ref": "Ex 26:1",
    "cita": "diez cortinas",
    "certeza": "texto"
   },
   "materiales": [
    {
     "nombre": "lino torcido, cárdeno, púrpura y carmesí, con querubines",
     "ref": "Ex 26:1",
     "cita": "diez cortinas de lino torcido, cárdeno, y púrpura, y carmesí"
    },
    {
     "nombre": "cincuenta corchetes de oro",
     "ref": "Ex 26:6",
     "cita": "cincuenta corchetes de oro"
    }
   ],
   "zona": null,
   "plano": {
    "x": 35,
    "y": 25,
    "certeza": "inferido",
    "nota": "Cubren el tabernáculo.",
    "rect": {
     "x0": 20,
     "y0": 20,
     "x1": 50,
     "y1": 30
    }
   },
   "funcion": {
    "texto": "Forman el tabernáculo",
    "ref": "Ex 26:6",
    "cita": "se formará un tabernáculo"
   },
   "nota": "Dos grupos de cinco unidos con corchetes (Ex 26:3-6): ver cálculos lino-ancho y lino-grupo."
  },
  {
   "id": "cortinas-cabra",
   "nombre": "Cortinas de pelo de cabra (la tienda)",
   "grupo": "cortinas",
   "instruccion": "Ex 26:7-13",
   "construccion": "Ex 36:14-18",
   "medidas": {
    "largo": {
     "codos": 30,
     "ref": "Ex 26:8",
     "cita": "La longitud de la una cortina será de treinta codos",
     "certeza": "texto"
    },
    "ancho": {
     "codos": 4,
     "ref": "Ex 26:8",
     "cita": "la anchura de la misma cortina de cuatro codos",
     "certeza": "texto"
    }
   },
   "cantidad": {
    "valor": 11,
    "ref": "Ex 26:7",
    "cita": "once cortinas harás",
    "certeza": "texto"
   },
   "materiales": [
    {
     "nombre": "pelo de cabras",
     "ref": "Ex 26:7",
     "cita": "cortinas de [pelo] de cabras"
    },
    {
     "nombre": "cincuenta corchetes de metal",
     "ref": "Ex 26:11",
     "cita": "cincuenta corchetes de alambre"
    }
   ],
   "zona": null,
   "plano": {
    "x": 35,
    "y": 25,
    "certeza": "inferido",
    "nota": "Sobre las de lino.",
    "rect": {
     "x0": 20,
     "y0": 20,
     "x1": 50,
     "y1": 30
    }
   },
   "funcion": {
    "texto": "Cubierta sobre el tabernáculo",
    "ref": "Ex 26:7",
    "cita": "para una cubierta sobre el tabernáculo"
   },
   "nota": "Once cortinas: la sexta se dobla delante y media cortina cuelga detrás (Ex 26:9, 26:12)."
  },
  {
   "id": "cubiertas",
   "nombre": "Cubiertas de pieles",
   "grupo": "cortinas",
   "instruccion": "Ex 26:14",
   "construccion": "Ex 36:19",
   "medidas": {},
   "materiales": [
    {
     "nombre": "cueros de carneros teñidos de rojo",
     "ref": "Ex 26:14",
     "cita": "una cubierta de cueros de carneros, teñidos de rojo"
    },
    {
     "nombre": "cueros de tejones, encima",
     "ref": "Ex 26:14",
     "cita": "una cubierta de cueros de tejones encima"
    }
   ],
   "zona": null,
   "plano": {
    "x": 35,
    "y": 25,
    "certeza": "inferido",
    "nota": "Encima de todo.",
    "rect": {
     "x0": 20,
     "y0": 20,
     "x1": 50,
     "y1": 30
    }
   },
   "nota": "El texto NO da medidas. «Tejones» es la traducción de la RV1909; la identificación del animal es dudosa."
  },
  {
   "id": "velo",
   "nombre": "Velo",
   "grupo": "cortinas",
   "instruccion": "Ex 26:31-33",
   "construccion": "Ex 36:35-36",
   "medidas": {},
   "materiales": [
    {
     "nombre": "cárdeno, púrpura, carmesí y lino torcido, con querubines",
     "ref": "Ex 26:31",
     "cita": "un velo de cárdeno, y púrpura, y carmesí, y de lino torcido"
    }
   ],
   "zona": null,
   "plano": {
    "x": 30,
    "y": 25,
    "certeza": "inferido",
    "nota": "Línea entre el santo y el santísimo, bajo los corchetes (Ex 26:33); x = 30 resulta del cálculo largo-santo.",
    "rot": 90,
    "relacion": [
     {
      "texto": "bajo los corchetes",
      "ref": "Ex 26:33",
      "cita": "pondrás el velo debajo de los corchetes"
     }
    ]
   },
   "funcion": {
    "texto": "Separar el lugar santo del santísimo",
    "ref": "Ex 26:33",
    "cita": "aquel velo os hará separación entre el lugar santo y el santísimo"
   },
   "nota": "El texto no da sus medidas; 10 × 10 codos sería inferido del ancho y alto del tabernáculo."
  },
  {
   "id": "cortina-entrada",
   "nombre": "Cortina de la entrada del tabernáculo",
   "grupo": "cortinas",
   "instruccion": "Ex 26:36-37",
   "construccion": "Ex 36:37-38",
   "medidas": {},
   "materiales": [
    {
     "nombre": "cárdeno, púrpura, carmesí y lino torcido, obra de bordador",
     "ref": "Ex 26:36",
     "cita": "una cortina de cárdeno, y púrpura, y carmesí, y lino torcido, obra de bordador"
    }
   ],
   "zona": null,
   "plano": {
    "x": 50,
    "y": 25,
    "certeza": "inferido",
    "nota": "Lado oriental del tabernáculo (supuesto de dibujo).",
    "rot": 90,
    "relacion": [
     {
      "texto": "a la puerta del tabernáculo",
      "ref": "Ex 26:36",
      "cita": "harás á la puerta del tabernáculo una cortina"
     }
    ]
   },
   "nota": "El texto no da sus medidas. En Ex 36:37 la RV1909 la llama «velo para la puerta»."
  },
  {
   "id": "cortinas-atrio",
   "nombre": "Cortinas del atrio",
   "grupo": "atrio",
   "instruccion": "Ex 27:9-15",
   "construccion": "Ex 38:9-16",
   "medidas": {
    "largo": {
     "codos": 100,
     "ref": "Ex 27:9",
     "cita": "de cien codos de longitud cada un lado",
     "certeza": "texto",
     "nota": "Lados sur y norte; occidente 50 (Ex 27:12), oriente 15 + 15 (Ex 27:14-15)."
    },
    "alto": {
     "codos": 5,
     "ref": "Ex 27:18",
     "cita": "la altura de cinco codos",
     "certeza": "texto"
    }
   },
   "materiales": [
    {
     "nombre": "lino torcido",
     "ref": "Ex 27:9",
     "cita": "cortinas de lino torcido"
    }
   ],
   "zona": {
    "id": "atrio",
    "certeza": "texto",
    "ref": "Ex 27:9",
    "cita": "harás el atrio del tabernáculo",
    "nota": null
   },
   "plano": {
    "x": 50,
    "y": 25,
    "certeza": "texto",
    "nota": "Perímetro del atrio (medidas del texto).",
    "rect": {
     "x0": 0,
     "y0": 0,
     "x1": 100,
     "y1": 50
    }
   },
   "nota": "Total: ver cálculo atrio-cortinas (280 codos más los 20 de la puerta)."
  },
  {
   "id": "columnas-atrio",
   "nombre": "Columnas del atrio",
   "grupo": "atrio",
   "instruccion": "Ex 27:10-17",
   "construccion": "Ex 38:10-19",
   "medidas": {},
   "cantidad": {
    "valor": 60,
    "ref": null,
    "cita": null,
    "certeza": "calculo",
    "calculo": "columnas-atrio"
   },
   "materiales": [
    {
     "nombre": "basas de metal (bronce)",
     "ref": "Ex 27:10",
     "cita": "sus veinte basas serán de metal"
    },
    {
     "nombre": "capiteles y molduras de plata",
     "ref": "Ex 27:10",
     "cita": "los capiteles de las columnas y sus molduras, de plata"
    },
    {
     "nombre": "ceñidas de plata",
     "ref": "Ex 27:17",
     "cita": "serán ceñidas de plata"
    }
   ],
   "zona": {
    "id": "atrio",
    "certeza": "texto",
    "ref": "Ex 27:17",
    "cita": "Todas las columnas del atrio en derredor",
    "nota": null
   },
   "plano": {
    "x": 50,
    "y": 25,
    "certeza": "inferido",
    "nota": "En el perímetro; reparto cada 5 codos supuesto (100/20, 50/10).",
    "rect": {
     "x0": 0,
     "y0": 0,
     "x1": 100,
     "y1": 50
    }
   },
   "nota": "El texto no da su altura ni su grosor; la altura de las cortinas es 5 codos (Ex 27:18)."
  },
  {
   "id": "puerta-atrio",
   "nombre": "Puerta (pabellón) del atrio",
   "grupo": "atrio",
   "instruccion": "Ex 27:16",
   "construccion": "Ex 38:18-19",
   "medidas": {
    "largo": {
     "codos": 20,
     "ref": "Ex 27:16",
     "cita": "un pabellón de veinte codos",
     "certeza": "texto"
    }
   },
   "materiales": [
    {
     "nombre": "cárdeno, púrpura, carmesí y lino torcido, obra de bordador",
     "ref": "Ex 27:16",
     "cita": "de cárdeno, y púrpura, y carmesí, y lino torcido, de obra de bordador"
    }
   ],
   "detalles": [
    {
     "texto": "cuatro columnas con cuatro basas",
     "ref": "Ex 27:16",
     "cita": "sus columnas cuatro, con sus cuatro basas"
    }
   ],
   "zona": {
    "id": "atrio",
    "certeza": "texto",
    "ref": "Ex 27:16",
    "cita": "á la puerta del atrio",
    "nota": null
   },
   "plano": {
    "x": 100,
    "y": 25,
    "certeza": "inferido",
    "nota": "Lado oriental; centrada porque quedan 15 codos a cada lado (cálculo atrio-oriente).",
    "rot": 90,
    "relacion": [
     {
      "texto": "al oriente",
      "ref": "Ex 27:13",
      "cita": "por la parte de levante, al oriente"
     }
    ]
   },
   "nota": "Los 20 codos son el ancho del vano; el texto no da su altura (Ex 38:18 la compara con las cortinas: cinco codos)."
  }
 ],
 "calculos": [
  {
   "id": "largo-tabernaculo",
   "texto": "20 tablas × 1½ codos = 30 codos de largo del tabernáculo",
   "operacion": "20*1.5",
   "resultado": 30,
   "certeza": "calculo",
   "pasos": [
    {
     "texto": "20 tablas en el lado sur",
     "ref": "Ex 26:18",
     "cita": "veinte tablas al lado del mediodía",
     "valor": 20
    },
    {
     "texto": "cada tabla mide codo y medio de ancho",
     "ref": "Ex 26:16",
     "cita": "de codo y medio la anchura de cada tabla",
     "valor": 1.5
    }
   ]
  },
  {
   "id": "pared-occidental",
   "texto": "6 tablas × 1½ codos = 9 codos en el fondo (sin las esquinas)",
   "operacion": "6*1.5",
   "resultado": 9,
   "certeza": "calculo",
   "pasos": [
    {
     "texto": "6 tablas al occidente",
     "ref": "Ex 26:22",
     "cita": "harás seis tablas",
     "valor": 6
    },
    {
     "texto": "cada tabla mide codo y medio de ancho",
     "ref": "Ex 26:16",
     "cita": "de codo y medio la anchura de cada tabla",
     "valor": 1.5
    }
   ]
  },
  {
   "id": "ancho-interior",
   "texto": "9 codos + 2 esquinas × ½ codo = 10 codos de ancho interior (tradición)",
   "operacion": "9+2*0.5",
   "resultado": 10,
   "certeza": "tradicion",
   "nota": "El texto no da el ancho del tabernáculo. Los 10 codos son la lectura de Rashi: tablas de un codo de grueso; cada tabla de esquina añade medio codo al interior. Otras reconstrucciones dan 12 codos por fuera.",
   "pasos": [
    {
     "texto": "fondo sin esquinas",
     "ref": null,
     "cita": null,
     "calculo": "pared-occidental",
     "valor": 9
    },
    {
     "texto": "dos tablas de esquina",
     "ref": "Ex 26:23",
     "cita": "dos tablas para las esquinas",
     "valor": 2
    },
    {
     "texto": "cada esquina añade medio codo al interior",
     "ref": null,
     "cita": null,
     "fuente": "Rashi (Fuente externa, tradición)",
     "url": "https://www.sefaria.org/Rashi_on_Exodus.26.23",
     "valor": 0.5,
     "nota": "Rashi a Ex 26:23: «thus making up the breadth to ten cubits»"
    }
   ]
  },
  {
   "id": "tablas-total",
   "texto": "20 + 20 + 6 + 2 = 48 tablas",
   "operacion": "20+20+6+2",
   "resultado": 48,
   "certeza": "calculo",
   "pasos": [
    {
     "texto": "lado sur",
     "ref": "Ex 26:18",
     "cita": "veinte tablas al lado del mediodía",
     "valor": 20
    },
    {
     "texto": "lado norte",
     "ref": "Ex 26:20",
     "cita": "veinte tablas",
     "valor": 20
    },
    {
     "texto": "occidente",
     "ref": "Ex 26:22",
     "cita": "harás seis tablas",
     "valor": 6
    },
    {
     "texto": "esquinas",
     "ref": "Ex 26:23",
     "cita": "dos tablas para las esquinas",
     "valor": 2
    },
    {
     "texto": "el texto suma el occidente con las esquinas",
     "ref": "Ex 26:25",
     "cita": "serán ocho tablas",
     "valor": 8
    }
   ]
  },
  {
   "id": "basas-tablas",
   "texto": "40 + 40 + 16 = 96 basas de plata bajo las tablas",
   "operacion": "40+40+16",
   "resultado": 96,
   "certeza": "calculo",
   "pasos": [
    {
     "texto": "sur",
     "ref": "Ex 26:19",
     "cita": "cuarenta basas de plata",
     "valor": 40
    },
    {
     "texto": "norte",
     "ref": "Ex 26:21",
     "cita": "sus cuarenta basas de plata",
     "valor": 40
    },
    {
     "texto": "occidente y esquinas",
     "ref": "Ex 26:25",
     "cita": "diez y seis basas",
     "valor": 16
    }
   ]
  },
  {
   "id": "basas-por-tabla",
   "texto": "48 tablas × 2 basas = 96 basas (comprobación)",
   "operacion": "48*2",
   "resultado": 96,
   "certeza": "calculo",
   "pasos": [
    {
     "texto": "total de tablas",
     "ref": null,
     "cita": null,
     "calculo": "tablas-total",
     "valor": 48
    },
    {
     "texto": "dos basas por tabla",
     "ref": "Ex 26:19",
     "cita": "dos basas debajo de la una tabla",
     "valor": 2
    }
   ]
  },
  {
   "id": "barras",
   "texto": "5 + 5 + 5 = 15 barras",
   "operacion": "5+5+5",
   "resultado": 15,
   "certeza": "calculo",
   "nota": "Si la barra del medio (Ex 26:28) es una de las cinco de cada lado o una más, el texto no lo precisa.",
   "pasos": [
    {
     "texto": "un lado",
     "ref": "Ex 26:26",
     "cita": "cinco barras de madera de Sittim",
     "valor": 5
    },
    {
     "texto": "el otro lado",
     "ref": "Ex 26:27",
     "cita": "cinco barras para las tablas del otro lado",
     "valor": 5
    },
    {
     "texto": "occidente",
     "ref": "Ex 26:27",
     "cita": "cinco barras para el otro lado del tabernáculo, que está al occidente",
     "valor": 5
    }
   ]
  },
  {
   "id": "columnas-tabernaculo",
   "texto": "4 columnas del velo + 5 de la entrada = 9 columnas",
   "operacion": "4+5",
   "resultado": 9,
   "certeza": "calculo",
   "pasos": [
    {
     "texto": "velo",
     "ref": "Ex 26:32",
     "cita": "cuatro columnas de madera de Sittim",
     "valor": 4
    },
    {
     "texto": "cortina de la entrada",
     "ref": "Ex 26:37",
     "cita": "cinco columnas de madera de Sittim",
     "valor": 5
    }
   ]
  },
  {
   "id": "lino-ancho",
   "texto": "10 cortinas × 4 codos = 40 codos de ancho unidas",
   "operacion": "10*4",
   "resultado": 40,
   "certeza": "calculo",
   "pasos": [
    {
     "texto": "diez cortinas",
     "ref": "Ex 26:1",
     "cita": "diez cortinas de lino torcido",
     "valor": 10
    },
    {
     "texto": "cuatro codos de ancho cada una",
     "ref": "Ex 26:2",
     "cita": "la anchura de la misma cortina de cuatro codos",
     "valor": 4
    }
   ]
  },
  {
   "id": "lino-largo-total",
   "texto": "10 cortinas × 28 codos = 280 codos de cortina de lino",
   "operacion": "10*28",
   "resultado": 280,
   "certeza": "calculo",
   "pasos": [
    {
     "texto": "diez cortinas",
     "ref": "Ex 26:1",
     "cita": "diez cortinas de lino torcido",
     "valor": 10
    },
    {
     "texto": "28 codos de largo cada una",
     "ref": "Ex 26:2",
     "cita": "La longitud de la una cortina de veintiocho codos",
     "valor": 28
    }
   ]
  },
  {
   "id": "lino-grupo",
   "texto": "5 cortinas × 4 codos = 20 codos cada mitad unida por los corchetes",
   "operacion": "5*4",
   "resultado": 20,
   "certeza": "calculo",
   "pasos": [
    {
     "texto": "dos grupos de cinco",
     "ref": "Ex 26:3",
     "cita": "Cinco cortinas estarán juntas",
     "valor": 5
    },
    {
     "texto": "cuatro codos de ancho",
     "ref": "Ex 26:2",
     "cita": "la anchura de la misma cortina de cuatro codos",
     "valor": 4
    },
    {
     "texto": "los grupos se unen con corchetes",
     "ref": "Ex 26:6",
     "cita": "cincuenta corchetes de oro",
     "valor": 50
    }
   ]
  },
  {
   "id": "cabra-ancho",
   "texto": "11 cortinas × 4 codos = 44 codos de ancho unidas",
   "operacion": "11*4",
   "resultado": 44,
   "certeza": "calculo",
   "pasos": [
    {
     "texto": "once cortinas",
     "ref": "Ex 26:7",
     "cita": "once cortinas harás",
     "valor": 11
    },
    {
     "texto": "cuatro codos de ancho",
     "ref": "Ex 26:8",
     "cita": "la anchura de la misma cortina de cuatro codos",
     "valor": 4
    }
   ]
  },
  {
   "id": "cabra-sobrante",
   "texto": "44 − 40 = 4 codos más que las de lino (una cortina)",
   "operacion": "44-40",
   "resultado": 4,
   "certeza": "calculo",
   "pasos": [
    {
     "texto": "pelo de cabra",
     "ref": null,
     "cita": null,
     "calculo": "cabra-ancho",
     "valor": 44
    },
    {
     "texto": "lino",
     "ref": null,
     "cita": null,
     "calculo": "lino-ancho",
     "valor": 40
    },
    {
     "texto": "la sexta se dobla delante",
     "ref": "Ex 26:9",
     "cita": "doblarás la sexta cortina delante de la faz del tabernáculo"
    },
    {
     "texto": "media cortina sobra detrás",
     "ref": "Ex 26:12",
     "cita": "la mitad de la una cortina que sobra, quedará á las espaldas del tabernáculo"
    }
   ]
  },
  {
   "id": "cabra-largo",
   "texto": "30 − 28 = 2 codos: uno de más a cada lado",
   "operacion": "30-28",
   "resultado": 2,
   "certeza": "calculo",
   "pasos": [
    {
     "texto": "pelo de cabra: 30 codos",
     "ref": "Ex 26:8",
     "cita": "La longitud de la una cortina será de treinta codos",
     "valor": 30
    },
    {
     "texto": "lino: 28 codos",
     "ref": "Ex 26:2",
     "cita": "La longitud de la una cortina de veintiocho codos",
     "valor": 28
    },
    {
     "texto": "el texto lo confirma: un codo por cada lado",
     "ref": "Ex 26:13",
     "cita": "un codo de la una parte, y otro codo de la otra",
     "valor": 1
    }
   ]
  },
  {
   "id": "largo-santo",
   "texto": "Lugar santo: 5 cortinas × 4 codos = 20 codos desde la entrada hasta el velo",
   "operacion": "5*4",
   "resultado": 20,
   "certeza": "inferido",
   "nota": "El texto no da el largo del lugar santo. Sale de colgar el velo bajo los corchetes, suponiendo que las cortinas de lino empiezan en la entrada. Rashi (Ex 26:32-35) da también 20 codos.",
   "pasos": [
    {
     "texto": "el velo cuelga bajo los corchetes",
     "ref": "Ex 26:33",
     "cita": "pondrás el velo debajo de los corchetes"
    },
    {
     "texto": "primer grupo de cinco cortinas",
     "ref": "Ex 26:3",
     "cita": "Cinco cortinas estarán juntas",
     "valor": 5
    },
    {
     "texto": "cuatro codos cada una",
     "ref": "Ex 26:2",
     "cita": "la anchura de la misma cortina de cuatro codos",
     "valor": 4
    },
    {
     "texto": "supuesto: las cortinas empiezan en la entrada (oriente)",
     "ref": null,
     "cita": null,
     "supuesto": true
    },
    {
     "texto": "Rashi llega a los mismos 20 codos",
     "ref": null,
     "cita": null,
     "fuente": "Rashi (Fuente externa, tradición)",
     "url": "https://www.sefaria.org/Rashi_on_Exodus.26.35",
     "nota": "Rashi a Ex 26:35: «from the entrance to the partition veil was 20 cubits»"
    }
   ]
  },
  {
   "id": "largo-santisimo",
   "texto": "Lugar santísimo: 30 − 20 = 10 codos",
   "operacion": "30-20",
   "resultado": 10,
   "certeza": "inferido",
   "pasos": [
    {
     "texto": "largo del tabernáculo",
     "ref": null,
     "cita": null,
     "calculo": "largo-tabernaculo",
     "valor": 30
    },
    {
     "texto": "largo del lugar santo (inferido)",
     "ref": null,
     "cita": null,
     "calculo": "largo-santo",
     "valor": 20
    }
   ]
  },
  {
   "id": "alto-tabernaculo",
   "texto": "Altura: tablas de 10 codos puestas derechas = 10 codos",
   "operacion": "10",
   "resultado": 10,
   "certeza": "inferido",
   "pasos": [
    {
     "texto": "tablas derechas",
     "ref": "Ex 26:15",
     "cita": "que estén derechas"
    },
    {
     "texto": "10 codos de largo cada tabla",
     "ref": "Ex 26:16",
     "cita": "La longitud de cada tabla será de diez codos",
     "valor": 10
    }
   ]
  },
  {
   "id": "atrio-oriente",
   "texto": "Lado oriental: 15 + 20 + 15 = 50 codos (cortinas, puerta, cortinas)",
   "operacion": "15+20+15",
   "resultado": 50,
   "certeza": "calculo",
   "pasos": [
    {
     "texto": "cortinas de un lado",
     "ref": "Ex 27:14",
     "cita": "serán de quince codos",
     "valor": 15
    },
    {
     "texto": "puerta",
     "ref": "Ex 27:16",
     "cita": "un pabellón de veinte codos",
     "valor": 20
    },
    {
     "texto": "cortinas del otro lado",
     "ref": "Ex 27:15",
     "cita": "Al otro lado quince codos de cortinas",
     "valor": 15
    },
    {
     "texto": "el lado oriental mide 50",
     "ref": "Ex 27:13",
     "cita": "habrá cincuenta codos",
     "valor": 50
    }
   ]
  },
  {
   "id": "atrio-perimetro",
   "texto": "Perímetro del atrio: 100 + 100 + 50 + 50 = 300 codos",
   "operacion": "100+100+50+50",
   "resultado": 300,
   "certeza": "calculo",
   "pasos": [
    {
     "texto": "sur",
     "ref": "Ex 27:9",
     "cita": "cien codos de longitud",
     "valor": 100
    },
    {
     "texto": "norte",
     "ref": "Ex 27:11",
     "cita": "cortinas de cien codos de longitud",
     "valor": 100
    },
    {
     "texto": "occidente",
     "ref": "Ex 27:12",
     "cita": "cortinas de cincuenta codos",
     "valor": 50
    },
    {
     "texto": "oriente",
     "ref": "Ex 27:13",
     "cita": "habrá cincuenta codos",
     "valor": 50
    }
   ]
  },
  {
   "id": "atrio-cortinas",
   "texto": "Cortinas de lino del atrio: 100 + 100 + 50 + 15 + 15 = 280 codos (más 20 de la puerta)",
   "operacion": "100+100+50+15+15",
   "resultado": 280,
   "certeza": "calculo",
   "pasos": [
    {
     "texto": "sur",
     "ref": "Ex 27:9",
     "cita": "cien codos de longitud",
     "valor": 100
    },
    {
     "texto": "norte",
     "ref": "Ex 27:11",
     "cita": "cortinas de cien codos de longitud",
     "valor": 100
    },
    {
     "texto": "occidente",
     "ref": "Ex 27:12",
     "cita": "cortinas de cincuenta codos",
     "valor": 50
    },
    {
     "texto": "oriente, un lado",
     "ref": "Ex 27:14",
     "cita": "serán de quince codos",
     "valor": 15
    },
    {
     "texto": "oriente, otro lado",
     "ref": "Ex 27:15",
     "cita": "quince codos de cortinas",
     "valor": 15
    }
   ]
  },
  {
   "id": "atrio-area",
   "texto": "Superficie del atrio: 100 × 50 = 5000 codos cuadrados",
   "operacion": "100*50",
   "resultado": 5000,
   "certeza": "calculo",
   "pasos": [
    {
     "texto": "largo",
     "ref": "Ex 27:18",
     "cita": "La longitud del atrio será de cien codos",
     "valor": 100
    },
    {
     "texto": "ancho",
     "ref": "Ex 27:18",
     "cita": "la anchura cincuenta",
     "valor": 50
    }
   ]
  },
  {
   "id": "columnas-atrio",
   "texto": "Columnas del atrio: 20 + 20 + 10 + 3 + 3 + 4 = 60",
   "operacion": "20+20+10+3+3+4",
   "resultado": 60,
   "certeza": "calculo",
   "nota": "Suma directa de las cifras del texto; si las columnas de las esquinas se cuentan dos veces, el número real sería menor. El texto no lo aclara.",
   "pasos": [
    {
     "texto": "sur",
     "ref": "Ex 27:10",
     "cita": "Sus veinte columnas",
     "valor": 20
    },
    {
     "texto": "norte",
     "ref": "Ex 27:11",
     "cita": "sus veinte columnas",
     "valor": 20
    },
    {
     "texto": "occidente",
     "ref": "Ex 27:12",
     "cita": "sus columnas diez",
     "valor": 10
    },
    {
     "texto": "oriente, un lado",
     "ref": "Ex 27:14",
     "cita": "sus columnas tres",
     "valor": 3
    },
    {
     "texto": "oriente, otro lado",
     "ref": "Ex 27:15",
     "cita": "sus columnas tres",
     "valor": 3
    },
    {
     "texto": "puerta",
     "ref": "Ex 27:16",
     "cita": "sus columnas cuatro",
     "valor": 4
    }
   ]
  }
 ],
 "montaje": [
  {
   "orden": 1,
   "pieza": "cortinas-lino",
   "ref": "Ex 40:18",
   "cita": "Moisés hizo levantar el tabernáculo",
   "certeza": "inferido",
   "nota": "En Ex 26:1 «el tabernáculo» son las diez cortinas de lino; aquí puede designar el conjunto."
  },
  {
   "orden": 2,
   "pieza": "basas",
   "ref": "Ex 40:18",
   "cita": "asentó sus basas",
   "certeza": "texto",
   "nota": null
  },
  {
   "orden": 3,
   "pieza": "tablas",
   "ref": "Ex 40:18",
   "cita": "colocó sus tablas",
   "certeza": "texto",
   "nota": null
  },
  {
   "orden": 4,
   "pieza": "barras",
   "ref": "Ex 40:18",
   "cita": "puso sus barras",
   "certeza": "texto",
   "nota": null
  },
  {
   "orden": 5,
   "pieza": "columnas-tabernaculo",
   "ref": "Ex 40:18",
   "cita": "hizo alzar sus columnas",
   "certeza": "texto",
   "nota": null
  },
  {
   "orden": 6,
   "pieza": "cortinas-cabra",
   "ref": "Ex 40:19",
   "cita": "extendió la tienda sobre el tabernáculo",
   "certeza": "inferido",
   "nota": "«La tienda» son las cortinas de pelo de cabra (Ex 26:7, 26:11)."
  },
  {
   "orden": 7,
   "pieza": "cubiertas",
   "ref": "Ex 40:19",
   "cita": "puso la sobrecubierta encima del mismo",
   "certeza": "inferido",
   "nota": "La sobrecubierta = las cubiertas de pieles (Ex 26:14)."
  },
  {
   "orden": 8,
   "pieza": "arca",
   "ref": "Ex 40:20",
   "cita": "puso el testimonio dentro del arca",
   "certeza": "texto",
   "nota": null
  },
  {
   "orden": 9,
   "pieza": "arca",
   "ref": "Ex 40:20",
   "cita": "colocó las varas en el arca",
   "certeza": "texto",
   "nota": null
  },
  {
   "orden": 10,
   "pieza": "propiciatorio",
   "ref": "Ex 40:20",
   "cita": "encima la cubierta sobre el arca",
   "certeza": "texto",
   "nota": null
  },
  {
   "orden": 11,
   "pieza": "arca",
   "ref": "Ex 40:21",
   "cita": "metió el arca en el tabernáculo",
   "certeza": "texto",
   "nota": null
  },
  {
   "orden": 12,
   "pieza": "velo",
   "ref": "Ex 40:21",
   "cita": "puso el velo de la tienda",
   "certeza": "texto",
   "nota": null
  },
  {
   "orden": 13,
   "pieza": "mesa",
   "ref": "Ex 40:22",
   "cita": "puso la mesa en el tabernáculo del testimonio",
   "certeza": "texto",
   "nota": null
  },
  {
   "orden": 14,
   "pieza": "mesa",
   "ref": "Ex 40:23",
   "cita": "sobre ella puso por orden los panes",
   "certeza": "texto",
   "nota": null
  },
  {
   "orden": 15,
   "pieza": "candelabro",
   "ref": "Ex 40:24",
   "cita": "puso el candelero en el tabernáculo del testimonio",
   "certeza": "texto",
   "nota": null
  },
  {
   "orden": 16,
   "pieza": "candelabro",
   "ref": "Ex 40:25",
   "cita": "encendió las lámparas",
   "certeza": "texto",
   "nota": null
  },
  {
   "orden": 17,
   "pieza": "altar-incienso",
   "ref": "Ex 40:26",
   "cita": "Puso también el altar de oro",
   "certeza": "texto",
   "nota": null
  },
  {
   "orden": 18,
   "pieza": "altar-incienso",
   "ref": "Ex 40:27",
   "cita": "encendió sobre él el perfume aromático",
   "certeza": "texto",
   "nota": null
  },
  {
   "orden": 19,
   "pieza": "cortina-entrada",
   "ref": "Ex 40:28",
   "cita": "Puso asimismo la cortina de la puerta del tabernáculo",
   "certeza": "texto",
   "nota": null
  },
  {
   "orden": 20,
   "pieza": "altar-holocausto",
   "ref": "Ex 40:29",
   "cita": "colocó el altar del holocausto",
   "certeza": "texto",
   "nota": null
  },
  {
   "orden": 21,
   "pieza": "fuente",
   "ref": "Ex 40:30",
   "cita": "puso la fuente entre el tabernáculo del testimonio y el altar",
   "certeza": "texto",
   "nota": null
  },
  {
   "orden": 22,
   "pieza": "cortinas-atrio",
   "ref": "Ex 40:33",
   "cita": "erigió el atrio en derredor del tabernáculo y del altar",
   "certeza": "texto",
   "nota": null
  },
  {
   "orden": 23,
   "pieza": "puerta-atrio",
   "ref": "Ex 40:33",
   "cita": "puso la cortina de la puerta del atrio",
   "certeza": "texto",
   "nota": null
  }
 ],
 "fuentes": [
  {
   "id": "rv1909",
   "nombre": "Reina-Valera 1909",
   "tipo": "texto",
   "licencia": "dominio público",
   "url": "https://ebible.org/find/details.php?id=spaRV1909",
   "nota": "Todas las citas son literales del texto de datos/biblia.js."
  },
  {
   "id": "insight",
   "nombre": "Insight on the Scriptures, «Cubit»",
   "tipo": "Fuente externa",
   "url": "https://www.jw.org/en/library/books/Insight-on-the-Scriptures/Cubit/",
   "uso": "equivalencia del codo común (44,5 cm)"
  },
  {
   "id": "wikipedia-unidades",
   "nombre": "Wikipedia (inglés), «Biblical and Talmudic units of measurement»",
   "tipo": "Fuente externa",
   "url": "https://en.wikipedia.org/wiki/Biblical_and_Talmudic_units_of_measurement",
   "uso": "equivalencia del codo real (52,5 cm)"
  },
  {
   "id": "rashi",
   "nombre": "Rashi (s. XI), comentario a Éxodo 26, traducción inglesa en Sefaria",
   "tipo": "Fuente externa (tradición judía)",
   "url": "https://www.sefaria.org/Rashi_on_Exodus.26",
   "uso": "ancho interior de 10 codos (Rashi a Ex 26:5 y 26:23: tablas de un codo de grueso y esquinas que completan los 10 codos), lugar santo de 20 codos y santísimo de 10×10 (Rashi a Ex 26:32 y 26:35)."
  }
 ]
};
