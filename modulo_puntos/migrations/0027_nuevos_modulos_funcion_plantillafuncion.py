from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Extiende FuncionServicio y RegistroFuncion con los nuevos módulos
    (Agenda, Encuesta, multi-stock, inline-ciudadano, bitácora)
    y crea el modelo PlantillaFuncion (biblioteca de plantillas de red).
    """

    dependencies = [
        ('modulo_puntos_app', '0026_drop_item_registro_servicio'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        # ── FuncionServicio: nuevos módulos y configuraciones ─────────────────
        migrations.AddField(
            model_name='funcionservicio',
            name='mod_agenda',
            field=models.BooleanField(default=False, verbose_name='Módulo: Agenda/Citas'),
        ),
        migrations.AddField(
            model_name='funcionservicio',
            name='mod_encuesta',
            field=models.BooleanField(default=False, verbose_name='Módulo: Encuesta automática'),
        ),
        migrations.AddField(
            model_name='funcionservicio',
            name='stock_alerta_en',
            field=models.PositiveIntegerField(
                null=True, blank=True,
                verbose_name='Alerta cuando disponibles ≤',
            ),
        ),
        migrations.AddField(
            model_name='funcionservicio',
            name='stock_items',
            field=models.JSONField(default=list, verbose_name='Múltiples ítems de inventario'),
        ),
        migrations.AddField(
            model_name='funcionservicio',
            name='ciudadano_rol_etiqueta',
            field=models.CharField(
                max_length=50, default='Ciudadano', blank=True,
                verbose_name='Etiqueta del rol',
            ),
        ),
        migrations.AddField(
            model_name='funcionservicio',
            name='ciudadano_permite_inline',
            field=models.BooleanField(
                default=False,
                verbose_name='Captura datos inline si no está registrado',
            ),
        ),
        migrations.AddField(
            model_name='funcionservicio',
            name='ciudadano_campos_inline',
            field=models.JSONField(default=list, verbose_name='Campos extra a capturar inline'),
        ),
        migrations.AddField(
            model_name='funcionservicio',
            name='agenda_config',
            field=models.JSONField(default=dict, verbose_name='Configuración de agenda'),
        ),
        migrations.AddField(
            model_name='funcionservicio',
            name='encuesta_config',
            field=models.JSONField(default=list, verbose_name='Preguntas de encuesta de cierre'),
        ),

        # ── RegistroFuncion: multi-stock, agenda, bitácora ────────────────────
        migrations.AddField(
            model_name='registrofuncion',
            name='stock_seleccion',
            field=models.JSONField(default=dict, verbose_name='Ítems tomados (multi-stock)'),
        ),
        migrations.AddField(
            model_name='registrofuncion',
            name='agenda_fecha',
            field=models.DateField(null=True, blank=True, verbose_name='Fecha de turno'),
        ),
        migrations.AddField(
            model_name='registrofuncion',
            name='agenda_hora',
            field=models.TimeField(null=True, blank=True, verbose_name='Hora de turno'),
        ),
        migrations.AddField(
            model_name='registrofuncion',
            name='bitacora',
            field=models.JSONField(default=list, verbose_name='Bitácora de eventos'),
        ),

        # ── PlantillaFuncion: biblioteca de plantillas de red ─────────────────
        migrations.CreateModel(
            name='PlantillaFuncion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200, verbose_name='Nombre de la plantilla')),
                ('descripcion', models.CharField(max_length=500, blank=True, verbose_name='Descripción')),
                ('icono', models.CharField(max_length=20, default='📋', verbose_name='Icono (emoji)')),
                ('categoria', models.CharField(max_length=100, blank=True, default='General', verbose_name='Categoría')),
                ('mod_formulario', models.BooleanField(default=False)),
                ('mod_estados', models.BooleanField(default=False)),
                ('mod_ciudadano', models.BooleanField(default=False)),
                ('mod_stock', models.BooleanField(default=False)),
                ('mod_agenda', models.BooleanField(default=False)),
                ('mod_encuesta', models.BooleanField(default=False)),
                ('campos', models.JSONField(default=list)),
                ('estados', models.JSONField(default=list)),
                ('ciudadano_requerido', models.BooleanField(default=False)),
                ('ciudadano_rol_etiqueta', models.CharField(max_length=50, default='Ciudadano', blank=True)),
                ('ciudadano_permite_inline', models.BooleanField(default=False)),
                ('ciudadano_campos_inline', models.JSONField(default=list)),
                ('stock_nombre', models.CharField(max_length=200, blank=True, default='')),
                ('stock_total', models.PositiveIntegerField(default=0)),
                ('stock_unidad', models.CharField(max_length=50, blank=True, default='unidades')),
                ('stock_alerta_en', models.PositiveIntegerField(null=True, blank=True)),
                ('stock_items', models.JSONField(default=list)),
                ('agenda_config', models.JSONField(default=dict)),
                ('encuesta_config', models.JSONField(default=list)),
                ('solo_admin_tic', models.BooleanField(default=False, verbose_name='Solo Admin TIC puede instalar')),
                ('instalaciones', models.PositiveIntegerField(default=0, verbose_name='Veces instalada')),
                ('activa', models.BooleanField(default=True, verbose_name='Activa en biblioteca')),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('creado_por', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='auth.user',
                    verbose_name='Creada por',
                )),
            ],
            options={
                'verbose_name': 'Plantilla de función',
                'verbose_name_plural': 'Plantillas de funciones',
                'db_table': 'pvd_plantillas_funcion',
                'ordering': ['categoria', 'nombre'],
                'app_label': 'modulo_puntos_app',
            },
        ),
    ]
