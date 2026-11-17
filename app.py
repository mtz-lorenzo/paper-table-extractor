"""Web interface (Gradio) for the scientific-paper table extractor."""
import json
import logging
import os

import gradio as gr
import pandas as pd

from table_extractor.config import DB_PATH
from table_extractor.database import save_to_db
from table_extractor.detector import extract_tables
from table_extractor.export import export_files

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


# ---------------------------------------------------------------------------
# Current-table view
# ---------------------------------------------------------------------------
def show_table(tables, idx):
    """Return everything needed to refresh the view of the current table."""
    total = len(tables)
    table = tables[idx]
    csv_path, xlsx_path = export_files(table)

    caption = table.get("caption", "")
    if len(caption) > 160:
        caption = caption[:157] + "..."
    info = (
        f"### Table {idx + 1} of {total}  \n"
        f"Page {table['page']} · {len(table['df'])} rows × "
        f"{len(table['df'].columns)} columns"
    )
    if caption:
        info += f"  \n*{caption}*"

    records = table["df"].to_dict(orient="records")
    return (
        idx,
        info,
        table["df"],
        json.dumps(records, indent=2, ensure_ascii=False),
        gr.update(value=csv_path, interactive=True),
        gr.update(value=xlsx_path, interactive=xlsx_path is not None),
        gr.update(interactive=idx > 0),
        gr.update(interactive=idx < total - 1),
    )


def empty_view(message):
    return (
        0,
        message,
        pd.DataFrame(),
        "",
        gr.update(value=None, interactive=False),
        gr.update(value=None, interactive=False),
        gr.update(interactive=False),
        gr.update(interactive=False),
    )


def process(pdf_file, extended_search):
    if pdf_file is None:
        return ("Please upload a PDF file.", []) + empty_view("")
    path = getattr(pdf_file, "name", pdf_file)
    tables = extract_tables(path, extended_search)
    if not tables:
        return (
            "No tables were detected in this PDF. If you know it has some, "
            "try enabling the extended search.",
            [],
        ) + empty_view("")
    status = f"Done! {len(tables)} tables extracted."
    return (status, tables) + show_table(tables, 0)


def move(tables, idx, delta):
    if not tables:
        return empty_view("")
    new_idx = min(max(idx + delta, 0), len(tables) - 1)
    return show_table(tables, new_idx)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
def _save(tables, indices, db_path):
    db_path = (db_path or DB_PATH).strip() or DB_PATH
    try:
        n = save_to_db(tables, indices, db_path)
    except Exception as e:
        return f"Could not save: {e}"
    return f"✅ {n} table(s) saved to {os.path.abspath(db_path)}"


def save_current(tables, idx, db_path):
    if not tables:
        return "Extract the tables from a PDF first."
    return _save(tables, [idx], db_path)


def save_all(tables, db_path):
    if not tables:
        return "Extract the tables from a PDF first."
    return _save(tables, list(range(len(tables))), db_path)


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
with gr.Blocks(title="Paper Table Extractor", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🧬 Scientific Paper Table Extractor")
    gr.Markdown(
        "Upload a paper as a PDF, browse the detected tables with the arrows and "
        "download any of them individually."
    )

    tables_state = gr.State([])
    idx_state = gr.State(0)

    with gr.Row():
        pdf_input = gr.File(label="Upload your paper (PDF)", file_types=[".pdf"])
        with gr.Column():
            extended_chk = gr.Checkbox(
                label="Extended search (also looks for tables with no 'Table N' caption "
                "and no lines; may produce false positives)",
                value=False,
            )
            extract_btn = gr.Button("Extract tables", variant="primary")

    status = gr.Textbox(label="Status", interactive=False)

    with gr.Row():
        prev_btn = gr.Button("◀ Previous", interactive=False)
        info = gr.Markdown("")
        next_btn = gr.Button("Next ▶", interactive=False)

    preview = gr.Dataframe(label="Table preview", interactive=False, wrap=True)

    with gr.Row():
        csv_btn = gr.DownloadButton("⬇ Download CSV", interactive=False)
        xlsx_btn = gr.DownloadButton("⬇ Download Excel", interactive=False)

    with gr.Group():
        gr.Markdown("#### 🗄️ Save to a SQL database (SQLite)")
        db_path_box = gr.Textbox(label="Database file", value=DB_PATH)
        with gr.Row():
            save_one_btn = gr.Button("💾 Save this table")
            save_all_btn = gr.Button("💾 Save all tables")
        db_status = gr.Textbox(label="Database status", interactive=False)

    with gr.Accordion("View as JSON (list of dictionaries)", open=False):
        json_out = gr.Code(language="json", lines=12, label="Current table as JSON")

    # Output order of show_table()
    view = [idx_state, info, preview, json_out, csv_btn, xlsx_btn, prev_btn, next_btn]

    extract_btn.click(
        fn=process,
        inputs=[pdf_input, extended_chk],
        outputs=[status, tables_state] + view,
    )
    prev_btn.click(
        fn=lambda t, i: move(t, i, -1),
        inputs=[tables_state, idx_state],
        outputs=view,
    )
    next_btn.click(
        fn=lambda t, i: move(t, i, +1),
        inputs=[tables_state, idx_state],
        outputs=view,
    )
    save_one_btn.click(
        fn=save_current,
        inputs=[tables_state, idx_state, db_path_box],
        outputs=db_status,
    )
    save_all_btn.click(
        fn=save_all,
        inputs=[tables_state, db_path_box],
        outputs=db_status,
    )

if __name__ == "__main__":
    demo.launch()
