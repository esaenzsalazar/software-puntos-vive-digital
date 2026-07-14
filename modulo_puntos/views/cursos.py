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
# CURSOS / TALLERES
# ==============================================================================

@login_required(login_url='/login/')
def lista_cursos(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'cursos.ver'):
        messages.error(request, 'No tienes permiso para ver cursos.')
        return redirect('modulo_puntos:panel_control')

    pvd_id = request.session.get('pvd_activo_id')
    es_admin_tic = usuario_es_admin_tic(request.user)

    if es_admin_tic:
        qs = Curso.objects.select_related('punto_vive_digital', 'registrado_por').all()
    elif pvd_id:
        qs = Curso.objects.filter(punto_vive_digital_id=pvd_id).select_related('punto_vive_digital', 'registrado_por')
    else:
        qs = Curso.objects.none()
    qs = qs.annotate(total_inscritos=Count('inscripciones', filter=Q(inscripciones__estado__in=['I', 'C'])))

    estado_filtro = request.GET.get('estado', '')
    fecha_desde_filtro = request.GET.get('fecha_desde', '').strip()
    fecha_hasta_filtro = request.GET.get('fecha_hasta', '').strip()
    q_filtro = request.GET.get('q', '').strip()
    if estado_filtro:
        qs = qs.filter(estado=estado_filtro)
    if fecha_desde_filtro:
        qs = qs.filter(fecha_inicio__gte=fecha_desde_filtro)
    if fecha_hasta_filtro:
        qs = qs.filter(fecha_inicio__lte=fecha_hasta_filtro)
    if q_filtro:
        qs = qs.filter(
            Q(nombre__icontains=q_filtro) |
            Q(poblacion_objetivo__icontains=q_filtro) |
            Q(descripcion__icontains=q_filtro)
        )

    paginator = Paginator(qs.order_by('-fecha_inicio'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'modulo_puntos/cursos/lista_cursos.html', {
        'cursos': page_obj,
        'page_obj': page_obj,
        'estado_filtro': estado_filtro,
        'fecha_desde_filtro': fecha_desde_filtro,
        'fecha_hasta_filtro': fecha_hasta_filtro,
        'q_filtro': q_filtro,
        'estados': Curso.ESTADO_CHOICES,
        'es_admin_tic': es_admin_tic,
        'total_cursos': qs.count(),
    })


@login_required(login_url='/login/')
def crear_curso(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'cursos.crear'):
        messages.error(request, 'No tienes permiso para crear cursos.')
        return redirect('modulo_puntos:lista_cursos')

    pvd_id = request.session.get('pvd_activo_id')
    if not pvd_id:
        messages.error(request, 'Debes seleccionar un Punto Vive Digital primero.')
        return redirect('modulo_puntos:seleccionar_pvd_view')

    form = CursoForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            curso = form.save(commit=False)
            if pvd_id:
                curso.punto_vive_digital_id = pvd_id
            curso.registrado_por = request.user
            curso.save()
            registrar_auditoria(request, 'CREATE', 'Curso', curso.pk, f'Curso creado: {curso.nombre}')
            messages.success(request, f'Curso "{curso.nombre}" creado correctamente.')
            return redirect('modulo_puntos:detalle_curso', curso_id=curso.pk)
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/cursos/form_curso.html', {
        'form': form,
        'titulo': 'Nuevo Curso / Taller',
        'accion': 'crear',
    })


@login_required(login_url='/login/')
def editar_curso(request, curso_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'cursos.editar'):
        messages.error(request, 'No tienes permiso para editar cursos.')
        return redirect('modulo_puntos:lista_cursos')

    curso = get_object_or_404(Curso, pk=curso_id)
    if not pvd_permitido(request, curso.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para editar cursos de otro PVD.')
        return redirect('modulo_puntos:lista_cursos')
    form = CursoForm(request.POST or None, instance=curso)

    if request.method == 'POST':
        if form.is_valid():
            curso = form.save()
            registrar_auditoria(request, 'UPDATE', 'Curso', curso.pk, f'Curso editado: {curso.nombre}')
            messages.success(request, 'Curso actualizado correctamente.')
            return redirect('modulo_puntos:detalle_curso', curso_id=curso.pk)
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/cursos/form_curso.html', {
        'form': form,
        'titulo': f'Editar: {curso.nombre}',
        'accion': 'editar',
        'curso': curso,
    })


@login_required(login_url='/login/')
def detalle_curso(request, curso_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'cursos.ver'):
        messages.error(request, 'No tienes permiso para ver cursos.')
        return redirect('modulo_puntos:panel_control')

    curso = get_object_or_404(Curso.objects.select_related('punto_vive_digital', 'registrado_por'), pk=curso_id)
    if not pvd_permitido(request, curso.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para ver cursos de otro PVD.')
        return redirect('modulo_puntos:lista_cursos')
    sesiones = curso.sesiones.order_by('numero_sesion')
    inscripciones = curso.inscripciones.select_related('ciudadano').order_by('fecha_inscripcion')

    return render(request, 'modulo_puntos/cursos/detalle_curso.html', {
        'curso': curso,
        'sesiones': sesiones,
        'inscripciones': inscripciones,
    })


@login_required(login_url='/login/')
def crear_sesion_curso(request, curso_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'cursos.sesiones'):
        messages.error(request, 'No tienes permiso para gestionar sesiones de cursos.')
        return redirect('modulo_puntos:lista_cursos')

    curso = get_object_or_404(Curso, pk=curso_id)
    if not pvd_permitido(request, curso.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para gestionar sesiones de cursos de otro PVD.')
        return redirect('modulo_puntos:lista_cursos')
    ultimo_num = curso.sesiones.aggregate(max_n=Max('numero_sesion'))['max_n'] or 0
    form = SesionCursoForm(request.POST or None, initial={'numero_sesion': ultimo_num + 1})

    if request.method == 'POST':
        if form.is_valid():
            sesion = form.save(commit=False)
            sesion.curso = curso
            sesion.save()
            registrar_auditoria(request, 'CREATE', 'SesionCurso', sesion.pk,
                                f'Sesión {sesion.numero_sesion} creada para curso {curso.nombre}')
            messages.success(request, f'Sesión {sesion.numero_sesion} registrada.')
            return redirect('modulo_puntos:detalle_curso', curso_id=curso.pk)
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/cursos/form_sesion.html', {
        'form': form,
        'curso': curso,
        'titulo': f'Nueva Sesión — {curso.nombre}',
    })


@login_required(login_url='/login/')
def inscribir_ciudadano(request, curso_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'cursos.inscribir'):
        messages.error(request, 'No tienes permiso para inscribir ciudadanos en cursos.')
        return redirect('modulo_puntos:lista_cursos')

    curso = get_object_or_404(Curso, pk=curso_id)
    if not pvd_permitido(request, curso.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para inscribir ciudadanos en cursos de otro PVD.')
        return redirect('modulo_puntos:lista_cursos')
    inscritos_ids = InscripcionCurso.objects.filter(curso=curso).values_list('ciudadano_id', flat=True)
    ciudadanos_disponibles = Ciudadano.objects.filter(estado='A').exclude(pk__in=inscritos_ids)

    form = InscripcionCursoForm(request.POST or None)
    form.fields['ciudadano'].queryset = ciudadanos_disponibles

    if request.method == 'POST':
        if form.is_valid():
            inscripcion = form.save(commit=False)
            inscripcion.curso = curso
            inscripcion.registrado_por = request.user
            inscripcion.save()
            registrar_auditoria(request, 'CREATE', 'InscripcionCurso', inscripcion.pk,
                                f'{inscripcion.ciudadano} inscrito en {curso.nombre}')
            messages.success(request, f'{inscripcion.ciudadano} inscrito correctamente.')
            return redirect('modulo_puntos:detalle_curso', curso_id=curso.pk)
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/cursos/form_inscripcion.html', {
        'form': form,
        'curso': curso,
        'titulo': f'Inscribir Ciudadano — {curso.nombre}',
    })


@login_required(login_url='/login/')
def marcar_asistencia(request, sesion_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'cursos.asistencia'):
        messages.error(request, 'No tienes permiso para registrar asistencia.')
        return redirect('modulo_puntos:lista_cursos')

    sesion = get_object_or_404(SesionCurso.objects.select_related('curso'), pk=sesion_id)
    if not pvd_permitido(request, sesion.curso.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para registrar asistencia en cursos de otro PVD.')
        return redirect('modulo_puntos:lista_cursos')
    inscritos = InscripcionCurso.objects.filter(
        curso=sesion.curso, estado__in=['I', 'C']
    ).select_related('ciudadano')

    asistencias_existentes = {
        a.ciudadano_id: a for a in AsistenciaSesion.objects.filter(sesion=sesion)
    }

    if request.method == 'POST':
        try:
            presentes = {int(v) for v in request.POST.getlist('asistio') if str(v).strip().isdigit()}
        except (ValueError, TypeError):
            presentes = set()
        for insc in inscritos:
            cid = insc.ciudadano_id
            asistio = cid in presentes
            if cid in asistencias_existentes:
                a = asistencias_existentes[cid]
                if a.asistio != asistio:
                    a.asistio = asistio
                    a.save()
            else:
                AsistenciaSesion.objects.create(sesion=sesion, ciudadano=insc.ciudadano, asistio=asistio)
        registrar_auditoria(request, 'UPDATE', 'SesionCurso', sesion.pk,
                            f'Asistencia registrada para sesión {sesion.numero_sesion} de {sesion.curso.nombre}')
        messages.success(request, 'Asistencia guardada correctamente.')
        return redirect('modulo_puntos:detalle_curso', curso_id=sesion.curso.pk)

    lista = []
    for insc in inscritos:
        lista.append({
            'ciudadano': insc.ciudadano,
            'asistio': asistencias_existentes.get(insc.ciudadano_id, None) and asistencias_existentes[insc.ciudadano_id].asistio,
        })

    return render(request, 'modulo_puntos/cursos/asistencia_sesion.html', {
        'sesion': sesion,
        'lista': lista,
    })


@login_required(login_url='/login/')
def cambiar_estado_curso(request, curso_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'cursos.editar'):
        messages.error(request, 'No tienes permiso para editar cursos.')
        return redirect('modulo_puntos:lista_cursos')
    if request.method != 'POST':
        return redirect('modulo_puntos:lista_cursos')

    curso = get_object_or_404(Curso, pk=curso_id)
    if not pvd_permitido(request, curso.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para cambiar el estado de cursos de otro PVD.')
        return redirect('modulo_puntos:lista_cursos')
    nuevo_estado = (request.POST.get('nuevo_estado') or request.POST.get('estado', '')).strip()
    estados_validos = {'PL', 'AC', 'FI', 'CA'}
    if nuevo_estado not in estados_validos:
        messages.error(request, 'Estado no válido.')
    else:
        curso.estado = nuevo_estado
        curso.save(update_fields=['estado'])
        registrar_auditoria(request, 'UPDATE', 'Curso', curso.pk,
                            f'Estado cambiado a {curso.get_estado_display()}')
        messages.success(request, f'Curso marcado como "{curso.get_estado_display()}".')
    return redirect('modulo_puntos:detalle_curso', curso_id=curso.pk)


@login_required(login_url='/login/')
def eliminar_curso(request, curso_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'cursos.editar'):
        messages.error(request, 'No tienes permiso para eliminar cursos.')
        return redirect('modulo_puntos:lista_cursos')
    curso = get_object_or_404(Curso, pk=curso_id)
    if not pvd_permitido(request, curso.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para eliminar cursos de otro PVD.')
        return redirect('modulo_puntos:lista_cursos')
    if request.method == 'POST':
        nombre = curso.nombre
        registrar_auditoria(request, 'DELETE', 'Curso', curso.pk, f'Curso eliminado: {nombre}')
        curso.delete()
        messages.success(request, f'Curso "{nombre}" eliminado.')
        return redirect('modulo_puntos:lista_cursos')
    return redirect('modulo_puntos:detalle_curso', curso_id=curso.pk)


@login_required(login_url='/login/')
def eliminar_sesion_curso(request, sesion_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')
    if not tiene_permiso(request.user, 'cursos.sesiones'):
        messages.error(request, 'No tienes permiso para gestionar sesiones.')
        return redirect('modulo_puntos:lista_cursos')
    sesion = get_object_or_404(SesionCurso.objects.select_related('curso'), pk=sesion_id)
    curso_id = sesion.curso_id
    if not pvd_permitido(request, sesion.curso.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para eliminar sesiones de cursos de otro PVD.')
        return redirect('modulo_puntos:lista_cursos')
    if request.method == 'POST':
        registrar_auditoria(request, 'DELETE', 'SesionCurso', sesion.pk,
                            f'Sesión {sesion.numero_sesion} eliminada del curso #{curso_id}')
        sesion.delete()
        messages.success(request, f'Sesión {sesion.numero_sesion} eliminada.')
    return redirect('modulo_puntos:detalle_curso', curso_id=curso_id)


@login_required(login_url='/login/')
def eliminar_inscripcion(request, inscripcion_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')
    inscripcion = get_object_or_404(InscripcionCurso.objects.select_related('curso'), pk=inscripcion_id)
    curso_id = inscripcion.curso_id
    if not pvd_permitido(request, inscripcion.curso.punto_vive_digital_id):
        messages.error(request, 'No tienes permiso para eliminar inscripciones de cursos de otro PVD.')
        return redirect('modulo_puntos:lista_cursos')
    if request.method == 'POST':
        nombre = inscripcion.ciudadano.get_nombre_completo() if inscripcion.ciudadano else '—'
        registrar_auditoria(request, 'DELETE', 'InscripcionCurso', inscripcion.pk,
                            f'Inscripción eliminada: {nombre} del curso #{curso_id}')
        inscripcion.delete()
        messages.success(request, f'Inscripción de {nombre} eliminada.')
    return redirect('modulo_puntos:detalle_curso', curso_id=curso_id)


