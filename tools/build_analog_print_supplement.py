"""Build cut-out A4 photo sheets from verified, preserved image files.

Run from any directory. Photo originals and prior PDF/PPTX are never overwritten.
The JSON layout and HTML are editable sources; report includes effective print PPI.
"""
from pathlib import Path
from io import BytesIO
from html import escape
from urllib.parse import urlparse
import base64
import hashlib
import json
import math

from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader, PdfWriter
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'research/analogs/print-2026-11-21'
OUT=ROOT/'outputs/current'
NAME='Analogs_remaining_photos_A4_2026-11-21'
for name,font in [('R','segoeui.ttf'),('B','segoeuib.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(Path('C:/Windows/Fonts')/font)))

def item(code,caption): return dict(code=code,caption=caption)
def section(number,title,subtitle,images,note):
    return dict(number=number,title=title,subtitle=subtitle,images=[item(*p) for p in images],note=note)

S={
'speed':section('04','Speediance Gym Monster 2','Напольная тросовая станция',[
    ('C01','Раскладка станции и инвентаря'),('C02','Платформа в сложенном виде'),('C03','Скамья и станция раздельно')],
    'Для анализа: место раскрытия платформы и отдельное место для скамьи.'),
'wall':section('05','NOHRD Wall Compact','Вертикальное хранение',[
    ('C04','Общий вид корпуса'),('C05','Экран и ряды хранения'),('C06','Деталь держателей грузов')],
    'Для анализа: высота каждого ряда и видимость предметов. Крепление к стене не переносим в свой проект.'),
'tonal':section('06','Tonal 2','Рычаги, работа с тросом, хват',[
    ('C55','Станция в интерьере'),('C56','Человек в рабочей зоне'),('C57','Кнопка на рукоятке')],
    'Для анализа: рабочая зона шире корпуса; рукоятка одновременно передаёт усилие и команду.'),
'solo':section('20','Solo Fitness','Signature Storage Bench (Adjustable)',[
    ('C10','Открытые ячейки под сиденьем'),('C11','Три положения спинки'),('C13','Хранение инвентаря рядом')],
    'Для анализа: доступ к весам при поднятой спинке. Размерная схема вынесена отдельно.'),
'kilo':section('19','KILO / Kilo_home','Два отдельных предмета одного бренда',[
    ('C09','3 KILO: общий вид'),('C45','4 KILO: предмет в интерьере')],
    'Для анализа: кольцевой хват, устойчивое положение при хранении и восприятие груза как предмета интерьера.'),
'kenko':section('13','Kenko','Aerobic Dumbbells Maple',[
    ('C28','Масштаб относительно человека'),('C29','Пара гантелей'),('C30','Подача размерного ряда')],
    'Для анализа: парность, тактильная поверхность и различимость предметов. Фото не задаёт нагрузку.'),
'cassina':section('07','Cassina Ottagono','UNA / UNLESS, Giulia Foscari',[
    ('C14','Закрытое и открытое состояния'),('C15','Работа рядом со шкафом')],
    'Для анализа: направление открывания дверей, свет и расположение инвентаря. Фото: Delfino Sisto Legnani.'),
'atleast':section('10','AT LEAST','Home Workout Bench / концепт',[
    ('C22','Скамья в жилом интерьере'),('C47','Открытый отсек сверху'),('C48','Закрытый корпус')],
    'Для анализа: порядок открывания и организация отсека. Изображения концепта не являются испытанием.'),
'sana':section('08','Javorina SANA','Tomas Kral / фото Lukas Pelech',[
    ('C16','Состояние у стены'),('C17','Съёмные элементы и скамья')],
    'Для анализа: хранение снятой детали и различие бытового и рабочего состояния. Чертёж - на отдельном листе.'),
'unigym':section('17','UniGym','Home Rehabilitation Robot / конкурсный проект',[
    ('C38','Корпус и трос'),('C39','Сменные насадки'),('C40','Раскладка принадлежностей')],
    'Для анализа: как различить, сменить и убрать насадку. Медицинские результаты по изображениям не выводятся.'),
'golden':section('09','Goldenhome','Integrated Fitness Cabinet',[
    ('C19','Встроенный корпус и хранение'),('C21','Общий вид в пространстве')],
    'Для анализа: что остаётся на виду, что закрывается и какое место занимают открытые части шкафа.'),
'kettler':section('11','KETTLER HOI RIDE+','Велоэргометр / два цветовых исполнения',[
    ('C23','Вид сбоку под углом'),('C24','Посадка и консоль спереди')],
    'Для анализа: подход к сиденью и расположение управления. Педалирование не входит в текущие 18 движений.'),
'pent':section('12','PENT. JOANA','Pilates Reformer',[
    ('C25','Полный вид реформера'),('C26','Пружины и регулировки'),('C27','Мягкие опоры и рукоятки')],
    'Для анализа: граница мягкой поверхности, дерева и металла; подача рабочего узла крупным планом.'),
'momo':section('14','MoMo','Modular Physiotherapy Kit / проект',[
    ('C31','Модули в единой системе'),('C34','Взаимодействие двух рук'),('C35','Соединение деталей')],
    'Для анализа: разные поверхности, расположение органов управления и наглядная модульность.'),
'bemy':section('15','be my form','Minseon Lim / студенческий проект iF',[
    ('C51','Предмет и носимый элемент'),('C52','Два сценария использования')],
    'Для анализа: хранение на стене и отдельный датчик. Сюжеты проекта не подтверждают лечебный эффект.'),
'dyno':section('16','DYNO','Контроллер и цифровая игра / конкурсный проект',[
    ('C36','Контроллер в руке'),('C37','Подача игровых сценариев')],
    'Для анализа: хват, управление и связь предмета с изображением на экране.'),
}

PAGES=[
 dict(sections=[S['speed'],S['wall']]),
 dict(sections=[S['tonal'],S['solo']]),
 dict(sections=[S['kilo'],S['kenko']]),
 dict(sections=[S['cassina'],S['atleast']]),
 dict(sections=[S['sana'],S['unigym']]),
 dict(sections=[S['golden'],S['kettler']]),
 dict(sections=[S['pent'],S['momo']]),
 dict(sections=[S['bemy'],S['dyno']]),
 dict(full=True,number='18',title='NEAR Exergame',subtitle='Платформа и схема авторов проекта',images=[
     dict(code='C53',caption='Вид измерительной платформы',box=[30,30,150,82]),
     dict(code='C54',caption='Схема: пользователь, игра и обработка сигнала',box=[26,134,158,119])],
     note='Схема показывает замысел проекта. Заявленные прогнозы восстановления здесь не проверялись.'),
 dict(full=True,number='20',title='Solo Fitness / размеры',subtitle='Схема производителя; не чертёж собственного изделия',images=[
     dict(code='C12',caption='Signature Storage Bench (Adjustable)',box=[15,34,180,210])],
     note='Сохраняем исходные размерные обозначения. Схема дана для анализа компоновки.'),
 dict(full=True,number='08',title='SANA / размерная схема',subtitle='WallBar with bench / схема производителя',images=[
     dict(code='C18',caption='Система, скамья и расположение элементов',box=[15,27,180,244])],
     note='Размерная схема конкретной комплектации. Настенное крепление отличается от условия нашего проекта.'),
 dict(full=True,number='17',title='UniGym / раскладка',subtitle='Принадлежности и места хранения / конкурсный проект',images=[
     dict(code='C40',caption='Расположение сменных элементов на подставке',box=[15,35,180,137]),
     dict(code='C39',caption='Насадки показаны отдельно от базы',box=[52,190,106,72])],
     note='Раскладка показывает состав и логику хранения; совместимость с нашими движениями требует проверки.')
]

def wrapped(value,font,size,width):
    words=value.split(); lines=[]; line=''
    for word in words:
        candidate=f'{line} {word}'.strip()
        if line and pdfmetrics.stringWidth(candidate,font,size)>width*mm:
            lines.append(line);line=word
        else:line=candidate
    if line:lines.append(line)
    return lines

def build():
    records={x['candidate']:x for x in json.loads((ASSETS/'candidates.json').read_text('utf-8'))}
    # Replace the old redirected Ottagono project page with its observed current URL.
    for code in ['C14','C15']:
        records[code]['page']='https://una-unless.org/en/work/ottagono-x-cassina---technogym'
    pdf=canvas.Canvas(str(OUT/f'{NAME}.pdf'),pagesize=(210*mm,297*mm),pageCompression=1)
    pdf.setTitle('Фотографии и схемы остальных аналогов для вырезания, А4')
    html=[]; placements=[]

    def txt(x,y,value,size=9,bold=False,color='#253D3A',width=190):
        font='B' if bold else 'R';lines=wrapped(value,font,size,width)
        pdf.setFillColor(HexColor(color));pdf.setFont(font,size)
        for i,line in enumerate(lines):
            yy=y+i*size*.43
            pdf.drawString(x*mm,(297-yy)*mm,line)
            html.append(f'<div class="t" style="left:{x}mm;top:{yy-size*.28}mm;font-size:{size}pt;font-weight:{700 if bold else 400};color:{color}">{escape(line)}</div>')
        return len(lines)

    def rule(x,y,w):
        pdf.setStrokeColor(HexColor('#D6DFDC'));pdf.setLineWidth(.45);pdf.line(x*mm,(297-y)*mm,(x+w)*mm,(297-y)*mm)
        html.append(f'<div class="rule" style="left:{x}mm;top:{y}mm;width:{w}mm"></div>')

    def photo(rec,box,caption,page):
        code=rec['candidate'];path=ROOT/rec['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==rec['sha256']
        im=Image.open(path);iw,ih=im.size
        x,y,w,h=box
        # A minimum 150 PPI limits physical size; no artificial upscaling of source pixels.
        scale=min(w/iw,h/ih,25.4/150)
        pw,ph=iw*scale,ih*scale;px=x+(w-pw)/2;py=y+(h-ph)/2
        # Preserve full downloaded originals separately; the print PDF needs at most
        # 450 PPI. Photo compression does not change the source files or HTML.
        rgb=im.convert('RGB')
        target=(max(1,round(pw/25.4*450)),max(1,round(ph/25.4*450)))
        rgb.thumbnail(target,Image.Resampling.LANCZOS)
        buf=BytesIO()
        if code in {'C11','C12','C18','C37','C54'}:
            rgb.save(buf,format='PNG',compress_level=4)
        else:
            rgb.save(buf,format='JPEG',quality=94,subsampling=0,optimize=True)
        data=buf.getvalue()
        pdf.drawImage(__import__('reportlab.lib.utils',fromlist=['ImageReader']).ImageReader(BytesIO(data)),px*mm,(297-py-ph)*mm,pw*mm,ph*mm)
        pdf.linkURL(rec['page'],(px*mm,(297-py-ph)*mm,(px+pw)*mm,(297-py)*mm),relative=0)
        ppi=round(rgb.width*25.4/pw)
        placements.append(dict(code=code,page=page,caption=caption,path=rec['path'],pixels=[iw,ih],pdf_pixels=list(rgb.size),printed_mm=[round(pw,2),round(ph,2)],ppi=ppi,source_page=rec['page'],image_url=rec['image_url'],sha256=rec['sha256']))
        src=path.relative_to(OUT) if path.is_relative_to(OUT) else Path('../../')/path.relative_to(ROOT)
        html.append(f'<a href="{escape(rec["page"])}"><img src="{src.as_posix()}" style="left:{px:.3f}mm;top:{py:.3f}mm;width:{pw:.3f}mm;height:{ph:.3f}mm"></a>')
        lines=txt(x,y+h+4,f'{code}  {caption}',7.7,True,width=w)
        domain=urlparse(rec['page']).hostname.removeprefix('www.')
        yy=y+h+4+lines*3.3
        txt(x,yy,domain,6.8,color='#61716B',width=w)
        pdf.linkURL(rec['page'],(x*mm,(297-yy-2)*mm,(x+w)*mm,(297-yy+2)*mm),relative=0)

    for pno,page in enumerate(PAGES,1):
        html.append('<section class="page">')
        if page.get('full'):
            txt(11,14,f'{page["number"]}  {page["title"]}',18,True)
            txt(11,21,page['subtitle'],8.3,color='#61716B')
            for v in page['images']:photo(records[v['code']],v['box'],v['caption'],pno)
            txt(11,283,page['note'],7.5,color='#61716B',width=185)
        else:
            for sec,top in zip(page['sections'],[9,146]):
                txt(11,top+6,f'{sec["number"]}  {sec["title"]}',17,True)
                txt(11,top+13,sec['subtitle'],8.4,color='#61716B')
                n=len(sec['images']);gap=5;w=(188-gap*(n-1))/n
                for j,v in enumerate(sec['images']):
                    photo(records[v['code']],[11+j*(w+gap),top+18,w,87],v['caption'],pno)
                txt(11,top+123,sec['note'],8.2,color='#425950',width=185)
                if top==9:rule(11,139,188)
        txt(11,290,'Фотографии для вырезания  /  Цвет, A4, 100%  /  Источники: C01-C57',6.6,color='#61716B')
        txt(184,290,f'{pno} / {len(PAGES)}',6.6,color='#61716B',width=20)
        html.append('</section>');pdf.showPage()
    pdf.save()
    css='''<style>@page{size:A4;margin:0}body{margin:0;background:#eee;font-family:"Segoe UI",sans-serif}.page{position:relative;width:210mm;height:297mm;background:white;margin:8mm auto;break-after:page;overflow:hidden}.t{position:absolute;white-space:nowrap;line-height:1}img{position:absolute;object-fit:contain}.rule{position:absolute;border-top:.45pt solid #D6DFDC}@media print{body{background:white}.page{margin:0}}</style>'''
    (OUT/f'{NAME}.html').write_text('<!doctype html><meta charset="utf-8"><title>Фотографии аналогов А4</title>'+css+''.join(html),encoding='utf-8')
    (ASSETS/'layout.json').write_text(json.dumps(PAGES,ensure_ascii=False,indent=2),encoding='utf-8')
    (ASSETS/'print-quality.json').write_text(json.dumps(placements,ensure_ascii=False,indent=2),encoding='utf-8')

    # A convenience bundle; the unchanged first PDF remains a separate deliverable.
    writer=PdfWriter()
    writer.append(str(OUT/'Trainer_photos_A4.pdf'))
    writer.append(str(OUT/f'{NAME}.pdf'))
    writer.write(str(OUT/'Analogs_ALL_photos_A4_2026-11-21.pdf'))

    chosen={x['code'] for x in placements}
    md=['# Фотографии аналогов: подборка для печати, 21.11.2026','',
        'Первый комплект: 4 А4, 3 аналога и каталог Technogym. Дополнение: 12 А4, остальные 17 позиций. Общий PDF: 16 А4, все 20 позиций таблицы. Нумерация 01-20 соответствует перечню из 18 прежних позиций плюс KILO и Solo, а не порядку вкладок Excel.','',
        'Для каждого изображения ниже даны страница публикации, прямая ссылка и локальный файл. Коды Cxx напечатаны под картинками. Фотографии в PDF также кликабельны. Печатать: A4, цвет, 100%, одна страница на листе, односторонняя печать для вырезания. Исходники не увеличены искусственно; размер ограничен минимумом 150 ppi в дополнении. Качество первого комплекта унаследовано без изменений.','',
        '## Что отобрано и зачем','',
        '| Позиция | Что изучать по изображениям | Предел вывода |','|---|---|---|']
    for s in S.values():md.append(f'| {s["number"]}. {s["title"]} | {s["note"]} | Подписи являются проектным анализом; фото не подтверждает размеры нашего изделия или удобство для всех групп. |')
    md.extend(['| 18. NEAR Exergame | Край платформы, вход на поверхность и подача цепочки обратной связи. | Описание разработчиков; медицинская эффективность и точность прогноза здесь не оценивались. |','',
        '## Источники изображений дополнения',''])
    for code in sorted(chosen):
        r=records[code]; pp=[x for x in placements if x['code']==code]
        md.extend([f'### {code} - {pp[0]["caption"]}',f'- [Страница публикации]({r["page"]})',f'- [Прямое изображение]({r["image_url"]})',f'- [Сохранённый файл]({(ROOT/Path(r["path"])).relative_to(ASSETS).as_posix()})',f'- Размер: {r["pixels"][0]} × {r["pixels"][1]} px; печать: '+', '.join(f'лист {a["page"]}, {a["printed_mm"][0]} × {a["printed_mm"][1]} мм, {a["ppi"]} ppi' for a in pp)+'.',f'- SHA-256: `{r["sha256"]}`.',''])
    md.extend(['## Восстановление первого комплекта','',
        'PDF и PowerPoint сохранены побайтно без изменения. 17 встроенных изображений извлечены из PowerPoint в `recovered-first-pack/`: первые 13 - подборка автора, последние 4 - растровые страницы каталога. Два изображения StepBox были обрезаны в прежней сборке, часть FITBENCH была преобразована в PNG. Извлечённые файлы не выдаются за полные оригиналы пользовательских вложений. Векторная выборка каталога стр. 8-11 сохранена отдельно. Полного загруженного каталога и видео в доступных локальных файлах не найдено.','',
        'Сопоставление первых 13 файлов с присланными названиями и ссылками производителя см. `recovered-first-pack/README.md`. Данные о происхождении не заменяют отсутствующие исходные вложения.','',
        '## Ограничения','',
        'Сравниваются серийные изделия, коллекции инвентаря и конкурсные проекты. Статус концепта сохранён в подписях. Лечебные обещания источников не подтверждались. Новые цены, материалы и технические характеристики этим подбором не обновлялись; исходная таблица сохранена без изменений. Не все старые ссылки доступны прямым HTTP-запросом; be my form и NEAR получены через публичную страницу в браузере.','',
        'Всего проверено 57 ссылок-кандидатов: 55 изображений получены; C08 недоступен (403), C42 сначала недоступен прямым запросом, его содержимое затем получено через браузер под кодом C54. Все успешные кандидаты сохранены, включая не вошедшие в печать. Исходные страницы и авторы остаются источниками изображений.','',
        'Сборка: `python tools/build_analog_print_supplement.py`. JSON в `layout.json` - сохранённая структура страниц; правки HTML можно делать вручную, повторная генерация их перезапишет. Предыдущие версии не перезаписываются.'])
    (ASSETS/'README.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    (ASSETS/'used-sources.json').write_text(json.dumps([records[k] for k in sorted(chosen)],ensure_ascii=False,indent=2),encoding='utf-8')
    # Render the final artifact for visual QA. No inference from text extraction alone.
    qa=ROOT/'.codex-build/analog-print-recovery-qa';qa.mkdir(exist_ok=True)
    doc=pymupdf.open(OUT/f'{NAME}.pdf')
    for i,page in enumerate(doc):page.get_pixmap(matrix=pymupdf.Matrix(1.3,1.3)).save(qa/f'page-{i+1:02}.png')
    print(json.dumps(dict(pages=len(PAGES),placements=len(placements),unique_images=len(chosen),min_ppi=min(x['ppi'] for x in placements),total_pages=len(PdfReader(OUT/'Analogs_ALL_photos_A4_2026-11-21.pdf').pages)),ensure_ascii=False))

if __name__=='__main__':build()
