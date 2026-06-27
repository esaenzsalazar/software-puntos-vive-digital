"""
0048 – Ciudadano.punto_vive_digital se vuelve NOT NULL (PROTECT).

Regla de negocio: un ciudadano SIEMPRE debe pertenecer a un PVD; la asignación
se hace automáticamente desde la sesión del request en la vista de registro.

Antes de aplicar el constraint NOT NULL, el paso RunPython elimina cualquier
registro huérfano (punto_vive_digital IS NULL) que pudiera quedar de datos
anteriores, evitando que la migración falle en bases con historia.
"""

import django.db.models.deletion
from django.db import migrations, models


def _eliminar_ciudadanos_sin_pvd(apps, schema_editor):
    Ciudadano = apps.get_model('modulo_puntos_app', 'Ciudadano')
    huerfanos = Ciudadano.objects.filter(punto_vive_digital__isnull=True)
    n = huerfanos.count()
    if n:
        huerfanos.delete()
        print(f'  [migración 0048] {n} ciudadano(s) sin PVD eliminados antes del ALTER.')


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0047_seguridad_indices_checkconstraint'),
    ]

    operations = [
        # 1. Limpiar registros huérfanos para que el ALTER no falle
        migrations.RunPython(
            _eliminar_ciudadanos_sin_pvd,
            reverse_code=migrations.RunPython.noop,
        ),

        # 2. Cambiar la columna a NOT NULL con on_delete=PROTECT
        migrations.AlterField(
            model_name='ciudadano',
            name='punto_vive_digital',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='modulo_puntos_app.puntovivedigital',
                verbose_name='Punto Vive Digital',
            ),
        ),
    ]
