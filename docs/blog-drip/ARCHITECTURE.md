# Blog drip: architecture

```
launchd (daily) ──> tools/blog/drip.py ──copy──> repo working tree
                         │                      │
                    local queue dir       tools/blog/generator.py ──> blog/
                    (never in git)              │
                                          git commit + push main ──> GitHub Pages
```

## Modules

**`tools/blog/generator.py`** (REQ-01)
- Owns turning Markdown with YAML frontmatter into post pages, `blog/index.html` and `blog/feed.xml`.
- Output is deterministic, with no timestamps, so re-runs produce no diff.
- Must not touch git or anything outside `out`.
- Build versus buy: it uses `markdown` (python-markdown, with the `extra` and `sane_lists` extensions) and `pyyaml`, both pinned in `pyproject.toml`. There's no hand-written Markdown parser.

**`tools/blog/drip.py`** (REQ-02 to REQ-08)
- Owns selecting the due post, validating the staged tree, copying it in, calling `generator.build`, and the git lifecycle with rollback.
- Must not edit staged content, publish more than one post per run, or force-push.
- Domain errors: `StagingError` (bad staged dir) and `RepoStateError` (the repo isn't safe to publish from). Both are subclasses of `DripError`.
- Seam: `run(repo: Path, queue: Path, today: date, push: bool = True) -> Result`. `git` is called through `subprocess` against `repo`, and tests use real temporary git repos with a bare `origin`.

**`launchd/`** owns the daily schedule (07:00 local) and installation. It holds no logic.

## Invariants

| Invariant | Owning test |
|---|---|
| Unpublished staged content is never committed or pushed. | `test_drip.py::test_only_due_post_reaches_origin` |
| A failed run leaves `origin` unchanged and the post staged. | `test_drip.py::test_push_failure_rolls_back_and_keeps_staged` |
| Regenerating committed content changes nothing in `blog/`. | `test_generator.py::test_golden_repo_regenerates_without_diff` |

## Trust boundary

The staged files are authored by Jason and come from the local queue. Post bodies may contain raw HTML (the hero `<figure>`), which is passed through as it was before.
