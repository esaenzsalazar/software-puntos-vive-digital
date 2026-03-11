from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    # El error estaba aquí: cambiamos registrar_citizen por registrar_ciudadano
    path('registrar/', views.registrar_ciudadano, name='registrar_ciudadano'), 
]