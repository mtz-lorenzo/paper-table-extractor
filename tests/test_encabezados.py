from extractor_tablas.encabezados import (
    aplanar_encabezado,
    contar_filas_encabezado,
    es_fila_seccion,
    matriz_a_df,
)

# Tabla con encabezado combinado (como las de los papers de experiencias)
COMBINADO = [
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


def test_encabezado_combinado_ocupa_dos_filas():
    assert contar_filas_encabezado(COMBINADO) == 2


def test_aplanar_repite_el_titulo_que_abarca_varias_columnas():
    nombres = aplanar_encabezado(COMBINADO[:2])
    assert nombres[0] == "Coded units and themes"
    assert nombres[1] == "Documented in experience, n (%) – All experiences (n = 3778)"
    assert nombres[2].startswith("Documented in experience, n (%) – Experiences with no")


def test_tabla_cualitativa_sin_numeros_no_se_come_filas_de_datos():
    assert contar_filas_encabezado(SIMPLE) == 1


def test_fila_de_seccion_corta_el_encabezado():
    assert es_fila_seccion(["Somatic", "", ""])
    assert not es_fila_seccion(["", "x", ""])
    assert not es_fila_seccion(["Somaesthesias", "1415", "1212"])


def test_matriz_a_df_separa_encabezado_y_datos():
    df = matriz_a_df(COMBINADO)
    assert len(df.columns) == 3
    assert len(df) == 3  # Somatic, Somaesthesias, Body vibration
    assert df.iloc[1, 1] == "1415 (37.5)"


def test_matriz_a_df_completa_filas_irregulares():
    df = matriz_a_df([["A", "B", "C"], ["1", "2"], ["3", "4", "5"]])
    assert df.shape == (2, 3)
    assert df.iloc[0, 2] == ""
