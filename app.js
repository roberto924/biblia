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
    const lugares = new Map(), lugaresPorRef = new Map(), mencionesLugar = new Map();
    const marcarL = (id, ref) => { const k = clave(ref); if (k === null || !id) return; if (!lugaresPorRef.has(k)) lugaresPorRef.set(k, new Set()); lugaresPorRef.get(k).add(id); };
    (d.lugares || []).forEach(l => { if (l && l.id) { lugares.set(l.id, l); (l.refs || []).forEach(r => marcarL(l.id, r)); } });
    (d.menciones_lugar || []).forEach(m => {
      const k = m && m.lugar ? clave(m.ref) : null; if (k === null) return;
      add(mencionesLugar, k, m); marcarL(m.lugar, m.ref);
    });
    return { datos: d, personas, hijos, padres, conyuges, edades, menciones, porRef, primera, lugares, lugaresPorRef, mencionesLugar };
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

  // Menciones de personas (tipo 'persona') o lugares ('lugar') en un versículo: las de los datos si son
  // válidas; si no hay, se buscan los nombres de quienes tienen ese versículo en sus refs.
  function mencionesDe(d, ref, texto, tipo) {
    const I = indice(d), k = clave(ref);
    const valida = m => Number.isInteger(m.inicio) && Number.isInteger(m.fin) && m.inicio >= 0 && m.fin > m.inicio && m.fin <= texto.length;
    const datos = ((tipo === 'lugar' ? I.mencionesLugar : I.menciones).get(k) || []).filter(valida);
    // Quien ya tiene mención en los datos no se busca por nombre; el resto, sí.
    const out = datos.map(m => ({ [tipo]: m[tipo], inicio: m.inicio, fin: m.fin })), cubiertos = new Set(datos.map(m => m[tipo]));
    const fuente = tipo === 'lugar' ? I.lugares : I.personas;
    for (const id of ((tipo === 'lugar' ? I.lugaresPorRef : I.porRef).get(k) || [])) {
      const p = fuente.get(id);
      if (!p || p.sin_nombre || cubiertos.has(id)) continue;
      for (const nom of new Set([p.nombre, p.nombre_rv1909].filter(Boolean))) {
        const re = new RegExp('(^|[^\\p{L}])(' + nom.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')(?![\\p{L}])', 'gu');
        let m;
        while ((m = re.exec(texto))) { const i = m.index + m[1].length; out.push({ [tipo]: id, inicio: i, fin: i + m[2].length }); }
      }
    }
    return out;
  }
  // Trozos [{texto, persona?|lugar?}] de un versículo; ignora menciones fuera de rango o solapadas.
  function segmentar(d, ref, texto) {
    texto = String(texto || '');
    const ms = mencionesDe(d, ref, texto, 'persona').concat(mencionesDe(d, ref, texto, 'lugar'))
      .sort((a, b) => a.inicio - b.inicio || b.fin - a.fin);
    const out = [];
    let pos = 0;
    for (const m of ms) {
      if (m.inicio < pos) continue;
      if (m.inicio > pos) out.push({ texto: texto.slice(pos, m.inicio) });
      out.push(m.lugar ? { texto: texto.slice(m.inicio, m.fin), lugar: m.lugar } : { texto: texto.slice(m.inicio, m.fin), persona: m.persona });
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
    const lugs = [];
    [...ks].sort((a, b) => a - b).forEach(k => (I.lugaresPorRef.get(k) || []).forEach(id => { if (!lugs.includes(id) && I.lugares.has(id)) lugs.push(id); }));
    return { personas: ids.map(id => ({ id, contexto: contextoPersona(d, id) })), vinculos, edades: edadesV,
      sinNombre: ids.filter(id => (I.personas.get(id) || {}).sin_nombre), lugares: lugs };
  }
  // ¿Tiene el versículo vínculos, edades, alusiones sin nombre o lugares? (marca al margen)
  const tieneApoyo = (d, ref) => { const A = acompanante(d, [ref]); return A.vinculos.length + A.edades.length + A.sinNombre.length + A.lugares.length > 0; };

  /* ---- Lugares y mapa ---- */
  const lugar = (d, id) => indice(d).lugares.get(id) || null;
  const lugaresDeRefs = (d, refs) => acompanante(d, refs).lugares;
  const lugaresDePasaje = (d, p) => lugaresDeRefs(d, versiculosDe(d, p).map(v => v.ref));
  // 'alta' | 'media' | 'baja' | 'desconocida' (sin coordenadas válidas)
  function confianzaLugar(l) {
    const u = l && l.ubicacion;
    if (!u || u.lat === null || u.lon === null || u.lat === undefined || u.lon === undefined || !Number.isFinite(+u.lat) || !Number.isFinite(+u.lon)) return 'desconocida';
    return ['alta', 'media', 'baja'].includes(u.confianza) ? u.confianza : 'baja';
  }
  // Equirectangular con corrección por la latitud media del recuadro.
  function proyeccion(bbox) {
    const b = Array.isArray(bbox) && bbox.length === 4 && bbox.every(Number.isFinite) ? bbox : [25, 20, 60, 45];
    const latMedia = (b[1] + b[3]) / 2;
    return { bbox: b, latMedia, k: Math.cos(latMedia * Math.PI / 180) };
  }
  const proyectar = (P, lon, lat) => [lon * P.k, -lat];
  const desproyectar = (P, x, y) => [x / P.k, -y];
  // Rectángulo {x,y,w,h} (coordenadas proyectadas) que contiene los puntos [lon,lat] con margen y tamaño mínimo (grados).
  function encuadre(P, puntos, opc) {
    opc = opc || {};
    const margen = opc.margen === undefined ? 0.15 : opc.margen, minimo = opc.minimo === undefined ? 2 : opc.minimo;
    let pts = (puntos || []).filter(p => p && Number.isFinite(p[0]) && Number.isFinite(p[1]));
    if (!pts.length) pts = [[P.bbox[0], P.bbox[1]], [P.bbox[2], P.bbox[3]]];
    const xy = pts.map(p => proyectar(P, p[0], p[1]));
    const xs = xy.map(p => p[0]), ys = xy.map(p => p[1]);
    let x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    let w = Math.max(x1 - x0, minimo * P.k), h = Math.max(y1 - y0, minimo);
    w *= 1 + 2 * margen; h *= 1 + 2 * margen;
    return { x: cx - w / 2, y: cy - h / 2, w, h };
  }
  // Coloca etiquetas sin solaparse entre sí ni con los marcadores; las que no caben se omiten.
  function colocarEtiquetas(items, ancho, alto) {
    const puestos = items.map(it => ({ x: it.x - 6, y: it.y - 6, w: 12, h: 12, id: it.id })), out = [];
    const choca = (r, id) => puestos.some(p => p.id !== id && r.x < p.x + p.w && p.x < r.x + r.w && r.y < p.y + p.h && p.y < r.y + r.h);
    items.slice().sort((a, b) => (b.prioridad || 0) - (a.prioridad || 0)).forEach(it => {
      const w = String(it.texto).length * 6.6 + 4, h = 14, g = 9;
      const ops = [{ x: it.x + g, y: it.y - h / 2, anc: 'start' }, { x: it.x - g - w, y: it.y - h / 2, anc: 'end' },
        { x: it.x - w / 2, y: it.y - g - h, anc: 'middle' }, { x: it.x - w / 2, y: it.y + g, anc: 'middle' }];
      for (const o of ops) {
        const r = { x: o.x, y: o.y, w, h };
        if (r.x < 0 || r.y < 0 || r.x + w > ancho || r.y + h > alto || choca(r, it.id)) continue;
        puestos.push(Object.assign({ id: '#' + it.id }, r));
        out.push({ id: it.id, texto: it.texto, x: o.anc === 'start' ? o.x : o.anc === 'end' ? o.x + w : o.x + w / 2, y: o.y + h - 3, anc: o.anc, caja: r });
        return;
      }
    });
    return out;
  }

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
    acompanante, tieneApoyo, primerasApariciones, miniArbol, anoDiluvio,
    lugar, lugaresDeRefs, lugaresDePasaje, confianzaLugar, proyeccion, proyectar, desproyectar, encuadre, colocarEtiquetas, indice, persona, hijosDe, encontrar, idAdan, idAbraham,
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
  const estado = { trad: store.get('biblia.trad', 'TM'), lineaSolo: false, mujeres: false, hoja: false, pasaje: null, activo: null, foco: null, mapaFiltro: '', mapaConf: new Set(['alta', 'media', 'baja']), mapaQ: '', mapaSel: null, plegados: new Set(), q: '' };

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
        if (s.lugar) return `<button type="button" class="mencion-lugar" data-lugar="${esc(s.lugar)}">${esc(s.texto)}</button>`;
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
    const n = A.vinculos.length + A.edades.length + A.sinNombre.length + A.lugares.length;
    const ambito = estado.activo ? `Gn ${estado.activo}` : 'Todo el pasaje';
    const sec = (t, cuerpo, icono) => `<section class="acomp-sec"><h3>${icono}${t}</h3>${cuerpo}</section>`;
    const I = (d) => `<svg viewBox="0 0 20 20" aria-hidden="true"><path d="${d}"/></svg>`;
    let html = '';
    if (A.personas.length) html += sec('Quién aparece', `<ul class="quien">${A.personas.map(x => `<li>${btnPersona(x.id)}${x.contexto ? `<span class="contexto">${esc(x.contexto)}</span>` : ''}</li>`).join('')}</ul>`, I('M10 9a3 3 0 100-6 3 3 0 000 6zM4 17c0-3.3 2.7-5 6-5s6 1.7 6 5'));
    if (A.lugares.length) {
      const ub = A.lugares.filter(id => N.confianzaLugar(N.lugar(D, id)) !== 'desconocida');
      html += sec('Dónde ocurre', `${ub.length ? mapaHTML(ub, { mini: true }) : ''}<ul class="lugares-lista">${A.lugares.map(id => { const l = N.lugar(D, id) || {}, c = N.confianzaLugar(l); return `<li>${btnLugar(id)}<span class="contexto">${c === 'desconocida' ? 'Ubicación desconocida' + (l.nota ? ': ' + esc(l.nota) : '') : esc((l.ubicacion && l.ubicacion.identificacion) || '') + '. ' + CONF_TXT[c]}</span></li>`; }).join('')}</ul>`, I('M10 17s5-4.6 5-8.5a5 5 0 10-10 0C5 12.4 10 17 10 17zM10 10.2a1.7 1.7 0 100-3.4 1.7 1.7 0 000 3.4'));
    }
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
    const a = $('#acompanante'); if (a) { a.innerHTML = acompHTML(); montarMapas(a); }
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
      <section><h2>Lugares y mapa</h2>
        <p>El <strong>nombre</strong> de cada lugar es texto bíblico. Su <strong>ubicación</strong> es una identificación moderna propuesta por la investigación y puede discutirse.</p>
        <ul class="fuentes">
          <li><strong>OpenBible.info, Bible Geocoding Data</strong>: identificaciones modernas, puntuaciones y alternativas.<br>Licencia: CC BY 4.0. Atribución: OpenBible.info.<br><a href="https://www.openbible.info/geo/" target="_blank" rel="noopener">https://www.openbible.info/geo/</a></li>
          <li><strong>${esc((MAPA && MAPA.fuente) || 'Natural Earth')}</strong>: costas, ríos y lagos del mapa base.<br>Licencia: dominio público. Hecho con Natural Earth.<br><a href="${esc((MAPA && MAPA.url) || 'https://www.naturalearthdata.com/')}" target="_blank" rel="noopener">${esc((MAPA && MAPA.url) || 'https://www.naturalearthdata.com/')}</a></li>
        </ul>
        <dl class="etiquetas">
          <dt>${icoConf('alta')} Confianza alta</dt><dd>La identificación moderna es ampliamente aceptada.</dd>
          <dt>${icoConf('media')} Confianza media</dt><dd>Identificación probable; hay propuestas alternativas, que se ven como marcadores huecos al seleccionar el lugar.</dd>
          <dt>${icoConf('baja')} Confianza baja</dt><dd>Identificación incierta o discutida; tómala como hipótesis.</dd>
          <dt>${icoConf('desconocida')} Ubicación desconocida</dt><dd>No hay identificación fiable (por ejemplo, Edén o Nod). Se dice, pero no se dibuja.</dd>
        </dl></section>
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

  /* ---------- Lugares y mapa ---------- */
  let MAPA = window.BIBLIA_MAPA || null;
  const CONF_TXT = { alta: 'Confianza alta', media: 'Confianza media', baja: 'Confianza baja', desconocida: 'Ubicación desconocida' };
  const CONF_DESC = {
    alta: 'la identificación moderna es ampliamente aceptada.',
    media: 'identificación probable; hay propuestas alternativas.',
    baja: 'identificación incierta o discutida; tómala como hipótesis.'
  };
  const TIPO_LUGAR = { ciudad: 'Ciudad', region: 'Región', rio: 'Río', monte: 'Monte', otro: 'Lugar' };
  const nombreLugar = id => { const l = N.lugar(D, id); return l ? (l.nombre || id) : id; };
  function formaConf(conf, r) {
    if (conf === 'alta') return `<circle r="${r}" class="f-alta"/>`;
    if (conf === 'media') return `<rect x="${-r * .8}" y="${-r * .8}" width="${r * 1.6}" height="${r * 1.6}" transform="rotate(45)" class="f-media"/>`;
    if (conf === 'baja') return `<path d="M0 ${-r * 1.15}L${r * 1.05} ${r * .75}H${-r * 1.05}Z" class="f-baja"/>`;
    if (conf === 'alt') return `<circle r="${r * .85}" class="f-alt"/>`;
    return `<circle r="${r * .9}" class="f-desc"/><path d="M-2.2 -1.6a2.2 2.2 0 1 1 2.2 2.6v1" class="f-desc-q"/>`;
  }
  const icoConf = conf => `<svg class="ico-conf" viewBox="-7 -7 14 14" aria-hidden="true">${formaConf(conf, 5)}</svg>`;
  const btnLugar = id => { const c = N.confianzaLugar(N.lugar(D, id)); return `<button type="button" class="lugar-btn conf-${c}" data-lugar="${esc(id)}">${icoConf(c)}${esc(nombreLugar(id))}</button>`; };
  const leyendaConf = () => `<p class="leyenda-mapa">${['alta', 'media', 'baja'].map(c => `<span>${icoConf(c)}${CONF_TXT[c].replace('Confianza ', '')}</span>`).join('')}<span>${icoConf('alt')}alternativa</span></p>`;
  const mapaHTML = (ids, opc) => `<div class="mapa${opc && opc.mini ? ' mini' : ''}" data-mapa="${esc(JSON.stringify({ ids, sel: (opc && opc.sel) || null, mini: !!(opc && opc.mini) }))}"></div>`;
  function montarMapas(raiz) { if (raiz) raiz.querySelectorAll('.mapa[data-mapa]:not([data-montado])').forEach(el => { try { crearMapa(el, JSON.parse(el.dataset.mapa)); } catch (e) { el.textContent = 'No se pudo dibujar el mapa.'; } }); }

  function crearMapa(el, cfg) {
    el.dataset.montado = '1';
    const P = N.proyeccion(MAPA && MAPA.bbox);
    const ubicados = cfg.ids.map(id => N.lugar(D, id)).filter(l => N.confianzaLugar(l) !== 'desconocida');
    const coord = l => [+l.ubicacion.lon, +l.ubicacion.lat];
    let sel = cfg.sel, W = 320, H = 220;
    const v = { cx: 0, cy: 0, s: 1 };
    const pth = (ring, cerrar) => (ring || []).length ? 'M' + ring.map(p => N.proyectar(P, p[0], p[1]).map(n => n.toFixed(3)).join(' ')).join('L') + (cerrar ? 'Z' : '') : '';
    let base = '<rect class="mar" x="-2000" y="-2000" width="4000" height="4000"/>';
    if (MAPA) {
      base += (MAPA.costas || []).map(r => `<path class="tierra" d="${pth(r, true)}"/>`).join('');
      base += (MAPA.lagos || []).map(r => `<path class="lago" d="${pth(r, true)}"/>`).join('');
      base += (MAPA.rios || []).map(r => `<path class="rio" d="${pth(r.puntos, false)}"/>`).join('');
    }
    const b = P.bbox; let ret = '';
    for (let lon = Math.ceil(b[0] / 5) * 5; lon <= b[2]; lon += 5) ret += `<path class="reticula" d="${pth([[lon, b[1]], [lon, b[3]]])}"/>`;
    for (let lat = Math.ceil(b[1] / 5) * 5; lat <= b[3]; lat += 5) ret += `<path class="reticula" d="${pth([[b[0], lat], [b[2], lat]])}"/>`;
    el.innerHTML = `<div class="mapa-lienzo"><svg tabindex="0" role="application" aria-roledescription="mapa" aria-label="Mapa con ${ubicados.length} ${ubicados.length === 1 ? 'lugar' : 'lugares'}. Flechas para mover, más y menos para acercar.">
        <g class="base">${base}${ret}</g><g class="capa"></g></svg>
        <div class="mapa-ctrl"><button type="button" data-z="1" aria-label="Acercar">+</button><button type="button" data-z="-1" aria-label="Alejar">−</button>
        <button type="button" data-z="0" aria-label="Encuadrar los lugares"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 7V3h4M13 3h4v4M17 13v4h-4M7 17H3v-4"/></svg></button></div>
        ${MAPA ? '' : '<p class="mapa-aviso">Mapa base no disponible: solo se muestra la retícula.</p>'}</div>
      ${leyendaConf()}<div class="mapa-info" aria-live="polite"></div>`;
    const svg = el.querySelector('svg'), gBase = el.querySelector('.base'), capa = el.querySelector('.capa'), info = el.querySelector('.mapa-info');
    const aPant = (lon, lat) => { const [x, y] = N.proyectar(P, lon, lat); return [(x - v.cx) * v.s + W / 2, (y - v.cy) * v.s + H / 2]; };
    const full = N.encuadre(P, [], { margen: 0 });
    const sMin = () => Math.min(W / full.w, H / full.h) * 0.6, sMax = () => Math.min(W, H) / 0.25;
    let pend = false;
    const pedir = () => { if (!pend) { pend = true; requestAnimationFrame(() => { pend = false; dibujar(); }); } };
    function dibujar() {
      svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
      gBase.setAttribute('transform', `matrix(${v.s} 0 0 ${v.s} ${W / 2 - v.cx * v.s} ${H / 2 - v.cy * v.s})`);
      let html = '';
      const lsel = sel && N.lugar(D, sel);
      if (lsel && N.confianzaLugar(lsel) !== 'desconocida') {
        const [x0, y0] = aPant(...coord(lsel));
        (lsel.alternativas || []).filter(a => Number.isFinite(+a.lat) && Number.isFinite(+a.lon)).forEach(a => {
          const [x, y] = aPant(+a.lon, +a.lat);
          html += `<line class="alt-linea" x1="${x0}" y1="${y0}" x2="${x}" y2="${y}"/><g class="marcador alt" transform="translate(${x} ${y})"><title>Alternativa: ${esc(a.identificacion || '')}</title>${formaConf('alt', 6)}</g>`;
        });
      }
      const items = ubicados.map(l => { const [x, y] = aPant(...coord(l)); const c = N.confianzaLugar(l); return { id: l.id, x, y, c, texto: l.nombre || l.id, prioridad: (l.id === sel ? 10 : 0) + { alta: 3, media: 2, baja: 1 }[c] }; });
      items.forEach(it => { html += `<g class="marcador conf-${it.c}${it.id === sel ? ' sel' : ''}" transform="translate(${it.x.toFixed(1)} ${it.y.toFixed(1)})" data-lugar-mapa="${esc(it.id)}" tabindex="0" role="button" aria-label="${esc(it.texto)}, ${CONF_TXT[it.c].toLowerCase()}"><circle r="16" class="toque"/>${formaConf(it.c, it.id === sel ? 8 : 6)}</g>`; });
      N.colocarEtiquetas(items, W, H).forEach(e => { html += `<text class="etq${e.id === sel ? ' sel' : ''}" x="${e.x.toFixed(1)}" y="${e.y.toFixed(1)}" text-anchor="${e.anc}">${esc(e.texto)}</text>`; });
      capa.innerHTML = html;
    }
    function encuadrar() {
      const pts = ubicados.map(coord);
      const lsel = sel && N.lugar(D, sel);
      if (lsel) (lsel.alternativas || []).forEach(a => { if (Number.isFinite(+a.lat) && Number.isFinite(+a.lon)) pts.push([+a.lon, +a.lat]); });
      const r = N.encuadre(P, pts, { minimo: cfg.mini ? 4 : 3 });
      v.s = Math.min(W / r.w, H / r.h); v.cx = r.x + r.w / 2; v.cy = r.y + r.h / 2;
      dibujar();
    }
    function zoomEn(px, py, f) {
      const s = Math.min(sMax(), Math.max(sMin(), v.s * f));
      const wx = v.cx + (px - W / 2) / v.s, wy = v.cy + (py - H / 2) / v.s;
      v.s = s; v.cx = wx - (px - W / 2) / s; v.cy = wy - (py - H / 2) / s;
      pedir();
    }
    function seleccionar(id) {
      sel = id; dibujar();
      const l = N.lugar(D, id);
      info.innerHTML = l ? `<p><strong>${esc(l.nombre)}</strong>: ${esc((l.ubicacion && l.ubicacion.identificacion) || '')} <span class="meta">(${CONF_TXT[N.confianzaLugar(l)].toLowerCase()}${(l.alternativas || []).length ? `, ${l.alternativas.length} alternativa${l.alternativas.length > 1 ? 's' : ''}` : ''})</span>
        <button type="button" class="boton mini-boton secundario" data-lugar="${esc(id)}">Ver ficha</button></p>` : '';
    }
    // Arrastre, pellizco y rueda
    const punteros = new Map(); let previo = null, recorrido = 0;
    const pos = e => { const r = svg.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
    const estadoP = () => { const ps = [...punteros.values()]; if (ps.length < 2) return { n: ps.length, c: ps[0], d: 0 }; const [a, c] = ps; return { n: 2, c: [(a[0] + c[0]) / 2, (a[1] + c[1]) / 2], d: Math.hypot(a[0] - c[0], a[1] - c[1]) }; };
    svg.addEventListener('pointerdown', e => { punteros.set(e.pointerId, pos(e)); previo = estadoP(); if (punteros.size === 1) recorrido = 0; });
    svg.addEventListener('pointermove', e => {
      if (!punteros.has(e.pointerId)) return;
      punteros.set(e.pointerId, pos(e));
      const ahora = estadoP();
      if (previo && ahora.n === previo.n && ahora.c) {
        const dx = ahora.c[0] - previo.c[0], dy = ahora.c[1] - previo.c[1];
        recorrido += Math.abs(dx) + Math.abs(dy);
        if (recorrido > 6 && !svg.hasPointerCapture(e.pointerId)) { try { svg.setPointerCapture(e.pointerId); } catch (er) { /* */ } }
        v.cx -= dx / v.s; v.cy -= dy / v.s;
        if (ahora.n === 2 && previo.d > 0) zoomEn(ahora.c[0], ahora.c[1], ahora.d / previo.d);
        pedir();
      }
      previo = ahora;
    });
    const soltar = e => { punteros.delete(e.pointerId); previo = punteros.size ? estadoP() : null; };
    svg.addEventListener('pointerup', soltar); svg.addEventListener('pointercancel', soltar);
    svg.addEventListener('wheel', e => { e.preventDefault(); const [x, y] = pos(e); zoomEn(x, y, Math.exp(-e.deltaY * 0.0015)); }, { passive: false });
    svg.addEventListener('click', e => { if (recorrido > 6) return; const m = e.target.closest('[data-lugar-mapa]'); if (m) seleccionar(m.dataset.lugarMapa); });
    svg.addEventListener('keydown', e => {
      const m = e.target.closest && e.target.closest('[data-lugar-mapa]');
      if (m && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); seleccionar(m.dataset.lugarMapa); return; }
      const paso = 40 / v.s, k = { ArrowLeft: [-paso, 0], ArrowRight: [paso, 0], ArrowUp: [0, -paso], ArrowDown: [0, paso] }[e.key];
      if (k) { e.preventDefault(); v.cx += k[0]; v.cy += k[1]; pedir(); }
      else if (e.key === '+' || e.key === '=') zoomEn(W / 2, H / 2, 1.4);
      else if (e.key === '-') zoomEn(W / 2, H / 2, 1 / 1.4);
    });
    el.querySelector('.mapa-ctrl').addEventListener('click', e => {
      const bt = e.target.closest('[data-z]'); if (!bt) return;
      const z = +bt.dataset.z; if (z === 0) encuadrar(); else zoomEn(W / 2, H / 2, z > 0 ? 1.5 : 1 / 1.5);
    });
    const medir = () => { const r = svg.getBoundingClientRect(); if (r.width > 10 && r.height > 10) { W = r.width; H = r.height; return true; } return false; };
    let listo = false;
    const alCambiar = () => { const w0 = W, h0 = H; if (!medir()) return; if (!listo) { listo = true; encuadrar(); } else if (w0 !== W || h0 !== H) dibujar(); };
    if (window.ResizeObserver) new ResizeObserver(alCambiar).observe(svg);
    alCambiar(); if (!listo) { listo = true; encuadrar(); }
    if (sel) seleccionar(sel);
  }

  function abrirLugar(id) {
    const l = N.lugar(D, id); if (!l) return;
    const c = N.confianzaLugar(l), u = l.ubicacion || {};
    const alts = (l.alternativas || []).filter(a => a && a.identificacion);
    const refs = [...new Set(l.refs || [])];
    const fuente = l.fuente === 'openbible' ? 'OpenBible.info, Bible Geocoding Data' : fuenteNombre(l.fuente);
    fichaDlg.querySelector('h2').textContent = l.nombre || id;
    fichaDlg.querySelector('.dialogo-cuerpo').innerHTML = `
      <p class="meta">${esc(TIPO_LUGAR[l.tipo] || 'Lugar')}${l.nombre_rv1909 && l.nombre_rv1909 !== l.nombre ? `. En la RV1909: «${esc(l.nombre_rv1909)}»` : ''}</p>
      <section class="bloque bloque-texto"><h3>El texto dice</h3>
        ${refs.length ? `<p class="meta">El nombre aparece en:</p><ul class="refs">${refs.map(r => `<li>${refHTML(r)}</li>`).join('')}</ul>` : '<p class="meta">Sin versículos registrados.</p>'}</section>
      <section class="bloque bloque-moderno"><h3>Identificación moderna</h3>
        ${c === 'desconocida' ? `<p class="desconocida">${icoConf('desconocida')} Ubicación desconocida.</p><p class="meta">No se dibuja en el mapa.</p>`
          : `<p class="ident">${icoConf(c)} <strong>${esc(u.identificacion || 'Sin nombre moderno')}</strong></p>
             <p><strong>${CONF_TXT[c]}</strong>: ${CONF_DESC[c]}</p>
             ${u.puntuacion_openbible !== undefined && u.puntuacion_openbible !== null ? `<p class="meta">Puntuación de OpenBible: ${esc(u.puntuacion_openbible)}</p>` : ''}
             <p class="meta">${(+u.lat).toFixed(2)}° N, ${(+u.lon).toFixed(2)}° E</p>
             ${mapaHTML([id], { mini: true, sel: id })}`}
        ${alts.length ? `<h4>Otras identificaciones propuestas</h4><ul class="alternativas">${alts.map(a => `<li>${esc(a.identificacion)}${a.puntuacion_openbible !== undefined && a.puntuacion_openbible !== null ? ` <span class="meta">(puntuación ${esc(a.puntuacion_openbible)})</span>` : ''}</li>`).join('')}</ul>` : ''}
        <p class="meta">Fuente: ${l.url_fuente ? `<a href="${esc(l.url_fuente)}" target="_blank" rel="noopener">${esc(fuente)}</a>` : esc(fuente)}</p>
        ${c !== 'desconocida' ? `<p><a class="boton secundario" href="#mapa/${encodeURIComponent(id)}">Ver en el mapa</a></p>` : ''}</section>
      ${l.nota ? `<h3>Nota</h3><p class="nota">${esc(l.nota)}</p>` : ''}`;
    mostrar(fichaDlg);
    fichaDlg.querySelector('.dialogo-cuerpo').scrollTop = 0;
    montarMapas(fichaDlg);
  }

  function vistaMapa(args) {
    const todos = D.lugares || [];
    if (args && args[0]) estado.mapaSel = args[0];
    const caps = D.capitulos || [], ps = N.pasajes(D);
    const f = estado.mapaFiltro;
    let ids = todos.map(l => l.id);
    if (f.startsWith('cap-')) { const cap = +f.slice(4), c = caps.find(x => x.cap === cap); ids = c ? N.lugaresDeRefs(D, (c.versiculos || []).map(v => `Gn ${cap}:${v.n}`)) : []; }
    else if (f.startsWith('p-')) ids = N.lugaresDePasaje(D, ps.find(p => p.id === f.slice(2)));
    const ubic = ids.filter(id => { const c = N.confianzaLugar(N.lugar(D, id)); return c !== 'desconocida' && estado.mapaConf.has(c); });
    const desc = ids.filter(id => N.confianzaLugar(N.lugar(D, id)) === 'desconocida');
    const opt = (v, t) => `<option value="${esc(v)}"${f === v ? ' selected' : ''}>${esc(t)}</option>`;
    return `<h1 tabindex="-1">Mapa de los lugares</h1>
      <p class="sub">El nombre de cada lugar es texto bíblico; su ubicación es una identificación moderna con un grado de confianza. Lo que no se puede ubicar no se dibuja.</p>
      <div class="herr mapa-filtros">
        <div class="campo"><label for="f-ambito">Pasaje o capítulo</label><select id="f-ambito">${opt('', 'Todo Génesis 1–11')}
          <optgroup label="Capítulos">${caps.map(c => opt('cap-' + c.cap, `${c.libro || 'Génesis'} ${c.cap}`)).join('')}</optgroup>
          ${(D.pasajes || []).length ? `<optgroup label="Pasajes">${ps.map(p => opt('p-' + p.id, p.titulo)).join('')}</optgroup>` : ''}</select></div>
        <div class="campo"><label for="buscar-lugar">Buscar lugar</label><input id="buscar-lugar" type="search" autocomplete="off" placeholder="Nombre…" value="${esc(estado.mapaQ)}"></div>
        <fieldset class="conf-filtro"><legend>Confianza</legend>${['alta', 'media', 'baja'].map(c => `<label><input type="checkbox" data-conf="${c}" ${estado.mapaConf.has(c) ? 'checked' : ''}><span>${icoConf(c)}${c[0].toUpperCase() + c.slice(1)}</span></label>`).join('')}</fieldset>
      </div>
      <ul class="resultados" id="res-lugar" aria-live="polite">${resultadosLugar()}</ul>
      ${todos.length ? mapaHTML(ubic, { sel: ubic.includes(estado.mapaSel) ? estado.mapaSel : null }) : '<p class="vacio-txt">Los datos todavía no traen lugares. Cuando se publiquen, aparecerán aquí.</p>'}
      ${todos.length ? `<h2>En el mapa (${ubic.length})</h2>${ubic.length ? `<ul class="chips">${ubic.map(id => `<li>${btnLugar(id)}</li>`).join('')}</ul>` : '<p class="vacio-txt">Ningún lugar ubicado con este filtro.</p>'}
      <h2>Sin ubicación conocida (${desc.length})</h2>${desc.length ? `<ul class="lugares-lista">${desc.map(id => { const l = N.lugar(D, id); return `<li>${btnLugar(id)}<span class="contexto">Ubicación desconocida${l.nota ? ': ' + esc(l.nota) : ''}</span></li>`; }).join('')}</ul>` : '<p class="vacio-txt">Todos los lugares de este filtro tienen ubicación.</p>'}` : ''}`;
  }
  function resultadosLugar() {
    const q = N.norm(estado.mapaQ);
    if (!q) return '';
    const r = (D.lugares || []).filter(l => N.norm(l.nombre).includes(q) || N.norm(l.nombre_rv1909).includes(q)).slice(0, 20);
    return r.length ? r.map(l => `<li>${btnLugar(l.id)}</li>`).join('') : '<li class="meta">Sin resultados.</li>';
  }

  /* ---------- Navegación ---------- */
  function ruta() { const h = decodeURIComponent(location.hash.slice(1)) || 'leer'; const [vista, ...args] = h.split('/'); return { vista, args }; }
  const VISTAS = { leer: vistaLeer, arbol: vistaArbol, edades: vistaEdades, mapa: vistaMapa, fuentes: vistaFuentes };
  let primera = true;
  function render(foco) {
    if (!D) { main.innerHTML = '<h1>Sin datos</h1><p>No se encontró <code>datos/genesis.js</code>. Añade <code>?ejemplo</code> a la dirección para ver los datos de prueba.</p>'; return; }
    const { vista, args } = ruta();
    const fn = VISTAS[vista] || vistaLeer;
    main.innerHTML = fn(args);
    montarMapas(main);
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
    const lg = t.closest('[data-lugar]'); if (lg) { e.preventDefault(); cerrar(detDlg); abrirLugar(lg.dataset.lugar); return; }
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
    if (t.id === 'f-ambito') { estado.mapaFiltro = t.value; rerender('#f-ambito'); }
    else if (t.dataset && t.dataset.conf) { t.checked ? estado.mapaConf.add(t.dataset.conf) : estado.mapaConf.delete(t.dataset.conf); rerender(`[data-conf="${t.dataset.conf}"]`); }
    else if (t.name === 'trad') { estado.trad = t.value; store.set('biblia.trad', t.value); rerender(`input[name="trad"][value="${t.value}"]`); }
  });
  document.addEventListener('input', e => {
    if (e.target.id === 'buscar-lugar') { estado.mapaQ = e.target.value; const r = $('#res-lugar'); if (r) r.innerHTML = resultadosLugar(); }
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
    s.onload = () => { D = window.BIBLIA_DATOS || null; MAPA = window.BIBLIA_MAPA || null; iniciar(); };
    s.onerror = iniciar;
    document.head.appendChild(s);
  } else iniciar();
})();
