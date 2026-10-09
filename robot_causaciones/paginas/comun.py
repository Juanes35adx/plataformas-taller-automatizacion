from playwright.sync_api import Page

from excepciones import ExcepcionSistema

TITULO_NO_DISPONIBLE = "Servicio temporalmente no disponible"


def titulo(pagina: Page, texto: str):
    return pagina.get_by_role("heading", name=texto, exact=True)


def alerta(pagina: Page):
    return pagina.get_by_role("alert")


def verificar_disponible(pagina: Page) -> None:
    """Convierte la pantalla SICOF-503 en una falla de sistema."""
    if titulo(pagina, TITULO_NO_DISPONIBLE).is_visible():
        raise ExcepcionSistema(f"{TITULO_NO_DISPONIBLE} (SICOF-503)")
