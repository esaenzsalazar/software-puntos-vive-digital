#!/usr/bin/env bash
# ============================================================
# Script de instalación en servidor Ubuntu 22.04
# Puntos Vive Digital · Alcaldía de Bugalagrande
#
# USO (en el VPS, como root o con sudo):
#   chmod +x setup.sh
#   sudo bash setup.sh
#
# PASOS PREVIOS:
#   - Tener el servidor Ubuntu 22.04 LTS con IP pública
#   - Tener el dominio (o subdominio) apuntando a la IP del servidor
#   - Haber subido el proyecto a /var/www/pvd (git clone o scp)
# ============================================================

set -e   # Detiene el script si cualquier comando falla

DOMINIO="pvd.bugalagrande.gov.co"    # ← CAMBIE ESTO antes de ejecutar
APP_DIR="/var/www/pvd"
LOG_DIR="/var/log/pvd"
PYTHON="$APP_DIR/entorno/bin/python"
PIP="$APP_DIR/entorno/bin/pip"

echo "=== [1/8] Actualizando sistema ==="
apt-get update -qq && apt-get upgrade -y -qq

echo "=== [2/8] Instalando dependencias del sistema ==="
apt-get install -y -qq \
    python3 python3-venv python3-dev \
    nginx \
    redis-server \
    certbot python3-certbot-nginx \
    default-libmysqlclient-dev build-essential \
    git curl

echo "=== [3/8] Preparando directorio del proyecto ==="
mkdir -p "$APP_DIR" "$LOG_DIR"
chown -R www-data:www-data "$LOG_DIR"

# Si el proyecto no está clonado aún, clonar aquí:
# git clone <URL_DEL_REPO> "$APP_DIR"

echo "=== [4/8] Creando entorno virtual e instalando dependencias Python ==="
python3 -m venv "$APP_DIR/entorno"
$PIP install --upgrade pip -q
$PIP install -r "$APP_DIR/requirements.txt" -q

echo "=== [5/8] Configurando variables de entorno ==="
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo ""
    echo "  IMPORTANTE: edite $APP_DIR/.env con los valores reales:"
    echo "    - DJANGO_SECRET_KEY  (clave única y secreta)"
    echo "    - DJANGO_DEBUG=False"
    echo "    - DJANGO_ALLOWED_HOSTS=$DOMINIO"
    echo "    - CSRF_TRUSTED_ORIGINS=https://$DOMINIO"
    echo "    - REDIS_URL=redis://127.0.0.1:6379/1"
    echo "    - Credenciales de Aiven MySQL"
    echo ""
    read -p "  Presione ENTER cuando haya editado .env..."
fi

echo "=== [6/8] Preparando Django para producción ==="
$PYTHON "$APP_DIR/manage.py" migrate --no-input
$PYTHON "$APP_DIR/manage.py" collectstatic --no-input
chown -R www-data:www-data "$APP_DIR"

echo "=== [7/8] Instalando servicio systemd ==="
sed "s|/var/www/pvd|$APP_DIR|g" "$APP_DIR/deploy/pvd.service" \
    > /etc/systemd/system/pvd.service
systemctl daemon-reload
systemctl enable pvd
systemctl start pvd

echo "=== [8/8] Configurando Nginx y SSL ==="
# Reemplazar dominio en la config de Nginx
sed "s/DOMINIO_AQUI/$DOMINIO/g" "$APP_DIR/deploy/nginx.conf" \
    > /etc/nginx/sites-available/pvd

# Activar el sitio
ln -sf /etc/nginx/sites-available/pvd /etc/nginx/sites-enabled/pvd
rm -f /etc/nginx/sites-enabled/default   # desactivar sitio por defecto

# Verificar configuración y recargar
nginx -t
systemctl reload nginx

# Obtener certificado SSL gratuito (Let's Encrypt)
certbot --nginx -d "$DOMINIO" --non-interactive --agree-tos \
    --email "alcaldiaesteban@gmail.com" --redirect

echo ""
echo "============================================================"
echo "  INSTALACIÓN COMPLETADA"
echo "  El sistema está disponible en: https://$DOMINIO"
echo ""
echo "  Comandos útiles:"
echo "    sudo systemctl status pvd          ← estado del servicio"
echo "    sudo systemctl restart pvd         ← reiniciar Django"
echo "    sudo journalctl -u pvd -f          ← logs en tiempo real"
echo "    sudo tail -f $LOG_DIR/pvd.log      ← logs de la aplicación"
echo "    sudo tail -f /var/log/nginx/pvd_error.log   ← logs de Nginx"
echo "============================================================"
