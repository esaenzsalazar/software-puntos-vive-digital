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

# ── ATENCIONES Y SERVICIOS ─────────────────────────────────────────────────────

@login_required(login_url='/login/')
def buscar_ciudadanos_json(request):
    """Endpoint AJAX para el autocompletado de ciudadanos en el formulario de atención."""
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})

    # Los ciudadanos son una población compartida: se pueden buscar y atender
    # desde cualquier PVD, sin importar en cuál fueron registrados originalmente.
    qs = Ciudadano.objects.filter(estado='A').filter(
        Q(primer_nombre__icontains=q)
        | Q(segundo_nombre__icontains=q)
        | Q(primer_apellido__icontains=q)
        | Q(segundo_apellido__icontains=q)
        | Q(numero_documento__icontains=q)
    ).order_by('primer_apellido', 'primer_nombre')[:12]

    return JsonResponse({'results': [
        {
            'id':     c.pk,
            'nombre': c.get_nombre_completo(),
            'doc':    c.numero_documento or '',
        }
        for c in qs
    ]})


@login_required(login_url='/login/')
def registrar_atencion(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    pvd_id = request.session.get('pvd_activo_id')
    if not pvd_id:
        messages.warning(request, 'Debes ingresar a un Punto Vive Digital antes de registrar una atención.')
        return redirect('modulo_puntos:seleccionar_pvd_view')

    pvd_activo = PuntoViveDigital.objects.filter(pk=pvd_id, estado='A').first()
    if not pvd_activo:
        del request.session['pvd_activo_id']
        messages.warning(request, 'El Punto Vive Digital de tu sesión ya no está disponible. Selecciona otro.')
        return redirect('modulo_puntos:seleccionar_pvd_view')

    ciudadano_id = request.GET.get('ciudadano')
    ciudadano_prefill = None
    initial = {}
    if ciudadano_id:
        try:
            ciudadano_prefill = Ciudadano.objects.get(pk=ciudadano_id, estado='A')
            initial['ciudadano'] = ciudadano_prefill
        except Ciudadano.DoesNotExist:
            pass

    form = AtencionForm(request.POST or None, initial=initial)

    if request.method == 'POST':
        if form.is_valid():
            try:
                atencion = form.save(commit=False)
                atencion.operador = request.user
                atencion.punto_vive_digital_id = pvd_id
                atencion.save()
                messages.success(request, 'Atención registrada. Ahora registra los servicios prestados.')
                return redirect('modulo_puntos:detalle_atencion', atencion_id=atencion.pk)
            except Exception as e:
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            messages.error(request, 'No se pudo guardar la atención. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/registrar_atencion.html', {
        'form': form,
        'ciudadano_prefill': ciudadano_prefill,
        'pvd_activo': pvd_activo,
    })


@login_required(login_url='/login/')
def editar_atencion(request, atencion_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    atencion = get_object_or_404(Atencion, pk=atencion_id)

    # Admin PVD solo puede editar atenciones de su PVD activo
    pvd_id = request.session.get('pvd_activo_id')
    es_admin_pvd_solo = (
        not request.user.is_superuser
        and not usuario_es_admin_tic(request.user)
        and request.user.groups.filter(name='Administrador PVD').exists()
    )
    if es_admin_pvd_solo and pvd_id and atencion.punto_vive_digital_id != int(pvd_id):
        messages.error(request, 'No tienes permiso para editar esta atención.')
        return redirect('modulo_puntos:lista_atenciones')

    form = AtencionForm(request.POST or None, instance=atencion)

    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Atención actualizada correctamente.')
                return redirect('modulo_puntos:detalle_atencion', atencion_id=atencion.pk)
            except Exception as e:
                messages.error(request, f'Error al guardar: {e}')
        else:
            messages.error(request, 'Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/registrar_atencion.html', {
        'form': form,
        'atencion': atencion,
    })


@login_required(login_url='/login/')
def lista_atenciones(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    user = request.user
    es_admin_pvd_solo = (
        not user.is_superuser
        and not usuario_es_admin_tic(user)
        and user.groups.filter(name='Administrador PVD').exists()
    )

    q = request.GET.get('q', '').strip()
    estado_filter = request.GET.get('estado', '').strip()
    fecha_desde_filter = request.GET.get('fecha_desde', '').strip()
    fecha_hasta_filter = request.GET.get('fecha_hasta', '').strip()
    pvd_filter = request.GET.get('pvd', '').strip()

    atenciones = Atencion.objects.select_related(
        'ciudadano', 'punto_vive_digital', 'operador'
    ).order_by('-fecha', '-pk')

    if es_admin_pvd_solo:
        pvd_id = request.session.get('pvd_activo_id')
        atenciones = atenciones.filter(punto_vive_digital_id=pvd_id) if pvd_id else atenciones.none()
    elif pvd_filter:
        atenciones = atenciones.filter(punto_vive_digital_id=pvd_filter)

    if q:
        atenciones = atenciones.filter(
            Q(ciudadano__primer_nombre__icontains=q) |
            Q(ciudadano__primer_apellido__icontains=q) |
            Q(ciudadano__numero_documento__icontains=q)
        )
    if estado_filter:
        atenciones = atenciones.filter(estado=estado_filter)
    if fecha_desde_filter:
        atenciones = atenciones.filter(fecha__gte=fecha_desde_filter)
    if fecha_hasta_filter:
        atenciones = atenciones.filter(fecha__lte=fecha_hasta_filter)

    total = atenciones.count()
    paginator = Paginator(atenciones, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    pvds_para_filtro = PuntoViveDigital.objects.filter(estado='A').order_by('nombre') if not es_admin_pvd_solo else None

    return render(request, 'modulo_puntos/lista_atenciones.html', {
        'atenciones': page_obj,
        'page_obj': page_obj,
        'total': total,
        'q': q,
        'estado_filter': estado_filter,
        'fecha_desde_filter': fecha_desde_filter,
        'fecha_hasta_filter': fecha_hasta_filter,
        'pvd_filter': pvd_filter,
        'pvds_para_filtro': pvds_para_filtro,
    })


@login_required(login_url='/login/')
def detalle_atencion(request, atencion_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    atencion = get_object_or_404(
        Atencion.objects.select_related('ciudadano', 'punto_vive_digital', 'operador'),
        pk=atencion_id
    )
    if not pvd_permitido(request, atencion.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para ver atenciones de otro PVD.')
        return redirect('modulo_puntos:lista_atenciones')
    servicios = Servicio.objects.filter(atencion=atencion).order_by('pk')
    satisfaccion = Satisfaccion.objects.filter(atencion=atencion).first()

    return render(request, 'modulo_puntos/detalle_atencion.html', {
        'atencion': atencion,
        'servicios': servicios,
        'satisfaccion': satisfaccion,
    })


@login_required(login_url='/login/')
def cambiar_estado_atencion(request, atencion_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')

    if request.method != 'POST':
        return redirect('modulo_puntos:lista_atenciones')

    atencion = get_object_or_404(Atencion, pk=atencion_id)
    if not pvd_permitido(request, atencion.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para modificar atenciones de otro PVD.')
        return redirect('modulo_puntos:lista_atenciones')
    nuevo_estado = request.POST.get('estado', '').strip()
    estados_validos = {'P', 'F', 'C'}

    etiquetas = {'P': 'Pendiente', 'F': 'Finalizada', 'C': 'Cancelada'}
    if nuevo_estado not in estados_validos:
        messages.error(request, 'Estado no válido.')
    elif nuevo_estado == 'C' and atencion.estado == 'P':
        messages.error(request, 'No se puede cancelar una atención pendiente directamente. Primero finalízala o cambia el motivo.')
    else:
        atencion.estado = nuevo_estado
        atencion.save(update_fields=['estado'])
        messages.success(request, f'Atención marcada como {etiquetas[nuevo_estado]}.')

    next_url = request.POST.get('next', '').strip()
    if next_url == 'lista':
        return redirect('modulo_puntos:lista_atenciones')
    return redirect('modulo_puntos:detalle_atencion', atencion_id=atencion.pk)


@login_required(login_url='/login/')
def finalizar_servicio(request, atencion_id, servicio_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')

    if request.method != 'POST':
        return redirect('modulo_puntos:detalle_atencion', atencion_id=atencion_id)

    servicio = get_object_or_404(
        Servicio.objects.select_related('atencion'), pk=servicio_id, atencion_id=atencion_id
    )
    if not pvd_permitido(request, servicio.atencion.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para modificar servicios de otro PVD.')
        return redirect('modulo_puntos:lista_atenciones')

    if servicio.estado == 'A':
        servicio.estado = 'F'
        servicio.save(update_fields=['estado'])
        registrar_auditoria(request, 'UPDATE', 'Servicio', servicio.pk,
                            f'Servicio finalizado: {servicio.nombre}')
        messages.success(request, f'Servicio "{servicio.nombre}" finalizado.')
    else:
        messages.warning(request, 'El servicio ya está finalizado o inactivo.')

    return redirect('modulo_puntos:detalle_atencion', atencion_id=atencion_id)


@login_required(login_url='/login/')
def registrar_satisfaccion(request, atencion_id=None):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    # PVD en sesión es obligatorio para registrar satisfacción
    pvd_id = request.session.get('pvd_activo_id')
    if not pvd_id:
        messages.warning(
            request,
            'Debes ingresar a un Punto Vive Digital antes de registrar una encuesta de satisfacción.'
        )
        return redirect('modulo_puntos:seleccionar_pvd_view')

    pvd_activo = PuntoViveDigital.objects.filter(pk=pvd_id, estado='A').first()
    if not pvd_activo:
        del request.session['pvd_activo_id']
        messages.warning(request, 'El Punto Vive Digital de tu sesión ya no está disponible. Selecciona otro.')
        return redirect('modulo_puntos:seleccionar_pvd_view')

    atencion = None
    if atencion_id:
        atencion = get_object_or_404(
            Atencion.objects.select_related('ciudadano', 'punto_vive_digital'),
            pk=atencion_id,
        )
        # Verificar que la atención pertenece al PVD activo
        if atencion.punto_vive_digital_id != pvd_activo.pk:
            messages.error(request, 'Esa atención no pertenece al Punto Vive Digital activo en tu sesión.')
            return redirect('modulo_puntos:panel_control')
        # Verificar que la atención tiene ciudadano
        if not atencion.ciudadano_id:
            messages.error(request, 'No se puede registrar satisfacción: la atención no tiene ciudadano asignado.')
            return redirect('modulo_puntos:detalle_atencion', atencion_id=atencion.pk)
        if Satisfaccion.objects.filter(atencion=atencion).exists():
            messages.warning(request, 'Esta atención ya tiene una encuesta de satisfacción registrada.')
            return redirect('modulo_puntos:detalle_atencion', atencion_id=atencion.pk)

    from django.utils import timezone
    initial = {'fecha': timezone.now().strftime('%Y-%m-%dT%H:%M')}
    if atencion:
        initial['atencion'] = atencion.pk

    form = SatisfaccionForm(request.POST or None, initial=initial, pvd_id=pvd_id)
    if atencion:
        form.fields['atencion'].widget = forms.HiddenInput()
        form.fields['atencion'].required = False   # oculto: ya viene fijo por atencion_id

    if request.method == 'POST':
        if form.is_valid():
            try:
                satisfaccion = form.save(commit=False)
                # Si viene de detalle de atención, forzar la atención correcta
                if atencion:
                    satisfaccion.atencion = atencion
                satisfaccion.save()
                registrar_auditoria(
                    request, 'CREATE', 'Satisfaccion', satisfaccion.pk,
                    f'Encuesta registrada en {pvd_activo.nombre}'
                )
                messages.success(request, 'Encuesta de satisfacción registrada correctamente.')
                if atencion:
                    return redirect('modulo_puntos:detalle_atencion', atencion_id=atencion.pk)
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                logger.error('Error al guardar satisfacción: %s', e, exc_info=True)
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            messages.error(request, 'No se pudo guardar la satisfacción. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/registrar_satisfaccion.html', {
        'form': form,
        'atencion': atencion,
        'pvd_activo': pvd_activo,
    })


@login_required(login_url='/login/')
def gestionar_servicios_pvd(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    user = request.user
    es_admin_pvd_solo = (
        not user.is_superuser
        and not usuario_es_admin_tic(user)
        and user.groups.filter(name='Administrador PVD').exists()
    )

    q           = request.GET.get('q', '').strip()
    tipo_filter = request.GET.get('tipo', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()

    servicios = (
        Servicio.objects
        .select_related('atencion', 'atencion__ciudadano', 'atencion__punto_vive_digital', 'recurso')
        .order_by('-atencion__fecha', '-pk')
    )

    if es_admin_pvd_solo:
        pvd_id = request.session.get('pvd_activo_id')
        servicios = servicios.filter(atencion__punto_vive_digital_id=pvd_id) if pvd_id else servicios.none()

    if q:
        servicios = servicios.filter(
            Q(atencion__ciudadano__primer_nombre__icontains=q) |
            Q(atencion__ciudadano__primer_apellido__icontains=q) |
            Q(atencion__ciudadano__numero_documento__icontains=q)
        )
    if tipo_filter:
        servicios = servicios.filter(tipo=tipo_filter)
    if fecha_desde:
        servicios = servicios.filter(atencion__fecha__gte=fecha_desde)
    if fecha_hasta:
        servicios = servicios.filter(atencion__fecha__lte=fecha_hasta)

    from .forms import TIPO_SERVICIO_CHOICES
    tipos = [c for c in TIPO_SERVICIO_CHOICES if c[0]]

    total = servicios.count()
    paginator = Paginator(servicios, 25)
    page = request.GET.get('page')
    servicios_page = paginator.get_page(page)

    return render(request, 'modulo_puntos/gestionar_servicios_pvd.html', {
        'servicios': servicios_page,
        'q': q,
        'tipo_filter': tipo_filter,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'tipos': tipos,
        'total': total,
    })


@login_required(login_url='/login/')
def registrar_servicio(request, atencion_id=None):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    atencion = get_object_or_404(Atencion, pk=atencion_id) if atencion_id else None
    if atencion and not pvd_permitido(request, atencion.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para registrar servicios en atenciones de otro PVD.')
        return redirect('modulo_puntos:lista_atenciones')

    pvd_id = request.session.get('pvd_activo_id')
    if pvd_id:
        recursos_pvd = Recurso.objects.filter(punto_vive_digital_id=pvd_id, estado='A').order_by('tipo', 'codigo')
        salas_pvd = Sala.objects.filter(punto_vive_digital_id=pvd_id, estado='A').order_by('nombre')
    else:
        recursos_pvd = Recurso.objects.filter(estado='A').order_by('tipo', 'codigo')
        salas_pvd = Sala.objects.filter(estado='A').order_by('nombre')

    initial = {'atencion': atencion} if atencion else {}
    form = ServicioForm(request.POST or None, initial=initial, recursos_pvd=recursos_pvd, salas_pvd=salas_pvd)

    if atencion:
        form.fields['atencion'].widget.attrs['disabled'] = True
        form.fields['atencion'].required = False

    if request.method == 'POST':
        if form.is_valid():
            try:
                servicio = form.save(commit=False)
                if atencion:
                    servicio.atencion = atencion
                servicio.save()
                messages.success(request, 'Servicio registrado correctamente.')
                if servicio.requiere_sala == 'S' and servicio.sala_id:
                    url = reverse('modulo_puntos:crear_habilitacion') + f'?sala_id={servicio.sala_id}'
                    if atencion:
                        url += f'&atencion_id={atencion.pk}'
                    return redirect(url)
                if atencion:
                    return redirect('modulo_puntos:detalle_atencion', atencion_id=atencion.pk)
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            messages.error(request, 'No se pudo guardar el servicio. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/registrar_servicio.html', {
        'form': form,
        'atencion': atencion,
    })


# ── EDITAR SERVICIO ────────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def editar_servicio(request, servicio_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')

    servicio = get_object_or_404(Servicio.objects.select_related('atencion'), pk=servicio_id)
    atencion = servicio.atencion
    if not pvd_permitido(request, atencion.punto_vive_digital_id if atencion else None):
        messages.error(request, 'No tienes permiso para editar servicios de otro PVD.')
        return redirect('modulo_puntos:lista_atenciones')

    pvd_id = request.session.get('pvd_activo_id')
    if pvd_id:
        recursos_pvd = Recurso.objects.filter(punto_vive_digital_id=pvd_id, estado='A').order_by('tipo', 'codigo')
        salas_pvd = Sala.objects.filter(punto_vive_digital_id=pvd_id, estado='A').order_by('nombre')
    else:
        recursos_pvd = Recurso.objects.filter(estado='A').order_by('tipo', 'codigo')
        salas_pvd = Sala.objects.filter(estado='A').order_by('nombre')

    form = ServicioForm(request.POST or None, instance=servicio, recursos_pvd=recursos_pvd, salas_pvd=salas_pvd)
    form.fields['atencion'].widget.attrs['disabled'] = True
    form.fields['atencion'].required = False

    if request.method == 'POST':
        if form.is_valid():
            s = form.save(commit=False)
            s.atencion = atencion
            s.save()
            registrar_auditoria(request, 'UPDATE', 'Servicio', servicio.pk, f'Servicio editado: {servicio.nombre}')
            messages.success(request, 'Servicio actualizado correctamente.')
            return redirect('modulo_puntos:detalle_atencion', atencion_id=atencion.pk)
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/registrar_servicio.html', {
        'form': form,
        'atencion': atencion,
        'editando': True,
        'servicio': servicio,
    })


# ── ELIMINAR SERVICIO ─────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def eliminar_servicio(request, servicio_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')

    servicio = get_object_or_404(Servicio.objects.select_related('atencion'), pk=servicio_id)
    atencion_id = servicio.atencion_id
    if not pvd_permitido(request, servicio.atencion.punto_vive_digital_id if servicio.atencion else None):
        messages.error(request, 'No tienes permiso para eliminar servicios de otro PVD.')
        return redirect('modulo_puntos:lista_atenciones')

    if request.method == 'POST':
        registrar_auditoria(request, 'DELETE', 'Servicio', servicio.pk,
                            f'Servicio eliminado: {servicio.nombre} — Atención #{atencion_id}')
        servicio.delete()
        messages.success(request, 'Servicio eliminado correctamente.')

    return redirect('modulo_puntos:detalle_atencion', atencion_id=atencion_id)


# ── EDITAR/ELIMINAR SATISFACCIÓN ───────────────────────────────────────────────

@login_required(login_url='/login/')
def editar_satisfaccion(request, satisfaccion_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')

    satisfaccion = get_object_or_404(Satisfaccion.objects.select_related('atencion'), pk=satisfaccion_id)
    atencion = satisfaccion.atencion
    if not pvd_permitido(request, atencion.punto_vive_digital_id if atencion else None):
        messages.error(request, 'No tienes permiso para editar encuestas de otro PVD.')
        return redirect('modulo_puntos:lista_atenciones')

    form = SatisfaccionForm(request.POST or None, instance=satisfaccion)
    form.fields['atencion'].widget = forms.HiddenInput()

    if request.method == 'POST':
        if form.is_valid():
            s = form.save(commit=False)
            s.atencion = atencion
            s.save()
            registrar_auditoria(request, 'UPDATE', 'Satisfaccion', satisfaccion.pk, f'Satisfacción editada — Atención #{atencion.pk}')
            messages.success(request, 'Encuesta de satisfacción actualizada.')
            return redirect('modulo_puntos:detalle_atencion', atencion_id=atencion.pk)
        messages.error(request, 'Revisa los datos.')

    return render(request, 'modulo_puntos/registrar_satisfaccion.html', {
        'form': form,
        'atencion': atencion,
        'editando': True,
    })


@login_required(login_url='/login/')
def eliminar_satisfaccion(request, satisfaccion_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')

    satisfaccion = get_object_or_404(Satisfaccion.objects.select_related('atencion'), pk=satisfaccion_id)
    atencion_id = satisfaccion.atencion_id
    if not pvd_permitido(request, satisfaccion.atencion.punto_vive_digital_id if satisfaccion.atencion else None):
        messages.error(request, 'No tienes permiso para eliminar encuestas de otro PVD.')
        return redirect('modulo_puntos:lista_atenciones')

    if request.method == 'POST':
        registrar_auditoria(request, 'DELETE', 'Satisfaccion', satisfaccion.pk, f'Satisfacción eliminada — Atención #{atencion_id}')
        satisfaccion.delete()
        messages.success(request, 'Encuesta de satisfacción eliminada.')

    return redirect('modulo_puntos:detalle_atencion', atencion_id=atencion_id)


