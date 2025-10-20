from django.shortcuts import render, redirect
from django.contrib import messages
from core.models import Usuario

def login_view(request):
    """Vista de login para docentes y administradores"""
    
    # Si ya está autenticado, redirigir al dashboard
    if request.session.get('usuario_id'):
        return redirect('dashboard')
    
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
                
                
                return redirect('dashboard')
            else:
                messages.error(request, 'Contraseña incorrecta.')
        
        except Usuario.DoesNotExist:
            messages.error(request, 'Usuario no encontrado.')
    
    return render(request, 'auth/login.html')


def logout_view(request):
    """Vista para cerrar sesión"""
    request.session.flush()
    messages.success(request, '')
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
    
    context = {
        'usuario': usuario,
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
    
    context = {
        'usuario': usuario,
    }
    
    return render(request, 'administrador/dashboard.html', context)