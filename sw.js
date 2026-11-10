/* Service worker: red primero, caché de respaldo. Cambia VERSION al publicar para que aparezca el aviso de actualización. */
const VERSION = '2026-11-10.5';
const CACHE = 'biblia-' + VERSION;
const CARCASA = ['./', 'index.html', 'app.js', 'estilos.css', 'manifest.webmanifest', 'datos/genesis.js', 'datos/mapa-base.js',
  'iconos/icono.svg', 'iconos/icono-192.png', 'iconos/icono-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(CARCASA.map(u => c.add(new Request(u, { cache: 'reload' })).catch(() => {})))));
});

self.addEventListener('message', e => { if (e.data === 'SKIP_WAITING') self.skipWaiting(); });

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k.startsWith('biblia-') && k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== self.location.origin) return;
  e.respondWith((async () => {
    try {
      const r = await fetch(req.mode === 'navigate' ? req : new Request(req, { cache: 'no-cache' }));
      if (r && r.ok && r.type === 'basic') { const c = await caches.open(CACHE); c.put(req, r.clone()); }
      return r;
    } catch (err) {
      const m = await caches.match(req, { ignoreSearch: true });
      if (m) return m;
      if (req.mode === 'navigate') { const i = await caches.match('index.html'); if (i) return i; }
      return Response.error();
    }
  })());
});
