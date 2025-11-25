"""
Módulo: competencia_views
ViewSets relacionados con la gestión de competencias.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from app.serializers import CompetenciaSerializer
from app.models import Competencia


class CompetenciaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para Competencias (solo lectura)
    
    Permite listar todas las competencias y obtener detalles de una competencia específica.
    
    Filtros disponibles:
    - ?activa=true/false - Filtra por competencias activas
    - ?en_curso=true/false - Filtra por competencias en curso
    """
    queryset = Competencia.objects.all().order_by('-datetime')
    serializer_class = CompetenciaSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Listar competencias",
        description="Obtiene todas las competencias con filtros opcionales",
        parameters=[
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filtrar por competencias activas (true/false)',
                required=False,
            ),
            OpenApiParameter(
                name='is_running',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filtrar por competencias en curso (true/false)',
                required=False,
            ),
        ],
        responses={200: CompetenciaSerializer(many=True)},
        tags=['Competencias']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Obtener competencia",
        description="Obtiene los detalles de una competencia específica por ID",
        responses={
            200: CompetenciaSerializer,
            404: {'description': 'Competencia no encontrada'},
        },
        tags=['Competencias']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Permite filtrar competencias por is_active y is_running.
        Solo retorna la competencia del equipo asignado al juez autenticado.
        """
        queryset = super().get_queryset()
        
        # Filtrar por la competencia del equipo del juez autenticado
        juez = self.request.user
        if hasattr(juez, 'team') and juez.team:
            queryset = queryset.filter(id=juez.team.competition_id)
        else:
            # Si el juez no tiene equipo asignado, no mostrar ninguna competencia
            queryset = queryset.none()
        
        # Filtro por is_active
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Filtro por is_running
        is_running = self.request.query_params.get('is_running')
        if is_running is not None:
            is_running_bool = is_running.lower() == 'true'
            queryset = queryset.filter(is_running=is_running_bool)
        
        return queryset
