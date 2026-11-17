"""End-to-end tests with synthetic PDFs (2 columns of text + tables)."""
import pytest

pytest.importorskip("pdfplumber")
pytest.importorskip("reportlab")

from sample_pdf import create_pdf, create_prose_only_pdf  # noqa: E402

from table_extractor.detector import extract_tables  # noqa: E402


@pytest.fixture
def tables(tmp_path):
    path = tmp_path / "paper.pdf"
    create_pdf(str(path))
    return extract_tables(str(path))


def test_finds_exactly_the_three_tables(tables):
    # Page 3 is plain two-column text: it must not produce false positives
    assert [t["page"] for t in tables] == [1, 2, 4]


def test_prose_only_pdf_gives_no_tables_even_with_extended_search(tmp_path):
    path = tmp_path / "prose.pdf"
    create_prose_only_pdf(str(path))
    assert extract_tables(str(path), extended_search=False) == []
    assert extract_tables(str(path), extended_search=True) == []


def test_extended_search_adds_no_junk(tmp_path):
    path = tmp_path / "paper.pdf"
    create_pdf(str(path))
    assert [t["page"] for t in extract_tables(str(path), extended_search=True)] == [1, 2, 4]


def test_grid_table_with_merged_header(tables):
    t = tables[0]
    assert t["source"] == "grid"
    assert t["caption"].startswith("Table 1.")
    cols = list(t["df"].columns)
    assert cols[0] == "Coded units and themes"
    assert cols[1] == "Documented in experience, n (%) – All experiences (n = 3778)"
    assert cols[2].startswith("Documented in experience, n (%) – Experiences with no reported")
    assert len(t["df"]) == 5  # Somatic + 4 data rows
    assert t["df"].iloc[1].tolist() == ["Somaesthesias", "1415 (37.5)", "1212 (37.4)"]


def test_booktabs_table_does_not_cut_words(tables):
    t = tables[1]
    assert t["source"] == "caption"
    assert list(t["df"].columns) == ["Compound", "Receptor", "Ki (nM)"]
    assert t["df"].iloc[0].tolist() == ["DMT", "5-HT2A", "127 ± 12"]
    assert len(t["df"]) == 4


def test_booktabs_with_merged_header_and_no_grid(tables):
    t = tables[2]
    assert list(t["df"].columns) == [
        "Compound",
        "Binding affinity (nM) – Ki",
        "Binding affinity (nM) – IC50",
    ]
    assert t["df"].iloc[0].tolist() == ["DMT", "127", "340"]
    assert len(t["df"]) == 3
