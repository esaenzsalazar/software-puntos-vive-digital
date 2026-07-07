"""
Comando para poblar la base de datos con datos de demostración completos.
Uso: python manage.py seed_demo

Limpia todos los datos y recarga con datos realistas para los dos PVDs:
  - PVD Edificio Rafael Arias
  - PVD Colegio Antonio Nariño
"""
import io
import os
from datetime import date, time, timedelta, datetime
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from django.db import connection
from django.utils import timezone
from django.core.files.base import ContentFile

from modulo_puntos.models import (
    PuntoViveDigital, UserProfile, Ciudadano,
    Recurso, PrestamoRecurso, Atencion, Servicio, Satisfaccion,
    Sala, HabilitacionSala,
    Curso, SesionCurso, InscripcionCurso, AsistenciaSesion,
    MantenimientoEquipo, Evidencia,
    PermisoDefinicion, PermisoRol,
)

HOY = date(2026, 6, 20)

NOMBRE_PVD1 = 'PVD Edificio Rafael Arias'
NOMBRE_PVD2 = 'PVD Colegio Antonio Nariño'


class Command(BaseCommand):
    help = 'Carga datos de demostración completos para todos los módulos del sistema'

    def _ok(self, msg):
        self.stdout.write(self.style.SUCCESS(f'  [OK] {msg}'))

    def _skip(self, msg):
        self.stdout.write(f'  [--] {msg} (ya existe)')

    def _del(self, msg):
        self.stdout.write(self.style.WARNING(f'  [DEL] {msg}'))

    def _titulo(self, msg):
        self.stdout.write(self.style.HTTP_INFO(f'\n>>> {msg}'))

    def add_arguments(self, parser):
        parser.add_argument(
            '--yes', action='store_true',
            help='Omite la confirmación interactiva (para uso en scripts).'
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                'Este comando borra y reemplaza datos reales (ciudadanos, atenciones, '
                'usuarios de demo con contraseñas conocidas). Sólo puede ejecutarse con '
                'DJANGO_DEBUG=True. Abortado.'
            )

        db_name = connection.settings_dict.get('NAME')
        db_host = connection.settings_dict.get('HOST')
        if not options['yes']:
            self.stdout.write(self.style.WARNING(
                f'\nEste comando BORRARÁ los datos existentes de ciudadanos, atenciones, '
                f'recursos, cursos, etc. en la base de datos "{db_name}" ({db_host}) y '
                f'los reemplazará con datos de demostración (incluye usuarios con '
                f'contraseñas conocidas de prueba).\n'
            ))
            respuesta = input(f'Escribe el nombre de la base de datos ("{db_name}") para confirmar: ').strip()
            if respuesta != db_name:
                raise CommandError('Confirmación no coincide. Abortado.')

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
        self._asegurar_permisos(superusuario)
        self._asegurar_salas(pvd1, pvd2)
        ciudadanos    = self._crear_ciudadanos(pvd1, pvd2)
        recursos      = self._crear_recursos(pvd1, pvd2)
        prestamos     = self._crear_prestamos(recursos, ciudadanos)
        atenciones    = self._crear_atenciones(pvd1, pvd2, ciudadanos, prestamos, julia, lady)
        self._crear_servicios(atenciones)
        self._crear_satisfaccion(atenciones)
        self._crear_habilitaciones(pvd1, pvd2, julia, lady)
        cursos        = self._crear_cursos(pvd1, pvd2, julia, lady)
        self._crear_sesiones_e_inscripciones(cursos, ciudadanos, julia, lady)
        self._crear_mantenimientos(pvd1, pvd2, ofitic)
        self._crear_evidencias(pvd1, pvd2, julia, lady)

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
        self._titulo('Limpiando datos anteriores')
        with connection.cursor() as cur:
            cur.execute('SET FOREIGN_KEY_CHECKS = 0;')

        for Model, label in [
            (Satisfaccion,       'encuestas de satisfacción'),
            (Servicio,           'servicios'),
            (AsistenciaSesion,   'asistencias'),
            (InscripcionCurso,   'inscripciones'),
            (Evidencia,          'evidencias'),
            (Atencion,           'atenciones'),
            (PrestamoRecurso,    'préstamos'),
            (HabilitacionSala,   'habilitaciones de sala'),
            (MantenimientoEquipo,'mantenimientos'),
        ]:
            n = Model.objects.count()
            if n:
                Model.objects.all().delete()
                self._del(f'{n} {label} eliminados')

        Curso.objects.all().delete()
        Ciudadano.objects.all().delete()
        Recurso.objects.all().delete()
        Sala.objects.all().delete()
        self._del('Cursos, ciudadanos, recursos y salas eliminados')

        users_a_borrar = User.objects.filter(is_superuser=False)
        n = users_a_borrar.count()
        if n:
            users_a_borrar.delete()
            self._del(f'{n} usuarios no-superuser eliminados')

        with connection.cursor() as cur:
            cur.execute('SET FOREIGN_KEY_CHECKS = 1;')

        self._ok('Limpieza completada')

    # ------------------------------------------------------------------
    # GRUPOS
    # ------------------------------------------------------------------
    def _asegurar_grupos(self):
        self._titulo('Grupos de roles')
        g_tic, c = Group.objects.get_or_create(name='Administrador TIC')
        self._ok('Administrador TIC') if c else self._skip('Administrador TIC')
        g_pvd, c = Group.objects.get_or_create(name='Administrador PVD')
        self._ok('Administrador PVD') if c else self._skip('Administrador PVD')
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
    # PERMISOS
    # ------------------------------------------------------------------
    def _asegurar_permisos(self, admin):
        self._titulo('Permisos del sistema (RBAC)')
        permisos_def = [
            ('ciudadanos.ver',            'Ver Ciudadanos',             'Ciudadanos',       True),
            ('ciudadanos.registrar',      'Registrar Ciudadano',        'Ciudadanos',       True),
            ('ciudadanos.editar',         'Editar Ciudadano',           'Ciudadanos',       True),
            ('atenciones.ver',            'Ver Atenciones',             'Atenciones',       True),
            ('atenciones.registrar',      'Registrar Atención',         'Atenciones',       True),
            ('atenciones.finalizar',      'Finalizar Atención',         'Atenciones',       True),
            ('servicios.registrar',       'Registrar Servicio',         'Servicios',        True),
            ('satisfaccion.registrar',    'Registrar Satisfacción',     'Calidad',          True),
            ('recursos.ver',              'Ver Recursos',               'Recursos',         True),
            ('recursos.registrar',        'Registrar Recurso',          'Recursos',         True),
            ('prestamos.registrar',       'Registrar Préstamo',         'Préstamos',        True),
            ('prestamos.devolucion',      'Registrar Devolución',       'Préstamos',        True),
            ('salas.ver',                 'Ver Salas',                  'Salas',            True),
            ('salas.gestionar',           'Gestionar Salas',            'Salas',            False),
            ('habilitaciones.ver',        'Ver Habilitaciones',         'Salas',            True),
            ('habilitaciones.gestionar',  'Gestionar Habilitaciones',   'Salas',            True),
            ('cursos.ver',                'Ver Cursos',                 'Cursos',           True),
            ('cursos.gestionar',          'Gestionar Cursos',           'Cursos',           True),
            ('cursos.inscribir',          'Inscribir Ciudadanos',       'Cursos',           True),
            ('mantenimiento.ver',         'Ver Mantenimientos',         'Mantenimiento',    True),
            ('mantenimiento.registrar',   'Registrar Mantenimiento',    'Mantenimiento',    False),
            ('evidencias.ver',            'Ver Evidencias',             'Evidencias',       True),
            ('evidencias.registrar',      'Registrar Evidencia',        'Evidencias',       True),
            ('reportes.ver',              'Ver Reportes',               'Reportes',         False),
            ('auditoria.ver',             'Ver Auditoría',              'Auditoría',        False),
            ('usuarios.gestionar',        'Gestionar Usuarios',         'Administración',   False),
            ('infraestructura.pvd',       'Gestionar PVDs',             'Infraestructura',  False),
        ]
        created = 0
        for codigo, nombre, cat, delegable in permisos_def:
            p, c = PermisoDefinicion.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre, 'categoria': cat,
                    'delegable_por_ofitic': delegable, 'activo': True,
                    'descripcion': f'Permite {nombre.lower()} en el sistema.',
                }
            )
            if c:
                created += 1
            PermisoRol.objects.get_or_create(
                rol='admin_tic', permiso=p,
                defaults={'otorgado_por': admin}
            )
            if delegable:
                PermisoRol.objects.get_or_create(
                    rol='admin_pvd', permiso=p,
                    defaults={'otorgado_por': admin}
                )
        self._ok(f'{created} permisos nuevos / {len(permisos_def)} total definidos')

    # ------------------------------------------------------------------
    # PVDs REALES
    # ------------------------------------------------------------------
    def _asegurar_pvds(self):
        self._titulo('Puntos Vive Digital')
        pvd1, c = PuntoViveDigital.objects.get_or_create(
            nombre=NOMBRE_PVD1,
            defaults={
                'direccion': 'Carrera 6 # 4-65, Edificio Rafael Arias',
                'barrio': 'Centro',
                'estado': 'A',
                'descripcion': (
                    'Punto Vive Digital ubicado en el Edificio Rafael Arias, '
                    'centro histórico de Bugalagrande. Atiende a la comunidad del casco urbano.'
                ),
            }
        )
        self._ok(NOMBRE_PVD1) if c else self._skip(NOMBRE_PVD1)

        pvd2, c = PuntoViveDigital.objects.get_or_create(
            nombre=NOMBRE_PVD2,
            defaults={
                'direccion': 'Calle 9 # 6-08, Institución Educativa Antonio Nariño',
                'barrio': 'Antonio Nariño',
                'estado': 'A',
                'descripcion': (
                    'Punto Vive Digital ubicado en la Institución Educativa Antonio Nariño, '
                    'comunidad del barrio Antonio Nariño y veredas aledañas.'
                ),
            }
        )
        self._ok(NOMBRE_PVD2) if c else self._skip(NOMBRE_PVD2)
        return pvd1, pvd2

    # ------------------------------------------------------------------
    # USUARIOS
    # ------------------------------------------------------------------
    def _crear_usuarios(self, grupos, pvd1, pvd2):
        self._titulo('Usuarios del sistema')

        ofitic, c = User.objects.get_or_create(
            username='ofitic',
            defaults={
                'first_name': 'Luz Adriana', 'last_name': 'Pérez Castaño',
                'email': 'ofitic@bugalagrande.gov.co', 'is_staff': True,
            }
        )
        if c:
            ofitic.set_password('ofitic123')
            ofitic.save()
            self._ok('ofitic (Admin TIC)')
        else:
            self._skip('ofitic')
        ofitic.groups.set([grupos['tic']])
        UserProfile.objects.update_or_create(
            usuario=ofitic, defaults={'rol': 'admin_tic', 'punto_asignado': None}
        )

        julia, c = User.objects.get_or_create(
            username='pvdjulia',
            defaults={
                'first_name': 'Julia Marcela', 'last_name': 'Giraldo Ospina',
                'email': 'julia.giraldo@bugalagrande.gov.co',
            }
        )
        if c:
            julia.set_password('pvd2026!')
            julia.save()
            self._ok('pvdjulia (Admin PVD – Rafael Arias)')
        else:
            self._skip('pvdjulia')
        julia.groups.set([grupos['pvd']])
        UserProfile.objects.update_or_create(
            usuario=julia, defaults={'rol': 'admin_pvd', 'punto_asignado': pvd1}
        )

        lady, c = User.objects.get_or_create(
            username='pvdlady',
            defaults={
                'first_name': 'Lady Diana', 'last_name': 'Morales Vargas',
                'email': 'lady.morales@bugalagrande.gov.co',
            }
        )
        if c:
            lady.set_password('pvd2026!')
            lady.save()
            self._ok('pvdlady (Admin PVD – Antonio Nariño)')
        else:
            self._skip('pvdlady')
        lady.groups.set([grupos['pvd']])
        UserProfile.objects.update_or_create(
            usuario=lady, defaults={'rol': 'admin_pvd', 'punto_asignado': pvd2}
        )

        pvd1.admin_a_cargo = julia
        pvd1.save()
        pvd2.admin_a_cargo = lady
        pvd2.save()

        return ofitic, julia, lady

    # ------------------------------------------------------------------
    # SALAS
    # ------------------------------------------------------------------
    def _asegurar_salas(self, pvd1, pvd2):
        self._titulo('Salas')
        salas_data = [
            ('Sala de Navegación',    'Sala principal con equipos de cómputo para acceso a internet y trámites.', 10),
            ('Sala de Capacitación',  'Espacio equipado para talleres, cursos y formación digital ciudadana.', 20),
        ]
        for pvd in [pvd1, pvd2]:
            for nombre, desc, cap in salas_data:
                sala, c = Sala.objects.get_or_create(
                    punto_vive_digital=pvd, nombre=nombre,
                    defaults={'descripcion': desc, 'capacidad': cap, 'estado': 'A'}
                )
                self._ok(f'{pvd.nombre} → {nombre}') if c else self._skip(f'{pvd.nombre} → {nombre}')

    # ------------------------------------------------------------------
    # CIUDADANOS (30 – variedad de perfiles para reportes)
    # ------------------------------------------------------------------
    def _crear_ciudadanos(self, pvd1, pvd2):
        self._titulo('Ciudadanos')
        # (tipo, num_doc, p_nombre, s_nombre, p_apellido, s_apellido,
        #  fecha_nac, genero, etnia, nivel_edu, ocupacion, estrato,
        #  discap, barrio, pvd, correo, telefono)
        datos = [
            # PVD1 – Rafael Arias
            ('CC','10943101','Ana','Lucía','Prado','Morales',
             date(1995,4,30),'F','Ninguna','Técnico/Tecnólogo','Estudiante',1,
             False,'Centro',pvd1,'ana.prado@gmail.com','3101234567'),
            ('CC','10943102','Juan','Pablo','Castaño','Vargas',
             date(1978,11,5),'M','Ninguna','Bachillerato','Agricultor',2,
             False,'Centro',pvd1,'','3112345678'),
            ('CC','10943103','María','Fernanda','Guerrero','Ospina',
             date(1992,7,22),'F','Ninguna','Universitario','Empleada',2,
             False,'Centro',pvd1,'mfguerrero@gmail.com','3123456789'),
            ('CC','10943104','Pedro','Antonio','Quintero','García',
             date(1965,8,12),'M','Ninguna','Primaria','Independiente',1,
             False,'Centro',pvd1,'','3134567890'),
            ('TI','10943105','Valentina','Andrea','Giraldo','Arenas',
             date(2008,2,28),'F','Ninguna','Bachillerato','Estudiante',1,
             False,'Centro',pvd1,'vgiraldo@gmail.com','3145678901'),
            ('CC','10943112','Andrés','Felipe','Montoya','Acosta',
             date(1995,8,23),'M','Ninguna','Técnico/Tecnólogo','Empleado',1,
             False,'Centro',pvd1,'andres.montoya@gmail.com','3212345678'),
            ('CC','10943114','Diego','Alejandro','Serna','Mejía',
             date(2000,7,4),'M','Ninguna','Técnico/Tecnólogo','Desempleado',1,
             False,'Centro',pvd1,'dserna@gmail.com','3234567890'),
            ('CC','10943116','Rosa','Elena','Patiño','Cruz',
             date(1958,3,14),'F','Ninguna','Primaria','Ama de casa',1,
             True,'Centro',pvd1,'','3201111111'),
            ('CC','10943117','Carlos','Arturo','Benítez','Ríos',
             date(1982,9,9),'M','Afrodescendiente','Universitario','Docente',3,
             False,'Centro',pvd1,'cbenitez@col.edu.co','3209876543'),
            ('CC','10943118','Luisa','Camila','Toro','Salinas',
             date(2003,5,20),'F','Ninguna','Bachillerato','Estudiante',2,
             False,'Centro',pvd1,'ltoro@gmail.com','3218765432'),
            ('CC','10943119','Jorge','Iván','Zapata','Muñoz',
             date(1970,12,3),'M','Ninguna','Bachillerato','Comerciante',2,
             False,'Centro',pvd1,'','3227654321'),
            ('CC','10943120','Patricia','del Carmen','Aguirre','Henao',
             date(1964,6,18),'F','Indígena','Primaria','Pensionada',1,
             False,'Centro',pvd1,'','3236543210'),
            ('CC','10943121','Samuel','','Londoño','Cano',
             date(1998,1,10),'M','Ninguna','Técnico/Tecnólogo','Independiente',2,
             False,'Centro',pvd1,'slondono@gmail.com','3245432109'),
            ('CC','10943122','Natalia','Paola','Cardona','Vélez',
             date(1990,8,25),'F','Ninguna','Universitario','Empleada',3,
             False,'Centro',pvd1,'npcardona@empresa.com','3254321098'),
            ('CC','10943123','Héctor','Fabio','Restrepo','Álvarez',
             date(1945,2,14),'M','Ninguna','Ninguno','Pensionado',1,
             True,'Centro',pvd1,'','3263210987'),
            # PVD2 – Antonio Nariño
            ('CC','10943106','Luis','Fernando','Herrera','Cano',
             date(1987,6,18),'M','Ninguna','Técnico/Tecnólogo','Independiente',2,
             False,'Antonio Nariño',pvd2,'lfherrera@hotmail.com','3156789012'),
            ('CC','10943107','Claudia','Patricia','Salazar','Hoyos',
             date(1975,9,3),'F','Ninguna','Universitario','Docente',3,
             False,'Antonio Nariño',pvd2,'cpsalazar@gmail.com','3167890123'),
            ('TI','10943108','Jhon','Alexander','Bermúdez','Ruiz',
             date(2007,12,14),'M','Ninguna','Bachillerato','Estudiante',1,
             False,'Antonio Nariño',pvd2,'','3178901234'),
            ('CC','10943109','Sofía','Alejandra','Muñoz','Torres',
             date(1998,1,25),'F','Ninguna','Universitario','Desempleada',1,
             False,'Antonio Nariño',pvd2,'sofia.munoz@gmail.com','3189012345'),
            ('CC','10943110','Ricardo','Emilio','Córdoba','Patiño',
             date(1955,10,7),'M','Afrodescendiente','Primaria','Pensionado',1,
             True,'Antonio Nariño',pvd2,'','3190123456'),
            ('CC','10943111','Gloria','Inés','Ramírez','Castro',
             date(1960,5,19),'F','Ninguna','Bachillerato','Ama de casa',2,
             False,'Antonio Nariño',pvd2,'','3201234567'),
            ('CC','10943113','Paola','Andrea','Ocampo','Villa',
             date(1988,3,11),'F','Indígena','Universitario','Enfermera',2,
             False,'Antonio Nariño',pvd2,'paola.ov@yahoo.com','3223456789'),
            ('CC','10943115','Lorena','Catalina','Zapata','Bedoya',
             date(1983,12,1),'F','Ninguna','Bachillerato','Comerciante',2,
             False,'Antonio Nariño',pvd2,'lorena.zb@gmail.com','3245678901'),
            ('CC','10943124','William','Alexander','Mosquera','Perea',
             date(1972,4,5),'M','Afrodescendiente','Técnico/Tecnólogo','Empleado',2,
             False,'Antonio Nariño',pvd2,'wmosquera@gmail.com','3251234567'),
            ('CC','10943125','Isabel','Cristina','Palomino','Díaz',
             date(2001,7,19),'F','Ninguna','Bachillerato','Estudiante',1,
             False,'Antonio Nariño',pvd2,'icpalomino@gmail.com','3259876543'),
            ('CC','10943126','Edwin','','Gutiérrez','Mena',
             date(1993,11,28),'M','Ninguna','Universitario','Independiente',2,
             False,'Antonio Nariño',pvd2,'egutierrez@gmail.com','3258765432'),
            ('CC','10943127','Marcela','','Flórez','Rivas',
             date(1969,8,7),'F','Ninguna','Bachillerato','Ama de casa',1,
             False,'Antonio Nariño',pvd2,'','3257654321'),
            ('TI','10943128','Kevin','Stiven','Mina','Lozano',
             date(2009,3,22),'M','Afrodescendiente','Bachillerato','Estudiante',1,
             False,'Antonio Nariño',pvd2,'','3256543210'),
            ('CC','10943129','Diana','Marcela','Aristizábal','Vélez',
             date(1986,10,12),'F','Ninguna','Universitario','Empleada',3,
             False,'Antonio Nariño',pvd2,'daristizabal@empresa.com','3255432109'),
            ('CC','10943130','Germán','Augusto','Cifuentes','Moreno',
             date(1950,6,30),'M','Ninguna','Primaria','Pensionado',1,
             True,'Antonio Nariño',pvd2,'','3254321098'),
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
                    municipio='Bugalagrande',
                    direccion=f'Calle {num[-2:]} No. 5-{num[-1:]}0, {barrio}',
                )
            )
            self._ok(f'{pn} {pa}') if c else self._skip(f'{pn} {pa}')
            ciudadanos.append(obj)

        return ciudadanos

    # ------------------------------------------------------------------
    # RECURSOS (inventario completo para ambos PVDs)
    # ------------------------------------------------------------------
    def _crear_recursos(self, pvd1, pvd2):
        self._titulo('Recursos tecnológicos')
        datos = [
            # PVD1
            (pvd1, 'Computador de Mesa',  'PC-RA-01', 'A'),
            (pvd1, 'Computador de Mesa',  'PC-RA-02', 'A'),
            (pvd1, 'Computador de Mesa',  'PC-RA-03', 'A'),
            (pvd1, 'Computador de Mesa',  'PC-RA-04', 'A'),
            (pvd1, 'Portátil',            'LAP-RA-01', 'A'),
            (pvd1, 'Portátil',            'LAP-RA-02', 'A'),
            (pvd1, 'Impresora',           'IMP-RA-01', 'A'),
            (pvd1, 'Escáner',             'ESC-RA-01', 'A'),
            (pvd1, 'Proyector',           'PRY-RA-01', 'A'),
            (pvd1, 'Tableta',             'TAB-RA-01', 'A'),
            # PVD2
            (pvd2, 'Computador de Mesa',  'PC-AN-01', 'A'),
            (pvd2, 'Computador de Mesa',  'PC-AN-02', 'A'),
            (pvd2, 'Computador de Mesa',  'PC-AN-03', 'A'),
            (pvd2, 'Portátil',            'LAP-AN-01', 'A'),
            (pvd2, 'Portátil',            'LAP-AN-02', 'A'),
            (pvd2, 'Impresora',           'IMP-AN-01', 'A'),
            (pvd2, 'Proyector',           'PRY-AN-01', 'A'),
            (pvd2, 'Tableta',             'TAB-AN-01', 'A'),
            (pvd2, 'Tableta',             'TAB-AN-02', 'A'),
            (pvd2, 'Cámara Web',          'CAM-AN-01', 'A'),
        ]
        recursos = []
        for pvd, tipo, codigo, estado in datos:
            r, c = Recurso.objects.get_or_create(
                codigo=codigo,
                defaults={'punto_vive_digital': pvd, 'tipo': tipo, 'estado': estado}
            )
            self._ok(f'{codigo} – {tipo}') if c else self._skip(codigo)
            recursos.append(r)

        # Recurso real histórico si existe
        r_real, c = Recurso.objects.get_or_create(
            codigo='626410',
            defaults={'punto_vive_digital': pvd1, 'tipo': 'Computador de Mesa', 'estado': 'A'}
        )
        if c:
            self._ok('Recurso 626410 (histórico)')
        return recursos

    # ------------------------------------------------------------------
    # PRÉSTAMOS
    # ------------------------------------------------------------------
    def _crear_prestamos(self, recursos, ciudadanos):
        self._titulo('Préstamos de recursos')
        # (recurso_idx, ciudadano_idx, dias_atras_entrega, dias_atras_dev|None, obs)
        datos = [
            (0, 0,  5, 4,    'Préstamo para trámite SISBEN en línea'),
            (1, 1,  3, 2,    'Uso para capacitación de ofimática básica'),
            (2, 2,  1, None, 'Préstamo activo – pendiente devolución'),
            (3, 3, 10, 8,    'Consulta formulario DIAN'),
            (4, 5,  7, 5,    'Apoyo inscripción curso SENA virtual'),
            (5, 6,  2, None, 'Préstamo activo – uso académico'),
            (10, 15, 6, 5,   'Trámite afiliación EPS en línea'),
            (11, 16, 4, 3,   'Capacitación uso de correo electrónico'),
            (12, 17, 2, 1,   'Uso en taller de redes sociales'),
            (13, 18, 1, None,'Préstamo activo – búsqueda de empleo'),
        ]
        prestamos = []
        for rec_idx, ciu_idx, dias_ent, dias_dev, obs in datos:
            if rec_idx >= len(recursos) or ciu_idx >= len(ciudadanos):
                continue
            fecha_ent = HOY - timedelta(days=dias_ent)
            fecha_dev = HOY - timedelta(days=dias_dev) if dias_dev is not None else None
            p = PrestamoRecurso.objects.create(
                recurso=recursos[rec_idx],
                ciudadano=ciudadanos[ciu_idx],
                fecha_entrega=timezone.make_aware(datetime.combine(fecha_ent, time(9, 0))),
                fecha_devolucion=timezone.make_aware(datetime.combine(fecha_dev, time(17, 0))) if fecha_dev else None,
                observaciones=obs,
            )
            self._ok(f'Préstamo {ciudadanos[ciu_idx].primer_nombre} – {fecha_ent}')
            prestamos.append(p)
        return prestamos

    # ------------------------------------------------------------------
    # ATENCIONES (distribuidas en los últimos 4 meses para gráficos)
    # ------------------------------------------------------------------
    def _crear_atenciones(self, pvd1, pvd2, ciudadanos, prestamos, julia, lady):
        self._titulo('Atenciones a ciudadanos (4 meses de historia)')

        atenciones = []

        # Datos de atenciones pasadas (para poblar gráfico mensual)
        # (pvd, ciu_idx, dias_atras, h_ini, h_fin, estado, obs, operador)
        datos_historicos = [
            # --- MARZO (hace ~90 días) ---
            (pvd1,  0, 90, time(8,0),  time(8,45),  'F', 'Trámite en línea SISBEN completado.', julia),
            (pvd1,  1, 89, time(9,0),  time(9,30),  'F', 'Asesoría plataforma Supernotariado.', julia),
            (pvd1,  2, 88, time(10,0), time(10,20), 'F', 'Acceso a internet y correo electrónico.', julia),
            (pvd1,  3, 87, time(11,0), time(11,45), 'F', 'Consulta trámite pensional Colpensiones.', julia),
            (pvd1,  4, 86, time(14,0), time(14,30), 'F', 'Inscripción a curso de ofimática básica.', julia),
            (pvd1,  5, 85, time(8,30), time(9,0),   'F', 'Impresión de documentos legales.', julia),
            (pvd2, 15, 90, time(8,0),  time(8,50),  'F', 'Certificado de estratificación en línea.', lady),
            (pvd2, 16, 89, time(9,30), time(10,15), 'F', 'Capacitación uso de correo electrónico.', lady),
            (pvd2, 17, 88, time(10,30),time(11,0),  'F', 'Acceso a internet búsqueda académica.', lady),
            (pvd2, 18, 87, time(13,0), time(13,45), 'F', 'Asesoría banca virtual Bancolombia.', lady),
            (pvd2, 19, 86, time(14,0), time(14,30), 'C', 'Cancelada: falla de conexión.', lady),
            (pvd2, 20, 85, time(15,0), time(15,30), 'F', 'Impresión hoja de vida y envío por correo.', lady),
            # --- ABRIL (hace ~60 días) ---
            (pvd1,  6, 62, time(8,0),  time(8,45),  'F', 'Trámite DIAN – consulta RUT.', julia),
            (pvd1,  7, 61, time(9,0),  time(9,30),  'F', 'Apoyo inscripción curso SENA virtual.', julia),
            (pvd1,  8, 60, time(10,0), time(10,30), 'F', 'Navegación libre, búsqueda de empleo.', julia),
            (pvd1,  9, 59, time(11,0), time(12,0),  'F', 'Uso de correo institucional.', julia),
            (pvd1, 10, 58, time(14,0), time(14,45), 'F', 'Asesoría manejo redes sociales.', julia),
            (pvd1, 11, 57, time(15,0), time(15,30), 'C', 'Cancelada: ciudadano no regresó.', julia),
            (pvd2, 21, 62, time(8,0),  time(8,30),  'F', 'Trámite afiliación EPS en línea.', lady),
            (pvd2, 22, 61, time(9,0),  time(9,45),  'F', 'Certificado de ingresos y retenciones.', lady),
            (pvd2, 23, 60, time(10,0), time(10,30), 'F', 'Acceso a internet y descarga de formularios.', lady),
            (pvd2, 24, 59, time(11,0), time(11,30), 'F', 'Videollamada con familiar en el exterior.', lady),
            (pvd2, 25, 58, time(13,0), time(14,0),  'F', 'Capacitación básica en Word.', lady),
            (pvd2, 26, 57, time(14,30),time(15,0),  'F', 'Trámite consulta historia laboral.', lady),
            # --- MAYO (hace ~30 días) ---
            (pvd1, 12, 32, time(8,0),  time(8,30),  'F', 'Asesoría sistema de turnos alcaldía.', julia),
            (pvd1, 13, 31, time(9,15), time(10,0),  'F', 'Navegación libre, búsqueda académica.', julia),
            (pvd1, 14, 30, time(10,30),time(11,15), 'F', 'Inscripción en línea diplomado SENA.', julia),
            (pvd1,  0, 29, time(14,0), time(14,30), 'F', 'Segunda visita trámite SISBEN.', julia),
            (pvd1,  2, 28, time(15,0), time(15,30), 'F', 'Correo y documentos adjuntos.', julia),
            (pvd1,  4, 27, time(8,30), time(9,0),   'C', 'Cancelada: corte de energía.', julia),
            (pvd2, 15, 32, time(8,0),  time(8,45),  'F', 'Trámite matrícula hijo en colegio.', lady),
            (pvd2, 16, 31, time(9,0),  time(9,30),  'F', 'Actualización datos EPS Sura.', lady),
            (pvd2, 27, 30, time(10,0), time(10,45), 'F', 'Consulta plataforma Colombia Aprende.', lady),
            (pvd2, 28, 29, time(11,0), time(11,30), 'F', 'Trámite certificado Cámara de Comercio.', lady),
            (pvd2, 29, 28, time(13,0), time(13,45), 'F', 'Asesoría declaración de renta.', lady),
            (pvd2, 17, 27, time(14,0), time(14,30), 'F', 'Uso internet y redes sociales.', lady),
            # --- JUNIO (esta semana y días recientes) ---
            (pvd1,  1, 10, time(8,0),  time(8,45),  'F', 'Trámite en línea SISBEN actualización datos.', julia),
            (pvd1,  3, 8,  time(9,0),  time(9,30),  'F', 'Asesoría Supernotariado consulta escrituras.', julia),
            (pvd1,  6, 6,  time(10,0), time(10,20), 'F', 'Ciudadana solicita acceso a internet.', julia),
            (pvd1,  8, 4,  time(10,30),time(11,0),  'F', 'Consulta trámite pensional Colpensiones.', julia),
            (pvd1, 10, 3,  time(8,30), time(9,0),   'F', 'Impresión de documentos legales.', julia),
            (pvd1, 12, 2,  time(9,15), time(10,0),  'F', 'Navegación libre, búsqueda de empleo.', julia),
            (pvd1, 13, 1,  time(10,30),time(11,0),  'F', 'Apoyo trámite formulario DIAN.', julia),
            (pvd1,  0, 0,  time(8,0),  time(8,45),  'P', 'En atención – solicita correo Gmail.', julia),
            (pvd1,  2, 0,  time(9,0),  time(9,45),  'P', 'En atención – trámite SISBEN.', julia),
            (pvd2, 18, 10, time(8,0),  time(8,50),  'F', 'Certificado de estratificación en línea.', lady),
            (pvd2, 20, 8,  time(9,30), time(10,15), 'F', 'Capacitación uso de correo electrónico.', lady),
            (pvd2, 22, 6,  time(10,30),time(11,0),  'F', 'Acceso internet búsqueda académica.', lady),
            (pvd2, 24, 4,  time(8,0),  time(8,30),  'F', 'Trámite afiliación EPS en línea.', lady),
            (pvd2, 26, 3,  time(13,0), time(13,45), 'F', 'Asesoría banca virtual.', lady),
            (pvd2, 27, 2,  time(9,0),  time(9,30),  'F', 'Impresión hoja de vida y envío por correo.', lady),
            (pvd2, 28, 1,  time(14,0), time(14,30), 'F', 'Consulta plataforma Colombia Aprende.', lady),
            (pvd2, 15, 0,  time(8,0),  time(8,45),  'P', 'En atención – trámite matrícula.', lady),
            (pvd2, 16, 0,  time(9,30), None,        'P', 'En atención – acceso a internet.', lady),
        ]

        for pvd, ci, dias, hi, hf, estado, obs, op in datos_historicos:
            if ci >= len(ciudadanos):
                continue
            fecha = HOY - timedelta(days=dias)
            a = Atencion.objects.create(
                punto_vive_digital=pvd,
                ciudadano=ciudadanos[ci],
                operador=op,
                fecha=fecha,
                hora_inicio=hi,
                hora_fin=hf,
                estado=estado,
                observaciones=obs,
            )
            atenciones.append(a)

        self._ok(f'{len(atenciones)} atenciones creadas')
        return atenciones

    # ------------------------------------------------------------------
    # SERVICIOS
    # ------------------------------------------------------------------
    def _crear_servicios(self, atenciones):
        self._titulo('Servicios por atención')
        servicios_tipos = [
            ('Trámite en Línea',       'Trámites digitales',   'S'),
            ('Asesoría Tecnológica',   'Asesoría',             'N'),
            ('Acceso a Internet',      'Conectividad',         'S'),
            ('Impresión de Documentos','Impresión/Escaneo',    'S'),
            ('Formación Digital',      'Formación',            'N'),
            ('Trámite en Línea',       'Trámites digitales',   'S'),
            ('Navegación Libre',       'Conectividad',         'S'),
            ('Asesoría Tecnológica',   'Asesoría',             'N'),
            ('Correo Electrónico',     'Formación',            'S'),
            ('Trámite en Línea',       'Trámites digitales',   'S'),
        ]
        count = 0
        for i, atencion in enumerate(atenciones):
            if atencion.estado in ('F', 'P'):
                nombre, tipo, req = servicios_tipos[i % len(servicios_tipos)]
                Servicio.objects.create(
                    atencion=atencion,
                    nombre=nombre,
                    tipo=tipo,
                    descripcion=atencion.observaciones[:100] if atencion.observaciones else nombre,
                    requiere_equipo=req,
                    estado='A' if atencion.estado == 'P' else 'F',
                )
                count += 1
        self._ok(f'{count} servicios creados')

    # ------------------------------------------------------------------
    # SATISFACCIÓN
    # ------------------------------------------------------------------
    def _crear_satisfaccion(self, atenciones):
        self._titulo('Encuestas de satisfacción')
        calificaciones = [5, 5, 4, 5, 5, 4, 3, 5, 5, 4, 5, 5, 4, 5, 3, 5, 4, 5, 5, 4]
        respuestas_por_calificacion = {
            5: ('E', 'E', 'E', 'E', 'E'),
            4: ('E', 'B', 'E', 'B', 'E'),
            3: ('B', 'B', 'B', 'B', 'M'),
        }
        comentarios = [
            'Excelente atención, muy amable el personal.',
            'Me ayudaron a resolver mi trámite rápidamente.',
            'Buen servicio, aunque la conexión era un poco lenta.',
            'Muy completo el servicio, volveré pronto.',
            'El administrador fue muy paciente y claro.',
            'Bien, aunque esperé un poco de tiempo.',
            'Todo perfecto, seguiré usando el Punto Vive Digital.',
            'Muy buena gestión del trámite en línea.',
            'El servicio fue muy bueno, me resolvieron todo.',
            'Excelente, me solucionaron el problema enseguida.',
        ]
        finalizadas = [a for a in atenciones if a.estado == 'F']
        count = 0
        for i, a in enumerate(finalizadas):
            r = respuestas_por_calificacion[calificaciones[i % len(calificaciones)]]
            Satisfaccion.objects.create(
                atencion=a,
                tiempo_espera=r[0],
                atencion_servidor=r[1],
                satisfaccion_servicio=r[2],
                informacion_recibida=r[3],
                comodidad_instalaciones=r[4],
                comentario=comentarios[i % len(comentarios)],
                fecha=timezone.make_aware(
                    datetime.combine(a.fecha, time(17, 0))
                ),
            )
            count += 1
        self._ok(f'{count} encuestas de satisfacción creadas')

    # ------------------------------------------------------------------
    # HABILITACIONES DE SALA
    # ------------------------------------------------------------------
    def _crear_habilitaciones(self, pvd1, pvd2, julia, lady):
        self._titulo('Habilitaciones de sala')

        def sala(pvd, nombre):
            return Sala.objects.get(punto_vive_digital=pvd, nombre=nombre)

        s1_nav = sala(pvd1, 'Sala de Navegación')
        s1_cap = sala(pvd1, 'Sala de Capacitación')
        s2_nav = sala(pvd2, 'Sala de Navegación')
        s2_cap = sala(pvd2, 'Sala de Capacitación')

        datos = [
            # Pasadas (históricas)
            (s1_cap, 'CAP', HOY - timedelta(days=30), time(8,0),  time(12,0),
             'Grupo Adultos Mayores Barrio Centro',
             'Taller de habilidades digitales básicas', 15, 'F', julia),
            (s1_nav, 'NAV', HOY - timedelta(days=20), time(8,0),  time(12,0),
             'Comunidad general',
             'Navegación libre mañana', 10, 'F', julia),
            (s1_cap, 'TRAM', HOY - timedelta(days=14), time(9,0), time(11,0),
             'Usuarios trámites en línea',
             'Atención de trámites en línea: SISBEN, EPS, DIAN', 8, 'F', julia),
            (s1_cap, 'CAP', HOY - timedelta(days=7),  time(14,0), time(17,0),
             'Jóvenes 15-25 años',
             'Taller de redes sociales y seguridad digital', 20, 'F', julia),
            (s2_cap, 'CAP', HOY - timedelta(days=25), time(8,0),  time(12,0),
             'Mujeres cabeza de hogar',
             'Taller de emprendimiento digital y comercio electrónico', 18, 'F', lady),
            (s2_nav, 'NAV', HOY - timedelta(days=10), time(13,0), time(17,0),
             'Comunidad general',
             'Navegación libre tarde', 8, 'F', lady),
            # Actuales
            (s1_cap, 'CAP', HOY,  time(8,0),  time(12,0),
             'Grupo Adultos Mayores Barrio Centro',
             'Continuación taller habilidades digitales – módulo 2', 15, 'C', julia),
            (s1_nav, 'NAV', HOY,  time(13,0), time(17,0),
             'Comunidad general',
             'Navegación libre tarde', 10, 'E', julia),
            (s2_cap, 'CAP', HOY,  time(14,0), time(17,0),
             'Jóvenes barrio Antonio Nariño',
             'Formación en ofimática – Word básico', 18, 'E', lady),
            # Próximas
            (s1_cap, 'CAP', HOY + timedelta(days=2),  time(8,0),  time(12,0),
             'Docentes IE Rafael Pombo',
             'Taller TIC para docentes: herramientas Google', 12, 'P', julia),
            (s2_cap, 'CONF', HOY + timedelta(days=3), time(10,0), time(12,0),
             'Alcaldía de Bugalagrande',
             'Reunión de seguimiento contrato CD-224-2026', 6, 'P', lady),
            (s2_nav, 'EXAM', HOY + timedelta(days=5), time(8,0),  time(10,0),
             'Estudiantes SENA',
             'Examen de certificación competencias digitales SENA', 8, 'P', lady),
        ]
        count = 0
        for sala_obj, tipo, fecha, hi, hf, sol, prop, cap, estado, reg in datos:
            HabilitacionSala.objects.create(
                sala=sala_obj, tipo_uso=tipo, fecha=fecha,
                hora_inicio=hi, hora_fin=hf,
                solicitante=sol, proposito=prop,
                capacidad_requerida=cap, estado=estado,
                registrado_por=reg,
            )
            count += 1
        self._ok(f'{count} habilitaciones de sala creadas')

    # ------------------------------------------------------------------
    # CURSOS / TALLERES
    # ------------------------------------------------------------------
    def _crear_cursos(self, pvd1, pvd2, julia, lady):
        self._titulo('Cursos y talleres')
        datos = [
            (pvd1, 'Ofimática Básica: Word y Excel',
             'Formación en procesador de texto y hoja de cálculo dirigida a personas sin experiencia previa en computadores.',
             'P', 'Adultos y jóvenes mayores de 15 años',
             HOY - timedelta(days=14), HOY + timedelta(days=7), 'AC', julia),

            (pvd1, 'Trámites Digitales del Estado Colombiano',
             'Apoyo para realizar trámites ante SISBEN, DIAN, Colpensiones y EPS desde casa usando internet.',
             'P', 'Ciudadanos en general',
             HOY - timedelta(days=45), HOY - timedelta(days=18), 'FI', julia),

            (pvd1, 'Emprendimiento Digital para Mujeres',
             'Curso práctico sobre redes sociales, marketplace y herramientas digitales para impulsar negocios locales.',
             'P', 'Mujeres emprendedoras mayores de 18 años',
             HOY + timedelta(days=7), HOY + timedelta(days=28), 'PL', julia),

            (pvd2, 'Seguridad Digital y Redes Sociales',
             'Aprende a proteger tu información personal en internet y a usar las redes sociales de forma segura y responsable.',
             'P', 'Jóvenes de 12 a 25 años',
             HOY - timedelta(days=7), HOY + timedelta(days=14), 'AC', lady),

            (pvd2, 'Internet para Adultos Mayores',
             'Navegación básica, correo electrónico y videollamadas para personas mayores de 60 años que quieran conectarse con su familia.',
             'P', 'Adultos mayores de 60 años',
             HOY - timedelta(days=30), HOY - timedelta(days=2), 'FI', lady),

            (pvd2, 'Ciudadanía Digital y Gobierno en Línea',
             'Conoce y usa los servicios del Estado en línea: portal GOV.CO, ventanilla única y servicios de la Alcaldía.',
             'P', 'Ciudadanos en general',
             HOY + timedelta(days=14), HOY + timedelta(days=35), 'PL', lady),
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
    # SESIONES, INSCRIPCIONES Y ASISTENCIAS
    # ------------------------------------------------------------------
    def _crear_sesiones_e_inscripciones(self, cursos, ciudadanos, julia, lady):
        self._titulo('Sesiones de cursos')

        sesiones_por_curso = {
            0: [  # Ofimática Básica (AC)
                (1, HOY - timedelta(days=14), time(8,0),  time(10,0), 'Introducción al computador', 'Partes del computador, encendido y manejo del ratón y teclado'),
                (2, HOY - timedelta(days=12), time(8,0),  time(10,0), 'Microsoft Word básico',       'Crear, guardar y dar formato a documentos de texto'),
                (3, HOY - timedelta(days=7),  time(8,0),  time(10,0), 'Word avanzado',               'Tablas, imágenes, estilos y revisión ortográfica'),
                (4, HOY + timedelta(days=1),  time(8,0),  time(10,0), 'Introducción a Excel',        'Hojas de cálculo, fórmulas básicas y gráficos'),
                (5, HOY + timedelta(days=7),  time(8,0),  time(10,0), 'Excel aplicado',              'Presupuestos, tablas dinámicas y formatos condicionales'),
            ],
            1: [  # Trámites Digitales (FI)
                (1, HOY - timedelta(days=45), time(14,0), time(16,0), 'SISBEN en línea',    'Consulta puntaje y actualización de datos'),
                (2, HOY - timedelta(days=38), time(14,0), time(16,0), 'DIAN y MUISCA',      'Consulta RUT y presentación de declaración de renta'),
                (3, HOY - timedelta(days=31), time(14,0), time(16,0), 'Colpensiones y EPS', 'Semanas cotizadas, afiliación y certificados'),
                (4, HOY - timedelta(days=24), time(14,0), time(16,0), 'Alcaldía en línea',  'Trámites en el portal de la Alcaldía de Bugalagrande'),
            ],
            3: [  # Seguridad Digital (AC)
                (1, HOY - timedelta(days=7),  time(15,0), time(17,0), 'Contraseñas seguras', 'Cómo crear y gestionar contraseñas fuertes'),
                (2, HOY + timedelta(days=1),  time(15,0), time(17,0), 'Redes sociales',      'Privacidad en Facebook e Instagram'),
                (3, HOY + timedelta(days=8),  time(15,0), time(17,0), 'Estafas digitales',   'Reconocer phishing, fraudes y noticias falsas'),
                (4, HOY + timedelta(days=14), time(15,0), time(17,0), 'Datos personales',    'Protección de datos y derechos HABEAS DATA'),
            ],
            4: [  # Internet para Adultos Mayores (FI)
                (1, HOY - timedelta(days=30), time(9,0),  time(11,0), 'Qué es internet',    'Navegadores, buscadores y páginas web'),
                (2, HOY - timedelta(days=23), time(9,0),  time(11,0), 'Correo electrónico', 'Crear cuenta Gmail y enviar correos'),
                (3, HOY - timedelta(days=16), time(9,0),  time(11,0), 'Videollamadas',      'WhatsApp y Google Meet con familiares'),
                (4, HOY - timedelta(days=2),  time(9,0),  time(11,0), 'Grado y clausura',   'Repaso general y certificación de participación'),
            ],
        }

        for ci, sesiones_data in sesiones_por_curso.items():
            if ci >= len(cursos):
                continue
            curso = cursos[ci]
            for num, fecha, hi, hf, tema, contenido in sesiones_data:
                s, c = SesionCurso.objects.get_or_create(
                    curso=curso, numero_sesion=num,
                    defaults=dict(fecha=fecha, hora_inicio=hi, hora_fin=hf,
                                  tema=tema, contenido=contenido)
                )
                self._ok(f'Sesión {num}: {tema}') if c else self._skip(f'Sesión {num}: {tema}')

        self._titulo('Inscripciones a cursos')
        # PVD1 ciudadanos: índices 0-14, PVD2: 15-29
        inscrip_map = {
            0: ([0, 1, 2, 4, 5, 6, 8, 9], julia),       # Ofimática Básica
            1: ([0, 3, 7, 10, 11, 12], julia),           # Trámites Digitales
            3: ([15, 17, 18, 21, 23, 24, 25], lady),     # Seguridad Digital
            4: ([16, 19, 20, 26, 27, 29], lady),         # Internet Adultos Mayores
        }
        for ci, (ciu_idxs, reg) in inscrip_map.items():
            if ci >= len(cursos):
                continue
            curso = cursos[ci]
            es_finalizado = curso.estado == 'FI'
            for idx in ciu_idxs:
                if idx >= len(ciudadanos):
                    continue
                ciudadano = ciudadanos[idx]
                estado = 'C' if es_finalizado else 'I'
                insc, c = InscripcionCurso.objects.get_or_create(
                    curso=curso, ciudadano=ciudadano,
                    defaults={'estado': estado, 'registrado_por': reg}
                )
                self._ok(f'{ciudadano.primer_nombre} → {curso.nombre[:40]}') if c else self._skip(f'{ciudadano.primer_nombre}')

        self._titulo('Asistencia a sesiones')
        asistencia_map = {
            1: {1: [0, 3, 7, 10, 11], 2: [0, 7, 10, 11], 3: [0, 3, 10, 12], 4: [0, 3, 11, 12]},
            4: {1: [16, 19, 20, 26, 27], 2: [16, 20, 26, 27], 3: [16, 19, 27, 29], 4: [16, 20, 26, 29]},
        }
        for ci, sesiones_asist in asistencia_map.items():
            if ci >= len(cursos):
                continue
            curso = cursos[ci]
            todos_idxs = inscrip_map.get(ci, ([], None))[0]
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
                    AsistenciaSesion.objects.get_or_create(
                        sesion=sesion, ciudadano=ciudadano,
                        defaults={'asistio': asistio}
                    )

        self._ok('Asistencias registradas')

    # ------------------------------------------------------------------
    # MANTENIMIENTOS
    # ------------------------------------------------------------------
    def _crear_mantenimientos(self, pvd1, pvd2, ofitic):
        self._titulo('Mantenimientos de equipos')
        datos = [
            (pvd1, 'PRV', HOY - timedelta(days=60),
             'Computadores de mesa PC-RA-01, PC-RA-02, PC-RA-03, PC-RA-04, Impresora IMP-RA-01',
             'Limpieza interna de unidades, actualización de sistema operativo y antivirus, revisión de teclados y ratones.',
             'Polvo acumulado en ventiladores. Software desactualizado en PC-RA-02.',
             'Revisión trimestral recomendada. PC-RA-02 requiere actualización de RAM.'),
            (pvd1, 'COR', HOY - timedelta(days=15),
             'Impresora IMP-RA-01',
             'Cambio de cartuchos de tinta (negro y color) y limpieza de cabezales de impresión.',
             'Cartuchos agotados. Calibración desajustada.',
             'Verificar nivel de tinta mensualmente. Solicitar cartuchos de repuesto.'),
            (pvd1, 'PRV', HOY + timedelta(days=15),
             'Todos los equipos de la Sala de Navegación y Sala de Capacitación',
             'Mantenimiento preventivo programado según cronograma trimestral CD-224-2026.',
             'Pendiente de realización.',
             'Programado. Coordinar con ofitic@bugalagrande.gov.co.'),
            (pvd2, 'PRV', HOY - timedelta(days=45),
             'Portátiles LAP-AN-01, LAP-AN-02, Computadores PC-AN-01, PC-AN-02, PC-AN-03',
             'Mantenimiento preventivo semestral: limpieza general, actualización antivirus y revisión de periféricos.',
             'Batería deficiente en LAP-AN-01. Sin otras novedades mayores.',
             'Reemplazar batería de LAP-AN-01 en próxima intervención.'),
            (pvd2, 'COR', HOY - timedelta(days=8),
             'Portátil LAP-AN-01',
             'Reemplazo de batería defectuosa. Instalación de nuevo módulo de batería certificado.',
             'Batería no cargaba. Duración menor a 5 minutos.',
             'Solicitar garantía al proveedor. Batería nueva instalada con éxito.'),
            (pvd2, 'PRV', HOY + timedelta(days=30),
             'Impresora IMP-AN-01, Proyector PRY-AN-01, Cámara Web CAM-AN-01',
             'Mantenimiento preventivo programado segundo semestre 2026.',
             'Pendiente de realización.',
             'Programado según cronograma. Coordinar con administradora PVD.'),
        ]
        count = 0
        for pvd, tipo, fecha, equipos, desc, hallazgos, acciones in datos:
            MantenimientoEquipo.objects.create(
                punto_vive_digital=pvd, tipo=tipo, fecha=fecha,
                equipos_intervenidos=equipos, descripcion=desc,
                hallazgos=hallazgos, acciones=acciones,
                realizado_por=ofitic,
            )
            count += 1
        self._ok(f'{count} mantenimientos creados')

    # ------------------------------------------------------------------
    # EVIDENCIAS (con imágenes generadas por Pillow)
    # ------------------------------------------------------------------
    def _crear_evidencias(self, pvd1, pvd2, julia, lady):
        self._titulo('Evidencias fotográficas')

        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            self.stdout.write('  [!!] Pillow no disponible – evidencias omitidas')
            return

        from django.conf import settings
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        if not media_root:
            self.stdout.write('  [!!] MEDIA_ROOT no configurado – evidencias omitidas')
            return

        datos = [
            (pvd1, 'Taller Adultos Mayores – Módulo Correo',
             'Ciudadanos adultos mayores del barrio Centro participando activamente en el taller de correo electrónico y videollamadas.',
             'CAP', HOY - timedelta(days=30), julia, '#1a4b8a', 'TALLER\nADULTOS MAYORES\nPVD Rafael Arias'),
            (pvd1, 'Jornada de Trámites en Línea',
             'Jornada especial de atención a ciudadanos para realización de trámites ante SISBEN, DIAN y Colpensiones.',
             'ACT', HOY - timedelta(days=20), julia, '#0d6e3f', 'JORNADA\nTRÁMITES\nEN LÍNEA'),
            (pvd1, 'Mantenimiento Preventivo Equipos',
             'Equipo técnico realizando mantenimiento preventivo a los computadores de la Sala de Navegación.',
             'MAN', HOY - timedelta(days=15), julia, '#7b2d00', 'MANTENIMIENTO\nPREVENTIVO\nEQUIPOS'),
            (pvd1, 'Curso Ofimática – Sesión Word',
             'Participantes del curso Ofimática Básica aprendiendo uso de Microsoft Word para elaboración de documentos.',
             'CAP', HOY - timedelta(days=12), julia, '#1a4b8a', 'CURSO\nOFIMÁTICA BÁSICA\nSesión 2 – Word'),
            (pvd1, 'Evento Día del Ciudadano Digital',
             'Evento especial en el marco del Día del Ciudadano Digital con participación de la comunidad y autoridades locales.',
             'EVE', HOY - timedelta(days=7), julia, '#6b1fa0', 'DÍA DEL\nCIUDADANO\nDIGITAL 2026'),
            (pvd2, 'Taller Jóvenes – Redes Sociales',
             'Jóvenes del barrio Antonio Nariño aprendiendo sobre privacidad, seguridad y uso responsable de redes sociales.',
             'CAP', HOY - timedelta(days=7), lady, '#1a4b8a', 'TALLER\nREDES SOCIALES\nPVD Antonio Nariño'),
            (pvd2, 'Atención Ciudadana – Internet Libre',
             'Ciudadanos haciendo uso de los equipos de la sala de navegación para trámites y consultas en línea.',
             'ACT', HOY - timedelta(days=5), lady, '#0d6e3f', 'ATENCIÓN\nCIUDADANA\nINTERNET LIBRE'),
            (pvd2, 'Capacitación Mujeres Emprendedoras',
             'Mujeres emprendedoras del municipio recibiendo formación en herramientas digitales para comercio electrónico.',
             'CAP', HOY - timedelta(days=3), lady, '#8a1a4b', 'FORMACIÓN\nMUJERES\nEMPRENDEDORAS'),
        ]

        count = 0
        for pvd, titulo, descripcion, categoria, fecha, reg, color, texto in datos:
            img_bytes = self._generar_imagen_demo(color, texto, titulo)
            nombre_archivo = f"demo_{titulo[:20].replace(' ', '_').replace('–','').replace('/','')}.jpg"
            evidencia = Evidencia(
                punto_vive_digital=pvd,
                titulo=titulo,
                descripcion=descripcion,
                categoria=categoria,
                fecha=fecha,
                registrado_por=reg,
            )
            evidencia.imagen.save(nombre_archivo, ContentFile(img_bytes), save=True)
            count += 1
            self._ok(f'Evidencia: {titulo[:50]}')

        self._ok(f'{count} evidencias con imágenes creadas')

    def _generar_imagen_demo(self, color_fondo, texto_centro, titulo):
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (800, 500), color=color_fondo)
        draw = ImageDraw.Draw(img)

        # Marco decorativo
        draw.rectangle([10, 10, 789, 489], outline='white', width=3)
        draw.rectangle([20, 20, 779, 479], outline='white', width=1)

        # Logo simulado (rectángulo superior)
        draw.rectangle([30, 30, 200, 80], fill='white')
        draw.text((40, 40), 'ALCALDÍA', fill=color_fondo)
        draw.text((40, 55), 'BUGALAGRANDE', fill=color_fondo)

        # Texto principal (centrado)
        lines = texto_centro.split('\n')
        y_start = 180
        for line in lines:
            # Texto grande simulado
            text_width = len(line) * 18
            x_pos = max(30, (800 - text_width) // 2)
            draw.text((x_pos, y_start), line, fill='white')
            y_start += 50

        # Pie de página
        draw.rectangle([0, 440, 800, 500], fill='rgba(0,0,0,128)')
        draw.text((30, 455), f'Puntos Vive Digital – Bugalagrande, Valle del Cauca', fill='white')
        draw.text((30, 470), 'Contrato CD-224-2026 | Municipio de Bugalagrande', fill='white')

        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85)
        return buf.getvalue()

    # ------------------------------------------------------------------
    # RESUMEN FINAL
    # ------------------------------------------------------------------
    def _imprimir_resumen(self, su, ofitic, julia, lady, pvd1, pvd2):
        from modulo_puntos.models import (
            Ciudadano, Recurso, PrestamoRecurso, Atencion,
            Servicio, Satisfaccion, Sala, HabilitacionSala,
            Curso, SesionCurso, InscripcionCurso, MantenimientoEquipo, Evidencia
        )
        self.stdout.write(self.style.WARNING(
            '\n  ╔══════════════════════════════════════════╗\n'
            '  ║     CREDENCIALES DE ACCESO               ║\n'
            '  ╠══════════════════════════════════════════╣\n'
            f'  ║  Superusuario  {su.username:<12}  (contraseña original)  ║\n'
            f'  ║  Admin TIC     ofitic       ofitic123         ║\n'
            f'  ║  Admin PVD 1   pvdjulia     pvd2026!          ║\n'
            f'  ║  Admin PVD 2   pvdlady      pvd2026!          ║\n'
            '  ╠══════════════════════════════════════════╣\n'
            '  ║     DATOS DE DEMO                        ║\n'
            '  ╠══════════════════════════════════════════╣\n'
            f'  ║  PVDs: 2  Salas: {Sala.objects.count():<3}  Recursos: {Recurso.objects.count():<3}         ║\n'
            f'  ║  Ciudadanos:    {Ciudadano.objects.count():<4}                        ║\n'
            f'  ║  Atenciones:    {Atencion.objects.count():<4}  Servicios: {Servicio.objects.count():<4}        ║\n'
            f'  ║  Satisfacción:  {Satisfaccion.objects.count():<4}  Préstamos: {PrestamoRecurso.objects.count():<4}       ║\n'
            f'  ║  Habilitaciones:{HabilitacionSala.objects.count():<4}  Cursos:    {Curso.objects.count():<4}       ║\n'
            f'  ║  Sesiones:      {SesionCurso.objects.count():<4}  Inscrip.:  {InscripcionCurso.objects.count():<4}       ║\n'
            f'  ║  Mantenimientos:{MantenimientoEquipo.objects.count():<4}  Evidencias:{Evidencia.objects.count():<4}       ║\n'
            '  ╚══════════════════════════════════════════╝\n'
        ))
