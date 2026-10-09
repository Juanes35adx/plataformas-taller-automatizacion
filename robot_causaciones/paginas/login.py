from playwright.sync_api import Page

from paginas.comun import alerta, verificar_disponible


class PaginaLogin:
    def __init__(self, pagina: Page, url_portal: str) -> None:
        self.pagina = pagina
        self.url = f"{url_portal}/login"

    def esta_en_login(self) -> bool:
        return self.pagina.url.split("?")[0].endswith("/login")

    def ingresar(self, usuario: str, clave: str) -> None:
        if not self.esta_en_login():
            self.pagina.goto(self.url)
        verificar_disponible(self.pagina)
        self.pagina.get_by_label("Usuario").fill(usuario)
        self.pagina.get_by_label("Contraseña").fill(clave)
        self.pagina.get_by_role("button", name="Ingresar").click()
        self.pagina.wait_for_load_state()
        if self.esta_en_login():
            mensaje = alerta(self.pagina).inner_text() if alerta(self.pagina).count() else "sin mensaje"
            raise SystemExit(f"SICOF rechazó las credenciales del operador: {mensaje}")
