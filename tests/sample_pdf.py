"""Generate synthetic PDFs that mimic a paper (2 columns + tables) to test the detector."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

PROSE = (
    "N,N-Dimethyltryptamine (N,N-DMT) is a naturally occurring classic psychedelic with "
    "psychoactive properties that are mediated primarily via the serotonergic pathway and "
    "serotonin 2A receptor agonism. Plant-based preparations of ayahuasca contain DMT and "
    "have been used for centuries in ritual settings across the Amazon basin and beyond. "
) * 6

WIDTH, HEIGHT = A4


def _text_columns(c, y_start, y_end):
    """Two columns of running text, like a paper."""
    c.setFont("Times-Roman", 9)
    for x in (50, 305):
        y = y_start
        for line in simpleSplit(PROSE, "Times-Roman", 9, 240):
            if y < y_end:
                break
            c.drawString(x, y, line)
            y -= 11


def _caption(c, x, y, text, font="Helvetica-Bold"):
    c.setFont(font, 9)
    c.drawString(x, y, text)


def _grid_table_merged_header(c, x, y_top):
    data = [
        ["Coded units and themes", "Documented in experience, n (%)", ""],
        ["", "All experiences (n = 3778)",
         "Experiences with no reported concomitant psychoactive substance use (n = 3242)"],
        ["Somatic", "", ""],
        ["Somaesthesias", "1415 (37.5)", "1212 (37.4)"],
        ["Body vibration, buzz, or tingling", "1026 (27.2)", "878 (27.1)"],
        ['Body "high" or euphoria', "209 (5.5)", "174 (5.4)"],
        ['Body "load"', "180 (4.8)", "160 (4.9)"],
    ]
    style = ParagraphStyle("c", fontName="Times-Roman", fontSize=8, leading=9)
    data[1][2] = Paragraph(data[1][2], style)  # wrapped header text
    t = Table(data, colWidths=[200, 120, 175])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Times-Roman", 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("SPAN", (1, 0), (2, 0)),
        ("SPAN", (0, 0), (0, 1)),
        ("BACKGROUND", (0, 0), (-1, 1), colors.lightgrey),
    ]))
    _, height = t.wrapOn(c, 500, 400)
    t.drawOn(c, x, y_top - height)


def _booktabs_table(c, x, y_top):
    """Only 3 horizontal rules (top, under the header, bottom): no grid."""
    rows = [
        ["Compound", "Receptor", "Ki (nM)"],
        ["DMT", "5-HT2A", "127 ± 12"],
        ["5-MeO-DMT", "5-HT1A", "3.2 ± 0.4"],
        ["Psilocin", "5-HT2A", "49 ± 6"],
        ["Harmine", "MAO-A", "0.8 ± 0.1"],
    ]
    c.setFont("Times-Roman", 9)
    xs = [x, x + 160, x + 290]
    y = y_top
    c.setLineWidth(1)
    c.line(x, y + 3, x + 400, y + 3)
    for i, row in enumerate(rows):
        y -= 14
        for xc, text in zip(xs, row):
            c.drawString(xc, y, text)
        if i == 0:
            c.line(x, y - 4, x + 400, y - 4)
            y -= 4
    c.line(x, y - 4, x + 400, y - 4)


def _booktabs_merged_header(c, x, y_top):
    """Booktabs with a title spanning two subcolumns and crossing the gap between them."""
    c.setFont("Times-Roman", 9)
    xs = [x, x + 150, x + 200]
    c.setLineWidth(1)
    c.line(x, y_top + 3, x + 300, y_top + 3)
    y = y_top - 14
    c.drawString(xs[1], y, "Binding affinity (nM)")      # spans Ki and IC50
    y -= 14
    for xc, text in zip(xs, ["Compound", "Ki", "IC50"]):
        c.drawString(xc, y, text)
    c.line(x, y - 4, x + 300, y - 4)
    y -= 4
    for row in [["DMT", "127", "340"], ["Psilocin", "49", "112"], ["Harmine", "0.8", "2.5"]]:
        y -= 14
        for xc, text in zip(xs, row):
            c.drawString(xc, y, text)
    c.line(x, y - 4, x + 300, y - 4)


def create_pdf(path):
    c = canvas.Canvas(path, pagesize=A4)

    # Page 1: two columns of prose + a grid table with a merged header
    _text_columns(c, HEIGHT - 60, 520)
    _caption(c, 50, 490, "Table 1. Coded units and themes in the experience reports.")
    _grid_table_merged_header(c, 50, 480)
    c.showPage()

    # Page 2: prose + a booktabs-style table (horizontal rules only)
    _text_columns(c, HEIGHT - 60, 420)
    _caption(c, 50, 390, "Table 2. Binding affinities of selected compounds.")
    _booktabs_table(c, 50, 372)
    c.showPage()

    # Page 3: prose only, in two columns (must detect nothing)
    _text_columns(c, HEIGHT - 60, 60)
    c.showPage()

    # Page 4: booktabs with a merged header
    _text_columns(c, HEIGHT - 60, 420)
    _caption(c, 50, 390, "Table 3. Affinity by assay type.")
    _booktabs_merged_header(c, 50, 372)
    c.showPage()

    c.save()


def create_prose_only_pdf(path):
    """A PDF with no tables at all: two columns of running text."""
    c = canvas.Canvas(path, pagesize=A4)
    _text_columns(c, HEIGHT - 60, 60)
    c.showPage()
    c.save()


def create_cjk_pdf(path):
    """Japanese (page 1) and Korean (page 2) pages: running text + a booktabs-style table.
    Uses reportlab's built-in CID fonts, so no font files are needed."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont

    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))        # Japanese
    pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))  # Korean

    def booktabs(c, font, y_top, rows):
        xs = [50, 200, 330]
        c.setFont(font, 9)
        c.setLineWidth(1)
        y = y_top
        c.line(50, y + 3, 450, y + 3)
        for i, row in enumerate(rows):
            y -= 14
            for xc, text in zip(xs, row):
                c.drawString(xc, y, text)
            if i == 0:
                c.line(50, y - 4, 450, y - 4)
                y -= 4
        c.line(50, y - 4, 450, y - 4)

    pages = [
        ("HeiseiMin-W3",
         "本研究ではジメチルトリプタミンのセロトニン受容体に対する作用を詳細に検討した結果を報告する。",
         "表1　結合親和性の比較",
         [["化合物", "受容体", "Ki (nM)"], ["DMT", "5-HT2A", "127 ± 12"],
          ["ハルミン", "MAO-A", "0.8 ± 0.1"], ["シロシン", "5-HT2A", "49 ± 6"]]),
        ("HYSMyeongJo-Medium",
         "본 연구에서는 디메틸트립타민이 세로토닌 수용체에 미치는 영향을 자세히 조사한 결과를 보고한다.",
         "표 1. 결합 친화도 비교",
         [["화합물", "수용체", "Ki (nM)"], ["DMT", "5-HT2A", "127 ± 12"],
          ["하르민", "MAO-A", "0.8 ± 0.1"], ["실로신", "5-HT2A", "49 ± 6"]]),
    ]
    c = canvas.Canvas(path, pagesize=A4)
    for font, paragraph, caption, rows in pages:
        c.setFont(font, 9)
        for i in range(18):
            c.drawString(50, 780 - i * 11, paragraph)
        c.setFont(font, 10)
        c.drawString(50, 560, caption)
        booktabs(c, font, 545, rows)
        c.showPage()
    c.save()


def _draw_words(c, x, y, text, font="Helvetica", size=8):
    """Draw text word by word with NO space characters, only a positional gap, as many
    publisher PDFs do. The gap (0.25 em) is smaller than pdfplumber's default tolerance."""
    c.setFont(font, size)
    for word in text.split(" "):
        c.drawString(x, y, word)
        x += c.stringWidth(word, font, size) + 0.25 * size


def _curve_rule(c, x0, x1, y, height=0.4):
    """A thin filled path (a 'curve' for pdfplumber), like the rules in Nature tables."""
    p = c.beginPath()
    p.moveTo(x0, y)
    p.lineTo(x1, y)
    p.lineTo(x1, y + height)
    p.curveTo(x1, y + height, x0, y + height, x0, y + height)
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def create_publisher_style_pdf(path):
    """One page that mimics a publisher PDF: positional word spacing, a table whose rules
    are drawn as curves (one stroke per column) and, below it, two figure grids without a
    'Table N' caption (a symbol heatmap and a 2-column mini table) that must be ignored."""
    c = canvas.Canvas(path, pagesize=A4)
    _text_columns(c, HEIGHT - 60, 520)

    edges = [50, 210, 350, 455, 545]  # one stroke per column
    xs = [50, 215, 355, 460]

    def rule(y):
        for a, b in zip(edges, edges[1:]):
            _curve_rule(c, a, b, y)

    rule(500)
    _draw_words(c, 50, 485, "Table 1 | Notable disease-cell type associations", "Helvetica-Bold", 8)
    rule(473)
    rows = [
        ["Disease/trait", "Cell type", "Data source", "Effect size (SE)"],
        ["Insomnia", "Photoreceptor cells", "Fetal brain scATAC", "0.81 (0.23)"],
        ["Bipolar disorder", "Parvalbumin interneurons", "Adult brain scATAC", "1.23 (0.28)"],
        ["Intelligence", "Corticofugal projection neurons", "Adult brain scRNA", "0.76 (0.14)"],
        ["Reaction time", "Ganglion cells", "Fetal brain scRNA", "0.45 (0.14)"],
    ]
    y = 460
    for i, row in enumerate(rows):
        for x, text in zip(xs, row):
            _draw_words(c, x, y, text)
        if i == 0:
            rule(y - 6)
            y -= 6
        y -= 13
    rule(y - 2)

    # Figure grids WITHOUT a table caption (must not be extracted)
    heat = [["*" if (i * 3 + j) % 4 == 0 else "" for j in range(8)] for i in range(8)]
    t = Table(heat, colWidths=[18] * 8, rowHeights=[12] * 8)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                           ("FONT", (0, 0), (-1, -1), "Helvetica", 8)]))
    _, h = t.wrapOn(c, 200, 200)
    t.drawOn(c, 60, 260 - h + 60)

    mini = Table([["Gene 1", "0.02"], ["...", "..."], ["Gene 20k", "0.005"]], colWidths=[70, 50])
    mini.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                              ("FONT", (0, 0), (-1, -1), "Helvetica", 8)]))
    _, h = mini.wrapOn(c, 200, 100)
    mini.drawOn(c, 300, 200)

    c.showPage()
    c.save()
