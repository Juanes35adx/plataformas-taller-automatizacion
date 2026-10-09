import logging
import subprocess
import sys
from collections import Counter

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

import config
from lector import leer_por_radicar
from reporte import escribir_resultados
from robot import RobotCausaciones


def configurar_log() -> None:
    config.CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    formato = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%Y-%m-%d %H:%M:%S")
    archivo = logging.FileHandler(config.ARCHIVO_LOG, mode="w", encoding="utf-8")
    archivo.setFormatter(formato)
    consola = logging.StreamHandler()
    consola.setFormatter(formato)
    log = logging.getLogger("bot")
    log.setLevel(logging.INFO)
    log.addHandler(archivo)
    log.addHandler(consola)


def lanzar_navegador(p):
    try:
        return p.chromium.launch(headless=config.HEADLESS)
    except PlaywrightError as e:
        if "Executable doesn't exist" not in str(e):
            raise
        # máquina sin estado previo: se descarga Chromium una sola vez
        print("Chromium no está instalado; ejecutando 'playwright install chromium'...", flush=True)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        return p.chromium.launch(headless=config.HEADLESS)


def main() -> None:
    if not config.ARCHIVO_ENTRADA.exists():
        raise SystemExit(f"No existe el libro de entrada {config.ARCHIVO_ENTRADA}")
    filas = leer_por_radicar(config.ARCHIVO_ENTRADA)
    configurar_log()
    print(f"{len(filas)} facturas por radicar en {config.ARCHIVO_ENTRADA.name} | portal {config.PORTAL_URL}", flush=True)

    resultados = []
    try:
        with sync_playwright() as p:
            navegador = lanzar_navegador(p)
            pagina = navegador.new_page()
            pagina.set_default_timeout(config.TIMEOUT_MS)
            robot = RobotCausaciones(pagina)
            for fila in filas:
                resultados.append(robot.procesar(fila))
            navegador.close()
    finally:
        # aunque el lote se interrumpa, queda el resultado de lo procesado
        escribir_resultados(config.ARCHIVO_RESULTADOS, resultados)

    resumen = Counter(r.estado for r in resultados)
    print(f"Resultados en {config.ARCHIVO_RESULTADOS}: " + ", ".join(f"{k}={v}" for k, v in resumen.items()), flush=True)


if __name__ == "__main__":
    main()
