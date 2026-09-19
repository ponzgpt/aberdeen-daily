# aberdeen-daily
The Aberdeen Daily: a nightly local newspaper for Aberdeen, written by an agent from public feeds plus code-computed weather and markets, published at https://aberdeen-daily.technoir.cloud and emailed through Beehiiv. Fork of vaelkeep/hermes-paper-agent; rendered and checked by vaelkeep/vael-paper (pinned in `scripts/engine.sh` and `Dockerfile`).

## Commands
- Check (before every commit and deploy): `.venv/bin/python -m ruff check . && .venv/bin/python -m pytest -q && $(scripts/engine.sh)/vael-paper-check --root editions --all` (setup: `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt`)
- Nightly edition: see "The nightly run" below
- Deploy: `./scripts/deploy.sh`

## Editorial law (breaking one is a failed run)
1. Never reproduce a publisher's wording; `inbox/feeds.md` is material to write original copy from.
2. Every story from a feed carries `sources:` with the outlet and the article link.
3. Figures come only from data desks (`scripts/weather-desk.py`, `scripts/finance-desk.py`); never type a number a desk or the source did not give.
4. No invented local detail: no street, person, business or score that is not in the material.
5. Thin news is reported as thin; never pad.

## The nightly run
1. `python3 scripts/fetch-feeds.py`; if it exits 1 there is no paper tonight.
2. `E=editions/$(TZ=Europe/London date +%F)` (the run is at 04:00, so that is the morning being published; if the folder already exists, stop); `python3 scripts/weather-desk.py $E --place Aberdeen`; `python3 scripts/finance-desk.py $E`. A desk that fails is dropped, never guessed.
3. Three to five prose stories from `inbox/feeds.md`, one file each (`04-…`), sections only from `editions/paper.json`; read `.engine/docs/WRITING.md` for the format.
4. The front page last: `01-front-page.md`, `section: front`, `priority: 1`, `span: full`; exactly one priority-1 story.
5. `vael-paper-check --root editions $E --json` until `"ok": true` (aim for `"clean": true`); never commit an edition with marks.
6. Commit the edition to `main` and push; deploy; create the Beehiiv draft (never send it: a human sends).
