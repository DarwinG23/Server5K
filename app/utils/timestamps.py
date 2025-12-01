"""
Módulo: timestamps
Utilidades para manejo de timestamps y formateo de tiempos.
"""

from datetime import datetime, timezone as dt_timezone
from typing import Dict, Optional
from django.utils import timezone


def formatear_tiempo_ms(tiempo_ms: int, formato: str = 'completo') -> str:
    """
    Formatea un tiempo en milisegundos a formato legible.
    
    Args:
        tiempo_ms: Tiempo en milisegundos
        formato: Tipo de formato ('completo', 'corto', 'iso')
        
    Returns:
        String formateado según el tipo especificado
    """
    if tiempo_ms is None:
        return "N/A"
    
    ms = tiempo_ms % 1000
    total_seconds = tiempo_ms // 1000
    s = total_seconds % 60
    total_minutes = total_seconds // 60
    m = total_minutes % 60
    h = total_minutes // 60
    
    if formato == 'completo':
        return f"{h}h {m}m {s}s {ms}ms"
    elif formato == 'corto':
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}.{ms:03d}"
        else:
            return f"{m}:{s:02d}.{ms:03d}"
    elif formato == 'iso':
        # Formato ISO 8601 para duración: PT1H23M45.678S
        return f"PT{h}H{m}M{s}.{ms:03d}S"
    else:
        return f"{h}h {m}m {s}s {ms}ms"


def parsear_tiempo_a_ms(tiempo_str: str) -> Optional[int]:
    """
    Parsea un string de tiempo a milisegundos.
    
    Soporta formatos:
    - "1h 23m 45s 678ms"
    - "1:23:45.678"
    - "23:45.678"
    
    Args:
        tiempo_str: String con el tiempo
        
    Returns:
        Tiempo en milisegundos o None si el formato es inválido
    """
    try:
        # Formato "1h 23m 45s 678ms"
        if 'h' in tiempo_str or 'm' in tiempo_str:
            h = m = s = ms = 0
            
            if 'h' in tiempo_str:
                h = int(tiempo_str.split('h')[0].strip())
                tiempo_str = tiempo_str.split('h')[1].strip()
            
            if 'm' in tiempo_str:
                m = int(tiempo_str.split('m')[0].strip())
                tiempo_str = tiempo_str.split('m')[1].strip()
            
            if 's' in tiempo_str:
                s = int(tiempo_str.split('s')[0].strip())
                tiempo_str = tiempo_str.split('s')[1].strip()
            
            if 'ms' in tiempo_str:
                ms = int(tiempo_str.split('ms')[0].strip())
            
            return (h * 3600 + m * 60 + s) * 1000 + ms
        
        # Formato "1:23:45.678" o "23:45.678"
        elif ':' in tiempo_str:
            partes = tiempo_str.split(':')
            
            if len(partes) == 3:  # h:m:s.ms
                h = int(partes[0])
                m = int(partes[1])
                s_ms = partes[2].split('.')
                s = int(s_ms[0])
                ms = int(s_ms[1]) if len(s_ms) > 1 else 0
            elif len(partes) == 2:  # m:s.ms
                h = 0
                m = int(partes[0])
                s_ms = partes[1].split('.')
                s = int(s_ms[0])
                ms = int(s_ms[1]) if len(s_ms) > 1 else 0
            else:
                return None
            
            return (h * 3600 + m * 60 + s) * 1000 + ms
        
        return None
        
    except (ValueError, IndexError):
        return None


def obtener_timestamp_actual() -> str:
    """
    Obtiene el timestamp actual en formato ISO 8601.
    
    Returns:
        String con timestamp en formato ISO 8601
    """
    return timezone.now().isoformat()


def parsear_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parsea un string de timestamp ISO 8601 a objeto datetime.
    
    Args:
        timestamp_str: String con timestamp en formato ISO 8601
        
    Returns:
        Objeto datetime o None si el formato es inválido
    """
    try:
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


def calcular_diferencia_ms(timestamp1: datetime, timestamp2: datetime) -> int:
    """
    Calcula la diferencia en milisegundos entre dos timestamps.
    
    Args:
        timestamp1: Primer timestamp
        timestamp2: Segundo timestamp
        
    Returns:
        Diferencia en milisegundos (absoluta)
    """
    delta = abs(timestamp1 - timestamp2)
    return int(delta.total_seconds() * 1000)


def es_timestamp_reciente(timestamp: datetime, minutos: int = 5) -> bool:
    """
    Verifica si un timestamp es reciente (dentro de los últimos N minutos).
    
    Args:
        timestamp: Timestamp a verificar
        minutos: Número de minutos para considerar reciente
        
    Returns:
        bool: True si es reciente
    """
    ahora = timezone.now()
    diferencia = calcular_diferencia_ms(ahora, timestamp)
    return diferencia <= (minutos * 60 * 1000)


def formatear_timestamp(timestamp: datetime, formato: str = 'completo') -> str:
    """
    Formatea un timestamp a string legible.
    
    Args:
        timestamp: Objeto datetime
        formato: Tipo de formato ('completo', 'fecha', 'hora', 'relativo')
        
    Returns:
        String formateado
    """
    if formato == 'completo':
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    elif formato == 'fecha':
        return timestamp.strftime('%Y-%m-%d')
    elif formato == 'hora':
        return timestamp.strftime('%H:%M:%S')
    elif formato == 'relativo':
        ahora = timezone.now()
        diferencia = ahora - timestamp
        
        segundos = diferencia.total_seconds()
        
        if segundos < 60:
            return "hace unos segundos"
        elif segundos < 3600:
            minutos = int(segundos / 60)
            return f"hace {minutos} minuto{'s' if minutos != 1 else ''}"
        elif segundos < 86400:
            horas = int(segundos / 3600)
            return f"hace {horas} hora{'s' if horas != 1 else ''}"
        else:
            dias = int(segundos / 86400)
            return f"hace {dias} día{'s' if dias != 1 else ''}"
    else:
        return timestamp.isoformat()
