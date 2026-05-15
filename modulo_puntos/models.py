"""
Models for Puntos Vive Digital system.
Contract CD-224-2026 - Alcaldía de Bugalagrande
"""
from django.db import models



class PuntoViveDigital(models.Model):
    ESTADO_CHOICES = [
        ('A', 'Activo'),
        ('I', 'Inactivo'),
        ('M', 'En mantenimiento'),
    ]

    nombre = models.CharField(max_length=128, null=True, blank=True, verbose_name='Nombre del Punto Vive Digital')
    direccion = models.CharField(max_length=128, null=True, blank=True, verbose_name='Dirección')
    barrio = models.CharField(max_length=64, null=True, blank=True, verbose_name='Barrio/Vereda')
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
    codigo = models.CharField(
        max_length=64, null=True, blank=True, unique=True,
        verbose_name='Código del recurso',
        help_text='Identificador único del equipo (ej: LAP-001). Opcional.'
    )
    estado = models.CharField(max_length=1, choices=ESTADO_CHOICES, verbose_name='Estado')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_recursos'
        verbose_name = 'Recurso'
        verbose_name_plural = 'Recursos'

    def __str__(self):
        if self.codigo:
            return f"{self.tipo} [{self.codigo}]"
        return self.tipo


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
        'auth.User', models.SET_NULL,
        null=True, blank=True,
        related_name='atenciones_registradas',
        verbose_name='Registrado por'
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


class ModuloHabilitado(models.Model):
    MODULOS_DISPONIBLES = [
        ('atencion_ciudadana', 'Atención ciudadana'),
        ('recursos_salas', 'Recursos y Salas'),
        ('cursos_talleres', 'Cursos y Talleres'),
        ('mantenimiento', 'Mantenimiento de equipos'),
        ('reportes', 'Reportes y exportaciones'),
    ]

    punto_vive_digital = models.ForeignKey(
        'PuntoViveDigital', on_delete=models.CASCADE,
        related_name='modulos_habilitados',
        verbose_name='Punto Vive Digital'
    )
    modulo = models.CharField(max_length=32, choices=MODULOS_DISPONIBLES, verbose_name='Módulo')
    habilitado = models.BooleanField(default=True, verbose_name='Habilitado')
    fecha_habilitacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de habilitación')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_modulos_habilitados'
        unique_together = [('punto_vive_digital', 'modulo')]
        verbose_name = 'Módulo Habilitado'
        verbose_name_plural = 'Módulos Habilitados'

    def __str__(self):
        return f"{self.get_modulo_display()} — {self.punto_vive_digital.nombre}"


class ServicioPersonalizado(models.Model):
    punto_vive_digital = models.ForeignKey(
        'PuntoViveDigital', on_delete=models.CASCADE,
        related_name='servicios_personalizados',
        verbose_name='Punto Vive Digital'
    )
    nombre = models.CharField(max_length=100, verbose_name='Nombre del servicio')
    icono = models.CharField(max_length=20, default='⚙️', verbose_name='Icono (emoji)')
    descripcion = models.CharField(max_length=255, blank=True, verbose_name='Descripción')
    categoria = models.CharField(max_length=100, default='', blank=True, verbose_name='Categoría')
    color = models.CharField(max_length=7, default='#64748b', blank=True, verbose_name='Color')
    campos = models.JSONField(default=list, verbose_name='Campos adicionales')
    requiere_ciudadano = models.BooleanField(default=False, verbose_name='Requiere ciudadano')
    modulos_sistema = models.JSONField(default=list, verbose_name='Módulos del sistema que activa')
    incluye_extra = models.JSONField(default=list, verbose_name='Ítems adicionales descriptivos')
    habilitado = models.BooleanField(default=True, verbose_name='Habilitado')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_servicios_personalizados'
        ordering = ['nombre']
        verbose_name = 'Servicio Personalizado'
        verbose_name_plural = 'Servicios Personalizados'

    def __str__(self):
        return f"{self.nombre} ({self.punto_vive_digital.nombre})"




# ──────────────────────────────────────────────────────────────────────────────
# COMPOSITOR DE MÓDULOS — Funciones de servicios personalizados
# ──────────────────────────────────────────────────────────────────────────────

class FuncionServicio(models.Model):
    """
    Función creada dentro de un ServicioPersonalizado.
    Combina hasta 6 módulos pluggables: formulario, estados, ciudadano,
    stock (inventario), agenda (citas/turnos) y encuesta automática.
    Cada módulo tiene su propia sección de configuración en JSON.
    """
    servicio = models.ForeignKey(
        'ServicioPersonalizado', on_delete=models.CASCADE,
        related_name='funciones', verbose_name='Servicio'
    )
    nombre      = models.CharField(max_length=200, verbose_name='Nombre de la función')
    descripcion = models.TextField(blank=True, default='', verbose_name='Descripción')

    # ── Módulos activos ───────────────────────────────────────────────────────
    mod_formulario = models.BooleanField(default=False, verbose_name='Módulo: Formulario')
    mod_estados    = models.BooleanField(default=False, verbose_name='Módulo: Estados')
    mod_ciudadano  = models.BooleanField(default=False, verbose_name='Módulo: Ciudadano')
    mod_stock      = models.BooleanField(default=False, verbose_name='Módulo: Inventario')
    mod_agenda     = models.BooleanField(default=False, verbose_name='Módulo: Agenda/Citas')
    mod_encuesta   = models.BooleanField(default=False, verbose_name='Módulo: Encuesta automática')

    # ── Config: formulario ────────────────────────────────────────────────────
    # [{nombre, tipo, requerido, opciones:[], visible_si:{campo,valor}|null}]
    # tipo: texto|textarea|numero|decimal|fecha|hora|email|telefono|booleano|lista|multiselect|calificacion|separador
    campos = models.JSONField(default=list, verbose_name='Campos del formulario')

    # ── Config: estados ───────────────────────────────────────────────────────
    # [{nombre, color, emoji, es_terminal, es_inicial, puede_ir_a:[], requiere_nota}]
    estados = models.JSONField(default=list, verbose_name='Estados del proceso')

    # ── Config: ciudadano ─────────────────────────────────────────────────────
    ciudadano_requerido      = models.BooleanField(default=False, verbose_name='Ciudadano requerido')
    ciudadano_rol_etiqueta   = models.CharField(max_length=50, default='Ciudadano', blank=True,
                                                verbose_name='Etiqueta del rol')
    ciudadano_permite_inline = models.BooleanField(default=False,
                                                   verbose_name='Captura datos inline si no está registrado')
    ciudadano_campos_inline  = models.JSONField(default=list,
                                                verbose_name='Campos extra a capturar inline')

    # ── Config: stock (ítem único legacy + multi-ítem nuevo) ─────────────────
    stock_nombre   = models.CharField(max_length=200, blank=True, default='', verbose_name='Nombre del ítem')
    stock_total    = models.PositiveIntegerField(default=0, verbose_name='Cantidad total')
    stock_unidad   = models.CharField(max_length=50, blank=True, default='unidades', verbose_name='Unidad')
    stock_alerta_en = models.PositiveIntegerField(null=True, blank=True,
                                                  verbose_name='Alerta cuando disponibles ≤')
    # [{nombre, total, unidad, alerta_en}]  — si no vacío, reemplaza los campos legacy
    stock_items    = models.JSONField(default=list, verbose_name='Múltiples ítems de inventario')

    # ── Config: agenda ────────────────────────────────────────────────────────
    # {dias:[0-6], hora_inicio:"HH:MM", hora_fin:"HH:MM", duracion_min:int, max_por_franja:int}
    agenda_config  = models.JSONField(default=dict, verbose_name='Configuración de agenda')

    # ── Config: encuesta automática ───────────────────────────────────────────
    # [{pregunta, tipo: "calificacion"|"texto"}]
    encuesta_config = models.JSONField(default=list, verbose_name='Preguntas de encuesta de cierre')

    activo    = models.BooleanField(default=True, verbose_name='Activo')
    orden     = models.PositiveIntegerField(default=0, verbose_name='Orden')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table  = 'pvd_funciones_servicio'
        ordering  = ['orden', 'nombre']
        verbose_name = 'Función de servicio'
        verbose_name_plural = 'Funciones de servicio'

    def __str__(self):
        return f'{self.servicio.nombre} → {self.nombre}'

    # ── Conteo rápido de registros activos ───────────────────────────────────
    @property
    def registros_activos_count(self):
        return self.registros_funcion.filter(activo=True).count()

    # ── Estado inicial ────────────────────────────────────────────────────────
    @property
    def estado_inicial(self):
        for e in self.estados:
            if e.get('es_inicial'):
                return e['nombre']
        return self.estados[0]['nombre'] if self.estados else ''

    # ── Stock: soporte legacy (1 ítem) y multi-ítem ───────────────────────────
    @property
    def usa_multi_stock(self):
        return bool(self.stock_items)

    @property
    def stock_en_uso(self):
        """Para ítem único legacy."""
        from django.db.models import Sum
        return self.registros_funcion.filter(activo=True).aggregate(
            t=Sum('stock_cantidad'))['t'] or 0

    @property
    def stock_disponible(self):
        return max(0, self.stock_total - self.stock_en_uso)

    @property
    def stock_alerta_activa(self):
        if not self.mod_stock or self.usa_multi_stock:
            return False
        if self.stock_alerta_en is None:
            return False
        return self.stock_disponible <= self.stock_alerta_en

    def stock_item_en_uso(self, nombre_item):
        """Unidades en uso de un ítem específico (multi-stock)."""
        total = 0
        for reg in self.registros_funcion.filter(activo=True):
            sel = reg.stock_seleccion or {}
            total += sel.get(nombre_item, 0)
        return total

    def stock_item_disponible(self, nombre_item):
        item = next((i for i in self.stock_items if i['nombre'] == nombre_item), None)
        if not item:
            return 0
        return max(0, item['total'] - self.stock_item_en_uso(nombre_item))

    # ── Agenda: slots disponibles para una fecha ──────────────────────────────
    def slots_agenda(self, fecha):
        """Retorna lista de (hora_str, ocupados, max) para la fecha dada."""
        import datetime
        cfg = self.agenda_config or {}
        if not cfg:
            return []
        try:
            h_ini  = datetime.time.fromisoformat(cfg['hora_inicio'])
            h_fin  = datetime.time.fromisoformat(cfg['hora_fin'])
            dur    = int(cfg.get('duracion_min', 30))
            maximo = int(cfg.get('max_por_franja', 1))
        except (KeyError, ValueError):
            return []
        slots = []
        actual = datetime.datetime.combine(fecha, h_ini)
        fin    = datetime.datetime.combine(fecha, h_fin)
        while actual < fin:
            hora_str = actual.strftime('%H:%M')
            ocupados = self.registros_funcion.filter(
                activo=True, agenda_fecha=fecha,
                agenda_hora=actual.time()).count()
            slots.append({'hora': hora_str, 'ocupados': ocupados, 'max': maximo,
                          'disponible': ocupados < maximo})
            actual += datetime.timedelta(minutes=dur)
        return slots


class RegistroFuncion(models.Model):
    """Registro/uso de una FuncionServicio creado por un operador."""
    funcion = models.ForeignKey(
        'FuncionServicio', on_delete=models.CASCADE,
        related_name='registros_funcion', verbose_name='Función'
    )
    ciudadano = models.ForeignKey(
        'Ciudadano', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Ciudadano'
    )
    nombre_persona = models.CharField(
        max_length=200, blank=True, default='',
        verbose_name='Nombre (si no es ciudadano registrado)'
    )
    estado_actual = models.CharField(
        max_length=100, blank=True, default='', verbose_name='Estado actual'
    )
    datos          = models.JSONField(default=dict, verbose_name='Datos del formulario')
    stock_cantidad = models.PositiveIntegerField(default=1, verbose_name='Cantidad (ítem único)')
    # {nombre_item: cantidad} para multi-stock
    stock_seleccion = models.JSONField(default=dict, verbose_name='Ítems tomados (multi-stock)')
    fecha_fin_esperada = models.DateTimeField(null=True, blank=True, verbose_name='Fecha fin esperada')
    fecha_fin_real     = models.DateTimeField(null=True, blank=True, verbose_name='Fecha fin real')
    notas  = models.TextField(blank=True, default='', verbose_name='Notas')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    # Agenda
    agenda_fecha = models.DateField(null=True, blank=True, verbose_name='Fecha de turno')
    agenda_hora  = models.TimeField(null=True, blank=True, verbose_name='Hora de turno')
    # Bitácora de eventos: [{tipo, texto, fecha_iso, usuario}]
    bitacora = models.JSONField(default=list, verbose_name='Bitácora de eventos')
    # Respuestas a la encuesta de satisfacción: {pregunta_texto: respuesta}
    encuesta_respuestas = models.JSONField(default=dict, verbose_name='Respuestas de encuesta')
    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='registros_funcion_creados',
        verbose_name='Creado por'
    )

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table  = 'pvd_registros_funcion'
        ordering  = ['-creado_en']
        verbose_name = 'Registro de función'
        verbose_name_plural = 'Registros de función'

    @property
    def persona_display(self):
        if self.ciudadano:
            n = f"{self.ciudadano.primer_nombre} {self.ciudadano.primer_apellido}".strip()
            return n or self.ciudadano.numero_documento
        return self.nombre_persona or '—'

    def agregar_evento(self, tipo, texto, usuario=None):
        """Añade un evento a la bitácora sin guardar — llama a save() después."""
        from django.utils import timezone
        evento = {
            'tipo':    tipo,
            'texto':   texto,
            'fecha':   timezone.now().isoformat(),
            'usuario': (usuario.get_full_name() or usuario.username) if usuario else 'Sistema',
        }
        if not self.bitacora:
            self.bitacora = []
        self.bitacora.append(evento)

    def __str__(self):
        return f'{self.funcion.nombre} — {self.persona_display}'


class PlantillaFuncion(models.Model):
    """
    Plantilla reutilizable de función creada por Admin TIC o superusuario.
    Cualquier Admin PVD puede instalarla en sus servicios con un clic,
    generando una copia local editable de la función.
    """
    nombre      = models.CharField(max_length=200, verbose_name='Nombre de la plantilla')
    descripcion = models.CharField(max_length=500, blank=True, verbose_name='Descripción')
    icono       = models.CharField(max_length=20, default='📋', verbose_name='Icono (emoji)')
    categoria   = models.CharField(max_length=100, blank=True, default='General',
                                   verbose_name='Categoría')
    # Flags de módulos
    mod_formulario = models.BooleanField(default=False)
    mod_estados    = models.BooleanField(default=False)
    mod_ciudadano  = models.BooleanField(default=False)
    mod_stock      = models.BooleanField(default=False)
    mod_agenda     = models.BooleanField(default=False)
    mod_encuesta   = models.BooleanField(default=False)
    # Configs (misma estructura que FuncionServicio)
    campos                   = models.JSONField(default=list)
    estados                  = models.JSONField(default=list)
    ciudadano_requerido      = models.BooleanField(default=False)
    ciudadano_rol_etiqueta   = models.CharField(max_length=50, default='Ciudadano', blank=True)
    ciudadano_permite_inline = models.BooleanField(default=False)
    ciudadano_campos_inline  = models.JSONField(default=list)
    stock_nombre             = models.CharField(max_length=200, blank=True, default='')
    stock_total              = models.PositiveIntegerField(default=0)
    stock_unidad             = models.CharField(max_length=50, blank=True, default='unidades')
    stock_alerta_en          = models.PositiveIntegerField(null=True, blank=True)
    stock_items              = models.JSONField(default=list)
    agenda_config            = models.JSONField(default=dict)
    encuesta_config          = models.JSONField(default=list)
    # Metadatos
    solo_admin_tic  = models.BooleanField(default=False,
                                          verbose_name='Solo Admin TIC puede instalar')
    instalaciones   = models.PositiveIntegerField(default=0, verbose_name='Veces instalada')
    activa          = models.BooleanField(default=True, verbose_name='Activa en biblioteca')
    creado_por      = models.ForeignKey('auth.User', on_delete=models.SET_NULL,
                                        null=True, blank=True, verbose_name='Creada por')
    creado_en       = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table  = 'pvd_plantillas_funcion'
        ordering  = ['categoria', 'nombre']
        verbose_name = 'Plantilla de función'
        verbose_name_plural = 'Plantillas de funciones'

    def __str__(self):
        return f'[{self.categoria}] {self.nombre}'

    @property
    def modulos_activos(self):
        m = []
        if self.mod_formulario: m.append('📋')
        if self.mod_estados:    m.append('🔄')
        if self.mod_ciudadano:  m.append('👤')
        if self.mod_stock:      m.append('📦')
        if self.mod_agenda:     m.append('📅')
        if self.mod_encuesta:   m.append('⭐')
        return m


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
    ]

    usuario = models.OneToOneField(
        'auth.User', on_delete=models.CASCADE,
        related_name='pvd_profile', verbose_name='Usuario'
    )
    punto_asignado = models.ForeignKey(
        'PuntoViveDigital', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='PVD Asignado'
    )
    pvd_temporal = models.ForeignKey(
        'PuntoViveDigital', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='accesos_temporales',
        verbose_name='PVD Temporal',
    )
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='admin_pvd', verbose_name='Rol del Usuario')

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


# ==============================================================================
# CURSOS / TALLERES
# ==============================================================================

class Curso(models.Model):
    MODALIDAD_CHOICES = [
        ('P', 'Presencial'),
        ('V', 'Virtual'),
        ('H', 'Híbrida'),
    ]
    ESTADO_CHOICES = [
        ('PL', 'Planificado'),
        ('AC', 'En curso'),
        ('FI', 'Finalizado'),
        ('CA', 'Cancelado'),
    ]
    nombre = models.CharField(max_length=200, verbose_name='Nombre del Curso / Taller')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    modalidad = models.CharField(max_length=1, choices=MODALIDAD_CHOICES, default='P', verbose_name='Modalidad')
    poblacion_objetivo = models.CharField(max_length=200, blank=True, null=True, verbose_name='Población Objetivo')
    fecha_inicio = models.DateField(verbose_name='Fecha de Inicio')
    fecha_fin = models.DateField(null=True, blank=True, verbose_name='Fecha de Fin')
    estado = models.CharField(max_length=2, choices=ESTADO_CHOICES, default='PL', verbose_name='Estado')
    punto_vive_digital = models.ForeignKey(
        'PuntoViveDigital', on_delete=models.CASCADE,
        related_name='cursos', verbose_name='Punto Vive Digital'
    )
    registrado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True,
        related_name='cursos_registrados', verbose_name='Registrado por'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_cursos'
        ordering = ['-fecha_inicio']
        verbose_name = 'Curso / Taller'
        verbose_name_plural = 'Cursos / Talleres'

    def __str__(self):
        return self.nombre

    def total_inscritos(self):
        return self.inscripciones.filter(estado__in=['I', 'C']).count()


class SesionCurso(models.Model):
    curso = models.ForeignKey(
        'Curso', on_delete=models.CASCADE,
        related_name='sesiones', verbose_name='Curso'
    )
    numero_sesion = models.PositiveSmallIntegerField(verbose_name='N° Sesión')
    fecha = models.DateField(verbose_name='Fecha')
    hora_inicio = models.TimeField(verbose_name='Hora de Inicio')
    hora_fin = models.TimeField(verbose_name='Hora de Fin')
    tema = models.CharField(max_length=200, verbose_name='Tema')
    contenido = models.TextField(blank=True, null=True, verbose_name='Contenido / Descripción')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_sesiones_curso'
        ordering = ['curso', 'numero_sesion']
        verbose_name = 'Sesión de Curso'
        verbose_name_plural = 'Sesiones de Curso'
        unique_together = [('curso', 'numero_sesion')]

    def __str__(self):
        return f"{self.curso.nombre} – Sesión {self.numero_sesion}: {self.tema}"


class InscripcionCurso(models.Model):
    ESTADO_CHOICES = [
        ('I', 'Inscrito'),
        ('C', 'Completado'),
        ('R', 'Retirado'),
    ]
    curso = models.ForeignKey(
        'Curso', on_delete=models.CASCADE,
        related_name='inscripciones', verbose_name='Curso'
    )
    ciudadano = models.ForeignKey(
        'Ciudadano', on_delete=models.CASCADE,
        related_name='inscripciones_cursos', verbose_name='Ciudadano'
    )
    estado = models.CharField(max_length=1, choices=ESTADO_CHOICES, default='I', verbose_name='Estado')
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    registrado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True,
        related_name='inscripciones_registradas', verbose_name='Registrado por'
    )

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_inscripciones_curso'
        verbose_name = 'Inscripción a Curso'
        verbose_name_plural = 'Inscripciones a Cursos'
        unique_together = [('curso', 'ciudadano')]

    def __str__(self):
        return f"{self.ciudadano} → {self.curso.nombre}"


class AsistenciaSesion(models.Model):
    sesion = models.ForeignKey(
        'SesionCurso', on_delete=models.CASCADE,
        related_name='asistencias', verbose_name='Sesión'
    )
    ciudadano = models.ForeignKey(
        'Ciudadano', on_delete=models.CASCADE,
        related_name='asistencias_sesiones', verbose_name='Ciudadano'
    )
    asistio = models.BooleanField(default=False, verbose_name='Asistió')

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_asistencia_sesion'
        verbose_name = 'Asistencia a Sesión'
        verbose_name_plural = 'Asistencias a Sesiones'
        unique_together = [('sesion', 'ciudadano')]

    def __str__(self):
        return f"{self.ciudadano} – Sesión {self.sesion.numero_sesion} ({'✓' if self.asistio else '✗'})"


# ==============================================================================
# MANTENIMIENTO DE EQUIPOS
# ==============================================================================

class MantenimientoEquipo(models.Model):
    TIPO_CHOICES = [
        ('PRV', 'Preventivo'),
        ('COR', 'Correctivo'),
    ]
    punto_vive_digital = models.ForeignKey(
        'PuntoViveDigital', on_delete=models.CASCADE,
        related_name='mantenimientos', verbose_name='Punto Vive Digital'
    )
    tipo = models.CharField(max_length=3, choices=TIPO_CHOICES, default='PRV', verbose_name='Tipo')
    fecha = models.DateField(verbose_name='Fecha')
    equipos_intervenidos = models.TextField(verbose_name='Equipos Intervenidos')
    descripcion = models.TextField(verbose_name='Descripción del Trabajo Realizado')
    hallazgos = models.TextField(blank=True, null=True, verbose_name='Hallazgos')
    acciones = models.TextField(blank=True, null=True, verbose_name='Acciones / Recomendaciones')
    realizado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True,
        related_name='mantenimientos_realizados', verbose_name='Registrado por'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'modulo_puntos_app'
        db_table = 'pvd_mantenimientos'
        ordering = ['-fecha']
        verbose_name = 'Mantenimiento de Equipo'
        verbose_name_plural = 'Mantenimientos de Equipos'

    def __str__(self):
        return f"{self.get_tipo_display()} – {self.punto_vive_digital.nombre} ({self.fecha})"

