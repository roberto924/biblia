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
  const fuera = D.personas.filter(p => p.sexo === 'f' && !s.has(p.id)).map(p => p.id);
  assert.deepEqual(j(fuera), []);
  assert.deepEqual(j(N.contarMujeres(D)), { conNombre: 4, sinNombre: 2 });
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
  assert.deepEqual(j(N.acompanante({}, ['Gn 1:1'])), { personas: [], vinculos: [], edades: [], sinNombre: [], lugares: [] });
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
  assert.deepEqual(j(N.parseRef('Gn 11:12')), { cap: 11, v: 12 });
});
prueba('tolerancia: datos vacíos o incompletos no rompen', () => {
  const V = { personas: [], relaciones: [{ de: 'X_1', a: 'Y_1', tipo: 'padre' }, { de: null }], edades: [{ persona: 'Y_1', tipo: 'total', tradicion: 'TM', valor: '' }] };
  assert.equal(N.construirBosque(V).length, 1);
  assert.deepEqual(j(N.lineaPorTradicion(V, 'TM')), []);
  assert.equal(N.edad(V, 'Y_1', 'total', 'TM'), null);
  assert.deepEqual(j(N.construirBosque({})), []);
});

const real = path.join(aqui, '..', 'datos', 'genesis.js');
if (existsSync(real)) {
  console.log('Datos reales (datos/genesis.js)');
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
    console.log(`     mujeres: ${m.conNombre} con nombre, ${m.sinNombre} sin nombre`);
    assert.deepEqual(j((D2.personas || []).filter(p => p.sexo === 'f' && !s.has(p.id)).map(p => p.id)), []);
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
} else console.log('(datos/genesis.js aún no existe: se omiten las pruebas con datos reales)');

console.log(`\n${ok} correctas, ${fallos} fallidas`);
process.exit(fallos ? 1 : 0);
