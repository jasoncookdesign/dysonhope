#!/bin/sh
# Install the daily (07:00) blog-drip launchd job.
# Env overrides: DRIP_SITE (publishing clone, default ~/DysonHope/site; cloned if missing),
# DRIP_QUEUE (staged posts, default ~/DysonHope/blog-queue), UV (default: uv on PATH).
# Safe to re-run: it replaces the loaded job.
set -eu
REPO=$(cd "$(dirname "$0")/.." && pwd)
SITE=${DRIP_SITE:-$HOME/DysonHope/site}
QUEUE=${DRIP_QUEUE:-$HOME/DysonHope/blog-queue}
UV=${UV:-$(command -v uv)}
LOG_DIR=$HOME/Library/Logs/dysonhope
AGENTS=$HOME/Library/LaunchAgents
LABEL=com.jasoncookdesign.dysonhope.blog-drip
mkdir -p "$LOG_DIR" "$AGENTS" "$QUEUE"

if [ ! -d "$SITE/.git" ]; then
  git clone --quiet "$(git -C "$REPO" remote get-url origin)" "$SITE"
  git -C "$SITE" config user.name "$(git -C "$REPO" config user.name)"
  git -C "$SITE" config user.email "$(git -C "$REPO" config user.email)"
fi
(cd "$SITE" && "$UV" sync --quiet --no-dev)

esc() { printf '%s' "$1" | sed -e 's/[&|\\]/\\&/g'; }
dest=$AGENTS/$LABEL.plist
sed -e "s|@@UV@@|$(esc "$UV")|g" \
    -e "s|@@SITE@@|$(esc "$SITE")|g" \
    -e "s|@@QUEUE@@|$(esc "$QUEUE")|g" \
    -e "s|@@LOG_DIR@@|$(esc "$LOG_DIR")|g" \
    "$REPO/launchd/$LABEL.plist.template" > "$dest"
plutil -lint "$dest" >/dev/null
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
# bootout is asynchronous; bootstrap can fail with EIO until the old job is gone.
tries=0
until launchctl bootstrap "gui/$(id -u)" "$dest"; do
  tries=$((tries + 1))
  if [ "$tries" -ge 5 ]; then echo "failed to bootstrap $LABEL" >&2; exit 1; fi
  sleep 1
done
echo "installed $LABEL -> $dest"
echo "site: $SITE  queue: $QUEUE  logs: $LOG_DIR"
