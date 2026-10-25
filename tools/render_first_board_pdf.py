"""Render the first board's native text/table and original source photos as PDF.

The authoring JS produces the shared layout, so PDF and PPTX use one content file.
No exercise illustrations are drawn or generated here.
"""
from pathlib import Path
import json
import sys
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parent.parent
layout = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = Path(sys.argv[2])
font_dir = Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("Arial", str(font_dir / "arial.ttf")))
pdfmetrics.registerFont(TTFont("ArialB", str(font_dir / "arialbd.ttf")))
SCALE = 0.75  # CSS pixels to PDF points
W, H = layout["width"] * SCALE, layout["height"] * SCALE
C = layout["C"]
c = canvas.Canvas(str(out), pagesize=(W, H))
c.setTitle(layout.get("title", "Пользователи и движения. Исследовательский лист 1"))
c.setAuthor("Дипломный проект: рабочие исследовательские материалы")
c.setFillColor(HexColor(C["paper"]))
c.rect(0, 0, W, H, fill=1, stroke=0)


def block(value, x, y, w, h, size, bold=False, color=None):
    font = "ArialB" if bold else "Arial"
    size_pt = size * SCALE
    lines = []
    for paragraph in value.split("\n"):
        line = ""
        for word in paragraph.split():
            trial = (line + " " + word).strip()
            if line and pdfmetrics.stringWidth(trial, font, size_pt) > w * SCALE:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
    leading = size_pt * 1.16
    if len(lines) * leading > h * SCALE + 1:
        raise ValueError(f"Text overflow ({len(lines)} lines): {value}")
    c.setFont(font, size_pt)
    c.setFillColor(HexColor(color or C["ink"]))
    baseline = H - y * SCALE - size_pt
    for line in lines:
        c.drawString(x * SCALE, baseline, line)
        baseline -= leading


for e in layout["elements"]:
    if e["kind"] == "text":
        block(e["value"], e["x"], e["y"], e["w"], e["h"], e["size"], e["bold"], e["color"])
    elif e["kind"] == "image":
        image = ImageReader(str(ROOT / e["path"]))
        iw, ih = image.getSize()
        factor = min(e["w"] / iw, e["h"] / ih)
        rw, rh = iw * factor, ih * factor
        x = e["x"] + (e["w"] - rw) / 2
        y = e["y"] + (e["h"] - rh) / 2
        c.drawImage(image, x * SCALE, H - (y + rh) * SCALE, rw * SCALE, rh * SCALE)
    elif e["kind"] == "table":
        top = e["y"]
        for row, values in enumerate(e["values"]):
            left = e["x"]
            rh = e["heights"][row]
            for col, value in enumerate(values):
                cw = e["widths"][col]
                c.setFillColor(HexColor(C["teal"] if row == 0 else C["paper"]))
                c.setStrokeColor(HexColor(C["pale"]))
                c.setLineWidth(0.6)
                c.rect(left * SCALE, H - (top + rh) * SCALE, cw * SCALE, rh * SCALE, fill=1, stroke=1)
                ml, mr = e.get("marginLeft", 10), e.get("marginRight", 14)
                mt, mb = e.get("marginTop", 9), e.get("marginBottom", 8)
                block(value, left + ml, top + mt, cw - ml - mr, rh - mt - mb,
                      e.get("headerSize", 18) if row == 0 else e["size"], row == 0 or col == 0,
                      "#FFFFFF" if row == 0 else C["teal"] if col == 0 else C["ink"])
                left += cw
            top += rh
c.showPage()
c.save()
print(out)
