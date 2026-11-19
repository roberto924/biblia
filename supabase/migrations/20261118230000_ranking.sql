-- Ranking mundial del desafío (diseño: docs/superpowers/specs/2026-11-18-ranking-mundial-design.md, contrato v2).
--
-- Acceso de la app (roles anon y authenticated; los usuarios anónimos de Supabase Auth son authenticated):
--   · NINGUNA tabla se lee ni se escribe por REST: RLS activado en todas, sin políticas y sin privilegios.
--   · Lo único público es la RPC public.ranking(tipo, nombre, limite) (security definer, search_path fijo), y solo
--     para adultos (v3: ningún nombre de niño se publica en una lista).
-- Todo lo demás pasa por la Edge Function `desafio`, que usa la clave de servicio (service_role salta RLS) y las
-- funciones internas desafio_llamada() y desafio_posicion(), que solo puede ejecutar service_role.

-- ---------- Tablas ----------
create table public.personajes_desafio (
  personaje   text primary key check (personaje ~ '^[A-Za-z0-9_]{1,64}$'),
  nivel       integer not null check (nivel >= 0),
  n_preguntas integer not null check (n_preguntas between 1 and 50),
  hasta_orden integer not null check (hasta_orden >= 0), -- ordinal del último versículo de su capítulo «listo»
  sin_nino    boolean not null default false
);

create table public.preguntas (
  id        text primary key check (id ~ '^[0-9a-f]{16}$'),
  personaje text not null references public.personajes_desafio (personaje) on delete cascade,
  libro     text not null,
  ref       text not null,
  orden     integer not null check (orden >= 0),          -- ordinal del versículo de `ref` (Gn 1:1 = 0)
  cita      text not null,
  pregunta  text not null,
  opciones  jsonb not null check (jsonb_typeof(opciones) = 'array' and jsonb_array_length(opciones) = 4),
  correcta  smallint not null check (correcta between 0 and 3),
  nino      boolean not null default true
);
create index preguntas_personaje_idx on public.preguntas (personaje, orden);

create table public.perfiles (
  id                uuid primary key references auth.users (id) on delete cascade,
  nombre            text not null check (char_length(nombre) between 3 and 40),
  -- Clave de unicidad calculada por la función (minúsculas y sin tildes: «José» = «jose»).
  nombre_clave      text not null check (nombre_clave = lower(nombre_clave) and char_length(nombre_clave) between 3 and 40),
  tipo              text not null check (tipo in ('adulto', 'nino')),
  zona_horaria      text not null check (char_length(zona_horaria) between 1 and 64),
  -- Ley 21.719 (Chile), art. 16 quáter: hora (del servidor) en que un adulto consintió el registro de un niño.
  consentimiento_en timestamptz,
  creado            timestamptz not null default now(),
  constraint perfiles_consentimiento check ((tipo = 'nino') = (consentimiento_en is not null))
);
create unique index perfiles_nombre_clave_key on public.perfiles (nombre_clave);

create table public.intentos (
  id          uuid primary key default gen_random_uuid(),
  perfil      uuid not null references public.perfiles (id) on delete cascade,
  personaje   text not null,
  dia         date not null,                       -- día local en la zona fija del perfil
  seg         integer not null check (seg between 1 and 120),
  total       integer not null check (total between 1 and 50),
  servidas    jsonb not null,                      -- [{ id, orden: [4] }]
  servidas_en jsonb not null,                      -- [ms epoch, hora de la base, en que se sirvió cada pregunta]
  respuestas  jsonb not null default '[]'::jsonb,  -- [{ opcion, acierto, ms }]
  i           integer not null default 0,          -- pregunta en curso (cerrojo optimista)
  aciertos    integer not null default 0,
  ms          integer not null default 0 check (ms >= 0),
  terminado   boolean not null default false,
  superado    boolean not null default false,
  puntos      integer not null default 0 check (puntos >= 0),
  creado      timestamptz not null default now(),
  constraint intentos_un_dia unique (perfil, personaje, dia),
  constraint intentos_i check (i between 0 and total),
  constraint intentos_aciertos check (aciertos between 0 and total),
  constraint intentos_superado check (not superado or (terminado and aciertos = total)),
  constraint intentos_puntos check (superado or puntos = 0)
);
-- Un solo superado por perfil y personaje (el ranking no puede sumar dos veces).
create unique index intentos_un_superado on public.intentos (perfil, personaje) where superado;
-- Para el ranking.
create index intentos_superados_idx on public.intentos (perfil) include (puntos, ms) where superado;

-- Límite de llamadas a la función por usuario (ventana fija de un minuto).
create table public.llamadas (
  usuario uuid primary key references auth.users (id) on delete cascade,
  ventana timestamptz not null,
  n       integer not null
);

-- ---------- RLS y privilegios: nada para anon ni authenticated ----------
alter table public.personajes_desafio enable row level security;
alter table public.preguntas          enable row level security;
alter table public.perfiles           enable row level security;
alter table public.intentos           enable row level security;
alter table public.llamadas           enable row level security;

revoke all on table public.personajes_desafio, public.preguntas, public.perfiles, public.intentos, public.llamadas
  from public, anon, authenticated;
grant select, insert, update, delete on table public.personajes_desafio, public.preguntas, public.perfiles,
  public.intentos, public.llamadas to service_role;
-- Sin políticas: con RLS activado, anon y authenticated no verían ninguna fila aunque tuvieran privilegios.

-- ---------- Funciones internas (solo service_role) ----------
-- Una sola RPC por llamada a la función: cuenta la llamada del usuario (ventana fija del minuto en curso) y devuelve
-- { permitido, ahora }: si no pasó de `limite`, y la hora de la base en ms, con la que se sirve y cronometra todo.
create function public.desafio_llamada(usuario uuid, limite integer)
returns jsonb
language sql volatile
set search_path = ''
as $$
  insert into public.llamadas as l (usuario, ventana, n) values ($1, clock_timestamp(), 1)
  on conflict (usuario) do update set
    n       = case when l.ventana < clock_timestamp() - interval '1 minute' then 1 else l.n + 1 end,
    ventana = case when l.ventana < clock_timestamp() - interval '1 minute' then clock_timestamp() else l.ventana end
  returning jsonb_build_object('permitido', n <= $2,
                               'ahora', (extract(epoch from clock_timestamp()) * 1000)::bigint);
$$;

-- Acción `posicion` (v3): puesto del perfil entre los de su tipo con algún superado (null si aún no tiene puntos),
-- cuántos son y sus totales. null si el perfil no existe.
create function public.desafio_posicion(usuario uuid)
returns jsonb
language sql stable
set search_path = ''
as $$
  with yo as (
    select p.tipo from public.perfiles p where p.id = $1
  ), filas as (
    select p.id,
           rank() over (order by sum(i.puntos) desc, sum(i.ms) asc)::integer as puesto,
           sum(i.puntos)::integer as puntos,
           count(*)::integer      as personajes,
           sum(i.ms)::integer     as ms
    from public.perfiles p
    join public.intentos i on i.perfil = p.id and i.superado
    where p.tipo = (select yo.tipo from yo)
    group by p.id
  )
  select case when not exists (select 1 from yo) then null else jsonb_build_object(
    'puesto',     (select f.puesto from filas f where f.id = $1),
    'total',      (select count(*) from filas)::integer,
    'puntos',     coalesce((select f.puntos from filas f where f.id = $1), 0),
    'personajes', coalesce((select f.personajes from filas f where f.id = $1), 0),
    'ms',         coalesce((select f.ms from filas f where f.id = $1), 0)
  ) end;
$$;

revoke all on function public.desafio_llamada(uuid, integer), public.desafio_posicion(uuid) from public, anon, authenticated;
grant execute on function public.desafio_llamada(uuid, integer), public.desafio_posicion(uuid) to service_role;

-- ---------- Ranking (RPC pública) ----------
-- POST /rest/v1/rpc/ranking { tipo, nombre?, limite? } → [{ puesto, nombre, puntos, personajes, ms }].
-- v3: solo tipo 'adulto'; con 'nino' (o cualquier otro) devuelve vacío: los niños solo ven su posición (`posicion`).
-- Solo perfiles con algún personaje superado; puesto = rank() dentro del tipo (puntos desc, ms asc); con nombre,
-- solo esa fila (sin distinguir mayúsculas). Nunca ids. Se usa un tipo compuesto porque los parámetros de entrada
-- (tipo, nombre) y las columnas de salida no pueden compartir nombre.
create type public.fila_ranking as (puesto integer, nombre text, puntos integer, personajes integer, ms integer);

create function public.ranking(tipo text, nombre text default null, limite integer default 100)
returns setof public.fila_ranking
language sql stable
security definer
set search_path = ''
as $$
  select r.puesto, r.nombre, r.puntos, r.personajes, r.ms
  from (
    select rank() over (order by sum(i.puntos) desc, sum(i.ms) asc)::integer as puesto,
           p.nombre,
           p.nombre_clave,
           sum(i.puntos)::integer as puntos,
           count(*)::integer      as personajes,
           sum(i.ms)::integer     as ms
    from public.perfiles p
    join public.intentos i on i.perfil = p.id and i.superado
    where p.tipo = 'adulto' and $1 = 'adulto'
    group by p.id, p.nombre, p.nombre_clave
  ) r
  where $2 is null or r.nombre_clave = lower($2) or lower(r.nombre) = lower($2)
  order by r.puesto, r.nombre
  limit least(greatest(coalesce($3, 100), 1), 100);
$$;

revoke all on function public.ranking(text, text, integer) from public, anon, authenticated;
grant execute on function public.ranking(text, text, integer) to anon, authenticated, service_role;
