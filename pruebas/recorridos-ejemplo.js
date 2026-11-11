/* EJEMPLO — datos de prueba para la vista «Recorridos» (se activan con ?ejemplo si no hay datos/recorridos.js).
   Las coordenadas son APROXIMADAS y SOLO DE PRUEBA: no son una identificación ni una hipótesis publicada.
   Las citas son de la RV1909 (dominio público). El contrato real lo genera herramientas/ en datos/recorridos.js. */
window.BIBLIA_RECORRIDOS = {
  ejemplo: true,
  fuentes: [{ id: 'ejemplo', nombre: 'EJEMPLO: coordenadas aproximadas solo de prueba', url: '' }],
  recorridos: [{
    id: 'exodo',
    titulo: 'Éxodo (EJEMPLO)',
    libro: 'Ex',
    personas: ['Moses_1', 'Aaron_1'],
    resumen: 'EJEMPLO de prueba: seis etapas de la salida de Egipto hasta el Sinaí.',
    hipotesis: [
      { id: 'sur', nombre: 'Ruta del sur (EJEMPLO)', descripcion: 'EJEMPLO: trazado que baja por la costa occidental de la península hacia el sur.', defecto: true, fuente: 'EJEMPLO sin fuente real', url: '' },
      { id: 'norte', nombre: 'Ruta del norte (EJEMPLO)', descripcion: 'EJEMPLO: trazado que cruza cerca de la costa mediterránea.', defecto: false, minoritaria: true, fuente: 'EJEMPLO sin fuente real', url: '' }
    ],
    etapas: [
      { orden: 1, lugar: 'rameses', nombre: 'Ramesés', ref: 'Ex 12:37',
        cita: 'Y partieron los hijos de Israel de Rameses á Succoth, como seiscientos mil hombres de á pie, sin [contar] los niños.',
        tiempo: { texto: 'día 15 del mes primero', dia: 1, certeza: 'texto', pasos: [{ texto: 'EJEMPLO: la fecha de la salida', ref: 'Ex 12:18' }] },
        ubicaciones: { sur: { lat: 30.8, lon: 31.83, confianza: 'alta', identificacion: 'EJEMPLO (cerca de Qantir)', fuente: 'EJEMPLO', url: '' } },
        nota: 'EJEMPLO' },
      { orden: 2, lugar: 'sucot', nombre: 'Sucot', ref: 'Ex 13:20',
        cita: 'Y partidos de Succoth, asentaron campo en Etham, á la entrada del desierto.',
        tiempo: null,
        ubicaciones: { sur: { lat: 30.55, lon: 32.1, confianza: 'media', identificacion: 'EJEMPLO (cerca de Tell el-Maskhuta)', fuente: 'EJEMPLO', url: '' },
          norte: { lat: null, lon: null, confianza: 'baja', identificacion: 'EJEMPLO: esta hipótesis no propone lugar', fuente: 'EJEMPLO', url: '' } },
        nota: '' },
      { orden: 3, lugar: 'pi-hahirot', nombre: 'Pi-hahirot', ref: 'Ex 14:2',
        cita: 'Habla á los hijos de Israel que den la vuelta, y asienten su campo delante de Pihahiroth, entre Migdol y la mar hacia Baalzephón: delante de él asentaréis el campo, junto á la mar.',
        tiempo: null,
        ubicaciones: {
          sur: { lat: 30.0, lon: 32.5, confianza: 'baja', identificacion: 'EJEMPLO (sur del golfo)', fuente: 'EJEMPLO', url: '' },
          norte: { lat: 31.05, lon: 32.75, confianza: 'baja', identificacion: 'EJEMPLO (costa norte)', fuente: 'EJEMPLO', url: '' } },
        nota: '' },
      { orden: 4, lugar: null, nombre: 'Cruce del mar', ref: 'Ex 14:22',
        cita: 'Entonces los hijos de Israel entraron por medio de la mar en seco, teniendo las aguas como muro á su diestra y á su siniestra:',
        tiempo: null,
        ubicaciones: {
          sur: { lat: 29.9, lon: 32.6, confianza: 'baja', identificacion: 'EJEMPLO (golfo de Suez)', fuente: 'EJEMPLO', url: '' },
          norte: { lat: 31.1, lon: 33.05, confianza: 'baja', identificacion: 'EJEMPLO (laguna costera)', fuente: 'EJEMPLO', url: '' } },
        nota: '' },
      { orden: 5, lugar: 'mara', nombre: 'Mara', ref: 'Ex 15:23',
        cita: 'Y llegaron á Mara, y no pudieron beber las aguas de Mara, porque eran amargas; por eso le pusieron el nombre de Mara.',
        tiempo: { texto: 'tres días después del mar', dia: null, certeza: 'calculo', pasos: [{ texto: 'EJEMPLO: «anduvieron tres días por el desierto»', ref: 'Ex 15:22' }] },
        ubicaciones: {
          sur: { lat: 29.35, lon: 32.94, confianza: 'media', identificacion: 'EJEMPLO (Ain Hawara)', fuente: 'EJEMPLO', url: '' },
          norte: { lat: 30.85, lon: 33.6, confianza: 'baja', identificacion: 'EJEMPLO (norte del Sinaí)', fuente: 'EJEMPLO', url: '' } },
        nota: '' },
      { orden: 6, lugar: 'sinai', nombre: 'Monte Sinaí', ref: 'Ex 19:2',
        cita: 'Porque partieron de Rephidim, y llegaron al desierto de Sinaí, y asentaron en el desierto; y acampó allí Israel delante del monte.',
        tiempo: { texto: 'mes tercero de la salida', dia: null, certeza: 'texto', pasos: [{ texto: '«Al mes tercero de la salida»', ref: 'Ex 19:1' }] },
        ubicaciones: {
          sur: { lat: 28.54, lon: 33.97, confianza: 'media', identificacion: 'EJEMPLO (Jebel Musa)', fuente: 'EJEMPLO', url: '' },
          norte: { lat: 30.3, lon: 34.75, confianza: 'baja', identificacion: 'EJEMPLO (Har Karkom)', fuente: 'EJEMPLO', url: '' } },
        nota: '' }
    ]
  }]
};
