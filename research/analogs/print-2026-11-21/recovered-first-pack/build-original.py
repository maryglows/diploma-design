from pathlib import Path
from io import BytesIO
import json
import sys

from PIL import Image
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader, PdfWriter, Transformation
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR
from pptx.enum.text import MSO_ANCHOR
from pptx.util import Mm, Pt

here=Path(__file__).resolve().parent
dest=Path('outputs/current')
source=Path(sys.argv[1])
catalog=source/'04_catalog_technogym_bench.pdf'
listing=json.loads((here/'inputs.json').read_text(encoding='utf-8'))
assets=[source/item['name'] for item in listing]
assert all(f.stat().st_size==item['size'] for f,item in zip(assets,listing))
assert len(assets)==13 and catalog.stat().st_size==2802894
ink='202C2D'; green='315D56'; muted='475958'; soft='BAC7C3'
page_h=297
for name,file in [('Regular','segoeui.ttf'),('Bold','segoeuib.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(Path('C:/Windows/Fonts')/file)))
pdf=Canvas(str(here/'base.pdf'),pagesize=(210*mm,297*mm),pageCompression=1)
prs=Presentation()
prs.slide_width=Mm(210);prs.slide_height=Mm(297)
blank=prs.slide_layouts[6]
used=set(); placements=[]; catalog_slots=[]
titles=[]
def slide(title,desc,folio):
    global current
    current=prs.slides.add_slide(blank)
    titles.append(title)
    text(11,19,title,23,True)
    text(11,26,desc,10,color=muted)
    line(11,30,199,30)
    line(11,285,199,285)
    text(11,290,'Промышленный дизайн   /   Анализ аналогов',7.8,color=muted)
    text(182,290,folio,7.8,True,green)
def text(x,y,s,pt=9,bold=False,color=ink):
    font='Bold' if bold else 'Regular'
    width=pdfmetrics.stringWidth(s,font,pt)/mm
    assert x+width<206, (s,width)
    pdf.setFillColor(HexColor('#'+color));pdf.setFont(font,pt)
    pdf.drawString(x*mm,(page_h-y)*mm,s)
    box=current.shapes.add_textbox(Mm(x),Mm(y-pt*0.329),Mm(max(4,width+3)),Mm(pt*0.52+1))
    tf=box.text_frame;tf.clear();tf.word_wrap=False
    tf.margin_top=0;tf.margin_bottom=0;tf.margin_left=0;tf.margin_right=0
    tf.vertical_anchor=MSO_ANCHOR.TOP
    par=tf.paragraphs[0];par.space_before=Pt(0);par.space_after=Pt(0);par.line_spacing=1.0
    run=par.add_run();run.text=s;run.font.name='Segoe UI';run.font.bold=bold;run.font.size=Pt(pt)
    run.font.color.rgb=RGBColor.from_string(color)
def line(x,y,x2,y2,col=soft,width=.5):
    pdf.setLineWidth(width);pdf.setStrokeColor(HexColor('#'+col));pdf.line(x*mm,(page_h-y)*mm,x2*mm,(page_h-y2)*mm)
    shape=current.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Mm(x),Mm(y),Mm(x2),Mm(y2))
    shape.line.color.rgb=RGBColor.from_string(col);shape.line.width=Pt(width)
def note_lines(ys):
    for y in ys: line(11,y,199,y,'CAD3CF',.38)
def image_asset(index,x,y,w,h,crop=None):
    path=assets[index]
    used.add(index)
    with Image.open(path) as im:
        if crop: im=im.crop(crop)
        iw,ih=im.size
        factor=min(w/iw,h/ih);pw=iw*factor;ph=ih*factor
        px=x+(w-pw)/2;py=y+(h-ph)/2
        if path.suffix.lower() in ('.jpg','.jpeg') and not crop: data=path.read_bytes()
        else:
            buf=BytesIO();im.convert('RGB').save(buf,'PNG');data=buf.getvalue()
        pdf.drawImage(ImageReader(BytesIO(data)),px*mm,(page_h-py-ph)*mm,pw*mm,ph*mm)
        current.shapes.add_picture(BytesIO(data),Mm(px),Mm(py),Mm(pw),Mm(ph))
        placements.append((path.name,round(iw*25.4/pw)))
def orig_page(num,x,y,w):
    image_path=here/f'cat-{num:02}.png'
    ref=catalog_pdf.pages[num-1]
    sw,sh=float(ref.mediabox.width),float(ref.mediabox.height)
    h=w*sh/sw
    current.shapes.add_picture(str(image_path),Mm(x),Mm(y),Mm(w),Mm(h))
    catalog_slots.append((num,x,y,w,h))
def caption(x,y,head,detail=None):
    text(x,y,head,10,True)
    if detail:text(x,y+4.7,detail,8.6,color=muted)
def close(): pdf.showPage()
catalog_pdf=PdfReader(str(catalog))
# Each source photo appears once. Only empty margins are removed from the two designated views.
slide('NOHRD StepBox','Съёмные панели, хранение и крепление эспандера','1 / 4')
image_asset(8,11,34,112,63)
caption(11,102,'Снятая боковина служит отдельным степом.')
image_asset(11,129,35,69,56,(202,285,1598,1035))
caption(129,95,'Закрытая скамья')
text(129,100,'Панель закрывает инвентарь.',8.6,color=muted)
line(11,108,199,108)
image_asset(10,11,112,45,45)
caption(60,125,'Как открывается')
text(60,131,'Боковину наклоняют',8.8,color=muted)
text(60,136,'и снимают с корпуса.',8.8,color=muted)
image_asset(9,111,112,45,45)
caption(161,125,'Крепление')
text(161,131,'Карабин и кольцо',8.8,color=muted)
text(161,136,'под основанием.',8.8,color=muted)
line(11,162,199,162)
text(11,170,'Профиль тренировок',13,True)
image_asset(12,11,174,119,99)
text(137,187,'Легенда диаграммы',10,True,green)
for k,(value,label) in enumerate([('30%','Сила и рост мышц'),('25%','Кардио и выносливость'),('15%','Мышечная выносливость'),('10%','Кор и стабилизация'),('10%','Координация и баланс'),('10%','Подвижность')]):
    yy=197+8*k
    text(137,yy,value,9,True,green);text(149.5,yy,label,8.7)
text(137,251,'Так производитель описывает',8.4,color=muted)
text(137,256,'направления тренировки.',8.4,color=muted)
text(11,280,'Диаграмма NOHRD и четыре фотографии из авторской подборки.',8,color=muted)
close()
slide('Technogym Bench','Скамья в интерьере и три способа использовать комплект','2 / 4')
for index,x,y,head,detail in [
 (0,11,34,'Хранение гантелей','Место каждой гантели видно сбоку.'),
 (4,108,34,'Жим гантелей лёжа','Спина опирается на скамью, стопы стоят на полу.'),
 (6,11,146,'Упражнение на равновесие','Кисть и колено опираются на скамью.'),
 (2,108,146,'Разведение рук с эспандерами','В кадре видны рукоятки и ход обеих лент.')]:
    image_asset(index,x,y,91,91);caption(x,y+97,head,detail)
line(11,257,199,257)
text(11,266,'Что видно в подаче',10,True,green)
text(11,272,'Один ракурс показывает устройство скамьи, три других дают масштаб по человеку и показывают движение.',9)
close()
slide('FITBENCH FREE','Боковые ячейки, торцевой отсек и подъёмная спинка','3 / 4')
image_asset(7,11,35,116,57,(47,398,1057,820))
caption(11,96,'Скамья со сложенной спинкой')
text(135,54,'Боковая сторона',10,True,green)
text(135,62,'Гантели размещены',9)
text(135,67,'в отдельных ячейках.',9)
text(135,75,'Рукоятки открыты',9)
text(135,80,'для захвата сбоку.',9)
line(11,103,199,103)
image_asset(3,26,108,53,53)
image_asset(1,126,108,53,53)
caption(11,167,'Поднятая спинка','Под ней видна наклонная опора.')
caption(109,167,'Эспандер на спинке','Хорошо видно верхнее крепление.')
line(11,179,199,179)
image_asset(5,13,186,55,41)
caption(78,200,'Торцевой отсек')
text(78,207,'Крупный план показывает положение гири и мяча',9,color=muted)
text(78,212,'рядом с боковым рядом гантелей.',9,color=muted)
line(11,234,199,234)
text(11,244,'Заметки по конструкции и подаче',10,True,green)
note_lines([255,265,275])
close()
slide('Technogym Bench','Страницы 8–11 каталога производителя','4 / 4')
text(11,40,'Упражнения',11,True,green)
text(93,40,'Инвентарь в комплекте',11,True,green)
orig_page(8,11,48,78)
orig_page(9,90.5,45,108.5)
caption(11,121,'Одна скамья, три положения')
text(11,127,'Фигуры собраны в одной композиции.',8.2,color=muted)
text(93,141,'Утяжелители для кистей, эспандеры, гантели и коврик.',8.4,color=muted)
line(11,149,199,149)
text(11,160,'Где хранится каждый предмет',12,True,green)
orig_page(10,11,167,94)
orig_page(11,105,167,94)
text(11,255,'Разворот сохранён целиком. Выноски связывают общий вид скамьи с держателями гантелей,',9)
text(11,261,'отсеками для лент, коврика и утяжелителей. Справа отдельно показаны колёса.',9)
text(11,278,'Источник изображений и английских подписей: каталог Technogym Bench, с. 8–11.',8,color=muted)
close()
pdf.save()
assert used==set(range(13)) and len(catalog_slots)==4
assert len(prs.slides)==4
prs.core_properties.title='Три домашних тренажёра. Листы анализа А4'
prs.core_properties.subject='NOHRD StepBox, Technogym Bench, FITBENCH FREE'
prs.save(dest/'Trainer_photos_A4.pptx')
writer=PdfWriter()
for i,base in enumerate(PdfReader(str(here/'base.pdf')).pages):
    page=writer.add_page(base)
    if i==3:
        for num,x,y,w,h in catalog_slots:
            src=catalog_pdf.pages[num-1]
            scale=w*mm/float(src.mediabox.width)
            page.merge_transformed_page(src,Transformation().scale(scale).translate(x*mm,(page_h-y-h)*mm),over=True,expand=False)
    writer.add_outline_item(titles[i]+(' | каталог' if i==3 else ''),i)
writer.add_metadata({'/Title':'Три аналога домашнего тренажёра | A4','/Subject':'Фотографии и каталог для цветной печати'})
with (dest/'Trainer_photos_A4.pdf').open('wb') as f:writer.write(f)
print('Photos and effective ppi:',[(name.encode('ascii','backslashreplace').decode(),dpi) for name,dpi in placements])

