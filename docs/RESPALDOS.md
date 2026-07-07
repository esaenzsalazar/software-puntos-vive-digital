# Estrategia de Respaldo — Puntos Vive Digital

## 1. Respaldo automático de Aiven (verificar primero)

La base de datos vive en Aiven Cloud (MySQL). Aiven toma backups automáticos
periódicos de las instancias administradas, con una ventana de retención que
depende del plan contratado. **Antes de configurar nada manual**, verificar
en la consola de Aiven (pestaña *Backups* del servicio):

- Que los backups automáticos estén activos.
- Cuántos días de retención tiene el plan actual (los planes de entrada
  suelen retener pocos días).
- Si el plan permite *point-in-time recovery* (restaurar a un instante
  específico) o sólo restaurar el snapshot más reciente.

Si la retención es corta (p. ej. 2-3 días) y se necesita más historial para
cumplir con la política de conservación de datos de la Alcaldía, hay que
subir de plan o complementar con el respaldo manual de la sección 2.

## 2. Respaldo manual complementario (`mysqldump`)

Recomendado como segunda copia independiente del proveedor, con retención
más larga y guardada fuera de Aiven.

```bash
#!/usr/bin/env bash
# backup_pvd.sh — respaldo diario de la base de datos PVD
set -euo pipefail

FECHA=$(date +%Y%m%d_%H%M%S)
DESTINO="/var/backups/pvd"
ARCHIVO="$DESTINO/pvd_$FECHA.sql.gz"
RETENCION_DIAS=30

mkdir -p "$DESTINO"

# Las credenciales se leen de las mismas variables de entorno que usa Django
# (ver .env en el servidor) — no hardcodear usuario/clave en este script.
mysqldump \
  --host="$DB_HOST" --port="$DB_PORT" \
  --user="$DB_USER" --password="$DB_PASSWORD" \
  --single-transaction --routines --triggers \
  "$DB_NAME" | gzip > "$ARCHIVO"

# Elimina respaldos locales más viejos que RETENCION_DIAS
find "$DESTINO" -name 'pvd_*.sql.gz' -mtime +"$RETENCION_DIAS" -delete

echo "Respaldo guardado en $ARCHIVO"
```

Programarlo con `cron` en el VPS de producción (ver `deploy/setup.sh`):

```cron
# Todos los días a las 3:00 a.m.
0 3 * * * DB_HOST=... DB_PORT=... DB_USER=... DB_PASSWORD=... DB_NAME=modeladobd /var/www/pvd/backup_pvd.sh >> /var/log/pvd/backup.log 2>&1
```

Idealmente, subir el archivo resultante a un almacenamiento distinto de
Aiven (otro proveedor cloud, un bucket S3-compatible, etc.) para no depender
de un solo proveedor si hay un incidente de cuenta o facturación.

## 3. Restaurar un respaldo manual

```bash
gunzip -c pvd_20260706_030000.sql.gz | mysql \
  --host="$DB_HOST" --port="$DB_PORT" \
  --user="$DB_USER" --password="$DB_PASSWORD" \
  "$DB_NAME"
```

Probar la restauración periódicamente (por ejemplo trimestralmente) contra
una base de datos de prueba — un respaldo que nunca se restauró no es un
respaldo confirmado.

## 4. Qué NO respalda esto

- **Archivos de `media/`** (imágenes de evidencias, ver `Evidencia.imagen` en
  `modulo_puntos/models.py`): no están en la base de datos, viven en el
  filesystem del servidor. Incluir `/var/www/pvd/media/` en la rutina de
  respaldo del servidor (rsync, tar, o snapshot del volumen).
- **Variables de entorno / `.env`**: guardar una copia segura (gestor de
  secretos o similar) por separado; sin ellas, un servidor nuevo no puede
  reconectarse a la base de datos ni descifrar la sesión.
