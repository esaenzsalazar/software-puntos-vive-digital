from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Nota histórica: en la base de datos real estas columnas se agregaron
    fuera del ORM y esta migración sólo sincronizaba el estado interno de
    Django (SeparateDatabaseAndState con database_operations=[]), sin tocar
    el esquema. Como esta migración ya está marcada como aplicada ahí,
    Django nunca la vuelve a ejecutar en esa base — pero ese "database_operations=[]"
    hacía que una base de datos nueva (pruebas, CI, entorno nuevo) nunca
    llegara a crear estas columnas de verdad. Se dejan como operaciones
    normales para que el historial se pueda reproducir igual en cualquier base.
    """

    dependencies = [
        ('modulo_puntos_app', '0023_remove_telefono_correo_pvd'),
    ]

    operations = [
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
    ]
