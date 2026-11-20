"""Two A3 vector sheets: conditional room, sourced heights, explicit assumptions.

Both PDF and editable SVG are drawn from the same vector primitives. No raster
figures, generated photos, measured claims, or normative clearances are used.
"""
from pathlib import Path
import argparse
import json
import math
from html import escape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/current'
BUILD=ROOT/'.codex-build/spatial-2026-10-30'
MODEL=ROOT/'research/spatial-model-2026-10-30.json'
STEM='Spatial_analysis_A3_2026-10-30'
C={'ink':'#203540','teal':'#087F80','pale':'#E4F3F0','pink':'#AE4775','pinkpale':'#F6E6ED','gold':'#AC7127','goldpale':'#FFF2D9','gray':'#667780','light':'#E9EDEF','ghost':'#BBC8CC','white':'#FFFFFF'}


class Sheet:
    def __init__(self): self.e=[]
    def line(self,x1,y1,x2,y2,color=None,width=.35,dash=None):
        self.e.append(dict(kind='line',x1=x1,y1=y1,x2=x2,y2=y2,color=color or C['ink'],width=width,dash=dash))
    def rect(self,x,y,w,h,fill=None,color=None,width=.35,dash=None):
        self.e.append(dict(kind='rect',x=x,y=y,w=w,h=h,fill=fill,color=color,width=width,dash=dash))
    def circle(self,x,y,r,fill=None,color=None,width=.35):
        self.e.append(dict(kind='circle',x=x,y=y,r=r,fill=fill,color=color or C['ink'],width=width))
    def poly(self,points,color=None,width=.5,dash=None,fill=None,close=False):
        self.e.append(dict(kind='poly',points=points,color=color or C['ink'],width=width,dash=dash,fill=fill,close=close))
    def text(self,x,y,value,size=10,color=None,bold=False,anchor='start',rotate=0):
        self.e.append(dict(kind='text',x=x,y=y,value=value,size=size,color=color or C['ink'],bold=bold,anchor=anchor,rotate=rotate))
    def para(self,x,y,w,value,size=10,leading=4.3,bold=False,color=None,max_lines=None):
        font='SpatialBold' if bold else 'Spatial'
        lines=[]
        for p in value.split('\n'):
            line=''
            for word in p.split():
                proposal=(line+' '+word).strip()
                if pdfmetrics.stringWidth(proposal,font,size)/mm<=w: line=proposal
                else:
                    if line: lines.append(line)
                    line=word
            lines.append(line)
        if max_lines and len(lines)>max_lines: raise ValueError(f'Text overflow: {value}')
        for i,line in enumerate(lines):self.text(x,y+i*leading,line,size,color,bold)
        return y+len(lines)*leading
    def arrow(self,x1,y1,x2,y2,color=None,width=.4,dash=None,both=False):
        color=color or C['ink'];self.line(x1,y1,x2,y2,color,width,dash)
        def head(x,y,angle):
            a=.95; b=.42
            p1=(x-a*math.cos(angle)+b*math.sin(angle),y-a*math.sin(angle)-b*math.cos(angle))
            p2=(x-a*math.cos(angle)-b*math.sin(angle),y-a*math.sin(angle)+b*math.cos(angle))
            self.poly([(x,y),p1,p2],color,.1,fill=color,close=True)
        ang=math.atan2(y2-y1,x2-x1);head(x2,y2,ang)
        if both:head(x1,y1,ang+math.pi)
    def dim_h(self,x1,x2,object_y,y,label,color=None):
        color=color or C['gray'];self.line(x1,object_y,x1,y,color,.2);self.line(x2,object_y,x2,y,color,.2)
        self.arrow(x1,y,x2,y,color,.22,both=True)
        width=pdfmetrics.stringWidth(label,'Spatial',9)/mm+3
        self.rect((x1+x2-width)/2,y-3.6,width,4.7,C['white'])
        self.text((x1+x2)/2,y-.6,label,9,color,anchor='middle')
    def dim_v(self,y1,y2,object_x,x,label,color=None):
        color=color or C['gray'];self.line(object_x,y1,x,y1,color,.2);self.line(object_x,y2,x,y2,color,.2)
        self.arrow(x,y1,x,y2,color,.22,both=True)
        self.text(x-1.2,(y1+y2)/2,label,9,color,anchor='middle',rotate=-90)
    def hatch(self,x,y,w,h,color=None,step=2.8):
        color=color or C['pink'];k=x-y-h
        while k<=x+w-y:
            pts=[]
            for xx,yy in [(x,x-k),(x+w,x+w-k),(k+y,y),(k+y+h,y+h)]:
                if x-.001<=xx<=x+w+.001 and y-.001<=yy<=y+h+.001:
                    if not any(abs(xx-a)<.01 and abs(yy-b)<.01 for a,b in pts):pts.append((xx,yy))
            if len(pts)>=2:self.line(*pts[0],*pts[1],color,.19)
            k+=step


def intersect(a,b):
    x=max(a[0],b[0]);y=max(a[1],b[1]);w=max(0,min(a[0]+a[2],b[0]+b[2])-x);h=max(0,min(a[1]+a[3],b[1]+b[3])-y)
    return [x,y,w,h]


def plan(s,m,x,top,mode):
    a=m['assumptions'];scale=25;rw=a['room']['width'];rh=a['room']['depth'];bottom=top+rh/scale
    def pt(xx,yy):return (x+xx/scale,bottom-yy/scale)
    def box(rect,fill=None,color=None,width=.4,dash=None):
        xx,yy,w,h=rect;px,py=pt(xx,yy+h);s.rect(px,py,w/scale,h/scale,fill,color,width,dash);return px,py,w/scale,h/scale
    def lab(xx,yy,t,size=9,color=None):px,py=pt(xx,yy);s.text(px,py,t,size,color,anchor='middle')
    s.rect(x,top,rw/scale,rh/scale,C['white'])
    if mode=='solo':
        box(a['solo_trial_zone']['rect'],C['pale'],C['teal'],.5,(2,1))
    elif mode=='ball':
        box(a['family_ball_zone']['rect'],C['pale'],C['teal'],.5,(2,1))
    else:
        box(a['family_ball_zone']['rect'],None,C['ghost'],.4,(1.3,1.2))
        box(a['family_chair_zone']['rect'],C['goldpale'],C['gold'],.5,(2,1))
        overlap=intersect(a['family_ball_zone']['rect'],a['family_chair_zone']['rect'])
        s.hatch(*box(overlap,None,None),C['gold'])
    if mode in ['solo','ball']:
        box(a['cabinet_swing']['rect'],None,C['pink'],.35,(1,1))
        hit=intersect(a['solo_trial_zone' if mode=='solo' else 'family_ball_zone']['rect'],a['cabinet_swing']['rect'])
        s.hatch(*box(hit,None,None),C['pink'])
    for name,label in [('sofa','диван'),('parked_table','столик'),('cabinet','шкафчик')]:
        rect=a[name]['rect'];box(rect,C['light'],C['gray'],.45)
        lab(rect[0]+rect[2]/2,rect[1]+rect[3]/2-55,label,8.7,C['gray'])
    s.line(x,top,x+rw/scale,top,C['ink'],.8);s.line(x,top,x,bottom,C['ink'],.8);s.line(x+rw/scale,top,x+rw/scale,bottom,C['ink'],.8)
    hinge=a['entrance']['hinge'];dw=a['entrance']['width'];hx,hy=pt(*hinge)
    s.line(x,bottom,hx,bottom,C['ink'],.8);s.line(hx+dw/scale,bottom,x+rw/scale,bottom,C['ink'],.8)
    s.line(hx,hy,hx,hy-dw/scale,C['gray'],.45)
    arc=[pt(hinge[0]+dw*math.cos(t),hinge[1]+dw*math.sin(t)) for t in [i*math.pi/40 for i in range(21)]]
    s.poly(arc,C['gray'],.3,(1.2,.8));s.dim_h(hx,hx+dw/scale,bottom,bottom+5,'800 У')
    s.dim_h(x,x+rw/scale,top,top-6,'4000 У');s.dim_v(top,bottom,x,x-6,'3500 У')
    if mode in ['solo','ball']:
        cx,cy=3400,1300;rad=900
        s.poly([pt(cx+rad*math.cos(t),cy+rad*math.sin(t)) for t in [math.pi/2+i*math.pi/40 for i in range(21)]],C['pink'],.4)
        s.line(*pt(cx,cy),*pt(cx-rad,cy),C['pink'],.55)
    if mode=='solo':
        box(a['mat']['rect'],None,C['teal'],.55)
        # Two positions of one conditional figure are not simultaneous users.
        main=[(1600,1400),(1850,1400),(2350,1400),(2700,1400)]
        s.poly([pt(*p) for p in main],C['ink'],1.0)
        s.line(*pt(2700,1400),*pt(2755,1400),C['ink'],.65)
        s.circle(*pt(2850,1400),95/scale,C['white'],C['ink'],.65)
        for hand in [(2580,1230),(2580,1570)]:s.line(*pt(2700,1400),*pt(*hand),C['ink'],.65);s.circle(*pt(*hand),1.1,C['teal'],C['teal'])
        lab(1850,2220,'пробный контур',9,C['teal'])
        lab(1850,2040,'2200 × 1800 У',9,C['teal'])
        path=[pt(500,0),pt(500,330),pt(3000,330),pt(3000,1150)]
        s.poly(path,C['gray'],.45,(2,1));s.arrow(*path[-2],*path[-1],C['gray'],.45,(2,1))
        lab(1600,200,'подход',8.5,C['gray'])
        py1=pt(3750,0)[1];py2=pt(3750,650)[1]
        s.dim_v(py2,py1,pt(3750,0)[0],x+rw/scale-5,'650 У')
        s.para(x-7,bottom+12,184,'Коврик 1800 × 600 У. Штриховка: пересечение с контрольным габаритом открывания.',9,3.8,color=C['gray'],max_lines=3)
    elif mode=='ball':
        # Same existing mat, repositioned for the ball scenario.
        box([1300,1300,1800,600],None,C['teal'],.45)
        for centre,sign,color in [(1500,1,C['teal']),(2400,-1,C['ink'])]:
            s.circle(*pt(centre+sign*100,1600),85/scale,C['white'],color,.6)
            s.line(*pt(centre-sign*130,1450),*pt(centre-sign*130,1750),color,1)
            for yy in [1450,1750]:s.poly([pt(centre-sign*130,yy),pt(centre+sign*210,yy),pt(1950,1600)],color,.65)
        s.circle(*pt(1950,1600),2.3,C['goldpale'],C['gold'],.45)
        c1=pt(1500,1150);c2=pt(2400,1150);s.dim_h(c1[0],c2[0],c1[1]-4,c1[1]+3,'900 У')
        lab(2100,2070,'А: мяч, двое',9,C['teal'])
        lab(2100,1920,'2200 × 1200 У',8.4,C['teal'])
        s.para(x-7,bottom+12,184,'900 - положение центров фигур для схемы. Досягаемость и траекторию мяча проверить.',9,3.8,color=C['gray'],max_lines=3)
    else:
        box(a['chair']['rect'],C['white'],C['ink'],.6)
        # Seated figure on plan; torso rotation is represented on the plan only.
        lab(2150,2250,'Б: один пользователь',8.8,C['gold'])
        s.circle(*pt(2150,1860),85/scale,C['white'],C['ink'],.5)
        s.line(*pt(1900,1830),*pt(2400,1830),C['ink'],.8)
        s.line(*pt(1980,1830),*pt(1980,1400),C['ink'],.65);s.line(*pt(2320,1830),*pt(2320,1400),C['ink'],.65)
        s.line(*pt(1900,1720),*pt(2380,1970),C['gold'],.65,(1,1))
        arc=[pt(2150+380*math.cos(t),1830+380*math.sin(t)) for t in [i*math.pi/36 for i in range(15)]]
        s.poly(arc,C['gold'],.35)
        s.para(x-7,bottom+12,184,'Зона Б 1000 × 1500 У. Общая часть А/Б - 1,20 м² Р: последовательное использование, не два занятия сразу.',9,3.8,color=C['gray'],max_lines=3)
    return pt


def figure(s,origin,floor,H,scale,pose,color=None,ghost=False,facing=1):
    color=color or C['ink'];width=.55 if ghost else .85;dash=(1.4,1) if ghost else None
    def pt(x,z):return origin+facing*x/scale,floor-z/scale
    def bones(points):s.poly([pt(x,z) for x,z in points],color,width,dash)
    r=.056*H
    if pose=='standing':
        bones([(0,.53*H),(0,.83*H),(0,.89*H)])
        bones([(0,.53*H),(.015*H,.27*H),(0,.04*H),(.13*H,0)])
        bones([(0,.83*H),(.015*H,.64*H),(.025*H,.45*H)])
        head=(0,H-r)
    elif pose=='hinge':
        bones([(-.14*H,.53*H),(.14*H,.71*H),(.19*H,.77*H)])
        bones([(-.14*H,.53*H),(.045*H,.27*H),(0,.04*H),(.13*H,0)])
        bones([(.14*H,.71*H),(.15*H,.52*H),(.15*H,.34*H)])
        head=(.22*H,.82*H)
        wx,wy=pt(.15*H,.34*H);s.rect(wx-3,wy-1.3,6,2.6,C['gray'],C['ink'],.35)
    elif pose in ['pushup_high','pushup_low']:
        high=pose.endswith('high')
        knees=(0,.04*H);hip=(.25*H,(.21 if high else .14)*H);shoulder=(.56*H,(.34 if high else .17)*H)
        bones([(-.17*H,.18*H),knees,hip,shoulder])
        bones([shoulder,((.59 if high else .49)*H,(.17 if high else .10)*H),(.60*H,0)])
        head=(.68*H,(.34 if high else .16)*H)
        bones([shoulder,(head[0]-r,head[1])])
    elif pose=='kneeling':
        bones([(-.24*H,0),(0,.04*H),(-.03*H,.26*H),(0,.50*H),(0,.56*H)])
        bones([(0,.50*H),(.16*H,.42*H),(.30*H,.44*H)])
        head=(0,.62*H)
    elif pose=='seated':
        seat=450
        bones([(0,seat),(0,seat+.31*H),(0,seat+.37*H)])
        bones([(0,seat),(.25*H,seat),(.25*H,.04*H),(.38*H,0)])
        bones([(0,seat+.31*H),(.13*H,seat+.20*H),(.08*H,seat+.29*H)])
        head=(0,seat+.43*H)
    elif pose=='supported':
        bones([(0,.53*H),(0,.83*H),(0,.89*H)])
        bones([(0,.53*H),(.015*H,.27*H),(0,.04*H),(-.13*H,0)])
        bones([(0,.83*H),(-.18*H,.63*H),(-.36*H,850)])
        head=(0,H-r)
    else:raise ValueError(pose)
    hx,hy=pt(*head);s.circle(hx,hy,r/scale,C['white'],color,width)
    return pt


def solo(m):
    s=Sheet();H=m['source_heights']['young_man']['value']
    s.text(12,19,'Один человек: пространство и движения',23,bold=True)
    s.para(12,29,396,'Обычная квартира и существующий инвентарь. Сравниваем коврик, пробную рабочую зону, подход и открытое хранение.',11.2,4.5,max_lines=2)
    s.text(12,41,'У - допущение; И - рост из прежних листов (медианы NCHS, США); Р - расчёт по модели. Все линейные размеры в мм.',9.8,C['gray'])
    s.text(18,54,'План: условная расстановка, 1:25',12.5,bold=True)
    plan(s,m,30,70,'solo')
    s.text(222,54,'Сбоку: стоя и наклон, 1:25',12.5,bold=True)
    s.line(225,68,390,68,C['gray'],.3,(2,1));s.line(225,172,390,172,C['ink'],.5)
    s.dim_v(68,172,390,398,'2600 У')
    figure(s,273,172,H,25,'standing',C['ghost'],True)
    figure(s,273,172,H,25,'hinge',C['teal'])
    s.dim_v(172-H/25,172,268,248,'1760 И')
    s.dim_v(68,172-H/25,253,257,'840 Р')
    s.para(309,82,76,'2600 - 1760 = 840 Р\nПросвет над головой стоя; не запас над поднятым инвентарём.',9.5,4.1,color=C['gray'],max_lines=5)
    s.para(310,128,76,'Серый контур - исходно.\nЦветной - другая фаза.\nАмплитуду и путь гантелей нужно измерить.',9.5,4.1,color=C['teal'],max_lines=5)
    s.arrow(287,149,289,158,C['teal'],.4,(1,1))
    s.text(222,188,'На полу: две фазы опоры, 1:20',12,bold=True)
    s.line(225,230,390,230,C['ink'],.45)
    s.line(240,230,330,230,C['teal'],1.2)
    figure(s,260,230,H,20,'pushup_high',C['ghost'],True)
    figure(s,260,230,H,20,'pushup_low',C['teal'])
    for x in [260,260+.60*H/20]:s.circle(x,230,1,C['teal'],C['teal'])
    s.dim_h(240,330,230,236,'1800 У: коврик')
    s.text(222,244,'Пропорции поз условные; крайние положения не обмерены.',9.1,C['gray'])
    blocks=[
      ('Принято для схемы','У: комната 4000 × 3500 × 2600; коврик 1800 × 600. Диван 2200 × 850, столик 1000 × 600, шкафчик 600 × 900. Это не обмер и не норматив.'),
      ('Что посчитано','Р: коврик 1,08 м²; пробная зона 3,96 м². Пересечение её с контрольным габаритом открывания - 0,72 м². Доступ к хранению согласовать с занятием.'),
      ('Что проверить в помещении','Реальные амплитуды, переход с пола, гантели, створку и подход. Просвет 650 У - результат выбранной расстановки, а не требуемая ширина прохода.')]
    for i,(head,body) in enumerate(blocks):
        x=12+i*134;s.text(x,253,head,11.3,C['teal'],True);s.para(x,261,127,body,10.2,4.4,max_lines=6)
    return s


def family(m):
    s=Sheet();hs=m['source_heights']
    s.text(12,19,'Семья: одна зона, разные пользователи',23,bold=True)
    s.para(12,29,396,'Двое с мячом, затем один пользователь у стула. Контуры наложены для сравнения этапов; одновременность всех действий не предполагается.',11.2,4.5,max_lines=2)
    s.text(12,41,'Рост (И, медианы NCHS, США): ребёнок 1340; взрослый 1630; бабушка 1580; дедушка 1730. У - допущение; Р - расчёт. Размеры в мм.',9.8,C['gray'])
    s.text(18,54,'А. Ребёнок и взрослый с мячом / 1:25',12.3,bold=True)
    s.text(218,54,'Б. Стул: следующий пользователь / 1:25',12.3,bold=True)
    plan(s,m,30,70,'ball');plan(s,m,230,70,'chair')
    s.text(12,232,'Мяч: общая зона контакта',11.3,C['teal'],True)
    s.text(148,232,'Сидя: стопы на полу',11.3,C['gold'],True)
    s.text(284,232,'Стоя: доступ к опоре',11.3,C['teal'],True)
    floor=273;scale=40
    s.line(16,floor,132,floor,C['ink'],.4);s.line(152,floor,268,floor,C['ink'],.4);s.line(288,floor,404,floor,C['ink'],.4)
    s.line(45,floor,90,floor,C['teal'],1)
    figure(s,55,floor,hs['child']['value'],scale,'kneeling',C['teal'])
    figure(s,77.5,floor,hs['adult_woman']['value'],scale,'kneeling',C['ink'],facing=-1)
    s.circle(66.25,floor-16,1.7,C['goldpale'],C['gold'],.4)
    # Ordinary chair, not the proposed product. Side profile is schematic.
    def chair(x,facing=1):
        seat=450/scale;back=850/scale;w=500/scale
        s.poly([(x,floor-back),(x,floor-seat),(x+facing*w,floor-seat)],C['gray'],.65)
        s.line(x,floor-seat,x,floor,C['gray'],.65);s.line(x+facing*w,floor-seat,x+facing*w,floor,C['gray'],.65)
        return seat,w
    chair(198);figure(s,199,floor,hs['grandmother']['value'],scale,'seated',C['gold'])
    s.dim_v(floor-450/scale,floor,222,229,'450 У')
    s.para(237,251,32,'Высоту сиденья подобрать отдельно.',8.8,3.7,color=C['gray'],max_lines=4)
    chair(344.5,-1);figure(s,360,floor,hs['grandfather']['value'],scale,'supported',C['teal'])
    s.dim_v(floor-hs['grandfather']['value']/scale,floor,370,390,'1730 И')
    s.poly([(360.5,273),(354.4,273)],C['ghost'],.5,(1,1));s.arrow(360.5,272.8,360.5,270.5,C['teal'],.3)
    captions=[
      'Виды сбоку 1:40; позы условные. Совместная передача мяча требует общей досягаемой зоны.',
      'Поворот корпуса показан на плане Б. Сиденье 450 У не выведено из роста и требует проверки.',
      'Тот же стул используют по очереди. Убрать мяч/коврик, проверить устойчивость и захват.'
    ]
    for i,text in enumerate(captions):s.para(12+i*136,282,128,text,9.2,3.9,max_lines=3)
    return s


def svg(sheet):
    rows=['<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297">','<rect width="420" height="297" fill="white"/>']
    for el in sheet.e:
        k=el['kind'];stroke=el.get('color') or 'none';fill=el.get('fill') or 'none'
        dash=f' stroke-dasharray="{el["dash"][0]} {el["dash"][1]}"' if el.get('dash') else ''
        style=f'fill="{fill}" stroke="{stroke}" stroke-width="{el.get("width",.3)}" stroke-linecap="round" stroke-linejoin="round"{dash}'
        if k=='line': rows.append(f'<line x1="{el["x1"]}" y1="{el["y1"]}" x2="{el["x2"]}" y2="{el["y2"]}" {style}/>')
        elif k=='rect':rows.append(f'<rect x="{el["x"]}" y="{el["y"]}" width="{el["w"]}" height="{el["h"]}" {style}/>')
        elif k=='circle':rows.append(f'<circle cx="{el["x"]}" cy="{el["y"]}" r="{el["r"]}" {style}/>')
        elif k=='poly':
            tag='polygon' if el.get('close') else 'polyline';points=' '.join(f'{x},{y}' for x,y in el['points']);rows.append(f'<{tag} points="{points}" {style}/>')
        else:
            transform=f' transform="rotate({el["rotate"]},{el["x"]},{el["y"]})"' if el['rotate'] else ''
            rows.append(f'<text x="{el["x"]}" y="{el["y"]}" font-family="Arial" font-size="{el["size"]/72*25.4}" font-weight="{700 if el["bold"] else 400}" fill="{el["color"]}" text-anchor="{el["anchor"]}"{transform}>{escape(el["value"])}</text>')
    rows.append('</svg>');return '\n'.join(rows)


def pdf_draw(c,sheet):
    height=297*mm
    for el in sheet.e:
        c.saveState();c.setStrokeColor(HexColor(el.get('color') or '#FFFFFF'));c.setFillColor(HexColor(el.get('fill') or '#FFFFFF'));c.setLineWidth(el.get('width',.3)*mm);c.setLineCap(1);c.setLineJoin(1)
        if el.get('dash'):c.setDash(el['dash'][0]*mm,el['dash'][1]*mm)
        stroke=int(bool(el.get('color')));fill=int(bool(el.get('fill')));k=el['kind']
        if k=='line':c.line(el['x1']*mm,height-el['y1']*mm,el['x2']*mm,height-el['y2']*mm)
        elif k=='rect':c.rect(el['x']*mm,height-(el['y']+el['h'])*mm,el['w']*mm,el['h']*mm,stroke=stroke,fill=fill)
        elif k=='circle':c.circle(el['x']*mm,height-el['y']*mm,el['r']*mm,stroke=stroke,fill=fill)
        elif k=='poly':
            p=c.beginPath();p.moveTo(el['points'][0][0]*mm,height-el['points'][0][1]*mm)
            for x,y in el['points'][1:]:p.lineTo(x*mm,height-y*mm)
            if el.get('close'):p.close()
            c.drawPath(p,stroke=stroke,fill=fill)
        else:
            c.setFillColor(HexColor(el['color']));c.setFont('SpatialBold' if el['bold'] else 'Spatial',el['size']);c.translate(el['x']*mm,height-el['y']*mm);c.rotate(-el['rotate'])
            method={'start':c.drawString,'middle':c.drawCentredString,'end':c.drawRightString}[el['anchor']];method(0,0,el['value'])
        c.restoreState()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=OUT);args=parser.parse_args();out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    pdfmetrics.registerFont(TTFont('Spatial','C:/Windows/Fonts/arial.ttf'));pdfmetrics.registerFont(TTFont('SpatialBold','C:/Windows/Fonts/arialbd.ttf'))
    m=json.loads(MODEL.read_text(encoding='utf-8'));BUILD.mkdir(parents=True,exist_ok=True)
    paths=[out/(STEM+'.pdf'),out/(STEM+'_01_solo.svg'),out/(STEM+'_02_family.svg')]
    if any(p.exists() for p in paths):raise FileExistsError('Refusing to overwrite existing deliverables')
    sheets=[solo(m),family(m)]
    c=canvas.Canvas(str(paths[0]),pagesize=(420*mm,297*mm),pageCompression=1)
    c.setTitle('Пространство и амплитуды: один человек и семья');c.setAuthor('Диплом / условная пространственная модель')
    for i,sh in enumerate(sheets):
        paths[i+1].write_text(svg(sh),encoding='utf-8');pdf_draw(c,sh);c.showPage()
    c.save();(BUILD/'layout.json').write_text(json.dumps([s.e for s in sheets],ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'pages':2,'files':[str(p) for p in paths],'vector_elements':[len(s.e) for s in sheets]}))


if __name__=='__main__':main()
