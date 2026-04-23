from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0002_rename_tables'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PermisoDefinicion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=64, unique=True, verbose_name='Código')),
                ('nombre', models.CharField(max_length=128, verbose_name='Nombre')),
                ('descripcion', models.TextField(blank=True, verbose_name='Descripción')),
                ('categoria', models.CharField(max_length=64, verbose_name='Categoría')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
                ('delegable_por_ofitic', models.BooleanField(default=False, verbose_name='Delegable por Ofitic')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
            ],
            options={
                'verbose_name': 'Permiso',
                'verbose_name_plural': 'Permisos',
                'db_table': 'pvd_permisos_definicion',
                'ordering': ['categoria', 'nombre'],
            },
        ),
        migrations.CreateModel(
            name='PermisoRol',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rol', models.CharField(
                    choices=[
                        ('admin_tic', 'Administrador TIC (Ofitic)'),
                        ('admin_pvd', 'Administrador PVD'),
                        ('operador', 'Operador'),
                    ],
                    max_length=32,
                    verbose_name='Rol',
                )),
                ('fecha_asignacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de asignación')),
                ('otorgado_por', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='permisos_rol_otorgados',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Otorgado por',
                )),
                ('permiso', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='roles',
                    to='modulo_puntos_app.permisodefinicion',
                    verbose_name='Permiso',
                )),
            ],
            options={
                'verbose_name': 'Permiso de Rol',
                'verbose_name_plural': 'Permisos de Roles',
                'db_table': 'pvd_permisos_rol',
            },
        ),
        migrations.AddConstraint(
            model_name='permisorol',
            constraint=models.UniqueConstraint(fields=['rol', 'permiso'], name='uq_permiso_rol'),
        ),
        migrations.CreateModel(
            name='PermisoUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('concedido', models.BooleanField(default=True, verbose_name='Concedido')),
                ('fecha_asignacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de asignación')),
                ('otorgado_por', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='permisos_usuario_otorgados',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Otorgado por',
                )),
                ('permiso', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='usuarios',
                    to='modulo_puntos_app.permisodefinicion',
                    verbose_name='Permiso',
                )),
                ('usuario', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='permisos_individuales',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuario',
                )),
            ],
            options={
                'verbose_name': 'Permiso de Usuario',
                'verbose_name_plural': 'Permisos de Usuarios',
                'db_table': 'pvd_permisos_usuario',
            },
        ),
        migrations.AddConstraint(
            model_name='permisousuario',
            constraint=models.UniqueConstraint(fields=['usuario', 'permiso'], name='uq_permiso_usuario'),
        ),
    ]
