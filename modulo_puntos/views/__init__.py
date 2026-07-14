"""Vistas del sistema, divididas por módulo. `from . import views` sigue
funcionando igual: este __init__ reexporta todas las vistas."""
from .auth import *
from .ciudadanos import *
from .reportes import *
from .atenciones import *
from .recursos import *
from .evidencias import *
from .exportaciones import *
from .usuarios import *
from .pvd import *
from .salas import *
from .permisos import *
from .cursos import *
from .mantenimientos import *
from .auditoria import *
from ._helpers import *
