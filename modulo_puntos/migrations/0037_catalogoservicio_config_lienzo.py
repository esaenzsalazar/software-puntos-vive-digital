from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0036_catalogoservicio_config_tipos'),
    ]

    operations = [
        migrations.RenameField(
            model_name='catalogoservicio',
            old_name='config',
            new_name='config_lienzo',
        ),
    ]
