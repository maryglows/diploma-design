"""Preserve two source clips and inventory every Git-tracked file in the bundle."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'docs/chat-analogs-complete-2026-11-23-files.json'
VIDEO_DIR=ROOT/'research/analogs/source-videos-2026-11-21'
SOURCE_HEAD='b1a2d8bf498d0c7a5b27fa6c710a38abc7df0925'

def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def archive_videos():
 sources=json.loads((ROOT/'research/analogs/detail-v2-2026-11-21/sources.json').read_text('utf-8'))
 VIDEO_DIR.mkdir(exist_ok=True)
 rows=[]
 for prefix,filename,title in [('fit','fit-official.mp4','FITBENCH FREE'),('pent','pent-official.mp4','PENT. JOANA Reformer')]:
  original=ROOT/'.codex-build/analog-detail-v2'/filename;dest=VIDEO_DIR/filename
  assert original.is_file(),original
  if dest.exists():assert digest(dest)==digest(original),'Existing source clip differs; preserve manual changes.'
  else:shutil.copy2(original,dest)
  assert dest.read_bytes()[4:8]==b'ftyp',filename
  frames=[{'id':k,'path':s['path'],'near_seconds':s['video_seconds']} for k,s in sources.items() if k.startswith(prefix+'-frame-')]
  source=next(s for k,s in sources.items() if k.startswith(prefix+'-frame-'))
  rows.append(dict(title=title,path=dest.relative_to(ROOT).as_posix(),source_url=source['url'],
   product_page=source['page'],bytes=dest.stat().st_size,sha256=digest(dest),selected_frames=frames))
 info={'downloaded_on':'2026-11-21','archived_on':'2026-11-23',
  'description':'Ролики производителей, найденные для фотокарточек v2. Не видео из консультации и не восстановленные пользовательские вложения. Время стоп-кадров приблизительное.',
  'videos':rows}
 (VIDEO_DIR/'sources.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'source_clips':len(rows),'total_bytes':sum(r['bytes'] for r in rows)}))

def staged_files():
 rows=[]
 for raw in git('ls-files','--stage','-z').split(b'\0'):
  if not raw:continue
  header,path=raw.split(b'\t',1);mode,oid,stage=header.decode().split()
  assert stage=='0','Unmerged index entry'
  name=path.decode('utf-8')
  if name!=MANIFEST.relative_to(ROOT).as_posix():rows.append((name,oid))
 return sorted(rows)

def create_manifest():
 # Read normalized Git blobs, not checkout bytes, so hashes survive CRLF conversion.
 proc=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
 rows=[]
 try:
  for name,oid in staged_files():
   proc.stdin.write((oid+'\n').encode());proc.stdin.flush()
   header=proc.stdout.readline().decode().strip().split();assert header[1]=='blob',header
   size=int(header[2]);left=size;h=hashlib.sha256()
   while left:
    chunk=proc.stdout.read(min(left,1024*1024));assert chunk
    h.update(chunk);left-=len(chunk)
   assert proc.stdout.read(1)==b'\n'
   rows.append({'path':name,'bytes':size,'git_blob':oid,'sha256':h.hexdigest()})
 finally:
  proc.stdin.close();proc.wait()
 info={'saved_on':'2026-11-23','repository':'maryglows/diploma-design',
  'branch':git('branch','--show-current').decode().strip(),'source_head':SOURCE_HEAD,
  'hash_basis':'Git blob content after text normalization. Entire tracked project tree; this manifest excludes itself. Temporary .codex-build caches are not deliverables.',
  'file_count':len(rows),'total_bytes':sum(r['bytes'] for r in rows),'files':rows}
 MANIFEST.write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'manifest_files':len(rows),'total_bytes':info['total_bytes']}))

def verify_manifest():
 info=json.loads(MANIFEST.read_text('utf-8'));actual={}
 for raw in git('ls-tree','-r','-z','HEAD').split(b'\0'):
  if not raw:continue
  header,path=raw.split(b'\t',1);actual[path.decode('utf-8')]=header.decode().split()[2]
 expected={r['path']:r['git_blob'] for r in info['files']}
 manifest_name=MANIFEST.relative_to(ROOT).as_posix()
 assert set(actual)==set(expected)|{manifest_name},'Tracked files missing from manifest'
 assert all(actual[p]==oid for p,oid in expected.items()),'Committed content differs from manifest'
 assert not git('status','--porcelain'), 'Working tree has unsaved changes'
 video_info=json.loads((VIDEO_DIR/'sources.json').read_text('utf-8'))
 for r in video_info['videos']:assert digest(ROOT/r['path'])==r['sha256']
 assert set(git('merge-base',SOURCE_HEAD,'HEAD').decode().split())=={SOURCE_HEAD}
 print(json.dumps({'status':'passed','files':len(expected),'clips':len(video_info['videos']),
  'head':git('rev-parse','HEAD').decode().strip(),'source_history_preserved':True}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['archive-videos','manifest','verify']);args=p.parse_args()
 {'archive-videos':archive_videos,'manifest':create_manifest,'verify':verify_manifest}[args.action]()
