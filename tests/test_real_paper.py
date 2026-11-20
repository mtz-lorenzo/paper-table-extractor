"""Regression test on a real open-access paper (Nature Communications, CC BY 4.0).
It is skipped automatically if the example PDF is not present."""
import os

import pytest

pytest.importorskip("pdfplumber")

from table_extractor.detector import extract_tables  # noqa: E402

PAPER = os.path.join(os.path.dirname(__file__), "..", "examples", "s41467-024-44742-0.pdf")


@pytest.fixture
def tables():
    if not os.path.exists(PAPER):
        pytest.skip("example PDF not found")
    return extract_tables(PAPER)


def test_finds_the_two_real_tables_and_nothing_from_figures_or_references(tables):
    # Tables 1 and 2 are on page 3. Figure heatmaps and the reference list are ignored.
    assert [(t["page"], t["caption"][:7]) for t in tables] == [(3, "Table 1"), (3, "Table 2")]


def test_table_1_summary_of_findings(tables):
    df = tables[0]["df"]
    assert list(df.columns) == ["col_0", "Fetal scATAC", "Fetal scRNA", "Adult scATAC", "Adult scRNA"]
    assert df.shape == (5, 5)
    assert df.iloc[0].tolist() == ["Brain cell types", "14", "34", "18", "17"]


def test_table_2_notable_associations(tables):
    df = tables[1]["df"]
    assert list(df.columns) == [
        "Disease/trait", "Cell type", "Data source", "τ∗ (SE)", "p-value(τ∗)", "q-value"
    ]
    assert df.shape == (11, 6)
    assert df.iloc[6].tolist()[1:4] == ["Ganglion cells", "Fetal brain scRNA", "0.45 (0.14)"]
    assert df.iloc[3, 4] == "8.72 × 10−10"
