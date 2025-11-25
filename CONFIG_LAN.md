# ============================================================================

# CONFIGURACIÓN DE RED LAN - SERVER5K

# ============================================================================

## 📋 Información del Servidor

**IP del Servidor:** `192.168.0.108`
**Puerto:** `8000`
**Redis:** Docker container `redis-dev` en puerto `6379`

---

## 🔗 URLs para Apps Móviles

### HTTP/API

```
http://192.168.0.108:8000
```

### WebSocket

```
ws://192.168.0.108:8000
```

### Endpoints principales

-   **API Base:** `http://192.168.0.108:8000/api/`
-   **Login:** `http://192.168.0.108:8000/api/login/`
-   **Competencias:** `http://192.168.0.108:8000/api/competencias/`
-   **Equipos:** `http://192.168.0.108:8000/api/equipos/`
-   **WebSocket Juez:** `ws://192.168.0.108:8000/ws/juez/{competencia_id}/`
-   **Admin:** `http://192.168.0.108:8000/admin/`
-   **API Docs:** `http://192.168.0.108:8000/api/docs/`

---

## 🚀 Iniciar Servidor

```powershell
# Opción 1: Script de inicio con validaciones (RECOMENDADO)
.\start_server_lan.ps1

# Opción 2: Comando directo
$env:DJANGO_SETTINGS_MODULE="server.settings"; uv run daphne -b 0.0.0.0 -p 8000 server.asgi:application
```

---

## 🔍 Verificaciones Previas

### 1. Verificar Redis

```powershell
# Ver containers corriendo
docker ps

# Debe mostrar: redis-dev

# Verificar conectividad
redis-cli ping
# Debe responder: PONG
```

### 2. Verificar IP

```powershell
ipconfig

# Buscar tu IP en "Adaptador de LAN inalámbrica Wi-Fi"
# Debe ser: 192.168.0.108
```

### 3. Verificar Firewall

```powershell
Get-NetFirewallRule -DisplayName "Django Server5K"

# Si no existe, crear (ejecutar como Administrador):
New-NetFirewallRule -DisplayName "Django Server5K" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

---

## 📱 Configuración en Apps Móviles

### JavaScript/React Native

```javascript
const BASE_URL = "http://192.168.0.108:8000";
const WS_URL = "ws://192.168.0.108:8000";

// WebSocket
const socket = new WebSocket(`${WS_URL}/ws/juez/${competenciaId}/`);

// HTTP
fetch(`${BASE_URL}/api/competencias/`)
    .then((response) => response.json())
    .then((data) => console.log(data));
```

### Flutter/Dart

```dart
const String baseUrl = 'http://192.168.0.108:8000';
const String wsUrl = 'ws://192.168.0.108:8000';

// WebSocket
final channel = WebSocketChannel.connect(
  Uri.parse('$wsUrl/ws/juez/$competenciaId/'),
);

// HTTP
final response = await http.get(Uri.parse('$baseUrl/api/competencias/'));
```

### Python (para testing)

```python
import requests
import websocket

BASE_URL = 'http://192.168.0.108:8000'
WS_URL = 'ws://192.168.0.108:8000'

# HTTP
response = requests.get(f'{BASE_URL}/api/competencias/')

# WebSocket
ws = websocket.WebSocket()
ws.connect(f'{WS_URL}/ws/juez/{competencia_id}/')
```

---

## 📊 Monitorear Redis en Tiempo Real

```powershell
# Terminal 1: Monitorear comandos Redis
redis-cli monitor

# Terminal 2: Ver estadísticas
redis-cli INFO stats

# Terminal 3: Ver keys actuales
redis-cli KEYS "server5k:*"

# Ver clientes conectados
redis-cli CLIENT LIST
```

---

## 🐛 Solución de Problemas

### Problema: "Connection refused" desde apps móviles

**Solución:**

1. Verificar que ambos dispositivos estén en la misma red WiFi
2. Verificar firewall: `Get-NetFirewallRule -DisplayName "Django Server5K"`
3. Verificar que el servidor esté en `0.0.0.0:8000` (no `127.0.0.1`)

### Problema: Redis no responde

**Solución:**

```powershell
# Ver logs del container
docker logs redis-dev

# Reiniciar container
docker restart redis-dev

# Verificar puerto
netstat -an | Select-String "6379"
```

### Problema: WebSocket no conecta

**Solución:**

1. Verificar que Redis esté corriendo: `redis-cli ping`
2. Verificar que CHANNEL_LAYERS use `channels_redis.core.RedisChannelLayer`
3. Verificar logs del servidor para errores de conexión
4. Probar desde navegador web: `http://192.168.0.108:8000/api/docs/`

---

## ✅ Checklist de Verificación

Antes de probar con dispositivos móviles:

-   [ ] Redis corriendo en Docker (`docker ps` muestra `redis-dev`)
-   [ ] Redis responde (`redis-cli ping` → `PONG`)
-   [ ] IP correcta en `ALLOWED_HOSTS` (`192.168.0.108`)
-   [ ] Firewall permite puerto 8000
-   [ ] Servidor iniciado en `0.0.0.0:8000` (no `127.0.0.1`)
-   [ ] Apps móviles configuradas con `http://192.168.0.108:8000`
-   [ ] Todos los dispositivos en la misma red WiFi
-   [ ] `redis-cli monitor` corriendo en otra terminal

---

## 📈 Capacidad Actual

**Configuración de Redis:**

-   `capacity`: 2000 mensajes por canal
-   `expiry`: 60 segundos TTL
-   `prefix`: 'server5k'

**Soporta:**

-   ~20 dispositivos conectados simultáneamente
-   ~15 registros por dispositivo
-   Total: ~300 mensajes en un período corto

---

## 🔧 Configuración Actual en settings.py

```python
# IP permitida
ALLOWED_HOSTS = [
    '192.168.0.108',
    '192.168.0.*',
    'localhost',
    '127.0.0.1',
]

# Redis activado
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
            'capacity': 2000,
            'expiry': 60,
            'prefix': 'server5k',
        },
    }
}

# CORS habilitado
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
```

---

**Última actualización:** 23 de noviembre de 2025
**IP configurada:** 192.168.0.108
**Redis container:** redis-dev
