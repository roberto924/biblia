// Lógica pura del desafío con antitrampas y del ranking (JS ESM sin dependencias: corre en Deno y en node).
// Diseño y contrato: docs/superpowers/specs/2026-11-18-ranking-mundial-design.md («Contrato app ↔ servidor»).
//
// El servidor corrige y cronometra: la app nunca recibe la respuesta correcta (ni antes ni después: el repaso solo
// trae pregunta y versículo), solo una pregunta a la vez, y cada respuesta vale solo si llega a ≤ seg + 2 s desde que
// se sirvió, medido con la hora de la base. El set lo elige el servidor entre todas las preguntas del personaje hasta
// el final de su capítulo «listo» (la app no puede forzarlo). Un intento por personaje y día en la zona horaria fijada
// al registrarse. El almacenamiento llega como parámetro (`almacen`): en la Edge Function es Postgres (index.ts); en
// pruebas y en el servidor local, crearAlmacenMemoria(). Contrato v2: «Cambios al contrato tras la revisión de
// seguridad» en el documento de diseño.

// ---------- Reglas (las mismas que herramientas/preguntas.py: ESCALA y SEGUNDOS) ----------
export const ESCALA = [[1, 3], [3, 5], [5, 7], [7, 10], [9, 12]]; // nivel mínimo → preguntas por desafío
export const SEGUNDOS = { adulto: 15, nino: 25 };
export const MARGEN_MS = 2000; // margen por la red
export const TOLERANCIA_MS = 500; // relojes desiguales: una respuesta hasta 500 ms «antes» de servirse aún vale
export const LIMITE_POR_MINUTO = 60; // llamadas a la función por usuario
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const ID_PERSONAJE_RE = /^[A-Za-z0-9_]{1,64}$/;

export function preguntasPorNivel(nivel, escala = ESCALA) {
  let n = 0;
  for (const [minimo, cuantas] of escala) if ((+nivel || 0) >= minimo) n = cuantas;
  return n;
}
export const segundosDe = tipo => (tipo === 'nino' ? SEGUNDOS.nino : SEGUNDOS.adulto);
export const plazoMs = seg => seg * 1000 + MARGEN_MS;

// Puntaje (Cálculo): 10 × n + round(5 × n × tiempo_sobrante / tiempo_total), tiempo_total = n × seg.
export function puntaje(n, msUsados, seg) {
  const total = n * seg * 1000;
  if (!(total > 0)) return 0;
  const sobrante = Math.max(0, Math.min(total, total - (+msUsados || 0)));
  return 10 * n + Math.round((5 * n * sobrante) / total);
}

// ---------- Día local y próxima medianoche en una zona IANA (con Intl) ----------
const formatos = new Map();
function formato(zona) {
  let f = formatos.get(zona);
  if (!f) {
    f = new Intl.DateTimeFormat('en-CA', { timeZone: zona, year: 'numeric', month: '2-digit', day: '2-digit' });
    formatos.set(zona, f);
  }
  return f;
}
export function zonaValida(zona) {
  if (typeof zona !== 'string' || !/^[A-Za-z0-9_+\-/]{1,64}$/.test(zona)) return false;
  try { formato(zona); return true; } catch { return false; }
}
// 'AAAA-MM-DD' del instante t (ms) en la zona.
export function diaEnZona(t, zona) {
  const partes = formato(zona).formatToParts(new Date(t));
  const g = tipo => partes.find(p => p.type === tipo).value;
  return `${g('year')}-${g('month')}-${g('day')}`;
}
// Primer instante (ms) en que el día local de la zona ya es posterior al de t. Búsqueda binaria: sirve también
// cuando la medianoche no existe por cambio de horario (Chile salta de 23:59:59 a 01:00).
export function proximaMedianoche(t, zona) {
  const hoy = diaEnZona(t, zona);
  let lo = t, hi = t + 50 * 3600 * 1000;
  while (hi - lo > 1) {
    const m = Math.floor((lo + hi) / 2);
    if (diaEnZona(m, zona) > hoy) hi = m; else lo = m;
  }
  return hi;
}

// ---------- Azar y barajado ----------
export function azarSeguro() {
  const a = new Uint32Array(1);
  crypto.getRandomValues(a);
  return a[0] / 4294967296;
}
export function barajar(xs, azar = azarSeguro) {
  const a = xs.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(azar() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}
// n preguntas al azar del grupo, cada una con el orden de sus opciones: orden[mostrada] = índice original.
export function elegirPreguntas(grupo, n, azar = azarSeguro) {
  return barajar(grupo, azar).slice(0, n).map(q => ({ id: q.id, orden: barajar([0, 1, 2, 3], azar) }));
}
// Lo único que ve la app de una pregunta: texto y opciones en el orden servido (nunca la correcta ni la cita).
export const servir = (q, orden) => ({ p: q.p, o: orden.map(k => q.o[k]) });

// ---------- Nombres ----------
// Niño: sustantivo + adjetivo + número 1–999. Palabras del mundo bíblico sin personas reales; adjetivos que no cambian
// con el género, para que siempre concuerden.
export const SUSTANTIVOS = [
  'Pastor', 'Estrella', 'Cordero', 'Paloma', 'Olivo', 'Cedro', 'Higuera', 'Viña', 'Arca', 'Lámpara', 'Sembrador',
  'Pescador', 'Alfarero', 'Viajero', 'Peregrino', 'Camello', 'León', 'Águila', 'Arcoíris', 'Trigo', 'Manantial',
  'Pozo', 'Monte', 'Río', 'Tienda', 'Rollo', 'Arpa', 'Trompeta', 'Granada', 'Palmera', 'Cántaro', 'Sandalia',
  'Oasis', 'Faro', 'Rebaño', 'Gacela', 'Cayado', 'Racimo', 'Lucero', 'Junco',
];
export const ADJETIVOS = [
  'Alegre', 'Valiente', 'Fiel', 'Humilde', 'Amable', 'Fuerte', 'Paciente', 'Feliz', 'Veloz', 'Noble', 'Prudente',
  'Constante', 'Brillante', 'Gentil', 'Leal', 'Dulce', 'Firme', 'Audaz', 'Jovial', 'Ágil', 'Tenaz', 'Cordial',
  'Sonriente', 'Radiante', 'Diligente', 'Capaz', 'Cortés',
];
export const normalizarNombre = s => String(s ?? '').normalize('NFC').trim().replace(/\s+/g, ' ');
const sinTildes = s => s.normalize('NFD').replace(/\p{M}/gu, '');
// Clave de unicidad: sin mayúsculas ni tildes («José» y «jose» chocan). Se guarda en perfiles.nombre_clave.
export const claveNombre = s => sinTildes(normalizarNombre(s).toLowerCase());
const clave = claveNombre;

export function generarNombreNino(azar = azarSeguro) {
  const s = SUSTANTIVOS[Math.floor(azar() * SUSTANTIVOS.length)];
  const a = ADJETIVOS[Math.floor(azar() * ADJETIVOS.length)];
  return `${s} ${a} ${1 + Math.floor(azar() * 999)}`;
}
// k nombres distintos que no estén en `usados` (claves en minúsculas).
export function generarNombresNino(k = 5, azar = azarSeguro, usados = new Set()) {
  const out = new Map();
  for (let vueltas = 0; out.size < k && vueltas < k * 50; vueltas++) {
    const n = generarNombreNino(azar);
    if (!usados.has(clave(n)) && !out.has(clave(n))) out.set(clave(n), n);
  }
  return [...out.values()];
}
// El nombre de un niño debe salir del generador, tal cual (mismas mayúsculas y tildes).
export function esNombreNino(nombre) {
  const m = /^(\S+) (\S+) ([1-9]\d{0,2})$/.exec(normalizarNombre(nombre));
  return !!m && SUSTANTIVOS.includes(m[1]) && ADJETIVOS.includes(m[2]);
}

// Adulto: 3–20 letras, números o espacios; filtro de palabras ofensivas (español e inglés).
// Raíces: se buscan dentro del nombre sin espacios. Palabras: deben ser una palabra entera (o el nombre entero sin
// espacios), para no tachar «computadora», «disputa», «Vergara» o «Essex». Es un filtro, no una moderación completa.
const RAICES = [
  'mierd', 'pendej', 'cabron', 'hijueput', 'hijodeput', 'conchetumadre', 'conchetumare', 'conchesumadre',
  'conchasumadre', 'culiao', 'culiado', 'aweonao', 'weon', 'hueon', 'huevon', 'maricon', 'malparid', 'gonorrea',
  'chingad', 'chingar', 'mamaguev', 'joder', 'jodete', 'follar', 'estupid', 'imbecil', 'idiota', 'pedofil',
  'fuck', 'bitch', 'nigger', 'nigga', 'faggot', 'asshole', 'motherf', 'pussy', 'porno', 'porn', 'hitler', 'dildo',
  'orgasm', 'masturb',
];
const PALABRAS = new Set([
  'puta', 'puto', 'putas', 'putos', 'putita', 'putito', 'ctm', 'csm', 'ql', 'qlo', 'qliao', 'culo', 'culos', 'verga',
  'vergas', 'pene', 'penes', 'vagina', 'sexo', 'sex', 'sexy', 'polla', 'zorra', 'perra', 'marica', 'chucha', 'teta',
  'tetas', 'tonto', 'tonta', 'shit', 'shitty', 'cunt', 'dick', 'cock', 'whore', 'slut', 'ass', 'rape', 'nazi',
  'nazis', 'idiot', 'stupid', 'bastard', 'semen', 'tits', 'boobs', 'penis', 'fag', 'fags', 'kkk', 'cum',
]);
const LEET = { 0: 'o', 1: 'i', 3: 'e', 4: 'a', 5: 's', 7: 't', 8: 'b', 9: 'g' };
const colapsar1 = s => s.replace(/(.)\1+/g, '$1'); // «puuuta» → «puta»
const colapsar2 = s => s.replace(/(.)\1{2,}/g, '$1$1'); // «perrrra» → «perra», pero «pera» sigue siendo «pera»
const sinDobles = r => colapsar1(r) === r;

export function esOfensivo(nombre) {
  const base = sinTildes(normalizarNombre(nombre).toLowerCase());
  const leet = base.replace(/[0-9]/g, d => LEET[d] ?? d);
  for (const b of new Set([base, leet])) {
    // f2 se compara con todo; f1 (todo colapsado) solo con lo que no tiene letras dobles.
    for (const [f, vale] of [[colapsar2(b), () => true], [colapsar1(b), sinDobles]]) {
      const junto = f.replace(/ /g, '');
      if (RAICES.some(r => vale(r) && junto.includes(r))) return true;
      const ps = [...f.split(' '), junto];
      if (ps.some(p => PALABRAS.has(p) && vale(p))) return true;
    }
  }
  return false;
}
// Solo alfabeto latino (con tildes, diéresis y ñ), números ASCII y espacios: sin cirílico, griego, letras de ancho
// completo ni otros parecidos que permitan suplantar un nombre.
const LATINO_RE = /^[A-Za-z0-9 ÁÉÍÓÚÜÑÀÈÌÒÙÂÊÎÔÛÄËÏÖÇáéíóúüñàèìòùâêîôûäëïöç]{3,20}$/;
// → { nombre } | { error: 'nombre-invalido' | 'nombre-ofensivo' } (se normaliza antes de validar y filtrar)
export function validarNombreAdulto(nombre) {
  if (typeof nombre !== 'string') return { error: 'nombre-invalido' };
  const n = normalizarNombre(nombre);
  if (!LATINO_RE.test(n) || !/[A-Za-z0-9]/.test(sinTildes(n))) return { error: 'nombre-invalido' };
  if (esOfensivo(n)) return { error: 'nombre-ofensivo' };
  return { nombre: n };
}

// ---------- Ranking (igual que la función SQL public.ranking) ----------
// Solo perfiles con algún personaje superado; puesto = rank() por tipo (puntos desc, ms asc).
function filasRanking(perfiles, intentos) {
  const acc = new Map();
  for (const it of intentos) {
    if (!it.superado) continue;
    const p = perfiles.find(x => x.id === it.perfil);
    if (!p) continue;
    const a = acc.get(p.id) || { id: p.id, nombre: p.nombre, tipo: p.tipo, puntos: 0, personajes: 0, ms: 0 };
    a.puntos += it.puntos; a.personajes += 1; a.ms += it.ms;
    acc.set(p.id, a);
  }
  const filas = [...acc.values()];
  for (const tipo of ['adulto', 'nino']) {
    const xs = filas.filter(f => f.tipo === tipo).sort((a, b) => b.puntos - a.puntos || a.ms - b.ms);
    xs.forEach((f, k) => {
      const prev = xs[k - 1];
      f.puesto = prev && prev.puntos === f.puntos && prev.ms === f.ms ? prev.puesto : k + 1;
    });
  }
  return filas.sort((a, b) => (a.tipo < b.tipo ? -1 : a.tipo > b.tipo ? 1 : a.puesto - b.puesto));
}
// Todas las filas, sin ids (uso interno: el servidor local y las pruebas).
export function calcularRanking(perfiles, intentos) {
  return filasRanking(perfiles, intentos)
    .map(f => ({ puesto: f.puesto, nombre: f.nombre, tipo: f.tipo, puntos: f.puntos, personajes: f.personajes, ms: f.ms }));
}
// Acción `posicion` (igual que la función SQL public.desafio_posicion): el puesto del perfil entre los de su tipo con
// algún superado (null si aún no tiene puntos), cuántos son y sus totales. null si el perfil no existe.
export function calcularPosicion(perfiles, intentos, uid) {
  const yo = perfiles.find(p => p.id === uid);
  if (!yo) return null;
  const filas = filasRanking(perfiles, intentos).filter(f => f.tipo === yo.tipo);
  const f = filas.find(x => x.id === uid);
  return { puesto: f ? f.puesto : null, total: filas.length, puntos: f ? f.puntos : 0, personajes: f ? f.personajes : 0, ms: f ? f.ms : 0 };
}
// Lo que devuelve la RPC `ranking { tipo, nombre?, limite? }`: solo adultos (v3: ningún nombre de niño se publica en
// una lista; con 'nino', vacío); sin `tipo`; con nombre, solo esa fila (sin distinguir mayúsculas ni tildes);
// límite entre 1 y 100.
export function ranking(filas, { tipo, nombre = null, limite = 100 } = {}) {
  const lim = Math.min(100, Math.max(1, Number.isInteger(limite) ? limite : 100));
  if (tipo !== 'adulto') return [];
  return filas
    .filter(f => f.tipo === tipo && (nombre == null || claveNombre(f.nombre) === claveNombre(nombre)))
    .sort((a, b) => a.puesto - b.puesto || (a.nombre < b.nombre ? -1 : 1))
    .slice(0, lim)
    .map(f => ({ puesto: f.puesto, nombre: f.nombre, puntos: f.puntos, personajes: f.personajes, ms: f.ms }));
}

// ---------- Servicio: las acciones del contrato (v2 + v3: `posicion`) ----------
const HTTP = {
  'no-autorizado': 401, 'datos-invalidos': 400, 'accion-desconocida': 400, 'zona-invalida': 400,
  'nombre-invalido': 400, 'nombre-ofensivo': 400, 'falta-consentimiento': 400, 'nombre-usado': 409,
  'ya-registrado': 409, 'solo-adulto': 403, 'sin-perfil': 403, 'sin-desafio': 404, 'superado': 409,
  'ya-intentado-hoy': 409, 'faltan-preguntas': 409, 'intento-invalido': 404, 'fuera-de-orden': 409,
  'demasiadas-llamadas': 429,
};
const esEntero = x => Number.isInteger(x);
const porCreado = (a, b) => (a.creado < b.creado ? -1 : a.creado > b.creado ? 1 : 0);
// Intento sin cerrar cuya pregunta en curso aún está en plazo (alguien lo está jugando).
export const intentoAbierto = (it, t) => !it.terminado && it.i < it.total && t - it.servidas_en[it.i] <= plazoMs(it.seg);

/**
 * almacen (todo async):
 *  perfil(uid) → { id, nombre, tipo, zona } | null
 *  nombresUsados(claves) → claves (de la lista) ya usadas
 *  crearPerfil({ id, nombre, nombre_clave, tipo, zona, consentimiento_en }) → 'ok' | 'nombre-usado' | 'ya-registrado'
 *  cambiarNombre(uid, nombre, nombre_clave) → 'ok' | 'nombre-usado'
 *  personaje(id) → { id, nivel, n, sinNino, hasta } | null   (hasta = ordinal del último versículo del capítulo listo)
 *  preguntasDe(personaje) → [{ id, personaje, ref, orden, cita, p, o[4], c, nino }]   (orden = ordinal del versículo)
 *  preguntasPorId(ids) → ídem
 *  intentosDe(uid, personaje?) → [fila de intento]
 *  crearIntento(fila) → fila con id | null si ya hay uno de ese perfil, personaje y día
 *  intento(id) → fila | null
 *  guardarIntento(id, iEsperado, cambios) → 'ok' | 'conflicto' (su `i` ya cambió) | 'superado' (ya hay otro superado)
 *  llamada(uid, limite) → { permitido, ahora }: cuenta la llamada (false si pasó de `limite` en el minuto) y da la
 *      hora en ms con que se sirve y cronometra todo (en la Edge Function, la de la base: una sola RPC)
 *  posicion(uid) → { puesto | null, total, puntos, personajes, ms } entre los de su tipo, o null sin perfil
 *  borrarCuenta(uid) → borra el usuario de auth y, en cascada, su perfil, intentos y contador
 */
export function crearServicio({ almacen, azar = azarSeguro, limitePorMinuto = LIMITE_POR_MINUTO }) {
  const error = (codigo, extra) => ({ status: HTTP[codigo] || 400, body: { error: codigo, ...(extra || {}) } });
  const ok = body => ({ status: 200, body });
  const iso = t => new Date(t).toISOString();

  const acciones = {
    async perfil(uid) {
      const p = await almacen.perfil(uid);
      return ok({ perfil: p ? { nombre: p.nombre, tipo: p.tipo } : null });
    },

    async nombres() {
      let nombres = [];
      for (let vuelta = 0; vuelta < 5 && nombres.length < 5; vuelta++) {
        const cand = generarNombresNino(5 - nombres.length, azar, new Set(nombres.map(clave)));
        const ocupados = new Set(await almacen.nombresUsados(cand.map(clave)));
        nombres = nombres.concat(cand.filter(n => !ocupados.has(clave(n))));
      }
      return ok({ nombres });
    },

    async registrar(uid, c, t) {
      if (await almacen.perfil(uid)) return error('ya-registrado');
      if (c.tipo !== 'adulto' && c.tipo !== 'nino') return error('datos-invalidos');
      if (!zonaValida(c.zona)) return error('zona-invalida');
      let nombre;
      if (c.tipo === 'nino') {
        // Ley 21.719 (Chile), art. 16 quáter: consentimiento de un adulto (lo declara en la app con su PIN).
        if (c.consentimiento !== true) return error('falta-consentimiento');
        if (typeof c.nombre !== 'string' || !esNombreNino(c.nombre)) return error('nombre-invalido');
        nombre = normalizarNombre(c.nombre);
      } else {
        const v = validarNombreAdulto(c.nombre);
        if (v.error) return error(v.error);
        nombre = v.nombre;
      }
      const r = await almacen.crearPerfil({
        id: uid, nombre, nombre_clave: clave(nombre), tipo: c.tipo, zona: c.zona,
        consentimiento_en: c.tipo === 'nino' ? iso(t) : null,
      });
      if (r !== 'ok') return error(r);
      return ok({ perfil: { nombre, tipo: c.tipo } });
    },

    async renombrar(uid, c) {
      const p = await almacen.perfil(uid);
      if (!p) return error('sin-perfil');
      if (p.tipo !== 'adulto') return error('solo-adulto');
      const v = validarNombreAdulto(c.nombre);
      if (v.error) return error(v.error);
      const r = await almacen.cambiarNombre(uid, v.nombre, clave(v.nombre));
      if (r !== 'ok') return error(r);
      return ok({ perfil: { nombre: v.nombre, tipo: p.tipo } });
    },

    // v3: la posición propia (el niño no aparece en ninguna lista; ve «Vas 12.º de 340»).
    async posicion(uid) {
      const r = await almacen.posicion(uid);
      if (!r) return error('sin-perfil');
      return ok({ puesto: r.puesto ?? null, total: r.total, puntos: r.puntos, personajes: r.personajes, ms: r.ms });
    },

    async borrar(uid) {
      await almacen.borrarCuenta(uid);
      return ok({ ok: true });
    },

    async estado(uid, _c, t) {
      const p = await almacen.perfil(uid);
      if (!p) return error('sin-perfil');
      const hoy = diaEnZona(t, p.zona);
      const xs = (await almacen.intentosDe(uid)).slice().sort(porCreado);
      const personajes = {};
      for (const it of xs) {
        const e = personajes[it.personaje] || (personajes[it.personaje] = { superado: false, puntos: 0, intentadoHoy: false, ultimo: null });
        if (it.superado) { e.superado = true; e.puntos = Math.max(e.puntos, it.puntos); }
        if (it.dia === hoy || intentoAbierto(it, t)) e.intentadoHoy = true;
        e.ultimo = { aciertos: it.aciertos, total: it.total };
      }
      return ok({ hoy, hasta: iso(proximaMedianoche(t, p.zona)), personajes });
    },

    // `ids` (contrato v1) se ignora: el set lo elige el servidor.
    async empezar(uid, c, t) {
      const p = await almacen.perfil(uid);
      if (!p) return error('sin-perfil');
      if (typeof c.personaje !== 'string' || !ID_PERSONAJE_RE.test(c.personaje)) return error('datos-invalidos');
      const pj = await almacen.personaje(c.personaje);
      if (!pj || !(pj.n > 0) || (p.tipo === 'nino' && pj.sinNino)) return error('sin-desafio');
      const previos = await almacen.intentosDe(uid, c.personaje);
      if (previos.some(x => x.superado)) return error('superado');
      const hoy = diaEnZona(t, p.zona), hasta = iso(proximaMedianoche(t, p.zona));
      if (previos.some(x => x.dia === hoy || intentoAbierto(x, t))) return error('ya-intentado-hoy', { hasta });
      // Todas las del personaje hasta el final de su capítulo «listo»; para el niño, solo las aptas.
      const grupo = (await almacen.preguntasDe(c.personaje)).filter(q =>
        q.personaje === c.personaje && Number.isInteger(q.orden) && Number.isInteger(pj.hasta) && q.orden <= pj.hasta &&
        (p.tipo !== 'nino' || q.nino !== false));
      if (grupo.length < pj.n) return error('faltan-preguntas');
      const servidas = elegirPreguntas(grupo, pj.n, azar);
      const seg = segundosDe(p.tipo);
      const fila = await almacen.crearIntento({
        perfil: uid, personaje: c.personaje, dia: hoy, seg, total: pj.n, servidas, servidas_en: [t], respuestas: [],
        i: 0, aciertos: 0, ms: 0, terminado: false, superado: false, puntos: 0,
      });
      if (!fila) return error('ya-intentado-hoy', { hasta });
      const q0 = grupo.find(q => q.id === servidas[0].id);
      return ok({ intento: fila.id, n: pj.n, seg, i: 0, pregunta: servir(q0, servidas[0].orden) });
    },

    async responder(uid, c, t) {
      if (!esEntero(c.i) || c.i < 0 || !esEntero(c.opcion) || c.opcion < -1 || c.opcion > 3) return error('datos-invalidos');
      if (typeof c.intento !== 'string' || !UUID_RE.test(c.intento)) return error('intento-invalido');
      const it = await almacen.intento(c.intento);
      if (!it || it.perfil !== uid || it.terminado) return error('intento-invalido');
      if (c.i !== it.i || c.i >= it.total) return error('fuera-de-orden');
      const p = await almacen.perfil(uid);
      if (!p) return error('sin-perfil');
      const i = c.i, s = it.servidas[i];
      const necesarias = i + 1 < it.total ? [s.id, it.servidas[i + 1].id] : it.servidas.map(x => x.id);
      const qs = new Map((await almacen.preguntasPorId(necesarias)).map(q => [q.id, q]));
      const q = qs.get(s.id);
      if (!q || necesarias.some(id => !qs.has(id))) return error('intento-invalido'); // el banco cambió a medio intento
      const transcurrido = t - it.servidas_en[i];
      const aTiempo = transcurrido >= -TOLERANCIA_MS && transcurrido <= plazoMs(it.seg);
      const acierto = c.opcion >= 0 && aTiempo && s.orden[c.opcion] === q.c;
      const msPregunta = c.opcion >= 0 && aTiempo ? Math.max(0, Math.min(transcurrido, it.seg * 1000)) : it.seg * 1000;
      const respuestas = it.respuestas.concat([{ opcion: c.opcion, acierto, ms: msPregunta }]);
      const aciertos = it.aciertos + (acierto ? 1 : 0), ms = it.ms + msPregunta;
      if (i + 1 < it.total) {
        const r = await almacen.guardarIntento(it.id, i, { i: i + 1, respuestas, aciertos, ms, servidas_en: it.servidas_en.concat([t]) });
        if (r !== 'ok') return error('fuera-de-orden');
        const sig = it.servidas[i + 1];
        return ok({ i: i + 1, pregunta: servir(qs.get(sig.id), sig.orden) });
      }
      const superado = aciertos === it.total;
      const puntos = superado ? puntaje(it.total, ms, it.seg) : 0;
      const r = await almacen.guardarIntento(it.id, i, { i: i + 1, respuestas, aciertos, ms, terminado: true, superado, puntos });
      if (r === 'superado') return error('superado'); // otro intento del mismo personaje se superó antes
      if (r !== 'ok') return error('fuera-de-orden');
      const fin = { fin: true, aciertos, total: it.total, ms, superado, puntos, hasta: iso(proximaMedianoche(t, p.zona)) };
      // Repaso solo si superó, y sin respuesta ni cita: pregunta y versículo para leerlo. Si no, solo «a de n».
      if (superado) fin.repaso = it.servidas.map(x => { const r2 = qs.get(x.id); return { p: r2.p, ref: r2.ref }; });
      return ok(fin);
    },
  };

  async function manejar(uid, cuerpo) {
    if (typeof uid !== 'string' || !uid) return error('no-autorizado');
    const { permitido, ahora: t } = await almacen.llamada(uid, limitePorMinuto);
    if (!permitido) return error('demasiadas-llamadas');
    if (!cuerpo || typeof cuerpo !== 'object' || Array.isArray(cuerpo)) return error('datos-invalidos');
    const accion = Object.hasOwn(acciones, cuerpo.accion) ? acciones[cuerpo.accion] : null;
    if (!accion) return error('accion-desconocida');
    return accion(uid, cuerpo, t);
  }
  return { manejar };
}

// ---------- Almacenamiento en memoria (pruebas y herramientas/servidor_local.mjs) ----------
// Imita las restricciones de la base: nombre_clave único, un intento por perfil+personaje+día, un solo superado por
// perfil+personaje, guardado solo si `i` no cambió (dos respuestas simultáneas: gana una), contador por minuto y
// borrado en cascada.
export function crearAlmacenMemoria({ preguntas = [], personajes = [], alBorrar = () => {}, ahora = () => Date.now() } = {}) {
  const P = new Map(preguntas.map(q => [q.id, q]));
  const PJ = new Map(personajes.map(x => [x.id, x]));
  const perfiles = new Map(), intentos = new Map(), llamadas = new Map();
  let orden = 0;
  const copia = x => (x == null ? null : structuredClone(x));
  const usado = (claveN, excepto) => [...perfiles.values()].some(p => p.id !== excepto && p.nombre_clave === claveN);
  return {
    perfiles, intentos, llamadas,
    async perfil(uid) { return copia(perfiles.get(uid)); },
    async nombresUsados(claves) { return claves.filter(k => usado(k)); },
    async crearPerfil(p) {
      if (perfiles.has(p.id)) return 'ya-registrado';
      if (usado(p.nombre_clave)) return 'nombre-usado';
      perfiles.set(p.id, { ...copia(p), creado: new Date().toISOString() });
      return 'ok';
    },
    async cambiarNombre(uid, nombre, nombreClave) {
      if (usado(nombreClave, uid)) return 'nombre-usado';
      Object.assign(perfiles.get(uid), { nombre, nombre_clave: nombreClave });
      return 'ok';
    },
    async personaje(id) { return copia(PJ.get(id)); },
    async preguntasDe(personaje) { return [...P.values()].filter(q => q.personaje === personaje).map(copia); },
    async preguntasPorId(ids) { return ids.map(id => P.get(id)).filter(Boolean).map(copia); },
    async intentosDe(uid, personaje) {
      return [...intentos.values()].filter(x => x.perfil === uid && (!personaje || x.personaje === personaje)).map(copia);
    },
    async crearIntento(fila) {
      if ([...intentos.values()].some(x => x.perfil === fila.perfil && x.personaje === fila.personaje && x.dia === fila.dia)) return null;
      const f = { ...copia(fila), id: crypto.randomUUID(), creado: String(++orden).padStart(12, '0') };
      intentos.set(f.id, f);
      return copia(f);
    },
    async intento(id) { return copia(intentos.get(id)); },
    async guardarIntento(id, iEsperado, cambios) {
      const it = intentos.get(id);
      if (!it || it.i !== iEsperado) return 'conflicto';
      // Como el índice único intentos_un_superado.
      if (cambios.superado && [...intentos.values()].some(x => x !== it && x.superado && x.perfil === it.perfil && x.personaje === it.personaje)) return 'superado';
      Object.assign(it, copia(cambios));
      return 'ok';
    },
    async llamada(uid, limite) {
      const t = ahora(), c = llamadas.get(uid);
      if (!c || c.ventana < t - 60000) { llamadas.set(uid, { ventana: t, n: 1 }); return { permitido: 1 <= limite, ahora: t }; }
      c.n += 1;
      return { permitido: c.n <= limite, ahora: t };
    },
    async posicion(uid) { return calcularPosicion([...perfiles.values()], [...intentos.values()], uid); },
    async borrarCuenta(uid) {
      perfiles.delete(uid); llamadas.delete(uid);
      for (const [id, x] of intentos) if (x.perfil === uid) intentos.delete(id);
      alBorrar(uid);
    },
    ranking() { return calcularRanking([...perfiles.values()], [...intentos.values()]); },
  };
}
