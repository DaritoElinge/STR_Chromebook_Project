from django.urls import path
from . import views 

urlpatterns = [
    # --- Vistas de Reserva (Docente) ---
    path('reserva/nueva/', views.crear_reserva, name='crear_reserva'),
    path('mis-reservas/', views.mis_reservas, name='mis_reservas'),  
    path('reserva/<int:reserva_id>/cancelar/', views.cancelar_reserva, name='cancelar_reserva'),  
    
    # --- Vistas de Gestión de Equipos (Admin) ---
    path('equipos/', views.gestionar_equipos, name='gestionar_equipos'),
    
    # --- Vistas de Reportes (Admin) ---
    path('reportes/', views.ver_reportes, name='ver_reportes'),
    path('reportes/descargar-excel/', views.descargar_reporte_excel, name='descargar_reporte_excel'),
    
    # --- Vistas de Gestión de Reservas (Admin) ---
    path('reservas/', views.gestionar_reservas_list, name='gestionar_reservas_list'),
    path('reservas/<int:reserva_id>/gestionar/', views.gestionar_reserva_detalle, name='gestionar_reserva_detalle'),
    
    # --- APIs para Dashboard (Aprobar/Rechazar) ---
    path('reserva/<int:reserva_id>/aprobar/', views.aprobar_reserva, name='aprobar_reserva'),
    path('reserva/<int:reserva_id>/rechazar/', views.rechazar_reserva, name='rechazar_reserva'),
    path('reserva/<int:reserva_id>/detalle/', views.detalle_reserva, name='detalle_reserva'),
    
    # --- APIs para CRUD de Equipos ---
    path('equipo/crear/', views.crear_equipo, name='crear_equipo'),
    path('equipo/<int:equipo_id>/editar/', views.editar_equipo, name='editar_equipo'),
    path('equipo/<int:equipo_id>/eliminar/', views.eliminar_equipo, name='eliminar_equipo'),
    path('equipo/<int:equipo_id>/detalle/', views.detalle_equipo, name='detalle_equipo'),
    
    # --- APIs para Creación de Reservas (Docente) ---
    path('api/autocompletar-responsable/', views.autocompletar_responsable, name='autocompletar_responsable'),
    path('api/filtrar-aulas/', views.filtrar_aulas_por_bloque, name='filtrar_aulas'),
    path('api/filtrar-asignaturas/', views.filtrar_asignaturas_por_carrera, name='filtrar_asignaturas'),
    
    # --- APIs de Gestión de Reservas (Admin) ---
    path('api/reservas/<int:reserva_id>/asignar-rack/', views.api_asignar_rack, name='api_asignar_rack'),
    path('api/reservas/<int:reserva_id>/desasignar-todos/', views.api_desasignar_todos_equipos, name='api_desasignar_todos_equipos'),
    path('api/reservas/desasignar-equipo/<int:asignacion_id>/', views.api_desasignar_equipo, name='api_desasignar_equipo'),
    path('api/reservas/<int:reserva_id>/asignar-supervisor/', views.api_asignar_supervisor, name='api_asignar_supervisor'),
    path('api/reservas/desasignar-supervisor/<int:supervisor_reserva_id>/', views.api_desasignar_supervisor, name='api_desasignar_supervisor'),
    path('api/reservas/eliminar-evidencia/<int:evidencia_id>/', views.api_eliminar_evidencia, name='api_eliminar_evidencia'),
    path('api/reservas/<int:reserva_id>/actualizar-gestion/', views.api_actualizar_gestion, name='api_actualizar_gestion'),
    path('api/reservas/<int:reserva_id>/finalizar/', views.api_finalizar_reserva, name='api_finalizar_reserva'),
]