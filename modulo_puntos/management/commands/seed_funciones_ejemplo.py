"""
Crea servicios personalizados de ejemplo con funciones complejas que usan los 4 módulos:
formulario de captura, estados del proceso, vínculo ciudadano y control de inventario.

Uso:
    python manage.py seed_funciones_ejemplo
    python manage.py seed_funciones_ejemplo --pvd-id 44
    python manage.py seed_funciones_ejemplo --borrar   # limpia los ejemplos antes de crear
"""

from django.core.management.base import BaseCommand, CommandError
from modulo_puntos.models import PuntoViveDigital, ServicioPersonalizado, FuncionServicio


SERVICIOS = [
    # ══════════════════════════════════════════════════════════════════════════
    # 1. BANCO DE EQUIPOS TECNOLÓGICOS
    # ══════════════════════════════════════════════════════════════════════════
    {
        "nombre":      "Banco de Equipos Tecnológicos",
        "icono":       "🖥️",
        "descripcion": "Préstamo de dispositivos tecnológicos del PVD a ciudadanos y estudiantes",
        "funciones": [
            {
                "nombre":      "Préstamo de Laptop para Trabajo o Estudio",
                "descripcion": "Registro y seguimiento de laptops prestadas a ciudadanos con control de stock en tiempo real",
                # ── Módulo formulario ──────────────────────────────────────
                "mod_formulario": True,
                "campos": [
                    {"nombre": "Propósito del préstamo",     "tipo": "lista",    "requerido": True,
                     "opciones": ["Trabajo remoto", "Estudio universitario", "Emprendimiento", "Búsqueda de empleo", "Otro"]},
                    {"nombre": "Institución u organización", "tipo": "texto",    "requerido": False, "opciones": []},
                    {"nombre": "Correo electrónico",         "tipo": "email",    "requerido": True,  "opciones": []},
                    {"nombre": "Teléfono de contacto",       "tipo": "telefono", "requerido": True,  "opciones": []},
                    {"nombre": "Tiene conexión a internet",  "tipo": "booleano", "requerido": True,  "opciones": []},
                    {"nombre": "Ha recibido laptop antes",   "tipo": "booleano", "requerido": True,  "opciones": []},
                    {"nombre": "Observaciones del operador", "tipo": "textarea", "requerido": False, "opciones": []},
                ],
                # ── Módulo estados ─────────────────────────────────────────
                "mod_estados": True,
                "estados": [
                    {"nombre": "Solicitado",    "color": "#f59e0b", "es_terminal": False},
                    {"nombre": "Verificado",    "color": "#3b82f6", "es_terminal": False},
                    {"nombre": "Entregado",     "color": "#8b5cf6", "es_terminal": False},
                    {"nombre": "Con retraso",   "color": "#f97316", "es_terminal": False},
                    {"nombre": "Devuelto",      "color": "#10b981", "es_terminal": True},
                    {"nombre": "Reportado como perdido", "color": "#ef4444", "es_terminal": True},
                ],
                # ── Módulo ciudadano ───────────────────────────────────────
                "mod_ciudadano": True,
                "ciudadano_requerido": True,
                # ── Módulo stock ───────────────────────────────────────────
                "mod_stock": True,
                "stock_nombre": "Laptop",
                "stock_total":  12,
                "stock_unidad": "laptops",
            },
            {
                "nombre":      "Préstamo de Cámara Web y Kit de Streaming",
                "descripcion": "Préstamo de kits para videoconferencias, entrevistas virtuales y transmisiones en vivo",
                "mod_formulario": True,
                "campos": [
                    {"nombre": "Tipo de uso",              "tipo": "lista",    "requerido": True,
                     "opciones": ["Entrevista de trabajo", "Clase virtual", "Reunión empresarial", "Streaming / transmisión", "Otro"]},
                    {"nombre": "Plataforma a usar",        "tipo": "lista",    "requerido": True,
                     "opciones": ["Zoom", "Google Meet", "Microsoft Teams", "YouTube Live", "Facebook Live", "Otra"]},
                    {"nombre": "Fecha del evento",         "tipo": "fecha",    "requerido": True,  "opciones": []},
                    {"nombre": "Hora inicio del evento",   "tipo": "hora",     "requerido": True,  "opciones": []},
                    {"nombre": "Duración estimada (horas)","tipo": "decimal",  "requerido": True,  "opciones": []},
                    {"nombre": "Correo para confirmación", "tipo": "email",    "requerido": True,  "opciones": []},
                    {"nombre": "Requiere asistencia técnica del PVD", "tipo": "booleano", "requerido": True, "opciones": []},
                ],
                "mod_estados": True,
                "estados": [
                    {"nombre": "Agendado",     "color": "#3b82f6", "es_terminal": False},
                    {"nombre": "Kit entregado","color": "#8b5cf6", "es_terminal": False},
                    {"nombre": "En uso",       "color": "#f59e0b", "es_terminal": False},
                    {"nombre": "Devuelto OK",  "color": "#10b981", "es_terminal": True},
                    {"nombre": "Devuelto con daño", "color": "#ef4444", "es_terminal": True},
                ],
                "mod_ciudadano": True,
                "ciudadano_requerido": False,
                "mod_stock": True,
                "stock_nombre": "Kit de streaming (cámara + micrófono + base)",
                "stock_total":  5,
                "stock_unidad": "kits",
            },
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 2. CERTIFICACIONES Y CONSTANCIAS DIGITALES
    # ══════════════════════════════════════════════════════════════════════════
    {
        "nombre":      "Certificaciones y Constancias Digitales",
        "icono":       "📜",
        "descripcion": "Gestión de solicitudes, generación y entrega de certificados de formación digital",
        "funciones": [
            {
                "nombre":      "Certificado de Competencias Digitales",
                "descripcion": "Proceso completo de radicación, revisión, firma y entrega de certificados a personas que finalizaron programas de formación",
                "mod_formulario": True,
                "campos": [
                    {"nombre": "Programa o curso completado", "tipo": "lista",   "requerido": True,
                     "opciones": ["Alfabetización Digital", "Excel Básico", "Redes Sociales para Negocios",
                                  "Seguridad en Internet", "Diseño Gráfico Básico", "E-commerce", "Otro"]},
                    {"nombre": "Institución que dictó el curso", "tipo": "texto",   "requerido": True,  "opciones": []},
                    {"nombre": "Fecha de inicio del curso",      "tipo": "fecha",   "requerido": True,  "opciones": []},
                    {"nombre": "Fecha de finalización",          "tipo": "fecha",   "requerido": True,  "opciones": []},
                    {"nombre": "Total de horas cursadas",        "tipo": "numero",  "requerido": True,  "opciones": []},
                    {"nombre": "Calificación obtenida (1.0 - 5.0)", "tipo": "decimal", "requerido": True, "opciones": []},
                    {"nombre": "Modalidad",                      "tipo": "lista",   "requerido": True,
                     "opciones": ["Presencial", "Virtual", "Mixta"]},
                    {"nombre": "Correo para envío digital",      "tipo": "email",   "requerido": True,  "opciones": []},
                    {"nombre": "El participante requiere certificado físico", "tipo": "booleano", "requerido": True, "opciones": []},
                ],
                "mod_estados": True,
                "estados": [
                    {"nombre": "Radicada",          "color": "#64748b", "es_terminal": False},
                    {"nombre": "En revisión",        "color": "#f59e0b", "es_terminal": False},
                    {"nombre": "Aprobada",           "color": "#3b82f6", "es_terminal": False},
                    {"nombre": "Lista para firma",   "color": "#8b5cf6", "es_terminal": False},
                    {"nombre": "Entregada",          "color": "#10b981", "es_terminal": True},
                    {"nombre": "Rechazada",          "color": "#ef4444", "es_terminal": True},
                ],
                "mod_ciudadano": True,
                "ciudadano_requerido": True,
                "mod_stock": True,
                "stock_nombre": "Hoja de certificado con sello oficial",
                "stock_total":  150,
                "stock_unidad": "hojas",
            },
            {
                "nombre":      "Constancia de Participación en Taller PVD",
                "descripcion": "Emisión de constancias para asistentes a talleres, charlas y capacitaciones organizadas por el PVD",
                "mod_formulario": True,
                "campos": [
                    {"nombre": "Nombre del taller o charla",  "tipo": "texto",    "requerido": True,  "opciones": []},
                    {"nombre": "Fecha del evento",            "tipo": "fecha",    "requerido": True,  "opciones": []},
                    {"nombre": "Hora de inicio",              "tipo": "hora",     "requerido": True,  "opciones": []},
                    {"nombre": "Duración total (horas)",      "tipo": "numero",   "requerido": True,  "opciones": []},
                    {"nombre": "Rol en el taller",            "tipo": "lista",    "requerido": True,
                     "opciones": ["Participante", "Monitor", "Coordinador", "Facilitador invitado"]},
                    {"nombre": "Correo del beneficiario",     "tipo": "email",    "requerido": False, "opciones": []},
                    {"nombre": "Requiere constancia impresa", "tipo": "booleano", "requerido": True,  "opciones": []},
                    {"nombre": "Observaciones adicionales",   "tipo": "textarea", "requerido": False, "opciones": []},
                ],
                "mod_estados": True,
                "estados": [
                    {"nombre": "Solicitada",    "color": "#64748b", "es_terminal": False},
                    {"nombre": "Verificando asistencia", "color": "#f59e0b", "es_terminal": False},
                    {"nombre": "Generada",      "color": "#3b82f6", "es_terminal": False},
                    {"nombre": "Entregada",     "color": "#10b981", "es_terminal": True},
                    {"nombre": "No asistió",    "color": "#ef4444", "es_terminal": True},
                ],
                "mod_ciudadano": True,
                "ciudadano_requerido": False,
                "mod_stock": True,
                "stock_nombre": "Hoja membretada para constancia",
                "stock_total":  300,
                "stock_unidad": "hojas",
            },
        ],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 3. CENTRO DE EMPRENDIMIENTO DIGITAL
    # ══════════════════════════════════════════════════════════════════════════
    {
        "nombre":      "Centro de Emprendimiento Digital",
        "icono":       "🚀",
        "descripcion": "Programas de acompañamiento y recursos para emprendedores y micronegocios digitales",
        "funciones": [
            {
                "nombre":      "Asesoría en Creación de Tienda Virtual",
                "descripcion": "Acompañamiento personalizado para emprendedores que quieren abrir su tienda en línea: diagnóstico, plataforma, configuración y primera venta",
                "mod_formulario": True,
                "campos": [
                    {"nombre": "Nombre del negocio",           "tipo": "texto",    "requerido": True,  "opciones": []},
                    {"nombre": "Tipo de productos o servicios","tipo": "lista",    "requerido": True,
                     "opciones": ["Ropa y accesorios", "Alimentos y bebidas", "Artesanías", "Tecnología",
                                  "Servicios profesionales", "Belleza y cuidado personal", "Otro"]},
                    {"nombre": "Plataforma de interés",        "tipo": "lista",    "requerido": True,
                     "opciones": ["MercadoLibre", "Shopify", "WooCommerce (WordPress)", "Instagram Shopping",
                                  "Facebook Marketplace", "No lo sé aún — necesito orientación"]},
                    {"nombre": "Tiene RUT activo",             "tipo": "booleano", "requerido": True,  "opciones": []},
                    {"nombre": "Correo del negocio",           "tipo": "email",    "requerido": True,  "opciones": []},
                    {"nombre": "Teléfono / WhatsApp",          "tipo": "telefono", "requerido": True,  "opciones": []},
                    {"nombre": "Ingresos mensuales aprox. ($)","tipo": "decimal",  "requerido": False, "opciones": []},
                    {"nombre": "Ya vende por internet",        "tipo": "booleano", "requerido": True,  "opciones": []},
                    {"nombre": "Expectativas y metas",         "tipo": "textarea", "requerido": True,  "opciones": []},
                ],
                "mod_estados": True,
                "estados": [
                    {"nombre": "Registrado",           "color": "#64748b", "es_terminal": False},
                    {"nombre": "Diagnóstico inicial",  "color": "#f59e0b", "es_terminal": False},
                    {"nombre": "Plan de trabajo",      "color": "#3b82f6", "es_terminal": False},
                    {"nombre": "En implementación",    "color": "#8b5cf6", "es_terminal": False},
                    {"nombre": "Tienda activa",        "color": "#10b981", "es_terminal": True},
                    {"nombre": "Abandonó el proceso",  "color": "#ef4444", "es_terminal": True},
                ],
                "mod_ciudadano": True,
                "ciudadano_requerido": True,
                "mod_stock": True,
                "stock_nombre": "Kit impreso del emprendedor (guías + folletos)",
                "stock_total":  20,
                "stock_unidad": "kits",
            },
            {
                "nombre":      "Inscripción a Programa Mujeres Digitales",
                "descripcion": "Registro y seguimiento de beneficiarias del programa de inclusión digital para mujeres: formación, acompañamiento y graduación",
                "mod_formulario": True,
                "campos": [
                    {"nombre": "Nivel educativo",                "tipo": "lista",    "requerido": True,
                     "opciones": ["Primaria incompleta", "Primaria completa", "Bachillerato incompleto",
                                  "Bachillerato completo", "Técnico/Tecnólogo", "Universitario"]},
                    {"nombre": "Ocupación actual",               "tipo": "lista",    "requerido": True,
                     "opciones": ["Ama de casa", "Empleada", "Independiente / emprendedora",
                                  "Desempleada", "Estudiante", "Pensionada"]},
                    {"nombre": "Tiene smartphone propio",        "tipo": "booleano", "requerido": True,  "opciones": []},
                    {"nombre": "Acceso a internet en casa",      "tipo": "booleano", "requerido": True,  "opciones": []},
                    {"nombre": "Disponibilidad horaria",         "tipo": "lista",    "requerido": True,
                     "opciones": ["Mañana (8am - 12m)", "Tarde (1pm - 5pm)", "Noche (6pm - 9pm)", "Fines de semana"]},
                    {"nombre": "Correo electrónico",             "tipo": "email",    "requerido": False, "opciones": []},
                    {"nombre": "Teléfono de contacto",           "tipo": "telefono", "requerido": True,  "opciones": []},
                    {"nombre": "Número de personas a cargo",     "tipo": "numero",   "requerido": False, "opciones": []},
                    {"nombre": "¿Por qué quiere participar?",    "tipo": "textarea", "requerido": True,  "opciones": []},
                ],
                "mod_estados": True,
                "estados": [
                    {"nombre": "Inscrita",          "color": "#64748b", "es_terminal": False},
                    {"nombre": "Preseleccionada",   "color": "#f59e0b", "es_terminal": False},
                    {"nombre": "Confirmada",        "color": "#3b82f6", "es_terminal": False},
                    {"nombre": "En formación",      "color": "#8b5cf6", "es_terminal": False},
                    {"nombre": "Graduada",          "color": "#10b981", "es_terminal": True},
                    {"nombre": "Retirada",          "color": "#ef4444", "es_terminal": True},
                ],
                "mod_ciudadano": True,
                "ciudadano_requerido": True,
                "mod_stock": True,
                "stock_nombre": "Manual del programa Mujeres Digitales",
                "stock_total":  25,
                "stock_unidad": "manuales",
            },
        ],
    },
]

MARKER = "[EJEMPLO]"


class Command(BaseCommand):
    help = "Crea servicios personalizados de ejemplo con funciones complejas (4 módulos activos)"

    def add_arguments(self, parser):
        parser.add_argument("--pvd-id", type=int, help="ID del PVD donde crear los servicios")
        parser.add_argument("--borrar", action="store_true",
                            help=f"Elimina los servicios de ejemplo existentes (marcados con '{MARKER}') antes de crear")

    def handle(self, *args, **options):
        # ── Seleccionar PVD ──────────────────────────────────────────────────
        pvd_id = options.get("pvd_id")
        if pvd_id:
            pvd = PuntoViveDigital.objects.filter(pk=pvd_id, estado="A").first()
            if not pvd:
                raise CommandError(f"No se encontró un PVD activo con ID {pvd_id}")
        else:
            pvd = PuntoViveDigital.objects.filter(estado="A").first()
            if not pvd:
                raise CommandError("No hay PVDs activos en la base de datos. Crea uno primero.")

        self.stdout.write(f"\n📍 PVD seleccionado: {pvd.nombre} (id={pvd.pk})\n")

        # ── Borrar ejemplos anteriores ───────────────────────────────────────
        if options["borrar"]:
            qs = ServicioPersonalizado.objects.filter(
                punto_vive_digital=pvd, nombre__startswith=MARKER
            )
            n = qs.count()
            qs.delete()
            self.stdout.write(self.style.WARNING(f"🗑  Se eliminaron {n} servicio(s) de ejemplo.\n"))

        # ── Crear servicios y funciones ──────────────────────────────────────
        total_svc = 0
        total_fun = 0

        for svc_def in SERVICIOS:
            nombre_svc = f"{MARKER} {svc_def['nombre']}"
            svc = ServicioPersonalizado.objects.create(
                punto_vive_digital=pvd,
                nombre=nombre_svc,
                icono=svc_def["icono"],
                descripcion=svc_def["descripcion"],
                habilitado=True,
            )
            total_svc += 1
            self.stdout.write(f"  ✅ Servicio: {svc_def['icono']} {svc_def['nombre']}")

            for orden, fun_def in enumerate(svc_def["funciones"]):
                FuncionServicio.objects.create(
                    servicio=svc,
                    nombre=fun_def["nombre"],
                    descripcion=fun_def["descripcion"],
                    mod_formulario=fun_def.get("mod_formulario", False),
                    mod_estados=fun_def.get("mod_estados", False),
                    mod_ciudadano=fun_def.get("mod_ciudadano", False),
                    mod_stock=fun_def.get("mod_stock", False),
                    campos=fun_def.get("campos", []),
                    estados=fun_def.get("estados", []),
                    ciudadano_requerido=fun_def.get("ciudadano_requerido", False),
                    stock_nombre=fun_def.get("stock_nombre", ""),
                    stock_total=fun_def.get("stock_total", 0),
                    stock_unidad=fun_def.get("stock_unidad", "unidades"),
                    orden=orden,
                )
                total_fun += 1
                modulos = []
                if fun_def.get("mod_formulario"): modulos.append(f"📋 {len(fun_def.get('campos', []))} campos")
                if fun_def.get("mod_estados"):    modulos.append(f"🔄 {len(fun_def.get('estados', []))} estados")
                if fun_def.get("mod_ciudadano"):  modulos.append("👤 ciudadano")
                if fun_def.get("mod_stock"):      modulos.append(f"📦 {fun_def.get('stock_total')} {fun_def.get('stock_unidad')}")
                self.stdout.write(f"       ⚙️  {fun_def['nombre']}")
                self.stdout.write(f"          {' · '.join(modulos)}")

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Listo. Se crearon {total_svc} servicios con {total_fun} funciones en '{pvd.nombre}'.\n"
            f"   Para verlos: panel del PVD → Gestionar servicio → (elige uno de los [EJEMPLO]).\n"
            f"   Para borrarlos luego: python manage.py seed_funciones_ejemplo --borrar\n"
        ))
