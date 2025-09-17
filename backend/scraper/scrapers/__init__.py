from .walmart import buscar_walmart
from .sucre import buscar_sucre
from .la_bomba import buscar_la_bomba
from .farmacia_fischel import buscar_fischel

TIENDAS = [
    buscar_fischel,
    buscar_la_bomba,
    buscar_sucre,
    buscar_walmart
]