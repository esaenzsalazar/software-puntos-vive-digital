from django.urls import path
from . import views


app_name = 'modulo_puntos'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('login/', views.login_usuario, name='login'),
    path('logout/', views.logout_usuario, name='logout'),
    path('historial-ciudadano/<int:ciu_cdgo>/', views.historial_ciudadano, name='historial_ciudadano'),
    path('panel/', views.panel_control, name='panel_control'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('registrar-recurso/', views.registrar_recurso, name='registrar_recurso'),
    path('registrar-operador/', views.registrar_operador, name='registrar_operador'),
    path('consultar-ciudadanos/', views.consultar_ciudadanos, name='consultar_ciudadanos'),
    path('registrar-ciudadano/', views.registrar_ciudadano, name='registrar_ciudadano'),
    path('registrar-atencion/', views.registrar_atencion, name='registrar_atencion'),
    path('registrar-prestamo/', views.registrar_prestamo, name='registrar_prestamo'),
    path('registrar-satisfaccion/', views.registrar_satisfaccion, name='registrar_satisfaccion'),
    path('registrar-servicio/', views.registrar_servicio, name='registrar_servicio'),
    path('editar-ciudadano/<int:ciu_cdgo>/', views.editar_ciudadano, name='editar_ciudadano'),
    path('crear-admin-tic/', views.crear_admin_tic, name='crear_admin_tic'),
    path('crear-admin-pvd/', views.crear_admin_pvd, name='crear_admin_pvd'),
    path('reportes/', views.reportes, name='reportes'),
    path('consultar-operadores/', views.consultar_operadores, name='consultar_operadores'),
    path('editar-operador/<int:opr_cdgo>/', views.editar_operador, name='editar_operador'),
    path('exportar-atenciones/', views.exportar_atenciones_csv, name='exportar_atenciones_csv'),
]