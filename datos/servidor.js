/* Servidor del desafío y del ranking (Supabase). La clave «anon» (o «publishable») es pública por diseño: la seguridad
   está en RLS y en la función `desafio` (docs/superpowers/specs/2026-11-18-ranking-mundial-design.md).
   NUNCA pegar aquí la clave secreta (service_role o sb_secret_…): este archivo se publica. Vacío = sin servidor. */
// Proyecto Supabase «biblia-ranking» (plan gratuito). Clave publicable (sb_publishable_…): pública por diseño.
window.BIBLIA_SERVIDOR = { url: 'https://qptykqllomyoklsvikgq.supabase.co', anon: 'sb_publishable_ibhGc-JrYQ6EJku0Ecs9qA_SOPztdbV' };
// Desarrollo: http://localhost…/?servidor=local usa herramientas/servidor_local.mjs (puerto 54321).
if (/^(localhost|127\.0\.0\.1)$/.test(location.hostname) && /[?&]servidor=local(&|$)/.test(location.search)) window.BIBLIA_SERVIDOR = { url: 'http://127.0.0.1:54321', anon: 'local' };
// Seguro: una clave secreta pegada por error no se usa.
(s => {
  let rol = '';
  try { rol = JSON.parse(atob(String(s.anon).split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))).role || ''; } catch (e) { /* no es JWT */ }
  if (/^sb_secret_/.test(s.anon) || rol === 'service_role') { console.error('datos/servidor.js tiene una clave SECRETA: no se usa. Pon la clave anon/publishable.'); s.url = ''; s.anon = ''; }
})(window.BIBLIA_SERVIDOR);
