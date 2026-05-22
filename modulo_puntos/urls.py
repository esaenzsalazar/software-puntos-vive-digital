"""
URL configuration for Puntos Vive Digital system.
Contract CD-224-2026 - Alcaldía de Bugalagrande

Defines all URL patterns organized by functionality.
"""
from django.urls import path
from . import views

app_name = 'modulo_puntos'

urlpatterns = [
    # ==========================================================================
    # AUTENTICACIÓN
    # ==========================================================================
    path('login/', views.login_usuario, name='login'),
    path('', views.login_usuario, name='home'),
    path('logout/', views.logout_usuario, name='logout'),
    
    # ==========================================================================
    # PANEL DE CONTROL Y NAVEGACIÓN
    # ==========================================================================
    path('panel/', views.panel_control, name='panel_control'),
    path('seleccionar-pvd/', views.seleccionar_pvd_view, name='seleccionar_pvd_view'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('inicio-pvd/', views.inicio_pvd, name='inicio_pvd'),
    
    # ==========================================================================
    # GESTIÓN DE CIUDADANOS
    # ==========================================================================
    path('consultar-ciudadanos/', views.consultar_ciudadanos, name='consultar_ciudadanos'),
    path('registrar-ciudadano/', views.registrar_ciudadano, name='registrar_ciudadano'),
    path('editar-ciudadano/<int:ciu_cdgo>/', views.editar_ciudadano, name='editar_ciudadano'),
    path('historial-ciudadano/<int:ciu_cdgo>/', views.historial_ciudadano, name='historial_ciudadano'),
    path('ciudadanos-pendientes/', views.ciudadanos_pendientes, name='ciudadanos_pendientes'),
    path('ciudadano/<int:ciu_id>/aprobar/', views.aprobar_ciudadano, name='aprobar_ciudadano'),
    path('ciudadano/<int:ciu_id>/rechazar/', views.rechazar_ciudadano, name='rechazar_ciudadano'),

    # ==========================================================================
    # REGISTRO DE USUARIO CIUDADANO (Sin autenticación)
    # ==========================================================================
    path('registrar-usuario-ciudadano/', views.registrar_usuario_ciudadano, name='registrar_usuario_ciudadano'),
    path('registro-exitoso/', views.registro_exitoso, name='registro_exitoso'),

    # ==========================================================================
    # REGISTRO DE ATENCIONES Y SERVICIOS
    # ==========================================================================
    path('atenciones/', views.lista_atenciones, name='lista_atenciones'),
    path('registrar-atencion/', views.registrar_atencion, name='registrar_atencion'),
    path('atencion/<int:atencion_id>/', views.detalle_atencion, name='detalle_atencion'),
    path('atencion/<int:atencion_id>/estado/', views.cambiar_estado_atencion, name='cambiar_estado_atencion'),
    path('servicio/<int:servicio_id>/usar/<int:atencion_id>/', views.formulario_servicio, name='formulario_servicio'),
    path('servicio/<int:servicio_id>/abrir/', views.abrir_servicio_canvas, name='abrir_servicio_canvas'),
    path('registrar-servicio/', views.registrar_servicio, name='registrar_servicio'),
    path('registrar-satisfaccion/', views.registrar_satisfaccion, name='registrar_satisfaccion'),
    
    # ==========================================================================
    # GESTIÓN DE RECURSOS Y PRÉSTAMOS
    # ==========================================================================
    path('recursos/', views.lista_recursos, name='registrar_recurso'),
    path('recursos/nuevo/', views.crear_recurso, name='crear_recurso'),
    path('registrar-prestamo/', views.registrar_prestamo, name='registrar_prestamo'),
    path('prestamos/<int:prestamo_id>/editar/', views.editar_prestamo, name='editar_prestamo'),
    path('prestamos/<int:prestamo_id>/devolver/', views.devolver_prestamo, name='devolver_prestamo'),
    
    # ==========================================================================
    # REPORTES Y EXPORTACIÓN
    # ==========================================================================
    path('reportes/', views.reportes, name='reportes'),
    path('exportar-atenciones/', views.exportar_atenciones_csv, name='exportar_atenciones_csv'),
    path('exportar-ciudadanos/', views.exportar_ciudadanos_csv, name='exportar_ciudadanos_csv'),
    path('exportar-servicios/', views.exportar_servicios_csv, name='exportar_servicios_csv'),
    path('exportar-satisfaccion/', views.exportar_satisfaccion_csv, name='exportar_satisfaccion_csv'),
    path('exportar-prestamos/', views.exportar_prestamos_csv, name='exportar_prestamos_csv'),
    # ==========================================================================
    # GESTIÓN DE USUARIOS
    # ==========================================================================
    path('crear-admin-tic/', views.crear_admin_tic, name='crear_admin_tic'),
    path('crear-admin-pvd/', views.crear_admin_pvd, name='crear_admin_pvd'),

    # ==========================================================================
    # GESTIÓN DE ROLES Y PERMISOS (Solo Superusuario)
    # ==========================================================================
    path('gestionar-roles/', views.gestionar_roles, name='gestionar_roles'),
    path('asignar-rol/<int:user_id>/', views.asignar_rol_usuario, name='asignar_rol_usuario'),
    path('crear-rol/', views.crear_grupo_rol, name='crear_grupo_rol'),
    
    # ==========================================================================
    # GESTIÓN DE PUNTOS VIVE DIGITAL (Multi-PVD)
    # ==========================================================================
    path('pvd/', views.lista_pvd, name='lista_pvd'),
    path('pvd/<int:pvd_id>/servicios/', views.gestionar_servicios_pvd, name='gestionar_servicios_pvd'),
    path('pvd/validar-nombre/', views.validar_nombre_pvd, name='validar_nombre_pvd'),
    path('pvd/crear/', views.crear_pvd, name='crear_pvd'),
    path('pvd/editar/<int:pvd_cdgo>/', views.editar_pvd, name='editar_pvd'),
    path('pvd/activar/<int:pvd_cdgo>/', views.activar_pvd, name='activar_pvd'),
    path('pvd/eliminar/<int:pvd_cdgo>/', views.eliminar_pvd, name='eliminar_pvd'),
    path('pvd/seleccionar/<int:pvd_cdgo>/', views.seleccionar_pvd, name='seleccionar_pvd'),
    # ── Wizard AJAX ──
    path('pvd/wizard/paso1/', views.wizard_pvd_paso1, name='wizard_pvd_paso1'),
    path('pvd/wizard/buscar-admin/', views.wizard_pvd_buscar_admin, name='wizard_pvd_buscar_admin'),
    path('pvd/<int:pvd_id>/wizard/asignar/', views.wizard_pvd_asignar_servicio, name='wizard_pvd_asignar_servicio'),
    path('pvd/<int:pvd_id>/wizard/quitar/<int:svc_id>/', views.wizard_pvd_quitar_servicio, name='wizard_pvd_quitar_servicio'),
    path('pvd/<int:pvd_id>/wizard/servicio/nuevo/', views.wizard_pvd_crear_servicio, name='wizard_pvd_crear_servicio'),
    path('pvd/<int:pvd_id>/wizard/finalizar/', views.wizard_pvd_finalizar, name='wizard_pvd_finalizar'),
    # ==========================================================================
    # GESTIÓN DE SALAS
    # ==========================================================================
    path('salas/', views.lista_salas, name='lista_salas'),
    path('salas/crear/', views.crear_sala, name='crear_sala'),
    path('salas/editar/<int:sala_cdgo>/', views.editar_sala, name='editar_sala'),
    path('salas/activar/<int:sala_cdgo>/', views.activar_sala, name='activar_sala'),
    path('salas/eliminar/<int:sala_cdgo>/', views.eliminar_sala, name='eliminar_sala'),
    
    # ==========================================================================
    # HABILITACIÓN DE SALAS
    # ==========================================================================
    path('habilitaciones/', views.lista_habilitaciones, name='lista_habilitaciones'),
    path('habilitaciones/crear/', views.crear_habilitacion, name='crear_habilitacion'),
    path('habilitaciones/editar/<int:hab_id>/', views.editar_habilitacion, name='editar_habilitacion'),
    path('habilitaciones/cancelar/<int:hab_id>/', views.cancelar_habilitacion, name='cancelar_habilitacion'),
    path('habilitaciones/eliminar/<int:hab_id>/', views.eliminar_habilitacion, name='eliminar_habilitacion'),
    path('salas/<int:sala_id>/agenda/', views.agenda_sala, name='agenda_sala'),

    # ==========================================================================
    # MÓDULO PERMISOS (Solo Superusuario / Ofitic según vista)
    # ==========================================================================
    path('permisos/', views.lista_permisos_roles, name='lista_permisos_roles'),
    path('permisos/editar/<int:permiso_id>/', views.editar_permiso, name='editar_permiso'),
    path('permisos/usuario/<int:user_id>/', views.permisos_usuario, name='permisos_usuario'),
    path('permisos/ofitic/', views.vista_permisos_ofitic, name='permisos_ofitic'),

    # ==========================================================================
    # CURSOS / TALLERES
    # ==========================================================================
    path('cursos/', views.lista_cursos, name='lista_cursos'),
    path('cursos/crear/', views.crear_curso, name='crear_curso'),
    path('cursos/<int:curso_id>/', views.detalle_curso, name='detalle_curso'),
    path('cursos/<int:curso_id>/editar/', views.editar_curso, name='editar_curso'),
    path('cursos/<int:curso_id>/sesion/', views.crear_sesion_curso, name='crear_sesion_curso'),
    path('cursos/<int:curso_id>/inscribir/', views.inscribir_ciudadano, name='inscribir_ciudadano'),
    path('cursos/sesion/<int:sesion_id>/asistencia/', views.marcar_asistencia, name='marcar_asistencia'),

    # ==========================================================================
    # MANTENIMIENTO DE EQUIPOS
    # ==========================================================================
    path('mantenimientos/', views.lista_mantenimientos, name='lista_mantenimientos'),
    path('mantenimientos/crear/', views.crear_mantenimiento, name='crear_mantenimiento'),
    path('mantenimientos/<int:mant_id>/editar/', views.editar_mantenimiento, name='editar_mantenimiento'),

    # ==========================================================================
    # ==========================================================================
    # ACCESOS TEMPORALES (Superusuario / Admin TIC)
    # ==========================================================================
    path('accesos-temporales/', views.accesos_temporales, name='accesos_temporales'),

    # ==========================================================================
    # AYUDA Y SOPORTE
    # ==========================================================================
    path('ayuda/', views.ayuda_sistema, name='ayuda'),
]
