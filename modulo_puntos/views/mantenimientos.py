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

# ==============================================================================
# MANTENIMIENTO DE EQUIPOS
# ==============================================================================

@login_required(login_url='/login/')
def lista_mantenimientos(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'mantenimiento.ver'):
        messages.error(request, 'No tienes permiso para ver mantenimientos.')
        return redirect('modulo_puntos:panel_control')

    pvd_id = request.session.get('pvd_activo_id')
    es_admin_tic = usuario_es_admin_tic(request.user)

    if es_admin_tic:
        qs = MantenimientoEquipo.objects.select_related('punto_vive_digital', 'realizado_por').all()
    elif pvd_id:
        qs = MantenimientoEquipo.objects.filter(punto_vive_digital_id=pvd_id).select_related('punto_vive_digital', 'realizado_por')
    else:
        qs = MantenimientoEquipo.objects.none()

    tipo_filtro = request.GET.get('tipo', '')
    fecha_desde_filtro = request.GET.get('fecha_desde', '').strip()
    fecha_hasta_filtro = request.GET.get('fecha_hasta', '').strip()
    q_filtro = request.GET.get('q', '').strip()
    if tipo_filtro:
        qs = qs.filter(tipo=tipo_filtro)
    if fecha_desde_filtro:
        qs = qs.filter(fecha__gte=fecha_desde_filtro)
    if fecha_hasta_filtro:
        qs = qs.filter(fecha__lte=fecha_hasta_filtro)
    if q_filtro:
        qs = qs.filter(
            Q(equipos_intervenidos__icontains=q_filtro) |
            Q(descripcion__icontains=q_filtro) |
            Q(realizado_por__first_name__icontains=q_filtro) |
            Q(realizado_por__last_name__icontains=q_filtro)
        )

    paginator = Paginator(qs.order_by('-fecha'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'modulo_puntos/mantenimientos/lista_mantenimientos.html', {
        'mantenimientos': page_obj,
        'page_obj': page_obj,
        'tipo_filtro': tipo_filtro,
        'fecha_desde_filtro': fecha_desde_filtro,
        'fecha_hasta_filtro': fecha_hasta_filtro,
        'q_filtro': q_filtro,
        'tipos': MantenimientoEquipo.TIPO_CHOICES,
        'es_admin_tic': es_admin_tic,
        'total_mantenimientos': qs.count(),
    })


@login_required(login_url='/login/')
def crear_mantenimiento(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')
    # Solo el Admin PVD y el Superusuario pueden registrar mantenimientos
    _es_admin_pvd = (
        not request.user.is_superuser
        and not usuario_es_admin_tic(request.user)
        and request.user.groups.filter(name='Administrador PVD').exists()
    )
    if not _es_admin_pvd and not request.user.is_superuser:
        messages.error(request, 'Solo el Administrador PVD o el Superusuario pueden registrar mantenimientos de equipos.')
        return redirect('modulo_puntos:lista_mantenimientos')
    if not tiene_permiso(request.user, 'mantenimiento.crear'):
        messages.error(request, 'No tienes permiso para registrar mantenimientos.')
        return redirect('modulo_puntos:lista_mantenimientos')

    pvd_id = request.session.get('pvd_activo_id')
    if not pvd_id:
        messages.warning(request, 'Debes ingresar a un Punto Vive Digital antes de registrar un mantenimiento.')
        return redirect('modulo_puntos:seleccionar_pvd_view')

    form = MantenimientoEquipoForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            mant = form.save(commit=False)
            if pvd_id:
                mant.punto_vive_digital_id = pvd_id
            mant.realizado_por = request.user
            mant.save()
            registrar_auditoria(request, 'CREATE', 'MantenimientoEquipo', mant.pk,
                                f'Mantenimiento {mant.get_tipo_display()} registrado: {mant.fecha}')
            messages.success(request, 'Mantenimiento registrado correctamente.')
            return redirect('modulo_puntos:lista_mantenimientos')
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/mantenimientos/form_mantenimiento.html', {
        'form': form,
        'titulo': 'Registrar Mantenimiento',
        'accion': 'crear',
    })


@login_required(login_url='/login/')
def editar_mantenimiento(request, mant_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'mantenimiento.editar'):
        messages.error(request, 'No tienes permiso para editar mantenimientos.')
        return redirect('modulo_puntos:lista_mantenimientos')

    mant = get_object_or_404(MantenimientoEquipo, pk=mant_id)
    if not pvd_permitido(request, mant.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para editar mantenimientos de otro PVD.')
        return redirect('modulo_puntos:lista_mantenimientos')

    form = MantenimientoEquipoForm(request.POST or None, instance=mant)

    if request.method == 'POST':
        if form.is_valid():
            mant = form.save()
            registrar_auditoria(request, 'UPDATE', 'MantenimientoEquipo', mant.pk,
                                f'Mantenimiento editado: {mant.fecha}')
            messages.success(request, 'Mantenimiento actualizado correctamente.')
            return redirect('modulo_puntos:lista_mantenimientos')
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/mantenimientos/form_mantenimiento.html', {
        'form': form,
        'titulo': f'Editar Mantenimiento — {mant.fecha}',
        'accion': 'editar',
        'mant': mant,
    })


@login_required(login_url='/login/')
def eliminar_mantenimiento(request, mant_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'mantenimiento.editar'):
        messages.error(request, 'No tienes permiso para eliminar mantenimientos.')
        return redirect('modulo_puntos:lista_mantenimientos')

    mant = get_object_or_404(MantenimientoEquipo, pk=mant_id)
    if not pvd_permitido(request, mant.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para eliminar mantenimientos de otro PVD.')
        return redirect('modulo_puntos:lista_mantenimientos')

    if request.method == 'POST':
        registrar_auditoria(request, 'DELETE', 'MantenimientoEquipo', mant.pk,
                            f'Mantenimiento eliminado: {mant.get_tipo_display()} — {mant.fecha}')
        mant.delete()
        messages.success(request, 'Registro de mantenimiento eliminado.')

    return redirect('modulo_puntos:lista_mantenimientos')


