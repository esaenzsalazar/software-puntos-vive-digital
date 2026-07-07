"""
Comando de inicialización limpia para revisión técnica.

Limpia TODAS las tablas de la aplicación (respetando FK) y crea exactamente
los dos PVD oficiales con sus salas de capacidad definida.

Preserva intactas:
  - Tablas de autenticación de Django (auth_*)
  - El superusuario existente
  - Las definiciones de permisos (PermisoDefinicion)

Uso:
    python manage.py seed_pvd_inicial
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from modulo_puntos.models import (
    PuntoViveDigital, Sala, Ciudadano, Recurso, PrestamoRecurso,
    Atencion, Servicio, Satisfaccion, HabilitacionSala,
    Curso, SesionCurso, InscripcionCurso, AsistenciaSesion,
    MantenimientoEquipo, Evidencia, UserProfile,
    PermisoRol, PermisoUsuario,
)


# ---------------------------------------------------------------------------
# Datos canónicos de los PVD
# ---------------------------------------------------------------------------
PVD_DATA = [
    {
        'nombre':    'PVD EDIFICIO RAFAEL ARIAS',
        'direccion': 'Carrera 6 #4 - 65',
        'salas': [
            {'nombre': 'Sala de sistemas',      'capacidad': 20},
            {'nombre': 'Sala de capacitacion',  'capacidad': 20},
        ],
    },
    {
        'nombre':    'PVD COLEGIO ANTONIO NARIÑO',
        'direccion': 'Calle 9 # a 106, Cl. 5 #52',
        'salas': [
            {'nombre': 'Sala de capacitacion',    'capacidad': 11},
            {'nombre': 'Sala de internet',         'capacidad': 12},
            {'nombre': 'Sala de consulta rapida',  'capacidad':  1},
        ],
    },
]


class Command(BaseCommand):
    help = (
        'Limpia las tablas de la app y crea los dos PVD oficiales con sus salas. '
        'El superusuario y las tablas auth de Django no se tocan.'
    )

    # ── helpers de salida ───────────────────────────────────────────────────
    def _ok(self, msg):
        self.stdout.write(self.style.SUCCESS(f'  [OK]  {msg}'))

    def _del(self, msg):
        self.stdout.write(self.style.WARNING(f'  [DEL] {msg}'))

    def _titulo(self, msg):
        self.stdout.write(self.style.HTTP_INFO(f'\n>>> {msg}'))

    # ── entry point ─────────────────────────────────────────────────────────
    def add_arguments(self, parser):
        parser.add_argument(
            '--yes', action='store_true',
            help='Omite la confirmación interactiva (para uso en scripts).'
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                'Este comando borra todas las tablas de la app (ciudadanos, atenciones, '
                'recursos, etc.). Sólo puede ejecutarse con DJANGO_DEBUG=True. Abortado.'
            )

        db_name = connection.settings_dict.get('NAME')
        db_host = connection.settings_dict.get('HOST')
        if not options['yes']:
            self.stdout.write(self.style.WARNING(
                f'\nEste comando BORRARÁ TODOS los datos de la aplicación en la base '
                f'de datos "{db_name}" ({db_host}) (conserva superusuarios y tablas auth).\n'
            ))
            respuesta = input(f'Escribe el nombre de la base de datos ("{db_name}") para confirmar: ').strip()
            if respuesta != db_name:
                raise CommandError('Confirmación no coincide. Abortado.')

        self.stdout.write(self.style.WARNING(
            '\n================================================\n'
            '  SEED PVD INICIAL – Puntos Vive Digital\n'
            '================================================\n'
        ))

        self._limpiar()
        self._crear_pvds_y_salas()

        self.stdout.write(self.style.SUCCESS(
            '\n================================================\n'
            '  Inicialización completada correctamente.\n'
            '  Superusuarios preservados: '
            f'{User.objects.filter(is_superuser=True).count()}\n'
            '  PVDs creados:  2\n'
            '================================================\n'
        ))

    # ── FASE 1: limpieza ────────────────────────────────────────────────────
    def _limpiar(self):
        self._titulo('Limpiando datos de la aplicación')

        # Desactivar restricciones FK temporalmente (MariaDB / MySQL)
        with connection.cursor() as cur:
            cur.execute('SET FOREIGN_KEY_CHECKS = 0;')

        # Orden: hojas → raíces del árbol de FK
        _modelos_hoja = [
            (AsistenciaSesion,    'asistencias a sesiones'),
            (InscripcionCurso,    'inscripciones a cursos'),
            (SesionCurso,         'sesiones de cursos'),
            (Satisfaccion,        'encuestas de satisfacción'),
            (Servicio,            'servicios'),
            (Evidencia,           'evidencias'),
            (Atencion,            'atenciones'),
            (PrestamoRecurso,     'préstamos de recursos'),
            (HabilitacionSala,    'habilitaciones de sala'),
            (MantenimientoEquipo, 'mantenimientos de equipos'),
            (PermisoUsuario,      'permisos individuales de usuario'),
            (PermisoRol,          'permisos de rol'),
        ]
        for Model, label in _modelos_hoja:
            n = Model.objects.count()
            if n:
                Model.objects.all().delete()
                self._del(f'{n} {label}')

        _modelos_intermedios = [
            (Curso,       'cursos'),
            (Ciudadano,   'ciudadanos'),
            (Recurso,     'recursos'),
            (Sala,        'salas'),
            (UserProfile, 'perfiles de usuario'),
        ]
        for Model, label in _modelos_intermedios:
            n = Model.objects.count()
            if n:
                Model.objects.all().delete()
                self._del(f'{n} {label}')

        # Usuarios no-superuser
        n = User.objects.filter(is_superuser=False).count()
        if n:
            User.objects.filter(is_superuser=False).delete()
            self._del(f'{n} usuarios no-superuser')

        # PVDs (va al final porque tiene FK desde todas las demás tablas)
        n = PuntoViveDigital.objects.count()
        if n:
            PuntoViveDigital.objects.all().delete()
            self._del(f'{n} PVDs')

        with connection.cursor() as cur:
            cur.execute('SET FOREIGN_KEY_CHECKS = 1;')

        self._ok('Limpieza completada')

    # ── FASE 2: creación de PVDs y salas ───────────────────────────────────
    def _crear_pvds_y_salas(self):
        self._titulo('Creando PVDs y Salas')

        for pvd_data in PVD_DATA:
            pvd, creado = PuntoViveDigital.objects.get_or_create(
                nombre=pvd_data['nombre'],
                defaults={
                    'direccion': pvd_data['direccion'],
                    'estado': 'A',
                },
            )
            if not creado:
                pvd.direccion = pvd_data['direccion']
                pvd.estado = 'A'
                pvd.save(update_fields=['direccion', 'estado'])

            self._ok(f'PVD "{pvd.nombre}"  →  {pvd.direccion}')

            for sala_data in pvd_data['salas']:
                sala, _ = Sala.objects.get_or_create(
                    punto_vive_digital=pvd,
                    nombre=sala_data['nombre'],
                    defaults={
                        'capacidad': sala_data['capacidad'],
                        'estado': 'A',
                    },
                )
                # Actualiza capacidad aunque ya existiera
                sala.capacidad = sala_data['capacidad']
                sala.estado = 'A'
                sala.save(update_fields=['capacidad', 'estado'])

                self._ok(
                    f'  Sala "{sala.nombre}"'
                    f'  (cap. {sala.capacidad} persona{"s" if sala.capacidad != 1 else ""})'
                )
