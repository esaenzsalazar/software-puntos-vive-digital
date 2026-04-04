# Manual de usuario — Sistema PVD Bugalagrande

Aplicación web para caracterización de usuarios (ciudadanos), registro de atenciones en el Punto Vive Digital, servicios prestados, inventario, préstamos y satisfacción. Alineado al objeto del contrato CD-224-2026 (apoyo a la gestión TIC).

## Acceso

1. Abra la URL que le indique la Oficina TIC (por ejemplo `http://127.0.0.1:8000/` en pruebas locales).
2. Inicie sesión con el usuario y contraseña asignados.
3. Use **Panel** para ir al menú principal; **Ayuda** resume flujos y exportaciones.

## Módulos principales

| Módulo | Uso |
|--------|-----|
| Consultar ciudadanos | Búsqueda por documento o nombre; edición e historial. |
| Registrar ciudadano | Caracterización con variables socio-demográficas definidas en el formulario. |
| Registrar atención | Vincula ciudadano, operador, fecha, horas y observaciones (trazabilidad). |
| Registrar servicio | Asocia tipo y detalle del servicio a una atención. |
| Registrar recurso / préstamo | Inventario y movimientos de equipos o elementos. |
| Registrar satisfacción | Calificación (1–5) y comentario por atención. |
| Reportes | Indicadores en pantalla y descarga de CSV para Excel. |

## Roles

- **Administrador PVD:** operación diaria del punto y reportes.
- **Administrador TIC:** además, creación de usuarios PVD (y operador asociado).
- **Superusuario:** creación de administradores TIC y acceso completo.

## Exportación (CSV)

En **Reportes** use los botones de descarga. Los archivos incluyen BOM UTF-8 para tildes y ñ. Puede abrirlos con Excel o LibreOffice Calc.

## Soporte

Ante errores de permisos o datos, contacte al supervisor TIC del contrato. Los datos sensibles deben manejarse según políticas de la entidad y la Ley 1581 de 2012 (habeas data).
