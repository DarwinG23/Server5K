"""
Módulo: juez
Define el modelo de Juez para gestionar la autenticación y permisos de los jueces.
"""

from django.db import models


class Juez(models.Model):
    # Credenciales de autenticación
    username = models.CharField(max_length=150, unique=True, verbose_name="Usuario")
    password = models.CharField(max_length=128, verbose_name="Contraseña")
    
    # Información personal
    first_name = models.CharField(max_length=150, blank=True, verbose_name="Nombre")
    last_name = models.CharField(max_length=150, blank=True, verbose_name="Apellido")
    email = models.EmailField(blank=True, verbose_name="Email")
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    
    # Relación con competencia
    competencia = models.ForeignKey(
        'Competencia', 
        on_delete=models.CASCADE, 
        related_name='jueces',
        verbose_name="Competencia"
    )
    
    # Estado
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    last_login = models.DateTimeField(null=True, blank=True, verbose_name="Último login")
    
    class Meta:
        verbose_name = "Juez"
        verbose_name_plural = "Jueces"
    
    def __str__(self):
        full_name = self.get_full_name()
        if full_name:
            return f"{full_name} - {self.competencia.nombre}"
        return f"{self.username} - {self.competencia.nombre}"
    
    def get_full_name(self):
        """Retorna el nombre completo del juez"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def set_password(self, raw_password):
        """Establece la contraseña hasheada"""
        from django.contrib.auth.hashers import make_password
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Verifica la contraseña"""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password)
    
    @property
    def is_authenticated(self):
        """Siempre retorna True para compatibilidad con JWT"""
        return True
