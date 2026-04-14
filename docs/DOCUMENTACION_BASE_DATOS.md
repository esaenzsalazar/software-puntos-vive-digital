# Documentación de Base de Datos - Puntos Vive Digital
## Contrato CD-224-2026 - Alcaldía de Bugalagrande

---

## 📋 TABLA DE CONTENIDOS
1. [Diagrama de Relaciones](#diagrama-de-relaciones)
2. [Modelos y Tablas](#modelos-y-tablas)
3. [Relaciones y Llaves Foráneas](#relaciones-y-llaves-foráneas)
4. [Sistema de Permisos y Roles](#sistema-de-permisos-y-roles)
5. [Flujos de Datos](#flujos-de-datos)

---

## DIAGRAMA DE RELACIONES

```
┌─────────────────────┐
│   auth_user (Django)│
│  (Usuarios Sistema) │
└─────────┬───────────┘
          │
          ├──1:1──► usr_userprofile ──N:1──► pvd_puntovivedigital
          │                                      │
          │                                       ├──1:N──► opr_operador
          │                                       ├──1:N──► ciu_ciudadano
          │                                       ├──1:N──► rec_recurso
          │                                       ├──1:N──► atn_atencion
          │                                       └──1:N──► sala_sala
          │
          └──N:M──► auth_group (Roles via Django Groups)
                   - Superusuario
                   - Administrador TIC
                   - Administrador PVD

pvd_puntovivedigital
    └──1:N──► atn_atencion ──1:1──► ciu_ciudadano
              │                    └──1:1──► opr_operador
              ├──1:N──► srv_servicio
              └──1:1──► sat_satisfaccion

atn_atencion ──1:1──► prs_prestamorecurso ──1:1──► rec_recurso
```

---

## MODELOS Y TABLAS

### 1. **pvd_puntovivedigital** (Puntos Vive Digital)
**Descripción:** Tabla principal que gestiona los diferentes PVDs (edificios/ubicaciones).

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `PVD_CDGO` | INT (PK, Auto) | NOT NULL | Código único del PVD |
| `PVD_NOMBRE` | VARCHAR(128) | NULL | Nombre del PVD |
| `PVD_DIRCION` | VARCHAR(128) | NULL | Dirección física |
| `PVD_BARRIO` | VARCHAR(64) | NULL | Barrio o vereda |
| `PVD_TELEFONO` | VARCHAR(32) | NULL | Teléfono de contacto |
| `PVD_CORREO` | VARCHAR(128) | NULL | Correo electrónico |
| `PVD_ESTDO` | CHAR(1) | DEFAULT 'A' | Estado: A=Activo, I=Inactivo, M=Mantenimiento |
| `PVD_FCH_CREA` | DATE | Auto | Fecha de creación |
| `PVD_DESCRIPCION` | TEXT | NULL | Descripción/notas adicionales |

**Índices:**
- PRIMARY KEY: `PVD_CDGO`
- ORDERING: `pvd_nombre`

---

### 2. **auth_user** (Usuarios Django - Built-in)
**Descripción:** Tabla de usuarios del sistema Django (built-in).

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INT (PK, Auto) | NOT NULL | ID único del usuario |
| `username` | VARCHAR(150) | UNIQUE, NOT NULL | Nombre de usuario |
| `password` | VARCHAR(128) | NOT NULL | Contraseña (hasheada) |
| `first_name` | VARCHAR(150) | NULL | Primer nombre |
| `last_name` | VARCHAR(150) | NULL | Apellidos |
| `email` | VARCHAR(254) | NULL | Correo electrónico |
| `is_superuser` | BOOLEAN | DEFAULT FALSE | ¿Es superusuario? |
| `is_active` | BOOLEAN | DEFAULT TRUE | ¿Está activo? |
| `date_joined` | DATETIME | Auto | Fecha de registro |

**NOTA:** Los nombres completos se almacenan en `first_name` y `last_name`.
- `first_name` = "Primer Nombre Segundo Nombre"
- `last_name` = "Primer Apellido Segundo Apellido"

---

### 3. **usr_userprofile** (Perfil de Usuario)
**Descripción:** Relación entre usuario Django y su PVD asignado.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INT (PK, Auto) | NOT NULL | ID único |
| `user_id` | INT (FK → auth_user) | UNIQUE, NOT NULL | Usuario asociado (OneToOne) |
| `pvd_asignado_id` | INT (FK → pvd_puntovivedigital) | NULL | PVD asignado al usuario |

**Relaciones:**
- `user_id` → `auth_user.id` (OneToOne - CASCADE on delete)
- `pvd_asignado_id` → `pvd_puntovivedigital.PVD_CDGO` (SET NULL on delete)

---

### 4. **auth_group** (Grupos/Roles Django)
**Descripción:** Grupos de Django para gestionar roles.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INT (PK, Auto) | NOT NULL | ID del grupo |
| `name` | VARCHAR(150) | UNIQUE, NOT NULL | Nombre del rol |

**Roles Predefinidos:**
1. **Superusuario** - Acceso total (no usa grupo, usa `is_superuser=True`)
2. **Administrador TIC** - Gestión de PVDs y usuarios
3. **Administrador PVD** - Operación de un PVD específico

**Tabla Intermedia:** `auth_user_groups` (ManyToMany)
- `user_id` → `auth_user.id`
- `group_id` → `auth_group.id`

---

### 5. **opr_operador** (Operadores)
**Descripción:** Funcionarios/operadores que trabajan en un PVD.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `OPR_CDGO` | INT (PK, Auto) | NOT NULL | Código único del operador |
| `PVD_CDGO` | INT (FK → pvd_puntovivedigital) | NULL | PVD donde trabaja |
| `USU_CDGO` | INT (FK → usu_usuariosistema) | NULL | Usuario del sistema heredado |
| `OPR_TPODOC` | VARCHAR(32) | NULL | Tipo de documento |
| `OPR_NUMDOC` | VARCHAR(32) | NULL | Número de documento |
| `OPR_NMBRES` | VARCHAR(128) | NULL | Nombres |
| `OPR_APLLDOS` | VARCHAR(128) | NULL | Apellidos |
| `OPR_EMAIL` | VARCHAR(128) | NULL | Correo electrónico |
| `OPR_TLFNO` | VARCHAR(32) | NULL | Teléfono |
| `OPR_ESTDO` | CHAR(1) | NULL | Estado: A=Activo, I=Inactivo |

**Relaciones:**
- `PVD_CDGO` → `pvd_puntovivedigital.PVD_CDGO` (SET NULL on delete)
- `USU_CDGO` → `usu_usuariosistema.USU_CDGO` (DO NOTHING)

**NOTA:** Los operadores se crean automáticamente al crear Admin PVD.

---

### 6. **ciu_ciudadano** (Ciudadanos)
**Descripción:** Ciudadanos atendidos en los PVDs.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `CIU_CDGO` | INT (PK, Auto) | NOT NULL | Código único del ciudadano |
| `PVD_CDGO` | INT (FK → pvd_puntovivedigital) | NULL | PVD donde se registró |
| `CIU_TPODOC` | VARCHAR(32) | NULL | Tipo de documento |
| `CIU_NUMDOC` | VARCHAR(32) | NULL | Número de documento |
| `CIU_NMBRES` | VARCHAR(128) | NULL | Nombres completos |
| `CIU_APLLDOS` | VARCHAR(128) | NULL | Apellidos completos |
| `CIU_FCHANCM` | DATE | NULL | Fecha de nacimiento |
| `CIU_GENRO` | VARCHAR(32) | NULL | Género: M=Masculino, F=Femenino, O=Otro |
| `CIU_ETNIA` | VARCHAR(64) | NULL | Pertenencia étnica |
| `CIU_NVLEDUC` | VARCHAR(64) | NULL | Nivel educativo |
| `CIU_OCPCION` | VARCHAR(64) | NULL | Ocupación |
| `CIU_DISCAPACIDAD` | BOOLEAN | DEFAULT FALSE | ¿Tiene discapacidad? |
| `CIU_DESC_DISCAPACIDAD` | VARCHAR(128) | NULL | Descripción discapacidad |
| `CIU_DIRCION` | VARCHAR(128) | NULL | Dirección de residencia |
| `CIU_BARRIO` | VARCHAR(64) | NULL | Barrio |
| `CIU_ZRURAL` | VARCHAR(64) | NULL | Zona rural |
| `CIU_ESTRATO` | INT | DEFAULT 1 | Estrato socioeconómico (1-3) |
| `CIU_ESTDO` | CHAR(1) | DEFAULT 'A' | Estado: A=Activo, I=Inactivo |
| `CIU_EMAIL` | VARCHAR(128) | DEFAULT '' | Correo electrónico |
| `CIU_TLFNO` | VARCHAR(32) | NULL | Teléfono |
| `CIU_PENDIENTE_APROBACION` | BOOLEAN | DEFAULT FALSE | ¿Pendiente de aprobación? |
| `CIU_FECHA_REGISTRO` | DATETIME | Auto | Fecha de registro |

**Relaciones:**
- `PVD_CDGO` → `pvd_puntovivedigital.PVD_CDGO` (SET NULL on delete)

---

### 7. **atn_atencion** (Atenciones)
**Descripción:** Atenciones realizadas a ciudadanos.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `ATN_CDGO` | INT (PK, Auto) | NOT NULL | Código único de atención |
| `PVD_CDGO` | INT (FK → pvd_puntovivedigital) | NULL | PVD donde se realizó |
| `CIU_CDGO` | INT (FK → ciu_ciudadano) | NULL | Ciudadano atendido |
| `OPR_CDGO` | INT (FK → opr_operador) | NULL | Operador que atendió |
| `PRS_CDGO` | INT (FK → prs_prestamorecurso) | NULL | Préstamo vinculado |
| `ATN_FECHA` | DATE | NOT NULL | Fecha de atención |
| `ATN_HRINI` | TIME | NOT NULL | Hora de inicio |
| `ATN_HRFIN` | TIME | NULL | Hora de finalización |
| `ATN_ESTDO` | CHAR(1) | DEFAULT 'P' | Estado: P=Pendiente, F=Finalizada, C=Cancelada |
| `ATN_OBS` | VARCHAR(512) | NULL | Observaciones |

**Relaciones:**
- `PVD_CDGO` → `pvd_puntovivedigital.PVD_CDGO` (SET NULL on delete)
- `CIU_CDGO` → `ciu_ciudadano.CIU_CDGO` (DO NOTHING)
- `OPR_CDGO` → `opr_operador.OPR_CDGO` (DO NOTHING)
- `PRS_CDGO` → `prs_prestamorecurso.PRS_CDGO` (DO NOTHING)

---

### 8. **srv_servicio** (Servicios)
**Descripción:** Servicios prestados durante una atención.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `SRV_CDGO` | INT (PK, Auto) | NOT NULL | Código único del servicio |
| `ATN_CDGO` | INT (FK → atn_atencion) | NULL | Atención vinculada |
| `SRV_NOMBRE` | VARCHAR(128) | NOT NULL | Nombre del servicio |
| `SRV_DESCR` | VARCHAR(512) | NULL | Descripción detallada |
| `SRV_TIPO` | VARCHAR(64) | NOT NULL | Tipo/categoría de servicio |
| `SRV_REQEQP` | CHAR(1) | DEFAULT 'N' | ¿Requiere equipo? S=Sí, N=No |
| `SRV_ESTDO` | CHAR(1) | DEFAULT 'A' | Estado: A=Activo, I=Inactivo |

**Relaciones:**
- `ATN_CDGO` → `atn_atencion.ATN_CDGO` (DO NOTHING)

---

### 9. **rec_recurso** (Recursos/Equipos)
**Descripción:** Equipos disponibles en cada PVD.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `REC_CDGO` | INT (PK) | NOT NULL | Código único del recurso |
| `PVD_CDGO` | INT (FK → pvd_puntovivedigital) | NULL | PVD donde se ubica |
| `REC_TIPO` | VARCHAR(64) | NOT NULL | Tipo de recurso |
| `REC_ESTDO` | CHAR(1) | NOT NULL | Estado: A=Activo, I=Inactivo |

**Relaciones:**
- `PVD_CDGO` → `pvd_puntovivedigital.PVD_CDGO` (SET NULL on delete)

---

### 10. **prs_prestamorecurso** (Préstamos de Recursos)
**Descripción:** Préstamos de recursos a ciudadanos.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `PRS_CDGO` | INT (PK, Auto) | NOT NULL | Código único del préstamo |
| `REC_CDGO` | INT (FK → rec_recurso) | NULL | Recurso prestado |
| `PRS_FCHENT` | DATETIME | NOT NULL | Fecha de entrega |
| `PRS_FCHDEV` | DATETIME | NULL | Fecha de devolución |
| `PRS_OBS` | VARCHAR(512) | NULL | Observaciones |

**Relaciones:**
- `REC_CDGO` → `rec_recurso.REC_CDGO` (DO NOTHING)

---

### 11. **sat_satisfaccion** (Encuestas de Satisfacción)
**Descripción:** Encuestas de satisfacción de ciudadanos.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `SAT_CDGO` | INT (PK, Auto) | NOT NULL | Código único de encuesta |
| `ATN_CDGO` | INT (FK → atn_atencion) | NULL | Atención evaluada |
| `SAT_CALIF` | INT | NOT NULL | Calificación (1-5) |
| `SAT_CMNTRIO` | VARCHAR(512) | NULL | Comentario |
| `SAT_FECHA` | DATETIME | NOT NULL | Fecha de encuesta |

**Relaciones:**
- `ATN_CDGO` → `atn_atencion.ATN_CDGO` (DO NOTHING)

---

### 12. **sala_sala** (Salas)
**Descripción:** Salas/espacios físicos dentro de cada PVD.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `SALA_CDGO` | INT (PK, Auto) | NOT NULL | Código único de sala |
| `PVD_CDGO` | INT (FK → pvd_puntovivedigital) | NOT NULL | PVD donde se ubica |
| `SALA_NOMBRE` | VARCHAR(128) | NOT NULL | Nombre de la sala |
| `SALA_DESCR` | TEXT | NULL | Descripción |
| `SALA_CAPACIDAD` | INT | NULL | Capacidad |
| `SALA_ESTDO` | CHAR(1) | DEFAULT 'A' | Estado: A=Activo, I=Inactivo, M=Mantenimiento |
| `SALA_FCH_CREA` | DATE | Auto | Fecha de creación |

**Relaciones:**
- `PVD_CDGO` → `pvd_puntovivedigital.PVD_CDGO` (CASCADE on delete)
- UNIQUE TOGETHER: `[['pvd_cdgo', 'sala_nombre']]`

---

### 13. **aud_auditoria_accion** (Auditoría)
**Descripción:** Registro de acciones del sistema.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `AUD_CDGO` | INT (PK, Auto) | NOT NULL | Código único de auditoría |
| `AUD_USUARIO` | VARCHAR(128) | NULL | Usuario que realizó la acción |
| `AUD_ACCION` | VARCHAR(32) | NOT NULL | Tipo de acción |
| `AUD_MODELO` | VARCHAR(128) | NULL | Modelo afectado |
| `AUD_OBJETO_ID` | VARCHAR(128) | NULL | ID del objeto afectado |
| `AUD_DESCRIPCION` | TEXT | NULL | Descripción detallada |
| `AUD_IP` | VARCHAR(45) | NULL | Dirección IP |
| `AUD_FECHA` | DATETIME | Auto | Fecha y hora de la acción |

**Tipos de Acción:**
- `CREATE` - Creación
- `UPDATE` - Actualización
- `DELETE` - Eliminación
- `LOGIN` - Inicio de sesión
- `LOGOUT` - Cierre de sesión
- `EXPORT` - Exportación de datos
- `OTHER` - Otra acción

---

## RELACIONES Y LLAVES FORÁNEAS

### Resumen de Relaciones

| Tabla Origen | Tabla Destino | Tipo | On Delete | Descripción |
|--------------|---------------|------|-----------|-------------|
| usr_userprofile | auth_user | OneToOne | CASCADE | Un usuario tiene un perfil |
| usr_userprofile | pvd_puntovivedigital | ManyToOne | SET NULL | Perfil tiene PVD asignado |
| opr_operador | pvd_puntovivedigital | ManyToOne | SET NULL | Operador trabaja en PVD |
| opr_operador | usu_usuariosistema | ManyToOne | DO NOTHING | Operador vinculado a usuario legado |
| ciu_ciudadano | pvd_puntovivedigital | ManyToOne | SET NULL | Ciudadano registrado en PVD |
| atn_atencion | pvd_puntovivedigital | ManyToOne | SET NULL | Atención realizada en PVD |
| atn_atencion | ciu_ciudadano | ManyToOne | DO NOTHING | Atención a ciudadano |
| atn_atencion | opr_operador | ManyToOne | DO NOTHING | Atención por operador |
| atn_atencion | prs_prestamorecurso | ManyToOne | DO NOTHING | Atención con préstamo vinculado |
| srv_servicio | atn_atencion | ManyToOne | DO NOTHING | Servicio de una atención |
| rec_recurso | pvd_puntovivedigital | ManyToOne | SET NULL | Recurso ubicado en PVD |
| prs_prestamorecurso | rec_recurso | ManyToOne | DO NOTHING | Préstamo de recurso |
| sat_satisfaccion | atn_atencion | ManyToOne | DO NOTHING | Encuesta de atención |
| sala_sala | pvd_puntovivedigital | ManyToOne | CASCADE | Sala ubicada en PVD |
| auth_user | auth_group | ManyToMany | - | Usuario pertenece a grupos |

---

## SISTEMA DE PERMISOS Y ROLES

### Estructura de Roles

```
┌─────────────────────────────────────────────────────────────┐
│                    Superusuario                              │
│              (is_superuser = True)                           │
│   Acceso total al sistema sin restricciones                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               Administrador TIC                              │
│            (Group: 'Administrador TIC')                      │
│   - Crear y gestionar PVDs                                   │
│   - Crear Admin PVD                                          │
│   - Ver reportes de todos los PVDs                           │
│   - Gestionar salas                                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               Administrador PVD                              │
│            (Group: 'Administrador PVD')                      │
│   - Operar un PVD específico                                 │
│   - Registrar ciudadanos                                     │
│   - Registrar atenciones y servicios                         │
│   - Gestionar recursos y préstamos                           │
│   - Aprobar ciudadanos pendientes                            │
└─────────────────────────────────────────────────────────────┘
```

### Permisos por Vista

| Vista | Superuser | Admin TIC | Admin PVD | Público |
|-------|-----------|-----------|-----------|---------|
| Login/Logout | ✅ | ✅ | ✅ | ✅ |
| Panel Control | ✅ | ✅ | ✅ | ❌ |
| Gestionar Roles | ✅ | ❌ | ❌ | ❌ |
| Crear Admin TIC | ✅ | ❌ | ❌ | ❌ |
| Crear Admin PVD | ✅ | ✅ | ❌ | ❌ |
| Crear/Editar PVD | ✅ | ✅ | ❌ | ❌ |
| Crear/Editar Salas | ✅ | ✅ | ❌ | ❌ |
| Registrar Ciudadano | ✅ | ✅ | ✅ | ❌ |
| Registro Ciudadano Público | ✅ | ✅ | ✅ | ✅ |
| Aprobar Ciudadanos | ❌* | ❌* | ✅ | ❌ |
| Registrar Atención | ✅ | ✅ | ✅ | ❌ |
| Registrar Servicio | ✅ | ✅ | ✅ | ❌ |
| Gestionar Recursos | ✅ | ✅ | ✅ | ❌ |
| Ver Reportes | ✅ | ✅ | ✅ | ❌ |
| Exportar Datos | ✅ | ✅ | ✅ | ❌ |

*Superuser y Admin TIC no pueden aprobar ciudadanos pendientes (solo Admin PVD)

### Flujo de Asignación de Roles

1. **Superusuario** crea un usuario
2. **Superusuario** o **Admin TIC** asigna el rol (grupo)
3. Para **Admin PVD**, se puede asignar un PVD específico en `usr_userprofile`
4. El sistema valida permisos en cada vista

---

## FLUJOS DE DATOS

### Flujo 1: Registro de Ciudadano
```
Ciudadano → Formulario → Validación → BD (ciu_ciudadano)
                                        ↓
                            ciu_pendiente_aprobacion = TRUE
                                        ↓
                        Admin PVD revisa y aprueba/rechaza
                                        ↓
                            ciu_pendiente_aprobacion = FALSE
                            pvd_cdgo asignado
```

### Flujo 2: Atención a Ciudadano
```
Admin PVD → Selecciona Ciudadano → Crea Atención
    ↓
atn_atencion (registrada)
    ↓
    ├──► srv_servicio (servicios prestados)
    └──► prs_prestamorecurso (si hay préstamo)
              ↓
         rec_recurso (equipo prestado)
```

### Flujo 3: Creación de PVD
```
Superuser → Formulario PVD → Validación → BD (pvd_puntovivedigital)
                                                      ↓
                                    (Opcional) Asignar Admin PVD
                                                      ↓
                                          usr_userprofile.pvd_asignado
```

### Flujo 4: Auditoría
```
Cualquier Acción → registrar_auditoria()
                        ↓
                aud_auditoria_accion
                        ↓
                - Usuario
                - Acción
                - Modelo
                - Objeto ID
                - IP
                - Timestamp
```

---

## NOTAS IMPORTANTES

### 1. **Heredado vs Nuevo**
- `usu_usuariosistema` es un modelo heredado de la base de datos original
- Para nuevos desarrollos, usar `auth.User` de Django
- `opr_operador.USU_CDGO` mantiene compatibilidad con sistema legacy

### 2. **Estados**
- **A** = Activo
- **I** = Inactivo  
- **M** = En mantenimiento (solo PVDs y Salas)
- **P** = Pendiente (atenciones)
- **F** = Finalizada (atenciones)
- **C** = Cancelada (atenciones)

### 3. **Campos Obligatorios por Modelo**
Solo los campos marcados como `NOT NULL` sin valor por defecto son obligatorios. La mayoría de los campos tienen `NULL` permitido para flexibilidad.

### 4. **Integridad Referencial**
- `SET NULL`: Si se elimina el padre, el hijo queda con NULL
- `CASCADE`: Si se elimina el padre, se eliminan los hijos
- `DO NOTHING`: No se permite eliminar si hay hijos

### 5. **Seguridad**
- Contraseñas hasheadas con Django's PBKDF2
- Auditoría de todas las acciones críticas
- Validación de permisos en cada vista
- Protección CSRF en todos los formularios

---

## ÍNDICES Y OPTIMIZACIÓN

### Índices Automáticos
- Todos los Primary Keys tienen índice automático
- Foreign Keys tienen índice automático en Django

### Índices Recomendados (para agregar si necesario)
```sql
-- Búsqueda de ciudadanos por documento
CREATE INDEX idx_ciudadano_numdoc ON ciu_ciudadano(CIU_NUMDOC);

-- Búsqueda de atenciones por fecha
CREATE INDEX idx_atencion_fecha ON atn_atencion(ATN_FECHA);

-- Búsqueda por PVD activo
CREATE INDEX idx_ciudadano_pvd ON ciu_ciudadano(PVD_CDGO);
CREATE INDEX idx_atencion_pvd ON atn_atencion(PVD_CDGO);
```

---

## BACKUP Y MIGRACIÓN

### Realizar Backup
```bash
python manage.py dumpdata > backup.json
```

### Restaurar Backup
```bash
python manage.py loaddata backup.json
```

### Crear Migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

---

**Documento generado:** 14 de abril de 2026  
**Versión:** 1.0  
**Contrato:** CD-224-2026  
**Alcaldía de Bugalagrande - Valle del Cauca**
