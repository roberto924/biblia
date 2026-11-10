/* Biblia · Compañero de lectura — lógica pura (Nucleo) + interfaz.
   Nucleo no usa DOM: pruebas/probar.mjs lo evalúa con node:vm y lo lee de globalThis.BibliaNucleo. */
'use strict';

const Nucleo = (() => {
  const TRADS = ['TM', 'LXX'];
  const TIPOS = ['al_engendrar', 'restantes', 'total'];

  const norm = s => String(s == null ? '' : s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
  const num = v => (v === null || v === undefined || v === '' || !Number.isFinite(+v)) ? null : +v;

  function parseRef(ref) {
    const m = /(\d+)\s*:\s*(\d+)/.exec(ref || '');
    if (m) return { cap: +m[1], v: +m[2] };
    const c = /(\d+)\s*$/.exec(ref || '');
    return c ? { cap: +c[1], v: null } : null;
  }

  // Clave numérica comparable de un versículo: Gn 4:1 → 4001
  function clave(ref) { const r = parseRef(ref); return r && r.v ? r.cap * 1000 + r.v : null; }
  const refTxt = (cap, v) => `Gn ${cap}:${v}`;

  function claseCerteza(c) {
    if (c === 'explicito' || c === 'texto') return 'texto';
    if (c === 'calculo') return 'calculo';
    return 'inferido';
  }

  function indexar(d) {
    d = d || {};
    const personas = new Map(), hijos = new Map(), padres = new Map(), conyuges = new Map(), edades = new Map();
    const add = (m, k, v) => { if (!m.has(k)) m.set(k, []); m.get(k).push(v); };
    (d.personas || []).forEach(p => { if (p && p.id) personas.set(p.id, p); });
    const asegurar = id => { if (!personas.has(id)) personas.set(id, { id, nombre: String(id).replace(/_\d+$/, ''), sexo: '?', refs: [] }); };
    (d.relaciones || []).forEach(r => {
      if (!r || !r.de || !r.a || r.de === r.a) return;
      asegurar(r.de); asegurar(r.a);
      if (r.tipo === 'padre' || r.tipo === 'madre') { add(hijos, r.de, r); add(padres, r.a, r); }
      else if (r.tipo === 'conyuge') { add(conyuges, r.de, Object.assign({}, r, { otro: r.a })); add(conyuges, r.a, Object.assign({}, r, { otro: r.de })); }
    });
    (d.edades || []).forEach(e => { if (e && e.persona) add(edades, e.persona, e); });
    // Índices por versículo: quién aparece (refs, primera_ref, ref_mencion, menciones) y primera aparición.
    const menciones = new Map(), porRef = new Map(), primera = new Map();
    const marcar = (id, ref) => {
      const k = clave(ref); if (k === null || !id) return;
      if (!porRef.has(k)) porRef.set(k, new Set());
      porRef.get(k).add(id);
      if (!primera.has(id) || k < primera.get(id)) primera.set(id, k);
    };
    (d.personas || []).forEach(p => { if (p && p.id) [].concat(p.refs || [], p.primera_ref || [], p.ref_mencion || []).forEach(r => marcar(p.id, r)); });
    (d.menciones || []).forEach(m => {
      const k = m && m.persona ? clave(m.ref) : null; if (k === null) return;
      add(menciones, k, m); marcar(m.persona, m.ref);
    });
    return { datos: d, personas, hijos, padres, conyuges, edades, menciones, porRef, primera };
  }

  const cache = new WeakMap();
  function indice(d) {
    if (d && typeof d === 'object') { if (!cache.has(d)) cache.set(d, indexar(d)); return cache.get(d); }
    return indexar(d);
  }
  const persona = (d, id) => indice(d).personas.get(id) || null;

  function hijosDe(d, id) {
    const vistos = new Set();
    return (indice(d).hijos.get(id) || []).filter(r => !vistos.has(r.a) && vistos.add(r.a));
  }

  function encontrar(d, candidatos) {
    const I = indice(d);
    for (const c of candidatos) if (I.personas.has(c)) return c;
    for (const c of candidatos) { const n = norm(c); for (const p of I.personas.values()) if (norm(p.nombre) === n) return p.id; }
    return null;
  }
  const idAdan = d => encontrar(d, ['Adam_1', 'Adán', 'Adam']);
  const idAbraham = d => encontrar(d, ['Abraham_1', 'Abram_1', 'Abraham', 'Abram']);

  // Árbol: {id, vinculos:[relaciones progenitor→este], hijos:[nodos]}; cada persona aparece una vez.
  function construirArbol(d, raiz, visit) {
    visit = visit || new Set();
    if (!raiz || visit.has(raiz)) return null;
    visit.add(raiz);
    const I = indice(d);
    const rec = (id, vinculos, padreId) => {
      const n = { id, vinculos, hijos: [],
        conyuges: (I.conyuges.get(id) || []).filter((r, i, a) => a.findIndex(x => x.otro === r.otro) === i),
        madres: (I.padres.get(id) || []).filter(x => x.tipo === 'madre' && x.de !== padreId) };
      const hs = hijosDe(d, id).slice().sort((a, b) => (sinNombre(d, a.a) ? 1 : 0) - (sinNombre(d, b.a) ? 1 : 0));
      for (const r of hs) {
        if (visit.has(r.a)) continue;
        visit.add(r.a);
        n.hijos.push(rec(r.a, (I.padres.get(r.a) || []).filter(x => x.de === id), id));
      }
      return n;
    };
    return rec(raiz, [], null);
  }
  const sinNombre = (d, id) => { const p = persona(d, id); return !!(p && p.sin_nombre); };

  // Ids visibles en el árbol: como nodo, como cónyuge de un nodo o como madre de un nodo.
  function alcanzables(d, bosque) {
    const s = new Set();
    (bosque || construirBosque(d)).forEach(function r(n) {
      s.add(n.id); n.conyuges.forEach(c => s.add(c.otro)); n.madres.forEach(m => s.add(m.de)); n.hijos.forEach(r);
    });
    return s;
  }

  function contarMujeres(d) {
    const out = { conNombre: 0, sinNombre: 0 };
    for (const p of indice(d).personas.values()) if (p.sexo === 'f') p.sin_nombre ? out.sinNombre++ : out.conNombre++;
    return out;
  }

  // Bosque: Adán primero, luego otras raíces (sin padres conocidos) no alcanzadas.
  function construirBosque(d) {
    const I = indice(d), visit = new Set(), raices = [];
    const a = idAdan(d);
    if (a) raices.push(construirArbol(d, a, visit));
    const cands = [...I.personas.values()].filter(p => !(I.padres.get(p.id) || []).length && hijosDe(d, p.id).length);
    // Primero quienes no son madres ni cónyuges, para que las madres/esposas queden como etiqueta y no como raíz.
    const esMadre = id => hijosDe(d, id).every(r => r.tipo === 'madre');
    cands.sort((x, y) => ((I.conyuges.has(x.id) || esMadre(x.id)) ? 1 : 0) - ((I.conyuges.has(y.id) || esMadre(y.id)) ? 1 : 0));
    for (const p of cands) {
      if (visit.has(p.id)) continue;
      if (hijosDe(d, p.id).every(h => visit.has(h.a))) continue;
      const t = construirArbol(d, p.id, visit);
      if (t) raices.push(t);
    }
    return raices.filter(Boolean);
  }

  function rutas(d, desde, hasta, limite) {
    limite = limite || 500;
    const out = [];
    if (!desde || !hasta) return out;
    const camino = [desde], vis = new Set([desde]);
    (function dfs(id) {
      if (out.length >= limite) return;
      if (id === hasta) { out.push(camino.slice()); return; }
      for (const r of hijosDe(d, id)) {
        if (vis.has(r.a)) continue;
        vis.add(r.a); camino.push(r.a);
        dfs(r.a);
        camino.pop(); vis.delete(r.a);
      }
    })(desde);
    return out;
  }

  function tradicionesDe(d, id) {
    const p = persona(d, id);
    if (p && Array.isArray(p.tradiciones) && p.tradiciones.length) return new Set(p.tradiciones);
    return new Set((indice(d).edades.get(id) || []).map(e => e.tradicion).filter(Boolean));
  }
  const presenteEn = (d, id, trad) => { const t = tradicionesDe(d, id); return t.size === 0 || t.has(trad); };
  const tieneEdadEn = (d, id, trad) => (indice(d).edades.get(id) || []).some(e => e.tradicion === trad);

  // Línea Adán→Abraham propia de una tradición: excluye personas que solo existen en la otra
  // y prefiere la ruta con más personas con edades en esa tradición (luego la más corta).
  function lineaPorTradicion(d, trad, desde, hasta) {
    desde = desde || idAdan(d); hasta = hasta || idAbraham(d);
    const todas = rutas(d, desde, hasta);
    if (!todas.length) return [];
    const validas = todas.filter(r => r.every((id, i) => i === 0 || i === r.length - 1 || presenteEn(d, id, trad)));
    const cand = validas.length ? validas : todas;
    const pts = r => r.filter(id => tieneEdadEn(d, id, trad)).length;
    cand.sort((a, b) => pts(b) - pts(a) || a.length - b.length);
    return cand[0];
  }

  function fusionarOrden(a, b) {
    const res = (a || []).slice();
    (b || []).forEach((x, i) => {
      if (res.includes(x)) return;
      const k = i > 0 ? res.indexOf(b[i - 1]) : -1;
      if (k >= 0) res.splice(k + 1, 0, x); else if (i === 0) res.unshift(x); else res.push(x);
    });
    return res;
  }

  const lineaAdanAbraham = d => fusionarOrden(lineaPorTradicion(d, 'LXX'), lineaPorTradicion(d, 'TM'));

  // Edad de una persona; si falta el total (o restantes) y se puede deducir, se marca derivado/cálculo.
  function edad(d, id, tipo, trad) {
    const lista = (indice(d).edades.get(id) || []).filter(e => e.tradicion === trad && num(e.valor) !== null);
    const e = lista.find(x => x.tipo === tipo);
    if (e) return Object.assign({}, e, { valor: num(e.valor), derivado: false });
    const g = lista.find(x => x.tipo === 'al_engendrar'), r = lista.find(x => x.tipo === 'restantes'), t = lista.find(x => x.tipo === 'total');
    const base = { persona: id, tipo, tradicion: trad, certeza: 'calculo', derivado: true };
    if (tipo === 'total' && g && r) return Object.assign(base, { valor: num(g.valor) + num(r.valor), de: [g, r], ref: g.ref });
    if (tipo === 'restantes' && g && t) return Object.assign(base, { valor: num(t.valor) - num(g.valor), de: [t, g], ref: t.ref });
    return null;
  }

  // Por tipo: 'igual' | 'difiere' | 'solo_TM' | 'solo_LXX' | null (sin dato).
  function diferencias(d, id) {
    const out = {};
    for (const tipo of TIPOS) {
      const a = edad(d, id, tipo, 'TM'), b = edad(d, id, tipo, 'LXX');
      out[tipo] = a && b ? (a.valor === b.valor ? 'igual' : 'difiere') : a ? 'solo_TM' : b ? 'solo_LXX' : null;
    }
    return out;
  }

  // Años desde Adán encadenando edades al engendrar (CÁLCULO). Si falta un eslabón, lo que sigue queda null.
  function anosDesdeAdan(d, trad, ruta) {
    ruta = ruta || lineaPorTradicion(d, trad);
    let nac = 0;
    const pasos = [];
    return ruta.map(id => {
      const tot = edad(d, id, 'total', trad);
      const fila = { id, nacimiento: nac, muerte: nac !== null && tot ? nac + tot.valor : null, total: tot, pasos: pasos.slice() };
      const g = edad(d, id, 'al_engendrar', trad);
      if (nac !== null && g) { nac += g.valor; pasos.push({ id, valor: g.valor, ref: g.ref || '' }); } else nac = null;
      return fila;
    });
  }

  function ordenPatriarcas(d) {
    const I = indice(d);
    const con = id => (I.edades.get(id) || []).length > 0;
    const orden = lineaAdanAbraham(d).filter(con);
    for (const id of I.edades.keys()) if (!orden.includes(id) && I.personas.has(id)) orden.push(id);
    return orden;
  }

  function personasEnCapitulo(d, cap) {
    const out = [];
    for (const p of indice(d).personas.values()) {
      const refs = [...new Set([].concat(p.refs || [], p.primera_ref ? [p.primera_ref] : []))];
      const vs = refs.map(parseRef).filter(r => r && r.cap === cap).map(r => r.v || 0);
      if (vs.length) out.push({ id: p.id, persona: p, versos: [...new Set(vs)].sort((a, b) => a - b) });
    }
    return out.sort((a, b) => a.versos[0] - b.versos[0]);
  }

  function buscar(d, q, max) {
    const n = norm(q);
    if (!n) return [];
    const res = [];
    for (const p of indice(d).personas.values()) {
      const nom = norm(p.nombre), id = norm(p.id);
      if (nom.includes(n) || id.includes(n)) res.push({ p, rango: nom.startsWith(n) ? 0 : 1 });
    }
    return res.sort((a, b) => a.rango - b.rango || norm(a.p.nombre).localeCompare(norm(b.p.nombre))).slice(0, max || 20).map(x => x.p);
  }

  /* ---- Lectura acompañada ---- */
  // Pasajes de los datos; si no hay, uno por capítulo.
  function pasajes(d) {
    d = d || {};
    if (Array.isArray(d.pasajes) && d.pasajes.length) return d.pasajes.filter(p => p && p.id && clave(p.inicio) && clave(p.fin));
    return (d.capitulos || []).map(c => {
      const vs = c.versiculos || [];
      return { id: 'cap-' + c.cap, inicio: refTxt(c.cap, vs.length ? vs[0].n : 1), fin: refTxt(c.cap, vs.length ? vs[vs.length - 1].n : 1),
        titulo: `${c.libro || 'Génesis'} ${c.cap}`, titulo_origen: 'capitulo', resumen: '' };
    });
  }
  function pasajeDe(d, ref) {
    const k = clave(ref);
    if (k === null) return null;
    return pasajes(d).find(p => clave(p.inicio) <= k && k <= clave(p.fin)) || null;
  }
  function versiculosDe(d, pasaje) {
    const out = [];
    if (!pasaje) return out;
    const a = clave(pasaje.inicio), b = clave(pasaje.fin);
    for (const c of ((d && d.capitulos) || [])) for (const v of (c.versiculos || [])) {
      const k = c.cap * 1000 + v.n;
      if (k >= a && k <= b) out.push({ cap: c.cap, n: v.n, texto: v.texto || '', ref: refTxt(c.cap, v.n), clave: k });
    }
    return out.sort((x, y) => x.clave - y.clave);
  }

  // Si no hay `menciones`, se buscan los nombres de las personas con ese versículo en sus refs.
  function mencionesPorNombre(d, ref, texto) {
    const I = indice(d), out = [];
    for (const id of (I.porRef.get(clave(ref)) || [])) {
      const p = I.personas.get(id);
      if (!p || p.sin_nombre) continue;
      for (const nom of new Set([p.nombre, p.nombre_rv1909].filter(Boolean))) {
        const re = new RegExp('(^|[^\\p{L}])(' + nom.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')(?![\\p{L}])', 'gu');
        let m;
        while ((m = re.exec(texto))) { const i = m.index + m[1].length; out.push({ persona: id, inicio: i, fin: i + m[2].length }); }
      }
    }
    return out;
  }
  // Trozos [{texto, persona?}] de un versículo; ignora menciones fuera de rango o solapadas.
  function segmentar(d, ref, texto) {
    texto = String(texto || '');
    let ms = (indice(d).menciones.get(clave(ref)) || []).filter(m => Number.isInteger(m.inicio) && Number.isInteger(m.fin) && m.inicio >= 0 && m.fin > m.inicio && m.fin <= texto.length);
    if (!ms.length) ms = mencionesPorNombre(d, ref, texto);
    ms = ms.slice().sort((a, b) => a.inicio - b.inicio || b.fin - a.fin);
    const out = [];
    let pos = 0;
    for (const m of ms) {
      if (m.inicio < pos) continue;
      if (m.inicio > pos) out.push({ texto: texto.slice(pos, m.inicio) });
      out.push({ texto: texto.slice(m.inicio, m.fin), persona: m.persona });
      pos = m.fin;
    }
    if (pos < texto.length) out.push({ texto: texto.slice(pos) });
    return out;
  }

  const unir = xs => xs.length < 2 ? (xs[0] || '') : xs.slice(0, -1).join(', ') + ' y ' + xs[xs.length - 1];
  const unicos = xs => xs.filter((x, i) => xs.indexOf(x) === i);
  // "hijo de Adán y Eva; esposo de …", calculado de las relaciones.
  function contextoPersona(d, id) {
    const I = indice(d), p = I.personas.get(id);
    if (!p) return '';
    const nom = x => (I.personas.get(x) || {}).nombre || x;
    const partes = [];
    const pad = unicos((I.padres.get(id) || []).map(r => r.de));
    if (pad.length) partes.push(`${p.sexo === 'f' ? 'hija' : p.sexo === 'm' ? 'hijo' : p.sin_nombre ? 'descendencia' : 'hijo o hija'} de ${unir(pad.map(nom))}`);
    const cs = unicos((I.conyuges.get(id) || []).map(r => r.otro));
    if (cs.length) partes.push(`${p.sexo === 'f' ? 'esposa' : p.sexo === 'm' ? 'esposo' : 'cónyuge'} de ${unir(cs.map(nom))}`);
    return partes.join('; ');
  }

  // Contenido del acompañante para uno o varios versículos.
  function acompanante(d, refs) {
    d = d || {};
    const I = indice(d), ks = new Set([].concat(refs || []).map(clave).filter(k => k !== null));
    const enSet = r => ks.has(clave(r));
    const ids = [];
    [...ks].sort((a, b) => a - b).forEach(k => (I.porRef.get(k) || []).forEach(id => { if (!ids.includes(id)) ids.push(id); }));
    const vistos = new Set();
    const vinculos = (d.relaciones || []).filter(r => r && r.de && r.a && enSet(r.ref)).filter(r => {
      const k = r.tipo + '|' + (r.tipo === 'conyuge' ? [r.de, r.a].sort().join('+') : r.de + '>' + r.a);
      return !vistos.has(k) && vistos.add(k);
    });
    const grupos = new Map();
    (d.edades || []).filter(e => e && e.persona && enSet(e.ref) && num(e.valor) !== null).forEach(e => {
      const k = e.persona + '|' + e.tipo;
      if (!grupos.has(k)) grupos.set(k, { persona: e.persona, tipo: e.tipo, ref: e.ref, TM: null, LXX: null });
      if (e.tradicion === 'TM' || e.tradicion === 'LXX') grupos.get(k)[e.tradicion] = Object.assign({}, e, { valor: num(e.valor) });
    });
    const edadesV = [...grupos.values()].map(g => Object.assign(g, {
      difiere: !!(g.TM && g.LXX && g.TM.valor !== g.LXX.valor), solo: g.TM && !g.LXX ? 'TM' : !g.TM && g.LXX ? 'LXX' : null }));
    return { personas: ids.map(id => ({ id, contexto: contextoPersona(d, id) })), vinculos, edades: edadesV,
      sinNombre: ids.filter(id => (I.personas.get(id) || {}).sin_nombre) };
  }
  // ¿Tiene el versículo vínculos, edades o alusiones sin nombre? (marca al margen)
  const tieneApoyo = (d, ref) => { const A = acompanante(d, [ref]); return A.vinculos.length + A.edades.length + A.sinNombre.length > 0; };

  // Personas cuya primera aparición en los datos cae dentro del pasaje.
  function primerasApariciones(d, pasaje) {
    if (!pasaje) return [];
    const a = clave(pasaje.inicio), b = clave(pasaje.fin);
    return [...indice(d).primera.entries()].filter(([, k]) => k >= a && k <= b).sort((x, y) => x[1] - y[1]).map(([id]) => id);
  }
  function miniArbol(d, id) {
    const I = indice(d);
    return { id, padres: unicos((I.padres.get(id) || []).map(r => r.de)), conyuges: unicos((I.conyuges.get(id) || []).map(r => r.otro)), hijos: hijosDe(d, id).map(r => r.a) };
  }
  // Año del diluvio desde Adán (CÁLCULO): nacimiento de quien tiene edad con ref Gn 7:6 + esa edad.
  function anoDiluvio(d, trad) {
    const filas = anosDesdeAdan(d, trad);
    for (const e of ((d && d.edades) || [])) {
      if (!e || clave(e.ref) !== 7006 || (e.tradicion && e.tradicion !== trad) || num(e.valor) === null) continue;
      const f = filas.find(x => x.id === e.persona);
      if (f && f.nacimiento !== null) return { ano: f.nacimiento + num(e.valor), persona: e.persona, valor: num(e.valor), ref: e.ref, cita: e.cita || '' };
    }
    return null;
  }

  return { TRADS, TIPOS, norm, parseRef, clave, claseCerteza, pasajes, pasajeDe, versiculosDe, segmentar, contextoPersona,
    acompanante, tieneApoyo, primerasApariciones, miniArbol, anoDiluvio, indice, persona, hijosDe, encontrar, idAdan, idAbraham,
    construirArbol, construirBosque, alcanzables, contarMujeres, sinNombre, rutas, tradicionesDe, presenteEn, lineaPorTradicion, fusionarOrden,
    lineaAdanAbraham, edad, diferencias, anosDesdeAdan, ordenPatriarcas, personasEnCapitulo, buscar };
})();

globalThis.BibliaNucleo = Nucleo;

/* ======================= Interfaz ======================= */
if (typeof document !== 'undefined') (function () {
  const N = Nucleo;
  let D = window.BIBLIA_DATOS || null;
  const $ = s => document.querySelector(s);
  const main = $('#principal');
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const store = {
    get(k, def) { try { const v = localStorage.getItem(k); return v == null ? def : JSON.parse(v); } catch (e) { return def; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* sin almacenamiento */ } }
  };
  const TIPO_TXT = { al_engendrar: 'Al engendrar', restantes: 'Años restantes', total: 'Total' };
  const CERT_TXT = { texto: 'Texto', inferido: 'Inferido', calculo: 'Cálculo' };
  const CERT_DESC = { texto: 'Lo dice el texto', inferido: 'Supuesto: no lo dice el texto de forma explícita', calculo: 'Cálculo hecho a partir del texto' };
  const estado = { trad: store.get('biblia.trad', 'TM'), lineaSolo: false, mujeres: false, hoja: false, pasaje: null, activo: null, foco: null, plegados: new Set(), q: '' };

  const nombre = id => { const p = N.persona(D, id); return p ? (p.nombre || id) : id; };
  const refHTML = ref => { const r = N.parseRef(ref); return r ? `<a class="ref" href="#leer/${r.cap}${r.v ? '/' + r.v : ''}">${esc(ref)}</a>` : esc(ref); };
  const insignia = (cert, ref) => { const k = N.claseCerteza(cert); return `<span class="insignia ${k}" title="${CERT_DESC[k]}">${CERT_TXT[k]}${ref ? ' · ' + refHTML(ref) : ''}</span>`; };
  const btnPersona = id => {
    const p = N.persona(D, id) || {};
    const cls = (p.sexo === 'f' ? ' mujer' : p.sexo === 'm' ? ' hombre' : ' indef') + (p.sin_nombre ? ' sin-nombre' : '');
    return `<button type="button" class="persona-btn${cls}" data-persona="${esc(id)}">${esc(nombre(id))}${p.sin_nombre ? '<span class="marca-sn">sin nombre en el texto</span>' : ''}</button>`;
  };
  const citaHTML = r => r && r.cita ? `<blockquote>${esc(r.cita)}</blockquote>` : '';
  const fuenteNombre = id => { const f = (D.fuentes || []).find(x => x.id === id); return f ? f.nombre : (id || 'sin fuente'); };
  const etiquetaTrad = id => { const t = [...N.tradicionesDe(D, id)]; return t.length === 1 ? `<span class="etiqueta">solo ${esc(t[0])}</span>` : ''; };
  const pasajesLeidos = () => new Set(store.get('biblia.pasajesLeidos', []));
  const rango = p => { const a = N.parseRef(p.inicio), b = N.parseRef(p.fin); return a.cap === b.cap ? `Gn ${a.cap}:${a.v}–${b.v}` : `Gn ${a.cap}:${a.v}–${b.cap}:${b.v}`; };
  const ESTADO_TXT = { leido: 'Leído', 'en-curso': 'En curso', pendiente: 'Pendiente' };
  const ICONO = {
    leido: '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 10.5l4 4 8-9"/></svg>',
    'en-curso': '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 4v12l10-6z"/></svg>',
    pendiente: '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="5"/></svg>'
  };

  /* ---------- Leer: inicio ---------- */
  function vistaLeer(args) {
    const ps = N.pasajes(D);
    if (args[0] === 'p') return vistaPasaje(ps.find(x => x.id === args[1]), args[2] || null);
    if (args[0]) {
      const cap = +args[0], v = +args[1] || null;
      const p = N.pasajeDe(D, `Gn ${cap}:${v || 1}`) || ps.find(x => N.parseRef(x.inicio).cap === cap);
      return vistaPasaje(p, v ? `${cap}:${v}` : null);
    }
    const L = pasajesLeidos(), pos = store.get('biblia.pos', null);
    const actual = pos && ps.find(x => x.id === pos.pasaje);
    const n = ps.filter(p => L.has(p.id)).length;
    const sig = (actual && !L.has(actual.id) ? actual : null) || ps.find(p => !L.has(p.id)) || actual || ps[0];
    const enSig = actual && sig && actual.id === sig.id && pos.v;
    const editorial = ps.some(p => p.titulo_origen === 'editorial');
    return `<section class="portada" aria-labelledby="t-portada">
        <h1 id="t-portada" tabindex="-1">${pos ? 'Continúa donde lo dejaste' : 'Empieza a leer'}</h1>
        ${sig ? `<a class="continuar" href="#leer/p/${esc(sig.id)}${enSig ? '/' + esc(pos.v) : ''}">
          <span class="continuar-rango">${rango(sig)}${enSig ? `, versículo ${esc(pos.v.split(':')[1])}` : ''}</span>
          <span class="continuar-titulo">${esc(sig.titulo)}</span>
          ${sig.resumen ? `<span class="continuar-resumen">${esc(sig.resumen)}</span>` : ''}
          <span class="continuar-accion">${pos ? 'Seguir leyendo' : 'Abrir el primer pasaje'}</span></a>` : '<p>No hay texto en los datos.</p>'}
        <div class="progreso"><progress max="${ps.length || 1}" value="${n}" aria-label="Progreso de lectura"></progress><span>${n} de ${ps.length} pasajes leídos</span></div>
      </section>
      <h2 class="titulo-seccion">Plan de lectura</h2>
      <ol class="pasajes">${ps.map((p, i) => {
        const est = L.has(p.id) ? 'leido' : actual && actual.id === p.id ? 'en-curso' : 'pendiente';
        return `<li class="pasaje ${est}"><a href="#leer/p/${esc(p.id)}"><span class="pasaje-num" aria-hidden="true">${i + 1}</span>
          <span class="pasaje-cuerpo"><span class="pasaje-titulo">${esc(p.titulo)}</span><span class="pasaje-rango">${rango(p)}</span>
          ${p.resumen ? `<span class="pasaje-resumen">${esc(p.resumen)}</span>` : ''}</span>
          <span class="estado ${est}">${ICONO[est]}${ESTADO_TXT[est]}</span></a></li>`;
      }).join('')}</ol>
      ${editorial ? '<p class="meta">Los títulos y resúmenes de los pasajes son editoriales: no forman parte del texto bíblico.</p>' : ''}`;
  }

  /* ---------- Leer: pasaje con acompañante ---------- */
  function vistaPasaje(p, activo) {
    if (!p) return `<h1 tabindex="-1">Pasaje no encontrado</h1><p class="vacio-txt">Ese pasaje no está en este piloto, que cubre Génesis 1–11.</p><p><a class="boton" href="#leer">Ver el plan de lectura</a></p>`;
    const ps = N.pasajes(D), i = ps.findIndex(x => x.id === p.id), prev = ps[i - 1], next = ps[i + 1];
    const vs = N.versiculosDe(D, p);
    estado.pasaje = p;
    estado.activo = activo && vs.some(v => `${v.cap}:${v.n}` === activo) ? activo : null;
    store.set('biblia.pos', { pasaje: p.id, v: estado.activo });
    const fuente = ((D.fuentes || []).find(f => /rv/i.test(f.id)) || {}).id;
    let capPrev = null;
    const texto = vs.map((v, j) => {
      const k = `${v.cap}:${v.n}`, ap = N.tieneApoyo(D, v.ref);
      const cab = v.cap !== capPrev && j ? `<span class="cap-marca">Capítulo ${v.cap}</span>` : '';
      capPrev = v.cap;
      const segs = N.segmentar(D, v.ref, v.texto);
      const partes = segs.map((s, si) => {
        if (s.persona) { const per = N.persona(D, s.persona) || {}; return `<button type="button" class="mencion${per.sexo === 'f' ? ' mujer' : ''}" data-persona="${esc(s.persona)}">${esc(s.texto)}</button>`; }
        if (j === 0 && si === 0 && s.texto) { const t = s.texto.trimStart(), c = Array.from(t)[0] || ''; return `<span class="capitular" aria-hidden="true">${esc(c)}</span><span class="sr">${esc(c)}</span>${esc(t.slice(c.length))}`; }
        return esc(s.texto);
      }).join('');
      return `${cab}<span class="vers${ap ? ' con-apoyo' : ''}${k === estado.activo ? ' activo' : ''}" id="v${v.cap}-${v.n}" data-v="${k}"><button type="button" class="vn" data-activar="${k}" aria-pressed="${k === estado.activo}" aria-label="Versículo ${v.n}${ap ? ', con datos en el acompañante' : ''}">${v.n}</button>${partes} </span>`;
    }).join('');
    const nuevos = N.primerasApariciones(D, p);
    return `<div class="pasaje-vista"><article class="lectura">
      <header class="cab-pasaje"><a class="volver" href="#leer"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M12 4l-6 6 6 6"/></svg>Plan de lectura</a>
        <p class="pasaje-rango">${rango(p)} · pasaje ${i + 1} de ${ps.length}</p>
        <h1 tabindex="-1">${esc(p.titulo)}</h1>
        ${p.titulo_origen === 'editorial' ? '<p class="meta">Título editorial, no del texto bíblico.</p>' : ''}</header>
      <div class="biblia">${texto || '<p class="vacio-txt">Este pasaje no tiene versículos en los datos.</p>'}</div>
      <p class="pista-lectura meta"><span class="marca-apoyo" aria-hidden="true"></span>Pulsa el número de un versículo para ver sus datos. La marca al margen indica vínculos, edades o personas sin nombre.</p>
      ${fuente ? `<p class="meta">Texto: ${esc(fuenteNombre(fuente))}</p>` : ''}
      <section class="nuevo" aria-labelledby="t-nuevo"><h2 id="t-nuevo">Lo nuevo en este pasaje</h2>
        ${nuevos.length ? `<p class="meta">Personas que aparecen por primera vez:</p><ul class="chips">${nuevos.map(id => `<li>${btnPersona(id)}</li>`).join('')}</ul>` : '<p class="vacio-txt">Nadie aparece aquí por primera vez.</p>'}</section>
      <nav class="pasos-pasaje" aria-label="Pasajes">
        ${prev ? `<a class="boton secundario" href="#leer/p/${esc(prev.id)}" title="${esc(prev.titulo)}">Anterior</a>` : '<span></span>'}
        <button type="button" class="boton" data-leido-seguir="${esc(p.id)}">${next ? 'Marcar como leído y seguir' : 'Marcar como leído'}</button>
        ${next ? `<a class="boton secundario" href="#leer/p/${esc(next.id)}" title="${esc(next.titulo)}">Siguiente</a>` : '<span></span>'}
      </nav></article>
      <aside class="acompanante${estado.hoja ? ' abierta' : ''}" id="acompanante" aria-label="Acompañante de lectura">${acompHTML()}</aside></div>`;
  }

  const TIPO_REL = r => r.tipo === 'conyuge' ? `${esc(nombre(r.de))} y ${esc(nombre(r.a))}: cónyuges`
    : `${esc(nombre(r.de))} es ${r.tipo === 'madre' ? 'madre' : 'padre'} de ${esc(nombre(r.a))}`;
  function acompHTML() {
    const p = estado.pasaje;
    if (!p) return '';
    const refs = estado.activo ? [`Gn ${estado.activo}`] : N.versiculosDe(D, p).map(v => v.ref);
    const A = N.acompanante(D, refs);
    const n = A.vinculos.length + A.edades.length + A.sinNombre.length;
    const ambito = estado.activo ? `Gn ${estado.activo}` : 'Todo el pasaje';
    const sec = (t, cuerpo, icono) => `<section class="acomp-sec"><h3>${icono}${t}</h3>${cuerpo}</section>`;
    const I = (d) => `<svg viewBox="0 0 20 20" aria-hidden="true"><path d="${d}"/></svg>`;
    let html = '';
    if (A.personas.length) html += sec('Quién aparece', `<ul class="quien">${A.personas.map(x => `<li>${btnPersona(x.id)}${x.contexto ? `<span class="contexto">${esc(x.contexto)}</span>` : ''}</li>`).join('')}</ul>`, I('M10 9a3 3 0 100-6 3 3 0 000 6zM4 17c0-3.3 2.7-5 6-5s6 1.7 6 5'));
    if (A.vinculos.length) html += sec('Vínculos que establece', `<ul class="vinculos">${A.vinculos.map(r => `<li><span>${TIPO_REL(r)}</span>${insignia(r.certeza, r.ref)}${citaHTML(r)}</li>`).join('')}</ul>`, I('M7 7a3 3 0 014 0l2 2a3 3 0 010 4M13 13a3 3 0 01-4 0l-2-2a3 3 0 010-4'));
    if (A.edades.length) html += sec('Edades', `<ul class="edades-acomp">${A.edades.map(e => {
      const val = tr => { const x = e[tr]; if (!x) return `<span class="vacio">${tr}: sin dato</span>`; const lbl = `<span class="trad">${tr}</span><strong>${x.valor}</strong>`; return N.TIPOS.includes(e.tipo) ? `<button type="button" class="celda-acomp" data-edad="${esc(e.persona)}|${e.tipo}|${tr}">${lbl}</button>` : `<span class="celda-acomp">${lbl}</span>`; };
      return `<li${e.difiere || e.solo ? ' class="difiere"' : ''}><span class="edad-quien">${esc(nombre(e.persona))}, ${esc(TIPO_TXT[e.tipo] || e.tipo.replace(/_/g, ' '))}</span><span class="par">${val('TM')}${val('LXX')}</span>
        ${e.difiere ? `<p class="difiere-txt">En la Septuaginta: ${e.LXX.valor}${e.LXX.ref && e.LXX.ref !== e.TM.ref ? ' (' + refHTML(e.LXX.ref) + ')' : ''}</p>` : e.solo ? `<p class="difiere-txt">Solo ${e.solo} da este dato.</p>` : ''}</li>`;
    }).join('')}</ul>`, I('M10 3a7 7 0 100 14 7 7 0 000-14zM10 6v4l3 2'));
    if (A.sinNombre.length) html += sec('Sin nombre', A.sinNombre.map(id => `<p class="sin-nombre-aviso">El texto alude a alguien sin dar su nombre: ${btnPersona(id)}</p>`).join(''), I('M10 3a7 7 0 100 14 7 7 0 000-14zM10 6.5v4M10 13.5v.5'));
    const centrales = A.personas.map(x => x.id).filter(id => { const m = N.miniArbol(D, id); return !(N.persona(D, id) || {}).sin_nombre && (m.padres.length || m.hijos.length); }).slice(0, estado.activo ? 2 : 3);
    if (centrales.length) html += sec('Dónde va en el árbol', centrales.map(id => {
      const m = N.miniArbol(D, id), mas = m.hijos.length - 5;
      return `<div class="mini"><div class="mini-gen">${m.padres.map(btnPersona).join('') || '<span class="meta">Padres no constan</span>'}</div>
        <div class="mini-gen centro">${btnPersona(id)}${m.conyuges.map(c => `<span class="cony-mini">⚭</span>${btnPersona(c)}`).join('')}</div>
        <div class="mini-gen">${m.hijos.slice(0, 5).map(btnPersona).join('') || '<span class="meta">Sin hijos registrados</span>'}${mas > 0 ? `<span class="meta">y ${mas} más</span>` : ''}</div>
        <a class="enlace-arbol" href="#arbol/${encodeURIComponent(id)}">Ver a ${esc(nombre(id))} en el árbol completo</a></div>`;
    }).join(''), I('M10 3v5M10 8H5v4M10 8h5v4M10 8v9'));
    if (!html) html = `<p class="vacio-txt">${estado.activo ? 'Este versículo no tiene personas, vínculos ni edades en los datos. Pulsa otro número o vuelve a todo el pasaje.' : 'Este pasaje no tiene personas, vínculos ni edades en los datos.'}</p>`;
    return `<div class="acomp-cab">
        <button type="button" class="acomp-asa" data-hoja aria-expanded="${!!estado.hoja}" aria-controls="acomp-cuerpo">
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 4h12v9H8l-4 3z"/></svg>
          <span class="acomp-titulo">Acompañante</span><span class="acomp-ambito">${esc(ambito)}${n ? ` · ${n} ${n === 1 ? 'dato' : 'datos'}` : ''}</span></button>
        ${estado.activo ? '<button type="button" class="boton mini-boton secundario" data-activar="">Todo el pasaje</button>' : ''}</div>
      <div class="acomp-cuerpo" id="acomp-cuerpo">${html}</div>`;
  }
  function activar(k) {
    estado.activo = k && k !== estado.activo ? k : null;
    document.querySelectorAll('.vers').forEach(el => { const on = el.dataset.v === estado.activo; el.classList.toggle('activo', on); el.querySelector('.vn').setAttribute('aria-pressed', on); });
    const a = $('#acompanante'); if (a) a.innerHTML = acompHTML();
    store.set('biblia.pos', { pasaje: estado.pasaje.id, v: estado.activo });
    try { history.replaceState(null, '', `#leer/p/${estado.pasaje.id}${estado.activo ? '/' + estado.activo : ''}`); } catch (e) { /* file:// */ }
  }

  /* ---------- Árbol ---------- */
  function vistaArbol(args) {
    estado.foco = args && args[0] ? args[0] : null;
    if (estado.foco) { estado.lineaSolo = false; estado.plegados.clear(); }
    return `<h1 tabindex="-1">Árbol genealógico</h1>
      <p class="sub">Cada vínculo indica si <span class="insignia texto">Texto</span> lo dice explícitamente o es <span class="insignia inferido">Inferido</span>, con su versículo.</p>
      <p class="leyenda-arbol meta"><span class="ley hombre">Hombre</span><span class="ley mujer">Mujer</span><span class="ley sin-nombre">Sin nombre en el texto</span><span class="ley linea">Línea de Adán a Abraham</span></p>
      <div class="herr">
        <div class="campo"><label for="buscar">Buscar persona</label><input id="buscar" type="search" autocomplete="off" placeholder="Nombre…" value="${esc(estado.q)}"></div>
        <button type="button" class="boton" id="btn-linea" aria-pressed="${estado.lineaSolo}">${estado.lineaSolo ? 'Mostrar todo el árbol' : 'Línea de Adán a Abraham'}</button>
        ${estado.lineaSolo ? '' : '<button type="button" class="boton secundario" id="btn-plegar">Plegar todo</button><button type="button" class="boton secundario" id="btn-desplegar">Desplegar todo</button>'}
      </div>
      <ul class="resultados" id="resultados" aria-live="polite">${resultadosHTML()}</ul>
      ${(m => `<p><button type="button" class="boton secundario" id="btn-mujeres" aria-pressed="${estado.mujeres}">Mujeres: ${m.conNombre} con nombre, ${m.sinNombre} sin nombre</button></p>`)(N.contarMujeres(D))}
      <div id="arbol"${estado.mujeres ? ' class="resaltar-mujeres"' : ''}>${arbolHTML()}</div>`;
  }
  function resultadosHTML() {
    if (!estado.q) return '';
    const r = N.buscar(D, estado.q, 20);
    return r.length ? r.map(p => `<li>${btnPersona(p.id)}${p.primera_ref ? ' <span class="meta">' + esc(p.primera_ref) + '</span>' : ''}</li>`).join('') : '<li class="meta">Sin resultados.</li>';
  }
  function arbolHTML() {
    const bosque = N.construirBosque(D);
    if (!bosque.length) return '<p>No hay relaciones en los datos.</p>';
    const linea = new Set(N.lineaAdanAbraham(D));
    const filtro = estado.lineaSolo ? linea : null;
    const filas = [];
    const rec = (n, prof) => {
      if (filtro && !filtro.has(n.id)) return;
      const hijos = filtro ? n.hijos.filter(h => filtro.has(h.id)) : n.hijos;
      const pleg = !filtro && estado.plegados.has(n.id);
      filas.push(`<li class="fila${linea.has(n.id) ? ' en-linea' : ''}${estado.foco === n.id ? ' foco' : ''}" data-fila="${esc(n.id)}" style="--n:${Math.min(prof, 14)}">
        <span class="gen" title="Generación ${prof + 1}">${prof + 1}</span>
        ${hijos.length ? `<button type="button" class="plegar" data-plegar="${esc(n.id)}" aria-expanded="${!pleg}" aria-label="${pleg ? 'Desplegar' : 'Plegar'} descendencia de ${esc(nombre(n.id))}">${pleg ? '▸' : '▾'}</button>` : '<span class="plegar vacio" aria-hidden="true"></span>'}
        <span class="fila-cont">${btnPersona(n.id)}${etiquetaTrad(n.id)}${n.vinculos.map(r => insignia(r.certeza, r.ref)).join('')}${pleg ? `<span class="meta">(${hijos.length} hijos)</span>` : ''}
        ${n.madres.map(r => `<span class="sublinea madre">madre: ${btnPersona(r.de)}${insignia(r.certeza, r.ref)}</span>`).join('')}
        ${n.conyuges.map(r => `<span class="sublinea cony"><span aria-label="cónyuge">⚭</span> ${btnPersona(r.otro)}${insignia(r.certeza, r.ref)}</span>`).join('')}</span></li>`);
      if (!pleg) hijos.forEach(h => rec(h, prof + 1));
    };
    const partes = [];
    (filtro ? bosque.slice(0, 1) : bosque).forEach((raiz, i) => {
      filas.length = 0; rec(raiz, 0);
      partes.push(`${i === 1 ? '<h2>Otras ramas</h2>' : ''}<ul class="arbol" aria-label="Descendencia de ${esc(nombre(raiz.id))}">${filas.join('')}</ul>`);
    });
    if (filtro && !linea.size) return '<p>No se encontró una línea de Adán a Abraham en los datos.</p>';
    return partes.join('');
  }

  /* ---------- Edades ---------- */
  function celda(id, tipo, trad, dif) {
    const e = N.edad(D, id, tipo, trad);
    const cls = dif && dif !== 'igual' ? ' class="difiere"' : '';
    if (!e) return `<td${cls}><span class="vacio" aria-label="sin dato">—</span></td>`;
    return `<td${cls}><button type="button" class="celda${e.derivado ? ' calculo' : ''}" data-edad="${esc(id)}|${tipo}|${trad}" aria-label="${esc(nombre(id))}, ${TIPO_TXT[tipo]} ${trad}: ${e.valor}${e.derivado ? ' (cálculo)' : ''}">${e.valor}${e.derivado ? '<span class="marca-calc" aria-hidden="true">*</span>' : ''}</button></td>`;
  }
  function vistaEdades() {
    const trads = estado.trad === 'ambas' ? ['TM', 'LXX'] : [estado.trad];
    const orden = N.ordenPatriarcas(D);
    const ambas = trads.length === 2;
    const cab = ambas
      ? `<tr><th rowspan="2" scope="col">Persona</th>${N.TIPOS.map(t => `<th colspan="2" scope="colgroup">${TIPO_TXT[t]}</th>`).join('')}</tr><tr>${N.TIPOS.map(() => '<th scope="col">TM</th><th scope="col">LXX</th>').join('')}</tr>`
      : `<tr><th scope="col">Persona</th>${N.TIPOS.map(t => `<th scope="col">${TIPO_TXT[t]}</th>`).join('')}</tr>`;
    const filas = orden.map(id => { const dif = N.diferencias(D, id); return `<tr><th scope="row">${btnPersona(id)}${etiquetaTrad(id)}</th>${N.TIPOS.map(t => trads.map(tr => celda(id, t, tr, dif[t])).join('')).join('')}</tr>`; }).join('');
    return `<h1 tabindex="-1">Edades de los patriarcas</h1>
      <fieldset class="segmentos"><legend>Tradición</legend>${['TM', 'LXX', 'ambas'].map(t => `<label><input type="radio" name="trad" value="${t}" ${estado.trad === t ? 'checked' : ''}><span>${t === 'ambas' ? 'Ambas' : t}</span></label>`).join('')}</fieldset>
      <p class="leyenda"><span class="muestra difiere"></span> TM y LXX difieren (o solo una da el dato) · <span class="marca-calc">*</span> cálculo (no está escrito; se deduce) · pulsa una cifra para ver versículo, cita y fuente.</p>
      ${orden.length ? `<div class="tabla-envoltura" tabindex="0" role="region" aria-label="Tabla de edades"><table class="edades"><thead>${cab}</thead><tbody>${filas}</tbody></table></div>` : '<p>No hay edades en los datos.</p>'}
      <section class="vidas" aria-labelledby="vidas-t"><h2 id="vidas-t">Vidas solapadas <span class="insignia calculo">Cálculo</span></h2>
        <p class="aviso-calculo"><strong>Esto es un CÁLCULO, no lo dice el texto.</strong> Los “años desde Adán” se obtienen sumando las edades al engendrar de la línea Adán → Abraham en la tradición elegida. Supone que cada edad corresponde al hijo siguiente de la línea (p. ej. Gn 5:32 da 500 años a Noé para sus tres hijos), por lo que es una aproximación.</p>
        ${trads.map(barrasHTML).join('')}
      </section>`;
  }
  function barrasHTML(trad) {
    const filas = N.anosDesdeAdan(D, trad).filter(f => f.nacimiento !== null);
    if (!filas.length) return `<p>Sin datos suficientes para ${trad}.</p>`;
    const max = Math.max(1, ...filas.map(f => f.muerte !== null ? f.muerte : f.nacimiento));
    const paso = max > 3000 ? 500 : max > 1200 ? 250 : 100;
    const marcas = []; for (let a = 0; a <= max; a += paso) marcas.push(a);
    const pct = x => (x / max * 100).toFixed(2) + '%';
    const dil = N.anoDiluvio(D, trad);
    const marcaDil = dil && dil.ano <= max ? `<span class="diluvio-marca" style="left:${pct(dil.ano)}"></span>` : '';
    return `<h3>${trad === 'TM' ? 'Texto Masorético (TM)' : 'Septuaginta (LXX)'}</h3>
      ${dil ? `<p class="leyenda"><span class="muestra-diluvio" aria-hidden="true"></span> Diluvio ≈ año ${dil.ano} desde Adán ${insignia('calculo')}: ${esc(nombre(dil.persona))} tenía ${dil.valor} años (${refHTML(dil.ref)}).</p>` : ''}
      <ol class="barras">${filas.map(f => `<li><button type="button" class="barra-fila" data-calc="${trad}|${esc(f.id)}">
        <span class="barra-nombre">${esc(nombre(f.id))}</span><span class="barra-anos">${f.nacimiento}–${f.muerte !== null ? f.muerte : '?'}</span>
        <span class="pista" aria-hidden="true">${marcaDil}<span class="barra${f.muerte === null ? ' abierta' : ''}" style="left:${pct(f.nacimiento)};width:${f.muerte !== null ? pct(f.muerte - f.nacimiento) : '4px'}"></span></span></button></li>`).join('')}</ol>
      <div class="eje" aria-hidden="true">${marcas.map(a => `<span style="left:${pct(a)}">${a}</span>`).join('')}</div>`;
  }

  /* ---------- Fuentes ---------- */
  function vistaFuentes() {
    const fs = D.fuentes || [];
    let fecha = D.generado || '';
    try { if (fecha) fecha = new Date(fecha).toLocaleString('es', { dateStyle: 'long', timeStyle: 'short' }); } catch (e) { /* texto tal cual */ }
    return `<h1 tabindex="-1">Fuentes y etiquetas</h1>
      <section><h2>Fuentes</h2>${fs.length ? `<ul class="fuentes">${fs.map(f => `<li><strong>${esc(f.nombre || f.id)}</strong> <span class="meta">(${esc(f.id)})</span><br>Licencia: ${esc(f.licencia || 'sin indicar')}${f.url ? `<br><a href="${esc(f.url)}" rel="noopener" target="_blank">${esc(f.url)}</a>` : ''}</li>`).join('')}</ul>` : '<p>Sin fuentes declaradas.</p>'}</section>
      <section><h2>Etiquetas de certeza</h2><dl class="etiquetas">
        <dt>${insignia('explicito')}</dt><dd>Lo dice el texto bíblico de forma explícita; se indica el versículo.</dd>
        <dt>${insignia('inferido')}</dt><dd>Supuesto razonable que el texto no afirma directamente (p. ej. una madre no nombrada, o un vínculo deducido por el contexto).</dd>
        <dt>${insignia('calculo')}</dt><dd>Cifra obtenida por operación aritmética a partir del texto (sumas de edades, años desde Adán). No está escrita como tal.</dd></dl></section>
      <section><h2>TM y LXX</h2><p><strong>TM — Texto Masorético:</strong> texto hebreo transmitido por los masoretas; base de la mayoría de las Biblias en español (como la Reina-Valera).</p>
        <p><strong>LXX — Septuaginta:</strong> traducción griega antigua del Antiguo Testamento. En Génesis 5 y 11 da a menudo cifras distintas (suele sumar 100 años a la edad al engendrar) e incluye a un Cainán en Gn 11 que el TM no menciona.</p></section>
      <p class="meta">Datos generados: ${esc(fecha || 'sin fecha')}</p>`;
  }

  /* ---------- Ficha y detalle ---------- */
  const fichaDlg = $('#ficha'), detDlg = $('#detalle');
  function mostrar(dlg) { if (dlg.open) return; if (dlg.showModal) dlg.showModal(); else dlg.setAttribute('open', ''); }
  function cerrar(dlg) { if (!dlg.open) return; if (dlg.close) dlg.close(); else dlg.removeAttribute('open'); }
  const lista = (items, vacio) => items.length ? `<ul class="vinculos">${items.join('')}</ul>` : `<p class="meta">${vacio}</p>`;

  function abrirFicha(id) {
    const p = N.persona(D, id); if (!p) return;
    const I = N.indice(D);
    const extra = r => `${citaHTML(r)}${r.nota ? `<p class="nota">${esc(r.nota)}</p>` : ''}`;
    const padres = (I.padres.get(id) || []).map(r => `<li>${btnPersona(r.de)} <span class="meta">${r.tipo}</span> ${insignia(r.certeza, r.ref)}${extra(r)}</li>`);
    const cony = (I.conyuges.get(id) || []).map(r => `<li>${btnPersona(r.otro)} ${insignia(r.certeza, r.ref)}${extra(r)}</li>`);
    const hijos = N.hijosDe(D, id).map(r => {
      const madre = r.tipo !== 'madre' ? (I.padres.get(r.a) || []).find(x => x.tipo === 'madre') : null;
      return `<li>${btnPersona(r.a)} ${insignia(r.certeza, r.ref)}${madre ? `<span class="meta">madre: ${esc(nombre(madre.de))}</span>` : ''}${extra(r)}</li>`;
    });
    const tieneEdades = N.TIPOS.some(t => N.TRADS.some(tr => N.edad(D, id, t, tr)));
    const dif = N.diferencias(D, id);
    const edades = tieneEdades ? `<table class="edades mini"><thead><tr><th scope="col"></th><th scope="col">TM</th><th scope="col">LXX</th></tr></thead><tbody>${N.TIPOS.map(t => `<tr><th scope="row">${TIPO_TXT[t]}</th>${N.TRADS.map(tr => celda(id, t, tr, dif[t])).join('')}</tr>`).join('')}</tbody></table>` : '<p class="meta">Sin edades registradas.</p>';
    const refs = [...new Set([].concat(p.primera_ref ? [p.primera_ref] : [], p.refs || []))];
    fichaDlg.querySelector('h2').textContent = p.nombre || id;
    fichaDlg.querySelector('.dialogo-cuerpo').innerHTML = `
      <p class="meta">${p.sexo === 'm' ? 'Varón' : p.sexo === 'f' ? 'Mujer' : 'Sexo no indicado'}${p.primera_ref ? ' · aparece en ' + refHTML(p.primera_ref) : ''} ${etiquetaTrad(id)}</p>
      ${(r => r ? `<p><a class="boton" href="#leer/${N.parseRef(r).cap}/${N.parseRef(r).v}">Leer donde aparece</a></p>` : '')([p.primera_ref, p.ref_mencion].concat(p.refs || []).find(x => N.clave(x)))}
      <h3>Padres</h3>${lista(padres, 'No constan.')}
      ${cony.length ? '<h3>Cónyuges</h3>' + lista(cony, '') : ''}
      <h3>Hijos</h3>${lista(hijos, 'No constan.')}
      <h3>Edades</h3>${edades}
      ${p.nota ? `<h3>Notas</h3><p class="nota">${esc(p.nota)}</p>` : ''}
      <h3>Versículos</h3>${refs.length ? `<ul class="refs">${refs.map(r => `<li>${refHTML(r)}</li>`).join('')}</ul>` : '<p class="meta">Sin referencias.</p>'}`;
    mostrar(fichaDlg);
    fichaDlg.querySelector('.dialogo-cuerpo').scrollTop = 0;
  }

  function abrirDetalle(titulo, html) {
    detDlg.querySelector('h2').textContent = titulo;
    detDlg.querySelector('.dialogo-cuerpo').innerHTML = html;
    mostrar(detDlg);
  }
  function detalleEdad(id, tipo, trad) {
    const e = N.edad(D, id, tipo, trad); if (!e) return;
    let cuerpo = `<p class="cifra">${e.valor} años</p><p>${insignia(e.derivado ? 'calculo' : (e.certeza === 'calculo' ? 'calculo' : 'texto'), e.derivado ? '' : e.ref)}</p>`;
    if (e.derivado) {
      cuerpo += `<p>No está escrito: se calcula como ${e.tipo === 'total' ? 'edad al engendrar + años restantes' : 'total − edad al engendrar'}.</p><ul class="vinculos">${e.de.map(x => `<li>${TIPO_TXT[x.tipo]}: <strong>${esc(x.valor)}</strong> · ${refHTML(x.ref)}${x.cita ? `<blockquote>${esc(x.cita)}</blockquote>` : ''}<span class="meta">Fuente: ${esc(fuenteNombre(x.fuente))}</span></li>`).join('')}</ul>`;
    } else {
      cuerpo += `${e.cita ? `<blockquote>${esc(e.cita)}</blockquote>` : '<p class="meta">Sin cita literal.</p>'}<p class="meta">Fuente: ${esc(fuenteNombre(e.fuente))}${e.ref ? ' · ' + refHTML(e.ref) : ''}</p>`;
    }
    const dif = N.diferencias(D, id)[tipo];
    if (dif === 'difiere') { const o = trad === 'TM' ? 'LXX' : 'TM'; cuerpo += `<p class="difiere-txt">En ${o}: ${N.edad(D, id, tipo, o).valor}.</p>`; }
    else if (dif && dif.startsWith('solo_')) cuerpo += `<p class="difiere-txt">Solo ${dif.slice(5)} da este dato.</p>`;
    abrirDetalle(`${nombre(id)} · ${TIPO_TXT[tipo]} (${trad})`, cuerpo);
  }
  function detalleCalc(trad, id) {
    const f = N.anosDesdeAdan(D, trad).find(x => x.id === id); if (!f) return;
    const suma = f.pasos.length ? `<ol class="vinculos">${f.pasos.map(p => `<li>${esc(nombre(p.id))} engendra a los <strong>${p.valor}</strong> · ${refHTML(p.ref)}</li>`).join('')}</ol>` : '<p>Punto de partida (año 0).</p>';
    const muerte = f.total ? `<p>Muerte ≈ ${f.nacimiento} + ${f.total.valor} (vida total${f.total.derivado ? ', también calculada' : ''}${f.total.ref ? ', ' + refHTML(f.total.ref) : ''}) = <strong>${f.muerte}</strong>.</p>` : '<p>Sin edad total: no se puede situar la muerte.</p>';
    abrirDetalle(`${nombre(id)} · años desde Adán (${trad})`, `<p>${insignia('calculo')}</p><p>Nacimiento ≈ año <strong>${f.nacimiento}</strong> desde Adán, sumando:</p>${suma}${muerte}<p class="meta">Cálculo de esta app, no texto bíblico.</p>`);
  }

  /* ---------- Navegación ---------- */
  function ruta() { const h = decodeURIComponent(location.hash.slice(1)) || 'leer'; const [vista, ...args] = h.split('/'); return { vista, args }; }
  const VISTAS = { leer: vistaLeer, arbol: vistaArbol, edades: vistaEdades, fuentes: vistaFuentes };
  let primera = true;
  function render(foco) {
    if (!D) { main.innerHTML = '<h1>Sin datos</h1><p>No se encontró <code>datos/genesis.js</code>. Añade <code>?ejemplo</code> a la dirección para ver los datos de prueba.</p>'; return; }
    const { vista, args } = ruta();
    const fn = VISTAS[vista] || vistaLeer;
    main.innerHTML = fn(args);
    document.querySelectorAll('.nav-principal a').forEach(a => { if (a.dataset.vista === (VISTAS[vista] ? vista : 'leer')) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); });
    document.title = (main.querySelector('h1') || {}).textContent + ' · Biblia';
    const marcado = main.querySelector('.vers.activo, .fila.foco');
    if (marcado && foco !== false) { marcado.scrollIntoView({ block: 'center' }); }
    else if (foco !== false && !primera) { window.scrollTo(0, 0); }
    if (foco !== false && !primera) { const h = main.querySelector('h1'); if (h) h.focus({ preventScroll: true }); }
    primera = false;
  }
  function rerender(selectorFoco) { const y = window.scrollY; render(false); window.scrollTo(0, y); if (selectorFoco) { const el = main.querySelector(selectorFoco); if (el) el.focus(); } }

  window.addEventListener('hashchange', () => { cerrar(detDlg); cerrar(fichaDlg); render(); });

  document.addEventListener('click', e => {
    const t = e.target;
    if (t instanceof HTMLDialogElement && t.open) { cerrar(t); return; }
    const c = t.closest('[data-cerrar]'); if (c) { cerrar(c.closest('dialog')); return; }
    const p = t.closest('[data-persona]'); if (p) { e.preventDefault(); cerrar(detDlg); abrirFicha(p.dataset.persona); return; }
    const ed = t.closest('[data-edad]'); if (ed) { const [id, tipo, trad] = ed.dataset.edad.split('|'); detalleEdad(id, tipo, trad); return; }
    const ca = t.closest('[data-calc]'); if (ca) { const [trad, id] = ca.dataset.calc.split('|'); detalleCalc(trad, id); return; }
    const pl = t.closest('[data-plegar]'); if (pl) { const id = pl.dataset.plegar; estado.plegados.has(id) ? estado.plegados.delete(id) : estado.plegados.add(id); rerender(`[data-plegar="${CSS.escape(id)}"]`); return; }
    const ac = t.closest('[data-activar]'); if (ac) { activar(ac.dataset.activar); return; }
    if (t.closest('[data-hoja]')) { estado.hoja = !estado.hoja; const a = $('#acompanante'); if (a) { a.classList.toggle('abierta', estado.hoja); a.querySelector('[data-hoja]').setAttribute('aria-expanded', estado.hoja); } return; }
    const ls = t.closest('[data-leido-seguir]'); if (ls) { const L = pasajesLeidos(); L.add(ls.dataset.leidoSeguir); store.set('biblia.pasajesLeidos', [...L]); const ps = N.pasajes(D), i = ps.findIndex(x => x.id === ls.dataset.leidoSeguir); location.hash = ps[i + 1] ? `#leer/p/${ps[i + 1].id}` : '#leer'; return; }
    const ve = t.closest('.vers'); if (ve && !t.closest('button, a')) { activar(ve.dataset.v); return; }
    if (t.closest('#btn-mujeres')) { estado.mujeres = !estado.mujeres; rerender('#btn-mujeres'); return; }
    if (t.closest('#btn-linea')) { estado.lineaSolo = !estado.lineaSolo; rerender('#btn-linea'); return; }
    if (t.closest('#btn-plegar')) { N.construirBosque(D).forEach(function r(n) { if (n.hijos.length) estado.plegados.add(n.id); n.hijos.forEach(r); }); rerender('#btn-plegar'); return; }
    if (t.closest('#btn-desplegar')) { estado.plegados.clear(); rerender('#btn-desplegar'); return; }
  });
  document.addEventListener('change', e => {
    const t = e.target;
    if (t.name === 'trad') { estado.trad = t.value; store.set('biblia.trad', t.value); rerender(`input[name="trad"][value="${t.value}"]`); }
  });
  document.addEventListener('input', e => {
    if (e.target.id === 'buscar') { estado.q = e.target.value; const r = $('#resultados'); if (r) r.innerHTML = resultadosHTML(); }
  });

  /* ---------- Service worker y aviso de versión ---------- */
  function registrarSW() {
    if (!('serviceWorker' in navigator) || location.protocol === 'file:') return;
    const aviso = $('#aviso'), btn = $('#actualizar');
    let pedido = false;
    const avisar = w => { if (!w) return; aviso.hidden = false; btn.onclick = () => { pedido = true; w.postMessage('SKIP_WAITING'); }; };
    navigator.serviceWorker.register('sw.js').then(reg => {
      if (reg.waiting && navigator.serviceWorker.controller) avisar(reg.waiting);
      reg.addEventListener('updatefound', () => {
        const n = reg.installing;
        if (n) n.addEventListener('statechange', () => { if (n.state === 'installed' && navigator.serviceWorker.controller) avisar(n); });
      });
      document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') reg.update().catch(() => {}); });
    }).catch(() => {});
    navigator.serviceWorker.addEventListener('controllerchange', () => { if (pedido) { pedido = false; location.reload(); } });
  }

  function iniciar() { render(false); registrarSW(); }
  if (!D && /[?&]ejemplo/.test(location.search)) {
    const s = document.createElement('script');
    s.src = 'pruebas/datos-ejemplo.js';
    s.onload = () => { D = window.BIBLIA_DATOS || null; iniciar(); };
    s.onerror = iniciar;
    document.head.appendChild(s);
  } else iniciar();
})();
