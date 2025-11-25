# 🧪 Script de Prueba de Carga - 16 Jueces Simultáneos

## 📋 Descripción

Este script simula 16 jueces conectándose simultáneamente al servidor, cada uno:

1. **Hace login** con sus credenciales
2. **Conecta por WebSocket** usando el token obtenido
3. **Envía 15 registros de tiempo** en un solo batch
4. **Recibe confirmación** de los registros guardados

**Total:** 16 jueces × 15 registros = **240 registros** enviados simultáneamente

## 🚀 Uso

### Requisitos previos

1. **Servidor corriendo**:

    ```powershell
    .\start_server_lan.ps1
    ```

2. **Redis activo**:

    ```powershell
    docker ps  # Debe mostrar redis-dev corriendo
    ```

3. **Competencia en curso**:
    - Accede al admin: http://127.0.0.1:8000/admin/
    - Inicia una competencia desde el panel de admin

### Ejecutar el script

```powershell
uv run python test_load_16_jueces.py
```

## 📊 Qué verás

El script mostrará en tiempo real:

```
================================================================================
  🧪 PRUEBA DE CARGA - SERVER5K
  16 Jueces Simultáneos × 15 Registros = 240 Registros Totales
================================================================================

 #  Juez                  Estado
 1  Joan Figuerola        ⏳ Esperando...
 2  Salud Garriga         ⏳ Esperando...
 ...
 16 Edelmiro Riera        ⏳ Esperando...

[procesando...]

================================================================================
  📊 RESULTADOS DE LA PRUEBA
================================================================================

 #  Juez                  Login  WS     Enviados  Confirmados  Tiempo
 1  Joan Figuerola        ✅     ✅     15        15           1.23s
 2  Salud Garriga         ✅     ✅     15        15           1.19s
 ...

┌─ 📈 Estadísticas Generales ─┐
│ ⏱️  Tiempo Total:      3.45 segundos │
│ 👥 Jueces Procesados:  16 │
│ ✅ Logins Exitosos:    16/16 │
│ 🔌 WebSockets Conectados: 16/16 │
│ 📤 Registros Enviados: 240 (esperados: 240) │
│ ✅ Registros Confirmados: 240/240 │
│ 📊 Tasa de Éxito:      100.0% │
│ ⚡ Throughput:         69.6 registros/segundo │
└────────────────────────────────────┘
```

## 🔍 Qué prueba este script

### 1. **Sistema de autenticación JWT**

-   Login de 16 usuarios simultáneos
-   Obtención de tokens de acceso
-   Validación de tokens en WebSocket

### 2. **Comunicación WebSocket**

-   16 conexiones WebSocket concurrentes
-   Manejo de grupos de canales (channels con Redis)
-   Envío/recepción de mensajes en tiempo real

### 3. **Redis como Transport Layer**

-   Distribución de mensajes entre múltiples conexiones
-   Capacidad de manejar carga concurrente
-   Persistencia temporal de mensajes

### 4. **Lógica de negocio**

-   Validación de competencia en curso
-   Registro batch de tiempos (15 a la vez)
-   Idempotencia (evitar duplicados)
-   Límite de 15 registros por equipo

### 5. **Performance**

-   Throughput (registros/segundo)
-   Latencia de respuesta
-   Manejo de errores
-   Estabilidad bajo carga

## 🐛 Solución de problemas

### Error: "Connection refused"

**Problema:** El servidor no está corriendo o Redis no está activo

**Solución:**

```powershell
# 1. Verifica Redis
docker ps

# 2. Inicia el servidor
.\start_server_lan.ps1
```

### Error: "La competencia no está en curso"

**Problema:** No hay competencia activa o no está iniciada

**Solución:**

1. Accede a http://127.0.0.1:8000/admin/
2. Ve a "Competencias"
3. Click en "▶️ Iniciar" en la competencia que deseas usar

### Error: "Login falló"

**Problema:** Las credenciales no son correctas o los jueces no existen

**Solución:**

```powershell
# Poblar datos de prueba
uv run python manage.py populate_data --clear
```

### Error: "WebSocket timeout"

**Problema:** Redis no está respondiendo o el servidor tiene problemas

**Solución:**

```powershell
# Verifica Redis
docker exec redis-dev redis-cli ping
# Debe responder: PONG

# Reinicia Redis si es necesario
docker restart redis-dev
```

## 📈 Interpretación de resultados

### ✅ Prueba Exitosa

```
✅ Logins Exitosos:    16/16
🔌 WebSockets Conectados: 16/16
✅ Registros Confirmados: 240/240
📊 Tasa de Éxito:      100.0%
```

### ⚠️ Prueba Parcial

```
✅ Logins Exitosos:    16/16
🔌 WebSockets Conectados: 14/16  ← Algunos fallos
✅ Registros Confirmados: 210/240
📊 Tasa de Éxito:      87.5%
```

**Revisar:** Logs del servidor y Redis monitor

### ❌ Prueba Fallida

```
✅ Logins Exitosos:    0/16  ← No hay logins
```

**Revisar:** Servidor no está corriendo o credenciales incorrectas

## 🔧 Personalización

### Cambiar número de registros por juez

Edita el archivo `test_load_16_jueces.py`:

```python
NUM_REGISTROS = 15  # Cambia este valor
```

### Cambiar URL del servidor

```python
BASE_URL = "http://192.168.0.108:8000"  # Para pruebas en LAN
WS_URL = "ws://192.168.0.108:8000"
```

### Cambiar rango de tiempos

```python
# Línea ~175 - Tiempo aleatorio entre 15-45 minutos
tiempo = random.randint(900000, 2700000)  # ms
```

## 📝 Notas

-   **Este script usa las credenciales de [`credenciales_jueces.txt`](credenciales_jueces.txt)**
-   **Cada juez envía registros para su equipo asignado** (juez1 → equipo1, etc.)
-   **Los tiempos son aleatorios** entre 15-45 minutos
-   **Redis debe estar configurado** en `settings.py` (ya configurado)
-   **El script es idempotente** - puedes ejecutarlo múltiples veces

## 🎯 Casos de uso

1. **Antes de desplegar a producción:** Verificar que el sistema aguanta carga
2. **Testing de Redis:** Confirmar que la configuración de Redis funciona
3. **Debugging:** Identificar cuellos de botella en el sistema
4. **Validación:** Asegurar que la lógica de negocio funciona correctamente

---

**Última actualización:** 23 de noviembre de 2025
