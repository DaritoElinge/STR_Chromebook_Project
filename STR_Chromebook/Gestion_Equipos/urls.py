from django.urls import path
from . import views

urlpatterns = [
    path('reserva/nueva/', views.crear_reserva, name='crear_reserva'),
    path('api/autocompletar-responsable/', views.autocompletar_responsable, name='autocompletar_responsable'),
    path('api/filtrar-aulas/', views.filtrar_aulas_por_bloque, name='filtrar_aulas'),
    path('api/filtrar-asignaturas/', views.filtrar_asignaturas_por_carrera, name='filtrar_asignaturas'),
]