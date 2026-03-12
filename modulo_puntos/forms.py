from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import Ciudadano, Atencion, Satisfaccion, Servicio


class CiudadanoForm(forms.ModelForm):
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
            'ciu_numdoc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de documento'}),
            'ciu_nmbres': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres completos'}),
            'ciu_aplldos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos completos'}),
            'ciu_fchancm': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ciu_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'ciu_tlfno': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono o celular'}),
            'ciu_genro': forms.Select(
                choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')],
                attrs={'class': 'form-control'}
            ),
            'ciu_etnia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Ninguna, Indígena, Afrocolombiano...'}),
            'ciu_nvleduc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Bachiller, Pregrado, Ninguno...'}),
            'ciu_ocpcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Estudiante, Empleado, Independiente...'}),
            'ciu_discapacidad': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ciu_estrato': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '6', 'value': '1'}),
            'ciu_estdo': forms.Select(
                choices=[('A', 'Activo'), ('I', 'Inactivo')],
                attrs={'class': 'form-control'}
            ),
        }


class AtencionForm(forms.ModelForm):
    class Meta:
        model = Atencion
        fields = ['atn_fecha', 'atn_hrini', 'atn_hrfin', 'atn_estdo', 'atn_obs']
        widgets = {
            'atn_fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'atn_hrini': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'atn_hrfin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'atn_estdo': forms.Select(
                choices=[('P', 'Pendiente'), ('F', 'Finalizada'), ('C', 'Cancelada')],
                attrs={'class': 'form-control'}
            ),
            'atn_obs': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observaciones de la atención...'}),
        }


class SatisfaccionForm(forms.ModelForm):
    class Meta:
        model = Satisfaccion
        fields = ['sat_calif', 'sat_cmntrio', 'sat_fecha']
        widgets = {
            'sat_calif': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '5', 'placeholder': 'Calificación (1 al 5)'}),
            'sat_cmntrio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Comentarios o sugerencias...'}),
            'sat_fecha': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['atn_cdgo', 'srv_nombre', 'srv_descr', 'srv_tipo', 'srv_reqeqp', 'srv_estdo']
        widgets = {
            'atn_cdgo': forms.Select(attrs={'class': 'form-control'}),
            'srv_nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del servicio'}),
            'srv_descr': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del servicio'}),
            'srv_tipo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tipo de servicio'}),
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