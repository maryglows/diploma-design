"""Build the detailed A4 report and six editable vector scenario boards."""
from pathlib import Path
from html import escape
import json,math,hashlib
import pymupdf
from PIL import Image
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from build_project_card_pencil_sketches import Doc

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'research/concept-explanation-2026-11-25'
DESIGN=ROOT/'design/concept-explanation-2026-11-25';DESIGN.mkdir(parents=True,exist_ok=True)
OUT=ROOT/'outputs/current'
data=json.loads((D/'analysis.json').read_text('utf-8'))
STEM='Concepts_functions_scenarios_A4_2026-11-25'
SCENARIO_STEM='Six_user_scenarios_A4_2026-11-25'

class Vector:
 """Millimetre primitives, rendered unchanged to SVG and native PDF objects."""
 def __init__(self,w=190,h=215):self.w=w;self.h=h;self.ops=[]
 def rect(self,x,y,w,h,fill='#FFFFFF',stroke='#B5B3AC',r=0):self.ops.append(('rect',(x,y,w,h,r),fill,stroke))
 def line(self,pts,col='#736E64',width=.4):self.ops.append(('line',(pts,width),None,col))
 def circle(self,x,y,r,fill='#707F81'):self.ops.append(('circle',(x,y,r),fill,fill))
 def text(self,x,y,text,size=8,bold=False,col='#42382F'):
  self.ops.append(('text',(x,y,text,size,bold),col,col))
 def wrap(self,x,y,text,w,size=8.6,bold=False):
  words=text.split();lines=[];line='';font='CardB' if bold else 'CardR'
  for word in words:
   candidate=(line+' '+word).strip()
   if line and pdfmetrics.stringWidth(candidate,font,size)>w*mm:lines.append(line);line=word
   else:line=candidate
  if line:lines.append(line)
  for i,line in enumerate(lines):self.text(x,y+i*size*1.22/mm,line,size,bold)
  return y+len(lines)*size*1.22/mm
 def arrow(self,x1,y1,x2,y2,col='#A86A3D'):
  self.line([(x1,y1),(x2,y2)],col,.55);ang=math.atan2(y2-y1,x2-x1)
  self.line([(x2-2*math.cos(ang-.45),y2-2*math.sin(ang-.45)),(x2,y2),(x2-2*math.cos(ang+.45),y2-2*math.sin(ang+.45))],col,.55)
 def save(self,name):
  items=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}mm" height="{self.h}mm" viewBox="0 0 {self.w} {self.h}"><rect width="100%" height="100%" fill="white"/>']
  for kind,p,fill,stroke in self.ops:
   if kind=='rect':
    x,y,w,h,r=p;items.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="0.25"/>')
   elif kind=='circle':
    x,y,r=p;items.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"/>')
   elif kind=='line':
    pts,lw=p;items.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+f'" fill="none" stroke="{stroke}" stroke-width="{lw}"/>')
   else:
    x,y,text,size,bold=p;items.append(f'<text x="{x}" y="{y}" font-family="Segoe UI,sans-serif" font-size="{size/mm}" font-weight="{700 if bold else 400}" fill="{fill}">{escape(text)}</text>')
  items.append('</svg>');path=DESIGN/name;path.write_text(''.join(items),encoding='utf-8');return path
 def draw(self,doc,x,y):
  c=doc.c;c.saveState();c.translate(x*mm,(297-y)*mm)
  for kind,p,fill,stroke in self.ops:
   c.setStrokeColor(HexColor(stroke));c.setFillColor(HexColor(fill or '#FFFFFF'))
   if kind=='rect':
    xx,yy,w,h,r=p;c.setLineWidth(.25*mm);c.roundRect(xx*mm,-(yy+h)*mm,w*mm,h*mm,r*mm,stroke=1,fill=1)
   elif kind=='circle':
    xx,yy,r=p;c.circle(xx*mm,-yy*mm,r*mm,stroke=0,fill=1)
   elif kind=='line':
    pts,lw=p;c.setLineWidth(lw*mm);path=c.beginPath();path.moveTo(pts[0][0]*mm,-pts[0][1]*mm)
    for xx,yy in pts[1:]:path.lineTo(xx*mm,-yy*mm)
    c.drawPath(path,stroke=1,fill=0)
   else:
    xx,yy,text,size,bold=p;c.setFont('CardB' if bold else 'CardR',size);c.drawString(xx*mm,-yy*mm,text)
  c.restoreState()

def scenario_figure(s):
 v=Vector(h=207)
 for i,step in enumerate(s['steps']):
  col=i%2;row=i//2;x=col*97;y=row*69
  v.rect(x,y,93,66,fill='#FEFDFC',r=1)
  v.text(x+2,y+5,str(i+1)+'. '+step['title'],8.7,True)
  # The floor-plan symbol is explicitly a location icon, not an exercise pose.
  cx=x+21;cy=y+10
  if s['concept']=='bench':
   v.rect(cx-12,cy,25,8,fill='#CDB99C',r=1)
   v.line([(cx-14,cy-1),(cx-14,cy+10)],'#606D6D',1)
   v.text(cx-10,cy+4.8,'корпус',7.2)
   if step['state']=='drawer':v.rect(cx-8,cy+8,11,6,fill='#E7D5BD')
  else:
   v.rect(cx-8,cy,16,6,fill='#CDB99C',r=1)
   v.line([(cx-10,cy-1),(cx-10,cy+15)],'#606D6D',.8)
   v.line([(cx+10,cy-1),(cx+10,cy+15)],'#606D6D',.8)
   v.text(cx-6,cy+4,'корпус',7.2)
   if step['state'] in ('open','seat','pending'):
    v.rect(cx-7,cy+6,14,7,fill='#D8CFBD')
    v.circle(cx-6,cy+12,0.8,'#606D6D');v.circle(cx+6,cy+12,.8,'#606D6D')
  if step['state'] in ('mat','child'):
   v.rect(x+52,y+10,33,13,fill='#DEE6DE',r=1);v.text(x+57,y+18,'панель',7)
   v.circle(x+69,y+15,1.3,'#7D8E92')
   if s['group']=='Дети':v.circle(x+47,y+18,1.3,'#AA7C52')
  elif step['state'] in ('adult','prepare','drawer'):
   v.circle(x+64,y+17,2,'#7D8E92');v.text(x+70,y+18,'человек',7.2);v.arrow(cx+13,cy+5,x+59,y+17)
  elif step['state'] in ('seat','grip'):
   px=cx-19 if step['state']=='grip' else cx;py=cy+11 if step['state']=='grip' else cy+14
   v.circle(px,py,1.8,'#7D8E92');v.text(x+53,y+18,'положение',7.2)
  elif step['state']=='pending':v.text(x+48,y+18,'доработать опоры',7,True,col='#9D593A')
  else:v.text(x+53,y+18,'хранение',7)
  end=v.wrap(x+2,y+29,step['text'],89,size=8.6)
  assert end<y+65,(s['title'],step['title'],end-y)
 return v

def space_figure():
 v=Vector(h=72);v.text(3,5,'Один масштаб оснований, числа только из прежней гипотезы',10,True)
 for xx,title,w,h in [(13,'Скамья',1200,650),(115,'Шкаф',800,900)]:
  sc=.043;v.text(xx,14,title,10,True);v.rect(xx,19,w*sc,h*sc,fill='#EBE3D5')
  v.text(xx,19+h*sc+5,f'{w} × {h} мм',9)
 v.text(13,67,'0,78 м²',10,True);v.text(115,67,'0,72 м²',10,True)
 return v

def mechanics_figure():
 v=Vector(h=72)
 for x,title in [(2,'Посадка'),(67,'Поддержка рукой'),(132,'Открытый ящик')]:v.text(x,5,title,9,True)
 for x in [5,70,135]:
  v.line([(x,57),(x+49,57)],'#736E64',.5);v.rect(x+7,37,30,4,fill='#D8C6AE');v.line([(x+9,41),(x+9,56)],'#606D6D',1);v.line([(x+35,41),(x+35,56)],'#606D6D',1)
 v.arrow(27,12,27,35);v.arrow(14,56,14,45,'#627F7A');v.arrow(40,56,40,45,'#627F7A')
 v.line([(76,56),(76,14)],'#606D6D',1.2);v.arrow(78,16,104,16);v.text(70,66,'хват → рама → пол',8)
 v.rect(164,38,18,5,fill='#E6D4B8');v.arrow(175,23,175,37);v.circle(170,57,1.2,'#9D593A');v.text(133,66,'проверить опрокидывание',7.9)
 v.text(3,66,'сиденье → рама → пол',8)
 return v

def write_md():
 lines=['# Подробное объяснение вариантов / 25.11.2026','',
 'Полный анализ двух собственных эскизов. Факты, требования и проектные гипотезы разделены. Основной список задач остаётся в TASKS.md.','',
 '[Полный PDF, 32 А4](../../outputs/current/'+STEM+'.pdf) · [Сценарии отдельно, 6 А4](../../outputs/current/'+SCENARIO_STEM+'.pdf) · [HTML](../../outputs/current/'+STEM+'.html)','',
 '[Исходные данные и статусы источников](analysis.json) · [Протокол проверки](verification.json) · [Редактируемые векторные схемы](../../design/concept-explanation-2026-11-25/README.md)','',
 'Печать: А4, книжная ориентация, 100%. Отдельный PDF сценариев повторяет страницы 14–19 полного документа и сохраняет их исходную нумерацию. Сборка: `python tools/prepare_concept_explanation.py`, затем `python tools/build_concept_explanation.py`. Проверка: `python tools/verify_concept_explanation.py`. Старые карандашные изображения и фотографии движений не изменены.','']
 for i,p in enumerate(data['pages'],1):
  lines+=['## '+str(i)+'. '+p['title'],'',p['lead'],'']
  for b in p['blocks']:
   if b['type']=='h':lines+=['### '+b['text'],'']
   elif b['type']=='p':lines+=[b['text'],'']
   else:
    lines+=['| '+' | '.join(b['headers'])+' |','| '+' | '.join('---' for _ in b['headers'])+' |']
    lines+=['| '+' | '.join(str(c).replace('|','/') for c in r)+' |' for r in b['rows']];lines+=['']
  for t in p.get('blocks_override',[]):lines+=[t,'']
  for m in p.get('movements',[]):lines+=['### '+m['name'],'',m['need'],'',m['comparison'],'',m['check'],'']
  if p['kind']=='scenario':
   s=p['scenario'];lines += [f"{j}. **{st['title']}.** {st['text']}" for j,st in enumerate(s['steps'],1)];lines+=['',s['note'],'',s['condition'],'']
  if p['kind']=='sources':
   for t,u,status in p['sources']:lines += ['- ['+t+']('+u+'): '+status]
   for t in p.get('tail',[]):lines+=['',t]
   lines+=['']
 (D/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def build():
 doc=Doc(STEM);doc.c.setTitle('Два варианта домашнего тренажёра: функции, упражнения и сценарии')
 doc.c.setAuthor('Дипломный проект: исследовательский разбор')
 log=[];svg_names=[]
 for i,p in enumerate(data['pages'],1):
  doc.start(p['title'],p['lead']);doc.c.bookmarkPage('page'+str(i));doc.c.addOutlineEntry(p['title'],'page'+str(i))
  y=31;kind=p['kind']
  if kind=='anatomy':
   doc.image(ROOT/'design/pencil-sketches-2026-11-25'/(p['concept']+'-color.png'),10,31,87,125)
   yy=32
   for text in p['blocks_override']:yy=doc.text(text,102,yy,98,'small')+4
   y=max(160,yy+3)
   y=doc.text('Найти на рисунке',10,y,190,'sub')+2
   names='; '.join(row[0].lower() for row in p['items'])+'.'
   y=doc.text(names,10,y,190)+5
   doc.text('Рисунок сохранён без изменения. Страница с карандашными видами создана ИИ ранее; здесь она служит визуальным указателем частей. Подробные аргументы и проверки каждой части - на следующем листе.',10,y,190,'small')
  elif kind=='movements':
   for j,m in enumerate(p['movements']):
    top=31+j*74
    yy=doc.text(m['name'],10,top,190,'sub')
    doc.image(ROOT/m['image'],10,top+7,43,47)
    yy=doc.text(m['need'],58,top+7,142,'body',bold='Нужно:')+2
    yy=doc.text(m['comparison'],58,yy,142,'small')+2
    yy=doc.text(m['check'],58,yy,142,'small',bold='Проверить:')
    assert yy<top+70,(p['title'],m['name'],yy-top)
   doc.text('Фотографии из сохранённых первоисточников; пояснения относятся к изделию. Источники и авторство - стр. 31–32. Условий индивидуального допуска и режима занятий этот лист не назначает.',10,256,190,'small')
  elif kind=='scenario':
   s=p['scenario'];v=scenario_figure(s);name=f"scenario-{len(svg_names)+1}-{s['concept']}.svg";path=v.save(name);svg_names.append(path.relative_to(ROOT).as_posix());v.draw(doc,10,31)
   doc.parts.append('<img src="../../'+path.relative_to(ROOT).as_posix()+'" style="width:190mm"/>')
   doc.text('На плане: синяя точка - человек; коричневая - взрослый рядом с ребёнком. Положение условное.',10,239,190,'small')
   y=doc.text(s['note'],10,246,190,'small',bold='Роль изделия:')+2
   doc.text(s['condition'],10,y,190,'small',bold='Условие:')
  elif kind in ('space','mechanics'):
   v=space_figure() if kind=='space' else mechanics_figure();name=kind+'.svg';path=v.save(name);svg_names.append(path.relative_to(ROOT).as_posix());v.draw(doc,10,31)
   doc.parts.append('<img src="../../'+path.relative_to(ROOT).as_posix()+'" style="width:190mm"/>')
   y=108
   for text in p['blocks_override']:y=doc.text(text,10,y,190)+4
  elif kind=='sources':
   for title,url,status in p['sources']:
    y=doc.link(title,url,y);y=doc.text(status,10,y,190,'small')+3
   for text in p.get('tail',[]):y=doc.text(text,10,y+2,190,'small')+2
  else:
   for block in p['blocks']:
    if block['type']=='h':y=doc.text(block['text'],10,y+2,190,'sub')+2
    elif block['type']=='p':y=doc.text(block['text'],10,y,190)+4
    else:y=doc.table(block['headers'],block['rows'],block['widths'] or [190/len(block['headers'])]*len(block['headers']),y,font='small')+5
  log.append(dict(page=i,title=p['title'],kind=kind));doc.finish()
 doc.save()
 full=pymupdf.open(OUT/(STEM+'.pdf'));short=pymupdf.open();short.insert_pdf(full,from_page=13,to_page=18);short.set_metadata({'title':'Шесть сценариев двух вариантов: дети, молодые, пожилые','author':'Дипломный проект'});short.save(OUT/(SCENARIO_STEM+'.pdf'),garbage=4,deflate=True);short.close();full.close()
 write_md()
 (D/'pages.json').write_text(json.dumps(log,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (D/'placements.json').write_text(json.dumps(doc.images,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (D/'vectors.json').write_text(json.dumps(svg_names,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(pages=doc.page,scenarios=6,vector_sources=len(svg_names),raster_placements=len(doc.images)),ensure_ascii=False))

if __name__=='__main__':build()
