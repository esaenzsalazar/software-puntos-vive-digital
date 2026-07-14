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

# ── REPORTES ───────────────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def reportes(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    fecha_desde_str = request.GET.get('fecha_desde', '')
    fecha_hasta_str = request.GET.get('fecha_hasta', '')
    fecha_desde = None
    fecha_hasta = None
    try:
        if fecha_desde_str:
            fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d').date()
        if fecha_hasta_str:
            fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d').date()
    except ValueError:
        pass

    # Filtrar por PVD activo cuando corresponde
    es_admin_pvd_rpt = usuario_necesita_seleccionar_pvd(request.user)
    pvd_id_rpt = obtener_pvd_activo_id(request)
    if es_admin_pvd_rpt and not pvd_id_rpt:
        # Fail-closed: sin PVD activo en sesión, un Admin PVD no puede ver reportes
        # (antes esto dejaba los querysets sin filtrar y exponía todos los PVD).
        messages.warning(request, 'Selecciona un Punto Vive Digital antes de ver los reportes.')
        return redirect('modulo_puntos:seleccionar_pvd_view')

    pvd_nombre_rpt = None
    if pvd_id_rpt:
        pvd_obj = PuntoViveDigital.objects.filter(pk=pvd_id_rpt).first()
        pvd_nombre_rpt = pvd_obj.nombre if pvd_obj else None

    atencion_qs = Atencion.objects.all()
    servicio_qs = Servicio.objects.all()
    ciudadano_qs = Ciudadano.objects.all()
    prestamo_qs  = PrestamoRecurso.objects.all()
    satisfaccion_qs = Satisfaccion.objects.all()

    if pvd_id_rpt:
        # Admin PVD siempre filtrado; Super/TIC filtrados sólo si eligieron un PVD activo.
        atencion_qs  = atencion_qs.filter(punto_vive_digital_id=pvd_id_rpt)
        servicio_qs  = servicio_qs.filter(atencion__punto_vive_digital_id=pvd_id_rpt)
        ciudadano_qs = ciudadano_qs.filter(punto_vive_digital_id=pvd_id_rpt)
        prestamo_qs  = prestamo_qs.filter(recurso__punto_vive_digital_id=pvd_id_rpt)
        satisfaccion_qs = satisfaccion_qs.filter(atencion__punto_vive_digital_id=pvd_id_rpt)

    if fecha_desde:
        atencion_qs = atencion_qs.filter(fecha__gte=fecha_desde)
        servicio_qs = servicio_qs.filter(atencion__fecha__gte=fecha_desde)
    if fecha_hasta:
        atencion_qs = atencion_qs.filter(fecha__lte=fecha_hasta)
        servicio_qs = servicio_qs.filter(atencion__fecha__lte=fecha_hasta)

    total_ciudadanos = ciudadano_qs.count()
    ciudadanos_activos = ciudadano_qs.filter(estado='A').count()
    total_atenciones = atencion_qs.count()
    atenciones_pendientes = atencion_qs.filter(estado='P').count()
    atenciones_finalizadas = atencion_qs.filter(estado='F').count()
    atenciones_canceladas = atencion_qs.filter(estado='C').count()
    total_servicios = servicio_qs.count()
    total_prestamos = prestamo_qs.count()
    prestamos_activos = prestamo_qs.filter(fecha_devolucion__isnull=True).count()

    satisfaccion_promedio = Satisfaccion.con_puntaje(satisfaccion_qs).aggregate(
        promedio=Avg('puntaje')
    )['promedio']

    servicios_por_tipo = servicio_qs.values('tipo').annotate(
        total=Count('id')
    ).order_by('-total', 'tipo')

    atenciones_por_admin = atencion_qs.values(
        'operador__first_name',
        'operador__last_name',
        'operador__username'
    ).annotate(
        total=Count('id')
    ).order_by('-total')

    atenciones_recientes = atencion_qs.select_related(
        'ciudadano', 'operador'
    ).order_by('-fecha', '-hora_inicio')[:10]

    gen_map = dict(Ciudadano.GENERO_CHOICES)
    ciudadanos_por_genero = []
    for row in ciudadano_qs.values('genero').annotate(total=Count('id')).order_by('-total'):
        clave = row['genero'] or ''
        ciudadanos_por_genero.append({
            'etiqueta': gen_map.get(clave, clave or 'Sin dato'),
            'total': row['total'],
        })

    ciudadanos_por_etnia = list(
        ciudadano_qs.exclude(etnia__isnull=True).exclude(etnia='').values('etnia').annotate(
            total=Count('id')
        ).order_by('-total')[:20]
    )

    ciudadanos_por_nvleduc = list(
        ciudadano_qs.exclude(nivel_educativo__isnull=True).exclude(nivel_educativo='').values('nivel_educativo').annotate(
            total=Count('id')
        ).order_by('-total')[:20]
    )

    ciudadanos_por_estrato = list(
        ciudadano_qs.values('estrato').annotate(total=Count('id')).order_by('estrato')
    )

    ciudadanos_por_ocupacion = list(
        ciudadano_qs.exclude(ocupacion__isnull=True).exclude(ocupacion='').values('ocupacion').annotate(
            total=Count('id')
        ).order_by('-total')[:15]
    )

    ciudadanos_con_discapacidad = ciudadano_qs.filter(tiene_discapacidad=True).count()
    ciudadanos_sin_discapacidad = ciudadano_qs.filter(tiene_discapacidad=False).count()

    atenciones_por_mes = list(
        atencion_qs.annotate(mes=TruncMonth('fecha'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('-mes')[:12]
    )

    # Reporte de salas
    habilitacion_qs = HabilitacionSala.objects.all()
    if pvd_id_rpt:
        habilitacion_qs = habilitacion_qs.filter(sala__punto_vive_digital_id=pvd_id_rpt)
    if fecha_desde:
        habilitacion_qs = habilitacion_qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        habilitacion_qs = habilitacion_qs.filter(fecha__lte=fecha_hasta)

    uso_por_sala = list(
        habilitacion_qs
        .exclude(estado='X')
        .values('sala__nombre', 'sala__capacidad')
        .annotate(total_usos=Count('id'), total_personas=Avg('capacidad_requerida'))
        .order_by('-total_usos')[:10]
    )
    tipo_uso_map = dict(HabilitacionSala.TIPO_USO_CHOICES)
    uso_por_tipo = list(
        habilitacion_qs
        .exclude(estado='X')
        .values('tipo_uso')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    for item in uso_por_tipo:
        item['tipo_uso_label'] = tipo_uso_map.get(item['tipo_uso'], item['tipo_uso'])

    # KPIs operacionales
    from django.db.models import ExpressionWrapper, DurationField, F
    tasa_finalizacion = (
        round(atenciones_finalizadas * 100 / total_atenciones, 1)
        if total_atenciones > 0 else 0
    )
    tasa_cancelacion = (
        round(atenciones_canceladas * 100 / total_atenciones, 1)
        if total_atenciones > 0 else 0
    )

    satisfaccion_por_admin = list(
        Satisfaccion.con_puntaje(satisfaccion_qs)
        .filter(atencion__operador__isnull=False)
        .values('atencion__operador__first_name', 'atencion__operador__last_name', 'atencion__operador__username')
        .annotate(promedio=Avg('puntaje'), total=Count('id'))
        .order_by('-promedio')
    )

    return render(request, 'modulo_puntos/reportes.html', {
        'total_ciudadanos': total_ciudadanos,
        'ciudadanos_activos': ciudadanos_activos,
        'total_atenciones': total_atenciones,
        'atenciones_pendientes': atenciones_pendientes,
        'atenciones_finalizadas': atenciones_finalizadas,
        'atenciones_canceladas': atenciones_canceladas,
        'total_servicios': total_servicios,
        'total_prestamos': total_prestamos,
        'prestamos_activos': prestamos_activos,
        'satisfaccion_promedio': satisfaccion_promedio,
        'servicios_por_tipo': servicios_por_tipo,
        'atenciones_por_admin': atenciones_por_admin,
        'atenciones_recientes': atenciones_recientes,
        'ciudadanos_por_genero': ciudadanos_por_genero,
        'ciudadanos_por_etnia': ciudadanos_por_etnia,
        'ciudadanos_por_nvleduc': ciudadanos_por_nvleduc,
        'ciudadanos_por_estrato': ciudadanos_por_estrato,
        'ciudadanos_por_ocupacion': ciudadanos_por_ocupacion,
        'ciudadanos_con_discapacidad': ciudadanos_con_discapacidad,
        'ciudadanos_sin_discapacidad': ciudadanos_sin_discapacidad,
        'atenciones_por_mes': atenciones_por_mes,
        'fecha_desde': fecha_desde_str,
        'fecha_hasta': fecha_hasta_str,
        'pvd_nombre_rpt': pvd_nombre_rpt,
        'tasa_finalizacion': tasa_finalizacion,
        'tasa_cancelacion': tasa_cancelacion,
        'satisfaccion_por_admin': satisfaccion_por_admin,
        'uso_por_sala': uso_por_sala,
        'uso_por_tipo': uso_por_tipo,
        'tipo_uso_map': tipo_uso_map,
    })


