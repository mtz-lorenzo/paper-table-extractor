from extractor_tablas.texto import encabezados_unicos, es_numerica, limpiar_celda


def test_es_numerica_acepta_valores_tipicos_de_papers():
    for celda in ["12.5%", "0.45 ± 0.03", "p<0.05", "1415 (37.5)", "n=3778", "<0.001"]:
        assert es_numerica(celda), celda


def test_es_numerica_rechaza_texto_y_etiquetas():
    for celda in ["Somatic", "All experiences (n = 3778)", "IC50", "10 mg", ""]:
        assert not es_numerica(celda), celda


def test_limpiar_celda_colapsa_saltos_y_espacios():
    assert limpiar_celda("  Body\nvibration   buzz ") == "Body vibration buzz"
    assert limpiar_celda(None) == ""


def test_encabezados_unicos_reemplaza_vacios_y_desambigua():
    assert encabezados_unicos(["A", "", "A", "A"]) == ["A", "col_1", "A_1", "A_2"]
