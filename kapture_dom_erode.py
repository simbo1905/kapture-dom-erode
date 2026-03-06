#!/usr/bin/env python3
import argparse
import sys
import re
from bs4 import BeautifulSoup, NavigableString


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
    with open(args.file, "r", encoding="utf-8") as f:
        # Sometimes Kapture DOM is wrapped in JSON
        content = f.read()
        if content.strip().startswith("{"):
            import json

            try:
                data = json.loads(content)
                content = data.get("html", content)
            except:
                pass

    soup = BeautifulSoup(content, "lxml")
    query = args.query.lower() if args.ignore_case else args.query

    for text_node in soup.find_all(string=True):
        if text_node.parent and text_node.parent.name not in ["script", "style"]:
            node_text = text_node.strip()
            if not node_text:
                continue

            search_text = node_text.lower() if args.ignore_case else node_text
            if query in search_text:
                path = get_gron_path(text_node.parent)
                # Escape quotes in value
                val = node_text.replace('"', '\\"')
                print(f'{path} = "{val}"')


def do_extract_text(args):
    with open(args.file, "r", encoding="utf-8") as f:
        content = f.read()
        if content.strip().startswith("{"):
            import json

            try:
                data = json.loads(content)
                content = data.get("html", content)
            except:
                pass

    soup = BeautifulSoup(content, "lxml")
    target = resolve_path(soup, args.path)

    if target:
        # Erode tags into text regions
        # We'll use a separator (like double newline) to show block separation
        text = target.get_text(separator=" \n ", strip=True)
        # Clean up excessive newlines
        text = re.sub(r"\n\s*\n", "\n", text)
        print(text)
    else:
        print(f"Could not resolve path: {args.path}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Tag Soup Parse: A tool to structurally erode and query DOM trees using gron-like syntax."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # gron-grep
    parser_gg = subparsers.add_parser(
        "gron-grep", help="Find text and output gron-style structural paths"
    )
    parser_gg.add_argument(
        "--file", "-f", required=True, help="Input HTML or JSON-wrapped HTML file"
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
        "--file", "-f", required=True, help="Input HTML or JSON-wrapped HTML file"
    )
    parser_et.add_argument(
        "--path",
        "-p",
        required=True,
        help="Gron-style path to the root element to extract text from",
    )

    args = parser.parse_args()

    if args.command == "gron-grep":
        do_gron_grep(args)
    elif args.command == "extract-text":
        do_extract_text(args)


if __name__ == "__main__":
    main()
