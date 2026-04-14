"""
Views for Puntos Vive Digital system.
Contract CD-224-2026 - Alcaldía de Bugalagrande

This module contains all view functions organized by functionality:
- Authentication & User Management
- Citizen Management
- Attention & Service Registration
- Resource & Loan Management
- Reports & Exports
- PVD Management
- Help & Support
"""
import csv
import random
from datetime import datetime

# Django imports
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.db.models import Q, Count, Avg
from django.db.models.functions import TruncMonth
from django.shortcuts import render, redirect
from django.urls import reverse

# Local imports
from .models import (
    Ciudadano, Atencion, Satisfaccion, Servicio,
    PrestamoRecurso, Recurso, Operador, PuntoViveDigital, UserProfile, Sala
)
from .forms import (
    CiudadanoForm, AtencionForm, SatisfaccionForm, ServicioForm,
    PrestamoRecursoForm, RecursoForm, LoginForm, PerfilUsuarioForm,
    CrearUsuarioForm, PuntoViveDigitalForm, SalaForm
)
from .utils import (
    registrar_auditoria, mensaje_exito, mensaje_error,
    mensaje_advertencia, mensaje_info, generar_username, generar_password
)

# ==============================================================================
# FUNCIONES AUXILIARES DE PERMISOS Y ROLES
# ==============================================================================

def usuario_es_superusuario(user):
    """Verifica si el usuario es superusuario."""
    return user.is_authenticated and user.is_superuser


def usuario_es_admin_tic(user):
    """Verifica si el usuario es Administrador TIC."""
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name='Administrador TIC').exists()


def usuario_puede_usar_modulos_pvd(user):
    """Verifica si el usuario puede usar los módulos del PVD."""
    if not user.is_authenticated:
        return False
    return (
        user.is_superuser
        or usuario_es_admin_tic(user)
        or user.groups.filter(name='Administrador PVD').exists()
    )


def obtener_rol_usuario(user):
    """Obtiene el rol del usuario como string legible."""
    if not user.is_authenticated:
        return 'Sin sesión'
    if user.is_superuser:
        return 'Superusuario'
    grupos = list(user.groups.values_list('name', flat=True))
    return ', '.join(grupos) if grupos else 'Sin rol asignado'


# ==============================================================================
# AUTENTICACIÓN (LOGIN/LOGOUT)
# ==============================================================================

def logout_usuario(request):
    """Cerrar sesión del usuario y registrar auditoría."""
    usuario = request.user.username if request.user.is_authenticated else 'Anónimo'
    try:
        registrar_auditoria(request, 'LOGOUT', descripcion=f'Cierre de sesión: {usuario}')
    except Exception:
        pass  # No interrumpir el flujo si falla la auditoría
    
    logout(request)
    return redirect('/login/')


def login_usuario(request):
    """
    Vista de login simplificada - solo usuario y contraseña.
    El sistema valida automáticamente el rol del usuario y redirige según corresponda.
    """
    # Si ya está autenticado, redirigir al panel
    if request.user.is_authenticated:
        return redirect('/panel/')

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        from django.contrib.auth import authenticate
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Login exitoso
            login(request, user)
            messages.success(request, f'Bienvenido, {username}.')

            # Redirigir automáticamente según el rol del usuario
            if user.is_superuser:
                return redirect('/panel/')
            elif user.groups.filter(name='Administrador TIC').exists():
                return redirect('/panel/')
            elif user.groups.filter(name='Administrador PVD').exists():
                return redirect('/seleccionar-pvd/')
            else:
                # Usuario sin rol definido - redirigir a registro ciudadano
                messages.info(request, 'Por favor, contacta a un administrador para que te asigne un rol.')
                return redirect('/registrar-usuario-ciudadano/')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'registration/login.html')


# ==============================================================================
# GESTIÓN DE PERFIL DE USUARIO
# ==============================================================================

@login_required(login_url='/login/')
def perfil_usuario(request):
    """Editar perfil del usuario y cambiar contraseña."""
    if request.method == 'POST':
        # Verificar si es cambio de contraseña
        if request.POST.get('cambiar_password'):
            from django.contrib.auth.forms import PasswordChangeForm
            from django.contrib.auth import update_session_auth_hash

            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Tu contraseña fue actualizada correctamente.')
                registrar_auditoria(
                    request, 'UPDATE', 'Usuario', request.user.pk, 
                    'Cambio de contraseña'
                )
            else:
                messages.error(
                    request, 
                    'Error al cambiar la contraseña. Verifica los datos.'
                )
        else:
            # Actualizar perfil
            form = PerfilUsuarioForm(request.POST, instance=request.user)
            if form.is_valid():
                usuario = form.save(commit=False)
                nueva_password = form.cleaned_data.get('password1')
                if nueva_password:
                    usuario.set_password(nueva_password)
                usuario.save()
                
                if nueva_password:
                    update_session_auth_hash(request, usuario)
                
                messages.success(request, 'Tu perfil fue actualizado correctamente.')
                registrar_auditoria(
                    request, 'UPDATE', 'Usuario', request.user.pk, 
                    'Actualización de perfil'
                )
                return redirect('modulo_puntos:perfil_usuario')
            else:
                messages.error(
                    request, 
                    'No se pudo actualizar el perfil. Revisa los datos ingresados.'
                )

    # GET - mostrar formularios
    form = PerfilUsuarioForm(instance=request.user)

    return render(request, 'modulo_puntos/perfil_usuario.html', {
        'form': form,
        'rol_usuario': obtener_rol_usuario(request.user),
    })


# ==============================================================================
# PANEL DE CONTROL Y NAVEGACIÓN
# ==============================================================================

@login_required(login_url='/login/')
def panel_control(request):
    """
    Panel principal del sistema.
    - Superuser: ve funciones de administración del sistema
    - Admin TIC: ve funciones de gestión de PVDs
    - Admin PVD: debe seleccionar un PVD activo antes de acceder
    """
    pvd_activo_id = request.session.get('pvd_activo_id')
    pvd_activo = None

    # Obtener PVD activo de la sesión
    if pvd_activo_id:
        try:
            pvd_activo = PuntoViveDigital.objects.get(pk=pvd_activo_id, pvd_estdo='A')
        except PuntoViveDigital.DoesNotExist:
            request.session.pop('pvd_activo_id', None)

    # Admin PVD DEBE tener un PVD seleccionado
    es_admin_pvd = (
        not usuario_es_admin_tic(request.user) and
        request.user.groups.filter(name='Administrador PVD').exists()
    )

    if es_admin_pvd and not pvd_activo:
        return redirect('modulo_puntos:seleccionar_pvd_view')

    # Calcular contadores filtrados por PVD activo (si hay uno seleccionado)
    if pvd_activo:
        atenciones_pvd = Atencion.objects.filter(pvd_cdgo=pvd_activo)
        atencion_ids = list(atenciones_pvd.values_list('atn_cdgo', flat=True))
        recursos_pvd = Recurso.objects.filter(pvd_cdgo=pvd_activo)
        recurso_ids = list(recursos_pvd.values_list('rec_cdgo', flat=True))

        total_ciudadanos = Ciudadano.objects.filter(pvd_cdgo=pvd_activo).count()
        atenciones_registradas = atenciones_pvd.count()
        total_satisfacciones = (
            Satisfaccion.objects.filter(atn_cdgo__in=atencion_ids).count()
            if atencion_ids else 0
        )
        total_servicios = (
            Servicio.objects.filter(atn_cdgo__in=atencion_ids).count()
            if atencion_ids else 0
        )
        total_prestamos = (
            PrestamoRecurso.objects.filter(rec_cdgo__in=recurso_ids).count()
            if recurso_ids else 0
        )
    else:
        # Superuser/Admin TIC sin PVD seleccionado ven totales globales
        total_ciudadanos = Ciudadano.objects.count()
        atenciones_registradas = Atencion.objects.count()
        total_satisfacciones = Satisfaccion.objects.count()
        total_servicios = Servicio.objects.count()
        total_prestamos = PrestamoRecurso.objects.count()

    # Contar ciudadanos pendientes de aprobación para Admin PVD
    total_pendientes = 0
    if es_admin_pvd:
        total_pendientes = Ciudadano.objects.filter(ciu_pendiente_aprobacion=True).count()
        if pvd_activo:
            total_pendientes = Ciudadano.objects.filter(
                ciu_pendiente_aprobacion=True,
                pvd_cdgo=pvd_activo
            ).count()

    # Determinar roles
    es_superusuario = request.user.is_superuser
    es_admin_tic_only = request.user.groups.filter(name='Administrador TIC').exists() and not request.user.is_superuser
    es_admin_pvd_only = request.user.groups.filter(name='Administrador PVD').exists() and not request.user.is_superuser and not usuario_es_admin_tic(request.user)

    context = {
        'total_ciudadanos': total_ciudadanos,
        'atenciones_registradas': atenciones_registradas,
        'total_satisfacciones': total_satisfacciones,
        'total_servicios': total_servicios,
        'total_prestamos': total_prestamos,
        'total_pendientes': total_pendientes,
        'pvd_activo': pvd_activo,
        'es_superusuario': es_superusuario,
        'es_admin_tic_only': es_admin_tic_only,
        'es_admin_pvd_only': es_admin_pvd_only,
        'rol_usuario': obtener_rol_usuario(request.user),
    }

    return render(request, 'modulo_puntos/panel_control.html', context)


@login_required(login_url='/login/')
def inicio_pvd(request):
    """Pantalla inicial con 2 botones: Seleccionar PVD y Crear PVD."""
    return render(request, 'modulo_puntos/inicio_pvd.html', {
        'rol_usuario': obtener_rol_usuario(request.user),
    })


@login_required(login_url='/login/')
def seleccionar_pvd_view(request):
    """
    Vista para seleccionar un PVD existente.
    - Superuser y Admin TIC: van directo al dashboard (no pasan por aquí)
    - Admin PVD: ve TODOS los PVDs activos para seleccionar dónde trabajar
    """
    # Admin PVD ve todos los PVDs activos para elegir
    pvds = PuntoViveDigital.objects.filter(pvd_estdo='A').order_by('pvd_nombre')

    # Contar registros por PVD
    for pvd in pvds:
        pvd.total_atenciones = Atencion.objects.filter(pvd_cdgo=pvd).count()
        pvd.total_ciudadanos = Ciudadano.objects.filter(pvd_cdgo=pvd).count()
        pvd.total_recursos = Recurso.objects.filter(pvd_cdgo=pvd).count()

    return render(request, 'modulo_puntos/seleccionar_pvd.html', {
        'pvds': pvds,
    })


# ==============================================================================
# GESTIÓN DE CIUDADANOS
# ==============================================================================

@login_required(login_url='/login/')
def consultar_ciudadanos(request):
    """Consultar y buscar ciudadanos registrados."""
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    busqueda = request.GET.get('q', '').strip()
    ciudadanos = Ciudadano.objects.all().order_by('-ciu_cdgo')

    if busqueda:
        ciudadanos = ciudadanos.filter(
            Q(ciu_numdoc__icontains=busqueda) |
            Q(ciu_nmbres__icontains=busqueda) |
            Q(ciu_aplldos__icontains=busqueda)
        )

    context = {
        'ciudadanos': ciudadanos,
        'busqueda': busqueda,
        'total_resultados': ciudadanos.count(),
    }
    return render(request, 'modulo_puntos/consultar_ciudadanos.html', context)


@login_required(login_url='/login/')
def registrar_ciudadano(request):
    """Registrar un nuevo ciudadano."""
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    form = CiudadanoForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                ciudadano = form.save(commit=False)
                # Si el registro viene de un admin (no del formulario público), no queda pendiente
                # Solo queda pendiente si viene del formulario público de usuarios
                ciudadano.ciu_pendiente_aprobacion = False
                ciudadano.save()
                
                messages.success(
                    request,
                    'Ciudadano registrado exitosamente en la base de datos.'
                )
                registrar_auditoria(
                    request, 'CREATE', 'Ciudadano', ciudadano.ciu_cdgo,
                    f'Registrado: {ciudadano.ciu_nmbres} {ciudadano.ciu_aplldos}'
                )
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            messages.error(request, 'Formulario inválido. Revisa los campos.')

    return render(
        request,
        'modulo_puntos/registrar_ciudadano.html',
        {'form': form}
    )


@login_required(login_url='/login/')
def editar_ciudadano(request, ciu_cdgo):
    """Editar información de un ciudadano existente."""
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    try:
        ciudadano = Ciudadano.objects.get(pk=ciu_cdgo)
    except Ciudadano.DoesNotExist:
        messages.error(request, 'El ciudadano no existe.')
        return redirect('modulo_puntos:consultar_ciudadanos')

    form = CiudadanoForm(request.POST or None, instance=ciudadano)
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(
                    request, 
                    'Ciudadano actualizado correctamente en la base de datos.'
                )
                registrar_auditoria(
                    request, 'UPDATE', 'Ciudadano', ciudadano.ciu_cdgo,
                    f'Actualizado: {ciudadano.ciu_nmbres} {ciudadano.ciu_aplldos}'
                )
                return redirect('modulo_puntos:consultar_ciudadanos')
            except Exception as e:
                messages.error(request, f'Error al actualizar en BD: {e}')
        else:
            messages.error(
                request, 
                'No se pudo actualizar el ciudadano. Revisa los datos ingresados.'
            )

    return render(request, 'modulo_puntos/editar_ciudadano.html', {
        'form': form,
        'ciudadano': ciudadano,
    })


@login_required(login_url='/login/')
def historial_ciudadano(request, ciu_cdgo):
    """Ver historial de atenciones de un ciudadano."""
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    try:
        ciudadano = Ciudadano.objects.get(pk=ciu_cdgo)
    except Ciudadano.DoesNotExist:
        messages.error(request, 'El ciudadano no existe.')
        return redirect('modulo_puntos:consultar_ciudadanos')

    # Obtener atenciones relacionadas
    atenciones = Atencion.objects.filter(
        ciu_cdgo=ciudadano
    ).select_related(
        'opr_cdgo',
        'prs_cdgo',
        'prs_cdgo__rec_cdgo'
    ).order_by('-atn_fecha', '-atn_hrini')

    # Agregar servicios y satisfacciones a cada atención
    for atencion in atenciones:
        atencion.servicios_rel = Servicio.objects.filter(atn_cdgo=atencion)
        atencion.satisfacciones_rel = Satisfaccion.objects.filter(atn_cdgo=atencion)

    return render(request, 'modulo_puntos/historial_ciudadano.html', {
        'ciudadano': ciudadano,
        'atenciones': atenciones,
        'total_atenciones': atenciones.count(),
    })


# ==============================================================================
# REGISTRO DE ATENCIONES Y SERVICIOS
# ==============================================================================

@login_required(login_url='/login/')
def registrar_atencion(request):
    """Registrar una nueva atención a ciudadano."""
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    # LÓGICA DE AUTO-ASIGNACIÓN:
    operador_actual = None
    if request.user.first_name:
        operador_actual = Operador.objects.filter(
            opr_nmbres__icontains=request.user.first_name
        ).first()

    datos_iniciales = {}
    if operador_actual:
        datos_iniciales['opr_cdgo'] = operador_actual.opr_cdgo

    form = AtencionForm(request.POST or None, initial=datos_iniciales)

    if request.method == 'POST':
        if form.is_valid():
            try:
                atencion = form.save()
                messages.success(
                    request, 
                    'Atención registrada correctamente en la base de datos.'
                )
                registrar_auditoria(
                    request, 'CREATE', 'Atencion', atencion.atn_cdgo,
                    f'Atención #{atencion.atn_cdgo} registrada'
                )
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            messages.error(
                request, 
                'No se pudo guardar la atención. Revisa los datos ingresados.'
            )

    return render(
        request, 
        'modulo_puntos/registrar_atencion.html', 
        {'form': form}
    )


@login_required(login_url='/login/')
def registrar_servicio(request):
    """Registrar un servicio prestado durante una atención."""
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    form = ServicioForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                servicio = form.save()
                messages.success(
                    request, 
                    'Servicio registrado correctamente en la base de datos.'
                )
                nombre_servicio = (
                    servicio.srv_nombre 
                    if hasattr(servicio, 'srv_nombre') 
                    else f'Servicio #{servicio.srv_cdgo}'
                )
                registrar_auditoria(
                    request, 'CREATE', 'Servicio', servicio.srv_cdgo,
                    f'Servicio: {nombre_servicio}'
                )
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            messages.error(
                request, 
                'No se pudo guardar el servicio. Revisa los datos ingresados.'
            )

    return render(
        request, 
        'modulo_puntos/registrar_servicio.html', 
        {'form': form}
    )


@login_required(login_url='/login/')
def registrar_satisfaccion(request):
    """Registrar encuesta de satisfacción."""
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    form = SatisfaccionForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                satisfaccion = form.save()
                messages.success(
                    request, 
                    'Satisfacción registrada correctamente en la base de datos.'
                )
                registrar_auditoria(
                    request, 'CREATE', 'Satisfaccion', satisfaccion.sat_cdgo,
                    f'Satisfacción: {satisfaccion.sat_calif}/5'
                )
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            messages.error(
                request, 
                'No se pudo guardar la satisfacción. Revisa los datos ingresados.'
            )

    return render(
        request, 
        'modulo_puntos/registrar_satisfaccion.html', 
        {'form': form}
    )


# ==============================================================================
# GESTIÓN DE RECURSOS Y PRÉSTAMOS
# ==============================================================================

@login_required(login_url='/login/')
def registrar_prestamo(request):
    """Registrar préstamo de recurso a ciudadano."""
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    form = PrestamoRecursoForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                prestamo = form.save()
                messages.success(
                    request, 
                    'Préstamo registrado correctamente en la base de datos.'
                )
                registrar_auditoria(
                    request, 'CREATE', 'PrestamoRecurso', prestamo.prs_cdgo,
                    f'Préstamo #{prestamo.prs_cdgo} registrado'
                )
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            messages.error(
                request, 
                'No se pudo guardar el préstamo. Revisa los datos ingresados.'
            )

    return render(
        request, 
        'modulo_puntos/registrar_prestamo.html', 
        {'form': form}
    )


@login_required(login_url='/login/')
def registrar_recurso(request):
    """Registrar un nuevo recurso/equipo del PVD."""
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    form = RecursoForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                recurso = form.save()
                messages.success(
                    request, 
                    'Recurso registrado correctamente en la base de datos.'
                )
                registrar_auditoria(
                    request, 'CREATE', 'Recurso', recurso.rec_cdgo,
                    f'Recurso #{recurso.rec_cdgo} registrado'
                )
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            messages.error(
                request, 
                'No se pudo guardar el recurso. Revisa los datos ingresados.'
            )

    return render(
        request, 
        'modulo_puntos/registrar_recurso.html', 
        {'form': form}
    )


# ==============================================================================
# REPORTES Y EXPORTACIÓN CSV
# ==============================================================================

@login_required(login_url='/login/')
def reportes(request):
    """Generar reportes y estadísticas del sistema."""
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    # Estadísticas generales
    total_ciudadanos = Ciudadano.objects.count()
    ciudadanos_activos = Ciudadano.objects.filter(ciu_estdo='A').count()
    total_operadores = Operador.objects.count()
    operadores_activos = Operador.objects.filter(opr_estdo='A').count()
    total_atenciones = Atencion.objects.count()
    atenciones_pendientes = Atencion.objects.filter(atn_estdo='P').count()
    atenciones_finalizadas = Atencion.objects.filter(atn_estdo='F').count()
    atenciones_canceladas = Atencion.objects.filter(atn_estdo='C').count()
    total_servicios = Servicio.objects.count()
    total_prestamos = PrestamoRecurso.objects.count()
    prestamos_activos = PrestamoRecurso.objects.filter(
        prs_fchdev__isnull=True
    ).count()

    # Satisfacción promedio
    satisfaccion_promedio = Satisfaccion.objects.aggregate(
        promedio=Avg('sat_calif')
    )['promedio']

    # Servicios por tipo
    servicios_por_tipo = Servicio.objects.values('srv_tipo').annotate(
        total=Count('srv_cdgo')
    ).order_by('-total', 'srv_tipo')

    # Atenciones por operador
    atenciones_por_operador = Atencion.objects.values(
        'opr_cdgo__opr_nmbres',
        'opr_cdgo__opr_aplldos'
    ).annotate(
        total=Count('atn_cdgo')
    ).order_by('-total')

    # Atenciones recientes
    atenciones_recientes = Atencion.objects.select_related(
        'ciu_cdgo',
        'opr_cdgo'
    ).order_by('-atn_fecha', '-atn_hrini')[:10]

    # Ciudadanos por género
    gen_map = dict(Ciudadano.GENERO_CHOICES)
    ciudadanos_por_genero = []
    for row in Ciudadano.objects.values('ciu_genro').annotate(
        total=Count('ciu_cdgo')
    ).order_by('-total'):
        clave = row['ciu_genro'] or ''
        ciudadanos_por_genero.append({
            'etiqueta': gen_map.get(clave, clave or 'Sin dato'),
            'total': row['total'],
        })

    # Estadísticas demográficas
    ciudadanos_por_etnia = list(
        Ciudadano.objects.exclude(ciu_etnia__isnull=True).exclude(ciu_etnia='')
        .values('ciu_etnia').annotate(total=Count('ciu_cdgo'))
        .order_by('-total')[:20]
    )

    ciudadanos_por_nvleduc = list(
        Ciudadano.objects.exclude(ciu_nvleduc__isnull=True)
        .exclude(ciu_nvleduc='').values('ciu_nvleduc')
        .annotate(total=Count('ciu_cdgo')).order_by('-total')[:20]
    )

    ciudadanos_por_estrato = list(
        Ciudadano.objects.values('ciu_estrato')
        .annotate(total=Count('ciu_cdgo')).order_by('ciu_estrato')
    )

    ciudadanos_por_ocupacion = list(
        Ciudadano.objects.exclude(ciu_ocpcion__isnull=True)
        .exclude(ciu_ocpcion='').values('ciu_ocpcion')
        .annotate(total=Count('ciu_cdgo')).order_by('-total')[:15]
    )

    # Discapacidad
    ciudadanos_con_discapacidad = Ciudadano.objects.filter(
        ciu_discapacidad=True
    ).count()
    ciudadanos_sin_discapacidad = Ciudadano.objects.filter(
        ciu_discapacidad=False
    ).count()

    # Atenciones por mes
    atenciones_por_mes = list(
        Atencion.objects.annotate(mes=TruncMonth('atn_fecha'))
        .values('mes')
        .annotate(total=Count('atn_cdgo'))
        .order_by('-mes')[:12]
    )

    return render(request, 'modulo_puntos/reportes.html', {
        'total_ciudadanos': total_ciudadanos,
        'ciudadanos_activos': ciudadanos_activos,
        'total_operadores': total_operadores,
        'operadores_activos': operadores_activos,
        'total_atenciones': total_atenciones,
        'atenciones_pendientes': atenciones_pendientes,
        'atenciones_finalizadas': atenciones_finalizadas,
        'atenciones_canceladas': atenciones_canceladas,
        'total_servicios': total_servicios,
        'total_prestamos': total_prestamos,
        'prestamos_activos': prestamos_activos,
        'satisfaccion_promedio': satisfaccion_promedio,
        'servicios_por_tipo': servicios_por_tipo,
        'atenciones_por_operador': atenciones_por_operador,
        'atenciones_recientes': atenciones_recientes,
        'ciudadanos_por_genero': ciudadanos_por_genero,
        'ciudadanos_por_etnia': ciudadanos_por_etnia,
        'ciudadanos_por_nvleduc': ciudadanos_por_nvleduc,
        'ciudadanos_por_estrato': ciudadanos_por_estrato,
        'ciudadanos_por_ocupacion': ciudadanos_por_ocupacion,
        'ciudadanos_con_discapacidad': ciudadanos_con_discapacidad,
        'ciudadanos_sin_discapacidad': ciudadanos_sin_discapacidad,
        'atenciones_por_mes': atenciones_por_mes,
    })


def _csv_response(filename_base):
    """Crear respuesta HTTP para descarga de CSV."""
    response = HttpResponse(content_type='text/csv')
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    response['Content-Disposition'] = (
        f'attachment; filename="{filename_base}_{fecha_actual}.csv"'
    )
    response.write('\ufeff'.encode('utf8'))  # BOM para UTF-8 en Excel
    return response


@login_required(login_url='/login/')
def exportar_atenciones_csv(request):
    """Exportar atenciones a CSV."""
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    registrar_auditoria(
        request, 'EXPORT', 'Atencion', 
        descripcion='Exportación CSV de atenciones'
    )

    response = HttpResponse(content_type='text/csv')
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    response['Content-Disposition'] = (
        f'attachment; filename="Reporte_Atenciones_PVD_{fecha_actual}.csv"'
    )
    response.write('\ufeff'.encode('utf8'))
    writer = csv.writer(response)

    # Encabezados
    writer.writerow([
        'ID Atención', 'Fecha', 'Hora Inicio', 'Hora Fin', 'Estado Atención',
        'Documento Ciudadano', 'Nombre Completo', 'Género', 'Etnia',
        'Discapacidad', 'Detalle Discapacidad', 'Barrio', 'Dirección', 
        'Vereda / Corregimiento',
        'Operador a Cargo', 'Observaciones'
    ])

    # Datos
    atenciones = Atencion.objects.select_related(
        'ciu_cdgo', 'opr_cdgo'
    ).order_by('-atn_fecha')

    for atencion in atenciones:
        if atencion.ciu_cdgo:
            doc_ciu = atencion.ciu_cdgo.ciu_numdoc
            nom_ciu = f"{atencion.ciu_cdgo.ciu_nmbres} {atencion.ciu_cdgo.ciu_aplldos}"
            gen_ciu = atencion.ciu_cdgo.get_ciu_genro_display()
            etnia_ciu = atencion.ciu_cdgo.ciu_etnia
            discap_ciu = "Sí" if atencion.ciu_cdgo.ciu_discapacidad else "No"
            desc_discap_ciu = (
                atencion.ciu_cdgo.ciu_desc_discapacidad 
                if atencion.ciu_cdgo.ciu_desc_discapacidad 
                else "N/A"
            )
            barrio_ciu = (
                atencion.ciu_cdgo.ciu_barrio 
                if atencion.ciu_cdgo.ciu_barrio 
                else "N/A"
            )
            dir_ciu = (
                atencion.ciu_cdgo.ciu_dircion 
                if atencion.ciu_cdgo.ciu_dircion 
                else "N/A"
            )
            rural_ciu = (
                atencion.ciu_cdgo.ciu_zrural 
                if atencion.ciu_cdgo.ciu_zrural 
                else "N/A"
            )
        else:
            doc_ciu = nom_ciu = gen_ciu = etnia_ciu = discap_ciu = ""
            desc_discap_ciu = barrio_ciu = dir_ciu = rural_ciu = "N/A"

        operador_info = (
            f"{atencion.opr_cdgo.opr_nmbres} {atencion.opr_cdgo.opr_aplldos}" 
            if atencion.opr_cdgo else "N/A"
        )
        estado_dict = dict(Atencion.ESTADO_CHOICES)
        estado_display = estado_dict.get(atencion.atn_estdo, atencion.atn_estdo)

        writer.writerow([
            atencion.atn_cdgo, atencion.atn_fecha, atencion.atn_hrini,
            atencion.atn_hrfin if atencion.atn_hrfin else "N/A", 
            estado_display,
            doc_ciu, nom_ciu, gen_ciu, etnia_ciu, discap_ciu, desc_discap_ciu,
            barrio_ciu, dir_ciu, rural_ciu, operador_info,
            atencion.atn_obs if atencion.atn_obs else "Sin observaciones"
        ])

    return response


@login_required(login_url='/login/')
def exportar_ciudadanos_csv(request):
    """Exportar ciudadanos a CSV."""
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    registrar_auditoria(
        request, 'EXPORT', 'Ciudadano', 
        descripcion='Exportación CSV de ciudadanos'
    )

    response = _csv_response('Reporte_Ciudadanos_PVD')
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Tipo doc.', 'Número doc.', 'Nombres', 'Apellidos', 
        'Fecha nacimiento', 'Género', 'Etnia',
        'Nivel educativo', 'Ocupación', 'Discapacidad', 
        'Descripción discapacidad', 'Dirección', 'Barrio',
        'Zona rural', 'Estrato', 'Estado', 'Email', 'Teléfono'
    ])
    
    for c in Ciudadano.objects.all().order_by('-ciu_cdgo'):
        writer.writerow([
            c.ciu_cdgo, c.ciu_tpodoc, c.ciu_numdoc, c.ciu_nmbres, 
            c.ciu_aplldos, c.ciu_fchancm,
            c.get_ciu_genro_display(), c.ciu_etnia, c.ciu_nvleduc, 
            c.ciu_ocpcion,
            'Sí' if c.ciu_discapacidad else 'No',
            c.ciu_desc_discapacidad or '',
            c.ciu_dircion or '', c.ciu_barrio or '', c.ciu_zrural or '',
            c.ciu_estrato, c.get_ciu_estdo_display(), c.ciu_email, c.ciu_tlfno
        ])
    return response


@login_required(login_url='/login/')
def exportar_servicios_csv(request):
    """Exportar servicios a CSV."""
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    registrar_auditoria(
        request, 'EXPORT', 'Servicio', 
        descripcion='Exportación CSV de servicios'
    )

    response = _csv_response('Reporte_Servicios_PVD')
    writer = csv.writer(response)
    writer.writerow([
        'ID servicio', 'ID atención', 'Fecha atención', 'Documento ciudadano', 
        'Nombre ciudadano',
        'Nombre servicio', 'Descripción', 'Tipo servicio', 
        'Requiere equipo', 'Estado servicio'
    ])
    
    qs = Servicio.objects.select_related(
        'atn_cdgo', 'atn_cdgo__ciu_cdgo'
    ).order_by('-srv_cdgo')
    
    for s in qs:
        atn = s.atn_cdgo
        fecha_atn = atn.atn_fecha if atn else ''
        doc = nom = ''
        if atn and atn.ciu_cdgo:
            doc = atn.ciu_cdgo.ciu_numdoc
            nom = f"{atn.ciu_cdgo.ciu_nmbres} {atn.ciu_cdgo.ciu_aplldos}"
        writer.writerow([
            s.srv_cdgo, atn.atn_cdgo if atn else '', fecha_atn, doc, nom,
            s.srv_nombre, s.srv_descr or '', s.srv_tipo, 
            s.get_srv_reqeqp_display(),
            s.get_srv_estdo_display()
        ])
    return response


@login_required(login_url='/login/')
def exportar_satisfaccion_csv(request):
    """Exportar encuestas de satisfacción a CSV."""
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    registrar_auditoria(
        request, 'EXPORT', 'Satisfaccion', 
        descripcion='Exportación CSV de satisfacción'
    )

    response = _csv_response('Reporte_Satisfaccion_PVD')
    writer = csv.writer(response)
    writer.writerow([
        'ID satisfacción', 'ID atención', 'Fecha atención', 'Estado atención', 
        'Documento ciudadano',
        'Nombre ciudadano', 'Calificación', 'Comentario', 
        'Fecha registro satisfacción'
    ])
    
    qs = Satisfaccion.objects.select_related(
        'atn_cdgo', 'atn_cdgo__ciu_cdgo'
    ).order_by('-sat_cdgo')
    estado_atn = dict(Atencion.ESTADO_CHOICES)
    
    for sat in qs:
        atn = sat.atn_cdgo
        doc = nom = fecha_atn = est_atn = ''
        if atn:
            fecha_atn = str(atn.atn_fecha)
            est_atn = estado_atn.get(atn.atn_estdo, atn.atn_estdo)
            if atn.ciu_cdgo:
                doc = atn.ciu_cdgo.ciu_numdoc
                nom = f"{atn.ciu_cdgo.ciu_nmbres} {atn.ciu_cdgo.ciu_aplldos}"
        writer.writerow([
            sat.sat_cdgo, atn.atn_cdgo if atn else '', fecha_atn, est_atn, 
            doc, nom,
            sat.sat_calif, sat.sat_cmntrio or '', sat.sat_fecha
        ])
    return response


@login_required(login_url='/login/')
def exportar_prestamos_csv(request):
    """Exportar préstamos a CSV."""
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    registrar_auditoria(
        request, 'EXPORT', 'PrestamoRecurso', 
        descripcion='Exportación CSV de préstamos'
    )

    response = _csv_response('Reporte_Prestamos_PVD')
    writer = csv.writer(response)
    writer.writerow([
        'ID préstamo', 'Tipo recurso', 'Fecha entrega', 'Fecha devolución', 
        'Observaciones', 'Estado'
    ])
    
    for p in PrestamoRecurso.objects.select_related('rec_cdgo').order_by(
        '-prs_cdgo'
    ):
        tipo = p.rec_cdgo.rec_tipo if p.rec_cdgo else ''
        dev = p.prs_fchdev if p.prs_fchdev else ''
        estado = 'Activo (sin devolución)' if not p.prs_fchdev else 'Devuelto'
        writer.writerow([
            p.prs_cdgo, tipo, p.prs_fchent, dev, p.prs_obs or '', estado
        ])
    return response


# ==============================================================================
# GESTIÓN DE USUARIOS (CREAR ADMIN TIC Y PVD)
# ==============================================================================

@login_required(login_url='/login/')
def ayuda_sistema(request):
    """Vista de ayuda del sistema."""
    return render(request, 'modulo_puntos/ayuda.html', {
        'rol_usuario': obtener_rol_usuario(request.user),
    })


@login_required(login_url='/login/')
def crear_admin_tic(request):
    """Crear usuario Administrador TIC (solo Superuser)."""
    if not usuario_es_superusuario(request.user):
        messages.error(request, 'No tienes permisos para crear Administradores TIC.')
        return redirect('modulo_puntos:panel_control')

    form = CrearUsuarioForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            grupo, _ = Group.objects.get_or_create(name='Administrador TIC')
            user.groups.add(grupo)
            messages.success(
                request, 
                f'Administrador TIC ({user.username}) creado correctamente.'
            )
            return redirect('modulo_puntos:panel_control')
        else:
            messages.error(
                request, 
                'No se pudo crear el usuario. Revisa los datos ingresados.'
            )

    return render(request, 'modulo_puntos/crear_usuario.html', {
        'form': form,
        'titulo': 'Crear Administrador TIC',
        'rol': 'Administrador TIC'
    })


@login_required(login_url='/login/')
def crear_admin_pvd(request):
    """Crear usuario Administrador PVD con PVD asignado."""
    if not (usuario_es_superusuario(request.user) or usuario_es_admin_tic(request.user)):
        messages.error(request, 'No tienes permisos para crear Administradores PVD.')
        return redirect('modulo_puntos:panel_control')

    form = CrearUsuarioForm(request.POST or None)
    pvds = PuntoViveDigital.objects.filter(pvd_estdo='A').order_by('pvd_nombre')
    pvd_seleccionado = None

    if request.method == 'POST':
        pvd_seleccionado = request.POST.get('pvd_asignado')
        if form.is_valid():
            user = form.save()
            grupo, _ = Group.objects.get_or_create(name='Administrador PVD')
            user.groups.add(grupo)

            # Crear el UserProfile con el PVD asignado
            if pvd_seleccionado:
                try:
                    pvd = PuntoViveDigital.objects.get(pk=pvd_seleccionado)
                    UserProfile.objects.create(user=user, pvd_asignado=pvd)
                except PuntoViveDigital.DoesNotExist:
                    messages.warning(
                        request, 
                        'El PVD seleccionado no existe. El usuario no tendrá PVD asignado.'
                    )

            # LÓGICA DE CREACIÓN AUTOMÁTICA DEL OPERADOR
            num_doc_temp = str(random.randint(10000000, 99999999))
            pvd_obj = (
                PuntoViveDigital.objects.filter(pk=pvd_seleccionado).first() 
                if pvd_seleccionado else None
            )
            Operador.objects.create(
                pvd_cdgo=pvd_obj,
                opr_tpodoc='CC',
                opr_numdoc=num_doc_temp,
                opr_nmbres=user.first_name,
                opr_aplldos=user.last_name,
                opr_email=user.email,
                opr_tlfno='0000000000',
                opr_estdo='A'
            )

            messages.success(
                request, 
                f'Administrador PVD ({user.username}) creado correctamente con PVD asignado.'
            )
            return redirect('modulo_puntos:panel_control')
        else:
            messages.error(
                request, 
                'No se pudo crear el usuario. Revisa los errores.'
            )

    return render(request, 'modulo_puntos/crear_usuario.html', {
        'form': form,
        'titulo': 'Crear Administrador PVD',
        'rol': 'Administrador PVD',
        'pvds': pvds,
    })


# ==============================================================================
# GESTIÓN DE PUNTOS VIVE DIGITAL (Multi-PVD)
# ==============================================================================

@login_required(login_url='/login/')
def lista_pvd(request):
    """Lista todos los Puntos Vive Digital registrados."""
    if not usuario_es_superusuario(request.user) and not usuario_es_admin_tic(request.user):
        messages.error(request, 'No tienes permisos para administrar los PVD.')
        return redirect('modulo_puntos:panel_control')

    pvds = PuntoViveDigital.objects.all().order_by('pvd_nombre')

    # Contar registros por PVD
    for pvd in pvds:
        pvd.total_atenciones = Atencion.objects.filter(pvd_cdgo=pvd).count()
        pvd.total_ciudadanos = Ciudadano.objects.filter(pvd_cdgo=pvd).count()
        pvd.total_recursos = Recurso.objects.filter(pvd_cdgo=pvd).count()
        pvd.total_operadores = Operador.objects.filter(pvd_cdgo=pvd).count()

    return render(request, 'modulo_puntos/lista_pvd.html', {
        'pvds': pvds,
    })


@login_required(login_url='/login/')
def crear_pvd(request):
    """Crea un nuevo Punto Vive Digital. SOLO Superuser.
    La asignación de Admin PVD es opcional y se puede hacer después.
    """
    if not usuario_es_superusuario(request.user):
        messages.error(request, 'Solo el Superusuario puede crear Puntos Vive Digital.')
        return redirect('modulo_puntos:panel_control')

    form = PuntoViveDigitalForm(request.POST or None)
    
    # Obtener lista de administradores PVD disponibles para asignación opcional
    admins_pvd_disponibles = User.objects.filter(
        groups__name='Administrador PVD'
    ).select_related('pvd_profile').order_by('username')
    
    if request.method == 'POST':
        if form.is_valid():
            pvd = form.save()
            messages.success(
                request,
                f'Punto Vive Digital "{pvd.pvd_nombre}" creado exitosamente.'
            )
            registrar_auditoria(
                request, 'CREATE', 'PuntoViveDigital', pvd.pvd_cdgo,
                f'Nuevo PVD creado: {pvd.pvd_nombre}'
            )
            
            # Verificar si se quiere asignar un admin PVD ahora
            admin_pvd_id = request.POST.get('admin_pvd_asignado', '')
            if admin_pvd_id:
                try:
                    admin_user = User.objects.get(pk=admin_pvd_id)
                    # Verificar que el usuario no tenga ya un PVD asignado
                    if not hasattr(admin_user, 'pvd_profile') or not admin_user.pvd_profile.pvd_asignado:
                        profile, created = UserProfile.objects.get_or_create(user=admin_user)
                        profile.pvd_asignado = pvd
                        profile.save()
                        messages.success(
                            request,
                            f'Administrador {admin_user.username} asignado al PVD correctamente.'
                        )
                        registrar_auditoria(
                            request, 'UPDATE', 'UserProfile', profile.pk,
                            f'Admin {admin_user.username} asignado a PVD: {pvd.pvd_nombre}'
                        )
                    else:
                        messages.warning(
                            request,
                            f'El administrador {admin_user.username} ya tiene un PVD asignado.'
                        )
                except User.DoesNotExist:
                    pass
            
            return redirect('modulo_puntos:lista_pvd')
        else:
            messages.error(request, 'Error al crear el PVD. Revisa los datos.')

    return render(request, 'modulo_puntos/form_pvd.html', {
        'form': form,
        'titulo': 'Crear Nuevo Punto Vive Digital',
        'accion': 'crear',
        'admins_pvd': admins_pvd_disponibles
    })


@login_required(login_url='/login/')
def editar_pvd(request, pvd_cdgo):
    """Edita un Punto Vive Digital existente."""
    if not usuario_es_superusuario(request.user) and not usuario_es_admin_tic(request.user):
        messages.error(request, 'No tienes permisos para editar PVD.')
        return redirect('modulo_puntos:panel_control')

    try:
        pvd = PuntoViveDigital.objects.get(pk=pvd_cdgo)
    except PuntoViveDigital.DoesNotExist:
        messages.error(request, 'El Punto Vive Digital no existe.')
        return redirect('modulo_puntos:lista_pvd')

    form = PuntoViveDigitalForm(request.POST or None, instance=pvd)
    if request.method == 'POST':
        if form.is_valid():
            pvd = form.save()
            messages.success(
                request, 
                f'Punto Vive Digital "{pvd.pvd_nombre}" actualizado correctamente.'
            )
            registrar_auditoria(
                request, 'UPDATE', 'PuntoViveDigital', pvd.pvd_cdgo,
                f'PVD actualizado: {pvd.pvd_nombre}'
            )
            return redirect('modulo_puntos:lista_pvd')
        else:
            messages.error(request, 'Error al actualizar el PVD. Revisa los datos.')

    return render(request, 'modulo_puntos/form_pvd.html', {
        'form': form,
        'titulo': f'Editar PVD: {pvd.pvd_nombre}',
        'accion': 'editar'
    })


@login_required(login_url='/login/')
def activar_pvd(request, pvd_cdgo):
    """Activa o desactiva un PVD (toggle)."""
    if not usuario_es_superusuario(request.user) and not usuario_es_admin_tic(request.user):
        messages.error(request, 'No tienes permisos para cambiar el estado del PVD.')
        return redirect('modulo_puntos:panel_control')

    try:
        pvd = PuntoViveDigital.objects.get(pk=pvd_cdgo)
        pvd.pvd_estdo = 'A' if pvd.pvd_estdo != 'A' else 'I'
        pvd.save()
        estado = 'activado' if pvd.pvd_estdo == 'A' else 'desactivado'
        messages.success(
            request, 
            f'PVD "{pvd.pvd_nombre}" {estado} correctamente.'
        )
        registrar_auditoria(
            request, 'UPDATE', 'PuntoViveDigital', pvd.pvd_cdgo,
            f'PVD {estado}: {pvd.pvd_nombre}'
        )
    except PuntoViveDigital.DoesNotExist:
        messages.error(request, 'El PVD no existe.')

    return redirect('modulo_puntos:lista_pvd')


@login_required(login_url='/login/')
def seleccionar_pvd(request, pvd_cdgo):
    """Selecciona el PVD activo para la sesión del usuario."""
    try:
        pvd = PuntoViveDigital.objects.get(pk=pvd_cdgo, pvd_estdo='A')
        request.session['pvd_activo_id'] = pvd_cdgo
        messages.success(request, f'Ahora trabajas desde: {pvd.pvd_nombre}')
        registrar_auditoria(
            request, 'OTHER', 'PuntoViveDigital', pvd_cdgo,
            f'PVD seleccionado: {pvd.pvd_nombre}'
        )
    except PuntoViveDigital.DoesNotExist:
        messages.error(request, 'El PVD no existe o está inactivo.')

    return redirect('modulo_puntos:panel_control')


# ==============================================================================
# GESTIÓN DE SALAS
# ==============================================================================

@login_required(login_url='/login/')
def lista_salas(request):
    """
    Lista todas las salas filtradas por el PVD activo de la sesión.
    Solo Superusuario y Admin TIC pueden ver todas las salas.
    Admin PVD ve las salas de su PVD asignado.
    """
    es_admin_tic = usuario_es_superusuario(request.user) or usuario_es_admin_tic(request.user)
    
    # Determinar qué PVD usar
    pvd_activo_id = request.session.get('pvd_activo_id')
    
    if es_admin_tic:
        # Superusuario y Admin TIC pueden ver todas las salas o filtrar por PVD
        pvd_id = request.GET.get('pvd_id', pvd_activo_id)
        if pvd_id:
            salas = Sala.objects.filter(pvd_cdgo_id=pvd_id).select_related('pvd_cdgo')
            pvd_seleccionado = PuntoViveDigital.objects.get(pk=pvd_id) if pvd_id else None
        else:
            salas = Sala.objects.all().select_related('pvd_cdgo')
            pvd_seleccionado = None
    else:
        # Admin PVD solo ve las salas de su PVD asignado
        try:
            perfil = request.user.pvd_profile
            pvd_id = perfil.pvd_asignado_id if perfil.pvd_asignado else pvd_activo_id
            if pvd_id:
                salas = Sala.objects.filter(pvd_cdgo_id=pvd_id).select_related('pvd_cdgo')
                pvd_seleccionado = PuntoViveDigital.objects.get(pk=pvd_id) if pvd_id else None
            else:
                salas = Sala.objects.none()
                pvd_seleccionado = None
        except Exception:
            salas = Sala.objects.none()
            pvd_seleccionado = None
    
    # Obtener lista de PVDs para el filtro (solo para Admin TIC y Superusuario)
    pvds = PuntoViveDigital.objects.filter(pvd_estdo='A').order_by('pvd_nombre') if es_admin_tic else []
    
    context = {
        'salas': salas,
        'pvds': pvds,
        'pvd_seleccionado': pvd_seleccionado,
        'es_admin_tic': es_admin_tic,
    }
    
    return render(request, 'modulo_puntos/lista_salas.html', context)


@login_required(login_url='/login/')
def crear_sala(request):
    """
    Crea una nueva sala para un PVD.
    Solo Superusuario y Admin TIC pueden crear salas.
    """
    if not usuario_es_superusuario(request.user) and not usuario_es_admin_tic(request.user):
        messages.error(request, 'No tienes permisos para crear salas.')
        return redirect('modulo_puntos:lista_salas')
    
    # Determinar PVD por defecto
    pvd_activo_id = request.session.get('pvd_activo_id')
    
    if request.method == 'POST':
        form = SalaForm(request.POST)
        if form.is_valid():
            sala = form.save(commit=False)
            # Si no se seleccionó PVD, usar el activo
            if not sala.pvd_cdgo_id and pvd_activo_id:
                sala.pvd_cdgo_id = pvd_activo_id
            sala.save()
            
            messages.success(
                request,
                f'Sala "{sala.sala_nombre}" creada exitosamente en {sala.pvd_cdgo.pvd_nombre}.'
            )
            registrar_auditoria(
                request, 'CREATE', 'Sala', sala.sala_cdgo,
                f'Nueva sala creada: {sala.sala_nombre} en {sala.pvd_cdgo.pvd_nombre}'
            )
            return redirect('modulo_puntos:lista_salas')
        else:
            messages.error(request, 'Error al crear la sala. Revisa los datos.')
    else:
        initial = {}
        if pvd_activo_id:
            initial['pvd_cdgo'] = pvd_activo_id
        form = SalaForm(initial=initial)
    
    return render(request, 'modulo_puntos/form_sala.html', {
        'form': form,
        'titulo': 'Crear Nueva Sala',
        'accion': 'crear'
    })


@login_required(login_url='/login/')
def editar_sala(request, sala_cdgo):
    """
    Edita una sala existente.
    Solo Superusuario y Admin TIC pueden editar salas.
    """
    if not usuario_es_superusuario(request.user) and not usuario_es_admin_tic(request.user):
        messages.error(request, 'No tienes permisos para editar salas.')
        return redirect('modulo_puntos:lista_salas')
    
    try:
        sala = Sala.objects.select_related('pvd_cdgo').get(pk=sala_cdgo)
    except Sala.DoesNotExist:
        messages.error(request, 'La sala no existe.')
        return redirect('modulo_puntos:lista_salas')
    
    if request.method == 'POST':
        form = SalaForm(request.POST, instance=sala)
        if form.is_valid():
            sala = form.save()
            messages.success(
                request,
                f'Sala "{sala.sala_nombre}" actualizada correctamente.'
            )
            registrar_auditoria(
                request, 'UPDATE', 'Sala', sala.sala_cdgo,
                f'Sala actualizada: {sala.sala_nombre} en {sala.pvd_cdgo.pvd_nombre}'
            )
            return redirect('modulo_puntos:lista_salas')
        else:
            messages.error(request, 'Error al actualizar la sala. Revisa los datos.')
    else:
        form = SalaForm(instance=sala)
    
    return render(request, 'modulo_puntos/form_sala.html', {
        'form': form,
        'titulo': f'Editar Sala: {sala.sala_nombre}',
        'accion': 'editar'
    })


@login_required(login_url='/login/')
def activar_sala(request, sala_cdgo):
    """
    Activa o desactiva una sala (toggle).
    Solo Superusuario y Admin TIC pueden cambiar el estado.
    """
    if not usuario_es_superusuario(request.user) and not usuario_es_admin_tic(request.user):
        messages.error(request, 'No tienes permisos para cambiar el estado de la sala.')
        return redirect('modulo_puntos:lista_salas')
    
    try:
        sala = Sala.objects.select_related('pvd_cdgo').get(pk=sala_cdgo)
        sala.sala_estdo = 'A' if sala.sala_estdo != 'A' else 'I'
        sala.save()
        estado = 'activada' if sala.sala_estdo == 'A' else 'desactivada'
        messages.success(
            request,
            f'Sala "{sala.sala_nombre}" {estado} correctamente.'
        )
        registrar_auditoria(
            request, 'UPDATE', 'Sala', sala.sala_cdgo,
            f'Sala {estado}: {sala.sala_nombre} en {sala.pvd_cdgo.pvd_nombre}'
        )
    except Sala.DoesNotExist:
        messages.error(request, 'La sala no existe.')

    return redirect('modulo_puntos:lista_salas')


# ==============================================================================
# REGISTRO DE USUARIO CIUDADANO (Sin autenticación)
# ==============================================================================

def registrar_usuario_ciudadano(request):
    """
    Vista para que los usuarios se registren como ciudadanos.
    No requiere autenticación. Los registros quedan pendientes de aprobación.
    """
    if request.method == 'POST':
        form = CiudadanoForm(request.POST)
        if form.is_valid():
            try:
                ciudadano = form.save(commit=False)
                ciudadano.ciu_pendiente_aprobacion = True
                ciudadano.ciu_estdo = 'A'
                ciudadano.save()
                
                messages.success(
                    request,
                    '¡Registro exitoso! Tu información ha sido enviada para aprobación. '
                    'Un administrador del PVD revisará tus datos.'
                )
                registrar_auditoria(
                    request, 'CREATE', 'Ciudadano', ciudadano.ciu_cdgo,
                    f'Registro pendiente de aprobación: {ciudadano.ciu_nmbres} {ciudadano.ciu_aplldos}'
                )
                return redirect('modulo_puntos:registro_exitoso')
            except Exception as e:
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            messages.error(request, 'Formulario inválido. Revisa los campos.')
    else:
        form = CiudadanoForm()

    return render(
        request,
        'modulo_puntos/registrar_usuario_ciudadano.html',
        {'form': form}
    )


def registro_exitoso(request):
    """Vista de confirmación de registro exitoso."""
    return render(request, 'modulo_puntos/registro_exitoso.html')


# ==============================================================================
# APROBACIÓN DE CIUDADANOS PENDIENTES (Admin PVD)
# ==============================================================================

@login_required(login_url='/login/')
def ciudadanos_pendientes(request):
    """
    Vista para que los Admin PVD revisen y aprueben ciudadanos pendientes.
    SOLO accesible para Admin PVD (no Superusuario ni Admin TIC).
    """
    # Verificar que sea SOLO Admin PVD (no superuser ni admin TIC)
    es_admin_pvd = request.user.groups.filter(name='Administrador PVD').exists()
    if not es_admin_pvd or request.user.is_superuser:
        messages.error(request, 'Solo los Administradores PVD pueden aprobar registros de ciudadanos.')
        return redirect('modulo_puntos:panel_control')

    # Obtener ciudadanos pendientes de aprobación
    ciudadanos_pendientes = Ciudadano.objects.filter(
        ciu_pendiente_aprobacion=True
    ).order_by('-ciu_fecha_registro')

    # Filtrar por PVD activo si hay uno seleccionado
    pvd_activo_id = request.session.get('pvd_activo_id')
    if pvd_activo_id:
        ciudadanos_pendientes = ciudadanos_pendientes.filter(
            Q(pvd_cdgo_id=pvd_activo_id) | Q(pvd_cdgo__isnull=True)
        )

    context = {
        'ciudadanos_pendientes': ciudadanos_pendientes,
        'total_pendientes': ciudadanos_pendientes.count(),
    }
    return render(request, 'modulo_puntos/ciudadanos_pendientes.html', context)


@login_required(login_url='/login/')
def aprobar_ciudadano(request, ciu_cdgo):
    """
    Aprobar un ciudadano pendiente.
    SOLO Admin PVD puede aprobar (no Superusuario ni Admin TIC).
    """
    es_admin_pvd = request.user.groups.filter(name='Administrador PVD').exists()
    if not es_admin_pvd or request.user.is_superuser:
        messages.error(request, 'Solo los Administradores PVD pueden aprobar registros.')
        return redirect('modulo_puntos:panel_control')

    try:
        ciudadano = Ciudadano.objects.get(pk=ciu_cdgo, ciu_pendiente_aprobacion=True)
        ciudadano.ciu_pendiente_aprobacion = False
        
        # Asignar al PVD activo si hay uno seleccionado
        pvd_activo_id = request.session.get('pvd_activo_id')
        if pvd_activo_id and not ciudadano.pvd_cdgo_id:
            try:
                ciudadano.pvd_cdgo_id = pvd_activo_id
            except PuntoViveDigital.DoesNotExist:
                pass
        
        ciudadano.save()
        
        messages.success(
            request,
            f'Ciudadano {ciudadano.ciu_nmbres} {ciudadano.ciu_aplldos} aprobado correctamente.'
        )
        registrar_auditoria(
            request, 'UPDATE', 'Ciudadano', ciudadano.ciu_cdgo,
            f'Ciudadano aprobado: {ciudadano.ciu_nmbres} {ciudadano.ciu_aplldos}'
        )
    except Ciudadano.DoesNotExist:
        messages.error(request, 'El ciudadano no existe o ya fue aprobado.')

    return redirect('modulo_puntos:ciudadanos_pendientes')


@login_required(login_url='/login/')
def rechazar_ciudadano(request, ciu_cdgo):
    """
    Rechazar/Eliminar un ciudadano pendiente.
    SOLO Admin PVD puede rechazar (no Superusuario ni Admin TIC).
    """
    es_admin_pvd = request.user.groups.filter(name='Administrador PVD').exists()
    if not es_admin_pvd or request.user.is_superuser:
        messages.error(request, 'Solo los Administradores PVD pueden rechazar registros.')
        return redirect('modulo_puntos:panel_control')

    try:
        ciudadano = Ciudadano.objects.get(pk=ciu_cdgo, ciu_pendiente_aprobacion=True)
        nombre_completo = f"{ciudadano.ciu_nmbres} {ciudadano.ciu_aplldos}"
        ciudadano.delete()
        
        messages.success(
            request,
            f'El registro de {nombre_completo} ha sido rechazado/eliminado.'
        )
        registrar_auditoria(
            request, 'DELETE', 'Ciudadano', ciu_cdgo,
            f'Ciudadano rechazado/eliminado: {nombre_completo}'
        )
    except Ciudadano.DoesNotExist:
        messages.error(request, 'El ciudadano no existe o ya fue procesado.')

    return redirect('modulo_puntos:ciudadanos_pendientes')


# ==============================================================================
# GESTIÓN DE ROLES Y PERMISOS
# ==============================================================================

@login_required(login_url='/login/')
def gestionar_roles(request):
    """
    Vista para que el Superusuario gestione roles y permisos de usuarios.
    Solo el Superusuario puede acceder a esta vista.
    """
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para gestionar roles.')
        return redirect('modulo_puntos:panel_control')

    from django.contrib.auth.models import User, Group
    from django.db.models import Q

    # Obtener todos los usuarios excepto el superusuario actual
    usuarios = User.objects.filter(is_superuser=False).order_by('username')
    
    # Obtener todos los grupos disponibles
    grupos = Group.objects.all().order_by('name')
    
    # Búsqueda y filtros
    busqueda = request.GET.get('q', '')
    rol_filtro = request.GET.get('rol', '')
    
    if busqueda:
        usuarios = usuarios.filter(
            Q(username__icontains=busqueda) |
            Q(first_name__icontains=busqueda) |
            Q(last_name__icontains=busqueda) |
            Q(email__icontains=busqueda)
        )
    
    if rol_filtro:
        usuarios = usuarios.filter(groups__name=rol_filtro)
    
    # Contar usuarios por rol
    stats_roles = {}
    for grupo in grupos:
        stats_roles[grupo.name] = grupo.user_set.count()
    
    context = {
        'usuarios': usuarios,
        'grupos': grupos,
        'stats_roles': stats_roles,
        'busqueda': busqueda,
        'rol_filtro': rol_filtro,
    }
    
    return render(request, 'modulo_puntos/gestionar_roles.html', context)


@login_required(login_url='/login/')
def asignar_rol_usuario(request, user_id):
    """
    Asigna o cambia el rol de un usuario.
    Solo el Superusuario puede realizar esta acción.
    """
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para asignar roles.')
        return redirect('modulo_puntos:panel_control')
    
    from django.contrib.auth.models import User, Group
    
    try:
        usuario = User.objects.get(pk=user_id)
        
        if request.method == 'POST':
            nuevo_rol = request.POST.get('nuevo_rol', '')
            
            # Remover todos los grupos actuales
            usuario.groups.clear()
            
            # Agregar al nuevo grupo si se especificó
            if nuevo_rol:
                try:
                    grupo = Group.objects.get(name=nuevo_rol)
                    usuario.groups.add(grupo)
                    messages.success(
                        request,
                        f'Rol "{nuevo_rol}" asignado correctamente a {usuario.username}.'
                    )
                    registrar_auditoria(
                        request, 'UPDATE', 'User', user_id,
                        f'Rol asignado: {nuevo_rol} a usuario {usuario.username}'
                    )
                except Group.DoesNotExist:
                    messages.error(request, f'El rol "{nuevo_rol}" no existe.')
            else:
                messages.info(request, f'Se removieron todos los roles de {usuario.username}.')
                registrar_auditoria(
                    request, 'UPDATE', 'User', user_id,
                    f'Roles removidos de usuario {usuario.username}'
                )
            
            return redirect('modulo_puntos:gestionar_roles')
        
    except User.DoesNotExist:
        messages.error(request, 'El usuario no existe.')
        return redirect('modulo_puntos:gestionar_roles')


@login_required(login_url='/login/')
def crear_grupo_rol(request):
    """
    Crea un nuevo grupo/rol personalizado.
    Solo el Superusuario puede crear nuevos roles.
    """
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para crear roles.')
        return redirect('modulo_puntos:panel_control')
    
    from django.contrib.auth.models import Group
    
    if request.method == 'POST':
        nombre_rol = request.POST.get('nombre_rol', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        
        if not nombre_rol:
            messages.error(request, 'El nombre del rol es requerido.')
        elif Group.objects.filter(name=nombre_rol).exists():
            messages.error(request, f'Ya existe un rol con el nombre "{nombre_rol}".')
        else:
            grupo = Group.objects.create(name=nombre_rol)
            messages.success(request, f'Rol "{nombre_rol}" creado correctamente.')
            registrar_auditoria(
                request, 'CREATE', 'Group', grupo.pk,
                f'Nuevo rol creado: {nombre_rol}'
            )
            return redirect('modulo_puntos:gestionar_roles')
    
    return redirect('modulo_puntos:gestionar_roles')
