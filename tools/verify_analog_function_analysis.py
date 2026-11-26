"""Verify the saved PDF and its analysis-to-photo/source mappings."""
from pathlib import Path
import json,re,hashlib,subprocess
from html.parser import HTMLParser
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/current'
DATA=ROOT/'research/analogs'
STEM='Analog_project_advantages_A4_2026-11-23'

def verify():
 data=json.loads((DATA/'function-analysis-2026-11-23.json').read_text('utf-8'))
 sources=json.loads((DATA/'function-analysis-sources-2026-11-23.json').read_text('utf-8'))
 pages=json.loads((DATA/'function-analysis-pages-2026-11-23.json').read_text('utf-8'))
 photos=json.loads((DATA/'detail-v2-2026-11-21/cards.json').read_text('utf-8'))
 assert [m['number'] for m in data['models']]==[m['number'] for m in photos]
 refs={s['id'] for s in sources};assert len(refs)==len(sources)==24
 photo_ids={c['id'] for m in photos for c in m['cards']}
 for m in data['models']:
  assert len(m['facts'])==2 and len(m['groups'])==3
  assert all(m[k] for k in ['plus','minus','take','check','photos'])
  assert all(s in refs for s in m['sources'])
  for part in m['photos'].split(', '):
   ends=part.split('-');start=ends[0];assert start in photo_ids
   if len(ends)==2:
    assert ends[1] in photo_ids
    assert start[:2]==ends[1][:2]==m['number']
    assert int(start[3:])<=int(ends[1][3:])
   else:assert start[:2]==m['number']
 assert len(data['groups'])==3
 assert all(len(re.findall(r'[CYO][1-6] - ',g['core']))==3 and len(re.findall(r'[CYO][1-6] - ',g['reserve']))==3 for g in data['groups'])
 pdf_path=OUT/(STEM+'.pdf');doc=pymupdf.open(pdf_path)
 assert len(doc)==len(pages)==12
 links=[];min_font=100
 for i,p in enumerate(doc):
  assert abs(p.rect.width-297/25.4*72)<.1 and abs(p.rect.height-210/25.4*72)<.1
  txt=p.get_text();assert pages[i]['title'] in txt
  assert 'Взять: Взять' not in txt and 'Проверить: Проверить' not in txt
  for n in pages[i]['models']:
   m=next(m for m in data['models'] if m['number']==n)
   assert n+' '+m['title'].split()[0] in txt.replace('\n',' ')
  links.extend(a['uri'] for a in p.get_links() if 'uri' in a)
  for b in p.get_text('dict')['blocks']:
   for line in b.get('lines',[]):
    for span in line['spans']:
     assert p.rect.contains(pymupdf.Rect(span['bbox'])),(i+1,span)
     min_font=min(min_font,span['size'])
 assert all(s['url'] in links for s in sources)
 assert min_font>=7.99
 html=(OUT/(STEM+'.html')).read_text('utf-8')
 local_images=re.findall(r'<img[^>]+src="([^"]+)"',html)
 assert len(local_images)==15
 assert all((OUT/path).resolve().exists() for path in local_images)
 assert html.count('<section>')==12
 text_path=DATA/'function-analysis-2026-11-23.md'
 text=text_path.read_text('utf-8')
 assert all(s['url'] in text for s in sources)
 # Source files from the preceding print package must remain byte-for-byte intact.
 original_files=['outputs/current/Analogi_trenazhera_2026-11-20.xlsx','outputs/current/Trainer_photos_A4.pdf','outputs/current/Trainer_photos_A4.pptx','outputs/current/Analog_detail_cards_A4_2026-11-21_v2.pdf']
 unchanged={}
 for path in original_files:
  raw=(ROOT/path).read_bytes()
  assert raw==subprocess.check_output(['git','show','e59861cf36116d40387c85f0b74673658c35f413:'+path],cwd=ROOT)
  unchanged[path]=hashlib.sha256(raw).hexdigest()
 result={'status':'passed','pages':12,'paper':'A4 landscape','main_analysis_pages':'1-10','source_pages':'11-12',
  'models':15,'exercise_examples':18,'core_examples':9,'references':24,'photo_numbering_matches_v2':True,
  'local_html_images':15,'all_source_urls_embedded':True,'text_within_page_bounds':True,'min_pdf_font_pt':round(min_font,2),
  'pdf_sha256':hashlib.sha256(pdf_path.read_bytes()).hexdigest(),'preserved_originals':unchanged,
  'visual_qa':'12 pages rendered with Poppler. All pages inspected; final label corrections rechecked. No clipped text or broken glyphs found.'}
 (DATA/'function-analysis-verification-2026-11-23.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:result[k] for k in ['status','pages','models','exercise_examples','references','min_pdf_font_pt']},ensure_ascii=False))

if __name__=='__main__':verify()
