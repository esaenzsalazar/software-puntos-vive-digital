from django.apps import AppConfig

class ModuloPuntosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modulo_puntos'
    label = 'modulo_puntos_app'  # Este es el ancla definitiva
    verbose_name = 'Sistema PVD Bugalagrande'