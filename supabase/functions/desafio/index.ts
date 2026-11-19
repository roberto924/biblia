// Edge Function `desafio` (Deno). Contrato: docs/superpowers/specs/2026-11-18-ranking-mundial-design.md
// POST {url}/functions/v1/desafio · cabeceras apikey + Authorization: Bearer <access_token> · cuerpo { accion, ... }
// Toda la lógica está en logica.js; aquí solo HTTP, CORS, el JWT del usuario y el almacenamiento en Postgres.
// verify_jwt = false en config.toml: el token se valida aquí con auth.getUser() (usuario vivo, no solo firma válida).
// Contrato v2 (tras la revisión de seguridad): acción `borrar`, límite de llamadas (429), hora de la base.
// v3: acción `posicion` (el ranking público es solo de adultos; lo filtra la RPC SQL).
import { createClient } from "jsr:@supabase/supabase-js@2";
import { crearServicio } from "./logica.js";

// deno-lint-ignore no-explicit-any
type Fila = Record<string, any>;

const URL_SB = Deno.env.get("SUPABASE_URL") ?? "";
// Clave secreta nueva (sb_secret_…, en SUPABASE_SECRET_KEYS); la legacy service_role solo como respaldo: deja de
// funcionar a fines de 2026 (docs: migrating-to-new-api-keys).
const CLAVE_SERVICIO = (() => {
  try {
    const k = JSON.parse(Deno.env.get("SUPABASE_SECRET_KEYS") ?? "{}")?.default;
    if (typeof k === "string" && k) return k;
  } catch { /* sin claves nuevas */ }
  return Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
})();
const db = createClient(URL_SB, CLAVE_SERVICIO, {
  auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
});

const ORIGENES = new Set(["https://roberto924.github.io"]);
const ORIGEN_LOCAL = /^http:\/\/(localhost|127\.0\.0\.1)(:\d{1,5})?$/;
const MAX_CUERPO = 16 * 1024;

function cabeceras(origen: string | null): Record<string, string> {
  const h: Record<string, string> = {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
    "Access-Control-Max-Age": "86400",
    "Cache-Control": "no-store",
    "Vary": "Origin",
  };
  if (origen && (ORIGENES.has(origen) || ORIGEN_LOCAL.test(origen))) h["Access-Control-Allow-Origin"] = origen;
  return h;
}

const unico = (e: Fila | null) => e?.code === "23505";
const falla = (e: unknown) => { throw e; };

const COLS_INTENTO =
  "id, perfil, personaje, dia, seg, total, servidas, servidas_en, respuestas, i, aciertos, ms, terminado, superado, puntos, creado";
const COLS_PREGUNTA = "id, personaje, ref, orden, cita, pregunta, opciones, correcta, nino";
const aPregunta = (q: Fila) => ({
  id: q.id, personaje: q.personaje, ref: q.ref, orden: q.orden, cita: q.cita, p: q.pregunta, o: q.opciones,
  c: q.correcta, nino: q.nino,
});

// Almacenamiento (interfaz descrita en logica.js). Las restricciones de la base hacen el trabajo atómico:
// nombre único, un intento por perfil+personaje+día, un solo superado, y el guardado con `i` esperado (dos respuestas
// a la vez: gana una). Una RPC por llamada (desafio_llamada) da el límite de llamadas y la hora de la base.
const almacen = {
  async llamada(uid: string, limite: number) {
    const { data, error } = await db.rpc("desafio_llamada", { usuario: uid, limite });
    if (error) falla(error);
    return { permitido: data?.permitido === true, ahora: Number(data?.ahora) };
  },
  async posicion(uid: string) {
    const { data, error } = await db.rpc("desafio_posicion", { usuario: uid });
    if (error) falla(error);
    return data ?? null;
  },
  async borrarCuenta(uid: string) {
    // Borra el usuario de auth; perfiles, intentos y llamadas caen en cascada (claves foráneas).
    const { error } = await db.auth.admin.deleteUser(uid);
    if (error && error.status !== 404) falla(error);
  },
  async perfil(uid: string) {
    const { data, error } = await db.from("perfiles").select("id, nombre, tipo, zona_horaria").eq("id", uid).maybeSingle();
    if (error) falla(error);
    return data && { id: data.id, nombre: data.nombre, tipo: data.tipo, zona: data.zona_horaria };
  },
  async nombresUsados(claves: string[]) {
    if (!claves.length) return [];
    const { data, error } = await db.from("perfiles").select("nombre_clave").in("nombre_clave", claves);
    if (error) falla(error);
    return (data ?? []).map((x: Fila) => x.nombre_clave);
  },
  async crearPerfil(p: Fila) {
    const { error } = await db.from("perfiles").insert({
      id: p.id, nombre: p.nombre, nombre_clave: p.nombre_clave, tipo: p.tipo, zona_horaria: p.zona,
      consentimiento_en: p.consentimiento_en,
    });
    if (unico(error)) return String(error?.message).includes("perfiles_pkey") ? "ya-registrado" : "nombre-usado";
    if (error) falla(error);
    return "ok";
  },
  async cambiarNombre(uid: string, nombre: string, nombre_clave: string) {
    const { error } = await db.from("perfiles").update({ nombre, nombre_clave }).eq("id", uid);
    if (unico(error)) return "nombre-usado";
    if (error) falla(error);
    return "ok";
  },
  async personaje(id: string) {
    const { data, error } = await db.from("personajes_desafio")
      .select("personaje, nivel, n_preguntas, hasta_orden, sin_nino").eq("personaje", id).maybeSingle();
    if (error) falla(error);
    return data && {
      id: data.personaje, nivel: data.nivel, n: data.n_preguntas, hasta: data.hasta_orden, sinNino: data.sin_nino,
    };
  },
  async preguntasDe(personaje: string) {
    const { data, error } = await db.from("preguntas").select(COLS_PREGUNTA).eq("personaje", personaje);
    if (error) falla(error);
    return (data ?? []).map(aPregunta);
  },
  async preguntasPorId(ids: string[]) {
    if (!ids.length) return [];
    const { data, error } = await db.from("preguntas").select(COLS_PREGUNTA).in("id", ids);
    if (error) falla(error);
    return (data ?? []).map(aPregunta);
  },
  async intentosDe(uid: string, personaje?: string) {
    let q = db.from("intentos").select(COLS_INTENTO).eq("perfil", uid);
    if (personaje) q = q.eq("personaje", personaje);
    const { data, error } = await q.order("creado", { ascending: true });
    if (error) falla(error);
    return data ?? [];
  },
  async crearIntento(fila: Fila) {
    const { data, error } = await db.from("intentos").insert(fila).select(COLS_INTENTO).single();
    if (unico(error)) return null;
    if (error) falla(error);
    return data;
  },
  async intento(id: string) {
    const { data, error } = await db.from("intentos").select(COLS_INTENTO).eq("id", id).maybeSingle();
    if (error) falla(error);
    return data;
  },
  async guardarIntento(id: string, iEsperado: number, cambios: Fila) {
    const { data, error } = await db.from("intentos").update(cambios).eq("id", id).eq("i", iEsperado).select("id");
    if (unico(error)) return "superado"; // índice intentos_un_superado: otro intento ya superó este personaje
    if (error) falla(error);
    return (data ?? []).length === 1 ? "ok" : "conflicto";
  },
};

const servicio = crearServicio({ almacen });

Deno.serve(async (req: Request) => {
  const h = cabeceras(req.headers.get("Origin"));
  const responder = (status: number, body: unknown) => new Response(JSON.stringify(body), { status, headers: h });
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: h });
  if (req.method !== "POST") return responder(405, { error: "metodo-no-permitido" });
  try {
    const token = (req.headers.get("Authorization") ?? "").replace(/^Bearer\s+/i, "").trim();
    if (!token) return responder(401, { error: "no-autorizado" });
    const { data: u, error: eu } = await db.auth.getUser(token);
    if (eu || !u?.user?.id) return responder(401, { error: "no-autorizado" });
    const texto = await req.text();
    if (texto.length > MAX_CUERPO) return responder(400, { error: "datos-invalidos" });
    let cuerpo: unknown;
    try { cuerpo = JSON.parse(texto || "{}"); } catch { return responder(400, { error: "datos-invalidos" }); }
    const r = await servicio.manejar(u.user.id, cuerpo);
    return responder(r.status, r.body);
  } catch (e) {
    console.error("desafio:", e);
    return responder(500, { error: "error-servidor" });
  }
});
