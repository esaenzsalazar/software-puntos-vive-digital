from django.contrib import admin
from .models import Ciudadano, Operador, Atencion, Servicio, Satisfaccion


@admin.register(Ciudadano)
class CiudadanoAdmin(admin.ModelAdmin):
    list_display = ('ciu_numdoc', 'ciu_nmbres', 'ciu_aplldos', 'ciu_estdo')
    list_display_links = ('ciu_numdoc', 'ciu_nmbres')
    search_fields = ('ciu_numdoc', 'ciu_nmbres', 'ciu_aplldos')
    list_filter = ('ciu_genro', 'ciu_nvleduc', 'ciu_estrato')

    fieldsets = (
        ('Datos de Identificación', {
            'fields': ('ciu_tpodoc', 'ciu_numdoc', 'ciu_nmbres', 'ciu_aplldos', 'ciu_fchancm')
        }),
        ('Caracterización Socio-demográfica', {
            'fields': ('ciu_genro', 'ciu_etnia', 'ciu_nvleduc', 'ciu_ocpcion', 'ciu_estrato', 'ciu_discapacidad')
        }),
        ('Contacto', {
            'fields': ('ciu_email', 'ciu_tlfno', 'ciu_estdo')
        }),
    )


admin.site.register(Operador)
admin.site.register(Atencion)
admin.site.register(Servicio)
admin.site.register(Satisfaccion)