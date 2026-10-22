"""Rebuild the review boards and slides: python3 tools/build_review.py.

Requires python-pptx, reportlab and Noto Sans (already present in this environment).
All drawings are conceptual vector diagrams, not measured or anatomical models.
"""
from pathlib import Path
import math

from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/current"
FONT = Path("/usr/share/fonts/truetype/noto")
pdfmetrics.registerFont(TTFont("Noto", str(FONT / "NotoSans-Regular.ttf")))
pdfmetrics.registerFont(TTFont("NotoB", str(FONT / "NotoSans-Bold.ttf")))
BG, INK, TEAL, AMBER, MUTED, PALE, WHITE = (
    "F5F3ED", "233438", "16736D", "A96923", "657577", "E5EBE6", "FFFFFF"
)


class Document:
    def __init__(self, w, h, pdf_name, pptx_name):
        self.w, self.h = w, h
        self.pdf = canvas.Canvas(str(OUT / pdf_name), pagesize=(w, h))
        self.pdf.setTitle("Диплом • исследование пользователей и движений")
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = Pt(w), Pt(h)
        self.pptx_name = pptx_name
        self.n = 0

    def rect(self, x, y, w, h, fill=WHITE, stroke=None, radius=False):
        c = self.pdf
        c.setFillColor("#" + fill)
        c.setStrokeColor("#" + (stroke or fill))
        c.rect(x, self.h - y - h, w, h, stroke=bool(stroke), fill=True)
        shape = self.slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Pt(x), Pt(y), Pt(w), Pt(h))
        style = shape._element.find(qn("p:style"))
        if style is not None:
            shape._element.remove(style)
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor.from_string(fill)
        if stroke:
            shape.line.color.rgb = RGBColor.from_string(stroke)
        else:
            shape.line.fill.background()

    def line(self, x1, y1, x2, y2, color=INK, width=1.5):
        self.pdf.setStrokeColor("#" + color)
        self.pdf.setLineWidth(width)
        self.pdf.line(x1, self.h - y1, x2, self.h - y2)
        shape = self.slide.shapes.add_connector(1, Pt(x1), Pt(y1), Pt(x2), Pt(y2))
        style = shape._element.find(qn("p:style"))
        if style is not None:
            shape._element.remove(style)
        shape.line.color.rgb = RGBColor.from_string(color)
        shape.line.width = Pt(width)

    def arrow(self, x1, y1, x2, y2, color=TEAL):
        self.line(x1, y1, x2, y2, color, 1.7)
        a = math.atan2(y2 - y1, x2 - x1)
        for offset in (-0.5, 0.5):
            self.line(x2, y2, x2 - 8 * math.cos(a + offset), y2 - 8 * math.sin(a + offset), color)

    def circle(self, x, y, r, color=INK, fill=None):
        self.pdf.setStrokeColor("#" + color)
        self.pdf.setLineWidth(1.5)
        self.pdf.setFillColor("#" + (fill or BG))
        self.pdf.circle(x, self.h - y, r, stroke=True, fill=bool(fill))
        s = self.slide.shapes.add_shape(MSO_SHAPE.OVAL, Pt(x-r), Pt(y-r), Pt(2*r), Pt(2*r))
        style = s._element.find(qn("p:style"))
        if style is not None:
            s._element.remove(style)
        s.line.color.rgb = RGBColor.from_string(color)
        s.line.width = Pt(1.5)
        if fill:
            s.fill.solid()
            s.fill.fore_color.rgb = RGBColor.from_string(fill)
        else:
            s.fill.background()

    def text(self, text, x, y, w, size=14, bold=False, color=INK, max_h=None, url=None):
        font = "NotoB" if bold else "Noto"
        lines = []
        for raw in text.split("\n"):
            words, line = raw.split(), ""
            for word in words:
                candidate = (line + " " + word).strip()
                if line and pdfmetrics.stringWidth(candidate, font, size) > w - 3:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
        leading = size * 1.38
        height = len(lines) * leading
        if max_h is not None and height > max_h + 0.1:
            raise ValueError(f"Text too tall on page {self.n}: {height:.1f}>{max_h}: {text[:70]}")
        if y + height > self.h - 14:
            raise ValueError(f"Text below footer on page {self.n}: {text[:80]}")
        self.pdf.setFillColor("#" + color)
        self.pdf.setFont(font, size)
        for i, line in enumerate(lines):
            yy = y + i * leading
            self.pdf.drawString(x, self.h - yy - size, line)
            tb = self.slide.shapes.add_textbox(Pt(x), Pt(yy-1), Pt(w+4), Pt(leading+4))
            tf = tb.text_frame
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            tf.word_wrap = False
            p = tf.paragraphs[0]
            p.space_before = p.space_after = Pt(0)
            p.font.name, p.font.size = "Noto Sans", Pt(size)
            p.font.bold = bold
            p.font.color.rgb = RGBColor.from_string(color)
            p.text = line
            if url:
                p.runs[0].hyperlink.address = url
        if url:
            self.pdf.linkURL(url, (x, self.h-y-height, x+w, self.h-y), relative=0)
        return y + height

    def page(self, number, title, subtitle, board=False):
        if self.n:
            self.pdf.showPage()
        self.n += 1
        self.slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self.rect(0, 0, self.w, self.h, BG)
        margin = 36 if board else 32
        self.text("ДИПЛОМ / ПРОМЫШЛЕННЫЙ ДИЗАЙН", margin, 22, 800, 10, True, TEAL)
        self.text(title, margin, 48, self.w - 2*margin, 29 if board else 28, True)
        self.text(subtitle, margin, 94, self.w - 2*margin, 11 if board else 12, color=MUTED)
        self.line(margin, self.h-37, self.w-margin, self.h-37, MUTED, .5)
        self.text("22.10.2026 • Рабочая версия • сроки и размеры не назначены", margin, self.h-31,
                  self.w-130, 8, color=MUTED)
        self.text(str(number), self.w-62, self.h-31, 30, 8, True, TEAL)

    def card(self, x, y, w, h, title, body, size=14, fill=WHITE):
        self.rect(x, y, w, h, fill)
        yy = self.text(title, x+15, y+12, w-30, size+2, True, TEAL)
        self.text(body, x+15, yy+10, w-30, size, max_h=y+h-yy-24)

    def note(self, text):
        self.slide.notes_slide.notes_text_frame.text = text

    def save(self):
        self.pdf.save()
        self.prs.save(OUT / self.pptx_name)


def figure(d, x, y, pose, color=INK):
    """Purely symbolic body, baseline at y+42. No anatomical dimensions."""
    if pose == "sit":
        hip, shoulder, head = (x, y), (x-3, y-33), (x-3, y-47)
        legs = [[hip, (x+28, y), (x+28, y+42)], [hip, (x+19, y+7), (x+19, y+42)]]
        arms = [[shoulder, (x+16, y-14), (x+27, y-3)]]
        d.line(x-22,y+4,x+17,y+4,MUTED,3)
        d.line(x-19,y+4,x-19,y+42,MUTED,3)
    elif pose == "rise":
        hip, shoulder, head = (x+8,y-10),(x+23,y-38),(x+28,y-52)
        legs = [[hip,(x+30,y+9),(x+21,y+42)],[hip,(x+19,y+7),(x+11,y+42)]]
        arms = [[shoulder,(x+37,y-18),(x+28,y-5)]]
    else:
        hip, shoulder, head = (x,y-6),(x,y-38),(x,y-52)
        step = 30 if pose == "step" else 13
        legs = [[hip,(x-step,y+42)],[hip,(x+step,y+42)]]
        if pose == "reach":
            arms = [[shoulder,(x+24,y-49),(x+47,y-49)], [shoulder,(x-16,y-10)]]
        elif pose == "support":
            arms = [[shoulder,(x+24,y-31),(x+45,y-31)], [shoulder,(x-14,y-11)]]
        else:
            arms = [[shoulder,(x-20,y-10)],[shoulder,(x+20,y-10)]]
    d.circle(*head,8,color)
    d.line(*shoulder,*hip,color,2)
    for chain in legs+arms:
        for a,b in zip(chain,chain[1:]): d.line(*a,*b,color,2)
    d.line(x-52,y+43,x+74,y+43,MUTED,.7)


def boards():
    # ISO A3 landscape in points, rounded only for the drawing coordinate system.
    d = Document(1190.551, 841.89, "Review_boards_A3.pdf", "Review_boards_editable.pptx")
    d.page("01", "Пользователь → движение → опора", "ОСНОВНОЙ ЛИСТ 1 / Сценарии и схемы для обсуждения; внешняя методическая проверка ещё не выполнена", True)
    d.card(36,133,365,154,"Молодые / взрослые",
           "Слова автора: мало места и времени; важно убирать инвентарь и не повреждать жильё. Это личный опыт, не вывод обо всей группе.\nПроверить: подготовку, хранение и доступную зону.",13)
    d.card(413,133,365,154,"Дети: подгруппы отдельно",
           "Гипотеза: игровой сценарий вместо уменьшенного взрослого тренажёра.\nПроверить отдельно дошкольников и школьников: интерес, действия и роль взрослого. Возраст допуска не задан.",13)
    d.card(790,133,365,154,"Пожилые: разные возможности",
           "Гипотеза: сравнить действия сидя, стоя и с поддержкой. Возраст сам по себе не определяет возможности.\nПроверить: подход, досягаемость опор и завершение действия.",13)
    d.text("ТРИ РАЗНЫХ СЦЕНАРИЯ ДЛЯ РАСКАДРОВКИ",36,307,1100,13,True,TEAL)
    rows = [
        (349,"M-01 / сидя–стоя","Проверить переход и место перед сиденьем.",["sit","rise","stand"],
         ["Исходное положение","Промежуточная фаза","Завершение"]),
        (472,"M-06 / боковой шаг","Проверить протяжённость поддержки.",["support","step","support"],
         ["Подход к опоре","Смена положения","Завершение"]),
        (595,"M-08 / достать предмет","Игровой кандидат; возраст не установлен.",["stand","reach","stand"],
         ["Найти предмет","Действие рукой","Возврат"]),
    ]
    for y,label,body,poses,labels in rows:
        d.line(36,y-12,1154,y-12,PALE,1)
        d.text(label,36,y,230,15,True)
        d.text(body,36,y+28,220,12,color=MUTED,max_h=70)
        for i,pose in enumerate(poses):
            x=350+285*i
            figure(d,x,y+40,pose)
            if label.startswith("M-06"):
                d.line(x+45,y+6,x+82,y+6,TEAL,3)
                d.line(x+80,y+6,x+80,y+82,TEAL,2)
            if pose=="reach": d.circle(x+52,y-9,5,TEAL,TEAL)
            d.text(labels[i],x-60,y+89,220,10,color=MUTED)
            if i<2: d.arrow(x+110,y+32,x+172,y+32)
    d.rect(36,725,1118,57,PALE)
    d.text("Схемы проектных гипотез • без масштаба • не инструкция по выполнению упражнений",49,733,1090,12,True,TEAL)
    d.text("Основание задания: C-01, 04:17–05:39, 14:12–14:24. Все 9 кандидатов и ограничения — в презентации и research/movements.md.",49,754,1090,10)
    d.note("Три изображения — условные проектные схемы. Техника и применимость не проверены. Исходник: meetings/raw/teacher-discussion-01.md. Матрица: research/users-comparison.md.")

    d.page("02", "Пространство → требования → варианты", "ОСНОВНОЙ ЛИСТ 2 / Метод анализа; реальные размеры и расчётные усилия ещё не получены",True)
    d.text("КАК ОБОСНОВАТЬ РАЗМЕР",36,134,540,14,True,TEAL)
    d.rect(36,165,540,310,WHITE)
    d.text("Вид сверху • условная зона, без масштаба",51,179,505,12,True)
    d.rect(112,228,305,173,PALE,TEAL)
    d.rect(140,247,105,55,WHITE,TEAL)
    d.text("предмет",151,263,88,11)
    d.circle(303,325,18,INK)
    d.arrow(305,347,305,383)
    d.text("положение тела",330,316,160,11)
    d.text("подход / выход",321,366,175,11)
    d.arrow(112,426,417,426)
    d.text("X = ?   ширина всей зоны",160,440,320,11,True,TEAL)
    d.arrow(83,228,83,401)
    d.text("Y = ?",45,310,65,11,True,TEAL)
    d.text("Фиксировать все фазы: подготовка → действие → уборка.",51,480,510,12)
    d.rect(36,516,540,194,WHITE)
    d.text("Вид сбоку • досягаемость и траектория",51,530,505,12,True)
    figure(d,178,611,"reach")
    d.rect(250,610,90,45,PALE,TEAL)
    d.arrow(382,561,382,654)
    d.text("Z = ?",400,598,130,12,True,TEAL)
    d.text("Неизвестны: размеры тела, высота опоры, зазоры.",51,677,505,10,color=MUTED)
    d.card(601,134,553,126,"Требования к проверке",
           "Показать путь тела и инвентаря, направления усилий, подход и уборку. У каждого размера — происхождение. «2 × 2 м» пока только ранняя оценка автора.",14)
    alternatives=[
        (277,"A / единый предмет","Сиденье / поддержка / хранение в одном объёме. Проверить конфликт функций и устойчивость."),
        (412,"B / база + элементы","Добавлять только реально нужные функции. Проверить соединения, перестройку и хранение частей."),
        (547,"C / отдельные простые предметы","Разделить поддержку, инвентарь и хранение. Проверить суммарное место и удобство подготовки."),
    ]
    for y,title,body in alternatives: d.card(601,y,553,118,title,body,14)
    d.rect(36,735,1118,47,PALE)
    d.text("Пока сравниваем варианты. Аудитория, габариты, материал и модульность не выбраны.",49,741,1090,13,True,TEAL)
    d.text("C-01: 02:51–03:01 и 06:39–08:05. Схемы и выводы — предложения помощника, не результаты замеров.",49,764,1090,9)
    d.note("X/Y/Z — неизвестные, а не размеры изделия. Не выводить расчёты из этих рисунков. Подробнее: research/analysis-plan.md.")
    # Save two-page main PDF before adding the optional board to the editable deck.
    d.pdf.save()
    d.pdf = canvas.Canvas(str(OUT / "Review_optional_board_A3.pdf"), pagesize=(d.w,d.h))
    d.pdf.setTitle("Диплом • резервный лист аргументов A3")
    d.n=0
    d.page("03", "Аргументы и проверяемые решения", "РЕЗЕРВНЫЙ ЛИСТ / Можно оставить в презентации, если показываем только два основных A3",True)
    cols=[36,360,757]
    headers=["Аргумент для обсуждения","Основание / что ещё выяснить","Возможное решение, не выбор"]
    widths=[300,373,373]
    for x,w,t in zip(cols,widths,headers): d.text(t,x,138,w,16,True,TEAL)
    args=[
        ("Начать с сценария, а не с формы.","Преподаватель: сначала пользователи и раскадровки, C-01 05:27–05:39.","Сравнить одни и те же действия для разных пользователей до эскиза лавочки или шкафа."),
        ("Основание мебели не равно зоне занятия.","Проектный разбор: тело движется; нужны подход и уборка. Замеров пока нет.","План и вид сбоку с крайними положениями и подписанными неизвестными."),
        ("Одна опора не гарантирует общую функцию.","Механическая гипотеза: посадка, толкание и поддержка дают разные усилия.","Отдельно проверить сдвиг, опрокидывание и доступ к контактным поверхностям."),
        ("Модульность нужно обосновать.","В консультации — возможное направление, 05:58–06:21, 08:51–09:41.","Сопоставить единую конструкцию, базу с элементами и независимые предметы."),
        ("Материал выбирается под задачу.","Нагрузки, масса, отделка и стоимость пока не установлены.","Сравнить фанеру, металлический каркас и комбинированную схему после требований."),
    ]
    for i,row in enumerate(args):
        y=195+i*103
        d.line(36,y-12,1154,y-12,PALE,1)
        for j,(x,w,t) in enumerate(zip(cols,widths,row)):
            d.text(t,x,y,w,14,bold=j==0,max_h=87)
    d.rect(36,730,1118,52,PALE)
    d.text("Что нельзя утверждать сейчас",49,736,1090,13,True,AMBER)
    d.text("Не доказаны: польза упражнений для всех возрастов, универсальные размеры, несущая способность и защита пола.",49,758,1090,11)
    d.note("Резервный лист, не обязательный третий носитель. Все варианты и механические рассуждения — гипотезы помощника.")
    d.save()


def presentation():
    d=Document(960,540,"Review_presentation.pdf","Review_presentation.pptx")
    d.page(1,"От домашнего сценария к предмету","Короткое сопровождение двух A3 • Промежуточный исследовательский показ")
    d.card(32,143,560,245,"Вопрос проекта",
           "Как организовать домашнюю активность и хранение инвентаря, не занимая комнату постоянно?\n\nСейчас сравниваем пользователей, движения, опоры и пространство. Форму пока не закрепляем.",19)
    d.card(610,143,318,245,"Что есть / чего нет",
           "Есть консультация, матрица и 9 кандидатов.\n\nНет проверенных методик, интервью, замеров и выбранной конструкции.",16,PALE)
    d.text("Рабочие схемы и гипотезы подписаны. Дата следующего показа неизвестна.",32,432,896,15,color=MUTED)
    d.note("Текст проекта: PROJECT.md. Личный опыт автора — не опрос пользователей. Не заявлять, что изделие заменяет тренажёрный зал.")

    d.page(2,"Что требуется и как это показываем","Требования преподавателя отделены от предложенного формата")
    d.card(32,140,438,300,"Преподаватель / C-01",
           "Расширить сравнение пользователей: 04:17–05:27.\nРаскадровки до формы: 05:27–05:39.\nОбосновать пространство: 07:10–08:05.\nДва-три листа: 10:43–10:46.\nСводная таблица: 14:12–14:24.",16)
    d.card(490,140,438,300,"Наша организация показа",
           "Автор разрешил часть материала перенести в презентацию.\n\nПредложение помощника: два основных A3, резервный третий лист и девять слайдов. Формат замены стоит уточнить у преподавателя.",17,PALE)
    d.note("Исходник: meetings/raw/teacher-discussion-01.md. Дата самой консультации неизвестна. Ошибки распознавания не превращать в требования.")

    d.page(3,"Кого сравниваем","Возрастные границы не утверждены; возможности важнее одного возрастного ярлыка")
    d.card(32,142,288,280,"Молодые / взрослые",
           "Опыт автора: мало места, подготовка и уборка, переезд.\n\nПроверить у других: реальную активность, инвентарь, место и число действий подготовки.",16)
    d.card(336,142,288,280,"Дети",
           "Игровой сценарий — гипотеза. Дошкольников и школьников рассматривать отдельно.\n\nНужны родитель, подходящая методика и проверка роли взрослого.",16)
    d.card(640,142,288,280,"Пожилые",
           "Сравнить самостоятельность, досягаемость и потребность в поддержке.\n\nНе считать всех малоподвижными. Условия применения уточнять со специалистом.",16)
    d.text("Семья — сценарий совместного использования, а не отдельная возрастная группа.",32,449,896,15,True,TEAL)
    d.note("Матрица и протокол беседы: research/users-comparison.md. Интервью не проводились; эти сценарии пока не подтверждены.")

    d.page(4,"Девять кандидатов для дальнейшей проверки","Техника, мышцы по источникам и возрастная применимость пока не подтверждены")
    groups=[("Действия стоя / переходы","M-01   Сидя → стоя\nM-02   Отталкивание от стены\nM-03   Подъём пяток у опоры"),
            ("Поддержка / положение сидя","M-04   Сидя → стоя с руками\nM-05   Движение голени сидя\nM-06   Боковой шаг у опоры"),
            ("Игровые действия","M-07   Путь между метками\nM-08   Достать предмет\nM-09   Действие у пола")]
    for i,(title,body) in enumerate(groups): d.card(32+304*i,148,288,225,title,body,15)
    d.rect(32,399,896,65,PALE)
    d.text("На A3 показаны три сценария. Остальные остаются в каталоге для отбора, а не становятся обязательной программой упражнений.",47,411,866,16,max_h=50)
    d.note("Полные карточки: research/movements.md. Связь с возрастом предстоит проверить. Не назначать нагрузку, повторы или амплитуду по этим рисункам.")

    d.page(5,"Что мы можем аргументировать сейчас","Проектные рассуждения не заменяют измерения и доказательства эффективности")
    arguments=[
        ("Сценарий раньше формы","Основание: C-01, 05:27–05:39. Показать путь от действия к опоре, а не защищать заранее выбранную лавочку."),
        ("Компактность надо измерить","Проверить не только хранение, но и подготовку, движение, подход и уборку. Целевого габарита пока нет."),
        ("Общая опора требует проверки","Посадка, толкание и поддержка могут давать разные усилия. Нужны расчётные условия и испытания."),
    ]
    for i,(title,body) in enumerate(arguments):
        y=139+i*109
        d.text(title,32,y,270,18,True,TEAL,max_h=85)
        d.text(body,330,y,598,16,max_h=90)
        if i<2:d.line(32,y+95,928,y+95,PALE)
    d.note("Первый аргумент — требование из консультации; второй и третий — аналитические гипотезы помощника. Не заявлять доказанную устойчивость или экономию площади.")

    d.page(6,"Возможные решения и материалы","Сравнение направлений • конструкция, материал и механизм пока не выбраны")
    d.card(32,140,288,206,"A / единый предмет","Функции в одном объёме.\nПроверить конфликт опор и хранения, массу, переноску и устойчивость.",16)
    d.card(336,140,288,206,"B / база + элементы","Добавлять нужные функции.\nПроверить соединения, фиксацию, перестройку и место для частей.",16)
    d.card(640,140,288,206,"C / отдельные предметы","Разделить функции.\nПроверить суммарное место, количество вещей и удобство уборки.",16)
    d.text("Материалы-кандидаты",32,370,896,17,True,TEAL)
    d.text("Фанера / листовые детали; металлический каркас; комбинированная схема; сменные накладки и текстиль. Сначала требования, затем сравнение узлов, массы, отделки, обслуживания и доступного изготовления.",32,403,896,16,max_h=80)
    d.note("Это список вариантов для исследования, не спецификация. Не заданы породы, марки, толщины, сварка, петли, газовые пружины или крепления сопротивления. Их нельзя выбрать без нагрузок и геометрии.")

    d.page(7,"Источники и происхождение данных","Внешние сайты при последней проверке заблокированы прокси: 403 Forbidden")
    y=140
    for label,url in [
        ("ВОЗ / общие рекомендации — кандидат, не прочитано","https://www.who.int/news-room/fact-sheets/detail/physical-activity"),
        ("ВОЗ / отдельное руководство для детей младше пяти лет — кандидат","https://www.who.int/publications/i/item/9789241550536"),
        ("NHS / методические упражнения — кандидат, не прочитано","https://www.nhs.uk/live-well/exercise/strength-and-flex-exercise-plan/strength-exercises/"),
    ]:
        d.text(label,32,y,896,15,True)
        d.text(url,32,y+29,896,11,color=TEAL,url=url)
        y+=82
    d.text("Прочитан: C-01, исходная консультация. Полный поисковый список и результаты запросов: research/sources.md. Кандидат в источники не равен проверенному основанию.",32,410,896,15,max_h=75)
    d.note("Источники не выдавать за прочитанные. После открытия доступа нужно записать точный раздел, условия применимости и вывод. Отдельно подобрать антропометрию; данные пока отсутствуют.")

    d.page(8,"Как довести листы до проверенного результата","Порядок работы • сроки не назначены • подробности в Review_execution_plan.md")
    steps=[("1–2 / основания","Открыть источники; уточнить формат показа; получить реальные сценарии и обмер комнаты."),
           ("3–4 / лист 1","Проверить сравнение групп; отобрать движения; заменить условные кадры проверенными раскадровками."),
           ("5–6 / лист 2","Нанести траектории и размеры; сравнить опоры и три конструктивных направления."),
           ("7–8 / проверка показа","Сверить подписи и источники; убрать дубли; проверить печать; проговорить выводы и открытые вопросы.")]
    for i,(title,body) in enumerate(steps):
        y=140+i*83
        d.text(title,32,y,245,17,True,TEAL,max_h=70)
        d.text(body,300,y,628,16,max_h=70)
    d.note("Это последовательность выполнения существующих задач DIP-001–006, а не новый независимый список статусов. Печать финальной версии только после подстановки достоверных данных либо с честными пометками об их отсутствии.")

    d.page(9,"Что нужно решить и принести автору","На показе можно обсуждать направление, не выдавая промежуточный анализ за завершённое исследование")
    d.card(32,140,438,300,"Твоё участие",
           "Уточнить дату и формат показа.\nДать обмер комнаты и инвентарь.\nОрганизовать согласованные беседы.\nСогласовать проверку движений со специалистом.\nВыбрать аудиторию после анализа.",16)
    d.card(490,140,438,300,"Вопросы преподавателю",
           "Подходит ли формат: два A3 + презентация?\nКакая глубина сравнения групп нужна сейчас?\nДостаточны ли выбранные сценарии для следующего этапа?\nПо каким данным сужаем аудиторию?",17,PALE)
    d.note("От автора не требуется самостоятельно проводить непроверенные упражнения на участниках. Дедлайн неизвестен. Поручения и состояния только в TASKS.md.")
    d.save()


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True,parents=True)
    boards()
    presentation()
    print("Built: 2 main A3 pages, 1 optional A3 page, 3 editable A3 slides, 9 presentation slides (PDF/PPTX).")
