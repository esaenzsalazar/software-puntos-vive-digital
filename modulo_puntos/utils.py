"""
Utilidades para el sistema PVD - Contrato CD-224-2026
Funciones helper para auditoría, validaciones y otras utilidades.
"""
import re
import random
import string
from datetime import datetime
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


def generar_username(primer_nombre, segundo_nombre='', primer_apellido='', segundo_apellido='', rol='usuario'):
    """
    Genera un nombre de usuario único basado en los nombres y apellidos.
    
    Args:
        primer_nombre: Primer nombre del usuario
        segundo_nombre: Segundo nombre del usuario (opcional)
        primer_apellido: Primer apellido del usuario
        segundo_apellido: Segundo apellido del usuario (opcional)
        rol: Rol del usuario para prefijo (admin_tic, admin_pvd, usuario)
    
    Returns:
        str: Nombre de usuario generado
    """
    # Limpiar caracteres especiales y convertir a minúsculas
    def limpiar(texto):
        if not texto:
            return ''
        texto = texto.lower().strip()
        texto = texto.replace(' ', '')
        # Eliminar caracteres especiales excepto ñ y vocales acentuadas
        texto = re.sub(r'[^a-záéíóúñ]', '', texto)
        # Convertir vocales acentuadas a normales
        texto = texto.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        return texto
    
    primer_nombre = limpiar(primer_nombre)
    segundo_nombre = limpiar(segundo_nombre)
    primer_apellido = limpiar(primer_apellido)
    segundo_apellido = limpiar(segundo_apellido)
    
    # Generar username: primera letra del primer nombre + primer apellido completo
    if primer_apellido:
        username = primer_nombre[0] + primer_apellido if primer_nombre else primer_apellido
    else:
        username = primer_nombre
    
    # Agregar segundo apellido si existe
    if segundo_apellido:
        username += segundo_apellido[0]
    
    # Agregar un número aleatorio para unicidad
    numero = random.randint(100, 999)
    username = f"{username}{numero}"
    
    # Truncar a 30 caracteres (límite de Django)
    username = username[:30]
    
    return username


def generar_password(longitud=10):
    """
    Genera una contraseña segura aleatoria.
    
    Args:
        longitud: Longitud de la contraseña (por defecto 10)
    
    Returns:
        str: Contraseña generada
    """
    # Asegurar al menos una mayúscula, una minúscula, un número y un carácter especial
    mayusculas = random.choice(string.ascii_uppercase)
    minusculas = random.choice(string.ascii_lowercase)
    numeros = random.choice(string.digits)
    especiales = random.choice('!@#$%^&*')
    
    # Rellenar con caracteres aleatorios
    restante = longitud - 4
    caracteres = string.ascii_letters + string.digits + '!@#$%^&*'
    restante = ''.join(random.choice(caracteres) for _ in range(restante))
    
    # Combinar y mezclar
    password = list(mayusculas + minusculas + numeros + especiales + restante)
    random.shuffle(password)
    
    return ''.join(password)


def validar_formato_documento(documento):
    """
    Valida el formato de un número de documento.
    
    Args:
        documento: Número de documento a validar
    
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    if not documento:
        return False, 'El número de documento es requerido'
    
    documento = documento.strip()
    
    if not documento.isdigit():
        return False, 'El documento solo debe contener números'
    
    if len(documento) < 6:
        return False, 'El documento debe tener al menos 6 dígitos'
    
    if len(documento) > 20:
        return False, 'El documento no puede tener más de 20 dígitos'
    
    return True, ''


def validar_formato_direccion(direccion):
    """
    Valida el formato de una dirección.
    
    Args:
        direccion: Dirección a validar
    
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    if not direccion:
        return False, 'La dirección es requerida'
    
    direccion = direccion.strip()
    
    if len(direccion) < 5:
        return False, 'La dirección debe tener al menos 5 caracteres'
    
    if len(direccion) > 200:
        return False, 'La dirección no puede tener más de 200 caracteres'
    
    # Verificar que tenga al menos una palabra
    palabras = direccion.split()
    if len(palabras) < 2:
        return False, 'La dirección debe incluir calle y número al menos'
    
    return True, ''


def validar_formato_telefono(telefono):
    """
    Valida el formato de un número de teléfono.
    
    Args:
        telefono: Número de teléfono a validar
    
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    if not telefono:
        return False, 'El teléfono es requerido'
    
    telefono = telefono.strip().replace(' ', '').replace('-', '')
    
    if not telefono.isdigit():
        return False, 'El teléfono solo debe contener números'
    
    if len(telefono) < 7:
        return False, 'El teléfono debe tener al menos 7 dígitos'
    
    if len(telefono) > 15:
        return False, 'El teléfono no puede tener más de 15 dígitos'
    
    return True, ''


def validar_formato_email(email):
    """
    Valida el formato de un correo electrónico.
    
    Args:
        email: Correo electrónico a validar
    
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    if not email:
        return True, ''  # Email es opcional en muchos casos
    
    email = email.strip()
    
    # Regex básico para email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, 'El formato del correo electrónico no es válido'
    
    if len(email) > 100:
        return False, 'El correo electrónico no puede tener más de 100 caracteres'
    
    return True, ''
