from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0016_servicio_ofertado'),
    ]

    operations = [
        migrations.RenameModel('ServicioOfertado', 'ModuloHabilitado'),
        migrations.AlterModelTable('ModuloHabilitado', 'pvd_modulos_habilitados'),
    ]
