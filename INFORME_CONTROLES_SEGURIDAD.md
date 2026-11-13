# Informe de controles de seguridad: autorización, sesiones y JWT

## 1. Objetivo

Este informe documenta la revisión y las pruebas realizadas sobre los
controles de seguridad relacionados con:

- autorización por objeto para prevenir vulnerabilidades IDOR;
- control de acceso entre jueces y administradores;
- expiración de tokens de sesión;
- validación de la firma de tokens JWT en el servidor.

La implementación corresponde al backend Django REST Framework del proyecto
Server5K.

## 2. Actividad 1: controles recomendados

### 2.1 Verificación de autorización por objeto

Se revisaron los endpoints que reciben identificadores de recursos mediante la
URL. El riesgo consiste en que un usuario autenticado modifique, por ejemplo,
`/api/equipos/1/` a `/api/equipos/2/` para consultar o modificar un recurso
perteneciente a otro usuario.

La autorización se implementó en dos niveles:

1. El `EquipoViewSet` limita el `queryset` a los equipos asignados al juez
   autenticado.
2. `EstadoEquipoRegistrosView` busca el equipo usando simultáneamente el
   identificador recibido y el identificador del juez autenticado.

Archivos relevantes:

- `app/views/equipo_views.py`
- `app/views/registro_views.py`

La consulta protegida quedó implementada así:

```python
equipo = Equipo.objects.get(id=equipo_id, judge_id=juez.id)
```

Cuando se intenta acceder a un equipo ajeno, el servidor responde `404 Not
Found`, evitando revelar información sobre el recurso.

### 2.2 Expiración de sesión

El proyecto utiliza tokens JWT para autenticar las peticiones de la API. La
duración se configura en `server/settings.py`:

```python
'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
```

Por lo tanto:

- el token de acceso expira después de 60 minutos;
- el token de renovación expira después de 7 días.

Después de la expiración, una petición protegida debe responder `401
Unauthorized`.

### 2.3 Validación de firma JWT

La autenticación global está configurada en `server/settings.py` mediante:

```python
'app.auth.authentication.JuezJWTAuthentication'
```

La clase personalizada se encuentra en
`app/auth/authentication.py` y hereda de `JWTAuthentication` de
SimpleJWT. La configuración de firma utiliza:

```python
'ALGORITHM': 'HS256',
'SIGNING_KEY': SECRET_KEY,
```

El servidor verifica la firma antes de aceptar el token. Si se altera
cualquier parte del token, la petición es rechazada con `401 Unauthorized`.

## 3. Actividad 2: laboratorio IDOR

### 3.1 Datos de prueba

Las pruebas crean:

- juez A: `juez-a`;
- juez B: `juez-b`;
- equipo A asignado al juez A;
- equipo B asignado al juez B;
- un registro de tiempo asociado al equipo B.

El juez A se autentica y posteriormente intenta acceder a los recursos del
juez B modificando el identificador del equipo en la URL.

### 3.2 Prueba IDOR 1: detalle de equipo

**Petición:**

```text
GET /api/equipos/{id_del_equipo_B}/
Authorization: Bearer <token_del_juez_A>
```

**Resultado esperado:** `404 Not Found`.

**Resultado obtenido:** `404 Not Found`.

**Corrección:** `EquipoViewSet.get_queryset()` filtra los equipos mediante
`judge_id=juez.id`, por lo que el detalle de un equipo ajeno no aparece en el
queryset.

Prueba automatizada:

```text
test_juez_cannot_retrieve_another_juez_team
```

### 3.3 Prueba IDOR 2: estado de registros

**Petición:**

```text
GET /api/equipos/{id_del_equipo_B}/registros/estado/
Authorization: Bearer <token_del_juez_A>
```

**Resultado esperado:** `404 Not Found`.

**Resultado obtenido:** `404 Not Found`.

**Corrección:** `EstadoEquipoRegistrosView` busca el equipo con la condición
`id=equipo_id` y `judge_id=juez.id`. De esta manera, no devuelve los registros
de un equipo asignado a otro juez.

Prueba automatizada:

```text
test_juez_cannot_read_another_juez_records_status
```

### 3.4 Prueba IDOR 3: envío de registros

**Petición:**

```text
POST /api/equipos/{id_del_equipo_B}/registros/
Authorization: Bearer <token_del_juez_A>
```

El cuerpo contiene 15 registros de prueba.

**Resultado esperado:** `403 Forbidden`.

**Resultado obtenido:** `403 Forbidden`.

**Corrección:** `RegistrarTiemposView` comprueba que `equipo.judge_id` coincida
con `juez.id` antes de guardar registros. También se verificó que el número de
registros del equipo B no aumentara.

Prueba automatizada:

```text
test_juez_cannot_submit_records_for_another_juez_team
```

## 4. Verificación de roles

El endpoint utilizado por la interfaz administrativa es:

```text
GET /api/admin/estado-competencias/
```

Anteriormente estaba declarado con `AllowAny`. Se corrigió para utilizar:

```python
authentication_classes = [SessionAuthentication]
permission_classes = [IsAdminUser]
```

Resultados:

| Usuario | Resultado |
|---|---:|
| Juez común autenticado | `403 Forbidden` |
| Usuario administrador Django (`staff`) | `200 OK` |

Pruebas automatizadas:

```text
test_admin_endpoint_rejects_common_user
test_admin_endpoint_accepts_staff_session
```

## 5. Verificación de tokens

### 5.1 Token alterado

Se obtuvo un token válido, se modificó su último carácter y se solicitó:

```text
GET /api/me/
Authorization: Bearer <token_alterado>
```

**Resultado:** `401 Unauthorized`.

Prueba automatizada:

```text
test_tampered_access_token_is_rejected
```

### 5.2 Token expirado

Se generó un token con fecha de expiración pasada y se solicitó:

```text
GET /api/me/
Authorization: Bearer <token_expirado>
```

**Resultado:** `401 Unauthorized`.

Prueba automatizada:

```text
test_expired_access_token_is_rejected
```

## 6. Ejecución de las pruebas

Desde la raíz del proyecto se ejecutó:

```powershell
.\.venv\Scripts\python.exe manage.py test app.tests.tests --verbosity 2
```

También se ejecutó la suite de la aplicación:

```powershell
.\.venv\Scripts\python.exe manage.py test app --verbosity 1
```

Resultado final:

```text
Ran 7 tests
OK
```

Las siete pruebas verificadas fueron:

1. acceso administrativo válido;
2. rechazo de juez común en endpoint administrativo;
3. rechazo de token expirado;
4. rechazo de consulta de registros ajenos;
5. rechazo de consulta de equipo ajeno;
6. rechazo de envío de registros a equipo ajeno;
7. rechazo de token alterado.

## 7. Cómo visualizar la evidencia

### Opción A: pruebas automatizadas

Ejecutar el comando de pruebas y capturar la terminal mostrando `Ran 7 tests`
 y `OK`.

### Opción B: documentación de la API

Iniciar el servidor y abrir:

```text
http://localhost:8000/api/docs/
```

En Swagger:

1. ejecutar `POST /api/login/`;
2. copiar el campo `access`;
3. pulsar **Authorize** y escribir `Bearer <access>`;
4. consultar un equipo propio;
5. cambiar manualmente el identificador por el de otro juez;
6. comprobar que la respuesta sea `404` o `403`;
7. probar `GET /api/me/` con un token alterado para observar `401`.

## 8. Figuras sugeridas y ubicación

Las siguientes figuras deben insertarse en el informe académico o en la
presentación. Los nombres ya están definidos para mantener una nomenclatura
consistente.

| Figura | Nombre o título | Ubicación sugerida |
|---|---|---|
| Figura 1 | Configuración global de autenticación JWT | Después de la sección 2.3, mostrando `server/settings.py` |
| Figura 2 | Configuración de expiración de tokens JWT | Después de la sección 2.2, mostrando `ACCESS_TOKEN_LIFETIME` y `REFRESH_TOKEN_LIFETIME` |
| Figura 3 | Autorización por objeto en equipos | Después de la sección 2.1, mostrando el filtro `judge_id=juez.id` |
| Figura 4 | Protección del estado de registros contra IDOR | Después de la sección 3.3, mostrando la consulta restringida |
| Figura 5 | Prueba IDOR de consulta de equipo ajeno | Después de la sección 3.2, mostrando la URL alterada y respuesta `404` |
| Figura 6 | Prueba IDOR de consulta de registros ajenos | Después de la sección 3.3, mostrando la respuesta `404` |
| Figura 7 | Prueba IDOR de envío no autorizado | Después de la sección 3.4, mostrando la respuesta `403` |
| Figura 8 | Control de acceso entre juez y administrador | Después de la sección 4, mostrando `403` para juez y `200` para administrador |
| Figura 9 | Rechazo de token JWT alterado | Después de la sección 5.1, mostrando la respuesta `401` |
| Figura 10 | Rechazo de token JWT expirado | Después de la sección 5.2, mostrando la respuesta `401` |
| Figura 11 | Ejecución exitosa de las pruebas de seguridad | Después de la sección 6, mostrando `Ran 7 tests` y `OK` |
| Figura 12 | Documentación Swagger de endpoints protegidos | Después de la sección 7, mostrando `/api/docs/` y el botón **Authorize** |

### Recomendación para las capturas

Cada captura debe mostrar únicamente datos de prueba. No se deben incluir
contraseñas reales, tokens completos, claves secretas ni información personal.
Si aparece un JWT en la captura, se debe ocultar la mayor parte del valor.

## 9. Conclusión

La revisión confirmó que los endpoints protegidos requieren autenticación,
que los jueces no pueden acceder a equipos o registros de otros jueces y que
el endpoint administrativo distingue entre un juez común y un administrador.
También se comprobó que la expiración y la firma de los tokens JWT son
validadas por el servidor.

El principal hallazgo corregido fue el acceso no autorizado al estado de
registros mediante la alteración del identificador `equipo_id`. La corrección
aplicó autorización por objeto directamente en la consulta de base de datos y
se validó con pruebas automatizadas.
