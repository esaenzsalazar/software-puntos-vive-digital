from django.urls import path
from . import views

app_name = 'modulo_puntos'

urlpatterns = [
    path('', views.PanelControlView.as_view(), name='panel_control'),
    path('registrar-ciudadano/', views.RegistrarCiudadanoView.as_view(), name='registrar_ciudadano'),
    path('registrar-atencion/', views.RegistrarAtencionView.as_view(), name='registrar_atencion'),
    path('registrar-satisfaccion/', views.RegistrarSatisfaccionView.as_view(), name='registrar_satisfaccion'),
]