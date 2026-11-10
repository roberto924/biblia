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
  assert.deepEqual(j(b[0].hijos.map(h => h.id)), ['Cain_1', 'Abel_1', 'Seth_1']);
  assert.ok(!b.some(t => t.id === 'Eve_1'), 'Eva (cónyuge) no debe ser otra raíz');
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
  assert.equal(r.length, 18 - 3); // todos menos Eva, Caín y Abel (incluye a Cainán)
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
} else console.log('(datos/genesis.js aún no existe: se omiten las pruebas con datos reales)');

console.log(`\n${ok} correctas, ${fallos} fallidas`);
process.exit(fallos ? 1 : 0);
