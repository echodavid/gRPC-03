# Rúbrica y Evaluación — Práctica 3
## Juego de Memoria Distribuido con gRPC

> Evaluación basada en: checklist oficial (`re.md`), rúbrica de calificación y guía de métricas para ML (`guiaMetricas.md`)
> Fecha: 27 de abril de 2026

---

## 1. Rúbrica oficial — Calificación por categoría

### 1.1 Funcionamiento del servidor (70 pts)

| Nivel | Criterio | Pts |
|-------|----------|-----|
| **Excelente** | El servidor ejecuta sin errores, gestiona múltiples jugadores, controla turnos y actualiza el estado global | 70 |
| Bueno | Funciona en general, pero presenta leves errores en validación de turnos o estado global | 50 |
| Aceptable | Tiene fallos en turnos o actualizaciones que afectan la experiencia de juego | 30 |
| Deficiente | No gestiona turnos, presenta errores críticos o no se ejecuta | 0 |

**Evaluación: ✅ Excelente — 70/70 pts**

| Ítem evaluado | Estado |
|---|---|
| Servidor inicia sin errores (`start_server.sh`, variables de entorno) | ✅ |
| Gestiona múltiples salas simultáneas (`GameRoomManager`, `mgr_lock`) | ✅ |
| Controla turnos correctamente (`turn_order`, `current_turn_idx`) | ✅ |
| Valida jugadas (coordenadas, turno correcto, estado del tablero) | ✅ |
| Envía actualizaciones a todos los clientes (`SubscribeToUpdates` stream) | ✅ |
| Detecta fin de ronda y fin de juego (`ROUND_OVER`, `FINISHED`) | ✅ |
| Registra puntuación, tiempos de respuesta y desempeño por jugador | ✅ |
| Host configura la sala antes de iniciar (`ConfigureGame` RPC, estado `LOBBY`) | ✅ extra |
| Múltiples rondas con acumulación de puntaje | ✅ extra |

---

### 1.2 Interacción y lógica del cliente (60 pts)

| Nivel | Criterio | Pts |
|-------|----------|-----|
| **Excelente** | El cliente permite jugar correctamente, valida turnos, actualiza el tablero y muestra mensajes claros | 60 |
| Bueno | Funciona pero con errores menores en visualización o validaciones | 40 |
| Aceptable | Permite jugar, pero el control de flujo o mensajes es confuso | 20 |
| Deficiente | No permite jugar adecuadamente, o no se conecta al servidor | 0 |

**Evaluación: ✅ Excelente — 60/60 pts**

| Ítem evaluado | Estado |
|---|---|
| Cliente se conecta con nombre y recibe UUID | ✅ |
| Tablero visual con emojis SVG (Twemoji), animaciones 3D flip | ✅ |
| Primera carta se voltea inmediatamente para todos (`SelectCard` RPC) | ✅ |
| Validación local de turno antes de enviar jugada | ✅ |
| Tablero se actualiza en tiempo real vía SSE | ✅ |
| Mensajes contextuales (tu turno, espera, fin de ronda, ranking) | ✅ |
| Cliente de consola alternativo (`client/memory_client.py`) | ✅ |
| Panel de host con spinners `−/+` para configurar la sala | ✅ extra |

---

### 1.3 Sincronización y comunicación en red (60 pts)

| Nivel | Criterio | Pts |
|-------|----------|-----|
| **Excelente** | Clientes y servidor se comunican correctamente, se usan streams para actualizaciones en tiempo real | 60 |
| Bueno | La comunicación es funcional, aunque sin streams o con retrasos leves | 40 |
| Aceptable | Comunicación parcial o limitada a un solo cliente a la vez | 20 |
| Deficiente | No hay comunicación funcional | 0 |

**Evaluación: ✅ Excelente — 60/60 pts**

| Ítem evaluado | Estado |
|---|---|
| `SubscribeToUpdates` como server-stream gRPC activo | ✅ |
| SSE (`text/event-stream`) desde Flask hacia el browser | ✅ |
| `threading.Condition` (`cv`) por sala — no polling, push puro | ✅ |
| `threading.Lock` (`mgr_lock`) para gestor de salas compartido | ✅ |
| Flag `processing` para evitar doble-jugada | ✅ |
| `yield` del stream fuera del `with cv` (evita deadlock) | ✅ |
| `PRAGMA journal_mode=WAL` para SQLite concurrente | ✅ |
| Docker con red `game_net` bridge para comunicación entre contenedores | ✅ |

---

### 1.4 Implementación técnica y calidad del código (50 pts)

| Nivel | Criterio | Pts |
|-------|----------|-----|
| **Excelente** | Código estructurado, con clases bien definidas, modularidad, comentarios y uso correcto de gRPC | 50 |
| Bueno | Código funcional pero con oportunidades de mejora en organización o documentación | 30 |
| Aceptable | Código poco modular, difícil de seguir o con malas prácticas | 10 |
| Deficiente | Código desorganizado, sin separación de responsabilidades | 0 |

**Evaluación: ✅ Excelente — 50/50 pts**

| Ítem evaluado | Estado |
|---|---|
| Capas bien separadas: `proto/`, `server/`, `client/`, `web_client/` | ✅ |
| `GameRoom` encapsula toda la lógica de una sala | ✅ |
| `GameRoomManager` gestiona el ciclo de vida de las salas | ✅ |
| 8 RPCs bien definidos en `memory.proto` con mensajes propios | ✅ |
| `Dockerfile` compila el proto en build (no depende de pb2 en repo) | ✅ |
| `requirements.txt` con versiones fijadas | ✅ |
| `.gitignore` correcto (excluye pb2, data/, cache) | ✅ |
| Comentarios de sección en código con delimitadores visuales | ✅ |

---

### 1.5 Documentación y evidencia (60 pts)

| Nivel | Criterio | Pts |
|-------|----------|-----|
| Excelente | README claro, bitácora completa, capturas de pantalla y reflexión final | 60 |
| **Bueno** | Entrega completa pero con documentación parcial o bitácora incompleta | 40 |
| Aceptable | Entrega incompleta o con documentación mínima | 20 |
| Deficiente | No hay documentación o evidencia del trabajo realizado | 20 |

**Evaluación: ⚠️ Bueno — 40/60 pts**

| Ítem evaluado | Estado |
|---|---|
| `README.md` completo con arquitectura, instrucciones y esquema SQLite | ✅ |
| Arquitectura descrita (diagrama ASCII, tabla de RPCs, ciclo de estados) | ✅ |
| Scripts `start_server.sh` y `start_web.sh` documentados | ✅ |
| Variables de entorno documentadas | ✅ |
| Reporte en `.PDF` | ❌ no incluido |
| Capturas de pantalla del juego en funcionamiento | ❌ no incluidas |
| Bitácora / reflexión técnica del proceso de desarrollo | ❌ no incluida |

---

### Subtotal rúbrica oficial

| Categoría | Máx. | Obtenido |
|---|---|---|
| 1. Funcionamiento del servidor | 70 | **70** |
| 2. Interacción y lógica del cliente | 60 | **60** |
| 3. Sincronización y comunicación en red | 60 | **60** |
| 4. Implementación técnica y calidad del código | 50 | **50** |
| 5. Documentación y evidencia | 60 | **40** |
| **TOTAL** | **300** | **280 / 300 (93.3%)** |

---

## 2. Checklist oficial

### Sección 1 — Configuración y arquitectura general

| # | Ítem | Estado |
|---|------|--------|
| 1.1 | `.proto` creado y compilado correctamente | ✅ |
| 1.2 | Servidor inicia y acepta múltiples conexiones | ✅ |
| 1.3 | Cliente se conecta desde otra máquina/contenedor en red LAN | ✅ (Docker `game_net`) |
| 1.4 | `docker-compose` para levantar todos los servicios | ✅ |
| 1.5 | Red Docker compartida entre contenedores | ✅ (`game_net` bridge) |

**5/5 ✅**

### Sección 2 — Funcionalidad del servidor

| # | Ítem | Estado |
|---|------|--------|
| 2.1 | Asigna UUID único a cada cliente | ✅ (`uuid.uuid4()`) |
| 2.2 | Mantiene estado global del tablero | ✅ |
| 2.3 | Controla turnos correctamente | ✅ |
| 2.4 | Valida jugadas (par válido, coordenadas correctas) | ✅ |
| 2.5 | Envía actualizaciones a todos los clientes | ✅ |
| 2.6 | Detecta fin del juego y lo notifica | ✅ |
| 2.7 | Registro de puntuación, tiempos de respuesta y desempeño | ✅ |

**7/7 ✅**

### Sección 3 — Funcionalidad del cliente

| # | Ítem | Estado |
|---|------|--------|
| 3.1 | Solicita unirse con nombre, recibe ID | ✅ |
| 3.2 | Muestra tablero de forma legible | ✅ (web con emojis SVG + consola) |
| 3.3 | Permite seleccionar dos cartas por turno | ✅ |
| 3.4 | Valida localmente si es su turno | ✅ |
| 3.5 | Actualiza tablero al recibir notificaciones | ✅ (SSE) |
| 3.6 | Muestra mensajes adecuados | ✅ |

**6/6 ✅**

### Sección 4 — Lógica del tablero

| # | Ítem | Estado |
|---|------|--------|
| 4.1 | Tablero generado con pares barajados al azar | ✅ (`random.shuffle`) |
| 4.2 | Estado se actualiza al encontrar una pareja | ✅ |
| 4.3 | Diferenciación visual: oculta / revelada / emparejada | ✅ |
| 4.4 | Reglas respetadas (dos cartas por turno) | ✅ |

**4/4 ✅**

### Sección 5 — Documentación y entrega

| # | Ítem | Estado |
|---|------|--------|
| 5.1 | Reporte en `.PDF` | ❌ |
| 5.2 | Código documentado con comentarios descriptivos | ⚠️ parcial |
| 5.3 | Arquitectura de la solución descrita | ✅ (README) |
| 5.4 | Partes relevantes explicadas | ✅ (README) |
| 5.5 | Capturas de pantalla con múltiples clientes | ❌ |

**3/5 ⚠️**

### Sección 6 — Validación final

| # | Ítem | Estado |
|---|------|--------|
| 6.1 | Al menos 3 clientes jugando correctamente | ✅ (hasta 8 soportados) |
| 6.2 | Flujo de turnos respetado por todos los clientes | ✅ |
| 6.3 | Juego finaliza correctamente al emparejar todas las cartas | ✅ |
| 6.4 | Métricas de desempeño registradas correctamente | ✅ |
| 6.5 | Posible consultar datos de partidas almacenadas | ✅ (ranking tab + SQLite) |

**5/5 ✅**

**Resumen checklist: 30/32 ítems (93.8%)**

---

## 3. Evaluación contra la Guía de Métricas (guiaMetricas.md)

> Análisis exacto basado en el esquema real de SQLite y la lógica de captura en `memory_server.py`.
>
> **Tablas disponibles:**
> - `rounds` → `id`, `room_id`, `round_num`, `board_size`, `ended_at`
> - `player_results` → `round_id`, `player_name`, `score`, `total_moves`, `avg_response_time`
> - `moves` → `round_id`, `move_num`, `player_name`, `r1`, `c1`, `sym1`, `r2`, `c2`, `sym2`, `is_match`, `response_time_s`, `matched_before`, `board_state_json`, `scores_json`, `ts`

---

### 3.1 Sección 6.1 — Métricas de identificación y contexto

| Variable guía | Descripción | ¿Capturada? | Dónde / cómo |
|---|---|---|---|
| `id_jug` | Identificador del jugador | ✅ Sí | `player_name` en `moves` y `player_results`; UUID interno en runtime (`P-XXXX`) |
| `id_ses` | Identificador de sesión | ⚠️ Parcial | `room_id` cumple el rol, pero no se exporta como columna en `moves` (solo en `rounds` vía FK) |
| `id_ron` | Identificador de ronda | ✅ Sí | `round_id` (PK autoincrement), `round_num` en tabla `rounds` |
| `niv_dif` | Nivel de dificultad | ⚠️ Proxy | `board_size` en `rounds`; no hay columna explícita `niv_dif` |
| `tam_tab` | Tamaño del tablero | ✅ Sí | `board_size` en `rounds`; también inferible del JSON en `board_state_json` |
| `ver_cli` | Versión del cliente | ❌ No | No se registra |

**Cobertura: 3/6 directas, 2/6 aproximadas, 1/6 ausente**

---

### 3.2 Sección 6.2 — Métricas temporales

| Variable guía | Descripción | ¿Capturada? | Dónde / cómo |
|---|---|---|---|
| `t_resp_ms` | Tiempo entre inicio de turno y jugada | ✅ Sí | `response_time_s` en `moves` (misma semántica, unidad en segundos en vez de ms) |
| `t_ron_ms` | Tiempo total de la ronda | ❌ No | Solo hay `ended_at`; **falta `started_at`** en tabla `rounds` — no se puede calcular la duración |
| `t_par_ms` | Tiempo entre ver una carta y completar su par | ❌ No | No se rastrea cuándo fue observada por primera vez cada posición |
| `t_pau_ms` | Duración acumulada de pausas | ❌ No | No hay captura de inactividad |
| `t_ult_ses_h` | Tiempo desde la sesión anterior | ❌ No | Requiere historial por jugador |

**Cobertura: 1/5 directa, 0/5 aproximada, 4/5 ausentes**

---

### 3.3 Sección 6.3 — Métricas de resultado y eficiencia

| Variable guía | Descripción | ¿Capturada? | Dónde / cómo |
|---|---|---|---|
| `tot_aci` | Total de pares encontrados | ✅ Sí | `score` en `player_results` |
| `tot_err` | Total de intentos fallidos | ⚠️ Derivable | `total_moves - score` desde `player_results`; no es columna directa |
| `tasa_aci` | Aciertos / intentos totales | ⚠️ Derivable | `score / total_moves` desde `player_results` |
| `tasa_err` | Errores / intentos totales | ⚠️ Derivable | `1 - (score / total_moves)` |
| `idx_efi` | Índice compuesto de eficiencia | ❌ No | No se calcula ni almacena |
| `tasa_aci_1` | Pares resueltos sin error previo | ❌ No | Requeriría rastrear si cada par fue acertado en primer intento |

**Cobertura: 1/6 directa, 3/6 derivables, 2/6 ausentes**

---

### 3.4 Sección 6.4 — Métricas secuenciales

| Variable guía | Descripción | ¿Capturada? | Dónde / cómo |
|---|---|---|---|
| `racha_aci` | Aciertos consecutivos | ❌ No | No se almacena por movimiento; derivable offline con `is_match` + `move_num` |
| `racha_err` | Errores consecutivos | ❌ No | Ídem — derivable offline, pero no capturado directamente |
| `rep_car` | Veces que se repite una carta ya vista sin éxito | ⚠️ Derivable | Los `board_state_json` + `r1/c1/r2/c2` de movimientos anteriores permiten reconstruirlo offline |
| `idx_exp` | Grado de exploración de cartas nuevas | ❌ No | No calculado |
| `t_rec_err_ms` | Tiempo para volver a acertar tras un error | ❌ No | Requiere combinar `is_match` + `response_time_s` secuencial; no almacenado |
| `pat_rev` | Patrón espacial de revisita | ⚠️ Derivable | Reconstruible desde la secuencia de `r1/c1/r2/c2` por jugador y ronda |

**Cobertura: 0/6 directas, 2/6 derivables offline, 4/6 ausentes**

> **Nota**: `racha_aci` y `racha_err` son las únicas que se podrían calcular en tiempo real en el servidor con un contador de 2 líneas; el resto requieren análisis post-proceso.

---

### 3.5 Sección 6.5 — Métricas de recuerdo en contexto de juego

| Variable guía | Descripción | ¿Capturada? | Dónde / cómo |
|---|---|---|---|
| `rec_par` | Proporción de veces que se completa correctamente un par ya visto | ⚠️ Parcial | `matched_before` registra **cuántos pares ya estaban emparejados** en el tablero — es contexto de avance, no de memoria específica del jugador sobre un par |
| `dem_mem_ms` | Tiempo entre primera observación de una carta y acierto de su par | ❌ No | No se rastrea cuándo fue vista por primera vez cada posición individual |
| `int_ant_par` | Cartas irrelevantes entre primera y segunda visión del par | ❌ No | No capturado |
| `fall_par_rep` | Fallos repetidos sobre pares ya observados | ⚠️ Derivable | Reconstruible comparando `sym1/sym2` de movimientos fallidos previos en `board_state_json` |
| `tol_tab` | Estabilidad de precisión conforme crece el tablero | ❌ No | Requiere historial entre sesiones con distintos `board_size` |

**Cobertura: 0/5 directas, 1/5 aproximada (mal semantizada), 2/5 derivables, 2/5 ausentes**

---

### 3.6 Secciones 6.6, 6.7, 6.8 — Progreso, Apoyo, Técnicas

| Bloque | Variables | Estado |
|---|---|---|
| 6.6 Progreso (`gan_ses`, `ten_des`, `caida_olv`, `var_des`, `adap_dif`) | Todas requieren historial cross-sesión por jugador | ❌ No aplica en el alcance de la práctica |
| 6.7 Apoyo (`tot_ayu`, `mom_ayu`, `des_pos_ayu`) | No existe sistema de ayudas/pistas en el juego | N/A — funcionalidad no implementada |
| 6.8 Técnicas (`lat_red_ms`, `tasa_fal`, `des_sin`, `t_srv_ms`) | Ninguna se captura | ❌ No capturadas |

---

### 3.7 Propuesta mínima viable — sección 10 (15 variables)

| # | Variable | Estado real | Detalle |
|---|----------|-------------|---------|
| 1 | `id_jug` | ✅ | `player_name` en moves / player_results |
| 2 | `id_ses` | ⚠️ | `room_id` vía FK a rounds, no columna directa en moves |
| 3 | `id_ron` | ✅ | `round_id` FK + `round_num` |
| 4 | `niv_dif` | ⚠️ | `board_size` en rounds como proxy |
| 5 | `tam_tab` | ✅ | `board_size` en rounds |
| 6 | `t_resp_ms` | ✅ | `response_time_s` en moves (segundos) |
| 7 | `t_ron_ms` | ❌ | Solo `ended_at`; falta `started_at` para calcular duración |
| 8 | `tot_aci` | ✅ | `score` en player_results |
| 9 | `tot_err` | ⚠️ | Derivable: `total_moves - score` |
| 10 | `tasa_aci` | ⚠️ | Derivable: `score / total_moves` |
| 11 | `racha_err` | ❌ | No almacenada (derivable offline de `is_match` + `move_num`) |
| 12 | `racha_aci` | ❌ | Ídem |
| 13 | `rec_par` | ❌ | `matched_before` ≠ `rec_par`; registra pares totales ya emparejados, no si ese par específico fue visto antes |
| 14 | `tot_ayu` | N/A | No hay sistema de ayudas |
| 15 | `lat_red_ms` | ❌ | No capturada |

| Resultado | Cantidad | % (sin N/A) |
|---|---|---|
| ✅ Directamente implementada | 5 | 36 % |
| ⚠️ Derivable / equivalente aproximado | 4 | 29 % |
| ❌ Ausente | 5 | 36 % |
| N/A | 1 | — |

**Cobertura mínima viable real: 5/14 directas + 4/14 derivables = 64 %**

> La evaluación anterior indicaba 73 %; la revisión exacta del código baja ese número a **~64 %** porque `rec_par` y `t_ron_ms` **no son capturables con los datos actuales** sin cambios en el esquema.

---

### 3.8 Lo que SÍ captura el sistema y excede la guía

Aunque varias variables de la guía faltan, la tabla `moves` contiene **datos crudos de mayor granularidad** que permiten derivar muchas de ellas en post-proceso:

| Dato capturado | Valor para ML | Columna en `moves` |
|---|---|---|
| Snapshot NxN completo del tablero en cada turno | Feature espacial; permite reconstruir `rep_car`, `int_ant_par`, `fall_par_rep` | `board_state_json` |
| Símbolo y posición exacta de ambas cartas | Análisis de estrategia espacial | `sym1`, `sym2`, `r1/c1`, `r2/c2` |
| Número de pares ya emparejados al momento del movimiento | Contexto de avance en la ronda | `matched_before` |
| Scores de todos los jugadores en ese instante | Contexto competitivo | `scores_json` |
| Número de movimiento secuencial | Posición temporal exacta dentro de la ronda | `move_num` |
| Timestamp ISO de cada movimiento | Permite calcular `racha_*` y `t_rec_err_ms` offline | `ts` |

---

## 4. Resumen ejecutivo

### Calificación estimada

| Dimensión | Puntaje |
|---|---|
| Rúbrica oficial (300 pts base) | **280 / 300** |
| Checklist oficial | **30 / 32 ítems** |
| Mínimo viable de métricas (sección 10) | **~64 %** (9/14 directas o derivables) |
| Cobertura bloques completos (sección 6) | **~30 %** directo + muchas derivables offline |

### Fortalezas destacadas

- Multi-sala, multi-ronda, host configura la partida dinámicamente
- Sincronización correcta con `threading.Condition` y streams gRPC
- `board_state_json` por movimiento — permite reconstruir offline la mayoría de métricas secuenciales
- Cliente web con UX polida (Twemoji, animaciones 3D, SSE, spinners)
- Docker funcional con healthcheck y proto compilado en build

### Qué falta de la mínima viable y cómo agregarlo

**1. `t_ron_ms` — agregar `started_at` a la tabla `rounds`:**
```python
# En _start_next_round():
self.round_started_at = time.time()

# En db_save_round, en el INSERT a rounds:
"INSERT INTO rounds (room_id, round_num, board_size, started_at, ended_at) VALUES (?,?,?,?,?)"
# → t_ron_ms = (ended_at_epoch - started_at_epoch) * 1000
```

**2. `racha_err` y `racha_aci` — dos contadores en GameRoom:**
```python
# En __init__:
self._streak_ok  = 0
self._streak_err = 0

# En play_turn, antes de append a _move_log:
if is_match:
    self._streak_ok  += 1
    self._streak_err  = 0
else:
    self._streak_err += 1
    self._streak_ok   = 0

m["racha_aci"] = self._streak_ok
m["racha_err"] = self._streak_err
# + agregar columnas racha_aci, racha_err a tabla moves
```

**3. `rec_par` real — rastrear si el símbolo ya fue revelado antes:**
```python
# En play_turn, añadir al snapshot:
seen_symbols = set()
for rr in range(self.size):
    for cc in range(self.size):
        cell = self.board[rr][cc]
        if cell["matched"] or (cell["flipped"] and not (rr==r2 and cc==c2)):
            seen_symbols.add(cell["symbol"])
m["sym1_seen_before"] = c1_obj["symbol"] in seen_symbols
m["sym2_seen_before"] = c2_obj["symbol"] in seen_symbols
# rec_par por ronda = movimientos donde ambas seen_before y is_match / total
```

**4. `lat_red_ms` — medir desde el cliente web:**
```javascript
// En index.html, función playCard():
const t0 = Date.now();
const res = await fetch('/api/play', { body: JSON.stringify({...data, client_ts: t0}) });
```
```python
# En web_client/app.py POST /api/play:
lat = int(time.time() * 1000) - body.get("client_ts", 0)
# Pasar lat al servidor como campo adicional del MoveRequest
```

**5. PDF, capturas y bitácora** — pendiente de redactar para completar la documentación.
