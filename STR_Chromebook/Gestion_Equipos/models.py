from django.db import models
from core.models import Usuario, Asignatura, Carrera, Aula, Rack

# ==================== EQUIPOS ====================

class EstadoEquipo(models.Model):
    """Tabla: Tb_ESTADO_EQUIPO"""
    id_estado_equipo = models.AutoField(primary_key=True, db_column='ID_EstadoEquipo')
    nom_estado = models.CharField(max_length=50, db_column='Nom_Estado')
    
    class Meta:
        db_table = 'Tb_ESTADO_EQUIPO'
        verbose_name = 'Estado de Equipo'
        verbose_name_plural = 'Estados de Equipo'
    
    def __str__(self):
        return self.nom_estado


class Equipo(models.Model):
    """Tabla: Tb_EQUIPO"""
    id_equipo = models.AutoField(primary_key=True, db_column='ID_Equipo')
    nom_equipo = models.CharField(max_length=10, db_column='Nom_Equipo')
    num_serie = models.CharField(max_length=50, unique=True, db_column='Num_Serie')
    modelo = models.CharField(max_length=50, db_column='Modelo')
    
    # Relaciones
    id_rack = models.ForeignKey(
        Rack,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='ID_Rack'
    )
    id_estado_equipo = models.ForeignKey(
        EstadoEquipo,
        on_delete=models.PROTECT,
        db_column='ID_EstadoEquipo'
    )
    
    class Meta:
        db_table = 'Tb_EQUIPO'
        verbose_name = 'Equipo'
        verbose_name_plural = 'Equipos'
    
    def __str__(self):
        return f"{self.nom_equipo} - {self.num_serie}"


# ==================== RESERVAS Y ASIGNACIONES ====================

class Reserva(models.Model):
    """Tabla: Tb_RESERVA"""
    id_reserva = models.AutoField(primary_key=True, db_column='ID_Reserva')
    fecha_uso = models.DateField(db_column='Fecha_Uso')
    hora_inicio = models.TimeField(db_column='Hora_Inicio')
    hora_fin = models.TimeField(db_column='Hora_Fin')
    cant_solicitada = models.IntegerField(db_column='Cant_Solicitada')
    estado_reserva = models.CharField(max_length=20, db_column='Estado_Reserva', default='Pendiente')
    
    # Campos adicionales para el responsable
    responsable_entrega = models.CharField(max_length=150, db_column='Responsable_Entrega', 
                                          help_text='Nombre del responsable de recibir los equipos')
    telefono_contacto = models.CharField(max_length=10, db_column='Telefono_Contacto',
                                        help_text='Teléfono de contacto del responsable')
    
    # Campo para motivo de rechazo
    motivo_rechazo = models.TextField(db_column='Motivo_Rechazo', blank=True, null=True,
                                      help_text='Motivo por el cual se rechazó la reserva')
    
    # Relaciones
    id_usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='ID_Usuario'
    )
    id_asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.CASCADE,
        db_column='ID_Asignatura'
    )
    id_aula = models.ForeignKey(
        Aula,
        on_delete=models.CASCADE,
        db_column='ID_Aula'
    )
    id_carrera = models.ForeignKey(
        Carrera,
        on_delete=models.CASCADE,
        db_column='ID_Carrera'
    )
    
    class Meta:
        db_table = 'Tb_RESERVA'
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
    
    def __str__(self):
        return f"Reserva {self.id_reserva} - {self.id_usuario.nom_completo} - {self.fecha_uso}"


class AsignacionEquipo(models.Model):
    """Tabla: Tb_ASIGNACION_EQUIPO"""
    id_asig_equipo = models.AutoField(primary_key=True, db_column='ID_AsigEquipo')
    fecha_registro = models.DateTimeField(auto_now_add=True, db_column='Fecha_Registro')
    
    # Relaciones
    id_reserva = models.ForeignKey(
        Reserva,
        on_delete=models.CASCADE,
        db_column='ID_Reserva'
    )
    id_equipo = models.ForeignKey(
        Equipo,
        on_delete=models.CASCADE,
        db_column='ID_Equipo'
    )
    
    class Meta:
        db_table = 'Tb_ASIGNACION_EQUIPO'
        verbose_name = 'Asignación de Equipo'
        verbose_name_plural = 'Asignaciones de Equipos'
        unique_together = ('id_reserva', 'id_equipo')
    
    def __str__(self):
        return f"Asignación {self.id_asig_equipo} - Reserva {self.id_reserva.id_reserva}"