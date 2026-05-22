"""
Migración 0035 — Elimina tablas huérfanas del app 'constructor' que ya no
existe en el código pero cuya FK a pvd_puntos bloqueaba el borrado de PVDs.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0034_respuestaservicio'),
    ]

    operations = [
        # La tabla tiene FK a pvd_puntos; hay que quitarla antes de borrar PVDs.
        # Usamos IF EXISTS porque puede no existir en entornos de desarrollo nuevos.
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS constructor_serviciodinamico;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Por si quedaron otras tablas del mismo app 'constructor'
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS constructor_campoDinamico;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS constructor_respuestadinamica;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
