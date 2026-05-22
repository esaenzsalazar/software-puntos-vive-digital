from django.db import migrations


SERVICIOS_BASE = [
    {
        'nombre': 'Acceso a Internet y Equipos',
        'descripcion': 'Uso de computadores y navegación en internet',
        'icono': '💻',
        'tipo': 'recoleccion',
        'campos': [],
        'url_externa': '',
        'es_embed': False,
    },
    {
        'nombre': 'Impresión y Digitalización',
        'descripcion': 'Impresión, escaneo y fotocopiado de documentos',
        'icono': '🖨️',
        'tipo': 'recoleccion',
        'campos': [],
        'url_externa': '',
        'es_embed': False,
    },
    {
        'nombre': 'Capacitación Digital',
        'descripcion': 'Cursos y talleres de alfabetización y competencias digitales',
        'icono': '🎓',
        'tipo': 'recoleccion',
        'campos': [],
        'url_externa': '',
        'es_embed': False,
    },
    {
        'nombre': 'Trámites y Documentos',
        'descripcion': 'Apoyo para diligenciar trámites en línea y documentos',
        'icono': '🪪',
        'tipo': 'recoleccion',
        'campos': [],
        'url_externa': '',
        'es_embed': False,
    },
    {
        'nombre': 'Servicios de la Alcaldía',
        'descripcion': 'Trámites y servicios municipales en línea',
        'icono': '🏛️',
        'tipo': 'redireccion',
        'campos': [],
        'url_externa': '',
        'es_embed': False,
    },
    {
        'nombre': 'Telesalud',
        'descripcion': 'Acceso a servicios de salud virtual y citas médicas en línea',
        'icono': '🩺',
        'tipo': 'redireccion',
        'campos': [],
        'url_externa': '',
        'es_embed': False,
    },
    {
        'nombre': 'Orientación Jurídica',
        'descripcion': 'Asesoría y orientación legal gratuita a ciudadanos',
        'icono': '⚖️',
        'tipo': 'recoleccion',
        'campos': [],
        'url_externa': '',
        'es_embed': False,
    },
    {
        'nombre': 'Programas Sociales',
        'descripcion': 'Información e inscripción a subsidios y programas sociales',
        'icono': '🤝',
        'tipo': 'recoleccion',
        'campos': [],
        'url_externa': '',
        'es_embed': False,
    },
    {
        'nombre': 'Emprendimiento Digital',
        'descripcion': 'Apoyo y orientación a emprendedores y negocios locales',
        'icono': '💡',
        'tipo': 'recoleccion',
        'campos': [],
        'url_externa': '',
        'es_embed': False,
    },
    {
        'nombre': 'Educación Virtual',
        'descripcion': 'Acceso a plataformas educativas y cursos en línea',
        'icono': '📚',
        'tipo': 'redireccion',
        'campos': [],
        'url_externa': '',
        'es_embed': False,
    },
]


def seed_servicios(apps, schema_editor):
    CatalogoServicio = apps.get_model('modulo_puntos_app', 'CatalogoServicio')
    for svc in SERVICIOS_BASE:
        CatalogoServicio.objects.get_or_create(
            nombre=svc['nombre'],
            defaults={
                'descripcion': svc['descripcion'],
                'icono': svc['icono'],
                'tipo': svc['tipo'],
                'campos': svc['campos'],
                'url_externa': svc['url_externa'],
                'es_embed': svc['es_embed'],
                'es_plantilla_sistema': True,
                'activo': True,
            },
        )


def unseed_servicios(apps, schema_editor):
    CatalogoServicio = apps.get_model('modulo_puntos_app', 'CatalogoServicio')
    nombres = [s['nombre'] for s in SERVICIOS_BASE]
    CatalogoServicio.objects.filter(nombre__in=nombres, es_plantilla_sistema=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_puntos_app', '0031_remove_registrofuncion_funcion_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_servicios, reverse_code=unseed_servicios),
    ]
