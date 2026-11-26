"""Collect public product-page media; preserve source pages and original assets."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
import requests,json,re,hashlib
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.codex-build/analog-detail-v2'
WORK.mkdir(parents=True,exist_ok=True)
PAGES=[
 ('speed','https://www.speediance.com/products/speediance-gym-monster-2'),
 ('speed-eu','https://eu.speediance.com/products/speediance-gym-monster-2'),
 ('solo','https://solofitness.co.uk/products/solo-signature-storage-bench-adjustable'),
 ('solo-workouts','https://solofitness.co.uk/blogs/news'),
 ('tech','https://www.technogym.com/en-US/product/technogym-bench_DGY100.html'),
 ('step','https://www.nohrd.com/uk/nohrd-stepbox/'),
 ('step-media','https://media.nohrd.com/media/images/stepbox/'),
 ('fit','https://fitbench.com/products/fitbench-free'),
 ('fit-exercise','https://fitbench.com/pages/exercise-library'),
 ('wall','https://www.nohrd.com/us/nohrd-wall-compact.html'),
 ('wall-media','https://media.nohrd.com/media/images/nohrd-wall/'),
 ('tonal','https://tonal.com/products/tonal-2'),
 ('cassina','https://una-unless.org/en/work/ottagono-x-cassina---technogym'),
 ('sana','https://tomaskral.ch/projects/sana'),
 ('sana-shop','https://www.beoak.com/sk-sk/products/sana-wallbar-with-bench'),
 ('golden','https://www.red-dot.org/project/integrated-fitness-cabinet-68274'),
 ('atleast','https://www.red-dot.org/de/project/at-least-home-workout-bench-72143'),
 ('kettler','https://kettlersport.com/nl-nl/ergometer/hoi-ride-plus/'),
 ('pent','https://www.pentfitness.com/products/joana-pilates-reformer'),
 ('kilo','https://kilo-home.ru/'),
 ('kenko','https://www.kenkostores.com/en/product-page/aerobic-hanteln-ahorn'),
]

def collect(pair):
 key,url=pair
 try:
  r=requests.get(url,timeout=(10,35),headers={'User-Agent':'Mozilla/5.0'})
  soup=BeautifulSoup(r.text,'html.parser')
  (WORK/f'{key}.html').write_text(r.text,encoding='utf-8')
  media=[]
  for tag in soup.find_all(['img','source','video','a']):
   for attr in ['src','data-src','data-original','poster','href']:
    value=tag.get(attr)
    if value and re.search(r'\.(jpg|jpeg|png|webp|avif|mp4|gif|pdf)(\?|$)',value,re.I):
     media.append(dict(url=urljoin(r.url,value),alt=tag.get('alt',''),tag=tag.name,attr=attr))
  for raw in re.findall(r'(?:https?:)?//[^\s"<>]+?\.(?:mp4|jpg|jpeg|png|webp)(?:\?[^\s"<>]*)?',r.text):
   if '\\' not in raw:media.append(dict(url=urljoin(r.url,raw.replace('&amp;','&')),alt='',tag='inline',attr=''))
  seen=set();media=[m for m in media if not(m['url'] in seen or seen.add(m['url']))]
  links=[dict(text=a.get_text(' ',strip=True)[:100],url=urljoin(r.url,a.get('href',''))) for a in soup.find_all('a',href=True)]
  record=dict(key=key,url=url,final_url=r.url,status=r.status_code,title=soup.title.get_text(strip=True) if soup.title else '',media=media,links=links,text=soup.get_text(' ',strip=True))
  (WORK/f'{key}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
  return dict(key=key,status=r.status_code,images=len(media),title=record['title'])
 except Exception as e:return dict(key=key,error=str(e)[:120])

if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=8) as pool:
  for result in pool.map(collect,PAGES):print(json.dumps(result,ensure_ascii=False),flush=True)
