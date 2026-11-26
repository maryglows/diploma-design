"""Print the analog-to-movement comparison as readable A4 landscape tables."""
from pathlib import Path
from io import BytesIO
from html import escape
from urllib.parse import urlparse
import json,re,hashlib
from PIL import Image as PILImage
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor,white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Table,TableStyle,Image,Spacer
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'research/analogs/function-analysis-2026-11-23.json'
SOURCE=ROOT/'research/analogs/function-analysis-sources-2026-11-23.json'
OUT=ROOT/'outputs/current'
STEM='Analog_project_advantages_A4_2026-11-23'
WORK=ROOT/'.codex-build/analog-function-analysis-2026-11-23'
WORK.mkdir(exist_ok=True,parents=True)
data=json.loads(DATA.read_text('utf-8'));sources=json.loads(SOURCE.read_text('utf-8'))
refs={s['id']:s for s in sources}
old=json.loads((ROOT/'research/analogs/detail-v2-2026-11-21/cards.json').read_text('utf-8'))
assets=json.loads((ROOT/'research/analogs/detail-v2-2026-11-21/sources.json').read_text('utf-8'))
for weight,font in [('R','segoeui.ttf'),('B','segoeuib.ttf')]:
 pdfmetrics.registerFont(TTFont(weight,str(Path('C:/Windows/Fonts')/font)))
pdfmetrics.registerFontFamily('R',normal='R',bold='B',italic='R',boldItalic='B')
styles={
 'body':ParagraphStyle('body',fontName='R',fontSize=9.3,leading=11.8,spaceAfter=4.5,textColor=HexColor('#243830')),
 'head':ParagraphStyle('head',fontName='B',fontSize=9.4,leading=11.4,textColor=white),
 'small':ParagraphStyle('small',fontName='R',fontSize=8,leading=10,spaceAfter=3,textColor=HexColor('#4A5D53')),
 'title':ParagraphStyle('title',fontName='B',fontSize=10.5,leading=13,spaceAfter=4,textColor=HexColor('#234D3B')),
 'source':ParagraphStyle('source',fontName='R',fontSize=9,leading=11,spaceAfter=3,textColor=HexColor('#243830'))
}
styles['reference']=ParagraphStyle('reference',fontName='R',fontSize=8.5,leading=10,textColor=HexColor('#243830'))
W,H=297*mm,210*mm;PAGELOG=[];html_pages=[]
pdf=Canvas(str(OUT/(STEM+'.pdf')),pagesize=(W,H),pageCompression=1)
pdf.setTitle('Что взять из аналогов для проекта: движения трёх групп')
pdf.setAuthor('Дипломный проект - рабочий анализ')

def markup(text):
 t=escape(text)
 def repl(match):
  ids=match.group(1).split(', ')
  if not all(i in refs for i in ids):return match.group(0)
  return '['+', '.join(f'<link href="{escape(refs[i]["url"],quote=True)}" color="#315E48">{i}</link>' for i in ids)+']'
 return re.sub(r'\[([SE][0-9a-z]+(?:, [SE][0-9a-z]+)*)\]',repl,t)

def para(text,style='body',boldlabel=None):
 if boldlabel=='Взять:':text=re.sub(r'^Взять\s+','',text)
 if boldlabel=='Проверить:':text=re.sub(r'^Проверить\s+','',text)
 t=markup(text)
 if boldlabel:t='<b>'+escape(boldlabel)+'</b> '+t
 return Paragraph(t,styles[style])

def begin(title,subtitle,bookmark=None):
 n=len(PAGELOG)+1
 pdf.setFillColor(HexColor('#234D3B'));pdf.setFont('B',16);pdf.drawString(10*mm,H-13*mm,title)
 pdf.setFont('R',8.7);pdf.setFillColor(HexColor('#4A5D53'));pdf.drawString(10*mm,H-19*mm,subtitle)
 if bookmark:pdf.bookmarkPage(bookmark);pdf.addOutlineEntry(title,bookmark)
 return n

def end(title,models=None):
 n=len(PAGELOG)+1
 pdf.setFont('R',8);pdf.setFillColor(HexColor('#52665B'))
 pdf.drawString(10*mm,7*mm,'23.11.2026   A4 альбомно, 100%   Номера соответствуют фотографиям v2 от 21.11.2026')
 pdf.drawRightString(287*mm,7*mm,str(n));pdf.showPage()
 PAGELOG.append({'page':n,'title':title,'models':models or []})

def table(rows,widths,top=182,minimum=None,padding=7):
 t=Table(rows,colWidths=[x*mm for x in widths],hAlign='LEFT')
 t.setStyle(TableStyle([
  ('BACKGROUND',(0,0),(-1,0),HexColor('#315E48')),('VALIGN',(0,0),(-1,-1),'TOP'),
  ('LEFTPADDING',(0,0),(-1,-1),padding),('RIGHTPADDING',(0,0),(-1,-1),padding),
  ('TOPPADDING',(0,0),(-1,-1),padding),('BOTTOMPADDING',(0,0),(-1,-1),padding),
  ('GRID',(0,0),(-1,-1),.4,HexColor('#C4D0C8')),
  ('ROWBACKGROUNDS',(0,1),(-1,-1),[white,HexColor('#F3F6F3')])]))
 _,height=t.wrap(277*mm,175*mm)
 assert top*mm-height>=14*mm,('table overflow',PAGELOG[-1:] or 'first',height/mm)
 t.drawOn(pdf,10*mm,top*mm-height)
 return top-height/mm

def head(cells):return [para(s,'head') for s in cells]

def model_cell(m):
 om=next(o for o in old if o['number']==m['number']);asset=assets[om['cards'][0]['asset']]
 path=ROOT/asset['path'];im=PILImage.open(path).convert('RGB');im.thumbnail((450,300))
 buf=BytesIO();im.save(buf,'JPEG',quality=92);buf.seek(0)
 scale=min(26*mm/im.width,20*mm/im.height)
 return [para(m['number']+' '+m['title'],'title'),Image(buf,width=im.width*scale,height=im.height*scale),Spacer(1,3),para(m['role'],'small'),para('Фото '+m['photos'],'small')]

def row(m):
 return [model_cell(m),[para(x) for x in m['facts']],
  [para(x) for x in m['groups']],
  [para(m['plus']),para(m['minus'])],
  [para(m['take'],boldlabel='Взять:'),para(m['check'],boldlabel='Проверить:')]]

def html_row(m):
 om=next(o for o in old if o['number']==m['number']);s=assets[om['cards'][0]['asset']]
 cells=[f'<b>{m["number"]} {escape(m["title"])}</b><img class="thumb" src="../../{escape(s["path"])}"><p>{escape(m["role"])}</p><small>Фото {escape(m["photos"])}</small>',
  ''.join('<p>'+escape(v)+'</p>' for v in m['facts']),''.join('<p>'+escape(v)+'</p>' for v in m['groups']),
  '<p>'+escape(m['plus'])+'</p><p>'+escape(m['minus'])+'</p>',
  '<p><b>Взять:</b> '+escape(re.sub(r'^Взять\s+','',m['take']))+'</p><p><b>Проверить:</b> '+escape(re.sub(r'^Проверить\s+','',m['check']))+'</p>']
 return '<tr>'+''.join('<td>'+v+'</td>' for v in cells)+'</tr>'

def intro():
 title='От движений к полезным деталям аналогов'
 begin(title,'Дети, молодые взрослые и пожилые используют одно изделие по очереди. Установка без сверления.', 'scope')
 rows=[head(['Группа','Первые три действия','Дополнительные примеры прежнего листа','Что нужно от изделия'])]
 for g in data['groups']:rows.append([para(g['name'],'title'),para(g['core']),para(g['reserve']),para(g['need']+' ['+', '.join(g['sources'])+']')])
 y=table(rows,[30,86,82,79])
 notes=[
  'Девять первых действий - текущая основа. Девять дополнительных сохранены для сравнения возможностей, не объявлены обязательными функциями. Коды C/Y/O соответствуют этой таблице; C1-C3, Y1-Y3, O1-O3 совпадают с ноябрьской матрицей.',
  '«Плюс» означает возможную пользу для нашего сценария. Связь с группой и предложение «взять» - проектный вывод помощника. Параметры изделия даны по источнику; они не подтверждают пригодность детям или пожилым.',
  'Возрастные границы, нагрузки и размеры своего изделия не утверждены. Новых наблюдений или испытаний нет. Дозировки не назначаются; детские примеры из терапии не являются общей программой занятий.'
 ]
 for note in notes:
  p=para(note);_,h=p.wrap(277*mm,100*mm);y-=4;assert y*mm-h>14*mm;p.drawOn(pdf,10*mm,y*mm-h);y-=h/mm
 end(title)
 html_pages.append('<section><h1>'+title+'</h1><p>Основа: одно изделие, три группы по очереди, установка без сверления.</p><table><tr>'+''.join('<th>'+x+'</th>' for x in ['Группа','Первые три действия','Дополнительные примеры','Требования'])+'</tr>'+''.join('<tr>'+''.join('<td>'+escape(g[k])+'</td>' for k in ['name','core','reserve','need'])+'</tr>' for g in data['groups'])+'</table>'+''.join('<p>'+escape(x)+'</p>' for x in notes)+'</section>')

HEADERS=['Аналог и роль','Инвентарь, конструкция, материал и габариты','Связь с движениями трёх групп','Плюсы и ограничения для нашего проекта','Что взять и проверить']

def models_page(models,label):
 begin(label,'Факты - в столбце конструкции. Связь с движениями, плюсы, ограничения и перенос - проектный разбор.', 'm'+models[0]['number'])
 table([head(HEADERS)]+[row(m) for m in models],[32,61,63,67,54],minimum=156)
 end(label,[m['number'] for m in models])
 html_pages.append('<section><h1>'+escape(label)+'</h1><table class="models"><colgroup>'+''.join(f'<col style="width:{v}mm">' for v in [32,61,63,67,54])+'</colgroup><tr>'+''.join('<th>'+h+'</th>' for h in HEADERS)+'</tr>'+''.join(html_row(m) for m in models)+'</table></section>')

def conclusions():
 title='Какие решения развивать в своём проекте'
 begin(title,'Это предложения по результатам сравнения. Материал, форма, высоты и механизмы автором ещё не выбраны.','takeaways')
 rows=[head(['Решение','Основание в движениях','На какие аналоги смотреть','Предлагаемый перенос и границы'])]
 for c in data['conclusions']:rows.append([para(c['feature'],'title'),para(c['why']),para(c['from']),para(c['decision'])])
 y=table(rows,[47,69,69,92])
 p=para('Первой проверить функцию поддержки рукой: ни одна изученная комплектация не даёт подтверждённого поручня для O2. Крюк ленты, магнит, колесо, подвижный рычаг и спинка скамьи не считаются его заменой.');_,h=p.wrap(277*mm,50*mm)
 assert (y-5)*mm-h>14*mm;p.drawOn(pdf,10*mm,(y-5)*mm-h)
 end(title)
 html_pages.append('<section><h1>'+title+'</h1><table><tr>'+''.join('<th>'+x+'</th>' for x in ['Решение','Основание','Аналоги','Перенос и границы'])+'</tr>'+''.join('<tr>'+''.join('<td>'+escape(c[k])+'</td>' for k in ['feature','why','from','decision'])+'</tr>' for c in data['conclusions'])+'</table></section>')

def references():
 # Compact source directory: full URLs remain clickable and are also written to the editable source text.
 for start in range(0,len(sources),12):
  part=sources[start:start+12];title='Источники и границы проверки - '+str(start//12+1)
  begin(title,'Ссылки в PDF кликабельны. Полные адреса и локальные основания сохранены в редактируемом тексте.','sources'+str(start))
  rows=[head(['Код','Источник','Что подтверждает и насколько доступен'])]
  for s in part:
   link=f'<link href="{escape(s["url"],quote=True)}" color="#315E48"><b>{escape(s["title"])}</b></link><br/>'+escape(urlparse(s['url']).netloc)
   rows.append([para(s['id'],'title'),Paragraph(link,styles['reference']),Paragraph('<b>'+escape(s['status'])+'.</b> '+escape(s['use']),styles['reference'])])
  table(rows,[18,97,162],padding=4);end(title)
  html_pages.append('<section><h1>'+title+'</h1><table><tr><th>Код</th><th>Источник</th><th>Проверка</th></tr>'+''.join('<tr><td>'+s['id']+'</td><td><a href="'+escape(s['url'])+'">'+escape(s['title'])+'</a></td><td>'+escape(s['status']+'. '+s['use'])+'</td></tr>' for s in part)+'</table></section>')

def write_text():
 md=['# Что взять из аналогов для проекта','',data['scope'],'',
  'Печать: А4 альбомно, 100%. Номера совпадают с фотокарточками v2. Параметры чужого изделия не задают размеры нашего. Плюсы, ограничения и перенос - проектный анализ, не результат испытания.','',
  '## Движения','']
 for g in data['groups']:md.extend(['### '+g['name'],g['core'],g['reserve'],g['need'],''])
 for m in data['models']:
  md.extend(['## '+m['number']+' '+m['title'],'**Роль:** '+m['role'],'**Факты:** '+' '.join(m['facts']),
   '**Связь с группами:** '+' '.join(m['groups']),m['plus'],m['minus'],'**Взять:** '+re.sub(r'^Взять\s+','',m['take']),'**Проверить:** '+re.sub(r'^Проверить\s+','',m['check']),'**Фото:** '+m['photos'],''])
 md.extend(['## Предлагаемый отбор',''])
 for c in data['conclusions']:md.extend(['**'+c['feature']+'**. '+c['why']+' Аналоги: '+c['from']+'. '+c['decision'],''])
 md.extend(['## Источники',''])
 for s in sources:
  md.extend(['**'+s['id']+'** ['+s['title']+']('+s['url']+'). '+s['status']+'. '+s['use']])
  if s.get('additional_url'):md.append('[Дополнительный первоисточник]('+s['additional_url']+')')
  if s.get('local'):md.append('[Сохранённый документ](../../'+s['local']+')')
  md.append('')
 md.extend(['## Основания проекта','',
  'Движения первого этапа: [матрица CSV](../../outputs/current/Function_selection_2026-11-06.csv), [данные и источники](../s-rank-development-2026-11-06.json). Все 18 примеров и первоисточники: [дети](../children-a3-analysis-2026-10-30.md), [молодые](../youth-a3-analysis-2026-10-30.md), [пожилые](../older-adults-a3-analysis-2026-10-30.md).',
  'Преподаватель: полезный функционал через упражнения, [консультация 03](../../meetings/raw/teacher-discussion-03.md), 09:18-09:59; габариты через движения, 10:53-11:56. Решения автора D-022: три группы по очереди; D-025: без сверления. Новых консультаций, обмеров и испытаний не добавлено.'])
 (ROOT/'research/analogs/function-analysis-2026-11-23.md').write_text('\n\n'.join(md)+'\n',encoding='utf-8')

if __name__=='__main__':
 assert [m['number'] for m in data['models']]==[f'{i:02}' for i in range(1,16)]
 for m in data['models']:assert all(s in refs for s in m['sources']) and len(m['groups'])==3
 intro()
 main=data['models'][:13]
 for i in range(0,12,2):models_page(main[i:i+2],f'Аналоги {main[i]["number"]}-{main[i+1]["number"]}: полезные детали')
 models_page(main[12:],'Аналог 13: дополнительный пример посадки')
 models_page(data['models'][13:],'Инвентарь 14-15: хват и места хранения')
 conclusions();references();pdf.save()
 css='''@page{size:A4 landscape;margin:10mm}body{font:9.3pt/1.27 "Segoe UI",sans-serif;color:#243830;background:#e1e6e1;margin:0}section{box-sizing:border-box;background:white;width:297mm;min-height:210mm;padding:10mm;margin:5mm auto;break-after:page}h1{font-size:16pt;color:#234d3b;margin:0 0 4mm}p{margin:0 0 1.7mm}table{border-collapse:collapse;table-layout:fixed;width:100%}th,td{border:.4pt solid #c4d0c8;padding:2.5mm;vertical-align:top;text-align:left}th{background:#315e48;color:white}tr:nth-child(odd){background:#f3f6f3}.thumb{display:block;max-width:26mm;max-height:20mm;margin:2mm 0}small{font-size:8pt}a{color:#315e48}@media print{body{background:white}section{width:277mm;min-height:190mm;padding:0;margin:0}}'''
 (OUT/(STEM+'.html')).write_text('<!doctype html><meta charset="utf-8"><title>Польза аналогов для проекта</title><style>'+css+'</style>'+''.join(html_pages),encoding='utf-8')
 write_text()
 (ROOT/'research/analogs/function-analysis-pages-2026-11-23.json').write_text(json.dumps(PAGELOG,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'pages':len(PAGELOG),'analogs':len(data['models']),'sources':len(sources),'pdf':str(OUT/(STEM+'.pdf'))},ensure_ascii=False))
