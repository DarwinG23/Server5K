"""
Módulo: routing
Configuración de rutas WebSocket para la aplicación.
"""

from django.urls import re_path
from .consumers import JuezConsumer

websocket_urlpatterns = [
    re_path(r'ws/juez/(?P<juez_id>[^/]+)/$', JuezConsumer.as_asgi()),
]
