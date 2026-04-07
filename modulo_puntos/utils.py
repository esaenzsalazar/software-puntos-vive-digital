"""
Utilidades para el sistema PVD - Contrato CD-224-2026
Funciones helper para auditoría, validaciones y otras utilidades.
"""
from django.contrib import messages


def registrar_auditoria(request, accion, modelo_afectado=None, objeto_id=None, descripcion=None):
    """
    Registra una acción en la tabla de auditoría.
    
    Esta función permite rastrear todas las acciones importantes del sistema,
    incluyendo creaciones, actualizaciones, eliminaciones, exports, etc.
    
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
    except Exception:
        # No interrumpir el flujo si falla la auditoría
        pass


def get_client_ip(request):
    """
    Obtiene la IP real del cliente.
    
    Primero intenta obtener la IP de los encabezados X-Forwarded-For
    (útil cuando hay proxies/load balancers), y si no, usa REMOTE_ADDR.
    
    Args:
        request: HttpRequest object
        
    Returns:
        str: Dirección IP del cliente
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For puede tener múltiples IPs separadas por comas
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def mensaje_exito(request, texto):
    """Muestra un mensaje de éxito al usuario."""
    messages.success(request, texto)


def mensaje_error(request, texto):
    """Muestra un mensaje de error al usuario."""
    messages.error(request, texto)


def mensaje_advertencia(request, texto):
    """Muestra un mensaje de advertencia al usuario."""
    messages.warning(request, texto)


def mensaje_info(request, texto):
    """Muestra un mensaje informativo al usuario."""
    messages.info(request, texto)
