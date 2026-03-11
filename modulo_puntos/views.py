from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CiudadanoForm

@login_required
def home(request):
    return render(request, 'modulo_puntos/home.html')

@login_required
def registrar_ciudadano(request):
    if request.method == 'POST':
        form = CiudadanoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = CiudadanoForm()
    return render(request, 'modulo_puntos/registrar_ciudadano.html', {'form': form})