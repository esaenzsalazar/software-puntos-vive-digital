from django.db import migrations


PERMISOS_INICIALES = [
    # Reportes
    {'codigo': 'reportes.ver', 'nombre': 'Ver Reportes', 'categoria': 'Reportes', 'descripcion': 'Acceso a la vista de reportes y estadísticas del sistema.', 'delegable_por_ofitic': True},
    {'codigo': 'reportes.exportar_csv', 'nombre': 'Exportar CSV', 'categoria': 'Reportes', 'descripcion': 'Exportar datos en formato CSV (atenciones, ciudadanos, servicios, etc.).', 'delegable_por_ofitic': True},
    # Ciudadanos
    {'codigo': 'ciudadanos.ver', 'nombre': 'Consultar Ciudadanos', 'categoria': 'Ciudadanos', 'descripcion': 'Buscar y listar ciudadanos registrados.', 'delegable_por_ofitic': True},
    {'codigo': 'ciudadanos.crear', 'nombre': 'Registrar Ciudadano', 'categoria': 'Ciudadanos', 'descripcion': 'Registrar nuevos ciudadanos en el sistema.', 'delegable_por_ofitic': True},
    {'codigo': 'ciudadanos.editar', 'nombre': 'Editar Ciudadano', 'categoria': 'Ciudadanos', 'descripcion': 'Modificar datos de ciudadanos existentes.', 'delegable_por_ofitic': True},
    {'codigo': 'ciudadanos.historial', 'nombre': 'Ver Historial de Ciudadano', 'categoria': 'Ciudadanos', 'descripcion': 'Ver el historial de atenciones de un ciudadano.', 'delegable_por_ofitic': True},
    # Atenciones
    {'codigo': 'atenciones.crear', 'nombre': 'Registrar Atención', 'categoria': 'Atenciones', 'descripcion': 'Registrar nuevas atenciones a ciudadanos.', 'delegable_por_ofitic': True},
    {'codigo': 'atenciones.registrar_servicio', 'nombre': 'Registrar Servicio', 'categoria': 'Atenciones', 'descripcion': 'Registrar servicios prestados durante una atención.', 'delegable_por_ofitic': True},
    {'codigo': 'atenciones.registrar_satisfaccion', 'nombre': 'Registrar Satisfacción', 'categoria': 'Atenciones', 'descripcion': 'Registrar encuestas de satisfacción de ciudadanos.', 'delegable_por_ofitic': True},
    # Inventario
    {'codigo': 'inventario.registrar_recurso', 'nombre': 'Registrar Recurso', 'categoria': 'Inventario', 'descripcion': 'Registrar nuevos recursos/equipos del PVD.', 'delegable_por_ofitic': True},
    {'codigo': 'inventario.registrar_prestamo', 'nombre': 'Registrar Préstamo', 'categoria': 'Inventario', 'descripcion': 'Registrar préstamos de recursos a ciudadanos.', 'delegable_por_ofitic': True},
    # Infraestructura
    {'codigo': 'infraestructura.ver_pvd', 'nombre': 'Ver PVDs', 'categoria': 'Infraestructura', 'descripcion': 'Listar y consultar Puntos Vive Digital.', 'delegable_por_ofitic': False},
    {'codigo': 'infraestructura.gestionar_salas', 'nombre': 'Gestionar Salas', 'categoria': 'Infraestructura', 'descripcion': 'Crear, editar y activar/desactivar salas del PVD.', 'delegable_por_ofitic': True},
]

# Roles que reciben cada permiso por defecto
ASIGNACIONES_POR_ROL = {
    'admin_tic': [
        'reportes.ver', 'reportes.exportar_csv',
        'ciudadanos.ver',
        'infraestructura.ver_pvd', 'infraestructura.gestionar_salas',
    ],
    'admin_pvd': [
        'reportes.ver', 'reportes.exportar_csv',
        'ciudadanos.ver', 'ciudadanos.crear', 'ciudadanos.editar', 'ciudadanos.historial',
        'atenciones.crear', 'atenciones.registrar_servicio', 'atenciones.registrar_satisfaccion',
        'inventario.registrar_recurso', 'inventario.registrar_prestamo',
        'infraestructura.gestionar_salas',
    ],
    'operador': [
        'ciudadanos.ver',
        'atenciones.crear', 'atenciones.registrar_servicio', 'atenciones.registrar_satisfaccion',
    ],
}


def crear_permisos(apps, schema_editor):
    PermisoDefinicion = apps.get_model('modulo_puntos_app', 'PermisoDefinicion')
    PermisoRol = apps.get_model('modulo_puntos_app', 'PermisoRol')

    for datos in PERMISOS_INICIALES:
        permiso, _ = PermisoDefinicion.objects.get_or_create(
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
        codigo__in=[p['codigo'] for p in PERMISOS_INICIALES]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0003_permisos'),
    ]

    operations = [
        migrations.RunPython(crear_permisos, eliminar_permisos),
    ]
