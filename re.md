A10 - Juego de Memoria Distribuido con gRPC

10 de 11

Descripción
Entrega
Actividad
A10 - Juego de Memoria Distribuido con gRPC

Detalle
Inicia:

20/abr/2026 - 00:00 hrs

Termina:

27/abr/2026 - 23:45 hrs

Valor:

10

Prerrequisitos

---

Descripción
Objetivo del proyecto
Desarrollar un juego de memoria distribuido, donde múltiples jugadores se conecten desde distintos equipos a un servidor central que coordina el estado del juego, usando gRPC como protocolo de comunicación. El juego se puede ejecutar en una red LAN, y los mensajes deben viajar entre cliente y servidor de forma estructurada.



Objetivos de aprendizaje
Al finalizar esta práctica, el estudiante será capaz de:

Comprender y aplicar el modelo de comunicación cliente-servidor mediante el uso de gRPC en un entorno distribuido.

Diseñar e implementar servicios gRPC personalizados, definiendo los mensajes y servicios necesarios para coordinar la lógica de un juego de memoria multijugador.

Sincronizar el estado compartido del juego entre múltiples clientes conectados al servidor, utilizando streams de respuesta para manejar actualizaciones en tiempo real.

Gestionar correctamente la concurrencia y los turnos de juego, aplicando mecanismos de control como semáforos o bloqueos (locks).

Orquestar la ejecución de servicios distribuidos mediante contenedores Docker, configurados para funcionar en una red local (LAN).

Integrar elementos de lógica de juego y visualización simple en consola, demostrando el funcionamiento del sistema en red desde distintas máquinas o contenedores.

Documentar adecuadamente el diseño y comportamiento del sistema distribuido, incluyendo bitácora de desarrollo y reflexiones técnicas.


¿Cómo funciona un juego de memoria?
El juego clásico de memoria (Memory Match o Concentration) consiste en:

Un tablero con cartas volteadas.

Cada jugador, en su turno, elige dos cartas para voltearlas.

Si hacen pareja, permanecen abiertas.

Si no hacen pareja, se vuelven a cerrar.

El juego continúa hasta que todas las parejas estén encontradas.



Componentes del sistema distribuido

1. Servidor gRPC
Responsable de:

Configurar los parámetros de la partida: tamaño del tablero (minimo 4 x 4), numero de jugadores, figuras en el tablero.

Registrar jugadores al inicio del juego.

Inicializar el tablero y barajar las cartas.

Mantener el estado global del juego (cartas abiertas, parejas encontradas, turnos).

Validar los turnos y verificar coincidencias.

Notificar a todos los clientes cuando el estado cambia mediante streams.

Notificar a todos los clientes del estado actualizado del juego 

Llevar un registro de los movimientos por jugador, los puntajes obtenidos y el tiempo de respuesta de cada jugador (tiempo que le lleva hacer la elección de la pareja de cartas a partir de que es su turno en la partida)

Detectar el fin del juego.

Mostrar estadísticas de desempeño de la partida por cada jugador. (en formato tabular, opcional gráficas con matplotlib)

El servidor corre un servicio gRPC con métodos como: JoinGame, PlayTurn, GetBoardState, SubscribeToUpdates. Entre otros.


Detalles técnicos sugeridos:
Usa threading.Lock() para proteger operaciones concurrentes.

Implementa SubscribeToUpdates como un método de streaming para notificar en tiempo real.

Puedes usar uuid para asignar identificadores únicos a cada jugador.

El servidor debe contar un una colección de figuras que puedan mostrarse en parejas en el tablero, defina el tamaño máximo del tablero de 8 x 8.



2. Clientes gRPC
Cada cliente:

Se conecta al servidor y se registra con un nombre de jugador.

Envía acciones (e.g. “quiero voltear la carta en la posición X”,).

Recibe actualizaciones del estado del tablero. No debe hacer polling, las actualizaciones deben enviarse con cada cambio de estado del tablero.

Muestra el tablero: 

Modo consola: una matriz definida previamente en la configuración de la partida, dentro de cada matriz se pueden mostrar emojis que representan las cartas.  ("🍓", "🐶", "🍇", etc.).

GUI: use algún componente como cards para mostrar iconos que simulen las cartas.

Mantiene una conexión activa para enviar su jugada y recibir actualizaciones del servidor.

Permitir al usuario seleccionar dos cartas por turno.

Esperar el turno correspondiente para jugar.

Mostrar actualizaciones del juego en línea.



 Detalles técnicos sugeridos
Las jugadas deben validarse localmente (¿es mi turno?, ¿posición válida?, etc.) antes de enviarlas.

Usa hilos (threading.Thread) para manejar listen_updates en paralelo al input del usuario.

El método get_public_view() devuelve una vista del tablero con cartas ocultas excepto las reveladas o emparejadas.

El servidor usará esta clase para enviar estados actualizados a todos los clientes.


Flujo de ejecución esperado
Servidor inicia y espera conexiones.

Cliente A se conecta → recibe ID.

Cliente B se conecta → recibe ID.

Turno de A: selecciona dos posiciones → servidor responde si son pareja.

Todos los clientes reciben la nueva vista del tablero.

Turno de B...

El juego termina cuando todas las cartas están emparejadas.



 Recomendaciones generales
Usa protobuf para definir claramente los mensajes y servicios.

Divide la lógica en capas: conexión gRPC, lógica del juego, representación del tablero.

Mantén registros de eventos (e.g. quién encontró qué pareja) para análisis.

Usa docker-compose para facilitar pruebas en red LAN con múltiples contenedores.



Checklist de Verificación para la Práctica
Los siguientes puntos deben ser revisados y marcados por el equipo antes de entregar el proyecto. Se recomienda usar este checklist durante las pruebas finales.

 1. Configuración y arquitectura general
#	Ítem	Verificado (✓)
1.1	Se creó y compiló correctamente el archivo .proto con definición de servicios y mensajes.	☐
1.2	El servidor inicia correctamente y está preparado para recibir múltiples conexiones.	☐
1.3	El cliente puede conectarse al servidor desde otra máquina o contenedor en red LAN.	☐
1.4	Se utilizó docker-compose para levantar todos los servicios en contenedores.	☐
1.5	Se definió una red Docker compartida para comunicar contenedores.	☐
 2. Funcionalidad del servidor
#	Ítem	Verificado (✓)
2.1	El servidor asigna un identificador único a cada cliente que se conecta.	☐
2.2	El servidor mantiene el estado global del tablero (cartas reveladas y emparejadas).	☐
2.3	El servidor controla correctamente el turno de cada jugador.	☐
2.4	El servidor valida las jugadas (par válido, coordenadas correctas).	☐
2.5	El servidor envía actualizaciones del tablero a todos los clientes conectados.	☐
2.6	El servidor detecta el final del juego y lo notifica a los jugadores.	☐
2.7
El servidor lleva un registro de la puntuación, tiempos de respuesta y desempeño de cada jugador por partida
☐
 3. Funcionalidad del cliente
#	Ítem	Verificado (✓)
3.1	El cliente solicita unirse al juego con un nombre y recibe un ID.	☐
3.2	El cliente muestra el tablero en consola de forma legible.	☐
3.3	El cliente permite al usuario seleccionar dos cartas por turno.	☐
3.4	El cliente valida localmente si es su turno antes de enviar jugada.	☐
3.5	El cliente actualiza el tablero al recibir notificaciones del servidor.	☐
3.6	El cliente muestra mensajes adecuados (inicio, turno, errores, fin del juego).	☐
4. Lógica del tablero
#	Ítem	Verificado (✓)
4.1	El tablero se genera con pares barajados al azar.	☐
4.2	El estado del tablero se actualiza correctamente al encontrar una pareja.	☐
4.3	Se diferencian visualmente las cartas ocultas, reveladas y emparejadas.	☐
4.4	Se respetan las reglas del juego de memoria (dos cartas por turno).	☐
5. Documentación y entrega
#	Ítem	Verificado (✓)
5.1	Se incluye el reporte de la practica en un archivo .PDF.	☐
5.2	Se documenta el código con comentarios descriptivos.	☐
5.3	Se describe la arquitectura de la solución y las partes que la componen.	☐
5.4	Se explican las partes mas relevantes de la solución (algoritmos, clases, componentes).	☐
5.5	Se incluyen capturas de pantalla del juego funcionando con múltiples clientes.	☐
6. Validación final (mínimo indispensable)
#	Ítem	Verificado (✓)
6.1	Al menos 3 clientes pueden jugar correctamente desde equipos distintos.	☐
6.2	El flujo de turnos es respetado por todos los clientes.	☐
6.3	El juego finaliza correctamente cuando se emparejan todas las cartas.	☐
6.4	Se registran correctamente las métricas de desempeño de cada uno de los jugadores	☐
6.5
Es posible consultar los datos de partidas almacenadas en el servidor.
☐




Rubrica de evaluación


Categoría	Puntos Máximos	Excelente	Bueno	Aceptable	Deficiente 
1. Funcionamiento del servidor	70 pts	El servidor ejecuta sin errores, gestiona múltiples jugadores, controla turnos y actualiza el estado global.
70 pts.
Funciona en general, pero presenta leves errores en validación de turnos o estado global.
50 pts.
Tiene fallos en turnos o actualizaciones que afectan la experiencia de juego.
30 pts.
No gestiona turnos, presenta errores críticos o no se ejecuta.
0 pts.
2. Interacción y lógica del cliente	60 pts	El cliente permite jugar correctamente, valida turnos, actualiza el tablero y muestra mensajes claros.
60 pts.
Funciona pero con errores menores en visualización o validaciones.
40 pts.
Permite jugar, pero el control de flujo o mensajes es confuso.
20 pts.
No permite jugar adecuadamente, o no se conecta al servidor.
0 pts.
3. Sincronización y comunicación en red	60 pts	Clientes y servidor se comunican correctamente, se usan streams para actualizaciones en tiempo real.
60 pts.
La comunicación es funcional, aunque sin streams o con retrasos leves.
40 pts.
Comunicación parcial o limitada a un solo cliente a la vez.
20 pts.
No hay comunicación funcional entre cliente y servidor.
0 pts.
4. Implementación técnica y calidad del código	50 pts	Código estructurado, con clases bien definidas, modularidad, comentarios y uso correcto de gRPC.
50 pts.
Código funcional pero con oportunidades de mejora en organización o documentación.
30 pts.
Código poco modular, difícil de seguir o con malas prácticas.
10 pts.
Código desorganizado, sin separación de responsabilidades o sin uso claro de gRPC.
0 pts.
5. Documentación y evidencia	60 pts	Incluye README claro, bitácora completa, capturas de pantalla y reflexión final bien elaborada.
60 pts.
Entrega completa pero con documentación parcial o bitácora incompleta.
40 pts.
Entrega incompleta o con documentación mínima.
20 pts.
No hay documentación o evidencia del trabajo realizado.
20 pts.



