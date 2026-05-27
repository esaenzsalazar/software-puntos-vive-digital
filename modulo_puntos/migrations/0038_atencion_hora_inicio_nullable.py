from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0037_catalogoservicio_config_lienzo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='atencion',
            name='hora_inicio',
            field=models.TimeField(blank=True, null=True, verbose_name='Hora de Inicio'),
        ),
    ]
