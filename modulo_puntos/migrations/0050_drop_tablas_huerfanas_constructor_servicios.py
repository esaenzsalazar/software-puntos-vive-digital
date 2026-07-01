"""
Migración 0050 — Elimina las tablas huérfanas que quedaron de dos features
abandonadas y nunca terminaron de limpiarse (ver comentarios de las
migraciones 0030, 0035 y 0039, que ya intentaron esta limpieza pero no
cubrieron todas las tablas):

  - App 'constructor' (arquetipos de servicio dinámicos): solo quedaba
    'constructor_arquetiposervicio' (sus tablas hermanas ya se borraron
    en la migración 0035).
  - "Constructor de servicios personalizados" (catálogo/grupos/servicios
    maestro/servicios activos/entradas de módulo): ningún modelo de
    Django las referencia hoy. 'pvd_servicios_activos' incluso tenía una
    FK colgando a 'pvd_servicios_personalizados', tabla que la migración
    0030 ya había borrado.

Todas estas tablas están vacías (0 filas) al momento de esta migración.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0049_backfill_permisos_rol'),
    ]

    operations = [
        migrations.RunSQL(
            sql="SET FOREIGN_KEY_CHECKS = 0;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS pvd_entradas_modulos;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS pvd_servicios_activos;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS pvd_catalogo_servicio;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS pvd_grupos_servicio;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS pvd_servicios_maestro;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS constructor_arquetiposervicio;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="SET FOREIGN_KEY_CHECKS = 1;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="DELETE FROM django_migrations WHERE app = 'constructor';",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
