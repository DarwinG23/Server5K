"""
Módulo: registrotiempo
Define los modelos para gestionar registros de tiempo de los equipos.
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class RegistroTiempo(models.Model):
    id_registro = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    equipo = models.ForeignKey(
        'Equipo', 
        on_delete=models.CASCADE, 
        related_name='tiempos'
    )
    
    # Relación directa con competencia para evitar datos inconsistentes
    competencia = models.ForeignKey(
        'Competencia',
        on_delete=models.CASCADE,
        related_name='registros_tiempo',
        verbose_name="Competencia"
    )
    
    # Keep a single integer field for total milliseconds (used for ordering/search)
    tiempo = models.BigIntegerField(help_text="Tiempo en milisegundos")

    # New, more granular fields
    horas = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    minutos = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(59)])
    segundos = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(59)])
    milisegundos = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(999)])

    timestamp = models.DateTimeField(default=timezone.now)
    
    @property
    def juez(self):
        return self.equipo.juez_asignado
    
    class Meta:
        ordering = ['tiempo']
        indexes = [
            models.Index(fields=['equipo', 'tiempo']),
        ]
        
    def __str__(self):
        return f"Registro {self.id_registro} - Equipo: {self.equipo.nombre} - Tiempo: {self.tiempo} ms"

    def save(self, *args, **kwargs):
        """
        Keep `tiempo` (total milliseconds) consistent with the granular fields.

        - If any of the granular fields are non-zero, compute `tiempo` from them.
        - Otherwise, if all granular fields are zero and `tiempo` is present, derive the granular
          fields from `tiempo` so existing records are preserved.
        - Auto-assign competencia from equipo if not provided.
        """
        # Auto-asignar competencia desde el equipo si no está presente
        if not self.competencia_id:
            self.competencia = self.equipo.competencia
        
        try:
            any_component = any([self.horas, self.minutos, self.segundos, self.milisegundos])
        except Exception:
            # In migrations or when fields aren't available yet, defer to default save
            return super().save(*args, **kwargs)

        if any_component:
            total_ms = ((int(self.horas) * 3600 + int(self.minutos) * 60 + int(self.segundos)) * 1000) + int(self.milisegundos)
            self.tiempo = int(total_ms)
        else:
            # derive components from existing tiempo
            total = int(self.tiempo or 0)
            ms = total % 1000
            total_seconds = total // 1000
            s = total_seconds % 60
            total_minutes = total_seconds // 60
            m = total_minutes % 60
            h = total_minutes // 60
            self.horas = h
            self.minutos = m
            self.segundos = s
            self.milisegundos = ms

        return super().save(*args, **kwargs)
