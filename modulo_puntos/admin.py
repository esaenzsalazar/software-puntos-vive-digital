"""
Django Admin configuration for Puntos Vive Digital system.
Contract CD-224-2026 - Alcaldía de Bugalagrande
"""
from django.contrib import admin
from .models import (
    Satisfaccion, PrestamoRecurso,
    Atencion, Ciudadano, Recurso, Servicio, PuntoViveDigital,
    AuditoriaAccion, UserProfile, Sala, HabilitacionSala,
    PermisoDefinicion, PermisoRol, PermisoUsuario,
    Curso, SesionCurso, InscripcionCurso, AsistenciaSesion,
    MantenimientoEquipo,
)


@admin.register(PuntoViveDigital)
class PuntoViveDigitalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'barrio', 'estado_legible', 'fecha_creacion')
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


@admin.register(HabilitacionSala)
class HabilitacionSalaAdmin(admin.ModelAdmin):
    list_display = ('sala', 'tipo_uso_legible', 'fecha', 'hora_inicio', 'hora_fin', 'solicitante', 'capacidad_requerida', 'estado_legible', 'registrado_por')
    list_filter = ('tipo_uso', 'estado', 'sala__punto_vive_digital', 'fecha')
    search_fields = ('solicitante', 'proposito', 'sala__nombre')
    ordering = ('-fecha', 'hora_inicio')
    readonly_fields = ('fecha_registro',)
    list_select_related = ('sala', 'sala__punto_vive_digital', 'registrado_por')

    @admin.display(description='Tipo de Uso')
    def tipo_uso_legible(self, obj):
        return obj.get_tipo_uso_display()

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


@admin.register(Atencion)
class AtencionAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'ciudadano_nombre', 'ciudadano_doc', 'admin_pvd_nombre', 'punto_vive_digital', 'hora_inicio', 'hora_fin', 'estado_legible')
    list_filter = ('fecha', 'estado', 'punto_vive_digital')
    search_fields = ('ciudadano__primer_nombre', 'ciudadano__primer_apellido', 'ciudadano__numero_documento', 'operador__username', 'observaciones')
    ordering = ('-fecha', '-hora_inicio')
    list_select_related = ('ciudadano', 'operador', 'punto_vive_digital')

    @admin.display(description='Ciudadano')
    def ciudadano_nombre(self, obj):
        return obj.ciudadano.get_nombre_completo() if obj.ciudadano else '—'

    @admin.display(description='Documento')
    def ciudadano_doc(self, obj):
        return obj.ciudadano.numero_documento if obj.ciudadano else '—'

    @admin.display(description='Admin PVD')
    def admin_pvd_nombre(self, obj):
        if obj.operador:
            return obj.operador.get_full_name() or obj.operador.username
        return '—'

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
    list_display = ('id', 'ciudadano_atencion', 'puntaje_promedio_display', 'fecha', 'comentario_corto')
    list_filter = ('tiempo_espera', 'atencion_servidor', 'satisfaccion_servicio', 'fecha')
    search_fields = ('comentario',)
    ordering = ('-fecha',)
    list_select_related = ('atencion', 'atencion__ciudadano')

    @admin.display(description='Ciudadano')
    def ciudadano_atencion(self, obj):
        if obj.atencion and obj.atencion.ciudadano:
            return obj.atencion.ciudadano.get_nombre_completo()
        return '—'

    @admin.display(description='Puntaje')
    def puntaje_promedio_display(self, obj):
        promedio = obj.puntaje_promedio
        return f'{promedio:.1f}/5' if promedio is not None else '—'

    @admin.display(description='Comentario')
    def comentario_corto(self, obj):
        return (obj.comentario[:60] + '...') if obj.comentario and len(obj.comentario) > 60 else obj.comentario or '—'



@admin.register(PermisoDefinicion)
class PermisoDefinicionAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'activo', 'delegable_por_ofitic', 'fecha_creacion')
    list_filter = ('categoria', 'activo', 'delegable_por_ofitic')
    search_fields = ('codigo', 'nombre', 'descripcion')
    ordering = ('categoria', 'nombre')
    readonly_fields = ('fecha_creacion',)


@admin.register(PermisoRol)
class PermisoRolAdmin(admin.ModelAdmin):
    list_display = ('rol_legible', 'permiso', 'otorgado_por', 'fecha_asignacion')
    list_filter = ('rol',)
    list_select_related = ('permiso', 'otorgado_por')
    ordering = ('rol', 'permiso__categoria')

    @admin.display(description='Rol')
    def rol_legible(self, obj):
        return obj.get_rol_display()


@admin.register(PermisoUsuario)
class PermisoUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'permiso', 'concedido_legible', 'otorgado_por', 'fecha_asignacion')
    list_filter = ('concedido',)
    list_select_related = ('usuario', 'permiso', 'otorgado_por')
    ordering = ('usuario__username', 'permiso__categoria')

    @admin.display(description='Estado')
    def concedido_legible(self, obj):
        return 'Concedido' if obj.concedido else 'Revocado'


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'punto_vive_digital', 'modalidad', 'estado', 'fecha_inicio', 'fecha_fin', 'total_inscritos')
    list_filter = ('estado', 'modalidad', 'punto_vive_digital')
    search_fields = ('nombre', 'descripcion', 'poblacion_objetivo')
    ordering = ('-fecha_inicio',)
    list_select_related = ('punto_vive_digital',)

    @admin.display(description='Inscritos')
    def total_inscritos(self, obj):
        return obj.total_inscritos()


@admin.register(SesionCurso)
class SesionCursoAdmin(admin.ModelAdmin):
    list_display = ('curso', 'numero_sesion', 'fecha', 'hora_inicio', 'hora_fin', 'tema')
    list_filter = ('curso__punto_vive_digital', 'fecha')
    search_fields = ('tema', 'curso__nombre')
    ordering = ('curso', 'numero_sesion')
    list_select_related = ('curso',)


@admin.register(InscripcionCurso)
class InscripcionCursoAdmin(admin.ModelAdmin):
    list_display = ('ciudadano', 'curso', 'estado', 'fecha_inscripcion')
    list_filter = ('estado', 'curso__punto_vive_digital')
    search_fields = ('ciudadano__primer_nombre', 'ciudadano__primer_apellido', 'curso__nombre')
    list_select_related = ('ciudadano', 'curso')


@admin.register(AsistenciaSesion)
class AsistenciaSesionAdmin(admin.ModelAdmin):
    list_display = ('sesion', 'ciudadano', 'asistio')
    list_filter = ('asistio', 'sesion__curso__punto_vive_digital')
    list_select_related = ('sesion', 'ciudadano')


@admin.register(MantenimientoEquipo)
class MantenimientoEquipoAdmin(admin.ModelAdmin):
    list_display = ('punto_vive_digital', 'tipo', 'fecha', 'realizado_por', 'fecha_registro')
    list_filter = ('tipo', 'punto_vive_digital', 'fecha')
    search_fields = ('descripcion', 'equipos_intervenidos', 'hallazgos')
    ordering = ('-fecha',)
    list_select_related = ('punto_vive_digital', 'realizado_por')

