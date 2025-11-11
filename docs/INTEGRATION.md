# Integration guide for the mobile app

This document explains how the mobile application should authenticate, connect to WebSocket notifications and send time records JSON to the Server5K backend.

All examples use the local development host `127.0.0.1:8000`. Replace with your server domain in production.

---

## Overview

- Mobile app flow:
  1. Judge user authenticates and obtains a JWT access token.
 2. App opens a WebSocket to receive the `carrera.iniciada` event for its judge id.
 3. When the race starts, the judge records times locally.
 4. At the end, the app sends a JSON payload with up to the first 15 records to the REST endpoint.

## Endpoints

- Obtain token (POST): `/api/token/` — send `username` and `password` JSON, receives `{ access, refresh }`.
- Refresh token (POST): `/api/token/refresh/` — send `refresh` token JSON.
- Send times (POST): `/api/enviar_tiempos/` — protected endpoint, requires `Authorization: Bearer <access>` header.

## WebSocket

- URL pattern (development):

  `ws://127.0.0.1:8000/ws/juez/{juez_id}/?token={ACCESS_TOKEN}`

- Notes:
  - For development we pass the JWT in the query string. In production avoid query string tokens (they can be logged) — prefer a secure cookie or a handshake endpoint.
  - The consumer validates the token and requires that the token's user has a `juez_profile` whose id equals `{juez_id}` used in the path.

### Example: connect with Python (websockets)

```python
import asyncio, websockets

async def run():
    token = "<ACCESS_TOKEN>"
    juez_id = "<JUEZ_ID>"
    url = f"ws://127.0.0.1:8000/ws/juez/{juez_id}/?token={token}"
    async with websockets.connect(url) as ws:
        print("Connected")
        while True:
            msg = await ws.recv()
            print("Received:", msg)

asyncio.run(run())
```

### Example: connect with JavaScript (browser)

```js
const token = '<ACCESS_TOKEN>';
const juezId = '<JUEZ_ID>';
const url = `ws://127.0.0.1:8000/ws/juez/${juezId}/?token=${token}`;
const socket = new WebSocket(url);

socket.onopen = () => console.log('WS open');
socket.onmessage = (e) => console.log('WS message', e.data);
socket.onclose = () => console.log('WS closed');
```

## Payload: sending time records (JSON)

- Request: POST `/api/enviar_tiempos/`
- Headers: `Authorization: Bearer <ACCESS_TOKEN>` and `Content-Type: application/json`
- Body schema:

```json
{
  "equipo_id": 1,
  "registros": [
    { "timestamp": "2025-11-11T12:00:00.000Z", "tiempo": 12345 },
    { "timestamp": "2025-11-11T12:00:01.000Z", "tiempo": 13345 }
  ]
}
```

- `timestamp`: ISO 8601 string. The backend uses this to store `timestamp` on `RegistroTiempo`.
- `tiempo`: integer milliseconds (total ms). The model will compute components or accept them as provided.
- Only the first 15 entries in `registros` are processed; extras are ignored.

### Example: curl

```bash
ACCESS_TOKEN="<ACCESS_TOKEN>"
curl -X POST http://127.0.0.1:8000/api/enviar_tiempos/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "equipo_id": 1, "registros": [ { "timestamp": "2025-11-11T12:00:00.000Z", "tiempo": 12345 } ] }'
```

### Example: PowerShell (Invoke-RestMethod)

```powershell
$token = '<ACCESS_TOKEN>'
$headers = @{ Authorization = "Bearer $token" }
$body = @{
  equipo_id = 1
  registros = @(
    @{ timestamp = (Get-Date).ToString('o'); tiempo = 12345 }
  )
} | ConvertTo-Json

Invoke-RestMethod -Uri http://127.0.0.1:8000/api/enviar_tiempos/ -Method Post -Body $body -Headers $headers -ContentType 'application/json'
```

## Server validation rules (summary)

- The API requires an authenticated JWT `request.user`.
- The user must have an associated `juez_profile` (created by the admin or migrations).
- The `equipo_id` must refer to a team whose `juez_asignado` is that judge — otherwise the request is rejected with 403.
- Only the first 15 `registros` are processed.

## Mobile recommended flow

1. Authenticate using username/password → store the returned `access` (short-lived) and `refresh` tokens securely.
2. Open a WebSocket to `ws://.../ws/juez/{juez_id}/?token={access}` and listen for `carrera.iniciada`.
3. On `carrera.iniciada`, start local recording of times (use device clock; consider monotonic timers).
4. When the run ends, prepare the JSON payload limited to the first 15 entries and POST to `/api/enviar_tiempos/` with `Authorization: Bearer {access}`.
5. If access token expired, use `refresh` to obtain new access token and retry.

## Testing locally

- Steps to simulate an end-to-end flow on your dev machine:
  1. Create a superuser and create a `Competencia`, `Juez` and `Equipo` in admin.
  2. Make sure the `Juez` has a linked `User` (migration creates users for existing judges or link manually in admin).
  3. Obtain JWT with `/api/token/` using the judge's username/password.
  4. Start the Python JS WebSocket example — it should connect.
  5. In admin, click ▶️ Iniciar on the `Competencia` — the WS client receives `carrera.iniciada`.
  6. POST the `enviar_tiempos` payload — check admin or DB that `RegistroTiempo` objects were created.

## Security considerations

- Querystring tokens are convenient for development but not ideal for production. Consider using a cookie-based auth or a handshake endpoint that exchanges a short-lived socket token.
- Use HTTPS/WSS in production.
- Store secrets and `SECRET_KEY` in environment variables. Set `DEBUG=False` and configure `ALLOWED_HOSTS`.
- Add rate limiting to the API to protect from misuse.

## Troubleshooting

- `401 Unauthorized` when connecting WS: token invalid or expired. Get a fresh `access` token and reconnect.
- `403 Forbidden` when POSTing times: check `equipo_id` is assigned to the judge user sending the request.
- No WS message on start: ensure the admin action triggers the group send (server logs, channel layer working). For dev the in-memory layer is used; verify process is the same (runserver). For multiple processes use Redis channel layer.

## Next steps (recommended)

- Use Redis (`channels_redis`) for scale and reliability.
- Implement secure WS auth (cookie or handshake) for production.
- Add unit/integration tests for the endpoint and consumer.
- Document the expected JSON error responses for the client.

---

If you want, I can also add example client code in Kotlin/Swift/React Native for the mobile app. Tell me the target platform and I create a small snippet.

*** End Patch