"""Build numbered, small cut-out cards and a short research guide from JSON."""
from pathlib import Path
from io import BytesIO
from html import escape
from urllib.parse import urlparse
import json,math,hashlib,re
from PIL import Image
import pymupdf
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,KeepTogether
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader,PdfWriter

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'research/analogs/detail-v2-2026-11-21'
OUT=ROOT/'outputs/current';PARTS=OUT/'Analog_details_v2_2026-11-21';PARTS.mkdir(exist_ok=True)
MODELS=json.loads((DATA/'cards.json').read_text('utf-8'))
SOURCES=json.loads((DATA/'sources.json').read_text('utf-8'))
for name,font in [('R','segoeui.ttf'),('B','segoeuib.ttf')]:pdfmetrics.registerFont(TTFont(name,str(Path('C:/Windows/Fonts')/font)))

def lines(s,font,size,width):
 result=[];line=''
 for word in s.split():
  cand=(line+' '+word).strip()
  if line and pdfmetrics.stringWidth(cand,font,size)>width*mm:result.append(line);line=word
  else:line=cand
 if line:result.append(line)
 return result

def chunks(model):
 cards=model['cards'];n=len(cards)
 count=math.ceil(n/12) if n>16 else 1
 size=math.ceil(n/count)
 return [cards[i:i+size] for i in range(0,n,size)]

PLACEMENTS=[];PAGE_INDEX=[]

def build_group(models,name,appendix=False):
 pdf=Canvas(str(OUT/(name+'.pdf')),pagesize=(210*mm,297*mm),pageCompression=1)
 pdf.setTitle('Детали аналогов: небольшие карточки для монтажа на А3')
 html=['<!doctype html><meta charset="utf-8"><title>Карточки аналогов v2</title>',
 '''<style>@page{size:A4;margin:0}body{margin:0;background:#ddd;font-family:"Segoe UI",sans-serif}.page{position:relative;width:210mm;height:297mm;background:#fff;overflow:hidden;break-after:page;margin:5mm auto}.t{position:absolute;white-space:nowrap;line-height:1}.photo{position:absolute;overflow:hidden;background:white}.photo img{position:absolute}.cut{position:absolute;border:0.3pt dashed #d6dcda;box-sizing:border-box}@media print{body{background:white}.page{margin:0}}</style>''']
 pnum=0;model_ranges=[]
 for model in models:
  blocks=chunks(model);start=pnum
  for sub,block in enumerate(blocks,1):
   pnum+=1;html.append('<section class="page">')
   def text(x,y,s,size=8.2,bold=False,color='#263C36',width=190,maxlines=10):
    font='B' if bold else 'R';ls=lines(s,font,size,width)
    assert len(ls)<=maxlines,(model['number'],s,len(ls))
    pdf.setFont(font,size);pdf.setFillColor(HexColor(color))
    for n,l in enumerate(ls):
     yy=y+n*size*.42
     assert yy<285,(s,yy)
     pdf.drawString(x*mm,(297-yy)*mm,l)
     html.append(f'<div class="t" style="left:{x}mm;top:{yy-size*.28}mm;font-size:{size}pt;font-weight:{700 if bold else 400};color:{color}">{escape(l)}</div>')
    return len(ls)
   text(10,12,model['number']+'  '+model['title'],17,True,width=188,maxlines=1)
   text(10,18.3,model['kind'],8.5,color='#53695E',width=188,maxlines=1)
   movements=re.sub(r'^(В кадрах: |В каталоге: |В ролике: )','',model['movements'])
   text(10,24.5,'Движения: '+movements,8.1,width=188,maxlines=2)
   text(10,33,'Что разобрать: '+model['focus'],8.1,width=188,maxlines=2)
   pdf.setStrokeColor(HexColor('#9DB3A8'));pdf.setLineWidth(.55);pdf.line(10*mm,257*mm,200*mm,257*mm)
   cols=4 if len(block)>12 else 3;gap=4;cw=(190-(cols-1)*gap)/cols;ch=58;top=44
   for pos,card in enumerate(block):
    x=10+pos%cols*(cw+gap);y=top+(pos//cols)*ch
    # The outer cut line includes the cue so the author can keep or trim it off.
    pdf.setStrokeColor(HexColor('#D6DCDA'));pdf.setDash(1.4,2);pdf.setLineWidth(.28)
    pdf.rect(x*mm,(297-y-ch+2)*mm,cw*mm,(ch-2)*mm);pdf.setDash()
    html.append(f'<div class="cut" style="left:{x}mm;top:{y}mm;width:{cw}mm;height:{ch-2}mm"></div>')
    src=SOURCES[card['asset']];path=ROOT/src['path'];raw=path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==src['saved_sha256']
    im=Image.open(BytesIO(raw))
    original_size=im.size
    crop=card.get('crop')
    if crop:
     box=tuple(round(v*(im.width if i%2==0 else im.height)) for i,v in enumerate(crop));im=im.crop(box)
    # Figure extraction/cropping for document layout; no synthetic product details.
    if im.mode=='RGBA':
     bg=Image.new('RGB',im.size,'white');bg.paste(im,mask=im.getchannel('A'));im=bg
    else:im=im.convert('RGB')
    iw,ih=im.size;bw=cw-4;bh=34 if cols==4 else 35
    scale=min(bw/iw,bh/ih,25.4/200)
    pw,ph=iw*scale,ih*scale;px=x+2+(bw-pw)/2;py=y+2+(bh-ph)/2
    target=(max(1,round(pw/25.4*400)),max(1,round(ph/25.4*400)))
    im.thumbnail(target,Image.Resampling.LANCZOS);buf=BytesIO();im.save(buf,'JPEG',quality=94,subsampling=0)
    pdf.drawImage(ImageReader(BytesIO(buf.getvalue())),px*mm,(297-py-ph)*mm,pw*mm,ph*mm)
    if src.get('page'):pdf.linkURL(src['page'],(px*mm,(297-py-ph)*mm,(px+pw)*mm,(297-py)*mm),relative=0)
    # Cropped HTML uses the full saved image with a clipped viewport, preserving the source.
    rel='../../'+src['path'];cx,cy,cx2,cy2=crop or [0,0,1,1]
    fullw=pw/(cx2-cx);fullh=ph/(cy2-cy)
    html.append(f'<a href="{escape(src["page"])}"><div class="photo" style="left:{px:.3f}mm;top:{py:.3f}mm;width:{pw:.3f}mm;height:{ph:.3f}mm"><img src="{escape(rel)}" style="width:{fullw:.3f}mm;height:{fullh:.3f}mm;left:{-cx*fullw:.3f}mm;top:{-cy*fullh:.3f}mm"></div></a>')
    size=7.6 if cols==4 else 8.2
    title=card['id']+'  '+card['title']
    tl=text(x+2,y+40,title,size,True,width=cw-4,maxlines=2)
    note=card['note']
    text(x+2,y+40+tl*size*.42+1.2,note,7.4 if cols==4 else 7.8,color='#3D594C',width=cw-4,maxlines=3)
    ppi=round(im.width*25.4/pw)
    PLACEMENTS.append(dict(id=card['id'],model=model['number'],asset=card['asset'],pdf=name+'.pdf',page=pnum,crop=crop,photo_mm=[round(pw,2),round(ph,2)],pdf_pixels=list(im.size),ppi=ppi,source_path=src['path']))
   pdf.setFont('R',6.8);pdf.setFillColor(HexColor('#5B6B63'))
   foot=f'{model["number"]} / {sub} из {len(blocks)}   ·   A4, цвет, 100%   ·   Картинки и подсказки для вырезания и монтажа на A3'
   pdf.drawString(10*mm,9*mm,foot)
   pdf.drawRightString(200*mm,9*mm,str(pnum))
   html.append(f'<div class="t" style="left:10mm;top:286mm;font-size:6.8pt;color:#5B6B63">{escape(foot)}</div></section>')
   if sub==1:
    pdf.bookmarkPage('model'+model['number']);pdf.addOutlineEntry(model['number']+' '+model['title'],'model'+model['number'])
   pdf.showPage()
  model_ranges.append((model,start,pnum))
  PAGE_INDEX.append(dict(number=model['number'],title=model['title'],pdf=name+'.pdf',pages=list(range(start+1,pnum+1)),cards=len(model['cards']),appendix=appendix))
 pdf.save();(OUT/(name+'.html')).write_text(''.join(html),encoding='utf-8')
 reader=PdfReader(OUT/(name+'.pdf'))
 for model,a,b in model_ranges:
  writer=PdfWriter()
  for i in range(a,b):writer.add_page(reader.pages[i])
  writer.add_metadata({'/Title':model['number']+' '+model['title']})
  with (PARTS/(model['number']+'_analog.pdf')).open('wb') as f:writer.write(f)
 return pnum

def guide():
 styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='Ru',fontName='R',fontSize=9.3,leading=13,spaceAfter=6,textColor=HexColor('#263C36')));styles.add(ParagraphStyle(name='RuH',fontName='B',fontSize=12,leading=15,spaceBefore=10,spaceAfter=5,textColor=HexColor('#315D48')))
 flow=[Paragraph('Что подписывать на физических листах А3',styles['RuH']),Paragraph('Номер на каждой карточке связывает её с одним аналогом. Печатные подсказки можно оставить рядом или срезать после переноса своих пометок. Фрагмент - увеличение части исходного изображения; кадр - стоп-кадр реального ролика. Схемы и утверждения производителя отделены от проверок собственного изделия.',styles['Ru'])]
 for model in MODELS:
  if model['appendix']:continue
  block=[Paragraph(model['number']+' / '+escape(model['title']),styles['RuH']),Paragraph('<b>Для чего:</b> '+escape(model['focus']),styles['Ru']),Paragraph('<b>Движения:</b> '+escape(model['movements']),styles['Ru']),Paragraph('<b>Что известно и чего нет:</b> '+escape(model['limit']),styles['Ru'])]
  flow.append(KeepTogether(block))
 SimpleDocTemplate(str(OUT/'Analog_analysis_cues_A4_2026-11-21_v2.pdf'),pagesize=(210*mm,297*mm),leftMargin=14*mm,rightMargin=14*mm,topMargin=12*mm,bottomMargin=14*mm).build(flow)

def write_register():
 index={x['number']:x for x in PAGE_INDEX};old={'01':'04','02':'20','03':'01','04':'02','05':'03','06':'05','07':'06','08':'07','09':'08','10':'09','11':'10','12':'12','13':'11','14':'19','15':'13'}
 md=['# Аналоги v2: детали, упражнения и подсказки для физических А3','',
 'По замечаниям автора от 21.11.2026 прежняя печатная подборка пересобрана. В основной файл включены 13 тренажёров и предметных систем; KILO и Kenko вынесены в отдельный файл инвентаря. MoMo, be my form, DYNO, UniGym и NEAR Exergame исключены из новой печати: связь с текущими движениями и мебельной функцией не обоснована. Старые файлы оставлены как история.','',
 'Карточки шириной 60,7 мм (сетка из трёх колонок) и 44,5 мм (четыре колонки у Solo). Фото вписаны с полями; вертикальные изображения уже из-за пропорций. Плотность изображений не ниже 200 ppi, искусственного увеличения пиксельных размеров нет. Принадлежность видна и после вырезания: каждый фрагмент несёт номер аналога и номер карточки. Формат A4, цвет, 100%, односторонняя печать.','',
 '## Порядок и страницы','', '| Новый № | Аналог | Роль | Старый № в перечне v1 | Страницы своего PDF | Карточек |','|---|---|---|---|---|---|']
 for m in MODELS:
  i=index[m['number']];md.append(f'| {m["number"]} | {m["title"]} | {m["kind"]} | {old[m["number"]]} | {", ".join(map(str,i["pages"]))} | {i["cards"]} |')
 md.extend(['','Нумерация относится к этому печатному комплекту. Исходная Excel-таблица не перенумерована и не перезаписана.','',
 '## Что изменилось и почему','',
 'В v1 механически перенесли все 20 позиций раннего поиска, поэтому медицинские концепты оказались рядом с силовыми станциями, а порядок был неудобен для физической раскладки. В v2 первыми идут Speediance и Solo по замечанию автора, затем основные аналоги и близкие мебельные системы. Медицинские примеры общего взаимодействия не заменяют обоснование полезной опоры или хранения и исключены из печати. KILO и Kenko представлены отдельно, потому что это инвентарь, а не тренажёры.','',
 'Для каждого изображения дан конкретный повод для ручной пометки: контакт тела, доступ, перенос детали, соединение, регулировка, программа или приём подачи. Упражнения перечисляются по показанным сценам; дозировки и индивидуальные назначения не добавлялись. Полные перечни упражнений редких концептов не выдумывались.','',
 '## Разбор по аналогам',''])
 for model in MODELS:
  md.extend([f'### {model["number"]}. {model["title"]}',f'**Зачем:** {model["focus"]}',f'**Движения:** {model["movements"]}',f'**Границы:** {model["limit"]}',''])
 md.extend(['## Источники каждой карточки',''])
 html=['<!doctype html><meta charset="utf-8"><title>Источники карточек v2</title><style>body{font:15px Segoe UI,sans-serif;max-width:1100px;margin:30px auto;color:#243b30}table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ddd;padding:8px;text-align:left}img{max-width:140px;max-height:100px}a{color:#21604a}</style><h1>Источники и подсказки по карточкам</h1><table><tr><th>Код</th><th>Снимок</th><th>Смысл</th><th>Источник</th></tr>']
 for m in MODELS:
  for c in m['cards']:
   s=SOURCES[c['asset']];extra=''
   if 'video_seconds' in s:extra=f' Кадр около {s["video_seconds"]:g} с официального ролика.'
   if 'pdf_page' in s:extra+=f' Страница PDF {s["pdf_page"]}.'
   if c.get('crop'):extra+=' Фрагмент исходного изображения.'
   md.extend([f'**{c["id"]} - {c["title"]}.** {c["note"]}{extra}',f'[Страница]({s["page"]})'+(f' · [Прямой файл]({s["url"]})' if s.get('url') else ' · Пользовательское вложение, восстановленное из PPTX')+f' · [Сохранённая копия]({Path(s["path"]).relative_to(DATA.relative_to(ROOT)).as_posix()})',''])
   rel=Path(s['path']).relative_to(DATA.relative_to(ROOT)).as_posix()
   html.append(f'<tr><td>{c["id"]}</td><td><img src="{escape(rel)}"></td><td><b>{escape(c["title"])}</b><br>{escape(c["note"]+extra)}</td><td><a href="{escape(s["page"])}">Страница публикации</a><br><a href="{escape(s.get("url") or s["page"])}">Исходный файл</a><br><a href="{escape(rel)}">Копия для печати</a></td></tr>')
 html.append('</table>');(DATA/'Sources.html').write_text(''.join(html),encoding='utf-8')
 md.extend(['## Сохранение и воспроизводимость','',
 'Полноразмерные скачивания подготовлены в рабочем кэше. В этой папке сохранены качественные копии до 2560 px по длинной стороне, прямые ссылки, нативные пиксельные размеры и контрольные суммы. Это копии для печати, а не обещание сохранения исходного JPEG без перекодирования. Исторические пользовательские оригиналы не изменены. Фрагменты кадрируются только при вёрстке, полный сохранённый снимок доступен рядом.','',
 'Фирменный полный каталог Technogym и инструкция Wall Compact сохранены целиком; у каталога указано происхождение копии с сайта дилера. Исходный каталог содержит авторские фотографии и рисунки производителя.','',
 'Редактируемые данные - cards.json и sources.json. Сборка - python tools/build_analog_detail_print_v2.py. HTML сохраняет такую же сетку. Перед повторной генерацией проверять ручные правки HTML; исходные v1/PPTX/Excel не перезаписываются.'])
 (DATA/'README.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
 (DATA/'page-index.json').write_text(json.dumps(PAGE_INDEX,ensure_ascii=False,indent=2),encoding='utf-8')
 (DATA/'print-quality.json').write_text(json.dumps(PLACEMENTS,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':
 main=build_group([x for x in MODELS if not x['appendix']],'Analog_detail_cards_A4_2026-11-21_v2')
 appendix=build_group([x for x in MODELS if x['appendix']],'Inventory_detail_cards_A4_2026-11-21_v2',True)
 guide();write_register()
 qa=ROOT/'.codex-build/analog-detail-v2/qa';qa.mkdir(exist_ok=True)
 for stem in ['Analog_detail_cards_A4_2026-11-21_v2','Inventory_detail_cards_A4_2026-11-21_v2','Analog_analysis_cues_A4_2026-11-21_v2']:
  doc=pymupdf.open(OUT/(stem+'.pdf'))
  for i,p in enumerate(doc):p.get_pixmap(matrix=pymupdf.Matrix(1.3,1.3)).save(qa/f'{stem}-{i+1:02}.png')
 print(json.dumps(dict(main_pages=main,inventory_pages=appendix,cards=len(PLACEMENTS),min_ppi=min(x['ppi'] for x in PLACEMENTS)),ensure_ascii=False))
