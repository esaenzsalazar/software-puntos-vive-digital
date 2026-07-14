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

# ── GESTIÓN DE SALAS ───────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def lista_salas(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'salas.ver'):
        messages.error(request, 'No tienes permiso para ver salas.')
        return redirect('modulo_puntos:panel_control')

    es_admin_tic = usuario_es_admin_tic(request.user) or request.user.is_superuser
    puede_eliminar = tiene_permiso(request.user, 'infraestructura.eliminar_sala')

    if es_admin_tic:
        pvds = PuntoViveDigital.objects.filter(estado='A').order_by('nombre')
        pvd_id = request.GET.get('pvd_id') or request.session.get('pvd_activo_id')
        pvd_seleccionado = PuntoViveDigital.objects.filter(pk=pvd_id).first() if pvd_id else None
        if pvd_seleccionado:
            salas = Sala.objects.filter(punto_vive_digital=pvd_seleccionado).order_by('nombre')
        else:
            salas = Sala.objects.all().select_related('punto_vive_digital').order_by('punto_vive_digital__nombre', 'nombre')
    else:
        pvds = []
        pvd_id = request.session.get('pvd_activo_id')
        pvd_seleccionado = PuntoViveDigital.objects.filter(pk=pvd_id).first() if pvd_id else None
        salas = Sala.objects.filter(punto_vive_digital_id=pvd_id).order_by('nombre') if pvd_id else Sala.objects.none()

    return render(request, 'modulo_puntos/lista_salas.html', {
        'salas': salas,
        'pvd': pvd_seleccionado,
        'pvd_seleccionado': pvd_seleccionado,
        'pvds': pvds,
        'es_admin_tic': es_admin_tic,
        'puede_eliminar': puede_eliminar,
    })


@login_required(login_url='/login/')
def crear_sala(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')
    # Solo superusuario o Admin TIC pueden crear salas
    if not usuario_es_admin_tic(request.user):
        messages.error(request, 'Solo el Superusuario o el Administrador TIC pueden crear nuevas salas.')
        return redirect('modulo_puntos:lista_salas')
    if not tiene_permiso(request.user, 'salas.crear'):
        messages.error(request, 'No tienes permiso para crear salas.')
        return redirect('modulo_puntos:lista_salas')

    pvd_id = request.session.get('pvd_activo_id')
    form = SalaForm(request.POST or None, initial={'punto_vive_digital': pvd_id} if pvd_id else None)
    if request.method == 'POST':
        if form.is_valid():
            sala = form.save()
            registrar_auditoria(request, 'CREATE', 'Sala', sala.pk, f'Sala creada: {sala.nombre}')
            messages.success(request, f'Sala "{sala.nombre}" creada correctamente.')
            return redirect('modulo_puntos:lista_salas')
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/form_sala.html', {
        'form': form,
        'titulo': 'Crear Sala',
        'accion': 'crear',
    })


@login_required(login_url='/login/')
def editar_sala(request, sala_cdgo):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'salas.editar'):
        messages.error(request, 'No tienes permiso para editar salas.')
        return redirect('modulo_puntos:lista_salas')

    sala = get_object_or_404(Sala, pk=sala_cdgo)
    if not pvd_permitido(request, sala.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para editar salas de otro PVD.')
        return redirect('modulo_puntos:lista_salas')
    form = SalaForm(request.POST or None, instance=sala)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            registrar_auditoria(request, 'UPDATE', 'Sala', sala.pk, f'Sala editada: {sala.nombre}')
            messages.success(request, f'Sala "{sala.nombre}" actualizada correctamente.')
            return redirect('modulo_puntos:lista_salas')
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/form_sala.html', {
        'form': form,
        'titulo': f'Editar Sala: {sala.nombre}',
        'accion': 'editar',
        'sala': sala,
    })


@login_required(login_url='/login/')
def activar_sala(request, sala_cdgo):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'salas.editar'):
        messages.error(request, 'No tienes permiso para cambiar el estado de salas.')
        return redirect('modulo_puntos:lista_salas')

    if request.method != 'POST':
        return redirect('modulo_puntos:lista_salas')
    sala = get_object_or_404(Sala, pk=sala_cdgo)
    if not pvd_permitido(request, sala.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para cambiar el estado de salas de otro PVD.')
        return redirect('modulo_puntos:lista_salas')
    sala.estado = 'I' if sala.estado == 'A' else 'A'
    sala.save()
    estado_str = 'activada' if sala.estado == 'A' else 'desactivada'
    registrar_auditoria(request, 'UPDATE', 'Sala', sala.pk, f'Sala {estado_str}: {sala.nombre}')
    messages.success(request, f'Sala "{sala.nombre}" {estado_str} correctamente.')
    return redirect('modulo_puntos:lista_salas')


@login_required(login_url='/login/')
def eliminar_sala(request, sala_cdgo):
    messages.error(request, 'La eliminación de salas está deshabilitada. Usa la opción de desactivar para retirarla.')
    return redirect('modulo_puntos:lista_salas')


# ── HABILITACIÓN DE SALAS ──────────────────────────────────────────────────────

def _actualizar_estados_habilitaciones(base_qs):
    """Actualiza automáticamente el estado de habilitaciones según la hora actual."""
    ahora = datetime.now()
    hoy = ahora.date()
    hora_actual = ahora.time()

    base = base_qs.exclude(estado__in=('X', 'F'))

    # Fechas pasadas → Finalizado
    base.filter(fecha__lt=hoy).update(estado='F')

    # Hoy, hora en rango → En curso
    base.filter(
        fecha=hoy,
        hora_inicio__lte=hora_actual,
        hora_fin__gte=hora_actual,
    ).exclude(estado='E').update(estado='E')

    # Hoy, hora superada → Finalizado
    base.filter(
        fecha=hoy,
        hora_fin__lt=hora_actual,
    ).update(estado='F')


@login_required(login_url='/login/')
def lista_habilitaciones(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'habilitaciones.ver'):
        messages.error(request, 'No tienes permiso para ver habilitaciones de sala.')
        return redirect('modulo_puntos:panel_control')

    pvd_id = request.session.get('pvd_activo_id')
    fecha_filtro = request.GET.get('fecha', '')
    sala_filtro = request.GET.get('sala_id', '')
    estado_filtro = request.GET.get('estado', '')

    if pvd_id:
        salas_pvd = Sala.objects.filter(punto_vive_digital_id=pvd_id)
        qs = HabilitacionSala.objects.filter(sala__punto_vive_digital_id=pvd_id)
        pvd = PuntoViveDigital.objects.filter(pk=pvd_id).first()
    else:
        salas_pvd = Sala.objects.all().select_related('punto_vive_digital')
        qs = HabilitacionSala.objects.all()
        pvd = None

    qs = qs.select_related('sala', 'sala__punto_vive_digital', 'registrado_por')

    if fecha_filtro:
        try:
            qs = qs.filter(fecha=fecha_filtro)
        except Exception:
            pass
    if sala_filtro:
        qs = qs.filter(sala_id=sala_filtro)
    if estado_filtro:
        qs = qs.filter(estado=estado_filtro)

    _actualizar_estados_habilitaciones(qs)
    qs = qs.order_by('fecha', 'hora_inicio')

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'modulo_puntos/habilitaciones/lista_habilitaciones.html', {
        'habilitaciones': page_obj,
        'page_obj': page_obj,
        'salas_pvd': salas_pvd,
        'pvd': pvd,
        'fecha_filtro': fecha_filtro,
        'sala_filtro': sala_filtro,
        'estado_filtro': estado_filtro,
        'estados': HabilitacionSala.ESTADO_CHOICES,
    })


@login_required(login_url='/login/')
def crear_habilitacion(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'habilitaciones.crear'):
        messages.error(request, 'No tienes permiso para crear habilitaciones.')
        return redirect('modulo_puntos:lista_habilitaciones')

    pvd_id = request.session.get('pvd_activo_id')
    if not pvd_id:
        messages.warning(request, 'Debes ingresar a un Punto Vive Digital antes de crear una habilitación de sala.')
        return redirect('modulo_puntos:seleccionar_pvd_view')

    sala_inicial = request.GET.get('sala_id')
    fecha_inicial = request.GET.get('fecha')
    atencion_id = request.GET.get('atencion_id') or request.POST.get('atencion_id')
    atencion_origen = Atencion.objects.filter(pk=atencion_id).first() if atencion_id else None

    initial = {}
    if sala_inicial:
        initial['sala'] = sala_inicial
    if fecha_inicial:
        initial['fecha'] = fecha_inicial
    if atencion_origen and atencion_origen.ciudadano_id:
        initial['solicitante'] = atencion_origen.ciudadano_id

    form = HabilitacionSalaForm(
        request.POST or None,
        pvd_id=pvd_id,
        initial=initial,
    )

    if request.method == 'POST':
        if form.is_valid():
            hab = form.save(commit=False)
            hab.registrado_por = request.user
            hab.save()
            form.save_m2m()
            registrar_auditoria(
                request, 'CREATE', 'HabilitacionSala', hab.pk,
                f'Habilitación creada: {hab.sala.nombre} – {hab.fecha}'
            )
            messages.success(request, f'Habilitación para "{hab.sala.nombre}" el {hab.fecha} registrada correctamente.')
            if atencion_id:
                return redirect('modulo_puntos:detalle_atencion', atencion_id=atencion_id)
            return redirect('modulo_puntos:lista_habilitaciones')
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/habilitaciones/form_habilitacion.html', {
        'form': form,
        'titulo': 'Nueva Habilitación de Sala',
        'accion': 'crear',
        'atencion_id': atencion_id,
        'atencion_origen': atencion_origen,
    })


@login_required(login_url='/login/')
def editar_habilitacion(request, hab_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'habilitaciones.editar'):
        messages.error(request, 'No tienes permiso para editar habilitaciones.')
        return redirect('modulo_puntos:lista_habilitaciones')

    hab = get_object_or_404(HabilitacionSala.objects.select_related('sala'), pk=hab_id)
    if not pvd_permitido(request, hab.sala.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para editar habilitaciones de otro PVD.')
        return redirect('modulo_puntos:lista_habilitaciones')

    pvd_id = request.session.get('pvd_activo_id')
    form = HabilitacionSalaForm(request.POST or None, instance=hab, pvd_id=pvd_id)

    if request.method == 'POST':
        if form.is_valid():
            hab = form.save()
            registrar_auditoria(
                request, 'UPDATE', 'HabilitacionSala', hab.pk,
                f'Habilitación editada: {hab.sala.nombre} – {hab.fecha}'
            )
            messages.success(request, f'Habilitación actualizada correctamente.')
            return redirect('modulo_puntos:lista_habilitaciones')
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/habilitaciones/form_habilitacion.html', {
        'form': form,
        'titulo': f'Editar Habilitación – {hab.sala.nombre}',
        'accion': 'editar',
        'hab': hab,
    })


@login_required(login_url='/login/')
def cancelar_habilitacion(request, hab_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'habilitaciones.cancelar'):
        messages.error(request, 'No tienes permiso para cancelar habilitaciones.')
        return redirect('modulo_puntos:lista_habilitaciones')

    try:
        hab = HabilitacionSala.objects.select_related('sala').get(pk=hab_id)
    except HabilitacionSala.DoesNotExist:
        messages.warning(request, 'La habilitación ya no existe.')
        return redirect('modulo_puntos:lista_habilitaciones')
    if not pvd_permitido(request, hab.sala.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para cancelar habilitaciones de otro PVD.')
        return redirect('modulo_puntos:lista_habilitaciones')

    if request.method != 'POST':
        return redirect('modulo_puntos:lista_habilitaciones')

    if hab.estado in ('F', 'X'):
        messages.warning(request, 'Esta habilitación ya está finalizada o cancelada.')
        return redirect('modulo_puntos:lista_habilitaciones')

    hab.estado = 'X'
    hab.save()
    registrar_auditoria(
        request, 'UPDATE', 'HabilitacionSala', hab.pk,
        f'Habilitación cancelada: {hab.sala.nombre} – {hab.fecha}'
    )
    messages.success(request, f'Habilitación de "{hab.sala.nombre}" cancelada.')
    return redirect('modulo_puntos:lista_habilitaciones')


@login_required(login_url='/login/')
def eliminar_habilitacion(request, hab_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'habilitaciones.eliminar'):
        messages.error(request, 'No tienes permiso para eliminar habilitaciones.')
        return redirect('modulo_puntos:lista_habilitaciones')

    if request.method != 'POST':
        return redirect('modulo_puntos:lista_habilitaciones')

    try:
        hab = HabilitacionSala.objects.select_related('sala').get(pk=hab_id)
    except HabilitacionSala.DoesNotExist:
        messages.warning(request, 'La habilitación ya no existe.')
        return redirect('modulo_puntos:lista_habilitaciones')
    if not pvd_permitido(request, hab.sala.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para eliminar habilitaciones de otro PVD.')
        return redirect('modulo_puntos:lista_habilitaciones')
    nombre_sala = hab.sala.nombre
    fecha = hab.fecha
    pk = hab.pk
    hab.delete()
    registrar_auditoria(
        request, 'DELETE', 'HabilitacionSala', pk,
        f'Habilitación eliminada: {nombre_sala} – {fecha}'
    )
    messages.success(request, f'Habilitación de "{nombre_sala}" eliminada.')
    return redirect('modulo_puntos:lista_habilitaciones')


@login_required(login_url='/login/')
def agenda_sala(request, sala_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')

    sala = get_object_or_404(Sala, pk=sala_id)
    if not pvd_permitido(request, sala.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para ver la agenda de salas de otro PVD.')
        return redirect('modulo_puntos:lista_salas')

    from datetime import date as dt_date, timedelta
    fecha_str = request.GET.get('fecha', '')
    try:
        fecha_base = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else dt_date.today()
    except ValueError:
        fecha_base = dt_date.today()

    fecha_inicio_semana = fecha_base - timedelta(days=fecha_base.weekday())
    dias_semana = [fecha_inicio_semana + timedelta(days=i) for i in range(7)]

    habilitaciones_semana = HabilitacionSala.objects.filter(
        sala=sala,
        fecha__range=[dias_semana[0], dias_semana[-1]],
    ).order_by('fecha', 'hora_inicio')

    _actualizar_estados_habilitaciones(habilitaciones_semana)

    agenda = {d: [] for d in dias_semana}
    for hab in habilitaciones_semana:
        if hab.fecha in agenda:
            agenda[hab.fecha].append(hab)

    semana_anterior = (fecha_inicio_semana - timedelta(days=7)).strftime('%Y-%m-%d')
    semana_siguiente = (fecha_inicio_semana + timedelta(days=7)).strftime('%Y-%m-%d')

    return render(request, 'modulo_puntos/habilitaciones/agenda_sala.html', {
        'sala': sala,
        'dias_semana': dias_semana,
        'agenda': agenda,
        'semana_anterior': semana_anterior,
        'semana_siguiente': semana_siguiente,
        'fecha_base': fecha_base,
    })


