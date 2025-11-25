from django.db import models
from django.utils import timezone

CATEGORIA_CHOICES = [
    ('estudiantes', 'Estudiantes por Equipos'),
    ('interfacultades', 'Interfacultades por Equipos'),
]

class Competencia(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    datetime = models.DateTimeField(verbose_name="Fecha y hora")
    category = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES,
        verbose_name="Categoría",
    )

    is_active = models.BooleanField(default=True, verbose_name="Activa")
    is_running = models.BooleanField(default=False, verbose_name="En curso")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de inicio")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de finalización")

    class Meta:
        verbose_name = "Competencia"
        verbose_name_plural = "Competencias"

    def __str__(self):
        return self.name

    def start(self):
        """Inicia la competencia"""
        if not self.is_running:
            self.is_running = True
            self.started_at = timezone.now()
            self.save()
            return True
        return False

    def stop(self):
        """Detiene la competencia"""
        if self.is_running:
            self.is_running = False
            self.finished_at = timezone.now()
            self.save()
            return True
        return False

    def get_status_code(self):
        """Retorna el código de estado de la competencia"""
        if self.is_running:
            return 'running'
        elif self.finished_at:
            return 'finished'
        return 'scheduled'

    def get_status_display(self):
        """Retorna el texto descriptivo del estado"""
        estados = {
            'running': 'En Curso',
            'finished': 'Finalizada',
            'scheduled': 'Programada',
        }
        return estados.get(self.get_status_code(), 'Desconocido')
