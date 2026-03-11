from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('registrar-ciudadano/', views.registrar_ciudadano, name='registrar_ciudadano'),
]