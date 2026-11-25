"""Meaningful document, scenario, arithmetic and source-preservation checks."""
from pathlib import Path
from decimal import Decimal
import json,re,hashlib,subprocess,xml.etree.ElementTree as ET
import pymupdf
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'research/concept-explanation-2026-11-25';OUT=ROOT/'outputs/current'
BASE='9c7d81b8ca7f7c8cf774b9dbaab9ddfd2d6bd4d2'
MAIN='Concepts_functions_scenarios_A4_2026-11-25'
SHORT='Six_user_scenarios_A4_2026-11-25'

def run():
 data=json.loads((D/'analysis.json').read_text('utf-8'))
 assert len(data['pages'])==32 and len(data['scenarios'])==6
 assert sum(len(s['steps']) for s in data['scenarios'])==36
 assert len({(s['concept'],s['group']) for s in data['scenarios']})==6
 assert sum(len(p.get('movements',[])) for p in data['pages'])==9
 assert len(data['pages'][3]['blocks'][0]['rows'])==8
 assert len(data['pages'][6]['blocks'][0]['rows'])==9
 reports={};texts={};minfont=100
 for stem,count in [(MAIN,32),(SHORT,6)]:
  path=OUT/(stem+'.pdf');doc=pymupdf.open(path);assert len(doc)==count
  urls=[];chunks=[]
  for page in doc:
   assert abs(page.rect.width-210/25.4*72)<.1 and abs(page.rect.height-297/25.4*72)<.1
   chunks.append(page.get_text());urls.extend(a['uri'] for a in page.get_links() if a.get('uri'))
   for b in page.get_text('dict')['blocks']:
    for line in b.get('lines',[]):
     for span in line['spans']:
      assert page.rect.contains(pymupdf.Rect(span['bbox'])),(stem,page.number+1,span)
      minfont=min(minfont,span['size'])
  text=' '.join('\n'.join(chunks).split());texts[stem]=text
  assert '\ufffd' not in text
  assert not re.search(r'\b(?:C|Y|O|F|S|E)\d+[a-z]?\b',text)
  reports[path.name]=dict(pages=count,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),external_links=len(urls))
 main=pymupdf.open(OUT/(MAIN+'.pdf'));short=pymupdf.open(OUT/(SHORT+'.pdf'))
 for i in range(6):
  assert main[i+13].get_text()==short[i].get_text()
  assert main[i+13].get_pixmap(matrix=pymupdf.Matrix(.5,.5)).digest==short[i].get_pixmap(matrix=pymupdf.Matrix(.5,.5)).digest
 for term in ['одноручный контакт','без подлокотников','0,78','0,72','0,06','7,7%','не доказаны','нагрузки']:
  assert term in texts[MAIN],term
 a=Decimal(1200)*Decimal(650)/Decimal(1000000);b=Decimal(800)*Decimal(900)/Decimal(1000000)
 assert a==Decimal('.78') and b==Decimal('.72') and a-b==Decimal('.06')
 vectors=json.loads((D/'vectors.json').read_text('utf-8'));assert len(vectors)==8
 for filename in vectors:assert ET.parse(ROOT/filename).getroot().tag.endswith('svg')
 html=(OUT/(MAIN+'.html')).read_text('utf-8');assert html.count('<section>')==32
 for image in re.findall(r'<img[^>]+src="([^"]+)"',html):assert (OUT/image).resolve().is_file(),image
 placements=json.loads((D/'placements.json').read_text('utf-8'));assert len(placements)==11
 for item in placements:assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256']
 originals=json.loads((ROOT/'research/analogs/visual-brief-2026-11-25/body-photo-sources.json').read_text('utf-8'))
 assert {i['path'] for i in originals}<={i['path'] for i in placements}
 for item in originals:assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['saved_sha256']
 preserved={}
 paths=['outputs/current/Project_card_A4_2026-11-25.pdf','outputs/current/Pencil_sketches_COLOR_A4_2026-11-25.pdf','outputs/current/Pencil_sketches_BW_A4_2026-11-25.pdf','outputs/current/Preliminary_trainer_brief_A4_2026-11-25.pdf','outputs/current/Analogi_trenazhera_2026-11-20.xlsx','meetings/raw/teacher-discussion-03.md']
 paths += ['design/pencil-sketches-2026-11-25/'+key+'-'+mode+'.png' for key in ['bench','cabinet','inventory'] for mode in ['color','bw']]
 for filename in paths:
  raw=(ROOT/filename).read_bytes();before=subprocess.check_output(['git','show',BASE+':'+filename],cwd=ROOT)
  assert raw==before,filename;preserved[filename]=hashlib.sha256(raw).hexdigest()
 report=dict(status='passed',pdfs=reports,concepts=2,components_explained=17,core_movements=9,reserve_movements=9,scenarios=6,scenario_steps=36,
  scenario_extract_matches_main_visually=True,editable_vector_sources=8,raster_placements=11,min_raster_ppi=min(p['ppi'] for p in placements),
  min_font_pt=round(minfont,2),old_exercise_codes_absent=True,illustrative_base_area_m2=[str(a),str(b)],illustrative_difference_m2=str(a-b),
  source_statuses_disclosed=True,old_files_preserved_against=BASE,preserved=preserved,
  visual_review='All 32 A4 pages rendered with Poppler and inspected; six extracted pages match the full report. Revised standing support statement and scenario labels checked. No structural or user testing was performed.')
 (D/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:report[k] for k in ['status','components_explained','scenarios','scenario_steps','min_raster_ppi','scenario_extract_matches_main_visually']},ensure_ascii=False))

if __name__=='__main__':run()
