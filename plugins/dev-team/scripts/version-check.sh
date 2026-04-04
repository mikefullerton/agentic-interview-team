#!/bin/bash
# version-check.sh — Compare running version against installed SKILL.md
# Usage: version-check.sh <skill-dir> <running-version>
# Outputs: Warning to stderr if versions differ, nothing if they match

SKILL_DIR="$1"
RUNNING_VERSION="$2"

if [[ ! -f "$SKILL_DIR/SKILL.md" ]]; then
  exit 0
fi

INSTALLED_VERSION=$(
  awk '/^---$/{ if (++n==2) exit } /^version: / && n==1 { sub(/^version: /, ""); print }' "$SKILL_DIR/SKILL.md"
)

if [[ -n "$INSTALLED_VERSION" && "$INSTALLED_VERSION" != "$RUNNING_VERSION" ]]; then
  echo "Warning: This skill is running v${RUNNING_VERSION} but v${INSTALLED_VERSION} is installed. Restart the session to use the latest version."
fi
