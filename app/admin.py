from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Min, Max
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django import forms
from .models import Competencia, Juez, Equipo, RegistroTiempo
from .models import Competencia, Juez, Equipo, RegistroTiempo, ResultadoEquipo


# ==================== FILTROS PERSONALIZADOS ====================

class EstadoCompetenciaFilter(admin.SimpleListFilter):
    """Filtro personalizado para el estado de las competencias"""
    title = 'Estado de la Competencia'
    parameter_name = 'estado'

    def lookups(self, request, model_admin):
        return (
            ('en_curso', '🟢 En Curso'),
            ('finalizada', '⚫ Finalizada'),
            ('programada', '🟠 Programada'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'en_curso':
            return queryset.filter(en_curso=True)
        if self.value() == 'finalizada':
            return queryset.filter(en_curso=False).exclude(fecha_fin__isnull=True)
        if self.value() == 'programada':
            return queryset.filter(en_curso=False, fecha_fin__isnull=True)
        return queryset


class FechaCompetenciaFilter(admin.SimpleListFilter):
    """Filtro por proximidad de fecha"""
    title = 'Fecha'
    parameter_name = 'fecha'

    def lookups(self, request, model_admin):
        return (
            ('hoy', 'Hoy'),
            ('esta_semana', 'Esta Semana'),
            ('este_mes', 'Este Mes'),
            ('pasadas', 'Pasadas'),
            ('futuras', 'Futuras'),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'hoy':
            return queryset.filter(fecha_hora__date=now.date())
        if self.value() == 'esta_semana':
            start_week = now - timezone.timedelta(days=now.weekday())
            return queryset.filter(fecha_hora__gte=start_week)
        if self.value() == 'este_mes':
            return queryset.filter(fecha_hora__month=now.month, fecha_hora__year=now.year)
        if self.value() == 'pasadas':
            return queryset.filter(fecha_hora__lt=now)
        if self.value() == 'futuras':
            return queryset.filter(fecha_hora__gte=now)
        return queryset


# ==================== INLINES ====================

class JuezInline(admin.TabularInline):
    """Inline para mostrar jueces en la competencia"""
    model = Juez
    extra = 0
    fields = ['username', 'get_full_name', 'email', 'activo']
    readonly_fields = ['get_full_name']
    can_delete = False
    
    def get_full_name(self, obj):
        return obj.get_full_name() or '-'
    get_full_name.short_description = 'Nombre Completo'


class EquipoInline(admin.TabularInline):
    """Inline para mostrar equipos asignados a un juez"""
    model = Equipo
    extra = 0
    fields = ['dorsal', 'nombre', 'num_registros_display']
    readonly_fields = ['num_registros_display']
    
    def num_registros_display(self, obj):
        if obj.pk:
            count = obj.tiempos.count()
            return format_html('<strong>{}</strong> registros', count)
        return '-'
    num_registros_display.short_description = 'Registros'


class RegistroTiempoInline(admin.TabularInline):
    """Inline para mostrar registros de tiempo de un equipo"""
    model = RegistroTiempo
    extra = 0
    fields = ['tiempo_formateado_display', 'timestamp', 'competencia']
    readonly_fields = ['tiempo_formateado_display', 'timestamp', 'competencia']
    can_delete = True
    ordering = ['tiempo']
    
    def tiempo_formateado_display(self, obj):
        if obj.pk:
            return format_html(
                '<strong>{}h {}m {}s {}ms</strong>',
                obj.horas, obj.minutos, obj.segundos, obj.milisegundos
            )
        return '-'
    tiempo_formateado_display.short_description = 'Tiempo'


# ==================== COMPETENCIA ADMIN ====================

@admin.register(Competencia)
class CompetenciaAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 
        'fecha_hora_formateada', 
        'categoria', 
        'estado_competencia', 
        'total_equipos',
        'total_registros',
        'activa', 
        'acciones_competencia'
    ]
    list_filter = [EstadoCompetenciaFilter, 'categoria', 'activa', FechaCompetenciaFilter]
    search_fields = ['nombre']
    readonly_fields = ['fecha_inicio', 'fecha_fin', 'estadisticas_competencia']
    date_hierarchy = 'fecha_hora'
    list_per_page = 25
    
    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'fecha_hora', 'categoria', 'activa')
        }),
        ('Estado de la Competencia', {
            'fields': ('en_curso', 'fecha_inicio', 'fecha_fin'),
            'classes': ('collapse',)
        }),
        ('Estadísticas', {
            'fields': ('estadisticas_competencia',),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [JuezInline]
    
    actions = ['iniciar_competencias_seleccionadas', 'detener_competencias_seleccionadas', 'activar_competencias', 'desactivar_competencias']

    def fecha_hora_formateada(self, obj):
        """Muestra la fecha y hora de forma más legible"""
        return format_html(
            '<div style="white-space: nowrap;">'
            '<i class="bi bi-calendar"></i> {}<br>'
            '<i class="bi bi-clock"></i> {}'
            '</div>',
            obj.fecha_hora.strftime('%d/%m/%Y'),
            obj.fecha_hora.strftime('%H:%M')
        )
    fecha_hora_formateada.short_description = 'Fecha y Hora'
    fecha_hora_formateada.admin_order_field = 'fecha_hora'

    def estado_competencia(self, obj):
        """Muestra el estado con colores y estilos"""
        if obj.en_curso:
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">🟢 EN CURSO</span>'
            )
        elif obj.fecha_fin:
            return format_html(
                '<span style="color: #6b7280; font-weight: bold;">⚫ FINALIZADA</span>'
            )
        else:
            return format_html(
                '<span style="color: #f59e0b; font-weight: bold;">🟠 PROGRAMADA</span>'
            )
    estado_competencia.short_description = 'Estado'
    
    def total_equipos(self, obj):
        """Muestra el total de equipos participantes"""
        total = Equipo.objects.filter(juez_asignado__competencia=obj).count()
        return format_html('<strong>{}</strong>', total)
    total_equipos.short_description = 'Equipos'
    
    def total_registros(self, obj):
        """Muestra el total de registros de tiempo"""
        total = RegistroTiempo.objects.filter(competencia=obj).count()
        if total > 0:
            return format_html('<span style="color: #2563eb; font-weight: bold;">{}</span>', total)
        return format_html('<span style="color: #9ca3af;">{}</span>', total)
    total_registros.short_description = 'Registros'

    def acciones_competencia(self, obj):
        """Botones de acción para iniciar/detener competencias"""
        if obj.en_curso:
            return format_html(
                '<a class="button" style="background-color: #dc2626; color: white; padding: 5px 10px; '
                'text-decoration: none; border-radius: 4px;" href="{}">🛑 Detener</a>',
                reverse('admin:detener-competencia', args=[obj.pk])
            )
        else:
            return format_html(
                '<a class="button" style="background-color: #10b981; color: white; padding: 5px 10px; '
                'text-decoration: none; border-radius: 4px;" href="{}">▶️ Iniciar</a>',
                reverse('admin:iniciar-competencia', args=[obj.pk])
            )
    acciones_competencia.short_description = 'Acciones'
    
    def estadisticas_competencia(self, obj):
        """Muestra estadísticas detalladas de la competencia"""
        equipos = Equipo.objects.filter(juez_asignado__competencia=obj)
        registros = RegistroTiempo.objects.filter(competencia=obj)
        
        stats = registros.aggregate(
            total=Count('id'),
            tiempo_min=Min('tiempo'),
            tiempo_max=Max('tiempo'),
            tiempo_avg=Avg('tiempo')
        )
        
        html = '<div style="font-family: monospace; line-height: 1.8;">'
        html += f'<strong>Total de Equipos:</strong> {equipos.count()}<br>'
        html += f'<strong>Total de Registros:</strong> {stats["total"]}<br>'
        
        if stats['tiempo_min']:
            html += f'<strong>Mejor Tiempo:</strong> {stats["tiempo_min"]} ms<br>'
        if stats['tiempo_max']:
            html += f'<strong>Peor Tiempo:</strong> {stats["tiempo_max"]} ms<br>'
        if stats['tiempo_avg']:
            html += f'<strong>Tiempo Promedio:</strong> {int(stats["tiempo_avg"])} ms<br>'
        
        html += '</div>'
        return format_html(html)
    estadisticas_competencia.short_description = 'Estadísticas'

    # Acciones en lote
    def iniciar_competencias_seleccionadas(self, request, queryset):
        """Inicia múltiples competencias"""
        count = 0
        for competencia in queryset:
            if competencia.iniciar_competencia():
                count += 1
        self.message_user(request, f'{count} competencia(s) iniciada(s) exitosamente.', messages.SUCCESS)
    iniciar_competencias_seleccionadas.short_description = '▶️ Iniciar competencias seleccionadas'
    
    def detener_competencias_seleccionadas(self, request, queryset):
        """Detiene múltiples competencias"""
        count = 0
        for competencia in queryset:
            if competencia.detener_competencia():
                count += 1
        self.message_user(request, f'{count} competencia(s) detenida(s) exitosamente.', messages.SUCCESS)
    detener_competencias_seleccionadas.short_description = '🛑 Detener competencias seleccionadas'
    
    def activar_competencias(self, request, queryset):
        """Activa competencias"""
        updated = queryset.update(activa=True)
        self.message_user(request, f'{updated} competencia(s) activada(s).', messages.SUCCESS)
    activar_competencias.short_description = '✅ Activar competencias'
    
    def desactivar_competencias(self, request, queryset):
        """Desactiva competencias"""
        updated = queryset.update(activa=False)
        self.message_user(request, f'{updated} competencia(s) desactivada(s).', messages.SUCCESS)
    desactivar_competencias.short_description = '❌ Desactivar competencias'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/iniciar/', self.admin_site.admin_view(self.iniciar_competencia_view), name='iniciar-competencia'),
            path('<int:pk>/detener/', self.admin_site.admin_view(self.detener_competencia_view), name='detener-competencia'),
        ]
        return custom_urls + urls

    def iniciar_competencia_view(self, request, pk):
        competencia = Competencia.objects.get(pk=pk)
        if competencia.iniciar_competencia():
            messages.success(request, f'La competencia "{competencia.nombre}" ha sido iniciada exitosamente.')
            # Notificar a los jueces vía WebSocket
            channel_layer = get_channel_layer()
            for juez in competencia.jueces.all():
                group = f'juez_{juez.id}'
                async_to_sync(channel_layer.group_send)(
                    group,
                    {
                        'type': 'competencia.iniciada',
                        'data': {
                            'mensaje': 'La competencia ha iniciado. Ya puedes registrar tiempos.',
                            'competencia_id': competencia.id,
                            'competencia_nombre': competencia.nombre,
                            'en_curso': True,
                        }
                    }
                )
        else:
            messages.warning(request, f'La competencia "{competencia.nombre}" ya está en curso.')
        return redirect('admin:app_competencia_changelist')

    def detener_competencia_view(self, request, pk):
        competencia = Competencia.objects.get(pk=pk)
        if competencia.detener_competencia():
            messages.success(request, f'La competencia "{competencia.nombre}" ha sido detenida exitosamente.')
            # Notificar a los jueces vía WebSocket
            channel_layer = get_channel_layer()
            for juez in competencia.jueces.all():
                group = f'juez_{juez.id}'
                async_to_sync(channel_layer.group_send)(
                    group,
                    {
                        'type': 'competencia.detenida',
                        'data': {
                            'mensaje': 'La competencia ha finalizado. No se pueden registrar más tiempos.',
                            'competencia_id': competencia.id,
                            'competencia_nombre': competencia.nombre,
                            'en_curso': False,
                        }
                    }
                )
        else:
            messages.warning(request, f'La competencia "{competencia.nombre}" no está en curso.')
        return redirect('admin:app_competencia_changelist')


# ==================== JUEZ ADMIN ====================

class JuezForm(forms.ModelForm):
    """Formulario personalizado para crear/editar jueces"""
    password1 = forms.CharField(
        label='Contraseña', 
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}), 
        required=False,
        help_text='Deja en blanco si no deseas cambiar la contraseña'
    )
    password2 = forms.CharField(
        label='Confirmar contraseña', 
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}), 
        required=False
    )

    class Meta:
        model = Juez
        fields = ['username', 'first_name', 'last_name', 'email', 'telefono', 'competencia', 'activo']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        # Si es un nuevo juez, la contraseña es requerida
        if not self.instance.pk and not password1:
            raise forms.ValidationError('La contraseña es requerida para nuevos jueces.')

        # Si se proporciona contraseña, deben coincidir
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError('Las contraseñas no coinciden.')

        return cleaned_data

    def save(self, commit=True):
        juez = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        if password:
            juez.set_password(password)
        if commit:
            juez.save()
        return juez


@admin.register(Juez)
class JuezAdmin(admin.ModelAdmin):
    form = JuezForm
    list_display = [
        'username', 
        'get_full_name_display', 
        'email', 
        'telefono',
        'competencia', 
        'total_equipos_asignados',
        'activo_badge', 
        'fecha_creacion'
    ]
    list_filter = ['competencia', 'activo', 'fecha_creacion']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'telefono']
    ordering = ['-fecha_creacion']
    readonly_fields = ['fecha_creacion', 'last_login']
    list_per_page = 25
    
    fieldsets = (
        ('Credenciales de Acceso', {
            'fields': ('username', 'password1', 'password2'),
            'description': 'Configura las credenciales de acceso del juez'
        }),
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'email', 'telefono')
        }),
        ('Asignación', {
            'fields': ('competencia', 'activo'),
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [EquipoInline]
    
    actions = ['activar_jueces', 'desactivar_jueces']

    def get_full_name_display(self, obj):
        full_name = obj.get_full_name()
        if full_name:
            return format_html('<strong>{}</strong>', full_name)
        return format_html('<em style="color: #9ca3af;">{}</em>', obj.username)
    get_full_name_display.short_description = 'Nombre Completo'
    get_full_name_display.admin_order_field = 'first_name'
    
    def activo_badge(self, obj):
        if obj.activo:
            return format_html('<span style="color: #10b981;">✓ Activo</span>')
        return format_html('<span style="color: #ef4444;">✗ Inactivo</span>')
    activo_badge.short_description = 'Estado'
    activo_badge.admin_order_field = 'activo'
    
    def total_equipos_asignados(self, obj):
        total = obj.equipos_asignados.count()
        return format_html('<strong>{}</strong>', total)
    total_equipos_asignados.short_description = 'Equipos'
    
    def activar_jueces(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} juez/jueces activado(s).', messages.SUCCESS)
    activar_jueces.short_description = '✅ Activar jueces'
    
    def desactivar_jueces(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} juez/jueces desactivado(s).', messages.SUCCESS)
    desactivar_jueces.short_description = '❌ Desactivar jueces'


# ==================== EQUIPO ADMIN ====================

@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = [
        'dorsal_badge',
        'nombre', 
        'juez_asignado', 
        'competencia_display',
        'total_registros',
        'mejor_tiempo_display',
        'tiempo_promedio_display'
    ]
    list_filter = ['juez_asignado__competencia', 'juez_asignado']
    search_fields = ['nombre', 'dorsal', 'juez_asignado__username']
    ordering = ['dorsal']
    list_per_page = 25
    
    fieldsets = (
        ('Información del Equipo', {
            'fields': ('nombre', 'dorsal', 'juez_asignado')
        }),
        ('Estadísticas', {
            'fields': ('estadisticas_equipo',)
        }),
    )
    
    readonly_fields = ['estadisticas_equipo']
    
    def dorsal_badge(self, obj):
        return format_html(
            '<span style="background-color: #1f2937; color: white; padding: 4px 8px; '
            'border-radius: 4px; font-weight: bold;">{}</span>',
            obj.dorsal
        )
    dorsal_badge.short_description = 'Dorsal'
    dorsal_badge.admin_order_field = 'dorsal'
    
    def competencia_display(self, obj):
        return obj.competencia
    competencia_display.short_description = 'Competencia'
    
    def total_registros(self, obj):
        count = obj.tiempos.count()
        if count > 0:
            return format_html('<strong style="color: #2563eb;">{}</strong>', count)
        return format_html('<span style="color: #9ca3af;">{}</span>', count)
    total_registros.short_description = 'Registros'
    
    def mejor_tiempo_display(self, obj):
        mejor = obj.mejor_tiempo()
        if mejor:
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">{}h {}m {}s</span>',
                mejor.horas, mejor.minutos, mejor.segundos
            )
        return '-'
    mejor_tiempo_display.short_description = 'Mejor Tiempo'
    
    def tiempo_promedio_display(self, obj):
        promedio = obj.tiempo_promedio()
        if promedio > 0:
            segundos = promedio / 1000
            segundos_formateado = '{:.2f}'.format(segundos)
            return format_html('<strong>{}s</strong>', segundos_formateado)
        return '-'
    tiempo_promedio_display.short_description = 'Promedio'
    
    def estadisticas_equipo(self, obj):
        """Muestra estadísticas detalladas del equipo"""
        html = '<div style="font-family: monospace; line-height: 1.8;">'
        html += f'<strong>Total de Registros:</strong> {obj.numero_registros()}<br>'
        html += f'<strong>Tiempo Total:</strong> {obj.tiempo_total_formateado()}<br>'
        
        mejor = obj.mejor_tiempo()
        if mejor:
            html += f'<strong>Mejor Tiempo:</strong> {mejor.horas}h {mejor.minutos}m {mejor.segundos}s {mejor.milisegundos}ms<br>'
        
        promedio = obj.tiempo_promedio()
        if promedio > 0:
            segundos_prom = promedio / 1000
            html += f'<strong>Tiempo Promedio:</strong> {promedio} ms ({segundos_prom:.2f}s)<br>'
        
        html += '</div>'
        return format_html(html)
    estadisticas_equipo.short_description = 'Estadísticas Detalladas'



# ==================== REGISTRO TIEMPO ADMIN MEJORADO ====================

@admin.register(RegistroTiempo)
class RegistroTiempoAdmin(admin.ModelAdmin):
    list_display = [
        'id_registro_corto',
        'equipo_con_dorsal',
        'competencia', 
        'tiempo_formateado_display',
        'timestamp_display'
    ]
    list_filter = ['competencia', 'equipo__juez_asignado__competencia', 'equipo', 'timestamp']
    search_fields = ['id_registro', 'equipo__nombre', 'equipo__dorsal']
    readonly_fields = ['id_registro', 'timestamp', 'competencia', 'tiempo_calculado']
    date_hierarchy = 'timestamp'
    ordering = ['competencia', 'equipo', 'tiempo']  # Agrupar por competencia y equipo
    list_per_page = 50
    
    fieldsets = (
        ('Información del Registro', {
            'fields': ('id_registro', 'equipo', 'competencia', 'timestamp')
        }),
        ('Tiempo Registrado', {
            'fields': ('horas', 'minutos', 'segundos', 'milisegundos', 'tiempo_calculado')
        }),
    )
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        qs = super().get_queryset(request)
        return qs.select_related('equipo', 'competencia')
    
    def id_registro_corto(self, obj):
        return format_html('<code>{}</code>', str(obj.id_registro)[:8])
    id_registro_corto.short_description = 'ID'
    
    def equipo_con_dorsal(self, obj):
        """Muestra el equipo con su dorsal"""
        return format_html(
            '<span style="background-color: #1f2937; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-weight: bold; margin-right: 5px;">{}</span> {}',
            obj.equipo.dorsal,
            obj.equipo.nombre
        )
    equipo_con_dorsal.short_description = 'Equipo'
    equipo_con_dorsal.admin_order_field = 'equipo__dorsal'
    
    def tiempo_formateado_display(self, obj):
        return format_html(
            '<strong style="color: #2563eb;">{}h {}m {}s {}ms</strong>',
            obj.horas, obj.minutos, obj.segundos, obj.milisegundos
        )
    tiempo_formateado_display.short_description = 'Tiempo'
    tiempo_formateado_display.admin_order_field = 'tiempo'
    
    def ranking_badge(self, obj):
        """Muestra el puesto del tiempo en la competencia"""
        # Obtener posición del tiempo en la competencia
        mejor_tiempos = RegistroTiempo.objects.filter(
            competencia=obj.competencia
        ).order_by('tiempo').values_list('id', flat=True)
        
        posicion = list(mejor_tiempos).index(obj.id) + 1 if obj.id in mejor_tiempos else None
        
        if posicion:
            if posicion == 1:
                return format_html('<span style="background-color: #ffd700; color: #000; padding: 3px 8px; border-radius: 4px; font-weight: bold;">🥇 #{}</span>', posicion)
            elif posicion == 2:
                return format_html('<span style="background-color: #c0c0c0; color: #000; padding: 3px 8px; border-radius: 4px; font-weight: bold;">🥈 #{}</span>', posicion)
            elif posicion == 3:
                return format_html('<span style="background-color: #cd7f32; color: #fff; padding: 3px 8px; border-radius: 4px; font-weight: bold;">🥉 #{}</span>', posicion)
            elif posicion <= 10:
                return format_html('<span style="background-color: #3b82f6; color: #fff; padding: 3px 8px; border-radius: 4px; font-weight: bold;">#{}</span>', posicion)
            else:
                return format_html('<span style="color: #6b7280;">#{}</span>', posicion)
        return '-'
    ranking_badge.short_description = 'Ranking'
    
    def timestamp_display(self, obj):
        return obj.timestamp.strftime('%d/%m/%Y %H:%M:%S')
    timestamp_display.short_description = 'Fecha/Hora'
    timestamp_display.admin_order_field = 'timestamp'
    
    def tiempo_calculado(self, obj):
        segundos = obj.tiempo / 1000
        segundos_formateado = '{:.3f}'.format(segundos)
        return format_html('<strong>{} ms</strong> ({} segundos)', obj.tiempo, segundos_formateado)
    tiempo_calculado.short_description = 'Tiempo Total'
    
    def ranking_en_competencia(self, obj):
        """Muestra información de ranking detallada"""
        registros = RegistroTiempo.objects.filter(competencia=obj.competencia).order_by('tiempo')
        posicion = list(registros.values_list('id', flat=True)).index(obj.id) + 1 if obj.id in registros.values_list('id', flat=True) else None
        
        if posicion:
            total = registros.count()
            return format_html(
                '<strong>Posición {} de {}</strong> en la competencia<br>'
                'Diferencia con el primero: <strong>{} ms</strong>',
                posicion, total,
                obj.tiempo - registros.first().tiempo if posicion > 1 else 0
            )
        return '-'
    ranking_en_competencia.short_description = 'Ranking Detallado'


# ==================== MODELO PROXY PARA RESULTADOS ====================

from django.db.models import Count, Min, Avg, Sum

@admin.register(ResultadoEquipo)
class ResultadoEquipoAdmin(admin.ModelAdmin):
    """Vista especial para ver resultados y rankings"""
    
    list_display = [
        'ranking_posicion',
        'dorsal_badge',
        'nombre',
        'competencia_display',
        'total_registros',
        'mejor_tiempo_display',
        'tiempo_promedio_display',
        'tiempo_total_display'
    ]
    list_filter = ['juez_asignado__competencia']
    search_fields = ['nombre', 'dorsal']
    ordering = ['juez_asignado__competencia', 'dorsal']
    list_per_page = 50
    
    def has_add_permission(self, request):
        """No permitir agregar desde esta vista"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar desde esta vista"""
        return False
    
    def get_queryset(self, request):
        """Optimizar consultas y agregar anotaciones"""
        qs = super().get_queryset(request)
        qs = qs.select_related('juez_asignado', 'juez_asignado__competencia')
        qs = qs.annotate(
            num_registros=Count('tiempos'),
            mejor_tiempo_ms=Min('tiempos__tiempo'),
            promedio_ms=Avg('tiempos__tiempo'),
            total_ms=Sum('tiempos__tiempo')
        )
        # Ordenar por mejor tiempo
        return qs.order_by('mejor_tiempo_ms')
    
    def ranking_posicion(self, obj):
        """Muestra la posición en el ranking general"""
        if hasattr(obj, 'mejor_tiempo_ms') and obj.mejor_tiempo_ms:
            # Obtener equipos de la misma competencia ordenados por mejor tiempo
            equipos = ResultadoEquipo.objects.filter(
                juez_asignado__competencia=obj.juez_asignado.competencia
            ).annotate(
                mejor_tiempo_ms=Min('tiempos__tiempo')
            ).order_by('mejor_tiempo_ms')
            
            posicion = list(equipos.values_list('id', flat=True)).index(obj.id) + 1
            
            if posicion == 1:
                return format_html('<span style="font-size: 24px;">🥇</span>')
            elif posicion == 2:
                return format_html('<span style="font-size: 24px;">🥈</span>')
            elif posicion == 3:
                return format_html('<span style="font-size: 24px;">🥉</span>')
            else:
                return format_html(
                    '<span style="background-color: #e5e7eb; padding: 5px 10px; '
                    'border-radius: 4px; font-weight: bold; font-size: 16px;">#{}</span>',
                    posicion
                )
        return '-'
    ranking_posicion.short_description = 'Pos.'
    
    def dorsal_badge(self, obj):
        return format_html(
            '<span style="background-color: #1f2937; color: white; padding: 6px 12px; '
            'border-radius: 4px; font-weight: bold; font-size: 18px;">{}</span>',
            obj.dorsal
        )
    dorsal_badge.short_description = 'Dorsal'
    dorsal_badge.admin_order_field = 'dorsal'
    
    def competencia_display(self, obj):
        return obj.juez_asignado.competencia.nombre
    competencia_display.short_description = 'Competencia'
    competencia_display.admin_order_field = 'juez_asignado__competencia'
    
    def total_registros(self, obj):
        count = obj.num_registros if hasattr(obj, 'num_registros') else obj.tiempos.count()
        if count > 0:
            return format_html('<strong style="color: #2563eb; font-size: 16px;">{}</strong>', count)
        return format_html('<span style="color: #9ca3af;">0</span>')
    total_registros.short_description = 'Registros'
    
    def mejor_tiempo_display(self, obj):
        if hasattr(obj, 'mejor_tiempo_ms') and obj.mejor_tiempo_ms:
            ms = obj.mejor_tiempo_ms
            milisegundos = ms % 1000
            total_seconds = ms // 1000
            segundos = total_seconds % 60
            total_minutes = total_seconds // 60
            minutos = total_minutes % 60
            horas = total_minutes // 60
            
            return format_html(
                '<strong style="color: #10b981; font-size: 16px;">{}h {}m {}s</strong>',
                horas, minutos, segundos
            )
        return '-'
    mejor_tiempo_display.short_description = '🏆 Mejor Tiempo'
    mejor_tiempo_display.admin_order_field = 'mejor_tiempo_ms'
    
    def tiempo_promedio_display(self, obj):
        if hasattr(obj, 'promedio_ms') and obj.promedio_ms:
            segundos = obj.promedio_ms / 1000
            segundos_formateado = '{:.2f}'.format(segundos)
            return format_html('<strong style="font-size: 15px;">{}s</strong>', segundos_formateado)
        return '-'
    tiempo_promedio_display.short_description = 'Promedio'
    tiempo_promedio_display.admin_order_field = 'promedio_ms'
    
    def tiempo_total_display(self, obj):
        if hasattr(obj, 'total_ms') and obj.total_ms:
            ms = obj.total_ms
            milisegundos = ms % 1000
            total_seconds = ms // 1000
            segundos = total_seconds % 60
            total_minutes = total_seconds // 60
            minutos = total_minutes % 60
            horas = total_minutes // 60
            
            return format_html(
                '<span style="font-size: 14px;">{}h {}m {}s</span>',
                horas, minutos, segundos
            )
        return '-'
    tiempo_total_display.short_description = 'Tiempo Total'
    tiempo_total_display.admin_order_field = 'total_ms'


# Personalización del título del admin
admin.site.site_header = "Administración de Competencias 5K"
admin.site.site_title = "Admin 5K"
admin.site.index_title = "Panel de Control"