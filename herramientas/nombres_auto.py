"""Localiza en un versículo RV1909 la forma española de un nombre propio inglés (BibleData/OpenBible).

Compara por «esqueleto» fonético simplificado (difflib) entre la etiqueta inglesa y las palabras
con mayúscula del versículo. Solo biblioteca estándar.
"""
import difflib
import re
import unicodedata

PALABRA = re.compile(r"[A-ZÁÉÍÓÚÂÊÎÔÛÑ][\wáéíóúâêîôûñü]*(?:-[\wáéíóúâêîôûñüÁÉÍÓÚÂÊÎÔÛÑ]+)*")
COMUNES = {"Y", "E", "O", "Mas", "Y", "Dios", "Jehová", "Señor", "Este", "Esta", "Estos", "Estas", "El",
           "La", "Los", "Las", "Entonces", "Porque", "Pues", "He", "Así", "Ahora", "Cuando", "Por",
           "No", "Yo", "Tú", "Que", "Sea", "Mira", "Ve", "Oh", "Si", "Mi", "Aconteció", "Después",
           "En", "De", "Al", "Á", "A", "Á", "Ruégote", "Ved", "Toma", "Sal", "Hijo", "Padre",
           "Dijo", "Respondió", "Vino", "Salió", "Fué", "Era", "Había", "Estaba", "Todo", "Todos"}


def sin_acentos(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


def esqueleto(s, idioma):
    s = sin_acentos(s).replace("-", "")
    reglas = [("sh", "s"), ("ph", "f"), ("th", "t"), ("ch", "c"), ("kh", "j"), ("qu", "c"), ("k", "c"),
              ("z", "s"), ("y", "i"), ("w", "v"), ("h", ""), ("x", "cs"), ("ee", "e"), ("oo", "o")]
    if idioma == "es":
        reglas = [("ph", "f"), ("th", "t"), ("ch", "c"), ("qu", "c"), ("k", "c"), ("z", "s"), ("y", "i"),
                  ("h", ""), ("x", "cs"), ("ll", "l"), ("j", "j")]
    for a, b in reglas:
        s = s.replace(a, b)
    return re.sub(r"(.)\1", r"\1", s)


def parecido(ingles, espanol):
    a, b = esqueleto(ingles, "en"), esqueleto(espanol, "es")
    if not a or not b:
        return 0.0
    r = difflib.SequenceMatcher(None, a, b).ratio()
    if a[0] != b[0] and not (a[0] in "ie" and b[0] in "ie"):
        r -= 0.15
    return r


def candidatas(verso):
    return [m.group(0) for m in PALABRA.finditer(verso) if m.group(0) not in COMUNES]


def mejor_forma(ingles, verso, umbral=0.62):
    """Devuelve (forma, puntuación) o (None, 0)."""
    mejor, pm = None, 0.0
    partes = ingles.split()
    for w in candidatas(verso):
        p = parecido(ingles, w)
        if len(partes) > 1:
            p = max(p, parecido(partes[0], w) - 0.05)
        if p > pm:
            mejor, pm = w, p
    return (mejor, pm) if pm >= umbral else (None, pm)
