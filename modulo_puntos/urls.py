from django.urls import path
from . import views

app_name = 'modulo_puntos'

urlpatterns = [
    path('login/', views.login_usuario, name='login'),
    path('', views.login_usuario, name='home'),
    path('logout/', views.logout_usuario, name='logout'),
    path('panel/', views.panel_control, name='panel_control'),
    path('seleccionar-pvd/', views.seleccionar_pvd_view, name='seleccionar_pvd_view'),
    path('historial-ciudadano/<int:ciu_cdgo>/', views.historial_ciudadano, name='historial_ciudadano'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('registrar-recurso/', views.registrar_recurso, name='registrar_recurso'),
    path('consultar-ciudadanos/', views.consultar_ciudadanos, name='consultar_ciudadanos'),
    path('registrar-ciudadano/', views.registrar_ciudadano, name='registrar_ciudadano'),
    path('registrar-atencion/', views.registrar_atencion, name='registrar_atencion'),
    path('registrar-prestamo/', views.registrar_prestamo, name='registrar_prestamo'),
    path('registrar-satisfaccion/', views.registrar_satisfaccion, name='registrar_satisfaccion'),
    path('registrar-servicio/', views.registrar_servicio, name='registrar_servicio'),
    path('editar-ciudadano/<int:ciu_cdgo>/', views.editar_ciudadano, name='editar_ciudadano'),
    path('reportes/', views.reportes, name='reportes'),
    path('exportar-atenciones/', views.exportar_atenciones_csv, name='exportar_atenciones_csv'),
    path('exportar-ciudadanos/', views.exportar_ciudadanos_csv, name='exportar_ciudadanos_csv'),
    path('exportar-servicios/', views.exportar_servicios_csv, name='exportar_servicios_csv'),
    path('exportar-satisfaccion/', views.exportar_satisfaccion_csv, name='exportar_satisfaccion_csv'),
    path('exportar-prestamos/', views.exportar_prestamos_csv, name='exportar_prestamos_csv'),
    path('ayuda/', views.ayuda_sistema, name='ayuda'),
    path('crear-admin-tic/', views.crear_admin_tic, name='crear_admin_tic'),
    path('crear-admin-pvd/', views.crear_admin_pvd, name='crear_admin_pvd'),

    # Gestión de Puntos Vive Digital
    path('pvd/', views.lista_pvd, name='lista_pvd'),
    path('pvd/crear/', views.crear_pvd, name='crear_pvd'),
    path('pvd/editar/<int:pvd_cdgo>/', views.editar_pvd, name='editar_pvd'),
    path('pvd/activar/<int:pvd_cdgo>/', views.activar_pvd, name='activar_pvd'),
    path('pvd/seleccionar/<int:pvd_cdgo>/', views.seleccionar_pvd, name='seleccionar_pvd'),
]