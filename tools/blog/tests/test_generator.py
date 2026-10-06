"""Generator tests: parsing, rendering, build, and the real-repo golden check."""
import datetime as dt
import json
import pathlib
import tempfile
import unittest

import generator as bloggen

REPO = pathlib.Path(__file__).resolve().parents[3]

CTX = {
    "site_title": "Jason Cook Design",
    "blog_url": "https://jasoncookdesign.com/blog",
    "author": "Jason Cook",
}

POST_A = """---
title: "Designing With Constraints"
date: 2026-06-20
tags: [design, process]
excerpt: "Why limits make better work."
---

# Designing With Constraints

A first paragraph of body text.

```python
print("hello")
```

- one
- two
"""

POST_B = """---
title: "On AI and Craft"
date: 2026-06-23
slug: ai-and-craft
tags: [ai]
---

Body for the newer post. It has no explicit excerpt.
"""

POST_DRAFT = """---
title: "Unfinished Thought"
date: 2026-06-22
draft: true
---

Not ready yet.
"""

# Regression: a post with a leading <figure> hero block and NO explicit excerpt.
# The auto-excerpt must skip the raw HTML block and use the first prose paragraph,
# never the figure markup itself.
POST_FIGURE = """---
title: "My Live Set Configuration"
date: 2026-07-04
slug: my-live-set-configuration
tags: [dj, performance]
---

<figure style="margin:0 0 1.8rem;"><img src="/assets/images/blog/my-live-set-configuration/hero.png" alt="My Live Set Configuration"><figcaption style="font-family:var(--mono);">Image: Dyson Hope</figcaption></figure>

In the eras when I played primarily with Ableton Live, people asked me how my set is built more than almost anything else.
"""

POST_TEMPLATE = """<!doctype html><html><head>
<title>{{ title }} &mdash; {{ site_title }}</title>
<meta name="description" content="{{ excerpt }}">
<link rel="canonical" href="{{ canonical_url }}">
</head><body>
<article><h1>{{ title }}</h1><time datetime="{{ date_iso }}">{{ date_display }}</time>
<div class="tags">{{ tags_html }}</div>
<div class="post-body">{{ body }}</div></article>
</body></html>"""

INDEX_TEMPLATE = """<!doctype html><html><head><title>Blog &mdash; {{ site_title }}</title></head>
<body><h1>Writing</h1><ul class="post-list">
<!-- BEGIN POST_CARD -->
<li><a href="{{ url }}">{{ title }}</a> <time datetime="{{ date_iso }}">{{ date_display }}</time>
<p>{{ excerpt }}</p></li>
<!-- END POST_CARD -->
</ul></body></html>"""


class TestSlug(unittest.TestCase):
    def test_slugify_basic(self):
        self.assertEqual(bloggen.slugify("On AI and Craft!"), "on-ai-and-craft")

    def test_slugify_collapses_separators(self):
        self.assertEqual(bloggen.slugify("  A  --  B  "), "a-b")


class TestParse(unittest.TestCase):
    def test_frontmatter_and_markdown(self):
        p = bloggen.parse_post(POST_A)
        self.assertEqual(p.title, "Designing With Constraints")
        self.assertEqual(p.date, dt.date(2026, 6, 20))
        self.assertIn("<h1>", p.body_html)
        self.assertIn("<p>", p.body_html)
        self.assertIn("<pre><code", p.body_html)  # fenced code rendered
        self.assertIn("<li>", p.body_html)    # list rendered
        self.assertEqual(p.tags, ["design", "process"])
        self.assertFalse(p.draft)

    def test_slug_derived_from_title(self):
        self.assertEqual(bloggen.parse_post(POST_A).slug, "designing-with-constraints")

    def test_explicit_slug_honored(self):
        self.assertEqual(bloggen.parse_post(POST_B).slug, "ai-and-craft")

    def test_draft_flag(self):
        self.assertTrue(bloggen.parse_post(POST_DRAFT).draft)

    def test_excerpt_autoderived_when_absent(self):
        p = bloggen.parse_post(POST_B)
        self.assertTrue(p.excerpt)  # non-empty
        self.assertIn("newer post", p.excerpt)

    def test_excerpt_skips_leading_figure_html(self):
        p = bloggen.parse_post(POST_FIGURE)
        self.assertTrue(p.excerpt)  # non-empty
        # Must be the first prose paragraph, not the hero figure markup.
        self.assertIn("Ableton Live", p.excerpt)
        for needle in ("<figure", "<img", "figcaption", "src=", "assets/images"):
            self.assertNotIn(needle, p.excerpt)

    def test_missing_title_raises(self):
        with self.assertRaises(ValueError):
            bloggen.parse_post("---\ndate: 2026-06-20\n---\nbody")

    def test_missing_date_raises(self):
        with self.assertRaises(ValueError):
            bloggen.parse_post('---\ntitle: "X"\n---\nbody')


class TestCollectAndRender(unittest.TestCase):
    def _posts(self):
        return [bloggen.parse_post(POST_A), bloggen.parse_post(POST_B),
                bloggen.parse_post(POST_DRAFT)]

    def test_sorted_desc_published_only(self):
        published = bloggen.published(self._posts())
        self.assertEqual([p.slug for p in published],
                         ["ai-and-craft", "designing-with-constraints"])

    def test_render_post_substitutes(self):
        p = bloggen.parse_post(POST_A)
        html = bloggen.render_post(p, POST_TEMPLATE, CTX)
        self.assertIn("<h1>Designing With Constraints</h1>", html)
        self.assertIn("Why limits make better work.", html)
        self.assertIn("2026-06-20", html)
        self.assertNotIn("{{", html)  # no unfilled tokens

    def test_render_index_card_per_published(self):
        html = bloggen.render_index(self._posts(), INDEX_TEMPLATE, CTX)
        self.assertEqual(html.count("<li>"), 2)  # drafts excluded
        self.assertIn("On AI and Craft", html)
        self.assertNotIn("Unfinished Thought", html)
        self.assertNotIn("{{", html)
        # newest first
        self.assertLess(html.index("On AI and Craft"),
                        html.index("Designing With Constraints"))

    def test_feed_items(self):
        xml = bloggen.render_feed(self._posts(), CTX)
        self.assertIn("<rss", xml)
        self.assertEqual(xml.count("<item>"), 2)
        self.assertIn("On AI and Craft", xml)
        self.assertNotIn("Unfinished Thought", xml)


class TestBuild(unittest.TestCase):
    def _setup_tree(self):
        d = pathlib.Path(tempfile.mkdtemp())
        (d / "content").mkdir()
        (d / "templates").mkdir()
        (d / "content" / "2026-06-20-a.md").write_text(POST_A)
        (d / "content" / "2026-06-23-b.md").write_text(POST_B)
        (d / "content" / "2026-06-22-draft.md").write_text(POST_DRAFT)
        (d / "templates" / "post.html").write_text(POST_TEMPLATE)
        (d / "templates" / "index.html").write_text(INDEX_TEMPLATE)
        return d

    def test_build_outputs_exist(self):
        d = self._setup_tree()
        out = d / "blog"
        bloggen.build(d / "content", d / "templates", out, CTX)
        self.assertTrue((out / "index.html").exists())
        self.assertTrue((out / "ai-and-craft" / "index.html").exists())
        self.assertTrue((out / "designing-with-constraints" / "index.html").exists())
        self.assertFalse((out / "unfinished-thought" / "index.html").exists())  # draft
        self.assertTrue((out / "feed.xml").exists())

    def test_build_deterministic(self):
        d = self._setup_tree()
        out1, out2 = d / "b1", d / "b2"
        bloggen.build(d / "content", d / "templates", out1, CTX)
        bloggen.build(d / "content", d / "templates", out2, CTX)
        for rel in ["index.html", "feed.xml", "ai-and-craft/index.html"]:
            self.assertEqual((out1 / rel).read_bytes(), (out2 / rel).read_bytes(),
                             f"non-deterministic: {rel}")


class TestGolden(unittest.TestCase):
    def test_golden_repo_regenerates_without_diff(self):
        """Rebuilding the committed content must reproduce the committed blog/ byte for byte."""
        cfg = json.loads((REPO / "blog.config.json").read_text())
        ctx = {k: cfg[k] for k in ("site_title", "blog_url", "author")}
        out = pathlib.Path(tempfile.mkdtemp()) / "blog"
        manifest = bloggen.build(REPO / cfg["content"], REPO / cfg["templates"], out, ctx)
        self.assertGreater(manifest["published"], 20)  # real posts were rendered
        for rel in manifest["written"]:
            self.assertEqual((out / rel).read_bytes(), (REPO / cfg["out"] / rel).read_bytes(),
                             f"generated output differs from committed: {rel}")
