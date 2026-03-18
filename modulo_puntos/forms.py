from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import Ciudadano, Atencion, Satisfaccion, Servicio, PrestamoRecurso, Recurso
from .models import Ciudadano, Atencion, Satisfaccion, Servicio, PrestamoRecurso, Recurso, Operador
from .models import Ciudadano, Atencion, Satisfaccion, Servicio, PrestamoRecurso


class CiudadanoForm(forms.ModelForm):
    ciu_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        })
    )

    class Meta:
        model = Ciudadano
        fields = [
            'ciu_tpodoc', 'ciu_numdoc', 'ciu_nmbres', 'ciu_aplldos',
            'ciu_fchancm', 'ciu_email', 'ciu_tlfno', 'ciu_genro',
            'ciu_etnia', 'ciu_nvleduc', 'ciu_ocpcion', 'ciu_discapacidad',
            'ciu_estrato', 'ciu_estdo'
        ]
        widgets = {
            'ciu_tpodoc': forms.Select(
                choices=[
                    ('CC', 'Cédula de Ciudadanía'),
                    ('TI', 'Tarjeta de Identidad'),
                    ('CE', 'Cédula de Extranjería'),
                    ('PP', 'Pasaporte')
                ],
                attrs={'class': 'form-control'}
            ),
            'ciu_numdoc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de documento'
            }),
            'ciu_nmbres': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombres completos'
            }),
            'ciu_aplldos': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellidos completos'
            }),
            'ciu_fchancm': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'ciu_tlfno': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono o celular'
            }),
            'ciu_genro': forms.Select(
                choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')],
                attrs={'class': 'form-control'}
            ),
            'ciu_etnia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Ninguna, Indígena, Afrocolombiano...'
            }),
            'ciu_nvleduc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Bachiller, Pregrado, Ninguno...'
            }),
            'ciu_ocpcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Estudiante, Empleado, Independiente...'
            }),
            'ciu_discapacidad': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ciu_estrato': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '6'
            }),
            'ciu_estdo': forms.Select(
                choices=[('A', 'Activo'), ('I', 'Inactivo')],
                attrs={'class': 'form-control'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ciu_estrato'].initial = 1
        self.fields['ciu_estdo'].initial = 'A'
        self.fields['ciu_discapacidad'].required = False


class AtencionForm(forms.ModelForm):
    class Meta:
        model = Atencion
        fields = ['ciu_cdgo', 'opr_cdgo', 'prs_cdgo', 'atn_fecha', 'atn_hrini', 'atn_hrfin', 'atn_estdo', 'atn_obs']
        widgets = {
            'ciu_cdgo': forms.Select(attrs={'class': 'form-control'}),
            'opr_cdgo': forms.Select(attrs={'class': 'form-control'}),
            'prs_cdgo': forms.Select(attrs={'class': 'form-control'}),
            'atn_fecha': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'atn_hrini': forms.TimeInput(
                format='%H:%M',
                attrs={'class': 'form-control', 'type': 'time'}
            ),
            'atn_hrfin': forms.TimeInput(
                format='%H:%M',
                attrs={'class': 'form-control', 'type': 'time'}
            ),
            'atn_estdo': forms.Select(
                choices=[('P', 'Pendiente'), ('F', 'Finalizada'), ('C', 'Cancelada')],
                attrs={'class': 'form-control'}
            ),
            'atn_obs': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones de la atención...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ciu_cdgo'].required = False
        self.fields['opr_cdgo'].required = False
        self.fields['prs_cdgo'].required = False
        self.fields['ciu_cdgo'].empty_label = 'Seleccione un ciudadano'
        self.fields['opr_cdgo'].empty_label = 'Seleccione un operador'
        self.fields['prs_cdgo'].empty_label = 'Seleccione un préstamo (opcional)'
        self.fields['atn_hrfin'].required = False
        self.fields['atn_estdo'].initial = 'P'

    def clean(self):
        cleaned_data = super().clean()
        hrini = cleaned_data.get('atn_hrini')
        hrfin = cleaned_data.get('atn_hrfin')

        if hrini and hrfin and hrfin < hrini:
            self.add_error('atn_hrfin', 'La hora final no puede ser menor que la hora inicial.')

        return cleaned_data


class SatisfaccionForm(forms.ModelForm):
    sat_fecha = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )

    class Meta:
        model = Satisfaccion
        fields = ['atn_cdgo', 'sat_calif', 'sat_cmntrio', 'sat_fecha']
        widgets = {
            'atn_cdgo': forms.Select(attrs={'class': 'form-control'}),
            'sat_calif': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5',
                'placeholder': 'Calificación (1 al 5)'
            }),
            'sat_cmntrio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Comentarios o sugerencias...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['atn_cdgo'].required = False
        self.fields['atn_cdgo'].empty_label = 'Seleccione una atención (opcional)'

    def clean_sat_calif(self):
        calif = self.cleaned_data.get('sat_calif')
        if calif is not None and (calif < 1 or calif > 5):
            raise forms.ValidationError('La calificación debe estar entre 1 y 5.')
        return calif


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['atn_cdgo', 'srv_nombre', 'srv_descr', 'srv_tipo', 'srv_reqeqp', 'srv_estdo']
        widgets = {
            'atn_cdgo': forms.Select(attrs={'class': 'form-control'}),
            'srv_nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del servicio'
            }),
            'srv_descr': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del servicio'
            }),
            'srv_tipo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tipo de servicio'
            }),
            'srv_reqeqp': forms.Select(
                choices=[('S', 'Sí'), ('N', 'No')],
                attrs={'class': 'form-control'}
            ),
            'srv_estdo': forms.Select(
                choices=[('A', 'Activo'), ('I', 'Inactivo')],
                attrs={'class': 'form-control'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['atn_cdgo'].required = False
        self.fields['atn_cdgo'].empty_label = 'Seleccione una atención (opcional)'
        self.fields['srv_reqeqp'].initial = 'N'
        self.fields['srv_estdo'].initial = 'A'


class PrestamoRecursoForm(forms.ModelForm):
    prs_fchent = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    prs_fchdev = forms.DateTimeField(
        required=False,
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )

    class Meta:
        model = PrestamoRecurso
        fields = ['rec_cdgo', 'prs_fchent', 'prs_fchdev', 'prs_obs']
        widgets = {
            'rec_cdgo': forms.Select(attrs={'class': 'form-control'}),
            'prs_obs': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones del equipo prestado...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rec_cdgo'].required = False
        self.fields['rec_cdgo'].empty_label = 'Seleccione un recurso (opcional)'

    def clean(self):
        cleaned_data = super().clean()
        fchent = cleaned_data.get('prs_fchent')
        fchdev = cleaned_data.get('prs_fchdev')

        if fchent and fchdev and fchdev < fchent:
            self.add_error('prs_fchdev', 'La fecha de devolución no puede ser menor que la fecha de entrega.')

        return cleaned_data

class RecursoForm(forms.ModelForm):
    class Meta:
        model = Recurso
        fields = ['rec_cdgo', 'rec_tipo', 'rec_estdo']
        widgets = {
            'rec_cdgo': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código del recurso'
            }),
            'rec_tipo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Portátil, Tablet, Diadema, Proyector'
            }),
            'rec_estdo': forms.Select(
                choices=[('A', 'Activo'), ('I', 'Inactivo')],
                attrs={'class': 'form-control'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rec_estdo'].initial = 'A'


class OperadorForm(forms.ModelForm):
    class Meta:
        model = Operador
        fields = [
            'opr_tpodoc',
            'opr_numdoc',
            'opr_nmbres',
            'opr_aplldos',
            'opr_email',
            'opr_tlfno',
            'opr_estdo',
        ]
        widgets = {
            'opr_tpodoc': forms.Select(
                choices=[
                    ('CC', 'Cédula de Ciudadanía'),
                    ('TI', 'Tarjeta de Identidad'),
                    ('CE', 'Cédula de Extranjería'),
                    ('PP', 'Pasaporte')
                ],
                attrs={'class': 'form-control'}
            ),
            'opr_numdoc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de documento'
            }),
            'opr_nmbres': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombres del operador'
            }),
            'opr_aplldos': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellidos del operador'
            }),
            'opr_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'opr_tlfno': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono o celular'
            }),
            'opr_estdo': forms.Select(
                choices=[('A', 'Activo'), ('I', 'Inactivo')],
                attrs={'class': 'form-control'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['opr_estdo'].initial = 'A'

class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Usuario')
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingrese su usuario'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña'
        })


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

        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingrese el usuario'
        })
        self.fields['first_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nombres'
        })
        self.fields['last_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Apellidos'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingrese una contraseña'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Repita la contraseña'
        })


class PerfilUsuarioForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Nueva contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Déjalo vacío si no deseas cambiarla'
        })
    )
    password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repite la nueva contraseña'
        })
    )

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
            if not password1:
                self.add_error('password1', 'Debes ingresar la nueva contraseña.')
            if not password2:
                self.add_error('password2', 'Debes confirmar la nueva contraseña.')

            if password1 and password2:
                if password1 != password2:
                    self.add_error('password2', 'Las contraseñas no coinciden.')
                else:
                    try:
                        validate_password(password1, self.instance)
                    except ValidationError as e:
                        self.add_error('password1', e)

        return cleaned_data