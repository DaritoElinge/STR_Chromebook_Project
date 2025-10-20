from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/docente/', views.dashboard_docente, name='dashboard_docente'),
    path('dashboard/administrador/', views.dashboard_administrador, name='dashboard_administrador'),
]