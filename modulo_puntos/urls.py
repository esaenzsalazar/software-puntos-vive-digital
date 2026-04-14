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

    # ==========================================================================
    # REGISTRO DE USUARIO CIUDADANO (Sin autenticación)
    # ==========================================================================
    path('registrar-usuario-ciudadano/', views.registrar_usuario_ciudadano, name='registrar_usuario_ciudadano'),
    path('registro-exitoso/', views.registro_exitoso, name='registro_exitoso'),

    # ==========================================================================
    # APROBACIÓN DE CIUDADANOS PENDIENTES
    # ==========================================================================
    path('ciudadanos-pendientes/', views.ciudadanos_pendientes, name='ciudadanos_pendientes'),
    path('aprobar-ciudadano/<int:ciu_cdgo>/', views.aprobar_ciudadano, name='aprobar_ciudadano'),
    path('rechazar-ciudadano/<int:ciu_cdgo>/', views.rechazar_ciudadano, name='rechazar_ciudadano'),
    
    # ==========================================================================
    # REGISTRO DE ATENCIONES Y SERVICIOS
    # ==========================================================================
    path('registrar-atencion/', views.registrar_atencion, name='registrar_atencion'),
    path('registrar-servicio/', views.registrar_servicio, name='registrar_servicio'),
    path('registrar-satisfaccion/', views.registrar_satisfaccion, name='registrar_satisfaccion'),
    
    # ==========================================================================
    # GESTIÓN DE RECURSOS Y PRÉSTAMOS
    # ==========================================================================
    path('registrar-recurso/', views.registrar_recurso, name='registrar_recurso'),
    path('registrar-prestamo/', views.registrar_prestamo, name='registrar_prestamo'),
    
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
    path('pvd/crear/', views.crear_pvd, name='crear_pvd'),
    path('pvd/editar/<int:pvd_cdgo>/', views.editar_pvd, name='editar_pvd'),
    path('pvd/activar/<int:pvd_cdgo>/', views.activar_pvd, name='activar_pvd'),
    path('pvd/seleccionar/<int:pvd_cdgo>/', views.seleccionar_pvd, name='seleccionar_pvd'),

    # ==========================================================================
    # GESTIÓN DE SALAS
    # ==========================================================================
    path('salas/', views.lista_salas, name='lista_salas'),
    path('salas/crear/', views.crear_sala, name='crear_sala'),
    path('salas/editar/<int:sala_cdgo>/', views.editar_sala, name='editar_sala'),
    path('salas/activar/<int:sala_cdgo>/', views.activar_sala, name='activar_sala'),
    
    # ==========================================================================
    # AYUDA Y SOPORTE
    # ==========================================================================
    path('ayuda/', views.ayuda_sistema, name='ayuda'),
]
