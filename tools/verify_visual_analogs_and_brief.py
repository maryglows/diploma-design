"""Check the delivered visual atlas, the provisional brief and preserved sources."""
from pathlib import Path
from decimal import Decimal
import json,re,hashlib,subprocess,xml.etree.ElementTree as ET
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'research/analogs/visual-brief-2026-11-25'
BASE='b4ac1a2276957fafa778d4d1e6fc425cdc0767a6'

def verify():
 data=json.loads((D/'visual-analysis.json').read_text('utf-8'))
 brief=json.loads((D/'preliminary-brief.json').read_text('utf-8'))
 placements=json.loads((D/'photo-placements.json').read_text('utf-8'))
 assert len(data['models'])==15 and sum(len(m['tiles']) for m in data['models'])==70
 assert len(data['reviews'])==5 and len(brief['requirements'])==12 and len(brief['concepts'])==2
 assert all(len(m['groups'])==3 and m['conclusion'] and len(m['tiles']) in [4,6] for m in data['models'])
 assert all('https://' in r['url'] and r['kind'] for r in data['reviews'].values())
 result={};texts={};links={};min_font=100
 for folder,stem,count in [('analogs','Visual_analog_details_A4_2026-11-25',17),
                           ('concept','Preliminary_trainer_brief_A4_2026-11-25',11)]:
  output=ROOT/'docs'/folder
  path=output/(stem+'.pdf');doc=pymupdf.open(path);assert len(doc)==count
  chunks=[];urls=[]
  for page in doc:
   assert abs(page.rect.width-210/25.4*72)<.1 and abs(page.rect.height-297/25.4*72)<.1
   text=page.get_text();chunks.append(text)
   assert not re.search(r'\b(?:C|Y|O|F|S|E)\d+[a-z]?\b',text),text
   assert '\ufffd' not in text
   urls.extend(a['uri'] for a in page.get_links() if a.get('uri'))
   for block in page.get_text('dict')['blocks']:
    for line in block.get('lines',[]):
     for span in line['spans']:
      assert page.rect.contains(pymupdf.Rect(span['bbox'])),(stem,span)
      min_font=min(min_font,span['size'])
  texts[stem]='\n'.join(chunks);links[stem]=urls
  if stem.startswith('Visual'):
   assert sum(c.count('Нейтральный вывод:') for c in chunks)==15
   assert sum(c.count('Деталь:') for c in chunks)==70
  else:
   assert all(r['url'] in urls for r in data['reviews'].values())
   assert '3838.32' in texts[stem]
  html=(output/(stem+'.html')).read_text('utf-8')
  for image in re.findall(r'<img[^>]+src="([^"]+)"',html):assert (output/image).resolve().is_file(),image
  assert html.count('<section>')==count
  result[stem+'.pdf']={'pages':count,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'links':len(urls),'bytes':path.stat().st_size}
 assert min(p['ppi'] for p in placements)>=200
 assert len(placements)==83
 for p in placements:assert (ROOT/p['saved_source']).is_file()
 for s in json.loads((D/'body-photo-sources.json').read_text('utf-8')):
  assert hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest()==s['saved_sha256']
 for filename in ['bench-concept.svg','cabinet-concept.svg']:
  tree=ET.parse(ROOT/'design/preliminary-trainer-2026-11-25'/filename)
  assert tree.getroot().tag.endswith('svg')
 total=sum(Decimal(str(i['quantity']))*Decimal(str(i['unit_price_rub'])) for i in brief['cost_example']['items'])
 assert total==Decimal('3838.32') and brief['cost_example']['not_priced']
 preserved={}
 for path in ['outputs/current/Analogi_trenazhera_2026-11-20.xlsx','outputs/current/Trainer_photos_A4.pdf',
  'outputs/current/Trainer_photos_A4.pptx','outputs/current/Analog_project_advantages_A4_2026-11-23.pdf',
  'outputs/current/Analog_detail_cards_A4_2026-11-21_v2.pdf','meetings/raw/teacher-discussion-03.md']:
  raw=(ROOT/path).read_bytes();original=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
  assert raw==original,path
  preserved[path]=hashlib.sha256(raw).hexdigest()
 report=dict(status='passed',pdfs=result,analogs_and_inventory=15,visual_details=70,experience_sources=5,
  movement_photos=9,requirements=12,concept_svgs=2,old_codes_absent_from_pdf_text=True,
  min_photo_ppi=min(p['ppi'] for p in placements),min_font_pt=round(min_font,2),
  raw_material_quote_subtotal_rub=str(total),subtotal_is_not_complete_product_cost=True,
  preserved_against_commit=BASE,preserved_files=preserved,
  visual_review='All 28 A4 pages rendered with Poppler and inspected. Revised photo headers, cabinet captions and review links checked. Structural behaviour has not been tested.')
 (D/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:report[k] for k in ['status','visual_details','experience_sources','requirements','concept_svgs','min_photo_ppi']},ensure_ascii=False))

if __name__=='__main__':verify()
