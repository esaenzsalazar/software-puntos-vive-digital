# Generated manually — unifica "Impresora Láser" e "Impresora de Inyección" en "Impresora"

from django.db import migrations


def unificar_impresoras(apps, schema_editor):
    Recurso = apps.get_model('modulo_puntos_app', 'Recurso')
    Recurso.objects.filter(
        tipo__in=['Impresora Láser', 'Impresora de Inyección']
    ).update(tipo='Impresora')


def revertir(apps, schema_editor):
    # No reversible con precisión: el tipo original (Láser o Inyección) no se conserva.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0055_habilitacion_solicitante_ciudadano'),
    ]

    operations = [
        migrations.RunPython(unificar_impresoras, revertir),
    ]
