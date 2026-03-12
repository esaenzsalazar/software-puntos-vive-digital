from django import forms
from .models import Ciudadano, Atencion, Satisfaccion

class CiudadanoForm(forms.ModelForm):
    class Meta:
        model = Ciudadano
        fields = [
            'ciu_tpodoc', 'ciu_numdoc', 'ciu_nmbres', 'ciu_aplldos',
            'ciu_fchancm', 'ciu_email', 'ciu_tlfno', 'ciu_genro',
            'ciu_etnia', 'ciu_nvleduc', 'ciu_ocpcion', 'ciu_estdo'
        ]
        widgets = {
            'ciu_tpodoc': forms.Select(choices=[('CC', 'Cédula de Ciudadanía'), ('TI', 'Tarjeta de Identidad'), ('CE', 'Cédula de Extranjería'), ('PP', 'Pasaporte')], attrs={'class': 'form-control'}),
            'ciu_numdoc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de documento'}),
            'ciu_nmbres': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres completos'}),
            'ciu_aplldos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos completos'}),
            'ciu_fchancm': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ciu_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'ciu_tlfno': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono o celular'}),
            'ciu_genro': forms.Select(choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')], attrs={'class': 'form-control'}),
            'ciu_etnia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Ninguna, Indígena, Afrocolombiano...'}),
            'ciu_nvleduc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Bachiller, Pregrado, Ninguno...'}),
            'ciu_ocpcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Estudiante, Empleado, Independiente...'}),
            'ciu_estdo': forms.Select(choices=[('A', 'Activo'), ('I', 'Inactivo')], attrs={'class': 'form-control'}),
        }

class AtencionForm(forms.ModelForm):
    class Meta:
        model = Atencion
        fields = ['atn_fecha', 'atn_hrini', 'atn_hrfin', 'atn_estdo', 'atn_obs']
        widgets = {
            'atn_fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'atn_hrini': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'atn_hrfin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'atn_estdo': forms.Select(choices=[('P', 'Pendiente'), ('F', 'Finalizada'), ('C', 'Cancelada')], attrs={'class': 'form-control'}),
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