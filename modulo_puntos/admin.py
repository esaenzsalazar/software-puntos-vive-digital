"""
Django Admin configuration for Puntos Vive Digital system.
Contract CD-224-2026 - Alcaldía de Bugalagrande

Customizes the Django admin interface for better usability.
"""
from django.contrib import admin
from .models import (
    UsuarioSistema, Satisfaccion, PrestamoRecurso, ListaValor,
    Atencion, Operador, Ciudadano, Recurso, Servicio, PuntoViveDigital,
    AuditoriaAccion, UserProfile, Sala
)

# ==============================================================================
# ADMINISTRACIÓN DE PUNTOS VIVE DIGITAL
# ==============================================================================

@admin.register(PuntoViveDigital)
class PuntoViveDigitalAdmin(admin.ModelAdmin):
    """Administración de Puntos Vive Digital con vista de lista mejorada."""
    list_display = ('pvd_nombre', 'pvd_barrio', 'pvd_estdo', 'pvd_correo', 'pvd_fch_crea')
    list_filter = ('pvd_estdo', 'pvd_fch_crea')
    search_fields = ('pvd_nombre', 'pvd_barrio', 'pvd_dircion')
    readonly_fields = ('pvd_fch_crea',)
    ordering = ('pvd_nombre',)


# ==============================================================================
# ADMINISTRACIÓN DE SALAS
# ==============================================================================

@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    """Administración de salas con filtros por PVD y estado."""
    list_display = ('sala_nombre', 'pvd_cdgo', 'sala_capacidad', 'sala_estdo', 'sala_fch_crea')
    list_filter = ('sala_estdo', 'pvd_cdgo')
    search_fields = ('sala_nombre', 'sala_descr')
    readonly_fields = ('sala_fch_crea',)
    ordering = ('pvd_cdgo', 'sala_nombre')


# ==============================================================================
# ADMINISTRACIÓN DE AUDITORÍA
# ==============================================================================

@admin.register(AuditoriaAccion)
class AuditoriaAccionAdmin(admin.ModelAdmin):
    """Administración de registros de auditoría (solo lectura)."""
    list_display = ('aud_cdgo', 'usuario', 'accion', 'modelo_afectado', 'fecha_accion')
    list_filter = ('accion', 'modelo_afectado', 'fecha_accion')
    search_fields = ('usuario', 'descripcion', 'modelo_afectado')
    readonly_fields = (
        'aud_cdgo', 'usuario', 'accion', 'modelo_afectado', 'objeto_id',
        'descripcion', 'ip_address', 'fecha_accion'
    )
    date_hierarchy = 'fecha_accion'
    ordering = ('-fecha_accion',)


# ==============================================================================
# ADMINISTRACIÓN DE CIUDADANOS
# ==============================================================================

@admin.register(Ciudadano)
class CiudadanoAdmin(admin.ModelAdmin):
    """Administración de ciudadanos con búsqueda por documento y nombre."""
    list_display = ('ciu_numdoc', 'ciu_nmbres', 'ciu_aplldos', 'ciu_email', 'ciu_estdo')
    search_fields = ('ciu_numdoc', 'ciu_nmbres', 'ciu_aplldos')
    list_filter = ('ciu_estdo', 'ciu_genro', 'ciu_etnia')
    ordering = ('-ciu_cdgo',)


# ==============================================================================
# ADMINISTRACIÓN DE OPERADORES
# ==============================================================================

@admin.register(Operador)
class OperadorAdmin(admin.ModelAdmin):
    """Administración de operadores con búsqueda por nombre y documento."""
    list_display = ('opr_numdoc', 'opr_nmbres', 'opr_aplldos', 'opr_estdo')
    search_fields = ('opr_numdoc', 'opr_nmbres', 'opr_aplldos')
    list_filter = ('opr_estdo', 'pvd_cdgo')
    ordering = ('-opr_cdgo',)


# ==============================================================================
# ADMINISTRACIÓN DE ATENCIONES
# ==============================================================================

@admin.register(Atencion)
class AtencionAdmin(admin.ModelAdmin):
    """Administración de atenciones con filtros por fecha y estado."""
    list_display = ('atn_cdgo', 'atn_fecha', 'atn_hrini', 'atn_hrfin', 'atn_estdo')
    list_filter = ('atn_fecha', 'atn_estdo', 'pvd_cdgo')
    search_fields = ('atn_obs',)
    ordering = ('-atn_fecha', '-atn_hrini')


# ==============================================================================
# ADMINISTRACIÓN DE PERFIL DE USUARIO
# ==============================================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Administración de perfiles de usuario con búsqueda por username y PVD."""
    list_display = ('user', 'pvd_asignado')
    list_filter = ('pvd_asignado',)
    search_fields = ('user__username', 'pvd_asignado__pvd_nombre')
    ordering = ('user__username',)


# ==============================================================================
# ADMINISTRACIÓN DE SERVICIOS
# ==============================================================================

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    """Administración de servicios con filtros."""
    list_display = ('srv_cdgo', 'srv_nombre', 'srv_tipo', 'srv_estdo')
    list_filter = ('srv_tipo', 'srv_estdo')
    search_fields = ('srv_nombre', 'srv_descr')
    ordering = ('-srv_cdgo',)


# ==============================================================================
# ADMINISTRACIÓN DE RECURSOS
# ==============================================================================

@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin):
    """Administración de recursos con filtros por tipo y estado."""
    list_display = ('rec_cdgo', 'rec_tipo', 'rec_estdo')
    list_filter = ('rec_tipo', 'rec_estdo')
    search_fields = ('rec_tipo',)
    ordering = ('rec_cdgo',)


# ==============================================================================
# ADMINISTRACIÓN DE PRÉSTAMOS
# ==============================================================================

@admin.register(PrestamoRecurso)
class PrestamoRecursoAdmin(admin.ModelAdmin):
    """Administración de préstamos con filtros por fecha."""
    list_display = ('prs_cdgo', 'rec_cdgo', 'prs_fchent', 'prs_fchdev')
    list_filter = ('prs_fchent', 'prs_fchdev')
    search_fields = ('prs_obs',)
    ordering = ('-prs_cdgo',)


# ==============================================================================
# ADMINISTRACIÓN DE SATISFACCIÓN
# ==============================================================================

@admin.register(Satisfaccion)
class SatisfaccionAdmin(admin.ModelAdmin):
    """Administración de encuestas de satisfacción."""
    list_display = ('sat_cdgo', 'atn_cdgo', 'sat_calif', 'sat_fecha')
    list_filter = ('sat_calif', 'sat_fecha')
    search_fields = ('sat_cmntrio',)
    ordering = ('-sat_fecha',)


# ==============================================================================
# ADMINISTRACIÓN DE LISTAS DE VALOR
# ==============================================================================

@admin.register(ListaValor)
class ListaValorAdmin(admin.ModelAdmin):
    """Administración de listas de valores genéricos."""
    list_display = ('lva_cdgo', 'lva_nombre', 'lva_estdo')
    list_filter = ('lva_estdo',)
    search_fields = ('lva_nombre', 'lva_descr')
    ordering = ('lva_cdgo',)


# ==============================================================================
# ADMINISTRACIÓN DE USUARIOS DEL SISTEMA (LEGACY)
# ==============================================================================

@admin.register(UsuarioSistema)
class UsuarioSistemaAdmin(admin.ModelAdmin):
    """
    Administración de usuarios del sistema heredado.
    Nota: Para nuevos desarrollos, usar el sistema de usuarios de Django.
    """
    list_display = ('usu_cdgo', 'usu_nombre', 'usu_estdo')
    search_fields = ('usu_nombre',)
    list_filter = ('usu_estdo',)
    ordering = ('usu_cdgo',)
