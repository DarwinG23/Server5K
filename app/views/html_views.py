"""
Módulo: html_views
Vistas HTML para la interfaz web pública.
"""

from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch
from app.models import Competencia, Equipo, RegistroTiempo


def competencia_list_view(request):
    """Listado público de competencias activas."""
    competencias = Competencia.objects.filter(is_active=True).order_by('-datetime')
    return render(request, 'app/competencia_list.html', {'competencias': competencias})


def competencia_detail_view(request, pk):
    """Detalle de competencia con sistema de clasificación y descalificación."""
    competencia = get_object_or_404(Competencia, pk=pk, is_active=True)
    
    # Si la competencia está en curso, mostrar solo información básica
    if competencia.is_running:
        total_equipos = Equipo.objects.filter(competition=competencia).count()
        return render(request, 'app/competencia_detail.html', {
            'competencia': competencia,
            'en_curso': True,
            'total_equipos': total_equipos,
        })
    
    # Competencia finalizada - mostrar resultados completos
    tiempos_qs = RegistroTiempo.objects.all().order_by('time')
    equipos = Equipo.objects.filter(
        competition=competencia
    ).select_related('judge').prefetch_related(
        Prefetch('times', queryset=tiempos_qs, to_attr='prefetched_tiempos')
    )
    
    equipos_calificados = []
    equipos_descalificados = []
    
    for equipo in equipos:
        tiempos_competencia = [t for t in equipo.prefetched_tiempos]
        
        # Detectar jugadores ausentes (tiempo = 0 ms)
        jugadores_ausentes = sum(1 for t in tiempos_competencia if t.time == 0)
        equipo.jugadores_ausentes = jugadores_ausentes
        equipo.descalificado = jugadores_ausentes > 0
        
        if tiempos_competencia:
            equipo.tiempo_total_ms = sum(t.time for t in tiempos_competencia)
            equipo.mejor_tiempo_ms = min(t.time for t in tiempos_competencia if t.time > 0) if any(t.time > 0 for t in tiempos_competencia) else 0
            
            # Formatear sin milisegundos
            total_seconds = equipo.tiempo_total_ms // 1000
            s = total_seconds % 60
            total_minutes = total_seconds // 60
            m = total_minutes % 60
            h = total_minutes // 60
            equipo.tiempo_total_formateado = f"{h:02d}:{m:02d}:{s:02d}"
            
            # Mejor tiempo sin milisegundos
            mejor_seconds = equipo.mejor_tiempo_ms // 1000
            mejor_s = mejor_seconds % 60
            mejor_m = (mejor_seconds // 60) % 60
            mejor_h = mejor_seconds // 3600
            equipo.mejor_tiempo_formateado = f"{mejor_h:02d}:{mejor_m:02d}:{mejor_s:02d}"
        else:
            equipo.tiempo_total_ms = 0
            equipo.mejor_tiempo_ms = 0
            equipo.tiempo_total_formateado = "00:00:00"
            equipo.mejor_tiempo_formateado = "00:00:00"
        
        equipo.num_registros = len(equipo.prefetched_tiempos)
        equipo.jugadores_completados = equipo.num_registros - jugadores_ausentes
        
        if equipo.descalificado:
            equipos_descalificados.append(equipo)
        else:
            equipos_calificados.append(equipo)
    
    # Ordenar calificados por tiempo total (menor a mayor)
    equipos_calificados.sort(key=lambda e: e.tiempo_total_ms if e.tiempo_total_ms > 0 else float('inf'))
    equipos_descalificados.sort(key=lambda e: e.tiempo_total_ms)
    
    # Asignar posiciones
    for idx, equipo in enumerate(equipos_calificados, 1):
        equipo.posicion = idx
    
    equipos_list = equipos_calificados + equipos_descalificados
    
    return render(request, 'app/competencia_detail.html', {
        'competencia': competencia,
        'equipos': equipos_list,
        'equipos_calificados': len(equipos_calificados),
        'equipos_descalificados': len(equipos_descalificados),
        'en_curso': False,
    })