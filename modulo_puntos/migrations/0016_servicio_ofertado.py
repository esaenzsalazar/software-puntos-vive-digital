from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0015_remove_registro_apertura'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServicioOfertado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(
                    choices=[
                        ('internet', 'Acceso a internet'),
                        ('sala_computo', 'Acceso a sala de capacitaciones y cómputo'),
                        ('impresiones', 'Impresiones'),
                        ('cursos', 'Cursos de aprendizaje'),
                        ('tramites', 'Trámites en Línea / Gobierno Digital'),
                    ],
                    max_length=64,
                    verbose_name='Servicio'
                )),
                ('habilitado', models.BooleanField(default=True, verbose_name='Habilitado')),
                ('fecha_habilitacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de habilitación')),
                ('punto_vive_digital', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='servicios_ofertados',
                    to='modulo_puntos_app.puntovivedigital',
                    verbose_name='Punto Vive Digital'
                )),
            ],
            options={
                'verbose_name': 'Servicio Ofertado',
                'verbose_name_plural': 'Servicios Ofertados',
                'db_table': 'pvd_servicios_ofertados',
                'unique_together': {('punto_vive_digital', 'nombre')},
            },
            # Nota: Este modelo fue renombrado a ModuloHabilitado en migración 0017
        ),
    ]
