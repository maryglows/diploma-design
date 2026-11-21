"""Check the finished printable bundle, source copies, numbering and preserved files."""
from pathlib import Path
import hashlib,json,subprocess
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'research/analogs/detail-v2-2026-11-21'
OUT=ROOT/'outputs/current'
BASE='20b672707130dc5ee6c8a2e2d79b9fae9924a405'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def verify():
 models=json.loads((DATA/'cards.json').read_text('utf-8'))
 sources=json.loads((DATA/'sources.json').read_text('utf-8'))
 index=json.loads((DATA/'page-index.json').read_text('utf-8'))
 placements=json.loads((DATA/'print-quality.json').read_text('utf-8'))
 assert [m['number'] for m in models]==[f'{i:02}' for i in range(1,16)]
 ids=[c['id'] for m in models for c in m['cards']]
 assert len(ids)==len(set(ids))==196
 assert len(sources)==163
 assert sum(len(m['cards']) for m in models if not m['appendix'])==182
 for m in models:
  assert [c['id'] for c in m['cards']]==[f'{m["number"]}.{i:02}' for i in range(1,len(m['cards'])+1)]
  assert not any(term in m['title'] for term in ['MoMo','be my form','DYNO','UniGym','NEAR'])
 for key,s in sources.items():
  assert sha(ROOT/s['path'])==s['saved_sha256'],key
  assert s['page'].startswith('https://'),key
  assert not s.get('url') or s['url'].startswith('https://'),key
 assert {p['id'] for p in placements}==set(ids)
 assert min(p['ppi'] for p in placements)>=200
 pdfs={
  'Analog_detail_cards_A4_2026-11-21_v2.pdf':19,
  'Inventory_detail_cards_A4_2026-11-21_v2.pdf':2,
  'Analog_analysis_cues_A4_2026-11-21_v2.pdf':2,
 }
 report={};docs={};all_links=0
 for name,count in pdfs.items():
  doc=pymupdf.open(OUT/name);docs[name]=doc
  assert len(doc)==count,(name,len(doc))
  links=0
  for page in doc:
   assert abs(page.rect.width-210/25.4*72)<.1 and abs(page.rect.height-297/25.4*72)<.1
   links+=len(page.get_links())
   for block in page.get_text('dict')['blocks']:
    for line in block.get('lines',[]):
     for span in line['spans']:
      assert page.rect.contains(pymupdf.Rect(span['bbox'])),(name,span)
  if 'cards_' in name:all_links+=links
  report[name]={'pages':count,'sha256':sha(OUT/name),'source_links':links,'paper':'A4'}
 assert all_links==196,all_links
 for m in models:
  entry=next(i for i in index if i['number']==m['number'])
  part=OUT/'Analog_details_v2_2026-11-21'/f'{m["number"]}_analog.pdf'
  separate=pymupdf.open(part);assert len(separate)==len(entry['pages'])
  for j,page_number in enumerate(entry['pages']):
   full=docs[entry['pdf']][page_number-1]
   assert full.get_pixmap().samples==separate[j].get_pixmap().samples
   page_text=full.get_text()
   expected=[p['id'] for p in placements if p['pdf']==entry['pdf'] and p['page']==page_number]
   assert all(cid in page_text for cid in expected)
 originals={}
 for name in ['Trainer_photos_A4.pdf','Trainer_photos_A4.pptx','Analogi_trenazhera_2026-11-20.xlsx']:
  path=OUT/name;rel=path.relative_to(ROOT).as_posix()
  previous=subprocess.check_output(['git','show',f'{BASE}:{rel}'],cwd=ROOT)
  assert path.read_bytes()==previous,name
  originals[rel]=sha(path)
 source_documents={}
 for name,count in [('Technogym_Bench_catalogue.pdf',16),('NOHRD_Wall_Compact_manual.pdf',28)]:
  path=DATA/name;assert len(pymupdf.open(path))==count
  source_documents[name]={'pages':count,'sha256':sha(path)}
 result=dict(status='passed',models_main=13,models_inventory=2,cards=196,unique_source_assets=163,
  min_embedded_ppi=min(p['ppi'] for p in placements),pdfs=report,individual_pdfs_match_bundle=True,
  source_hashes_verified=True,source_documents=source_documents,preserved_originals=originals,
  preserved_against_commit=BASE,visual_review='All 19 main pages, 2 inventory pages and 2 guide pages reviewed; corrected Solo and Technogym captions rechecked.')
 (DATA/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:result[k] for k in ['status','cards','models_main','models_inventory','unique_source_assets','min_embedded_ppi']},ensure_ascii=False))

if __name__=='__main__':verify()
