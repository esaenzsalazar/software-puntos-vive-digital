from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0007_ajustes_permisos'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='puntovivedigital',
            name='admin_a_cargo',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='pvd_a_cargo',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Administrador PVD a cargo',
            ),
        ),
    ]
