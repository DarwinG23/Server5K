"""
Módulo: consumers
Consumer WebSocket para gestionar las conexiones de jueces y recepción de tiempos en tiempo real.
Responsable de:
- Validar autenticación JWT
- Verificar permisos del juez
- Recibir y procesar registros de tiempo
- Enviar notificaciones en tiempo real
"""

import urllib.parse
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .validators import (
    get_juez_from_token,
    verificar_competencia_activa,
    obtener_estado_competencia,
    validar_datos_registro,
    validar_datos_batch,
)


class JuezConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer WebSocket para jueces.
    
    Maneja la conexión, autenticación y recepción de tiempos de los jueces.
    Usa Redis como transport layer para mensajería entre workers.
    """
    
    async def connect(self):
        """
        Maneja la conexión inicial del WebSocket.
        
        Valida:
        - Token JWT en query string
        - Que el juez esté activo
        - Que el juez_id de la URL coincida con el token
        - Que la competencia esté activa
        """
        # Expect token in querystring: ?token=...
        qs = self.scope.get('query_string', b'').decode()
        params = urllib.parse.parse_qs(qs)
        token = params.get('token', [None])[0]
        
        if not token:
            await self.close()
            return

        try:
            juez = await get_juez_from_token(token)
            if not juez:
                await self.close()
                return
        except Exception:
            await self.close()
            return

        self.juez = juez

        # Verificar que el juez_id de la URL coincida con el juez autenticado
        self.juez_id = str(self.scope['url_route']['kwargs'].get('juez_id'))
        if str(self.juez.id) != self.juez_id:
            await self.close()
            return

        # Verificar que la competencia esté activa
        competencia_activa = await verificar_competencia_activa(self.juez)
        if not competencia_activa:
            await self.close()
            return

        # Unirse al grupo del juez y al grupo de la competencia
        self.group_name = f'juez_{self.juez_id}'
        
        # Obtener competencia_id del equipo asignado al juez
        competencia_id = None
        if hasattr(self.juez, 'team') and self.juez.team:
            competencia_id = self.juez.team.competition_id
        
        if competencia_id:
            self.competencia_group = f'competencia_{competencia_id}'
            await self.channel_layer.group_add(self.competencia_group, self.channel_name)
        
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        
        await self.accept()
        
        # Enviar estado de la competencia al conectar
        estado_competencia = await obtener_estado_competencia(self.juez)
        await self.send_json({
            'tipo': 'conexion_establecida',
            'mensaje': 'Conectado exitosamente',
            'competencia': estado_competencia
        })

    async def disconnect(self, close_code):
        """
        Maneja la desconexión del WebSocket.
        Remueve al juez de los grupos de Redis.
        """
        try:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            await self.channel_layer.group_discard(self.competencia_group, self.channel_name)
        except Exception:
            pass

    async def receive_json(self, content, **kwargs):
        """
        Maneja mensajes JSON del cliente.
        
        Mensajes soportados:
        1. registrar_tiempo: Registra el tiempo de llegada de un equipo
        2. registrar_tiempos: Registra múltiples tiempos en batch
        """
        tipo = content.get('tipo')
        
        if tipo == 'registrar_tiempo':
            await self.manejar_registro_tiempo(content)
        elif tipo == 'registrar_tiempos':
            await self.manejar_registro_tiempos_batch(content)
        else:
            # Mensaje no reconocido
            await self.send_json({
                'tipo': 'error',
                'mensaje': f'Tipo de mensaje no reconocido: {tipo}'
            })
    
    async def manejar_registro_tiempo(self, content):
        """
        Registra el tiempo de un equipo.
        
        Esperado en content:
        {
            "tipo": "registrar_tiempo",
            "equipo_id": 1,
            "tiempo": 1234567,  # milisegundos totales
            "horas": 0,
            "minutos": 20,
            "segundos": 34,
            "milisegundos": 567
        }
        """
        try:
            # Validar datos básicos
            es_valido, error = validar_datos_registro(content)
            if not es_valido:
                await self.send_json({
                    'tipo': 'error',
                    'mensaje': error
                })
                return
            
            equipo_id = content.get('equipo_id')
            tiempo = content.get('tiempo')
            horas = content.get('horas', 0)
            minutos = content.get('minutos', 0)
            segundos = content.get('segundos', 0)
            milisegundos = content.get('milisegundos', 0)
            
            # Registrar el tiempo usando el servicio
            from app.services.registro_service import RegistroService
            
            service = RegistroService()
            resultado = await service.registrar_tiempo(
                juez=self.juez,
                equipo_id=equipo_id,
                tiempo=tiempo,
                horas=horas,
                minutos=minutos,
                segundos=segundos,
                milisegundos=milisegundos
            )
            
            if resultado['exito']:
                registro = resultado['registro']
                # Enviar confirmación al cliente
                await self.send_json({
                    'tipo': 'tiempo_registrado',
                    'registro': {
                        'id_registro': str(registro.record_id),
                        'equipo_id': registro.team_id,
                        'equipo_nombre': registro.team.name,
                        'equipo_dorsal': registro.team.number,
                        'tiempo': registro.time,
                        'horas': registro.hours,
                        'minutos': registro.minutes,
                        'segundos': registro.seconds,
                        'milisegundos': registro.milliseconds,
                        'timestamp': registro.created_at.isoformat()
                    }
                })
            else:
                await self.send_json({
                    'tipo': 'error',
                    'mensaje': resultado['error']
                })
            
        except Exception as e:
            await self.send_json({
                'tipo': 'error',
                'mensaje': f'Error al registrar tiempo: {str(e)}'
            })
    
    async def manejar_registro_tiempos_batch(self, content):
        """
        Registra múltiples tiempos en batch (lote).
        
        Esperado en content:
        {
            "tipo": "registrar_tiempos",
            "equipo_id": 1,
            "registros": [
                {
                    "tiempo": 1234567,
                    "horas": 0,
                    "minutos": 20,
                    "segundos": 34,
                    "milisegundos": 567
                },
                ...
            ]
        }
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Log de debug: recibimos el mensaje
            logger.info(f"[BATCH] Juez {self.juez.username} - Recibido batch para equipo {content.get('equipo_id')}")
            logger.info(f"[BATCH] Total registros en batch: {len(content.get('registros', []))}")
            
            # Validar datos del batch
            es_valido, error = validar_datos_batch(content)
            if not es_valido:
                logger.warning(f"[BATCH] Validación fallida: {error}")
                await self.send_json({
                    'tipo': 'error',
                    'mensaje': error
                })
                return
            
            equipo_id = content.get('equipo_id')
            registros = content.get('registros', [])
            
            # Procesar batch usando el servicio
            from app.services.registro_service import RegistroService
            
            service = RegistroService()
            resultado = await service.registrar_batch(
                juez=self.juez,
                equipo_id=equipo_id,
                registros=registros
            )
            
            # Log de resultado
            logger.info(f"[BATCH] Resultado - Guardados: {resultado['total_guardados']}, Fallidos: {resultado['total_fallidos']}")
            
            # Enviar respuesta con resumen
            await self.send_json({
                'tipo': 'tiempos_registrados_batch',
                'total_enviados': resultado['total_enviados'],
                'total_guardados': resultado['total_guardados'],
                'total_fallidos': resultado['total_fallidos'],
                'registros_guardados': resultado['registros_guardados'],
                'registros_fallidos': resultado['registros_fallidos']
            })
            
            logger.info(f"[BATCH] Respuesta enviada al cliente")
            
        except Exception as e:
            logger.error(f"[BATCH] Error crítico: {str(e)}", exc_info=True)
            await self.send_json({
                'tipo': 'error',
                'mensaje': f'Error al procesar batch: {str(e)}'
            })

    # Manejadores de eventos de grupo
    async def competencia_iniciada(self, event):
        """
        Notifica al cliente que la competencia ha iniciado.
        Ahora puede enviar registros de tiempos.
        """
        await self.send_json({
            'tipo': 'competencia_iniciada',
            'mensaje': event['data']['mensaje'],
            'competencia': {
                'id': event['data']['competencia_id'],
                'nombre': event['data']['competencia_nombre'],
                'en_curso': event['data']['en_curso'],
            }
        })
    
    async def competencia_detenida(self, event):
        """
        Notifica al cliente que la competencia ha finalizado.
        Ya no puede enviar más registros de tiempos.
        """
        await self.send_json({
            'tipo': 'competencia_detenida',
            'mensaje': event['data']['mensaje'],
            'competencia': {
                'id': event['data']['competencia_id'],
                'nombre': event['data']['competencia_nombre'],
                'en_curso': event['data']['en_curso'],
            }
        })

    async def carrera_iniciada(self, event):
        """Mantener compatibilidad con código antiguo"""
        await self.send_json({
            'type': 'carrera.iniciada',
            'data': event.get('data', {})
        })
