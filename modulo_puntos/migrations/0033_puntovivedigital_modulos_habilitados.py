from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0032_seed_catalogo_servicios'),
    ]

    operations = [
        migrations.AddField(
            model_name='puntovivedigital',
            name='modulos_habilitados',
            field=models.JSONField(blank=True, default=list, verbose_name='Módulos habilitados'),
        ),
    ]
