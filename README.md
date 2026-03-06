# kapture-dom-erode

You asked your LLM to check a web page. It saved an DOM dump that blows up its context window. 😱 


```bash
❯ ls -alh kapture-dom-page-save.html
-rw-r--r--  1 yourname  staff   1.8M Mar  6 13:06 kapture-dom-page-save.html 😤 
```
 
What now? Use the kapture-dom-erode skill. Read the *visible* text from multi-megabyte Kapture snapshots without drowning in `<div>` soup.

This tool lets it `gron-grep` for the strings you care about then `extract-text` to *erode* away all the `div` soup between them. This returns the smallest region of screen text that *includes* all the strings you searched for. This allows it to find all the text within a heavily nested side panel of a complex dynamic web page.  

## You Know That Moment When...

Your agent says *"I can see the page"* but what it actually has is millions of characters of nested HTML. 

**You** see text on screen that is not far apart. The **LLM** sees that text a mile apart inside 47 wrapper tags. 

## The Problem

- 🤯 **Kapture DOM dumps are massive** -- 1-5MB of framework-generated tag soup
- 🔍 **Text is buried** -- "Wireless Headphones" lives at `html[0].body[0].div[6].div[2].div[1].div[4].div[0].h3[0]`
- 💸 **Context windows cry** -- feeding raw HTML to your LLM is... not ideal
- ⚠️ **Screenshots aren't parseable** -- you can see it, but the agent can't read it

If you can see six products on "special offer" on the page. The agent cannot see those six special offers amongst the 25 products in the 2M tag soup! 

## The Solution `kapture-dom-erode`

The commands. Find two on special, erode the tags to find them all. Done.

```bash
# Step 1: grep for WHERE the first special offer lives in the DOM tree
./tools.sh gron-grep -f saved_page.html -q "Wireless Headphones"
# html[0].body[0].div[1].main[0].div[1].div[0].div[3].section[1].div[0].div[1].div[0].div[0].h3[0]

# Step 2: grep for WHERE another special offer lives in the DOM tree
./tools.sh gron-grep -f saved_page.html -q "Gaming Mouse"
# html[0].body[0].div[1].main[0].div[1].div[0].div[3].section[1].div[0].div[1].div[1].div[0].h3[0]

# Step 3: erode the tag soup to get the readable text
./tools.sh extract-text -f saved_page.html \
  -p "html[0].body[0].div[1].main[0].div[1].div[0].div[3].section[1]"
```

Boom. Human-readable content from the tag soup.

---

## 🚀 Features That Actually Matter

**1. Structural grep for the DOM** 🔍

Search any text and get back its exact coordinates in the HTML tree. Like GPS for where content lives.

```bash
./tools.sh gron-grep -f page.html -q "On Sale"

# html[0].body[0].div[3].div[1].div[2].span[0] = "On Sale"
# html[0].body[0].div[3].div[5].div[2].span[0] = "On Sale"
```

**2. Tag Erosion** 🧽

Strip away all the markup and return just the visible text from any region of the page. Reading order preserved.

```bash
./tools.sh extract-text -f page.html -p "html[0].body[0].div[3]"

# On Sale
# Wireless Headphones -- Was $99, now $49
# USB-C Hub -- Was $45, now $29
# Mechanical Keyboard -- Was $129, now $79
```

**3. Zero Dependencies** 

Just Python + BeautifulSoup. No npm install, no Docker, no 47 layers of abstraction. Pure DOM parsing goodness.

**4. Stupid Fast** ⚡

Processes multi-megabyte files in seconds. Because waiting for tag soup to parse is nobody's idea of fun.

---

## 💡 Use Cases That'll Make You Look Like a Genius

### For AI Agent Wranglers

- **📊 Extract structured data** -- "I can see 3 products on sale. List all of them."
- **👥 Scrape member lists** -- Chat sidebars, team directories, attendee lists
- **🛒 Parse e-commerce** -- "Find all items marked 'Special Offer' and their prices"
- **📑 Read documentation tables** -- API endpoints, config options, pricing tiers

### For Web Scraping Without Scraping

- **🔒 No rate limits** -- you already have the DOM snapshot
- **📄 No anti-bot** -- it's a local file, not a live site
- **🎯 Precise extraction** -- find the container, erode the tags, get clean text

---

## Example: "Show Me All The Deals"

You're browsing Amazon. You see two products with "Limited Time Deal" badges. You want your LLM to extract **every** deal on the page.

**Step 1** -- Find where "Limited Time Deal" lives:

```bash
./tools.sh gron-grep -f amazon.html -q "Limited Time Deal"
# html[0].body[0].div[2].div[1].div[0].div[3].span[0]
# html[0].body[0].div[2].div[3].div[0].div[3].span[0]
```

**Step 2** -- Both share a common ancestor (`div[2]`). Extract everything from there:

```bash
./tools.sh extract-text -f amazon.html -p "html[0].body[0].div[2]"
```

**Result** -- clean, readable list:

```
Today's Deals
Sony WH-1000XM5
Was $399, now $299
Limited Time Deal
Anker USB-C Hub
Was $59, now $39
Limited Time Deal
Logitech MX Master 3S
Was $99, now $79
Limited Time Deal
...
```

All the wrapper divs, CSS classes, React component markup -- gone. Just what the human sees.

---

## 📖 Quick Reference (The Details)

```
NAME
  kapture-dom-erode — search and extract text from Kapture DOM snapshots

SYNOPSIS
  ./tools.sh gron-grep -f <file> -q <text> [-i]
  ./tools.sh extract-text -f <file> -p <path>

COMMANDS
  gron-grep     Find text, output structural paths (gron-style)
  extract-text  Strip tags below path, return visible text

OPTIONS
  -f, --file     Input HTML file from Kapture
  -q, --query    Text to search for (gron-grep)
  -p, --path     Structural path to extract from (extract-text)
  -i             Case-insensitive search (gron-grep)

EXAMPLES
  # Find where "Add to Cart" buttons live
  ./tools.sh gron-grep -f shop.html -q "Add to Cart" -i

  # Extract all product names from a listing page
  ./tools.sh gron-grep -f shop.html -q "iPhone 15"
  # (compare paths, find common ancestor)
  ./tools.sh extract-text -f shop.html -p "html[0].body[0].div[4]"
```

---

## ⚡ Installation

Copy the skill to your agent's skills directory:

```bash
# OpenCode
cp -r kapture-dom-erode ~/.config/opencode/skills/

# Claude Code
cp -r kapture-dom-erode ~/.claude/skills/
```

Dependencies? Just Python + BeautifulSoup. The wrapper handles it via `uv`.

---

## 🎯 Why This Exists

Born from frustration with Kapture MCP saving massive DOM dumps and then... what? Screenshots are pretty but not parseable. Raw HTML is machine-readable but human-unreadable. You need something in between.

This skill is that bridge: find the text, erode the tags, get clean content.

You are not someone who enjoys manually grepping through `div[6].div[0].div[0].div[0].div[1].div[0]...` paths to find where the "Buy Now" button lives. Obviously not you. Me neither.

---

## 📜 License

MIT -- Copyright (c) 2026 Simon Massey

Use it, fork it, put it in production. No warranty -- if it deletes your DOM files, that's on you (though it only reads, so you're probably fine).

---

Made with ❤️ and frustration by someone who spent too many tokens hunting for text in tag soup.

Now go erode some DOMs like a pro. 🧽✨
