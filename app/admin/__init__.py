"""
Módulo: admin
Configuración del Django Admin personalizado.
"""

from .admin import (
    CompetenciaAdmin,
    JuezAdmin,
    EquipoAdmin,
    RegistroTiempoAdmin,
    ResultadoEquipoAdmin,
)

__all__ = [
    'CompetenciaAdmin',
    'JuezAdmin',
    'EquipoAdmin',
    'RegistroTiempoAdmin',
    'ResultadoEquipoAdmin',
]
