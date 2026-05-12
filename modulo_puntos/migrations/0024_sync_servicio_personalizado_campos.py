from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Las columnas categoria, color, campos y requiere_ciudadano ya existen
    en la tabla pvd_servicios_personalizados (creadas fuera del ORM).
    Esta migración solo actualiza el estado interno de Django sin ejecutar
    ningún SQL, usando SeparateDatabaseAndState.
    """

    dependencies = [
        ('modulo_puntos_app', '0023_remove_telefono_correo_pvd'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='serviciopersonalizado',
                    name='categoria',
                    field=models.CharField(blank=True, default='', max_length=100, verbose_name='Categoría'),
                ),
                migrations.AddField(
                    model_name='serviciopersonalizado',
                    name='color',
                    field=models.CharField(blank=True, default='#64748b', max_length=7, verbose_name='Color'),
                ),
                migrations.AddField(
                    model_name='serviciopersonalizado',
                    name='campos',
                    field=models.JSONField(default=list, verbose_name='Campos adicionales'),
                ),
                migrations.AddField(
                    model_name='serviciopersonalizado',
                    name='requiere_ciudadano',
                    field=models.BooleanField(default=False, verbose_name='Requiere ciudadano'),
                ),
            ],
        ),
    ]
