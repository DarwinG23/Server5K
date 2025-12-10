# Server5K - Guía de Despliegue en Producción

Sistema backend para gestión de competencias 5K con registro de tiempos en tiempo real.

## Arquitectura

-   **Django 5.x** + Django REST Framework (API REST)
-   **Django Channels** + Daphne (WebSocket para tiempo real)
-   **PostgreSQL 16** (Base de datos)
-   **Redis 7** (Channel layer para WebSocket)
-   **WhiteNoise** (Archivos estáticos)

## Requisitos del Servidor

-   **Docker** y **Docker Compose**
-   **Python 3.13+**
-   **Git**
-   **uv** (recomendado) o **pip**

---

## 1. Clonar el Repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd Server5K
```

---

## 2. Configurar Variables de Entorno

Copia el archivo de ejemplo y edítalo con tus valores:

```bash
cp .env.example .env
```

Edita `.env` con tus configuraciones:

```env
# IMPORTANTE: Genera una nueva SECRET_KEY para producción
SECRET_KEY=tu_clave_secreta_super_segura

# Configuración de Django
DEBUG=False
ALLOWED_HOSTS=midominio.com,api.midominio.com,192.168.0.108

# Base de datos PostgreSQL
POSTGRES_DB=server5k
POSTGRES_USER=server5k
POSTGRES_PASSWORD=tu_password_seguro
POSTGRES_HOST=localhost
POSTGRES_PORT=5433

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# CORS (producción)
CORS_ALLOWED_ORIGINS=http://midominio.com,http://app.midominio.com
```

### Generar SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 3. Iniciar Servicios con Docker

```bash
docker-compose up -d
```

Esto iniciará:

-   **PostgreSQL** en el puerto 5433
-   **Redis** en el puerto 6379

### Verificar servicios

```bash
docker-compose ps
docker-compose logs -f
```

---

## 4. Configurar Entorno Python

### Opción A: Con uv (recomendado)

```bash
# Instalar uv si no lo tienes
pip install uv

# Crear entorno e instalar dependencias
uv sync

# Activar entorno
# Linux/macOS:
source .venv/bin/activate
# Windows:
.\.venv\Scripts\activate
```

### Opción B: Con pip

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .\.venv\Scripts\activate  # Windows

pip install -e .
```

---

## 5. Preparar la Aplicación Django

```bash
# Aplicar migraciones
python manage.py migrate

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# (Opcional) Crear superusuario
python manage.py createsuperuser

# (Opcional) Cargar datos de prueba
python manage.py populate_data
```

---

## 6. Iniciar el Servidor

### Desarrollo (LAN local)

```bash
daphne -b 0.0.0.0 -p 8000 server.asgi:application
```

### Producción con múltiples workers

```bash
daphne -b 0.0.0.0 -p 8000 --verbosity 1 server.asgi:application
```

La aplicación estará disponible en: `http://<IP_DEL_SERVIDOR>:8000`

---

## 7. (Opcional) Nginx como Reverse Proxy

Para producción robusta, usa Nginx delante de Daphne:

```nginx
# /etc/nginx/sites-available/server5k
server {
    listen 80;
    server_name midominio.com;

    location = /favicon.ico { access_log off; log_not_found off; }

    # Archivos estáticos
    location /static/ {
        alias /ruta/a/Server5K/staticfiles/;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # HTTP
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Habilitar y reiniciar:

```bash
sudo ln -s /etc/nginx/sites-available/server5k /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 8. (Opcional) Systemd Service

Para mantener el servidor corriendo como servicio:

```ini
# /etc/systemd/system/server5k.service
[Unit]
Description=Server5K Daphne ASGI Server
After=network.target docker.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/ruta/a/Server5K
Environment="PATH=/ruta/a/Server5K/.venv/bin"
EnvironmentFile=/ruta/a/Server5K/.env
ExecStart=/ruta/a/Server5K/.venv/bin/daphne -b 127.0.0.1 -p 8000 server.asgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable server5k
sudo systemctl start server5k
sudo systemctl status server5k
```

---

## Endpoints Principales

| Endpoint              | Descripción                    |
| --------------------- | ------------------------------ |
| `/admin/`             | Panel de administración Django |
| `/api/docs/`          | Documentación Swagger UI       |
| `/api/redoc/`         | Documentación ReDoc            |
| `/api/`               | Endpoints de la API REST       |
| `/ws/juez/<juez_id>/` | WebSocket para jueces          |

---

## Comandos Útiles

```bash
# Ver logs de Docker
docker-compose logs -f

# Reiniciar servicios
docker-compose restart

# Backup de base de datos
docker exec server5k-postgres pg_dump -U server5k server5k > backup.sql

# Restaurar backup
cat backup.sql | docker exec -i server5k-postgres psql -U server5k server5k

# Verificar WebSocket/Redis
python manage.py shell
>>> from channels.layers import get_channel_layer
>>> channel_layer = get_channel_layer()
>>> print(channel_layer)
```

---

## Solución de Problemas

### Error de conexión a PostgreSQL

-   Verifica que Docker esté corriendo: `docker-compose ps`
-   Verifica las variables de entorno en `.env`

### Error de conexión a Redis

-   Verifica el contenedor: `docker exec server5k-redis redis-cli ping`
-   Debe responder `PONG`

### WebSocket no conecta

-   Verifica que Daphne esté corriendo
-   Verifica logs: `docker-compose logs redis`
-   Verifica que el token JWT sea válido

---

## Licencia

Proyecto privado - Todos los derechos reservados.
