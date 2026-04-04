from django import forms
from .models import Ciudadano, Atencion, Satisfaccion, Servicio, PrestamoRecurso, Recurso

class AtencionForm(forms.ModelForm):
    class Meta:
        model = Atencion
        fields = ['ciu_cdgo', 'opr_cdgo', 'atn_fecha', 'atn_hrini', 'atn_hrfin', 'atn_estdo', 'atn_obs']
        labels = {
            'ciu_cdgo': 'Seleccionar Ciudadano',
            'opr_cdgo': 'Operador Responsable',
            'atn_fecha': 'Fecha',
            'atn_hrini': 'Hora Inicio',
            'atn_hrfin': 'Hora Fin',
            'atn_estdo': 'Estado',
            'atn_obs': 'Observaciones'
        }
        widgets = {
            'atn_fecha': forms.DateInput(attrs={'type': 'date'}),
            'atn_hrini': forms.TimeInput(attrs={'type': 'time'}),
            'atn_hrfin': forms.TimeInput(attrs={'type': 'time'}),
            'atn_obs': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicamos clases para el estilo
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        
        # Lógica de bloqueo de operador que ya teníamos
        if 'initial' in kwargs and 'opr_cdgo' in kwargs['initial']:
            self.fields['opr_cdgo'].widget.attrs['readonly'] = True
            self.fields['opr_cdgo'].widget.attrs['style'] = 'background-color: #e9ecef; pointer-events: none;'

class CiudadanoForm(forms.ModelForm):
    class Meta:
        model = Ciudadano
        fields = '__all__'
        widgets = {
            'ciu_fchancm': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})