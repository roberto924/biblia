/* Biblia · Compañero de lectura — lógica pura (Nucleo) + interfaz.
   Nucleo no usa DOM: pruebas/probar.mjs lo evalúa con node:vm y lo lee de globalThis.BibliaNucleo. */
'use strict';

const Nucleo = (() => {
  const TRADS = ['TM', 'LXX'];
  const TIPOS = ['al_engendrar', 'restantes', 'total'];

  const norm = s => String(s == null ? '' : s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
  const num = v => (v === null || v === undefined || v === '' || !Number.isFinite(+v)) ? null : +v;

  /* ---- Libros: orden canónico (para comparar refs de varios libros) y nombres ---- */
  const CANON = ['Gn', 'Ex', 'Lv', 'Nm', 'Dt', 'Jos', 'Jue', 'Rt', '1S', '2S', '1R', '2R', '1Cr', '2Cr', 'Esd', 'Neh', 'Est', 'Job', 'Sal', 'Pr', 'Ec', 'Cnt',
    'Is', 'Jer', 'Lm', 'Ez', 'Dn', 'Os', 'Jl', 'Am', 'Abd', 'Jon', 'Mi', 'Nah', 'Hab', 'Sof', 'Hag', 'Zac', 'Mal',
    'Mt', 'Mr', 'Lc', 'Jn', 'Hch', 'Ro', '1Co', '2Co', 'Ga', 'Ef', 'Fil', 'Col', '1Ts', '2Ts', '1Ti', '2Ti', 'Tit', 'Flm', 'He', 'Stg', '1P', '2P', '1Jn', '2Jn', '3Jn', 'Jud', 'Ap'];
  const NOMBRES_LIBRO = { Gn: 'Génesis', Ex: 'Éxodo', Lv: 'Levítico', Nm: 'Números', Dt: 'Deuteronomio', Jos: 'Josué', Jue: 'Jueces', Rt: 'Rut' };
  const ordLibro = new Map(), idPorOrd = new Map(), idCanon = new Map();
  CANON.forEach((id, i) => { ordLibro.set(norm(id), i + 1); idPorOrd.set(i + 1, id); idCanon.set(norm(id), id); });
  Object.entries(NOMBRES_LIBRO).forEach(([id, n]) => idCanon.set(norm(n), id));
  // Id de libro con su grafía canónica ("éx" → "Ex"); un id desconocido se registra en orden de aparición.
  function libroCanon(x) {
    const k = norm(x).replace(/\s+/g, '').replace(/\.$/, '');
    if (!k) return 'Gn';
    if (idCanon.has(k)) return idCanon.get(k);
    const id = String(x).trim();
    if (!ordLibro.has(k)) { const o = 100 + ordLibro.size; ordLibro.set(k, o); idPorOrd.set(o, id); idCanon.set(k, id); }
    return idCanon.get(k);
  }
  const ordDe = id => ordLibro.get(norm(libroCanon(id)));

  // "Ex 7:7" → { libro: 'Ex', cap: 7, v: 7 }. Sin libro (datos antiguos) se entiende Génesis.
  function parseRef(ref) {
    const s = String(ref == null ? '' : ref);
    const b = /([1-3]?\s?[A-Za-zÀ-ÿ]+)\.?\s*(\d+)(?:\s*:\s*(\d+))?/.exec(s);
    if (b) {
      const k = norm(b[1]).replace(/\s+/g, '');
      if (idCanon.has(k)) return { libro: idCanon.get(k), cap: +b[2], v: b[3] ? +b[3] : null };
    }
    const m = /(\d+)\s*:\s*(\d+)/.exec(s);
    if (m) return { libro: 'Gn', cap: +m[1], v: +m[2] };
    const c = /(\d+)\s*$/.exec(s);
    return c ? { libro: 'Gn', cap: +c[1], v: null } : null;
  }

  // Clave numérica comparable de un versículo: Gn 4:1 → 1004001, Ex 7:7 → 2007007
  function clave(ref) { const r = parseRef(ref); return r && r.v ? ordDe(r.libro) * 1e6 + r.cap * 1000 + r.v : null; }
  const refTxt = (cap, v, libro) => `${libro || 'Gn'} ${cap}:${v}`;
  const refDeClave = k => refTxt(Math.floor(k / 1000) % 1000, k % 1000, idPorOrd.get(Math.floor(k / 1e6)));
  // Id del libro de un capítulo: `libro` puede traer el id ("Ex") o el nombre ("Éxodo").
  function libroIdDe(d, x) {
    if (x == null || x === '') return 'Gn';
    const k = norm(x), L = (d && Array.isArray(d.libros)) ? d.libros : [];
    const l = L.find(l => l && (norm(l.id) === k || norm(l.nombre) === k));
    return libroCanon(l ? l.id : x);
  }
  // Libros presentes: `libros` de los datos si viene; si no, derivados de `capitulos`.
  const libros = d => memo(d || {}, 'libros', () => {
    d = d || {};
    const caps = d.capitulos || [], porId = new Map();
    caps.forEach(c => {
      const id = libroIdDe(d, c.libro);
      if (!porId.has(id)) porId.set(id, { id, nombre: c.libro && norm(c.libro) !== norm(id) ? String(c.libro) : (NOMBRES_LIBRO[id] || id), capitulos: 0, presentes: 0 });
      const b = porId.get(id); b.capitulos = Math.max(b.capitulos, +c.cap || 0); b.presentes++;
    });
    if (Array.isArray(d.libros) && d.libros.length) {
      return d.libros.filter(l => l && l.id).map(l => {
        const id = libroCanon(l.id), b = porId.get(id);
        return { id, nombre: l.nombre || (b && b.nombre) || NOMBRES_LIBRO[id] || id, capitulos: +l.capitulos || (b ? b.capitulos : 0), presentes: b ? b.presentes : 0 };
      }).sort((a, b) => ordDe(a.id) - ordDe(b.id));
    }
    return [...porId.values()].sort((a, b) => ordDe(a.id) - ordDe(b.id));
  });
  const nombreLibro = (d, id) => { const c = libroCanon(id), l = libros(d).find(x => x.id === c); return l ? l.nombre : (NOMBRES_LIBRO[c] || c); };
  const libroDe = p => { const r = p && parseRef(p.inicio); return r ? r.libro : 'Gn'; };

  function claseCerteza(c) {
    if (c === 'explicito' || c === 'texto') return 'texto';
    if (c === 'calculo') return 'calculo';
    return 'inferido';
  }

  function indexar(d) {
    d = d || {};
    // Registra los libros de los datos antes de calcular claves (un id fuera del canon también vale).
    (d.libros || []).forEach(l => { if (l && l.id) libroCanon(l.id); });
    (d.capitulos || []).forEach(c => libroIdDe(d, c && c.libro));
    const personas = new Map(), hijos = new Map(), padres = new Map(), conyuges = new Map(), edades = new Map();
    const add = (m, k, v) => { if (!m.has(k)) m.set(k, []); m.get(k).push(v); };
    (d.personas || []).forEach(p => { if (p && p.id) personas.set(p.id, p); });
    const asegurar = id => { if (!personas.has(id)) personas.set(id, { id, nombre: String(id).replace(/_\d+$/, ''), sexo: '?', refs: [] }); };
    // Relaciones y edades por versículo: el acompañante no recorre las listas completas en cada render.
    const relPorRef = new Map(), edadesPorRef = new Map();
    (d.relaciones || []).forEach(r => {
      if (!r || !r.de || !r.a || r.de === r.a) return;
      asegurar(r.de); asegurar(r.a);
      const k = clave(r.ref); if (k !== null) add(relPorRef, k, r);
      if (r.tipo === 'padre' || r.tipo === 'madre') { add(hijos, r.de, r); add(padres, r.a, r); }
      else if (r.tipo === 'conyuge') { add(conyuges, r.de, Object.assign({}, r, { otro: r.a })); add(conyuges, r.a, Object.assign({}, r, { otro: r.de })); }
    });
    (d.edades || []).forEach(e => { if (e && e.persona) { add(edades, e.persona, e); const k = clave(e.ref); if (k !== null) add(edadesPorRef, k, e); } });
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
    return { datos: d, personas, hijos, padres, conyuges, edades, menciones, porRef, primera, lugares, lugaresPorRef, mencionesLugar,
      relPorRef, edadesPorRef, memo: new Map() };
  }

  const cache = new WeakMap();
  function indice(d) {
    if (d && typeof d === 'object') { if (!cache.has(d)) cache.set(d, indexar(d)); return cache.get(d); }
    return indexar(d);
  }
  // Resultado calculado una vez por conjunto de datos (los datos no cambian durante la sesión).
  function memo(d, k, fn) {
    if (!d || typeof d !== 'object') return fn();
    const m = indice(d).memo;
    if (!m.has(k)) m.set(k, fn());
    return m.get(k);
  }
  const persona = (d, id) => indice(d).personas.get(id) || null;
  // Todos los nombres de un registro (p. ej. Abram/Abraham en un solo registro).
  const lista = v => Array.isArray(v) ? v : v ? [v] : [];
  const nombresDe = p => p ? [...new Set([p.nombre, p.nombre_rv1909].concat(lista(p.formas_rv1909), lista(p.otros_nombres), lista(p.nombres), lista(p.alias)).filter(x => typeof x === 'string' && x.trim()))] : [];

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
        // Quien tiene padre conocido cuelga del padre, no de la madre (Lea → Rubén va bajo Jacob, no bajo Labán).
        if (r.tipo === 'madre' && (I.padres.get(r.a) || []).some(x => x.tipo === 'padre' && x.de !== id)) continue;
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

  // Bosque: Adán primero, luego otras raíces (sin padres conocidos) no alcanzadas. Se calcula una vez.
  const construirBosque = d => memo(d, 'bosque', () => bosque(d));
  function bosque(d) {
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
    // Parejas sin padres ni hijos conocidos (Potifar y su esposa): también tienen sitio, como rama propia.
    const visibles = alcanzables(d, raices.filter(Boolean));
    const parejas = [...I.personas.values()].filter(p => I.conyuges.has(p.id) && !visibles.has(p.id))
      .sort((x, y) => (x.sexo === 'm' ? 0 : 1) - (y.sexo === 'm' ? 0 : 1));
    for (const p of parejas) {
      if (visibles.has(p.id)) continue;
      const t = construirArbol(d, p.id, visit);
      if (t) { raices.push(t); visibles.add(p.id); t.conyuges.forEach(c => visibles.add(c.otro)); }
    }
    return raices.filter(Boolean);
  }

  // Posición de cada persona en el bosque: nodo (padre, generación) o dónde aparece como cónyuge/madre.
  function mapaArbol(d) {
    return memo(d, 'mapaArbol', () => {
      const nodos = new Map(), aparece = new Map();
      construirBosque(d).forEach((raiz, ri) => (function r(n, padre, prof) {
        nodos.set(n.id, { n, padre, prof, raiz: ri });
        n.conyuges.forEach(c => { if (!aparece.has(c.otro)) aparece.set(c.otro, { nodo: n.id, como: 'conyuge' }); });
        n.madres.forEach(m => { if (!aparece.has(m.de)) aparece.set(m.de, { nodo: n.id, como: 'madre' }); });
        n.hijos.forEach(h => r(h, n.id, prof + 1));
      })(raiz, null, 0));
      return { nodos, aparece };
    });
  }
  const nodoArbol = (d, id) => { const x = mapaArbol(d).nodos.get(id); return x ? x.n : null; };
  // Ruta raíz→nodo para llegar a una persona; si no es nodo, al nodo donde aparece como cónyuge o madre.
  function rutaArbol(d, id) {
    const M = mapaArbol(d);
    let nodo = id, como = 'nodo';
    if (!M.nodos.has(id)) { const a = M.aparece.get(id); if (!a) return null; nodo = a.nodo; como = a.como; }
    const ruta = [];
    for (let x = nodo; x !== null && x !== undefined; x = M.nodos.get(x).padre) ruta.unshift(x);
    return { id, nodo, como, ruta };
  }
  // Personas sin ningún parentesco registrado (Melquisedec, Faraón…): sección propia del Árbol, en orden de aparición.
  function sinParentesco(d) {
    return memo(d, 'sinPar', () => {
      const I = indice(d);
      return [...I.personas.values()].filter(p => !I.padres.has(p.id) && !I.hijos.has(p.id) && !I.conyuges.has(p.id))
        .sort((a, b) => (I.primera.get(a.id) || 1e9) - (I.primera.get(b.id) || 1e9)).map(p => p.id);
    });
  }
  // ¿Se ve la persona en la pantalla Árbol? (nodo, cónyuge, madre o sección sin parentesco)
  const enPantallaArbol = (d, id) => !!rutaArbol(d, id) || sinParentesco(d).includes(id);
  // Nodos desplegados al abrir el árbol: los `niveles` primeros de la primera raíz.
  function arbolInicial(d, niveles) {
    niveles = niveles === undefined ? 2 : niveles;
    const s = new Set(), b = construirBosque(d);
    if (b[0]) (function r(n, prof) { if (prof < niveles && n.hijos.length) { s.add(n.id); n.hijos.forEach(h => r(h, prof + 1)); } })(b[0], 0);
    return s;
  }
  // Hijos de un nodo agrupados por madre cuando hay varias cónyuges o varias madres (Jacob: Lea, Raquel, Bilha, Zilpa).
  // [{madre, vinculo (relación cónyuge con su nota), hijos}]; un solo grupo con madre null si no hace falta agrupar.
  function hijosPorMadre(d, n) {
    const I = indice(d), hs = (n && n.hijos) || [], cony = (n && n.conyuges) || [];
    const madreDe = h => { const m = (I.padres.get(h.id) || []).find(x => x.tipo === 'madre' && x.de !== n.id); return m ? m.de : null; };
    const madres = unicos(hs.map(madreDe).filter(Boolean));
    if (!(cony.length > 1 || madres.length > 1)) return [{ madre: null, vinculo: null, hijos: hs }];
    // Orden: el del primer hijo de cada madre (orden de los datos, que sigue el relato).
    const orden = madres;
    const grupos = orden.map(m => ({ madre: m, vinculo: cony.find(c => c.otro === m) || null, hijos: hs.filter(h => madreDe(h) === m) }));
    const sin = hs.filter(h => !madreDe(h));
    if (sin.length) grupos.push({ madre: null, vinculo: null, hijos: sin });
    return grupos;
  }
  // Parejas de un nodo, cada una con sus hijos: [{pareja, vinculo (relación cónyuge o null si el texto no registra
  // matrimonio), hijos}]. Primero las parejas con hijos (orden del primer hijo), luego las cónyuges sin hijos; los hijos
  // sin madre indicada van en un grupo {pareja: null}. Excepción: si hay una sola esposa (cónyuge) y ningún hijo tiene
  // madre escrita (Noé, Sem…), cuelgan de ella con `supuesta: true`: es INFERIDO que sea la madre, no lo dice el texto.
  function uniones(d, n) {
    const I = indice(d), hs = (n && n.hijos) || [], cony = (n && n.conyuges) || [];
    const madreDe = h => { const m = (I.padres.get(h.id) || []).find(x => x.tipo === 'madre' && x.de !== n.id); return m ? m.de : null; };
    const out = [], de = id => { let u = out.find(x => x.pareja === id); if (!u) { u = { pareja: id, vinculo: cony.find(c => c.otro === id) || null, hijos: [] }; out.push(u); } return u; };
    const sin = [];
    hs.forEach(h => { const m = madreDe(h); if (m) de(m).hijos.push(h); else sin.push(h); });
    cony.forEach(c => de(c.otro));
    if (out.length === 1 && out[0].vinculo && !out[0].hijos.length && sin.length) Object.assign(out[0], { hijos: sin, supuesta: true });
    else if (sin.length) out.push({ pareja: null, vinculo: null, hijos: sin });
    return out;
  }
  // Madre supuesta de un hijo (única esposa de su padre, el texto no la nombra como madre) o null.
  function madreSupuesta(d, id) {
    const x = mapaArbol(d).nodos.get(id), p = x && x.padre !== null && x.padre !== undefined ? nodoArbol(d, x.padre) : null;
    const u = p && uniones(d, p).find(u => u.supuesta && u.hijos.some(h => h.id === id));
    return u ? u.pareja : null;
  }
  // Años vividos (edad total: texto o cálculo) y nacimiento/muerte en años desde Adán (siempre cálculo) para una tradición.
  function vida(d, id, trad, combo) {
    const total = edad(d, id, 'total', trad), x = combo ? vidasCrono(d, combo).get(id) : null;
    return { total, nacimiento: x ? x.nacimiento : null, muerte: x ? x.muerte : null, evNac: x ? x.evNac : null, evMuerte: x ? x.evMuerte : null };
  }

  function rutas(d, desde, hasta, limite) {
    limite = limite || 500;
    const out = [];
    if (!desde || !hasta) return out;
    // Solo se baja por quienes pueden llegar a `hasta` (sus ascendientes): evita recorrer todo el árbol.
    const I = indice(d), anc = new Set([hasta]), cola = [hasta];
    while (cola.length) { const x = cola.pop(); for (const r of (I.padres.get(x) || [])) if (!anc.has(r.de)) { anc.add(r.de); cola.push(r.de); } }
    if (!anc.has(desde)) return out;
    const camino = [desde], vis = new Set([desde]);
    (function dfs(id) {
      if (out.length >= limite) return;
      if (id === hasta) { out.push(camino.slice()); return; }
      for (const r of hijosDe(d, id)) {
        if (vis.has(r.a) || !anc.has(r.a)) continue;
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
    if (!desde && !hasta) return memo(d, 'linea|' + trad, () => { const a = idAdan(d), b = idAbraham(d); return a && b ? lineaPorTradicion(d, trad, a, b) : []; });
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

  const lineaAdanAbraham = d => memo(d, 'lineaAA', () => fusionarOrden(lineaPorTradicion(d, 'LXX'), lineaPorTradicion(d, 'TM')));
  const idJacob = d => encontrar(d, ['Jacob_1', 'Israel_1', 'Jacob', 'Israel']);
  // Atajos de línea calculados de los datos; solo los que existen: Adán → Abraham y Abraham → hijos de Jacob.
  function atajosLinea(d) {
    return memo(d, 'atajos', () => {
      const out = [], adan = idAdan(d), abr = idAbraham(d), jac = idJacob(d);
      const l1 = adan && abr ? lineaAdanAbraham(d) : [];
      if (l1.length) out.push({ id: 'adan-abraham', desde: adan, hasta: abr, ruta: l1, extra: [] });
      if (abr && jac) {
        const r = rutas(d, abr, jac, 50).sort((a, b) => a.length - b.length)[0];
        if (r) out.push({ id: 'abraham-jacob', desde: abr, hasta: jac, ruta: r, extra: hijosDe(d, jac).map(x => x.a), hijosDeFinal: true });
      }
      return out;
    });
  }
  // Ids de la línea principal (unión de los atajos), para destacarla en el árbol.
  const lineaPrincipal = d => memo(d, 'lineaP', () => new Set(atajosLinea(d).flatMap(a => a.ruta)));

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
    // Solo quienes tienen edades de la tabla (al engendrar, restantes, total); las "en_evento" van aparte.
    const con = id => (I.edades.get(id) || []).some(e => TIPOS.includes(e.tipo));
    const orden = lineaAdanAbraham(d).filter(con);
    for (const id of I.edades.keys()) if (!orden.includes(id) && I.personas.has(id) && con(id)) orden.push(id);
    return orden;
  }
  // Barras de vidas: filas con nacimiento calculable y, aparte, quienes tienen edades pero no la cadena completa.
  function vidas(d, trad) {
    const filas = anosDesdeAdan(d, trad).filter(f => f.nacimiento !== null), en = new Set(filas.map(f => f.id)), I = indice(d);
    const omitidas = ordenPatriarcas(d).filter(id => !en.has(id) && (I.edades.get(id) || []).some(e => e.tradicion === trad && TIPOS.includes(e.tipo)));
    return { filas, omitidas };
  }
  // Edades "en un momento del relato" (tipo en_evento), TM y LXX juntas, en orden de versículo.
  // Con refs, solo las de esos versículos.
  function edadesEnEvento(d, refs) {
    const I = indice(d);
    let fuente;
    if (refs) { fuente = []; [...new Set([].concat(refs).map(clave).filter(k => k !== null))].sort((a, b) => a - b).forEach(k => (I.edadesPorRef.get(k) || []).forEach(e => fuente.push(e))); }
    else fuente = (d && d.edades) || [];
    const g = new Map();
    fuente.forEach(e => {
      if (!e || e.tipo !== 'en_evento' || !e.persona || num(e.valor) === null) return;
      const k0 = clave(e.ref), key = e.persona + '|' + (e.evento ? norm(e.evento) : '@' + k0);
      if (!g.has(key)) g.set(key, { persona: e.persona, tipo: 'en_evento', evento: e.evento || '', ref: e.ref, clave: k0, TM: null, LXX: null });
      const x = g.get(key);
      if (k0 !== null && (x.clave === null || k0 < x.clave)) { x.clave = k0; x.ref = e.ref; }
      x[e.tradicion === 'LXX' ? 'LXX' : 'TM'] = Object.assign({}, e, { valor: num(e.valor) });
    });
    return [...g.values()].map(x => Object.assign(x, { difiere: !!(x.TM && x.LXX && x.TM.valor !== x.LXX.valor), solo: x.TM && !x.LXX ? 'TM' : !x.TM && x.LXX ? 'LXX' : null }))
      .sort((a, b) => (a.clave || 0) - (b.clave || 0));
  }
  // Las mismas, agrupadas por persona (en orden de su primera edad en el relato).
  function edadesEnEventoPorPersona(d) {
    const m = new Map();
    edadesEnEvento(d).forEach(x => { if (!m.has(x.persona)) m.set(x.persona, { persona: x.persona, items: [] }); m.get(x.persona).items.push(x); });
    return [...m.values()];
  }

  function personasEnCapitulo(d, cap, libro) {
    const out = [], lb = libroCanon(libro || 'Gn');
    for (const p of indice(d).personas.values()) {
      const refs = [...new Set([].concat(p.refs || [], p.primera_ref ? [p.primera_ref] : []))];
      const vs = refs.map(parseRef).filter(r => r && r.cap === cap && r.libro === lb).map(r => r.v || 0);
      if (vs.length) out.push({ id: p.id, persona: p, versos: [...new Set(vs)].sort((a, b) => a - b) });
    }
    return out.sort((a, b) => a.versos[0] - b.versos[0]);
  }

  function buscar(d, q, max) {
    const n = norm(q);
    if (!n) return [];
    const res = [];
    for (const p of indice(d).personas.values()) {
      const noms = nombresDe(p).map(norm), id = norm(p.id);
      if (noms.some(x => x.includes(n)) || id.includes(n)) res.push({ p, rango: noms.some(x => x.startsWith(n)) ? 0 : 1 });
    }
    return res.sort((a, b) => a.rango - b.rango || norm(a.p.nombre).localeCompare(norm(b.p.nombre))).slice(0, max || 20).map(x => x.p);
  }

  /* ---- Lectura acompañada ---- */
  // Pasajes de los datos; si no hay, uno por capítulo.
  const pasajes = d => memo(d || {}, 'pasajes', () => pasajesCalc(d || {}));
  function pasajesCalc(d) {
    if (Array.isArray(d.pasajes) && d.pasajes.length) return d.pasajes.filter(p => p && p.id && clave(p.inicio) && clave(p.fin));
    return (d.capitulos || []).map(c => ({ c, lb: libroIdDe(d, c.libro) }))
      .sort((x, y) => ordDe(x.lb) - ordDe(y.lb) || x.c.cap - y.c.cap)
      .map(({ c, lb }) => {
        const vs = c.versiculos || [];
        return { id: lb === 'Gn' ? 'cap-' + c.cap : `cap-${lb}-${c.cap}`, inicio: refTxt(c.cap, vs.length ? vs[0].n : 1, lb), fin: refTxt(c.cap, vs.length ? vs[vs.length - 1].n : 1, lb),
          titulo: `${c.libro && norm(c.libro) !== norm(lb) ? c.libro : nombreLibro(d, lb)} ${c.cap}`, titulo_origen: 'capitulo', resumen: '' };
      });
  }
  // Plan agrupado por `seccion` (editorial) con su progreso. Un pasaje sin sección hereda la del anterior
  // del mismo libro. Si ningún pasaje trae sección, devuelve un único grupo con titulo null.
  // Con `libro`, solo los pasajes de ese libro (numerados desde 1 dentro del libro).
  function seccionesPlan(d, leidos, sigId, libro) {
    const L = new Set(leidos || []), out = [], porT = new Map(), lb = libro ? libroCanon(libro) : null;
    let previa = '', libPrev = null;
    pasajes(d).filter(p => !lb || libroDe(p) === lb).forEach((p, i) => {
      const lp = libroDe(p);
      if (lp !== libPrev) { previa = ''; libPrev = lp; }
      const t = (typeof p.seccion === 'string' && p.seccion.trim()) || previa;
      previa = t;
      const kt = lp + '|' + t;
      if (!porT.has(kt)) {
        const base = norm(t).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
        const g = { id: 'sec-' + (lp === 'Gn' ? '' : norm(lp) + '-') + (base || out.length + 1), libro: lp, titulo: t || null, pasajes: [], total: 0, leidos: 0, siguiente: false };
        porT.set(kt, g); out.push(g);
      }
      const g = porT.get(kt), le = L.has(p.id);
      g.pasajes.push({ pasaje: p, n: i + 1, leido: le });
      g.total++; if (le) g.leidos++; if (p.id === sigId) g.siguiente = true;
    });
    out.forEach(g => {
      g.estado = g.leidos === g.total ? 'leido' : (g.leidos || g.siguiente) ? 'en-curso' : 'pendiente';
      g.inicio = g.pasajes[0].pasaje.inicio; g.fin = g.pasajes[g.pasajes.length - 1].pasaje.fin;
    });
    return out;
  }
  // Alcance de los datos ("Génesis 1–50"), calculado de los capítulos presentes.
  // Con varios libros: "Génesis 1–50 y Éxodo 1–40".
  function alcance(d) {
    const caps = ((d && d.capitulos) || []).filter(c => Number.isFinite(+c.cap));
    if (!caps.length) return { libro: 'Génesis', desde: null, hasta: null, texto: 'Génesis', corto: 'Gn', libros: [] };
    const partes = libros(d).map(l => {
      const cs = caps.filter(c => libroIdDe(d, c.libro) === l.id).map(c => +c.cap);
      if (!cs.length) return null;
      const a = Math.min(...cs), b = Math.max(...cs), r = a === b ? `${a}` : `${a}–${b}`;
      return { id: l.id, libro: l.nombre, desde: a, hasta: b, texto: `${l.nombre} ${r}`, corto: `${l.id} ${r}` };
    }).filter(Boolean);
    const unir = xs => xs.length < 2 ? xs.join('') : xs.slice(0, -1).join(', ') + ' y ' + xs[xs.length - 1];
    const p0 = partes[0];
    return { libro: p0.libro, desde: p0.desde, hasta: p0.hasta, texto: unir(partes.map(x => x.texto)), corto: unir(partes.map(x => x.corto)), libros: partes };
  }
  function pasajeDe(d, ref) {
    const k = clave(ref);
    if (k === null) return null;
    return pasajes(d).find(p => clave(p.inicio) <= k && k <= clave(p.fin)) || null;
  }
  function versiculosDe(d, pasaje) {
    if (!pasaje) return [];
    const a = clave(pasaje.inicio), b = clave(pasaje.fin);
    return todosLosVersiculos(d).filter(v => v.clave >= a && v.clave <= b);
  }
  const todosLosVersiculos = d => memo(d || {}, 'versiculos', () => {
    const out = [];
    for (const c of ((d && d.capitulos) || [])) {
      const lb = libroIdDe(d, c.libro), o = ordDe(lb) * 1e6;
      for (const v of (c.versiculos || [])) out.push({ libro: lb, cap: c.cap, n: v.n, texto: v.texto || '', ref: refTxt(c.cap, v.n, lb), clave: o + c.cap * 1000 + v.n });
    }
    return out.sort((x, y) => x.clave - y.clave);
  });

  // Menciones de personas (tipo 'persona') o lugares ('lugar') en un versículo: las de los datos si son
  // válidas; si no hay, se buscan los nombres de quienes tienen ese versículo en sus refs.
  const reNombre = new Map();
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
      for (const nom of (tipo === 'lugar' ? [...new Set([p.nombre, p.nombre_rv1909].filter(Boolean))] : nombresDe(p))) {
        if (!reNombre.has(nom)) reNombre.set(nom, new RegExp('(^|[^\\p{L}])(' + nom.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')(?![\\p{L}])', 'gu'));
        const re = reNombre.get(nom); re.lastIndex = 0;
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
    const orden = [...ks].sort((a, b) => a - b);
    const ids = [], idsV = new Set();
    orden.forEach(k => (I.porRef.get(k) || []).forEach(id => { if (!idsV.has(id)) { idsV.add(id); ids.push(id); } }));
    const vistos = new Set();
    const vinculos = orden.flatMap(k => I.relPorRef.get(k) || []).filter(r => {
      const k = r.tipo + '|' + (r.tipo === 'conyuge' ? [r.de, r.a].sort().join('+') : r.de + '>' + r.a);
      return !vistos.has(k) && vistos.add(k);
    });
    const grupos = new Map();
    orden.flatMap(k => I.edadesPorRef.get(k) || []).filter(e => e.tipo !== 'en_evento' && num(e.valor) !== null).forEach(e => {
      const k = e.persona + '|' + e.tipo;
      if (!grupos.has(k)) grupos.set(k, { persona: e.persona, tipo: e.tipo, ref: e.ref, TM: null, LXX: null });
      if (e.tradicion === 'TM' || e.tradicion === 'LXX') grupos.get(k)[e.tradicion] = Object.assign({}, e, { valor: num(e.valor) });
    });
    const edadesV = [...grupos.values()].map(g => Object.assign(g, {
      difiere: !!(g.TM && g.LXX && g.TM.valor !== g.LXX.valor), solo: g.TM && !g.LXX ? 'TM' : !g.TM && g.LXX ? 'LXX' : null }));
    const lugs = [];
    orden.forEach(k => (I.lugaresPorRef.get(k) || []).forEach(id => { if (!lugs.includes(id) && I.lugares.has(id)) lugs.push(id); }));
    return { personas: ids.map(id => ({ id, contexto: contextoPersona(d, id) })), vinculos, edades: edadesV,
      eventos: edadesEnEvento(d, orden.map(refDeClave)),
      sinNombre: ids.filter(id => (I.personas.get(id) || {}).sin_nombre), lugares: lugs };
  }
  // ¿Tiene el versículo vínculos, edades, alusiones sin nombre o lugares? (marca al margen; solo índices)
  function tieneApoyo(d, ref) {
    const I = indice(d), k = clave(ref);
    if (k === null) return false;
    if ((I.relPorRef.get(k) || []).length) return true;
    if ((I.edadesPorRef.get(k) || []).some(e => num(e.valor) !== null)) return true;
    for (const id of (I.lugaresPorRef.get(k) || [])) if (I.lugares.has(id)) return true;
    for (const id of (I.porRef.get(k) || [])) if ((I.personas.get(id) || {}).sin_nombre) return true;
    return false;
  }
  // Personas del acompañante separadas: las que aparecen por primera vez en el pasaje y el resto.
  function quienAparece(d, pasaje, ids) {
    const I = indice(d), a = pasaje ? clave(pasaje.inicio) : null, b = pasaje ? clave(pasaje.fin) : null;
    const esNueva = id => { const k = I.primera.get(id); return a !== null && k !== undefined && k >= a && k <= b; };
    return { nuevas: ids.filter(esNueva), resto: ids.filter(id => !esNueva(id)) };
  }

  /* ---- Lugares y mapa ---- */
  const lugar = (d, id) => indice(d).lugares.get(id) || null;
  function lugaresDeRefs(d, refs) {
    const I = indice(d), out = [], vistos = new Set();
    [...new Set([].concat(refs || []).map(clave).filter(k => k !== null))].sort((a, b) => a - b)
      .forEach(k => (I.lugaresPorRef.get(k) || []).forEach(id => { if (!vistos.has(id) && I.lugares.has(id)) { vistos.add(id); out.push(id); } }));
    return out;
  }
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
  // Por prioridad (mayor primero); `max` limita cuántas se colocan (el mapa lo sube al acercar).
  function colocarEtiquetas(items, ancho, alto, max) {
    const puestos = items.map(it => ({ x: it.x - 6, y: it.y - 6, w: 12, h: 12, id: it.id })), out = [];
    const tope = Number.isFinite(max) ? max : Infinity;
    const choca = (r, id) => puestos.some(p => p.id !== id && r.x < p.x + p.w && p.x < r.x + r.w && r.y < p.y + p.h && p.y < r.y + r.h);
    for (const it of items.slice().sort((a, b) => (b.prioridad || 0) - (a.prioridad || 0))) {
      if (out.length >= tope) break;
      const w = String(it.texto).length * 6.6 + 4, h = 14, g = 9;
      const ops = [{ x: it.x + g, y: it.y - h / 2, anc: 'start' }, { x: it.x - g - w, y: it.y - h / 2, anc: 'end' },
        { x: it.x - w / 2, y: it.y - g - h, anc: 'middle' }, { x: it.x - w / 2, y: it.y + g, anc: 'middle' }];
      for (const o of ops) {
        const r = { x: o.x, y: o.y, w, h };
        if (r.x < 0 || r.y < 0 || r.x + w > ancho || r.y + h > alto || choca(r, it.id)) continue;
        puestos.push(Object.assign({ id: '#' + it.id }, r));
        out.push({ id: it.id, texto: it.texto, x: o.anc === 'start' ? o.x : o.anc === 'end' ? o.x + w : o.x + w / 2, y: o.y + h - 3, anc: o.anc, caja: r });
        break;
      }
    }
    return out;
  }
  // Cuántas etiquetas caben según el acercamiento (z = escala actual / escala al encuadrar).
  const etiquetasPorZoom = (z, total) => Math.min(total, Math.max(8, Math.round(12 * Math.max(1, z) * Math.max(1, z))));
  // Importancia de un lugar para su etiqueta: veces que se nombra (refs) y confianza.
  const prioridadLugar = l => Math.min(99, ((l && l.refs) || []).length) * 10 + ({ alta: 3, media: 2, baja: 1 }[confianzaLugar(l)] || 0);

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
      if (!e || clave(e.ref) !== clave('Gn 7:6') || (e.tradicion && e.tradicion !== trad) || num(e.valor) === null) continue;
      const f = filas.find(x => x.id === e.persona);
      if (f && f.nacimiento !== null) return { ano: f.nacimiento + num(e.valor), persona: e.persona, valor: num(e.valor), ref: e.ref, cita: e.cita || '' };
    }
    return null;
  }

  /* ---- Cronología: todo año es CÁLCULO (años desde la creación de Adán) ---- */
  function crono(d) {
    return memo(d || {}, 'crono', () => {
      const c = d && d.cronologia;
      if (!c || !Array.isArray(c.eventos)) return null;
      const eventos = c.eventos.filter(e => e && e.id);
      return { unidad: c.unidad || 'años desde la creación de Adán (cálculo)', eventos, porId: new Map(eventos.map(e => [e.id, e])),
        supuestos: (c.supuestos || []).filter(s => s && s.id && Array.isArray(s.opciones) && s.opciones.length),
        combinaciones: (c.combinaciones || []).filter(Boolean), hitos: (c.hitos_sin_fecha || []).filter(h => h && h.titulo) };
    });
  }
  // Elección de cada supuesto: la guardada si es válida; si no, la opción por defecto.
  function elecciones(d, guardadas) {
    const C = crono(d), out = {};
    if (C) C.supuestos.forEach(s => {
      const g = guardadas && guardadas[s.id], ok = id => s.opciones.some(o => o.id === id);
      out[s.id] = ok(g) ? g : ok(s.defecto) ? s.defecto : s.opciones[0].id;
    });
    return out;
  }
  // Id de la combinación (tradición + supuestos) con la que se leen los `anios` de cada evento.
  function combinacion(d, trad, eleg) {
    const C = crono(d); if (!C) return null;
    const e = elecciones(d, eleg);
    const c = C.combinaciones.find(x => x.tradicion === trad && C.supuestos.every(s => (x.supuestos || {})[s.id] === e[s.id]));
    return c && c.id ? c.id : [trad].concat(C.supuestos.map(s => e[s.id])).join('|');
  }
  const anioEvento = (d, id, combo) => { const C = crono(d), e = C && C.porId.get(id); return e && e.anios ? num(e.anios[combo]) : null; };
  // Cadena completa desde el origen siguiendo `depende_de`: [{evento, titulo, ref, anio (subtotal), pasos}].
  function cadenaEvento(d, id, combo) {
    const C = crono(d), out = [], vis = new Set();
    if (!C) return out;
    for (let e = C.porId.get(id); e && !vis.has(e.id); e = e.depende_de ? C.porId.get(e.depende_de) : null) {
      vis.add(e.id);
      out.unshift({ evento: e.id, titulo: e.titulo || e.id, ref: e.ref || '', anio: anioEvento(d, e.id, combo), pasos: (e.pasos || []).filter(Boolean) });
    }
    return out;
  }
  // Nacimiento y muerte (años desde Adán) por persona en una combinación.
  function vidasCrono(d, combo) {
    return memo(d || {}, 'vidasC|' + combo, () => {
      const C = crono(d), m = new Map(), I = indice(d);
      // En un nacimiento también figuran los padres (Sara en "Nace Isaac"): no nacen ese año.
      const esProgenitor = (id, ps) => (I.hijos.get(id) || []).some(r => r.a !== id && ps.includes(r.a));
      if (C) C.eventos.forEach(e => {
        if (e.tipo !== 'nacimiento' && e.tipo !== 'muerte') return;
        const a = anioEvento(d, e.id, combo), ps = e.personas || [];
        ps.forEach(id => {
          if (e.tipo === 'nacimiento' && esProgenitor(id, ps)) return;
          if (!m.has(id)) m.set(id, { persona: id, nacimiento: null, muerte: null, evNac: null, evMuerte: null });
          const x = m.get(id);
          if (e.tipo === 'nacimiento') { x.nacimiento = a; x.evNac = e.id; } else { x.muerte = a; x.evMuerte = e.id; }
        });
      });
      return m;
    });
  }
  // Quién vivía en un año: nacimiento ≤ año ≤ muerte (ambos conocidos), con su edad entonces.
  function vivosEn(d, anio, combo) {
    if (anio === null || anio === undefined) return [];
    const out = [];
    for (const x of vidasCrono(d, combo).values())
      if (x.nacimiento !== null && x.muerte !== null && x.nacimiento <= anio && anio <= x.muerte) out.push(Object.assign({ edad: anio - x.nacimiento }, x));
    return out.sort((a, b) => a.nacimiento - b.nacimiento);
  }
  // Contemporáneos: vidas que se solapan con la de `id`; primero la línea principal, luego el solape más largo.
  function contemporaneos(d, id, combo, max) {
    const m = vidasCrono(d, combo), x = m.get(id);
    if (!x || x.nacimiento === null) return [];
    const fin = x.muerte === null ? x.nacimiento : x.muerte, lp = lineaPrincipal(d), out = [];
    for (const y of m.values()) {
      if (y.persona === id || y.nacimiento === null || y.muerte === null) continue;
      const solape = Math.min(fin, y.muerte) - Math.max(x.nacimiento, y.nacimiento);
      if (solape >= 0) out.push({ persona: y.persona, solape, linea: lp.has(y.persona) });
    }
    return out.sort((a, b) => (b.linea - a.linea) || b.solape - a.solape).slice(0, max || 8);
  }
  const porVersiculo = (a, b) => (clave(a.ref) || 0) - (clave(b.ref) || 0);
  function eventosDeRefs(d, refs) {
    const C = crono(d), ks = new Set([].concat(refs || []).map(clave).filter(k => k !== null));
    return C ? C.eventos.filter(e => ks.has(clave(e.ref))).sort(porVersiculo) : [];
  }
  function eventosDePasaje(d, p) {
    const C = crono(d); if (!C || !p) return [];
    const a = clave(p.inicio), b = clave(p.fin);
    return C.eventos.filter(e => { const k = clave(e.ref); return k !== null && k >= a && k <= b; }).sort(porVersiculo);
  }
  // Eventos fechados antes y después de un tramo, por ORDEN DE LECTURA (no es un dato del texto).
  function vecinosFechados(d, desde, hasta, combo) {
    const C = crono(d), a = clave(desde), b = clave(hasta === undefined ? desde : hasta);
    let anterior = null, siguiente = null;
    if (C && a !== null && b !== null) C.eventos.forEach(e => {
      const k = clave(e.ref), y = anioEvento(d, e.id, combo);
      if (k === null || y === null) return;
      const x = { evento: e.id, titulo: e.titulo || e.id, ref: e.ref, anio: y, k };
      if (k < a && (!anterior || k > anterior.k || (k === anterior.k && y > anterior.anio))) anterior = x;
      if (k > b && (!siguiente || k < siguiente.k || (k === siguiente.k && y < siguiente.anio))) siguiente = x;
    });
    return { anterior, siguiente };
  }
  // "N años después de <evento del que depende>".
  function despuesDe(d, id, combo) {
    const C = crono(d), e = C && C.porId.get(id), p = e && e.depende_de && C.porId.get(e.depende_de);
    if (!p) return null;
    const a = anioEvento(d, id, combo), b = anioEvento(d, p.id, combo);
    return a === null || b === null ? null : { evento: p.id, titulo: p.titulo || p.id, anios: a - b };
  }
  function compararEvento(d, id, eleg) {
    const TM = anioEvento(d, id, combinacion(d, 'TM', eleg)), LXX = anioEvento(d, id, combinacion(d, 'LXX', eleg));
    return { TM, LXX, dif: TM !== null && LXX !== null ? LXX - TM : null };
  }
  const esDiluvio = e => !!e && /diluvio/i.test((e.id || '') + ' ' + (e.titulo || ''));
  // Línea de tiempo por secciones de lectura: eventos por año (los sin año al final) y, aparte, los hitos sin fecha.
  function lineaDeTiempo(d, combo) {
    const C = crono(d); if (!C) return [];
    const secs = seccionesPlan(d, [], null), dePasaje = new Map(), grupos = new Map();
    secs.forEach(g => { grupos.set(g.id, { id: g.id, titulo: g.titulo, eventos: [], hitos: [] }); g.pasajes.forEach(x => dePasaje.set(x.pasaje.id, g.id)); });
    const grupo = ref => { const p = pasajeDe(d, ref), id = (p && dePasaje.get(p.id)) || 'otros'; if (!grupos.has(id)) grupos.set(id, { id, titulo: 'Otros', eventos: [], hitos: [] }); return grupos.get(id); };
    // Sin versículo propio (p. ej. un dato solo de la LXX): se sitúa con el suceso del que depende.
    const refDe = e => { for (let x = e, n = 0; x && n < 50; x = x.depende_de && C.porId.get(x.depende_de), n++) if (clave(x.ref) !== null) return x.ref; return null; };
    C.eventos.forEach(e => { const r = refDe(e); grupo(r).eventos.push({ tipo: 'evento', evento: e, anio: anioEvento(d, e.id, combo), k: clave(r) || 0 }); });
    C.hitos.forEach(h => grupo(h.ref).hitos.push({ tipo: 'hito', hito: h, k: clave(h.ref) || 0 }));
    const out = [];
    for (const g of grupos.values()) {
      if (!g.eventos.length && !g.hitos.length) continue;
      // Los hitos sin fecha NO entran en el eje (sugerirían un año que el texto no da): van aparte, en orden de lectura.
      const items = g.eventos.sort((a, b) => (a.anio === null ? Infinity : a.anio) - (b.anio === null ? Infinity : b.anio) || a.k - b.k);
      out.push({ id: g.id, titulo: g.titulo, items, hitos: g.hitos.sort((a, b) => a.k - b.k) });
    }
    return out;
  }

  /* ---- Personajes: colección, ficha ampliada y curiosidades (todo derivado de los datos) ---- */
  // Coleccionables: personas con nombre que aparecen en algún versículo, en orden de primera aparición.
  const coleccionables = d => memo(d || {}, 'colec', () => {
    const I = indice(d);
    return ((d && d.personas) || []).filter(p => p && p.id && !p.sin_nombre && I.primera.has(p.id)).map(p => p.id)
      .sort((a, b) => I.primera.get(a) - I.primera.get(b));
  });
  // Claves de los versículos en que aparece cada persona según los datos (refs y menciones).
  const versosPersona = d => memo(d || {}, 'versosP', () => {
    const m = new Map();
    for (const [k, s] of indice(d).porRef) for (const id of s) { if (!m.has(id)) m.set(id, []); m.get(id).push(k); }
    m.forEach(ks => ks.sort((a, b) => a - b));
    return m;
  });
  // Rareza: solo cuántos versículos de los datos la nombran (no mide importancia).
  const RAREZAS = [{ id: 'rara', nombre: 'Rara', min: 1, max: 1 }, { id: 'poco-comun', nombre: 'Poco común', min: 2, max: 9 },
    { id: 'comun', nombre: 'Común', min: 10, max: 29 }, { id: 'protagonista', nombre: 'Protagonista', min: 30, max: Infinity }];
  function rareza(d, id) {
    const n = (versosPersona(d).get(id) || []).length;
    return Object.assign({ versiculos: n }, RAREZAS.find(x => n >= x.min && n <= x.max) || RAREZAS[0]);
  }
  // Personas coleccionables que aparecen en un pasaje (orden de primera aparición).
  function personasDePasaje(d, p) {
    if (!p) return [];
    return memo(d || {}, 'pdp|' + p.inicio + '|' + p.fin, () => {
      const a = clave(p.inicio), b = clave(p.fin), V = versosPersona(d);
      return coleccionables(d).filter(id => (V.get(id) || []).some(k => k >= a && k <= b));
    });
  }
  // Colección: personas de los pasajes leídos.
  function coleccion(d, leidos) {
    const L = new Set(leidos || []), out = new Set();
    pasajes(d).forEach(p => { if (L.has(p.id)) personasDePasaje(d, p).forEach(id => out.add(id)); });
    return out;
  }
  // Las que entran al marcar `pasajeId` como leído, dado lo ya leído.
  function nuevasAlLeer(d, leidos, pasajeId) {
    const p = pasajes(d).find(x => x.id === pasajeId); if (!p) return [];
    const antes = coleccion(d, [].concat(leidos || []).filter(x => x !== pasajeId));
    return personasDePasaje(d, p).filter(id => !antes.has(id));
  }
  const libroDeClave = k => idPorOrd.get(Math.floor(k / 1e6));
  // Fichas de la colección: sin desbloquear solo se da el capítulo de la primera aparición.
  function fichasColeccion(d, leidos) {
    const obt = coleccion(d, leidos), I = indice(d), V = versosPersona(d);
    return coleccionables(d).map(id => {
      const k = I.primera.get(id), p = I.personas.get(id) || {};
      return { id, desbloqueada: obt.has(id), primera: refDeClave(k), primeraCap: `${libroDeClave(k)} ${Math.floor(k / 1000) % 1000}`,
        libros: unicos((V.get(id) || []).map(libroDeClave)), sexo: p.sexo === 'f' || p.sexo === 'm' ? p.sexo : '?', rareza: rareza(d, id) };
    });
  }
  // Pasajes en que aparece una persona, con cuántos versículos suyos tiene cada uno.
  function pasajesDePersona(d, id) {
    const ks = versosPersona(d).get(id) || [];
    return pasajes(d).map(p => { const a = clave(p.inicio), b = clave(p.fin); return { pasaje: p, versiculos: ks.filter(k => k >= a && k <= b).length }; }).filter(x => x.versiculos);
  }
  // Lugares nombrados en los mismos versículos que la persona (coincidencia en el texto, no un vínculo afirmado).
  function lugaresDePersona(d, id, max) {
    const I = indice(d), cuenta = new Map();
    (versosPersona(d).get(id) || []).forEach(k => (I.lugaresPorRef.get(k) || []).forEach(l => { if (I.lugares.has(l)) cuenta.set(l, (cuenta.get(l) || 0) + 1); }));
    return [...cuenta.entries()].sort((a, b) => b[1] - a[1]).slice(0, max || 12).map(([lugar, veces]) => ({ lugar, veces }));
  }
  // Descendientes con su número de generaciones y el camino desde `id`.
  function descendientes(d, id) {
    return memo(d || {}, 'desc|' + id, () => {
      const I = indice(d), m = new Map(), cola = [[id, 0, [id]]];
      while (cola.length) {
        const [x, g, cam] = cola.shift();
        (I.hijos.get(x) || []).forEach(r => { if (r.a !== id && !m.has(r.a)) { m.set(r.a, { gen: g + 1, camino: cam.concat(r.a) }); cola.push([r.a, g + 1, cam.concat(r.a)]); } });
      }
      return m;
    });
  }
  const tradDeCombo = (d, combo) => { const C = crono(d), c = C && C.combinaciones.find(x => x.id === combo); return (c && c.tradicion) || String(combo || '').split('|')[0] || 'TM'; };
  // Curiosidades (CÁLCULO) para una combinación de tradición y supuestos. Cada una: {id, tipo, personas,
  // protagonistas, texto, valor, pasos [{texto, ref}], refs}. Solo salen de los datos; nada se redacta a mano.
  function curiosidades(d, combo) {
    return memo(d || {}, 'curio|' + combo, () => {
      const C = crono(d); if (!C) return [];
      const I = indice(d), m = vidasCrono(d, combo), trad = tradDeCombo(d, combo), out = [];
      const nom = id => (I.personas.get(id) || {}).nombre || id;
      const ev = id => C.porId.get(id) || {};
      const completas = [...m.values()].filter(x => x.nacimiento !== null && x.muerte !== null);
      const pNac = x => ({ texto: `${nom(x.persona)} nace en el año ${x.nacimiento}`, ref: ev(x.evNac).ref || '' });
      const pMuerte = x => ({ texto: `${nom(x.persona)} muere en el año ${x.muerte}`, ref: ev(x.evMuerte).ref || '' });
      const refsDe = pasos => unicos(pasos.map(p => p.ref).filter(r => clave(r) !== null));
      const an = n => `${n} ${n === 1 ? 'año' : 'años'}`;
      const lp = lineaPrincipal(d), enLinea = completas.filter(x => lp.has(x.persona));
      // 1. Vidas a la vez: con quien nace más tarde de la línea principal y aún coincide (no hijos ni nietos).
      enLinea.forEach(x => {
        const D = descendientes(d, x.persona);
        const y = enLinea.filter(y => y.nacimiento > x.nacimiento && Math.min(x.muerte, y.muerte) - y.nacimiento > 0 && !((D.get(y.persona) || {}).gen <= 2))
          .sort((a, b) => b.nacimiento - a.nacimiento)[0];
        if (!y) return;
        const fin = Math.min(x.muerte, y.muerte), n = fin - y.nacimiento;
        const pasos = [pNac(x), pMuerte(x), pNac(y), pMuerte(y), { texto: `A la vez: desde ${y.nacimiento} hasta ${fin} = ${an(n)}`, ref: '' }];
        out.push({ id: `solape|${x.persona}|${y.persona}`, tipo: 'solape', personas: [x.persona, y.persona], protagonistas: [x.persona, y.persona], valor: n,
          texto: `${nom(x.persona)} y ${nom(y.persona)} vivieron a la vez ${an(n)}`, pasos, refs: refsDe(pasos) });
      });
      // 2. Muere el mismo año que un suceso fechado en el que no participa.
      completas.forEach(x => {
        C.eventos.filter(e => e.tipo !== 'nacimiento' && e.tipo !== 'muerte' && !(e.personas || []).includes(x.persona) && anioEvento(d, e.id, combo) === x.muerte).forEach(e => {
          const pasos = [pNac(x)].concat((ev(x.evMuerte).pasos || []).map(s => ({ texto: s.texto, ref: s.ref || '' })), [pMuerte(x), { texto: `«${e.titulo || e.id}»: año ${x.muerte}`, ref: e.ref || '' }]);
          out.push({ id: `muerte-evento|${x.persona}|${e.id}`, tipo: 'muerte-evento', personas: [x.persona], protagonistas: [x.persona], valor: x.muerte,
            texto: `${nom(x.persona)} muere en el año ${x.muerte}, el mismo año que «${e.titulo || e.id}»`, pasos, refs: refsDe(pasos) });
        });
      });
      // 3. El más longevo de quienes tienen edad total en un mismo capítulo (una genealogía), sin empate.
      const grupos = new Map();
      coleccionables(d).forEach(id => {
        const e = edad(d, id, 'total', trad), r = e && parseRef(e.ref);
        if (!e || !r) return;
        const g = `${r.libro} ${r.cap}`;
        if (!grupos.has(g)) grupos.set(g, []);
        grupos.get(g).push({ id, valor: e.valor, ref: e.ref, derivado: e.derivado });
      });
      grupos.forEach((xs, g) => {
        if (xs.length < 3) return;
        const max = Math.max(...xs.map(x => x.valor)), top = xs.filter(x => x.valor === max);
        if (top.length !== 1) return;
        const pasos = xs.slice().sort((a, b) => b.valor - a.valor).map(x => ({ texto: `${nom(x.id)}: ${x.valor} años${x.derivado ? ' (suma de sus dos edades)' : ''}`, ref: x.ref }));
        out.push({ id: `longevo|${g}|${top[0].id}`, tipo: 'longevo', personas: xs.map(x => x.id), protagonistas: [top[0].id], valor: max,
          texto: `${nom(top[0].id)} es quien más vive de los ${xs.length} cuya edad total da ${g} (${trad}): ${max} años`, pasos, refs: refsDe(pasos) });
      });
      // 4. Sobrevive a descendientes suyos (con vida completa en el cálculo).
      completas.forEach(x => {
        const D = descendientes(d, x.persona);
        const ys = completas.filter(y => D.has(y.persona) && y.muerte < x.muerte)
          .sort((a, b) => D.get(b.persona).gen - D.get(a.persona).gen || lp.has(b.persona) - lp.has(a.persona) || b.nacimiento - a.nacimiento);
        if (!ys.length) return;
        const y = ys[0], cam = D.get(y.persona).camino.map(nom).join(' → ');
        const pasos = [pMuerte(x)].concat(ys.slice().sort((a, b) => a.muerte - b.muerte).map(pMuerte), [{ texto: `Descendencia: ${cam} (${D.get(y.persona).gen} generaciones)`, ref: '' }]);
        out.push({ id: `sobrevive|${x.persona}`, tipo: 'sobrevive', personas: [x.persona].concat(ys.map(z => z.persona)), protagonistas: [x.persona, y.persona], valor: ys.length,
          texto: `${nom(x.persona)} sobrevive a ${ys.length === 1 ? `su descendiente ${nom(y.persona)}` : `${ys.length} de sus descendientes, entre ellos ${nom(y.persona)}`}: ${nom(y.persona)} muere en el año ${y.muerte} y ${nom(x.persona)} en el ${x.muerte}`,
          pasos, refs: refsDe(pasos) });
      });
      return out;
    });
  }
  // De una persona: primero aquellas de las que es protagonista principal, luego por tipo.
  const curiosidadesDe = (d, id, combo) => curiosidades(d, combo).filter(c => c.personas.includes(id)).map((c, i) => ({ c, i,
    k: (c.protagonistas[0] === id ? 0 : c.protagonistas.includes(id) ? 10 : 20) + PRIO_CURIO[c.tipo] }))
    .sort((a, b) => a.k - b.k || a.i - b.i).map(x => x.c);
  // «¿Sabías que…?» por pasaje (máx. `max`): alguno de sus protagonistas aparece en el pasaje y todos ya han
  // aparecido; primero las que tienen un versículo en el pasaje y las aún no mostradas; nunca la misma que en el pasaje anterior.
  const PRIO_CURIO = { 'muerte-evento': 0, longevo: 1, sobrevive: 2, solape: 3 };
  function sabiasQue(d, combo, max) {
    return memo(d || {}, 'sabias|' + combo + '|' + (max || 2), () => {
      const cs = curiosidades(d, combo), I = indice(d), res = new Map(), vistas = new Set();
      let prev = new Set();
      pasajes(d).forEach(p => {
        const a = clave(p.inicio), b = clave(p.fin), aqui = new Set(personasDePasaje(d, p));
        const elegidas = cs.filter(c => !prev.has(c.id) && c.protagonistas.some(id => aqui.has(id)) && c.protagonistas.every(id => (I.primera.get(id) || Infinity) <= b))
          .map(c => ({ c, s: (c.refs.some(r => { const k = clave(r); return k >= a && k <= b; }) ? 2 : 0) + (vistas.has(c.id) ? 0 : 1) }))
          .filter(x => x.s > 0).sort((x, y) => y.s - x.s || PRIO_CURIO[x.c.tipo] - PRIO_CURIO[y.c.tipo]).slice(0, max || 2).map(x => x.c);
        elegidas.forEach(c => vistas.add(c.id));
        res.set(p.id, elegidas);
        prev = new Set(elegidas.map(c => c.id));
      });
      return res;
    });
  }
  // Enlaces para profundizar (FUENTE EXTERNA): búsquedas estables; no se copia su contenido.
  function enlacesExternos(d, id) {
    const p = persona(d, id); if (!p || p.sin_nombre) return [];
    const en = String(id).replace(/_\d+$/, '').replace(/_/g, ' '), letra = norm(en).charAt(0);
    return [
      { id: 'wikipedia', titulo: 'Wikipedia en español', detalle: `búsqueda «${p.nombre} personaje bíblico»`, url: 'https://es.wikipedia.org/w/index.php?search=' + encodeURIComponent(`${p.nombre} personaje bíblico`) },
      { id: 'easton', titulo: "Easton's Bible Dictionary (1897, dominio público)", detalle: `en inglés, vía Wikisource; búsqueda «${en}»`, url: 'https://en.wikisource.org/w/index.php?search=' + encodeURIComponent(en) + '&prefix=' + encodeURIComponent("Easton's Bible Dictionary (1897)/") },
      { id: 'smith', titulo: "Smith's Bible Dictionary (dominio público)", detalle: `en inglés, vía Bible Study Tools; índice de la letra ${letra.toUpperCase()}`, url: 'https://www.biblestudytools.com/dictionaries/smiths-bible-dictionary/?letter=' + encodeURIComponent(letra) }
    ].filter(x => letra || x.id !== 'smith');
  }

  /* ---- Textos originales (datos/originales.js y datos/griego-swete.js, cargados bajo demanda) ---- */
  // "Ex 1:1-Ex 1:22", "Ex 1:1-22", "Gn 1:1-2:3", "Gn 1" (capítulo) o "Ex" (libro) → { a, b } en claves de versículo.
  function rangoClaves(s) {
    const [x, y] = String(s == null ? '' : s).split(/\s*[-–—]\s*/);
    if (!x || !x.trim()) return null;
    const solo = /^\s*([1-3]?\s?[A-Za-zÀ-ÿ]+)\.?\s*$/.exec(x);
    if (solo && !y) { const o = ordDe(libroCanon(solo[1])); return o ? { a: o * 1e6 + 1001, b: o * 1e6 + 999999 } : null; }
    const A = parseRef(x); if (!A) return null;
    const o = ordDe(A.libro);
    let B;
    if (!y) B = { libro: A.libro, cap: A.cap, v: A.v };
    else if (/[A-Za-zÀ-ÿ]/.test(y)) B = parseRef(y);
    else if (y.includes(':')) { const m = /(\d+)\s*:\s*(\d+)/.exec(y); B = m && { libro: A.libro, cap: +m[1], v: +m[2] }; }
    else B = A.v ? { libro: A.libro, cap: A.cap, v: +y } : { libro: A.libro, cap: +y, v: null };
    if (!B || !ordDe(B.libro)) return null;
    const a = o * 1e6 + A.cap * 1000 + (A.v || 1), b = ordDe(B.libro) * 1e6 + B.cap * 1000 + (B.v || 999);
    return a <= b ? { a, b } : { a: b, b: a };
  }
  // Extremos (claves) de una lista de refs de versículo.
  const extremos = refs => { const ks = (refs || []).map(clave).filter(k => k !== null); return ks.length ? { a: Math.min(...ks), b: Math.max(...ks) } : null; };
  // Testigos (códices, rollos…) que contienen alguna parte de los versículos dados, en el orden de los datos.
  function testigosDe(O, refs) {
    const r = extremos(refs); if (!r) return [];
    return ((O && O.testigos) || []).filter(t => (t.contiene || []).some(s => { const c = rangoClaves(s); return c && c.a <= r.b && r.a <= c.b; }));
  }
  // Variantes cuyo versículo (o rango) cae en los versículos dados.
  function variantesDe(O, refs) {
    const ks = new Set((refs || []).map(clave).filter(k => k !== null));
    return ((O && O.variantes) || []).filter(v => { const c = rangoClaves(v.ref); if (!c) return false; for (const k of ks) if (k >= c.a && k <= c.b) return true; return false; });
  }
  // Ref de la numeración hebrea solo cuando difiere de la de la RV ("Gn 31:55" → "Gn 32:1"); null si coincide o falta.
  function numeracionHebrea(ref, r) {
    if (!r) return null;
    const a = parseRef(ref), b = parseRef(r);
    if (!a || !b || (a.libro === b.libro && a.cap === b.cap && a.v === b.v)) return null;
    return a.libro === b.libro ? `${b.cap}:${b.v}` : `${b.libro} ${b.cap}:${b.v}`;
  }
  // Filas alineadas por versículo de la RV: { ref, cap, n, rv, he, heNum, gr }. Lo que falta queda en null.
  function alinearOriginales(d, pasaje, O, G) {
    const H = (O && O.hebreo) || {}, T = (G && G.texto) || {};
    return versiculosDe(d, pasaje).map(v => {
      const h = H[v.ref];
      return { ref: v.ref, cap: v.cap, n: v.n, rv: v.texto || null, he: (h && h.t) || null, heNum: h ? numeracionHebrea(v.ref, h.r) : null, gr: T[v.ref] || null };
    });
  }
  const videosDeLibro = (O, libro) => ((O && O.videos) || []).filter(v => libroCanon(v.libro) === libroCanon(libro) && esIdYoutube(v.youtube_id));
  const esIdYoutube = id => /^[A-Za-z0-9_-]{11}$/.test(String(id || ''));
  // Escritura de un texto original, para lang/dir: hebreo, griego o ninguno.
  const escritura = t => /[֐-׿]/.test(t || '') ? 'he' : /[Ͱ-Ͽἀ-῿]/.test(t || '') ? 'grc' : null;

  // Texto para la voz sintética: sin acentos de cantilación ni marcas de párrafo (hebreo); griego politónico → monotónico.
  function textoParaVoz(t, idioma) {
    let s = String(t == null ? '' : t);
    if (idioma === 'he') s = s.replace(/[{\[(]\s*[פס]\s*[}\])]/g, ' ').replace(/[֑-ֽ֯׀ׅׄ]/g, '').replace(/־/g, ' ').replace(/׃/g, '.').replace(/[/\\|]/g, ' ');
    else if (idioma === 'el') s = s.normalize('NFD').replace(/[̓̔ͅ]/g, '').replace(/[̀͂]/g, '́').replace(/́+/g, '́').normalize('NFC');
    return s.replace(/\s+/g, ' ').trim();
  }
  // Voz del sistema para un idioma ('es', 'he', 'el'); prefiere la región indicada y las voces locales. null si no hay.
  function vozPara(voces, idioma, region) {
    const base = idioma === 'he' ? ['he', 'iw'] : [idioma];
    const vs = (voces || []).filter(v => base.includes(String(v.lang || '').toLowerCase().replace('_', '-').split('-')[0]));
    if (!vs.length) return null;
    const pref = region ? `${idioma}-${region}`.toLowerCase() : '';
    const punt = v => (pref && String(v.lang).toLowerCase().replace('_', '-') === pref ? 2 : 0) + (v.localService ? 1 : 0) + (v.default ? .5 : 0);
    return vs.slice().sort((a, b) => punt(b) - punt(a))[0];
  }

  /* ---- Recursos (datos/recursos.js): arte, objetos, mapas antiguos, videos y audio ---- */
  // Solo lo que se puede mostrar: con licencia, atribución y fuente, no rechazado y sin imagen si la licencia no lo permite.
  const LIC_RESTRINGIDA = /^(desconocida|derechos reservados)$/i;
  const recursoValido = f => !!(f && f.id && f.titulo && f.licencia && f.atribucion && /^https?:\/\//.test(f.url_fuente || '')
    && f.auditoria !== 'RECHAZAR' && !(f.imagen && LIC_RESTRINGIDA.test(f.licencia)) && Array.isArray(f.rangos));
  const cacheRec = new WeakMap();
  const recursos = R => {
    if (!R || typeof R !== 'object') return [];
    if (!cacheRec.has(R)) cacheRec.set(R, (R.fichas || []).filter(recursoValido));
    return cacheRec.get(R);
  };
  // Versículos (claves) del conjunto que caen dentro de los rangos de la ficha.
  const solape = (f, ks) => ks.reduce((n, k) => n + (f.rangos.some(([a, b]) => k >= a && k <= b) ? 1 : 0), 0);
  const amplitud = f => f.rangos.reduce((n, [a, b]) => n + (b - a), 0);
  // Fichas que tocan esos versículos, de mayor a menor solapamiento; a igualdad, la más concreta y luego el orden del catálogo.
  function recursosDe(R, claves, tipos) {
    const ks = [...new Set((claves || []).filter(k => k !== null && k !== undefined))];
    if (!ks.length) return [];
    return recursos(R).map((f, i) => ({ f, i, n: tipos && !tipos.includes(f.tipo) ? 0 : solape(f, ks) })).filter(x => x.n > 0)
      .sort((x, y) => y.n - x.n || amplitud(x.f) - amplitud(y.f) || x.i - y.i).map(x => x.f);
  }
  // Imagen del pasaje: solo arte, reconstrucción o ilustración con imagen local; la primera es la principal.
  const imagenesDe = (R, claves) => recursosDe(R, claves, ['arte', 'reconstruccion', 'ilustracion']).filter(f => f.imagen);
  // Acompañante: objetos y otras imágenes (sin las ya mostradas arriba) y videos o audio.
  function relacionadosDe(R, claves, excluir) {
    const fuera = new Set(excluir || []), r = recursosDe(R, claves, ['arqueologia', 'arte', 'reconstruccion', 'ilustracion']).filter(f => !fuera.has(f.id));
    return { objetos: r.filter(f => f.tipo === 'arqueologia'), imagenes: r.filter(f => f.tipo !== 'arqueologia'), medios: recursosDe(R, claves, ['video', 'audio']) };
  }
  const mapasAntiguos = R => recursos(R).filter(f => f.tipo === 'mapa_antiguo');
  // Rótulo de certeza según el tipo (principio del proyecto: registro histórico ≠ arte ≠ ilustración ≠ reconstrucción).
  function rotuloRecurso(f) {
    if (!f) return '';
    if (f.tipo === 'arte') return 'Arte · interpretación';
    if (f.tipo === 'reconstruccion') return 'Reconstrucción moderna';
    if (f.tipo === 'ilustracion') return 'Ilustración moderna';
    if (f.tipo === 'mapa_antiguo') return 'Mapa antiguo';
    if (f.tipo === 'arqueologia') return f.relacion === 'contexto' ? 'Contexto de la época' : 'Objeto histórico';
    return 'Fuente externa';
  }

  return { recursos, recursoValido, recursosDe, imagenesDe, relacionadosDe, mapasAntiguos, rotuloRecurso,
    TRADS, TIPOS, norm, rangoClaves, testigosDe, variantesDe, numeracionHebrea, alinearOriginales, videosDeLibro, esIdYoutube, escritura, textoParaVoz, vozPara, crono, elecciones, combinacion, anioEvento, cadenaEvento, vidasCrono, vivosEn, eventosDeRefs, eventosDePasaje,
    coleccionables, rareza, RAREZAS, personasDePasaje, coleccion, nuevasAlLeer, fichasColeccion, pasajesDePersona, lugaresDePersona, descendientes,
    curiosidades, curiosidadesDe, sabiasQue, enlacesExternos, tradDeCombo,
    vecinosFechados, despuesDe, contemporaneos, compararEvento, esDiluvio, lineaDeTiempo, parseRef, clave, claseCerteza, pasajes, pasajeDe, versiculosDe, segmentar, contextoPersona,
    acompanante, tieneApoyo, quienAparece, primerasApariciones, miniArbol, anoDiluvio, seccionesPlan, alcance, nombresDe,
    lugar, lugaresDeRefs, lugaresDePasaje, confianzaLugar, proyeccion, proyectar, desproyectar, encuadre, colocarEtiquetas, etiquetasPorZoom, prioridadLugar,
    indice, persona, hijosDe, encontrar, idAdan, idAbraham, idJacob,
    construirArbol, construirBosque, sinParentesco, enPantallaArbol, mapaArbol, nodoArbol, rutaArbol, arbolInicial, hijosPorMadre, uniones, madreSupuesta, vida, atajosLinea, lineaPrincipal,
    alcanzables, contarMujeres, sinNombre, rutas, tradicionesDe, presenteEn, lineaPorTradicion, fusionarOrden,
    lineaAdanAbraham, edad, diferencias, anosDesdeAdan, ordenPatriarcas, vidas, edadesEnEvento, edadesEnEventoPorPersona, personasEnCapitulo, buscar,
    libros, nombreLibro, libroDe, libroIdDe, refDeClave };
})();

globalThis.BibliaNucleo = Nucleo;

/* ======================= Interfaz ======================= */
if (typeof document !== 'undefined') (function () {
  const N = Nucleo;
  let D = window.BIBLIA_DATOS || null;
  const R = window.BIBLIA_RECURSOS || null; // imágenes, objetos, mapas antiguos y medios (herramientas/recursos.py)
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
  const estado = { trad: store.get('biblia.trad', 'TM'), lineaSolo: false, mujeres: false, hoja: false, pasaje: null, activo: null, foco: null, focoHash: undefined, aviso: '',
    mapaFiltro: '', mapaConf: new Set(['alta', 'media', 'baja']), mapaQ: '', mapaSel: null, abiertos: null, q: '', secAbiertas: new Map(),
    vistaArbol: store.get('biblia.vistaArbol', 'lista') === 'grafico' ? 'grafico' : 'lista', gaZoom: 1, colLibro: '', colSexo: '',
    comparar: store.get('biblia.comparar', false) === true, escuchar: false, videoPedido: null, hablarTrasCarga: null };

  const nombre = id => { const p = N.persona(D, id); return p ? (p.nombre || id) : id; };
  // Enlace a un versículo: #leer/Ex/7/7 (los enlaces antiguos #leer/7/7 se leen como Génesis).
  const hrefRef = r => `#leer/${encodeURIComponent(r.libro || 'Gn')}/${r.cap}${r.v ? '/' + r.v : ''}`;
  const refHTML = ref => { const r = N.parseRef(ref); return r ? `<a class="ref" href="${hrefRef(r)}">${esc(ref)}</a>` : esc(ref); };
  // pre: a quién se refiere (padre, madre…), escrito dentro de la insignia; quien: solo en el título.
  const insignia = (cert, ref, pre, quien) => { const k = N.claseCerteza(cert); return `<span class="insignia ${k}" title="${quien || pre ? esc(quien || pre[0].toUpperCase() + pre.slice(1)) + ': ' : ''}${CERT_DESC[k]}">${pre ? `<span class="ins-pre">${esc(pre)}</span>` : ''}${CERT_TXT[k]}${ref ? ' · ' + refHTML(ref) : ''}</span>`; };
  const btnPersona = id => {
    const p = N.persona(D, id) || {};
    const cls = (p.sexo === 'f' ? ' mujer' : p.sexo === 'm' ? ' hombre' : ' indef') + (p.sin_nombre ? ' sin-nombre' : '');
    return `<button type="button" class="persona-btn${cls}" data-persona="${esc(id)}">${esc(nombre(id))}${p.sin_nombre ? '<span class="marca-sn">sin nombre en el texto</span>' : ''}</button>`;
  };
  const citaHTML = r => r && r.cita ? `<blockquote>${esc(r.cita)}</blockquote>` : '';
  const fuenteNombre = id => { const f = (D.fuentes || []).find(x => x.id === id); return f ? f.nombre : (id || 'sin fuente'); };
  const etiquetaTrad = id => { const t = [...N.tradicionesDe(D, id)]; return t.length === 1 ? `<span class="etiqueta">solo ${esc(t[0])}</span>` : ''; };
  const pasajesLeidos = () => new Set(store.get('biblia.pasajesLeidos', []));
  const rango = p => {
    const a = N.parseRef(p.inicio), b = N.parseRef(p.fin);
    if (a.libro !== b.libro) return `${a.libro} ${a.cap}:${a.v} – ${b.libro} ${b.cap}:${b.v}`;
    return a.cap === b.cap ? (a.v === b.v ? `${a.libro} ${a.cap}:${a.v}` : `${a.libro} ${a.cap}:${a.v}–${b.v}`) : `${a.libro} ${a.cap}:${a.v}–${b.cap}:${b.v}`;
  };
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
    // #leer/Ex (plan de ese libro), #leer/Ex/7/7 (versículo) y los enlaces antiguos #leer/7/7 (Génesis).
    let a = args.filter(x => x !== ''), lbRuta = null;
    if (a[0] && !/^\d+$/.test(a[0])) { lbRuta = N.libroIdDe(D, a[0]); a = a.slice(1); }
    if (a[0]) {
      const lb = lbRuta || 'Gn', cap = +a[0], v = +a[1] || null;
      const p = N.pasajeDe(D, `${lb} ${cap}:${v || 1}`) || ps.find(x => { const r = N.parseRef(x.inicio); return r.libro === lb && r.cap === cap; });
      return vistaPasaje(p, v ? `${cap}:${v}` : null);
    }
    const L = pasajesLeidos(), pos = store.get('biblia.pos', null);
    const actual = pos && ps.find(x => x.id === pos.pasaje);
    const n = ps.filter(p => L.has(p.id)).length;
    const sig = (actual && !L.has(actual.id) ? actual : null) || ps.find(p => !L.has(p.id)) || actual || ps[0];
    const enSig = actual && sig && actual.id === sig.id && pos.v;
    const editorial = ps.some(p => p.titulo_origen === 'editorial');
    // Libros con pasajes; con más de uno, el plan muestra un selector y solo el libro elegido.
    const LB = N.libros(D).map(l => { const pl = ps.filter(p => N.libroDe(p) === l.id); return Object.assign({}, l, { pasajes: pl.length, leidos: pl.filter(p => L.has(p.id)).length }); }).filter(l => l.pasajes);
    const varios = LB.length > 1;
    if (lbRuta && LB.some(l => l.id === lbRuta)) { estado.libro = lbRuta; store.set('biblia.libro', lbRuta); }
    const elegido = [estado.libro, store.get('biblia.libro', null), sig && N.libroDe(sig)].find(id => id && LB.some(l => l.id === id)) || (LB[0] && LB[0].id);
    estado.libro = elegido;
    const libroSel = LB.find(l => l.id === elegido);
    const selector = varios ? `<nav class="libros" aria-label="Libros">${LB.map(l => `<a class="libro-btn" href="#leer/${esc(l.id)}"${l.id === elegido ? ' aria-current="true"' : ''}>
        <span class="libro-nombre">${esc(l.nombre)}</span>
        <span class="libro-meta">${l.capitulos ? `${l.capitulos} capítulos, ` : ''}${l.leidos} de ${l.pasajes} pasajes</span>
        <span class="libro-prog" aria-hidden="true"><span style="width:${Math.round(100 * l.leidos / l.pasajes)}%"></span></span></a>`).join('')}</nav>` : '';
    const itemPasaje = (p, num) => {
      const est = L.has(p.id) ? 'leido' : actual && actual.id === p.id ? 'en-curso' : 'pendiente';
      return `<li class="pasaje ${est}"><a href="#leer/p/${esc(p.id)}"><span class="pasaje-num" aria-hidden="true">${num}</span>
          <span class="pasaje-cuerpo"><span class="pasaje-titulo">${esc(p.titulo)}</span><span class="pasaje-rango">${rango(p)}</span>
          ${p.resumen ? `<span class="pasaje-resumen">${esc(p.resumen)}</span>` : ''}</span>
          <span class="estado ${est}">${ICONO[est]}${ESTADO_TXT[est]}</span></a></li>`;
    };
    const secs = N.seccionesPlan(D, [...L], sig && sig.id, varios ? elegido : undefined);
    const totalSel = secs.reduce((s, g) => s + g.total, 0);
    const plan = secs.length === 1 && !secs[0].titulo
      ? `<ol class="pasajes">${secs[0].pasajes.map(x => itemPasaje(x.pasaje, x.n)).join('')}</ol>`
      : `<p class="meta">${secs.length} ${secs.length === 1 ? 'sección' : 'secciones'}, ${totalSel} pasajes. Pulsa una sección para abrirla o cerrarla.</p>
        <div class="secciones">${secs.map(g => {
          const abierta = estado.secAbiertas.has(g.id) ? estado.secAbiertas.get(g.id) : g.siguiente;
          return `<details class="seccion-plan ${g.estado}" data-sec="${esc(g.id)}"${abierta ? ' open' : ''}>
            <summary><span class="sec-cab"><span class="sec-titulo">${esc(g.titulo || 'Pasajes')}</span>
              <span class="sec-meta">${g.siguiente ? '<span class="sec-aqui">Aquí sigues</span> · ' : ''}${g.total} ${g.total === 1 ? 'pasaje' : 'pasajes'} · ${rango({ inicio: g.inicio, fin: g.fin })}</span></span>
              <span class="sec-prog"><progress max="${g.total}" value="${g.leidos}" aria-label="Progreso de la sección"></progress><span>${g.leidos}/${g.total}</span></span></summary>
            <ol class="pasajes">${g.pasajes.map(x => itemPasaje(x.pasaje, x.n)).join('')}</ol></details>`;
        }).join('')}</div>`;
    return `<div class="inicio"><section class="portada" aria-labelledby="t-portada">
        <p class="portada-alcance">${esc(N.alcance(D).texto)}</p>
        <h1 id="t-portada" tabindex="-1">${pos ? 'Continúa donde lo dejaste' : 'Empieza a leer'}</h1>
        ${sig ? `<a class="continuar" href="#leer/p/${esc(sig.id)}${enSig ? '/' + esc(pos.v) : ''}">
          <span class="continuar-rango">${varios ? esc(N.nombreLibro(D, N.libroDe(sig))) + ', ' : ''}${rango(sig)}${enSig ? `, versículo ${esc(pos.v.split(':')[1])}` : ''}</span>
          <span class="continuar-titulo">${esc(sig.titulo)}</span>
          ${sig.resumen ? `<span class="continuar-resumen">${esc(sig.resumen)}</span>` : ''}
          <span class="continuar-accion">${pos ? 'Seguir leyendo' : 'Abrir el primer pasaje'}<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M7 4l6 6-6 6"/></svg></span></a>` : '<p>No hay texto en los datos.</p>'}
        <div class="progreso"><progress max="${ps.length || 1}" value="${n}" aria-label="Progreso de lectura"></progress><span>${n} de ${ps.length} pasajes leídos${varios ? ' en total' : ''}</span></div>
      </section>
      <div class="plan">
      <h2 class="titulo-seccion">Plan de lectura${varios && libroSel ? `<span class="sr">: ${esc(libroSel.nombre)}</span>` : ''}</h2>
      ${selector}
      ${elegido ? videoLibroHTML(elegido) : ''}
      ${plan}
      ${editorial ? `<p class="meta">Los títulos${secs.some(g => g.titulo) ? ', secciones' : ''} y resúmenes de los pasajes son editoriales: no forman parte del texto bíblico.</p>` : ''}</div></div>`;
  }

  /* ---------- Leer: pasaje con acompañante ---------- */
  function vistaPasaje(p, activo) {
    if (!p) return `<h1 tabindex="-1">Pasaje no encontrado</h1><p class="vacio-txt">Ese pasaje no está en los datos, que cubren ${esc(N.alcance(D).texto)}.</p><p><a class="boton" href="#leer">Ver el plan de lectura</a></p>`;
    const ps = N.pasajes(D), i = ps.findIndex(x => x.id === p.id), prev = ps[i - 1], next = ps[i + 1];
    const lb = N.libroDe(p), psL = ps.filter(x => N.libroDe(x) === lb), iL = psL.findIndex(x => x.id === p.id);
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
      return `${cab}<span class="vers${ap ? ' con-apoyo' : ''}${k === estado.activo ? ' activo' : ''}${habla.k === k ? ' sonando' : ''}" id="v${v.cap}-${v.n}" data-v="${k}"><button type="button" class="vn" data-activar="${k}" aria-pressed="${k === estado.activo}" aria-label="Versículo ${v.n}${ap ? ', con datos en el acompañante' : ''}">${v.n}</button>${marcaVariante(v.ref, v.n)}${partes} </span>`;
    }).join('');
    const nuevos = N.primerasApariciones(D, p);
    return `<div class="pasaje-vista"><article class="lectura">
      <header class="cab-pasaje"><a class="volver" href="#leer/${esc(lb)}"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M12 4l-6 6 6 6"/></svg>Plan de lectura</a>
        <p class="pasaje-libro">${esc(N.nombreLibro(D, lb))}</p>
        <p class="pasaje-rango">${rango(p)}<span class="pasaje-pos">pasaje ${iL + 1} de ${psL.length}</span></p>
        <h1 tabindex="-1">${esc(p.titulo)}</h1>
        ${p.titulo_origen === 'editorial' ? '<p class="meta">Título editorial, no del texto bíblico.</p>' : ''}</header>
      ${imagenPasajeHTML(p)}
      ${herramientasPasajeHTML()}
      ${estado.comparar ? compararHTML(p) : `<div class="biblia">${texto || '<p class="vacio-txt">Este pasaje no tiene versículos en los datos.</p>'}</div>
      <p class="pista-lectura meta"><span class="marca-apoyo" aria-hidden="true"></span>Pulsa el número de un versículo para ver sus datos. La marca al margen indica vínculos, edades o personas sin nombre.${ORIG.o && N.variantesDe(ORIG.o, vs.map(v => v.ref)).length ? ' «var.» señala una variante entre manuscritos.' : ''}</p>
      ${fuente ? `<p class="meta">Texto: ${esc(fuenteNombre(fuente))}</p>` : ''}`}
      <section class="nuevo" aria-labelledby="t-nuevo"><h2 id="t-nuevo">Lo nuevo en este pasaje</h2>
        ${nuevos.length ? `<p class="meta">Personas que aparecen por primera vez:</p><ul class="chips">${nuevos.map(id => `<li>${btnPersona(id)}</li>`).join('')}</ul>` : '<p class="vacio-txt">Nadie aparece aquí por primera vez.</p>'}</section>
      <nav class="pasos-pasaje" aria-label="Pasajes">
        ${prev ? `<a class="boton secundario" href="#leer/p/${esc(prev.id)}" title="${esc(prev.titulo)}">Anterior</a>` : '<span></span>'}
        <button type="button" class="boton" data-leido-seguir="${esc(p.id)}">${next ? 'Marcar como leído y seguir' : 'Marcar como leído'}</button>
        ${next ? `<a class="boton secundario" href="#leer/p/${esc(next.id)}" title="${esc(next.titulo)}">Siguiente</a>` : '<span></span>'}
      </nav></article>
      <aside class="acompanante${estado.hoja ? ' abierta' : ''}" id="acompanante" aria-label="Acompañante de lectura">${acompHTML()}</aside></div>`;
  }

  // Nota del vínculo tal como viene en los datos («sierva», «concubina»…), sin reinterpretarla.
  const notaVinculo = r => r && r.nota ? `<span class="nota-vinculo">${esc(r.nota)}</span>` : '';
  const TIPO_REL = r => r.tipo === 'conyuge' ? `${esc(nombre(r.de))} y ${esc(nombre(r.a))}: cónyuges${notaVinculo(r)}`
    : `${esc(nombre(r.de))} es ${r.tipo === 'madre' ? 'madre' : 'padre'} de ${esc(nombre(r.a))}`;
  // "Abram tenía 75 años al salir de Harán" (+ LXX si difiere).
  function eventoHTML(x) {
    const base = x.TM || x.LXX;
    return `<li${x.difiere ? ' class="difiere"' : ''}><span class="edad-quien">${esc(nombre(x.persona))} tenía <strong>${base.valor}</strong> años${x.evento ? ' ' + esc(x.evento) : ''}${x.solo === 'LXX' ? ' (según la LXX)' : ''}</span>
      ${insignia(base.certeza || 'texto', x.ref)}${base.cita ? ` <span class="cita-corta">«${esc(base.cita)}»</span>` : ''}
      ${x.difiere ? `<p class="difiere-txt">En la Septuaginta: ${x.LXX.valor}${x.LXX.ref && x.LXX.ref !== x.TM.ref ? ' (' + refHTML(x.LXX.ref) + ')' : ''}</p>` : ''}</li>`;
  }
  const QUIEN_MAX = 8; // a partir de aquí "Quién aparece" se agrupa
  function acompHTML() {
    const p = estado.pasaje;
    if (!p) return '';
    const lb = N.libroDe(p);
    const refs = estado.activo ? [`${lb} ${estado.activo}`] : N.versiculosDe(D, p).map(v => v.ref);
    const A = N.acompanante(D, refs);
    const n = A.vinculos.length + A.edades.length + A.eventos.length + A.sinNombre.length + A.lugares.length;
    const ambito = estado.activo ? `${lb} ${estado.activo}` : 'Todo el pasaje';
    const sec = (t, cuerpo, icono) => `<section class="acomp-sec"><h3>${icono}${t}</h3>${cuerpo}</section>`;
    const I = (d) => `<svg viewBox="0 0 20 20" aria-hidden="true"><path d="${d}"/></svg>`;
    let html = '';
    if (A.personas.length) {
      // Sin parentesco, se muestra su papel en el relato (`rol`, p. ej. "rey de Salem") si los datos lo traen.
      const li = x => { const c = x.contexto || (N.persona(D, x.id) || {}).rol || ''; return `<li>${btnPersona(x.id)}${c ? `<span class="contexto">${esc(c)}</span>` : ''}</li>`; };
      let cuerpo;
      if (A.personas.length > QUIEN_MAX) {
        const porId = new Map(A.personas.map(x => [x.id, x])), Q = N.quienAparece(D, p, A.personas.map(x => x.id));
        cuerpo = (Q.nuevas.length ? `<p class="meta">Nuevas en este pasaje (${Q.nuevas.length})</p><ul class="quien">${Q.nuevas.map(id => li(porId.get(id))).join('')}</ul>` : '')
          + (Q.resto.length ? `<details class="plegable"><summary>Ya aparecidas antes (${Q.resto.length})</summary><ul class="quien">${Q.resto.map(id => li(porId.get(id))).join('')}</ul></details>` : '');
      } else cuerpo = `<ul class="quien">${A.personas.map(li).join('')}</ul>`;
      html += sec(`Quién aparece${A.personas.length > QUIEN_MAX ? ` (${A.personas.length})` : ''}`, cuerpo, I('M10 9a3 3 0 100-6 3 3 0 000 6zM4 17c0-3.3 2.7-5 6-5s6 1.7 6 5'));
    }
    if (A.lugares.length) {
      const ub = A.lugares.filter(id => N.confianzaLugar(N.lugar(D, id)) !== 'desconocida');
      html += sec('Dónde ocurre', `${ub.length ? mapaHTML(ub, { mini: true }) : ''}<ul class="lugares-lista">${A.lugares.map(id => { const l = N.lugar(D, id) || {}, c = N.confianzaLugar(l); return `<li>${btnLugar(id)}<span class="contexto">${c === 'desconocida' ? 'Ubicación desconocida' + (l.nota ? ': ' + esc(l.nota) : '') : esc((l.ubicacion && l.ubicacion.identificacion) || '') + '. ' + CONF_TXT[c]}</span></li>`; }).join('')}</ul>`, I('M10 17s5-4.6 5-8.5a5 5 0 10-10 0C5 12.4 10 17 10 17zM10 10.2a1.7 1.7 0 100-3.4 1.7 1.7 0 000 3.4'));
    }
    if (N.crono(D)) {
      // Año (cálculo) de los sucesos de este versículo o pasaje; si no hay, entre qué sucesos fechados queda por orden de lectura.
      const tr = tradSimple(), combo = comboDe(tr);
      const evs = estado.activo ? N.eventosDeRefs(D, refs) : N.eventosDePasaje(D, p);
      const enlace = (x, t) => `<a href="#tiempo/linea/${encodeURIComponent(x)}">${t}</a>`;
      let cuerpo;
      if (evs.length) cuerpo = `<ul class="cuando">${evs.map(ev => {
        const a = N.anioEvento(D, ev.id, combo), dsp = N.despuesDe(D, ev.id, combo);
        return `<li><span class="edad-quien"><strong>${esc(ev.titulo || ev.id)}</strong> · ${refHTML(ev.ref)}</span>
          <span class="anio-calc">${a === null ? 'Sin año en esta combinación' : `Año ${a} desde Adán (${tr})`}</span> ${insignia('calculo')}
          ${dsp ? `<span class="contexto">${relTxt(dsp)}</span>` : ''}
          <a class="enlace-arbol" href="#tiempo/linea/${encodeURIComponent(ev.id)}">Ver en la línea de tiempo</a></li>`;
      }).join('')}</ul>`;
      else {
        const r = estado.activo ? [refs[0], refs[0]] : [p.inicio, p.fin], v = N.vecinosFechados(D, r[0], r[1], combo);
        const t = x => `${enlace(x.evento, '«' + esc(x.titulo) + '»')} (año ${x.anio}, ${refHTML(x.ref)})`;
        const donde = v.anterior && v.siguiente ? `entre ${t(v.anterior)} y ${t(v.siguiente)}` : v.anterior ? `después de ${t(v.anterior)}` : v.siguiente ? `antes de ${t(v.siguiente)}` : '';
        cuerpo = `<p class="contexto">${estado.activo ? 'Este versículo' : 'Este pasaje'} no trae datos de tiempo.${donde ? ` Por el orden de lectura queda ${donde}. Es el orden del relato, no un dato del texto.` : ''}</p>`;
      }
      html += sec('Cuándo ocurre', cuerpo, I('M10 3a7 7 0 100 14 7 7 0 000-14zM10 6v4l3 2'));
    }
    if (A.vinculos.length) html += sec('Vínculos que establece', `<ul class="vinculos">${A.vinculos.map(r => `<li><span>${TIPO_REL(r)}</span>${insignia(r.certeza, r.ref)}${citaHTML(r)}</li>`).join('')}</ul>`, I('M7 7a3 3 0 014 0l2 2a3 3 0 010 4M13 13a3 3 0 01-4 0l-2-2a3 3 0 010-4'));
    if (A.edades.length) html += sec('Edades', `<ul class="edades-acomp">${A.edades.map(e => {
      const val = tr => { const x = e[tr]; if (!x) return `<span class="vacio">${tr}: sin dato</span>`; const lbl = `<span class="trad">${tr}</span><strong>${x.valor}</strong>`; return N.TIPOS.includes(e.tipo) ? `<button type="button" class="celda-acomp" data-edad="${esc(e.persona)}|${e.tipo}|${tr}">${lbl}</button>` : `<span class="celda-acomp">${lbl}</span>`; };
      return `<li${e.difiere || e.solo ? ' class="difiere"' : ''}><span class="edad-quien">${esc(nombre(e.persona))}, ${esc(TIPO_TXT[e.tipo] || e.tipo.replace(/_/g, ' '))}</span><span class="par">${val('TM')}${val('LXX')}</span>
        ${e.difiere ? `<p class="difiere-txt">En la Septuaginta: ${e.LXX.valor}${e.LXX.ref && e.LXX.ref !== e.TM.ref ? ' (' + refHTML(e.LXX.ref) + ')' : ''}</p>` : e.solo ? `<p class="difiere-txt">Solo ${e.solo} da este dato.</p>` : ''}</li>`;
    }).join('')}</ul>`, I('M10 3a7 7 0 100 14 7 7 0 000-14zM10 6v4l3 2'));
    if (A.eventos.length) html += sec('Edad en este momento', `<ul class="edades-acomp">${A.eventos.map(eventoHTML).join('')}</ul>`, I('M10 3a7 7 0 100 14 7 7 0 000-14zM10 6v4l3 2'));
    if (A.sinNombre.length) html += sec('Sin nombre', A.sinNombre.map(id => `<p class="sin-nombre-aviso">El texto alude a alguien sin dar su nombre: ${btnPersona(id)}</p>`).join(''), I('M10 3a7 7 0 100 14 7 7 0 000-14zM10 6.5v4M10 13.5v.5'));
    const centrales = A.personas.map(x => x.id).filter(id => { const m = N.miniArbol(D, id); return !(N.persona(D, id) || {}).sin_nombre && (m.padres.length || m.hijos.length); }).slice(0, estado.activo ? 2 : 3);
    if (centrales.length) html += sec('Dónde va en el árbol', centrales.map(id => {
      const m = N.miniArbol(D, id), mas = m.hijos.length - 5;
      return `<div class="mini"><div class="mini-gen">${m.padres.map(btnPersona).join('') || '<span class="meta">Padres no constan</span>'}</div>
        <div class="mini-gen centro">${btnPersona(id)}${m.conyuges.map(c => `<span class="cony-mini">⚭</span>${btnPersona(c)}`).join('')}</div>
        <div class="mini-gen">${m.hijos.slice(0, 5).map(btnPersona).join('') || '<span class="meta">Sin hijos registrados</span>'}${mas > 0 ? `<span class="meta">y ${mas} más</span>` : ''}</div>
        <a class="enlace-arbol" href="#arbol/${encodeURIComponent(id)}">Ver a ${esc(nombre(id))} en el árbol completo</a></div>`;
    }).join(''), I('M10 3v5M10 8H5v4M10 8h5v4M10 8v9'));
    // «¿Sabías que…?» (cálculo) del pasaje: como mucho dos, elegidas en el núcleo sin repetir las del pasaje anterior.
    if (N.crono(D) && !estado.activo) {
      const tr = tradSimple(), cs = N.sabiasQue(D, comboDe(tr)).get(p.id) || [];
      if (cs.length) html += `<section class="acomp-sec sabias"><h3>${I('M10 3.5a4.5 4.5 0 00-2.6 8.2c.5.4.8 1 .8 1.6v.7h3.6v-.7c0-.6.3-1.2.8-1.6A4.5 4.5 0 0010 3.5zM8.3 16.5h3.4')}¿Sabías que…?</h3>
        <ul class="sabias-lista">${cs.map(c => `<li><p>${esc(c.texto)}.</p><span class="sabias-pie">${insignia('calculo')}<button type="button" class="enlace-boton" data-curio="${esc(c.id)}">Ver el cálculo</button></span></li>`).join('')}</ul>
        <p class="meta">${tr}, con los supuestos elegidos en Tiempo.</p></section>`;
    }
    if (!html) html = `<p class="vacio-txt">${estado.activo ? 'Este versículo no tiene personas, vínculos ni edades en los datos. Pulsa otro número o vuelve a todo el pasaje.' : 'Este pasaje no tiene personas, vínculos ni edades en los datos.'}</p>`;
    html += recursosAcompHTML(p, refs, sec, I);
    html += sec('De dónde sale este texto', origenAcompHTML(refs), I('M6 3h6l3 3v11H6zM12 3v3h3M8.5 10h4M8.5 13h4'));
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
    const rv = $('#rep-verso'); if (rv) rv.outerHTML = repVersoHTML();
  }

  /* ---------- Textos originales: carga bajo demanda ---------- */
  // datos/originales.js (hebreo, testigos, variantes, videos) y datos/griego-swete.js se inyectan solo cuando
  // la persona abre la comparación, el audio en lengua original, «De dónde sale este texto», Fuentes o un video.
  const EJEMPLO = /[?&]ejemplo/.test(location.search);
  const ORIG = { o: null, g: null, est: { o: '', g: '' }, foco: null };
  const scripts = new Map();
  function cargarScript(src) {
    if (!scripts.has(src)) scripts.set(src, new Promise((ok, mal) => {
      const s = document.createElement('script'); s.src = src; s.onload = ok;
      s.onerror = () => { scripts.delete(src); s.remove(); mal(new Error(src)); };
      document.head.appendChild(s);
    }));
    return scripts.get(src);
  }
  function cargarOriginales(que, foco) {
    const qs = que === 'ambos' ? ['o', 'g'] : [que];
    const pend = qs.filter(q => ORIG.est[q] !== 'ok' && ORIG.est[q] !== 'cargando');
    if (!pend.length) return;
    if (foco) ORIG.foco = foco;
    pend.forEach(q => {
      ORIG.est[q] = 'cargando';
      const src = EJEMPLO ? 'pruebas/originales-ejemplo.js' : q === 'o' ? 'datos/originales.js' : 'datos/griego-swete.js';
      cargarScript(src).then(() => {
        const v = q === 'o' ? window.BIBLIA_ORIGINALES : window.BIBLIA_GRIEGO;
        ORIG[q] = v || null; ORIG.est[q] = v ? 'ok' : 'error';
      }, () => { ORIG.est[q] = 'error'; }).then(() => {
        if (ORIG.est.o === 'cargando' || ORIG.est.g === 'cargando') return;
        const f = ORIG.foco; ORIG.foco = null;
        rerender(f);
        const h = estado.hablarTrasCarga; estado.hablarTrasCarga = null;
        if (h) hablar(h.id, h.ks);
      });
    });
    const el = main.querySelector('[data-estado-carga]'); if (el) el.textContent = 'Cargando los textos originales…';
  }
  const haySinCargar = q => ORIG.est[q] === '' || ORIG.est[q] === 'error';
  const NO_DISP = { o: 'Los textos hebreos, manuscritos y variantes aún no están en los datos (datos/originales.js).', g: 'El texto griego aún no está en los datos (datos/griego-swete.js).' };
  const estadoCarga = q => ORIG.est[q] === 'cargando' ? '<p class="meta" data-estado-carga>Cargando…</p>' : ORIG.est[q] === 'error' ? `<p class="vacio-txt">${NO_DISP[q]} <button type="button" class="enlace-boton" data-reintentar="${q}">Reintentar</button></p>` : '';
  // Fuente hebrea con buen soporte de vocales y acentos (Noto Serif Hebrew, licencia OFL), pedida solo al ver hebreo.
  let fuenteHeb = false;
  function pedirFuenteHebrea() {
    if (fuenteHeb) return; fuenteHeb = true;
    const l = document.createElement('link'); l.rel = 'stylesheet';
    l.href = 'https://fonts.googleapis.com/css2?family=Noto+Serif+Hebrew:wght@400;600&display=swap';
    document.head.appendChild(l);
  }
  const fuenteHebreo = () => { const f = ((ORIG.o && ORIG.o.fuentes) || []).find(x => /lening|wlc|masor|hebr|tanach/i.test(`${x.id} ${x.nombre}`)); return f ? f.nombre : 'Códice de Leningrado'; };
  const fuenteGriego = () => (ORIG.g && ORIG.g.fuente) || 'Swete 1930';
  const urlSegura = u => /^https:\/\//i.test(String(u || '')) ? String(u) : '';
  const extLink = (u, t) => urlSegura(u) ? `<a href="${esc(urlSegura(u))}" target="_blank" rel="noopener noreferrer">${esc(t)}</a> <span class="etiqueta externa">Fuente externa</span>` : '';
  // Atributos lang/dir de un texto original según su escritura.
  const attrsOrig = t => { const s = N.escritura(t); return s === 'he' ? ' lang="he" dir="rtl"' : s === 'grc' ? ' lang="grc"' : ''; };

  /* ---------- Comparar lado a lado ---------- */
  const COLS = {
    rv: { t: 'Español', idioma: 'es', fuente: () => { const f = ((D.fuentes || []).find(x => /rv/i.test(x.id)) || {}).id; return f ? fuenteNombre(f) : 'Reina-Valera 1909'; } },
    he: { t: 'Hebreo', idioma: 'he', fuente: fuenteHebreo },
    gr: { t: 'Griego (LXX)', idioma: 'el', fuente: fuenteGriego }
  };
  const estrecho = () => window.matchMedia && window.matchMedia('(max-width: 699px)').matches;
  // Columnas elegidas, en orden de activación; en teléfono caben dos (las dos últimas elegidas).
  function columnas() {
    let c = (store.get('biblia.cols', ['gr', 'rv', 'he']) || []).filter(x => COLS[x]);
    if (!c.length) c = ['rv', 'he'];
    if (estrecho() && c.length > 2) c = c.slice(-2);
    return c;
  }
  function alternarColumna(id, on) {
    let c = columnas().filter(x => x !== id);
    if (on) c.push(id);
    if (!c.length) c = [id]; // siempre queda una
    if (estrecho() && c.length > 2) c = c.slice(-2);
    store.set('biblia.cols', c);
  }
  function herramientasPasajeHTML() {
    return `<div class="herr-pasaje">
      <fieldset class="segmentos modo"><legend class="sr">Modo de lectura</legend>${[['leer', 'Leer'], ['comparar', 'Comparar']].map(([v, t]) => `<label><input type="radio" name="modo-pasaje" value="${v}" ${(estado.comparar ? 'comparar' : 'leer') === v ? 'checked' : ''}><span>${t}</span></label>`).join('')}</fieldset>
      <button type="button" class="boton secundario btn-escuchar" data-escuchar aria-expanded="${!!estado.escuchar}" aria-controls="reproductor"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 8h3l4-3.5v11L7 12H4zM14 7.5a3.5 3.5 0 010 5M16 5a7 7 0 010 10"/></svg>Escuchar</button>
    </div>${estado.escuchar ? reproductorHTML() : ''}`;
  }
  function compararHTML(p) {
    const orden = ['rv', 'he', 'gr'], sel = columnas(), vis = orden.filter(c => sel.includes(c));
    const filas = N.alinearOriginales(D, p, ORIG.o, ORIG.g);
    const cargando = vis.some(c => (c === 'he' && ORIG.est.o !== 'ok') || (c === 'gr' && ORIG.est.g !== 'ok'));
    const elegir = `<fieldset class="cmp-cols"><legend>Columnas${estrecho() ? ' <span class="meta">(dos en pantallas estrechas)</span>' : ''}</legend>${orden.map(c => `<label class="chip-check"><input type="checkbox" data-col="${c}" ${vis.includes(c) ? 'checked' : ''}><span>${COLS[c].t}</span></label>`).join('')}</fieldset>`;
    const cab = vis.map(c => `<div class="cmp-cab"><span class="cmp-col-t">${esc(COLS[c].t)}</span><span class="cmp-fuente">${esc(COLS[c].fuente())}</span>${c === 'he' ? estadoCarga('o') : c === 'gr' ? estadoCarga('g') : ''}</div>`).join('');
    const vars = new Set(ORIG.o ? filas.filter(f => N.variantesDe(ORIG.o, [f.ref]).length).map(f => f.ref) : []);
    let capPrev = null;
    const cuerpo = filas.map((f, j) => {
      const k = `${f.cap}:${f.n}`;
      const marca = f.cap !== capPrev && j ? `<div class="cmp-capitulo">Capítulo ${f.cap}</div>` : ''; capPrev = f.cap;
      const celda = c => {
        const t = c === 'rv' ? f.rv : c === 'he' ? f.he : f.gr;
        const pend = (c === 'he' && ORIG.est.o === 'cargando') || (c === 'gr' && ORIG.est.g === 'cargando');
        const attrs = c === 'he' ? ' lang="he" dir="rtl"' : c === 'gr' ? ' lang="grc"' : '';
        const num = c === 'he' && f.heNum ? `<span class="num-heb" title="En la Biblia hebrea este versículo lleva otro número">Heb. ${esc(f.heNum)}</span>` : '';
        return `<div class="cmp-celda cmp-${c}">${num}${t ? `<p class="cmp-txt"${attrs}>${esc(t)}</p><button type="button" class="hablar-btn" data-hablar="${COLS[c].idioma}|${k}" aria-label="Escuchar el versículo ${f.n} en ${esc(COLS[c].t.toLowerCase())}"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 8h3l4-3.5v11L7 12H4zM14 7.5a3.5 3.5 0 010 5"/></svg></button>` : `<p class="cmp-vacio">${pend ? '…' : 'Sin texto en los datos'}</p>`}</div>`;
      };
      return `${marca}<div class="cmp-fila${habla.k === k ? ' sonando' : ''}${vars.has(f.ref) ? ' con-variante' : ''}" data-v="${k}"><div class="cmp-num">${f.n}${vars.has(f.ref) ? marcaVariante(f.ref, f.n) : ''}</div>${vis.map(celda).join('')}</div>`;
    }).join('');
    return `<section class="comparar" aria-label="Comparar textos lado a lado" style="--cols:${vis.length}">${elegir}
      <div class="cmp-tabla" role="group" aria-busy="${cargando}"><div class="cmp-fila cmp-cabecera"><div class="cmp-num" aria-hidden="true"></div>${cab}</div>${cuerpo || '<p class="vacio-txt">Este pasaje no tiene versículos en los datos.</p>'}</div>
      <p class="meta">Versos alineados según la numeración de la Reina-Valera; «Heb.» indica el número en la Biblia hebrea cuando difiere. El hebreo y el griego vienen de fuentes externas, con su licencia en <a href="#fuentes">Fuentes</a>.</p></section>`;
  }

  /* ---------- Variantes y testigos ---------- */
  const TIPO_TESTIGO = { codice: 'Códice', rollo: 'Rollo', pentateuco_samaritano: 'Pentateuco samaritano' };
  const TESTIGO_CONOCIDO = { lxx: 'Septuaginta (LXX)', tm: 'Texto Masorético (TM)', sp: 'Pentateuco samaritano' };
  const nombreTestigo = id => { const t = ((ORIG.o && ORIG.o.testigos) || []).find(x => x.id === id); return t ? t.nombre : (TESTIGO_CONOCIDO[String(id).toLowerCase()] || id); };
  function marcaVariante(ref, n) {
    if (!ORIG.o || !N.variantesDe(ORIG.o, [ref]).length) return '';
    return `<button type="button" class="marca-var" data-variante="${esc(ref)}" title="Variante entre manuscritos: ver las lecturas" aria-label="Variante entre manuscritos en el versículo ${n}">var.</button>`;
  }
  function varianteHTML(v) {
    return `<article class="variante"><p class="var-cab"><strong>${refHTML(v.ref)}</strong>${v.tema ? ` · ${esc(v.tema)}` : ''}</p>
      <div class="lecturas">${(v.lecturas || []).map(l => `<div class="lectura-var">
        <p class="lv-testigos">${(l.testigos || []).map(t => `<span class="etiqueta">${esc(nombreTestigo(t))}</span>`).join(' ')}</p>
        ${l.texto_original ? `<p class="lv-orig"${attrsOrig(l.texto_original)}>${esc(l.texto_original)}</p>` : ''}
        ${l.traduccion_es ? `<p class="lv-trad">«${esc(l.traduccion_es)}»</p>` : ''}</div>`).join('')}</div>
      ${v.nota ? `<p class="meta">${esc(v.nota)}</p>` : ''}
      <p class="meta">Fuente: ${esc(v.fuente || 'sin indicar')} ${extLink(v.url_fuente, 'Ver la fuente')}</p></article>`;
  }
  function testigoHTML(t) {
    const datos = [t.idioma, t.fecha ? `${t.fecha}${t.fecha_certeza ? ` (${t.fecha_certeza})` : ''}` : '', t.institucion].filter(Boolean).map(esc).join(' · ');
    return `<li class="testigo"><span class="testigo-cab"><strong>${esc(t.nombre || t.id)}</strong><span class="etiqueta">${esc(TIPO_TESTIGO[t.tipo] || t.tipo || 'Testigo')}</span></span>
      ${datos ? `<span class="meta">${datos}</span>` : ''}${t.nota ? `<span class="meta">${esc(t.nota)}</span>` : ''}
      ${urlSegura(t.url) ? `<span>${extLink(t.url, 'Ver el manuscrito')}</span>` : ''}</li>`;
  }
  const QUE_ES = `<details class="plegable"><summary>Qué son el TM, la LXX y Qumrán</summary><dl class="que-es">
      <dt>TM · Texto Masorético</dt><dd>El texto hebreo que copiaron los masoretas, escribas judíos que le añadieron vocales y acentos. El Códice de Leningrado es su manuscrito completo más usado hoy. La Reina-Valera traduce un texto hebreo de esta tradición.</dd>
      <dt>LXX · Septuaginta</dt><dd>Traducción griega antigua de las Escrituras hebreas. A veces refleja un texto hebreo distinto del masorético; el Nuevo Testamento la cita a menudo.</dd>
      <dt>Qumrán · Rollos del Mar Muerto</dt><dd>Manuscritos hallados en cuevas junto al mar Muerto, entre ellos copias de libros bíblicos más antiguas que los códices medievales. Unas veces coinciden con el TM y otras con la LXX o con el Pentateuco samaritano: por eso ayudan a ver de dónde sale cada lectura.</dd>
      <dt>Pentateuco samaritano</dt><dd>Los cinco libros de Moisés en hebreo, tal como los transmitió la comunidad samaritana, con su propia escritura.</dd></dl>
      <p class="meta">Las fechas de cada manuscrito vienen de sus fuentes, con su grado de certeza.</p></details>`;
  function origenAcompHTML(refs) {
    if (ORIG.est.o !== 'ok') return `<p class="contexto">Qué manuscritos antiguos contienen ${estado.activo ? 'este versículo' : 'este pasaje'} y dónde difieren entre sí.</p>
      ${ORIG.est.o === 'cargando' ? '<p class="meta" data-estado-carga>Cargando…</p>' : ORIG.est.o === 'error' ? `<p class="vacio-txt">${NO_DISP.o} <button type="button" class="enlace-boton" data-reintentar="o">Reintentar</button></p>` : '<button type="button" class="boton mini-boton secundario" data-cargar-origen>Ver manuscritos y variantes</button>'}${QUE_ES}`;
    const ts = N.testigosDe(ORIG.o, refs), vs = N.variantesDe(ORIG.o, refs);
    return `${vs.length ? `<p class="meta">${vs.length === 1 ? 'Una variante' : vs.length + ' variantes'} entre manuscritos:</p>${vs.map(varianteHTML).join('')}` : `<p class="contexto">Los datos no registran variantes en ${estado.activo ? 'este versículo' : 'este pasaje'}.</p>`}
      ${ts.length ? `<p class="meta">Manuscritos que contienen ${estado.activo ? 'este versículo' : 'parte de este pasaje'}:</p><ul class="testigos">${ts.map(testigoHTML).join('')}</ul>` : '<p class="vacio-txt">Ningún manuscrito de los datos cubre este pasaje.</p>'}${QUE_ES}`;
  }
  function abrirVariante(ref) {
    const vs = ORIG.o ? N.variantesDe(ORIG.o, [ref]) : [];
    if (vs.length) abrirDetalle(`Variante en ${ref}`, vs.map(varianteHTML).join('') + '<p class="meta">Lecturas lado a lado, cada una con los manuscritos que la traen.</p>');
  }

  /* ---------- Escuchar (voz sintética del dispositivo) ---------- */
  const IDIOMAS = { es: { t: 'Español', lang: 'es-ES', region: 'ES', nombre: 'español' }, he: { t: 'Hebreo', lang: 'he-IL', region: 'IL', nombre: 'hebreo' }, el: { t: 'Griego', lang: 'el-GR', region: 'GR', nombre: 'griego' } };
  const SINTESIS = typeof window.speechSynthesis !== 'undefined' && typeof window.SpeechSynthesisUtterance !== 'undefined';
  const habla = { gen: 0, cola: [], i: 0, idioma: store.get('biblia.vozIdioma', 'es'), vel: +store.get('biblia.vozVel', 1) || 1, k: null, estado: 'parado' };
  if (!IDIOMAS[habla.idioma]) habla.idioma = 'es';
  const voces = () => { try { return SINTESIS ? speechSynthesis.getVoices() : []; } catch (e) { return []; } };
  const vozDe = id => N.vozPara(voces(), id, IDIOMAS[id].region);
  if (SINTESIS) try { speechSynthesis.addEventListener('voiceschanged', () => { const el = $('#rep-voz'); if (el) el.innerHTML = vozEstadoHTML(); }); } catch (e) { /* sin evento */ }
  function textoDe(id, ref) {
    if (id === 'he') { const h = ORIG.o && ORIG.o.hebreo && ORIG.o.hebreo[ref]; return h ? h.t : ''; }
    if (id === 'el') return (ORIG.g && ORIG.g.texto && ORIG.g.texto[ref]) || '';
    const v = N.versiculosDe(D, { inicio: ref, fin: ref })[0]; return v ? v.texto : '';
  }
  function marcarSonando(k) {
    habla.k = k;
    document.querySelectorAll('.sonando').forEach(el => el.classList.remove('sonando'));
    if (!k) return;
    document.querySelectorAll(`[data-v="${CSS.escape(k)}"]`).forEach(el => el.classList.add('sonando'));
    const el = document.querySelector(`.vers[data-v="${CSS.escape(k)}"], .cmp-fila[data-v="${CSS.escape(k)}"]`);
    if (el) { const r = el.getBoundingClientRect(); if (r.top < 80 || r.bottom > window.innerHeight - 140) el.scrollIntoView({ block: 'center', behavior: 'smooth' }); }
  }
  function pintarRep() {
    const el = $('#rep-ctrl'); if (el) el.innerHTML = repCtrlHTML();
    const r = main.querySelector(`input[name="voz-idioma"][value="${habla.idioma}"]`);
    if (r && !r.checked) { r.checked = true; const v = $('#rep-voz'); if (v) v.innerHTML = vozEstadoHTML(); }
  }
  function parar() {
    habla.gen++; habla.cola = []; habla.estado = 'parado';
    if (SINTESIS) try { speechSynthesis.cancel(); } catch (e) { /* nada */ }
    marcarSonando(null); pintarRep();
  }
  function hablar(id, ks) {
    if (!SINTESIS || !estado.pasaje) return;
    const lb = N.libroDe(estado.pasaje);
    const cola = ks.map(k => ({ k, t: N.textoParaVoz(textoDe(id, `${lb} ${k}`), id) })).filter(x => x.t);
    parar();
    if (!cola.length) { const e = $('#rep-voz'); if (e) e.innerHTML = `<span class="vacio">No hay texto en ${IDIOMAS[id].nombre} para ${ks.length === 1 ? 'este versículo' : 'este pasaje'} en los datos.</span>`; return; }
    Object.assign(habla, { cola, i: 0, idioma: id, estado: 'sonando' });
    const gen = habla.gen;
    const sig = () => {
      if (gen !== habla.gen) return;
      if (habla.i >= habla.cola.length) { habla.estado = 'parado'; marcarSonando(null); pintarRep(); return; }
      const x = habla.cola[habla.i], u = new SpeechSynthesisUtterance(x.t), v = vozDe(id);
      u.lang = v ? v.lang : IDIOMAS[id].lang; if (v) u.voice = v; u.rate = habla.vel;
      u.onend = () => { if (gen === habla.gen) { habla.i++; sig(); } };
      u.onerror = ev => { if (gen === habla.gen && ev.error !== 'interrupted' && ev.error !== 'canceled') { habla.i++; sig(); } };
      marcarSonando(x.k);
      speechSynthesis.speak(u);
    };
    sig(); pintarRep();
  }
  function pausar() {
    if (!SINTESIS) return;
    if (habla.estado === 'sonando') { speechSynthesis.pause(); habla.estado = 'pausa'; }
    else if (habla.estado === 'pausa') { speechSynthesis.resume(); habla.estado = 'sonando'; }
    pintarRep();
  }
  const versosPasaje = () => estado.pasaje ? N.versiculosDe(D, estado.pasaje).map(v => `${v.cap}:${v.n}`) : [];
  // Pide los textos que necesita un idioma y, si ya están, empieza a hablar.
  function escucharEn(id, ks, foco) {
    const q = id === 'he' ? 'o' : id === 'el' ? 'g' : null;
    if (q && ORIG.est[q] !== 'ok') { habla.idioma = id; estado.hablarTrasCarga = { id, ks }; cargarOriginales(q, foco); return; }
    hablar(id, ks);
  }
  function vozEstadoHTML() {
    if (!SINTESIS) return '<span class="vacio">Este navegador no tiene síntesis de voz.</span>';
    const id = habla.idioma, v = vozDe(id);
    if (v) return `Voz: ${esc(v.name)} <span class="meta">(${esc(v.lang)})</span>`;
    if (!voces().length) return '<span class="meta">Buscando las voces del dispositivo…</span>';
    return `<span class="vacio">No hay voz de ${IDIOMAS[id].nombre} en este dispositivo.</span>
      <details class="plegable"><summary>Cómo instalar una voz de ${IDIOMAS[id].nombre}</summary><ul class="instalar-voz">
        <li><strong>Windows:</strong> Configuración › Hora e idioma › Voz › Agregar voces; elige ${IDIOMAS[id].t.toLowerCase()} y reinicia el navegador. Microsoft Edge ofrece además voces en línea de varios idiomas.</li>
        <li><strong>Android:</strong> Ajustes › Sistema › Idiomas › Salida de texto a voz › motor de Google (ajustes) › Instalar datos de voz › ${IDIOMAS[id].t.toLowerCase()}.</li>
        <li><strong>iPhone y iPad:</strong> Ajustes › Accesibilidad › Contenido leído › Voces › ${IDIOMAS[id].t.toLowerCase()} y descarga una voz.</li>
      </ul><p class="meta">Los menús cambian según la versión del sistema.</p></details>`;
  }
  const repVersoHTML = () => `<button type="button" class="boton mini-boton secundario" id="rep-verso" data-rep="verso"${estado.activo ? '' : ' hidden'}>Solo el versículo ${esc(estado.activo ? estado.activo.split(':')[1] : '')}</button>`;
  function repCtrlHTML() {
    const s = habla.estado;
    return `<button type="button" class="boton mini-boton" data-rep="${s === 'parado' ? 'pasaje' : 'pausa'}">${s === 'sonando' ? 'Pausa' : s === 'pausa' ? 'Reanudar' : 'Escuchar el pasaje'}</button>
      ${repVersoHTML()}
      <button type="button" class="boton mini-boton secundario" data-rep="parar"${s === 'parado' ? ' disabled' : ''}>Detener</button>`;
  }
  function reproductorHTML() {
    return `<section class="reproductor" id="reproductor" aria-label="Escuchar el pasaje">
      <p class="voz-aviso"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3a7 7 0 100 14 7 7 0 000-14zM10 6.5v4M10 13.5v.5"/></svg>Voz sintética del dispositivo · pronunciación moderna, no la antigua</p>
      <fieldset class="segmentos"><legend class="sr">Idioma</legend>${Object.entries(IDIOMAS).map(([v, x]) => `<label><input type="radio" name="voz-idioma" value="${v}" ${habla.idioma === v ? 'checked' : ''}><span>${x.t}</span></label>`).join('')}</fieldset>
      <div class="rep-ctrl" id="rep-ctrl">${repCtrlHTML()}</div>
      <label class="rep-vel">Velocidad <input type="range" id="rep-vel" min="0.5" max="1.5" step="0.1" value="${habla.vel}"><output id="rep-vel-txt">${habla.vel.toFixed(1).replace('.', ',')}×</output></label>
      <div class="rep-voz" id="rep-voz" aria-live="polite">${vozEstadoHTML()}</div>
      <p class="meta">${habla.idioma === 'he' ? `Texto: ${esc(fuenteHebreo())}.` : habla.idioma === 'el' ? `Texto: ${esc(fuenteGriego())}.` : 'Texto: Reina-Valera 1909.'} Se oye el versículo resaltado.</p></section>`;
  }

  /* ---------- Video del libro (fachada: no se carga nada de YouTube hasta pulsar) ---------- */
  const iframeVideo = v => `<div class="video-marco"><iframe src="https://www.youtube-nocookie.com/embed/${esc(v.youtube_id)}?autoplay=1&amp;rel=0" title="${esc(v.titulo || 'Video')}" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" referrerpolicy="strict-origin-when-cross-origin"></iframe></div>`;
  function videoLibroHTML(lb) {
    const nom = N.nombreLibro(D, lb);
    const pie = v => `<p class="video-pie"><strong>${esc(v.titulo || 'Video')}</strong>${v.rango ? ` <span class="meta">· ${esc(v.rango)}</span>` : ''}<br>
      <span class="video-rotulo">Video de ${esc(v.fuente || 'Proyecto Biblia')} · <span class="etiqueta externa">Fuente externa</span></span>${urlSegura(v.url) ? ` <a href="${esc(urlSegura(v.url))}" target="_blank" rel="noopener noreferrer">Ver la fuente</a>` : ''}</p>`;
    if (ORIG.est.o === 'ok') {
      const v = N.videosDeLibro(ORIG.o, lb)[0];
      if (!v) return estado.videoPedido === lb ? `<p class="meta video-libro">No hay video de ${esc(nom)} en los datos.</p>` : '';
      const cuerpo = estado.videoPedido === lb ? iframeVideo(v)
        : `<button type="button" class="video-fachada" data-video="${esc(v.youtube_id)}" aria-label="Reproducir el video: ${esc(v.titulo || nom)}"><img src="https://i.ytimg.com/vi/${esc(v.youtube_id)}/hqdefault.jpg" alt="" loading="lazy" onerror="this.remove()"><span class="video-play" aria-hidden="true"><svg viewBox="0 0 20 20"><path d="M7 5v10l8-5z"/></svg></span></button>`;
      return `<section class="video-libro" aria-label="Video sobre ${esc(nom)}">${cuerpo}${pie(v)}</section>`;
    }
    return `<section class="video-libro" aria-label="Video sobre ${esc(nom)}"><button type="button" class="video-fachada vacia" data-video-cargar="${esc(lb)}">
        <span class="video-play" aria-hidden="true"><svg viewBox="0 0 20 20"><path d="M7 5v10l8-5z"/></svg></span><span class="video-invita">De qué trata ${esc(nom)}: ver el video</span></button>
      ${ORIG.est.o === 'cargando' ? '<p class="meta" data-estado-carga>Cargando…</p>' : ORIG.est.o === 'error' ? `<p class="vacio-txt">${NO_DISP.o}</p>` : '<p class="video-pie"><span class="video-rotulo">Video de Proyecto Biblia · <span class="etiqueta externa">Fuente externa</span></span> <span class="meta">Se carga desde YouTube al pulsar.</span></p>'}</section>`;
  }

  /* ---------- Imágenes, objetos, mapas antiguos, videos y audio (datos/recursos.js, ~100 KB: se carga al arrancar) ---------- */
  // Las imágenes vienen de recursos/imagenes/ y se piden con loading="lazy" solo cuando se ven.
  const urlRec = u => /^https?:\/\//i.test(String(u || '')) ? String(u) : '';
  const linkRec = (u, t) => urlRec(u) ? `<a href="${esc(urlRec(u))}" target="_blank" rel="noopener noreferrer">${t}</a>` : '';
  const recPorId = id => N.recursos(R).find(f => f.id === id) || null;
  const rotuloRec = f => `<span class="etiqueta rec-rotulo rec-${esc(f.tipo)}${f.relacion === 'contexto' ? ' rec-contexto' : ''}">${esc(N.rotuloRecurso(f))}</span>`
    + (/debatida/i.test(f.certeza || '') ? ' <span class="etiqueta rec-debatida">relación debatida</span>' : '');
  const autorFecha = f => [f.autor, f.fecha].filter(Boolean).map(esc).join(', ');
  const licRec = f => { const l = String(f.licencia || ''); return esc(/^desconocida$/i.test(l) ? 'Licencia desconocida' : l.charAt(0).toUpperCase() + l.slice(1)); };
  // Pie: tipo rotulado · autor, fecha · licencia · institución · Fuente, y la atribución exacta (lo exige CC BY-SA).
  function pieRec(f, conTitulo) {
    const partes = [autorFecha(f), licRec(f), esc(f.institucion)].filter(Boolean);
    return `${conTitulo ? `<strong class="rec-titulo">${esc(f.titulo)}</strong>` : ''}
      <span class="rec-datos">${rotuloRec(f)} ${partes.join(' · ')}${urlRec(f.url_fuente) ? ' · ' + linkRec(f.url_fuente, 'Fuente') : ''}</span>
      <span class="rec-atrib">${esc(f.atribucion)}</span>`;
  }
  const altRec = f => `${f.titulo}. ${f.descripcion || ''}`.trim();
  const imgRec = (f, cls) => `<img class="${cls}" src="${esc(f.imagen)}" alt="${esc(altRec(f))}" loading="lazy" decoding="async"${f.ancho && f.alto ? ` width="${f.ancho}" height="${f.alto}"` : ''}>`;
  const ICO_AMPLIAR = '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M12 3h5v5M8 17H3v-5M17 3l-6 6M3 17l6-6"/></svg>';
  const imagenesPasaje = p => p ? N.imagenesDe(R, N.versiculosDe(D, p).map(v => v.clave)) : [];
  // Imagen principal del pasaje: solo si alguna obra se solapa con él; si hay varias, carrusel discreto.
  function imagenPasajeHTML(p) {
    const imgs = imagenesPasaje(p);
    if (!imgs.length) return '';
    if (!estado.recIdx || estado.recIdx.id !== p.id) estado.recIdx = { id: p.id, i: 0 };
    const i = Math.min(estado.recIdx.i, imgs.length - 1), f = imgs[i];
    return `<figure class="rec-principal" id="rec-principal">
      <button type="button" class="rec-marco" data-visor="${esc(f.id)}" aria-label="Ampliar: ${esc(f.titulo)}">${imgRec(f, 'rec-img')}<span class="rec-ampliar">${ICO_AMPLIAR}</span></button>
      <figcaption class="rec-pie">${pieRec(f, true)}</figcaption>
      ${imgs.length > 1 ? `<div class="rec-carrusel" role="group" aria-label="Imágenes del pasaje">
        <button type="button" class="rec-paso" data-rec-paso="-1" aria-label="Imagen anterior"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M12 4l-6 6 6 6"/></svg></button>
        <span class="rec-cuenta" aria-live="polite">${i + 1} de ${imgs.length}</span>
        <button type="button" class="rec-paso" data-rec-paso="1" aria-label="Imagen siguiente"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M8 4l6 6-6 6"/></svg></button></div>` : ''}
    </figure>`;
  }
  function pasoImagen(d) {
    const imgs = imagenesPasaje(estado.pasaje), el = $('#rec-principal');
    if (!el || imgs.length < 2) return;
    estado.recIdx = { id: estado.pasaje.id, i: (estado.recIdx.i + d + imgs.length) % imgs.length };
    el.outerHTML = imagenPasajeHTML(estado.pasaje);
    const b = main.querySelector(`[data-rec-paso="${d}"]`); if (b) b.focus();
  }
  // Ficha compacta de un recurso (acompañante, galería de mapas).
  function recItemHTML(f) {
    const mini = f.imagen ? `<button type="button" class="rec-mini" data-visor="${esc(f.id)}" aria-label="Ampliar: ${esc(f.titulo)}">${imgRec(f, '')}</button>` : '';
    const nota = f.nota_certeza ? `<span class="rec-nota">${esc(f.nota_certeza)}</span>` : '';
    return `<li class="rec-item${f.imagen ? '' : ' sin-imagen'}">${mini}<div class="rec-cuerpo"><strong class="rec-titulo">${esc(f.titulo)}</strong>
      <span class="rec-datos">${rotuloRec(f)} ${[autorFecha(f), esc(f.institucion)].filter(Boolean).join(' · ')}</span>${nota}
      <span class="rec-datos">${licRec(f)}${urlRec(f.url_fuente) ? ' · ' + linkRec(f.url_fuente, f.imagen ? 'Fuente' : 'Ver en la fuente') : ''}${f.imagen ? '' : ' <span class="etiqueta externa">Fuente externa</span>'}</span>
      <span class="rec-atrib">${esc(f.atribucion)}</span></div></li>`;
  }
  function medioHTML(f) {
    const verbo = f.tipo === 'audio' ? 'Escuchar' : 'Ver';
    const det = [f.autor, f.idioma === 'es' ? 'en español' : f.idioma === 'en' ? 'en inglés' : f.idioma, f.duracion].filter(Boolean).map(esc).join(' · ');
    const cuerpo = f.modo === 'incrustable' && N.esIdYoutube(f.youtube)
      ? (estado.recVideo === f.id ? iframeVideo({ youtube_id: f.youtube, titulo: f.titulo })
        : `<button type="button" class="video-fachada" data-rec-video="${esc(f.id)}" aria-label="Reproducir el video: ${esc(f.titulo)}"><img src="https://i.ytimg.com/vi/${esc(f.youtube)}/hqdefault.jpg" alt="" loading="lazy" onerror="this.remove()"><span class="video-play" aria-hidden="true"><svg viewBox="0 0 20 20"><path d="M7 5v10l8-5z"/></svg></span></button>`)
      : '';
    return `<li class="rec-medio">${cuerpo}<strong class="rec-titulo">${esc(f.titulo)}</strong>
      <span class="rec-datos"><span class="etiqueta externa">Fuente externa</span> ${f.tipo === 'audio' ? 'Audio' : 'Video'}${det ? ' · ' + det : ''}</span>
      ${f.nota_certeza ? `<span class="rec-nota">${esc(f.nota_certeza)}</span>` : ''}
      <span class="rec-datos">${licRec(f)} · ${linkRec(f.url_fuente, `${verbo} en ${esc(f.institucion.split(' (')[0] || 'la fuente')}`)}</span>
      <span class="rec-atrib">${esc(f.atribucion)}</span></li>`;
  }
  // Acompañante: lo relacionado con el versículo o el pasaje, sin repetir las imágenes del carrusel.
  function recursosAcompHTML(p, refs, sec, I) {
    if (!R) return '';
    const ks = refs.map(N.clave), A = N.relacionadosDe(R, ks, imagenesPasaje(p).map(f => f.id));
    let html = '';
    const objs = A.objetos.concat(A.imagenes);
    if (objs.length) html += sec('Imágenes y objetos', `<ul class="rec-lista">${objs.map(recItemHTML).join('')}</ul>`, I('M3 5h14v10H3zM3 13l4-4 3 3 2-2 5 5'));
    if (A.medios.length) html += sec('Videos y audio', `<ul class="rec-lista medios">${A.medios.map(medioHTML).join('')}</ul>`, I('M7 5v10l8-5z'));
    return html;
  }
  function mapasAntiguosHTML() {
    const ms = N.mapasAntiguos(R);
    if (!ms.length) return '';
    const con = ms.filter(f => f.imagen), sin = ms.filter(f => !f.imagen);
    return `<section class="mapas-antiguos" aria-labelledby="t-mapas-antiguos"><h2 id="t-mapas-antiguos">Mapas antiguos</h2>
      <p class="sub">Mapas impresos entre los siglos XVI y XIX: registran cómo se dibujaba entonces la geografía del relato, no cómo era en tiempos bíblicos. Pulsa uno para verlo ampliado.</p>
      ${con.length ? `<ul class="rec-galeria">${con.map(f => `<li><button type="button" class="rec-marco" data-visor="${esc(f.id)}" aria-label="Ampliar: ${esc(f.titulo)}">${imgRec(f, 'rec-img')}</button>
        <p class="rec-pie">${pieRec(f, true)}</p></li>`).join('')}</ul>` : ''}
      ${sin.length ? `<h3>Solo enlace (${sin.length})</h3><p class="meta">Sin imagen con licencia que permita copiarla: se enlaza a la institución que la conserva.</p><ul class="rec-lista">${sin.map(recItemHTML).join('')}</ul>` : ''}</section>`;
  }
  const TIPO_REC_TXT = { arte: 'Arte', reconstruccion: 'Reconstrucciones modernas', ilustracion: 'Ilustraciones modernas', arqueologia: 'Objetos históricos', mapa_antiguo: 'Mapas antiguos', video: 'Videos', audio: 'Audio' };
  function creditosHTML() {
    const fs = N.recursos(R);
    if (!fs.length) return '';
    const exc = (R.excluidas || []).length;
    return `<section><h2>Imágenes, objetos, mapas y medios</h2>
      <p>Cada imagen va rotulada: <strong>Arte · interpretación</strong> (la visión de un artista, con su fecha), <strong>Objeto histórico</strong> o <strong>Contexto de la época</strong> (registro con su museo), <strong>Mapa antiguo</strong>, <strong>Reconstrucción moderna</strong> o <strong>Ilustración moderna</strong>. Videos y audio son <span class="etiqueta externa">Fuente externa</span>. Lo que no tiene licencia abierta solo se enlaza.</p>
      <p class="meta">${R.auditado ? 'Catálogo revisado: cada imagen se comparó con su pasaje.' : 'Catálogo sin auditar todavía.'}${exc ? ` ${exc} ${exc === 1 ? 'ficha no se muestra' : 'fichas no se muestran'} (rechazada en la revisión o sin licencia que lo permita).` : ''}</p>
      ${Object.keys(TIPO_REC_TXT).map(t => { const xs = fs.filter(f => f.tipo === t); return xs.length ? `<h3>${TIPO_REC_TXT[t]} (${xs.length})</h3><ul class="fuentes creditos">${xs.map(f => `<li><strong>${esc(f.titulo)}</strong>${f.refs.length ? ` <span class="meta">· ${esc(f.refs.join(', '))}</span>` : ''}<br>${esc(f.atribucion)}<br><span class="meta">Licencia: ${esc(f.licencia)}${f.institucion ? ' · ' + esc(f.institucion) : ''}</span>${urlRec(f.url_fuente) ? ' · ' + linkRec(f.url_fuente, 'Fuente') : ''}</li>`).join('')}</ul>` : ''; }).join('')}
    </section>`;
  }

  /* ---------- Visor a pantalla completa con zoom ---------- */
  const visorDlg = $('#visor'), VISOR = { z: 1, f: null };
  function abrirVisor(id) {
    const f = recPorId(id); if (!f || !f.imagen || !visorDlg) return;
    VISOR.f = f; VISOR.z = 1;
    visorDlg.querySelector('#visor-titulo').textContent = f.titulo;
    visorDlg.querySelector('#visor-lienzo').innerHTML = `<img src="${esc(f.imagen)}" alt="${esc(altRec(f))}" draggable="false"${f.ancho && f.alto ? ` width="${f.ancho}" height="${f.alto}"` : ''}>`;
    visorDlg.querySelector('#visor-pie').innerHTML = `<p class="rec-pie">${pieRec(f, false)}${f.nota_certeza ? `<span class="rec-nota">${esc(f.nota_certeza)}</span>` : ''}</p>`;
    mostrar(visorDlg);
    zoomVisor(0);
  }
  // z = 1: la imagen cabe entera; cada paso multiplica por 1,5 (máx. 6×), manteniendo el centro de la vista.
  function zoomVisor(paso, cx, cy) {
    const lz = visorDlg.querySelector('#visor-lienzo'), img = lz.querySelector('img'), f = VISOR.f;
    if (!img || !f) return;
    const nw = f.ancho || img.naturalWidth || 1, nh = f.alto || img.naturalHeight || 1;
    const ajuste = Math.min(lz.clientWidth / nw, lz.clientHeight / nh);
    const antes = img.offsetWidth || nw * ajuste;
    const px = cx === undefined ? lz.clientWidth / 2 : cx, py = cy === undefined ? lz.clientHeight / 2 : cy;
    const rx = (lz.scrollLeft + px) / (img.offsetWidth || 1), ry = (lz.scrollTop + py) / (img.offsetHeight || 1);
    VISOR.z = paso === 0 ? 1 : Math.min(6, Math.max(1, VISOR.z * (paso > 0 ? 1.5 : 1 / 1.5)));
    img.style.width = Math.round(nw * ajuste * VISOR.z) + 'px'; img.style.height = Math.round(nh * ajuste * VISOR.z) + 'px';
    lz.classList.toggle('ampliado', VISOR.z > 1);
    if (paso !== 0 && antes) { lz.scrollLeft = rx * img.offsetWidth - px; lz.scrollTop = ry * img.offsetHeight - py; }
    const o = visorDlg.querySelector('#visor-pct'); if (o) o.textContent = Math.round(VISOR.z * 100) + ' %';
  }
  if (visorDlg) {
    visorDlg.addEventListener('wheel', e => { const lz = e.target.closest('#visor-lienzo'); if (!lz) return; e.preventDefault(); const r = lz.getBoundingClientRect(); zoomVisor(e.deltaY < 0 ? 1 : -1, e.clientX - r.left, e.clientY - r.top); }, { passive: false });
    visorDlg.addEventListener('dblclick', e => { const lz = e.target.closest('#visor-lienzo'); if (!lz) return; const r = lz.getBoundingClientRect(); if (VISOR.z > 1) zoomVisor(0); else { zoomVisor(1, e.clientX - r.left, e.clientY - r.top); zoomVisor(1, e.clientX - r.left, e.clientY - r.top); } });
    let arr = null;
    visorDlg.addEventListener('pointerdown', e => { const lz = e.target.closest('#visor-lienzo'); if (!lz || e.pointerType !== 'mouse' || e.button !== 0 || VISOR.z <= 1) return; e.preventDefault(); arr = { lz, x: e.clientX, y: e.clientY, sl: lz.scrollLeft, st: lz.scrollTop }; lz.classList.add('arrastrando'); });
    visorDlg.addEventListener('pointermove', e => { if (arr) { arr.lz.scrollLeft = arr.sl - (e.clientX - arr.x); arr.lz.scrollTop = arr.st - (e.clientY - arr.y); } });
    const fin = () => { if (arr) { arr.lz.classList.remove('arrastrando'); arr = null; } };
    visorDlg.addEventListener('pointerup', fin); visorDlg.addEventListener('pointercancel', fin);
    visorDlg.addEventListener('close', () => { visorDlg.querySelector('#visor-lienzo').innerHTML = ''; VISOR.f = null; });
    window.addEventListener('resize', () => { if (visorDlg.open && VISOR.f) zoomVisor(0); });
  }

  /* ---------- Fuentes: textos originales ---------- */
  function fuentesOriginalesHTML() {
    const O = ORIG.o, G = ORIG.g;
    const lista = [...((O && O.fuentes) || []), ...(G ? [{ id: 'griego', nombre: G.fuente, licencia: G.licencia, url: G.url }] : [])];
    const gpl = G && /gpl/i.test(G.licencia || '');
    return `<section><h2>De dónde sale el texto</h2>
      <p>La app muestra junto a la Reina-Valera el texto hebreo y el griego de la Septuaginta, y los manuscritos antiguos que contienen cada pasaje, con enlace a su institución. Las imágenes de los manuscritos no se copian: se enlazan.</p>
      ${QUE_ES.replace('<details class="plegable">', '<details class="plegable" open>')}
      ${estadoCarga('o')}${estadoCarga('g')}
      ${lista.length ? `<ul class="fuentes">${lista.map(f => `<li><strong>${esc(f.nombre || f.id)}</strong><br>Licencia: ${esc(f.licencia || 'sin indicar')}${urlSegura(f.url) ? `<br>${extLink(f.url, f.url)}` : ''}</li>`).join('')}</ul>` : ''}
      ${gpl ? `<p class="aviso-licencia"><strong>Aviso de licencia del texto griego:</strong> ${esc(G.fuente)} se distribuye con licencia GNU GPL versión 3 (GPL-3.0). Puedes copiarlo, modificarlo y redistribuirlo bajo esa misma licencia, conservando este aviso; se ofrece sin ninguna garantía. Texto de la licencia: <a href="https://www.gnu.org/licenses/gpl-3.0.html" target="_blank" rel="noopener noreferrer">gnu.org/licenses/gpl-3.0</a> <span class="etiqueta externa">Fuente externa</span></p>` : ''}
      ${O && (O.testigos || []).length ? `<h3>Manuscritos</h3><ul class="testigos">${O.testigos.map(testigoHTML).join('')}</ul>` : ''}
      <h3>Voz</h3><p>El audio usa la voz sintética del dispositivo: pronunciación moderna, no la antigua. Los videos se cargan desde YouTube (youtube-nocookie.com) solo al pulsarlos.</p></section>`;
  }

  /* ---------- Árbol ---------- */
  // Árbol perezoso: solo se generan las filas de las ramas desplegadas (estado.abiertos); al desplegar o
  // plegar se insertan o quitan filas en el DOM sin volver a pintar la vista.
  const tituloAtajo = a => `${nombre(a.desde)} → ${a.hijosDeFinal ? 'hijos de ' : ''}${nombre(a.hasta)}`;
  function abrirHasta(id) {
    const u = N.rutaArbol(D, id); if (!u) return null;
    if (!estado.abiertos) estado.abiertos = N.arbolInicial(D, 2);
    u.ruta.slice(0, -1).forEach(x => estado.abiertos.add(x));
    estado.foco = u.nodo;
    estado.aviso = u.como === 'conyuge' ? `${nombre(id)} aparece como cónyuge de ${nombre(u.nodo)}.` : u.como === 'madre' ? `${nombre(id)} aparece como madre de ${nombre(u.nodo)}.` : '';
    return u;
  }
  function vistaArbol(args) {
    if (!estado.abiertos) estado.abiertos = N.arbolInicial(D, 2);
    const h = args && args[0] ? args[0] : null;
    if (h !== estado.focoHash) { estado.focoHash = h; estado.foco = null; estado.aviso = ''; if (h) { estado.lineaSolo = false; if (!abrirHasta(h) && N.sinParentesco(D).includes(h)) { estado.sinParAbierta = true; estado.foco = h; estado.aviso = `${nombre(h)} no tiene parentesco registrado en el texto: está en la lista del final.`; } } }
    const atajos = N.atajosLinea(D);
    const lp = atajos.length ? [atajos[0].desde].concat(atajos.map(a => a.hasta)).map(nombre).join(' → ') : '';
    const g = estado.vistaArbol === 'grafico';
    return `<h1 tabindex="-1">Árbol genealógico</h1>
      <p class="sub">Cada vínculo indica si <span class="insignia texto">Texto</span> lo dice explícitamente o es <span class="insignia inferido">Inferido</span>, con su versículo. Los años son <span class="insignia texto">Texto</span> si el versículo da la edad total y <span class="insignia calculo">Cálculo</span> si sale de sumar cifras; «año 0 → 930» cuenta desde la creación de Adán y siempre es cálculo.</p>
      <p class="leyenda-arbol meta"><span class="ley hombre">Hombre</span><span class="ley mujer">Mujer</span><span class="ley sin-nombre">Sin nombre en el texto</span><span class="ley-txt"><b>⚭</b> matrimonio</span><span class="ley-txt"><b>+</b> madre de sus hijos sin matrimonio registrado</span>${lp ? `<span class="ley linea">Línea principal (${esc(lp)})</span>` : ''}</p>
      <div class="herr herr-arbol">
        <fieldset class="segmentos"><legend>Vista</legend>${[['lista', 'Lista'], ['grafico', 'Árbol']].map(([v, t]) => `<label><input type="radio" name="vista-arbol" value="${v}" ${estado.vistaArbol === v ? 'checked' : ''}><span>${t}</span></label>`).join('')}</fieldset>
        ${segTrad()}
        ${g ? `<div class="ga-zoom" role="group" aria-label="Tamaño del árbol"><button type="button" class="boton secundario" data-zoom="-1" aria-label="Alejar">−</button><span class="meta" id="ga-zoom-txt">${Math.round(estado.gaZoom * 100)} %</span><button type="button" class="boton secundario" data-zoom="1" aria-label="Acercar">+</button></div>` : ''}
      </div>
      <div class="herr">
        <div class="campo"><label for="buscar">Buscar persona</label><input id="buscar" type="search" autocomplete="off" placeholder="Nombre…" value="${esc(estado.q)}"></div>
      </div>
      <ul class="resultados" id="resultados" aria-live="polite">${resultadosHTML()}</ul>
      ${atajos.length ? `<div class="herr atajos" role="group" aria-label="Ver solo una línea"><span class="atajos-txt meta">Ver solo la línea:</span>${atajos.map(a => `<button type="button" class="boton${estado.lineaSolo === a.id ? '' : ' secundario'}" data-atajo="${esc(a.id)}" aria-pressed="${estado.lineaSolo === a.id}">${esc(tituloAtajo(a))}</button>`).join('')}
        ${estado.lineaSolo ? '<button type="button" class="boton secundario" id="btn-todo">Mostrar todo el árbol</button>' : ''}</div>` : ''}
      ${estado.lineaSolo ? '' : '<div class="herr"><button type="button" class="boton secundario" id="btn-plegar">Plegar todo</button><button type="button" class="boton secundario" id="btn-desplegar">Desplegar todo</button></div>'}
      ${(m => `<p><button type="button" class="boton secundario" id="btn-mujeres" aria-pressed="${estado.mujeres}">Mujeres: ${m.conNombre} con nombre, ${m.sinNombre} sin nombre</button></p>`)(N.contarMujeres(D))}
      <p class="meta" id="arbol-aviso" aria-live="polite">${esc(estado.aviso) || (estado.lineaSolo ? '' : `${N.indice(D).personas.size} personas. Las ramas empiezan plegadas: despliégalas con ▸ o busca un nombre para ir a él.`)}</p>
      <div id="arbol"${estado.mujeres ? ' class="resaltar-mujeres"' : ''}>${arbolHTML()}</div>`;
  }
  function resultadosHTML() {
    if (!estado.q) return '';
    const r = N.buscar(D, estado.q, 20);
    return r.length ? r.map(p => `<li><button type="button" class="persona-btn${p.sexo === 'f' ? ' mujer' : p.sexo === 'm' ? ' hombre' : ' indef'}" data-ir-arbol="${esc(p.id)}" aria-label="Ir a ${esc(p.nombre || p.id)} en el árbol">${esc(p.nombre || p.id)}${p.primera_ref ? ` <span class="meta">${esc(p.primera_ref)}</span>` : ''}</button></li>`).join('') : '<li class="meta">Sin resultados.</li>';
  }
  // Lleva a una persona: despliega sus ascendientes, pinta y la centra.
  function irArbol(id) {
    const u = abrirHasta(id);
    if (!u) {
      if (!N.sinParentesco(D).includes(id)) { abrirFicha(id); return; }
      // Sin parentesco: abre su sección y la señala.
      estado.lineaSolo = false; estado.sinParAbierta = true; estado.foco = id; estado.focoHash = id;
      estado.aviso = `${nombre(id)} no tiene parentesco registrado en el texto: está en la lista del final.`;
      try { history.replaceState(null, '', `#arbol/${encodeURIComponent(id)}`); } catch (e) { /* file:// */ }
      rerender();
      const li = main.querySelector('.foco-sp');
      if (li) { li.scrollIntoView({ block: 'center' }); const b = li.querySelector('.persona-btn'); if (b) b.focus({ preventScroll: true }); }
      return;
    }
    estado.lineaSolo = false; estado.focoHash = id;
    try { history.replaceState(null, '', `#arbol/${encodeURIComponent(id)}`); } catch (e) { /* file:// */ }
    rerender();
    const f = main.querySelector('.fila.foco, .ga-fam.foco');
    if (f) { f.scrollIntoView({ block: 'center', inline: 'center' }); const b = f.querySelector('.persona-btn'); if (b) b.focus({ preventScroll: true }); }
  }
  // Vínculo con los padres: una sola insignia si padre y madre comparten certeza y versículo; si no, una por cada uno.
  const SUPUESTA = 'Madre supuesta: es la única esposa registrada de su padre, pero el texto no dice que sea su madre';
  function vinculosHTML(n) {
    const v = n.vinculos || [], m = n.madres || [], k = r => N.claseCerteza(r.certeza) + '|' + r.ref;
    if (!m.length) return v.map(r => insignia(r.certeza, r.ref, r.tipo)).join('') + (N.madreSupuesta(D, n.id) ? insignia('inferido', '', 'madre', SUPUESTA) : '');
    if (v.length && v.concat(m).every(r => k(r) === k(v[0]))) return insignia(v[0].certeza, v[0].ref, 'padres', 'Padre y madre');
    return v.map(r => insignia(r.certeza, r.ref, r.tipo)).join('') + m.map(r => insignia(r.certeza, r.ref, 'madre')).join('');
  }
  // Años vividos (verde si lo dice el texto, violeta si es cálculo) y de qué año a qué año desde Adán (siempre cálculo).
  // En "Comparar" se muestran TM y LXX solo si difieren.
  function vidaHTML(id) {
    const C = N.crono(D), ts = trads();
    let vs = ts.map(tr => ({ tr, v: N.vida(D, id, tr, C ? comboDe(tr) : null) })).filter(x => x.v.total || x.v.nacimiento !== null);
    if (!vs.length) return '';
    const firma = x => [x.v.total && x.v.total.valor, x.v.nacimiento, x.v.muerte].join('|');
    if (vs.length > 1 && firma(vs[0]) === firma(vs[1])) vs = [vs[0]];
    const pre = tr => ts.length > 1 && vs.length > 1 ? `<span class="ins-pre">${tr}</span>` : '';
    return `<span class="vida">${vs.map(({ tr, v }) => {
      const t = v.total, ct = t ? (t.derivado ? 'calculo' : N.claseCerteza(t.certeza)) : '';
      const tot = t ? `<button type="button" class="insignia dato-vida ${ct}" data-edad="${esc(id)}|total|${tr}" title="Años que vivió (${tr}): ${ct === 'texto' ? 'lo dice el texto, ' + esc(t.ref) : 'cálculo a partir del texto'}" aria-label="${esc(nombre(id))} vivió ${t.valor} años (${tr}, ${CERT_TXT[ct].toLowerCase()})">${pre(tr)}${t.valor} años</button>` : '';
      const ran = v.nacimiento !== null ? `<button type="button" class="insignia dato-vida calculo" data-ev="${esc(v.evNac)}" title="Años contados desde la creación de Adán (${tr}). Cálculo con los supuestos elegidos en Tiempo." aria-label="Nace en el año ${v.nacimiento}${v.muerte !== null ? ' y muere en el ' + v.muerte : ''} desde Adán (${tr}, cálculo)">${pre(tr)}${v.muerte !== null ? `año ${v.nacimiento} → ${v.muerte}` : `nace año ${v.nacimiento}`}</button>` : '';
      return tot + ran;
    }).join('')}</span>`;
  }
  // La otra persona de una pareja, en la misma línea: ⚭ si el texto registra el matrimonio; "+" si solo es madre de sus hijos.
  const lazoHTML = u => u.vinculo ? '<span class="lazo" title="Cónyuges" aria-label="cónyuge:">⚭</span>' : '<span class="lazo sin-matr" title="Madre de sus hijos; el texto no registra matrimonio" aria-label="con:">+</span>';
  const parejaHTML = u => `<span class="pareja${u.vinculo ? '' : ' sin-matr'}"><span class="par-nombre">${lazoHTML(u)}${btnPersona(u.pareja)}</span>${vidaHTML(u.pareja)}${notaVinculo(u.vinculo)}${u.vinculo ? insignia(u.vinculo.certeza, u.vinculo.ref) : ''}</span>`;
  // Una fila: la persona y, en la misma línea, su pareja o parejas. opc: {solo (vista de línea: sin plegar), gen}
  function filaHTML(n, prof, opc) {
    opc = opc || {};
    const linea = N.lineaPrincipal(D), abierto = opc.solo || estado.abiertos.has(n.id), nh = opc.solo ? 0 : n.hijos.length;
    const gen = opc.gen !== undefined ? opc.gen : prof;
    const us = N.uniones(D, n), parejas = us.filter(u => u.pareja);
    // Con varias parejas y las ramas a la vista, cada rama lleva los datos de su pareja; aquí basta el nombre.
    // Las que no tienen rama visible (sin hijos, fila plegada o línea sola) muestran aquí su versículo, nota y años.
    const conRama = u => !opc.solo && abierto && us.length > 1 && u.hijos.length;
    return `<li class="fila${linea.has(n.id) ? ' en-linea' : ''}${estado.foco === n.id ? ' foco' : ''}" data-fila="${esc(n.id)}" data-prof="${prof}" style="--n:${Math.min(prof, 10)}">
        <span class="gen" title="Generación ${gen + 1}">${gen + 1}</span>
        ${nh ? `<button type="button" class="plegar" data-plegar="${esc(n.id)}" aria-expanded="${abierto}" aria-label="${abierto ? 'Plegar' : 'Desplegar'} descendencia de ${esc(nombre(n.id))} (${nh})">${abierto ? '▾' : '▸'}</button>` : '<span class="plegar vacio" aria-hidden="true"></span>'}
        <span class="fila-cont"><span class="pareja principal">${btnPersona(n.id)}${vidaHTML(n.id)}${etiquetaTrad(n.id)}</span>${parejas.length > 1
          ? `<span class="parejas-varias">${parejas.map(u => conRama(u) ? `<span class="pareja"><span class="par-nombre">${lazoHTML(u)}${btnPersona(u.pareja)}</span></span>` : parejaHTML(u)).join('')}</span>` : parejas.map(parejaHTML).join('')}${(v => v ? `<span class="vinc-padres">${v}</span>` : '')(vinculosHTML(n))}${nh && !abierto ? `<span class="meta">(${nh} ${nh === 1 ? 'hijo' : 'hijos'})</span>` : ''}</span></li>`;
  }
  // Con varias parejas, los hijos de cada una van en su propia rama.
  const ramaHTML = (u, n, prof) => `<li class="grupo-madre" data-prof="${prof}" style="--n:${Math.min(prof, 10)}"><span class="grupo-txt">${u.pareja
    ? `Hijos de ${esc(nombre(n.id))} ${u.vinculo ? 'y' : 'con'} ${btnPersona(u.pareja)}${vidaHTML(u.pareja)}${u.vinculo ? insignia(u.vinculo.certeza, u.vinculo.ref, '', 'Matrimonio') : ''}${notaVinculo(u.vinculo)}` : `Hijos de ${esc(nombre(n.id))}: madre no indicada en el texto`} <span class="meta">(${u.hijos.length})</span></span></li>`;
  // Filas de los hijos (y sus ramas abiertas), una rama por pareja cuando hay más de una.
  function hijosHTML(n, prof, fila) {
    fila = fila || (h => bloqueHTML(h, prof + 1));
    const us = N.uniones(D, n);
    if (us.length < 2) return n.hijos.map(fila).join('');
    return us.filter(u => u.hijos.length).map(u => ramaHTML(u, n, prof + 1) + u.hijos.map(fila).join('')).join('');
  }
  const bloqueHTML = (n, prof) => filaHTML(n, prof) + (n.hijos.length && estado.abiertos.has(n.id) ? hijosHTML(n, prof) : '');
  // Nodo para una persona de la línea aunque no sea nodo del bosque (p. ej. si la ruta pasa por una madre).
  function nodoLinea(id, padreId) {
    const n = N.nodoArbol(D, id), I = N.indice(D);
    const vinculos = (I.padres.get(id) || []).filter(x => x.de === padreId);
    return n ? Object.assign({}, n, { vinculos: padreId ? vinculos : n.vinculos }) : { id, vinculos, hijos: [], conyuges: (I.conyuges.get(id) || []).filter((r, i, a) => a.findIndex(x => x.otro === r.otro) === i), madres: [] };
  }
  function lineaHTML(at) {
    const M = N.mapaArbol(D), gen = (id, i) => { const x = M.nodos.get(id); return x ? x.prof : i; };
    let html = at.ruta.map((id, i) => filaHTML(nodoLinea(id, at.ruta[i - 1]), i, { solo: true, gen: gen(id, i) })).join('');
    if (at.extra.length) {
      const fin = at.ruta[at.ruta.length - 1], nf = N.nodoArbol(D, fin), prof = at.ruta.length - 1, g0 = gen(fin, prof) + 1;
      const fila = h => filaHTML(h, prof + 1, { solo: true, gen: g0 });
      html += nf ? hijosHTML(nf, prof, fila) : at.extra.map(id => fila(nodoLinea(id, fin))).join('');
    }
    return `<ul class="arbol" aria-label="Línea ${esc(tituloAtajo(at))}">${html}</ul>`;
  }
  function arbolHTML() {
    const bosque = N.construirBosque(D);
    if (!bosque.length) return '<p>No hay relaciones en los datos.</p>';
    const g = estado.vistaArbol === 'grafico';
    if (estado.lineaSolo) {
      const at = N.atajosLinea(D).find(a => a.id === estado.lineaSolo);
      if (at) return g ? lienzoHTML(gaLinea(at), `Línea ${tituloAtajo(at)}`) : lineaHTML(at);
      estado.lineaSolo = false;
    }
    const otras = bosque.slice(1);
    if (g) return `${lienzoHTML(gaNodo(bosque[0]), `Descendencia de ${nombre(bosque[0].id)}`)}
      ${otras.length ? `<h2>Otras ramas (${otras.length})</h2><p class="meta">Familias sin enlace conocido con la rama principal.</p>${lienzoHTML(otras.map(r => gaNodo(r)).join(''), 'Otras ramas', true)}` : ''}
      ${sinParHTML()}`;
    return `<ul class="arbol" aria-label="Descendencia de ${esc(nombre(bosque[0].id))}">${bloqueHTML(bosque[0], 0)}</ul>
      ${otras.length ? `<h2>Otras ramas (${otras.length})</h2><p class="meta">Familias sin enlace conocido con la rama principal.</p><ul class="arbol" aria-label="Otras ramas">${otras.map(r => bloqueHTML(r, 0)).join('')}</ul>` : ''}
      ${sinParHTML()}`;
  }

  /* ---- Vista gráfica: árbol genealógico de arriba abajo (pareja en una fila, hijos debajo) ---- */
  const gaTarjeta = (id, extra, cls, boton) => `<div class="ga-tarjeta${cls || ''}">${btnPersona(id)}${vidaHTML(id)}${extra || ''}${boton || ''}</div>`;
  // Certeza del vínculo con sus padres, para colorear la línea que llega a la tarjeta: inferido si alguno lo es.
  const certNodo = n => { const rs = (n.vinculos || []).concat(n.madres || []); return !rs.length ? '' : rs.some(r => N.claseCerteza(r.certeza) === 'inferido') || N.madreSupuesta(D, n.id) ? 'inferido' : 'texto'; };
  // Un nodo con su pareja y sus hijos. opc: {solo (línea: sin plegar), sig (HTML del siguiente de la línea), forzar (abierto, hijos sin plegar)}
  // Las líneas no son CSS: las dibuja conectoresGA() desde el ⚭ de cada pareja hasta la tarjeta de cada hijo.
  function gaNodo(n, opc) {
    opc = opc || {};
    const linea = N.lineaPrincipal(D), us = N.uniones(D, n), parejas = us.filter(u => u.pareja);
    const nh = opc.solo || opc.forzar ? 0 : n.hijos.length, abierto = opc.solo || opc.forzar || estado.abiertos.has(n.id);
    // El botón de plegar va bajo el ⚭ si hay una sola pareja (de ahí baja la descendencia); si no, bajo la persona.
    const btn = nh ? `<button type="button" class="ga-plegar" data-ga-plegar="${esc(n.id)}" aria-expanded="${abierto}" aria-label="${abierto ? 'Plegar' : 'Desplegar'} descendencia de ${esc(nombre(n.id))} (${nh})">${abierto ? '▾ plegar' : `▸ ${nh} ${nh === 1 ? 'hijo' : 'hijos'}`}</button>` : '';
    const enLazo = parejas.length === 1;
    const lazo = u => u.vinculo ? `<span class="lazo" data-pareja="${esc(u.pareja)}" title="Cónyuges"><span aria-label="cónyuge:">⚭</span>${enLazo ? btn : ''}</span>`
      : `<span class="lazo sin-matr" data-pareja="${esc(u.pareja)}" title="Madre de sus hijos; el texto no registra matrimonio"><span aria-label="con:">+</span>${enLazo ? btn : ''}</span>`;
    const fam = `<div class="ga-fam${linea.has(n.id) ? ' en-linea' : ''}${estado.foco === n.id ? ' foco' : ''}${btn ? ' con-boton' : ''}" data-ga="${esc(n.id)}" data-cert="${certNodo(n)}" data-madre="${esc(((n.madres || [])[0] || {}).de || '')}">
      ${gaTarjeta(n.id, etiquetaTrad(n.id) + vinculosHTML(n), ' principal', enLazo ? '' : btn)}
      ${parejas.map(u => `${lazo(u)}${gaTarjeta(u.pareja, notaVinculo(u.vinculo) + (u.vinculo ? insignia(u.vinculo.certeza, u.vinculo.ref, '', 'Matrimonio') : ''))}`).join('')}</div>`;
    let sub = '';
    if (opc.solo && !opc.forzar) sub = opc.sig ? `<ul>${opc.sig}</ul>` : '';
    else if (abierto && n.hijos.length) {
      const hijo = h => gaNodo(h, opc.forzar ? { solo: true } : null);
      sub = us.length < 2 ? `<ul>${n.hijos.map(hijo).join('')}</ul>`
        : `<ul>${us.filter(u => u.hijos.length).map(u => `<li class="ga-rama"${u.pareja ? ` data-pareja="${esc(u.pareja)}"` : ''}><div class="ga-rama-txt">${u.pareja ? `hijos con ${esc(nombre(u.pareja))}` : 'madre no indicada'}</div><ul>${u.hijos.map(hijo).join('')}</ul></li>`).join('')}</ul>`;
    }
    return `<li>${fam}${sub}</li>`;
  }
  // Dibuja las líneas del árbol gráfico en un SVG bajo las tarjetas, en coordenadas del contenido del lienzo
  // (no dependen del desplazamiento ni del zoom). Tronco neutro desde la pareja; el último tramo de cada hijo,
  // con el color de la certeza de su vínculo (Texto continuo, Inferido discontinuo).
  function conectoresGA(l) {
    const cont = l.querySelector('.ga-contenido'); if (!cont) return;
    let svg = l.querySelector(':scope > svg.ga-lineas');
    if (!svg) { svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.setAttribute('class', 'ga-lineas'); svg.setAttribute('aria-hidden', 'true'); l.prepend(svg); }
    const lr = l.getBoundingClientRect(), sl = l.scrollLeft, st = l.scrollTop, z = estado.gaZoom;
    const pt = (el, fx, fy) => { const r = el.getBoundingClientRect(); return { x: Math.round(r.left - lr.left + sl + r.width * fx) + .5, y: Math.round(r.top - lr.top + st + r.height * fy) }; };
    const d = { base: '', texto: '', inferido: '' };
    const tramo = (s, hijos, escalon) => {
      if (!s || !hijos.length) return;
      const tops = hijos.map(h => pt(h.el, .5, 0)), mid = Math.min(...tops.map(t => t.y)) - Math.round((10 + (escalon || 0) * 7) * z);
      const xs = tops.map(t => t.x).concat(s.x);
      d.base += `M${s.x} ${s.y}V${mid}M${Math.min(...xs)} ${mid}H${Math.max(...xs)}`;
      tops.forEach((t, i) => { const k = hijos[i].cert === 'texto' || hijos[i].cert === 'inferido' ? hijos[i].cert : 'base'; d[k] += `M${t.x} ${mid}V${t.y}`; });
    };
    const hijosDe = ul => [...ul.children].map(c => { const f = c.querySelector(':scope > .ga-fam'); return f && { el: f.querySelector(':scope > .ga-tarjeta.principal'), cert: f.dataset.cert, madre: f.dataset.madre }; }).filter(Boolean);
    l.querySelectorAll('.ga-fam').forEach(f => {
      const ul = f.parentElement.querySelector(':scope > ul'); if (!ul) return;
      const principal = pt(f.querySelector(':scope > .ga-tarjeta.principal'), .5, 1);
      // Una pareja: desde el ⚭ (entre los dos). Varias: desde la tarjeta de esa madre, porque un ⚭ entre dos esposas confundiría.
      const varias = f.querySelectorAll(':scope > .lazo').length > 1;
      const desde = id => { const z0 = id && f.querySelector(`:scope > .lazo[data-pareja="${CSS.escape(id)}"]`); return !z0 ? principal : pt(varias ? z0.nextElementSibling : z0, .5, 1); };
      const ramas = [...ul.children].filter(x => x.classList.contains('ga-rama'));
      if (!ramas.length) {
        // Sin ramas: de la única pareja; con varias (línea sola), del ⚭ de la madre de cada hijo.
        const lz = f.querySelectorAll(':scope > .lazo'), grupos = new Map();
        hijosDe(ul).forEach(h => { const k = lz.length === 1 ? lz[0].dataset.pareja : (h.madre || ''); if (!grupos.has(k)) grupos.set(k, []); grupos.get(k).push(h); });
        [...grupos].forEach(([k, hs], i) => tramo(desde(k), hs, i));
        return;
      }
      ramas.forEach((r, i) => {
        const lab = r.querySelector(':scope > .ga-rama-txt'), sub = r.querySelector(':scope > ul');
        tramo(desde(r.dataset.pareja), [{ el: lab, cert: '' }], i);
        if (sub) tramo(pt(lab, .5, 1), hijosDe(sub));
      });
    });
    svg.style.width = svg.style.height = '0';
    svg.style.width = l.scrollWidth + 'px'; svg.style.height = l.scrollHeight + 'px';
    svg.innerHTML = ['base', 'texto', 'inferido'].map(k => d[k] ? `<path class="ga-l-${k}" d="${d[k]}"/>` : '').join('');
  }
  const conectoresTodos = () => main.querySelectorAll('.ga-lienzo').forEach(conectoresGA);
  // Línea sola: una cadena de arriba abajo; al final, si toca, todos los hijos (p. ej. los de Jacob).
  function gaLinea(at) {
    const r = at.ruta;
    let html = '';
    for (let i = r.length - 1; i >= 0; i--) {
      const n = nodoLinea(r[i], r[i - 1]);
      html = i === r.length - 1 ? gaNodo(n, at.extra.length ? { forzar: true } : { solo: true }) : gaNodo(n, { solo: true, sig: html });
    }
    return html;
  }
  const lienzoHTML = (lis, etiqueta, bosque) => `<div class="ga-lienzo" tabindex="0" aria-label="${esc(etiqueta)}: árbol gráfico, desplázate para recorrerlo"><div class="ga-contenido" style="zoom:${estado.gaZoom}"><ul class="ga${bosque ? ' ga-bosque' : ''}">${lis}</ul></div></div>`;
  // Despliega o pliega una rama del árbol gráfico manteniendo el nodo en el mismo sitio de la pantalla.
  function alternarGA(id) {
    const sel = `.ga-fam[data-ga="${CSS.escape(id)}"]`, a = main.querySelector(sel), r0 = a && a.getBoundingClientRect();
    if (estado.abiertos.has(id)) estado.abiertos.delete(id); else estado.abiertos.add(id);
    const pos = [...main.querySelectorAll('.ga-lienzo')].map(l => [l.scrollLeft, l.scrollTop]);
    rerender();
    main.querySelectorAll('.ga-lienzo').forEach((l, i) => { if (pos[i]) { l.scrollLeft = pos[i][0]; l.scrollTop = pos[i][1]; } });
    const b = main.querySelector(sel);
    if (b && r0) { const r1 = b.getBoundingClientRect(), l = b.closest('.ga-lienzo'); l.scrollLeft += r1.left - r0.left; l.scrollTop += r1.top - r0.top; }
    const p = main.querySelector(`[data-ga-plegar="${CSS.escape(id)}"]`); if (p) p.focus({ preventScroll: true });
  }
  // Personas sin parentesco registrado: sección plegable al final, cada una abre su ficha.
  function sinParHTML() {
    const ids = N.sinParentesco(D);
    if (!ids.length) return '';
    return `<details class="plegable sin-parentesco" id="sin-parentesco"${estado.sinParAbierta ? ' open' : ''}>
      <summary>Personas sin parentesco registrado en el texto (${ids.length})</summary>
      <ul class="quien">${ids.map(id => { const p = N.persona(D, id) || {}; return `<li class="${estado.foco === id ? 'foco-sp' : ''}" data-sp="${esc(id)}">${btnPersona(id)}${p.rol ? `<span class="contexto">${esc(p.rol)}</span>` : ''}${p.primera_ref ? `<span class="meta">${refHTML(p.primera_ref)}</span>` : ''}</li>`; }).join('')}</ul></details>`;
  }
  // Despliega o pliega una rama en el DOM, sin repintar el resto.
  function alternarRama(id) {
    const fila = main.querySelector(`.fila[data-fila="${CSS.escape(id)}"]`), n = N.nodoArbol(D, id);
    if (!fila || !n) return;
    const prof = +fila.dataset.prof, abrir = !estado.abiertos.has(id);
    if (abrir) estado.abiertos.add(id); else estado.abiertos.delete(id);
    let s = fila.nextElementSibling;
    while (s && +s.dataset.prof > prof) { const x = s.nextElementSibling; s.remove(); s = x; }
    fila.insertAdjacentHTML('afterend', filaHTML(n, prof, { agrupado: fila.dataset.agrupado === '1' }) + (abrir ? hijosHTML(n, prof) : ''));
    const nueva = fila.nextElementSibling; fila.remove();
    const b = nueva && nueva.querySelector('[data-plegar]'); if (b) b.focus();
  }

  /* ---------- Edades ---------- */
  function celda(id, tipo, trad, dif) {
    const e = N.edad(D, id, tipo, trad);
    const cls = dif && dif !== 'igual' ? ' class="difiere"' : '';
    if (!e) return `<td${cls}><span class="vacio" aria-label="sin dato">—</span></td>`;
    return `<td${cls}><button type="button" class="celda${e.derivado ? ' calculo' : ''}" data-edad="${esc(id)}|${tipo}|${trad}" aria-label="${esc(nombre(id))}, ${TIPO_TXT[tipo]} ${trad}: ${e.valor}${e.derivado ? ' (cálculo)' : ''}">${e.valor}${e.derivado ? '<span class="marca-calc" aria-hidden="true">*</span>' : ''}</button></td>`;
  }
  /* ---------- Tiempo: línea de tiempo, vidas solapadas y tabla de edades ---------- */
  // Génesis no da fechas: todo año es CÁLCULO (años desde la creación de Adán) y se presenta como tal.
  const trads = () => estado.trad === 'ambas' ? ['TM', 'LXX'] : [estado.trad === 'LXX' ? 'LXX' : 'TM'];
  const tradSimple = () => estado.trad === 'LXX' ? 'LXX' : 'TM'; // "comparar" → TM donde solo cabe una
  const eleg = () => N.elecciones(D, store.get('biblia.supuestos', {}));
  const comboDe = tr => N.combinacion(D, tr, eleg());
  const TRAD_TXT = { TM: 'Texto Masorético (TM)', LXX: 'Septuaginta (LXX)' };
  const TIPO_EV = { nacimiento: 'Nacimiento', muerte: 'Muerte', evento: 'Suceso' };
  const ICO_EV = {
    nacimiento: '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="5.5"/><path d="M10 7v6M7 10h6"/></svg>',
    muerte: '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3.5v13M6 7.5h8"/></svg>',
    evento: '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3.5l6.5 6.5-6.5 6.5L3.5 10z"/></svg>',
    diluvio: '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M2.5 8c2.5-2 5-2 7.5 0s5 2 7.5 0M2.5 13c2.5-2 5-2 7.5 0s5 2 7.5 0"/></svg>',
    hito: '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="5" stroke-dasharray="2 2.2"/></svg>'
  };
  const icoEv = ev => N.esDiluvio(ev) ? ICO_EV.diluvio : ICO_EV[ev.tipo] || ICO_EV.evento;
  const anioTxt = a => a === null || a === undefined ? 'sin año' : `año ${a}`;
  const anios = n => `${n} ${Math.abs(n) === 1 ? 'año' : 'años'}`;
  const relTxt = d => `${anios(Math.abs(d.anios))} ${d.anios < 0 ? 'antes' : 'después'} de «${esc(d.titulo)}»`;
  // "años desde la creación de Adán" sin el "(cálculo)" final: la insignia ya lo dice.
  const unidadTxt = C => String(C.unidad || '').replace(/\s*\(c[áa]lculo\)\s*$/i, '') || 'años desde la creación de Adán';

  function vistaTiempo(args) {
    let sub = args && args[0];
    if (!['linea', 'vidas', 'tabla'].includes(sub)) sub = 'linea';
    estado.focoEv = sub === 'linea' && args[1] ? args[1] : null;
    const pest = [['linea', 'Línea de tiempo'], ['vidas', 'Vidas solapadas'], ['tabla', 'Tabla de edades']];
    return `<h1 tabindex="-1">Tiempo</h1>
      <nav class="subvistas" aria-label="Vistas de Tiempo">${pest.map(([id, t]) => `<a href="#tiempo/${id}"${sub === id ? ' aria-current="page"' : ''}>${t}</a>`).join('')}</nav>
      ${controlesTiempo(sub !== 'tabla')}
      ${sub === 'linea' ? lineaTiempoHTML() : sub === 'vidas' ? vidasHTML() : tablaHTML()}`;
  }
  // Tradición (TM / LXX / comparar) y un selector por supuesto; la elección se guarda.
  const segTrad = () => `<fieldset class="segmentos"><legend>Tradición</legend>${[['TM', 'TM'], ['LXX', 'LXX'], ['ambas', 'Comparar']].map(([v, t]) => `<label><input type="radio" name="trad" value="${v}" ${estado.trad === v ? 'checked' : ''}><span>${t}</span></label>`).join('')}</fieldset>`;
  function controlesTiempo(conSupuestos) {
    const C = N.crono(D), e = eleg();
    return `${segTrad()}
      ${conSupuestos && C && C.supuestos.length ? `<details class="plegable supuestos-caja" id="supuestos"${estado.supAbiertos ? ' open' : ''}>
        <summary>Supuestos del cálculo (${C.supuestos.length}) · ${C.supuestos.filter(s => e[s.id] !== s.defecto).length ? 'hay cambios' : 'por defecto'}</summary>
        <div class="supuestos">${C.supuestos.map(s => `<fieldset class="supuesto"><legend>${esc(s.pregunta || s.id)}</legend>
        ${s.opciones.map(o => `<label class="opcion"><input type="radio" name="sup-${esc(s.id)}" data-sup="${esc(s.id)}" value="${esc(o.id)}" ${e[s.id] === o.id ? 'checked' : ''}><span>${esc(o.texto || o.id)}${(o.refs || []).length ? ` <span class="meta">${o.refs.map(refHTML).join(', ')}</span>` : ''}</span></label>`).join('')}</fieldset>`).join('')}</div></details>` : ''}`;
  }
  function lineaTiempoHTML() {
    const C = N.crono(D);
    if (!C) return '<p class="vacio-txt">Los datos todavía no traen la cronología. Cuando lleguen, aquí verás la línea de tiempo; mientras, mira la tabla de edades.</p>';
    const comparar = estado.trad === 'ambas', e = eleg(), combo = N.combinacion(D, comparar ? 'TM' : tradSimple(), e);
    const L = N.lineaDeTiempo(D, combo);
    const secs = L.map(g => {
      let prev = null;
      const items = g.items.map(it => {
        const ev = it.evento, a = it.anio, c = comparar ? N.compararEvento(D, ev.id, e) : null;
        const salto = prev !== null && a !== null && a > prev ? `<li class="tl-salto" aria-hidden="true">+${anios(a - prev)}</li>` : '';
        if (a !== null) prev = a;
        const anio = c ? `<span class="tl-anio">TM ${anioTxt(c.TM)} · LXX ${anioTxt(c.LXX)}</span>${c.dif ? `<span class="tl-dif">diferencia ${c.dif > 0 ? '+' : ''}${c.dif}</span>` : ''}`
          : `<span class="tl-anio">${a === null ? 'Sin año en esta combinación' : 'Año ' + a}</span>`;
        return `${salto}<li class="tl-ev tipo-${esc(ev.tipo || 'evento')}${N.esDiluvio(ev) ? ' diluvio' : ''}${estado.focoEv === ev.id ? ' foco' : ''}" id="ev-${esc(ev.id)}">
          <button type="button" class="tl-btn" data-ev="${esc(ev.id)}"><span class="tl-ico">${icoEv(ev)}</span>
          <span class="tl-cuerpo">${anio}<span class="tl-tit">${esc(ev.titulo || ev.id)}</span><span class="tl-ref">${esc(TIPO_EV[ev.tipo] || 'Suceso')} · ${esc(ev.ref || '')}</span></span></button></li>`;
      }).join('');
      const hitos = g.hitos.length ? `<div class="tl-sin-tiempo"><h3>${ICO_EV.hito}Hechos de esta sección sin dato de tiempo <span class="meta">(en orden de lectura)</span></h3>
        <ul>${g.hitos.map(h => `<li><span class="tl-tit">${esc(h.hito.titulo)}</span> <span class="meta">${refHTML(h.hito.ref)}</span>${h.hito.nota ? `<span class="nota">${esc(h.hito.nota)}</span>` : ''}</li>`).join('')}</ul></div>` : '';
      return `<section class="tl-sec"><h2>${esc(g.titulo || 'Sucesos')}</h2>${items ? `<ol class="tl">${items}</ol>` : ''}${hitos}</section>`;
    }).join('');
    return `<p class="aviso-calculo"><strong>El texto bíblico no da fechas de calendario.</strong> Cada año es un ${insignia('calculo')}: ${esc(unidadTxt(C))}, encadenando edades del texto${comparar ? '; se ordena por el TM' : ''}. Pulsa un suceso para ver cómo se calcula.</p>
      <p class="leyenda-tl meta"><span>${ICO_EV.nacimiento}Nacimiento</span><span>${ICO_EV.muerte}Muerte</span><span>${ICO_EV.evento}Suceso</span><span>${ICO_EV.diluvio}Diluvio</span><span>${ICO_EV.hito}Sin dato de tiempo (fuera del eje)</span></p>
      ${secs || '<p class="vacio-txt">La cronología no trae sucesos.</p>'}`;
  }
  // Tarjeta de un suceso: año(s), cadena de pasos desde Adán (plegada), supuestos y quién vivía entonces.
  function abrirEvento(id) {
    const C = N.crono(D), ev = C && C.porId.get(id); if (!ev) return;
    const e = eleg(), comparar = estado.trad === 'ambas';
    const bloque = tr => {
      const combo = N.combinacion(D, tr, e), a = N.anioEvento(D, id, combo), cad = N.cadenaEvento(D, id, combo), dsp = N.despuesDe(D, id, combo), vivos = N.vivosEn(D, a, combo);
      return `<section class="bloque bloque-calc"><h3>${TRAD_TXT[tr]}</h3>
        <p class="cifra calc">${a === null ? 'Sin año en esta combinación' : 'Año ' + a}</p>
        <p>${insignia('calculo')}${dsp ? ` ${relTxt(dsp)}` : ''}</p>
        <details class="plegable"><summary>Cómo se calcula (${cad.length} ${cad.length === 1 ? 'paso' : 'pasos'} desde Adán)</summary>
          <ol class="cadena">${cad.map(b => `<li><strong>${esc(b.titulo)}</strong>${b.ref ? ' · ' + refHTML(b.ref) : ''}
            ${b.pasos.length ? `<ul>${b.pasos.map(p => `<li>${esc(p.texto || '')}${p.ref ? ' · ' + refHTML(p.ref) : ''}</li>`).join('')}</ul>` : ''}
            <span class="subtotal">= ${anioTxt(b.anio)}</span></li>`).join('')}</ol></details>
        <h4>Quién vivía entonces ${insignia('calculo')}</h4>
        ${vivos.length ? `<ul class="chips">${vivos.map(v => `<li>${btnPersona(v.persona)}<span class="meta"> ${anios(v.edad)}</span></li>`).join('')}</ul>` : '<p class="meta">Nadie con nacimiento y muerte calculables en ese año.</p>'}</section>`;
    };
    const c = comparar ? N.compararEvento(D, id, e) : null;
    const sup = C.supuestos.map(s => { const o = s.opciones.find(x => x.id === e[s.id]) || {}; return `<li>${esc(s.pregunta || s.id)}: <strong>${esc(o.texto || o.id)}</strong></li>`; }).join('');
    abrirDetalle(ev.titulo || id, `<p class="meta">${esc(TIPO_EV[ev.tipo] || 'Suceso')} · ${refHTML(ev.ref)}</p>
      ${(ev.personas || []).length ? `<ul class="chips">${ev.personas.map(p => `<li>${btnPersona(p)}</li>`).join('')}</ul>` : ''}
      ${c && c.dif !== null ? `<p class="difiere-txt">Entre TM y LXX hay ${anios(Math.abs(c.dif))} de diferencia.</p>` : ''}
      ${(comparar ? ['TM', 'LXX'] : [tradSimple()]).map(bloque).join('')}
      ${sup ? `<p class="meta">Supuestos usados (se cambian en Tiempo):</p><ul class="vinculos">${sup}</ul>` : ''}
      ${ev.nota ? `<p class="nota">${esc(ev.nota)}</p>` : ''}
      <p><a class="boton secundario" href="#tiempo/linea/${encodeURIComponent(id)}">Ver en la línea de tiempo</a></p>
      <p class="meta">El texto bíblico no da fechas de calendario: este año es un cálculo de la app a partir de las edades del texto.</p>`);
  }
  function vidasHTML() {
    const C = N.crono(D);
    return `<section class="vidas" aria-labelledby="vidas-t"><h2 id="vidas-t">Vidas solapadas ${insignia('calculo')}</h2>
      <p class="aviso-calculo"><strong>Esto es un CÁLCULO, no lo dice el texto.</strong> ${C
        ? `Nacimiento y muerte en ${esc(unidadTxt(C))}, según la cronología con la tradición y los supuestos elegidos. Pulsa una vida para ver cómo se calcula su nacimiento.`
        : 'Los “años desde Adán” se obtienen sumando las edades al engendrar de la línea Adán → Abraham en la tradición elegida. Supone que cada edad corresponde al hijo siguiente de la línea (p. ej. Gn 5:32 da 500 años a Noé para sus tres hijos), por lo que es una aproximación.'}</p>
      ${trads().map(C ? barrasCronoHTML : barrasHTML).join('')}</section>`;
  }
  function barrasCronoHTML(trad) {
    const C = N.crono(D), combo = comboDe(trad), m = N.vidasCrono(D, combo);
    const filas = [...m.values()].filter(x => x.nacimiento !== null).sort((a, b) => a.nacimiento - b.nacimiento);
    const omit = [...m.values()].filter(x => x.nacimiento === null);
    const aviso = omit.length ? `<p class="meta omitidas">Sin nacimiento calculable en esta combinación (se omiten): ${omit.map(x => esc(nombre(x.persona))).join(', ')}.</p>` : '';
    if (!filas.length) return `<h3>${TRAD_TXT[trad]}</h3><p>Sin datos suficientes.</p>${aviso}`;
    const max = Math.max(1, ...filas.map(f => f.muerte !== null ? f.muerte : f.nacimiento));
    const paso = max > 3000 ? 500 : max > 1200 ? 250 : 100;
    const marcas = []; for (let a = 0; a <= max; a += paso) marcas.push(a);
    const pct = x => (x / max * 100).toFixed(2) + '%';
    const evD = C.eventos.find(N.esDiluvio), dil = evD ? N.anioEvento(D, evD.id, combo) : null;
    const marcaDil = dil !== null && dil <= max ? `<span class="diluvio-marca" style="left:${pct(dil)}"></span>` : '';
    return `<h3>${TRAD_TXT[trad]}</h3>
      ${dil !== null ? `<p class="leyenda"><span class="muestra-diluvio" aria-hidden="true"></span> Diluvio ≈ año ${dil} desde Adán ${insignia('calculo')} (${refHTML(evD.ref)}).</p>` : ''}
      <ol class="barras">${filas.map(f => `<li><button type="button" class="barra-fila" data-ev="${esc(f.evNac)}">
        <span class="barra-nombre">${esc(nombre(f.persona))}</span><span class="barra-anos">${f.nacimiento}–${f.muerte !== null ? f.muerte : '?'}</span>
        <span class="pista" aria-hidden="true">${marcaDil}<span class="barra${f.muerte === null ? ' abierta' : ''}" style="left:${pct(f.nacimiento)};width:${f.muerte !== null ? pct(f.muerte - f.nacimiento) : '4px'}"></span></span></button></li>`).join('')}</ol>
      <div class="eje" aria-hidden="true">${marcas.map(a => `<span style="left:${pct(a)}">${a}</span>`).join('')}</div>${aviso}`;
  }
  function tablaHTML() {
    const ts = trads(), orden = N.ordenPatriarcas(D), ambas = ts.length === 2;
    const cab = ambas
      ? `<tr><th rowspan="2" scope="col">Persona</th>${N.TIPOS.map(t => `<th colspan="2" scope="colgroup">${TIPO_TXT[t]}</th>`).join('')}</tr><tr>${N.TIPOS.map(() => '<th scope="col">TM</th><th scope="col">LXX</th>').join('')}</tr>`
      : `<tr><th scope="col">Persona</th>${N.TIPOS.map(t => `<th scope="col">${TIPO_TXT[t]}</th>`).join('')}</tr>`;
    const filas = orden.map(id => { const dif = N.diferencias(D, id); return `<tr><th scope="row">${btnPersona(id)}${etiquetaTrad(id)}</th>${N.TIPOS.map(t => ts.map(tr => celda(id, t, tr, dif[t])).join('')).join('')}</tr>`; }).join('');
    return `<h2>Edades de los patriarcas</h2>
      <p class="leyenda"><span class="muestra difiere"></span> TM y LXX difieren (o solo una da el dato) · <span class="marca-calc">*</span> cálculo (no está escrito; se deduce) · pulsa una cifra para ver versículo, cita y fuente.</p>
      ${orden.length ? `<div class="tabla-envoltura" tabindex="0" role="region" aria-label="Tabla de edades"><table class="edades"><thead>${cab}</thead><tbody>${filas}</tbody></table></div>` : '<p>No hay edades de patriarcas en los datos.</p>'}
      ${eventosHTML()}`;
  }
  function eventosHTML() {
    const gs = N.edadesEnEventoPorPersona(D);
    return `<section class="eventos" aria-labelledby="ev-t"><h2 id="ev-t">Edades en momentos del relato</h2>
      ${gs.length ? `<p class="meta">Edad que el texto da a una persona en un momento concreto, en orden de versículo. Si la Septuaginta da otra cifra, se indica.</p>
        <ul class="eventos-lista">${gs.map(g => `<li><h3>${btnPersona(g.persona)}</h3><ul class="edades-acomp">${g.items.map(eventoHTML).join('')}</ul></li>`).join('')}</ul>`
        : '<p class="vacio-txt">Los datos todavía no traen edades en momentos del relato.</p>'}</section>`;
  }
  function barrasHTML(trad) {
    const { filas, omitidas } = N.vidas(D, trad);
    const aviso = omitidas.length ? `<p class="meta omitidas">Se ${omitidas.length === 1 ? 'omite' : 'omiten'} ${omitidas.length} ${omitidas.length === 1 ? 'persona' : 'personas'} con edades pero sin la cadena completa desde Adán, así que no se pueden situar: ${omitidas.map(id => esc(nombre(id))).join(', ')}.</p>` : '';
    if (!filas.length) return `<p>Sin datos suficientes para ${trad}.</p>${aviso}`;
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
      <div class="eje" aria-hidden="true">${marcas.map(a => `<span style="left:${pct(a)}">${a}</span>`).join('')}</div>${aviso}`;
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
      ${fuentesOriginalesHTML()}
      ${(C => C ? `<section><h2>Tiempo y cronología</h2>
        <p>El texto bíblico no da fechas de calendario. La app sitúa los sucesos en <strong>${esc(unidadTxt(C))}</strong>, encadenando edades que el texto sí da (por ejemplo, la edad de cada padre al engendrar). Por eso <strong>todo año es ${insignia('calculo')}</strong>: no está escrito así en el texto, y cada suceso muestra la cadena de pasos y sus versículos.</p>
        <p>No se dan fechas antes de Cristo: convertir estos años exigiría supuestos ajenos al texto. El TM y la LXX dan edades distintas, así que los años cambian según la tradición.</p>
        ${C.supuestos.length ? `<h3>Supuestos</h3><p>Donde el texto admite más de una lectura, puedes elegir en Tiempo; la elección se guarda en este dispositivo.</p><dl class="etiquetas">${C.supuestos.map(s => `<dt>${esc(s.pregunta || s.id)}</dt><dd><ul>${s.opciones.map(o => `<li>${esc(o.texto || o.id)}${o.id === s.defecto ? ' <span class="etiqueta">por defecto</span>' : ''}${(o.refs || []).length ? ' · ' + o.refs.map(refHTML).join(', ') : ''}${o.nota ? `<br><span class="meta">${esc(o.nota)}</span>` : ''}</li>`).join('')}</ul></dd>`).join('')}</dl>` : ''}
        <p>Los sucesos sin dato de tiempo en el texto (como ${C.hitos.length ? '«' + esc(C.hitos[0].titulo) + '»' : 'la torre de Babel'}) se muestran en orden de lectura, sin año.</p></section>` : '')(N.crono(D))}
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
      ${creditosHTML()}
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
    const evs = N.edadesEnEvento(D).filter(x => x.persona === id);
    const edades = (tieneEdades ? `<table class="edades mini"><thead><tr><th scope="col"></th><th scope="col">TM</th><th scope="col">LXX</th></tr></thead><tbody>${N.TIPOS.map(t => `<tr><th scope="row">${TIPO_TXT[t]}</th>${N.TRADS.map(tr => celda(id, t, tr, dif[t])).join('')}</tr>`).join('')}</tbody></table>` : '')
      + (evs.length ? `<ul class="edades-acomp">${evs.map(eventoHTML).join('')}</ul>` : '') || '<p class="meta">Sin edades registradas.</p>';
    // En el tiempo: nacimiento y muerte en años desde Adán (cálculo) con la combinación elegida en Tiempo.
    let tiempo = '', curios = '';
    if (N.crono(D)) {
      const tr = tradSimple(), combo = comboDe(tr), x = N.vidasCrono(D, combo).get(id);
      const cs = N.curiosidadesDe(D, id, combo);
      const liC = c => `<li class="curio"><p>${esc(c.texto)}.</p><details class="plegable"><summary>Pasos y versículos</summary>${pasosCurio(c)}</details></li>`;
      if (cs.length) curios = `<h3>Curiosidades ${insignia('calculo')}</h3><ul class="curios">${cs.slice(0, 3).map(liC).join('')}</ul>
        ${cs.length > 3 ? `<details class="plegable"><summary>Ver ${cs.length - 3} más</summary><ul class="curios">${cs.slice(3).map(liC).join('')}</ul></details>` : ''}
        <p class="meta">Calculadas por esta app con ${esc(TRAD_TXT[tr])} y los supuestos elegidos en Tiempo; los años son «años desde la creación de Adán».</p>`;
      if (x && (x.nacimiento !== null || x.muerte !== null)) {
        const cel = (a, ev) => a === null ? '<span class="meta">sin dato</span>' : `<button type="button" class="celda-acomp" data-ev="${esc(ev)}"><strong>${a}</strong></button>`;
        const cont = N.contemporaneos(D, id, combo, 8);
        tiempo = `<h3>En el tiempo ${insignia('calculo')}</h3>
          <div class="par"><span>Nace<br>${cel(x.nacimiento, x.evNac)}</span><span>Muere<br>${cel(x.muerte, x.evMuerte)}</span></div>
          <p class="meta">Años desde la creación de Adán (${tr}, con los supuestos elegidos en Tiempo). Pulsa una cifra para ver el cálculo.</p>
          ${cont.length ? `<p class="meta">Contemporáneos destacados:</p><ul class="chips">${cont.map(c => `<li>${btnPersona(c.persona)}</li>`).join('')}</ul>` : ''}`;
      }
    }
    const refs = [...new Set([].concat(p.primera_ref ? [p.primera_ref] : [], p.refs || []))];
    // Grafía de la RV1909 si difiere del nombre mostrado.
    const formas = [...new Set([].concat(p.formas_rv1909 || [], p.nombre_rv1909 || []).filter(Boolean))];
    const grafia = formas.some(f => N.norm(f) !== N.norm(p.nombre)) ? formas.join(', ') : '';
    const notaGrafia = grafia && /^En la Reina-Valera 1909:/.test(p.nota || '');
    const k1 = N.indice(D).primera.get(id), primera = k1 ? N.refDeClave(k1) : p.primera_ref;
    const enCol = !p.sin_nombre && N.coleccion(D, [...pasajesLeidos()]).has(id), rz = N.rareza(D, id);
    const pas = N.pasajesDePersona(D, id);
    const pasLi = x => `<li><a href="#leer/p/${esc(x.pasaje.id)}"><span class="pp-rango">${rango(x.pasaje)}</span><span class="pp-titulo">${esc(x.pasaje.titulo)}</span></a><span class="meta">${x.versiculos} ${x.versiculos === 1 ? 'versículo' : 'versículos'}</span></li>`;
    const lugs = N.lugaresDePersona(D, id, 10), ext = N.enlacesExternos(D, id);
    fichaDlg.querySelector('h2').textContent = p.nombre || id;
    fichaDlg.querySelector('.dialogo-cuerpo').innerHTML = `
      <div class="ficha-cab">${retratoHTML(p)}<div class="ficha-datos">
        ${p.rol ? `<p class="rol">${esc(p.rol)}</p>` : ''}
        ${grafia ? `<p class="grafia">En la Reina-Valera 1909: <strong>${esc(grafia)}</strong></p>` : ''}
        <p class="meta">${p.sexo === 'm' ? 'Varón' : p.sexo === 'f' ? 'Mujer' : 'Sexo no indicado'}${primera ? ' · primera aparición: ' + refHTML(primera) : ''} ${etiquetaTrad(id)}</p>
        ${p.sin_nombre ? '' : `<p class="ficha-estado${enCol ? ' en-col' : ''}">${enCol ? 'En tu colección' : 'Aún no está en tu colección'} · <span class="rareza-muestra r-${rz.id}">${esc(rz.nombre)}</span> <span class="meta">${rz.versiculos} ${rz.versiculos === 1 ? 'versículo' : 'versículos'}</span></p>`}
      </div></div>
      <p class="acciones-ficha">${(r => r ? `<a class="boton" href="${hrefRef(N.parseRef(r))}">Leer donde aparece</a>` : '')([primera, p.primera_ref, p.ref_mencion].concat(p.refs || []).find(x => N.clave(x)))}
        ${N.enPantallaArbol(D, id) ? `<a class="boton secundario" href="#arbol/${encodeURIComponent(id)}">Ver en el árbol</a>` : ''}</p>
      <h3>Padres</h3>${lista(padres, 'No constan.')}
      ${cony.length ? '<h3>Cónyuges</h3>' + lista(cony, '') : ''}
      <h3>Hijos</h3>${lista(hijos, 'No constan.')}
      <h3>Edades</h3>${edades}${tiempo}${curios}
      ${pas.length ? `<h3>Pasajes donde aparece (${pas.length})</h3><ul class="pasajes-persona">${pas.slice(0, 5).map(pasLi).join('')}</ul>
        ${pas.length > 5 ? `<details class="plegable"><summary>Ver los otros ${pas.length - 5}</summary><ul class="pasajes-persona">${pas.slice(5).map(pasLi).join('')}</ul></details>` : ''}` : ''}
      ${lugs.length ? `<h3>Lugares</h3><p class="meta">Nombrados en los mismos versículos que ${esc(p.nombre || id)}: coincidencia en el texto, no un vínculo afirmado.</p><ul class="chips">${lugs.map(x => `<li>${btnLugar(x.lugar)}</li>`).join('')}</ul>` : ''}
      ${p.nota && !notaGrafia ? `<h3>Notas</h3><p class="nota">${esc(p.nota)}</p>` : ''}
      ${refs.length ? `<details class="plegable"><summary>Versículos de los datos (${refs.length})</summary><ul class="refs">${refs.map(r => `<li>${refHTML(r)}</li>`).join('')}</ul></details>` : ''}
      ${ext.length ? `<h3>Profundizar</h3><p class="meta">Enlaces a sitios ajenos a esta app (se abren aparte); su contenido no se copia aquí.</p>
        <ul class="externos">${ext.map(x => `<li><a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">${esc(x.titulo)}</a> <span class="etiqueta externa">Fuente externa</span><span class="meta">${esc(x.detalle)}</span></li>`).join('')}</ul>` : ''}`;
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
    const conf = ubicados.map(l => N.confianzaLugar(l)), prio = ubicados.map(l => N.prioridadLugar(l));
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
      // Solo lo que cae en pantalla; etiquetas por importancia, más cuanto más se acerca.
      const items = [];
      ubicados.forEach((l, i) => {
        const [x, y] = aPant(...coord(l));
        if (x < -20 || y < -20 || x > W + 20 || y > H + 20) return;
        items.push({ id: l.id, x, y, c: conf[i], texto: l.nombre || l.id, prioridad: (l.id === sel ? 1e4 : 0) + prio[i] });
      });
      items.forEach(it => { html += `<g class="marcador conf-${it.c}${it.id === sel ? ' sel' : ''}" transform="translate(${it.x.toFixed(1)} ${it.y.toFixed(1)})" data-lugar-mapa="${esc(it.id)}" tabindex="0" role="button" aria-label="${esc(it.texto)}, ${CONF_TXT[it.c].toLowerCase()}"><circle r="16" class="toque"/>${formaConf(it.c, it.id === sel ? 8 : 6)}</g>`; });
      N.colocarEtiquetas(items, W, H, cfg.mini ? Infinity : N.etiquetasPorZoom(v.s / (v.s0 || v.s), items.length)).forEach(e => { html += `<text class="etq${e.id === sel ? ' sel' : ''}" x="${e.x.toFixed(1)}" y="${e.y.toFixed(1)}" text-anchor="${e.anc}">${esc(e.texto)}</text>`; });
      capa.innerHTML = html;
    }
    function encuadrar() {
      const pts = ubicados.map(coord);
      const lsel = sel && N.lugar(D, sel);
      if (lsel) (lsel.alternativas || []).forEach(a => { if (Number.isFinite(+a.lat) && Number.isFinite(+a.lon)) pts.push([+a.lon, +a.lat]); });
      const r = N.encuadre(P, pts, { minimo: cfg.mini ? 4 : 3 });
      v.s = Math.min(W / r.w, H / r.h); v.cx = r.x + r.w / 2; v.cy = r.y + r.h / 2; v.s0 = v.s;
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
    if (f.startsWith('cap-')) {
      const [lb, cs] = f.slice(4).split('-'), cap = +cs, c = caps.find(x => x.cap === cap && N.libroIdDe(D, x.libro) === lb);
      ids = c ? N.lugaresDeRefs(D, (c.versiculos || []).map(v => `${lb} ${cap}:${v.n}`)) : [];
    }
    else if (f.startsWith('p-')) ids = N.lugaresDePasaje(D, ps.find(p => p.id === f.slice(2)));
    const ubic = ids.filter(id => { const c = N.confianzaLugar(N.lugar(D, id)); return c !== 'desconocida' && estado.mapaConf.has(c); });
    const desc = ids.filter(id => N.confianzaLugar(N.lugar(D, id)) === 'desconocida');
    const opt = (v, t) => `<option value="${esc(v)}"${f === v ? ' selected' : ''}>${esc(t)}</option>`;
    return `<h1 tabindex="-1">Mapa de los lugares</h1>
      <p class="sub">El nombre de cada lugar es texto bíblico; su ubicación es una identificación moderna con un grado de confianza. Lo que no se puede ubicar no se dibuja.</p>
      <div class="herr mapa-filtros">
        <div class="campo"><label for="f-ambito">Pasaje o capítulo</label><select id="f-ambito">${opt('', 'Todo ' + N.alcance(D).texto)}
          ${(D.pasajes || []).length ? N.seccionesPlan(D, [], null).map(g => `<optgroup label="${esc(g.titulo ? 'Pasajes · ' + g.titulo : 'Pasajes')}">${g.pasajes.map(x => opt('p-' + x.pasaje.id, x.pasaje.titulo)).join('')}</optgroup>`).join('') : ''}
          ${N.libros(D).map(l => { const cs = caps.filter(c => N.libroIdDe(D, c.libro) === l.id).sort((a, b) => a.cap - b.cap); return cs.length ? `<optgroup label="Capítulos · ${esc(l.nombre)}">${cs.map(c => opt(`cap-${l.id}-${c.cap}`, `${l.nombre} ${c.cap}`)).join('')}</optgroup>` : ''; }).join('')}</select></div>
        <div class="campo"><label for="buscar-lugar">Buscar lugar</label><input id="buscar-lugar" type="search" autocomplete="off" placeholder="Nombre…" value="${esc(estado.mapaQ)}"></div>
        <fieldset class="conf-filtro"><legend>Confianza</legend>${['alta', 'media', 'baja'].map(c => `<label><input type="checkbox" data-conf="${c}" ${estado.mapaConf.has(c) ? 'checked' : ''}><span>${icoConf(c)}${c[0].toUpperCase() + c.slice(1)}</span></label>`).join('')}</fieldset>
      </div>
      <ul class="resultados" id="res-lugar" aria-live="polite">${resultadosLugar()}</ul>
      ${todos.length ? mapaHTML(ubic, { sel: ubic.includes(estado.mapaSel) ? estado.mapaSel : null }) : '<p class="vacio-txt">Los datos todavía no traen lugares. Cuando se publiquen, aparecerán aquí.</p>'}
      ${todos.length ? `<h2>En el mapa (${ubic.length})</h2>${ubic.length ? `<ul class="chips">${ubic.map(id => `<li>${btnLugar(id)}</li>`).join('')}</ul>` : '<p class="vacio-txt">Ningún lugar ubicado con este filtro.</p>'}
      <h2>Sin ubicación conocida (${desc.length})</h2>${desc.length ? `<ul class="lugares-lista">${desc.map(id => { const l = N.lugar(D, id); return `<li>${btnLugar(id)}<span class="contexto">Ubicación desconocida${l.nota ? ': ' + esc(l.nota) : ''}</span></li>`; }).join('')}</ul>` : '<p class="vacio-txt">Todos los lugares de este filtro tienen ubicación.</p>'}` : ''}
      ${mapasAntiguosHTML()}`;
  }
  function resultadosLugar() {
    const q = N.norm(estado.mapaQ);
    if (!q) return '';
    const r = (D.lugares || []).filter(l => N.norm(l.nombre).includes(q) || N.norm(l.nombre_rv1909).includes(q)).slice(0, 20);
    return r.length ? r.map(l => `<li>${btnLugar(l.id)}</li>`).join('') : '<li class="meta">Sin resultados.</li>';
  }

  /* ---------- Personajes: colección, ficha y curiosidades ---------- */
  const SILUETA = '<svg class="silueta" viewBox="0 0 40 48" aria-hidden="true"><circle cx="20" cy="15" r="8.5"/><path d="M4 47c0-10.5 7-18 16-18s16 7.5 16 18z"/></svg>';
  const inicial = id => Array.from(String(nombre(id)))[0] || '?';
  // Hueco para el retrato: si algún día lo hay, siempre rotulado (Arte con autor y fecha, o Ilustración moderna).
  function retratoHTML(p) {
    const r = p && p.retrato;
    if (r && r.url && (r.tipo === 'arte' || r.tipo === 'ilustracion'))
      return `<figure class="retrato"><img src="${esc(r.url)}" alt="${esc(r.alt || 'Retrato de ' + (p.nombre || ''))}" loading="lazy">
        <figcaption><span class="etiqueta img-${r.tipo}">${r.tipo === 'arte' ? 'Arte' : 'Ilustración moderna'}</span> ${esc([r.autor, r.fecha].filter(Boolean).join(', '))}</figcaption></figure>`;
    return `<figure class="retrato vacio" title="Si se añade un retrato, irá rotulado como Arte (artista y fecha) o Ilustración moderna">${SILUETA}<figcaption>Sin retrato</figcaption></figure>`;
  }
  const pasosCurio = c => `<ol class="pasos-curio">${c.pasos.map(s => `<li>${esc(s.texto)}${s.ref ? ` · ${refHTML(s.ref)}` : ''}</li>`).join('')}</ol>`;
  function detalleCurio(id) {
    const tr = tradSimple(), c = N.curiosidades(D, comboDe(tr)).find(x => x.id === id); if (!c) return;
    abrirDetalle('¿Sabías que…?', `<p>${insignia('calculo')}</p><p class="curio-txt">${esc(c.texto)}.</p><h3>Pasos</h3>${pasosCurio(c)}
      <p class="meta">Cálculo de esta app con ${esc(TRAD_TXT[tr])} y los supuestos elegidos en Tiempo (años desde la creación de Adán). No es texto bíblico.</p>
      <ul class="chips">${c.protagonistas.map(x => `<li>${btnPersona(x)}</li>`).join('')}</ul>`);
  }
  const rangoRareza = r => r.max === Infinity ? `${r.min} o más versículos` : r.min === r.max ? `${r.min} versículo` : `${r.min}–${r.max} versículos`;
  function fichaColHTML(f) {
    if (!f.desbloqueada) return `<li class="ficha-col bloqueada"><span class="ficha-retrato">${SILUETA}</span><span class="ficha-nombre"><span aria-hidden="true">Sin descubrir</span><span class="sr">Personaje sin descubrir,</span></span><span class="ficha-pie">Aparece en ${esc(f.primeraCap).replace(' ', '&nbsp;')}</span></li>`;
    return `<li><button type="button" class="ficha-col r-${f.rareza.id}${f.sexo === 'f' ? ' mujer' : ''}" data-persona="${esc(f.id)}">
      <span class="ficha-retrato"><span class="ficha-inicial" aria-hidden="true">${esc(inicial(f.id))}</span></span>
      <span class="ficha-nombre">${esc(nombre(f.id))}</span><span class="rareza-muestra r-${f.rareza.id}">${esc(f.rareza.nombre)}</span>
      <span class="ficha-pie">${esc(f.primera)}</span></button></li>`;
  }
  function vistaPersonajes() {
    const F = N.fichasColeccion(D, [...pasajesLeidos()]), obt = F.filter(f => f.desbloqueada).length;
    const LB = N.libros(D).filter(l => F.some(f => f.libros.includes(l.id)));
    const lib = LB.some(l => l.id === estado.colLibro) ? estado.colLibro : '';
    const sx = estado.colSexo === 'f' || estado.colSexo === 'm' ? estado.colSexo : '';
    const enLibro = F.filter(f => !lib || f.libros.includes(lib)), obtL = enLibro.filter(f => f.desbloqueada).length;
    const vis = enLibro.filter(f => !sx || (f.desbloqueada && f.sexo === sx));
    const sinDesc = sx ? enLibro.filter(f => !f.desbloqueada).length : 0;
    const seg = (leyenda, name, actual, ops) => `<fieldset class="segmentos"><legend>${leyenda}</legend>${ops.map(([v, t]) => `<label><input type="radio" name="${name}" value="${esc(v)}" ${actual === v ? 'checked' : ''}><span>${esc(t)}</span></label>`).join('')}</fieldset>`;
    const nomLib = lib ? (LB.find(l => l.id === lib) || {}).nombre : '';
    return `<h1 tabindex="-1">Personajes</h1>
      <p class="sub">Cada persona con nombre entra en tu colección cuando marcas como leído un pasaje donde aparece. Ábrela para ver su ficha.</p>
      <div class="colec-resumen"><p class="colec-cuenta"><strong>${obt}</strong> de ${F.length}</p>
        <progress max="${F.length || 1}" value="${obt}" aria-label="Personajes obtenidos"></progress>
        ${lib ? `<p class="meta">En ${esc(nomLib)}: ${obtL} de ${enLibro.length}</p>` : ''}</div>
      <div class="colec-filtros">${LB.length > 1 ? seg('Libro', 'col-libro', lib, [['', 'Todos']].concat(LB.map(l => [l.id, l.nombre]))) : ''}
        ${seg('Mostrar', 'col-sexo', sx, [['', 'Todos'], ['f', 'Mujeres'], ['m', 'Hombres']])}</div>
      <details class="plegable"><summary>Qué significa la rareza</summary>
        <p class="meta">Sale solo de los datos: en cuántos versículos de ${esc(N.alcance(D).texto)} aparece la persona. No mide su importancia.</p>
        <ul class="rarezas">${N.RAREZAS.map(r => `<li><span class="rareza-muestra r-${r.id}">${esc(r.nombre)}</span> ${rangoRareza(r)} <span class="meta">· ${F.filter(f => f.rareza.id === r.id).length} personas</span></li>`).join('')}</ul></details>
      ${obt ? '' : `<p class="colec-vacia">Todavía no tienes fichas. <a href="#leer">Empieza a leer</a> y marca un pasaje como leído.</p>`}
      ${sx && sinDesc ? `<p class="meta">Las ${sinDesc} fichas sin descubrir no se filtran por mujeres u hombres, para no adelantar nada.</p>` : ''}
      ${vis.length ? `<ul class="fichas-col">${vis.map(fichaColHTML).join('')}</ul>` : '<p class="vacio-txt">Aún no tienes fichas con este filtro.</p>'}`;
  }
  // Aviso «Nuevo en tu colección» tras marcar un pasaje como leído. Muchas fichas: se resumen.
  let tNuevas = 0;
  const ocultarNuevas = () => { clearTimeout(tNuevas); const el = $('#nuevas'); if (el) { el.hidden = true; el.classList.remove('entra'); } };
  const programarNuevas = () => { clearTimeout(tNuevas); tNuevas = setTimeout(ocultarNuevas, 9000); };
  function mostrarNuevas(ids) {
    const el = $('#nuevas'); if (!el || !ids.length) return;
    const total = N.coleccionables(D).length, obt = N.coleccion(D, [...pasajesLeidos()]).size;
    const vis = ids.length > 4 ? ids.slice(0, 3) : ids, resto = ids.length - vis.length;
    el.innerHTML = `<div class="nuevas-cab"><p class="nuevas-titulo">Nuevo en tu colección<span class="nuevas-cuenta">${ids.length === 1 ? '1 personaje' : ids.length + ' personajes'} · llevas ${obt} de ${total}</span></p>
        <button type="button" class="cerrar" data-cerrar-nuevas aria-label="Cerrar aviso"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 5l10 10M15 5L5 15"/></svg></button></div>
      <ul class="nuevas-fichas">${vis.map((id, i) => { const r = N.rareza(D, id); return `<li style="--i:${i}"><button type="button" class="nueva-ficha r-${r.id}" data-persona="${esc(id)}"><span class="ficha-inicial" aria-hidden="true">${esc(inicial(id))}</span><span class="nueva-nombre">${esc(nombre(id))}</span><span class="rareza-muestra r-${r.id}">${esc(r.nombre)}</span></button></li>`; }).join('')}
        ${resto ? `<li class="nuevas-resto" style="--i:${vis.length}">y ${resto} más</li>` : ''}</ul>
      <a class="nuevas-ver" href="#personajes" data-cerrar-nuevas>Ver la colección</a>`;
    el.hidden = false; el.classList.remove('entra'); void el.offsetWidth; el.classList.add('entra');
    programarNuevas();
  }
  // Mientras se mira o se recorre con el teclado, el aviso no se cierra solo.
  (el => { if (!el) return;
    el.addEventListener('pointerenter', () => clearTimeout(tNuevas)); el.addEventListener('pointerleave', () => { if (!el.hidden) programarNuevas(); });
    el.addEventListener('focusin', () => clearTimeout(tNuevas)); el.addEventListener('focusout', e => { if (!el.hidden && !el.contains(e.relatedTarget)) programarNuevas(); });
  })($('#nuevas'));

  /* ---------- Navegación ---------- */
  function ruta() { const h = decodeURIComponent(location.hash.slice(1)) || 'leer'; const [vista, ...args] = h.split('/'); return { vista, args }; }
  const VISTAS = { leer: vistaLeer, personajes: vistaPersonajes, arbol: vistaArbol, tiempo: vistaTiempo, edades: () => vistaTiempo(['tabla']), mapa: vistaMapa, fuentes: vistaFuentes };
  const PESTANA = { edades: 'tiempo' }; // rutas antiguas
  let primera = true;
  function render(foco) {
    if (!D) { main.innerHTML = '<h1>Sin datos</h1><p>No se encontró <code>datos/biblia.js</code>. Añade <code>?ejemplo</code> a la dirección para ver los datos de prueba.</p>'; return; }
    const { vista, args } = ruta();
    const fn = VISTAS[vista] || vistaLeer;
    main.innerHTML = fn(args);
    trasPintar(vista);
    montarMapas(main);
    conectoresTodos();
    document.querySelectorAll('.nav-principal a').forEach(a => { if (a.dataset.vista === (VISTAS[vista] ? PESTANA[vista] || vista : 'leer')) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); });
    document.title = (main.querySelector('h1') || {}).textContent + ' · Biblia';
    const marcado = main.querySelector('.vers.activo, .fila.foco, .ga-fam.foco, .foco-sp, .tl-ev.foco');
    if (marcado && foco !== false) { marcado.scrollIntoView({ block: 'center', inline: 'center' }); }
    else {
      if (foco !== false || primera) centrarLienzos();
      if (foco !== false && !primera) window.scrollTo(0, 0);
    }
    if (foco !== false && !primera) { const h = main.querySelector('h1'); if (h) h.focus({ preventScroll: true }); }
    primera = false;
  }
  // Carga bajo demanda lo que pide la vista recién pintada (Fuentes, o la comparación si quedó elegida).
  function trasPintar(vista) {
    if (vista === 'fuentes') { if (ORIG.est.o === '') cargarOriginales('o'); if (ORIG.est.g === '') cargarOriginales('g'); }
    const cmp = main.querySelector('.comparar');
    if (cmp) {
      const c = columnas();
      if (c.includes('he') && ORIG.est.o === '') cargarOriginales('o');
      if (c.includes('gr') && ORIG.est.g === '') cargarOriginales('g');
    }
    if (ORIG.est.o === 'ok' && (cmp || main.querySelector('.lv-orig[lang="he"]'))) pedirFuenteHebrea();
  }
  function rerender(selectorFoco) { const y = window.scrollY; render(false); window.scrollTo(0, y); if (selectorFoco) { const el = main.querySelector(selectorFoco); if (el) el.focus(); } }

  if (window.matchMedia) { const mq = window.matchMedia('(max-width: 699px)'); if (mq.addEventListener) mq.addEventListener('change', () => { if (main.querySelector('.comparar')) rerender(); }); }
  window.addEventListener('hashchange', () => { parar(); cerrar(detDlg); cerrar(fichaDlg); if (visorDlg) cerrar(visorDlg); estado.focoHash = undefined; render(); });
  // Secciones del plan: se recuerda en la sesión cuáles abrió o cerró la persona.
  document.addEventListener('toggle', e => {
    const s = e.target; if (!s || !s.dataset) return;
    if (s.dataset.sec) estado.secAbiertas.set(s.dataset.sec, s.open);
    if (s.id === 'sin-parentesco') estado.sinParAbierta = s.open;
    if (s.id === 'supuestos') estado.supAbiertos = s.open;
  }, true);
  document.addEventListener('keydown', e => {
    if (e.target && e.target.id === 'buscar' && e.key === 'Enter') { const r = N.buscar(D, estado.q, 1)[0]; if (r) { e.preventDefault(); irArbol(r.id); } }
  });

  document.addEventListener('click', e => {
    const t = e.target;
    if (t instanceof HTMLDialogElement && t.open) { cerrar(t); return; }
    const cn = t.closest('[data-cerrar-nuevas]'); if (cn) { ocultarNuevas(); if (cn.tagName !== 'A') return; }
    const c = t.closest('[data-cerrar]'); if (c) { cerrar(c.closest('dialog')); return; }
    const vi = t.closest('[data-visor]'); if (vi) { abrirVisor(vi.dataset.visor); return; }
    const vz = t.closest('[data-vzoom]'); if (vz) { zoomVisor(+vz.dataset.vzoom); return; }
    const rpa = t.closest('[data-rec-paso]'); if (rpa) { pasoImagen(+rpa.dataset.recPaso); return; }
    const rv = t.closest('[data-rec-video]'); if (rv) { const f = recPorId(rv.dataset.recVideo); if (f && N.esIdYoutube(f.youtube)) { estado.recVideo = f.id; rv.outerHTML = iframeVideo({ youtube_id: f.youtube, titulo: f.titulo }); } return; }
    const va = t.closest('[data-variante]'); if (va) { abrirVariante(va.dataset.variante); return; }
    if (t.closest('[data-escuchar]')) {
      estado.escuchar = !estado.escuchar; if (!estado.escuchar) parar();
      const b = main.querySelector('[data-escuchar]'), r = $('#reproductor');
      if (b) { b.setAttribute('aria-expanded', estado.escuchar); if (r) r.remove(); if (estado.escuchar) b.closest('.herr-pasaje').insertAdjacentHTML('afterend', reproductorHTML()); }
      return;
    }
    const rp = t.closest('[data-rep]'); if (rp) {
      const a = rp.dataset.rep;
      if (a === 'pasaje') escucharEn(habla.idioma, versosPasaje(), '[data-rep]');
      else if (a === 'verso' && estado.activo) escucharEn(habla.idioma, [estado.activo], '[data-rep]');
      else if (a === 'pausa') pausar();
      else if (a === 'parar') parar();
      return;
    }
    const hb = t.closest('[data-hablar]'); if (hb) { const [id, k] = hb.dataset.hablar.split('|'); habla.idioma = id; if (habla.k === k && habla.estado !== 'parado') parar(); else escucharEn(id, [k]); return; }
    if (t.closest('[data-cargar-origen]')) { cargarOriginales('o'); return; }
    const rt = t.closest('[data-reintentar]'); if (rt) { cargarOriginales(rt.dataset.reintentar); return; }
    const vc = t.closest('[data-video-cargar]'); if (vc) { estado.videoPedido = vc.dataset.videoCargar; cargarOriginales('o'); return; }
    const vd = t.closest('[data-video]'); if (vd) { const v = ORIG.o && N.videosDeLibro(ORIG.o, estado.libro).find(x => x.youtube_id === vd.dataset.video); if (v) { estado.videoPedido = estado.libro; vd.outerHTML = iframeVideo(v); } return; }
    const cu = t.closest('[data-curio]'); if (cu) { detalleCurio(cu.dataset.curio); return; }
    const ia = t.closest('[data-ir-arbol]'); if (ia) { irArbol(ia.dataset.irArbol); return; }
    const lg = t.closest('[data-lugar]'); if (lg) { e.preventDefault(); cerrar(detDlg); abrirLugar(lg.dataset.lugar); return; }
    const p = t.closest('[data-persona]'); if (p) { e.preventDefault(); if (p.closest('#nuevas')) ocultarNuevas(); cerrar(detDlg); abrirFicha(p.dataset.persona); return; }
    const ed = t.closest('[data-edad]'); if (ed) { const [id, tipo, trad] = ed.dataset.edad.split('|'); detalleEdad(id, tipo, trad); return; }
    const evb = t.closest('[data-ev]'); if (evb) { abrirEvento(evb.dataset.ev); return; }
    const ca = t.closest('[data-calc]'); if (ca) { const [trad, id] = ca.dataset.calc.split('|'); detalleCalc(trad, id); return; }
    const pl = t.closest('[data-plegar]'); if (pl) { alternarRama(pl.dataset.plegar); return; }
    const gp = t.closest('[data-ga-plegar]'); if (gp) { alternarGA(gp.dataset.gaPlegar); return; }
    const zm = t.closest('[data-zoom]'); if (zm) { zoomGA(+zm.dataset.zoom); return; }
    const at = t.closest('[data-atajo]'); if (at) { estado.lineaSolo = estado.lineaSolo === at.dataset.atajo ? false : at.dataset.atajo; estado.aviso = ''; rerender(`[data-atajo="${CSS.escape(at.dataset.atajo)}"]`); centrarLienzos(); return; }
    const ac = t.closest('[data-activar]'); if (ac) { activar(ac.dataset.activar); return; }
    if (t.closest('[data-hoja]')) { estado.hoja = !estado.hoja; const a = $('#acompanante'); if (a) { a.classList.toggle('abierta', estado.hoja); a.querySelector('[data-hoja]').setAttribute('aria-expanded', estado.hoja); } return; }
    const ls = t.closest('[data-leido-seguir]'); if (ls) {
      const L = pasajesLeidos(), pid = ls.dataset.leidoSeguir, nuevas = L.has(pid) ? [] : N.nuevasAlLeer(D, [...L], pid);
      L.add(pid); store.set('biblia.pasajesLeidos', [...L]);
      const ps = N.pasajes(D), i = ps.findIndex(x => x.id === pid); location.hash = ps[i + 1] ? `#leer/p/${ps[i + 1].id}` : '#leer';
      if (nuevas.length) mostrarNuevas(nuevas);
      return;
    }
    const ve = t.closest('.vers'); if (ve && !t.closest('button, a')) { activar(ve.dataset.v); return; }
    if (t.closest('#btn-mujeres')) { estado.mujeres = !estado.mujeres; rerender('#btn-mujeres'); return; }
    if (t.closest('#btn-todo')) { estado.lineaSolo = false; rerender('[data-atajo]'); centrarLienzos(); return; }
    if (t.closest('#btn-plegar')) { estado.abiertos = new Set(); rerender('#btn-plegar'); return; }
    if (t.closest('#btn-desplegar')) { estado.abiertos = new Set([...N.mapaArbol(D).nodos.values()].filter(x => x.n.hijos.length).map(x => x.n.id)); rerender('#btn-desplegar'); return; }
  });
  document.addEventListener('change', e => {
    const t = e.target;
    if (t.id === 'f-ambito') { estado.mapaFiltro = t.value; rerender('#f-ambito'); }
    else if (t.dataset && t.dataset.conf) { t.checked ? estado.mapaConf.add(t.dataset.conf) : estado.mapaConf.delete(t.dataset.conf); rerender(`[data-conf="${t.dataset.conf}"]`); }
    else if (t.dataset && t.dataset.sup) { const g = store.get('biblia.supuestos', {}); g[t.dataset.sup] = t.value; store.set('biblia.supuestos', g); rerender(`input[data-sup="${CSS.escape(t.dataset.sup)}"][value="${CSS.escape(t.value)}"]`); }
    else if (t.name === 'col-libro' || t.name === 'col-sexo') { estado[t.name === 'col-libro' ? 'colLibro' : 'colSexo'] = t.value; rerender(`input[name="${t.name}"][value="${CSS.escape(t.value)}"]`); }
    else if (t.name === 'modo-pasaje') { estado.comparar = t.value === 'comparar'; store.set('biblia.comparar', estado.comparar); rerender(`input[name="modo-pasaje"][value="${t.value}"]`); }
    else if (t.dataset && t.dataset.col) { alternarColumna(t.dataset.col, t.checked); rerender(`input[data-col="${t.dataset.col}"]`); }
    else if (t.name === 'voz-idioma') {
      parar(); habla.idioma = t.value; store.set('biblia.vozIdioma', t.value);
      const r = $('#reproductor'); if (r) { r.outerHTML = reproductorHTML(); const i = main.querySelector(`input[name="voz-idioma"][value="${t.value}"]`); if (i) i.focus(); }
      if (t.value !== 'es') cargarOriginales(t.value === 'he' ? 'o' : 'g', `input[name="voz-idioma"][value="${t.value}"]`);
    }
    else if (t.name === 'trad') { estado.trad = t.value; store.set('biblia.trad', t.value); rerender(`input[name="trad"][value="${t.value}"]`); }
    else if (t.name === 'vista-arbol') { estado.vistaArbol = t.value; store.set('biblia.vistaArbol', t.value); rerender(`input[name="vista-arbol"][value="${t.value}"]`); if (estado.vistaArbol === 'grafico') centrarLienzos(); }
  });
  // Árbol gráfico: tamaño (se aplica sin repintar), centrado inicial y arrastre con el ratón para recorrerlo.
  function zoomGA(paso) {
    estado.gaZoom = Math.min(1.5, Math.max(0.4, Math.round((estado.gaZoom + paso * 0.1) * 10) / 10));
    main.querySelectorAll('.ga-contenido').forEach(c => { c.style.zoom = estado.gaZoom; });
    conectoresTodos();
    const z = $('#ga-zoom-txt'); if (z) z.textContent = Math.round(estado.gaZoom * 100) + ' %';
  }
  let tRes = 0;
  window.addEventListener('resize', () => { clearTimeout(tRes); tRes = setTimeout(conectoresTodos, 120); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(conectoresTodos);
  function centrarLienzos() {
    main.querySelectorAll('.ga-lienzo').forEach(l => {
      const f = l.querySelector('.ga > li > .ga-fam'); if (!f) return;
      const rl = l.getBoundingClientRect(), rf = f.getBoundingClientRect();
      l.scrollLeft += (rf.left + rf.width / 2) - (rl.left + rl.width / 2);
    });
  }
  let arrastre = null;
  document.addEventListener('pointerdown', e => {
    const l = e.target.closest && e.target.closest('.ga-lienzo');
    if (!l || e.pointerType !== 'mouse' || e.button !== 0 || e.target.closest('button, a, input')) return;
    arrastre = { l, x: e.clientX, y: e.clientY, sl: l.scrollLeft, st: l.scrollTop }; l.classList.add('arrastrando'); try { l.setPointerCapture(e.pointerId); } catch (x) { /* sin captura */ }
  });
  document.addEventListener('pointermove', e => { if (arrastre) { arrastre.l.scrollLeft = arrastre.sl - (e.clientX - arrastre.x); arrastre.l.scrollTop = arrastre.st - (e.clientY - arrastre.y); } });
  const soltar = () => { if (arrastre) { arrastre.l.classList.remove('arrastrando'); arrastre = null; } };
  document.addEventListener('pointerup', soltar); document.addEventListener('pointercancel', soltar);
  document.addEventListener('input', e => {
    if (e.target.id === 'rep-vel') { habla.vel = +e.target.value || 1; store.set('biblia.vozVel', habla.vel); const o = $('#rep-vel-txt'); if (o) o.textContent = habla.vel.toFixed(1).replace('.', ',') + '×'; }
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

  function iniciar() {
    const ml = document.querySelector('.marca-libro'); if (ml && D) ml.textContent = N.alcance(D).texto; // alcance de los datos, no fijo
    render(false); registrarSW();
  }
  if (!D && /[?&]ejemplo/.test(location.search)) {
    const s = document.createElement('script');
    s.src = 'pruebas/datos-ejemplo.js';
    s.onload = () => { D = window.BIBLIA_DATOS || null; if (D && window.BIBLIA_EJEMPLO_EXODO) D = window.BIBLIA_EJEMPLO_EXODO(D); MAPA = window.BIBLIA_MAPA || null; iniciar(); };
    s.onerror = iniciar;
    document.head.appendChild(s);
  } else iniciar();
})();
