from django.contrib import admin
from django.utils.html import format_html
from app.models import Competencia, Juez, Equipo, RegistroTiempo, ResultadoEquipo

# ======= FILTROS PERSONALIZADOS =======

class EstadoCompetenciaFilter(admin.SimpleListFilter):
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
            return queryset.filter(is_running=True)
        if self.value() == 'finalizada':
            return queryset.filter(is_running=False, finished_at__isnull=False)
        if self.value() == 'programada':
            return queryset.filter(is_running=False, finished_at__isnull=True)
        return queryset

# ======= INLINES =======

class EquipoInline(admin.TabularInline):
    model = Equipo
    extra = 0
    fields = ['number', 'name', 'judge', 'num_registros_display']
    readonly_fields = ['num_registros_display']

    def num_registros_display(self, obj):
        if obj.pk:
            count = obj.times.count()
            return format_html('<b>{}</b> registros', count)
        return '-'
    num_registros_display.short_description = 'Registros'

class RegistroTiempoInline(admin.TabularInline):
    model = RegistroTiempo
    extra = 0
    fields = ['tiempo_formateado_display', 'created_at']
    readonly_fields = ['tiempo_formateado_display', 'created_at']
    can_delete = True
    ordering = ['time']

    def tiempo_formateado_display(self, obj):
        if obj.pk:
            return format_html(
                '<b>{}h {}m {}s {}ms</b>',
                obj.hours, obj.minutes, obj.seconds, obj.milliseconds
            )
        return '-'
    tiempo_formateado_display.short_description = 'Tiempo'

# ======= ADMIN MODELS =======

@admin.register(Competencia)
class CompetenciaAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'datetime',
        'category',
        'get_status_display',
        'total_equipos',
        'total_registros',
        'is_active',
    ]
    list_filter = [EstadoCompetenciaFilter, 'category', 'is_active']
    search_fields = ['name']
    readonly_fields = ['started_at', 'finished_at']
    list_per_page = 25

    fieldsets = (
        ('Información General', {
            'fields': ('name', 'datetime', 'category', 'is_active')
        }),
        ('Estado de la Competencia', {
            'fields': ('is_running', 'started_at', 'finished_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [EquipoInline]

    def total_equipos(self, obj):
        return obj.teams.count()
    total_equipos.short_description = 'Equipos'

    def total_registros(self, obj):
        # Suma registros de todos los equipos en esta competencia
        return RegistroTiempo.objects.filter(team__competition=obj).count()
    total_registros.short_description = 'Registros de Tiempo'


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ['number', 'name', 'competition', 'judge', 'num_registros']
    list_filter = ['competition']
    search_fields = ['name']
    inlines = [RegistroTiempoInline]

    def num_registros(self, obj):
        return obj.times.count()
    num_registros.short_description = 'Registros'


@admin.register(Juez)
class JuezAdmin(admin.ModelAdmin):
    list_display = ['username', 'get_full_name', 'email', 'equipo_asignado', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']

    def equipo_asignado(self, obj):
        return getattr(obj, 'team', None) or '-'
    equipo_asignado.short_description = 'Equipo'


@admin.register(RegistroTiempo)
class RegistroTiempoAdmin(admin.ModelAdmin):
    list_display = [
        'id_registro_corto', 
        'equipo_con_dorsal', 
        'competencia_display',
        'tiempo_formateado_display', 
        'created_at'
    ]
    list_filter = ['team__competition']
    search_fields = ['team__name']
    ordering = ['time']
    readonly_fields = ['record_id', 'team', 'time', 'hours', 'minutes', 'seconds', 'milliseconds', 'created_at']

    def id_registro_corto(self, obj):
        return str(obj.record_id)[:8]
    id_registro_corto.short_description = 'ID'

    def equipo_con_dorsal(self, obj):
        return f"{obj.team.number} {obj.team.name}"
    equipo_con_dorsal.short_description = 'Equipo'
    equipo_con_dorsal.admin_order_field = 'team__number'

    def competencia_display(self, obj):
        return obj.team.competition
    competencia_display.short_description = 'Competencia'
    competencia_display.admin_order_field = 'team__competition'

    def tiempo_formateado_display(self, obj):
        return f"{obj.hours}h {obj.minutes}m {obj.seconds}s {obj.milliseconds}ms"
    tiempo_formateado_display.short_description = 'Tiempo'


@admin.register(ResultadoEquipo)
class ResultadoEquipoAdmin(admin.ModelAdmin):
    list_display = ['number', 'name', 'competition', 'tiempo_total_display']
    list_filter = ['competition']
    search_fields = ['name']
    
    def tiempo_total_display(self, obj):
        total = obj.total_time()
        if total:
            hours = total // 3600000
            minutes = (total % 3600000) // 60000
            seconds = (total % 60000) // 1000
            return f"{hours}h {minutes}m {seconds}s"
        return '-'
    tiempo_total_display.short_description = 'Tiempo Total'
