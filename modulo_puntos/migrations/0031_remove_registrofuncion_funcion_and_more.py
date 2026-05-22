import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0030_remove_registrofuncion_funcion_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Tell Django's state machine these legacy models are gone.
        # Physical tables were already dropped by RunSQL in 0030 — no DB ops needed.
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name='FuncionServicio'),
                migrations.DeleteModel(name='ModuloHabilitado'),
                migrations.DeleteModel(name='RegistroFuncion'),
                migrations.DeleteModel(name='ServicioPersonalizado'),
            ],
        ),
        # Create new catalogue models
        migrations.CreateModel(
            name='CatalogoServicio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, verbose_name='Nombre del servicio')),
                ('descripcion', models.CharField(blank=True, max_length=255, verbose_name='Descripción')),
                ('icono', models.CharField(default='⚙️', max_length=10, verbose_name='Ícono (emoji)')),
                ('tipo', models.CharField(choices=[('recoleccion', 'Recolección de datos'), ('redireccion', 'Redirección / Enlace externo')], default='recoleccion', max_length=20, verbose_name='Tipo')),
                ('campos', models.JSONField(default=list, verbose_name='Esquema de campos')),
                ('url_externa', models.CharField(blank=True, max_length=500, verbose_name='URL externa')),
                ('es_embed', models.BooleanField(default=False, verbose_name='Mostrar como iframe')),
                ('es_plantilla_sistema', models.BooleanField(default=False, verbose_name='Plantilla del sistema')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='servicios_catalogo_creados', to=settings.AUTH_USER_MODEL, verbose_name='Creado por')),
            ],
            options={
                'verbose_name': 'Servicio del Catálogo',
                'verbose_name_plural': 'Catálogo de Servicios',
                'db_table': 'pvd_catalogo_servicios',
                'ordering': ['-es_plantilla_sistema', 'nombre'],
            },
        ),
        migrations.CreateModel(
            name='PVDServicio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
                ('orden', models.PositiveIntegerField(default=0, verbose_name='Orden')),
                ('asignado_en', models.DateTimeField(auto_now_add=True)),
                ('pvd', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pvd_servicios', to='modulo_puntos_app.puntovivedigital', verbose_name='Punto Vive Digital')),
                ('servicio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pvd_asignaciones', to='modulo_puntos_app.catalogoservicio', verbose_name='Servicio')),
            ],
            options={
                'verbose_name': 'Servicio del PVD',
                'verbose_name_plural': 'Servicios del PVD',
                'db_table': 'pvd_pvd_servicios',
                'ordering': ['orden', 'servicio__nombre'],
                'unique_together': {('pvd', 'servicio')},
            },
        ),
    ]
