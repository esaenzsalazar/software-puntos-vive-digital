from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CiudadanoForm


def home(request):
    return redirect('panel_control')


@login_required
def panel_control(request):
    return render(request, 'modulo_puntos/panel_control.html')


@login_required
def registrar_ciudadano(request):
    if request.method == 'POST':
        form = CiudadanoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('panel_control')
    else:
        form = CiudadanoForm()

    return render(
        request,
        'modulo_puntos/registrar_ciudadano.html',
        {'form': form}
    )


@login_required
def registrar_operador(request):
    return render(request, 'modulo_puntos/registrar_operador.html')


@login_required
def registrar_atencion(request):
    return render(request, 'modulo_puntos/registrar_atencion.html')


@login_required
def registrar_satisfaccion(request):
    return render(request, 'modulo_puntos/registrar_satisfaccion.html')