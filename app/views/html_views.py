"""
Módulo: html_views
Vistas HTML para la interfaz web pública.
"""

from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch
from app.models import Competencia, Equipo, RegistroTiempo


def competencia_list_view(request):
    """Listado público de competencias activas (interfaz simple)."""
    competencias = Competencia.objects.filter(is_active=True).order_by('-datetime')
    return render(request, 'app/competencia_list.html', {'competencias': competencias})


def competencia_detail_view(request, pk):
    """Detalle de competencia: lista de equipos y sus registros de tiempo."""
    competencia = get_object_or_404(Competencia, pk=pk, is_active=True)
    
    # Obtener TODOS los equipos de esta competencia con sus registros
    tiempos_qs = RegistroTiempo.objects.all().order_by('time')
    
    # Obtener los equipos de esta competencia
    equipos = Equipo.objects.filter(
        competition=competencia
    ).select_related('judge').prefetch_related(
        Prefetch('times', queryset=tiempos_qs, to_attr='prefetched_tiempos')
    )
    
    # Agregar estadísticas a cada equipo
    for equipo in equipos:
        tiempos_competencia = [t for t in equipo.prefetched_tiempos]
        
        if tiempos_competencia:
            equipo.tiempo_total_ms = sum(t.time for t in tiempos_competencia)
            equipo.tiempo_promedio = equipo.tiempo_total_ms // len(tiempos_competencia)
            equipo.mejor_tiempo_ms = tiempos_competencia[0].time  # Ya están ordenados por tiempo ascendente
            
            # Formatear tiempo total
            total_ms = equipo.tiempo_total_ms
            ms = total_ms % 1000
            total_seconds = total_ms // 1000
            s = total_seconds % 60
            total_minutes = total_seconds // 60
            m = total_minutes % 60
            h = total_minutes // 60
            equipo.tiempo_total_formateado = f"{h}h {m}m {s}s {ms}ms"
        else:
            equipo.tiempo_total_ms = 0
            equipo.tiempo_promedio = 0
            equipo.mejor_tiempo_ms = float('inf')  # Infinito para equipos sin tiempos
            equipo.tiempo_total_formateado = "0h 0m 0s 0ms"
        
        equipo.num_registros = len(equipo.prefetched_tiempos)
    
    # Obtener parámetros de ordenamiento
    orden = request.GET.get('orden', 'mejor_tiempo')
    direccion = request.GET.get('dir', 'asc')  # 'asc' o 'desc'
    
    equipos_list = list(equipos)
    
    # Determinar si es orden descendente
    reverse = (direccion == 'desc')
    
    # Ordenamiento basado en parámetro
    if orden == 'tiempo_total':
        equipos_list.sort(key=lambda e: e.tiempo_total_ms, reverse=reverse)
    elif orden == 'promedio':
        equipos_list.sort(key=lambda e: e.tiempo_promedio, reverse=reverse)
    else:  # 'mejor_tiempo' por defecto
        equipos_list.sort(key=lambda e: e.mejor_tiempo_ms, reverse=reverse)
    
    return render(request, 'app/competencia_detail.html', {
        'competencia': competencia,
        'equipos': equipos_list,
    })
