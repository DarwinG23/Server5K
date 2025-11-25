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
    queryset = Competencia.objects.all().order_by('-fecha_hora')
    serializer_class = CompetenciaSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Listar competencias",
        description="Obtiene todas las competencias con filtros opcionales",
        parameters=[
            OpenApiParameter(
                name='activa',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filtrar por competencias activas (true/false)',
                required=False,
            ),
            OpenApiParameter(
                name='en_curso',
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
        Permite filtrar competencias por activa y en_curso.
        Solo retorna la competencia del juez autenticado.
        """
        queryset = super().get_queryset()
        
        # Filtrar por la competencia del juez autenticado
        juez = self.request.user
        queryset = queryset.filter(id=juez.competencia_id)
        
        # Filtro por activa
        activa = self.request.query_params.get('activa')
        if activa is not None:
            activa_bool = activa.lower() == 'true'
            queryset = queryset.filter(activa=activa_bool)
        
        # Filtro por en_curso
        en_curso = self.request.query_params.get('en_curso')
        if en_curso is not None:
            en_curso_bool = en_curso.lower() == 'true'
            queryset = queryset.filter(en_curso=en_curso_bool)
        
        return queryset
