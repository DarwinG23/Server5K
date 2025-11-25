"""
ASGI config for server project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

# Obtener la aplicación ASGI de Django PRIMERO (esto inicializa Django)
django_asgi_app = get_asgi_application()

# DESPUÉS importar componentes que dependen de Django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from app.websocket.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
	"http": django_asgi_app,
	"websocket": AuthMiddlewareStack(
		URLRouter(
			websocket_urlpatterns
		)
	),
})
