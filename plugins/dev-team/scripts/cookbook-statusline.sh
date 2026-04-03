#!/bin/bash
# Cookbook pipeline progress display
#
# PURPOSE: Shows progress through the /cookbook-start + /cookbook-next
# pipeline by reading .cookbook/pipeline.json (written by /cookbook-start,
# updated by /cookbook-next on each step).
#
# HOW IT GETS CALLED: This is NOT a general-purpose status line script.
# It is invoked by Claude Code's statusLine mechanism (settings.json) on
# each turn, but only because that is the delivery mechanism available.
# The content it displays is purely about cookbook pipeline state.
#
# INSTALLATION: /install-cookbook copies this to .cookbook/statusline.sh
# in consuming projects and writes to ~/.claude/settings.json:
#   { "statusLine": { "type": "command", "command": ".cookbook/statusline.sh" } }
#
# OUTPUT: "Planning: Step 2/5 — security" or "Pipeline complete" or nothing.

input=$(cat)

# Read pipeline progress if active
if [ -f .cookbook/pipeline.json ]; then
  step=$(jq -r '.current_step // empty' .cookbook/pipeline.json 2>/dev/null)
  total=$(jq -r '.total_steps // empty' .cookbook/pipeline.json 2>/dev/null)
  phase=$(jq -r '.phase // empty' .cookbook/pipeline.json 2>/dev/null)

  if [ -n "$step" ] && [ -n "$total" ]; then
    steps_len=$(jq '.steps | length' .cookbook/pipeline.json 2>/dev/null)
    if [ "$step" -le "${steps_len:-0}" ]; then
      concern=$(jq -r '.results[-1].concern // "starting"' .cookbook/pipeline.json 2>/dev/null)
      Phase=$(echo "$phase" | awk '{print toupper(substr($0,1,1)) substr($0,2)}')
      echo "$Phase: Step $step/$total — $concern"
    else
      echo "Pipeline complete"
    fi
  fi
fi
