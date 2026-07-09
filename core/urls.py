from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('modulo_puntos.urls')),
]

# /media/ NO se sirve directamente: las imágenes de Evidencias solo se ven
# a través de modulo_puntos:servir_evidencia, que exige sesión iniciada.
