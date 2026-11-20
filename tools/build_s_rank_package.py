"""Illustrated A3 design studies, detailed A4 explanation and editable sources."""
from pathlib import Path
import json,argparse,base64,csv,io
from html import escape
from PIL import Image as PILImage
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Image,Table,TableStyle,KeepTogether
from reportlab.lib.colors import HexColor
from build_spatial_boards import Sheet,C,svg,pdf_draw

ROOT=Path(__file__).resolve().parents[1]
MODEL=ROOT/'research/s-rank-development-2026-11-06.json'
STEM='Functions_and_layouts_A3_2026-11-06'
REPORT='Functions_and_layouts_explained_A4_2026-11-06'

class Board(Sheet):
    def picture(self,path,x,y,w,h):
        path=ROOT/path
        with PILImage.open(path) as im:iw,ih=im.size
        fac=min(w/iw,h/ih);ww=iw*fac;hh=ih*fac
        self.e.append(dict(kind='image',path=str(path),x=x+(w-ww)/2,y=y+(h-hh)/2,w=ww,h=hh))
    def heading(self,t,sub):
        self.text(12,19,t,23,bold=True)
        self.para(12,29,396,sub,11.3,4.6,max_lines=3)
    def note(self,x,y,w,h,b):
        self.text(x,y,h,12.2,C['teal'],True);self.para(x,y+7,w,b,10.7,4.5,max_lines=10)
    def marker(self,x,y,n):
        self.circle(x,y,3.2,C['teal'],C['white'],.5);self.text(x,y+1.1,str(n),10,C['white'],True,anchor='middle')

def movement_board(m):
    s=Board();s.heading('Шаг 1. От действия к нужной части изделия','Для первого сравнения я отобрала по три действия на группу. Это проектные примеры из источников, а не готовая программа занятий. Возраст допуска ещё не определён.')
    for col,group in enumerate(['Дети','Молодые взрослые','Пожилые']):
        x=12+134*col;s.text(x,48,group,14,C['teal'],True)
        for row,c in enumerate(z for z in m['movements'] if z['group']==group):
            y=54+74*row
            s.rect(x,y,128,70,'#F7FAF9',C['light'],.25)
            s.picture(c['image'],x+2,y+2,124,35)
            s.text(x+3,y+43,c['name'],11.1,C['ink'],True)
            brief={'C1':'Нужна панель под ладонь и колено; свободное место перед рукой и за стопой.','C2':'Нужны покрытие пола и отдельный лёгкий предмет, до которого можно дотянуться.','C3':'Нужна поверхность под спину и стопы; на сиденье подниматься не требуется.','Y1':'Панель работает как часть изделия: ладони и колени опираются на неё.','Y2':'Изделие хранит гантель. Сам присед выполняется на свободном полу рядом.','Y3':'Нужны доступ к гантелям и свободная траектория тела, без мешающих кромок.','O1':'Нужно подходящее сиденье и свободное место для стоп и наклона вперёд.','O2':'Нужно удобное место захвата, связанное с устойчивым основанием.','O3':'Нужны сиденье, стопы на полу и свободное место по бокам для локтей.'}[c['id']]
            s.para(x+3,y+50,122,brief,10.4,4.3,max_lines=4)
    s.text(12,286,'Вывод: одна конструкция даёт разные опоры. Часть действий использует само изделие, часть - хранящийся в нём инвентарь.',10.7,C['teal'],True)
    return s

def analog_board(m):
    s=Board();s.heading('Шаг 2. Какие приёмы беру из аналогов','Смотрю, что помогает выбранному действию. На листе - сохранённые фото производителей, сверенные с их материалами. Видео из консультации пока не получены.')
    for i,a in enumerate(m['analogs']):
        x=12+134*i;s.text(x,51,a['name'],15,C['teal'],True)
        s.picture(a['image'],x,59,128,91)
        s.note(x,163,125,'Что беру',a['take'])
        s.note(x,201,125,'Что пока исключаю',a['omit'])
        s.para(x,246,125,a['limit'],10.4,4.4,max_lines=8)
    s.text(12,290,'Фото: Technogym, NOHRD, FITBENCH. Полные ссылки и границы переноса приёмов - в подробном пояснении.',9.2,C['gray'])
    return s

def kit_board(m):
    s=Board();s.heading('Шаг 3. Собираю полезный набор','Общая основа для сравнения: напольная панель, сиденье, перекладина для поддержки и места хранения. Это предложение для разработки; свойства ещё нужно проверить.')
    s.picture('design/assets/s-rank-2026-11-06/function-kit.png',12,49,270,180)
    for n,(x,y) in enumerate([(48,198),(104,100),(107,70),(112,143)],1):s.marker(x,y,n)
    for i,f in enumerate(m['functions']):
        y=53+i*45;s.marker(293,y-1,i+1);s.para(300,y,106,f['name'],12,4.8,bold=True,max_lines=2)
        s.para(294,y+12,113,f['why'],10.5,4.4,max_lines=6)
    s.note(12,249,123,'Для занятий на полу','Одно покрытие показано разложенным и сложенным. Это два состояния одной части, а не два разных коврика.')
    s.note(146,249,123,'Для действий сидя и стоя','Высоту сиденья и перекладины подбираю отдельно. Среднего роста для этих размеров недостаточно.')
    s.note(280,249,126,'Для смены пользователя','Лёгкие предметы видны; тяжёлые убраны отдельно. Способ закрывания и ограничения доступа ещё предстоит выбрать.')
    return s

def concept_board(m,c):
    s=Board();names={'A':'Вариант 1. Открытая скамья','B':'Вариант 2. Сиденье в открытой раме','C':'Вариант 3. Консоль со складным сиденьем'}
    s.heading(names[c['id']],'Один полезный набор, три пользователя по очереди. Цвет показывает контактные поверхности; материал, размеры и допустимые нагрузки пока не выбраны.')
    s.picture(c['image'],12,51,274,183)
    for n,(x,y) in enumerate([(16,53),(153,53),(16,145),(153,145)],1):s.marker(x,y,n)
    labels=[('Собрано',c['what']),('Ребёнок',c['child']),('Молодой взрослый',c['young']),('Пожилой пользователь',c['older'])]
    for i,(head,body) in enumerate(labels):
        y=52+i*47;s.marker(295,y-1,i+1);s.text(302,y,head,12.1,C['teal'],True);s.para(294,y+7,113,body,10.5,4.4,max_lines=8)
    s.note(12,252,123,'Что даёт этот вариант',c['strength'])
    s.note(146,252,123,'Что может мешать',c['weakness'])
    s.note(280,252,126,'Что проверить первым',c['checks'])
    return s

def sequence_board(m):
    s=Board();s.heading('Шаг 4. Подготовка, уборка и поддержка рукой','На примере скамьи показываю, где находится человек и какую часть использует. Это пояснение к одному эскизу, а не выбор окончательной конструкции.')
    s.picture('design/assets/s-rank-2026-11-06/support-story.png',12,49,396,132)
    labels=[
      ('1. Подготовить место','Взрослый достаёт одну напольную панель и раскладывает её перед скамьёй. Место хранения панели при этом пустое. Подход и края покрытия нужно проверить в комнате.'),
      ('2. Вернуть инвентарь','Молодой взрослый кладёт гантели в нижний отдельный отсек. Перед следующим пользователем нужно убрать предметы с пола. Удобство такого низкого доступа ещё предстоит проверить.'),
      ('3. Держаться за перекладину','Пожилой человек стоит за скамьёй и держит заднюю перекладину при небольшом подъёме пяток. Нужен свободный подход сзади; вплотную к стене этот сценарий не работает.')]
    for i,(head,body) in enumerate(labels):
        x=12+134*i;s.text(x,197,head,13,C['teal'],True);s.para(x,207,126,body,11,4.8,max_lines=9)
    s.note(12,262,258,'Что это меняет в компоновке','Доступ нужен не только спереди. Для заднего хвата необходимо оставить место стопам и подходу. Если комната этого не позволяет, положение перекладины нужно пересмотреть.')
    s.note(280,262,126,'Что рисунок ещё не доказывает','Устойчивость и прочность опоры. Связь перекладины с основанием нужно рассчитать и проверить на образце.')
    return s

def comparison_board(m):
    s=Board();s.heading('Шаг 5. Сравниваю использование и смену людей','Общая функция проверяется на разных конструкциях. Оценки ниже - выводы по эскизам, без обмеров и испытаний; окончательный вариант ещё не выбран.')
    for i,c in enumerate(m['concepts']):
        x=12+134*i;s.text(x,49,['1. Скамья','2. Открытая рама','3. Складная консоль'][i],14,C['teal'],True)
        s.picture(c['image'],x,55,128,82)
    widths=[62,111,111,112];xs=[12,74,185,296];y=148
    rows=[
      ['Что меняется','Скамья','Рама','Консоль'],
      ['Перед посадкой','Сиденье уже готово','Сиденье уже готово','Развернуть сиденье и опорную рамку'],
      ['Доступ к лёгкому','Передние ячейки','Боковые ниши','Боковые ячейки'],
      ['Для ребёнка и взрослого','Панель на полу перед корпусом','Панель на полу перед рамой','Сиденье закрыто; панель на полу'],
      ['Главная проверка','Посадка, хват, доступ под сиденьем','Место локтей и стоп между рамами','Фиксаторы, передние опоры и устойчивость'],
      ['Смена пользователя','Убрать панель и предметы перед посадкой','Убрать панель и вернуть предметы','Дополнительно открыть/закрыть сиденье']]
    for j,row in enumerate(rows):
        h=13 if j==0 else 18;s.rect(12,y,396,h,C['pale'] if j%2==0 else '#F8FAFA')
        for i,v in enumerate(row):s.para(xs[i]+2,y+5,widths[i]-4,v,10.3,4.2,bold=j==0 or i==0,max_lines=3)
        y+=h+1
    s.note(12,269,258,'Следующий шаг','Предлагаю сравнить скамью и раму в полноразмерной компоновке. Складной вариант оставить для отдельной проверки механизма; это предложение, а не выбор автора.')
    s.para(280,269,126,'Сначала: посадка, хват и место тела. Затем: прочность, устойчивость, материал и узлы. Все три группы остаются в задании.',10.8,4.5,bold=True,color=C['teal'],max_lines=5)
    return s

def draw_pdf(c,s):
    for e in s.e:
        if e['kind']=='image':c.drawImage(e['path'],e['x']*mm,(297-e['y']-e['h'])*mm,e['w']*mm,e['h']*mm,mask='auto')
        else:
            one=Sheet();one.e=[e];pdf_draw(c,one)

def board_svg(s):
    rows=['<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297">','<rect width="420" height="297" fill="white"/>']
    for e in s.e:
        if e['kind']=='image':
            path=Path(e['path']);b=base64.b64encode(path.read_bytes()).decode()
            with PILImage.open(path) as im:mime='image/jpeg' if im.format=='JPEG' else 'image/png'
            rows.append(f'<image x="{e["x"]}" y="{e["y"]}" width="{e["w"]}" height="{e["h"]}" href="data:{mime};base64,{b}"/>')
        else:
            one=Sheet();one.e=[e];rows.extend(svg(one).splitlines()[2:-1])
    return '\n'.join(rows+['</svg>'])

def report_pages(m):
    pages=[]
    pages.append(dict(title='От упражнения к форме',sections=[
      ('Что я сделала на этом этапе','Я отобрала девять действий для сравнения: по три на каждую обязательную группу. Связала их с частями изделия, посмотрела полезные приёмы трёх сохранённых аналогов и предложила три устройства одного общего набора. Рисунки показывают людей при использовании, а не только мебель в закрытом виде.'),
      ('Как читается этот анализ','Сначала - что делает человек. Затем - к чему прикасаются тело и руки. После этого - что должен дать предмет: поверхность, сиденье, поддержку или доступ к инвентарю. Только тогда я рассматриваю расположение этих частей. Это порядок из консультации 03, 09:18-09:59 и 10:19-11:56.'),
      ('Что общее у всех вариантов','Напольная панель, сиденье, перекладина и распределённое хранение. У ребёнка и молодого взрослого в выбранных примерах основная рабочая часть находится на полу. Для пожилого важны посадка и поддержка стоя. Поэтому единое изделие не означает одну и ту же позу для всех.'),
      ('Какая общность найдена','Общее у детей и молодых взрослых - контакт с полом и место для вытягивания тела. У молодых и пожилых - работа ног из положения стоя, но способы нагрузки и поддержки отличаются. Взять предмет, подготовить место и затем убрать его нужно во всех сценариях. Объединяю эти требования к предмету; одинаковую высоту опор для трёх групп из этого не вывожу.'),
      ('Главный вопрос к этим эскизам','Сиденье и перекладина пока нужны прежде всего пожилому пользователю. Ребёнок работает на съёмной панели; в приседе и наклоне корпус только хранит инвентарь. Поэтому дальше нужно проверить пользу общего корпуса по сравнению с отдельным ковриком, стулом и хранением. Его преимущество должно проявиться в удобстве подготовки, опор и уборки; само наличие ячеек ещё этого не доказывает.'),
      ('Что я не объявляю проверенным','Количество и выбор действий предложены для проектного анализа. Они не составляют индивидуальную программу. Детские примеры взяты из терапии, окончательный возраст допуска ещё не выбран. На этом этапе нет обмеров, испытаний, утверждённых нагрузок, материала или механизма. Цветные изображения созданы ИИ и показывают гипотезы.')]))
    for group in ['Дети','Молодые взрослые','Пожилые']:
        actions=[c for c in m['movements'] if c['group']==group]
        sections=[]
        for a in actions:
            sections.append((a['name']+' ['+a['source']+']',a['action']+' '+a['contact']+'\nРоль изделия: '+a['product']+'\nПроверка: '+a['check']))
        extra={
          'Дети':'Взрослый готовит место и выбирает подходящий пример; затем убирает тяжёлый инвентарь из доступа. Для выбранных действий ребёнку не нужно сидеть на высокой лавочке или забираться на степ. Возможность занятий детей в нашем изделии - обязательное требование автора, но она ещё не доказана этими рисунками.',
          'Молодые взрослые':'В отжимании панель непосредственно поддерживает тело. В приседе и наклоне изделие организует инвентарь, а тело движется на свободном полу. Это разные роли: нельзя приписывать корпусу работу, которую выполняет человек с гантелью. Для добавления тяги ленты или упражнения на скамье нужен отдельный отбор.',
          'Пожилые':'Сиденье и перекладина решают разные задачи. Для посадки нужно проверить стопы и колени, для поддержки стоя - захват и устойчивость корпуса. Пока не предлагаю выполнять отжимание от нашего предмета вместо стены. Возможность помощи при подготовке и смене положения уточняется по конкретному пользователю.'}[group]
        sections.append(('Вывод для формы',extra));pages.append(dict(title=group+': зачем нужны части',sections=sections))
    pages.append(dict(title='Что переношу из аналогов',sections=[(a['name']+' ['+a['source']+']',a['fact']+'\nПолезный приём: '+a['take']+'\nПока не беру: '+a['omit']+'\nГраница вывода: '+a['limit']) for a in m['analogs']]+[
      ('Что изменится после видео','Это первый отбор по сохранённым фото и материалам производителей. Прямые видео из консультации пока не получены. После их получения нужно сверить модель, последовательность открывания, доступ, крепления и эпизод с колёсами. Увиденное в кадре и предположения о скрытом механизме отмечаются отдельно.')]))
    pages.append(dict(title='Три устройства одного набора',sections=[(c['name'],c['what']+'\nПуть усилия: '+c['loadpath']+'\nПреимущество по эскизу: '+c['strength']+'\nВопрос: '+c['weakness']) for c in m['concepts']]+[
      ('Какой вариант проверять первым','Для полноразмерной компоновки предлагаю сначала сравнить постоянную скамью и открытую раму: у них меньше подготовительных операций для посадки. Это предложение помощника. Складной вариант не отвергаю, но он требует отдельной проверки фиксации, передних опор и устойчивости. Ни один вариант автором пока не выбран.')]))
    pages.append(dict(title='Как меняется пользователь',sections=[
      ('Ребёнок → молодой взрослый','Взрослый завершает детский сценарий, возвращает мягкий предмет, проверяет свободный пол и состояние панели. Молодой взрослый использует панель для действия на полу либо убирает её перед работой с гантелью. По рисункам нельзя назначить требуемую толщину и сцепление покрытия.'),
      ('Молодой взрослый → пожилой','Вернуть гантели в предусмотренное место, убрать панель с подхода к сиденью, проверить место стоп. В постоянных вариантах сиденье уже есть; в складном нужно развернуть сиденье и опору без нагрузки, затем проверить фиксацию. Отдельно узнать, может ли человек выполнить подготовку сам или нужна помощь.'),
      ('Что измерять дальше','Длину вытягивания ребёнка и взрослого; положение шва панели; удобную высоту/глубину сиденья; расстояние между боковыми рамами; высоту и форму захвата; движение локтей; положение основания около стоп; наклон к месту хранения. Размер изделия и рабочую зону записывать отдельно. Новых чисел на этом этапе не придумано.'),
      ('Что проверять после компоновки','Устойчивость при вставании и поддержке рукой, скольжение, прогибы и соединения. У складного варианта - фиксаторы, обе передние опоры, возможность защемления и непреднамеренного складывания. Не проверять прочность людьми до расчёта и подготовки подходящего образца.'),
      ('Что пока не добавляю', '\n'.join(d['item']+': '+d['reason'] for d in m['deferred']))]))
    pages.append(dict(title='Источники и происхождение',sections=[(x['id']+' / '+x['title'],x['use'],x['url']) for x in m['sources']]+[
      ('Фото и иллюстрации','Исходные фотографии движений и аналогов сохранены в проекте; их происхождение записано в research/age-group-sources.md и research/analogs/photos/Sources.txt. Фото наклона: Kathryn Alexander / Becca Ewing. Новые цветные рисунки созданы встроенным ImageGen; точные промпты и правки сохранены в design. Рисунки не являются CAD-моделью, фотографией испытаний или подтверждением прочности.')]))
    return pages

def build_report(m,out,pages_override=None,report_name=REPORT):
    target=out/(report_name+'.pdf');styles={
      'title':ParagraphStyle('rt',fontName='SpatialBold',fontSize=20,leading=24,textColor=C['ink'],spaceAfter=13),
      'head':ParagraphStyle('rh',fontName='SpatialBold',fontSize=11.6,leading=14.5,textColor=C['teal'],spaceBefore=8,spaceAfter=5),
      'body':ParagraphStyle('rb',fontName='Spatial',fontSize=10.3,leading=13.8,textColor=C['ink'],spaceAfter=9),
      'url':ParagraphStyle('ru',fontName='Spatial',fontSize=8,leading=10.3,textColor=C['gray'],spaceAfter=7)
    }
    pages=pages_override if pages_override is not None else report_pages(m);story=[];markdown=['# Подробное пояснение: от упражнения к форме','',m['scope'],'',m['stage'],'']
    compact={
      'head':ParagraphStyle('sh',parent=styles['head'],fontSize=10.2,leading=12.4,spaceBefore=5,spaceAfter=3),
      'body':ParagraphStyle('sb',parent=styles['body'],fontSize=9.6,leading=12,spaceAfter=4),
      'url':ParagraphStyle('su',parent=styles['url'],fontSize=7.8,leading=9.5,spaceAfter=3)
    }
    for n,page in enumerate(pages):
        ps=compact if n==len(pages)-1 else styles
        story.append(Paragraph(escape(page['title']),styles['title']));markdown+=['## '+page['title'],'']
        for section in page['sections']:
            head,body=section[:2];items=[Paragraph(escape(head),ps['head']),Paragraph(escape(body).replace('\n','<br/>'),ps['body'])]
            if len(section)>2:
                url=section[2];items.append(Paragraph(f'<link href="{escape(url)}" color="#087F80">{escape(url)}</link>',ps['url']))
            story.append(KeepTogether(items));markdown+=['### '+head,'',body,'']
            if len(section)>2:markdown+=['Источник: '+section[2],'']
        if n<len(pages)-1:story.append(PageBreak())
    def footer(c,doc):
        c.saveState();c.setFont('Spatial',8);c.setFillColor(HexColor(C['gray']));c.drawString(17*mm,12*mm,'Исследовательский этап / 06.11.2026');c.drawRightString(193*mm,12*mm,str(doc.page));c.restoreState()
    doc=SimpleDocTemplate(str(target),pagesize=A4,rightMargin=17*mm,leftMargin=17*mm,topMargin=17*mm,bottomMargin=22*mm,title='От упражнения к форме: подробное пояснение',author='Диплом: исследовательский этап')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    (out/(report_name+'.md')).write_text('\n'.join(markdown),encoding='utf-8')
    return target,len(pages)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=ROOT/'outputs/current');a=ap.parse_args();out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    targets=[out/(STEM+'.pdf'),out/(REPORT+'.pdf'),out/(STEM+'.html')]
    if any(p.exists() for p in targets):raise FileExistsError('Existing deliverables will not be overwritten')
    pdfmetrics.registerFont(TTFont('Spatial','C:/Windows/Fonts/arial.ttf'));pdfmetrics.registerFont(TTFont('SpatialBold','C:/Windows/Fonts/arialbd.ttf'))
    m=json.loads(MODEL.read_text(encoding='utf-8'))
    boards=[movement_board(m),analog_board(m),kit_board(m)]+[concept_board(m,c) for c in m['concepts']]+[sequence_board(m),comparison_board(m)]
    pdf=canvas.Canvas(str(targets[0]),pagesize=(420*mm,297*mm));pdf.setTitle('От движения к функции и устройству изделия');pdf.setAuthor('Диплом: этап S')
    vectors=[]
    for i,b in enumerate(boards,1):
        draw_pdf(pdf,b);pdf.showPage();v=board_svg(b);vectors.append(v);(out/f'{STEM}_{i:02d}.svg').write_text(v,encoding='utf-8')
    pdf.save()
    html='<!doctype html><html lang="ru"><meta charset="utf-8"><title>От движения к форме</title><style>@page{size:A3 landscape;margin:0}body{margin:0;background:#ddd}.sheet{width:420mm;height:297mm;margin:10px auto;break-after:page;background:white}svg{display:block}@media print{body{background:white}.sheet{margin:0}}</style>'+''.join('<div class="sheet">'+v+'</div>' for v in vectors)+'</html>'
    targets[2].write_text(html,encoding='utf-8')
    with (out/'Function_selection_2026-11-06.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f,delimiter=';');w.writerow(['Группа','Действие','Инвентарь','Контакты','Что даёт изделие','Функции','Приём аналога или собственная гипотеза','Что пока исключено и почему','Что проверить','Источник движения'])
        for x in m['movements']:w.writerow([x['group'],x['name'],x['inventory'],x['contact'],x['product'],', '.join(x['functions']),x['analogue'],x['excluded'],x['check'],x['source']])
    report,expected=build_report(m,out)
    build=ROOT/'.codex-build/s-rank-2026-11-06';build.mkdir(parents=True,exist_ok=True)
    (build/'layout.json').write_text(json.dumps([b.e for b in boards],ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'a3_pages':len(boards),'a4_expected_pages':expected,'a3_pdf':str(targets[0]),'a4_pdf':str(report),'html':str(targets[2])}))

if __name__=='__main__':main()
