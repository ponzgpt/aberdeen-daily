#!/usr/bin/env python3
"""Email the latest published edition to the editor for review (not to subscribers).

Reads https://aberdeen-daily.technoir.cloud/api/editions/latest.json, renders it as a plain HTML
email and sends it through Gmail SMTP. Sends each edition once (state in STATE).
Standard library only.

    email-edition.py --dry-run > preview.html     # render only
    email-edition.py                              # send (needs /etc/aberdeen-daily/smtp.env)

/etc/aberdeen-daily/smtp.env (root, 600), written by scripts/set-email-password.sh:
    SMTP_USER=<gmail address>  SMTP_PASSWORD=<app password>  MAIL_TO=<address>
"""

import argparse
import html
import json
import re
import smtplib
import sys
import urllib.request
from email.message import EmailMessage
from pathlib import Path

SITE = "https://aberdeen-daily.technoir.cloud"
ENV = Path("/etc/aberdeen-daily/smtp.env")
STATE = Path("/var/lib/aberdeen-daily/last-emailed")


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
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print the HTML instead of sending")
    ap.add_argument(
        "--force", action="store_true", help="send even if this edition was already sent"
    )
    args = ap.parse_args()
    with urllib.request.urlopen(f"{SITE}/api/editions/latest.json", timeout=30) as r:
        ed = json.load(r)
    subject, body = render(ed)
    if args.dry_run:
        print(body)
        return 0
    if not args.force and STATE.exists() and STATE.read_text().strip() == ed["id"]:
        return 0
    if not ENV.exists():
        print(f"not configured: run scripts/set-email-password.sh ({ENV} missing)")
        return 0
    env = dict(ln.split("=", 1) for ln in ENV.read_text().splitlines() if "=" in ln)
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, env["SMTP_USER"], env["MAIL_TO"]
    msg.set_content(f"{ed['masthead']} {ed['date']}: {SITE}")
    msg.add_alternative(body, subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
        s.login(env["SMTP_USER"], env["SMTP_PASSWORD"])
        s.send_message(msg)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(ed["id"])
    print(f"emailed {ed['id']} to {env['MAIL_TO']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
