# Blog drip: requirements

Publish approved blog posts on their dates. Until a post goes live, its text and image stay on the publishing Mac and are never pushed to GitHub.

| ID | Requirement | Acceptance |
|---|---|---|
| REQ-01 | The generator renders `content/blog/*.md` into `blog/` (post pages, index, RSS) with the existing templates. | Regenerating the current repo produces no diff in `blog/`. |
| REQ-02 | A staged post is a directory named `YYYY-MM-DD-<slug>` in a local queue dir. Its tree mirrors repo paths: `content/blog/…md` and `assets/images/blog/<slug>/hero.*`. | A staged dir whose name has no valid date, or that contains a path outside `content/blog/` or `assets/images/blog/<slug>/`, is rejected with `StagingError` and nothing is copied. |
| REQ-03 | A run publishes at most one post: the oldest staged dir dated today or earlier. | With two due posts, one run publishes the older one and leaves the newer one staged. With nothing due, the run changes nothing and exits 0. |
| REQ-04 | Publishing copies the staged tree into the repo, runs the generator, commits only the post's files plus `blog/` with the message `feat(blog): publish "<title>"`, and pushes `main`. | The commit touches only those paths, and the post page exists in `blog/<slug>/index.html`. |
| REQ-05 | A run refuses to start unless the repo is on `main` with a clean tree and fast-forwards from `origin/main`. | A dirty tree, another branch, or a non-fast-forward raises `RepoStateError`, and the queue is untouched. |
| REQ-06 | If generate, commit or push fails, the repo is reset to `origin/main` and the post stays staged. | After a forced push failure, `HEAD == origin/main`, the working tree is clean, and the staged dir still exists. The exit code is non-zero. |
| REQ-07 | After a successful push, the staged dir moves to `<queue>/published/`. | The dir is under `published/` and no longer in the queue root. |
| REQ-08 | Each run logs one line: published `<slug> <commit>`, `nothing due (next: <date>)`, or the error. | The log line appears on stdout or stderr. launchd captures both. |
| REQ-09 | If the due post is already live, because copying it changes nothing (say a run pushed but crashed before moving it), the run moves it to `published/` without committing. | Origin gets no new commit, and the dir moves to `published/`. |

**Non-goals:** random spacing (dates are fixed when staged), drafting or approval workflow, reel reminders, publishing from CI.

**Failure behavior:** fail closed. A run that can't publish cleanly leaves the post staged for the next run and exits non-zero. It never force-pushes.

**Data handling:** the queue dir lives outside the repo (default `~/DysonHope/blog-queue`). The drip reads only the one post it publishes.

**Security:** the push uses the user's existing git credentials (keychain). No tokens are stored by this tool.

**Scale:** about one post every few days, and one run per day.
