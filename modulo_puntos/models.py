"""
Models for Puntos Vive Digital system.
Contract CD-224-2026 - Alcaldía de Bugalagrande
"""
from django.db import models


class UsuarioSistema(models.Model):
    nombre = models.CharField(max_length=64, null=True, blank=True, verbose_name='Nombre')
    contrasena = models.CharField(max_length=256, null=True, blank=True, verbose_name='Contraseña')
    estado = models.CharField(max_length=1, null=True, blank=True, verbose_name='Estado')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_usuarios_legacy'
        verbose_name = 'Usuario del Sistema'
        verbose_name_plural = 'Usuarios del Sistema'

    def __str__(self):
        return self.nombre or ''


class ListaValor(models.Model):
    nombre = models.CharField(max_length=64, verbose_name='Nombre')
    descripcion = models.CharField(max_length=256, null=True, blank=True, verbose_name='Descripción')
    estado = models.CharField(max_length=1, verbose_name='Estado')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_listas_valor'
        verbose_name = 'Lista de Valor'
        verbose_name_plural = 'Listas de Valor'

    def __str__(self):
        return self.nombre


class PuntoViveDigital(models.Model):
    ESTADO_CHOICES = [
        ('A', 'Activo'),
        ('I', 'Inactivo'),
        ('M', 'En mantenimiento'),
    ]

    nombre = models.CharField(max_length=128, null=True, blank=True, verbose_name='Nombre del Punto Vive Digital')
    direccion = models.CharField(max_length=128, null=True, blank=True, verbose_name='Dirección')
    barrio = models.CharField(max_length=64, null=True, blank=True, verbose_name='Barrio/Vereda')
    telefono = models.CharField(max_length=32, null=True, blank=True, verbose_name='Teléfono')
    correo = models.CharField(max_length=128, null=True, blank=True, verbose_name='Correo electrónico')
    estado = models.CharField(max_length=1, default='A', choices=ESTADO_CHOICES, verbose_name='Estado')
    fecha_creacion = models.DateField(auto_now_add=True, null=True, verbose_name='Fecha de creación')
    descripcion = models.TextField(null=True, blank=True, verbose_name='Descripción/Notas')
    admin_a_cargo = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='pvd_a_cargo',
        verbose_name='Administrador PVD a cargo',
    )

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_puntos'
        ordering = ['nombre']
        verbose_name = 'Punto Vive Digital'
        verbose_name_plural = 'Puntos Vive Digital'

    def __str__(self):
        return self.nombre or ''


class Operador(models.Model):
    ESTADO_CHOICES = [
        ('A', 'Activo'),
        ('I', 'Inactivo'),
    ]

    punto_vive_digital = models.ForeignKey(
        'PuntoViveDigital', models.SET_NULL,
        null=True, blank=True, verbose_name='Punto Vive Digital'
    )
    tipo_documento = models.CharField(max_length=32, null=True, blank=True, verbose_name='Tipo de Documento')
    numero_documento = models.CharField(max_length=32, null=True, blank=True, unique=True, verbose_name='Número de Documento')
    primer_nombre = models.CharField(max_length=64, null=True, blank=True, verbose_name='Primer Nombre')
    segundo_nombre = models.CharField(max_length=64, null=True, blank=True, verbose_name='Segundo Nombre')
    primer_apellido = models.CharField(max_length=64, null=True, blank=True, verbose_name='Primer Apellido')
    segundo_apellido = models.CharField(max_length=64, null=True, blank=True, verbose_name='Segundo Apellido')
    correo = models.CharField(max_length=128, null=True, blank=True, verbose_name='Correo Electrónico')
    telefono = models.CharField(max_length=32, null=True, blank=True, verbose_name='Teléfono')
    estado = models.CharField(max_length=1, null=True, blank=True, choices=ESTADO_CHOICES, verbose_name='Estado')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_operadores'
        verbose_name = 'Operador'
        verbose_name_plural = 'Operadores'

    def get_nombre_completo(self):
        partes = [self.primer_nombre, self.segundo_nombre, self.primer_apellido, self.segundo_apellido]
        return ' '.join(p for p in partes if p) or 'Sin nombre'

    def __str__(self):
        return self.get_nombre_completo()


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

    punto_vive_digital = models.ForeignKey(
        'PuntoViveDigital', models.SET_NULL,
        null=True, blank=True, verbose_name='Punto Vive Digital'
    )
    tipo_documento = models.CharField(max_length=32, null=True, blank=True, verbose_name='Tipo de Documento')
    numero_documento = models.CharField(max_length=32, null=True, blank=True, unique=True, verbose_name='Número de Documento')
    primer_nombre = models.CharField(max_length=64, null=True, blank=True, verbose_name='Primer Nombre')
    segundo_nombre = models.CharField(max_length=64, null=True, blank=True, verbose_name='Segundo Nombre')
    primer_apellido = models.CharField(max_length=64, null=True, blank=True, verbose_name='Primer Apellido')
    segundo_apellido = models.CharField(max_length=64, null=True, blank=True, verbose_name='Segundo Apellido')
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name='Fecha de Nacimiento')
    genero = models.CharField(max_length=32, choices=GENERO_CHOICES, null=True, blank=True, verbose_name='Género')
    etnia = models.CharField(max_length=64, null=True, blank=True, verbose_name='Etnia')
    nivel_educativo = models.CharField(max_length=64, null=True, blank=True, verbose_name='Nivel Educativo')
    ocupacion = models.CharField(max_length=64, null=True, blank=True, verbose_name='Ocupación')
    tiene_discapacidad = models.BooleanField(default=False, verbose_name='Tiene Discapacidad')
    descripcion_discapacidad = models.CharField(max_length=128, null=True, blank=True, verbose_name='Descripción Discapacidad')
    direccion = models.CharField(max_length=128, null=True, blank=True, verbose_name='Dirección')
    barrio = models.CharField(max_length=64, null=True, blank=True, verbose_name='Barrio')
    zona_rural = models.CharField(max_length=64, null=True, blank=True, verbose_name='Zona Rural')
    estrato = models.IntegerField(default=1, verbose_name='Estrato Socioeconómico')
    estado = models.CharField(max_length=1, default='A', choices=ESTADO_CHOICES, verbose_name='Estado')
    correo = models.CharField(max_length=128, default='', blank=True, verbose_name='Correo Electrónico')
    telefono = models.CharField(max_length=32, null=True, blank=True, verbose_name='Teléfono')
    fecha_registro = models.DateTimeField(auto_now_add=True, null=True, verbose_name='Fecha de Registro')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_ciudadanos'
        verbose_name = 'Ciudadano'
        verbose_name_plural = 'Ciudadanos'
        indexes = [
            models.Index(fields=['primer_nombre', 'primer_apellido'], name='idx_ciu_nombres'),
            models.Index(fields=['punto_vive_digital', 'estado'], name='idx_ciu_pvd_estdo'),
            models.Index(fields=['fecha_nacimiento'], name='idx_ciu_fchancm'),
            models.Index(fields=['direccion'], name='idx_ciu_dircion'),
        ]

    def get_nombre_completo(self):
        partes = [self.primer_nombre, self.segundo_nombre, self.primer_apellido, self.segundo_apellido]
        return ' '.join(p for p in partes if p) or 'Sin nombre'

    def __str__(self):
        return f"{self.get_nombre_completo()} ({self.numero_documento})"


class Recurso(models.Model):
    ESTADO_CHOICES = [
        ('A', 'Activo'),
        ('I', 'Inactivo'),
    ]

    punto_vive_digital = models.ForeignKey(
        'PuntoViveDigital', models.SET_NULL,
        null=True, blank=True, verbose_name='Punto Vive Digital'
    )
    tipo = models.CharField(max_length=64, verbose_name='Tipo de Recurso')
    estado = models.CharField(max_length=1, choices=ESTADO_CHOICES, verbose_name='Estado')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_recursos'
        verbose_name = 'Recurso'
        verbose_name_plural = 'Recursos'

    def __str__(self):
        return f"Recurso: {self.tipo}"


class PrestamoRecurso(models.Model):
    recurso = models.ForeignKey(
        'Recurso', models.PROTECT,
        null=True, blank=True, verbose_name='Recurso'
    )
    fecha_entrega = models.DateTimeField(verbose_name='Fecha de Entrega')
    fecha_devolucion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Devolución')
    observaciones = models.CharField(max_length=512, null=True, blank=True, verbose_name='Observaciones')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_prestamos'
        verbose_name = 'Préstamo de Recurso'
        verbose_name_plural = 'Préstamos de Recursos'

    def __str__(self):
        return f"Préstamo #{self.pk}"


class Atencion(models.Model):
    ESTADO_CHOICES = [
        ('P', 'Pendiente'),
        ('F', 'Finalizada'),
        ('C', 'Cancelada'),
    ]

    punto_vive_digital = models.ForeignKey(
        'PuntoViveDigital', models.SET_NULL,
        null=True, blank=True, verbose_name='Punto Vive Digital'
    )
    ciudadano = models.ForeignKey(
        'Ciudadano', models.PROTECT,
        null=True, blank=True, verbose_name='Ciudadano'
    )
    operador = models.ForeignKey(
        'Operador', models.PROTECT,
        null=True, blank=True, verbose_name='Operador'
    )
    prestamo = models.ForeignKey(
        'PrestamoRecurso', models.SET_NULL,
        null=True, blank=True, verbose_name='Préstamo'
    )
    fecha = models.DateField(verbose_name='Fecha de Atención')
    hora_inicio = models.TimeField(verbose_name='Hora de Inicio')
    hora_fin = models.TimeField(null=True, blank=True, verbose_name='Hora de Finalización')
    estado = models.CharField(max_length=1, default='P', choices=ESTADO_CHOICES, verbose_name='Estado')
    observaciones = models.CharField(max_length=512, null=True, blank=True, verbose_name='Observaciones')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_atenciones'
        verbose_name = 'Atención'
        verbose_name_plural = 'Atenciones'
        indexes = [
            models.Index(fields=['punto_vive_digital', 'fecha'], name='idx_atn_pvd_fecha'),
            models.Index(fields=['estado'], name='idx_atn_estdo'),
        ]

    def __str__(self):
        return f"Atención #{self.pk} - {self.fecha} - {self.ciudadano}"


class Servicio(models.Model):
    ESTADO_CHOICES = [
        ('A', 'Activo'),
        ('I', 'Inactivo'),
    ]
    REQUIERE_EQUIPO_CHOICES = [
        ('S', 'Sí'),
        ('N', 'No'),
    ]

    atencion = models.ForeignKey(
        'Atencion', models.PROTECT,
        null=True, blank=True, verbose_name='Atención'
    )
    nombre = models.CharField(max_length=128, verbose_name='Nombre del Servicio')
    descripcion = models.CharField(max_length=512, null=True, blank=True, verbose_name='Descripción')
    tipo = models.CharField(max_length=64, verbose_name='Tipo de Servicio')
    requiere_equipo = models.CharField(max_length=1, default='N', choices=REQUIERE_EQUIPO_CHOICES, verbose_name='¿Requiere Equipo?')
    estado = models.CharField(max_length=1, default='A', choices=ESTADO_CHOICES, verbose_name='Estado')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_servicios'
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'

    def __str__(self):
        return self.nombre


class Satisfaccion(models.Model):
    atencion = models.ForeignKey(
        'Atencion', models.PROTECT,
        null=True, blank=True, verbose_name='Atención'
    )
    calificacion = models.IntegerField(verbose_name='Calificación (1-5)')
    comentario = models.CharField(max_length=512, null=True, blank=True, verbose_name='Comentario')
    fecha = models.DateTimeField(verbose_name='Fecha de Encuesta')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_satisfaccion'
        verbose_name = 'Encuesta de Satisfacción'
        verbose_name_plural = 'Encuestas de Satisfacción'

    def __str__(self):
        return f"Calificación: {self.calificacion}"


class AuditoriaAccion(models.Model):
    TIPO_ACCION = [
        ('CREATE', 'Creación'), ('UPDATE', 'Actualización'), ('DELETE', 'Eliminación'),
        ('LOGIN', 'Inicio de sesión'), ('LOGOUT', 'Cierre de sesión'),
        ('EXPORT', 'Exportación de datos'), ('OTHER', 'Otra acción'),
    ]

    usuario = models.CharField(max_length=128, null=True, blank=True, verbose_name='Usuario')
    accion = models.CharField(max_length=32, choices=TIPO_ACCION, verbose_name='Acción')
    modelo_afectado = models.CharField(max_length=128, null=True, blank=True, verbose_name='Modelo Afectado')
    objeto_id = models.CharField(max_length=128, null=True, blank=True, verbose_name='ID del Objeto')
    descripcion = models.TextField(null=True, blank=True, verbose_name='Descripción')
    direccion_ip = models.CharField(max_length=45, null=True, blank=True, verbose_name='Dirección IP')
    fecha_accion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y Hora')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_auditoria'
        ordering = ['-fecha_accion']
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'

    def __str__(self):
        return f"[{self.get_accion_display()}] {self.usuario} - {self.modelo_afectado}"


class UserProfile(models.Model):
    ROL_CHOICES = [
        ('superadmin', 'Superadministrador'),
        ('admin_tic', 'Administrador TIC'),
        ('admin_pvd', 'Administrador PVD'),
        ('operador', 'Operador'),
    ]

    usuario = models.OneToOneField(
        'auth.User', on_delete=models.CASCADE,
        related_name='pvd_profile', verbose_name='Usuario'
    )
    punto_asignado = models.ForeignKey(
        'PuntoViveDigital', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='PVD Asignado'
    )
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='operador', verbose_name='Rol del Usuario')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_perfiles'
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'

    def __str__(self):
        pvd_name = self.punto_asignado.nombre if self.punto_asignado else 'Sin PVD'
        return f"{self.usuario.username} - {pvd_name}"


class PermisoDefinicion(models.Model):
    codigo = models.CharField(max_length=64, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=128, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    categoria = models.CharField(max_length=64, verbose_name='Categoría')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    delegable_por_ofitic = models.BooleanField(default=False, verbose_name='Delegable por Ofitic')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_permisos_definicion'
        ordering = ['categoria', 'nombre']
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'

    def __str__(self):
        return f"[{self.categoria}] {self.nombre}"


class PermisoRol(models.Model):
    ROL_CHOICES = [
        ('admin_tic', 'Administrador TIC (Ofitic)'),
        ('admin_pvd', 'Administrador PVD'),
        ('operador', 'Operador'),
    ]

    rol = models.CharField(max_length=32, choices=ROL_CHOICES, verbose_name='Rol')
    permiso = models.ForeignKey(
        PermisoDefinicion, on_delete=models.CASCADE,
        related_name='roles', verbose_name='Permiso'
    )
    otorgado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='permisos_rol_otorgados', verbose_name='Otorgado por'
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de asignación')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_permisos_rol'
        unique_together = [('rol', 'permiso')]
        verbose_name = 'Permiso de Rol'
        verbose_name_plural = 'Permisos de Roles'

    def __str__(self):
        return f"{self.get_rol_display()} → {self.permiso.nombre}"


class PermisoUsuario(models.Model):
    usuario = models.ForeignKey(
        'auth.User', on_delete=models.CASCADE,
        related_name='permisos_individuales', verbose_name='Usuario'
    )
    permiso = models.ForeignKey(
        PermisoDefinicion, on_delete=models.CASCADE,
        related_name='usuarios', verbose_name='Permiso'
    )
    concedido = models.BooleanField(default=True, verbose_name='Concedido')
    otorgado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='permisos_usuario_otorgados', verbose_name='Otorgado por'
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de asignación')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_permisos_usuario'
        unique_together = [('usuario', 'permiso')]
        verbose_name = 'Permiso de Usuario'
        verbose_name_plural = 'Permisos de Usuarios'

    def __str__(self):
        estado = 'Concedido' if self.concedido else 'Revocado'
        return f"{self.usuario.username} → {self.permiso.nombre} [{estado}]"


class Sala(models.Model):
    ESTADO_CHOICES = [
        ('A', 'Activo'),
        ('I', 'Inactivo'),
        ('M', 'En mantenimiento'),
    ]

    punto_vive_digital = models.ForeignKey(
        'PuntoViveDigital', models.CASCADE,
        verbose_name='Punto Vive Digital'
    )
    nombre = models.CharField(max_length=128, verbose_name='Nombre de la Sala')
    descripcion = models.TextField(null=True, blank=True, verbose_name='Descripción')
    capacidad = models.IntegerField(null=True, blank=True, verbose_name='Capacidad')
    estado = models.CharField(max_length=1, default='A', choices=ESTADO_CHOICES, verbose_name='Estado')
    fecha_creacion = models.DateField(auto_now_add=True, null=True, verbose_name='Fecha de creación')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_salas'
        ordering = ['punto_vive_digital', 'nombre']
        verbose_name = 'Sala'
        verbose_name_plural = 'Salas'
        unique_together = [['punto_vive_digital', 'nombre']]

    def __str__(self):
        return f"{self.nombre} - {self.punto_vive_digital.nombre}"


class HabilitacionSala(models.Model):
    TIPO_USO_CHOICES = [
        ('NAV', 'Sala de Navegación'),
        ('CAP', 'Capacitación / Formación'),
        ('CONF', 'Conferencia / Reunión'),
        ('TRAM', 'Trámite en Línea'),
        ('EXAM', 'Examen / Evaluación'),
        ('OTRO', 'Otro uso'),
    ]
    ESTADO_CHOICES = [
        ('P', 'Pendiente'),
        ('C', 'Confirmada'),
        ('E', 'En curso'),
        ('F', 'Finalizada'),
        ('X', 'Cancelada'),
    ]

    sala = models.ForeignKey(
        'Sala', on_delete=models.CASCADE,
        related_name='habilitaciones', verbose_name='Sala'
    )
    tipo_uso = models.CharField(max_length=4, choices=TIPO_USO_CHOICES, verbose_name='Tipo de Uso')
    fecha = models.DateField(verbose_name='Fecha')
    hora_inicio = models.TimeField(verbose_name='Hora de Inicio')
    hora_fin = models.TimeField(verbose_name='Hora de Fin')
    solicitante = models.CharField(max_length=128, verbose_name='Solicitante / Grupo')
    proposito = models.TextField(blank=True, null=True, verbose_name='Propósito / Descripción')
    capacidad_requerida = models.IntegerField(null=True, blank=True, verbose_name='Personas Esperadas')
    estado = models.CharField(max_length=1, default='P', choices=ESTADO_CHOICES, verbose_name='Estado')
    registrado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='habilitaciones_registradas', verbose_name='Registrado por'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')
    observaciones = models.TextField(null=True, blank=True, verbose_name='Observaciones')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_habilitaciones_sala'
        ordering = ['fecha', 'hora_inicio']
        verbose_name = 'Habilitación de Sala'
        verbose_name_plural = 'Habilitaciones de Sala'
        indexes = [
            models.Index(fields=['sala', 'fecha'], name='idx_hab_sala_fecha'),
            models.Index(fields=['estado'], name='idx_hab_estado'),
        ]

    def __str__(self):
        return f"{self.sala.nombre} – {self.fecha} {self.hora_inicio.strftime('%H:%M')}"

    def duracion_horas(self):
        from datetime import datetime
        inicio = datetime.combine(self.fecha, self.hora_inicio)
        fin = datetime.combine(self.fecha, self.hora_fin)
        return round((fin - inicio).seconds / 3600, 1)
