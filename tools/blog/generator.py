#!/usr/bin/env python3
"""
Markdown to HTML static blog generator for dysonhope.com.

Reads Markdown with YAML frontmatter from the content dir, renders each post
through the site templates, and regenerates the blog index and RSS feed.
Output is deterministic (stable ordering, no generation timestamps) so the
committed HTML diffs stay clean.

Usage (from the repo root):
    uv run python tools/blog/generator.py --config blog.config.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import pathlib
import re
import sys
from dataclasses import dataclass, field
from xml.sax.saxutils import escape as xml_escape

import markdown
import yaml

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
_TOKEN_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")
_CARD_RE = re.compile(
    r"<!--\s*BEGIN POST_CARD\s*-->(.*?)<!--\s*END POST_CARD\s*-->", re.DOTALL
)
_MD_STRIP_RE = re.compile(r"[#*_`>\[\]()!]+")
_HTML_TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class Post:
    title: str
    date: dt.date
    slug: str
    tags: list = field(default_factory=list)
    excerpt: str = ""
    draft: bool = False
    cover_image: str = ""
    canonical_url: str = ""
    body_html: str = ""
    body_md: str = ""
    source_name: str = ""


# ── helpers ─────────────────────────────────────────────────────────────────

def render_markdown(body_md: str) -> str:
    return markdown.markdown(body_md, extensions=["extra", "sane_lists"], output_format="html5")


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def _coerce_date(value, source_name: str) -> dt.date:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value.strip())
        except ValueError as exc:
            raise ValueError(
                f"{source_name or 'post'}: invalid date {value!r} (want ISO YYYY-MM-DD)"
            ) from exc
    raise ValueError(f"{source_name or 'post'}: unparseable date {value!r}")


def _auto_excerpt(body_md: str, limit: int = 200) -> str:
    for block in re.split(r"\n\s*\n", body_md.strip()):
        line = block.strip()
        # Skip empty blocks, markdown headings, fenced code, and any block that
        # is a raw HTML element (e.g. the leading <figure> hero image). Without
        # the HTML guard, the figure markup itself would become the excerpt.
        if (
            not line
            or line.startswith("#")
            or line.startswith("```")
            or line.startswith("<")
        ):
            continue
        # Defensively strip any inline HTML tags before flattening markdown.
        flat = _HTML_TAG_RE.sub("", line)
        flat = _MD_STRIP_RE.sub("", flat).replace("\n", " ").strip()
        flat = re.sub(r"\s+", " ", flat)
        if not flat:
            continue
        if len(flat) <= limit:
            return flat
        return flat[:limit].rsplit(" ", 1)[0].rstrip() + "…"
    return ""


def parse_post(text: str, *, source_name: str = "") -> Post:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError(f"{source_name or 'post'}: missing YAML frontmatter block")
    raw_meta, body_md = m.group(1), m.group(2)
    meta = yaml.safe_load(raw_meta) or {}
    if not isinstance(meta, dict):
        raise ValueError(f"{source_name or 'post'}: frontmatter is not a mapping")

    title = meta.get("title")
    if not title or not str(title).strip():
        raise ValueError(f"{source_name or 'post'}: required field 'title' missing")
    title = str(title).strip()

    if "date" not in meta or meta.get("date") in (None, ""):
        raise ValueError(f"{source_name or 'post'}: required field 'date' missing")
    date = _coerce_date(meta["date"], source_name)

    slug = str(meta.get("slug") or "").strip() or slugify(title)

    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    tags = [str(t).strip() for t in tags]

    body_md = body_md.lstrip("\n")
    body_html = render_markdown(body_md)

    excerpt = str(meta.get("excerpt") or "").strip() or _auto_excerpt(body_md)

    return Post(
        title=title,
        date=date,
        slug=slug,
        tags=tags,
        excerpt=excerpt,
        draft=bool(meta.get("draft", False)),
        cover_image=str(meta.get("cover_image") or "").strip(),
        canonical_url=str(meta.get("canonical_url") or "").strip(),
        body_html=body_html,
        body_md=body_md,
        source_name=source_name,
    )


def published(posts):
    """Non-draft posts, newest first (date desc, slug asc tiebreak) — deterministic."""
    live = [p for p in posts if not p.draft]
    return sorted(live, key=lambda p: (-p.date.toordinal(), p.slug))


# ── rendering ───────────────────────────────────────────────────────────────

def _fill(template: str, ctx: dict) -> str:
    return _TOKEN_RE.sub(lambda m: str(ctx.get(m.group(1), "")), template)


def _date_display(d: dt.date) -> str:
    return f"{d:%B} {d.day}, {d.year}"


def _tags_html(tags) -> str:
    return "".join(
        f'<span class="blog-tag">{html.escape(t)}</span>' for t in tags
    )


def _base_ctx(ctx: dict) -> dict:
    return {
        "site_title": html.escape(str(ctx.get("site_title", ""))),
        "blog_url": html.escape(str(ctx.get("blog_url", "")), quote=True),
        "author": html.escape(str(ctx.get("author", ""))),
    }


def _post_link(post: Post, ctx: dict) -> str:
    base = str(ctx.get("blog_url", "")).rstrip("/")
    return f"{base}/{post.slug}/"


def render_post(post: Post, template: str, ctx: dict) -> str:
    canonical = post.canonical_url or _post_link(post, ctx)
    pctx = _base_ctx(ctx)
    pctx.update({
        "title": html.escape(post.title),
        "body": post.body_html,  # already HTML
        "excerpt": html.escape(post.excerpt, quote=True),
        "date_iso": post.date.isoformat(),
        "date_display": _date_display(post.date),
        "tags_html": _tags_html(post.tags),
        "canonical_url": html.escape(canonical, quote=True),
        "cover_image": html.escape(post.cover_image, quote=True),
        "url": html.escape(_post_link(post, ctx), quote=True),
    })
    return _fill(template, pctx)


def render_index(posts, template: str, ctx: dict) -> str:
    cards_m = _CARD_RE.search(template)
    if not cards_m:
        raise ValueError("index template missing <!-- BEGIN/END POST_CARD --> block")
    card_tpl = cards_m.group(1)
    cards = []
    for post in published(posts):
        cctx = _base_ctx(ctx)
        cctx.update({
            "title": html.escape(post.title),
            "url": html.escape(f"{post.slug}/", quote=True),  # relative to /blog/
            "date_iso": post.date.isoformat(),
            "date_display": _date_display(post.date),
            "excerpt": html.escape(post.excerpt),
            "tags_html": _tags_html(post.tags),
        })
        cards.append(_fill(card_tpl, cctx))
    body = template[:cards_m.start()] + "".join(cards) + template[cards_m.end():]
    return _fill(body, _base_ctx(ctx))


def _rfc822(d: dt.date) -> str:
    return dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc) \
        .strftime("%a, %d %b %Y %H:%M:%S +0000")


def render_feed(posts, ctx: dict) -> str:
    live = published(posts)
    site_title = ctx.get("site_title", "")
    blog_url = str(ctx.get("blog_url", "")).rstrip("/")
    last_build = _rfc822(live[0].date) if live else _rfc822(dt.date(1970, 1, 1))
    items = []
    for post in live:
        link = post.canonical_url or _post_link(post, ctx)
        items.append(
            "    <item>\n"
            f"      <title>{xml_escape(post.title)}</title>\n"
            f"      <link>{xml_escape(link)}</link>\n"
            f"      <guid isPermaLink=\"true\">{xml_escape(_post_link(post, ctx))}</guid>\n"
            f"      <pubDate>{_rfc822(post.date)}</pubDate>\n"
            f"      <description>{xml_escape(post.excerpt)}</description>\n"
            "    </item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "  <channel>\n"
        f"    <title>{xml_escape(site_title)} — Writing</title>\n"
        f"    <link>{xml_escape(blog_url)}/</link>\n"
        f"    <description>Long-form writing from {xml_escape(site_title)}.</description>\n"
        f"    <lastBuildDate>{last_build}</lastBuildDate>\n"
        + "\n".join(items)
        + ("\n" if items else "")
        + "  </channel>\n"
        "</rss>\n"
    )


# ── build ───────────────────────────────────────────────────────────────────

def build(content_dir, templates_dir, out_dir, ctx) -> dict:
    content_dir = pathlib.Path(content_dir)
    templates_dir = pathlib.Path(templates_dir)
    out_dir = pathlib.Path(out_dir)

    post_tpl = (templates_dir / "post.html").read_text(encoding="utf-8")
    index_tpl = (templates_dir / "index.html").read_text(encoding="utf-8")

    posts = []
    for path in sorted(content_dir.glob("*.md")):
        posts.append(parse_post(path.read_text(encoding="utf-8"), source_name=path.name))

    out_dir.mkdir(parents=True, exist_ok=True)
    written = []

    (out_dir / "index.html").write_text(render_index(posts, index_tpl, ctx), encoding="utf-8")
    written.append("index.html")
    (out_dir / "feed.xml").write_text(render_feed(posts, ctx), encoding="utf-8")
    written.append("feed.xml")

    for post in published(posts):
        post_dir = out_dir / post.slug
        post_dir.mkdir(parents=True, exist_ok=True)
        (post_dir / "index.html").write_text(render_post(post, post_tpl, ctx), encoding="utf-8")
        written.append(f"{post.slug}/index.html")

    drafts = [p.slug for p in posts if p.draft]
    return {"published": len(written) - 2, "drafts": len(drafts),
            "written": written, "draft_slugs": drafts}


# ── CLI ─────────────────────────────────────────────────────────────────────

def _load_config(args) -> tuple:
    cfg = {}
    if args.config:
        cfg = json.loads(pathlib.Path(args.config).read_text(encoding="utf-8"))
    base = pathlib.Path(args.config).parent if args.config else pathlib.Path(".")
    content = args.content or cfg.get("content")
    templates = args.templates or cfg.get("templates")
    out = args.out or cfg.get("out")
    ctx = {
        "site_title": args.site_title or cfg.get("site_title", ""),
        "blog_url": args.blog_url or cfg.get("blog_url", ""),
        "author": args.author or cfg.get("author", ""),
    }
    if args.config:
        content = content if pathlib.Path(content).is_absolute() else base / content
        templates = templates if pathlib.Path(templates).is_absolute() else base / templates
        out = out if pathlib.Path(out).is_absolute() else base / out
    missing = [n for n, v in [("content", content), ("templates", templates), ("out", out)] if not v]
    if missing:
        sys.exit(f"error: missing required path(s): {', '.join(missing)}")
    return content, templates, out, ctx


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Markdown to HTML blog generator")
    ap.add_argument("--config", help="JSON site config (paths resolved relative to it)")
    ap.add_argument("--content", help="markdown source dir")
    ap.add_argument("--templates", help="dir with post.html + index.html")
    ap.add_argument("--out", help="output dir (the site's blog/ folder)")
    ap.add_argument("--site-title", dest="site_title", default=None)
    ap.add_argument("--blog-url", dest="blog_url", default=None)
    ap.add_argument("--author", default=None)
    args = ap.parse_args(argv)

    content, templates, out, ctx = _load_config(args)
    manifest = build(content, templates, out, ctx)
    print(f"blog: {manifest['published']} published, {manifest['drafts']} draft(s) skipped "
          f"→ {out}")
    for rel in manifest["written"]:
        print(f"  + {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
