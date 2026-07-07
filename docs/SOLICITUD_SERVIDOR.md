# Solicitud de Infraestructura — Puntos Vive Digital

Documento para entregar al área de Sistemas/TIC de la Alcaldía de Bugalagrande:
esto es lo que necesita el software para pasar de pruebas a producción.

## 1. Servidor (VPS)

| Requisito | Valor |
|---|---|
| Sistema operativo | Ubuntu 22.04 LTS (64 bits) |
| CPU | 1 vCPU (mínimo) |
| Memoria RAM | 2 GB (mínimo) |
| Disco | 25–50 GB SSD |
| Costo estimado | USD $10–15/mes (plan básico de cualquier proveedor) |
| Proveedores sugeridos | DigitalOcean, AWS Lightsail, Vultr, Linode — cualquiera que ya use la Alcaldía sirve igual |

**Puertos que deben quedar abiertos al público (firewall):**
- `22` — para administración remota (SSH)
- `80` — tráfico web normal (HTTP)
- `443` — tráfico web seguro (HTTPS)

**Acceso que necesita el contratista (quien instala el software):**
- La dirección IP pública del servidor.
- Usuario con permisos de administrador (`root` o `sudo`) y contraseña, o una llave
  SSH — lo que sea el estándar de seguridad que maneje la Alcaldía.

## 2. Dominio / subdominio

Se necesita un subdominio del dominio institucional apuntando a este servidor,
por ejemplo:

```
pvd.bugalagrande.gov.co
```

El área de Sistemas debe crear un registro DNS tipo **A** para ese subdominio
apuntando a la IP pública del servidor (paso 1), una vez el servidor exista.
Esto lo hace la misma persona que administra el dominio `.gov.co` de la Alcaldía.

## 3. Base de datos

**Ya existe — no hay que crear una nueva.** La base de datos vive en Aiven
Cloud (MySQL) y ya está configurada. Solo hay que confirmar con el
administrador de esa cuenta de Aiven (probablemente la misma persona que
maneja este proyecto) que el servidor nuevo puede conectarse a ella. Aiven
por defecto permite conexión desde cualquier IP con las credenciales
correctas; si en algún momento se restringe por lista blanca de IPs, hay que
agregar ahí la IP del servidor nuevo.

## 4. Correo electrónico

No aplica — este sistema no envía correos (no hay recuperación de
contraseña por email; los reinicios de clave los hace un administrador
manualmente).

## 5. Qué NO se necesita

- No se necesita un balanceador de carga ni múltiples servidores — con uno
  solo alcanza para el volumen esperado.
- No se necesita almacenamiento en la nube aparte (S3, etc.) — las imágenes
  de evidencias se guardan en el disco del mismo servidor.

## 6. Una vez el servidor exista

Con el servidor creado (IP, acceso SSH) y el dominio apuntando a él, la
instalación del software es automática: existe un script
(`deploy/setup.sh` en el repositorio) que instala todo lo necesario, deja
el sitio funcionando con HTTPS gratuito (Let's Encrypt), y programa el
respaldo diario de la base de datos. Solo hace falta que alguien con acceso
técnico (el contratista, o quien la Alcaldía designe) lo ejecute una vez.
