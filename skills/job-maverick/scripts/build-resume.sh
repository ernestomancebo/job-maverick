#!/usr/bin/env bash
# Build a resume .docx and .pdf from a markdown source using reference-template.docx.
# The master is the comprehensive superset (no page limit); tailored versions must fit 2 pages.
# Usage: ./build-resume.sh <source.md> <output-basename>
# Example: ./build-resume.sh master-resume.md Master_Resume
set -euo pipefail

SRC="${1:-master-resume.md}"
OUT="${2:-Master_Resume}"
DIR="$(cd "$(dirname "$SRC")" && pwd)"
TEMPLATE="${RESUME_TEMPLATE:-$(pwd)/reference-template.docx}"
SOFFICE="${SOFFICE:-$(command -v soffice || echo /Applications/LibreOffice.app/Contents/MacOS/soffice)}"

pandoc "$SRC" --reference-doc="$TEMPLATE" -o "$DIR/$OUT.docx"

# Body text stays at the template's 11pt (FDU guide: no smaller than 11).

"$SOFFICE" --headless --convert-to pdf --outdir "$DIR" "$DIR/$OUT.docx" >/dev/null 2>&1
PAGES=$(python3 -c "import re;print(len(re.findall(rb'/Type\s*/Page[^s]',open('$DIR/$OUT.pdf','rb').read())))")
echo "built $DIR/$OUT.docx and .pdf ($PAGES pages)"
case "$OUT" in *Master*) ;; *) [ "$PAGES" -le 2 ] || echo "WARNING: tailored resume is more than 2 pages" >&2 ;; esac
