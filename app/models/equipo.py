"""
Módulo: equipo
Define el modelo de Equipo para gestionar participantes en las competencias.
"""

from django.db import models


class Equipo(models.Model):
    nombre = models.CharField(max_length=200)
    dorsal = models.IntegerField()
    
    juez_asignado = models.ForeignKey(
        'Juez',
        on_delete=models.CASCADE,
        related_name='equipos_asignados'
    )
    
    @property
    def competencia(self):
        return self.juez_asignado.competencia
    
    class Meta:
        unique_together = ('juez_asignado', 'dorsal')
        ordering = ['dorsal']
    
    def __str__(self):
        return f"{self.nombre} (Dorsal {self.dorsal})"
    
    def tiempo_total(self):
        """Retorna el tiempo total acumulado de todos los registros en milisegundos"""
        from django.db.models import Sum
        total = self.tiempos.aggregate(total=Sum('tiempo'))['total']
        return total or 0

    def tiempo_promedio(self):
        """Retorna el tiempo promedio de todos los registros en milisegundos"""
        from django.db.models import Avg
        promedio = self.tiempos.aggregate(promedio=Avg('tiempo'))['promedio']
        return int(promedio) if promedio else 0

    def mejor_tiempo(self):
        """Retorna el mejor tiempo (más bajo) del equipo"""
        return self.tiempos.order_by('tiempo').first()

    def tiempo_total_formateado(self):
        """Retorna el tiempo total en formato legible"""
        total_ms = self.tiempo_total()
        ms = total_ms % 1000
        total_seconds = total_ms // 1000
        s = total_seconds % 60
        total_minutes = total_seconds // 60
        m = total_minutes % 60
        h = total_minutes // 60
        return f"{h}h {m}m {s}s {ms}ms"

    def numero_registros(self):
        """Retorna el número total de registros de tiempo"""
        return self.tiempos.count()


class ResultadoEquipo(Equipo):
    """Modelo proxy para mostrar resultados de equipos en el admin"""
    class Meta:
        proxy = True
        verbose_name = 'Resultado por Equipo'
        verbose_name_plural = '📊 Resultados por Equipo'
