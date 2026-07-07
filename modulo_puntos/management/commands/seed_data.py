"""
Comando: python manage.py seed_data
Crea datos de prueba completos para todas las funciones del sistema PVD.
"""
from datetime import date, time, timedelta, datetime
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from django.utils import timezone

from modulo_puntos.models import (
    PuntoViveDigital, UserProfile,
    Ciudadano, Recurso, PrestamoRecurso,
    Atencion, Servicio, Satisfaccion,
    Sala, HabilitacionSala,
    Curso, SesionCurso, InscripcionCurso, AsistenciaSesion,
    MantenimientoEquipo,
    PermisoDefinicion, PermisoRol,
)


class Command(BaseCommand):
    help = 'Crea datos de prueba para todas las funciones del sistema'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                'Este comando crea usuarios con contraseñas de prueba conocidas '
                '(admin/admin, Tic2026!, Pvd2026!). Sólo puede ejecutarse con '
                'DJANGO_DEBUG=True. Abortado.'
            )

        self.stdout.write('\n================================================')
        self.stdout.write(  '         SEMILLA DE DATOS DE PRUEBA             ')
        self.stdout.write(  '================================================\n')

        admin = User.objects.filter(username='admin').first()
        if not admin:
            admin = User.objects.create_superuser('admin', '', 'admin')
            self.stdout.write('  [OK] Superusuario admin creado')

        # ── 1. GRUPOS ──────────────────────────────────────────────────────────
        grupo_tic, _ = Group.objects.get_or_create(name='Administrador TIC')
        grupo_pvd, _ = Group.objects.get_or_create(name='Administrador PVD')
        self._ok('Grupos de roles')

        # ── 2. PERMISOS ────────────────────────────────────────────────────────
        permisos_def = [
            ('ciudadanos.ver',       'Ver Ciudadanos',          'Ciudadanos',  True),
            ('ciudadanos.registrar', 'Registrar Ciudadano',     'Ciudadanos',  True),
            ('atenciones.ver',       'Ver Atenciones',          'Atenciones',  True),
            ('atenciones.registrar', 'Registrar Atención',      'Atenciones',  True),
            ('servicios.registrar',  'Registrar Servicio',      'Servicios',   True),
            ('satisfaccion.registrar','Registrar Satisfacción', 'Calidad',     True),
            ('recursos.ver',         'Ver Recursos',            'Recursos',    True),
            ('recursos.registrar',   'Registrar Recurso',       'Recursos',    True),
            ('prestamos.registrar',  'Registrar Préstamo',      'Préstamos',   True),
            ('salas.ver',            'Ver Salas',               'Salas',       True),
            ('salas.gestionar',      'Gestionar Salas',         'Salas',       False),
            ('habilitaciones.ver',   'Ver Habilitaciones',      'Salas',       True),
            ('cursos.ver',           'Ver Cursos',              'Cursos',      True),
            ('cursos.gestionar',     'Gestionar Cursos',        'Cursos',      True),
            ('mantenimiento.ver',    'Ver Mantenimientos',      'Mantenimiento',True),
            ('mantenimiento.registrar','Registrar Mantenimiento','Mantenimiento',False),
            ('reportes.ver',         'Ver Reportes',            'Reportes',    False),
            ('infraestructura.eliminar_pvd','Eliminar PVD',     'Infraestructura',False),
        ]
        for codigo, nombre, cat, delegable in permisos_def:
            p, _ = PermisoDefinicion.objects.get_or_create(
                codigo=codigo,
                defaults={'nombre': nombre, 'categoria': cat,
                          'delegable_por_ofitic': delegable, 'activo': True}
            )
            # Asignar al rol admin_tic
            PermisoRol.objects.get_or_create(rol='admin_tic', permiso=p,
                                              defaults={'otorgado_por': admin})
            # Permisos operativos también al admin_pvd
            if delegable:
                PermisoRol.objects.get_or_create(rol='admin_pvd', permiso=p,
                                                  defaults={'otorgado_por': admin})
        self._ok('Permisos del sistema')

        # ── 3. USUARIOS ────────────────────────────────────────────────────────
        tic = self._usuario('javier.restrepo', 'Javier', 'Restrepo', 'Tic2026!', grupo_tic)
        pvd1_user = self._usuario('maria.cardona', 'María', 'Cardona', 'Pvd2026!', grupo_pvd)
        pvd2_user = self._usuario('carlos.jimenez', 'Carlos', 'Jiménez', 'Pvd2026!', grupo_pvd)
        self._ok('Usuarios (1 Admin TIC + 2 Admin PVD)')

        # ── 4. PVDs ────────────────────────────────────────────────────────────
        pvd1 = self._pvd('PVD Centro', 'Calle 5 # 4 - 32', 'Centro', pvd1_user)
        pvd2 = self._pvd('PVD La María', 'Carrera 8 # 12 - 15', 'La María', pvd2_user)
        UserProfile.objects.update_or_create(usuario=pvd1_user,
            defaults={'punto_asignado': pvd1, 'rol': 'admin_pvd'})
        UserProfile.objects.update_or_create(usuario=pvd2_user,
            defaults={'punto_asignado': pvd2, 'rol': 'admin_pvd'})
        self._ok('PVDs (PVD Centro + PVD La María)')

        # ── 5. CIUDADANOS ──────────────────────────────────────────────────────
        ciudadanos_data = [
            # pvd, doc, p_nom, s_nom, p_ape, s_ape, nac, gen, etnia, edu, ocu, est, disc
            (pvd1,'1094820011','Luisa','Fernanda','Martínez','Ospina', '1992-03-15','F','Ninguna','Universitaria','Empleado',3,False),
            (pvd1,'1094820012','Andrés','Felipe','García','Ríos',     '1988-07-22','M','Ninguna','Bachillerato','Independiente',2,False),
            (pvd1,'1094820013','Valentina','','Rojas','Herrera',      '2000-11-05','F','Ninguna','Técnico','Estudiante',1,False),
            (pvd1,'1094820014','Miguel','Ángel','Salcedo','',         '1975-04-18','M','Afrocolombiano','Primaria','Agricultor',1,True),
            (pvd1,'1094820015','Sandra','Milena','López','Castaño',   '1983-09-30','F','Ninguna','Universitaria','Empleado',3,False),
            (pvd1,'1094820016','Johan','David','Díaz','Morales',      '1998-06-12','M','Ninguna','Bachillerato','Desempleado',2,False),
            (pvd1,'1094820017','Ana','Lucía','Torres','Vergara',      '1960-02-28','F','Indígena','Primaria','Pensionado',1,True),
            (pvd1,'1094820018','Sebastián','','Cano','Pedraza',       '2005-08-19','M','Ninguna','Bachillerato','Estudiante',2,False),
            (pvd2,'1094820019','Paola','Andrea','Ríos','Acosta',      '1991-12-07','F','Ninguna','Universitaria','Empleado',3,False),
            (pvd2,'1094820020','Julián','Esteban','Gómez','Hurtado',  '1986-05-14','M','Ninguna','Técnico','Independiente',2,False),
            (pvd2,'1094820021','Marcela','','Suárez','',              '1978-10-23','F','Ninguna','Bachillerato','Empleado',2,False),
            (pvd2,'1094820022','Tomás','','Vargas','Mejía',           '2003-01-31','M','Afrocolombiano','Bachillerato','Estudiante',1,False),
            (pvd2,'1094820023','Carolina','Isabel','Muñoz','Calderón','1995-07-09','F','Ninguna','Universitaria','Empleado',3,False),
            (pvd2,'1094820024','Ricardo','Alfonso','Patiño','Soto',   '1970-03-26','M','Ninguna','Técnico','Pensionado',2,False),
            (pvd2,'1094820025','Daniela','','Agudelo','Arango',       '2001-04-17','F','Ninguna','Bachillerato','Estudiante',1,False),
        ]
        ciudadanos = []
        for row in ciudadanos_data:
            pvd, doc, pn, sn, pa, sa, nac, gen, etnia, edu, ocu, est, disc = row
            c, _ = Ciudadano.objects.get_or_create(
                numero_documento=doc,
                defaults=dict(
                    punto_vive_digital=pvd,
                    tipo_documento='CC',
                    primer_nombre=pn, segundo_nombre=sn,
                    primer_apellido=pa, segundo_apellido=sa,
                    fecha_nacimiento=date.fromisoformat(nac),
                    genero=gen, etnia=etnia,
                    nivel_educativo=edu, ocupacion=ocu,
                    estrato=est, estado='A',
                    tiene_discapacidad=disc,
                    descripcion_discapacidad='Visual' if disc else '',
                    direccion='Calle 5 # 4 - 10',
                    barrio='Centro', correo='',
                    telefono='3001234567',
                )
            )
            ciudadanos.append(c)
        self._ok(f'{len(ciudadanos)} ciudadanos')

        # ── 6. RECURSOS ────────────────────────────────────────────────────────
        recursos_data = [
            (pvd1,'Portátil','LAP-C01'),(pvd1,'Portátil','LAP-C02'),
            (pvd1,'Portátil','LAP-C03'),(pvd1,'Computador de escritorio','PC-C01'),
            (pvd1,'Impresora','IMP-C01'),(pvd1,'Tableta','TAB-C01'),
            (pvd1,'Proyector','PRY-C01'),(pvd1,'Escáner','ESC-C01'),
            (pvd2,'Portátil','LAP-M01'),(pvd2,'Portátil','LAP-M02'),
            (pvd2,'Computador de escritorio','PC-M01'),(pvd2,'Impresora','IMP-M01'),
            (pvd2,'Tableta','TAB-M01'),(pvd2,'Cámara web','CAM-M01'),
        ]
        recursos = []
        for pvd, tipo, codigo in recursos_data:
            r, _ = Recurso.objects.get_or_create(
                codigo=codigo,
                defaults={'punto_vive_digital': pvd, 'tipo': tipo, 'estado': 'A'}
            )
            recursos.append(r)
        self._ok(f'{len(recursos)} recursos')

        # ── 7. PRÉSTAMOS ───────────────────────────────────────────────────────
        hoy = date.today()
        prestamos_data = [
            (recursos[0], hoy - timedelta(days=5),  hoy - timedelta(days=2),  'Préstamo para trámite en línea'),
            (recursos[1], hoy - timedelta(days=3),  hoy - timedelta(days=1),  'Uso en capacitación básica'),
            (recursos[2], hoy - timedelta(days=1),  None,                     'Préstamo activo — pendiente devolución'),
            (recursos[3], hoy - timedelta(days=10), hoy - timedelta(days=7),  'Préstamo para examen SENA'),
            (recursos[8], hoy - timedelta(days=4),  hoy - timedelta(days=2),  'Uso en taller digital'),
            (recursos[9], hoy - timedelta(days=2),  None,                     'Préstamo activo'),
        ]
        prestamos = []
        for rec, fent, fdev, obs in prestamos_data:
            p = PrestamoRecurso.objects.create(
                recurso=rec,
                fecha_entrega=timezone.make_aware(datetime.combine(fent, time(9, 0))),
                fecha_devolucion=timezone.make_aware(datetime.combine(fdev, time(17, 0))) if fdev else None,
                observaciones=obs,
            )
            prestamos.append(p)
        self._ok(f'{len(prestamos)} préstamos')

        # ── 8. ATENCIONES ──────────────────────────────────────────────────────
        # 10 para pvd1, 10 para pvd2, estados variados
        estados = ['F','F','F','F','F','P','P','C','F','F']
        atenciones = []
        for i, ciu in enumerate(ciudadanos[:8]):
            a = Atencion.objects.create(
                punto_vive_digital=pvd1,
                ciudadano=ciu,
                operador=pvd1_user,
                fecha=hoy - timedelta(days=i*3),
                hora_inicio=time(8 + i % 4, 0),
                hora_fin=time(9 + i % 4, 30),
                estado=estados[i],
                observaciones=f'Atención de prueba #{i+1} — PVD Centro',
            )
            atenciones.append(a)
        for i, ciu in enumerate(ciudadanos[8:]):
            a = Atencion.objects.create(
                punto_vive_digital=pvd2,
                ciudadano=ciu,
                operador=pvd2_user,
                fecha=hoy - timedelta(days=i*2),
                hora_inicio=time(8 + i % 3, 0),
                hora_fin=time(9 + i % 3, 0),
                estado=estados[i],
                observaciones=f'Atención de prueba #{i+1} — PVD La María',
            )
            atenciones.append(a)
        self._ok(f'{len(atenciones)} atenciones')

        # ── 9. SERVICIOS ───────────────────────────────────────────────────────
        servicios_info = [
            ('Trámite de cédula de ciudadanía','Asesoría y apoyo para solicitud de cédula','N',None),
            ('Gestión de correo electrónico','Creación y configuración de cuenta de correo','N',None),
            ('Acceso a internet','Uso de internet para consultas personales','S',recursos[0]),
            ('Inscripción SENA virtual','Apoyo para inscripción a cursos del SENA','S',recursos[1]),
            ('Impresión de documentos','Impresión de hojas de vida y documentos','S',recursos[4]),
            ('Trámite de pensión','Radicación de documentos para pensión','N',None),
            ('Uso de portátil','Préstamo de equipo para trabajo personal','S',recursos[8]),
            ('Consulta de certificados','Descarga de certificados laborales','N',None),
        ]
        servicios = []
        for i, (nombre, desc, req, rec) in enumerate(servicios_info):
            at = atenciones[i] if i < len(atenciones) else atenciones[0]
            s = Servicio.objects.create(
                atencion=at,
                nombre=nombre,
                tipo=nombre[:64],
                descripcion=desc,
                requiere_equipo=req,
                recurso=rec,
                estado='A',
            )
            servicios.append(s)
        self._ok(f'{len(servicios)} servicios')

        # ── 10. SATISFACCIÓN ───────────────────────────────────────────────────
        comentarios = [
            'Excelente atención, muy amable el personal.',
            'Buena atención, me resolvieron la duda.',
            'Regular, tuve que esperar mucho tiempo.',
            'Muy buena atención, volveré.',
            'El personal fue muy atento y eficiente.',
            'Podría mejorar la velocidad del servicio.',
            'Estoy satisfecho con la atención recibida.',
            'Todo estuvo perfecto, muchas gracias.',
        ]
        satisfacciones = []
        respuestas_encuesta = [
            ('E', 'E', 'E', 'E', 'E'),
            ('E', 'B', 'E', 'B', 'E'),
            ('B', 'B', 'B', 'B', 'M'),
            ('E', 'B', 'E', 'B', 'E'),
            ('E', 'E', 'E', 'E', 'E'),
            ('B', 'B', 'B', 'B', 'M'),
            ('E', 'B', 'E', 'B', 'E'),
            ('E', 'E', 'E', 'E', 'E'),
        ]
        for i, at in enumerate(atenciones[:8]):
            if at.estado == 'F':
                r = respuestas_encuesta[i % len(respuestas_encuesta)]
                s = Satisfaccion.objects.create(
                    atencion=at,
                    tiempo_espera=r[0],
                    atencion_servidor=r[1],
                    satisfaccion_servicio=r[2],
                    informacion_recibida=r[3],
                    comodidad_instalaciones=r[4],
                    comentario=comentarios[i % len(comentarios)],
                    fecha=timezone.now() - timedelta(days=i),
                )
                satisfacciones.append(s)
        self._ok(f'{len(satisfacciones)} encuestas de satisfacción')

        # ── 11. SALAS ──────────────────────────────────────────────────────────
        salas_data = [
            (pvd1, 'Sala de Navegación A', 'Sala principal con 10 equipos de cómputo', 10),
            (pvd1, 'Sala de Capacitación', 'Sala para talleres y formación grupal', 25),
            (pvd2, 'Sala de Navegación B', 'Sala de acceso a internet para ciudadanos', 8),
            (pvd2, 'Sala Multiusos',       'Sala para reuniones y eventos', 30),
        ]
        salas = []
        for pvd, nombre, desc, cap in salas_data:
            s, _ = Sala.objects.get_or_create(
                punto_vive_digital=pvd, nombre=nombre,
                defaults={'descripcion': desc, 'capacidad': cap, 'estado': 'A'}
            )
            salas.append(s)
        self._ok(f'{len(salas)} salas')

        # ── 12. HABILITACIONES ─────────────────────────────────────────────────
        hab_data = [
            (salas[0],'NAV',hoy - timedelta(days=2),time(8,0), time(12,0),'Comunidad barrio Centro','Navegación libre ciudadanos',15,'F'),
            (salas[1],'CAP',hoy - timedelta(days=1),time(14,0),time(17,0),'Grupo adultos mayores','Taller básico de Word',20,'C'),
            (salas[0],'NAV',hoy,                     time(8,0), time(12,0),'Público general','Acceso internet mañana',10,'E'),
            (salas[1],'CONF',hoy + timedelta(days=1),time(9,0), time(11,0),'Junta de acción comunal','Reunión mensual JAC',15,'P'),
            (salas[2],'NAV',hoy - timedelta(days=3),time(8,0), time(12,0),'Comunidad La María','Navegación libre',8,'F'),
            (salas[3],'CAP',hoy,                     time(13,0),time(17,0),'Jóvenes 15-25 años','Taller de redes sociales',20,'E'),
        ]
        habilitaciones = []
        for sala, tipo, fecha, hi, hf, sol, prop, cap, est in hab_data:
            h = HabilitacionSala.objects.create(
                sala=sala, tipo_uso=tipo, fecha=fecha,
                hora_inicio=hi, hora_fin=hf,
                solicitante=sol, proposito=prop,
                capacidad_requerida=cap, estado=est,
                registrado_por=admin,
            )
            habilitaciones.append(h)
        self._ok(f'{len(habilitaciones)} habilitaciones de sala')

        # ── 13. CURSOS ─────────────────────────────────────────────────────────
        cursos_data = [
            (pvd1, 'Ofimática Básica',
             'Curso de Word, Excel y PowerPoint para principiantes.',
             'P', 'Adultos mayores y personas sin experiencia digital',
             hoy - timedelta(days=20), hoy + timedelta(days=10), 'AC'),
            (pvd2, 'Ciudadanía Digital',
             'Uso seguro de internet, redes sociales y trámites en línea.',
             'P', 'Jóvenes y adultos',
             hoy - timedelta(days=5), hoy + timedelta(days=25), 'AC'),
        ]
        cursos = []
        for pvd, nombre, desc, mod, pob, fi, ff, est in cursos_data:
            c, _ = Curso.objects.get_or_create(
                nombre=nombre, punto_vive_digital=pvd,
                defaults={
                    'descripcion': desc, 'modalidad': mod,
                    'poblacion_objetivo': pob,
                    'fecha_inicio': fi, 'fecha_fin': ff,
                    'estado': est, 'registrado_por': admin,
                }
            )
            cursos.append(c)
        self._ok(f'{len(cursos)} cursos')

        # ── 14. SESIONES ───────────────────────────────────────────────────────
        sesiones_c1 = [
            (1, hoy - timedelta(days=18), time(8,0),  time(10,0),  'Introducción a la ofimática',    'Conceptos básicos de computador y teclado'),
            (2, hoy - timedelta(days=15), time(8,0),  time(10,0),  'Microsoft Word básico',          'Crear y guardar documentos de texto'),
            (3, hoy - timedelta(days=10), time(8,0),  time(10,0),  'Microsoft Excel básico',         'Hojas de cálculo y fórmulas simples'),
            (4, hoy - timedelta(days=5),  time(8,0),  time(10,0),  'PowerPoint y presentaciones',    'Crear diapositivas básicas'),
        ]
        sesiones_c2 = [
            (1, hoy - timedelta(days=4), time(14,0), time(16,0),  'Internet seguro',                'Navegación segura y contraseñas'),
            (2, hoy - timedelta(days=2), time(14,0), time(16,0),  'Redes sociales responsables',    'Privacidad y uso responsable de redes'),
            (3, hoy + timedelta(days=2), time(14,0), time(16,0),  'Trámites en línea',              'SENA, Colpensiones, DIAN online'),
            (4, hoy + timedelta(days=5), time(14,0), time(16,0),  'Correo electrónico y WhatsApp',  'Comunicación digital efectiva'),
        ]
        todas_sesiones = []
        for num, fecha, hi, hf, tema, cont in sesiones_c1:
            s, _ = SesionCurso.objects.get_or_create(
                curso=cursos[0], numero_sesion=num,
                defaults={'fecha': fecha, 'hora_inicio': hi, 'hora_fin': hf,
                          'tema': tema, 'contenido': cont}
            )
            todas_sesiones.append(s)
        for num, fecha, hi, hf, tema, cont in sesiones_c2:
            s, _ = SesionCurso.objects.get_or_create(
                curso=cursos[1], numero_sesion=num,
                defaults={'fecha': fecha, 'hora_inicio': hi, 'hora_fin': hf,
                          'tema': tema, 'contenido': cont}
            )
            todas_sesiones.append(s)
        self._ok(f'{len(todas_sesiones)} sesiones de curso')

        # ── 15. INSCRIPCIONES ──────────────────────────────────────────────────
        inscritos_c1 = ciudadanos[:6]   # primeros 6 ciudadanos al curso 1
        inscritos_c2 = ciudadanos[8:13] # ciudadanos del pvd2 al curso 2
        inscripciones = []
        for ciu in inscritos_c1:
            ins, _ = InscripcionCurso.objects.get_or_create(
                curso=cursos[0], ciudadano=ciu,
                defaults={'estado': 'I', 'registrado_por': admin}
            )
            inscripciones.append(ins)
        for ciu in inscritos_c2:
            ins, _ = InscripcionCurso.objects.get_or_create(
                curso=cursos[1], ciudadano=ciu,
                defaults={'estado': 'I', 'registrado_por': admin}
            )
            inscripciones.append(ins)
        self._ok(f'{len(inscripciones)} inscripciones a cursos')

        # ── 16. ASISTENCIAS ────────────────────────────────────────────────────
        asistencias = 0
        sesiones_pasadas_c1 = [s for s in todas_sesiones[:4] if s.fecha <= hoy]
        for sesion in sesiones_pasadas_c1:
            for i, ciu in enumerate(inscritos_c1):
                AsistenciaSesion.objects.get_or_create(
                    sesion=sesion, ciudadano=ciu,
                    defaults={'asistio': i % 5 != 0}  # 80% de asistencia
                )
                asistencias += 1
        sesiones_pasadas_c2 = [s for s in todas_sesiones[4:] if s.fecha <= hoy]
        for sesion in sesiones_pasadas_c2:
            for i, ciu in enumerate(inscritos_c2):
                AsistenciaSesion.objects.get_or_create(
                    sesion=sesion, ciudadano=ciu,
                    defaults={'asistio': i % 4 != 3}  # 75% asistencia
                )
                asistencias += 1
        self._ok(f'{asistencias} registros de asistencia')

        # ── 17. MANTENIMIENTOS ─────────────────────────────────────────────────
        mantenimientos_data = [
            (pvd1,'PRV', hoy - timedelta(days=30),
             '8 portátiles, 2 escritorios',
             'Limpieza de polvo, actualización de antivirus y revisión de teclados.',
             'Teclado dañado en LAP-C02',
             'Reemplazar teclado de LAP-C02 en el próximo mantenimiento.'),
            (pvd1,'COR', hoy - timedelta(days=10),
             'Impresora IMP-C01',
             'Revisión y reemplazo de cartucho de tinta negro.',
             'Cartucho agotado, rollos de papel con atasco.',
             'Programar revisión mensual de consumibles.'),
            (pvd2,'PRV', hoy - timedelta(days=20),
             '6 portátiles, 1 cámara web',
             'Mantenimiento preventivo semestral — limpieza general.',
             'Sin novedades mayores.',
             'Continuar con mantenimiento preventivo cada 6 meses.'),
            (pvd2,'COR', hoy - timedelta(days=3),
             'Portátil LAP-M01',
             'Reemplazo de batería defectuosa.',
             'Batería no cargaba. Se reemplazó.',
             'Solicitar garantía al proveedor.'),
        ]
        mantenimientos = []
        for pvd, tipo, fecha, equipos, desc, hall, acc in mantenimientos_data:
            m = MantenimientoEquipo.objects.create(
                punto_vive_digital=pvd, tipo=tipo, fecha=fecha,
                equipos_intervenidos=equipos, descripcion=desc,
                hallazgos=hall, acciones=acc,
                realizado_por=admin,
            )
            mantenimientos.append(m)
        self._ok(f'{len(mantenimientos)} mantenimientos de equipos')

        # ── RESUMEN ────────────────────────────────────────────────────────────
        self.stdout.write('\n' + '-' * 48)
        self.stdout.write(self.style.SUCCESS('  Datos de prueba creados exitosamente\n'))
        self.stdout.write('  Usuarios disponibles:')
        self.stdout.write('    admin / admin               -> Superusuario')
        self.stdout.write('    javier.restrepo / Tic2026!  -> Admin TIC')
        self.stdout.write('    maria.cardona   / Pvd2026!  -> Admin PVD (PVD Centro)')
        self.stdout.write('    carlos.jimenez  / Pvd2026!  -> Admin PVD (PVD La Maria)')
        self.stdout.write('-' * 48 + '\n')

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _ok(self, msg):
        self.stdout.write(f'  [OK] {msg}')

    def _usuario(self, username, first, last, pwd, grupo):
        u, created = User.objects.get_or_create(
            username=username,
            defaults={'first_name': first, 'last_name': last, 'email': ''}
        )
        if created:
            u.set_password(pwd)
            u.save()
        u.groups.add(grupo)
        return u

    def _pvd(self, nombre, direccion, barrio, admin_user):
        pvd, _ = PuntoViveDigital.objects.get_or_create(
            nombre=nombre,
            defaults={
                'direccion': direccion,
                'barrio': barrio,
                'estado': 'A',
                'admin_a_cargo': admin_user,
                'descripcion': f'Punto Vive Digital {nombre} — Bugalagrande, Valle del Cauca.',
            }
        )
        return pvd
