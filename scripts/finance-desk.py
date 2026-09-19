#!/usr/bin/env python3
"""Data desk: a Financial page with live quotes for example tickers.

Fetches quotes from Yahoo Finance's public chart API (no key) for a set of
tickers and renders a Financial story: a quote table and a short templated
reading. Everything on the page is computed from what the API returned — a
data desk, deliberately code, never handed to a model. Fix the script if the
numbers or phrasing are wrong; do not have a model "improve" it.

Usage:
    finance-desk.py <edition_dir> [TICKER ...]

Tickers default to the North Sea board: Brent crude (BZ=F), Shell, BP
and Harbour Energy — the prices that move Aberdeen. Exit status is 1 (and nothing is written) if
any ticker fails to resolve, so a nightly job fails the run rather than print
a paper page with a guessed price.

Writes <edition_dir>/articles/03-the-markets.md (code 03 — after the lead and
weather, where a markets board belongs).
"""

import argparse
import json
import sys
import urllib.request
from pathlib import Path

API = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=1d&interval=1d"
HEADERS = {"User-Agent": "Mozilla/5.0 (vael-paper-example/1.0)"}
# Readers know these by name, not by Yahoo's listing titles ("HARBOUR ENERGY PLC ORD 0.002P").
NAMES = {"BZ=F": "Brent crude", "SHEL.L": "Shell", "BP.L": "BP", "HBR.L": "Harbour Energy"}


def fetch_quote(ticker: str) -> dict:
    req = urllib.request.Request(API.format(ticker=ticker), headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        body = json.load(r)
    result = body["chart"]["result"]
    if not result:
        raise ValueError(f"{ticker}: no quote data")
    meta = result[0]["meta"]
    price = meta.get("regularMarketPrice")
    if price is None:
        raise ValueError(f"{ticker}: no price in response")
    prev = meta.get("chartPreviousClose")
    change = (price - prev) if prev else 0.0
    pct = meta.get("regularMarketChangePercent", 0.0)
    return {
        "symbol": meta.get("symbol", ticker),
        "name": NAMES.get(ticker) or meta.get("shortName") or meta.get("longName") or ticker,
        "currency": meta.get("currency", "USD"),
        "price": price,
        "change": change,
        "pct": pct,
        "hi52": meta.get("fiftyTwoWeekHigh"),
        "lo52": meta.get("fiftyTwoWeekLow"),
    }


def money(x: float, currency: str = "USD") -> str:
    """London listings quote in pence (GBp); everything else here is in dollars."""
    if currency == "GBp":
        return f"{x:,.1f}p"
    if currency == "GBP":
        return f"£{x:,.2f}"
    return f"${x:,.2f}"


# A paper spells small numbers; anything larger sets as a figure.
NUMBER_WORDS = {
    1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five",
    6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten",
}


def spell(n: int) -> str:
    return NUMBER_WORDS.get(n, str(n))


def build_article(quotes: list[dict]) -> str:
    up = sum(1 for q in quotes if q["change"] >= 0)
    down = len(quotes) - up
    best = max(quotes, key=lambda q: q["pct"])
    worst = min(quotes, key=lambda q: q["pct"])

    # Five columns (Ticker, Price, Chg, %, 52-wk) risks a table_wide lint;
    # keep to four (all but one numeric) and fold the 52-week into the prose.
    rows = "\n".join(
        f"| {q['symbol']} | {money(q['price'], q.get('currency', 'USD'))} | "
        f"{'+' if q['change'] >= 0 else '−'}{abs(q['change']):,.2f} | "
        f"{'+' if q['pct'] >= 0 else '−'}{abs(q['pct']):.2f}% |"
        for q in quotes
    )

    deck = (
        f"{best['name']} led ({'+' if best['pct'] >= 0 else '−'}"
        f"{abs(best['pct']):.1f}%); {worst['name']} lagged"
    )

    if up and down:
        direction = "mixed"
    elif up:
        direction = "higher"
    else:
        direction = "lower"

    body = (
        f"{spell(len(quotes))} of the names this paper follows finished {direction} "
        f"at the last close — {up} up, {down} down on the day. The standouts were "
        f"{best['name']}, {'up' if best['pct'] >= 0 else 'down'} {abs(best['pct']):.1f}%, "
        f"and {worst['name']}, {'down' if worst['pct'] < 0 else 'up'} "
        f"{abs(worst['pct']):.1f}%. "
        f"The figures are the last close as Yahoo Finance reported it at run time; "
        f"London shares are in pence, Brent in dollars a barrel. None of this is advice — "
        f"it is a board, not a recommendation, and the paper reads the same "
        f"line to itself every morning."
    )

    return f"""---
id: 03-the-markets
headline: Markets at the Close
deck: {deck}
section: business
priority: 3
sources:
  - name: Yahoo Finance
    url: https://finance.yahoo.com
---

{body}

### The board

| Ticker | Price | Chg | % |
|:---|---:|---:|---:|
{rows}

Quotes are the regular-session close for {up + down} names, pulled live from
Yahoo Finance. A minus before a figure is a decline, set in italic on the
page, the way every decline in this paper is.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("edition_dir", type=Path)
    ap.add_argument("tickers", nargs="*", default=["BZ=F", "SHEL.L", "BP.L", "HBR.L"])
    args = ap.parse_args()

    quotes = []
    for t in args.tickers:
        try:
            quotes.append(fetch_quote(t.upper()))
        except Exception as e:
            print(f"error: could not fetch {t}: {e}", file=sys.stderr)
            return 1

    articles = args.edition_dir / "articles"
    articles.mkdir(parents=True, exist_ok=True)
    out = articles / "03-the-markets.md"
    out.write_text(build_article(quotes))
    print(f"wrote {out} ({', '.join(q['symbol'] for q in quotes)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
