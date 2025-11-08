"""
Este paquete de 'views' organiza la lógica en archivos separados.
El __init__.py los une para que Django los pueda encontrar.
"""

# Importar todo desde los archivos de vistas
from .core import *
from .reportes import *
from .gestion import *