"""
Django Admin configuration for Puntos Vive Digital system.
Contract CD-224-2026 - Alcaldía de Bugalagrande
"""
from django.contrib import admin
from .models import (
    UsuarioSistema, Satisfaccion, PrestamoRecurso, ListaValor,
    Atencion, Operador, Ciudadano, Recurso, Servicio, PuntoViveDigital,
    AuditoriaAccion, UserProfile, Sala
)


@admin.register(PuntoViveDigital)
class PuntoViveDigitalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'barrio', 'estado_legible', 'telefono', 'correo', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('nombre', 'barrio', 'direccion')
    readonly_fields = ('fecha_creacion',)
    ordering = ('nombre',)

    @admin.display(description='Estado')
    def estado_legible(self, obj):
        return obj.get_estado_display()


@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'punto_vive_digital', 'capacidad', 'estado_legible', 'fecha_creacion')
    list_filter = ('estado', 'punto_vive_digital')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('fecha_creacion',)
    ordering = ('punto_vive_digital', 'nombre')

    @admin.display(description='Estado')
    def estado_legible(self, obj):
        return obj.get_estado_display()


@admin.register(AuditoriaAccion)
class AuditoriaAccionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'accion_legible', 'modelo_afectado', 'objeto_id', 'fecha_accion', 'direccion_ip')
    list_filter = ('accion', 'modelo_afectado', 'fecha_accion')
    search_fields = ('usuario', 'descripcion', 'modelo_afectado')
    readonly_fields = (
        'id', 'usuario', 'accion', 'modelo_afectado', 'objeto_id',
        'descripcion', 'direccion_ip', 'fecha_accion'
    )
    date_hierarchy = 'fecha_accion'
    ordering = ('-fecha_accion',)

    @admin.display(description='Acción')
    def accion_legible(self, obj):
        return obj.get_accion_display()


@admin.register(Ciudadano)
class CiudadanoAdmin(admin.ModelAdmin):
    list_display = ('numero_documento', 'tipo_documento', 'nombre_completo', 'telefono', 'correo', 'punto_vive_digital', 'estado_legible')
    search_fields = ('numero_documento', 'primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido', 'correo')
    list_filter = ('estado', 'genero', 'etnia', 'punto_vive_digital')
    ordering = ('-id',)
    list_select_related = ('punto_vive_digital',)

    @admin.display(description='Nombre Completo')
    def nombre_completo(self, obj):
        return obj.get_nombre_completo()

    @admin.display(description='Estado')
    def estado_legible(self, obj):
        return obj.get_estado_display()


@admin.register(Operador)
class OperadorAdmin(admin.ModelAdmin):
    list_display = ('numero_documento', 'nombre_completo', 'correo', 'telefono', 'punto_vive_digital', 'estado_legible')
    search_fields = ('numero_documento', 'primer_nombre', 'primer_apellido', 'segundo_apellido', 'correo')
    list_filter = ('estado', 'punto_vive_digital')
    ordering = ('-id',)
    list_select_related = ('punto_vive_digital',)

    @admin.display(description='Nombre Completo')
    def nombre_completo(self, obj):
        return obj.get_nombre_completo()

    @admin.display(description='Estado')
    def estado_legible(self, obj):
        return obj.get_estado_display()


@admin.register(Atencion)
class AtencionAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'ciudadano_nombre', 'ciudadano_doc', 'operador_nombre', 'punto_vive_digital', 'hora_inicio', 'hora_fin', 'estado_legible')
    list_filter = ('fecha', 'estado', 'punto_vive_digital')
    search_fields = ('ciudadano__primer_nombre', 'ciudadano__primer_apellido', 'ciudadano__numero_documento', 'operador__primer_nombre', 'observaciones')
    ordering = ('-fecha', '-hora_inicio')
    list_select_related = ('ciudadano', 'operador', 'punto_vive_digital')

    @admin.display(description='Ciudadano')
    def ciudadano_nombre(self, obj):
        return obj.ciudadano.get_nombre_completo() if obj.ciudadano else '—'

    @admin.display(description='Documento')
    def ciudadano_doc(self, obj):
        return obj.ciudadano.numero_documento if obj.ciudadano else '—'

    @admin.display(description='Operador')
    def operador_nombre(self, obj):
        return obj.operador.get_nombre_completo() if obj.operador else '—'

    @admin.display(description='Estado')
    def estado_legible(self, obj):
        return obj.get_estado_display()


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('nombre_usuario', 'nombre_completo_usuario', 'correo_usuario', 'rol_legible', 'punto_asignado')
    list_filter = ('punto_asignado', 'rol')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'punto_asignado__nombre')
    ordering = ('usuario__username',)
    list_select_related = ('usuario', 'punto_asignado')

    @admin.display(description='Usuario')
    def nombre_usuario(self, obj):
        return obj.usuario.username

    @admin.display(description='Nombre')
    def nombre_completo_usuario(self, obj):
        return f"{obj.usuario.first_name} {obj.usuario.last_name}".strip() or '—'

    @admin.display(description='Correo')
    def correo_usuario(self, obj):
        return obj.usuario.email or '—'

    @admin.display(description='Rol')
    def rol_legible(self, obj):
        return obj.get_rol_display()


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'tipo', 'requiere_equipo_legible', 'estado_legible', 'atencion')
    list_filter = ('tipo', 'estado')
    search_fields = ('nombre', 'descripcion')
    ordering = ('-id',)

    @admin.display(description='Requiere Equipo')
    def requiere_equipo_legible(self, obj):
        return obj.get_requiere_equipo_display()

    @admin.display(description='Estado')
    def estado_legible(self, obj):
        return obj.get_estado_display()


@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin):
    list_display = ('id', 'tipo', 'punto_vive_digital', 'estado_legible')
    list_filter = ('tipo', 'estado', 'punto_vive_digital')
    search_fields = ('tipo',)
    ordering = ('id',)
    list_select_related = ('punto_vive_digital',)

    @admin.display(description='Estado')
    def estado_legible(self, obj):
        return obj.get_estado_display()


@admin.register(PrestamoRecurso)
class PrestamoRecursoAdmin(admin.ModelAdmin):
    list_display = ('id', 'tipo_recurso', 'fecha_entrega', 'fecha_devolucion', 'estado_devolucion')
    list_filter = ('fecha_entrega', 'fecha_devolucion')
    search_fields = ('observaciones', 'recurso__tipo')
    ordering = ('-id',)
    list_select_related = ('recurso',)

    @admin.display(description='Recurso')
    def tipo_recurso(self, obj):
        return obj.recurso.tipo if obj.recurso else '—'

    @admin.display(description='Estado')
    def estado_devolucion(self, obj):
        return 'Devuelto' if obj.fecha_devolucion else 'En préstamo'


@admin.register(Satisfaccion)
class SatisfaccionAdmin(admin.ModelAdmin):
    list_display = ('id', 'ciudadano_atencion', 'calificacion', 'fecha', 'comentario_corto')
    list_filter = ('calificacion', 'fecha')
    search_fields = ('comentario',)
    ordering = ('-fecha',)
    list_select_related = ('atencion', 'atencion__ciudadano')

    @admin.display(description='Ciudadano')
    def ciudadano_atencion(self, obj):
        if obj.atencion and obj.atencion.ciudadano:
            return obj.atencion.ciudadano.get_nombre_completo()
        return '—'

    @admin.display(description='Comentario')
    def comentario_corto(self, obj):
        return (obj.comentario[:60] + '...') if obj.comentario and len(obj.comentario) > 60 else obj.comentario or '—'


@admin.register(ListaValor)
class ListaValorAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'descripcion', 'estado')
    list_filter = ('estado',)
    search_fields = ('nombre', 'descripcion')
    ordering = ('id',)


@admin.register(UsuarioSistema)
class UsuarioSistemaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'estado')
    search_fields = ('nombre',)
    list_filter = ('estado',)
    ordering = ('id',)
