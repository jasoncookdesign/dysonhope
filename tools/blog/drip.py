#!/usr/bin/env python3
"""
Local blog drip: publish the oldest due staged post, one per run.

Staged posts live outside the repo (never pushed before their date), one directory per
post named YYYY-MM-DD-<slug>. Each directory mirrors repo paths:

    2026-10-11-the-hardest-part-of-djing/
        content/blog/2026-10-11-the-hardest-part-of-djing.md
        assets/images/blog/the-hardest-part-of-djing/hero.png

A run copies the due post into the repo, regenerates blog/, commits, and pushes main.
On any failure it resets the repo to origin/main and leaves the post staged. Published
directories move to <queue>/published/. See docs/blog-drip/.

Usage (from the repo root):
    uv run python tools/blog/drip.py --repo . --queue ~/DysonHope/blog-queue
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import generator

_STAGED_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9][a-z0-9-]*)$")
PUBLISHED_DIR = "published"
LOCK_FILE = ".drip.lock"


class DripError(Exception):
    """Base class for drip failures."""


class StagingError(DripError):
    """A staged post directory is malformed."""


class RepoStateError(DripError):
    """The repo is not in a state that is safe to publish from."""


@dataclass
class Result:
    status: str  # "published" | "nothing-due" | "already-live"
    slug: str | None = None
    commit: str | None = None
    next_date: dt.date | None = None


@dataclass
class Staged:
    path: Path
    date: dt.date
    slug: str


# ── queue ───────────────────────────────────────────────────────────────────

def _parse_staged(path: Path) -> Staged:
    m = _STAGED_RE.match(path.name)
    if not m:
        raise StagingError(f"{path.name}: staged dir must be named YYYY-MM-DD-<slug>")
    try:
        date = dt.date.fromisoformat(m.group(1))
    except ValueError as exc:
        raise StagingError(f"{path.name}: invalid date") from exc
    return Staged(path=path, date=date, slug=m.group(2))


def _staged(queue: Path) -> list[Staged]:
    items = [_parse_staged(p) for p in queue.iterdir()
             if p.is_dir() and p.name != PUBLISHED_DIR and not p.name.startswith(".")]
    return sorted(items, key=lambda s: (s.date, s.slug))


def _files(item: Staged) -> list[Path]:
    """Validated repo-relative file paths of a staged post."""
    entries = [p for p in item.path.rglob("*") if p.name != ".DS_Store"]
    for p in entries:
        if p.is_symlink():
            raise StagingError(f"{item.path.name}: {p.relative_to(item.path)} is a symlink")
    files = sorted(p.relative_to(item.path) for p in entries if p.is_file())
    hero_prefix = ("assets", "images", "blog", item.slug)
    posts = []
    for rel in files:
        parts = rel.parts
        if len(parts) == 3 and parts[:2] == ("content", "blog") and rel.suffix == ".md":
            posts.append(rel)
        elif len(parts) == 5 and parts[:4] == hero_prefix and rel.stem == "hero":
            continue
        else:
            raise StagingError(f"{item.path.name}: {rel} is not content/blog/*.md "
                               f"or assets/images/blog/{item.slug}/hero.*")
    if len(posts) != 1:
        raise StagingError(f"{item.path.name}: needs exactly one content/blog/*.md, found {len(posts)}")
    return files


# ── git ─────────────────────────────────────────────────────────────────────

def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        raise DripError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def _prepare_repo(repo: Path) -> None:
    branch = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    if branch != "main":
        raise RepoStateError(f"repo is on {branch!r}, not main")
    if _git(repo, "status", "--porcelain", "--untracked-files=all"):
        raise RepoStateError("repo has uncommitted changes")
    _git(repo, "fetch", "--quiet", "origin", "main")
    try:
        _git(repo, "merge", "--ff-only", "--quiet", "origin/main")
    except DripError as exc:
        raise RepoStateError(f"main does not fast-forward from origin/main: {exc}") from exc
    if _git(repo, "rev-parse", "HEAD") != _git(repo, "rev-parse", "origin/main"):
        raise RepoStateError("main has commits that are not on origin/main")


def _rollback(repo: Path) -> None:
    _git(repo, "reset", "--hard", "--quiet", "origin/main")
    _git(repo, "clean", "-fdq")


# ── publish ─────────────────────────────────────────────────────────────────

def _build(repo: Path) -> None:
    cfg = json.loads((repo / "blog.config.json").read_text(encoding="utf-8"))
    ctx = {k: cfg.get(k, "") for k in ("site_title", "blog_url", "author")}
    generator.build(repo / cfg["content"], repo / cfg["templates"], repo / cfg["out"], ctx)


def _archive(item: Staged, queue: Path) -> None:
    dest = queue / PUBLISHED_DIR
    dest.mkdir(exist_ok=True)
    shutil.move(str(item.path), str(dest / item.path.name))


@contextlib.contextmanager
def _lock(queue: Path):
    with open(queue / LOCK_FILE, "w") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise DripError("another run holds the queue lock") from exc
        yield


def run(repo: Path, queue: Path, today: dt.date, push: bool = True) -> Result:
    repo, queue = Path(repo), Path(queue)
    with _lock(queue):
        return _run_locked(repo, queue, today, push)


def _run_locked(repo: Path, queue: Path, today: dt.date, push: bool) -> Result:
    items = _staged(queue)
    due = [s for s in items if s.date <= today]
    if not due:
        return Result("nothing-due", next_date=items[0].date if items else None)
    item = due[0]
    files = _files(item)
    _prepare_repo(repo)

    try:
        for rel in files:
            target = repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item.path / rel, target)
        post_rel = next(r for r in files if r.parts[0] == "content")
        title = generator.parse_post(
            (repo / post_rel).read_text(encoding="utf-8"), source_name=post_rel.name).title
        _build(repo)
        if not _git(repo, "status", "--porcelain", "--untracked-files=all"):
            _archive(item, queue)
            return Result("already-live", slug=item.slug, commit=_git(repo, "rev-parse", "HEAD"))
        _git(repo, "add", "--", *[str(r) for r in files], "blog")
        _git(repo, "commit", "--quiet", "-m", f'feat(blog): publish "{title}"')
        if push:
            _git(repo, "push", "--quiet", "origin", "main")
    except Exception as exc:
        _rollback(repo)
        if isinstance(exc, DripError):
            raise
        raise DripError(f"{item.path.name}: {type(exc).__name__}: {exc}") from exc

    commit = _git(repo, "rev-parse", "HEAD")
    _archive(item, queue)
    return Result("published", slug=item.slug, commit=commit)


# ── CLI ─────────────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Publish the oldest due staged blog post")
    ap.add_argument("--repo", required=True, help="dysonhope repo clone (on main, clean)")
    ap.add_argument("--queue", required=True, help="local staged-post dir (outside the repo)")
    ap.add_argument("--today", type=dt.date.fromisoformat, default=None,
                    help="override today's date, YYYY-MM-DD (past dates only)")
    args = ap.parse_args(argv)
    real_today = dt.date.today()
    today = args.today or real_today
    if today > real_today:
        print(f"DripError: --today {today} is in the future; refusing to publish early",
              file=sys.stderr)
        return 1
    try:
        result = run(Path(args.repo).expanduser(), Path(args.queue).expanduser(), today)
    except DripError as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    if result.status == "nothing-due":
        nxt = result.next_date.isoformat() if result.next_date else "queue empty"
        print(f"nothing due (next: {nxt})")
    else:
        print(f"{result.status} {result.slug} {result.commit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
