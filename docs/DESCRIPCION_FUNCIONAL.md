# Descripción funcional del sistema

## Marco contractual

El sistema da cumplimiento técnico a las obligaciones específicas del contrato de prestación de servicios de apoyo a la gestión en la Oficina TIC del Municipio de Bugalagrande (CD-224-2026), en particular:

1. **Caracterización de usuarios y servicios PVD** — Registro y consulta de ciudadanos; registro de servicios por atención.
2. **Estructura funcional** — Módulos separados para ciudadanos, atenciones, servicios, recursos, préstamos, satisfacción, usuarios y reportes.
3. **Modelo de datos** — Entidades relacionadas con trazabilidad (atención → ciudadano, operador; servicio → atención; satisfacción → atención). Variables socio-demográficas en el modelo de ciudadano (género, etnia, nivel educativo, ocupación, estrato, discapacidad, ubicación, contacto).
4. **Interfaces** — Formularios web responsive para registro, consulta y actualización.
5. **Consulta y reportes** — Panel de indicadores; desagregados por tipo de servicio, operador, perfiles de usuario; exportación CSV para consolidados externos.
6. **Satisfacción** — Registro de calificación y comentarios por atención; promedios en reportes e historial por ciudadano.

## Alcance fuera de software

Quedan para la entidad o el contratista en coordinación con el supervisor: capacitación presencial, pruebas de aceptación firmadas, hosting definitivo, respaldos en servidores del municipio y ajustes de catálogos (listas desplegables) según políticas nuevas.

## Seguridad y configuración

La conexión a base de datos y credenciales deben configurarse de forma segura en despliegue (idealmente variables de entorno y archivo `.env` no versionado). No comparta contraseñas de producción en repositorios públicos.
