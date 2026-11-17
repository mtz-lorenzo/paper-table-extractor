"""Japanese and Korean papers: captions like 表1 / 표 1., and text written without spaces."""
import pytest

pytest.importorskip("pdfplumber")
pytest.importorskip("reportlab")

from sample_pdf import create_cjk_pdf  # noqa: E402

from table_extractor.detector import extract_tables  # noqa: E402


@pytest.fixture
def tables(tmp_path):
    path = tmp_path / "cjk.pdf"
    create_cjk_pdf(str(path))
    return extract_tables(str(path))


def test_finds_one_table_per_page_and_no_false_positives(tables):
    assert [t["page"] for t in tables] == [1, 2]


def test_japanese_table(tables):
    t = tables[0]
    assert t["caption"].startswith("表1")
    assert list(t["df"].columns) == ["化合物", "受容体", "Ki (nM)"]
    assert t["df"].iloc[1].tolist() == ["ハルミン", "MAO-A", "0.8 ± 0.1"]


def test_korean_table(tables):
    t = tables[1]
    assert t["caption"].startswith("표 1.")
    assert list(t["df"].columns) == ["화합물", "수용체", "Ki (nM)"]
    assert t["df"].iloc[1].tolist() == ["하르민", "MAO-A", "0.8 ± 0.1"]
