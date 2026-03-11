from django.shortcuts import render, redirect
from .forms import CiudadanoForm
from django.contrib import messages

def registrar_ciudadano(request):
    if request.method == 'POST':
        form = CiudadanoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Ciudadano registrado exitosamente!")
            return redirect('registrar_ciudadano')
    else:
        form = CiudadanoForm()
    return render(request, 'modulo_puntos/registrar_ciudadano.html', {'form': form})

def home(request):
    return render(request, 'modulo_puntos/home.html')