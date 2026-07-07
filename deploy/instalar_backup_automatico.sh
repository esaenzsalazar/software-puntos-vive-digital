#!/usr/bin/env bash
# ============================================================
# Instala el respaldo automático diario de la base de datos
# Puntos Vive Digital · Alcaldía de Bugalagrande
#
# USO (en el VPS de producción, una sola vez, como root o con sudo):
#   chmod +x deploy/instalar_backup_automatico.sh
#   sudo bash deploy/instalar_backup_automatico.sh
#
# QUÉ HACE:
#   1. Verifica que exista mysqldump.
#   2. Deja deploy/backup_pvd.sh ejecutable.
#   3. Prueba el respaldo una vez, ahí mismo, para confirmar que
#      las credenciales del .env funcionan.
#   4. Programa ese mismo script para correr todas las noches a
#      las 3:00 a.m. (hora del servidor) usando cron.
#      Si ya estaba programado, no lo duplica.
# ============================================================

set -euo pipefail

APP_DIR="/var/www/pvd"
SCRIPT="$APP_DIR/deploy/backup_pvd.sh"
LOG="/var/log/pvd/backup.log"
LINEA_CRON="0 3 * * * $SCRIPT >> $LOG 2>&1"

echo "=== [1/4] Verificando que mysqldump esté instalado ==="
if ! command -v mysqldump >/dev/null 2>&1; then
    echo "mysqldump no está instalado. Instalando cliente de MySQL..."
    apt-get update -qq
    apt-get install -y -qq default-mysql-client
fi

echo "=== [2/4] Dejando el script ejecutable ==="
chmod +x "$SCRIPT"
mkdir -p /var/log/pvd
touch "$LOG"

echo "=== [3/4] Probando el respaldo una vez (esto puede tardar unos segundos) ==="
"$SCRIPT"

echo "=== [4/4] Programando el respaldo diario a las 3:00 a.m. ==="
if crontab -l 2>/dev/null | grep -qF "$SCRIPT"; then
    echo "  Ya estaba programado. No se duplica."
else
    (crontab -l 2>/dev/null; echo "$LINEA_CRON") | crontab -
    echo "  Programado correctamente."
fi

echo ""
echo "============================================================"
echo "  LISTO. El respaldo corre solo todas las noches a las 3:00 a.m."
echo "  Copias guardadas en:   /var/backups/pvd/"
echo "  Log de cada corrida:   $LOG"
echo "  Para ver la programación: crontab -l"
echo "============================================================"
