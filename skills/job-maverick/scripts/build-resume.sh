#!/usr/bin/env bash
# Build a resume .docx and .pdf from a Markdown source.
# Usage: build-resume.sh <source.md> <OutputBasename>
# Env:   RESUME_TEMPLATE  optional reference .docx for styling (pandoc --reference-doc)
#        RESUME_MAX_PAGES page limit for tailored resumes (default 2); outputs whose name contains
#                         "master" or "Master" are exempt (the master is a source, not a submission)
#        SOFFICE          path to LibreOffice's soffice if not on PATH
# Needs: pandoc; LibreOffice for the PDF; poppler (pdftotext) for the page count. Without LibreOffice
#        the .docx is still produced.
set -euo pipefail

SRC="${1:?usage: build-resume.sh <source.md> <OutputBasename>}"
OUT="${2:?usage: build-resume.sh <source.md> <OutputBasename>}"
DIR="$(cd "$(dirname "$SRC")" && pwd)"
MAX_PAGES="${RESUME_MAX_PAGES:-2}"
SOFFICE="${SOFFICE:-$(command -v soffice || ls /Applications/LibreOffice.app/Contents/MacOS/soffice 2>/dev/null || true)}"

command -v pandoc >/dev/null || { echo "pandoc is required" >&2; exit 1; }

if [ -n "${RESUME_TEMPLATE:-}" ] && [ -f "$RESUME_TEMPLATE" ]; then
  pandoc "$SRC" --reference-doc="$RESUME_TEMPLATE" -o "$DIR/$OUT.docx"
else
  pandoc "$SRC" -o "$DIR/$OUT.docx"
fi
echo "built $DIR/$OUT.docx"

if [ -z "$SOFFICE" ]; then
  echo "LibreOffice not found; skipping PDF (set SOFFICE or install LibreOffice)" >&2
  exit 0
fi
"$SOFFICE" --headless --convert-to pdf --outdir "$DIR" "$DIR/$OUT.docx" >/dev/null 2>&1
PAGES=$(python3 -c "import re,sys;print(len(re.findall(rb'/Type\s*/Page[^s]',open(sys.argv[1],'rb').read())))" "$DIR/$OUT.pdf")
echo "built $DIR/$OUT.pdf ($PAGES pages)"
case "$OUT" in
  *aster*) ;;
  *) [ "$PAGES" -le "$MAX_PAGES" ] || echo "WARNING: tailored resume is $PAGES pages; the limit is $MAX_PAGES" >&2 ;;
esac
