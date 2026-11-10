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
    P('Shelah_1', 'Sala', 'm', ['Gn 11:12']), P('Abraham_1', 'Abram', 'm', ['Gn 11:26'])
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
    R('Shelah_1', 'Abraham_1', 'Gn 11:26', 'inferido')
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

  g.BIBLIA_DATOS = {
    generado: '2026-11-10T00:00:00Z',
    fuentes: [
      { id: 'rv1909', nombre: 'Reina-Valera 1909', licencia: 'Dominio público', url: 'https://example.org/rv1909' },
      { id: 'brenton', nombre: 'Brenton LXX (1851)', licencia: 'Dominio público', url: 'https://example.org/brenton' }
    ],
    capitulos: [
      { libro: 'Génesis', cap: 5, versiculos: [{ n: 1, texto: 'Este es el libro de las generaciones de Adán (texto de ejemplo).' }, { n: 3, texto: 'Y vivió Adán ciento y treinta años, y engendró un hijo… (ejemplo)' }] },
      { libro: 'Génesis', cap: 11, versiculos: [{ n: 10, texto: 'Estas son las generaciones de Sem (texto de ejemplo).' }, { n: 12, texto: 'Y Arphaxad vivió treinta y cinco años… (ejemplo)' }] }
    ],
    personas, relaciones, edades
  };
})(typeof window !== 'undefined' ? window : globalThis);
