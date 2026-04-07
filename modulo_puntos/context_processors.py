"""Contexto global para navegación según permisos (contrato PVD / roles)."""
from .models import PuntoViveDigital


def pvd_navigation(request):
    rm = getattr(request, 'resolver_match', None)
    ctx = {
        'nav_pvd': False,
        'nav_tic': False,
        'nav_super': False,
        'current_url_name': getattr(rm, 'url_name', '') or '',
        'pvd_activo': None,
        'pvds_disponibles': [],
    }
    u = request.user
    if not u.is_authenticated:
        return ctx

    ctx['nav_super'] = u.is_superuser
    ctx['nav_tic'] = u.is_superuser or u.groups.filter(name='Administrador TIC').exists()
    ctx['nav_pvd'] = (
        u.is_superuser
        or ctx['nav_tic']
        or u.groups.filter(name='Administrador PVD').exists()
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
