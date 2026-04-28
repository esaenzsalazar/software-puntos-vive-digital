from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0012_nuevos_modulos'),
    ]

    operations = [
        migrations.AddField(
            model_name='recurso',
            name='codigo',
            field=models.CharField(
                blank=True,
                help_text='Identificador único del equipo (ej: LAP-001). Opcional.',
                max_length=64,
                null=True,
                unique=True,
                verbose_name='Código del recurso',
            ),
        ),
    ]
