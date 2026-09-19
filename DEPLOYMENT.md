# Deployment

**Site:** https://aberdeen-daily.technoir.cloud: Hostinger VPS (`ssh hoid`), Swarm service `aberdeen-daily` on `dokploy-network`, Traefik route `/etc/dokploy/traefik/dynamic/aberdeen-daily.yml`, Let's Encrypt.

The Dockerfile clones the vael-paper engine at a pinned commit, builds its reader, **fails the build if any edition has a mark** (`vael-paper-check --all`), exports the static site from `editions/`, adds `web/` (about page) and serves it with nginx.

```bash
./scripts/deploy.sh                                   # tests + edition check, build <sha> on the VPS, roll out, wait for /healthz
ssh hoid docker service rollback aberdeen-daily       # undo
```

**Email:** each edition becomes a Beehiiv draft in the "The Aberdeen Daily" publication. Sending stays a human action in Beehiiv.

## The nightly edition (automatic)

- **Writer:** the Hermes agent on the VPS (Swarm service `personal-assistant-hermes-*`), cron job "Aberdeen Daily nightly edition" at `0 3 * * *` UTC (04:00 in summer, 03:00 in winter, London), pinned to `anthropic/claude-sonnet-5` via OpenRouter (the default mini model truncates a whole edition). It runs as the container user `hermes`, so the working copy must stay owned by `hermes`. Working copy: `/opt/hermes-data/workspace/aberdeen-daily`; prompt: `/opt/hermes-data/workspace/.deploy/nightly-prompt.txt`. It follows AGENTS.md, checks the edition, commits and pushes to `main` with a write deploy key (`/opt/hermes-data/workspace/.deploy/aberdeen-daily`, GitHub deploy key "Hermes on hoid").
- **Publisher:** the systemd timer `aberdeen-daily-autodeploy.timer` on the VPS checks `main` every 15 minutes and rebuilds when it moved (`scripts/vps-autodeploy.sh`; reinstall with `scripts/install-autodeploy.sh`). The Docker build refuses an edition with marks, so the site keeps the last good paper.
- **Inspect:** `ssh hoid 'docker exec $(docker ps -q -f name=personal-assistant-hermes) hermes cron list'` and `ssh hoid journalctl -u aberdeen-daily-autodeploy -n 20`.

## Review email (while Beehiiv is paused)

Every day at 07:00 London time a systemd timer on the VPS (not Hermes) emails the latest edition to the editor, once per edition (`scripts/email-edition.py`, installed as `/usr/local/bin/aberdeen-daily-email` by `scripts/install-email.sh`). Credentials: a Google app password stored with `./scripts/set-email-password.sh` in `/etc/aberdeen-daily/smtp.env` (root, 600). Preview locally: `python3 scripts/email-edition.py --dry-run > preview.html`.
