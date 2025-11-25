from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class RegistroTiempo(models.Model):
    record_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID de registro"
    )

    team = models.ForeignKey(
        'Equipo',
        on_delete=models.CASCADE,
        related_name='times',
        verbose_name='Equipo',
    )

    time = models.BigIntegerField(help_text="Tiempo en milisegundos", verbose_name="Tiempo")

    hours = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Horas")
    minutes = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(59)],
        verbose_name="Minutos"
    )
    seconds = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(59)],
        verbose_name="Segundos"
    )
    milliseconds = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(999)],
        verbose_name="Milisegundos"
    )

    created_at = models.DateTimeField(default=timezone.now, verbose_name="Fecha de creación")

    class Meta:
        ordering = ['time']
        indexes = [
            models.Index(fields=['team', 'time']),
        ]
        verbose_name = "Registro de Tiempo"
        verbose_name_plural = "Registros de Tiempo"

    def __str__(self):
        return f"Registro {self.record_id} - Equipo: {self.team.name} - {self.time} ms"

    @property
    def competition(self):
        """Retorna la competencia del equipo"""
        return self.team.competition

    @property
    def judge(self):
        """Retorna el juez asignado al equipo"""
        return getattr(self.team, 'judge', None)

    def save(self, *args, **kwargs):
        """Calcula tiempo total desde componentes o viceversa"""
        any_component = any([self.hours, self.minutes, self.seconds, self.milliseconds])
        if any_component:
            total_ms = (
                (int(self.hours) * 3600 + int(self.minutes) * 60 + int(self.seconds)) * 1000
                + int(self.milliseconds)
            )
            self.time = int(total_ms)
        else:
            total = int(self.time or 0)
            ms = total % 1000
            total_seconds = total // 1000
            s = total_seconds % 60
            total_minutes = total_seconds // 60
            m = total_minutes % 60
            h = total_minutes // 60
            self.hours = h
            self.minutes = m
            self.seconds = s
            self.milliseconds = ms

        return super().save(*args, **kwargs)
