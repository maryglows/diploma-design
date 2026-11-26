"""Download candidate images for the second, detailed print selection."""
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import requests,json,hashlib,re
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
W=ROOT/'.codex-build/analog-detail-v2';A=W/'assets';A.mkdir(exist_ok=True)
rows=[]
def add(key,url,page,alt=''):
 if not url.startswith('http'):url='https:'+url
 rows.append(dict(key=key,url=url,page=page,alt=alt))

for key in ['speed','solo','fit','tonal','pent']:
 p=W/f'{key}-product.json'
 if not p.exists():continue
 d=json.loads(p.read_text('utf-8'));page={'fit':'https://fitbench.com/products/fitbench-free-naked','speed':'https://www.speediance.com/products/speediance-gym-monster-2','solo':'https://solofitness.co.uk/products/solo-signature-storage-bench-adjustable','tonal':'https://tonal.com/products/tonal-2','pent':'https://www.pentfitness.com/products/joana-pilates-reformer'}[key]
 for i,m in enumerate(d.get('media',[])):
  if m.get('media_type')=='image' and (key!='speed' or i in [4,5,6,7,12,13,14,15]):add(f'{key}-p{i:02}',m['src'],page,m.get('alt') or '')
 # Record official video sources separately for possible real-frame extraction.
 videos=[m for m in d.get('media',[]) if m.get('media_type')=='video']
 if videos:(W/f'{key}-videos.json').write_text(json.dumps(videos,indent=2),encoding='utf-8')

# These exact filenames and full srcset choices were observed in the public GM2 page DOM.
speed_extra=[
 ('orientation','gym_monster_new_user_orientation.jpg?v=1718683620&width=1280','Выбор и подготовка программы'),
 ('plans','2_393a3f2e-0808-48ae-acb9-28b240e4b89b.webp?v=1758781495&width=1280','Библиотека и планы'),
 ('during','3_0a70ce1d-21be-4bd3-b798-d0bc0edccf46.png?v=1726644233&width=1280','Интерфейс во время занятия'),
 ('after','gym_monster_after_training.jpg?v=1718683620&width=1080','Статистика после занятия'),
 ('speaker','20241023-152238.jpg?v=1729668192&width=1280','Аудиосистема'),
 ('detail-a','02dd5badc89ba729a0b107b99d733cf7.png?v=1726643432&width=1280','Узел корпуса'),
 ('detail-b','13010d0b6d12dba7c6b25c7e043069e0_5bace317-94e3-4029-84dd-edce9960ff83.png?v=1726643575&width=1280','Узел корпуса'),
 ('detail-c','20240918-160110.jpg?v=1726646493&width=1280','Узел корпуса'),
 ('rowing','20260713-140416.png?v=1783922797&width=750','Гребля'),
 ('ski','8a09a2376e84dcfff62ff3aaf55f8da0_b2bd629f-0267-4db3-9a32-dc165cf57337.png?v=1774264830&width=750','Лыжная тяга'),
 ('ring','https://cdn.shopify.com/s/files/1/0701/9950/9207/files/20260824-175916.png?v=1787565585','Bluetooth Ring'),
 ('hooks','https://cdn.shopify.com/s/files/1/0701/9950/9207/files/2.0_77d1f71e-eff1-4108-97e7-da1f2d97c1e7.png?v=1787565209','Держатели грифа'),
 ('ankle','https://cdn.shopify.com/s/files/1/0701/9950/9207/files/2_7ea879d2-7dc5-47b7-8314-19d234d3d339.png?v=1787716497','Манжета для ноги'),
]
for key,url,alt in speed_extra:add('speed-'+key,url if url.startswith('http') else 'https://www.speediance.com/cdn/shop/files/'+url,'https://www.speediance.com/products/speediance-gym-monster-2',alt)

for key in ['cassina','sana','sana-shop','solo-trainer','solo-practice','solo-changes','kenko','kilo']:
 d=json.loads((W/f'{key}.json').read_text('utf-8'))
 seen=set();selected=[]
 for m in d['media']:
  u=m['url'];host=urlparse(u).hostname or ''
  if not re.search(r'\.(jpg|jpeg|png|webp)(\?|$)',u,re.I):continue
  if re.search(r'logo|instagram|pinterest|designer|portrait|portret|font|flac|basket|pay|icon|\.svg',u,re.I):continue
  if key=='sana-shop' and '/products/' not in u and 'dimensions' not in u:continue
  if key=='sana' and '/media/pages/projects/sana/' not in u:continue
  if key=='cassina' and '/works/wide/' not in u:continue
  if key.startswith('solo') and '/files/' not in u:continue
  if key=='kilo' and 'static.tildacdn.com' not in u:continue
  if key=='kenko' and ('static.wixstatic.com/media/' not in u):continue
  base=urlparse(u).path.split('/v1/')[0]
  if base in seen:continue
  seen.add(base);selected.append(m)
 for i,m in enumerate(selected[:25]):add(f'{key}-{i:02}',m['url'],d['url'],m['alt'])

# The official media browser exposed these full-image routes after opening 0672.
# Original-route substitution from the thumbnails is verified by image decoding.
bundle=Path('C:/Users/mekae/AppData/Local/Temp/browser-use/assets/669ee63f-c4ab-41fd-9cf6-c6193e280517/manifest.json')
if bundle.exists():
 seen=set()
 for m in json.loads(bundle.read_text('utf-8'))['assets']:
  fn=m['name']
  if fn in seen:continue
  seen.add(fn)
  add('step-'+Path(fn).stem,'https://media.nohrd.com/media/content/images/nohrd-stepbox/ambient/'+fn,'https://media.nohrd.com/media/images/nohrd-stepbox/ambient/',fn)

def fetch(r):
 target=A/(r['key']+'.jpg');meta=A/(r['key']+'.json')
 if target.exists() and meta.exists():return json.loads(meta.read_text('utf-8'))
 try:
  v=requests.get(r['url'],timeout=(12,35));v.raise_for_status();im=Image.open(BytesIO(v.content));im.load();native=im.size
  if min(native)<200:raise ValueError('thumbnail too small')
  im=im.convert('RGB');im.thumbnail((2560,2560),Image.Resampling.LANCZOS)
  im.save(target,'JPEG',quality=95,subsampling=0,optimize=True)
  r.update(path=target.relative_to(ROOT).as_posix(),pixels=list(im.size),native_pixels=list(native),original_sha256=hashlib.sha256(v.content).hexdigest(),saved_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),status='ok')
 except Exception as e:r.update(status='failed',error=str(e)[:150])
 meta.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
 return r

if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=7) as pool:results=list(pool.map(fetch,rows))
 (W/'candidate-images.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
 for prefix in sorted(set(x['key'].split('-')[0] for x in results)):
  items=[x for x in results if x['key'].split('-')[0]==prefix and x['status']=='ok']
  if not items:continue
  sheet=Image.new('RGB',(1200,((len(items)+5)//6)*170),'#eee')
  draw=ImageDraw.Draw(sheet)
  for i,x in enumerate(items):
   im=Image.open(ROOT/x['path']);im.thumbnail((192,138));xx=i%6*200;yy=i//6*170
   sheet.paste(im,(xx+(200-im.width)//2,yy+22));draw.text((xx+3,yy+3),x['key'],fill='black')
  sheet.save(W/f'contact-{prefix}.jpg')
 print(json.dumps(dict(total=len(results),ok=sum(x['status']=='ok' for x in results),failed=[x['key'] for x in results if x['status']!='ok']),ensure_ascii=False))
