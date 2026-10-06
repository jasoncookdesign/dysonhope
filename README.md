# Dyson Hope — Official Website

Website for Dyson Hope, electronic music producer and DJ based in Austin, Texas. Founder and label boss of [SIGIL.ZERO Records](https://sigilzero.com).

**Live site:** [dysonhope.com](https://dysonhope.com)

---

## About Dyson Hope

Dyson Hope got his start as an FM radio DJ at WRCT 88.3 FM Pittsburgh before moving into the underground rave scene in Los Angeles in the late '90s, where he spun drum & bass and wrote original records. After years of international bookings and a nomadic stretch through London, Berlin, Barcelona, Istanbul, and elsewhere, he settled in Austin, Texas. Today he produces genre-defying electronic music spanning tech house, progressive house, techno, and beyond — music built for dark rooms and dancefloors.

In 2026 he founded **SIGIL.ZERO Records**, an underground electronic imprint with a ruthless focus on quality, longevity, and DJ-first releases.

---

## Discography (Selected)

| Year | Title | Notes |
| ---- | ----- | ----- |
| 2026 | Drums in the Deep | Bass-heavy tech house |
| 2026 | Afterphase | Stripped-down progressive tech house |
| 2026 | Bounce Ritual | Swinging body-first groove |
| 2026 | Edge of the Night | Peak-time progressive tech house anthem |
| 2026 | Got a Body | Dark, hypnotic tech house |
| 2025 | Need More Drugs | Breakbeat collab with NOTOTO |
| 2023 | Get Up and Go | Second album — all house music |
| 2022 | At Your Own Risk | Debut album, released Winter Solstice 2022 |

---

## Listen

| Platform | Link |
| -------- | ---- |
| Spotify | [Open](https://open.spotify.com/artist/61OXIOIVIfdZtFBZG4cY4J) |
| Beatport | [Open](https://www.beatport.com/artist/dyson-hope/2262866) |
| SoundCloud | [Open](https://soundcloud.com/dyson-hope) |
| YouTube | [Open](https://www.youtube.com/@DysonHope) |
| Apple Music | [Open](https://music.apple.com/us/artist/dyson-hope/1658448375) |
| Amazon Music | [Open](https://music.amazon.com/artists/B0BP9TJ341/dyson-hope) |
| Bandcamp | [Open](https://dysonhope.bandcamp.com/) |

---

## Connect

- **Booking:** [booking@dysonhope.com](mailto:booking@dysonhope.com)
- **Production / collaboration:** [studio@dysonhope.com](mailto:studio@dysonhope.com)
- **General:** [info@dysonhope.com](mailto:info@dysonhope.com)
- **Facebook:** [DysonHopeMusic](https://facebook.com/DysonHopeMusic)
- **Instagram:** [DysonHopeMusic](https://instagram.com/DysonHopeMusic)
- **Label:** [sigilzero.com](https://sigilzero.com)

---

## Tech Stack

The site is a hand-built static site — no framework, no JavaScript libraries, and no build server.

- **HTML5** — hand-authored pages, no framework templating. The `/blog/` section is rendered from Markdown to committed static HTML by a small generator (see [Writing (Blog)](#writing-blog)); everything served is still plain static HTML.
- **CSS** — a single hand-written design system in `assets/css/dysonhope.css` (CSS custom properties for color, type, spacing, and motion), supplemented by small page-specific `<style>` blocks inlined in each page's `<head>`.
- **Typography** — Google Fonts: [Archivo](https://fonts.google.com/specimen/Archivo) (display), [Inter](https://fonts.google.com/specimen/Inter) (body), and [IBM Plex Mono](https://fonts.google.com/specimen/IBM+Plex+Mono) (labels/meta).
- **Icons** — [Font Awesome](https://fontawesome.com) (webfont via `css/all.css`). The brand mark and wordmark are inline SVG.
- **Media** — a looping MP4 video hero (`assets/video/hero-loop.mp4`) with a static poster image fallback; a Spotify embed player on the homepage.
- **Analytics** — [Google Tag Manager](https://tagmanager.google.com) (container `GTM-5T87PLM6`). Interactive elements carry declarative `data-track` / `data-*` attributes (see [Analytics](#analytics)).

There is **no** Bootstrap, jQuery, carousel/lightbox/scroll-animation library, SCSS toolchain, or server-side code. Earlier versions of this site shipped a purchased HTML template with that stack; it has been fully removed.

### Repository layout

```
.
├── index.html              # homepage
├── calendar/index.html     # legacy redirect → /#schedule (studio booking is now on-domain)
├── links/index.html        # link-in-bio hub
├── privacy/index.html      # privacy policy
├── blog/                   # GENERATED blog — listing, per-post pages, RSS (do not hand-edit)
├── content/blog/           # blog post sources (Markdown + YAML frontmatter)
├── templates/blog/         # blog templates (post.html, index.html)
├── blog.config.json        # blog generator config (paths + site metadata)
├── tools/blog/             # blog generator + scheduled-publishing drip (Python, tests in tests/)
├── launchd/                # daily drip job for the publishing Mac (install.sh / uninstall.sh)
├── docs/blog-drip/         # drip requirements and architecture
├── pyproject.toml, uv.lock # Python deps for tools/blog (run with uv)
├── CNAME                    # custom domain (dysonhope.com)
└── assets/
    ├── css/dysonhope.css    # the design system (only stylesheet)
    ├── images/              # covers, favicon, hero poster, textures
    ├── video/hero-loop.mp4  # homepage hero loop
    ├── svg/                 # brand logo source files
    ├── press/               # press kit (logos, photo, zip)
    └── plugins/font-awesome # icon webfont (css/ + webfonts/)
```

---

## Development

No build step is required. Edit the HTML/CSS directly.

- **View locally:** open `index.html` in a browser, or serve the folder from any static server, e.g.:

  ```bash
  python3 -m http.server 8000
  # then visit http://localhost:8000
  ```

  A static server (rather than `file://`) is recommended so that relative links between `/`, `/links/`, and `/calendar/` resolve the way they do in production.

- **Deploy:** the site is served via GitHub Pages on the custom domain in `CNAME` (`dysonhope.com`). Pushing to the default branch publishes it; there is nothing to compile.

### Site pages and features

- **`index.html`** — main artist page: video hero, statement bar, **Listen** (platform links + Spotify embed), **Works** (release grid), about/interlude, **Contact** (mailto CTAs), **Schedule** (an always-visible Cal.com inline embed for booking studio sessions), and a social/connections footer. Single-page anchor nav (`#home`, `#listen`, `#works`, `#contact`); `#schedule` is bookmarkable but intentionally not in the nav.
- **`links/index.html`** — "link in bio" hub with featured releases (per-platform outbound links) and streaming/social tiles. Self-contained inline styling on top of the shared design system.
- **`calendar/index.html`** — a legacy-compatibility redirect (`meta refresh` + JS fallback) to the on-domain `/#schedule` embed. Studio booking previously lived here as a branded interstitial that forwarded visitors to an external scheduler; it now happens inline on the homepage. The route is kept so any existing shared `/calendar/` links still resolve.

> **Schedule vs. Calendar.** "Schedule" names the **studio-booking** function (the Cal.com embed at `#schedule`). "Calendar" is reserved for a future **live-events** section (`#calendar`, currently commented out) listing where and when Dyson Hope is playing. Studio bookings run on the shared Cal.com account `jasoncookdesign` (event: [`cal.com/jasoncookdesign/studio`](https://cal.com/jasoncookdesign/studio), 120 / 180 / 240-minute options).
- **`blog/`** — the writing section, reachable from the **Blog** link in the main navigation (between Works and Links). The pages here are generated; see [Writing (Blog)](#writing-blog).

### Writing (Blog)

The `/blog/` section is long-form writing — studio notes and music writing — reachable from the **Blog** link in the main navigation. It keeps the site's "commit static HTML, no server" model: posts are authored in Markdown and rendered to static HTML by a small generator, and the **rendered HTML is committed** — there is no CMS, build server, or CI.

```
content/blog/<YYYY-MM-DD-slug>.md   Post source (Markdown + YAML frontmatter)
templates/blog/post.html            Per-post template (site chrome + typography)
templates/blog/index.html           Listing template; the card markup between
                                     <!-- BEGIN POST_CARD --> / <!-- END POST_CARD --> repeats per post
blog.config.json                    Generator config (source/template/output paths + site metadata)

blog/index.html                     GENERATED listing
blog/<slug>/index.html              GENERATED post page
blog/feed.xml                       GENERATED RSS feed
```

The `blog/` directory is generated output — **do not hand-edit it**. Edit the Markdown source or the templates, then regenerate.

**Post frontmatter:**

```yaml
title:         "Post title"        # required
date:          2026-06-23          # required; ISO date; drives ordering + RSS
slug:          optional            # derived from title if absent
tags:          [studio notes]      # optional
excerpt:       "One-line summary"  # optional; used for listing + meta description; auto-derived if absent
draft:         false               # true = the post is skipped by the generator
cover_image:   assets/blog/x.jpg   # optional; used for the social/og:image
canonical_url: optional            # optional; set only when syndicating the post elsewhere
```

**Publishing a post now:**

1. Add `content/blog/<YYYY-MM-DD-slug>.md` with frontmatter and a Markdown body. Put the hero at `assets/images/blog/<slug>/hero.png`.
2. Regenerate: `uv run python tools/blog/generator.py --config blog.config.json`. It renders every non-draft post and rewrites `blog/` deterministically.
3. Commit the Markdown, the image **and** the regenerated `blog/` files, then open a PR. Merging to `main` publishes to [dysonhope.com/blog/](https://dysonhope.com/blog/).

**Scheduling posts (the drip):** posts dated in the future stay on the publishing Mac, never in git, until their day comes.

- **Queue:** `~/DysonHope/blog-queue/` holds one directory per post, named `YYYY-MM-DD-<slug>`. Each directory mirrors repo paths: `content/blog/<file>.md` plus `assets/images/blog/<slug>/hero.*`. Anything else in it is rejected.
- **Daily run:** a launchd job runs `tools/blog/drip.py` at 07:00 against a dedicated clone, `~/DysonHope/site`, kept on `main`. Each run publishes the oldest due post (at most one), regenerates `blog/`, commits `feat(blog): publish "<title>"`, pushes `main`, and moves the directory to `blog-queue/published/`.
- **Failures:** on any failure the clone is reset to `origin/main` and the post stays queued for the next run.
- **Logs:** `~/Library/Logs/dysonhope/blog-drip.log` (one line per run) and `blog-drip.err.log`.
- **Install or update:** `launchd/install.sh`, run from a clone of `main`. Env overrides: `DRIP_SITE` (publishing clone), `DRIP_QUEUE` (queue dir), `UV` (path to uv).
- **Remove:** `launchd/uninstall.sh`.
- **Run once now:** `launchctl kickstart gui/$(id -u)/com.jasoncookdesign.dysonhope.blog-drip`.
- **Tests:** `uv run pytest`.

Blog asset and navigation links are root-relative (`/assets/...`, `/blog/`), so preview by serving the **repo root** and visiting `/blog/`:

```bash
python3 -m http.server 8000   # then open http://localhost:8000/blog/
```

### Contact and booking flow

All contact is handled via `mailto:` links — there is no form or backend.

- **Booking** requests → `booking@dysonhope.com`
- **Production / collaboration** requests → `studio@dysonhope.com`
- **General** contact (links hub) → `info@dysonhope.com`

---

## Analytics

Page analytics run through **Google Tag Manager** (container `GTM-5T87PLM6`), loaded on every page (including the generated blog pages) behind the cookie-consent gate. GTM is the only third-party script embedded in the site.

To support event mapping in the tag manager, interactive elements (CTAs, platform/store links, social links, release/mix items) carry declarative data attributes that describe the interaction:

- `data-track="true"` — marks an element for click tracking
- `data-entity`, `data-action`, `data-target` — the event taxonomy
- `data-platform`, `data-page-type` — context
- `data-release-title`, `data-mix-title`, `data-cta-type` — payload detail

These attributes are consumed by GTM; no first-party tracking script is checked into the repo.

---

## License

&copy; Dyson Hope. All rights reserved.  
Made with ♥ in Austin, Texas.
