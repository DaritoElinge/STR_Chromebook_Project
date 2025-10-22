from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from core.models import Usuario
from .models import Reserva
from .forms import ReservaForm

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
            
            messages.success(request, f'Reserva #{reserva.id_reserva} creada exitosamente. Estado: Pendiente de aprobación.')
            return redirect('dashboard_docente')
    else:
        form = ReservaForm()
    
    context = {
        'usuario': usuario,
        'form': form
    }
    
    return render(request, 'docente/crear_reserva.html', context)


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
        
        from core.models import Aula
        aulas = Aula.objects.filter(id_bloque_id=bloque_id).values('id_aula', 'nom_aula')
        
        return JsonResponse({'aulas': list(aulas)})
    
    return JsonResponse({'aulas': []})


def filtrar_asignaturas_por_carrera(request):
    """API para filtrar asignaturas según la carrera seleccionada"""
    
    if request.method == 'GET':
        carrera_id = request.GET.get('carrera_id')
        
        if not carrera_id:
            return JsonResponse({'asignaturas': []})
        
        from core.models import Asignatura
        asignaturas = Asignatura.objects.filter(id_carrera_id=carrera_id).values('id_asignatura', 'nom_asignatura')
        
        return JsonResponse({'asignaturas': list(asignaturas)})
    
    return JsonResponse({'asignaturas': []})