"""Render the editable consultation brief JSON as three printable A4 pages."""
from pathlib import Path
import json
from xml.sax.saxutils import escape

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'research/consultation-02-brief-2026-10-30.json'
TARGET = ROOT / 'outputs/current/Consultation_02_next_steps_2026-10-30.pdf'


def main():
    if TARGET.exists():
        raise FileExistsError('Refusing to overwrite an existing PDF')
    data = json.loads(SOURCE.read_text(encoding='utf-8'))
    pdfmetrics.registerFont(TTFont('BriefArial', 'C:/Windows/Fonts/arial.ttf'))
    pdfmetrics.registerFont(TTFont('BriefArialBold', 'C:/Windows/Fonts/arialbd.ttf'))
    W, H = A4
    margin = 18 * mm
    width = W - 2 * margin
    ink, blue, gray = '#18252F', '#245A79', '#56636C'
    title = ParagraphStyle('title', fontName='BriefArialBold', fontSize=23, leading=27, textColor=ink)
    sub = ParagraphStyle('sub', fontName='BriefArial', fontSize=10, leading=14, textColor=gray)
    heading = ParagraphStyle('heading', fontName='BriefArialBold', fontSize=12, leading=15, textColor=blue)
    body = ParagraphStyle('body', fontName='BriefArial', fontSize=10.5, leading=14.3, textColor=ink)
    foot = ParagraphStyle('foot', fontName='BriefArial', fontSize=8.5, leading=11, textColor=gray)
    pdf = canvas.Canvas(str(TARGET), pagesize=A4, pageCompression=1)
    pdf.setTitle(data['title'])
    pdf.setAuthor('Diploma design - consultation review')
    occupied = []

    def draw(value, style, y):
        paragraph = Paragraph(escape(value).replace('\n', '<br/>'), style)
        _, height = paragraph.wrap(width, H)
        paragraph.drawOn(pdf, margin, y-height)
        return y-height

    for n, page in enumerate(data['pages'], 1):
        y = H - margin
        y = draw(page['title'], title, y) - 10
        y = draw(page['subtitle'], sub, y) - 22
        for section in page['sections']:
            y = draw(section['heading'], heading, y) - 6
            y = draw(section['body'], body, y) - 17
        if y < 43 * mm:
            raise ValueError(f'Page {n} text is too close to the footer: {y/mm:.1f} mm')
        occupied.append(round(y/mm, 1))
        draw(page['footer'], foot, 30 * mm)
        pdf.setFont('BriefArial', 8.5)
        pdf.setFillColor(gray)
        pdf.drawString(margin, 13 * mm, 'Диплом / Обсуждение 02 / 30.10.2026')
        pdf.drawRightString(W-margin, 13*mm, f'{n} / {len(data["pages"])}')
        pdf.showPage()
    pdf.save()
    print(json.dumps({'pages': len(data['pages']), 'text_bottom_mm': occupied, 'output': str(TARGET)}))


if __name__ == '__main__':
    main()
