from django.db import migrations


class Migration(migrations.Migration):
    """
    Elimina las tablas pvd_item_servicio y pvd_registro_servicio,
    reemplazadas por el nuevo sistema FuncionServicio / RegistroFuncion.
    """

    dependencies = [
        ('modulo_puntos_app', '0025_funcion_servicio_registro_funcion'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql='DROP TABLE IF EXISTS pvd_registro_servicio;',
                    reverse_sql='',
                ),
                migrations.RunSQL(
                    sql='DROP TABLE IF EXISTS pvd_item_servicio;',
                    reverse_sql='',
                ),
            ],
            state_operations=[
                migrations.DeleteModel(name='RegistroServicio'),
                migrations.DeleteModel(name='ItemServicio'),
            ],
        ),
    ]
