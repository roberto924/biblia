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

console.log(`\n${ok} correctas, ${fallos} fallidas`);
process.exit(fallos ? 1 : 0);
