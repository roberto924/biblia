"""Catálogo de imágenes, objetos, mapas antiguos, videos y audio → datos/recursos.js.

Uso:  python -I herramientas/recursos.py

Entrada (no se modifica):
  recursos/catalogo.json   fichas investigadas (ver recursos/LEEME.md)
  recursos/auditoria.json  opcional: {fichas: {id: {veredicto: OK|AJUSTAR|RECHAZAR, refs?, motivo}}}
  datos/biblia.js          para comprobar que cada ref de Gn/Ex existe (capítulo y versículo)

Reglas:
  - RECHAZAR se excluye; AJUSTAR sustituye las refs por las de la auditoría.
  - Licencia «desconocida» o «Derechos reservados»: solo se conserva si no se copia nada
    (uso solo_enlace, o incrustable con el reproductor oficial); nunca como imagen local.
  - Las imágenes se sirven desde recursos/imagenes/ (ruta relativa). Si el uso no es
    «descargable», el archivo local no se usa.
  - Refs de Gn y Ex → rangos de claves de la app (libro*1e6 + cap*1000 + v). Las de otros
    libros se conservan como texto, sin rango (no se enlazan a pasajes).

Verificación (exit 1 y no escribe nada si falla): cada imagen existe; cada ficha mostrada
tiene licencia, atribución, fuente y refs de Gn/Ex válidas.
"""
import json
import os
import re
import struct
import sys
from datetime import datetime, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOGO = os.path.join(RAIZ, 'recursos', 'catalogo.json')
AUDITORIA = os.path.join(RAIZ, 'recursos', 'auditoria.json')
BIBLIA = os.path.join(RAIZ, 'datos', 'biblia.js')
SALIDA = os.path.join(RAIZ, 'datos', 'recursos.js')

# Mismo orden que CANON en app.js (la clave depende de él).
CANON = ['Gn', 'Ex', 'Lv', 'Nm', 'Dt', 'Jos', 'Jue', 'Rt', '1S', '2S', '1R', '2R', '1Cr', '2Cr', 'Esd', 'Neh', 'Est', 'Job', 'Sal',
         'Pr', 'Ec', 'Cnt', 'Is', 'Jer', 'Lm', 'Ez', 'Dn', 'Os', 'Jl', 'Am', 'Abd', 'Jon', 'Mi', 'Nah', 'Hab', 'Sof', 'Hag', 'Zac', 'Mal']
ORD = {b: i + 1 for i, b in enumerate(CANON)}
ENLAZABLES = ('Gn', 'Ex', 'Lv', 'Nm', 'Dt')
TIPOS = ('arte', 'arqueologia', 'mapa_antiguo', 'video', 'audio', 'reconstruccion', 'ilustracion')
USOS = ('descargable', 'solo_enlace', 'incrustable')
RESTRINGIDAS = ('desconocida', 'derechos reservados')
# recursos/auditoria.md: «Escenas cruentas a filtrar en perfil niño: Gn 4 (Caín), Gn 7, Gn 8, Ex 9, Ex 10,
# Ex 12, Ex 32 (Schnorr)». Se marcan `sensible` las imágenes de esos capítulos (de Ex 32, solo la de Schnorr).
SENSIBLE_CAPS = {('Gn', 4), ('Gn', 7), ('Gn', 8), ('Ex', 9), ('Ex', 10), ('Ex', 12)}
SENSIBLE_IDS = {'schnorr-ex-32-becerro-oro'}
# Objetos cuyo vínculo con el pasaje es solo de contexto (auditoría): se rotulan «Contexto de la época».
CONTEXTO_PREFIJOS = ('amarna-', 'beni-hasan-', 'estela-merneptah-')
RE_REF = re.compile(r'^\s*([1-3]?[A-Za-zÀ-ÿ]+)\.?\s+(\d+)(?::(\d+))?(?:\s*[-–]\s*(?:(\d+):)?(\d+))?\s*$')
RE_YT = re.compile(r'(?:youtube(?:-nocookie)?\.com/(?:watch\?(?:.*&)?v=|embed/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})')


def leer_js(ruta):
    t = open(ruta, encoding='utf-8').read()
    return json.loads(t[t.index('{'):t.rstrip().rstrip(';').rindex('}') + 1])


def versiculos_por_cap(d):
    out = {}
    for c in d.get('capitulos', []):
        vs = [v['n'] for v in c.get('versiculos', [])]
        out[(c['libro'], int(c['cap']))] = max(vs) if vs else 0
    return out


def rango(ref, vmax):
    """'Gn 1:3-5' → (libro, a, b, error). Rango de capítulos 'Ex 25-27'; capítulo suelto 'Gn 10'."""
    m = RE_REF.match(ref or '')
    if not m:
        return None, None, None, f'ref ilegible «{ref}»'
    lb, c1, v1, c2, v2 = m.group(1), int(m.group(2)), m.group(3), m.group(4), m.group(5)
    if lb not in ORD:
        return None, None, None, f'libro desconocido en «{ref}»'
    if lb not in ENLAZABLES:
        return lb, None, None, None
    if v1 is None:  # capítulos: Gn 10 · Ex 25-27
        if c2 is not None:
            return lb, None, None, f'ref mixta «{ref}»'
        cb = int(v2) if v2 else c1
        a, b = (c1, 1), (cb, None)
    else:
        v1 = int(v1)
        if v2 is None:
            a, b = (c1, v1), (c1, v1)
        else:
            a, b = (c1, v1), (int(c2) if c2 else c1, int(v2))
    for cap, v in (a, b):
        if (lb, cap) not in vmax:
            return lb, None, None, f'capítulo inexistente en «{ref}»'
        if v is not None and not 1 <= v <= vmax[(lb, cap)]:
            return lb, None, None, f'versículo inexistente en «{ref}»'
    o = ORD[lb] * 1_000_000
    ka = o + a[0] * 1000 + a[1]
    kb = o + b[0] * 1000 + (b[1] if b[1] is not None else vmax[(lb, b[0])])
    if ka > kb:
        return lb, None, None, f'rango invertido «{ref}»'
    return lb, ka, kb, None


def medidas_jpeg(ruta):
    """(ancho, alto) leyendo el marcador SOF del JPEG; None si no se puede."""
    try:
        with open(ruta, 'rb') as f:
            if f.read(2) != b'\xff\xd8':
                return None
            while True:
                b = f.read(1)
                while b and b != b'\xff':
                    b = f.read(1)
                while b == b'\xff':
                    b = f.read(1)
                if not b:
                    return None
                m = b[0]
                if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
                    continue
                n = struct.unpack('>H', f.read(2))[0]
                if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    alto, ancho = struct.unpack('>xHH', f.read(5))
                    return ancho, alto
                f.seek(n - 2, 1)
    except (OSError, struct.error):
        return None


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass
    fichas = json.load(open(CATALOGO, encoding='utf-8'))
    if os.path.exists(AUDITORIA):
        aud = json.load(open(AUDITORIA, encoding='utf-8')).get('fichas', {})
        auditado = True
    else:
        aud, auditado = {}, False
        print('AVISO: no existe recursos/auditoria.json; todas las fichas quedan «sin auditar».')
    vmax = versiculos_por_cap(leer_js(BIBLIA))
    ruta_orig = os.path.join(RAIZ, 'datos', 'originales.js')
    videos_originales = ({v['youtube_id'] for v in leer_js(ruta_orig).get('videos', [])}
                         if os.path.exists(ruta_orig) else set())

    errores, salida, excluidas = [], [], []
    ids = set()
    for f in fichas:
        fid = f.get('id') or ''
        if fid in ids:
            errores.append(f'{fid}: id repetido')
        ids.add(fid)
        a = aud.get(fid) or {}
        ver = (a.get('veredicto') or '').upper() if auditado else ''
        if auditado and fid not in aud:
            ver = 'SIN AUDITAR'
        if ver == 'RECHAZAR':
            excluidas.append({'id': fid, 'motivo': 'auditoría: ' + (a.get('motivo') or 'rechazada')})
            continue
        lic = (f.get('licencia') or '').strip()
        uso = f.get('uso')
        restringida = lic.lower() in RESTRINGIDAS
        if restringida and uso not in ('solo_enlace', 'incrustable'):
            excluidas.append({'id': fid, 'motivo': f'licencia «{lic}» con uso «{uso}»'})
            continue
        refs = a.get('refs') if ver == 'AJUSTAR' and a.get('refs') else f.get('refs') or []
        rangos, refs_ok = [], []
        for r in refs:
            lb, ka, kb, err = rango(r, vmax)
            if err:
                errores.append(f'{fid}: {err}')
                continue
            refs_ok.append(r.strip())
            if ka is not None:
                rangos.append([ka, kb])
        # Comprobaciones de la ficha mostrada.
        tipo = f.get('tipo')
        if tipo not in TIPOS:
            errores.append(f'{fid}: tipo desconocido «{tipo}»')
        if uso not in USOS:
            errores.append(f'{fid}: uso desconocido «{uso}»')
        for campo in ('titulo', 'licencia', 'atribucion', 'url_fuente'):
            if not (f.get(campo) or '').strip():
                errores.append(f'{fid}: falta {campo}')
        if not refs_ok:
            errores.append(f'{fid}: sin refs válidas')
        if (f.get('url_fuente') or '') and not re.match(r'^https?://', f['url_fuente']):
            errores.append(f'{fid}: url_fuente no es http(s)')
        imagen, medidas = None, None
        if uso == 'descargable' and f.get('archivo_local') and not restringida:
            rel = f['archivo_local'].replace('\\', '/')
            ruta = os.path.join(RAIZ, *rel.split('/'))
            if not rel.startswith('recursos/imagenes/') or '..' in rel:
                errores.append(f'{fid}: archivo_local fuera de recursos/imagenes/')
            elif not os.path.isfile(ruta):
                errores.append(f'{fid}: no existe {rel}')
            else:
                imagen, medidas = rel, medidas_jpeg(ruta)
        if tipo in ('arte', 'reconstruccion', 'ilustracion', 'mapa_antiguo') and uso == 'descargable' and not imagen:
            errores.append(f'{fid}: descargable sin imagen local')
        yt = None
        for u in (f.get('url_archivo'), f.get('url_fuente')):
            mt = RE_YT.search(u or '')
            if mt:
                yt = mt.group(1)
                break
        if yt and yt in videos_originales:  # ya se muestra como video del libro (datos/originales.js)
            excluidas.append({'id': fid, 'motivo': f'video {yt} ya está en datos/originales.js'})
            continue
        modo = 'imagen' if imagen else ('incrustable' if uso == 'incrustable' and yt else 'enlace')
        caps = {(CANON[ka // 1_000_000 - 1], c) for ka, kb in rangos for c in range((ka // 1000) % 1000, (kb // 1000) % 1000 + 1)}
        sensible = bool(imagen) and tipo != 'mapa_antiguo' and (fid in SENSIBLE_IDS or bool(caps & SENSIBLE_CAPS))
        if imagen and isinstance(a.get('sensible'), bool):  # la auditoría (mirando la imagen) manda
            sensible = a['sensible']
        relacion = 'contexto' if tipo == 'arqueologia' and fid.startswith(CONTEXTO_PREFIJOS) else 'pasaje'
        salida.append({
            'id': fid, 'tipo': tipo, 'titulo': f['titulo'].strip(), 'descripcion': f.get('descripcion') or '',
            'autor': f.get('autor') or '', 'fecha': f.get('fecha_obra') or '', 'institucion': f.get('institucion') or '',
            'url_fuente': f['url_fuente'], 'imagen': imagen,
            'ancho': medidas[0] if medidas else None, 'alto': medidas[1] if medidas else None,
            'licencia': lic, 'atribucion': f['atribucion'].strip(), 'uso': uso, 'modo': modo, 'youtube': yt if modo == 'incrustable' else None,
            'certeza': f.get('certeza') or '', 'nota_certeza': f.get('nota_certeza') or '',
            'idioma': f.get('idioma'), 'duracion': f.get('duracion'),
            'refs': refs_ok, 'rangos': rangos, 'sensible': sensible, 'relacion': relacion,
            'auditoria': ver or 'sin auditar', 'motivo_auditoria': (a.get('motivo') or '') if ver == 'AJUSTAR' else '',
        })

    for e in errores:
        print('ERROR', e)
    for x in excluidas:
        print('excluida', x['id'], '·', x['motivo'])
    if errores:
        print(f'{len(errores)} errores: no se escribe {os.path.relpath(SALIDA, RAIZ)}')
        sys.exit(1)

    datos = {'generado': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'auditado': auditado,
             'fichas': salida, 'excluidas': excluidas}
    with open(SALIDA, 'w', encoding='utf-8', newline='\n') as fo:
        fo.write('/* Generado por herramientas/recursos.py desde recursos/catalogo.json. No editar a mano. */\n')
        fo.write('window.BIBLIA_RECURSOS = ')
        json.dump(datos, fo, ensure_ascii=False, separators=(',', ':'))
        fo.write(';\n')
    imgs = sum(1 for x in salida if x['imagen'])
    enl = sum(1 for x in salida if x['rangos'])
    print(f'{len(salida)} fichas mostradas ({imgs} con imagen local, {enl} enlazadas a {"/".join(ENLAZABLES)}), '
          f'{len(excluidas)} excluidas · auditado: {"sí" if auditado else "no"} → {os.path.relpath(SALIDA, RAIZ)} '
          f'({os.path.getsize(SALIDA) // 1024} KB)')


if __name__ == '__main__':
    main()
