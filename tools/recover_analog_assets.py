"""Recover the previous print selection and verify its saved image candidates."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from urllib.parse import urlparse
import hashlib
import json
import zipfile

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'research/analogs/print-2026-11-21'
DEST.mkdir(parents=True, exist_ok=True)

def recover():
    out = DEST / 'recovered-first-pack'
    out.mkdir(exist_ok=True)
    records = []
    with zipfile.ZipFile(ROOT/'outputs/current/Trainer_photos_A4.pptx') as z:
        for name in z.namelist():
            if not name.startswith('ppt/media/'):
                continue
            data = z.read(name)
            target = out / Path(name).name
            if target.exists():
                assert target.read_bytes() == data
            else:
                target.write_bytes(data)
            im = Image.open(BytesIO(data))
            records.append(dict(path=target.relative_to(ROOT).as_posix(), pixels=im.size,
                                sha256=hashlib.sha256(data).hexdigest(),
                                origin='Embedded media from unchanged Trainer_photos_A4.pptx; some images were cropped/converted in the original layout.'))
    catalog = ROOT/'.codex-build/printrefs-1120/Technogym_Bench_inventory_pp08-11.pdf'
    if catalog.exists():
        (out/catalog.name).write_bytes(catalog.read_bytes())
    (out/'manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')

def download(item):
    idx, row = item
    url = row['url']
    rec = dict(candidate=f'C{idx:02}', page=row['site'], image_url=url)
    try:
        response = requests.get(url, timeout=(12,35),headers={'User-Agent':'Mozilla/5.0'})
        response.raise_for_status()
        data = response.content
        im = Image.open(BytesIO(data))
        im.load()
        ext = {'JPEG':'.jpg','PNG':'.png','WEBP':'.webp','AVIF':'.avif'}.get(im.format,'.img')
        path = DEST/'candidates'/f'C{idx:02}{ext}'
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(data)
        rec.update(path=path.relative_to(ROOT).as_posix(),pixels=im.size,bytes=len(data),
                   sha256=hashlib.sha256(data).hexdigest(),status='downloaded',final_url=response.url)
    except Exception as exc:
        rec.update(status='failed',error=str(exc)[:180])
    return rec

if __name__ == '__main__':
    recover()
    rows=json.loads((ROOT/'.codex-build/full-analog-1120/sources.json').read_text('utf-8'))
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(download,enumerate(rows,1)))
    (DEST/'candidates.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    for x in results:
        print(x['candidate'],x['status'],x.get('pixels',x.get('error')))
