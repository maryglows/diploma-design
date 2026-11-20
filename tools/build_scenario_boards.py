"""Build three A3 scenario sheets from editable JSON and unmodified artwork.

ImageGen artwork is retained whole. Captions are separate native text objects.
Writes a PDF plus a geometry manifest consumed by the PowerPoint author.
"""
from pathlib import Path
import argparse
import json
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / '.codex-build/scenarios-2026-10-30'
SOURCE = ROOT / 'research/scenarios-2026-10-30.json'
FINAL = ROOT / 'outputs/current/Scenarios_A3_2026-10-30.pdf'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=FINAL)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--build-dir', type=Path, default=BUILD)
    args = parser.parse_args()
    target = args.output.resolve()
    if target.exists():
        raise FileExistsError('Refusing to overwrite an existing final PDF')
    data = json.loads(args.source.read_text(encoding='utf-8'))
    pdfmetrics.registerFont(TTFont('ScenarioArial', 'C:/Windows/Fonts/arial.ttf'))
    pdfmetrics.registerFont(TTFont('ScenarioArialBold', 'C:/Windows/Fonts/arialbd.ttf'))
    build_dir = args.build_dir.resolve()
    build_dir.mkdir(parents=True, exist_ok=True)
    W, H = landscape(A3)
    pdf = canvas.Canvas(str(target), pagesize=(W, H), pageCompression=1)
    pdf.setTitle('Сценарии использования / три листа А3')
    pdf.setAuthor('Диплом / проектные сценарии')
    ink, teal, muted = '#1C2C36', '#176A70', '#52616B'
    output = {'width_mm': 420, 'height_mm': 297, 'font': 'Arial', 'pages': []}

    def wrap(value, font, size, width_pt):
        result = []
        for paragraph in value.split('\n'):
            line = ''
            for word in paragraph.split():
                candidate = (line + ' ' + word).strip()
                if pdfmetrics.stringWidth(candidate, font, size) <= width_pt:
                    line = candidate
                else:
                    if not line:
                        raise ValueError('Unbreakable word: '+word)
                    result.append(line)
                    line = word
            result.append(line)
        return result

    for number, page in enumerate(data['pages'], 1):
        elements = []

        def text(name, value, x, top, w, max_h, size=10.5, bold=False, color=ink, leading=None):
            font = 'ScenarioArialBold' if bold else 'ScenarioArial'
            lead = leading or size*1.22
            lines = wrap(value, font, size, w*mm)
            needed = len(lines)*lead/mm
            if needed > max_h:
                raise ValueError(f'{page["id"]}/{name} needs {needed:.2f} mm, has {max_h}')
            pdf.setFont(font, size)
            pdf.setFillColor(HexColor(color))
            for i, line in enumerate(lines):
                pdf.drawString(x*mm, H-top*mm-size-i*lead, line)
            elements.append({'kind':'text', 'name':name, 'value':'\n'.join(lines),
                             'x':x,'y':top,'w':w,'h':max_h,'size':size,
                             'bold':bold,'color':color,'leading':lead})

        if data.get('show_service_labels', True):
            text('eyebrow', 'СЦЕНАРИИ ИСПОЛЬЗОВАНИЯ / DIP-010', 12, 7, 350, 5, 8.5, True, teal)
        text('title', page['title'], 12, 13, 396, 13, 24, True)
        text('subtitle', page['subtitle'], 12, 29, 396, 12, 11.3, False, muted)
        image = ROOT / page['artwork']
        with Image.open(image) as im:
            ratio = im.width / im.height
            resolution = list(im.size)
        # Preserve the entire image in its original aspect ratio.
        art_w = 384
        art_h = art_w/ratio
        if not 210 < art_h < 220:
            raise ValueError('Expected a 16:9 storyboard, inspect before placing')
        art_x, art_y = 18, 44
        pdf.drawImage(str(image), art_x*mm, H-(art_y+art_h)*mm, art_w*mm, art_h*mm, mask='auto')
        elements.append({'kind':'image','path':page['artwork'],'x':art_x,'y':art_y,'w':art_w,'h':art_h,'pixels':resolution})
        cw, ch = art_w/3, art_h/2
        for i, step in enumerate(page['steps']):
            col, row = i%3, i//3
            x = art_x + col*cw + 3
            y = art_y + row*ch + ch*.745
            # Caption backgrounds are native white rectangles, not raster edits.
            pdf.setFillColor(HexColor('#FFFFFF'))
            pdf.rect((x-1)*mm,H-(art_y+(row+1)*ch-1)*mm,(cw-4)*mm,(ch*.255-1)*mm,fill=1,stroke=0)
            elements.append({'kind':'rect','x':x-1,'y':art_y+row*ch+ch*.745,'w':cw-4,'h':ch*.255-1,'fill':'#FFFFFF'})
            text(f'step-{i+1}-title', step['title'], x, y+1, cw-7, 6, 11.5, True, teal)
            text(f'step-{i+1}-body', step['text'], x, y+7, cw-7, ch*.255-9, 10.3, False, ink, 12.4)
        for i, note in enumerate(page['notes']):
            x = 12+i*134
            text(f'note-{i+1}-title', note['title'], x, 264, 128, 5, 9.7, True, teal)
            text(f'note-{i+1}-body', note['text'], x, 270, 128, 13, 9.5, False, ink, 11.5)
        if data.get('show_service_labels', True):
            text('footer', 'Проектная гипотеза. Рисунки созданы ИИ. Без масштаба; наблюдений и обмеров нет.', 12, 286, 365, 4, 7.7, False, muted)
            text('page-number', f'{number:02} / 03', 391, 286, 17, 4, 7.7, False, muted)
        output['pages'].append({'id':page['id'],'title':page['title'],'elements':elements})
        pdf.showPage()
    pdf.save()
    (build_dir/'layout.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'pages':len(output['pages']), 'pdf':str(target), 'layout':str(build_dir/'layout.json')}))


if __name__ == '__main__':
    main()
