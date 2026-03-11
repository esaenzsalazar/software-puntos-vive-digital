from django import forms
from .models import Ciudadano


class CiudadanoForm(forms.ModelForm):
    class Meta:
        model = Ciudadano
        fields = [
            'ciu_tpodoc',
            'ciu_numdoc',
            'ciu_nmbres',
            'ciu_aplldos',
            'ciu_fchancm',
            'ciu_email',
            'ciu_tlfno',
            'ciu_genro',
            'ciu_etnia',
            'ciu_nvleduc',
            'ciu_ocpcion',
            'ciu_discapacidad',
            'ciu_estrato',
            'ciu_estdo',
        ]
        widgets = {
            'ciu_tpodoc': forms.TextInput(attrs={'class': 'form-control'}),
            'ciu_numdoc': forms.TextInput(attrs={'class': 'form-control'}),
            'ciu_nmbres': forms.TextInput(attrs={'class': 'form-control'}),
            'ciu_aplldos': forms.TextInput(attrs={'class': 'form-control'}),
            'ciu_fchancm': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ciu_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'ciu_tlfno': forms.TextInput(attrs={'class': 'form-control'}),
            'ciu_genro': forms.TextInput(attrs={'class': 'form-control'}),
            'ciu_etnia': forms.TextInput(attrs={'class': 'form-control'}),
            'ciu_nvleduc': forms.TextInput(attrs={'class': 'form-control'}),
            'ciu_ocpcion': forms.TextInput(attrs={'class': 'form-control'}),
            'ciu_discapacidad': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ciu_estrato': forms.NumberInput(attrs={'class': 'form-control'}),
            'ciu_estdo': forms.TextInput(attrs={'class': 'form-control'}),
        }