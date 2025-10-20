from django.contrib import admin
from .models import EstadoEquipo, Equipo, Reserva, AsignacionEquipo

# ==================== EQUIPOS ====================

@admin.register(EstadoEquipo)
class EstadoEquipoAdmin(admin.ModelAdmin):
    list_display = ('id_estado_equipo', 'nom_estado')
    search_fields = ('nom_estado',)


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('id_equipo', 'nom_equipo', 'num_serie', 'modelo', 'get_estado', 'get_rack')
    list_filter = ('id_estado_equipo', 'id_rack')
    search_fields = ('nom_equipo', 'num_serie', 'modelo')
    fieldsets = (
        ('Información del Equipo', {
            'fields': ('nom_equipo', 'num_serie', 'modelo')
        }),
        ('Ubicación y Estado', {
            'fields': ('id_rack', 'id_estado_equipo')
        }),
    )
    
    def get_estado(self, obj):
        return obj.id_estado_equipo.nom_estado
    get_estado.short_description = 'Estado'
    
    def get_rack(self, obj):
        return obj.id_rack.nom_rack if obj.id_rack else 'Sin asignar'
    get_rack.short_description = 'Rack'


# ==================== RESERVAS ====================

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id_reserva', 'get_usuario', 'fecha_uso', 'hora_inicio', 'hora_fin', 
                    'cant_solicitada', 'estado_reserva', 'get_carrera')
    list_filter = ('estado_reserva', 'fecha_uso', 'id_carrera')
    search_fields = ('id_usuario__nom_completo', 'id_asignatura__nom_asignatura')
    date_hierarchy = 'fecha_uso'
    fieldsets = (
        ('Información de la Reserva', {
            'fields': ('id_usuario', 'fecha_uso', 'hora_inicio', 'hora_fin', 'cant_solicitada')
        }),
        ('Detalles Académicos', {
            'fields': ('id_asignatura', 'id_carrera', 'id_aula')
        }),
        ('Estado', {
            'fields': ('estado_reserva',)
        }),
    )
    
    def get_usuario(self, obj):
        return obj.id_usuario.nom_completo
    get_usuario.short_description = 'Usuario'
    
    def get_carrera(self, obj):
        return obj.id_carrera.nom_carrera
    get_carrera.short_description = 'Carrera'


@admin.register(AsignacionEquipo)
class AsignacionEquipoAdmin(admin.ModelAdmin):
    list_display = ('id_asig_equipo', 'get_reserva', 'get_equipo', 'fecha_registro')
    list_filter = ('fecha_registro',)
    search_fields = ('id_reserva__id_usuario__nom_completo', 'id_equipo__num_serie')
    date_hierarchy = 'fecha_registro'
    
    def get_reserva(self, obj):
        return f"Reserva #{obj.id_reserva.id_reserva} - {obj.id_reserva.id_usuario.nom_completo}"
    get_reserva.short_description = 'Reserva'
    
    def get_equipo(self, obj):
        return f"{obj.id_equipo.nom_equipo} - {obj.id_equipo.num_serie}"
    get_equipo.short_description = 'Equipo'