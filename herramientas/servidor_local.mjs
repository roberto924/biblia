// Servidor SOLO PARA DESARROLLO que imita el contrato app ↔ servidor del desafío
// (docs/superpowers/specs/2026-11-18-ranking-mundial-design.md, contrato v2) para probar la app antes de desplegar.
//
// Uso: node herramientas/servidor_local.mjs        → http://127.0.0.1:54321 (PUERTO=… para otro)
// En la app: window.BIBLIA_SERVIDOR = { url: "http://127.0.0.1:54321", anon: "anon-local" }
//
// Imita: POST /auth/v1/signup (alta anónima falsa), POST /auth/v1/token?grant_type=refresh_token,
// POST /functions/v1/desafio (logica.js, con `borrar`, `posicion` y el límite de llamadas) y POST /rest/v1/rpc/ranking
// (v3: solo adultos; con tipo nino, vacío).
// Todo en memoria (se pierde al cerrar). Banco: datos/preguntas.js (local, fuera de git); el tope de cada personaje
// (final de su capítulo «listo») sale de datos/juego.js y datos/biblia.js, como en herramientas/subir_preguntas.py.
// CORS para http://localhost:* y http://127.0.0.1:*.
import { createServer } from 'node:http';
import { readFileSync, existsSync } from 'node:fs';
import { createHash, randomUUID, randomBytes } from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { crearServicio, crearAlmacenMemoria, preguntasPorNivel, ranking } from '../supabase/functions/desafio/logica.js';

const raiz = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const PUERTO = +(process.env.PUERTO || 54321);
const cargarJs = r => { const s = readFileSync(r, 'utf8'); return JSON.parse(s.slice(s.indexOf('{'), s.lastIndexOf('}') + 1)); };

const rutaPreg = path.join(raiz, 'datos', 'preguntas.js');
if (!existsSync(rutaPreg)) {
  console.error('Falta datos/preguntas.js: corre python -I herramientas/preguntas.py');
  process.exit(1);
}
const P = cargarJs(rutaPreg), J = cargarJs(path.join(raiz, 'datos', 'juego.js')), B = cargarJs(path.join(raiz, 'datos', 'biblia.js'));
const idPregunta = (pj, p) => createHash('sha256').update(`${pj}\n${p}`, 'utf8').digest('hex').slice(0, 16);
// Ordinal de cada versículo (Gn 1:1 = 0) y el último de cada capítulo.
const orden = new Map(), ultimo = new Map(), libros = B.libros.map(l => l.id);
for (const c of B.capitulos.slice().sort((a, b) => libros.indexOf(a.libro) - libros.indexOf(b.libro) || a.cap - b.cap)) {
  for (const v of c.versiculos) { ultimo.set(`${c.libro} ${c.cap}`, orden.size); orden.set(`${c.libro} ${c.cap}:${v.n}`, orden.size); }
}

const preguntas = [], personajes = [];
for (const [pj, qs] of Object.entries(P.personajes)) {
  const e = J.personajes[pj] || {}, nivel = e.nivel || 0, hasta = ultimo.get((e.listo || {}).capitulo);
  if (hasta === undefined) { console.warn(`AVISO: ${pj} sin capítulo «listo»: sin desafío`); continue; }
  personajes.push({ id: pj, nivel, n: preguntasPorNivel(nivel, P.escala), hasta, sinNino: (P.sinNino || []).includes(pj) });
  for (const q of qs) preguntas.push({ id: idPregunta(pj, q.p), personaje: pj, ref: q.ref, orden: orden.get(q.ref), cita: q.cita, p: q.p, o: q.o, c: q.c, nino: q.nino !== false });
}

// Auth anónima falsa: tokens con forma de JWT (sin firma real) → uid. `borrar` los olvida (como deleteUser).
const accesos = new Map(), renovaciones = new Map();
const olvidar = uid => {
  for (const [k, v] of accesos) if (v.uid === uid) accesos.delete(k);
  for (const [k, v] of renovaciones) if (v === uid) renovaciones.delete(k);
};
const almacen = crearAlmacenMemoria({ preguntas, personajes, alBorrar: olvidar });
const servicio = crearServicio({ almacen });

const b64 = o => Buffer.from(JSON.stringify(o)).toString('base64url');
function sesion(uid) {
  const exp = Math.floor(Date.now() / 1000) + 3600;
  const access_token = `${b64({ alg: 'none', typ: 'JWT' })}.${b64({ sub: uid, role: 'authenticated', is_anonymous: true, exp })}.${randomBytes(16).toString('base64url')}`;
  const refresh_token = randomBytes(24).toString('base64url');
  accesos.set(access_token, { uid, exp }); renovaciones.set(refresh_token, uid);
  return { access_token, token_type: 'bearer', expires_in: 3600, expires_at: exp, refresh_token, user: { id: uid, role: 'authenticated', is_anonymous: true } };
}

const ORIGEN_LOCAL = /^http:\/\/(localhost|127\.0\.0\.1)(:\d{1,5})?$/;
function enviar(req, res, status, body) {
  const h = {
    'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', Vary: 'Origin',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'authorization, apikey, content-type, x-client-info, prefer',
  };
  const o = req.headers.origin;
  if (o && ORIGEN_LOCAL.test(o)) h['Access-Control-Allow-Origin'] = o;
  res.writeHead(status, h);
  res.end(body === undefined ? '' : JSON.stringify(body));
}
const leer = req => new Promise((ok, mal) => {
  let s = ''; req.setEncoding('utf8');
  req.on('data', c => { s += c; if (s.length > 16384) { mal(new Error('grande')); req.destroy(); } });
  req.on('end', () => ok(s)); req.on('error', mal);
});
const leerJson = async req => { try { return JSON.parse(await leer(req) || '{}'); } catch { return null; } };

createServer(async (req, res) => {
  const u = new URL(req.url, `http://${req.headers.host || '127.0.0.1'}`);
  const log = status => console.log(`${new Date().toISOString().slice(11, 19)} ${req.method} ${u.pathname}${u.search} → ${status}`);
  const fin = (status, body) => { log(status); return enviar(req, res, status, body); };
  try {
    if (req.method === 'OPTIONS') return fin(204);
    if (!req.headers.apikey) return fin(401, { message: 'No API key found in request' });
    if (req.method === 'POST' && u.pathname === '/auth/v1/signup') { await leer(req); return fin(200, sesion(randomUUID())); }
    if (req.method === 'POST' && u.pathname === '/auth/v1/token' && u.searchParams.get('grant_type') === 'refresh_token') {
      const c = await leerJson(req) || {};
      const uid = renovaciones.get(c.refresh_token);
      if (!uid) return fin(400, { error: 'invalid_grant', error_description: 'Invalid Refresh Token' });
      renovaciones.delete(c.refresh_token);
      return fin(200, sesion(uid));
    }
    if (req.method === 'POST' && u.pathname === '/functions/v1/desafio') {
      const a = accesos.get((req.headers.authorization || '').replace(/^Bearer\s+/i, ''));
      if (!a || a.exp * 1000 < Date.now()) return fin(401, { error: 'no-autorizado' });
      const cuerpo = await leerJson(req);
      if (cuerpo === null) return fin(400, { error: 'datos-invalidos' });
      const r = await servicio.manejar(a.uid, cuerpo);
      return fin(r.status, r.body);
    }
    if (req.method === 'POST' && u.pathname === '/rest/v1/rpc/ranking') {
      const c = await leerJson(req);
      if (!c || typeof c.tipo !== 'string') return fin(400, { message: 'falta tipo' });
      return fin(200, ranking(almacen.ranking(), { tipo: c.tipo, nombre: c.nombre ?? null, limite: c.limite ?? 100 }));
    }
    return fin(404, { message: 'no existe' });
  } catch (e) {
    console.error(e);
    return fin(500, { error: 'error-servidor' });
  }
}).on('error', e => {
  console.error(e.code === 'EADDRINUSE' ? `El puerto ${PUERTO} está ocupado (¿otro servidor local?). Usa PUERTO=… para otro.` : e);
  process.exit(1);
}).listen(PUERTO, '127.0.0.1', () => {
  console.log(`Servidor local del desafío (solo desarrollo) en http://127.0.0.1:${PUERTO}`);
  console.log(`  ${personajes.length} personajes, ${preguntas.length} preguntas en memoria`);
  console.log(`  En la app: window.BIBLIA_SERVIDOR = { url: "http://127.0.0.1:${PUERTO}", anon: "anon-local" }`);
});
