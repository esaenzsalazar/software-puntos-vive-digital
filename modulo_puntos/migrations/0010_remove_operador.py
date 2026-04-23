import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def limpiar_datos_operador(apps, schema_editor):
    # Limpiar operador_id en atenciones (FK a pvd_operadores, IDs incompatibles con auth_user)
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("UPDATE pvd_atenciones SET operador_id = NULL")
    # Eliminar permisos del rol 'operador'
    PermisoRol = apps.get_model('modulo_puntos_app', 'PermisoRol')
    PermisoRol.objects.filter(rol='operador').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0009_remove_permisorol_uq_permiso_rol_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(limpiar_datos_operador, migrations.RunPython.noop),

        migrations.AlterField(
            model_name='atencion',
            name='operador',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='atenciones_registradas',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Registrado por',
            ),
        ),

        migrations.DeleteModel(
            name='Operador',
        ),

        migrations.AlterField(
            model_name='userprofile',
            name='rol',
            field=models.CharField(
                choices=[
                    ('superadmin', 'Superadministrador'),
                    ('admin_tic', 'Administrador TIC'),
                    ('admin_pvd', 'Administrador PVD'),
                ],
                default='admin_pvd',
                max_length=20,
                verbose_name='Rol del Usuario',
            ),
        ),

        migrations.AlterField(
            model_name='permisorol',
            name='rol',
            field=models.CharField(
                choices=[
                    ('admin_tic', 'Administrador TIC (Ofitic)'),
                    ('admin_pvd', 'Administrador PVD'),
                ],
                max_length=32,
                verbose_name='Rol',
            ),
        ),
    ]
