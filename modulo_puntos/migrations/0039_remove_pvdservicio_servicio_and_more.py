from django.db import migrations


class Migration(migrations.Migration):
    """
    Remove CatalogoServicio, PVDServicio, RespuestaServicio from Django state.
    Tables were never physically created (migrations 0031-0037 were fake-applied
    on the desktop), so database_operations is empty to avoid 'table not found' errors.
    """

    dependencies = [
        ('modulo_puntos_app', '0038_atencion_hora_inicio_nullable'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveField(
                    model_name='pvdservicio',
                    name='servicio',
                ),
                migrations.RemoveField(
                    model_name='respuestaservicio',
                    name='servicio',
                ),
                migrations.AlterUniqueTogether(
                    name='pvdservicio',
                    unique_together=None,
                ),
                migrations.RemoveField(
                    model_name='pvdservicio',
                    name='pvd',
                ),
                migrations.RemoveField(
                    model_name='respuestaservicio',
                    name='atencion',
                ),
                migrations.RemoveField(
                    model_name='puntovivedigital',
                    name='modulos_habilitados',
                ),
                migrations.DeleteModel(
                    name='CatalogoServicio',
                ),
                migrations.DeleteModel(
                    name='PVDServicio',
                ),
                migrations.DeleteModel(
                    name='RespuestaServicio',
                ),
            ],
        ),
    ]
