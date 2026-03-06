# kapture-dom-erode

> **Your LLM saved a web page with [Kapture MCP](https://github.com/anthropics/anthropic-quickstarts/tree/main/kapture-mcp). Now what?**
>
> The saved DOM is millions of characters of nested `<div>` soup. This skill finds visible text and extracts clean, readable regions -- the way a human sees the page.

---

## The Problem

When an AI agent captures a page with `kapture_dom`, the result is a multi-megabyte HTML file. The text you can *see* on screen is buried inside hundreds of wrapper tags. Screenshots aren't machine-readable. Raw HTML is unreadable. You need something in between.

## The Solution

**Two commands. That's it.**

```
gron-grep  -->  find where text lives in the DOM tree
extract-text  -->  strip tags, return just the readable content
```

---

## Example: "Show me all the deals on this page"

You're browsing an e-commerce site. You can see two products on sale:

> *"Wireless Headphones -- Was $99, now $49"*
> *"USB-C Hub -- Was $45, now $29"*

You want your LLM to extract **all** the deals, not just those two. Here's what happens:

**Step 1** -- Search for the product names you can see:

```bash
./tools.sh gron-grep -f page.html -q "Wireless Headphones"
# html[0].body[0].div[2].div[1].div[0].div[3].div[0].h3[0]

./tools.sh gron-grep -f page.html -q "USB-C Hub"
# html[0].body[0].div[2].div[1].div[0].div[5].div[0].h3[0]
```

**Step 2** -- Both paths share a common ancestor (`div[2].div[1]`). Extract text from there:

```bash
./tools.sh extract-text -f page.html \
  -p "html[0].body[0].div[2].div[1]"
```

**Result** -- all the deals, clean and readable:

```
Today's Deals
Wireless Headphones
Was $99, now $49
4.5 stars (2,341 reviews)
USB-C Hub
Was $45, now $29
4.7 stars (892 reviews)
Mechanical Keyboard
Was $129, now $79
4.3 stars (1,205 reviews)
Webcam HD Pro
Was $89, now $59
4.6 stars (567 reviews)
```

All the wrapper divs, CSS classes, and framework markup -- gone. Just the content.

---

## Install

Copy the skill folder to your skills directory:

```bash
# OpenCode
cp -r kapture-dom-erode ~/.config/opencode/skills/

# Claude Code
cp -r kapture-dom-erode ~/.claude/skills/
```

### Dependencies

- Python 3 (via [`uv`](https://docs.astral.sh/uv/))
- beautifulsoup4 + lxml (auto-installed at runtime by `uv`)

No manual `pip install` needed.

---

## Commands

### `gron-grep` -- find text

```bash
./tools.sh gron-grep -f <dom-file> -q <search-text> [-i]
```

| Flag | Description |
|------|-------------|
| `-f` | Saved DOM file (HTML from Kapture) |
| `-q` | Text to search for |
| `-i` | Case-insensitive search |

### `extract-text` -- erode tags, get content

```bash
./tools.sh extract-text -f <dom-file> -p <gron-path>
```

| Flag | Description |
|------|-------------|
| `-f` | Saved DOM file |
| `-p` | Gron-style path (from `gron-grep` output) |

---

## How It Works

1. **`gron-grep`** walks the entire DOM tree and returns a precise structural path (like `html[0].body[0].div[2].span[0]`) for every element matching your search text.

2. You compare paths to find their **common ancestor** -- the container that holds the region of the page you're interested in.

3. **`extract-text`** takes that ancestor path, strips away all HTML tags below it, and returns the visible text in reading order.

Think of it as **`grep` for what's on screen**, not what's in the source code.

---

## License

MIT

---

*Built for use with [Kapture MCP](https://github.com/anthropics/anthropic-quickstarts/tree/main/kapture-mcp) and the [OpenCode](https://opencode.ai) / [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview) ecosystem.*
