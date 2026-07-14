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

@login_required(login_url='/login/')
def registrar_prestamo(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    pvd_id = request.session.get('pvd_activo_id')
    if not pvd_id:
        messages.warning(request, 'Debes ingresar a un Punto Vive Digital antes de registrar un préstamo.')
        return redirect('modulo_puntos:seleccionar_pvd_view')

    pvd_activo = PuntoViveDigital.objects.filter(pk=pvd_id, estado='A').first()
    if not pvd_activo:
        del request.session['pvd_activo_id']
        messages.warning(request, 'El Punto Vive Digital de tu sesión ya no está disponible. Selecciona otro.')
        return redirect('modulo_puntos:seleccionar_pvd_view')

    form = PrestamoRecursoForm(request.POST or None, pvd_id=pvd_id)
    if request.method == 'POST':
        if form.is_valid():
            try:
                prestamo = form.save()
                registrar_auditoria(request, 'CREATE', 'PrestamoRecurso', prestamo.pk,
                                    f'Nuevo préstamo: {prestamo.recurso}')
                messages.success(request, 'Préstamo registrado correctamente.')
                return redirect('modulo_puntos:registrar_recurso')
            except Exception as e:
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            if form.non_field_errors():
                messages.error(request, form.non_field_errors()[0])
            else:
                messages.error(request, 'Revisa los campos del formulario.')

    return render(request, 'modulo_puntos/registrar_prestamo.html', {'form': form})


@login_required(login_url='/login/')
def editar_prestamo(request, prestamo_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'inventario.editar_prestamo'):
        messages.error(request, 'No tienes permiso para editar préstamos.')
        return redirect('modulo_puntos:registrar_recurso')

    pvd_id = request.session.get('pvd_activo_id')
    prestamo = get_object_or_404(PrestamoRecurso.objects.select_related('recurso'), pk=prestamo_id)
    recurso_pvd_id = prestamo.recurso.punto_vive_digital_id if prestamo.recurso else None
    if not pvd_permitido(request, recurso_pvd_id):
        messages.error(request, 'No tienes permiso para editar préstamos de otro PVD.')
        return redirect('modulo_puntos:registrar_recurso')
    form = PrestamoRecursoForm(request.POST or None, instance=prestamo, pvd_id=pvd_id)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            registrar_auditoria(
                request, 'UPDATE', 'PrestamoRecurso', prestamo.pk,
                f'Préstamo editado: {prestamo.recurso} – entrega {prestamo.fecha_entrega}'
            )
            messages.success(request, 'Préstamo actualizado correctamente.')
            return redirect('modulo_puntos:registrar_recurso')  # lista_recursos
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/editar_prestamo.html', {
        'form': form,
        'prestamo': prestamo,
    })


@login_required(login_url='/login/')
def devolver_prestamo(request, prestamo_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    if request.method != 'POST':
        return redirect('modulo_puntos:registrar_recurso')

    from django.utils import timezone
    prestamo = get_object_or_404(PrestamoRecurso.objects.select_related('recurso'), pk=prestamo_id)
    recurso_pvd_id = prestamo.recurso.punto_vive_digital_id if prestamo.recurso else None
    if not pvd_permitido(request, recurso_pvd_id):
        messages.error(request, 'No tienes permiso para modificar préstamos de otro PVD.')
        return redirect('modulo_puntos:registrar_recurso')
    now = timezone.now()

    # Solo actuar si aún está en préstamo
    if prestamo.fecha_devolucion is None or prestamo.fecha_devolucion > now:
        prestamo.fecha_devolucion = now
        prestamo.save(update_fields=['fecha_devolucion'])
        registrar_auditoria(
            request, 'UPDATE', 'PrestamoRecurso', prestamo.pk,
            f'Devolución anticipada registrada: {prestamo.recurso} a las {now.strftime("%d/%m/%Y %H:%M")}'
        )
        messages.success(request, f'Devolución de "{prestamo.recurso}" registrada a las {now.strftime("%H:%M")}.')
    else:
        messages.info(request, 'Este préstamo ya figura como devuelto.')

    return redirect('modulo_puntos:registrar_recurso')


@login_required(login_url='/login/')
def lista_prestamos_global(request):
    """Vista global de todos los préstamos de ambos PVDs."""
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    from django.utils import timezone
    now = timezone.now()

    prestamos = (
        PrestamoRecurso.objects
        .select_related('recurso', 'recurso__punto_vive_digital', 'ciudadano')
        .order_by('-fecha_entrega')
    )

    q          = request.GET.get('q', '').strip()
    pvd_filter = request.GET.get('pvd_id', '').strip()
    estado     = request.GET.get('estado', '').strip()

    if usuario_necesita_seleccionar_pvd(request.user):
        # Admin PVD sólo ve préstamos de recursos de su PVD activo
        prestamos = prestamos.filter(recurso__punto_vive_digital_id=obtener_pvd_activo_id(request))
    elif pvd_filter:
        prestamos = prestamos.filter(recurso__punto_vive_digital_id=pvd_filter)

    if q:
        prestamos = prestamos.filter(
            Q(ciudadano__primer_nombre__icontains=q)
            | Q(ciudadano__primer_apellido__icontains=q)
            | Q(ciudadano__numero_documento__icontains=q)
            | Q(recurso__tipo__icontains=q)
            | Q(recurso__codigo__icontains=q)
        )
    if estado == 'activo':
        prestamos = prestamos.filter(Q(fecha_devolucion__isnull=True) | Q(fecha_devolucion__gt=now))
    elif estado == 'devuelto':
        prestamos = prestamos.filter(fecha_devolucion__lte=now)

    total = prestamos.count()
    pvds  = PuntoViveDigital.objects.filter(estado='A').order_by('nombre')

    paginator = Paginator(prestamos, 25)
    page_obj  = paginator.get_page(request.GET.get('page'))

    for p in page_obj:
        p.ya_devuelto = p.fecha_devolucion is not None and p.fecha_devolucion <= now

    return render(request, 'modulo_puntos/lista_prestamos_global.html', {
        'prestamos':   page_obj,
        'page_obj':    page_obj,
        'total':       total,
        'pvds':        pvds,
        'q':           q,
        'pvd_filter':  pvd_filter,
        'estado':      estado,
    })


@login_required(login_url='/login/')
def lista_recursos(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    pvd_id = request.session.get('pvd_activo_id')
    pvd = PuntoViveDigital.objects.filter(pk=pvd_id).first() if pvd_id else None

    from django.db.models import Prefetch
    from django.utils import timezone
    from itertools import groupby

    now = timezone.now()

    es_admin_pvd_solo = (
        not request.user.is_superuser
        and not usuario_es_admin_tic(request.user)
        and request.user.groups.filter(name='Administrador PVD').exists()
    )

    # Admin PVD solo ve su propio punto; Superusuario/Admin TIC ven todos los
    # PVD a la vez, así que para ellos se muestra a qué PVD pertenece cada recurso.
    mostrar_pvd_por_recurso = not es_admin_pvd_solo

    recursos_qs = Recurso.objects.all()
    if es_admin_pvd_solo:
        recursos_qs = recursos_qs.filter(punto_vive_digital_id=pvd_id) if pvd_id else recursos_qs.none()

    tipo_filter = request.GET.get('tipo', '').strip()
    q_filter = request.GET.get('q', '').strip()
    pvd_filter = request.GET.get('pvd_id', '').strip() if mostrar_pvd_por_recurso else ''

    tipos_disponibles = sorted(recursos_qs.values_list('tipo', flat=True).distinct())
    pvds_disponibles = (
        PuntoViveDigital.objects.filter(estado='A').order_by('nombre')
        if mostrar_pvd_por_recurso else []
    )

    display_qs = recursos_qs
    if tipo_filter:
        display_qs = display_qs.filter(tipo=tipo_filter)
    if pvd_filter:
        display_qs = display_qs.filter(punto_vive_digital_id=pvd_filter)
    if q_filter:
        display_qs = display_qs.filter(
            Q(tipo__icontains=q_filter) | Q(codigo__icontains=q_filter)
        )

    recursos = list(
        display_qs
          .select_related('punto_vive_digital')
          .annotate(total_prestamos=Count('prestamorecurso'))
          .prefetch_related(
              Prefetch('prestamorecurso_set',
                       queryset=PrestamoRecurso.objects.order_by('-fecha_entrega'),
                       to_attr='todos_los_prestamos')
          )
          .order_by('tipo', 'punto_vive_digital__nombre', 'codigo')
    )

    for recurso in recursos:
        for p in recurso.todos_los_prestamos:
            p.ya_devuelto = p.fecha_devolucion is not None and p.fecha_devolucion <= now
        ultimo = recurso.todos_los_prestamos[0] if recurso.todos_los_prestamos else None
        recurso.prestado_ahora = ultimo is not None and not ultimo.ya_devuelto if ultimo else False

    prestados_count = sum(1 for r in recursos if r.prestado_ahora)
    disponibles_count = len(recursos) - prestados_count

    total_filtrados = len(recursos)
    # Página grande: cada tarjeta ahora es compacta y se agrupan por tipo,
    # así un mismo tipo (ej. "Portátil") no queda partido entre dos páginas.
    paginator = Paginator(recursos, 200)
    page = request.GET.get('page')
    recursos_page = paginator.get_page(page)

    grupos = []
    for tipo, items in groupby(recursos_page, key=lambda r: r.tipo):
        items = list(items)
        grupos.append({
            'tipo': tipo,
            'items': items,
            'total': len(items),
            'disponibles': sum(1 for r in items if not r.prestado_ahora),
            'prestados': sum(1 for r in items if r.prestado_ahora),
        })

    return render(request, 'modulo_puntos/lista_recursos.html', {
        'recursos': recursos_page,
        'grupos': grupos,
        'pvd': pvd,
        'mostrar_pvd_por_recurso': mostrar_pvd_por_recurso,
        'total_recursos': total_filtrados,
        'prestados_count': prestados_count,
        'disponibles_count': disponibles_count,
        'tipos_disponibles': tipos_disponibles,
        'tipo_filter': tipo_filter,
        'q_filter': q_filter,
        'pvds_disponibles': pvds_disponibles,
        'pvd_filter': pvd_filter,
        'puede_eliminar_recursos': tiene_permiso(request.user, 'inventario.eliminar_recurso'),
    })


@login_required(login_url='/login/')
def crear_recurso(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para registrar recursos.')
        return redirect('modulo_puntos:panel_control')

    pvd_id = request.session.get('pvd_activo_id')
    if not pvd_id:
        messages.warning(request, 'Debes ingresar a un Punto Vive Digital antes de agregar un recurso.')
        return redirect('modulo_puntos:seleccionar_pvd_view')

    pvd = PuntoViveDigital.objects.filter(pk=pvd_id, estado='A').first()
    if not pvd:
        del request.session['pvd_activo_id']
        messages.warning(request, 'El Punto Vive Digital de tu sesión ya no está disponible. Selecciona otro.')
        return redirect('modulo_puntos:seleccionar_pvd_view')

    form = RecursoForm(request.POST or None, pvd_id=pvd.pk)
    if request.method == 'POST':
        if form.is_valid():
            recurso = form.save(commit=False)
            recurso.punto_vive_digital = pvd
            recurso.save()
            registrar_auditoria(request, 'CREATE', 'Recurso', recurso.pk, f'Nuevo recurso: {recurso.tipo} — PVD: {pvd}')
            messages.success(request, f'Recurso "{recurso.tipo}" registrado correctamente.')
            return redirect('modulo_puntos:registrar_recurso')
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/registrar_recurso.html', {'form': form, 'pvd': pvd})


# ── EDITAR RECURSO ─────────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def editar_recurso(request, recurso_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')

    recurso = get_object_or_404(Recurso, pk=recurso_id)
    if not pvd_permitido(request, recurso.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para editar recursos de otro PVD.')
        return redirect('modulo_puntos:registrar_recurso')
    form = RecursoForm(request.POST or None, instance=recurso)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            registrar_auditoria(request, 'UPDATE', 'Recurso', recurso.pk, f'Recurso editado: {recurso.tipo} ({recurso.codigo})')
            messages.success(request, f'Recurso "{recurso.tipo}" actualizado correctamente.')
            return redirect('modulo_puntos:registrar_recurso')
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/registrar_recurso.html', {
        'form': form,
        'editando': True,
        'recurso': recurso,
    })


# ── ELIMINAR RECURSO ──────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def eliminar_recurso(request, recurso_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'inventario.eliminar_recurso'):
        messages.error(request, 'No tienes permiso para eliminar recursos del inventario.')
        return redirect('modulo_puntos:registrar_recurso')

    recurso = get_object_or_404(Recurso, pk=recurso_id)
    if not pvd_permitido(request, recurso.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para eliminar recursos de otro PVD.')
        return redirect('modulo_puntos:registrar_recurso')

    if request.method == 'POST':
        prestamos_activos = PrestamoRecurso.objects.filter(recurso=recurso, fecha_devolucion=None).count()
        if prestamos_activos:
            messages.error(request, f'No se puede eliminar: el recurso tiene {prestamos_activos} préstamo(s) activo(s).')
            return redirect('modulo_puntos:registrar_recurso')
        registrar_auditoria(request, 'DELETE', 'Recurso', recurso.pk,
                            f'Recurso eliminado: {recurso.tipo} ({recurso.codigo or "sin código"})')
        recurso.delete()
        messages.success(request, 'Recurso eliminado correctamente.')

    return redirect('modulo_puntos:registrar_recurso')


