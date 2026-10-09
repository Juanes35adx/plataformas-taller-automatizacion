import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).parent

# Si no existe .env se usa .env.example, que apunta al portal en el puerto por defecto.
archivo_env = RAIZ / ".env"
if not archivo_env.exists():
    archivo_env = RAIZ / ".env.example"
load_dotenv(archivo_env)

REQUERIDOS = ("PORTAL_URL", "PORTAL_USUARIO", "PORTAL_CLAVE")

faltantes = [x for x in REQUERIDOS if not os.getenv(x)]
if faltantes:
    raise SystemExit(f"Faltan variables de entorno requeridas: {faltantes}")

PORTAL_URL = os.getenv("PORTAL_URL").rstrip("/")
PORTAL_USUARIO = os.getenv("PORTAL_USUARIO")
PORTAL_CLAVE = os.getenv("PORTAL_CLAVE")
HEADLESS = os.getenv("BOT_HEADLESS", "true").strip().lower() in ("true", "1", "si", "sí")

ARCHIVO_ENTRADA = RAIZ / "datos" / "por_radicar.xlsx"
CARPETA_SALIDA = RAIZ / "salida"
CARPETA_EVIDENCIAS = CARPETA_SALIDA / "evidencias"
ARCHIVO_LOG = CARPETA_SALIDA / "bot.log"
ARCHIVO_RESULTADOS = CARPETA_SALIDA / "resultados.xlsx"

MAX_INTENTOS = 3
ESPERA_REINTENTO_S = 2
TIMEOUT_MS = 15_000
