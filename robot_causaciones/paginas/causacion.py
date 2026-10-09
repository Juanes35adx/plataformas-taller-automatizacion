import re

from playwright.sync_api import Page

from excepciones import ExcepcionNegocio, ExcepcionSistema
from modelo import Factura
from paginas.comun import TITULO_NO_DISPONIBLE, alerta, titulo, verificar_disponible

NUMERO_CAUSACION = re.compile(r"CXP-\d{4}-\d{6}")


class PaginaCausacion:
    def __init__(self, pagina: Page, url_portal: str) -> None:
        self.pagina = pagina
        self.url = f"{url_portal}/causaciones/nueva"

    def abrir(self) -> None:
        self.pagina.goto(self.url)
        verificar_disponible(self.pagina)

    def llenar(self, factura: Factura) -> None:
        centro = self.pagina.get_by_label("Centro de costo")
        opciones = centro.locator("option").evaluate_all("ops => ops.map(o => o.value)")
        if factura.centro_costo not in opciones:
            raise ExcepcionNegocio(f"El centro de costo {factura.centro_costo} no existe en SICOF")

        # fill espera a que SICOF habilite los campos tras cargar el maestro de proveedores
        self.pagina.get_by_label("NIT del proveedor").fill(factura.nit)
        self.pagina.get_by_label("Número de factura").fill(factura.factura)
        self.pagina.get_by_label("Fecha de factura").fill(factura.fecha_factura.strftime("%d/%m/%Y"))
        self.pagina.get_by_label("Valor total").fill(str(factura.valor))
        centro.select_option(value=factura.centro_costo)

    def continuar(self) -> None:
        self.pagina.get_by_role("button", name="Continuar").click()
        confirmar = titulo(self.pagina, "Confirmar causación")
        no_disponible = titulo(self.pagina, TITULO_NO_DISPONIBLE)
        confirmar.or_(alerta(self.pagina)).or_(no_disponible).first.wait_for()
        verificar_disponible(self.pagina)
        if alerta(self.pagina).count():
            raise ExcepcionNegocio(alerta(self.pagina).inner_text().strip())

    def confirmar(self) -> str:
        self.pagina.get_by_role("button", name="Confirmar causación").click()
        registrada = titulo(self.pagina, "Causación registrada")
        no_disponible = titulo(self.pagina, TITULO_NO_DISPONIBLE)
        registrada.or_(alerta(self.pagina)).or_(no_disponible).first.wait_for()
        verificar_disponible(self.pagina)
        if alerta(self.pagina).count():
            raise ExcepcionNegocio(alerta(self.pagina).inner_text().strip())

        encontrado = NUMERO_CAUSACION.search(self.pagina.locator("body").inner_text())
        if not encontrado:
            raise ExcepcionSistema("La pantalla de causación registrada no muestra el número de causación")
        return encontrado.group()
