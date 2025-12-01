from django.urls import path, include
from rest_framework.routers import DefaultRouter
from app.views import (
    LoginView,
    LogoutView,
    MeView,
    RefreshTokenView,
    CompetenciaViewSet,
    EquipoViewSet,
    EstadoCompetenciaAdminView,
)

# Router de DRF para ViewSets
router = DefaultRouter()
router.register(r'competencias', CompetenciaViewSet, basename='competencia')
router.register(r'equipos', EquipoViewSet, basename='equipo')

urlpatterns = [
    # Autenticación
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('token/refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    
    # Endpoint público para admin (sin autenticación)
    path('admin/estado-competencias/', EstadoCompetenciaAdminView.as_view(), name='admin_estado_competencias'),
    
    # Incluir rutas del router (Competencias y Equipos)
    path('', include(router.urls)),
]
