from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0035_drop_constructor_huerfano'),
    ]

    operations = [
        migrations.AddField(
            model_name='catalogoservicio',
            name='config',
            field=models.JSONField(blank=True, default=dict, verbose_name='Configuración del arquetipo'),
        ),
    ]
