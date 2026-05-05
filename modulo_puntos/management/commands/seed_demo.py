"""
Comando para poblar la base de datos con datos de demostracion.
Uso: python manage.py seed_demo

Limpia los datos incorrectos creados anteriormente y recrea todo
con los PVDs correctos: PVD Edificio Rafael Arias y PVD Colegio Antonio Narino.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import connection
from django.utils import timezone
from datetime import date, time, timedelta, datetime

from modulo_puntos.models import (
    PuntoViveDigital, UserProfile, Ciudadano,
    Recurso, PrestamoRecurso, Atencion, Servicio, Satisfaccion,
    Sala, HabilitacionSala,
    Curso, SesionCurso, InscripcionCurso, AsistenciaSesion,
    MantenimientoEquipo,
)

HOY = date(2026, 5, 5)

# IDs de los PVDs reales que deben quedar
NOMBRE_PVD1 = 'PVD Edificio Rafael Arias'
NOMBRE_PVD2 = 'PVD Colegio Antonio Narino'


class Command(BaseCommand):
    help = 'Limpia datos de demo incorrectos y recarga con los PVDs correctos'

    def _ok(self, msg):
        self.stdout.write(self.style.SUCCESS(f'  [OK] {msg}'))

    def _skip(self, msg):
        self.stdout.write(f'  [--] {msg} (ya existe)')

    def _del(self, msg):
        self.stdout.write(self.style.WARNING(f'  [DEL] {msg}'))

    def _titulo(self, msg):
        self.stdout.write(self.style.HTTP_INFO(f'\n>>> {msg}'))

    # ------------------------------------------------------------------
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            '\n==========================================\n'
            '  SEED DEMO - Puntos Vive Digital\n'
            '==========================================\n'
        ))

        self._limpiar()
        grupos        = self._asegurar_grupos()
        superusuario  = self._obtener_superusuario()
        pvd1, pvd2    = self._asegurar_pvds()
        ofitic, julia, lady = self._crear_usuarios(grupos, pvd1, pvd2)
        self._asegurar_salas(pvd1, pvd2)
        ciudadanos    = self._crear_ciudadanos(pvd1, pvd2)
        recurso_real  = self._obtener_recurso_real(pvd1)
        prestamos     = self._crear_prestamos(recurso_real)
        atenciones    = self._crear_atenciones(pvd1, pvd2, ciudadanos, prestamos, julia, lady)
        self._crear_servicios(atenciones)
        self._crear_satisfaccion(atenciones)
        self._crear_habilitaciones(pvd1, pvd2, julia, lady)
        cursos        = self._crear_cursos(pvd1, pvd2, julia, lady)
        self._crear_sesiones_e_inscripciones(cursos, ciudadanos, julia)
        self._crear_mantenimientos(pvd1, pvd2, ofitic)

        self.stdout.write(self.style.SUCCESS(
            '\n==========================================\n'
            '  Datos de demo cargados exitosamente!\n'
            '==========================================\n'
        ))
        self._imprimir_resumen(superusuario, ofitic, julia, lady, pvd1, pvd2)

    # ------------------------------------------------------------------
    # LIMPIEZA
    # ------------------------------------------------------------------
    def _limpiar(self):
        self._titulo('Limpiando datos de demo anteriores')
        # Deshabilitar FK checks de MySQL para poder borrar en cualquier orden
        with connection.cursor() as cur:
            cur.execute('SET FOREIGN_KEY_CHECKS = 0;')

        # 1) Satisfaccion (referencia Atencion, sin PROTECT)
        n = Satisfaccion.objects.count()
        if n:
            Satisfaccion.objects.all().delete()
            self._del(f'{n} encuestas de satisfaccion eliminadas')

        # 2) Servicio (referencia Atencion, sin PROTECT)
        n = Servicio.objects.count()
        if n:
            Servicio.objects.all().delete()
            self._del(f'{n} servicios eliminados')

        # 3) Asistencia a sesiones
        n = AsistenciaSesion.objects.count()
        if n:
            AsistenciaSesion.objects.all().delete()
            self._del(f'{n} asistencias eliminadas')

        # 4) Inscripciones a cursos
        n = InscripcionCurso.objects.count()
        if n:
            InscripcionCurso.objects.all().delete()
            self._del(f'{n} inscripciones eliminadas')

        # 5) Atenciones (PROTECT sobre Ciudadano, borrar antes que ciudadanos)
        n = Atencion.objects.count()
        if n:
            Atencion.objects.all().delete()
            self._del(f'{n} atenciones eliminadas')

        # 6) Prestamos (PROTECT sobre Recurso, borrar antes que recursos)
        n = PrestamoRecurso.objects.count()
        if n:
            PrestamoRecurso.objects.all().delete()
            self._del(f'{n} prestamos eliminados')

        # 7) Ciudadanos
        n = Ciudadano.objects.count()
        if n:
            Ciudadano.objects.all().delete()
            self._del(f'{n} ciudadanos eliminados')

        # 8) Recursos falsos (dejar solo el real 626410)
        falsos = Recurso.objects.exclude(codigo='626410')
        n = falsos.count()
        if n:
            falsos.delete()
            self._del(f'{n} recursos hipoteticos eliminados')

        # 9) Habilitaciones de sala
        n = HabilitacionSala.objects.count()
        if n:
            HabilitacionSala.objects.all().delete()
            self._del(f'{n} habilitaciones de sala eliminadas')

        # 10) Mantenimientos
        n = MantenimientoEquipo.objects.count()
        if n:
            MantenimientoEquipo.objects.all().delete()
            self._del(f'{n} mantenimientos eliminados')

        # 11) Cursos y sesiones (CASCADE)
        n = Curso.objects.count()
        if n:
            Curso.objects.all().delete()
            self._del(f'{n} cursos eliminados (sesiones en cascada)')

        # 12) PVDs falsos (Centro y La Maria) si quedaron - CASCADE a salas
        for nombre in ['PVD Centro', 'PVD La Maria']:
            qs = PuntoViveDigital.objects.filter(nombre=nombre)
            if qs.exists():
                qs.delete()
                self._del(f'PVD "{nombre}" eliminado')

        # 13) Salas extra de los PVDs reales (dejar limpias para recrear)
        Sala.objects.filter(
            punto_vive_digital__nombre__in=[NOMBRE_PVD1, NOMBRE_PVD2]
        ).delete()

        # 14) Usuarios no-superuser (todos para recrear limpio)
        users_a_borrar = User.objects.filter(is_superuser=False)
        n = users_a_borrar.count()
        if n:
            users_a_borrar.delete()
            self._del(f'{n} usuarios no-superuser eliminados')

        # Re-habilitar FK checks de MySQL
        with connection.cursor() as cur:
            cur.execute('SET FOREIGN_KEY_CHECKS = 1;')

        self._ok('Limpieza completada')

    # ------------------------------------------------------------------
    # GRUPOS
    # ------------------------------------------------------------------
    def _asegurar_grupos(self):
        self._titulo('Grupos')
        g_tic, c = Group.objects.get_or_create(name='Administrador TIC')
        self._ok('Grupo Administrador TIC') if c else self._skip('Grupo Administrador TIC')
        g_pvd, c = Group.objects.get_or_create(name='Administrador PVD')
        self._ok('Grupo Administrador PVD') if c else self._skip('Grupo Administrador PVD')
        return {'tic': g_tic, 'pvd': g_pvd}

    # ------------------------------------------------------------------
    # SUPERUSUARIO
    # ------------------------------------------------------------------
    def _obtener_superusuario(self):
        self._titulo('Superusuario')
        su = User.objects.filter(is_superuser=True).first()
        if su:
            self._skip(f'Superusuario: {su.username}')
        UserProfile.objects.get_or_create(usuario=su, defaults={'rol': 'superadmin'})
        return su

    # ------------------------------------------------------------------
    # PVDs REALES
    # ------------------------------------------------------------------
    def _asegurar_pvds(self):
        self._titulo('Puntos Vive Digital')

        pvd1, c = PuntoViveDigital.objects.get_or_create(
            nombre=NOMBRE_PVD1,
            defaults={
                'direccion': 'Edificio Rafael Arias, Calle 5 No. 8-32, Bugalagrande',
                'barrio': 'Centro',
                'telefono': '3104521890',
                'correo': 'pvdrafaelarias@bugalagrande.gov.co',
                'estado': 'A',
                'descripcion': 'Punto Vive Digital ubicado en el Edificio Rafael Arias.',
            }
        )
        self._ok(NOMBRE_PVD1) if c else self._skip(NOMBRE_PVD1)

        pvd2, c = PuntoViveDigital.objects.get_or_create(
            nombre=NOMBRE_PVD2,
            defaults={
                'direccion': 'Colegio Antonio Narino, Carrera 3 No. 12-15, Bugalagrande',
                'barrio': 'La Maria',
                'telefono': '3156784321',
                'correo': 'pvdantonionarino@bugalagrande.gov.co',
                'estado': 'A',
                'descripcion': 'Punto Vive Digital ubicado en el Colegio Antonio Narino.',
            }
        )
        self._ok(NOMBRE_PVD2) if c else self._skip(NOMBRE_PVD2)

        return pvd1, pvd2

    # ------------------------------------------------------------------
    # USUARIOS
    # ------------------------------------------------------------------
    def _crear_usuarios(self, grupos, pvd1, pvd2):
        self._titulo('Usuarios del sistema')

        # Admin TIC: ofitic
        ofitic, c = User.objects.get_or_create(
            username='ofitic',
            defaults={
                'first_name': 'Luz Adriana',
                'last_name': 'Perez Castano',
                'email': 'ofitic@bugalagrande.gov.co',
                'is_staff': True,
            }
        )
        if c:
            ofitic.set_password('ofitic123')
            ofitic.save()
            self._ok('ofitic (Admin TIC)')
        else:
            self._skip('ofitic')
        ofitic.groups.add(grupos['tic'])
        UserProfile.objects.get_or_create(usuario=ofitic, defaults={'rol': 'admin_tic'})

        # Admin PVD: juliapvd -> PVD Rafael Arias
        julia, c = User.objects.get_or_create(
            username='juliapvd',
            defaults={
                'first_name': 'Julia',
                'last_name': 'Administradora PVD',
                'email': 'julia@pvdrafaelarias.gov.co',
            }
        )
        if c:
            julia.set_password('balon102@')
            julia.save()
            self._ok('juliapvd (Admin PVD - Rafael Arias)')
        else:
            self._skip('juliapvd')
        julia.groups.add(grupos['pvd'])
        profile_julia, _ = UserProfile.objects.get_or_create(
            usuario=julia,
            defaults={'rol': 'admin_pvd', 'punto_asignado': pvd1}
        )
        if profile_julia.punto_asignado != pvd1:
            profile_julia.punto_asignado = pvd1
            profile_julia.save()

        # Admin PVD: ladypvd -> PVD Antonio Narino
        lady, c = User.objects.get_or_create(
            username='ladypvd',
            defaults={
                'first_name': 'Lady',
                'last_name': 'Administradora PVD',
                'email': 'lady@pvdantonionarino.gov.co',
            }
        )
        if c:
            lady.set_password('balon102@')
            lady.save()
            self._ok('ladypvd (Admin PVD - Antonio Narino)')
        else:
            self._skip('ladypvd')
        lady.groups.add(grupos['pvd'])
        profile_lady, _ = UserProfile.objects.get_or_create(
            usuario=lady,
            defaults={'rol': 'admin_pvd', 'punto_asignado': pvd2}
        )
        if profile_lady.punto_asignado != pvd2:
            profile_lady.punto_asignado = pvd2
            profile_lady.save()

        # Actualizar admin_a_cargo en los PVDs
        pvd1.admin_a_cargo = julia
        pvd1.save()
        pvd2.admin_a_cargo = lady
        pvd2.save()

        return ofitic, julia, lady

    # ------------------------------------------------------------------
    # SALAS (2 por PVD)
    # ------------------------------------------------------------------
    def _asegurar_salas(self, pvd1, pvd2):
        self._titulo('Salas (2 por PVD)')
        salas_data = [
            ('Sala Principal',       'Sala de atencion y navegacion libre con equipos de computo.', 12),
            ('Sala de Capacitacion', 'Espacio para talleres y formacion digital ciudadana.', 20),
        ]
        for pvd in [pvd1, pvd2]:
            # Eliminar una tercera sala si quedara de antes
            salas_extra = Sala.objects.filter(
                punto_vive_digital=pvd
            ).exclude(nombre__in=['Sala Principal', 'Sala de Capacitacion'])
            if salas_extra.exists():
                salas_extra.delete()
                self._del(f'Salas extra de {pvd.nombre} eliminadas')

            for nombre, desc, cap in salas_data:
                sala, c = Sala.objects.get_or_create(
                    punto_vive_digital=pvd,
                    nombre=nombre,
                    defaults={'descripcion': desc, 'capacidad': cap, 'estado': 'A'}
                )
                self._ok(f'{pvd.nombre} -> {nombre}') if c else self._skip(f'{pvd.nombre} -> {nombre}')

    # ------------------------------------------------------------------
    # CIUDADANOS
    # ------------------------------------------------------------------
    def _crear_ciudadanos(self, pvd1, pvd2):
        self._titulo('Ciudadanos')
        datos = [
            # (tipo, num_doc, p_nombre, s_nombre, p_apellido, s_apellido,
            #  fecha_nac, genero, etnia, nivel_edu, ocupacion, estrato,
            #  discap, barrio, pvd, correo, telefono)
            ('CC','10943101','Ana','Lucia','Prado','Morales',
             date(1995,4,30),'F','Ninguna','Tecnico/Tecnologo','Estudiante',1,
             False,'Centro',pvd1,'ana.prado@gmail.com','3101234567'),

            ('CC','10943102','Juan','Pablo','Castano','Vargas',
             date(1978,11,5),'M','Ninguna','Bachillerato','Agricultor',2,
             False,'Centro',pvd1,'','3112345678'),

            ('CC','10943103','Maria','Fernanda','Guerrero','Ospina',
             date(1992,7,22),'F','Ninguna','Universitario','Empleada',2,
             False,'Centro',pvd1,'mfguerrero@gmail.com','3123456789'),

            ('CC','10943104','Pedro','Antonio','Quintero','Garcia',
             date(1965,8,12),'M','Ninguna','Primaria','Independiente',1,
             False,'Centro',pvd1,'','3134567890'),

            ('TI','10943105','Valentina','Andrea','Giraldo','Arenas',
             date(2008,2,28),'F','Ninguna','Bachillerato','Estudiante',1,
             False,'Centro',pvd1,'vgiraldo@gmail.com','3145678901'),

            ('CC','10943106','Luis','Fernando','Herrera','Cano',
             date(1987,6,18),'M','Ninguna','Tecnico/Tecnologo','Independiente',2,
             False,'La Maria',pvd2,'lfherrera@hotmail.com','3156789012'),

            ('CC','10943107','Claudia','Patricia','Salazar','Hoyos',
             date(1975,9,3),'F','Ninguna','Universitario','Docente',3,
             False,'La Maria',pvd2,'cpsalazar@gmail.com','3167890123'),

            ('TI','10943108','Jhon','Alexander','Bermudez','Ruiz',
             date(2007,12,14),'M','Ninguna','Bachillerato','Estudiante',1,
             False,'La Maria',pvd2,'','3178901234'),

            ('CC','10943109','Sofia','Alejandra','Munoz','Torres',
             date(1998,1,25),'F','Ninguna','Universitario','Desempleada',1,
             False,'La Maria',pvd2,'sofia.munoz@gmail.com','3189012345'),

            ('CC','10943110','Ricardo','Emilio','Cordoba','Patino',
             date(1955,10,7),'M','Afrodescendiente','Primaria','Pensionado',1,
             True,'Centro',pvd1,'','3190123456'),

            ('CC','10943111','Gloria','Ines','Ramirez','Castro',
             date(1960,5,19),'F','Ninguna','Bachillerato','Ama de casa',2,
             False,'La Maria',pvd2,'','3201234567'),

            ('CC','10943112','Andres','Felipe','Montoya','Acosta',
             date(1995,8,23),'M','Ninguna','Tecnico/Tecnologo','Empleado',1,
             False,'Centro',pvd1,'andres.montoya@gmail.com','3212345678'),

            ('CC','10943113','Paola','Andrea','Ocampo','Villa',
             date(1988,3,11),'F','Indigena','Universitario','Enfermera',2,
             False,'La Maria',pvd2,'paola.ov@yahoo.com','3223456789'),

            ('CC','10943114','Diego','Alejandro','Serna','Mejia',
             date(2000,7,4),'M','Ninguna','Tecnico/Tecnologo','Desempleado',1,
             False,'Centro',pvd1,'dserna@gmail.com','3234567890'),

            ('CC','10943115','Lorena','Catalina','Zapata','Bedoya',
             date(1983,12,1),'F','Ninguna','Bachillerato','Comerciante',2,
             False,'La Maria',pvd2,'lorena.zb@gmail.com','3245678901'),
        ]

        ciudadanos = []
        for (tipo, num, pn, sn, pa, sa, fnac, gen, etnia, edu, ocu, est,
             disc, barrio, pvd, correo, telf) in datos:
            obj, c = Ciudadano.objects.get_or_create(
                numero_documento=num,
                defaults=dict(
                    punto_vive_digital=pvd,
                    tipo_documento=tipo,
                    primer_nombre=pn, segundo_nombre=sn,
                    primer_apellido=pa, segundo_apellido=sa,
                    fecha_nacimiento=fnac, genero=gen, etnia=etnia,
                    nivel_educativo=edu, ocupacion=ocu, estrato=est,
                    tiene_discapacidad=disc,
                    descripcion_discapacidad='Discapacidad visual' if disc else '',
                    barrio=barrio, estado='A',
                    correo=correo, telefono=telf,
                    direccion=f'Calle {num[-2:]} No. 5-{num[-1:]}0, {barrio}',
                )
            )
            self._ok(f'{pn} {pa}') if c else self._skip(f'{pn} {pa}')
            ciudadanos.append(obj)
        return ciudadanos

    # ------------------------------------------------------------------
    # RECURSO REAL (el que ya estaba en la BD)
    # ------------------------------------------------------------------
    def _obtener_recurso_real(self, pvd1):
        self._titulo('Recursos')
        try:
            r = Recurso.objects.get(codigo='626410')
            if not r.punto_vive_digital:
                r.punto_vive_digital = pvd1
                r.save()
                self._ok(f'Recurso existente "{r.tipo}" asignado a {pvd1.nombre}')
            else:
                self._skip(f'Recurso "{r.tipo}" [{r.codigo}]')
            return r
        except Recurso.DoesNotExist:
            # Si fue borrado, lo recreamos
            r = Recurso.objects.create(
                punto_vive_digital=pvd1,
                tipo='Computador de Mesa',
                codigo='626410',
                estado='A',
            )
            self._ok(f'Recurso "Computador de Mesa" recreado')
            return r

    # ------------------------------------------------------------------
    # PRESTAMOS
    # ------------------------------------------------------------------
    def _crear_prestamos(self, recurso):
        self._titulo('Prestamos de recursos')
        ahora = timezone.make_aware(datetime.combine(HOY, time(9, 0)))
        datos = [
            (ahora - timedelta(hours=3),
             ahora - timedelta(hours=1),
             'Ciudadano uso el equipo para tramite SISBEN'),
            (ahora - timedelta(days=1, hours=2),
             ahora - timedelta(days=1),
             'Prestamo para consulta en linea EPS'),
            (ahora - timedelta(days=2),
             ahora - timedelta(hours=-2, days=2) + timedelta(hours=4),
             'Uso para capacitacion de ofimatica'),
        ]
        prestamos = []
        for entrega, devolucion, obs in datos:
            qs = PrestamoRecurso.objects.filter(recurso=recurso, fecha_entrega=entrega)
            if qs.exists():
                self._skip(f'Prestamo {entrega.date()}')
                prestamos.append(qs.first())
            else:
                p = PrestamoRecurso.objects.create(
                    recurso=recurso,
                    fecha_entrega=entrega,
                    fecha_devolucion=devolucion,
                    observaciones=obs,
                )
                self._ok(f'Prestamo {entrega.date()}')
                prestamos.append(p)
        return prestamos

    # ------------------------------------------------------------------
    # ATENCIONES
    # ------------------------------------------------------------------
    def _crear_atenciones(self, pvd1, pvd2, ciudadanos, prestamos, julia, lady):
        self._titulo('Atenciones a ciudadanos')
        # (pvd, ciu_idx, fecha, h_ini, h_fin, estado, obs, prestamo_idx|None, operador)
        datos = [
            (pvd1,0,  HOY,                     time(8,0),  time(8,45),  'F',
             'Tramite en linea SISBEN completado.',          0, julia),
            (pvd1,1,  HOY,                     time(9,0),  time(9,30),  'F',
             'Asesoria plataforma Supernotariado.',          None, julia),
            (pvd1,2,  HOY,                     time(10,0), time(10,20), 'P',
             'Ciudadana solicita acceso a internet.',        None, julia),
            (pvd1,3,  HOY,                     time(10,30),None,        'P',
             'Consulta tramite pensional Colpensiones.',     1, julia),
            (pvd1,11, HOY - timedelta(days=1), time(8,30), time(9,0),   'F',
             'Impresion de documentos legales.',             None, julia),
            (pvd1,13, HOY - timedelta(days=1), time(9,15), time(10,0),  'F',
             'Navegacion libre, busqueda de empleo.',        None, julia),
            (pvd1,9,  HOY - timedelta(days=2), time(14,0), time(14,30), 'C',
             'Atencion cancelada: ciudadano no regreso.',    None, julia),
            (pvd1,4,  HOY - timedelta(days=3), time(11,0), time(11,45), 'F',
             'Inscripcion a curso de ofimatica basica.',     None, julia),

            (pvd2,5,  HOY,                     time(8,0),  time(8,50),  'F',
             'Certificado de estratificacion en linea.',     None, lady),
            (pvd2,6,  HOY,                     time(9,30), time(10,15), 'F',
             'Capacitacion uso de correo electronico.',      None, lady),
            (pvd2,7,  HOY,                     time(10,30),None,        'P',
             'Acceso a internet busqueda academica.',        2, lady),
            (pvd2,8,  HOY - timedelta(days=1), time(8,0),  time(8,30),  'F',
             'Tramite afiliacion EPS en linea.',             None, lady),
            (pvd2,12, HOY - timedelta(days=1), time(13,0), time(13,45), 'F',
             'Asesoria en uso de banca virtual.',            None, lady),
            (pvd2,14, HOY - timedelta(days=2), time(9,0),  time(9,30),  'F',
             'Impresion hoja de vida y envio por correo.',   None, lady),
            (pvd2,10, HOY - timedelta(days=3), time(15,0), time(15,30), 'C',
             'Atencion cancelada: falla de conexion.',       None, lady),
        ]
        atenciones = []
        for pvd, ci, fecha, hi, hf, estado, obs, pi, op in datos:
            prestamo = prestamos[pi] if pi is not None else None
            qs = Atencion.objects.filter(
                punto_vive_digital=pvd, ciudadano=ciudadanos[ci], fecha=fecha
            )
            if qs.exists():
                self._skip(f'Atencion {ciudadanos[ci].primer_nombre} {fecha}')
                atenciones.append(qs.first())
            else:
                a = Atencion.objects.create(
                    punto_vive_digital=pvd,
                    ciudadano=ciudadanos[ci],
                    operador=op,
                    prestamo=prestamo,
                    fecha=fecha,
                    hora_inicio=hi,
                    hora_fin=hf,
                    estado=estado,
                    observaciones=obs,
                )
                self._ok(
                    f'Atencion {ciudadanos[ci].primer_nombre} '
                    f'{ciudadanos[ci].primer_apellido} - {fecha} [{estado}]'
                )
                atenciones.append(a)
        return atenciones

    # ------------------------------------------------------------------
    # SERVICIOS
    # ------------------------------------------------------------------
    def _crear_servicios(self, atenciones):
        self._titulo('Servicios')
        mapa = [
            (0,  'Tramite en Linea',        'Tramites digitales',  'SISBEN III actualizacion', 'S'),
            (1,  'Asesoria Tecnologica',     'Asesoria',            'Orientacion Supernotariado', 'S'),
            (2,  'Acceso a Internet',        'Conectividad',        'Navegacion libre con equipo de sala', 'S'),
            (3,  'Tramite Pensional',        'Tramites digitales',  'Colpensiones consulta semanas', 'S'),
            (4,  'Impresion de Documentos',  'Impresion/Escaneo',   'Impresion 3 paginas A4', 'S'),
            (5,  'Navegacion Libre',         'Conectividad',        'Busqueda de ofertas laborales', 'S'),
            (7,  'Inscripcion a Curso',      'Formacion',           'Inscripcion a Ofimatica Basica', 'N'),
            (8,  'Tramite en Linea',         'Tramites digitales',  'Certificado estratificacion Alcaldia', 'S'),
            (9,  'Capacitacion Digital',     'Formacion',           'Uso basico de correo electronico', 'S'),
            (10, 'Acceso a Internet',        'Conectividad',        'Busqueda academica', 'S'),
            (11, 'Tramite EPS',             'Tramites digitales',   'Afiliacion a EPS en linea', 'S'),
            (12, 'Asesoria Banca Virtual',   'Asesoria',            'Orientacion app Bancolombia', 'N'),
            (13, 'Impresion y Correo',       'Impresion/Escaneo',   'Impresion hoja de vida + envio', 'S'),
        ]
        for ai, nombre, tipo, desc, req in mapa:
            if ai >= len(atenciones):
                continue
            atencion = atenciones[ai]
            qs = Servicio.objects.filter(atencion=atencion, nombre=nombre)
            if not qs.exists():
                Servicio.objects.create(
                    atencion=atencion, nombre=nombre, tipo=tipo,
                    descripcion=desc, requiere_equipo=req, estado='A'
                )
                self._ok(f'Servicio "{nombre}"')
            else:
                self._skip(f'Servicio "{nombre}"')

    # ------------------------------------------------------------------
    # SATISFACCION
    # ------------------------------------------------------------------
    def _crear_satisfaccion(self, atenciones):
        self._titulo('Encuestas de satisfaccion')
        calificaciones = [5, 5, 4, 5, 5, 4, 5, 5, 3, 5]
        comentarios = [
            'Excelente atencion, muy amable el personal.',
            'Me ayudaron a resolver mi tramite rapidamente.',
            'Buen servicio, pero la conexion era lenta.',
            'Muy completo el servicio, volvere.',
            'El administrador fue muy paciente y claro.',
            'Bien, aunque espere un poco.',
            'Todo perfecto, seguire usando el PVD.',
            'Muy buena gestion del tramite.',
            'El servicio fue regular, el equipo fallo una vez.',
            'Excelente, me solucionaron el problema enseguida.',
        ]
        finalizadas = [a for a in atenciones if a.estado == 'F']
        for i, a in enumerate(finalizadas):
            if not Satisfaccion.objects.filter(atencion=a).exists():
                Satisfaccion.objects.create(
                    atencion=a,
                    calificacion=calificaciones[i % len(calificaciones)],
                    comentario=comentarios[i % len(comentarios)],
                    fecha=timezone.make_aware(datetime.combine(a.fecha, time(17, 0))),
                )
                self._ok(f'Encuesta atencion #{a.pk} - {calificaciones[i % len(calificaciones)]} estrellas')
            else:
                self._skip(f'Encuesta atencion #{a.pk}')

    # ------------------------------------------------------------------
    # HABILITACIONES DE SALA
    # ------------------------------------------------------------------
    def _crear_habilitaciones(self, pvd1, pvd2, julia, lady):
        self._titulo('Habilitaciones de sala')

        def sala(pvd, nombre):
            return Sala.objects.get(punto_vive_digital=pvd, nombre=nombre)

        s1_principal = sala(pvd1, 'Sala Principal')
        s1_cap       = sala(pvd1, 'Sala de Capacitacion')
        s2_principal = sala(pvd2, 'Sala Principal')
        s2_cap       = sala(pvd2, 'Sala de Capacitacion')

        datos = [
            (s1_cap,     'CAP', HOY,                      time(8,0),  time(12,0),
             'Grupo Adultos Mayores Barrio Centro',
             'Taller de habilidades digitales basicas', 15, 'C', julia),
            (s1_principal,'NAV',HOY,                      time(13,0), time(17,0),
             'Comunidad general',
             'Navegacion libre tarde', 12, 'E', julia),
            (s1_cap,     'TRAM',HOY - timedelta(days=1),  time(9,0),  time(11,0),
             'Usuarios tramites',
             'Atencion de tramites en linea', 6, 'F', julia),
            (s2_cap,     'CAP', HOY,                      time(14,0), time(17,0),
             'Jovenes barrio La Maria',
             'Formacion en ofimatica', 18, 'E', lady),
            (s2_principal,'NAV',HOY + timedelta(days=1),  time(8,0),  time(12,0),
             'Comunidad general',
             'Navegacion libre manana', 12, 'P', lady),
            (s2_cap,     'CONF',HOY + timedelta(days=2),  time(10,0), time(12,0),
             'Alcaldia de Bugalagrande',
             'Reunion de seguimiento contrato CD-224-2026', 6, 'P', lady),
        ]
        for sala_obj, tipo, fecha, hi, hf, sol, prop, cap, estado, reg in datos:
            qs = HabilitacionSala.objects.filter(sala=sala_obj, fecha=fecha, hora_inicio=hi)
            if not qs.exists():
                HabilitacionSala.objects.create(
                    sala=sala_obj, tipo_uso=tipo, fecha=fecha,
                    hora_inicio=hi, hora_fin=hf,
                    solicitante=sol, proposito=prop,
                    capacidad_requerida=cap, estado=estado,
                    registrado_por=reg,
                )
                self._ok(f'{sala_obj.nombre} ({sala_obj.punto_vive_digital.nombre}) - {fecha} [{tipo}]')
            else:
                self._skip(f'{sala_obj.nombre} {fecha} {hi}')

    # ------------------------------------------------------------------
    # CURSOS
    # ------------------------------------------------------------------
    def _crear_cursos(self, pvd1, pvd2, julia, lady):
        self._titulo('Cursos / Talleres')
        datos = [
            (pvd1, 'Ofimatica Basica: Word y Excel',
             'Formacion en procesador de texto y hoja de calculo sin experiencia previa.',
             'P', 'Adultos y jovenes mayores de 15 anos',
             HOY - timedelta(days=7), HOY + timedelta(days=14), 'AC', julia),

            (pvd1, 'Tramites Digitales del Estado Colombiano',
             'Tramites ante SISBEN, DIAN, Colpensiones y EPS desde casa.',
             'P', 'Ciudadanos en general',
             HOY - timedelta(days=30), HOY - timedelta(days=9), 'FI', julia),

            (pvd2, 'Seguridad Digital y Redes Sociales',
             'Protege tu informacion personal en internet y usa las redes de forma segura.',
             'P', 'Jovenes de 12 a 25 anos',
             HOY + timedelta(days=3), HOY + timedelta(days=17), 'PL', lady),

            (pvd2, 'Introduccion a Internet para Adultos Mayores',
             'Navegacion basica, correo electronico y videollamadas para mayores de 60 anos.',
             'P', 'Adultos mayores de 60 anos',
             HOY - timedelta(days=14), HOY - timedelta(days=1), 'FI', lady),
        ]
        cursos = []
        for pvd, nombre, desc, modalidad, pob, f_ini, f_fin, estado, reg in datos:
            obj, c = Curso.objects.get_or_create(
                nombre=nombre, punto_vive_digital=pvd,
                defaults=dict(
                    descripcion=desc, modalidad=modalidad,
                    poblacion_objetivo=pob,
                    fecha_inicio=f_ini, fecha_fin=f_fin,
                    estado=estado, registrado_por=reg,
                )
            )
            self._ok(nombre) if c else self._skip(nombre)
            cursos.append(obj)
        return cursos

    # ------------------------------------------------------------------
    # SESIONES E INSCRIPCIONES
    # ------------------------------------------------------------------
    def _crear_sesiones_e_inscripciones(self, cursos, ciudadanos, julia):
        self._titulo('Sesiones de cursos')
        sesiones_por_curso = [
            (0, [
                (1, HOY - timedelta(days=7), time(8,0),  time(10,0),  'Introduccion a Word', 'Interfaz y formato basico'),
                (2, HOY - timedelta(days=5), time(8,0),  time(10,0),  'Word avanzado',       'Tablas, imagenes y estilos'),
                (3, HOY + timedelta(days=2), time(8,0),  time(10,0),  'Introduccion a Excel','Formulas basicas y graficos'),
            ]),
            (1, [
                (1, HOY - timedelta(days=30), time(14,0), time(16,0), 'SISBEN en linea',    'Consulta puntaje y actualizacion'),
                (2, HOY - timedelta(days=23), time(14,0), time(16,0), 'DIAN y MUISCA',      'Consulta RUT y declaracion'),
                (3, HOY - timedelta(days=16), time(14,0), time(16,0), 'Colpensiones y EPS', 'Semanas cotizadas y afiliacion'),
            ]),
            (2, [
                (1, HOY + timedelta(days=3), time(15,0), time(17,0), 'Contrasenas seguras', 'Como crear y gestionar contrasenas'),
                (2, HOY + timedelta(days=10),time(15,0), time(17,0), 'Redes sociales',      'Privacidad en Facebook e Instagram'),
                (3, HOY + timedelta(days=17),time(15,0), time(17,0), 'Estafas digitales',   'Reconocer phishing y fraudes'),
            ]),
            (3, [
                (1, HOY - timedelta(days=14), time(9,0), time(11,0), 'Que es internet',    'Navegadores y buscadores'),
                (2, HOY - timedelta(days=7),  time(9,0), time(11,0), 'Correo electronico', 'Crear cuenta Gmail y enviar correos'),
                (3, HOY - timedelta(days=1),  time(9,0), time(11,0), 'Videollamadas',      'WhatsApp y Google Meet'),
            ]),
        ]
        for ci, sesiones_data in sesiones_por_curso:
            if ci >= len(cursos):
                continue
            curso = cursos[ci]
            for num, fecha, hi, hf, tema, contenido in sesiones_data:
                s, c = SesionCurso.objects.get_or_create(
                    curso=curso, numero_sesion=num,
                    defaults=dict(fecha=fecha, hora_inicio=hi, hora_fin=hf,
                                  tema=tema, contenido=contenido)
                )
                self._ok(f'Sesion {num}: {tema}') if c else self._skip(f'Sesion {num}: {tema}')

        self._titulo('Inscripciones a cursos')
        inscrip_map = [
            (0, [0, 1, 2, 4, 11, 13]),
            (1, [0, 3, 9, 11]),
            (2, [5, 7, 8, 14]),
            (3, [6, 10, 12, 14]),
        ]
        for ci, ciu_idxs in inscrip_map:
            if ci >= len(cursos):
                continue
            curso = cursos[ci]
            for idx in ciu_idxs:
                if idx >= len(ciudadanos):
                    continue
                ciudadano = ciudadanos[idx]
                estado = 'C' if curso.estado == 'FI' else 'I'
                insc, c = InscripcionCurso.objects.get_or_create(
                    curso=curso, ciudadano=ciudadano,
                    defaults={'estado': estado, 'registrado_por': julia}
                )
                self._ok(f'{ciudadano.primer_nombre} -> {curso.nombre[:35]}') if c else self._skip(f'{ciudadano.primer_nombre} -> {curso.nombre[:35]}')

        self._titulo('Asistencia a sesiones')
        asistencia_map = {
            1: {1: [0, 9, 11], 2: [0, 9], 3: [0, 3, 9, 11]},
            3: {1: [6, 10, 12, 14], 2: [6, 12, 14], 3: [6, 10, 14]},
        }
        for ci, sesiones_asist in asistencia_map.items():
            if ci >= len(cursos):
                continue
            curso = cursos[ci]
            todos_idxs_map = {r[0]: r[1] for r in inscrip_map}
            todos_idxs = todos_idxs_map.get(ci, [])
            for num_sesion, asistieron_idxs in sesiones_asist.items():
                try:
                    sesion = SesionCurso.objects.get(curso=curso, numero_sesion=num_sesion)
                except SesionCurso.DoesNotExist:
                    continue
                for idx in todos_idxs:
                    if idx >= len(ciudadanos):
                        continue
                    ciudadano = ciudadanos[idx]
                    asistio = idx in asistieron_idxs
                    _, c = AsistenciaSesion.objects.get_or_create(
                        sesion=sesion, ciudadano=ciudadano,
                        defaults={'asistio': asistio}
                    )
                    if c:
                        marca = 'asistio' if asistio else 'ausente'
                        self._ok(f'{ciudadano.primer_nombre} - Sesion {num_sesion} [{marca}]')

    # ------------------------------------------------------------------
    # MANTENIMIENTOS
    # ------------------------------------------------------------------
    def _crear_mantenimientos(self, pvd1, pvd2, ofitic):
        self._titulo('Mantenimientos de equipo')
        datos = [
            (pvd1, 'PRV', HOY - timedelta(days=15),
             'Computadores de mesa, impresora y proyector',
             'Limpieza interna, actualizacion de antivirus y sistema operativo.',
             'Polvo acumulado. Software desactualizado en un equipo.',
             'Revision trimestral recomendada.'),
            (pvd2, 'COR', HOY - timedelta(days=5),
             'Impresora del salon de capacitacion',
             'Cambio de cartucho y limpieza de cabezales de impresion.',
             'Impresora con saturacion de cabezales.',
             'Verificar nivel de tinta mensualmente.'),
            (pvd1, 'PRV', HOY + timedelta(days=10),
             'Todos los equipos de la sala principal',
             'Mantenimiento preventivo programado segun cronograma trimestral.',
             None,
             'Programado. No requiere accion inmediata.'),
        ]
        for pvd, tipo, fecha, equipos, desc, hallazgos, acciones in datos:
            qs = MantenimientoEquipo.objects.filter(
                punto_vive_digital=pvd, tipo=tipo, fecha=fecha
            )
            if not qs.exists():
                MantenimientoEquipo.objects.create(
                    punto_vive_digital=pvd, tipo=tipo, fecha=fecha,
                    equipos_intervenidos=equipos, descripcion=desc,
                    hallazgos=hallazgos, acciones=acciones,
                    realizado_por=ofitic,
                )
                self._ok(f'{pvd.nombre} - {tipo} {fecha}')
            else:
                self._skip(f'{pvd.nombre} - {tipo} {fecha}')

    # ------------------------------------------------------------------
    # RESUMEN
    # ------------------------------------------------------------------
    def _imprimir_resumen(self, su, ofitic, julia, lady, pvd1, pvd2):
        self.stdout.write(self.style.WARNING(
            '\n  CREDENCIALES DE ACCESO\n'
            '  ------------------------------------------\n'
            f'  Superusuario   usuario: {su.username:<16} contrasena: (la que ya tenia)\n'
            f'  Admin TIC      usuario: {ofitic.username:<16} contrasena: ofitic123\n'
            f'  Admin PVD      usuario: {julia.username:<16} contrasena: balon102@\n'
            f'  Admin PVD      usuario: {lady.username:<16} contrasena: balon102@\n'
            '\n  PVDs ACTIVOS\n'
            '  ------------------------------------------\n'
            f'  {pvd1.nombre} -> admin: {julia.username}\n'
            f'  {pvd2.nombre} -> admin: {lady.username}\n'
            '\n  DATOS DE DEMO CARGADOS\n'
            '  ------------------------------------------\n'
            '  2  Puntos Vive Digital\n'
            '  2  Salas por PVD (4 en total)\n'
            '  15 Ciudadanos registrados\n'
            '  1  Recurso (el real: Computador de Mesa 626410)\n'
            '  3  Prestamos de recursos\n'
            '  15 Atenciones (8 finalizadas, 4 pendientes, 3 canceladas)\n'
            '  13 Servicios prestados\n'
            '  10 Encuestas de satisfaccion\n'
            '  6  Habilitaciones de sala\n'
            '  4  Cursos + 12 Sesiones\n'
            '  3  Mantenimientos de equipo\n'
        ))
