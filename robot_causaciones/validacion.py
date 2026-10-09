import re
from datetime import date, datetime

from openpyxl.utils.datetime import from_excel

from excepciones import ExcepcionNegocio
from modelo import Factura, FilaEntrada

# 900123456, 900.123.456, 900,123,456
MILES = re.compile(r"^\d{1,3}([.,]\d{3})+$")
DECIMAL_CERO = re.compile(r"^(\d+)[.,]0+$")
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def entero_limpio(valor: object) -> int | None:
    """Convierte números y textos con separadores de miles a entero; None si no es entero."""
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float):
        return int(valor) if valor.is_integer() else None
    texto = str(valor).strip().replace(" ", "")
    if texto.isdigit():
        return int(texto)
    if MILES.match(texto):
        return int(re.sub(r"[.,]", "", texto))
    if m := DECIMAL_CERO.match(texto):
        return int(m.group(1))
    return None


def texto_limpio(valor: object) -> str:
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    return str(valor).strip()


def limpiar_nit(valor: object) -> str | None:
    nit = entero_limpio(valor)
    return str(nit) if nit is not None and nit > 0 else None


def leer_fecha(valor: object) -> date | None:
    """Acepta fecha de Excel, serial de Excel o texto yyyy-MM-dd."""
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        try:
            return from_excel(valor).date()
        except (ValueError, OverflowError, TypeError):
            return None
    texto = texto_limpio(valor)
    if not ISO.match(texto):
        return None
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        return None


def validar(fila: FilaEntrada, hoy: date) -> Factura:
    """Valida la fila antes de tocar SICOF; lanza ExcepcionNegocio si se rechaza."""
    id_lista = entero_limpio(fila.id_lista)
    if id_lista is None:
        raise ExcepcionNegocio(f"IdLista {fila.id_lista!r} no es un número entero")

    factura = texto_limpio(fila.factura)
    if not factura:
        raise ExcepcionNegocio("El número de factura es obligatorio")

    nit = limpiar_nit(fila.nit)
    if nit is None:
        raise ExcepcionNegocio(f"El NIT {texto_limpio(fila.nit) or '(vacío)'} no es un número válido")

    valor = entero_limpio(fila.valor)
    if valor is None or valor <= 0:
        raise ExcepcionNegocio("El valor debe ser un número entero mayor que cero")

    fecha = leer_fecha(fila.fecha_factura)
    if fecha is None:
        raise ExcepcionNegocio("La fecha de factura debe ser una fecha válida con formato yyyy-MM-dd")
    if fecha > hoy:
        raise ExcepcionNegocio("La fecha de factura no puede ser posterior a la fecha actual")

    centro = texto_limpio(fila.centro_costo).upper()
    if not centro:
        raise ExcepcionNegocio("Seleccione un centro de costo válido")

    return Factura(
        id_lista=id_lista,
        factura=factura,
        nit=nit,
        proveedor=texto_limpio(fila.proveedor),
        valor=valor,
        centro_costo=centro,
        fecha_factura=fecha,
    )
