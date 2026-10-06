#!/bin/sh
# Remove the blog-drip launchd job. Leaves the publishing clone and the queue in place.
set -eu
LABEL=com.jasoncookdesign.dysonhope.blog-drip
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/$LABEL.plist"
echo "removed $LABEL"
