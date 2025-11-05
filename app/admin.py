from django.contrib import admin

# Register your models here.
from .models import Competencia, Juez, Equipo, RegistroTiempo
admin.site.register(Competencia)
admin.site.register(Juez)
admin.site.register(Equipo)
admin.site.register(RegistroTiempo)

