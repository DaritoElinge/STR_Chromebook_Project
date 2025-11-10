from django.shortcuts import render, redirect
from django.contrib import messages
from core.models import Usuario

def login_view(request):
    """Vista de login para docentes y administradores"""
    
    # Si ya está autenticado, redirigir al dashboard
    if request.session.get('usuario_id'):
        return redirect('dashboard')
    
    # Limpiar mensajes antiguos al cargar el login
    from django.contrib.messages import get_messages
    storage = get_messages(request)
    list(storage)  # Consumir y limpiar mensajes
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        perfil = request.POST.get('perfil')  # 'docente' o 'admin'
        
        try:
            # Buscar usuario por username
            usuario = Usuario.objects.get(username=username)
            
            # Verificar el tipo de usuario según el perfil seleccionado
            tipo_usuario = usuario.id_tipo_usuario.nom_rol.lower()
            
            # Mapear 'admin' del frontend a 'administrador' del backend
            perfil_esperado = 'administrador' if perfil == 'admin' else 'docente'
            
            # Validar que el perfil seleccionado coincida con el tipo de usuario
            if tipo_usuario != perfil_esperado:
                messages.error(request, f'El usuario no tiene el rol de {perfil_esperado}.')
                return render(request, 'auth/login.html')
            
            # Verificar contraseña encriptada
            if usuario.check_password(password):
                # Guardar datos en sesión
                request.session['usuario_id'] = usuario.id_usuario
                request.session['usuario_nombre'] = usuario.nom_completo
                request.session['usuario_tipo'] = tipo_usuario
                request.session['usuario_cedula'] = usuario.cedula
                request.session['usuario_username'] = usuario.username
                
                messages.success(request, f'Bienvenido {usuario.nom_completo}')
                return redirect('dashboard')
            else:
                messages.error(request, 'Contraseña incorrecta.')
        
        except Usuario.DoesNotExist:
            messages.error(request, 'Usuario no encontrado.')
    
    return render(request, 'auth/login.html')


def logout_view(request):
    """Vista para cerrar sesión"""
    # Limpiar TODA la sesión (incluye mensajes)
    request.session.flush()
    
    # Agregar mensaje DESPUÉS de limpiar la sesión
    # Así solo aparece una vez en el login
    from django.contrib.messages import get_messages
    storage = get_messages(request)
    for _ in storage:
        pass  # Limpiar mensajes antiguos
    
    return redirect('login')


def dashboard_view(request):
    """Vista principal que redirige según el tipo de usuario"""
    
    if not request.session.get('usuario_id'):
        messages.error(request, 'Debe iniciar sesión.')
        return redirect('login')
    
    usuario_tipo = request.session.get('usuario_tipo')
    
    if usuario_tipo == 'administrador':
        return redirect('dashboard_administrador')
    elif usuario_tipo == 'docente':
        return redirect('dashboard_docente')
    else:
        messages.error(request, 'Tipo de usuario no válido.')
        return redirect('login')


def dashboard_docente(request):
    """Dashboard principal del docente"""
    
    if not request.session.get('usuario_id'):
        messages.error(request, 'Debe iniciar sesión.')
        return redirect('login')
    
    if request.session.get('usuario_tipo') != 'docente':
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')
    
    usuario_id = request.session.get('usuario_id')
    usuario = Usuario.objects.get(id_usuario=usuario_id)
    
    # Importar modelo de Reserva
    from Gestion_Equipos.models import Reserva
    
    # Obtener estadísticas del docente
    reservas_totales = Reserva.objects.filter(id_usuario=usuario).count()
    reservas_pendientes = Reserva.objects.filter(id_usuario=usuario, estado_reserva='Pendiente').count()
    reservas_aprobadas = Reserva.objects.filter(id_usuario=usuario, estado_reserva='Aprobada').count()
    reservas_rechazadas = Reserva.objects.filter(id_usuario=usuario, estado_reserva='Rechazada').count()
    
    # Obtener próximas reservas (aprobadas, ordenadas por fecha)
    from datetime import date
    proximas_reservas = Reserva.objects.filter(
        id_usuario=usuario,
        estado_reserva='Aprobada',
        fecha_uso__gte=date.today()
    ).order_by('fecha_uso', 'hora_inicio')[:5]
    
    context = {
        'usuario': usuario,
        'reservas_totales': reservas_totales,
        'reservas_pendientes': reservas_pendientes,
        'reservas_aprobadas': reservas_aprobadas,
        'reservas_rechazadas': reservas_rechazadas,
        'proximas_reservas': proximas_reservas,
    }
    
    return render(request, 'docente/dashboard.html', context)


def dashboard_administrador(request):
    """Dashboard principal del administrador"""
    
    if not request.session.get('usuario_id'):
        messages.error(request, 'Debe iniciar sesión.')
        return redirect('login')
    
    if request.session.get('usuario_tipo') != 'administrador':
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')
    
    usuario_id = request.session.get('usuario_id')
    usuario = Usuario.objects.get(id_usuario=usuario_id)
    
    # Importar modelos necesarios
    from Gestion_Equipos.models import Reserva, Equipo
    from datetime import date
    
    # Estadísticas de reservas
    total_reservas_pendientes = Reserva.objects.filter(estado_reserva='Pendiente').count()
    total_equipos_disponibles = Equipo.objects.filter(id_estado_equipo__nom_estado='Disponible').count()
    total_equipos_en_uso = Equipo.objects.filter(id_estado_equipo__nom_estado='En uso').count()
    total_equipos_mantenimiento = Equipo.objects.filter(id_estado_equipo__nom_estado__iexact='En Mantenimiento').count()
    
    # Reservas pendientes (últimas 10)
    reservas_pendientes = Reserva.objects.filter(
        estado_reserva='Pendiente'
    ).select_related(
        'id_usuario', 'id_asignatura', 'id_carrera', 'id_aula', 'id_aula__id_bloque'
    ).order_by('fecha_uso', 'hora_inicio')[:10]
    
    # Reservas aprobadas (últimas 10)
    reservas_aprobadas = Reserva.objects.filter(
        estado_reserva='Aprobada'
    ).select_related(
        'id_usuario', 'id_asignatura', 'id_carrera', 'id_aula', 'id_aula__id_bloque'
    ).order_by('-fecha_uso', '-hora_inicio')[:10]
    
    # Reservas rechazadas (últimas 10)
    reservas_rechazadas = Reserva.objects.filter(
        estado_reserva='Rechazada'
    ).select_related(
        'id_usuario', 'id_asignatura', 'id_carrera', 'id_aula', 'id_aula__id_bloque'
    ).order_by('-fecha_uso', '-hora_inicio')[:10]
    
    # Reservas de hoy
    reservas_hoy = Reserva.objects.filter(
        fecha_uso=date.today(),
        estado_reserva='Aprobada'
    ).count()
    
    context = {
        'usuario': usuario,
        'total_pendientes': total_reservas_pendientes,
        'total_equipos_disponibles': total_equipos_disponibles,
        'total_equipos_en_uso': total_equipos_en_uso,
        'total_equipos_mantenimiento': total_equipos_mantenimiento,
        'reservas_pendientes': reservas_pendientes,
        'reservas_aprobadas': reservas_aprobadas,
        'reservas_rechazadas': reservas_rechazadas,
        'reservas_hoy': reservas_hoy,
    }
    
    return render(request, 'administrador/dashboard.html', context)


# ======================================================
# NUEVA VISTA: Recuperar Datos de Cuenta
# ======================================================
def recuperar_datos_view(request):
    """
    Maneja la solicitud POST del modal de recuperación de datos.
    Busca al usuario por cédula y devuelve un mensaje.
    """
    if request.method == 'POST':
        cedula_ingresada = request.POST.get('cedula_recuperar')
        
        # Validar que la cédula no esté vacía
        if not cedula_ingresada:
            messages.error(request, 'Debe ingresar un número de cédula.')
            return redirect('login')
            
        try:
            # Busca al usuario por la cédula
            usuario = Usuario.objects.get(cedula=cedula_ingresada)
            
            # ¡Éxito! Envía un mensaje de éxito con los datos
            # Asegurarse de que el email no sea None antes de mostrarlo
            email_usuario = usuario.email if usuario.email else 'No registrado'
            mensaje = f"Datos encontrados: Usuario: {usuario.username} | Email: {email_usuario}"
            messages.success(request, mensaje)
            
        except Usuario.DoesNotExist:
            # Error: No se encontró
            messages.error(request, 'No se encontró ningún usuario con ese número de cédula.')
        except Exception as e:
            # Otro error
            messages.error(request, f'Ocurrió un error inesperado: {e}')
    
    # Redirige de vuelta a la página de login en cualquier caso
    # La página de login mostrará el mensaje (success o error).
    return redirect('login')