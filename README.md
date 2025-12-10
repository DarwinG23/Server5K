# Server5K - Sistema de Competencias 5K

Sistema backend para gestión de competencias 5K con registro de tiempos en tiempo real.

## Arquitectura

-   **Django 6.0** + Django REST Framework (API REST)
-   **Django Channels** + Daphne (WebSocket para tiempo real)
-   **PostgreSQL 16** (Base de datos)
-   **Redis 7** (Channel layer para WebSocket)
-   **WhiteNoise** (Archivos estáticos)

---

## 🐳 Despliegue con Docker Compose

El proyecto se despliega con **3 contenedores**:

| Contenedor          | Imagen             | Puerto | Descripción                  |
| ------------------- | ------------------ | ------ | ---------------------------- |
| `server5k-web`      | Build local        | 8000   | Django + Daphne (ASGI)       |
| `server5k-postgres` | postgres:16-alpine | 5432   | Base de datos PostgreSQL     |
| `server5k-redis`    | redis:7-alpine     | 6379   | Channel layer para WebSocket |

### Requisitos

-   **Docker** 20.10+
-   **Docker Compose** 2.0+

### 1. Configurar Variables de Entorno

```bash
# Copiar el archivo de ejemplo
cp .env.docker.example .env

# Editar con tus valores
nano .env  # o usa tu editor preferido
```

**Variables importantes a configurar:**

```env
# Genera una clave segura para producción:
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=tu_clave_secreta_de_50_caracteres

# En producción, cambia a False
DEBUG=False

# Dominios/IPs permitidos (separados por coma)
ALLOWED_HOSTS=midominio.com,192.168.1.100

# Password seguro para PostgreSQL
POSTGRES_PASSWORD=tu_password_super_seguro
```

### 2. Iniciar los Contenedores

```bash
# Construir y levantar todos los servicios
docker compose up -d --build

# Ver logs en tiempo real
docker compose logs -f

# Ver logs de un servicio específico
docker compose logs -f web
```

### 3. Crear Superusuario (Primera vez)

```bash
docker compose exec web python manage.py createsuperuser
```

### 4. Crear Competencia, Jueces y Equipos

El comando `populate_data` crea los datos iniciales necesarios para la competencia:

```bash
# DESARROLLO: Crea 50 jueces con contraseñas simples (juez1123, juez2123, etc.)
docker compose exec web python manage.py populate_data

# PRODUCCIÓN: Crea jueces con contraseñas seguras aleatorias
docker compose exec web python manage.py populate_data --production

# Personalizado: 20 jueces con nombre de competencia específico
docker compose exec web python manage.py populate_data --production --jueces 20 --competencia "5K UNL 2025"

# Limpiar y recrear todo (¡CUIDADO! Elimina datos existentes)
docker compose exec web python manage.py populate_data --clear --production --jueces 30
```

**Opciones disponibles:**

| Opción                   | Descripción                                                             |
| ------------------------ | ----------------------------------------------------------------------- |
| `--production`           | Genera contraseñas seguras aleatorias (12 caracteres)                   |
| `--jueces N`             | Número de jueces/equipos a crear (default: 50, máx: 100)                |
| `--competencia "NOMBRE"` | Nombre personalizado para la competencia                                |
| `--password BASE`        | Contraseña base en desarrollo (ej: `--password pass` → pass1, pass2...) |
| `--clear`                | Elimina todos los datos antes de crear nuevos                           |

**⚠️ IMPORTANTE**: El comando genera un archivo `credenciales_jueces.txt` con todas las contraseñas.

```bash
# Ver las credenciales generadas
docker compose exec web cat credenciales_jueces.txt

# Copiar el archivo a tu máquina local
docker cp server5k-web:/app/credenciales_jueces.txt ./credenciales_jueces.txt
```

### 5. Verificar que todo funciona

-   **API REST**: http://localhost:8000/api/
-   **Admin Django**: http://localhost:8000/admin/
-   **Documentación API**: http://localhost:8000/api/docs/
-   **Health Check**: http://localhost:8000/api/health/

---

## Comandos Útiles

```bash
# Detener todos los contenedores
docker compose down

# Detener y eliminar volúmenes (¡BORRA DATOS!)
docker compose down -v

# Reiniciar un servicio específico
docker compose restart web

# Ejecutar migraciones manualmente
docker compose exec web python manage.py migrate

# Acceder al shell de Django
docker compose exec web python manage.py shell

# Ver estado de los contenedores
docker compose ps

# Reconstruir solo la imagen web
docker compose build web
```

---

## Estructura de Volúmenes

| Volumen              | Contenido             |
| -------------------- | --------------------- |
| `server5k_pgdata`    | Datos de PostgreSQL   |
| `server5k_redisdata` | Datos de Redis        |
| `server5k_static`    | Archivos estáticos    |
| `server5k_media`     | Archivos subidos      |
| `server5k_logs`      | Logs de la aplicación |

---

## API Endpoints Principales

### Autenticación

-   `POST /api/login/` - Login de juez
-   `POST /api/logout/` - Logout
-   `POST /api/token/refresh/` - Refrescar token JWT
-   `GET /api/me/` - Información del juez autenticado

### Competencias

-   `GET /api/competencias/` - Listar competencias
-   `GET /api/competencias/{id}/` - Detalle de competencia

### Equipos

-   `GET /api/equipos/` - Listar equipos del juez
-   `GET /api/equipos/{id}/` - Detalle de equipo

### Registros de Tiempo

-   `POST /api/equipos/{id}/registros/` - Registrar tiempo
-   `GET /api/equipos/{id}/registros/estado/` - Estado de registros

### WebSocket

-   `ws://host:8000/ws/juez/{juez_id}/` - Conexión WebSocket para tiempo real

---

## Producción con HTTPS (Nginx)

Para producción con SSL, agrega Nginx como reverse proxy:

```nginx
server {
    listen 80;
    server_name midominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name midominio.com;

    ssl_certificate /etc/letsencrypt/live/midominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/midominio.com/privkey.pem;

    location /static/ {
        alias /var/www/server5k/staticfiles/;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Nota**: Para habilitar redirección HTTPS en Django, agrega `ENABLE_HTTPS=True` en `.env`.

---

## Desarrollo Local (sin Docker)

Si prefieres desarrollar sin Docker:

```bash
# Instalar dependencias con uv
uv sync

# Activar entorno
source .venv/bin/activate  # Linux/macOS
.\.venv\Scripts\activate   # Windows

# Iniciar PostgreSQL y Redis con Docker
docker compose up -d postgres redis

# Aplicar migraciones
python manage.py migrate

# Iniciar servidor de desarrollo
daphne -b 127.0.0.1 -p 8000 server.asgi:application
```

---

## Troubleshooting

### El contenedor web no inicia

```bash
# Ver logs detallados
docker compose logs web

# Verificar que postgres y redis estén healthy
docker compose ps
```

### Error de conexión a la base de datos

```bash
# Verificar que postgres esté corriendo
docker compose exec postgres pg_isready -U server5k

# Reiniciar postgres
docker compose restart postgres
```

### Problemas con migraciones

```bash
# Ejecutar migraciones manualmente
docker compose exec web python manage.py migrate --noinput
```

---

## Licencia

MIT License
