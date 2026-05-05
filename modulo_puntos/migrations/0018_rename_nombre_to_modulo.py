from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0017_rename_servicio_ofertado_modulo_habilitado'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ModuloHabilitado',
            old_name='nombre',
            new_name='modulo',
        ),
    ]
