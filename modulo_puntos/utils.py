"""
Utilidades para el sistema PVD - Contrato CD-224-2026
Funciones helper para auditoría, validaciones y otras utilidades.
"""
from django.contrib import messages
from django.contrib.messages import SUCCESS, ERROR, WARNING, INFO


def registrar_auditoria(request, accion, modelo_afectado=None, objeto_id=None, descripcion=None):
    """
    Registra una acción en la tabla de auditoría.
    
    Args:
        request: HttpRequest object
        accion: Tipo de acción (CREATE, UPDATE, DELETE, LOGIN, LOGOUT, EXPORT, OTHER)
        modelo_afectado: Nombre del modelo/tabla afectada
        objeto_id: ID del objeto afectado
        descripcion: Descripción detallada de la acción
    """
    try:
        from modulo_puntos.models import AuditoriaAccion
        
        usuario = request.user.username if request.user.is_authenticated else 'Anónimo'
        ip_address = get_client_ip(request)
        
        AuditoriaAccion.objects.create(
            usuario=usuario,
            accion=accion,
            modelo_afectado=modelo_afectado,
            objeto_id=str(objeto_id) if objeto_id else None,
            descripcion=descripcion or '',
            ip_address=ip_address,
        )
    except Exception as e:
        # No interrumpir el flujo si falla la auditoría
        pass


def get_client_ip(request):
    """Obtiene la IP real del cliente."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def mensaje_exito(request, texto):
    """Mensaje de éxito."""
    messages.success(request, texto)


def mensaje_error(request, texto):
    """Mensaje de error."""
    messages.error(request, texto)


def mensaje_advertencia(request, texto):
    """Mensaje de advertencia."""
    messages.warning(request, texto)


def mensaje_info(request, texto):
    """Mensaje informativo."""
    messages.info(request, texto)
