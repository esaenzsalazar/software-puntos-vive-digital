import csv
import random
from datetime import datetime, date as date_type, time as time_type
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, Permission, User
from django.db.models import Q, Count, Avg
from django.db.models.functions import TruncMonth
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .models import (
    Ciudadano, Atencion, Satisfaccion, Servicio, PrestamoRecurso,
    Recurso, Operador, PuntoViveDigital, Sala, UserProfile, AuditoriaAccion,
    PermisoDefinicion, PermisoRol, PermisoUsuario, HabilitacionSala,
)
from .forms import (
    CiudadanoForm, AtencionForm, SatisfaccionForm, ServicioForm,
    PrestamoRecursoForm, RecursoForm, LoginForm, PerfilUsuarioForm,
    CrearUsuarioForm, PuntoViveDigitalForm, SalaForm, PermisoDefinicionForm,
    HabilitacionSalaForm,
)
from .utils import registrar_auditoria, tiene_permiso


# ── HELPERS ────────────────────────────────────────────────────────────────────

def usuario_es_superusuario(user):
    return user.is_authenticated and user.is_superuser


def usuario_es_admin_tic(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name='Administrador TIC').exists()


def usuario_es_operador(user):
    if not user.is_authenticated:
        return False
    return user.groups.filter(name='Operador').exists()


def usuario_necesita_seleccionar_pvd(user):
    """Admin PVD y Operador deben elegir un PVD antes de operar."""
    if not user.is_authenticated:
        return False
    if user.is_superuser or usuario_es_admin_tic(user):
        return False
    return (
        user.groups.filter(name='Administrador PVD').exists()
        or user.groups.filter(name='Operador').exists()
    )


def usuario_puede_usar_modulos_pvd(user):
    if not user.is_authenticated:
        return False
    return (
        user.is_superuser
        or usuario_es_admin_tic(user)
        or user.groups.filter(name='Administrador PVD').exists()
        or user.groups.filter(name='Operador').exists()
    )


def obtener_rol_usuario(user):
    if not user.is_authenticated:
        return 'Sin sesión'
    if user.is_superuser:
        return 'Superusuario'
    grupos = list(user.groups.values_list('name', flat=True))
    return ', '.join(grupos) if grupos else 'Sin rol asignado'


# ── AUTENTICACIÓN ──────────────────────────────────────────────────────────────

def inicio(request):
    if request.user.is_authenticated:
        return redirect('modulo_puntos:panel_control')
    return redirect('modulo_puntos:login')


def login_usuario(request):
    if request.user.is_authenticated:
        return redirect('modulo_puntos:panel_control')

    next_url = request.GET.get('next') or request.POST.get('next') or reverse('modulo_puntos:panel_control')
    form = LoginForm(request=request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Inicio de sesión correcto.')
            if usuario_necesita_seleccionar_pvd(user):
                return redirect('modulo_puntos:seleccionar_pvd_view')
            return redirect(next_url)
        messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'registration/login.html', {'form': form, 'next': next_url})


def logout_usuario(request):
    logout(request)
    return redirect('modulo_puntos:login')


# ── PERFIL ─────────────────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def perfil_usuario(request):
    if request.method == 'POST':
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
            return redirect('modulo_puntos:perfil_usuario')
        messages.error(request, 'No se pudo actualizar el perfil. Revisa los datos ingresados.')
    else:
        form = PerfilUsuarioForm(instance=request.user)

    return render(request, 'modulo_puntos/perfil_usuario.html', {
        'form': form,
        'rol_usuario': obtener_rol_usuario(request.user),
    })


# ── PANEL DE CONTROL ───────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def panel_control(request):
    user = request.user

    # Admin PVD y Operador deben seleccionar PVD antes de entrar al panel
    if usuario_necesita_seleccionar_pvd(user):
        pvd_id_session = request.session.get('pvd_activo_id')
        if not pvd_id_session:
            messages.info(request, 'Selecciona un Punto Vive Digital para comenzar.')
            return redirect('modulo_puntos:seleccionar_pvd_view')

    es_operador_only = (
        usuario_es_operador(user)
        and not user.groups.filter(name='Administrador PVD').exists()
        and not usuario_es_admin_tic(user)
        and not user.is_superuser
    )

    context = {
        'total_ciudadanos': Ciudadano.objects.count(),
        'atenciones_registradas': Atencion.objects.count(),
        'total_satisfacciones': Satisfaccion.objects.count(),
        'total_servicios': Servicio.objects.count(),
        'total_prestamos': PrestamoRecurso.objects.count(),
        'es_superusuario': usuario_es_superusuario(user),
        'es_admin_tic_only': user.groups.filter(name='Administrador TIC').exists() and not user.is_superuser,
        'es_admin_pvd_only': user.groups.filter(name='Administrador PVD').exists() and not usuario_es_admin_tic(user),
        'es_operador_only': es_operador_only,
        'mostrar_modulos_tic': usuario_es_admin_tic(user),
        'mostrar_modulos_pvd': usuario_puede_usar_modulos_pvd(user),
        'rol_usuario': obtener_rol_usuario(user),
        'pvd_activo': None,
    }
    pvd_id = request.session.get('pvd_activo_id')
    if pvd_id:
        context['pvd_activo'] = PuntoViveDigital.objects.filter(pk=pvd_id, estado='A').first()
    return render(request, 'modulo_puntos/panel_control.html', context)


# ── SELECCIÓN DE PVD ───────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def seleccionar_pvd_view(request):
    pvds = PuntoViveDigital.objects.filter(estado='A').order_by('nombre')
    return render(request, 'modulo_puntos/seleccionar_pvd.html', {'pvds': pvds})


@login_required(login_url='/login/')
def seleccionar_pvd(request, pvd_cdgo):
    pvd = get_object_or_404(PuntoViveDigital, pk=pvd_cdgo, estado='A')
    request.session['pvd_activo_id'] = pvd.pk
    messages.success(request, f'Trabajando en: {pvd.nombre}')
    return redirect('modulo_puntos:panel_control')


@login_required(login_url='/login/')
def inicio_pvd(request):
    pvd_id = request.session.get('pvd_activo_id')
    pvd = None
    context = {}
    if pvd_id:
        pvd = PuntoViveDigital.objects.filter(pk=pvd_id, estado='A').first()
    if pvd:
        context['total_ciudadanos'] = Ciudadano.objects.filter(punto_vive_digital=pvd).count()
        context['total_atenciones'] = Atencion.objects.filter(punto_vive_digital=pvd).count()
        context['total_salas'] = Sala.objects.filter(punto_vive_digital=pvd).count()
    context['pvd'] = pvd
    return render(request, 'modulo_puntos/inicio_pvd.html', context)


# ── GESTIÓN DE CIUDADANOS ──────────────────────────────────────────────────────

@login_required(login_url='/login/')
def consultar_ciudadanos(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    busqueda = request.GET.get('q', '').strip()
    ciudadanos = Ciudadano.objects.all().order_by('-pk')

    if busqueda:
        ciudadanos = ciudadanos.filter(
            Q(numero_documento__icontains=busqueda) |
            Q(primer_nombre__icontains=busqueda) |
            Q(primer_apellido__icontains=busqueda) |
            Q(segundo_nombre__icontains=busqueda) |
            Q(segundo_apellido__icontains=busqueda)
        )

    return render(request, 'modulo_puntos/consultar_ciudadanos.html', {
        'ciudadanos': ciudadanos,
        'busqueda': busqueda,
        'total_resultados': ciudadanos.count(),
    })


@login_required(login_url='/login/')
def registrar_ciudadano(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    form = CiudadanoForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Ciudadano registrado exitosamente en la base de datos.')
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            messages.error(request, 'Formulario inválido. Revisa los campos.')

    return render(request, 'modulo_puntos/registrar_ciudadano.html', {'form': form})


@login_required(login_url='/login/')
def editar_ciudadano(request, ciu_cdgo):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    ciudadano = get_object_or_404(Ciudadano, pk=ciu_cdgo)
    form = CiudadanoForm(request.POST or None, instance=ciudadano)
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Ciudadano actualizado correctamente en la base de datos.')
                return redirect('modulo_puntos:consultar_ciudadanos')
            except Exception as e:
                messages.error(request, f'Error al actualizar en BD: {e}')
        else:
            messages.error(request, 'No se pudo actualizar el ciudadano. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/editar_ciudadano.html', {
        'form': form,
        'ciudadano': ciudadano,
    })


@login_required(login_url='/login/')
def historial_ciudadano(request, ciu_cdgo):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    ciudadano = get_object_or_404(Ciudadano, pk=ciu_cdgo)

    atenciones = Atencion.objects.filter(
        ciudadano=ciudadano
    ).select_related(
        'operador',
        'prestamo',
        'prestamo__recurso'
    ).order_by('-fecha', '-hora_inicio')

    for atencion in atenciones:
        atencion.servicios_rel = Servicio.objects.filter(atencion=atencion)
        atencion.satisfacciones_rel = Satisfaccion.objects.filter(atencion=atencion)

    return render(request, 'modulo_puntos/historial_ciudadano.html', {
        'ciudadano': ciudadano,
        'atenciones': atenciones,
        'total_atenciones': atenciones.count(),
    })


# ── REGISTRO CIUDADANO PÚBLICO (sin login) ─────────────────────────────────────

def registrar_usuario_ciudadano(request):
    form = CiudadanoForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('modulo_puntos:registro_exitoso')
        messages.error(request, 'Revisa los datos ingresados.')
    return render(request, 'modulo_puntos/registrar_usuario_ciudadano.html', {'form': form})


def registro_exitoso(request):
    return render(request, 'modulo_puntos/registro_exitoso.html')


# ── REPORTES ───────────────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def reportes(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    total_ciudadanos = Ciudadano.objects.count()
    ciudadanos_activos = Ciudadano.objects.filter(estado='A').count()
    total_operadores = Operador.objects.count()
    operadores_activos = Operador.objects.filter(estado='A').count()
    total_atenciones = Atencion.objects.count()
    atenciones_pendientes = Atencion.objects.filter(estado='P').count()
    atenciones_finalizadas = Atencion.objects.filter(estado='F').count()
    atenciones_canceladas = Atencion.objects.filter(estado='C').count()
    total_servicios = Servicio.objects.count()
    total_prestamos = PrestamoRecurso.objects.count()
    prestamos_activos = PrestamoRecurso.objects.filter(fecha_devolucion__isnull=True).count()

    satisfaccion_promedio = Satisfaccion.objects.aggregate(
        promedio=Avg('calificacion')
    )['promedio']

    servicios_por_tipo = Servicio.objects.values('tipo').annotate(
        total=Count('id')
    ).order_by('-total', 'tipo')

    atenciones_por_operador = Atencion.objects.values(
        'operador__primer_nombre',
        'operador__primer_apellido'
    ).annotate(
        total=Count('id')
    ).order_by('-total')

    atenciones_recientes = Atencion.objects.select_related(
        'ciudadano', 'operador'
    ).order_by('-fecha', '-hora_inicio')[:10]

    gen_map = dict(Ciudadano.GENERO_CHOICES)
    ciudadanos_por_genero = []
    for row in Ciudadano.objects.values('genero').annotate(total=Count('id')).order_by('-total'):
        clave = row['genero'] or ''
        ciudadanos_por_genero.append({
            'etiqueta': gen_map.get(clave, clave or 'Sin dato'),
            'total': row['total'],
        })

    ciudadanos_por_etnia = list(
        Ciudadano.objects.exclude(etnia__isnull=True).exclude(etnia='').values('etnia').annotate(
            total=Count('id')
        ).order_by('-total')[:20]
    )

    ciudadanos_por_nvleduc = list(
        Ciudadano.objects.exclude(nivel_educativo__isnull=True).exclude(nivel_educativo='').values('nivel_educativo').annotate(
            total=Count('id')
        ).order_by('-total')[:20]
    )

    ciudadanos_por_estrato = list(
        Ciudadano.objects.values('estrato').annotate(total=Count('id')).order_by('estrato')
    )

    ciudadanos_por_ocupacion = list(
        Ciudadano.objects.exclude(ocupacion__isnull=True).exclude(ocupacion='').values('ocupacion').annotate(
            total=Count('id')
        ).order_by('-total')[:15]
    )

    ciudadanos_con_discapacidad = Ciudadano.objects.filter(tiene_discapacidad=True).count()
    ciudadanos_sin_discapacidad = Ciudadano.objects.filter(tiene_discapacidad=False).count()

    atenciones_por_mes = list(
        Atencion.objects.annotate(mes=TruncMonth('fecha'))
        .values('mes')
        .annotate(total=Count('id'))
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


# ── ATENCIONES Y SERVICIOS ─────────────────────────────────────────────────────

@login_required(login_url='/login/')
def registrar_atencion(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    operador_actual = None
    if request.user.first_name:
        operador_actual = Operador.objects.filter(
            primer_nombre__icontains=request.user.first_name
        ).first()

    datos_iniciales = {}
    if operador_actual:
        datos_iniciales['operador'] = operador_actual.pk

    form = AtencionForm(request.POST or None, initial=datos_iniciales)

    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Atención registrada correctamente en la base de datos.')
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            messages.error(request, 'No se pudo guardar la atención. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/registrar_atencion.html', {'form': form})


@login_required(login_url='/login/')
def registrar_prestamo(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    form = PrestamoRecursoForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Préstamo registrado correctamente en la base de datos.')
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            messages.error(request, 'No se pudo guardar el préstamo. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/registrar_prestamo.html', {'form': form})


@login_required(login_url='/login/')
def registrar_recurso(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    form = RecursoForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Recurso registrado correctamente en la base de datos.')
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            messages.error(request, 'No se pudo guardar el recurso. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/registrar_recurso.html', {'form': form})


@login_required(login_url='/login/')
def registrar_satisfaccion(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    form = SatisfaccionForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Satisfacción registrada correctamente en la base de datos.')
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            messages.error(request, 'No se pudo guardar la satisfacción. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/registrar_satisfaccion.html', {'form': form})


@login_required(login_url='/login/')
def registrar_servicio(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    form = ServicioForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Servicio registrado correctamente en la base de datos.')
                return redirect('modulo_puntos:panel_control')
            except Exception as e:
                messages.error(request, f'Error al guardar en BD: {e}')
        else:
            messages.error(request, 'No se pudo guardar el servicio. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/registrar_servicio.html', {'form': form})


# ── EXPORTACIÓN CSV ────────────────────────────────────────────────────────────

def _csv_response(filename_base):
    response = HttpResponse(content_type='text/csv')
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    response['Content-Disposition'] = f'attachment; filename="{filename_base}_{fecha_actual}.csv"'
    response.write('﻿'.encode('utf8'))
    return response


@login_required(login_url='/login/')
def exportar_atenciones_csv(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    response = _csv_response('Reporte_Atenciones_PVD')
    writer = csv.writer(response)
    writer.writerow([
        'ID Atención', 'Fecha', 'Hora Inicio', 'Hora Fin', 'Estado Atención',
        'Documento Ciudadano', 'Nombre Completo', 'Género', 'Etnia',
        'Discapacidad', 'Detalle Discapacidad', 'Barrio', 'Dirección', 'Vereda / Corregimiento',
        'Operador a Cargo', 'Observaciones'
    ])

    atenciones = Atencion.objects.select_related('ciudadano', 'operador').order_by('-fecha', '-hora_inicio')
    estado_dict = dict(Atencion.ESTADO_CHOICES)

    for atencion in atenciones:
        if atencion.ciudadano:
            c = atencion.ciudadano
            doc_ciu = c.numero_documento
            nom_ciu = f"{c.primer_nombre or ''} {c.primer_apellido or ''}".strip()
            gen_ciu = c.get_genero_display()
            etnia_ciu = c.etnia or 'N/A'
            discap_ciu = 'Sí' if c.tiene_discapacidad else 'No'
            desc_discap_ciu = c.descripcion_discapacidad or 'N/A'
            barrio_ciu = c.barrio or 'N/A'
            dir_ciu = c.direccion or 'N/A'
            rural_ciu = c.zona_rural or 'N/A'
        else:
            doc_ciu = nom_ciu = gen_ciu = etnia_ciu = discap_ciu = desc_discap_ciu = barrio_ciu = dir_ciu = rural_ciu = 'N/A'

        if atencion.operador:
            o = atencion.operador
            operador_info = f"{o.primer_nombre or ''} {o.primer_apellido or ''}".strip()
        else:
            operador_info = 'N/A'

        estado_display = estado_dict.get(atencion.estado, atencion.estado)

        writer.writerow([
            atencion.pk, atencion.fecha, atencion.hora_inicio,
            atencion.hora_fin or 'N/A', estado_display,
            doc_ciu, nom_ciu, gen_ciu, etnia_ciu, discap_ciu, desc_discap_ciu,
            barrio_ciu, dir_ciu, rural_ciu, operador_info,
            atencion.observaciones or 'Sin observaciones'
        ])

    return response


@login_required(login_url='/login/')
def exportar_ciudadanos_csv(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    response = _csv_response('Reporte_Ciudadanos_PVD')
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Tipo doc.', 'Número doc.', 'Nombres', 'Apellidos', 'Fecha nacimiento', 'Género', 'Etnia',
        'Nivel educativo', 'Ocupación', 'Discapacidad', 'Descripción discapacidad', 'Dirección', 'Barrio',
        'Zona rural', 'Estrato', 'Estado', 'Email', 'Teléfono'
    ])
    for c in Ciudadano.objects.all().order_by('-pk'):
        writer.writerow([
            c.pk, c.tipo_documento, c.numero_documento,
            f"{c.primer_nombre or ''} {c.segundo_nombre or ''}".strip(),
            f"{c.primer_apellido or ''} {c.segundo_apellido or ''}".strip(),
            c.fecha_nacimiento, c.get_genero_display(), c.etnia or '',
            c.nivel_educativo or '', c.ocupacion or '',
            'Sí' if c.tiene_discapacidad else 'No',
            c.descripcion_discapacidad or '',
            c.direccion or '', c.barrio or '', c.zona_rural or '',
            c.estrato, c.get_estado_display(), c.correo, c.telefono
        ])
    return response


@login_required(login_url='/login/')
def exportar_servicios_csv(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    response = _csv_response('Reporte_Servicios_PVD')
    writer = csv.writer(response)
    writer.writerow([
        'ID servicio', 'ID atención', 'Fecha atención', 'Documento ciudadano', 'Nombre ciudadano',
        'Nombre servicio', 'Descripción', 'Tipo servicio', 'Requiere equipo', 'Estado servicio'
    ])
    qs = Servicio.objects.select_related('atencion', 'atencion__ciudadano').order_by('-pk')
    for s in qs:
        atn = s.atencion
        fecha_atn = atn.fecha if atn else ''
        doc = nom = ''
        if atn and atn.ciudadano:
            doc = atn.ciudadano.numero_documento
            nom = f"{atn.ciudadano.primer_nombre or ''} {atn.ciudadano.primer_apellido or ''}".strip()
        writer.writerow([
            s.pk, atn.pk if atn else '', fecha_atn, doc, nom,
            s.nombre, s.descripcion or '', s.tipo,
            s.get_requiere_equipo_display(), s.get_estado_display()
        ])
    return response


@login_required(login_url='/login/')
def exportar_satisfaccion_csv(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    response = _csv_response('Reporte_Satisfaccion_PVD')
    writer = csv.writer(response)
    writer.writerow([
        'ID satisfacción', 'ID atención', 'Fecha atención', 'Estado atención', 'Documento ciudadano',
        'Nombre ciudadano', 'Calificación', 'Comentario', 'Fecha registro satisfacción'
    ])
    qs = Satisfaccion.objects.select_related('atencion', 'atencion__ciudadano').order_by('-pk')
    estado_atn = dict(Atencion.ESTADO_CHOICES)
    for sat in qs:
        atn = sat.atencion
        doc = nom = fecha_atn = est_atn = ''
        if atn:
            fecha_atn = str(atn.fecha)
            est_atn = estado_atn.get(atn.estado, atn.estado)
            if atn.ciudadano:
                doc = atn.ciudadano.numero_documento
                nom = f"{atn.ciudadano.primer_nombre or ''} {atn.ciudadano.primer_apellido or ''}".strip()
        writer.writerow([
            sat.pk, atn.pk if atn else '', fecha_atn, est_atn, doc, nom,
            sat.calificacion, sat.comentario or '', sat.fecha
        ])
    return response


@login_required(login_url='/login/')
def exportar_prestamos_csv(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    response = _csv_response('Reporte_Prestamos_PVD')
    writer = csv.writer(response)
    writer.writerow([
        'ID préstamo', 'Tipo recurso', 'Fecha entrega', 'Fecha devolución', 'Observaciones', 'Estado'
    ])
    for p in PrestamoRecurso.objects.select_related('recurso').order_by('-pk'):
        tipo = p.recurso.tipo if p.recurso else ''
        dev = p.fecha_devolucion or ''
        estado = 'Activo (sin devolución)' if not p.fecha_devolucion else 'Devuelto'
        writer.writerow([p.pk, tipo, p.fecha_entrega, dev, p.observaciones or '', estado])
    return response


# ── AYUDA ──────────────────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def ayuda_sistema(request):
    return render(request, 'modulo_puntos/ayuda.html', {
        'rol_usuario': obtener_rol_usuario(request.user),
    })


# ── GESTIÓN DE USUARIOS ────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def crear_admin_tic(request):
    if not usuario_es_superusuario(request.user):
        messages.error(request, 'No tienes permisos para crear Administradores TIC.')
        return redirect('modulo_puntos:panel_control')

    form = CrearUsuarioForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            grupo, _ = Group.objects.get_or_create(name='Administrador TIC')
            user.groups.add(grupo)
            messages.success(request, f'Administrador TIC creado. Usuario: {user.username}')
            return redirect('modulo_puntos:panel_control')
        messages.error(request, 'No se pudo crear el usuario. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/crear_usuario.html', {
        'form': form,
        'titulo': 'Crear Administrador TIC',
        'rol': 'Administrador TIC',
        'rol_tipo': 'admin_tic',
    })


@login_required(login_url='/login/')
def crear_admin_pvd(request):
    if not (usuario_es_superusuario(request.user) or usuario_es_admin_tic(request.user)):
        messages.error(request, 'No tienes permisos para crear Administradores PVD.')
        return redirect('modulo_puntos:panel_control')

    form = CrearUsuarioForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            grupo, _ = Group.objects.get_or_create(name='Administrador PVD')
            user.groups.add(grupo)

            num_doc_temp = str(random.randint(10000000, 99999999))
            Operador.objects.create(
                tipo_documento='CC',
                numero_documento=num_doc_temp,
                primer_nombre=form.cleaned_data.get('primer_nombre', ''),
                primer_apellido=form.cleaned_data.get('primer_apellido', ''),
                correo=form.cleaned_data.get('email', ''),
                telefono='0000000000',
                estado='A'
            )

            messages.success(request, f'Administrador PVD "{user.get_full_name() or user.username}" creado correctamente.')
            return redirect('modulo_puntos:panel_control')
        messages.error(request, 'No se pudo crear el usuario. Revisa los errores.')

    return render(request, 'modulo_puntos/crear_usuario.html', {
        'form': form,
        'titulo': 'Crear Administrador PVD',
        'rol': 'Administrador PVD',
        'rol_tipo': 'admin_pvd',
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


# ── GESTIÓN DE PUNTOS VIVE DIGITAL ─────────────────────────────────────────────

@login_required(login_url='/login/')
def lista_pvd(request):
    if not usuario_es_admin_tic(request.user):
        messages.error(request, 'No tienes permisos para gestionar PVDs.')
        return redirect('modulo_puntos:panel_control')
    pvds = PuntoViveDigital.objects.all().order_by('nombre')
    puede_eliminar_pvd = tiene_permiso(request.user, 'infraestructura.eliminar_pvd')
    return render(request, 'modulo_puntos/lista_pvd.html', {
        'pvds': pvds,
        'puede_eliminar_pvd': puede_eliminar_pvd,
    })


@login_required(login_url='/login/')
def crear_pvd(request):
    if not usuario_es_admin_tic(request.user):
        messages.error(request, 'No tienes permisos para crear PVDs.')
        return redirect('modulo_puntos:panel_control')

    form = PuntoViveDigitalForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            pvd = form.save()

            Sala.objects.get_or_create(
                punto_vive_digital=pvd,
                nombre='Sala Principal',
                defaults={'descripcion': 'Sala principal del PVD', 'estado': 'A'}
            )

            registrar_auditoria(request, 'CREATE', 'PuntoViveDigital', pvd.pk, f'PVD creado: {pvd.nombre}')
            messages.success(request, f'PVD "{pvd.nombre}" creado correctamente.')
            return redirect('modulo_puntos:lista_pvd')
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/form_pvd.html', {
        'form': form,
        'titulo': 'Crear Punto Vive Digital',
        'accion': 'crear',
    })


@login_required(login_url='/login/')
def editar_pvd(request, pvd_cdgo):
    if not usuario_es_admin_tic(request.user):
        messages.error(request, 'No tienes permisos para editar PVDs.')
        return redirect('modulo_puntos:panel_control')

    pvd = get_object_or_404(PuntoViveDigital, pk=pvd_cdgo)
    form = PuntoViveDigitalForm(request.POST or None, instance=pvd)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            registrar_auditoria(request, 'UPDATE', 'PuntoViveDigital', pvd.pk, f'PVD editado: {pvd.nombre}')
            messages.success(request, f'PVD "{pvd.nombre}" actualizado correctamente.')
            return redirect('modulo_puntos:lista_pvd')
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/form_pvd.html', {
        'form': form,
        'titulo': f'Editar PVD: {pvd.nombre}',
        'accion': 'editar',
        'pvd': pvd,
    })


@login_required(login_url='/login/')
def activar_pvd(request, pvd_cdgo):
    if not usuario_es_admin_tic(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')

    pvd = get_object_or_404(PuntoViveDigital, pk=pvd_cdgo)
    pvd.estado = 'I' if pvd.estado == 'A' else 'A'
    pvd.save()
    estado_str = 'activado' if pvd.estado == 'A' else 'desactivado'
    messages.success(request, f'PVD "{pvd.nombre}" {estado_str} correctamente.')
    return redirect('modulo_puntos:lista_pvd')


@login_required(login_url='/login/')
def eliminar_pvd(request, pvd_cdgo):
    if not tiene_permiso(request.user, 'infraestructura.eliminar_pvd'):
        messages.error(request, 'No tienes permiso para eliminar Puntos Vive Digital.')
        return redirect('modulo_puntos:lista_pvd')

    pvd = get_object_or_404(PuntoViveDigital, pk=pvd_cdgo)
    if request.method == 'POST':
        nombre = pvd.nombre
        registrar_auditoria(request, 'DELETE', 'PuntoViveDigital', pvd.pk, f'PVD eliminado: {nombre}')
        pvd.delete()
        messages.success(request, f'PVD "{nombre}" eliminado correctamente.')
        return redirect('modulo_puntos:lista_pvd')

    return redirect('modulo_puntos:lista_pvd')


# ── GESTIÓN DE SALAS ───────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def lista_salas(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
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

    pvd_id = request.session.get('pvd_activo_id')
    initial = {}
    if pvd_id:
        initial['punto_vive_digital'] = pvd_id

    form = SalaForm(request.POST or None, initial=initial)
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

    sala = get_object_or_404(Sala, pk=sala_cdgo)
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

    sala = get_object_or_404(Sala, pk=sala_cdgo)
    sala.estado = 'I' if sala.estado == 'A' else 'A'
    sala.save()
    estado_str = 'activada' if sala.estado == 'A' else 'desactivada'
    messages.success(request, f'Sala "{sala.nombre}" {estado_str} correctamente.')
    return redirect('modulo_puntos:lista_salas')


@login_required(login_url='/login/')
def eliminar_sala(request, sala_cdgo):
    if not tiene_permiso(request.user, 'infraestructura.eliminar_sala'):
        messages.error(request, 'No tienes permiso para eliminar salas.')
        return redirect('modulo_puntos:lista_salas')

    sala = get_object_or_404(Sala, pk=sala_cdgo)
    if request.method == 'POST':
        nombre = sala.nombre
        registrar_auditoria(request, 'DELETE', 'Sala', sala.pk, f'Sala eliminada: {nombre}')
        sala.delete()
        messages.success(request, f'Sala "{nombre}" eliminada correctamente.')
        return redirect('modulo_puntos:lista_salas')

    return redirect('modulo_puntos:lista_salas')


# ── MÓDULO PERMISOS ────────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def lista_permisos_roles(request):
    """Matriz de permisos por rol. Superusuario: todos los roles. Admin TIC: solo admin_pvd y operador."""
    es_superusuario = request.user.is_superuser
    es_admin_tic = not es_superusuario and usuario_es_admin_tic(request.user)

    if not (es_superusuario or es_admin_tic):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('modulo_puntos:panel_control')

    if es_superusuario:
        roles = [('admin_tic', 'Administrador TIC'), ('admin_pvd', 'Administrador PVD'), ('operador', 'Operador')]
        usuarios_con_permisos = User.objects.filter(
            groups__name__in=['Administrador TIC', 'Administrador PVD']
        ).distinct().order_by('username')
    else:
        roles = [('admin_pvd', 'Administrador PVD'), ('operador', 'Operador')]
        usuarios_con_permisos = User.objects.filter(
            Q(groups__name='Administrador PVD') | Q(pvd_profile__rol='operador')
        ).distinct().order_by('username')

    permisos = PermisoDefinicion.objects.filter(activo=True).order_by('categoria', 'nombre')

    if request.method == 'POST':
        for permiso in PermisoDefinicion.objects.filter(activo=True):
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

        actor = 'superusuario' if es_superusuario else 'admin_tic'
        registrar_auditoria(
            request, 'UPDATE', 'PermisoRol', None,
            f'Matriz de permisos por rol actualizada por {actor}.'
        )
        messages.success(request, 'Permisos de roles actualizados correctamente.')
        return redirect('modulo_puntos:lista_permisos_roles')

    asignaciones = set(
        PermisoRol.objects.values_list('permiso_id', 'rol')
    )

    categorias = {}
    for permiso in permisos:
        cat = permiso.categoria
        if cat not in categorias:
            categorias[cat] = []
        celdas = []
        for rol_codigo, _ in roles:
            marcado = (permiso.pk, rol_codigo) in asignaciones
            celdas.append((f'perm_{permiso.pk}_{rol_codigo}', marcado))
        categorias[cat].append({'permiso': permiso, 'celdas': celdas})

    return render(request, 'modulo_puntos/permisos/lista_roles.html', {
        'categorias': categorias,
        'roles': roles,
        'usuarios_con_permisos': usuarios_con_permisos,
        'es_superusuario': es_superusuario,
    })


@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_superuser)
def crear_permiso(request):
    """Crear nueva definición de permiso. Solo superusuario."""
    form = PermisoDefinicionForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            permiso = form.save()
            registrar_auditoria(
                request, 'CREATE', 'PermisoDefinicion', permiso.pk,
                f'Permiso creado: [{permiso.categoria}] {permiso.nombre} ({permiso.codigo})'
            )
            messages.success(request, f'Permiso "{permiso.nombre}" creado correctamente.')
            return redirect('modulo_puntos:lista_permisos_roles')
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/permisos/form_permiso.html', {
        'form': form,
        'titulo': 'Crear Permiso',
        'accion': 'crear',
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
    """Overrides individuales por usuario. Superusuario: cualquier usuario. Admin TIC: solo admin_pvd y operador."""
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
        rol_usuario = 'operador'

    if es_admin_tic and rol_usuario == 'admin_tic':
        messages.error(request, 'No tienes permisos para gestionar los permisos de un Administrador TIC.')
        return redirect('modulo_puntos:lista_permisos_roles')

    if es_admin_tic:
        permisos_pvd_operador_ids = PermisoRol.objects.filter(
            rol__in=['admin_pvd', 'operador']
        ).values_list('permiso_id', flat=True)
        permisos = PermisoDefinicion.objects.filter(
            activo=True, pk__in=permisos_pvd_operador_ids
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


@login_required(login_url='/login/')
def vista_permisos_ofitic(request):
    """Permisos que Ofitic puede gestionar para usuarios admin_pvd."""
    if not usuario_es_admin_tic(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('modulo_puntos:panel_control')

    permisos_delegables = PermisoDefinicion.objects.filter(
        activo=True, delegable_por_ofitic=True
    ).order_by('categoria', 'nombre')

    usuarios_pvd = User.objects.filter(
        groups__name='Administrador PVD'
    ).select_related('pvd_profile').distinct()

    usuario_seleccionado = None
    user_id = request.GET.get('usuario_id') or request.POST.get('usuario_id')
    if user_id:
        usuario_seleccionado = get_object_or_404(User, pk=user_id, groups__name='Administrador PVD')

    overrides_existentes = {}
    permisos_rol_pvd = set(
        PermisoRol.objects.filter(
            rol='admin_pvd',
            permiso__in=permisos_delegables
        ).values_list('permiso_id', flat=True)
    )

    if usuario_seleccionado:
        overrides_existentes = {
            pu.permiso_id: pu
            for pu in PermisoUsuario.objects.filter(usuario=usuario_seleccionado, permiso__in=permisos_delegables)
        }

    if request.method == 'POST' and usuario_seleccionado:
        for permiso in permisos_delegables:
            checkbox_name = f'perm_{permiso.pk}'
            marcado = checkbox_name in request.POST
            override_existente = overrides_existentes.get(permiso.pk)
            hereda_del_rol = permiso.pk in permisos_rol_pvd

            if marcado == hereda_del_rol and override_existente:
                override_existente.delete()
            elif marcado != hereda_del_rol:
                PermisoUsuario.objects.update_or_create(
                    usuario=usuario_seleccionado,
                    permiso=permiso,
                    defaults={'concedido': marcado, 'otorgado_por': request.user},
                )

        registrar_auditoria(
            request, 'UPDATE', 'PermisoUsuario', usuario_seleccionado.pk,
            f'Ofitic {request.user.username} actualizó permisos de {usuario_seleccionado.username}'
        )
        messages.success(request, f'Permisos de {usuario_seleccionado.username} actualizados.')
        return redirect(f"{request.path}?usuario_id={usuario_seleccionado.pk}")

    categorias = {}
    if usuario_seleccionado:
        for permiso in permisos_delegables:
            cat = permiso.categoria
            if cat not in categorias:
                categorias[cat] = []
            override = overrides_existentes.get(permiso.pk)
            if override is not None:
                activo = override.concedido
                es_override = True
            else:
                activo = permiso.pk in permisos_rol_pvd
                es_override = False
            categorias[cat].append({
                'permiso': permiso,
                'activo': activo,
                'es_override': es_override,
            })

    return render(request, 'modulo_puntos/permisos/ofitic_permisos.html', {
        'usuarios_pvd': usuarios_pvd,
        'usuario_seleccionado': usuario_seleccionado,
        'categorias': categorias,
        'user_id': user_id,
    })


# ── HABILITACIÓN DE SALAS ──────────────────────────────────────────────────────

def _actualizar_estados_habilitaciones(qs):
    """Actualiza automáticamente el estado de habilitaciones según la hora actual."""
    ahora = datetime.now()
    hoy = ahora.date()
    hora_actual = ahora.time()

    for hab in qs:
        if hab.estado in ('X', 'F'):
            continue
        if hab.fecha < hoy:
            if hab.estado != 'F':
                HabilitacionSala.objects.filter(pk=hab.pk).update(estado='F')
                hab.estado = 'F'
        elif hab.fecha == hoy:
            if hab.hora_inicio <= hora_actual <= hab.hora_fin and hab.estado not in ('E',):
                HabilitacionSala.objects.filter(pk=hab.pk).update(estado='E')
                hab.estado = 'E'
            elif hora_actual > hab.hora_fin and hab.estado != 'F':
                HabilitacionSala.objects.filter(pk=hab.pk).update(estado='F')
                hab.estado = 'F'


@login_required(login_url='/login/')
def lista_habilitaciones(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
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

    _actualizar_estados_habilitaciones(list(qs))
    qs = qs.order_by('fecha', 'hora_inicio')

    return render(request, 'modulo_puntos/habilitaciones/lista_habilitaciones.html', {
        'habilitaciones': qs,
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

    pvd_id = request.session.get('pvd_activo_id')
    sala_inicial = request.GET.get('sala_id')
    fecha_inicial = request.GET.get('fecha')

    initial = {}
    if sala_inicial:
        initial['sala'] = sala_inicial
    if fecha_inicial:
        initial['fecha'] = fecha_inicial

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
            registrar_auditoria(
                request, 'CREATE', 'HabilitacionSala', hab.pk,
                f'Habilitación creada: {hab.sala.nombre} – {hab.fecha}'
            )
            messages.success(request, f'Habilitación para "{hab.sala.nombre}" el {hab.fecha} registrada correctamente.')
            return redirect('modulo_puntos:lista_habilitaciones')
        messages.error(request, 'Revisa los datos del formulario.')

    return render(request, 'modulo_puntos/habilitaciones/form_habilitacion.html', {
        'form': form,
        'titulo': 'Nueva Habilitación de Sala',
        'accion': 'crear',
    })


@login_required(login_url='/login/')
def editar_habilitacion(request, hab_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    hab = get_object_or_404(HabilitacionSala, pk=hab_id)

    if hab.estado in ('F', 'X'):
        messages.warning(request, 'No se puede editar una habilitación finalizada o cancelada.')
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

    hab = get_object_or_404(HabilitacionSala, pk=hab_id)

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
def agenda_sala(request, sala_id):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')

    sala = get_object_or_404(Sala, pk=sala_id)

    fecha_str = request.GET.get('fecha', '')
    try:
        from datetime import date as dt_date, timedelta
        if fecha_str:
            fecha_base = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        else:
            fecha_base = dt_date.today()
    except ValueError:
        from datetime import date as dt_date, timedelta
        fecha_base = dt_date.today()

    from datetime import timedelta
    fecha_inicio_semana = fecha_base - timedelta(days=fecha_base.weekday())
    dias_semana = [fecha_inicio_semana + timedelta(days=i) for i in range(7)]

    habilitaciones_semana = HabilitacionSala.objects.filter(
        sala=sala,
        fecha__range=[dias_semana[0], dias_semana[-1]],
    ).order_by('fecha', 'hora_inicio')

    _actualizar_estados_habilitaciones(list(habilitaciones_semana))

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
