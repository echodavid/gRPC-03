Universidad Veracruzana
Facultad de Negocios y Tecnologías
Ingeniería de Software
Guía sugerida de métricas para un
juego de memoria distribuido
Construcción de un dataset para el entrenamiento de modelos de
machine learning
Documento de apoyo académico
Experiencia educativa: Desarrollo de Sistemas en Red
Autor: Ph.D.(c) Jorge Ernesto González Díaz
Fecha: 20 de abril de 2026
Desarrollo de Sistemas en Red Ingeniería de Software
Índice
1. Introducción 3
2. Propósito de las métricas 3
3. Criterios para la selección de métricas 4
4. Convención de nombres 4
5. Niveles de captura de datos 4
5.1. Nivel de evento . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
5.2. Nivel de ronda . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
5.3. Nivel de sesión e historial . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
6. Bloques de métricas sugeridas 5
6.1. Métricas de identificación y contexto . . . . . . . . . . . . . . . . . . . . . . 5
6.2. Métricas temporales . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
6.3. Métricas de resultado y eficiencia . . . . . . . . . . . . . . . . . . . . . . . . 6
6.4. Métricas secuenciales . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
6.5. Métricas de recuerdo en contexto de juego . . . . . . . . . . . . . . . . . . . 8
6.6. Métricas de progreso . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
6.7. Métricas de apoyo . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
6.8. Métricas técnicas . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
7. Relación entre métricas y problemas de machine learning 10
7.1. Predicción del tiempo de ronda . . . . . . . . . . . . . . . . . . . . . . . . . 10
7.2. Clasificación del desempeño . . . . . . . . . . . . . . . . . . . . . . . . . . . 11
7.3. Predicción del siguiente error . . . . . . . . . . . . . . . . . . . . . . . . . . 11
7.4. Predicción de mejora entre sesiones . . . . . . . . . . . . . . . . . . . . . . . 11
Ph.D.(c) Jorge Ernesto González Díaz 1 de 15
Desarrollo de Sistemas en Red Ingeniería de Software
7.5. Predicción de necesidad de apoyo . . . . . . . . . . . . . . . . . . . . . . . . 11
8. Ejemplo de relación entre variable e interpretación 12
9. Recomendaciones para la construcción del dataset 12
10.Propuesta mínima viable de variables 13
11.Consideraciones metodológicas y éticas 14
12.Conclusiones 14
Apéndice. Diccionario breve de variables 15
Ph.D.(c) Jorge Ernesto González Díaz 2 de 15
Desarrollo de Sistemas en Red Ingeniería de Software
1. Introducción
En el desarrollo de un juego de memoria distribuido, la instrumentación de métricas constituye una decisión metodológica y técnica de primer orden. La captura sistemática de datos
permite que el sistema no se limite a ejecutar una dinámica lúdica, sino que además funcione
como una fuente estructurada de información para análisis cuantitativo, modelado predictivo
y evaluación del comportamiento observable de los jugadores en contextos controlados.
La utilidad de un dataset derivado de este tipo de aplicación depende, en gran medida, de la
pertinencia de las variables registradas. Si el sistema únicamente almacena resultados finales,
como la victoria, la derrota o el tiempo total, el potencial analítico se reduce de forma
considerable. Por el contrario, si se registran eventos finos, tiempos de respuesta, errores,
rachas, apoyos, progresión y condiciones técnicas de ejecución, es posible derivar variables
con mayor capacidad descriptiva y predictiva.
En este documento se presenta una guía sugerida de métricas para un juego de memoria
implementado sobre una arquitectura distribuida. Para cada bloque de métricas se expone
su propósito, su justificación dentro del sistema y la manera en que puede contribuir al entrenamiento de modelos de machine learning. El alcance del documento se mantiene dentro de
un marco académico y técnico; en consecuencia, las métricas aquí planteadas deben interpretarse como indicadores de desempeño observable dentro del juego, y no como instrumentos
de evaluación clínica o psicológica.
2. Propósito de las métricas
La definición de métricas en este tipo de sistema persigue tres finalidades complementarias.
En primer término, permite describir de manera objetiva la interacción de cada jugador con
el tablero y con la dinámica del juego. En segundo término, hace posible la construcción
de un dataset consistente, trazable y reutilizable. Finalmente, habilita el entrenamiento de
modelos de machine learning orientados a estimar resultados como el tiempo de resolución,
la probabilidad de error, la mejora entre sesiones, la estabilidad del desempeño o la necesidad
de apoyo adaptativo.
Desde la perspectiva del modelado, una métrica resulta pertinente cuando representa un
aspecto observable del comportamiento, resume una condición relevante del jugador o constituye una señal útil para inferir estados posteriores. Por ello, la selección de métricas no
debe responder a intuiciones aisladas, sino a una relación explícita entre el dato capturado,
su interpretación y su posible función dentro del proceso de entrenamiento.
Ph.D.(c) Jorge Ernesto González Díaz 3 de 15
Desarrollo de Sistemas en Red Ingeniería de Software
3. Criterios para la selección de métricas
A fin de que una métrica resulte útil tanto para el análisis como para el entrenamiento de
modelos, conviene verificar que cumpla con los siguientes criterios:
1. Debe corresponder a un comportamiento observable dentro del sistema.
2. Debe poder registrarse de manera uniforme en todos los jugadores y sesiones.
3. Debe poseer una interpretación clara y estable.
4. Debe aportar información pertinente para descripción, comparación o predicción.
5. Debe estar temporalmente bien definida.
6. Debe evitar la recolección de información sensible no necesaria.
4. Convención de nombres
Con el propósito de unificar la nomenclatura del documento y facilitar su implementación,
se propone la convención de nombres mostrada en la Tabla 1.
Tabla 1: Convención de nombres de variables
Prefijo Uso
id_ Identificadores, por ejemplo id_jug, id_ses, id_ron.
t_ Tiempos, por ejemplo t_resp_ms, t_ron_ms.
tot_ Totales o conteos, por ejemplo tot_aci, tot_err.
tasa_ Proporciones o tasas, por ejemplo tasa_aci, tasa_err.
idx_ Índices compuestos, por ejemplo idx_exp, idx_efi.
niv_ Nivel o dificultad, por ejemplo niv_dif.
des_ Variables vinculadas con desempeño, por ejemplo
des_pos_ayu.
var_ Variabilidad o dispersión, por ejemplo var_des.
5. Niveles de captura de datos
Para estructurar adecuadamente el dataset, conviene distinguir tres niveles de captura.
Ph.D.(c) Jorge Ernesto González Díaz 4 de 15
Desarrollo de Sistemas en Red Ingeniería de Software
5.1. Nivel de evento
En este nivel se registra cada acción o suceso puntual que ocurre durante la ejecución del
juego, como el inicio de sesión, el volteo de una carta, un acierto, un error o la solicitud de
una ayuda.
5.2. Nivel de ronda
En este nivel se integran los eventos correspondientes a una partida específica. Aquí se derivan
métricas como el tiempo total de la ronda, el número de intentos, la precisión, las rachas de
error o la eficiencia general.
5.3. Nivel de sesión e historial
En este nivel se examina el comportamiento del jugador a través de varias rondas o sesiones.
Ello permite modelar progreso, estabilidad, deterioro, variabilidad y adaptación a diferentes
grados de dificultad.
6. Bloques de métricas sugeridas
6.1. Métricas de identificación y contexto
Estas métricas permiten organizar el dataset, enlazar registros y contextualizar adecuadamente cada observación.
Variable Justificación Contribución al entrenamiento Nivel
id_jug Identifica al jugador
sin exponer
información personal
directa.
Permite analizar progresión
individual y definir particiones
adecuadas entre entrenamiento y
prueba.
Sesión /
historial
id_ses Identifica una sesión
completa de juego.
Facilita la agrupación de eventos y
la construcción de variables
derivadas por sesión.
Evento /
sesión
id_ron Identifica una ronda
específica.
Permite construir muestras por
partida para tareas de regresión o
clasificación.
Evento /
ronda
niv_dif Registra el nivel de
dificultad asociado a
la ronda.
Ayuda a explicar variaciones en
tiempo, precisión y error conforme
aumenta la complejidad.
Ronda
Ph.D.(c) Jorge Ernesto González Díaz 5 de 15
Desarrollo de Sistemas en Red Ingeniería de Software
Variable Justificación Contribución al entrenamiento Nivel
tam_tab Registra el tamaño del
tablero o el número
total de cartas.
Permite modelar el efecto del
tamaño del problema sobre el
desempeño observado.
Ronda
ver_cli Registra la versión del
cliente utilizada.
Permite distinguir cambios de
comportamiento asociados al
software y no al jugador.
Sesión
6.2. Métricas temporales
Las métricas temporales son fundamentales porque describen ritmo de interacción, vacilación,
carga de trabajo y continuidad operativa.
Variable Justificación Contribución al entrenamiento Nivel
t_resp_ms Mide el intervalo entre
una acción y la
siguiente decisión
relevante.
Permite modelar fluidez, vacilación
y probabilidad de error.
Evento
t_ron_ms Mide el tiempo total
requerido para
completar una ronda.
Puede utilizarse como variable
objetivo en problemas de regresión.
Ronda
t_par_ms Mide el tiempo
transcurrido entre
observar una carta y
completar
correctamente su par.
Aporta una medida operativa del
recuerdo dentro del contexto del
tablero.
Evento
derivado
t_pau_ms Cuantifica la duración
acumulada de pausas
durante la sesión.
Permite detectar interrupciones y
pérdida de continuidad en la
ejecución.
Sesión
t_ult_ses_h Mide el tiempo
transcurrido desde la
sesión previa.
Es útil para modelar deterioro o
pérdida de fluidez entre sesiones.
Historial
6.3. Métricas de resultado y eficiencia
Estas métricas sintetizan el resultado observable del juego y constituyen una base mínima
para el modelado predictivo.
Ph.D.(c) Jorge Ernesto González Díaz 6 de 15
Desarrollo de Sistemas en Red Ingeniería de Software
Variable Justificación Contribución al entrenamiento Nivel
tot_aci Cuenta los pares
resueltos
correctamente.
Resume el avance efectivo del
jugador dentro de la ronda.
Ronda
tot_err Cuenta los intentos
fallidos.
Ayuda a caracterizar dificultad,
interferencia o estrategia
ineficiente.
Ronda
tasa_aci Mide la proporción de
aciertos respecto al
total de intentos.
Permite comparar jugadores más
allá del tiempo total de resolución.
Ronda
tasa_err Mide la proporción de
errores respecto al
total de intentos.
Es una variable útil para clasificar
desempeño o estimar necesidad de
apoyo.
Ronda
idx_efi Resume de forma
compuesta la
eficiencia con la que se
resolvió el tablero.
Ayuda a construir etiquetas de
desempeño global.
Ronda
derivada
tasa_aci_1 Mide cuántos pares se
resolvieron sin error
previo.
Refleja precisión temprana y
calidad de codificación inicial de
posiciones.
Ronda
derivada
6.4. Métricas secuenciales
Estas métricas permiten describir la trayectoria del jugador durante la partida y no únicamente su resultado final.
Variable Justificación Contribución al entrenamiento Nivel
racha_aci Mide la longitud de
secuencias de aciertos
consecutivos.
Permite detectar consolidación
operativa y estabilidad
momentánea del desempeño.
Evento /
ronda
racha_err Mide la longitud de
secuencias de errores
consecutivos.
Permite identificar bloqueo
temporal, frustración o deterioro
local del rendimiento.
Evento /
ronda
rep_car Mide la frecuencia con
la que se repiten
cartas ya observadas
sin éxito.
Distingue entre exploración
productiva y repetición ineficiente.
Ronda
derivada
idx_exp Mide el grado de
exploración de cartas
nuevas antes de
repetir selecciones.
Aporta información sobre la
estrategia de búsqueda empleada
por el jugador.
Ronda
derivada
Ph.D.(c) Jorge Ernesto González Díaz 7 de 15
Desarrollo de Sistemas en Red Ingeniería de Software
Variable Justificación Contribución al entrenamiento Nivel
t_rec_err_ms Mide el tiempo
necesario para volver a
acertar después de un
error.
Permite modelar la capacidad de
recuperación operativa dentro de
la ronda.
Ronda
derivada
pat_rev Resume el patrón
espacial de revisita de
posiciones del tablero.
Puede aportar señales útiles en
modelos secuenciales o de
estrategia espacial.
Evento
derivado
6.5. Métricas de recuerdo en contexto de juego
Estas métricas describen la recuperación de información dentro del tablero. Su interpretación
debe mantenerse circunscrita al entorno del juego.
Variable Justificación Contribución al entrenamiento Nivel
rec_par Mide la proporción de
veces que el jugador
identifica
correctamente el par
de una carta ya
observada.
Puede funcionar como predictor
fuerte del desempeño posterior.
Ronda
derivada
dem_mem_ms Mide el tiempo entre
la primera observación
de una carta y el
acierto de su par.
Resume la eficiencia de
recuperación en el corto plazo.
Evento
derivado
int_ant_par Cuenta cuántas cartas
irrelevantes median
antes de completar un
par.
Ayuda a modelar resistencia a la
interferencia dentro de la dinámica
del juego.
Evento
derivado
fall_par_rep Cuenta fallos
repetidos sobre pares
previamente
observados.
Señala dificultad para consolidar
información ya disponible.
Ronda
derivada
tol_tab Mide la estabilidad de
la precisión conforme
aumenta el tamaño
del tablero.
Permite estimar robustez del
desempeño ante mayor
complejidad.
Historial
Ph.D.(c) Jorge Ernesto González Díaz 8 de 15
Desarrollo de Sistemas en Red Ingeniería de Software
6.6. Métricas de progreso
Estas métricas permiten examinar la evolución del jugador a lo largo del tiempo.
Variable Justificación Contribución al entrenamiento Nivel
gan_ses Mide la mejora entre
las primeras y las
últimas rondas de una
sesión.
Permite estimar adaptación
inmediata durante una misma
ejecución.
Sesión
derivada
ten_des Resume la tendencia
general del desempeño
a través de sesiones
sucesivas.
Ayuda a modelar progreso
longitudinal.
Historial
caida_olv Mide la disminución
del desempeño
después de un periodo
sin jugar.
Permite estudiar deterioro entre
sesiones.
Historial
derivado
var_des Cuantifica la
estabilidad o
inestabilidad del
desempeño.
Permite identificar perfiles
consistentes o erráticos.
Sesión /
historial
adap_dif Mide la rapidez con la
que el jugador
conserva buen
desempeño al
aumentar la dificultad.
Aporta información útil para
sistemas de adaptación dinámica.
Historial
6.7. Métricas de apoyo
Si el juego incorpora ayudas, pistas o mecanismos de asistencia, estas variables deben registrarse porque modifican la interpretación del desempeño observado.
Variable Justificación Contribución al entrenamiento Nivel
tot_ayu Cuenta cuántas
ayudas utilizó el
jugador durante la
ronda.
Permite ajustar el análisis del
desempeño en función de la
dependencia de apoyo.
Ronda
mom_ayu Indica en qué
momento de la ronda
se solicitó la ayuda.
Aporta información sobre el punto
en el que emerge la dificultad.
Evento
derivado
Ph.D.(c) Jorge Ernesto González Díaz 9 de 15
Desarrollo de Sistemas en Red Ingeniería de Software
Variable Justificación Contribución al entrenamiento Nivel
des_pos_ayu Mide el desempeño
posterior a la
utilización de una
ayuda.
Permite valorar si la asistencia
mejora el rendimiento o solo
posterga el error.
Ronda
derivada
6.8. Métricas técnicas
En un sistema distribuido, las condiciones de infraestructura también influyen sobre los datos.
Por ello deben registrarse como variables de control y depuración.
Variable Justificación Contribución al entrenamiento Nivel
lat_red_ms Mide la latencia de
comunicación entre
cliente y servidor.
Permite separar demoras técnicas
de demoras atribuibles al jugador.
Evento /
sesión
tasa_fal Registra la proporción
de fallos de
comunicación.
Ayuda a depurar el dataset y a
descartar registros de baja
confiabilidad.
Sesión
des_sin Cuenta eventos de
desincronización entre
cliente y servidor.
Evita entrenar modelos con
observaciones potencialmente
corruptas.
Evento /
sesión
t_srv_ms Mide el tiempo de
procesamiento en el
servidor.
Permite controlar retrasos que no
dependen del usuario.
Evento
7. Relación entre métricas y problemas de machine learning
Una vez definidas las métricas, es necesario establecer con precisión qué resultado se desea
estimar. Sin una variable objetivo claramente delimitada, el dataset pierde coherencia y
utilidad analítica.
7.1. Predicción del tiempo de ronda
En este caso, la variable objetivo puede ser t_ron_ms. Como variables predictoras conviene
considerar niv_dif, tam_tab, t_resp_ms, tasa_err, racha_err y tot_ayu. Este problema
puede abordarse como una tarea de regresión.
Ph.D.(c) Jorge Ernesto González Díaz 10 de 15
Desarrollo de Sistemas en Red Ingeniería de Software
7.2. Clasificación del desempeño
Es posible construir una etiqueta de desempeño bajo, medio o alto combinando t_ron_ms,
tasa_aci e idx_efi. A partir de ello, el problema puede tratarse como clasificación multiclase.
7.3. Predicción del siguiente error
La probabilidad de que el siguiente intento resulte erróneo puede estimarse con variables
como racha_err, t_resp_ms, rep_car, idx_exp y t_rec_err_ms. Esta formulación resulta
útil para sistemas que deseen adaptar ayudas en tiempo real.
7.4. Predicción de mejora entre sesiones
La variable objetivo puede definirse como el cambio porcentual de desempeño entre la sesión
actual y la siguiente. Para ello, resultan especialmente útiles gan_ses, ten_des, caida_olv,
var_des y adap_dif.
7.5. Predicción de necesidad de apoyo
Si se desea decidir de manera automática cuándo ofrecer una pista o asistencia, puede entrenarse un modelo que estime bloqueo o deterioro del desempeño. En ese caso, variables como
racha_err, tasa_err, t_resp_ms y des_pos_ayu resultan particularmente relevantes.
Ph.D.(c) Jorge Ernesto González Díaz 11 de 15
Desarrollo de Sistemas en Red Ingeniería de Software
8. Ejemplo de relación entre variable e interpretación
Tabla 10: Relación sugerida entre variables e interpretación
Variable Interpretación Uso sugerido en machine
learning
t_ron_ms Velocidad global de
resolución
Variable objetivo en tareas de
regresión
tasa_aci Calidad general del
desempeño
Predictor o componente para
construir etiquetas
racha_err Señal de bloqueo
temporal
Predictor para apoyo adaptativo
rec_par Eficiencia de recuerdo
dentro del tablero
Predictor del desempeño futuro
gan_ses Adaptación dentro de
una misma sesión
Predictor de progreso
caida_olv Pérdida de desempeño
entre sesiones
Variable objetivo o predictor
longitudinal
lat_red_ms Influencia técnica
externa
Variable de control para
limpieza del dataset
9. Recomendaciones para la construcción del dataset
Para que las métricas descritas puedan utilizarse de forma adecuada, conviene atender las
siguientes recomendaciones metodológicas:
1. Registrar inicialmente los eventos crudos y derivar posteriormente las variables agregadas.
2. Asociar cada evento con una marca de tiempo consistente y verificable.
3. Separar los identificadores técnicos de cualquier dato personal del jugador.
4. Mantener la misma semántica para cada variable en todas las tablas y servicios.
5. Evitar fugas de información. Si se pretende predecir un evento futuro, no deben utilizarse como entrada variables que solo son conocidas al final de la ronda.
Ph.D.(c) Jorge Ernesto González Díaz 12 de 15
Desarrollo de Sistemas en Red Ingeniería de Software
6. Controlar la calidad de los datos técnicos, especialmente latencia, pérdidas y desincronización.
7. Documentar formalmente la definición de cada variable en un diccionario de datos.
10. Propuesta mínima viable de variables
Si el equipo desea comenzar con una instrumentación manejable, se recomienda registrar al
menos las siguientes variables:
1. id_jug
2. id_ses
3. id_ron
4. niv_dif
5. tam_tab
6. t_resp_ms
7. t_ron_ms
8. tot_aci
9. tot_err
10. tasa_aci
11. racha_err
12. racha_aci
13. rec_par
14. tot_ayu
15. lat_red_ms
Este conjunto resulta suficiente para construir un primer dataset funcional, generar tablas
derivadas y entrenar modelos básicos de regresión o clasificación.
Ph.D.(c) Jorge Ernesto González Díaz 13 de 15
Desarrollo de Sistemas en Red Ingeniería de Software
11. Consideraciones metodológicas y éticas
Las métricas propuestas en esta guía deben interpretarse exclusivamente dentro del contexto
del juego. El sistema puede describir desempeño observable, eficiencia de interacción, recuperación ante el error, progresión y estabilidad del comportamiento. Sin embargo, estos registros
no equivalen, por sí mismos, a una evaluación clínica de memoria ni a una medición general
de capacidades cognitivas.
En consecuencia, al documentar el proyecto conviene emplear expresiones como desempeño
en el juego, recuerdo de posiciones en contexto de juego, progreso entre sesiones o estimación
de dificultad. Si en una etapa posterior se pretendiera establecer relación con constructos
cognitivos más amplios, sería indispensable incorporar procedimientos de validación externa
y el marco ético correspondiente.
12. Conclusiones
La definición de métricas en un juego de memoria distribuido constituye una decisión de
arquitectura de datos con implicaciones metodológicas directas. Las variables seleccionadas
condicionan la calidad del dataset, el alcance del análisis y la viabilidad del entrenamiento
de modelos de machine learning.
Cuando las métricas se diseñan con claridad semántica, consistencia temporal y propósito
analítico, el sistema trasciende su función lúdica inmediata y se convierte en una plataforma
para la observación computacional del comportamiento en un entorno controlado. Bajo esta
lógica, los datos permiten describir el desempeño del jugador, estimar tendencias, anticipar
dificultades y sentar bases para mecanismos adaptativos sustentados en evidencia empírica.
En consecuencia, la estrategia más adecuada consiste en registrar eventos finos, derivar indicadores por ronda y sesión, y alinear cada variable con un objetivo específico de análisis o
predicción.
Ph.D.(c) Jorge Ernesto González Díaz 14 de 15
Desarrollo de Sistemas en Red Ingeniería de Software
Apéndice. Diccionario breve de variables
Tabla 11: Diccionario breve de variables
Variable Tipo sugerido Descripción
id_jug UUID /
VARCHAR
Identificador anónimo del jugador.
id_ses UUID /
VARCHAR
Identificador único de la sesión.
id_ron UUID /
VARCHAR
Identificador único de la ronda.
niv_dif INT Nivel de dificultad asociado a la ronda.
tam_tab INT Número total de cartas o tamaño del
tablero.
t_resp_ms BIGINT Tiempo de respuesta medido en
milisegundos.
t_ron_ms BIGINT Tiempo total requerido para completar la
ronda.
tot_aci INT Total de aciertos en la ronda.
tot_err INT Total de errores en la ronda.
tasa_aci DECIMAL Proporción de aciertos respecto al total
de intentos.
racha_err INT Número máximo de errores consecutivos.
racha_aci INT Número máximo de aciertos consecutivos.
rec_par DECIMAL Proporción de recuperación correcta de
pares previamente observados.
tot_ayu INT Número total de ayudas utilizadas.
lat_red_ms FLOAT Latencia de comunicación entre cliente y
servidor en milisegundos.
Ph.D.(c) Jorge Ernesto González Díaz 15 de 15