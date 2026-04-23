from django.db import migrations


def agregar_permiso_eliminar_sala(apps, schema_editor):
    PermisoDefinicion = apps.get_model('modulo_puntos_app', 'PermisoDefinicion')
    PermisoRol = apps.get_model('modulo_puntos_app', 'PermisoRol')

    permiso, _ = PermisoDefinicion.objects.get_or_create(
        codigo='infraestructura.eliminar_sala',
        defaults={
            'nombre': 'Eliminar Sala',
            'categoria': 'Infraestructura',
            'descripcion': 'Permite eliminar permanentemente una sala del sistema. Solo disponible si está habilitado desde el panel de permisos.',
            'delegable_por_ofitic': True,
            'activo': True,
        }
    )

    PermisoRol.objects.get_or_create(rol='admin_tic', permiso=permiso)


def eliminar_permiso_eliminar_sala(apps, schema_editor):
    PermisoDefinicion = apps.get_model('modulo_puntos_app', 'PermisoDefinicion')
    PermisoDefinicion.objects.filter(codigo='infraestructura.eliminar_sala').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0005_habilitacion_sala'),
    ]

    operations = [
        migrations.RunPython(agregar_permiso_eliminar_sala, eliminar_permiso_eliminar_sala),
    ]
