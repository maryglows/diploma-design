"""Build the project passport and A4 presentation of the saved image_gen sketches.

Generated artwork is embedded without cropping or pixel upscaling. The monochrome
PDF is normalized to the grayscale document colorspace for economical printing.
"""
from pathlib import Path
from html import escape
import json, hashlib, re
from PIL import Image
import pymupdf
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'design/pencil-sketches-2026-11-25'
RESEARCH=ROOT/'research/bork-style-2026-11-25'
OUT=ROOT/'outputs/current'
for n,f in [('CardR','segoeui.ttf'),('CardB','segoeuib.ttf')]:
    pdfmetrics.registerFont(TTFont(n,str(Path('C:/Windows/Fonts')/f)))
pdfmetrics.registerFontFamily('CardR',normal='CardR',bold='CardB',italic='CardR',boldItalic='CardB')

CONTENT={
 'date':'2026-11-25',
 'status':'Предварительная карточка проекта. Авторские требования отделены от предложений для макета.',
 'goal':'Одно домашнее изделие с мебельной функцией: подготовить место, взять инвентарь, выполнить выбранные движения и вернуть пространство к бытовому использованию. Дети, молодые взрослые и пожилые пользуются им по очереди.',
 'author_choices':[
  'Все три группы пользуются одним изделием по очереди; точные возрастные границы ещё уточняются.',
  'Установка без сверления: рабочую нагрузку принимает собственная рама и пол.',
  'Минималистичный мебельный образ, видимая древесина и дорогой на вид аккуратный продукт. BORK подтверждён автором как эстетический ориентир.',
  'Подача эскизов карандашом на А4: цветная и чёрно-белая версии, подписи обычными словами.'
 ],
 'users':[
  ['Дети','Вытянуть противоположные руку и ногу; дотянуться до мягкого предмета; поднять таз лёжа.','Отдельная напольная панель, лёгкий предмет и цель. Свободное вытягивание; тяжёлое хранение отделено.'],
  ['Молодые взрослые','Отжаться с коленей; присесть с гантелью; наклониться с гантелями.','Панель и свободные веса. Открытый подход, место кисти и возможность взять вес без переноса изделия.'],
  ['Пожилые','Сесть и встать; поднять пятки у опоры; повернуть корпус сидя.','Подобранное неподвижное сиденье, стопы на полу и отдельный фиксированный хват на своей раме.']
 ],
 'functions':[
  ['Покрытие пола','Мягкий контакт ладони, колена и спины; хранится отдельно. Складка не попадает под основной контакт тела.'],
  ['Сиденье','Постоянное либо жёстко зафиксированное после раскрытия. Подход перед стопами и место для рук остаются свободны.'],
  ['Поддержка рукой','Фиксированный хват связан с силовой рамой. Дерево - контактная оболочка; не опираемся на магнит или трос.'],
  ['Раздельное хранение','Гнёзда весов, лёгкая ячейка и место панели. Один предмет извлекается без перекладывания остальных.']
 ],
 'inventory':[
  ['Основа','Одна складная панель; мягкий лёгкий предмет и цель; гантель или пара по выбранным действиям.'],
  ['Резерв','Лента для дополнительных движений после проверки. В прежней тяге сидя она удерживается стопами; силовой анкер не обязателен.'],
  ['Пока не включаем','Экран, моторный привод, пружинную каретку, педали, ролик для пресса и скакалку: необходимость не выведена из девяти основных движений.']
 ],
 'materials':[
  ['Корпус и фасады','Фанера с натуральным шпоном ореха; массив - возможен локально.','Сравнить образцы кромки, шпон/массив, влагу, ремонт и цену. Вид дерева не задаёт ресурс.'],
  ['Силовая рама','Сталь с матовым покрытием; декоративные накладки отделены от силовых связей.','Сечение, крепёж, усталость, устойчивость пустого изделия и работа с открытым ящиком.'],
  ['Хват','Стальной несущий сердечник; гладкая деревянная оболочка, доступный крепёж.','Реальный обхват, скольжение, стык, очистка и смена накладки. Один красивый хват не подходит всем автоматически.'],
  ['Сиденье','Сменный мягкий модуль: основание, упругая пена, доступный чехол.','Посадка/вставание, жёсткость, сжатие, шов и разрешённая очистка; кожу сравнить с другими обивками.'],
  ['Панель для пола','Гибкая закрытоячеистая пена со сменной/очищаемой контактной частью.','Сцепление с конкретным полом, толщина, стыки и контакт тела. Не делать коврик жёсткими деревянными плитами.'],
  ['Гнёзда и опоры','Сменные вкладыши, противоскользящие подпятники, ограничители хода.','Гантель не выкатывается; кисть не зажимается; опоры не оставляют следов. Способ защиты от доступа ребёнка ещё выбрать.']
 ],
 'quality':[
  ['Что переносим из подачи BORK','Тёплую древесину, спокойную геометрию, единство инвентаря и хранения, аккуратные стыки и малые металлические акценты. Это наш анализ фотографий.'],
  ['Что считаем качеством своего изделия','Проверенная устойчивость, понятный хват/доступ, ровная кромка без заноз, обслуживаемый крепёж, сменные контактные части и документированный материал.'],
  ['Что ещё не определено','Выбор скамьи или шкафа, размеры людей/изделия, массы грузов, допустимые нагрузки, сорт древесины, обивка, механизм защиты весов, бюджет и стоимость изготовления.']
 ],
 'sources':[
  ['BORK HS844: материалы и хранение','https://www.bork.ru/eShop/Sports-Equipment/hs844/'],
  ['BORK HS841: гантели и отделка','https://www.bork.ru/eShop/Sports-Equipment/hs841/'],
  ['BORK HS830: панель и ремень','https://www.bork.ru/eShop/Sports-Equipment/hs830/']
 ],
 'plates':[
  {'key':'bench','title':'Скамья с хранением',
   'study':'Постоянное сиденье, отдельный боковой хват, два отсека и место панели. На малых видах - доступ к весам и использование напольной панели.',
   'check':'Проверить: хват под нагрузкой, подход к сиденью, выдвинутый тяжёлый ящик и защита весов от ребёнка. Гнёзда делать под измеренный инвентарь.',
   'relationship':'Раздельный доступ - из сравнения Solo, Technogym и StepBox; деревянная мебельная подача - из SANA, AT LEAST и BORK. Собственный хват - проектная задача.'},
  {'key':'cabinet','title':'Напольный шкаф со складным сиденьем',
   'study':'Два состояния, две передние ножки и боковые неподвижные опоры. Перед коленями нет поперечной рукояти; стена не несёт рабочую нагрузку.',
   'check':'Проверить: разворот и проход между опорами, фиксацию ножек и шарнира, высоту хранения и устойчивость пустого шкафа. Открытая полка весов пока не решает ограничение доступа.',
   'relationship':'Распределение по высоте - из Wall Compact и Ottagono; механически опёртое сиденье и собственная рама исследуются отдельно от настенных аналогов.'},
  {'key':'inventory','title':'Инвентарь и детали контакта',
   'study':'Сверху - гантели и их гнёзда. В середине - гибкая панель, мягкий предмет и цель. Снизу - сменное сиденье и хват со стальным сердечником.',
   'check':'Проверить: крепление деревянной оболочки, просвет пальцев, очистку, швы панели и замену чехла. Гантели показаны как формообразование; изготовление грузов не назначено.',
   'relationship':'Разделение предметов - из Technogym/StepBox; материалы и завершённая подача - из KILO/Kenko и BORK. Массы и размеры ещё не выбраны.'}
 ],
 'next_steps':['Сравнить две формы и выбрать компоновку первого макета.','Обмерить посадку, хват и доступ к предметам с представителями трёх групп.','Проверить устойчивость/узлы и сравнить образцы дерева, покрытия и обивки с расчётом изготовления.']
}

class Doc:
 def __init__(self,stem,mono=False):
  self.stem=stem;self.mono=mono;self.c=Canvas(str(OUT/(stem+'.pdf')),pagesize=(210*mm,297*mm));self.page=0;self.html=[];self.parts=[];self.images=[]
  self.color='#242424' if mono else '#42382F'
  self.styles={n:ParagraphStyle(n,fontName='CardB' if n in ('sub','head') else 'CardR',fontSize=size,leading=lead,textColor=HexColor(self.color)) for n,size,lead in [('body',9.6,12.6),('small',8.8,11.3),('sub',10.5,13),('head',9,11.4)]}
  self.c.setTitle('Карточка будущего проекта' if 'Project_card' in stem else 'Карандашные эскизы домашнего тренажёра')
 def start(self,title,subtitle):
  self.page+=1;self.parts=['<section><h1>'+escape(title)+'</h1><p class="subtitle">'+escape(subtitle)+'</p>']
  self.c.setFillColor(HexColor(self.color));self.c.setFont('CardB',15)
  assert pdfmetrics.stringWidth(title,'CardB',15)<190*mm,title
  self.c.drawString(10*mm,282*mm,title);self.text(subtitle,10,21,190,'small',html=False)
 def text(self,text,x,y,w,style='body',bold=None,html=True):
  markup=('<b>'+escape(bold)+'</b> ' if bold else '')+escape(text)
  p=Paragraph(markup,self.styles[style]);_,h=p.wrap(w*mm,270*mm)
  assert y+h/mm<287,(self.stem,self.page,y,text)
  p.drawOn(self.c,x*mm,(297-y)*mm-h)
  if html:self.parts.append('<p>'+markup+'</p>')
  return y+h/mm
 def table(self,headers,rows,widths,y,font='body'):
  def p(t,head=False):return Paragraph(escape(t),self.styles['head' if head else font])
  data=([[p(t,True) for t in headers]] if headers else [])+[[p(t) for t in row] for row in rows]
  t=Table(data,colWidths=[w*mm for w in widths]);t.setStyle(TableStyle([
   ('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.4,HexColor('#CFC6BC')),
   ('BACKGROUND',(0,0),(-1,0),HexColor('#EDE8E1')),
   ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
  _,h=t.wrap(190*mm,270*mm);assert y+h/mm<286,('table',self.page,y+h/mm)
  t.drawOn(self.c,10*mm,(297-y)*mm-h)
  self.parts.append('<table>'+('<tr>'+''.join('<th>'+escape(t)+'</th>' for t in headers)+'</tr>' if headers else '')+''.join('<tr>'+''.join('<td>'+escape(t)+'</td>' for t in row)+'</tr>' for row in rows)+'</table>')
  return y+h/mm
 def image(self,path,x,y,w,h,link=None):
  path=Path(path);im=Image.open(path);iw,ih=im.size;s=min(w/iw,h/ih);pw,ph=iw*s,ih*s;x+=(w-pw)/2;y+=(h-ph)/2
  self.c.drawImage(str(path),x*mm,(297-y-ph)*mm,pw*mm,ph*mm,mask='auto')
  if link:self.c.linkURL(link,(x*mm,(297-y-ph)*mm,(x+pw)*mm,(297-y)*mm),relative=0)
  rel=path.relative_to(ROOT).as_posix();self.parts.append('<img src="../../'+rel+'" style="width:'+str(round(pw,2))+'mm"/>')
  self.images.append(dict(pdf=self.stem+'.pdf',page=self.page,path=rel,ppi=round(iw*25.4/pw,1),crop=False,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
 def link(self,label,url,y):
  p=Paragraph('<link href="'+escape(url,quote=True)+'">'+escape(label)+'</link>',self.styles['small']);_,h=p.wrap(190*mm,20*mm);assert y+h/mm<286
  p.drawOn(self.c,10*mm,(297-y)*mm-h);self.parts.append('<p><a href="'+escape(url)+'">'+escape(label)+'</a></p>');return y+h/mm+1
 def finish(self):
  self.c.setFillColor(HexColor(self.color));self.c.setFont('CardR',7.1)
  note='Эскизная визуализация ИИ, без масштаба' if self.stem.startswith('Pencil_') else 'Поисковый проект, конструкция ещё проверяется'
  self.c.drawString(10*mm,5*mm,'25.11.2026   А4, 100%   '+note)
  self.c.drawRightString(200*mm,5*mm,str(self.page));self.c.showPage();self.parts.append('</section>');self.html.append(''.join(self.parts))
 def save(self):
  self.c.save()
  if self.mono:
   path=OUT/(self.stem+'.pdf');doc=pymupdf.open(path)
   for page in doc:page.recolor(components=1)
   tmp=path.with_suffix('.gray.pdf');doc.save(tmp,garbage=4,deflate=True);doc.close();tmp.replace(path)
  css='''@page{size:A4;margin:10mm}*{box-sizing:border-box}body{font:9.2pt/1.3 "Segoe UI",sans-serif;color:#42382f;background:#ddd}section{background:white;width:210mm;min-height:297mm;margin:4mm auto;padding:10mm;break-after:page}h1{font-size:15pt;margin:0 0 2mm}h2{font-size:10.5pt}p{margin:2mm 0}p.subtitle{font-size:8pt}table{width:100%;border-collapse:collapse;table-layout:fixed}td,th{border:.4pt solid #cfc6bc;text-align:left;vertical-align:top;padding:2mm}th{background:#ede8e1}img{display:block;max-width:100%;margin:2mm auto}a{color:inherit}@media print{body{background:white}section{width:190mm;min-height:277mm;margin:0;padding:0}}'''
  if self.mono:css+='section{filter:grayscale(1)}'
  (OUT/(self.stem+'.html')).write_text('<!doctype html><meta charset="utf-8"><title>'+self.stem+'</title><style>'+css+'</style>'+''.join(self.html),encoding='utf-8')

def card():
 d=Doc('Project_card_A4_2026-11-25')
 d.start('Карточка будущего проекта','Рабочая версия: требования автора, предлагаемая основа и открытые проверки.')
 y=d.text(CONTENT['goal'],10,31,190)+3
 y=d.text('Для кого и для каких действий',10,y,190,'sub')+2
 y=d.table(['Группа','Основные движения','Что даёт изделие'],CONTENT['users'],[28,77,85],y,font='small')+4
 y=d.text('Предлагаемая основа - четыре функции',10,y,190,'sub')+2
 for i,(title,text) in enumerate(CONTENT['functions']):
  col=i%2;row=i//2;x=10+col*97;yy=y+row*26
  d.c.setStrokeColor(HexColor('#CFC6BC'));d.c.rect(x*mm,(297-yy-24)*mm,93*mm,24*mm)
  yy=d.text(title,x+2,yy+2,89,'sub');d.text(text,x+2,yy+1,89,'small')
 y+=55
 y=d.text('Предлагаемый инвентарь',10,y,190,'sub')+2
 y=d.table([],CONTENT['inventory'],[29,161],y,font='small')+4
 y=d.text('Что уже задано автором',10,y,190,'sub')+1
 for t in [CONTENT['author_choices'][1],CONTENT['author_choices'][2]]:y=d.text(t,10,y+1,190,'small')
 d.text('Изображение человека показывает сценарий. Возраст допуска, самостоятельность подготовки, нагрузки и подходящие размеры ещё не определены.',10,y+2,190,'small')
 d.finish()
 d.start('Материалы, образ и качество','Дерево предпочтительно по пожеланию автора; конкретные материалы ещё сравниваются.')
 source=json.loads((RESEARCH/'sources.json').read_text('utf-8'))
 for i,r in enumerate(source['images']):
  d.image(ROOT/r['path'],10+i*48,31,45,35,r['page'])
  labels=['Древесина и акцент','Хранение как мебель','Стык и шов','Гибкая поверхность']
  d.text(labels[i],10+i*48,67,45,'small')
 y=d.text('На официальных страницах BORK указаны орех, кожа и латунь. На фото выше видим отделку и организацию хранения. Это эстетический ориентир; фотографии и заявления бренда не подтверждают долговечность нашего будущего изделия.',10,77,190,'small')+3
 y=d.table(['Часть','Предлагаемая проработка','Что проверяем'],CONTENT['materials'],[28,70,92],y,font='small')+3
 for title,text in CONTENT['quality'][1:]:y=d.text(text,10,y+1,190,'small',bold=title+':')
 y=d.text('Первый кандидат - скамья; шкаф - вариант для сравнения. Эскизы не в масштабе. Сечение рамы, размеры, нагрузки и полная стоимость здесь не назначены.',10,y+2,190,'small')+3
 for title,url in CONTENT['sources']:y=d.link(title,url,y)
 d.finish();d.save();return d

def sketches(mono):
 d=Doc('Pencil_sketches_'+('BW' if mono else 'COLOR')+'_A4_2026-11-25',mono)
 for plate in CONTENT['plates']:
  d.start(plate['title'],'Графитный карандаш' if mono else 'Графит и цветные карандаши: орех, камень, графит, тёплый акцент')
  d.image(ART/(plate['key']+('-bw.png' if mono else '-color.png')),22,28,166,232)
  y=d.text(plate['study'],10,262,190,'small',bold='Идея:')
  d.text(plate['check'],10,y+1.5,190,'small',bold='Проверки:')
  d.parts.append('<p class="subtitle">Эскизная визуализация ИИ, без масштаба. Конструкция ещё проверяется.</p>')
  d.finish()
 d.save();return d

def main():
 (ART/'project-card.json').write_text(json.dumps(CONTENT,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 docs=[card(),sketches(False),sketches(True)]
 places=[p for d in docs for p in d.images]
 (ART/'print-placements.json').write_text(json.dumps(places,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({d.stem:d.page for d in docs},ensure_ascii=False))

if __name__=='__main__':main()
