# Puntos Vive Digital - Sistema de Gestión

## Descripción
Sistema web para la gestión de Puntos Vive Digital (PVD) en Bugalagrande, Colombia. Administra atenciones a ciudadanos, recursos, préstamos, cursos, salas, mantenimientos y permisos de usuario.

## Stack Técnico
- **Backend**: Django 5.x, Python 3.14
- **Base de datos**: MySQL (Aiven Cloud)
- **Frontend**: Django templates, sin framework JS externo
- **Excel**: openpyxl
- **Autenticación**: Django auth + sistema RBAC propio
- **Entorno virtual**: `entorno\Scripts\` (Windows)

## Estructura principal
- `modulo_puntos/models.py` — todos los modelos
- `modulo_puntos/views.py` — todas las vistas (~3000+ líneas)
- `modulo_puntos/forms.py` — formularios
- `modulo_puntos/utils.py` — utilidades (auditoría, permisos: `tiene_permiso(user, codigo)`)
- `modulo_puntos/context_processors.py` — navegación global, breadcrumb automático, botones de topbar
- `modulo_puntos/urls.py` — rutas
- `templates/modulo_puntos/` — plantillas HTML
- `templates/modulo_puntos/base.html` — layout principal (sidebar + topbar)
- `templates/registration/login.html` — login con diseño split-panel institucional
- `core/settings.py` — configuración Django
- `static/css/pvd-theme.css` — tema CSS completo

## Roles de usuario
- **Superusuario**: acceso total
- **Administrador TIC** (grupo `Administrador TIC`): gestión global, ve todos los PVDs
- **Administrador PVD** (grupo `Administrador PVD`): solo ve y gestiona su(s) PVD(s) asignado(s)

> El rol "Operador" fue eliminado (migración 0010). Admin PVD absorbió sus funciones.
> `RegistroApertura` (apertura/cierre de jornada) fue eliminado completamente (migración 0015).

## Flujo de Admin PVD
1. Hace login → si tiene un solo PVD asignado, se asigna automáticamente en sesión
2. Si tiene varios PVDs, va a `seleccionar_pvd_view` para elegir
3. El PVD activo se guarda en `request.session['pvd_activo_id']`
4. No existe más lógica de apertura/cierre de jornada (fue eliminada)

## Sistema de Permisos (RBAC propio)
- `PermisoDefinicion` — define cada permiso (`codigo`, `nombre`, `descripcion`, `delegable_por_ofitic`)
- `PermisoRol` — asigna permisos por defecto a roles (Admin TIC / Admin PVD)
- `PermisoUsuario` — sobreescritura individual por usuario
- `tiene_permiso(user, codigo)` en `utils.py`: superuser siempre true → PermisoUsuario → PermisoRol
- `delegable_por_ofitic`: el Superusuario activa qué permisos puede el Admin TIC delegar a Admin PVD
- Vista `lista_permisos_roles` (solo TIC/Super): matriz de permisos por rol + sección de delegables
- Vista `vista_permisos_ofitic`: Admin TIC delega permisos individuales a Admin PVD
- Vista `permisos_usuario`: ajuste de permisos individuales por usuario

## Context Processor (`pvd_navigation`)
Disponible en todos los templates. Variables que inyecta:
- `nav_super`, `nav_tic`, `nav_pvd` — booleanos de rol
- `es_superusuario`, `es_admin_tic_only`, `es_admin_pvd_only` — booleanos específicos
- `pvd_activo` — objeto PuntoViveDigital activo (de sesión) o None
- `pvds_disponibles` — lista de PVDs activos
- `bc_label` — label de la página actual
- `bc_parent_label` — label del padre (sustituye "Panel" por el nombre del PVD activo si hay uno)
- `bc_parent_url` — URL del padre (pre-resuelta en Python)
- `topbar_actions` — lista de `{label, url, css}` con botones contextuales según la página actual
  - `''` = botón azul primario (base `.btn`)
  - `'btn-secondary'` = botón gris secundario
  - Usa sentinel `__back__` para botones de cancelar que apuntan a `bc_parent_url`

## Topbar y Breadcrumb
- Breadcrumb automático basado en `_BREADCRUMB_MAP` en `context_processors.py`
- Cuando hay PVD activo: padre de sub-páginas muestra nombre del PVD en lugar de "Panel"
- Botones de topbar automáticos por página definidos en `_TOPBAR_ACTIONS`:
  - Panel: "↓ Exportar" + "+ Nueva atención"
  - Ciudadanos: "+ Registrar ciudadano"
  - Recursos: "+ Préstamo" + "+ Nuevo recurso"
  - Listas (salas, cursos, pvd, mantenimientos): botón "+ Nuevo..."
  - Formularios (crear/editar): "← Cancelar" que vuelve al padre

## Exportaciones Excel
Todas las exportaciones usan `_crear_hoja()` → openpyxl con:
- Cabecera oscura (#0B1220), texto blanco
- Filas pares con fondo azul claro (#EFF6FF)
- Bordes en todas las celdas
- Columna "Punto Vive Digital" en todos los reportes
- Filtrado automático por PVD activo cuando el usuario es Admin PVD

Exportaciones disponibles:
- `/exportar-atenciones/` → Atenciones
- `/exportar-ciudadanos/` → Ciudadanos
- `/exportar-servicios/` → Servicios
- `/exportar-satisfaccion/` → Encuestas
- `/exportar-prestamos/` → Préstamos de recursos

## Página de Reportes (`templates/modulo_puntos/reportes.html`)
Estructura organizada en secciones:
1. **Hero + filtro de fechas + panel de exportación** (un solo card)
2. **KPIs** — 5 stat-cards (ciudadanos, atenciones, servicios, préstamos, satisfacción)
3. **Layout 2 columnas**:
   - Izquierda: "Perfil de ciudadanos" — filas con mini barra proporcional (género, discapacidad, estrato, etnia, nivel educativo, ocupación)
   - Derecha: 3 cards apilados (atenciones por mes, servicios por tipo, atenciones por admin PVD)
4. **Últimas atenciones** — tabla `.table` con badge de estado (Pendiente=warning, Finalizada=success, Cancelada=danger)

## Login (`templates/registration/login.html`)
Diseño split-panel:
- Panel izquierdo: fondo degradado oscuro, logos (logo-alcaldia.png + logo-pvd.png), título, 3 stats (puntos activos, 24/7, 100% en línea), footer "Puntos Vive Digital"
- Panel derecho: formulario usuario/contraseña con toggle de visibilidad
- Sin link de correo, sin features marketing, sin referencia a contrato

## Clases CSS relevantes (`pvd-theme.css`)
- `.btn` — botón azul primario
- `.btn-secondary` — botón gris secundario
- `.btn--sm` — tamaño pequeño
- `.stat-card`, `.stat-card--accent-*` — KPI cards con borde de color
- `.table` + `.table-responsive` — tablas de datos
- `.badge`, `.badge-success/danger/warning/info` — etiquetas de estado
- `.card` — contenedor con sombra y borde
- `.menu-card` — tarjeta de acceso/módulo (min-height 172px, NO usar para datos)
- `.page-hero` — cabecera de página con eyebrow + título + descripción
- `.export-panel` — `<details>` expandible para exportación

## Modelos clave
- `PuntoViveDigital` — punto/sede (estado: A=activo)
- `UserProfile` — perfil con rol y PVD asignado
- `Ciudadano` — ciudadano atendido
- `Atencion` (estados: P=Pendiente, F=Finalizada, C=Cancelada) → `Servicio`, `Satisfaccion`
- `Recurso` → `PrestamoRecurso` — recursos y préstamos
- `Curso` → `SesionCurso` → `InscripcionCurso` → `AsistenciaSesion` — formación
- `Sala` → `HabilitacionSala` — gestión de salas
- `MantenimientoEquipo` — mantenimiento
- `PermisoDefinicion`, `PermisoRol`, `PermisoUsuario` — RBAC propio
- `AuditoriaAccion` — log de auditoría

## Comandos útiles
```bash
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
# Instalar dependencias en el entorno virtual (Windows):
& ".\entorno\Scripts\pip.exe" install <paquete>
```

## Notas importantes
- En Windows usar PowerShell con `& ".\entorno\Scripts\python.exe"` para ejecutar comandos del entorno
- El CSS base `.btn` ya ES el botón azul primario — no existe `.btn-primary`
- `menu-card` es para módulos/accesos, NO para mostrar datos tabulares
- `widthratio` de Django templates sirve para calcular porcentajes: `{% widthratio value total 100 %}`
- Siempre verificar con `python manage.py check` antes de declarar que algo está listo
