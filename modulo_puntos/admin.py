from django.contrib import admin
from .models import (
    UsuarioSistema, Satisfaccion, PrestamoRecurso, ListaValor,
    Atencion, Operador, Ciudadano, Recurso, Servicio, PuntoViveDigital,
    AuditoriaAccion, UserProfile
)

# Registramos el modelo de PuntoViveDigital mejorado
@admin.register(PuntoViveDigital)
class PuntoViveDigitalAdmin(admin.ModelAdmin):
    list_display = ('pvd_nombre', 'pvd_barrio', 'pvd_estdo', 'pvd_correo', 'pvd_fch_crea')
    list_filter = ('pvd_estdo', 'pvd_fch_crea')
    search_fields = ('pvd_nombre', 'pvd_barrio', 'pvd_dircion')
    readonly_fields = ('pvd_fch_crea',)

# Registramos el modelo de auditoría
@admin.register(AuditoriaAccion)
class AuditoriaAccionAdmin(admin.ModelAdmin):
    list_display = ('aud_cdgo', 'usuario', 'accion', 'modelo_afectado', 'fecha_accion')
    list_filter = ('accion', 'modelo_afectado', 'fecha_accion')
    search_fields = ('usuario', 'descripcion', 'modelo_afectado')
    readonly_fields = ('aud_cdgo', 'usuario', 'accion', 'modelo_afectado', 'objeto_id', 
                       'descripcion', 'ip_address', 'fecha_accion')
    date_hierarchy = 'fecha_accion'

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


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'pvd_asignado')
    list_filter = ('pvd_asignado',)
    search_fields = ('user__username', 'pvd_asignado__pvd_nombre')