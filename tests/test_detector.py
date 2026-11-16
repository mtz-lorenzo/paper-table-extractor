"""Pruebas de punta a punta con PDFs sintéticos (2 columnas de texto + tablas)."""
import pytest

pytest.importorskip("pdfplumber")
pytest.importorskip("reportlab")

from pdf_ejemplo import crear_pdf, crear_pdf_solo_prosa  # noqa: E402

from extractor_tablas.detector import extraer_tablas  # noqa: E402


@pytest.fixture
def tablas(tmp_path):
    ruta = tmp_path / "paper.pdf"
    crear_pdf(str(ruta))
    return extraer_tablas(str(ruta))


def test_encuentra_exactamente_las_tres_tablas(tablas):
    # Página 3 es solo texto en dos columnas: no debe generar falsos positivos
    assert [t["pagina"] for t in tablas] == [1, 2, 4]


def test_ninguna_pagina_de_prosa_da_falsos_positivos_ni_con_busqueda_ampliada(tmp_path):
    ruta = tmp_path / "prosa.pdf"
    crear_pdf_solo_prosa(str(ruta))
    assert extraer_tablas(str(ruta), permisivo=False) == []
    assert extraer_tablas(str(ruta), permisivo=True) == []


def test_busqueda_ampliada_no_agrega_basura(tmp_path):
    ruta = tmp_path / "paper.pdf"
    crear_pdf(str(ruta))
    assert [t["pagina"] for t in extraer_tablas(str(ruta), permisivo=True)] == [1, 2, 4]


def test_tabla_con_grilla_y_encabezado_combinado(tablas):
    t = tablas[0]
    assert t["origen"] == "grilla"
    assert t["titulo"].startswith("Table 1.")
    cols = list(t["df"].columns)
    assert cols[0] == "Coded units and themes"
    assert cols[1] == "Documented in experience, n (%) – All experiences (n = 3778)"
    assert cols[2].startswith("Documented in experience, n (%) – Experiences with no reported")
    assert len(t["df"]) == 5  # Somatic + 4 filas de datos
    assert t["df"].iloc[1].tolist() == ["Somaesthesias", "1415 (37.5)", "1212 (37.4)"]


def test_tabla_booktabs_no_corta_palabras(tablas):
    t = tablas[1]
    assert t["origen"] == "titulo"
    assert list(t["df"].columns) == ["Compound", "Receptor", "Ki (nM)"]
    assert t["df"].iloc[0].tolist() == ["DMT", "5-HT2A", "127 ± 12"]
    assert len(t["df"]) == 4


def test_booktabs_con_encabezado_combinado_sin_grilla(tablas):
    t = tablas[2]
    assert list(t["df"].columns) == [
        "Compound",
        "Binding affinity (nM) – Ki",
        "Binding affinity (nM) – IC50",
    ]
    assert t["df"].iloc[0].tolist() == ["DMT", "127", "340"]
    assert len(t["df"]) == 3
