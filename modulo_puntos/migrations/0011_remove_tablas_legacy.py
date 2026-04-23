from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0010_remove_operador'),
    ]

    operations = [
        migrations.DeleteModel(
            name='UsuarioSistema',
        ),
        migrations.DeleteModel(
            name='ListaValor',
        ),
    ]
