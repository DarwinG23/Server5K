"""
Módulo: equipo_views
ViewSets relacionados con la gestión de equipos.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from app.serializers import EquipoSerializer
from app.models import Equipo


class EquipoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para Equipos (solo lectura)
    
    Permite listar todos los equipos y obtener detalles de un equipo específico.
    
    Filtros disponibles:
    - ?competencia_id={id} - Filtra equipos por competencia
    - ?juez_id={id} - Filtra equipos por juez asignado
    """
    queryset = Equipo.objects.select_related(
        'judge',
        'competition'
    ).all().order_by('number')
    serializer_class = EquipoSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Listar equipos",
        description="Obtiene todos los equipos con filtros opcionales",
        parameters=[
            OpenApiParameter(
                name='competencia_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filtrar por ID de competencia',
                required=False,
            ),
            OpenApiParameter(
                name='juez_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filtrar por ID de juez',
                required=False,
            ),
        ],
        responses={200: EquipoSerializer(many=True)},
        tags=['Equipos']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Obtener equipo",
        description="Obtiene los detalles de un equipo específico por ID",
        responses={
            200: EquipoSerializer,
            404: {'description': 'Equipo no encontrado'},
        },
        tags=['Equipos']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Permite filtrar equipos por competition_id y judge_id.
        Solo retorna los equipos asignados al juez autenticado.
        """
        queryset = super().get_queryset()
        
        # Filtrar por equipos asignados al juez autenticado
        juez = self.request.user
        queryset = queryset.filter(judge_id=juez.id)
        
        # Filtro por competencia (opcional, ya está filtrado por juez)
        competition_id = self.request.query_params.get('competition_id')
        if competition_id:
            queryset = queryset.filter(competition_id=competition_id)
        
        # Filtro por juez (opcional, redundante pero se mantiene para compatibilidad)
        judge_id = self.request.query_params.get('judge_id')
        if judge_id:
            queryset = queryset.filter(judge_id=judge_id)
        
        return queryset
