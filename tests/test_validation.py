from table_extractor.validation import is_prose_row, looks_like_table, tidy_matrix

# A paper paragraph split into "cells" by a bad detection (the original failure case)
PROSE = [
    ["N, N-Dimethyltryptami", "that are mediated prima", "ne (N, N-DMT) is a na", "rily via the serotonerg", "turally occurring classic p"],
    ["sychedelic with p", "2A (5-HT ) rec 2A", "sychoactive properties", "eptor agonism1. Plant-", "based preparations of"],
    ["ayahuasca contain DMT", "and have been used for", "centuries in ritual", "settings across the", "Amazon basin and beyond"],
]

NUMERIC = [
    ["Group", "N", "Mean (SD)", "p-value"],
    ["Control", "24", "12.4 (3.1)", "0.032"],
    ["DMT 0.5 mg/kg", "22", "15.8 (4.0)", "<0.001"],
    ["DMT 1.0 mg/kg", "23", "18.2 (3.7)", "<0.001"],
]

QUALITATIVE = [
    ["Compound", "Receptor", "Effect"],
    ["DMT", "5-HT2A", "Agonist"],
    ["Harmine", "MAO-A", "Inhibitor"],
    ["5-MeO-DMT", "5-HT1A", "Agonist"],
]

# Japanese table: the body text has no spaces
JAPANESE_PROSE = [
    ["本研究ではジメチルトリプタミンの", "セロトニン受容体に対する作用を", "詳細に検討した結果を報告する"],
    ["結合親和性の測定には放射性", "リガンドを用いた競合実験を", "実施し解析を行った結果である"],
    ["得られたデータは統計学的に", "解析されその有意性が確認され", "考察において詳しく議論される"],
]

JAPANESE_TABLE = [
    ["化合物", "受容体", "Ki (nM)"],
    ["DMT", "5-HT2A", "127 ± 12"],
    ["ハルミン", "MAO-A", "0.8 ± 0.1"],
    ["シロシン", "5-HT2A", "49 ± 6"],
]


def test_split_paragraph_is_never_a_table():
    for source in ("grid", "caption", "free"):
        assert not looks_like_table(tidy_matrix(PROSE), source), source


def test_numeric_table_is_accepted_for_every_source():
    for source in ("grid", "caption", "free"):
        assert looks_like_table(tidy_matrix(NUMERIC), source), source


def test_qualitative_table_needs_strong_evidence():
    assert looks_like_table(QUALITATIVE, "caption")
    assert looks_like_table(QUALITATIVE, "grid")
    assert not looks_like_table(QUALITATIVE, "free")  # no numbers, no caption: stricter


def test_too_small_is_not_a_table():
    assert not looks_like_table([["A", "B"], ["1", "2"]], "caption")  # only 2 rows
    assert not looks_like_table([["A"], ["1"], ["2"]], "caption")     # one column


def test_japanese_running_text_is_not_a_table():
    for source in ("grid", "caption", "free"):
        assert not looks_like_table(tidy_matrix(JAPANESE_PROSE), source), source


def test_japanese_table_is_accepted():
    assert looks_like_table(JAPANESE_TABLE, "caption")


def test_is_prose_row():
    assert is_prose_row(["Table 1. A very long caption describing what the table contains", ""])
    assert not is_prose_row(["Control", "24", "12.4 (3.1)"])
    assert is_prose_row(["本研究ではジメチルトリプタミンのセロトニン受容体に対する作用を詳細に検討した", ""])


def test_tidy_matrix_removes_caption_and_empty_rows_and_columns():
    matrix = [
        ["Table 1. A very long caption describing what the table contains in detail", "", ""],
        ["", "", ""],
        ["Group", "N", ""],
        ["A", "1", ""],
        ["B", "2", ""],
    ]
    assert tidy_matrix(matrix) == [["Group", "N"], ["A", "1"], ["B", "2"]]
