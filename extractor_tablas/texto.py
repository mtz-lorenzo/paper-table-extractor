"""Utilidades de limpieza y clasificación de texto de celdas."""
import re

_RE_PALABRA = re.compile(r"[^\W\d_]{2,}")  # 2 o más letras seguidas


def limpiar_celda(celda):
    """Colapsa saltos de línea y espacios repetidos; None -> ''."""
    return re.sub(r"\s+", " ", celda).strip() if celda else ""


def es_numerica(celda):
    """True si la celda es mayormente números (ej: '0.45 ± 0.03', 'p<0.05', '12.5%').
    Una etiqueta como 'IC50' o '10 mg' no cuenta: tiene palabras de 2+ letras."""
    sin_espacios = celda.replace(" ", "")
    if not sin_espacios or _RE_PALABRA.search(sin_espacios):
        return False
    digitos = sum(ch.isdigit() for ch in sin_espacios)
    return digitos / len(sin_espacios) >= 0.5


def encabezados_unicos(encabezados):
    """Reemplaza encabezados vacíos por col_N y desambigua los repetidos."""
    vistos, resultado = {}, []
    for i, col in enumerate(encabezados):
        nombre = col or f"col_{i}"
        if nombre in vistos:
            vistos[nombre] += 1
            nombre = f"{nombre}_{vistos[nombre]}"
        else:
            vistos[nombre] = 0
        resultado.append(nombre)
    return resultado
