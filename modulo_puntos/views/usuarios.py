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

# ── GESTIÓN DE USUARIOS ────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def crear_usuario_sistema(request):
    if not (usuario_es_superusuario(request.user) or usuario_es_admin_tic(request.user)):
        messages.error(request, 'No tienes permisos para crear usuarios del sistema.')
        return redirect('modulo_puntos:panel_control')

    pvd_pendiente = None
    pvd_pendiente_id = request.session.get('pvd_pendiente_id')
    if pvd_pendiente_id:
        pvd_pendiente = PuntoViveDigital.objects.filter(pk=pvd_pendiente_id).first()
        if not pvd_pendiente:
            request.session.pop('pvd_pendiente_id', None)
            request.session.pop('pvd_pendiente_nombre', None)

    # Admin TIC solo puede crear Admin PVD; si hay un PVD recién creado esperando
    # administrador, se fuerza el rol Admin PVD también para el Superusuario.
    solo_pvd = (not usuario_es_superusuario(request.user)) or pvd_pendiente is not None

    initial = {'pvd_asignado': pvd_pendiente.pk} if pvd_pendiente else None
    form = CrearUsuarioSistemaForm(request.POST or None, solo_pvd=solo_pvd, initial=initial)
    if request.method == 'POST':
        if form.is_valid():
            rol_elegido = form.cleaned_data['rol']
            # Doble verificación: si eligió admin_tic pero no es super → error
            if rol_elegido == 'admin_tic' and solo_pvd:
                messages.error(request, 'Solo el Superusuario puede crear Administradores TIC.')
                return redirect('modulo_puntos:crear_usuario_sistema')

            user = form.save()
            nombre_grupo = 'Administrador TIC' if rol_elegido == 'admin_tic' else 'Administrador PVD'
            grupo, _ = Group.objects.get_or_create(name=nombre_grupo)
            user.groups.add(grupo)

            pvd_asignado = form.cleaned_data.get('pvd_asignado')
            if rol_elegido == 'admin_pvd' and pvd_asignado:
                UserProfile.objects.update_or_create(
                    usuario=user,
                    defaults={'rol': 'admin_pvd', 'punto_asignado': pvd_asignado},
                )
                sincronizar_admin_a_cargo(user, pvd_nuevo=pvd_asignado)

            registrar_auditoria(request, 'CREATE', 'User', user.pk,
                                f'{nombre_grupo} creado: {user.username} — {user.get_full_name()}')

            mensaje = (
                f'{nombre_grupo} creado correctamente. '
                f'Usuario generado: "{user.username}"'
            )
            if pvd_asignado:
                mensaje += f'. Asignado al PVD "{pvd_asignado.nombre}".'
            messages.success(request, mensaje)

            if pvd_pendiente:
                request.session.pop('pvd_pendiente_id', None)
                request.session.pop('pvd_pendiente_nombre', None)
                if pvd_asignado and pvd_asignado.pk == pvd_pendiente.pk:
                    messages.success(request, f'El PVD "{pvd_pendiente.nombre}" ya cuenta con su administrador.')
                return redirect('modulo_puntos:lista_pvd')

            return redirect('modulo_puntos:accesos_temporales')
        messages.error(request, 'No se pudo crear el usuario. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/crear_usuario_sistema.html', {
        'form': form,
        'solo_pvd': solo_pvd,
        'pvd_pendiente': pvd_pendiente,
    })


@login_required(login_url='/login/')
def crear_admin_tic(request):
    return redirect('modulo_puntos:crear_usuario_sistema')


@login_required(login_url='/login/')
def crear_admin_pvd(request):
    return redirect('modulo_puntos:crear_usuario_sistema')


@login_required(login_url='/login/')
def lista_admins_pvd(request):
    if not usuario_es_admin_tic(request.user):
        messages.error(request, 'No tienes permisos para gestionar administradores PVD.')
        return redirect('modulo_puntos:panel_control')

    admins_pvd = (
        User.objects
        .filter(groups__name='Administrador PVD')
        .select_related('pvd_profile__punto_asignado')
        .distinct()
        .order_by('last_name', 'first_name', 'username')
    )

    return render(request, 'modulo_puntos/lista_admins_pvd.html', {
        'admins_pvd': admins_pvd,
    })


@login_required(login_url='/login/')
def editar_admin_pvd(request, user_id):
    if not usuario_es_admin_tic(request.user):
        messages.error(request, 'No tienes permisos para editar administradores PVD.')
        return redirect('modulo_puntos:panel_control')

    admin_pvd = get_object_or_404(User, pk=user_id, groups__name='Administrador PVD')
    profile, _ = UserProfile.objects.get_or_create(usuario=admin_pvd, defaults={'rol': 'admin_pvd'})

    form = EditarAdminPvdForm(
        request.POST or None,
        instance=admin_pvd,
        initial={'pvd_asignado': profile.punto_asignado_id},
    )
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            pvd_anterior = profile.punto_asignado
            profile.punto_asignado = form.cleaned_data['pvd_asignado']
            profile.save(update_fields=['punto_asignado'])
            sincronizar_admin_a_cargo(admin_pvd, pvd_anterior=pvd_anterior, pvd_nuevo=profile.punto_asignado)

            nueva_pwd = form.cleaned_data.get('password1')
            if nueva_pwd:
                admin_pvd.set_password(nueva_pwd)
                admin_pvd.save(update_fields=['password'])

            registrar_auditoria(request, 'UPDATE', 'User', admin_pvd.pk,
                                f'Administrador PVD editado: {admin_pvd.username}')
            messages.success(
                request,
                f'Administrador "{admin_pvd.get_full_name() or admin_pvd.username}" actualizado correctamente.'
            )
            return redirect('modulo_puntos:lista_admins_pvd')
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/editar_admin_pvd.html', {
        'form': form,
        'admin_pvd': admin_pvd,
    })


# ── GESTIÓN DE ROLES Y PERMISOS ────────────────────────────────────────────────

@user_passes_test(lambda u: u.is_superuser)
def gestionar_roles(request):
    roles = Group.objects.all()
    permisos_disponibles = Permission.objects.filter(
        content_type__app_label='modulo_puntos_app'
    ).order_by('content_type__model')

    if request.method == 'POST':
        nombre_rol = request.POST.get('nombre_rol')
        permisos_id = request.POST.getlist('permisos')
        rol_id = request.POST.get('rol_id')

        if rol_id:
            rol = get_object_or_404(Group, id=rol_id)
            rol.name = nombre_rol
            rol.save()
        else:
            rol, _ = Group.objects.get_or_create(name=nombre_rol)

        rol.permissions.set(Permission.objects.filter(id__in=permisos_id))
        messages.success(request, f"Configuración de '{nombre_rol}' guardada.")
        return redirect('modulo_puntos:gestionar_roles')

    return render(request, 'modulo_puntos/gestionar_roles.html', {
        'roles': roles,
        'permisos_disponibles': permisos_disponibles
    })


@user_passes_test(lambda u: u.is_superuser)
def asignar_rol_usuario(request, user_id):
    usuario = get_object_or_404(User, pk=user_id)
    grupos = Group.objects.all()

    if request.method == 'POST':
        grupo_id = request.POST.get('grupo_id')
        if grupo_id:
            grupo = get_object_or_404(Group, pk=grupo_id)
            usuario.groups.set([grupo])
            messages.success(request, f'Rol "{grupo.name}" asignado a {usuario.username}.')
        else:
            usuario.groups.clear()
            messages.success(request, f'Roles removidos de {usuario.username}.')
        return redirect('modulo_puntos:gestionar_roles')

    permisos_disponibles = Permission.objects.filter(
        content_type__app_label='modulo_puntos_app'
    ).order_by('content_type__model')

    return render(request, 'modulo_puntos/gestionar_roles.html', {
        'usuario_objetivo': usuario,
        'grupos': grupos,
        'roles': grupos,
        'permisos_disponibles': permisos_disponibles,
    })


@user_passes_test(lambda u: u.is_superuser)
def crear_grupo_rol(request):
    if request.method == 'POST':
        nombre_rol = request.POST.get('nombre_rol', '').strip()
        if nombre_rol:
            grupo, created = Group.objects.get_or_create(name=nombre_rol)
            if created:
                messages.success(request, f'Rol "{nombre_rol}" creado correctamente.')
            else:
                messages.warning(request, f'El rol "{nombre_rol}" ya existe.')
    return redirect('modulo_puntos:gestionar_roles')


# ── ACCESOS TEMPORALES ─────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def accesos_temporales(request):
    if not usuario_es_admin_tic(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('modulo_puntos:panel_control')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        pvd_id = request.POST.get('pvd_id') or None
        campo = request.POST.get('campo', 'pvd_temporal')

        try:
            usuario_objetivo = User.objects.get(pk=user_id, groups__name='Administrador PVD')
        except User.DoesNotExist:
            messages.error(request, 'Usuario no encontrado.')
            return redirect('modulo_puntos:accesos_temporales')

        profile, _ = UserProfile.objects.get_or_create(
            usuario=usuario_objetivo,
            defaults={'rol': 'admin_pvd'}
        )

        nombre_usuario = usuario_objetivo.get_full_name() or usuario_objetivo.username

        if campo == 'punto_asignado':
            pvd_anterior = profile.punto_asignado
            if pvd_id:
                try:
                    pvd = PuntoViveDigital.objects.get(pk=pvd_id)
                    profile.punto_asignado = pvd
                    profile.save(update_fields=['punto_asignado'])
                    sincronizar_admin_a_cargo(usuario_objetivo, pvd_anterior=pvd_anterior, pvd_nuevo=pvd)
                    messages.success(request, f'PVD asignado a {nombre_usuario}: {pvd.nombre}')
                except PuntoViveDigital.DoesNotExist:
                    messages.error(request, 'PVD no encontrado.')
            else:
                profile.punto_asignado = None
                profile.save(update_fields=['punto_asignado'])
                sincronizar_admin_a_cargo(usuario_objetivo, pvd_anterior=pvd_anterior, pvd_nuevo=None)
                messages.success(request, f'PVD permanente de {nombre_usuario} eliminado.')
        else:
            if pvd_id:
                try:
                    pvd = PuntoViveDigital.objects.get(pk=pvd_id, estado='A')
                    profile.pvd_temporal = pvd
                    profile.save(update_fields=['pvd_temporal'])
                    messages.success(request, f'Acceso temporal a "{pvd.nombre}" otorgado a {nombre_usuario}.')
                except PuntoViveDigital.DoesNotExist:
                    messages.error(request, 'PVD no encontrado o inactivo.')
            else:
                nombre_pvd = profile.pvd_temporal.nombre if profile.pvd_temporal else '—'
                profile.pvd_temporal = None
                profile.save(update_fields=['pvd_temporal'])
                messages.success(request, f'Acceso temporal de {nombre_usuario} a "{nombre_pvd}" revocado.')

        registrar_auditoria(
            request, 'UPDATE', 'UserProfile', profile.pk,
            f'{request.user.username} modificó acceso PVD de {nombre_usuario}'
        )
        return redirect('modulo_puntos:accesos_temporales')

    admins_pvd = (
        User.objects
        .filter(groups__name='Administrador PVD')
        .select_related('pvd_profile__punto_asignado', 'pvd_profile__pvd_temporal')
        .distinct()
        .order_by('last_name', 'first_name', 'username')
    )
    pvds_activos = PuntoViveDigital.objects.filter(estado='A').order_by('nombre')

    return render(request, 'modulo_puntos/accesos_temporales.html', {
        'admins_pvd': admins_pvd,
        'pvds_activos': pvds_activos,
    })


