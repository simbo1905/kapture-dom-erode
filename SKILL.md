---
name: kapture-dom-erode
description: Search and extract readable text from multi-megabyte Kapture MCP DOM snapshots by eroding away HTML tag soup. Use when you have a saved DOM from kapture_dom and need to find or read visible on-screen content.
version: 1.0.0
tags: [kapture, kapture-mcp, kapture-dom, dom-parsing, opencode-skill, agent-skills]
---

# kapture-dom-erode

**A companion skill for the [Kapture MCP](https://github.com/anthropics/kapture) browser plugin.**

Modern web pages produce enormous DOM snapshots -- often 1-5 MB of deeply nested HTML. When an AI agent saves a page with `kapture_dom`, the result is millions of characters of markup where the actual on-screen text is buried inside layers of `<div>`, `<span>`, and framework-generated wrappers. This skill cuts through that noise.

## What it does

**kapture-dom-erode** takes a saved Kapture DOM snapshot and helps you:

1. **Search** -- find any visible text inside the multi-megabyte HTML and report exactly where it lives in the page structure.
2. **Erode** -- strip away all the surrounding markup to reveal just the human-readable text from a region of the page, in the order a user would see it on screen.

Think of it like `grep` for what's actually visible on a web page, not what's buried in the source code.

## Why you need this

The Kapture MCP plugin captures the full DOM of a browser tab. That's great for fidelity, but the raw HTML is unreadable -- a single sidebar might be wrapped in 20 levels of nested divs. Screenshots show you what's on screen but aren't machine-parseable. This skill bridges the gap: it lets an agent find and read specific on-screen content from the raw DOM, without screenshots and without drowning in markup.

**Typical use cases:**
- Extract a list of names, statuses, or labels from a web app
- Find a specific message, heading, or button text in a complex SPA
- Read structured content (tables, cards, menus) from the DOM as clean text
- Navigate multi-megabyte page captures that are too large to read directly

## Saving the DOM to a file

**This is the critical first step.** The `kapture_dom` MCP tool returns a JSON response object with many keys, including `"html"`.

**Where to save:** Write the DOM to a local scratch space in your current working directory (e.g., `.tmp/`, `scratch/`, or similar). If your sandbox does not permit local writes, use `/tmp` as a fallback.

**File format:** Save one of these two formats:

1. **Full `kapture_dom` response object (preferred):** write the complete JSON returned by `kapture_dom` to a file as-is. This includes metadata fields like `success`, `url`, `title`, and `html`.
2. **Raw HTML:** the literal HTML string (e.g. `<body>...</body>`) -- no JSON wrapper.

The parser defaults to reading `"html"` from JSON.
Use `-k / --content-key` if your JSON uses a different field name.

```bash
# Save to local scratch space (preferred)
./skills/kapture-dom-erode/tools.sh top-content -f .tmp/page.json
./skills/kapture-dom-erode/tools.sh top-content -f .tmp/page.json -k html

# Or fallback to /tmp if local writes are blocked
./skills/kapture-dom-erode/tools.sh top-content -f /tmp/page.json
```

**Global behavior across commands:**

- `-k, --content-key` -- optional JSON key for DOM extraction. Default is `html`.

## Commands

### `gron-grep` -- find text in the DOM

Search for any text and get back its structural path (like a GPS coordinate for where it sits in the page).

```bash
./skills/kapture-dom-erode/tools.sh gron-grep -f page.json -q "search text" [-i]
```

**Options:**
- `-f, --file` -- saved DOM file (JSON with `"html"` key, or raw HTML -- see "Saving the DOM" above)
- `-k, --content-key` -- JSON key for DOM content when using JSON input (default: `html`)
- `-q, --query` -- the text to search for
- `-i, --ignore-case` -- case-insensitive search

**Example:** find the word "Online" in a messaging app DOM:
```bash
./skills/kapture-dom-erode/tools.sh gron-grep -f .tmp/page.html -q "online" -i
```

Output:
```
html[0].body[0].div[6].div[0]...div[0].span[0] = "Online"
html[0].body[0].div[6].div[0]...div[1].span[0] = "Offline"
```

These paths are like addresses -- they tell you exactly where in the page tree each match lives.

### `extract-text` -- erode tags, reveal content

Given a structural path, strip away all HTML tags below that point and return just the visible text, in reading order.

```bash
./skills/kapture-dom-erode/tools.sh extract-text -f page.html -p "structural.path.here"
```

**Options:**
- `-f, --file` -- saved DOM file (JSON with `"html"` key, or raw HTML -- see "Saving the DOM" above)
- `-k, --content-key` -- JSON key for DOM content when using JSON input (default: `html`)
- `-p, --path` -- a gron-style path from `gron-grep` output (or a common ancestor of multiple results)

**Example:** extract the member list from a chat sidebar:
```bash
./skills/kapture-dom-erode/tools.sh extract-text -f .tmp/page.html \
  -p "html[0].body[0].div[6].div[0].div[0].div[0].div[1]"
```

Output:
```
Online
Meagan Connolly
Moderator
You
Julian Le Beron
Offline
Ben Casey
Zoe Spurgeon
```

All the wrapper divs, spans, avatar markup, and CSS classes are gone. What's left is what the user sees.

## Workflow

The typical two-step process:

1. **Search** for a keyword you know is on screen:
   ```bash
   ./skills/kapture-dom-erode/tools.sh gron-grep -f page.html -q "Online" -i
   ```

2. **Compare paths** from the results. Find where they diverge -- the shared prefix is their common container (the region of the page that holds both results).

3. **Extract text** from that common container to get all the visible content in that region:
   ```bash
   ./skills/kapture-dom-erode/tools.sh extract-text -f page.html -p "shared.path"
   ```

This works on any web app -- dashboards, messaging platforms, admin panels, documentation sites -- anything Kapture can capture.

## Files

- `tools.sh` -- POSIX shell wrapper (handles dependencies automatically)
- `kapture_dom_erode.py` -- Python implementation (BeautifulSoup + lxml)

## Dependencies

- Python 3 (via `uv`)
- beautifulsoup4 and lxml (auto-installed by `uv` at runtime)

No manual installation required.

## Keywords

kapture, kapture-mcp, kapture-dom, dom-erode, dom-parse, dom-extract, tag-soup, structural-erosion, browser-automation, web-scraping, opencode-skill
