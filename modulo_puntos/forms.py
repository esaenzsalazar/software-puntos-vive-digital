"""
Forms for Puntos Vive Digital system.
Defines all form classes with validation and custom widgets.
Contract CD-224-2026 - Alcaldía de Bugalagrande
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import (
    Ciudadano, Atencion, Satisfaccion, Servicio, ModuloHabilitado, PrestamoRecurso, Recurso,
    PuntoViveDigital, Sala, PermisoDefinicion, HabilitacionSala,
    Curso, SesionCurso, InscripcionCurso, MantenimientoEquipo,
)

# ==============================================================================
# LISTAS DE OPCIONES GLOBALES
# ==============================================================================

BARRIO_CHOICES = [
    ('', '— Seleccione un barrio —'),
    ('Ninguno / Área Rural', 'Ninguno / Área Rural'),
    ('Centro', 'Centro'), ('Obrero', 'Obrero'), ('Municipal', 'Municipal'),
    ('La Planta', 'La Planta'), ('Gualcoche', 'Gualcoche'), ('Los Mármoles', 'Los Mármoles'),
    ('Paulus VI', 'Paulus VI'), ('Primero de Mayo', 'Primero de Mayo'),
    ('José Antonio Galán', 'José Antonio Galán'), ('La Esperanza', 'La Esperanza'),
    ('Cocicoinpa', 'Cocicoinpa'), ('Ricaurte', 'Ricaurte'), ('Brisas del Río', 'Brisas del Río'),
    ('Cañaveral', 'Cañaveral'), ('El Edén', 'El Edén'), ('La María', 'La María'),
    ('La María II Etapa', 'La María II Etapa'), ('El Jardín', 'El Jardín'),
    ('Antonio Nariño', 'Antonio Nariño'), ('Ceilán', 'Ceilán'), ('Chorreras', 'Chorreras'),
    ('El Guayabo', 'El Guayabo'), ('El Overo', 'El Overo'), ('Galicia', 'Galicia'),
    ('Chicoral', 'Chicoral'), ('El Placer', 'El Placer'), ('Uribe', 'Uribe'),
    ('Paila Arriba', 'Paila Arriba'), ('Mestizal', 'Mestizal'), ('Otro', 'Otro barrio')
]

ETNIA_CHOICES = [
    ('Ninguna', 'Ninguna (Mestizo / Blanco)'), ('Indígena', 'Indígena'),
    ('Afrocolombiano', 'Afrocolombiano / Afrodescendiente'), ('Raizal', 'Raizal del Archipiélago'),
    ('Palenquero', 'Palenquero'), ('Rrom', 'Rrom (Gitano)'), ('Otra', 'Extranjero / Otra'),
]

EDUCACION_CHOICES = [
    ('Ninguno', 'Ninguno'), ('Preescolar', 'Preescolar'), ('Primaria', 'Básica Primaria'),
    ('Secundaria', 'Básica Secundaria'), ('Media', 'Media (Bachiller)'), ('Técnico', 'Técnico'),
    ('Tecnólogo', 'Tecnólogo'), ('Universitario', 'Universitario / Profesional'),
    ('Especialización', 'Especialización'), ('Maestría', 'Maestría'), ('Doctorado', 'Doctorado'),
]

OCUPACION_CHOICES = [
    ('Estudiante', 'Estudiante'), ('Empleado', 'Empleado (Contrato)'),
    ('Independiente', 'Trabajador Independiente'), ('Desempleado', 'Desempleado / Buscando trabajo'),
    ('Hogar', 'Labores del Hogar'), ('Pensionado', 'Pensionado'), ('Otro', 'Otro'),
]

NOMBRE_SERVICIO_CHOICES = [
    ('', '--- Seleccione un servicio ---'),
    ('Acceso a internet', 'Acceso a internet'),
    ('Acceso a sala de capacitaciones y cómputo', 'Acceso a sala de capacitaciones y cómputo'),
    ('Impresiones', 'Impresiones'),
    ('Cursos de aprendizaje', 'Cursos de aprendizaje'),
    ('Trámites en Línea / Gobierno Digital', 'Trámites en Línea / Gobierno Digital'),
]

TIPO_SERVICIO_CHOICES = [
    ('', '--- Seleccione una categoría ---'),
    ('Acceso a internet', 'Acceso a internet'),
    ('Capacitación / Cómputo', 'Capacitación / Cómputo'),
    ('Impresión', 'Impresión'),
    ('Formación', 'Formación'),
]

TIPO_RECURSO_CHOICES = [
    ('', '— Seleccione un tipo —'),
    ('Portátil', 'Portátil'),
    ('Video Beam', 'Video Beam'),
    ('Televisor', 'Televisor'),
    ('Impresora Láser', 'Impresora Láser'),
    ('Impresora de Inyección', 'Impresora de Inyección'),
    ('Computador de Mesa', 'Computador de Mesa'),
    ('__otro__', 'Otro...'),
]

# ==============================================================================
# FORMULARIOS PRINCIPALES
# ==============================================================================

class CiudadanoForm(forms.ModelForm):
    """
    Formulario para registrar y editar ciudadanos.
    Incluye validaciones para documento, email y teléfono.
    """
    correo = forms.EmailField(
        label='Correo Electrónico',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        })
    )

    class Meta:
        model = Ciudadano
        fields = [
            'tipo_documento', 'numero_documento',
            'primer_nombre', 'segundo_nombre',
            'primer_apellido', 'segundo_apellido',
            'fecha_nacimiento', 'correo', 'telefono', 'genero',
            'direccion', 'barrio', 'zona_rural',
            'etnia', 'nivel_educativo', 'ocupacion', 'estrato',
            'tiene_discapacidad', 'descripcion_discapacidad', 'estado'
        ]
        labels = {
            'tipo_documento': 'Tipo de Documento',
            'numero_documento': 'Número de Documento',
            'primer_nombre': 'Primer Nombre *',
            'segundo_nombre': 'Segundo Nombre (Opcional)',
            'primer_apellido': 'Primer Apellido *',
            'segundo_apellido': 'Segundo Apellido *',
            'fecha_nacimiento': 'Fecha de Nacimiento',
            'genero': 'Género',
            'direccion': 'Dirección de Residencia',
            'barrio': 'Barrio (Cabecera Municipal)',
            'zona_rural': 'Vereda / Corregimiento (Opcional)',
            'etnia': 'Pertenencia Étnica',
            'nivel_educativo': 'Nivel Educativo',
            'ocupacion': 'Ocupación Actual',
            'estrato': 'Estrato Socioeconómico',
            'tiene_discapacidad': '¿Tiene alguna discapacidad?',
            'descripcion_discapacidad': '¿Cuál discapacidad? (Descríbala)',
            'estado': 'Estado en el Sistema',
            'telefono': 'Teléfono o Celular',
        }
        widgets = {
            'tipo_documento': forms.Select(
                choices=[
                    ('CC', 'Cédula de Ciudadanía'),
                    ('TI', 'Tarjeta de Identidad'),
                    ('CE', 'Cédula de Extranjería'),
                    ('RC', 'Registro Civil'),
                    ('PA', 'Pasaporte'),
                    ('PEP', 'Permiso Especial de Permanencia'),
                    ('PPT', 'Permiso por Protección Temporal')
                ],
                attrs={'class': 'form-control'}
            ),
            'numero_documento': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Número de documento',
                    'oninput': "this.value = this.value.replace(/[^0-9]/g, '')"
                }
            ),
            'primer_nombre': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: Nicolás'}
            ),
            'segundo_nombre': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: Andrés (opcional)'}
            ),
            'primer_apellido': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: García'}
            ),
            'segundo_apellido': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: López'}
            ),
            'fecha_nacimiento': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'telefono': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej. 3001234567',
                    'oninput': "this.value = this.value.replace(/[^0-9]/g, '').substring(0,10)",
                    'maxlength': '10',
                    'pattern': "[0-9]{10}"
                }
            ),
            'genero': forms.Select(
                choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')],
                attrs={'class': 'form-control'}
            ),
            'direccion': forms.HiddenInput(attrs={'id': 'id_direccion'}),
            'barrio': forms.Select(choices=BARRIO_CHOICES, attrs={'class': 'form-control'}),
            'zona_rural': forms.HiddenInput(attrs={'id': 'id_zona_rural'}),
            'etnia': forms.Select(choices=ETNIA_CHOICES, attrs={'class': 'form-control'}),
            'nivel_educativo': forms.Select(choices=EDUCACION_CHOICES, attrs={'class': 'form-control'}),
            'ocupacion': forms.Select(choices=OCUPACION_CHOICES, attrs={'class': 'form-control'}),
            'estrato': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '1', 'max': '3'}
            ),
            'estado': forms.Select(
                choices=[('A', 'Activo'), ('I', 'Inactivo')],
                attrs={'class': 'form-control'}
            ),
            'tiene_discapacidad': forms.CheckboxInput(
                attrs={'class': 'form-check-input', 'id': 'id_check_discapacidad'}
            ),
            'descripcion_discapacidad': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'id': 'id_desc_discapacidad',
                    'placeholder': 'Ej: Visual, Auditiva, Motriz, Cognitiva...'
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['estrato'].initial = 1
        self.fields['estado'].initial = 'A'
        self.fields['tiene_discapacidad'].required = False
        self.fields['primer_nombre'].required = True
        self.fields['segundo_nombre'].required = False
        self.fields['primer_apellido'].required = True
        self.fields['segundo_apellido'].required = True

    def clean_numero_documento(self):
        """Valida que el número de documento no esté duplicado."""
        numdoc = self.cleaned_data.get('numero_documento')
        if numdoc:
            qs = Ciudadano.objects.filter(numero_documento=numdoc)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('Ya existe un ciudadano registrado con este número de documento.')
        return numdoc.strip() if numdoc else numdoc

    def clean_correo(self):
        """Valida formato de email si se proporciona."""
        email = self.cleaned_data.get('correo')
        if email:
            qs = Ciudadano.objects.filter(correo=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('Este correo electrónico ya está registrado.')
        return email

    def clean_telefono(self):
        """Valida formato de teléfono."""
        tlfno = self.cleaned_data.get('telefono')
        if tlfno:
            limpio = tlfno.replace(' ', '').replace('-', '')
            if not limpio.isdigit():
                raise ValidationError('El teléfono solo debe contener números.')
            if len(limpio) != 10:
                raise ValidationError('El teléfono debe tener exactamente 10 dígitos.')
        return tlfno


class AtencionForm(forms.ModelForm):
    """
    Formulario para registrar atenciones a ciudadanos.
    """
    class Meta:
        model = Atencion
        fields = [
            'ciudadano', 'prestamo',
            'fecha', 'hora_inicio', 'hora_fin',
            'estado', 'observaciones'
        ]
        labels = {
            'ciudadano': 'Ciudadano Atendido',
            'prestamo': 'Préstamo Vinculado (Opcional)',
            'fecha': 'Fecha de Atención',
            'hora_inicio': 'Hora de Inicio',
            'hora_fin': 'Hora de Finalización',
            'estado': 'Estado de la Atención',
            'observaciones': 'Observaciones / Notas',
        }
        widgets = {
            'ciudadano': forms.Select(attrs={'class': 'form-control'}),
            'prestamo': forms.Select(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'hora_inicio': forms.TimeInput(
                format='%H:%M',
                attrs={'class': 'form-control', 'type': 'time'}
            ),
            'hora_fin': forms.TimeInput(
                format='%H:%M',
                attrs={'class': 'form-control', 'type': 'time'}
            ),
            'estado': forms.Select(
                choices=[('P', 'Pendiente'), ('F', 'Finalizada'), ('C', 'Cancelada')],
                attrs={'class': 'form-control'}
            ),
            'observaciones': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Describe brevemente la atención realizada...'
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ciudadano'].required = False
        self.fields['prestamo'].required = False
        self.fields['ciudadano'].empty_label = '--- Seleccione un ciudadano ---'
        self.fields['prestamo'].empty_label = '--- Sin préstamo vinculado ---'
        self.fields['hora_fin'].required = False
        self.fields['estado'].initial = 'P'

    def clean(self):
        """Validar que la hora final no sea menor que la hora inicial."""
        cleaned_data = super().clean()
        hr_ini = cleaned_data.get('hora_inicio')
        hr_fin = cleaned_data.get('hora_fin')

        if hr_ini and hr_fin and hr_fin < hr_ini:
            self.add_error('hora_fin', 'La hora final no puede ser menor que la hora inicial.')

        return cleaned_data


class SatisfaccionForm(forms.ModelForm):
    """
    Formulario para registrar encuestas de satisfacción.
    Incluye validación de calificación (1-5).
    """
    fecha = forms.DateTimeField(
        label='Fecha y Hora del Reporte',
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(
            attrs={'class': 'form-control', 'type': 'datetime-local'}
        )
    )

    class Meta:
        model = Satisfaccion
        fields = ['atencion', 'calificacion', 'comentario', 'fecha']
        labels = {
            'atencion': 'Atención Evaluada',
            'calificacion': 'Calificación (1 a 5)',
            'comentario': 'Comentarios del Ciudadano',
        }
        widgets = {
            'atencion': forms.Select(attrs={'class': 'form-control'}),
            'calificacion': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '1', 'max': '5'}
            ),
            'comentario': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
        }

    def __init__(self, *args, **kwargs):
        """Inicializar campo de atención como opcional."""
        super().__init__(*args, **kwargs)
        self.fields['atencion'].required = False
        self.fields['atencion'].empty_label = '--- Seleccione una atención ---'

    def clean_calificacion(self):
        """Valida que la calificación esté entre 1 y 5."""
        calif = self.cleaned_data.get('calificacion')
        if calif is not None and (calif < 1 or calif > 5):
            raise ValidationError('La calificación debe estar entre 1 y 5 estrellas.')
        return calif


class ServicioForm(forms.ModelForm):
    """
    Formulario para registrar servicios prestados durante atenciones.
    """
    class Meta:
        model = Servicio
        fields = [
            'atencion', 'nombre', 'descripcion',
            'tipo', 'requiere_equipo', 'estado'
        ]
        labels = {
            'atencion': 'Atención Vinculada',
            'nombre': 'Nombre del Servicio',
            'descripcion': 'Descripción Detallada',
            'tipo': 'Categoría',
            'requiere_equipo': '¿Requiere equipo?',
            'estado': 'Estado'
        }
        widgets = {
            'atencion': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.Select(
                choices=NOMBRE_SERVICIO_CHOICES,
                attrs={'class': 'form-control'}
            ),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tipo': forms.Select(
                choices=TIPO_SERVICIO_CHOICES,
                attrs={'class': 'form-control'}
            ),
            'requiere_equipo': forms.Select(
                choices=[('S', 'Sí'), ('N', 'No')],
                attrs={'class': 'form-control'}
            ),
            'estado': forms.Select(
                choices=[('A', 'Activo'), ('I', 'Inactivo')],
                attrs={'class': 'form-control'}
            ),
        }

    def __init__(self, *args, **kwargs):
        """Inicializar campos con valores por defecto."""
        super().__init__(*args, **kwargs)
        self.fields['atencion'].required = False
        self.fields['atencion'].empty_label = '--- Seleccione una atención ---'
        self.fields['requiere_equipo'].initial = 'N'
        self.fields['estado'].initial = 'A'


MODULOS_WIZARD_CHOICES = [
    ('atencion_ciudadana', 'Atención ciudadana'),
    ('recursos_salas', 'Recursos y Salas'),
    ('cursos_talleres', 'Cursos y Talleres'),
    ('mantenimiento', 'Mantenimiento de equipos'),
    ('reportes', 'Reportes y exportaciones'),
]

CAPACIDADES_INFO = [
    {'codigo': 'ciudadanos',     'label': 'Ciudadanos',            'icono': '👤', 'descripcion': 'Consultar y registrar ciudadanos atendidos',               'grupo': 'Atención ciudadana'},
    {'codigo': 'atenciones',     'label': 'Atenciones',            'icono': '🎯', 'descripcion': 'Registrar atenciones al ciudadano',                        'grupo': 'Atención ciudadana'},
    {'codigo': 'servicios',      'label': 'Servicios',             'icono': '🛠️', 'descripcion': 'Registro de servicios prestados en cada atención',          'grupo': 'Atención ciudadana'},
    {'codigo': 'satisfaccion',   'label': 'Satisfacción',          'icono': '⭐', 'descripcion': 'Encuestas de satisfacción del ciudadano',                  'grupo': 'Atención ciudadana'},
    {'codigo': 'recursos',       'label': 'Recursos (inventario)', 'icono': '📦', 'descripcion': 'Gestión de equipos e inventario del PVD',                  'grupo': 'Recursos y Salas'},
    {'codigo': 'prestamos',      'label': 'Préstamos',             'icono': '🔄', 'descripcion': 'Préstamo de recursos y equipos a ciudadanos',              'grupo': 'Recursos y Salas'},
    {'codigo': 'salas',          'label': 'Salas',                 'icono': '🏛️', 'descripcion': 'Gestión de salas y espacios físicos del PVD',             'grupo': 'Recursos y Salas'},
    {'codigo': 'habilitaciones', 'label': 'Habilitación de salas', 'icono': '🔓', 'descripcion': 'Habilitar espacios y salas para uso programado',          'grupo': 'Recursos y Salas'},
    {'codigo': 'cursos',         'label': 'Cursos y Talleres',     'icono': '📚', 'descripcion': 'Formación ciudadana: cursos, inscripciones y asistencia',  'grupo': 'Formación'},
    {'codigo': 'mantenimiento',  'label': 'Mantenimiento',         'icono': '🔧', 'descripcion': 'Mantenimiento preventivo y correctivo de equipos',        'grupo': 'Mantenimiento'},
    {'codigo': 'reportes',       'label': 'Reportes',              'icono': '📊', 'descripcion': 'Estadísticas, indicadores y exportación a Excel',         'grupo': 'Reportes'},
]

def _agrupar_capacidades():
    from collections import OrderedDict
    grupos = OrderedDict()
    for cap in CAPACIDADES_INFO:
        g = cap['grupo']
        if g not in grupos:
            grupos[g] = []
        grupos[g].append(cap)
    return [{'grupo': g, 'capacidades': caps} for g, caps in grupos.items()]

CAPACIDADES_POR_GRUPO = _agrupar_capacidades()

MODULOS_INFO = [
    {
        'codigo': 'atencion_ciudadana',
        'label': 'Atención ciudadana',
        'icono': '👥',
        'descripcion': 'Registro y seguimiento de atenciones a la comunidad.',
        'incluye': ['Ciudadanos', 'Registrar ciudadano', 'Atenciones', 'Servicios', 'Satisfacción'],
    },
    {
        'codigo': 'recursos_salas',
        'label': 'Recursos y Salas',
        'icono': '💼',
        'descripcion': 'Inventario de equipos, préstamos y gestión de salas.',
        'incluye': ['Recursos', 'Préstamos de recursos', 'Salas', 'Habilitación de salas'],
    },
    {
        'codigo': 'cursos_talleres',
        'label': 'Cursos y Talleres',
        'icono': '📚',
        'descripcion': 'Formación ciudadana, sesiones, inscripciones y asistencia.',
        'incluye': ['Cursos', 'Sesiones', 'Inscripciones', 'Control de asistencia'],
    },
    {
        'codigo': 'mantenimiento',
        'label': 'Mantenimiento de equipos',
        'icono': '🔧',
        'descripcion': 'Registro de mantenimientos preventivos y correctivos.',
        'incluye': ['Mantenimiento preventivo', 'Mantenimiento correctivo'],
    },
    {
        'codigo': 'reportes',
        'label': 'Reportes y exportaciones',
        'icono': '📊',
        'descripcion': 'Estadísticas, indicadores y exportación de datos a Excel.',
        'incluye': ['Panel de reportes', 'Exportación a Excel', 'Indicadores KPI'],
    },
]


class ModulosHabilitadosForm(forms.Form):
    modulos = forms.MultipleChoiceField(
        choices=MODULOS_WIZARD_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Servicios funcionales del PVD',
    )


class AsignarAdminPVDForm(forms.Form):
    admin_a_cargo = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label='Administrador PVD a cargo',
        empty_label='— Sin asignación (se puede cambiar después) —',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['admin_a_cargo'].queryset = User.objects.filter(
            groups__name='Administrador PVD'
        ).order_by('first_name', 'last_name', 'username')


class PrestamoRecursoForm(forms.ModelForm):
    """
    Formulario para registrar préstamos de recursos.
    """
    fecha_entrega = forms.DateTimeField(
        label='Entrega',
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(
            attrs={'class': 'form-control', 'type': 'datetime-local'}
        )
    )
    fecha_devolucion = forms.DateTimeField(
        label='Devolución',
        required=False,
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(
            attrs={'class': 'form-control', 'type': 'datetime-local'}
        )
    )

    class Meta:
        model = PrestamoRecurso
        fields = ['recurso', 'fecha_entrega', 'fecha_devolucion', 'observaciones']
        widgets = {
            'recurso': forms.Select(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['recurso'].required = False
        self.fields['recurso'].empty_label = '--- Seleccione un recurso ---'

    def clean(self):
        from django.db.models import Q
        from django.utils import timezone
        cleaned_data = super().clean()
        recurso = cleaned_data.get('recurso')
        if recurso:
            now = timezone.now()
            activos = PrestamoRecurso.objects.filter(
                recurso=recurso
            ).filter(
                Q(fecha_devolucion__isnull=True) | Q(fecha_devolucion__gt=now)
            )
            if self.instance.pk:
                activos = activos.exclude(pk=self.instance.pk)
            if activos.exists():
                raise forms.ValidationError(
                    f'"{recurso}" ya está en préstamo y no ha sido devuelto. '
                    'Debe registrar su devolución antes de prestarlo nuevamente.'
                )
        return cleaned_data


class RecursoForm(forms.ModelForm):
    tipo_personalizado = forms.CharField(
        label='Nombre del recurso',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Adaptador HDMI',
        })
    )

    class Meta:
        model = Recurso
        fields = ['tipo', 'codigo', 'estado']
        widgets = {
            'tipo': forms.Select(
                choices=TIPO_RECURSO_CHOICES,
                attrs={'class': 'form-control', 'id': 'id_tipo'}
            ),
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: LAP-001',
            }),
            'estado': forms.Select(
                choices=[('A', 'Activo'), ('I', 'Inactivo')],
                attrs={'class': 'form-control'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['estado'].initial = 'A'

        # Tipos base siempre presentes
        base = ['Portátil', 'Video Beam', 'Televisor', 'Impresora Láser',
                'Impresora de Inyección', 'Computador de Mesa']
        # Tipos guardados en BD (incluye los creados con "Otro")
        from .models import Recurso as RecursoModel
        db_tipos = list(RecursoModel.objects.values_list('tipo', flat=True).distinct())
        todos = sorted(set(base) | set(db_tipos))
        choices = [('', '— Seleccione un tipo —')]
        choices += [(t, t) for t in todos]
        choices += [('__otro__', 'Otro...')]
        self.fields['tipo'].widget.choices = choices

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('tipo') == '__otro__':
            nombre = cleaned.get('tipo_personalizado', '').strip()
            if not nombre:
                self.add_error('tipo_personalizado', 'Escribe el nombre del nuevo recurso.')
            else:
                cleaned['tipo'] = nombre
        return cleaned


# ==============================================================================
# FORMULARIOS DE AUTENTICACIÓN Y USUARIOS
# ==============================================================================

class LoginForm(AuthenticationForm):
    """
    Formulario de inicio de sesión personalizado.
    """
    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese su usuario'
            }
        )
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese su contraseña'
            }
        )
    )


class PerfilUsuarioForm(forms.ModelForm):
    """
    Formulario para editar perfil de usuario y cambiar contraseña.
    """
    password1 = forms.CharField(
        label='Nueva contraseña',
        required=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Déjalo vacío si no deseas cambiarla'
            }
        )
    )
    password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        required=False,
        widget=forms.PasswordInput(
            attrs={'class': 'form-control'}
        )
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        """Validar que las contraseñas coincidan."""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 or password2:
            if not password1:
                self.add_error('password1', 'Requerido')
            if not password2:
                self.add_error('password2', 'Requerido')
            if password1 and password2 and password1 != password2:
                self.add_error('password2', 'No coinciden')

        return cleaned_data


class CrearUsuarioForm(UserCreationForm):
    """
    Formulario para crear Administradores TIC y PVD.
    El usuario y contraseña son ingresados manualmente por quien crea la cuenta.
    """
    primer_nombre = forms.CharField(
        label='Primer Nombre',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan'})
    )
    segundo_nombre = forms.CharField(
        label='Segundo Nombre',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'})
    )
    primer_apellido = forms.CharField(
        label='Primer Apellido',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Pérez'})
    )
    segundo_apellido = forms.CharField(
        label='Segundo Apellido',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'})
    )
    email = forms.EmailField(
        label='Correo electrónico',
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'})
    )

    class Meta:
        model = User
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: PVDJuan o admintic_nombre',
                'autocomplete': 'off',
            })
        }
        labels = {'username': 'Nombre de usuario'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña (mínimo 8 caracteres)',
            'autocomplete': 'new-password',
            'id': 'id_password1_visible',
        })
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repite la contraseña',
            'autocomplete': 'new-password',
        })
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'

    def save(self, commit=True):
        user = super().save(commit=False)
        primer_nombre  = self.cleaned_data.get('primer_nombre', '')
        segundo_nombre = self.cleaned_data.get('segundo_nombre', '')
        primer_apellido  = self.cleaned_data.get('primer_apellido', '')
        segundo_apellido = self.cleaned_data.get('segundo_apellido', '')
        user.first_name = f"{primer_nombre} {segundo_nombre}".strip()
        user.last_name  = f"{primer_apellido} {segundo_apellido}".strip()
        email = self.cleaned_data.get('email')
        if email:
            user.email = email
        if commit:
            user.save()
        return user


class PuntoViveDigitalForm(forms.ModelForm):
    """
    Formulario para crear y editar Puntos Vive Digital.
    """
    class Meta:
        model = PuntoViveDigital
        fields = [
            'nombre', 'direccion', 'barrio',
            'estado', 'descripcion', 'admin_a_cargo',
        ]
        labels = {
            'nombre': 'Nombre del Punto Vive Digital',
            'direccion': 'Dirección',
            'barrio': 'Barrio / Vereda',
            'estado': 'Estado',
            'descripcion': 'Descripción / Notas',
            'admin_a_cargo': 'Administrador PVD a cargo (referencia)',
        }
        widgets = {
            'nombre': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej: PVD Centro, PVD La María'
                }
            ),
            'direccion': forms.HiddenInput(attrs={'id': 'id_direccion'}),
            'barrio': forms.Select(
                choices=BARRIO_CHOICES,
                attrs={'class': 'form-control'}
            ),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Notas adicionales sobre el PVD'
                }
            ),
            'admin_a_cargo': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, wizard=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['admin_a_cargo'].queryset = User.objects.filter(
            groups__name='Administrador PVD'
        ).order_by('first_name', 'last_name', 'username')
        self.fields['admin_a_cargo'].empty_label = '— Sin asignación (se puede cambiar después) —'
        self.fields['admin_a_cargo'].required = False
        if wizard:
            del self.fields['admin_a_cargo']

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            qs = PuntoViveDigital.objects.filter(nombre__iexact=nombre.strip())
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    f'Ya existe un PVD con el nombre "{nombre.strip()}". '
                    'Cada Punto Vive Digital debe tener un nombre único.'
                )
        return nombre.strip() if nombre else nombre

    def clean_direccion(self):
        direccion = self.cleaned_data.get('direccion')
        if direccion:
            qs = PuntoViveDigital.objects.filter(direccion__iexact=direccion.strip())
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                pvd_existente = qs.first()
                raise ValidationError(
                    f'Esta dirección ya está registrada en el PVD "{pvd_existente.nombre}". '
                    'Verifica que no estés creando un punto duplicado.'
                )
        return direccion.strip() if direccion else direccion



# ==============================================================================
# FORMULARIOS DE SALAS
# ==============================================================================

class SalaForm(forms.ModelForm):
    """
    Formulario para crear y editar salas de un Punto Vive Digital.
    """
    class Meta:
        model = Sala
        fields = [
            'punto_vive_digital', 'nombre', 'descripcion',
            'capacidad', 'estado'
        ]
        labels = {
            'punto_vive_digital': 'Punto Vive Digital',
            'nombre': 'Nombre de la Sala',
            'descripcion': 'Descripción',
            'capacidad': 'Capacidad (personas)',
            'estado': 'Estado',
        }
        widgets = {
            'punto_vive_digital': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej: Sala de Capacitación, Sala de Navegación'
                }
            ),
            'descripcion': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Descripción de la sala y su propósito'
                }
            ),
            'capacidad': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Número de personas'}
            ),
            'estado': forms.Select(
                choices=[('A', 'Activo'), ('I', 'Inactivo'), ('M', 'En mantenimiento')],
                attrs={'class': 'form-control'}
            ),
        }

    def __init__(self, *args, **kwargs):
        """Inicializar campo de PVD como opcional si se pasa por contexto."""
        super().__init__(*args, **kwargs)
        self.fields['punto_vive_digital'].empty_label = '--- Seleccione un PVD ---'
        self.fields['estado'].initial = 'A'

    def clean_nombre(self):
        """Valida que no haya otra sala con el mismo nombre en el mismo PVD."""
        nombre = self.cleaned_data.get('nombre')
        pvd = self.cleaned_data.get('punto_vive_digital')

        if nombre and pvd:
            qs = Sala.objects.filter(nombre=nombre, punto_vive_digital=pvd)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('Ya existe una sala con este nombre en este PVD.')

        return nombre


# ==============================================================================
# FORMULARIO DE PERMISOS
# ==============================================================================

CATEGORIA_CHOICES = [
    ('', '— Seleccione una categoría —'),
    ('Reportes', 'Reportes'),
    ('Ciudadanos', 'Ciudadanos'),
    ('Atenciones', 'Atenciones'),
    ('Inventario', 'Inventario'),
    ('Infraestructura', 'Infraestructura'),
]


class PermisoDefinicionForm(forms.ModelForm):
    categoria = forms.ChoiceField(
        choices=CATEGORIA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Categoría',
    )

    class Meta:
        model = PermisoDefinicion
        fields = ['codigo', 'nombre', 'descripcion', 'categoria', 'activo', 'delegable_por_ofitic']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ej: ciudadanos.ver',
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ej: Consultar Ciudadanos',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del permiso...',
            }),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'delegable_por_ofitic': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'codigo': 'Código único',
            'nombre': 'Nombre visible',
            'descripcion': 'Descripción',
            'activo': 'Activo',
            'delegable_por_ofitic': 'Delegable por Ofitic (admin TIC)',
        }

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').strip().lower()
        qs = PermisoDefinicion.objects.filter(codigo=codigo)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Ya existe un permiso con este código.')
        return codigo


# ==============================================================================
# FORMULARIO DE HABILITACIÓN DE SALAS
# ==============================================================================

class HabilitacionSalaForm(forms.ModelForm):
    class Meta:
        model = HabilitacionSala
        fields = [
            'sala', 'tipo_uso', 'fecha',
            'hora_inicio', 'hora_fin',
            'solicitante', 'proposito',
            'capacidad_requerida', 'estado', 'observaciones',
        ]
        labels = {
            'sala': 'Sala',
            'tipo_uso': 'Tipo de Uso',
            'fecha': 'Fecha',
            'hora_inicio': 'Hora de Inicio',
            'hora_fin': 'Hora de Fin',
            'solicitante': 'Solicitante / Grupo',
            'proposito': 'Propósito / Descripción',
            'capacidad_requerida': 'Personas Esperadas',
            'estado': 'Estado',
            'observaciones': 'Observaciones',
        }
        widgets = {
            'sala': forms.Select(attrs={'class': 'form-control'}),
            'tipo_uso': forms.Select(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'hora_inicio': forms.TimeInput(
                format='%H:%M',
                attrs={'class': 'form-control', 'type': 'time'}
            ),
            'hora_fin': forms.TimeInput(
                format='%H:%M',
                attrs={'class': 'form-control', 'type': 'time'}
            ),
            'solicitante': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: Grupo comunitario, Empresa XYZ, Ciudadano'}
            ),
            'proposito': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe el propósito de uso de la sala...'}
            ),
            'capacidad_requerida': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '1', 'placeholder': 'N.º de personas'}
            ),
            'estado': forms.Select(
                choices=[('P', 'Pendiente'), ('C', 'Confirmada'), ('E', 'En curso'), ('F', 'Finalizada'), ('X', 'Cancelada')],
                attrs={'class': 'form-control'}
            ),
            'observaciones': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notas adicionales...'}
            ),
        }

    def __init__(self, *args, pvd_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proposito'].required = False
        self.fields['capacidad_requerida'].required = False
        self.fields['observaciones'].required = False
        self.fields['sala'].empty_label = '--- Seleccione una sala ---'
        if pvd_id:
            self.fields['sala'].queryset = Sala.objects.filter(
                punto_vive_digital_id=pvd_id, estado='A'
            ).order_by('nombre')
        else:
            self.fields['sala'].queryset = Sala.objects.filter(estado='A').order_by(
                'punto_vive_digital__nombre', 'nombre'
            )

    def clean(self):
        cleaned_data = super().clean()
        sala = cleaned_data.get('sala')
        fecha = cleaned_data.get('fecha')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')

        if hora_inicio and hora_fin and hora_fin <= hora_inicio:
            self.add_error('hora_fin', 'La hora de fin debe ser posterior a la hora de inicio.')
            return cleaned_data

        if sala and fecha and hora_inicio and hora_fin:
            qs = HabilitacionSala.objects.filter(
                sala=sala,
                fecha=fecha,
                estado__in=['P', 'C', 'E'],
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            conflictos = qs.filter(
                hora_inicio__lt=hora_fin,
                hora_fin__gt=hora_inicio
            )
            if conflictos.exists():
                c = conflictos.first()
                self.add_error(
                    None,
                    f'Conflicto: la sala ya tiene una habilitación de '
                    f'{c.hora_inicio.strftime("%H:%M")} a {c.hora_fin.strftime("%H:%M")} '
                    f'en esa fecha ({c.get_tipo_uso_display()} — {c.solicitante}).'
                )


# ==============================================================================
# CURSOS / TALLERES
# ==============================================================================

class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['nombre', 'descripcion', 'modalidad', 'poblacion_objetivo',
                  'fecha_inicio', 'fecha_fin', 'estado']
        labels = {
            'nombre': 'Nombre del Curso / Taller *',
            'descripcion': 'Descripción',
            'modalidad': 'Modalidad *',
            'poblacion_objetivo': 'Población Objetivo',
            'fecha_inicio': 'Fecha de Inicio *',
            'fecha_fin': 'Fecha de Fin (opcional)',
            'estado': 'Estado *',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Alfabetización Digital Básica'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción breve del curso...'}),
            'modalidad': forms.Select(attrs={'class': 'form-control'}),
            'poblacion_objetivo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Adultos mayores, jóvenes...'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        fecha_inicio = cleaned.get('fecha_inicio')
        fecha_fin = cleaned.get('fecha_fin')
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            self.add_error('fecha_fin', 'La fecha de fin no puede ser anterior a la de inicio.')
        return cleaned


class SesionCursoForm(forms.ModelForm):
    class Meta:
        model = SesionCurso
        fields = ['numero_sesion', 'fecha', 'hora_inicio', 'hora_fin', 'tema', 'contenido']
        labels = {
            'numero_sesion': 'N° de Sesión *',
            'fecha': 'Fecha *',
            'hora_inicio': 'Hora de Inicio *',
            'hora_fin': 'Hora de Fin *',
            'tema': 'Tema *',
            'contenido': 'Contenido / Descripción',
        }
        widgets = {
            'numero_sesion': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'tema': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Uso de correo electrónico'}),
            'contenido': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned = super().clean()
        hi = cleaned.get('hora_inicio')
        hf = cleaned.get('hora_fin')
        if hi and hf and hf <= hi:
            self.add_error('hora_fin', 'La hora de fin debe ser posterior a la de inicio.')
        return cleaned


class InscripcionCursoForm(forms.ModelForm):
    class Meta:
        model = InscripcionCurso
        fields = ['ciudadano', 'estado']
        labels = {
            'ciudadano': 'Ciudadano *',
            'estado': 'Estado',
        }
        widgets = {
            'ciudadano': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }


# ==============================================================================
# MANTENIMIENTO DE EQUIPOS
# ==============================================================================

class MantenimientoEquipoForm(forms.ModelForm):
    class Meta:
        model = MantenimientoEquipo
        fields = ['tipo', 'fecha', 'equipos_intervenidos', 'descripcion', 'hallazgos', 'acciones']
        labels = {
            'tipo': 'Tipo de Mantenimiento *',
            'fecha': 'Fecha *',
            'equipos_intervenidos': 'Equipos Intervenidos *',
            'descripcion': 'Descripción del Trabajo Realizado *',
            'hallazgos': 'Hallazgos',
            'acciones': 'Acciones / Recomendaciones',
        }
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'equipos_intervenidos': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ej. 5 computadores de mesa, 1 impresora...'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe el trabajo realizado...'}),
            'hallazgos': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Problemas encontrados...'}),
            'acciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Acciones tomadas o recomendaciones...'}),
        }



