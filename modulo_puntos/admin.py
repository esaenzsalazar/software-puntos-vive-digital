from django.contrib import admin
# Importamos todos los modelos que definimos
from .models import Ciudadano, PuntoViveDigital, Operador, Atencion, Servicio, Recurso, UsuarioSistema, Rol

# Registramos uno por uno
admin.site.register(Ciudadano)
admin.site.register(PuntoViveDigital)
admin.site.register(Operador)
admin.site.register(Atencion)
admin.site.register(Servicio)
admin.site.register(Recurso)
admin.site.register(UsuarioSistema)
admin.site.register(Rol)