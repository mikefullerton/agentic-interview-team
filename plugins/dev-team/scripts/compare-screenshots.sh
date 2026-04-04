#!/bin/bash
# compare-screenshots.sh — Compare two sets of screenshots using ImageMagick
# Usage: compare-screenshots.sh <baseline-dir> <target-dir> <output-dir>
# Requires: ImageMagick (compare, identify commands)
# Outputs: Diff images in <output-dir>/diffs/, markdown report to stdout

set -euo pipefail

BASELINE_DIR="$1"
TARGET_DIR="$2"
OUTPUT_DIR="$3"

mkdir -p "$OUTPUT_DIR/diffs"

if ! command -v compare &> /dev/null; then
  echo "ImageMagick not installed. Install with: brew install imagemagick" >&2
  exit 1
fi

echo "# Screenshot Comparison"
echo ""
echo "| Screenshot | Baseline | Target | Similarity | Diff |"
echo "|------------|----------|--------|------------|------|"

TOTAL=0
MATCHED=0

for BASELINE_IMG in "$BASELINE_DIR"/*.png; do
  [[ -f "$BASELINE_IMG" ]] || continue
  FILENAME=$(basename "$BASELINE_IMG")
  TARGET_IMG="$TARGET_DIR/$FILENAME"
  DIFF_IMG="$OUTPUT_DIR/diffs/diff-$FILENAME"

  TOTAL=$((TOTAL + 1))

  if [[ ! -f "$TARGET_IMG" ]]; then
    echo "| $FILENAME | exists | **missing** | N/A | N/A |"
    continue
  fi

  DIFF_PIXELS=$(compare -metric AE "$BASELINE_IMG" "$TARGET_IMG" "$DIFF_IMG" 2>&1 || true)
  TOTAL_PIXELS=$(identify -format "%[fx:w*h]" "$BASELINE_IMG" 2>/dev/null || echo "1")

  if [[ "$TOTAL_PIXELS" -gt 0 && "$DIFF_PIXELS" =~ ^[0-9]+$ ]]; then
    SIMILARITY=$(python3 -c "print(f'{(1 - $DIFF_PIXELS / $TOTAL_PIXELS) * 100:.1f}%')" 2>/dev/null || echo "N/A")
  else
    SIMILARITY="N/A"
  fi

  if [[ "$DIFF_PIXELS" == "0" ]]; then
    MATCHED=$((MATCHED + 1))
    echo "| $FILENAME | exists | exists | 100.0% | identical |"
    rm -f "$DIFF_IMG"
  else
    echo "| $FILENAME | exists | exists | $SIMILARITY | [diff](diffs/diff-$FILENAME) |"
  fi
done

for TARGET_IMG in "$TARGET_DIR"/*.png; do
  [[ -f "$TARGET_IMG" ]] || continue
  FILENAME=$(basename "$TARGET_IMG")
  if [[ ! -f "$BASELINE_DIR/$FILENAME" ]]; then
    echo "| $FILENAME | **missing** | exists | N/A | new in target |"
  fi
done

echo ""
echo "**Summary:** $MATCHED/$TOTAL screenshots identical"
