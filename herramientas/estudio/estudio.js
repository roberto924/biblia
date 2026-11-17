/* Estudio · Biblia narrada — página local (no se publica) para ver, revisar, editar los prompts y generar las
   imágenes de los guiones. Habla solo con herramientas/estudio.py (misma página, sin CORS); toda generación pasa
   por capa-ia en el servidor. Sin dependencias ni build. */
'use strict';
(() => {
  // Estimación del lote del 16-nov (≈ 0,2 % de la semana de Codex por imagen); capa-ia mide el gasto real.
  const COSTO_IMAGEN = 0.2;
  const VISTAS = { resumen: 'Resumen', estilo: 'Estilo', personajes: 'Personajes', escenarios: 'Escenarios', tomas: 'Tomas', cola: 'Cola y registro' };
  const GRUPOS = [['estilo', 'Estilo (láminas patrón)'], ['personajes', 'Personajes'], ['escenarios', 'Escenarios'], ['tomas', 'Tomas']];
  const PAGINA = 50;

  let datos = null;      // /api/datos
  let estado = null;     // /api/estado
  let lote = null;       // /api/lote
  let vista = 'resumen';
  let destino = null;    // id de la tarjeta a mostrar (#ver=<id>)
  let errorCarga = null;
  let verTrabajos = PAGINA;
  let sondeo = null;
  const plegado = new Map(); // clave de <details> → abierto (true/false) elegido por el usuario

  const $ = (sel) => document.querySelector(sel);
  const main = $('#principal');

  // ------------------------------------------------------------------ utilidades
  /** Crea un elemento: h('p', {class: 'x', onclick: f}, 'texto', otroNodo, [más]). Nunca usa innerHTML. */
  function h(tag, attrs, ...hijos) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
      else if (k === 'class') el.className = v;
      else if (v === true) el.setAttribute(k, '');
      else el.setAttribute(k, String(v));
    }
    const poner = (x) => {
      if (x == null || x === false) return;
      if (Array.isArray(x)) x.forEach(poner);
      else el.append(x instanceof Node ? x : document.createTextNode(String(x)));
    };
    hijos.forEach(poner);
    return el;
  }

  const num = (x, dec = 2) => (typeof x === 'number' ? x.toLocaleString('es', { maximumFractionDigits: dec }) : '—');
  const pct = (x) => (typeof x === 'number' ? `${num(x)} %` : '—');
  const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

  /** ISO (con zona, o sin ella = hora local) → «vie 21 nov, 18:49» en hora local. */
  function fecha(s, conHora = true) {
    if (!s) return '—';
    const d = new Date(s);
    if (Number.isNaN(d.getTime())) return String(s);
    const op = { weekday: 'short', day: 'numeric', month: 'short' };
    if (conHora) Object.assign(op, { hour: '2-digit', minute: '2-digit' });
    return d.toLocaleString('es', op);
  }
  const hora = (s) => { const d = new Date(s); return Number.isNaN(d.getTime()) ? '—' : d.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' }); };
  /** «codex directo (2026-11-16)» → «codex directo (16-nov)». */
  const origen = (s) => String(s).replace(/\((\d{4})-(\d{2})-(\d{2})\)/, (_, a, m, d) => `(${Number(d)}-${MESES[Number(m) - 1]})`);

  function mensaje(texto, tipo = 'ok', extra = null) {
    const caja = h('div', { class: `mensaje ${tipo}`, role: tipo === 'error' ? 'alert' : null },
      h('div', null, h('p', null, texto), extra),
      h('button', { type: 'button', class: 'boton secundario chico', onclick: () => caja.remove() }, 'Cerrar'));
    $('#mensajes').append(caja);
    if (tipo !== 'error') setTimeout(() => caja.remove(), 9000);
  }

  /** GET (sin cuerpo) o POST JSON a la API. Nunca lanza: {ok, status, datos}. */
  async function api(ruta, cuerpo) {
    const op = cuerpo === undefined ? { cache: 'no-store' }
      : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cuerpo) };
    let r;
    try { r = await fetch(ruta, op); } catch (e) {
      return { ok: false, status: 0, datos: { error: 'No hay conexión con el servidor del Estudio (¿sigue corriendo herramientas/estudio.py?).' } };
    }
    let d;
    try { d = await r.json(); } catch (e) { d = { error: `Respuesta inesperada del servidor (HTTP ${r.status}).` }; }
    return { ok: r.ok, status: r.status, datos: d || {} };
  }
  const errorDe = (r) => {
    const d = r.datos || {};
    const lista = Array.isArray(d.errores) && d.errores.length ? d.errores : [d.error || `HTTP ${r.status}`];
    return lista.map(String);
  };

  // ------------------------------------------------------------------ datos derivados
  function todos() {
    if (!datos) return [];
    const tomas = [];
    for (const p of datos.pasajes || []) for (const e of p.escenas) for (const t of e.tomas) tomas.push(t);
    return [...(datos.laminas || []), ...(datos.personajes || []), ...(datos.escenarios || []), ...tomas];
  }
  const porId = () => new Map(todos().map((x) => [x.id, x]));
  const delGrupo = (g) => todos().filter((x) => x.grupo === g);
  const vistaDe = (it) => (it.grupo === 'estilo' ? 'estilo' : it.grupo);

  /** Estado visible de una tarjeta: sin imagen / bloqueada / pendiente / aprobada / rechazada / cambiada. */
  function estadoDe(it) {
    if (!it.imagen) return it.bloqueo ? 'bloqueada' : 'sin-imagen';
    return it.revision?.estado || 'pendiente';
  }
  const TEXTO_ESTADO = {
    'sin-imagen': 'Sin imagen', bloqueada: 'Bloqueada', pendiente: 'Pendiente de revisar',
    aprobada: 'Aprobada', rechazada: 'Rechazada', cambiada: 'Cambió: revisar de nuevo',
  };

  function conteos(lista) {
    const c = { total: lista.length, porGenerar: 0, bloqueadas: 0, generadas: 0, pendiente: 0, aprobada: 0, rechazada: 0, cambiada: 0 };
    for (const it of lista) {
      if (!it.imagen) { c.porGenerar++; if (it.bloqueo) c.bloqueadas++; continue; }
      c.generadas++;
      const e = it.revision?.estado || 'pendiente';
      if (e in c) c[e]++;
    }
    return c;
  }

  /** Todas las filas del historial (capa-ia y la vieja del 16-nov), la más reciente primero. */
  function trabajos() {
    const filas = [];
    for (const it of todos()) for (const f of it.historial || []) filas.push({ ...f, _item: it });
    return filas.sort((a, b) => String(b.fecha || '').localeCompare(String(a.fecha || '')));
  }

  const loteEnCurso = () => Boolean(lote && lote.en_curso);

  // ------------------------------------------------------------------ carga y sondeo
  async function cargar() {
    const [d, e, l] = await Promise.all([api('/api/datos'), api('/api/estado'), api('/api/lote')]);
    if (d.ok) { datos = d.datos; errorCarga = null; } else errorCarga = errorDe(d).join(' ');
    if (e.ok) estado = e.datos; else estado = { aviso: `No se pudo leer el estado: ${errorDe(e).join(' ')}` };
    if (l.ok) lote = l.datos;
    pintarCabecera();
    pintar();
    if (loteEnCurso()) empezarSondeo();
  }

  async function recargarDatos() {
    const d = await api('/api/datos');
    if (d.ok) { datos = d.datos; errorCarga = null; } else mensaje(`No se pudieron recargar los datos: ${errorDe(d).join(' ')}`, 'error');
    pintar();
  }

  async function recargarEstado() {
    const e = await api('/api/estado');
    if (e.ok) estado = e.datos;
    pintarCabecera();
  }

  function empezarSondeo() {
    if (sondeo) return;
    let hechas = lote?.hechas?.length || 0;
    sondeo = setInterval(async () => {
      const r = await api('/api/lote');
      if (!r.ok) return;
      const antes = loteEnCurso();
      const cambio = JSON.stringify(r.datos) !== JSON.stringify(lote);
      lote = r.datos;
      const n = lote.hechas?.length || 0;
      if (n !== hechas) { hechas = n; await recargarDatos(); }
      // solo se vuelve a pintar si el lote cambió: no se pierde la selección ni el puntero cada 2 s
      if (cambio) { pintarCabecera(); if (vista === 'cola' || vista === 'resumen') pintar(); }
      if (antes && !lote.en_curso) {
        clearInterval(sondeo); sondeo = null;
        await recargarDatos();
        await recargarEstado();
        const p = textoParada(lote);
        mensaje(`Lote terminado. ${p.texto}`, p.mal ? 'error' : 'ok');
      }
    }, 2000);
  }

  // ------------------------------------------------------------------ cabecera
  function pintarCabecera() {
    const caja = $('#estado-capa');
    const partes = [];
    const e = estado || {};
    const c = e.cuota;
    if (c) {
      partes.push(h('span', null, 'Codex: semana ', h('b', null, pct(c.semanal_pct)),
        c.semanal_reinicio_en ? ` (reinicia ${fecha(c.semanal_reinicio_en)})` : ''));
      partes.push(h('span', null, '5 h: ', h('b', null, pct(c.usado_pct)), c.reinicio_en ? ` (reinicia ${hora(c.reinicio_en)})` : ''));
    } else partes.push(h('span', null, 'Codex: cuota sin leer'));
    const tope = e.tope_biblia_pct ?? 30;
    const gasto = e.gasto_biblia_semana_pct;
    partes.push(h('span', { class: typeof gasto === 'number' && gasto >= tope ? 'tope-pasado' : null },
      'Biblia esta semana ', h('b', null, typeof gasto === 'number' ? `≈ ${pct(gasto)}` : 'sin dato'), ` de su tope ${pct(tope)}`));
    partes.push(h('span', null, 'capa-ia: ', h('b', null, e.capa === 'http' ? 'servidor (http)' : e.capa === 'cli' ? 'CLI' : (e.capa || '—'))));
    if (e.generar === false) partes.push(h('span', null, h('b', null, 'generar desactivado')));
    if (loteEnCurso()) partes.push(h('span', null, h('b', null, `Generando${lote.actual ? `: ${lote.actual.id}` : '…'}`)));
    caja.replaceChildren(...partes.flatMap((p, i) => (i ? [h('span', { class: 'sep', 'aria-hidden': 'true' }, '·'), p] : [p])));
    const avisos = [e.aviso, datos?.aviso].filter(Boolean);
    const av = $('#aviso-capa');
    av.hidden = !avisos.length;
    av.textContent = avisos.length ? `Aviso: ${avisos.join(' ')}` : '';
  }

  // ------------------------------------------------------------------ vistas
  function ruta() {
    const hsh = decodeURIComponent(location.hash.slice(1));
    destino = null;
    if (hsh.startsWith('ver=')) {
      destino = hsh.slice(4);
      const it = porId().get(destino);
      vista = it ? vistaDe(it) : (destino.split('/')[0] in VISTAS ? destino.split('/')[0] : 'tomas');
    } else vista = hsh in VISTAS ? hsh : 'resumen';
  }

  function pintar() {
    // conservar foco
    const activo = document.activeElement;
    const clave = activo && main.contains(activo) ? activo.dataset.k : null;
    for (const a of document.querySelectorAll('.pestanas a')) {
      if (a.dataset.vista === vista) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    }
    document.title = `${VISTAS[vista]} · Estudio · Biblia narrada`;
    let contenido;
    if (errorCarga && !datos) {
      contenido = [h('h2', null, 'No se pudieron cargar los datos'), h('p', { class: 'errores' }, errorCarga),
        h('button', { type: 'button', class: 'boton', onclick: cargar }, 'Reintentar')];
    } else if (!datos) contenido = [h('p', { class: 'vacio-txt' }, 'Cargando los datos del Estudio…')];
    else contenido = ({ resumen: vResumen, estilo: () => vGrupo('estilo'), personajes: () => vGrupo('personajes'),
      escenarios: () => vGrupo('escenarios'), tomas: vTomas, cola: vCola })[vista]();
    main.replaceChildren(...[contenido].flat(Infinity).filter((x) => x != null && x !== false));
    if (clave) {
      const el = main.querySelector(`[data-k="${CSS.escape(clave)}"]`);
      if (el) el.focus({ preventScroll: true });
    }
  }

  function irADestino() {
    if (!destino) return;
    const el = document.getElementById(`card-${destino}`);
    if (!el) return;
    for (let d = el.parentElement?.closest('details'); d; d = d.parentElement?.closest('details')) d.open = true;
    el.scrollIntoView({ block: 'start' });
    const t = el.querySelector('h3');
    if (t) t.focus({ preventScroll: true });
  }

  /** <details> que recuerda si el usuario lo abrió o cerró (las vistas se vuelven a pintar). */
  function desplegable(clave, resumen, cuerpo, { abierto = false, clase = 'desplegable' } = {}) {
    const d = h('details', { class: clase, 'data-k': clave }, h('summary', { 'data-k': `${clave}|s` }, resumen), cuerpo);
    d.open = plegado.has(clave) ? plegado.get(clave) : abierto;
    d.addEventListener('toggle', () => plegado.set(clave, d.open));
    return d;
  }

  function figura(src, ancho, alto, alt, pie) {
    const rotulo = datos?.estilo?.rotulo_ia || 'Ilustración moderna (generada con IA)';
    return h('figure', { class: 'figura' },
      h('a', { href: src, target: '_blank', rel: 'noopener' },
        h('img', { src, alt, loading: 'lazy', decoding: 'async', width: ancho || null, height: alto || null })),
      h('figcaption', null, rotulo, pie ? ` · ${pie}` : ''));
  }

  function botonesGenerar(lista, { global = false } = {}) {
    const sinImagen = lista.filter((x) => !x.imagen);
    const listas = sinImagen.filter((x) => !x.bloqueo);
    const ocupado = loteEnCurso();
    const n = global ? sinImagen.length : listas.length;
    const titulo = ocupado ? 'Hay un lote en curso' : null;
    const botones = [h('button', {
      type: 'button', class: 'boton', disabled: ocupado || !n, title: titulo, 'data-k': `gen-pend-${global ? 'todo' : lista[0]?.grupo}`,
      onclick: () => confirmarLote(global ? { n } : { ids: listas.map((x) => x.id) }, n, global),
    }, `Generar pendientes (${n})`)];
    if (global) {
      botones.push(h('button', {
        type: 'button', class: 'boton secundario', disabled: ocupado || !n, title: titulo, 'data-k': 'gen-1',
        onclick: () => confirmarLote({ n: 1 }, 1, true),
      }, 'Generar 1'));
    }
    return h('div', { class: 'acciones' }, botones);
  }

  function vResumen() {
    const filas = GRUPOS.map(([g, nombre]) => [nombre, conteos(delGrupo(g))]);
    const total = conteos(todos());
    const celdas = (c) => [c.total, c.porGenerar, c.bloqueadas, c.generadas, c.pendiente, c.aprobada, c.rechazada, c.cambiada]
      .map((x) => h('td', { class: 'num' }, x));
    const cab = ['Total', 'Por generar', 'de ellas bloqueadas', 'Generadas', 'Sin revisar', 'Aprobadas', 'Rechazadas', 'Cambiadas'];
    const ultimos = trabajos().slice(0, 10);
    return [
      h('div', { class: 'barra' }, h('h2', null, 'Resumen'), botonesGenerar(todos(), { global: true })),
      h('p', { class: 'meta' }, `«Generar pendientes» genera de una en una, en orden láminas → hojas → tomas (las bloqueadas entran cuando se hace su hoja), y para en el primer fallo, al acabarse la cuota o al llegar al tope de la Biblia. Cada imagen gasta ~${num(COSTO_IMAGEN)} % de la semana de Codex.`),
      loteBreve(),
      h('div', { class: 'tabla-env', tabindex: '0', role: 'region', 'aria-label': 'Conteos por grupo' },
        h('table', null,
          h('caption', { class: 'sr' }, 'Imágenes por grupo y estado de revisión'),
          h('thead', null, h('tr', null, h('th', { scope: 'col' }, 'Grupo'), cab.map((x) => h('th', { scope: 'col', class: 'num' }, x)))),
          h('tbody', null, filas.map(([n, c]) => h('tr', null, h('th', { scope: 'row' }, n), celdas(c)))),
          h('tfoot', null, h('tr', null, h('th', { scope: 'row' }, 'Todo'), celdas(total))))),
      h('h2', null, 'Últimos trabajos'),
      ultimos.length ? h('ul', { class: 'lista-trabajos' }, ultimos.map((f, i) => filaTrabajo(f, `res-${i}`, true, false)))
        : h('p', { class: 'vacio-txt' }, 'Todavía no hay trabajos en el registro.'),
      h('p', null, h('a', { href: '#cola' }, 'Ver la cola y el registro completo')),
    ];
  }

  function vGrupo(g) {
    const lista = delGrupo(g);
    const c = conteos(lista);
    const titulo = GRUPOS.find((x) => x[0] === g)[1];
    return [
      h('div', { class: 'barra' }, h('h2', null, titulo), botonesGenerar(lista)),
      h('p', { class: 'meta' }, `${c.total} en total · ${c.generadas} con imagen · ${c.aprobada} aprobadas · ${c.rechazada} rechazadas · ${c.pendiente + c.cambiada} por revisar · ${c.porGenerar} sin imagen${c.bloqueadas ? ` (${c.bloqueadas} bloqueadas)` : ''}.`),
      lista.length ? h('div', { class: 'tarjetas' }, lista.map(tarjeta)) : h('p', { class: 'vacio-txt' }, 'No hay nada en este grupo.'),
    ];
  }

  function vTomas() {
    const lista = delGrupo('tomas');
    const libros = new Map();
    for (const p of datos.pasajes || []) {
      if (!libros.has(p.libro)) libros.set(p.libro, []);
      libros.get(p.libro).push(p);
    }
    const nTomas = (p) => p.escenas.reduce((s, e) => s + e.tomas.length, 0);
    const nCon = (p) => p.escenas.reduce((s, e) => s + e.tomas.filter((t) => t.imagen).length, 0);
    return [
      h('div', { class: 'barra' }, h('h2', null, 'Tomas'), botonesGenerar(lista)),
      h('p', { class: 'meta' }, 'Por libro → pasaje → escena → toma. Una toma queda bloqueada hasta que existen las hojas de sus personajes y su escenario.'),
      libros.size ? [...libros].map(([libro, pasajes]) => desplegable(`libro-${libro}`,
        [libro, h('span', { class: 'meta' }, `${pasajes.length} pasaje${pasajes.length === 1 ? '' : 's'}`)],
        pasajes.map((p) => desplegable(`pasaje-${p.id}`,
          [`${p.id} · ${p.titulo}`, h('span', { class: 'meta' }, `${nTomas(p)} tomas · ${nCon(p)} con imagen`)],
          p.escenas.map((e) => h('section', { class: 'escena' },
            h('h4', null, `Escena ${e.id}${e.titulo ? `: ${e.titulo}` : ''}`),
            h('div', { class: 'tarjetas' }, e.tomas.map(tarjeta)))),
          { abierto: true, clase: 'desplegable pasaje' })),
        { abierto: true, clase: 'desplegable libro' }))
        : h('p', { class: 'vacio-txt' }, 'No hay guiones con tomas.'),
    ];
  }

  function vCola() {
    const filas = trabajos();
    return [
      h('h2', null, 'Lote'),
      loteDetalle(),
      h('h2', null, `Registro de trabajos (${filas.length})`),
      h('p', { class: 'meta' }, 'Del registro de capa-ia (app biblia) y las filas del 16-nov, que se hicieron con Codex directo. La más reciente primero.'),
      filas.length ? h('ul', { class: 'lista-trabajos' }, filas.slice(0, verTrabajos).map((f, i) => filaTrabajo(f, `cola-${i}`, true)))
        : h('p', { class: 'vacio-txt' }, 'Todavía no hay trabajos en el registro.'),
      filas.length > verTrabajos ? h('button', {
        type: 'button', class: 'boton secundario', 'data-k': 'mas-trabajos',
        onclick: () => { verTrabajos += PAGINA; pintar(); },
      }, `Mostrar ${Math.min(PAGINA, filas.length - verTrabajos)} más`) : null,
    ];
  }

  // ------------------------------------------------------------------ lote
  function textoParada(l) {
    const ultimo = [...(l.hechas || [])].reverse().find((x) => x.estado !== 'saltado') || {};
    switch (l.parado_por) {
      case 'terminado': return { texto: 'Terminado: no quedaba nada más que hacer en el lote.' };
      case 'detenido': return { texto: 'Detenido a petición, tras la imagen en curso.' };
      case 'esperando_cuota': {
        const r = ultimo.reinicio_en || estado?.cuota?.semanal_reinicio_en;
        return { mal: true, texto: `Parado: esperando cuota de Codex${r ? `; reinicia ${fecha(r)}` : ''}. No se reintenta solo.${ultimo.motivo ? ` (${ultimo.motivo})` : ''}` };
      }
      case 'bloqueado_coste': return { mal: true, texto: `Parado: el tope de gasto de la Biblia (${pct(estado?.tope_biblia_pct ?? 30)} de la semana) no deja seguir.${ultimo.motivo ? ` (${ultimo.motivo})` : ''}` };
      case 'fallo': return { mal: true, texto: `Parado por un fallo${ultimo.id ? ` en ${ultimo.id}` : ''}: ${ultimo.motivo || 'sin motivo'}.` };
      default: return { texto: l.parado_por ? `Parado: ${l.parado_por}.` : '' };
    }
  }

  function loteBreve() {
    if (!lote || (!lote.en_curso && !lote.parado_por)) return null;
    if (lote.en_curso) {
      return h('p', { class: 'lote' }, h('strong', null, 'Lote en curso: '),
        lote.actual ? `generando ${lote.actual.id} desde las ${hora(lote.actual.desde)}` : 'preparando la siguiente imagen',
        ` · ${lote.hechas.length} hecha${lote.hechas.length === 1 ? '' : 's'}. `, h('a', { href: '#cola' }, 'Ver la cola'));
    }
    const p = textoParada(lote);
    return h('p', { class: 'lote' }, h('strong', null, 'Último lote: '), h('span', { class: `parada${p.mal ? ' mal' : ''}` }, p.texto),
      ` ${lote.hechas.length} resultado${lote.hechas.length === 1 ? '' : 's'}. `, h('a', { href: '#cola' }, 'Ver la cola'));
  }

  function loteDetalle() {
    const l = lote || { en_curso: false, hechas: [] };
    const p = textoParada(l);
    const contenido = [];
    if (l.en_curso) {
      contenido.push(h('p', null, h('strong', null, 'En curso. '),
        l.actual ? ['Ahora: ', h('a', { href: `#ver=${l.actual.id}` }, l.actual.id), ` (desde las ${hora(l.actual.desde)})`] : 'Preparando la siguiente imagen…'));
    } else if (l.parado_por) contenido.push(h('p', { class: `parada${p.mal ? ' mal' : ''}` }, p.texto));
    else contenido.push(h('p', { class: 'vacio-txt' }, 'No se ha lanzado ningún lote desde que arrancó el Estudio.'));
    contenido.push(h('div', { class: 'acciones' }, h('button', {
      type: 'button', class: 'boton peligro', disabled: !l.en_curso, 'data-k': 'detener', onclick: detener,
    }, 'Detener tras la actual')));
    contenido.push(h('p', { class: 'nota-regenerar' },
      'La imagen en curso siempre termina (capa-ia no deja cortarla) y no se empieza otra. Ojo con «Regenerar»: si detienes justo cuando empieza, la imagen anterior puede quedar ya apartada en «versiones anteriores» (guiones/imagenes/_anteriores/) sin que se pida la nueva; la tarjeta queda sin imagen y la anterior sigue en sus versiones anteriores.'));
    if (l.hechas?.length) {
      contenido.push(h('h3', null, `Resultados de este lote (${l.hechas.length})`));
      contenido.push(h('ul', { class: 'historial' }, l.hechas.map((x) => h('li', null,
        h('a', { href: `#ver=${x.id}` }, x.id || '—'), ` · ${x.estado || '—'}`,
        x.proveedor ? ` · ${x.proveedor}` : '', typeof x.segundos === 'number' ? ` · ${num(x.segundos, 0)} s` : '',
        cuotaTexto(x) ? ` · ${cuotaTexto(x)}` : '', x.motivo ? ` · ${x.motivo}` : '',
        x.reinicio_en ? ` · reinicia ${fecha(x.reinicio_en)}` : ''))));
    }
    return h('div', { class: 'lote' }, contenido);
  }

  async function detener() {
    const r = await api('/api/lote/detener', {});
    if (!r.ok) { mensaje(`No se pudo detener: ${errorDe(r).join(' ')}`, 'error'); return; }
    mensaje(r.datos.en_curso ? 'Se detendrá cuando termine la imagen en curso.' : 'No había ningún lote en curso.');
    const l = await api('/api/lote');
    if (l.ok) lote = l.datos;
    pintar();
  }

  async function lanzar(cuerpo) {
    const r = await api('/api/generar', cuerpo);
    if (r.status !== 202) return errorDe(r);
    lote = r.datos.lote || { en_curso: true, hechas: [] };
    mensaje('Lote iniciado: se genera de una en una. Puedes seguir revisando mientras tanto.');
    pintarCabecera();
    pintar();
    empezarSondeo();
    return null;
  }

  function confirmarLote(cuerpo, n, global) {
    const tope = estado?.tope_biblia_pct ?? 30;
    const gasto = estado?.gasto_biblia_semana_pct;
    confirmar({
      titulo: n === 1 && !cuerpo.ids ? 'Generar 1 imagen' : `Generar ${n} ${n === 1 ? 'imagen' : 'imágenes'}`,
      texto: [
        h('p', null, global
          ? (n === 1 ? 'Se genera la siguiente imagen pendiente en el orden láminas → hojas → tomas.'
            : `Se generan hasta ${n} imágenes de una en una, en el orden láminas → hojas → tomas; las bloqueadas entran cuando se hace su hoja.`)
          : `Se generan, de una en una y en el orden de la lista, las ${n} de este grupo que no tienen imagen ni están bloqueadas.`),
        h('p', null, `Gasta ~${num(COSTO_IMAGEN)} % de la semana de Codex por imagen (≈ ${num(n * COSTO_IMAGEN)} % en total). La Biblia lleva ${typeof gasto === 'number' ? `≈ ${pct(gasto)}` : 'un gasto sin dato'} de su tope ${pct(tope)} esta semana.`),
        h('p', { class: 'meta' }, 'Para en el primer fallo, al acabarse la cuota o al llegar al tope; nunca reintenta solo.'),
      ],
      boton: 'Generar',
      accion: () => lanzar(cuerpo),
    });
  }

  // ------------------------------------------------------------------ tarjeta
  function cuotaTexto(f) {
    if (typeof f.cuota_antes === 'number' || typeof f.cuota_despues === 'number') {
      return `cuota ${pct(f.cuota_antes)} → ${pct(f.cuota_despues)}`;
    }
    return '';
  }

  function eleccion(e) {
    if (!e) return null;
    if (typeof e === 'string') return h('p', { class: 'meta' }, `Elección: ${e}`);
    if (!Array.isArray(e) || !e.length) return null;
    return h('div', null, h('p', { class: 'etiqueta-campo' }, 'Por qué este proveedor'),
      h('ul', { class: 'eleccion' }, e.map((x) => h('li', null,
        h('span', { class: x.admitido ? 'si' : null }, x.admitido ? 'elegido' : 'descartado'),
        ` · ${x.proveedor || 'aviso'}: ${x.motivo || ''}`))));
  }

  /** Una fila del historial. `conItem`: muestra a qué imagen pertenece; `completa`: también la elección. */
  function filaTrabajo(f, clave, conItem, completa = conItem) {
    const partes = [h('span', null, fecha(f.fecha))];
    if (conItem && f._item) partes.push(h('a', { href: `#ver=${f._item.id}` }, h('strong', null, f._item.id)));
    partes.push(h('span', null, f.estado || '—'));
    partes.push(h('span', null, f.proveedor || '—'));
    if (typeof f.segundos === 'number') partes.push(h('span', null, `${num(f.segundos, 0)} s`));
    if (f.origen) partes.push(h('span', null, origen(f.origen)));
    else if (cuotaTexto(f)) partes.push(h('span', null, cuotaTexto(f)));
    if (typeof f.costo_estimado === 'number') partes.push(h('span', null, `≈ ${pct(f.costo_estimado)} de la semana`));
    return h('li', { class: conItem ? 'trabajo' : null },
      h('div', { class: 'trabajo-cab' }, partes.flatMap((p, i) => (i ? [h('span', { class: 'meta', 'aria-hidden': 'true' }, '·'), p] : [p]))),
      f.motivo ? h('p', { class: 'meta' }, `Motivo: ${f.motivo}`) : null,
      f.reinicio_en ? h('p', { class: 'meta' }, `Reinicio de cuota: ${fecha(f.reinicio_en)}`) : null,
      completa ? eleccion(f.eleccion) : null,
      desplegable(`hist-${clave}-${f.fecha}-${f._item?.id || ''}`, 'Prompt enviado entonces',
        f.prompt ? h('pre', null, f.prompt) : h('p', { class: 'meta' }, f.prompt_nota ? `Sin prompt: ${f.prompt_nota}.` : 'Sin prompt en el registro.')));
  }

  function tarjeta(it) {
    const est = estadoDe(it);
    const k = (s) => `${it.id}|${s}`;
    const mapa = porId();
    const esToma = it.grupo === 'tomas';
    const ocupado = loteEnCurso();
    const generandoEsta = ocupado && lote.actual && lote.actual.id === it.id;
    const rev = it.revision || {};

    const media = it.imagen
      ? figura(it.imagen, it.ancho, it.alto, `Imagen generada: ${it.titulo}`, it.ancho ? `${it.ancho}×${it.alto}` : '')
      : h('div', { class: 'sin-imagen' }, it.bloqueo ? `Sin imagen · bloqueada: ${it.bloqueo}` : (generandoEsta ? 'Generando ahora…' : 'Sin imagen todavía'));

    const acciones = [
      h('button', { type: 'button', class: 'boton chico', 'data-k': k('aprobar'), disabled: !it.imagen,
        title: it.imagen ? null : 'No hay imagen que revisar', onclick: () => revisar(it, 'aprobada') }, 'Aprobar'),
      h('button', { type: 'button', class: 'boton secundario chico', 'data-k': k('rechazar'), disabled: !it.imagen,
        title: it.imagen ? null : 'No hay imagen que revisar', onclick: () => rechazar(it) }, 'Rechazar con nota'),
      h('button', { type: 'button', class: 'boton secundario chico', 'data-k': k('editar'), onclick: () => abrirEditar(it) }, 'Editar prompt'),
    ];
    if (it.imagen) {
      acciones.push(h('button', { type: 'button', class: 'boton peligro chico', 'data-k': k('regenerar'), disabled: ocupado || Boolean(it.bloqueo),
        title: ocupado ? 'Hay un lote en curso' : (it.bloqueo ? `Bloqueada: ${it.bloqueo}` : null), onclick: () => regenerar(it) }, 'Regenerar'));
    } else {
      acciones.push(h('button', { type: 'button', class: 'boton secundario chico', 'data-k': k('generar'), disabled: ocupado || Boolean(it.bloqueo),
        title: ocupado ? 'Hay un lote en curso' : (it.bloqueo ? `Bloqueada: ${it.bloqueo}` : null), onclick: () => generarUna(it) }, 'Generar'));
    }

    const refs = esToma ? [h('p', { class: 'etiqueta-campo' }, 'Hojas que usa'),
      h('ul', { class: 'refs' }, (it.refs || []).map((r) => {
        const x = mapa.get(r);
        const falta = !x || !x.imagen;
        return h('li', { class: falta ? 'falta' : null }, falta ? `falta: ${r.split('/').pop()}` : h('a', { href: `#ver=${r}` }, r.split('/').pop()));
      }))] : null;

    const notaRev = rev.nota ? h('p', { class: `nota ${est}` }, h('strong', null, 'Nota: '), `«${rev.nota}»`, rev.fecha ? h('span', { class: 'meta' }, ` · ${fecha(rev.fecha)}`) : '') : null;
    const sinNegativo = !it.editables?.includes('negativo_en')
      ? 'Las láminas patrón usan el negativo general de estilo.json (no se edita desde el Estudio).' : 'Sin negativo propio.';

    return h('article', { class: `tarjeta${it.bloqueo ? ' bloqueada' : ''}`, id: `card-${it.id}`, 'aria-labelledby': `t-${it.id}` },
      media,
      h('div', { class: 'tarjeta-cuerpo' },
        h('div', { class: 'tarjeta-cab' },
          h('h3', { id: `t-${it.id}`, tabindex: '-1' }, it.titulo),
          h('span', { class: `estado e-${est}` }, generandoEsta ? 'Generando ahora' : TEXTO_ESTADO[est])),
        h('p', { class: 'tarjeta-id' }, it.id, ' · ', h('code', null, it.fuente),
          esToma && it.ficha?.versiculos ? ` · ${it.ficha.versiculos}` : ''),
        notaRev,
        it.bloqueo ? h('p', { class: 'bloqueo' }, `Bloqueada: ${it.bloqueo}`) : null,
        refs,
        h('div', { class: 'acciones' }, acciones),
        desplegable(k('enviado'), ['Prompt enviado', h('span', { class: 'meta' }, 'base + prompt + negativos, tal cual se manda')], h('pre', null, it.prompt_enviado || '—')),
        desplegable(k('prompt'), [esToma ? 'Prompt de imagen (inglés)' : 'Prompt (inglés)', h('span', { class: 'meta' }, it.campo)],
          h('pre', null, it.prompt_en || '—'), { abierto: esToma }),
        desplegable(k('negativo'), ['Negativo', it.negativo_en ? h('span', { class: 'meta' }, it.campo_negativo) : null],
          it.negativo_en ? h('pre', null, it.negativo_en) : h('p', { class: 'meta' }, sinNegativo)),
        esToma ? desplegable(k('movimiento'), 'Prompt de movimiento (inglés)',
          it.movimiento_en ? h('pre', null, it.movimiento_en) : h('p', { class: 'meta' }, 'Sin prompt de movimiento.'), { abierto: true }) : null,
        desplegable(k('ficha'), 'Ficha', h('div', { class: 'ficha' }, valor(it.ficha))),
        desplegable(k('historial'), `Historial (${(it.historial || []).length})`,
          (it.historial || []).length ? h('ul', { class: 'historial' }, [...it.historial].reverse().map((f, i) => filaTrabajo(f, `${it.id}-${i}`, false)))
            : h('p', { class: 'meta' }, 'Todavía no se ha generado.')),
        (it.anteriores || []).length ? desplegable(k('anteriores'), `Versiones anteriores (${it.anteriores.length})`,
          h('div', { class: 'anteriores' }, [...it.anteriores].reverse().map((u) => {
            const m = /-(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})(?:-\d+)?\.png$/.exec(decodeURIComponent(u));
            const cuando = m ? `apartada ${Number(m[3])}-${MESES[Number(m[2]) - 1]} ${m[4]}:${m[5]}` : 'versión anterior';
            return figura(u, null, null, `Versión anterior de ${it.titulo} (${cuando})`, cuando);
          }))) : null));
  }

  // ------------------------------------------------------------------ ficha legible
  const NOMBRES = {
    prompt_es: 'Prompt (español)', negativo_es: 'Negativo (español)', descripcion_es: 'Descripción de la imagen',
    movimiento_es: 'Movimiento', clips_8s: 'Clips de 8 s', versiculos: 'Versículos', camara: 'Cámara', ref: 'Cita',
    transicion: 'Transición', element: 'Elemento', epoca: 'Época', certeza: 'Certeza', calculo: 'Cálculo',
    operacion: 'Operación', interpretacion: 'Interpretación', archivo: 'Archivo',
  };
  const nombre = (k) => NOMBRES[k] || (k.charAt(0).toUpperCase() + k.slice(1)).replace(/_/g, ' ');

  function valor(v, clave) {
    if (v == null || v === '') return '—';
    if (Array.isArray(v)) {
      if (!v.length) return '—';
      if (v.every((x) => x === null || typeof x !== 'object')) return v.join(', ');
      return h('ol', null, v.map((x) => h('li', null, valor(x))));
    }
    if (typeof v === 'object') {
      return h('dl', null, Object.entries(v).flatMap(([kk, x]) => [h('dt', null, nombre(kk)),
        h('dd', null, kk === 'certeza' && typeof x === 'string' ? h('span', { class: `certeza ${x}` }, x) : valor(x, kk))]));
    }
    if (clave === 'cita') return `«${v}»`;
    return String(v);
  }

  // ------------------------------------------------------------------ acciones
  async function revisar(it, estadoNuevo, nota = '') {
    const r = await api('/api/revision', { id: it.id, estado: estadoNuevo, nota });
    if (!r.ok) return errorDe(r);
    mensaje(r.datos.mensaje || `${it.titulo}: ${estadoNuevo === 'aprobada' ? 'aprobada' : 'rechazada'}.`);
    await recargarDatos();
    return null;
  }

  function rechazar(it) {
    confirmar({
      titulo: `Rechazar · ${it.titulo}`,
      texto: [h('p', null, 'Escribe qué está mal (se guarda con la revisión, junto al sha256 de esta imagen). Para corregirla: edita el prompt y regenera.')],
      nota: { etiqueta: 'Nota', valor: it.revision?.estado === 'rechazada' ? it.revision.nota : '', requerida: true },
      boton: 'Rechazar',
      accion: (nota) => revisar(it, 'rechazada', nota),
    });
  }

  function regenerar(it) {
    confirmar({
      titulo: `Regenerar · ${it.titulo}`,
      texto: [
        h('p', null, 'La imagen actual pasa a «versiones anteriores» (guiones/imagenes/_anteriores/) y se pide una nueva con el prompt vigente. Gasta ~0,2 % de la semana de Codex.'),
        h('p', { class: 'nota-regenerar' }, 'Si después pulsas «Detener» en la cola justo cuando empieza, la anterior puede quedar ya en «versiones anteriores» sin que se pida la nueva: no se pierde, se ve en esta tarjeta.'),
      ],
      boton: 'Regenerar',
      accion: () => lanzar({ ids: [it.id], regenerar: true }),
    });
  }

  function generarUna(it) {
    confirmar({
      titulo: `Generar · ${it.titulo}`,
      texto: [h('p', null, `Se genera la imagen de ${it.id} con el prompt vigente. Gasta ~${num(COSTO_IMAGEN)} % de la semana de Codex.`)],
      boton: 'Generar',
      accion: () => lanzar({ ids: [it.id] }),
    });
  }

  // ------------------------------------------------------------------ diálogo de confirmación
  const dlgC = $('#dlg-confirmar');
  let accionC = null;
  let notaRequerida = false;

  function confirmar({ titulo, texto, boton = 'Confirmar', nota = null, accion }) {
    $('#dlg-confirmar-titulo').textContent = titulo;
    $('#dlg-confirmar-texto').replaceChildren(...texto);
    $('#dlg-confirmar-si').textContent = boton;
    $('#dlg-confirmar-si').disabled = false;
    $('#dlg-confirmar-si').dataset.texto = boton;
    $('#dlg-confirmar-campo').hidden = !nota;
    $('#dlg-confirmar-nota').value = nota?.valor || '';
    $('#dlg-confirmar-etiqueta').textContent = nota?.etiqueta || 'Nota';
    notaRequerida = Boolean(nota?.requerida);
    ponerErrores($('#dlg-confirmar-errores'), null);
    accionC = { accion, conNota: Boolean(nota), volver: document.activeElement };
    dlgC.showModal();
    if (nota) $('#dlg-confirmar-nota').focus();
  }

  $('#dlg-confirmar-si').addEventListener('click', async () => {
    if (!accionC) return;
    const nota = $('#dlg-confirmar-nota').value.trim();
    if (accionC.conNota && notaRequerida && !nota) {
      ponerErrores($('#dlg-confirmar-errores'), ['Escribe la nota: qué está mal en la imagen.']);
      $('#dlg-confirmar-nota').focus();
      return;
    }
    const btn = $('#dlg-confirmar-si');
    btn.disabled = true;
    btn.textContent = 'Un momento…';
    const errores = await accionC.accion(nota);
    btn.disabled = false;
    btn.textContent = btn.dataset.texto;
    if (errores && errores.length) { ponerErrores($('#dlg-confirmar-errores'), errores, 'No se hizo:'); return; }
    cerrarConfirmar();
  });
  $('#dlg-confirmar-no').addEventListener('click', () => cerrarConfirmar());
  function cerrarConfirmar() {
    const volver = accionC?.volver;
    accionC = null;
    if (dlgC.open) dlgC.close();
    restaurarFoco(volver);
  }
  dlgC.addEventListener('cancel', () => { const v = accionC?.volver; accionC = null; setTimeout(() => restaurarFoco(v)); });

  function restaurarFoco(el) {
    if (!el) return;
    const k = el.dataset?.k;
    const nuevo = (k && main.querySelector(`[data-k="${CSS.escape(k)}"]`)) || (document.contains(el) ? el : null);
    if (nuevo && !nuevo.disabled) nuevo.focus();
  }

  function ponerErrores(caja, errores, titulo = 'Errores:') {
    caja.hidden = !errores || !errores.length;
    caja.replaceChildren();
    if (caja.hidden) return;
    caja.append(h('strong', null, titulo), h('ul', null, errores.map((e) => h('li', null, e))));
    caja.scrollIntoView({ block: 'nearest' });
  }

  // ------------------------------------------------------------------ diálogo de edición
  const dlgE = $('#dlg-editar');
  const edP = $('#ed-prompt');
  const edN = $('#ed-negativo');
  let ed = null;

  function abrirEditar(it) {
    const negEditable = (it.editables || []).includes('negativo_en');
    ed = { it, p0: it.prompt_en || '', n0: it.negativo_en || '', negEditable, volver: document.activeElement, guardados: [] };
    $('#dlg-editar-titulo').textContent = `Editar prompt · ${it.titulo}`;
    $('#dlg-editar-donde').textContent = `${it.id} · ${it.fuente}`;
    $('#dlg-editar-campo-p').textContent = it.campo;
    $('#dlg-editar-campo-n').textContent = negEditable ? it.campo_negativo : 'no editable';
    edP.value = ed.p0;
    edN.value = ed.n0;
    edN.disabled = !negEditable;
    $('#ed-negativo-nota').hidden = negEditable;
    ponerErrores($('#ed-errores'), null);
    $('#ed-guardar').disabled = false;
    $('#ed-guardar').textContent = 'Guardar';
    pintarDiff();
    dlgE.showModal();
    edP.focus();
  }

  /** Diferencia por palabras (LCS sobre palabras y espacios): [['=', s] | ['-', s] | ['+', s]]. */
  function diferencia(a, b) {
    const A = a.match(/\S+|\s+/g) || [];
    const B = b.match(/\S+|\s+/g) || [];
    if (A.length * B.length > 4e6) return [['-', a], ['+', b]];
    const n = A.length, m = B.length;
    const T = Array.from({ length: n + 1 }, () => new Uint32Array(m + 1));
    for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) T[i][j] = A[i] === B[j] ? T[i + 1][j + 1] + 1 : Math.max(T[i + 1][j], T[i][j + 1]);
    const out = [];
    const push = (t, s) => { if (out.length && out[out.length - 1][0] === t) out[out.length - 1][1] += s; else out.push([t, s]); };
    let i = 0, j = 0;
    while (i < n && j < m) {
      if (A[i] === B[j]) { push('=', A[i]); i++; j++; } else if (T[i + 1][j] >= T[i][j + 1]) push('-', A[i++]); else push('+', B[j++]);
    }
    while (i < n) push('-', A[i++]);
    while (j < m) push('+', B[j++]);
    return out;
  }

  function bloqueDiff(nombreCampo, antes, despues) {
    if (antes.trim() === despues.trim()) return [h('h4', null, nombreCampo), h('p', { class: 'meta' }, 'Sin cambios.')];
    return [h('h4', null, nombreCampo), h('p', null, diferencia(antes, despues).map(([t, s]) =>
      (t === '=' ? s : h(t === '-' ? 'del' : 'ins', null, s))))];
  }

  let temporizadorDiff = null;
  function pintarDiff() {
    if (!ed) return;
    $('#ed-diff').replaceChildren(...bloqueDiff('Prompt', ed.p0, edP.value),
      ...(ed.negEditable ? bloqueDiff('Negativo', ed.n0, edN.value) : []));
  }
  for (const t of [edP, edN]) t.addEventListener('input', () => { clearTimeout(temporizadorDiff); temporizadorDiff = setTimeout(pintarDiff, 150); });

  $('#ed-guardar').addEventListener('click', async () => {
    if (!ed) return;
    const cambios = [];
    if (edP.value.trim() !== ed.p0.trim()) cambios.push(['prompt_en', edP.value, 'el prompt']);
    if (ed.negEditable && edN.value.trim() !== ed.n0.trim()) cambios.push(['negativo_en', edN.value, 'el negativo']);
    if (!cambios.length) { ponerErrores($('#ed-errores'), ['No hay cambios que guardar.'], 'Nada que guardar:'); return; }
    const btn = $('#ed-guardar');
    btn.disabled = true;
    btn.textContent = 'Validando…';
    ponerErrores($('#ed-errores'), null);
    const avisos = [];
    for (const [campo, valorNuevo, nombreCampo] of cambios) {
      const r = await api('/api/prompt', { id: ed.it.id, campo, valor: valorNuevo });
      if (!r.ok || !r.datos.ok) {
        btn.disabled = false;
        btn.textContent = 'Guardar';
        const previos = ed.guardados.length ? `Se guardó ${ed.guardados.join(' y ')}, pero no ${nombreCampo}. El validador dice:` : `No se guardó ${nombreCampo}. El validador dice:`;
        ponerErrores($('#ed-errores'), errorDe(r), previos);
        if (ed.guardados.length) recargarDatos();
        pintarDiff();
        return;
      }
      if (campo === 'prompt_en') ed.p0 = (r.datos.despues ?? valorNuevo.trim()); else ed.n0 = (r.datos.despues ?? valorNuevo.trim());
      ed.guardados.push(nombreCampo);
      if (r.datos.aviso) avisos.push(r.datos.aviso);
    }
    const volver = ed.volver;
    const titulo = ed.it.titulo;
    ed = null;
    dlgE.close();
    mensaje(`${titulo}: guardado y validado (${cambios.map((c) => c[2]).join(' y ')}). Las fichas .md se regeneraron.${avisos.length ? ` ${avisos.join(' ')}` : ''}`, avisos.length ? 'error' : 'ok');
    await recargarDatos();
    restaurarFoco(volver);
  });
  $('#ed-cancelar').addEventListener('click', () => { const v = ed?.volver; ed = null; dlgE.close(); restaurarFoco(v); });
  dlgE.addEventListener('cancel', () => { const v = ed?.volver; ed = null; setTimeout(() => restaurarFoco(v)); });

  // ------------------------------------------------------------------ arranque
  window.addEventListener('hashchange', () => {
    ruta();
    pintar();
    if (destino) irADestino(); else { window.scrollTo(0, 0); main.focus({ preventScroll: true }); }
  });
  ruta();
  cargar().then(irADestino);
  // la cuota y el gasto cambian aunque nadie toque la página
  setInterval(() => { if (!document.hidden) recargarEstado(); }, 60000);
})();
