#!/usr/bin/env bash
# ============================================================
# Respaldo diario de la base de datos
# Puntos Vive Digital · Alcaldía de Bugalagrande
#
# QUÉ HACE:
#   Se conecta a la base de datos (con las mismas credenciales que
#   usa Django, leídas de .env), saca una copia comprimida y la
#   guarda en $DESTINO. Borra las copias de más de $RETENCION_DIAS
#   días para no llenar el disco.
#
# NO SE EJECUTA A MANO TODOS LOS DÍAS: se programa una sola vez
# con deploy/instalar_backup_automatico.sh (ver ese archivo) y
# desde ahí corre solo, todas las noches.
# ============================================================

set -euo pipefail

APP_DIR="/var/www/pvd"
ENV_FILE="$APP_DIR/.env"
DESTINO="/var/backups/pvd"
RETENCION_DIAS=30

if [ ! -f "$ENV_FILE" ]; then
    echo "No se encontró $ENV_FILE. Este script debe correr en el servidor de producción." >&2
    exit 1
fi

# Carga DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME desde el .env de Django
# (las mismas variables que usa core/settings.py) sin escribirlas en este archivo.
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

FECHA=$(date +%Y%m%d_%H%M%S)
ARCHIVO="$DESTINO/pvd_${FECHA}.sql.gz"

mkdir -p "$DESTINO"

mysqldump \
  --host="$DB_HOST" --port="${DB_PORT:-3306}" \
  --user="$DB_USER" --password="$DB_PASSWORD" \
  --single-transaction --routines --triggers \
  "$DB_NAME" | gzip > "$ARCHIVO"

# Elimina respaldos locales más viejos que RETENCION_DIAS
find "$DESTINO" -name 'pvd_*.sql.gz' -mtime +"$RETENCION_DIAS" -delete

echo "$(date '+%Y-%m-%d %H:%M:%S') — Respaldo guardado en $ARCHIVO ($(du -h "$ARCHIVO" | cut -f1))"
