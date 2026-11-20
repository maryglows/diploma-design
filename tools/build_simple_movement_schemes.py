"""Readable vector people and plain-language captions, three landscape A3 sheets."""
from pathlib import Path
import argparse,json,math
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader,PdfWriter
from build_spatial_boards import Sheet,C,svg,pdf_draw

ROOT=Path(__file__).resolve().parents[1]
STEM='Simple_movement_schemes_A3_2026-11-06'

POSE={
 'stand':dict(hip=(0,23),shoulder=(0,39),head=(0,46),arms=[[(0,39),(1,31),(2,24)]],legs=[[(0,23),(0,12),(0,1),(6,1)]],weight='hand'),
 'goblet_stand':dict(hip=(0,23),shoulder=(0,39),head=(0,46),arms=[[(0,39),(9,30),(7,36)]],legs=[[(0,23),(0,12),(0,1),(6,1)]],weight='chest'),
 'squat':dict(hip=(-9,17),shoulder=(-1,31),head=(1,38),arms=[[(-1,31),(9,24),(8,31)]],legs=[[(-9,17),(9,12),(1,1),(7,1)]],weight='chest'),
 'hinge':dict(hip=(-7,25),shoulder=(12,30),head=(21,32),arms=[[(12,30),(13,20),(13,11)]],legs=[[(-7,25),(1,13),(0,1),(6,1)]],weight='hand'),
 'push_high':dict(hip=(6,12),shoulder=(25,25),head=(33,26),arms=[[(25,25),(27,13),(27,1)]],legs=[[(6,12),(-10,1),(-19,7),(-21,11)]]),
 'push_low':dict(hip=(5,6),shoulder=(25,12),head=(33,13),arms=[[(25,12),(19,7),(27,1)]],legs=[[(5,6),(-10,1),(-20,7),(-22,10)]]),
 'all_fours':dict(hip=(-5,25),shoulder=(17,25),head=(25,33),arms=[[(17,25),(18,13),(18,1)]],legs=[[(-5,25),(-4,1),(-18,1)]]),
 'reach':dict(hip=(-5,25),shoulder=(17,25),head=(25,33),arms=[[(17,25),(18,13),(18,1)],[(17,25),(32,27),(46,27)]],legs=[[(-5,25),(-4,1),(-18,1)],[(-5,25),(-20,26),(-35,26)]]),
 'wall_high':dict(hip=(-2,23),shoulder=(4,38),head=(7,45),arms=[[(4,38),(15,37),(27,36)]],legs=[[(-2,23),(-5,12),(-8,1),(-2,1)]]),
 'wall_low':dict(hip=(1,23),shoulder=(15,37),head=(20,43),arms=[[(15,37),(16,29),(27,36)]],legs=[[(1,23),(-4,12),(-8,1),(-2,1)]]),
 'seated':dict(hip=(0,18),shoulder=(0,34),head=(0,41),arms=[[(0,34),(8,26),(14,21)]],legs=[[(0,18),(16,18),(17,1),(23,1)]]),
}
POSE['stand_empty']={k:v for k,v in POSE['stand'].items() if k!='weight'}

def dumbbell(s,x,y,color):
    s.line(x-3,y,x+3,y,color,.9)
    for dx in [-3,3]:s.rect(x+dx-.9,y-2.1,1.8,4.2,C['goldpale'],C['gold'],.5)

def person(s,ox,fl,pose,scale=1,mirror=1,color=None):
    color=color or C['teal'];p=POSE[pose]
    def pt(a):return (ox+a[0]*scale*mirror,fl-a[1]*scale)
    def path(v,col=color,w=1.5):s.poly([pt(a) for a in v],col,w)
    # A second visible limb helps the side-view figure read as a person.
    for leg in p['legs']:path([(a-2,b) for a,b in leg],C['ghost'],1.1)
    path([p['hip'],p['shoulder'],(p['head'][0],p['head'][1]-4)],color,1.7)
    for leg in p['legs']:path(leg)
    for arm in p['arms']:path(arm)
    hx,hy=pt(p['head']);s.circle(hx,hy,3.5*scale,C['white'],color,.9)
    s.circle(hx+mirror*1.6*scale,hy-.4*scale,.35*scale,color,color)
    if p.get('weight')=='hand':dumbbell(s,*pt(p['arms'][0][-1]),C['gold'])
    if p.get('weight')=='chest':dumbbell(s,*pt(p['arms'][0][-1]),C['gold'])
    if pose.startswith('wall'):
        wx=ox+27*scale*mirror;s.line(wx,fl-52*scale,wx,fl,C['gray'],1.3)
    if pose=='seated':
        s.poly([pt((-4,33)),pt((-4,18)),pt((15,18))],C['gray'],.9)
        for a in [-4,15]:s.line(*pt((a,18)),*pt((a,0)),C['gray'],.9)

def front(s,ox,fl,kind,color=None):
    color=color or C['teal']
    if kind.startswith('turn'):
        s.rect(ox-11,fl-21,22,3,C['light'],C['gray'],.7)
        for xx in [ox-10,ox+10]:s.line(xx,fl-19,xx,fl,C['gray'],.7)
        s.line(ox,fl-22,ox,fl-36,color,1.7)
        for sg in [-1,1]:s.poly([(ox,fl-22),(ox+sg*8,fl-19),(ox+sg*8,fl-1),(ox+sg*13,fl-1)],color,1.4)
        s.circle(ox+(2 if kind=='turn_end' else 0),fl-43,3.5,C['white'],color,.9)
        if kind=='turn_start':
            s.line(ox-10,fl-35,ox+10,fl-35,color,1.6)
            s.poly([(ox-10,fl-35),(ox-5,fl-27),(ox+7,fl-32)],color,1.1)
            s.poly([(ox+10,fl-35),(ox+5,fl-27),(ox-7,fl-32)],color,1.1)
        else:
            s.line(ox-5,fl-35,ox+7,fl-35,color,1.6)
            s.poly([(ox-5,fl-35),(ox-2,fl-27),(ox+9,fl-32)],color,1.1)
            s.poly([(ox+7,fl-35),(ox+12,fl-29),(ox+1,fl-30)],color,1.1)
            s.circle(ox+4,fl-43,.4,color,color)
            arc=[(ox+15*math.cos(a),fl-43-10*math.sin(a)) for a in [math.pi*.9-j*math.pi*.8/20 for j in range(21)]]
            s.poly(arc,C['pink'],.45);s.arrow(*arc[-2],*arc[-1],C['pink'],.45)
    else:
        spread=12 if kind=='step_wide' else 3
        s.circle(ox,fl-46,3.5,C['white'],color,.9)
        s.line(ox,fl-42,ox,fl-23,color,1.7)
        for sg in [-1,1]:
            s.poly([(ox,fl-37),(ox+sg*8,fl-31),(ox+sg*9,fl-23)],color,1.4)
            s.poly([(ox,fl-23),(ox+sg*spread,fl-12),(ox+sg*spread,fl-1),(ox+sg*(spread+4),fl-1)],color,1.4)

def family(s,x,fl):
    # Two separate kneeling figures face a common ball, with elbows/forearms.
    for ox,scale,sg,col in [(x,0.83,1,C['teal']),(x+102,1,-1,C['ink'])]:
        def pt(a):return ox+a[0]*scale*sg,fl-a[1]*scale
        s.poly([pt((-12,1)),pt((0,1)),pt((0,16)),pt((0,34)),pt((0,37))],col,1.7)
        s.circle(*pt((0,42)),3.5*scale,C['white'],col,.9)
        s.poly([pt((0,32)),pt((12,24)),pt((22,25))],col,1.4)
    s.circle(x+48,fl-22,5,C['goldpale'],C['gold'],.7)
    s.arrow(x+30,fl-22,x+65,fl-22,C['gold'],.5,both=True)

def row(s,card,x,y):
    s.rect(x,y,396,73,'#F8FAFA',C['light'],.3)
    s.text(x+5,y+8,card['title'],15,C['teal'],True)
    # Figures have no physical scale; all stay above the drawn floor.
    fl=y+63;poses=card['poses'];left=x+5
    s.line(left+4,fl,left+171,fl,C['gray'],.4)
    if poses==['family']:
        family(s,left+29,fl)
        s.text(left+86,fl+6,card['labels'][0],10,C['gray'],anchor='middle')
    elif len(poses)==3:
        for i,p in enumerate(poses):
            ox=left+22+i*61;front(s,ox,fl,p,C['gray'] if i==0 else C['teal'])
            s.text(ox,fl+6,card['labels'][i],9.5,C['gray'],anchor='middle')
            if i<2:s.arrow(ox+19,fl-27,ox+40,fl-27,C['pink'],.55)
    else:
        for i,p in enumerate(poses):
            ox=left+34+i*93
            if p.startswith('turn'):front(s,ox,fl,p,C['gray'] if i==0 else C['teal'])
            else:person(s,ox,fl,p,.84 if p=='reach' else .9,color=C['gray'] if i==0 else C['teal'])
            s.text(ox+(5 if p=='reach' else 0),fl+6,card['labels'][i],10,C['gray'],anchor='middle')
        s.arrow(left+65,fl-28,left+92,fl-28,C['pink'],.55)
        if poses[-1]=='squat':s.arrow(left+152,fl-34,left+152,fl-13,C['pink'],.55)
        if poses[-1]=='reach':
            s.arrow(left+138,fl-31,left+161,fl-31,C['pink'],.5)
            s.arrow(left+117,fl-31,left+98,fl-31,C['pink'],.5)
    tx=x+184
    s.text(tx,y+18,'Что делает человек',11.5,C['ink'],True)
    s.para(tx,y+24,204,card['action'],11.2,4.7,max_lines=3)
    s.text(tx,y+41,'Какое место оставить',11.5,C['ink'],True)
    s.para(tx,y+47,204,card['space'],11.2,4.7,max_lines=3)
    s.text(tx,y+67,card['size'],11.2,C['teal'],True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=ROOT/'outputs/current');a=ap.parse_args();out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    pdfmetrics.registerFont(TTFont('Spatial','C:/Windows/Fonts/arial.ttf'));pdfmetrics.registerFont(TTFont('SpatialBold','C:/Windows/Fonts/arialbd.ttf'))
    data=json.loads((ROOT/'research/simple-movement-schemes-2026-11-06.json').read_text(encoding='utf-8'))
    names=['Стоя и на полу','Опоры и смена положения','Поворот, шаг и взаимодействие']
    sheets=[]
    for page in range(3):
        s=Sheet();s.text(12,19,names[page],23,bold=True)
        s.text(12,30,'Человечки показывают движение. Стрелки помогают проследить, что меняется.',12)
        s.para(12,39,396,'Размеры - прежние пробные предположения для примерки в комнате. Их ещё нужно проверить обмером. Рисунки без масштаба.',10.5,4.5,max_lines=2)
        for i,card in enumerate(data['cards'][page*3:page*3+3]):row(s,card,12,52+i*78)
        sheets.append(s)
    pdf=out/(STEM+'.pdf');combined=out/'Movement_and_form_studies_A3_2026-11-06_v2.pdf'
    svgs=[out/f'{STEM}_{i+1:02d}.svg' for i in range(3)]
    if any(p.exists() for p in [pdf,combined]+svgs):raise FileExistsError('Existing deliverables will not be overwritten')
    c=canvas.Canvas(str(pdf),pagesize=(420*mm,297*mm));c.setTitle('Простые схемы движений');c.setAuthor('Диплом: схемы для обсуждения')
    for s,p in zip(sheets,svgs):pdf_draw(c,s);c.showPage();p.write_text(svg(s),encoding='utf-8')
    c.save()
    old=PdfReader(ROOT/'outputs/current/Movement_and_form_studies_A3_2026-11-06.pdf');new=PdfReader(pdf);writer=PdfWriter()
    writer.add_page(old.pages[0])
    for p in new.pages:writer.add_page(p)
    for p in old.pages[2:]:writer.add_page(p)
    writer.add_metadata({'/Title':'Анализ движений и формы: простые схемы, версия 2'})
    with combined.open('wb') as f:writer.write(f)
    b=ROOT/'.codex-build/simple-movements-2026-11-06';b.mkdir(parents=True,exist_ok=True)
    (b/'layout.json').write_text(json.dumps([s.e for s in sheets],ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'simple_pdf':str(pdf),'combined_pdf':str(combined),'simple_pages':3,'combined_pages':7}))

if __name__=='__main__':main()
