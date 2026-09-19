# aberdeen-daily
The Aberdeen Daily: a free morning email and site about what is good in Aberdeen today: things to do, new places, concerts and shows, and good news from the city. Written by an agent from public sources, published at https://aberdeen-daily.technoir.cloud. Fork of vaelkeep/hermes-paper-agent; rendered and checked by vaelkeep/vael-paper (pinned in `scripts/engine.sh` and `Dockerfile`).

## Commands
- Check (before every commit and deploy): `.venv/bin/python -m ruff check . && .venv/bin/python -m pytest -q && $(scripts/engine.sh)/vael-paper-check --root editions --all` (setup: `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt`)
- Email preview of the live edition: `python3 scripts/email-edition.py > preview.html`
- Deploy: `./scripts/deploy.sh` (the VPS also deploys every push to `main` within 15 minutes)

## Editorial line
The reader opens this over breakfast to find out what's on and what's new. It is warm, useful and calm, never alarming.
1. **Positive and practical.** Lead with things to do: events, openings, concerts, shows, markets, exhibitions, outdoor plans, and good news (awards, new facilities, community wins).
2. **Leave out** crime, courts, accidents, deaths, missing people, layoffs, disputes and scandal. If a story is bad news, it is not this paper's story.
3. **No sensationalism.** No clickbait headlines, no superlatives the source doesn't support, no exclamation marks.
4. **Never invent a detail.** Name only the venue, date, time, price, person or place the source gives. Example of a failure: a source says "ordnance donated for an exhibition" and the story says "museum" and "live": both words were invented.
5. **Original words, credited sources.** Never reproduce a publisher's wording; every story carries `sources:` with the outlet and link.
6. **Thin is fine.** A short edition beats a padded one.

## The nightly run
1. `git pull`; `python3 scripts/fetch-feeds.py` (exit 1 = no paper today).
2. `E=editions/$(TZ=Europe/London date +%F)`; if it exists, stop. `python3 scripts/weather-desk.py $E --place Aberdeen` (dropped, never guessed, if it fails).
3. Read `inbox/feeds.md` and the `pages` listed in `inbox/sources.json` for dates and venues. Write three to six stories (`04-…`), sections only from `editions/paper.json`; read `.engine/docs/WRITING.md` for the format. Prefer events in the next seven days, with day, venue and how to go.
4. The front page last: `01-front-page.md`, `section: front`, `priority: 1`, `span: full`: "Today in Aberdeen", the best of the edition in the order a reader would plan the day.
5. `vael-paper-check --root editions $E --json` until `"ok": true`; pytest must pass (it rejects repeated headlines).
6. Commit the edition to `main` and push. The VPS deploys it; the editor gets it as a Gmail draft for review. Beehiiv is paused until the format settles.
