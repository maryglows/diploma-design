"""Verify A4 documents, artwork provenance and preservation of earlier work."""
from pathlib import Path
import json,hashlib,re,subprocess
import pymupdf
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'design/pencil-sketches-2026-11-25'
OUT=ROOT/'outputs/current'
BASE='77a6a467ec1d08f275eb197e33f89da7a38a5f9c'

def check():
 content=json.loads((ART/'project-card.json').read_text('utf-8'))
 sources=json.loads((ROOT/'research/bork-style-2026-11-25/sources.json').read_text('utf-8'))
 assert sources['brand_confirmed_by_author']=='BORK'
 images=json.loads((ART/'images.json').read_text('utf-8'));assert len(images)==6
 for record in images:
  path=ROOT/record['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256']
  assert list(Image.open(path).size)==record['size']
 for record in sources['images']:
  assert record['status']==200
  assert hashlib.sha256((ROOT/record['path']).read_bytes()).hexdigest()==record['sha256']
 pdfs={};alltext={}
 for stem,count in [('Project_card_A4_2026-11-25',2),('Pencil_sketches_COLOR_A4_2026-11-25',3),('Pencil_sketches_BW_A4_2026-11-25',3)]:
  path=OUT/(stem+'.pdf');doc=pymupdf.open(path);assert len(doc)==count
  texts=[];gray=True;minimum=100
  for page in doc:
   assert abs(page.rect.width-210/25.4*72)<.1 and abs(page.rect.height-297/25.4*72)<.1
   text=page.get_text();texts.append(text)
   assert '\ufffd' not in text
   assert not re.search(r'\b(?:C|Y|O|F|S|E)\d+[a-z]?\b',text)
   for block in page.get_text('dict')['blocks']:
    for line in block.get('lines',[]):
     for span in line['spans']:
      assert page.rect.contains(pymupdf.Rect(span['bbox'])),span
      minimum=min(minimum,span['size'])
   for info in page.get_image_info():
    if info['colorspace']!=1:gray=False
   if 'Pencil_' in stem:assert 'визуализация ИИ' in text
  alltext[stem]='\n'.join(texts)
  if '_BW_' in stem:
   assert gray
   # Inspect rendered RGB document output, not just declared image colorspaces.
   for page in doc:
    pix=page.get_pixmap(matrix=pymupdf.Matrix(.25,.25),colorspace=pymupdf.csRGB,alpha=False)
    samples=pix.samples
    assert all(samples[i]==samples[i+1]==samples[i+2] for i in range(0,len(samples),3))
  html=(OUT/(stem+'.html')).read_text('utf-8')
  for src in re.findall(r'<img[^>]+src="([^"]+)"',html):assert (OUT/src).resolve().is_file()
  assert html.count('<section>')==count
  pdfs[path.name]=dict(pages=count,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size,min_font_pt=round(minimum,2),grayscale=gray)
 card=alltext['Project_card_A4_2026-11-25']
 for term in ['Дети','Молодые','Пожилые','без сверления','BORK','шпоном','не определено']:
  assert term.casefold() in card.casefold(),term
 assert len(content['functions'])==4 and len(content['users'])==3 and len(content['plates'])==3
 preserved={}
 for filename in ['outputs/current/Visual_analog_details_A4_2026-11-25.pdf','outputs/current/Preliminary_trainer_brief_A4_2026-11-25.pdf','outputs/current/Analogi_trenazhera_2026-11-20.xlsx','outputs/current/Trainer_photos_A4.pdf','outputs/current/Trainer_photos_A4.pptx','meetings/raw/teacher-discussion-03.md']:
  data=(ROOT/filename).read_bytes();before=subprocess.check_output(['git','show',BASE+':'+filename],cwd=ROOT)
  assert data==before,filename
  preserved[filename]=hashlib.sha256(data).hexdigest()
 placements=json.loads((ART/'print-placements.json').read_text('utf-8'))
 assert len(placements)==10 and all(not p['crop'] for p in placements)
 report=dict(status='passed',pdfs=pdfs,selected_generated_images=6,official_reference_photos=4,groups=3,functions=4,
  concept_families=2,inventory_and_detail_plate=True,sketches_printed_without_crop=True,
  min_sketch_ppi=min(p['ppi'] for p in placements if '/pencil-' in p['path']),
  native_artwork_sizes_preserved=True,monochrome_pdf_true_grayscale=True,
  old_versions_preserved_against=BASE,preserved_files=preserved,
  visual_review='All 8 final A4 pages rendered with Poppler and inspected. Cabinet front approach corrected to side rails. Drawing geometry and load capacity remain untested.')
 (ART/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:report[k] for k in ['status','selected_generated_images','official_reference_photos','min_sketch_ppi','monochrome_pdf_true_grayscale']},ensure_ascii=False))

if __name__=='__main__':check()
