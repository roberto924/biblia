/* EJEMPLO DE PRUEBA con el contrato de datos/originales.js y datos/griego-swete.js (se carga con ?ejemplo).
   Textos breves solo para probar la interfaz: no son los datos verificados que generará herramientas/.
   Incluye Gn 31:55 (RV) = Gn 32:1 (hebreo) y la variante 70/75 de Ex 1:5. El video usa un id de prueba. */
(function (g) {
  g.BIBLIA_ORIGINALES = {
    fuentes: [
      { id: 'wlc', nombre: 'Códice de Leningrado (Westminster Leningrad Codex) · EJEMPLO', licencia: 'Dominio público', url: 'https://tanach.us/' }
    ],
    hebreo: {
      'Gn 1:1': { t: 'בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃' },
      'Gn 1:2': { t: 'וְהָאָ֗רֶץ הָיְתָ֥ה תֹ֙הוּ֙ וָבֹ֔הוּ וְחֹ֖שֶׁךְ עַל־פְּנֵ֣י תְה֑וֹם וְר֣וּחַ אֱלֹהִ֔ים מְרַחֶ֖פֶת עַל־פְּנֵ֥י הַמָּֽיִם׃' },
      'Gn 1:3': { t: 'וַיֹּ֥אמֶר אֱלֹהִ֖ים יְהִ֣י א֑וֹר וַֽיְהִי־אֽוֹר׃' },
      'Gn 31:55': { t: 'וַיַּשְׁכֵּם לָבָן בַּבֹּקֶר וַיְנַשֵּׁק לְבָנָיו וְלִבְנוֹתָיו וַיְבָרֶךְ אֶתְהֶם וַיֵּלֶךְ וַיָּשָׁב לָבָן לִמְקֹמוֹ׃', r: 'Gn 32:1' },
      'Ex 1:1': { t: 'וְאֵלֶּה שְׁמוֹת בְּנֵי יִשְׂרָאֵל הַבָּאִים מִצְרָיְמָה אֵת יַעֲקֹב אִישׁ וּבֵיתוֹ בָּאוּ׃' },
      'Ex 1:2': { t: 'רְאוּבֵן שִׁמְעוֹן לֵוִי וִיהוּדָה׃' },
      'Ex 1:3': { t: 'יִשָּׂשכָר זְבוּלֻן וּבִנְיָמִן׃' },
      'Ex 1:4': { t: 'דָּן וְנַפְתָּלִי גָּד וְאָשֵׁר׃' },
      'Ex 1:5': { t: 'וַיְהִי כָּל־נֶפֶשׁ יֹצְאֵי יֶרֶךְ־יַעֲקֹב שִׁבְעִים נָפֶשׁ וְיוֹסֵף הָיָה בְמִצְרָיִם׃' }
    },
    testigos: [
      { id: 'leningrado', nombre: 'Códice de Leningrado (EJEMPLO)', tipo: 'codice', idioma: 'hebreo', fecha: '1008-1009 d. C.', fecha_certeza: 'colofón', contiene: ['Gn 1:1-Mal 4:6'],
        institucion: 'Biblioteca Nacional de Rusia', url: 'https://archive.org/details/Leningrad_Codex', uso: 'solo_enlace', nota: 'Dato de prueba.', fuente: 'ejemplo' },
      { id: '4q13', nombre: '4QExod-b (4Q13) (EJEMPLO)', tipo: 'rollo', idioma: 'hebreo', fecha: 'siglo I a. C. (aprox.)', fecha_certeza: 'aproximada', contiene: ['Ex 1:1-Ex 1:6'],
        institucion: 'Leon Levy Dead Sea Scrolls Digital Library', url: 'https://www.deadseascrolls.org.il/', uso: 'solo_enlace', nota: 'Dato de prueba.', fuente: 'ejemplo' },
      { id: 'samaritano', nombre: 'Pentateuco samaritano (EJEMPLO)', tipo: 'pentateuco_samaritano', idioma: 'hebreo samaritano', fecha: 'sin fecha en el ejemplo', fecha_certeza: '', contiene: ['Gn', 'Ex'],
        institucion: '', url: '', uso: 'solo_enlace', nota: 'Dato de prueba.', fuente: 'ejemplo' }
    ],
    variantes: [
      { ref: 'Ex 1:5', tema: 'Cuántas personas bajaron con Jacob a Egipto', lecturas: [
        { testigos: ['leningrado'], texto_original: 'שִׁבְעִים נָפֶשׁ', traduccion_es: 'setenta personas' },
        { testigos: ['4q13', 'lxx'], texto_original: 'πέντε καὶ ἑβδομήκοντα', traduccion_es: 'setenta y cinco' }
      ], fuente: 'ejemplo', url_fuente: '', nota: 'Dato de prueba: Hch 7:14 también dice setenta y cinco.' }
    ],
    videos: [
      { libro: 'Ex', titulo: 'Éxodo 1-18 (EJEMPLO, id de prueba)', youtube_id: 'aaaaaaaaaaa', idioma: 'es', rango: 'Ex 1-18', fuente: 'Proyecto Biblia', url: 'https://www.youtube.com/@ProyectoBiblia' }
    ]
  };
  g.BIBLIA_GRIEGO = {
    fuente: 'Swete 1930 · EJEMPLO', licencia: 'GPL-3.0', url: 'https://github.com/',
    texto: {
      'Gn 1:1': 'Ἐν ἀρχῇ ἐποίησεν ὁ θεὸς τὸν οὐρανὸν καὶ τὴν γῆν.',
      'Gn 1:2': 'ἡ δὲ γῆ ἦν ἀόρατος καὶ ἀκατασκεύαστος, καὶ σκότος ἐπάνω τῆς ἀβύσσου, καὶ πνεῦμα θεοῦ ἐπεφέρετο ἐπάνω τοῦ ὕδατος.',
      'Gn 1:3': 'καὶ εἶπεν ὁ θεός Γενηθήτω φῶς· καὶ ἐγένετο φῶς.',
      'Ex 1:1': 'Ταῦτα τὰ ὀνόματα τῶν υἱῶν Ἰσραὴλ τῶν εἰσπεπορευμένων εἰς Αἴγυπτον ἅμα Ἰακὼβ τῷ πατρὶ αὐτῶν· ἕκαστος πανοικὶ αὐτῶν εἰσήλθοσαν.',
      'Ex 1:2': 'Ῥουβήν, Συμεών, Λευί, Ἰούδας,',
      'Ex 1:3': 'Ἰσσαχὰρ, Ζαβουλὼν καὶ Βενιαμίν,',
      'Ex 1:4': 'Δὰν καὶ Νεφθαλείμ, Γὰδ καὶ Ἀσήρ.',
      'Ex 1:5': 'Ἰωσὴφ δὲ ἦν ἐν Αἰγύπτῳ. ἦσαν δὲ πᾶσαι ψυχαὶ ἐξ Ἰακὼβ πέντε καὶ ἑβδομήκοντα.'
    }
  };
})(typeof window !== 'undefined' ? window : globalThis);
