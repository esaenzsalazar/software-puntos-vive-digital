from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView
from django.contrib import messages
from .models import Ciudadano, Atencion, Satisfaccion
from .forms import CiudadanoForm, AtencionForm, SatisfaccionForm

class PanelControlView(TemplateView):
    template_name = 'modulo_puntos/panel_control.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_ciudadanos'] = Ciudadano.objects.count()
        context['atenciones_registradas'] = Atencion.objects.count()
        return context

class RegistrarCiudadanoView(CreateView):
    model = Ciudadano
    form_class = CiudadanoForm
    template_name = 'modulo_puntos/registrar_ciudadano.html'
    success_url = reverse_lazy('modulo_puntos:panel_control')

    def form_valid(self, form):
        messages.success(self.request, "Ciudadano registrado exitosamente en el sistema.")
        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)
        messages.error(self.request, "Error al registrar el ciudadano. Verifica los datos ingresados.")
        return super().form_invalid(form)

class RegistrarAtencionView(CreateView):
    model = Atencion
    form_class = AtencionForm
    template_name = 'modulo_puntos/registrar_atencion.html'
    success_url = reverse_lazy('modulo_puntos:panel_control')

    def form_valid(self, form):
        messages.success(self.request, "Atención registrada correctamente.")
        return super().form_valid(form)

class RegistrarSatisfaccionView(CreateView):
    model = Satisfaccion
    form_class = SatisfaccionForm
    template_name = 'modulo_puntos/registrar_satisfaccion.html'
    success_url = reverse_lazy('modulo_puntos:panel_control')

    def form_valid(self, form):
        messages.success(self.request, "Encuesta de satisfacción guardada con éxito.")
        return super().form_valid(form)