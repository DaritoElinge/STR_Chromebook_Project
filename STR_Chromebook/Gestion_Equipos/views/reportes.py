# ======================================================
# VISTAS DE REPORTES (ADMIN)
# ======================================================

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count
from datetime import datetime
import calendar

# Importar Modelos
from core.models import Usuario
from Gestion_Equipos.models import Reserva, Equipo

# Importar openpyxl
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
except ImportError:
    Workbook = None
    print("ADVERTENCIA: 'openpyxl' no está instalado. La descarga de Excel fallará.")
    print("Ejecuta: pip install openpyxl")


def ver_reportes(request):
    """Vista para visualizar y generar reportes"""
    
    if not request.session.get('usuario_id'):
        messages.error(request, 'Debe iniciar sesión.')
        return redirect('login')
    if request.session.get('usuario_tipo') != 'administrador':
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')
    
    usuario = Usuario.objects.get(id_usuario=request.session.get('usuario_id'))
    
    mes_filtro = request.GET.get('mes', datetime.now().month)
    anio_filtro = request.GET.get('anio', datetime.now().year)
    
    try:
        mes_filtro = int(mes_filtro)
        anio_filtro = int(anio_filtro)
    except:
        mes_filtro = datetime.now().month
        anio_filtro = datetime.now().year
    
    reservas_mes = Reserva.objects.filter(
        fecha_uso__month=mes_filtro,
        fecha_uso__year=anio_filtro
    ).select_related('id_usuario', 'id_carrera', 'id_asignatura', 'id_aula')
    
    total_reservas = reservas_mes.count()
    reservas_aprobadas = reservas_mes.filter(estado_reserva='Aprobada').count()
    reservas_rechazadas = reservas_mes.filter(estado_reserva='Rechazada').count()
    reservas_pendientes = reservas_mes.filter(estado_reserva='Pendiente').count()
    
    total_equipos_solicitados = sum([r.cant_solicitada for r in reservas_mes])
    
    reservas_por_carrera = reservas_mes.values(
        'id_carrera__nom_carrera'
    ).annotate(
        cantidad=Count('id_reserva')
    ).order_by('-cantidad')
    
    reservas_por_docente = reservas_mes.values(
        'id_usuario__nom_completo'
    ).annotate(
        cantidad=Count('id_reserva')
    ).order_by('-cantidad')[:10]
    
    equipos_en_uso = Equipo.objects.filter(
        id_estado_equipo__nom_estado='En uso'
    ).count()
    
    meses = [{'num': i, 'nombre': calendar.month_name[i]} for i in range(1, 13)]
    anios = list(range(2024, datetime.now().year + 2))
    
    context = {
        'usuario': usuario, 'mes_filtro': mes_filtro, 'anio_filtro': anio_filtro,
        'mes_nombre': calendar.month_name[mes_filtro], 'meses': meses, 'anios': anios,
        'total_reservas': total_reservas, 'reservas_aprobadas': reservas_aprobadas,
        'reservas_rechazadas': reservas_rechazadas, 'reservas_pendientes': reservas_pendientes,
        'total_equipos_solicitados': total_equipos_solicitados,
        'reservas_por_carrera': reservas_por_carrera,
        'reservas_por_docente': reservas_por_docente,
        'equipos_en_uso': equipos_en_uso,
        'reservas_mes': reservas_mes.order_by('-fecha_uso'),
    }
    
    return render(request, 'administrador/ver_reportes.html', context)


def descargar_reporte_excel(request):
    """Vista para descargar reporte mensual en Excel"""
    
    if request.session.get('usuario_tipo') != 'administrador':
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')
    
    if Workbook is None:
        messages.error(request, 'La librería openpyxl no está instalada. No se puede generar el reporte.')
        return redirect('ver_reportes') # Asume que no hay namespace

    mes = int(request.GET.get('mes', datetime.now().month))
    anio = int(request.GET.get('anio', datetime.now().year))
    
    wb = Workbook()
    ws = wb.active
    ws.title = f"Reporte {calendar.month_name[mes]} {anio}"
    
    header_fill = PatternFill(start_color="016BB8", end_color="016BB8", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    title_font = Font(bold=True, size=14)
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    
    ws['A1'] = f'REPORTE DE RESERVAS DE CHROMEBOOKS - {calendar.month_name[mes].upper()} {anio}'
    ws['A1'].font = title_font
    ws.merge_cells('A1:H1')
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    
    ws['A2'] = f'Generado el: {datetime.now().strftime("%d/%m/%Y %H:%M")}'
    ws.merge_cells('A2:H2')
    ws['A2'].alignment = Alignment(horizontal='center')
    
    reservas = Reserva.objects.filter(
        fecha_uso__month=mes,
        fecha_uso__year=anio
    ).select_related(
        'id_usuario', 'id_carrera', 'id_asignatura', 'id_aula', 'id_aula__id_bloque'
    ).order_by('fecha_uso', 'hora_inicio')
    
    ws['A4'] = 'ESTADÍSTICAS GENERALES'
    ws['A4'].font = Font(bold=True, size=12)
    
    stats_row = 5
    ws[f'A{stats_row}'] = 'Total de Reservas:'; ws[f'B{stats_row}'] = reservas.count()
    stats_row += 1
    ws[f'A{stats_row}'] = 'Aprobadas:'; ws[f'B{stats_row}'] = reservas.filter(estado_reserva='Aprobada').count()
    stats_row += 1
    ws[f'A{stats_row}'] = 'Rechazadas:'; ws[f'B{stats_row}'] = reservas.filter(estado_reserva='Rechazada').count()
    stats_row += 1
    ws[f'A{stats_row}'] = 'Pendientes:'; ws[f'B{stats_row}'] = reservas.filter(estado_reserva='Pendiente').count()
    stats_row += 1
    ws[f'A{stats_row}'] = 'Total Equipos Solicitados:'; ws[f'B{stats_row}'] = sum([r.cant_solicitada for r in reservas])
    
    detail_row = stats_row + 3
    ws[f'A{detail_row}'] = 'DETALLE DE RESERVAS'
    ws[f'A{detail_row}'].font = Font(bold=True, size=12)
    
    header_row = detail_row + 1
    headers = ['Fecha', 'Hora Inicio', 'Hora Fin', 'Docente', 'Carrera', 'Asignatura', 
               'Bloque', 'Aula', 'Cantidad', 'Responsable', 'Teléfono', 'Estado']
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col_num)
        cell.value = header; cell.fill = header_fill; cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center'); cell.border = border
    
    data_row = header_row + 1
    for reserva in reservas:
        ws.cell(row=data_row, column=1, value=reserva.fecha_uso.strftime('%d/%m/%Y'))
        ws.cell(row=data_row, column=2, value=reserva.hora_inicio.strftime('%H:%M'))
        ws.cell(row=data_row, column=3, value=reserva.hora_fin.strftime('%H:%M'))
        ws.cell(row=data_row, column=4, value=reserva.id_usuario.nom_completo)
        ws.cell(row=data_row, column=5, value=reserva.id_carrera.nom_carrera)
        ws.cell(row=data_row, column=6, value=reserva.id_asignatura.nom_asignatura)
        ws.cell(row=data_row, column=7, value=reserva.id_aula.id_bloque.nom_bloque)
        ws.cell(row=data_row, column=8, value=reserva.id_aula.nom_aula)
        ws.cell(row=data_row, column=9, value=reserva.cant_solicitada)
        ws.cell(row=data_row, column=10, value=reserva.responsable_entrega)
        ws.cell(row=data_row, column=11, value=reserva.telefono_contacto)
        ws.cell(row=data_row, column=12, value=reserva.estado_reserva)
        
        for col in range(1, 13):
            cell = ws.cell(row=data_row, column=col)
            cell.border = border; cell.alignment = Alignment(horizontal='left', vertical='center')
        
        data_row += 1
    
    column_widths = [12, 12, 12, 30, 35, 30, 10, 15, 10, 35, 15, 15]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[chr(64 + i)].width = width
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f'Reporte_Chromebooks_{calendar.month_name[mes]}_{anio}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response