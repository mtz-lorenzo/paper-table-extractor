from table_extractor.headers import (
    count_header_rows,
    flatten_header,
    is_section_row,
    matrix_to_df,
)

# Table with a merged header (like the ones in experience-report papers)
MERGED = [
    ["Coded units and themes", "Documented in experience, n (%)", ""],
    ["", "All experiences (n = 3778)", "Experiences with no reported concomitant psychoactive substance use (n = 3242)"],
    ["Somatic", "", ""],
    ["Somaesthesias", "1415 (37.5)", "1212 (37.4)"],
    ["Body vibration, buzz, or tingling", "1026 (27.2)", "878 (27.1)"],
]

SIMPLE = [
    ["Compound", "Receptor", "Effect"],
    ["DMT", "5-HT2A", "Agonist"],
    ["Harmine", "MAO-A", "Inhibitor"],
]


def test_merged_header_spans_two_rows():
    assert count_header_rows(MERGED) == 2


def test_flatten_repeats_the_title_that_spans_several_columns():
    names = flatten_header(MERGED[:2])
    assert names[0] == "Coded units and themes"
    assert names[1] == "Documented in experience, n (%) – All experiences (n = 3778)"
    assert names[2].startswith("Documented in experience, n (%) – Experiences with no")


def test_qualitative_table_without_numbers_keeps_its_data_rows():
    assert count_header_rows(SIMPLE) == 1


def test_section_row_ends_the_header():
    assert is_section_row(["Somatic", "", ""])
    assert not is_section_row(["", "x", ""])
    assert not is_section_row(["Somaesthesias", "1415", "1212"])


def test_matrix_to_df_splits_header_and_data():
    df = matrix_to_df(MERGED)
    assert len(df.columns) == 3
    assert len(df) == 3  # Somatic, Somaesthesias, Body vibration
    assert df.iloc[1, 1] == "1415 (37.5)"


def test_matrix_to_df_pads_ragged_rows():
    df = matrix_to_df([["A", "B", "C"], ["1", "2"], ["3", "4", "5"]])
    assert df.shape == (2, 3)
    assert df.iloc[0, 2] == ""
