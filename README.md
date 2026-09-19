# The Aberdeen Daily 📰

A free morning paper about what is good in Aberdeen: what's on, new places to eat,
concerts and shows, and good news from the city. Written by an agent from public
sources, and it will not publish an edition that fails its own checks.

**Read it:** https://aberdeen-daily.technoir.cloud · [how it is written](https://aberdeen-daily.technoir.cloud/about.html)

> **This is a fork.** The engine, the desk model and the write → check → fix
> loop are the work of [**vaelkeep/hermes-paper-agent**](https://github.com/vaelkeep/hermes-paper-agent),
> MIT licensed. What is mine here is the Aberdeen adaptation: the local
> source list and ingest desk, the sections, and the editorial rules below. If you want the original general-purpose
> personal paper, go there — it is excellent, and this would not exist
> without it.

---

## What it is

Aberdeen has plenty on and a small number of outlets covering it. This gathers what they
publish, adds the venues' own listings and a forecast computed from live data, and prints a
morning paper: what's on, food and drink, culture, things to do outdoors, the universities
and the Dons.

- **Positive by design** — crime, courts, accidents and scandal are out of scope. This is the
  paper you read to decide what to do this week.
- **Local by default** — The Press and Journal's What's On, Food and Drink, Entertainment and
  Lifestyle feeds, the University of Aberdeen, Aberdeen Live, plus the Aberdeen Performing Arts
  and VisitAberdeenshire listings.
- **Weather for the Granite City** — a seven-day Aberdeen forecast in Celsius from Open-Meteo,
  rendered as a chart and a table by code.
- **It fails loudly** — if the feeds are down or a check comes back red, the run stops. It does
  not reprint yesterday.

## Editorial rules

1. **Positive and practical.** Lead with what to do and what is new. Bad news is another
   paper's job.
2. **Never reproduce a publisher's text.** The ingest desk carries a headline, a trimmed
   extract and the link; the prose desks write original copy.
3. **Always attribute and link.** Every story carries `sources:` naming the outlet.
4. **Never invent a detail.** Only the venue, date, time or price the source gives.
5. **Thin is fine.** A quiet day makes a short paper.

## Sources

`inbox/sources.json` holds the feed list, the city coordinates and the
timezone. Every URL in it was verified to return a valid feed:

| Source | Beat |
|---|---|
| The Press and Journal — What's On | whats-on |
| The Press and Journal — Food and Drink | food |
| The Press and Journal — Entertainment | culture |
| The Press and Journal — Lifestyle | city |
| University of Aberdeen — News | campus |
| Aberdeen Live | city |

Listings pages the editor reads directly: Aberdeen Performing Arts and VisitAberdeenshire.

Add or remove freely — a feed that fails is skipped, not fatal, unless every
feed fails.

## Running it

Python 3.11+ and Node for the engine's reader; nothing else on the host.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
python3 scripts/fetch-feeds.py                              # the week's items into inbox/feeds.md
E=editions/$(date -u -v+1d +%F)                             # GNU date: date -u -d tomorrow +%F
python3 scripts/weather-desk.py $E --place Aberdeen
# the agent writes the stories and the front page (AGENTS.md, "The nightly run")
$(scripts/engine.sh)/vael-paper-check --root editions $E    # never publish on red
./scripts/deploy.sh                                         # site; the edition also becomes a Beehiiv draft
```

The upstream personal desks and demo material were removed; this repo is only the Aberdeen paper.

## Licence

MIT, inherited from [vaelkeep/hermes-paper-agent](https://github.com/vaelkeep/hermes-paper-agent).
The original copyright notice is preserved in [LICENSE](LICENSE).
