"""
Módulo: competencia
Define el modelo de Competencia para gestionar eventos deportivos.
"""

from django.db import models
from django.utils import timezone

CATEGORIA_CHOICES = [
    ('estudiantes', 'Estudiantes por Equipos'),
    ('interfacultades', 'Interfacultades por Equipos'),
]


class Competencia(models.Model):
    nombre = models.CharField(max_length=200)
    fecha_hora = models.DateTimeField()
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES
    )
    activa = models.BooleanField(default=True)
    en_curso = models.BooleanField(default=False, verbose_name="En curso")
    fecha_inicio = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de inicio")
    fecha_fin = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de finalización")
    
    def iniciar_competencia(self):
        """Inicia la competencia"""
        if not self.en_curso:
            self.en_curso = True
            self.fecha_inicio = timezone.now()
            self.save()
            return True
        return False
    
    def detener_competencia(self):
        """Detiene la competencia"""
        if self.en_curso:
            self.en_curso = False
            self.fecha_fin = timezone.now()
            self.save()
            return True
        return False
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Competencia"
        verbose_name_plural = "Competencias"
        
    def get_estado_display(self):
        """Retorna el estado actual de la competencia"""
        if self.en_curso:
            return 'en_curso'
        elif self.fecha_fin:
            return 'finalizada'
        else:
            return 'programada'
    
    def get_estado_texto(self):
        """Retorna el texto del estado para mostrar"""
        estado = self.get_estado_display()
        estados = {
            'en_curso': 'En Curso',
            'finalizada': 'Finalizada',
            'programada': 'Programada'
        }
        return estados.get(estado, 'Desconocido')
