#!/usr/bin/env sh

# Wrapper to execute kapture_dom_erode.py using uv
# Structural tag erosion and gron-grep for Kapture DOM snapshots

set -eu

if [ $# -eq 0 ]; then
	echo "Usage: $0 [gron-grep|extract-text] [options]"
	echo ""
	echo "This tool performs structural tag erosion and matching."
	echo "It uses 'uv' to run 'kapture_dom_erode.py'."
	echo ""
	uv run --with beautifulsoup4 --with lxml python "$(dirname "$0")/kapture_dom_erode.py" -h
	exit 1
fi

uv run --with beautifulsoup4 --with lxml python "$(dirname "$0")/kapture_dom_erode.py" "$@"
