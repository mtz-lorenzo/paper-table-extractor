from table_extractor.text_utils import (
    clean_cell,
    count_words,
    is_numeric,
    unique_headers,
    visual_length,
)


def test_is_numeric_accepts_typical_paper_values():
    for cell in ["12.5%", "0.45 ± 0.03", "p<0.05", "1415 (37.5)", "n=3778", "<0.001"]:
        assert is_numeric(cell), cell


def test_is_numeric_rejects_text_and_labels():
    for cell in ["Somatic", "All experiences (n = 3778)", "IC50", "10 mg", ""]:
        assert not is_numeric(cell), cell


def test_clean_cell_collapses_line_breaks_and_spaces():
    assert clean_cell("  Body\nvibration   buzz ") == "Body vibration buzz"
    assert clean_cell(None) == ""


def test_unique_headers_replaces_empty_and_disambiguates():
    assert unique_headers(["A", "", "A", "A"]) == ["A", "col_1", "A_1", "A_2"]


def test_count_words_space_separated_text():
    assert count_words("Experiences with no reported psychoactive substance use") == 7
    assert count_words("DMT") == 1


def test_count_words_chinese_japanese_has_no_spaces():
    # 12 characters without spaces ~ 6 words
    assert count_words("結合親和性の測定結果を示す") >= 5
    assert count_words("結合") == 1


def test_count_words_korean_uses_spaces():
    assert count_words("결합 친화도 측정 결과") == 4


def test_visual_length_counts_wide_characters_double():
    assert visual_length("abcd") == 4
    assert visual_length("結合親和") == 8
    assert visual_length("결합") == 4
