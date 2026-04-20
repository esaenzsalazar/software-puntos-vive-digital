"""
Models for Puntos Vive Digital system.
Contract CD-224-2026 - Alcaldía de Bugalagrande
Defines database structure for citizen management, attention tracking, and resource management.
"""
from django.db import models


# ==============================================================================
# MODELOS BÁSICOS DEL SISTEMA
# ==============================================================================

class UsuarioSistema(models.Model):
    """
    Modelo de usuario del sistema heredado de la base de datos original.
    Nota: Para nuevos desarrollos, usar el sistema de usuarios de Django.
    """
    usu_cdgo = models.AutoField(primary_key=True, db_column='USU_CDGO')
    usu_nombre = models.CharField(max_length=64, db_column='USU_NOMBRE', null=True, blank=True)
    usu_passwd = models.CharField(max_length=256, db_column='USU_PASSWD', null=True, blank=True)
    usu_estdo = models.CharField(max_length=1, db_column='USU_ESTDO', null=True, blank=True)

    class Meta:
        db_table = 'usu_usuariosistema'
        verbose_name = 'Usuario del Sistema'
        verbose_name_plural = 'Usuarios del Sistema'

    def __str__(self):
        return f"{self.usu_nombre} ({self.usu_estdo})"


class ListaValor(models.Model):
    """
    Modelo para listas de valores genéricos del sistema.
    Permite gestionar listas desplegables dinámicamente.
    """
    lva_cdgo = models.IntegerField(primary_key=True, db_column='LVA_CDGO')
    lva_nombre = models.CharField(max_length=64, db_column='LVA_NOMBRE')
    lva_descr = models.CharField(max_length=256, db_column='LVA_DESCR', null=True, blank=True)
    lva_estdo = models.CharField(max_length=1, db_column='LVA_ESTDO')

    class Meta:
        db_table = 'lva_listavalor'
        verbose_name = 'Lista de Valor'
        verbose_name_plural = 'Listas de Valor'

    def __str__(self):
        return self.lva_nombre


# ==============================================================================
# MODELOS PRINCIPALES DEL PVD
# ==============================================================================

class PuntoViveDigital(models.Model):
    """
    Modelo expandible para gestionar múltiples Puntos Vive Digital.
    Permite crear nuevos PVDs dinámicamente desde el sistema.
    """
    ESTADO_CHOICES = [
        ('A', 'Activo'),
        ('I', 'Inactivo'),
        ('M', 'En mantenimiento'),
    ]

    pvd_cdgo = models.AutoField(primary_key=True, db_column='PVD_CDGO')
    pvd_nombre = models.CharField(
        max_length=128,
        db_column='PVD_NOMBRE',
        null=True,
        blank=True,
        verbose_name='Nombre del Punto Vive Digital'
    )
    pvd_dircion = models.CharField(
        max_length=128,
        db_column='PVD_DIRCION',
        null=True,
        blank=True,
        verbose_name='Dirección'
    )
    pvd_barrio = models.CharField(
        max_length=64,
        db_column='PVD_BARRIO',
        null=True,
        blank=True,
        verbose_name='Barrio/Vereda'
    )
    pvd_telefono = models.CharField(
        max_length=32, 
        db_column='PVD_TELEFONO', 
        null=True, 
        blank=True,
        verbose_name='Teléfono'
    )
    pvd_correo = models.CharField(
        max_length=128, 
        db_column='PVD_CORREO', 
        null=True, 
        blank=True,
        verbose_name='Correo electrónico'
    )
    pvd_estdo = models.CharField(
        max_length=1, 
        db_column='PVD_ESTDO', 
        default='A',
        choices=ESTADO_CHOICES, 
        verbose_name='Estado'
    )
    pvd_fch_crea = models.DateField(
        auto_now_add=True, 
        db_column='PVD_FCH_CREA', 
        null=True,
        verbose_name='Fecha de creación'
    )
    pvd_descripcion = models.TextField(
        db_column='PVD_DESCRIPCION', 
        null=True, 
        blank=True,
        verbose_name='Descripción/Notas'
    )

    class Meta:
        db_table = 'pvd_puntovivedigital'
        ordering = ['pvd_nombre']
        verbose_name = 'Punto Vive Digital'
        verbose_name_plural = 'Puntos Vive Digital'

    def __str__(self):
        return self.pvd_nombre

    def get_total_atenciones(self):
        """Retorna el total de atenciones asociadas a este PVD."""
        return self.atencion_set.count()

    def get_total_ciudadanos(self):
        """Retorna el total de ciudadanos asociados a este PVD."""
        return self.ciudadano_set.count()


class Operador(models.Model):
    """
    Modelo para operadores/funcionarios que trabajan en un PVD.
    Los operadores son creados automáticamente al crear usuarios Admin PVD.
    """
    ESTADO_CHOICES = [
        ('A', 'Activo'),
        ('I', 'Inactivo'),
    ]

    opr_cdgo = models.AutoField(primary_key=True, db_column='OPR_CDGO')
    pvd_cdgo = models.ForeignKey(
        'PuntoViveDigital',
        models.SET_NULL,
        db_column='PVD_CDGO',
        null=True,
        blank=True,
        verbose_name='Punto Vive Digital'
    )
    usu_cdgo = models.ForeignKey(
        UsuarioSistema, 
        models.DO_NOTHING, 
        db_column='USU_CDGO', 
        null=True, 
        blank=True,
        verbose_name='Usuario del Sistema'
    )
    opr_tpodoc = models.CharField(
        max_length=32, 
        db_column='OPR_TPODOC', 
        null=True, 
        blank=True,
        verbose_name='Tipo de Documento'
    )
    opr_numdoc = models.CharField(
        max_length=32,
        db_column='OPR_NUMDOC',
        null=True,
        blank=True,
        unique=True,
        verbose_name='Número de Documento'
    )
    opr_nmbres = models.CharField(
        max_length=128, 
        db_column='OPR_NMBRES', 
        null=True, 
        blank=True,
        verbose_name='Nombres'
    )
    opr_aplldos = models.CharField(
        max_length=128, 
        db_column='OPR_APLLDOS', 
        null=True, 
        blank=True,
        verbose_name='Apellidos'
    )
    opr_email = models.CharField(
        max_length=128, 
        db_column='OPR_EMAIL', 
        null=True, 
        blank=True,
        verbose_name='Correo Electrónico'
    )
    opr_tlfno = models.CharField(
        max_length=32, 
        db_column='OPR_TLFNO', 
        null=True, 
        blank=True,
        verbose_name='Teléfono'
    )
    opr_estdo = models.CharField(
        max_length=1, 
        db_column='OPR_ESTDO', 
        null=True, 
        blank=True, 
        choices=ESTADO_CHOICES,
        verbose_name='Estado'
    )

    class Meta:
        db_table = 'opr_operador'
        verbose_name = 'Operador'
        verbose_name_plural = 'Operadores'

    def __str__(self):
        return f"{self.opr_nmbres} {self.opr_aplldos}"


class Ciudadano(models.Model):
    """
    Modelo para gestionar los ciudadanos atendidos en los PVDs.
    Incluye información demográfica, de ubicación y discapacidad.
    """
    ESTADO_CHOICES = [
        ('A', 'Activo'),
        ('I', 'Inactivo'),
    ]

    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]

    ciu_cdgo = models.AutoField(primary_key=True, db_column='CIU_CDGO')
    pvd_cdgo = models.ForeignKey(
        'PuntoViveDigital',
        models.SET_NULL,
        db_column='PVD_CDGO',
        null=True,
        blank=True,
        verbose_name='Punto Vive Digital'
    )
    ciu_tpodoc = models.CharField(
        max_length=32, 
        db_column='CIU_TPODOC', 
        null=True, 
        blank=True,
        verbose_name='Tipo de Documento'
    )
    ciu_numdoc = models.CharField(
        max_length=32,
        db_column='CIU_NUMDOC',
        null=True,
        blank=True,
        unique=True,
        verbose_name='Número de Documento'
    )
    ciu_nmbres = models.CharField(
        max_length=128, 
        db_column='CIU_NMBRES', 
        null=True, 
        blank=True,
        verbose_name='Nombres'
    )
    ciu_aplldos = models.CharField(
        max_length=128, 
        db_column='CIU_APLLDOS', 
        null=True, 
        blank=True,
        verbose_name='Apellidos'
    )
    ciu_fchancm = models.DateField(
        db_column='CIU_FCHANCM', 
        null=True, 
        blank=True,
        verbose_name='Fecha de Nacimiento'
    )
    ciu_genro = models.CharField(
        max_length=32, 
        db_column='CIU_GENRO', 
        choices=GENERO_CHOICES, 
        null=True, 
        blank=True,
        verbose_name='Género'
    )
    ciu_etnia = models.CharField(
        max_length=64, 
        db_column='CIU_ETNIA', 
        null=True, 
        blank=True,
        verbose_name='Etnia'
    )
    ciu_nvleduc = models.CharField(
        max_length=64, 
        db_column='CIU_NVLEDUC', 
        null=True, 
        blank=True,
        verbose_name='Nivel Educativo'
    )
    ciu_ocpcion = models.CharField(
        max_length=64, 
        db_column='CIU_OCPCION', 
        null=True, 
        blank=True,
        verbose_name='Ocupación'
    )
    ciu_discapacidad = models.BooleanField(
        db_column='CIU_DISCAPACIDAD', 
        default=False,
        verbose_name='Tiene Discapacidad'
    )
    ciu_desc_discapacidad = models.CharField(
        max_length=128, 
        db_column='CIU_DESC_DISCAPACIDAD', 
        null=True, 
        blank=True,
        verbose_name='Descripción Discapacidad'
    )

    # Campos de ubicación
    ciu_dircion = models.CharField(
        max_length=128, 
        db_column='CIU_DIRCION', 
        null=True, 
        blank=True,
        verbose_name='Dirección'
    )
    ciu_barrio = models.CharField(
        max_length=64, 
        db_column='CIU_BARRIO', 
        null=True, 
        blank=True,
        verbose_name='Barrio'
    )
    ciu_zrural = models.CharField(
        max_length=64, 
        db_column='CIU_ZRURAL', 
        null=True, 
        blank=True,
        verbose_name='Zona Rural'
    )

    ciu_estrato = models.IntegerField(
        db_column='CIU_ESTRATO', 
        default=1,
        verbose_name='Estrato Socioeconómico'
    )
    ciu_estdo = models.CharField(
        max_length=1, 
        db_column='CIU_ESTDO', 
        default='A', 
        choices=ESTADO_CHOICES,
        verbose_name='Estado'
    )
    ciu_email = models.CharField(
        max_length=128, 
        db_column='CIU_EMAIL', 
        default='', 
        blank=True,
        verbose_name='Correo Electrónico'
    )
    ciu_tlfno = models.CharField(
        max_length=32,
        db_column='CIU_TLFNO',
        null=True,
        blank=True,
        verbose_name='Teléfono'
    )
    ciu_pendiente_aprobacion = models.BooleanField(
        db_column='CIU_PENDIENTE_APROBACION',
        default=False,
        verbose_name='Pendiente de Aprobación'
    )
    ciu_fecha_registro = models.DateTimeField(
        db_column='CIU_FECHA_REGISTRO',
        auto_now_add=True,
        null=True,
        verbose_name='Fecha de Registro'
    )

    class Meta:
        db_table = 'ciu_ciudadano'
        verbose_name = 'Ciudadano'
        verbose_name_plural = 'Ciudadanos'
        indexes = [
            models.Index(fields=['ciu_nmbres', 'ciu_aplldos'], name='idx_ciu_nombres'),
            models.Index(fields=['pvd_cdgo', 'ciu_estdo'], name='idx_ciu_pvd_estdo'),
        ]

    def __str__(self):
        return f"{self.ciu_nmbres} {self.ciu_aplldos} ({self.ciu_numdoc})"


class Recurso(models.Model):
    """
    Modelo para gestionar los recursos/equipos disponibles en cada PVD.
    Ejemplo: Computadores, tablets, impresoras, etc.
    """
    ESTADO_CHOICES = [
        ('A', 'Activo'),
        ('I', 'Inactivo'),
    ]

    rec_cdgo = models.IntegerField(primary_key=True, db_column='REC_CDGO')
    pvd_cdgo = models.ForeignKey(
        'PuntoViveDigital',
        models.SET_NULL,
        db_column='PVD_CDGO',
        null=True,
        blank=True,
        verbose_name='Punto Vive Digital'
    )
    rec_tipo = models.CharField(
        max_length=64, 
        db_column='REC_TIPO',
        verbose_name='Tipo de Recurso'
    )
    rec_estdo = models.CharField(
        max_length=1, 
        db_column='REC_ESTDO', 
        choices=ESTADO_CHOICES,
        verbose_name='Estado'
    )

    class Meta:
        db_table = 'rec_recurso'
        verbose_name = 'Recurso'
        verbose_name_plural = 'Recursos'

    def __str__(self):
        return f"Recurso: {self.rec_tipo}"


# ==============================================================================
# MODELOS DE ATENCIÓN Y SERVICIOS
# ==============================================================================

class PrestamoRecurso(models.Model):
    """
    Modelo para registrar préstamos de recursos a ciudadanos.
    Registra fecha de entrega, devolución y observaciones.
    """
    prs_cdgo = models.AutoField(primary_key=True, db_column='PRS_CDGO')
    rec_cdgo = models.ForeignKey(
        'Recurso',
        models.PROTECT,
        db_column='REC_CDGO',
        null=True,
        blank=True,
        verbose_name='Recurso'
    )
    prs_fchent = models.DateTimeField(
        db_column='PRS_FCHENT',
        verbose_name='Fecha de Entrega'
    )
    prs_fchdev = models.DateTimeField(
        db_column='PRS_FCHDEV', 
        null=True, 
        blank=True,
        verbose_name='Fecha de Devolución'
    )
    prs_obs = models.CharField(
        max_length=512, 
        db_column='PRS_OBS', 
        null=True, 
        blank=True,
        verbose_name='Observaciones'
    )

    class Meta:
        db_table = 'prs_prestamorecurso'
        verbose_name = 'Préstamo de Recurso'
        verbose_name_plural = 'Préstamos de Recursos'

    def __str__(self):
        return f"Préstamo {self.prs_cdgo}"


class Atencion(models.Model):
    """
    Modelo principal para registrar atenciones a ciudadanos en los PVDs.
    Vincula ciudadano, operador y recursos prestados.
    """
    ESTADO_CHOICES = [
        ('P', 'Pendiente'),
        ('F', 'Finalizada'),
        ('C', 'Cancelada'),
    ]

    atn_cdgo = models.AutoField(primary_key=True, db_column='ATN_CDGO')
    pvd_cdgo = models.ForeignKey(
        'PuntoViveDigital',
        models.SET_NULL,
        db_column='PVD_CDGO',
        null=True,
        blank=True,
        verbose_name='Punto Vive Digital'
    )
    ciu_cdgo = models.ForeignKey(
        'Ciudadano',
        models.PROTECT,
        db_column='CIU_CDGO',
        null=True,
        blank=True,
        verbose_name='Ciudadano'
    )
    opr_cdgo = models.ForeignKey(
        'Operador',
        models.PROTECT,
        db_column='OPR_CDGO',
        null=True,
        blank=True,
        verbose_name='Operador'
    )
    prs_cdgo = models.ForeignKey(
        'PrestamoRecurso',
        models.SET_NULL,
        db_column='PRS_CDGO',
        null=True,
        blank=True,
        verbose_name='Préstamo'
    )
    atn_fecha = models.DateField(
        db_column='ATN_FECHA',
        verbose_name='Fecha de Atención'
    )
    atn_hrini = models.TimeField(
        db_column='ATN_HRINI',
        verbose_name='Hora de Inicio'
    )
    atn_hrfin = models.TimeField(
        db_column='ATN_HRFIN', 
        null=True, 
        blank=True,
        verbose_name='Hora de Finalización'
    )
    atn_estdo = models.CharField(
        max_length=1, 
        db_column='ATN_ESTDO', 
        default='P', 
        choices=ESTADO_CHOICES,
        verbose_name='Estado'
    )
    atn_obs = models.CharField(
        max_length=512, 
        db_column='ATN_OBS', 
        null=True, 
        blank=True,
        verbose_name='Observaciones'
    )

    class Meta:
        db_table = 'atn_atencion'
        verbose_name = 'Atención'
        verbose_name_plural = 'Atenciones'
        indexes = [
            models.Index(fields=['pvd_cdgo', 'atn_fecha'], name='idx_atn_pvd_fecha'),
            models.Index(fields=['atn_estdo'], name='idx_atn_estdo'),
        ]

    def __str__(self):
        return f"Atención {self.atn_cdgo} - {self.atn_fecha}"


class Servicio(models.Model):
    """
    Modelo para registrar servicios prestados durante una atención.
    Permite categorizar y hacer seguimiento de los servicios.
    """
    ESTADO_CHOICES = [
        ('A', 'Activo'),
        ('I', 'Inactivo'),
    ]

    REQUIERE_EQUIPO_CHOICES = [
        ('S', 'Sí'),
        ('N', 'No'),
    ]

    srv_cdgo = models.AutoField(primary_key=True, db_column='SRV_CDGO')
    atn_cdgo = models.ForeignKey(
        'Atencion',
        models.PROTECT,
        db_column='ATN_CDGO',
        null=True,
        blank=True,
        verbose_name='Atención'
    )
    srv_nombre = models.CharField(
        max_length=128, 
        db_column='SRV_NOMBRE',
        verbose_name='Nombre del Servicio'
    )
    srv_descr = models.CharField(
        max_length=512, 
        db_column='SRV_DESCR', 
        null=True, 
        blank=True,
        verbose_name='Descripción'
    )
    srv_tipo = models.CharField(
        max_length=64, 
        db_column='SRV_TIPO',
        verbose_name='Tipo de Servicio'
    )
    srv_reqeqp = models.CharField(
        max_length=1, 
        db_column='SRV_REQEQP', 
        default='N', 
        choices=REQUIERE_EQUIPO_CHOICES,
        verbose_name='¿Requiere Equipo?'
    )
    srv_estdo = models.CharField(
        max_length=1, 
        db_column='SRV_ESTDO', 
        default='A', 
        choices=ESTADO_CHOICES,
        verbose_name='Estado'
    )

    class Meta:
        db_table = 'srv_servicio'
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'

    def __str__(self):
        return self.srv_nombre


class Satisfaccion(models.Model):
    """
    Modelo para registrar encuestas de satisfacción de ciudadanos.
    Permite medir la calidad del servicio prestado en los PVDs.
    """
    sat_cdgo = models.AutoField(primary_key=True, db_column='SAT_CDGO')
    atn_cdgo = models.ForeignKey(
        'Atencion',
        models.PROTECT,
        db_column='ATN_CDGO',
        null=True,
        blank=True,
        verbose_name='Atención'
    )
    sat_calif = models.IntegerField(
        db_column='SAT_CALIF',
        verbose_name='Calificación (1-5)'
    )
    sat_cmntrio = models.CharField(
        max_length=512, 
        db_column='SAT_CMNTRIO', 
        null=True, 
        blank=True,
        verbose_name='Comentario'
    )
    sat_fecha = models.DateTimeField(
        db_column='SAT_FECHA',
        verbose_name='Fecha de Encuesta'
    )

    class Meta:
        db_table = 'sat_satisfaccion'
        verbose_name = 'Encuesta de Satisfacción'
        verbose_name_plural = 'Encuestas de Satisfacción'

    def __str__(self):
        return f"Calificación: {self.sat_calif} - {self.sat_fecha.strftime('%Y-%m-%d')}"


# ==============================================================================
# MODELOS DE AUDITORÍA Y PERFIL DE USUARIO
# ==============================================================================

class AuditoriaAccion(models.Model):
    """
    Modelo para registrar auditoría de acciones del sistema.
    Permite rastrear cambios y actividades de los usuarios.
    Contrato CD-224-2026
    """
    TIPO_ACCION = [
        ('CREATE', 'Creación'),
        ('UPDATE', 'Actualización'),
        ('DELETE', 'Eliminación'),
        ('LOGIN', 'Inicio de sesión'),
        ('LOGOUT', 'Cierre de sesión'),
        ('EXPORT', 'Exportación de datos'),
        ('OTHER', 'Otra acción'),
    ]

    aud_cdgo = models.AutoField(primary_key=True, db_column='AUD_CDGO')
    usuario = models.CharField(
        max_length=128, 
        db_column='AUD_USUARIO', 
        null=True, 
        blank=True,
        verbose_name='Usuario'
    )
    accion = models.CharField(
        max_length=32, 
        db_column='AUD_ACCION', 
        choices=TIPO_ACCION,
        verbose_name='Acción'
    )
    modelo_afectado = models.CharField(
        max_length=128, 
        db_column='AUD_MODELO', 
        null=True, 
        blank=True,
        verbose_name='Modelo Afectado'
    )
    objeto_id = models.CharField(
        max_length=128, 
        db_column='AUD_OBJETO_ID', 
        null=True, 
        blank=True,
        verbose_name='ID del Objeto'
    )
    descripcion = models.TextField(
        db_column='AUD_DESCRIPCION', 
        null=True, 
        blank=True,
        verbose_name='Descripción'
    )
    ip_address = models.CharField(
        max_length=45, 
        db_column='AUD_IP', 
        null=True, 
        blank=True,
        verbose_name='Dirección IP'
    )
    fecha_accion = models.DateTimeField(
        auto_now_add=True, 
        db_column='AUD_FECHA',
        verbose_name='Fecha y Hora'
    )

    class Meta:
        db_table = 'aud_auditoria_accion'
        ordering = ['-fecha_accion']
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'

    def __str__(self):
        return f"[{self.get_accion_display()}] {self.usuario} - {self.modelo_afectado} ({self.fecha_accion.strftime('%Y-%m-%d %H:%M')})"


class UserProfile(models.Model):
    """
    Perfil de usuario para almacenar la relación con un PVD.
    Permite que los Admin PVD tengan asignado su edificio específico.
    """
    user = models.OneToOneField(
        'auth.User', 
        on_delete=models.CASCADE, 
        related_name='pvd_profile',
        verbose_name='Usuario'
    )
    pvd_asignado = models.ForeignKey(
        'PuntoViveDigital',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='PVD Asignado'
    )

    class Meta:
        db_table = 'usr_userprofile'
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'

    def __str__(self):
        pvd_name = self.pvd_asignado.pvd_nombre if self.pvd_asignado else 'Sin PVD'
        return f"{self.user.username} - {pvd_name}"


# ==============================================================================
# MODELOS DE SALAS
# ==============================================================================

class Sala(models.Model):
    """
    Modelo para gestionar las salas/espacios físicos dentro de cada Punto Vive Digital.
    Permite administrar los diferentes espacios de trabajo asignados a cada PVD.
    """
    ESTADO_CHOICES = [
        ('A', 'Activo'),
        ('I', 'Inactivo'),
        ('M', 'En mantenimiento'),
    ]

    sala_cdgo = models.AutoField(primary_key=True, db_column='SALA_CDGO')
    pvd_cdgo = models.ForeignKey(
        'PuntoViveDigital',
        models.CASCADE,
        db_column='PVD_CDGO',
        verbose_name='Punto Vive Digital'
    )
    sala_nombre = models.CharField(
        max_length=128,
        db_column='SALA_NOMBRE',
        verbose_name='Nombre de la Sala'
    )
    sala_descr = models.TextField(
        db_column='SALA_DESCR',
        null=True,
        blank=True,
        verbose_name='Descripción'
    )
    sala_capacidad = models.IntegerField(
        db_column='SALA_CAPACIDAD',
        null=True,
        blank=True,
        verbose_name='Capacidad'
    )
    sala_estdo = models.CharField(
        max_length=1,
        db_column='SALA_ESTDO',
        default='A',
        choices=ESTADO_CHOICES,
        verbose_name='Estado'
    )
    sala_fch_crea = models.DateField(
        auto_now_add=True,
        db_column='SALA_FCH_CREA',
        null=True,
        verbose_name='Fecha de creación'
    )

    class Meta:
        db_table = 'sala_sala'
        ordering = ['pvd_cdgo', 'sala_nombre']
        verbose_name = 'Sala'
        verbose_name_plural = 'Salas'
        unique_together = [['pvd_cdgo', 'sala_nombre']]

    def __str__(self):
        return f"{self.sala_nombre} - {self.pvd_cdgo.pvd_nombre}"
