"""The finance desk: a markets board built from Yahoo quote responses.

fetch_quote is exercised against canned bodies via a stubbed urlopen, so no
test touches the network.
"""

import io
import json
import sys
from contextlib import contextmanager

import pytest
from conftest import FIXTURES, frontmatter


@contextmanager
def _canned(payload: dict):
    yield io.BytesIO(json.dumps(payload).encode())


def test_money_formatting(finance_desk):
    assert finance_desk.money(183.156) == "$183.16"
    assert finance_desk.money(1234.5) == "$1,234.50"


@pytest.mark.parametrize("n,word", [(1, "One"), (3, "Three"), (10, "Ten"), (11, "11")])
def test_spell(finance_desk, n, word):
    assert finance_desk.spell(n) == word


def test_fetch_quote_reads_the_response(finance_desk, monkeypatch):
    body = json.loads((FIXTURES / "yahoo-nvda.json").read_text())
    monkeypatch.setattr(finance_desk.urllib.request, "urlopen",
                        lambda *a, **k: _canned(body))
    q = finance_desk.fetch_quote("NVDA")
    assert q["symbol"] == "NVDA"
    assert q["name"] == "NVIDIA Corporation"
    assert q["price"] == pytest.approx(183.16)
    assert q["change"] == pytest.approx(3.16)      # 183.16 - 180.00
    assert q["hi52"] == pytest.approx(212.19)


def test_fetch_quote_raises_on_empty_result(finance_desk, monkeypatch):
    body = json.loads((FIXTURES / "yahoo-empty.json").read_text())
    monkeypatch.setattr(finance_desk.urllib.request, "urlopen",
                        lambda *a, **k: _canned(body))
    with pytest.raises(ValueError, match="no quote data"):
        finance_desk.fetch_quote("NOPE")


def test_fetch_quote_raises_when_price_is_missing(finance_desk, monkeypatch):
    body = {"chart": {"result": [{"meta": {"symbol": "X"}}]}}
    monkeypatch.setattr(finance_desk.urllib.request, "urlopen",
                        lambda *a, **k: _canned(body))
    with pytest.raises(ValueError, match="no price"):
        finance_desk.fetch_quote("X")


def test_count_matches_the_tickers_given(finance_desk, quote):
    """Regression: the body opened "Three of the names" for any number of
    tickers, though the README documents passing two."""
    two = finance_desk.build_article([quote("AAPL"), quote("MSFT", pct=-1.0, change=-1)])
    assert two.startswith("---") and "Two of the names" in two
    assert "Three of the names" not in two

    three = finance_desk.build_article([quote("A"), quote("B"), quote("C")])
    assert "Three of the names" in three


@pytest.mark.parametrize("pcts,expected", [
    ([1.0, 2.0], "higher"),
    ([-1.0, -2.0], "lower"),
    ([1.0, -2.0], "mixed"),
])
def test_direction_is_honest(finance_desk, quote, pcts, expected):
    """Regression: an all-down day reported "mixed"."""
    quotes = [quote(f"T{i}", pct=p, change=p) for i, p in enumerate(pcts)]
    assert f"finished {expected} at the last close" in finance_desk.build_article(quotes)


def test_declines_use_the_typographic_minus(finance_desk, quote):
    article = finance_desk.build_article([quote("X", price=10.0, change=-1.5, pct=-2.5)])
    assert "−1.50" in article and "−2.50%" in article


def test_board_has_four_columns(finance_desk, quote):
    """Five would risk the table_wide lint; the 52-week span folds into prose."""
    article = finance_desk.build_article([quote()])
    header = next(ln for ln in article.splitlines() if ln.startswith("| Ticker"))
    assert header.count("|") - 1 == 4


def test_carries_a_sources_block(finance_desk, quote):
    """A story built on someone else's reporting must say so."""
    article = finance_desk.build_article([quote()])
    assert "sources:" in article
    assert "url: https://finance.yahoo.com" in article


def test_section_is_one_the_paper_knows(finance_desk, quote, paper_sections):
    fm = frontmatter(finance_desk.build_article([quote()]))
    assert fm["section"] in paper_sections


def test_main_writes_the_board(finance_desk, quote, tmp_path, monkeypatch):
    out = tmp_path / "edition"
    monkeypatch.setattr(finance_desk, "fetch_quote", lambda t: quote(t))
    monkeypatch.setattr(sys, "argv", ["finance-desk.py", str(out), "AAPL", "MSFT"])
    assert finance_desk.main() == 0
    assert (out / "articles" / "03-the-markets.md").exists()


def test_main_fails_and_writes_nothing_when_a_ticker_will_not_resolve(
    finance_desk, tmp_path, monkeypatch
):
    """One bad ticker fails the run rather than printing a page with a hole."""
    def boom(ticker):
        raise ValueError(f"{ticker}: no quote data")

    out = tmp_path / "edition"
    monkeypatch.setattr(finance_desk, "fetch_quote", boom)
    monkeypatch.setattr(sys, "argv", ["finance-desk.py", str(out), "NOPE"])
    assert finance_desk.main() == 1
    assert not (out / "articles" / "03-the-markets.md").exists()


def test_main_uppercases_tickers(finance_desk, quote, tmp_path, monkeypatch):
    seen = []

    def record(ticker):
        seen.append(ticker)
        return quote(ticker)

    monkeypatch.setattr(finance_desk, "fetch_quote", record)
    monkeypatch.setattr(sys, "argv", ["finance-desk.py", str(tmp_path / "e"), "nvda"])
    assert finance_desk.main() == 0
    assert seen == ["NVDA"]
