from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class FlujoPvdPendienteMiddleware:
    """
    Al crear un PVD nuevo se guarda 'pvd_pendiente_id' en sesión y se obliga
    a completar la creación del Administrador PVD antes de navegar a
    cualquier otra parte del sistema.
    """
    RUTAS_LIBRES_PREFIJOS = ('/static/', '/media/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        pvd_pendiente_id = request.session.get('pvd_pendiente_id')
        if pvd_pendiente_id and request.user.is_authenticated:
            url_crear_usuario = reverse('modulo_puntos:crear_usuario_sistema')
            url_logout = reverse('modulo_puntos:logout')
            ruta_libre = (
                request.path in (url_crear_usuario, url_logout)
                or request.path.startswith(self.RUTAS_LIBRES_PREFIJOS)
            )
            if not ruta_libre:
                nombre_pvd = request.session.get('pvd_pendiente_nombre', '')
                messages.warning(
                    request,
                    f'Antes de continuar debes crear el Administrador PVD del punto "{nombre_pvd}".'
                )
                return redirect('modulo_puntos:crear_usuario_sistema')
        return self.get_response(request)
