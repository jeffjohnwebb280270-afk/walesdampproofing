#!/usr/bin/env bash
# Build the landlord pack.
#
# PDFs are rendered with headless Chromium so the print CSS is honoured.
# The three templates are emitted twice — .docx so a landlord can add their own
# logo and type into them, and PDF so front-line staff can fill one in on paper.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
out="$here/../build"
zip_name="Wales Damp Proofing — Landlord Pack.zip"

rm -rf "$out"; mkdir -p "$out"
python3 "$here/make_templates.py"          # writes .docx and .html to build/

for f in "$here"/0[1-3]-*.html "$out"/0[4-6]-*.html; do
  name="$(basename "${f%.html}")"
  /opt/pw-browsers/chromium --headless --disable-gpu --no-sandbox \
    --no-pdf-header-footer --print-to-pdf-no-header \
    --print-to-pdf="$out/$name.pdf" "file://$f" 2>/dev/null
done
echo "  6 pdfs rendered"

cp "$here/README.txt" "$out/README.txt"
cd "$out"
rm -f "../$zip_name"
zip -q -X "../$zip_name" README.txt ./*.pdf ./*.docx
cd ..
echo "  $(unzip -l "$zip_name" | tail -1 | awk '{print $2}') files, $(du -h "$zip_name" | cut -f1)"
