"""
Módulo: competencia_service
Responsable de la gestión del estado de las competencias.

Características:
- Iniciar/detener competencias
- Notificar cambios de estado a jueces conectados
- Validar transiciones de estado
"""

from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from typing import Dict, Any


class CompetenciaService:
    """
    Servicio para gestionar el ciclo de vida de las competencias.
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def iniciar_competencia(self, competencia_id: int) -> Dict[str, Any]:
        """
        Inicia una competencia y notifica a todos los jueces conectados.
        
        Args:
            competencia_id: ID de la competencia a iniciar
            
        Returns:
            Dict con resultado de la operación
        """
        from app.models import Competencia
        
        try:
            competencia = Competencia.objects.get(id=competencia_id)
            
            if competencia.en_curso:
                return {
                    'exito': False,
                    'error': 'La competencia ya está en curso'
                }
            
            if not competencia.activa:
                return {
                    'exito': False,
                    'error': 'La competencia no está activa'
                }
            
            # Iniciar competencia
            competencia.en_curso = True
            competencia.fecha_inicio = timezone.now()
            competencia.save()
            
            # Notificar a todos los jueces de esta competencia
            self._notificar_jueces_competencia(
                competencia_id=competencia.id,
                tipo='competencia_iniciada',
                mensaje='La competencia ha iniciado',
                competencia_nombre=competencia.nombre,
                en_curso=True
            )
            
            return {
                'exito': True,
                'competencia': competencia
            }
            
        except Competencia.DoesNotExist:
            return {
                'exito': False,
                'error': f'La competencia con ID {competencia_id} no existe'
            }
        except Exception as e:
            return {
                'exito': False,
                'error': f'Error al iniciar competencia: {str(e)}'
            }
    
    def detener_competencia(self, competencia_id: int) -> Dict[str, Any]:
        """
        Detiene una competencia y notifica a todos los jueces conectados.
        
        Args:
            competencia_id: ID de la competencia a detener
            
        Returns:
            Dict con resultado de la operación
        """
        from app.models import Competencia
        
        try:
            competencia = Competencia.objects.get(id=competencia_id)
            
            if not competencia.en_curso:
                return {
                    'exito': False,
                    'error': 'La competencia no está en curso'
                }
            
            # Detener competencia
            competencia.en_curso = False
            competencia.fecha_fin = timezone.now()
            competencia.save()
            
            # Notificar a todos los jueces de esta competencia
            self._notificar_jueces_competencia(
                competencia_id=competencia.id,
                tipo='competencia_detenida',
                mensaje='La competencia ha finalizado',
                competencia_nombre=competencia.nombre,
                en_curso=False
            )
            
            return {
                'exito': True,
                'competencia': competencia
            }
            
        except Competencia.DoesNotExist:
            return {
                'exito': False,
                'error': f'La competencia con ID {competencia_id} no existe'
            }
        except Exception as e:
            return {
                'exito': False,
                'error': f'Error al detener competencia: {str(e)}'
            }
    
    def _notificar_jueces_competencia(
        self,
        competencia_id: int,
        tipo: str,
        mensaje: str,
        competencia_nombre: str,
        en_curso: bool
    ):
        """
        Notifica a todos los jueces de una competencia sobre un cambio de estado.
        
        Args:
            competencia_id: ID de la competencia
            tipo: Tipo de evento ('competencia_iniciada' o 'competencia_detenida')
            mensaje: Mensaje descriptivo
            competencia_nombre: Nombre de la competencia
            en_curso: Estado de la competencia
        """
        if not self.channel_layer:
            return
        
        group_name = f'competencia_{competencia_id}'
        
        async_to_sync(self.channel_layer.group_send)(
            group_name,
            {
                'type': tipo,
                'data': {
                    'mensaje': mensaje,
                    'competencia_id': competencia_id,
                    'competencia_nombre': competencia_nombre,
                    'en_curso': en_curso,
                }
            }
        )
    
    def obtener_estado_competencia(self, competencia_id: int) -> Dict[str, Any]:
        """
        Obtiene el estado actual de una competencia.
        
        Args:
            competencia_id: ID de la competencia
            
        Returns:
            Dict con información de la competencia
        """
        from app.models import Competencia
        
        try:
            competencia = Competencia.objects.get(id=competencia_id)
            
            return {
                'exito': True,
                'competencia': {
                    'id': competencia.id,
                    'nombre': competencia.nombre,
                    'categoria': competencia.categoria,
                    'activa': competencia.activa,
                    'en_curso': competencia.en_curso,
                    'fecha_inicio': competencia.fecha_inicio.isoformat() if competencia.fecha_inicio else None,
                    'fecha_fin': competencia.fecha_fin.isoformat() if competencia.fecha_fin else None,
                    'estado': competencia.get_estado_display(),
                    'estado_texto': competencia.get_estado_texto(),
                }
            }
            
        except Competencia.DoesNotExist:
            return {
                'exito': False,
                'error': f'La competencia con ID {competencia_id} no existe'
            }
