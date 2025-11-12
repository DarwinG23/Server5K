from django.urls import path
from .views import EnviarTiemposView

urlpatterns = [
    path('enviar_tiempos/', EnviarTiemposView.as_view(), name='enviar_tiempos'),
]
