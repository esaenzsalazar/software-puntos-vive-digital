from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import Ciudadano, Atencion, Satisfaccion, Servicio, PrestamoRecurso, Recurso, Operador

# --- LISTAS DE OPCIONES GLOBALES ---
BARRIO_CHOICES = [
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

TIPO_SERVICIO_CHOICES = [
    ('Navegación Libre', 'Navegación Libre (Internet)'), ('Capacitación', 'Capacitación / Curso'),
    ('Trámite en Línea', 'Trámite en Línea (Gobierno/Entidades)'), ('Entretenimiento', 'Entretenimiento / Juegos'),
    ('Impresión/Escáner', 'Servicio de Impresión o Escáner'), ('Otro', 'Otro'),
]

TIPO_RECURSO_CHOICES = [
    ('Computador de Mesa', 'Computador de Mesa'), ('Portátil', 'Computador Portátil'),
    ('Tablet', 'Tablet'), ('Diadema', 'Diadema / Audífonos'),
    ('Proyector', 'Video Beam / Proyector'), ('Impresora', 'Impresora / Escáner'),
    ('Mobiliario', 'Silla / Mesa'), ('Otro', 'Otro'),
]


class CiudadanoForm(forms.ModelForm):
    ciu_email = forms.EmailField(
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'})
    )

    class Meta:
        model = Ciudadano
        fields = [
            'ciu_tpodoc', 'ciu_numdoc', 'ciu_nmbres', 'ciu_aplldos',
            'ciu_fchancm', 'ciu_email', 'ciu_tlfno', 'ciu_genro',
            'ciu_dircion', 'ciu_barrio', 'ciu_zrural',
            'ciu_etnia', 'ciu_nvleduc', 'ciu_ocpcion', 'ciu_estrato', 
            'ciu_discapacidad', 'ciu_desc_discapacidad', 'ciu_estdo'
        ]
        labels = {
            'ciu_tpodoc': 'Tipo de Documento', 'ciu_numdoc': 'Número de Documento',
            'ciu_nmbres': 'Nombres Completos', 'ciu_aplldos': 'Apellidos Completos',
            'ciu_fchancm': 'Fecha de Nacimiento', 'ciu_genro': 'Género',
            'ciu_dircion': 'Dirección de Residencia', 'ciu_barrio': 'Barrio (Cabecera Municipal)',
            'ciu_zrural': 'Vereda / Corregimiento (Opcional)',
            'ciu_etnia': 'Pertenencia Étnica', 'ciu_nvleduc': 'Nivel Educativo',
            'ciu_ocpcion': 'Ocupación Actual', 'ciu_estrato': 'Estrato Socioeconómico',
            'ciu_discapacidad': '¿Tiene alguna discapacidad?',
            'ciu_desc_discapacidad': '¿Cuál discapacidad? (Descríbala)',
            'ciu_estdo': 'Estado en el Sistema', 'ciu_tlfno': 'Teléfono o Celular',
        }
        widgets = {
            'ciu_tpodoc': forms.Select(choices=[('CC', 'Cédula de Ciudadanía'), ('TI', 'Tarjeta de Identidad'), ('CE', 'Cédula de Extranjería'), ('RC', 'Registro Civil'), ('PA', 'Pasaporte'), ('PEP', 'Permiso Especial de Permanencia'), ('PPT', 'Permiso por Protección Temporal')], attrs={'class': 'form-control'}),
            'ciu_numdoc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de documento', 'oninput': "this.value = this.value.replace(/[^0-9]/g, '')"}),
            'ciu_nmbres': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres completos'}),
            'ciu_aplldos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos completos'}),
            'ciu_fchancm': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'ciu_tlfno': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 3001234567', 'oninput': "this.value = this.value.replace(/[^0-9]/g, '')", 'pattern': "[0-9]+"}),
            'ciu_genro': forms.Select(choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')], attrs={'class': 'form-control'}),
            
            # EL TRUCO: Ocultamos el campo real de dirección porque lo vamos a llenar con la interfaz gráfica
            'ciu_dircion': forms.HiddenInput(attrs={'id': 'id_ciu_dircion'}),
            'ciu_barrio': forms.Select(choices=BARRIO_CHOICES, attrs={'class': 'form-control'}),
            'ciu_zrural': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Vereda San Juan (Dejar vacío si vive en el pueblo)'}),
            
            'ciu_etnia': forms.Select(choices=ETNIA_CHOICES, attrs={'class': 'form-control'}),
            'ciu_nvleduc': forms.Select(choices=EDUCACION_CHOICES, attrs={'class': 'form-control'}),
            'ciu_ocpcion': forms.Select(choices=OCUPACION_CHOICES, attrs={'class': 'form-control'}),
            'ciu_estrato': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '6'}),
            'ciu_estdo': forms.Select(choices=[('A', 'Activo'), ('I', 'Inactivo')], attrs={'class': 'form-control'}),
            'ciu_discapacidad': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_check_discapacidad'}),
            'ciu_desc_discapacidad': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_desc_discapacidad', 'placeholder': 'Ej: Visual, Auditiva, Motriz, Cognitiva...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ciu_estrato'].initial = 1
        self.fields['ciu_estdo'].initial = 'A'
        self.fields['ciu_discapacidad'].required = False

# ... EL RESTO DEL ARCHIVO FORMS.PY SE MANTIENE EXACTAMENTE IGUAL ...
class AtencionForm(forms.ModelForm):
    class Meta:
        model = Atencion
        fields = ['ciu_cdgo', 'opr_cdgo', 'prs_cdgo', 'atn_fecha', 'atn_hrini', 'atn_hrfin', 'atn_estdo', 'atn_obs']
        labels = {
            'ciu_cdgo': 'Ciudadano Atendido', 'opr_cdgo': 'Operador a Cargo',
            'prs_cdgo': 'Préstamo Vinculado (Opcional)', 'atn_fecha': 'Fecha de Atención',
            'atn_hrini': 'Hora de Inicio', 'atn_hrfin': 'Hora de Finalización',
            'atn_estdo': 'Estado de la Atención', 'atn_obs': 'Observaciones / Notas',
        }
        widgets = {
            'ciu_cdgo': forms.Select(attrs={'class': 'form-control'}),
            'opr_cdgo': forms.Select(attrs={'class': 'form-control'}),
            'prs_cdgo': forms.Select(attrs={'class': 'form-control'}),
            'atn_fecha': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'atn_hrini': forms.TimeInput(format='%H:%M', attrs={'class': 'form-control', 'type': 'time'}),
            'atn_hrfin': forms.TimeInput(format='%H:%M', attrs={'class': 'form-control', 'type': 'time'}),
            'atn_estdo': forms.Select(choices=[('P', 'Pendiente'), ('F', 'Finalizada'), ('C', 'Cancelada')], attrs={'class': 'form-control'}),
            'atn_obs': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe brevemente la atención realizada...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ciu_cdgo'].required = False
        self.fields['opr_cdgo'].required = False
        self.fields['prs_cdgo'].required = False
        self.fields['ciu_cdgo'].empty_label = '--- Seleccione un ciudadano ---'
        self.fields['opr_cdgo'].empty_label = '--- Seleccione un operador ---'
        self.fields['prs_cdgo'].empty_label = '--- Sin préstamo vinculado ---'
        self.fields['atn_hrfin'].required = False
        self.fields['atn_estdo'].initial = 'P'

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('atn_hrini') and cleaned_data.get('atn_hrfin') and cleaned_data.get('atn_hrfin') < cleaned_data.get('atn_hrini'):
            self.add_error('atn_hrfin', 'La hora final no puede ser menor que la hora inicial.')
        return cleaned_data


class SatisfaccionForm(forms.ModelForm):
    sat_fecha = forms.DateTimeField(
        label='Fecha y Hora del Reporte',
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )

    class Meta:
        model = Satisfaccion
        fields = ['atn_cdgo', 'sat_calif', 'sat_cmntrio', 'sat_fecha']
        labels = {
            'atn_cdgo': 'Atención Evaluada', 'sat_calif': 'Calificación (1 a 5)',
            'sat_cmntrio': 'Comentarios del Ciudadano',
        }
        widgets = {
            'atn_cdgo': forms.Select(attrs={'class': 'form-control'}),
            'sat_calif': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '5', 'placeholder': 'Ej: 5 (Excelente)'}),
            'sat_cmntrio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Sugerencias, quejas o felicitaciones...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['atn_cdgo'].required = False
        self.fields['atn_cdgo'].empty_label = '--- Seleccione una atención (opcional) ---'

    def clean_sat_calif(self):
        calif = self.cleaned_data.get('sat_calif')
        if calif is not None and (calif < 1 or calif > 5):
            raise forms.ValidationError('La calificación debe estar entre 1 y 5.')
        return calif


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['atn_cdgo', 'srv_nombre', 'srv_descr', 'srv_tipo', 'srv_reqeqp', 'srv_estdo']
        labels = {
            'atn_cdgo': 'Atención Vinculada', 'srv_nombre': 'Nombre Específico del Servicio',
            'srv_descr': 'Descripción Detallada', 'srv_tipo': 'Categoría del Servicio',
            'srv_reqeqp': '¿Requiere equipo físico?', 'srv_estdo': 'Estado del Servicio'
        }
        widgets = {
            'atn_cdgo': forms.Select(attrs={'class': 'form-control'}),
            'srv_nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Creación correo Gmail'}),
            'srv_descr': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalles de lo que se le ayudó al ciudadano...'}),
            'srv_tipo': forms.Select(choices=TIPO_SERVICIO_CHOICES, attrs={'class': 'form-control'}),
            'srv_reqeqp': forms.Select(choices=[('S', 'Sí requiere'), ('N', 'No requiere')], attrs={'class': 'form-control'}),
            'srv_estdo': forms.Select(choices=[('A', 'Activo'), ('I', 'Inactivo')], attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['atn_cdgo'].required = False
        self.fields['atn_cdgo'].empty_label = '--- Seleccione una atención (opcional) ---'
        self.fields['srv_reqeqp'].initial = 'N'
        self.fields['srv_estdo'].initial = 'A'


class PrestamoRecursoForm(forms.ModelForm):
    prs_fchent = forms.DateTimeField(
        label='Fecha y Hora de Entrega',
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )
    prs_fchdev = forms.DateTimeField(
        label='Fecha y Hora de Devolución',
        required=False,
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )

    class Meta:
        model = PrestamoRecurso
        fields = ['rec_cdgo', 'prs_fchent', 'prs_fchdev', 'prs_obs']
        labels = {
            'rec_cdgo': 'Recurso / Equipo a Prestar', 'prs_obs': 'Observaciones del Equipo (Estado físico)'
        }
        widgets = {
            'rec_cdgo': forms.Select(attrs={'class': 'form-control'}),
            'prs_obs': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ej: Se entrega en buen estado, incluye cargador...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rec_cdgo'].required = False
        self.fields['rec_cdgo'].empty_label = '--- Seleccione un recurso ---'

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('prs_fchent') and cleaned_data.get('prs_fchdev') and cleaned_data.get('prs_fchdev') < cleaned_data.get('prs_fchent'):
            self.add_error('prs_fchdev', 'La fecha de devolución no puede ser menor que la fecha de entrega.')
        return cleaned_data

class RecursoForm(forms.ModelForm):
    class Meta:
        model = Recurso
        fields = ['rec_cdgo', 'rec_tipo', 'rec_estdo']
        labels = {
            'rec_cdgo': 'Código Interno (Inventario)', 'rec_tipo': 'Tipo de Recurso', 'rec_estdo': 'Estado Físico'
        }
        widgets = {
            'rec_cdgo': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 101, 102...'}),
            'rec_tipo': forms.Select(choices=TIPO_RECURSO_CHOICES, attrs={'class': 'form-control'}),
            'rec_estdo': forms.Select(choices=[('A', 'Activo / Buen Estado'), ('I', 'Inactivo / Dañado')], attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rec_estdo'].initial = 'A'


class OperadorForm(forms.ModelForm):
    class Meta:
        model = Operador
        fields = ['opr_tpodoc', 'opr_numdoc', 'opr_nmbres', 'opr_aplldos', 'opr_email', 'opr_tlfno', 'opr_estdo']
        labels = {
            'opr_tpodoc': 'Tipo de Documento', 'opr_numdoc': 'Número de Documento',
            'opr_nmbres': 'Nombres Completos', 'opr_aplldos': 'Apellidos Completos',
            'opr_email': 'Correo Electrónico', 'opr_tlfno': 'Teléfono o Celular',
            'opr_estdo': 'Estado Contractual'
        }
        widgets = {
            'opr_tpodoc': forms.Select(choices=[('CC', 'Cédula de Ciudadanía'), ('TI', 'Tarjeta de Identidad'), ('CE', 'Cédula de Extranjería'), ('PP', 'Pasaporte')], attrs={'class': 'form-control'}),
            'opr_numdoc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de documento', 'oninput': "this.value = this.value.replace(/[^0-9]/g, '')"}),
            'opr_nmbres': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres del operador'}),
            'opr_aplldos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos del operador'}),
            'opr_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'opr_tlfno': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono o celular', 'oninput': "this.value = this.value.replace(/[^0-9]/g, '')", 'pattern': "[0-9]+"}),
            'opr_estdo': forms.Select(choices=[('A', 'Activo'), ('I', 'Inactivo')], attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['opr_estdo'].initial = 'A'


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Usuario')
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}))
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Ingrese su usuario'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Ingrese su contraseña'})

class CrearUsuarioForm(UserCreationForm):
    first_name = forms.CharField(label='Nombres', required=False)
    last_name = forms.CharField(label='Apellidos', required=False)
    email = forms.EmailField(label='Correo electrónico', required=False)
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Usuario'
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Ingrese el usuario'})
        self.fields['first_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Nombres'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Apellidos'})
        self.fields['email'].widget.attrs.update({'class': 'form-control', 'placeholder': 'correo@ejemplo.com'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Ingrese una contraseña'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Repita la contraseña'})

class PerfilUsuarioForm(forms.ModelForm):
    password1 = forms.CharField(label='Nueva contraseña', required=False, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Déjalo vacío si no deseas cambiarla'}))
    password2 = forms.CharField(label='Confirmar nueva contraseña', required=False, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repite la nueva contraseña'}))
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
        }
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 or password2:
            if not password1: self.add_error('password1', 'Debes ingresar la nueva contraseña.')
            if not password2: self.add_error('password2', 'Debes confirmar la nueva contraseña.')
            if password1 and password2:
                if password1 != password2:
                    self.add_error('password2', 'Las contraseñas no coinciden.')
                else:
                    try:
                        validate_password(password1, self.instance)
                    except ValidationError as e:
                        self.add_error('password1', e)
        return cleaned_data