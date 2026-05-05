from django.db import migrations


NUEVOS_PERMISOS = [
    # Salas
    {'codigo': 'salas.ver',      'nombre': 'Ver Salas',           'categoria': 'Salas', 'descripcion': 'Listar y consultar las salas del PVD.',                           'delegable_por_ofitic': True},
    {'codigo': 'salas.crear',    'nombre': 'Crear Sala',          'categoria': 'Salas', 'descripcion': 'Registrar nuevas salas en el PVD.',                               'delegable_por_ofitic': True},
    {'codigo': 'salas.editar',   'nombre': 'Editar / Activar Sala','categoria': 'Salas', 'descripcion': 'Modificar datos de salas y cambiar su estado activo/inactivo.',   'delegable_por_ofitic': True},
    # Habilitaciones
    {'codigo': 'habilitaciones.ver',      'nombre': 'Ver Habilitaciones',      'categoria': 'Habilitaciones', 'descripcion': 'Consultar la agenda de habilitaciones de sala.',                   'delegable_por_ofitic': True},
    {'codigo': 'habilitaciones.crear',    'nombre': 'Crear Habilitación',      'categoria': 'Habilitaciones', 'descripcion': 'Registrar nuevas habilitaciones de sala.',                         'delegable_por_ofitic': True},
    {'codigo': 'habilitaciones.editar',   'nombre': 'Editar Habilitación',     'categoria': 'Habilitaciones', 'descripcion': 'Modificar datos de habilitaciones existentes.',                    'delegable_por_ofitic': True},
    {'codigo': 'habilitaciones.cancelar', 'nombre': 'Cancelar Habilitación',   'categoria': 'Habilitaciones', 'descripcion': 'Cancelar habilitaciones pendientes o en curso.',                   'delegable_por_ofitic': True},
    {'codigo': 'habilitaciones.eliminar', 'nombre': 'Eliminar Habilitación',   'categoria': 'Habilitaciones', 'descripcion': 'Eliminar permanentemente una habilitación del sistema.',           'delegable_por_ofitic': False},
    # Mantenimiento
    {'codigo': 'mantenimiento.ver',    'nombre': 'Ver Mantenimientos',    'categoria': 'Mantenimiento', 'descripcion': 'Listar y consultar registros de mantenimiento de equipos.',      'delegable_por_ofitic': True},
    {'codigo': 'mantenimiento.crear',  'nombre': 'Registrar Mantenimiento','categoria': 'Mantenimiento', 'descripcion': 'Registrar nuevos mantenimientos de equipos.',                   'delegable_por_ofitic': True},
    {'codigo': 'mantenimiento.editar', 'nombre': 'Editar Mantenimiento',   'categoria': 'Mantenimiento', 'descripcion': 'Modificar registros de mantenimiento existentes.',               'delegable_por_ofitic': True},
    # Cursos y Talleres
    {'codigo': 'cursos.ver',        'nombre': 'Ver Cursos',           'categoria': 'Cursos', 'descripcion': 'Listar y ver el detalle de cursos y talleres.',               'delegable_por_ofitic': True},
    {'codigo': 'cursos.crear',      'nombre': 'Crear Curso',          'categoria': 'Cursos', 'descripcion': 'Registrar nuevos cursos o talleres.',                         'delegable_por_ofitic': True},
    {'codigo': 'cursos.editar',     'nombre': 'Editar Curso',         'categoria': 'Cursos', 'descripcion': 'Modificar datos de cursos existentes.',                       'delegable_por_ofitic': True},
    {'codigo': 'cursos.sesiones',   'nombre': 'Gestionar Sesiones',   'categoria': 'Cursos', 'descripcion': 'Crear y gestionar sesiones dentro de un curso.',              'delegable_por_ofitic': True},
    {'codigo': 'cursos.inscribir',  'nombre': 'Inscribir Ciudadanos', 'categoria': 'Cursos', 'descripcion': 'Inscribir ciudadanos en cursos o talleres.',                  'delegable_por_ofitic': True},
    {'codigo': 'cursos.asistencia', 'nombre': 'Registrar Asistencia', 'categoria': 'Cursos', 'descripcion': 'Marcar asistencia de ciudadanos en sesiones de curso.',       'delegable_por_ofitic': True},
    # Inventario (ampliar los existentes con editar préstamo)
    {'codigo': 'inventario.editar_prestamo', 'nombre': 'Editar Préstamo', 'categoria': 'Inventario', 'descripcion': 'Modificar datos de préstamos de recursos existentes.', 'delegable_por_ofitic': True},
]

ASIGNACIONES_POR_ROL = {
    'admin_tic': [
        'salas.ver', 'salas.crear', 'salas.editar',
        'habilitaciones.ver', 'habilitaciones.crear', 'habilitaciones.editar', 'habilitaciones.cancelar', 'habilitaciones.eliminar',
        'mantenimiento.ver', 'mantenimiento.crear', 'mantenimiento.editar',
        'cursos.ver', 'cursos.crear', 'cursos.editar', 'cursos.sesiones', 'cursos.inscribir', 'cursos.asistencia',
        'inventario.editar_prestamo',
    ],
    'admin_pvd': [
        'salas.ver', 'salas.crear', 'salas.editar',
        'habilitaciones.ver', 'habilitaciones.crear', 'habilitaciones.editar', 'habilitaciones.cancelar',
        'mantenimiento.ver', 'mantenimiento.crear', 'mantenimiento.editar',
        'cursos.ver', 'cursos.crear', 'cursos.editar', 'cursos.sesiones', 'cursos.inscribir', 'cursos.asistencia',
        'inventario.editar_prestamo',
    ],
}


def crear_permisos(apps, schema_editor):
    PermisoDefinicion = apps.get_model('modulo_puntos_app', 'PermisoDefinicion')
    PermisoRol = apps.get_model('modulo_puntos_app', 'PermisoRol')

    for datos in NUEVOS_PERMISOS:
        PermisoDefinicion.objects.get_or_create(
            codigo=datos['codigo'],
            defaults={
                'nombre': datos['nombre'],
                'categoria': datos['categoria'],
                'descripcion': datos.get('descripcion', ''),
                'delegable_por_ofitic': datos.get('delegable_por_ofitic', False),
                'activo': True,
            }
        )

    for rol, codigos in ASIGNACIONES_POR_ROL.items():
        for codigo in codigos:
            try:
                permiso = PermisoDefinicion.objects.get(codigo=codigo)
                PermisoRol.objects.get_or_create(rol=rol, permiso=permiso)
            except PermisoDefinicion.DoesNotExist:
                pass


def eliminar_permisos(apps, schema_editor):
    PermisoDefinicion = apps.get_model('modulo_puntos_app', 'PermisoDefinicion')
    PermisoDefinicion.objects.filter(
        codigo__in=[p['codigo'] for p in NUEVOS_PERMISOS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0018_rename_nombre_to_modulo'),
    ]

    operations = [
        migrations.RunPython(crear_permisos, eliminar_permisos),
    ]
