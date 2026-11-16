"""Exportación de una tabla a archivos CSV / Excel temporales."""
import logging
import os
import tempfile

logger = logging.getLogger(__name__)


def exportar_archivos(tabla):
    """Crea el CSV y el Excel de una tabla en una carpeta temporal.
    Devuelve (ruta_csv, ruta_xlsx); ruta_xlsx es None si falta openpyxl."""
    carpeta = tempfile.mkdtemp()
    base = f"tabla_p{tabla['pagina']}_n{tabla['tabla_num']}"
    ruta_csv = os.path.join(carpeta, base + ".csv")
    ruta_xlsx = os.path.join(carpeta, base + ".xlsx")

    tabla["df"].to_csv(ruta_csv, index=False, encoding="utf-8-sig")
    try:
        tabla["df"].to_excel(ruta_xlsx, index=False)  # requiere openpyxl
    except ImportError:
        logger.warning("openpyxl no está instalado: no se genera el Excel")
        ruta_xlsx = None
    return ruta_csv, ruta_xlsx
