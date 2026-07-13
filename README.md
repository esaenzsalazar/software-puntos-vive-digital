# Sistema de Gestión — Puntos Vive Digital
### Alcaldía de Bugalagrande · 

Sistema web para la administración integral de los Puntos Vive Digital (PVD) del municipio de Bugalagrande, Valle del Cauca. Gestiona atenciones a ciudadanos, recursos, préstamos, cursos, salas, mantenimientos, evidencias y control de acceso por roles.

---

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Django 5.x · Python 3.13 |
| Base de datos | MySQL (Aiven Cloud) |
| Frontend | Django Templates · CSS propio (`pvd-theme.css`) |
| Exportación | openpyxl (Excel) |
| Producción | Gunicorn · WhiteNoise |

---

## Estructura del Proyecto

```
software-puntos-vive-digital/
├── core/                        # Configuración Django (settings, urls, wsgi)
├── modulo_puntos/               # Aplicación principal
│   ├── models.py                # Todos los modelos del sistema
│   ├── views.py                 # Todas las vistas (~3800 líneas)
│   ├── forms.py                 # Formularios con validación
│   ├── urls.py                  # Rutas de la aplicación
│   ├── context_processors.py   # Navegación, breadcrumb y topbar global
│   ├── utils.py                 # Auditoría y permisos RBAC
│   ├── admin.py                 # Panel de administración Django
│   ├── migrations/              # Historial de migraciones
│   └── management/commands/     # Comandos de gestión personalizados
├── templates/
│   ├── modulo_puntos/           # Plantillas HTML del sistema
│   └── registration/            # Login
├── static/
│   ├── css/pvd-theme.css        # Tema visual completo
│   ├── js/                      # Scripts de frontend
│   └── img/                     # Logos institucionales
├── deploy/                      # Configuración nginx, systemd y respaldo automático
├── docs/                        # Documentación entregada a la Alcaldía
├── manage.py
├── requirements.txt
└── gunicorn.conf.py
```

---

## Módulos del Sistema

| Módulo | Descripción |
|---|---|
| **Panel de control** | Dashboard con KPIs y acceso rápido por rol |
| **Ciudadanos** | Registro, historial y gestión de ciudadanos atendidos |
| **Atenciones** | Registro de atenciones con servicios y encuesta de satisfacción |
| **Recursos / Préstamos** | Inventario de recursos y control de préstamos |
| **Visualizar préstamos** | Vista global de préstamos de todos los PVDs |
| **Salas / Habilitaciones** | Gestión de salas y agenda semanal de habilitaciones |
| **Cursos** | Talleres, sesiones, inscripciones y asistencia |
| **Mantenimientos** | Registro de mantenimiento de equipos |
| **Evidencias** | Registro fotográfico de actividades |
| **Reportes** | Estadísticas, gráficas y exportación a Excel |
| **Puntos PVD** | Administración de sedes (solo TIC) |
| **Usuarios del sistema** | Creación de Administradores TIC y PVD |
| **Permisos** | Matriz RBAC por rol y delegación de permisos |
| **Accesos temporales** | Gestión de accesos con vigencia limitada |
| **Log de auditoría** | Trazabilidad de todas las acciones del sistema |

---

## Roles de Usuario

| Rol | Acceso |
|---|---|
| **Superusuario** | Acceso total al sistema |
| **Administrador TIC** | Gestión global, ve todos los PVDs |
| **Administrador PVD** | Solo gestiona su(s) PVD(s) asignado(s) |

El sistema utiliza un RBAC propio (`PermisoDefinicion` / `PermisoRol` / `PermisoUsuario`) que permite sobreescritura de permisos por usuario individual.

---

## Instalación Local

```bash
# 1. Clonar el repositorio
git clone https://github.com/alcaldiaesteban/software-puntos-vive-digital.git
cd software-puntos-vive-digital

# 2. Crear y activar entorno virtual
python -m venv entorno
source entorno/bin/activate          # Linux/Mac
# entorno\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con los datos de conexión a la base de datos

# 5. Aplicar migraciones
python manage.py migrate

# 6. Ejecutar servidor de desarrollo
python manage.py runserver
```

---

## Variables de Entorno

Crea un archivo `.env` en la raíz basado en `.env.example`:

```env
SECRET_KEY=tu_clave_secreta
DEBUG=True
DB_HOST=...
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_PORT=3306
```

---

## Despliegue en Producción

Los archivos de configuración para producción están en `deploy/`:

- `deploy/nginx.conf` — configuración de Nginx como proxy inverso
- `deploy/pvd.service` — servicio systemd para Gunicorn
- `deploy/setup.sh` — script de configuración del servidor
- `gunicorn.conf.py` — configuración de workers y bind

---

## Documentación

La carpeta `docs/` contiene:

- `Manual_Usuario_PVD.pdf` — manual de uso del sistema para administradores de PVD
- `Requisitos_Infraestructura_PVD.pdf` — requisitos técnicos entregados al área de Sistemas/TIC para levantar el servidor de producción
- `RESPALDOS.md` — estrategia de respaldo y restauración de la base de datos
- `Plantilla_Registro_Ciudadanos_PVD.xlsx` — plantilla para recolección de datos de ciudadanos

---

*Alcaldía Municipal de Bugalagrande · Valle del Cauca · 2026*
