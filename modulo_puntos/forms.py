from django import forms
from .models import Ciudadano

class CiudadanoForm(forms.ModelForm):
    class Meta:
        model = Ciudadano
        fields = [
            'ciu_cdgo', 'ciu_tpodoc', 'ciu_numdoc', 'ciu_nmbres',
            'ciu_aplldos', 'ciu_fchancm', 'ciu_genro', 'ciu_etnia',
            'ciu_nvleduc', 'ciu_ocpcion', 'ciu_email', 'ciu_tlfno'
        ]
        widgets = {
            'ciu_fchancm': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'ciu_cdgo': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Código interno'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})