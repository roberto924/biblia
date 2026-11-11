window.BIBLIA_RECORRIDOS = {
 "generado": "2026-11-11T20:29:35+00:00",
 "fuentes": [
  {
   "id": "rv1909",
   "nombre": "Reina-Valera 1909 (texto de las citas)",
   "licencia": "Dominio público",
   "url": "https://ebible.org/Scriptures/spaRV1909_vpl.zip"
  },
  {
   "id": "openbible",
   "nombre": "OpenBible.info, Bible Geocoding Data (coordenadas, identificaciones y puntuaciones)",
   "licencia": "CC BY 4.0",
   "url": "https://github.com/openbibleinfo/Bible-Geocoding-Data",
   "atribucion": "Ubicaciones: OpenBible.info, CC BY 4.0; identificaciones y puntuaciones adaptadas"
  },
  {
   "id": "wikipedia",
   "nombre": "Wikipedia en inglés (fuente secundaria para describir las hipótesis): «Biblical Mount Sinai», «Har Karkom», «Jabal al-Lawz», «Ur Kaśdim»",
   "licencia": "CC BY-SA 4.0 (solo datos, no texto)",
   "url": "https://en.wikipedia.org/wiki/Biblical_Mount_Sinai"
  }
 ],
 "recorridos": [
  {
   "id": "exodo",
   "titulo": "De Egipto al Sinaí",
   "libro": "Ex",
   "personas": [
    "Moses_1",
    "Aaron_1",
    "Miriam_1",
    "Joshua_1",
    "Hur_1"
   ],
   "resumen": "Itinerario de Ex 12–19: de Ramesés al desierto de Sinaí, con las fechas que da el texto (mes primero, día 15 del mes segundo, mes tercero) y cuatro hipótesis sobre dónde está el monte.",
   "hipotesis": [
    {
     "id": "tradicional",
     "nombre": "Sinaí en Jebel Musa (tradición bizantina)",
     "defecto": true,
     "descripcion": "Ruta por el sur de la península del Sinaí: cruce en la zona de los lagos Amargos, bajada por la costa del golfo de Suez y llegada a Jebel Musa. La identificación del Sinaí con Jebel Musa es la tradición cristiana desde el s. IV (iglesia de Elena hacia el 330; monasterio de Santa Catalina, s. VI; la peregrina Egeria). Fuente externa. Cada etapa usa la identificación mejor puntuada de OpenBible, salvo el cruce (ver la nota de esa etapa).",
     "fuente": "Wikipedia, «Biblical Mount Sinai» (tradición de Jebel Musa); coordenadas: OpenBible.info",
     "url": "https://en.wikipedia.org/wiki/Biblical_Mount_Sinai"
    },
    {
     "id": "sin-bishar",
     "nombre": "Sinaí en Jebel Sin Bishar (oeste-centro del Sinaí)",
     "defecto": false,
     "descripcion": "Propuesta de Menashe Har-El, geógrafo bíblico de la Universidad de Tel Aviv (The Sinai Journeys): el monte estaría en el oeste-centro de la península, mucho más al norte que Jebel Musa. Solo se sitúa aquí el monte (y las etapas de Egipto comunes a todas); las estaciones intermedias de esta propuesta no se han podido verificar y quedan sin ubicación. Fuente externa.",
     "fuente": "Wikipedia, «Biblical Mount Sinai» (Har-El y Jebel Sin Bishar); coordenadas: OpenBible.info",
     "url": "https://en.wikipedia.org/wiki/Biblical_Mount_Sinai"
    },
    {
     "id": "har-karkom",
     "nombre": "Sinaí en Har Karkom (Négueb)",
     "defecto": false,
     "descripcion": "Emmanuel Anati, que excavó Har Karkom (también Jabal Ideid), en el Négueb, la identificó con el monte Sinaí (The Riddle of Mount Sinai, 2001). Críticas recogidas: I. Finkelstein y J. K. Hoffmeier (cronología unos mil años anterior y hallazgos no exclusivos de este monte). Solo se sitúa el monte; las estaciones intermedias quedan sin ubicación. Fuente externa.",
     "fuente": "Wikipedia, «Har Karkom» y «Biblical Mount Sinai»; E. Anati, The Riddle of Mount Sinai (2001); coordenadas: OpenBible.info",
     "url": "https://en.wikipedia.org/wiki/Har_Karkom"
    },
    {
     "id": "al-lawz",
     "nombre": "Sinaí en Jabal al-Lawz, Arabia (minoritaria)",
     "defecto": false,
     "minoritaria": true,
     "descripcion": "Teoría «arábiga»: el mar sería el golfo de Áqaba y el Sinaí estaría en Jabal al-Lawz (o Jabal Maqla), en el noroeste de Arabia Saudí. La defienden autores como R. Wyatt, B. Cornuke y L. Möller; la rechazan académicos como J. K. Hoffmeier (Ancient Israel in Sinai, 2005). Se marca minoritaria porque OpenBible le da una puntuación de 4 frente a 465 de Jebel Musa. Fuente externa.",
     "fuente": "Wikipedia, «Jabal al-Lawz» y «Biblical Mount Sinai»; coordenadas: OpenBible.info",
     "url": "https://en.wikipedia.org/wiki/Jabal_al-Lawz"
    }
   ],
   "etapas": [
    {
     "orden": 1,
     "lugar": "rameses",
     "nombre": "Ramesés",
     "ref": "Ex 12:37",
     "cita": "Y partieron los hijos de Israel de Rameses",
     "tiempo": {
      "texto": "Mes primero, día 15 (la noche que sigue a la pascua del día 14)",
      "mes": 1,
      "dia": 15,
      "certeza": "calculo",
      "pasos": [
       {
        "texto": "Este mes es el primero del año.",
        "ref": "Ex 12:2",
        "cita": "será este para vosotros el primero en los meses del año"
       },
       {
        "texto": "El cordero se guarda hasta el día 14 y se inmola «entre las dos tardes».",
        "ref": "Ex 12:6",
        "cita": "hasta el día catorce de este mes"
       },
       {
        "texto": "Los panes sin levadura empiezan el día 14 por la tarde.",
        "ref": "Ex 12:18",
        "cita": "el día catorce del mes por la tarde"
       },
       {
        "texto": "A medianoche mueren los primogénitos.",
        "ref": "Ex 12:29",
        "cita": "á la medianoche"
       },
       {
        "texto": "Faraón llama a Moisés y Aarón de noche y los manda salir.",
        "ref": "Ex 12:31",
        "cita": "E hizo llamar á Moisés y á Aarón de noche"
       },
       {
        "texto": "Convención: el día hebreo empieza al ponerse el sol; la noche posterior a la tarde del día 14 ya es el día 15. Números 33:3 da expresamente «el día quince del mes primero», pero Números no está en los datos y aquí no se verifica.",
        "ref": null,
        "convencion": true
       }
      ]
     },
     "ubicaciones": {
      "tradicional": {
       "lat": 30.7994,
       "lon": 31.8342,
       "confianza": "alta",
       "identificacion": "Qantir",
       "puntuacion_openbible": 509,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Rameses → Qantir",
       "url": "https://www.openbible.info/geo/ancient/a079b21/rameses"
      },
      "sin-bishar": {
       "lat": 30.7994,
       "lon": 31.8342,
       "confianza": "alta",
       "identificacion": "Qantir (común a todas las hipótesis)",
       "puntuacion_openbible": 509,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Rameses → Qantir",
       "url": "https://www.openbible.info/geo/ancient/a079b21/rameses"
      },
      "har-karkom": {
       "lat": 30.7994,
       "lon": 31.8342,
       "confianza": "alta",
       "identificacion": "Qantir (común a todas las hipótesis)",
       "puntuacion_openbible": 509,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Rameses → Qantir",
       "url": "https://www.openbible.info/geo/ancient/a079b21/rameses"
      },
      "al-lawz": {
       "lat": 30.7994,
       "lon": 31.8342,
       "confianza": "alta",
       "identificacion": "Qantir (común a todas las hipótesis)",
       "puntuacion_openbible": 509,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Rameses → Qantir",
       "url": "https://www.openbible.info/geo/ancient/a079b21/rameses"
      }
     },
     "nota": "El texto no dice el día de la salida: dice el día 14 para la pascua y que salieron esa noche."
    },
    {
     "orden": 2,
     "lugar": "sucot-egipto",
     "nombre": "Sucot",
     "ref": "Ex 12:37",
     "cita": "de Rameses á Succoth",
     "tiempo": null,
     "ubicaciones": {
      "tradicional": {
       "lat": 30.5527,
       "lon": 32.099,
       "confianza": "media",
       "identificacion": "Tell el Maskhuta",
       "puntuacion_openbible": 206,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Succoth 2 → Tell el Maskhuta",
       "url": "https://www.openbible.info/geo/ancient/aa28709/succoth-2"
      },
      "sin-bishar": {
       "lat": 30.5527,
       "lon": 32.099,
       "confianza": "media",
       "identificacion": "Tell el Maskhuta (común a todas las hipótesis)",
       "puntuacion_openbible": 206,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Succoth 2 → Tell el Maskhuta",
       "url": "https://www.openbible.info/geo/ancient/aa28709/succoth-2"
      },
      "har-karkom": {
       "lat": 30.5527,
       "lon": 32.099,
       "confianza": "media",
       "identificacion": "Tell el Maskhuta (común a todas las hipótesis)",
       "puntuacion_openbible": 206,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Succoth 2 → Tell el Maskhuta",
       "url": "https://www.openbible.info/geo/ancient/aa28709/succoth-2"
      },
      "al-lawz": {
       "lat": 30.5527,
       "lon": 32.099,
       "confianza": "media",
       "identificacion": "Tell el Maskhuta (común a todas las hipótesis)",
       "puntuacion_openbible": 206,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Succoth 2 → Tell el Maskhuta",
       "url": "https://www.openbible.info/geo/ancient/aa28709/succoth-2"
      }
     },
     "nota": "Distinta de Sucot de Gn 33:17 (al este del Jordán)."
    },
    {
     "orden": 3,
     "lugar": "etam",
     "nombre": "Etam",
     "ref": "Ex 13:20",
     "cita": "asentaron campo en Etham, á la entrada del desierto",
     "tiempo": null,
     "ubicaciones": {
      "tradicional": {
       "lat": 30.861,
       "lon": 32.3523,
       "confianza": "media",
       "identificacion": "Tell Abu Sefeh",
       "puntuacion_openbible": 135,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Etham → Tell Abu Sefeh",
       "url": "https://www.openbible.info/geo/ancient/a27d0e0/etham"
      },
      "sin-bishar": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Biblical Mount Sinai» (Har-El y Jebel Sin Bishar); coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Biblical_Mount_Sinai"
      },
      "har-karkom": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Har Karkom» y «Biblical Mount Sinai»; E. Anati, The Riddle of Mount Sinai (2001); coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Har_Karkom"
      },
      "al-lawz": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Jabal al-Lawz» y «Biblical Mount Sinai»; coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Jabal_al-Lawz"
      }
     },
     "nota": "Sin ubicación propuesta en: Sinaí en Jebel Sin Bishar (oeste-centro del Sinaí); Sinaí en Har Karkom (Négueb); Sinaí en Jabal al-Lawz, Arabia (minoritaria)."
    },
    {
     "orden": 4,
     "lugar": "pi-hahirot",
     "nombre": "Pi-hahirot",
     "ref": "Ex 14:2",
     "cita": "asienten su campo delante de Pihahiroth, entre Migdol y la mar hacia Baalzephón",
     "tiempo": null,
     "ubicaciones": {
      "tradicional": {
       "lat": 30.2252,
       "lon": 32.4695,
       "confianza": "media",
       "identificacion": "plain near Jabal Jinayfah",
       "puntuacion_openbible": 103,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Pi-hahiroth → plain near Jabal Jinayfah",
       "url": "https://www.openbible.info/geo/ancient/ababfd2/pi-hahiroth"
      },
      "sin-bishar": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Biblical Mount Sinai» (Har-El y Jebel Sin Bishar); coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Biblical_Mount_Sinai"
      },
      "har-karkom": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Har Karkom» y «Biblical Mount Sinai»; E. Anati, The Riddle of Mount Sinai (2001); coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Har_Karkom"
      },
      "al-lawz": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Jabal al-Lawz» y «Biblical Mount Sinai»; coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Jabal_al-Lawz"
      }
     },
     "nota": "Entre Migdol y el mar, frente a Baal-zefón. OpenBible da casi el mismo peso a otras propuestas (p. ej. Tell Defenneh, que identifica con Baal-zefón). Sin ubicación propuesta en: Sinaí en Jebel Sin Bishar (oeste-centro del Sinaí); Sinaí en Har Karkom (Négueb); Sinaí en Jabal al-Lawz, Arabia (minoritaria)."
    },
    {
     "orden": 5,
     "lugar": "mar-rojo",
     "nombre": "Cruce del mar",
     "ref": "Ex 14:22",
     "cita": "Entonces los hijos de Israel entraron por medio de la mar en seco",
     "tiempo": {
      "texto": "De noche",
      "dia": null,
      "certeza": "texto",
      "pasos": [
       {
        "texto": "El viento sopla «toda aquella noche».",
        "ref": "Ex 14:21",
        "cita": "por recio viento oriental toda aquella noche"
       }
      ]
     },
     "ubicaciones": {
      "tradicional": {
       "lat": 30.3383,
       "lon": 32.3778,
       "confianza": "media",
       "identificacion": "Bitter Lakes",
       "puntuacion_openbible": 304,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Red Sea 1 → Bitter Lakes",
       "url": "https://www.openbible.info/geo/ancient/a3d18b2/red-sea-1"
      },
      "sin-bishar": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Biblical Mount Sinai» (Har-El y Jebel Sin Bishar); coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Biblical_Mount_Sinai"
      },
      "har-karkom": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Har Karkom» y «Biblical Mount Sinai»; E. Anati, The Riddle of Mount Sinai (2001); coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Har_Karkom"
      },
      "al-lawz": {
       "lat": 28.75,
       "lon": 34.75,
       "confianza": "baja",
       "identificacion": "Gulf of Aqaba",
       "puntuacion_openbible": 62,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Red Sea 1 → Gulf of Aqaba",
       "url": "https://www.openbible.info/geo/ancient/a3d18b2/red-sea-1"
      }
     },
     "nota": "Ex 14 dice «la mar»; Ex 15:4 lo llama «mar Bermejo» (yam suf). La identificación mejor puntuada de OpenBible es el golfo de Suez (369), pero su punto es el centro del golfo, unos 170 km al sur de Pi-hahirot; para la ruta tradicional se toma la segunda, los lagos Amargos (304). Esta elección es inferida. Otras propuestas en OpenBible: lago Timsah, lagos de Ballah, lago Manzala, lago Bardawil (Sirbonis). Sin ubicación propuesta en: Sinaí en Jebel Sin Bishar (oeste-centro del Sinaí); Sinaí en Har Karkom (Négueb). Alguna identificación va con confianza baja (dudosa)."
    },
    {
     "orden": 6,
     "lugar": "shur",
     "nombre": "Desierto de Shur",
     "ref": "Ex 15:22",
     "cita": "salieron al desierto de Shur",
     "tiempo": null,
     "ubicaciones": {
      "tradicional": {
       "lat": 30.4933,
       "lon": 32.9567,
       "confianza": "alta",
       "identificacion": "Ar Ruwaysat",
       "puntuacion_openbible": 554,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Shur → Ar Ruwaysat",
       "url": "https://www.openbible.info/geo/ancient/acdbce0/shur"
      },
      "sin-bishar": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Biblical Mount Sinai» (Har-El y Jebel Sin Bishar); coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Biblical_Mount_Sinai"
      },
      "har-karkom": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Har Karkom» y «Biblical Mount Sinai»; E. Anati, The Riddle of Mount Sinai (2001); coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Har_Karkom"
      },
      "al-lawz": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Jabal al-Lawz» y «Biblical Mount Sinai»; coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Jabal_al-Lawz"
      }
     },
     "nota": "Región; el punto es representativo. Sin ubicación propuesta en: Sinaí en Jebel Sin Bishar (oeste-centro del Sinaí); Sinaí en Har Karkom (Négueb); Sinaí en Jabal al-Lawz, Arabia (minoritaria)."
    },
    {
     "orden": 7,
     "lugar": "mara",
     "nombre": "Mara",
     "ref": "Ex 15:23",
     "cita": "Y llegaron á Mara",
     "tiempo": {
      "texto": "Tres días después de dejar el mar",
      "dia": null,
      "certeza": "calculo",
      "pasos": [
       {
        "texto": "Caminan tres días sin agua desde el mar Bermejo.",
        "ref": "Ex 15:22",
        "cita": "anduvieron tres días por el desierto sin hallar agua"
       },
       {
        "texto": "Al terminar ese camino llegan a Mara.",
        "ref": "Ex 15:23",
        "cita": "Y llegaron á Mara"
       }
      ]
     },
     "ubicaciones": {
      "tradicional": {
       "lat": 29.346,
       "lon": 32.9428,
       "confianza": "media",
       "identificacion": "Ain Hawarah",
       "puntuacion_openbible": 384,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Marah → Ain Hawarah",
       "url": "https://www.openbible.info/geo/ancient/ad3970d/marah"
      },
      "sin-bishar": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Biblical Mount Sinai» (Har-El y Jebel Sin Bishar); coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Biblical_Mount_Sinai"
      },
      "har-karkom": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Har Karkom» y «Biblical Mount Sinai»; E. Anati, The Riddle of Mount Sinai (2001); coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Har_Karkom"
      },
      "al-lawz": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Jabal al-Lawz» y «Biblical Mount Sinai»; coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Jabal_al-Lawz"
      }
     },
     "nota": "Aguas amargas. Sin ubicación propuesta en: Sinaí en Jebel Sin Bishar (oeste-centro del Sinaí); Sinaí en Har Karkom (Négueb); Sinaí en Jabal al-Lawz, Arabia (minoritaria)."
    },
    {
     "orden": 8,
     "lugar": "elim",
     "nombre": "Elim",
     "ref": "Ex 15:27",
     "cita": "Y llegaron á Elim, donde había doce fuentes de aguas, y setenta palmas",
     "tiempo": null,
     "ubicaciones": {
      "tradicional": {
       "lat": 29.2547,
       "lon": 32.9158,
       "confianza": "alta",
       "identificacion": "Wadi Gharandal",
       "puntuacion_openbible": 533,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Elim → Wadi Gharandal",
       "url": "https://www.openbible.info/geo/ancient/a2410c1/elim"
      },
      "sin-bishar": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Biblical Mount Sinai» (Har-El y Jebel Sin Bishar); coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Biblical_Mount_Sinai"
      },
      "har-karkom": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Har Karkom» y «Biblical Mount Sinai»; E. Anati, The Riddle of Mount Sinai (2001); coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Har_Karkom"
      },
      "al-lawz": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Jabal al-Lawz» y «Biblical Mount Sinai»; coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Jabal_al-Lawz"
      }
     },
     "nota": "Sin ubicación propuesta en: Sinaí en Jebel Sin Bishar (oeste-centro del Sinaí); Sinaí en Har Karkom (Négueb); Sinaí en Jabal al-Lawz, Arabia (minoritaria)."
    },
    {
     "orden": 9,
     "lugar": "desierto-de-sin",
     "nombre": "Desierto de Sin",
     "ref": "Ex 16:1",
     "cita": "vino al desierto de Sin, que está entre Elim y Sinaí",
     "tiempo": {
      "texto": "Mes segundo, día 15",
      "mes": 2,
      "dia": 15,
      "certeza": "texto",
      "pasos": [
       {
        "texto": "Llegan «á los quince días del segundo mes» desde la salida de Egipto.",
        "ref": "Ex 16:1",
        "cita": "á los quince días del segundo mes después que salieron de la tierra de Egipto"
       }
      ]
     },
     "ubicaciones": {
      "tradicional": {
       "lat": 29.1478,
       "lon": 33.5367,
       "confianza": "media",
       "identificacion": "Debbet er Ramleh",
       "puntuacion_openbible": 311,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Sin → Debbet er Ramleh",
       "url": "https://www.openbible.info/geo/ancient/a0f54e4/sin"
      },
      "sin-bishar": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Biblical Mount Sinai» (Har-El y Jebel Sin Bishar); coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Biblical_Mount_Sinai"
      },
      "har-karkom": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Har Karkom» y «Biblical Mount Sinai»; E. Anati, The Riddle of Mount Sinai (2001); coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Har_Karkom"
      },
      "al-lawz": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Jabal al-Lawz» y «Biblical Mount Sinai»; coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Jabal_al-Lawz"
      }
     },
     "nota": "Región; el punto es representativo. Sin ubicación propuesta en: Sinaí en Jebel Sin Bishar (oeste-centro del Sinaí); Sinaí en Har Karkom (Négueb); Sinaí en Jabal al-Lawz, Arabia (minoritaria)."
    },
    {
     "orden": 10,
     "lugar": "refidim",
     "nombre": "Refidim",
     "ref": "Ex 17:1",
     "cita": "asentaron el campo en Rephidim",
     "tiempo": null,
     "ubicaciones": {
      "tradicional": {
       "lat": 28.6231,
       "lon": 33.8803,
       "confianza": "media",
       "identificacion": "Wadi Rufaiyil",
       "puntuacion_openbible": 379,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Rephidim → Wadi Rufaiyil",
       "url": "https://www.openbible.info/geo/ancient/a05ebb7/rephidim"
      },
      "sin-bishar": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Biblical Mount Sinai» (Har-El y Jebel Sin Bishar); coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Biblical_Mount_Sinai"
      },
      "har-karkom": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Har Karkom» y «Biblical Mount Sinai»; E. Anati, The Riddle of Mount Sinai (2001); coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Har_Karkom"
      },
      "al-lawz": {
       "lat": null,
       "lon": null,
       "confianza": "baja",
       "identificacion": "Sin identificación propuesta en esta hipótesis",
       "fuente": "Wikipedia, «Jabal al-Lawz» y «Biblical Mount Sinai»; coordenadas: OpenBible.info",
       "url": "https://en.wikipedia.org/wiki/Jabal_al-Lawz"
      }
     },
     "nota": "Aquí sitúa el texto el agua de la peña y la batalla con Amalec (Ex 17). Sin ubicación propuesta en: Sinaí en Jebel Sin Bishar (oeste-centro del Sinaí); Sinaí en Har Karkom (Négueb); Sinaí en Jabal al-Lawz, Arabia (minoritaria)."
    },
    {
     "orden": 11,
     "lugar": "desierto-de-sinai",
     "nombre": "Desierto y monte Sinaí",
     "ref": "Ex 19:1",
     "cita": "vinieron al desierto de Sinaí",
     "tiempo": {
      "texto": "Mes tercero",
      "mes": 3,
      "dia": null,
      "certeza": "texto",
      "pasos": [
       {
        "texto": "Llegan «al mes tercero» de la salida, «en aquel día» (el texto no precisa el día).",
        "ref": "Ex 19:1",
        "cita": "AL mes tercero de la salida de los hijos de Israel de la tierra de Egipto"
       }
      ]
     },
     "ubicaciones": {
      "tradicional": {
       "lat": 28.5397,
       "lon": 33.9733,
       "confianza": "baja",
       "identificacion": "Jebel Musa",
       "puntuacion_openbible": 465,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Mount Sinai → Jebel Musa",
       "url": "https://www.openbible.info/geo/ancient/abfba2a/mount-sinai"
      },
      "sin-bishar": {
       "lat": 29.671,
       "lon": 32.961,
       "confianza": "baja",
       "identificacion": "Jebel Sin Bishar",
       "puntuacion_openbible": 89,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Mount Sinai → Jebel Sin Bishar",
       "url": "https://www.openbible.info/geo/ancient/abfba2a/mount-sinai"
      },
      "har-karkom": {
       "lat": 30.2833,
       "lon": 34.75,
       "confianza": "baja",
       "identificacion": "Har Karkom",
       "puntuacion_openbible": 103,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Mount Sinai → Har Karkom",
       "url": "https://www.openbible.info/geo/ancient/abfba2a/mount-sinai"
      },
      "al-lawz": {
       "lat": 28.6542,
       "lon": 35.3058,
       "confianza": "baja",
       "identificacion": "Jabal al Lawz",
       "puntuacion_openbible": 4,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Mount Sinai → Jabal al Lawz",
       "url": "https://www.openbible.info/geo/ancient/abfba2a/mount-sinai"
      }
     },
     "nota": "Ex 19:2: «acampó allí Israel delante del monte». Las coordenadas son las del monte Sinaí en OpenBible; no hay consenso y todas van con confianza baja."
    }
   ]
  },
  {
   "id": "abraham",
   "titulo": "Los caminos de Abraham",
   "libro": "Gn",
   "personas": [
    "Terah_1",
    "Abram_1",
    "Sarai_1",
    "Lot_1"
   ],
   "resumen": "De Ur de los caldeos a Harán, Canaán, Egipto y de vuelta al Négueb y Hebrón (Gn 11–25), con dos hipótesis sobre Ur.",
   "hipotesis": [
    {
     "id": "ur-sur",
     "nombre": "Ur del sur (Tell el-Muqayyar, Irak)",
     "defecto": true,
     "descripcion": "Identificación de H. Rawlinson (1862), excavada por L. Woolley; es la opinión académica mayoritaria. Fuente externa.",
     "fuente": "Wikipedia, «Ur Kaśdim»; coordenadas: OpenBible.info",
     "url": "https://en.wikipedia.org/wiki/Ur_Ka%C5%9Bdim"
    },
    {
     "id": "ur-norte",
     "nombre": "Ur del norte (Urfa / Şanlıurfa, Turquía)",
     "defecto": false,
     "minoritaria": true,
     "descripcion": "Tradición judía e islámica que sitúa a Abraham en Urfa (la antigua Edesa), cerca de Harán; apoyo académico minoritario (p. ej. G. Rendsburg, 2019). Solo cambia la primera etapa. Fuente externa.",
     "fuente": "Wikipedia, «Ur Kaśdim»; coordenadas: OpenBible.info",
     "url": "https://en.wikipedia.org/wiki/Ur_Ka%C5%9Bdim"
    }
   ],
   "etapas": [
    {
     "orden": 1,
     "lugar": "ur",
     "nombre": "Ur de los caldeos",
     "ref": "Gn 11:31",
     "cita": "salió con ellos de Ur de los Caldeos",
     "tiempo": null,
     "ubicaciones": {
      "ur-sur": {
       "lat": 30.9622,
       "lon": 46.1044,
       "confianza": "alta",
       "identificacion": "Tell el Muqayyar",
       "puntuacion_openbible": 703,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Ur 1 → Tell el Muqayyar",
       "url": "https://www.openbible.info/geo/ancient/a6cf75c/ur-1"
      },
      "ur-norte": {
       "lat": 37.1478,
       "lon": 38.7844,
       "confianza": "baja",
       "identificacion": "Urfa",
       "puntuacion_openbible": 53,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Ur 1 → Urfa",
       "url": "https://www.openbible.info/geo/ancient/a6cf75c/ur-1"
      }
     },
     "nota": "Sale Taré con Abram, Sarai y Lot. Alguna identificación va con confianza baja (dudosa)."
    },
    {
     "orden": 2,
     "lugar": "haran",
     "nombre": "Harán",
     "ref": "Gn 11:31",
     "cita": "y vinieron hasta Harán, y asentaron allí",
     "tiempo": {
      "texto": "Abram sale de Harán a los 75 años",
      "dia": null,
      "certeza": "texto",
      "pasos": [
       {
        "texto": "Taré muere en Harán a los 205 años.",
        "ref": "Gn 11:32",
        "cita": "murió Thare en Harán"
       },
       {
        "texto": "Abram tiene 75 años al salir de Harán.",
        "ref": "Gn 12:4",
        "cita": "era Abram de edad de setenta y cinco años cuando salió de Harán"
       }
      ]
     },
     "ubicaciones": {
      "ur-sur": {
       "lat": 36.8644,
       "lon": 39.0328,
       "confianza": "alta",
       "identificacion": "Harran",
       "puntuacion_openbible": 922,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Haran → Harran",
       "url": "https://www.openbible.info/geo/ancient/a6d9af3/haran"
      },
      "ur-norte": {
       "lat": 36.8644,
       "lon": 39.0328,
       "confianza": "alta",
       "identificacion": "Harran (común a todas las hipótesis)",
       "puntuacion_openbible": 922,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Haran → Harran",
       "url": "https://www.openbible.info/geo/ancient/a6d9af3/haran"
      }
     },
     "nota": ""
    },
    {
     "orden": 3,
     "lugar": "siquem",
     "nombre": "Siquem, valle de More",
     "ref": "Gn 12:6",
     "cita": "hasta el lugar de Sichêm, hasta el valle de Moreh",
     "tiempo": null,
     "ubicaciones": {
      "ur-sur": {
       "lat": 32.2136,
       "lon": 35.2819,
       "confianza": "alta",
       "identificacion": "Tell Balatah",
       "puntuacion_openbible": 1000,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Shechem → Tell Balatah",
       "url": "https://www.openbible.info/geo/ancient/adf74d4/shechem"
      },
      "ur-norte": {
       "lat": 32.2136,
       "lon": 35.2819,
       "confianza": "alta",
       "identificacion": "Tell Balatah (común a todas las hipótesis)",
       "puntuacion_openbible": 1000,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Shechem → Tell Balatah",
       "url": "https://www.openbible.info/geo/ancient/adf74d4/shechem"
      }
     },
     "nota": "Primera parada en Canaán."
    },
    {
     "orden": 4,
     "lugar": "betel",
     "nombre": "Entre Betel y Hai",
     "ref": "Gn 12:8",
     "cita": "á un monte al oriente de Bethel",
     "tiempo": null,
     "ubicaciones": {
      "ur-sur": {
       "lat": 31.9228,
       "lon": 35.2414,
       "confianza": "alta",
       "identificacion": "Beitin",
       "puntuacion_openbible": 716,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Bethel 1 → Beitin",
       "url": "https://www.openbible.info/geo/ancient/a64f355/bethel-1"
      },
      "ur-norte": {
       "lat": 31.9228,
       "lon": 35.2414,
       "confianza": "alta",
       "identificacion": "Beitin (común a todas las hipótesis)",
       "puntuacion_openbible": 716,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Bethel 1 → Beitin",
       "url": "https://www.openbible.info/geo/ancient/a64f355/bethel-1"
      }
     },
     "nota": "El texto dice «teniendo á Bethel al occidente y Hai al oriente»; el punto es el de Betel."
    },
    {
     "orden": 5,
     "lugar": null,
     "nombre": "Négueb («el Mediodía»)",
     "ref": "Gn 12:9",
     "cita": "caminando y yendo hacia el Mediodía",
     "tiempo": null,
     "ubicaciones": {
      "ur-sur": {
       "lat": 31.2447,
       "lon": 34.8408,
       "confianza": "alta",
       "identificacion": "Tel Beer Sheva",
       "puntuacion_openbible": 823,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Negeb → Tel Beer Sheva",
       "url": "https://www.openbible.info/geo/ancient/a1cb244/negeb"
      },
      "ur-norte": {
       "lat": 31.2447,
       "lon": 34.8408,
       "confianza": "alta",
       "identificacion": "Tel Beer Sheva (común a todas las hipótesis)",
       "puntuacion_openbible": 823,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Negeb → Tel Beer Sheva",
       "url": "https://www.openbible.info/geo/ancient/a1cb244/negeb"
      }
     },
     "nota": "La RV1909 dice «el Mediodía» (el Négueb). No está en la lista de lugares de la aplicación; el punto es el que OpenBible usa para representar la región (coincide con Beerseba)."
    },
    {
     "orden": 6,
     "lugar": "egipto",
     "nombre": "Egipto",
     "ref": "Gn 12:10",
     "cita": "descendió Abram á Egipto",
     "tiempo": null,
     "ubicaciones": {
      "ur-sur": {
       "lat": 30.1294,
       "lon": 31.3075,
       "confianza": "alta",
       "identificacion": "Ain Shams",
       "puntuacion_openbible": 1000,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Egypt → Ain Shams",
       "url": "https://www.openbible.info/geo/ancient/af301ca/egypt"
      },
      "ur-norte": {
       "lat": 30.1294,
       "lon": 31.3075,
       "confianza": "alta",
       "identificacion": "Ain Shams (común a todas las hipótesis)",
       "puntuacion_openbible": 1000,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Egypt → Ain Shams",
       "url": "https://www.openbible.info/geo/ancient/af301ca/egypt"
      }
     },
     "nota": "País: el punto es el representativo de OpenBible (On/Heliópolis); el texto no dice a qué ciudad fue."
    },
    {
     "orden": 7,
     "lugar": "betel",
     "nombre": "Regreso a Betel",
     "ref": "Gn 13:3",
     "cita": "hasta el lugar donde había estado antes su tienda entre Bethel y Hai",
     "tiempo": null,
     "ubicaciones": {
      "ur-sur": {
       "lat": 31.9228,
       "lon": 35.2414,
       "confianza": "alta",
       "identificacion": "Beitin",
       "puntuacion_openbible": 716,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Bethel 1 → Beitin",
       "url": "https://www.openbible.info/geo/ancient/a64f355/bethel-1"
      },
      "ur-norte": {
       "lat": 31.9228,
       "lon": 35.2414,
       "confianza": "alta",
       "identificacion": "Beitin (común a todas las hipótesis)",
       "puntuacion_openbible": 716,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Bethel 1 → Beitin",
       "url": "https://www.openbible.info/geo/ancient/a64f355/bethel-1"
      }
     },
     "nota": ""
    },
    {
     "orden": 8,
     "lugar": "mamre",
     "nombre": "Mamre, en Hebrón",
     "ref": "Gn 13:18",
     "cita": "moró en el alcornocal de Mamre, que es en Hebrón",
     "tiempo": null,
     "ubicaciones": {
      "ur-sur": {
       "lat": 31.5565,
       "lon": 35.1053,
       "confianza": "alta",
       "identificacion": "Ramat el Khalil",
       "puntuacion_openbible": 667,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Mamre → Ramat el Khalil",
       "url": "https://www.openbible.info/geo/ancient/aeb9e97/mamre"
      },
      "ur-norte": {
       "lat": 31.5565,
       "lon": 35.1053,
       "confianza": "alta",
       "identificacion": "Ramat el Khalil (común a todas las hipótesis)",
       "puntuacion_openbible": 667,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Mamre → Ramat el Khalil",
       "url": "https://www.openbible.info/geo/ancient/aeb9e97/mamre"
      }
     },
     "nota": ""
    },
    {
     "orden": 9,
     "lugar": "gerar",
     "nombre": "Gerar",
     "ref": "Gn 20:1",
     "cita": "habitó como forastero en Gerar",
     "tiempo": null,
     "ubicaciones": {
      "ur-sur": {
       "lat": 31.3821,
       "lon": 34.6065,
       "confianza": "alta",
       "identificacion": "Tel Haror",
       "puntuacion_openbible": 694,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Gerar → Tel Haror",
       "url": "https://www.openbible.info/geo/ancient/a3f5814/gerar"
      },
      "ur-norte": {
       "lat": 31.3821,
       "lon": 34.6065,
       "confianza": "alta",
       "identificacion": "Tel Haror (común a todas las hipótesis)",
       "puntuacion_openbible": 694,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Gerar → Tel Haror",
       "url": "https://www.openbible.info/geo/ancient/a3f5814/gerar"
      }
     },
     "nota": "«Entre Cades y Shur»."
    },
    {
     "orden": 10,
     "lugar": "beerseba",
     "nombre": "Beerseba",
     "ref": "Gn 21:33",
     "cita": "Y plantó [Abraham] un bosque en Beer-seba",
     "tiempo": null,
     "ubicaciones": {
      "ur-sur": {
       "lat": 31.2447,
       "lon": 34.8408,
       "confianza": "media",
       "identificacion": "Tel Beer Sheva",
       "puntuacion_openbible": 334,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Beersheba 2 → Tel Beer Sheva",
       "url": "https://www.openbible.info/geo/ancient/a075d61/beersheba-2"
      },
      "ur-norte": {
       "lat": 31.2447,
       "lon": 34.8408,
       "confianza": "media",
       "identificacion": "Tel Beer Sheva (común a todas las hipótesis)",
       "puntuacion_openbible": 334,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Beersheba 2 → Tel Beer Sheva",
       "url": "https://www.openbible.info/geo/ancient/a075d61/beersheba-2"
      }
     },
     "nota": "El nombre del lugar se explica en Gn 21:31."
    },
    {
     "orden": 11,
     "lugar": "moriah",
     "nombre": "Tierra de Moriah",
     "ref": "Gn 22:2",
     "cita": "vete á tierra de Moriah",
     "tiempo": null,
     "ubicaciones": {
      "ur-sur": {
       "lat": 31.7778,
       "lon": 35.2356,
       "confianza": "media",
       "identificacion": "Mount Moriah",
       "puntuacion_openbible": 325,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Moriah → Mount Moriah",
       "url": "https://www.openbible.info/geo/ancient/adaf385/moriah"
      },
      "ur-norte": {
       "lat": 31.7778,
       "lon": 35.2356,
       "confianza": "media",
       "identificacion": "Mount Moriah (común a todas las hipótesis)",
       "puntuacion_openbible": 325,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Moriah → Mount Moriah",
       "url": "https://www.openbible.info/geo/ancient/adaf385/moriah"
      }
     },
     "nota": "El texto no dice qué monte; la identificación con el monte del templo de Jerusalén es tradicional (OpenBible, confianza media)."
    },
    {
     "orden": 12,
     "lugar": "beerseba",
     "nombre": "Regreso a Beerseba",
     "ref": "Gn 22:19",
     "cita": "y habitó Abraham en Beer-seba",
     "tiempo": null,
     "ubicaciones": {
      "ur-sur": {
       "lat": 31.2447,
       "lon": 34.8408,
       "confianza": "media",
       "identificacion": "Tel Beer Sheva",
       "puntuacion_openbible": 334,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Beersheba 2 → Tel Beer Sheva",
       "url": "https://www.openbible.info/geo/ancient/a075d61/beersheba-2"
      },
      "ur-norte": {
       "lat": 31.2447,
       "lon": 34.8408,
       "confianza": "media",
       "identificacion": "Tel Beer Sheva (común a todas las hipótesis)",
       "puntuacion_openbible": 334,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Beersheba 2 → Tel Beer Sheva",
       "url": "https://www.openbible.info/geo/ancient/a075d61/beersheba-2"
      }
     },
     "nota": ""
    },
    {
     "orden": 13,
     "lugar": "hebron",
     "nombre": "Hebrón (Quiriat-arba)",
     "ref": "Gn 23:2",
     "cita": "murió Sara en Kiriath-arba, que es Hebrón",
     "tiempo": null,
     "ubicaciones": {
      "ur-sur": {
       "lat": 31.5251,
       "lon": 35.1022,
       "confianza": "alta",
       "identificacion": "Tel Rumeida",
       "puntuacion_openbible": 1000,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Hebron → Tel Rumeida",
       "url": "https://www.openbible.info/geo/ancient/a85151a/hebron"
      },
      "ur-norte": {
       "lat": 31.5251,
       "lon": 35.1022,
       "confianza": "alta",
       "identificacion": "Tel Rumeida (común a todas las hipótesis)",
       "puntuacion_openbible": 1000,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Hebron → Tel Rumeida",
       "url": "https://www.openbible.info/geo/ancient/a85151a/hebron"
      }
     },
     "nota": "Muere Sara; Abraham compra la cueva de Macpela (Gn 23)."
    },
    {
     "orden": 14,
     "lugar": "macpela",
     "nombre": "Cueva de Macpela",
     "ref": "Gn 25:9",
     "cita": "en la cueva de Macpela",
     "tiempo": {
      "texto": "Abraham muere a los 175 años",
      "dia": null,
      "certeza": "texto",
      "pasos": [
       {
        "texto": "Edad de Abraham al morir.",
        "ref": "Gn 25:7",
        "cita": "ciento setenta y cinco años"
       }
      ]
     },
     "ubicaciones": {
      "ur-sur": {
       "lat": 31.5247,
       "lon": 35.1108,
       "confianza": "alta",
       "identificacion": "Cave of the Patriarchs",
       "puntuacion_openbible": 1000,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Machpelah → Cave of the Patriarchs",
       "url": "https://www.openbible.info/geo/ancient/ae00861/machpelah"
      },
      "ur-norte": {
       "lat": 31.5247,
       "lon": 35.1108,
       "confianza": "alta",
       "identificacion": "Cave of the Patriarchs (común a todas las hipótesis)",
       "puntuacion_openbible": 1000,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Machpelah → Cave of the Patriarchs",
       "url": "https://www.openbible.info/geo/ancient/ae00861/machpelah"
      }
     },
     "nota": "Lo sepultan Isaac e Ismael «enfrente de Mamre»."
    }
   ]
  },
  {
   "id": "jacob",
   "titulo": "Los viajes de Jacob",
   "libro": "Gn",
   "personas": [
    "Jacob_1",
    "Leah_1",
    "Rachel_1"
   ],
   "resumen": "De Beerseba a Harán y vuelta a Canaán por Galaad, Peniel y Siquem; después Betel, Belén, Hebrón y la bajada a Gosén (Gn 28–46).",
   "hipotesis": [
    {
     "id": "openbible",
     "nombre": "Identificaciones mejor puntuadas de OpenBible",
     "defecto": true,
     "descripcion": "Una sola hipótesis: en cada lugar, la identificación moderna con mayor puntuación en OpenBible (la misma que usa el mapa de la aplicación). Fuente externa.",
     "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0)",
     "url": "https://www.openbible.info/geo/"
    }
   ],
   "etapas": [
    {
     "orden": 1,
     "lugar": "beerseba",
     "nombre": "Beerseba",
     "ref": "Gn 28:10",
     "cita": "Y salió Jacob de Beer-seba, y fué á Harán",
     "tiempo": null,
     "ubicaciones": {
      "openbible": {
       "lat": 31.2447,
       "lon": 34.8408,
       "confianza": "media",
       "identificacion": "Tel Beer Sheva",
       "puntuacion_openbible": 334,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Beersheba 2 → Tel Beer Sheva",
       "url": "https://www.openbible.info/geo/ancient/a075d61/beersheba-2"
      }
     },
     "nota": ""
    },
    {
     "orden": 2,
     "lugar": "betel",
     "nombre": "Betel",
     "ref": "Gn 28:19",
     "cita": "llamó el nombre de aquel lugar Beth-el",
     "tiempo": null,
     "ubicaciones": {
      "openbible": {
       "lat": 31.9228,
       "lon": 35.2414,
       "confianza": "alta",
       "identificacion": "Beitin",
       "puntuacion_openbible": 716,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Bethel 1 → Beitin",
       "url": "https://www.openbible.info/geo/ancient/a64f355/bethel-1"
      }
     },
     "nota": "El sueño de la escalera; antes se llamaba Luz."
    },
    {
     "orden": 3,
     "lugar": "haran",
     "nombre": "Harán",
     "ref": "Gn 29:4",
     "cita": "De Harán somos",
     "tiempo": null,
     "ubicaciones": {
      "openbible": {
       "lat": 36.8644,
       "lon": 39.0328,
       "confianza": "alta",
       "identificacion": "Harran",
       "puntuacion_openbible": 922,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Haran → Harran",
       "url": "https://www.openbible.info/geo/ancient/a6d9af3/haran"
      }
     },
     "nota": "Jacob sirve a Labán; se casa con Lea y Raquel."
    },
    {
     "orden": 4,
     "lugar": "galaad",
     "nombre": "Monte de Galaad",
     "ref": "Gn 31:21",
     "cita": "puso su rostro al monte de Galaad",
     "tiempo": {
      "texto": "Tras veinte años en casa de Labán",
      "dia": null,
      "certeza": "texto",
      "pasos": [
       {
        "texto": "Jacob dice a Labán cuánto tiempo le sirvió.",
        "ref": "Gn 31:41",
        "cita": "Así he estado veinte años en tu casa"
       }
      ]
     },
     "ubicaciones": {
      "openbible": {
       "lat": 32.187,
       "lon": 35.6921,
       "confianza": "alta",
       "identificacion": "Tell edh Dhahab esh Sherqiyeh",
       "puntuacion_openbible": 694,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Gilead 1 → Tell edh Dhahab esh Sherqiyeh",
       "url": "https://www.openbible.info/geo/ancient/ae73b90/gilead-1"
      }
     },
     "nota": "Labán lo alcanza allí (Gn 31:25). Región: el punto es representativo."
    },
    {
     "orden": 5,
     "lugar": "mahanaim",
     "nombre": "Mahanaim",
     "ref": "Gn 32:2",
     "cita": "llamó el nombre de aquel lugar Mahanaim",
     "tiempo": null,
     "ubicaciones": {
      "openbible": {
       "lat": 32.1857,
       "lon": 35.6867,
       "confianza": "alta",
       "identificacion": "Tell edh Dhahab el Gharbi",
       "puntuacion_openbible": 654,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Mahanaim → Tell edh Dhahab el Gharbi",
       "url": "https://www.openbible.info/geo/ancient/ae5bfe9/mahanaim"
      }
     },
     "nota": ""
    },
    {
     "orden": 6,
     "lugar": "peniel",
     "nombre": "Peniel",
     "ref": "Gn 32:30",
     "cita": "Y llamó Jacob el nombre de aquel lugar, Peniel",
     "tiempo": null,
     "ubicaciones": {
      "openbible": {
       "lat": 32.187,
       "lon": 35.6921,
       "confianza": "alta",
       "identificacion": "Tell edh Dhahab esh Sherqiyeh",
       "puntuacion_openbible": 694,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Penuel → Tell edh Dhahab esh Sherqiyeh",
       "url": "https://www.openbible.info/geo/ancient/a8a9ff9/penuel"
      }
     },
     "nota": "Junto al vado de Jaboc (Gn 32:22). OpenBible usa el mismo punto para Galaad."
    },
    {
     "orden": 7,
     "lugar": "sucot",
     "nombre": "Sucot",
     "ref": "Gn 33:17",
     "cita": "Y Jacob se partió á Succoth",
     "tiempo": null,
     "ubicaciones": {
      "openbible": {
       "lat": 32.1966,
       "lon": 35.6212,
       "confianza": "alta",
       "identificacion": "Tell Deir Alla",
       "puntuacion_openbible": 600,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Succoth 1 → Tell Deir Alla",
       "url": "https://www.openbible.info/geo/ancient/a0905b5/succoth-1"
      }
     },
     "nota": "Al este del Jordán; distinta de Sucot de Ex 12:37."
    },
    {
     "orden": 8,
     "lugar": "siquem",
     "nombre": "Siquem",
     "ref": "Gn 33:18",
     "cita": "Y vino Jacob sano á la ciudad de Sichêm",
     "tiempo": null,
     "ubicaciones": {
      "openbible": {
       "lat": 32.2136,
       "lon": 35.2819,
       "confianza": "alta",
       "identificacion": "Tell Balatah",
       "puntuacion_openbible": 1000,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Shechem → Tell Balatah",
       "url": "https://www.openbible.info/geo/ancient/adf74d4/shechem"
      }
     },
     "nota": ""
    },
    {
     "orden": 9,
     "lugar": "betel",
     "nombre": "Betel",
     "ref": "Gn 35:6",
     "cita": "Y llegó Jacob á Luz",
     "tiempo": null,
     "ubicaciones": {
      "openbible": {
       "lat": 31.9228,
       "lon": 35.2414,
       "confianza": "alta",
       "identificacion": "Beitin",
       "puntuacion_openbible": 716,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Bethel 1 → Beitin",
       "url": "https://www.openbible.info/geo/ancient/a64f355/bethel-1"
      }
     },
     "nota": "«esta es Beth-el»."
    },
    {
     "orden": 10,
     "lugar": "efrata",
     "nombre": "Efrata (Belén)",
     "ref": "Gn 35:19",
     "cita": "en el camino de Ephrata, la cual es Beth-lehem",
     "tiempo": null,
     "ubicaciones": {
      "openbible": {
       "lat": 31.7043,
       "lon": 35.2076,
       "confianza": "alta",
       "identificacion": "Bethlehem",
       "puntuacion_openbible": 1000,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Ephrath → Bethlehem",
       "url": "https://www.openbible.info/geo/ancient/af4e985/ephrath"
      }
     },
     "nota": "Muere Raquel al dar a luz a Benjamín."
    },
    {
     "orden": 11,
     "lugar": "mamre",
     "nombre": "Mamre, Hebrón",
     "ref": "Gn 35:27",
     "cita": "Y vino Jacob á Isaac su padre á Mamre",
     "tiempo": null,
     "ubicaciones": {
      "openbible": {
       "lat": 31.5565,
       "lon": 35.1053,
       "confianza": "alta",
       "identificacion": "Ramat el Khalil",
       "puntuacion_openbible": 667,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Mamre → Ramat el Khalil",
       "url": "https://www.openbible.info/geo/ancient/aeb9e97/mamre"
      }
     },
     "nota": "«á la ciudad de Arba, que es Hebrón»."
    },
    {
     "orden": 12,
     "lugar": "beerseba",
     "nombre": "Beerseba",
     "ref": "Gn 46:1",
     "cita": "vino á Beer-seba",
     "tiempo": null,
     "ubicaciones": {
      "openbible": {
       "lat": 31.2447,
       "lon": 34.8408,
       "confianza": "media",
       "identificacion": "Tel Beer Sheva",
       "puntuacion_openbible": 334,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Beersheba 2 → Tel Beer Sheva",
       "url": "https://www.openbible.info/geo/ancient/a075d61/beersheba-2"
      }
     },
     "nota": "Camino de Egipto."
    },
    {
     "orden": 13,
     "lugar": "gosen",
     "nombre": "Gosén, en Egipto",
     "ref": "Gn 46:28",
     "cita": "y llegaron á la tierra de Gosén",
     "tiempo": {
      "texto": "Jacob tiene 130 años ante Faraón",
      "dia": null,
      "certeza": "texto",
      "pasos": [
       {
        "texto": "Entran en Egipto.",
        "ref": "Gn 46:6",
        "cita": "viniéronse á Egipto"
       },
       {
        "texto": "Jacob dice su edad a Faraón.",
        "ref": "Gn 47:9",
        "cita": "ciento treinta años"
       }
      ]
     },
     "ubicaciones": {
      "openbible": {
       "lat": 30.7994,
       "lon": 31.8342,
       "confianza": "alta",
       "identificacion": "Qantir",
       "puntuacion_openbible": 519,
       "fuente": "OpenBible.info, Bible Geocoding Data (CC BY 4.0): Goshen 1 → Qantir",
       "url": "https://www.openbible.info/geo/ancient/a60f092/goshen-1"
      }
     },
     "nota": "Región: el punto es representativo."
    }
   ]
  }
 ]
};
