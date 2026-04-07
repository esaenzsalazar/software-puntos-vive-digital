from django.db import models


class UsuarioSistema(models.Model):
    usu_cdgo = models.AutoField(primary_key=True, db_column='USU_CDGO')
    usu_nombre = models.CharField(max_length=64, db_column='USU_NOMBRE', null=True, blank=True)
    usu_passwd = models.CharField(max_length=256, db_column='USU_PASSWD', null=True, blank=True)
    usu_estdo = models.CharField(max_length=1, db_column='USU_ESTDO', null=True, blank=True)

    class Meta:
        db_table = 'usu_usuariosistema'

    def __str__(self):
        return f"{self.usu_nombre} ({self.usu_estdo})"


class ListaValor(models.Model):
    lva_cdgo = models.IntegerField(primary_key=True, db_column='LVA_CDGO')
    lva_nombre = models.CharField(max_length=64, db_column='LVA_NOMBRE')
    lva_descr = models.CharField(max_length=256, db_column='LVA_DESCR', null=True, blank=True)
    lva_estdo = models.CharField(max_length=1, db_column='LVA_ESTDO')

    class Meta:
        db_table = 'lva_listavalor'

    def __str__(self):
        return self.lva_nombre


class Satisfaccion(models.Model):
    sat_cdgo = models.AutoField(primary_key=True, db_column='SAT_CDGO')
    atn_cdgo = models.ForeignKey(
        'Atencion',
        models.DO_NOTHING,
        db_column='ATN_CDGO',
        null=True,
        blank=True
    )
    sat_calif = models.IntegerField(db_column='SAT_CALIF')
    sat_cmntrio = models.CharField(max_length=512, db_column='SAT_CMNTRIO', null=True, blank=True)
    sat_fecha = models.DateTimeField(db_column='SAT_FECHA')

    class Meta:
        db_table = 'sat_satisfaccion'

    def __str__(self):
        return f"Calificación: {self.sat_calif} - {self.sat_fecha.strftime('%Y-%m-%d')}"


class PrestamoRecurso(models.Model):
    prs_cdgo = models.AutoField(primary_key=True, db_column='PRS_CDGO')
    rec_cdgo = models.ForeignKey(
        'Recurso',
        models.DO_NOTHING,
        db_column='REC_CDGO',
        null=True,
        blank=True
    )
    prs_fchent = models.DateTimeField(db_column='PRS_FCHENT')
    prs_fchdev = models.DateTimeField(db_column='PRS_FCHDEV', null=True, blank=True)
    prs_obs = models.CharField(max_length=512, db_column='PRS_OBS', null=True, blank=True)

    class Meta:
        db_table = 'prs_prestamorecurso'

    def __str__(self):
        return f"Préstamo {self.prs_cdgo}"


class Atencion(models.Model):
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
        models.DO_NOTHING,
        db_column='CIU_CDGO',
        null=True,
        blank=True
    )
    opr_cdgo = models.ForeignKey(
        'Operador',
        models.DO_NOTHING,
        db_column='OPR_CDGO',
        null=True,
        blank=True
    )
    prs_cdgo = models.ForeignKey(
        PrestamoRecurso,
        models.DO_NOTHING,
        db_column='PRS_CDGO',
        null=True,
        blank=True
    )
    atn_fecha = models.DateField(db_column='ATN_FECHA')
    atn_hrini = models.TimeField(db_column='ATN_HRINI')
    atn_hrfin = models.TimeField(db_column='ATN_HRFIN', null=True, blank=True)
    atn_estdo = models.CharField(max_length=1, db_column='ATN_ESTDO', default='P', choices=ESTADO_CHOICES)
    atn_obs = models.CharField(max_length=512, db_column='ATN_OBS', null=True, blank=True)

    class Meta:
        db_table = 'atn_atencion'

    def __str__(self):
        return f"Atención {self.atn_cdgo} - {self.atn_fecha}"


class Operador(models.Model):
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
    usu_cdgo = models.ForeignKey(UsuarioSistema, models.DO_NOTHING, db_column='USU_CDGO', null=True, blank=True)
    opr_tpodoc = models.CharField(max_length=32, db_column='OPR_TPODOC', null=True, blank=True)
    opr_numdoc = models.CharField(max_length=32, db_column='OPR_NUMDOC', null=True, blank=True)
    opr_nmbres = models.CharField(max_length=128, db_column='OPR_NMBRES', null=True, blank=True)
    opr_aplldos = models.CharField(max_length=128, db_column='OPR_APLLDOS', null=True, blank=True)
    opr_email = models.CharField(max_length=128, db_column='OPR_EMAIL', null=True, blank=True)
    opr_tlfno = models.CharField(max_length=32, db_column='OPR_TLFNO', null=True, blank=True)
    opr_estdo = models.CharField(max_length=1, db_column='OPR_ESTDO', null=True, blank=True, choices=ESTADO_CHOICES)

    class Meta:
        db_table = 'opr_operador'

    def __str__(self):
        return f"{self.opr_nmbres} {self.opr_aplldos}"


class Ciudadano(models.Model):
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
    ciu_tpodoc = models.CharField(max_length=32, db_column='CIU_TPODOC', null=True, blank=True)
    ciu_numdoc = models.CharField(max_length=32, db_column='CIU_NUMDOC', null=True, blank=True)
    ciu_nmbres = models.CharField(max_length=128, db_column='CIU_NMBRES', null=True, blank=True)
    ciu_aplldos = models.CharField(max_length=128, db_column='CIU_APLLDOS', null=True, blank=True)
    ciu_fchancm = models.DateField(db_column='CIU_FCHANCM', null=True, blank=True)
    ciu_genro = models.CharField(max_length=32, db_column='CIU_GENRO', choices=GENERO_CHOICES, null=True, blank=True)
    ciu_etnia = models.CharField(max_length=64, db_column='CIU_ETNIA', null=True, blank=True)
    ciu_nvleduc = models.CharField(max_length=64, db_column='CIU_NVLEDUC', null=True, blank=True)
    ciu_ocpcion = models.CharField(max_length=64, db_column='CIU_OCPCION', null=True, blank=True)
    ciu_discapacidad = models.BooleanField(db_column='CIU_DISCAPACIDAD', default=False)
    ciu_desc_discapacidad = models.CharField(max_length=128, db_column='CIU_DESC_DISCAPACIDAD', null=True, blank=True)
    
    # NUEVOS CAMPOS DE UBICACIÓN
    ciu_dircion = models.CharField(max_length=128, db_column='CIU_DIRCION', null=True, blank=True)
    ciu_barrio = models.CharField(max_length=64, db_column='CIU_BARRIO', null=True, blank=True)
    ciu_zrural = models.CharField(max_length=64, db_column='CIU_ZRURAL', null=True, blank=True)
    
    ciu_estrato = models.IntegerField(db_column='CIU_ESTRATO', default=1)
    ciu_estdo = models.CharField(max_length=1, db_column='CIU_ESTDO', default='A', choices=ESTADO_CHOICES)
    ciu_email = models.CharField(max_length=128, db_column='CIU_EMAIL', default='', blank=True)
    ciu_tlfno = models.CharField(max_length=32, db_column='CIU_TLFNO', null=True, blank=True)

    class Meta:
        db_table = 'ciu_ciudadano'

    def __str__(self):
        return f"{self.ciu_nmbres} {self.ciu_aplldos} ({self.ciu_numdoc})"


class Recurso(models.Model):
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
    rec_tipo = models.CharField(max_length=64, db_column='REC_TIPO')
    rec_estdo = models.CharField(max_length=1, db_column='REC_ESTDO', choices=ESTADO_CHOICES)

    class Meta:
        db_table = 'rec_recurso'

    def __str__(self):
        return f"Recurso: {self.rec_tipo}"


class Servicio(models.Model):
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
        Atencion,
        models.DO_NOTHING,
        db_column='ATN_CDGO',
        null=True,
        blank=True
    )
    srv_nombre = models.CharField(max_length=128, db_column='SRV_NOMBRE')
    srv_descr = models.CharField(max_length=512, db_column='SRV_DESCR', null=True, blank=True)
    srv_tipo = models.CharField(max_length=64, db_column='SRV_TIPO')
    srv_reqeqp = models.CharField(max_length=1, db_column='SRV_REQEQP', default='N', choices=REQUIERE_EQUIPO_CHOICES)
    srv_estdo = models.CharField(max_length=1, db_column='SRV_ESTDO', default='A', choices=ESTADO_CHOICES)

    class Meta:
        db_table = 'srv_servicio'

    def __str__(self):
        return self.srv_nombre


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
    pvd_nombre = models.CharField(max_length=128, db_column='PVD_NOMBRE', null=True,
                                  verbose_name='Nombre del Punto Vive Digital')
    pvd_dircion = models.CharField(max_length=128, db_column='PVD_DIRCION', null=True,
                                   verbose_name='Dirección')
    pvd_barrio = models.CharField(max_length=64, db_column='PVD_BARRIO', null=True,
                                  verbose_name='Barrio/Vereda')
    pvd_telefono = models.CharField(max_length=32, db_column='PVD_TELEFONO', null=True, blank=True,
                                    verbose_name='Teléfono')
    pvd_correo = models.CharField(max_length=128, db_column='PVD_CORREO', null=True, blank=True,
                                  verbose_name='Correo electrónico')
    pvd_estdo = models.CharField(max_length=1, db_column='PVD_ESTDO', default='A',
                                 choices=ESTADO_CHOICES, verbose_name='Estado')
    pvd_fch_crea = models.DateField(auto_now_add=True, db_column='PVD_FCH_CREA', null=True,
                                    verbose_name='Fecha de creación')
    pvd_descripcion = models.TextField(db_column='PVD_DESCRIPCION', null=True, blank=True,
                                       verbose_name='Descripción/Notas')

    class Meta:
        db_table = 'pvd_puntovivedigital'
        ordering = ['pvd_nombre']
        verbose_name = 'Punto Vive Digital'
        verbose_name_plural = 'Puntos Vive Digital'

    def __str__(self):
        return self.pvd_nombre

    def get_total_atenciones(self):
        return self.atencion_set.count()

    def get_total_ciudadanos(self):
        return self.ciudadano_set.count()


class AuditoriaAccion(models.Model):
    """Modelo para registrar auditoría de acciones del sistema (contrato CD-224-2026)."""
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
    usuario = models.CharField(max_length=128, db_column='AUD_USUARIO', null=True, blank=True)
    accion = models.CharField(max_length=32, db_column='AUD_ACCION', choices=TIPO_ACCION)
    modelo_afectado = models.CharField(max_length=128, db_column='AUD_MODELO', null=True, blank=True)
    objeto_id = models.CharField(max_length=128, db_column='AUD_OBJETO_ID', null=True, blank=True)
    descripcion = models.TextField(db_column='AUD_DESCRIPCION', null=True, blank=True)
    ip_address = models.CharField(max_length=45, db_column='AUD_IP', null=True, blank=True)
    fecha_accion = models.DateTimeField(auto_now_add=True, db_column='AUD_FECHA')

    class Meta:
        db_table = 'aud_auditoria_accion'
        ordering = ['-fecha_accion']
        verbose_name = 'Registro de auditoría'
        verbose_name_plural = 'Registros de auditoría'

    def __str__(self):
        return f"[{self.get_accion_display()}] {self.usuario} - {self.modelo_afectado} ({self.fecha_accion.strftime('%Y-%m-%d %H:%M')})"


class UserProfile(models.Model):
    """
    Perfil de usuario para almacenar la relación con un PVD.
    Permite que los Admin PVD tengan asignado su edificio específico.
    """
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='pvd_profile')
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