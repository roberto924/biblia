// Pruebas de la lógica del servidor del desafío (supabase/functions/desafio/logica.js), sin base ni red.
// Uso: node pruebas/servidor.mjs
// Usa un banco sintético (el real está fuera de git); si existen datos/desafios.js (o DESAFIOS_JS=ruta) y
// datos/preguntas.js, también comprueba que el archivo público no lleve ids, preguntas, opciones ni citas.
// Contrato v2: «Cambios al contrato tras la revisión de seguridad» en el documento de diseño.
import { readFileSync, existsSync, readdirSync } from 'node:fs';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as L from '../supabase/functions/desafio/logica.js';

const aqui = path.dirname(fileURLToPath(import.meta.url));
let ok = 0, fallos = 0;
const pruebas = [];
const prueba = (nombre, fn) => pruebas.push([nombre, fn]);

// ---------- Banco sintético ----------
const Q = (id, personaje, n, c, extra = {}) => ({
  id, personaje, ref: `Gn 12:${n}`, orden: 1000 + n, cita: `cita literal de ${personaje} ${n}`, p: `¿Pregunta ${n} sobre ${personaje}?`,
  o: ['A', 'B', 'C', 'D'].map(x => `Opción ${x} de ${personaje} ${n}`), c, nino: true, ...extra,
});
const hex = k => k.toString(16).padStart(16, '0');
const BANCO = [
  Q(hex(1), 'Abram_1', 1, 0), Q(hex(2), 'Abram_1', 2, 1), Q(hex(3), 'Abram_1', 3, 2), Q(hex(4), 'Abram_1', 4, 3),
  Q(hex(5), 'Abram_1', 5, 1, { nino: false }),
  Q(hex(6), 'Abram_1', 9, 0), // después de su capítulo «listo»: nunca se sirve
  Q(hex(11), 'Canaan_1', 1, 0), Q(hex(12), 'Canaan_1', 2, 1), Q(hex(13), 'Canaan_1', 3, 2),
  Q(hex(21), 'Isaac_1', 1, 0), Q(hex(22), 'Isaac_1', 2, 1), Q(hex(23), 'Isaac_1', 3, 2, { nino: false }),
  Q(hex(24), 'Isaac_1', 4, 3, { nino: false }),
  Q(hex(31), 'Lot_1', 1, 0), Q(hex(32), 'Lot_1', 2, 1), Q(hex(33), 'Lot_1', 4, 2), Q(hex(34), 'Lot_1', 5, 3),
];
const PERSONAJES = [
  { id: 'Abram_1', nivel: 2, n: 3, hasta: 1005, sinNino: false },
  { id: 'Canaan_1', nivel: 2, n: 3, hasta: 1005, sinNino: true },
  { id: 'Isaac_1', nivel: 2, n: 3, hasta: 1005, sinNino: false },
  { id: 'Lot_1', nivel: 2, n: 3, hasta: 1003, sinNino: false }, // solo 2 preguntas hasta su capítulo
];
const idsDe = pj => BANCO.filter(q => q.personaje === pj).map(q => q.id);
const T0 = Date.UTC(2026, 10, 18, 15, 0, 0); // 2026-11-18 12:00 en Santiago (UTC−3)

function montar() {
  const borrados = [];
  const reloj = { t: T0 };
  const almacen = L.crearAlmacenMemoria({ preguntas: BANCO, personajes: PERSONAJES, alBorrar: uid => borrados.push(uid), ahora: () => reloj.t });
  let s = 12345; const azar = () => (s = (s * 1103515245 + 12345) % 2147483648) / 2147483648;
  const sv = L.crearServicio({ almacen, azar });
  const llamar = (uid, cuerpo) => sv.manejar(uid, cuerpo);
  return { almacen, reloj, llamar, borrados };
}
const U1 = '11111111-1111-4111-8111-111111111111', U2 = '22222222-2222-4222-8222-222222222222';
const UN = '33333333-3333-4333-8333-333333333333';
const NOMBRE_NINO = 'Pastor Valiente 482';
const registrarAdulto = (llamar, uid = U1, nombre = 'Roberto 92', zona = 'America/Santiago') =>
  llamar(uid, { accion: 'registrar', tipo: 'adulto', nombre, zona });
const registrarNino = (llamar, uid = UN, nombre = NOMBRE_NINO) =>
  llamar(uid, { accion: 'registrar', tipo: 'nino', nombre, zona: 'America/Santiago', consentimiento: true });
// Opción mostrada que es la correcta (la prueba mira el banco; la app no puede).
const correcta = pregunta => { const q = BANCO.find(x => x.p === pregunta.p); return pregunta.o.indexOf(q.o[q.c]); };
const incorrecta = pregunta => (correcta(pregunta) + 1) % 4;
async function jugar(llamar, reloj, uid, personaje, { fallar = -1, demora = 1000 } = {}) {
  const e = await llamar(uid, { accion: 'empezar', personaje });
  assert.equal(e.status, 200, JSON.stringify(e.body));
  let r = e, pregunta = e.body.pregunta, servidas = [pregunta];
  for (let i = 0; i < e.body.n; i++) {
    reloj.t += demora;
    r = await llamar(uid, { accion: 'responder', intento: e.body.intento, i, opcion: i === fallar ? incorrecta(pregunta) : correcta(pregunta) });
    assert.equal(r.status, 200, JSON.stringify(r.body));
    if (!r.body.fin) { pregunta = r.body.pregunta; servidas.push(pregunta); }
  }
  return { empezar: e.body, fin: r.body, servidas };
}

// ---------- Reglas puras ----------
prueba('escala por nivel y segundos (15 adulto, 25 niño) con 2 s de margen', () => {
  assert.deepEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 15].map(n => L.preguntasPorNivel(n)), [3, 3, 5, 5, 7, 7, 10, 10, 12, 12]);
  assert.equal(L.preguntasPorNivel(0), 0);
  assert.equal(L.segundosDe('adulto'), 15); assert.equal(L.segundosDe('nino'), 25);
  assert.equal(L.plazoMs(15), 17000);
});
const rd = process.env.DESAFIOS_JS || path.join(aqui, '..', 'datos', 'desafios.js');
const cargarJs = r => { const s = readFileSync(r, 'utf8'); return JSON.parse(s.slice(s.indexOf('{'), s.lastIndexOf('}') + 1)); };
if (existsSync(rd)) prueba('datos/desafios.js usa la misma escala y segundos que logica.js', () => {
  const d = cargarJs(rd);
  assert.deepEqual(d.escala, L.ESCALA); assert.deepEqual(d.segundos, L.SEGUNDOS);
});
prueba('puntaje: 10 × n + round(5 × n × sobrante / total) (Noé: 10 preguntas, 15 s → 100 a 150)', () => {
  assert.equal(L.puntaje(10, 0, 15), 150);
  assert.equal(L.puntaje(10, 150000, 15), 100);
  assert.equal(L.puntaje(10, 75000, 15), 125);
  assert.equal(L.puntaje(10, 999999, 15), 100, 'nunca menos que 10 × n');
  assert.equal(L.puntaje(3, 10000, 25), 30 + Math.round(15 * 65000 / 75000));
});
prueba('día local y próxima medianoche en la zona IANA (Santiago, Tokio, UTC)', () => {
  assert.equal(L.diaEnZona(T0, 'America/Santiago'), '2026-11-18');
  assert.equal(L.diaEnZona(Date.UTC(2026, 10, 18, 20), 'Asia/Tokyo'), '2026-11-19');
  assert.equal(new Date(L.proximaMedianoche(Date.UTC(2026, 10, 18, 20), 'Asia/Tokyo')).toISOString(), '2026-11-19T15:00:00.000Z');
  assert.equal(new Date(L.proximaMedianoche(Date.UTC(2026, 10, 18, 23, 59, 59), 'UTC')).toISOString(), '2026-11-19T00:00:00.000Z');
  assert.equal(new Date(L.proximaMedianoche(T0, 'America/Santiago')).toISOString(), '2026-11-19T03:00:00.000Z');
  // Con cambio de horario (Chile en septiembre, Nueva York en marzo): primer instante del día siguiente.
  for (const [t, z] of [[Date.UTC(2026, 8, 5, 20), 'America/Santiago'], [Date.UTC(2026, 2, 7, 20), 'America/New_York'], [Date.UTC(2026, 3, 4, 20), 'America/Santiago']]) {
    const m = L.proximaMedianoche(t, z), hoy = L.diaEnZona(t, z);
    assert.ok(L.diaEnZona(m, z) > hoy && L.diaEnZona(m - 1, z) === hoy, `${z} ${new Date(m).toISOString()}`);
  }
  assert.ok(L.zonaValida('America/Santiago')); assert.ok(!L.zonaValida('Marte/Olimpo')); assert.ok(!L.zonaValida(''));
  assert.ok(!L.zonaValida({}));
});
prueba('barajar y elegir: n distintas, cada una con su orden (permutación de 0–3)', () => {
  let s = 7; const azar = () => (s = (s * 9301 + 49297) % 233280) / 233280;
  const xs = L.elegirPreguntas(BANCO.slice(0, 5), 3, azar);
  assert.equal(xs.length, 3); assert.equal(new Set(xs.map(x => x.id)).size, 3);
  xs.forEach(x => assert.deepEqual([...x.orden].sort(), [0, 1, 2, 3]));
  const q = BANCO[0], sv = L.servir(q, [2, 0, 3, 1]);
  assert.deepEqual(Object.keys(sv), ['p', 'o']); assert.deepEqual(sv.o, [q.o[2], q.o[0], q.o[3], q.o[1]]);
});
prueba('nombres de niño: solo los del generador (sustantivo + adjetivo + 1–999)', () => {
  const ns = L.generarNombresNino(5);
  assert.equal(ns.length, 5); assert.equal(new Set(ns).size, 5);
  ns.forEach(n => assert.ok(L.esNombreNino(n), n));
  for (const malo of ['Juanito', 'Pastor Valiente', 'Pastor Valiente 0', 'Pastor Valiente 1000', 'Pastor Valiente 042',
    'pastor valiente 4', 'Moisés Valiente 4', 'Pastor Malvado 4', 'Pastor Valiente 4 x', 'Pastor  Valiente 4!'])
    assert.ok(!L.esNombreNino(malo), malo);
  assert.ok(L.esNombreNino('Arcoíris Brillante 999')); assert.ok(L.esNombreNino(' Estrella Alegre 17 '));
});
prueba('nombres de adulto: 3–20 letras, números o espacios; filtro de palabras ofensivas', () => {
  for (const bueno of ['Roberto 92', 'José María', 'Ana', 'Computadora', 'Disputa 3', 'Pera', 'Vergara', 'Essex', 'Shittim',
    'Pastor Fiel', 'Sexto Día', 'Grapes', 'Peacock 2'])
    assert.deepEqual(L.validarNombreAdulto(bueno), { nombre: bueno }, bueno);
  assert.deepEqual(L.validarNombreAdulto('  Ana   Luz  '), { nombre: 'Ana Luz' });
  for (const invalido of ['ab', 'a'.repeat(21), 'hola!', 'Ana_Luz', 'emoji 😀', '   ', 42, null])
    assert.deepEqual(L.validarNombreAdulto(invalido), { error: 'nombre-invalido' }, String(invalido));
  for (const feo of ['puta madre', 'P U T A', 'puuuta', 'mierda123', 'Fuck you', 'h1jueputa', 'Huevón', 'weon 1', 'perrrra',
    'CTM', 'conchetumare', 'Sh1t', 'a s s', 'Hitler 88', 'pendejo'])
    assert.deepEqual(L.validarNombreAdulto(feo), { error: 'nombre-ofensivo' }, feo);
});
prueba('nombres de adulto: solo alfabeto latino (cirílico, griego o ancho completo → nombre-invalido)', () => {
  for (const ajeno of ['Аna Luz', 'Rоberto', 'Ρedro', 'Ｒoberto', 'Иван', '李小龍', 'Ana ١٢', 'Ana​Luz', 'José'.normalize('NFD') + ' ẍ̈'])
    assert.deepEqual(L.validarNombreAdulto(ajeno), { error: 'nombre-invalido' }, ajeno);
  for (const bueno of ['Peña Ñandú', 'Çedille Ö', 'Müller 7'])
    assert.deepEqual(L.validarNombreAdulto(bueno), { nombre: bueno }, bueno);
  // Normaliza antes de validar: una tilde combinada (NFD) vale como la compuesta.
  assert.deepEqual(L.validarNombreAdulto('José Luis'), { nombre: 'José Luis' });
  assert.equal(L.claveNombre('  JOSÉ   María '), 'jose maria');
});
prueba('ranking: rank() por tipo (puntos desc, ms asc), empates comparten puesto, sin ids', () => {
  const perfiles = [
    { id: 'a', nombre: 'Ana', tipo: 'adulto' }, { id: 'b', nombre: 'Beto', tipo: 'adulto' }, { id: 'c', nombre: 'Caro', tipo: 'adulto' },
    { id: 'd', nombre: 'Dani', tipo: 'adulto' }, { id: 'n', nombre: NOMBRE_NINO, tipo: 'nino' }, { id: 'z', nombre: 'Cero', tipo: 'adulto' },
  ];
  const it = (perfil, puntos, ms, superado = true) => ({ perfil, puntos, ms, superado });
  const r = L.calcularRanking(perfiles, [it('a', 40, 5000), it('a', 35, 9000), it('b', 75, 9000), it('c', 75, 14000),
    it('d', 75, 9000), it('n', 30, 2000), it('z', 0, 0, false)]);
  assert.deepEqual(r.map(x => [x.tipo, x.puesto, x.nombre, x.puntos, x.personajes, x.ms]), [
    ['adulto', 1, 'Beto', 75, 1, 9000], ['adulto', 1, 'Dani', 75, 1, 9000], ['adulto', 3, 'Ana', 75, 2, 14000],
    ['adulto', 3, 'Caro', 75, 1, 14000], ['nino', 1, NOMBRE_NINO, 30, 1, 2000]]);
  r.forEach(x => assert.deepEqual(Object.keys(x), ['puesto', 'nombre', 'tipo', 'puntos', 'personajes', 'ms']));
});

// ---------- Acciones: perfil, nombres, registro ----------
prueba('sin usuario o cuerpo raro: no-autorizado, datos-invalidos, accion-desconocida', async () => {
  const { llamar } = montar();
  assert.deepEqual(await llamar('', { accion: 'perfil' }), { status: 401, body: { error: 'no-autorizado' } });
  assert.equal((await llamar(U1, null)).body.error, 'datos-invalidos');
  assert.equal((await llamar(U1, [1])).body.error, 'datos-invalidos');
  assert.equal((await llamar(U1, { accion: 'borrarTodo' })).body.error, 'accion-desconocida');
  assert.equal((await llamar(U1, { accion: 'constructor' })).body.error, 'accion-desconocida');
  assert.equal((await llamar(U1, { accion: 'toString' })).body.error, 'accion-desconocida');
});
prueba('registrar adulto; perfil; ya-registrado; nombre repetido sin distinguir mayúsculas; zona inválida', async () => {
  const { llamar } = montar();
  assert.deepEqual((await llamar(U1, { accion: 'perfil' })).body, { perfil: null });
  assert.equal((await registrarAdulto(llamar, U1, 'Roberto 92', 'Marte/Olimpo')).body.error, 'zona-invalida');
  assert.deepEqual(await registrarAdulto(llamar), { status: 200, body: { perfil: { nombre: 'Roberto 92', tipo: 'adulto' } } });
  assert.deepEqual((await llamar(U1, { accion: 'perfil' })).body, { perfil: { nombre: 'Roberto 92', tipo: 'adulto' } });
  assert.equal((await registrarAdulto(llamar, U1, 'Otro Nombre')).body.error, 'ya-registrado');
  const r = await registrarAdulto(llamar, U2, 'ROBERTO 92');
  assert.equal(r.status, 409); assert.equal(r.body.error, 'nombre-usado');
  assert.equal((await registrarAdulto(llamar, U2, 'Róberto  92')).body.error, 'nombre-usado', 'ni con tildes ni espacios');
  assert.equal((await registrarAdulto(llamar, U2, 'R\u043eberto 92')).body.error, 'nombre-invalido', 'o cirílica');
  assert.equal((await registrarAdulto(llamar, U2, 'puta 1')).body.error, 'nombre-ofensivo');
  assert.equal((await registrarAdulto(llamar, U2, 'x!')).body.error, 'nombre-invalido');
  assert.equal((await llamar(U2, { accion: 'registrar', tipo: 'admin', nombre: 'Luis', zona: 'UTC' })).body.error, 'datos-invalidos');
});
prueba('niño: nombre fuera del generador → nombre-invalido; sin consentimiento → falta-consentimiento (400)', async () => {
  const { llamar, almacen } = montar();
  for (const consentimiento of [undefined, false, 'true', 1]) {
    const r = await llamar(UN, { accion: 'registrar', tipo: 'nino', nombre: NOMBRE_NINO, zona: 'America/Santiago', consentimiento });
    assert.deepEqual(r, { status: 400, body: { error: 'falta-consentimiento' } }, String(consentimiento));
  }
  assert.equal((await registrarNino(llamar, UN, 'Juanito Pérez')).body.error, 'nombre-invalido');
  assert.equal((await registrarNino(llamar, UN, 'Pastor Valiente')).body.error, 'nombre-invalido');
  assert.equal((await registrarNino(llamar, UN, 'pastor valiente 482')).body.error, 'nombre-invalido');
  assert.equal(almacen.perfiles.size, 0);
  assert.deepEqual((await registrarNino(llamar)).body, { perfil: { nombre: NOMBRE_NINO, tipo: 'nino' } });
  assert.equal(almacen.perfiles.get(UN).consentimiento_en, new Date(T0).toISOString(), 'hora del servidor');
  await registrarAdulto(llamar, U1);
  assert.equal(almacen.perfiles.get(U1).consentimiento_en, null, 'adulto: null');
});
prueba('nombres: 5 generados, válidos y libres; renombrar solo adulto, con los mismos filtros', async () => {
  const { llamar } = montar();
  const { nombres } = (await llamar(U1, { accion: 'nombres' })).body;
  assert.equal(nombres.length, 5); nombres.forEach(n => assert.ok(L.esNombreNino(n)));
  await registrarNino(llamar);
  assert.equal((await llamar(UN, { accion: 'renombrar', nombre: 'Nuevo Nombre' })).body.error, 'solo-adulto');
  assert.equal((await llamar(U1, { accion: 'renombrar', nombre: 'Nuevo Nombre' })).body.error, 'sin-perfil');
  await registrarAdulto(llamar);
  assert.equal((await llamar(U1, { accion: 'renombrar', nombre: NOMBRE_NINO.toUpperCase() })).body.error, 'nombre-usado');
  assert.equal((await llamar(U1, { accion: 'renombrar', nombre: 'mierda' })).body.error, 'nombre-ofensivo');
  assert.deepEqual((await llamar(U1, { accion: 'renombrar', nombre: 'roberto 92' })).body, { perfil: { nombre: 'roberto 92', tipo: 'adulto' } });
  assert.deepEqual((await llamar(U1, { accion: 'renombrar', nombre: 'Rober' })).body, { perfil: { nombre: 'Rober', tipo: 'adulto' } });
});

// ---------- Desafío: casos de trampa ----------
prueba('la pregunta servida nunca lleva la correcta, la cita ni la ref; solo { p, o[4] }', async () => {
  const { llamar, reloj } = montar();
  await registrarAdulto(llamar);
  const e = await llamar(U1, { accion: 'empezar', personaje: 'Abram_1' });
  assert.equal(e.status, 200);
  assert.deepEqual(Object.keys(e.body).sort(), ['i', 'intento', 'n', 'pregunta', 'seg']);
  assert.deepEqual({ n: e.body.n, seg: e.body.seg, i: e.body.i }, { n: 3, seg: 15, i: 0 });
  let pregunta = e.body.pregunta;
  for (let i = 0; i < 3; i++) {
    assert.deepEqual(Object.keys(pregunta), ['p', 'o']); assert.equal(pregunta.o.length, 4);
    const q = BANCO.find(x => x.p === pregunta.p);
    assert.deepEqual([...pregunta.o].sort(), [...q.o].sort());
    const texto = JSON.stringify(e.body) + JSON.stringify(pregunta);
    assert.ok(!texto.includes(q.cita) && !texto.includes(q.ref) && !texto.includes(q.id) && !/"c"|correcta/.test(texto));
    reloj.t += 1000;
    const r = await llamar(U1, { accion: 'responder', intento: e.body.intento, i, opcion: correcta(pregunta) });
    if (i < 2) { assert.deepEqual(Object.keys(r.body), ['i', 'pregunta']); pregunta = r.body.pregunta; }
  }
});
prueba('supera: puntos con rapidez y repaso solo { p, ref } (sin respuesta ni cita); el repaso solo si supera', async () => {
  const { llamar, reloj } = montar();
  await registrarAdulto(llamar);
  const { fin, servidas } = await jugar(llamar, reloj, U1, 'Abram_1', { demora: 3000 });
  assert.equal(fin.superado, true); assert.equal(fin.aciertos, 3); assert.equal(fin.total, 3); assert.equal(fin.ms, 9000);
  assert.equal(fin.puntos, L.puntaje(3, 9000, 15)); assert.equal(fin.puntos, 42);
  assert.equal(fin.hasta, '2026-11-19T03:00:00.000Z');
  assert.deepEqual(fin.repaso.map(x => x.p), servidas.map(x => x.p));
  fin.repaso.forEach(x => { const q = BANCO.find(b => b.p === x.p); assert.deepEqual(x, { p: q.p, ref: q.ref }); });
  const texto = JSON.stringify(fin);
  servidas.forEach(sv => { const q = BANCO.find(b => b.p === sv.p); assert.ok(!texto.includes(q.cita) && !texto.includes(q.o[q.c]), 'ni cita ni respuesta'); });
  // Falla: solo «a de n», sin repaso y sin decir cuál falló.
  await registrarAdulto(llamar, U2, 'Luisa');
  const f = (await jugar(llamar, reloj, U2, 'Abram_1', { fallar: 1 })).fin;
  assert.deepEqual(Object.keys(f).sort(), ['aciertos', 'fin', 'hasta', 'ms', 'puntos', 'superado', 'total']);
  assert.deepEqual([f.aciertos, f.total, f.superado, f.puntos], [2, 3, false, 0]);
});
prueba('responder fuera de plazo (> seg + 2 s) cuenta como fallada aunque sea la correcta; −1 = salió', async () => {
  const { llamar, reloj } = montar();
  await registrarAdulto(llamar);
  const e = (await llamar(U1, { accion: 'empezar', personaje: 'Abram_1' })).body;
  reloj.t += 17000; // justo en el límite: vale
  let r = await llamar(U1, { accion: 'responder', intento: e.intento, i: 0, opcion: correcta(e.pregunta) });
  reloj.t += 17001; // 1 ms tarde
  r = await llamar(U1, { accion: 'responder', intento: e.intento, i: 1, opcion: correcta(r.body.pregunta) });
  assert.equal(r.status, 200, 'se acepta el mensaje pero cuenta como fallada');
  reloj.t += 1000;
  r = await llamar(U1, { accion: 'responder', intento: e.intento, i: 2, opcion: -1 });
  assert.deepEqual([r.body.aciertos, r.body.total, r.body.superado, r.body.puntos], [1, 3, false, 0]);
  assert.equal(r.body.repaso, undefined);
  assert.equal(r.body.ms, 15000 + 15000 + 15000, 'tarde o −1 cuentan el tiempo entero');
});
prueba('responder fuera de orden, dos veces la misma, a la vez, o con opción inválida', async () => {
  const { llamar, reloj } = montar();
  await registrarAdulto(llamar);
  const e = (await llamar(U1, { accion: 'empezar', personaje: 'Abram_1' })).body;
  assert.equal((await llamar(U1, { accion: 'responder', intento: e.intento, i: 1, opcion: 0 })).body.error, 'fuera-de-orden');
  assert.equal((await llamar(U1, { accion: 'responder', intento: e.intento, i: 2, opcion: 0 })).body.error, 'fuera-de-orden');
  for (const opcion of [4, -2, 1.5, '1', null]) assert.equal((await llamar(U1, { accion: 'responder', intento: e.intento, i: 0, opcion })).body.error, 'datos-invalidos');
  reloj.t += 1000;
  const [a, b] = await Promise.all([0, 1].map(k => llamar(U1, { accion: 'responder', intento: e.intento, i: 0, opcion: k })));
  assert.deepEqual([a.status, b.status].sort(), [200, 409], 'dos respuestas simultáneas: gana una');
  assert.equal((await llamar(U1, { accion: 'responder', intento: e.intento, i: 0, opcion: 0 })).body.error, 'fuera-de-orden');
  assert.equal((await llamar(U1, { accion: 'responder', intento: e.intento, i: 99, opcion: 0 })).body.error, 'fuera-de-orden');
});
prueba('intento ajeno, inventado, mal formado o ya terminado → intento-invalido', async () => {
  const { llamar, reloj } = montar();
  await registrarAdulto(llamar); await registrarAdulto(llamar, U2, 'Luisa');
  const e = (await llamar(U1, { accion: 'empezar', personaje: 'Abram_1' })).body;
  assert.equal((await llamar(U2, { accion: 'responder', intento: e.intento, i: 0, opcion: 0 })).body.error, 'intento-invalido');
  assert.equal((await llamar(U1, { accion: 'responder', intento: crypto.randomUUID(), i: 0, opcion: 0 })).body.error, 'intento-invalido');
  assert.equal((await llamar(U1, { accion: 'responder', intento: "1' or '1'='1", i: 0, opcion: 0 })).body.error, 'intento-invalido');
  for (let i = 0; i < 3; i++) { reloj.t += 500; await llamar(U1, { accion: 'responder', intento: e.intento, i, opcion: 0 }); }
  assert.equal((await llamar(U1, { accion: 'responder', intento: e.intento, i: 3, opcion: 0 })).body.error, 'intento-invalido');
});
prueba('segundo intento el mismo día → ya-intentado-hoy (+hasta); empezar ya lo consume; superado no se repite', async () => {
  const { llamar, reloj } = montar();
  await registrarAdulto(llamar);
  const e = await llamar(U1, { accion: 'empezar', personaje: 'Abram_1' });
  assert.equal(e.status, 200); // y no responde nada: abandonar cuenta como intento
  reloj.t += 3600e3;
  const r = await llamar(U1, { accion: 'empezar', personaje: 'Abram_1' });
  assert.deepEqual(r, { status: 409, body: { error: 'ya-intentado-hoy', hasta: '2026-11-19T03:00:00.000Z' } });
  // Dos empezar a la vez otro personaje: solo uno.
  const [a, b] = await Promise.all([1, 2].map(() => llamar(U1, { accion: 'empezar', personaje: 'Isaac_1' })));
  assert.deepEqual([a.status, b.status].sort(), [200, 409]);
  // Responder el intento abandonado al día siguiente: tarde, fallada.
  reloj.t += 24 * 3600e3;
  const tarde = await llamar(U1, { accion: 'responder', intento: e.body.intento, i: 0, opcion: correcta(e.body.pregunta) });
  assert.equal(tarde.status, 200);
  reloj.t += 17001; // la respuesta tardía sirvió la siguiente: deja pasar su plazo
  const { fin } = await jugar(llamar, reloj, U1, 'Abram_1');
  assert.equal(fin.superado, true);
  reloj.t += 24 * 3600e3;
  assert.equal((await llamar(U1, { accion: 'empezar', personaje: 'Abram_1' })).body.error, 'superado');
});
prueba('pasar la medianoche de su zona: el día es el de la zona fija del perfil y la hora del servidor', async () => {
  const { llamar, reloj } = montar();
  await registrarAdulto(llamar, U1, 'Roberto 92', 'America/Santiago');
  await registrarAdulto(llamar, U2, 'Kenji', 'Asia/Tokyo');
  reloj.t = Date.UTC(2026, 11, 1, 2, 59, 50); // 23:59:50 en Santiago (UTC−3); 11:59:50 en Tokio
  const e = (await llamar(U1, { accion: 'empezar', personaje: 'Abram_1', ids: idsDe('Abram_1'), dia: '2030-01-01', hoy: '2030-01-01' })).body;
  assert.equal((await llamar(U1, { accion: 'estado' })).body.hoy, '2026-11-30', 'ignora un día enviado por la app');
  reloj.t += 5000; // el intento sigue siendo del día en que empezó, aunque se responda pasada la medianoche
  let r = await llamar(U1, { accion: 'responder', intento: e.intento, i: 0, opcion: incorrecta(e.pregunta) });
  reloj.t += 6000; // 00:00:01 del día siguiente en Santiago
  r = await llamar(U1, { accion: 'responder', intento: e.intento, i: 1, opcion: 0 });
  reloj.t += 1000; r = await llamar(U1, { accion: 'responder', intento: e.intento, i: 2, opcion: 0 });
  assert.equal(r.body.hasta, '2026-12-02T03:00:00.000Z', 'próxima medianoche contada desde la hora de la respuesta');
  const est = (await llamar(U1, { accion: 'estado' })).body;
  assert.equal(est.hoy, '2026-12-01'); assert.equal(est.personajes.Abram_1.intentadoHoy, false);
  assert.equal((await llamar(U1, { accion: 'empezar', personaje: 'Abram_1' })).status, 200, 'nuevo día: puede');
  // Tokio a la misma hora: su día es otro; su medianoche, otra.
  const k = (await llamar(U2, { accion: 'estado' })).body;
  assert.equal(k.hoy, '2026-12-01'); assert.equal(k.hasta, '2026-12-01T15:00:00.000Z');
  await llamar(U2, { accion: 'empezar', personaje: 'Abram_1' });
  reloj.t = Date.UTC(2026, 11, 1, 14, 59, 59); // 23:59:59 en Tokio: aún el mismo día
  assert.equal((await llamar(U2, { accion: 'empezar', personaje: 'Abram_1' })).body.error, 'ya-intentado-hoy');
  reloj.t += 2000;
  assert.equal((await llamar(U2, { accion: 'empezar', personaje: 'Abram_1' })).status, 200);
});
prueba('niño: sin personajes sin_nino ni preguntas nino:false (aunque las mande la app)', async () => {
  const { llamar, reloj, almacen } = montar();
  await registrarNino(llamar);
  assert.equal((await llamar(UN, { accion: 'empezar', personaje: 'Canaan_1' })).body.error, 'sin-desafio');
  // Isaac: solo 2 aptas para niño, pide 3.
  const f = await llamar(UN, { accion: 'empezar', personaje: 'Isaac_1' });
  assert.equal(f.body.error, 'faltan-preguntas');
  for (let k = 0; k < 20; k++) { // Abram: 4 aptas + 1 no apta; nunca sale la no apta
    const uid = crypto.randomUUID();
    await llamar(uid, { accion: 'registrar', tipo: 'nino', nombre: `Cedro Fiel ${k + 1}`, zona: 'UTC', consentimiento: true });
    const { empezar, servidas } = await jugar(llamar, reloj, uid, 'Abram_1');
    assert.equal(empezar.seg, 25);
    servidas.forEach(p => assert.notEqual(BANCO.find(q => q.p === p.p).nino, false));
  }
  const usadas = new Set([...almacen.intentos.values()].flatMap(x => x.servidas.map(s => s.id)));
  assert.ok(!usadas.has(hex(5)));
  // El adulto sí tiene Canaán.
  await registrarAdulto(llamar);
  assert.equal((await llamar(U1, { accion: 'empezar', personaje: 'Canaan_1' })).status, 200);
});
prueba('empezar ignora los ids de la app: el servidor elige entre todas hasta el capítulo «listo»', async () => {
  const { llamar, almacen } = montar();
  for (let k = 0; k < 30; k++) {
    const uid = crypto.randomUUID();
    await registrarAdulto(llamar, uid, `Jugador ${k + 1}`);
    const e = await llamar(uid, { accion: 'empezar', personaje: 'Abram_1', ids: k % 2 ? [hex(6)] : ['ffffffffffffffff', 'x'] });
    assert.equal(e.status, 200, 'ids inventados o ajenos no cambian nada');
  }
  const usadas = new Set([...almacen.intentos.values()].flatMap(x => x.servidas.map(s => s.id)));
  assert.ok(!usadas.has(hex(6)), 'nunca una pregunta posterior a su capítulo listo, aunque la app la pida');
  assert.deepEqual([...usadas].sort(), [hex(1), hex(2), hex(3), hex(4), hex(5)], 'el azar recorre todo el banco permitido');
  // Lot: 2 preguntas hasta su capítulo y pide 3 → faltan-preguntas, sin gastar el intento.
  await registrarAdulto(llamar);
  const r = await llamar(U1, { accion: 'empezar', personaje: 'Lot_1', ids: idsDe('Lot_1') });
  assert.deepEqual(r, { status: 409, body: { error: 'faltan-preguntas' } });
  assert.equal((await llamar(U1, { accion: 'estado' })).body.personajes.Lot_1, undefined, 'no consume el intento');
  assert.equal((await llamar(U1, { accion: 'empezar', personaje: 'Nadie_1' })).body.error, 'sin-desafio');
  for (const personaje of ['../x', '', null, 7]) assert.equal((await llamar(U1, { accion: 'empezar', personaje })).body.error, 'datos-invalidos');
});
prueba('intento abierto del mismo personaje (aunque ya sea otro día) → ya-intentado-hoy hasta que vence su plazo', async () => {
  const { llamar, reloj } = montar();
  await registrarAdulto(llamar);
  reloj.t = Date.UTC(2026, 11, 1, 2, 59, 55); // 23:59:55 en Santiago
  assert.equal((await llamar(U1, { accion: 'empezar', personaje: 'Abram_1' })).status, 200);
  reloj.t += 10000; // 00:00:05 del día siguiente: la pregunta 1 sigue en plazo
  const r = await llamar(U1, { accion: 'empezar', personaje: 'Abram_1' });
  assert.equal(r.body.error, 'ya-intentado-hoy'); assert.equal(r.body.hasta, '2026-12-02T03:00:00.000Z');
  assert.equal((await llamar(U1, { accion: 'estado' })).body.personajes.Abram_1.intentadoHoy, true);
  reloj.t += 7001; // vencido el plazo (17 s): ya no está abierto
  assert.equal((await llamar(U1, { accion: 'empezar', personaje: 'Abram_1' })).status, 200);
});
prueba('al cerrar, si otro intento ya superó el personaje (choque del índice único) → superado, no fuera-de-orden', async () => {
  const { llamar, reloj, almacen } = montar();
  await registrarAdulto(llamar);
  const e = (await llamar(U1, { accion: 'empezar', personaje: 'Abram_1' })).body;
  // Simula la carrera: otro intento del mismo personaje quedó superado mientras tanto.
  const otro = await almacen.crearIntento({ perfil: U1, personaje: 'Abram_1', dia: '2026-11-17', seg: 15, total: 3, servidas: [], servidas_en: [0], respuestas: [], i: 3, aciertos: 3, ms: 3000, terminado: true, superado: true, puntos: 40 });
  assert.ok(otro);
  let pregunta = e.pregunta, r;
  for (let i = 0; i < 3; i++) {
    reloj.t += 1000;
    r = await llamar(U1, { accion: 'responder', intento: e.intento, i, opcion: correcta(pregunta) });
    pregunta = r.body.pregunta;
  }
  assert.deepEqual(r, { status: 409, body: { error: 'superado' } });
  assert.equal(almacen.ranking()[0].puntos, 40, 'el ranking no suma dos veces');
});
prueba('relojes desiguales: hasta 500 ms «antes» de servirse vale; más, cuenta como fallada', async () => {
  const { llamar, reloj } = montar();
  await registrarAdulto(llamar);
  const e = (await llamar(U1, { accion: 'empezar', personaje: 'Abram_1' })).body;
  reloj.t -= 500;
  let r = await llamar(U1, { accion: 'responder', intento: e.intento, i: 0, opcion: correcta(e.pregunta) });
  reloj.t -= 501;
  r = await llamar(U1, { accion: 'responder', intento: e.intento, i: 1, opcion: correcta(r.body.pregunta) });
  reloj.t += 2000;
  r = await llamar(U1, { accion: 'responder', intento: e.intento, i: 2, opcion: correcta(r.body.pregunta) });
  assert.deepEqual([r.body.aciertos, r.body.superado], [2, false]);
  assert.equal(r.body.ms, 0 + 15000 + 2000, 'un tiempo negativo cuenta como 0 ms');
});
prueba('borrar: { ok: true }; se van la cuenta, el perfil, los intentos y el ranking; el nombre queda libre', async () => {
  const { llamar, reloj, almacen, borrados } = montar();
  await registrarAdulto(llamar); await registrarNino(llamar);
  await jugar(llamar, reloj, U1, 'Abram_1'); await jugar(llamar, reloj, UN, 'Abram_1');
  assert.equal(almacen.ranking().length, 2);
  assert.deepEqual(await llamar(UN, { accion: 'borrar' }), { status: 200, body: { ok: true } });
  assert.deepEqual(borrados, [UN], 'borra el usuario de auth');
  assert.deepEqual((await llamar(UN, { accion: 'perfil' })).body, { perfil: null });
  assert.equal([...almacen.intentos.values()].filter(x => x.perfil === UN).length, 0);
  assert.deepEqual(almacen.ranking().map(f => f.nombre), ['Roberto 92']);
  assert.equal((await registrarNino(llamar, U2)).status, 200, 'el nombre del niño queda libre');
  assert.deepEqual((await llamar(crypto.randomUUID(), { accion: 'borrar' })).body, { ok: true }, 'sin perfil también');
});
prueba('límite de llamadas: 60 por minuto y usuario; la 61 → demasiadas-llamadas (429)', async () => {
  const { llamar, reloj } = montar();
  assert.equal(L.LIMITE_POR_MINUTO, 60);
  for (let k = 0; k < 60; k++) assert.equal((await llamar(U1, { accion: 'perfil' })).status, 200, `llamada ${k + 1}`);
  assert.deepEqual(await llamar(U1, { accion: 'perfil' }), { status: 429, body: { error: 'demasiadas-llamadas' } });
  assert.equal((await llamar(U1, { accion: 'responder', intento: crypto.randomUUID(), i: 0, opcion: 0 })).status, 429, 'cuenta todas las acciones');
  assert.equal((await llamar(U2, { accion: 'perfil' })).status, 200, 'por usuario');
  reloj.t += 60001;
  assert.equal((await llamar(U1, { accion: 'perfil' })).status, 200, 'nueva ventana');
});
prueba('ranking RPC: filas de un tipo sin `tipo` ni ids; con nombre, solo esa fila; límite 1–100', () => {
  const filas = [
    { puesto: 1, nombre: 'Beto', tipo: 'adulto', puntos: 75, personajes: 1, ms: 9000 },
    { puesto: 2, nombre: 'José María', tipo: 'adulto', puntos: 40, personajes: 1, ms: 9000 },
    { puesto: 1, nombre: NOMBRE_NINO, tipo: 'nino', puntos: 30, personajes: 1, ms: 2000 },
  ];
  assert.deepEqual(L.ranking(filas, { tipo: 'adulto' }), [
    { puesto: 1, nombre: 'Beto', puntos: 75, personajes: 1, ms: 9000 }, { puesto: 2, nombre: 'José María', puntos: 40, personajes: 1, ms: 9000 }]);
  assert.deepEqual(L.ranking(filas, { tipo: 'adulto', nombre: 'José María' }).map(f => f.puesto), [2]);
  assert.deepEqual(L.ranking(filas, { tipo: 'adulto', limite: 1 }).length, 1);
  assert.deepEqual(L.ranking(filas, { tipo: 'adulto', limite: 0 }).length, 1, 'mínimo 1');
  assert.deepEqual(L.ranking(filas, { tipo: 'otro' }), []);
  assert.deepEqual(L.ranking(filas, { tipo: 'nino' }), [], 'v3: ningún nombre de niño en una lista');
  assert.deepEqual(L.ranking(filas, { tipo: 'nino', nombre: NOMBRE_NINO }), [], 'ni buscándolo por nombre');
});
prueba('posicion (v3): puesto entre los de su tipo con algún superado, total y sus totales; null sin puntos', async () => {
  const { llamar, reloj } = montar();
  assert.equal((await llamar(U1, { accion: 'posicion' })).body.error, 'sin-perfil');
  await registrarAdulto(llamar); await registrarAdulto(llamar, U2, 'Luisa'); await registrarNino(llamar);
  assert.deepEqual((await llamar(U1, { accion: 'posicion' })).body, { puesto: null, total: 0, puntos: 0, personajes: 0, ms: 0 });
  const a = (await jugar(llamar, reloj, U1, 'Abram_1', { demora: 5000 })).fin;
  const b = (await jugar(llamar, reloj, U2, 'Abram_1', { demora: 1000 })).fin;
  const c = (await jugar(llamar, reloj, U2, 'Canaan_1', { demora: 1000 })).fin;
  assert.deepEqual((await llamar(U1, { accion: 'posicion' })).body, { puesto: 2, total: 2, puntos: a.puntos, personajes: 1, ms: a.ms });
  assert.deepEqual((await llamar(U2, { accion: 'posicion' })).body, { puesto: 1, total: 2, puntos: b.puntos + c.puntos, personajes: 2, ms: b.ms + c.ms });
  // El niño: aún sin puntos, y cuenta solo entre niños.
  assert.deepEqual((await llamar(UN, { accion: 'posicion' })).body, { puesto: null, total: 0, puntos: 0, personajes: 0, ms: 0 });
  const n = (await jugar(llamar, reloj, UN, 'Abram_1')).fin;
  const r = await llamar(UN, { accion: 'posicion' });
  assert.deepEqual(r, { status: 200, body: { puesto: 1, total: 1, puntos: n.puntos, personajes: 1, ms: n.ms } });
  assert.ok(!JSON.stringify(r.body).includes(NOMBRE_NINO), 'no devuelve nombres');
});
prueba('SQL: authenticated y anon sin SELECT ni escritura en tablas; RLS en todas; solo la RPC ranking es pública', () => {
  const dir = path.join(aqui, '..', 'supabase', 'migrations');
  const sql = readdirSync(dir).filter(f => f.endsWith('.sql')).map(f => readFileSync(path.join(dir, f), 'utf8')).join('\n')
    .replace(/--[^\n]*/g, '').replace(/\s+/g, ' ').toLowerCase();
  const tablas = [...sql.matchAll(/create table public\.(\w+)/g)].map(m => m[1]);
  assert.deepEqual(tablas.sort(), ['intentos', 'llamadas', 'perfiles', 'personajes_desafio', 'preguntas']);
  for (const t of tablas) {
    assert.ok(sql.includes(`alter table public.${t} enable row level security`), `RLS en ${t}`);
    assert.match(sql, new RegExp(`revoke all on table [^;]*public\\.${t}[^;]* from public, anon, authenticated;`), `revoke en ${t}`);
  }
  assert.ok(!/create policy/.test(sql), 'sin políticas');
  assert.ok(!/create (or replace )?view/.test(sql), 'sin vistas');
  // Ningún grant de tabla a anon/authenticated (ni por columnas).
  for (const m of sql.matchAll(/grant ([^;]*?) on (table |function )?([^;]*?) to ([^;]*);/g)) {
    const [, privs, tipo, objeto, roles] = m;
    if (/\b(anon|authenticated)\b/.test(roles)) {
      assert.equal((tipo || '').trim(), 'function', `grant a ${roles}: ${privs} on ${objeto}`);
      assert.equal(privs.trim(), 'execute'); assert.match(objeto, /^public\.ranking\(/);
    }
  }
  assert.match(sql, /create function public\.ranking\(tipo text, nombre text default null, limite integer default 100\) returns setof public\.fila_ranking language sql stable security definer set search_path = ''/);
  assert.match(sql, /revoke all on function public\.ranking\(text, text, integer\) from public, anon, authenticated;/);
  assert.match(sql, /revoke all on function public\.desafio_llamada\(uuid, integer\), public\.desafio_posicion\(uuid\) from public, anon, authenticated;/);
  assert.match(sql, /grant execute on function public\.desafio_llamada\(uuid, integer\), public\.desafio_posicion\(uuid\) to service_role;/);
  assert.equal([...sql.matchAll(/create function public\.(\w+)/g)].map(m => m[1]).sort().join(), 'desafio_llamada,desafio_posicion,ranking');
  // v3: la RPC pública solo lista adultos.
  assert.match(sql, /where p\.tipo = 'adulto' and \$1 = 'adulto'/);
  assert.match(sql, /fila_ranking as \(puesto integer, nombre text, puntos integer, personajes integer, ms integer\)/, 'sin ids');
});
prueba('sin perfil: empezar, estado y renombrar → sin-perfil', async () => {
  const { llamar } = montar();
  for (const accion of ['empezar', 'estado', 'renombrar']) assert.equal((await llamar(U1, { accion, personaje: 'Abram_1', ids: [], nombre: 'Ana' })).body.error, 'sin-perfil');
});
prueba('estado: hoy, hasta y por personaje superado, puntos, intentadoHoy y último resultado', async () => {
  const { llamar, reloj } = montar();
  await registrarAdulto(llamar);
  const a = (await jugar(llamar, reloj, U1, 'Abram_1')).fin;
  await jugar(llamar, reloj, U1, 'Isaac_1', { fallar: 0 });
  const r = (await llamar(U1, { accion: 'estado' })).body;
  assert.deepEqual(r, {
    hoy: '2026-11-18', hasta: '2026-11-19T03:00:00.000Z', personajes: {
      Abram_1: { superado: true, puntos: a.puntos, intentadoHoy: true, ultimo: { aciertos: 3, total: 3 } },
      Isaac_1: { superado: false, puntos: 0, intentadoHoy: true, ultimo: { aciertos: 2, total: 3 } },
    },
  });
});
prueba('ranking del almacén tras jugar: suma de superados por tipo', async () => {
  const { llamar, reloj, almacen } = montar();
  await registrarAdulto(llamar); await registrarNino(llamar);
  const a = (await jugar(llamar, reloj, U1, 'Abram_1')).fin, b = (await jugar(llamar, reloj, U1, 'Canaan_1')).fin;
  await jugar(llamar, reloj, UN, 'Abram_1', { fallar: 2 });
  assert.deepEqual(almacen.ranking(), [{ puesto: 1, nombre: 'Roberto 92', tipo: 'adulto', puntos: a.puntos + b.puntos, personajes: 2, ms: a.ms + b.ms }]);
});

// ---------- El archivo público ----------
const rp = process.env.PREGUNTAS_JS || path.join(aqui, '..', 'datos', 'preguntas.js');
const v1 = existsSync(rd) && Object.values(cargarJs(rd).personajes).flat().some(x => 'id' in x);
if (v1) console.log(`  - (pendiente) ${rd} sigue en formato v1, con ids: regenerar con python -I herramientas/subir_preguntas.py`);
if (existsSync(rd) && existsSync(rp) && !v1) prueba('datos/desafios.js sin ids, preguntas, opciones ni citas del banco; mismas refs', () => {
  const texto = readFileSync(rd, 'utf8'), d = cargarJs(rd), P = cargarJs(rp);
  let n = 0;
  for (const [id, qs] of Object.entries(P.personajes)) {
    assert.deepEqual(d.personajes[id].map(x => x.ref), qs.map(q => q.ref), id);
    assert.deepEqual(d.personajes[id].map(x => x.nino === false), qs.map(q => q.nino === false), id);
    for (const q of qs) for (const t of [q.p, q.cita, ...q.o]) if (t.length >= 8) { assert.ok(!texto.includes(t), t); n++; }
  }
  for (const qs of Object.values(d.personajes)) qs.forEach(x => {
    assert.deepEqual(Object.keys(x).filter(k => !['ref', 'nino'].includes(k)), [], 'solo ref y nino');
    assert.ok(x.nino === undefined || x.nino === false);
  });
  console.log(`     ${n} textos del banco comprobados`);
});

for (const [nombre, fn] of pruebas) {
  try { await fn(); ok++; console.log('  ✓', nombre); } catch (e) { fallos++; console.log('  ✗', nombre, '\n    ', e.message); }
}
console.log(`\n${ok} correctas, ${fallos} fallidas`);
process.exit(fallos ? 1 : 0);
