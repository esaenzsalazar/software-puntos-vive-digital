"""
Contexto global para navegación según permisos (contrato PVD / roles).
Proporciona variables de contexto disponibles en todos los templates.
"""
from .models import PuntoViveDigital, Ciudadano
from django.urls import reverse, NoReverseMatch
from django.core.cache import cache

# (label, parent_label, parent_url_name)
_BREADCRUMB_MAP = {
    'panel_control':         ('Panel de control',      None,                    None),
    'seleccionar_pvd_view':  ('Seleccionar PVD',       None,                    None),
    'perfil_usuario':        ('Mi Perfil',             'Panel',                 'panel_control'),
    'ayuda':                 ('Ayuda',                 'Panel',                 'panel_control'),
    'log_auditoria':         ('Log de Auditoría',      'Panel',                 'panel_control'),
    # Ciudadanos
    'consultar_ciudadanos':  ('Ciudadanos',            'Panel',                 'panel_control'),
    'registrar_ciudadano':   ('Registrar Ciudadano',   'Ciudadanos',            'consultar_ciudadanos'),
    'editar_ciudadano':      ('Editar Ciudadano',      'Ciudadanos',            'consultar_ciudadanos'),
    'historial_ciudadano':   ('Historial',             'Ciudadanos',            'consultar_ciudadanos'),
    'ciudadanos_pendientes': ('Pendientes',            'Ciudadanos',            'consultar_ciudadanos'),
    # Atenciones
    'lista_atenciones':              ('Atenciones',           'Panel',       'panel_control'),
    'detalle_atencion':              ('Detalle de Atención',  'Atenciones',  'lista_atenciones'),
    'editar_atencion':               ('Editar Atención',      'Atenciones',  'lista_atenciones'),
    'registrar_atencion':            ('Nueva Atención',       'Atenciones',  'lista_atenciones'),
    'registrar_servicio':            ('Registrar Servicio',   'Atenciones',  'lista_atenciones'),
    'registrar_servicio_atencion':   ('Registrar Servicio',   'Atenciones',  'lista_atenciones'),
    'gestionar_servicios_pvd':       ('Historial de Servicios', 'Panel',     'panel_control'),
    'registrar_satisfaccion':        ('Satisfacción',         'Panel',       'panel_control'),
    'registrar_satisfaccion_atencion':('Satisfacción',        'Atenciones',  'lista_atenciones'),
    # Recursos
    'registrar_recurso':        ('Recursos',              'Panel',                    'panel_control'),
    'crear_recurso':            ('Nuevo Recurso',         'Recursos',                 'registrar_recurso'),
    'editar_recurso':           ('Editar Recurso',        'Recursos',                 'registrar_recurso'),
    'registrar_prestamo':       ('Nuevo Préstamo',        'Recursos',                 'registrar_recurso'),
    'editar_prestamo':          ('Editar Préstamo',       'Recursos',                 'registrar_recurso'),
    'lista_prestamos_global':   ('Visualizar Préstamos',  'Panel',                    'panel_control'),
    # Reportes
    'reportes':              ('Reportes',              'Panel',                 'panel_control'),
    # PVDs
    'lista_pvd':             ('Puntos Vive Digital',   'Panel',                 'panel_control'),
    'crear_pvd':             ('Nuevo PVD',             'Puntos Vive Digital',   'lista_pvd'),
    'editar_pvd':            ('Editar PVD',            'Puntos Vive Digital',   'lista_pvd'),
    # Salas
    'lista_salas':           ('Salas / Habilitaciones', 'Panel',                'panel_control'),
    'crear_sala':            ('Nueva Sala',             'Salas / Habilitaciones', 'lista_salas'),
    'editar_sala':           ('Editar Sala',            'Salas / Habilitaciones', 'lista_salas'),
    'lista_habilitaciones':  ('Habilitaciones',         'Salas / Habilitaciones', 'lista_salas'),
    'crear_habilitacion':    ('Nueva Habilitación',     'Salas / Habilitaciones', 'lista_salas'),
    'editar_habilitacion':   ('Editar Habilitación',    'Salas / Habilitaciones', 'lista_salas'),
    'agenda_sala':           ('Agenda de Sala',         'Salas / Habilitaciones', 'lista_salas'),
    # Permisos
    'lista_permisos_roles':  ('Permisos',              'Panel',                 'panel_control'),
    'editar_permiso':        ('Editar Permiso',        'Permisos',              'lista_permisos_roles'),
    'permisos_usuario':      ('Permisos de Usuario',   'Permisos',              'lista_permisos_roles'),
    # Cursos
    'lista_cursos':          ('Cursos',                'Panel',                 'panel_control'),
    'crear_curso':           ('Nuevo Curso',           'Cursos',                'lista_cursos'),
    'detalle_curso':         ('Detalle Curso',         'Cursos',                'lista_cursos'),
    'editar_curso':          ('Editar Curso',          'Cursos',                'lista_cursos'),
    'crear_sesion_curso':    ('Nueva Sesión',          'Cursos',                'lista_cursos'),
    'inscribir_ciudadano':   ('Inscripción',           'Cursos',                'lista_cursos'),
    'marcar_asistencia':     ('Asistencia',            'Cursos',                'lista_cursos'),
    # Mantenimientos
    'lista_mantenimientos':  ('Mantenimientos',        'Panel',                 'panel_control'),
    'crear_mantenimiento':   ('Nuevo Mantenimiento',   'Mantenimientos',        'lista_mantenimientos'),
    'editar_mantenimiento':  ('Editar Mantenimiento',  'Mantenimientos',        'lista_mantenimientos'),
    # Evidencias
    'lista_evidencias':      ('Evidencias',            'Panel',                 'panel_control'),
    'crear_evidencia':       ('Nueva Evidencia',       'Evidencias',            'lista_evidencias'),
    'editar_evidencia':      ('Editar Evidencia',      'Evidencias',            'lista_evidencias'),
    # Usuarios y roles
    'gestionar_roles':         ('Gestión de Roles',      'Panel',               'panel_control'),
    'crear_usuario_sistema':   ('Usuarios del Sistema',  'Panel',               'panel_control'),
    'crear_admin_tic':         ('Nuevo Admin TIC',       'Panel',               'panel_control'),
    'crear_admin_pvd':         ('Nuevo Admin PVD',       'Panel',               'panel_control'),
    'accesos_temporales':      ('Accesos Temporales',    'Panel',               'panel_control'),
}

# Acciones que requieren PVD activo en sesión para mostrarse en el topbar
_TOPBAR_REQUIERE_PVD = {
    'registrar_atencion', 'registrar_ciudadano', 'crear_recurso',
    'registrar_prestamo', 'crear_sala', 'crear_habilitacion', 'crear_curso',
}

# Acciones que solo se muestran para superusuario o Admin TIC
_TOPBAR_SOLO_SUPERTIC = {'crear_sala'}

# Acciones que solo se muestran para Admin PVD (no super, no TIC)
_TOPBAR_SOLO_ADMINPVD = {'crear_mantenimiento', 'crear_evidencia'}

_TOPBAR_MODULO_REQUERIDO = {
    'registrar_atencion':  {'atencion_ciudadana', 'atenciones', 'ciudadanos'},
    'registrar_ciudadano': {'atencion_ciudadana', 'ciudadanos'},
    'crear_recurso':       {'recursos_salas', 'recursos'},
    'registrar_prestamo':  {'recursos_salas', 'prestamos'},
    'reportes':            {'reportes'},
    'crear_sala':          {'recursos_salas', 'salas'},
    'crear_habilitacion':  {'recursos_salas', 'habilitaciones'},
    'crear_curso':         {'cursos_talleres', 'cursos'},
    'crear_mantenimiento': {'mantenimiento'},
}

_TOPBAR_ACTIONS = {
    'panel_control':         [('↓ Exportar', 'reportes', 'btn-secondary'), ('+ Nueva atención', 'registrar_atencion', '')],
    'consultar_ciudadanos':  [('+ Registrar ciudadano', 'registrar_ciudadano', '')],
    'ciudadanos_pendientes': [('← Ciudadanos', '__back__', 'btn-secondary')],
    'registrar_ciudadano':   [('← Cancelar', '__back__', 'btn-secondary')],
    'editar_ciudadano':      [('← Cancelar', '__back__', 'btn-secondary')],
    'historial_ciudadano':   [('← Volver', '__back__', 'btn-secondary'), ('+ Nueva atención', 'registrar_atencion', '')],
    'lista_atenciones':      [('+ Nueva atención', 'registrar_atencion', '')],
    'detalle_atencion':      [('← Volver', '__back__', 'btn-secondary')],
    'editar_atencion':       [('← Cancelar', '__back__', 'btn-secondary')],
    'gestionar_servicios_pvd': [],
    'registrar_atencion':    [('← Cancelar', '__back__', 'btn-secondary')],
    'registrar_servicio':    [('← Cancelar', '__back__', 'btn-secondary')],
    'registrar_servicio_atencion': [('← Cancelar', '__back__', 'btn-secondary')],
    'registrar_satisfaccion':[('← Cancelar', '__back__', 'btn-secondary')],
    'registrar_satisfaccion_atencion': [('← Cancelar', '__back__', 'btn-secondary')],
    'registrar_recurso':     [('+ Préstamo', 'registrar_prestamo', 'btn-secondary'), ('+ Nuevo recurso', 'crear_recurso', '')],
    'crear_recurso':         [('← Cancelar', '__back__', 'btn-secondary')],
    'registrar_prestamo':    [('← Cancelar', '__back__', 'btn-secondary')],
    'editar_prestamo':       [('← Cancelar', '__back__', 'btn-secondary')],
    'lista_pvd':             [('+ Nuevo PVD', 'crear_pvd', '')],
    'crear_pvd':             [('← Cancelar', '__back__', 'btn-secondary')],
    'editar_pvd':            [('← Cancelar', '__back__', 'btn-secondary')],
    'lista_salas':           [('+ Nueva sala', 'crear_sala', '')],
    'crear_sala':            [('← Cancelar', '__back__', 'btn-secondary')],
    'editar_sala':           [('← Cancelar', '__back__', 'btn-secondary')],
    'lista_habilitaciones':  [],
    'crear_habilitacion':    [('← Cancelar', '__back__', 'btn-secondary')],
    'editar_habilitacion':   [('← Cancelar', '__back__', 'btn-secondary')],
    'editar_permiso':        [('← Cancelar', '__back__', 'btn-secondary')],
    'permisos_usuario':      [('← Volver', '__back__', 'btn-secondary')],
    'accesos_temporales':    [('← Volver', '__back__', 'btn-secondary')],
    'log_auditoria':         [],
    'editar_recurso':        [('← Cancelar', '__back__', 'btn-secondary')],
    'editar_satisfaccion':   [('← Cancelar', '__back__', 'btn-secondary')],
    'editar_evidencia':      [('← Cancelar', '__back__', 'btn-secondary')],
    'agenda_sala':           [('← Volver', '__back__', 'btn-secondary')],
    'lista_cursos':          [('+ Nuevo curso', 'crear_curso', '')],
    'crear_curso':           [('← Cancelar', '__back__', 'btn-secondary')],
    'editar_curso':          [('← Cancelar', '__back__', 'btn-secondary')],
    'detalle_curso':         [('← Volver', '__back__', 'btn-secondary')],
    'crear_sesion_curso':    [('← Cancelar', '__back__', 'btn-secondary')],
    'inscribir_ciudadano':   [('← Cancelar', '__back__', 'btn-secondary')],
    'marcar_asistencia':     [('← Cancelar', '__back__', 'btn-secondary')],
    'lista_mantenimientos':     [('+ Nuevo mantenimiento', 'crear_mantenimiento', '')],
    'crear_mantenimiento':      [('← Cancelar', '__back__', 'btn-secondary')],
    'editar_mantenimiento':     [('← Cancelar', '__back__', 'btn-secondary')],
    'lista_evidencias':         [('+ Nueva evidencia', 'crear_evidencia', '')],
    'crear_evidencia':          [('← Cancelar', '__back__', 'btn-secondary')],
    'lista_prestamos_global':   [],
    'perfil_usuario':           [('← Volver', '__back__', 'btn-secondary')],
    'crear_usuario_sistema':    [('← Cancelar', '__back__', 'btn-secondary')],
    'crear_admin_tic':          [('← Cancelar', '__back__', 'btn-secondary')],
    'crear_admin_pvd':          [('← Cancelar', '__back__', 'btn-secondary')],
}


def pvd_navigation(request):
    """
    Context processor para proporcionar variables de navegación según el rol del usuario.
    """
    rm = getattr(request, 'resolver_match', None)
    url_name = getattr(rm, 'url_name', '') or ''
    bc = _BREADCRUMB_MAP.get(url_name)
    if bc:
        bc_label, bc_parent_label, bc_parent_url_name = bc
    else:
        bc_label = url_name.replace('_', ' ').title() if url_name else ''
        bc_parent_label = 'Panel'
        bc_parent_url_name = 'panel_control'

    try:
        bc_parent_url = reverse(f'modulo_puntos:{bc_parent_url_name}') if bc_parent_url_name else None
    except NoReverseMatch:
        bc_parent_url = None

    ctx = {
        'nav_pvd': False,
        'nav_tic': False,
        'nav_super': False,
        'current_url_name': url_name,
        'pvd_activo': None,
        'pvds_disponibles': [],
        'bc_label': bc_label,
        'bc_parent_label': bc_parent_label,
        'bc_parent_url': bc_parent_url,
        'topbar_actions': [],
        'restringir_modulos': False,
        'modulos_pvd_activo': set(),
    }

    u = request.user
    if not u.is_authenticated:
        return ctx

    ctx['nav_super'] = u.is_superuser
    ctx['nav_tic'] = u.is_superuser or u.groups.filter(name='Administrador TIC').exists()

    es_admin_pvd = u.groups.filter(name='Administrador PVD').exists()
    ctx['es_admin_pvd_only'] = es_admin_pvd and not u.is_superuser and not ctx['nav_tic']
    ctx['es_admin_tic_only'] = u.groups.filter(name='Administrador TIC').exists() and not u.is_superuser
    ctx['es_superusuario'] = u.is_superuser

    ctx['nav_pvd'] = (
        u.is_superuser
        or ctx['nav_tic']
        or es_admin_pvd
    )

    pvd_id = request.session.get('pvd_activo_id')
    if pvd_id:
        try:
            pvd = PuntoViveDigital.objects.get(pk=pvd_id, estado='A')
            ctx['pvd_activo'] = pvd
        except PuntoViveDigital.DoesNotExist:
            request.session.pop('pvd_activo_id', None)

    if ctx['pvd_activo'] and bc_parent_label == 'Panel':
        ctx['bc_parent_label'] = ctx['pvd_activo'].nombre

    _pvds_key = 'pvds_disponibles_activos'
    pvds_cache = cache.get(_pvds_key)
    if pvds_cache is None:
        pvds_cache = list(PuntoViveDigital.objects.filter(estado='A').order_by('nombre'))
        cache.set(_pvds_key, pvds_cache, 60)
    ctx['pvds_disponibles'] = pvds_cache

    raw_actions = _TOPBAR_ACTIONS.get(url_name, [])
    resolved = []
    modulos_activos = ctx.get('modulos_pvd_activo', set())
    es_nav_tic   = ctx.get('nav_tic', False)
    es_admin_pvd = ctx.get('es_admin_pvd_only', False)
    tiene_pvd    = ctx['pvd_activo'] is not None

    for label, target, css in raw_actions:
        if target == '__back__':
            action_url = bc_parent_url
        else:
            try:
                action_url = reverse(f'modulo_puntos:{target}')
            except NoReverseMatch:
                action_url = None
        if not action_url:
            continue
        # Filtro por módulos habilitados
        if ctx.get('restringir_modulos') and target in _TOPBAR_MODULO_REQUERIDO:
            if not _TOPBAR_MODULO_REQUERIDO[target].intersection(modulos_activos):
                continue
        # Filtro: requiere PVD activo en sesión
        if target in _TOPBAR_REQUIERE_PVD and not tiene_pvd:
            continue
        # Filtro: solo superusuario o Admin TIC
        if target in _TOPBAR_SOLO_SUPERTIC and not es_nav_tic:
            continue
        # Filtro: solo Admin PVD (no super, no TIC)
        if target in _TOPBAR_SOLO_ADMINPVD and not es_admin_pvd:
            continue
        resolved.append({'label': label, 'url': action_url, 'css': css})
    ctx['topbar_actions'] = resolved

    if u.is_authenticated and ctx['nav_pvd']:
        _pend_key = 'ciudadanos_pendientes_count'
        pend = cache.get(_pend_key)
        if pend is None:
            pend = Ciudadano.objects.filter(estado='P').count()
            cache.set(_pend_key, pend, 30)
        ctx['pendientes_count'] = pend
    else:
        ctx['pendientes_count'] = 0

    return ctx
