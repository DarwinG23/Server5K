"""
Módulo: serializers
Serializadores de DRF para la API REST.
"""

from .serializers import (
    CompetenciaSerializer,
    JuezMeSerializer,
    EquipoSerializer,
    RegistroTiempoSerializer,
)

__all__ = [
    'CompetenciaSerializer',
    'JuezMeSerializer',
    'EquipoSerializer',
    'RegistroTiempoSerializer',
]
