# ======================================================
# VISTAS DE GESTIÓN DE RESERVAS (ADMIN)
# (Asignar equipos, supervisores, subir evidencia)
# ======================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q, F
from django.db import transaction # ¡Importante para las nuevas APIs!
from datetime import datetime
import json

# Importar Modelos
from core.models import Usuario, Rack
from Gestion_Equipos.models import (
    Reserva, Equipo, EstadoEquipo, AsignacionEquipo, 
    SupervisorReserva, EvidenciaReserva
)

# Importar Forms
from Gestion_Equipos.forms import EvidenciaReservaForm


# ======================================================
# VISTAS HTML (PÁGINAS)
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
        'supervisores', 
        'asignacionequipo_set' # Usamos el related_name por defecto
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
    
    return render(request, 'administrador/gestionar_reservas_list.html', context)


def gestionar_reserva_detalle(request, reserva_id):
    """
    Vista detallada para GESTIONAR una reserva específica.
    Aquí es donde asignas Racks, supervisores y subes evidencia.
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
    if request.method == 'POST' and 'submit_evidencia' in request.POST:
        form_evidencia = EvidenciaReservaForm(request.POST, request.FILES)
        if form_evidencia.is_valid():
            evidencia = form_evidencia.save(commit=False)
            evidencia.id_reserva = reserva
            evidencia.save()
            messages.success(request, '✅ Evidencia subida correctamente.')
            return redirect('gestionar_reserva_detalle', reserva_id=reserva_id)
        else:
            messages.error(request, 'Error al subir la evidencia. Revise el formulario.')
    else:
        form_evidencia = EvidenciaReservaForm()

    # --- DATOS PARA EL CONTEXTO DE LA VISTA (GET) ---

    equipos_asignados = AsignacionEquipo.objects.filter(
        id_reserva=reserva
    ).select_related('id_equipo', 'id_equipo__id_rack')
    
    equipos_asignados_count = equipos_asignados.count()
    equipos_necesarios = reserva.cant_solicitada - equipos_asignados_count

    # 2. Racks "Disponibles" para ser asignados
    racks_disponibles = Rack.objects.annotate(
        # 1. Contar equipos cuyo estado es 'Disponible' (ignorando mayúsculas)
        equipos_disponibles_en_rack=Count('equipo', filter=Q(
            equipo__id_estado_equipo__nom_estado__iexact='Disponible' 
        ))
    ).filter(
        # 2. Asegurarse de que la cantidad sea suficiente
        equipos_disponibles_en_rack__gte=equipos_necesarios,
        
        # 3. Asegurarse de que el Rack esté 'Disponible' (ignorando mayúsculas)
        estado_rack__iexact='Disponible' 
        
    ).order_by('nom_rack')


    # 3. Supervisores ya asignados
    supervisores_asignados = SupervisorReserva.objects.filter(
        id_reserva=reserva
    ).select_related('id_supervisor')

    # 4. Supervisores "Disponibles"
    supervisores_asignados_ids = [s.id_supervisor_id for s in supervisores_asignados]
    supervisores_disponibles = Usuario.objects.filter(
        id_tipo_usuario__nom_rol='Supervisor'
    ).exclude(
        id_usuario__in=supervisores_asignados_ids
    ).order_by('nom_completo')
    
    # 5. Evidencia ya subida
    evidencias = EvidenciaReserva.objects.filter(
        id_reserva=reserva
    ).order_by('-fecha_subida')

    context = {
        'usuario': usuario,
        'reserva': reserva,
        'equipos_asignados': equipos_asignados,
        'equipos_asignados_count': equipos_asignados_count,
        'equipos_necesarios': equipos_necesarios,
        'racks_disponibles': racks_disponibles, 
        'supervisores_asignados': supervisores_asignados,
        'supervisores_disponibles': supervisores_disponibles,
        'evidencias': evidencias,
        'form_evidencia': form_evidencia,
    }
    
    return render(request, 'administrador/gestionar_reserva_detalle.html', context)


# ======================================================
# --- APIs (AJAX) - GESTIÓN DE RESERVAS (ADMIN) ---
# ======================================================

def api_asignar_rack(request, reserva_id):
    """
    API para asignar automáticament 'equipos_necesarios' desde un Rack.
    """
    if request.session.get('usuario_tipo') != 'administrador':
        return JsonResponse({'success': False, 'error': 'Acceso denegado'})
    
    if request.method == 'POST':
        try:
            reserva = get_object_or_404(Reserva, id_reserva=reserva_id)
            data = json.loads(request.body)
            rack_id = data.get('rack_id')
            
            if not rack_id:
                return JsonResponse({'success': False, 'error': 'Debe seleccionar un rack'})

            rack = get_object_or_404(Rack, id_rack=rack_id)

            equipos_asignados_count = AsignacionEquipo.objects.filter(id_reserva=reserva).count()
            equipos_necesarios = reserva.cant_solicitada - equipos_asignados_count

            if equipos_necesarios <= 0:
                return JsonResponse({'success': False, 'error': 'Ya se asignó la cantidad total de equipos solicitados.'})

            # Buscar equipos 'Disponibles' (ignorando mayúsculas)
            equipos_para_asignar = Equipo.objects.filter(
                id_rack=rack,
                id_estado_equipo__nom_estado__iexact='Disponible' 
            )[:equipos_necesarios]

            if len(equipos_para_asignar) < equipos_necesarios:
                return JsonResponse({'success': False, 'error': f'El Rack {rack.nom_rack} solo tiene {len(equipos_para_asignar)} equipos disponibles. Se necesitan {equipos_necesarios}.'})

            # Asignar los equipos y cambiar su estado
            estado_en_uso, _ = EstadoEquipo.objects.get_or_create(nom_estado='En uso')
            
            nuevas_asignaciones = []
            for equipo in equipos_para_asignar:
                asignacion = AsignacionEquipo(
                    id_reserva=reserva,
                    id_equipo=equipo
                )
                nuevas_asignaciones.append(asignacion)
                equipo.id_estado_equipo = estado_en_uso
            
            AsignacionEquipo.objects.bulk_create(nuevas_asignaciones)
            Equipo.objects.bulk_update(equipos_para_asignar, ['id_estado_equipo'])

            messages.success(request, f'✅ {len(nuevas_asignaciones)} equipos asignados exitosamente desde {rack.nom_rack}.')
            return JsonResponse({'success': True, 'asignados': len(nuevas_asignaciones)})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@transaction.atomic # Asegura que toda la operación falle o tenga éxito
def api_desasignar_todos_equipos(request, reserva_id):
    """
    API para quitar TODOS los equipos de una reserva y devolverlos a 'Disponible'.
    """
    if request.session.get('usuario_tipo') != 'administrador':
        return JsonResponse({'success': False, 'error': 'Acceso denegado'})

    if request.method == 'POST':
        try:
            reserva = get_object_or_404(Reserva, id_reserva=reserva_id)
            asignaciones = AsignacionEquipo.objects.filter(id_reserva=reserva)
            
            if not asignaciones.exists():
                return JsonResponse({'success': False, 'error': 'No hay equipos asignados para quitar.'})

            estado_disponible, _ = EstadoEquipo.objects.get_or_create(nom_estado='Disponible')
            
            # Obtener todos los IDs de equipos antes de borrar las asignaciones
            equipo_ids = list(asignaciones.values_list('id_equipo_id', flat=True))
            
            # Borrar todas las asignaciones de esta reserva
            asignaciones.delete()
            
            # Actualizar todos los equipos correspondientes a 'Disponible'
            Equipo.objects.filter(id_equipo__in=equipo_ids).update(id_estado_equipo=estado_disponible)
            
            messages.info(request, f'♻️ Se quitaron {len(equipo_ids)} equipos de la reserva.')
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def api_desasignar_equipo(request, asignacion_id):
    """
    API para quitar UN equipo de una reserva y devolverlo a 'Disponible'.
    """
    if request.session.get('usuario_tipo') != 'administrador':
        return JsonResponse({'success': False, 'error': 'Acceso denegado'})

    if request.method == 'POST':
        try:
            asignacion = get_object_or_404(AsignacionEquipo, id_asig_equipo=asignacion_id)
            equipo = asignacion.id_equipo
            
            estado_disponible, _ = EstadoEquipo.objects.get_or_create(nom_estado='Disponible')
            equipo.id_estado_equipo = estado_disponible
            equipo.save()
            
            asignacion.delete()
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def api_asignar_supervisor(request, reserva_id):
    """
    API para asignar un supervisor a una reserva (usando tu modelo).
    """
    if request.session.get('usuario_tipo') != 'administrador':
        return JsonResponse({'success': False, 'error': 'Acceso denegado'})

    if request.method == 'POST':
        try:
            reserva = get_object_or_404(Reserva, id_reserva=reserva_id)
            data = json.loads(request.body)
            supervisor_id = data.get('supervisor_id')
            supervisor = get_object_or_404(Usuario, id_usuario=supervisor_id)

            if supervisor.id_tipo_usuario.nom_rol != 'Supervisor':
                 return JsonResponse({'success': False, 'error': 'Este usuario no es Supervisor'})

            asignacion, created = SupervisorReserva.objects.get_or_create(
                id_reserva=reserva,
                id_supervisor=supervisor
            )

            if not created:
                return JsonResponse({'success': False, 'error': 'Supervisor ya asignado'})

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
            
            if evidencia.foto:
                evidencia.foto.delete(save=False)
            
            evidencia.delete()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def api_actualizar_gestion(request, reserva_id):
    """
    API para guardar observaciones y timestamps de la reserva.
    """
    if request.session.get('usuario_tipo') != 'administrador':
        return JsonResponse({'success': False, 'error': 'Acceso denegado'})

    if request.method == 'POST':
        try:
            reserva = get_object_or_404(Reserva, id_reserva=reserva_id)
            data = json.loads(request.body)
            
            reserva.observaciones = data.get('observaciones', reserva.observaciones)
            
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


# --- ¡NUEVA API PARA FINALIZAR! ---
@transaction.atomic
def api_finalizar_reserva(request, reserva_id):
    """
    API para marcar una reserva como 'Finalizada' y devolver todos
    los equipos asignados a 'Disponible'.
    """
    if request.session.get('usuario_tipo') != 'administrador':
        return JsonResponse({'success': False, 'error': 'Acceso denegado'})

    if request.method == 'POST':
        try:
            reserva = get_object_or_404(Reserva, id_reserva=reserva_id)
            
            # 1. Verificar que la reserva esté 'Aprobada'
            if reserva.estado_reserva != 'Aprobada':
                return JsonResponse({'success': False, 'error': f'Solo se pueden finalizar reservas "Aprobadas". Esta reserva está "{reserva.estado_reserva}".'})

            # 2. Encontrar todas las asignaciones y equipos
            asignaciones = AsignacionEquipo.objects.filter(id_reserva=reserva)
            equipo_ids = list(asignaciones.values_list('id_equipo_id', flat=True))
            
            # 3. Poner todos los equipos como 'Disponible'
            estado_disponible, _ = EstadoEquipo.objects.get_or_create(nom_estado='Disponible')
            Equipo.objects.filter(id_equipo__in=equipo_ids).update(id_estado_equipo=estado_disponible)
            
            # 4. (Opcional) Borrar las asignaciones, ya que la reserva terminó
            # asignaciones.delete() 
            # -> O puedes dejarlas para el historial. Decidimos dejarlas.

            # 5. Marcar la reserva como 'Finalizada'
            reserva.estado_reserva = 'Finalizada'
            
            # (Opcional) Sellar la fecha de devolución si está vacía
            if not reserva.fecha_devolucion:
                reserva.fecha_devolucion = datetime.now()

            reserva.save()
            
            messages.success(request, f'✅ Reserva #{reserva.id_reserva} marcada como "Finalizada".')
            return JsonResponse({'success': True, 'redirect_url': request.build_absolute_uri(redirect('gestionar_reservas_list').url)})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})