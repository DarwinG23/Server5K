# Server5K

Aplicación Django para gestionar competencias de relevos 5K con registro de tiempos por equipo. El proyecto ofrece un panel administrativo para crear competencias, asignar jueces, cargar equipos y almacenar tiempos capturados durante la carrera.

-   **Competencias** con fecha, categoría y estado activo.
-   **Jueces** vinculados a cada competencia que registran equipos asignados.
-   **Equipos** identificados por dorsal y asociados a un juez específico.
-   **Registros de tiempo** almacenados con identificadores UUID, marca temporal y milisegundos.

## Requisitos

-   Python 3.13
-   uv (gestor de entornos y dependencias)
-   SQLite (por defecto) o cualquier base soportada por Django

## Configuración del proyecto

```powershell
# 1. Crear y activar el entorno
uv venv
uv sync

# 2. Ejecutar migraciones
uv run python manage.py migrate

# 3. Crear superusuario (opcional)
uv run python manage.py createsuperuser

# 4. Ejecutar el servidor de desarrollo
uv run python manage.py runserver
```

La aplicación estará disponible en `http://127.0.0.1:8000/`. Accede al panel de administración en `http://127.0.0.1:8000/admin/`.

## Variables de entorno útiles

-   `SECRET_KEY`: clave de Django para despliegues.
-   `DEBUG`: establecer en `False` en producción.
-   `ALLOWED_HOSTS`: dominios permitidos cuando `DEBUG=False`.

## Estructura principal

```
app/
├── admin.py        # Registro de modelos en el panel de administración
├── models.py       # Competencia, Juez, Equipo y RegistroTiempo
├── views.py        # Vistas (por implementar)
└── migrations/     # Migraciones de base de datos

server/             # Configuración del proyecto Django
```

## Próximos pasos

-   Implementar vistas y formularios para gestionar competencias y registros desde la interfaz pública.
-   Añadir pruebas automatizadas en `app/tests.py`.
-   Configurar despliegue (Gunicorn, Nginx, etc.) cuando el proyecto esté listo para producción.
