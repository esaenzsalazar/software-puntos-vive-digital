"""
Crea servicios y funciones de ejemplo usando los 6 módulos disponibles:
formulario, estados, ciudadano, stock (multi-ítem), agenda y encuesta.

Uso:
    python manage.py seed_funciones_ejemplo
    python manage.py seed_funciones_ejemplo --pvd-id 44
    python manage.py seed_funciones_ejemplo --borrar
"""

from django.core.management.base import BaseCommand
from modulo_puntos.models import PuntoViveDigital, ServicioPersonalizado, FuncionServicio

MARCADOR = "[EJEMPLO]"

SERVICIOS = [
    # ══════════════════════════════════════════════════════════════════════════
    # 1. BANCO DE EQUIPOS — stock multi-ítem + estados controlados + ciudadano
    # ══════════════════════════════════════════════════════════════════════════
    {
        "nombre": f"{MARCADOR} Banco de Equipos Tecnológicos",
        "icono": "🖥️",
        "descripcion": "Préstamo de dispositivos tecnológicos del PVD a ciudadanos y estudiantes",
        "funciones": [
            {
                "nombre": "Préstamo de Equipos (multi-ítem)",
                "descripcion": "Control de varios tipos de equipos en un solo inventario con alertas automáticas",
                "mod_formulario": True,
                "campos": [
                    {"nombre": "proposito", "label": "Propósito del préstamo", "tipo": "lista", "requerido": True,
                     "opciones": ["Trabajo remoto", "Estudio universitario", "Emprendimiento", "Búsqueda de empleo", "Otro"]},
                    {"nombre": "correo", "label": "Correo electrónico", "tipo": "email", "requerido": True, "opciones": []},
                    {"nombre": "telefono", "label": "Teléfono de contacto", "tipo": "telefono", "requerido": True, "opciones": []},
                    {"nombre": "tiene_internet", "label": "Tiene conexión a internet", "tipo": "booleano", "requerido": True, "opciones": []},
                    {"nombre": "observaciones", "label": "Observaciones del operador", "tipo": "textarea", "requerido": False, "opciones": []},
                ],
                "mod_estados": True,
                "estados": [
                    {"nombre": "Solicitado", "color": "#f59e0b", "emoji": "📋", "es_inicial": True, "es_terminal": False,
                     "puede_ir_a": ["Verificado", "Rechazado"], "requiere_nota": False},
                    {"nombre": "Verificado", "color": "#3b82f6", "emoji": "🔍", "es_inicial": False, "es_terminal": False,
                     "puede_ir_a": ["Entregado", "Rechazado"], "requiere_nota": False},
                    {"nombre": "Entregado", "color": "#8b5cf6", "emoji": "📤", "es_inicial": False, "es_terminal": False,
                     "puede_ir_a": ["Devuelto", "Con retraso", "Reportado perdido"], "requiere_nota": False},
                    {"nombre": "Con retraso", "color": "#f97316", "emoji": "⚠️", "es_inicial": False, "es_terminal": False,
                     "puede_ir_a": ["Devuelto"], "requiere_nota": True},
                    {"nombre": "Devuelto", "color": "#10b981", "emoji": "✅", "es_inicial": False, "es_terminal": True,
                     "puede_ir_a": [], "requiere_nota": False},
                    {"nombre": "Rechazado", "color": "#64748b", "emoji": "❌", "es_inicial": False, "es_terminal": True,
                     "puede_ir_a": [], "requiere_nota": True},
                    {"nombre": "Reportado perdido", "color": "#ef4444", "emoji": "🚨", "es_inicial": False, "es_terminal": True,
                     "puede_ir_a": [], "requiere_nota": True},
                ],
                "mod_ciudadano": True,
                "ciudadano_requerido": True,
                "ciudadano_rol_etiqueta": "Beneficiario",
                "ciudadano_permite_inline": False,
                "ciudadano_campos_inline": [],
                "mod_stock": True,
                "stock_nombre": "", "stock_total": 0, "stock_unidad": "unidades", "stock_alerta_en": None,
                "stock_items": [
                    {"nombre": "Laptop", "total": 12, "unidad": "equipos", "alerta_en": 3},
                    {"nombre": "Tablet", "total": 20, "unidad": "equipos", "alerta_en": 5},
                    {"nombre": "Cable de carga", "total": 30, "unidad": "unidades", "alerta_en": 8},
                    {"nombre": "Mouse inalámbrico", "total": 15, "unidad": "unidades", "alerta_en": 4},
                ],
                "mod_agenda": False, "agenda_config": {},
                "mod_encuesta": True,
                "encuesta_config": [
                    {"pregunta": "¿Cómo calificaría la atención recibida?", "tipo": "calificacion"},
                    {"pregunta": "¿El equipo prestado cumplió sus necesidades?", "tipo": "calificacion"},
                    {"pregunta": "¿Tiene alguna sugerencia para mejorar el servicio?", "tipo": "texto"},
                ],
            },
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 2. ASESORÍAS JURÍDICAS — agenda + estados + ciudadano + formulario
    # ══════════════════════════════════════════════════════════════════════════
    {
        "nombre": f"{MARCADOR} Asesorías Jurídicas Gratuitas",
        "icono": "⚖️",
        "descripcion": "Citas de asesoría legal gratuita para ciudadanos en situación de vulnerabilidad",
        "funciones": [
            {
                "nombre": "Solicitud de Cita Jurídica",
                "descripcion": "Agendamiento de turnos de asesoría con abogado. Incluye formulario de caso, agenda y encuesta de satisfacción.",
                "mod_formulario": True,
                "campos": [
                    {"nombre": "tipo_caso", "label": "Tipo de caso", "tipo": "lista", "requerido": True,
                     "opciones": ["Derecho de familia", "Laboral", "Penal", "Civil", "Tierras y territorios", "Otro"]},
                    {"nombre": "descripcion_breve", "label": "Descripción breve del caso", "tipo": "textarea", "requerido": True, "opciones": []},
                    {"nombre": "tiene_documentos", "label": "Tiene documentos de soporte", "tipo": "booleano", "requerido": True, "opciones": []},
                    {"nombre": "nombre_documentos", "label": "¿Cuáles documentos?", "tipo": "texto", "requerido": False, "opciones": [],
                     "visible_si": {"campo": "tiene_documentos", "valor": "1"}},
                    {"nombre": "urgencia", "label": "Nivel de urgencia", "tipo": "lista", "requerido": True,
                     "opciones": ["Alta — hay fecha límite", "Media — puede esperar semanas", "Baja — consulta general"]},
                ],
                "mod_estados": True,
                "estados": [
                    {"nombre": "Agendado", "color": "#3b82f6", "emoji": "📅", "es_inicial": True, "es_terminal": False,
                     "puede_ir_a": ["Atendido", "No se presentó", "Cancelado"], "requiere_nota": False},
                    {"nombre": "Atendido", "color": "#10b981", "emoji": "✅", "es_inicial": False, "es_terminal": True,
                     "puede_ir_a": [], "requiere_nota": False},
                    {"nombre": "No se presentó", "color": "#f59e0b", "emoji": "⚠️", "es_inicial": False, "es_terminal": True,
                     "puede_ir_a": [], "requiere_nota": True},
                    {"nombre": "Cancelado", "color": "#ef4444", "emoji": "❌", "es_inicial": False, "es_terminal": True,
                     "puede_ir_a": [], "requiere_nota": True},
                ],
                "mod_ciudadano": True,
                "ciudadano_requerido": True,
                "ciudadano_rol_etiqueta": "Solicitante",
                "ciudadano_permite_inline": True,
                "ciudadano_campos_inline": [
                    {"nombre": "ci_nombre", "label": "Nombre completo", "tipo": "texto"},
                    {"nombre": "ci_documento", "label": "Número de documento", "tipo": "texto"},
                    {"nombre": "ci_telefono", "label": "Teléfono", "tipo": "telefono"},
                ],
                "mod_stock": False,
                "stock_nombre": "", "stock_total": 0, "stock_unidad": "unidades", "stock_alerta_en": None,
                "stock_items": [],
                "mod_agenda": True,
                "agenda_config": {
                    "dias": [1, 2, 3, 4, 5],
                    "hora_inicio": "08:00",
                    "hora_fin": "12:00",
                    "duracion_min": 30,
                    "max_por_franja": 2,
                },
                "mod_encuesta": True,
                "encuesta_config": [
                    {"pregunta": "¿Cómo calificaría la atención del abogado?", "tipo": "calificacion"},
                    {"pregunta": "¿Su caso fue resuelto o encaminado?", "tipo": "calificacion"},
                    {"pregunta": "¿Recomendaría este servicio?", "tipo": "calificacion"},
                    {"pregunta": "Comentarios adicionales", "tipo": "texto"},
                ],
            },
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 3. PROGRAMA DE INCLUSIÓN DIGITAL — formulario rico + estados + encuesta
    # ══════════════════════════════════════════════════════════════════════════
    {
        "nombre": f"{MARCADOR} Programa de Inclusión Digital",
        "icono": "💻",
        "descripcion": "Registro de participantes en talleres de alfabetización digital y habilidades TIC",
        "funciones": [
            {
                "nombre": "Inscripción a Taller TIC",
                "descripcion": "Formulario completo de inscripción con campos condicionales según nivel del participante",
                "mod_formulario": True,
                "campos": [
                    {"nombre": "nivel_digital", "label": "Nivel de conocimientos digitales", "tipo": "lista", "requerido": True,
                     "opciones": ["Principiante — nunca ha usado un computador", "Básico — uso básico", "Intermedio", "Avanzado"]},
                    {"nombre": "taller_interes", "label": "Taller de interés", "tipo": "multiselect", "requerido": True,
                     "opciones": ["Internet básico", "Office / Google Docs", "Redes sociales", "Emprendimiento digital", "Trámites en línea", "Seguridad digital"]},
                    {"nombre": "ocupacion", "label": "Ocupación actual", "tipo": "lista", "requerido": True,
                     "opciones": ["Ama/o de casa", "Estudiante", "Empleado", "Independiente", "Pensionado", "Desempleado"]},
                    {"nombre": "nombre_empresa", "label": "Empresa o entidad", "tipo": "texto", "requerido": False, "opciones": [],
                     "visible_si": {"campo": "ocupacion", "valor": "Empleado"}},
                    {"nombre": "experiencia_previa", "label": "Describe tu experiencia previa", "tipo": "textarea", "requerido": False, "opciones": [],
                     "visible_si": {"campo": "nivel_digital", "valor": "Intermedio"}},
                    {"nombre": "dispositivo_propio", "label": "Tiene dispositivo propio", "tipo": "booleano", "requerido": True, "opciones": []},
                    {"nombre": "tipo_dispositivo", "label": "Tipo de dispositivo", "tipo": "lista", "requerido": False,
                     "opciones": ["Smartphone", "Tablet", "Laptop", "PC de escritorio"],
                     "visible_si": {"campo": "dispositivo_propio", "valor": "1"}},
                    {"nombre": "calificacion_motivacion", "label": "¿Cuánto desea aprender? (1=poco, 5=mucho)", "tipo": "calificacion", "requerido": True, "opciones": []},
                ],
                "mod_estados": True,
                "estados": [
                    {"nombre": "Inscrito", "color": "#3b82f6", "emoji": "📝", "es_inicial": True, "es_terminal": False,
                     "puede_ir_a": ["En curso", "Retirado"], "requiere_nota": False},
                    {"nombre": "En curso", "color": "#8b5cf6", "emoji": "🎓", "es_inicial": False, "es_terminal": False,
                     "puede_ir_a": ["Finalizado", "Certificado", "Retirado"], "requiere_nota": False},
                    {"nombre": "Finalizado", "color": "#10b981", "emoji": "✅", "es_inicial": False, "es_terminal": True,
                     "puede_ir_a": [], "requiere_nota": False},
                    {"nombre": "Certificado", "color": "#f59e0b", "emoji": "🏆", "es_inicial": False, "es_terminal": True,
                     "puede_ir_a": [], "requiere_nota": False},
                    {"nombre": "Retirado", "color": "#64748b", "emoji": "↩️", "es_inicial": False, "es_terminal": True,
                     "puede_ir_a": [], "requiere_nota": True},
                ],
                "mod_ciudadano": True,
                "ciudadano_requerido": True,
                "ciudadano_rol_etiqueta": "Participante",
                "ciudadano_permite_inline": True,
                "ciudadano_campos_inline": [
                    {"nombre": "ci_nombre", "label": "Nombre completo", "tipo": "texto"},
                    {"nombre": "ci_doc", "label": "Número de documento", "tipo": "texto"},
                    {"nombre": "ci_tel", "label": "Teléfono", "tipo": "telefono"},
                ],
                "mod_stock": True,
                "stock_nombre": "", "stock_total": 0, "stock_unidad": "unidades", "stock_alerta_en": None,
                "stock_items": [
                    {"nombre": "Cupo en taller", "total": 25, "unidad": "cupos", "alerta_en": 5},
                    {"nombre": "Material didáctico impreso", "total": 30, "unidad": "kits", "alerta_en": 6},
                ],
                "mod_agenda": True,
                "agenda_config": {
                    "dias": [1, 3, 5],
                    "hora_inicio": "14:00",
                    "hora_fin": "17:00",
                    "duracion_min": 60,
                    "max_por_franja": 25,
                },
                "mod_encuesta": True,
                "encuesta_config": [
                    {"pregunta": "¿Cómo calificaría el contenido del taller?", "tipo": "calificacion"},
                    {"pregunta": "¿Cómo calificaría al instructor?", "tipo": "calificacion"},
                    {"pregunta": "¿Las instalaciones fueron adecuadas?", "tipo": "calificacion"},
                    {"pregunta": "¿Qué temas le gustaría ver en próximos talleres?", "tipo": "texto"},
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Crea servicios y funciones de ejemplo usando todos los módulos disponibles'

    def add_arguments(self, parser):
        parser.add_argument('--pvd-id', type=int, default=None, help='ID del PVD destino')
        parser.add_argument('--borrar', action='store_true', help='Borrar ejemplos existentes antes de crear')

    def handle(self, *args, **options):
        pvd_id = options['pvd_id']
        borrar  = options['borrar']

        # ── Determinar PVD ──────────────────────────────────────────────────
        if pvd_id:
            try:
                pvd = PuntoViveDigital.objects.get(pk=pvd_id)
            except PuntoViveDigital.DoesNotExist:
                raise Exception(f'PVD con id={pvd_id} no existe.')
        else:
            pvd = PuntoViveDigital.objects.filter(estado='A').first()
            if not pvd:
                raise Exception('No hay PVDs activos. Crea uno primero.')
        self.stdout.write(f'PVD: {pvd.nombre} (id={pvd.pk})')

        # ── Borrar ejemplos existentes ──────────────────────────────────────
        if borrar:
            eliminados = ServicioPersonalizado.objects.filter(nombre__startswith=MARCADOR, punto_vive_digital=pvd).delete()
            self.stdout.write(self.style.WARNING(f'Eliminados: {eliminados}'))

        # ── Crear servicios y funciones ─────────────────────────────────────
        for svc_data in SERVICIOS:
                svc, created = ServicioPersonalizado.objects.get_or_create(
                    nombre=svc_data["nombre"],
                    punto_vive_digital=pvd,
                    defaults={
                        "icono": svc_data["icono"],
                        "descripcion": svc_data["descripcion"],
                        "habilitado": True,
                    },
                )
                tag = 'CREADO' if created else 'YA EXISTE'
                self.stdout.write(f'  {tag}: Servicio "{svc.nombre}"')

                for fun_data in svc_data["funciones"]:
                    fun, fcreated = FuncionServicio.objects.get_or_create(
                        servicio=svc,
                        nombre=fun_data["nombre"],
                        defaults={k: v for k, v in fun_data.items() if k != "nombre"},
                    )
                    if not fcreated:
                        # Actualizar campos si ya existe
                        for k, v in fun_data.items():
                            if k != "nombre":
                                setattr(fun, k, v)
                        fun.save()
                    ftag = 'CREADA' if fcreated else 'ACTUALIZADA'
                    self.stdout.write(f'    {ftag}: Función "{fun.nombre}"')

        self.stdout.write(self.style.SUCCESS('¡Listo! Ejemplos creados correctamente.'))
