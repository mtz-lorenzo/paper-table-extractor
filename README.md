# 🧬 Paper Table Extractor

A web app that extracts tables from scientific papers in PDF format, shows them one at a time
with a preview, lets you download each one individually (CSV / Excel) and save them to a SQL
database (SQLite).

![Interface](docs/screenshot.png)

## Features

- **Detects real tables and discards running text.** Two-column papers are a classic problem:
  if you extract "everything that looks like a table", paragraphs end up split into fake
  cells. This project combines several signals to avoid that (see below).
- **One table at a time.** Navigate with ◀ ▶ arrows, with a preview and the table's caption
  (e.g. *Table 2. Binding affinities…*).
- **Multi-level headers.** A merged cell such as *Documented in experience* spanning two
  subcolumns is turned into full column names
  (`Documented in experience, n (%) – All experiences (n = 3778)`).
- **Multilingual captions:** `Table`, `Tabla`, `Tabela`, `表`, `표`.
- **Works on publisher PDFs** (Nature-style), where words have no real space characters and
  table rules are drawn as thin paths, and **ignores figures** such as heatmaps.
- **Individual download** as CSV or Excel.
- **Save to SQLite:** each table becomes its own SQL table, plus a `catalog` table recording
  where it came from.

## Installation and usage

Requires Python 3.9 or higher.

```bash
python -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:7860, upload a PDF and click **Extract tables**.

## How tables are detected

Each page goes through three stages, from the strongest evidence to the weakest:

1. **Drawn grid:** tables with real vertical *and* horizontal ruling lines. A grid without a
   "Table N" caption could be a figure, so it must meet the stricter criteria of stage 3.
2. **"Table N" caption:** the caption is located and only the area below it is extracted. If
   there are horizontal rules (*booktabs* style: top, under the header, bottom), the region is
   cropped exactly between them. Rules can be lines, rectangles or thin paths, and even drawn
   as one stroke per column. Columns are reconstructed from the vertical white space between
   words (`columns.py`), so a word is never cut in half.
3. **Extended search (optional, off by default):** tables with no caption and no lines, using
   stricter criteria (numeric columns) because the evidence is weaker.

Every candidate also goes through an **anti-paragraph filter** (`validation.py`): it is
discarded if it has many cells with 6 or more words, if its cells are lowercase-initial
fragments with no numbers, if most cells hold only symbols (heatmaps with `*`), or if it is
mostly empty. Words are split by a gap proportional to the font size, because many publisher
PDFs have no real space characters. For Chinese and Japanese, which are
written without spaces, words are approximated by character count. The thresholds live in
`table_extractor/config.py`.

## Database

When saving, a SQLite file is created (or updated), `paper_tables.db` by default:

- one SQL table per extracted table, named `<pdf>__p<page>_t<n>`;
- a `catalog` table with the source PDF, page, caption, number of rows and columns, and when
  it was saved.

Saving the same table again replaces it instead of duplicating it.

```bash
sqlite3 paper_tables.db
```
```sql
SELECT sql_name, file, page, caption, n_rows FROM catalog;
SELECT * FROM "paper_dmt_2024__p3_t1";
```

It can also be read from Python:

```python
import sqlite3, pandas as pd
con = sqlite3.connect("paper_tables.db")
df = pd.read_sql('SELECT * FROM "paper_dmt_2024__p3_t1"', con)
```

> All values are stored as text (for example `"1415 (37.5)"`), because paper tables often mix
> numbers with percentages, deviations and symbols.

## Try it with real papers

The `examples/` folder contains an open-access paper you can upload to the app:

| File | Paper | License |
|------|-------|---------|
| `s41467-024-44742-0.pdf` | Kim, S. S., Truong, B., Jagadeesh, K., Dey, K. K., Shen, A. Z., Raychaudhuri, S., Kellis, M. & Price, A. L. (2024). *Leveraging single-cell ATAC-seq and RNA-seq to identify disease-critical fetal and adult brain cell types*. Nature Communications 15, 563. https://doi.org/10.1038/s41467-024-44742-0 | CC BY 4.0 |

It has two tables on page 3 (**Table 1**: summary of findings, 5 × 5; **Table 2**: notable
disease–cell type associations, 11 × 6), plus figures with heatmaps and a reference list that
the extractor correctly ignores.

## Project structure

```
app.py                      # Gradio interface
table_extractor/
├── config.py               # thresholds and regular expressions
├── text_utils.py           # cell cleaning, "is it numeric?", word counting
├── geometry.py             # text segments, crops, ruling lines, captions
├── columns.py              # columns from white space between words
├── headers.py              # multi-level headers and DataFrame building
├── validation.py           # real table or running text?
├── detector.py             # orchestrates per-page extraction
├── export.py               # CSV / Excel
└── database.py             # saving to SQLite
tests/                      # unit and end-to-end tests
examples/                   # open-access paper to try the app
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The end-to-end tests generate synthetic PDFs (`tests/sample_pdf.py`) that mimic a paper: two
columns of running text, a table with a grid and a merged header, *booktabs*-style tables, and
Japanese and Korean pages. Among other things, they verify that pages of plain text do not
produce false positives.

There is also a regression test on the open-access paper in `examples/`. The project was
refined using tables from real papers; the synthetic PDFs make most tests reproducible without
depending on third-party documents.

## Known limitations

- The caption ("Table N") is assumed to be **above** the table.
- In two-column papers, a table **without lines** inside a single column may pull in text from
  the other column. The anti-paragraph filter usually discards it.
- A multi-line cell in a table without a grid may show up as separate rows.
- Merged cells are handled for headers (up to 3 levels), but not inside the table body.
- No OCR: it does not work with scanned PDFs or tables embedded as images.
- Category rows (for example "Somatic") are kept as rows with empty cells.
- Superscript citation numbers stay glued to the text (`Insomnia75`), and a character with no
  Unicode mapping in the PDF (for example some `fi` ligatures) can be dropped.
- Two columns of a table must be separated by a visible gap (at least 6 pt); cells that touch
  the next column cannot be split.
- Japanese and Korean support is covered by synthetic PDFs only; it has not been validated on
  a large set of real papers. Vertical (tategaki) text is not supported.

## Next steps

- Turn category rows into a `Category` column.
- Split values such as `1415 (37.5)` into numeric columns (n and %).
- OCR support for scanned PDFs.
- Recognize captions placed below the table.

## License

MIT. See [LICENSE](LICENSE).
