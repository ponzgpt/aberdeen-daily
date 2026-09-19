#!/usr/bin/env python3
"""Render the latest published edition as an HTML email for the editor's review.

Reads the site's /api/editions/latest.json and prints the HTML to stdout. The daily
Claude task puts it in the editor's Gmail as a draft. Standard library only.

    email-edition.py > preview.html
"""

import html
import json
import re
import sys
import urllib.request

SITE = "https://aberdeen-daily.technoir.cloud"


def inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)


def body_html(markdown: str) -> str:
    """Enough Markdown for the paper: paragraphs, ### labels, lists, quotes; tables as monospace."""
    out = []
    for block in re.split(r"\n\s*\n", markdown.strip()):
        lines = block.splitlines()
        if block.startswith("|"):
            rows = [ln for ln in lines if not re.fullmatch(r"\|[\s:|-]+\|", ln)]
            out.append("<pre style='font-size:13px'>" + html.escape("\n".join(rows)) + "</pre>")
        elif block.startswith("#"):
            out.append(f"<h4 style='margin:1em 0 .3em'>{inline(block.lstrip('#').strip())}</h4>")
        elif all(ln.lstrip().startswith(("- ", "* ")) for ln in lines):
            out.append(
                "<ul>" + "".join(f"<li>{inline(ln.lstrip()[2:])}</li>" for ln in lines) + "</ul>"
            )
        elif block.startswith(">"):
            out.append(
                f"<blockquote>{inline(' '.join(ln.lstrip('> ') for ln in lines))}</blockquote>"
            )
        elif block.strip() == "---":
            out.append("<hr>")
        else:
            out.append(f"<p>{inline(' '.join(lines))}</p>")
    return "\n".join(out)


def render(ed: dict) -> tuple[str, str]:
    arts = sorted(ed["articles"], key=lambda a: (a.get("priority") != 1, a["file"]))
    parts = [
        "<div style='max-width:640px;margin:0 auto;font:16px/1.55 Georgia,serif;color:#1c1a17'>",
        f"<p style='color:#8a1c1c;font-size:13px'>EDITOR'S REVIEW COPY · not sent to subscribers · "
        f"<a href='{SITE}'>read it on the site</a></p>",
        f"<h1 style='margin:0'>{html.escape(ed['masthead'])}</h1>",
        f"<p style='color:#6b655c;margin-top:0'>No. {ed['number']} · {ed['date']} · "
        f"{len(arts)} stories</p>",
    ]
    for a in arts:
        parts.append("<hr>")
        parts.append(
            "<p style='color:#6b655c;font-size:12px;text-transform:uppercase'>"
            f"{html.escape(a['section'] or '')}</p>"
        )
        parts.append(f"<h2 style='margin:.2em 0'>{html.escape(a['headline'])}</h2>")
        if a.get("deck"):
            parts.append(f"<p><em>{html.escape(a['deck'])}</em></p>")
        parts.append(body_html(a.get("body") or ""))
        srcs = [s for s in a.get("sources") or [] if isinstance(s, dict) and s.get("url")]
        if srcs:
            links = " · ".join(
                f"<a href='{html.escape(s['url'])}'>{html.escape(s.get('name') or s['url'])}</a>"
                for s in srcs
            )
            parts.append(f"<p style='font-size:13px;color:#6b655c'>Sources: {links}</p>")
    parts.append("</div>")
    subject = f"[Review] {ed['masthead']} — {ed['date']}"
    return subject, "\n".join(parts)


def main() -> int:
    with urllib.request.urlopen(f"{SITE}/api/editions/latest.json", timeout=30) as r:
        ed = json.load(r)
    subject, body = render(ed)
    print(f"<!-- subject: {subject} -->")
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
