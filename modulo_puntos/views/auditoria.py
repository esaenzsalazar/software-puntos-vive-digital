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
from .exportaciones import _crear_hoja, _xlsx_response

# ── LOG DE AUDITORÍA ───────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def log_auditoria(request):
    if not usuario_es_admin_tic(request.user):
        messages.error(request, 'Solo Administradores TIC y Superusuarios pueden ver el log de auditoría.')
        return redirect('modulo_puntos:panel_control')

    q = request.GET.get('q', '').strip()
    accion_filter = request.GET.get('accion', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()

    qs = AuditoriaAccion.objects.all()
    if q:
        qs = qs.filter(
            Q(usuario__icontains=q) |
            Q(descripcion__icontains=q) |
            Q(modelo_afectado__icontains=q)
        )
    if accion_filter:
        qs = qs.filter(accion=accion_filter)
    if fecha_desde:
        qs = qs.filter(fecha_accion__date__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha_accion__date__lte=fecha_hasta)

    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'modulo_puntos/log_auditoria.html', {
        'registros': page_obj,
        'page_obj': page_obj,
        'q': q,
        'accion_filter': accion_filter,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'tipo_choices': AuditoriaAccion.TIPO_ACCION,
    })


@login_required(login_url='/login/')
def exportar_auditoria(request):
    if not usuario_es_admin_tic(request.user):
        messages.error(request, 'Solo Administradores TIC y Superusuarios pueden exportar el log de auditoría.')
        return redirect('modulo_puntos:panel_control')

    q = request.GET.get('q', '').strip()
    accion_filter = request.GET.get('accion', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()

    qs = AuditoriaAccion.objects.all()
    if q:
        qs = qs.filter(
            Q(usuario__icontains=q) |
            Q(descripcion__icontains=q) |
            Q(modelo_afectado__icontains=q)
        )
    if accion_filter:
        qs = qs.filter(accion=accion_filter)
    if fecha_desde:
        qs = qs.filter(fecha_accion__date__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha_accion__date__lte=fecha_hasta)

    headers = ['Fecha / Hora', 'Usuario', 'Acción', 'Modelo', 'ID Objeto', 'Descripción', 'IP']
    filas = []
    for reg in qs:
        filas.append([
            reg.fecha_accion.strftime('%d/%m/%Y %H:%M') if reg.fecha_accion else '',
            reg.usuario or '',
            reg.get_accion_display(),
            reg.modelo_afectado or '',
            str(reg.objeto_id) if reg.objeto_id else '',
            reg.descripcion or '',
            reg.direccion_ip or '',
        ])

    registrar_auditoria(request, 'EXPORT', 'AuditoriaAccion', None, f'Exportación log auditoría ({len(filas)} registros)')
    wb = _crear_hoja('Log Auditoría', headers, filas)
    return _xlsx_response('Log_Auditoria_PVD', wb)


