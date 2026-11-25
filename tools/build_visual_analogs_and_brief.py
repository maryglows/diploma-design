"""Create a photo-led analog atlas and a provisional sketch brief, with plain labels."""
from pathlib import Path
from io import BytesIO
from html import escape
from decimal import Decimal
import json,re,hashlib,math
from PIL import Image
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor,white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Table,TableStyle

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'research/analogs/visual-brief-2026-11-25';OUT=ROOT/'outputs/current'
DESIGN=ROOT/'design/preliminary-trainer-2026-11-25';DESIGN.mkdir(parents=True,exist_ok=True)
WORK=ROOT/'.codex-build/visual-brief-2026-11-25';WORK.mkdir(parents=True,exist_ok=True)
data=json.loads((D/'visual-analysis.json').read_text('utf-8'))
brief=json.loads((D/'preliminary-brief.json').read_text('utf-8'))
assets=json.loads((ROOT/'research/analogs/detail-v2-2026-11-21/sources.json').read_text('utf-8'))
BODY=[
 ('Дети',[('child-6.jpg','Рука и противоположная нога','https://www.nhft.nhs.uk/childrens-ot/'),('child-5.jpg','Дотянуться до мягкого предмета','https://www.nhft.nhs.uk/childrens-ot/'),('child-4.jpg','Поднять таз лёжа','https://www.nhft.nhs.uk/childrens-ot/')],
  'Нужны покрытие под ладонями, коленями и спиной, свободное вытягивание и место взрослого. В нашем изделии используются отдельная панель и лёгкое хранение; высокая скамья этим действиям не требуется.'),
 ('Молодые взрослые',[('youth-pushup.jpg','Отжаться с коленей','https://www.acefitness.org/resources/everyone/blog/5241/4-upper-body-movements-for-beginners/'),('youth-goblet-lowered.jpg','Присесть с гантелью','https://www.acefitness.org/resources/everyone/exercise-library/362/goblet-squat/'),('youth-rdl-dumbbells.jpg','Наклониться с гантелями','https://www.kathrynalexander.com/resources/exercise-library-1/legs-and-glutes/')],
  'Нужны панель и доступ к свободным весам. Корпус и открытые детали остаются вне движения головы, коленей, таза и гантелей. Взять предмет должно быть возможно без переноса всей скамьи.'),
 ('Пожилые',[('../board-1/nhs-sit-to-stand.jpg','Сесть и встать','https://www.nhs.uk/live-well/exercise/strength-exercises/'),('older-calf.jpg','Поднять пятки у опоры','https://www.nhs.uk/live-well/exercise/strength-exercises/'),('older-twist.jpg','Повернуть корпус сидя','https://www.nhs.uk/live-well/exercise/sitting-exercises/')],
  'Нужны подобранное сиденье и неподвижная поддержка рукой. На первом макете проверяются стопы, подход, движение локтей и высота хвата. Нагрузка на хват проходит через собственную раму в пол.')
]
body_sources=[]
for _,pics,_ in BODY:
 for filename,label,page in pics:
  path=(ROOT/'research/assets/age-groups'/filename).resolve();key='body-'+path.stem
  record=dict(path=path.relative_to(ROOT).as_posix(),page=page,label=label,saved_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
  assets[key]=record;body_sources.append(record)
(D/'body-photo-sources.json').write_text(json.dumps(body_sources,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for n,f in [('R','segoeui.ttf'),('B','segoeuib.ttf')]:pdfmetrics.registerFont(TTFont(n,str(Path('C:/Windows/Fonts')/f)))
pdfmetrics.registerFontFamily('R',normal='R',bold='B',italic='R',boldItalic='B')
styles={
 'body':ParagraphStyle('body',fontName='R',fontSize=9.5,leading=12.3,spaceAfter=4,textColor=HexColor('#273A34')),
 'small':ParagraphStyle('small',fontName='R',fontSize=8.3,leading=10.4,spaceAfter=3,textColor=HexColor('#4D6259')),
 'tile':ParagraphStyle('tile',fontName='R',fontSize=9.2,leading=11.3,textColor=HexColor('#273A34')),
 'head':ParagraphStyle('head',fontName='B',fontSize=9.4,leading=11.5,textColor=white),
 'sub':ParagraphStyle('sub',fontName='B',fontSize=11.3,leading=14,spaceAfter=5,textColor=HexColor('#244F3D'))
}
PAGELOG=[];PLACEMENTS=[]

def p(text,style='body',bold=None):
 s=escape(text)
 if bold:s='<b>'+escape(bold)+'</b> '+s
 return Paragraph(s,styles[style])

class Document:
 def __init__(self,stem):
  self.stem=stem;self.c=Canvas(str(OUT/(stem+'.pdf')),pagesize=(210*mm,297*mm),pageCompression=1)
  self.c.setTitle('Детали аналогов и предварительное задание на эскиз' if 'Visual' in stem else 'Предварительное задание на эскиз домашнего тренажёра')
  self.html=[];self.pages=0;self.current=[]
 def begin(self,title,subtitle):
  self.pages+=1;self.title=title;self.current=['<section><h1>'+escape(title)+'</h1><p class="subtitle">'+escape(subtitle)+'</p>']
  self.c.setFillColor(HexColor('#244F3D'));self.c.setFont('B',16)
  assert pdfmetrics.stringWidth(title,'B',16)<190*mm,title
  self.c.drawString(10*mm,282*mm,title)
  self.text(subtitle,10,21,190,'small')
  self.c.bookmarkPage('p'+str(self.pages));self.c.addOutlineEntry(title,'p'+str(self.pages))
 def text(self,text,x,y,w,style='body',bold=None,html=True):
  obj=p(text,style,bold);_,h=obj.wrap(w*mm,270*mm)
  assert y+h/mm<=280,(self.title,text,y+h/mm)
  obj.drawOn(self.c,x*mm,(297-y)*mm-h)
  if html:self.current.append('<p>'+('<b>'+escape(bold)+'</b> ' if bold else '')+escape(text)+'</p>')
  return y+h/mm
 def links(self,items,y):
  x=10
  for title,url in items:
   label=title
   o=Paragraph('<link href="'+escape(url,quote=True)+'" color="#315E48">'+escape(label)+'</link>',styles['small'])
   _,h=o.wrap(190*mm,40*mm);assert y+h/mm<281
   o.drawOn(self.c,x*mm,(297-y)*mm-h);y+=h/mm+1.2
   self.current.append('<p class="source"><a href="'+escape(url)+'">'+escape(label)+'</a></p>')
  return y
 def table(self,headers,rows,widths,y=34,font='body'):
  cells=[[p(h,'head') for h in headers]]
  for row in rows:cells.append([p(str(c),font) for c in row])
  t=Table(cells,colWidths=[w*mm for w in widths]);t.setStyle(TableStyle([
   ('BACKGROUND',(0,0),(-1,0),HexColor('#315E48')),('VALIGN',(0,0),(-1,-1),'TOP'),
   ('GRID',(0,0),(-1,-1),.35,HexColor('#C8D2CC')),
   ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
   ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
   ('ROWBACKGROUNDS',(0,1),(-1,-1),[white,HexColor('#F3F6F3')])]))
  _,h=t.wrap(190*mm,260*mm);assert y+h/mm<=280,('table overflow',self.title,h/mm,y)
  t.drawOn(self.c,10*mm,(297-y)*mm-h)
  self.current.append('<table><tr>'+''.join('<th>'+escape(h)+'</th>' for h in headers)+'</tr>'+''.join('<tr>'+''.join('<td>'+escape(str(c))+'</td>' for c in r)+'</tr>' for r in rows)+'</table>')
  return y+h/mm
 def photo(self,asset,crop,x,y,w,h,label=None):
  s=assets[asset];path=ROOT/s['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==s['saved_sha256']
  im=Image.open(path).convert('RGB')
  if crop:im=im.crop(tuple(round(v*(im.width if i%2==0 else im.height)) for i,v in enumerate(crop)))
  sc=min(w/im.width,h/im.height,25.4/200);pw,ph=im.width*sc,im.height*sc
  px=x+(w-pw)/2;py=y+(h-ph)/2
  im.thumbnail((round(pw/25.4*400),round(ph/25.4*400)),Image.Resampling.LANCZOS)
  b=BytesIO();im.save(b,'JPEG',quality=93,subsampling=0)
  from reportlab.lib.utils import ImageReader
  self.c.drawImage(ImageReader(BytesIO(b.getvalue())),px*mm,(297-py-ph)*mm,pw*mm,ph*mm)
  self.c.linkURL(s['page'],(px*mm,(297-py-ph)*mm,(px+pw)*mm,(297-py)*mm),relative=0)
  PLACEMENTS.append(dict(pdf=self.stem+'.pdf',page=self.pages,asset=asset,crop=crop,
    saved_source=s['path'],ppi=round(im.width*25.4/pw),label=label))
  return s
 def finish(self):
  self.c.setFont('R',7.6);self.c.setFillColor(HexColor('#53675D'))
  self.c.drawString(10*mm,7*mm,'25.11.2026   А4, 100%   Фотографии источников и проектные выводы различены')
  self.c.drawRightString(200*mm,7*mm,str(self.pages));self.c.showPage()
  self.current.append('</section>');self.html.append(''.join(self.current))
  PAGELOG.append({'pdf':self.stem+'.pdf','page':self.pages,'title':self.title})
 def save(self):
  self.c.save()
  css='''@page{size:A4;margin:10mm}*{box-sizing:border-box}body{font:9.5pt/1.3 "Segoe UI",sans-serif;background:#e0e5e0;color:#273a34}section{background:white;width:210mm;min-height:297mm;padding:10mm;margin:5mm auto;break-after:page}h1{color:#244f3d;font-size:16pt;margin:0 0 3mm}h2{color:#244f3d;font-size:11pt}p{margin:1.5mm 0}.subtitle,.source{font-size:8.3pt;color:#4d6259}a{color:#315e48}.grid{display:grid;grid-template-columns:1fr 1fr;gap:3mm}.tile{border:1px solid #c8d2cc;padding:2mm}.tile img{display:block;max-width:100%;object-fit:contain;margin:auto}.tile h2{font-size:9.5pt;margin:1mm 0}.plus{color:#315e48}.minus{color:#81592d}table{border-collapse:collapse;table-layout:fixed;width:100%;margin:3mm 0}td,th{border:.4pt solid #c8d2cc;padding:2mm;vertical-align:top;text-align:left}th{background:#315e48;color:white}tr:nth-child(odd){background:#f3f6f3}.concept{width:100%;max-height:115mm}@media print{body{margin:0;background:white}section{width:190mm;min-height:277mm;padding:0;margin:0}}'''
  (OUT/(self.stem+'.html')).write_text('<!doctype html><meta charset="utf-8"><title>'+self.stem+'</title><style>'+css+'</style>'+''.join(self.html),encoding='utf-8')

class Figure:
 """A shared primitive list drawn both as editable SVG and as PDF vectors."""
 def __init__(self,w=760,h=440):self.w=w;self.h=h;self.items=[]
 def poly(self,points,fill,stroke='#50635b',width=1):self.items.append(('poly',points,fill,stroke,width))
 def line(self,points,color='#50635b',width=1.3):self.items.append(('line',points,None,color,width))
 def text(self,x,y,text,size=15,color='#273a34'):self.items.append(('text',(x,y,text,size),None,color,0))
 def save(self,name):
  a=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}"><rect width="100%" height="100%" fill="white"/>']
  for kind,q,fill,col,width in self.items:
   if kind=='text':
    x,y,text,size=q;a.append(f'<text x="{x}" y="{y}" font-family="Segoe UI,sans-serif" font-size="{size}" fill="{col}">{escape(text)}</text>')
   else:
    pts=' '.join(f'{x:.2f},{y:.2f}' for x,y in q)
    tag='polygon' if kind=='poly' else 'polyline'
    a.append(f'<{tag} points="{pts}" fill="{fill or "none"}" stroke="{col}" stroke-width="{width}" stroke-linejoin="round"/>')
  a.append('</svg>');(DESIGN/name).write_text(''.join(a),encoding='utf-8')
 def draw(self,doc,x,y,w):
  s=w*mm/self.w;c=doc.c;c.saveState();c.translate(x*mm,(297-y)*mm)
  for kind,q,fill,col,lw in self.items:
   c.setStrokeColor(HexColor(col));c.setLineWidth(lw*s)
   if kind=='text':
    xx,yy,t,size=q;c.setFillColor(HexColor(col));c.setFont('R',size*s);c.drawString(xx*s,-yy*s,t)
   else:
    path=c.beginPath();path.moveTo(q[0][0]*s,-q[0][1]*s)
    for xx,yy in q[1:]:path.lineTo(xx*s,-yy*s)
    if kind=='poly':path.close();c.setFillColor(HexColor(fill))
    c.drawPath(path,stroke=1,fill=int(kind=='poly'))
  c.restoreState()

def box(fig,origin,scale,x,y,z,l,d,h,color):
 def pr(a,b,c):return origin[0]+scale*(a+.60*b),origin[1]+scale*(.32*b-c)
 bottom=[pr(x,y,z),pr(x+l,y,z),pr(x+l,y+d,z),pr(x,y+d,z)]
 top=[pr(x,y,z+h),pr(x+l,y,z+h),pr(x+l,y+d,z+h),pr(x,y+d,z+h)]
 fig.poly([bottom[0],bottom[1],top[1],top[0]],color)
 fig.poly([bottom[1],bottom[2],top[2],top[1]],color)
 fig.poly(top,color)
 return pr

def diagrams():
 a=Figure(h=480);o=(60,355);s=.32
 # Open rectangular floor frame, not a solid exercise platform.
 for x,y,l,d in [(0,0,1200,30),(0,0,30,650),(1170,0,30,650)]:box(a,o,s,x,y,0,l,d,30,'#87958c')
 for x in [180,1020]:
  for y in [90,470]:box(a,o,s,x,y,30,30,30,360,'#788980')
 box(a,o,s,165,85,115,880,420,255,'#d4c5ae')
 # Three frontal storage zones are diagrammatic, not a specified latch design.
 for x,l in [(180,245),(445,245),(710,315)]:box(a,o,s,x,72,145,l,20,195,'#e2d6c4')
 box(a,o,s,150,65,390,900,450,15,'#d4c5ae')
 box(a,o,s,150,65,405,900,450,45,'#a6b9aa')
 for y in [95,485]:box(a,o,s,35,y,30,30,30,840,'#788980')
 box(a,o,s,35,95,870,30,420,30,'#788980')
 a.text(25,22,'Скамья с постоянным сиденьем',20)
 a.text(25,47,'Поисковая схема без масштаба. Цвет разделяет части, материал ещё выбирается.',13)
 a.line([(129,98),(200,70),(450,70)]);a.text(250,65,'Неподвижный хват',15)
 a.line([(364,237),(520,160),(735,160)]);a.text(520,145,'Сменная мягкая накладка',14)
 a.line([(298,286),(555,280),(735,280)]);a.text(525,265,'Раздельное хранение',14)
 a.poly([(550,330),(685,330),(730,370),(595,370)],'#c7d4c7')
 a.text(555,393,'Отдельная панель для пола',14)
 a.line([(540,404),(565,435),(735,435)]);a.text(460,455,'Своя напольная рама',14)
 a.save('bench-concept.svg')
 b=Figure(h=470)
 b.text(20,24,'Напольный шкаф со складным сиденьем',20)
 b.text(20,49,'Стена - только фон. Основание остаётся на полу в обоих состояниях.',13)
 for origin,opened in [((30,307),False),((415,307),True)]:
  sc=.24
  for x,y,l,d in [(0,0,800,30),(0,0,30,900),(770,0,30,900)]:box(b,origin,sc,x,y,0,l,d,30,'#87958c')
  box(b,origin,sc,50,50,30,700,400,970,'#d4c5ae')
  for x in [60,720]:box(b,origin,sc,x,430,30,25,25,875,'#788980')
  box(b,origin,sc,60,430,905,685,25,25,'#788980')
  if opened:
   for x in [90,680]:box(b,origin,sc,x,830,30,30,30,390,'#788980')
   box(b,origin,sc,70,450,420,650,450,30,'#a6b9aa')
  else:box(b,origin,sc,70,455,450,650,30,420,'#a6b9aa')
 b.text(50,402,'Сиденье убрано',15);b.text(450,402,'Сиденье на двух передних ножках',15)
 b.text(20,445,'Нужны расчёт рамы, фиксация ножек и проверка подхода к хвату.',14)
 b.save('cabinet-concept.svg')
 return a,b

def atlas():
 doc=Document('Visual_analog_details_A4_2026-11-25')
 for m in data['models']:
  doc.begin(f"{int(m['number']):02d}. {m['title']}",'Детали на фотографиях: польза, ограничения и перенос в наш проект.')
  y=doc.text(m['facts'],10,29,190,'small')+3
  top=max(y,43);six=len(m['tiles'])==6;ch=54 if six else 75;ph=24 if six else 41;cw=93.5
  doc.current.append('<div class="grid">')
  for i,t in enumerate(m['tiles']):
   x=10+(i%2)*96.5;yy=top+(i//2)*ch
   doc.c.setStrokeColor(HexColor('#CDD7D0'));doc.c.setLineWidth(.4);doc.c.rect(x*mm,(297-yy-ch+2)*mm,cw*mm,(ch-2)*mm)
   source=doc.photo(t['asset'],t['crop'],x+2,yy+2,cw-4,ph,label=t['title'])
   ty=yy+ph+3
   ty=doc.text(t['title'],x+2,ty,cw-4,'tile',bold='Деталь:',html=False)+1
   ty=doc.text(t['plus'],x+2,ty,cw-4,'tile',bold='Плюс:',html=False)+1
   ty=doc.text(t['minus'],x+2,ty,cw-4,'tile',bold='Ограничение:',html=False)
   assert ty<=yy+ch-1,(m['title'],t['title'],ty,yy+ch)
   crop=t.get('crop');c=crop or [0,0,1,1];left,up,right,down=c
   # Editable HTML preserves the full original behind a crop viewport.
   rel='../../'+source['path']
   pic=f'<div style="height:{ph}mm;display:flex;justify-content:center;align-items:center"><a href="{escape(source["page"])}"><img src="{escape(rel)}" style="max-height:{ph}mm;max-width:88mm"></a></div>'
   if crop:
    # Explicit image crop, generated only from a preserved source for the editable document.
    ip=Image.open(ROOT/source['path']);ip=ip.crop(tuple(round(v*(ip.width if j%2==0 else ip.height)) for j,v in enumerate(crop)))
    crop_name=t['photo_id'].replace('.','-')+'.jpg';crop_dir=D/'layout-crops';crop_dir.mkdir(exist_ok=True)
    ip.convert('RGB').save(crop_dir/crop_name,quality=94)
    pic=f'<img src="../../research/analogs/visual-brief-2026-11-25/layout-crops/{crop_name}" style="height:{ph}mm;max-width:88mm;object-fit:contain">'
   doc.current.append('<div class="tile">'+pic+'<h2>'+escape(t['title'])+'</h2><p class="plus"><b>Плюс:</b> '+escape(t['plus'])+'</p><p class="minus"><b>Ограничение:</b> '+escape(t['minus'])+'</p></div>')
  doc.current.append('</div>');y=top+math.ceil(len(m['tiles'])/2)*ch+1
  for g in m['groups']:y=doc.text(g,10,y,190,'small')+1
  y=doc.text(m['conclusion'],10,y+1,190,'body',bold='Нейтральный вывод:')+2
  if m.get('review'):
   r=data['reviews'][m['review']];y=doc.text(r['finding'],10,y,190,'small',bold='Опыт использования:')+1
   y=doc.links([(r['title'],r['url'])],y)
  else:y=doc.text('Надёжный длительный опыт именно этой модели в текущей подборке не установлен. Ресурс и удобство по одним фотографиям не оцениваем.',10,y,190,'small')+1
  maker=m['maker_sources'][0]
  doc.links([('Характеристики и фото: '+maker['title'],maker['url'])],max(y,270-3))
  doc.finish()
 # Human bibliography, without source or movement codes.
 all_refs=[];seen=set()
 for m in data['models']:
  for s in m['maker_sources']:
   if s['url'] not in seen:all_refs.append((s['title'],s['url'],'Параметры и изображения из сохранённого исследования.'));seen.add(s['url'])
 for r in data['reviews'].values():all_refs.append((r['title'],r['url'],r['kind']))
 for k in range(0,len(all_refs),11):
  doc.begin('Источники фотографий и опыта','Факты источников отделены от наших проектных выводов. Проверка дополнений: 25 ноября 2026.')
  y=32
  for title,url,note in all_refs[k:k+11]:
   y=doc.links([(title,url)],y);y=doc.text(note,10,y,190,'small')+3
  y=doc.text('Характеристики ранее проверялись 23 ноября; новые отзывы и материалы прочитаны 25 ноября. У редких концептов технические пробелы сохранены. Отзывы не дают статистики отказов. Увеличенные фрагменты и кадры роликов не выданы за новые съёмки. На листах нет буквенных кодов упражнений и источников.',10,y+2,190,'body')
  doc.finish()
 doc.save();return doc

def add_concept(doc,fig,concept):
 doc.begin(concept['name'],'Предложение для эскиза, не выбранная автором конструкция и не чертёж изготовления.')
 fig.draw(doc,10,30,190);doc.current.append('<img class="concept" src="../../design/preliminary-trainer-2026-11-25/'+concept['file']+'">')
 y=30+fig.h/fig.w*190+6
 for label,key in [('Устройство:','proposal'),('Плюс:','plus'),('Ограничение:','minus'),('Размеры для рисунка:','dimensions'),('Как использовать:','first')]:
  text=re.sub(r'^Для рисунка: ','',concept[key]) if key=='dimensions' else concept[key]
  y=doc.text(text,10,y,190,'body',bold=label)+3
 doc.finish()

def make_brief(a,b):
 doc=Document('Preliminary_trainer_brief_A4_2026-11-25')
 doc.begin('Предварительное задание на эскиз','Начало разработки модели по упражнениям, аналогам и найденному опыту использования.')
 y=doc.text(brief['purpose'],10,31,190,'body')+4
 rows=[[f['name'],f['why'],f['proposal']] for f in brief['base_functions']]
 y=doc.table(['Функция','Зачем нужна','Предлагаемое устройство'],rows,[34,70,86],y)+5
 for text in [brief['status'],'Сохраняем все три группы и установку без сверления. Основные действия: ребёнок на четвереньках и лёжа; молодой взрослый с ковриком и гантелями; пожилой сидя и стоя у неподвижной опоры. Дополнительные примеры остаются резервом.',
  'Сначала сравниваем простую скамью и напольный шкаф. Скамья - первый кандидат для проверки посадки, доступа и хвата с меньшим числом шарниров. Это рекомендация помощника, не окончательный выбор формы.']:
  y=doc.text(text,10,y,190,'body')+3
 doc.finish()
 doc.begin('Движения определяют части изделия','Ранее выбранные примеры показаны словами и исходными изображениями, без кодов.')
 for row,(group,pics,need) in enumerate(BODY):
  top=32+row*72;doc.text(group,10,top,190,'sub')
  for col,(filename,label,page) in enumerate(pics):
   key='body-'+Path(filename).stem;x=10+col*32
   s=doc.photo(key,None,x,top+8,29,30,label=label)
   doc.text(label,x,top+40,30,'small',html=False)
   doc.current.append('<figure style="display:inline-block;width:28mm;margin:1mm"><img style="width:28mm;height:30mm;object-fit:contain" src="../../'+s['path']+'"><figcaption>'+escape(label)+'</figcaption></figure>')
  doc.text(need,111,top+8,89,'body')
  doc.current.append('<p>'+escape(need)+'</p>')
  doc.c.setStrokeColor(HexColor('#D0D9D3'));doc.c.line(10*mm,(297-top-67)*mm,200*mm,(297-top-67)*mm)
 doc.text('Детские изображения - примеры из детской терапии для анализа контактов. Возрастные границы и индивидуальная применимость не установлены. Дозировки и масса весов здесь не назначаются.',10,253,190,'small')
 refs=[('NHFT','https://www.nhft.nhs.uk/childrens-ot/'),('ACE','https://www.acefitness.org/resources/everyone/blog/5241/4-upper-body-movements-for-beginners/'),('Kathryn Alexander / Becca Ewing','https://www.kathrynalexander.com/resources/exercise-library-1/legs-and-glutes/'),('NHS','https://www.nhs.uk/live-well/exercise/strength-exercises/')]
 source_text='Источники: '+', '.join('<link href="'+url+'" color="#315E48">'+escape(title)+'</link>' for title,url in refs)
 source_paragraph=Paragraph(source_text,styles['small']);_,height=source_paragraph.wrap(190*mm,20*mm)
 source_paragraph.drawOn(doc.c,10*mm,30*mm-height)
 doc.current.append('<p class="source">Источники: '+', '.join('<a href="'+url+'">'+escape(title)+'</a>' for title,url in refs)+'</p>')
 doc.finish()
 add_concept(doc,a,brief['concepts'][0]);add_concept(doc,b,brief['concepts'][1])
 doc.begin('Предлагаемый инвентарь','Количество и масса не равны назначению нагрузки конкретному человеку.')
 rows=[[i['item']+'\n'+i['quantity'],i['use'],i['storage']+' '+i['state']] for i in brief['inventory']]
 y=doc.table(['Что','Для какого действия','Хранение и статус'],rows,[43,65,82],32)+5
 y=doc.text('Не включаем в основу без нового обоснования: тяжёлый мяч для детской игры, степ, пружинную каретку, педали, моторы, экран и сложную наклонную спинку. Лента остаётся резервом; исходная тяга сидя не требует крепить её к корпусу.',10,y,190,'body')
 doc.finish()
 doc.begin('Материалы: что сравнивать','Предпочтение сменным контактам - проектная гипотеза. Окончательные марки не выбраны.')
 # Real photographs show material assemblies; they are not swatches of a selected specification.
 for j,(key,label) in enumerate([('solo-p12','Сталь и узел колеса'),('step-0700','Покрытие отдельной части'),('fit-p06','Полимерный корпус'),('pent-p01','Дерево и механика')]):
  doc.photo(key,None,10+j*48,31,45,25,label=label);doc.text(label,10+j*48,57,45,'small',html=False)
  doc.current.append('<img style="width:43mm;height:25mm;object-fit:contain" src="../../'+assets[key]['path']+'">')
 rows=[[m['part'],m['candidate'],m['limit']] for m in brief['materials']]
 y=doc.table(['Часть','Первый кандидат','Что пока не доказано'],rows,[35,78,77],68,'small')+4
 doc.text('Мой предварительный выбор для сравнения: стальная силовая рама, фанерное хранение, отдельные мягкие накладки и панель. Цель - понятное изготовление и замена изнашиваемых частей. Это не доказательство превосходства над массивом, алюминием или формованным пластиком.',10,y,190,'small')
 doc.finish()
 doc.begin('Отзывы и долговечность','Изучены пять источников опыта. У каждого есть пределы применимости.')
 rows=[]
 for key in ['speed','tech','tonal','solo','fit']:
  r=data['reviews'][key];rows.append([r['title'],r['finding'],r['kind']])
 y=doc.table(['Источник опыта','Что заметил автор','Как читать'],rows,[46,95,49],32,'small')+4
 notes=[
  'Вывод по отзывам: удержание весов при перемещении, жёсткость опоры и зависимость от программы надо проверять отдельно. Нельзя ранжировать все аналоги по сроку службы: длительных сопоставимых испытаний не найдено.',
  'У Solo сталь и швы имеют пожизненную домашнюю гарантию, обивка - 90 дней по карточке. Это условия гарантии, а не ресурс и не обещание для нашей конструкции.',
  'У технических материалов сравниваем режим испытания, а не красивое число. На странице Silvertex указан Wyzenbeek 100 000 циклов; в старом европейском каталоге - другой тест Martindale. Они не переводятся друг в друга и в годы службы.',
  'У пены нужны данные о сжатии и восстановлении, у обивки - о шве и очистке. Окончательный выбор делается на доступных образцах, а не по названию «премиум».'
 ]
 for note in notes:y=doc.text(note,10,y,190,'body')+3
 doc.links([(r['title'],r['url']) for r in data['reviews'].values()],y+1)
 doc.finish()
 for start,title in [(0,'Требования к использованию'),(6,'Требования к конструкции и проверке')]:
  doc.begin(title,'Рабочая версия задания. У каждого требования указаны основание и проверяемый результат.')
  rows=[[r['topic'],r['requirement'],r['basis']+'. '+r['acceptance']] for r in brief['requirements'][start:start+6]]
  doc.table(['Тема','Что требуется','Основание и критерий проверки'],rows,[31,83,76],32)
  doc.finish()
 doc.begin('Стоимость и следующие решения','Ориентиры прайсов на 25 ноября 2026. Полная стоимость изделия пока не определена.')
 cost=brief['cost_example'];total=Decimal('0');rows=[]
 for item in cost['items']:
  sub=Decimal(str(item['quantity']))*Decimal(str(item['unit_price_rub']));total+=sub
  rows.append([item['item'],str(item['quantity'])+' '+item['unit'],f'{item["unit_price_rub"]:.2f} руб.',f'{sub:.2f} руб.'])
 y=doc.table(['Закупочный пример','Количество','Цена единицы','Подытог'],rows,[80,27,39,44],32)+4
 y=doc.text('Итого только две позиции: '+f'{total:.2f}'+' руб. Сечение трубы, толщина листа и расход - ценовой пример, не результат расчёта. Установленная масса рамы и расход деталей здесь не определены.',10,y,190,'body')+4
 y=doc.text(cost['region'],10,y,190,'small')+4
 y=doc.text(cost['not_priced'],10,y,190,'body',bold='Не включено:')+4
 y=doc.text(cost['value'],10,y,190,'body',bold='Цена и функция:')+5
 for i,text in enumerate(brief['next_steps'],1):y=doc.text(str(i)+'. '+text,10,y,190,'body')+3
 y=doc.links([('Цена трубы: Стройсталь',cost['items'][0]['url']),('Цена листа: Фанераоптом',cost['items'][1]['url'])],y+2)
 doc.finish()
 doc.begin('Основания выбора и ссылки','Паспорта, отзывы и открытые прайсы. Ссылки кликабельны, без служебных кодов.')
 y=31
 for s in data['new_sources']:
  y=doc.links([(s['title'],s['url'])],y);y=doc.text(s['finding'],10,y,190,'small')+3
 y=doc.text('Основания проекта: консультация 6 ноября - полезные функции через упражнения (09:18-09:59), габариты через движения и опоры (10:53-11:56). Решения автора: все три группы по очереди, без сверления. Ни новая форма, ни нагрузки и материалы пока не утверждены.',10,y,190,'small')+4
 doc.links([('Детский источник движений: NHFT','https://www.nhft.nhs.uk/childrens-ot/'),('Вставание и поддержка стоя: NHS','https://www.nhs.uk/live-well/exercise/strength-exercises/'),('Поворот сидя: NHS','https://www.nhs.uk/live-well/exercise/sitting-exercises/')],y)
 doc.finish();doc.save();return doc,total

def write_research(total):
 lines=['# Визуальный разбор и предварительное задание / 25.11.2026','',brief['status'],'',
 'В печатной подаче буквенные обозначения упражнений, источников и функций заменены словами. Внутренние ключи JSON сохранены только для связи с фотографиями. Старые авторские версии и исходники не перезаписаны.','']
 for m in data['models']:
  lines.extend(['## '+m['title'],m['facts'],''])
  for t in m['tiles']:lines.append('**'+t['title']+'**. Плюс: '+t['plus']+' Ограничение: '+t['minus'])
  lines.extend(m['groups']);lines.append('**Нейтральный вывод:** '+m['conclusion'])
  if m.get('review'):
   r=data['reviews'][m['review']];lines.append('**Опыт:** ['+r['title']+']('+r['url']+'). '+r['finding']+' '+r['kind'])
  else:lines.append('Длительный независимый опыт именно этой модели в текущей подборке не установлен.')
  for s in m['maker_sources']:lines.append('[Характеристики и фото: '+s['title']+']('+s['url']+')')
  lines.append('')
 lines.extend(['# Предварительная модель','',brief['purpose']])
 for c in brief['concepts']:lines.extend(['## '+c['name'],c['proposal'],c['plus'],c['minus'],c['dimensions'],c['first']])
 lines.extend(['## Материалы',''])
 for m in brief['materials']:lines.extend(['**'+m['part']+'**. '+m['candidate'],m['why'],m['limit'],'Проверить: '+m['test']])
 lines.extend(['## Предварительное ТЗ',''])
 for r in brief['requirements']:lines.extend(['**'+r['topic']+'**. '+r['requirement'],'Основание: '+r['basis']+'. Критерий: '+r['acceptance']])
 lines.extend(['## Стоимость','Две закупочные позиции на 25.11.2026: '+str(total)+' руб. Это не себестоимость изделия.',brief['cost_example']['not_priced']])
 for s in data['new_sources']:lines.extend(['['+s['title']+']('+s['url']+'). '+s['finding']])
 (D/'README.md').write_text('\n\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':
 a,b=diagrams();at=atlas();br,total=make_brief(a,b);write_research(total)
 (D/'pages.json').write_text(json.dumps(PAGELOG,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (D/'photo-placements.json').write_text(json.dumps(PLACEMENTS,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'atlas_pages':at.pages,'brief_pages':br.pages,'detail_photos':sum(len(m['tiles']) for m in data['models']),'raw_material_example_rub':str(total)},ensure_ascii=False))
