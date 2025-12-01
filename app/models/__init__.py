"""
Módulo: models
Contiene todos los modelos de datos de la aplicación organizados por entidad.
"""

from .competencia import Competencia
from .juez import Juez
from .equipo import Equipo, ResultadoEquipo
from .registrotiempo import RegistroTiempo

__all__ = [
    'Competencia',
    'Juez',
    'Equipo',
    'RegistroTiempo',
    'ResultadoEquipo',
]
