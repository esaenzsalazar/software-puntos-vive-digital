from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('registrar/', views.registrar_citizen, name='registrar_ciudadano'),
]