from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/juez/(?P<juez_id>[^/]+)/$', consumers.JuezConsumer.as_asgi()),
]
