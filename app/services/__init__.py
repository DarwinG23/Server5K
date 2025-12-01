"""
Módulo: services
Contiene la lógica de negocio de la aplicación organizada en servicios.
"""

from .registro_service import RegistroService
from .competencia_service import CompetenciaService
from .results_service import ResultsService

__all__ = [
    'RegistroService',
    'CompetenciaService',
    'ResultsService',
]
