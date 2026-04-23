from django.db import migrations


def ajustar_permisos(apps, schema_editor):
    PermisoDefinicion = apps.get_model('modulo_puntos_app', 'PermisoDefinicion')
    PermisoRol = apps.get_model('modulo_puntos_app', 'PermisoRol')

    # Quitar la asignación automática de eliminar_sala para admin_tic:
    # el superusuario debe concederla explícitamente desde la matriz de permisos.
    try:
        perm_sala = PermisoDefinicion.objects.get(codigo='infraestructura.eliminar_sala')
        PermisoRol.objects.filter(rol='admin_tic', permiso=perm_sala).delete()
    except PermisoDefinicion.DoesNotExist:
        pass

    # Agregar permiso para eliminar PVDs (edificios) — solo el superusuario lo otorga
    PermisoDefinicion.objects.get_or_create(
        codigo='infraestructura.eliminar_pvd',
        defaults={
            'nombre': 'Eliminar PVD (Edificio)',
            'categoria': 'Infraestructura',
            'descripcion': (
                'Permite eliminar permanentemente un Punto Vive Digital del sistema. '
                'Solo disponible si el superusuario lo habilita explícitamente.'
            ),
            'delegable_por_ofitic': False,
            'activo': True,
        }
    )


def revertir_ajustes(apps, schema_editor):
    PermisoDefinicion = apps.get_model('modulo_puntos_app', 'PermisoDefinicion')
    PermisoRol = apps.get_model('modulo_puntos_app', 'PermisoRol')

    try:
        perm_sala = PermisoDefinicion.objects.get(codigo='infraestructura.eliminar_sala')
        PermisoRol.objects.get_or_create(rol='admin_tic', permiso=perm_sala)
    except PermisoDefinicion.DoesNotExist:
        pass

    PermisoDefinicion.objects.filter(codigo='infraestructura.eliminar_pvd').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0006_permiso_eliminar_sala'),
    ]

    operations = [
        migrations.RunPython(ajustar_permisos, revertir_ajustes),
    ]
