"""
Módulo: results_service
Responsable del cálculo de tiempos finales por equipo.

Características:
- Ordenar registros por tiempo
- Sumar los primeros 15 registros
- Calcular promedios y mejores tiempos
- Evitar recomputación innecesaria
"""

from typing import Dict, List, Any
from django.db.models import Sum, Avg, Count, Min


class ResultsService:
    """
    Servicio para calcular y obtener resultados de equipos.
    """
    
    MAX_REGISTROS_CONSIDERADOS = 15
    
    def obtener_resultados_equipo(self, equipo_id: int, competencia_id: int = None) -> Dict[str, Any]:
        """
        Obtiene los resultados calculados de un equipo.
        
        Args:
            equipo_id: ID del equipo
            competencia_id: ID de la competencia (opcional, si no se especifica usa todos los registros)
            
        Returns:
            Dict con estadísticas del equipo
        """
        from app.models import Equipo, RegistroTiempo
        
        try:
            equipo = Equipo.objects.get(id=equipo_id)
            
            # Filtrar registros
            registros_query = RegistroTiempo.objects.filter(equipo=equipo)
            
            if competencia_id:
                registros_query = registros_query.filter(competencia_id=competencia_id)
            
            # Obtener los mejores tiempos (ordenados ascendentemente)
            registros = registros_query.order_by('tiempo')[:self.MAX_REGISTROS_CONSIDERADOS]
            
            if not registros:
                return {
                    'exito': True,
                    'equipo_id': equipo_id,
                    'equipo_nombre': equipo.nombre,
                    'equipo_dorsal': equipo.dorsal,
                    'num_registros': 0,
                    'tiempo_total': 0,
                    'tiempo_promedio': 0,
                    'mejor_tiempo': None,
                    'registros': []
                }
            
            # Calcular estadísticas
            tiempos = [r.tiempo for r in registros]
            tiempo_total = sum(tiempos)
            tiempo_promedio = tiempo_total // len(tiempos) if tiempos else 0
            mejor_tiempo = min(tiempos) if tiempos else None
            
            return {
                'exito': True,
                'equipo_id': equipo_id,
                'equipo_nombre': equipo.nombre,
                'equipo_dorsal': equipo.dorsal,
                'num_registros': len(registros),
                'tiempo_total': tiempo_total,
                'tiempo_promedio': tiempo_promedio,
                'mejor_tiempo': mejor_tiempo,
                'tiempo_total_formateado': self._formatear_tiempo(tiempo_total),
                'tiempo_promedio_formateado': self._formatear_tiempo(tiempo_promedio),
                'mejor_tiempo_formateado': self._formatear_tiempo(mejor_tiempo) if mejor_tiempo else None,
                'registros': [
                    {
                        'id_registro': str(r.id_registro),
                        'tiempo': r.tiempo,
                        'horas': r.horas,
                        'minutos': r.minutos,
                        'segundos': r.segundos,
                        'milisegundos': r.milisegundos,
                        'timestamp': r.timestamp.isoformat()
                    }
                    for r in registros
                ]
            }
            
        except Exception as e:
            return {
                'exito': False,
                'error': f'Error al obtener resultados: {str(e)}'
            }
    
    def obtener_ranking_competencia(self, competencia_id: int) -> Dict[str, Any]:
        """
        Obtiene el ranking de equipos de una competencia.
        
        Args:
            competencia_id: ID de la competencia
            
        Returns:
            Dict con lista de equipos ordenados por mejor tiempo
        """
        from app.models import Equipo, RegistroTiempo, Competencia
        
        try:
            competencia = Competencia.objects.get(id=competencia_id)
            
            # Obtener IDs de equipos que tienen registros en esta competencia
            equipos_ids = RegistroTiempo.objects.filter(
                competencia_id=competencia_id
            ).values_list('equipo_id', flat=True).distinct()
            
            # Obtener equipos
            equipos = Equipo.objects.filter(id__in=equipos_ids)
            
            # Calcular resultados para cada equipo
            resultados = []
            for equipo in equipos:
                resultado = self.obtener_resultados_equipo(equipo.id, competencia_id)
                if resultado['exito']:
                    resultados.append(resultado)
            
            # Ordenar por mejor tiempo (ascendente)
            resultados.sort(key=lambda x: x['mejor_tiempo'] if x['mejor_tiempo'] is not None else float('inf'))
            
            # Asignar posiciones
            for idx, resultado in enumerate(resultados, 1):
                resultado['posicion'] = idx
            
            return {
                'exito': True,
                'competencia_id': competencia_id,
                'competencia_nombre': competencia.nombre,
                'total_equipos': len(resultados),
                'ranking': resultados
            }
            
        except Competencia.DoesNotExist:
            return {
                'exito': False,
                'error': f'La competencia con ID {competencia_id} no existe'
            }
        except Exception as e:
            return {
                'exito': False,
                'error': f'Error al obtener ranking: {str(e)}'
            }
    
    def _formatear_tiempo(self, tiempo_ms: int) -> str:
        """
        Formatea un tiempo en milisegundos a formato legible.
        
        Args:
            tiempo_ms: Tiempo en milisegundos
            
        Returns:
            String formateado (ej: "1h 23m 45s 678ms")
        """
        if tiempo_ms is None:
            return "N/A"
        
        ms = tiempo_ms % 1000
        total_seconds = tiempo_ms // 1000
        s = total_seconds % 60
        total_minutes = total_seconds // 60
        m = total_minutes % 60
        h = total_minutes // 60
        
        return f"{h}h {m}m {s}s {ms}ms"
