from django.contrib import admin
from .models import Ciudadano, PuntoViveDigital, Operador, Atencion

# Registro simplificado para probar
admin.site.register(Ciudadano)
admin.site.register(PuntoViveDigital)
admin.site.register(Operador)
admin.site.register(Atencion)