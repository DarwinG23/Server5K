# Server5K

Servidor Django para la aplicación móvil de registro de tiempos en carreras 5K.

## Resumen

Server5K es el backend (servidor) que soporta una app móvil usada por los jueces en carreras. Permite:

- Administrar competencias, jueces y equipos desde el panel de administración.
- Notificar a jueces en tiempo real (WebSocket) cuando una competencia inicia.
- Recibir y almacenar registros de tiempo enviados por la app móvil (JSON), limitando a los primeros 15 por envío.

El proyecto incluye integración con Django REST Framework, JWT (SimpleJWT) y Django Channels.

## Estructura del proyecto y componentes clave

Raíz del proyecto (resumen):

- `manage.py` — utilidades de Django.
- `pyproject.toml` / `requirements.txt` — dependencias del proyecto.
- `db.sqlite3` — base de datos SQLite (dev).
- `server/` — configuración del proyecto Django (ASGI, settings, urls, wsgi).
- `app/` — app principal que contiene modelos, vistas, consumers, serializadores y migraciones.
  - `models.py` — `Competencia`, `Juez`, `Equipo`, `RegistroTiempo`.
  - `admin.py` — personalizaciones del panel de admin (botón Iniciar/Detener competencia que notifica por WS).
  - `consumers.py` — `JuezConsumer` para WebSockets.
  - `serializers.py` — `EnvioTiemposSerializer` que valida el JSON entrante.
  - `views.py` — vista DRF `EnviarTiemposView` que procesa y guarda registros.
  - `migrations/` — migraciones de la base de datos.

## Modelos (comportamiento clave)

- `Competencia`: nombre, fecha, categoría, `en_curso`, `fecha_inicio`, `fecha_fin`. Métodos: `iniciar_competencia()` y `detener_competencia()` que actualizan estado y timestamps.
- `Juez`: `nombre`, `competencia`, `activo` y `user` (OneToOne a `AUTH_USER_MODEL`, nullable para migración). El `user` permite autenticación desde la app móvil.
- `Equipo`: `nombre`, `dorsal`, `juez_asignado` (FK a `Juez`). Propiedad `competencia` devuelve la competencia del juez.
- `RegistroTiempo`: `id_registro` (UUID), `equipo`, `tiempo` (ms), `timestamp` y campos desglosados (`horas`, `minutos`, `segundos`, `milisegundos`). El método `save()` sincroniza `tiempo` con los componentes.

## Requisitos

- Python 3.13+
- Sistema operativo: Windows (instrucciones aquí usan PowerShell), también funciona en macOS/Linux.
- Dependencias: ver `requirements.txt`.

## Preparar entorno (PowerShell)

1. Abrir PowerShell y ubicar el proyecto:

```powershell
cd "c:\Users\darwi\OneDrive\Escritorio\Universidad\Sexto\Software Distribuido\Unidad 1\WorkSpace\Server5K"
```

2. Crear y activar entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

4. Aplicar migraciones y crear superusuario:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

5. Ejecutar servidor (desarrollo):

```powershell
python manage.py runserver
```

Alternativa ASGI (Daphne):

```powershell
daphne -b 127.0.0.1 -p 8000 server.asgi:application
```

## Uso del panel Admin

- URL: http://127.0.0.1:8000/admin/
- Crear `Competencia`, `Juez` y `Equipo`.
- Asignar `user` a cada `Juez` (el campo `user` permite que el juez se autentique con JWT desde la app).
- Al presionar ▶️ Iniciar en una competencia, el admin enviará un evento `carrera.iniciada` por WebSocket a los jueces de esa competencia.

## API: endpoints y ejemplos

- Obtener token (JWT): POST `/api/token/` — body JSON { "username": "...", "password": "..." } -> devuelve { access, refresh }.
- Refrescar token: POST `/api/token/refresh/` — body JSON { "refresh": "..." }.
- Enviar tiempos: POST `/api/enviar_tiempos/` — protegido, requiere header `Authorization: Bearer <access>`.

### Formato JSON para enviar tiempos

Request POST `/api/enviar_tiempos/`

Headers:

```
Authorization: Bearer <ACCESS_TOKEN>
Content-Type: application/json
```

Body (ejemplo):

```json
{
  "equipo_id": 1,
  "registros": [
    { "timestamp": "2025-11-11T12:00:00.000Z", "tiempo": 12345 },
    { "timestamp": "2025-11-11T12:00:01.000Z", "tiempo": 13345 }
  ]
}
```

Notas:

- El serializer valida la estructura; únicamente los primeros 15 registros son procesados.
- Se valida que `request.user` tenga una `juez_profile` y que el `equipo_id` corresponda al `Equipo` cuyo `juez_asignado` es ese juez.

### Ejemplo PowerShell (enviar tiempos)

```powershell
$token = '<ACCESS_TOKEN>'
$headers = @{ Authorization = "Bearer $token" }
$body = @{ equipo_id = 1; registros = @( @{ timestamp = (Get-Date).ToString('o'); tiempo = 12345 } ) } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/enviar_tiempos/ -Method Post -Body $body -Headers $headers -ContentType 'application/json'
```

## WebSocket (realtime)

- Endpoint (desarrollo):

```
ws://127.0.0.1:8000/ws/juez/{juez_id}/?token={ACCESS_TOKEN}
```

- El consumer comprueba que el token JWT corresponde a un `User` con `juez_profile` y que `juez_id` coincide.
- Al iniciar la competencia, el servidor envía a cada grupo `juez_{id}` un evento `carrera.iniciada` con un payload `{ mensaje, competencia_id }`.

Importante: pasar tokens en la query string está bien para desarrollo pero no es seguro en producción; considera usar cookies seguras o un handshake.

## Integración móvil (resumen)

Flujo recomendado:

1. Logearse con `/api/token/` y guardar `access` y `refresh` tokens.
2. Abrir WebSocket a `ws://.../ws/juez/{juez_id}/?token={access}` y escuchar `carrera.iniciada`.
3. Al recibir `carrera.iniciada`, comenzar a registrar tiempos localmente.
4. Al finalizar, enviar JSON con hasta 15 registros a `/api/enviar_tiempos/` usando `Authorization: Bearer {access}`.

Detalles y ejemplos de integración están en `docs/INTEGRATION.md` (cliente Python/JS y ejemplos curl/PowerShell).

## Pruebas end-to-end (local)

1. Crear un superuser y desde admin crear `Competencia`, `Juez` y `Equipo`.
2. Asociar `Juez.user` a una cuenta (o usar la migración automática que crea `User` para jueces existentes).
3. Obtener token con `/api/token/`.
4. Conectar WebSocket con token y `juez_id`.
5. Iniciar competencia en admin → cliente WS debe recibir `carrera.iniciada`.
6. Registrar tiempos y POST a `/api/enviar_tiempos/`.
7. Verificar `RegistroTiempo` en admin o base de datos.

## Seguridad y despliegue (recomendaciones)

- Poner `DEBUG=False` y configurar `ALLOWED_HOSTS`.
- Mover `SECRET_KEY` y credenciales a variables de entorno.
- Usar PostgreSQL o MySQL en producción.
- Usar `channels_redis` y Redis para `CHANNEL_LAYERS` en producción.
- Ejecutar con Daphne/Uvicorn y colocar Nginx como reverse proxy (TLS/SSL terminación).
- Evitar tokens en querystring para WebSocket en producción; usar un handshake o cookies seguras.
- Añadir rate-limiting, logging y auditoría.

## Troubleshooting común

- 401 al obtener token: credenciales inválidas.
- 401 al conectar WS: token inválido/expirado.
- 403 al POSTear tiempos: `equipo_id` no pertenece al juez.
- Mensajes WS no entregados en entorno multi-proceso: usar Redis channel layer.

## Archivos clave para revisar

- `app/models.py` — modelos y `RegistroTiempo.save()`.
- `app/admin.py` — admin personalizado que notifica por WebSocket al iniciar competencia.
- `app/consumers.py` — `JuezConsumer` (WebSocket).
- `app/serializers.py` — validación de `EnvioTiemposSerializer`.
- `app/views.py` — `EnviarTiemposView`.
- `server/asgi.py` y `server/settings.py` — configuración ASGI/Channels y DRF.

## Próximos pasos sugeridos

- Añadir pruebas unitarias y de integración.
- Implementar refresh token handling en clientes móviles.
- Mejorar la seguridad del WebSocket para producción.
- Crear `docs/DEPLOY.md` con pasos de despliegue (Docker, Redis, Daphne, Nginx).

---

Si quieres que genere alguno de los siguientes ahora, dime cuál:

- 1) `docs/DEPLOY.md` (playbook de despliegue con Redis + Daphne + Nginx)
- 2) Tests automáticos para `EnviarTiemposView` y `JuezConsumer`
- 3) Ejemplo de cliente Android (Activity + ViewModel) completo

Indica el número (o varios) y lo implemento.
# Server5K

Servidor Django para la aplicación móvil de registro de tiempos en carreras 5K.

Descripción breve
- Esta aplicación provee: administración de competencias, jueces, equipos y registro de tiempos.
- Los jueces son usuarios de Django (vínculo OneToOne `Juez.user`) y se autentican desde la app móvil.
- Se soporta notificaciones en tiempo real (WebSocket via Django Channels) para avisar a los jueces que "la carrera ha iniciado".
- La app móvil registra tiempos localmente y, al finalizar, envía un JSON con hasta 15 registros que el servidor valida y persiste.

Estado actual
- Modelos y migraciones: listos (incluye campos desglosados de tiempo y `Juez.user`).
- Autenticación: JWT con SimpleJWT (endpoints `/api/token/` y `/api/token/refresh/`).
- WebSockets: Channels configurado (InMemory para desarrollo). Consumer `JuezConsumer` implementado en `app/consumers.py`.
- API: endpoint `POST /api/enviar_tiempos/` implementado en `app/views.py` y validado por `app/serializers.py`.

Requisitos
- Python 3.13+
- Paquetes (principales): Django, djangorestframework, channels, djangorestframework-simplejwt, daphne (opcional), websockets (para pruebas).
- En desarrollo se usa SQLite; en producción se recomienda PostgreSQL/MySQL.

Instalación y preparación (PowerShell)
```powershell
cd "c:\Users\darwi\OneDrive\Escritorio\Universidad\Sexto\Software Distribuido\Unidad 1\WorkSpace\Server5K"
# Crear/activar entorno (ejemplo con venv)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependencias (ejemplo mínimo)
pip install -r requirements.txt
# o instalar manualmente si no tienes requirements.txt
pip install django djangorestframework channels djangorestframework-simplejwt daphne websockets

# Aplicar migraciones y crear superuser
python manage.py migrate
python manage.py createsuperuser

# Ejecutar servidor en desarrollo
python manage.py runserver
```

Acceso
- Admin: http://127.0.0.1:8000/admin/

Endpoints principales
- Obtener token (JWT): POST /api/token/  -> retorna { access, refresh }
- Refrescar token: POST /api/token/refresh/
- Enviar tiempos: POST /api/enviar_tiempos/ (autenticado Bearer token)

WebSocket (realtime)
- URL de conexión (ejemplo):
	ws://127.0.0.1:8000/ws/juez/{juez_id}/?token={ACCESS_TOKEN}
- El consumer espera el token JWT en query string (para desarrollo). Valida que el token corresponde al `User` con `juez_profile` y que `juez_id` coincide.
- Al iniciar una competencia desde Admin, el servidor envía un evento `carrera.iniciada` al grupo `juez_{id}`. El payload contiene `data` con `mensaje` y `competencia_id`.

Ejemplo cliente WebSocket (Python)
```python
import asyncio, websockets

async def run():
		token = "<ACCESS_TOKEN>"
		juez_id = "<JUEZ_ID>"
		url = f"ws://127.0.0.1:8000/ws/juez/{juez_id}/?token={token}"
		async with websockets.connect(url) as ws:
				print("Conectado al WS")
				while True:
						msg = await ws.recv()
						print("Recibido:", msg)

asyncio.run(run())
```

Formato JSON para enviar tiempos (payload)
- Endpoint: POST /api/enviar_tiempos/
- Cabecera: Authorization: Bearer <ACCESS_TOKEN>
- Body (ejemplo):
```json
{
	"equipo_id": 1,
	"registros": [
		{ "timestamp": "2025-11-11T12:00:00.000Z", "tiempo": 12345 },
		{ "timestamp": "2025-11-11T12:00:01.000Z", "tiempo": 13345 }
	]
}
```

Notas sobre recepción y validación
- El servidor acepta JSON: el serializer `EnvioTiemposSerializer` valida la estructura y tipos.
- Solo los primeros 15 elementos de `registros` se procesan (si llegan más, se recortan).
- Se valida que `request.user` tenga un `juez_profile` y que el `Equipo` indicado pertenezca al juez (solo puede enviar para su equipo asignado).
- Si la validación pasa, se crean objetos `RegistroTiempo` con `equipo`, `tiempo` y `timestamp`.

¿Se reciben correctamente los datos en JSON?
- Sí: la API espera JSON conforme al formato anterior y los guarda si la validación es correcta. Revisa `app/serializers.py` y `app/views.py` para la lógica exacta.

Pruebas básicas localmente
1. Obtener token con /api/token/ usando un usuario que sea juez.
2. Conectar WebSocket con ese token y el `juez_id`.
3. En Admin iniciar la competencia -> el cliente WS recibirá `carrera.iniciada`.
4. En la app móvil enviar el JSON a /api/enviar_tiempos/ con Authorization header; el servidor guardará hasta 15 registros para el equipo del juez.

Archivos clave para revisar
- `app/models.py` — modelos y lógica de `RegistroTiempo`.
- `app/consumers.py` — WebSocket consumer para jueces.
- `app/serializers.py` — serializers de entrada.
- `app/views.py` — endpoint `EnviarTiemposView`.
- `server/asgi.py` y `server/settings.py` — configuración ASGI/Channels y DRF.

Checklist producción / recomendaciones
- Usar Redis (`channels_redis`) para `CHANNEL_LAYERS`.
- Ejecutar ASGI con Daphne/Uvicorn y colocar Nginx como reverse proxy.
- Poner `DEBUG=False`, configurar `ALLOWED_HOSTS`, mover `SECRET_KEY` a variable de entorno.
- Añadir rate-limiting y validación temporal (evitar registros fuera de la ventana de competencia).
- Añadir logs/auditoría y tests automatizados.

Siguientes pasos:
- Añadir pruebas unitarias para el endpoint y el consumer.
- Crear un `docs/INTEGRATION.md` más detallado para la app móvil con ejemplos.

---
