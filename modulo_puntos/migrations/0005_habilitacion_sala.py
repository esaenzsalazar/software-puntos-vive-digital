from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0004_seed_permisos'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HabilitacionSala',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_uso', models.CharField(
                    choices=[
                        ('NAV', 'Sala de Navegación'),
                        ('CAP', 'Capacitación / Formación'),
                        ('CONF', 'Conferencia / Reunión'),
                        ('TRAM', 'Trámite en Línea'),
                        ('EXAM', 'Examen / Evaluación'),
                        ('OTRO', 'Otro uso'),
                    ],
                    max_length=4,
                    verbose_name='Tipo de Uso',
                )),
                ('fecha', models.DateField(verbose_name='Fecha')),
                ('hora_inicio', models.TimeField(verbose_name='Hora de Inicio')),
                ('hora_fin', models.TimeField(verbose_name='Hora de Fin')),
                ('solicitante', models.CharField(max_length=128, verbose_name='Solicitante / Grupo')),
                ('proposito', models.TextField(blank=True, null=True, verbose_name='Propósito / Descripción')),
                ('capacidad_requerida', models.IntegerField(blank=True, null=True, verbose_name='Personas Esperadas')),
                ('estado', models.CharField(
                    choices=[
                        ('P', 'Pendiente'),
                        ('C', 'Confirmada'),
                        ('E', 'En curso'),
                        ('F', 'Finalizada'),
                        ('X', 'Cancelada'),
                    ],
                    default='P',
                    max_length=1,
                    verbose_name='Estado',
                )),
                ('fecha_registro', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')),
                ('observaciones', models.TextField(blank=True, null=True, verbose_name='Observaciones')),
                ('sala', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='habilitaciones',
                    to='modulo_puntos_app.sala',
                    verbose_name='Sala',
                )),
                ('registrado_por', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='habilitaciones_registradas',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Registrado por',
                )),
            ],
            options={
                'verbose_name': 'Habilitación de Sala',
                'verbose_name_plural': 'Habilitaciones de Sala',
                'db_table': 'pvd_habilitaciones_sala',
                'ordering': ['fecha', 'hora_inicio'],
            },
        ),
        migrations.AddIndex(
            model_name='habilitacionsala',
            index=models.Index(fields=['sala', 'fecha'], name='idx_hab_sala_fecha'),
        ),
        migrations.AddIndex(
            model_name='habilitacionsala',
            index=models.Index(fields=['estado'], name='idx_hab_estado'),
        ),
    ]
