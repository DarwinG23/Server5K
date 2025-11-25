# 🔍 Debugging del Test de Carga - Análisis Detallado

## ❌ Problema Detectado

```
✅ Logins Exitosos: 16/16
🔌 WebSockets Conectados: 16/16
📤 Registros Enviados: 240
❌ Registros Confirmados: 0/240  ← PROBLEMA
📊 Tasa de Éxito: 0.0%
⚠️ Todos los jueces reportan: "15 registros fallaron"
```

---

## 🔬 Análisis de Redis Monitor

### Al Iniciar Competencia (COMPORTAMIENTO NORMAL ✅)

```redis
ZREMRANGEBYSCORE "server5k:group:juez_25" "0" "1763844728"
ZRANGE "server5k:group:juez_25" "0" "-1"
```

**Explicación**:

-   Django Channels limpia mensajes antiguos (> 24h) de cada grupo Redis
-   Se ejecuta para cada juez (25-40) al iniciar la competencia
-   **Esto es NORMAL y ESPERADO** ✅

---

### Durante el Test (COMPORTAMIENTO ANORMAL ⚠️)

```redis
# 1. Conexiones establecidas (✅ CORRECTO)
ZADD "server5k:group:juez_40" "timestamp" "channel_name"
ZADD "server5k:group:juez_25" "timestamp" "channel_name"
...

# 2. Mensajes agregados a grupos (✅ CORRECTO)
ZADD "server5k:group:competencia_7" "timestamp" "specific.xxx"

# 3. Mensajes ELIMINADOS sin procesamiento (❌ PROBLEMA)
ZREM "server5k:group:juez_40" "specific.xxx"
ZREM "server5k:group:competencia_7" "specific.xxx"
```

**Problema Detectado**:

-   Los mensajes se agregan a Redis (`ZADD`)
-   Luego se eliminan inmediatamente (`ZREM`)
-   **NO hay logs de procesamiento en el servidor**
-   Los clientes reciben "15 registros fallaron"

---

## 🔍 Causas Posibles

### 1. La Competencia NO está en curso ⚠️

**Verificar**:

```sql
-- En Django shell o admin
SELECT id, nombre, en_curso FROM app_competencia WHERE id = 7;
```

**Síntoma**: El campo `en_curso` es `False`

**Solución**:

1. Ir a http://localhost:8000/admin/app/competencia/7/
2. Click en botón "Iniciar Competencia"
3. Verificar que `en_curso = True`

---

### 2. Error Silencioso en el Consumer ⚠️

**Posible causa**: Excepción no capturada en `manejar_registro_tiempos_batch()`

**Qué buscar en logs del servidor**:

```
[ERROR] [BATCH] Error crítico: ...
```

**Pasos**:

1. Ver terminal donde corre Daphne (`start_server_lan.ps1`)
2. Buscar líneas que contengan `[BATCH]` o `[ERROR]`
3. Si no hay logs, el problema es anterior (validación)

---

### 3. Validación de Datos Falla ⚠️

**Posible causa**: `validar_datos_batch()` rechaza el mensaje

**Qué revisa la validación**:

```python
# En app/websocket/validators.py
def validar_datos_batch(content):
    # Verifica:
    - content tiene 'equipo_id'
    - content tiene 'registros' (lista)
    - registros no está vacío
    - cada registro tiene campo 'tiempo'
```

**Solución**:

-   Ver logs del servidor: `[BATCH] Validación fallida: ...`
-   Verificar formato del mensaje en el script

---

### 4. Equipos NO asignados a Jueces ⚠️

**Verificar en admin**:

```
Equipo 1 → juez_asignado = juez_40 (Joan Figuerola)
Equipo 2 → juez_asignado = juez_25 (Salud Garriga)
...
```

**Síntoma**: Error "El equipo no pertenece a este juez"

**Solución**:

```powershell
uv run python manage.py populate_data
```

---

## 🔧 Mejoras Implementadas

### 1. Logging Detallado en Consumer

```python
# Ahora el consumer loggea:
[INFO] [BATCH] Juez juez01 - Recibido batch para equipo 1
[INFO] [BATCH] Total registros en batch: 15
[INFO] [BATCH] Resultado - Guardados: 15, Fallidos: 0
[INFO] [BATCH] Respuesta enviada al cliente
```

### 2. Timeout en Script de Test

```python
# Antes: wait indefinidamente
respuesta = await websocket.recv()

# Ahora: timeout de 5 segundos
try:
    respuesta = await asyncio.wait_for(websocket.recv(), timeout=5.0)
except asyncio.TimeoutError:
    # Error claro en el reporte
```

### 3. Debug Output en Script

```python
# Muestra qué tipo de respuesta se recibió
print(f"[DEBUG {juez_nombre}] Respuesta recibida: {tipo}")

# Muestra errores específicos de registros fallidos
for fallo in data_respuesta.get("registros_fallidos", [])[:3]:
    print(f"  ❌ {juez_nombre}: {fallo.get('error')}")
```

### 4. Configuración de Logging en Django

```python
# En server/settings.py
LOGGING = {
    'loggers': {
        'app.websocket.consumers': {'level': 'INFO'},
        'app.services': {'level': 'INFO'},
    }
}
```

---

## 🚀 Pasos para Resolver

### Paso 1: Verificar Estado de la Competencia

```powershell
# Django shell
uv run python manage.py shell
```

```python
from app.models import Competencia
comp = Competencia.objects.get(id=7)
print(f"En curso: {comp.en_curso}")  # Debe ser True
```

---

### Paso 2: Reiniciar Servidor con Logs

```powershell
# Terminal 1: Detener servidor actual
Ctrl+C

# Reiniciar con logging habilitado
.\start_server_lan.ps1
```

**Buscar al inicio**:

```
[INFO] Applying LOGGING configuration...
[INFO] Django check system...
[INFO] System check identified no issues (0 silenced).
```

---

### Paso 3: Ejecutar Test Nuevamente

```powershell
# Terminal 2: Ejecutar test
uv run python test_load_16_jueces.py
```

**Observar**:

1. **En terminal del servidor** (Terminal 1):

    ```
    [INFO] [BATCH] Juez juez40 - Recibido batch para equipo 1
    [INFO] [BATCH] Total registros en batch: 15
    ```

2. **En terminal del test** (Terminal 2):

    ```
    [DEBUG Joan Figuerola] Respuesta recibida: tiempos_registrados_batch
    ```

3. **En redis-cli monitor** (Terminal 3 - opcional):
    ```redis
    ZADD "server5k:group:juez_40" ...
    [procesamiento]
    ZREM "server5k:group:juez_40" ...
    ```

---

### Paso 4: Analizar Resultados

#### Si sale: `✅ Registros Confirmados: 240/240`

**¡Problema resuelto!** 🎉

-   El sistema funciona correctamente
-   Proceder a testing con dispositivos móviles

#### Si sale: `❌ Registros Confirmados: 0/240`

**Revisar logs del servidor**:

1. ¿Aparecen líneas `[BATCH]`?

    - **NO**: El mensaje no está llegando al consumer
    - **SÍ**: Ver qué error reporta

2. ¿Aparece `[BATCH] Validación fallida`?

    - Revisar formato del mensaje
    - Verificar que equipo_id existe

3. ¿Aparece `[BATCH] Resultado - Guardados: 0, Fallidos: 15`?
    - Ver `registros_fallidos` para detalles
    - Común: "La competencia no está en curso"

---

## 📋 Checklist de Verificación

Antes de ejecutar el test, confirmar:

-   [ ] **Redis corriendo**: `docker ps | Select-String redis-dev`
-   [ ] **Servidor activo**: Ver terminal con Daphne corriendo
-   [ ] **Competencia iniciada**: Admin panel → `en_curso = True`
-   [ ] **Equipos asignados**: Cada equipo tiene `juez_asignado` no nulo
-   [ ] **Logging configurado**: Ver `LOGGING` en `settings.py`
-   [ ] **Script actualizado**: Con timeout y debug output

---

## 🆘 Información para Reportar

Si el problema persiste, compartir:

### 1. Logs del Servidor (Terminal 1)

```
[copiar últimas 50 líneas desde que ejecutaste el test]
```

### 2. Output del Test (Terminal 2)

```
[copiar toda la salida, incluyendo líneas [DEBUG]]
```

### 3. Estado de la Competencia

```powershell
uv run python manage.py shell
```

```python
from app.models import Competencia, Juez, Equipo
comp = Competencia.objects.get(id=7)
print(f"Competencia: {comp.nombre}, En curso: {comp.en_curso}")

jueces = Juez.objects.filter(competencia=comp)
print(f"Total jueces: {jueces.count()}")

equipos = Equipo.objects.all()
sin_asignar = equipos.filter(juez_asignado__isnull=True).count()
print(f"Equipos sin asignar: {sin_asignar}")
```

### 4. Versiones

```powershell
uv run python --version
uv run python -m django --version
docker exec redis-dev redis-cli INFO server | Select-String "redis_version"
```

---

## 🎯 Resultado Esperado Final

```
================================================================================
                     📊 RESULTADOS DE LA PRUEBA
================================================================================

 #  Juez                  Login  WS  Enviados  Confirmados  Tiempo
 1  Joan Figuerola          ✅    ✅     15         15       1.96s
 2  Salud Garriga           ✅    ✅     15         15       2.07s
...

📈 Estadísticas Generales:
  ⏱️  Tiempo Total: 2.12 segundos
  ✅ Registros Confirmados: 240/240
  📊 Tasa de Éxito: 100.0%
  ⚡ Throughput: 113.2 registros/segundo

✅ PRUEBA EXITOSA - Todos los registros confirmados
```

---

**Última actualización**: 23 de noviembre de 2025  
**Versión**: 1.0 - Con mejoras de logging y debugging
