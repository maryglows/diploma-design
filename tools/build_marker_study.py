"""Lay out the marker studies for A4 printing from editable captions and unmodified PNGs."""
import json
import os
import shutil
import subprocess
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "design/marker-study-2026-11-26"
OUT = ROOT / "outputs/current"
STEM = "Marker_concepts_in_use_A4_2026-11-26"
ASSETS = "../../design/marker-study-2026-11-26"
BOARDS = json.loads((DESIGN / "boards.json").read_text(encoding="utf-8"))
PHOTOS = json.loads((ROOT / "research/analogs/visual-brief-2026-11-25/body-photo-sources.json").read_text(encoding="utf-8"))
STYLE = """
@page{size:A4;margin:0}*{box-sizing:border-box}html,body{margin:0;padding:0}
body{background:#eae7df;color:#292926;font:10pt/1.28 "Segoe UI",Arial,sans-serif}
section{position:relative;background:white;width:210mm;height:297mm;margin:5mm auto;padding:10mm 13mm 11mm;break-after:page}
section:last-child{break-after:auto}
header{border-top:1.05mm solid #28485a;padding-top:2mm;height:39mm}
.run{display:flex;justify-content:space-between;color:#335164;font-size:9pt;font-weight:650}
h1{font:normal 23pt/1.04 Georgia,serif;margin:2.3mm 0 1.7mm;letter-spacing:-.24mm}
header p{margin:0;max-width:180mm;font-size:10.3pt;line-height:1.23}
footer{position:absolute;left:13mm;right:13mm;bottom:7mm;border-top:.24mm solid #bebaba;padding-top:1.2mm;font-size:8.3pt;color:#575c59;display:flex;justify-content:space-between}
.quads{display:grid;grid-template-columns:1fr 1fr;gap:3.5mm 7mm}
.tile{height:91mm}.frame{position:relative;width:100%;height:55mm;overflow:hidden;background:white}
.frame svg{width:82.5mm;height:55mm;margin:auto;display:block}.tile h2,.room-notes h2{font-size:12.1pt;font-weight:650;line-height:1.1;margin:1.6mm 0 1mm;color:#213c4a}
.tile p,.room-notes p{margin:0;font-size:10.15pt;line-height:1.26}.step{color:#9b592c;margin-right:1.5mm;font-variant-numeric:tabular-nums}
.duo{border-top:.35mm solid #b8a69a;display:grid;grid-template-columns:1fr 1fr;gap:7mm;padding:2.5mm 0;margin-top:3.5mm}
.duo strong{display:block;font-size:10pt;color:#80502f;margin:0 0 1mm}
.duo p{font-size:9.6pt;line-height:1.27;margin:0}
.room header{height:32mm}.hero{width:100%;height:100mm;display:block;object-fit:contain;background:#fff}
.room-bottom{display:grid;grid-template-columns:92mm 1fr;gap:6mm;margin-top:3mm}
.plan-title{font-size:10.2pt;color:#234350;font-weight:650;margin:0 0 1mm}
.plan{width:100%;height:69mm;display:block}.plan-note{margin:0;color:#59615e;font-size:8.8pt}
.room-notes h2{font-size:10.4pt;margin:0 0 .7mm}
.room-notes p{font-size:9.25pt;line-height:1.22;margin:0 0 2mm}
.room .duo{margin-top:2.5mm}
.photo-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:2.7mm 4mm}
.group{grid-column:1/-1;font-weight:650;font-size:10.1pt;color:#80502f;border-bottom:.25mm solid #cbbcae;padding-bottom:1mm}
.photo img{width:100%;height:31mm;object-fit:contain;display:block;margin-bottom:1mm}
.photo b{font-size:10.4pt;color:#244352;display:block;line-height:1.1}.photo p{font-size:9pt;margin:1mm 0}
a{color:#275169;text-decoration:underline;text-underline-offset:1.1pt}.photo a{font-size:8.2pt}
.sources{margin-top:3mm;padding-top:2mm;border-top:.25mm solid #cbbcae;font-size:8.8pt}
.opening header{height:32mm}.overview{width:100%;height:201mm;object-fit:contain;display:block}
@media print{body{background:white}section{margin:0}.tile,.photo{break-inside:avoid}}
"""


CALLOUTS = {
    "bench-contact": [("Накладка",230,149),("Две кисти",350,101),("Профиль рамы",378,183),("Край коврика",484,249)],
    "bench-storage": [("Полка",484,422),("Рукоять",509,259),("Перегородка",536,281),("Личинка замка",381,262)],
    "cabinet-seat": [("Край панели",128,307),("Ось поворота",411,198),("Передняя ножка",482,314),("Палец фиксатора",344,294)],
    "cabinet-access": [("Место локтя",211,156),("Поперечина",461,177),("Гнездо веса",462,364),("Стойка рамы",468,278)],
}


def imgview(key, index):
    # The four windows are print crops; the original marker drawings stay intact.
    x = index % 2 * 768
    y = index // 2 * 512
    picture = f'<image href="{ASSETS}/{key}.png" x="{-x}" y="{-y}" width="1536" height="1024"/>'
    if key == "cabinet-seat" and index == 1:
        picture = f'<image href="{ASSETS}/hinge.png" width="768" height="512"/>'
    mark = ""
    if key in CALLOUTS:
        label, tx, ty = CALLOUTS[key][index]
        w = 20 + len(label)*15
        mark = (f'<path d="M{w} 33 L{w+25} 33 L{tx} {ty}" fill="none" stroke="white" stroke-width="7"/>'
                f'<path d="M{w} 33 L{w+25} 33 L{tx} {ty}" fill="none" stroke="#2e5366" stroke-width="3"/>'
                f'<circle cx="{tx}" cy="{ty}" r="6" fill="#2e5366" stroke="white" stroke-width="2"/>'
                f'<rect x="6" y="11" width="{w}" height="42" rx="7" fill="#264759"/>'
                f'<text x="16" y="40" fill="white" font-family="Segoe UI,Arial" font-size="26">{label}</text>')
    return '<div class="frame"><svg viewBox="0 0 768 512">' + picture + mark + '</svg></div>'


def room_plan(cabinet):
    # A functional layout, intentionally without dimensional claims.
    furniture = """
      <rect x="63" y="27" width="105" height="33" rx="3" fill="#ddb58a" stroke="#71543d"/>
      <path d="M64 29v29" stroke="#2d4b5c" stroke-width="4"/>
      <text x="118" y="48" text-anchor="middle">скамья</text>
      <path d="M65 60v34q31 0 34-34" fill="#eedfce" fill-opacity=".6" stroke="#996139" stroke-dasharray="3 2"/>
      <text x="90" y="109">ход дверцы</text>
      <path d="M40 49h19" stroke="#286081" stroke-width="2" marker-end="url(#tip)"/>
      <text x="15" y="74">к хвату</text>
      <path d="M194 48h-21" stroke="#286081" stroke-width="2" marker-end="url(#tip)"/>
      <text x="179" y="71">коврик</text>
    """ if not cabinet else """
      <rect x="57" y="24" width="101" height="34" rx="3" fill="#ddb58a" stroke="#71543d"/>
      <path d="M128 24v34M156 25v32" stroke="#71543d" stroke-width="1.5"/>
      <text x="89" y="45" text-anchor="middle">шкаф</text>
      <rect x="61" y="58" width="65" height="34" fill="#efdfce" stroke="#996139" stroke-dasharray="3 2"/>
      <path d="M53 23v51m109-51v51" stroke="#465460" stroke-width="3"/>
      <text x="62" y="107">ход сиденья</text>
      <path d="M196 44h-29" stroke="#286081" stroke-width="2" marker-end="url(#tip)"/>
      <text x="172" y="64">к хвату</text>
    """
    return ("""<svg class="plan" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 270 200" role="img" aria-label="План подходов и прохода">
      <defs><marker id="tip" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="3.5" markerHeight="3.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10" fill="#286081"/></marker></defs>
      <rect width="270" height="200" rx="4" fill="#faf8f2"/>
      <path d="M12 157V12H257V187H43" stroke="#737771" stroke-width="3" fill="none"/>
      <path d="M16 15h60" stroke="#87adbb" stroke-width="3"/>
      <g font-family="Segoe UI,Arial" font-size="10" fill="#243b47">""" + furniture + """
      <rect x="42" y="118" width="111" height="28" fill="#d9e2d0" stroke="#8d9e86" rx="3"/>
      <text x="97" y="136" text-anchor="middle">место коврика</text>
      <rect x="214" y="95" width="39" height="61" rx="5" fill="#e7e3d9" stroke="#a4a099"/>
      <text x="234" y="128" text-anchor="middle" font-size="9">диван</text>
      <path d="M18 168h158q15 0 15-14v-22" stroke="#286081" fill="none" stroke-width="2" stroke-dasharray="4 3" marker-end="url(#tip)"/>
      <text x="79" y="181">проход по комнате</text></g></svg>""")


def note_pair(board):
    return (f'<div class="duo"><div><strong>Связь с исследованием</strong><p>{escape(board["back"])}</p></div>'
            f'<div><strong>Что проверить на макете</strong><p>{escape(board["check"])}</p></div></div>')


def room(board):
    notes = "".join(f"<h2>{escape(k)}</h2><p>{escape(t)}</p>" for k, t in board["notes"])
    return (f'<img class="hero" src="{ASSETS}/{board["key"]}.png" alt="{escape(board["title"])}">'
            '<div class="room-bottom"><div><p class="plan-title">Вид сверху</p>'
            + room_plan(board["model"] == "Шкаф")
            + '<p class="plan-note">Условная гостиная. Положение предметов и маршруты показаны без масштаба.</p></div>'
            + f'<div class="room-notes">{notes}</div></div>' + note_pair(board))


def cards(board):
    tiles = []
    for i, (title, caption) in enumerate(board["tiles"]):
        step = f'<span class="step">{i+1}.</span>' if board["kind"] == "scene" else ""
        tiles.append(f'<article class="tile">{imgview(board["key"], i)}<h2>{step}{escape(title)}</h2>'
                     f'<p>{escape(caption)}</p></article>')
    return '<div class="quads">' + "".join(tiles) + '</div>' + note_pair(board)


def page(n, label, title, lead, content, kind):
    return (f'<section class="{kind}" id="p{n}"><header><div class="run"><span>{escape(label)}</span>'
            f'<span>Диплом · 26.11.2026</span></div><h1>{escape(title)}</h1><p>{escape(lead)}</p></header>'
            f'{content}<footer><span>Поисковый эскиз · геометрия и нагрузки требуют проверки</span>'
            f'<span>{n} / 14</span></footer></section>')


def movement_page():
    labels = ["Дети", "Молодые взрослые", "Пожилые"]
    contacts = ["Длина коврика по кисти и стопе.", "Мягкая цель в пределах досягаемости.", "Место для спины и обеих стоп.",
                "Коврик под колени и ладони.", "Одна гантель и пол перед мебелью.", "Две гантели и место позади таза.",
                "Сиденье и пол под стопами.", "Фиксированный хват для двух рук.", "Свободный ход локтей у сиденья."]
    owners = ["NHFT"]*3 + ["ACE","ACE","Kathryn Alexander"] + ["NHS"]*3
    cells = []
    for i, (r, contact, owner) in enumerate(zip(PHOTOS, contacts, owners)):
        if i % 3 == 0:
            cells.append(f'<div class="group">{labels[i//3]}</div>')
        cells.append(f'<div class="photo"><img alt="{escape(r["label"])}" src="../../{r["path"]}">'
                     f'<b>{escape(r["label"])}</b><p>{contact}</p><a href="{r["page"]}">{owner} · фото</a></div>')
    return page(14, "Обе компоновки  /  Девять движений", "Какая деталь нужна в каждом движении",
                "Шесть первых движений используют пол или отдельный инвентарь. В трёх последних тело опирается на сиденье или поручень.",
                '<div class="photo-grid">'+"".join(cells)+'</div><div class="sources">Фотографии из источников исследования. '
                '<a href="https://www.nasm.org/resource-center/exercise-library/dumbbell-romanian-deadlift">Описание наклона с гантелями · NASM</a>. '
                'Проектные подписи указывают на контакты, которые следует проверить в обеих компоновках.</div>', "movement")


def print_pdf(html_path):
    candidates = [shutil.which(cmd) for cmd in ("chromium", "google-chrome", "msedge")]
    candidates += [Path(os.environ.get("ProgramFiles", "")) / "Google/Chrome/Application/chrome.exe",
                   Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft/Edge/Application/msedge.exe"]
    browser = next((str(path) for path in candidates if path and Path(path).is_file()), None)
    if not browser:
        raise RuntimeError("Укажите установленный Chromium или откройте HTML и сохраните в PDF A4 с полями 0.")
    build = ROOT / ".codex-build/marker-room"
    build.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=build, ignore_cleanup_errors=True) as folder:
        raw = Path(folder) / "print.pdf"
        subprocess.run([browser, "--headless", "--disable-extensions", "--disable-gpu",
                        "--no-first-run", "--disable-background-networking", "--no-pdf-header-footer",
                        "--user-data-dir=" + str(Path(folder) / "profile"),
                        "--print-to-pdf=" + str(raw), html_path.as_uri()], check=True, timeout=120)
        with pymupdf.open(raw) as doc:
            if len(doc) != 14:
                raise RuntimeError(f"Ожидалось 14 листов, получено {len(doc)}")
            # Print-quality image compression without reducing pixel dimensions.
            doc.rewrite_images(quality=92, bitonal=False)
            doc.save(html_path.with_suffix(".pdf"), garbage=4, deflate=True)


def main():
    opening = (f'<img class="overview" src="{ASSETS}/room-compare.png" alt="Сверху скамья, снизу шкаф">'
               '<div class="duo"><div><strong>Сверху · Скамья / стр. 2–7</strong><p>Сиденье всегда доступно. '
               'Свободный левый торец нужен для подхода к поручню, правый — для выдачи коврика.</p></div>'
               '<div><strong>Снизу · Шкаф / стр. 8–13</strong><p>Сиденье поднято между занятиями. '
               'Для раскрытия нужен пол перед фасадом, для хвата — место у правого торца.</p></div></div>')
    pages = [page(1, "Сравнение компоновок", "Два варианта в одной гостиной",
                  "Один ракурс от двери показывает оба предмета между занятиями. Видимое дерево, спокойные фасады и графитовые детали развивают выбранный ориентир BORK.", opening, "opening")]
    for n, b in enumerate(BOARDS, 2):
        typ = {"room":"Размещение", "part":"Детали", "scene":b.get("group", "")}[b["kind"]]
        label = f'Вариант {1 if n <= 7 else 2}  /  {b["model"]}  /  {typ}'
        pages.append(page(n, label, b["title"], b["lead"], room(b) if b["kind"] == "room" else cards(b), b["kind"]))
    pages.append(movement_page())
    html = '<!doctype html><html lang="ru"><meta charset="utf-8"><title>Два тренажёра в комнате · Маркерные листы</title>'
    html_path = OUT / (STEM + ".html")
    markup = html + "<style>" + STYLE + "</style><body>" + "\n".join(pages) + "</body></html>"
    html_path.write_text("\n".join(line.rstrip() for line in markup.splitlines()) + "\n", encoding="utf-8")
    print_pdf(html_path)


if __name__ == "__main__":
    main()
