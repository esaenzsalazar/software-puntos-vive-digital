import csv
from datetime import datetime
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Q, Count, Avg
from django.shortcuts import render, redirect
from django.urls import reverse

from .models import Ciudadano, Atencion, Satisfaccion, Servicio, PrestamoRecurso, Recurso, Operador
from .forms import (
    CiudadanoForm,
    AtencionForm,
    SatisfaccionForm,
    ServicioForm,
    PrestamoRecursoForm,
    RecursoForm,
    OperadorForm,
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
    return (
        user.is_superuser
        or usuario_es_admin_tic(user)
        or user.groups.filter(name='Administrador PVD').exists()
    )


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

    return render(request, 'registration/login.html', {
        'form': form,
        'next': next_url
    })


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
        'total_prestamos': PrestamoRecurso.objects.count(),
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
def editar_ciudadano(request, ciu_cdgo):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    try:
        ciudadano = Ciudadano.objects.get(pk=ciu_cdgo)
    except Ciudadano.DoesNotExist:
        messages.error(request, 'El ciudadano no existe.')
        return redirect('modulo_puntos:consultar_ciudadanos')

    form = CiudadanoForm(request.POST or None, instance=ciudadano)

    if request.method == 'POST':
        if form.is_valid():
            try:
                ciudadano = form.save()
                print('CIUDADANO ACTUALIZADO:', ciudadano.ciu_cdgo)
                messages.success(request, 'Ciudadano actualizado correctamente en la base de datos.')
                return redirect('modulo_puntos:consultar_ciudadanos')
            except Exception as e:
                import traceback
                traceback.print_exc()
                print('ERROR AL ACTUALIZAR CIUDADANO:', str(e))
                messages.error(request, f'Error al actualizar en BD: {e}')
        else:
            print('ERRORES DEL FORMULARIO EDICION CIUDADANO:', form.errors)
            messages.error(request, 'No se pudo actualizar el ciudadano. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/editar_ciudadano.html', {
        'form': form,
        'ciudadano': ciudadano,
    })


@login_required(login_url='/login/')
def historial_ciudadano(request, ciu_cdgo):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    try:
        ciudadano = Ciudadano.objects.get(pk=ciu_cdgo)
    except Ciudadano.DoesNotExist:
        messages.error(request, 'El ciudadano no existe.')
        return redirect('modulo_puntos:consultar_ciudadanos')

    atenciones = Atencion.objects.filter(
        ciu_cdgo=ciudadano
    ).select_related(
        'opr_cdgo',
        'prs_cdgo',
        'prs_cdgo__rec_cdgo'
    ).order_by('-atn_fecha', '-atn_hrini')

    for atencion in atenciones:
        atencion.servicios_rel = Servicio.objects.filter(atn_cdgo=atencion)
        atencion.satisfacciones_rel = Satisfaccion.objects.filter(atn_cdgo=atencion)

    return render(request, 'modulo_puntos/historial_ciudadano.html', {
        'ciudadano': ciudadano,
        'atenciones': atenciones,
        'total_atenciones': atenciones.count(),
    })


@login_required(login_url='/login/')
def reportes(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    total_ciudadanos = Ciudadano.objects.count()
    ciudadanos_activos = Ciudadano.objects.filter(ciu_estdo='A').count()

    total_operadores = Operador.objects.count()
    operadores_activos = Operador.objects.filter(opr_estdo='A').count()

    total_atenciones = Atencion.objects.count()
    atenciones_pendientes = Atencion.objects.filter(atn_estdo='P').count()
    atenciones_finalizadas = Atencion.objects.filter(atn_estdo='F').count()
    atenciones_canceladas = Atencion.objects.filter(atn_estdo='C').count()

    total_servicios = Servicio.objects.count()
    total_prestamos = PrestamoRecurso.objects.count()
    prestamos_activos = PrestamoRecurso.objects.filter(prs_fchdev__isnull=True).count()

    satisfaccion_promedio = Satisfaccion.objects.aggregate(
        promedio=Avg('sat_calif')
    )['promedio']

    servicios_por_tipo = Servicio.objects.values('srv_tipo').annotate(
        total=Count('srv_cdgo')
    ).order_by('-total', 'srv_tipo')

    atenciones_por_operador = Atencion.objects.values(
        'opr_cdgo__opr_nmbres',
        'opr_cdgo__opr_aplldos'
    ).annotate(
        total=Count('atn_cdgo')
    ).order_by('-total')

    atenciones_recientes = Atencion.objects.select_related(
        'ciu_cdgo',
        'opr_cdgo'
    ).order_by('-atn_fecha', '-atn_hrini')[:10]

    return render(request, 'modulo_puntos/reportes.html', {
        'total_ciudadanos': total_ciudadanos,
        'ciudadanos_activos': ciudadanos_activos,
        'total_operadores': total_operadores,
        'operadores_activos': operadores_activos,
        'total_atenciones': total_atenciones,
        'atenciones_pendientes': atenciones_pendientes,
        'atenciones_finalizadas': atenciones_finalizadas,
        'atenciones_canceladas': atenciones_canceladas,
        'total_servicios': total_servicios,
        'total_prestamos': total_prestamos,
        'prestamos_activos': prestamos_activos,
        'satisfaccion_promedio': satisfaccion_promedio,
        'servicios_por_tipo': servicios_por_tipo,
        'atenciones_por_operador': atenciones_por_operador,
        'atenciones_recientes': atenciones_recientes,
    })

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
def registrar_recurso(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    form = RecursoForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            try:
                recurso = form.save()
                print('RECURSO GUARDADO:', recurso.rec_cdgo)
                messages.success(request, 'Recurso registrado correctamente en la base de datos.')
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                import traceback
                traceback.print_exc()
                print('ERROR AL GUARDAR RECURSO:', str(e))
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            print('ERRORES DEL FORMULARIO RECURSO:', form.errors)
            messages.error(request, 'No se pudo guardar el recurso. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/registrar_recurso.html', {'form': form})


@login_required(login_url='/login/')
def registrar_operador(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    form = OperadorForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            try:
                operador = form.save()
                print('OPERADOR GUARDADO:', operador.opr_cdgo)
                messages.success(request, 'Operador registrado correctamente en la base de datos.')
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                import traceback
                traceback.print_exc()
                print('ERROR AL GUARDAR OPERADOR:', str(e))
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            print('ERRORES DEL FORMULARIO OPERADOR:', form.errors)
            messages.error(request, 'No se pudo guardar el operador. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/registrar_operador.html', {'form': form})


@login_required(login_url='/login/')
def consultar_operadores(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    busqueda = request.GET.get('q', '').strip()
    operadores = Operador.objects.all().order_by('-opr_cdgo')

    if busqueda:
        operadores = operadores.filter(
            Q(opr_numdoc__icontains=busqueda) |
            Q(opr_nmbres__icontains=busqueda) |
            Q(opr_aplldos__icontains=busqueda)
        )

    return render(request, 'modulo_puntos/consultar_operadores.html', {
        'operadores': operadores,
        'busqueda': busqueda,
        'total_resultados': operadores.count(),
    })


@login_required(login_url='/login/')
def editar_operador(request, opr_cdgo):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    try:
        operador = Operador.objects.get(pk=opr_cdgo)
    except Operador.DoesNotExist:
        messages.error(request, 'El operador no existe.')
        return redirect('modulo_puntos:consultar_operadores')

    form = OperadorForm(request.POST or None, instance=operador)

    if request.method == 'POST':
        if form.is_valid():
            try:
                operador = form.save()
                print('OPERADOR ACTUALIZADO:', operador.opr_cdgo)
                messages.success(request, 'Operador actualizado correctamente en la base de datos.')
                return redirect('modulo_puntos:consultar_operadores')
            except Exception as e:
                import traceback
                traceback.print_exc()
                print('ERROR AL ACTUALIZAR OPERADOR:', str(e))
                messages.error(request, f'Error al actualizar en BD: {e}')
        else:
            print('ERRORES DEL FORMULARIO EDICION OPERADOR:', form.errors)
            messages.error(request, 'No se pudo actualizar el operador. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/editar_operador.html', {
        'form': form,
        'operador': operador,
    })

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

# --- NUEVA FUNCIONALIDAD: EXPORTAR A CSV ---
@login_required(login_url='/login/')
def exportar_atenciones_csv(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    response = HttpResponse(content_type='text/csv')
    # Nombre del archivo con la fecha actual
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    response['Content-Disposition'] = f'attachment; filename="Reporte_Atenciones_PVD_{fecha_actual}.csv"'

    writer = csv.writer(response)
    # Encabezados del Excel
    writer.writerow(['ID Atención', 'Fecha', 'Hora Inicio', 'Hora Fin', 'Estado', 'Ciudadano (Documento)', 'Operador', 'Observaciones'])

    atenciones = Atencion.objects.select_related('ciu_cdgo', 'opr_cdgo').order_by('-atn_fecha', '-atn_hrini')

    for atencion in atenciones:
        ciudadano_info = f"{atencion.ciu_cdgo.ciu_nmbres} {atencion.ciu_cdgo.ciu_aplldos} ({atencion.ciu_cdgo.ciu_numdoc})" if atencion.ciu_cdgo else "N/A"
        operador_info = f"{atencion.opr_cdgo.opr_nmbres} {atencion.opr_cdgo.opr_aplldos}" if atencion.opr_cdgo else "N/A"
        estado_dict = dict(Atencion.ESTADO_CHOICES)
        estado_display = estado_dict.get(atencion.atn_estdo, atencion.atn_estdo)

        writer.writerow([
            atencion.atn_cdgo,
            atencion.atn_fecha,
            atencion.atn_hrini,
            atencion.atn_hrfin if atencion.atn_hrfin else "N/A",
            estado_display,
            ciudadano_info,
            operador_info,
            atencion.atn_obs if atencion.atn_obs else "Sin observaciones"
        ])

    return response