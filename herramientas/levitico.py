"""Levítico 1–27: personas, relaciones, pasajes, menciones y lugares (lo usa construir_datos.py).

Reutiliza la lógica de exodo.py (exodo.construir / exodo.construir_lugares con este módulo como
configuración). Mismo principio: cada dato lleva versículo, fuente y certeza; las citas se comprueban
literalmente contra la RV1909. Las personas de Éxodo (Moisés, Aarón, sus hijos, Uziel…) son la misma
persona (mismo id de BibleData): se amplían sus `refs`. Levítico no da edades ni años: no hay cronología
propia. Solo biblioteca estándar.
"""
import sys

import exodo

LIBRO = "Lv"
NOMBRE = "Levítico"
USX = "LEV"
CAPITULOS = 27
VERSICULOS = 859

EXCLUIR = {"YHVH_1", "NA"}
# En Levítico «Israel» es el pueblo; de Jacob solo vale la fila con la etiqueta «Jacob» (Lv 26:42).
SOLO_ETIQUETA = {"Jacob_1": {"Jacob"}}
FORMA_NO_MENCION = {("Jacob_1", "israel")}
PV_DESCARTAR = {}
FORMAS_FORZADAS = {"Dibri_1": ["Dribi"], "Shelomith_1": ["Selomith"]}

MODERNO = {"Shelomith_1": "Selomit", "Dibri_1": "Dibri"}
NOTAS = {
    "Shelomith_1": "Lv 24:11: «su madre se llamaba Selomith, hija de Dribi, de la tribu de Dan». Madre del hijo que "
                   "blasfema el Nombre (Lv 24:10-11).",
    "Dibri_1": "BibleData lo registra como Dibri; la RV1909 escribe «Dribi» (Lv 24:11).",
}
IDENTIDAD = {}
# Notas que se añaden a personas que ya vienen de Génesis/Éxodo.
NOTAS_EXISTENTES = {
    "Uzziel_1": "Lv 10:4 lo llama «tío de Aarón» (es hermano de Amram: ambos hijos de Coat, Ex 6:18).",
    "Mishael_1": "Lv 10:4-5: Moisés lo llama para sacar a Nadab y Abiú («vuestros hermanos») fuera del campamento.",
    "Elzaphan_1": "Lv 10:4-5: Moisés lo llama para sacar a Nadab y Abiú («vuestros hermanos») fuera del campamento.",
    "Nadab_1": "Lv 10:1-2: ofrece con Abiú «fuego extraño» y ambos mueren por fuego salido de delante de Jehová.",
    "Abihu_1": "Lv 10:1-2: ofrece con Nadab «fuego extraño» y ambos mueren por fuego salido de delante de Jehová.",
}
NOTAS_VERIFICAR = [("TM", (10, 4), "tío de Aarón"), ("TM", (10, 4), "vuestros hermanos"),
                   ("TM", (10, 5), "sacáronlos con sus túnicas fuera del campo"), ("TM", (10, 1), "fuego extraño"),
                   ("TM", (10, 2), "salió fuego de delante de Jehová que los quemó, y murieron"),
                   ("TM", (24, 10), "el cual era hijo de un Egipcio"),
                   ("TM", (24, 11), "su madre se llamaba Selomith, hija de Dribi, de la tribu de Dan"),
                   ("TM", (24, 23), "sacaron al blasfemo fuera del real, y apedreáronlo")]
ROLES = {
    "Dibri_1": ("padre de Selomit, de la tribu de Dan", (24, 11), "hija de Dribi, de la tribu de Dan"),
    "Hijo_de_Selomit": ("blasfema el Nombre y es apedreado", (24, 11),
                        "el hijo de la mujer Israelita pronunció el Nombre, y maldijo"),
}
SIN_NOMBRE = {
    "Hijo_de_Selomit": ("Hijo de Selomit (el blasfemo)", "m",
                        "El texto no da su nombre. Su padre era un egipcio, del que tampoco da el nombre (Lv 24:10); "
                        "es apedreado fuera del campamento (Lv 24:23).",
                        [("Shelomith_1", "Hijo_de_Selomit", "madre", (24, 11), "explicito",
                          "su madre se llamaba Selomith")]),
}
REFS_EXTRA = {"Hijo_de_Selomit": [(24, 10), (24, 14), (24, 23)]}
RELACIONES = [("Dibri_1", "Shelomith_1", "padre", (24, 11), "Selomith, hija de Dribi", "")]
NOTAS_REL = {}
# Relaciones que ya están en Éxodo y que Levítico repite: se añade la referencia a la nota.
REPITE_GN = [
    ("Aaron_1", "Nadab_1", "padre", (10, 1), "hijos de Aarón, Nadab y Abiú"),
    ("Aaron_1", "Abihu_1", "padre", (10, 1), "hijos de Aarón, Nadab y Abiú"),
    ("Aaron_1", "Eleazar_1", "padre", (10, 6), "á Aarón, y á Eleazar y á Ithamar, sus hijos"),
    ("Aaron_1", "Ithamar_1", "padre", (10, 6), "á Aarón, y á Eleazar y á Ithamar, sus hijos"),
    ("Uzziel_1", "Mishael_1", "padre", (10, 4), "á Misael, y á Elzaphán, hijos de Uzziel"),
    ("Uzziel_1", "Elzaphan_1", "padre", (10, 4), "á Misael, y á Elzaphán, hijos de Uzziel"),
]
EDADES = []  # Levítico no da edades

S1 = "Las ofrendas (Lv 1–7)"
S2 = "La consagración de los sacerdotes (Lv 8–10)"
S3 = "Lo puro y lo impuro (Lv 11–15)"
S4 = "El día de la expiación (Lv 16)"
S5 = "La ley de santidad (Lv 17–26)"
S6 = "Votos y cosas consagradas (Lv 27)"
PASAJES = [
    ("1:1", "1:17", "El holocausto", "Jehová llama a Moisés desde el tabernáculo y da la ley del holocausto de ganado vacuno, ovejas, cabras o aves.", S1),
    ("2:1", "2:16", "La ofrenda de presente", "La ofrenda de flor de harina con aceite e incienso, cocida o cruda; sin levadura ni miel, y siempre con sal.", S1),
    ("3:1", "3:17", "El sacrificio de paces", "Sacrificio de paces de vacas, ovejas o cabras; la grosura es de Jehová y no se come grosura ni sangre.", S1),
    ("4:1", "4:21", "Expiación por el sacerdote y por la congregación", "Becerro por el pecado por yerro del sacerdote ungido y de toda la congregación.", S1),
    ("4:22", "4:35", "Expiación por el príncipe y por el pueblo", "Macho cabrío por el príncipe; cabra o cordera por una persona del común del pueblo.", S1),
    ("5:1", "5:13", "Faltas ocultas y ofrenda según los recursos", "Testigo que calla, contacto con lo inmundo y juramento a la ligera; quien no alcanza para un cordero trae tórtolas o harina.", S1),
    ("5:14", "6:7", "La expiación de la culpa", "Ofrenda por la culpa en las cosas santas y por el daño al prójimo, con restitución y un quinto más.", S1),
    ("6:8", "6:23", "Leyes del holocausto y del presente para los sacerdotes", "El fuego del altar no se apagará; la porción de los sacerdotes y la ofrenda del día de la unción.", S1),
    ("6:24", "7:10", "Leyes de la expiación y de la culpa", "Dónde se degüellan y quién come la expiación y la culpa, cosas muy santas.", S1),
    ("7:11", "7:21", "Ley del sacrificio de paces", "Paces en acción de gracias, por voto o voluntarias; cuándo se comen y quién no puede comerlas.", S1),
    ("7:22", "7:38", "Grosura, sangre y la porción de los sacerdotes", "No se come grosura ni sangre; el pecho y la espaldilla son de Aarón y sus hijos. Resumen de las leyes dadas en el monte Sinaí.", S1),
    ("8:1", "8:13", "Moisés viste y unge a Aarón y a sus hijos", "Ante la congregación, Moisés lava a Aarón y a sus hijos, los viste y unge el tabernáculo y a Aarón.", S2),
    ("8:14", "8:29", "Los sacrificios de la consagración", "Becerro de expiación, carnero del holocausto y carnero de las consagraciones; la sangre en la oreja, el pulgar de la mano y del pie.", S2),
    ("8:30", "8:36", "Siete días de consagración", "Moisés rocía aceite y sangre sobre ellos; durante siete días no salen de la puerta del tabernáculo.", S2),
    ("9:1", "9:14", "El día octavo: Aarón ofrece por sí", "Aarón ofrece por primera vez la expiación y el holocausto por sí mismo.", S2),
    ("9:15", "9:24", "Fuego de delante de Jehová", "Aarón ofrece por el pueblo y lo bendice; la gloria de Jehová aparece y un fuego consume el holocausto.", S2),
    ("10:1", "10:7", "Nadab y Abiú", "Los hijos de Aarón ofrecen fuego extraño y mueren; Misael y Elzafán sacan sus cuerpos y Aarón no hace duelo.", S2),
    ("10:8", "10:20", "Normas para los sacerdotes", "Ni vino ni sidra al entrar en el tabernáculo; distinguir lo santo de lo profano; Moisés se enoja con Eleazar e Itamar.", S2),
    ("11:1", "11:12", "Animales de la tierra y del agua", "Qué animales de la tierra y del agua se pueden comer y cuáles son inmundos.", S3),
    ("11:13", "11:28", "Aves, insectos y cuerpos muertos", "Aves e insectos que no se comen; quien toca sus cuerpos muertos queda inmundo hasta la tarde.", S3),
    ("11:29", "11:47", "Los reptiles; «seréis santos»", "Reptiles inmundos y objetos que contaminan; «seréis santos, porque yo soy santo».", S3),
    ("12:1", "12:8", "La purificación después del parto", "Días de purificación de la madre por hijo o hija y su ofrenda.", S3),
    ("13:1", "13:17", "La lepra: el examen del sacerdote", "El sacerdote examina las manchas de la piel, encierra siete días y declara limpio o inmundo.", S3),
    ("13:18", "13:37", "Apostemas, quemaduras y tiña", "Llagas que aparecen en una apostema sanada, en una quemadura o en la cabeza y la barba.", S3),
    ("13:38", "13:46", "Otras manchas; el leproso fuera del campamento", "Manchas blancas, calvicie y el leproso, que habita solo fuera del real.", S3),
    ("13:47", "13:59", "La lepra en los vestidos", "Plaga en vestidos de lana o lino y en pieles: examen, lavado o fuego.", S3),
    ("14:1", "14:20", "La purificación del leproso", "Las dos avecillas, el lavado, los siete días y los sacrificios del leproso sanado.", S3),
    ("14:21", "14:32", "Purificación del leproso pobre", "Si no alcanza, ofrece un cordero y dos tórtolas o dos palominos.", S3),
    ("14:33", "14:45", "La plaga en las casas", "En la tierra de Canaán: el sacerdote examina la casa, manda quitar piedras o derribarla.", S3),
    ("14:46", "14:57", "Purificación de la casa; resumen de la ley", "Quien entra en la casa cerrada queda inmundo; purificación de la casa y resumen de la ley de la lepra.", S3),
    ("15:1", "15:18", "Flujos del hombre", "Impureza por flujo y por derramamiento de semen, y cómo se purifica.", S3),
    ("15:19", "15:33", "Flujos de la mujer", "Impureza por la menstruación y por un flujo prolongado, y su purificación.", S3),
    ("16:1", "16:10", "Aarón no entrará en todo tiempo", "Tras la muerte de sus hijos, Aarón entra tras el velo solo como Dios manda; suertes sobre dos machos cabríos.", S4),
    ("16:11", "16:22", "La expiación del santuario y el macho cabrío vivo", "Sangre sobre la cubierta del arca; Aarón confiesa las iniquidades sobre el macho cabrío vivo y lo envía al desierto.", S4),
    ("16:23", "16:34", "Estatuto perpetuo: el día diez del mes séptimo", "Aarón se cambia las vestiduras; cada año, el día diez del mes séptimo, se aflige el alma y se hace expiación.", S4),
    ("17:1", "17:16", "El lugar del sacrificio y la sangre", "Los sacrificios se llevan a la puerta del tabernáculo; no se come sangre, porque la vida de la carne está en la sangre.", S5),
    ("18:1", "18:18", "Uniones prohibidas entre parientes", "No hacer como en Egipto ni como en Canaán; lista de parientes con quienes no hay unión.", S5),
    ("18:19", "18:30", "Otras prácticas prohibidas", "Prohibiciones, entre ellas dar hijos a Moloc; la tierra vomita a los pueblos que hicieron estas cosas.", S5),
    ("19:1", "19:18", "«Santos seréis»; amarás a tu prójimo", "Honra a padre y madre, sábados, la rebusca para el pobre, justicia; «amarás a tu prójimo como a ti mismo».", S5),
    ("19:19", "19:37", "Leyes diversas; el extranjero", "Mezclas, árboles nuevos, prácticas paganas, respeto al anciano; amar al extranjero; pesas justas.", S5),
    ("20:1", "20:8", "Moloc y los adivinos", "Pena para quien da de sus hijos a Moloc y para quien acude a encantadores y adivinos.", S5),
    ("20:9", "20:27", "Penas por maldecir a los padres y por uniones prohibidas", "Penas por maldecir a los padres y por adulterio e incesto; Israel apartado de los pueblos; el adivino es apedreado.", S5),
    ("21:1", "21:15", "La santidad de los sacerdotes", "Duelo, matrimonio y conducta de los sacerdotes y del sumo sacerdote.", S5),
    ("21:16", "21:24", "Sacerdotes con defecto", "El descendiente de Aarón con defecto físico come del pan de su Dios pero no se acerca a ofrecer.", S5),
    ("22:1", "22:16", "Quién come de las cosas santas", "El sacerdote inmundo no come de lo santo; quiénes de su casa pueden comer y quiénes no.", S5),
    ("22:17", "22:33", "Ofrendas sin defecto", "Los animales ofrecidos han de ser sin defecto; siete días con su madre; el sacrificio de acción de gracias.", S5),
    ("23:1", "23:14", "El sábado, la Pascua y las primicias", "El sábado, la Pascua, los panes sin levadura y la gavilla de las primicias.", S5),
    ("23:15", "23:22", "El nuevo presente a los cincuenta días", "Se cuentan cincuenta días y se ofrece presente nuevo; se deja la rebusca al pobre y al extranjero.", S5),
    ("23:23", "23:32", "El son de trompetas y el día de las expiaciones", "El primero del mes séptimo, conmemoración al son de trompetas; el día diez, día de las expiaciones.", S5),
    ("23:33", "23:44", "La solemnidad de las cabañas", "Siete días en cabañas desde el quince del mes séptimo, en memoria de la salida de Egipto.", S5),
    ("24:1", "24:9", "El aceite de las lámparas y los panes", "Aceite de olivas para las lámparas y doce tortas sobre la mesa cada sábado.", S5),
    ("24:10", "24:23", "El blasfemo", "El hijo de Selomit y de un egipcio blasfema el Nombre; Dios manda apedrearlo y da la ley del talión.", S5),
    ("25:1", "25:7", "El año sabático", "Dicho en el monte Sinaí: el séptimo año la tierra descansa.", S5),
    ("25:8", "25:22", "El año del jubileo", "Al año cincuenta se pregona libertad y cada uno vuelve a su posesión; Dios promete cosecha suficiente.", S5),
    ("25:23", "25:34", "El rescate de la tierra y de las casas", "La tierra es de Jehová y no se vende para siempre; el derecho de rescate y las ciudades de los levitas.", S5),
    ("25:35", "25:46", "El hermano empobrecido", "Préstamo sin usura al hermano pobre; el israelita vendido no sirve como esclavo.", S5),
    ("25:47", "25:55", "Rescate del vendido a un extranjero", "El israelita vendido a un extranjero puede ser rescatado; vuelve libre en el jubileo.", S5),
    ("26:1", "26:13", "Bendiciones por la obediencia", "Lluvias, cosechas, paz y la presencia de Dios si guardan sus mandamientos.", S5),
    ("26:14", "26:33", "Castigos por la desobediencia", "Si no obedecen: enfermedad, hambre, guerra, y al final la dispersión entre las naciones.", S5),
    ("26:34", "26:46", "La tierra descansa y Dios recuerda su pacto", "La tierra goza sus sábados; si confiesan, Dios se acordará de su pacto con Jacob, Isaac y Abraham.", S5),
    ("27:1", "27:15", "Votos de personas, animales y casas", "Estimación en siclos de las personas consagradas por voto, y de animales y casas.", S6),
    ("27:16", "27:34", "Tierras, primogénitos, anatema y diezmos", "Estimación de las tierras; los primogénitos, lo consagrado por anatema y el diezmo son de Jehová.", S6),
]

# Lugares: Egipto, Canaán y Sinaí ya existen (Génesis/Éxodo): solo se amplían sus refs.
LUGARES = {}
EXCLUIR_LUGAR = {
    "ab9a5ec": ("Azazel (Lv 16:8, 10, 26): el texto lo pone en paralelo con «por Jehová» y no lo presenta como "
                "un lugar; su sentido es discutido (Fuente externa). No se sitúa en el mapa."),
}
# En Lv 7:38 aparecen «monte de Sinaí» y «desierto de Sinaí» en el mismo versículo.
PRECEDIDO = {"abfba2a": "monte de ", "ae50cf1": "desierto de "}
OBLIGATORIOS_LUGAR = ["egipto", "canaan", "sinai", "desierto-de-sinai"]


def construir(cx):
    return exodo.construir(cx, sys.modules[__name__])


def construir_lugares(rv, menciones_personas, rutas, lugares_previos, errores, avisos, sa):
    return exodo.construir_lugares(rv, menciones_personas, rutas, lugares_previos, errores, avisos, sa,
                                   sys.modules[__name__])


# ---------------------------------------------------------------- hechos obligatorios (sobre los datos finales)
def comprobar(datos, errores):
    """Comprueba los hechos pedidos para Levítico (falla si falta alguno). Devuelve líneas de informe."""
    P = {p["id"]: p for p in datos["personas"]}
    R = {(x["de"], x["a"], x["tipo"]): x for x in datos["relaciones"]}
    caps = [c for c in datos["capitulos"] if c["libro"] == LIBRO]
    texto = {f"{LIBRO} {c['cap']}:{v['n']}": v["texto"] for c in caps for v in c["versiculos"]}
    M = {(m["ref"], m["persona"]) for m in datos["menciones"]}
    lineas = []

    def ok_(cond, desc):
        lineas.append(f"{'OK ' if cond else 'FALTA'} {desc}")
        if not cond:
            errores.append(f"Hecho obligatorio (Levítico): {desc}")

    ok_(len(caps) == CAPITULOS and len(texto) == VERSICULOS,
        f"{CAPITULOS} capítulos y {VERSICULOS} versículos (hay {len(caps)} y {len(texto)})")

    def tiene(pid, ref):
        return ref in P.get(pid, {}).get("refs", [])

    def rel(de, a, tipo, ref=None, certeza="explicito", nota=None):
        x = R.get((de, a, tipo))
        c = bool(x) and x["certeza"] == certeza and (ref is None or x["ref"] == ref) and (nota is None or nota in x["nota"])
        ok_(c, f"{de}→{a} {tipo}" + (f" {ref}" if ref else "") + (f" (nota con {nota})" if nota else "")
            + (f" [hay {x['ref']} {x['certeza']}]" if x and not c else ""))

    for h in ("Nadab_1", "Abihu_1"):
        ok_(tiene(h, "Lv 10:1") and ("Lv 10:1", h) in M, f"{h} con ref y mención en Lv 10:1")
        rel("Aaron_1", h, "padre", nota="Lv 10:1")
    for h in ("Mishael_1", "Elzaphan_1"):
        ok_(tiene(h, "Lv 10:4") and ("Lv 10:4", h) in M, f"{h} con ref y mención en Lv 10:4")
        rel("Uzziel_1", h, "padre", nota="Lv 10:4")
    ok_(tiene("Uzziel_1", "Lv 10:4") and "tío de Aarón" in P["Uzziel_1"]["nota"]
        and "tío de Aarón" in texto.get("Lv 10:4", ""), "Uziel, «tío de Aarón» (Lv 10:4), con ref y nota")
    rel("Kohath_1", "Uzziel_1", "padre", "Ex 6:18")
    rel("Kohath_1", "Amram_1", "padre", "Ex 6:18")
    rel("Amram_1", "Aaron_1", "padre", "Ex 6:20")
    # Selomit, hija de Dibri (RV1909 «Dribi»), de la tribu de Dan; su hijo sin nombre
    s, d, h = P.get("Shelomith_1", {}), P.get("Dibri_1", {}), P.get("Hijo_de_Selomit", {})
    v = texto.get("Lv 24:11", "")
    ok_(s.get("sexo") == "f" and s.get("nombre") == "Selomit" and s.get("nombre_rv1909") == "Selomith"
        and "Selomith" in v and tiene("Shelomith_1", "Lv 24:11"), "Selomit (RV1909 «Selomith», literal en Lv 24:11)")
    ok_(d.get("nombre_rv1909") == "Dribi" and "Dribi" in d.get("formas_rv1909", []) and "Dribi" in v
        and "tribu de Dan" in d.get("rol", "") and "de la tribu de Dan" in v,
        "Dibri (RV1909 «Dribi», literal en Lv 24:11), de la tribu de Dan")
    rel("Dibri_1", "Shelomith_1", "padre", "Lv 24:11")
    ok_(h.get("sin_nombre") is True and h.get("sexo") == "m" and tiene("Hijo_de_Selomit", "Lv 24:11"),
        "hijo de Selomit sin nombre (sin_nombre: true)")
    x = R.get(("Shelomith_1", "Hijo_de_Selomit", "madre"))
    ok_(bool(x) and x["ref"] == "Lv 24:11" and x.get("cita", "") in v and x.get("cita"),
        "Selomit→hijo madre con cita literal (Lv 24:11)")
    for pid in ("Moses_1", "Aaron_1"):
        n = sum(1 for r in P.get(pid, {}).get("refs", []) if r.startswith("Lv "))
        ok_(n > 0, f"{pid} con refs en Levítico ({n})")
    # Formas RV1909 literales: cada persona nueva con nombre aparece tal cual en alguna de sus refs de Lv
    for p in datos["personas"]:
        if p["sin_nombre"] or not p.get("nombre_rv1909") or not any(r.startswith("Lv ") for r in p["refs"]):
            continue
        if not any(r.startswith(("Gn ", "Ex ")) for r in p["refs"]):
            ok_(any(p["nombre_rv1909"] in texto.get(r, "") for r in p["refs"]),
                f"forma literal «{p['nombre_rv1909']}» de {p['id']}")
    # Pasajes y secciones
    pas = [p for p in datos["pasajes"] if p["libro"] == LIBRO]
    ok_(len(pas) == len(PASAJES) and pas[0]["inicio"] == "Lv 1:1" and pas[-1]["fin"] == "Lv 27:34",
        f"{len(pas)} pasajes lv-NN de Lv 1:1 a Lv 27:34")
    ok_(len({p["seccion"] for p in pas}) == 6, "6 secciones")
    # Lugares
    L = {l["id"]: l for l in datos["lugares"]}
    for lid in OBLIGATORIOS_LUGAR:
        l = L.get(lid)
        ok_(bool(l) and any(r.startswith("Lv ") for r in l["refs"]),
            f"lugar {lid} con refs de Levítico ({sum(1 for r in l['refs'] if r.startswith('Lv ')) if l else 0})")
    return lineas
