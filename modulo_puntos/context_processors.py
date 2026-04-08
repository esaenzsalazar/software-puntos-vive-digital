"""
Contexto global para navegación según permisos (contrato PVD / roles).
Proporciona variables de contexto disponibles en todos los templates.
"""
from .models import PuntoViveDigital


def pvd_navigation(request):
    """
    Context processor para proporcionar variables de navegación según el rol del usuario.
    
    Este processor agrega variables que determinan qué menú mostrar a cada usuario
    según sus permisos (Superuser, Admin TIC, Admin PVD).
    
    Args:
        request: HttpRequest object
        
    Returns:
        dict: Variables de contexto para los templates
    """
    rm = getattr(request, 'resolver_match', None)
    ctx = {
        'nav_pvd': False,  # Puede usar módulos del PVD
        'nav_tic': False,  # Es Admin TIC o Superuser
        'nav_super': False,  # Es Superuser
        'current_url_name': getattr(rm, 'url_name', '') or '',
        'pvd_activo': None,
        'pvds_disponibles': [],
    }
    
    u = request.user
    if not u.is_authenticated:
        return ctx

    # Determinar permisos de navegación
    ctx['nav_super'] = u.is_superuser
    ctx['nav_tic'] = u.is_superuser or u.groups.filter(name='Administrador TIC').exists()
    
    # Verificar si es SOLO Admin PVD (no superuser ni admin TIC)
    es_admin_pvd = u.groups.filter(name='Administrador PVD').exists()
    ctx['es_admin_pvd_only'] = es_admin_pvd and not u.is_superuser and not ctx['nav_tic']
    
    # Verificar si es SOLO Admin TIC (no superuser)
    ctx['es_admin_tic_only'] = u.groups.filter(name='Administrador TIC').exists() and not u.is_superuser
    
    # Verificar si es SOLO Superusuario
    ctx['es_superusuario'] = u.is_superuser
    
    ctx['nav_pvd'] = (
        u.is_superuser
        or ctx['nav_tic']
        or es_admin_pvd
    )

    # NO auto-seleccionar PVD - el usuario debe seleccionar manualmente
    pvd_id = request.session.get('pvd_activo_id')
    if pvd_id:
        try:
            pvd = PuntoViveDigital.objects.get(pk=pvd_id, pvd_estdo='A')
            # Solo usar si el PVD sigue activo
            ctx['pvd_activo'] = pvd
        except PuntoViveDigital.DoesNotExist:
            request.session.pop('pvd_activo_id', None)

    # Lista de PVDs disponibles (solo para la vista de selección)
    ctx['pvds_disponibles'] = list(
        PuntoViveDigital.objects.filter(pvd_estdo='A').order_by('pvd_nombre')
    )

    return ctx
