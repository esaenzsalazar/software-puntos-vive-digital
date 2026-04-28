from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0013_recurso_codigo'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='pvd_temporal',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='accesos_temporales',
                to='modulo_puntos_app.puntovivedigital',
                verbose_name='PVD Temporal',
            ),
        ),
    ]
