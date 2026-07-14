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


# ── HELPERS ────────────────────────────────────────────────────────────────────

def usuario_es_superusuario(user):
    return user.is_authenticated and user.is_superuser


def usuario_es_admin_tic(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name='Administrador TIC').exists()


def usuario_necesita_seleccionar_pvd(user):
    """Admin PVD debe elegir un PVD antes de operar."""
    if not user.is_authenticated:
        return False
    if user.is_superuser or usuario_es_admin_tic(user):
        return False
    return user.groups.filter(name='Administrador PVD').exists()


def usuario_puede_usar_modulos_pvd(user):
    if not user.is_authenticated:
        return False
    return (
        user.is_superuser
        or usuario_es_admin_tic(user)
        or user.groups.filter(name='Administrador PVD').exists()
    )


def obtener_rol_usuario(user):
    if not user.is_authenticated:
        return 'Sin sesión'
    if user.is_superuser:
        return 'Superusuario'
    grupos = list(user.groups.values_list('name', flat=True))
    return ', '.join(grupos) if grupos else 'Sin rol asignado'


def obtener_pvd_activo_id(request):
    """PVD activo guardado en sesión (int) o None si no hay ninguno."""
    pvd_id = request.session.get('pvd_activo_id')
    try:
        return int(pvd_id) if pvd_id else None
    except (TypeError, ValueError):
        return None


def pvd_permitido(request, punto_vive_digital_id):
    """
    Verifica si el usuario puede ver/editar/eliminar un objeto que pertenece a
    `punto_vive_digital_id` (puede ser None si el objeto no tiene PVD asignado).

    - Superusuario y Administrador TIC: siempre True (ven todos los PVD).
    - Administrador PVD: sólo True si coincide con su PVD activo en sesión.
    """
    if not usuario_necesita_seleccionar_pvd(request.user):
        return True
    pvd_activo_id = obtener_pvd_activo_id(request)
    return pvd_activo_id is not None and punto_vive_digital_id == pvd_activo_id


def exigir_pvd_activo_para_admin_pvd(request):
    """
    Para reportes/exportaciones: si el usuario es Admin PVD y no tiene un PVD
    activo válido en sesión, retorna None (sin permitir "ver todo" por defecto).
    Retorna el pvd_id (int) a filtrar, o False si el usuario no está restringido
    (Superusuario/Admin TIC → sin filtro, ven todos los PVD).
    """
    if not usuario_necesita_seleccionar_pvd(request.user):
        return False
    return obtener_pvd_activo_id(request)


