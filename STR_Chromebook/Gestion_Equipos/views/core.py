# ======================================================
# VISTAS PRINCIPALES Y CRUDs BÁSICOS
# (Lógica del dashboard, CRUD de Equipos, etc.)
# ======================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
import json

# Importar Modelos
from core.models import Usuario, Aula, Asignatura, Rack
from Gestion_Equipos.models import Reserva, Equipo, EstadoEquipo

# Importar Forms
from Gestion_Equipos.forms import ReservaForm


# ======================================================
# VISTAS DE RESERVA (DOCENTE)
# ======================================================

def crear_reserva(request):
    """Vista para crear una nueva reserva de Chromebooks"""
    
    # Verificar sesión
    if not request.session.get('usuario_id'):
        messages.error(request, 'Debe iniciar sesión.')
        return redirect('login')
    
    # Verificar que sea docente
    if request.session.get('usuario_tipo') != 'docente':
        messages.error(request, 'Solo los docentes pueden crear reservas.')
        return redirect('dashboard')
    
    usuario_id = request.session.get('usuario_id')
    usuario = Usuario.objects.get(id_usuario=usuario_id)
    
    if request.method == 'POST':
        form = ReservaForm(request.POST)
        
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.id_usuario = usuario
            reserva.estado_reserva = 'Pendiente'
            
            # Convertir responsable a mayúsculas
            reserva.responsable_entrega = reserva.responsable_entrega.upper()
            
            reserva.save()
            
            messages.success(
                request, 
                f'✅ Reserva #{reserva.id_reserva} creada exitosamente. '
                f'Estado: <strong>Pendiente de aprobación</strong>. '
                f'Recibirá notificación cuando sea procesada.'
            )
            return redirect('dashboard_docente')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = ReservaForm()
    
    context = {
        'usuario': usuario,
        'form': form
    }
    
    return render(request, 'docente/crear_reserva.html', context)


def mis_reservas(request):
    """Vista para ver todas las reservas del docente"""
    
    if not request.session.get('usuario_id'):
        messages.error(request, 'Debe iniciar sesión.')
        return redirect('login')
    
    if request.session.get('usuario_tipo') != 'docente':
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')
    
    usuario_id = request.session.get('usuario_id')
    usuario = Usuario.objects.get(id_usuario=usuario_id)
    
    # Obtener todas las reservas del docente ordenadas por fecha
    reservas = Reserva.objects.filter(
        id_usuario=usuario
    ).select_related(
        'id_carrera', 'id_asignatura', 'id_aula', 'id_aula__id_bloque'
    ).order_by('-fecha_uso', '-hora_inicio')
    
    # Calcular si cada reserva puede cancelarse (24 horas de antelación)
    ahora = timezone.now()
    for reserva in reservas:
        # Combinar fecha y hora de uso
        fecha_hora_uso = datetime.combine(reserva.fecha_uso, reserva.hora_inicio)
        # Convertir a timezone-aware
        if timezone.is_naive(fecha_hora_uso):
            fecha_hora_uso = timezone.make_aware(fecha_hora_uso)
        
        # Calcular diferencia en horas
        diferencia = (fecha_hora_uso - ahora).total_seconds() / 3600
        
        # Puede cancelar si:
        # 1. Estado es Pendiente, O
        # 2. Estado es Aprobada Y faltan más de 24 horas
        reserva.puede_cancelar = (
            reserva.estado_reserva == 'Pendiente' or 
            (reserva.estado_reserva == 'Aprobada' and diferencia > 24)
        )
    
    context = {
        'usuario': usuario,
        'reservas': reservas
    }
    
    return render(request, 'docente/mis_reservas.html', context)


def cancelar_reserva(request, reserva_id):
    """Vista para cancelar una reserva (AJAX)"""
    
    if not request.session.get('usuario_id'):
        return JsonResponse({'success': False, 'error': 'Debe iniciar sesión'})
    
    if request.session.get('usuario_tipo') != 'docente':
        return JsonResponse({'success': False, 'error': 'Acceso denegado'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            motivo = data.get('motivo', '').strip()
            
            if not motivo:
                return JsonResponse({'success': False, 'error': 'Debe proporcionar un motivo de cancelación'})
            
            usuario_id = request.session.get('usuario_id')
            reserva = get_object_or_404(Reserva, id_reserva=reserva_id, id_usuario_id=usuario_id)
            
            # Validar que pueda cancelarse
            ahora = timezone.now()
            fecha_hora_uso = datetime.combine(reserva.fecha_uso, reserva.hora_inicio)
            if timezone.is_naive(fecha_hora_uso):
                fecha_hora_uso = timezone.make_aware(fecha_hora_uso)
            
            diferencia_horas = (fecha_hora_uso - ahora).total_seconds() / 3600
            
            # Validar condiciones de cancelación
            if reserva.estado_reserva == 'Pendiente':
                # Puede cancelar en cualquier momento si está pendiente
                pass
            elif reserva.estado_reserva == 'Aprobada':
                # Solo puede cancelar si faltan más de 24 horas
                if diferencia_horas <= 24:
                    return JsonResponse({
                        'success': False, 
                        'error': 'No puede cancelar una reserva aprobada con menos de 24 horas de antelación'
                    })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': f'No puede cancelar una reserva en estado {reserva.estado_reserva}'
                })
            
            # Cancelar reserva
            reserva.estado_reserva = 'Rechazada'
            reserva.motivo_rechazo = f'[CANCELADA POR DOCENTE] {motivo}'
            reserva.save()
            
            messages.success(request, f'✅ Reserva #{reserva_id} cancelada exitosamente.')
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


# ======================================================
# APIs (AJAX) - CREACIÓN DE RESERVA (DOCENTE)
# ======================================================

def autocompletar_responsable(request):
    """API para autocompletar nombres de responsables"""
    
    if request.method == 'GET':
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return JsonResponse({'results': []})
        
        # Buscar usuarios que coincidan con el query
        usuarios = Usuario.objects.filter(
            nom_completo__icontains=query
        ).values_list('nom_completo', flat=True)[:10]
        
        # Convertir a mayúsculas
        results = [nombre.upper() for nombre in usuarios]
        
        return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})


def filtrar_aulas_por_bloque(request):
    """API para filtrar aulas según el bloque seleccionado"""
    
    if request.method == 'GET':
        bloque_id = request.GET.get('bloque_id')
        
        if not bloque_id:
            return JsonResponse({'aulas': []})
        
        aulas = Aula.objects.filter(id_bloque_id=bloque_id).values('id_aula', 'nom_aula')
        
        return JsonResponse({'aulas': list(aulas)})
    
    return JsonResponse({'aulas': []})


def filtrar_asignaturas_por_carrera(request):
    """API para filtrar asignaturas según la carrera seleccionada"""
    
    if request.method == 'GET':
        carrera_id = request.GET.get('carrera_id')
        
        if not carrera_id:
            return JsonResponse({'asignaturas': []})
        
        try:
            # Convertir a entero y validar
            carrera_id = int(carrera_id)
            
            # Filtrar asignaturas por carrera
            asignaturas = Asignatura.objects.filter(
                id_carrera_id=carrera_id
            ).values('id_asignatura', 'nom_asignatura').order_by('nom_asignatura')
            
            # Convertir a lista
            asignaturas_list = list(asignaturas)
            
            # Debug: imprimir en consola
            print(f"DEBUG - Carrera ID: {carrera_id}")
            print(f"DEBUG - Asignaturas encontradas: {len(asignaturas_list)}")
            print(f"DEBUG - Asignaturas: {asignaturas_list}")
            
            return JsonResponse({
                'asignaturas': asignaturas_list,
                'count': len(asignaturas_list)
            })
            
        except ValueError:
            return JsonResponse({'error': 'ID de carrera inválido', 'asignaturas': []})
        except Exception as e:
            print(f"ERROR en filtrar_asignaturas_por_carrera: {str(e)}")
            return JsonResponse({'error': str(e), 'asignaturas': []})
    
    return JsonResponse({'asignaturas': []})

# ======================================================
# APIs (AJAX) - DASHBOARD ADMIN (Aprobar/Rechazar)
# ======================================================

def aprobar_reserva(request, reserva_id):
    """Vista para aprobar una reserva"""
    
    # Verificar que sea administrador
    if request.session.get('usuario_tipo') != 'administrador':
        return JsonResponse({'success': False, 'error': 'Acceso denegado'})
    
    if request.method == 'POST':
        try:
            reserva = get_object_or_404(Reserva, id_reserva=reserva_id)
            
            reserva.estado_reserva = 'Aprobada'
            reserva.save()
            
            messages.success(request, f'✅ Reserva #{reserva_id} aprobada exitosamente.')
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def rechazar_reserva(request, reserva_id):
    """Vista para rechazar una reserva con motivo"""
    
    # Verificar que sea administrador
    if request.session.get('usuario_tipo') != 'administrador':
        return JsonResponse({'success': False, 'error': 'Acceso denegado'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            motivo = data.get('motivo', '').strip()
            
            if not motivo:
                return JsonResponse({'success': False, 'error': 'Debe proporcionar un motivo'})
            
            reserva = get_object_or_404(Reserva, id_reserva=reserva_id)
            
            reserva.estado_reserva = 'Rechazada'
            reserva.motivo_rechazo = motivo
            reserva.save()
            
            messages.warning(request, f'❌ Reserva #{reserva_id} rechazada.')
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def detalle_reserva(request, reserva_id):
    """Vista para obtener detalles completos de una reserva (JSON)"""
    
    # Verificar que sea administrador o docente
    if not request.session.get('usuario_id'):
        return JsonResponse({'success': False, 'error': 'No autenticado'})
    
    try:
        reserva = get_object_or_404(Reserva, id_reserva=reserva_id)
        
        # Construir respuesta JSON con todos los detalles
        data = {
            'success': True,
            'reserva': {
                'id': reserva.id_reserva,
                'fecha_uso': reserva.fecha_uso.strftime('%d/%m/%Y'),
                'hora_inicio': reserva.hora_inicio.strftime('%H:%M'),
                'hora_fin': reserva.hora_fin.strftime('%H:%M'),
                'estado': reserva.estado_reserva,
                'cant_solicitada': reserva.cant_solicitada,
                'responsable_entrega': reserva.responsable_entrega,
                'telefono_contacto': reserva.telefono_contacto,
                'motivo_rechazo': reserva.motivo_rechazo if reserva.motivo_rechazo else '',
                'docente': {
                    'nombre': reserva.id_usuario.nom_completo,
                    'cedula': reserva.id_usuario.cedula,
                    'email': reserva.id_usuario.email,
                    'telefono': reserva.id_usuario.telefono,
                },
                'asignatura': reserva.id_asignatura.nom_asignatura,
                'carrera': reserva.id_carrera.nom_carrera,
                'facultad': reserva.id_carrera.id_facultad.nom_facultad if reserva.id_carrera.id_facultad else 'N/A',
                'bloque': reserva.id_aula.id_bloque.nom_bloque,
                'aula': reserva.id_aula.nom_aula,
            }
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ======================================================
# VISTAS DE GESTIÓN DE EQUIPOS (ADMIN)
# ======================================================

def gestionar_equipos(request):
    """Vista para gestionar equipos (CRUD de Chromebooks)"""
    
    # Verificar que sea administrador
    if not request.session.get('usuario_id'):
        messages.error(request, 'Debe iniciar sesión.')
        return redirect('login')
    
    if request.session.get('usuario_tipo') != 'administrador':
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')
    
    usuario = Usuario.objects.get(id_usuario=request.session.get('usuario_id'))
    
    # Filtros
    estado_filtro = request.GET.get('estado', '')
    rack_filtro = request.GET.get('rack', '')
    busqueda = request.GET.get('q', '')
    
    equipos = Equipo.objects.select_related('id_estado_equipo', 'id_rack')
    
    # Aplicar filtros
    if estado_filtro:
        equipos = equipos.filter(id_estado_equipo__nom_estado=estado_filtro)
    
    if rack_filtro:
        equipos = equipos.filter(id_rack_id=rack_filtro)
    
    if busqueda:
        equipos = equipos.filter(
            models.Q(nom_equipo__icontains=busqueda) |
            models.Q(num_serie__icontains=busqueda) |
            models.Q(modelo__icontains=busqueda)
        )
    
    equipos = equipos.order_by('nom_equipo')
    
    # Obtener catálogos para filtros y formularios
    estados = EstadoEquipo.objects.all()
    racks = Rack.objects.all()
    
    # Estadísticas
    total_equipos = Equipo.objects.count()
    equipos_disponibles = Equipo.objects.filter(id_estado_equipo__nom_estado='Disponible').count()
    equipos_en_uso = Equipo.objects.filter(id_estado_equipo__nom_estado='En uso').count()
    equipos_mantenimiento = Equipo.objects.filter(id_estado_equipo__nom_estado__iexact='En Mantenimiento').count()
    
    context = {
        'usuario': usuario,
        'equipos': equipos,
        'estados': estados,
        'racks': racks,
        'estado_filtro': estado_filtro,
        'rack_filtro': rack_filtro,
        'busqueda': busqueda,
        'total_equipos': total_equipos,
        'equipos_disponibles': equipos_disponibles,
        'equipos_en_uso': equipos_en_uso,
        'equipos_mantenimiento': equipos_mantenimiento,
    }
    
    return render(request, 'administrador/gestionar_equipos.html', context)

# ======================================================
# APIs (AJAX) - CRUD DE EQUIPOS (ADMIN)
# ======================================================

def crear_equipo(request):
    """Vista para crear un nuevo equipo"""
    
    if request.session.get('usuario_tipo') != 'administrador':
        return JsonResponse({'success': False, 'error': 'Acceso denegado'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validar que no exista el número de serie
            if Equipo.objects.filter(num_serie=data['num_serie']).exists():
                return JsonResponse({'success': False, 'error': 'Ya existe un equipo con ese número de serie'})
            
            # Obtener instancias
            estado = EstadoEquipo.objects.get(id_estado_equipo=data['id_estado'])
            rack = Rack.objects.get(id_rack=data['id_rack']) if data.get('id_rack') else None
            
            # <<<=====================================================>>>
            # <<< VALIDACIÓN: Verificar capacidad del Rack            >>>
            # <<<=====================================================>>>
            if rack:
                conteo_actual = Equipo.objects.filter(id_rack=rack).count()
                if conteo_actual >= rack.capacidad_total:
                    return JsonResponse({
                        'success': False, 
                        'error': f'El Rack {rack.nom_rack} está lleno (Capacidad máxima: {rack.capacidad_total} equipos)'
                    })
            # <<<=====================================================>>>
            
            equipo = Equipo.objects.create(
                nom_equipo=data['nom_equipo'],
                num_serie=data['num_serie'],
                modelo=data['modelo'],
                id_estado_equipo=estado,
                id_rack=rack
            )
            
            messages.success(request, f'✅ Equipo {equipo.nom_equipo} creado exitosamente.')
            return JsonResponse({'success': True, 'equipo_id': equipo.id_equipo})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def editar_equipo(request, equipo_id):
    """Vista para editar un equipo"""
    
    if request.session.get('usuario_tipo') != 'administrador':
        return JsonResponse({'success': False, 'error': 'Acceso denegado'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            equipo = get_object_or_404(Equipo, id_equipo=equipo_id)
            
            # Validar número de serie único (excepto el actual)
            if Equipo.objects.filter(num_serie=data['num_serie']).exclude(id_equipo=equipo_id).exists():
                return JsonResponse({'success': False, 'error': 'Ya existe otro equipo con ese número de serie'})
            
            # <<<=====================================================>>>
            # <<< VALIDACIÓN: Verificar capacidad del Rack            >>>
            # <<<=====================================================>>>
            
            rack_nuevo_id = data.get('id_rack')
            rack_nuevo = Rack.objects.get(id_rack=rack_nuevo_id) if rack_nuevo_id else None
            rack_anterior = equipo.id_rack
            
            if rack_nuevo and rack_nuevo != rack_anterior:
                conteo_actual = Equipo.objects.filter(id_rack=rack_nuevo).count()
                if conteo_actual >= rack_nuevo.capacidad_total:
                    return JsonResponse({
                        'success': False, 
                        'error': f'No se puede mover al Rack {rack_nuevo.nom_rack} (Capacidad máxima: {rack_nuevo.capacidad_total} equipos)'
                    })
            # <<<=====================================================>>>

            # Actualizar datos
            equipo.nom_equipo = data['nom_equipo']
            equipo.num_serie = data['num_serie']
            equipo.modelo = data['modelo']
            equipo.id_estado_equipo = EstadoEquipo.objects.get(id_estado_equipo=data['id_estado'])
            equipo.id_rack = rack_nuevo
            equipo.save()
            
            messages.success(request, f'✅ Equipo {equipo.nom_equipo} actualizado exitosamente.')
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def eliminar_equipo(request, equipo_id):
    """Vista para eliminar (o dar de baja) un equipo"""
    
    if request.session.get('usuario_tipo') != 'administrador':
        return JsonResponse({'success': False, 'error': 'Acceso denegado'})
    
    if request.method == 'POST':
        try:
            equipo = get_object_or_404(Equipo, id_equipo=equipo_id)
            
            # En lugar de eliminar, cambiar a "Dado de baja"
            estado_baja, _ = EstadoEquipo.objects.get_or_create(nom_estado='Dado de baja')
            equipo.id_estado_equipo = estado_baja
            equipo.save()
            
            messages.warning(request, f'⚠️ Equipo {equipo.nom_equipo} dado de baja.')
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def detalle_equipo(request, equipo_id):
    """Vista para obtener detalles de un equipo (JSON)"""
    
    if not request.session.get('usuario_id'):
        return JsonResponse({'success': False, 'error': 'No autenticado'})
    
    try:
        equipo = get_object_or_404(Equipo, id_equipo=equipo_id)
        
        data = {
            'success': True,
            'equipo': {
                'id': equipo.id_equipo,
                'nom_equipo': equipo.nom_equipo,
                'num_serie': equipo.num_serie,
                'modelo': equipo.modelo,
                'id_estado': equipo.id_estado_equipo.id_estado_equipo,
                'estado': equipo.id_estado_equipo.nom_estado,
                'id_rack': equipo.id_rack.id_rack if equipo.id_rack else None,
                'rack': equipo.id_rack.nom_rack if equipo.id_rack else 'Sin asignar',
                'ubicacion': equipo.id_rack.ubicacion if equipo.id_rack else 'N/A',
            }
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})