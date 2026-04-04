import csv
import random
from datetime import datetime
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Q, Count, Avg
from django.db.models.functions import TruncMonth
from django.shortcuts import render, redirect
from django.urls import reverse

from .models import Ciudadano, Atencion, Satisfaccion, Servicio, PrestamoRecurso, Recurso, Operador
from .forms import (
    CiudadanoForm,
    AtencionForm,
    SatisfaccionForm,
    ServicioForm,
    PrestamoRecursoForm,
    RecursoForm,
    LoginForm,
    PerfilUsuarioForm,
    CrearUsuarioForm
)

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

    return render(request, 'registration/login.html', {
        'form': form,
        'next': next_url
    })

def logout_usuario(request):
    logout(request)
    return redirect('modulo_puntos:login')

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

@login_required(login_url='/login/')
def panel_control(request):
    context = {
        'total_ciudadanos': Ciudadano.objects.count(),
        'atenciones_registradas': Atencion.objects.count(),
        'total_satisfacciones': Satisfaccion.objects.count(),
        'total_servicios': Servicio.objects.count(),
        'total_prestamos': PrestamoRecurso.objects.count(),
        'es_superusuario': usuario_es_superusuario(request.user),
        'mostrar_modulos_tic': usuario_es_admin_tic(request.user),
        'mostrar_modulos_pvd': usuario_puede_usar_modulos_pvd(request.user),
        'rol_usuario': obtener_rol_usuario(request.user),
    }
    return render(request, 'modulo_puntos/panel_control.html', context)

@login_required(login_url='/login/')
def consultar_ciudadanos(request):
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

    try:
        ciudadano = Ciudadano.objects.get(pk=ciu_cdgo)
    except Ciudadano.DoesNotExist:
        messages.error(request, 'El ciudadano no existe.')
        return redirect('modulo_puntos:consultar_ciudadanos')

    atenciones = Atencion.objects.filter(
        ciu_cdgo=ciudadano
    ).select_related(
        'opr_cdgo',
        'prs_cdgo',
        'prs_cdgo__rec_cdgo'
    ).order_by('-atn_fecha', '-atn_hrini')

    for atencion in atenciones:
        atencion.servicios_rel = Servicio.objects.filter(atn_cdgo=atencion)
        atencion.satisfacciones_rel = Satisfaccion.objects.filter(atn_cdgo=atencion)

    return render(request, 'modulo_puntos/historial_ciudadano.html', {
        'ciudadano': ciudadano,
        'atenciones': atenciones,
        'total_atenciones': atenciones.count(),
    })

@login_required(login_url='/login/')
def reportes(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

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
    prestamos_activos = PrestamoRecurso.objects.filter(prs_fchdev__isnull=True).count()

    satisfaccion_promedio = Satisfaccion.objects.aggregate(
        promedio=Avg('sat_calif')
    )['promedio']

    servicios_por_tipo = Servicio.objects.values('srv_tipo').annotate(
        total=Count('srv_cdgo')
    ).order_by('-total', 'srv_tipo')

    atenciones_por_operador = Atencion.objects.values(
        'opr_cdgo__opr_nmbres',
        'opr_cdgo__opr_aplldos'
    ).annotate(
        total=Count('atn_cdgo')
    ).order_by('-total')

    atenciones_recientes = Atencion.objects.select_related(
        'ciu_cdgo',
        'opr_cdgo'
    ).order_by('-atn_fecha', '-atn_hrini')[:10]

    gen_map = dict(Ciudadano.GENERO_CHOICES)
    ciudadanos_por_genero = []
    for row in Ciudadano.objects.values('ciu_genro').annotate(total=Count('ciu_cdgo')).order_by('-total'):
        clave = row['ciu_genro'] or ''
        ciudadanos_por_genero.append({
            'etiqueta': gen_map.get(clave, clave or 'Sin dato'),
            'total': row['total'],
        })

    ciudadanos_por_etnia = list(
        Ciudadano.objects.exclude(ciu_etnia__isnull=True).exclude(ciu_etnia='').values('ciu_etnia').annotate(
            total=Count('ciu_cdgo')
        ).order_by('-total')[:20]
    )

    ciudadanos_por_nvleduc = list(
        Ciudadano.objects.exclude(ciu_nvleduc__isnull=True).exclude(ciu_nvleduc='').values('ciu_nvleduc').annotate(
            total=Count('ciu_cdgo')
        ).order_by('-total')[:20]
    )

    ciudadanos_por_estrato = list(
        Ciudadano.objects.values('ciu_estrato').annotate(total=Count('ciu_cdgo')).order_by('ciu_estrato')
    )

    ciudadanos_por_ocupacion = list(
        Ciudadano.objects.exclude(ciu_ocpcion__isnull=True).exclude(ciu_ocpcion='').values('ciu_ocpcion').annotate(
            total=Count('ciu_cdgo')
        ).order_by('-total')[:15]
    )

    ciudadanos_con_discapacidad = Ciudadano.objects.filter(ciu_discapacidad=True).count()
    ciudadanos_sin_discapacidad = Ciudadano.objects.filter(ciu_discapacidad=False).count()

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

@login_required(login_url='/login/')
def registrar_atencion(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    # LÓGICA DE AUTO-ASIGNACIÓN:
    operador_actual = None
    if request.user.first_name:
        operador_actual = Operador.objects.filter(opr_nmbres__icontains=request.user.first_name).first()

    datos_iniciales = {}
    if operador_actual:
        datos_iniciales['opr_cdgo'] = operador_actual.opr_cdgo

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

@login_required(login_url='/login/')
def exportar_atenciones_csv(request):
    if not usuario_puede_usar_modulos_pvd(request.user):
        messages.error(request, 'No tienes permisos para acceder a este módulo.')
        return redirect('modulo_puntos:panel_control')

    response = HttpResponse(content_type='text/csv')
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    response['Content-Disposition'] = f'attachment; filename="Reporte_Atenciones_PVD_{fecha_actual}.csv"'

    response.write('\ufeff'.encode('utf8'))
    writer = csv.writer(response)
    
    writer.writerow([
        'ID Atención', 'Fecha', 'Hora Inicio', 'Hora Fin', 'Estado Atención', 
        'Documento Ciudadano', 'Nombre Completo', 'Género', 'Etnia', 
        'Discapacidad', 'Detalle Discapacidad', 'Barrio', 'Dirección', 'Vereda / Corregimiento',
        'Operador a Cargo', 'Observaciones'
    ])

    atenciones = Atencion.objects.select_related('ciu_cdgo', 'opr_cdgo').order_by('-atn_fecha', '-atn_hrini')

    for atencion in atenciones:
        if atencion.ciu_cdgo:
            doc_ciu = atencion.ciu_cdgo.ciu_numdoc
            nom_ciu = f"{atencion.ciu_cdgo.ciu_nmbres} {atencion.ciu_cdgo.ciu_aplldos}"
            gen_ciu = atencion.ciu_cdgo.get_ciu_genro_display()
            etnia_ciu = atencion.ciu_cdgo.ciu_etnia
            discap_ciu = "Sí" if atencion.ciu_cdgo.ciu_discapacidad else "No"
            desc_discap_ciu = atencion.ciu_cdgo.ciu_desc_discapacidad if atencion.ciu_cdgo.ciu_desc_discapacidad else "N/A"
            barrio_ciu = atencion.ciu_cdgo.ciu_barrio if atencion.ciu_cdgo.ciu_barrio else "N/A"
            dir_ciu = atencion.ciu_cdgo.ciu_dircion if atencion.ciu_cdgo.ciu_dircion else "N/A"
            rural_ciu = atencion.ciu_cdgo.ciu_zrural if atencion.ciu_cdgo.ciu_zrural else "N/A"
        else:
            doc_ciu = nom_ciu = gen_ciu = etnia_ciu = discap_ciu = desc_discap_ciu = barrio_ciu = dir_ciu = rural_ciu = "N/A"

        operador_info = f"{atencion.opr_cdgo.opr_nmbres} {atencion.opr_cdgo.opr_aplldos}" if atencion.opr_cdgo else "N/A"
        estado_dict = dict(Atencion.ESTADO_CHOICES)
        estado_display = estado_dict.get(atencion.atn_estdo, atencion.atn_estdo)

        writer.writerow([
            atencion.atn_cdgo, atencion.atn_fecha, atencion.atn_hrini,
            atencion.atn_hrfin if atencion.atn_hrfin else "N/A", estado_display,
            doc_ciu, nom_ciu, gen_ciu, etnia_ciu, discap_ciu, desc_discap_ciu,
            barrio_ciu, dir_ciu, rural_ciu, operador_info,
            atencion.atn_obs if atencion.atn_obs else "Sin observaciones"
        ])

    return response


def _csv_response(filename_base):
    response = HttpResponse(content_type='text/csv')
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    response['Content-Disposition'] = f'attachment; filename="{filename_base}_{fecha_actual}.csv"'
    response.write('\ufeff'.encode('utf8'))
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
    for c in Ciudadano.objects.all().order_by('-ciu_cdgo'):
        writer.writerow([
            c.ciu_cdgo, c.ciu_tpodoc, c.ciu_numdoc, c.ciu_nmbres, c.ciu_aplldos, c.ciu_fchancm,
            c.get_ciu_genro_display(), c.ciu_etnia, c.ciu_nvleduc, c.ciu_ocpcion,
            'Sí' if c.ciu_discapacidad else 'No',
            c.ciu_desc_discapacidad or '',
            c.ciu_dircion or '', c.ciu_barrio or '', c.ciu_zrural or '',
            c.ciu_estrato, c.get_ciu_estdo_display(), c.ciu_email, c.ciu_tlfno
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
    qs = Servicio.objects.select_related('atn_cdgo', 'atn_cdgo__ciu_cdgo').order_by('-srv_cdgo')
    for s in qs:
        atn = s.atn_cdgo
        fecha_atn = atn.atn_fecha if atn else ''
        doc = nom = ''
        if atn and atn.ciu_cdgo:
            doc = atn.ciu_cdgo.ciu_numdoc
            nom = f"{atn.ciu_cdgo.ciu_nmbres} {atn.ciu_cdgo.ciu_aplldos}"
        writer.writerow([
            s.srv_cdgo, atn.atn_cdgo if atn else '', fecha_atn, doc, nom,
            s.srv_nombre, s.srv_descr or '', s.srv_tipo, s.get_srv_reqeqp_display(),
            s.get_srv_estdo_display()
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
    qs = Satisfaccion.objects.select_related('atn_cdgo', 'atn_cdgo__ciu_cdgo').order_by('-sat_cdgo')
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
            sat.sat_cdgo, atn.atn_cdgo if atn else '', fecha_atn, est_atn, doc, nom,
            sat.sat_calif, sat.sat_cmntrio or '', sat.sat_fecha
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
    for p in PrestamoRecurso.objects.select_related('rec_cdgo').order_by('-prs_cdgo'):
        tipo = p.rec_cdgo.rec_tipo if p.rec_cdgo else ''
        dev = p.prs_fchdev if p.prs_fchdev else ''
        estado = 'Activo (sin devolución)' if not p.prs_fchdev else 'Devuelto'
        writer.writerow([p.prs_cdgo, tipo, p.prs_fchent, dev, p.prs_obs or '', estado])
    return response


@login_required(login_url='/login/')
def ayuda_sistema(request):
    return render(request, 'modulo_puntos/ayuda.html', {
        'rol_usuario': obtener_rol_usuario(request.user),
    })

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
        else:
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

            # LÓGICA DE CREACIÓN AUTOMÁTICA DEL OPERADOR
            num_doc_temp = str(random.randint(10000000, 99999999))
            Operador.objects.create(
                opr_tpodoc='CC',
                opr_numdoc=num_doc_temp,
                opr_nmbres=user.first_name,
                opr_aplldos=user.last_name,
                opr_email=user.email,
                opr_tlfno='0000000000',
                opr_estdo='A'
            )

            messages.success(request, f'Administrador PVD ({user.username}) y su perfil de Operador creados correctamente.')
            return redirect('modulo_puntos:panel_control')
        else:
            messages.error(request, 'No se pudo crear el usuario. Revisa los errores.')

    return render(request, 'modulo_puntos/crear_usuario.html', {
        'form': form,
        'titulo': 'Crear Administrador PVD',
        'rol': 'Administrador PVD'
    })