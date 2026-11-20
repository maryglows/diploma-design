"""Five printable A3 research sheets; editable SVG, explicit assumed envelopes."""
from pathlib import Path
import sys, json, math, argparse, base64
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from build_spatial_boards import Sheet, C, svg, pdf_draw, figure

ROOT=Path(__file__).resolve().parents[1]
STEM='Movement_and_form_studies_A3_2026-11-06'
MODEL=ROOT/'research/movement-envelopes-2026-11-06.json'
ASSET=ROOT/'design/assets/concepts-2026-11-06/form-studies.png'

def title(s,t,sub):
    s.text(12,19,t,23,bold=True)
    s.para(12,29,396,sub,11,4.5,max_lines=3)

def block(s,x,y,w,head,body,size=10):
    s.text(x,y,head,12,C['teal'],True)
    return s.para(x,y+8,w,body,size,4.4,max_lines=10)

def functions(m):
    s=Sheet();title(s,'Общие действия → функции изделия','Я сопоставила движения из возрастных листов. Общность движения помогает выделить функцию, но не задаёт одинаковые высоты, нагрузки и размеры.')
    cols=[12,55,139,223,307,408]
    headers=['Функция','Детские примеры','Молодой взрослый','Старший пользователь','Следствие для формы']
    for i,h in enumerate(headers):s.text(cols[i]+2,51,h,10.3,C['teal'],True)
    rows=[
    ['Контакт с полом','Четвереньки; мост; рука и нога [S7]','Колени/ладони; боковая опора [S3, S10]','Не основной сценарий: переход на пол проверить отдельно','Отдельный коврик/панель; кромки вне контакта'],
    ['Сесть / встать','Низкая игровая поза не равна взрослому сиденью','Посадка для подготовки и смены инвентаря','Посадка, наклон вперёд, вставание [S4]','Высоту подбирать по ногам и позе, не по медиане роста'],
    ['Оттолкнуться','Ладони на стене [S7]','Ладони и колени на полу [S3]','Ладони на стене [S4]','Вертикальная и напольная опоры различаются по силам'],
    ['Потянуть','Дотянуться до предмета [S7]','Гантели к корпусу в наклоне [S3]','Лента в прежнем листе; поворот сидя [S5]','Захват и свободный ход локтя; анкер не задан'],
    ['Шаг / перенос','Мяч, предмет, смена точки опоры','Подход к гантелям; наклон [S2]','Боковые шаги; поддержка рядом [S6]','Свободный пол; неподвижное хранение вне маршрута'],
    ['Достать / убрать','Доступ к лёгкому предмету при участии взрослого','Раздельные места для гантелей, лент и коврика','Доступ без лишнего наклона и тянущегося захвата','Лёгкое - доступно; тяжёлое - низко, доступ и устойчивость проверить']]
    y=57
    for n,row in enumerate(rows):
        s.rect(12,y,396,22,C['pale'] if n%2==0 else '#F7F9F9')
        for i,t in enumerate(row):s.para(cols[i]+2,y+5,cols[i+1]-cols[i]-4,t,9.5,3.8,bold=i==0,max_lines=5)
        y+=23
    block(s,12,207,123,'База для сравнения','Свободная зона пола, отдельная мягкая поверхность, понятные места хранения. Сначала проверяю подготовку и уборку, затем добавляю силовую функцию.')
    block(s,148,207,123,'Инвентарь по задаче','Гантели: наклон/тяга/присед. Лента: отдельный сценарий сопротивления. Мяч: взаимодействие. Стул или поддержка: отдельная опорная функция, не аксессуар хранилища.')
    block(s,284,207,123,'Что не объединяю автоматически','Сиденье ≠ опора для отжимания ≠ анкер ленты. Одинаковая форма движения не доказывает пригодность одной конструкции для всех возрастов.')
    s.para(12,278,396,'Основания S1–S7: ACE, NASM, NHS, NHFT; полные ссылки и границы применения - в исследовательской записке. Подбор движений здесь служит анализу конструкции.',9.3,4,max_lines=2)
    return s

def mini_plan(s,c,x,y):
    k=60;L=c['L']/k;W=c['W']/k;d=300/k
    left=x+d;top=y+d
    s.rect(x,y,L+(d if c.get('wall_side') else 2*d),W+2*d,C['pale'],C['teal'],.3,(1.1,.8))
    if c.get('wall_side'):
        left=x;L=c['L']/k
        s.line(x,y,x,y+W+2*d,C['ink'],.8)
    s.rect(left,top,L,W,None,C['ink'],.4)
    cx=left+L/2;cy=top+W/2
    s.line(cx-1,cy,cx+1,cy,C['pink'],.3);s.line(cx,cy-1,cx,cy+1,C['pink'],.3)
    s.arrow(cx,cy,left+L,top,C['pink'],.25)
    # Pictogram only, not an anthropometric body drawing.
    if c['pose'] in ['floor','reach']:
        s.line(left+L*.2,cy,left+L*.73,cy,C['gray'],.8);s.circle(left+L*.8,cy,1.5,C['white'],C['gray'],.4)
        s.poly([(left+L*.4,cy),(left+L*.25,cy+W*.3),(left+L*.1,cy+W*.3)],C['gray'],.6)
        s.poly([(left+L*.65,cy),(left+L*.72,cy-W*.3),(left+L*.95,cy-W*.3)],C['gray'],.6)
    elif c['pose']=='ball':
        for a in [.22,.78]:s.circle(left+L*a,cy,2,C['white'],C['gray'],.5)
        s.circle(cx,cy,1.4,C['goldpale'],C['gold'],.4);s.arrow(left+L*.35,cy,left+L*.65,cy,C['gold'],.3,both=True)
    elif c['pose']=='walk':
        for a in [.2,.45,.7]:s.circle(left+L*a,cy,1.3,None,C['gray'],.4)
        s.arrow(left+L*.15,cy+4,left+L*.85,cy+4,C['teal'],.3)
    else:
        if c['pose'] in ['chair','seated']:s.rect(left+2,cy-3,5,6,C['light'],C['gray'],.4)
        s.circle(cx,cy,2,C['white'],C['gray'],.5);s.line(cx,cy-5,cx,cy+5,C['gray'],.65)
    s.text(x,y+W+2*d+5,'План 1:60 / У',8.3,C['gray'])

def zones(m):
    s=Sheet();title(s,'Рабочие контуры девяти действий','Тёмный контур - пробный охват тела, опор и инвентаря (У). Бирюзовый - пробная зона с добавкой d = 300 мм. У стены добавка только с трёх сторон.')
    s.text(12,43,'Радиус r - от центра тёмного прямоугольника до угла: r = ½√(L² + W²). Это расчёт габарита, не радиус руки или безопасности.',9.8,C['pink'])
    for i,c in enumerate(m['cases']):
        x=12+(i%3)*134;y=51+(i//3)*78
        s.rect(x,y,128,74,'#F9FAFA',C['light'],.3)
        s.text(x+3,y+6,c['id']+'  '+c['title'],10.3,C['teal'],True)
        s.text(x+3,y+12,c['group']+' / '+c['source'],8.4,C['gray'])
        mini_plan(s,c,x+3,y+21)
        Lp=c['L']+600-(300 if c.get('wall_side') else 0);Wp=c['W']+600
        r=.5*math.hypot(c['L'],c['W'])/1000;A=Lp*Wp/1e6
        s.text(x+56,y+24,f"Контур: {c['L']} × {c['W']} У",9.2)
        s.text(x+56,y+31,f'С добавкой: {Lp} × {Wp} У',9.2)
        s.text(x+56,y+38,f'S = {A:.2f} м²; r = {r:.2f} м Р'.replace('.',','),9.6,C['pink'],True)
        s.para(x+56,y+46,68,c['check'],9.2,3.9,max_lines=6)
    s.para(12,288,396,'Все размеры контуров и d выбраны для пробной раскладки. Они не получены обмером и не являются нормами. Масштаб верен только при печати А3 / 100%.',9,3.8,max_lines=1)
    return s

def heights(m):
    s=Sheet();title(s,'Высота, радиусы и доступ к инвентарю','Проверяю объём движения по всем фазам. Рост стоя не определяет верхнюю точку гантели; площадь коврика не описывает подход, разворот и уборку.')
    for i,h in enumerate(['Поднятые руки / вид спереди','Сесть → наклониться → встать','Пол → крайнее вытягивание']):s.text(12+i*134,52,h,12,C['teal'],True)
    # Overhead: all segment lengths assumed independently of sourced body height.
    x=65;fl=166;k=25
    s.line(18,fl,131,fl,C['gray'],.4);s.line(18,fl-2600/k,131,fl-2600/k,C['gray'],.4)
    s.circle(x,fl-1650/k,4,C['white'],C['ink'],.8)
    s.poly([(x,fl-1550/k),(x,fl-900/k),(x-180/k,fl),(x-300/k,fl)],C['ink'],.9)
    s.poly([(x,fl-900/k),(x+180/k,fl),(x+300/k,fl)],C['ink'],.9)
    for sign in [-1,1]:
        s.poly([(x,fl-1450/k),(x+sign*300/k,fl-1800/k),(x+sign*200/k,fl-2250/k)],C['teal'],.9)
        s.rect(x+sign*200/k-2,fl-2350/k,4,4,C['goldpale'],C['gold'],.4)
    s.dim_v(fl-2350/k,fl,85,105,'2350 У: кисть + предмет')
    s.text(18,fl-2600/k-3,'2600 У: потолок / 1:25',9,C['gray'])
    s.para(12,180,124,'2250 У: кисть + 100 У: предмет. Просвет 250 Р. Рост 1760 - масштаб прежнего листа; высота кисти задана отдельно.',10,4.3,max_lines=5)
    # Sit to stand: fixed chair and alternate phases, same origin.
    x=174;fl=166
    s.line(150,fl,267,fl,C['gray'],.4)
    s.poly([(x,fl-850/k),(x,fl-450/k),(x+500/k,fl-450/k)],C['gray'],.65)
    for xx in [x,x+500/k]:s.line(xx,fl-450/k,xx,fl,C['gray'],.65)
    figure(s,x+2,fl,1580,k,'seated',C['ghost'],True)
    figure(s,x+24,fl,1580,k,'standing',C['teal'])
    s.arrow(x+12,fl-32,x+30,fl-48,C['pink'],.4,(1,1))
    s.dim_h(155,254,fl,fl+7,'Стул + наклон + стопы: измерить')
    s.para(146,180,124,'Высота сиденья 450 У - только макет. Нужны стопы на полу и подходящий захват; подлокотники могут менять доступ рук [S4, S5].',10,4.3,max_lines=5)
    # Floor side view hand and leg extend out of contacts, 1:20 diagram.
    fl=166;x=301
    s.line(284,fl,402,fl,C['gray'],.4)
    s.poly([(x+28,fl-28),(x+46,fl-28),(x+58,fl-27)],C['ink'],1)
    s.circle(x+64,fl-29,3,C['white'],C['ink'],.7)
    s.poly([(x+46,fl-28),(x+50,fl-8),(x+50,fl)],C['ghost'],.8,(1,1))
    s.poly([(x+28,fl-28),(x+28,fl),(x+16,fl)],C['ink'],.8)
    s.poly([(x+28,fl-28),(x+10,fl-30),(x-2,fl-30)],C['teal'],.9)
    s.poly([(x+46,fl-28),(x+62,fl-30),(x+76,fl-30)],C['teal'],.9)
    s.circle(x+50,fl,1.2,C['teal'],C['teal']);s.circle(x+28,fl,1.2,C['teal'],C['teal'])
    s.dim_h(x-2,x+76,fl-33,fl-48,'Рука + корпус + нога: обмер')
    s.para(280,180,124,'Детский пример [S7]. Поза схематичная, без размерного масштаба. Вытягивание выходит за исходные точки опоры. Нужны переходы и смена стороны.',10,4.3,max_lines=5)
    s.line(12,205,408,205,C['light'],.5)
    block(s,12,217,123,'Реальный радиус движения','Фиксирую исходную точку x0, y0. По видео отмечаю крайние точки тела/предмета: r = max √[(xi - x0)² + (yi - y0)²]. Для шагов центр перемещается; нужен весь путь.',10.1)
    block(s,146,217,123,'Полный цикл использования','Достать → перенести → подготовить → выполнить → сменить пользователя → убрать. Проверить раскрытие хранения и место рядом с человеком; при необходимости - место помощника.',10.1)
    block(s,280,217,124,'Проверенный пример [S9]','Concept2: собранное место 155 × 66 см = 1,02 м²; с местом использования 203 × 97 см = 1,97 м² Р. Отдельные габариты полезны как метод; на наш проект числа не переносятся.',10.1)
    s.text(12,286,'На следующем обмере: линейка в кадре, виды сверху/сбоку, все фазы и инвентарь. Высоты и углы не восстанавливать только по росту [S8].',9.1,C['gray'])
    return s

def sketches(m):
    s=Sheet();title(s,'Три возможных направления формы','Предварительные эскизы: сверху хранение, снизу подготовка места. Материал, нагрузка и размерный ряд остаются открытыми.')
    for i,t in enumerate(['А. Скамья-хранилище','Б. Независимые модули','В. Вертикальное хранение']):s.text(46+i*110,43,t,11.4,C['teal'],True)
    s.e.append(dict(kind='image',path=str(ASSET),x=45,y=49,w=330,h=220))
    s.para(12,280,396,'Форма сравнивается по сценарию и занимаемому месту. Эскизы созданы ИИ; конструктивный принцип и пробные размеры показаны на следующем листе. Это не чертёж для изготовления.',9.7,4.1,max_lines=2)
    return s

def structures(m):
    s=Sheet();title(s,'Конструкция: опоры, хранение и ограничения','Схемы показывают предполагаемый путь нагрузки. Стрелки качественные; толщина деталей, крепёж, допустимые массы и прочность ещё не рассчитаны.')
    heads=['А. Неподвижный несущий верх','Б. Два самостоятельных каркаса','В. Корпус отдельно от пола']
    for i,h in enumerate(heads):s.text(12+i*134,53,h,12,C['teal'],True)
    # A side view: shell carries top load, drawer is not a support.
    x=26;y=83;w=96;h=36
    s.rect(x,y,w,h,None,C['ink'],.8);s.rect(x,y,w,4,C['pale'],C['teal'],.6)
    s.rect(x+6,y+14,w-12,15,C['light'],C['gray'],.4)
    for xx in [x+3,x+w-3]:
        s.arrow(xx,y+5,xx,y+h-2,C['teal'],.65);s.rect(xx-3,y+h,6,3,C['gray'])
    s.arrow(x+w/2,y-12,x+w/2,y+3,C['pink'],.7)
    s.arrow(x+w/2,y+22,x+w/2+12,y+32,C['gray'],.4)
    s.text(x+31,y+39,'лоток не несёт тело',9,C['gray'])
    s.dim_h(x,x+w,y+h,133,'1200 У / вид спереди 1:12,5')
    # B modules do not bridge or share load.
    for xx in [158,214]:
        s.rect(xx,83,40,36,None,C['ink'],.8);s.rect(xx,83,40,4,C['pale'],C['teal'],.5)
        s.rect(xx+7,98,26,14,None,C['gray'],.4)
        s.arrow(xx+20,68,xx+20,86,C['pink'],.7)
        for p in [xx+3,xx+37]:s.arrow(p,89,p,116,C['teal'],.55)
        s.rect(xx,119,40,3,C['gray'])
    s.text(158,133,'Каждый 500 × 450 × 450 У',10)
    s.text(158,141,'Перемычки под телом нет',9.4,C['gray'])
    # C side view of tall cabinet and flat floor panel.
    x=304;fl=144
    s.rect(x,62,40,78,None,C['ink'],.8);s.rect(x-3,140,46,4,C['gray'])
    for yy in [88,112]:s.line(x,yy,x+40,yy,C['gray'],.4)
    s.rect(x+3,123,22,13,C['light'],C['gray'],.4)
    s.text(x+5,132,'груз',8.5,C['gray'])
    s.rect(355,141,48,3,C['pale'],C['teal'],.6);s.line(379,141,379,144,C['teal'],.5)
    s.arrow(x+40,92,x+58,92,C['pink'],.65)
    s.text(350,87,'F',11,C['pink'],True);s.text(350,132,'панель',9,C['teal'])
    s.text(285,154,'Корпус 700 × 400 × 1100 У',10)
    blocks=[
      ('Размеры и связь с движением','1200 × 450 × 450 мм У; пятно 0,54 м² Р. Коврик на полу - для опоры ладоней/коленей. Посадка/вставание возможны как функция для проверки, не готовый допуск.'),
      ('Размеры и связь с движением','Два модуля по 500 × 450 × 450 мм У; суммарное пятно 0,45 м² Р. У каждого своё основание. Можно менять расстановку, но рабочие зоны людей проверить отдельно.'),
      ('Размеры и связь с движением','700 × 400 × 1100 мм У; пятно 0,28 м² Р. Панель раскрывается на полу. Шкаф хранит предметы, не заменяет стену, сиденье и поддержку рукой.')]
    for i,(head,body) in enumerate(blocks):block(s,12+i*134,171,124,head,body,10)
    checks=[
      'Проверить: прогиб верха; эксцентричную посадку; скольжение; опрокидывание с выдвинутым лотком. Перед занятием лоток закрыть.',
      'Проверить: устойчивость каждого модуля; перенос с грузом; контакт ручек и кромок. Стык двух верхов не считать непрерывной опорой.',
      'Проверить: доставание и открывание без опрокидывания; доступ детей; стык напольной панели. Если без сверления неустойчив - пересмотреть вариант.'
    ]
    for i,t in enumerate(checks):s.para(12+i*134,220,124,t,9.7,4.2,max_lines=6)
    s.rect(12,250,396,34,C['pale'])
    s.text(16,258,'Проверка устойчивости: Mопр = F × h; Mуд = G × b. Скольжение и прочность проверяются отдельно.',10.5,C['teal'],True)
    s.para(16,266,386,'F - горизонтальная сила; h - её высота; G - вес; b - плечо веса до края опоры. Пока нет значений сил и масс, нельзя назначить допустимую нагрузку. Начать предлагаю с компоновочного макета А; Б сравнить по расстановке, В - по доступу и устойчивости.',10,4.2,max_lines=4)
    s.text(12,292,'Пробные размеры - предложения помощника. Степ, прыжки, подвешивание и анкер ленты в эти варианты не включены.',9,C['gray'])
    return s

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=ROOT/'outputs/current');a=ap.parse_args();out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    pdfmetrics.registerFont(TTFont('Spatial','C:/Windows/Fonts/arial.ttf'));pdfmetrics.registerFont(TTFont('SpatialBold','C:/Windows/Fonts/arialbd.ttf'))
    m=json.loads(MODEL.read_text(encoding='utf-8'));sheets=[functions(m),zones(m),heights(m),sketches(m),structures(m)]
    pdf=out/(STEM+'.pdf');svgs=[out/f'{STEM}_{i+1:02d}.svg' for i in range(5)]
    if any(p.exists() for p in [pdf]+svgs):raise FileExistsError('Refusing to overwrite existing output')
    c=canvas.Canvas(str(pdf),pagesize=(420*mm,297*mm));c.setTitle('Движения, пространство и первые формы');c.setAuthor('Диплом: исследовательские варианты')
    for sh,path in zip(sheets,svgs):
        normal=Sheet();normal.e=[e for e in sh.e if e['kind']!='image'];content=svg(normal)
        for e in sh.e:
            if e['kind']!='image':continue
            data=base64.b64encode(Path(e['path']).read_bytes()).decode()
            tag=f'<image x="{e["x"]}" y="{e["y"]}" width="{e["w"]}" height="{e["h"]}" href="data:image/png;base64,{data}"/>'
            content=content.replace('</svg>',tag+'\n</svg>')
        path.write_text(content,encoding='utf-8');pdf_draw(c,normal)
        for e in sh.e:
            if e['kind']=='image':c.drawImage(e['path'],e['x']*mm,(297-e['y']-e['h'])*mm,e['w']*mm,e['h']*mm,mask='auto')
        c.showPage()
    c.save()
    build=ROOT/'.codex-build/movement-form-2026-11-06';build.mkdir(parents=True,exist_ok=True)
    (build/'layout.json').write_text(json.dumps([s.e for s in sheets],ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'pdf':str(pdf),'svg':[str(p) for p in svgs],'pages':len(sheets)}))

if __name__=='__main__':main()
