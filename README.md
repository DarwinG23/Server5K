# Server5K - Sistema de Gestión de Competencias 5K

Sistema completo para gestión de competencias deportivas con registro de tiempos en tiempo real mediante WebSocket.

## 📋 Tabla de Contenidos

-   [Características](#características)
-   [Arquitectura del Proyecto](#arquitectura-del-proyecto)
-   [Requisitos](#requisitos)
-   [Instalación](#instalación)
-   [Configuración](#configuración)
-   [Desarrollo](#desarrollo)
-   [Producción](#producción)
-   [API Documentation](#api-documentation)

## ✨ Características

-   **Autenticación JWT** para jueces
-   **WebSocket en tiempo real** para registro de tiempos
-   **Redis como transport layer** para escalabilidad
-   **API REST completa** con documentación OpenAPI
-   **Panel de administración** personalizado
-   **Servicios de negocio** separados y testeables
-   **Idempotencia** en registros de tiempo
-   **Validación robusta** de datos
-   **Soporte multi-juez** y multi-competencia

## 🏗️ Arquitectura del Proyecto

```
Server5K/
├── app/
│   ├── models/              # Modelos de datos
│   │   ├── competencia.py
│   │   ├── juez.py
│   │   ├── equipo.py
│   │   └── registrotiempo.py
│   ├── websocket/           # WebSocket consumers y routing
│   │   ├── consumers.py
│   │   ├── routing.py
│   │   └── validators.py
│   ├── services/            # Lógica de negocio
│   │   ├── registro_service.py
│   │   ├── competencia_service.py
│   │   └── results_service.py
│   ├── utils/               # Utilidades
│   │   ├── idempotency.py
│   │   └── timestamps.py
│   ├── serializers/         # Serializers DRF
│   ├── views/               # Vistas y ViewSets
│   ├── admin/               # Configuración del admin
│   └── management/          # Comandos personalizados
├── server/
│   ├── settings.py          # Configuración
│   ├── asgi.py             # ASGI application
│   └── urls.py             # URLs principales
├── templates/               # Templates HTML
├── manage.py
└── pyproject.toml          # Dependencias (uv)
```

## 📦 Requisitos

### Desarrollo

-   Python 3.13+
-   uv (gestor de paquetes)
-   SQLite (incluido)

### Producción

-   Python 3.13+
-   PostgreSQL 14+
-   Redis 7+
-   Nginx (reverse proxy)
-   Supervisor o systemd

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <repo-url>
cd Server5K
```

### 2. Crear entorno virtual con uv

```bash
# Instalar uv si no lo tienes
pip install uv

# Crear entorno y instalar dependencias
uv sync
```

### 3. Configurar base de datos

```bash
# Desarrollo (SQLite)
uv run python manage.py migrate

# Producción (ver sección de producción)
```

### 4. Crear superusuario

```bash
uv run python manage.py createsuperuser
```

### 5. Poblar datos de prueba (opcional)

```bash
uv run python manage.py populate_data
```

## ⚙️ Configuración

### Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Base de datos
DB_ENGINE=django.db.backends.postgresql
DB_NAME=server5k
DB_USER=server5k_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

### Configurar Redis en settings.py

Para producción, editar `server/settings.py`:

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(os.environ.get('REDIS_HOST', '127.0.0.1'),
                      int(os.environ.get('REDIS_PORT', 6379)))],
            'capacity': 1500,
            'expiry': 10,
        },
    }
}
```

## 💻 Desarrollo

### Iniciar servidor de desarrollo

```powershell
# Con uv
uv run python manage.py runserver

# O con Daphne (recomendado para WebSocket)
uv run daphne -b 127.0.0.1 -p 8000 server.asgi:application

# O usar el script incluido
.\start_server.ps1
```

### Acceder a la aplicación

-   **API**: http://localhost:8000/api/
-   **Admin**: http://localhost:8000/admin/
-   **Docs API**: http://localhost:8000/api/schema/swagger-ui/
-   **WebSocket**: ws://localhost:8000/ws/juez/{juez_id}/?token={jwt_token}

### Ejecutar tests

```powershell
uv run pytest
uv run pytest --cov=app
```

## 🌐 Producción

### 1. Instalar Redis

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server

# Verificar instalación
redis-cli ping
# Debe responder: PONG

# Configurar Redis para iniciar al arranque
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 2. Instalar PostgreSQL

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# Crear base de datos y usuario
sudo -u postgres psql

CREATE DATABASE server5k;
CREATE USER server5k_user WITH PASSWORD 'your-password';
ALTER ROLE server5k_user SET client_encoding TO 'utf8';
ALTER ROLE server5k_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE server5k_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE server5k TO server5k_user;
\q
```

### 3. Configurar el proyecto

```bash
# Instalar dependencias del sistema
sudo apt install python3.13 python3.13-dev python3-pip build-essential libpq-dev

# Instalar uv
pip install uv

# Clonar y configurar
cd /opt
sudo git clone <repo-url> server5k
cd server5k
sudo chown -R www-data:www-data /opt/server5k

# Instalar dependencias
uv sync

# Configurar variables de entorno
sudo nano /opt/server5k/.env
# (Copiar configuración de producción)

# Migraciones
uv run python manage.py migrate

# Recolectar archivos estáticos
uv run python manage.py collectstatic --noinput

# Crear superusuario
uv run python manage.py createsuperuser
```

### 4. Configurar Daphne con Supervisor

Crear `/etc/supervisor/conf.d/server5k.conf`:

```ini
[program:server5k]
command=/opt/server5k/.venv/bin/daphne -b 127.0.0.1 -p 8000 server.asgi:application
directory=/opt/server5k
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/server5k/daphne.log
stderr_logfile=/var/log/server5k/daphne.error.log
environment=DJANGO_SETTINGS_MODULE="server.settings"
```

Crear directorio de logs:

```bash
sudo mkdir -p /var/log/server5k
sudo chown www-data:www-data /var/log/server5k
```

Iniciar Supervisor:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start server5k
sudo supervisorctl status
```

### 5. Configurar Nginx

Crear `/etc/nginx/sites-available/server5k`:

```nginx
upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirigir a HTTPS (configurar después de obtener certificado SSL)
    # return 301 https://$server_name$request_uri;

    client_max_body_size 100M;

    # Logs
    access_log /var/log/nginx/server5k_access.log;
    error_log /var/log/nginx/server5k_error.log;

    # Archivos estáticos
    location /static/ {
        alias /opt/server5k/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /opt/server5k/media/;
        expires 30d;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://django;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # API y Admin
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

Activar configuración:

```bash
sudo ln -s /etc/nginx/sites-available/server5k /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Configurar SSL con Let's Encrypt (Opcional pero recomendado)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 7. Monitoreo de Redis

```bash
# Ver estadísticas en tiempo real
redis-cli INFO
redis-cli MONITOR

# Ver número de clientes conectados
redis-cli CLIENT LIST

# Ver uso de memoria
redis-cli INFO memory
```

## 📡 Uso de WebSocket

### Conectar desde cliente

```javascript
const token = "your-jwt-access-token";
const juezId = 1;
const ws = new WebSocket(
    `ws://localhost:8000/ws/juez/${juezId}/?token=${token}`
);

ws.onopen = () => {
    console.log("Conectado");
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("Mensaje recibido:", data);
};

// Registrar un tiempo
ws.send(
    JSON.stringify({
        tipo: "registrar_tiempo",
        equipo_id: 5,
        tiempo: 1234567, // milisegundos
        horas: 0,
        minutos: 20,
        segundos: 34,
        milisegundos: 567,
    })
);

// Registrar múltiples tiempos (batch)
ws.send(
    JSON.stringify({
        tipo: "registrar_tiempos",
        equipo_id: 5,
        registros: [
            {
                tiempo: 1234567,
                horas: 0,
                minutos: 20,
                segundos: 34,
                milisegundos: 567,
            },
            // ... más registros (máximo 15)
        ],
    })
);
```

## 📚 API Documentation

La documentación completa de la API está disponible en:

-   **Swagger UI**: `/api/schema/swagger-ui/`
-   **ReDoc**: `/api/schema/redoc/`
-   **OpenAPI Schema**: `/api/schema/`

### Endpoints principales

#### Autenticación

-   `POST /api/login/` - Iniciar sesión
-   `POST /api/logout/` - Cerrar sesión
-   `POST /api/refresh/` - Refrescar token
-   `GET /api/me/` - Información del juez autenticado

#### Competencias

-   `GET /api/competencias/` - Listar competencias
-   `GET /api/competencias/{id}/` - Detalle de competencia

#### Equipos

-   `GET /api/equipos/` - Listar equipos
-   `GET /api/equipos/{id}/` - Detalle de equipo

## 🔧 Comandos útiles

```powershell
# Crear datos de prueba
uv run python manage.py populate_data

# Limpiar registros antiguos
uv run python manage.py shell
>>> from app.utils.idempotency import limpiar_registros_antiguos
>>> count = limpiar_registros_antiguos(dias=90)
>>> print(f"Eliminados {count} registros")

# Ver estadísticas de Redis
redis-cli INFO stats

# Limpiar Redis (¡CUIDADO!)
redis-cli FLUSHALL

# Ver logs de Daphne (Linux)
sudo tail -f /var/log/server5k/daphne.log
```

## 🐛 Troubleshooting

### Redis no conecta

```bash
# Verificar que Redis está corriendo
sudo systemctl status redis-server

# Verificar puerto
sudo netstat -tulpn | grep 6379

# Ver logs
sudo journalctl -u redis-server -f
```

### WebSocket no conecta

1. Verificar que Daphne está corriendo
2. Verificar configuración de Nginx para WebSocket
3. Revisar logs: `sudo tail -f /var/log/nginx/server5k_error.log`
4. Verificar que el token JWT es válido

### Errores de base de datos

```bash
# Ver conexiones activas
sudo -u postgres psql server5k -c "SELECT * FROM pg_stat_activity;"

# Reiniciar PostgreSQL
sudo systemctl restart postgresql
```

## 📝 Notas de Seguridad

-   Cambiar `SECRET_KEY` en producción
-   Configurar `ALLOWED_HOSTS` apropiadamente
-   Usar HTTPS en producción
-   Configurar firewall (UFW) para permitir solo puertos necesarios
-   Actualizar dependencias regularmente: `uv sync --upgrade`
-   Hacer backups regulares de la base de datos y Redis

## 📄 Licencia

[Especificar licencia]

## 👥 Contribución

[Instrucciones de contribución]

## 📞 Soporte

[Información de contacto]
