from django.contrib import admin
from .models import (
    Ciudadano, Atencion, Operador, PuntoViveDigital, 
    Servicio, Recurso, UsuarioSistema, Rol, 
    ListaValor, ListaValorDetalle, PrestamoRecurso, Satisfaccion
)

@admin.register(Ciudadano)
class CiudadanoAdmin(admin.ModelAdmin):
    list_display = ('ciu_numdoc', 'ciu_nmbres', 'ciu_aplldos', 'ciu_email')

@admin.register(Atencion)
class AtencionAdmin(admin.ModelAdmin):
    list_display = ('atn_cdgo', 'atn_fecha', 'atn_hrini', 'atn_estdo')

@admin.register(Operador)
class OperadorAdmin(admin.ModelAdmin):
    list_display = ('opr_numdoc', 'opr_nmbres', 'opr_aplldos')

# Registros simples para el resto
admin.site.register(PuntoViveDigital)
admin.site.register(Servicio)
admin.site.register(Recurso)
admin.site.register(UsuarioSistema)
admin.site.register(Rol)
admin.site.register(ListaValor)
admin.site.register(ListaValorDetalle)
admin.site.register(PrestamoRecurso)
admin.site.register(Satisfaccion)