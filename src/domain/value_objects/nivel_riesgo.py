from enum import Enum

class NivelRiesgoEnum(str, Enum):
    ALTO = "ALTO"
    MEDIO = "MEDIO"
    BAJO = "BAJO"

class GiroComercialEnum(str, Enum):
    RESTAURANTE = "Restaurante"
    BODEGA = "Bodega"
    OFICINA = "Oficina"
    PANADERIA = "Panaderia"
    TIENDA = "Tienda"

class TipoTramiteEnum(str, Enum):
    NUEVA_LICENCIA = "Nueva licencia"
    RENOVACION = "Renovacion"
    MODIFICACION = "Modificacion"
