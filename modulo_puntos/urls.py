from django.urls import path
from . import views

app_name = 'modulo_puntos'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('login/', views.login_usuario, name='login'),
    path('logout/', views.logout_usuario, name='logout'),

    path('panel/', views.panel_control, name='panel_control'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),

    path('consultar-ciudadanos/', views.consultar_ciudadanos, name='consultar_ciudadanos'),
    path('registrar-ciudadano/', views.registrar_ciudadano, name='registrar_ciudadano'),

    path('registrar-atencion/', views.registrar_atencion, name='registrar_atencion'),
    path('registrar-prestamo/', views.registrar_prestamo, name='registrar_prestamo'),
    path('registrar-satisfaccion/', views.registrar_satisfaccion, name='registrar_satisfaccion'),
    path('registrar-servicio/', views.registrar_servicio, name='registrar_servicio'),

    path('crear-admin-tic/', views.crear_admin_tic, name='crear_admin_tic'),
    path('crear-admin-pvd/', views.crear_admin_pvd, name='crear_admin_pvd'),
]