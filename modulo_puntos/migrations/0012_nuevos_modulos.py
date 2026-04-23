from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0011_remove_tablas_legacy'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── Curso ──────────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Curso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200, verbose_name='Nombre del Curso / Taller')),
                ('descripcion', models.TextField(blank=True, null=True, verbose_name='Descripción')),
                ('modalidad', models.CharField(choices=[('P', 'Presencial'), ('V', 'Virtual'), ('H', 'Híbrida')], default='P', max_length=1, verbose_name='Modalidad')),
                ('poblacion_objetivo', models.CharField(blank=True, max_length=200, null=True, verbose_name='Población Objetivo')),
                ('fecha_inicio', models.DateField(verbose_name='Fecha de Inicio')),
                ('fecha_fin', models.DateField(blank=True, null=True, verbose_name='Fecha de Fin')),
                ('estado', models.CharField(choices=[('PL', 'Planificado'), ('AC', 'En curso'), ('FI', 'Finalizado'), ('CA', 'Cancelado')], default='PL', max_length=2, verbose_name='Estado')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('punto_vive_digital', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cursos', to='modulo_puntos_app.puntovivedigital', verbose_name='Punto Vive Digital')),
                ('registrado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cursos_registrados', to=settings.AUTH_USER_MODEL, verbose_name='Registrado por')),
            ],
            options={
                'verbose_name': 'Curso / Taller',
                'verbose_name_plural': 'Cursos / Talleres',
                'db_table': 'pvd_cursos',
                'ordering': ['-fecha_inicio'],
            },
        ),
        # ── SesionCurso ────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='SesionCurso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_sesion', models.PositiveSmallIntegerField(verbose_name='N° Sesión')),
                ('fecha', models.DateField(verbose_name='Fecha')),
                ('hora_inicio', models.TimeField(verbose_name='Hora de Inicio')),
                ('hora_fin', models.TimeField(verbose_name='Hora de Fin')),
                ('tema', models.CharField(max_length=200, verbose_name='Tema')),
                ('contenido', models.TextField(blank=True, null=True, verbose_name='Contenido / Descripción')),
                ('curso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sesiones', to='modulo_puntos_app.curso', verbose_name='Curso')),
            ],
            options={
                'verbose_name': 'Sesión de Curso',
                'verbose_name_plural': 'Sesiones de Curso',
                'db_table': 'pvd_sesiones_curso',
                'ordering': ['curso', 'numero_sesion'],
            },
        ),
        migrations.AddConstraint(
            model_name='sesioncurso',
            constraint=models.UniqueConstraint(fields=['curso', 'numero_sesion'], name='uniq_curso_sesion'),
        ),
        # ── InscripcionCurso ───────────────────────────────────────────────────
        migrations.CreateModel(
            name='InscripcionCurso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(choices=[('I', 'Inscrito'), ('C', 'Completado'), ('R', 'Retirado')], default='I', max_length=1, verbose_name='Estado')),
                ('fecha_inscripcion', models.DateTimeField(auto_now_add=True)),
                ('ciudadano', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inscripciones_cursos', to='modulo_puntos_app.ciudadano', verbose_name='Ciudadano')),
                ('curso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inscripciones', to='modulo_puntos_app.curso', verbose_name='Curso')),
                ('registrado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inscripciones_registradas', to=settings.AUTH_USER_MODEL, verbose_name='Registrado por')),
            ],
            options={
                'verbose_name': 'Inscripción a Curso',
                'verbose_name_plural': 'Inscripciones a Cursos',
                'db_table': 'pvd_inscripciones_curso',
            },
        ),
        migrations.AddConstraint(
            model_name='inscripcioncurso',
            constraint=models.UniqueConstraint(fields=['curso', 'ciudadano'], name='uniq_inscripcion_curso_ciudadano'),
        ),
        # ── AsistenciaSesion ───────────────────────────────────────────────────
        migrations.CreateModel(
            name='AsistenciaSesion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asistio', models.BooleanField(default=False, verbose_name='Asistió')),
                ('ciudadano', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asistencias_sesiones', to='modulo_puntos_app.ciudadano', verbose_name='Ciudadano')),
                ('sesion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asistencias', to='modulo_puntos_app.sesioncurso', verbose_name='Sesión')),
            ],
            options={
                'verbose_name': 'Asistencia a Sesión',
                'verbose_name_plural': 'Asistencias a Sesiones',
                'db_table': 'pvd_asistencia_sesion',
            },
        ),
        migrations.AddConstraint(
            model_name='asistenciasesion',
            constraint=models.UniqueConstraint(fields=['sesion', 'ciudadano'], name='uniq_asistencia_sesion_ciudadano'),
        ),
        # ── MantenimientoEquipo ────────────────────────────────────────────────
        migrations.CreateModel(
            name='MantenimientoEquipo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('PRV', 'Preventivo'), ('COR', 'Correctivo')], default='PRV', max_length=3, verbose_name='Tipo')),
                ('fecha', models.DateField(verbose_name='Fecha')),
                ('equipos_intervenidos', models.TextField(verbose_name='Equipos Intervenidos')),
                ('descripcion', models.TextField(verbose_name='Descripción del Trabajo Realizado')),
                ('hallazgos', models.TextField(blank=True, null=True, verbose_name='Hallazgos')),
                ('acciones', models.TextField(blank=True, null=True, verbose_name='Acciones / Recomendaciones')),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('punto_vive_digital', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mantenimientos', to='modulo_puntos_app.puntovivedigital', verbose_name='Punto Vive Digital')),
                ('realizado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mantenimientos_realizados', to=settings.AUTH_USER_MODEL, verbose_name='Registrado por')),
            ],
            options={
                'verbose_name': 'Mantenimiento de Equipo',
                'verbose_name_plural': 'Mantenimientos de Equipos',
                'db_table': 'pvd_mantenimientos',
                'ordering': ['-fecha'],
            },
        ),
        # ── RegistroApertura ───────────────────────────────────────────────────
        migrations.CreateModel(
            name='RegistroApertura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(verbose_name='Fecha')),
                ('hora_apertura', models.TimeField(verbose_name='Hora de Apertura')),
                ('hora_cierre', models.TimeField(blank=True, null=True, verbose_name='Hora de Cierre')),
                ('observaciones', models.TextField(blank=True, null=True, verbose_name='Observaciones')),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('punto_vive_digital', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aperturas', to='modulo_puntos_app.puntovivedigital', verbose_name='Punto Vive Digital')),
                ('registrado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='aperturas_registradas', to=settings.AUTH_USER_MODEL, verbose_name='Registrado por')),
            ],
            options={
                'verbose_name': 'Registro de Apertura / Cierre',
                'verbose_name_plural': 'Registros de Apertura / Cierre',
                'db_table': 'pvd_apertura_cierre',
                'ordering': ['-fecha'],
            },
        ),
        migrations.AddConstraint(
            model_name='registroapertura',
            constraint=models.UniqueConstraint(fields=['punto_vive_digital', 'fecha'], name='uniq_apertura_pvd_fecha'),
        ),
        migrations.AddIndex(
            model_name='registroapertura',
            index=models.Index(fields=['punto_vive_digital', 'fecha'], name='idx_apertura_pvd_fecha'),
        ),
    ]
