from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import Ciudadano, Atencion, Satisfaccion, Servicio, PrestamoRecurso, Recurso, Operador, PuntoViveDigital

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
            'ciu_dircion': forms.HiddenInput(attrs={'id': 'id_ciu_dircion'}),
            'ciu_barrio': forms.Select(choices=BARRIO_CHOICES, attrs={'class': 'form-control'}),
            'ciu_zrural': forms.HiddenInput(attrs={'id': 'id_ciu_zrural'}),
            'ciu_etnia': forms.Select(choices=ETNIA_CHOICES, attrs={'class': 'form-control'}),
            'ciu_nvleduc': forms.Select(choices=EDUCACION_CHOICES, attrs={'class': 'form-control'}),
            'ciu_ocpcion': forms.Select(choices=OCUPACION_CHOICES, attrs={'class': 'form-control'}),
            'ciu_estrato': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '3'}),
            'ciu_estdo': forms.Select(choices=[('A', 'Activo'), ('I', 'Inactivo')], attrs={'class': 'form-control'}),
            'ciu_discapacidad': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_check_discapacidad'}),
            'ciu_desc_discapacidad': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_desc_discapacidad', 'placeholder': 'Ej: Visual, Auditiva, Motriz, Cognitiva...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ciu_estrato'].initial = 1
        self.fields['ciu_estdo'].initial = 'A'
        self.fields['ciu_discapacidad'].required = False

    def clean_ciu_numdoc(self):
        """Valida que el número de documento no esté duplicado."""
        numdoc = self.cleaned_data.get('ciu_numdoc')
        if numdoc:
            qs = Ciudadano.objects.filter(ciu_numdoc=numdoc)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('Ya existe un ciudadano registrado con este número de documento.')
        return numdoc.strip() if numdoc else numdoc

    def clean_ciu_email(self):
        """Valida formato de email si se proporciona."""
        email = self.cleaned_data.get('ciu_email')
        if email:
            qs = Ciudadano.objects.filter(ciu_email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('Este correo electrónico ya está registrado.')
        return email

    def clean_ciu_tlfno(self):
        """Valida formato de teléfono."""
        tlfno = self.cleaned_data.get('ciu_tlfno')
        if tlfno:
            limpio = tlfno.replace(' ', '').replace('-', '')
            if not limpio.isdigit():
                raise ValidationError('El teléfono solo debe contener números.')
            if len(limpio) < 7:
                raise ValidationError('El teléfono debe tener al menos 7 dígitos.')
        return tlfno


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

        # BLOQUEAR OPERADOR SI SE ASIGNÓ AUTOMÁTICAMENTE
        if 'initial' in kwargs and 'opr_cdgo' in kwargs['initial']:
            self.fields['opr_cdgo'].widget.attrs['readonly'] = True
            self.fields['opr_cdgo'].widget.attrs['style'] = 'pointer-events: none; background-color: #e2e8f0;'

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
            'sat_calif': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '5'}),
            'sat_cmntrio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['atn_cdgo'].required = False
        self.fields['atn_cdgo'].empty_label = '--- Seleccione una atención ---'

    def clean_sat_calif(self):
        """Valida que la calificación esté entre 1 y 5."""
        calif = self.cleaned_data.get('sat_calif')
        if calif is not None and (calif < 1 or calif > 5):
            raise ValidationError('La calificación debe estar entre 1 y 5 estrellas.')
        return calif


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['atn_cdgo', 'srv_nombre', 'srv_descr', 'srv_tipo', 'srv_reqeqp', 'srv_estdo']
        labels = {
            'atn_cdgo': 'Atención Vinculada', 'srv_nombre': 'Nombre del Servicio',
            'srv_descr': 'Descripción Detallada', 'srv_tipo': 'Categoría',
            'srv_reqeqp': '¿Requiere equipo?', 'srv_estdo': 'Estado'
        }
        widgets = {
            'atn_cdgo': forms.Select(attrs={'class': 'form-control'}),
            'srv_nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'srv_descr': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'srv_tipo': forms.Select(choices=TIPO_SERVICIO_CHOICES, attrs={'class': 'form-control'}),
            'srv_reqeqp': forms.Select(choices=[('S', 'Sí'), ('N', 'No')], attrs={'class': 'form-control'}),
            'srv_estdo': forms.Select(choices=[('A', 'Activo'), ('I', 'Inactivo')], attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['atn_cdgo'].required = False
        self.fields['atn_cdgo'].empty_label = '--- Seleccione una atención ---'
        self.fields['srv_reqeqp'].initial = 'N'
        self.fields['srv_estdo'].initial = 'A'


class PrestamoRecursoForm(forms.ModelForm):
    prs_fchent = forms.DateTimeField(label='Entrega', input_formats=['%Y-%m-%dT%H:%M'], widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}))
    prs_fchdev = forms.DateTimeField(label='Devolución', required=False, input_formats=['%Y-%m-%dT%H:%M'], widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}))
    class Meta:
        model = PrestamoRecurso
        fields = ['rec_cdgo', 'prs_fchent', 'prs_fchdev', 'prs_obs']
        widgets = {'rec_cdgo': forms.Select(attrs={'class': 'form-control'}), 'prs_obs': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rec_cdgo'].required = False
        self.fields['rec_cdgo'].empty_label = '--- Seleccione un recurso ---'


class RecursoForm(forms.ModelForm):
    class Meta:
        model = Recurso
        fields = ['rec_cdgo', 'rec_tipo', 'rec_estdo']
        widgets = {
            'rec_cdgo': forms.NumberInput(attrs={'class': 'form-control'}),
            'rec_tipo': forms.Select(choices=TIPO_RECURSO_CHOICES, attrs={'class': 'form-control'}),
            'rec_estdo': forms.Select(choices=[('A', 'Activo'), ('I', 'Inactivo')], attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rec_estdo'].initial = 'A'


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Usuario', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su usuario'}))
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su contraseña'}))


class PerfilUsuarioForm(forms.ModelForm):
    password1 = forms.CharField(label='Nueva contraseña', required=False, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Déjalo vacío si no deseas cambiarla'}))
    password2 = forms.CharField(label='Confirmar nueva contraseña', required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
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
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 or password2:
            if not password1: self.add_error('password1', 'Requerido')
            if not password2: self.add_error('password2', 'Requerido')
            if password1 and password2 and password1 != password2:
                self.add_error('password2', 'No coinciden')
        return cleaned_data


class CrearUsuarioForm(UserCreationForm):
    first_name = forms.CharField(label='Nombres (Importante para auto-asignar atenciones)', required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Lady'}))
    last_name = forms.CharField(label='Apellidos', required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Pérez'}))
    email = forms.EmailField(label='Correo electrónico', required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}))
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Ingrese el nombre de usuario'})
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class PuntoViveDigitalForm(forms.ModelForm):
    """Formulario para crear y editar Puntos Vive Digital."""
    class Meta:
        model = PuntoViveDigital
        fields = ['pvd_nombre', 'pvd_dircion', 'pvd_barrio', 'pvd_telefono', 'pvd_correo', 'pvd_estdo', 'pvd_descripcion']
        labels = {
            'pvd_nombre': 'Nombre del Punto Vive Digital',
            'pvd_dircion': 'Dirección',
            'pvd_barrio': 'Barrio / Vereda',
            'pvd_telefono': 'Teléfono',
            'pvd_correo': 'Correo electrónico',
            'pvd_estdo': 'Estado',
            'pvd_descripcion': 'Descripción / Notas',
        }
        widgets = {
            'pvd_nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: PVD Centro, PVD La María'}),
            'pvd_dircion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección completa'}),
            'pvd_barrio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Barrio o vereda'}),
            'pvd_telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono del PVD'}),
            'pvd_correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'pvd_estdo': forms.Select(attrs={'class': 'form-control'}),
            'pvd_descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notas adicionales sobre el PVD'}),
        }