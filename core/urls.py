from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Rutas nativas de login/logout de Django
    path('accounts/', include('django.contrib.auth.urls')), 
    # Rutas de la aplicación de los puntos
    path('', include('modulo_puntos.urls')), 
]