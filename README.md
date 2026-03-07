# kapture-dom-erode

You asked your LLM to check a web page. It saved a DOM dump that blows up its context window. 😱 

```bash
❯ ls -alh kapture-dom-page-save.html
-rw-r--r--  1 yourname  staff   1.8M Mar  6 13:06 kapture-dom-page-save.html 😤 
```

What now? Use the kapture-dom-erode skill. Read the *visible* text from multi-megabyte Kapture snapshots without drowning in `<div>` soup.

## You Know That Moment When...

Your agent says *"I can see the page"* but what it actually has is millions of characters of nested HTML.

**You** see text on screen that is not far apart. The **LLM** sees that text a mile apart inside 47 wrapper tags.

## The Problem

- 🤯 **Kapture DOM dumps are massive** -- 1-5MB of framework-generated tag soup
- 🔍 **Text is buried** -- "Bake at 180°C" lives at `html[0].body[0].div[6].div[2].div[1].div[4].div[0].p[0]`
- 💸 **Context windows cry** -- feeding raw HTML to your LLM is not ideal
- ⚠️ **Screenshots aren't parseable** -- you can see it, but the agent can't read it

## The Solution

Four commands. Find what you need. Erode the tags. Done.

```bash
# Find WHERE text lives in the DOM
./tools.sh gron-grep -f page.html -q "Bake at 180"

# Auto-extract the page's main body text in one shot
./tools.sh main-text -f page.html

# Rank all block elements by size, auto-detect main content region
./tools.sh top-content -f page.html

# Strip tags below a known path, return visible text
./tools.sh extract-text -f page.html -p "html[0].body[0].div[3]"
```

---

## 🚀 Commands

### `top-content` — Rank blocks and detect content region

Scans every block element, counts visible characters, prints the top N by size with previews. Also auto-detects the most likely "real content" region by spotting the heading + body alternating pattern.

```bash
./tools.sh top-content -f page.html
```

```
Path                                    Chars   Words  Preview
---------------------------------------------------------------
html[0].body[0].main[0]                18432    2901  Roasted Vegetable Tart Serves 4 Ready in 55 minutes...
html[0].body[0].main[0].div[0]         18201    2870  Roasted Vegetable Tart Serves 4 Ready in 55 minutes...
html[0].body[0].main[0].div[0].div[1]   9823    1544  Ingredients 2 sheets shortcrust pastry 3 courgettes...

--- Content region detection ---
Best candidate: html[0].body[0].main[0].div[0].div[1]
  Score: 14  (headings=4, blocks=6)
```

Options: `--top N` (default 10), `--no-detect` (skip auto-detection).

### `gron-grep` — Structural grep

Search any text string and get back its exact coordinates in the HTML tree.

```bash
./tools.sh gron-grep -f page.html -q "On Sale"
# html[0].body[0].div[3].div[1].div[2].span[0] = "On Sale"
# html[0].body[0].div[3].div[5].div[2].span[0] = "On Sale"
```

Options: `-q <text>`, `-i` (case-insensitive).

### `extract-text` — Tag erosion

Strip away all markup and return visible text from any subtree. Reading order preserved.

```bash
./tools.sh extract-text -f page.html -p "html[0].body[0].div[3]"
# On Sale
# Wireless Headphones -- Was $99, now $49
# USB-C Hub -- Was $45, now $29
```

### `main-text` — One-shot main body extraction

The fastest path to clean page text. Finds the two largest content blocks, computes their common ancestor, and erodes everything from that ancestor. Because the two biggest text blocks are almost always in the main body — their common ancestor joins all the siblings together, capturing everything above, between, and below them while excluding nav chrome.

```bash
./tools.sh main-text -f page.html
```

Output (diagnostic lines + extracted text):
```
Top-1: html[0].body[0].main[0].div[0].section[1]
Top-2: html[0].body[0].main[0].div[0].section[2]
Common ancestor: html[0].body[0].main[0].div[0]

Roasted Vegetable Tart
Serves 4 · Ready in 55 minutes

Ingredients
2 sheets shortcrust pastry
3 courgettes, sliced
...
```

Use `--quiet` / `-q` to suppress the diagnostic lines and get only the text.


---

## Example: "Show Me All The Deals"

You see two products with "Limited Time Deal" badges. You want all of them.

```bash
# Find both
./tools.sh gron-grep -f shop.html -q "Limited Time Deal"
# html[0].body[0].div[2].div[1].div[0].div[3].span[0]
# html[0].body[0].div[2].div[3].div[0].div[3].span[0]

# Both share ancestor div[2] — extract everything from there
./tools.sh extract-text -f shop.html -p "html[0].body[0].div[2]"
```

Or skip the manual steps entirely:

```bash
./tools.sh main-text -f shop.html
```

---

## Input Format

`-f` accepts either:
1. The full JSON object returned by `kapture_dom` (recommended) — the tool reads the `"html"` key by default
2. A raw `.html` file

Override the JSON key with `-k / --content-key` if your dump uses a different field name.

---

## 📖 Quick Reference

```
SYNOPSIS
  ./tools.sh main-text    -f <file> [-q]
  ./tools.sh top-content  -f <file> [--top N] [--no-detect]
  ./tools.sh gron-grep    -f <file> -q <text> [-i]
  ./tools.sh extract-text -f <file> -p <path>

OPTIONS (all commands)
  -f, --file         Input file (kapture_dom JSON or raw HTML)
  -k, --content-key  JSON key for DOM content (default: html)

main-text
  -q, --quiet        Output extracted text only, no diagnostics

top-content
  --top N            Show top N results (default: 10)
  --no-detect        Skip content region auto-detection

gron-grep
  -q, --query        Text to search for
  -i                 Case-insensitive search

extract-text
  -p, --path         Gron-style path to extract from
```

---

## ⚡ Installation

```bash
# OpenCode
cp -r kapture-dom-erode ~/.config/opencode/skills/

# Claude Code
cp -r kapture-dom-erode ~/.claude/skills/
```

Dependencies: Python + BeautifulSoup, handled via `uv`.

---

## 📜 License

MIT — Copyright (c) 2026 Simon Massey
