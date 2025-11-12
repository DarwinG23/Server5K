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

mensajeria/         # Comunicación distribuida con MQTT
```

## Módulo Mensajería

El módulo `mensajeria` implementa la comunicación distribuida del sistema de registro de tiempos de la carrera atlética de 5 km organizada por la Universidad Nacional de Loja.

Utiliza el protocolo MQTT (con el broker Mosquitto) para permitir que los jueces envíen los tiempos de llegada de los atletas hacia el servidor central Django, incluso en entornos con conectividad limitada o sin Internet.

El sistema funciona de forma local (LAN/Wi-Fi), garantizando tolerancia a fallos y sincronización eventual.

### ⚙️ Componentes principales

| Archivo       | Descripción |
|---------------|-------------|
| `mqtt_client.py` | Cliente MQTT que escucha los mensajes publicados por los jueces en la red y los almacena en la base de datos Django (`RegistroTiempo`). |
| `runmqtt.py` | Comando personalizado de Django para ejecutar el cliente MQTT desde la línea de comandos. |

### Uso

Para usar el módulo de mensajería:

1. **Instalar dependencias adicionales**:
   ```bash
   pip install paho-mqtt
   ```

2. **Asegurarse de que Mosquitto esté corriendo**:
   - Instala Mosquitto si no lo tienes: `sudo apt install mosquitto` (en Ubuntu/Debian).
   - Inicia el broker: `mosquitto` (corre en localhost:1883 por defecto).

3. **Ejecutar el cliente MQTT**:
   ```bash
    python manage.py runmqtt
   ```

El comando inicia el cliente MQTT que se conecta al broker local, se suscribe al tópico `carrera/registro/#` y procesa los mensajes entrantes de los jueces. Los tiempos se almacenan automáticamente en la base de datos como registros `RegistroTiempo`.

## Próximos pasos

-   Implementar vistas y formularios para gestionar competencias y registros desde la interfaz pública.
-   Añadir pruebas automatizadas en `app/tests.py`.
-   Configurar despliegue (Gunicorn, Nginx, etc.) cuando el proyecto esté listo para producción.
