"""
Contexto global para navegación según permisos (contrato PVD / roles).
Proporciona variables de contexto disponibles en todos los templates.
"""
from .models import PuntoViveDigital, ModuloHabilitado, ServicioPersonalizado
from django.urls import reverse, NoReverseMatch

_FUNCTION_URL_NAMES = frozenset({
    'gestionar_servicio_custom', 'gestionar_funcion', 'crear_funcion',
    'editar_funcion', 'crear_registro_funcion', 'cambiar_estado_registro_funcion',
    'cerrar_registro_funcion', 'reabrir_registro_funcion', 'agregar_nota_registro',
    'api_slots_agenda', 'eliminar_funcion', 'crear_plantilla_desde_funcion',
    'instalar_plantilla', 'lista_plantillas',
})

# (label, parent_label, parent_url_name)
_BREADCRUMB_MAP = {
    'panel_control':         ('Panel de control',      None,                    None),
    'seleccionar_pvd_view':  ('Seleccionar PVD',       None,                    None),
    'perfil_usuario':        ('Mi Perfil',             'Panel',                 'panel_control'),
    'ayuda':                 ('Ayuda',                 'Panel',                 'panel_control'),
    # Ciudadanos
    'consultar_ciudadanos':  ('Ciudadanos',            'Panel',                 'panel_control'),
    'registrar_ciudadano':   ('Registrar Ciudadano',   'Ciudadanos',            'consultar_ciudadanos'),
    'editar_ciudadano':      ('Editar Ciudadano',      'Ciudadanos',            'consultar_ciudadanos'),
    'historial_ciudadano':   ('Historial',             'Ciudadanos',            'consultar_ciudadanos'),
    'ciudadanos_pendientes': ('Pendientes',            'Ciudadanos',            'consultar_ciudadanos'),
    # Atenciones
    'registrar_atencion':    ('Nueva Atención',        'Panel',                 'panel_control'),
    'registrar_servicio':    ('Registrar Servicio',    'Panel',                 'panel_control'),
    'registrar_satisfaccion':('Satisfacción',          'Panel',                 'panel_control'),
    # Recursos
    'registrar_recurso':     ('Recursos',              'Panel',                 'panel_control'),
    'crear_recurso':         ('Nuevo Recurso',         'Recursos',              'registrar_recurso'),
    'registrar_prestamo':    ('Nuevo Préstamo',        'Recursos',              'registrar_recurso'),
    'editar_prestamo':       ('Editar Préstamo',       'Recursos',              'registrar_recurso'),
    # Reportes
    'reportes':              ('Reportes',              'Panel',                 'panel_control'),
    # PVDs
    'lista_pvd':             ('Puntos Vive Digital',   'Panel',                 'panel_control'),
    'crear_pvd':             ('Nuevo PVD',             'Puntos Vive Digital',   'lista_pvd'),
    'editar_pvd':            ('Editar PVD',            'Puntos Vive Digital',   'lista_pvd'),
    # Salas
    'lista_salas':           ('Salas',                 'Panel',                 'panel_control'),
    'crear_sala':            ('Nueva Sala',            'Salas',                 'lista_salas'),
    'editar_sala':           ('Editar Sala',           'Salas',                 'lista_salas'),
    'lista_habilitaciones':  ('Habilitaciones',        'Panel',                 'panel_control'),
    'crear_habilitacion':    ('Nueva Habilitación',    'Habilitaciones',        'lista_habilitaciones'),
    'editar_habilitacion':   ('Editar Habilitación',   'Habilitaciones',        'lista_habilitaciones'),
    'agenda_sala':           ('Agenda de Sala',        'Salas',                 'lista_salas'),
    # Permisos
    'lista_permisos_roles':  ('Permisos',              'Panel',                 'panel_control'),
    'editar_permiso':        ('Editar Permiso',        'Permisos',              'lista_permisos_roles'),
    'permisos_usuario':      ('Permisos de Usuario',   'Permisos',              'lista_permisos_roles'),
    'permisos_ofitic':       ('Delegar Permisos PVD',  'Permisos',              'lista_permisos_roles'),
    # Cursos
    'lista_cursos':          ('Cursos',                'Panel',                 'panel_control'),
    'crear_curso':           ('Nuevo Curso',           'Cursos',                'lista_cursos'),
    'detalle_curso':         ('Detalle Curso',         'Cursos',                'lista_cursos'),
    'editar_curso':          ('Editar Curso',          'Cursos',                'lista_cursos'),
    'crear_sesion_curso':    ('Nueva Sesión',          'Cursos',                'lista_cursos'),
    'inscribir_ciudadano':   ('Inscripción',           'Cursos',                'lista_cursos'),
    'marcar_asistencia':     ('Asistencia',            'Cursos',                'lista_cursos'),
    # Servicios personalizados y plantillas
    'lista_servicios_custom':         ('Servicios Personalizados', 'Panel',                     'panel_control'),
    'gestionar_servicio_custom':      ('Gestión de servicio',      'Servicios Personalizados',  'lista_servicios_custom'),
    'gestionar_funcion':              ('Gestionar función',        'Servicios Personalizados',  'lista_servicios_custom'),
    'crear_funcion':                  ('Nueva función',            'Servicios Personalizados',  'lista_servicios_custom'),
    'editar_funcion':                 ('Editar función',           'Servicios Personalizados',  'lista_servicios_custom'),
    'lista_plantillas':               ('Plantillas de red',        'Panel',                     'panel_control'),
    'crear_plantilla_desde_funcion':  ('Crear plantilla',         'Plantillas de red',          'lista_plantillas'),
    # Mantenimientos
    'lista_mantenimientos':  ('Mantenimientos',        'Panel',                 'panel_control'),
    'crear_mantenimiento':   ('Nuevo Mantenimiento',   'Mantenimientos',        'lista_mantenimientos'),
    'editar_mantenimiento':  ('Editar Mantenimiento',  'Mantenimientos',        'lista_mantenimientos'),
    # Usuarios y roles
    'gestionar_roles':       ('Gestión de Roles',      'Panel',                 'panel_control'),
    'crear_admin_tic':       ('Nuevo Admin TIC',       'Panel',                 'panel_control'),
    'crear_admin_pvd':       ('Nuevo Admin PVD',       'Panel',                 'panel_control'),
    'accesos_temporales':    ('Accesos Temporales',    'Panel',                 'panel_control'),
}

# target url_name → cualquier código que permite mostrar el botón al Admin PVD
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

# (label, url_name_or_sentinel, css_extra)
# '__back__' = use bc_parent_url resolved at runtime
# '' = base .btn (blue primary), 'btn-secondary' = light secondary
_TOPBAR_ACTIONS = {
    'panel_control':         [('↓ Exportar', 'reportes', 'btn-secondary'), ('+ Nueva atención', 'registrar_atencion', '')],
    'consultar_ciudadanos':  [('+ Registrar ciudadano', 'registrar_ciudadano', '')],
    'registrar_ciudadano':   [('← Cancelar', '__back__', 'btn-secondary')],
    'editar_ciudadano':      [('← Cancelar', '__back__', 'btn-secondary')],
    'historial_ciudadano':   [('← Volver', '__back__', 'btn-secondary')],
    'registrar_atencion':    [('← Cancelar', '__back__', 'btn-secondary')],
    'registrar_servicio':    [('← Cancelar', '__back__', 'btn-secondary')],
    'registrar_satisfaccion':[('← Cancelar', '__back__', 'btn-secondary')],
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
    'lista_habilitaciones':  [('+ Nueva habilitación', 'crear_habilitacion', '')],
    'crear_habilitacion':    [('← Cancelar', '__back__', 'btn-secondary')],
    'editar_habilitacion':   [('← Cancelar', '__back__', 'btn-secondary')],
    'editar_permiso':        [('← Cancelar', '__back__', 'btn-secondary')],
    'permisos_usuario':      [('← Volver', '__back__', 'btn-secondary')],
    'permisos_ofitic':       [('← Volver', '__back__', 'btn-secondary')],
    'lista_cursos':          [('+ Nuevo curso', 'crear_curso', '')],
    'crear_curso':           [('← Cancelar', '__back__', 'btn-secondary')],
    'editar_curso':          [('← Cancelar', '__back__', 'btn-secondary')],
    'detalle_curso':         [('← Volver', '__back__', 'btn-secondary')],
    'crear_sesion_curso':    [('← Cancelar', '__back__', 'btn-secondary')],
    'inscribir_ciudadano':   [('← Cancelar', '__back__', 'btn-secondary')],
    'marcar_asistencia':     [('← Cancelar', '__back__', 'btn-secondary')],
    'lista_mantenimientos':  [('+ Nuevo mantenimiento', 'crear_mantenimiento', '')],
    'crear_mantenimiento':   [('← Cancelar', '__back__', 'btn-secondary')],
    'editar_mantenimiento':  [('← Cancelar', '__back__', 'btn-secondary')],
    'perfil_usuario':        [('← Volver', '__back__', 'btn-secondary')],
    'crear_admin_tic':       [('← Cancelar', '__back__', 'btn-secondary')],
    'crear_admin_pvd':       [('← Cancelar', '__back__', 'btn-secondary')],
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

    # Determinar permisos de navegación
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

    # Sustituir "Panel" en breadcrumb por el nombre del PVD activo
    if ctx['pvd_activo'] and bc_parent_label == 'Panel':
        ctx['bc_parent_label'] = ctx['pvd_activo'].nombre

    ctx['pvds_disponibles'] = list(
        PuntoViveDigital.objects.filter(estado='A').order_by('nombre')
    )

    # Servicios personalizados para el sidebar (requiere pvd_activo)
    ctx['es_pagina_servicio_custom'] = url_name in _FUNCTION_URL_NAMES
    if ctx.get('pvd_activo'):
        ctx['servicios_custom_nav'] = list(
            ServicioPersonalizado.objects.filter(
                punto_vive_digital=ctx['pvd_activo']
            ).only('pk', 'nombre', 'icono')
        )
        _svc_id_raw = (getattr(rm, 'kwargs', None) or {}).get('svc_id')
        ctx['active_svc_id'] = int(_svc_id_raw) if _svc_id_raw else None
    else:
        ctx['servicios_custom_nav'] = []
        ctx['active_svc_id'] = None

    # Restricción de módulos: solo aplica para Admin PVD con PVD activo seleccionado.
    # Superusuario y Admin TIC ven todo sin restricción.
    if ctx.get('es_admin_pvd_only') and ctx.get('pvd_activo'):
        ctx['restringir_modulos'] = True
        # Módulos del sistema (coarse-grained)
        modulos_activos = set(
            ModuloHabilitado.objects.filter(
                punto_vive_digital=ctx['pvd_activo'],
                habilitado=True
            ).values_list('modulo', flat=True)
        )
        # Añadir capacidades granulares de servicios personalizados habilitados
        for svc in ServicioPersonalizado.objects.filter(
            punto_vive_digital=ctx['pvd_activo'], habilitado=True
        ).only('modulos_sistema'):
            modulos_activos.update(svc.modulos_sistema or [])
        ctx['modulos_pvd_activo'] = modulos_activos

    # Resolver acciones del topbar para la página actual
    raw_actions = _TOPBAR_ACTIONS.get(url_name, [])
    resolved = []
    modulos_activos = ctx.get('modulos_pvd_activo', set())
    for label, target, css in raw_actions:
        if target == '__back__':
            action_url = bc_parent_url
        else:
            try:
                action_url = reverse(f'modulo_puntos:{target}')
            except NoReverseMatch:
                action_url = None
        if action_url:
            # Ocultar botones que requieren módulos no habilitados
            if ctx.get('restringir_modulos') and target in _TOPBAR_MODULO_REQUERIDO:
                if not _TOPBAR_MODULO_REQUERIDO[target].intersection(modulos_activos):
                    continue
            resolved.append({'label': label, 'url': action_url, 'css': css})
    ctx['topbar_actions'] = resolved

    return ctx
