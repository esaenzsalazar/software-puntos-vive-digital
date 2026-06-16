# ============================================================
# Gunicorn — Configuración de producción
# Puntos Vive Digital · Alcaldía de Bugalagrande
# ============================================================
# Uso: gunicorn core.wsgi:application -c gunicorn.conf.py

# Dirección donde escucha (Nginx hace proxy a este puerto)
bind = "127.0.0.1:8000"

# Número de workers: regla general = 2 × CPUs + 1
# Para un VPS de 1 CPU (DigitalOcean $12/mes) usar 3
workers = 3

# Tiempo máximo por petición antes de matar el worker (segundos)
timeout = 120

# Reutilizar conexiones HTTP/1.1
keepalive = 5

# Reiniciar workers periódicamente para evitar fugas de memoria
max_requests = 1000
max_requests_jitter = 100

# Logs
loglevel = "warning"
accesslog = "/var/log/pvd/access.log"
errorlog  = "/var/log/pvd/error.log"

# PID del proceso principal
pidfile = "/tmp/pvd-gunicorn.pid"
