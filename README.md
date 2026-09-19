# The Aberdeen Daily 📰

A nightly newspaper for Aberdeen, written by an agent: the local desks read
real feeds, the figures come from code, and it will not publish an edition
that fails its own checks.

**Read it:** https://aberdeen-daily.technoir.cloud · [how it is written](https://aberdeen-daily.technoir.cloud/about.html)

> **This is a fork.** The engine, the desk model and the write → check → fix
> loop are the work of [**vaelkeep/hermes-paper-agent**](https://github.com/vaelkeep/hermes-paper-agent),
> MIT licensed. What is mine here is the Aberdeen adaptation: the local
> source list and ingest desk, the North Sea market board, the sections, and
> the editorial rules below. If you want the original general-purpose
> personal paper, go there — it is excellent, and this would not exist
> without it.

---

## What it is

Aberdeen has real news and a small number of outlets covering it. This takes
what those outlets publish, plus figures computed from live data, and prints
a paper every night: a front page, a City section, Energy & the North Sea,
Weather, Sport, Council, and the rest.

- **Local by default** — BBC North East Scotland, *The Press and Journal*,
  *Energy Voice*, BBC Scotland. All four feeds are live and checked.
- **The board is code, not a model** — Brent crude, Shell, BP and Harbour
  Energy come from a data desk in Python. The model never types a number.
- **Weather for the Granite City** — a seven-day Aberdeen forecast in Celsius
  from Open-Meteo, rendered as a chart and a table by code.
- **It fails loudly** — if the feeds are down or a check comes back red, the
  run stops. It does not reprint yesterday.

## Editorial rules

These are not decoration. A local paper that launders other people's
reporting is both a copyright problem and a worthless product.

1. **Never reproduce a publisher's text.** The ingest desk carries a
   headline, a trimmed extract of the publisher's own feed summary, and the
   link. The prose desks write **original** copy about the story.
2. **Always attribute and link.** Every story carries a `sources:` entry
   naming the outlet and linking the original. Readers should be sent to the
   people who did the reporting.
3. **Never invent a fact or a figure.** Numbers come from data desks. If a
   desk cannot fetch, its story is dropped — it is not guessed.
4. **Say what is unknown.** If the feeds are thin on a story, the paper says
   so rather than padding it.
5. **This is not a substitute for the local press.** It is a nightly digest
   with original commentary that points at them.

## Sources

`inbox/sources.json` holds the feed list, the city coordinates and the
timezone. Every URL in it was verified to return a valid feed:

| Source | Beat |
|---|---|
| BBC News — North East Scotland, Orkney & Shetland | city |
| The Press and Journal | city |
| Energy Voice | energy |
| BBC News — Scotland | scotland |

Add or remove freely — a feed that fails is skipped, not fatal, unless every
feed fails.

## Running it

Python 3.11+ and Node for the engine's reader; nothing else on the host.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
python3 scripts/fetch-feeds.py                              # tonight's news into inbox/feeds.md
E=editions/$(date -u -v+1d +%F)                             # GNU date: date -u -d tomorrow +%F
python3 scripts/weather-desk.py $E --place Aberdeen
python3 scripts/finance-desk.py $E
# the agent writes the prose desks and the front page (AGENTS.md, "The nightly run")
$(scripts/engine.sh)/vael-paper-check --root editions $E    # never publish on red
./scripts/deploy.sh                                         # site; the edition also becomes a Beehiiv draft
```

The upstream personal desks (steps, ledger) and demo material were removed; this repo is only the Aberdeen paper.

## Licence

MIT, inherited from [vaelkeep/hermes-paper-agent](https://github.com/vaelkeep/hermes-paper-agent).
The original copyright notice is preserved in [LICENSE](LICENSE).
