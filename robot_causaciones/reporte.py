from pathlib import Path

from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

from modelo import Resultado

COLUMNAS = ("IdLista", "Factura", "NIT", "Estado", "Causacion", "Detalle")


def escribir_resultados(ruta: Path, resultados: list[Resultado]) -> None:
    """Escribe el libro con la tabla de Excel Resultados que lee el flujo de cierre."""
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Resultados"
    hoja.append(COLUMNAS)
    for r in resultados:
        hoja.append([r.id_lista, r.factura, r.nit, r.estado, r.causacion or None, r.detalle or None])

    # una tabla de Excel necesita al menos una fila de datos
    ultima_fila = max(len(resultados), 1) + 1
    tabla = Table(displayName="Resultados", ref=f"A1:F{ultima_fila}")
    tabla.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    hoja.add_table(tabla)

    for columna, ancho in zip("ABCDEF", (10, 14, 14, 16, 20, 60)):
        hoja.column_dimensions[columna].width = ancho

    ruta.parent.mkdir(parents=True, exist_ok=True)
    libro.save(ruta)
