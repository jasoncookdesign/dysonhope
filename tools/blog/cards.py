"""Share cards: 1200x630 PNGs for og:image / twitter:image.

Fonts are vendored in ./fonts (Archivo and IBM Plex Mono, SIL OFL, licences alongside)
so a card renders the same on any machine. Output is deterministic.

CLI: `uv run python tools/blog/cards.py` writes the site-page cards to assets/cards/.
Post cards are written by generator.build.
"""
import argparse
import io
import pathlib

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
FONTS = HERE / "fonts"
LOGO = REPO / "assets/images/dyson-hope-logo-square.png"

W, H = 1200, 630
MARGIN = 56
GROUND = (25, 25, 25)
TEXT = (237, 237, 237)
TEXT_2 = (156, 156, 160)
ACCENT = (156, 151, 244)

# Cards for pages that are not generated. The home page keeps the static photo card.
# name -> (title, description, url label). Copy mirrors each page's og:title/og:description.
SITE_CARDS = {
    "links": ("Links", "Electronic music producer, DJ, and founder of SIGIL.ZERO Records.",
              "dysonhope.com/links/"),
    "press": ("Press Kit", "Bios, mixes, releases, press photos, logos, and booking contact.",
              "dysonhope.com/press/"),
    "privacy": ("Privacy Policy", "How this site handles visitor data and analytics.",
                "dysonhope.com/privacy/"),
    "calendar": ("Book the Studio", "Studio sessions with Dyson Hope in 2, 3, or 4 hour blocks.",
                 "dysonhope.com/calendar/"),
    "blog": ("Writing", "Notes on electronic music, the underground, and the craft behind the records.",
             "dysonhope.com/blog/"),
}


def _archivo(size: int, weight: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(FONTS / "Archivo.ttf"), size, layout_engine=ImageFont.Layout.BASIC)
    font.set_variation_by_axes([weight, 100])  # axes: wght, wdth
    return font


def _mono(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / "PlexMono-Medium.ttf"), size, layout_engine=ImageFont.Layout.BASIC)


def _wrap(text: str, font, width: int) -> list:
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if line and font.getlength(trial) > width:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


def _fit(text: str, make_font, width: int, max_lines: int, sizes) -> tuple:
    """Largest size whose wrap fits max_lines; at the smallest size, ellipsize."""
    for size in sizes:
        font = make_font(size)
        lines = _wrap(text, font, width)
        if len(lines) <= max_lines:
            return font, size, lines
    lines = lines[:max_lines]
    while lines[-1] and font.getlength(lines[-1] + "…") > width:
        lines[-1] = lines[-1][:-1].rstrip()
    lines[-1] += "…"
    return font, size, lines


def render_card(title: str, description: str, label: str) -> bytes:
    im = Image.new("RGB", (W, H), GROUND)
    d = ImageDraw.Draw(im)
    inner = W - 2 * MARGIN - 24

    if LOGO.is_file():
        logo = Image.open(LOGO).convert("RGB").resize((56, 56), Image.LANCZOS)
        im.paste(logo, (MARGIN, 44))
    d.text((MARGIN + 76, 72), "DYSON HOPE", font=_mono(24), fill=ACCENT, anchor="lm")
    d.rectangle((MARGIN, 124, MARGIN + 96, 129), fill=ACCENT)

    t_font, t_size, t_lines = _fit(title, lambda s: _archivo(s, 800), inner, 3, range(76, 43, -4))
    d_font, d_size, d_lines = _fit(description, lambda s: _archivo(s, 500), inner, 2, range(34, 25, -2))
    t_lead, d_lead = int(t_size * 1.08), int(d_size * 1.4)

    y = 164
    for line in t_lines:
        d.text((MARGIN, y), line, font=t_font, fill=TEXT)
        y += t_lead
    y += 20
    for line in d_lines:
        d.text((MARGIN, y), line, font=d_font, fill=TEXT_2)
        y += d_lead

    foot = _mono(24)
    while len(label) > 1 and foot.getlength(label) > inner:
        label = label[:-2].rstrip("-/ ") + "…"
    d.text((MARGIN, H - 56), label, font=foot, fill=ACCENT, anchor="ls")

    out = io.BytesIO()
    im.save(out, "PNG", optimize=True)
    return out.getvalue()


def write_card(path, title: str, description: str, label: str) -> None:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(render_card(title, description, label))


def build_site_cards(repo=REPO) -> list:
    out = pathlib.Path(repo) / "assets/cards"
    for name, (title, desc, label) in SITE_CARDS.items():
        write_card(out / f"{name}.png", title, desc, label)
    return sorted(SITE_CARDS)


def main(argv=None) -> int:
    argparse.ArgumentParser(description="Write the site-page share cards to assets/cards/").parse_args(argv)
    print("cards:", ", ".join(build_site_cards()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
