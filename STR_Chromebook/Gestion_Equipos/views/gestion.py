# ======================================================
# VISTAS DEL MÓDULO "GESTIONAR RESERVAS" (ADMIN)
# ======================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime
import json

# Importar Modelos
from core.models import Usuario
from Gestion_Equipos.models import (
    Reserva, Equipo, EstadoEquipo, AsignacionEquipo, 
    SupervisorReserva, EvidenciaReserva
)

# Importar Forms
from Gestion_Equipos.forms import EvidenciaReservaForm


# ======================================================
# VISTAS PRINCIPALES (HTML)
# ======================================================

def gestionar_reservas_list(request):
    """
    Vista principal para que el admin vea TODAS las reservas (Pendientes,
    Aprobadas, etc.) y pueda gestionarlas.
    """
    if not request.session.get('usuario_id'):
        messages.error(request, 'Debe iniciar sesión.')
        return redirect('login')
    if request.session.get('usuario_tipo') != 'administrador':
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')

    usuario = Usuario.objects.get(id_usuario=request.session.get('usuario_id'))

    estado_filtro = request.GET.get('estado', '')
    
    reservas_list = Reserva.objects.select_related(
        'id_usuario', 'id_carrera', 'id_aula', 'id_aula__id_bloque'
    ).prefetch_related(
        'supervisores', # related_name de SupervisorReserva
        'asignacionequipo_set' # related_name por defecto
    ).order_by('-fecha_uso', '-hora_inicio')

    if estado_filtro:
        reservas_list = reservas_list.filter(estado_reserva=estado_filtro)

    # Contar equipos asignados para cada reserva
    for reserva in reservas_list:
        reserva.equipos_asignados_count = reserva.asignacionequipo_set.count()

    context = {
        'usuario': usuario,
        'reservas': reservas_list,
        'estado_filtro': estado_filtro,
    }
    
    # Plantilla: templates/administrador/gestionar_reservas_list.html
    return render(request, 'administrador/gestionar_reservas_list.html', context)


def gestionar_reserva_detalle(request, reserva_id):
    """
    Vista detallada para GESTIONAR una reserva específica.
    Aquí es donde asignas equipos, supervisores y subes evidencia.
    """
    if not request.session.get('usuario_id'):
        messages.error(request, 'Debe iniciar sesión.')
        return redirect('login')
    if request.session.get('usuario_tipo') != 'administrador':
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')

    usuario = Usuario.objects.get(id_usuario=request.session.get('usuario_id'))
    reserva = get_object_or_404(Reserva.objects.select_related(
        'id_usuario', 'id_carrera', 'id_aula__id_bloque'
    ), id_reserva=reserva_id)

    # --- Manejo de SUBIDA DE EVIDENCIA (FOTO) ---
    if request.method == 'POST':
        # El formulario EvidenciaReservaForm se encarga de esto
        form_evidencia = EvidenciaReservaForm(request.POST, request.FILES)
        if form_evidencia.is_valid():
            evidencia = form_evidencia.save(commit=False)
            evidencia.id_reserva = reserva
            evidencia.save()
            messages.success(request, '✅ Evidencia subida correctamente.')
            # Redirigir para limpiar el POST y evitar reenvíos
            return redirect('gestionar_reserva_detalle', reserva_id=reserva_id)
        else:
            messages.error(request, 'Error al subir la evidencia. Revise el formulario.')
    else:
        # Crear un formulario vacío para el template (para peticiones GET)
        form_evidencia = EvidenciaReservaForm()

    # --- DATOS PARA EL CONTEXTO DE LA VISTA (GET) ---

    # 1. Equipos ya asignados a ESTA reserva
    equipos_asignados = AsignacionEquipo.objects.filter(
        id_reserva=reserva
    ).select_related('id_equipo', 'id_equipo__id_rack')

    # 2. Equipos "Disponibles" para ser asignados
    equipos_disponibles = Equipo.objects.filter(
        id_estado_equipo__nom_estado='Disponible'
    ).select_related('id_rack').order_by('id_rack', 'nom_equipo')

    # 3. Supervisores ya asignados (usando tu modelo SupervisorReserva)
    supervisores_asignados = SupervisorReserva.objects.filter(
        id_reserva=reserva
    ).select_related('id_supervisor')

    # 4. Supervisores "Disponibles" (Usuarios con el rol)
    supervisores_asignados_ids = [s.id_supervisor_id for s in supervisores_asignados]
    supervisores_disponibles = Usuario.objects.filter(
        id_tipo_usuario__nom_rol='Supervisor'
    ).exclude(
        id_usuario__in=supervisores_asignados_ids
    ).order_by('nom_completo')
    
    # 5. Evidencia ya subida para esta reserva
    evidencias = EvidenciaReserva.objects.filter(
        id_reserva=reserva
    ).order_by('-fecha_subida')

    context = {
        'usuario': usuario,
        'reserva': reserva,
        'equipos_asignados': equipos_asignados,
        'equipos_disponibles': equipos_disponibles,
        'supervisores_asignados': supervisores_asignados,
        'supervisores_disponibles': supervisores_disponibles,
        'evidencias': evidencias,
        'form_evidencia': form_evidencia, # El formulario para subir fotos
    }
    
    # Plantilla: templates/administrador/gestionar_reserva_detalle.html
    return render(request, 'administrador/gestionar_reserva_detalle.html', context)


# ======================================================
# --- APIs (AJAX) - GESTIÓN DE RESERVAS (ADMIN) ---
# ======================================================

def api_asignar_equipo(request, reserva_id):
    """
    API para asignar un equipo 'Disponible' a una reserva.
    Cambia el estado del equipo a 'En uso'.
    """
    if request.session.get('usuario_tipo') != 'administrador':
        return JsonResponse({'success': False, 'error': 'Acceso denegado'})
    
    if request.method == 'POST':
        try:
            reserva = get_object_or_404(Reserva, id_reserva=reserva_id)
            data = json.loads(request.body)
            equipo_id = data.get('equipo_id')
            equipo = get_object_or_404(Equipo, id_equipo=equipo_id)

            # Validar que el equipo esté realmente disponible
            if equipo.id_estado_equipo.nom_estado != 'Disponible':
                return JsonResponse({'success': False, 'error': 'El equipo no está disponible'})

            # Validar que no se pasen de la cantidad solicitada
            conteo_actual = AsignacionEquipo.objects.filter(id_reserva=reserva).count()
            if conteo_actual >= reserva.cant_solicitada:
                return JsonResponse({'success': False, 'error': f'Ya se asignó la cantidad máxima solicitada ({reserva.cant_solicitada})'})

            # Crear la asignación
            asignacion, created = AsignacionEquipo.objects.get_or_create(
                id_reserva=reserva,
                id_equipo=equipo
            )
            
            if not created:
                return JsonResponse({'success': False, 'error': 'Este equipo ya estaba asignado'})

            # Cambiar estado del equipo
            estado_en_uso = EstadoEquipo.objects.get(nom_estado='En uso')
            equipo.id_estado_equipo = estado_en_uso
            equipo.save()
            
            # Devolver datos para la UI
            data = {
                'success': True,
                'asignacion': {
                    'id': asignacion.id_asig_equipo,
                    'equipo_nombre': equipo.nom_equipo,
                    'equipo_serie': equipo.num_serie,
                    'rack': equipo.id_rack.nom_rack if equipo.id_rack else 'N/A'
                }
            }
            return JsonResponse(data)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def api_desasignar_equipo(request, asignacion_id):
    """
    API para quitar un equipo de una reserva y devolverlo a 'Disponible'.
    """
    if request.session.get('usuario_tipo') != 'administrador':
        return JsonResponse({'success': False, 'error': 'Acceso denegado'})

    if request.method == 'POST':
        try:
            # Buscar la asignación específica
            asignacion = get_object_or_404(AsignacionEquipo, id_asig_equipo=asignacion_id)
            equipo = asignacion.id_equipo
            
            # Devolver el equipo a 'Disponible'
            estado_disponible = EstadoEquipo.objects.get(nom_estado='Disponible')
            equipo.id_estado_equipo = estado_disponible
            equipo.save()
            
            # Eliminar la asignación
            asignacion.delete()
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def api_asignar_supervisor(request, reserva_id):
    """
    API para asignar un supervisor a una reserva (usando tu modelo SupervisorReserva).
    """
    if request.session.get('usuario_tipo') != 'administrador':
        return JsonResponse({'success': False, 'error': 'Acceso denegado'})

    if request.method == 'POST':
        try:
            reserva = get_object_or_404(Reserva, id_reserva=reserva_id)
            data = json.loads(request.body)
            supervisor_id = data.get('supervisor_id')
            supervisor = get_object_or_404(Usuario, id_usuario=supervisor_id)

            # Validar que el usuario tenga el rol 'Supervisor'
            if supervisor.id_tipo_usuario.nom_rol != 'Supervisor':
                 return JsonResponse({'success': False, 'error': 'Este usuario no es Supervisor'})

            # Crear la asignación
            asignacion, created = SupervisorReserva.objects.get_or_create(
                id_reserva=reserva,
                id_supervisor=supervisor
            )

            if not created:
                return JsonResponse({'success': False, 'error': 'Supervisor ya asignado'})

            # Devolver datos para la UI
            data = {
                'success': True,
                'asignacion': {
                    'id': asignacion.id_supervisor_reserva,
                    'nombre': supervisor.nom_completo,
                    'email': supervisor.email
                }
            }
            return JsonResponse(data)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def api_desasignar_supervisor(request, supervisor_reserva_id):
    """
    API para quitar un supervisor de una reserva.
    """
    if request.session.get('usuario_tipo') != 'administrador':
        return JsonResponse({'success': False, 'error': 'Acceso denegado'})

    if request.method == 'POST':
        try:
            # Buscar la asignación específica por su ID único
            asignacion = get_object_or_404(SupervisorReserva, id_supervisor_reserva=supervisor_reserva_id)
            asignacion.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def api_eliminar_evidencia(request, evidencia_id):
    """
    API para eliminar una foto de evidencia.
    """
    if request.session.get('usuario_tipo') != 'administrador':
        return JsonResponse({'success': False, 'error': 'Acceso denegado'})

    if request.method == 'POST':
        try:
            evidencia = get_object_or_404(EvidenciaReserva, id_evidencia=evidencia_id)
            
            # Borrar el archivo de media/evidencias/
            if evidencia.foto:
                evidencia.foto.delete(save=False) # No guardar el modelo aún
            
            # Borrar el registro de la BD
            evidencia.delete()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def api_actualizar_gestion(request, reserva_id):
    """
    API para guardar observaciones y timestamps (fecha_entrega, fecha_devolucion).
    """
    if request.session.get('usuario_tipo') != 'administrador':
        return JsonResponse({'success': False, 'error': 'Acceso denegado'})

    if request.method == 'POST':
        try:
            reserva = get_object_or_404(Reserva, id_reserva=reserva_id)
            data = json.loads(request.body)
            
            # Actualizar campos del modelo Reserva
            reserva.observaciones = data.get('observaciones', reserva.observaciones)
            
            # Convertir string de datetime-local a objeto datetime
            fecha_entrega_str = data.get('fecha_entrega')
            fecha_devolucion_str = data.get('fecha_devolucion')
            
            if fecha_entrega_str:
                reserva.fecha_entrega = datetime.fromisoformat(fecha_entrega_str)
            else:
                reserva.fecha_entrega = None
                
            if fecha_devolucion_str:
                reserva.fecha_devolucion = datetime.fromisoformat(fecha_devolucion_str)
            else:
                reserva.fecha_devolucion = None
            
            reserva.save()
            
            messages.success(request, 'Gestión de reserva actualizada.')
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error procesando datos: {str(e)}'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})