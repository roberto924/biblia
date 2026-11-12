"""Rut 1–4: personas, relaciones, pasajes, menciones y lugares (lo usa construir_datos.py).

Reutiliza la lógica de exodo.py (exodo.construir / exodo.construir_lugares con este módulo como configuración), como
Jueces. Cada dato lleva versículo, fuente y certeza; las citas se comprueban literalmente contra la RV1909. Las
personas de Génesis–Jueces (Fares, Hezrón, Aminadab, Naasón, Tamar, Judá, Raquel, Lea) son la misma persona (mismo id
de BibleData): se amplían sus `refs`.

Versificación (comprobada al generar): la RV1909 de eBible tiene 85 versículos (22, 23, 18, 22), los mismos que
Brenton y que la numeración inglesa de BibleData y OpenBible (sin `REMAP_REF`). Además de los recuentos se compara
versículo a versículo con Brenton: proporción de longitudes, comienzo y fin de cada capítulo, y que los nombres poco
frecuentes (Elimelec, Mahalón, Quelión, Orfa, Obed, Isaí, David, Fares, Belén) caigan en los mismos versículos.

Solo biblioteca estándar.
"""
import re
import sys

import exodo

LIBRO = "Rut"
NOMBRE = "Rut"
USX = "RUT"
CAPITULOS = 4
VERSICULOS = 85
POR_CAPITULO = [22, 23, 18, 22]
# Extremos de cada capítulo en la RV1909 y en Brenton (se comprueban: el contenido cae en el mismo versículo).
VERSIFICACION = [((1, 1), "Y ACONTECIÓ en los días que gobernaban los jueces"), ((1, 22), "Así volvió Noemi y Ruth"),
                 ((2, 1), "Y TENÍA Noemi un pariente de su marido"), ((2, 23), "Estuvo pues junta con las mozas de Booz"),
                 ((3, 1), "Y DÍJOLE su suegra Noemi"), ((3, 18), "Entonces [Noemi] dijo: Reposa"),
                 ((4, 1), "Y BOOZ subió á la puerta"), ((4, 22), "Y Obed engendró á Isaí")]
VERSIFICACION_LXX = [((1, 1), "when the judges ruled"), ((1, 22), "So Noemin and Ruth the Moabitess"),
                     ((2, 1), "And Noemin had"), ((2, 23), "damsels of Booz"), ((3, 1), "Noemin her mother-in-law"),
                     ((3, 18), "Sit still"), ((4, 1), "And Booz went up to the gate"), ((4, 22), "Obed begot Jess")]
# Nombres que deben caer en los mismos versículos en la RV1909 y en Brenton (comparación versículo a versículo).
PARALELOS = [("Elimelech", "Elimelech"), ("Mahalón", "Maalon"), ("Chelión", "Chelaion"), ("Orpha", "Orpha"),
             ("Obed", "Obed"), ("Isaí", "Jess"), ("David", "David"), ("Phares", "Phares"), ("Beth-lehem", "Bethleem")]
PROPORCION = (0.45, 1.6)  # longitud RV1909 / Brenton por versículo (observado: 0,54–1,36)

# Personas de BibleData que no se crean: Dios y «NA». BibleData no toma por personas en Rut a «Moabita», «Ephrateos»
# ni «Israel» (gentilicios y pueblo); Moab (hijo de Lot) no está situado en Rut.
EXCLUIR = {"YHVH_1", "NA"}
SOLO_ETIQUETA = {"Jacob_1": {"Jacob"}}
FORMA_NO_MENCION = {("Jacob_1", "israel")}
PV_DESCARTAR = {}
REL_DESCARTAR = {}
FORMAS_FORZADAS = {"Ruth_1": ["Ruth"], "Naomi_1": ["Noemi", "Mara"], "Boaz_1": ["Booz"], "Elimelech_1": ["Elimelech"],
                   "Mahlon_1": ["Mahalón"], "Chilion_1": ["Chelión"], "Orpah_1": ["Orpha"], "Obed_1": ["Obed"],
                   "Jesse_1": ["Isaí"], "David_1": ["David"], "Ram_1": ["Ram"], "Salmon_1": ["Salmón"],
                   "Nahshon_1": ["Nahasón"]}
MODERNO = {"Ruth_1": "Rut", "Naomi_1": "Noemí", "Boaz_1": "Booz", "Elimelech_1": "Elimelec", "Mahlon_1": "Mahlón",
           "Chilion_1": "Quelión", "Orpah_1": "Orfa", "Obed_1": "Obed", "Jesse_1": "Isaí", "David_1": "David",
           "Ram_1": "Ram", "Salmon_1": "Salmón"}
PARIENTE = "Pariente_de_Rut_4"  # el pariente más cercano sin nombre (Rut 3:12; 4:1-8)
NOTAS = {
    "Naomi_1": "Rut 1:20: «No me llaméis Noemi, sino llamadme Mara»: Mara es el nombre que ella pide, no otra persona.",
    "Boaz_1": ("Rut 2:1: «un pariente de su marido» (de Noemí), «de la familia de Elimelech»; Rut 2:20: «de nuestros "
               "redentores es». Rut 3:12: hay otro pariente más cercano. El texto no precisa el grado de parentesco."),
    "Mahlon_1": "Muere en Moab (Rut 1:5). Rut 4:10: «Ruth Moabita, mujer de Mahalón».",
    "Chilion_1": "Muere en Moab (Rut 1:5).",
    "Orpah_1": "Rut 1:14: «Orpha besó á su suegra, mas Ruth se quedó con ella».",
    "Salmon_1": ("La RV1909 de eBible escribe «Salmón» en Rut 4:20 y 4:21 (Brenton: «Salmon» en ambos); BibleData lo "
                 "registra como una sola persona (Salmon_1). No confundir con el monte Salmón (Jue 9:48)."),
    "Ram_1": ("Rut 4:19: «Hesrón engendró á Ram, y Ram engendró á Aminadab». BibleData lo hace abuelo de Aminadab según "
              "Lc 3:33 (Fuente externa, fuera del AT); aquí se sigue lo que dice Rut 4:19."),
    "Obed_1": "Rut 4:17: le ponen nombre «las vecinas»; «Este es padre de Isaí, padre de David».",
    "David_1": "En Rut solo aparece en la genealogía (Rut 4:17, 4:22), como hijo de Isaí.",
}
IDENTIDAD = {
    "Naomi_1": {"certeza": "texto", "refs": ["Rut 1:20"], "nombres_rv1909": ["Noemi", "Mara"], "fuente": "rv1909",
                "nota": "Rut 1:20: «No me llaméis Noemi, sino llamadme Mara»."},
}
NOTAS_VERIFICAR = [
    ("TM", (1, 20), "No me llaméis Noemi, sino llamadme Mara"), ("TM", (2, 1), "un pariente de su marido"),
    ("TM", (2, 1), "de la familia de Elimelech"), ("TM", (2, 20), "de nuestros redentores es"),
    ("TM", (3, 12), "hay pariente más cercano que yo"), ("TM", (1, 5), "Y murieron también los dos, Mahalón y Chelión"),
    ("TM", (4, 10), "Ruth Moabita, mujer de Mahalón"), ("TM", (1, 14), "Orpha besó á su suegra, mas Ruth se quedó con ella"),
    ("TM", (4, 20), "Salmón"), ("TM", (4, 21), "Salmón"), ("LXX", (4, 20), "Salmon"), ("LXX", (4, 21), "Salmon"),
    ("TM", (4, 19), "Hesrón engendró á Ram, y Ram engendró á Aminadab"), ("TM", (4, 17), "las vecinas"),
    ("TM", (4, 17), "Este es padre de Isaí, padre de David"), ("TM", (4, 1), "Eh, fulano"),
    ("TM", (4, 11), "las cuales dos edificaron la casa de Israel"), ("TM", (4, 18), "las generaciones de Phares"),
]
ROLES = {
    "Elimelech_1": ("varón de Belén de Judá, marido de Noemí", (1, 2), "El nombre de aquel varón era Elimelech"),
    "Naomi_1": ("mujer de Elimelec; vuelve de Moab a Belén", (1, 2), "el de su mujer Noemi"),
    "Mahlon_1": ("hijo de Elimelec y Noemí, marido de Rut", (4, 10), "Ruth Moabita, mujer de Mahalón"),
    "Chilion_1": ("hijo de Elimelec y Noemí", (1, 2), "Mahalón y Chelión"),
    "Orpah_1": ("moabita, nuera de Noemí; vuelve a su pueblo", (1, 4), "el nombre de la una Orpha"),
    "Ruth_1": ("moabita, nuera de Noemí, mujer de Booz", (1, 22), "Ruth Moabita su nuera"),
    "Boaz_1": ("pariente de Elimelec, varón poderoso de Belén", (2, 1), "varón poderoso y de hecho, de la familia de Elimelech"),
    "Obed_1": ("hijo de Booz y Rut, abuelo de David", (4, 17), "llamáronle Obed"),
    "Jesse_1": ("padre de David", (4, 17), "padre de Isaí, padre de David"),
    "David_1": ("hijo de Isaí", (4, 22), "Isaí engendró á David"),
    PARIENTE: ("pariente más cercano que Booz; renuncia a redimir", (3, 12), "hay pariente más cercano que yo"),
}
SIN_NOMBRE = {
    PARIENTE: ("El pariente más cercano (sin nombre)", "m",
               "El texto no da su nombre: Booz le dice «Eh, fulano» (Rut 4:1). Es pariente más cercano que Booz (Rut "
               "3:12) y renuncia a redimir la heredad de Elimelec y a tomar a Rut (Rut 4:6-8).", []),
}
RELACIONES = [
    ("Elimelech_1", "Naomi_1", "conyuge", (1, 3), "Elimelech, marido de Noemi",
     "Rut 1:2: «El nombre de aquel varón era Elimelech, y el de su mujer Noemi»."),
    ("Elimelech_1", "Mahlon_1", "padre", (1, 2), "los nombres de sus dos hijos eran, Mahalón y Chelión", ""),
    ("Elimelech_1", "Chilion_1", "padre", (1, 2), "los nombres de sus dos hijos eran, Mahalón y Chelión", ""),
    ("Naomi_1", "Mahlon_1", "madre", (1, 3), "quedó ella con sus dos hijos", "Rut 1:2 los nombra: «Mahalón y Chelión»."),
    ("Naomi_1", "Chilion_1", "madre", (1, 3), "quedó ella con sus dos hijos", "Rut 1:2 los nombra: «Mahalón y Chelión»."),
    ("Mahlon_1", "Ruth_1", "conyuge", (4, 10), "Ruth Moabita, mujer de Mahalón",
     "Rut 1:4: los dos hijos «tomaron para sí mujeres de Moab»."),
    ("Chilion_1", "Orpah_1", "conyuge", (1, 4), "el nombre de la una Orpha, y el nombre de la otra Ruth",
     "Rut 1:4 no dice quién se casó con quién; Rut 4:10 dice que Rut era «mujer de Mahalón», de donde se infiere que "
     "Orfa lo era de Quelión."),
    ("Boaz_1", "Ruth_1", "conyuge", (4, 13), "Booz pues tomó á Ruth, y ella fué su mujer",
     "Rut 4:10: «tomo por mi mujer á Ruth Moabita»."),
    ("Ruth_1", "Obed_1", "madre", (4, 13), "Jehová le dió que concibiese y pariese un hijo",
     "Rut 4:17: «llamáronle Obed»."),
    ("Boaz_1", "Obed_1", "padre", (4, 21), "Booz engendró á Obed", "Rut 4:13 y 4:17."),
    ("Obed_1", "Jesse_1", "padre", (4, 17), "Este es padre de Isaí", "Rut 4:22: «Obed engendró á Isaí»."),
    ("Jesse_1", "David_1", "padre", (4, 17), "Isaí, padre de David", "Rut 4:22: «Isaí engendró á David»."),
    ("Hezron_2", "Ram_1", "padre", (4, 19), "Hesrón engendró á Ram", ""),
    ("Ram_1", "Amminadab_1", "padre", (4, 19), "Ram engendró á Aminadab",
     "BibleData la registra como abuelo/nieto (según Lc 3:33, Fuente externa); Rut 4:19 dice «engendró»."),
    ("Nahshon_1", "Salmon_1", "padre", (4, 20), "Nahasón engendró á Salmón", ""),
    ("Salmon_1", "Boaz_1", "padre", (4, 21), "Salmón engendró á Booz", ""),
]
# Relaciones que el texto no dice: se dejan con certeza «inferido» (la nota dice por qué).
INFERIDAS = {("Chilion_1", "Orpah_1", "conyuge")}
NOTAS_REL = {}
# Relaciones de los libros anteriores que Rut repite: se añade la referencia a la nota.
REPITE_GN = [
    ("Judah_1", "Perez_1", "padre", (4, 12), "Phares, al que parió Thamar á Judá"),
    ("Tamar_1", "Perez_1", "madre", (4, 12), "Phares, al que parió Thamar"),
    ("Perez_1", "Hezron_2", "padre", (4, 18), "Phares engendró á Hesrón"),
    ("Amminadab_1", "Nahshon_1", "padre", (4, 20), "Aminadab engendró á Nahasón"),
]
EDADES = []
NOTAS_EXISTENTES = {
    "Perez_1": "Rut 4:18-22: «las generaciones de Phares» llegan hasta David.",
    "Rachel_1": "Rut 4:11: con Lea, «las cuales dos edificaron la casa de Israel».",
    "Leah_1": "Rut 4:11: con Raquel, «las cuales dos edificaron la casa de Israel».",
}
REFS_EXTRA = {PARIENTE: [(4, 1), (4, 3), (4, 6), (4, 8)]}
REFS_QUITAR = {}

S1 = "De Moab a Belén (Rut 1)"
S2 = "En el campo de Booz (Rut 2)"
S3 = "La era (Rut 3)"
S4 = "La puerta y la genealogía (Rut 4)"
PASAJES = [
    ("1:1", "1:5", "Elimelec y los suyos en Moab", "En días de los jueces, por el hambre, Elimelec de Belén va a Moab con Noemí y sus dos hijos; los hijos se casan con Orfa y Rut, y mueren los tres hombres.", S1),
    ("1:6", "1:22", "«Tu pueblo será mi pueblo»", "Noemí vuelve a Judá; Orfa regresa a su pueblo y Rut se queda con ella. En Belén, Noemí pide que la llamen Mara.", S1),
    ("2:1", "2:13", "Rut espiga en el campo de Booz", "Rut espiga tras los segadores en el campo de Booz, pariente de Elimelec, que la deja quedarse con sus criadas y la protege.", S2),
    ("2:14", "2:23", "«De nuestros redentores es»", "Booz le da de comer y manda dejarle espigas; Noemí reconoce en él a un pariente y Rut espiga hasta el fin de la siega.", S2),
    ("3:1", "3:18", "En la era de Booz", "Por consejo de Noemí, Rut va de noche a la era y se acuesta a los pies de Booz; él promete redimirla si no lo hace el pariente más cercano y la despide con seis medidas de cebada.", S3),
    ("4:1", "4:12", "El pariente en la puerta", "Ante diez ancianos, el pariente más cercano renuncia a redimir y se quita el zapato; Booz adquiere lo de Elimelec y toma por mujer a Rut.", S4),
    ("4:13", "4:22", "Nace Obed; de Fares a David", "Rut da a luz a Obed y las vecinas bendicen a Noemí; Obed es padre de Isaí, padre de David. Genealogía de Fares a David.", S4),
]
# Citas de los resúmenes que van entre comillas (se comprueban).
CITAS_RESUMEN = [((1, 16), "Tu pueblo será mi pueblo"), ((2, 20), "de nuestros redentores es")]

# ---------------------------------------------------------------- lugares
# OpenBible sitúa en Rut tres lugares: Belén y Moab (ya registrados) y Ephrathah, que se une a Efrata (misma
# identificación, Bethlehem, 1000). «Campos de Moab» en Rut es la tierra de Moab (OpenBible: Moab), no los llanos de
# Moab junto al Jordán (Nm 22:1): el lugar `campos-de-moab` no se marca en Rut.
LUGARES = {}
UNIR_LUGAR = {"af6c09e": "efrata"}
EXCLUIR_LUGAR = {}
PRECEDIDO = {}
LUGAR_OPCIONAL = set()
# Judá como región: OpenBible no la registra (ni en Rut ni en ningún libro), así que no hay identificación moderna.
# Se marca solo donde el texto la da como lugar (Rut 1:1, 1:2 «Beth-lehem de Judá»; 1:7 «la tierra de Judá»); en
# Rut 4:12 «Judá» es la persona.
JUDA = {"id": "juda", "nombre": "Judá", "nombre_rv1909": "Judá", "formas_rv1909": ["Judá"], "tipo": "region",
        "ubicacion": None, "alternativas": [], "fuente": "rv1909", "url_fuente": "",
        "nota": ("Región de la tribu de Judá: Rut 1:1-2 «Beth-lehem de Judá», Rut 1:7 «la tierra de Judá». OpenBible no "
                 "la registra como lugar: OpenBible no da identificación con coordenadas. Por ahora solo se marca desde "
                 "Rut; en los libros anteriores «Judá» como territorio no está marcado.")}
JUDA_REFS = [((1, 1), "Beth-lehem de "), ((1, 2), "Beth-lehem de "), ((1, 7), "la tierra de ")]
OBLIGATORIOS_LUGAR = ["belen", "moab", "juda"]


def construir(cx):
    rv, br, errores = cx["rv"], cx["br"], cx["errores"]
    for c, n in enumerate(POR_CAPITULO, 1):
        hay = sum(1 for (cc, _) in rv if cc == c)
        if hay != n:
            errores.append(f"Rut {c}: la RV1909 tiene {hay} versículos (numeración inglesa/hebrea: {n})")
        if sum(1 for (cc, _) in br if cc == c) != n:
            errores.append(f"Rut {c}: Brenton no tiene {n} versículos")
    for ref, ini in VERSIFICACION:
        if not rv.get(ref, "").startswith(ini):
            errores.append(f"Versificación de Rut {ref[0]}:{ref[1]}: la RV1909 no empieza «{ini}»")
    for ref, frag in VERSIFICACION_LXX:
        if frag not in br.get(ref, ""):
            errores.append(f"Brenton Rut {ref[0]}:{ref[1]} no dice «{frag}»")
    for es, en in PARALELOS:
        a = {k for k, v in rv.items() if re.search(r"(?<!\w)%s(?!\w)" % re.escape(es), v)}
        b = {k for k, v in br.items() if re.search(r"(?<!\w)%s" % re.escape(en), v)}
        if a != b or not a:
            errores.append(f"Versificación de Rut: «{es}» (RV1909) y «{en}» (Brenton) no caen en los mismos versículos: "
                           f"solo RV {sorted(a - b)}, solo LXX {sorted(b - a)}")
    for k in sorted(rv):
        if k in br and br[k] and not PROPORCION[0] <= len(rv[k]) / len(br[k]) <= PROPORCION[1]:
            errores.append(f"Versificación de Rut {k[0]}:{k[1]}: longitud RV1909/Brenton fuera de rango "
                           f"({len(rv[k])}/{len(br[k])})")
    for ref, frag in CITAS_RESUMEN:
        if frag not in rv.get(ref, ""):
            errores.append(f"Resumen de pasaje: «{frag}» no está en Rut {ref[0]}:{ref[1]}")
    res = exodo.construir(cx, sys.modules[__name__])
    for x in res["relaciones"]:
        if (x["de"], x["a"], x["tipo"]) in INFERIDAS:
            x["certeza"] = "inferido"
    faltan = INFERIDAS - {(x["de"], x["a"], x["tipo"]) for x in res["relaciones"]}
    if faltan:
        errores.append(f"Rut: relaciones inferidas sin crear {sorted(faltan)}")
    return res


def construir_lugares(rv, menciones_personas, rutas, lugares_previos, errores, avisos, sa):
    nuevos, menciones, info = exodo.construir_lugares(rv, menciones_personas, rutas, lugares_previos, errores, avisos,
                                                      sa, sys.modules[__name__])
    if any(l["id"] == JUDA["id"] for l in lugares_previos + nuevos):
        errores.append("Rut: el lugar «juda» ya existe")
        return nuevos, menciones, info
    ocupado = {(m["ref"], m["inicio"]) for m in menciones_personas}
    refs = []
    for ref, antes in JUDA_REFS:
        t, R = rv.get(ref, ""), f"{LIBRO} {ref[0]}:{ref[1]}"
        i = t.find(antes + "Judá")
        if i < 0:
            errores.append(f"Rut: «{antes}Judá» no está en {R}")
            continue
        a = exodo._u16(t, i + len(antes))
        if (R, a) in ocupado:
            errores.append(f"Rut: «Judá» de {R} ya está marcado como persona")
            continue
        menciones.append({"ref": R, "lugar": JUDA["id"], "inicio": a, "fin": a + len("Judá")})
        refs.append(R)
    nuevos.append(dict(JUDA, refs=refs))
    menciones.sort(key=lambda x: (exodo.parse_ref(x["ref"]), x["inicio"]))
    return nuevos, menciones, info


# ---------------------------------------------------------------- hechos obligatorios (sobre los datos finales)
def comprobar(datos, errores):
    """Comprueba los hechos pedidos para Rut (falla si falta alguno). Devuelve líneas de informe."""
    P = {p["id"]: p for p in datos["personas"]}
    R = {(x["de"], x["a"], x["tipo"]): x for x in datos["relaciones"]}
    L = {l["id"]: l for l in datos["lugares"]}
    caps = [c for c in datos["capitulos"] if c["libro"] == LIBRO]
    texto = {f"{LIBRO} {c['cap']}:{v['n']}": v["texto"] for c in caps for v in c["versiculos"]}
    M = {(m["ref"], m["persona"]) for m in datos["menciones"]}
    ML = {(m["ref"], m["lugar"]) for m in datos["menciones_lugar"]}
    lineas = []

    def ok_(cond, desc):
        lineas.append(f"{'OK ' if cond else 'FALTA'} {desc}")
        if not cond:
            errores.append(f"Hecho obligatorio (Rut): {desc}")

    def tiene(pid, ref, mencion=True):
        return ref in P.get(pid, {}).get("refs", []) and (not mencion or (ref, pid) in M)

    def rel(de, a, tipo, ref, certeza="explicito"):
        if tipo == "conyuge":
            de, a = sorted((de, a))
        x = R.get((de, a, tipo))
        return bool(x) and x["certeza"] == certeza and (
            x["ref"] == ref and x.get("cita") and x["cita"] in texto.get(ref, "") or f"{ref}:" in x["nota"])

    ok_(len(caps) == CAPITULOS and len(texto) == VERSICULOS and [len(c["versiculos"]) for c in caps] == POR_CAPITULO,
        f"{CAPITULOS} capítulos y {VERSICULOS} versículos (hay {len(caps)} y {len(texto)})")
    ok_(not [r for r, t in texto.items() if not t], "ningún versículo vacío")
    ok_(tiene("Elimelech_1", "Rut 1:2") and tiene("Elimelech_1", "Rut 1:3") and rel("Elimelech_1", "Naomi_1", "conyuge", "Rut 1:3"),
        "Elimelec, marido de Noemí (Rut 1:2-3)")
    ok_(all(rel("Elimelech_1", h, "padre", "Rut 1:2") and tiene(h, "Rut 1:2") for h in ("Mahlon_1", "Chilion_1")),
        "Mahlón y Quelión, hijos de Elimelec (Rut 1:2)")
    ok_(tiene("Ruth_1", "Rut 1:4") and tiene("Ruth_1", "Rut 1:22") and "moabita" in P["Ruth_1"]["rol"]
        and "Ruth Moabita" in texto.get("Rut 1:22", ""), "Rut, la moabita (Rut 1:4, 1:22)")
    ok_(tiene("Orpah_1", "Rut 1:4") and rel("Chilion_1", "Orpah_1", "conyuge", "Rut 1:4", "inferido"),
        "Orfa (Rut 1:4), mujer de Quelión inferida")
    ok_(tiene("Boaz_1", "Rut 2:1") and "pariente de Elimelec" in P["Boaz_1"]["rol"], "Booz, pariente de Elimelec (Rut 2:1)")
    ok_(tiene("Obed_1", "Rut 4:17") and tiene("Obed_1", "Rut 4:21") and rel("Boaz_1", "Obed_1", "padre", "Rut 4:21")
        and rel("Ruth_1", "Obed_1", "madre", "Rut 4:13") and rel("Boaz_1", "Ruth_1", "conyuge", "Rut 4:13"),
        "Obed, hijo de Booz y Rut (Rut 4:13, 4:17, 4:21)")
    ok_(tiene("Jesse_1", "Rut 4:17") and tiene("Jesse_1", "Rut 4:22") and rel("Jesse_1", "David_1", "padre", "Rut 4:17")
        and rel("Obed_1", "Jesse_1", "padre", "Rut 4:17"), "Isaí, padre de David (Rut 4:17, 4:22)")
    cadena = [("Perez_1", "Hezron_2", "Rut 4:18"), ("Hezron_2", "Ram_1", "Rut 4:19"), ("Ram_1", "Amminadab_1", "Rut 4:19"),
              ("Amminadab_1", "Nahshon_1", "Rut 4:20"), ("Nahshon_1", "Salmon_1", "Rut 4:20"),
              ("Salmon_1", "Boaz_1", "Rut 4:21"), ("Boaz_1", "Obed_1", "Rut 4:21"), ("Obed_1", "Jesse_1", "Rut 4:22"),
              ("Jesse_1", "David_1", "Rut 4:22")]
    previos = {"Perez_1": "Gn 38:29", "Hezron_2": "Gn 46:12", "Amminadab_1": "Nm 1:7", "Nahshon_1": "Nm 1:7"}
    ok_(all(rel(de, a, "padre", r) or rel(de, a, "padre", "Rut 4:17") for de, a, r in cadena)
        and all(tiene(de, r) for de, _, r in cadena) and all(g in P[p]["refs"] for p, g in previos.items()),
        "genealogía de Rut 4:18-22 de Fares a David, con Fares, Hezrón, Aminadab y Naasón de Gn/Nm (mismo id)")
    ok_("Nahasón" in P["Nahshon_1"]["formas_rv1909"] and "Naasón" in P["Nahshon_1"]["formas_rv1909"],
        "Naasón: la RV1909 escribe «Nahasón» en Rut 4:20 (misma persona)")
    ok_(P.get(PARIENTE, {}).get("sin_nombre") and P[PARIENTE]["nombre_rv1909"] is None and "Rut 4:6" in P[PARIENTE]["refs"],
        "el pariente más cercano (Rut 3:12; 4:1-8) sin nombre")
    ok_(not [p for p in EXCLUIR if any(r.startswith("Rut ") for r in P.get(p, {}).get("refs", []))]
        and not any(r.startswith("Rut ") for r in P.get("Moab_1", {}).get("refs", [])),
        "sin personas para Dios, «NA» ni Moab (gentilicio «Moabita»)")
    for lid in OBLIGATORIOS_LUGAR:
        l = L.get(lid)
        ok_(bool(l) and any(r.startswith("Rut ") and (r, lid) in ML for r in l["refs"]),
            f"lugar {lid} con refs de Rut ({sum(1 for r in l['refs'] if r.startswith('Rut ')) if l else 0})")
    ok_(not any(r.startswith("Rut ") for r in L.get("campos-de-moab", {}).get("refs", []))
        and ("Rut 4:12", "Judah_1") in M and ("Rut 4:12", "juda") not in ML,
        "«campos de Moab» = Moab (no los llanos de Nm 22:1); Judá en Rut 4:12 es la persona")
    pas = [p for p in datos["pasajes"] if p["libro"] == LIBRO]
    ok_(len(pas) == len(PASAJES) and pas[0]["inicio"] == "Rut 1:1" and pas[-1]["fin"] == "Rut 4:22",
        f"{len(pas)} pasajes rut-NN de Rut 1:1 a Rut 4:22")
    ok_(len({p["seccion"] for p in pas}) == 4, "4 secciones")
    ids = [p["id"] for p in datos["pasajes"]]
    ult_jue = max(i for i, p in enumerate(datos["pasajes"]) if p["libro"] == "Jue")
    ok_(ids.index(pas[0]["id"]) == ult_jue + 1 and [l["id"] for l in datos["libros"]].index(LIBRO) == [l["id"] for l in datos["libros"]].index("Jue") + 1,
        "Rut va justo después de Jueces en el orden de los pasajes (lectura en orden)")
    return lineas
