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

# ── GESTIÓN DE PUNTOS VIVE DIGITAL ─────────────────────────────────────────────

@login_required(login_url='/login/')
def validar_nombre_pvd(request):
    nombre = request.GET.get('nombre', '').strip()
    exclude_id = request.GET.get('exclude_id', '').strip()
    if not nombre:
        return JsonResponse({'disponible': True})
    qs = PuntoViveDigital.objects.filter(nombre__iexact=nombre)
    if exclude_id:
        try:
            qs = qs.exclude(pk=int(exclude_id))
        except ValueError:
            pass
    return JsonResponse({'disponible': not qs.exists()})


@login_required(login_url='/login/')
def lista_pvd(request):
    if not usuario_es_admin_tic(request.user):
        messages.error(request, 'No tienes permisos para gestionar PVDs.')
        return redirect('modulo_puntos:panel_control')
    puede_eliminar_pvd = tiene_permiso(request.user, 'infraestructura.eliminar_pvd')

    # Conteos en una sola query con annotate
    pvds = (
        PuntoViveDigital.objects
        .order_by('nombre')
        .annotate(
            total_atenciones=Count('atencion', distinct=True),
            total_ciudadanos=Count(
                'ciudadano',
                filter=Q(ciudadano__estado='A'),
                distinct=True,
            ),
        )
    )

    # Admins por PVD en una sola query
    from ..models import UserProfile
    profiles = UserProfile.objects.select_related('usuario', 'punto_asignado').filter(punto_asignado__isnull=False)
    admin_por_pvd = {}
    for p in profiles:
        admin_por_pvd.setdefault(p.punto_asignado_id, []).append(p.usuario)

    pvd_list = []
    for pvd in pvds:
        pvd.admins = admin_por_pvd.get(pvd.pk, [])
        pvd_list.append(pvd)

    return render(request, 'modulo_puntos/lista_pvd.html', {
        'pvds': pvd_list,
        'puede_eliminar_pvd': puede_eliminar_pvd,
    })


@login_required(login_url='/login/')
def crear_pvd(request):
    if not usuario_es_admin_tic(request.user):
        messages.error(request, 'No tienes permisos para crear PVDs.')
        return redirect('modulo_puntos:panel_control')

    initial = {'nombre': 'PVD '}
    form = PuntoViveDigitalForm(request.POST or None, initial=initial)
    if request.method == 'POST':
        if form.is_valid():
            pvd = form.save()
            registrar_auditoria(request, 'CREATE', 'PuntoViveDigital', pvd.pk, f'PVD creado: {pvd.nombre}')
            request.session['pvd_pendiente_id'] = pvd.pk
            request.session['pvd_pendiente_nombre'] = pvd.nombre
            messages.success(
                request,
                f'PVD "{pvd.nombre}" creado correctamente. Ahora crea el Administrador PVD que lo tendrá a cargo.'
            )
            return redirect('modulo_puntos:crear_usuario_sistema')
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/form_pvd.html', {
        'form': form,
        'titulo': 'Nuevo Punto Vive Digital',
        'accion': 'crear',
    })


@login_required(login_url='/login/')
def editar_pvd(request, pvd_cdgo):
    if not usuario_es_admin_tic(request.user):
        messages.error(request, 'No tienes permisos para editar PVDs.')
        return redirect('modulo_puntos:panel_control')

    pvd = get_object_or_404(PuntoViveDigital, pk=pvd_cdgo)
    form = PuntoViveDigitalForm(request.POST or None, instance=pvd)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            cache.delete('pvds_disponibles_activos')
            registrar_auditoria(request, 'UPDATE', 'PuntoViveDigital', pvd.pk, f'PVD editado: {pvd.nombre}')
            messages.success(request, f'PVD "{pvd.nombre}" actualizado correctamente.')
            return redirect('modulo_puntos:lista_pvd')
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/form_pvd.html', {
        'form': form,
        'titulo': f'Editar PVD: {pvd.nombre}',
        'accion': 'editar',
        'pvd': pvd,
    })


@login_required(login_url='/login/')
def activar_pvd(request, pvd_cdgo):
    if not usuario_es_admin_tic(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')
    if request.method != 'POST':
        return redirect('modulo_puntos:lista_pvd')

    pvd = get_object_or_404(PuntoViveDigital, pk=pvd_cdgo)
    pvd.estado = 'I' if pvd.estado == 'A' else 'A'
    pvd.save()
    estado_str = 'activado' if pvd.estado == 'A' else 'desactivado'
    cache.delete('pvds_disponibles_activos')
    registrar_auditoria(request, 'UPDATE', 'PuntoViveDigital', pvd.pk, f'PVD {estado_str}: {pvd.nombre}')
    messages.success(request, f'PVD "{pvd.nombre}" {estado_str} correctamente.')
    return redirect('modulo_puntos:lista_pvd')


@login_required(login_url='/login/')
def eliminar_pvd(request, pvd_cdgo):
    messages.error(request, 'La eliminación de Puntos Vive Digital está deshabilitada. Usa la opción de activar/desactivar.')
    return redirect('modulo_puntos:lista_pvd')


