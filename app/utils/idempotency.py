"""
Módulo: idempotency
Utilidades para garantizar idempotencia en operaciones de registro de tiempos.

Características:
- Generar hash único por registro
- Verificar duplicados
- Limpiar registros antiguos
"""

import hashlib
import json
from typing import Dict, Any, Optional
from datetime import timedelta
from django.utils import timezone


def generar_hash_registro(equipo_id: int, tiempo: int, timestamp: str = None) -> str:
    """
    Genera un hash único para un registro de tiempo basado en sus datos.
    
    Args:
        equipo_id: ID del equipo
        tiempo: Tiempo en milisegundos
        timestamp: Timestamp ISO opcional
        
    Returns:
        String hash SHA256
    """
    datos = {
        'equipo_id': equipo_id,
        'tiempo': tiempo,
        'timestamp': timestamp or timezone.now().isoformat()
    }
    
    datos_str = json.dumps(datos, sort_keys=True)
    return hashlib.sha256(datos_str.encode()).hexdigest()


def verificar_duplicado(
    equipo_id: int,
    tiempo: int,
    competencia_id: int,
    ventana_minutos: int = 5
) -> Optional[Any]:
    """
    Verifica si existe un registro duplicado reciente.
    
    Args:
        equipo_id: ID del equipo
        tiempo: Tiempo en milisegundos
        competencia_id: ID de la competencia
        ventana_minutos: Ventana de tiempo en minutos para considerar duplicado
        
    Returns:
        RegistroTiempo si se encuentra duplicado, None en caso contrario
    """
    from app.models import RegistroTiempo
    
    # Calcular ventana de tiempo
    tiempo_limite = timezone.now() - timedelta(minutes=ventana_minutos)
    
    # Buscar registros similares recientes
    # Consideramos duplicado si el tiempo es exactamente igual y está en la ventana
    registro_existente = RegistroTiempo.objects.filter(
        equipo_id=equipo_id,
        tiempo=tiempo,
        competencia_id=competencia_id,
        timestamp__gte=tiempo_limite
    ).first()
    
    return registro_existente


def limpiar_registros_antiguos(dias: int = 90) -> int:
    """
    Limpia registros de tiempos más antiguos que el número de días especificado.
    
    Args:
        dias: Número de días de antigüedad para considerar un registro como antiguo
        
    Returns:
        Número de registros eliminados
    """
    from app.models import RegistroTiempo
    
    fecha_limite = timezone.now() - timedelta(days=dias)
    
    # Eliminar solo registros de competencias finalizadas
    registros_antiguos = RegistroTiempo.objects.filter(
        timestamp__lt=fecha_limite,
        competencia__en_curso=False
    )
    
    count = registros_antiguos.count()
    registros_antiguos.delete()
    
    return count


def generar_id_idempotente(equipo_id: int, juez_id: int, tiempo: int) -> str:
    """
    Genera un ID idempotente para evitar duplicados en el mismo request.
    
    Args:
        equipo_id: ID del equipo
        juez_id: ID del juez
        tiempo: Tiempo en milisegundos
        
    Returns:
        String hash único
    """
    datos = f"{juez_id}:{equipo_id}:{tiempo}:{timezone.now().timestamp()}"
    return hashlib.md5(datos.encode()).hexdigest()


def es_registro_valido(tiempo: int, min_tiempo: int = 0, max_tiempo: int = 86400000) -> bool:
    """
    Valida que un tiempo esté dentro de rangos razonables.
    
    Args:
        tiempo: Tiempo en milisegundos
        min_tiempo: Tiempo mínimo permitido (default: 0ms)
        max_tiempo: Tiempo máximo permitido (default: 24 horas en ms)
        
    Returns:
        bool: True si el tiempo es válido
    """
    return min_tiempo <= tiempo <= max_tiempo


def normalizar_tiempo(horas: int, minutos: int, segundos: int, milisegundos: int) -> int:
    """
    Normaliza componentes de tiempo a milisegundos totales.
    
    Args:
        horas: Componente de horas
        minutos: Componente de minutos
        segundos: Componente de segundos
        milisegundos: Componente de milisegundos
        
    Returns:
        Tiempo total en milisegundos
    """
    total_segundos = (horas * 3600) + (minutos * 60) + segundos
    return (total_segundos * 1000) + milisegundos


def descomponer_tiempo(tiempo_ms: int) -> Dict[str, int]:
    """
    Descompone un tiempo en milisegundos a sus componentes.
    
    Args:
        tiempo_ms: Tiempo en milisegundos
        
    Returns:
        Dict con componentes: horas, minutos, segundos, milisegundos
    """
    ms = tiempo_ms % 1000
    total_seconds = tiempo_ms // 1000
    s = total_seconds % 60
    total_minutes = total_seconds // 60
    m = total_minutes % 60
    h = total_minutes // 60
    
    return {
        'horas': h,
        'minutos': m,
        'segundos': s,
        'milisegundos': ms
    }
