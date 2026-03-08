#!/usr/bin/env python3
import argparse
import json
import sys
import re
from bs4 import BeautifulSoup, Comment, NavigableString


def get_gron_path(element):
    """Generates a gron-style path for a BeautifulSoup tag."""
    parts = []
    current = element
    while (
        current is not None
        and current.name is not None
        and current.name != "[document]"
    ):
        # Find siblings with the same tag
        if current.parent:
            siblings = current.parent.find_all(current.name, recursive=False)
            try:
                idx = siblings.index(current)
            except ValueError:
                idx = 0
        else:
            idx = 0

        parts.append(f"{current.name}[{idx}]")
        current = current.parent

    return ".".join(reversed(parts))


def resolve_path(soup, path):
    """Resolves a gron-style path back to a BeautifulSoup tag."""
    if not path:
        return soup

    parts = path.split(".")
    current = soup
    for part in parts:
        if not part:
            continue
        match = re.match(r"([\w-]+)(?:\[(\d+)\])?", part)
        if not match:
            print(f"Warning: could not parse path part {part}", file=sys.stderr)
            return None

        tag_name = match.group(1)
        idx = int(match.group(2)) if match.group(2) else 0

        children = current.find_all(tag_name, recursive=False)
        if idx < len(children):
            current = children[idx]
        else:
            print(
                f"Warning: index out of bounds for {part} (found {len(children)} children)",
                file=sys.stderr,
            )
            return None

    return current


def do_gron_grep(args):
    content = load_dom_content(args.file, args.content_key)

    soup = BeautifulSoup(content, "lxml")
    query = args.query.lower() if args.ignore_case else args.query

    for text_node in soup.find_all(string=True):
        if isinstance(text_node, Comment):
            continue
        if text_node.parent and not _any_ancestor_hidden(text_node.parent):
            node_text = text_node.strip()
            if not node_text:
                continue

            search_text = node_text.lower() if args.ignore_case else node_text
            if query in search_text:
                path = get_gron_path(text_node.parent)
                val = node_text.replace('"', '\\"')
                print(f'{path} = "{val}"')


def do_extract_text(args):
    content = load_dom_content(args.file, args.content_key)

    soup = BeautifulSoup(content, "lxml")
    target = resolve_path(soup, args.path)

    if target:
        text = _visible_text(target)
        print(text)
    else:
        print(f"Could not resolve path: {args.path}", file=sys.stderr)
        sys.exit(1)


# Tags that are never user-visible content
_SKIP_TAGS = {
    "script",
    "style",
    "noscript",
    "head",
    "meta",
    "link",
    "template",
    "svg",
    "iframe",
    "object",
    "embed",
}

# Block-level tags that form natural content containers
_BLOCK_TAGS = {
    "div",
    "section",
    "article",
    "main",
    "aside",
    "nav",
    "header",
    "footer",
    "p",
    "li",
    "td",
    "th",
    "blockquote",
    "pre",
    "figure",
    "figcaption",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
}

# Heading tags used for section-header detection
_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

_HIDDEN_CLASSES = {
    "screenreader-only",
    "sr-only",
    "visually-hidden",
    "screen-reader-text",
}

_DISPLAY_NONE_RE = re.compile(r"display\s*:\s*none", re.I)
_VISIBILITY_HIDDEN_RE = re.compile(r"visibility\s*:\s*hidden", re.I)


def _is_hidden(tag):
    if not hasattr(tag, "attrs"):
        return False
    if tag.has_attr("hidden"):
        return True
    if tag.get("aria-hidden") == "true":
        return True
    style = tag.get("style", "")
    if style and (_DISPLAY_NONE_RE.search(style) or _VISIBILITY_HIDDEN_RE.search(style)):
        return True
    classes = tag.get("class", [])
    if isinstance(classes, str):
        classes = classes.split()
    if _HIDDEN_CLASSES.intersection(classes):
        return True
    return False


def _any_ancestor_hidden(tag):
    p = tag
    while p and p.name:
        if p.name in _SKIP_TAGS or _is_hidden(p):
            return True
        p = p.parent
    return False


def _visible_text(element):
    """Return all visible text under element, skipping hidden and skip-tags."""
    chunks = []
    for node in element.descendants:
        if isinstance(node, Comment):
            continue
        if isinstance(node, NavigableString):
            if _any_ancestor_hidden(node.parent):
                continue
            text = node.strip()
            if text:
                chunks.append(text)
    return " ".join(chunks)


def _score_block(element):
    """Return (char_count, word_count, preview) for a block element."""
    text = _visible_text(element)
    chars = len(text)
    words = len(text.split()) if text else 0
    preview = text[:256].replace("\n", " ")
    return chars, words, preview


def common_ancestor_path(path_a, path_b):
    """Return the longest common ancestor path shared by two gron-style paths."""
    parts_a = path_a.split(".")
    parts_b = path_b.split(".")
    common = []
    for a, b in zip(parts_a, parts_b):
        if a == b:
            common.append(a)
        else:
            break
    return ".".join(common) if common else ""


def do_main_text(args):
    content = load_dom_content(args.file, args.content_key)
    soup = BeautifulSoup(content, "lxml")

    # Collect scores for every block-level element (same as top-content)
    results = []
    seen_paths = set()
    for tag in soup.find_all(_BLOCK_TAGS):
        skip = False
        p = tag.parent
        while p and p.name:
            if p.name in _SKIP_TAGS:
                skip = True
                break
            p = p.parent
        if skip:
            continue
        chars, words, preview = _score_block(tag)
        if chars < 50:
            continue
        path = get_gron_path(tag)
        if path in seen_paths:
            continue
        seen_paths.add(path)
        results.append((chars, words, preview, path, tag))

    results.sort(key=lambda x: x[0], reverse=True)

    if len(results) < 2:
        print("Not enough content blocks found.", file=sys.stderr)
        sys.exit(1)

    path_1 = results[0][3]
    path_2 = results[1][3]

    ancestor_path = common_ancestor_path(path_1, path_2)
    if not ancestor_path:
        print(
            f"Warning: no common ancestor found for:\n  {path_1}\n  {path_2}\n"
            "Falling back to largest block.",
            file=sys.stderr,
        )
        ancestor_path = path_1

    if not args.quiet:
        print(f"Top-1: {path_1}")
        print(f"Top-2: {path_2}")
        print(f"Common ancestor: {ancestor_path}")
        print()

    ancestor = resolve_path(soup, ancestor_path)
    if ancestor is None:
        print(f"Could not resolve ancestor path: {ancestor_path}", file=sys.stderr)
        sys.exit(1)

    text = _visible_text(ancestor)
    print(text)


def do_top_content(args):
    content = load_dom_content(args.file, args.content_key)

    soup = BeautifulSoup(content, "lxml")
    top_n = args.top

    # Collect scores for every block-level element
    results = []
    seen_paths = set()

    for tag in soup.find_all(_BLOCK_TAGS):
        # Skip if ancestor already in skip-tags
        skip = False
        p = tag.parent
        while p and p.name:
            if p.name in _SKIP_TAGS:
                skip = True
                break
            p = p.parent
        if skip:
            continue

        chars, words, preview = _score_block(tag)
        if chars < 50:
            continue  # too small to be interesting

        path = get_gron_path(tag)
        if path in seen_paths:
            continue
        seen_paths.add(path)

        results.append((chars, words, preview, path, tag))

    # Sort by char count descending, take top N
    results.sort(key=lambda x: x[0], reverse=True)
    top = results[:top_n]

    # Print table
    col_path = max(len(r[3]) for r in top) if top else 10
    col_chars = 6
    col_words = 6

    header = (
        f"{'Path':<{col_path}}  {'Chars':>{col_chars}}  {'Words':>{col_words}}  Preview"
    )
    print(header)
    print("-" * len(header))
    for chars, words, preview, path, _tag in top:
        trunc = (preview[:253] + "...") if len(preview) > 256 else preview
        print(
            f"{path:<{col_path}}  {chars:>{col_chars}}  {words:>{col_words}}  {trunc}"
        )

    # --- Auto-detect main course content region ---
    # Heuristic: look for the element whose DIRECT children include both
    # heading tags and substantial sibling body blocks in alternating pattern.
    # Score each block-container by counting (heading child, big-sibling) pairs.
    if not args.no_detect:
        print("\n--- Content region detection ---")
        best_score = 0
        best_path = None
        best_tag = None

        for _chars, _words, _preview, path, tag in results[:50]:
            children = [c for c in tag.children if hasattr(c, "name") and c.name]
            if len(children) < 3:
                continue

            heading_count = sum(1 for c in children if c.name in _HEADING_TAGS)
            big_block_count = sum(
                1
                for c in children
                if c.name in _BLOCK_TAGS and len(_visible_text(c)) > 80
            )
            # Alternating pattern score: headings + big blocks together
            score = heading_count * 2 + big_block_count
            if score > best_score:
                best_score = score
                best_path = path
                best_tag = tag

        if best_tag is not None:
            print(f"Best candidate: {best_path}")
            print(
                f"  Score: {best_score}  "
                f"(headings={sum(1 for c in best_tag.children if hasattr(c, 'name') and c.name in _HEADING_TAGS)}, "
                f"blocks={sum(1 for c in best_tag.children if hasattr(c, 'name') and c.name in _BLOCK_TAGS)})"
            )
            print(f"\nTo extract all content from this region:")
            print(
                f'  uv run kapture_dom_erode.py extract-text -f {args.file} -p "{best_path}" -k {args.content_key}'
            )
        else:
            print(
                "No clear content region detected -- try extract-text on the largest path above."
            )


def load_dom_content(file_path, content_key="html"):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.strip().startswith("{"):
        return content

    try:
        data = json.loads(content)
    except Exception:
        return content

    if isinstance(data, dict) and content_key in data:
        return data.get(content_key)

    if isinstance(data, dict):
        return data.get("html", content)

    return content


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Tag Soup Parse: structurally erode and query DOM trees using gron-like syntax.\n\n"
            "INPUT FILE FORMAT: The -f/--file argument accepts either:\n"
            "  1. The full JSON object returned by kapture_dom (recommended).\n"
            '     The parser reads the value from the configured content key (default: "html").\n'
            "  2. A raw HTML file: <body>...</body>\n"
            "The tool auto-detects raw HTML by checking whether the file starts with '{'."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # gron-grep
    parser_gg = subparsers.add_parser(
        "gron-grep", help="Find text and output gron-style structural paths"
    )
    parser_gg.add_argument(
        "--file",
        "-f",
        required=True,
        help="Saved DOM file: kapture_dom response JSON (preferred) or raw HTML",
    )
    parser_gg.add_argument(
        "--content-key",
        "-k",
        default="html",
        help='JSON key that contains DOM content when loading from kapture_dom JSON (default: "html")',
    )
    parser_gg.add_argument("--query", "-q", required=True, help="Text to search for")
    parser_gg.add_argument(
        "--ignore-case", "-i", action="store_true", help="Case insensitive search"
    )

    # extract-text
    parser_et = subparsers.add_parser(
        "extract-text",
        help="Extract all visible text below a certain gron path (erodes tags)",
    )
    parser_et.add_argument(
        "--file",
        "-f",
        required=True,
        help="Saved DOM file: kapture_dom response JSON (preferred) or raw HTML",
    )
    parser_et.add_argument(
        "--content-key",
        "-k",
        default="html",
        help='JSON key that contains DOM content when loading from kapture_dom JSON (default: "html")',
    )
    parser_et.add_argument(
        "--path",
        "-p",
        required=True,
        help="Gron-style path to the root element to extract text from",
    )

    # main-text
    parser_mt = subparsers.add_parser(
        "main-text",
        help="Auto-extract main body text: finds top-2 content blocks, erodes their common ancestor",
    )
    parser_mt.add_argument(
        "--file",
        "-f",
        required=True,
        help="Saved DOM file: kapture_dom response JSON (preferred) or raw HTML",
    )
    parser_mt.add_argument(
        "--content-key",
        "-k",
        default="html",
        help='JSON key that contains DOM content when loading from kapture_dom JSON (default: "html")',
    )
    parser_mt.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress path diagnostics, output only the extracted text",
    )

    # top-content
    parser_tc = subparsers.add_parser(
        "top-content",
        help="Rank all block elements by visible text size and auto-detect main content region",
    )
    parser_tc.add_argument(
        "--file",
        "-f",
        required=True,
        help="Saved DOM file: kapture_dom response JSON (preferred) or raw HTML",
    )
    parser_tc.add_argument(
        "--content-key",
        "-k",
        default="html",
        help='JSON key that contains DOM content when loading from kapture_dom JSON (default: "html")',
    )
    parser_tc.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top results to show (default: 10)",
    )
    parser_tc.add_argument(
        "--no-detect",
        action="store_true",
        help="Skip content region auto-detection",
    )

    args = parser.parse_args()

    if args.command == "gron-grep":
        do_gron_grep(args)
    elif args.command == "extract-text":
        do_extract_text(args)
    elif args.command == "top-content":
        do_top_content(args)
    elif args.command == "main-text":
        do_main_text(args)


if __name__ == "__main__":
    main()
