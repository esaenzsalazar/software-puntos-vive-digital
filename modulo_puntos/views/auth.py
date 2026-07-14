import logging
import mimetypes
from io import BytesIO
from django import forms
from datetime import datetime, date as date_type, time as time_type
from django.conf import settings
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, Permission, User
from django.db import transaction
from django.db.models import Q, Count, Avg, Max, Prefetch
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.core.cache import cache
from django.views.decorators.csrf import ensure_csrf_cookie

from ..models import (
    Ciudadano, Atencion, Satisfaccion, Servicio, PrestamoRecurso,
    Recurso, PuntoViveDigital, Sala, UserProfile, AuditoriaAccion,
    PermisoDefinicion, PermisoRol, PermisoUsuario, HabilitacionSala,
    Curso, SesionCurso, InscripcionCurso, AsistenciaSesion,
    MantenimientoEquipo, Evidencia,
)
from ..forms import (
    CiudadanoForm, AtencionForm, SatisfaccionForm, ServicioForm,
    PrestamoRecursoForm, RecursoForm, LoginForm, PerfilUsuarioForm,
    CrearUsuarioForm, CrearUsuarioSistemaForm, EditarAdminPvdForm, PuntoViveDigitalForm, SalaForm, PermisoDefinicionForm,
    HabilitacionSalaForm, CursoForm, SesionCursoForm, InscripcionCursoForm,
    MantenimientoEquipoForm, EvidenciaForm,
)
from ..utils import registrar_auditoria, tiene_permiso, sincronizar_admin_a_cargo

logger = logging.getLogger('modulo_puntos')


from ._helpers import (
    usuario_es_superusuario, usuario_es_admin_tic,
    usuario_necesita_seleccionar_pvd, usuario_puede_usar_modulos_pvd,
    obtener_rol_usuario, obtener_pvd_activo_id, pvd_permitido,
    exigir_pvd_activo_para_admin_pvd,
)

# ── AUTENTICACIÓN ──────────────────────────────────────────────────────────────


_LOGIN_MAX_INTENTOS = 5
_LOGIN_BLOQUEO_SEGUNDOS = 300  # 5 minutos


@never_cache
@ensure_csrf_cookie
def login_usuario(request):
    if request.user.is_authenticated:
        return redirect('modulo_puntos:panel_control')

    raw_next = request.GET.get('next') or request.POST.get('next') or ''
    if raw_next and url_has_allowed_host_and_scheme(raw_next, allowed_hosts={request.get_host()}):
        next_url = raw_next
    else:
        next_url = reverse('modulo_puntos:panel_control')

    # Control de intentos fallidos por IP (última entrada XFF = puesta por proxy, no por cliente)
    _xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    ip = _xff.split(',')[-1].strip() if _xff else request.META.get('REMOTE_ADDR', 'unknown')
    cache_key = f'login_intentos_{ip}'
    bloqueo_key = f'login_bloqueo_{ip}'

    pvd_count = PuntoViveDigital.objects.filter(estado='A').count()

    bloqueado_hasta = cache.get(bloqueo_key)
    segundos_restantes = 0
    if bloqueado_hasta:
        import time
        segundos_restantes = max(0, int(bloqueado_hasta - time.time()))
        if segundos_restantes > 0:
            minutos = segundos_restantes // 60
            segundos = segundos_restantes % 60
            messages.error(request, f'Demasiados intentos fallidos. Espera {minutos}m {segundos}s antes de intentar de nuevo.')
            return render(request, 'registration/login.html', {
                'form': LoginForm(),
                'next': next_url,
                'bloqueado': True,
                'segundos_restantes': segundos_restantes,
                'pvd_count': pvd_count,
            })

    form = LoginForm(request=request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            cache.delete(cache_key)
            cache.delete(bloqueo_key)
            login(request, user)
            messages.success(request, 'Inicio de sesión correcto.')
            if usuario_necesita_seleccionar_pvd(user):
                try:
                    profile = user.pvd_profile
                    if profile.punto_asignado_id and not profile.pvd_temporal_id:
                        pvd = profile.punto_asignado
                        if pvd.estado == 'A':
                            request.session['pvd_activo_id'] = pvd.pk
                            request.session['pvd_nombre'] = pvd.nombre
                            messages.success(request, f'Trabajando en: {pvd.nombre}')
                            return redirect(next_url)
                except UserProfile.DoesNotExist:
                    pass
                return redirect('modulo_puntos:seleccionar_pvd_view')
            return redirect(next_url)
        else:
            import time
            intentos = cache.get(cache_key, 0) + 1
            cache.set(cache_key, intentos, _LOGIN_BLOQUEO_SEGUNDOS)
            restantes = _LOGIN_MAX_INTENTOS - intentos
            if intentos >= _LOGIN_MAX_INTENTOS:
                cache.set(bloqueo_key, time.time() + _LOGIN_BLOQUEO_SEGUNDOS, _LOGIN_BLOQUEO_SEGUNDOS)
                cache.delete(cache_key)
                messages.error(request, f'Cuenta bloqueada por {_LOGIN_BLOQUEO_SEGUNDOS // 60} minutos por múltiples intentos fallidos.')
            else:
                messages.error(request, f'Usuario o contraseña incorrectos. Te quedan {restantes} intento(s).')

    return render(request, 'registration/login.html', {'form': form, 'next': next_url, 'pvd_count': pvd_count})


@login_required(login_url='/login/')
def logout_usuario(request):
    if request.method != 'POST':
        return redirect('modulo_puntos:panel_control')
    logout(request)
    return redirect('modulo_puntos:login')


# ── PERFIL ─────────────────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def perfil_usuario(request):
    if request.method == 'POST':
        if request.POST.get('cambiar_password'):
            old_pw = request.POST.get('old_password', '').strip()
            new_pw1 = request.POST.get('new_password1', '').strip()
            new_pw2 = request.POST.get('new_password2', '').strip()
            if not request.user.check_password(old_pw):
                messages.error(request, 'La contraseña actual no es correcta.')
            elif len(new_pw1) < 8:
                messages.error(request, 'La nueva contraseña debe tener al menos 8 caracteres.')
            elif new_pw1 != new_pw2:
                messages.error(request, 'Las contraseñas nuevas no coinciden.')
            else:
                request.user.set_password(new_pw1)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Contraseña cambiada correctamente.')
            return redirect('modulo_puntos:perfil_usuario')

        form = PerfilUsuarioForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil fue actualizado correctamente.')
            return redirect('modulo_puntos:perfil_usuario')
        messages.error(request, 'No se pudo actualizar el perfil. Revisa los datos ingresados.')
    else:
        form = PerfilUsuarioForm(instance=request.user)

    return render(request, 'modulo_puntos/perfil_usuario.html', {
        'form': form,
        'rol_usuario': obtener_rol_usuario(request.user),
    })


# ── PANEL DE CONTROL ───────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def panel_control(request):
    user = request.user

    # Admin PVD debe seleccionar PVD antes de entrar al panel
    if usuario_necesita_seleccionar_pvd(user):
        pvd_id_session = request.session.get('pvd_activo_id')
        if not pvd_id_session:
            messages.info(request, 'Selecciona un Punto Vive Digital para comenzar.')
            return redirect('modulo_puntos:seleccionar_pvd_view')

    from datetime import date as date_cls
    hoy = date_cls.today()
    context = {
        'total_ciudadanos': Ciudadano.objects.count(),
        'atenciones_registradas': Atencion.objects.count(),
        'total_satisfacciones': Satisfaccion.objects.count(),
        'total_servicios': Servicio.objects.count(),
        'total_prestamos': PrestamoRecurso.objects.count(),
        'total_pvds': PuntoViveDigital.objects.count(),
        'total_recursos': Recurso.objects.count(),
        'total_cursos': Curso.objects.count(),
        'atenciones_hoy_global': Atencion.objects.filter(fecha=hoy).count(),

        'es_superusuario': usuario_es_superusuario(user),
        'es_admin_tic_only': user.groups.filter(name='Administrador TIC').exists() and not user.is_superuser,
        'es_admin_pvd_only': user.groups.filter(name='Administrador PVD').exists() and not usuario_es_admin_tic(user),
        'mostrar_modulos_tic': usuario_es_admin_tic(user),
        'mostrar_modulos_pvd': usuario_puede_usar_modulos_pvd(user),
        'rol_usuario': obtener_rol_usuario(user),
        'pvd_activo': None,
    }
    pvd_id = request.session.get('pvd_activo_id')
    if pvd_id:
        pvd_activo = PuntoViveDigital.objects.filter(pk=pvd_id, estado='A').first()
        context['pvd_activo'] = pvd_activo
        if pvd_activo:
            context['pvd_ciudadanos']     = Ciudadano.objects.filter(punto_vive_digital_id=pvd_id).count()
            context['pvd_atenciones']     = Atencion.objects.filter(punto_vive_digital_id=pvd_id).count()
            context['pvd_salas']          = Sala.objects.filter(punto_vive_digital_id=pvd_id).count()
            context['pvd_cursos']         = Curso.objects.filter(punto_vive_digital_id=pvd_id).count()
            context['pvd_mantenimientos'] = MantenimientoEquipo.objects.filter(punto_vive_digital_id=pvd_id).count()
            context['pvd_habilitaciones'] = HabilitacionSala.objects.filter(sala__punto_vive_digital_id=pvd_id).count()
            context['atenciones_hoy'] = Atencion.objects.filter(punto_vive_digital_id=pvd_id, fecha=hoy).count()
            context['atenciones_pendientes'] = (
                Atencion.objects
                .filter(punto_vive_digital_id=pvd_id, estado='P')
                .select_related('ciudadano')
                .order_by('-fecha', '-pk')[:10]
            )
    return render(request, 'modulo_puntos/panel_control.html', context)


# ── SELECCIÓN DE PVD ───────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def seleccionar_pvd_view(request):
    sin_asignacion = False
    permanente_id = None
    temporal_id = None

    conteos = dict(
        total_ciudadanos=Count('ciudadano', filter=Q(ciudadano__estado='A'), distinct=True),
        total_atenciones=Count('atencion', distinct=True),
        total_recursos=Count('recurso', filter=Q(recurso__estado='A'), distinct=True),
        total_salas=Count('sala', filter=Q(sala__estado='A'), distinct=True),
    )

    if usuario_necesita_seleccionar_pvd(request.user):
        try:
            profile = request.user.pvd_profile
            if profile.punto_asignado_id:
                permanente_id = profile.punto_asignado_id
                pvd_ids = [profile.punto_asignado_id]
                if profile.pvd_temporal_id:
                    temporal_id = profile.pvd_temporal_id
                    pvd_ids.append(profile.pvd_temporal_id)
                pvds = PuntoViveDigital.objects.filter(pk__in=pvd_ids, estado='A').annotate(**conteos).order_by('nombre')
            else:
                # Admin PVD sin PVD asignado: bloquear, no mostrar lista
                pvds = PuntoViveDigital.objects.none()
                sin_asignacion = True
        except UserProfile.DoesNotExist:
            pvds = PuntoViveDigital.objects.none()
            sin_asignacion = True
    else:
        pvds = PuntoViveDigital.objects.filter(estado='A').annotate(**conteos).order_by('nombre')

    pvds = list(pvds)
    for pvd in pvds:
        pvd.es_permanente = (pvd.pk == permanente_id)
        pvd.es_temporal = (pvd.pk == temporal_id)

    return render(request, 'modulo_puntos/seleccionar_pvd.html', {
        'pvds': pvds,
        'sin_asignacion': sin_asignacion,
    })


@login_required(login_url='/login/')
def seleccionar_pvd(request, pvd_cdgo):
    pvd = get_object_or_404(PuntoViveDigital, pk=pvd_cdgo, estado='A')

    if usuario_necesita_seleccionar_pvd(request.user):
        try:
            profile = request.user.pvd_profile
            if not profile.punto_asignado_id:
                messages.error(request, 'No tienes ningún Punto Vive Digital asignado. Contacta al Administrador TIC.')
                return redirect('modulo_puntos:seleccionar_pvd_view')
            pvd_ids_permitidos = [profile.punto_asignado_id]
            if profile.pvd_temporal_id:
                pvd_ids_permitidos.append(profile.pvd_temporal_id)
            if pvd_cdgo not in pvd_ids_permitidos:
                messages.error(request, 'No tienes permiso para acceder a ese Punto Vive Digital.')
                return redirect('modulo_puntos:seleccionar_pvd_view')
        except UserProfile.DoesNotExist:
            messages.error(request, 'No tienes ningún Punto Vive Digital asignado. Contacta al Administrador TIC.')
            return redirect('modulo_puntos:seleccionar_pvd_view')

    request.session['pvd_activo_id'] = pvd.pk
    request.session['pvd_nombre'] = pvd.nombre
    messages.success(request, f'Trabajando en: {pvd.nombre}')
    return redirect('modulo_puntos:panel_control')


# ── AYUDA ──────────────────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def ayuda_sistema(request):
    return render(request, 'modulo_puntos/ayuda.html', {
        'rol_usuario': obtener_rol_usuario(request.user),
    })


