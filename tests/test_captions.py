from table_extractor.config import ANY_CAPTION_RE, CAPTION_RE


def test_recognizes_table_captions_in_several_languages():
    captions = [
        "Table 1. Coded units and themes",
        "Table 2: Binding affinities",
        "TABLE II",
        "Table S1.",
        "Tabla 3 - Resultados",
        "Tabela 4. Resultados principais",
        "表 1. 結合親和性",
        "表1　結合親和性",
        "표 1. 결합 친화도",
        "표 2 실험 결과",
    ]
    for text in captions:
        assert CAPTION_RE.match(text), text


def test_does_not_mistake_body_text_for_captions():
    body_text = [
        "Table 1 shows that the effect was larger",
        "表1に示すように結合が増加した",
        "표 1은 결과를 보여준다",
        "Tablets 1. were administered",
        "as described in Table 1.",
    ]
    for text in body_text:
        assert not CAPTION_RE.match(text), text


def test_any_caption_includes_figures():
    for text in ["Figure 3. Dose-response", "Fig. 2 Overview", "図1 概要", "그림 1. 개요", "Figura 4."]:
        assert ANY_CAPTION_RE.match(text), text
