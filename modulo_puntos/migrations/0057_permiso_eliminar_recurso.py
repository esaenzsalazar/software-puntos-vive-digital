# Generated manually — agrega el permiso "inventario.eliminar_recurso",
# asignado solo a Admin TIC (y Superusuario, que siempre tiene acceso total).
# Admin PVD no puede eliminar recursos del inventario.

from django.db import migrations

CODIGO = 'inventario.eliminar_recurso'


def crear_permiso(apps, schema_editor):
    PermisoDefinicion = apps.get_model('modulo_puntos_app', 'PermisoDefinicion')
    PermisoRol = apps.get_model('modulo_puntos_app', 'PermisoRol')

    permiso, _ = PermisoDefinicion.objects.get_or_create(
        codigo=CODIGO,
        defaults={
            'nombre': 'Eliminar Recurso',
            'categoria': 'Inventario',
            'descripcion': 'Eliminar permanentemente un recurso del inventario.',
            'delegable_por_ofitic': False,
            'activo': True,
        }
    )
    PermisoRol.objects.get_or_create(rol='admin_tic', permiso=permiso)


def eliminar_permiso(apps, schema_editor):
    PermisoDefinicion = apps.get_model('modulo_puntos_app', 'PermisoDefinicion')
    PermisoDefinicion.objects.filter(codigo=CODIGO).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0056_unificar_tipo_impresora'),
    ]

    operations = [
        migrations.RunPython(crear_permiso, eliminar_permiso),
    ]
