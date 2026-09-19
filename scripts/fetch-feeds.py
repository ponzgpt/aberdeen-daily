#!/usr/bin/env python3
"""Ingest desk: pull the day's Aberdeen news into inbox/feeds.md.

Reads the source list in inbox/sources.json, fetches each RSS feed, and
writes one block per item into inbox/feeds.md in the format the prose desks
expect: a heading, a short extract, and the source URL.

This is an ingest step, not a writing step. It carries the headline, a
trimmed extract of the feed summary, the publisher's name and the canonical
link, so that a prose desk can write an original story that cites and links
the source. Reproducing a publisher's article text in the paper is not
permitted; see AGENTS.md.

Only Python's standard library is used, so there is nothing to install.

Usage:
    fetch-feeds.py [--sources inbox/sources.json] [--out inbox/feeds.md]
                   [--max-per-feed 6] [--hours 36]

Exits 1 without writing if every feed fails, so a nightly run fails loudly
rather than reprinting yesterday's paper.
"""

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree

UA = "aberdeen-daily/1.0 (+https://github.com/ponzgpt/aberdeen-daily)"
TAGS = re.compile(r"<[^>]+>")
SPACES = re.compile(r"\s+")
EXTRACT_WORDS = 45


def clean(text):
    """Strip markup and collapse whitespace out of a feed field."""
    if not text:
        return ""
    return SPACES.sub(" ", html.unescape(TAGS.sub(" ", text))).strip()


def trim(text, words=EXTRACT_WORDS):
    """Cut an extract to a fixed number of words, marking it as cut."""
    parts = text.split()
    if len(parts) <= words:
        return text
    return " ".join(parts[:words]).rstrip(".,;:") + " …"


def published(item):
    """Best-effort publication datetime for an RSS or Atom item."""
    for tag in ("pubDate", "published", "updated", "{http://www.w3.org/2005/Atom}updated"):
        raw = item.findtext(tag)
        if not raw:
            continue
        try:
            when = parsedate_to_datetime(raw)
        except (TypeError, ValueError):
            try:
                when = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                continue
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)
        return when
    return None


def link_of(item):
    """RSS puts the URL in <link> text; Atom puts it in an href attribute."""
    raw = item.findtext("link")
    if raw and raw.strip():
        return raw.strip()
    for el in item.iter():
        if el.tag.endswith("link") and el.get("href"):
            return el.get("href").strip()
    return ""


def fetch(url, timeout=20):
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def items_from(xml_bytes, limit):
    """Yield (title, extract, link, when) for RSS <item> or Atom <entry>."""
    root = ElementTree.fromstring(xml_bytes)
    nodes = root.iter("item")
    found = list(nodes)
    if not found:
        found = [el for el in root.iter() if el.tag.endswith("entry")]
    out = []
    for node in found[: limit * 3]:
        title = clean(node.findtext("title") or "")
        if not title:
            continue
        summary = ""
        for tag in ("description", "summary", "{http://www.w3.org/2005/Atom}summary"):
            summary = clean(node.findtext(tag) or "")
            if summary:
                break
        out.append((title, summary, link_of(node), published(node)))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", default="inbox/sources.json")
    parser.add_argument("--out", default="inbox/feeds.md")
    parser.add_argument("--max-per-feed", type=int, default=8)
    parser.add_argument("--hours", type=int, default=168,
                        help="drop items older than this many hours (0 = keep all)")
    args = parser.parse_args()

    sources_path = Path(args.sources)
    if not sources_path.exists():
        print(f"no source list at {sources_path}", file=sys.stderr)
        return 1
    sources = json.loads(sources_path.read_text(encoding="utf-8"))["sources"]

    cutoff = None
    if args.hours:
        cutoff = datetime.now(UTC) - timedelta(hours=args.hours)

    blocks, failures, seen = [], [], set()
    for source in sources:
        name, url = source["name"], source["url"]
        try:
            raw = fetch(url)
            entries = items_from(raw, args.max_per_feed)
        except (urllib.error.URLError, ElementTree.ParseError, OSError) as exc:
            failures.append(f"{name}: {exc}")
            continue

        kept = 0
        for title, summary, link, when in entries:
            if kept >= args.max_per_feed:
                break
            if cutoff and when and when < cutoff:
                continue
            key = title.lower()
            if key in seen:
                continue
            seen.add(key)
            kept += 1
            stamp = when.strftime("%Y-%m-%d %H:%M UTC") if when else "undated"
            blocks.append(
                f"## {title}\n\n"
                f"{trim(summary) if summary else '(No summary in the feed.)'}\n\n"
                f"Source: {name} · {stamp}\n"
                f"{link}\n"
            )

    if not blocks:
        print("every feed failed or returned nothing; not writing", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1

    today = datetime.now(UTC).strftime("%A %d %B %Y")
    header = (
        f"# Feeds — {today}\n\n"
        "Fetched by `scripts/fetch-feeds.py`. Each block is one item: a "
        "headline, a trimmed extract of the publisher's own summary, the "
        "publisher, and the canonical link.\n\n"
        "The prose desks pick three to five of these and write **original** "
        "stories about them, each carrying a `sources:` entry with the link "
        "below. Do not reproduce a publisher's wording in the paper.\n\n"
        "---\n\n"
    )
    Path(args.out).write_text(header + "\n".join(blocks), encoding="utf-8")

    ok = len(sources) - len(failures)
    print(f"wrote {len(blocks)} items from {ok}/{len(sources)} feeds to {args.out}")
    for line in failures:
        print(f"  feed failed — {line}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
