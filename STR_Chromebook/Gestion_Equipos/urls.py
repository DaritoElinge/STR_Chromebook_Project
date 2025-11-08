from django.urls import path
from . import views

urlpatterns = [
    # Reservas (Docentes)
    path('reserva/nueva/', views.crear_reserva, name='crear_reserva'),
    
    # APIs (Dashboard Admin - Aprobar/Rechazar)
    path('reserva/<int:reserva_id>/aprobar/', views.aprobar_reserva, name='aprobar_reserva'),
    path('reserva/<int:reserva_id>/rechazar/', views.rechazar_reserva, name='rechazar_reserva'),
    path('reserva/<int:reserva_id>/detalle/', views.detalle_reserva, name='detalle_reserva'),
    
    # Equipos (CRUD Admin)
    path('equipos/', views.gestionar_equipos, name='gestionar_equipos'),
    path('equipo/crear/', views.crear_equipo, name='crear_equipo'),
    path('equipo/<int:equipo_id>/editar/', views.editar_equipo, name='editar_equipo'),
    path('equipo/<int:equipo_id>/eliminar/', views.eliminar_equipo, name='eliminar_equipo'),
    path('equipo/<int:equipo_id>/detalle/', views.detalle_equipo, name='detalle_equipo'),
    
    # APIs (Formulario Creación de Reserva)
    path('api/autocompletar-responsable/', views.autocompletar_responsable, name='autocompletar_responsable'),
    path('api/filtrar-aulas/', views.filtrar_aulas_por_bloque, name='filtrar_aulas'),
    path('api/filtrar-asignaturas/', views.filtrar_asignaturas_por_carrera, name='filtrar_asignaturas'),

    # Vistas de Reportes (Admin)
    path('reportes/', views.ver_reportes, name='ver_reportes'),
    path('reportes/descargar-excel/', views.descargar_reporte_excel, name='descargar_reporte_excel'),

    # Vistas de Gestión de Reservas (Admin)
    # Página de lista
    path('gestion/reservas/', views.gestionar_reservas_list, name='gestionar_reservas_list'),

    # Página de detalle para gestionar UNa reserva
    path('gestion/reservas/<int:reserva_id>/', views.gestionar_reserva_detalle, name='gestionar_reserva_detalle'),

    # --- APIs de Gestión de Reservas (Admin) ---
    path('api/gestion/reservas/<int:reserva_id>/asignar-equipo/', views.api_asignar_equipo, name='api_asignar_equipo'),
    path('api/gestion/reservas/desasignar-equipo/<int:asignacion_id>/', views.api_desasignar_equipo, name='api_desasignar_equipo'),
    path('api/gestion/reservas/<int:reserva_id>/asignar-supervisor/', views.api_asignar_supervisor, name='api_asignar_supervisor'),
    path('api/gestion/reservas/desasignar-supervisor/<int:supervisor_reserva_id>/', views.api_desasignar_supervisor, name='api_desasignar_supervisor'),
    path('api/gestion/reservas/eliminar-evidencia/<int:evidencia_id>/', views.api_eliminar_evidencia, name='api_eliminar_evidencia'),
    path('api/gestion/reservas/<int:reserva_id>/actualizar-gestion/', views.api_actualizar_gestion, name='api_actualizar_gestion'),

]