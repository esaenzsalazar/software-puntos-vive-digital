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

# ── GESTIÓN DE CIUDADANOS ──────────────────────────────────────────────────────

@login_required(login_url='/login/')
def consultar_ciudadanos(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    busqueda   = request.GET.get('q', '').strip()
    pvd_filtro = request.GET.get('pvd', '').strip()
    estado_filtro = request.GET.get('estado', 'A').strip()  # Por defecto solo activos

    # Los ciudadanos son una población compartida: cualquier PVD puede consultar,
    # atender y editar a un ciudadano sin importar en qué PVD fue registrado.
    ciudadanos = Ciudadano.objects.select_related('punto_vive_digital').order_by('-pk')

    if pvd_filtro:
        ciudadanos = ciudadanos.filter(punto_vive_digital_id=pvd_filtro)

    if estado_filtro in ('A', 'I'):
        ciudadanos = ciudadanos.filter(estado=estado_filtro)
    # '' → todos (activos + inactivos)

    if busqueda:
        ciudadanos = ciudadanos.filter(
            Q(numero_documento__icontains=busqueda) |
            Q(primer_nombre__icontains=busqueda)   |
            Q(primer_apellido__icontains=busqueda)  |
            Q(segundo_nombre__icontains=busqueda)   |
            Q(segundo_apellido__icontains=busqueda) |
            Q(telefono__icontains=busqueda)         |
            Q(barrio__icontains=busqueda)
        )

    total_resultados = ciudadanos.count()
    paginator = Paginator(ciudadanos, 25)
    page_obj  = paginator.get_page(request.GET.get('page'))

    pvds_para_filtro = PuntoViveDigital.objects.filter(estado='A').order_by('nombre')

    return render(request, 'modulo_puntos/consultar_ciudadanos.html', {
        'ciudadanos': page_obj,
        'page_obj': page_obj,
        'busqueda': busqueda,
        'pvd_filtro': pvd_filtro,
        'estado_filtro': estado_filtro,
        'pvds_para_filtro': pvds_para_filtro,
        'total_resultados': total_resultados,
    })


@login_required(login_url='/login/')
def registrar_ciudadano(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    # Restricción de sesión: sin PVD activo no se puede registrar ningún ciudadano,
    # independientemente del rol (incluyendo superusuario).
    pvd_id = request.session.get('pvd_activo_id')
    if not pvd_id:
        messages.warning(
            request,
            'Debes ingresar a un Punto Vive Digital antes de registrar un ciudadano. '
            'Selecciona uno de la lista.'
        )
        return redirect('modulo_puntos:seleccionar_pvd_view')

    pvd_activo = PuntoViveDigital.objects.filter(pk=pvd_id, estado='A').first()
    if not pvd_activo:
        # El PVD en sesión fue desactivado o eliminado
        del request.session['pvd_activo_id']
        messages.warning(request, 'El Punto Vive Digital de tu sesión ya no está disponible. Selecciona otro.')
        return redirect('modulo_puntos:seleccionar_pvd_view')

    form = CiudadanoForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                ciudadano = form.save(commit=False)
                ciudadano.punto_vive_digital_id = pvd_id   # siempre obligatorio
                ciudadano.save()
                registrar_auditoria(
                    request, 'CREATE', 'Ciudadano', ciudadano.pk,
                    f'Ciudadano registrado en {pvd_activo.nombre}: {ciudadano.get_nombre_completo()}'
                )
                messages.success(request, 'Ciudadano registrado exitosamente en la base de datos.')
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                logger.error('Error al guardar ciudadano: %s', e, exc_info=True)
                messages.error(request, 'Error al guardar los datos. Inténtalo de nuevo.')
        else:
            messages.error(request, 'Formulario inválido. Revisa los campos.')

    return render(request, 'modulo_puntos/registrar_ciudadano.html', {
        'form': form,
        'pvd_activo': pvd_activo,
    })


@login_required(login_url='/login/')
def editar_ciudadano(request, ciu_cdgo):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    # Los ciudadanos son una población compartida entre PVDs: cualquier Admin PVD
    # puede editar los datos de un ciudadano, sin importar dónde fue registrado.
    ciudadano = get_object_or_404(Ciudadano, pk=ciu_cdgo)

    form = CiudadanoForm(request.POST or None, instance=ciudadano)
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Ciudadano actualizado correctamente en la base de datos.')
                return redirect('modulo_puntos:consultar_ciudadanos')
            except Exception as e:
                logger.error('Error al actualizar ciudadano %s: %s', ciu_cdgo, e, exc_info=True)
                messages.error(request, 'Error al guardar los datos. Inténtalo de nuevo.')
        else:
            messages.error(request, 'No se pudo actualizar el ciudadano. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/editar_ciudadano.html', {
        'form': form,
        'ciudadano': ciudadano,
    })


@login_required(login_url='/login/')
def desactivar_ciudadano(request, ciu_cdgo):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')
    if request.method != 'POST':
        return redirect('modulo_puntos:consultar_ciudadanos')
    # Los ciudadanos son una población compartida entre PVDs.
    ciudadano = get_object_or_404(Ciudadano, pk=ciu_cdgo)
    nuevo_estado = 'I' if ciudadano.estado == 'A' else 'A'
    ciudadano.estado = nuevo_estado
    ciudadano.save(update_fields=['estado'])
    etiqueta = 'desactivado' if nuevo_estado == 'I' else 'reactivado'
    registrar_auditoria(request, 'UPDATE', 'Ciudadano', ciudadano.pk,
                        f'Ciudadano {etiqueta}: {ciudadano.get_nombre_completo()}')
    messages.success(request, f'Ciudadano {etiqueta} correctamente.')
    return redirect('modulo_puntos:consultar_ciudadanos')


@login_required(login_url='/login/')
def historial_ciudadano(request, ciu_cdgo):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    # Los ciudadanos son una población compartida entre PVDs: cualquier Admin PVD
    # puede consultar el historial completo de un ciudadano (incluye atenciones
    # prestadas en cualquier PVD), sin importar dónde fue registrado.
    ciudadano = get_object_or_404(Ciudadano, pk=ciu_cdgo)

    atenciones = list(
        Atencion.objects.filter(ciudadano=ciudadano)
        .select_related('operador', 'prestamo', 'prestamo__recurso')
        .prefetch_related(
            Prefetch('servicio_set', queryset=Servicio.objects.order_by('pk'), to_attr='servicios_rel'),
            Prefetch('satisfaccion_set', to_attr='satisfacciones_rel'),
        )
        .order_by('-fecha', '-hora_inicio')
    )

    return render(request, 'modulo_puntos/historial_ciudadano.html', {
        'ciudadano': ciudadano,
        'atenciones': atenciones,
        'total_atenciones': len(atenciones),
    })


@login_required(login_url='/login/')
def ciudadanos_pendientes(request):
    if not (request.user.is_superuser or usuario_es_admin_tic(request.user)):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    pendientes = list(Ciudadano.objects.filter(estado='P').order_by('-fecha_registro'))
    return render(request, 'modulo_puntos/ciudadanos_pendientes.html', {
        'ciudadanos_pendientes': pendientes,
        'total_pendientes': len(pendientes),
    })


@login_required(login_url='/login/')
def aprobar_ciudadano(request, ciu_id):
    if not (request.user.is_superuser or usuario_es_admin_tic(request.user)):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('modulo_puntos:panel_control')

    if request.method != 'POST':
        return redirect('modulo_puntos:ciudadanos_pendientes')

    ciudadano = get_object_or_404(Ciudadano, pk=ciu_id, estado='P')
    nombre = ciudadano.get_nombre_completo()
    ciudadano.estado = 'A'
    ciudadano.save()
    messages.success(request, f'Ciudadano {nombre} aprobado exitosamente.')
    return redirect('modulo_puntos:ciudadanos_pendientes')


@login_required(login_url='/login/')
def rechazar_ciudadano(request, ciu_id):
    if not (request.user.is_superuser or usuario_es_admin_tic(request.user)):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('modulo_puntos:panel_control')

    if request.method != 'POST':
        return redirect('modulo_puntos:ciudadanos_pendientes')

    ciudadano = get_object_or_404(Ciudadano, pk=ciu_id, estado='P')
    nombre = ciudadano.get_nombre_completo()
    ciudadano.delete()
    messages.success(request, f'Registro de {nombre} rechazado y eliminado.')
    return redirect('modulo_puntos:ciudadanos_pendientes')


# ── REGISTRO CIUDADANO PÚBLICO (sin login) ─────────────────────────────────────

def registrar_usuario_ciudadano(request):
    _xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    _ip = _xff.split(',')[-1].strip() if _xff else request.META.get('REMOTE_ADDR', 'unknown')
    _rate_key = f'reg_pub_{_ip}'
    if cache.get(_rate_key, 0) >= 5:
        return render(request, 'modulo_puntos/registrar_usuario_ciudadano.html', {
            'form': CiudadanoForm(),
            'bloqueado': True,
        }, status=429)

    form = CiudadanoForm(request.POST or None)
    if request.method == 'POST':
        cache.set(_rate_key, cache.get(_rate_key, 0) + 1, 300)
        if form.is_valid():
            ciudadano = form.save(commit=False)
            ciudadano.estado = 'P'
            # Autorregistro público: no hay PVD activo en sesión (no requiere login),
            # así que se asigna al primer PVD activo por defecto; el Admin PVD
            # puede reasignarlo al aprobar el registro.
            ciudadano.punto_vive_digital = PuntoViveDigital.objects.filter(estado='A').order_by('nombre').first()
            ciudadano.save()
            return redirect('modulo_puntos:registro_exitoso')
        messages.error(request, 'Revisa los datos ingresados.')
    return render(request, 'modulo_puntos/registrar_usuario_ciudadano.html', {'form': form})


def registro_exitoso(request):
    return render(request, 'modulo_puntos/registro_exitoso.html')


