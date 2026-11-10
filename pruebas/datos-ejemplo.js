/* Datos de ejemplo (pequeños) con el mismo contrato que datos/genesis.js.
   Adán→Noé con TM y LXX, Cainán (Gn 11) solo en LXX, y una línea corta hasta Abram para la ruta. */
(function (g) {
  const P = (id, nombre, sexo, refs, nota) => ({ id, nombre, sexo, primera_ref: refs[0], refs, nota: nota || '' });
  const personas = [
    P('Adam_1', 'Adán', 'm', ['Gn 2:7', 'Gn 5:1', 'Gn 5:3']), P('Eve_1', 'Eva', 'f', ['Gn 3:20', 'Gn 4:1']),
    P('Cain_1', 'Caín', 'm', ['Gn 4:1']), P('Abel_1', 'Abel', 'm', ['Gn 4:2']), P('Seth_1', 'Set', 'm', ['Gn 4:25', 'Gn 5:3']),
    P('Enosh_1', 'Enós', 'm', ['Gn 4:26', 'Gn 5:6']), P('Kenan_1', 'Cainán', 'm', ['Gn 5:9']), P('Mahalalel_1', 'Mahalaleel', 'm', ['Gn 5:12']),
    P('Jared_1', 'Jared', 'm', ['Gn 5:15']), P('Enoch_2', 'Enoc', 'm', ['Gn 5:18']), P('Methuselah_1', 'Matusalén', 'm', ['Gn 5:21']),
    P('Lamech_2', 'Lamec', 'm', ['Gn 5:25']), P('Noah_1', 'Noé', 'm', ['Gn 5:29']), P('Shem_1', 'Sem', 'm', ['Gn 5:32', 'Gn 11:10']),
    P('Arphaxad_1', 'Arfaxad', 'm', ['Gn 10:22', 'Gn 11:10']), P('Cainan_2', 'Cainán', 'm', ['Gn 11:12'], 'Solo en la Septuaginta (LXX Gn 11:12-13).'),
    P('Shelah_1', 'Sala', 'm', ['Gn 11:12']), P('Abraham_1', 'Abram', 'm', ['Gn 11:26', 'Gn 12:4'], 'Abram; Dios le cambia el nombre a Abraham (Gn 17:5). Un solo registro.'),
    // Patriarcas (Gn 12–30) abreviados: Jacob con cuatro mujeres para agrupar hijos por madre
    P('Isaac_1', 'Isaac', 'm', ['Gn 21:3', 'Gn 25:26']), P('Jacob_1', 'Jacob', 'm', ['Gn 25:26', 'Gn 29:32'], 'Llamado también Israel (Gn 32:28). Un solo registro.'),
    P('Leah_1', 'Lea', 'f', ['Gn 29:32']), P('Rachel_1', 'Raquel', 'f', ['Gn 30:24']), P('Bilhah_1', 'Bilha', 'f', ['Gn 30:4']), P('Zilpah_1', 'Zilpa', 'f', ['Gn 30:4']),
    P('Reuben_1', 'Rubén', 'm', ['Gn 29:32']), P('Dinah_1', 'Dina', 'f', ['Gn 30:24']), P('Joseph_1', 'José', 'm', ['Gn 30:24']),
    P('Dan_1', 'Dan', 'm', ['Gn 30:4']), P('Gad_1', 'Gad', 'm', ['Gn 30:4']),
    // Sin ningún parentesco registrado: van a su propia sección del Árbol
    Object.assign(P('Melchizedek_1', 'Melquisedec', 'm', ['Gn 14:18']), { rol: 'rey de Salem' }), P('Deborah_1', 'Débora', 'f', ['Gn 35:8']),
    // Línea de Caín abreviada en el ejemplo (Enoc→Lamec omite generaciones) y mujeres
    P('Enoch_1', 'Enoc', 'm', ['Gn 4:17']), P('Lamech_1', 'Lamec', 'm', ['Gn 4:18'], 'Ejemplo abreviado.'),
    P('Adah_1', 'Ada', 'f', ['Gn 4:19']), P('Zillah_1', 'Zila', 'f', ['Gn 4:19']),
    P('Jabal_1', 'Jabal', 'm', ['Gn 4:20']), P('TubalCain_1', 'Tubal-caín', 'm', ['Gn 4:22']), P('Naamah_1', 'Naama', 'f', ['Gn 4:22']),
    Object.assign(P('NoahWife_1', 'Esposa de Noé', 'f', ['Gn 7:7']), { sin_nombre: true }),
    Object.assign(P('CainWife_1', 'Esposa de Caín', 'f', ['Gn 4:17']), { sin_nombre: true, ref_mencion: 'Gn 4:17' }),
    Object.assign(P('AdamOtros_1', 'Otros hijos e hijas de Adán', '?', ['Gn 5:4']), { sin_nombre: true })
  ];
  const R = (de, a, ref, certeza, tipo) => ({ de, a, tipo: tipo || 'padre', ref, certeza: certeza || 'explicito', fuente: 'ejemplo', nota: '' });
  const relaciones = [
    R('Adam_1', 'Eve_1', 'Gn 2:22', 'explicito', 'conyuge'),
    R('Adam_1', 'Cain_1', 'Gn 4:1'), R('Eve_1', 'Cain_1', 'Gn 4:1', 'explicito', 'madre'), R('Adam_1', 'Abel_1', 'Gn 4:2', 'inferido'),
    R('Adam_1', 'Seth_1', 'Gn 5:3'), R('Seth_1', 'Enosh_1', 'Gn 5:6'), R('Enosh_1', 'Kenan_1', 'Gn 5:9'), R('Kenan_1', 'Mahalalel_1', 'Gn 5:12'),
    R('Mahalalel_1', 'Jared_1', 'Gn 5:15'), R('Jared_1', 'Enoch_2', 'Gn 5:18'), R('Enoch_2', 'Methuselah_1', 'Gn 5:21'),
    R('Methuselah_1', 'Lamech_2', 'Gn 5:25'), R('Lamech_2', 'Noah_1', 'Gn 5:28'), R('Noah_1', 'Shem_1', 'Gn 5:32'),
    R('Shem_1', 'Arphaxad_1', 'Gn 11:10'), R('Arphaxad_1', 'Shelah_1', 'Gn 11:12'),
    R('Arphaxad_1', 'Cainan_2', 'Gn 11:12'), R('Cainan_2', 'Shelah_1', 'Gn 11:13'),
    R('Shelah_1', 'Abraham_1', 'Gn 11:26', 'inferido'),
    R('Adam_1', 'AdamOtros_1', 'Gn 5:4'),
    R('Cain_1', 'Enoch_1', 'Gn 4:17'), R('Enoch_1', 'Lamech_1', 'Gn 4:18', 'inferido'),
    Object.assign(R('Lamech_1', 'Adah_1', 'Gn 4:19', 'explicito', 'conyuge'), { cita: 'Y tomó para sí Lamech dos mujeres' }),
    R('Lamech_1', 'Zillah_1', 'Gn 4:19', 'explicito', 'conyuge'),
    R('Lamech_1', 'Jabal_1', 'Gn 4:20'), R('Adah_1', 'Jabal_1', 'Gn 4:20', 'explicito', 'madre'),
    R('Lamech_1', 'TubalCain_1', 'Gn 4:22'), R('Zillah_1', 'TubalCain_1', 'Gn 4:22', 'explicito', 'madre'),
    R('Lamech_1', 'Naamah_1', 'Gn 4:22'),
    R('Noah_1', 'NoahWife_1', 'Gn 7:7', 'explicito', 'conyuge'),
    R('Cain_1', 'CainWife_1', 'Gn 4:17', 'explicito', 'conyuge'),
    R('Abraham_1', 'Isaac_1', 'Gn 21:3'), R('Isaac_1', 'Jacob_1', 'Gn 25:26'),
    R('Jacob_1', 'Leah_1', 'Gn 29:32', 'explicito', 'conyuge'), R('Jacob_1', 'Rachel_1', 'Gn 30:24', 'explicito', 'conyuge'),
    Object.assign(R('Jacob_1', 'Bilhah_1', 'Gn 30:4', 'explicito', 'conyuge'), { nota: 'sierva' }),
    Object.assign(R('Jacob_1', 'Zilpah_1', 'Gn 30:4', 'explicito', 'conyuge'), { nota: 'concubina' }),
    R('Jacob_1', 'Reuben_1', 'Gn 29:32'), R('Leah_1', 'Reuben_1', 'Gn 29:32', 'explicito', 'madre'),
    R('Jacob_1', 'Dan_1', 'Gn 30:4'), R('Bilhah_1', 'Dan_1', 'Gn 30:4', 'explicito', 'madre'),
    R('Jacob_1', 'Gad_1', 'Gn 30:4'), R('Zilpah_1', 'Gad_1', 'Gn 30:4', 'explicito', 'madre'),
    R('Jacob_1', 'Dinah_1', 'Gn 30:24'), R('Leah_1', 'Dinah_1', 'Gn 30:24', 'inferido', 'madre'),
    R('Jacob_1', 'Joseph_1', 'Gn 30:24'), R('Rachel_1', 'Joseph_1', 'Gn 30:24', 'explicito', 'madre')
  ];
  const edades = [];
  const E = (persona, trad, eng, rest, tot, ref) => {
    const f = trad === 'TM' ? 'rv1909' : 'brenton';
    if (eng != null) edades.push({ persona, tipo: 'al_engendrar', tradicion: trad, valor: eng, ref, certeza: 'texto', fuente: f, cita: 'fragmento de ejemplo' });
    if (rest != null) edades.push({ persona, tipo: 'restantes', tradicion: trad, valor: rest, ref, certeza: 'texto', fuente: f, cita: '' });
    if (tot != null) edades.push({ persona, tipo: 'total', tradicion: trad, valor: tot, ref, certeza: 'texto', fuente: f, cita: '' });
  };
  E('Adam_1', 'TM', 130, 800, 930, 'Gn 5:3'); E('Adam_1', 'LXX', 230, 700, 930, 'Gn 5:3');
  E('Seth_1', 'TM', 105, 807, 912, 'Gn 5:6'); E('Seth_1', 'LXX', 205, 707, null, 'Gn 5:6'); // total LXX se deduce
  E('Enosh_1', 'TM', 90, 815, 905, 'Gn 5:9'); E('Enosh_1', 'LXX', 190, 715, 905, 'Gn 5:9');
  E('Kenan_1', 'TM', 70, null, 910, 'Gn 5:12'); E('Kenan_1', 'LXX', 170, null, 910, 'Gn 5:12');
  E('Mahalalel_1', 'TM', 65, null, 895, 'Gn 5:15'); E('Mahalalel_1', 'LXX', 165, null, 895, 'Gn 5:15');
  E('Jared_1', 'TM', 162, null, 962, 'Gn 5:18'); E('Jared_1', 'LXX', 162, null, 962, 'Gn 5:18');
  E('Enoch_2', 'TM', 65, null, 365, 'Gn 5:21'); E('Enoch_2', 'LXX', 165, null, 365, 'Gn 5:21');
  E('Methuselah_1', 'TM', 187, null, 969, 'Gn 5:25'); E('Methuselah_1', 'LXX', 167, null, 969, 'Gn 5:25');
  E('Lamech_2', 'TM', 182, null, 777, 'Gn 5:28'); E('Lamech_2', 'LXX', 188, null, 753, 'Gn 5:28');
  E('Noah_1', 'TM', 500, null, 950, 'Gn 5:32'); E('Noah_1', 'LXX', 500, null, 950, 'Gn 5:32');
  E('Shem_1', 'TM', 100, 500, null, 'Gn 11:10'); E('Shem_1', 'LXX', 100, 500, null, 'Gn 11:10');
  E('Arphaxad_1', 'TM', 35, 403, null, 'Gn 11:12'); E('Arphaxad_1', 'LXX', 135, 430, null, 'Gn 11:12');
  E('Cainan_2', 'LXX', 130, 330, null, 'Gn 11:13');
  E('Shelah_1', 'TM', 30, 403, null, 'Gn 11:14'); E('Shelah_1', 'LXX', 130, 330, null, 'Gn 11:14');
  ['TM', 'LXX'].forEach(t => edades.push({ persona: 'Noah_1', tipo: 'al_diluvio', tradicion: t, valor: 600, ref: 'Gn 7:6', certeza: 'texto', fuente: t === 'TM' ? 'rv1909' : 'brenton', cita: 'Y era Noé de seiscientos años' }));
  // Edades en un momento del relato (tipo en_evento)
  const EV = (persona, trad, valor, evento, ref) => edades.push({ persona, tipo: 'en_evento', evento, tradicion: trad, valor, ref, certeza: 'texto', fuente: trad === 'TM' ? 'rv1909' : 'brenton', cita: '' });
  EV('Abraham_1', 'TM', 75, 'al salir de Harán', 'Gn 12:4'); EV('Abraham_1', 'LXX', 75, 'al salir de Harán', 'Gn 12:4');
  EV('Abraham_1', 'TM', 100, 'cuando nació Isaac', 'Gn 21:5');
  EV('Isaac_1', 'TM', 60, 'cuando nacieron Esaú y Jacob', 'Gn 25:26');

  const capitulos = [
    { libro: 'Génesis', cap: 4, versiculos: [
      { n: 1, texto: 'Y conoció Adam a su mujer Eva, la cual concibió y parió a Caín.' },
      { n: 2, texto: 'Y después parió a su hermano Abel.' },
      { n: 16, texto: 'Y salió Caín de delante de Jehová, y habitó en tierra de Nod, al oriente de Edén.' },
      { n: 17, texto: 'Y conoció Caín a su mujer, la cual concibió y parió a Enoc.' },
      { n: 19, texto: 'Y tomó para sí Lamech dos mujeres; el nombre de la una fue Ada, y el nombre de la otra Zila.' },
      { n: 20, texto: 'Y Ada parió a Jabal.' },
      { n: 22, texto: 'Y Zila también parió a Tubal-caín; y la hermana de Tubal-caín fue Naama.' }] },
    { libro: 'Génesis', cap: 5, versiculos: [{ n: 1, texto: 'Este es el libro de las generaciones de Adam (texto de ejemplo).' }, { n: 3, texto: 'Y vivió Adam ciento y treinta años, y engendró un hijo… (ejemplo)' }] },
    { libro: 'Génesis', cap: 7, versiculos: [{ n: 6, texto: 'Y era Noé de seiscientos años cuando el diluvio de las aguas fue sobre la tierra.' }] },
    { libro: 'Génesis', cap: 11, versiculos: [{ n: 10, texto: 'Estas son las generaciones de Sem (texto de ejemplo).' }, { n: 12, texto: 'Y Arphaxad vivió treinta y cinco años… (ejemplo)' },
      { n: 31, texto: 'Y salieron con ellos de Ur de los Caldeos, para ir á la tierra de Canaán: y vinieron hasta Harán.' }] },
    { libro: 'Génesis', cap: 8, versiculos: [{ n: 4, texto: 'Y reposó el arca sobre los montes de Ararat.' }] },
    { libro: 'Génesis', cap: 12, versiculos: [{ n: 4, texto: 'Y fuése Abram, como Jehová le dijo; y era Abram de edad de setenta y cinco años cuando salió de Harán.' }] },
    { libro: 'Génesis', cap: 21, versiculos: [{ n: 3, texto: 'Y llamó Abraham el nombre de su hijo Isaac (ejemplo).' }, { n: 5, texto: 'Y era Abraham de cien años cuando le nació Isaac su hijo.' }] },
    { libro: 'Génesis', cap: 25, versiculos: [{ n: 26, texto: 'Y fué llamado su nombre Jacob; y era Isaac de edad de sesenta años (ejemplo).' }] },
    { libro: 'Génesis', cap: 29, versiculos: [{ n: 32, texto: 'Y concibió Lea, y parió un hijo, y llamó su nombre Rubén.' }] },
    { libro: 'Génesis', cap: 30, versiculos: [{ n: 4, texto: 'Así le dió á Bilha su sierva por mujer; y Jacob entró á ella (ejemplo con Dan y Gad).' }, { n: 24, texto: 'Y llamó su nombre José (ejemplo).' }] }
  ];
  capitulos.sort((a, b) => a.cap - b.cap);
  const textoDe = ref => { const [c, v] = ref.slice(3).split(':').map(Number); return capitulos.find(x => x.cap === c).versiculos.find(x => x.n === v).texto; };
  const M = (ref, persona, palabra) => { const i = textoDe(ref).indexOf(palabra); return { ref, persona, inicio: i, fin: i + palabra.length }; };
  const menciones = [
    M('Gn 4:1', 'Adam_1', 'Adam'), M('Gn 4:1', 'Eve_1', 'Eva'), M('Gn 4:1', 'Cain_1', 'Caín'),
    M('Gn 4:17', 'Cain_1', 'Caín'), M('Gn 4:17', 'Enoch_1', 'Enoc'),
    M('Gn 4:19', 'Lamech_1', 'Lamech'), M('Gn 4:19', 'Adah_1', 'Ada'), M('Gn 4:19', 'Zillah_1', 'Zila'),
    { ref: 'Gn 4:20', persona: 'Jabal_1', inicio: 50, fin: 60 }, // fuera de rango: se ignora
    M('Gn 4:16', 'Cain_1', 'Caín')
  ];
  const ML = (ref, lugar, palabra) => { const i = textoDe(ref).indexOf(palabra); return { ref, lugar, inicio: i, fin: i + palabra.length }; };
  const menciones_lugar = [ML('Gn 4:16', 'nod', 'Nod'), ML('Gn 11:31', 'ur', 'Ur de los Caldeos'), ML('Gn 11:31', 'haran', 'Harán')]; // Edén y Canaán: por nombre
  const L = (id, nombre, tipo, refs, ubicacion, extra) => Object.assign({ id, nombre, nombre_rv1909: nombre, tipo, refs, ubicacion, alternativas: [], fuente: 'openbible', url_fuente: 'https://www.openbible.info/geo/', nota: '' }, extra || {});
  const lugares = [
    L('eden', 'Edén', 'region', ['Gn 2:8', 'Gn 4:16'], null, { nota: 'Sin identificación geográfica fiable.' }),
    L('nod', 'Nod', 'region', ['Gn 4:16'], null),
    L('ararat', 'Ararat', 'monte', ['Gn 8:4'], { lat: 39.70, lon: 44.30, identificacion: 'Región de Urartu (Armenia, Turquía, Irán)', confianza: 'baja', puntuacion_openbible: 120 }),
    L('ur', 'Ur de los Caldeos', 'ciudad', ['Gn 11:28', 'Gn 11:31'], { lat: 30.96, lon: 46.10, identificacion: 'Tell el-Muqayyar (Irak)', confianza: 'alta', puntuacion_openbible: 900 },
      { alternativas: [{ identificacion: 'Urfa (Turquía)', lat: 37.16, lon: 38.79, puntuacion_openbible: 80 }] }),
    L('haran', 'Harán', 'ciudad', ['Gn 11:31'], { lat: 36.86, lon: 39.03, identificacion: 'Harran (Turquía)', confianza: 'alta', puntuacion_openbible: 950 }),
    L('canaan', 'Canaán', 'region', ['Gn 11:31'], { lat: 31.9, lon: 35.2, identificacion: 'Levante meridional', confianza: 'media', puntuacion_openbible: 500 }),
    L('roto', 'Lugar sin coordenadas válidas', 'otro', [], { lat: 'x', lon: null, identificacion: '?', confianza: 'alta' })
  ];
  g.BIBLIA_MAPA = {
    bbox: [30, 24, 52, 41],
    costas: [[[30, 41], [52, 41], [52, 30], [50, 29.6], [48.6, 30.1], [48, 29], [50, 26.5], [52, 25.5], [52, 24], [38.5, 24], [35, 28], [34.6, 31.6], [35.8, 34.2], [36, 36.6], [33, 36.2], [30, 36.6], [30, 41]]],
    rios: [{ nombre: 'Éufrates', puntos: [[38.5, 38.6], [38.3, 36.6], [40.4, 35.1], [43, 33.6], [44.4, 32.1], [46.4, 31.1], [47.8, 30.6]] },
      { nombre: 'Tigris', puntos: [[40.4, 38.1], [42.5, 37.1], [43.2, 36.3], [44.4, 33.3], [45.8, 32.4], [47.4, 31]] }],
    lagos: [[[42.4, 38.6], [43.3, 38.95], [43.6, 38.5], [42.9, 38.3]]],
    fuente: 'Natural Earth (ejemplo simplificado)', url: 'https://www.naturalearthdata.com/'
  };
  const pasajes = [
    { id: 'ej-01', seccion: 'Los orígenes (Gn 4–7)', inicio: 'Gn 4:1', fin: 'Gn 4:22', titulo: 'Caín, Abel y la familia de Lamec', titulo_origen: 'editorial', resumen: 'Resumen de ejemplo.' },
    { id: 'ej-02', seccion: 'Los orígenes (Gn 4–7)', inicio: 'Gn 5:1', fin: 'Gn 7:6', titulo: 'De Adán a Noé', titulo_origen: 'editorial', resumen: '' },
    { id: 'ej-03', seccion: 'De Sem a Abram (Gn 11)', inicio: 'Gn 11:10', fin: 'Gn 11:31', titulo: 'Descendientes de Sem', titulo_origen: 'editorial', resumen: '' },
    { id: 'ej-04', seccion: 'Abraham, Isaac y Jacob (Gn 12–30)', inicio: 'Gn 12:4', fin: 'Gn 21:5', titulo: 'Abram sale de Harán', titulo_origen: 'editorial', resumen: '' },
    { id: 'ej-05', inicio: 'Gn 25:26', fin: 'Gn 30:24', titulo: 'Los hijos de Jacob', titulo_origen: 'editorial', resumen: 'Sin sección: hereda la anterior.' }
  ];

  // Cronología de ejemplo (cifras reales de TM/LXX para Adán→Noé; la cadena Enós→Noé y Sem→Abram está abreviada).
  const combos = ['TM|tare70', 'TM|tare130', 'LXX|tare70', 'LXX|tare130'];
  const A = (tm, lxx, tm130, lxx130) => ({ 'TM|tare70': tm, 'LXX|tare70': lxx, 'TM|tare130': tm130 === undefined ? tm : tm130, 'LXX|tare130': lxx130 === undefined ? lxx : lxx130 });
  const EVT = (id, titulo, tipo, ref, personas, depende_de, pasos, anios) => ({ id, titulo, tipo, ref, personas, depende_de, pasos, anios, certeza: 'calculo', nota: '' });
  const paso = (texto, ref, persona, tipo) => ({ texto, ref, edad: persona ? { persona, tipo: tipo || 'al_engendrar' } : null });
  const cronologia = {
    unidad: 'años desde la creación de Adán (cálculo)',
    supuestos: [{ id: 'tare', pregunta: '¿Qué edad tenía Taré al nacer Abram?', defecto: 'tare70',
      opciones: [{ id: 'tare70', texto: '70 (lectura directa de Gn 11:26)', refs: ['Gn 11:26'], nota: '' },
        { id: 'tare130', texto: '130 (Taré muere a los 205 en Harán y Abram sale con 75)', refs: ['Gn 11:32', 'Gn 12:4'], nota: '' }] }],
    combinaciones: combos.map(id => ({ id, tradicion: id.split('|')[0], supuestos: { tare: id.split('|')[1] } })),
    eventos: [
      EVT('ev-adan', 'Creación de Adán', 'nacimiento', 'Gn 5:1', ['Adam_1'], null, [paso('Origen de la cuenta: año 0', 'Gn 5:1')], A(0, 0)),
      EVT('ev-nac-set', 'Nace Set', 'nacimiento', 'Gn 5:3', ['Seth_1'], 'ev-adan', [paso('Adán tenía 130 años (LXX 230) al engendrar a Set', 'Gn 5:3', 'Adam_1')], A(130, 230)),
      EVT('ev-muere-adan', 'Muere Adán', 'muerte', 'Gn 5:5', ['Adam_1'], 'ev-adan', [paso('Adán vivió 930 años', 'Gn 5:5', 'Adam_1', 'total')], A(930, 930)),
      EVT('ev-nac-enos', 'Nace Enós', 'nacimiento', 'Gn 5:6', ['Enosh_1'], 'ev-nac-set', [paso('Set tenía 105 años (LXX 205) al engendrar a Enós', 'Gn 5:6', 'Seth_1')], A(235, 435)),
      EVT('ev-muere-set', 'Muere Set', 'muerte', 'Gn 5:8', ['Seth_1'], 'ev-nac-set', [paso('Set vivió 912 años', 'Gn 5:8', 'Seth_1', 'total')], A(1042, 1142)),
      EVT('ev-nac-noe', 'Nace Noé', 'nacimiento', 'Gn 5:29', ['Noah_1'], 'ev-nac-enos', [paso('Suma de las edades al engendrar de Enós a Lamec (abreviado en el ejemplo)', 'Gn 5:28')], A(1056, 1642)),
      EVT('ev-diluvio', 'El diluvio', 'evento', 'Gn 7:6', ['Noah_1'], 'ev-nac-noe', [paso('Noé tenía 600 años cuando vino el diluvio', 'Gn 7:6', 'Noah_1', 'al_diluvio')], A(1656, 2242)),
      EVT('ev-muere-noe', 'Muere Noé', 'muerte', 'Gn 9:29', ['Noah_1'], 'ev-nac-noe', [paso('Noé vivió 950 años', 'Gn 9:29', 'Noah_1', 'total')], A(2006, 2592)),
      EVT('ev-nac-abram', 'Nace Abram', 'nacimiento', 'Gn 11:26', ['Abraham_1'], 'ev-diluvio', [paso('De Sem a Taré (abreviado en el ejemplo)', 'Gn 11:10'), paso('Taré tenía 70 años al engendrar a Abram (o 130, según el supuesto)', 'Gn 11:26')], A(1948, 3312, 2008, 3372)),
      EVT('ev-sale-haran', 'Abram sale de Harán', 'evento', 'Gn 12:4', ['Abraham_1'], 'ev-nac-abram', [paso('Abram tenía 75 años al salir de Harán', 'Gn 12:4', 'Abraham_1', 'en_evento')], A(2023, 3387, 2083, null))
    ],
    hitos_sin_fecha: [{ titulo: 'Caín mata a Abel', ref: 'Gn 4:8', nota: '' }, { titulo: 'Los hijos de Dios y las hijas de los hombres', ref: 'Gn 6:1', nota: '' }]
  };

  g.BIBLIA_DATOS = {
    cronologia,
    generado: '2026-11-10T00:00:00Z',
    fuentes: [
      { id: 'rv1909', nombre: 'Reina-Valera 1909', licencia: 'Dominio público', url: 'https://example.org/rv1909' },
      { id: 'brenton', nombre: 'Brenton LXX (1851)', licencia: 'Dominio público', url: 'https://example.org/brenton' }
    ],
    capitulos, pasajes, menciones, menciones_lugar, lugares, personas, relaciones, edades
  };
})(typeof window !== 'undefined' ? window : globalThis);
