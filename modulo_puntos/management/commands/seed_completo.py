"""
Carga datos completos sin borrar usuarios ni PVDs existentes.
Uso: python manage.py seed_completo
"""
import io
import random
from datetime import date, time, timedelta, datetime

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from modulo_puntos.models import (
    PuntoViveDigital, Ciudadano,
    Recurso, PrestamoRecurso, Atencion, Servicio, Satisfaccion,
    Sala, HabilitacionSala,
    Curso, SesionCurso, InscripcionCurso, AsistenciaSesion,
    MantenimientoEquipo, Evidencia,
)

HOY = date(2026, 6, 25)
RNG = random.Random(42)

# ── Listas de nombres colombianos realistas ───────────────────────────────────

NOMBRES_F = [
    'Ana','María','Laura','Claudia','Patricia','Gloria','Sandra','Marcela',
    'Luisa','Sofía','Valentina','Camila','Natalia','Andrea','Paola','Diana',
    'Lorena','Isabel','Mónica','Adriana','Rosa','Luz','Carmen','Esperanza',
    'Yolanda','Beatriz','Rocío','Liliana','Ángela','Olga','Marta','Teresa',
    'Blanca','Amparo','Pilar','Consuelo','Cecilia','Nohora','Flor','Viviana',
]
SEGUNDOS_F = [
    'Lucía','Fernanda','Alejandra','Cristina','del Carmen','Inés','Elena',
    'Paola','Catalina','Marcela','Andrea','Tatiana','Milena','Patricia','Juliana',
]
NOMBRES_M = [
    'Juan','Carlos','Luis','Jorge','Pedro','Andrés','Ricardo','Diego','Héctor',
    'Camilo','Felipe','Sebastián','Santiago','Alejandro','Mauricio','Fabio',
    'Wilson','Édgar','Germán','Hernán','Gustavo','Álvaro','Jairo','Nelson',
    'Óscar','Marco','Iván','Rodrigo','Edwin','Ernesto','Javier','Rafael',
    'Samuel','William','Jhon','Kevin','Steven','Brayan','Cristian','Daniel',
]
SEGUNDOS_M = [
    'Antonio','Emilio','Fernando','Augusto','Arturo','Alberto','Eduardo',
    'Enrique','Manuel','David','Alejandro','Felipe','Andrés','Ernesto','Iván',
]
PRIMER_APELLIDO = [
    'García','Martínez','López','González','Rodríguez','Hernández','Pérez',
    'Vargas','Morales','Ramírez','Torres','Flores','Reyes','Díaz','Cruz',
    'Guerrero','Castillo','Ramos','Sánchez','Ortiz','Jiménez','Rojas','Álvarez',
    'Córdoba','Patiño','Ospina','Salazar','Muñoz','Cano','Giraldo','Ríos',
    'Zapata','Castaño','Bedoya','Mejía','Montoya','Henao','Vélez','Arango',
    'Cifuentes','Mena','Mosquera','Lozano','Cardona','Palomino','Ocampo',
    'Flórez','Arias','Castro','Hoyos',
]
SEGUNDO_APELLIDO = [
    'Prada','Moreno','Acosta','Herrera','Medina','Ruiz','Aguilar','Romero',
    'Mendoza','Guzmán','Navarro','Ibáñez','Suárez','Molina','Serrano',
    'Blanco','Vega','Soto','Delgado','Fuentes','Cárdenas','Bermúdez',
    'Solano','Arenas','Salinas','Meza','Villa','Rivas','Mora','Peña',
    'Quintero','Bravo','Gallego','Escobar','Urrego','Parra','Sierra',
    'Bernal','Pulido','Gutiérrez',
]

ETNIAS = ['Ninguna','Ninguna','Ninguna','Ninguna','Ninguna',
          'Afrodescendiente','Indígena','Raizal']
EDUCACION = ['Ninguno','Primaria','Bachillerato','Técnico/Tecnólogo','Universitario','Posgrado']
OCUPACIONES = ['Estudiante','Empleado','Independiente','Comerciante','Agricultor',
               'Ama de casa','Pensionado','Desempleado','Docente','Enfermero/a',
               'Conductor','Construcción']
BARRIOS_PVD1 = ['Centro','El Bosque','La Esperanza','Villa del Río','Los Pinos','La Palmera']
BARRIOS_PVD2 = ['Antonio Nariño','El Jardín','San José','La Granja','Villa Esperanza','Los Álamos']
TIPOS_DOC = ['CC','CC','CC','CC','TI','CE']

TIPOS_SERVICIO = [
    ('Trámite en Línea',        'Trámites digitales', 'S'),
    ('Acceso a Internet',       'Conectividad',       'S'),
    ('Asesoría Tecnológica',    'Asesoría',           'N'),
    ('Impresión de Documentos', 'Impresión/Escaneo',  'S'),
    ('Correo Electrónico',      'Formación',          'S'),
    ('Formación Digital',       'Formación',          'N'),
    ('Navegación Libre',        'Conectividad',       'S'),
    ('Videoconferencia',        'Conectividad',       'S'),
    ('Escaneo de Documentos',   'Impresión/Escaneo',  'S'),
    ('Consulta Plataformas',    'Trámites digitales', 'N'),
]

OBS_ATENCIONES = [
    'Trámite en línea SISBEN completado exitosamente.',
    'Asesoría plataforma Supernotariado – consulta escrituras.',
    'Acceso a internet y creación de correo Gmail.',
    'Consulta trámite pensional Colpensiones.',
    'Inscripción en línea curso SENA virtual.',
    'Impresión de documentos legales y formularios.',
    'Navegación libre, búsqueda de empleo en portales.',
    'Actualización datos EPS Sura en línea.',
    'Trámite certificado Cámara de Comercio.',
    'Asesoría declaración de renta simplificada.',
    'Uso internet y redes sociales.',
    'Trámite afiliación EPS en línea.',
    'Certificado de ingresos y retenciones DIAN.',
    'Videollamada con familiar en el exterior.',
    'Capacitación básica en Word y Excel.',
    'Consulta historia laboral AFP.',
    'Trámite matrícula en institución educativa.',
    'Apoyo envío de hoja de vida por correo.',
    'Consulta plataforma Colombia Aprende.',
    'Gestión cuenta banca virtual Bancolombia.',
    'Impresión hoja de vida y carta de presentación.',
    'Trámite subsidio de vivienda en línea.',
    'Consulta convocatoria Icetex – crédito educativo.',
    'Acceso plataforma GOV.CO trámites alcaldía.',
    'Certificado de estratificación socioeconómica.',
    'Renovación libreta militar en línea.',
    'Descarga formularios Registraduría.',
    'Trámite consulta RUT plataforma DIAN.',
    'Asesoría uso redes sociales para negocio.',
    'Búsqueda información académica bases de datos.',
]

COMENTARIOS_SAT = [
    'Excelente atención, muy amable el personal.',
    'Me ayudaron a resolver mi trámite rápidamente.',
    'Buen servicio, aunque la conexión era lenta.',
    'Muy completo el servicio, volveré pronto.',
    'El administrador fue muy paciente y claro.',
    'Todo bien organizado y limpio.',
    'Me explicaron paso a paso, muy bueno.',
    'Muy buena gestión, resolví todo lo que necesitaba.',
    'Servicio excelente, lo recomiendo.',
    'Me solucionaron el problema enseguida.',
    'Buen servicio al ciudadano.',
    'El personal muy capacitado y amable.',
    'Un espacio muy bien dotado de tecnología.',
    'Esperé un poco pero valió la pena.',
    'Muy buena iniciativa del municipio.',
]


class Command(BaseCommand):
    help = 'Carga 100 ciudadanos por PVD y todos los datos de demo sin borrar usuarios'

    def _ok(self, msg):  self.stdout.write(self.style.SUCCESS(f'  [OK] {msg}'))
    def _info(self, msg): self.stdout.write(f'  [--] {msg}')
    def _titulo(self, msg): self.stdout.write(self.style.HTTP_INFO(f'\n>>> {msg}'))

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n=== SEED COMPLETO ===\n'))

        pvd1 = PuntoViveDigital.objects.get(pk=14)  # Rafael Arias (Edificio)
        pvd2 = PuntoViveDigital.objects.get(pk=15)  # Antonio Nariño (Colegio)
        lady    = User.objects.get(username='lserna')
        julia   = User.objects.get(username='jgonzalez')
        ofitic  = User.objects.get(username='ofitic')

        self._titulo(f'PVD 1: {pvd1.nombre}')
        self._titulo(f'PVD 2: {pvd2.nombre}')

        ciudadanos = self._crear_ciudadanos(pvd1, pvd2)
        recursos   = self._crear_recursos(pvd1, pvd2)
        prestamos  = self._crear_prestamos(recursos, ciudadanos)
        atenciones = self._crear_atenciones(pvd1, pvd2, ciudadanos, lady, julia)
        self._crear_servicios(atenciones)
        self._crear_satisfaccion(atenciones)
        self._crear_salas(pvd1, pvd2)
        self._crear_habilitaciones(pvd1, pvd2, lady, julia)
        cursos = self._crear_cursos(pvd1, pvd2, lady, julia)
        self._crear_sesiones_inscripciones(cursos, ciudadanos, lady, julia)
        self._crear_mantenimientos(pvd1, pvd2, ofitic)
        self._crear_evidencias(pvd1, pvd2, lady, julia)

        self._resumen()

    # ── CIUDADANOS ────────────────────────────────────────────────────────────
    def _crear_ciudadanos(self, pvd1, pvd2):
        self._titulo('Ciudadanos (100 por PVD)')

        def generar_lote(pvd, barrios, base_doc, cantidad):
            resultado = []
            for i in range(cantidad):
                genero = RNG.choice(['M', 'F'])
                if genero == 'F':
                    pnombre = RNG.choice(NOMBRES_F)
                    snombre = RNG.choice(SEGUNDOS_F + [''])
                else:
                    pnombre = RNG.choice(NOMBRES_M)
                    snombre = RNG.choice(SEGUNDOS_M + [''])

                papellido = RNG.choice(PRIMER_APELLIDO)
                sapellido = RNG.choice(SEGUNDO_APELLIDO)
                tipo_doc  = RNG.choice(TIPOS_DOC)
                num_doc   = str(base_doc + i)
                anio      = RNG.randint(1945, 2010)
                mes       = RNG.randint(1, 12)
                dia       = RNG.randint(1, 28)
                fnac      = date(anio, mes, dia)
                etnia     = RNG.choice(ETNIAS)
                edu       = RNG.choice(EDUCACION)
                ocu       = RNG.choice(OCUPACIONES)
                estrato   = RNG.randint(1, 3)
                disc      = RNG.random() < 0.08
                barrio    = RNG.choice(barrios)

                obj, created = Ciudadano.objects.get_or_create(
                    numero_documento=num_doc,
                    defaults=dict(
                        punto_vive_digital=pvd,
                        tipo_documento=tipo_doc,
                        primer_nombre=pnombre,
                        segundo_nombre=snombre,
                        primer_apellido=papellido,
                        segundo_apellido=sapellido,
                        fecha_nacimiento=fnac,
                        genero=genero,
                        etnia=etnia,
                        nivel_educativo=edu,
                        ocupacion=ocu,
                        estrato=estrato,
                        tiene_discapacidad=disc,
                        descripcion_discapacidad='Discapacidad física' if disc else '',
                        barrio=barrio,
                        estado='A',
                        municipio='Bugalagrande',
                        direccion=f'Calle {RNG.randint(1,20)} # {RNG.randint(1,15)}-{RNG.randint(10,99)}, {barrio}',
                        telefono=f'3{RNG.randint(10,29)}{RNG.randint(1000000,9999999)}',
                    )
                )
                resultado.append(obj)
                if i % 20 == 0:
                    self._info(f'{pvd.nombre[:20]} – {i+1}/{cantidad} ciudadanos...')
            return resultado

        c1 = generar_lote(pvd1, BARRIOS_PVD1, 20000000, 100)
        c2 = generar_lote(pvd2, BARRIOS_PVD2, 30000000, 100)
        self._ok(f'{len(c1)} ciudadanos en {pvd1.nombre}')
        self._ok(f'{len(c2)} ciudadanos en {pvd2.nombre}')
        return c1, c2

    # ── RECURSOS ──────────────────────────────────────────────────────────────
    def _crear_recursos(self, pvd1, pvd2):
        self._titulo('Recursos tecnológicos')
        datos = [
            # PVD1 – Rafael Arias
            (pvd1,'Computador de Mesa','PC-RA-01','A'),
            (pvd1,'Computador de Mesa','PC-RA-02','A'),
            (pvd1,'Computador de Mesa','PC-RA-03','A'),
            (pvd1,'Computador de Mesa','PC-RA-04','A'),
            (pvd1,'Computador de Mesa','PC-RA-05','A'),
            (pvd1,'Portátil',          'LAP-RA-01','A'),
            (pvd1,'Portátil',          'LAP-RA-02','A'),
            (pvd1,'Impresora',         'IMP-RA-01','A'),
            (pvd1,'Escáner',           'ESC-RA-01','A'),
            (pvd1,'Proyector',         'PRY-RA-01','A'),
            # PVD2 – Antonio Nariño
            (pvd2,'Computador de Mesa','PC-AN-01','A'),
            (pvd2,'Computador de Mesa','PC-AN-02','A'),
            (pvd2,'Computador de Mesa','PC-AN-03','A'),
            (pvd2,'Computador de Mesa','PC-AN-04','A'),
            (pvd2,'Portátil',          'LAP-AN-01','A'),
            (pvd2,'Portátil',          'LAP-AN-02','A'),
            (pvd2,'Impresora',         'IMP-AN-01','A'),
            (pvd2,'Proyector',         'PRY-AN-01','A'),
            (pvd2,'Tableta',           'TAB-AN-01','A'),
            (pvd2,'Tableta',           'TAB-AN-02','A'),
        ]
        recursos1, recursos2 = [], []
        for pvd, tipo, codigo, estado in datos:
            r, c = Recurso.objects.get_or_create(
                codigo=codigo,
                defaults={'punto_vive_digital': pvd, 'tipo': tipo, 'estado': estado}
            )
            if pvd == pvd1:
                recursos1.append(r)
            else:
                recursos2.append(r)
        self._ok(f'{len(recursos1)} recursos PVD1, {len(recursos2)} recursos PVD2')
        return recursos1, recursos2

    # ── PRÉSTAMOS ─────────────────────────────────────────────────────────────
    def _crear_prestamos(self, recursos_tuple, ciudadanos_tuple):
        self._titulo('Préstamos de recursos')
        r1, r2 = recursos_tuple
        c1, c2 = ciudadanos_tuple

        lotes = [
            (r1, c1, 15),  # 15 préstamos PVD1
            (r2, c2, 15),  # 15 préstamos PVD2
        ]
        prestamos = []
        obs_list = [
            'Trámite SISBEN en línea','Capacitación ofimática básica',
            'Uso académico','Búsqueda de empleo en portales',
            'Trámite DIAN – consulta RUT','Inscripción SENA virtual',
            'Uso correo electrónico','Formulario Registraduría',
            'Consulta historia laboral','Trámite EPS en línea',
            'Hoja de vida y postulación','Declaración de renta',
            'Taller redes sociales','Consulta GOV.CO','Banca virtual',
        ]
        for recursos, ciudadanos, n in lotes:
            r_disponibles = [r for r in recursos if r.estado == 'A']
            for i in range(n):
                dias_atras = RNG.randint(1, 60)
                devuelto   = RNG.random() < 0.75
                fecha_ent  = HOY - timedelta(days=dias_atras)
                fecha_dev  = fecha_ent + timedelta(days=RNG.randint(1, dias_atras)) if devuelto else None
                r = RNG.choice(r_disponibles)
                c = ciudadanos[RNG.randint(0, len(ciudadanos)-1)]
                p = PrestamoRecurso.objects.create(
                    recurso=r,
                    ciudadano=c,
                    fecha_entrega=timezone.make_aware(datetime.combine(fecha_ent, time(9,0))),
                    fecha_devolucion=timezone.make_aware(datetime.combine(fecha_dev, time(17,0))) if fecha_dev else None,
                    observaciones=RNG.choice(obs_list),
                )
                prestamos.append(p)
        self._ok(f'{len(prestamos)} préstamos creados')
        return prestamos

    # ── ATENCIONES ────────────────────────────────────────────────────────────
    def _crear_atenciones(self, pvd1, pvd2, ciudadanos_tuple, lady, julia):
        self._titulo('Atenciones (distribuidas en 4 meses)')
        c1, c2 = ciudadanos_tuple
        atenciones = []

        def generar_para_pvd(pvd, ciudadanos, operador, cantidad):
            resultado = []
            # Distribución mensual: marzo~25%, abril~25%, mayo~25%, junio~25%
            for i in range(cantidad):
                mes_offset = RNG.choice([85, 86, 87, 88, 89,   # marzo
                                          55, 56, 57, 58, 59,   # abril
                                          25, 26, 27, 28, 29,   # mayo
                                          1,  2,  3,  4,  5, 6, 7, 8, 9, 10])  # junio
                dias_atras = mes_offset + RNG.randint(0, 4)
                fecha = HOY - timedelta(days=dias_atras)
                h_ini = time(RNG.randint(8, 15), RNG.choice([0, 15, 30, 45]))
                h_fin_h = h_ini.hour + RNG.randint(0, 1)
                h_fin_m = RNG.choice([15, 30, 45, 0])
                h_fin   = time(min(h_fin_h, 16), h_fin_m)
                estado  = RNG.choices(['F','F','F','F','C','P'], weights=[70,70,70,70,10,5])[0]
                if dias_atras <= 1:
                    estado = RNG.choice(['P', 'F'])
                c = ciudadanos[RNG.randint(0, len(ciudadanos)-1)]
                a = Atencion.objects.create(
                    punto_vive_digital=pvd,
                    ciudadano=c,
                    operador=operador,
                    fecha=fecha,
                    hora_inicio=h_ini,
                    hora_fin=h_fin if estado != 'P' else None,
                    estado=estado,
                    observaciones=RNG.choice(OBS_ATENCIONES),
                )
                resultado.append(a)
            return resultado

        atenciones += generar_para_pvd(pvd1, c1, julia, 100)
        atenciones += generar_para_pvd(pvd2, c2, lady, 100)
        self._ok(f'{len(atenciones)} atenciones creadas')
        return atenciones

    # ── SERVICIOS ─────────────────────────────────────────────────────────────
    def _crear_servicios(self, atenciones):
        self._titulo('Servicios')
        count = 0
        for a in atenciones:
            if a.estado == 'C':
                continue
            nombre, tipo, req = RNG.choice(TIPOS_SERVICIO)
            Servicio.objects.create(
                atencion=a,
                nombre=nombre,
                tipo=tipo,
                descripcion=a.observaciones[:120] if a.observaciones else nombre,
                requiere_equipo=req,
                estado='A' if a.estado == 'P' else 'F',
            )
            count += 1
        self._ok(f'{count} servicios creados')

    # ── SATISFACCIÓN ─────────────────────────────────────────────────────────
    def _crear_satisfaccion(self, atenciones):
        self._titulo('Encuestas de satisfacción')
        finalizadas = [a for a in atenciones if a.estado == 'F']
        count = 0
        opciones_encuesta = ['E', 'B', 'M']
        pesos_encuesta = [60, 30, 10]
        for a in finalizadas:
            # ~85% de las finalizadas tienen encuesta
            if RNG.random() > 0.85:
                continue
            Satisfaccion.objects.create(
                atencion=a,
                tiempo_espera=RNG.choices(opciones_encuesta, weights=pesos_encuesta)[0],
                atencion_servidor=RNG.choices(opciones_encuesta, weights=pesos_encuesta)[0],
                satisfaccion_servicio=RNG.choices(opciones_encuesta, weights=pesos_encuesta)[0],
                informacion_recibida=RNG.choices(opciones_encuesta, weights=pesos_encuesta)[0],
                comodidad_instalaciones=RNG.choices(opciones_encuesta, weights=pesos_encuesta)[0],
                comentario=RNG.choice(COMENTARIOS_SAT),
                fecha=timezone.make_aware(datetime.combine(a.fecha, time(17, 0))),
            )
            count += 1
        self._ok(f'{count} encuestas creadas')

    # ── SALAS ─────────────────────────────────────────────────────────────────
    def _crear_salas(self, pvd1, pvd2):
        self._titulo('Salas (2 por PVD = 4 total)')
        salas_def = [
            ('Sala de Navegación',   'Sala con equipos de cómputo para acceso a internet y trámites en línea.', 12),
            ('Sala de Capacitación', 'Espacio equipado para talleres, cursos y formación digital ciudadana.',   20),
        ]
        for pvd in [pvd1, pvd2]:
            for nombre, desc, cap in salas_def:
                s, c = Sala.objects.get_or_create(
                    punto_vive_digital=pvd, nombre=nombre,
                    defaults={'descripcion': desc, 'capacidad': cap, 'estado': 'A'}
                )
                self._ok(f'{pvd.nombre[:20]} → {nombre}') if c else self._info(f'Ya existe: {nombre}')

    # ── HABILITACIONES ────────────────────────────────────────────────────────
    def _crear_habilitaciones(self, pvd1, pvd2, lady, julia):
        self._titulo('Habilitaciones de sala (12 total)')

        def get_sala(pvd, nombre):
            return Sala.objects.get(punto_vive_digital=pvd, nombre=nombre)

        s1n = get_sala(pvd1, 'Sala de Navegación')
        s1c = get_sala(pvd1, 'Sala de Capacitación')
        s2n = get_sala(pvd2, 'Sala de Navegación')
        s2c = get_sala(pvd2, 'Sala de Capacitación')

        datos = [
            # PVD1 – Rafael Arias (6 habilitaciones)
            (s1c,'CAP', HOY-timedelta(days=45), time(8,0),  time(12,0),'Comunidad barrio Centro',
             'Taller habilidades digitales básicas – adultos mayores',15,'F',julia),
            (s1n,'NAV', HOY-timedelta(days=30), time(8,0),  time(12,0),'Comunidad general',
             'Navegación libre – trámites ciudadanos',10,'F',julia),
            (s1c,'TRAM',HOY-timedelta(days=20), time(9,0),  time(11,0),'Usuarios trámites DIAN/EPS',
             'Jornada trámites en línea: SISBEN, EPS, DIAN',8,'F',julia),
            (s1c,'CAP', HOY-timedelta(days=7),  time(14,0), time(17,0),'Jóvenes 15-25 años',
             'Taller redes sociales y seguridad digital',20,'F',julia),
            (s1n,'NAV', HOY,                    time(8,0),  time(12,0),'Comunidad general',
             'Navegación libre mañana',12,'E',julia),
            (s1c,'CAP', HOY+timedelta(days=3),  time(8,0),  time(12,0),'Docentes IE Rafael Arias',
             'Taller TIC para docentes – herramientas Google Workspace',15,'P',julia),
            # PVD2 – Antonio Nariño (6 habilitaciones)
            (s2c,'CAP', HOY-timedelta(days=40), time(8,0),  time(12,0),'Mujeres cabeza de hogar',
             'Taller emprendimiento digital y comercio electrónico',18,'F',lady),
            (s2n,'NAV', HOY-timedelta(days=25), time(13,0), time(17,0),'Comunidad general',
             'Navegación libre tarde',8,'F',lady),
            (s2c,'CAP', HOY-timedelta(days=10), time(8,0),  time(12,0),'Adultos mayores +60',
             'Internet para adultos mayores – correo y videollamadas',14,'F',lady),
            (s2n,'NAV', HOY-timedelta(days=3),  time(8,0),  time(12,0),'Comunidad general',
             'Navegación libre – acceso a portales del Estado',10,'F',lady),
            (s2c,'CAP', HOY,                    time(14,0), time(17,0),'Jóvenes barrio Antonio Nariño',
             'Ofimática básica – Word aplicado',18,'E',lady),
            (s2n,'EXAM',HOY+timedelta(days=5),  time(8,0),  time(10,0),'Estudiantes SENA',
             'Examen certificación competencias digitales SENA',8,'P',lady),
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
        self._ok(f'{count} habilitaciones creadas')

    # ── CURSOS ────────────────────────────────────────────────────────────────
    def _crear_cursos(self, pvd1, pvd2, lady, julia):
        self._titulo('Cursos y talleres (3 por PVD = 6 total)')
        datos = [
            # PVD1 – Rafael Arias
            (pvd1,'Ofimática Básica: Word y Excel',
             'Formación en procesador de texto y hoja de cálculo para personas sin experiencia previa.',
             'P','Adultos y jóvenes mayores de 15 años',
             HOY-timedelta(days=21), HOY+timedelta(days=7),'AC',julia),
            (pvd1,'Trámites Digitales del Estado Colombiano',
             'Apoyo para trámites ante SISBEN, DIAN, Colpensiones y EPS desde internet.',
             'P','Ciudadanos en general',
             HOY-timedelta(days=50), HOY-timedelta(days=15),'FI',julia),
            (pvd1,'Emprendimiento Digital para Mujeres',
             'Redes sociales, marketplace y herramientas digitales para impulsar negocios locales.',
             'P','Mujeres emprendedoras mayores de 18 años',
             HOY+timedelta(days=10), HOY+timedelta(days=31),'PL',julia),
            # PVD2 – Antonio Nariño
            (pvd2,'Seguridad Digital y Redes Sociales',
             'Protección de información personal y uso responsable de redes sociales.',
             'P','Jóvenes de 12 a 25 años',
             HOY-timedelta(days=14), HOY+timedelta(days=7),'AC',lady),
            (pvd2,'Internet para Adultos Mayores',
             'Navegación básica, correo electrónico y videollamadas para personas mayores de 60 años.',
             'P','Adultos mayores de 60 años',
             HOY-timedelta(days=35), HOY-timedelta(days=3),'FI',lady),
            (pvd2,'Ciudadanía Digital y Gobierno en Línea',
             'Servicios del Estado en línea: portal GOV.CO, ventanilla única y servicios municipales.',
             'P','Ciudadanos en general',
             HOY+timedelta(days=14), HOY+timedelta(days=35),'PL',lady),
        ]
        cursos = []
        for pvd, nombre, desc, modalidad, pob, f_ini, f_fin, estado, reg in datos:
            obj, c = Curso.objects.get_or_create(
                nombre=nombre, punto_vive_digital=pvd,
                defaults=dict(descripcion=desc, modalidad=modalidad,
                              poblacion_objetivo=pob, fecha_inicio=f_ini,
                              fecha_fin=f_fin, estado=estado, registrado_por=reg)
            )
            self._ok(nombre[:55]) if c else self._info(f'Ya existe: {nombre[:40]}')
            cursos.append(obj)
        return cursos

    # ── SESIONES / INSCRIPCIONES / ASISTENCIAS ────────────────────────────────
    def _crear_sesiones_inscripciones(self, cursos, ciudadanos_tuple, lady, julia):
        self._titulo('Sesiones de cursos')
        c1, c2 = ciudadanos_tuple

        sesiones_def = {
            0: [  # Ofimática Básica (AC) – PVD1
                (1, HOY-timedelta(days=21), time(8,0),  time(10,0), 'Introducción al computador',    'Partes del equipo, encendido, ratón y teclado'),
                (2, HOY-timedelta(days=14), time(8,0),  time(10,0), 'Microsoft Word básico',          'Crear, guardar y dar formato a documentos'),
                (3, HOY-timedelta(days=7),  time(8,0),  time(10,0), 'Word avanzado',                  'Tablas, imágenes, estilos y revisión ortográfica'),
                (4, HOY+timedelta(days=1),  time(8,0),  time(10,0), 'Introducción a Excel',           'Hojas de cálculo, fórmulas básicas y gráficos'),
                (5, HOY+timedelta(days=7),  time(8,0),  time(10,0), 'Excel aplicado',                 'Presupuestos y tablas dinámicas'),
            ],
            1: [  # Trámites Digitales (FI) – PVD1
                (1, HOY-timedelta(days=50), time(14,0), time(16,0), 'SISBEN en línea',    'Consulta puntaje y actualización de datos'),
                (2, HOY-timedelta(days=43), time(14,0), time(16,0), 'DIAN y MUISCA',      'RUT y declaración de renta simplificada'),
                (3, HOY-timedelta(days=36), time(14,0), time(16,0), 'Colpensiones y EPS', 'Semanas cotizadas, afiliación, certificados'),
                (4, HOY-timedelta(days=22), time(14,0), time(16,0), 'Alcaldía en línea',  'Trámites portal Alcaldía de Bugalagrande'),
            ],
            3: [  # Seguridad Digital (AC) – PVD2
                (1, HOY-timedelta(days=14), time(15,0), time(17,0), 'Contraseñas seguras', 'Crear y gestionar contraseñas fuertes'),
                (2, HOY-timedelta(days=7),  time(15,0), time(17,0), 'Redes sociales',      'Privacidad en Facebook e Instagram'),
                (3, HOY+timedelta(days=1),  time(15,0), time(17,0), 'Estafas digitales',   'Phishing, fraudes y noticias falsas'),
                (4, HOY+timedelta(days=7),  time(15,0), time(17,0), 'Datos personales',    'Protección de datos y HABEAS DATA'),
            ],
            4: [  # Internet Adultos Mayores (FI) – PVD2
                (1, HOY-timedelta(days=35), time(9,0),  time(11,0), 'Qué es internet',    'Navegadores, buscadores y páginas web'),
                (2, HOY-timedelta(days=28), time(9,0),  time(11,0), 'Correo electrónico', 'Crear cuenta Gmail y enviar correos'),
                (3, HOY-timedelta(days=21), time(9,0),  time(11,0), 'Videollamadas',      'WhatsApp y Google Meet'),
                (4, HOY-timedelta(days=7),  time(9,0),  time(11,0), 'Grado y clausura',   'Repaso general y certificación'),
            ],
        }

        for ci, sesiones_data in sesiones_def.items():
            curso = cursos[ci]
            for num, fecha, hi, hf, tema, contenido in sesiones_data:
                s, c = SesionCurso.objects.get_or_create(
                    curso=curso, numero_sesion=num,
                    defaults=dict(fecha=fecha, hora_inicio=hi, hora_fin=hf,
                                  tema=tema, contenido=contenido)
                )
                self._ok(f'Sesión {num} – {tema[:40]}') if c else None

        self._titulo('Inscripciones (12 por curso)')
        inscrip_map = {
            0: (RNG.sample(range(100), 12), julia),   # Ofimática – PVD1
            1: (RNG.sample(range(100), 12), julia),   # Trámites – PVD1
            3: (RNG.sample(range(100), 12), lady),    # Seguridad – PVD2
            4: (RNG.sample(range(100), 12), lady),    # Adultos Mayores – PVD2
        }
        for ci, (idxs, reg) in inscrip_map.items():
            curso = cursos[ci]
            pool  = c1 if ci < 3 else c2
            es_fi = curso.estado == 'FI'
            for idx in idxs:
                ciudadano = pool[idx % len(pool)]
                InscripcionCurso.objects.get_or_create(
                    curso=curso, ciudadano=ciudadano,
                    defaults={'estado': 'C' if es_fi else 'I', 'registrado_por': reg}
                )
        self._ok('Inscripciones registradas')

        self._titulo('Asistencias a sesiones pasadas')
        count = 0
        for ci, (idxs, _) in inscrip_map.items():
            curso = cursos[ci]
            pool  = c1 if ci < 3 else c2
            sesiones_pasadas = SesionCurso.objects.filter(curso=curso, fecha__lte=HOY)
            for sesion in sesiones_pasadas:
                for idx in idxs:
                    ciudadano = pool[idx % len(pool)]
                    asistio   = RNG.random() < 0.80
                    AsistenciaSesion.objects.get_or_create(
                        sesion=sesion, ciudadano=ciudadano,
                        defaults={'asistio': asistio}
                    )
                    count += 1
        self._ok(f'{count} registros de asistencia creados')

    # ── MANTENIMIENTOS ────────────────────────────────────────────────────────
    def _crear_mantenimientos(self, pvd1, pvd2, ofitic):
        self._titulo('Mantenimientos de equipos')
        datos = [
            (pvd1,'PRV', HOY-timedelta(days=70),
             'PC-RA-01, PC-RA-02, PC-RA-03, PC-RA-04, PC-RA-05, IMP-RA-01',
             'Mantenimiento preventivo trimestral: limpieza interna, actualización SO y antivirus.',
             'Polvo acumulado en ventiladores. PC-RA-03 con actualización pendiente.',
             'Revisión trimestral recomendada. Solicitar RAM adicional PC-RA-03.'),
            (pvd1,'COR', HOY-timedelta(days=20),
             'IMP-RA-01',
             'Cambio de cartuchos (negro y color) y limpieza de cabezales.',
             'Cartuchos agotados. Calibración desajustada.',
             'Verificar nivel de tinta mensualmente. Solicitar repuestos.'),
            (pvd1,'PRV', HOY+timedelta(days=20),
             'Todos los equipos Sala de Navegación y Sala de Capacitación',
             'Mantenimiento preventivo programado – segundo semestre 2026.',
             'Pendiente de realización.',
             'Coordinar con Oficina TIC. Revisar estado de baterías de portátiles.'),
            (pvd2,'PRV', HOY-timedelta(days=55),
             'PC-AN-01, PC-AN-02, PC-AN-03, PC-AN-04, LAP-AN-01, LAP-AN-02',
             'Mantenimiento preventivo semestral: limpieza general, antivirus, periféricos.',
             'Batería deficiente en LAP-AN-01. Sin otras novedades.',
             'Reemplazar batería LAP-AN-01 en próxima intervención.'),
            (pvd2,'COR', HOY-timedelta(days=10),
             'LAP-AN-01',
             'Reemplazo de batería defectuosa. Instalación módulo certificado.',
             'Batería no cargaba. Duración menor a 5 minutos.',
             'Batería nueva instalada con éxito. Solicitar garantía al proveedor.'),
            (pvd2,'PRV', HOY+timedelta(days=35),
             'IMP-AN-01, PRY-AN-01, TAB-AN-01, TAB-AN-02',
             'Mantenimiento preventivo programado – segundo semestre 2026.',
             'Pendiente de realización.',
             'Incluir revisión del proyector (filtro de polvo). Coordinar con administradora PVD.'),
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

    # ── EVIDENCIAS ────────────────────────────────────────────────────────────
    def _crear_evidencias(self, pvd1, pvd2, lady, julia):
        self._titulo('Evidencias fotográficas')
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.stdout.write('  [!!] Pillow no disponible – evidencias omitidas')
            return

        from django.core.files.base import ContentFile

        datos = [
            (pvd1,'Taller Adultos Mayores – Correo Electrónico',
             'Ciudadanos adultos mayores del barrio Centro participando en taller de correo y videollamadas.',
             'CAP', HOY-timedelta(days=45), julia, '#1a4b8a', 'TALLER\nADULTOS MAYORES'),
            (pvd1,'Jornada Trámites en Línea – SISBEN y DIAN',
             'Jornada especial de atención para trámites ante SISBEN, DIAN y Colpensiones.',
             'ACT', HOY-timedelta(days=30), julia, '#0d6e3f', 'JORNADA\nTRÁMITES EN LÍNEA'),
            (pvd1,'Mantenimiento Preventivo Equipos Rafael Arias',
             'Equipo técnico realizando mantenimiento preventivo a computadores de la Sala de Navegación.',
             'MAN', HOY-timedelta(days=20), julia, '#7b2d00', 'MANTENIMIENTO\nPREVENTIVO'),
            (pvd1,'Curso Ofimática – Sesión Word Avanzado',
             'Participantes del curso Ofimática Básica aprendiendo Word para elaboración de documentos.',
             'CAP', HOY-timedelta(days=7),  julia, '#1a4b8a', 'CURSO\nOFIMÁTICA BÁSICA'),
            (pvd2,'Taller Jóvenes – Redes Sociales Seguras',
             'Jóvenes del barrio Antonio Nariño aprendiendo privacidad y uso seguro de redes sociales.',
             'CAP', HOY-timedelta(days=14), lady,  '#1a4b8a', 'TALLER\nREDES SOCIALES'),
            (pvd2,'Capacitación Mujeres Emprendedoras',
             'Mujeres emprendedoras recibiendo formación en comercio electrónico y herramientas digitales.',
             'CAP', HOY-timedelta(days=10), lady,  '#8a1a4b', 'FORMACIÓN\nMUJERES EMPREND.'),
            (pvd2,'Atención Ciudadana Internet Libre',
             'Ciudadanos haciendo uso de los equipos de navegación para trámites y consultas en línea.',
             'ACT', HOY-timedelta(days=5),  lady,  '#0d6e3f', 'ATENCIÓN\nCIUDADANA'),
            (pvd2,'Mantenimiento Equipos Antonio Nariño',
             'Intervención correctiva en portátil LAP-AN-01 – reemplazo de batería defectuosa.',
             'MAN', HOY-timedelta(days=10), lady,  '#7b2d00', 'MANTENIMIENTO\nCORRECTIVO'),
        ]

        count = 0
        for pvd, titulo, descripcion, categoria, fecha, reg, color, texto in datos:
            img_bytes = self._imagen(color, texto)
            nombre_arch = f"seed_{titulo[:18].replace(' ','_').replace('–','').replace('/','')}.jpg"
            ev = Evidencia(
                punto_vive_digital=pvd, titulo=titulo, descripcion=descripcion,
                categoria=categoria, fecha=fecha, registrado_por=reg,
            )
            ev.imagen.save(nombre_arch, ContentFile(img_bytes), save=True)
            count += 1
            self._ok(f'Evidencia: {titulo[:50]}')
        self._ok(f'{count} evidencias creadas')

    def _imagen(self, color, texto):
        from PIL import Image, ImageDraw
        img  = Image.new('RGB', (800, 500), color=color)
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, 789, 489], outline='white', width=3)
        lines  = texto.split('\n')
        y = 200
        for line in lines:
            draw.text(((800 - len(line)*14)//2, y), line, fill='white')
            y += 50
        draw.rectangle([0, 440, 800, 500], fill='black')
        draw.text((30, 458), 'Puntos Vive Digital – Bugalagrande', fill='white')
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85)
        return buf.getvalue()

    # ── RESUMEN ───────────────────────────────────────────────────────────────
    def _resumen(self):
        from modulo_puntos.models import (
            Ciudadano, Recurso, PrestamoRecurso, Atencion,
            Servicio, Satisfaccion, Sala, HabilitacionSala,
            Curso, SesionCurso, InscripcionCurso, AsistenciaSesion,
            MantenimientoEquipo, Evidencia,
        )
        self.stdout.write(self.style.SUCCESS(
            '\n╔══════════════════════════════════════╗\n'
            '║        RESUMEN DATOS CARGADOS        ║\n'
            '╠══════════════════════════════════════╣\n'
            f'║  Ciudadanos:      {Ciudadano.objects.count():<5}                ║\n'
            f'║  Atenciones:      {Atencion.objects.count():<5}                ║\n'
            f'║  Servicios:       {Servicio.objects.count():<5}                ║\n'
            f'║  Satisfacciones:  {Satisfaccion.objects.count():<5}                ║\n'
            f'║  Recursos:        {Recurso.objects.count():<5}                ║\n'
            f'║  Préstamos:       {PrestamoRecurso.objects.count():<5}                ║\n'
            f'║  Salas:           {Sala.objects.count():<5}                ║\n'
            f'║  Habilitaciones:  {HabilitacionSala.objects.count():<5}                ║\n'
            f'║  Cursos:          {Curso.objects.count():<5}                ║\n'
            f'║  Sesiones:        {SesionCurso.objects.count():<5}                ║\n'
            f'║  Inscripciones:   {InscripcionCurso.objects.count():<5}                ║\n'
            f'║  Asistencias:     {AsistenciaSesion.objects.count():<5}                ║\n'
            f'║  Mantenimientos:  {MantenimientoEquipo.objects.count():<5}                ║\n'
            f'║  Evidencias:      {Evidencia.objects.count():<5}                ║\n'
            '╚══════════════════════════════════════╝\n'
        ))
