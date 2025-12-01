"""
Módulo: utils
Utilidades y funciones auxiliares de la aplicación.
"""

from .idempotency import (
    generar_hash_registro,
    verificar_duplicado,
    limpiar_registros_antiguos,
)
from .timestamps import (
    formatear_tiempo_ms,
    parsear_tiempo_a_ms,
    obtener_timestamp_actual,
)

__all__ = [
    'generar_hash_registro',
    'verificar_duplicado',
    'limpiar_registros_antiguos',
    'formatear_tiempo_ms',
    'parsear_tiempo_a_ms',
    'obtener_timestamp_actual',
]
