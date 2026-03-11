from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Vista protegida: solo usuarios logueados pueden verla
@login_required
def home(request):
    return render(request, 'modulo_puntos/home.html')