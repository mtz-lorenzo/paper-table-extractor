"""Export a table to temporary CSV / Excel files."""
import logging
import os
import tempfile

logger = logging.getLogger(__name__)


def export_files(table):
    """Create the CSV and Excel files of a table in a temporary folder.
    Returns (csv_path, xlsx_path); xlsx_path is None if openpyxl is missing."""
    folder = tempfile.mkdtemp()
    base = f"table_p{table['page']}_n{table['table_num']}"
    csv_path = os.path.join(folder, base + ".csv")
    xlsx_path = os.path.join(folder, base + ".xlsx")

    table["df"].to_csv(csv_path, index=False, encoding="utf-8-sig")
    try:
        table["df"].to_excel(xlsx_path, index=False)  # requires openpyxl
    except ImportError:
        logger.warning("openpyxl is not installed: skipping the Excel file")
        xlsx_path = None
    return csv_path, xlsx_path
