import csv
import random
from datetime import datetime
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
    Recurso, Operador, PuntoViveDigital, Sala, UserProfile, AuditoriaAccion
)
from .forms import (
    CiudadanoForm, AtencionForm, SatisfaccionForm, ServicioForm,
    PrestamoRecursoForm, RecursoForm, LoginForm, PerfilUsuarioForm,
    CrearUsuarioForm, PuntoViveDigitalForm, SalaForm
)
from .utils import registrar_auditoria


# ── HELPERS ────────────────────────────────────────────────────────────────────

def usuario_es_superusuario(user):
    return user.is_authenticated and user.is_superuser


def usuario_es_admin_tic(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name='Administrador TIC').exists()


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
            login(request, form.get_user())
            messages.success(request, 'Inicio de sesión correcto.')
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
    context = {
        'total_ciudadanos': Ciudadano.objects.count(),
        'atenciones_registradas': Atencion.objects.count(),
        'total_satisfacciones': Satisfaccion.objects.count(),
        'total_servicios': Servicio.objects.count(),
        'total_prestamos': PrestamoRecurso.objects.count(),
        'es_superusuario': usuario_es_superusuario(request.user),
        'es_admin_tic_only': request.user.groups.filter(name='Administrador TIC').exists() and not request.user.is_superuser,
        'es_admin_pvd_only': request.user.groups.filter(name='Administrador PVD').exists() and not usuario_es_admin_tic(request.user),
        'mostrar_modulos_tic': usuario_es_admin_tic(request.user),
        'mostrar_modulos_pvd': usuario_puede_usar_modulos_pvd(request.user),
        'rol_usuario': obtener_rol_usuario(request.user),
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
    return redirect('modulo_puntos:inicio_pvd')


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
            messages.success(request, f'Administrador TIC ({user.username}) creado correctamente.')
            return redirect('modulo_puntos:panel_control')
        messages.error(request, 'No se pudo crear el usuario. Revisa los datos ingresados.')

    return render(request, 'modulo_puntos/crear_usuario.html', {
        'form': form,
        'titulo': 'Crear Administrador TIC',
        'rol': 'Administrador TIC'
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
                primer_nombre=user.first_name,
                primer_apellido=user.last_name,
                correo=user.email,
                telefono='0000000000',
                estado='A'
            )

            messages.success(request, f'Administrador PVD ({user.username}) y su perfil de Operador creados correctamente.')
            return redirect('modulo_puntos:panel_control')
        messages.error(request, 'No se pudo crear el usuario. Revisa los errores.')

    return render(request, 'modulo_puntos/crear_usuario.html', {
        'form': form,
        'titulo': 'Crear Administrador PVD',
        'rol': 'Administrador PVD'
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
    return render(request, 'modulo_puntos/lista_pvd.html', {'pvds': pvds})


@login_required(login_url='/login/')
def crear_pvd(request):
    if not usuario_es_admin_tic(request.user):
        messages.error(request, 'No tienes permisos para crear PVDs.')
        return redirect('modulo_puntos:panel_control')

    admins_pvd = User.objects.filter(
        groups__name='Administrador PVD'
    ).exclude(
        pvd_profile__punto_asignado__isnull=False
    ).distinct()

    form = PuntoViveDigitalForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            pvd = form.save()

            admin_id = request.POST.get('admin_pvd_asignado')
            if admin_id:
                try:
                    admin_user = User.objects.get(pk=admin_id)
                    profile, _ = UserProfile.objects.get_or_create(usuario=admin_user)
                    profile.punto_asignado = pvd
                    profile.rol = 'admin_pvd'
                    profile.save()
                except User.DoesNotExist:
                    pass

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
        'admins_pvd': admins_pvd,
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


# ── GESTIÓN DE SALAS ───────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def lista_salas(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('modulo_puntos:panel_control')

    pvd_id = request.session.get('pvd_activo_id')
    if pvd_id:
        salas = Sala.objects.filter(punto_vive_digital_id=pvd_id).order_by('nombre')
        pvd = PuntoViveDigital.objects.filter(pk=pvd_id).first()
    else:
        salas = Sala.objects.all().select_related('punto_vive_digital').order_by('punto_vive_digital__nombre', 'nombre')
        pvd = None

    return render(request, 'modulo_puntos/lista_salas.html', {'salas': salas, 'pvd': pvd})


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
