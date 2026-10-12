#!/bin/bash
# compile changed engine + card files of the fork worktree against pinned jars
cd /tmp/claude-0/mcards
rm -rf /tmp/claude-0/cc; mkdir -p /tmp/claude-0/cc
FILES=$( (git diff --name-only c6954ac5efe; git ls-files -o --exclude-standard) | grep '\.java$' | grep -v '^Mage.Tests' | sort -u)
javac -nowarn -encoding UTF-8 -implicit:none -sourcepath Mage/src/main/java:Mage.Sets/src -d /tmp/claude-0/cc -cp "$(cat /tmp/claude-0/cp.txt)" $FILES 2>&1 | grep -E "error:|\.java:[0-9]+:" | head -${1:-30}
