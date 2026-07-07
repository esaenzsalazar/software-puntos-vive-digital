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

Si la retención es corta (como los 2 días confirmados el 2026-07-07 en el
plan actual — el diálogo "Change backup settings" de Aiven sólo permite
cambiar la *hora* del backup, no cuántos días se guardan; eso depende del
plan) y se necesita más historial para cumplir con la política de
conservación de datos de la Alcaldía, hay que subir de plan o complementar
con el respaldo manual de la sección 2 — lo segundo no cuesta nada extra.

## 2. Respaldo manual complementario (`mysqldump`)

Recomendado como segunda copia independiente del proveedor, con retención
más larga (30 días por defecto) y guardada fuera de Aiven, sin costo
adicional. Ya está listo en dos archivos — sólo falta ejecutarlos una vez
en el servidor de producción:

- **`deploy/backup_pvd.sh`** — el respaldo en sí (lee las credenciales del
  `.env` del servidor, nunca hay que escribir contraseñas a mano).
- **`deploy/instalar_backup_automatico.sh`** — se corre **una sola vez**,
  prueba el respaldo y lo deja programado para correr solo todas las
  noches a las 3:00 a.m.

Instalación (en el VPS, como root o con `sudo`, una sola vez):

```bash
cd /var/www/pvd
chmod +x deploy/instalar_backup_automatico.sh
sudo bash deploy/instalar_backup_automatico.sh
```

Con eso queda funcionando solo. Para confirmar que corrió: `crontab -l`
muestra la programación, y `/var/log/pvd/backup.log` muestra cada corrida.

Idealmente, subir también el archivo resultante (`/var/backups/pvd/*.sql.gz`)
a un almacenamiento distinto de Aiven (otro proveedor cloud, un bucket
S3-compatible, etc.) para no depender de un solo proveedor si hay un
incidente de cuenta o facturación — esto queda como mejora futura, no es
necesario para que el respaldo funcione.

## 3. Restaurar un respaldo manual

```bash
gunzip -c /var/backups/pvd/pvd_20260706_030000.sql.gz | mysql \
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
