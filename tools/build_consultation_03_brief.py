"""Printable consultation analysis and ranked next steps from editable JSON."""
from pathlib import Path
import argparse,json
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'research/consultation-03-brief-2026-11-06.json'
STEM='Consultation_03_analysis_priorities_2026-11-06'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=ROOT/'outputs/current');args=ap.parse_args()
    out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True);target=out/(STEM+'.pdf')
    if target.exists():raise FileExistsError('Existing PDF will not be overwritten')
    data=json.loads(SOURCE.read_text(encoding='utf-8'))
    pdfmetrics.registerFont(TTFont('BriefArial','C:/Windows/Fonts/arial.ttf'));pdfmetrics.registerFont(TTFont('BriefArialBold','C:/Windows/Fonts/arialbd.ttf'))
    W,H=A4;margin=18*mm;width=W-2*margin;ink='#203540';teal='#087F80';gray='#61727A'
    styles={
      'title':ParagraphStyle('title',fontName='BriefArialBold',fontSize=23,leading=27,textColor=ink),
      'subtitle':ParagraphStyle('subtitle',fontName='BriefArial',fontSize=10,leading=13.5,textColor=gray),
      'heading':ParagraphStyle('heading',fontName='BriefArialBold',fontSize=11.6,leading=15,textColor=teal),
      'body':ParagraphStyle('body',fontName='BriefArial',fontSize=11.2,leading=15.2,textColor=ink)
    }
    c=canvas.Canvas(str(target),pagesize=A4,pageCompression=1);c.setTitle(data['title']);c.setAuthor('Диплом: разбор консультации 03')
    limits=[]
    def draw(text,style,y):
        p=Paragraph(escape(text).replace('\n','<br/>'),styles[style]);_,h=p.wrap(width,H)
        p.drawOn(c,margin,y-h);return y-h
    for n,page in enumerate(data['pages'],1):
        y=H-margin;y=draw(page['title'],'title',y)-10;y=draw(page['subtitle'],'subtitle',y)-19
        for section in page['sections']:
            y=draw(section['heading'],'heading',y)-5;y=draw(section['body'],'body',y)-14
        if y<29*mm:raise ValueError(f'Page {n} body is too close to footer: {y/mm}')
        limits.append(round(y/mm,1))
        c.setStrokeColor(teal);c.setLineWidth(.4);c.line(margin,21*mm,W-margin,21*mm)
        c.setFont('BriefArial',8);c.setFillColor(gray);c.drawString(margin,16*mm,'Основание: meetings/raw/teacher-discussion-03.md');c.drawRightString(W-margin,16*mm,f'{n} / {len(data["pages"])}')
        c.showPage()
    c.save();print(json.dumps({'pages':len(data['pages']),'text_bottom_mm':limits,'output':str(target)}))

if __name__=='__main__':main()
