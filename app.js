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
  const NOMBRES_LIBRO = { Gn: 'Génesis', Ex: 'Éxodo', Lv: 'Levítico', Nm: 'Números', Dt: 'Deuteronomio', Jos: 'Josué', Jue: 'Jueces', Rt: 'Rut', '1S': '1 Samuel', '2S': '2 Samuel', '1R': '1 Reyes' };
  const ordLibro = new Map(), idPorOrd = new Map(), idCanon = new Map();
  CANON.forEach((id, i) => { ordLibro.set(norm(id), i + 1); idPorOrd.set(i + 1, id); idCanon.set(norm(id), id); });
  Object.entries(NOMBRES_LIBRO).forEach(([id, n]) => { idCanon.set(norm(n), id); idCanon.set(norm(n).replace(/\s+/g, ''), id); }); // «1 Samuel» y «1Samuel»
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
      for (const v of (c.versiculos || [])) out.push(Object.assign({ libro: lb, cap: c.cap, n: v.n, texto: v.texto || '', ref: refTxt(c.cap, v.n, lb), clave: o + c.cap * 1000 + v.n }, !v.texto && v.nota ? { nota: v.nota } : {}));
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
  // Menciones de personas y lugares que se marcan en un versículo, en orden y sin solapes (gana la que empieza antes y,
  // a igual inicio, la más larga).
  function mencionesVerso(d, ref, texto) {
    const ms = mencionesDe(d, ref, texto, 'persona').concat(mencionesDe(d, ref, texto, 'lugar'))
      .sort((a, b) => a.inicio - b.inicio || b.fin - a.fin);
    const out = [];
    let pos = 0;
    for (const m of ms) { if (m.inicio < pos) continue; out.push(m); pos = m.fin; }
    return out;
  }
  const solapan = (a, b) => a.inicio < b.fin && b.inicio < a.fin;
  // Términos ({termino, inicio, fin}) que quedan en un versículo: una persona o un lugar que se solapa gana al término.
  function terminosVerso(ms, ts, largo) {
    const out = [];
    [...(ts || [])].sort((a, b) => a.inicio - b.inicio).forEach(t => {
      if (!t || !t.termino || !Number.isInteger(t.inicio) || !Number.isInteger(t.fin) || t.inicio < 0 || t.fin <= t.inicio || t.fin > largo) return;
      if (!ms.some(m => solapan(m, t)) && !out.some(o => solapan(o, t))) out.push(t);
    });
    return out;
  }
  // Trozos [{texto, persona?|lugar?|termino?}] de un versículo; ignora menciones fuera de rango o solapadas.
  // `terminos` (opcional): los términos a subrayar en este versículo (ver marcadoPasaje); pierden ante personas y lugares.
  function segmentar(d, ref, texto, terminos) {
    texto = String(texto || '');
    const ms = mencionesVerso(d, ref, texto);
    const todos = ms.concat(terminos && terminos.length ? terminosVerso(ms, terminos, texto.length) : []).sort((a, b) => a.inicio - b.inicio);
    const out = [];
    let pos = 0;
    for (const m of todos) {
      if (m.inicio > pos) out.push({ texto: texto.slice(pos, m.inicio) });
      const s = texto.slice(m.inicio, m.fin);
      out.push(m.lugar ? { texto: s, lugar: m.lugar } : m.persona ? { texto: s, persona: m.persona } : { texto: s, termino: m.termino });
      pos = m.fin;
    }
    if (pos < texto.length) out.push({ texto: texto.slice(pos) });
    return out;
  }

  const unir = xs => xs.length < 2 ? (xs[0] || '') : xs.slice(0, -1).join(', ') + ' y ' + xs[xs.length - 1];
  const unicos = xs => xs.filter((x, i) => xs.indexOf(x) === i);
  // "hijo de Adán y Eva; esposo de …", calculado de las relaciones. `refOk(ref)` (opcional) deja solo las
  // relaciones cuya cita ya es accesible (lectura en orden): sin él, «esposo de Betsabé» saldría antes de 2 S 11.
  function contextoPersona(d, id, refOk) {
    const I = indice(d), p = I.personas.get(id);
    if (!p) return '';
    const nom = x => (I.personas.get(x) || {}).nombre || x;
    const ok = r => !refOk || refOk(r.ref);
    const partes = [];
    const pad = unicos((I.padres.get(id) || []).filter(ok).map(r => r.de));
    if (pad.length) partes.push(`${p.sexo === 'f' ? 'hija' : p.sexo === 'm' ? 'hijo' : p.sin_nombre ? 'descendencia' : 'hijo o hija'} de ${unir(pad.map(nom))}`);
    const cs = unicos((I.conyuges.get(id) || []).filter(ok).map(r => r.otro));
    if (cs.length) partes.push(`${p.sexo === 'f' ? 'esposa' : p.sexo === 'm' ? 'esposo' : 'cónyuge'} de ${unir(cs.map(nom))}`);
    return partes.join('; ');
  }

  // Contenido del acompañante para uno o varios versículos.
  function acompanante(d, refs, refOk) {
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
    return { personas: ids.map(id => ({ id, contexto: contextoPersona(d, id, refOk) })), vinculos, edades: edadesV,
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
  // Personas nombradas en los pasajes leídos (desbloqueo sin catálogo de juego, y obtención de los NPC).
  function coleccionBase(d, leidos) {
    const L = new Set(leidos || []), out = new Set();
    pasajes(d).forEach(p => { if (L.has(p.id)) personasDePasaje(d, p).forEach(id => out.add(id)); });
    return out;
  }
  /* ---- Catálogo de juego (datos/juego.js, `J`): estado de personajes, objetos y escenarios según lo leído ----
     Personaje: se desbloquea al terminar de leer el capítulo `listo.capitulo` (todos los pasajes que lo cubren);
     antes, si ya apareció en algo leído, está «en curso». NPC (solo genealogías): al leer su primera mención.
     Objeto y escenario: al leer el pasaje de su primera aparición. Sin `J`, todo como antes (primera mención). */
  const juegoValido = J => !!(J && typeof J === 'object' && J.personajes && typeof J.personajes === 'object');
  const cacheJ = new WeakMap();
  function memoJ(d, J, k, fn) {
    if (!cacheJ.has(J)) cacheJ.set(J, new WeakMap());
    const w = cacheJ.get(J), dd = d && typeof d === 'object' ? d : cacheJ;
    if (!w.has(dd)) w.set(dd, new Map());
    const m = w.get(dd); if (!m.has(k)) m.set(k, fn()); return m.get(k);
  }
  const rangosAp = aps => (Array.isArray(aps) ? aps : []).map(x => x && x.inicio ? rangoClaves(`${x.inicio}-${x.fin || x.inicio}`) : null).filter(Boolean);
  const cruzaRangos = (rs, r) => !!r && rs.some(x => x.a <= r.b && r.a <= x.b);
  // Pasajes (ids, en orden de lectura) que se solapan con los rangos.
  const pasajesEnRangos = (d, rs) => rs.length ? pasajes(d).filter(p => cruzaRangos(rs, rangoPasaje(p))).map(p => p.id) : [];
  const capDeRef = ref => { const r = parseRef(ref); return r ? `${r.libro} ${r.cap}` : null; };
  // Capítulo cuya lectura completa desbloquea: `listo.capitulo`, o el de `listo.ref`, o el de la última aparición.
  function capituloListo(e) {
    if (!e) return null;
    const l = e.listo || {};
    if (l.capitulo && rangoClaves(l.capitulo)) return String(l.capitulo);
    if (l.ref && clave(l.ref) !== null) return capDeRef(l.ref);
    const rs = rangosAp(e.apariciones);
    return rs.length ? capDeRef(refDeClave(Math.max(...rs.map(r => r.b)))) : null;
  }
  function infoPersonaje(d, J, id) {
    return memoJ(d, J, 'p|' + id, () => {
      const e = J.personajes[id]; if (!e || typeof e !== 'object') return null;
      const npc = !!e.npc, cap = npc ? null : capituloListo(e), rc = cap && rangoClaves(cap);
      return { npc, nivel: npc ? 0 : (Number.isFinite(+e.nivel) && e.nivel !== null ? +e.nivel : null), capitulo: cap,
        apar: pasajesEnRangos(d, rangosAp(e.apariciones)), capPasajes: rc ? pasajesEnRangos(d, [rc]) : [] };
    });
  }
  function estadoDe(d, J, id, L, menc) {
    const visto = menc.has(id), inf = juegoValido(J) ? infoPersonaje(d, J, id) : null;
    if (!inf) return { id, juego: false, estado: visto ? 'obtenido' : 'bloqueado', npc: false, nivel: null, capitulo: null, leidos: 0, total: 0 };
    const leidos = inf.apar.filter(x => L.has(x)).length;
    let estado;
    if (inf.npc) estado = visto ? 'obtenido' : 'bloqueado';
    else if (!inf.capPasajes.length) estado = visto || leidos ? 'obtenido' : 'bloqueado'; // capítulo fuera de los datos cargados
    else if (inf.capPasajes.every(x => L.has(x))) estado = 'obtenido';
    else estado = visto || leidos ? 'en-curso' : 'bloqueado';
    return { id, juego: true, estado, npc: inf.npc, nivel: inf.nivel, capitulo: inf.capitulo, leidos, total: inf.apar.length };
  }
  // Estado de un personaje: { estado: 'obtenido'|'en-curso'|'bloqueado', npc, nivel, capitulo, leidos, total }.
  const estadoPersonaje = (d, J, id, leidos) => estadoDe(d, J, id, new Set(leidos || []), coleccionBase(d, leidos));
  // Colección: personas obtenidas (con catálogo de juego, según su regla; sin él, las nombradas en lo leído).
  function coleccion(d, leidos, J) {
    const base = coleccionBase(d, leidos);
    if (!juegoValido(J)) return base;
    const L = new Set(leidos || []);
    return new Set(coleccionables(d).filter(id => estadoDe(d, J, id, L, base).estado === 'obtenido'));
  }
  // Las que entran al marcar `pasajeId` como leído, dado lo ya leído.
  function nuevasAlLeer(d, leidos, pasajeId, J) {
    const p = pasajes(d).find(x => x.id === pasajeId); if (!p) return [];
    const sin = [].concat(leidos || []).filter(x => x !== pasajeId);
    const antes = coleccion(d, sin, J);
    if (!juegoValido(J)) return personasDePasaje(d, p).filter(id => !antes.has(id));
    const despues = coleccion(d, sin.concat(pasajeId), J);
    return coleccionables(d).filter(id => despues.has(id) && !antes.has(id));
  }
  const libroDeClave = k => idPorOrd.get(Math.floor(k / 1e6));
  const capDeClave = k => `${libroDeClave(k)} ${Math.floor(k / 1000) % 1000}`;
  // Fichas de la colección: sin desbloquear solo se da el capítulo de la primera aparición.
  function fichasColeccion(d, leidos, J) {
    const base = coleccionBase(d, leidos), L = new Set(leidos || []), I = indice(d), V = versosPersona(d);
    return coleccionables(d).map(id => {
      const k = I.primera.get(id), p = I.personas.get(id) || {}, e = estadoDe(d, J, id, L, base);
      return { id, desbloqueada: e.estado === 'obtenido', estado: e.estado, juego: e.juego, npc: e.npc, nivel: e.nivel, capitulo: e.capitulo, leidos: e.leidos, total: e.total,
        primera: refDeClave(k), primeraCap: capDeClave(k),
        libros: unicos((V.get(id) || []).map(libroDeClave)), sexo: p.sexo === 'f' || p.sexo === 'm' ? p.sexo : '?', rareza: rareza(d, id) };
    });
  }
  const GRUPOS_JUEGO = ['objetos', 'escenarios'];
  function infoCosa(d, J, grupo, id) {
    return memoJ(d, J, grupo + '|' + id, () => {
      const rs = rangosAp(((J[grupo] || {})[id] || {}).apariciones);
      if (!rs.length) return { primera: null, pasaje: null, apar: [] };
      const k = Math.min(...rs.map(r => r.a)), p = pasajes(d).find(x => { const r = rangoPasaje(x); return r && k >= r.a && k <= r.b; });
      return { primera: k, pasaje: p ? p.id : null, apar: pasajesEnRangos(d, rs) };
    });
  }
  // Estado de un objeto o escenario: obtenido al leer el pasaje de su primera aparición.
  function estadoCosa(d, J, grupo, id, leidos) {
    if (!juegoValido(J) || !GRUPOS_JUEGO.includes(grupo) || !(J[grupo] || {})[id]) return null;
    const L = leidos instanceof Set ? leidos : new Set(leidos || []), inf = infoCosa(d, J, grupo, id);
    return { id, grupo, estado: inf.pasaje && L.has(inf.pasaje) ? 'obtenido' : 'bloqueado', pasaje: inf.pasaje,
      primera: inf.primera ? refDeClave(inf.primera) : null, primeraCap: inf.primera ? capDeClave(inf.primera) : null,
      leidos: inf.apar.filter(x => L.has(x)).length, total: inf.apar.length };
  }
  // Fichas de objetos o escenarios, en orden de primera aparición (solo las que caen en los pasajes cargados).
  function fichasCosas(d, J, grupo, leidos) {
    if (!juegoValido(J) || !GRUPOS_JUEGO.includes(grupo) || !J[grupo] || typeof J[grupo] !== 'object') return [];
    const L = new Set(leidos || []);
    return Object.keys(J[grupo]).map(id => {
      const e = J[grupo][id] || {}, s = estadoCosa(d, J, grupo, id, L);
      return s && Object.assign(s, { nombre: e.nombre || id, tipo: e.tipo || '', desbloqueada: s.estado === 'obtenido', orden: infoCosa(d, J, grupo, id).primera });
    }).filter(x => x && x.pasaje).sort((a, b) => a.orden - b.orden);
  }
  // Todo lo que entra al marcar `pasajeId` como leído: { personas, objetos, escenarios }.
  function nuevosAlLeer(d, J, leidos, pasajeId) {
    const sin = [].concat(leidos || []).filter(x => x !== pasajeId), con = sin.concat(pasajeId);
    const out = { personas: nuevasAlLeer(d, sin, pasajeId, J) };
    GRUPOS_JUEGO.forEach(g => { const a = new Set(fichasCosas(d, J, g, sin).filter(x => x.desbloqueada).map(x => x.id)); out[g] = fichasCosas(d, J, g, con).filter(x => x.desbloqueada && !a.has(x.id)).map(x => x.id); });
    return out;
  }
  // Qué puede mostrar una ficha abierta desde cualquier enlace: el contenido del catálogo solo si está obtenida;
  // si no, como en la colección (capítulo de la primera aparición y, en curso, el avance). null: sin entrada en el catálogo.
  function vistaFichaJuego(d, J, grupo, id, leidos) {
    if (!juegoValido(J)) return null;
    if (grupo === 'personajes') {
      if (!J.personajes[id]) return null;
      const e = estadoPersonaje(d, J, id, leidos), k = indice(d).primera.get(id);
      return Object.assign(e, { visible: e.estado === 'obtenido', primeraCap: k ? capDeClave(k) : null });
    }
    const s = estadoCosa(d, J, grupo, id, leidos);
    return s && Object.assign(s, { visible: s.estado === 'obtenido' });
  }
  // Genealogías del catálogo que se solapan con un pasaje (el lector las rotula; nunca cuentan como aparición).
  function genealogiasDe(J, p) {
    const r = rangoPasaje(p);
    if (!r || !J || !Array.isArray(J.genealogias)) return [];
    return J.genealogias.filter(g => g && g.inicio && cruzaRangos([rangoClaves(`${g.inicio}-${g.fin || g.inicio}`)].filter(Boolean), r));
  }
  const esGenealogia = (J, p) => genealogiasDe(J, p).length > 0;
  // Perfil niño: un dato cuya ref cae en una parte de contenido alto se pliega, como el resto de la app.
  const datoPlegado = (perfil, C, ref) => esNino(perfil) && clave(ref) !== null && esAlto(C, clave(ref));
  // Objetos y escenarios del catálogo que nombran a una persona; y escenarios que incluyen un objeto.
  function relacionadosJuego(J, tipo, id) {
    if (!juegoValido(J)) return { objetos: [], escenarios: [] };
    const tiene = (e, campo) => Array.isArray(e && e[campo]) && e[campo].includes(id);
    const campo = tipo === 'objeto' ? 'objetos' : 'personas';
    return { objetos: tipo === 'objeto' ? [] : Object.keys(J.objetos || {}).filter(k => tiene(J.objetos[k], campo)),
      escenarios: Object.keys(J.escenarios || {}).filter(k => tiene(J.escenarios[k], campo)) };
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
  /* ---- Manuscritos (datos/manuscritos.js, bajo demanda): el registro real de donde sale el texto ---- */
  // "Gn 1:1", "Gn 1:1" → "Gn 1:1"; mismo capítulo → "Gn 1:1–19"; mismo libro → "Gn 1:26–2:3"; libros distintos con guion largo espaciado.
  function tramoRefs(a, b) {
    const x = parseRef(a), y = parseRef(b); if (!x || !y) return '';
    if (x.libro !== y.libro) return `${x.libro} ${x.cap}:${x.v} – ${y.libro} ${y.cap}:${y.v}`;
    if (x.cap !== y.cap) return `${x.libro} ${x.cap}:${x.v}–${y.cap}:${y.v}`;
    return x.v === y.v ? `${x.libro} ${x.cap}:${x.v}` : `${x.libro} ${x.cap}:${x.v}–${y.v}`;
  }
  // "001b" → "1v" (a = recto, b = verso), como lo numera Commons ("folio 001b (1v)").
  const nombreFolio = id => { const m = /^0*(\d+)([ab])$/.exec(String(id || '')); return m ? m[1] + (m[2] === 'a' ? 'r' : 'v') : String(id || ''); };
  const foliosCache = new WeakMap();
  const foliosRangos = M => {
    const F = M && M.leningrado && M.leningrado.folios; if (!F) return [];
    if (!foliosCache.has(F)) foliosCache.set(F, Object.keys(F).sort().map(id => ({ id, f: F[id], rs: (F[id].rv || []).map(rangoClaves).filter(Boolean) })));
    return foliosCache.get(F);
  };
  // Folios del Códice de Leningrado que contienen versículos del pasaje. `muestra` dice solo el tramo de ESTE pasaje
  // (lectura en orden: nunca adelanta versículos posteriores); `otros` = la página también trae texto de fuera del pasaje.
  function foliosDePasaje(M, d, p) {
    if (!p) return [];
    const vs = versiculosDe(d, p); if (!vs.length) return [];
    const a = vs[0].clave, b = vs[vs.length - 1].clave;
    return foliosRangos(M).map(({ id, f, rs }) => {
      const dentro = vs.filter(v => rs.some(r => v.clave >= r.a && v.clave <= r.b));
      if (!dentro.length) return null;
      return Object.assign({}, f, { id, nombre: nombreFolio(id), muestra: tramoRefs(dentro[0].ref, dentro[dentro.length - 1].ref), otros: rs.some(r => r.a < a || r.b > b) });
    }).filter(Boolean);
  }
  // Rollos testigo con versículos del pasaje y a qué se enlaza (Leon Levy: solo enlace). El fragmento solo si alguno de los
  // suyos cae en el pasaje; si no, las láminas o la ficha. Sin datos de manuscritos, la ficha del testigo.
  function rollosDePasaje(M, O, d, p) {
    if (!p) return [];
    const vs = versiculosDe(d, p); if (!vs.length) return [];
    const a = vs[0].clave, b = vs[vs.length - 1].clave, R = (M && M.rollos) || {}, base = R.url_imagen || '';
    const img = x => ({ imagen: x.imagen, url: base + x.imagen, tipo_foto: x.tipo_foto || null, lado: x.lado || null });
    return testigosDe(O, vs.map(v => v.ref)).filter(t => t.tipo === 'rollo').map(t => {
      const r = (R.rollos || {})[t.id] || {};
      const frs = r.nivel === 'fragmento' ? (r.fragmentos || []).filter(f => (f.versiculos || []).some(s => { const c = rangoClaves(s); return c && c.a <= b && a <= c.b; })) : [];
      const nivel = frs.length ? 'fragmento' : (r.laminas || []).length ? 'lamina' : 'ficha';
      return { id: t.id, nombre: t.nombre || t.id, sigla: r.sigla || t.sigla || null, institucion: t.institucion || null, fecha: t.fecha || null, nivel,
        fragmentos: frs.map(f => ({ abegg: f.abegg, imagenes: (f.imagenes || []).map(img), comprobado: f.comprobado || null })),
        laminas: nivel === 'lamina' ? r.laminas.map(img) : [], ficha: r.ficha || t.url || null };
    });
  }
  // Página donde empieza el libro en el Códice Vaticano (solo enlace).
  // Las claves del archivo son ids de libro («Rut», «1S»); se comparan por libro canónico («Rt» = «Rut»).
  function vaticanoDeLibro(M, lb) {
    const V = (M && M.vaticano && M.vaticano.libros) || {}, o = ordDe(lb);
    if (V[lb]) return V[lb];
    const k = o ? Object.keys(V).find(x => ordDe(x) === o) : null;
    return k ? V[k] : null;
  }
  // Variantes cuyo versículo (o rango) cae en los versículos dados.
  function variantesDe(O, refs) {
    const ks = new Set((refs || []).map(clave).filter(k => k !== null));
    return ((O && O.variantes) || []).filter(v => { const c = rangoClaves(v.ref); if (!c) return false; for (const k of ks) if (k >= c.a && k <= c.b) return true; return false; });
  }
  // Ref de la numeración hebrea solo cuando difiere de la de la RV ("Gn 31:55" → "Gn 32:1"); null si coincide o falta.
  // Si a un versículo RV le corresponden varios hebreos, r es un tramo ("Nm 13:32-33" → "13:32–33"; "Nm 25:19-26:1" → "25:19–26:1").
  // Notas del griego que vienen del TVTMS («TVTMS (LongVerseDuplicated): GreekUndivided* «1Ki.12:3 [=1Ki.12:24.15]»»):
  // se dicen en castellano para el lector; el dato técnico queda en griego-swete.js.
  const OSIS_LIBRO = { Gen: 'Gn', Exo: 'Ex', Lev: 'Lv', Num: 'Nm', Deu: 'Dt', Jos: 'Jos', Jdg: 'Jue', Rut: 'Rt', '1Sa': '1 S', '2Sa': '2 S', '1Ki': '1 R', '2Ki': '2 R' };
  const TVTMS_FRASE = {
    TextMayBeMissing: 'En la LXX este versículo puede faltar o venir incompleto',
    MergedPrevVerse: 'En la LXX este texto va unido al versículo anterior',
    MergedVerse: 'En la LXX este texto va unido a otro versículo',
    LongVerseElsewhereJoin: 'En la LXX este texto va unido a otro versículo',
    SubdividedVerse: 'En la LXX este versículo se divide de otra forma',
    OneToOne: 'En la LXX corresponde a otro número de versículo',
    DuplicateTarget: 'En la LXX corresponde a un versículo que también recoge otro texto',
    LongVerseElsewhere: 'La LXX trae este contenido en otro lugar',
    'LongVerse/LVElsewhere': 'La LXX trae este contenido en otro lugar',
    LongVerseDuplicated: 'La LXX repite este contenido en otro lugar',
    'LongVerse/LVDuplicated': 'La LXX repite este contenido en otro lugar' };
  function notaGriegoLegible(t) {
    const s = String(t == null ? '' : t), m = /^TVTMS \(([^)]+)\):\s*(?:en\s+)?[^«]*«([^»]*)»\s*(.*)$/.exec(s);
    if (!m) return s;
    const ref = m[2].replace(/\b(Gen|Exo|Lev|Num|Deu|Jos|Jdg|Rut|1Sa|2Sa|1Ki|2Ki)\.(\d)/g, (_, b, d) => `${OSIS_LIBRO[b]} ${d}`)
      .replace(/\[=\+?/g, '(= ').replace(/\]/g, ')').replace(/(\d+:\d+)\.0\b/g, '$1');
    const resto = m[3].replace(/^;\s*corresponde a .*?equivalente\b/, '').replace(/^;\s*/, '').replace(/^sin versículo completo equivalente/, 'sin un versículo completo equivalente')
      .replace(/\(esta edición no cumple todos los TEST del bloque\)/, '(la edición de Swete no cumple todas las comprobaciones del TVTMS)').replace(/\s+$/, '');
    return `${TVTMS_FRASE[m[1]] || 'En la LXX la numeración difiere'}: ${ref}${resto ? '. ' + resto.charAt(0).toUpperCase() + resto.slice(1) + (/[.»]$/.test(resto) ? '' : '.') : '.'} (Correspondencia según el TVTMS, de Tyndale House.)`;
  }
  function numeracionHebrea(ref, r) {
    if (!r) return null;
    const a = parseRef(ref), b = parseRef(r);
    const tramo = /:\s*\d+\s*-\s*\d/.test(String(r)) ? String(r).replace(/^\s*(?:[1-3]\s?)?[^\d\s:]+\.?\s+/, '').replace(/\s*-\s*/, '–') : null;
    if (tramo && a && b && a.libro === b.libro) return tramo;
    const parte = /:\s*\d+([a-z])\s*$/.exec(String(r));  // media unidad del hebreo (p. ej. Jue 14:18a)
    if (parte && a && b && a.libro === b.libro) return `${b.cap}:${b.v}${parte[1]}`;
    if (!a || !b || (a.libro === b.libro && a.cap === b.cap && a.v === b.v)) return null;
    return a.libro === b.libro ? `${b.cap}:${b.v}` : `${b.libro} ${b.cap}:${b.v}`;
  }
  // Filas alineadas por versículo de la RV: { ref, cap, n, rv, he, heNum, gr }. Lo que falta queda en null.
  function alinearOriginales(d, pasaje, O, G) {
    const H = (O && O.hebreo) || {}, T = (G && G.texto) || {};
    return versiculosDe(d, pasaje).map(v => {
      const h = H[v.ref];
      const he = (h && h.t) || null, gr = T[v.ref] || null, falta = sinTextoDe(O, G, v.ref);
      const heNota = (O && O.hebreo_notas && O.hebreo_notas[v.ref]) || null, grNota = (G && G.notas && G.notas[v.ref]) ? notaGriegoLegible(G.notas[v.ref]) : null;
      return Object.assign({ ref: v.ref, cap: v.cap, n: v.n, rv: v.texto || null, he, heNum: h ? numeracionHebrea(v.ref, h.r) : null, gr }, v.nota ? { nota: v.nota } : {},
        !he && falta.he ? { heFalta: falta.he } : {}, !gr && falta.gr ? { grFalta: falta.gr } : {},
        he && heNota ? { heNota } : {}, gr && grNota ? { grNota } : {});
    });
  }
  // Motivo por el que un versículo no tiene texto original (datos: `hebreo_sin_texto` y `sin_texto` del griego), tal cual.
  const notaFalta = x => typeof x === 'string' ? x : x && typeof x === 'object' ? String(x.nota || x.motivo || '') : '';
  const sinTextoDe = (O, G, ref) => ({ he: notaFalta(((O && O.hebreo_sin_texto) || {})[ref]) || null, gr: notaFalta(((G && G.sin_texto) || {})[ref]) || null });
  // Lista de versículos sin hebreo o sin griego, con su motivo: [{ ref, idioma: 'he'|'gr', nota }].
  const sinTextoOriginal = (O, G, refs) => [].concat(...(refs || []).map(ref => { const f = sinTextoDe(O, G, ref); return [['he', f.he], ['gr', f.gr]].filter(x => x[1]).map(([idioma, nota]) => ({ ref, idioma, nota })); }));
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
    if (f.tipo === 'registro') return 'Registro histórico';
    if (f.tipo === 'arqueologia') return f.relacion === 'contexto' ? 'Contexto de la época' : 'Objeto histórico';
    return 'Fuente externa';
  }

  /* ---- Recorridos (datos/recorridos.js): etapas del relato y su ubicación según cada hipótesis ---- */
  // El nombre, el orden, la cita y la ref de cada etapa son texto bíblico; su ubicación es una hipótesis moderna (fuente externa).
  const listaRecorridos = RC => ((RC && RC.recorridos) || []).filter(r => r && r.id && Array.isArray(r.etapas) && r.etapas.length);
  const recorrido = (RC, id) => listaRecorridos(RC).find(r => r.id === id) || null;
  // Etapas por `orden` (las que no lo traen quedan en su posición de los datos).
  const etapasOrdenadas = rec => ((rec && rec.etapas) || []).filter(Boolean).map((e, i) => ({ e, i, o: Number.isFinite(+e.orden) && e.orden !== null ? +e.orden : i }))
    .sort((a, b) => (a.o - b.o) || (a.i - b.i)).map(x => x.e);
  const hipotesisDefecto = rec => { const hs = ((rec && rec.hipotesis) || []).filter(h => h && h.id); return hs.find(h => h.defecto) || hs[0] || null; };
  const coordValida = u => !!u && u.lat !== null && u.lon !== null && u.lat !== undefined && u.lon !== undefined && u.lat !== '' && u.lon !== '' && Number.isFinite(+u.lat) && Number.isFinite(+u.lon);
  // Ubicación de una etapa según la hipótesis. Si la clave de esa hipótesis FALTA en `ubicaciones`, vale la de la hipótesis
  // por defecto (`heredada`). Si la clave está pero sin coordenadas, esa hipótesis no propone lugar: null (ver sinPropuesta).
  const tieneClave = (o, k) => !!o && !!k && Object.prototype.hasOwnProperty.call(o, k) && o[k] !== undefined;
  function ubicacionEtapa(rec, etapa, hipId) {
    const U = (etapa && etapa.ubicaciones) || {}, def = hipotesisDefecto(rec);
    const sale = (u, h, heredada) => Object.assign({}, u, { lat: +u.lat, lon: +u.lon, confianza: ['alta', 'media', 'baja'].includes(u.confianza) ? u.confianza : 'baja', hipotesis: h, heredada });
    if (tieneClave(U, hipId)) return coordValida(U[hipId]) ? sale(U[hipId], hipId, false) : null;
    if (def && coordValida(U[def.id])) return sale(U[def.id], def.id, !!hipId && hipId !== def.id);
    return null;
  }
  // La hipótesis trae la etapa pero sin coordenadas: no propone ubicación para ella.
  const sinPropuesta = (rec, etapa, hipId) => { const U = (etapa && etapa.ubicaciones) || {}, h = tieneClave(U, hipId) ? hipId : (hipotesisDefecto(rec) || {}).id; return tieneClave(U, h) && !coordValida(U[h]); };
  // Índices (sobre etapasOrdenadas) de las etapas cuya ref cae en alguno de los versículos dados.
  function etapasDeRefs(rec, refs) {
    const ks = [...new Set([].concat(refs || []).map(clave).filter(k => k !== null))];
    if (!ks.length) return [];
    return etapasOrdenadas(rec).map((e, i) => ({ c: rangoClaves(e.ref), i })).filter(x => x.c && ks.some(k => k >= x.c.a && k <= x.c.b)).map(x => x.i);
  }
  // Etapa activa al leer: la del versículo marcado si es una etapa; si no, la última del pasaje. null si el pasaje no toca el recorrido.
  function etapaActiva(rec, refsPasaje, refActivo) {
    const aqui = etapasDeRefs(rec, refsPasaje);
    if (!aqui.length) return null;
    const enActivo = refActivo ? etapasDeRefs(rec, [refActivo]) : [];
    return { actual: enActivo.length ? enActivo[enActivo.length - 1] : aqui[aqui.length - 1], aqui };
  }
  const recorridosDeRefs = (RC, refs, refActivo) => listaRecorridos(RC).map(rec => ({ rec, a: etapaActiva(rec, refs, refActivo) })).filter(x => x.a).map(x => ({ rec: x.rec, actual: x.a.actual, aqui: x.a.aqui }));
  function distanciaKm(a, b) { // [lon, lat] → km (haversine)
    const r = Math.PI / 180, dLat = (b[1] - a[1]) * r, dLon = (b[0] - a[0]) * r;
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(a[1] * r) * Math.cos(b[1] * r) * Math.sin(dLon / 2) ** 2;
    return 2 * 6371 * Math.asin(Math.min(1, Math.sqrt(h)));
  }
  // Tramos entre etapas ubicadas consecutivas. Un tramo es incierto si toca una etapa de confianza baja;
  // `sinPropuesta` si salta etapas que esa hipótesis no sitúa (se dibuja tenue, como unión sin propuesta).
  function tramosRecorrido(rec, hipId) {
    const out = []; let prev = null, saltadas = false;
    etapasOrdenadas(rec).forEach((e, i) => {
      const u = ubicacionEtapa(rec, e, hipId);
      if (!u) { if (sinPropuesta(rec, e, hipId)) saltadas = true; return; }
      if (prev) {
        const cs = [prev.u.confianza, u.confianza], desde = [prev.u.lon, prev.u.lat], hasta = [u.lon, u.lat];
        out.push({ de: prev.i, a: i, desde, hasta, incierto: cs.includes('baja'), sinPropuesta: saltadas, confianza: cs.includes('baja') ? 'baja' : cs.includes('media') ? 'media' : 'alta', km: distanciaKm(desde, hasta) });
      }
      prev = { i, u }; saltadas = false;
    });
    return out;
  }
  // Ritmo del relato: el viaje dura más cuanto más lejos (no lineal) y la parada, según lo que hay que leer.
  const duracionTramo = km => Math.round(Math.min(4200, Math.max(900, 520 + 420 * Math.sqrt(Math.max(0, +km || 0) / 10))));
  const pausaEtapa = e => Math.round(Math.min(6500, Math.max(2200, 1500 + 34 * String((e && e.cita) || '').length)));

  /* ---- Perfiles locales (sin cuentas): cada uno guarda lo suyo bajo biblia.p.<id>.* ---- */
  const PREF = 'biblia.', CLAVE_PERFILES = 'biblia.perfiles';
  const COLORES_PERFIL = ['lapis', 'verdin', 'ocre', 'murice', 'carmin', 'mar'];
  const TIPOS_PERFIL = ['adulto', 'nino'];
  const subclave = k => { const s = String(k); return s.startsWith(PREF) ? s.slice(PREF.length) : s; };
  const clavePerfil = (id, k) => `${PREF}p.${id}.${subclave(k)}`;
  // Claves de antes de los perfiles (biblia.pos, biblia.pasajesLeidos…): ni el registro ni las ya separadas por perfil.
  const esClaveLegada = k => typeof k === 'string' && k.startsWith(PREF) && k !== CLAVE_PERFILES && !k.startsWith(PREF + 'p.');
  const clavesDePerfil = (claves, id) => (claves || []).filter(k => typeof k === 'string' && k.startsWith(`${PREF}p.${id}.`));
  const inicialDe = nombre => (Array.from(String(nombre || '').trim())[0] || '?').toLocaleUpperCase('es');
  function nuevoPerfil(lista, datos) {
    const usados = new Set((lista || []).map(p => p.id));
    let n = (lista || []).length + 1; while (usados.has('p' + n)) n++;
    const x = datos || {}, nombre = String(x.nombre || '').trim().slice(0, 24) || (x.tipo === 'nino' ? 'Niño' : 'Adulto');
    return { id: 'p' + n, nombre, tipo: TIPOS_PERFIL.includes(x.tipo) ? x.tipo : 'adulto', color: COLORES_PERFIL.includes(x.color) ? x.color : COLORES_PERFIL[(n - 1) % COLORES_PERFIL.length],
      inicial: x.inicial ? inicialDe(x.inicial) : inicialDe(nombre), avisar: x.avisar === true };
  }
  // Registro válido o null: { v, activo, lista: [perfil], pin: hash|null }.
  function normalizarRegistro(r) {
    if (!r || typeof r !== 'object' || !Array.isArray(r.lista)) return null;
    const lista = r.lista.filter(p => p && typeof p.id === 'string' && /^p\d+$/.test(p.id))
      .map(p => Object.assign(nuevoPerfil([], p), { id: p.id }));
    if (!lista.length) return null;
    return { v: 1, activo: lista.some(p => p.id === r.activo) ? r.activo : lista[0].id, lista, pin: typeof r.pin === 'string' && r.pin ? r.pin : null };
  }
  // Primer arranque con perfiles: los datos que ya hubiera pasan al primer perfil (adulto); nada se pierde.
  function migrarPerfiles(claves, registro) {
    const r = normalizarRegistro(registro);
    if (r) return { registro: r, mover: [], nuevo: false };
    const p = nuevoPerfil([], { nombre: 'Adulto', tipo: 'adulto', color: 'lapis' });
    return { registro: { v: 1, activo: p.id, lista: [p], pin: null }, mover: (claves || []).filter(esClaveLegada).map(k => [k, clavePerfil(p.id, k)]), nuevo: true };
  }
  const perfilDe = (r, id) => ((r && r.lista) || []).find(p => p.id === id) || null;
  // Pasar de un perfil niño a uno adulto pide el PIN (si hay PIN definido).
  const cambioPidePin = (r, desde, hacia) => { const a = perfilDe(r, desde), b = perfilDe(r, hacia); return !!(r && r.pin && b && b.tipo === 'adulto' && (!a || a.tipo === 'nino')); };
  const pinValido = s => /^\d{4}$/.test(String(s == null ? '' : s));

  /* ---- Contenido fuerte (datos/contenido.js): clasificación editorial del proyecto, no del texto bíblico ---- */
  const NIVEL_CONT = { medio: 1, alto: 2 };
  const cacheCont = new WeakMap();
  const marcasContenido = C => {
    if (!C || typeof C !== 'object') return [];
    if (!cacheCont.has(C)) cacheCont.set(C, (C.marcas || []).map(m => {
      const a = m && clave(m.desde), b = m && clave(m.hasta || m.desde);
      return a !== null && b !== null && NIVEL_CONT[m.nivel] ? Object.assign({}, m, { a: Math.min(a, b), b: Math.max(a, b) }) : null;
    }).filter(Boolean));
    return cacheCont.get(C);
  };
  // La marca más fuerte que cubre un versículo (ref o clave), o null.
  function marcaDe(C, ref) {
    const k = typeof ref === 'number' ? ref : clave(ref);
    if (k === null || k === undefined) return null;
    return marcasContenido(C).filter(m => k >= m.a && k <= m.b).sort((x, y) => NIVEL_CONT[y.nivel] - NIVEL_CONT[x.nivel] || x.a - y.a)[0] || null;
  }
  const esNino = perfil => !!perfil && perfil.tipo === 'nino';
  // Qué hacer con un versículo marcado: 'plegar' | 'nota' | 'aviso' | 'mostrar'.
  function decisionVerso(perfil, marca) {
    if (!marca || !NIVEL_CONT[marca.nivel]) return 'mostrar';
    if (esNino(perfil)) return marca.nivel === 'alto' ? 'plegar' : 'nota';
    if (perfil && perfil.avisar) return marca.nivel === 'alto' ? 'aviso' : 'nota';
    return 'mostrar';
  }
  const accionVerso = (C, perfil, ref) => { const marca = marcaDe(C, ref); return { accion: decisionVerso(perfil, marca), marca }; };
  const esAlto = (C, k) => { const m = marcaDe(C, k); return !!m && m.nivel === 'alto'; };
  const VISUALES = ['arte', 'reconstruccion', 'ilustracion', 'arqueologia', 'mapa_antiguo'];
  // Recurso visible para el perfil: el niño no ve imágenes `sensible` ni imágenes u objetos de una parte plegada
  // (dentro de `claves`, los versículos que se están viendo; sin claves, cualquier solape con una parte plegada).
  function recursoPermitido(f, perfil, C, claves) {
    if (!f) return false;
    if (!esNino(perfil)) return true;
    if (f.sensible) return false;
    if (f.tipo === 'video') return /proyecto biblia|bibleproject/i.test(`${f.institucion || ''} ${f.url_fuente || ''}`); // solo los de Proyecto Biblia
    if (!VISUALES.includes(f.tipo)) return true; // videos y audio: enlaces o fachadas; lo externo pide PIN aparte
    const rs = f.rangos || [];
    if (claves && claves.length) return !claves.some(k => rs.some(([a, b]) => k >= a && k <= b) && esAlto(C, k));
    return !rs.some(([a, b]) => marcasContenido(C).some(m => m.nivel === 'alto' && m.a <= b && a <= m.b));
  }
  // Curiosidad o «¿Sabías que…?» oculta al niño si alguna de sus refs cae en una parte plegada.
  const curiosidadPermitida = (c, perfil, C) => !esNino(perfil) || !((c && c.refs) || []).some(r => esAlto(C, clave(r)));
  // Enlaces externos que el niño puede abrir sin PIN: solo los videos de Proyecto Biblia.
  const enlaceLibre = u => /^https:\/\/(www\.)?bibleproject\.com\/es\//i.test(String(u || ''));
  // Agrupa versículos seguidos con la misma acción y la misma marca (para plegar un tramo de una vez).
  function tramosContenido(C, perfil, refs) {
    const out = [];
    (refs || []).forEach(ref => {
      const x = accionVerso(C, perfil, ref), u = out[out.length - 1];
      if (u && u.accion === x.accion && (x.accion === 'mostrar' || u.marca === x.marca)) u.refs.push(ref); else out.push({ accion: x.accion, marca: x.marca, refs: [ref] });
    });
    return out;
  }

  /* ---- Tabernáculo (datos/tabernaculo.js): medidas en codos con su cita, plano en codos y montaje de Éx 40 ---- */
  // Plano: origen en la esquina suroeste del atrio, x hacia el oriente, y hacia el norte (en codos).
  const TB_GRUPOS = ['atrio', 'estructura', 'cortinas', 'mobiliario'];
  const tbPiezas = T => ((T && T.piezas) || []).filter(p => p && p.id && p.nombre);
  const tbPieza = (T, id) => tbPiezas(T).find(p => p.id === id) || null;
  const tbZona = (T, id) => ((T && T.zonas) || []).find(z => z && z.id === id) || null;
  const tbCodos = x => x && x.codos !== null && x.codos !== undefined && x.codos !== '' && Number.isFinite(+x.codos) ? +x.codos : null;
  // Codo elegido (por id), si no el marcado por defecto, si no el primero.
  function tbCodo(T, id) {
    const cs = ((T && T.codos) || []).filter(c => c && c.id && Number.isFinite(+c.cm) && +c.cm > 0);
    return cs.find(c => c.id === id) || cs.find(c => c.defecto) || cs[0] || null;
  }
  // Codos → metros (Cálculo), redondeado al centímetro.
  const codosAMetros = (codos, cm) => codos === null || codos === undefined || codos === '' || !Number.isFinite(+codos) || !Number.isFinite(+cm) ? null : Math.round(+codos * +cm) / 100;
  // «Ex 25:10-22» o «Ex 25:10-22; Ex 37:1-9» → rangos de claves.
  const rangosDe = s => String(s || '').split(/\s*;\s*/).map(rangoClaves).filter(Boolean);
  const cruza = (rs, a, b) => rs.some(r => r.a <= b && a <= r.b);
  const rangoPasaje = p => p && p.inicio ? rangoClaves(`${p.inicio}-${p.fin || p.inicio}`) : null;
  // Pasos del montaje en su orden (solo los que nombran una pieza que existe).
  function tbMontaje(T) {
    const ids = new Set(tbPiezas(T).map(p => p.id));
    return ((T && T.montaje) || []).filter(m => m && ids.has(m.pieza)).map((m, i) => ({ m, i, o: Number.isFinite(+m.orden) && m.orden !== null ? +m.orden : i }))
      .sort((x, y) => x.o - y.o || x.i - y.i).map(x => x.m);
  }
  // Piezas ya colocadas tras los n primeros pasos, sin repetir.
  const tbColocadas = (T, n) => [...new Set(tbMontaje(T).slice(0, Math.max(0, n)).map(m => m.pieza))];
  // Piezas cuya instrucción o construcción (o su paso del montaje) cae en el rango de claves [a, b].
  function tbPiezasDeRango(T, a, b) {
    if (!Number.isFinite(a) || !Number.isFinite(b)) return [];
    const mont = new Set(tbMontaje(T).filter(m => { const k = clave(m.ref); return k !== null && k >= a && k <= b; }).map(m => m.pieza));
    return tbPiezas(T).filter(p => mont.has(p.id) || cruza(rangosDe(p.instruccion), a, b) || cruza(rangosDe(p.construccion), a, b));
  }
  const tbPiezasDePasaje = (T, p) => { const r = rangoPasaje(p); return r ? tbPiezasDeRango(T, r.a, r.b) : []; };
  const tbPiezasDeRefs = (T, refs) => { const e = extremos(refs); return e ? tbPiezasDeRango(T, e.a, e.b) : []; };
  // Éx 25–31 (instrucciones) y 35–40 (construcción y montaje): donde el acompañante ofrece «En el tabernáculo».
  const tbCapitulo = ref => { const r = parseRef(ref); return !!r && libroCanon(r.libro) === 'Ex' && ((r.cap >= 25 && r.cap <= 31) || (r.cap >= 35 && r.cap <= 40)); };
  const tbEnPasaje = p => !!p && [p.inicio, p.fin].some(tbCapitulo);
  // «Según voy leyendo»: piezas cuyos pasajes de instrucción están TODOS marcados como leídos (y hay al menos uno).
  function tbVisiblesLeido(T, pasajes, leidos) {
    const L = new Set(leidos || []), ps = (pasajes || []).map(p => ({ id: p.id, r: rangoPasaje(p) })).filter(x => x.r);
    return tbPiezas(T).filter(p => {
      const ri = rangosDe(p.instruccion); if (!ri.length) return false;
      const toca = ps.filter(x => cruza(ri, x.r.a, x.r.b));
      return toca.length > 0 && toca.every(x => L.has(x.id));
    }).map(p => p.id);
  }
  // Huella de una pieza en el plano: rectángulo (largo a lo largo de x si rot = 0), línea (sin ancho) o punto (sin medidas).
  function tbHuella(p) {
    const pl = p && p.plano; if (!pl || !Number.isFinite(+pl.x) || !Number.isFinite(+pl.y) || pl.x === null || pl.y === null) return null;
    const m = p.medidas || {}, l = tbCodos(m.largo), an = tbCodos(m.ancho), alto = tbCodos(m.alto), x = +pl.x, y = +pl.y;
    // Piezas que forman un contorno (tablas, cortinas, cortinas del atrio): su rectángulo `plano.rect`.
    const rc = tbRect(pl.rect);
    if (rc) return { x, y, contorno: true, rect: rc, alto, esquinas: [[rc.x0, rc.y0], [rc.x1, rc.y0], [rc.x1, rc.y1], [rc.x0, rc.y1]] };
    if (l === null && an === null) return { x, y, punto: true, alto: null, esquinas: [[x, y], [x, y], [x, y], [x, y]] };
    const L = l !== null ? l : an, A = an !== null ? an : 0, t = (+pl.rot || 0) * Math.PI / 180, c = Math.cos(t), s = Math.sin(t);
    const esquinas = [[-L / 2, -A / 2], [L / 2, -A / 2], [L / 2, A / 2], [-L / 2, A / 2]].map(([u, v]) => [x + u * c - v * s, y + u * s + v * c].map(n => Math.round(n * 1e6) / 1e6));
    return { x, y, punto: false, linea: an === null || l === null, alto, esquinas };
  }
  // Rectángulos de las zonas. El atrio va en el origen (dato del contrato). Santo y santísimo: con `plano` (centro) si lo traen;
  // si no, el santísimo se centra en sus piezas (Inferido) y el santo va pegado al oriente (el velo los separa, Ex 26:33);
  // sin piezas, la disposición habitual de las reconstrucciones (Tradición).
  const tbRect = r => r && ['x0', 'y0', 'x1', 'y1'].every(k => r[k] !== null && r[k] !== undefined && r[k] !== '' && Number.isFinite(+r[k])) ? { x0: Math.min(+r.x0, +r.x1), y0: Math.min(+r.y0, +r.y1), x1: Math.max(+r.x0, +r.x1), y1: Math.max(+r.y0, +r.y1) } : null;
  function tbDisposicion(T) {
    // Zonas que traen su rectángulo en `plano` (x0, y0, x1, y1): se usan tal cual, con su certeza.
    const zs = ((T && T.zonas) || []).filter(z => z && z.id);
    if (zs.length && zs.every(z => tbRect(z.plano))) return zs.map(z => Object.assign({ id: z.id, nombre: z.nombre || z.id, alto: tbCodos(z.alto), certeza: z.plano.certeza || 'inferido', origen: 'datos', nota: z.plano.nota || '' }, tbRect(z.plano)));
    const out = [], at = tbZona(T, 'atrio');
    const AL = tbCodos(at && at.largo), AA = tbCodos(at && at.ancho);
    if (at && AL !== null && AA !== null) out.push({ id: 'atrio', nombre: at.nombre || 'Atrio', x0: 0, y0: 0, x1: AL, y1: AA, alto: tbCodos(at.alto), certeza: 'texto', origen: 'contrato' });
    const sm = tbZona(T, 'santisimo'), sa = tbZona(T, 'santo');
    const dim = z => z && tbCodos(z.largo) !== null && tbCodos(z.ancho) !== null ? { L: tbCodos(z.largo), A: tbCodos(z.ancho) } : null;
    const dSm = dim(sm), dSa = dim(sa);
    const centroDe = id => {
      const ps = tbPiezas(T).filter(p => p.zona && p.zona.id === id && p.grupo === 'mobiliario' && tbHuella(p));
      if (!ps.length) return null;
      const peor = ps.some(p => (p.plano || {}).certeza === 'tradicion') ? 'tradicion' : 'inferido';
      return { x: ps.reduce((s, p) => s + +p.plano.x, 0) / ps.length, y: ps.reduce((s, p) => s + +p.plano.y, 0) / ps.length, certeza: peor, origen: 'piezas' };
    };
    const conPlano = z => z && z.plano && Number.isFinite(+z.plano.x) && Number.isFinite(+z.plano.y) ? { x: +z.plano.x, y: +z.plano.y, certeza: z.plano.certeza || 'inferido', origen: 'datos', nota: z.plano.nota } : null;
    const rect = (z, d, c) => ({ id: z.id, nombre: z.nombre || z.id, x0: c.x - d.L / 2, y0: c.y - d.A / 2, x1: c.x + d.L / 2, y1: c.y + d.A / 2, alto: tbCodos(z.alto), certeza: c.certeza, origen: c.origen, nota: c.nota || '' });
    let cSm = dSm && (conPlano(sm) || centroDe('santisimo')), cSa = dSa && conPlano(sa);
    if (dSm && !cSm && AL !== null && AA !== null) cSm = { x: AL / 4, y: AA / 2, certeza: 'tradicion', origen: 'habitual' };
    if (dSa && !cSa && cSm && dSm) cSa = { x: cSm.x + dSm.L / 2 + dSa.L / 2, y: cSm.y, certeza: cSm.certeza, origen: cSm.origen === 'datos' ? 'contiguo' : cSm.origen };
    if (dSa && !cSa) cSa = centroDe('santo') || (AL !== null && AA !== null ? { x: AL / 4 + 10, y: AA / 2, certeza: 'tradicion', origen: 'habitual' } : null);
    if (dSm && cSm) out.push(rect(sm, dSm, cSm));
    if (dSa && cSa) out.push(rect(sa, dSa, cSa));
    return out;
  }
  // Reconstrucciones y arte (datos/recursos.js) que tocan la instrucción o la construcción de la pieza.
  function tbRecursos(R, p) {
    const rs = rangosDe(p && p.instruccion).concat(rangosDe(p && p.construccion));
    if (!rs.length) return [];
    return recursos(R).filter(f => (f.tipo === 'reconstruccion' || f.tipo === 'arte') && f.rangos.some(([a, b]) => cruza(rs, a, b)));
  }

  /* ---- Notas y subrayados del lector (por perfil, en biblia.p.<id>.notas). Son del usuario, no datos de la app. ---- */
  const NOTAS_COLORES = ['amarillo', 'verde', 'azul', 'rosa'];
  const NOTA_MAX = 4000;
  // «Ex 3:14», «éx 3:14», «Éxodo 3:14» → «Ex 3:14»; cualquier otra cosa → null (sin el «Génesis por defecto» de parseRef).
  function refNota(ref) {
    const m = /^\s*([1-3]?\s?[A-Za-zÀ-ÿ]+)\.?\s+(\d{1,3})\s*:\s*(\d{1,3})\s*$/.exec(String(ref == null ? '' : ref));
    if (!m) return null;
    const k = norm(m[1]).replace(/\s+/g, '');
    if (!idCanon.has(k) || !ordLibro.has(norm(idCanon.get(k)))) return null;
    const cap = +m[2], v = +m[3];
    return cap > 0 && v > 0 ? refTxt(cap, v, idCanon.get(k)) : null;
  }
  // Una entrada válida o null: color conocido y/o nota con texto; `t` (ISO) se conserva si es una fecha.
  function entradaNota(e) {
    if (!e || typeof e !== 'object') return null;
    const color = NOTAS_COLORES.includes(e.color) ? e.color : null;
    const nota = typeof e.nota === 'string' ? e.nota.replace(/\r\n?/g, '\n').trim().slice(0, NOTA_MAX) : '';
    if (!color && !nota) return null;
    const out = {}; if (color) out.color = color; if (nota) out.nota = nota;
    out.t = typeof e.t === 'string' && !isNaN(Date.parse(e.t)) ? e.t : '';
    return out;
  }
  // Objeto guardado → { v: 1, versos: { ref: entrada } } limpio (refs canónicas, entradas vacías fuera).
  function normalizarNotas(o) {
    const versos = {};
    const src = o && typeof o === 'object' && o.versos && typeof o.versos === 'object' && !Array.isArray(o.versos) ? o.versos : {};
    Object.keys(src).forEach(r => { const ref = refNota(r), e = entradaNota(src[r]); if (ref && e && (!versos[ref] || (e.t || '') > (versos[ref].t || ''))) versos[ref] = e; });
    return { v: 1, versos };
  }
  // Pone o quita color/nota de un versículo (cambios: { color?, nota? }, null o '' quita). Sin color ni nota, el versículo sale.
  function ponerNota(o, ref, cambios, t) {
    const N0 = normalizarNotas(o), r = refNota(ref);
    if (!r) return N0;
    const prev = N0.versos[r] || {}, c = cambios || {};
    const e = entradaNota({ color: 'color' in c ? c.color : prev.color, nota: 'nota' in c ? c.nota : prev.nota, t: t || new Date().toISOString() });
    if (e) N0.versos[r] = e; else delete N0.versos[r];
    return N0;
  }
  const quitarNota = (o, ref) => { const N0 = normalizarNotas(o), r = refNota(ref); if (r) delete N0.versos[r]; return N0; };
  const notaDe = (o, ref) => { const r = refNota(ref); return (r && normalizarNotas(o).versos[r]) || null; };
  // Lista en orden canónico (libro, capítulo, versículo). Filtros: { color, conNota, q } (q busca en el texto de las notas).
  function listarNotas(o, f) {
    const F = f || {}, q = norm(F.q || '');
    return Object.entries(normalizarNotas(o).versos).map(([ref, e]) => Object.assign({ ref, clave: clave(ref) }, e))
      .filter(x => (!F.color || x.color === F.color) && (!F.conNota || !!x.nota) && (!q || norm(x.nota || '').includes(q)))
      .sort((a, b) => a.clave - b.clave);
  }
  // Fusión de una importación: por versículo gana la entrada más reciente (`t`); empate o sin fecha, se queda la actual.
  function fusionarNotas(actual, entrante) {
    const A = normalizarNotas(actual), B = normalizarNotas(entrante);
    let anadidos = 0, actualizados = 0, iguales = 0;
    Object.entries(B.versos).forEach(([ref, e]) => {
      const a = A.versos[ref];
      if (!a) { A.versos[ref] = e; anadidos++; return; }
      if ((e.t || '') > (a.t || '') && (e.color !== a.color || e.nota !== a.nota)) { A.versos[ref] = e; actualizados++; } else iguales++;
    });
    return { notas: A, anadidos, actualizados, iguales };
  }
  // Texto de un archivo importado → { ok, notas, total, descartados } o { ok: false, error } (mensaje para la persona).
  function validarNotas(texto) {
    let o;
    try { o = JSON.parse(String(texto == null ? '' : texto).replace(/^﻿/, '')); } catch (e) { return { ok: false, error: 'El archivo no es JSON válido.' }; }
    if (!o || typeof o !== 'object' || Array.isArray(o)) return { ok: false, error: 'El archivo no tiene el formato de notas de esta app.' };
    if (o.app !== undefined && o.app !== 'biblia-notas') return { ok: false, error: 'El archivo es de otra aplicación.' };
    if (o.v !== 1) return { ok: false, error: 'Versión de archivo desconocida (se esperaba v: 1).' };
    if (!o.versos || typeof o.versos !== 'object' || Array.isArray(o.versos)) return { ok: false, error: 'El archivo no trae la lista «versos».' };
    const notas = normalizarNotas(o), total = Object.keys(notas.versos).length, descartados = Object.keys(o.versos).length - total;
    if (!total && descartados) return { ok: false, error: 'Ninguna entrada del archivo es válida (referencia, color o nota).' };
    return { ok: true, notas, total, descartados: Math.max(0, descartados) };
  }
  // Archivo de exportación (lo que validarNotas acepta de vuelta).
  const exportarNotas = (o, extra) => Object.assign({ app: 'biblia-notas', v: 1 }, extra || {}, { versos: normalizarNotas(o).versos });
  // «Éxodo 3:14 (RV 1909)» y la cita completa con el texto.
  const refLegible = (d, ref, sigla) => { const r = refNota(ref); if (!r) return ''; const p = parseRef(r); return `${nombreLibro(d, p.libro)} ${p.cap}:${p.v}${sigla === '' ? '' : ` (${sigla || 'RV 1909'})`}`; };
  const citaVerso = (d, ref, texto, sigla) => { const t = String(texto || '').trim(), r = refLegible(d, ref, sigla); return t ? `«${t}» ${r}` : r; };
  const textoVerso = (d, ref) => { const k = clave(refNota(ref)); const v = k === null ? null : todosLosVersiculos(d).find(x => x.clave === k); return v ? v.texto : ''; };
  // Toda la lista como texto plano (para copiar): referencia, color, texto del versículo y «Tu nota».
  const textoNotas = (d, lista, sigla) => (lista || []).map(x => [
    `${refLegible(d, x.ref, sigla)}${x.color ? ` · subrayado ${x.color}` : ''}`,
    textoVerso(d, x.ref) ? `«${textoVerso(d, x.ref)}»` : '',
    x.nota ? `Tu nota: ${x.nota}` : ''].filter(Boolean).join('\n')).join('\n\n');

  /* ---- Lectura en orden: lo accesible y el tiempo mínimo de lectura ----
     Frontera = primer pasaje sin leer (en el orden de `pasajes`). Accesible = lo leído (aunque se marcara fuera
     de orden) más todo hasta la frontera incluida. Lo demás no se muestra en ninguna vista. */
  const conjunto = x => x instanceof Set ? x : new Set(x || []);
  const frontera = (d, leidos) => { const L = conjunto(leidos); return pasajes(d).find(p => !L.has(p.id)) || null; };
  // Último versículo de cada capítulo («Ex|7» → clave), para las refs de capítulo entero («Gn 5»).
  const finCapitulo = d => memo(d || {}, 'finCap', () => {
    const m = new Map(); todosLosVersiculos(d).forEach(v => m.set(v.libro + '|' + v.cap, v.clave)); return m;
  });
  // Objeto de acceso: { frontera, todo, ids, rangos, pasaje(id), clave(k), ref(ref), refs(refs) }.
  function accesibles(d, leidos) {
    const L = conjunto(leidos), ps = pasajes(d), f = ps.findIndex(p => !L.has(p.id));
    const ids = new Set(), rangos = [];
    ps.forEach((p, i) => {
      if (f >= 0 && i > f && !L.has(p.id)) return;
      ids.add(p.id);
      const a = clave(p.inicio), b = clave(p.fin), u = rangos[rangos.length - 1];
      if (u && u.i === i - 1) { u.b = Math.max(u.b, b); u.i = i; } else rangos.push({ a, b, i });
    });
    const todo = f < 0, fc = finCapitulo(d);
    const enClave = k => k !== null && k !== undefined && Number.isFinite(k) && (todo || rangos.some(r => k >= r.a && k <= r.b));
    // Una ref es accesible si lo son su principio y su final (rango «Ex 25:10-22», capítulo «Gn 5» o versículo).
    const ref = r => {
      if (todo) return true;
      if (r === null || r === undefined || r === '') return false;
      const s = String(r);
      if (/[-–—]/.test(s)) { const x = rangoClaves(s); if (!x) return false; const fin = x.b % 1000 === 999 ? fc.get(refDeClave(x.b).replace(/:\d+$/, '').replace(' ', '|')) || x.b : x.b; return enClave(x.a) && enClave(fin); }
      const p = parseRef(s); if (!p) return false;
      if (p.v) return enClave(clave(s));
      const k = fc.get(p.libro + '|' + p.cap); return enClave(ordDe(p.libro) * 1e6 + p.cap * 1000 + 1) && enClave(k);
    };
    return { frontera: todo ? null : ps[f], todo, ids, rangos: rangos.map(r => ({ a: r.a, b: r.b })),
      pasaje: id => ids.has(id), clave: enClave, ref, refs: rs => (rs || []).every(ref) };
  }
  const acc = (d, A) => A && typeof A.ref === 'function' ? A : accesibles(d, A); // acepta el objeto o la lista de leídos
  const esAccesible = (d, leidos, pasajeId) => acc(d, leidos).pasaje(pasajeId);
  // Adónde lleva un enlace a un pasaje: él mismo si es accesible; si no, la frontera (con `bloqueado`).
  function destinoPasaje(d, leidos, pasajeId) {
    const A = acc(d, leidos), p = pasajes(d).find(x => x.id === pasajeId) || null;
    if (!p || A.pasaje(p.id)) return { pasaje: p, bloqueado: false };
    return { pasaje: A.frontera || p, bloqueado: true, pedido: p };
  }
  // Palabras del texto RV que se muestra del pasaje; `omitir(ref)` quita versículos (p. ej. plegados en perfil niño).
  const contarPalabras = s => (String(s || '').match(/[\p{L}\p{N}]+(?:['’-][\p{L}\p{N}]+)*/gu) || []).length;
  const palabrasPasaje = (d, p, omitir) => versiculosDe(d, p).filter(v => !(omitir && omitir(v.ref))).reduce((s, v) => s + contarPalabras(v.texto), 0);
  const PPM = { adulto: 250, nino: 150 };
  const ppmDe = perfil => esNino(perfil) ? PPM.nino : PPM.adulto;
  // Segundos mínimos con el pasaje abierto antes de poder marcarlo: palabras ÷ ppm (redondeado al segundo, hacia arriba).
  const segundosMinimos = (palabras, perfil) => Math.ceil(Math.max(0, +palabras || 0) / ppmDe(perfil) * 60);
  // Cuenta atrás legible: 83 → «1:23».
  const relojTxt = s => { s = Math.max(0, Math.ceil(+s || 0)); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`; };
  // Tiempos acumulados por pasaje ({ id: segundos }) saneados.
  const normalizarTiempos = o => { const out = {}; if (o && typeof o === 'object' && !Array.isArray(o)) Object.keys(o).forEach(k => { const v = +o[k]; if (Number.isFinite(v) && v > 0) out[k] = Math.min(v, 864000); }); return out; };
  // Puede marcarse: ya leído (releer no pide tiempo) o acumuló el mínimo.
  const puedeMarcar = (yaLeido, acumulado, minimo) => !!yaLeido || (+acumulado || 0) >= (+minimo || 0);
  // Filtros reutilizables por las vistas (A = objeto de `accesibles`).
  // Persona accesible: aparece en algún versículo accesible (también en lo leído fuera de orden).
  const clavesPersona = d => memo(d || {}, 'clavesP', () => {
    const m = new Map(); for (const [k, ids] of indice(d).porRef) ids.forEach(id => { if (!m.has(id)) m.set(id, []); m.get(id).push(k); });
    m.forEach(ks => ks.sort((a, b) => a - b)); return m;
  });
  const personaAccesible = (d, A, id) => (clavesPersona(d).get(id) || []).some(A.clave);
  const refsLugar = (d, id) => memo(d || {}, 'refsL|' + id, () => {
    const l = lugar(d, id), out = [].concat((l && l.refs) || []);
    for (const [k, ms] of indice(d).mencionesLugar) if (ms.some(m => m.lugar === id)) out.push(refDeClave(k));
    return out;
  });
  const lugarAccesible = (d, A, id) => refsLugar(d, id).some(A.ref);
  const buscarAccesible = (d, A, q, max) => buscar(d, q, 1e6).filter(p => personaAccesible(d, A, p.id)).slice(0, max || 20);
  const lugaresAccesibles = (d, A, ids) => (ids || ((d && d.lugares) || []).map(l => l.id)).filter(id => lugarAccesible(d, A, id));
  const curiosidadAccesible = (A, c) => !!c && A.refs(c.refs || []) && (c.refs || []).length > 0;
  const edadAccesible = (A, e) => !!e && A.ref(e.ref) && (e.de || []).every(x => A.ref(x.ref));
  // Línea de tiempo con solo los sucesos e hitos cuya ref es accesible (las secciones vacías desaparecen).
  const lineaAccesible = (d, combo, A) => lineaDeTiempo(d, combo).map(g => Object.assign({}, g, {
    items: g.items.filter(it => A.ref(it.evento.ref)), hitos: g.hitos.filter(h => A.ref(h.hito.ref)) })).filter(g => g.items.length || g.hitos.length);
  // Vida (cálculo) vista desde lo accesible: sin nacimiento accesible no se muestra; sin muerte accesible, queda abierta.
  function vidaAccesible(d, x, A) {
    const C = crono(d); if (!x || !C) return null;
    const ok = id => { const e = id && C.porId.get(id); return !!e && A.ref(e.ref); };
    if (!ok(x.evNac) || !personaAccesible(d, A, x.persona)) return null;
    return ok(x.evMuerte) ? x : Object.assign({}, x, { muerte: null, evMuerte: null });
  }

  /* ---- Explicaciones (datos/explicaciones.js, herramientas/explicaciones.py): términos y pasajes difíciles ----
     E = { terminos: {id: {tipo, lema, formas, adulto, nino, certeza, fuentes, calculo?}}, ocurrencias: {"Ex 30:13": [{t, i, f}]},
     pasajes: {id: {refs, titulo, dice, posturas, nino, certeza}} }; i y f son offsets UTF-16 como los de `menciones`. */
  const explicacionesValidas = E => !!E && typeof E === 'object' && !!E.terminos && typeof E.terminos === 'object' && !!E.ocurrencias && typeof E.ocurrencias === 'object';
  const termino = (E, id) => explicacionesValidas(E) && Object.prototype.hasOwnProperty.call(E.terminos, id) ? E.terminos[id] : null;
  const cacheExpl = new WeakMap();
  // Índice: clave de versículo → ocurrencias válidas; término → claves donde aparece (ordenadas).
  function indiceExpl(E) {
    if (!cacheExpl.has(E)) {
      const porClave = new Map(), claves = new Map();
      Object.keys(E.ocurrencias).forEach(ref => {
        const k = clave(ref); if (k === null) return;
        const xs = (Array.isArray(E.ocurrencias[ref]) ? E.ocurrencias[ref] : []).filter(o => o && termino(E, o.t) && Number.isInteger(o.i) && Number.isInteger(o.f) && o.f > o.i);
        if (!xs.length) return;
        porClave.set(k, xs);
        xs.forEach(o => { if (!claves.has(o.t)) claves.set(o.t, []); claves.get(o.t).push(k); });
      });
      claves.forEach(ks => ks.sort((a, b) => a - b));
      cacheExpl.set(E, { porClave, claves });
    }
    return cacheExpl.get(E);
  }
  const ocurrenciasDe = (E, ref) => explicacionesValidas(E) ? (indiceExpl(E).porClave.get(clave(ref)) || []).map(o => ({ termino: o.t, inicio: o.i, fin: o.f })) : [];
  // Términos a subrayar en un pasaje: la primera aparición de cada término, contada después de quitar las que pierden
  // ante una persona o un lugar. `omitir(ref)` salta versículos que no se ven (plegados para el niño). → Map ref → [{termino, inicio, fin}]
  function marcadoPasaje(d, E, vs, omitir) {
    const out = new Map(), vistos = new Set();
    if (!explicacionesValidas(E)) return out;
    for (const v of (vs || [])) {
      if (!v || !v.texto || (omitir && omitir(v.ref))) continue;
      const ts = ocurrenciasDe(E, v.ref); if (!ts.length) continue;
      const ok = terminosVerso(mencionesVerso(d, v.ref, v.texto), ts, v.texto.length).filter(t => { if (vistos.has(t.termino)) return false; vistos.add(t.termino); return true; });
      if (ok.length) out.set(v.ref, ok);
    }
    return out;
  }
  // Interruptor por perfil: sin valor guardado cuenta como encendido.
  const explicacionesActivas = guardado => guardado !== false;
  // Texto de la explicación según el perfil: el del niño en perfil niño.
  const textoTermino = (t, perfil) => !t ? '' : String((esNino(perfil) ? t.nino : t.adulto) || t.adulto || '');
  // Un término es accesible si aparece en algún versículo accesible (lectura en orden); `omitir(ref)` descarta versículos.
  const clavesTermino = (E, id, A, omitir) => explicacionesValidas(E) ? (indiceExpl(E).claves.get(id) || []).filter(k => A.clave(k) && !(omitir && omitir(refDeClave(k)))) : [];
  const terminoAccesible = (E, A, id, omitir) => clavesTermino(E, id, A, omitir).length > 0;
  // Glosario: términos accesibles, filtrados por texto (lema o formas, sin acentos) y ordenados por lema.
  function glosario(E, A, q, omitir) {
    if (!explicacionesValidas(E)) return [];
    const nq = norm(q);
    return Object.keys(E.terminos).map(id => ({ id, termino: E.terminos[id], ks: clavesTermino(E, id, A, omitir) })).filter(x => x.ks.length)
      .filter(x => !nq || [x.termino.lema].concat(x.termino.formas || []).some(s => norm(s).includes(nq)))
      .map(x => ({ id: x.id, termino: x.termino, primera: refDeClave(x.ks[0]) }))
      .sort((a, b) => norm(a.termino.lema).localeCompare(norm(b.termino.lema), 'es'));
  }
  // Rango con alguna parte que el perfil niño pliega (contenido alto).
  const rangoPlegado = (C, perfil, ref) => { if (!esNino(perfil)) return false; const r = rangoClaves(ref); return !!r && marcasContenido(C).some(m => m.nivel === 'alto' && m.a <= r.b && r.a <= m.b); };
  // Fuente bíblica vista desde la lectura en orden: sin texto si su ref aún no es accesible («se verá al llegar»)
  // o si `plegada(ref)` (parte plegada para el niño).
  function citaFuente(A, f, plegada) {
    if (!f || f.tipo !== 'biblia') return null;
    const ok = !!A && A.ref(f.ref);
    return { ref: f.ref, cita: ok && f.cita && !(plegada && plegada(f.ref)) ? f.cita : null, bloqueada: !ok };
  }
  // Pasajes difíciles que tocan un pasaje de lectura: solo con todo su rango accesible; al niño, solo con texto `nino`
  // y sin partes plegadas.
  function dificilesDe(E, p, A, perfil, C) {
    if (!explicacionesValidas(E) || !p || !E.pasajes || typeof E.pasajes !== 'object') return [];
    const a = clave(p.inicio), b = clave(p.fin);
    return Object.keys(E.pasajes).map(id => Object.assign({ id }, E.pasajes[id])).filter(x => {
      const r = rangoClaves(x.refs); if (!r || r.b < a || r.a > b || !A.ref(x.refs)) return false;
      return !esNino(perfil) || (!!x.nino && !rangoPlegado(C, perfil, x.refs));
    });
  }

  return { explicacionesValidas, termino, ocurrenciasDe, marcadoPasaje, explicacionesActivas, textoTermino, terminoAccesible, glosario, rangoPlegado, citaFuente, dificilesDe,
    frontera, accesibles, esAccesible, destinoPasaje, contarPalabras, palabrasPasaje, PPM, ppmDe, segundosMinimos, relojTxt, normalizarTiempos, puedeMarcar,
    personaAccesible, refsLugar, lugarAccesible, buscarAccesible, lugaresAccesibles, curiosidadAccesible, edadAccesible, lineaAccesible, vidaAccesible,
    NOTAS_COLORES, refNota, normalizarNotas, ponerNota, quitarNota, notaDe, listarNotas, fusionarNotas, validarNotas, exportarNotas, refLegible, citaVerso, textoVerso, textoNotas,
    TB_GRUPOS, tbPiezas, tbPieza, tbZona, tbCodos, tbRect, tbCodo, codosAMetros, rangosDe, tbMontaje, tbColocadas, tbPiezasDeRango, tbPiezasDePasaje, tbPiezasDeRefs,
    tbCapitulo, tbEnPasaje, tbVisiblesLeido, tbHuella, tbDisposicion, tbRecursos,
    CLAVE_PERFILES, COLORES_PERFIL, clavePerfil, esClaveLegada, clavesDePerfil, nuevoPerfil, normalizarRegistro, migrarPerfiles, perfilDe, cambioPidePin, pinValido, inicialDe,
    marcasContenido, marcaDe, decisionVerso, accionVerso, recursoPermitido, curiosidadPermitida, enlaceLibre, tramosContenido,
    listaRecorridos, recorrido, etapasOrdenadas, hipotesisDefecto, ubicacionEtapa, sinPropuesta, etapasDeRefs, etapaActiva, recorridosDeRefs, distanciaKm, tramosRecorrido, duracionTramo, pausaEtapa,
    recursos, recursoValido, recursosDe, imagenesDe, relacionadosDe, mapasAntiguos, rotuloRecurso,
    TRADS, TIPOS, norm, rangoClaves, testigosDe, tramoRefs, nombreFolio, foliosDePasaje, rollosDePasaje, vaticanoDeLibro, variantesDe, numeracionHebrea, notaGriegoLegible, alinearOriginales, sinTextoDe, sinTextoOriginal, videosDeLibro, esIdYoutube, escritura, textoParaVoz, vozPara, crono, elecciones, combinacion, anioEvento, cadenaEvento, vidasCrono, vivosEn, eventosDeRefs, eventosDePasaje,
    coleccionables, rareza, RAREZAS, personasDePasaje, coleccion, nuevasAlLeer, fichasColeccion, pasajesDePersona,
    GRUPOS_JUEGO, juegoValido, estadoPersonaje, vistaFichaJuego, estadoCosa, fichasCosas, nuevosAlLeer, genealogiasDe, esGenealogia, datoPlegado, relacionadosJuego, capituloListo, rangosAp, lugaresDePersona, descendientes,
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
  let JG = window.BIBLIA_JUEGO || null; // catálogo de juego (herramientas/juego.py); sin él, la colección es solo de personajes
  const JUEGO = () => N.juegoValido(JG) ? JG : null;
  const $ = s => document.querySelector(s);
  const main = $('#principal');
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  /* ---------- Perfiles locales: cada perfil guarda su progreso, colección y preferencias aparte ---------- */
  const LS = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); return true; } catch (e) { return false; } },
    del(k) { try { localStorage.removeItem(k); } catch (e) { /* nada */ } },
    claves() { try { return Object.keys(localStorage); } catch (e) { return []; } }
  };
  const leerJSON = k => { const v = LS.get(k); if (v == null) return null; try { return JSON.parse(v); } catch (e) { return null; } };
  const PERF = (() => {
    const m = N.migrarPerfiles(LS.claves(), leerJSON(N.CLAVE_PERFILES));
    let nuevo = false;
    if (m.nuevo) {
      m.mover.forEach(([de, a]) => { const v = LS.get(de); if (v != null && LS.set(a, v)) LS.del(de); });
      nuevo = LS.set(N.CLAVE_PERFILES, JSON.stringify(m.registro)); // sin almacenamiento no se insiste en la bienvenida
    }
    return { r: m.registro, nuevo };
  })();
  const guardarPerfiles = () => LS.set(N.CLAVE_PERFILES, JSON.stringify(PERF.r));
  const perfil = () => N.perfilDe(PERF.r, PERF.r.activo) || PERF.r.lista[0];
  const esNinoActivo = () => perfil().tipo === 'nino';
  const store = {
    get(k, def) { const v = LS.get(N.clavePerfil(PERF.r.activo, k)); if (v == null) return def; try { return JSON.parse(v); } catch (e) { return def; } },
    set(k, v) { LS.set(N.clavePerfil(PERF.r.activo, k), JSON.stringify(v)); }
  };
  /* ---------- Contenido fuerte (datos/contenido.js; con ?ejemplo, pruebas/contenido-ejemplo.js) ---------- */
  const CONT = () => window.BIBLIA_CONTENIDO || null;
  const ROTULO_CONT = 'Clasificación editorial del proyecto, no del texto bíblico.';
  const desplegados = new Set(); // tramos mostrados con el PIN en esta sesión (por su «desde»)
  function accionDe(ref) {
    const x = N.accionVerso(CONT(), perfil(), ref);
    return x.accion === 'plegar' && desplegados.has(x.marca.desde) ? { accion: 'desplegado', marca: x.marca } : x;
  }
  const plegadoRef = ref => !!ref && accionDe(ref).accion === 'plegar';
  /* ---------- Explicaciones (datos/explicaciones.js): términos subrayados, tarjeta, pasajes difíciles y glosario ---------- */
  const EXPL = () => N.explicacionesValidas(window.BIBLIA_EXPLICACIONES) ? window.BIBLIA_EXPLICACIONES : null;
  const explOn = () => N.explicacionesActivas(store.get('biblia.explicaciones', null)); // clave biblia.p.<id>.explicaciones
  const NOTA_CONT = { violencia: 'Aquí se narra un hecho violento.', crueldad: 'Aquí se narra un hecho cruel.', sexual: 'Aquí se alude a un tema de personas adultas.' };
  const CAT_CONT = { violencia: 'violencia', crueldad: 'crueldad', sexual: 'contenido sexual' };
  // Recurso accesible (lectura en orden): todos sus rangos de versículos ya se pueden leer (un video de «Gn 1-11», al llegar a Gn 11).
  const rangosRec = f => Array.isArray(f.rangos) && f.rangos.length ? f.rangos.filter(r => Array.isArray(r) && r.length === 2) : null;
  const recOk = f => { const A = ACC(); if (A.todo) return true; const rs = rangosRec(f); return rs ? rs.every(([a, b]) => A.clave(a) && A.clave(b)) : (f.refs || []).length > 0 && f.refs.every(A.ref); };
  const permitidos = (fs, claves) => (fs || []).filter(f => N.recursoPermitido(f, perfil(), CONT(), claves) && recOk(f));
  const TIPO_TXT = { al_engendrar: 'Al engendrar', restantes: 'Años restantes', total: 'Total' };
  const CERT_TXT = { texto: 'Texto', inferido: 'Inferido', calculo: 'Cálculo' };
  const CERT_DESC = { texto: 'Lo dice el texto', inferido: 'Supuesto: no lo dice el texto de forma explícita', calculo: 'Cálculo hecho a partir del texto' };
  const estado = { trad: store.get('biblia.trad', 'TM'), lineaSolo: false, mujeres: false, hoja: false, pasaje: null, activo: null, foco: null, focoHash: undefined, aviso: '',
    mapaFiltro: '', mapaConf: new Set(['alta', 'media', 'baja']), mapaQ: '', mapaSel: null, abiertos: null, q: '', secAbiertas: new Map(),
    vistaArbol: store.get('biblia.vistaArbol', 'lista') === 'grafico' ? 'grafico' : 'lista', gaZoom: 1, colLibro: '', colSexo: '', colGrupo: 'personajes', colEstado: '',
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
  const citaHTML = r => r && r.cita && !plegadoRef(r.ref) ? `<blockquote>${esc(r.cita)}</blockquote>` : '';
  const fuenteNombre = id => { const f = (D.fuentes || []).find(x => x.id === id); return f ? f.nombre : (id || 'sin fuente'); };
  const etiquetaTrad = id => { const t = [...N.tradicionesDe(D, id)]; return t.length === 1 ? `<span class="etiqueta">solo ${esc(t[0])}</span>` : ''; };
  const pasajesLeidos = () => new Set(store.get('biblia.pasajesLeidos', []));
  /* ---------- Lectura en orden: qué es accesible (núcleo: accesibles) y tiempo mínimo por pasaje ---------- */
  let accCache = { k: null, A: null };
  const ACC = () => {
    const g = store.get('biblia.pasajesLeidos', []), L = Array.isArray(g) ? g : [], k = PERF.r.activo + '|' + L.join(',');
    if (accCache.k !== k) accCache = { k, A: N.accesibles(D, L) };
    return accCache.A;
  };
  const refOk = ref => ACC().ref(ref);
  const personaOk = id => N.personaAccesible(D, ACC(), id);
  const lugarOk = id => N.lugarAccesible(D, ACC(), id);
  const ICO_CANDADO = '<svg class="ico-candado" viewBox="0 0 20 20" aria-hidden="true"><rect x="4.5" y="9" width="11" height="8" rx="1.5"/><path d="M7 9V6.5a3 3 0 016 0V9"/></svg>';
  const bloqueadoHTML = txt => `<p class="aviso-bloqueo">${ICO_CANDADO}<span>${txt}</span></p>`;
  // Tiempo acumulado con el pasaje abierto y la página visible (o sonando «Escuchar»); se guarda por perfil.
  const LECT = { id: null, acum: 0, min: 0, palabras: 0, leido: false, ult: Date.now(), timer: 0 };
  let paginaVisible = document.visibilityState !== 'hidden';
  const tiemposGuardados = () => N.normalizarTiempos(store.get('biblia.tiemposLectura', null));
  function guardarTiempo() {
    if (!LECT.id || LECT.leido) return;
    const t = tiemposGuardados(); t[LECT.id] = Math.floor(LECT.acum); store.set('biblia.tiemposLectura', t);
  }
  const cuentaActiva = () => paginaVisible || habla.estado === 'sonando'; // `habla` (Escuchar) se define más abajo; solo se usa al contar
  function empezarLectura(p) {
    if (LECT.id !== p.id) { guardarTiempo(); LECT.id = p.id; LECT.acum = tiemposGuardados()[p.id] || 0; }
    LECT.leido = pasajesLeidos().has(p.id);
    LECT.palabras = N.palabrasPasaje(D, p, esNinoActivo() ? plegadoRef : null); // lo plegado para el niño no se le muestra
    LECT.min = N.segundosMinimos(LECT.palabras, perfil()); LECT.ult = Date.now();
    if (!LECT.timer) LECT.timer = setInterval(tickLectura, 1000);
  }
  function tickLectura() {
    const ahora = Date.now(), dt = Math.min(65, Math.max(0, (ahora - LECT.ult) / 1000)); LECT.ult = ahora;
    if (!LECT.id) return;
    if (!main.querySelector(`[data-leido-seguir="${CSS.escape(LECT.id)}"]`)) { guardarTiempo(); LECT.id = null; return; } // salió del pasaje
    if (LECT.leido || !cuentaActiva()) return;
    const antes = LECT.acum; LECT.acum += dt;
    if (Math.floor(LECT.acum / 5) !== Math.floor(antes / 5)) guardarTiempo();
    pintarMarcar();
  }
  document.addEventListener('visibilitychange', () => { tickLectura(); paginaVisible = document.visibilityState !== 'hidden'; LECT.ult = Date.now(); guardarTiempo(); });
  window.addEventListener('pagehide', () => { tickLectura(); guardarTiempo(); });
  const listoMarcar = () => N.puedeMarcar(LECT.leido, LECT.acum, LECT.min);
  const textoMarcar = (hayNext) => hayNext ? 'Marcar como leído y seguir' : 'Marcar como leído';
  function marcarHTML(p, next) {
    const listo = listoMarcar();
    return `<button type="button" class="boton boton-marcar" data-leido-seguir="${esc(p.id)}" data-txt="${esc(textoMarcar(!!next))}"${listo ? '' : ' disabled aria-describedby="regla-lectura"'}>${listo ? textoMarcar(!!next) : `${ICO_RELOJ}Podrás marcarlo en ${N.relojTxt(LECT.min - LECT.acum)}`}</button>`;
  }
  const ICO_RELOJ = '<svg class="ico-reloj" viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="7"/><path d="M10 6v4l2.5 2"/></svg>';
  function reglaHTML() {
    const ppm = N.ppmDe(perfil());
    if (LECT.leido) return '<p class="regla-lectura meta" id="regla-lectura">Ya lo leíste: puedes releerlo sin esperar.</p>';
    return `<p class="regla-lectura meta" id="regla-lectura">La lectura avanza en orden. Antes de marcar un pasaje hay un tiempo mínimo: sus ${LECT.palabras} palabras a ${ppm} palabras por minuto (${esNinoActivo() ? 'perfil de niño' : 'perfil adulto'}) = ${N.relojTxt(LECT.min)}. Solo cuenta mientras el pasaje está abierto y a la vista, o mientras suena «Escuchar».</p>
      <p class="sr" id="marcar-aviso" aria-live="polite"></p>`;
  }
  function pintarMarcar() {
    const b = main.querySelector('[data-leido-seguir]'); if (!b || b.dataset.leidoSeguir !== LECT.id) return;
    if (listoMarcar()) {
      if (b.disabled) { b.disabled = false; b.removeAttribute('aria-describedby'); b.textContent = b.dataset.txt; const a = $('#marcar-aviso'); if (a) a.textContent = 'Ya puedes marcar el pasaje como leído.'; }
      return;
    }
    const t = `Podrás marcarlo en ${N.relojTxt(LECT.min - LECT.acum)}`;
    if (b.textContent !== t) b.innerHTML = ICO_RELOJ + t;
  }
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
    if (args[0] === 'p') return pasajeAccesible(ps.find(x => x.id === args[1]), args[2] || null);
    // #leer/Ex (plan de ese libro), #leer/Ex/7/7 (versículo) y los enlaces antiguos #leer/7/7 (Génesis).
    let a = args.filter(x => x !== ''), lbRuta = null;
    if (a[0] && !/^\d+$/.test(a[0])) { lbRuta = N.libroIdDe(D, a[0]); a = a.slice(1); }
    if (a[0]) {
      const lb = lbRuta || 'Gn', cap = +a[0], v = +a[1] || null;
      const p = N.pasajeDe(D, `${lb} ${cap}:${v || 1}`) || ps.find(x => { const r = N.parseRef(x.inicio); return r.libro === lb && r.cap === cap; });
      return pasajeAccesible(p, v ? `${cap}:${v}` : null);
    }
    const L = pasajesLeidos(), pos = store.get('biblia.pos', null), A = ACC();
    const actual0 = pos && ps.find(x => x.id === pos.pasaje), actual = actual0 && A.pasaje(actual0.id) ? actual0 : null;
    const n = ps.filter(p => L.has(p.id)).length;
    // Se sigue en la frontera (primer pasaje sin leer); con todo leído, donde se quedó.
    const sig = A.frontera || actual || ps[0];
    const enSig = actual && sig && actual.id === sig.id && pos.v;
    const editorial = ps.some(p => p.titulo_origen === 'editorial');
    // Libros con pasajes; con más de uno, el plan muestra un selector y solo el libro elegido.
    const LB = N.libros(D).map(l => { const pl = ps.filter(p => N.libroDe(p) === l.id); return Object.assign({}, l, { pasajes: pl.length, leidos: pl.filter(p => L.has(p.id)).length, bloqueado: !!pl.length && !A.pasaje(pl[0].id), entero: !!pl.length && pl.every(p => A.pasaje(p.id)) }); }).filter(l => l.pasajes);
    const varios = LB.length > 1;
    if (lbRuta && LB.some(l => l.id === lbRuta)) { estado.libro = lbRuta; store.set('biblia.libro', lbRuta); }
    // Un libro aún bloqueado solo se abre si se pide por enlace (#leer/Ex); si no, el de la frontera.
    const elegido = [lbRuta, estado.libro, store.get('biblia.libro', null), sig && N.libroDe(sig)].find(id => id && LB.some(l => l.id === id && (id === lbRuta || !l.bloqueado))) || (LB[0] && LB[0].id);
    estado.libro = elegido;
    const libroSel = LB.find(l => l.id === elegido);
    const selector = varios ? `<nav class="libros" aria-label="Libros">${LB.map(l => `<a class="libro-btn${l.bloqueado ? ' bloqueado' : ''}" href="#leer/${esc(l.id)}"${l.id === elegido ? ' aria-current="true"' : ''}>
        <span class="libro-nombre">${l.bloqueado ? ICO_CANDADO : ''}${esc(l.nombre)}${l.bloqueado ? '<span class="sr"> (bloqueado)</span>' : ''}</span>
        <span class="libro-meta">${l.capitulos ? `${l.capitulos} capítulos, ` : ''}${l.leidos} de ${l.pasajes} pasajes</span>
        <span class="libro-prog" aria-hidden="true"><span style="width:${Math.round(100 * l.leidos / l.pasajes)}%"></span></span></a>`).join('')}</nav>` : '';
    const itemPasaje = (p, num) => {
      // Bloqueado: sin título ni resumen (no se adelanta nada), solo su referencia y el candado.
      if (!A.pasaje(p.id)) return `<li class="pasaje bloqueado"><span class="pasaje-fila" aria-label="Pasaje ${num}, ${esc(rango(p))}: bloqueado hasta leer los anteriores"><span class="pasaje-num" aria-hidden="true">${num}</span>
          <span class="pasaje-cuerpo" aria-hidden="true"><span class="pasaje-titulo">Pasaje bloqueado</span><span class="pasaje-rango">${rango(p)}</span></span>
          <span class="estado bloqueado" aria-hidden="true">${ICO_CANDADO}Bloqueado</span></span></li>`;
      const est = L.has(p.id) ? 'leido' : A.frontera && A.frontera.id === p.id ? 'en-curso' : 'pendiente';
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
      ${elegido && libroSel && libroSel.entero ? videoLibroHTML(elegido) : elegido && libroSel ? `<p class="meta video-libro-bloq">${ICO_CANDADO} El video sobre ${esc(libroSel.nombre)} resume todo el libro: se podrá ver cuando llegues a su último pasaje.</p>` : ''}
      ${elegido === 'Ex' && libroSel && !libroSel.bloqueado ? entradaTBHTML() : ''}
      ${plan}
      ${editorial ? `<p class="meta">Los títulos${secs.some(g => g.titulo) ? ', secciones' : ''} y resúmenes de los pasajes son editoriales: no forman parte del texto bíblico.</p>` : ''}</div></div>`;
  }

  /* ---------- Leer: pasaje con acompañante ---------- */
  // Rótulo discreto si el pasaje es (o contiene) una genealogía del catálogo de juego; el texto no cambia.
  function genealogiaHTML(p) {
    const gs = N.genealogiasDe(JUEGO(), p); if (!gs.length) return '';
    const entera = g => N.clave(g.inicio) <= N.clave(p.inicio) && N.clave(g.fin || g.inicio) >= N.clave(p.fin);
    return `<p class="pasaje-genealogia">${gs.map(g => `<span class="etiqueta genealogia" title="${esc(g.titulo ? g.titulo + '. ' : '')}Quien solo se nombra en una genealogía no cuenta como aparición en la colección.">Genealogía${entera(g) ? '' : ' · ' + esc(rango({ inicio: g.inicio, fin: g.fin || g.inicio }))}</span>`).join('')}</p>`;
  }
  // Enlace a un pasaje (hash, «continúa», referencias): si está bloqueado, se abre la frontera con un aviso.
  function pasajeAccesible(p, activo) {
    const r = p ? N.destinoPasaje(D, ACC(), p.id) : { pasaje: null };
    if (!r.bloqueado) return vistaPasaje(p, activo);
    try { history.replaceState(null, '', `#leer/p/${r.pasaje.id}`); } catch (e) { /* file:// */ }
    estado.avisoBloq = { id: r.pasaje.id, html: bloqueadoHTML(`${esc(rango(r.pedido))} todavía está bloqueado: la lectura avanza en orden. Te llevamos al primer pasaje que te falta leer.`) };
    return vistaPasaje(r.pasaje, null);
  }
  function vistaPasaje(p, activo) {
    const aviso = p && estado.avisoBloq && estado.avisoBloq.id === p.id ? estado.avisoBloq.html : ''; // se mantiene al repintar, hasta cambiar de ruta
    if (!p) return `<h1 tabindex="-1">Pasaje no encontrado</h1><p class="vacio-txt">Ese pasaje no está en los datos, que cubren ${esc(N.alcance(D).texto)}.</p><p><a class="boton" href="#leer">Ver el plan de lectura</a></p>`;
    const ps = N.pasajes(D), i = ps.findIndex(x => x.id === p.id), prev = ps[i - 1], next = ps[i + 1];
    const lb = N.libroDe(p), psL = ps.filter(x => N.libroDe(x) === lb), iL = psL.findIndex(x => x.id === p.id);
    const vs = N.versiculosDe(D, p);
    estado.pasaje = p;
    estado.activo = activo && vs.some(v => `${v.cap}:${v.n}` === activo && !plegadoRef(v.ref)) ? activo : null;
    store.set('biblia.pos', { pasaje: p.id, v: estado.activo });
    empezarLectura(p);
    const nextOk = next && ACC().pasaje(next.id);
    const fuente = ((D.fuentes || []).find(f => /rv/i.test(f.id)) || {}).id;
    let capPrev = null;
    const NT = notasGuardadas().versos;
    // Términos con explicación: primera aparición por pasaje, sin los versículos plegados (no se ven).
    const TM = EXPL() && explOn() && !estado.comparar ? N.marcadoPasaje(D, EXPL(), vs, plegadoRef) : null;
    const texto = tramosVersos(vs, (v, j) => {
      const k = `${v.cap}:${v.n}`, ap = N.tieneApoyo(D, v.ref), nt = NT[v.ref] || null;
      const cab = v.cap !== capPrev && j ? `<span class="cap-marca">Capítulo ${v.cap}</span>` : '';
      capPrev = v.cap;
      const segs = N.segmentar(D, v.ref, v.texto, TM && TM.get(v.ref));
      const partes = !v.texto && v.nota ? `<span class="meta">${esc(v.nota)}</span>` : segs.map((s, si) => {
        if (s.lugar) return `<button type="button" class="mencion-lugar" data-lugar="${esc(s.lugar)}">${esc(s.texto)}</button>`;
        if (s.persona) { const per = N.persona(D, s.persona) || {}; return `<button type="button" class="mencion${per.sexo === 'f' ? ' mujer' : ''}" data-persona="${esc(s.persona)}">${esc(s.texto)}</button>`; }
        if (s.termino) return `<button type="button" class="termino" data-termino="${esc(s.termino)}" aria-haspopup="dialog" title="Ver la explicación">${esc(s.texto)}</button>`;
        if (j === 0 && si === 0 && s.texto) { const t = s.texto.trimStart(), c = Array.from(t)[0] || ''; return `<span class="capitular" aria-hidden="true">${esc(c)}</span><span class="sr">${esc(c)}</span>${esc(t.slice(c.length))}`; }
        return esc(s.texto);
      }).join('');
      return `${cab}<span class="vers${ap ? ' con-apoyo' : ''}${k === estado.activo ? ' activo' : ''}${habla.k === k ? ' sonando' : ''}${nbClases(nt)}" id="v${v.cap}-${v.n}" data-v="${k}"><button type="button" class="vn" data-activar="${k}" aria-pressed="${k === estado.activo}" aria-label="Versículo ${v.n}${ap ? ', con datos en el acompañante' : ''}">${v.n}</button>${nbSrHTML(nt)}${marcaVariante(v.ref, v.n)}${partes}${nbIndHTML(nt, k, v.n)} </span>`;
    }, (vsP, j) => { const v = vsP[0], cab = v.cap !== capPrev && j ? `<span class="cap-marca">Capítulo ${v.cap}</span>` : ''; capPrev = vsP[vsP.length - 1].cap; return cab; });
    const nuevos = N.primerasApariciones(D, p);
    return `<div class="pasaje-vista"><article class="lectura">${aviso ? `<div role="status">${aviso}</div>` : ''}
      <header class="cab-pasaje"><a class="volver" href="#leer/${esc(lb)}"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M12 4l-6 6 6 6"/></svg>Plan de lectura</a>
        <p class="pasaje-libro">${esc(N.nombreLibro(D, lb))}</p>
        <p class="pasaje-rango">${rango(p)}<span class="pasaje-pos">pasaje ${iL + 1} de ${psL.length}</span></p>
        <h1 tabindex="-1">${esc(p.titulo)}</h1>
        ${p.titulo_origen === 'editorial' ? '<p class="meta">Título editorial, no del texto bíblico.</p>' : ''}${genealogiaHTML(p)}</header>
      ${imagenPasajeHTML(p)}
      ${herramientasPasajeHTML()}
      ${dificilesHTML(p)}
      ${estado.comparar ? compararHTML(p) : `<div class="biblia">${texto || '<p class="vacio-txt">Este pasaje no tiene versículos en los datos.</p>'}</div>
      <p class="pista-lectura meta"><span class="marca-apoyo" aria-hidden="true"></span>Pulsa el número de un versículo para ver sus datos. La marca al margen indica vínculos, edades o personas sin nombre.${ORIG.o && N.variantesDe(ORIG.o, vs.map(v => v.ref)).length ? ' «var.» señala una variante entre manuscritos.' : ''}</p>
      ${fuente ? `<p class="meta">Texto: ${esc(fuenteNombre(fuente))}</p>` : ''}`}
      ${manuscritoHTML(p)}
      <section class="nuevo" aria-labelledby="t-nuevo"><h2 id="t-nuevo">Lo nuevo en este pasaje</h2>
        ${nuevos.length ? `<p class="meta">Personas que aparecen por primera vez:</p><ul class="chips">${nuevos.map(id => `<li>${btnPersona(id)}</li>`).join('')}</ul>` : '<p class="vacio-txt">Nadie aparece aquí por primera vez.</p>'}</section>
      <nav class="pasos-pasaje" aria-label="Pasajes">
        ${prev ? `<a class="boton secundario" href="#leer/p/${esc(prev.id)}" title="${esc(prev.titulo)}">Anterior</a>` : '<span></span>'}
        ${marcarHTML(p, next)}
        ${nextOk ? `<a class="boton secundario" href="#leer/p/${esc(next.id)}" title="${esc(next.titulo)}">Siguiente</a>` : next ? `<span class="boton secundario siguiente-bloq" aria-disabled="true" title="Se desbloquea al marcar como leído este pasaje">${ICO_CANDADO}Siguiente</span>` : '<span></span>'}
      </nav>${reglaHTML()}</article>
      <aside class="acompanante${estado.hoja ? ' abierta' : ''}" id="acompanante" aria-label="Acompañante de lectura">${acompHTML()}</aside></div>`;
  }

  /* ---------- Contenido fuerte en la lectura: plegado (niño), nota (medio) o aviso (adulto que lo pide) ---------- */
  const ICO_CONT = '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3a7 7 0 100 14 7 7 0 000-14zM10 6.5v4M10 13.5v.5"/></svg>';
  const rangoVs = vs => { const a = vs[0], b = vs[vs.length - 1]; return a.cap === b.cap ? (a.n === b.n ? `Versículo ${a.n}` : `Versículos ${a.n} a ${b.n}`) : `Versículos ${a.cap}:${a.n} a ${b.cap}:${b.n}`; };
  const rotuloCont = () => `<span class="cont-rotulo">${ROTULO_CONT}</span>`;
  const plegadoHTML = (vs, m) => `<span class="cont-bloque cont-plegado" role="note"><span class="cont-cab">${ICO_CONT}<strong>Esta parte es para leerla con un adulto</strong></span>
      <span class="cont-meta">${rangoVs(vs)}. El texto sigue aquí, solo está plegado.</span>
      <span class="cont-acc"><button type="button" class="boton mini-boton secundario" data-mostrar-cont="${esc(m.desde)}">Mostrar</button></span>${rotuloCont()}</span>`;
  const avisoContHTML = m => `<span class="cont-bloque cont-aviso" role="note"><span class="cont-cab">${ICO_CONT}<strong>Aviso: contenido fuerte</strong><span class="etiqueta">${esc(CAT_CONT[m.categoria] || m.categoria || '')}</span></span>
      ${m.motivo ? `<span class="cont-meta">${esc(m.motivo)}</span>` : ''}${rotuloCont()}</span>`;
  const notaContHTML = m => `<span class="cont-nota" role="note">${ICO_CONT}<span>${esc(NOTA_CONT[m.categoria] || 'Aquí hay un pasaje delicado.')} ${rotuloCont()}</span></span>`;
  const desplegadoHTML = m => `<span class="cont-bloque cont-desplegado" role="note"><span class="cont-meta">Parte mostrada con el PIN de un adulto.</span>
      <span class="cont-acc"><button type="button" class="enlace-boton" data-plegar-cont="${esc(m.desde)}">Volver a plegar</button></span>${rotuloCont()}</span>`;
  // Versículos agrupados según lo que el perfil hace con cada marca; el texto nunca se altera y los números se conservan.
  function tramosVersos(vs, verso, cabPlegado) {
    const xs = vs.map(v => accionDe(v.ref));
    let out = '', i = 0;
    while (i < vs.length) {
      let j = i; while (j + 1 < vs.length && xs[j + 1].accion === xs[i].accion && (xs[i].accion === 'mostrar' || xs[j + 1].marca === xs[i].marca)) j++;
      const g = vs.slice(i, j + 1), x = xs[i], ini = i;
      if (x.accion === 'plegar') out += cabPlegado(g, ini) + plegadoHTML(g, x.marca);
      else {
        const cuerpo = g.map((v, t) => verso(v, ini + t)).join('');
        out += x.accion === 'aviso' ? avisoContHTML(x.marca) + cuerpo : x.accion === 'desplegado' ? desplegadoHTML(x.marca) + cuerpo
          : x.accion === 'nota' ? cuerpo + notaContHTML(x.marca) : cuerpo;
      }
      i = j + 1;
    }
    return out;
  }

  // Nota del vínculo tal como viene en los datos («sierva», «concubina»…), sin reinterpretarla.
  const notaVinculo = r => r && r.nota ? `<span class="nota-vinculo">${esc(r.nota)}</span>` : '';
  const TIPO_REL = r => r.tipo === 'conyuge' ? `${esc(nombre(r.de))} y ${esc(nombre(r.a))}: cónyuges${notaVinculo(r)}`
    : `${esc(nombre(r.de))} es ${r.tipo === 'madre' ? 'madre' : 'padre'} de ${esc(nombre(r.a))}`;
  // "Abram tenía 75 años al salir de Harán" (+ LXX si difiere).
  function eventoHTML(x) {
    const base = x.TM || x.LXX;
    return `<li${x.difiere ? ' class="difiere"' : ''}><span class="edad-quien">${esc(nombre(x.persona))} tenía <strong>${base.valor}</strong> años${x.evento ? ' ' + esc(x.evento) : ''}${x.solo === 'LXX' ? ' (según la LXX)' : ''}</span>
      ${insignia(base.certeza || 'texto', x.ref)}${base.cita && !plegadoRef(x.ref) ? ` <span class="cita-corta">«${esc(base.cita)}»</span>` : ''}
      ${x.difiere ? `<p class="difiere-txt">En la Septuaginta: ${x.LXX.valor}${x.LXX.ref && x.LXX.ref !== x.TM.ref ? ' (' + refHTML(x.LXX.ref) + ')' : ''}</p>` : ''}</li>`;
  }
  const QUIEN_MAX = 8; // a partir de aquí "Quién aparece" se agrupa
  function acompHTML() {
    const p = estado.pasaje;
    if (!p) return '';
    const lb = N.libroDe(p);
    const refs = estado.activo ? [`${lb} ${estado.activo}`] : N.versiculosDe(D, p).map(v => v.ref).filter(r => !plegadoRef(r)); // lo plegado no alimenta el acompañante
    const A = N.acompanante(D, refs, refOk);
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
    html += enCaminoHTML(p, sec, I);
    html += tabernaculoAcompHTML(p, refs, sec, I);
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
        const r = estado.activo ? [refs[0], refs[0]] : [p.inicio, p.fin], v0 = N.vecinosFechados(D, r[0], r[1], combo);
        const v = { anterior: v0.anterior && refOk(v0.anterior.ref) ? v0.anterior : null, siguiente: v0.siguiente && refOk(v0.siguiente.ref) ? v0.siguiente : null }; // nada de lo aún no leído
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
    const miniOk = id => { const m = N.miniArbol(D, id); return Object.assign({}, m, { padres: m.padres.filter(personaOk), hijos: m.hijos.filter(personaOk), conyuges: m.conyuges.filter(personaOk) }); };
    const centrales = A.personas.map(x => x.id).filter(id => { const m = miniOk(id); return !(N.persona(D, id) || {}).sin_nombre && (m.padres.length || m.hijos.length); }).slice(0, estado.activo ? 2 : 3);
    if (centrales.length) html += sec('Dónde va en el árbol', centrales.map(id => {
      const m = miniOk(id), mas = m.hijos.length - 5;
      return `<div class="mini"><div class="mini-gen">${m.padres.map(btnPersona).join('') || '<span class="meta">Padres no constan</span>'}</div>
        <div class="mini-gen centro">${btnPersona(id)}${m.conyuges.map(c => `<span class="cony-mini">⚭</span>${btnPersona(c)}`).join('')}</div>
        <div class="mini-gen">${m.hijos.slice(0, 5).map(btnPersona).join('') || '<span class="meta">Sin hijos registrados</span>'}${mas > 0 ? `<span class="meta">y ${mas} más</span>` : ''}</div>
        <a class="enlace-arbol" href="#arbol/${encodeURIComponent(id)}">Ver a ${esc(nombre(id))} en el árbol completo</a></div>`;
    }).join(''), I('M10 3v5M10 8H5v4M10 8h5v4M10 8v9'));
    // «¿Sabías que…?» (cálculo) del pasaje: como mucho dos, elegidas en el núcleo sin repetir las del pasaje anterior.
    if (N.crono(D) && !estado.activo) {
      const tr = tradSimple(), cs = (N.sabiasQue(D, comboDe(tr)).get(p.id) || []).filter(c => N.curiosidadPermitida(c, perfil(), CONT()) && N.curiosidadAccesible(ACC(), c));
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
    const b = ponerBarraNotas(); if (b) b.scrollIntoView({ block: 'nearest' });
  }

  /* ---------- Notas y subrayados del lector (por perfil). Son del usuario: siempre «Tu nota», sin insignias de certeza. ---------- */
  const NB_NOMBRE = { amarillo: 'amarillo', verde: 'verde', azul: 'azul', rosa: 'rosa' };
  const ICO_NOTA = '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 3.5h7l3 3v10H5z"/><path d="M7.5 9h5M7.5 12h5M7.5 15h3"/></svg>';
  let nbEditar = null, nbDeshacer = null; // ref cuya nota se está escribiendo; última entrada quitada (para deshacer)
  const nbF = { color: '', conNota: false, q: '' }; // filtros de «Mis notas»
  const notasGuardadas = () => N.normalizarNotas(store.get('notas', null));
  const guardarNotas = o => LS.set(N.clavePerfil(PERF.r.activo, 'notas'), JSON.stringify(N.normalizarNotas(o)));
  const nbClases = e => (e && e.color ? ` nb-sub nb-${e.color}` : '') + (e && e.nota ? ' nb-con-nota' : '');
  const nbSrHTML = e => e && e.color ? `<span class="sr nb-sr">Subrayado ${NB_NOMBRE[e.color]}.</span>` : '';
  const nbIndHTML = (e, k, n) => e && e.nota ? `<button type="button" class="nb-ind" data-nb-abrir="${esc(k)}" aria-label="Tu nota del versículo ${esc(n)}" title="Tu nota">${ICO_NOTA}</button>` : '';
  const notaUsuarioHTML = t => `<div class="nb-nota"><span class="nb-rotulo">Tu nota</span><p>${esc(t)}</p></div>`;
  const refActiva = () => estado.pasaje && estado.activo ? `${N.libroDe(estado.pasaje)} ${estado.activo}` : null;
  function barraNotasHTML(ref) {
    const e = N.notaDe(notasGuardadas(), ref), legible = N.refLegible(D, ref, ''), editando = nbEditar === ref;
    const colores = N.NOTAS_COLORES.map(c => `<button type="button" class="nb-color nb-c-${c}" data-nb-color="${c}" aria-pressed="${!!e && e.color === c}" aria-label="Subrayar en ${NB_NOMBRE[c]}" title="${NB_NOMBRE[c][0].toUpperCase() + NB_NOMBRE[c].slice(1)}"></button>`).join('');
    return `<div class="nb-barra" role="group" aria-label="Subrayado y nota de ${esc(legible)}" data-nb="${esc(ref)}">
      <div class="nb-fila"><span class="nb-colores" role="group" aria-label="Subrayar">${colores}</span>
        <button type="button" class="boton mini-boton secundario" data-nb-nota aria-expanded="${editando}">${ICO_NOTA}${e && e.nota ? 'Editar nota' : 'Nota'}</button>
        <button type="button" class="boton mini-boton secundario" data-nb-copiar>Copiar cita</button>
        ${e ? '<button type="button" class="boton mini-boton secundario" data-nb-quitar>Quitar</button>' : ''}</div>
      ${editando ? `<form class="nb-editor" data-nb-form><label class="nb-rotulo" for="nb-texto">Tu nota</label>
          <textarea id="nb-texto" rows="3" maxlength="4000">${esc(e && e.nota || '')}</textarea>
          <span class="nb-editor-acc"><button type="submit" class="boton mini-boton">Guardar</button><button type="button" class="boton mini-boton secundario" data-nb-cancelar>Cancelar</button></span></form>`
        : e && e.nota ? notaUsuarioHTML(e.nota) : ''}
      <p class="nb-estado meta" role="status" aria-live="polite"></p></div>`;
  }
  // Barra bajo el versículo activo (fuera de él: no lo tapa y no interfiere con su clic). Devuelve la barra o null.
  function ponerBarraNotas(foco, msg) {
    main.querySelectorAll('.nb-barra').forEach(b => b.remove());
    const ve = main.querySelector('.biblia .vers.activo'), ref = refActiva();
    if (!ve || !ref) { nbEditar = null; return null; }
    if (nbEditar !== ref) nbEditar = null;
    ve.insertAdjacentHTML('afterend', barraNotasHTML(ref));
    const b = ve.nextElementSibling;
    if (foco) { const el = b.querySelector(foco); if (el) el.focus(); }
    if (msg) setTimeout(() => { const s = b.isConnected && b.querySelector('.nb-estado'); if (s) s.innerHTML = msg; }, 40);
    return b;
  }
  // Clases e indicador del versículo tras un cambio, sin repintar el pasaje.
  function refrescarVerso(ref) {
    const r = N.parseRef(ref), ve = main.querySelector(`.vers[data-v="${r.cap}:${r.v}"]`); if (!ve) return;
    const e = N.notaDe(notasGuardadas(), ref);
    [...ve.classList].filter(c => c.startsWith('nb-')).forEach(c => ve.classList.remove(c));
    nbClases(e).trim().split(/\s+/).filter(Boolean).forEach(c => ve.classList.add(c));
    ve.querySelectorAll('.nb-sr, .nb-ind').forEach(x => x.remove());
    const vn = ve.querySelector('.vn'); if (vn) vn.insertAdjacentHTML('afterend', nbSrHTML(e));
    ve.insertAdjacentHTML('beforeend', nbIndHTML(e, `${r.cap}:${r.v}`, r.v));
  }
  function cambiarNota(ref, cambios, foco, msg) {
    if (!guardarNotas(N.ponerNota(notasGuardadas(), ref, cambios))) msg = 'No se pudo guardar: el almacenamiento del navegador no está disponible.';
    refrescarVerso(ref); ponerBarraNotas(foco, msg);
  }
  async function copiarTexto(t) {
    try { await navigator.clipboard.writeText(t); return true; } catch (e) {
      const ta = document.createElement('textarea'); ta.value = t; ta.setAttribute('readonly', ''); ta.style.cssText = 'position:fixed;top:0;opacity:0';
      document.body.appendChild(ta); ta.select(); let ok = false; try { ok = document.execCommand('copy'); } catch (er) { /* nada */ } ta.remove(); return ok;
    }
  }
  const nbEstadoVista = msg => { const s = $('#nb-estado-copia'); if (s) s.innerHTML = msg; };
  function listaNotasHTML() {
    const todas = N.listarNotas(notasGuardadas());
    if (!todas.length) return `<div class="nb-vacio"><p class="vacio-txt">Aún no tienes subrayados ni notas en este perfil.</p>
      <p>Mientras lees un pasaje, pulsa el número de un versículo (o el versículo): aparece una barra para subrayarlo en un color, escribir tu nota o copiar la cita. Todo lo que marques se reúne aquí, en el orden de la Biblia.</p>
      <p><a class="boton" href="#leer">Ir a leer</a></p></div>`;
    const xs0 = N.listarNotas(notasGuardadas(), nbF), xs = xs0.filter(x => refOk(x.ref)), ocultas = xs0.length - xs.length; // lectura en orden
    const avisoOcultas = ocultas ? `<p class="meta">${ICO_CANDADO} ${ocultas} ${ocultas === 1 ? 'marca está' : 'marcas están'} en pasajes aún bloqueados: se verán al llegar (siguen guardadas y se exportan).</p>` : '';
    if (!xs.length) return avisoOcultas + `<p class="vacio-txt">Ninguna de tus ${todas.length} marcas ${ocultas ? 'accesibles ' : ''}coincide con el filtro.</p>`;
    return `${avisoOcultas}<p class="meta" aria-live="polite">${xs.length === todas.length ? `${xs.length} ${xs.length === 1 ? 'versículo' : 'versículos'}` : `${xs.length} de ${todas.length}`}</p>
      <ol class="nb-lista">${xs.map(x => {
        const r = N.parseRef(x.ref), txt = N.textoVerso(D, x.ref);
        const cuerpo = plegadoRef(x.ref) ? '<span class="meta">Texto plegado para este perfil.</span>' : txt ? `<span class="${x.color ? `nb-sub nb-${x.color}` : ''}">${esc(txt)}</span>` : '<span class="meta">Este versículo no está en los datos cargados.</span>';
        return `<li class="nb-item${x.color ? ` nb-borde-${x.color}` : ''}"><div class="nb-item-cab"><a class="nb-ir" href="#leer/${esc(r.libro)}/${r.cap}/${r.v}">${esc(N.refLegible(D, x.ref, ''))}</a>
          ${x.color ? `<span class="nb-chip"><span class="nb-punto nb-c-${x.color}" aria-hidden="true"></span>Subrayado ${NB_NOMBRE[x.color]}</span>` : ''}</div>
          <p class="nb-texto">${cuerpo}</p>${x.nota ? notaUsuarioHTML(x.nota) : ''}</li>`;
      }).join('')}</ol>`;
  }
  function vistaNotas() {
    const hay = N.listarNotas(notasGuardadas()).length;
    const filtros = hay ? `<div class="nb-filtros">
        <span class="nb-f-colores" role="group" aria-label="Filtrar por color"><button type="button" class="boton mini-boton secundario" data-nb-filtro="" aria-pressed="${!nbF.color}">Todos</button>${N.NOTAS_COLORES.map(c => `<button type="button" class="boton mini-boton secundario" data-nb-filtro="${c}" aria-pressed="${nbF.color === c}"><span class="nb-punto nb-c-${c}" aria-hidden="true"></span>${NB_NOMBRE[c][0].toUpperCase() + NB_NOMBRE[c].slice(1)}</button>`).join('')}</span>
        <label class="nb-check"><input type="checkbox" id="nb-connota"${nbF.conNota ? ' checked' : ''}> Solo con nota</label>
        <label class="nb-buscar"><span class="sr">Buscar en el texto de tus notas</span><input type="search" id="nb-q" placeholder="Buscar en tus notas" value="${esc(nbF.q)}" autocomplete="off"></label></div>` : '';
    return `<div class="nb-vista"><h1 tabindex="-1">Mis notas</h1>
      <p class="sub">Tus subrayados y notas de lectura. Son tuyos, no datos de la app: se guardan en este dispositivo, solo para el perfil «${esc(perfil().nombre)}».</p>
      ${filtros}<div id="nb-lista">${listaNotasHTML()}</div>
      <section class="nb-copia" aria-labelledby="t-nb-copia"><h2 id="t-nb-copia">Exportar e importar</h2>
        <p class="meta">Guarda una copia o pásala a otro dispositivo o perfil. Al importar se juntan con las que ya tienes; si un versículo está en ambas, se queda la versión más reciente.</p>
        <div class="nb-acciones"><button type="button" class="boton secundario" data-nb-exportar${hay ? '' : ' disabled'}>Exportar (JSON)</button>
          <button type="button" class="boton secundario" data-nb-copiar-todo${hay ? '' : ' disabled'}>Copiar como texto</button>
          <label class="boton secundario nb-importar">Importar JSON<input type="file" id="nb-archivo" class="sr" accept=".json,application/json"></label></div>
        <p class="nb-estado" id="nb-estado-copia" role="status" aria-live="polite"></p></section></div>`;
  }
  function refrescarListaNotas() {
    const l = $('#nb-lista'); if (l) l.innerHTML = listaNotasHTML();
    document.querySelectorAll('[data-nb-filtro]').forEach(b => b.setAttribute('aria-pressed', b.dataset.nbFiltro === nbF.color));
  }
  function exportarNotasArchivo() {
    const p = perfil(), hoy = new Date().toISOString();
    const datos = N.exportarNotas(notasGuardadas(), { perfil: p.nombre, exportado: hoy });
    const url = URL.createObjectURL(new Blob([JSON.stringify(datos, null, 2)], { type: 'application/json' }));
    const a = document.createElement('a'), nombreArch = N.norm(p.nombre).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'perfil';
    a.href = url; a.download = `biblia-notas-${nombreArch}-${hoy.slice(0, 10)}.json`; a.hidden = true;
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 2000);
    const n = Object.keys(datos.versos).length;
    nbEstadoVista(`Archivo generado con ${n} ${n === 1 ? 'versículo' : 'versículos'} (${esc(a.download)}).`);
  }
  function importarNotasArchivo(input) {
    const f = input.files && input.files[0]; if (!f) return;
    const fin = msg => { input.value = ''; nbEstadoVista(msg); };
    if (f.size > 2e6) { fin(`No se importó «${esc(f.name)}»: es demasiado grande para ser un archivo de notas.`); return; }
    f.text().then(txt => {
      const v = N.validarNotas(txt);
      if (!v.ok) { fin(`No se importó «${esc(f.name)}»: ${esc(v.error)}`); return; }
      const r = N.fusionarNotas(notasGuardadas(), v.notas);
      if (!guardarNotas(r.notas)) { fin('No se pudo guardar: el almacenamiento del navegador no está disponible.'); return; }
      const msg = `Importado «${esc(f.name)}»: ${r.anadidos} ${r.anadidos === 1 ? 'añadido' : 'añadidos'}, ${r.actualizados} ${r.actualizados === 1 ? 'actualizado' : 'actualizados'}, ${r.iguales} sin cambios${v.descartados ? `; ${v.descartados} ${v.descartados === 1 ? 'entrada no válida descartada' : 'entradas no válidas descartadas'}` : ''}.`;
      rerender(); nbEstadoVista(msg);
    }, () => fin(`No se pudo leer «${esc(f.name)}».`));
  }
  document.addEventListener('click', e => {
    const t = e.target; if (!t.closest) return;
    const ab = t.closest('[data-nb-abrir]'); if (ab) { if (estado.activo !== ab.dataset.nbAbrir) activar(ab.dataset.nbAbrir); const b = ponerBarraNotas('.nb-nota, [data-nb-nota]'); if (b) b.scrollIntoView({ block: 'nearest' }); return; }
    const barra = t.closest('.nb-barra');
    if (barra) {
      const ref = barra.dataset.nb, prev = N.notaDe(notasGuardadas(), ref);
      const co = t.closest('[data-nb-color]'); if (co) { const c = co.dataset.nbColor, quita = prev && prev.color === c; cambiarNota(ref, { color: quita ? null : c }, `[data-nb-color="${c}"]`, quita ? 'Subrayado quitado.' : `Subrayado en ${NB_NOMBRE[c]}.`); return; }
      if (t.closest('[data-nb-nota]')) { nbEditar = nbEditar === ref ? null : ref; ponerBarraNotas(nbEditar ? '#nb-texto' : '[data-nb-nota]'); return; }
      if (t.closest('[data-nb-cancelar]')) { nbEditar = null; ponerBarraNotas('[data-nb-nota]'); return; }
      if (t.closest('[data-nb-copiar]')) {
        const st = barra.querySelector('.nb-estado');
        copiarTexto(N.citaVerso(D, ref, N.textoVerso(D, ref))).then(ok => { if (st) st.textContent = ok ? `Cita copiada: ${N.refLegible(D, ref)}.` : 'No se pudo copiar en este navegador.'; });
        return;
      }
      if (t.closest('[data-nb-quitar]')) { nbDeshacer = prev ? { ref, e: prev } : null; nbEditar = null; guardarNotas(N.quitarNota(notasGuardadas(), ref)); refrescarVerso(ref); ponerBarraNotas('[data-nb-nota]', 'Subrayado y nota quitados. <button type="button" class="enlace-boton" data-nb-deshacer>Deshacer</button>'); return; }
      if (t.closest('[data-nb-deshacer]') && nbDeshacer && nbDeshacer.ref === ref) { const d = nbDeshacer; nbDeshacer = null; cambiarNota(ref, { color: d.e.color || null, nota: d.e.nota || null }, '[data-nb-nota]', 'Recuperado.'); return; }
      return;
    }
    const fi = t.closest('[data-nb-filtro]'); if (fi) { nbF.color = fi.dataset.nbFiltro; refrescarListaNotas(); return; }
    if (t.closest('[data-nb-exportar]')) { exportarNotasArchivo(); return; }
    if (t.closest('[data-nb-copiar-todo]')) { copiarTexto(N.textoNotas(D, N.listarNotas(notasGuardadas(), nbF).filter(x => refOk(x.ref)))).then(ok => nbEstadoVista(ok ? 'Notas copiadas como texto (las que muestra el filtro).' : 'No se pudo copiar en este navegador.')); }
  });
  document.addEventListener('submit', e => {
    const f = e.target.closest && e.target.closest('[data-nb-form]'); if (!f) return;
    e.preventDefault();
    const ref = f.closest('.nb-barra').dataset.nb, txt = f.querySelector('#nb-texto').value;
    nbEditar = null; cambiarNota(ref, { nota: txt }, '[data-nb-nota]', txt.trim() ? 'Nota guardada.' : 'Nota vacía: no se guarda.');
  });
  document.addEventListener('change', e => {
    if (e.target.id === 'nb-connota') { nbF.conNota = e.target.checked; refrescarListaNotas(); }
    else if (e.target.id === 'nb-archivo') importarNotasArchivo(e.target);
  });
  document.addEventListener('input', e => {
    if (e.target.id === 'nb-q') { nbF.q = e.target.value; refrescarListaNotas(); }
    else if (e.target.id === 'gl-q') { estado.glQ = e.target.value; const l = document.getElementById('gl-lista'); if (l) l.innerHTML = glosarioListaHTML(); }
  });
  document.addEventListener('keydown', e => {
    const barra = e.target.closest && e.target.closest('.nb-barra'); if (!barra) return;
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && e.target.id === 'nb-texto') { e.preventDefault(); e.target.form.requestSubmit(); return; }
    if (e.key !== 'Escape') return;
    e.preventDefault();
    if (nbEditar) { nbEditar = null; ponerBarraNotas('[data-nb-nota]'); return; }
    const k = estado.activo; activar(k); const vn = main.querySelector(`.vers[data-v="${k}"] .vn`); if (vn) vn.focus();
  });

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
      ${EXPL() && !estado.comparar ? `<label class="chip-check expl-interruptor" title="Subraya con un punteado las palabras, medidas y costumbres que tienen explicación"><input type="checkbox" name="explicaciones" ${explOn() ? 'checked' : ''}><span>Explicaciones</span></label>` : ''}
    </div>${estado.escuchar ? reproductorHTML() : ''}`;
  }

  /* ---------- Explicaciones: tarjeta de un término, aviso de pasaje difícil y glosario ---------- */
  const TIPO_TERMINO = { palabra: 'Palabra antigua', medida: 'Medida', concepto: 'Costumbre o concepto' };
  const IDIOMA_TXT = { en: 'en inglés', de: 'en alemán', fr: 'en francés', la: 'en latín', it: 'en italiano', pt: 'en portugués' };
  const certezaExplHTML = c => c === 'externa' ? '<span class="etiqueta externa">Fuente externa</span>' : insignia(c);
  // Una fuente de explicación: la cita bíblica respeta la lectura en orden; lo de fuera de la Biblia lleva «Fuente externa».
  function fuenteExplHTML(f) {
    if (!f || typeof f !== 'object') return '';
    if (f.tipo === 'biblia') {
      const c = N.citaFuente(ACC(), f, ref => N.rangoPlegado(CONT(), perfil(), ref));
      if (c.bloqueada) return `<li class="expl-fuente bloqueada">${ICO_CANDADO}${esc(f.ref)} · <span class="meta">se verá al llegar</span></li>`;
      return `<li class="expl-fuente">${refHTML(f.ref)}${c.cita ? `<blockquote>«${esc(c.cita)}»</blockquote>` : ''}</li>`;
    }
    const idioma = f.idioma && f.idioma !== 'es' ? ` <span class="meta">(${esc(IDIOMA_TXT[f.idioma] || f.idioma)})</span>` : '';
    const txt = f.tipo === 'rae' ? `${f.obra || 'Diccionario de la lengua española (RAE)'}, «${f.entrada || ''}»`
      : f.tipo === 'diccionario' ? `${f.obra || ''}${f.autor ? ` (${f.autor})` : ''}, «${f.entrada || ''}»`
      : `${f.autor ? f.autor + ', ' : ''}${f.obra || ''}${f.entrada ? `, «${f.entrada}»` : ''}`;
    return `<li class="expl-fuente">${urlSegura(f.url) ? extLink(f.url, txt) : `${esc(txt)} <span class="etiqueta externa">Fuente externa</span>`}${idioma}</li>`;
  }
  function abrirTermino(id) {
    const E = EXPL(), t = N.termino(E, id); if (!t) return;
    if (!N.terminoAccesible(E, ACC(), id)) { abrirBloqueada('Término sin descubrir', 'Este término aparece más adelante en la lectura. Su explicación se verá cuando llegues.'); return; }
    const c = t.calculo;
    const calc = c ? `<section class="bloque expl-calculo"><h3>Equivalencia actual</h3>
        <p class="cifra">${esc(c.resultado)} ${insignia('calculo')}</p>
        <details><summary>Cómo se calcula</summary><ol>${(c.pasos || []).map(x => `<li>${esc(x)}</li>`).join('')}</ol>
          ${(c.supuestos || []).length ? `<h4>Supuestos</h4><ul>${c.supuestos.map(x => `<li>${esc(x)}</li>`).join('')}</ul>` : ''}
          ${c.fuente ? `<p class="meta">Fuente del cálculo:</p><ul class="expl-fuentes">${fuenteExplHTML(c.fuente)}</ul>` : ''}</details></section>` : '';
    abrirDetalle(t.lema || id, `<p class="meta">${esc(TIPO_TERMINO[t.tipo] || 'Explicación')}</p>
      <p class="expl-texto">${esc(N.textoTermino(t, perfil()))}</p>
      <p>${certezaExplHTML(t.certeza)}</p>
      ${calc}
      <section class="bloque"><h3>Fuentes</h3><ul class="expl-fuentes">${(t.fuentes || []).map(fuenteExplHTML).join('')}</ul></section>
      <p class="meta">Explicación redactada por el proyecto a partir de estas fuentes; no forma parte del texto bíblico.</p>`);
  }
  // Aviso plegable al inicio del pasaje (el niño ve solo el texto `nino`, y nada si su perfil pliega esa parte).
  function dificilesHTML(p) {
    const xs = N.dificilesDe(EXPL(), p, ACC(), perfil(), CONT()); if (!xs.length) return '';
    const nino = esNinoActivo();
    return xs.map(x => `<details class="dificil" data-dificil="${esc(x.id)}">
      <summary><span class="dificil-cab">${ICO_CONT}<strong>Pasaje difícil</strong>${nino ? '' : ': qué dice el texto y qué posturas hay'}</span><span class="dificil-ref">${esc(x.titulo)} · ${esc(x.refs)}</span></summary>
      <div class="dificil-cuerpo">${nino ? `<p>${esc(x.nino)}</p>` : `
        <h3>Qué dice el texto</h3><ul class="dificil-dice">${(x.dice || []).map(c => `<li>${refHTML(c.ref)}<blockquote>«${esc(c.cita)}»</blockquote></li>`).join('')}</ul>
        <h3>Posturas</h3><ul class="dificil-posturas">${(x.posturas || []).map(s => `<li><p>${esc(s.resumen)}</p><ul class="expl-fuentes">${fuenteExplHTML(s.fuente)}</ul></li>`).join('')}</ul>
        <p class="meta">Se presentan las lecturas con su fuente, sin decidir por el lector. ${certezaExplHTML(x.certeza)}</p>`}</div></details>`).join('');
  }
  const glosarioListaHTML = () => {
    const xs = N.glosario(EXPL(), ACC(), estado.glQ || '', plegadoRef);
    if (!xs.length) return `<p class="vacio-txt">${estado.glQ ? 'Ningún término coincide con la búsqueda.' : 'Aún no aparece ningún término con explicación en lo que leíste.'}</p>`;
    return `<ul class="glosario">${xs.map(x => `<li><button type="button" class="enlace-boton" data-termino="${esc(x.id)}">${esc(x.termino.lema || x.id)}</button>
      <span class="meta">${esc(TIPO_TERMINO[x.termino.tipo] || '')} · desde ${esc(x.primera)}</span></li>`).join('')}</ul>`;
  };
  // Sección «Glosario» de la vista Fuentes: solo lo que ya apareció en lo accesible.
  const glosarioHTML = () => EXPL() ? `<section id="glosario" aria-labelledby="t-glosario"><h2 id="t-glosario">Glosario</h2>
      <p>Palabras antiguas, medidas y costumbres que ya aparecieron en lo que leíste. Toca una para ver su explicación y sus fuentes. Lo que viene más adelante aparecerá al llegar.</p>
      <p class="gl-buscar"><label for="gl-q" class="sr">Buscar en el glosario</label><input type="search" id="gl-q" placeholder="Buscar en el glosario" value="${esc(estado.glQ || '')}" autocomplete="off"></p>
      <div id="gl-lista" aria-live="polite">${glosarioListaHTML()}</div></section>` : '';
  function compararHTML(p) {
    const orden = ['rv', 'he', 'gr'], sel = columnas(), vis = orden.filter(c => sel.includes(c));
    const filas = N.alinearOriginales(D, p, ORIG.o, ORIG.g);
    const cargando = vis.some(c => (c === 'he' && ORIG.est.o !== 'ok') || (c === 'gr' && ORIG.est.g !== 'ok'));
    const elegir = `<fieldset class="cmp-cols"><legend>Columnas${estrecho() ? ' <span class="meta">(dos en pantallas estrechas)</span>' : ''}</legend>${orden.map(c => `<label class="chip-check"><input type="checkbox" data-col="${c}" ${vis.includes(c) ? 'checked' : ''}><span>${COLS[c].t}</span></label>`).join('')}</fieldset>`;
    const cab = vis.map(c => `<div class="cmp-cab"><span class="cmp-col-t">${esc(COLS[c].t)}</span><span class="cmp-fuente">${esc(COLS[c].fuente())}</span>${c === 'he' ? estadoCarga('o') : c === 'gr' ? estadoCarga('g') : ''}</div>`).join('');
    const vars = new Set(ORIG.o ? filas.filter(f => N.variantesDe(ORIG.o, [f.ref]).length).map(f => f.ref) : []);
    let capPrev = null;
    const accs = filas.map(f => accionDe(f.ref)), NTc = notasGuardadas().versos;
    const cuerpo = filas.map((f, j) => {
      const k = `${f.cap}:${f.n}`, x = accs[j];
      if (x.accion === 'plegar') { // una sola fila plegada por tramo, con sus números
        if (j && accs[j - 1].accion === 'plegar' && accs[j - 1].marca === x.marca) return '';
        const g = filas.filter((y, i) => i >= j && accs[i].marca === x.marca).map(y => ({ cap: y.cap, n: y.n }));
        const marca = f.cap !== capPrev && j ? `<div class="cmp-capitulo">Capítulo ${f.cap}</div>` : ''; capPrev = g[g.length - 1].cap;
        return `${marca}<div class="cmp-fila cmp-plegada"><div class="cmp-num">${g.length > 1 ? `${f.n}–${g[g.length - 1].n}` : f.n}</div><div class="cmp-celda">${plegadoHTML(g, x.marca)}</div></div>`;
      }
      const marca = (f.cap !== capPrev && j ? `<div class="cmp-capitulo">Capítulo ${f.cap}</div>` : '') + (x.accion === 'aviso' && !(j && accs[j - 1].marca === x.marca) ? `<div class="cmp-aviso">${avisoContHTML(x.marca)}</div>` : '')
        + (x.accion === 'desplegado' && !(j && accs[j - 1].marca === x.marca) ? `<div class="cmp-aviso">${desplegadoHTML(x.marca)}</div>` : ''); capPrev = f.cap;
      const nota = x.accion === 'nota' && !(filas[j + 1] && accs[j + 1].marca === x.marca) ? `<div class="cmp-aviso">${notaContHTML(x.marca)}</div>` : '';
      const celda = c => {
        const t = c === 'rv' ? f.rv : c === 'he' ? f.he : f.gr;
        const pend = (c === 'he' && ORIG.est.o === 'cargando') || (c === 'gr' && ORIG.est.g === 'cargando');
        const attrs = c === 'he' ? ' lang="he" dir="rtl"' : c === 'gr' ? ' lang="grc"' : '';
        const num = c === 'he' && f.heNum ? `<span class="num-heb" title="En la Biblia hebrea este versículo lleva otro número">Heb. ${esc(f.heNum)}</span>` : '';
        const nt = c === 'rv' ? NTc[f.ref] : null; // subrayado del lector (Tu nota se ve y edita en la lectura normal)
        const nfu = c === 'he' ? f.heNota : c === 'gr' ? f.grNota : null; // nota de la fuente (grafías, ketiv/qere, cortes de versículo)
        const notaFu = nfu ? `<details class="cmp-nota-fuente"><summary>Nota sobre este texto</summary><p>${esc(nfu)}</p></details>` : '';
        return `<div class="cmp-celda cmp-${c}">${num}${t ? `<p class="cmp-txt"${attrs}>${nt && nt.color ? `<span class="nb-sub nb-${nt.color}">${esc(t)}</span>${nbSrHTML(nt)}` : esc(t)}${nt && nt.nota ? ' <span class="nb-chip" title="Tienes una nota en este versículo">' + ICO_NOTA + '<span class="sr">Tienes una nota en este versículo.</span></span>' : ''}</p><button type="button" class="hablar-btn" data-hablar="${COLS[c].idioma}|${k}" aria-label="Escuchar el versículo ${f.n} en ${esc(COLS[c].t.toLowerCase())}"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 8h3l4-3.5v11L7 12H4zM14 7.5a3.5 3.5 0 010 5"/></svg></button>${notaFu}` : `<p class="cmp-vacio">${pend ? '…' : c === 'rv' && f.nota ? esc(f.nota) : c === 'he' && f.heFalta ? esc(f.heFalta) : c === 'gr' && f.grFalta ? esc(f.grFalta) : 'Sin texto en los datos'}</p>`}</div>`;
      };
      return `${marca}<div class="cmp-fila${habla.k === k ? ' sonando' : ''}${vars.has(f.ref) ? ' con-variante' : ''}" data-v="${k}"><div class="cmp-num">${f.n}${vars.has(f.ref) ? marcaVariante(f.ref, f.n) : ''}</div>${vis.map(celda).join('')}</div>${nota}`;
    }).join('');
    return `<section class="comparar" aria-label="Comparar textos lado a lado" style="--cols:${vis.length}">${elegir}
      <div class="cmp-tabla" role="group" aria-busy="${cargando}"><div class="cmp-fila cmp-cabecera"><div class="cmp-num" aria-hidden="true"></div>${cab}</div>${cuerpo || '<p class="vacio-txt">Este pasaje no tiene versículos en los datos.</p>'}</div>
      <p class="meta">Versos alineados según la numeración de la Reina-Valera; «Heb.» indica el número en la Biblia hebrea cuando difiere. El hebreo y el griego vienen de fuentes externas, con su licencia en <a href="#fuentes">Fuentes</a>.</p></section>`;
  }

  /* ---------- Variantes y testigos ---------- */
  const TIPO_TESTIGO = { codice: 'Códice', rollo: 'Rollo', papiro: 'Papiro', pentateuco_samaritano: 'Pentateuco samaritano' };
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
  function testigoHTML(t, p) {
    const datos = [t.idioma, t.fecha ? `${t.fecha}${t.fecha_certeza ? ` (${t.fecha_certeza})` : ''}` : '', t.institucion].filter(Boolean).map(esc).join(' · ');
    return `<li class="testigo"><span class="testigo-cab"><strong>${esc(t.nombre || t.id)}</strong><span class="etiqueta">${esc(TIPO_TESTIGO[t.tipo] || t.tipo || 'Testigo')}</span></span>
      ${datos ? `<span class="meta">${datos}</span>` : ''}${t.nota ? `<span class="meta">${esc(t.nota)}</span>` : ''}
      ${urlSegura(t.url) ? `<span>${extLink(t.url, 'Ver el manuscrito')}</span>` : ''}${p ? enlacesRegistroHTML(t, p) : ''}</li>`;
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
    // Versículos sin hebreo o sin griego: una línea por versículo con el motivo de los datos, tal cual.
    const st = N.sinTextoOriginal(ORIG.o, ORIG.g, refs);
    const sinTxt = st.length ? `<p class="meta">Sin texto original en ${st.length === 1 ? 'un versículo' : st.length + ' casos'}:</p><ul class="sin-texto-orig">${st.map(x => `<li><strong>${esc(x.ref)} · ${x.idioma === 'he' ? 'hebreo' : 'griego'}</strong>: ${esc(x.nota)}</li>`).join('')}</ul>` : '';
    return `${vs.length ? `<p class="meta">${vs.length === 1 ? 'Una variante' : vs.length + ' variantes'} entre manuscritos:</p>${vs.map(varianteHTML).join('')}` : `<p class="contexto">Los datos no registran variantes en ${estado.activo ? 'este versículo' : 'este pasaje'}.</p>`}
      ${ts.length ? `<p class="meta">Manuscritos que contienen ${estado.activo ? 'este versículo' : 'parte de este pasaje'}:</p><ul class="testigos">${ts.map(t => testigoHTML(t, estado.pasaje)).join('')}</ul>` : '<p class="vacio-txt">Ningún manuscrito de los datos cubre este pasaje.</p>'}${sinTxt}${QUE_ES}`;
  }
  /* ---------- El manuscrito: el registro real de donde sale el texto (datos/manuscritos.js, bajo demanda) ---------- */
  // Plegado al final del pasaje (Leer y Comparar): no compite con la lectura, y la imagen (Wikimedia Commons, en línea)
  // solo se pide al abrirlo, para no cargar folios que nadie mira. Rollos y Vaticano: solo enlace, por sus condiciones.
  const MS = { d: null, est: '' };
  const aExt = (u, t) => urlSegura(u) ? `<a href="${esc(urlSegura(u))}" target="_blank" rel="noopener noreferrer">${esc(t)}</a>` : '';
  const EXT = ' <span class="etiqueta externa">Fuente externa</span>';
  function cargarManuscritos() {
    if (MS.est === 'ok' || MS.est === 'cargando') return;
    MS.est = 'cargando';
    cargarScript('datos/manuscritos.js').then(() => { MS.d = window.BIBLIA_MANUSCRITOS || null; MS.est = MS.d ? 'ok' : 'error'; }, () => { MS.est = 'error'; })
      .then(() => { pintarManuscrito(); const a = $('#acompanante'); if (a && a.querySelector('.testigos')) { a.innerHTML = acompHTML(); montarMapas(a); } });
  }
  function pintarManuscrito() { const c = main.querySelector('[data-manuscrito] .ms-cuerpo'); if (c && estado.pasaje) c.innerHTML = manuscritoCuerpoHTML(estado.pasaje); }
  function abrirManuscrito() {
    cargarManuscritos();
    if (ORIG.est.o === '') cargarOriginales('o', '[data-manuscrito] > summary'); // los rollos salen de originales.js; al repintar, el foco vuelve aquí
    pintarManuscrito();
  }
  const enlaceRollo = (r, sinFicha) => r.nivel === 'fragmento'
    ? r.fragmentos.map(f => f.imagenes.map(x => aExt(x.url, `Ver el fragmento${r.fragmentos.length > 1 || f.imagenes.length > 1 ? ' ' + f.abegg.replace(/^f/, '') : ''} en la Leon Levy (IAA)`)).join(' · ')).join(' · ')
    : r.nivel === 'lamina' ? `${aExt(r.laminas[0].url, `Ver láminas del rollo${r.laminas.length > 1 ? ` (1 de ${r.laminas.length})` : ''}`)}${r.ficha && !sinFicha ? ' · ' + aExt(r.ficha, 'Ficha del rollo') : ''}`
    : r.ficha ? aExt(r.ficha, 'Ficha del rollo') : '';
  // Enlaces al registro de un testigo en la lista «Manuscritos que contienen…» (si ya están cargados los manuscritos).
  function enlacesRegistroHTML(t, p) {
    if (MS.est !== 'ok') return '';
    if (t.id === 'leningrado') { const fs = N.foliosDePasaje(MS.d, D, p); return fs.length ? `<span>${fs.map(f => aExt(f.pagina, `Folio ${f.nombre} en Wikimedia Commons`)).join(' · ')}${EXT}</span>` : ''; }
    if (t.id === 'vaticano') { const v = N.vaticanoDeLibro(MS.d, N.libroDe(p)); return v ? `<span>${aExt(v.url, `Inicio de ${N.nombreLibro(D, N.libroDe(p))} (BAV)`)}${EXT}</span>` : ''; }
    if (t.tipo === 'rollo') { const r = N.rollosDePasaje(MS.d, ORIG.o, D, p).find(x => x.id === t.id); return r && r.nivel !== 'ficha' ? `<span>${enlaceRollo(r, true)}${EXT}</span>` : ''; }
    return '';
  }
  function manuscritoHTML(p) {
    return `<details class="plegable manuscrito" data-manuscrito${estado.msAbierto ? ' open' : ''}><summary>El manuscrito<span class="ms-sub">de dónde sale este texto</span></summary>
      <div class="ms-cuerpo">${estado.msAbierto ? manuscritoCuerpoHTML(p) : ''}</div></details>`;
  }
  function manuscritoCuerpoHTML(p) {
    if (MS.est !== 'ok') return MS.est === 'error'
      ? '<p class="vacio-txt">No se pudieron cargar los datos de manuscritos (datos/manuscritos.js). <button type="button" class="enlace-boton" data-ms-reintentar>Reintentar</button></p>'
      : '<p class="meta">Cargando…</p>';
    const L = MS.d.leningrado || {}, lb = N.libroDe(p), libro = N.nombreLibro(D, lb);
    const fs = N.foliosDePasaje(MS.d, D, p);
    const folio = f => {
      const img = f.uso === 'mostrar' && urlSegura(f.miniatura)
        ? `<button type="button" class="rec-marco ms-marco" data-visor="ms:${esc(f.id)}" aria-label="Ampliar el folio ${esc(f.nombre)} del Códice de Leningrado"><img class="rec-img" src="${esc(f.miniatura)}" alt="Folio ${esc(f.nombre)} del Códice de Leningrado, con el texto hebreo de ${esc(f.muestra)}" loading="lazy" decoding="async"${f.ancho_miniatura && f.alto_miniatura ? ` width="${f.ancho_miniatura}" height="${f.alto_miniatura}"` : ''}><span class="rec-ampliar">${ICO_AMPLIAR}</span></button>` : '';
      return `<figure class="ms-folio">${img}<figcaption class="rec-pie">
        <span class="rec-datos"><span class="etiqueta rec-rotulo rec-registro">Registro histórico</span> <strong>Códice de Leningrado</strong>, folio ${esc(f.nombre)}${L.fecha ? ` · ${esc(L.fecha)}` : ''}${L.institucion ? ` · ${esc(L.institucion)}` : ''}</span>
        <span>En este folio: ${esc(f.muestra)}${f.otros ? '; la página trae también texto de otros pasajes' : ''}.</span>
        <span class="rec-atrib">Imagen: Wikimedia Commons · ${esc(f.licencia || 'licencia sin indicar')}${f.credito ? ` · origen: ${urlSegura(f.credito) ? aExt(f.credito, 'manuscripts.sefaria.org') : esc(f.credito)}` : ''} · ${aExt(f.pagina, 'Ver en Commons')}${EXT}</span></figcaption></figure>`;
    };
    const rs = ORIG.est.o === 'ok' ? N.rollosDePasaje(MS.d, ORIG.o, D, p) : [];
    const rollos = ORIG.est.o === 'ok'
      ? (rs.length ? `<ul class="ms-enlaces">${rs.map(r => `<li><strong>${esc(r.nombre)}</strong><span class="meta">${[r.fecha, r.institucion].filter(Boolean).map(esc).join(' · ')}</span><span>${enlaceRollo(r)}${EXT}</span></li>`).join('')}</ul>`
        : '<p class="meta">Ningún rollo de los datos conserva versículos de este pasaje.</p>')
      : ORIG.est.o === 'error' ? `<p class="vacio-txt">${NO_DISP.o} <button type="button" class="enlace-boton" data-reintentar="o">Reintentar</button></p>` : '<p class="meta">Cargando…</p>';
    const v = N.vaticanoDeLibro(MS.d, lb), V = MS.d.vaticano || {};
    return `${fs.length ? fs.map(folio).join('') : '<p class="meta">Los datos no tienen el folio de este pasaje.</p>'}
      <p class="meta">De este códice sale el texto hebreo de la app. Qué versículos trae cada folio lo dice la descripción de Commons; la imagen es del manuscrito, no una ilustración.</p>
      <h3 class="ms-sub-t">Rollos del mar Muerto</h3>${rollos}
      <p class="meta">Imágenes de la Leon Levy Dead Sea Scrolls Digital Library (Autoridad de Antigüedades de Israel): solo enlace, porque sus condiciones no permiten mostrarlas aquí.</p>
      ${v ? `<h3 class="ms-sub-t">Códice Vaticano</h3><ul class="ms-enlaces"><li><span>${aExt(v.url, `Ver el inicio de ${libro} en el Códice Vaticano (BAV)`)}${EXT}</span>
        <span class="meta">${esc(V.nombre || 'Códice Vaticano')} · ${esc(V.institucion || 'Biblioteca Apostólica Vaticana')} · p. ${esc(v.pagina)}. Solo enlace: la BAV no permite mostrar sus imágenes.</span>${v.nota ? `<span class="meta">${esc(v.nota)}</span>` : ''}</li></ul>` : ''}`;
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
    // Lo plegado para el perfil no se lee en voz alta.
    const cola = ks.filter(k => !plegadoRef(`${lb} ${k}`)).map(k => ({ k, t: N.textoParaVoz(textoDe(id, `${lb} ${k}`), id) })).filter(x => x.t);
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
  const imagenesPasaje = p => { if (!p) return []; const ks = N.versiculosDe(D, p).map(v => v.clave); return permitidos(N.imagenesDe(R, ks), ks); };
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
    const ksP = N.versiculosDe(D, p).map(v => v.clave); // el permiso se mira en todo el pasaje, como en el carrusel
    const objs = permitidos(A.objetos.concat(A.imagenes), ksP);
    A.medios = permitidos(A.medios, ksP);
    if (objs.length) html += sec('Imágenes y objetos', `<ul class="rec-lista">${objs.map(recItemHTML).join('')}</ul>`, I('M3 5h14v10H3zM3 13l4-4 3 3 2-2 5 5'));
    if (A.medios.length) html += sec('Videos y audio', `<ul class="rec-lista medios">${A.medios.map(medioHTML).join('')}</ul>`, I('M7 5v10l8-5z'));
    return html;
  }
  function mapasAntiguosHTML() {
    // Mapas antiguos: cuando su primer tramo de referencia (p. ej. «Ex 12-19») ya es accesible entero.
    const ms0 = N.mapasAntiguos(R), ms = ms0.filter(f => { const rs = rangosRec(f); return ACC().todo || (rs ? ACC().clave(rs[0][0]) && ACC().clave(rs[0][1]) : recOk(f)); });
    if (!ms.length) return ms0.length ? `<section class="mapas-antiguos"><h2>Mapas antiguos</h2>${bloqueadoHTML('Los mapas antiguos se irán mostrando cuando llegues a los relatos que dibujan.')}</section>` : '';
    const con = ms.filter(f => f.imagen), sin = ms.filter(f => !f.imagen);
    return `<section class="mapas-antiguos" aria-labelledby="t-mapas-antiguos"><h2 id="t-mapas-antiguos">Mapas antiguos</h2>
      <p class="sub">Mapas impresos entre los siglos XVI y XIX: registran cómo se dibujaba entonces la geografía del relato, no cómo era en tiempos bíblicos. Pulsa uno para verlo ampliado.</p>
      ${con.length ? `<ul class="rec-galeria">${con.map(f => `<li><button type="button" class="rec-marco" data-visor="${esc(f.id)}" aria-label="Ampliar: ${esc(f.titulo)}">${imgRec(f, 'rec-img')}</button>
        <p class="rec-pie">${pieRec(f, true)}</p></li>`).join('')}</ul>` : ''}
      ${sin.length ? `<h3>Solo enlace (${sin.length})</h3><p class="meta">Sin imagen con licencia que permita copiarla: se enlaza a la institución que la conserva.</p><ul class="rec-lista">${sin.map(recItemHTML).join('')}</ul>` : ''}</section>`;
  }
  const TIPO_REC_TXT = { arte: 'Arte', reconstruccion: 'Reconstrucciones modernas', ilustracion: 'Ilustraciones modernas', arqueologia: 'Objetos históricos', mapa_antiguo: 'Mapas antiguos', video: 'Videos', audio: 'Audio' };
  function creditosHTML() {
    const fs = permitidos(N.recursos(R));
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
  // Folio de Leningrado en el visor: mismo pie que un recurso, rotulado «Registro histórico».
  function folioVisor(id) {
    const m = /^ms:(.+)$/.exec(String(id || '')); if (!m || MS.est !== 'ok') return null;
    const L = MS.d.leningrado || {}, f = (L.folios || {})[m[1]];
    if (!f || f.uso !== 'mostrar' || !urlSegura(f.miniatura)) return null;
    return { id, tipo: 'registro', titulo: `Códice de Leningrado, folio ${N.nombreFolio(m[1])}`, imagen: f.miniatura, ancho: f.ancho_miniatura, alto: f.alto_miniatura,
      fecha: L.fecha, licencia: f.licencia, institucion: L.institucion, url_fuente: f.pagina, atribucion: `Imagen: Wikimedia Commons${f.credito ? ' · origen: ' + f.credito : ''}`,
      descripcion: 'Página del manuscrito hebreo del que sale el texto de la app.' };
  }
  function abrirVisor(id) {
    const f = recPorId(id) || folioVisor(id); if (!f || !f.imagen || !visorDlg || (esNinoActivo() && f.sensible)) return;
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
    const atajos = N.atajosLinea(D).filter(a => personaOk(a.desde) && personaOk(a.hasta)); // líneas que ya se pueden recorrer leyendo
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
      <p class="meta" id="arbol-aviso" aria-live="polite">${esc(estado.aviso) || (estado.lineaSolo ? '' : `${[...N.indice(D).personas.keys()].filter(personaOk).length} personas hasta donde has leído. Las ramas empiezan plegadas: despliégalas con ▸ o busca un nombre para ir a él.`)}</p>
      <div id="arbol"${estado.mujeres ? ' class="resaltar-mujeres"' : ''}>${arbolHTML()}</div>`;
  }
  function resultadosHTML() {
    if (!estado.q) return '';
    const r = N.buscarAccesible(D, ACC(), estado.q, 20); // solo quien ya apareció en lo accesible
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
  // Vida vista desde lo accesible: años vividos y nacimiento/muerte (cálculo) solo con versículos ya accesibles.
  function vidaOk(id, tr, combo) {
    const v = N.vida(D, id, tr, combo), A = ACC();
    const c = v.nacimiento !== null ? N.vidaAccesible(D, Object.assign({ persona: id }, v), A) : null;
    return { total: v.total && N.edadAccesible(A, v.total) ? v.total : null, nacimiento: c ? c.nacimiento : null, muerte: c ? c.muerte : null, evNac: c ? c.evNac : null, evMuerte: c ? c.evMuerte : null };
  }
  function vidaHTML(id) {
    const C = N.crono(D), ts = trads();
    let vs = ts.map(tr => ({ tr, v: vidaOk(id, tr, C ? comboDe(tr) : null) })).filter(x => x.v.total || x.v.nacimiento !== null);
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
    const us = unionesOk(n), parejas = us.filter(u => u.pareja);
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
    const us = unionesOk(n);
    if (us.length < 2) return n.hijos.map(fila).join('');
    return us.filter(u => u.hijos.length).map(u => ramaHTML(u, n, prof + 1) + u.hijos.map(fila).join('')).join('');
  }
  const bloqueHTML = (n, prof) => filaHTML(n, prof) + (n.hijos.length && estado.abiertos.has(n.id) ? hijosHTML(n, prof) : '');
  // Nodo para una persona de la línea aunque no sea nodo del bosque (p. ej. si la ruta pasa por una madre).
  function nodoLinea(id, padreId) {
    const n = N.nodoArbol(D, id), I = N.indice(D);
    const vinculos = (I.padres.get(id) || []).filter(x => x.de === padreId);
    return n ? Object.assign(podarArbol(n), { vinculos: padreId ? vinculos : n.vinculos }) : { id, vinculos, hijos: [], conyuges: (I.conyuges.get(id) || []).filter((r, i, a) => a.findIndex(x => x.otro === r.otro) === i), madres: [] };
  }
  function lineaHTML(at) {
    const M = N.mapaArbol(D), gen = (id, i) => { const x = M.nodos.get(id); return x ? x.prof : i; };
    let html = at.ruta.map((id, i) => filaHTML(nodoLinea(id, at.ruta[i - 1]), i, { solo: true, gen: gen(id, i) })).join('');
    if (at.extra.length) {
      const fin = at.ruta[at.ruta.length - 1], nf0 = N.nodoArbol(D, fin), nf = nf0 && podarArbol(nf0), prof = at.ruta.length - 1, g0 = gen(fin, prof) + 1;
      const fila = h => filaHTML(h, prof + 1, { solo: true, gen: g0 });
      html += nf ? hijosHTML(nf, prof, fila) : at.extra.map(id => fila(nodoLinea(id, fin))).join('');
    }
    return `<ul class="arbol" aria-label="Línea ${esc(tituloAtajo(at))}">${html}</ul>`;
  }
  // Árbol podado a lo accesible: sin personas (ni parejas) que aún no han aparecido en la lectura.
  const podarArbol = n => Object.assign({}, n, { hijos: (n.hijos || []).filter(h => personaOk(h.id)).map(podarArbol), conyuges: (n.conyuges || []).filter(c => personaOk(c.otro) && refOk(c.ref)),
    madres: (n.madres || []).filter(r => personaOk(r.de) && refOk(r.ref)), vinculos: (n.vinculos || []).filter(r => refOk(r.ref)) });
  // Parejas de un nodo: la madre (o cónyuge) aún no aparecida en lo accesible queda como «madre no indicada».
  const unionesOk = n => { const us = N.uniones(D, n), out = [];
    us.forEach(u => { const ok = !u.pareja || personaOk(u.pareja); const x = ok ? u : Object.assign({}, u, { pareja: null, vinculo: null });
      const sin = !x.pareja && out.find(y => !y.pareja); if (sin) sin.hijos = sin.hijos.concat(x.hijos); else out.push(x); });
    return out; };
  const atajoOk = at => at && Object.assign({}, at, { ruta: at.ruta.filter(personaOk), extra: (at.extra || []).filter(personaOk) });
  function arbolHTML() {
    const bosque = N.construirBosque(D).filter(r => personaOk(r.id)).map(podarArbol);
    if (!bosque.length) return N.construirBosque(D).length ? bloqueadoHTML('El árbol crece a medida que lees en orden: aún no ha aparecido nadie.') : '<p>No hay relaciones en los datos.</p>';
    const g = estado.vistaArbol === 'grafico';
    if (estado.lineaSolo) {
      const at = atajoOk(N.atajosLinea(D).find(a => a.id === estado.lineaSolo));
      if (at && at.ruta.length) return g ? lienzoHTML(gaLinea(at), `Línea ${tituloAtajo(at)}`) : lineaHTML(at);
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
    const linea = N.lineaPrincipal(D), us = unionesOk(n), parejas = us.filter(u => u.pareja);
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
    const ids = N.sinParentesco(D).filter(personaOk);
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
    const e0 = N.edad(D, id, tipo, trad), e = e0 && N.edadAccesible(ACC(), e0) ? e0 : null; // edad de un versículo aún no accesible: «—»
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
    const L = N.lineaAccesible(D, combo, ACC()); // solo sucesos e hitos ya accesibles
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
      ${ACC().todo ? '' : `<p class="meta">${ICO_CANDADO} Solo los sucesos hasta donde has leído; los siguientes aparecerán al avanzar.</p>`}
      ${secs || '<p class="vacio-txt">Aún no hay sucesos en lo que has leído.</p>'}`;
  }
  // Tarjeta de un suceso: año(s), cadena de pasos desde Adán (plegada), supuestos y quién vivía entonces.
  function abrirEvento(id) {
    const C = N.crono(D), ev = C && C.porId.get(id); if (!ev) return;
    if (!refOk(ev.ref)) { abrirBloqueada('Suceso sin descubrir', 'Este suceso ocurre más adelante en la lectura.'); return; }
    const e = eleg(), comparar = estado.trad === 'ambas';
    const bloque = tr => {
      const combo = N.combinacion(D, tr, e), a = N.anioEvento(D, id, combo), cad = N.cadenaEvento(D, id, combo), dsp = N.despuesDe(D, id, combo), vivos = N.vivosEn(D, a, combo).filter(v => personaOk(v.persona));
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
      ${(ev.personas || []).filter(personaOk).length ? `<ul class="chips">${ev.personas.filter(personaOk).map(p => `<li>${btnPersona(p)}</li>`).join('')}</ul>` : ''}
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
    const C = N.crono(D), combo = comboDe(trad), m = N.vidasCrono(D, combo), A = ACC();
    const filas = [...m.values()].map(x => N.vidaAccesible(D, x, A)).filter(x => x && x.nacimiento !== null).sort((a, b) => a.nacimiento - b.nacimiento);
    const omit = [...m.values()].filter(x => x.nacimiento === null && personaOk(x.persona));
    const aviso = omit.length ? `<p class="meta omitidas">Sin nacimiento calculable en esta combinación (se omiten): ${omit.map(x => esc(nombre(x.persona))).join(', ')}.</p>` : '';
    if (!filas.length) return `<h3>${TRAD_TXT[trad]}</h3><p>Sin datos suficientes.</p>${aviso}`;
    const max = Math.max(1, ...filas.map(f => f.muerte !== null ? f.muerte : f.nacimiento));
    const paso = max > 3000 ? 500 : max > 1200 ? 250 : 100;
    const marcas = []; for (let a = 0; a <= max; a += paso) marcas.push(a);
    const pct = x => (x / max * 100).toFixed(2) + '%';
    const evD = C.eventos.find(N.esDiluvio), dil = evD && refOk(evD.ref) ? N.anioEvento(D, evD.id, combo) : null;
    const marcaDil = dil !== null && dil <= max ? `<span class="diluvio-marca" style="left:${pct(dil)}"></span>` : '';
    return `<h3>${TRAD_TXT[trad]}</h3>
      ${dil !== null ? `<p class="leyenda"><span class="muestra-diluvio" aria-hidden="true"></span> Diluvio ≈ año ${dil} desde Adán ${insignia('calculo')} (${refHTML(evD.ref)}).</p>` : ''}
      <ol class="barras">${filas.map(f => `<li><button type="button" class="barra-fila" data-ev="${esc(f.evNac)}">
        <span class="barra-nombre">${esc(nombre(f.persona))}</span><span class="barra-anos">${f.nacimiento}–${f.muerte !== null ? f.muerte : '?'}</span>
        <span class="pista" aria-hidden="true">${marcaDil}<span class="barra${f.muerte === null ? ' abierta' : ''}" style="left:${pct(f.nacimiento)};width:${f.muerte !== null ? pct(f.muerte - f.nacimiento) : '4px'}"></span></span></button></li>`).join('')}</ol>
      <div class="eje" aria-hidden="true">${marcas.map(a => `<span style="left:${pct(a)}">${a}</span>`).join('')}</div>${aviso}`;
  }
  function tablaHTML() {
    const ts = trads(), orden = N.ordenPatriarcas(D).filter(personaOk), ambas = ts.length === 2;
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
    const gs = N.edadesEnEventoPorPersona(D).filter(g => personaOk(g.persona)).map(g => Object.assign({}, g, { items: g.items.filter(x => refOk(x.ref)) })).filter(g => g.items.length);
    return `<section class="eventos" aria-labelledby="ev-t"><h2 id="ev-t">Edades en momentos del relato</h2>
      ${gs.length ? `<p class="meta">Edad que el texto da a una persona en un momento concreto, en orden de versículo. Si la Septuaginta da otra cifra, se indica.</p>
        <ul class="eventos-lista">${gs.map(g => `<li><h3>${btnPersona(g.persona)}</h3><ul class="edades-acomp">${g.items.map(eventoHTML).join('')}</ul></li>`).join('')}</ul>`
        : '<p class="vacio-txt">Los datos todavía no traen edades en momentos del relato.</p>'}</section>`;
  }
  function barrasHTML(trad) {
    const v0 = N.vidas(D, trad), filas = v0.filas.filter(f => personaOk(f.id)), omitidas = v0.omitidas.filter(personaOk);
    const aviso = omitidas.length ? `<p class="meta omitidas">Se ${omitidas.length === 1 ? 'omite' : 'omiten'} ${omitidas.length} ${omitidas.length === 1 ? 'persona' : 'personas'} con edades pero sin la cadena completa desde Adán, así que no se pueden situar: ${omitidas.map(id => esc(nombre(id))).join(', ')}.</p>` : '';
    if (!filas.length) return `<p>Sin datos suficientes para ${trad}.</p>${aviso}`;
    const max = Math.max(1, ...filas.map(f => f.muerte !== null ? f.muerte : f.nacimiento));
    const paso = max > 3000 ? 500 : max > 1200 ? 250 : 100;
    const marcas = []; for (let a = 0; a <= max; a += paso) marcas.push(a);
    const pct = x => (x / max * 100).toFixed(2) + '%';
    const dil0 = N.anoDiluvio(D, trad), dil = dil0 && refOk(dil0.ref) ? dil0 : null;
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
        <dt>${insignia('calculo')}</dt><dd>Cifra obtenida por operación aritmética a partir del texto (sumas de edades, años desde Adán). No está escrita como tal.</dd>
        <dt><span class="etiqueta externa">Fuente externa</span></dt><dd>Sale de fuera de la Biblia: un diccionario, una obra de consulta, un museo o un video.</dd></dl></section>
      ${glosarioHTML()}
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

  /* ---------- Catálogo de juego en las fichas: todo lo que se sabe, apariciones y relacionados ---------- */
  const capLegible = c => { const r = N.parseRef(c); return r ? `${N.nombreLibro(D, r.libro)} ${r.cap}` : String(c || ''); };
  const nivelHTML = f => f.npc ? '<span class="nivel-muestra npc" title="Solo aparece en genealogías: personaje no jugable (NPC)">NPC</span> '
    : f.nivel !== null && f.nivel !== undefined && Number.isFinite(+f.nivel) ? `<span class="nivel-muestra" title="Nivel provisional del catálogo: según cuánto texto hay sobre el personaje">Nivel ${+f.nivel}</span> ` : '';
  const avanceTxt = f => `${f.total ? `Leído ${f.leidos} de ${f.total} ${f.total === 1 ? 'pasaje' : 'pasajes'} donde aparece · ` : ''}se desbloquea al terminar ${esc(capLegible(f.capitulo))}`;
  const ICO_COSA = {
    objetos: '<svg class="ico-cosa" viewBox="0 0 40 40" aria-hidden="true"><path d="M7 17h26v14a3 3 0 01-3 3H10a3 3 0 01-3-3z"/><path d="M5 12h30v5H5z"/><path d="M17 23h6"/></svg>',
    escenarios: '<svg class="ico-cosa" viewBox="0 0 40 40" aria-hidden="true"><path d="M3 33l11-15 7 9 5-6 11 12z"/><circle cx="29" cy="10" r="3.5"/></svg>'
  };
  const GRUPO_TXT = { objetos: 'Objeto', escenarios: 'Escenario' };
  const datoCosa = g => g === 'objetos' ? 'objeto' : 'escenario';
  const btnCosa = (g, id) => { const e = ((JUEGO() || {})[g] || {})[id]; return e ? `<button type="button" class="cosa-btn c-${g}" data-${datoCosa(g)}="${esc(id)}">${ICO_COSA[g]}${esc(e.nombre || id)}</button>` : ''; };
  // Imágenes del catálogo de recursos que tocan las apariciones (las que permite el perfil), como miniaturas ampliables.
  function imagenesJuegoHTML(aps) {
    if (!R || !aps.length) return '';
    const ks = [].concat(...aps.map(x => N.versiculosDe(D, { inicio: x.inicio, fin: x.fin || x.inicio }).map(v => v.clave)));
    const fs = permitidos(N.imagenesDe(R, ks), ks).slice(0, 4);
    return fs.length ? `<p class="meta">Imágenes del catálogo de la app que tocan estos versículos (cada una rotulada: arte, reconstrucción o ilustración).</p>
      <ul class="juego-imgs">${fs.map(f => `<li><button type="button" class="juego-img" data-visor="${esc(f.id)}" aria-label="Ampliar: ${esc(f.titulo)}">${imgRec(f, '')}</button><span class="meta">${rotuloRec(f)}</span></li>`).join('')}</ul>` : '';
  }
  // Bloques comunes a las fichas de personaje, objeto y escenario. tipo: 'persona' | 'objetos' | 'escenarios'.
  function bloquesJuegoHTML(e, tipo, id) {
    const JJ = JUEGO();
    const ds = (Array.isArray(e.datos) ? e.datos : []).filter(x => x && x.texto && N.clave(x.ref) !== null && refOk(x.ref));
    const ex = (Array.isArray(e.externo) ? e.externo : []).filter(x => x && x.texto && x.fuente && /^https:\/\//i.test(x.url || ''));
    const aps0 = (Array.isArray(e.apariciones) ? e.apariciones : []).filter(x => x && N.clave(x.inicio) !== null);
    const aps = aps0.filter(x => refOk(x.inicio)), apsOcultas = aps0.length - aps.length;
    const mps = (Array.isArray(e.menciones_posteriores) ? e.menciones_posteriores : []).filter(x => x && N.clave(x.ref) !== null && refOk(x.ref));
    const datoLi = x => plegadoRef(x.ref) ? `<li class="dato plegado"><span class="meta">Dato plegado en este perfil (contenido para personas adultas).</span> ${refHTML(x.ref)}</li>`
      : `<li class="dato"><p class="dato-txt">${esc(x.texto)}</p><p class="dato-ins">${insignia(x.certeza === 'inferido' ? 'inferido' : 'texto', x.ref)}</p>${x.cita ? `<blockquote>${esc(x.cita)}</blockquote>` : ''}</li>`;
    const exLi = x => `<li><span class="etiqueta externa">Fuente externa</span> ${esc(x.texto)} <span class="meta">${esc(x.fuente)} · <a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">abrir la fuente</a></span></li>`;
    const apLi = x => `<li><a class="ref" href="${hrefRef(N.parseRef(x.inicio))}">${esc(rango({ inicio: x.inicio, fin: x.fin || x.inicio }))}</a></li>`;
    // Relacionados: personas, lugares del mapa, pieza del tabernáculo, objetos y escenarios del catálogo.
    const rel = [];
    const personas = (Array.isArray(e.personas) ? e.personas : []).filter(p => N.persona(D, p) && personaOk(p));
    if (personas.length) rel.push(`<p class="rel-tit">Personas</p><ul class="chips">${personas.map(p => `<li>${btnPersona(p)}</li>`).join('')}</ul>`);
    const lugs = [].concat(e.lugar ? [e.lugar] : [], Array.isArray(e.lugares) ? e.lugares : []).filter((l, i, a) => N.lugar(D, l) && a.indexOf(l) === i && lugarOk(l));
    if (lugs.length) rel.push(`<p class="rel-tit">Lugares del mapa</p><ul class="chips">${lugs.map(l => `<li>${btnLugar(l)}</li>`).join('')}</ul>`);
    if (e.tabernaculo && TB && N.tbPieza(TB, e.tabernaculo) && visiblesLeidoTB().has(e.tabernaculo)) rel.push(`<p class="rel-tit">Tabernáculo</p><p><a class="boton secundario" href="${hrefTB(e.tabernaculo)}">Ver «${esc(N.tbPieza(TB, e.tabernaculo).nombre || e.tabernaculo)}» en el plano</a></p>`);
    const inv = N.relacionadosJuego(JJ, tipo === 'persona' ? 'persona' : tipo === 'objetos' ? 'objeto' : 'escenario', id);
    const objs = tipo === 'escenarios' ? (Array.isArray(e.objetos) ? e.objetos : []) : inv.objetos;
    const escs = tipo === 'escenarios' ? [] : inv.escenarios;
    const cosaOk = (g, x) => { const s = N.vistaFichaJuego(D, JJ, g, x, [...pasajesLeidos()]); return !!s && (!!s.visible || (!!s.primera && refOk(s.primera))); };
    const cs = objs.filter(o => cosaOk('objetos', o)).map(o => btnCosa('objetos', o)).concat(escs.filter(x => cosaOk('escenarios', x)).map(x => btnCosa('escenarios', x))).filter(Boolean);
    if (cs.length) rel.push(`<p class="rel-tit">Objetos y escenarios</p><ul class="chips">${cs.map(b => `<li>${b}</li>`).join('')}</ul>`);
    const imgs = imagenesJuegoHTML(aps);
    if (imgs) rel.push(`<p class="rel-tit">Imágenes</p>${imgs}`);
    return `<section class="juego-ficha">
      ${ds.length ? `<h3>Lo que dice el texto</h3><ul class="datos-juego">${ds.map(datoLi).join('')}</ul>` : ''}
      ${ex.length ? `<h3>Fuera de la Biblia</h3><p class="meta">Historia, arqueología o tradición: no lo dice el texto bíblico. Enlaces a sitios ajenos a esta app.</p><ul class="externos">${ex.map(exLi).join('')}</ul>` : ''}
      <h3>Apariciones${aps.length ? ` (${aps.length})` : ''}</h3>
      ${aps.length ? `<p class="meta">Donde está presente en el relato (aunque no se le nombre); las genealogías no cuentan.</p><ul class="chips apariciones">${aps.map(apLi).join('')}</ul>` : aps0.length ? '' : '<p class="meta">Solo se le nombra en genealogías.</p>'}
      ${apsOcultas ? `<p class="meta">${ICO_CANDADO} Hay más apariciones adelante: se verán al leerlas.</p>` : ''}
      ${mps.length ? `<h3>Menciones posteriores</h3><p class="meta">Otros lo nombran más adelante.</p><ul class="chips">${mps.map(x => `<li>${refHTML(x.ref)}</li>`).join('')}</ul>` : ''}
      ${rel.length ? `<h3>Relacionados</h3>${rel.join('')}` : ''}
      <p class="meta">Catálogo de juego del proyecto: resumen y nivel son editoriales; cada dato lleva su versículo.</p></section>`;
  }
  // Los resúmenes del catálogo no llevan versículo: por prudencia solo se ven cuando todas sus apariciones son accesibles.
  const resumenOk = e => ACC().todo || ((Array.isArray(e.apariciones) ? e.apariciones : []).length > 0 && e.apariciones.every(x => x && refOk(x.fin || x.inicio)));
  // Ficha de objeto o escenario (mismo diálogo que la de personaje).
  function abrirCosa(g, id) {
    const JJ = JUEGO(), e = JJ && (JJ[g] || {})[id]; if (!e) return;
    const s = N.vistaFichaJuego(D, JJ, g, id, [...pasajesLeidos()]) || {}, obt = !!s.visible;
    const ico = obt ? ICO_COSA[g] : ICO_COSA[g].replace('class="ico-cosa"', 'class="ico-cosa silueta-cosa"');
    fichaDlg.querySelector('h2').textContent = e.nombre || id;
    // Sin obtener: silueta, nombre y capítulo de la primera aparición, como en la colección (sin adelantar el contenido).
    fichaDlg.querySelector('.dialogo-cuerpo').innerHTML = `
      <div class="ficha-cab"><figure class="retrato vacio cosa c-${g}${obt ? '' : ' sin-obtener'}">${ico}<figcaption>${obt ? GRUPO_TXT[g] : 'Sin descubrir'}</figcaption></figure><div class="ficha-datos">
        <p class="rol">${GRUPO_TXT[g]}${obt && e.tipo ? ' · ' + esc(e.tipo) : ''}</p>
        ${obt && e.resumen && resumenOk(e) ? `<p class="resumen-juego">${esc(e.resumen)}</p>` : ''}
        <p class="ficha-estado${obt ? ' en-col' : ''}">${obt ? 'En tu colección' : `Aún no está en tu colección${s.primeraCap ? ' · aparece en ' + esc(capLegible(s.primeraCap)) : ''}`}</p>
        ${obt ? '' : '<p class="meta">Su ficha se verá cuando leas el pasaje donde aparece por primera vez.</p>'}
      </div></div>
      ${s.pasaje ? `<p class="acciones-ficha"><a class="boton" href="#leer/p/${esc(s.pasaje)}">Leer donde aparece</a></p>` : ''}
      ${obt ? bloquesJuegoHTML(e, g, id) : ''}`;
    mostrar(fichaDlg);
    fichaDlg.querySelector('.dialogo-cuerpo').scrollTop = 0;
  }
  function abrirFicha(id) {
    const p = N.persona(D, id); if (!p) return;
    if (!personaOk(id)) { abrirBloqueada('Persona sin descubrir', 'Esta persona aparece más adelante en la lectura. Su ficha se verá cuando llegues al pasaje donde se la nombra.'); return; }
    const I = N.indice(D);
    const relOk = (r, otro) => refOk(r.ref) && personaOk(otro); // vínculo y la otra persona, ya accesibles
    const extra = r => `${citaHTML(r)}${r.nota ? `<p class="nota">${esc(r.nota)}</p>` : ''}`;
    const padres = (I.padres.get(id) || []).filter(r => relOk(r, r.de)).map(r => `<li>${btnPersona(r.de)} <span class="meta">${r.tipo}</span> ${insignia(r.certeza, r.ref)}${extra(r)}</li>`);
    const cony = (I.conyuges.get(id) || []).filter(r => relOk(r, r.otro)).map(r => `<li>${btnPersona(r.otro)} ${insignia(r.certeza, r.ref)}${extra(r)}</li>`);
    const hijos = N.hijosDe(D, id).filter(r => relOk(r, r.a)).map(r => {
      const madre = r.tipo !== 'madre' ? (I.padres.get(r.a) || []).find(x => x.tipo === 'madre' && relOk(x, x.de)) : null;
      return `<li>${btnPersona(r.a)} ${insignia(r.certeza, r.ref)}${madre ? `<span class="meta">madre: ${esc(nombre(madre.de))}</span>` : ''}${extra(r)}</li>`;
    });
    const tieneEdades = N.TIPOS.some(t => N.TRADS.some(tr => N.edadAccesible(ACC(), N.edad(D, id, t, tr))));
    const dif = N.diferencias(D, id);
    const evs = N.edadesEnEvento(D).filter(x => x.persona === id && refOk(x.ref));
    const edades = (tieneEdades ? `<table class="edades mini"><thead><tr><th scope="col"></th><th scope="col">TM</th><th scope="col">LXX</th></tr></thead><tbody>${N.TIPOS.map(t => `<tr><th scope="row">${TIPO_TXT[t]}</th>${N.TRADS.map(tr => celda(id, t, tr, dif[t])).join('')}</tr>`).join('')}</tbody></table>` : '')
      + (evs.length ? `<ul class="edades-acomp">${evs.map(eventoHTML).join('')}</ul>` : '') || '<p class="meta">Sin edades registradas.</p>';
    // En el tiempo: nacimiento y muerte en años desde Adán (cálculo) con la combinación elegida en Tiempo.
    let tiempo = '', curios = '';
    if (N.crono(D)) {
      const tr = tradSimple(), combo = comboDe(tr), x0 = N.vidasCrono(D, combo).get(id), x = x0 ? N.vidaAccesible(D, x0, ACC()) : null;
      const cs = N.curiosidadesDe(D, id, combo).filter(c => N.curiosidadPermitida(c, perfil(), CONT()) && N.curiosidadAccesible(ACC(), c) && c.personas.every(personaOk));
      const liC = c => `<li class="curio"><p>${esc(c.texto)}.</p><details class="plegable"><summary>Pasos y versículos</summary>${pasosCurio(c)}</details></li>`;
      if (cs.length) curios = `<h3>Curiosidades ${insignia('calculo')}</h3><ul class="curios">${cs.slice(0, 3).map(liC).join('')}</ul>
        ${cs.length > 3 ? `<details class="plegable"><summary>Ver ${cs.length - 3} más</summary><ul class="curios">${cs.slice(3).map(liC).join('')}</ul></details>` : ''}
        <p class="meta">Calculadas por esta app con ${esc(TRAD_TXT[tr])} y los supuestos elegidos en Tiempo; los años son «años desde la creación de Adán».</p>`;
      if (x && (x.nacimiento !== null || x.muerte !== null)) {
        const cel = (a, ev) => a === null ? '<span class="meta">sin dato</span>' : `<button type="button" class="celda-acomp" data-ev="${esc(ev)}"><strong>${a}</strong></button>`;
        const cont = N.contemporaneos(D, id, combo, 30).filter(c => personaOk(c.persona)).slice(0, 8);
        tiempo = `<h3>En el tiempo ${insignia('calculo')}</h3>
          <div class="par"><span>Nace<br>${cel(x.nacimiento, x.evNac)}</span><span>Muere<br>${cel(x.muerte, x.evMuerte)}</span></div>
          <p class="meta">Años desde la creación de Adán (${tr}, con los supuestos elegidos en Tiempo). Pulsa una cifra para ver el cálculo.</p>
          ${cont.length ? `<p class="meta">Contemporáneos destacados:</p><ul class="chips">${cont.map(c => `<li>${btnPersona(c.persona)}</li>`).join('')}</ul>` : ''}`;
      }
    }
    const refs0 = [...new Set([].concat(p.primera_ref ? [p.primera_ref] : [], p.refs || []))], refs = refs0.filter(refOk);
    const todoLeido = refs.length === refs0.length; // la nota y el resumen no llevan versículo: solo cuando todo lo suyo es accesible
    // Grafía de la RV1909 si difiere del nombre mostrado.
    const formas = [...new Set([].concat(p.formas_rv1909 || [], p.nombre_rv1909 || []).filter(Boolean))];
    const grafia = formas.some(f => N.norm(f) !== N.norm(p.nombre)) ? formas.join(', ') : '';
    const notaGrafia = grafia && /^En la Reina-Valera 1909:/.test(p.nota || '');
    const k1 = N.indice(D).primera.get(id), primera = k1 ? N.refDeClave(k1) : p.primera_ref;
    const JJ = JUEGO(), ej = JJ && JJ.personajes[id], leidosF = [...pasajesLeidos()];
    const est = !p.sin_nombre && ej ? N.vistaFichaJuego(D, JJ, 'personajes', id, leidosF) : null;
    const oculto = !!est && !est.visible; // no obtenido: sin el contenido del catálogo (como en la colección)
    const enCol = !p.sin_nombre && N.coleccion(D, leidosF, JJ).has(id), rz = N.rareza(D, id);
    const estadoTxt = enCol ? 'En tu colección' : est && est.estado === 'en-curso' ? `En curso · ${avanceTxt(est)}` : est && est.capitulo ? `Aún no está en tu colección · se desbloquea al terminar ${esc(capLegible(est.capitulo))}` : 'Aún no está en tu colección';
    const pas = N.pasajesDePersona(D, id).filter(x => ACC().pasaje(x.pasaje.id));
    const pasLi = x => `<li><a href="#leer/p/${esc(x.pasaje.id)}"><span class="pp-rango">${rango(x.pasaje)}</span><span class="pp-titulo">${esc(x.pasaje.titulo)}</span></a><span class="meta">${x.versiculos} ${x.versiculos === 1 ? 'versículo' : 'versículos'}</span></li>`;
    const lugs = N.lugaresDePersona(D, id, 40).filter(x => lugarOk(x.lugar)).slice(0, 10), ext = N.enlacesExternos(D, id);
    fichaDlg.querySelector('h2').textContent = p.nombre || id;
    fichaDlg.querySelector('.dialogo-cuerpo').innerHTML = `
      <div class="ficha-cab">${retratoHTML(p)}<div class="ficha-datos">
        ${p.rol ? `<p class="rol">${esc(p.rol)}</p>` : ''}
        ${grafia ? `<p class="grafia">En la Reina-Valera 1909: <strong>${esc(grafia)}</strong></p>` : ''}
        <p class="meta">${p.sexo === 'm' ? 'Varón' : p.sexo === 'f' ? 'Mujer' : 'Sexo no indicado'}${primera ? ' · primera aparición: ' + refHTML(primera) : ''} ${etiquetaTrad(id)}</p>
        ${p.sin_nombre ? '' : `<p class="ficha-estado${enCol ? ' en-col' : est && est.estado === 'en-curso' ? ' en-curso' : ''}">${estadoTxt} · ${est ? nivelHTML(est) : ''}<span class="rareza-muestra r-${rz.id}">${esc(rz.nombre)}</span> <span class="meta">${rz.versiculos} ${rz.versiculos === 1 ? 'versículo' : 'versículos'}</span></p>`}
        ${ej && ej.resumen && !oculto && resumenOk(ej) && todoLeido ? `<p class="resumen-juego">${esc(ej.resumen)}</p>` : ''}
        ${oculto && est.primeraCap ? `<p class="meta">Aparece en ${esc(capLegible(est.primeraCap))}. Su ficha de la colección se verá cuando la obtengas.</p>` : ''}
      </div></div>
      <p class="acciones-ficha">${(r => r ? `<a class="boton" href="${hrefRef(N.parseRef(r))}">Leer donde aparece</a>` : '')([primera, p.primera_ref, p.ref_mencion].concat(p.refs || []).find(x => N.clave(x)))}
        ${N.enPantallaArbol(D, id) ? `<a class="boton secundario" href="#arbol/${encodeURIComponent(id)}">Ver en el árbol</a>` : ''}</p>
      ${ej && !oculto ? bloquesJuegoHTML(ej, 'persona', id) : ''}
      <h3>Padres</h3>${lista(padres, 'No constan.')}
      ${cony.length ? '<h3>Cónyuges</h3>' + lista(cony, '') : ''}
      <h3>Hijos</h3>${lista(hijos, 'No constan.')}
      <h3>Edades</h3>${edades}${tiempo}${curios}
      ${pas.length ? `<h3>Pasajes donde aparece (${pas.length})</h3><ul class="pasajes-persona">${pas.slice(0, 5).map(pasLi).join('')}</ul>
        ${pas.length > 5 ? `<details class="plegable"><summary>Ver los otros ${pas.length - 5}</summary><ul class="pasajes-persona">${pas.slice(5).map(pasLi).join('')}</ul></details>` : ''}` : ''}
      ${lugs.length ? `<h3>Lugares</h3><p class="meta">Nombrados en los mismos versículos que ${esc(p.nombre || id)}: coincidencia en el texto, no un vínculo afirmado.</p><ul class="chips">${lugs.map(x => `<li>${btnLugar(x.lugar)}</li>`).join('')}</ul>` : ''}
      ${p.nota && !notaGrafia && todoLeido ? `<h3>Notas</h3><p class="nota">${esc(p.nota)}</p>` : ''}
      ${todoLeido ? '' : `<p class="meta">${ICO_CANDADO} Solo lo que va hasta donde has leído; el resto de su historia se verá al avanzar.</p>`}
      ${refs.length ? `<details class="plegable"><summary>Versículos de los datos (${refs.length})</summary><ul class="refs">${refs.map(r => `<li>${refHTML(r)}</li>`).join('')}</ul></details>` : ''}
      ${ext.length ? `<h3>Profundizar</h3><p class="meta">Enlaces a sitios ajenos a esta app (se abren aparte); su contenido no se copia aquí.</p>
        <ul class="externos">${ext.map(x => `<li><a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">${esc(x.titulo)}</a> <span class="etiqueta externa">Fuente externa</span><span class="meta">${esc(x.detalle)}</span></li>`).join('')}</ul>` : ''}`;
    mostrar(fichaDlg);
    fichaDlg.querySelector('.dialogo-cuerpo').scrollTop = 0;
  }

  // Ficha de algo que aún no se ha alcanzado leyendo en orden: ni nombre ni datos, solo el candado.
  function abrirBloqueada(titulo, texto) {
    fichaDlg.querySelector('h2').textContent = titulo;
    const f = ACC().frontera;
    fichaDlg.querySelector('.dialogo-cuerpo').innerHTML = `${bloqueadoHTML(esc(texto))}<p class="meta">La lectura avanza en orden: lo que viene después del primer pasaje sin leer está bloqueado.</p>
      ${f ? `<p class="acciones-ficha"><a class="boton" href="#leer/p/${esc(f.id)}">Seguir leyendo</a></p>` : ''}`;
    mostrar(fichaDlg);
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
  function montarMapas(raiz) {
    if (!raiz) return;
    raiz.querySelectorAll('.mapa[data-mapa]:not([data-montado])').forEach(el => { try { crearMapa(el, JSON.parse(el.dataset.mapa)); } catch (e) { el.textContent = 'No se pudo dibujar el mapa.'; } });
    montarTB(raiz);
    raiz.querySelectorAll('.rc[data-rc]:not([data-montado])').forEach(el => { try { crearRecorrido(el, JSON.parse(el.dataset.rc)); } catch (e) { const l = el.querySelector('.rc-lienzo'); if (l) l.textContent = 'No se pudo dibujar el recorrido.'; console.error(e); } });
  }
  // Costas, lagos, ríos (Natural Earth) y retícula de 5°, en coordenadas proyectadas.
  function baseMapaSVG(P) {
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
    return base + ret;
  }

  function crearMapa(el, cfg) {
    el.dataset.montado = '1';
    const P = N.proyeccion(MAPA && MAPA.bbox);
    const ubicados = cfg.ids.map(id => N.lugar(D, id)).filter(l => N.confianzaLugar(l) !== 'desconocida');
    const coord = l => [+l.ubicacion.lon, +l.ubicacion.lat];
    const conf = ubicados.map(l => N.confianzaLugar(l)), prio = ubicados.map(l => N.prioridadLugar(l));
    let sel = cfg.sel, W = 320, H = 220;
    const v = { cx: 0, cy: 0, s: 1 };
    el.innerHTML = `<div class="mapa-lienzo"><svg tabindex="0" role="application" aria-roledescription="mapa" aria-label="Mapa con ${ubicados.length} ${ubicados.length === 1 ? 'lugar' : 'lugares'}. Flechas para mover, más y menos para acercar.">
        <g class="base">${baseMapaSVG(P)}</g><g class="capa"></g></svg>
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
    if (!lugarOk(id)) { abrirBloqueada('Lugar sin descubrir', 'Este lugar aparece más adelante en la lectura. Su ficha se verá cuando llegues al pasaje donde se nombra.'); return; }
    const c = N.confianzaLugar(l), u = l.ubicacion || {};
    const alts = (l.alternativas || []).filter(a => a && a.identificacion);
    const refs = [...new Set(l.refs || [])].filter(refOk); // solo los versículos ya accesibles
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
    if (args && args[0] === 'recorridos') return vistaRecorridos(args.slice(1));
    const todos = D.lugares || [], A = ACC();
    if (args && args[0]) estado.mapaSel = args[0];
    const caps = D.capitulos || [], ps = N.pasajes(D);
    const f = estado.mapaFiltro;
    let ids = todos.map(l => l.id);
    if (f.startsWith('cap-')) {
      const [lb, cs] = f.slice(4).split('-'), cap = +cs, c = caps.find(x => x.cap === cap && N.libroIdDe(D, x.libro) === lb);
      ids = c ? N.lugaresDeRefs(D, (c.versiculos || []).map(v => `${lb} ${cap}:${v.n}`)) : [];
    }
    else if (f.startsWith('p-')) ids = N.lugaresDePasaje(D, ps.find(p => p.id === f.slice(2)));
    ids = N.lugaresAccesibles(D, A, ids); // solo lugares nombrados en lo accesible
    const ubic = ids.filter(id => { const c = N.confianzaLugar(N.lugar(D, id)); return c !== 'desconocida' && estado.mapaConf.has(c); });
    const desc = ids.filter(id => N.confianzaLugar(N.lugar(D, id)) === 'desconocida');
    const opt = (v, t) => `<option value="${esc(v)}"${f === v ? ' selected' : ''}>${esc(t)}</option>`;
    return `<h1 tabindex="-1">Mapa de los lugares</h1>
      ${subvistasMapa('lugares')}
      <p class="sub">El nombre de cada lugar es texto bíblico; su ubicación es una identificación moderna con un grado de confianza. Lo que no se puede ubicar no se dibuja.</p>
      ${A.todo ? '' : `<p class="meta">${ICO_CANDADO} Solo los lugares nombrados hasta donde has leído; los demás aparecerán al avanzar.</p>`}
      <div class="herr mapa-filtros">
        <div class="campo"><label for="f-ambito">Pasaje o capítulo</label><select id="f-ambito">${opt('', 'Todo ' + N.alcance(D).texto)}
          ${(D.pasajes || []).length ? N.seccionesPlan(D, [], null).map(g => [g, g.pasajes.filter(x => A.pasaje(x.pasaje.id))]).filter(x => x[1].length).map(([g, xs]) => `<optgroup label="${esc(g.titulo ? 'Pasajes · ' + g.titulo : 'Pasajes')}">${xs.map(x => opt('p-' + x.pasaje.id, x.pasaje.titulo)).join('')}</optgroup>`).join('') : ''}
          ${N.libros(D).map(l => { const cs = caps.filter(c => N.libroIdDe(D, c.libro) === l.id && A.ref(`${l.id} ${c.cap}:1`)).sort((a, b) => a.cap - b.cap); return cs.length ? `<optgroup label="Capítulos · ${esc(l.nombre)}">${cs.map(c => opt(`cap-${l.id}-${c.cap}`, `${l.nombre} ${c.cap}`)).join('')}</optgroup>` : ''; }).join('')}</select></div>
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
    const r = (D.lugares || []).filter(l => (N.norm(l.nombre).includes(q) || N.norm(l.nombre_rv1909).includes(q)) && lugarOk(l.id)).slice(0, 20);
    return r.length ? r.map(l => `<li>${btnLugar(l.id)}</li>`).join('') : '<li class="meta">Sin resultados.</li>';
  }

  /* ---------- Recorridos (datos/recorridos.js): el relato animado sobre el mapa ---------- */
  // Texto: nombre, orden, cita y ref de cada etapa. Fuente externa: dónde estaba cada lugar (una hipótesis, nunca un hecho).
  let RC = window.BIBLIA_RECORRIDOS || null;
  // Recorridos vistos desde lo accesible: solo las etapas cuya ref ya se puede leer (lectura en orden).
  let rcCache = { A: null, rc: null, v: null };
  const RCV = () => {
    const A = ACC(); if (!RC) return RC;
    if (rcCache.A !== A || rcCache.rc !== RC) rcCache = { A, rc: RC, v: Object.assign({}, RC, { recorridos: (RC.recorridos || []).map(r => r && Array.isArray(r.etapas) ? Object.assign({}, r, { etapas: r.etapas.filter(e => e && A.ref(e.ref)) }) : r) }) };
    return rcCache.v;
  };
  const recCompleto = rec => { const o = N.recorrido(RC, rec.id); return !!o && o.etapas.length === rec.etapas.length; };
  const estadoRC = { hip: {}, vel: [0.5, 1, 2].includes(store.get('biblia.rcVel', 1)) ? store.get('biblia.rcVel', 1) : 1 };
  const movReducido = () => !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  // Rótulos de regiones y mares para situarse: posición aproximada, sin fronteras (no son datos del texto).
  const ROTULOS = [['Egipto', 30.2, 27.3], ['Sinaí', 33.85, 29.5], ['Madián', 36.5, 27.9], ['Canaán', 35.25, 32.4], ['Edom', 35.6, 30.25], ['Moab', 35.95, 31.4],
    ['Mesopotamia', 43.4, 34.2], ['Mar Mediterráneo', 31.3, 33.2, 'mar'], ['Mar Rojo', 36.2, 25.2, 'mar']];
  const subvistasMapa = act => `<nav class="subvistas" aria-label="Vistas del mapa"><a href="#mapa"${act === 'lugares' ? ' aria-current="page"' : ''}>Lugares</a><a href="#mapa/recorridos"${act === 'recorridos' ? ' aria-current="page"' : ''}>Recorridos</a></nav>`;
  const hipDe = rec => { const h = estadoRC.hip[rec.id]; return (rec.hipotesis || []).some(x => x && x.id === h) ? h : (N.hipotesisDefecto(rec) || {}).id || null; };
  const hipPorId = (rec, id) => (rec.hipotesis || []).find(h => h && h.id === id) || null;
  const enlaceExt = (txt, url) => url && /^https?:\/\//.test(url) ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(txt)}</a>` : esc(txt);
  const hrefEtapa = (rec, e) => `#mapa/recorridos/${encodeURIComponent(rec.id)}/${encodeURIComponent(e.orden)}`;
  const ICO_PLAY = '<svg viewBox="0 0 20 20" aria-hidden="true"><path class="rell" d="M6 4l10 6-10 6z"/></svg>';
  const ICO_PAUSA = '<svg viewBox="0 0 20 20" aria-hidden="true"><path class="rell" d="M5.5 4h3v12h-3zM11.5 4h3v12h-3z"/></svg>';
  const ICO_OTRA = '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4.5 10a5.5 5.5 0 109-4.2M13.5 2.5v3.6H9.9"/></svg>';

  function hipotesisHTML(rec, hid) {
    const h = hipPorId(rec, hid); if (!h) return '';
    return `<p><strong>${esc(h.nombre || h.id)}</strong>${h.defecto ? ' <span class="etiqueta">por defecto</span>' : ''}${h.minoritaria ? ' <span class="etiqueta minoritaria">minoritaria</span>' : ''}</p>
      ${h.descripcion ? `<p>${esc(h.descripcion)}</p>` : ''}
      <p class="meta"><span class="etiqueta externa">Fuente externa</span> ${h.fuente ? enlaceExt(h.fuente, h.url) : 'sin fuente indicada'}</p>`;
  }
  function tarjetaEtapaHTML(rec, i, hid, enCamino) {
    const E = N.etapasOrdenadas(rec), e = E[i]; if (!e) return '';
    const u = N.ubicacionEtapa(rec, e, hid), h = hipPorId(rec, hid), def = N.hipotesisDefecto(rec);
    const tm = e.tiempo, lg = e.lugar && D && N.lugar(D, e.lugar);
    const tiempo = tm && tm.texto ? `<div class="rc-tiempo"><p><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3a7 7 0 100 14 7 7 0 000-14zM10 6v4l3 2"/></svg><strong>${esc(tm.texto)}</strong>
        ${tm.certeza === 'texto' || tm.certeza === 'calculo' ? insignia(tm.certeza) : '<span class="meta">(certeza no indicada)</span>'}</p>
        ${(tm.pasos || []).length ? `<details class="plegable"><summary>${tm.certeza === 'calculo' ? 'Cómo se calcula' : 'De dónde sale'}</summary><ol class="rc-pasos">${tm.pasos.map(p => `<li${p.convencion ? ' class="convencion"' : ''}>${p.convencion ? '<span class="etiqueta">convención</span> ' : ''}${esc(p.texto || '')}${p.ref ? ' · ' + refHTML(p.ref) : ''}${p.cita ? `<q>${esc(p.cita)}</q>` : ''}</li>`).join('')}</ol></details>` : ''}</div>` : '';
    const donde = u ? `<p class="ident">${icoConf(u.confianza)} <strong>${esc(u.identificacion || 'Sin nombre moderno')}</strong></p>
        <p class="meta"><strong>${CONF_TXT[u.confianza]}</strong>: ${CONF_DESC[u.confianza]}${u.puntuacion_openbible !== undefined && u.puntuacion_openbible !== null ? ` Puntuación de OpenBible: ${esc(u.puntuacion_openbible)}.` : ''}</p>
        <p class="meta">Según la hipótesis «${esc((h && h.nombre) || hid)}»${u.heredada ? `, que aquí no propone otro sitio: se usa el de «${esc((def && def.nombre) || u.hipotesis)}»` : ''}. ${u.fuente ? 'Fuente: ' + enlaceExt(u.fuente, u.url) : ''}</p>`
      : N.sinPropuesta(rec, e, hid) ? `<p class="desconocida">${icoConf('desconocida')} Esta hipótesis no propone ubicación para esta etapa.</p><p class="meta">No se dibuja: el trazo une las etapas conocidas anterior y siguiente con una línea tenue.</p>`
      : `<p class="desconocida">${icoConf('desconocida')} Ninguna hipótesis sitúa esta etapa: no se dibuja.</p>`;
    return `<p class="rc-cuenta">Etapa ${i + 1} de ${E.length}${enCamino ? ' · <span class="rc-camino">en camino</span>' : ''}</p>
      <h2 class="rc-nombre">${esc(e.nombre || e.lugar || 'Etapa')}</h2>
      ${e.cita ? `<blockquote class="rc-cita">${esc(e.cita)}</blockquote>` : ''}
      <p class="rc-ref">${insignia('texto', e.ref)}</p>
      ${tiempo}
      <section class="rc-donde"><h3>Dónde pudo estar <span class="etiqueta externa">Fuente externa</span></h3>${donde}
        ${lg ? `<button type="button" class="enlace-boton" data-lugar="${esc(e.lugar)}">Ficha del lugar</button>` : ''}</section>
      ${e.nota ? `<p class="nota">${esc(e.nota)}</p>` : ''}`;
  }

  function vistaRecorridos(args) {
    const L = N.listaRecorridos(RCV());
    const cab = `<h1 tabindex="-1">Recorridos</h1>${subvistasMapa('recorridos')}`;
    if (!L.length) return cab + (N.listaRecorridos(RC).length ? bloqueadoHTML('Los recorridos se van dibujando a medida que lees en orden: todavía no has llegado a ninguna de sus etapas.') : '<p class="vacio-txt">Los datos de los recorridos (datos/recorridos.js) todavía no están. Cuando lleguen, aquí verás el relato animado del Éxodo, de Abraham y de Jacob.</p>');
    const rec = N.recorrido(RCV(), args[0]) || L[0], E = N.etapasOrdenadas(rec), hid = hipDe(rec);
    let idx = 0; if (args[1] !== undefined) { const k = E.findIndex(e => String(e.orden) === args[1]); if (k >= 0) idx = k; }
    const hs = (rec.hipotesis || []).filter(h => h && h.id);
    const personas = (rec.personas || []).filter(id => N.persona(D, id));
    const dots = E.map((e, i) => { const u = N.ubicacionEtapa(rec, e, hid); return `<span class="rc-punto c-${u ? u.confianza : N.sinPropuesta(rec, e, hid) ? 'sinprop' : 'desc'}" style="left:${E.length > 1 ? (i / (E.length - 1) * 100).toFixed(2) : 50}%"></span>`; }).join('');
    const vel = v => `<label><input type="radio" name="rc-vel" value="${v}" ${estadoRC.vel === v ? 'checked' : ''}><span>${String(v).replace('.', ',')}×</span></label>`;
    return `${cab}
      <p class="sub">El nombre, el orden y la cita de cada etapa son <strong>texto</strong> bíblico. Dónde estaba cada lugar es una <strong>hipótesis moderna</strong> con su confianza: cambia de hipótesis y mira cómo se mueve la ruta.</p>
      ${RC.ejemplo ? '<p class="rc-ejemplo">EJEMPLO: datos de prueba con coordenadas aproximadas. No es una identificación real.</p>' : ''}
      ${L.length > 1 ? `<nav class="subvistas rc-recs" aria-label="Recorrido">${L.map(r => `<a href="#mapa/recorridos/${encodeURIComponent(r.id)}"${r.id === rec.id ? ' aria-current="page"' : ''}>${esc(r.titulo || r.id)}</a>`).join('')}</nav>` : ''}
      <div class="rc rc-completo" data-rc="${esc(JSON.stringify({ rec: rec.id, idx }))}">
        <div class="rc-escena">
          <div class="mapa rc-mapa"><div class="mapa-lienzo rc-lienzo">
            <div class="mapa-ctrl"><button type="button" data-z="1" aria-label="Acercar">+</button><button type="button" data-z="-1" aria-label="Alejar">−</button>
              <button type="button" data-z="0" aria-label="Ver el recorrido entero"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 7V3h4M13 3h4v4M17 13v4h-4M7 17H3v-4"/></svg></button></div>
            <p class="rc-sello">Hipótesis: <strong>${esc((hipPorId(rec, hid) || {}).nombre || hid || '')}</strong></p>
            ${MAPA ? '' : '<p class="mapa-aviso">Mapa base no disponible: solo se muestra la retícula.</p>'}</div></div>
          <div class="rc-mando">
            <button type="button" class="rc-play" data-rc-play aria-label="Reproducir el relato">${ICO_PLAY}</button>
            <button type="button" class="rc-paso" data-rc-paso="-1" aria-label="Etapa anterior"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M12.5 4.5L7 10l5.5 5.5"/></svg></button>
            <div class="rc-barra" role="slider" tabindex="0" aria-label="Etapa del recorrido" aria-valuemin="1" aria-valuemax="${E.length}" aria-valuenow="${idx + 1}">
              <div class="rc-pista"><span class="rc-lleno"></span>${dots}<span class="rc-cursor"></span></div></div>
            <button type="button" class="rc-paso" data-rc-paso="1" aria-label="Etapa siguiente"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M7.5 4.5L13 10l-5.5 5.5"/></svg></button>
          </div>
          <div class="rc-mando2"><p class="rc-estado meta" aria-hidden="true"></p>
            <fieldset class="segmentos rc-vel"><legend class="sr">Velocidad del relato</legend>${[0.5, 1, 2].map(vel).join('')}</fieldset></div>
        </div>
        <article class="rc-tarjeta" aria-live="polite">${tarjetaEtapaHTML(rec, idx, hid, false)}</article>
        <section class="rc-hip" aria-labelledby="t-rc-hip">
          <h2 id="t-rc-hip">Hipótesis sobre el trazado</h2>
          <p class="meta">Ninguna es un hecho: son propuestas modernas sobre dónde estaban los lugares que el texto nombra.</p>
          ${hs.length > 1 ? `<fieldset class="segmentos rc-hips"><legend class="sr">Hipótesis</legend>${hs.map(h => `<label><input type="radio" name="rc-hip" value="${esc(h.id)}" ${h.id === hid ? 'checked' : ''}><span>${esc(h.nombre || h.id)}${h.minoritaria && !/minoritaria/i.test(h.nombre || '') ? '<small class="rc-min">minoritaria</small>' : ''}</span></label>`).join('')}</fieldset>` : ''}
          <div class="rc-hip-desc">${hipotesisHTML(rec, hid)}</div>
        </section>
        <div class="rc-pie">
          <p class="leyenda-mapa">${['alta', 'media', 'baja'].map(c => `<span>${icoConf(c)}${CONF_TXT[c].replace('Confianza ', '')}</span>`).join('')}
            <span><svg class="ico-tramo" viewBox="0 0 28 10" aria-hidden="true"><path d="M2 5h24"/></svg>Tramo</span>
            <span><svg class="ico-tramo incierto" viewBox="0 0 28 10" aria-hidden="true"><path class="halo" d="M2 5h24"/><path d="M2 5h24"/></svg>Tramo incierto (toca una etapa de confianza baja)</span>
            <span><svg class="ico-tramo sin-propuesta" viewBox="0 0 28 10" aria-hidden="true"><path d="M2 5h24"/></svg>Tramo sin propuesta en esta hipótesis</span></p>
          <p class="meta">Regiones y mares: rótulos orientativos de posición aproximada, sin fronteras. Mapa base: Natural Earth.</p>
          ${rec.resumen && recCompleto(rec) ? `<p>${esc(rec.resumen)}</p>` : ''}
          ${recCompleto(rec) ? '' : `<p class="meta">${ICO_CANDADO} Se muestran las ${rec.etapas.length} etapas a las que ya has llegado leyendo; las siguientes aparecerán al avanzar.</p>`}
          ${personas.length ? `<p class="rc-personas"><span class="meta">Quién va:</span> ${personas.map(btnPersona).join(' ')}</p>` : ''}
          <details class="plegable"><summary>Todas las etapas (${E.length})</summary><ol class="rc-lista">${E.map((e, i) => `<li><button type="button" class="enlace-boton" data-rc-ir="${i}">${esc(e.nombre || 'Etapa')}</button> <span class="meta">${esc(e.ref || '')}</span></li>`).join('')}</ol></details>
          ${(RC.fuentes || []).length ? `<details class="plegable"><summary>Fuentes de las ubicaciones</summary><ul class="rc-fuentes">${RC.fuentes.map(f => `<li><span class="etiqueta externa">Fuente externa</span> ${enlaceExt(f.nombre || f.id || '', f.url)}${f.licencia ? ` <span class="meta">(${esc(f.licencia)})</span>` : ''}</li>`).join('')}</ul></details>` : ''}
        </div>
      </div>`;
  }

  // Motor del recorrido (vista completa y mini mapa del acompañante): cámara que sigue al grupo, ruta que se dibuja,
  // marcadores que aparecen al llegar y transformación animada al cambiar de hipótesis.
  function crearRecorrido(raiz, cfg) {
    raiz.dataset.montado = '1';
    const rec = N.recorrido(RCV(), cfg.rec), lienzo = raiz.querySelector('.rc-lienzo');
    if (!rec || !lienzo) return;
    const mini = !!cfg.mini, E = N.etapasOrdenadas(rec), n = E.length, aqui = new Set(cfg.aqui || []);
    const P = N.proyeccion(MAPA && MAPA.bbox);
    lienzo.insertAdjacentHTML('afterbegin', `<svg ${mini ? `role="img" aria-label="${esc(`Mapa del recorrido ${rec.titulo || rec.id}: etapa ${(cfg.idx || 0) + 1} de ${n} resaltada y las anteriores trazadas`)}"` : 'tabindex="0" role="application" aria-roledescription="mapa" aria-label="Mapa del recorrido. Flechas para mover, más y menos para acercar."'}>
      <g class="base">${baseMapaSVG(P)}</g><g class="rc-rot" aria-hidden="true"></g><g class="rc-ruta" aria-hidden="true"></g><g class="rc-marcas"></g>
      <g class="rc-cabeza" aria-hidden="true"><circle class="onda" r="10"/><circle class="punto" r="4.5"/></g><g class="rc-etq" aria-hidden="true"></g></svg>`);
    const svg = lienzo.querySelector('svg'), gBase = svg.querySelector('.base'), gRot = svg.querySelector('.rc-rot'), gRuta = svg.querySelector('.rc-ruta'),
      gMarcas = svg.querySelector('.rc-marcas'), gCab = svg.querySelector('.rc-cabeza'), gEtq = svg.querySelector('.rc-etq');
    const tarjeta = raiz.querySelector('.rc-tarjeta'), barra = raiz.querySelector('.rc-barra'), lleno = raiz.querySelector('.rc-lleno'), cursor = raiz.querySelector('.rc-cursor'),
      btnPlay = raiz.querySelector('[data-rc-play]'), estadoTxt = raiz.querySelector('.rc-estado');
    let W = 320, H = 220, hip = mini ? hipDe(rec) : hipDe(rec);
    const v = { cx: 0, cy: 0, s: 1 }, obj = { cx: 0, cy: 0, s: 1 };
    const ubic = h => E.map(e => { const u = N.ubicacionEtapa(rec, e, h); return u ? { lon: u.lon, lat: u.lat, c: u.confianza } : null; });
    let U = ubic(hip), T = N.tramosRecorrido(rec, hip), morph = null, tramosDOM = [], marcasDOM = [];
    const pos = { idx: Math.max(0, Math.min(n - 1, cfg.idx || 0)), t: 1 };
    let fase = 'quieto', jugando = false, tFase = 0, durFase = 0, libre = false, terminado = false, ultimo = 0, raf = 0;
    const suave = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;

    function lugarDe(i) {
      const b = U[i]; if (!morph) return b;
      const a = morph.de[i], k = suave(morph.k);
      if (a && b) return { lon: a.lon + (b.lon - a.lon) * k, lat: a.lat + (b.lat - a.lat) * k, c: b.c };
      return b || a;
    }
    const tramoHacia = i => T.find(t => t.a === i) || null;
    const ultimoUbicado = i => { for (let k = i; k >= 0; k--) if (lugarDe(k)) return k; return -1; };
    function construir() {
      gRuta.innerHTML = '<path class="rc-fantasma"/>' + T.map(t => `<g class="rc-tr conf-${t.confianza}${t.incierto ? ' incierto' : ''}${t.sinPropuesta ? ' sin-propuesta' : ''}">${t.incierto ? '<path class="halo"/>' : ''}<path class="linea"/></g>`).join('');
      tramosDOM = [...gRuta.querySelectorAll('.rc-tr')].map((g, k) => ({ t: T[k], ps: [...g.querySelectorAll('path')] }));
      gMarcas.innerHTML = E.map((e, i) => { const l = U[i] || (morph && morph.de[i]); if (!l) return ''; const c = (U[i] || l).c;
        return `<g class="rc-marca conf-${c}" data-rc-etapa="${i}"${mini ? '' : ` tabindex="-1" role="button" aria-label="${esc(`${e.nombre}, ${CONF_TXT[c].toLowerCase()}`)}"`}><g class="rc-forma">${c === 'baja' ? '<circle class="rc-halo" r="13"/>' : ''}<circle class="toque" r="16"/>${formaConf(c, 6)}</g></g>`; }).join('');
      marcasDOM = [...gMarcas.querySelectorAll('.rc-marca')].map(g => ({ i: +g.dataset.rcEtapa, g }));
    }
    const aPant = (lon, lat) => { const [x, y] = N.proyectar(P, lon, lat); return [(x - v.cx) * v.s + W / 2, (y - v.cy) * v.s + H / 2]; };
    const f1 = p => p[0].toFixed(1) + ' ' + p[1].toFixed(1);
    function pintar() {
      svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
      gBase.setAttribute('transform', `matrix(${v.s} 0 0 ${v.s} ${W / 2 - v.cx * v.s} ${H / 2 - v.cy * v.s})`);
      const S = E.map((e, i) => { const l = lugarDe(i); return l ? aPant(l.lon, l.lat) : null; });
      const vis = S.filter(Boolean);
      gRuta.firstChild.setAttribute('d', vis.length > 1 ? 'M' + vis.map(f1).join('L') : '');
      let cabeza = null; const items = [];
      tramosDOM.forEach(({ t, ps }) => {
        const p0 = S[t.de], p1 = S[t.a], f = t.a < pos.idx ? 1 : t.a === pos.idx ? pos.t : 0;
        let d = '';
        if (p0 && p1 && f > 0) { const q = [p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f]; d = `M${f1(p0)}L${f1(q)}`; if (t.a === pos.idx && f < 1) cabeza = q; }
        ps.forEach(p => p.setAttribute('d', d));
        if (d && t.sinPropuesta && !mini && p0 && p1) items.push({ id: 'sp' + t.a, x: (p0[0] + p1[0]) / 2, y: (p0[1] + p1[1]) / 2, texto: 'sin propuesta', prioridad: 50, sp: true });
      });
      if (!cabeza) { const k = ultimoUbicado(pos.idx); if (k >= 0 && S[k]) cabeza = S[k]; }
      if (cabeza && !mini && (fase === 'viaje' || ultimoUbicado(pos.idx) !== pos.idx)) { gCab.setAttribute('transform', `translate(${f1(cabeza)})`); gCab.classList.toggle('viajando', fase === 'viaje'); gCab.style.display = ''; } else gCab.style.display = 'none';
      marcasDOM.forEach(({ i, g }) => {
        const p = S[i]; if (!p) { g.style.display = 'none'; return; }
        g.style.display = ''; g.setAttribute('transform', `translate(${f1(p)})`);
        const est = i < pos.idx ? 'pasada' : i === pos.idx && pos.t >= 1 ? 'actual' : 'futura';
        if (g.dataset.est !== est) { g.dataset.est = est; g.setAttribute('class', `rc-marca conf-${(U[i] || {}).c || 'baja'} ${est}${aqui.has(i) ? ' aqui' : ''}`); }
        if (est !== 'futura' || aqui.has(i)) items.push({ id: String(i), x: p[0], y: p[1], texto: E[i].nombre || '', prioridad: est === 'actual' ? 1e4 : aqui.has(i) ? 5e3 : i === 0 ? 3e3 : 100 + i });
      });
      gEtq.innerHTML = N.colocarEtiquetas(items, W, H, mini ? 4 : 7).map(e => `<text class="etq${e.id === String(pos.idx) ? ' sel' : ''}${e.id.startsWith('sp') ? ' etq-sp' : ''}" x="${e.x.toFixed(1)}" y="${e.y.toFixed(1)}" text-anchor="${e.anc}">${esc(e.texto)}</text>`).join('');
      gRot.innerHTML = ROTULOS.map(([t, lon, lat, tipo]) => { const [x, y] = aPant(lon, lat); return x < -60 || y < -20 || x > W + 60 || y > H + 20 ? '' : `<text class="rc-region${tipo === 'mar' ? ' mar' : ''}" x="${x.toFixed(1)}" y="${y.toFixed(1)}" text-anchor="middle">${esc(t)}</text>`; }).join('');
      if (lleno) {
        const tr = tramoHacia(pos.idx), fr = n > 1 ? (pos.t < 1 && tr ? tr.de + (pos.idx - tr.de) * pos.t : pos.idx) / (n - 1) : 1;
        lleno.style.width = (fr * 100).toFixed(2) + '%'; cursor.style.left = (fr * 100).toFixed(2) + '%';
      }
    }
    // Cámara: encuadra puntos [lon,lat]; `minimo` en grados.
    function mirar(pts, minimo, margen) {
      const r = N.encuadre(P, pts.filter(Boolean).map(l => [l.lon, l.lat]), { minimo, margen });
      obj.s = Math.min(W / r.w, H / r.h); obj.cx = r.x + r.w / 2; obj.cy = r.y + r.h / 2;
    }
    const todo = () => E.map((e, i) => lugarDe(i)).filter(Boolean);
    function enfocar() {
      libre = false;
      if (mini) { const vistos = E.map((e, i) => i <= pos.idx + 1 || aqui.has(i) ? lugarDe(i) : null).filter(Boolean); mirar(vistos.length ? vistos : todo(), 3, .15); return; }
      const tr = tramoHacia(pos.idx);
      if (fase === 'intro' || fase === 'fin' || terminado || pos.idx < 0) { mirar(todo(), 3, .1); return; }
      if (fase === 'viaje' && tr) { mirar([lugarDe(tr.de), lugarDe(tr.a)], 1.4, .35); return; }
      const k = ultimoUbicado(pos.idx); if (k < 0) { mirar(todo(), 3, .1); return; }
      const t2 = tramoHacia(k), km = t2 ? t2.km : 150;
      mirar(t2 ? [lugarDe(t2.de), lugarDe(k)] : [lugarDe(k)], Math.min(4, Math.max(1.3, km / 111 * 1.1)), .3);
    }
    const quieta = () => Math.abs(v.cx - obj.cx) * v.s < .3 && Math.abs(v.cy - obj.cy) * v.s < .3 && Math.abs(Math.log(v.s / obj.s)) < .002;
    // requestAnimationFrame, con un temporizador de respaldo por si el navegador no pinta (vistas incrustadas u ocultas).
    let rto = 0;
    function pedir() {
      if (raf) return;
      raf = requestAnimationFrame(t => { clearTimeout(rto); tick(t); });
      rto = setTimeout(() => { if (raf) { cancelAnimationFrame(raf); tick(performance.now()); } }, 100);
    }
    function tick(ahora) {
      raf = 0;
      if (!svg.isConnected) return;
      const dt = ultimo ? Math.min(120, Math.max(0, ahora - ultimo)) : 16; ultimo = ahora;
      const red = movReducido();
      if (morph) { morph.k = red ? 1 : Math.min(1, morph.k + dt / 1100); if (morph.k >= 1) { const sobra = morph.de.some((a, i) => a && !U[i]); morph = null; if (sobra) construir(); } if (!libre) enfocar(); }
      if (fase === 'viaje') {
        tFase += dt * (jugando ? estadoRC.vel : 1.6);
        pos.t = red || !durFase ? 1 : suave(Math.min(1, tFase / durFase));
        if (pos.t >= 1) llegar();
      } else if (jugando && (fase === 'pausa' || fase === 'intro')) {
        tFase += dt * estadoRC.vel;
        if (tFase >= durFase) { if (fase === 'intro') llegar(); else if (pos.idx < n - 1) partir(pos.idx + 1); else terminar(); }
      }
      if (!libre) {
        const k = red ? 1 : 1 - Math.exp(-dt / (fase === 'viaje' ? 520 : 380));
        v.cx += (obj.cx - v.cx) * k; v.cy += (obj.cy - v.cy) * k; v.s = Math.exp(Math.log(v.s) + (Math.log(obj.s) - Math.log(v.s)) * k);
      }
      pintar();
      if (jugando || morph || fase === 'viaje' || (!libre && !quieta())) pedir(); else ultimo = 0;
    }
    function tarjetaA(i, enCamino) {
      if (tarjeta) {
        tarjeta.innerHTML = tarjetaEtapaHTML(rec, i, hip, enCamino);
        if (!enCamino) { tarjeta.classList.remove('entra'); void tarjeta.offsetWidth; tarjeta.classList.add('entra'); }
      }
      if (barra) { barra.setAttribute('aria-valuenow', i + 1); barra.setAttribute('aria-valuetext', `Etapa ${i + 1} de ${n}: ${E[i].nombre || ''}`); }
      if (estadoTxt) estadoTxt.textContent = `${i + 1} / ${n} · ${E[i].nombre || ''}`;
    }
    function partir(i) {
      pos.idx = i; terminado = false;
      const tr = tramoHacia(i);
      if (!tr || movReducido()) { pos.t = 1; llegar(); return; }
      fase = 'viaje'; tFase = 0; pos.t = 0; durFase = N.duracionTramo(tr.km) * (jugando ? 1 : .55);
      tarjetaA(i, true); enfocar(); pedir();
    }
    function llegar() {
      pos.t = 1; tarjetaA(pos.idx, false);
      if (jugando) { fase = 'pausa'; tFase = 0; durFase = N.pausaEtapa(E[pos.idx]); } else { fase = 'quieto'; anotar(); }
      enfocar(); pedir();
    }
    function terminar() { jugando = false; terminado = true; fase = 'fin'; enfocar(); fase = 'quieto'; libre = false; botones(); anotar(); pedir(); }
    function ir(i, animar) {
      i = Math.max(0, Math.min(n - 1, i));
      if (animar && i === pos.idx + 1 && fase !== 'viaje') { partir(i); return; }
      pos.idx = i; pos.t = 1; terminado = false; fase = jugando ? 'pausa' : 'quieto'; tFase = 0; durFase = N.pausaEtapa(E[i]);
      tarjetaA(i, false); if (!jugando) anotar(); enfocar(); pedir();
    }
    function anotar() { if (!mini) try { history.replaceState(null, '', hrefEtapa(rec, E[pos.idx])); } catch (e) { /* file:// */ } }
    function botones() {
      if (!btnPlay) return;
      btnPlay.innerHTML = jugando ? ICO_PAUSA : terminado ? ICO_OTRA : ICO_PLAY;
      btnPlay.setAttribute('aria-label', jugando ? 'Pausar el relato' : terminado ? 'Volver a empezar el relato' : 'Reproducir el relato');
      btnPlay.classList.toggle('activo', jugando);
    }
    function alternar() {
      if (jugando) { jugando = false; const f = fase; if (f === 'pausa' || f === 'intro') { fase = 'quieto'; if (f === 'intro') llegar(); } anotar(); botones(); pedir(); return; }
      jugando = true; botones();
      if (terminado || (pos.idx === n - 1 && fase === 'quieto')) { pos.idx = 0; pos.t = 1; terminado = false; }
      if (pos.idx === 0 && fase !== 'viaje') { fase = 'intro'; tFase = 0; durFase = 1500; tarjetaA(0, false); enfocar(); }
      else if (fase !== 'viaje') { fase = 'pausa'; tFase = 0; durFase = 600; }
      pedir();
    }
    function cambiarHip(h) {
      if (h === hip) return;
      const de = E.map((e, i) => lugarDe(i));
      hip = h; estadoRC.hip[rec.id] = h; U = ubic(h); T = N.tramosRecorrido(rec, h);
      morph = movReducido() ? null : { de, k: 0 };
      construir(); if (!libre) enfocar();
      const hh = hipPorId(rec, h), sello = raiz.querySelector('.rc-sello strong'), desc = raiz.querySelector('.rc-hip-desc');
      if (sello) sello.textContent = (hh && hh.nombre) || h;
      if (desc) desc.innerHTML = hipotesisHTML(rec, h);
      raiz.querySelectorAll('.rc-punto').forEach((p, i) => { const u = N.ubicacionEtapa(rec, E[i], h); p.className = `rc-punto c-${u ? u.confianza : N.sinPropuesta(rec, E[i], h) ? 'sinprop' : 'desc'}`; });
      if (tarjeta) tarjeta.innerHTML = tarjetaEtapaHTML(rec, pos.idx, h, fase === 'viaje');
      lienzo.classList.remove('cambia'); void lienzo.offsetWidth; lienzo.classList.add('cambia');
      pedir();
    }
    construir();

    if (!mini) {
      // Arrastre, pellizco y rueda: la cámara deja de seguir al grupo hasta la próxima etapa.
      const punteros = new Map(); let previo = null, recorrido = 0;
      const posP = e => { const r = svg.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
      const estP = () => { const ps = [...punteros.values()]; if (ps.length < 2) return { n: ps.length, c: ps[0], d: 0 }; const [a, c] = ps; return { n: 2, c: [(a[0] + c[0]) / 2, (a[1] + c[1]) / 2], d: Math.hypot(a[0] - c[0], a[1] - c[1]) }; };
      const zoomEn = (px, py, f) => {
        const s = Math.min(Math.min(W, H) / .2, Math.max(.5, v.s * f)), wx = v.cx + (px - W / 2) / v.s, wy = v.cy + (py - H / 2) / v.s;
        v.s = s; v.cx = wx - (px - W / 2) / s; v.cy = wy - (py - H / 2) / s; libre = true; pedir();
      };
      svg.addEventListener('pointerdown', e => { punteros.set(e.pointerId, posP(e)); previo = estP(); if (punteros.size === 1) recorrido = 0; });
      svg.addEventListener('pointermove', e => {
        if (!punteros.has(e.pointerId)) return;
        punteros.set(e.pointerId, posP(e)); const ahora = estP();
        if (previo && ahora.n === previo.n && ahora.c) {
          const dx = ahora.c[0] - previo.c[0], dy = ahora.c[1] - previo.c[1]; recorrido += Math.abs(dx) + Math.abs(dy);
          if (recorrido > 6) { if (!svg.hasPointerCapture(e.pointerId)) try { svg.setPointerCapture(e.pointerId); } catch (er) { /* */ } v.cx -= dx / v.s; v.cy -= dy / v.s; libre = true; pedir(); }
          if (ahora.n === 2 && previo.d > 0) zoomEn(ahora.c[0], ahora.c[1], ahora.d / previo.d);
        }
        previo = ahora;
      });
      const soltar = e => { punteros.delete(e.pointerId); previo = punteros.size ? estP() : null; };
      svg.addEventListener('pointerup', soltar); svg.addEventListener('pointercancel', soltar);
      svg.addEventListener('wheel', e => { e.preventDefault(); const [x, y] = posP(e); zoomEn(x, y, Math.exp(-e.deltaY * 0.0015)); }, { passive: false });
      svg.addEventListener('click', e => { if (recorrido > 6) return; const m = e.target.closest('[data-rc-etapa]'); if (m) ir(+m.dataset.rcEtapa); });
      svg.addEventListener('keydown', e => {
        const paso = 40 / v.s, k = { ArrowLeft: [-paso, 0], ArrowRight: [paso, 0], ArrowUp: [0, -paso], ArrowDown: [0, paso] }[e.key];
        if (k) { e.preventDefault(); v.cx += k[0]; v.cy += k[1]; libre = true; pedir(); }
        else if (e.key === '+' || e.key === '=') zoomEn(W / 2, H / 2, 1.4);
        else if (e.key === '-') zoomEn(W / 2, H / 2, 1 / 1.4);
      });
      const ctrl = lienzo.querySelector('.mapa-ctrl');
      if (ctrl) ctrl.addEventListener('click', e => { const bt = e.target.closest('[data-z]'); if (!bt) return; const z = +bt.dataset.z; if (z === 0) { mirar(todo(), 3, .1); libre = false; pedir(); } else zoomEn(W / 2, H / 2, z > 0 ? 1.5 : 1 / 1.5); });
      // Barra de progreso: pulsar o arrastrar elige etapa; flechas, Inicio y Fin con el teclado.
      if (barra) {
        const idxDe = e => { const r = barra.querySelector('.rc-pista').getBoundingClientRect(); return Math.round(Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)) * (n - 1)); };
        let arr = false;
        barra.addEventListener('pointerdown', e => { arr = true; try { barra.setPointerCapture(e.pointerId); } catch (er) { /* */ } const i = idxDe(e); if (i !== pos.idx) ir(i); });
        barra.addEventListener('pointermove', e => { if (arr) { const i = idxDe(e); if (i !== pos.idx) ir(i); } });
        const fin = () => { arr = false; }; barra.addEventListener('pointerup', fin); barra.addEventListener('pointercancel', fin);
        barra.addEventListener('keydown', e => {
          const d = { ArrowLeft: -1, ArrowDown: -1, ArrowRight: 1, ArrowUp: 1 }[e.key];
          if (d) { e.preventDefault(); ir(pos.idx + d, d > 0); } else if (e.key === 'Home') { e.preventDefault(); ir(0); } else if (e.key === 'End') { e.preventDefault(); ir(n - 1); }
        });
      }
      raiz.addEventListener('click', e => {
        if (e.target.closest('[data-rc-play]')) { alternar(); return; }
        const p = e.target.closest('[data-rc-paso]'); if (p) { const d = +p.dataset.rcPaso; ir(pos.idx + d, d > 0); return; }
        const g = e.target.closest('[data-rc-ir]'); if (g) { ir(+g.dataset.rcIr); lienzo.scrollIntoView({ block: 'nearest', behavior: movReducido() ? 'auto' : 'smooth' }); }
      });
      raiz.addEventListener('change', e => {
        const t = e.target;
        if (t.name === 'rc-hip') cambiarHip(t.value);
        else if (t.name === 'rc-vel') { estadoRC.vel = +t.value || 1; store.set('biblia.rcVel', estadoRC.vel); }
      });
      const alOcultar = () => { if (!svg.isConnected) { document.removeEventListener('visibilitychange', alOcultar); return; } if (document.hidden && jugando) alternar(); };
      document.addEventListener('visibilitychange', alOcultar);
    }
    const medir = () => { const r = svg.getBoundingClientRect(); if (r.width > 10 && r.height > 10) { W = r.width; H = r.height; return true; } return false; };
    let listo = false;
    const alCambiar = () => { if (!medir()) return; const prim = !listo; listo = true; enfocar(); if (prim) { v.cx = obj.cx; v.cy = obj.cy; v.s = obj.s; } pintar(); pedir(); };
    if (window.ResizeObserver) new ResizeObserver(alCambiar).observe(svg);
    alCambiar(); if (!listo) { listo = true; enfocar(); v.cx = obj.cx; v.cy = obj.cy; v.s = obj.s; pintar(); }
    tarjetaA(pos.idx, false); if (tarjeta) tarjeta.classList.remove('entra');
    botones();
  }

  // Acompañante: «En el camino» cuando el pasaje toca una etapa de un recorrido.
  function enCaminoHTML(p, sec, I) {
    if (!N.listaRecorridos(RCV()).length || !p) return '';
    const lb = N.libroDe(p), refs = N.versiculosDe(D, p).map(v => v.ref);
    const rs = N.recorridosDeRefs(RCV(), refs, estado.activo ? `${lb} ${estado.activo}` : null);
    if (!rs.length) return '';
    return sec('En el camino', rs.map(x => {
      const E = N.etapasOrdenadas(x.rec), e = E[x.actual], h = hipPorId(x.rec, hipDe(x.rec));
      return `<div class="rc rc-mini" data-rc="${esc(JSON.stringify({ rec: x.rec.id, idx: x.actual, aqui: x.aqui, mini: true }))}">
        <div class="mapa mini"><div class="mapa-lienzo rc-lienzo"></div></div>
        <p class="rc-mini-txt"><strong>${esc(x.rec.titulo || x.rec.id)}</strong> · etapa ${x.actual + 1} de ${E.length}: <strong>${esc(e.nombre || '')}</strong></p>
        ${x.aqui.length > 1 ? `<p class="meta">En este pasaje: ${x.aqui.map(i => `<a href="${hrefEtapa(x.rec, E[i])}">${esc(E[i].nombre || '')}</a> (${esc(E[i].ref || '')})`).join(' · ')}</p>` : ''}
        <p class="meta">Trazado según la hipótesis «${esc((h && h.nombre) || '')}» <span class="etiqueta externa">Fuente externa</span>: no es un hecho.</p>
        <p><a class="boton secundario" href="${hrefEtapa(x.rec, e)}">Ver el recorrido completo</a></p></div>`;
    }).join(''), I('M4 16c2.5 0 3-3 6-4s3-5 6-6M3 16h2M15 5h2'));
  }

  /* ---------- Tabernáculo (datos/tabernaculo.js): plano a escala, relieve isométrico y montaje de Éx 40 ---------- */
  // Medidas: codos con su cita (Texto/Inferido/Cálculo); metros siempre como Cálculo según el codo elegido.
  // Posición en el plano: Texto (trazo continuo), Inferida (discontinuo) o Tradición (punteado), dicho en la tarjeta.
  let TB = window.BIBLIA_TABERNACULO || null;
  const TB_CAPA_TXT = { atrio: 'Atrio', estructura: 'Estructura', cortinas: 'Cortinas', mobiliario: 'Mobiliario' };
  const TB_POS_TXT = { texto: 'Texto', inferido: 'Inferida', tradicion: 'Tradición' };
  const TB_POS_DESC = { texto: 'el texto dice dónde va.', inferido: 'el texto no da el punto exacto; se deduce de lo que sí dice.', tradicion: 'el texto no la da; se sigue la disposición habitual de las reconstrucciones.' };
  const TB_POS_TRAZO = { texto: 'trazo continuo', inferido: 'trazo discontinuo', tradicion: 'trazo punteado' };
  const certPos = c => c === 'texto' || c === 'tradicion' ? c : 'inferido';
  const estadoTB = { sel: null, modo: 'leido', capas: null }; // lectura en orden: siempre «Según voy leyendo»
  let TBM = null; // motor de la vista completa montada
  const numES = (n, d) => Number(n).toLocaleString('es-ES', { maximumFractionDigits: d === undefined ? 2 : d });
  const codoTB = () => N.tbCodo(TB, store.get('biblia.codo', null));
  const capasTB = () => { if (!estadoTB.capas) { const g = store.get('biblia.tbCapas', null); estadoTB.capas = new Set(Array.isArray(g) ? g.filter(x => N.TB_GRUPOS.includes(x)) : N.TB_GRUPOS); } return estadoTB.capas; };
  const vistaTBGuardada = () => store.get('biblia.tbVista', 'plano') === 'relieve' ? 'relieve' : 'plano';
  // «Ex 25:10-22; Ex 37:1-9» → enlaces a Leer (al primer versículo de cada tramo).
  const refRangoHTML = s => String(s || '').split(/\s*;\s*/).filter(Boolean).map(x => { const r = N.parseRef(x.split(/\s*[-–]\s*/)[0]); return r ? `<a class="ref" href="${hrefRef(r)}">${esc(x)}</a>` : esc(x); }).join('; ');
  const hrefTB = id => `#tabernaculo${id ? '/' + encodeURIComponent(id) : ''}`;
  const ICO_TB = '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M2.5 15.5h15M4 15.5V8.5h12v7M4 8.5l6-4 6 4M8.5 15.5v-4h3v4"/></svg>';

  /* Escena: primitivas en codos (x oriente, y norte, z alto) que el pintor proyecta en plano (k = 0) o relieve (k = 1). */
  const TB_C = Math.cos(Math.PI / 6), TB_S = 0.5;
  const proyTB = (x, y, z, k) => [x + ((x + y) * TB_C - x) * k, -y + ((x - y) * TB_S - (z || 0) + y) * k];
  const rectTB = r => [[r.x0, r.y0], [r.x1, r.y0], [r.x1, r.y1], [r.x0, r.y1]];
  function escenaTB(op) {
    const Z = N.tbDisposicion(TB), at = Z.find(z => z.id === 'atrio'), dentro = Z.filter(z => z.id !== 'atrio');
    const piezas = N.tbPiezas(TB), capas = op.capas, ver = id => !op.visibles || op.visibles.has(id);
    const S ={ suelo: [], cuerpos: [], techo: [], puntos: [], etq: [], at, dentro, extra: [] };
    if (at) S.suelo.push({ pts: rectTB(at), cls: 'tb-z tb-z-atrio', cert: 'texto', etq: at.nombre, c: [(at.x0 + at.x1) / 2, at.y0 + 3] });
    dentro.forEach(z => S.suelo.push({ pts: rectTB(z), cls: 'tb-z tb-z-' + z.id, cert: certPos(z.certeza), etq: z.nombre, c: [(z.x0 + z.x1) / 2, (z.y0 + z.y1) / 2] }));
    const u = dentro.length ? { x0: Math.min(...dentro.map(z => z.x0)), y0: Math.min(...dentro.map(z => z.y0)), x1: Math.max(...dentro.map(z => z.x1)), y1: Math.max(...dentro.map(z => z.y1)) } : null;
    const hT = dentro.reduce((m, z) => Math.max(m, z.alto || 0), 0);
    const pared = (a, b, h, cls, cert, id, sinAlto) => S.cuerpos.push({ pared: [a, b], h, cls, cert, id, sinAlto, d: (a[0] + b[0]) / 2 - (a[1] + b[1]) / 2 });
    // Contornos (`plano.rect`): la estructura levanta paredes al sur, norte y occidente (la entrada queda al oriente);
    // las cortinas cubren el rectángulo; el atrio lo cierra por los cuatro lados. Piezas que comparten contorno se dibujan una vez.
    const hechos = new Set(), ord = new Map(N.tbMontaje(TB).map((m, i) => [m.pieza, i]));
    const piezasOrd = piezas.slice().sort((a, b) => (a.grupo === 'mobiliario') - (b.grupo === 'mobiliario') || (ord.has(a.id) ? ord.get(a.id) : 999) - (ord.has(b.id) ? ord.get(b.id) : 999));
    piezasOrd.forEach(p => {
      if (!ver(p.id) || !capas.has(p.grupo)) return;
      const hu = N.tbHuella(p); if (!hu) return;
      const cert = certPos(p.plano.certeza), cls = `tb-p tb-g-${p.grupo}`;
      if (hu.contorno) {
        const r = hu.rect, q = rectTB(r), clave = p.grupo + '|' + [r.x0, r.y0, r.x1, r.y1].join(',');
        if (hechos.has(clave)) return; hechos.add(clave);
        if (p.grupo === 'cortinas') S.techo.push({ id: p.id, pts: q, z: hT, cls: cls + ' tb-techo', cert });
        else if (p.grupo === 'atrio') { const h = hu.alto !== null ? hu.alto : (at && at.alto) || 0; [[q[3], q[2]], [q[0], q[3]], [q[1], q[2]], [q[0], q[1]]].forEach(([a, b]) => pared(a, b, h, cls, cert, p.id)); }
        else [[q[3], q[2]], [q[0], q[3]], [q[0], q[1]]].forEach(([a, b]) => pared(a, b, hT, cls, cert, p.id));
        return;
      }
      // Sin medidas pero con orientación y dentro del tabernáculo (velo, cortina de la entrada): línea de lado a lado, plana.
      if (hu.punto && u && p.plano.rot !== undefined && p.plano.rot !== null && hu.x >= u.x0 && hu.x <= u.x1 && hu.y >= u.y0 && hu.y <= u.y1) {
        const v = Math.round(+p.plano.rot) % 180 === 90;
        pared(v ? [hu.x, u.y0] : [u.x0, hu.y], v ? [hu.x, u.y1] : [u.x1, hu.y], 0, cls + ' tb-linea', cert, p.id, true);
        return;
      }
      // Pieza plana sobre otra con alto en el mismo punto (el propiciatorio, encima del arca): se apoya en ella.
      const base = hu.alto === null ? piezas.filter(o => o.id !== p.id && o.plano && +o.plano.x === hu.x && +o.plano.y === hu.y).reduce((m, o) => { const h2 = N.tbHuella(o); return h2 && !h2.contorno && h2.alto ? Math.max(m, h2.alto) : m; }, 0) : 0;
      if (hu.punto) S.puntos.push({ id: p.id, x: hu.x, y: hu.y, z0: base, cls, cert });
      else S.cuerpos.push({ id: p.id, esq: hu.esquinas, h: hu.alto || 0, z0: base, sinAlto: hu.alto === null, cls, cert, d: hu.x - hu.y + 0.01 + base * 0.001 });
    });
    if (op.humana && op.codo) {
      const h = 170 / op.codo.cm, r = 25 / op.codo.cm, sp = op.sel && N.tbHuella(N.tbPieza(TB, op.sel));
      const x = sp ? Math.max(...sp.esquinas.map(c => c[0])) + 1.2 : at ? at.x1 - 5 : 0, y = sp ? sp.y - 1.2 : at ? at.y1 / 2 - 14 : 0;
      S.cuerpos.push({ humana: true, x, y, h, r, d: x - y });
    }
    if (at) S.extra.push({ flecha: [[at.x1 + 4, (at.y0 + at.y1) / 2], [at.x1 + 16, (at.y0 + at.y1) / 2]], rotulo: [at.x1 + 30, (at.y0 + at.y1) / 2] });
    S.cuerpos.sort((a, b) => a.d - b.d);
    return S;
  }
  // Caja que encierra la escena proyectada (para encuadrar la cámara).
  function cajaTB(S, k, soloId) {
    const pts = [];
    const add = (x, y, z) => pts.push(proyTB(x, y, z, k));
    if (soloId) {
      const hu = N.tbHuella(N.tbPieza(TB, soloId)); if (!hu) return null;
      hu.esquinas.forEach(c => { add(c[0], c[1], 0); add(c[0], c[1], hu.alto || 0); });
      const m = 9; // contexto alrededor de la pieza (codos)
      add(hu.x - m, hu.y - m, 0); add(hu.x + m, hu.y + m, 0); add(hu.x - m, hu.y + m, 0); add(hu.x + m, hu.y - m, 0);
    } else {
      S.suelo.forEach(s => s.pts.forEach(c => add(c[0], c[1], 0)));
      S.cuerpos.forEach(b => { if (b.pared) b.pared.forEach(c => { add(c[0], c[1], 0); add(c[0], c[1], b.h); }); else if (b.esq) b.esq.forEach(c => add(c[0], c[1], b.h)); });
      S.techo.forEach(t => t.pts.forEach(c => add(c[0], c[1], t.z)));
      S.puntos.forEach(p => add(p.x, p.y, 0));
      S.extra.forEach(e => e.flecha.concat([e.rotulo]).forEach(c => add(c[0], c[1], 0)));
    }
    if (!pts.length) return null;
    const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
    return { x0: Math.min(...xs), y0: Math.min(...ys), x1: Math.max(...xs), y1: Math.max(...ys) };
  }
  const encuadreTB = (c, W, H, margen) => { if (!c) return { cx: 0, cy: 0, s: 1 }; const m = margen === undefined ? 28 : margen; return { cx: (c.x0 + c.x1) / 2, cy: (c.y0 + c.y1) / 2, s: Math.max(0.05, Math.min((W - 2 * m) / Math.max(1, c.x1 - c.x0), (H - 2 * m) / Math.max(1, c.y1 - c.y0))) }; };
  // Pinta la escena en coordenadas de pantalla (los textos conservan su tamaño a cualquier zoom).
  function svgTB(S, op) {
    const { k, cam, W, H } = op;
    const P = (x, y, z) => { const q = proyTB(x, y, z, k); return [(q[0] - cam.cx) * cam.s + W / 2, (q[1] - cam.cy) * cam.s + H / 2]; };
    const pts = l => l.map(p => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join(' ');
    const ap = op.aparicion || new Map(), resaltar = op.resaltar || null;
    const estadoP = id => (id === op.sel ? ' sel' : '') + (resaltar ? (resaltar.has(id) ? ' resaltada' : ' atenuada') : '');
    let out = '<g class="tb-suelo">';
    S.suelo.forEach(s => { out += `<polygon class="${s.cls} cert-${s.cert}" points="${pts(s.pts.map(c => P(c[0], c[1], 0)))}"/>`; });
    out += '</g><g class="tb-cuerpos">';
    S.cuerpos.forEach(b => {
      if (b.humana) {
        const pie = P(b.x, b.y, 0), cab = P(b.x, b.y, b.h * 0.9), rr = Math.max(2.5, b.r * cam.s);
        out += k < 0.02 ? `<g class="tb-humana"><circle cx="${pie[0].toFixed(1)}" cy="${pie[1].toFixed(1)}" r="${Math.max(3, rr * 1.4).toFixed(1)}"/></g>`
          : `<g class="tb-humana"><path d="M${pie[0].toFixed(1)} ${pie[1].toFixed(1)}L${cab[0].toFixed(1)} ${(cab[1] + rr).toFixed(1)}"/><circle cx="${cab[0].toFixed(1)}" cy="${cab[1].toFixed(1)}" r="${rr.toFixed(1)}"/></g>`;
        return;
      }
      if (b.pared) {
        const [a, c] = b.pared, t0 = ap.get(b.id), t = t0 === undefined ? 1 : Math.min(1, Math.max(0, t0)), e = 1 - Math.pow(1 - t, 3), hh = b.h * e;
        out += `<g class="${b.cls} tb-pared cert-${b.cert}${b.id ? estadoP(b.id) : ''}"${b.id ? ` data-tb-pieza="${esc(b.id)}"` : ''}${t < 1 ? ` style="opacity:${e.toFixed(2)}"` : ''}>${b.h > 0 ? `<polygon class="cara" points="${pts([P(a[0], a[1], 0), P(c[0], c[1], 0), P(c[0], c[1], hh), P(a[0], a[1], hh)])}"/>` : ''}<path class="pie" d="M${pts([P(a[0], a[1], 0), P(c[0], c[1], 0)]).replace(' ', 'L')}"/></g>`;
        return;
      }
      const t0 = ap.get(b.id), t = t0 === undefined ? 1 : Math.min(1, Math.max(0, t0)), e = 1 - Math.pow(1 - t, 3), dz = (1 - e) * 14 + (b.z0 || 0);
      let g = `<g class="${b.cls} cert-${b.cert}${estadoP(b.id)}${b.sinAlto ? ' sin-alto' : ''}" data-tb-pieza="${esc(b.id)}"${t < 1 ? ` style="opacity:${e.toFixed(2)}"` : ''}>`;
      if (b.h > 0 && k > 0.001) b.esq.forEach((a, i) => {
        const c = b.esq[(i + 1) % 4], dx = c[0] - a[0], dy = c[1] - a[1]; if (dx + dy <= 1e-9) return;
        g += `<polygon class="${Math.abs(dx) >= Math.abs(dy) ? 'cs' : 'ce'}" points="${pts([P(a[0], a[1], dz), P(c[0], c[1], dz), P(c[0], c[1], b.h + dz), P(a[0], a[1], b.h + dz)])}"/>`;
      });
      g += `<polygon class="tapa" points="${pts(b.esq.map(c => P(c[0], c[1], b.h + dz)))}"/>`;
      if (t < 1) { const m = P((b.esq[0][0] + b.esq[2][0]) / 2, (b.esq[0][1] + b.esq[2][1]) / 2, 0); g += `<circle class="tb-onda" cx="${m[0].toFixed(1)}" cy="${m[1].toFixed(1)}" r="${(8 + 34 * e).toFixed(1)}" style="opacity:${(1 - e).toFixed(2)}"/>`; }
      out += g + '</g>';
    });
    out += '</g><g class="tb-techos">';
    S.techo.forEach(tc => {
      const t0 = ap.get(tc.id), t = t0 === undefined ? 1 : Math.min(1, Math.max(0, t0)), e = 1 - Math.pow(1 - t, 3);
      out += `<g class="${tc.cls} cert-${tc.cert}${estadoP(tc.id)}" data-tb-pieza="${esc(tc.id)}"${t < 1 ? ` style="opacity:${e.toFixed(2)}"` : ''}><polygon class="tapa" points="${pts(tc.pts.map(c => P(c[0], c[1], tc.z + (1 - e) * 8)))}"/></g>`;
    });
    out += '</g><g class="tb-puntos">';
    S.puntos.forEach(p => {
      const q = P(p.x, p.y, p.z0 || 0), t0 = ap.get(p.id), t = t0 === undefined ? 1 : Math.min(1, t0);
      out += `<g class="${p.cls} tb-punto cert-${p.cert}${estadoP(p.id)}" data-tb-pieza="${esc(p.id)}"${t < 1 ? ` style="opacity:${t.toFixed(2)}"` : ''}><circle class="toque" cx="${q[0].toFixed(1)}" cy="${q[1].toFixed(1)}" r="14"/><circle class="tapa" cx="${q[0].toFixed(1)}" cy="${q[1].toFixed(1)}" r="5.5"/></g>`;
    });
    out += '</g>';
    S.extra.forEach(x => {
      const a = P(x.flecha[0][0], x.flecha[0][1], 0), b = P(x.flecha[1][0], x.flecha[1][1], 0), dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1, ux = dx / l, uy = dy / l;
      const h1 = [b[0] - ux * 9 - uy * 5, b[1] - uy * 9 + ux * 5], h2 = [b[0] - ux * 9 + uy * 5, b[1] - uy * 9 - ux * 5];
      out += `<g class="tb-oriente" aria-hidden="true"><path d="M${a[0].toFixed(1)} ${a[1].toFixed(1)}L${b[0].toFixed(1)} ${b[1].toFixed(1)}"/><polygon points="${pts([b, h1, h2])}"/>
        <text x="${(b[0] + ux * 6).toFixed(1)}" y="${(b[1] + uy * 6 + 4).toFixed(1)}" text-anchor="${ux > 0.3 ? 'start' : 'middle'}">${op.mini ? 'E' : 'Oriente'}</text></g>`;
    });
    // Rótulos: zonas, piezas (las grandes y la elegida primero), «alto no indicado» en relieve y la figura humana.
    const items = [];
    if (!op.mini || resaltar) {
      const vistos = new Set();
      S.cuerpos.concat(S.puntos, S.techo).forEach(b => {
        if (!b.id || vistos.has(b.id) || (resaltar && !resaltar.has(b.id))) return;
        if ((b.pared && !b.sinAlto || b.pts) && b.id !== op.sel) return; // contornos: solo rotulados al elegirlos
        vistos.add(b.id);
        const p = N.tbPieza(TB, b.id), q = b.esq ? P((b.esq[0][0] + b.esq[2][0]) / 2, (b.esq[0][1] + b.esq[2][1]) / 2, b.h + (b.z0 || 0))
          : b.pared ? P((b.pared[0][0] + b.pared[1][0]) / 2, (b.pared[0][1] + b.pared[1][1]) / 2, b.h) : b.pts ? P((b.pts[0][0] + b.pts[2][0]) / 2, (b.pts[0][1] + b.pts[2][1]) / 2, b.z) : P(b.x, b.y, b.z0 || 0);
        const sinAlto = k > 0.5 && (b.sinAlto || b.x !== undefined);
        items.push({ id: b.id, x: q[0], y: q[1], texto: p.nombre + (sinAlto && (b.id === op.sel || resaltar || p.grupo === 'mobiliario') ? ' (alto no indicado en el texto)' : ''), prioridad: (b.id === op.sel ? 100 : 0) + (p.grupo === 'mobiliario' ? 20 : 0) + (resaltar ? 10 : 0) });
      });
    }
    if (!op.mini) S.suelo.forEach((s, i) => { const q = P(s.c[0], s.c[1], 0); items.push({ id: 'z' + i, x: q[0], y: q[1], texto: s.etq, prioridad: 5, zona: true }); });
    const etqs = N.colocarEtiquetas(items, W, H, op.mini ? 6 : 24), porId = new Map(items.map(i => [i.id, i]));
    out += '<g class="tb-etiquetas" aria-hidden="true">' + etqs.map(e => `<text class="${porId.get(e.id).zona ? 'tb-etq-zona' : 'tb-etq'}${e.id === op.sel ? ' sel' : ''}" x="${e.x.toFixed(1)}" y="${e.y.toFixed(1)}" text-anchor="${e.anc}">${esc(e.texto)}</text>`).join('');
    const hum = S.cuerpos.find(b => b.humana);
    if (hum && !op.mini) { const q = P(hum.x, hum.y, k > 0.5 ? hum.h : 0); const izq = q[0] + 270 > W; out += `<text class="tb-etq-humana" x="${(q[0] + (izq ? -8 : 8)).toFixed(1)}" y="${(q[1] - 6).toFixed(1)}" text-anchor="${izq ? 'end' : 'start'}">figura de referencia de 1,70 m (ilustrativa)</text>`; }
    return out + '</g>';
  }
  // Mini plano estático (acompañante): planta con las piezas del pasaje resaltadas.
  function miniPlanoTB(ids) {
    const W = 320, H = 170, op = { capas: new Set(N.TB_GRUPOS), visibles: null, humana: false };
    const S = escenaTB(op), dentro = S.dentro, hs = ids.map(id => N.tbHuella(N.tbPieza(TB, id))).filter(Boolean);
    // Si todo lo resaltado cae dentro del tabernáculo, el encuadre se acerca a él; si no, todo el atrio.
    const u = dentro.length && { x0: Math.min(...dentro.map(z => z.x0)) - 4, y0: Math.min(...dentro.map(z => z.y0)) - 4, x1: Math.max(...dentro.map(z => z.x1)) + 4, y1: Math.max(...dentro.map(z => z.y1)) + 4 };
    const cerca = u && hs.length && hs.every(h => h.esquinas.every(c => c[0] >= u.x0 && c[0] <= u.x1 && c[1] >= u.y0 && c[1] <= u.y1));
    const cam = encuadreTB(cerca ? { x0: u.x0, y0: -u.y1, x1: u.x1, y1: -u.y0 } : cajaTB(S, 0), W, H, 12);
    return `<svg class="tb-svg tb-mini-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc('Plano del tabernáculo con ' + ids.map(id => (N.tbPieza(TB, id) || {}).nombre).join(', ') + ' resaltado')}">${svgTB(S, { k: 0, cam, W, H, mini: true, resaltar: new Set(ids) })}</svg>`;
  }

  // Insignia con «Tradición» además de Texto, Inferido y Cálculo.
  const insigniaTB = (c, ref) => c === 'tradicion' ? `<span class="insignia inferido tradicion" title="Tradición: lectura de una fuente externa, no está escrito">Tradición${ref ? ' · ' + refHTML(ref) : ''}</span>` : insignia(c || 'inferido', ref);
  const calcTB = id => { const c = id && (TB.calculos || []).find(x => x && x.id === id); return c ? `<button type="button" class="enlace-boton tb-ver-calc" data-tb-calc="${esc(id)}">Ver el cálculo</button>` : ''; };
  const fuenteExtTB = (f, url) => f ? `<span class="tb-fuente"><span class="etiqueta externa">Fuente externa</span> ${enlaceExt(String(f).replace(/^Fuente externa:\s*/i, ''), url)}</span>` : '';
  // Una medida: codos con su certeza y cita, de dónde sale si no es del texto, y su equivalencia en metros (Cálculo).
  function medidaTB(etq, m, codo, faltaTxt) {
    const c = N.tbCodos(m);
    if (c === null) return `<div class="tb-med"><dt>${etq}</dt><dd><span class="vacio">${faltaTxt || 'No indicado en el texto'}</span></dd></div>`;
    const mts = codo ? N.codosAMetros(c, codo.cm) : null;
    return `<div class="tb-med"><dt>${etq}</dt><dd><span class="tb-cifra"><strong>${numES(c)} ${c === 1 ? 'codo' : 'codos'}</strong>${insigniaTB(m.certeza, m.ref)}</span>
      ${m.cita ? `<q class="tb-cita">${esc(m.cita)}</q>` : ''}${fuenteExtTB(m.fuente, m.url)}${calcTB(m.calculo)}
      ${m.nota ? `<span class="nota">${esc(m.nota)}</span>` : ''}
      ${mts !== null ? `<span class="tb-metros">≈ <strong>${numES(mts)} m</strong>${insignia('calculo')}<span class="meta">${numES(c)} × ${numES(codo.cm, 1)} cm (${esc(codo.nombre || codo.id)})</span></span>` : ''}</dd></div>`;
  }
  const citaRefTB = (x, cert) => x ? `${x.ref || cert ? insigniaTB(cert || x.certeza || 'texto', x.ref) : ''}${x.cita ? `<q class="tb-cita">${esc(x.cita)}</q>` : ''}${fuenteExtTB(x.fuente, x.url)}${calcTB(x.calculo)}` : '';
  const codoNotaHTML = codo => codo ? `${esc(codo.nombre || codo.id)} = ${numES(codo.cm, 1)} cm. ${fuenteExtTB(codo.fuente || 'sin fuente indicada', codo.url)}${codo.cita_fuente ? ` <q class="tb-cita">${esc(codo.cita_fuente)}</q>` : ''}${codo.nota ? ` <details class="plegable tb-codo-nota"><summary>Sobre este valor</summary><p class="nota">${esc(codo.nota)}</p></details>` : ''}` : '';
  function tarjetaTB(id) {
    const codo = codoTB(), p = id && N.tbPieza(TB, id);
    if (!p) {
      const Z = (TB.zonas || []).filter(z => z && z.id);
      const o = TB.orientacion;
      return `<div class="tb-tarjeta-cab"><p class="tb-grupo">Para empezar</p><h2>Toca una pieza</h2></div>
        <p class="meta">Cada pieza dice sus medidas en codos con su cita y su equivalencia en metros según el codo elegido.</p>
        ${o ? `<section class="tb-sec"><h3>Orientación</h3><p>${esc(o.texto || '')}</p>${citaRefTB(o, 'texto')}${(o.otras || []).length ? `<ul class="tb-lista">${o.otras.map(x => `<li>${esc(x.texto || '')}${citaRefTB(x, 'texto')}</li>`).join('')}</ul>` : ''}</section>` : ''}
        ${Z.length ? `<section class="tb-sec"><h3>Zonas</h3>${Z.map(z => `<h4>${esc(z.nombre || z.id)}</h4><dl class="tb-medidas">${medidaTB('Largo', z.largo, codo)}${medidaTB('Ancho', z.ancho, codo)}${z.alto ? medidaTB('Alto', z.alto, codo) : ''}</dl>${z.nota ? `<p class="nota">${esc(z.nota)}</p>` : ''}`).join('')}</section>` : ''}`;
    }
    const m = p.medidas || {}, hu = N.tbHuella(p), cert = certPos((p.plano || {}).certeza), z = p.zona || {}, zn = z.id && N.tbZona(TB, z.id);
    const pasos = N.tbMontaje(TB).filter(x => x.pieza === p.id);
    const imgs = R ? permitidos(N.tbRecursos(R, p)) : [];
    const ninguna = ['largo', 'ancho', 'alto'].every(k => N.tbCodos(m[k]) === null);
    return `<div class="tb-tarjeta-cab"><p class="tb-grupo">${esc(TB_CAPA_TXT[p.grupo] || p.grupo || '')}${zn ? ' · ' + esc(zn.nombre || zn.id) : ''}</p><h2 id="tb-nombre">${esc(p.nombre)}</h2>
        <button type="button" class="cerrar" data-tb-cerrar aria-label="Cerrar la tarjeta"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 5l10 10M15 5L5 15"/></svg></button></div>
      ${(p.plano && p.plano.relacion || []).length ? `<section class="tb-sec"><h3>Dónde la pone el texto</h3><ul class="tb-lista">${p.plano.relacion.map(x => `<li><strong>${esc(x.texto || '')}</strong>${citaRefTB(x, 'texto')}</li>`).join('')}</ul></section>` : ''}
      ${hu ? `<p class="tb-pos pos-${cert}"><span class="tb-trazo" aria-hidden="true"></span><span><strong>${cert === 'texto' ? 'Posición en el plano: Texto' : `Coordenada del plano: ${TB_POS_TXT[cert]}`}</strong> (${TB_POS_TRAZO[cert]}): ${TB_POS_DESC[cert]}${p.plano.nota ? ' ' + esc(p.plano.nota) : ''}</span></p>` : '<p class="tb-pos pos-tradicion"><span>Sin posición en el plano: no se dibuja.</span></p>'}
      <section class="tb-sec"><h3>Medidas</h3>
        ${ninguna ? '<p class="vacio-txt">El texto no da sus medidas: se marca como un punto en el plano.</p>' : `<dl class="tb-medidas">${medidaTB('Largo', m.largo, codo)}${medidaTB('Ancho', m.ancho, codo)}${medidaTB('Alto', m.alto, codo, hu && hu.contorno ? 'No indicado para esta pieza: en el relieve toma el alto de su zona' : 'No indicado en el texto: en el relieve se dibuja plana')}</dl>`}
        ${p.cantidad && p.cantidad.valor !== undefined && p.cantidad.valor !== null ? `<p class="tb-cant"><strong>Cantidad: ${esc(p.cantidad.valor)}</strong>${citaRefTB(p.cantidad, p.cantidad.certeza || 'texto')}</p>` : ''}</section>
      ${(p.materiales || []).length ? `<section class="tb-sec"><h3>Materiales</h3><ul class="tb-lista">${p.materiales.map(x => `<li><strong>${esc(x.nombre)}</strong>${citaRefTB(x, x.certeza || 'texto')}</li>`).join('')}</ul></section>` : ''}
      ${p.funcion && p.funcion.texto ? `<section class="tb-sec"><h3>Función</h3><p>${esc(p.funcion.texto)}</p>${citaRefTB(p.funcion, p.funcion.certeza || 'texto')}</section>` : ''}
      ${zn ? `<section class="tb-sec"><h3>Dónde va</h3><p><strong>${esc(zn.nombre || zn.id)}</strong>${insigniaTB(z.certeza, z.ref)}</p>${z.cita ? `<q class="tb-cita">${esc(z.cita)}</q>` : ''}${z.nota ? `<p class="nota">${esc(z.nota)}</p>` : ''}</section>` : ''}
      <section class="tb-sec"><h3>En el texto</h3><ul class="tb-refs">
        ${p.instruccion ? `<li><span class="meta">Instrucción</span> ${refRangoHTML(p.instruccion)}</li>` : ''}
        ${p.construccion ? `<li><span class="meta">Construcción</span> ${refRangoHTML(p.construccion)}</li>` : ''}
        ${pasos.map(x => `<li><span class="meta">Montaje</span> ${insigniaTB(x.certeza || 'texto', x.ref)}${x.cita ? ` <q class="tb-cita">${esc(x.cita)}</q>` : ''}${x.certeza && x.certeza !== 'texto' ? ` <span class="nota">Identificación inferida${x.nota ? ': ' + esc(x.nota) : ''}</span>` : ''}</li>`).join('')}</ul></section>
      ${p.nota ? `<p class="nota">${esc(p.nota)}</p>` : ''}
      ${imgs.length ? `<section class="tb-sec"><h3>Cómo se ha imaginado</h3><p class="meta">No son datos del texto: reconstrucciones modernas y obras de arte, cada una con su autor.</p><ul class="rec-lista">${imgs.map(recItemHTML).join('')}</ul></section>` : ''}`;
  }
  function calculosTBHTML() {
    // Solo los cálculos cuyos pasos citan versículos ya accesibles (lectura en orden).
    const cs = (TB.calculos || []).filter(c => c && (c.texto || c.resultado !== undefined) && (c.pasos || []).every(x => !x || !x.ref || refOk(x.ref)) && (c.pasos || []).some(x => x && x.ref));
    if (!cs.length) return '';
    const paso = x => `<li${x.supuesto ? ' class="convencion"' : ''}>${x.supuesto ? '<span class="etiqueta">supuesto</span> ' : ''}${esc(x.texto || '')}${x.valor !== undefined && x.valor !== null ? ` <strong>= ${esc(typeof x.valor === 'number' ? numES(x.valor) : x.valor)}</strong>` : ''}${x.ref ? ' · ' + refHTML(x.ref) : ''}${x.cita ? `<q>${esc(x.cita)}</q>` : ''}${fuenteExtTB(x.fuente, x.url)}${calcTB(x.calculo)}${x.nota ? ` <span class="nota">${esc(x.nota)}</span>` : ''}</li>`;
    return `<section class="tb-calculos" aria-labelledby="t-tb-calc"><h2 id="t-tb-calc">Cálculos (${cs.length})</h2><p class="meta">Cifras que el texto no da de una vez: salen de varios versículos, paso a paso. Algunas dependen de una lectura tradicional o de un supuesto, y lo dicen.</p>
      ${cs.map(c => `<details class="plegable tb-calc" id="tb-calc-${esc(c.id || '')}"><summary><span>${esc(c.texto || '')}${c.resultado !== undefined && c.resultado !== null && !String(c.texto || '').includes('=') ? `: <strong>${esc(typeof c.resultado === 'number' ? numES(c.resultado) : c.resultado)}</strong>` : ''}</span>${insigniaTB(c.certeza || 'calculo')}</summary>
        ${c.operacion ? `<p class="tb-op"><span class="meta">Operación:</span> <code>${esc(String(c.operacion).replace(/\*/g, ' × ').replace(/\//g, ' ÷ ').replace(/\+/g, ' + ').replace(/\s+/g, ' '))}</code>${c.resultado !== undefined && c.resultado !== null ? ` = <strong>${esc(typeof c.resultado === 'number' ? numES(c.resultado) : c.resultado)}</strong>` : ''}</p>` : ''}
        <ol class="rc-pasos">${(c.pasos || []).map(paso).join('')}</ol>${c.nota ? `<p class="nota">${esc(c.nota)}</p>` : ''}</details>`).join('')}</section>`;
  }
  // «Según voy leyendo»: piezas visibles y las que faltan, con el pasaje que las trae.
  const visiblesLeidoTB = () => new Set(N.tbVisiblesLeido(TB, N.pasajes(D), [...pasajesLeidos()]));
  function leidoTBHTML() {
    if (estadoTB.modo !== 'leido') return '';
    const vis = visiblesLeidoTB(), ps = N.tbPiezas(TB).filter(p => p.instruccion), faltan = ps.filter(p => !vis.has(p.id));
    // Las que faltan no se nombran: aparecerán al leer sus instrucciones (lectura en orden).
    return `<p>Ves <strong>${vis.size} de ${ps.length}</strong> piezas: las que tienen leídos (marcados en Leer) todos los pasajes de su instrucción.</p>
      ${faltan.length ? `<p class="meta">${ICO_CANDADO} Faltan ${faltan.length}: irán apareciendo a medida que leas sus instrucciones en Éxodo.</p>` : '<p class="meta">Ya las has leído todas.</p>'}`;
  }

  function vistaTabernaculo(args) {
    const cab = `<p class="tb-volver"><a class="volver" href="#leer/Ex"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M12 4l-6 6 6 6"/></svg>Éxodo</a></p><h1 tabindex="-1">El tabernáculo</h1>`;
    if (!TB || !N.tbPiezas(TB).length) return cab + '<p class="vacio-txt">Los datos del tabernáculo (datos/tabernaculo.js) todavía no están. Cuando lleguen, aquí verás el plano a escala, el relieve y el montaje de Éxodo 40.</p>';
    const visTB = visiblesLeidoTB(), sel = args[0] && N.tbPieza(TB, args[0]) && visTB.has(args[0]) ? args[0] : null;
    estadoTB.sel = sel; estadoTB.modo = 'leido';
    const codo = codoTB(), cs = (TB.codos || []).filter(c => c && c.id && +c.cm > 0), capas = capasTB(), vista = vistaTBGuardada(), M = N.tbMontaje(TB);
    const o = TB.orientacion;
    const porGrupo = N.TB_GRUPOS.map(g => [g, N.tbPiezas(TB).filter(p => p.grupo === g && visTB.has(p.id))]).filter(x => x[1].length);
    const montajeOk = M.length && M.every(m => refOk(m.ref)); // «Armar según Éx 40» cuando Éx 40 ya es accesible
    return `${cab}
      <p class="sub">Medidas y lugares según Éxodo 25–40. Cada cifra dice de dónde sale: <strong>Texto</strong> (con su cita), <strong>Inferido</strong> o <strong>Cálculo</strong>. Los metros son siempre un cálculo según el codo que elijas.</p>
      ${TB.ejemplo ? '<p class="rc-ejemplo">EJEMPLO: datos de prueba. Las posiciones no son una reconstrucción real.</p>' : ''}
      <div class="tb" data-tb>
        <div class="tb-escena">
          <div class="tb-barra">
            <fieldset class="segmentos tb-vista"><legend class="sr">Vista</legend>
              <label><input type="radio" name="tb-vista" value="plano" ${vista === 'plano' ? 'checked' : ''}><span>Plano</span></label>
              <label><input type="radio" name="tb-vista" value="relieve" ${vista === 'relieve' ? 'checked' : ''}><span>Relieve</span></label></fieldset>
            ${cs.length ? `<fieldset class="segmentos tb-codo"><legend class="sr">Codo para pasar a metros</legend>${cs.map(c => `<label><input type="radio" name="tb-codo" value="${esc(c.id)}" ${codo && codo.id === c.id ? 'checked' : ''}><span>${esc(c.nombre || c.id)} <small>${numES(c.cm, 1)} cm</small></span></label>`).join('')}</fieldset>` : ''}
          </div>
          ${codo ? `<p class="meta tb-codo-fuente">${codoNotaHTML(codo)}</p>` : ''}
          <div class="tb-lienzo">
            <svg class="tb-svg" role="group" aria-label="Plano del tabernáculo. Las piezas se pueden elegir también en la lista de debajo."></svg>
            <div class="mapa-ctrl"><button type="button" data-tb-z="1" aria-label="Acercar">+</button><button type="button" data-tb-z="-1" aria-label="Alejar">−</button>
              <button type="button" data-tb-z="0" aria-label="Ver el conjunto"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 7V3h4M13 3h4v4M17 13v4h-4M7 17H3v-4"/></svg></button></div>
            <div class="tb-montaje" aria-live="polite" hidden></div>
          </div>
          ${o ? `<p class="tb-orient meta"><span class="tb-orient-flecha" aria-hidden="true">→</span> Oriente: ${esc(o.texto || '')} ${insignia('texto', o.ref)}${o.cita ? `<q class="tb-cita">${esc(o.cita)}</q>` : ''}</p>` : ''}
          <div class="tb-mando">
            ${montajeOk ? `<button type="button" class="boton" data-tb-armar>${ICO_PLAY}Armar según Éx 40</button>` : ''}
            <p class="tb-modo-fijo meta">${ICO_CANDADO}<span><strong>Según voy leyendo</strong>: la lectura avanza en orden, así que solo se ven las piezas ya leídas.${M.length && !montajeOk ? ' El montaje de Éx 40 se podrá ver al llegar allí.' : ''}</span></p>
          </div>
          <div class="tb-leido" aria-live="polite">${leidoTBHTML()}</div>
          <fieldset class="tb-capas"><legend>Capas</legend>
            ${N.TB_GRUPOS.map(g => `<label class="tb-capa tb-g-${g}"><input type="checkbox" data-tb-capa="${g}" ${capas.has(g) ? 'checked' : ''}><span class="tb-capa-muestra" aria-hidden="true"></span>${TB_CAPA_TXT[g]}</label>`).join('')}
            <label class="tb-capa"><input type="checkbox" id="tb-humana" ${store.get('biblia.tbHumana', false) === true ? 'checked' : ''}>Figura de referencia de 1,70 m (ilustrativa)</label></fieldset>
          <p class="leyenda-mapa tb-leyenda">${['texto', 'inferido', 'tradicion'].map(c => `<span><svg class="tb-ico-trazo pos-${c}" viewBox="0 0 28 10" aria-hidden="true"><path d="M2 5h24"/></svg>Posición: ${TB_POS_TXT[c]}</span>`).join('')}</p>
          <nav class="tb-piezas" aria-label="Piezas">${porGrupo.map(([g, ps]) => `<div class="tb-piezas-grupo"><span class="meta">${TB_CAPA_TXT[g]}</span><ul class="chips">${ps.map(p => `<li><button type="button" class="chip-tb${p.id === sel ? ' sel' : ''}" data-tb-pieza="${esc(p.id)}" aria-pressed="${p.id === sel}">${esc(p.nombre)}</button></li>`).join('')}</ul></div>`).join('')}</nav>
        </div>
        <article class="tb-tarjeta${sel ? ' con-pieza' : ''}" aria-live="polite" aria-labelledby="tb-nombre">${tarjetaTB(sel)}</article>
        ${calculosTBHTML()}
        ${(TB.fuentes || []).length ? `<details class="plegable tb-fuentes"><summary>Fuentes</summary><ul class="rc-fuentes">${TB.fuentes.map(f => `<li><span class="etiqueta externa">Fuente externa</span> ${enlaceExt(f.nombre || f.id || '', f.url)}</li>`).join('')}</ul></details>` : ''}
      </div>`;
  }

  // Motor de la vista completa: transición plano ↔ relieve, cámara, selección y montaje.
  function crearTabernaculo(raiz) {
    raiz.dataset.montado = '1';
    const lienzo = raiz.querySelector('.tb-lienzo'), svg = lienzo.querySelector('svg'), panelM = raiz.querySelector('.tb-montaje');
    const M = N.tbMontaje(TB), DUR_AP = 700;
    let W = 640, H = 420, raf = 0, anim = null, libre = false;
    const E = { k: vistaTBGuardada() === 'relieve' ? 1 : 0, cam: null, ap: new Map() };
    const mont = { activo: false, i: -1, jugando: false, timer: 0, fin: false };
    const suave = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
    const opciones = () => ({ capas: capasTB(), sel: estadoTB.sel, humana: store.get('biblia.tbHumana', false) === true, codo: codoTB(),
      visibles: mont.activo && !mont.fin ? new Set(N.tbColocadas(TB, mont.i + 1)) : estadoTB.modo === 'leido' ? visiblesLeidoTB() : null });
    const objetivo = (k, id) => { const S = escenaTB(Object.assign(opciones(), { visibles: null })); return encuadreTB(cajaTB(S, k, id), W, H, id ? 18 : 28); };
    function medir() { const r = lienzo.getBoundingClientRect(); W = Math.max(200, Math.round(r.width)); H = Math.max(180, Math.round(r.height)); }
    function pintar(ahora) {
      if (!E.cam) E.cam = objetivo(E.k);
      const ap = new Map(); E.ap.forEach((t0, id) => { const t = (ahora - t0) / DUR_AP; if (t < 1) ap.set(id, t); });
      svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
      svg.innerHTML = svgTB(escenaTB(opciones()), Object.assign(opciones(), { k: E.k, cam: E.cam, W, H, aparicion: ap }));
      svg.classList.toggle('relieve', E.k > 0.5);
      return ap.size > 0;
    }
    function cuadro(ahora) {
      raf = 0;
      if (!raiz.isConnected) { clearTimeout(mont.timer); return; }
      let seguir = false;
      if (anim) {
        const t = Math.min(1, (ahora - anim.t0) / anim.dur), e = suave(t), a = anim;
        E.k = a.k0 + (a.k1 - a.k0) * e;
        E.cam = { cx: a.c0.cx + (a.c1.cx - a.c0.cx) * e, cy: a.c0.cy + (a.c1.cy - a.c0.cy) * e, s: a.c0.s * Math.pow(a.c1.s / a.c0.s, e) };
        if (t < 1) seguir = true; else anim = null;
      }
      if (pintar(ahora)) seguir = true;
      if (seguir) raf = requestAnimationFrame(cuadro);
    }
    const pedir = () => { if (!raf) raf = requestAnimationFrame(cuadro); };
    const ya = () => { if (anim) pedir(); else if (pintar(performance.now())) pedir(); }; // sin transición pendiente se pinta en el acto
    // Lleva k y la cámara a su destino (sin animación si se pide movimiento reducido).
    function ir(k1, c1, dur) {
      if (!E.cam) E.cam = objetivo(E.k);
      if (movReducido() || !dur) { anim = null; E.k = k1; E.cam = c1; ya(); return; }
      anim = { t0: performance.now(), dur, k0: E.k, k1, c0: E.cam, c1 }; pedir();
    }
    const kVista = () => vistaTBGuardada() === 'relieve' ? 1 : 0;
    const encuadrar = dur => { libre = false; ir(E.k, objetivo(anim ? anim.k1 : E.k, null), dur); };
    function seleccionar(id, enfocar) {
      estadoTB.sel = id && N.tbPieza(TB, id) ? id : null;
      const t = raiz.querySelector('.tb-tarjeta');
      if (t) { t.innerHTML = tarjetaTB(estadoTB.sel); t.classList.toggle('con-pieza', !!estadoTB.sel); }
      raiz.querySelectorAll('.chip-tb').forEach(b => { const on = b.dataset.tbPieza === estadoTB.sel; b.classList.toggle('sel', on); b.setAttribute('aria-pressed', on); });
      try { history.replaceState(null, '', hrefTB(estadoTB.sel)); } catch (e) { /* file:// */ }
      if (enfocar && estadoTB.sel && N.tbHuella(N.tbPieza(TB, estadoTB.sel))) {
        const c = objetivo(E.k, estadoTB.sel);
        // Móvil: la tarjeta sube como hoja inferior; el plano se coloca arriba y la pieza en la parte que queda visible.
        if (t && getComputedStyle(t).position === 'fixed') {
          try { lienzo.scrollIntoView({ block: 'start', behavior: 'auto' }); } catch (e) { /* sin opciones */ }
          const lt = lienzo.getBoundingClientRect().top, hoja = t.getBoundingClientRect().top, y = Math.max(50, Math.min(H / 2, (hoja - lt) / 2));
          c.cy += (H / 2 - y) / c.s;
        }
        libre = true; ir(E.k, c, 800);
      } else ya();
    }
    function vista(v) { store.set('biblia.tbVista', v); const k1 = v === 'relieve' ? 1 : 0; const foco = libre && estadoTB.sel ? estadoTB.sel : null; ir(k1, objetivo(k1, foco), 1100); }
    function zoom(f) {
      if (!E.cam) E.cam = objetivo(E.k);
      if (!f) { encuadrar(500); return; }
      libre = true; ir(E.k, Object.assign({}, E.cam, { s: Math.min(60, Math.max(0.5, E.cam.s * (f > 0 ? 1.45 : 1 / 1.45))) }), 280);
    }
    // Montaje (Éx 40): una pieza por paso, con su cita; el ritmo depende de lo largo de la cita.
    const durPaso = m => Math.min(8000, Math.max(2600, 1500 + 48 * String(m.cita || '').length));
    function panelMontaje() {
      if (!mont.activo) { panelM.hidden = true; panelM.innerHTML = ''; return; }
      panelM.hidden = false;
      const m = M[mont.i], p = m && N.tbPieza(TB, m.pieza), red = movReducido();
      panelM.innerHTML = mont.fin
        ? `<p class="tb-m-cuenta">Montaje completo · ${M.length} pasos</p><p>${refHTML(M[M.length - 1].ref)}${M[M.length - 1].cita ? ` <q class="tb-cita">${esc(M[M.length - 1].cita)}</q>` : ''}</p>
          <div class="tb-m-botones"><button type="button" class="boton secundario mini-boton" data-tb-m="otra">${ICO_OTRA}Otra vez</button><button type="button" class="boton secundario mini-boton" data-tb-m="salir">Cerrar</button></div>`
        : `<p class="tb-m-cuenta">Paso ${mont.i + 1} de ${M.length}${p ? ` · <strong>${esc(p.nombre)}</strong>` : ''}</p>
          ${m.cita ? `<blockquote class="rc-cita">${esc(m.cita)}</blockquote>` : ''}<p class="rc-ref">${insigniaTB(m.certeza || 'texto', m.ref)}${m.certeza && m.certeza !== 'texto' ? ` <span class="nota">Identificación inferida${m.nota ? ': ' + esc(m.nota) : ''}</span>` : ''}</p>
          <div class="tb-m-barra" aria-hidden="true"><span style="width:${((mont.i + 1) / M.length * 100).toFixed(1)}%"></span></div>
          <div class="tb-m-botones">
            <button type="button" class="boton secundario mini-boton" data-tb-m="-1" aria-label="Paso anterior"${mont.i ? '' : ' disabled'}><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M12.5 4.5L7 10l5.5 5.5"/></svg></button>
            ${red ? '' : `<button type="button" class="boton secundario mini-boton" data-tb-m="pausa" aria-label="${mont.jugando ? 'Pausar' : 'Seguir'}">${mont.jugando ? ICO_PAUSA : ICO_PLAY}</button>`}
            <button type="button" class="boton secundario mini-boton" data-tb-m="1" aria-label="Paso siguiente"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M7.5 4.5L13 10l-5.5 5.5"/></svg></button>
            <button type="button" class="boton secundario mini-boton" data-tb-m="salir">Salir</button></div>
          ${red ? '<p class="meta">Movimiento reducido: avanza con «siguiente».</p>' : ''}`;
    }
    function paso(i) {
      clearTimeout(mont.timer);
      if (i >= M.length) { mont.fin = true; mont.jugando = false; panelMontaje(); encuadrar(1200); return; }
      mont.i = Math.max(0, i); mont.fin = false;
      const m = M[mont.i];
      if (!movReducido() && !N.tbColocadas(TB, mont.i).includes(m.pieza)) E.ap.set(m.pieza, performance.now());
      if (window.matchMedia && window.matchMedia('(min-width: 900px)').matches) { estadoTB.sel = null; seleccionar(m.pieza, false); }
      panelMontaje();
      const c = objetivo(E.k, N.tbHuella(N.tbPieza(TB, m.pieza)) ? m.pieza : null), hp = panelM.hidden ? 0 : panelM.offsetHeight;
      if (hp && hp < H * 0.6) c.cy += (hp / 2 + 6) / c.s; // la cita tapa la parte de abajo: la pieza queda encima
      libre = true; ir(E.k, c, 900);
      if (mont.jugando && !movReducido()) mont.timer = setTimeout(() => paso(mont.i + 1), durPaso(m));
    }
    function armar() { try { lienzo.scrollIntoView({ block: 'center', behavior: movReducido() ? 'auto' : 'smooth' }); } catch (e) { /* sin opciones */ } mont.activo = true; mont.fin = false; mont.jugando = !movReducido(); E.ap.clear(); paso(0); }
    function salir() { clearTimeout(mont.timer); mont.activo = false; mont.jugando = false; mont.fin = false; panelMontaje(); encuadrar(700); }
    function accionMontaje(a) {
      if (a === 'salir') salir();
      else if (a === 'otra') armar();
      else if (a === 'pausa') { mont.jugando = !mont.jugando; if (mont.jugando) paso(mont.i + 1); else { clearTimeout(mont.timer); panelMontaje(); } }
      else { mont.jugando = false; paso(mont.i + +a); }
    }
    // Arrastre para mover la cámara (ratón, lápiz o dedo).
    let arr = null;
    svg.addEventListener('pointerdown', e => { if (e.button !== 0 || e.target.closest('[data-tb-pieza]')) return; arr = { x: e.clientX, y: e.clientY, c: Object.assign({}, E.cam), mov: false }; try { svg.setPointerCapture(e.pointerId); } catch (x) { /* sin captura */ } });
    svg.addEventListener('pointermove', e => {
      if (!arr) return; const dx = e.clientX - arr.x, dy = e.clientY - arr.y;
      if (!arr.mov && Math.hypot(dx, dy) < 4) return;
      arr.mov = true; libre = true; anim = null; E.cam = { cx: arr.c.cx - dx / arr.c.s, cy: arr.c.cy - dy / arr.c.s, s: arr.c.s }; ya();
    });
    const soltarTB = () => { arr = null; };
    svg.addEventListener('pointerup', soltarTB); svg.addEventListener('pointercancel', soltarTB);
    svg.addEventListener('keydown', e => { const g = e.target.closest && e.target.closest('[data-tb-pieza]'); if (g && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); seleccionar(g.dataset.tbPieza, true); } });
    if (window.ResizeObserver) new ResizeObserver(() => { const w = W, h = H; medir(); if (w !== W || h !== H) { if (!libre) E.cam = objetivo(E.k, null); ya(); } }).observe(lienzo);
    medir();
    E.cam = estadoTB.sel ? objetivo(E.k, estadoTB.sel) : objetivo(E.k);
    if (estadoTB.sel) libre = true;
    pintar(performance.now());
    return { seleccionar, vista, zoom, armar, accionMontaje, repintar: () => { if (!libre) E.cam = objetivo(E.k); ya(); }, raiz, estaMontando: () => mont.activo };
  }
  function montarTB(raiz) {
    raiz.querySelectorAll('.tb[data-tb]:not([data-montado])').forEach(el => { try { TBM = crearTabernaculo(el); } catch (e) { const l = el.querySelector('.tb-lienzo'); if (l) l.textContent = 'No se pudo dibujar el tabernáculo.'; console.error(e); } });
  }
  const tbVivo = () => TBM && TBM.raiz.isConnected ? TBM : null;
  document.addEventListener('click', e => {
    const t = e.target; if (!t.closest) return;
    const m = tbVivo(); if (!m) return;
    const pz = t.closest('[data-tb-pieza]'); if (pz && m.raiz.contains(pz)) { m.seleccionar(pz.dataset.tbPieza, true); const c = m.raiz.querySelector('.tb-tarjeta'); if (c && window.matchMedia && window.matchMedia('(min-width: 900px)').matches) c.scrollTop = 0; return; }
    if (t.closest('[data-tb-cerrar]')) { m.seleccionar(null, false); return; }
    const vc = t.closest('[data-tb-calc]'); if (vc) { const d = document.getElementById('tb-calc-' + vc.dataset.tbCalc); if (d) { d.open = true; d.scrollIntoView({ block: 'start', behavior: movReducido() ? 'auto' : 'smooth' }); const sm = d.querySelector('summary'); if (sm) sm.focus({ preventScroll: true }); } return; }
    const z = t.closest('[data-tb-z]'); if (z) { m.zoom(+z.dataset.tbZ); return; }
    if (t.closest('[data-tb-armar]')) { m.armar(); return; }
    const mm = t.closest('[data-tb-m]'); if (mm) { m.accionMontaje(mm.dataset.tbM); }
  });
  document.addEventListener('change', e => {
    const t = e.target, m = tbVivo(); if (!m || !m.raiz.contains(t)) return;
    if (t.name === 'tb-vista') m.vista(t.value);
    else if (t.name === 'tb-codo') {
      store.set('biblia.codo', t.value);
      const c = m.raiz.querySelector('.tb-tarjeta'); if (c) c.innerHTML = tarjetaTB(estadoTB.sel);
      const f = m.raiz.querySelector('.tb-codo-fuente'), codo = codoTB(); if (f && codo) f.innerHTML = codoNotaHTML(codo);
      m.repintar();
    }
    else if (t.name === 'tb-modo') { estadoTB.modo = 'leido'; const l = m.raiz.querySelector('.tb-leido'); if (l) l.innerHTML = leidoTBHTML(); m.repintar(); }
    else if (t.dataset.tbCapa) { const cs = capasTB(); if (t.checked) cs.add(t.dataset.tbCapa); else cs.delete(t.dataset.tbCapa); store.set('biblia.tbCapas', [...cs]); m.repintar(); }
    else if (t.id === 'tb-humana') { store.set('biblia.tbHumana', t.checked); m.repintar(); }
  });
  // Leer (plan de Éxodo): acceso a la vista.
  const entradaTBHTML = () => TB && N.tbPiezas(TB).length ? `<a class="tb-entrada" href="#tabernaculo">${ICO_TB}<span><strong>El tabernáculo, a escala</strong><span class="meta">Plano y relieve con las medidas de Éxodo 25–40 y su montaje según Éxodo 40.</span></span></a>` : '';
  // Acompañante (Éx 25–31 y 35–40): mini plano con las piezas del pasaje o del versículo.
  function tabernaculoAcompHTML(p, refs, sec, I) {
    if (!TB || !N.tbEnPasaje(p)) return '';
    const ps = estado.activo ? N.tbPiezasDeRefs(TB, refs) : N.tbPiezasDePasaje(TB, p);
    if (!ps.length) return '';
    const ids = ps.map(x => x.id), dib = ids.filter(id => N.tbHuella(N.tbPieza(TB, id)));
    return sec('En el tabernáculo', `<div class="tb-acomp">${dib.length ? `<a class="tb-mini" href="${hrefTB(dib[0])}" aria-label="Abrir el tabernáculo en ${esc(N.tbPieza(TB, dib[0]).nombre)}">${miniPlanoTB(dib)}</a>` : ''}
      <ul class="chips">${ps.map(x => `<li><a class="chip-tb" href="${hrefTB(x.id)}">${esc(x.nombre)}</a></li>`).join('')}</ul>
      ${TB.ejemplo ? '<p class="meta">EJEMPLO: datos de prueba.</p>' : ''}
      <p><a class="boton secundario" href="${hrefTB(ids[0])}">Ver ${esc(ps[0].nombre)} en el tabernáculo</a></p></div>`, I('M2.5 15.5h15M4 15.5V8.5h12v7M4 8.5l6-4 6 4M8.5 15.5v-4h3v4'));
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
  const bloqueadaHTML = (f, quien, ico) => `<li class="ficha-col bloqueada"><span class="ficha-retrato">${ico || SILUETA}</span><span class="ficha-nombre"><span aria-hidden="true">Sin descubrir</span><span class="sr">${quien} sin descubrir,</span></span><span class="ficha-pie">Aparece en ${esc(f.primeraCap).replace(' ', '&nbsp;')}</span></li>`;
  function fichaColHTML(f) {
    if (f.estado === 'bloqueado' || (!f.estado && !f.desbloqueada)) return bloqueadaHTML(f, 'Personaje');
    const curso = f.estado === 'en-curso';
    const chip = f.juego ? nivelHTML(f) : `<span class="rareza-muestra r-${f.rareza.id}">${esc(f.rareza.nombre)}</span>`;
    return `<li><button type="button" class="ficha-col r-${f.rareza.id}${f.sexo === 'f' ? ' mujer' : ''}${curso ? ' en-curso' : ''}" data-persona="${esc(f.id)}">
      <span class="ficha-retrato"><span class="ficha-inicial" aria-hidden="true">${esc(inicial(f.id))}</span></span>
      <span class="ficha-nombre">${esc(nombre(f.id))}</span>${chip}
      ${curso ? `<span class="ficha-avance"><progress max="${f.total || 1}" value="${f.leidos}" aria-label="Pasajes leídos donde aparece"></progress><span>${f.leidos}/${f.total}</span></span>
      <span class="ficha-pie">En curso · hasta ${esc(f.capitulo || '').replace(' ', '&nbsp;')}</span>` : `<span class="ficha-pie">${esc(f.primera)}</span>`}</button></li>`;
  }
  function fichaCosaHTML(f) {
    if (!f.desbloqueada) return bloqueadaHTML(f, GRUPO_TXT[f.grupo], ICO_COSA[f.grupo].replace('class="ico-cosa"', 'class="ico-cosa silueta-cosa"'));
    return `<li><button type="button" class="ficha-col cosa c-${f.grupo}" data-${datoCosa(f.grupo)}="${esc(f.id)}">
      <span class="ficha-retrato">${ICO_COSA[f.grupo]}</span><span class="ficha-nombre">${esc(f.nombre)}</span>
      ${f.tipo ? `<span class="ficha-tipo">${esc(f.tipo)}</span>` : ''}<span class="ficha-pie">${esc(f.primera)}</span></button></li>`;
  }
  const segCol = (leyenda, name, actual, ops) => `<fieldset class="segmentos"><legend>${leyenda}</legend>${ops.map(([v, t]) => `<label><input type="radio" name="${name}" value="${esc(v)}" ${actual === v ? 'checked' : ''}><span>${esc(t)}</span></label>`).join('')}</fieldset>`;
  // Colección: personajes y, con el catálogo de juego, objetos y escenarios.
  function vistaPersonajes() {
    const JJ = JUEGO(), Ls = [...pasajesLeidos()];
    const F = N.fichasColeccion(D, Ls, JJ);
    const G = { personajes: F };
    if (JJ) N.GRUPOS_JUEGO.forEach(g => { G[g] = N.fichasCosas(D, JJ, g, Ls); });
    const grupo = G[estado.colGrupo] ? estado.colGrupo : 'personajes';
    const fe = estado.colEstado === 'obtenidos' || (estado.colEstado === 'en-curso' && grupo === 'personajes') ? estado.colEstado : '';
    const pasaFE = f => !fe || (fe === 'obtenidos' ? f.desbloqueada : f.estado === 'en-curso');
    const NOM_G = { personajes: 'Personajes', objetos: 'Objetos', escenarios: 'Escenarios' };
    const obtDe = xs => xs.filter(f => f.desbloqueada).length;
    const pestanas = JJ ? `<div class="colec-grupos">${segCol('Grupo', 'col-grupo', grupo, Object.keys(G).map(g => [g, `${NOM_G[g]} ${obtDe(G[g])}/${G[g].length}`]))}</div>` : '';
    const filtroEstado = JJ ? segCol('Estado', 'col-estado', fe, [['', 'Todos'], ['obtenidos', 'Obtenidos']].concat(grupo === 'personajes' ? [['en-curso', 'En curso']] : [])) : '';
    const sub = JJ ? `<p class="sub">Un personaje se desbloquea al terminar de leer el capítulo donde se cierra la primera historia en la que es protagonista; mientras tanto su ficha está «en curso». Quien solo aparece en genealogías (NPC) entra al leer su primera mención. Objetos y escenarios entran al leer el pasaje donde aparecen por primera vez.</p>`
      : `<p class="sub">Cada persona con nombre entra en tu colección cuando marcas como leído un pasaje donde aparece. Ábrela para ver su ficha.</p>`;
    const cab = `<h1 tabindex="-1">Colección</h1>${sub}${pestanas}`;
    if (grupo !== 'personajes') {
      const xs = G[grupo], obt = obtDe(xs), vis = xs.filter(pasaFE);
      return `${cab}
        <div class="colec-resumen"><p class="colec-cuenta"><strong>${obt}</strong> de ${xs.length}</p>
          <progress max="${xs.length || 1}" value="${obt}" aria-label="${NOM_G[grupo]} obtenidos"></progress></div>
        <div class="colec-filtros">${filtroEstado}</div>
        ${vis.length ? `<ul class="fichas-col">${vis.map(fichaCosaHTML).join('')}</ul>` : '<p class="vacio-txt">Aún no tienes fichas con este filtro.</p>'}`;
    }
    const obt = obtDe(F);
    const LB = N.libros(D).filter(l => F.some(f => f.libros.includes(l.id)));
    const lib = LB.some(l => l.id === estado.colLibro) ? estado.colLibro : '';
    const sx = estado.colSexo === 'f' || estado.colSexo === 'm' ? estado.colSexo : '';
    const enLibro = F.filter(f => !lib || f.libros.includes(lib)), obtL = obtDe(enLibro);
    const conocida = f => f.desbloqueada || f.estado === 'en-curso';
    const vis = enLibro.filter(f => (!sx || (conocida(f) && f.sexo === sx)) && pasaFE(f));
    const sinDesc = sx && !fe ? enLibro.filter(f => !conocida(f)).length : 0;
    const enCurso = F.filter(f => f.estado === 'en-curso').length;
    const nomLib = lib ? (LB.find(l => l.id === lib) || {}).nombre : '';
    return `${cab}
      <div class="colec-resumen"><p class="colec-cuenta"><strong>${obt}</strong> de ${F.length}</p>
        <progress max="${F.length || 1}" value="${obt}" aria-label="Personajes obtenidos"></progress>
        ${JJ && enCurso ? `<p class="meta">${enCurso} en curso</p>` : ''}
        ${lib ? `<p class="meta">En ${esc(nomLib)}: ${obtL} de ${enLibro.length}</p>` : ''}</div>
      <div class="colec-filtros">${LB.length > 1 ? segCol('Libro', 'col-libro', lib, [['', 'Todos']].concat(LB.map(l => [l.id, l.nombre]))) : ''}
        ${segCol('Mostrar', 'col-sexo', sx, [['', 'Todos'], ['f', 'Mujeres'], ['m', 'Hombres']])}${filtroEstado}</div>
      ${JJ ? `<details class="plegable"><summary>Qué significa el nivel</summary>
        <p class="meta">${insignia('calculo')} Nivel provisional del catálogo: 1 + log₂ de los versículos donde el personaje está presente (tope 12). Mide cuánto texto hay sobre él, no su importancia; se recalcula con cada libro. NPC: solo aparece en genealogías.</p></details>` : ''}
      <details class="plegable"><summary>Qué significa la rareza</summary>
        <p class="meta">Sale solo de los datos: en cuántos versículos de ${esc(N.alcance(D).texto)} aparece la persona. No mide su importancia.</p>
        <ul class="rarezas">${N.RAREZAS.map(r => `<li><span class="rareza-muestra r-${r.id}">${esc(r.nombre)}</span> ${rangoRareza(r)} <span class="meta">· ${F.filter(f => f.rareza.id === r.id).length} personas</span></li>`).join('')}</ul></details>
      ${obt || enCurso ? '' : `<p class="colec-vacia">Todavía no tienes fichas. <a href="#leer">Empieza a leer</a> y marca un pasaje como leído.</p>`}
      ${sx && sinDesc ? `<p class="meta">Las ${sinDesc} fichas sin descubrir no se filtran por mujeres u hombres, para no adelantar nada.</p>` : ''}
      ${vis.length ? `<ul class="fichas-col">${vis.map(fichaColHTML).join('')}</ul>` : '<p class="vacio-txt">Aún no tienes fichas con este filtro.</p>'}`;
  }
  // Aviso «Nuevo en tu colección» tras marcar un pasaje como leído. Muchas fichas: se resumen.
  let tNuevas = 0;
  const ocultarNuevas = () => { clearTimeout(tNuevas); const el = $('#nuevas'); if (el) { el.hidden = true; el.classList.remove('entra'); } };
  const programarNuevas = () => { clearTimeout(tNuevas); tNuevas = setTimeout(ocultarNuevas, 9000); };
  // nv: lista de personas, o { personas, objetos, escenarios } (con el catálogo de juego).
  function mostrarNuevas(nv) {
    const el = $('#nuevas'); if (!el || !nv) return;
    const JJ = JUEGO(), Ls = [...pasajesLeidos()];
    const items = (Array.isArray(nv) ? nv : nv.personas || []).map(id => ['persona', id])
      .concat(Array.isArray(nv) ? [] : [].concat(...N.GRUPOS_JUEGO.map(g => (nv[g] || []).map(id => [g, id]))));
    if (!items.length) return;
    const gs = JJ ? N.GRUPOS_JUEGO.map(g => N.fichasCosas(D, JJ, g, Ls)) : [];
    const total = N.coleccionables(D).length + gs.reduce((n, xs) => n + xs.length, 0);
    const obt = N.coleccion(D, Ls, JJ).size + gs.reduce((n, xs) => n + xs.filter(x => x.desbloqueada).length, 0);
    const soloP = items.every(x => x[0] === 'persona');
    const vis = items.length > 4 ? items.slice(0, 3) : items, resto = items.length - vis.length;
    const liP = (id, i) => { const r = N.rareza(D, id), e = JJ && JJ.personajes[id] ? N.estadoPersonaje(D, JJ, id, Ls) : null;
      return `<li style="--i:${i}"><button type="button" class="nueva-ficha r-${r.id}" data-persona="${esc(id)}"><span class="ficha-inicial" aria-hidden="true">${esc(inicial(id))}</span><span class="nueva-nombre">${esc(nombre(id))}</span>${e ? nivelHTML(e) : `<span class="rareza-muestra r-${r.id}">${esc(r.nombre)}</span>`}</button></li>`; };
    const liC = (g, id, i) => `<li style="--i:${i}"><button type="button" class="nueva-ficha cosa c-${g}" data-${datoCosa(g)}="${esc(id)}"><span class="ficha-inicial" aria-hidden="true">${ICO_COSA[g]}</span><span class="nueva-nombre">${esc(((JJ || {})[g] || {})[id] ? JJ[g][id].nombre || id : id)}</span><span class="rareza-muestra">${GRUPO_TXT[g]}</span></button></li>`;
    const n = items.length, cuenta = soloP ? (n === 1 ? '1 personaje' : n + ' personajes') : (n === 1 ? '1 ficha' : n + ' fichas');
    el.innerHTML = `<div class="nuevas-cab"><p class="nuevas-titulo">Nuevo en tu colección<span class="nuevas-cuenta">${cuenta} · llevas ${obt} de ${total}</span></p>
        <button type="button" class="cerrar" data-cerrar-nuevas aria-label="Cerrar aviso"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 5l10 10M15 5L5 15"/></svg></button></div>
      <ul class="nuevas-fichas">${vis.map(([g, id], i) => g === 'persona' ? liP(id, i) : liC(g, id, i)).join('')}
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

  /* ---------- Perfiles: botón de la cabecera, selector, edición y PIN de adulto ---------- */
  const perfilesDlg = $('#perfiles'), pinDlg = $('#pin');
  const TIPO_PERFIL_TXT = { adulto: 'Adulto', nino: 'Niño' };
  const COLOR_TXT = { lapis: 'Azul', verdin: 'Verde', ocre: 'Ocre', murice: 'Morado', carmin: 'Rojo', mar: 'Turquesa' };
  const AVISO_PIN = 'Es un control parental sencillo: evita cambios por descuido, pero no es seguridad real. Todo se guarda solo en este navegador.';
  const OLVIDE_PIN = `<details class="plegable"><summary>Olvidé el PIN</summary><p class="meta">El PIN no se puede recuperar: solo se guarda una huella cifrada (SHA-256). Para restablecerlo hay que borrar los datos de este sitio en el navegador (Configuración › Privacidad › Cookies y datos de sitios › este sitio › Borrar). <strong>Se borran también los perfiles y el progreso de todos.</strong> Al volver a abrir la app empiezas de cero.</p></details>`;
  const avatarHTML = (p, cls) => `<span class="avatar av-${esc(p.color)}${cls ? ' ' + cls : ''}" aria-hidden="true">${esc(p.inicial)}</span>`;
  function pintarBotonPerfil() {
    const b = $('#perfil-btn'), p = perfil(); if (!b) return;
    b.innerHTML = `${avatarHTML(p)}<span class="perfil-txt"><span class="perfil-nombre">${esc(p.nombre)}</span><span class="perfil-tipo">${TIPO_PERFIL_TXT[p.tipo]}</span></span>`;
    b.setAttribute('aria-label', `Perfil: ${p.nombre}, ${TIPO_PERFIL_TXT[p.tipo].toLowerCase()}. Cambiar de perfil`);
    document.documentElement.classList.toggle('perfil-nino', p.tipo === 'nino');
  }
  async function hashPin(pin) {
    const txt = 'biblia-pin|' + pin;
    try {
      const b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(txt));
      return 'sha256:' + Array.from(new Uint8Array(b), x => x.toString(16).padStart(2, '0')).join('');
    } catch (e) { // sin SubtleCrypto (página sin https): huella simple, igual de «no segura»
      let h = 2166136261; for (const c of txt) { h ^= c.codePointAt(0); h = Math.imul(h, 16777619) >>> 0; } return 'fnv:' + h.toString(16);
    }
  }
  // Pide (o define, con opc.definir) el PIN de adulto. Resuelve true si es correcto; sin PIN definido no pide nada.
  let pinResolver = null;
  function pedirPin(opc) {
    const o = opc || {};
    if (!o.definir && !PERF.r.pin) return Promise.resolve(true);
    if (!pinDlg) return Promise.resolve(false);
    if (pinResolver) pinResolver(false);
    pinDlg.innerHTML = `<div class="dialogo-cab"><h2 id="pin-titulo">${esc(o.titulo || (o.definir ? 'Define el PIN de adulto' : 'PIN de adulto'))}</h2><button type="button" class="cerrar" data-cerrar aria-label="Cancelar"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 5l10 10M15 5L5 15"/></svg></button></div>
      <form class="dialogo-cuerpo pin-form" id="pin-form" novalidate>
        <p>${esc(o.texto || (o.definir ? 'Elige 4 cifras. Se pedirán para pasar a un perfil de adulto, crear, editar o borrar perfiles y mostrar lo plegado.' : 'Escribe las 4 cifras del PIN.'))}</p>
        <label class="campo">PIN de 4 cifras<input id="pin-1" autofocus type="password" inputmode="numeric" pattern="[0-9]{4}" maxlength="4" autocomplete="${o.definir ? 'new-password' : 'off'}" required></label>
        ${o.definir ? '<label class="campo">Repite el PIN<input id="pin-2" type="password" inputmode="numeric" pattern="[0-9]{4}" maxlength="4" autocomplete="new-password" required></label>' : ''}
        <p class="form-error" id="pin-error" role="alert"></p>
        <div class="form-acc"><button type="submit" class="boton">${o.definir ? 'Guardar el PIN' : 'Aceptar'}</button><button type="button" class="boton secundario" data-cerrar>Cancelar</button></div>
        <p class="meta">${AVISO_PIN}</p>${o.definir ? '' : OLVIDE_PIN}</form>`;
    return new Promise(res => {
      pinResolver = v => { pinResolver = null; res(v); };
      pinDlg.onclose = () => { if (pinResolver) pinResolver(false); };
      const f = pinDlg.querySelector('#pin-form'), err = pinDlg.querySelector('#pin-error');
      let ocupado = false;
      f.onsubmit = async ev => {
        ev.preventDefault();
        if (ocupado || !pinResolver) return; // doble envío o pedido ya resuelto
        ocupado = true;
        try { await enviar(); } finally { ocupado = false; }
      };
      const enviar = async () => {
        const a = f.querySelector('#pin-1').value.trim(), b2 = f.querySelector('#pin-2');
        if (!N.pinValido(a)) { err.textContent = 'El PIN son 4 cifras.'; return; }
        if (o.definir) {
          if (b2.value.trim() !== a) { err.textContent = 'Los dos PIN no coinciden.'; return; }
          PERF.r.pin = await hashPin(a); guardarPerfiles();
        } else if (await hashPin(a) !== PERF.r.pin) { err.textContent = 'PIN incorrecto.'; f.querySelector('#pin-1').select(); return; }
        const r = pinResolver; pinResolver = null;
        if (!r) return; // se canceló mientras se calculaba la huella
        if (o.enlace) { // el enlace se abre con un toque de la persona (los navegadores bloquean ventanas abiertas por código)
          let dom = ''; try { dom = new URL(o.enlace).hostname; } catch (e) { /* nada */ }
          f.innerHTML = `<p>Enlace externo${dom ? ` a <strong>${esc(dom)}</strong>` : ''}:</p><p><a class="boton" data-libre href="${esc(o.enlace)}" target="_blank" rel="noopener noreferrer">Abrir el enlace</a> <span class="etiqueta externa">Fuente externa</span></p><div class="form-acc"><button type="button" class="boton secundario" data-cerrar>Cerrar</button></div>`;
          r(true); return;
        }
        cerrar(pinDlg); r(true);
      };
      mostrar(pinDlg);
      setTimeout(() => { const i = pinDlg.querySelector('#pin-1'); if (i) i.focus(); }, 30);
    });
  }
  const modoPerfiles = { modo: 'lista', id: null };
  function perfilesListaHTML() {
    const act = perfil(), C = CONT();
    return `<p class="meta">Quién lee ahora. Cada perfil guarda en este dispositivo su propio progreso, colección y preferencias.</p>
      <ul class="perfiles-lista">${PERF.r.lista.map(p => `<li class="perfil-fila${p.id === act.id ? ' actual' : ''}">
        <button type="button" class="perfil-elegir" data-perfil-elegir="${esc(p.id)}"${p.id === act.id ? ' aria-current="true"' : ''}>${avatarHTML(p)}<span class="perfil-fila-txt"><strong>${esc(p.nombre)}</strong><span class="meta">${TIPO_PERFIL_TXT[p.tipo]}${p.id === act.id ? ' · leyendo ahora' : ''}${N.cambioPidePin(PERF.r, act.id, p.id) ? ' · pide PIN' : ''}</span></span></button>
        <button type="button" class="boton mini-boton secundario" data-perfil-editar="${esc(p.id)}" aria-label="Editar el perfil ${esc(p.nombre)}">Editar</button></li>`).join('')}</ul>
      <p><button type="button" class="boton secundario" data-perfil-nuevo>Añadir perfil</button></p>
      ${act.tipo === 'adulto' ? `<label class="chk"><input type="checkbox" id="perfil-avisar"${act.avisar ? ' checked' : ''}><span>Avisar antes de contenido fuerte</span></label>
        <p class="meta">En este perfil se ve todo. Con esta opción aparece un aviso antes de los pasajes marcados, sin plegarlos.</p>` : ''}
      <section class="perfil-sec"><h3>Perfil de niño</h3>
        <p class="meta">Pliega los pasajes marcados como fuertes («Esta parte es para leerla con un adulto»), anota los delicados, oculta imágenes cruentas y pide el PIN para abrir enlaces externos. Los videos de Proyecto Biblia siguen disponibles.</p>
        ${C && C.criterio ? `<details class="plegable"><summary>Qué se marca y con qué criterio</summary><p class="meta">${esc(C.criterio)}</p><p class="meta">${ROTULO_CONT}</p></details>` : `<p class="meta">${ROTULO_CONT}</p>`}</section>
      <section class="perfil-sec"><h3>PIN de adulto</h3>
        <p class="meta">${PERF.r.pin ? 'Definido.' : 'Sin definir: se pide al crear el primer perfil de niño.'} ${AVISO_PIN}</p>
        <button type="button" class="boton mini-boton secundario" data-pin-cambiar>${PERF.r.pin ? 'Cambiar el PIN' : 'Definir un PIN'}</button>${PERF.r.pin ? OLVIDE_PIN : ''}</section>`;
  }
  function perfilFormHTML(p, bienvenida) {
    const x = p || { nombre: '', tipo: 'adulto', color: N.COLORES_PERFIL[PERF.r.lista.length % N.COLORES_PERFIL.length], inicial: '' };
    const borrar = p && !bienvenida && PERF.r.lista.length > 1 && p.id !== PERF.r.activo;
    return `${bienvenida ? '<p>Crea el perfil de quien va a leer. Si ya habías leído aquí, tu progreso pasa a este primer perfil. Después puedes añadir más (por ejemplo, uno de niño) desde el botón de perfil.</p>' : ''}
      <form class="perfil-form" id="perfil-form" novalidate>
        <label class="campo">Nombre<input name="nombre" maxlength="24" required value="${esc(x.nombre)}" autocomplete="off"></label>
        <fieldset class="segmentos"><legend>Tipo de perfil</legend>${['adulto', 'nino'].map(t => `<label><input type="radio" name="tipo" value="${t}"${x.tipo === t ? ' checked' : ''}><span>${TIPO_PERFIL_TXT[t]}</span></label>`).join('')}</fieldset>
        <p class="meta">Niño: lectura filtrada y apta para niños. Adulto: se muestra todo el texto y todos los recursos.</p>
        <fieldset class="colores"><legend>Color</legend>${N.COLORES_PERFIL.map(c => `<label class="color-op"><input type="radio" name="color" value="${c}"${x.color === c ? ' checked' : ''}><span class="avatar av-${c}" aria-hidden="true">${esc(x.inicial || '?')}</span><span class="sr">${COLOR_TXT[c]}</span></label>`).join('')}</fieldset>
        <label class="campo campo-corto">Inicial<input name="inicial" maxlength="2" value="${esc(x.inicial || '')}" autocomplete="off" placeholder="Auto"></label>
        <p class="form-error" id="perfil-error" role="alert"></p>
        <div class="form-acc"><button type="submit" class="boton">${bienvenida ? 'Empezar a leer' : 'Guardar'}</button>
          ${bienvenida ? '' : '<button type="button" class="boton secundario" data-perfil-volver>Volver</button>'}
          ${borrar ? `<button type="button" class="boton secundario peligro" data-perfil-borrar="${esc(p.id)}">Borrar perfil</button>` : ''}</div></form>`;
  }
  function pintarPerfiles() {
    if (!perfilesDlg) return;
    const { modo, id } = modoPerfiles, p = id ? N.perfilDe(PERF.r, id) : null;
    perfilesDlg.querySelector('#perfiles-titulo').textContent = modo === 'bienvenida' ? '¿Quién va a leer?' : modo === 'editar' ? (p ? `Editar: ${p.nombre}` : 'Nuevo perfil') : 'Perfiles';
    perfilesDlg.querySelector('.dialogo-cuerpo').innerHTML = modo === 'lista' ? perfilesListaHTML() : perfilFormHTML(p, modo === 'bienvenida');
  }
  function abrirPerfiles(modo, id) { modoPerfiles.modo = modo || 'lista'; modoPerfiles.id = id || null; pintarPerfiles(); mostrar(perfilesDlg); }
  async function elegirPerfil(id) {
    if (id === PERF.r.activo) { cerrar(perfilesDlg); return; }
    const p = N.perfilDe(PERF.r, id); if (!p) return;
    if (N.cambioPidePin(PERF.r, PERF.r.activo, id) && !(await pedirPin({ titulo: `Pasar a ${p.nombre}`, texto: 'Es un perfil de adulto: escribe el PIN.' }))) return;
    PERF.r.activo = id; guardarPerfiles(); parar();
    location.reload(); // cada perfil arranca con sus propias preferencias
  }
  async function editarPerfil(id) { if (await pedirPin({ titulo: id ? 'Editar perfil' : 'Añadir perfil', texto: 'Para crear, editar o borrar perfiles hace falta el PIN de adulto.' })) abrirPerfiles('editar', id); }
  async function guardarPerfil(form) {
    const err = form.querySelector('#perfil-error'), fd = new FormData(form);
    const datos = { nombre: String(fd.get('nombre') || '').trim(), tipo: fd.get('tipo'), color: fd.get('color'), inicial: String(fd.get('inicial') || '').trim() };
    if (!datos.nombre) { err.textContent = 'Escribe un nombre.'; form.querySelector('[name="nombre"]').focus(); return; }
    if (datos.tipo === 'nino' && !PERF.r.pin && !(await pedirPin({ definir: true, texto: 'Un perfil de niño necesita un PIN de adulto: elige 4 cifras. Se pedirán para pasar a un perfil de adulto, gestionar perfiles, mostrar lo plegado o abrir enlaces externos.' }))) {
      err.textContent = 'Sin PIN no se puede crear un perfil de niño.'; return;
    }
    const previo = modoPerfiles.id ? N.perfilDe(PERF.r, modoPerfiles.id) : null;
    const nuevo = N.nuevoPerfil(previo ? PERF.r.lista.filter(x => x.id !== previo.id) : PERF.r.lista, Object.assign({ avisar: previo ? previo.avisar : false }, datos));
    if (previo) Object.assign(previo, nuevo, { id: previo.id }); else PERF.r.lista.push(nuevo);
    guardarPerfiles(); pintarBotonPerfil();
    if (modoPerfiles.modo === 'bienvenida' || (previo && previo.id === PERF.r.activo)) { cerrar(perfilesDlg); rerender(); return; }
    abrirPerfiles('lista');
  }
  function borrarPerfil(id) {
    const p = N.perfilDe(PERF.r, id); if (!p || id === PERF.r.activo || PERF.r.lista.length < 2) return;
    if (!confirm(`¿Borrar el perfil «${p.nombre}»? Se borran para siempre su progreso, su colección y sus preferencias en este dispositivo.`)) return;
    N.clavesDePerfil(LS.claves(), id).forEach(LS.del);
    PERF.r.lista = PERF.r.lista.filter(x => x.id !== id); guardarPerfiles();
    abrirPerfiles('lista');
  }
  async function cambiarPin() {
    if (PERF.r.pin && !(await pedirPin({ titulo: 'Cambiar el PIN', texto: 'Primero, el PIN actual.' }))) return;
    if (await pedirPin({ definir: true })) pintarPerfiles();
  }
  // Perfil niño: los enlaces externos (salvo Proyecto Biblia) piden el PIN antes de abrirse.
  document.addEventListener('click', e => {
    const a = e.target.closest && e.target.closest('a[href]');
    if (!a || !esNinoActivo() || a.hasAttribute('data-libre')) return;
    let u; try { u = new URL(a.href, location.href); } catch (er) { return; }
    if (!/^https?:$/.test(u.protocol) || u.origin === location.origin || N.enlaceLibre(u.href)) return;
    e.preventDefault(); e.stopPropagation();
    pedirPin({ titulo: 'Enlace externo', texto: 'Este enlace sale de la app. Un adulto puede abrirlo con su PIN.', enlace: u.href });
  }, true);
  document.addEventListener('click', e => {
    const t = e.target; if (!t.closest) return;
    if (t.closest('#perfil-btn')) { abrirPerfiles('lista'); return; }
    const el = t.closest('[data-perfil-elegir]'); if (el) { elegirPerfil(el.dataset.perfilElegir); return; }
    const ed = t.closest('[data-perfil-editar]'); if (ed) { editarPerfil(ed.dataset.perfilEditar); return; }
    if (t.closest('[data-perfil-nuevo]')) { editarPerfil(null); return; }
    if (t.closest('[data-perfil-volver]')) { abrirPerfiles('lista'); return; }
    const bo = t.closest('[data-perfil-borrar]'); if (bo) { borrarPerfil(bo.dataset.perfilBorrar); return; }
    if (t.closest('[data-pin-cambiar]')) { cambiarPin(); return; }
    const mc = t.closest('[data-mostrar-cont]'); if (mc) {
      const desde = mc.dataset.mostrarCont;
      pedirPin({ titulo: 'Mostrar esta parte', texto: 'Esta parte es para leerla con un adulto. Escribe el PIN para mostrarla.' }).then(ok => { if (ok) { desplegados.add(desde); rerender(); } });
      return;
    }
    const pc = t.closest('[data-plegar-cont]'); if (pc) { desplegados.delete(pc.dataset.plegarCont); rerender(); }
  });
  document.addEventListener('submit', e => { if (e.target.id === 'perfil-form') { e.preventDefault(); guardarPerfil(e.target); } });
  document.addEventListener('change', e => {
    if (e.target.id === 'perfil-avisar') { const p = perfil(); p.avisar = e.target.checked; guardarPerfiles(); rerender(); }
  });
  document.addEventListener('input', e => { // la inicial de las muestras de color sigue al nombre
    const f = e.target.closest && e.target.closest('#perfil-form'); if (!f || (e.target.name !== 'nombre' && e.target.name !== 'inicial')) return;
    const ini = N.inicialDe(f.querySelector('[name="inicial"]').value.trim() || f.querySelector('[name="nombre"]').value);
    f.querySelectorAll('.color-op .avatar').forEach(s => { s.textContent = ini; });
  });
  window.addEventListener('storage', e => { if (e.key === N.CLAVE_PERFILES) location.reload(); }); // otra pestaña cambió de perfil

  /* ---------- Navegación ---------- */
  function ruta() { const h = decodeURIComponent(location.hash.slice(1)) || 'leer'; const [vista, ...args] = h.split('/'); return { vista, args }; }
  const VISTAS = { leer: vistaLeer, personajes: vistaPersonajes, arbol: vistaArbol, tiempo: vistaTiempo, edades: () => vistaTiempo(['tabla']), mapa: vistaMapa, fuentes: vistaFuentes, tabernaculo: vistaTabernaculo, notas: vistaNotas };
  const PESTANA = { edades: 'tiempo', tabernaculo: 'leer' }; // rutas antiguas
  let primera = true;
  function render(foco) {
    if (!D) { main.innerHTML = '<h1>Sin datos</h1><p>No se encontró <code>datos/biblia.js</code>. Añade <code>?ejemplo</code> a la dirección para ver los datos de prueba.</p>'; return; }
    tickLectura(); // cuenta el tiempo del pasaje que se deja antes de pintar el siguiente
    const { vista, args } = ruta();
    const fn = VISTAS[vista] || vistaLeer;
    main.innerHTML = fn(args);
    trasPintar(vista);
    montarMapas(main);
    conectoresTodos();
    document.querySelectorAll('.nav-principal a').forEach(a => { if (a.dataset.vista === (VISTAS[vista] ? PESTANA[vista] || vista : 'leer')) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); });
    document.title = (main.querySelector('h1') || {}).textContent + ' · Biblia';
    const marcado = main.querySelector('.vers.activo, .fila.foco, .ga-fam.foco, .foco-sp, .tl-ev.foco');
    if (marcado && foco !== false) {
      marcado.scrollIntoView({ block: 'center', inline: 'center' });
      const nb = main.querySelector('.nb-barra'); if (nb) requestAnimationFrame(() => nb.scrollIntoView({ block: 'nearest' })); // que la barra no quede bajo el acompañante
    }
    else {
      if (foco !== false || primera) centrarLienzos();
      if (foco !== false && !primera) window.scrollTo(0, 0);
    }
    if (foco !== false && !primera) { const h = main.querySelector('h1'); if (h) h.focus({ preventScroll: true }); }
    primera = false;
  }
  // Carga bajo demanda lo que pide la vista recién pintada (Fuentes, o la comparación si quedó elegida).
  function trasPintar(vista) {
    ponerBarraNotas();
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
  window.addEventListener('hashchange', () => { estado.avisoBloq = null; parar(); cerrar(detDlg); cerrar(fichaDlg); if (visorDlg) cerrar(visorDlg); estado.focoHash = undefined; render(); });
  // Secciones del plan: se recuerda en la sesión cuáles abrió o cerró la persona.
  document.addEventListener('toggle', e => {
    const s = e.target; if (!s || !s.dataset) return;
    if (s.dataset.sec) estado.secAbiertas.set(s.dataset.sec, s.open);
    if (s.id === 'sin-parentesco') estado.sinParAbierta = s.open;
    if (s.id === 'supuestos') estado.supAbiertos = s.open;
    if (s.dataset.manuscrito !== undefined) { estado.msAbierto = s.open; if (s.open) abrirManuscrito(); }
  }, true);
  document.addEventListener('keydown', e => {
    if (e.target && e.target.id === 'buscar' && e.key === 'Enter') { const r = N.buscarAccesible(D, ACC(), estado.q, 1)[0]; if (r) { e.preventDefault(); irArbol(r.id); } }
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
    if (t.closest('[data-cargar-origen]')) { cargarOriginales('o'); cargarManuscritos(); return; }
    if (t.closest('[data-ms-reintentar]')) { cargarManuscritos(); pintarManuscrito(); return; }
    const rt = t.closest('[data-reintentar]'); if (rt) { cargarOriginales(rt.dataset.reintentar); return; }
    const vc = t.closest('[data-video-cargar]'); if (vc) { estado.videoPedido = vc.dataset.videoCargar; cargarOriginales('o'); return; }
    const vd = t.closest('[data-video]'); if (vd) { const v = ORIG.o && N.videosDeLibro(ORIG.o, estado.libro).find(x => x.youtube_id === vd.dataset.video); if (v) { estado.videoPedido = estado.libro; vd.outerHTML = iframeVideo(v); } return; }
    const cu = t.closest('[data-curio]'); if (cu) { detalleCurio(cu.dataset.curio); return; }
    const ia = t.closest('[data-ir-arbol]'); if (ia) { irArbol(ia.dataset.irArbol); return; }
    const cs = t.closest('[data-objeto], [data-escenario]'); if (cs) { e.preventDefault(); if (cs.closest('#nuevas')) ocultarNuevas(); cerrar(detDlg); abrirCosa(cs.dataset.objeto ? 'objetos' : 'escenarios', cs.dataset.objeto || cs.dataset.escenario); return; }
    const tm = t.closest('[data-termino]'); if (tm) { e.preventDefault(); abrirTermino(tm.dataset.termino); return; }
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
      const L = pasajesLeidos(), pid = ls.dataset.leidoSeguir;
      // Solo un pasaje accesible, y con el tiempo mínimo cumplido (o ya leído).
      if (ls.disabled || !ACC().pasaje(pid) || (pid === LECT.id && !listoMarcar())) return;
      const nuevas = L.has(pid) ? null : N.nuevosAlLeer(D, JUEGO(), [...L], pid);
      L.add(pid); store.set('biblia.pasajesLeidos', [...L]);
      const t = tiemposGuardados(); if (pid in t) { delete t[pid]; store.set('biblia.tiemposLectura', t); }
      if (LECT.id === pid) LECT.leido = true;
      const ps = N.pasajes(D), i = ps.findIndex(x => x.id === pid), A = ACC(), sig = ps[i + 1] && A.pasaje(ps[i + 1].id) ? ps[i + 1] : A.frontera;
      location.hash = sig ? `#leer/p/${sig.id}` : '#leer';
      if (nuevas) mostrarNuevas(nuevas);
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
    else if (['col-libro', 'col-sexo', 'col-grupo', 'col-estado'].includes(t.name)) { estado[{ 'col-libro': 'colLibro', 'col-sexo': 'colSexo', 'col-grupo': 'colGrupo', 'col-estado': 'colEstado' }[t.name]] = t.value; rerender(`input[name="${t.name}"][value="${CSS.escape(t.value)}"]`); }
    else if (t.name === 'explicaciones') { store.set('biblia.explicaciones', !!t.checked); rerender('input[name="explicaciones"]'); }
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
    const ml = document.querySelector('.marca-libro'); if (ml && D) { ml.textContent = N.alcance(D).texto; ml.title = ml.textContent; } // alcance de los datos, no fijo
    pintarBotonPerfil();
    render(false); registrarSW();
    if (PERF.nuevo) abrirPerfiles('bienvenida', PERF.r.lista[0].id);
  }
  const arrancar0 = () => {
    if (!D && EJEMPLO) {
      const s = document.createElement('script');
      s.src = 'pruebas/datos-ejemplo.js';
      s.onload = () => { D = window.BIBLIA_DATOS || null; if (D && window.BIBLIA_EJEMPLO_EXODO) D = window.BIBLIA_EJEMPLO_EXODO(D); MAPA = window.BIBLIA_MAPA || null; iniciar(); };
      s.onerror = iniciar;
      document.head.appendChild(s);
    } else iniciar();
  };
  // Con ?ejemplo, las marcas de contenido de prueba (pruebas/contenido-ejemplo.js) sustituyen a datos/contenido.js.
  const arrancar = () => EJEMPLO ? cargarScript('pruebas/contenido-ejemplo.js').then(arrancar0, arrancar0) : arrancar0();
  // Recorridos de prueba (EJEMPLO) con ?ejemplo mientras no exista datos/recorridos.js.
  // Tabernáculo de prueba (EJEMPLO) con ?ejemplo o ?tabernaculo-ejemplo mientras no exista datos/tabernaculo.js.
  const tbEjemplo = () => (EJEMPLO || /[?&]tabernaculo-ejemplo/.test(location.search)) && !TB
    ? cargarScript('pruebas/tabernaculo-ejemplo.js').then(() => { TB = window.BIBLIA_TABERNACULO || null; }, () => {}) : Promise.resolve();
  // Catálogo de juego de prueba (EJEMPLO): con ?ejemplo si falta datos/juego.js; con ?juego-ejemplo, siempre (lo sustituye).
  const juegoEjemplo = () => /[?&]juego-ejemplo/.test(location.search) || (EJEMPLO && !N.juegoValido(JG))
    ? cargarScript('pruebas/juego-ejemplo.js').then(() => { JG = window.BIBLIA_JUEGO || null; }, () => {}) : Promise.resolve();
  if (EJEMPLO && !RC) cargarScript('pruebas/recorridos-ejemplo.js').then(() => { RC = window.BIBLIA_RECORRIDOS || null; }, () => {}).then(tbEjemplo).then(juegoEjemplo).then(arrancar);
  else tbEjemplo().then(juegoEjemplo).then(arrancar);
})();
