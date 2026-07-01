from django.db import migrations


def backfill_permisos_rol(apps, schema_editor):
    """
    Restaura la matriz de permisos por rol:
      - Administrador TIC: todos los permisos activos (gestión global).
      - Administrador PVD: los permisos activos marcados como delegables
        por Ofitic (mismo criterio que usaba el módulo "Delegar permisos PVD",
        ahora consolidado en esta matriz).
    Idempotente (get_or_create), no borra overrides individuales existentes.
    """
    PermisoDefinicion = apps.get_model('modulo_puntos_app', 'PermisoDefinicion')
    PermisoRol = apps.get_model('modulo_puntos_app', 'PermisoRol')

    for permiso in PermisoDefinicion.objects.filter(activo=True):
        PermisoRol.objects.get_or_create(rol='admin_tic', permiso=permiso)
        if permiso.delegable_por_ofitic:
            PermisoRol.objects.get_or_create(rol='admin_pvd', permiso=permiso)


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0048_ciudadano_pvd_not_null'),
    ]

    operations = [
        migrations.RunPython(backfill_permisos_rol, migrations.RunPython.noop),
    ]
