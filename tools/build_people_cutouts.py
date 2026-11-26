"""Inventory existing raster assets, then impose a reviewed selection on A4.

No network requests or raster retouching. Original files are never overwritten.
Run with --inventory first, review the numbered contact sheets, then --build.
"""
from pathlib import Path
from io import BytesIO
import argparse
import base64
import hashlib
import json
import math
import zipfile

from PIL import Image, ImageDraw, ImageFont, ImageOps
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / '.codex-build' / 'people-cutouts-2026-10-29'
OUT = ROOT / 'outputs' / 'current'
SELECTION = ROOT / 'research' / 'people-cutouts-2026-10-29.json'
STEM = 'People_cutouts_A4_2026-10-29'


def inventory():
    BUILD.mkdir(parents=True, exist_ok=True)
    (BUILD / 'assets').mkdir(exist_ok=True)
    items, by_digest, errors, scanned = [], {}, [], []

    def add(raw, source):
        try:
            im = Image.open(BytesIO(raw))
            im.load()
            if im.width < 80 or im.height < 80:
                return
            rgb = ImageOps.exif_transpose(im).convert('RGB')
            digest = hashlib.sha256(str(rgb.size).encode() + rgb.tobytes()).hexdigest()
            if digest in by_digest:
                by_digest[digest]['sources'].append(source)
                return
            n = len(items) + 1
            asset = BUILD / 'assets' / f'{n:03}.png'
            # Lossless working copy for inspection only; no cropping or enhancement.
            rgb.save(asset)
            item = {'id': n, 'pixel_sha256': digest, 'size': list(rgb.size),
                    'asset': asset.relative_to(ROOT).as_posix(), 'sources': [source]}
            items.append(item)
            by_digest[digest] = item
        except Exception as exc:
            errors.append({'source': source, 'error': str(exc)[:240]})

    for p in sorted((ROOT / 'research').rglob('*')):
        if p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.jp2'):
            add(p.read_bytes(), p.relative_to(ROOT).as_posix())
    for p in sorted((ROOT / 'outputs').rglob('*')):
        if p.name.startswith(STEM):
            continue
        if p.suffix.lower() in ('.pptx', '.docx'):
            scanned.append(p.relative_to(ROOT).as_posix())
            with zipfile.ZipFile(p) as z:
                for name in sorted(z.namelist()):
                    if '/media/' in name and not name.endswith('/'):
                        add(z.read(name), p.relative_to(ROOT).as_posix() + '::' + name)
        elif p.suffix.lower() == '.pdf':
            scanned.append(p.relative_to(ROOT).as_posix())
            try:
                for page_n, page in enumerate(PdfReader(p).pages, 1):
                    for pic in page.images:
                        add(pic.data, f'{p.relative_to(ROOT).as_posix()}::page{page_n}/{pic.name}')
            except Exception as exc:
                errors.append({'source': p.relative_to(ROOT).as_posix(), 'error': str(exc)[:240]})
    (BUILD / 'inventory.json').write_text(json.dumps({'items': items, 'scanned': scanned, 'errors': errors}, ensure_ascii=False, indent=2), encoding='utf-8')
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 14)
    for start in range(0, len(items), 30):
        chunk = items[start:start+30]
        sheet = Image.new('RGB', (1250, math.ceil(len(chunk) / 5) * 195), 'white')
        d = ImageDraw.Draw(sheet)
        for i, it in enumerate(chunk):
            im = Image.open(ROOT / it['asset'])
            im.thumbnail((238, 155))
            x, y = (i % 5) * 250, (i // 5) * 195
            sheet.paste(im, (x + (250-im.width)//2, y))
            label = f"{it['id']:03}  {it['size'][0]}x{it['size'][1]}"
            d.text((x+5, y+158), label, fill='black', font=font)
            d.text((x+5, y+176), it['sources'][0].split('/')[-1][:28], fill='black', font=font)
        sheet.save(BUILD / f'inventory-{start//30+1:02}.jpg')
    print(json.dumps({'unique_rasters': len(items), 'files_scanned': len(scanned), 'errors': len(errors), 'sheets': math.ceil(len(items)/30)}))


def build():
    data = json.loads(SELECTION.read_text(encoding='utf-8'))
    images = data['images']
    # 10 mm printer margins, 6 mm gutters, 2 columns x 3 rows.
    W, H = A4
    margin, gutter = 10*mm, 6*mm
    cell_w, cell_h = (W-2*margin-gutter)/2, (H-2*margin-2*gutter)/3
    pages, positions = [], []
    for k in range(0, len(images), 6):
        batch, page_pos = images[k:k+6], []
        for i, item in enumerate(batch):
            p = ROOT / item['path']
            with Image.open(p) as im:
                iw, ih = ImageOps.exif_transpose(im).size
            # Do not enlarge the smallest source beyond 120 effective DPI.
            scale = min(cell_w / iw, cell_h / ih, 72/120)
            w, h = iw*scale, ih*scale
            x = margin + (i % 2)*(cell_w+gutter) + (cell_w-w)/2
            top = margin + (i // 2)*(cell_h+gutter) + (cell_h-h)/2
            page_pos.append({**item, 'x':x, 'top':top, 'w':w, 'h':h,
                             'effective_dpi': round(iw / (w/72)), 'page':len(pages)+1})
        pages.append(page_pos)
        positions.extend(page_pos)
    pdf_path, html_path = OUT / (STEM+'.pdf'), OUT / (STEM+'.html')
    for p in (pdf_path, html_path):
        if p.exists():
            raise FileExistsError('Refusing to overwrite '+str(p))
    pdf = canvas.Canvas(str(pdf_path), pagesize=A4, pageCompression=1)
    pdf.setTitle('People photos for cutting - A4')
    pdf.setAuthor('Diploma design working materials')
    html = ['<!doctype html><html lang="ru"><meta charset="utf-8"><title>Картинки для вырезания А4</title><style>',
            '@page{size:A4 portrait;margin:0}*{box-sizing:border-box}body{margin:0;background:#ddd}.page{position:relative;width:210mm;height:297mm;margin:6mm auto;background:white;break-after:page;overflow:hidden}.page:last-child{break-after:auto}img{position:absolute;object-fit:contain}@media print{body{background:white}.page{margin:0}}',
            '</style><body>']
    for page in pages:
        html.append('<section class="page">')
        for it in page:
            p = ROOT / it['path']
            pdf.drawImage(ImageReader(str(p)), it['x'], H-it['top']-it['h'], width=it['w'], height=it['h'], mask='auto')
            # Embed originals so the editable HTML is a portable single file.
            mime = 'image/png' if p.suffix.lower() == '.png' else 'image/jpeg'
            b64 = base64.b64encode(p.read_bytes()).decode('ascii')
            values = [it[key]/mm for key in ('x','top','w','h')]
            html.append(f'<img alt="{p.stem}" src="data:{mime};base64,{b64}" style="left:{values[0]:.4f}mm;top:{values[1]:.4f}mm;width:{values[2]:.4f}mm;height:{values[3]:.4f}mm">')
        html.append('</section>')
        pdf.showPage()
    pdf.save()
    html.append('</body></html>')
    html_path.write_text('\n'.join(html), encoding='utf-8')
    (BUILD/'layout.json').write_text(json.dumps({'page_size_mm':[210,297], 'pages':len(pages), 'photos':positions}, ensure_ascii=False, indent=2),encoding='utf-8')
    print(json.dumps({'pages':len(pages),'photos':len(images),'pdf':str(pdf_path),'editable':str(html_path),'min_effective_dpi':min(i['effective_dpi'] for i in positions)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--inventory', action='store_true')
    parser.add_argument('--build', action='store_true')
    args = parser.parse_args()
    if args.inventory:
        inventory()
    if args.build:
        build()
