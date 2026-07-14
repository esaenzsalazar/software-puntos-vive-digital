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

# ── MÓDULO PERMISOS ────────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def lista_permisos_roles(request):
    es_superusuario = request.user.is_superuser
    es_admin_tic = not es_superusuario and usuario_es_admin_tic(request.user)

    if not (es_superusuario or es_admin_tic):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('modulo_puntos:panel_control')

    roles = [('admin_tic', 'Administrador TIC'), ('admin_pvd', 'Administrador PVD')]
    usuarios_con_permisos = User.objects.filter(
        groups__name__in=['Administrador TIC', 'Administrador PVD']
    ).distinct().order_by('last_name', 'first_name', 'username')

    permisos = PermisoDefinicion.objects.filter(activo=True).order_by('categoria', 'nombre')

    if request.method == 'POST':
        todos_permisos = list(PermisoDefinicion.objects.filter(activo=True))
        for permiso in todos_permisos:
            for rol_codigo, _ in roles:
                checkbox_name = f'perm_{permiso.pk}_{rol_codigo}'
                tiene = checkbox_name in request.POST
                if tiene:
                    PermisoRol.objects.get_or_create(
                        rol=rol_codigo,
                        permiso=permiso,
                        defaults={'otorgado_por': request.user},
                    )
                else:
                    PermisoRol.objects.filter(rol=rol_codigo, permiso=permiso).delete()

            if es_superusuario:
                delegable = f'delegable_{permiso.pk}' in request.POST
                if delegable != permiso.delegable_por_ofitic:
                    permiso.delegable_por_ofitic = delegable
                    permiso.save(update_fields=['delegable_por_ofitic'])

        actor = 'superusuario' if es_superusuario else 'admin_tic'
        registrar_auditoria(
            request, 'UPDATE', 'PermisoRol', None,
            f'Matriz de permisos por rol actualizada por {actor}.'
        )
        messages.success(request, 'Permisos actualizados correctamente.')
        return redirect('modulo_puntos:lista_permisos_roles')

    asignaciones = set(PermisoRol.objects.values_list('permiso_id', 'rol'))

    roles_data = []
    for rol_codigo, rol_nombre in roles:
        categorias = {}
        for permiso in permisos:
            cat = permiso.categoria
            if cat not in categorias:
                categorias[cat] = []
            categorias[cat].append({
                'permiso': permiso,
                'marcado': (permiso.pk, rol_codigo) in asignaciones,
                'field_name': f'perm_{permiso.pk}_{rol_codigo}',
            })
        roles_data.append({'codigo': rol_codigo, 'nombre': rol_nombre, 'categorias': categorias})

    delegables_data = []
    if es_superusuario:
        categorias_del = {}
        for permiso in permisos:
            cat = permiso.categoria
            if cat not in categorias_del:
                categorias_del[cat] = []
            categorias_del[cat].append(permiso)
        delegables_data = categorias_del

    return render(request, 'modulo_puntos/permisos/lista_roles.html', {
        'roles_data': roles_data,
        'usuarios_con_permisos': usuarios_con_permisos,
        'es_superusuario': es_superusuario,
        'delegables_data': delegables_data,
    })



@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_superuser)
def editar_permiso(request, permiso_id):
    """Editar definición de permiso existente. Solo superusuario."""
    permiso = get_object_or_404(PermisoDefinicion, pk=permiso_id)
    form = PermisoDefinicionForm(request.POST or None, instance=permiso)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            registrar_auditoria(
                request, 'UPDATE', 'PermisoDefinicion', permiso.pk,
                f'Permiso editado: [{permiso.categoria}] {permiso.nombre} ({permiso.codigo})'
            )
            messages.success(request, f'Permiso "{permiso.nombre}" actualizado correctamente.')
            return redirect('modulo_puntos:lista_permisos_roles')
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/permisos/form_permiso.html', {
        'form': form,
        'titulo': f'Editar Permiso: {permiso.nombre}',
        'accion': 'editar',
        'permiso': permiso,
    })


@login_required(login_url='/login/')
def permisos_usuario(request, user_id):
    """Overrides individuales por usuario. Superusuario: cualquier usuario. Admin TIC: solo admin_pvd."""
    es_superusuario = request.user.is_superuser
    es_admin_tic = not es_superusuario and usuario_es_admin_tic(request.user)

    if not (es_superusuario or es_admin_tic):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('modulo_puntos:panel_control')

    usuario_objetivo = get_object_or_404(User, pk=user_id)

    grupos = list(usuario_objetivo.groups.values_list('name', flat=True))
    if 'Administrador TIC' in grupos:
        rol_usuario = 'admin_tic'
    elif 'Administrador PVD' in grupos:
        rol_usuario = 'admin_pvd'
    else:
        rol_usuario = 'admin_pvd'

    if es_admin_tic and rol_usuario == 'admin_tic':
        messages.error(request, 'No tienes permisos para gestionar los permisos de un Administrador TIC.')
        return redirect('modulo_puntos:lista_permisos_roles')

    if es_admin_tic:
        permisos_pvd_ids = PermisoRol.objects.filter(
            rol='admin_pvd'
        ).values_list('permiso_id', flat=True)
        permisos = PermisoDefinicion.objects.filter(
            activo=True, pk__in=permisos_pvd_ids
        ).order_by('categoria', 'nombre')
    else:
        permisos = PermisoDefinicion.objects.filter(activo=True).order_by('categoria', 'nombre')

    permisos_rol = set(
        PermisoRol.objects.filter(rol=rol_usuario).values_list('permiso_id', flat=True)
    )
    overrides_existentes = {
        pu.permiso_id: pu for pu in PermisoUsuario.objects.filter(usuario=usuario_objetivo)
    }

    if request.method == 'POST':
        for permiso in permisos:
            checkbox_name = f'perm_{permiso.pk}'
            marcado = checkbox_name in request.POST
            override_existente = overrides_existentes.get(permiso.pk)
            hereda_del_rol = permiso.pk in permisos_rol

            if marcado == hereda_del_rol and override_existente:
                override_existente.delete()
            elif marcado != hereda_del_rol:
                PermisoUsuario.objects.update_or_create(
                    usuario=usuario_objetivo,
                    permiso=permiso,
                    defaults={'concedido': marcado, 'otorgado_por': request.user},
                )
            elif marcado == hereda_del_rol and not override_existente:
                pass

        registrar_auditoria(
            request, 'UPDATE', 'PermisoUsuario', usuario_objetivo.pk,
            f'Permisos individuales actualizados para usuario: {usuario_objetivo.username}'
        )
        messages.success(request, f'Permisos de {usuario_objetivo.username} actualizados.')
        return redirect('modulo_puntos:permisos_usuario', user_id=user_id)

    categorias = {}
    for permiso in permisos:
        cat = permiso.categoria
        if cat not in categorias:
            categorias[cat] = []
        override = overrides_existentes.get(permiso.pk)
        if override is not None:
            activo = override.concedido
            es_override = True
        else:
            activo = permiso.pk in permisos_rol
            es_override = False
        categorias[cat].append({
            'permiso': permiso,
            'activo': activo,
            'es_override': es_override,
            'hereda_rol': permiso.pk in permisos_rol,
        })

    return render(request, 'modulo_puntos/permisos/usuario_permisos.html', {
        'usuario_objetivo': usuario_objetivo,
        'categorias': categorias,
        'rol_usuario': rol_usuario,
        'es_superusuario': es_superusuario,
    })


