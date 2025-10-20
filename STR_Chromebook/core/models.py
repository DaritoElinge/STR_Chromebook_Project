from django.db import models
from django.contrib.auth.hashers import make_password, check_password

# ==================== USUARIOS ====================

class TipoUsuario(models.Model):
    """Tabla: Tb_TIPO_USUARIO"""
    id_tipo_usuario = models.AutoField(primary_key=True, db_column='ID_TipoUsuario')
    nom_rol = models.CharField(max_length=50, db_column='Nom_Rol')
    
    class Meta:
        db_table = 'Tb_TIPO_USUARIO'
        verbose_name = 'Tipo de Usuario'
        verbose_name_plural = 'Tipos de Usuario'
    
    def __str__(self):
        return self.nom_rol


class TituloProfesional(models.Model):
    """Tabla: Tb_TITULO_PROFESIONAL"""
    id_titulo = models.AutoField(primary_key=True, db_column='ID_Titulo')
    nom_titulo = models.CharField(max_length=50, db_column='Nom_Titulo')
    
    class Meta:
        db_table = 'Tb_TITULO_PROFESIONAL'
        verbose_name = 'Título Profesional'
        verbose_name_plural = 'Títulos Profesionales'
    
    def __str__(self):
        return self.nom_titulo


class Usuario(models.Model):
    """Tabla: Tb_USUARIO"""
    id_usuario = models.AutoField(primary_key=True, db_column='ID_Usuario')
    nom_completo = models.CharField(max_length=150, db_column='Nom_Completo')
    cedula = models.CharField(max_length=10, unique=True, db_column='Cedula')
    telefono = models.CharField(max_length=10, db_column='Telefono')
    email = models.CharField(max_length=100, db_column='Email')
    
    # Campos de autenticación
    username = models.CharField(max_length=10, unique=True, db_column='Username',help_text='Nombre de usuario para login')
    password = models.CharField(max_length=255, db_column='Password', help_text='Contraseña encriptada')

    # Relaciones
    id_tipo_usuario = models.ForeignKey(
        TipoUsuario, 
        on_delete=models.PROTECT,
        db_column='ID_TipoUsuario'
    )
    id_titulo = models.ForeignKey(
        TituloProfesional,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='ID_Titulo'
    )
    
    class Meta:
        db_table = 'Tb_USUARIO'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.nom_completo} - {self.cedula}"

    def set_password(self, raw_password):
        """Encripta y guarda la contraseña usando el hash de Django"""
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Verifica si la contraseña ingresada coincide con la encriptada"""
        return check_password(raw_password, self.password)

# ==================== ACADÉMICO ====================

class Facultad(models.Model):
    """Tabla: Tb_FACULTAD (Nueva Entidad)"""
    id_facultad = models.AutoField(primary_key=True, db_column='ID_Facultad')
    nom_facultad = models.CharField(max_length=100, db_column='Nom_Facultad')
    
    class Meta:
        db_table = 'Tb_FACULTAD'
        verbose_name = 'Facultad'
        verbose_name_plural = 'Facultades'
    
    def __str__(self):
        return self.nom_facultad

class Carrera(models.Model):
    """Tabla: Tb_CARRERA"""
    id_carrera = models.AutoField(primary_key=True, db_column='ID_Carrera')
    nom_carrera = models.CharField(max_length=100, db_column='Nom_Carrera')
    
    # Relaciones
    id_facultad = models.ForeignKey(
        Facultad,
        on_delete=models.PROTECT,  
        db_column='ID_Facultad',
        verbose_name='Facultad'
    )

    class Meta:
        db_table = 'Tb_CARRERA'
        verbose_name = 'Carrera'
        verbose_name_plural = 'Carreras'
    
    def __str__(self):
        return self.nom_carrera


class Asignatura(models.Model):
    """Tabla: Tb_ASIGNATURA"""
    id_asignatura = models.AutoField(primary_key=True, db_column='ID_Asignatura')
    nom_asignatura = models.CharField(max_length=50, db_column='Nom_Asignatura')
    
    class Meta:
        db_table = 'Tb_ASIGNATURA'
        verbose_name = 'Asignatura'
        verbose_name_plural = 'Asignaturas'
    
    def __str__(self):
        return self.nom_asignatura


class DocenteCarrera(models.Model):
    """Tabla: Tb_DOCENTE_CARRERA (Relación N:M entre Usuario y Carrera)"""
    id_docente_carrera = models.AutoField(primary_key=True, db_column='ID_DocenteCarrera')
    
    # Relaciones
    id_usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='ID_Usuario'
    )
    id_carrera = models.ForeignKey(
        Carrera,
        on_delete=models.CASCADE,
        db_column='ID_Carrera'
    )
    
    class Meta:
        db_table = 'Tb_DOCENTE_CARRERA'
        verbose_name = 'Docente-Carrera'
        verbose_name_plural = 'Docentes-Carreras'
        unique_together = ('id_usuario', 'id_carrera')
    
    def __str__(self):
        return f"{self.id_usuario.nom_completo} - {self.id_carrera.nom_carrera}"


# ==================== INFRAESTRUCTURA ====================

class Bloque(models.Model):
    """Tabla: Tb_BLOQUE"""
    id_bloque = models.AutoField(primary_key=True, db_column='ID_Bloque')
    nom_bloque = models.CharField(max_length=30, db_column='Nom_Bloque')
    
    class Meta:
        db_table = 'Tb_BLOQUE'
        verbose_name = 'Bloque'
        verbose_name_plural = 'Bloques'
    
    def __str__(self):
        return self.nom_bloque


class Aula(models.Model):
    """Tabla: Tb_AULA"""
    id_aula = models.AutoField(primary_key=True, db_column='ID_Aula')
    nom_aula = models.CharField(max_length=30, db_column='Nom_Aula')
    
    # Relación
    id_bloque = models.ForeignKey(
        Bloque,
        on_delete=models.CASCADE,
        db_column='ID_Bloque'
    )
    
    class Meta:
        db_table = 'Tb_AULA'
        verbose_name = 'Aula'
        verbose_name_plural = 'Aulas'
    
    def __str__(self):
        return f"{self.nom_aula} - {self.id_bloque.nom_bloque}"


class Rack(models.Model):
    """Tabla: Tb_RACK"""
    id_rack = models.AutoField(primary_key=True, db_column='ID_Rack')
    nom_rack = models.CharField(max_length=10, db_column='Nom_Rack')
    ubicacion = models.CharField(max_length=50, db_column='Ubicacion')
    capacidad_total = models.IntegerField(db_column='Capacidad_Total')
    capacidad_func = models.IntegerField(db_column='Capacidad_Func')
    estado_rack = models.CharField(max_length=20, db_column='Estado_Rack')
    
    class Meta:
        db_table = 'Tb_RACK'
        verbose_name = 'Rack'
        verbose_name_plural = 'Racks'
    
    def __str__(self):
        return f"{self.nom_rack} - {self.ubicacion}"
