"""Genera PDFs sintéticos que imitan un paper (2 columnas + tablas) para probar el detector."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

PROSA = (
    "N,N-Dimethyltryptamine (N,N-DMT) is a naturally occurring classic psychedelic with "
    "psychoactive properties that are mediated primarily via the serotonergic pathway and "
    "serotonin 2A receptor agonism. Plant-based preparations of ayahuasca contain DMT and "
    "have been used for centuries in ritual settings across the Amazon basin and beyond. "
) * 6

ANCHO, ALTO = A4


def _columnas_de_texto(c, y_inicio, y_fin):
    """Dos columnas de texto corrido, como en un paper."""
    c.setFont("Times-Roman", 9)
    for x in (50, 305):
        lineas = simpleSplit(PROSA, "Times-Roman", 9, 240)
        y = y_inicio
        for linea in lineas:
            if y < y_fin:
                break
            c.drawString(x, y, linea)
            y -= 11


def _titulo(c, x, y, texto):
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x, y, texto)


def _tabla_grilla_encabezado_combinado(c, x, y_top):
    datos = [
        ["Coded units and themes", "Documented in experience, n (%)", ""],
        ["", "All experiences (n = 3778)", "Experiences with no reported concomitant psychoactive substance use (n = 3242)"],
        ["Somatic", "", ""],
        ["Somaesthesias", "1415 (37.5)", "1212 (37.4)"],
        ["Body vibration, buzz, or tingling", "1026 (27.2)", "878 (27.1)"],
        ['Body "high" or euphoria', "209 (5.5)", "174 (5.4)"],
        ['Body "load"', "180 (4.8)", "160 (4.9)"],
    ]
    # Textos largos de la cabecera envueltos en varias líneas
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    est = ParagraphStyle("c", fontName="Times-Roman", fontSize=8, leading=9)
    datos[1][2] = Paragraph(datos[1][2], est)
    t = Table(datos, colWidths=[200, 120, 175])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Times-Roman", 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("SPAN", (1, 0), (2, 0)),
        ("SPAN", (0, 0), (0, 1)),
        ("BACKGROUND", (0, 0), (-1, 1), colors.lightgrey),
    ]))
    _, alto = t.wrapOn(c, 500, 400)
    t.drawOn(c, x, y_top - alto)
    return y_top - alto


def _tabla_booktabs(c, x, y_top):
    """Solo 3 líneas horizontales (arriba, bajo el encabezado, abajo): sin grilla."""
    filas = [
        ["Compound", "Receptor", "Ki (nM)"],
        ["DMT", "5-HT2A", "127 ± 12"],
        ["5-MeO-DMT", "5-HT1A", "3.2 ± 0.4"],
        ["Psilocin", "5-HT2A", "49 ± 6"],
        ["Harmine", "MAO-A", "0.8 ± 0.1"],
    ]
    c.setFont("Times-Roman", 9)
    xs = [x, x + 160, x + 290]
    alto_fila = 14
    y = y_top
    c.setLineWidth(1)
    c.line(x, y + 3, x + 400, y + 3)
    for i, fila in enumerate(filas):
        y -= alto_fila
        for xc, texto in zip(xs, fila):
            c.drawString(xc, y, texto)
        if i == 0:
            c.line(x, y - 4, x + 400, y - 4)
            y -= 4
    c.line(x, y - 4, x + 400, y - 4)
    return y - 4


def _tabla_booktabs_encabezado_combinado(c, x, y_top):
    """Booktabs con un título que abarca dos subcolumnas y cruza el hueco entre ellas."""
    c.setFont("Times-Roman", 9)
    xs = [x, x + 150, x + 200]
    c.setLineWidth(1)
    c.line(x, y_top + 3, x + 300, y_top + 3)
    y = y_top - 14
    c.drawString(xs[1], y, "Binding affinity (nM)")      # abarca Ki e IC50
    y -= 14
    for xc, texto in zip(xs, ["Compound", "Ki", "IC50"]):
        c.drawString(xc, y, texto)
    c.line(x, y - 4, x + 300, y - 4)
    y -= 4
    for fila in [["DMT", "127", "340"], ["Psilocin", "49", "112"], ["Harmine", "0.8", "2.5"]]:
        y -= 14
        for xc, texto in zip(xs, fila):
            c.drawString(xc, y, texto)
    c.line(x, y - 4, x + 300, y - 4)


def crear_pdf(ruta):
    c = canvas.Canvas(ruta, pagesize=A4)

    # Página 1: prosa en 2 columnas + tabla con grilla y encabezado combinado
    _columnas_de_texto(c, ALTO - 60, 520)
    _titulo(c, 50, 490, "Table 1. Coded units and themes in the experience reports.")
    _tabla_grilla_encabezado_combinado(c, 50, 480)
    c.showPage()

    # Página 2: prosa + tabla estilo booktabs (solo líneas horizontales)
    _columnas_de_texto(c, ALTO - 60, 420)
    _titulo(c, 50, 390, "Table 2. Binding affinities of selected compounds.")
    _tabla_booktabs(c, 50, 372)
    c.showPage()

    # Página 3: solo prosa en dos columnas (no debe detectar nada)
    _columnas_de_texto(c, ALTO - 60, 60)
    c.showPage()

    # Página 4: booktabs con encabezado combinado
    _columnas_de_texto(c, ALTO - 60, 420)
    _titulo(c, 50, 390, "Table 3. Affinity by assay type.")
    _tabla_booktabs_encabezado_combinado(c, 50, 372)
    c.showPage()

    c.save()


def crear_pdf_solo_prosa(ruta):
    """PDF sin ninguna tabla: dos columnas de texto corrido."""
    c = canvas.Canvas(ruta, pagesize=A4)
    _columnas_de_texto(c, ALTO - 60, 60)
    c.showPage()
    c.save()
