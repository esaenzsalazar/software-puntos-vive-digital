from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0014_userprofile_pvd_temporal'),
    ]

    operations = [
        migrations.DeleteModel(
            name='RegistroApertura',
        ),
    ]
