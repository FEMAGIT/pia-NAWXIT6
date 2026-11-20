"""Converte i documenti Markdown di docs/ in PDF (reportlab).

Uso:  python docs/genera_pdf.py docs/api.md docs/api-test.md
Supporta: titoli, paragrafi, elenchi, tabelle, blocchi di codice, **grassetto**, *corsivo*, `codice`.
Usa Arial e Courier New di Windows per coprire i caratteri accentati e i simboli tipografici.
"""

import re
import sys
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, ListFlowable, ListItem, Paragraph, Preformatted, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

FONT_DIR = Path('C:/Windows/Fonts')
pdfmetrics.registerFont(TTFont('Corpo', str(FONT_DIR / 'arial.ttf')))
pdfmetrics.registerFont(TTFont('Corpo-B', str(FONT_DIR / 'arialbd.ttf')))
pdfmetrics.registerFont(TTFont('Corpo-I', str(FONT_DIR / 'ariali.ttf')))
pdfmetrics.registerFont(TTFont('Corpo-BI', str(FONT_DIR / 'arialbi.ttf')))
pdfmetrics.registerFont(TTFont('Mono', str(FONT_DIR / 'cour.ttf')))
pdfmetrics.registerFontFamily('Corpo', normal='Corpo', bold='Corpo-B', italic='Corpo-I', boldItalic='Corpo-BI')

BLU = colors.HexColor('#1F3A5F')
GRIGIO = colors.HexColor('#F2F4F7')
BORDO = colors.HexColor('#C9CED6')

STILI = {
    'p': ParagraphStyle('p', fontName='Corpo', fontSize=9.5, leading=13, alignment=TA_LEFT, spaceAfter=5),
    'h1': ParagraphStyle('h1', fontName='Corpo-B', fontSize=20, leading=24, textColor=BLU, spaceAfter=10),
    'h2': ParagraphStyle('h2', fontName='Corpo-B', fontSize=14, leading=18, textColor=BLU, spaceBefore=12,
                         spaceAfter=6),
    'h3': ParagraphStyle('h3', fontName='Corpo-B', fontSize=11, leading=14, textColor=BLU, spaceBefore=8,
                         spaceAfter=4),
    'cella': ParagraphStyle('cella', fontName='Corpo', fontSize=8.5, leading=11),
    'cella_h': ParagraphStyle('cella_h', fontName='Corpo-B', fontSize=8.5, leading=11, textColor=colors.white),
    'codice': ParagraphStyle('codice', fontName='Mono', fontSize=7.8, leading=9.6, backColor=GRIGIO,
                             borderColor=BORDO, borderWidth=0.5, borderPadding=5, spaceBefore=3, spaceAfter=9,
                             leftIndent=5, rightIndent=5),
}


def inline(testo):
    """Markdown inline -> markup reportlab."""
    parti = re.split(r'(`[^`]+`)', testo)
    risultato = []
    for parte in parti:
        if parte.startswith('`') and parte.endswith('`') and len(parte) > 1:
            risultato.append(f'<font name="Mono" size="8.3" color="#8A2D3B">{escape(parte[1:-1])}</font>')
            continue
        parte = escape(parte)
        parte = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', parte)
        parte = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', parte)
        parte = re.sub(r'(?<![*\w])\*([^*\n]+)\*(?![*\w])', r'<i>\1</i>', parte)
        risultato.append(parte)
    return ''.join(risultato)


def celle_tabella(riga):
    riga = riga.strip()
    if riga.startswith('|'):
        riga = riga[1:]
    if riga.endswith('|'):
        riga = riga[:-1]
    # separa su | non preceduti da backslash
    return [c.strip().replace('\\|', '|') for c in re.split(r'(?<!\\)\|', riga)]


def tabella(righe, larghezza):
    intestazione = celle_tabella(righe[0])
    corpo = [celle_tabella(r) for r in righe[2:]]
    n = len(intestazione)
    dati = [[Paragraph(inline(c), STILI['cella_h']) for c in intestazione]]
    for r in corpo:
        r = (r + [''] * n)[:n]
        dati.append([Paragraph(inline(c), STILI['cella']) for c in r])

    # larghezze proporzionali alla lunghezza del testo (con minimi e massimi ragionevoli)
    pesi = [max(8, min(60, max(len(re.sub(r'[`*]', '', riga_[i])) for riga_ in [intestazione] + corpo
                                if i < len(riga_)))) for i in range(n)]
    totale = sum(pesi)
    larghezze = [larghezza * p / totale for p in pesi]
    t = Table(dati, colWidths=larghezze, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLU),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.4, BORDO),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRIGIO]),
        ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    return [t, Spacer(1, 8)]


def codice(righe, larghezza):
    colonne = int(larghezza / (7.8 * 0.6)) - 2  # Courier: ~0.6 em per carattere
    rientro = []
    for riga in righe:
        riga = riga.expandtabs(4)
        if len(riga) <= colonne:
            rientro.append(riga)
            continue
        spazi = len(riga) - len(riga.lstrip())
        rientro.extend(textwrap.wrap(riga, colonne, subsequent_indent=' ' * (spazi + 2),
                                     break_long_words=True, replace_whitespace=False, drop_whitespace=False))
    return Preformatted('\n'.join(rientro), STILI['codice'])


def converti(sorgente: Path, destinazione: Path):
    larghezza = A4[0] - 36 * mm
    righe = sorgente.read_text(encoding='utf-8').splitlines()
    storia, i = [], 0
    titolo = sorgente.stem
    while i < len(righe):
        riga = righe[i]
        if riga.startswith('```'):
            blocco, i = [], i + 1
            while i < len(righe) and not righe[i].startswith('```'):
                blocco.append(righe[i])
                i += 1
            storia.append(codice(blocco, larghezza))
        elif riga.startswith('|') and i + 1 < len(righe) and re.match(r'^\|?\s*:?-{2,}', righe[i + 1]):
            blocco = []
            while i < len(righe) and righe[i].startswith('|'):
                blocco.append(righe[i])
                i += 1
            storia.extend(tabella(blocco, larghezza))
            continue
        elif re.match(r'^#{1,3} ', riga):
            livello = len(riga.split(' ')[0])
            testo = riga[livello + 1:]
            if livello == 1 and titolo == sorgente.stem:
                titolo = testo
            storia.append(Paragraph(inline(testo), STILI[f'h{livello}']))
        elif re.match(r'^\s*([-*]|\d+\.) ', riga):
            ordinato = bool(re.match(r'^\s*\d+\.', riga))
            voci = []
            while i < len(righe) and re.match(r'^\s*([-*]|\d+\.) ', righe[i]):
                voci.append(re.sub(r'^\s*([-*]|\d+\.) ', '', righe[i]))
                i += 1
            storia.append(ListFlowable(
                [ListItem(Paragraph(inline(v), STILI['p']), leftIndent=14) for v in voci],
                bulletType='1' if ordinato else 'bullet', bulletFontName='Corpo', bulletFontSize=8,
                start=1 if ordinato else '•', leftIndent=14))
            continue
        elif riga.strip():
            paragrafo = [riga.strip()]
            i += 1
            while (i < len(righe) and righe[i].strip() and not righe[i].startswith(('#', '```', '|'))
                   and not re.match(r'^\s*([-*]|\d+\.) ', righe[i])):
                paragrafo.append(righe[i].strip())
                i += 1
            storia.append(Paragraph(inline(' '.join(paragrafo)), STILI['p']))
            continue
        i += 1

    def piè_di_pagina(canvas, doc):
        canvas.saveState()
        canvas.setFont('Corpo', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(18 * mm, 10 * mm, titolo)
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f'Pagina {doc.page}')
        canvas.restoreState()

    SimpleDocTemplate(str(destinazione), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                      bottomMargin=18 * mm, title=titolo, author='PIA ICS').build(
        storia, onFirstPage=piè_di_pagina, onLaterPages=piè_di_pagina)


if __name__ == '__main__':
    for percorso in sys.argv[1:]:
        origine = Path(percorso)
        converti(origine, origine.with_suffix('.pdf'))
        print(f'{origine} -> {origine.with_suffix(".pdf")}')
