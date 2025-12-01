"""
Filtros personalizados para formatear tiempos.
"""
from django import template

register = template.Library()


@register.filter
def format_time_ms(milliseconds):
    """
    Formatea milisegundos en formato HH:MM:SS.mmm
    Ejemplo: 784784 ms -> 00:13:04.784
    """
    if not milliseconds or milliseconds == 0:
        return "00:00:00.000"
    
    ms = int(milliseconds) % 1000
    total_seconds = int(milliseconds) // 1000
    s = total_seconds % 60
    total_minutes = total_seconds // 60
    m = total_minutes % 60
    h = total_minutes // 60
    
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


@register.filter
def format_time_readable(milliseconds):
    """
    Formatea milisegundos en formato legible (sin mostrar partes vacías)
    Ejemplo: 784784 ms -> 13m 4s 784ms
    """
    if not milliseconds or milliseconds == 0:
        return "0s"
    
    ms = int(milliseconds) % 1000
    total_seconds = int(milliseconds) // 1000
    s = total_seconds % 60
    total_minutes = total_seconds // 60
    m = total_minutes % 60
    h = total_minutes // 60
    
    parts = []
    if h > 0:
        parts.append(f"{h}h")
    if m > 0:
        parts.append(f"{m}m")
    if s > 0:
        parts.append(f"{s}s")
    if ms > 0 and h == 0:  # Solo mostrar ms si no hay horas
        parts.append(f"{ms}ms")
    
    return " ".join(parts) if parts else "0s"
