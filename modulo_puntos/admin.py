from django.contrib import admin
from .models import (
    UsuarioSistema, Satisfaccion, PrestamoRecurso, ListaValor, 
    Atencion, Operador, Ciudadano, Recurso, Servicio, PuntoViveDigital
)

# Registramos los modelos básicos
admin.site.register(UsuarioSistema)
admin.site.register(Satisfaccion)
admin.site.register(PrestamoRecurso)
admin.site.register(ListaValor)
admin.site.register(Recurso)
admin.site.register(Servicio)
admin.site.register(PuntoViveDigital)

# Podemos personalizar un poco los listados más importantes
@admin.register(Ciudadano)
class CiudadanoAdmin(admin.ModelAdmin):
    list_display = ('ciu_numdoc', 'ciu_nmbres', 'ciu_aplldos', 'ciu_email', 'ciu_estdo')
    search_fields = ('ciu_numdoc', 'ciu_nmbres', 'ciu_aplldos')

@admin.register(Operador)
class OperadorAdmin(admin.ModelAdmin):
    list_display = ('opr_numdoc', 'opr_nmbres', 'opr_aplldos', 'opr_estdo')
    search_fields = ('opr_numdoc', 'opr_nmbres')

@admin.register(Atencion)
class AtencionAdmin(admin.ModelAdmin):
    list_display = ('atn_cdgo', 'atn_fecha', 'atn_hrini', 'atn_hrfin', 'atn_estdo')
    list_filter = ('atn_fecha', 'atn_estdo')