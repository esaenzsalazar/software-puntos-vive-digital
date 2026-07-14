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

# ── EDITAR EVIDENCIA ───────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def editar_evidencia(request, evidencia_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')

    evidencia = get_object_or_404(Evidencia, pk=evidencia_id)
    pvd_id = request.session.get('pvd_activo_id')
    if pvd_id and not request.user.is_superuser and not usuario_es_admin_tic(request.user):
        if evidencia.punto_vive_digital_id != pvd_id:
            messages.error(request, 'No tienes permisos para editar esta evidencia.')
            return redirect('modulo_puntos:lista_evidencias')

    form = EvidenciaForm(request.POST or None, request.FILES or None, instance=evidencia)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            registrar_auditoria(request, 'UPDATE', 'Evidencia', evidencia.pk, f'Evidencia editada: {evidencia.titulo}')
            messages.success(request, f'Evidencia "{evidencia.titulo}" actualizada.')
            return redirect('modulo_puntos:lista_evidencias')
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/crear_evidencia.html', {
        'form': form,
        'pvd': evidencia.punto_vive_digital,
        'editando': True,
        'evidencia': evidencia,
    })


# ── EVIDENCIAS ────────────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def lista_evidencias(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    es_admin_pvd_solo = (
        not request.user.is_superuser
        and not usuario_es_admin_tic(request.user)
        and request.user.groups.filter(name='Administrador PVD').exists()
    )

    pvd_id = request.session.get('pvd_activo_id')
    pvd = PuntoViveDigital.objects.filter(pk=pvd_id).first() if pvd_id else None

    qs = Evidencia.objects.select_related('punto_vive_digital', 'registrado_por').order_by('-fecha', '-fecha_registro')
    if es_admin_pvd_solo and pvd:
        qs = qs.filter(punto_vive_digital=pvd)

    categoria = request.GET.get('categoria', '')
    if categoria:
        qs = qs.filter(categoria=categoria)

    paginator = Paginator(qs, 12)
    page = request.GET.get('page')
    evidencias = paginator.get_page(page)

    return render(request, 'modulo_puntos/lista_evidencias.html', {
        'evidencias': evidencias,
        'pvd': pvd,
        'categoria_activa': categoria,
        'categorias': Evidencia.CATEGORIA_CHOICES,
        'total': qs.count(),
        'es_admin_pvd_solo': es_admin_pvd_solo,
    })


@login_required(login_url='/login/')
def crear_evidencia(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para registrar evidencias.')
        return redirect('modulo_puntos:panel_control')
    # Solo el Admin PVD y el Superusuario pueden subir evidencias
    _es_admin_pvd = (
        not request.user.is_superuser
        and not usuario_es_admin_tic(request.user)
        and request.user.groups.filter(name='Administrador PVD').exists()
    )
    if not _es_admin_pvd and not request.user.is_superuser:
        messages.error(request, 'Solo el Administrador PVD o el Superusuario pueden registrar evidencias de trabajo.')
        return redirect('modulo_puntos:lista_evidencias')

    pvd_id = request.session.get('pvd_activo_id')
    pvd = PuntoViveDigital.objects.filter(pk=pvd_id, estado='A').first() if pvd_id else None

    if not pvd:
        messages.warning(request, 'Debes seleccionar un Punto Vive Digital antes de registrar evidencias.')
        return redirect('modulo_puntos:seleccionar_pvd_view')

    form = EvidenciaForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            evidencia = form.save(commit=False)
            evidencia.punto_vive_digital = pvd
            evidencia.registrado_por = request.user
            evidencia.save()
            registrar_auditoria(request, 'CREATE', 'Evidencia', evidencia.pk, f'Nueva evidencia: {evidencia.titulo} — PVD: {pvd}')
            messages.success(request, f'Evidencia "{evidencia.titulo}" registrada correctamente.')
            return redirect('modulo_puntos:lista_evidencias')
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/crear_evidencia.html', {'form': form, 'pvd': pvd})


@login_required(login_url='/login/')
def eliminar_evidencia(request, evidencia_id):
    messages.error(request, 'Las evidencias no pueden ser eliminadas. Contacta al Administrador TIC si necesitas gestionar esta evidencia.')
    return redirect('modulo_puntos:lista_evidencias')


@login_required(login_url='/login/')
def servir_evidencia(request, evidencia_id):
    """
    Sirve la imagen de una Evidencia solo a usuarios con sesión iniciada
    (y con permiso sobre el PVD dueño de la evidencia). El archivo en sí
    vive fuera del alcance público: en producción Nginx no expone /media/
    directamente, así que este es el único camino para verlo.
    """
    if not usuario_puede_usar_modulos_pvd(request.user):
        raise Http404
    evidencia = get_object_or_404(Evidencia, pk=evidencia_id)
    if not pvd_permitido(request, evidencia.punto_vive_digital_id):
        raise Http404
    if not evidencia.imagen:
        raise Http404

    content_type = mimetypes.guess_type(evidencia.imagen.name)[0] or 'application/octet-stream'

    if settings.DEBUG:
        return FileResponse(evidencia.imagen.open('rb'), content_type=content_type)

    response = HttpResponse(content_type=content_type)
    response['X-Accel-Redirect'] = f'/protected-media/{evidencia.imagen.name}'
    return response


