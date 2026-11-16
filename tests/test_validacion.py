from extractor_tablas.validacion import depurar, es_fila_prosa, parece_tabla

# Párrafo de un paper partido en "celdas" por una mala detección (el caso original)
PROSA = [
    ["N, N-Dimethyltryptami", "that are mediated prima", "ne (N, N-DMT) is a na", "rily via the serotonerg", "turally occurring classic p"],
    ["sychedelic with p", "2A (5-HT ) rec 2A", "sychoactive properties", "eptor agonism1. Plant-", "based preparations of"],
    ["ayahuasca contain DMT", "and have been used for", "centuries in ritual", "settings across the", "Amazon basin and beyond"],
]

NUMERICA = [
    ["Group", "N", "Mean (SD)", "p-value"],
    ["Control", "24", "12.4 (3.1)", "0.032"],
    ["DMT 0.5 mg/kg", "22", "15.8 (4.0)", "<0.001"],
    ["DMT 1.0 mg/kg", "23", "18.2 (3.7)", "<0.001"],
]

CUALITATIVA = [
    ["Compound", "Receptor", "Effect"],
    ["DMT", "5-HT2A", "Agonist"],
    ["Harmine", "MAO-A", "Inhibitor"],
    ["5-MeO-DMT", "5-HT1A", "Agonist"],
]


def test_parrafo_partido_nunca_es_tabla():
    for origen in ("grilla", "titulo", "libre"):
        assert not parece_tabla(depurar(PROSA), origen), origen


def test_tabla_numerica_se_acepta_en_todos_los_origenes():
    for origen in ("grilla", "titulo", "libre"):
        assert parece_tabla(depurar(NUMERICA), origen), origen


def test_tabla_cualitativa_solo_con_evidencia_fuerte():
    assert parece_tabla(CUALITATIVA, "titulo")
    assert parece_tabla(CUALITATIVA, "grilla")
    assert not parece_tabla(CUALITATIVA, "libre")  # sin números ni título: se exige más


def test_demasiado_chica_no_es_tabla():
    assert not parece_tabla([["A", "B"], ["1", "2"]], "titulo")  # solo 2 filas
    assert not parece_tabla([["A"], ["1"], ["2"]], "titulo")     # una columna


def test_es_fila_prosa():
    assert es_fila_prosa(["Table 1. A very long caption describing what the table contains", ""])
    assert not es_fila_prosa(["Control", "24", "12.4 (3.1)"])


def test_depurar_quita_titulo_filas_y_columnas_vacias():
    matriz = [
        ["Table 1. A very long caption describing what the table contains in detail", "", ""],
        ["", "", ""],
        ["Group", "N", ""],
        ["A", "1", ""],
        ["B", "2", ""],
    ]
    assert depurar(matriz) == [["Group", "N"], ["A", "1"], ["B", "2"]]
