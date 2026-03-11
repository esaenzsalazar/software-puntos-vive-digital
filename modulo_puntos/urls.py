from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('panel/', views.panel_control, name='panel_control'),
    path('registrar-ciudadano/', views.registrar_ciudadano, name='registrar_ciudadano'),
    path('registrar-operador/', views.registrar_operador, name='registrar_operador'),
    path('registrar-atencion/', views.registrar_atencion, name='registrar_atencion'),
    path('registrar-satisfaccion/', views.registrar_satisfaccion, name='registrar_satisfaccion'),
]