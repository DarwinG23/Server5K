"""Vistas específicas para el Admin de Django."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser
from app.models import Competencia


class EstadoCompetenciaAdminView(APIView):
    """
    Vista protegida para obtener el estado de las competencias.
    Usada por el admin de Django para actualizar el cronómetro.
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Retorna todas las competencias con su estado"""
        competencias = Competencia.objects.all()
        
        data = []
        for comp in competencias:
            data.append({
                'id': comp.id,
                'name': comp.name,
                'is_running': comp.is_running,
                'started_at': comp.started_at.isoformat() if comp.started_at else None,
                'finished_at': comp.finished_at.isoformat() if comp.finished_at else None,
            })
        
        return Response(data)
