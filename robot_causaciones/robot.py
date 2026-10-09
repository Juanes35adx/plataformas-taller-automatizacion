import logging
import re
from datetime import date, datetime

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page
from tenacity import RetryCallState, Retrying, retry_if_exception_type, stop_after_attempt, wait_fixed

import config
from excepciones import ExcepcionNegocio, ExcepcionSistema
from modelo import CAUSADA, FALLA_SISTEMA, RECHAZADA, YA_CAUSADA, Factura, FilaEntrada, Resultado
from paginas.causacion import PaginaCausacion
from paginas.consulta import PaginaConsulta
from paginas.login import PaginaLogin
from validacion import entero_limpio, limpiar_nit, texto_limpio, validar

log = logging.getLogger("bot")

# 503, tiempos de espera agotados (TimeoutError hereda de Error) y errores de conexión
FALLAS_SISTEMA = (ExcepcionSistema, PlaywrightError)


def primera_linea(error: BaseException) -> str:
    texto = str(error).strip() or type(error).__name__
    return texto.splitlines()[0]


class RobotCausaciones:
    def __init__(self, pagina: Page) -> None:
        self.pagina = pagina
        self.login = PaginaLogin(pagina, config.PORTAL_URL)
        self.consulta = PaginaConsulta(pagina, config.PORTAL_URL)
        self.causacion = PaginaCausacion(pagina, config.PORTAL_URL)
        self.hoy = date.today()
        self._confirmo = False

    def procesar(self, fila: FilaEntrada) -> Resultado:
        try:
            factura = validar(fila, self.hoy)
        except ExcepcionNegocio as e:
            return self._registrar(self._resultado_crudo(fila, RECHAZADA, str(e)))

        try:
            estado, numero = self._causar_con_reintentos(factura)
            resultado = Resultado(factura.id_lista, factura.factura, int(factura.nit), estado, causacion=numero)
        except ExcepcionNegocio as e:
            resultado = Resultado(factura.id_lista, factura.factura, int(factura.nit), RECHAZADA, detalle=str(e))
        except FALLAS_SISTEMA as e:
            captura = self._capturar(factura)
            detalle = f"Falla de sistema tras {config.MAX_INTENTOS} intentos: {primera_linea(e)}"
            if captura:
                detalle += f" (captura {captura})"
            resultado = Resultado(factura.id_lista, factura.factura, int(factura.nit), FALLA_SISTEMA, detalle=detalle)
        return self._registrar(resultado)

    def _causar_con_reintentos(self, factura: Factura) -> tuple[str, str]:
        self._confirmo = False
        reintentos = Retrying(
            stop=stop_after_attempt(config.MAX_INTENTOS),
            wait=wait_fixed(config.ESPERA_REINTENTO_S),
            retry=retry_if_exception_type(FALLAS_SISTEMA),
            before_sleep=lambda estado: self._log_reintento(factura, estado),
            reraise=True,
        )
        return reintentos(self._causar, factura)

    def _causar(self, factura: Factura) -> tuple[str, str]:
        self._asegurar_sesion()

        existente = self.consulta.buscar_causacion(factura.nit, factura.factura)
        if existente:
            # si un intento anterior de esta ejecución alcanzó a confirmar, la causación es nuestra
            return (CAUSADA if self._confirmo else YA_CAUSADA), existente

        self.causacion.abrir()
        self.causacion.llenar(factura)
        self.causacion.continuar()
        self._confirmo = True
        return CAUSADA, self.causacion.confirmar()

    def _asegurar_sesion(self) -> None:
        self.pagina.goto(f"{config.PORTAL_URL}/")
        if self.login.esta_en_login():
            self.login.ingresar(config.PORTAL_USUARIO, config.PORTAL_CLAVE)

    def _log_reintento(self, factura: Factura, estado: RetryCallState) -> None:
        log.warning(
            "IdLista=%s | Factura=%s | NIT=%s | REINTENTO %s de %s | %s",
            factura.id_lista,
            factura.factura,
            factura.nit,
            estado.attempt_number,
            config.MAX_INTENTOS - 1,
            primera_linea(estado.outcome.exception()),
        )

    def _capturar(self, factura: Factura) -> str | None:
        config.CARPETA_EVIDENCIAS.mkdir(parents=True, exist_ok=True)
        nombre = re.sub(r"[^A-Za-z0-9_-]", "_", f"{factura.id_lista}_{factura.factura}_{factura.nit}")
        ruta = config.CARPETA_EVIDENCIAS / f"falla_{nombre}_{datetime.now():%Y%m%d_%H%M%S}.png"
        try:
            self.pagina.screenshot(path=ruta, full_page=True)
            return f"evidencias/{ruta.name}"
        except PlaywrightError:
            return None

    @staticmethod
    def _resultado_crudo(fila: FilaEntrada, estado: str, detalle: str) -> Resultado:
        id_lista = entero_limpio(fila.id_lista)
        nit = limpiar_nit(fila.nit)
        return Resultado(
            id_lista=id_lista if id_lista is not None else texto_limpio(fila.id_lista),
            factura=texto_limpio(fila.factura),
            nit=int(nit) if nit else texto_limpio(fila.nit),
            estado=estado,
            detalle=detalle,
        )

    @staticmethod
    def _registrar(resultado: Resultado) -> Resultado:
        nivel = logging.INFO if resultado.estado in (CAUSADA, YA_CAUSADA) else logging.WARNING
        if resultado.estado == FALLA_SISTEMA:
            nivel = logging.ERROR
        log.log(
            nivel,
            "IdLista=%s | Factura=%s | NIT=%s | %s | %s",
            resultado.id_lista,
            resultado.factura,
            resultado.nit,
            resultado.estado,
            resultado.causacion or resultado.detalle,
        )
        return resultado
