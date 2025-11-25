"""
Módulo: registro_service
Responsable de procesar y validar los registros de tiempo enviados por los jueces.
Asegura idempotencia, concurrencia y transacciones seguras.

Características:
- Validación de equipos y jueces
- Idempotencia por id_registro
- Transacciones atómicas
- Evita duplicados
- Limita a máximo 15 registros por equipo
"""

from django.db import transaction
from channels.db import database_sync_to_async
from typing import Dict, List, Any
import uuid


class RegistroService:
    """
    Servicio para gestionar el registro de tiempos de equipos.
    """
    
    MAX_REGISTROS_POR_EQUIPO = 15
    
    @database_sync_to_async
    def registrar_tiempo(
        self,
        juez,
        equipo_id: int,
        tiempo: int,
        horas: int = 0,
        minutos: int = 0,
        segundos: int = 0,
        milisegundos: int = 0,
        id_registro: str = None
    ) -> Dict[str, Any]:
        """
        Registra un tiempo para un equipo de manera segura y atómica.
        
        Args:
            juez: Instancia del modelo Juez
            equipo_id: ID del equipo
            tiempo: Tiempo total en milisegundos
            horas: Componente de horas
            minutos: Componente de minutos
            segundos: Componente de segundos
            milisegundos: Componente de milisegundos
            id_registro: UUID opcional para idempotencia
            
        Returns:
            Dict con claves 'exito', 'registro' (si exitoso) o 'error' (si falla)
        """
        from app.models import Equipo, RegistroTiempo, Juez
        
        try:
            with transaction.atomic():
                # Refrescar el juez con su competencia para tener datos actualizados
                juez_actualizado = Juez.objects.select_related('competencia').get(id=juez.id)
                
                # Verificar que la competencia esté en curso
                if not juez_actualizado.competencia or not juez_actualizado.competencia.en_curso:
                    return {
                        'exito': False,
                        'error': 'No se pueden registrar tiempos. La competencia no ha iniciado o ya finalizó.'
                    }
                
                # Verificar que el equipo existe y pertenece a este juez
                try:
                    equipo = Equipo.objects.select_for_update().get(id=equipo_id)
                except Equipo.DoesNotExist:
                    return {
                        'exito': False,
                        'error': f'El equipo con ID {equipo_id} no existe'
                    }
                
                if equipo.juez_asignado_id != juez.id:
                    return {
                        'exito': False,
                        'error': f'El equipo con ID {equipo_id} no pertenece a tu lista de equipos asignados'
                    }
                
                # Verificar si ya existe un registro con este id_registro (idempotencia)
                if id_registro:
                    registro_existente = RegistroTiempo.objects.filter(
                        id_registro=id_registro
                    ).first()
                    
                    if registro_existente:
                        return {
                            'exito': True,
                            'registro': registro_existente,
                            'duplicado': True
                        }
                
                # Contar registros actuales del equipo en esta competencia
                num_registros = RegistroTiempo.objects.filter(
                    equipo=equipo,
                    competencia=juez_actualizado.competencia
                ).count()
                
                if num_registros >= self.MAX_REGISTROS_POR_EQUIPO:
                    return {
                        'exito': False,
                        'error': f'El equipo ya tiene el máximo de {self.MAX_REGISTROS_POR_EQUIPO} registros permitidos'
                    }
                
                # Crear el registro de tiempo
                registro = RegistroTiempo.objects.create(
                    id_registro=id_registro or uuid.uuid4(),
                    equipo=equipo,
                    competencia=juez_actualizado.competencia,
                    tiempo=tiempo,
                    horas=horas,
                    minutos=minutos,
                    segundos=segundos,
                    milisegundos=milisegundos
                )
                
                return {
                    'exito': True,
                    'registro': registro,
                    'duplicado': False
                }
                
        except Exception as e:
            return {
                'exito': False,
                'error': f'Error al guardar registro: {str(e)}'
            }
    
    @database_sync_to_async
    def registrar_batch(
        self,
        juez,
        equipo_id: int,
        registros: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Registra múltiples tiempos en batch de manera transaccional.
        
        Args:
            juez: Instancia del modelo Juez
            equipo_id: ID del equipo
            registros: Lista de diccionarios con datos de registros
            
        Returns:
            Dict con resumen de registros guardados y fallidos
        """
        from app.models import Equipo, RegistroTiempo, Juez
        
        registros_guardados = []
        registros_fallidos = []
        
        try:
            with transaction.atomic():
                # Refrescar el juez con su competencia
                juez_actualizado = Juez.objects.select_related('competencia').get(id=juez.id)
                
                # Verificar que la competencia esté en curso
                if not juez_actualizado.competencia or not juez_actualizado.competencia.en_curso:
                    return {
                        'total_enviados': len(registros),
                        'total_guardados': 0,
                        'total_fallidos': len(registros),
                        'registros_guardados': [],
                        'registros_fallidos': [
                            {'indice': i, 'error': 'La competencia no está en curso'}
                            for i in range(len(registros))
                        ]
                    }
                
                # Verificar que el equipo existe y pertenece a este juez
                try:
                    equipo = Equipo.objects.select_for_update().get(id=equipo_id)
                except Equipo.DoesNotExist:
                    return {
                        'total_enviados': len(registros),
                        'total_guardados': 0,
                        'total_fallidos': len(registros),
                        'registros_guardados': [],
                        'registros_fallidos': [
                            {'indice': i, 'error': f'El equipo con ID {equipo_id} no existe'}
                            for i in range(len(registros))
                        ]
                    }
                
                if equipo.juez_asignado_id != juez.id:
                    return {
                        'total_enviados': len(registros),
                        'total_guardados': 0,
                        'total_fallidos': len(registros),
                        'registros_guardados': [],
                        'registros_fallidos': [
                            {'indice': i, 'error': 'El equipo no pertenece a este juez'}
                            for i in range(len(registros))
                        ]
                    }
                
                # Contar registros actuales
                num_registros_actuales = RegistroTiempo.objects.filter(
                    equipo=equipo,
                    competencia=juez_actualizado.competencia
                ).count()
                
                # Procesar cada registro
                for idx, reg in enumerate(registros):
                    try:
                        # Verificar límite
                        if num_registros_actuales >= self.MAX_REGISTROS_POR_EQUIPO:
                            registros_fallidos.append({
                                'indice': idx,
                                'error': f'Se alcanzó el límite de {self.MAX_REGISTROS_POR_EQUIPO} registros'
                            })
                            continue
                        
                        tiempo = reg.get('tiempo')
                        horas = reg.get('horas', 0)
                        minutos = reg.get('minutos', 0)
                        segundos = reg.get('segundos', 0)
                        milisegundos = reg.get('milisegundos', 0)
                        id_registro = reg.get('id_registro')
                        
                        if tiempo is None:
                            registros_fallidos.append({
                                'indice': idx,
                                'error': 'Falta el campo tiempo'
                            })
                            continue
                        
                        # Verificar idempotencia
                        if id_registro:
                            registro_existente = RegistroTiempo.objects.filter(
                                id_registro=id_registro
                            ).first()
                            
                            if registro_existente:
                                registros_guardados.append({
                                    'indice': idx,
                                    'id_registro': str(registro_existente.id_registro),
                                    'tiempo': registro_existente.tiempo,
                                    'duplicado': True
                                })
                                continue
                        
                        # Crear el registro
                        registro = RegistroTiempo.objects.create(
                            id_registro=id_registro or uuid.uuid4(),
                            equipo=equipo,
                            competencia=juez_actualizado.competencia,
                            tiempo=tiempo,
                            horas=horas,
                            minutos=minutos,
                            segundos=segundos,
                            milisegundos=milisegundos
                        )
                        
                        registros_guardados.append({
                            'indice': idx,
                            'id_registro': str(registro.id_registro),
                            'tiempo': registro.tiempo,
                            'duplicado': False
                        })
                        
                        num_registros_actuales += 1
                        
                    except Exception as e:
                        registros_fallidos.append({
                            'indice': idx,
                            'error': str(e)
                        })
                
                return {
                    'total_enviados': len(registros),
                    'total_guardados': len(registros_guardados),
                    'total_fallidos': len(registros_fallidos),
                    'registros_guardados': registros_guardados,
                    'registros_fallidos': registros_fallidos
                }
                
        except Exception as e:
            return {
                'total_enviados': len(registros),
                'total_guardados': 0,
                'total_fallidos': len(registros),
                'registros_guardados': [],
                'registros_fallidos': [
                    {'indice': i, 'error': f'Error general: {str(e)}'}
                    for i in range(len(registros))
                ]
            }
