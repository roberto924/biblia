// Pruebas de las funciones puras de app.js (sin DOM). Uso: node pruebas/probar.mjs
import { readFileSync, existsSync } from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const aqui = path.dirname(fileURLToPath(import.meta.url));
const cargar = (...archivos) => {
  const ctx = { console }; ctx.window = ctx; vm.createContext(ctx);
  for (const a of archivos) vm.runInContext(readFileSync(a, 'utf8'), ctx, { filename: a });
  return ctx;
};
const j = x => JSON.parse(JSON.stringify(x)); // los objetos vienen de otro "realm"
let ok = 0, fallos = 0;
const prueba = (nombre, fn) => { try { fn(); ok++; console.log('  ✓', nombre); } catch (e) { fallos++; console.log('  ✗', nombre, '\n    ', e.message); } };

const ctx = cargar(path.join(aqui, 'datos-ejemplo.js'), path.join(aqui, '..', 'app.js'));
const N = ctx.BibliaNucleo, D = ctx.BIBLIA_DATOS;
console.log('Datos de ejemplo');

prueba('el árbol parte de Adán y contiene a cada persona una sola vez', () => {
  const b = N.construirBosque(D);
  assert.equal(b[0].id, 'Adam_1');
  const ids = []; (function r(n) { ids.push(n.id); n.hijos.forEach(r); })(b[0]);
  assert.equal(new Set(ids).size, ids.length);
  assert.deepEqual(j(b[0].hijos.map(h => h.id)), ['Cain_1', 'Abel_1', 'Seth_1', 'AdamOtros_1']); // grupo sin nombre al final
  assert.equal(b.length, 1, 'esposas y madres no son raíces sueltas');
});
const nodo = (b, id) => { let f = null; b.forEach(function r(n) { if (n.id === id) f = n; n.hijos.forEach(r); }); return f; };
prueba('cónyuges en los nodos del árbol', () => {
  const b = N.construirBosque(D);
  assert.deepEqual(j(nodo(b, 'Adam_1').conyuges.map(c => c.otro)), ['Eve_1']);
  assert.deepEqual(j(nodo(b, 'Lamech_1').conyuges.map(c => c.otro)), ['Adah_1', 'Zillah_1']);
  assert.equal(nodo(b, 'Lamech_1').conyuges[0].cita, 'Y tomó para sí Lamech dos mujeres');
  assert.deepEqual(j(nodo(b, 'Noah_1').conyuges.map(c => c.otro)), ['NoahWife_1']);
});
prueba('madre por hijo (Lamec: Ada y Zila)', () => {
  const b = N.construirBosque(D);
  assert.deepEqual(j(nodo(b, 'Cain_1').madres.map(m => [m.de, m.ref])), [['Eve_1', 'Gn 4:1']]);
  assert.equal(nodo(b, 'Jabal_1').madres[0].de, 'Adah_1');
  assert.equal(nodo(b, 'TubalCain_1').madres[0].de, 'Zillah_1');
  assert.equal(nodo(b, 'Naamah_1').madres.length, 0);
});
prueba('ninguna mujer queda fuera del árbol renderizable', () => {
  const s = N.alcanzables(D);
  const fuera = D.personas.filter(p => p.sexo === 'f' && !s.has(p.id) && !N.sinParentesco(D).includes(p.id)).map(p => p.id);
  assert.deepEqual(j(fuera), []);
  assert.deepEqual(j(N.contarMujeres(D)), { conNombre: 10, sinNombre: 2 });
  assert.deepEqual(j(D.personas.filter(p => p.sexo === 'f' && !N.enPantallaArbol(D, p.id)).map(p => p.id)), []);
});
console.log('Línea de tiempo (cálculo)');
prueba('combinación y año de un evento por tradición y supuesto', () => {
  assert.deepEqual(j(N.elecciones(D, {})), { tare: 'tare70' });
  assert.deepEqual(j(N.elecciones(D, { tare: 'nada' })), { tare: 'tare70' });
  assert.equal(N.combinacion(D, 'TM', {}), 'TM|tare70');
  assert.equal(N.combinacion(D, 'LXX', { tare: 'tare130' }), 'LXX|tare130');
  assert.equal(N.anioEvento(D, 'ev-nac-set', 'TM|tare70'), 130); assert.equal(N.anioEvento(D, 'ev-nac-set', 'LXX|tare70'), 230);
  assert.equal(N.anioEvento(D, 'ev-nac-abram', 'TM|tare130'), 2008);
  assert.equal(N.anioEvento(D, 'ev-sale-haran', 'LXX|tare130'), null);
  assert.equal(N.anioEvento(D, 'nada', 'TM|tare70'), null);
  assert.equal(N.crono({}), null); assert.equal(N.combinacion({}, 'TM', {}), null);
});
prueba('cadena de pasos desde Adán con subtotales', () => {
  const c = j(N.cadenaEvento(D, 'ev-diluvio', 'TM|tare70'));
  assert.deepEqual(c.map(x => [x.evento, x.anio]), [['ev-adan', 0], ['ev-nac-set', 130], ['ev-nac-enos', 235], ['ev-nac-noe', 1056], ['ev-diluvio', 1656]]);
  assert.equal(c[4].pasos[0].ref, 'Gn 7:6');
  assert.deepEqual(j(N.cadenaEvento(D, 'ev-diluvio', 'LXX|tare70')).map(x => x.anio).at(-1), 2242);
  const Dc = { cronologia: { eventos: [{ id: 'a', depende_de: 'b', anios: {} }, { id: 'b', depende_de: 'a', anios: {} }] } };
  assert.equal(N.cadenaEvento(Dc, 'a', 'TM').length, 2, 'un ciclo no cuelga');
});
prueba('quién vivía en un año', () => {
  const v = j(N.vivosEn(D, 900, 'TM|tare70'));
  assert.deepEqual(v.map(x => [x.persona, x.edad]), [['Adam_1', 900], ['Seth_1', 770]]);
  assert.deepEqual(j(N.vivosEn(D, 1000, 'TM|tare70')).map(x => x.persona), ['Seth_1']);
  assert.deepEqual(j(N.vivosEn(D, 1700, 'TM|tare70')).map(x => x.persona), ['Noah_1']);
  assert.deepEqual(j(N.vivosEn(D, null, 'TM|tare70')), []);
  const vida = N.vidasCrono(D, 'LXX|tare70').get('Noah_1');
  assert.equal(vida.nacimiento, 1642); assert.equal(vida.muerte, 2592);
});
prueba('eventos de un ref y de un pasaje; vecinos fechados de un pasaje sin eventos', () => {
  assert.deepEqual(j(N.eventosDeRefs(D, ['Gn 7:6'])).map(e => e.id), ['ev-diluvio']);
  assert.deepEqual(j(N.eventosDePasaje(D, N.pasajeDe(D, 'Gn 5:1'))).map(e => e.id), ['ev-adan', 'ev-nac-set', 'ev-muere-adan', 'ev-nac-enos', 'ev-muere-set', 'ev-nac-noe', 'ev-diluvio']);
  const p1 = N.pasajeDe(D, 'Gn 4:1');
  assert.deepEqual(j(N.eventosDePasaje(D, p1)), []);
  const v = j(N.vecinosFechados(D, p1.inicio, p1.fin, 'TM|tare70'));
  assert.equal(v.anterior, null); assert.equal(v.siguiente.evento, 'ev-adan');
  const v2 = j(N.vecinosFechados(D, 'Gn 8:4', 'Gn 8:4', 'TM|tare70'));
  assert.equal(v2.anterior.evento, 'ev-diluvio'); assert.equal(v2.siguiente.evento, 'ev-muere-noe');
  assert.deepEqual(j(N.despuesDe(D, 'ev-diluvio', 'TM|tare70')), { evento: 'ev-nac-noe', titulo: 'Nace Noé', anios: 600 });
  assert.equal(N.despuesDe(D, 'ev-adan', 'TM|tare70'), null);
});
prueba('comparación TM/LXX y línea de tiempo por secciones con hitos sin fecha', () => {
  assert.deepEqual(j(N.compararEvento(D, 'ev-diluvio', {})), { TM: 1656, LXX: 2242, dif: 586 });
  assert.equal(N.compararEvento(D, 'ev-sale-haran', { tare: 'tare130' }).dif, null);
  const L = j(N.lineaDeTiempo(D, 'TM|tare70'));
  assert.equal(L[0].titulo, 'Los orígenes (Gn 4–7)');
  // El eje solo lleva sucesos con año; los hitos sin fecha van aparte, en orden de lectura.
  assert.deepEqual(L[0].items.map(x => x.evento.id), ['ev-adan', 'ev-nac-set', 'ev-nac-enos', 'ev-muere-adan', 'ev-muere-set', 'ev-nac-noe', 'ev-diluvio']);
  assert.ok(L.every(g => g.items.every(x => x.tipo === 'evento')));
  assert.deepEqual(L[0].hitos.map(h => h.hito.ref), ['Gn 4:8', 'Gn 6:1']);
  assert.ok(N.esDiluvio(L[0].items.at(-1).evento));
  const Lx = j(N.lineaDeTiempo(D, 'LXX|tare130'));
  const gA = Lx.find(g => g.items.some(x => x.evento && x.evento.id === 'ev-sale-haran'));
  assert.equal(gA.titulo, 'Abraham, Isaac y Jacob (Gn 12–30)');
  assert.equal(gA.items.at(-1).evento.id, 'ev-sale-haran', 'sin año en esta combinación: al final');
  assert.equal(Lx.at(-1).titulo, 'Otros', 'eventos fuera de los pasajes, al final');
  assert.deepEqual(j(N.lineaDeTiempo({}, 'TM')), []);
});
prueba('personas sin parentesco: sección propia en orden de aparición, con rol', () => {
  assert.deepEqual(j(N.sinParentesco(D)), ['Melchizedek_1', 'Deborah_1']);
  assert.equal(N.persona(D, 'Melchizedek_1').rol, 'rey de Salem');
  assert.equal(N.rutaArbol(D, 'Deborah_1'), null); assert.equal(N.enPantallaArbol(D, 'Deborah_1'), true);
  assert.equal(N.buscar(D, 'melqui')[0].id, 'Melchizedek_1');
  assert.ok(!N.sinParentesco(D).includes('Adam_1'));
});
console.log('Escala Génesis 1–50');
prueba('plan agrupado por sección con progreso (y sin secciones, un grupo)', () => {
  const s = j(N.seccionesPlan(D, ['ej-01'], 'ej-02'));
  assert.deepEqual(s.map(g => [g.titulo, g.total, g.leidos]), [['Los orígenes (Gn 4–7)', 2, 1], ['De Sem a Abram (Gn 11)', 1, 0], ['Abraham, Isaac y Jacob (Gn 12–30)', 2, 0]]);
  assert.equal(s[0].siguiente, true); assert.equal(s[0].estado, 'en-curso'); assert.equal(s[2].estado, 'pendiente');
  assert.deepEqual(s[2].pasajes.map(x => x.n), [4, 5], 'numeración global; ej-05 hereda la sección');
  assert.equal(s[0].inicio, 'Gn 4:1'); assert.equal(s[0].fin, 'Gn 7:6');
  assert.equal(new Set(s.map(g => g.id)).size, 3);
  assert.equal(N.seccionesPlan(D, ['ej-03'], null)[1].estado, 'leido');
  const sin = j(N.seccionesPlan({ capitulos: [{ cap: 1, versiculos: [{ n: 1, texto: 'x' }] }] }, [], null));
  assert.equal(sin.length, 1); assert.equal(sin[0].titulo, null);
});
prueba('alcance calculado de los datos', () => {
  assert.equal(N.alcance(D).texto, 'Génesis 4–30'); assert.equal(N.alcance(D).corto, 'Gn 4–30');
  assert.equal(N.alcance({}).texto, 'Génesis');
  assert.equal(N.alcance({ capitulos: [{ libro: 'Génesis', cap: 3 }] }).texto, 'Génesis 3');
});
prueba('hijos agrupados por madre con la nota del vínculo (Jacob, Lamec)', () => {
  const g = j(N.hijosPorMadre(D, N.nodoArbol(D, 'Jacob_1')));
  assert.deepEqual(g.map(x => [x.madre, x.hijos.map(h => h.id)]), [['Leah_1', ['Reuben_1', 'Dinah_1']], ['Bilhah_1', ['Dan_1']], ['Zilpah_1', ['Gad_1']], ['Rachel_1', ['Joseph_1']]]);
  assert.equal(g[1].vinculo.nota, 'sierva'); assert.equal(g[2].vinculo.nota, 'concubina'); assert.equal(g[0].vinculo.otro, 'Leah_1');
  const l = j(N.hijosPorMadre(D, N.nodoArbol(D, 'Lamech_1')));
  assert.deepEqual(l.map(x => [x.madre, x.hijos.map(h => h.id)]), [['Adah_1', ['Jabal_1']], ['Zillah_1', ['TubalCain_1']], [null, ['Naamah_1']]]);
  const n = j(N.hijosPorMadre(D, N.nodoArbol(D, 'Noah_1')));
  assert.equal(n.length, 1); assert.equal(n[0].madre, null);
  assert.ok(!N.nodoArbol(D, 'Leah_1'), 'Lea no es raíz ni nodo: sus hijos cuelgan de Jacob');
});
prueba('uniones: una pareja por rama, con sus hijos (Adán, Jacob, Lamec, Noé)', () => {
  const u = id => j(N.uniones(D, N.nodoArbol(D, id))).map(x => [x.pareja, !!x.vinculo, x.hijos.map(h => h.id)]);
  // En los datos de ejemplo Eva solo es madre registrada de Caín: el resto va en rama aparte, sin madre supuesta.
  assert.deepEqual(u('Adam_1'), [['Eve_1', true, ['Cain_1']], [null, false, ['Abel_1', 'Seth_1', 'AdamOtros_1']]]);
  assert.equal(N.madreSupuesta(D, 'AdamOtros_1'), null);
  assert.deepEqual(u('Jacob_1').map(x => x[0]), ['Leah_1', 'Bilhah_1', 'Zilpah_1', 'Rachel_1']);
  assert.deepEqual(u('Lamech_1'), [['Adah_1', true, ['Jabal_1']], ['Zillah_1', true, ['TubalCain_1']], [null, false, ['Naamah_1']]]);
  // Única esposa y ningún hijo con madre escrita: cuelgan de ella, marcada como madre SUPUESTA (inferido).
  assert.deepEqual(u('Noah_1'), [['NoahWife_1', true, ['Shem_1']]]);
  assert.equal(j(N.uniones(D, N.nodoArbol(D, 'Noah_1')))[0].supuesta, true);
  assert.equal(N.madreSupuesta(D, 'Shem_1'), 'NoahWife_1'); assert.equal(N.madreSupuesta(D, 'Cain_1'), null);
  // Madre sin matrimonio registrado: es pareja de la rama pero sin vínculo de cónyuge.
  const Dm = { personas: [{ id: 'P', sexo: 'm' }, { id: 'M', sexo: 'f' }, { id: 'H', sexo: 'm' }, { id: 'H2', sexo: 'm' }], relaciones: [{ de: 'P', a: 'H', tipo: 'padre', ref: 'Gn 1:1' }, { de: 'M', a: 'H', tipo: 'madre', ref: 'Gn 1:1' }] };
  assert.deepEqual(j(N.uniones(Dm, N.nodoArbol(Dm, 'P'))).map(x => [x.pareja, x.vinculo, x.hijos.map(h => h.id)]), [['M', null, ['H']]]);
  // Si esa madre (sin matrimonio, o madre solo de uno) no es madre de los demás, los demás no se le atribuyen (Simeón y la cananea).
  const Dm2 = Object.assign({}, Dm, { relaciones: Dm.relaciones.concat([{ de: 'P', a: 'H2', tipo: 'padre', ref: 'Gn 1:2' }]) });
  assert.deepEqual(j(N.uniones(Dm2, N.nodoArbol(Dm2, 'P'))).map(x => [x.pareja, x.hijos.map(h => h.id)]), [['M', ['H']], [null, ['H2']]]);
  assert.deepEqual(j(N.uniones(Dm, { hijos: [], conyuges: [] })), []);
});
prueba('vida: años vividos (texto o cálculo) y años desde Adán (cálculo)', () => {
  const v = j(N.vida(D, 'Adam_1', 'TM', N.combinacion(D, 'TM', {})));
  assert.deepEqual([v.total.valor, v.total.certeza, v.total.derivado, v.nacimiento, v.muerte], [930, 'texto', false, 0, 930]);
  const s = j(N.vida(D, 'Seth_1', 'LXX', null));
  assert.deepEqual([s.total.valor, s.total.derivado, s.nacimiento], [912, true, null]);
  assert.equal(j(N.vida(D, 'Eve_1', 'TM', null)).total, null);
  // La madre que figura en el evento de nacimiento de su hijo no "nace" ese año.
  const Dn = { personas: [{ id: 'S', sexo: 'f' }, { id: 'I', sexo: 'm' }], relaciones: [{ de: 'S', a: 'I', tipo: 'madre', ref: 'Gn 21:2' }],
    cronologia: { eventos: [{ id: 'ns', tipo: 'nacimiento', personas: ['S'], anios: { c: 10 } }, { id: 'ni', tipo: 'nacimiento', personas: ['I', 'S'], anios: { c: 100 } }] } };
  assert.equal(N.vidasCrono(Dn, 'c').get('S').nacimiento, 10);
  assert.equal(N.vidasCrono(Dn, 'c').get('I').nacimiento, 100);
});
prueba('edades en_evento por ref y por persona; no entran en la tabla', () => {
  const e = j(N.edadesEnEvento(D, ['Gn 12:4']));
  assert.equal(e.length, 1);
  assert.deepEqual([e[0].persona, e[0].evento, e[0].TM.valor, e[0].LXX.valor, e[0].difiere], ['Abraham_1', 'al salir de Harán', 75, 75, false]);
  assert.equal(j(N.acompanante(D, ['Gn 12:4'])).eventos.length, 1);
  assert.equal(j(N.acompanante(D, ['Gn 12:4'])).edades.length, 0);
  assert.equal(N.tieneApoyo(D, 'Gn 12:4'), true);
  const pp = j(N.edadesEnEventoPorPersona(D));
  assert.deepEqual(pp.map(x => [x.persona, x.items.map(i => i.ref)]), [['Abraham_1', ['Gn 12:4', 'Gn 21:5']], ['Isaac_1', ['Gn 25:26']]]);
  assert.equal(pp[0].items[1].solo, 'TM');
  assert.ok(!j(N.ordenPatriarcas(D)).includes('Isaac_1'));
  const Dx = { edades: [{ persona: 'A', tipo: 'en_evento', evento: 'x', tradicion: 'TM', valor: 75, ref: 'Gn 12:4' }, { persona: 'A', tipo: 'en_evento', evento: 'x', tradicion: 'LXX', valor: 80, ref: 'Gn 12:5' }] };
  assert.equal(N.edadesEnEvento(Dx)[0].difiere, true);
  assert.equal(N.edadesEnEvento(Dx)[0].ref, 'Gn 12:4');
});
prueba('árbol plegado al inicio y ruta para llegar a una persona', () => {
  const ini = N.arbolInicial(D, 2);
  assert.ok(ini.has('Adam_1') && ini.has('Seth_1') && ini.has('Cain_1'));
  assert.ok(!ini.has('Enosh_1') && !ini.has('Jacob_1'));
  const r = j(N.rutaArbol(D, 'Joseph_1'));
  assert.equal(r.ruta[0], 'Adam_1'); assert.deepEqual(r.ruta.slice(-4), ['Abraham_1', 'Isaac_1', 'Jacob_1', 'Joseph_1']); assert.equal(r.como, 'nodo');
  assert.deepEqual(j(N.rutaArbol(D, 'Bilhah_1')), Object.assign(j(N.rutaArbol(D, 'Jacob_1')), { id: 'Bilhah_1', como: 'conyuge' }));
  assert.equal(N.rutaArbol(D, 'Nadie'), null);
  const at = j(N.atajosLinea(D));
  assert.deepEqual(at.map(a => a.id), ['adan-abraham', 'abraham-jacob']);
  assert.deepEqual(at[1].ruta, ['Abraham_1', 'Isaac_1', 'Jacob_1']); assert.ok(at[1].extra.includes('Joseph_1'));
  assert.ok(N.lineaPrincipal(D).has('Jacob_1') && N.lineaPrincipal(D).has('Adam_1'));
  assert.deepEqual(j(N.atajosLinea({ personas: [{ id: 'X', nombre: 'X' }] })), []);
});
prueba('vidas: quien no tiene la cadena completa se omite y se cuenta', () => {
  assert.deepEqual(j(N.vidas(D, 'TM').omitidas), []);
  const Dx = Object.assign({}, D, { edades: D.edades.concat([{ persona: 'Jacob_1', tipo: 'total', tradicion: 'TM', valor: 147, ref: 'Gn 47:28' }]) });
  const v = j(N.vidas(Dx, 'TM'));
  assert.deepEqual(v.omitidas, ['Jacob_1']); assert.ok(!v.filas.some(f => f.id === 'Jacob_1'));
});
prueba('etiquetas por prioridad según zoom; nombres alternativos', () => {
  const items = [{ id: 'a', x: 100, y: 100, texto: 'Babel', prioridad: 3 }, { id: 'c', x: 300, y: 50, texto: 'Harán', prioridad: 9 }];
  assert.deepEqual(j(N.colocarEtiquetas(items, 400, 300, 1)).map(e => e.id), ['c']);
  assert.equal(N.etiquetasPorZoom(1, 100), 12); assert.equal(N.etiquetasPorZoom(2, 100), 48); assert.equal(N.etiquetasPorZoom(1, 5), 5);
  assert.ok(N.prioridadLugar(N.lugar(D, 'ur')) > N.prioridadLugar(N.lugar(D, 'haran')));
  const Dx = { personas: [{ id: 'Abraham_1', nombre: 'Abram', otros_nombres: ['Abraham'], refs: ['Gn 17:5'] }] };
  assert.equal(N.buscar(Dx, 'abraham')[0].id, 'Abraham_1');
  assert.deepEqual(j(N.segmentar(Dx, 'Gn 17:5', 'Y será tu nombre Abraham.')).filter(x => x.persona).map(x => x.texto), ['Abraham']);
});
console.log('Lectura acompañada');
prueba('pasaje de un ref (también cruzando capítulo) y respaldo por capítulos', () => {
  assert.equal(N.pasajeDe(D, 'Gn 4:19').id, 'ej-01');
  assert.equal(N.pasajeDe(D, 'Gn 6:1').id, 'ej-02');
  assert.equal(N.pasajeDe(D, 'Gn 9:1'), null);
  assert.deepEqual(j(N.versiculosDe(D, N.pasajeDe(D, 'Gn 5:1')).map(v => v.ref)), ['Gn 5:1', 'Gn 5:3', 'Gn 7:6']);
  const sin = { capitulos: [{ libro: 'Génesis', cap: 1, versiculos: [{ n: 1, texto: 'x' }, { n: 2, texto: 'y' }] }] };
  assert.deepEqual(j(N.pasajes(sin)[0]), { id: 'cap-1', inicio: 'Gn 1:1', fin: 'Gn 1:2', titulo: 'Génesis 1', titulo_origen: 'capitulo', resumen: '' });
  assert.equal(N.pasajeDe(sin, 'Gn 1:2').id, 'cap-1');
});
prueba('segmentación de un versículo con menciones', () => {
  const t = D.capitulos[0].versiculos[0].texto;
  const s = j(N.segmentar(D, 'Gn 4:1', t));
  assert.equal(s.map(x => x.texto).join(''), t);
  assert.deepEqual(s.filter(x => x.persona).map(x => [x.persona, x.texto]), [['Adam_1', 'Adam'], ['Eve_1', 'Eva'], ['Cain_1', 'Caín']]);
  const abel = j(N.segmentar(D, 'Gn 4:2', 'Y después parió a su hermano Abel.')); // sin menciones: por nombre
  assert.deepEqual(abel.filter(x => x.persona), [{ texto: 'Abel', persona: 'Abel_1' }]);
  const jabal = j(N.segmentar(D, 'Gn 4:20', 'Y Ada parió a Jabal.')); // mención fuera de rango ignorada
  assert.ok(jabal.some(x => x.persona === 'Jabal_1' && x.texto === 'Jabal'));
  assert.deepEqual(j(N.segmentar(D, 'Gn 9:9', '')), []);
});
prueba('contexto de una persona calculado de las relaciones', () => {
  assert.equal(N.contextoPersona(D, 'Cain_1'), 'hijo de Adán y Eva; esposo de Esposa de Caín');
  assert.equal(N.contextoPersona(D, 'Jabal_1'), 'hijo de Lamec y Ada');
  assert.equal(N.contextoPersona(D, 'Adah_1'), 'esposa de Lamec');
  assert.equal(N.contextoPersona(D, 'Nadie'), '');
});
prueba('contenido del acompañante para un ref', () => {
  const a = j(N.acompanante(D, ['Gn 4:19']));
  ['Lamech_1', 'Adah_1', 'Zillah_1'].forEach(id => assert.ok(a.personas.some(p => p.id === id), id));
  assert.equal(a.vinculos.length, 2);
  assert.equal(a.vinculos[0].cita, 'Y tomó para sí Lamech dos mujeres');
  const e = j(N.acompanante(D, 'Gn 5:3')).edades.find(x => x.persona === 'Adam_1' && x.tipo === 'al_engendrar');
  assert.equal(e.TM.valor, 130); assert.equal(e.LXX.valor, 230); assert.equal(e.difiere, true);
  assert.deepEqual(j(N.acompanante(D, ['Gn 4:17']).sinNombre), ['CainWife_1']);
  assert.equal(N.tieneApoyo(D, 'Gn 4:1'), true);
  assert.equal(N.tieneApoyo(D, 'Gn 5:1'), false);
  assert.deepEqual(j(N.acompanante({}, ['Gn 1:1'])), { personas: [], vinculos: [], edades: [], eventos: [], sinNombre: [], lugares: [] });
});
console.log('Lugares y mapa');
prueba('proyección ida y vuelta', () => {
  const P = N.proyeccion(ctx.BIBLIA_MAPA.bbox);
  assert.equal(P.latMedia, 32.5);
  for (const [lon, lat] of [[46.1, 30.96], [30, 24], [52, 41]]) {
    const [x, y] = N.proyectar(P, lon, lat), [lo, la] = N.desproyectar(P, x, y);
    assert.ok(Math.abs(lo - lon) < 1e-9 && Math.abs(la - lat) < 1e-9);
  }
  const [xa] = N.proyectar(P, 40, 30), [xb] = N.proyectar(P, 41, 30);
  assert.ok(Math.abs((xb - xa) - Math.cos(32.5 * Math.PI / 180)) < 1e-9, 'un grado de longitud se acorta por cos(lat media)');
  assert.equal(N.proyeccion(null).bbox.length, 4);
});
prueba('encuadre de un conjunto de puntos', () => {
  const P = N.proyeccion([30, 24, 52, 41]);
  const pts = [[46.1, 30.96], [39.03, 36.86]];
  const r = N.encuadre(P, pts, { margen: 0.1, minimo: 0 });
  pts.forEach(([lon, lat]) => { const [x, y] = N.proyectar(P, lon, lat); assert.ok(x > r.x && x < r.x + r.w && y > r.y && y < r.y + r.h); });
  assert.ok(Math.abs(r.h - (36.86 - 30.96) * 1.2) < 1e-9);
  const uno = N.encuadre(P, [[44, 33]], { margen: 0, minimo: 3 });
  assert.equal(uno.h, 3); assert.ok(Math.abs(uno.y + uno.h / 2 + 33) < 1e-9);
  const vacio = N.encuadre(P, [], { margen: 0 });
  assert.ok(Math.abs(vacio.h - 17) < 1e-9, 'sin puntos encuadra el bbox');
});
prueba('lugares de un ref y de un pasaje; confianza', () => {
  assert.deepEqual(j(N.lugaresDeRefs(D, ['Gn 4:16'])).sort(), ['eden', 'nod']);
  assert.deepEqual(j(N.lugaresDePasaje(D, N.pasajeDe(D, 'Gn 11:31'))).sort(), ['canaan', 'haran', 'ur']);
  assert.deepEqual(j(N.lugaresDePasaje(D, N.pasajeDe(D, 'Gn 5:1'))), []);
  assert.equal(N.confianzaLugar(N.lugar(D, 'ur')), 'alta');
  assert.equal(N.confianzaLugar(N.lugar(D, 'eden')), 'desconocida');
  assert.equal(N.confianzaLugar(N.lugar(D, 'roto')), 'desconocida');
  assert.equal(N.tieneApoyo(D, 'Gn 8:4'), true);
});
prueba('segmentación con personas y lugares mezclados sin solape', () => {
  const t = 'Y salió Caín de delante de Jehová, y habitó en tierra de Nod, al oriente de Edén.';
  const s = j(N.segmentar(D, 'Gn 4:16', t));
  assert.equal(s.map(x => x.texto).join(''), t);
  assert.deepEqual(s.filter(x => x.persona || x.lugar).map(x => x.persona ? 'p:' + x.texto : 'l:' + x.texto), ['p:Caín', 'l:Nod', 'l:Edén']);
  const t2 = 'Y salieron con ellos de Ur de los Caldeos, para ir á la tierra de Canaán: y vinieron hasta Harán.';
  const s2 = j(N.segmentar(D, 'Gn 11:31', t2));
  assert.equal(s2.map(x => x.texto).join(''), t2);
  assert.deepEqual(s2.filter(x => x.lugar).map(x => x.lugar), ['ur', 'canaan', 'haran']);
  // menciones solapadas: gana la que empieza antes (o la más larga)
  const Dx = { personas: [{ id: 'A', nombre: 'Ur' }], lugares: [{ id: 'u', nombre: 'Ur de los Caldeos' }],
    menciones: [{ ref: 'Gn 1:1', persona: 'A', inicio: 0, fin: 2 }], menciones_lugar: [{ ref: 'Gn 1:1', lugar: 'u', inicio: 0, fin: 17 }] };
  assert.deepEqual(j(N.segmentar(Dx, 'Gn 1:1', 'Ur de los Caldeos y más')), [{ texto: 'Ur de los Caldeos', lugar: 'u' }, { texto: ' y más' }]);
});
prueba('etiquetas del mapa sin solaparse', () => {
  const items = [{ id: 'a', x: 100, y: 100, texto: 'Babel', prioridad: 3 }, { id: 'b', x: 104, y: 102, texto: 'Borsippa', prioridad: 1 }, { id: 'c', x: 300, y: 50, texto: 'Harán', prioridad: 2 }, { id: 'd', x: 5, y: 5, texto: 'Muy al borde' }];
  const e = j(N.colocarEtiquetas(items, 400, 300));
  for (let i = 0; i < e.length; i++) for (let k = i + 1; k < e.length; k++) {
    const a = e[i].caja, b = e[k].caja;
    assert.ok(!(a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h), `${e[i].id} y ${e[k].id} se solapan`);
  }
  e.forEach(x => assert.ok(x.caja.x >= 0 && x.caja.x + x.caja.w <= 400));
  assert.ok(e.some(x => x.id === 'a') && e.some(x => x.id === 'c'));
});
prueba('primeras apariciones por pasaje', () => {
  const p1 = j(N.primerasApariciones(D, N.pasajeDe(D, 'Gn 4:1')));
  ['Cain_1', 'Abel_1', 'CainWife_1', 'Adah_1', 'Naamah_1'].forEach(id => assert.ok(p1.includes(id), id));
  assert.ok(!p1.includes('Eve_1') && !p1.includes('Adam_1'));
  assert.equal(p1[0], 'Cain_1');
  const p2 = j(N.primerasApariciones(D, N.pasajeDe(D, 'Gn 5:1')));
  assert.ok(p2.includes('Kenan_1') && !p2.includes('Seth_1'));
});
prueba('año del diluvio desde Adán por tradición (cálculo)', () => {
  assert.equal(N.anoDiluvio(D, 'TM').ano, 1656);
  assert.equal(N.anoDiluvio(D, 'LXX').ano, 2242);
  assert.equal(N.anoDiluvio({}, 'TM'), null);
});
prueba('cada vínculo del árbol conserva certeza y versículo', () => {
  const abel = N.construirBosque(D)[0].hijos.find(h => h.id === 'Abel_1');
  assert.equal(abel.vinculos[0].certeza, 'inferido');
  assert.equal(abel.vinculos[0].ref, 'Gn 4:2');
});
prueba('ruta TM Adán→Abraham omite a Cainán (solo LXX)', () => {
  const r = j(N.lineaPorTradicion(D, 'TM'));
  assert.equal(r[0], 'Adam_1'); assert.equal(r.at(-1), 'Abraham_1');
  assert.ok(!r.includes('Cainan_2')); assert.ok(r.includes('Shelah_1'));
});
prueba('ruta LXX incluye a Cainán entre Arfaxad y Sala', () => {
  const r = j(N.lineaPorTradicion(D, 'LXX'));
  const i = r.indexOf('Cainan_2');
  assert.ok(i > 0); assert.equal(r[i - 1], 'Arphaxad_1'); assert.equal(r[i + 1], 'Shelah_1');
});
prueba('línea combinada = LXX con nodos TM fusionados', () => {
  const r = j(N.lineaAdanAbraham(D));
  assert.equal(r.length, 15); // Adán…Abram con Cainán
  assert.ok(r.includes('Cainan_2'));
});
prueba('años acumulados desde Adán por tradición', () => {
  const tm = Object.fromEntries(j(N.anosDesdeAdan(D, 'TM')).map(f => [f.id, f]));
  const lxx = Object.fromEntries(j(N.anosDesdeAdan(D, 'LXX')).map(f => [f.id, f]));
  assert.equal(tm.Adam_1.nacimiento, 0); assert.equal(tm.Adam_1.muerte, 930);
  assert.equal(tm.Seth_1.nacimiento, 130); assert.equal(lxx.Seth_1.nacimiento, 230);
  assert.equal(tm.Enosh_1.nacimiento, 235); assert.equal(lxx.Enosh_1.nacimiento, 435);
  assert.equal(tm.Noah_1.nacimiento, 1056); // cronología masorética clásica
  assert.equal(lxx.Seth_1.muerte, 230 + 912); // total LXX deducido (205+707)
  assert.equal(tm.Shelah_1.nacimiento, 1056 + 500 + 100 + 35);
  assert.equal(lxx.Shelah_1.nacimiento, lxx.Cainan_2.nacimiento + 130);
  assert.equal(tm.Abraham_1.muerte, null);
});
prueba('si falta un eslabón, lo siguiente queda sin calcular', () => {
  const r = j(N.anosDesdeAdan(D, 'TM', ['Adam_1', 'Eve_1', 'Cain_1']));
  assert.equal(r[1].nacimiento, 130); assert.equal(r[2].nacimiento, null);
});
prueba('total derivado se marca como cálculo', () => {
  const e = j(N.edad(D, 'Seth_1', 'total', 'LXX'));
  assert.equal(e.valor, 912); assert.equal(e.derivado, true); assert.equal(e.certeza, 'calculo');
  assert.equal(N.edad(D, 'Seth_1', 'total', 'TM').derivado, false);
});
prueba('detección de diferencias TM/LXX', () => {
  assert.deepEqual(j(N.diferencias(D, 'Adam_1')), { al_engendrar: 'difiere', restantes: 'difiere', total: 'igual' });
  assert.equal(N.diferencias(D, 'Jared_1').al_engendrar, 'igual');
  assert.equal(N.diferencias(D, 'Lamech_2').total, 'difiere');
  assert.deepEqual(j(N.diferencias(D, 'Cainan_2')), { al_engendrar: 'solo_LXX', restantes: 'solo_LXX', total: 'solo_LXX' });
  assert.deepEqual(j(N.diferencias(D, 'Eve_1')), { al_engendrar: null, restantes: null, total: null });
});
prueba('orden de patriarcas sigue la genealogía', () => {
  const o = j(N.ordenPatriarcas(D));
  assert.equal(o[0], 'Adam_1'); assert.ok(o.indexOf('Cainan_2') > o.indexOf('Arphaxad_1'));
  assert.ok(o.indexOf('Shelah_1') > o.indexOf('Cainan_2'));
});
prueba('personas en un capítulo y búsqueda sin acentos', () => {
  const c5 = j(N.personasEnCapitulo(D, 5)).map(p => p.id);
  assert.ok(c5.includes('Adam_1') && c5.includes('Noah_1') && !c5.includes('Cain_1'));
  assert.equal(N.buscar(D, 'adan')[0].id, 'Adam_1');
  assert.deepEqual(j(N.parseRef('Gn 11:12')), { libro: 'Gn', cap: 11, v: 12 });
});
prueba('tolerancia: datos vacíos o incompletos no rompen', () => {
  const V = { personas: [], relaciones: [{ de: 'X_1', a: 'Y_1', tipo: 'padre' }, { de: null }], edades: [{ persona: 'Y_1', tipo: 'total', tradicion: 'TM', valor: '' }] };
  assert.equal(N.construirBosque(V).length, 1);
  assert.deepEqual(j(N.lineaPorTradicion(V, 'TM')), []);
  assert.equal(N.edad(V, 'Y_1', 'total', 'TM'), null);
  assert.deepEqual(j(N.construirBosque({})), []);
});

// Datos reales: datos/biblia.js (varios libros) si existe; si no, datos/genesis.js.
const real = [path.join(aqui, '..', 'datos', 'biblia.js'), path.join(aqui, '..', 'datos', 'genesis.js')].find(existsSync) || path.join(aqui, '..', 'datos', 'biblia.js');
console.log('Varios libros (ejemplo con Éxodo)');
{
  const CX = cargar(path.join(aqui, 'datos-ejemplo.js'), path.join(aqui, '..', 'app.js'));
  const NX = CX.BibliaNucleo, DX = CX.BIBLIA_EJEMPLO_EXODO(CX.BIBLIA_DATOS);
  prueba('refs con libro: lectura, orden y clave reversible', () => {
    assert.deepEqual(j(NX.parseRef('Ex 7:7')), { libro: 'Ex', cap: 7, v: 7 });
    assert.equal(NX.parseRef('Éxodo 7:7').libro, 'Ex'); assert.equal(NX.parseRef('éx 7').libro, 'Ex');
    assert.equal(NX.parseRef('4:1').libro, 'Gn', 'sin libro se entiende Génesis');
    assert.equal(NX.parseRef('LXX Gn 11:12').cap, 11);
    assert.ok(NX.clave('Ex 1:1') > NX.clave('Gn 50:26'));
    assert.notEqual(NX.clave('Ex 7:7'), NX.clave('Gn 7:7'));
    assert.equal(NX.refDeClave(NX.clave('Ex 7:7')), 'Ex 7:7');
  });
  prueba('libros de los datos o derivados de los capítulos', () => {
    assert.deepEqual(j(NX.libros(DX)).map(l => [l.id, l.nombre, l.capitulos]), [['Gn', 'Génesis', 50], ['Ex', 'Éxodo', 40]]);
    const sinL = Object.assign({}, DX); delete sinL.libros;
    assert.deepEqual(j(NX.libros(sinL)).map(l => [l.id, l.nombre]), [['Gn', 'Génesis'], ['Ex', 'Éxodo']]);
    assert.equal(NX.nombreLibro(sinL, 'Ex'), 'Éxodo');
    assert.equal(NX.alcance(DX).texto, 'Génesis 4–30 y Éxodo 2–7'); assert.equal(NX.alcance(DX).corto, 'Gn 4–30 y Ex 2–7');
    assert.deepEqual(j(NX.libros({})), []);
  });
  prueba('pasajes, versículos y plan por libro sin mezclar capítulos iguales', () => {
    assert.equal(NX.pasajeDe(DX, 'Ex 7:7').id, 'ex-02'); assert.equal(NX.pasajeDe(DX, 'Gn 7:6').id, 'ej-02');
    assert.deepEqual(j(NX.versiculosDe(DX, NX.pasajeDe(DX, 'Ex 7:7'))).map(v => v.ref), ['Ex 7:7']);
    assert.deepEqual(j(NX.versiculosDe(DX, NX.pasajeDe(DX, 'Gn 5:1'))).map(v => v.ref), ['Gn 5:1', 'Gn 5:3', 'Gn 7:6']);
    const ex = j(NX.seccionesPlan(DX, ['ex-01'], 'ex-02', 'Ex'));
    assert.deepEqual(ex.map(g => [g.titulo, g.total, g.leidos, g.libro]), [['Israel en Egipto (Ex 1–7)', 2, 1, 'Ex']]);
    assert.equal(ex[0].pasajes[0].n, 1, 'se numera dentro del libro');
    assert.equal(NX.seccionesPlan(DX, [], null, 'Gn').length, 3);
    assert.equal(NX.edadesEnEvento(DX, ['Ex 7:7']).length >= 1, true);
    assert.equal(NX.tieneApoyo(DX, 'Ex 7:7'), true);
    assert.deepEqual(j(NX.personasEnCapitulo(DX, 7, 'Ex')).map(p => p.id).sort(), ['Aaron_1', 'Moses_1']);
    const sin = { capitulos: [{ libro: 'Éxodo', cap: 1, versiculos: [{ n: 1, texto: 'x' }] }, { libro: 'Génesis', cap: 1, versiculos: [{ n: 1, texto: 'y' }] }] };
    assert.deepEqual(j(NX.pasajes(sin)).map(p => [p.id, p.inicio, p.titulo]), [['cap-1', 'Gn 1:1', 'Génesis 1'], ['cap-Ex-1', 'Ex 1:1', 'Éxodo 1']]);
  });
}

if (existsSync(real)) {
  console.log(`Datos reales (${path.basename(real)})`);
  const C2 = cargar(real, path.join(aqui, '..', 'app.js'));
  const N2 = C2.BibliaNucleo, D2 = C2.BIBLIA_DATOS;
  prueba('estructura básica y funciones sin excepciones', () => {
    assert.ok(D2 && Array.isArray(D2.capitulos));
    const b = N2.construirBosque(D2);
    const tm = N2.lineaPorTradicion(D2, 'TM'), lxx = N2.lineaPorTradicion(D2, 'LXX');
    console.log(`     capítulos ${D2.capitulos.length}, personas ${(D2.personas || []).length}, raíces ${b.length}, línea TM ${tm.length}, LXX ${lxx.length}`);
    assert.ok(tm.length > 0, 'hay línea Adán→Abraham');
    N2.ordenPatriarcas(D2).forEach(id => N2.diferencias(D2, id));
    ['TM', 'LXX'].forEach(t => N2.anosDesdeAdan(D2, t));
  });
  prueba('ninguna mujer de los datos reales queda fuera del árbol', () => {
    const s = N2.alcanzables(D2), m = N2.contarMujeres(D2);
    // En la pantalla Árbol: como nodo, cónyuge, madre o en la sección "sin parentesco registrado".
    const sp = N2.sinParentesco(D2);
    console.log(`     mujeres: ${m.conNombre} con nombre, ${m.sinNombre} sin nombre; personas sin parentesco ${sp.length} (con rol ${sp.filter(id => N2.persona(D2, id).rol).length})`);
    assert.deepEqual(j((D2.personas || []).filter(p => p.sexo === 'f' && !s.has(p.id) && !sp.includes(p.id)).map(p => p.id)), []);
    assert.deepEqual(j((D2.personas || []).filter(p => !N2.enPantallaArbol(D2, p.id)).map(p => p.id)), [], 'toda persona está en la pantalla Árbol');
  });
  prueba('lectura acompañada sobre los datos reales', () => {
    const ps = N2.pasajes(D2);
    let vs = 0, conPersona = 0;
    ps.forEach(p => N2.versiculosDe(D2, p).forEach(v => {
      vs++;
      const s = N2.segmentar(D2, v.ref, v.texto);
      assert.equal(s.map(x => x.texto).join(''), v.texto, v.ref);
      if (s.some(x => x.persona)) conPersona++;
      N2.acompanante(D2, [v.ref]);
    }));
    const lu = D2.lugares || [];
    console.log(`     lugares ${lu.length} (sin ubicación ${lu.filter(l => N2.confianzaLugar(l) === 'desconocida').length}), menciones de lugar ${(D2.menciones_lugar || []).length}`);
    console.log(`     pasajes ${ps.length} (${(D2.pasajes || []).length ? 'de los datos' : 'por capítulo'}), versículos ${vs}, con nombres resaltados ${conPersona}, menciones ${(D2.menciones || []).length}`);
    assert.ok(vs > 0);
  });
  prueba('escala: secciones, edades en_evento, atajos, árbol y tiempos', () => {
    // Datos frescos: el índice se construye dentro de la medición.
    const C3 = cargar(real, path.join(aqui, '..', 'app.js')), N3 = C3.BibliaNucleo, D3 = C3.BIBLIA_DATOS;
    const t0 = performance.now();
    N3.indice(D3); const tIdx = performance.now() - t0;
    const t1 = performance.now();
    const secs = N3.seccionesPlan(D3, [], null);
    const ini = N3.arbolInicial(D3, 2), at = N3.atajosLinea(D3), ev = N3.edadesEnEvento(D3);
    N3.ordenPatriarcas(D3); ['TM', 'LXX'].forEach(t => N3.vidas(D3, t));
    const tTab = performance.now() - t1;
    const t2 = performance.now();
    N3.pasajes(D3).forEach(p => { const vs = N3.versiculosDe(D3, p); N3.acompanante(D3, vs.map(v => v.ref)); vs.forEach(v => N3.tieneApoyo(D3, v.ref)); });
    const tPas = (performance.now() - t2) / Math.max(1, N3.pasajes(D3).length);
    const M = N3.mapaArbol(D3);
    const sinRuta = (D3.personas || []).filter(p => !N3.rutaArbol(D3, p.id)).length;
    const jac = N3.idJacob(D3), gj = jac && N3.nodoArbol(D3, jac) ? N3.hijosPorMadre(D3, N3.nodoArbol(D3, jac)) : [];
    console.log(`     secciones ${secs.length}${secs[0] && secs[0].titulo ? '' : ' (los pasajes aún no traen sección)'}, edades en_evento ${ev.length}, atajos ${at.map(a => a.id).join(', ') || 'ninguno'}`);
    console.log(`     árbol: ${M.nodos.size} nodos, ${ini.size} desplegados al inicio, ${sinRuta} personas sin lugar en el árbol${jac ? `, hijos de Jacob en ${gj.length} grupo(s)` : ''}`);
    console.log(`     tiempos: índice ${tIdx.toFixed(0)} ms, primeras pestañas ${tTab.toFixed(0)} ms, acompañante por pasaje ${tPas.toFixed(1)} ms`);
    assert.ok(secs.length >= 1 && secs.reduce((s, g) => s + g.total, 0) === N3.pasajes(D3).length);
    assert.ok(tIdx + tTab < 1500, 'abrir la app no debe bloquear');
    assert.ok(tPas < 100, 'un pasaje con su acompañante se calcula en menos de 100 ms');
  });
  prueba('cronología real: línea, cadenas y vecinos sin excepciones', () => {
    const C = N2.crono(D2);
    if (!C) { console.log('     (los datos aún no traen cronologia: se omite)'); return; }
    const e = N2.elecciones(D2, {}), combos = ['TM', 'LXX'].map(t => N2.combinacion(D2, t, e));
    const t0 = performance.now();
    combos.forEach(c => { N2.lineaDeTiempo(D2, c); C.eventos.forEach(ev => { const cad = N2.cadenaEvento(D2, ev.id, c); assert.equal(cad.at(-1).evento, ev.id); N2.vivosEn(D2, N2.anioEvento(D2, ev.id, c), c); }); });
    N2.pasajes(D2).forEach(p => { if (!N2.eventosDePasaje(D2, p).length) N2.vecinosFechados(D2, p.inicio, p.fin, combos[0]); });
    const conAnio = C.eventos.filter(ev => N2.anioEvento(D2, ev.id, combos[0]) !== null).length;
    const dil = C.eventos.find(N2.esDiluvio);
    console.log(`     cronología: ${C.eventos.length} sucesos (${conAnio} con año en ${combos[0]}), ${C.supuestos.length} supuestos, ${C.hitos.length} hitos sin fecha; diluvio ${dil ? 'TM ' + N2.anioEvento(D2, dil.id, combos[0]) + ' / LXX ' + N2.anioEvento(D2, dil.id, combos[1]) : 'no encontrado'}; ${(performance.now() - t0).toFixed(0)} ms`);
  });
  console.log('Personajes (colección y curiosidades, datos reales)');
  prueba('desbloqueo: leer Gn 5 incluye a Set y Enós; lo ya obtenido no se repite', () => {
    const gn5 = N2.pasajes(D2).filter(p => N2.parseRef(p.inicio).libro === 'Gn' && (N2.parseRef(p.inicio).cap === 5 || N2.parseRef(p.fin).cap === 5)).map(p => p.id);
    assert.ok(gn5.length >= 1);
    const col = N2.coleccion(D2, gn5);
    assert.ok(col.has('Seth_1') && col.has('Enosh_1'), 'Set y Enós');
    assert.ok(!col.has('Abram_1'), 'Abraham no aparece en Gn 5');
    const nuevas = j(N2.nuevasAlLeer(D2, [], gn5[0]));
    assert.ok(nuevas.includes('Seth_1') && nuevas.includes('Enosh_1'));
    const p4 = N2.pasajeDe(D2, 'Gn 4:26').id;
    assert.ok(!N2.nuevasAlLeer(D2, [p4], gn5[0]).includes('Enosh_1'), 'Enós ya se obtuvo en Gn 4');
    const f = j(N2.fichasColeccion(D2, gn5));
    assert.equal(f.length, N2.coleccionables(D2).length);
    assert.ok(f.every(x => !N2.persona(D2, x.id).sin_nombre), 'las alusiones sin nombre no son fichas');
    const set = f.find(x => x.id === 'Seth_1'); assert.equal(set.desbloqueada, true); assert.equal(set.primeraCap, 'Gn 4');
    assert.equal(f.find(x => x.id === 'Abram_1').desbloqueada, false);
    assert.equal(N2.rareza(D2, 'Abram_1').id, 'protagonista');
    assert.ok(N2.pasajesDePersona(D2, 'Seth_1').some(x => x.pasaje.id === gn5[0]));
    console.log(`     coleccionables ${f.length}; rareza: ${N2.RAREZAS.map(r => `${r.nombre} ${f.filter(x => x.rareza.id === r.id).length}`).join(', ')}`);
  });
  // Catálogo de juego (pruebas/juego-ejemplo.js con los datos reales): desbloqueo por capítulo, NPC, objetos y escenarios.
  const CJ = cargar(real, path.join(aqui, 'juego-ejemplo.js'), path.join(aqui, '..', 'app.js'));
  const NJ = CJ.BibliaNucleo, DJ = CJ.BIBLIA_DATOS, J = CJ.BIBLIA_JUEGO;
  const deCap = (cap, lb = 'Gn') => j(NJ.pasajes(DJ).filter(p => { const a = NJ.parseRef(p.inicio), b = NJ.parseRef(p.fin); return a.libro === lb && a.cap <= cap && b.cap >= cap; }).map(p => p.id));
  prueba('juego: Abraham «en curso» con Gn 24 leído y desbloqueado al leer todo Gn 25', () => {
    const gn24 = deCap(24), gn25 = deCap(25);
    assert.deepEqual(gn25, ['gn-52', 'gn-53']);
    const e = j(NJ.estadoPersonaje(DJ, J, 'Abram_1', gn24));
    assert.equal(e.estado, 'en-curso'); assert.equal(e.capitulo, 'Gn 25'); assert.equal(e.leidos, 4); assert.ok(e.total > 4); assert.equal(e.nivel, 10);
    assert.equal(NJ.estadoPersonaje(DJ, J, 'Abram_1', gn24.concat('gn-52')).estado, 'en-curso', 'falta la segunda mitad de Gn 25');
    assert.equal(NJ.estadoPersonaje(DJ, J, 'Abram_1', gn24.concat(gn25)).estado, 'obtenido');
    assert.equal(NJ.estadoPersonaje(DJ, J, 'Abram_1', gn25).estado, 'obtenido', 'terminar el capítulo basta');
    assert.equal(NJ.estadoPersonaje(DJ, J, 'Abram_1', []).estado, 'bloqueado');
    assert.ok(!NJ.coleccion(DJ, gn24, J).has('Abram_1') && NJ.coleccion(DJ, gn24, J).has('Isaac_1'), 'sin entrada en el catálogo: como antes');
    assert.ok(NJ.coleccion(DJ, gn24, null).has('Abram_1'), 'sin catálogo, primera mención');
    assert.deepEqual(j(NJ.nuevasAlLeer(DJ, gn24.concat('gn-52'), 'gn-53', J)).includes('Abram_1'), true);
    assert.ok(!j(NJ.nuevasAlLeer(DJ, [], 'gn-48', J)).includes('Abram_1'));
    const f = j(NJ.fichasColeccion(DJ, gn24, J)).find(x => x.id === 'Abram_1');
    assert.equal(f.estado, 'en-curso'); assert.equal(f.desbloqueada, false);
  });
  prueba('juego: Adán listo al terminar Gn 3; NPC al leer su primera mención; genealogía sin apariciones', () => {
    assert.equal(NJ.estadoPersonaje(DJ, J, 'Adam_1', ['gn-03']).estado, 'en-curso');
    assert.equal(NJ.estadoPersonaje(DJ, J, 'Adam_1', ['gn-05', 'gn-06']).estado, 'obtenido');
    const n0 = j(NJ.estadoPersonaje(DJ, J, 'Mahalalel_1', ['gn-10']));
    assert.equal(n0.estado, 'bloqueado'); assert.equal(n0.npc, true); assert.equal(n0.nivel, 0);
    assert.equal(NJ.estadoPersonaje(DJ, J, 'Mahalalel_1', ['gn-11']).estado, 'obtenido');
    assert.ok(NJ.esGenealogia(J, NJ.pasajeDe(DJ, 'Gn 5:1')) && NJ.esGenealogia(J, NJ.pasajeDe(DJ, 'Gn 5:30')));
    assert.ok(!NJ.esGenealogia(J, NJ.pasajeDe(DJ, 'Gn 6:1')) && !NJ.esGenealogia(null, NJ.pasajeDe(DJ, 'Gn 5:1')));
    assert.deepEqual(j(NJ.genealogiasDe(J, NJ.pasajeDe(DJ, 'Gn 25:1'))).map(g => g.id), ['gn-25-ismael']);
  });
  prueba('juego: objeto obtenido al leer Gn 6 (arca de Noé); escenario Edén; relacionados', () => {
    const p = NJ.pasajeDe(DJ, 'Gn 6:14').id;
    assert.equal(NJ.estadoCosa(DJ, J, 'objetos', 'arca-noe', []).estado, 'bloqueado');
    assert.equal(NJ.estadoCosa(DJ, J, 'objetos', 'arca-noe', [p]).estado, 'obtenido');
    assert.equal(NJ.estadoCosa(DJ, J, 'objetos', 'arca-noe', []).primeraCap, 'Gn 6');
    const ob = j(NJ.fichasCosas(DJ, J, 'objetos', [p]));
    assert.deepEqual(ob.map(x => [x.id, x.desbloqueada]), [['arca-noe', true], ['arca-pacto', false]]);
    assert.equal(NJ.estadoCosa(DJ, J, 'escenarios', 'eden', ['gn-03']).estado, 'obtenido');
    const nu = j(NJ.nuevosAlLeer(DJ, J, [], p));
    assert.deepEqual(nu.objetos, ['arca-noe']); assert.deepEqual(nu.escenarios, []);
    assert.deepEqual(j(NJ.relacionadosJuego(J, 'persona', 'Adam_1')), { objetos: [], escenarios: ['eden'] });
    assert.deepEqual(j(NJ.fichasCosas(DJ, null, 'objetos', [p])), []); assert.equal(NJ.estadoCosa(DJ, {}, 'objetos', 'arca-noe', []), null);
  });
  prueba('juego: una ficha no obtenida abierta desde un enlace no muestra su contenido', () => {
    const v0 = j(NJ.vistaFichaJuego(DJ, J, 'objetos', 'arca-pacto', []));
    assert.equal(v0.visible, false); assert.equal(v0.primeraCap, 'Ex 25');
    assert.equal(NJ.vistaFichaJuego(DJ, J, 'objetos', 'arca-pacto', [NJ.pasajeDe(DJ, 'Ex 25:10').id]).visible, true);
    const a = j(NJ.vistaFichaJuego(DJ, J, 'personajes', 'Abram_1', deCap(24)));
    assert.equal(a.visible, false); assert.equal(a.estado, 'en-curso'); assert.equal(a.leidos, 4); assert.equal(a.primeraCap, 'Gn 11');
    assert.equal(NJ.vistaFichaJuego(DJ, J, 'personajes', 'Abram_1', deCap(24).concat(deCap(25))).visible, true);
    assert.equal(NJ.vistaFichaJuego(DJ, J, 'escenarios', 'eden', []).visible, false);
    assert.equal(NJ.vistaFichaJuego(DJ, J, 'personajes', 'Isaac_1', []), null, 'sin entrada: la ficha como siempre');
    assert.equal(NJ.vistaFichaJuego(DJ, null, 'objetos', 'arca-noe', []), null);
  });
  prueba('juego: perfil niño pliega el dato de una parte marcada como alta; las citas son literales', () => {
    const C = { marcas: [{ desde: 'Gn 9:20', hasta: 'Gn 9:27', categoria: 'sexual', nivel: 'alto' }] };
    assert.equal(NJ.datoPlegado({ tipo: 'nino' }, C, 'Gn 9:20'), true);
    assert.equal(NJ.datoPlegado({ tipo: 'adulto' }, C, 'Gn 9:20'), false);
    assert.equal(NJ.datoPlegado({ tipo: 'nino' }, C, 'Gn 9:29'), false);
    const todos = [].concat(...Object.values(J.personajes).map(e => e.datos || []), ...['objetos', 'escenarios'].map(g => [].concat(...Object.values(J[g]).map(e => e.datos || []))));
    todos.forEach(x => assert.ok(NJ.textoVerso(DJ, x.ref).includes(x.cita), `${x.ref}: «${x.cita}»`));
  });
  const realJ = path.join(aqui, '..', 'datos', 'juego.js');
  if (existsSync(realJ)) prueba('juego real (datos/juego.js): estados sin excepciones y coherentes', () => {
    const CR = cargar(real, realJ, path.join(aqui, '..', 'app.js')), NR = CR.BibliaNucleo, DR = CR.BIBLIA_DATOS, JR = CR.BIBLIA_JUEGO;
    assert.ok(NR.juegoValido(JR));
    const todos = NR.pasajes(DR).map(p => p.id);
    const f0 = j(NR.fichasColeccion(DR, [], JR)), f1 = j(NR.fichasColeccion(DR, todos, JR));
    assert.ok(f0.every(x => !x.desbloqueada)); assert.ok(f1.every(x => x.desbloqueada), 'todo leído: todo obtenido');
    ['objetos', 'escenarios'].forEach(g => assert.ok(j(NR.fichasCosas(DR, JR, g, todos)).every(x => x.desbloqueada), g));
    const ab = NR.estadoPersonaje(DR, JR, 'Abram_1', deCap(24));
    assert.ok(['en-curso', 'obtenido'].includes(ab.estado));
    console.log(`     catálogo real: ${f1.filter(x => x.juego).length} personajes con entrada, ${f1.filter(x => x.npc).length} NPC; objetos ${NR.fichasCosas(DR, JR, 'objetos', []).length}, escenarios ${NR.fichasCosas(DR, JR, 'escenarios', []).length}`);
  });
  prueba('curiosidades (cálculo): Noé y Abraham 58 años; Matusalén muere en 1656 (TM, Taré 70)', () => {
    const tm = N2.combinacion(D2, 'TM', { tare: 'tare70' }), cs = j(N2.curiosidades(D2, tm));
    const sol = cs.find(c => c.id === 'solape|Noah_1|Abram_1');
    assert.ok(sol, 'existe el solape Noé–Abraham'); assert.equal(sol.valor, 58);
    assert.ok(sol.pasos.length >= 4 && sol.refs.length >= 2, 'con pasos y versículos');
    const mat = cs.find(c => c.tipo === 'muerte-evento' && c.personas[0] === 'Methuselah_1');
    assert.ok(mat && mat.valor === 1656 && /diluvio/i.test(mat.texto));
    assert.equal(N2.vidasCrono(D2, tm).get('Methuselah_1').muerte, 1656);
    assert.ok(cs.some(c => c.tipo === 'longevo' && c.protagonistas[0] === 'Methuselah_1' && c.valor === 969));
    assert.ok(cs.some(c => c.tipo === 'sobrevive' && c.personas[0] === 'Shem_1' && c.personas.includes('Abram_1')), 'Sem sobrevive a Abraham');
    // Con la LXX el diluvio y la muerte de Matusalén no coinciden: la curiosidad no aparece.
    const lxx = j(N2.curiosidades(D2, N2.combinacion(D2, 'LXX', {})));
    assert.ok(!lxx.some(c => c.tipo === 'muerte-evento' && c.personas[0] === 'Methuselah_1'));
    assert.ok(N2.curiosidadesDe(D2, 'Noah_1', tm).some(c => c.id === 'solape|Noah_1|Abram_1'));
  });
  prueba('«¿Sabías que…?»: máx. 2 por pasaje, nunca la misma en pasajes seguidos', () => {
    const tm = N2.combinacion(D2, 'TM', {}), S = N2.sabiasQue(D2, tm), ps = N2.pasajes(D2);
    let prev = [];
    ps.forEach(p => {
      const ids = S.get(p.id).map(c => c.id);
      assert.ok(ids.length <= 2);
      assert.ok(!ids.some(id => prev.includes(id)), p.id);
      prev = ids;
    });
    const gn12 = S.get(N2.pasajeDe(D2, 'Gn 5:27').id).map(c => c.tipo);
    assert.ok(gn12.includes('muerte-evento'), 'Matusalén y el diluvio, donde muere');
  });
  prueba('profundizar: enlaces externos con búsqueda estable', () => {
    const e = j(N2.enlacesExternos(D2, 'Methuselah_1'));
    assert.deepEqual(e.map(x => x.id), ['wikipedia', 'easton', 'smith']);
    assert.ok(e[0].url.startsWith('https://es.wikipedia.org/w/index.php?search=') && e[0].url.includes(encodeURIComponent('Matusalén personaje bíblico')));
    assert.ok(e[1].url.includes('Methuselah') && e[1].url.includes('prefix='));
    assert.ok(e[2].url.endsWith('?letter=m'));
    // Tolerancia: datos vacíos no rompen las funciones de personajes.
    assert.deepEqual(j(N2.curiosidades({}, 'TM')), []); assert.deepEqual(j(N2.fichasColeccion({}, [])), []);
    assert.deepEqual(j(N2.nuevasAlLeer({}, [], 'x')), []); assert.equal(N2.sabiasQue({}, 'TM').size, 0);
  });
  if ((D2.libros || []).some(l => l.id === 'Lv')) {
    prueba('Levítico: selector de libro y plan por secciones', () => {
      assert.deepEqual(j(N2.libros(D2)).map(l => l.id).slice(0, 3), ['Gn', 'Ex', 'Lv']);
      assert.equal(N2.nombreLibro(D2, 'Lv'), 'Levítico');
      assert.equal(N2.parseRef('Levítico 24:11').libro, 'Lv');
      assert.ok(N2.clave('Lv 1:1') > N2.clave('Ex 40:38'));
      const s = j(N2.seccionesPlan(D2, ['lv-01'], 'lv-02', 'Lv'));
      assert.equal(s.length, 6); assert.ok(s.every(g => g.libro === 'Lv'));
      assert.equal(s.reduce((n, g) => n + g.total, 0), D2.pasajes.filter(p => p.libro === 'Lv').length);
      assert.equal(s[0].pasajes[0].n, 1, 'se numera dentro del libro'); assert.equal(s[0].leidos, 1);
    });
    prueba('Levítico: lector (pasajes sin huecos, nombres resaltados)', () => {
      const ps = N2.pasajes(D2).filter(p => N2.libroDe(p) === 'Lv');
      const vs = ps.flatMap(p => j(N2.versiculosDe(D2, p)).map(v => v.ref));
      assert.equal(vs.length, 859); assert.equal(new Set(vs).size, 859);
      assert.equal(vs[0], 'Lv 1:1'); assert.equal(vs[vs.length - 1], 'Lv 27:34');
      assert.equal(N2.pasajeDe(D2, 'Lv 24:11').titulo, 'El blasfemo');
      const ids = j(N2.personasEnCapitulo(D2, 10, 'Lv')).map(p => p.id);
      ['Nadab_1', 'Abihu_1', 'Mishael_1', 'Elzaphan_1', 'Uzziel_1'].forEach(id => assert.ok(ids.includes(id), id));
      const v = j(N2.versiculosDe(D2, N2.pasajeDe(D2, 'Lv 24:11'))).find(x => x.ref === 'Lv 24:11');
      const seg = j(N2.segmentar(D2, v.ref, v.texto));
      assert.deepEqual(seg.filter(x => x.persona).map(x => [x.texto, x.persona]),
        [['Moisés', 'Moses_1'], ['Selomith', 'Shelomith_1'], ['Dribi', 'Dibri_1'], ['Dan', 'Dan_1']]);
    });
    const rc = path.join(aqui, '..', 'datos', 'contenido.js');
    if (existsSync(rc)) prueba('Levítico: marcas de contenido (Nadab y Abiú, el blasfemo)', () => {
      const cr = cargar(rc, path.join(aqui, '..', 'app.js')), NC = cr.BibliaNucleo, CR = cr.BIBLIA_CONTENIDO, nino = { tipo: 'nino' };
      assert.equal(NC.marcaDe(CR, 'Lv 10:1').categoria, 'violencia');
      assert.equal(NC.accionVerso(CR, nino, 'Lv 24:16').accion, 'nota');
      assert.equal(NC.marcaDe(CR, 'Lv 10:3'), null);
      assert.equal(NC.marcaDe(CR, 'Lv 1:5'), null, 'los sacrificios no se marcan (misma escala que Éxodo)');
    });
  }
  if ((D2.libros || []).some(l => l.id === 'Nm')) {
    prueba('Números: selector, plan por 8 secciones y lector sin huecos (versículos vacíos con nota)', () => {
      assert.deepEqual(j(N2.libros(D2)).map(l => l.id).slice(0, 4), ['Gn', 'Ex', 'Lv', 'Nm']);
      assert.equal(N2.nombreLibro(D2, 'Nm'), 'Números');
      assert.equal(N2.parseRef('Números 13:17').libro, 'Nm');
      assert.ok(N2.clave('Nm 1:1') > N2.clave('Lv 27:34'));
      const s = j(N2.seccionesPlan(D2, ['nm-01'], 'nm-02', 'Nm'));
      assert.equal(s.length, 8); assert.ok(s.every(g => g.libro === 'Nm'));
      assert.equal(s.reduce((n, g) => n + g.total, 0), D2.pasajes.filter(p => p.libro === 'Nm').length);
      const vs = N2.pasajes(D2).filter(p => N2.libroDe(p) === 'Nm').flatMap(p => j(N2.versiculosDe(D2, p)));
      assert.equal(vs.length, 1288); assert.equal(new Set(vs.map(v => v.ref)).size, 1288);
      assert.equal(vs[0].ref, 'Nm 1:1'); assert.equal(vs[vs.length - 1].ref, 'Nm 36:13');
      const v = vs.find(x => x.ref === 'Nm 12:16');
      assert.equal(v.texto, ''); assert.ok(/Nm 13:1/.test(v.nota), 'el versículo vacío dice dónde está su texto');
      assert.equal(vs.find(x => x.ref === 'Nm 12:15').nota, undefined);
    });
    prueba('Números: homónimos en el lector (Coré, Eliab, Milca, Hur, Josué = Oseas)', () => {
      const seg = r => { const v = j(N2.versiculosDe(D2, N2.pasajeDe(D2, r))).find(x => x.ref === r); return j(N2.segmentar(D2, r, v.texto)).filter(x => x.persona).map(x => [x.texto, x.persona]); };
      const s161 = seg('Nm 16:1');
      assert.deepEqual(s161.slice(0, 4), [['CORÉ', 'Korah_3'], ['Ishar', 'Izhar_1'], ['Coath', 'Kohath_1'], ['Leví', 'Levi_1']]);
      assert.ok(s161.some(x => x[0] === 'Eliab' && x[1] === 'Eliab_2'), 'Eliab de Rubén, no el de Zabulón');
      assert.ok(seg('Nm 27:1').some(x => x[0] === 'Milca' && x[1] === 'Milcah_2'), 'Milca hija de Zelofehad');
      assert.ok(seg('Nm 31:8').some(x => x[0] === 'Hur' && x[1] === 'Hur_2'), 'Hur rey de Madián');
      assert.ok(seg('Nm 13:17').some(x => x[0] === 'Oseas' && x[1] === 'Joshua_1'));
    });
    prueba('Números: mapa (Cades, monte Hor) y tiempo (muerte de Aarón, 123 años)', () => {
      const ls = j(N2.lugaresDePasaje(D2, N2.pasajeDe(D2, 'Nm 20:22')));
      assert.ok(ls.includes('monte-hor'), 'monte Hor en el pasaje de la muerte de Aarón');
      assert.ok(j(N2.lugaresDeRefs(D2, ['Nm 20:1'])).includes('cades'));
      assert.ok(['alta', 'media', 'baja'].includes(N2.confianzaLugar(N2.lugar(D2, 'monte-hor'))));
      const tm = 'TM|tare70|sem2|egipto';
      assert.equal(N2.anioEvento(D2, 'ev-muerte-aaron', tm) - N2.anioEvento(D2, 'ev-nac-aaron', tm), 123);
      assert.equal(N2.anioEvento(D2, 'ev-censo-sinai', tm) - N2.anioEvento(D2, 'ev-salida-egipto', tm), 1);
      assert.ok(j(N2.eventosDePasaje(D2, N2.pasajeDe(D2, 'Nm 33:38'))).some(e => e.id === 'ev-muerte-aaron'));
    });
    const rc2 = path.join(aqui, '..', 'datos', 'contenido.js');
    if (existsSync(rc2)) prueba('Números: marcas de contenido (Madián alta, Coré medio)', () => {
      const cr = cargar(rc2, path.join(aqui, '..', 'app.js')), NC = cr.BibliaNucleo, CR = cr.BIBLIA_CONTENIDO;
      assert.equal(NC.marcaDe(CR, 'Nm 31:17').nivel, 'alto');
      assert.equal(NC.marcaDe(CR, 'Nm 16:32').categoria, 'violencia'); assert.equal(NC.marcaDe(CR, 'Nm 16:32').nivel, 'medio');
      assert.equal(NC.marcaDe(CR, 'Nm 5:20').categoria, 'sexual');
      assert.equal(NC.marcaDe(CR, 'Nm 6:24'), null);
    });
  }
  if ((D2.libros || []).some(l => l.id === 'Dt')) {
    prueba('Deuteronomio: selector, plan por 7 secciones y lector sin huecos (numeración inglesa, sin vacíos)', () => {
      assert.deepEqual(j(N2.libros(D2)).map(l => l.id).slice(0, 5), ['Gn', 'Ex', 'Lv', 'Nm', 'Dt']);
      assert.equal(N2.nombreLibro(D2, 'Dt'), 'Deuteronomio');
      assert.equal(N2.parseRef('Deuteronomio 34:7').libro, 'Dt');
      assert.ok(N2.clave('Dt 1:1') > N2.clave('Nm 36:13'));
      const s = j(N2.seccionesPlan(D2, ['dt-01'], 'dt-02', 'Dt'));
      assert.equal(s.length, 7); assert.ok(s.every(g => g.libro === 'Dt'));
      assert.equal(s.reduce((n, g) => n + g.total, 0), D2.pasajes.filter(p => p.libro === 'Dt').length);
      const vs = N2.pasajes(D2).filter(p => N2.libroDe(p) === 'Dt').flatMap(p => j(N2.versiculosDe(D2, p)));
      assert.equal(vs.length, 959); assert.equal(new Set(vs.map(v => v.ref)).size, 959);
      assert.equal(vs[0].ref, 'Dt 1:1'); assert.equal(vs[vs.length - 1].ref, 'Dt 34:12');
      assert.ok(vs.every(v => v.texto), 'ningún versículo vacío');
      assert.ok(/^Cuidaréis/.test(vs.find(x => x.ref === 'Dt 12:32').texto) && /^ESTAS son las palabras del pacto/.test(vs.find(x => x.ref === 'Dt 29:1').texto));
    });
    prueba('Deuteronomio: personas compartidas en el lector (Josué, Datán y Abiram, Balaam, Og, Eleazar)', () => {
      const seg = r => { const v = j(N2.versiculosDe(D2, N2.pasajeDe(D2, r))).find(x => x.ref === r); return j(N2.segmentar(D2, r, v.texto)).filter(x => x.persona).map(x => [x.texto, x.persona]); };
      assert.deepEqual(seg('Dt 34:9').slice(0, 2), [['Josué', 'Joshua_1'], ['Nun', 'Nun_1']]);
      assert.deepEqual(seg('Dt 11:6').slice(0, 3), [['Dathán', 'Dathan_1'], ['Abiram', 'Abiram_1'], ['Eliab', 'Eliab_2']]);
      assert.ok(seg('Dt 23:4').some(x => x[0] === 'Balaam' && x[1] === 'Balaam_1'));
      assert.ok(seg('Dt 3:1').some(x => x[0] === 'Og' && x[1] === 'Og_1'));
      assert.ok(seg('Dt 10:6').some(x => x[0] === 'Eleazar' && x[1] === 'Eleazar_1'));
      assert.ok(!seg('Dt 32:9').some(x => x[1] === 'Jacob_1'), '«Jacob» como pueblo no se marca');
    });
    prueba('Deuteronomio: mapa (Nebo, Pisga, Ebal, Gerizim, refugio) y tiempo (Moisés muere a los 120)', () => {
      const ls = j(N2.lugaresDePasaje(D2, N2.pasajeDe(D2, 'Dt 34:1')));
      ['monte-nebo', 'pisga', 'campos-de-moab', 'jerico'].forEach(id => assert.ok(ls.includes(id), id));
      assert.ok(['monte-ebal', 'monte-gerizim'].every(id => j(N2.lugaresDeRefs(D2, ['Dt 11:29'])).includes(id)));
      assert.ok(['beser', 'ramot-galaad', 'golan'].every(id => j(N2.lugaresDeRefs(D2, ['Dt 4:43'])).includes(id)));
      const tm = 'TM|tare70|sem2|egipto';
      assert.equal(N2.anioEvento(D2, 'ev-muerte-moises', tm) - N2.anioEvento(D2, 'ev-nac-moises', tm), 120);
      assert.equal(N2.anioEvento(D2, 'ev-discursos-moab', tm) - N2.anioEvento(D2, 'ev-salida-egipto', tm), 40);
      assert.ok(j(N2.eventosDePasaje(D2, N2.pasajeDe(D2, 'Dt 34:5'))).some(e => e.id === 'ev-muerte-moises'));
    });
    const rc3 = path.join(aqui, '..', 'datos', 'contenido.js');
    if (existsSync(rc3)) prueba('Deuteronomio: marcas de contenido (asedio alto, Sehón alto, Shemá sin marca)', () => {
      const cr = cargar(rc3, path.join(aqui, '..', 'app.js')), NC = cr.BibliaNucleo, CR = cr.BIBLIA_CONTENIDO;
      assert.equal(NC.marcaDe(CR, 'Dt 28:53').nivel, 'alto'); assert.equal(NC.marcaDe(CR, 'Dt 2:34').nivel, 'alto');
      assert.equal(NC.marcaDe(CR, 'Dt 21:20').categoria, 'crueldad'); assert.equal(NC.marcaDe(CR, 'Dt 22:25').categoria, 'sexual');
      assert.equal(NC.marcaDe(CR, 'Dt 6:4'), null);
    });
  }
  if ((D2.libros || []).some(l => l.id === 'Jos')) {
    prueba('Josué: selector, plan por 6 secciones y lector sin huecos (658 versículos, con Jos 21:36-37)', () => {
      assert.deepEqual(j(N2.libros(D2)).map(l => l.id).slice(0, 6), ['Gn', 'Ex', 'Lv', 'Nm', 'Dt', 'Jos']);
      assert.equal(N2.nombreLibro(D2, 'Jos'), 'Josué');
      assert.equal(N2.parseRef('Josué 24:29').libro, 'Jos');
      assert.ok(N2.clave('Jos 1:1') > N2.clave('Dt 34:12'));
      const s = j(N2.seccionesPlan(D2, ['jos-01'], 'jos-02', 'Jos'));
      assert.equal(s.length, 6); assert.ok(s.every(g => g.libro === 'Jos'));
      const vs = N2.pasajes(D2).filter(p => N2.libroDe(p) === 'Jos').flatMap(p => j(N2.versiculosDe(D2, p)));
      assert.equal(vs.length, 658); assert.equal(new Set(vs.map(v => v.ref)).size, 658);
      assert.equal(vs[0].ref, 'Jos 1:1'); assert.equal(vs[vs.length - 1].ref, 'Jos 24:33');
      assert.ok(/^Y de la tribu de Rubén/.test(vs.find(x => x.ref === 'Jos 21:36').texto), 'Jos 21:36-37 presentes');
    });
    prueba('Josué: personas nuevas y compartidas en el lector (Rahab, Acán, Caleb, hijas de Zelofehad, Siquem)', () => {
      const seg = r => { const v = j(N2.versiculosDe(D2, N2.pasajeDe(D2, r))).find(x => x.ref === r); return j(N2.segmentar(D2, r, v.texto)).filter(x => x.persona).map(x => [x.texto, x.persona]); };
      assert.ok(seg('Jos 2:1').some(x => x[0] === 'Rahab' && x[1] === 'Rahab_1'));
      assert.deepEqual(seg('Jos 7:1').slice(0, 2), [['Achân', 'Achan_1'], ['Carmi', 'Carmi_2']]);
      assert.deepEqual(seg('Jos 1:1').filter(x => x[1] !== 'Moses_1'), [['Josué', 'Joshua_1'], ['Nun', 'Nun_1']]);
      assert.ok(seg('Jos 17:3').some(x => x[0] === 'Maala' && x[1] === 'Mahlah_1'));
      assert.ok(seg('Jos 15:14').some(x => x[0] === 'Aiman' && x[1] === 'Ahiman_1'));
      assert.equal(seg('Jos 24:32').filter(x => x[1] === 'Shechem_1').length, 1, 'la Siquem ciudad no se marca como persona');
    });
    prueba('Josué: mapa (refugio, Siquem, homónimos) y tiempo (Jordán año 41, Caleb 40 + 45 = 85)', () => {
      assert.ok(['cedes-de-neftali', 'siquem', 'hebron'].every(id => j(N2.lugaresDeRefs(D2, ['Jos 20:7'])).includes(id)));
      assert.ok(['beser', 'ramot-galaad', 'golan'].every(id => j(N2.lugaresDeRefs(D2, ['Jos 20:8', 'Dt 4:43'])).includes(id)));
      const ls = j(N2.lugaresDePasaje(D2, N2.pasajeDe(D2, 'Jos 15:21')));
      assert.ok(ls.length > 20, 'las listas de ciudades traen muchos lugares');
      const L = Object.fromEntries(D2.lugares.map(l => [l.id, l]));
      assert.notEqual(L['afec'].nombre, L['afec-13-4'].nombre, 'homónimos con nombre distinguible');
      const tm = 'TM|tare70|sem2|egipto';
      assert.equal(N2.anioEvento(D2, 'ev-paso-jordan', tm) - N2.anioEvento(D2, 'ev-salida-egipto', tm), 41);
      assert.equal(N2.anioEvento(D2, 'ev-caleb-hebron', tm) - N2.anioEvento(D2, 'ev-nac-caleb', tm), 85);
      assert.ok(j(N2.eventosDePasaje(D2, N2.pasajeDe(D2, 'Jos 4:19'))).some(e => e.id === 'ev-paso-jordan'));
    });
    const rc4 = path.join(aqui, '..', 'datos', 'contenido.js');
    if (existsSync(rc4)) prueba('Josué: marcas de contenido (Jericó alto, granizo medio, Rahab sexual, 1:9 sin marca)', () => {
      const cr = cargar(rc4, path.join(aqui, '..', 'app.js')), NC = cr.BibliaNucleo, CR = cr.BIBLIA_CONTENIDO;
      assert.equal(NC.marcaDe(CR, 'Jos 6:21').nivel, 'alto'); assert.equal(NC.marcaDe(CR, 'Jos 10:26').categoria, 'crueldad');
      assert.equal(NC.marcaDe(CR, 'Jos 10:11').nivel, 'medio'); assert.equal(NC.marcaDe(CR, 'Jos 2:1').categoria, 'sexual');
      assert.equal(NC.marcaDe(CR, 'Jos 1:9'), null);
    });
  }
  if ((D2.libros || []).some(l => l.id === 'Jue')) {
    prueba('Jueces: selector, 9 secciones, lector sin huecos (618 versículos) y Jue 14:18-20 de la RV1909', () => {
      assert.deepEqual(j(N2.libros(D2)).map(l => l.id).slice(0, 7), ['Gn', 'Ex', 'Lv', 'Nm', 'Dt', 'Jos', 'Jue']);
      assert.equal(N2.nombreLibro(D2, 'Jue'), 'Jueces');
      assert.equal(N2.parseRef('Jueces 21:25').libro, 'Jue');
      assert.ok(N2.clave('Jue 1:1') > N2.clave('Jos 24:33'));
      const s = j(N2.seccionesPlan(D2, ['jue-01'], 'jue-02', 'Jue'));
      assert.equal(s.length, 9); assert.ok(s.every(g => g.libro === 'Jue'));
      const vs = N2.pasajes(D2).filter(p => N2.libroDe(p) === 'Jue').flatMap(p => j(N2.versiculosDe(D2, p)));
      assert.equal(vs.length, 618); assert.equal(new Set(vs.map(v => v.ref)).size, 618);
      assert.equal(vs[0].ref, 'Jue 1:1'); assert.equal(vs[vs.length - 1].ref, 'Jue 21:25');
      assert.ok(/^Y él les respondió/.test(vs.find(x => x.ref === 'Jue 14:19').texto), 'la RV1909 parte el 14:18 inglés');
    });
    prueba('Jueces: lectura en orden después de Josué y tiempo mínimo del primer pasaje', () => {
      const ps = j(N2.pasajes(D2)), i = ps.findIndex(p => p.id === 'jue-01');
      assert.equal(ps[i - 1].id, ps.filter(p => N2.libroDe(p) === 'Jos').pop().id, 'jue-01 va justo después del último de Josué');
      const antes = ps.slice(0, i).map(p => p.id);
      assert.equal(N2.frontera(D2, antes).id, 'jue-01');
      const A = N2.accesibles(D2, antes);
      assert.ok(A.ref('Jue 1:15') && !A.ref('Jue 1:16') && !A.pasaje('jue-02'), 'Jueces se abre pasaje a pasaje');
      const pal = N2.palabrasPasaje(D2, ps[i]);
      assert.ok(pal > 300); assert.equal(N2.segundosMinimos(pal, { tipo: 'adulto' }), Math.ceil(pal / 250 * 60));
    });
    prueba('Jueces: personas en el lector (Gedeón = Jerobaal, Jabín de Jue 4 ≠ Jos 11, Hobab, Dan/Lais) y mapa', () => {
      const seg = r => { const v = j(N2.versiculosDe(D2, N2.pasajeDe(D2, r))).find(x => x.ref === r); return j(N2.segmentar(D2, r, v.texto)).filter(x => x.persona).map(x => [x.texto, x.persona]); };
      assert.deepEqual(seg('Jue 6:32'), [['Gedeón', 'Gideon_1'], ['Jerobaal', 'Gideon_1']]);
      assert.ok(seg('Jue 4:2').some(x => x[0] === 'Jabín' && x[1] === 'Jabin_Jue4'));
      assert.ok(seg('Jos 11:1').some(x => x[0] === 'Jabín' && x[1] === 'Jabin_1'));
      assert.ok(seg('Jue 4:11').some(x => x[0] === 'Hobab' && x[1] === 'Hobab_1'));
      assert.ok(seg('Jue 4:4').some(x => x[0] === 'Débora' && x[1] === 'Deborah_2'));
      assert.equal(seg('Jue 18:29').filter(x => x[1] === 'Dan_1').length, 1, 'la ciudad Dan no se marca como persona');
      assert.ok(['dan', 'gabaa', 'siloh', 'mizpa-de-galaad'].every(id => j(N2.lugaresDeRefs(D2, ['Jue 18:29', 'Jue 19:12', 'Jue 18:31', 'Jue 11:29'])).includes(id)));
    });
    const rc5 = path.join(aqui, '..', 'datos', 'contenido.js');
    if (existsSync(rc5)) prueba('Jueces: marcas de contenido (Jael alto, Gabaa sexual alto, despedazada crueldad, 6:12 sin marca)', () => {
      const cr = cargar(rc5, path.join(aqui, '..', 'app.js')), NC = cr.BibliaNucleo, CR = cr.BIBLIA_CONTENIDO;
      assert.equal(NC.marcaDe(CR, 'Jue 4:21').nivel, 'alto'); assert.equal(NC.marcaDe(CR, 'Jue 19:25').categoria, 'sexual');
      assert.equal(NC.marcaDe(CR, 'Jue 19:29').categoria, 'crueldad'); assert.equal(NC.marcaDe(CR, 'Jue 15:15').nivel, 'medio');
      assert.equal(NC.marcaDe(CR, 'Jue 6:12'), null);
    });
  }
} else console.log('(datos/biblia.js aún no existe: se omiten las pruebas con datos reales)');

// ---- Textos originales: alineación, testigos, variantes, voz y video (con pruebas/originales-ejemplo.js) ----
{
  const cx = cargar(path.join(aqui, 'originales-ejemplo.js'), path.join(aqui, '..', 'app.js'));
  const NO = cx.BibliaNucleo, O = cx.BIBLIA_ORIGINALES, G = cx.BIBLIA_GRIEGO;
  console.log('Textos originales (ejemplo)');
  prueba('rangos de testigos: libro, capítulo, versículos y entre libros', () => {
    const k = r => NO.clave(r);
    assert.deepEqual(j(NO.rangoClaves('Ex 1:1-Ex 1:22')), { a: k('Ex 1:1'), b: k('Ex 1:22') });
    assert.deepEqual(j(NO.rangoClaves('Ex 1:1-22')), { a: k('Ex 1:1'), b: k('Ex 1:22') });
    assert.deepEqual(j(NO.rangoClaves('Gn 1:1-2:3')), { a: k('Gn 1:1'), b: k('Gn 2:3') });
    assert.equal(NO.rangoClaves('Gn 1').a, k('Gn 1:1')); assert.ok(NO.rangoClaves('Gn 1').b < k('Gn 2:1'));
    const ex = NO.rangoClaves('Ex'); assert.ok(ex.a <= k('Ex 1:1') && ex.b >= k('Ex 40:38') && ex.a > k('Gn 50:26'));
    assert.equal(NO.rangoClaves(''), null);
  });
  prueba('testigos que contienen el pasaje (filtro por rango)', () => {
    const ids = refs => j(NO.testigosDe(O, refs)).map(t => t.id);
    assert.deepEqual(ids(['Ex 1:1', 'Ex 1:5']), ['leningrado', '4q13', 'samaritano']);
    assert.deepEqual(ids(['Ex 1:7', 'Ex 1:9']), ['leningrado', 'samaritano'], '4Q13 del ejemplo llega solo hasta Ex 1:6');
    assert.deepEqual(ids(['Ex 1:6', 'Ex 1:9']), ['leningrado', '4q13', 'samaritano'], 'basta con que se solapen');
    assert.deepEqual(ids(['Gn 1:1']), ['leningrado', 'samaritano']);
    assert.deepEqual(ids([]), []); assert.deepEqual(j(NO.testigosDe({}, ['Gn 1:1'])), []);
  });
  prueba('variantes por pasaje', () => {
    assert.deepEqual(j(NO.variantesDe(O, ['Ex 1:1', 'Ex 1:5', 'Ex 1:6'])).map(v => v.ref), ['Ex 1:5']);
    assert.equal(NO.variantesDe(O, ['Ex 1:1', 'Ex 1:4']).length, 0);
    assert.equal(NO.variantesDe(O, ['Gn 1:5']).length, 0, 'mismo capítulo y versículo en otro libro no cuenta');
  });
  prueba('alineación por versículo con numeración hebrea distinta', () => {
    assert.equal(NO.numeracionHebrea('Gn 31:55', 'Gn 32:1'), '32:1');
    assert.equal(NO.numeracionHebrea('Gn 1:1', 'Gn 1:1'), null); assert.equal(NO.numeracionHebrea('Gn 1:1', undefined), null);
    assert.equal(NO.numeracionHebrea('Ml 4:1', 'Mal 3:19'), 'Mal 3:19', 'otro libro: se muestra completo');
    assert.equal(NO.numeracionHebrea('Jue 14:18', 'Jue 14:18a'), '14:18a', 'media unidad: se rotula aunque el número coincida');
    assert.equal(NO.numeracionHebrea('Jue 14:19', 'Jue 14:18b'), '14:18b');
    const d = { capitulos: [{ libro: 'Gn', cap: 31, versiculos: [{ n: 54, texto: 'a' }, { n: 55, texto: 'Y levantóse Labán' }] }] };
    const f = j(NO.alinearOriginales(d, { inicio: 'Gn 31:54', fin: 'Gn 31:55' }, O, G));
    assert.deepEqual(f.map(x => x.ref), ['Gn 31:54', 'Gn 31:55']);
    assert.equal(f[0].he, null, 'sin texto hebreo en los datos: no se inventa');
    assert.equal(f[1].heNum, '32:1'); assert.ok(f[1].he.startsWith('וַיַּשְׁכֵּם')); assert.equal(f[1].rv, 'Y levantóse Labán');
    const e = j(NO.alinearOriginales({ capitulos: [{ libro: 'Ex', cap: 1, versiculos: [{ n: 5, texto: 'x' }] }] }, { inicio: 'Ex 1:5', fin: 'Ex 1:5' }, O, G))[0];
    assert.equal(e.heNum, null); assert.ok(e.gr.includes('πέντε καὶ ἑβδομήκοντα'));
    assert.deepEqual(j(NO.alinearOriginales(d, { inicio: 'Gn 31:55', fin: 'Gn 31:55' }, null, null)).map(x => [x.he, x.gr]), [[null, null]]);
  });
  prueba('texto para la voz: sin cantilación (hebreo) y monotónico (griego)', () => {
    const h = NO.textoParaVoz(O.hebreo['Gn 1:1'].t, 'he');
    assert.ok(!/[֑-֯]/.test(h) && h.includes('בְּרֵאשִׁית') && h.endsWith('.'));
    assert.equal(NO.textoParaVoz('עַל־פְּנֵי {פ}', 'he'), 'עַל פְּנֵי');
    const gr = NO.textoParaVoz('Ἐν ἀρχῇ ἐποίησεν ὁ θεὸς', 'el');
    assert.equal(gr, 'Εν αρχή εποίησεν ο θεός'.normalize('NFC'));
  });
  prueba('elección de voz por idioma (he/iw, región, local)', () => {
    const vs = [{ name: 'A', lang: 'es-MX', localService: false }, { name: 'B', lang: 'es-ES', localService: true }, { name: 'C', lang: 'iw-IL', localService: true }, { name: 'D', lang: 'el_GR' }];
    assert.equal(NO.vozPara(vs, 'es').name, 'B'); assert.equal(NO.vozPara(vs, 'es', 'MX').name, 'A');
    assert.equal(NO.vozPara(vs, 'he', 'IL').name, 'C'); assert.equal(NO.vozPara(vs, 'el', 'GR').name, 'D');
    assert.equal(NO.vozPara(vs, 'la'), null); assert.equal(NO.vozPara(null, 'es'), null);
  });
  prueba('videos del libro con id de YouTube válido; escritura del texto', () => {
    assert.deepEqual(j(NO.videosDeLibro(O, 'Éxodo')).map(v => v.libro), ['Ex']);
    assert.equal(NO.videosDeLibro(O, 'Gn').length, 0);
    assert.equal(NO.videosDeLibro({ videos: [{ libro: 'Ex', youtube_id: 'x"><script' }] }, 'Ex').length, 0);
    assert.equal(NO.escritura('שִׁבְעִים'), 'he'); assert.equal(NO.escritura('πέντε'), 'grc'); assert.equal(NO.escritura('setenta'), null);
  });
}

// ---- Textos originales reales: Levítico (datos/originales.js y datos/griego-swete.js) ----
{
  const ro = path.join(aqui, '..', 'datos', 'originales.js'), rg = path.join(aqui, '..', 'datos', 'griego-swete.js');
  if (existsSync(real) && existsSync(ro) && existsSync(rg)) {
    const cx = cargar(real, ro, rg, path.join(aqui, '..', 'app.js'));
    const NO = cx.BibliaNucleo, D = cx.BIBLIA_DATOS, O = cx.BIBLIA_ORIGINALES, G = cx.BIBLIA_GRIEGO;
    if ((D.libros || []).some(l => l.id === 'Lv')) {
      console.log('Textos originales reales (Levítico)');
      prueba('Levítico: todo versículo con hebreo y griego; TM 5:20-26 = RV 6:1-7 y Lv 6 corrido', () => {
        const f = j(NO.alinearOriginales(D, { inicio: 'Lv 1:1', fin: 'Lv 27:34' }, O, G));
        assert.equal(f.length, 859);
        assert.ok(f.every(x => x.he && x.gr), 'ningún versículo de Lv sin hebreo ni griego');
        const por = Object.fromEntries(f.map(x => [x.ref, x]));
        assert.equal(por['Lv 6:1'].heNum, '5:20'); assert.equal(por['Lv 6:7'].heNum, '5:26');
        assert.equal(por['Lv 6:8'].heNum, '6:1'); assert.equal(por['Lv 5:19'].heNum, null); assert.equal(por['Lv 7:1'].heNum, null);
        assert.ok(por['Lv 16:8'].gr.includes('ἀποπομπαίῳ') && NO.escritura(por['Lv 16:8'].he) === 'he');
      });
      prueba('Levítico: testigos por pasaje y video del libro', () => {
        const ids = refs => j(NO.testigosDe(O, refs)).map(t => t.id);
        const a = ids(['Lv 16:8']);
        assert.ok(['leningrado', 'vaticano', 'alejandrino'].every(x => a.includes(x)) && !a.includes('alepo') && !a.includes('sinaitico'));
        assert.ok(ids(['Lv 21:1']).includes('sinaitico'), 'el Sinaítico conserva Lv 20:27-22:30');
        assert.ok(ids(['Lv 26:14']).includes('4Q249j') && ids(['Lv 8:12']).includes('6Q2'));
        assert.ok(!ids(['Ex 40:38']).includes('4Q156'), 'el targum sin contenido calculado no se atribuye a ningún pasaje');
        const v = j(NO.videosDeLibro(O, 'Levítico'));
        assert.equal(v[0].youtube_id, 'vKT8eo3hAMw'); assert.ok(v.every(x => x.libro === 'Lv'));
      });
    }
    if ((D.libros || []).some(l => l.id === 'Nm')) {
      console.log('Textos originales reales (Números)');
      prueba('Números: hebreo y griego en todo versículo con texto; numeración propia de la RV en Nm 13, 16-17, 26 y 30', () => {
        const f = j(NO.alinearOriginales(D, { inicio: 'Nm 1:1', fin: 'Nm 36:13' }, O, G));
        assert.equal(f.length, 1288);
        const vacios = f.filter(x => !x.rv).map(x => x.ref);
        assert.deepEqual(vacios, ['Nm 12:16', 'Nm 29:40']);
        assert.ok(f.filter(x => x.rv).every(x => x.he && x.gr), 'ningún versículo con texto sin hebreo ni griego');
        const por = Object.fromEntries(f.map(x => [x.ref, x]));
        assert.ok(!por['Nm 12:16'].he && !por['Nm 12:16'].gr && /Nm 13:1/.test(por['Nm 12:16'].nota), 'el vacío no recibe hebreo duplicado y conserva su nota');
        assert.equal(por['Nm 13:1'].heNum, '12:16'); assert.equal(por['Nm 13:33'].heNum, '13:32–33');
        assert.equal(por['Nm 16:36'].heNum, '17:1'); assert.equal(por['Nm 17:13'].heNum, '17:28');
        assert.equal(por['Nm 26:1'].heNum, '25:19–26:1'); assert.equal(por['Nm 30:16'].heNum, '30:16–17'); assert.equal(por['Nm 30:1'].heNum, null);
        assert.ok(por['Nm 21:9'].gr.includes('ὄφιν χαλκοῦν') && por['Nm 6:24'].gr.includes('Εὐλογήσαι'));
      });
      prueba('Números: testigos (Qumrán y códices) y videos del libro', () => {
        const ids = refs => j(NO.testigosDe(O, refs)).map(t => t.id);
        const a = ids(['Nm 7:88']);
        assert.ok(['leningrado', 'vaticano', 'alejandrino', '2Q8'].every(x => a.includes(x)) && !a.includes('alepo') && !a.includes('sinaitico'));
        assert.ok(ids(['Nm 13:8']).includes('4Q27') && ids(['Nm 23:6']).includes('2Q29'));
        assert.deepEqual(j(NO.videosDeLibro(O, 'Números')).map(v => v.youtube_id), ['dtfbSxNecMk', 'IhW7gXB3o8I']);
      });
    }
    if ((D.libros || []).some(l => l.id === 'Dt')) {
      console.log('Textos originales reales (Deuteronomio)');
      prueba('Deuteronomio: hebreo en todo versículo (TM 13:1, 23:1, 28:69 y 29:1-28); sin griego solo los 4 de «sin_texto»', () => {
        const f = j(NO.alinearOriginales(D, { inicio: 'Dt 1:1', fin: 'Dt 34:12' }, O, G));
        assert.equal(f.length, 959);
        assert.ok(f.every(x => x.he), 'ningún versículo de Dt sin hebreo');
        const sin = ['Dt 14:14', 'Dt 23:2', 'Dt 23:12', 'Dt 25:16'];
        assert.deepEqual(f.filter(x => !x.gr).map(x => x.ref), sin, 'Swete no tiene «todo cuervo» y tiene tres versículos vacíos');
        assert.deepEqual(Object.keys(G.sin_texto).filter(r => r.startsWith('Dt ')), sin, 'cada uno con su motivo');
        const por = Object.fromEntries(f.map(x => [x.ref, x]));
        assert.equal(por['Dt 12:32'].heNum, '13:1'); assert.equal(por['Dt 22:30'].heNum, '23:1');
        assert.equal(por['Dt 29:1'].heNum, '28:69'); assert.equal(por['Dt 29:29'].heNum, '29:28'); assert.equal(por['Dt 30:1'].heNum, null);
        assert.ok(por['Dt 6:4'].he.includes('ע') && por['Dt 6:4'].gr.includes('Ἄκουε'), 'Shemá con la ע grande');
        assert.ok(por['Dt 5:17'].gr.includes('φονεύσεις') && por['Dt 14:15'].gr.includes('στρουθὸν'));
      });
      prueba('Deuteronomio: testigos (Qumrán, papiros, Alepo), variante de Dt 32:8 y videos', () => {
        const ids = refs => j(NO.testigosDe(O, refs)).map(t => t.id);
        const a = ids(['Dt 32:8']);
        assert.ok(['leningrado', 'alepo', 'vaticano', 'alejandrino', '4Q37'].every(x => a.includes(x)) && !a.includes('sinaitico'));
        assert.ok(ids(['Dt 6:4']).includes('papiro-nash') && ids(['Dt 26:18']).includes('rylands-458') && !ids(['Dt 1:1']).includes('alepo'));
        assert.equal(O.testigos.find(t => t.id === 'papiro-nash').tipo, 'papiro');
        const v = j(NO.variantesDe(O, ['Dt 32:8']));
        assert.equal(v.length, 1); assert.deepEqual(v[0].lecturas.map(l => l.testigos[0]), ['leningrado', '4Q37', 'vaticano']);
        assert.deepEqual(j(NO.videosDeLibro(O, 'Deuteronomio')).map(v => v.youtube_id), ['qfMplfJoYA0', 'lq36F3b-S2U']);
      });
    }
  }
}

console.log('Recursos (imágenes, objetos, medios)');
{
  const NR = cargar(path.join(aqui, '..', 'app.js')).BibliaNucleo;
  const k = (c, v, lb = 1) => lb * 1e6 + c * 1000 + v;
  const ficha = (id, tipo, rangos, extra) => Object.assign({ id, tipo, titulo: id, licencia: 'Dominio público', atribucion: 'Autor. Dominio público.', url_fuente: 'https://commons.wikimedia.org/x', imagen: 'recursos/imagenes/' + id + '.jpg', rangos, auditoria: 'OK' }, extra);
  const R = { fichas: [
    ficha('amplia', 'arte', [[k(1, 1), k(1, 31)]]),
    ficha('luz', 'arte', [[k(1, 3), k(1, 5)]]),
    ficha('dia2', 'arte', [[k(1, 6), k(1, 8)]]),
    ficha('maqueta', 'reconstruccion', [[k(1, 3), k(1, 4)]]),
    ficha('objeto', 'arqueologia', [[k(1, 3), k(1, 3)]], { relacion: 'contexto' }),
    ficha('video', 'video', [[k(1, 1), k(11, 32)]], { imagen: null }),
    ficha('rechazada', 'arte', [[k(1, 1), k(1, 31)]], { auditoria: 'RECHAZAR' }),
    ficha('sin-licencia', 'arte', [[k(1, 1), k(1, 31)]], { licencia: 'desconocida' }),
    ficha('sin-atrib', 'arte', [[k(1, 1), k(1, 31)]], { atribucion: '' }),
    ficha('salmo', 'arte', [])
  ] };
  prueba('imagen del pasaje: la de mayor solapamiento, luego la más concreta', () => {
    const ks = [3, 4, 5].map(v => k(1, v));
    assert.deepEqual(j(NR.imagenesDe(R, ks).map(f => f.id)), ['luz', 'amplia', 'maqueta'], 'luz y amplia cubren 3 versículos; luz es más concreta');
    assert.deepEqual(j(NR.imagenesDe(R, [k(1, 7)]).map(f => f.id)), ['dia2', 'amplia']);
    assert.equal(NR.imagenesDe(R, [k(2, 1)]).length, 0, 'sin solapamiento no hay imagen (ni hueco)');
    assert.equal(NR.imagenesDe(R, []).length, 0);
    assert.equal(NR.imagenesDe(null, ks).length, 0);
    assert.equal(NR.imagenesDe(R, [k(1, 3, 2)]).length, 0, 'mismo capítulo y versículo de otro libro no cuenta');
  });
  prueba('excluidas no aparecen (rechazada, licencia desconocida con imagen, sin atribución)', () => {
    const ids = j(NR.recursos(R).map(f => f.id));
    for (const x of ['rechazada', 'sin-licencia', 'sin-atrib']) assert.ok(!ids.includes(x), x);
    assert.ok(NR.recursoValido(ficha('enlace', 'arqueologia', [], { imagen: null, licencia: 'desconocida' })), 'licencia desconocida solo como enlace');
    const todas = j(NR.recursosDe(R, [k(1, 3)]).map(f => f.id));
    assert.ok(!todas.some(x => ['rechazada', 'sin-licencia', 'sin-atrib', 'salmo'].includes(x)));
  });
  prueba('acompañante: objetos y medios, sin repetir el carrusel; rótulos', () => {
    const A = NR.relacionadosDe(R, [k(1, 3)], ['luz', 'amplia', 'maqueta']);
    assert.deepEqual(j(A.objetos.map(f => f.id)), ['objeto']); assert.equal(A.imagenes.length, 0);
    assert.deepEqual(j(A.medios.map(f => f.id)), ['video']);
    assert.equal(NR.rotuloRecurso(R.fichas[0]), 'Arte · interpretación');
    assert.equal(NR.rotuloRecurso(R.fichas[3]), 'Reconstrucción moderna');
    assert.equal(NR.rotuloRecurso({ tipo: 'ilustracion' }), 'Ilustración moderna');
    assert.equal(NR.rotuloRecurso(R.fichas[4]), 'Contexto de la época');
    assert.equal(NR.rotuloRecurso({ tipo: 'arqueologia' }), 'Objeto histórico');
  });
  const recReal = path.join(aqui, '..', 'datos', 'recursos.js');
  if (existsSync(real) && existsSync(recReal)) {
    const CR = cargar(real, recReal, path.join(aqui, '..', 'app.js'));
    const N3 = CR.BibliaNucleo, D3 = CR.BIBLIA_DATOS, R3 = CR.BIBLIA_RECURSOS;
    prueba('datos/recursos.js: Gn 1:3-5 muestra «La creación de la luz» de Doré; ninguna excluida ni sin licencia', () => {
      const p = N3.pasajeDe(D3, 'Gn 1:3');
      const imgs = N3.imagenesDe(R3, N3.versiculosDe(D3, p).map(v => v.clave));
      assert.equal(imgs[0].id, 'dore-gn-1-creacion-luz'); assert.equal(imgs[0].titulo, 'La creación de la luz');
      const ex = new Set((R3.excluidas || []).map(x => x.id)), vis = N3.recursos(R3);
      assert.ok(ex.has('tissot-ex-40-tabernaculo-altar') && !vis.some(f => f.id === 'tissot-ex-40-tabernaculo-altar'), 'la rechazada no se muestra');
      assert.equal(vis.length, R3.fichas.length, 'todas las fichas generadas pasan el filtro');
      for (const f of vis) {
        assert.ok(!ex.has(f.id) && f.auditoria !== 'RECHAZAR', f.id);
        if (f.imagen) assert.ok(!/desconocida|reservados/i.test(f.licencia) && existsSync(path.join(aqui, '..', f.imagen)), f.id);
      }
    });
  }
}

console.log('\nRecorridos (pruebas/recorridos-ejemplo.js)');
{
  const CX = cargar(path.join(aqui, 'recorridos-ejemplo.js'), path.join(aqui, '..', 'app.js'));
  const NR = CX.BibliaNucleo, RC = CX.BIBLIA_RECORRIDOS;
  const ex = NR.recorrido(RC, 'exodo');
  prueba('etapas en el orden de `orden`, aunque los datos vengan desordenados', () => {
    assert.deepEqual(j(NR.etapasOrdenadas(ex).map(e => e.orden)), [1, 2, 3, 4, 5, 6]);
    const rev = Object.assign({}, ex, { etapas: ex.etapas.slice().reverse() });
    assert.deepEqual(j(NR.etapasOrdenadas(rev).map(e => e.nombre)), j(NR.etapasOrdenadas(ex).map(e => e.nombre)));
    assert.equal(NR.recorrido(RC, 'no-existe'), null);
  });
  prueba('etapa activa para una ref: Ex 14 resalta Pi-hahirot y el cruce del mar', () => {
    const refs = Array.from({ length: 31 }, (_, i) => `Ex 14:${i + 1}`);
    const a = NR.etapaActiva(ex, refs, null);
    assert.deepEqual(j(a.aqui.map(i => NR.etapasOrdenadas(ex)[i].nombre)), ['Pi-hahirot', 'Cruce del mar']);
    assert.equal(NR.etapasOrdenadas(ex)[a.actual].nombre, 'Cruce del mar', 'sin versículo marcado: la última del pasaje');
    assert.equal(NR.etapasOrdenadas(ex)[NR.etapaActiva(ex, refs, 'Ex 14:2').actual].nombre, 'Pi-hahirot', 'el versículo marcado manda');
    assert.equal(NR.etapaActiva(ex, ['Gn 1:1', 'Ex 3:1'], null), null);
    assert.equal(NR.recorridosDeRefs(RC, ['Ex 15:23']).length, 1);
  });
  prueba('ubicación por hipótesis; la por defecto solo si FALTA la clave; clave sin coordenadas = sin propuesta', () => {
    const E = NR.etapasOrdenadas(ex);
    assert.equal(NR.hipotesisDefecto(ex).id, 'sur');
    const pi = NR.ubicacionEtapa(ex, E[2], 'norte');
    assert.equal(pi.hipotesis, 'norte'); assert.equal(pi.heredada, false); assert.equal(pi.lat, 31.05);
    const ram = NR.ubicacionEtapa(ex, E[0], 'norte'); // «norte» no trae la clave: hereda la de «sur»
    assert.equal(ram.hipotesis, 'sur'); assert.equal(ram.heredada, true); assert.equal(ram.confianza, 'alta');
    assert.equal(NR.sinPropuesta(ex, E[0], 'norte'), false);
    assert.equal(NR.ubicacionEtapa(ex, E[1], 'norte'), null, 'Sucot: «norte» trae la clave sin coordenadas, no hereda');
    assert.equal(NR.sinPropuesta(ex, E[1], 'norte'), true);
    assert.equal(NR.ubicacionEtapa(ex, E[1], 'sur').lat, 30.55);
    assert.equal(NR.ubicacionEtapa(ex, E[0], 'sur').heredada, false);
    assert.equal(NR.ubicacionEtapa(ex, { ubicaciones: {} }, 'sur'), null);
    assert.equal(NR.ubicacionEtapa(ex, { ubicaciones: { sur: { lat: null, lon: 3 } } }, 'sur'), null, 'sin coordenadas no se ubica');
  });
  prueba('tramo que salta una etapa sin propuesta: une anterior y siguiente, marcado sinPropuesta', () => {
    const T = NR.tramosRecorrido(ex, 'norte');
    assert.deepEqual(j(T.map(t => [t.de, t.a, t.sinPropuesta])), [[0, 2, true], [2, 3, false], [3, 4, false], [4, 5, false]]);
    assert.ok(NR.tramosRecorrido(ex, 'sur').every(t => !t.sinPropuesta));
  });
  prueba('tramos inciertos: los que tocan una etapa de confianza baja', () => {
    const T = NR.tramosRecorrido(ex, 'sur');
    assert.equal(T.length, 5);
    assert.deepEqual(j(T.map(t => t.incierto)), [false, true, true, true, false]);
    assert.deepEqual(j(T.map(t => t.confianza)), ['media', 'baja', 'baja', 'baja', 'media']);
    assert.ok(T.every(t => t.km > 0));
    const sinUbic = Object.assign({}, ex, { etapas: ex.etapas.map(e => e.orden === 2 ? Object.assign({}, e, { ubicaciones: {} }) : e) });
    assert.deepEqual(j(NR.tramosRecorrido(sinUbic, 'sur').slice(0, 1).map(t => [t.de, t.a])), [[0, 2]], 'una etapa sin ubicación se salta');
  });
  prueba('ritmo: más distancia, viaje más largo (con tope); parada según la cita', () => {
    assert.ok(NR.duracionTramo(10) < NR.duracionTramo(100) && NR.duracionTramo(100) < NR.duracionTramo(400));
    assert.equal(NR.duracionTramo(0), 900); assert.equal(NR.duracionTramo(1e5), 4200);
    assert.ok(NR.pausaEtapa({ cita: 'corta' }) < NR.pausaEtapa({ cita: 'x'.repeat(120) }));
    assert.ok(Math.abs(NR.distanciaKm([31, 30], [32, 30]) - 96.3) < 1);
  });
  const recReal = path.join(aqui, '..', 'datos', 'recorridos.js');
  if (existsSync(recReal)) {
    const CR = cargar(recReal, path.join(aqui, '..', 'app.js'));
    const N4 = CR.BibliaNucleo, R4 = CR.BIBLIA_RECORRIDOS;
    prueba('datos/recorridos.js: contrato (refs legibles, una hipótesis por defecto con fuente) y Ex 14 en el éxodo', () => {
      const L = N4.listaRecorridos(R4);
      assert.ok(L.length >= 1);
      for (const r of L) {
        assert.ok(N4.hipotesisDefecto(r), r.id + ': sin hipótesis');
        for (const h of r.hipotesis) assert.ok(h.fuente, `${r.id}/${h.id}: hipótesis sin fuente`);
        for (const e of r.etapas) assert.ok(N4.rangoClaves(e.ref), `${r.id}: ref ilegible ${e.ref}`);
      }
      const exr = N4.recorrido(R4, 'exodo');
      if (exr) {
        const a = N4.etapaActiva(exr, Array.from({ length: 31 }, (_, i) => `Ex 14:${i + 1}`), null);
        assert.ok(a, 'Ex 14 no toca ninguna etapa del éxodo');
        const E4 = N4.etapasOrdenadas(exr);
        assert.ok(a.aqui.some(i => /hahirot/i.test(E4[i].nombre)) && /mar/i.test(E4[a.actual].nombre), 'Ex 14: Pi-hahirot y el cruce del mar');
        // Una hipótesis con la clave sin coordenadas no hereda la ubicación por defecto.
        for (const h of exr.hipotesis) for (const e of E4) {
          const u = e.ubicaciones && e.ubicaciones[h.id];
          if (u && (u.lat === null || u.lon === null)) { assert.equal(N4.ubicacionEtapa(exr, e, h.id), null, `${h.id}/${e.nombre}`); assert.ok(N4.sinPropuesta(exr, e, h.id)); }
        }
      }
    });
  }
}

// ---- Perfiles locales y contenido fuerte (pruebas/contenido-ejemplo.js) ----
{
  const cx = cargar(path.join(aqui, 'contenido-ejemplo.js'), path.join(aqui, '..', 'app.js'));
  const P = cx.BibliaNucleo, C = cx.BIBLIA_CONTENIDO;
  console.log('\nPerfiles y contenido (ejemplo)');
  const nino = { id: 'p2', tipo: 'nino' }, adulto = { id: 'p1', tipo: 'adulto', avisar: false }, avisa = { id: 'p3', tipo: 'adulto', avisar: true };
  prueba('claves por perfil: cada perfil tiene su espacio y no se pisan', () => {
    assert.equal(P.clavePerfil('p1', 'biblia.pasajesLeidos'), 'biblia.p.p1.pasajesLeidos');
    assert.equal(P.clavePerfil('p2', 'biblia.pasajesLeidos'), 'biblia.p.p2.pasajesLeidos');
    assert.equal(P.clavePerfil('p2', 'notas'), 'biblia.p.p2.notas', 'claves futuras sin prefijo también');
    assert.ok(P.esClaveLegada('biblia.pos') && !P.esClaveLegada('biblia.perfiles') && !P.esClaveLegada('biblia.p.p1.pos') && !P.esClaveLegada('otra.app'));
    const ks = ['biblia.p.p1.pos', 'biblia.p.p1.trad', 'biblia.p.p12.pos', 'biblia.p.p2.pos', 'biblia.perfiles'];
    assert.deepEqual(j(P.clavesDePerfil(ks, 'p1')), ['biblia.p.p1.pos', 'biblia.p.p1.trad'], 'p1 no arrastra las de p12');
  });
  prueba('migración: los datos de antes pasan al primer perfil (adulto) sin perder nada', () => {
    const m = P.migrarPerfiles(['biblia.pos', 'biblia.pasajesLeidos', 'biblia.supuestos', 'otra.cosa'], null);
    assert.equal(m.nuevo, true);
    assert.equal(m.registro.lista.length, 1);
    assert.equal(m.registro.lista[0].tipo, 'adulto');
    assert.equal(m.registro.activo, m.registro.lista[0].id);
    assert.equal(m.registro.pin, null);
    assert.deepEqual(j(m.mover), [['biblia.pos', 'biblia.p.p1.pos'], ['biblia.pasajesLeidos', 'biblia.p.p1.pasajesLeidos'], ['biblia.supuestos', 'biblia.p.p1.supuestos']]);
    const r = { v: 1, activo: 'p2', pin: 'sha256:x', lista: [{ id: 'p1', nombre: 'Ana', tipo: 'adulto' }, { id: 'p2', nombre: 'Leo', tipo: 'nino', color: 'ocre' }] };
    const m2 = P.migrarPerfiles(['biblia.pos'], r);
    assert.equal(m2.nuevo, false); assert.equal(m2.mover.length, 0, 'con registro no se mueve nada');
    assert.equal(m2.registro.activo, 'p2'); assert.equal(m2.registro.lista[1].inicial, 'L');
    assert.equal(P.normalizarRegistro({ lista: [] }), null);
    assert.equal(P.normalizarRegistro({ activo: 'p9', lista: [{ id: 'p1', nombre: 'A' }] }).activo, 'p1', 'activo inexistente → el primero');
  });
  prueba('nuevo perfil: id libre, tipo y color válidos, inicial del nombre', () => {
    const p = P.nuevoPerfil([{ id: 'p1' }, { id: 'p2' }], { nombre: '  ñandú ', tipo: 'nino', color: 'verdin' });
    assert.equal(p.id, 'p3'); assert.equal(p.nombre, 'ñandú'); assert.equal(p.tipo, 'nino'); assert.equal(p.color, 'verdin'); assert.equal(p.inicial, 'Ñ');
    const q = P.nuevoPerfil([{ id: 'p2' }], { nombre: '', tipo: 'x', color: 'neón' });
    assert.equal(q.id, 'p3'); assert.equal(q.tipo, 'adulto'); assert.ok(P.COLORES_PERFIL.includes(q.color)); assert.equal(q.nombre, 'Adulto');
  });
  prueba('PIN: de niño a adulto se pide; de adulto a niño o sin PIN, no', () => {
    const r = { pin: 'h', lista: [{ id: 'p1', tipo: 'adulto' }, { id: 'p2', tipo: 'nino' }, { id: 'p3', tipo: 'nino' }] };
    assert.equal(P.cambioPidePin(r, 'p2', 'p1'), true);
    assert.equal(P.cambioPidePin(r, 'p1', 'p2'), false);
    assert.equal(P.cambioPidePin(r, 'p2', 'p3'), false);
    assert.equal(P.cambioPidePin(Object.assign({}, r, { pin: null }), 'p2', 'p1'), false);
    assert.ok(P.pinValido('0427') && !P.pinValido('427') && !P.pinValido('12a4') && !P.pinValido('12345'));
  });
  prueba('decisión por versículo: niño pliega lo alto y anota lo medio; adulto lo ve todo (o con aviso si lo pide)', () => {
    const d = (perf, ref) => P.accionVerso(C, perf, ref).accion;
    assert.equal(d(nino, 'Gn 4:8'), 'plegar'); assert.equal(d(nino, 'Gn 19:4'), 'plegar'); assert.equal(d(nino, 'Gn 19:11'), 'plegar');
    assert.equal(d(nino, 'Gn 19:12'), 'mostrar'); assert.equal(d(nino, 'Gn 19:3'), 'mostrar');
    assert.equal(d(nino, 'Ex 2:12'), 'nota'); assert.equal(d(nino, 'Gn 4:7'), 'mostrar');
    assert.equal(d(adulto, 'Gn 19:5'), 'mostrar'); assert.equal(d(adulto, 'Ex 2:12'), 'mostrar');
    assert.equal(d(avisa, 'Gn 19:5'), 'aviso'); assert.equal(d(avisa, 'Ex 2:12'), 'nota');
    assert.equal(P.decisionVerso(nino, null), 'mostrar');
    assert.equal(P.marcaDe(C, 'Gn 19:7').categoria, 'sexual');
    assert.equal(P.marcaDe({ marcas: [{ desde: 'Gn 1:1', hasta: 'Gn 1:3', nivel: 'medio' }, { desde: 'Gn 1:2', hasta: 'Gn 1:2', nivel: 'alto' }] }, 'Gn 1:2').nivel, 'alto', 'gana la marca más fuerte');
    assert.equal(P.marcasContenido({ marcas: [{ desde: 'xx', nivel: 'alto' }, { desde: 'Gn 1:1', nivel: 'bajo' }] }).length, 0, 'marcas ilegibles o de nivel desconocido se ignoran');
  });
  prueba('tramos: los versículos plegados seguidos van juntos y conservan sus números', () => {
    const refs = ['Gn 19:3', 'Gn 19:4', 'Gn 19:5', 'Gn 19:11', 'Gn 19:12'];
    const t = P.tramosContenido(C, nino, refs);
    assert.deepEqual(j(t.map(x => [x.accion, x.refs])), [['mostrar', ['Gn 19:3']], ['plegar', ['Gn 19:4', 'Gn 19:5', 'Gn 19:11']], ['mostrar', ['Gn 19:12']]]);
    assert.equal(P.tramosContenido(C, adulto, refs).length, 1);
  });
  prueba('recursos: el niño no ve imágenes sensibles ni de una parte plegada; el adulto, todo', () => {
    const k = r => P.clave(r);
    const cain = { id: 'c', tipo: 'arte', sensible: true, rangos: [[k('Gn 4:8'), k('Gn 4:8')]] };
    const sodoma = { id: 's', tipo: 'arte', sensible: false, rangos: [[k('Gn 19:1'), k('Gn 19:11')]] };
    const huida = { id: 'h', tipo: 'arte', sensible: false, rangos: [[k('Gn 19:15'), k('Gn 19:26')]] };
    const audio = { id: 'a', tipo: 'audio', sensible: false, rangos: [[k('Gn 1:1'), k('Gn 50:26')]], institucion: 'LibriVox' };
    const pb = { id: 'v', tipo: 'video', institucion: 'Proyecto Biblia', url_fuente: 'https://bibleproject.com/es/videos/genesis-1-11/', rangos: [[k('Gn 1:1'), k('Gn 11:32')]] };
    const otro = { id: 'o', tipo: 'video', institucion: 'Otro canal', url_fuente: 'https://example.org/v', rangos: [[k('Gn 1:1'), k('Gn 11:32')]] };
    const ks19 = ['Gn 19:1', 'Gn 19:4', 'Gn 19:15', 'Gn 19:20'].map(k);
    for (const f of [cain, sodoma, huida, audio, pb, otro]) assert.equal(P.recursoPermitido(f, adulto, C, ks19), true, 'adulto: ' + f.id);
    assert.equal(P.recursoPermitido(cain, nino, C), false, 'sensible');
    assert.equal(P.recursoPermitido(sodoma, nino, C, ks19), false, 'toca la parte plegada');
    assert.equal(P.recursoPermitido(huida, nino, C, ks19), true, 'otra escena del capítulo');
    assert.equal(P.recursoPermitido(audio, nino, C, ks19), true, 'audio de todo el libro (su enlace pide PIN aparte)');
    assert.equal(P.recursoPermitido(pb, nino, C), true, 'Proyecto Biblia');
    assert.equal(P.recursoPermitido(otro, nino, C), false, 'otros videos no');
    assert.equal(P.recursoPermitido(sodoma, nino, C), false, 'sin claves: cualquier solape con lo plegado');
  });
  prueba('curiosidades y enlaces: ocultas al niño si su ref cae en lo plegado; Proyecto Biblia sin PIN', () => {
    assert.equal(P.curiosidadPermitida({ refs: ['Gn 5:3', 'Gn 4:8'] }, nino, C), false);
    assert.equal(P.curiosidadPermitida({ refs: ['Gn 5:3', 'Ex 2:12'] }, nino, C), true, 'lo medio no se oculta');
    assert.equal(P.curiosidadPermitida({ refs: ['Gn 4:8'] }, adulto, C), true);
    assert.ok(P.enlaceLibre('https://bibleproject.com/es/videos/genesis-1-11/'));
    assert.ok(!P.enlaceLibre('https://es.wikipedia.org/wiki/Abel') && !P.enlaceLibre('https://evil.com/?bibleproject.com/es/'));
  });
  const real = path.join(aqui, '..', 'datos', 'contenido.js');
  if (existsSync(real)) prueba('datos/contenido.js: contrato (refs legibles, nivel y categoría válidos, origen editorial)', () => {
    const cr = cargar(real, path.join(aqui, '..', 'app.js')), CR = cr.BIBLIA_CONTENIDO;
    assert.ok(CR && Array.isArray(CR.marcas) && CR.marcas.length);
    assert.match(String(CR.origen || ''), /editorial/i);
    assert.equal(cr.BibliaNucleo.marcasContenido(CR).length, CR.marcas.length, 'todas las marcas se leen');
    for (const m of CR.marcas) { assert.ok(['alto', 'medio'].includes(m.nivel), m.desde); assert.ok(['sexual', 'violencia', 'crueldad'].includes(m.categoria), m.desde); }
  });
}

// ---- Tabernáculo (pruebas/tabernaculo-ejemplo.js y, si existe, datos/tabernaculo.js) ----
console.log('\nTabernáculo (pruebas/tabernaculo-ejemplo.js)');
{
  const cx = cargar(path.join(aqui, 'tabernaculo-ejemplo.js'), path.join(aqui, '..', 'app.js')), NT = cx.BibliaNucleo, T = cx.BIBLIA_TABERNACULO;
  const ps = [{ id: 'a', inicio: 'Ex 25:1', fin: 'Ex 25:22' }, { id: 'b', inicio: 'Ex 25:23', fin: 'Ex 25:40' }, { id: 'c', inicio: 'Ex 26:15', fin: 'Ex 26:37' }, { id: 'd', inicio: 'Ex 27:1', fin: 'Ex 27:21' }, { id: 'e', inicio: 'Ex 40:17', fin: 'Ex 40:38' }];
  prueba('codos → metros según el codo elegido (cálculo, al centímetro)', () => {
    assert.equal(NT.codosAMetros(2.5, 44.5), 1.11);
    assert.equal(NT.codosAMetros(2.5, 52.5), 1.31);
    assert.equal(NT.codosAMetros(100, 44.5), 44.5);
    assert.equal(NT.codosAMetros(null, 44.5), null);
    assert.equal(NT.tbCodo(T).id, 'comun', 'sin elección, el codo por defecto');
    assert.equal(NT.tbCodo(T, 'real').cm, 52.5);
    assert.equal(NT.tbCodo(T, 'inexistente').id, 'comun');
  });
  prueba('orden de montaje según `orden` y piezas colocadas sin repetir', () => {
    const t2 = JSON.parse(JSON.stringify(T)); t2.montaje = t2.montaje.slice().reverse().concat([{ orden: 2.5, pieza: 'arca', ref: 'Ex 40:21' }, { orden: 9, pieza: 'no-existe', ref: 'Ex 40:1' }]);
    assert.deepEqual(j(NT.tbMontaje(t2).map(m => m.pieza)), ['tablas', 'arca', 'arca', 'velo', 'mesa', 'candelabro', 'altar-bronce', 'cortinas-atrio']);
    assert.deepEqual(j(NT.tbColocadas(t2, 3)), ['tablas', 'arca']);
    assert.deepEqual(j(NT.tbColocadas(t2, 0)), []);
  });
  prueba('según voy leyendo: solo piezas con todos los pasajes de su instrucción leídos', () => {
    assert.deepEqual(j(NT.tbVisiblesLeido(T, ps, [])), []);
    assert.deepEqual(j(NT.tbVisiblesLeido(T, ps, ['a'])), ['arca']);
    assert.deepEqual(j(NT.tbVisiblesLeido(T, ps, ['a', 'b', 'd'])), ['arca', 'mesa', 'candelabro', 'altar-bronce', 'cortinas-atrio']);
    const parte = [{ id: 'x', inicio: 'Ex 25:10', fin: 'Ex 25:15' }, { id: 'y', inicio: 'Ex 25:16', fin: 'Ex 25:22' }];
    assert.deepEqual(j(NT.tbVisiblesLeido(T, parte, ['x'])), [], 'instrucción repartida en dos pasajes: hace falta leer ambos');
    assert.deepEqual(j(NT.tbVisiblesLeido(T, parte, ['x', 'y'])), ['arca']);
  });
  prueba('piezas por pasaje (instrucción, construcción o paso del montaje) y capítulos del acompañante', () => {
    assert.deepEqual(j(NT.tbPiezasDePasaje(T, ps[1]).map(p => p.id)), ['mesa', 'candelabro']);
    assert.deepEqual(j(NT.tbPiezasDePasaje(T, { inicio: 'Ex 37:1', fin: 'Ex 37:16' }).map(p => p.id)), ['arca', 'mesa']);
    assert.deepEqual(j(NT.tbPiezasDePasaje(T, ps[4]).map(p => p.id)), ['arca', 'mesa', 'candelabro', 'altar-bronce', 'tablas', 'velo', 'cortinas-atrio'].sort((a, b) => T.piezas.findIndex(p => p.id === a) - T.piezas.findIndex(p => p.id === b)));
    assert.deepEqual(j(NT.tbPiezasDeRefs(T, ['Ex 40:22']).map(p => p.id)), ['mesa']);
    assert.deepEqual(j(NT.tbPiezasDePasaje(T, { inicio: 'Ex 33:1', fin: 'Ex 33:23' })), []);
    assert.ok(NT.tbEnPasaje({ inicio: 'Ex 25:1', fin: 'Ex 25:22' }) && NT.tbEnPasaje({ inicio: 'Ex 40:17', fin: 'Ex 40:38' }));
    assert.ok(!NT.tbEnPasaje({ inicio: 'Ex 32:1', fin: 'Ex 32:35' }) && !NT.tbEnPasaje({ inicio: 'Gn 25:1', fin: 'Gn 25:6' }));
  });
  prueba('plano: huellas (rectángulo girado, punto sin medidas, contorno) y zonas', () => {
    assert.deepEqual(j(NT.tbHuella(NT.tbPieza(T, 'mesa')).esquinas), [[37, 27.5], [39, 27.5], [39, 28.5], [37, 28.5]]);
    assert.ok(NT.tbHuella(NT.tbPieza(T, 'candelabro')).punto, 'sin medidas: punto');
    const g = NT.tbHuella({ plano: { x: 10, y: 10, rot: 90 }, medidas: { largo: { codos: 4 }, ancho: { codos: 2 } } });
    assert.deepEqual(j(g.esquinas), [[11, 8], [11, 12], [9, 12], [9, 8]], 'rot 90: el largo va de sur a norte');
    const c = NT.tbHuella({ plano: { x: 35, y: 25, rect: { x0: 20, y0: 20, x1: 50, y1: 30 } }, medidas: {} });
    assert.ok(c.contorno && c.rect.x1 === 50);
    const Z = NT.tbDisposicion(T);
    assert.deepEqual(j(Z.map(z => [z.id, z.x0, z.x1, z.certeza])), [['atrio', 0, 100, 'texto'], ['santisimo', 20, 30, 'tradicion'], ['santo', 30, 50, 'tradicion']]);
    const t2 = JSON.parse(JSON.stringify(T)); t2.zonas.forEach((z, i) => { z.plano = [{ x0: 0, y0: 0, x1: 100, y1: 50, certeza: 'texto' }, { x0: 30, y0: 20, x1: 50, y1: 30, certeza: 'inferido' }, { x0: 20, y0: 20, x1: 30, y1: 30, certeza: 'inferido' }][i]; });
    assert.deepEqual(j(NT.tbDisposicion(t2).map(z => [z.id, z.x0, z.certeza])), [['atrio', 0, 'texto'], ['santo', 30, 'inferido'], ['santisimo', 20, 'inferido']], 'con plano en las zonas, se usa tal cual');
  });
  const real = path.join(aqui, '..', 'datos', 'tabernaculo.js');
  if (existsSync(real)) prueba('datos/tabernaculo.js: contrato (piezas, montaje, codos y citas legibles)', () => {
    const cr = cargar(real, path.join(aqui, '..', 'app.js')), NR = cr.BibliaNucleo, TR = cr.BIBLIA_TABERNACULO;
    const P = NR.tbPiezas(TR);
    assert.ok(P.length && P.length === TR.piezas.length, 'toda pieza tiene id y nombre');
    assert.ok(NR.tbCodo(TR) && TR.codos.every(c => +c.cm > 0));
    for (const p of P) { assert.ok(NR.TB_GRUPOS.includes(p.grupo), p.id); assert.ok(NR.rangosDe(p.instruccion).length, p.id + ': instrucción legible'); assert.ok(NR.tbHuella(p), p.id + ': posición en el plano'); }
    assert.equal(NR.tbMontaje(TR).length, TR.montaje.length, 'todos los pasos nombran una pieza que existe');
    assert.ok(TR.montaje.every(m => NR.parseRef(m.ref)), 'refs del montaje legibles');
    assert.ok(NR.tbDisposicion(TR).some(z => z.id === 'atrio'));
  });
}

console.log('Notas y subrayados');
{
  const DN = { libros: [{ id: 'Gn', nombre: 'Génesis' }, { id: 'Ex', nombre: 'Éxodo' }],
    capitulos: [{ libro: 'Gn', cap: 50, versiculos: [{ n: 26, texto: 'Y murió José de edad de ciento diez años.' }] },
      { libro: 'Ex', cap: 1, versiculos: [{ n: 1, texto: 'Estos son los nombres de los hijos de Israel.' }] },
      { libro: 'Ex', cap: 3, versiculos: [{ n: 14, texto: 'Y respondió Dios á Moisés: YO SOY EL QUE SOY.' }] }] };
  prueba('refs de notas: canónicas o rechazadas (sin Génesis por defecto)', () => {
    assert.equal(N.refNota('Ex 3:14'), 'Ex 3:14');
    assert.equal(N.refNota('éx 3:14'), 'Ex 3:14');
    assert.equal(N.refNota('Éxodo 3:14'), 'Ex 3:14');
    assert.equal(N.refNota('3:14'), null);
    assert.equal(N.refNota('Ex 3'), null);
    assert.equal(N.refNota('Xyz 3:14'), null);
    assert.equal(N.refNota('Ex 0:1'), null);
  });
  prueba('poner y quitar: un versículo sin color ni nota desaparece', () => {
    let o = N.ponerNota(null, 'Ex 3:14', { color: 'amarillo' }, '2026-11-11T10:00:00Z');
    assert.deepEqual(j(o), { v: 1, versos: { 'Ex 3:14': { color: 'amarillo', t: '2026-11-11T10:00:00Z' } } });
    o = N.ponerNota(o, 'Ex 3:14', { nota: '  prueba\r\nsegunda ' }, '2026-11-11T11:00:00Z');
    assert.deepEqual(j(o.versos['Ex 3:14']), { color: 'amarillo', nota: 'prueba\nsegunda', t: '2026-11-11T11:00:00Z' });
    o = N.ponerNota(o, 'Ex 3:14', { color: null }, '2026-11-11T12:00:00Z');
    assert.deepEqual(j(o.versos['Ex 3:14']), { nota: 'prueba\nsegunda', t: '2026-11-11T12:00:00Z' }, 'quitar el color conserva la nota');
    o = N.ponerNota(o, 'Ex 3:14', { nota: '   ' }, '2026-11-11T13:00:00Z');
    assert.deepEqual(j(o.versos), {}, 'sin color ni nota: fuera');
    o = N.ponerNota(o, 'Ex 3:14', { color: 'morado' });
    assert.deepEqual(j(o.versos), {}, 'color desconocido: no se guarda');
    o = N.quitarNota(N.ponerNota(null, 'Gn 1:1', { color: 'verde', nota: 'x' }, '2026-01-01T00:00:00Z'), 'Gn 1:1');
    assert.deepEqual(j(o), { v: 1, versos: {} });
  });
  prueba('normalizar lo guardado: entradas rotas fuera, refs canónicas', () => {
    const o = N.normalizarNotas({ v: 1, versos: { 'éx 3:14': { color: 'azul', t: 'ayer' }, '3:1': { color: 'azul' }, 'Gn 1:1': { color: 'rojo' }, 'Gn 2:1': 5 } });
    assert.deepEqual(j(o), { v: 1, versos: { 'Ex 3:14': { color: 'azul', t: '' } } });
    assert.deepEqual(j(N.normalizarNotas('basura')), { v: 1, versos: {} });
  });
  prueba('lista en orden canónico (Gn 50:26 antes de Ex 1:1) con filtros', () => {
    const o = { v: 1, versos: { 'Ex 3:14': { color: 'amarillo', nota: 'Nombre de Dios', t: '2026-11-11T00:00:00Z' }, 'Ex 1:1': { color: 'verde', t: '2026-11-11T00:00:00Z' },
      'Gn 50:26': { nota: 'José muere', t: '2026-11-11T00:00:00Z' }, 'Gn 3:15': { color: 'amarillo', t: '2026-11-11T00:00:00Z' } } };
    assert.deepEqual(j(N.listarNotas(o).map(x => x.ref)), ['Gn 3:15', 'Gn 50:26', 'Ex 1:1', 'Ex 3:14']);
    assert.deepEqual(j(N.listarNotas(o, { color: 'amarillo' }).map(x => x.ref)), ['Gn 3:15', 'Ex 3:14']);
    assert.deepEqual(j(N.listarNotas(o, { conNota: true }).map(x => x.ref)), ['Gn 50:26', 'Ex 3:14']);
    assert.deepEqual(j(N.listarNotas(o, { q: 'jose' }).map(x => x.ref)), ['Gn 50:26'], 'búsqueda sin tildes ni mayúsculas');
    assert.deepEqual(j(N.listarNotas(o, { q: 'Moisés' })), []);
  });
  prueba('fusionar una importación: gana lo más reciente por versículo, con conteos', () => {
    const actual = { v: 1, versos: { 'Ex 3:14': { color: 'amarillo', nota: 'vieja', t: '2026-11-01T00:00:00Z' }, 'Gn 1:1': { color: 'verde', t: '2026-11-10T00:00:00Z' }, 'Gn 2:1': { color: 'azul', t: '2026-11-05T00:00:00Z' } } };
    const entra = { v: 1, versos: { 'Ex 3:14': { color: 'rosa', nota: 'nueva', t: '2026-11-11T00:00:00Z' }, 'Gn 1:1': { color: 'azul', t: '2026-11-09T00:00:00Z' },
      'Gn 2:1': { color: 'azul', t: '2026-11-05T00:00:00Z' }, 'Ex 1:1': { nota: 'añadida', t: '2026-11-11T00:00:00Z' } } };
    const r = N.fusionarNotas(actual, entra);
    assert.deepEqual([r.anadidos, r.actualizados, r.iguales], [1, 1, 2]);
    assert.equal(r.notas.versos['Ex 3:14'].nota, 'nueva', 'la entrante es más reciente');
    assert.equal(r.notas.versos['Gn 1:1'].color, 'verde', 'la actual es más reciente');
    assert.equal(r.notas.versos['Ex 1:1'].nota, 'añadida');
    assert.equal(actual.versos['Ex 3:14'].nota, 'vieja', 'no muta la entrada');
  });
  prueba('validar un JSON importado: inválidos rechazados con motivo; exportación de ida y vuelta', () => {
    assert.equal(N.validarNotas('{no es json').ok, false);
    assert.match(N.validarNotas('{no es json').error, /JSON/);
    assert.equal(N.validarNotas('[1,2]').ok, false);
    assert.equal(N.validarNotas('{"v":2,"versos":{}}').ok, false);
    assert.equal(N.validarNotas('{"app":"otra","v":1,"versos":{}}').ok, false);
    assert.equal(N.validarNotas('{"v":1}').ok, false);
    assert.equal(N.validarNotas('{"v":1,"versos":{"zz":{"color":"amarillo"}}}').ok, false, 'ninguna entrada válida');
    const exp = N.exportarNotas({ v: 1, versos: { 'Ex 3:14': { color: 'amarillo', nota: 'prueba', t: '2026-11-11T00:00:00Z' } } }, { perfil: 'Ana' });
    const v = N.validarNotas('﻿' + JSON.stringify(exp));
    assert.ok(v.ok); assert.equal(v.total, 1); assert.equal(v.descartados, 0);
    assert.deepEqual(j(v.notas.versos['Ex 3:14']), { color: 'amarillo', nota: 'prueba', t: '2026-11-11T00:00:00Z' });
    const m = N.validarNotas('{"v":1,"versos":{"Ex 3:14":{"color":"verde"},"malo":{"color":"verde"}}}');
    assert.ok(m.ok); assert.equal(m.total, 1); assert.equal(m.descartados, 1);
  });
  prueba('cita del versículo y texto para copiar', () => {
    assert.equal(N.refLegible(DN, 'Ex 3:14'), 'Éxodo 3:14 (RV 1909)');
    assert.equal(N.textoVerso(DN, 'Ex 3:14'), 'Y respondió Dios á Moisés: YO SOY EL QUE SOY.');
    assert.equal(N.citaVerso(DN, 'Ex 3:14', N.textoVerso(DN, 'Ex 3:14')), '«Y respondió Dios á Moisés: YO SOY EL QUE SOY.» Éxodo 3:14 (RV 1909)');
    const lista = N.listarNotas({ v: 1, versos: { 'Ex 1:1': { color: 'verde', t: '' }, 'Gn 50:26': { nota: 'José', t: '' } } });
    assert.equal(N.textoNotas(DN, lista), 'Génesis 50:26 (RV 1909)\n«Y murió José de edad de ciento diez años.»\nTu nota: José\n\nÉxodo 1:1 (RV 1909) · subrayado verde\n«Estos son los nombres de los hijos de Israel.»');
  });
}

console.log('Lectura en orden');
{
  const ps = N.pasajes(D), ids = ps.map(p => p.id);
  prueba('frontera: primer pasaje sin leer; lo leído fuera de orden no la mueve', () => {
    assert.ok(ps.length >= 4, 'el ejemplo trae varios pasajes');
    assert.equal(N.frontera(D, []).id, ids[0]);
    assert.equal(N.frontera(D, [ids[0], ids[1]]).id, ids[2]);
    assert.equal(N.frontera(D, [ids[0], ids[3]]).id, ids[1], 'leer el 4.º no salta el 2.º');
    assert.equal(N.frontera(D, ids), null, 'todo leído');
  });
  prueba('accesibles: lo leído más todo hasta la frontera incluida', () => {
    const A = N.accesibles(D, [ids[0], ids[3]]);
    assert.ok(A.pasaje(ids[0]) && A.pasaje(ids[1]), 'leído y frontera');
    assert.equal(A.pasaje(ids[2]), false, 'posterior a la frontera, sin leer');
    assert.equal(A.pasaje(ids[3]), true, 'leído fuera de orden: se conserva');
    assert.equal(N.esAccesible(D, [], ids[1]), false);
    assert.equal(N.esAccesible(D, [], ids[0]), true);
    const last = ps[ps.length - 1];
    assert.equal(A.ref(last.fin), ids.length - 1 === 3, 'ref del último pasaje solo si es accesible');
    assert.equal(A.ref(ps[2].inicio), false);
    assert.equal(A.ref(ps[1].inicio), true);
    assert.equal(A.ref(''), false, 'sin ref no es accesible');
    assert.equal(N.accesibles(D, ids).todo, true);
    assert.equal(N.accesibles(D, ids).ref('Ap 22:21'), true, 'con todo leído no se oculta nada');
  });
  prueba('refs de rango y de capítulo: accesibles solo si lo son su principio y su final', () => {
    const A = N.accesibles(D, []), p0 = ps[0], a = N.parseRef(p0.inicio), b = N.parseRef(p0.fin);
    assert.equal(A.ref(`${a.libro} ${a.cap}:${a.v}-${b.v}`), a.cap === b.cap);
    const p1 = ps[1], c = N.parseRef(p1.fin);
    assert.equal(A.ref(`${a.libro} ${a.cap}:${a.v}-${c.cap}:${c.v}`), false, 'el final cae tras la frontera');
  });
  prueba('enlace a un pasaje bloqueado lleva a la frontera', () => {
    const r = N.destinoPasaje(D, [ids[0]], ids[3]);
    assert.equal(r.bloqueado, true); assert.equal(r.pasaje.id, ids[1]); assert.equal(r.pedido.id, ids[3]);
    const s = N.destinoPasaje(D, [ids[0]], ids[1]);
    assert.equal(s.bloqueado, false); assert.equal(s.pasaje.id, ids[1]);
  });
  prueba('segundos mínimos: palabras ÷ 250 (adulto) o ÷ 150 (niño) por minuto', () => {
    assert.equal(N.contarPalabras('Y dijo Dios: Sea la luz: y fué la luz.'), 10);
    assert.equal(N.segundosMinimos(250, { tipo: 'adulto' }), 60);
    assert.equal(N.segundosMinimos(250, { tipo: 'nino' }), 100);
    assert.equal(N.segundosMinimos(251, { tipo: 'adulto' }), 61, 'se redondea hacia arriba');
    assert.equal(N.segundosMinimos(0, null), 0);
    const w = N.palabrasPasaje(D, ps[0]);
    assert.ok(w > 0, 'el pasaje tiene palabras');
    assert.equal(N.palabrasPasaje(D, ps[0], () => true), 0, 'omitir quita versículos');
    assert.equal(N.relojTxt(83), '1:23'); assert.equal(N.relojTxt(5.2), '0:06');
    assert.equal(N.puedeMarcar(false, 59, 60), false); assert.equal(N.puedeMarcar(false, 60, 60), true); assert.equal(N.puedeMarcar(true, 0, 60), true, 'releer no pide tiempo');
    assert.deepEqual(j(N.normalizarTiempos({ a: 12, b: -1, c: 'x', d: '7' })), { a: 12, d: 7 });
    assert.deepEqual(j(N.normalizarTiempos(null)), {});
  });
  prueba('búsqueda y fichas: solo personas que aparecen en algo accesible (también leído fuera de orden)', () => {
    const A0 = N.accesibles(D, []), Atodo = N.accesibles(D, ids), I = N.indice(D);
    const tarde = [...I.primera.keys()].filter(id => ![...I.porRef].some(([k, s]) => s.has(id) && A0.clave(k)));
    assert.ok(tarde.length, 'hay personas que aparecen después del primer pasaje');
    const id = tarde[0], nom = N.persona(D, id).nombre;
    assert.ok(N.buscar(D, nom).some(p => p.id === id));
    assert.equal(N.buscarAccesible(D, A0, nom).some(p => p.id === id), false, 'no se encuentra antes de llegar');
    assert.equal(N.buscarAccesible(D, Atodo, nom).some(p => p.id === id), true);
    assert.equal(N.personaAccesible(D, A0, id), false);
    const pid = N.pasajes(D).find(p => N.versiculosDe(D, p).some(v => (I.porRef.get(v.clave) || new Set()).has(id))).id;
    assert.equal(N.personaAccesible(D, N.accesibles(D, [pid]), id), true, 'leer fuera de orden un pasaje donde aparece la muestra');
  });
  prueba('mapa: solo lugares mencionados en lo accesible', () => {
    const A0 = N.accesibles(D, []), Atodo = N.accesibles(D, ids), todos = (D.lugares || []).map(l => l.id);
    if (!todos.length) return;
    const vis = N.lugaresAccesibles(D, A0);
    assert.ok(vis.length < todos.length || todos.every(id => N.refsLugar(D, id).some(A0.ref)), 'algo queda oculto');
    vis.forEach(id => assert.ok(N.refsLugar(D, id).some(A0.ref)));
    assert.equal(N.lugaresAccesibles(D, Atodo).length, todos.filter(id => N.refsLugar(D, id).length).length);
  });
  prueba('tiempo: solo sucesos e hitos con ref accesible; vidas sin muerte futura', () => {
    const C = N.crono(D); if (!C) return;
    const combo = N.combinacion(D, 'TM', N.elecciones(D, {}));
    const A1 = N.accesibles(D, [ids[0]]), Atodo = N.accesibles(D, ids);
    const cuenta = L => L.reduce((s, g) => s + g.items.length + g.hitos.length, 0);
    const parcial = N.lineaAccesible(D, combo, A1);
    parcial.forEach(g => { g.items.forEach(it => assert.ok(A1.ref(it.evento.ref))); g.hitos.forEach(h => assert.ok(A1.ref(h.hito.ref))); });
    assert.ok(cuenta(parcial) < cuenta(N.lineaAccesible(D, combo, Atodo)), 'se ocultan sucesos posteriores');
    for (const x of N.vidasCrono(D, combo).values()) {
      const v = N.vidaAccesible(D, x, A1);
      if (v && v.evMuerte) assert.ok(A1.ref(C.porId.get(v.evMuerte).ref));
    }
  });
  prueba('curiosidades y edades: solo si todas sus refs son accesibles', () => {
    const A = N.accesibles(D, [ids[0]]);
    assert.equal(N.curiosidadAccesible(A, { refs: [ps[0].inicio] }), true);
    assert.equal(N.curiosidadAccesible(A, { refs: [ps[0].inicio, ps[3].inicio] }), false);
    assert.equal(N.curiosidadAccesible(A, { refs: [] }), false);
    assert.equal(N.edadAccesible(A, { ref: ps[0].inicio, de: [{ ref: ps[3].inicio }] }), false);
  });
}

console.log('Versículos sin texto original');
prueba('sin hebreo o sin griego: el motivo de los datos, tal cual, en la alineación y en la lista', () => {
  const O = { hebreo: { 'Gn 1:1': { t: 'בְּרֵאשִׁית' } }, hebreo_sin_texto: { 'Gn 1:2': 'No está en el Códice de Leningrado.' } };
  const G = { texto: { 'Gn 1:1': 'Ἐν ἀρχῇ' }, sin_texto: { 'Gn 1:2': 'Swete lo tiene vacío.' } };
  assert.deepEqual(j(N.sinTextoDe(O, G, 'Gn 1:2')), { he: 'No está en el Códice de Leningrado.', gr: 'Swete lo tiene vacío.' });
  assert.deepEqual(j(N.sinTextoDe(O, G, 'Gn 1:1')), { he: null, gr: null });
  assert.deepEqual(j(N.sinTextoOriginal(O, null, ['Gn 1:1', 'Gn 1:2'])), [{ ref: 'Gn 1:2', idioma: 'he', nota: 'No está en el Códice de Leningrado.' }]);
  const p = N.pasajes(D).find(x => N.clave(x.inicio) <= N.clave('Gn 1:2') && N.clave('Gn 1:2') <= N.clave(x.fin));
  if (p) {
    const f = N.alinearOriginales(D, p, O, G).find(x => x.ref === 'Gn 1:2');
    assert.equal(f.heFalta, 'No está en el Códice de Leningrado.'); assert.equal(f.grFalta, 'Swete lo tiene vacío.');
    assert.equal(N.alinearOriginales(D, p, O, G).find(x => x.ref === 'Gn 1:1').heFalta, undefined);
  }
  const ro = path.join(aqui, '..', 'datos', 'originales.js');
  if (existsSync(ro)) {
    const NR = cargar(ro, path.join(aqui, '..', 'app.js'));
    const st = NR.BibliaNucleo.sinTextoOriginal(NR.BIBLIA_ORIGINALES, null, ['Jos 21:36', 'Jos 21:37']);
    if ((NR.BIBLIA_ORIGINALES.hebreo_sin_texto || {})['Jos 21:36']) { assert.equal(st.length, 2); assert.match(st[0].nota, /Leningrado/); }
  }
});

console.log(`\n${ok} correctas, ${fallos} fallidas`);
process.exit(fallos ? 1 : 0);
