"""Genera icono-192.png e icono-512.png (libro abierto) solo con la biblioteca estándar.
Uso: python iconos/generar_iconos.py  — el dibujo queda dentro de la zona segura de iconos 'maskable'."""
import os, struct, zlib

FONDO, PAPEL, LINEA, HILO = (29, 39, 44), (236, 235, 228), (154, 163, 166), (192, 71, 59)


def pixel(x, y):  # coordenadas normalizadas 0..1
    # páginas: dos rectángulos con borde superior/inferior curvado hacia el lomo
    if 0.19 <= x <= 0.81:
        d = abs(x - 0.5)
        curva = 0.035 * (1 - d / 0.31)
        arriba, abajo = 0.30 + curva, 0.72 + curva
        if arriba <= y <= abajo:
            if d < 0.012:
                return HILO
            # renglones
            for r in (0.40, 0.48, 0.56):
                if abs(y - (r + curva)) < 0.01 and 0.08 < d < 0.24:
                    return LINEA
            return PAPEL
    return FONDO


def png(n, ruta):
    filas = bytearray()
    for j in range(n):
        filas.append(0)
        for i in range(n):
            filas.extend(pixel((i + 0.5) / n, (j + 0.5) / n))
    def bloque(t, datos):
        c = t + datos
        return struct.pack('>I', len(datos)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
    with open(ruta, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + bloque(b'IHDR', struct.pack('>IIBBBBB', n, n, 8, 2, 0, 0, 0))
                + bloque(b'IDAT', zlib.compress(bytes(filas), 9)) + bloque(b'IEND', b''))


aqui = os.path.dirname(os.path.abspath(__file__))
for n in (192, 512):
    png(n, os.path.join(aqui, f'icono-{n}.png'))
    print('ok', n)
