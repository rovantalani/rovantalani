"""Regenerate profile artwork using fontTools and Brotli.

Usage: python generate-profile.py --sans SPACE_GROTESK.woff2 --mono JETBRAINS_MONO.woff2
Fonts are converted to outlines so GitHub needs no external resources.
"""

import argparse
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont


BIO = [
    "Founding Engineer at Maesn, building a Unified API connecting 25+ accounting and ERP systems. M.Sc. in Sociotechnical Systems Engineering from Uppsala University.",
    "My background spans full-stack development and machine learning. These days, I'm exploring AI and agentic engineering — and always happy to swap ideas about what we're building.",
]
STACK = [
    ("Programming", "TypeScript · JavaScript · Python · Java"),
    ("Web Development", "HTML · CSS · React · Vue · Node.js · Next.js · FastAPI"),
    ("Databases", "MongoDB · SQL · PostgreSQL · ChromaDB · Redis · Prisma"),
    ("Data Science", "Pandas · NumPy · R · MATLAB · SciPy · Excel"),
    ("ML / AI", "TensorFlow · PyTorch · LangChain · Keras · Scikit-learn · MCP"),
    ("Cloud & DevOps", "Azure · AWS · Docker · Git"),
]
LANGUAGES = [
    ("Swedish", "Fluent", 1),
    ("English", "Fluent", 1),
    ("Kurdish", "Fluent", 1),
    ("French", "Intermediate", 0.6),
    ("German", "Elementary", 0.3),
]
CLOSING = "Scroll down for projects and experiments, or visit my website for a deeper look into my life."


def load_font(path, weight):
    font = TTFont(path)
    if "fvar" in font:
        font = instantiateVariableFont(font, {"wght": weight}, inplace=True)
    return font


def width(font, text, size, spacing=0):
    cmap, glyphs = font.getBestCmap(), font.getGlyphSet()
    return sum(glyphs[cmap[ord(c)]].width for c in text) * size / font["head"].unitsPerEm + max(0, len(text) - 1) * spacing


def outline(font, text, x, y, size, color, spacing=0):
    glyphs, cmap = font.getGlyphSet(), font.getBestCmap()
    scale = size / font["head"].unitsPerEm
    paths = []
    for char in text:
        glyph = glyphs[cmap[ord(char)]]
        pen = SVGPathPen(glyphs, ntos=lambda n: format(n, ".2f").rstrip("0").rstrip("."))
        glyph.draw(TransformPen(pen, (scale, 0, 0, -scale, x, y)))
        if pen.getCommands():
            paths.append(pen.getCommands())
        x += glyph.width * scale + spacing
    return f'<path fill="{color}" d="{" ".join(paths)}"/>'


def wrap(font, text, size, available):
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and width(font, candidate, size) > available:
            lines.append(current)
            current = word
        else:
            current = candidate
    return lines + [current]


def render(sans, bold, mono, dark=False, mobile=False):
    bg, fg, accent, border, muted = (
        ("#271B21", "#F9EDF2", "#F387B0", "#4A3542", "#C09FAD") if dark else
        ("#FDF6F8", "#33202A", "#CE4379", "#F3DEE5", "#82626E")
    )
    w, pad, size, leading = (440, 28, 14, 22) if mobile else (900, 40, 15, 24)
    card = "#332430" if dark else "#FFFFFF"
    available = w - 2 * pad
    elements = []

    def text(font, value, x, y, font_size, color, spacing=0):
        elements.append(outline(font, value, x, y, font_size, color, spacing))

    def line(y):
        elements.append(f'<path d="M{pad} {y}H{w-pad}" stroke="{border}"/>')

    elements.append(f'<path d="M{pad} 35h32" stroke="{accent}" stroke-width="3" stroke-linecap="round"/>')
    text(bold, "Råvan Talani", pad - 2, 94, 42 if mobile else 56, fg, -1.4)
    text(mono, "FOUNDING ENGINEER · MARSEILLE", pad, 126, 9 if mobile else 10, muted, 0.5 if mobile else 1.4)
    if not mobile:
        elements.append(f'<rect x="{w-pad-70}" y="49" width="70" height="70" rx="18" fill="none" stroke="{border}"/>')
        text(bold, "RT", w-pad-55, 95, 28, accent, -1)
    line(160)
    y = 204
    text(mono, "01 / ABOUT", pad, y, 10, accent, 1.4)
    y += 43
    for paragraph in BIO:
        for value in wrap(sans, paragraph, size, available):
            text(sans, value, pad, y, size, fg)
            y += leading
        y += 18
    line(y + 1)
    y += 46
    text(mono, "02 / SKILLS", pad, y, 10, accent, 1.4)
    y += 40
    for label, tools in STACK:
        text(mono, label.upper(), pad, y, 10, muted, 1.2)
        y += 14
        x = pad
        for skill in tools.split(" · "):
            pill_width = width(mono, skill, 12, 0.36) + 26
            if x > pad and x + pill_width > w - pad:
                x = pad
                y += 36
            elements.append(f'<rect x="{x}" y="{y}" width="{pill_width}" height="28" rx="6" fill="{card}" stroke="{border}"/>')
            text(mono, skill, x + 13, y + 18, 12, muted, 0.36)
            x += pill_width + 8
        y += 60
    line(y - 5)
    y += 25
    text(mono, "SPOKEN LANGUAGES", pad, y, 10, muted, 1.2)
    y += 28
    bar_x = pad + 96
    bar_width = min(448, available) - 96
    for name, level, proficiency in LANGUAGES:
        text(mono, name, pad, y + 10, 12, fg)
        text(mono, level, bar_x + bar_width - width(mono, level, 10), y, 10, muted)
        elements.append(f'<rect x="{bar_x}" y="{y+7}" width="{bar_width}" height="6" rx="3" fill="{border}"/>')
        elements.append(f'<rect x="{bar_x}" y="{y+7}" width="{bar_width*proficiency}" height="6" rx="3" fill="{accent}" opacity="0.7"/>')
        y += 42
    line(y)
    y += 32
    for value in wrap(sans, CLOSING, size, available):
        text(sans, value, pad, y, size, muted)
        y += leading
    height = y + 12
    description = "Råvan Talani. Founding Engineer · Marseille. " + " ".join(BIO) + " Skills: " + "; ".join(f"{label}: {tools}" for label, tools in STACK)
    description += ". Spoken languages: " + "; ".join(f"{name}: {level}" for name, level, _ in LANGUAGES)
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{height}" viewBox="0 0 {w} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Råvan Talani — About &amp; Skills</title>',
        f'<desc id="desc">{escape(description)}. {escape(CLOSING)}</desc>',
        '<!-- Generated by scripts/generate-profile.py. Space Grotesk and JetBrains Mono outlines. -->',
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{height-1}" rx="12" fill="{bg}" stroke="{border}"/>',
        *elements,
        '</svg>\n',
    ])


def render_button(mono, label, w, dark=False):
    bg, fg, accent, border = ("#271B21", "#F9EDF2", "#F387B0", "#4A3542") if dark else ("#FDF6F8", "#33202A", "#CE4379", "#F3DEE5")
    height = 48
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{height}" viewBox="0 0 {w} {height}" role="img" aria-labelledby="title">',
        f'<title id="title">Visit {escape(label)}</title>',
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{height-1}" rx="12" fill="{bg}" stroke="{border}"/>',
        outline(mono, label, (w - width(mono, label, 12)) / 2, 28, 12, accent),
        '</svg>\n',
    ])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sans", required=True)
    parser.add_argument("--mono", required=True)
    args = parser.parse_args()
    sans, bold, mono = load_font(args.sans, 400), load_font(args.sans, 600), load_font(args.mono, 400)
    assets = Path(__file__).resolve().parents[1] / "assets"
    assets.mkdir(exist_ok=True)
    for dark in (False, True):
        for key, label, button_width in [("website", "rovantalani.com", 230), ("linkedin", "LinkedIn", 130)]:
            (assets / f'{key}-{"dark" if dark else "light"}.svg').write_text(render_button(mono, label, button_width, dark))
        for mobile in (False, True):
            name = f'profile-skills-{"dark" if dark else "light"}{"-mobile" if mobile else ""}.svg'
            (assets / name).write_text(render(sans, bold, mono, dark, mobile))
