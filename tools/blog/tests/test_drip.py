"""Drip contract tests. Each test builds a real git repo with a bare origin."""
import datetime as dt
import json
import pathlib
import subprocess

import pytest

import drip
import generator

TODAY = dt.date(2026, 10, 7)

POST_TPL = "<html><title>{{ title }}</title><body>{{ body }}</body></html>"
INDEX_TPL = ("<ul><!-- BEGIN POST_CARD --><li><a href=\"{{ url }}\">{{ title }}</a></li>"
             "<!-- END POST_CARD --></ul>")


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                          text=True).stdout.strip()


def post_md(title, date, slug, body="A paragraph of body text."):
    return f'---\ntitle: "{title}"\ndate: {date}\nslug: {slug}\ndraft: false\n---\n\n{body}\n'


@pytest.fixture
def site(tmp_path):
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    repo = tmp_path / "repo"
    git(tmp_path, "clone", "-q", str(origin), str(repo))
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "checkout", "-q", "-b", "main")
    (repo / "blog.config.json").write_text(json.dumps({
        "content": "content/blog", "templates": "templates/blog", "out": "blog",
        "site_title": "Site", "blog_url": "https://example.com/blog", "author": "A"}))
    (repo / "templates/blog").mkdir(parents=True)
    (repo / "templates/blog/post.html").write_text(POST_TPL)
    (repo / "templates/blog/index.html").write_text(INDEX_TPL)
    (repo / "content/blog").mkdir(parents=True)
    (repo / "content/blog/2026-01-01-old.md").write_text(post_md("Old Post", "2026-01-01", "old"))
    generator.build(repo / "content/blog", repo / "templates/blog", repo / "blog",
                    {"site_title": "Site", "blog_url": "https://example.com/blog", "author": "A"})
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    git(repo, "push", "-q", "-u", "origin", "main")
    queue = tmp_path / "queue"
    queue.mkdir()
    return {"repo": repo, "origin": origin, "queue": queue, "tmp": tmp_path}


def stage(queue, date, slug, title=None, md=None, extra=None):
    d = queue / f"{date}-{slug}"
    (d / "content/blog").mkdir(parents=True)
    text = md if md is not None else post_md(title or slug.title(), date, slug,
                                             body=f"Body of {slug} marker-{slug}.")
    (d / f"content/blog/{date}-{slug}.md").write_text(text)
    hero = d / f"assets/images/blog/{slug}/hero.png"
    hero.parent.mkdir(parents=True)
    hero.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + slug.encode())
    for rel, content in (extra or {}).items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return d


def origin_head(site):
    return git(site["origin"], "rev-parse", "main")


def origin_file(site, path):
    r = subprocess.run(["git", "show", f"main:{path}"], cwd=site["origin"], capture_output=True)
    return r.stdout.decode("utf-8", errors="replace") if r.returncode == 0 else None


# ── REQ-03: selection ────────────────────────────────────────────────────────

def test_nothing_due_changes_nothing(site):
    staged = stage(site["queue"], "2026-10-08", "later")
    before = origin_head(site)
    result = drip.run(site["repo"], site["queue"], TODAY)
    assert result.status == "nothing-due"
    assert result.next_date == dt.date(2026, 10, 8)
    assert origin_head(site) == before
    assert staged.exists()


def test_empty_queue_is_nothing_due(site):
    result = drip.run(site["repo"], site["queue"], TODAY)
    assert result.status == "nothing-due"
    assert result.next_date is None


def test_only_due_post_reaches_origin(site):
    """Invariant: unpublished staged content is never committed or pushed."""
    a = stage(site["queue"], "2026-10-05", "alpha", "Alpha Post")
    b = stage(site["queue"], "2026-10-07", "bravo", "Bravo Post")
    c = stage(site["queue"], "2026-10-09", "charlie", "Charlie Post")
    result = drip.run(site["repo"], site["queue"], TODAY)

    assert result.status == "published"
    assert result.slug == "alpha"
    assert result.commit == origin_head(site)
    page = origin_file(site, "blog/alpha/index.html")
    assert page is not None and "Alpha Post" in page and "marker-alpha" in page
    assert origin_file(site, "assets/images/blog/alpha/hero.png") is not None
    assert "Alpha Post" in origin_file(site, "blog/index.html")
    tree = git(site["origin"], "ls-tree", "-r", "--name-only", "main")
    assert "bravo" not in tree and "charlie" not in tree
    log = git(site["origin"], "log", "-p", "main")
    assert "marker-bravo" not in log and "marker-charlie" not in log
    assert not a.exists() and (site["queue"] / "published" / a.name).is_dir()
    assert b.exists() and c.exists()
    assert git(site["repo"], "status", "--porcelain", "--untracked-files=all") == ""


def test_second_run_publishes_next_due(site):
    stage(site["queue"], "2026-10-05", "alpha")
    stage(site["queue"], "2026-10-07", "bravo")
    drip.run(site["repo"], site["queue"], TODAY)
    result = drip.run(site["repo"], site["queue"], TODAY)
    assert result.slug == "bravo"
    assert origin_file(site, "blog/bravo/index.html") is not None
    assert origin_file(site, "blog/alpha/index.html") is not None


# ── REQ-04: commit shape ─────────────────────────────────────────────────────

def test_commit_touches_only_post_paths_and_blog(site):
    stage(site["queue"], "2026-10-07", "alpha", "Alpha Post")
    before = origin_head(site)
    result = drip.run(site["repo"], site["queue"], TODAY)
    changed = git(site["origin"], "diff", "--name-only", before, "main").splitlines()
    assert "content/blog/2026-10-07-alpha.md" in changed
    assert "assets/images/blog/alpha/hero.png" in changed
    assert "blog/alpha/index.html" in changed
    for path in changed:
        assert path.startswith(("content/blog/", "assets/images/blog/alpha/", "blog/")), path
    assert git(site["origin"], "log", "-1", "--format=%s", "main") == 'feat(blog): publish "Alpha Post"'
    assert git(site["origin"], "rev-list", "--count", f"{before}..main") == "1"
    assert result.commit == origin_head(site)


def test_fast_forwards_from_origin_before_publishing(site):
    other = site["tmp"] / "other"
    git(site["tmp"], "clone", "-q", str(site["origin"]), str(other))
    git(other, "config", "user.name", "T")
    git(other, "config", "user.email", "t@example.com")
    (other / "README.md").write_text("upstream change")
    git(other, "add", "-A")
    git(other, "commit", "-q", "-m", "upstream")
    git(other, "push", "-q", "origin", "main")
    upstream = origin_head(site)

    stage(site["queue"], "2026-10-07", "alpha")
    drip.run(site["repo"], site["queue"], TODAY)
    assert git(site["origin"], "rev-parse", "main~1") == upstream
    assert origin_file(site, "README.md") == "upstream change"


# ── REQ-02: staging validation ───────────────────────────────────────────────

@pytest.mark.parametrize("name", ["alpha", "2026-13-01-alpha", "20261007-alpha", "2026-10-07-"])
def test_bad_staged_dir_name_rejected(site, name):
    d = site["queue"] / name
    (d / "content/blog").mkdir(parents=True)
    (d / "content/blog/x.md").write_text(post_md("X", "2026-10-07", "x"))
    before = origin_head(site)
    with pytest.raises(drip.StagingError):
        drip.run(site["repo"], site["queue"], TODAY)
    assert origin_head(site) == before
    assert git(site["repo"], "status", "--porcelain") == ""


@pytest.mark.parametrize("rel", ["index.html", "content/other.md",
                                 "assets/images/blog/someone-else/hero.png",
                                 "content/blog/sub/x.md", "blog/alpha/index.html",
                                 "assets/images/blog/alpha/sub/hero.png",
                                 "assets/images/blog/alpha/notes.txt"])
def test_staged_path_outside_allowed_tree_rejected(site, rel):
    d = stage(site["queue"], "2026-10-07", "alpha", extra={rel: "x"})
    before = origin_head(site)
    with pytest.raises(drip.StagingError):
        drip.run(site["repo"], site["queue"], TODAY)
    assert origin_head(site) == before
    assert git(site["repo"], "status", "--porcelain") == ""
    assert d.exists()


def test_staged_dir_needs_exactly_one_post_file(site):
    d = stage(site["queue"], "2026-10-07", "alpha",
              extra={"content/blog/2026-10-07-second.md": post_md("S", "2026-10-07", "s")})
    with pytest.raises(drip.StagingError):
        drip.run(site["repo"], site["queue"], TODAY)
    assert d.exists()


# ── REQ-05: repo preconditions ───────────────────────────────────────────────

def test_dirty_tree_refused(site):
    d = stage(site["queue"], "2026-10-07", "alpha")
    (site["repo"] / "README.md").write_text("uncommitted")
    before = origin_head(site)
    with pytest.raises(drip.RepoStateError):
        drip.run(site["repo"], site["queue"], TODAY)
    assert origin_head(site) == before and d.exists()
    assert (site["repo"] / "README.md").read_text() == "uncommitted"


def test_other_branch_refused(site):
    d = stage(site["queue"], "2026-10-07", "alpha")
    git(site["repo"], "checkout", "-q", "-b", "feature")
    with pytest.raises(drip.RepoStateError):
        drip.run(site["repo"], site["queue"], TODAY)
    assert d.exists()
    assert git(site["repo"], "rev-parse", "--abbrev-ref", "HEAD") == "feature"


def test_local_commits_not_on_origin_refused(site):
    d = stage(site["queue"], "2026-10-07", "alpha")
    (site["repo"] / "README.md").write_text("local only")
    git(site["repo"], "add", "-A")
    git(site["repo"], "commit", "-q", "-m", "local")
    before = origin_head(site)
    with pytest.raises(drip.RepoStateError):
        drip.run(site["repo"], site["queue"], TODAY)
    assert origin_head(site) == before and d.exists()


def test_drip_errors_share_a_base():
    assert issubclass(drip.StagingError, drip.DripError)
    assert issubclass(drip.RepoStateError, drip.DripError)
    assert not issubclass(drip.StagingError, drip.RepoStateError)


# ── REQ-06: rollback ─────────────────────────────────────────────────────────

def test_push_failure_rolls_back_and_keeps_staged(site):
    """Invariant: a failed run leaves origin unchanged and the post staged."""
    hook = site["origin"] / "hooks" / "pre-receive"
    hook.write_text("#!/bin/sh\necho rejected >&2\nexit 1\n")
    hook.chmod(0o755)
    d = stage(site["queue"], "2026-10-07", "alpha")
    before = origin_head(site)
    with pytest.raises(drip.DripError):
        drip.run(site["repo"], site["queue"], TODAY)
    assert origin_head(site) == before
    assert git(site["repo"], "rev-parse", "HEAD") == before
    assert git(site["repo"], "status", "--porcelain", "--untracked-files=all") == ""
    assert d.exists() and not (site["queue"] / "published" / d.name).exists()


def test_generator_failure_rolls_back_and_keeps_staged(site):
    d = stage(site["queue"], "2026-10-07", "alpha", md="---\ndate: 2026-10-07\n---\nno title\n")
    before = origin_head(site)
    with pytest.raises(drip.DripError):
        drip.run(site["repo"], site["queue"], TODAY)
    assert origin_head(site) == before
    assert git(site["repo"], "status", "--porcelain", "--untracked-files=all") == ""
    assert d.exists()


# ── REQ-09: already live ─────────────────────────────────────────────────────

def test_already_live_post_is_archived_without_commit(site):
    d = stage(site["queue"], "2026-10-07", "alpha")
    drip.run(site["repo"], site["queue"], TODAY)
    # Simulate a crash after push: the staged dir is back in the queue.
    (site["queue"] / "published" / d.name).rename(d)
    before = origin_head(site)
    result = drip.run(site["repo"], site["queue"], TODAY)
    assert result.status == "already-live"
    assert origin_head(site) == before
    assert not d.exists() and (site["queue"] / "published" / d.name).is_dir()


# ── REQ-08: CLI ──────────────────────────────────────────────────────────────

def test_cli_publishes_and_reports(site, capsys):
    stage(site["queue"], "2026-01-05", "alpha")
    code = drip.main(["--repo", str(site["repo"]), "--queue", str(site["queue"]),
                      "--today", "2026-01-05"])
    out = capsys.readouterr().out
    assert code == 0
    assert out.strip() == f"published alpha {origin_head(site)}"


@pytest.mark.parametrize("later", ["2026-02-11", "2026-03-25"])
def test_cli_nothing_due(site, capsys, later):
    stage(site["queue"], "2026-04-01", "much-later")
    stage(site["queue"], later, "later")
    code = drip.main(["--repo", str(site["repo"]), "--queue", str(site["queue"]),
                      "--today", "2026-01-05"])
    assert code == 0
    assert capsys.readouterr().out.strip() == f"nothing due (next: {later})"


def test_cli_error_exits_nonzero(site, capsys):
    stage(site["queue"], "2026-01-05", "alpha")
    (site["repo"] / "README.md").write_text("dirty")
    code = drip.main(["--repo", str(site["repo"]), "--queue", str(site["queue"]),
                      "--today", "2026-01-05"])
    captured = capsys.readouterr()
    assert code == 1
    assert "RepoStateError" in captured.err


def test_cli_refuses_future_today(site, capsys):
    """--today must never let a post go live before its real date."""
    tomorrow = dt.date.today() + dt.timedelta(days=1)
    d = stage(site["queue"], tomorrow.isoformat(), "alpha")
    before = origin_head(site)
    code = drip.main(["--repo", str(site["repo"]), "--queue", str(site["queue"]),
                      "--today", tomorrow.isoformat()])
    assert code != 0
    assert "future" in capsys.readouterr().err
    assert origin_head(site) == before and d.exists()


def test_staged_symlink_rejected(site, tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("not for publishing")
    d = stage(site["queue"], "2026-10-07", "alpha")
    (d / "assets/images/blog/alpha/hero.png").unlink()
    (d / "assets/images/blog/alpha/hero.png").symlink_to(secret)
    before = origin_head(site)
    with pytest.raises(drip.StagingError):
        drip.run(site["repo"], site["queue"], TODAY)
    assert origin_head(site) == before and d.exists()


def test_concurrent_run_refused(site):
    import fcntl
    d = stage(site["queue"], "2026-10-07", "alpha")
    with open(site["queue"] / drip.LOCK_FILE, "w") as held:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = origin_head(site)
        with pytest.raises(drip.DripError, match="another run"):
            drip.run(site["repo"], site["queue"], TODAY)
        assert origin_head(site) == before and d.exists()
