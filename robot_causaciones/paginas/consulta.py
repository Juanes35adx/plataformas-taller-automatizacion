from urllib.parse import quote

from playwright.sync_api import Page

from paginas.comun import verificar_disponible


class PaginaConsulta:
    def __init__(self, pagina: Page, url_portal: str) -> None:
        self.pagina = pagina
        self.url_portal = url_portal

    def buscar_causacion(self, nit: str, factura: str) -> str | None:
        """Devuelve el número de causación existente para la pareja NIT + factura, o None."""
        self.pagina.goto(f"{self.url_portal}/causaciones?factura={quote(factura)}")
        verificar_disponible(self.pagina)

        tabla = self.pagina.get_by_role("table")
        encabezados = [t.strip() for t in tabla.get_by_role("columnheader").all_inner_texts()]
        i_causacion = encabezados.index("Causación")
        i_nit = encabezados.index("NIT")
        i_factura = encabezados.index("Factura")

        for fila in tabla.get_by_role("row").all():
            celdas = [c.strip() for c in fila.get_by_role("cell").all_inner_texts()]
            if len(celdas) != len(encabezados):
                continue
            if celdas[i_nit] == nit and celdas[i_factura].upper() == factura.upper():
                return celdas[i_causacion]
        return None
