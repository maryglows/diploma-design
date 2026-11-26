"""Export the bench and the two hand contacts from the 25 November sketch."""

from copy import deepcopy
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "design/preliminary-trainer-2026-11-25/bench-concept.svg"
OUTPUT = ROOT / "docs/concept/bench-grip"
SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)


def export(view, name):
    subprocess.run(
        ["rsvg-convert", "--output", str(OUTPUT / name), "-"],
        input=ET.tostring(view, encoding="utf-8"),
        check=True,
    )


def add_contact(view, center, leader, label, label_x, label_y):
    x, y = center
    ET.SubElement(view, "polyline", points=leader, fill="none", stroke="#943c28",
                  attrib={"stroke-width": "1.7", "stroke-linejoin": "round"})
    ET.SubElement(view, "circle", cx=str(x), cy=str(y), r="5.2", fill="#943c28",
                  stroke="white", attrib={"stroke-width": "1.8"})
    ET.SubElement(view, "text", x=str(label_x), y=str(label_y), fill="#702f20",
                  attrib={"font-family": "Arial, sans-serif", "font-size": "16"}).text = label


def main():
    source = ET.parse(SOURCE).getroot()
    view = ET.Element(f"{{{SVG}}}svg", width="1554", height="1134", viewBox="25 32 555 405")
    ET.SubElement(view, "rect", x="25", y="32", width="555", height="405", fill="white")
    # In this source all bench solids precede the title. The detached floor
    # panel and the leaders for the original sheet are drawn after the title.
    for part in source:
        if part.tag == f"{{{SVG}}}text":
            break
        if part.tag == f"{{{SVG}}}polygon":
            view.append(deepcopy(part))
    export(view, "bench.png")
    # Same projection and rail as diagrams() in build_visual_analogs_and_brief.py.
    # The person faces the bench from its short end. The right hand is nearer.
    add_contact(view, (118.24, 89.53), "118.24,89.53 145,52 165,52",
                "Левая кисть", 171, 57)
    add_contact(view, (152.80, 107.96), "152.80,107.96 200,101 221,101",
                "Правая кисть", 228, 106)
    export(view, "contacts.png")


if __name__ == "__main__":
    main()
