/* EJEMPLO — datos de prueba para la vista «Tabernáculo» (se activan con ?ejemplo o ?tabernaculo-ejemplo si no hay datos/tabernaculo.js).
   Las posiciones del plano son SOLO DE PRUEBA y siguen la disposición habitual de las reconstrucciones: no son datos del texto.
   Las citas son de la RV1909 (dominio público). El contrato real lo genera herramientas/ en datos/tabernaculo.js. */
window.BIBLIA_TABERNACULO = {
  ejemplo: true,
  unidad: 'codo',
  codos: [
    { id: 'comun', nombre: 'Codo común', cm: 44.5, fuente: 'EJEMPLO: valor aproximado de prueba', url: '', defecto: true },
    { id: 'real', nombre: 'Codo real', cm: 52.5, fuente: 'EJEMPLO: valor aproximado de prueba', url: '' }
  ],
  orientacion: { texto: 'La entrada del atrio está al oriente', ref: 'Ex 27:13', cita: 'Y en el ancho del atrio por la parte de levante, al oriente, habrá cincuenta codos.' },
  zonas: [
    { id: 'atrio', nombre: 'Atrio',
      largo: { codos: 100, ref: 'Ex 27:18', cita: 'La longitud del atrio será de cien codos', certeza: 'texto' },
      ancho: { codos: 50, ref: 'Ex 27:18', cita: 'y la anchura cincuenta por un lado y cincuenta por el otro', certeza: 'texto' },
      alto: { codos: 5, ref: 'Ex 27:18', cita: 'y la altura de cinco codos', certeza: 'texto' }, nota: 'EJEMPLO' },
    { id: 'santo', nombre: 'Lugar santo',
      largo: { codos: 20, ref: 'Ex 26:18', cita: 'veinte tablas al lado del mediodía, al austro.', certeza: 'calculo' },
      ancho: { codos: 10, ref: 'Ex 26:22', cita: 'Y para el lado del tabernáculo, al occidente, harás seis tablas.', certeza: 'inferido' },
      alto: { codos: 10, ref: 'Ex 26:16', cita: 'La longitud de cada tabla será de diez codos', certeza: 'inferido' }, nota: 'EJEMPLO: el largo resulta de restar el santísimo a las veinte tablas.' },
    { id: 'santisimo', nombre: 'Lugar santísimo',
      largo: { codos: 10, ref: 'Ex 26:33', cita: 'aquel velo os hará separación entre el lugar santo y el santísimo.', certeza: 'inferido' },
      ancho: { codos: 10, ref: 'Ex 26:22', cita: 'Y para el lado del tabernáculo, al occidente, harás seis tablas.', certeza: 'inferido' },
      alto: { codos: 10, ref: 'Ex 26:16', cita: 'La longitud de cada tabla será de diez codos', certeza: 'inferido' }, nota: 'EJEMPLO' }
  ],
  piezas: [
    { id: 'arca', nombre: 'Arca del testimonio', grupo: 'mobiliario', instruccion: 'Ex 25:10-22', construccion: 'Ex 37:1-9',
      medidas: {
        largo: { codos: 2.5, ref: 'Ex 25:10', cita: 'cuya longitud será de dos codos y medio', certeza: 'texto' },
        ancho: { codos: 1.5, ref: 'Ex 25:10', cita: 'y su anchura de codo y medio', certeza: 'texto' },
        alto: { codos: 1.5, ref: 'Ex 25:10', cita: 'y su altura de codo y medio', certeza: 'texto' } },
      materiales: [{ nombre: 'Madera de acacia (Sittim)', ref: 'Ex 25:10', cita: 'Harán también un arca de madera de Sittim' },
        { nombre: 'Oro puro', ref: 'Ex 25:11', cita: 'Y la cubrirás de oro puro' }],
      zona: { id: 'santisimo', certeza: 'texto', ref: 'Ex 26:33', cita: 'y meterás allí, del velo adentro, el arca del testimonio', nota: '' },
      plano: { x: 25, y: 25, certeza: 'tradicion', nota: 'EJEMPLO: el texto la pone tras el velo, pero no dice en qué punto.' },
      funcion: { texto: 'Lugar desde donde Dios habla a Moisés', ref: 'Ex 25:22', cita: 'Y de allí me declararé á ti, y hablaré contigo de sobre la cubierta' },
      nota: 'EJEMPLO' },
    { id: 'mesa', nombre: 'Mesa de los panes', grupo: 'mobiliario', instruccion: 'Ex 25:23-30', construccion: 'Ex 37:10-16',
      medidas: {
        largo: { codos: 2, ref: 'Ex 25:23', cita: 'su longitud será de dos codos', certeza: 'texto' },
        ancho: { codos: 1, ref: 'Ex 25:23', cita: 'y de un codo su anchura', certeza: 'texto' },
        alto: { codos: 1.5, ref: 'Ex 25:23', cita: 'y su altura de codo y medio', certeza: 'texto' } },
      materiales: [{ nombre: 'Madera de acacia (Sittim)', ref: 'Ex 25:23', cita: 'Harás asimismo una mesa de madera de Sittim' },
        { nombre: 'Oro puro', ref: 'Ex 25:24', cita: 'Y la cubrirás de oro puro' }],
      zona: { id: 'santo', certeza: 'texto', ref: 'Ex 40:22', cita: 'al lado septentrional del pabellón, fuera del velo', nota: '' },
      plano: { x: 38, y: 28, certeza: 'inferido', nota: 'EJEMPLO: el lado norte lo dice el texto; el punto exacto, no.' },
      funcion: { texto: 'Sobre ella se pone el pan de la proposición', ref: 'Ex 25:30', cita: 'Y pondrás sobre la mesa el pan de la proposición delante de mí continuamente.' },
      nota: 'EJEMPLO' },
    { id: 'candelabro', nombre: 'Candelabro', grupo: 'mobiliario', instruccion: 'Ex 25:31-40', construccion: 'Ex 37:17-24',
      medidas: {},
      cantidad: null,
      materiales: [{ nombre: 'Oro puro labrado a martillo', ref: 'Ex 25:31', cita: 'Harás además un candelero de oro puro; labrado á martillo' },
        { nombre: 'Un talento de oro', ref: 'Ex 25:39', cita: 'De un talento de oro fino lo harás' }],
      zona: { id: 'santo', certeza: 'texto', ref: 'Ex 40:24', cita: 'enfrente de la mesa, al lado meridional del pabellón.', nota: '' },
      plano: { x: 38, y: 22, certeza: 'inferido', nota: 'EJEMPLO: frente a la mesa, en el lado sur.' },
      nota: 'EJEMPLO: el texto no da sus medidas.' },
    { id: 'altar-bronce', nombre: 'Altar del holocausto', grupo: 'mobiliario', instruccion: 'Ex 27:1-8', construccion: 'Ex 38:1-7',
      medidas: {
        largo: { codos: 5, ref: 'Ex 27:1', cita: 'de cinco codos de longitud', certeza: 'texto' },
        ancho: { codos: 5, ref: 'Ex 27:1', cita: 'y de cinco codos de anchura', certeza: 'texto' },
        alto: { codos: 3, ref: 'Ex 27:1', cita: 'y su altura de tres codos', certeza: 'texto' } },
      materiales: [{ nombre: 'Madera de acacia (Sittim)', ref: 'Ex 27:1', cita: 'HARÁS también altar de madera de Sittim' },
        { nombre: 'Metal (bronce)', ref: 'Ex 27:2', cita: 'y lo cubrirás de metal.' }],
      zona: { id: 'atrio', certeza: 'texto', ref: 'Ex 40:29', cita: 'Y colocó el altar del holocausto á la puerta del tabernáculo', nota: '' },
      plano: { x: 70, y: 25, certeza: 'tradicion', nota: 'EJEMPLO: «a la puerta del tabernáculo»; la distancia no la da el texto.' },
      nota: 'EJEMPLO' },
    { id: 'tablas', nombre: 'Tablas', grupo: 'estructura', instruccion: 'Ex 26:15-30', construccion: 'Ex 36:20-34',
      medidas: {
        largo: { codos: 1.5, ref: 'Ex 26:16', cita: 'y de codo y medio la anchura de cada tabla.', certeza: 'texto' },
        alto: { codos: 10, ref: 'Ex 26:16', cita: 'La longitud de cada tabla será de diez codos', certeza: 'texto' } },
      cantidad: { valor: 20, ref: 'Ex 26:18', cita: 'veinte tablas al lado del mediodía, al austro.' },
      materiales: [{ nombre: 'Madera de acacia (Sittim)', ref: 'Ex 26:15', cita: 'tablas de madera de Sittim, que estén derechas.' }],
      zona: { id: 'santo', certeza: 'inferido', ref: 'Ex 26:18', cita: 'veinte tablas al lado del mediodía', nota: '' },
      plano: { x: 35, y: 20, certeza: 'inferido', nota: 'EJEMPLO: pared sur.' }, nota: 'EJEMPLO: solo se indican las del lado sur.' },
    { id: 'velo', nombre: 'Velo', grupo: 'cortinas', instruccion: 'Ex 26:31-35', construccion: 'Ex 36:35-36',
      medidas: {},
      materiales: [{ nombre: 'Cárdeno, púrpura, carmesí y lino torcido', ref: 'Ex 26:31', cita: 'Y harás también un velo de cárdeno, y púrpura, y carmesí, y de lino torcido' }],
      zona: { id: 'santo', certeza: 'texto', ref: 'Ex 26:33', cita: 'aquel velo os hará separación entre el lugar santo y el santísimo.', nota: '' },
      plano: { x: 30, y: 25, rot: 90, certeza: 'inferido', nota: 'EJEMPLO: entre las dos estancias.' }, nota: 'EJEMPLO' },
    { id: 'cortinas-atrio', nombre: 'Cortinas del atrio', grupo: 'atrio', instruccion: 'Ex 27:9-19', construccion: 'Ex 38:9-20',
      medidas: { largo: { codos: 100, ref: 'Ex 27:9', cita: 'de cien codos de longitud cada un lado', certeza: 'texto' },
        alto: { codos: 5, ref: 'Ex 27:18', cita: 'y la altura de cinco codos', certeza: 'texto' } },
      materiales: [{ nombre: 'Lino torcido', ref: 'Ex 27:9', cita: 'tendrá el atrio cortinas de lino torcido' }],
      zona: { id: 'atrio', certeza: 'texto', ref: 'Ex 27:9', cita: 'Asimismo harás el atrio del tabernáculo', nota: '' },
      plano: { x: 50, y: 0, certeza: 'texto', nota: 'EJEMPLO: lado sur del atrio.' }, nota: 'EJEMPLO' }
  ],
  calculos: [
    { id: 'largo-tabernaculo', texto: 'Largo del tabernáculo', resultado: '30 codos',
      pasos: [{ texto: '20 tablas en el lado sur', ref: 'Ex 26:18', cita: 'veinte tablas al lado del mediodía, al austro.' },
        { texto: 'cada tabla mide codo y medio de ancho: 20 × 1,5 = 30', ref: 'Ex 26:16', cita: 'y de codo y medio la anchura de cada tabla.' }] }
  ],
  montaje: [
    { orden: 1, pieza: 'tablas', ref: 'Ex 40:18', cita: 'Y Moisés hizo levantar el tabernáculo, y asentó sus basas, y colocó sus tablas' },
    { orden: 2, pieza: 'arca', ref: 'Ex 40:20', cita: 'Y tomó y puso el testimonio dentro del arca' },
    { orden: 3, pieza: 'velo', ref: 'Ex 40:21', cita: 'Y metió el arca en el tabernáculo, y puso el velo de la tienda' },
    { orden: 4, pieza: 'mesa', ref: 'Ex 40:22', cita: 'Y puso la mesa en el tabernáculo del testimonio, al lado septentrional del pabellón, fuera del velo' },
    { orden: 5, pieza: 'candelabro', ref: 'Ex 40:24', cita: 'Y puso el candelero en el tabernáculo del testimonio, enfrente de la mesa' },
    { orden: 6, pieza: 'altar-bronce', ref: 'Ex 40:29', cita: 'Y colocó el altar del holocausto á la puerta del tabernáculo' },
    { orden: 7, pieza: 'cortinas-atrio', ref: 'Ex 40:33', cita: 'Finalmente erigió el atrio en derredor del tabernáculo y del altar' }
  ],
  fuentes: [{ id: 'ejemplo', nombre: 'EJEMPLO: datos de prueba', url: '' }]
};
