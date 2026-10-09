# Radicación automatizada de facturas de proveedores

Taller de automatización de Plataformas de Programación (2026-2). Juan Esteban Correa, prefijo `juane.correa`.

| Carpeta | Contenido |
| :--- | :--- |
| `robot_causaciones/` | Robot RPA en Python (Playwright) que causa en SICOF las facturas de la cola `PorRadicar` |
| `flujos/` | Flujos de Power Automate exportados como paquete: aprobación y cierre |
| `evidencias/` | Log y resultados del robot, y capturas de los flujos |

## Robot de causación

Requiere Python 3.13 y uv 0.8 o superior. Con el portal SICOF arriba en el puerto 8020:

```bash
cd robot_causaciones
cp .env.example .env
uv run python main.py
```

Si Chromium no está instalado, el robot ejecuta `playwright install chromium` la primera vez. Sin `.env` usa los valores de `.env.example`.

Entrada: `datos/por_radicar.xlsx` (libro `juane.correa-por_radicar.xlsx` descargado de OneDrive). Salida: `salida/bot.log`, `salida/resultados.xlsx` (tabla `Resultados`) y, si alguna factura agota los tres intentos, capturas en `salida/evidencias/`.

| Módulo | Responsabilidad |
| :--- | :--- |
| `main.py` | Orquesta el lote: lee el libro, abre el navegador, procesa cada fila y escribe resultados |
| `config.py` | Variables de `.env` y rutas |
| `lector.py` | Lee la primera hoja ubicando las columnas por encabezado; ignora filas sin `IdLista` |
| `validacion.py` | Limpia el NIT y valida valor y fecha antes de tocar SICOF |
| `robot.py` | Idempotencia (consulta previa), reintentos con tenacity y clasificación del resultado |
| `paginas/` | Page objects de SICOF con localizadores por etiqueta y rol, que sirven en `--ui v1` y `--ui v2` |
| `reporte.py` | Escribe `resultados.xlsx` con la tabla `Resultados` |

Clasificación de errores: los mensajes `role="alert"` de SICOF y los centros de costo que no están en la lista desplegable son rechazos de negocio y no se reintentan. La pantalla SICOF-503, los tiempos de espera agotados y los errores de conexión son fallas de sistema y se reintentan hasta tres intentos por factura.
