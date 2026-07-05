from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0051_servicio_requiere_sala_servicio_sala'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='satisfaccion',
            name='chk_sat_calificacion',
        ),
        migrations.RemoveField(
            model_name='satisfaccion',
            name='calificacion',
        ),
        migrations.AddField(
            model_name='satisfaccion',
            name='tiempo_espera',
            field=models.CharField(
                choices=[('E', 'Excelente'), ('B', 'Bueno'), ('M', 'Por mejorar')],
                default='E', max_length=1,
                verbose_name='¿Tiempo de espera para ser atendido?',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='satisfaccion',
            name='atencion_servidor',
            field=models.CharField(
                choices=[('E', 'Excelente'), ('B', 'Bueno'), ('M', 'Por mejorar')],
                default='E', max_length=1,
                verbose_name='¿Atención brindada por el servidor público?',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='satisfaccion',
            name='satisfaccion_servicio',
            field=models.CharField(
                choices=[('E', 'Excelente'), ('B', 'Bueno'), ('M', 'Por mejorar')],
                default='E', max_length=1,
                verbose_name='¿Quedó satisfecho con la prestación del servicio?',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='satisfaccion',
            name='informacion_recibida',
            field=models.CharField(
                choices=[('E', 'Excelente'), ('B', 'Bueno'), ('M', 'Por mejorar')],
                default='E', max_length=1,
                verbose_name='¿La información recibida fue?',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='satisfaccion',
            name='comodidad_instalaciones',
            field=models.CharField(
                choices=[('E', 'Excelente'), ('B', 'Bueno'), ('M', 'Por mejorar')],
                default='E', max_length=1,
                verbose_name='¿Comodidad y limpieza de las instalaciones?',
            ),
            preserve_default=False,
        ),
    ]
