from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class FilaEntrada:
    """Fila de PorRadicar tal como llega del libro, sin limpiar."""

    id_lista: object
    factura: object
    nit: object
    proveedor: object
    valor: object
    centro_costo: object
    fecha_factura: object


@dataclass(frozen=True)
class Factura:
    """Factura ya limpia y validada, lista para SICOF."""

    id_lista: int
    factura: str
    nit: str
    proveedor: str
    valor: int
    centro_costo: str
    fecha_factura: date


@dataclass(frozen=True)
class Resultado:
    id_lista: int | str
    factura: str
    nit: int | str
    estado: str
    causacion: str = ""
    detalle: str = ""


CAUSADA = "CAUSADA"
YA_CAUSADA = "YA_CAUSADA"
RECHAZADA = "RECHAZADA"
FALLA_SISTEMA = "FALLA_SISTEMA"
