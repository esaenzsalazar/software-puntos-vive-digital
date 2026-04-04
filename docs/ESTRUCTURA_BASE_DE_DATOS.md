# Estructura principal de la base de datos

Esquema lógico usado por Django ORM (tablas físicas según `db_table` en modelos). Claves foráneas permiten **trazabilidad de la atención**.

## Tablas núcleo

| Tabla (modelo) | Descripción |
|----------------|-------------|
| `ciu_ciudadano` | Ciudadano/usuario PVD caracterizado. |
| `atn_atencion` | Atención: fechas, estado, ciudadano, operador, observaciones. |
| `srv_servicio` | Servicio prestado, ligado a una atención (`ATN_CDGO`). |
| `sat_satisfaccion` | Calificación y comentario, ligada a atención. |
| `opr_operador` | Perfil del operador PVD. |
| `rec_recurso` | Tipo/estado de recurso de inventario. |
| `prs_prestamorecurso` | Préstamo: fechas entrega/devolución, recurso. |
| `pvd_puntovivedigital` | Entidad de punto (relaciones con servicio/recurso/operador/atención según modelo). |
| `usu_usuariosistema` | Usuario de sistema legado (modelo `UsuarioSistema`). |
| `lva_listavalor` | Lista de valores / catálogos si aplica. |

## Relaciones destacadas

- `atn_atencion.CIU_CDGO` → `ciu_ciudadano`
- `atn_atencion.OPR_CDGO` → `opr_operador`
- `srv_servicio.ATN_CDGO` → `atn_atencion`
- `sat_satisfaccion.ATN_CDGO` → `atn_atencion`
- `prs_prestamorecurso.REC_CDGO` → `rec_recurso`

## Autenticación Django

Usuarios administrativos (`auth_user`) y grupos (`Administrador PVD`, `Administrador TIC`) se gestionan con el módulo de creación de usuarios; el perfil `Operador` puede crearse automáticamente al crear un admin PVD.

Para el detalle de columnas revise `modulo_puntos/models.py` y las migraciones en `modulo_puntos/migrations/`.
