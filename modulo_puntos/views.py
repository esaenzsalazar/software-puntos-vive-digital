from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse

from .models import Ciudadano, Atencion, Satisfaccion, Servicio, PrestamoRecurso
from .forms import (
    CiudadanoForm,
    AtencionForm,
    SatisfaccionForm,
    ServicioForm,
    PrestamoRecursoForm,
    LoginForm,
    CrearUsuarioForm,
    PerfilUsuarioForm
)


def usuario_es_superusuario(user):
    return user.is_authenticated and user.is_superuser


def usuario_es_admin_tic(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name='Administrador TIC').exists()


def usuario_puede_usar_modulos_pvd(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or usuario_es_admin_tic(user) or user.groups.filter(name='Administrador PVD').exists()


def obtener_rol_usuario(user):
    if not user.is_authenticated:
        return 'Sin sesión'
    if user.is_superuser:
        return 'Superusuario'
    grupos = list(user.groups.values_list('name', flat=True))
    return ', '.join(grupos) if grupos else 'Sin rol asignado'


def inicio(request):
    if request.user.is_authenticated:
        return redirect('modulo_puntos:panel_control')
    return redirect('modulo_puntos:login')


def login_usuario(request):
    if request.user.is_authenticated:
        return redirect('modulo_puntos:panel_control')

    next_url = request.GET.get('next') or request.POST.get('next') or reverse('modulo_puntos:panel_control')
    form = LoginForm(request=request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, 'Inicio de sesión correcto.')
            return redirect(next_url)
        messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'registration/login.html', {'form': form, 'next': next_url})


def logout_usuario(request):
    logout(request)
    return redirect('modulo_puntos:login')


@login_required(login_url='/login/')
def perfil_usuario(request):
    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, instance=request.user)
        if form.is_valid():
            usuario = form.save(commit=False)
            nueva_password = form.cleaned_data.get('password1')
            if nueva_password:
                usuario.set_password(nueva_password)
            usuario.save()
            if nueva_password:
                update_session_auth_hash(request, usuario)
            messages.success(request, 'Tu perfil fue actualizado correctamente.')
            return redirect('modulo_puntos:perfil_usuario')
        messages.error(request, 'No se pudo actualizar el perfil. Revisa los datos ingresados.')
    else:
        form = PerfilUsuarioForm(instance=request.user)

    return render(request, 'modulo_puntos/perfil_usuario.html', {
        'form': form,
        'rol_usuario': obtener_rol_usuario(request.user),
    })


@login_required(login_url='/login/')
def panel_control(request):
    context = {
        'total_ciudadanos': Ciudadano.objects.count(),
        'atenciones_registradas': Atencion.objects.count(),
        'total_satisfacciones': Satisfaccion.objects.count(),
        'total_servicios': Servicio.objects.count(),
        'es_superusuario': usuario_es_superusuario(request.user),
        'mostrar_modulos_tic': usuario_es_admin_tic(request.user),
        'mostrar_modulos_pvd': usuario_puede_usar_modulos_pvd(request.user),
        'rol_usuario': obtener_rol_usuario(request.user),
    }
    return render(request, 'modulo_puntos/panel_control.html', context)


@login_required(login_url='/login/')
def consultar_ciudadanos(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    busqueda = request.GET.get('q', '').strip()
    ciudadanos = Ciudadano.objects.all().order_by('-ciu_cdgo')

    if busqueda:
        ciudadanos = ciudadanos.filter(
            Q(ciu_numdoc__icontains=busqueda) |
            Q(ciu_nmbres__icontains=busqueda) |
            Q(ciu_aplldos__icontains=busqueda)
        )

    context = {
        'ciudadanos': ciudadanos,
        'busqueda': busqueda,
        'total_resultados': ciudadanos.count(),
    }
    return render(request, 'modulo_puntos/consultar_ciudadanos.html', context)


@login_required(login_url='/login/')
def registrar_ciudadano(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    form = CiudadanoForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            try:
                ciudadano = form.save()
                print('CIUDADANO GUARDADO:', ciudadano.ciu_cdgo)
                messages.success(request, 'Ciudadano registrado exitosamente en la base de datos.')
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                import traceback
                traceback.print_exc()
                print('ERROR AL GUARDAR CIUDADANO:', str(e))
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            print('ERRORES DEL FORMULARIO CIUDADANO:', form.errors)
            messages.error(request, 'Formulario inválido. Revisa los campos.')

    return render(request, 'modulo_puntos/registrar_ciudadano.html', {'form': form})


@login_required(login_url='/login/')
def registrar_atencion(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    form = AtencionForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            try:
                atencion = form.save()
                print('ATENCION GUARDADA:', atencion.atn_cdgo)
                messages.success(request, 'Atención registrada correctamente en la base de datos.')
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                import traceback
                traceback.print_exc()
                print('ERROR AL GUARDAR ATENCION:', str(e))
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            print('ERRORES DEL FORMULARIO ATENCION:', form.errors)
            messages.error(request, 'No se pudo guardar la atención. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/registrar_atencion.html', {'form': form})


@login_required(login_url='/login/')
def registrar_prestamo(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    form = PrestamoRecursoForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            try:
                prestamo = form.save()
                print('PRESTAMO GUARDADO:', prestamo.prs_cdgo)
                messages.success(request, 'Préstamo registrado correctamente en la base de datos.')
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                import traceback
                traceback.print_exc()
                print('ERROR AL GUARDAR PRESTAMO:', str(e))
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            print('ERRORES DEL FORMULARIO PRESTAMO:', form.errors)
            messages.error(request, 'No se pudo guardar el préstamo. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/registrar_prestamo.html', {'form': form})


@login_required(login_url='/login/')
def registrar_satisfaccion(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    form = SatisfaccionForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            try:
                satisfaccion = form.save()
                print('SATISFACCION GUARDADA:', satisfaccion.sat_cdgo)
                messages.success(request, 'Satisfacción registrada correctamente en la base de datos.')
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                import traceback
                traceback.print_exc()
                print('ERROR AL GUARDAR SATISFACCION:', str(e))
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            print('ERRORES DEL FORMULARIO SATISFACCION:', form.errors)
            messages.error(request, 'No se pudo guardar la satisfacción. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/registrar_satisfaccion.html', {'form': form})


@login_required(login_url='/login/')
def registrar_servicio(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    form = ServicioForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            try:
                servicio = form.save()
                print('SERVICIO GUARDADO:', servicio.srv_cdgo)
                messages.success(request, 'Servicio registrado correctamente en la base de datos.')
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                import traceback
                traceback.print_exc()
                print('ERROR AL GUARDAR SERVICIO:', str(e))
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            print('ERRORES DEL FORMULARIO SERVICIO:', form.errors)
            messages.error(request, 'No se pudo guardar el servicio. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/registrar_servicio.html', {'form': form})


@login_required(login_url='/login/')
def crear_admin_tic(request):
    if not usuario_es_superusuario(request.user):
        messages.error(request, 'No tienes permisos para crear usuarios.')
        return redirect('modulo_puntos:panel_control')

    form = CrearUsuarioForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            grupo, _ = Group.objects.get_or_create(name='Administrador TIC')
            user.groups.add(grupo)
            messages.success(request, 'Administrador TIC creado correctamente en la base de datos.')
            return redirect('modulo_puntos:panel_control')
        messages.error(request, 'No se pudo crear el usuario. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/crear_usuario.html', {
        'form': form,
        'titulo': 'Crear Administrador TIC',
        'rol': 'Administrador TIC'
    })


@login_required(login_url='/login/')
def crear_admin_pvd(request):
    if not usuario_es_superusuario(request.user):
        messages.error(request, 'No tienes permisos para crear usuarios.')
        return redirect('modulo_puntos:panel_control')

    form = CrearUsuarioForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            grupo, _ = Group.objects.get_or_create(name='Administrador PVD')
            user.groups.add(grupo)
            messages.success(request, 'Administrador PVD creado correctamente en la base de datos.')
            return redirect('modulo_puntos:panel_control')
        messages.error(request, 'No se pudo crear el usuario. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/crear_usuario.html', {
        'form': form,
        'titulo': 'Crear Administrador PVD',
        'rol': 'Administrador PVD'
    })