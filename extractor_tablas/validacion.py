"""Heurísticas para decidir si una matriz es una tabla real o texto corrido."""
from .config import MIN_COLS, MIN_FILAS, MIN_RELLENO
from .encabezados import contar_filas_encabezado
from .texto import es_numerica


def es_fila_prosa(fila):
    """Fila que parece texto corrido (un párrafo o un título largo) y no datos."""
    llenas = [c for c in fila if c]
    if not llenas:
        return True
    total = sum(len(c) for c in llenas)
    if len(llenas) == 1:
        return total >= 45
    sin_numeros = not any(es_numerica(c) for c in llenas)
    minusculas = sum(c[0].islower() for c in llenas) / len(llenas)
    return sin_numeros and total >= 60 and minusculas >= 0.5


def depurar(matriz):
    """Quita filas/columnas vacías y filas de prosa en los extremos (título, párrafos)."""
    matriz = [f for f in matriz if any(f)]
    if not matriz:
        return []
    ancho = max(len(f) for f in matriz)
    matriz = [f + [""] * (ancho - len(f)) for f in matriz]
    usar = [j for j in range(ancho) if any(f[j] for f in matriz)]
    matriz = [[f[j] for j in usar] for f in matriz]
    while matriz and es_fila_prosa(matriz[0]):
        matriz.pop(0)
    while matriz and es_fila_prosa(matriz[-1]):
        matriz.pop()
    return matriz


def parece_tabla(matriz, origen):
    """
    origen:
      'grilla'  -> detectada por líneas dibujadas (evidencia fuerte)
      'titulo'  -> debajo de un título "Table N" (evidencia fuerte)
      'libre'   -> solo por alineación de texto (evidencia débil, se exige más)
    """
    if len(matriz) < MIN_FILAS or len(matriz[0]) < MIN_COLS:
        return False

    n_enc = contar_filas_encabezado(matriz)
    cuerpo = matriz[n_enc:]
    if len(cuerpo) < MIN_FILAS - 1:
        return False

    celdas = [c for f in cuerpo for c in f]
    llenas = [c for c in celdas if c]
    if not llenas or len(llenas) / len(celdas) < MIN_RELLENO:
        return False

    prop_num = sum(es_numerica(c) for c in llenas) / len(llenas)
    prop_largas = sum(len(c.split()) >= 6 for c in llenas) / len(llenas)
    texto = [c for c in llenas if not es_numerica(c)]
    prop_minus = sum(c[0].islower() for c in texto) / len(texto) if texto else 0.0

    # Señales de prosa: celdas con muchas palabras o fragmentos que empiezan en minúscula
    if prop_largas > 0.25:
        return False
    if prop_minus > 0.4 and prop_num < 0.2:
        return False

    if origen == "libre":
        return len(matriz[0]) >= 3 and len(matriz) >= 4 and prop_num >= 0.35
    return True
