"""Regression tests for publisher-style PDFs (e.g. Nature): no real space characters,
table rules drawn as curves, and figure grids that must not be mistaken for tables."""
import pytest

pytest.importorskip("pdfplumber")
pytest.importorskip("reportlab")

from sample_pdf import create_publisher_style_pdf  # noqa: E402

from table_extractor.detector import extract_tables  # noqa: E402


@pytest.fixture
def pdf_path(tmp_path):
    path = tmp_path / "publisher.pdf"
    create_publisher_style_pdf(str(path))
    return str(path)


def test_extracts_the_table_with_curve_rules_and_positional_spacing(pdf_path):
    tables = extract_tables(pdf_path)
    assert len(tables) == 1
    t = tables[0]
    assert t["source"] == "caption"
    assert t["caption"] == "Table 1 | Notable disease-cell type associations"
    assert list(t["df"].columns) == ["Disease/trait", "Cell type", "Data source", "Effect size (SE)"]
    assert len(t["df"]) == 4
    assert t["df"].iloc[2].tolist() == [
        "Intelligence", "Corticofugal projection neurons", "Adult brain scRNA", "0.76 (0.14)"
    ]


def test_figure_grids_without_caption_are_not_tables(pdf_path):
    # the heatmap ('*' cells) and the 2-column mini grid sit below the table
    for extended in (False, True):
        tables = extract_tables(pdf_path, extended_search=extended)
        assert len(tables) == 1, extended
