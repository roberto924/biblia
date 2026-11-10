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
    return { datos: d, personas, hijos, padres, conyuges, edades };
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
    const rec = (id, vinculos) => {
      const n = { id, vinculos, hijos: [] };
      for (const r of hijosDe(d, id)) {
        if (visit.has(r.a)) continue;
        visit.add(r.a);
        n.hijos.push(rec(r.a, (I.padres.get(r.a) || []).filter(x => x.de === id)));
      }
      return n;
    };
    return rec(raiz, []);
  }

  // Bosque: Adán primero, luego otras raíces (sin padres conocidos) no alcanzadas.
  function construirBosque(d) {
    const I = indice(d), visit = new Set(), raices = [];
    const a = idAdan(d);
    if (a) raices.push(construirArbol(d, a, visit));
    const cands = [...I.personas.values()].filter(p => !(I.padres.get(p.id) || []).length && hijosDe(d, p.id).length);
    cands.sort((x, y) => (I.conyuges.has(x.id) ? 1 : 0) - (I.conyuges.has(y.id) ? 1 : 0));
    for (const p of cands) {
      if (visit.has(p.id)) continue;
      const cony = I.conyuges.get(p.id) || [];
      if (cony.some(c => visit.has(c.otro)) && hijosDe(d, p.id).every(h => visit.has(h.a))) continue;
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

  return { TRADS, TIPOS, norm, parseRef, claseCerteza, indice, persona, hijosDe, encontrar, idAdan, idAbraham,
    construirArbol, construirBosque, rutas, tradicionesDe, presenteEn, lineaPorTradicion, fusionarOrden,
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
  const estado = { trad: store.get('biblia.trad', 'TM'), lineaSolo: false, plegados: new Set(), q: '' };

  const nombre = id => { const p = N.persona(D, id); return p ? (p.nombre || id) : id; };
  const refHTML = ref => { const r = N.parseRef(ref); return r ? `<a class="ref" href="#leer/${r.cap}${r.v ? '/' + r.v : ''}">${esc(ref)}</a>` : esc(ref); };
  const insignia = (cert, ref) => { const k = N.claseCerteza(cert); return `<span class="insignia ${k}" title="${CERT_DESC[k]}">${CERT_TXT[k]}${ref ? ' · ' + refHTML(ref) : ''}</span>`; };
  const btnPersona = id => `<button type="button" class="persona-btn" data-persona="${esc(id)}">${esc(nombre(id))}</button>`;
  const fuenteNombre = id => { const f = (D.fuentes || []).find(x => x.id === id); return f ? f.nombre : (id || 'sin fuente'); };
  const etiquetaTrad = id => { const t = [...N.tradicionesDe(D, id)]; return t.length === 1 ? `<span class="etiqueta">solo ${esc(t[0])}</span>` : ''; };
  const leidos = () => new Set(store.get('biblia.leidos', []));

  /* ---------- Leer ---------- */
  function vistaLeer(args) {
    const caps = D.capitulos || [];
    if (args[0]) return vistaCapitulo(+args[0], +args[1] || null);
    const L = leidos(), n = caps.filter(c => L.has(c.cap)).length;
    return `<h1 tabindex="-1">Plan de lectura</h1>
      <p class="sub">${esc((caps[0] && caps[0].libro) || 'Génesis')} ${caps.length ? caps[0].cap + '–' + caps[caps.length - 1].cap : ''}: un capítulo por sesión.</p>
      <div class="progreso"><progress max="${caps.length || 1}" value="${n}" aria-label="Progreso de lectura"></progress><span>${n} de ${caps.length} capítulos leídos</span></div>
      <ol class="plan">${caps.map(c => `<li class="${L.has(c.cap) ? 'leido' : ''}">
        <a href="#leer/${c.cap}"><span class="plan-titulo">${esc(c.libro)} ${c.cap}</span><span class="meta">${(c.versiculos || []).length} versículos</span></a>
        <label class="marca"><input type="checkbox" data-leido="${c.cap}" ${L.has(c.cap) ? 'checked' : ''}><span class="sr">Marcar ${esc(c.libro)} ${c.cap} como leído</span></label></li>`).join('')}</ol>`;
  }

  function vistaCapitulo(cap, v) {
    const caps = D.capitulos || [];
    const i = caps.findIndex(c => c.cap === cap), c = caps[i];
    if (!c) return `<h1 tabindex="-1">Génesis ${esc(cap)}</h1><p>Este capítulo no está en el piloto (Génesis 1–11).</p><p><a href="#leer">← Volver al plan</a></p>`;
    const leido = leidos().has(cap);
    const pers = N.personasEnCapitulo(D, cap);
    const fuente = c.fuente || ((D.fuentes || []).find(f => /rv/i.test(f.id)) || {}).id;
    const prev = caps[i - 1], next = caps[i + 1];
    return `<div class="capitulo"><article class="lectura">
      <header class="cab-cap"><a class="volver" href="#leer">← Plan</a><h1 tabindex="-1">${esc(c.libro)} ${cap}</h1>
        <button type="button" class="boton" data-toggle-leido="${cap}" aria-pressed="${leido}">${leido ? '✓ Leído' : 'Marcar como leído'}</button></header>
      <div class="biblia">${(c.versiculos || []).map(x => `<span class="vers" id="v${cap}-${x.n}"><sup class="vn">${esc(x.n)}</sup>${esc(x.texto)} </span>`).join('')}</div>
      ${fuente ? `<p class="meta">Texto: ${esc(fuenteNombre(fuente))}</p>` : ''}
      <nav class="pasos-cap" aria-label="Capítulos">${prev ? `<a class="boton" href="#leer/${prev.cap}">← ${esc(prev.libro)} ${prev.cap}</a>` : '<span></span>'}${next ? `<a class="boton" href="#leer/${next.cap}">${esc(next.libro)} ${next.cap} →</a>` : ''}</nav>
    </article>
    <aside class="en-cap" aria-labelledby="pc"><h2 id="pc">Personas en este capítulo</h2>
      ${pers.length ? `<ul class="chips">${pers.map(p => `<li>${btnPersona(p.id)}<span class="meta">v. ${p.versos.filter(Boolean).join(', ')}</span></li>`).join('')}</ul>` : '<p class="meta">Ninguna registrada.</p>'}
    </aside></div>`;
  }

  /* ---------- Árbol ---------- */
  function vistaArbol() {
    return `<h1 tabindex="-1">Árbol genealógico</h1>
      <p class="sub">Cada vínculo indica si <span class="insignia texto">Texto</span> lo dice explícitamente o es <span class="insignia inferido">Inferido</span>, con su versículo.</p>
      <div class="herr">
        <div class="campo"><label for="buscar">Buscar persona</label><input id="buscar" type="search" autocomplete="off" placeholder="Nombre…" value="${esc(estado.q)}"></div>
        <button type="button" class="boton" id="btn-linea" aria-pressed="${estado.lineaSolo}">${estado.lineaSolo ? 'Mostrar todo el árbol' : 'Línea de Adán a Abraham'}</button>
        ${estado.lineaSolo ? '' : '<button type="button" class="boton secundario" id="btn-plegar">Plegar todo</button><button type="button" class="boton secundario" id="btn-desplegar">Desplegar todo</button>'}
      </div>
      <ul class="resultados" id="resultados" aria-live="polite">${resultadosHTML()}</ul>
      <div id="arbol">${arbolHTML()}</div>`;
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
      filas.push(`<li class="fila${linea.has(n.id) ? ' en-linea' : ''}" style="--n:${Math.min(prof, 14)}">
        <span class="gen" title="Generación ${prof + 1}">${prof + 1}</span>
        ${hijos.length ? `<button type="button" class="plegar" data-plegar="${esc(n.id)}" aria-expanded="${!pleg}" aria-label="${pleg ? 'Desplegar' : 'Plegar'} descendencia de ${esc(nombre(n.id))}">${pleg ? '▸' : '▾'}</button>` : '<span class="plegar vacio" aria-hidden="true"></span>'}
        <span class="fila-cont">${btnPersona(n.id)}${etiquetaTrad(n.id)}${n.vinculos.map(r => insignia(r.certeza, r.ref)).join('')}${pleg ? `<span class="meta">(${hijos.length} hijos)</span>` : ''}</span></li>`);
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
    return `<h3>${trad === 'TM' ? 'Texto Masorético (TM)' : 'Septuaginta (LXX)'}</h3>
      <ol class="barras">${filas.map(f => `<li><button type="button" class="barra-fila" data-calc="${trad}|${esc(f.id)}">
        <span class="barra-nombre">${esc(nombre(f.id))}</span><span class="barra-anos">${f.nacimiento}–${f.muerte !== null ? f.muerte : '?'}</span>
        <span class="pista" aria-hidden="true"><span class="barra${f.muerte === null ? ' abierta' : ''}" style="left:${pct(f.nacimiento)};width:${f.muerte !== null ? pct(f.muerte - f.nacimiento) : '4px'}"></span></span></button></li>`).join('')}</ol>
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
    const padres = (I.padres.get(id) || []).map(r => `<li>${btnPersona(r.de)} <span class="meta">${r.tipo}</span> ${insignia(r.certeza, r.ref)}${r.nota ? `<p class="nota">${esc(r.nota)}</p>` : ''}</li>`);
    const cony = (I.conyuges.get(id) || []).map(r => `<li>${btnPersona(r.otro)} ${insignia(r.certeza, r.ref)}${r.nota ? `<p class="nota">${esc(r.nota)}</p>` : ''}</li>`);
    const hijos = N.hijosDe(D, id).map(r => `<li>${btnPersona(r.a)} ${insignia(r.certeza, r.ref)}${r.nota ? `<p class="nota">${esc(r.nota)}</p>` : ''}</li>`);
    const tieneEdades = N.TIPOS.some(t => N.TRADS.some(tr => N.edad(D, id, t, tr)));
    const dif = N.diferencias(D, id);
    const edades = tieneEdades ? `<table class="edades mini"><thead><tr><th scope="col"></th><th scope="col">TM</th><th scope="col">LXX</th></tr></thead><tbody>${N.TIPOS.map(t => `<tr><th scope="row">${TIPO_TXT[t]}</th>${N.TRADS.map(tr => celda(id, t, tr, dif[t])).join('')}</tr>`).join('')}</tbody></table>` : '<p class="meta">Sin edades registradas.</p>';
    const refs = [...new Set([].concat(p.primera_ref ? [p.primera_ref] : [], p.refs || []))];
    fichaDlg.querySelector('h2').textContent = p.nombre || id;
    fichaDlg.querySelector('.dialogo-cuerpo').innerHTML = `
      <p class="meta">${p.sexo === 'm' ? 'Varón' : p.sexo === 'f' ? 'Mujer' : 'Sexo no indicado'}${p.primera_ref ? ' · aparece en ' + refHTML(p.primera_ref) : ''} ${etiquetaTrad(id)}</p>
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
    if (vista === 'leer' && args[1]) {
      const el = document.getElementById(`v${+args[0]}-${+args[1]}`);
      if (el) { el.classList.add('destacado'); el.scrollIntoView({ block: 'center' }); }
    } else if (foco !== false && !primera) { window.scrollTo(0, 0); }
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
    const tl = t.closest('[data-toggle-leido]'); if (tl) { toggleLeido(+tl.dataset.toggleLeido); rerender('[data-toggle-leido]'); return; }
    if (t.closest('#btn-linea')) { estado.lineaSolo = !estado.lineaSolo; rerender('#btn-linea'); return; }
    if (t.closest('#btn-plegar')) { N.construirBosque(D).forEach(function r(n) { if (n.hijos.length) estado.plegados.add(n.id); n.hijos.forEach(r); }); rerender('#btn-plegar'); return; }
    if (t.closest('#btn-desplegar')) { estado.plegados.clear(); rerender('#btn-desplegar'); return; }
  });
  document.addEventListener('change', e => {
    const t = e.target;
    if (t.dataset && t.dataset.leido) { toggleLeido(+t.dataset.leido); rerender(`[data-leido="${t.dataset.leido}"]`); }
    else if (t.name === 'trad') { estado.trad = t.value; store.set('biblia.trad', t.value); rerender(`input[name="trad"][value="${t.value}"]`); }
  });
  document.addEventListener('input', e => {
    if (e.target.id === 'buscar') { estado.q = e.target.value; const r = $('#resultados'); if (r) r.innerHTML = resultadosHTML(); }
  });
  function toggleLeido(cap) { const L = leidos(); L.has(cap) ? L.delete(cap) : L.add(cap); store.set('biblia.leidos', [...L]); }

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
