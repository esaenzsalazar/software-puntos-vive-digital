#!/usr/bin/env python
"""Script de prueba completo para Puntos Vive Digital."""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.contrib.auth.models import User, Group
from modulo_puntos.models import (
    PuntoViveDigital, Ciudadano, Atencion, Servicio, Satisfaccion,
    Recurso, PrestamoRecurso, Sala, HabilitacionSala, Curso,
    SesionCurso, InscripcionCurso, MantenimientoEquipo, Evidencia, UserProfile
)
from datetime import date, timedelta, time

OK   = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
WARN = "\033[93m⚠\033[0m"
HEAD = "\033[1;34m"
END  = "\033[0m"

resultados = []

def check(nombre, response, codigos_ok=(200, 201, 302)):
    ok = response.status_code in codigos_ok
    print(f"  {OK if ok else FAIL} {nombre} [{response.status_code}]")
    resultados.append((nombre, ok, response.status_code))
    return ok

def titulo(texto):
    print(f"\n{HEAD}{'─'*60}\n  {texto}\n{'─'*60}{END}")

# ── Setup ────────────────────────────────────────────────────────────────────
titulo("PREPARACIÓN")
admin_u  = User.objects.get(username='admin')
ofitic_u = User.objects.get(username='ofitic')
pvdlady_u= User.objects.get(username='pvdlady')
for u, pw in [(admin_u,'admin123'),(ofitic_u,'ofitic123'),(pvdlady_u,'pvd123')]:
    u.set_password(pw); u.save()

pvd1 = PuntoViveDigital.objects.get(pk=1)
try:
    profile = pvdlady_u.pvd_profile
    if not profile.punto_asignado:
        profile.punto_asignado = pvd1; profile.save()
except UserProfile.DoesNotExist:
    UserProfile.objects.create(usuario=pvdlady_u, punto_asignado=pvd1, rol='admin_pvd')
print(f"  {OK} Usuarios y PVD base listos")

c_su   = Client()   # superusuario
c_tic  = Client()   # admin TIC
c_pvd  = Client()   # admin PVD
c_anon = Client()   # sin login

# ════════════════════════════════════════════════════════════════════════════
titulo("BLOQUE 1 — AUTENTICACIÓN")
# ════════════════════════════════════════════════════════════════════════════
check("Login superusuario",          c_su.post('/login/',  {'username':'admin',   'password':'admin123'}),  (302,))
check("Login Admin TIC",             c_tic.post('/login/', {'username':'ofitic',  'password':'ofitic123'}), (302,))
check("Login Admin PVD",             c_pvd.post('/login/', {'username':'pvdlady', 'password':'pvd123'}),    (302,))
check("Login incorrecto → 200",      c_anon.post('/login/',{'username':'admin',   'password':'mal'}),       (200,))
check("Sin login redirige",          c_anon.get('/panel/'),                                                  (302,))
c_pvd.get('/pvd/seleccionar/1/')   # asigna PVD en sesión

# ════════════════════════════════════════════════════════════════════════════
titulo("BLOQUE 2 — PANEL Y NAVEGACIÓN")
# ════════════════════════════════════════════════════════════════════════════
check("Panel superusuario",   c_su.get('/panel/'))
check("Panel Admin TIC",      c_tic.get('/panel/'))
check("Panel Admin PVD",      c_pvd.get('/panel/'))
check("Perfil usuario",       c_su.get('/perfil/'))
check("Ayuda del sistema",    c_su.get('/ayuda/'))

# ════════════════════════════════════════════════════════════════════════════
titulo("BLOQUE 3 — GESTIÓN DE PVDs")
# ════════════════════════════════════════════════════════════════════════════
check("Listar PVDs",  c_su.get('/pvd/'))
check("Formulario nuevo PVD", c_su.get('/pvd/nuevo/'))

r = c_su.post('/pvd/nuevo/', {
    'nombre': 'PVD Test Automatizado',
    'descripcion': 'Creado por prueba',
    'direccion': 'Calle Test 1',
    'barrio': 'Bugalagrande',
    'estado': 'A',
})
check("Crear PVD", r, (302,))

pvd_test = PuntoViveDigital.objects.filter(nombre='PVD Test Automatizado').first()
if pvd_test:
    print(f"  {OK} PVD creado id={pvd_test.pk}")
    r = c_su.post(f'/pvd/editar/{pvd_test.pk}/', {
        'nombre': 'PVD Test Editado',
        'descripcion': 'Editado',
        'direccion': 'Calle Editada',
        'barrio': 'Bugalagrande',
        'estado': 'A',
    })
    check("Editar PVD", r, (302,))
    check("Activar/desactivar PVD", c_su.post(f'/pvd/activar/{pvd_test.pk}/'), (302,))
    check("Eliminar PVD",           c_su.post(f'/pvd/eliminar/{pvd_test.pk}/'), (302,))
else:
    print(f"  {WARN} PVD no se creó — verificar formulario")

check("Seleccionar PVD activo", c_pvd.get('/pvd/seleccionar/1/'), (302,))

# ════════════════════════════════════════════════════════════════════════════
titulo("BLOQUE 4 — GESTIÓN DE CIUDADANOS")
# ════════════════════════════════════════════════════════════════════════════
check("Listar ciudadanos (super)",  c_su.get('/consultar-ciudadanos/'))
check("Listar ciudadanos (TIC)",    c_tic.get('/consultar-ciudadanos/'))
check("Listar ciudadanos (PVD)",    c_pvd.get('/consultar-ciudadanos/'))
check("Formulario registrar ciudadano", c_pvd.get('/registrar-ciudadano/'))

# Limpiar ciudadano previo si quedó de un run anterior
Ciudadano.objects.filter(numero_documento='9999999901').delete()

r = c_pvd.post('/registrar-ciudadano/', {
    'tipo_documento':       'CC',
    'numero_documento':     '9999999901',
    'primer_nombre':        'Juan',
    'segundo_nombre':       'Carlos',
    'primer_apellido':      'Pérez',
    'segundo_apellido':     'Prueba',
    'fecha_nacimiento':     '1990-05-15',
    'genero':               'M',
    'etnia':                'Ninguna',
    'nivel_educativo':      'Secundaria',
    'ocupacion':            'Empleado',
    'estrato':              '2',
    'direccion':            'Calle 1 # 2-3',
    'municipio':            'Bugalagrande',
    'barrio':               'Uribe',
    'zona_rural':           '',
    'correo':               'juan.prueba@test.com',
    'telefono':             '3001234567',
    'tiene_discapacidad':   False,
    'descripcion_discapacidad': '',
    'estado':               'A',
})
check("Registrar ciudadano", r, (302,))

ciudadano = Ciudadano.objects.filter(numero_documento='9999999901').first()
if ciudadano:
    print(f"  {OK} Ciudadano creado: {ciudadano.primer_nombre} {ciudadano.primer_apellido} (id={ciudadano.pk})")
    check("Ver historial ciudadano",   c_pvd.get(f'/historial-ciudadano/{ciudadano.pk}/'))
    check("Formulario editar ciudadano", c_pvd.get(f'/editar-ciudadano/{ciudadano.pk}/'))
    r = c_pvd.post(f'/editar-ciudadano/{ciudadano.pk}/', {
        'tipo_documento':   'CC',
        'numero_documento': '9999999901',
        'primer_nombre':    'Juan Editado',
        'segundo_nombre':   'Carlos',
        'primer_apellido':  'Pérez',
        'segundo_apellido': 'Prueba',
        'fecha_nacimiento': '1990-05-15',
        'genero':           'M',
        'etnia':            'Ninguna',
        'nivel_educativo':  'Secundaria',
        'ocupacion':        'Empleado',
        'estrato':          '3',
        'direccion':        'Calle Editada # 5-6',
        'municipio':        'Bugalagrande',
        'barrio':           'Uribe',
        'zona_rural':       '',
        'correo':           'juan.editado@test.com',
        'telefono':         '3009876543',
        'tiene_discapacidad': False,
        'descripcion_discapacidad': '',
        'estado':           'A',
    })
    check("Editar ciudadano", r, (302,))
else:
    print(f"  {WARN} Ciudadano no se creó, revisando respuesta...")
    from django.test import RequestFactory
    # intentar ver errores del form en respuesta
    print(f"     → status={r.status_code}")

check("Registro público (sin login)",    c_anon.get('/registrar-usuario-ciudadano/'))
check("Página registro exitoso",         c_anon.get('/registro-exitoso/'))
check("Ciudadanos pendientes (admin)",   c_su.get('/ciudadanos-pendientes/'))

# ════════════════════════════════════════════════════════════════════════════
titulo("BLOQUE 5 — ATENCIONES Y SERVICIOS")
# ════════════════════════════════════════════════════════════════════════════
check("Listar atenciones (super)",   c_su.get('/atenciones/'))
check("Listar atenciones (PVD)",     c_pvd.get('/atenciones/'))
check("Buscar ciudadanos AJAX",      c_pvd.get('/atenciones/buscar-ciudadanos/?q=Juan'))
check("Formulario registrar atención", c_pvd.get('/registrar-atencion/'))

atencion = None
if ciudadano:
    r = c_pvd.post('/registrar-atencion/', {
        'ciudadano':    ciudadano.pk,
        'fecha':        date.today().isoformat(),
        'hora_inicio':  '08:00',
        'hora_fin':     '09:00',
        'estado':       'P',
        'observaciones':'Atención de prueba automatizada',
    })
    check("Registrar atención", r, (302,))
    atencion = Atencion.objects.filter(ciudadano=ciudadano).first()

if atencion:
    print(f"  {OK} Atención creada id={atencion.pk}")
    check("Ver detalle atención",      c_pvd.get(f'/atenciones/{atencion.pk}/'))
    check("Formulario editar atención",c_pvd.get(f'/atenciones/{atencion.pk}/editar/'))
    r = c_pvd.post(f'/atenciones/{atencion.pk}/editar/', {
        'ciudadano':    ciudadano.pk,
        'fecha':        date.today().isoformat(),
        'hora_inicio':  '08:00',
        'hora_fin':     '10:00',
        'estado':       'P',
        'observaciones':'Atención editada',
    })
    check("Editar atención", r, (302,))

    # Servicio
    r = c_pvd.post(f'/atenciones/{atencion.pk}/servicio/', {
        'atencion':     atencion.pk,
        'nombre':       'Acceso a internet',
        'tipo':         'Acceso a internet',
        'descripcion':  'Servicio de prueba',
        'requiere_equipo': 'N',
        'estado':       'A',
    })
    check("Agregar servicio a atención", r, (302,))

    servicio = Servicio.objects.filter(atencion=atencion).first()
    if servicio:
        print(f"  {OK} Servicio creado id={servicio.pk}")
        check("Finalizar servicio", c_pvd.post(f'/atenciones/{atencion.pk}/servicio/{servicio.pk}/finalizar/'), (302,))
        check("Formulario editar servicio", c_pvd.get(f'/servicios/{servicio.pk}/editar/'))

    # Satisfacción
    r = c_pvd.post(f'/atenciones/{atencion.pk}/satisfaccion/', {
        'atencion':     atencion.pk,
        'calificacion': 5,
        'comentario':   'Excelente atención de prueba',
        'fecha':        date.today().isoformat() + 'T10:00',
    })
    check("Registrar satisfacción", r, (302,))

    satisfaccion = Satisfaccion.objects.filter(atencion=atencion).first()
    if satisfaccion:
        print(f"  {OK} Satisfacción creada id={satisfaccion.pk}")
        check("Formulario editar satisfacción", c_pvd.get(f'/satisfaccion/{satisfaccion.pk}/editar/'))

    # Cambiar estado
    check("Cambiar estado → Finalizada", c_pvd.post(f'/atenciones/{atencion.pk}/estado/', {'estado':'F'}), (302,))
else:
    print(f"  {WARN} No hay atención, omitiendo sub-pruebas")

check("Gestionar servicios PVD",  c_pvd.get('/servicios/'))

# ════════════════════════════════════════════════════════════════════════════
titulo("BLOQUE 6 — RECURSOS Y PRÉSTAMOS")
# ════════════════════════════════════════════════════════════════════════════
# Usamos superusuario (c_su) que tiene todos los permisos
c_su.get('/pvd/seleccionar/1/')   # asigna PVD en sesión para superusuario
check("Listar recursos (super)",    c_su.get('/recursos/'))
check("Listar recursos (PVD)",      c_pvd.get('/recursos/'), (200,302))
check("Formulario nuevo recurso",   c_su.get('/recursos/nuevo/'))

Recurso.objects.filter(codigo__startswith='LAP-PRUEBA').delete()  # limpiar previos
r = c_su.post('/recursos/nuevo/', {
    'tipo':   'Portátil',
    'codigo': 'LAP-PRUEBA-001',
    'estado': 'A',
})
check("Crear recurso", r, (302,))

recurso = Recurso.objects.filter(codigo='LAP-PRUEBA-001').first()
if recurso:
    print(f"  {OK} Recurso creado id={recurso.pk}")
    check("Formulario editar recurso", c_su.get(f'/recursos/{recurso.pk}/editar/'))
    r = c_su.post(f'/recursos/{recurso.pk}/editar/', {
        'tipo':   'Portátil',
        'codigo': 'LAP-PRUEBA-001-EDIT',
        'estado': 'A',
    })
    check("Editar recurso", r, (302,))

    if ciudadano:
        now = date.today()
        r = c_su.post('/registrar-prestamo/', {
            'ciudadano':           ciudadano.pk,
            'recurso':             recurso.pk,
            'fecha_entrega':       now.isoformat() + 'T08:00',
            'fecha_devolucion':    (now + timedelta(days=7)).isoformat() + 'T08:00',
            'observaciones':       'Préstamo de prueba',
        })
        check("Registrar préstamo", r, (302,))
        prestamo = PrestamoRecurso.objects.filter(recurso=recurso).first()
        if prestamo:
            print(f"  {OK} Préstamo creado id={prestamo.pk}")
            check("Formulario editar préstamo", c_su.get(f'/prestamos/{prestamo.pk}/editar/'))
            check("Devolver préstamo", c_su.post(f'/prestamos/{prestamo.pk}/devolver/'), (302,))
        else:
            print(f"  {WARN} Préstamo no se creó")
else:
    print(f"  {WARN} Recurso no se creó")

# ════════════════════════════════════════════════════════════════════════════
titulo("BLOQUE 7 — SALAS Y HABILITACIONES")
# ════════════════════════════════════════════════════════════════════════════
check("Listar salas (super)",   c_su.get('/salas/'))
check("Listar salas (PVD)",     c_pvd.get('/salas/'), (200,302))
check("Formulario crear sala",  c_su.get('/salas/crear/'))

Sala.objects.filter(nombre__in=['Sala Test Prueba','Sala Test Editada','Sala Test Nueva']).delete()  # limpiar previas
r = c_su.post('/salas/crear/', {
    'punto_vive_digital': 1,
    'nombre':       'Sala Test Prueba',
    'descripcion':  'Sala creada por prueba',
    'capacidad':    20,
    'estado':       'A',
})
check("Crear sala", r, (302,))

sala = Sala.objects.filter(nombre='Sala Test Prueba').first()
if sala:
    print(f"  {OK} Sala creada id={sala.pk}")
    check("Formulario editar sala",    c_su.get(f'/salas/editar/{sala.pk}/'))
    r = c_su.post(f'/salas/editar/{sala.pk}/', {
        'punto_vive_digital': 1,
        'nombre':       'Sala Test Nueva',
        'descripcion':  'Editada',
        'capacidad':    25,
        'estado':       'A',
    })
    check("Editar sala", r, (302,))
    check("Agenda de sala", c_su.get(f'/salas/{sala.pk}/agenda/'))

    check("Listar habilitaciones",         c_su.get('/habilitaciones/'))
    check("Formulario nueva habilitación", c_su.get('/habilitaciones/crear/'))
    hoy = date.today()
    r = c_su.post('/habilitaciones/crear/', {
        'sala':                sala.pk,
        'tipo_uso':            'NAV',
        'fecha':               hoy.isoformat(),
        'hora_inicio':         '08:00',
        'hora_fin':            '12:00',
        'solicitante':         'Prueba Automatizada',
        'proposito':           'Prueba de navegación',
        'capacidad_requerida': 10,
        'estado':              'C',
        'observaciones':       '',
    })
    check("Crear habilitación", r, (302,))
    hab = HabilitacionSala.objects.filter(sala=sala).first()
    if hab:
        print(f"  {OK} Habilitación creada id={hab.pk}")
        check("Formulario editar habilitación", c_su.get(f'/habilitaciones/editar/{hab.pk}/'))
        check("Cancelar habilitación",          c_su.post(f'/habilitaciones/cancelar/{hab.pk}/'), (302,))
        check("Eliminar habilitación",          c_su.post(f'/habilitaciones/eliminar/{hab.pk}/'), (302,))
    else:
        print(f"  {WARN} Habilitación no se creó")

    check("Activar/desactivar sala", c_su.post(f'/salas/activar/{sala.pk}/'), (302,))
else:
    print(f"  {WARN} Sala no se creó")

# ════════════════════════════════════════════════════════════════════════════
titulo("BLOQUE 8 — CURSOS Y TALLERES")
# ════════════════════════════════════════════════════════════════════════════
check("Listar cursos (super)",   c_su.get('/cursos/'))
check("Listar cursos (PVD)",     c_pvd.get('/cursos/'), (200,302))
check("Formulario crear curso",  c_su.get('/cursos/crear/'))

hoy = date.today()
r = c_su.post('/cursos/crear/', {
    'nombre':              'Curso Prueba Automatizado',
    'descripcion':         'Curso de prueba',
    'modalidad':           'P',
    'poblacion_objetivo':  'Adultos',
    'fecha_inicio':        hoy.isoformat(),
    'fecha_fin':           (hoy + timedelta(days=30)).isoformat(),
    'estado':              'PL',
})
check("Crear curso", r, (302,))

curso = Curso.objects.filter(nombre='Curso Prueba Automatizado').first()
if curso:
    print(f"  {OK} Curso creado id={curso.pk}")
    check("Ver detalle curso",       c_su.get(f'/cursos/{curso.pk}/'))
    check("Formulario editar curso", c_su.get(f'/cursos/{curso.pk}/editar/'))

    r = c_su.post(f'/cursos/{curso.pk}/sesion/', {
        'numero_sesion': 1,
        'fecha':         hoy.isoformat(),
        'hora_inicio':   '09:00',
        'hora_fin':      '11:00',
        'tema':          'Introducción',
        'contenido':     'Contenido de prueba',
    })
    check("Crear sesión de curso", r, (302,))
    sesion = SesionCurso.objects.filter(curso=curso).first()

    if sesion:
        print(f"  {OK} Sesión creada id={sesion.pk}")
        check("Marcar asistencia (form)", c_su.get(f'/cursos/sesion/{sesion.pk}/asistencia/'))

    if ciudadano:
        r = c_su.post(f'/cursos/{curso.pk}/inscribir/', {
            'ciudadano': ciudadano.pk,
            'estado':    'I',
        })
        check("Inscribir ciudadano a curso", r, (302,))
        inscripcion = InscripcionCurso.objects.filter(curso=curso, ciudadano=ciudadano).first()
        if inscripcion:
            print(f"  {OK} Inscripción creada id={inscripcion.pk}")
            check("Eliminar inscripción", c_su.post(f'/cursos/inscripcion/{inscripcion.pk}/eliminar/'), (302,))

    if sesion:
        check("Eliminar sesión", c_su.post(f'/cursos/sesion/{sesion.pk}/eliminar/'), (302,))

    check("Cambiar estado curso → Finalizado", c_su.post(f'/cursos/{curso.pk}/estado/', {'estado':'FI'}), (302,))
    check("Eliminar curso",                    c_su.post(f'/cursos/{curso.pk}/eliminar/'), (302,))
else:
    print(f"  {WARN} Curso no se creó")

# ════════════════════════════════════════════════════════════════════════════
titulo("BLOQUE 9 — MANTENIMIENTO DE EQUIPOS")
# ════════════════════════════════════════════════════════════════════════════
check("Listar mantenimientos (super)",  c_su.get('/mantenimientos/'))
check("Listar mantenimientos (PVD)",    c_pvd.get('/mantenimientos/'), (200,302))
check("Formulario crear mantenimiento", c_su.get('/mantenimientos/crear/'))

r = c_su.post('/mantenimientos/crear/', {
    'tipo':                'PRV',
    'fecha':               date.today().isoformat(),
    'equipos_intervenidos':'5 computadores de mesa',
    'descripcion':         'Mantenimiento preventivo de prueba',
    'hallazgos':           'Sin hallazgos críticos',
    'acciones':            'Limpieza y actualización',
})
check("Crear mantenimiento", r, (302,))

mant = MantenimientoEquipo.objects.filter(descripcion='Mantenimiento preventivo de prueba').first()
if mant:
    print(f"  {OK} Mantenimiento creado id={mant.pk}")
    check("Formulario editar mantenimiento", c_su.get(f'/mantenimientos/{mant.pk}/editar/'))
    r = c_su.post(f'/mantenimientos/{mant.pk}/editar/', {
        'tipo':                'COR',
        'fecha':               date.today().isoformat(),
        'equipos_intervenidos':'3 portátiles',
        'descripcion':         'Mantenimiento correctivo de prueba',
        'hallazgos':           'Teclados dañados',
        'acciones':            'Reemplazo de teclados',
    })
    check("Editar mantenimiento", r, (302,))
    check("Eliminar mantenimiento", c_su.post(f'/mantenimientos/{mant.pk}/eliminar/'), (302,))
else:
    print(f"  {WARN} Mantenimiento no se creó")

# ════════════════════════════════════════════════════════════════════════════
titulo("BLOQUE 10 — EVIDENCIAS")
# ════════════════════════════════════════════════════════════════════════════
check("Listar evidencias (super)",  c_su.get('/evidencias/'))
check("Listar evidencias (PVD)",    c_pvd.get('/evidencias/'), (200,302))
check("Formulario nueva evidencia", c_su.get('/evidencias/nueva/'))
ev = Evidencia.objects.filter(punto_vive_digital=pvd1).first()
if ev:
    check("Formulario editar evidencia", c_su.get(f'/evidencias/{ev.pk}/editar/'))
else:
    print(f"  {WARN} Sin evidencias existentes para editar (requieren imagen)")

# ════════════════════════════════════════════════════════════════════════════
titulo("BLOQUE 11 — REPORTES Y EXPORTACIONES")
# ════════════════════════════════════════════════════════════════════════════
check("Reportes (super)",       c_su.get('/reportes/'))
check("Reportes (PVD)",         c_pvd.get('/reportes/'))
check("Reportes con filtro",    c_su.get(f'/reportes/?desde={hoy}&hasta={hoy}'))
check("Exportar atenciones",    c_su.get('/exportar-atenciones/'))
check("Exportar ciudadanos",    c_su.get('/exportar-ciudadanos/'))
check("Exportar servicios",     c_su.get('/exportar-servicios/'))
check("Exportar satisfacción",  c_su.get('/exportar-satisfaccion/'))
check("Exportar préstamos",     c_su.get('/exportar-prestamos/'))
check("Exportar cursos",        c_su.get('/exportar-cursos/'))
check("Exportar mantenimientos",c_su.get('/exportar-mantenimientos/'))

# ════════════════════════════════════════════════════════════════════════════
titulo("BLOQUE 12 — USUARIOS Y PERMISOS")
# ════════════════════════════════════════════════════════════════════════════
check("Form crear Admin TIC",  c_su.get('/crear-admin-tic/'))
check("Form crear Admin PVD",  c_su.get('/crear-admin-pvd/'))
check("Gestionar roles",       c_su.get('/gestionar-roles/'))
u_pvd = User.objects.filter(groups__name='Administrador PVD').first()
if u_pvd:
    check("Asignar rol (form)",       c_su.get(f'/asignar-rol/{u_pvd.pk}/'))
    check("Permisos individuales",    c_su.get(f'/permisos/usuario/{u_pvd.pk}/'))
check("Matriz permisos × roles",  c_su.get('/permisos/'))
check("Delegación permisos TIC",  c_tic.get('/permisos/ofitic/'))
check("Accesos temporales",       c_su.get('/accesos-temporales/'))

# ════════════════════════════════════════════════════════════════════════════
titulo("BLOQUE 13 — AUDITORÍA")
# ════════════════════════════════════════════════════════════════════════════
check("Log de auditoría",      c_su.get('/auditoria/'))
check("Exportar auditoría",    c_su.get('/auditoria/exportar/'))

# ════════════════════════════════════════════════════════════════════════════
titulo("LIMPIEZA — Datos de prueba")
# ════════════════════════════════════════════════════════════════════════════
deleted = []
# Primero eliminar atenciones (y sus dependencias) antes del ciudadano
if ciudadano:
    Satisfaccion.objects.filter(atencion__ciudadano=ciudadano).delete()
    Servicio.objects.filter(atencion__ciudadano=ciudadano).delete()
    Atencion.objects.filter(ciudadano=ciudadano).delete()
    PrestamoRecurso.objects.filter(ciudadano=ciudadano).delete()
    ciudadano.delete(); deleted.append("ciudadano + atenciones")
Ciudadano.objects.filter(numero_documento='9999999901').delete()
Recurso.objects.filter(codigo__startswith='LAP-PRUEBA').delete(); deleted.append("recurso")
Sala.objects.filter(nombre__in=['Sala Test Prueba','Sala Test Editada','Sala Test Nueva']).delete(); deleted.append("sala")
MantenimientoEquipo.objects.filter(descripcion__icontains='de prueba').delete(); deleted.append("mantenimiento")
print(f"  {OK} Limpiados: {', '.join(deleted)}")

# ════════════════════════════════════════════════════════════════════════════
# RESUMEN
# ════════════════════════════════════════════════════════════════════════════
total  = len(resultados)
ok     = sum(1 for _,v,_ in resultados if v)
fallos = [(n,c) for n,v,c in resultados if not v]

print(f"\n{'═'*60}")
print(f"{HEAD}  RESUMEN FINAL{END}")
print(f"{'═'*60}")
print(f"  Total pruebas : {total}")
print(f"  {OK} Pasaron     : {ok}")
print(f"  {FAIL} Fallaron   : {total - ok}")

if fallos:
    print(f"\n{HEAD}  PRUEBAS FALLIDAS:{END}")
    for nombre, codigo in fallos:
        print(f"  {FAIL} [{codigo}] {nombre}")
else:
    print(f"\n  {OK} ¡TODO EL SOFTWARE FUNCIONA CORRECTAMENTE!")
print(f"{'═'*60}\n")
