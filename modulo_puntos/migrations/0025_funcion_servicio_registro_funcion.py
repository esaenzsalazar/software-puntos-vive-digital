from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0024_sync_servicio_personalizado_campos'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='FuncionServicio',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200, verbose_name='Nombre de la función')),
                ('descripcion', models.TextField(blank=True, default='', verbose_name='Descripción')),
                ('mod_formulario', models.BooleanField(default=False, verbose_name='Módulo: Formulario libre')),
                ('mod_estados', models.BooleanField(default=False, verbose_name='Módulo: Estados personalizados')),
                ('mod_ciudadano', models.BooleanField(default=False, verbose_name='Módulo: Vínculo ciudadano')),
                ('mod_stock', models.BooleanField(default=False, verbose_name='Módulo: Control de stock')),
                ('campos', models.JSONField(default=list, verbose_name='Campos del formulario')),
                ('estados', models.JSONField(default=list, verbose_name='Estados personalizados')),
                ('ciudadano_requerido', models.BooleanField(default=False, verbose_name='Ciudadano requerido')),
                ('stock_nombre', models.CharField(blank=True, default='', max_length=200, verbose_name='Nombre del ítem')),
                ('stock_total', models.PositiveIntegerField(default=0, verbose_name='Cantidad total')),
                ('stock_unidad', models.CharField(blank=True, default='unidades', max_length=50, verbose_name='Unidad')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
                ('orden', models.PositiveIntegerField(default=0, verbose_name='Orden')),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('servicio', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='funciones',
                    to='modulo_puntos_app.serviciopersonalizado',
                    verbose_name='Servicio',
                )),
            ],
            options={
                'verbose_name': 'Función de servicio',
                'verbose_name_plural': 'Funciones de servicio',
                'db_table': 'pvd_funciones_servicio',
                'ordering': ['orden', 'nombre'],
                'app_label': 'modulo_puntos_app',
            },
        ),
        migrations.CreateModel(
            name='RegistroFuncion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre_persona', models.CharField(blank=True, default='', max_length=200, verbose_name='Nombre (si no es ciudadano registrado)')),
                ('estado_actual', models.CharField(blank=True, default='', max_length=100, verbose_name='Estado actual')),
                ('datos', models.JSONField(default=dict, verbose_name='Datos del formulario')),
                ('stock_cantidad', models.PositiveIntegerField(default=1, verbose_name='Cantidad (stock)')),
                ('fecha_fin_esperada', models.DateTimeField(blank=True, null=True, verbose_name='Fecha fin esperada')),
                ('fecha_fin_real', models.DateTimeField(blank=True, null=True, verbose_name='Fecha fin real')),
                ('notas', models.TextField(blank=True, default='', verbose_name='Notas')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
                ('ciudadano', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='modulo_puntos_app.ciudadano',
                    verbose_name='Ciudadano',
                )),
                ('creado_por', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='auth.user',
                    verbose_name='Creado por',
                )),
                ('funcion', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='registros_funcion',
                    to='modulo_puntos_app.funcionservicio',
                    verbose_name='Función',
                )),
            ],
            options={
                'verbose_name': 'Registro de función',
                'verbose_name_plural': 'Registros de función',
                'db_table': 'pvd_registros_funcion',
                'ordering': ['-creado_en'],
                'app_label': 'modulo_puntos_app',
            },
        ),
    ]
