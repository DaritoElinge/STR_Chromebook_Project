from django.contrib import admin
from .models import (
    TipoUsuario, TituloProfesional, Usuario,
    Carrera, Asignatura, DocenteCarrera,
    Bloque, Aula, Rack
)
from .forms import UsuarioAdminForm 


# ==================== USUARIOS ====================

@admin.register(TipoUsuario)
class TipoUsuarioAdmin(admin.ModelAdmin):
    list_display = ('id_tipo_usuario', 'nom_rol')
    search_fields = ('nom_rol',)


@admin.register(TituloProfesional)
class TituloProfesionalAdmin(admin.ModelAdmin):
    list_display = ('id_titulo', 'nom_titulo')
    search_fields = ('nom_titulo',)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    form = UsuarioAdminForm  
    list_display = ('id_usuario', 'username', 'nom_completo', 'cedula', 'email', 'id_tipo_usuario', 'telefono')
    list_filter = ('id_tipo_usuario',)
    search_fields = ('nom_completo', 'cedula', 'email', 'username')
    
    fieldsets = (
        ('Credenciales de Acceso', {
            'fields': ('username', 'password_input', 'password_confirm'),
            'description': 'Configure el nombre de usuario y contraseña para el acceso al sistema.'
        }),
        ('Información Personal', {
            'fields': ('nom_completo', 'cedula', 'telefono', 'email')
        }),
        ('Información Académica/Profesional', {
            'fields': ('id_tipo_usuario', 'id_titulo')
        }),
    )


# ==================== ACADÉMICO ====================

@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ('id_carrera', 'nom_carrera')
    search_fields = ('nom_carrera',)


@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ('id_asignatura', 'nom_asignatura')
    search_fields = ('nom_asignatura',)


@admin.register(DocenteCarrera)
class DocenteCarreraAdmin(admin.ModelAdmin):
    list_display = ('id_docente_carrera', 'get_docente', 'get_carrera')
    list_filter = ('id_carrera',)
    search_fields = ('id_usuario__nom_completo', 'id_carrera__nom_carrera')
    
    def get_docente(self, obj):
        return obj.id_usuario.nom_completo
    get_docente.short_description = 'Docente'
    
    def get_carrera(self, obj):
        return obj.id_carrera.nom_carrera
    get_carrera.short_description = 'Carrera'


# ==================== INFRAESTRUCTURA ====================

@admin.register(Bloque)
class BloqueAdmin(admin.ModelAdmin):
    list_display = ('id_bloque', 'nom_bloque')
    search_fields = ('nom_bloque',)


@admin.register(Aula)
class AulaAdmin(admin.ModelAdmin):
    list_display = ('id_aula', 'nom_aula', 'get_bloque')
    list_filter = ('id_bloque',)
    search_fields = ('nom_aula',)
    
    def get_bloque(self, obj):
        return obj.id_bloque.nom_bloque
    get_bloque.short_description = 'Bloque'


@admin.register(Rack)
class RackAdmin(admin.ModelAdmin):
    list_display = ('id_rack', 'nom_rack', 'ubicacion', 'capacidad_total', 'capacidad_func', 'estado_rack')
    list_filter = ('estado_rack',)
    search_fields = ('nom_rack', 'ubicacion')
    fieldsets = (
        ('Información Básica', {
            'fields': ('nom_rack', 'ubicacion')
        }),
        ('Capacidades', {
            'fields': ('capacidad_total', 'capacidad_func', 'estado_rack')
        }),
    )