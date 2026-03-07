#!/usr/bin/env sh

# Wrapper to execute kapture_dom_erode.py using uv
# Structural tag erosion and gron-grep for Kapture DOM snapshots

set -eu

if [ $# -eq 0 ]; then
	echo "Usage: $0 [gron-grep|extract-text|top-content] [options]"
	echo ""
	echo "Structural tag erosion and gron-grep for Kapture DOM snapshots."
	echo ""
	echo "INPUT FILE FORMAT (-f/--file):"
	echo "  The -f argument accepts one of two formats:"
	echo "  1. Full kapture_dom JSON response object (preferred)."
	echo "     This object includes fields like success/url/title and an html field."
	echo "  2. Raw HTML:  <body>...</body>"
	echo "  The tool auto-detects by checking if the file content starts with '{'."
	echo ""
	echo "Optional override:"
	echo "  Use -k/--content-key to specify which JSON key contains the DOM content."
	echo "  Default key is: html"
	echo ""
	uv run --with beautifulsoup4 --with lxml python "$(dirname "$0")/kapture_dom_erode.py" -h
	exit 1
fi

uv run --with beautifulsoup4 --with lxml python "$(dirname "$0")/kapture_dom_erode.py" "$@"
