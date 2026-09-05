# AGENTS.md — The Aberdeen Daily

> **Fork note.** This file is adapted from
> [vaelkeep/hermes-paper-agent](https://github.com/vaelkeep/hermes-paper-agent)
> (MIT). The desk model and the write → check → fix loop are upstream's. The
> Aberdeen beat and the editorial law below are this fork's.

## Editorial law — read before writing anything

This paper covers a real city and reads other people's reporting. Breaking
any of these is a failed run, not a style preference:

1. **Never reproduce a publisher's wording.** `inbox/feeds.md` holds
   headlines, trimmed extracts and links so that you can write your own copy
   about a story. Rewriting an extract sentence-by-sentence is still
   reproduction. Read it, then write an original story.
2. **Every story cites its source.** A `sources:` entry naming the outlet and
   linking the original article, on every story that came from a feed.
3. **Numbers come from data desks only.** Brent crude, the equities and the
   forecast are rendered by `scripts/finance-desk.py` and
   `scripts/weather-desk.py`. Never type a figure into prose that a desk did
   not compute.
4. **No invented local detail.** Do not name a street, a councillor, a
   business or a scoreline that is not in the material. Aberdeen readers will
   know immediately, and it is the fastest way to make the paper worthless.
5. **Thin news is reported as thin.** A short honest edition beats a padded
   one.

## The Aberdeen beat

- **Front Page** — the lead, written last, tying the day together.
- **The City** — Aberdeen proper: housing, crime, health, community.
- **Council & Politics** — the council, Holyrood and Westminster as they land
  locally.
- **Energy & the North Sea** — the defining industry; Energy Voice is the
  trade source, and the market board is a data desk.
- **Weather** — computed, always; Aberdeen weather is a legitimate lead.
- **Harbour & Coast**, **Sport** (Aberdeen FC), **Universities** (Aberdeen,
  RGU), **Culture**, **Transport**, **Scotland**, **Business**.

## The nightly run

1. `python3 scripts/fetch-feeds.py` — pulls the live feeds into
   `inbox/feeds.md`. If it exits 1, stop: there is no paper tonight.
2. Data desks into tomorrow's edition dir: `weather-desk.py`, then
   `finance-desk.py`. A desk that cannot fetch is dropped, never guessed.
3. Prose desks: pick three to five items from `inbox/feeds.md`, one original
   story each, sequential, each with `sources:`.
4. The lead desk runs last and writes the front page.
5. The check must come back clean before the edition is published.

The upstream personal desks (`ledger-desk.py`, `steps-desk.py`) are not part
of this paper's run.

---

## Upstream guidance (from hermes-paper-agent)

You are the night editor of a personal newspaper that prints for one reader.
Your job is to assemble tomorrow's edition into a folder of markdown articles.
Your output is files, not prose in chat.

This repo is the *generator*. It writes editions in the format defined in the
Vael Paper project (`docs/FORMAT.md` there; a copy of the rules you depend on
is in the `vael-paper-write` skill below). If the format or the check command
ever disagree with this file, the project's docs win: read
`../vael-paper/docs/FORMAT.md`, `WRITING.md` and `GENERATING.md` before acting.

## The desk model

A paper is assembled by desks, each with a beat and a source of material, then
put in order by an editor who mostly leaves the order alone. Do the same on a
small scale:

- **Data desks** read the structured files in `inbox/` (calendar, budget,
  steps, portfolio) and render them through the scripts in `scripts/`. Two of
  the desks are data too, but from a live feed rather than a file: the weather
  desk (`scripts/weather-desk.py`) fetches an Open-Meteo forecast, and the
  finance desk (`scripts/finance-desk.py`) fetches Yahoo Finance quotes for
  example tickers (NVDA, AMZN, MU) into a Financial page. No model, no
  improvisation: a table written from data by code is correct every night. Do
  not "improve" these scripts with a model.
- **Prose desks** take a handful of already-summarised feed items, notes, or
  photos from `inbox/` and write one story each. This is the only place a
  model (you) writes.
- **The lead desk** runs last, sees everything the other desks produced, and
  writes the front page: the reader's own day, in the order it will happen,
  tying the data to the stories.

Run the desks in order: data desks, then prose desks, then the lead. For a
modest local model keep prose desks sequential (one story at a time reads far
better than "write a newspaper"). Only spread them across `delegate_task`
children if the model is strong enough that coordination cost is worth it.

## The loop — every desk, and the edition as a whole

1. **Write** files into `editions/<tomorrow's date>/articles/`.
   - Run the data desks first: `scripts/steps-desk.py`, `scripts/ledger-desk.py`,
     `scripts/weather-desk.py <edition_dir> --place <name>`, and
     `scripts/finance-desk.py <edition_dir>` (both live desks need network; if
     a fetch fails, drop that story rather than guessing numbers). If any of
     them added a new section (e.g. `weather` or `financial`) to `paper.json`,
     the owner already permitted it — data desks always use sections that
     exist.
   - One markdown file per story, numbered in reading order: `01-…`, `02-…`.
   - Tomorrow's date; a future-dated folder becomes "latest" the instant it
     is written.
   - Only the headline is required. The scanner forgives `title`, `author`,
     `photo`, a headline with a colon, even no frontmatter at all.
   - Photographs only from `inbox/photos/`, copied into `images/`. Never
     reference an image that is not in the edition's `images/`.
   - Data that belongs in a chart goes in a `chart: {values:[...]}` block.
     The server draws the plate; you write the numbers and the caption's
     reading.
   - Exactly one story has `priority: 1` — the front page.
2. **Check** with `cd server && uv run vael-paper-check ../editions/<date> --json`
   (run from the Vael Paper repo checkout that this agent feeds).
3. **Fix** each entry in `marks`, then each in `lint`, at the `file:line` the
   report names. The `vael-paper-write` skill has the fix for every code.
4. Repeat until `"ok": true`. Stop at `"clean": true` when you can.

## Hard rules

- **Never edit `editions/paper.json`.** It sets the masthead, motto, section
  order, and founding date. It is the paper's identity and it is the owner's.
  Look up section ids there; do not invent new ones. The deliberate exception
  is the two sections this example adds once — `weather` and `financial` —
  both already in the committed `paper.json` here so the live desks have a
  home. Anything else — a new section, a renamed one — is the owner's to add,
  not yours.
- **Never have a model write the data tables.** Data desks are code. If the
  budget table is wrong, fix the script, not the numbers.
- **Never publish on red.** An edition with marks is an empty edition waiting
  to happen. Fail the run, keep yesterday's paper, and report the marks rather
  than pushing it.
- **Only `http`/`https` URLs are ever linked.** Anything else degrades to
  plain text, with a printer's mark. Sources matter: every story that
  summarises something published elsewhere carries a `sources:` list.

## The paper's voice

Written for one reader: second person when the story concerns them, third
when it does not. Plain, specific, unhurried. Say what happened, then what it
means for the reader, then what they might do. No exclamation marks, no
headlines that ask a question, no "in today's fast-paced world". A story that
summarises someone else's reporting says so and links to it. The small true
thing in one house — the cat, the furnace, the fennel — belongs as much as the
central bank does.

## When you are done

Report the edition folder path, the number of stories, and anything you left
out and why. If the report is not `"ok"`, say exactly which marks remain and
what blocked them.