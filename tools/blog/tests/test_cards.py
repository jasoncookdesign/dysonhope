"""Share-card contract: renderer, per-post cards, and the real-site wiring."""
import io
import pathlib
import re

import pytest
from PIL import Image

import cards
import generator

REPO = pathlib.Path(__file__).resolve().parents[3]
SITE = "https://dysonhope.com"
GROUND = (25, 25, 25)
W_H = 1200 * 630

LONG = ("An Unreasonably Long Title About Zero Tolerance Rig Reliability "
        "and Everything Else That Goes Wrong on Stage")


def _colors(im: Image.Image) -> set:
    return {c for _, c in im.getcolors(maxcolors=W_H)}


def _img(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data)).convert("RGB")


def test_card_is_a_1200x630_png():
    data = cards.render_card("The Long Version", "Rooms, gear, and reasons.", "dysonhope.com/blog/")
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert _img(data).size == (1200, 630)


def test_card_has_real_content_not_a_blank_ground():
    im = _img(cards.render_card("Press Kit", "Bios and logos.", "dysonhope.com/press/"))
    assert len(_colors(im.resize((120, 63)))) > 4


def test_title_and_description_change_the_pixels():
    a = cards.render_card("Alpha", "one", "dysonhope.com/a/")
    assert a != cards.render_card("Bravo", "one", "dysonhope.com/a/")
    assert a != cards.render_card("Alpha", "two", "dysonhope.com/a/")


def test_card_is_deterministic():
    args = ("Alpha", "one", "dysonhope.com/a/")
    assert cards.render_card(*args) == cards.render_card(*args)


def test_long_text_stays_inside_the_margins():
    im = _img(cards.render_card(LONG, LONG * 2, "dysonhope.com/blog/x/"))
    w, h = im.size
    right = im.crop((w - 48, 0, w, h))
    bottom = im.crop((0, h - 24, w, h))
    for strip in (right, bottom):
        assert _colors(strip) <= {GROUND, (156, 151, 244)}, "text or art bled into the margin"
    # positive evidence the long text rendered at all
    body = im.crop((56, 150, w - 56, h - 90))
    assert len(_colors(body)) > 4


# ── per-post cards through the generator ─────────────────────────────────────

POST = '---\ntitle: "Alpha Post"\ndate: 2026-01-01\nslug: alpha\nexcerpt: "About alpha."\n---\n\nBody.\n'
HIDDEN = '---\ntitle: "Hidden"\ndate: 2026-01-02\nslug: hidden\ndraft: true\n---\n\nBody.\n'
TPL = '<meta property="og:image" content="{{ card_url }}"><title>{{ title }}</title>'
IDX = "<!-- BEGIN POST_CARD -->{{ title }}<!-- END POST_CARD -->"
CTX = {"site_title": "S", "blog_url": "https://x.test/blog", "author": "A",
       "cards_url": "https://x.test/assets/cards/blog"}


def _site(tmp_path):
    (tmp_path / "c").mkdir()
    (tmp_path / "c/2026-01-01-alpha.md").write_text(POST)
    (tmp_path / "t").mkdir()
    (tmp_path / "t/post.html").write_text(TPL)
    (tmp_path / "t/index.html").write_text(IDX)
    return tmp_path / "c", tmp_path / "t", tmp_path / "out", tmp_path / "cards"


def test_build_writes_a_card_per_post_and_points_og_image_at_it(tmp_path):
    c, t, out, cdir = _site(tmp_path)
    generator.build(c, t, out, CTX, cards_dir=cdir)
    card = cdir / "alpha.png"
    assert _img(card.read_bytes()).size == (1200, 630)
    assert 'content="https://x.test/assets/cards/blog/alpha.png"' in (out / "alpha/index.html").read_text()


def test_build_skips_drafts(tmp_path):
    c, t, out, cdir = _site(tmp_path)
    (c / "2026-01-02-hidden.md").write_text(HIDDEN)
    generator.build(c, t, out, CTX, cards_dir=cdir)
    assert sorted(p.name for p in cdir.glob("*.png")) == ["alpha.png"]


# ── the real site ────────────────────────────────────────────────────────────

def _meta(page: str, key: str) -> str:
    m = re.search(rf'<meta (?:property|name)="{key}" content="([^"]*)"', page)
    assert m, f"missing {key}"
    return m.group(1)


def _pages():
    skip = {"index.html"}  # the home page keeps the static photo card
    return sorted(p for p in REPO.glob("**/index.html")
                  if p.relative_to(REPO).as_posix() not in skip
                  and not {".venv", "templates", "design", "node_modules"} & set(p.relative_to(REPO).parts))


def test_the_site_has_pages_to_check():
    names = {p.relative_to(REPO).parent.as_posix() for p in _pages()}
    assert {"links", "press", "privacy", "calendar", "blog"} <= names
    assert len(names) > 30


@pytest.mark.parametrize("path", _pages(), ids=lambda p: p.relative_to(REPO).parent.as_posix())
def test_every_page_has_its_own_card(path):
    rel = path.relative_to(REPO).parent.as_posix()
    page = path.read_text(encoding="utf-8")
    url = f"{SITE}/{rel}/"
    assert _meta(page, "og:url") == url
    for key in ("og:image", "twitter:image"):
        img = _meta(page, key)
        assert img.startswith(f"{SITE}/assets/cards/"), (key, img)
        assert (REPO / img.removeprefix(SITE + "/")).is_file(), f"{img} not generated"
    assert _meta(page, "og:image") == _meta(page, "twitter:image")
    assert _meta(page, "twitter:card") == "summary_large_image"
    assert _meta(page, "og:title") and _meta(page, "og:description")


def test_card_images_are_unique_per_page():
    imgs = [_meta(p.read_text(encoding="utf-8"), "og:image") for p in _pages()]
    assert len(imgs) == len(set(imgs))


def test_checked_in_site_cards_match_the_renderer():
    for name, (title, desc, label) in cards.SITE_CARDS.items():
        on_disk = (REPO / "assets/cards" / f"{name}.png").read_bytes()
        assert on_disk == cards.render_card(title, desc, label), f"{name}.png is stale; run cards.py"


@pytest.mark.parametrize("words", range(2, 22, 3))
def test_text_never_runs_into_the_url_line(words):
    title = " ".join(["Reliability"] * words)
    im = _img(cards.render_card(title, LONG * 3, "dysonhope.com/blog/x/"))
    gap = im.crop((0, 630 - 100, 1200, 630 - 86))
    assert _colors(gap) == {GROUND}, "title/description reach the footer line"


def test_fonts_use_the_basic_layout_engine_so_output_matches_across_machines():
    assert cards._archivo(40, 800).layout_engine == cards.ImageFont.Layout.BASIC
    assert cards._mono(24).layout_engine == cards.ImageFont.Layout.BASIC


def test_a_very_long_label_stays_inside_the_right_margin():
    im = _img(cards.render_card("Title", "Text.", "dysonhope.com/blog/" + "a-very-long-slug-" * 6))
    assert _colors(im.crop((1200 - 48, 0, 1200, 630))) <= {GROUND, (156, 151, 244)}
    assert _colors(im.crop((1200 - 48, 540, 1200, 600))) == {GROUND}


def test_checked_in_post_cards_match_the_renderer(tmp_path):
    import json
    cfg = json.loads((REPO / "blog.config.json").read_text())
    ctx = {k: cfg[k] for k in ("site_title", "blog_url", "author", "cards_url")}
    manifest = generator.build(REPO / cfg["content"], REPO / cfg["templates"], tmp_path / "blog", ctx,
                               cards_dir=tmp_path / "cards")
    assert manifest["published"] > 20
    on_disk = sorted(p.name for p in (REPO / cfg["cards_out"]).glob("*.png"))
    assert on_disk == sorted(p.name for p in (tmp_path / "cards").glob("*.png")), "orphan or missing post card"
    for card in (tmp_path / "cards").glob("*.png"):
        assert (REPO / cfg["cards_out"] / card.name).read_bytes() == card.read_bytes(), f"{card.name} is stale"
