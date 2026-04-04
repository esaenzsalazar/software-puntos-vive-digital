"""Contexto global para navegación lateral según permisos (contrato PVD / roles)."""


def pvd_navigation(request):
    rm = getattr(request, 'resolver_match', None)
    ctx = {
        'nav_pvd': False,
        'nav_tic': False,
        'nav_super': False,
        'current_url_name': getattr(rm, 'url_name', '') or '',
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
    return ctx
