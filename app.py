"""Interfaz web (Gradio) del extractor de tablas de papers científicos."""
import json
import logging
import os

import gradio as gr
import pandas as pd

from extractor_tablas.base_datos import guardar_en_db
from extractor_tablas.config import DB_PATH
from extractor_tablas.detector import extraer_tablas
from extractor_tablas.exportacion import exportar_archivos

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


# ---------------------------------------------------------------------------
# Vista de la tabla actual
# ---------------------------------------------------------------------------
def mostrar(tablas, idx):
    """Devuelve todo lo necesario para refrescar la vista de la tabla actual."""
    total = len(tablas)
    tabla = tablas[idx]
    ruta_csv, ruta_xlsx = exportar_archivos(tabla)

    titulo = tabla.get("titulo", "")
    if len(titulo) > 160:
        titulo = titulo[:157] + "..."
    info = (
        f"### Tabla {idx + 1} de {total}  \n"
        f"Página {tabla['pagina']} · {len(tabla['df'])} filas × "
        f"{len(tabla['df'].columns)} columnas"
    )
    if titulo:
        info += f"  \n*{titulo}*"

    registros = tabla["df"].to_dict(orient="records")
    return (
        idx,
        info,
        tabla["df"],
        json.dumps(registros, indent=2, ensure_ascii=False),
        gr.update(value=ruta_csv, interactive=True),
        gr.update(value=ruta_xlsx, interactive=ruta_xlsx is not None),
        gr.update(interactive=idx > 0),
        gr.update(interactive=idx < total - 1),
    )


def vista_vacia(mensaje):
    return (
        0,
        mensaje,
        pd.DataFrame(),
        "",
        gr.update(value=None, interactive=False),
        gr.update(value=None, interactive=False),
        gr.update(interactive=False),
        gr.update(interactive=False),
    )


def procesar(archivo_pdf, permisivo):
    if archivo_pdf is None:
        return ("Por favor, sube un archivo PDF.", []) + vista_vacia("")
    ruta = getattr(archivo_pdf, "name", archivo_pdf)
    tablas = extraer_tablas(ruta, permisivo)
    if not tablas:
        return (
            "No se detectaron tablas en este PDF. Si sabés que tiene, probá activar "
            "la búsqueda ampliada.",
            [],
        ) + vista_vacia("")
    estado = f"¡Listo! Se extrajeron {len(tablas)} tablas en total."
    return (estado, tablas) + mostrar(tablas, 0)


def mover(tablas, idx, delta):
    if not tablas:
        return vista_vacia("")
    nuevo = min(max(idx + delta, 0), len(tablas) - 1)
    return mostrar(tablas, nuevo)


# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------
def _guardar(tablas, indices, ruta_db):
    ruta_db = (ruta_db or DB_PATH).strip() or DB_PATH
    try:
        n = guardar_en_db(tablas, indices, ruta_db)
    except Exception as e:
        return f"No se pudo guardar: {e}"
    return f"✅ {n} tabla(s) guardada(s) en {os.path.abspath(ruta_db)}"


def guardar_actual(tablas, idx, ruta_db):
    if not tablas:
        return "Primero extraé las tablas de un PDF."
    return _guardar(tablas, [idx], ruta_db)


def guardar_todas(tablas, ruta_db):
    if not tablas:
        return "Primero extraé las tablas de un PDF."
    return _guardar(tablas, list(range(len(tablas))), ruta_db)


# ---------------------------------------------------------------------------
# Interfaz
# ---------------------------------------------------------------------------
with gr.Blocks(title="Paper Table Extractor", theme=gr.themes.Soft()) as interfaz:
    gr.Markdown("# 🧬 Extractor de Tablas de Papers Científicos")
    gr.Markdown(
        "Sube el PDF de un paper, navega entre las tablas detectadas con las "
        "flechas y descarga la que quieras de forma individual."
    )

    tablas_state = gr.State([])
    idx_state = gr.State(0)

    with gr.Row():
        input_pdf = gr.File(label="Sube tu Paper en PDF", file_types=[".pdf"])
        with gr.Column():
            chk_permisivo = gr.Checkbox(
                label="Búsqueda ampliada (incluye tablas sin título 'Table N' ni líneas; "
                "puede traer falsos positivos)",
                value=False,
            )
            btn_procesar = gr.Button("Extraer Tablas", variant="primary")

    estado = gr.Textbox(label="Estado del proceso", interactive=False)

    with gr.Row():
        btn_prev = gr.Button("◀ Anterior", interactive=False)
        info = gr.Markdown("")
        btn_next = gr.Button("Siguiente ▶", interactive=False)

    preview = gr.Dataframe(label="Preview de la tabla", interactive=False, wrap=True)

    with gr.Row():
        dl_csv = gr.DownloadButton("⬇ Descargar CSV", interactive=False)
        dl_xlsx = gr.DownloadButton("⬇ Descargar Excel", interactive=False)

    with gr.Group():
        gr.Markdown("#### 🗄️ Guardar en base de datos SQL (SQLite)")
        ruta_db = gr.Textbox(label="Archivo de base de datos", value=DB_PATH)
        with gr.Row():
            btn_db_una = gr.Button("💾 Guardar esta tabla")
            btn_db_todas = gr.Button("💾 Guardar todas las tablas")
        estado_db = gr.Textbox(label="Estado de la base de datos", interactive=False)

    with gr.Accordion("Ver como JSON (lista de diccionarios)", open=False):
        out_json = gr.Code(language="json", lines=12, label="JSON de la tabla actual")

    # Orden de las salidas de mostrar()
    vista = [idx_state, info, preview, out_json, dl_csv, dl_xlsx, btn_prev, btn_next]

    btn_procesar.click(
        fn=procesar,
        inputs=[input_pdf, chk_permisivo],
        outputs=[estado, tablas_state] + vista,
    )
    btn_prev.click(
        fn=lambda t, i: mover(t, i, -1),
        inputs=[tablas_state, idx_state],
        outputs=vista,
    )
    btn_next.click(
        fn=lambda t, i: mover(t, i, +1),
        inputs=[tablas_state, idx_state],
        outputs=vista,
    )
    btn_db_una.click(
        fn=guardar_actual,
        inputs=[tablas_state, idx_state, ruta_db],
        outputs=estado_db,
    )
    btn_db_todas.click(
        fn=guardar_todas,
        inputs=[tablas_state, ruta_db],
        outputs=estado_db,
    )

if __name__ == "__main__":
    interfaz.launch()
