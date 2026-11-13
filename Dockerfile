# ============================================================================
# Dockerfile para Server5K - Django + Daphne (ASGI)
# ============================================================================
FROM python:3.13-slim


# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app


# Directorio de trabajo
WORKDIR /app


# Instalar dependencias del sistema (incluye curl para healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*


# Instalar uv para manejo de paquetes
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv


# Copiar archivos de dependencias
COPY pyproject.toml ./
COPY requirements.txt ./


# Instalar dependencias con uv
RUN uv pip install --system --no-cache -r requirements.txt


# Copiar el código de la aplicación
COPY . .


# Crear directorios necesarios
RUN mkdir -p /app/logs /app/staticfiles /app/mediafiles


# Recolectar archivos estáticos
RUN python manage.py collectstatic --noinput --skip-checks


# Puerto de la aplicación
EXPOSE 8000


# Comando por defecto: Daphne (ASGI server para WebSocket + HTTP)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "server.asgi:application"]
