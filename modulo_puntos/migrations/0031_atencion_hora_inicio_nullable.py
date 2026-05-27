from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Dos cambios en uno:
    1. Limpia del esquema las tablas del wizard/custom-services (ya eliminadas de models.py).
    2. Hace nullable hora_inicio en Atencion (se quitó del formulario de registro).

    Las tablas del wizard se eliminan con DROP TABLE IF EXISTS + FK_CHECKS=0 porque
    algunas fueron marcadas como aplicadas via --fake y puede que no existan en la BD.
    """

    dependencies = [
        ('modulo_puntos_app', '0030_merge_20260526_1146'),
    ]

    operations = [
        # ── Actualizar estado del modelo Django (state) y limpiar BD con IF EXISTS ──
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(model_name='funcionservicio', name='servicio'),
                migrations.RemoveField(model_name='registrofuncion', name='funcion'),
                migrations.AlterUniqueTogether(name='modulohabilitado', unique_together=None),
                migrations.RemoveField(model_name='modulohabilitado', name='punto_vive_digital'),
                migrations.RemoveField(model_name='plantillaservicio', name='creado_por'),
                migrations.RemoveField(model_name='registrofuncion', name='ciudadano'),
                migrations.RemoveField(model_name='registrofuncion', name='creado_por'),
                migrations.RemoveField(model_name='serviciopersonalizado', name='punto_vive_digital'),
                migrations.DeleteModel(name='EntradaServicio'),
                migrations.DeleteModel(name='FuncionServicio'),
                migrations.DeleteModel(name='ModuloHabilitado'),
                migrations.DeleteModel(name='PlantillaServicio'),
                migrations.DeleteModel(name='RegistroFuncion'),
                migrations.DeleteModel(name='ServicioPersonalizado'),
            ],
            database_operations=[
                migrations.RunSQL("SET FOREIGN_KEY_CHECKS = 0", ""),
                migrations.RunSQL("DROP TABLE IF EXISTS pvd_entradas_servicio", ""),
                migrations.RunSQL("DROP TABLE IF EXISTS pvd_funciones_servicio", ""),
                migrations.RunSQL("DROP TABLE IF EXISTS pvd_modulos_habilitados", ""),
                migrations.RunSQL("DROP TABLE IF EXISTS pvd_plantillas_servicio", ""),
                migrations.RunSQL("DROP TABLE IF EXISTS pvd_registros_funcion", ""),
                migrations.RunSQL("DROP TABLE IF EXISTS pvd_servicios_personalizados", ""),
                migrations.RunSQL("SET FOREIGN_KEY_CHECKS = 1", ""),
            ],
        ),

        # ── Cambio real en BD: hora_inicio pasa a nullable ──
        migrations.AlterField(
            model_name='atencion',
            name='hora_inicio',
            field=models.TimeField(blank=True, null=True, verbose_name='Hora de Inicio'),
        ),

        # ── Sincronizar estado del campo estado de PVD (sin cambio de BD) ──
        migrations.AlterField(
            model_name='puntovivedigital',
            name='estado',
            field=models.CharField(
                choices=[('A', 'Activo'), ('I', 'Inactivo'), ('M', 'En mantenimiento')],
                default='A', max_length=1, verbose_name='Estado',
            ),
        ),
    ]
